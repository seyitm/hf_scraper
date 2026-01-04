"""
Google Shopping Agent for harbifırsat
Searches for discounted products and creates deals
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from config import AgentConfig, load_config
from models import (
    ShoppingProduct, 
    SearchQuery, 
    DealToCreate,
    AgentResult,
    DealStatus
)
from serp_api_client import SerpApiClient
from supabase_client import HarbiSupabaseClient

logger = logging.getLogger(__name__)


class GoogleShoppingAgent:
    """
    AI Agent that searches Google Shopping for discounted products
    and creates deals in the harbifırsat platform
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or load_config()
        self.supabase = HarbiSupabaseClient(self.config.supabase)
        self._result = AgentResult(success=True)
    
    def _product_to_deal(
        self,
        product: ShoppingProduct,
        category_id: Optional[str] = None,
        store_id: Optional[str] = None,
        posted_by: Optional[str] = None
    ) -> DealToCreate:
        """
        Convert a ShoppingProduct to a DealToCreate
        
        Args:
            product: Shopping product from Google
            category_id: Optional category UUID
            store_id: Optional store UUID
            posted_by: Optional user UUID who "posted" (agent system user)
            
        Returns:
            DealToCreate object
        """
        # Use original price if available, otherwise estimate
        original_price = product.original_price
        if not original_price and product.discount_percentage:
            # Calculate original from discount
            original_price = product.price / (1 - product.discount_percentage / 100)
        elif not original_price:
            original_price = product.price  # No discount info available
        
        discount_pct = product.calculate_discount_percentage() or 0
        
        # Build description
        description_parts = [f"Found on {product.source}"]
        if product.rating:
            description_parts.append(f"Rating: {product.rating}/5")
        if product.reviews:
            description_parts.append(f"({product.reviews} reviews)")
        if product.delivery_info:
            description_parts.append(f"Delivery: {product.delivery_info}")
        if product.condition:
            description_parts.append(f"Condition: {product.condition}")
        
        description = " | ".join(description_parts)
        
        return DealToCreate(
            title=product.title[:200],  # Limit title length
            description=description,
            original_price=round(original_price, 2),
            discounted_price=round(product.price, 2),
            discount_percentage=round(discount_pct, 2),
            currency=product.currency,
            affiliate_url=product.product_link or "",
            image_url=product.thumbnail,
            category_id=category_id,
            store_id=store_id,
            posted_by=posted_by,
            status=DealStatus.PENDING  # Requires manual approval
        )
    
    async def gather_search_queries(self) -> List[SearchQuery]:
        """
        Gather all search queries from various sources
        
        Returns:
            List of SearchQuery objects to process
        """
        queries = []
        
        # 1. Get queries from deal alerts (highest priority)
        logger.info("Fetching deal alerts...")
        deal_alert_queries = await self.supabase.get_active_deal_alerts()
        for q in deal_alert_queries:
            q.priority = 10  # Highest priority
        queries.extend(deal_alert_queries)
        logger.info(f"Found {len(deal_alert_queries)} deal alert queries")
        
        # 2. Add trending keywords
        logger.info("Fetching trending keywords...")
        trending = await self.supabase.get_trending_keywords(limit=10)
        for keyword in trending:
            queries.append(SearchQuery(
                keyword=keyword,
                on_sale=True,
                priority=5
            ))
        logger.info(f"Added {len(trending)} trending keyword queries")
        
        # Sort by priority (highest first) and deduplicate
        seen_keywords = set()
        unique_queries = []
        for q in sorted(queries, key=lambda x: x.priority, reverse=True):
            keyword_lower = q.keyword.lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                unique_queries.append(q)
        
        logger.info(f"Total unique queries to process: {len(unique_queries)}")
        return unique_queries
    
    async def process_products(
        self,
        products: List[ShoppingProduct],
        category_id: Optional[str] = None
    ) -> int:
        """
        Process found products and create deals
        
        Args:
            products: List of products to process
            category_id: Optional category to assign
            
        Returns:
            Number of deals created
        """
        deals_created = 0
        
        for product in products:
            try:
                # Skip if no valid URL
                if not product.product_link:
                    continue
                
                # Check if deal already exists
                if await self.supabase.check_deal_exists(product.product_id):
                    logger.debug(f"Deal already exists for: {product.title}")
                    continue
                
                # Get or create store
                store_id = await self.supabase.get_or_create_store(product.source)
                
                # Convert to deal
                deal = self._product_to_deal(
                    product,
                    category_id=category_id,
                    store_id=store_id
                )
                
                # Create deal
                deal_id = await self.supabase.create_deal(deal)
                if deal_id:
                    deals_created += 1
                    logger.info(f"Created deal: {product.title[:50]}...")
                
            except Exception as e:
                logger.error(f"Error processing product {product.title}: {e}")
                self._result.add_error(str(e))
        
        return deals_created
    
    async def run(
        self,
        max_queries: int = 20,
        min_discount: float = None
    ) -> AgentResult:
        """
        Run the Google Shopping agent
        
        Args:
            max_queries: Maximum number of search queries to process
            min_discount: Minimum discount percentage (uses config default if not specified)
            
        Returns:
            AgentResult with execution statistics
        """
        if min_discount is None:
            min_discount = self.config.min_discount_percentage
        
        logger.info("=" * 50)
        logger.info("Starting Google Shopping Agent")
        logger.info(f"Minimum discount threshold: {min_discount}%")
        logger.info("=" * 50)
        
        # Gather search queries (can still read from Supabase for query generation)
        queries = await self.gather_search_queries()
        queries = queries[:max_queries]  # Limit queries
        
        # Search Google Shopping
        async with SerpApiClient(self.config.serp_api) as serp_client:
            for query in queries:
                try:
                    logger.info(f"\nSearching: {query.keyword}")
                    
                    products = await serp_client.search_with_discount_filter(
                        query,
                        min_discount=min_discount
                    )
                    
                    self._result.products_found += len(products)
                    self._result.products_with_discount += len([p for p in products if p.has_discount])
                    self._result.search_queries_processed += 1
                    
                    # Products found - no longer writing to Supabase
                    # Use Google Sheets or Streamlit UI to export products
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing query '{query.keyword}': {e}")
                    self._result.add_error(f"Query '{query.keyword}': {str(e)}")
        
        logger.info("\n" + "=" * 50)
        logger.info("Google Shopping Agent Complete")
        logger.info(f"Queries processed: {self._result.search_queries_processed}")
        logger.info(f"Products found: {self._result.products_found}")
        logger.info(f"Products with discount: {self._result.products_with_discount}")
        if self._result.errors:
            logger.warning(f"Errors: {len(self._result.errors)}")
        logger.info("=" * 50)
        
        return self._result


async def run_agent(
    max_queries: int = 20,
    min_discount: float = 10.0
) -> AgentResult:
    """
    Convenience function to run the agent
    
    Args:
        max_queries: Maximum search queries to process
        min_discount: Minimum discount percentage
        
    Returns:
        AgentResult
    """
    agent = GoogleShoppingAgent()
    return await agent.run(max_queries=max_queries, min_discount=min_discount)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the agent
    result = asyncio.run(run_agent())
    print(f"\nResult: {result.to_dict()}")
