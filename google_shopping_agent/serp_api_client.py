"""
SERP API Client for Google Shopping searches
"""
import httpx
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config import SerpApiConfig
from models import ShoppingProduct, SearchQuery

logger = logging.getLogger(__name__)


class SerpApiClient:
    """Client for interacting with SERP API Google Shopping endpoint"""
    
    def __init__(self, config: SerpApiConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    def _build_params(self, query: SearchQuery) -> Dict[str, Any]:
        """Build API parameters from search query"""
        params = {
            "engine": self.config.engine,
            "q": query.keyword,
            "api_key": self.config.api_key,
            "gl": self.config.country,
            "hl": self.config.language,
            "google_domain": self.config.google_domain,
            "num": query.num_results or self.config.default_num_results,
        }
        
        # Add optional filters
        if query.on_sale:
            params["on_sale"] = "true"
        
        if query.min_price is not None:
            params["min_price"] = query.min_price
        
        if query.max_price is not None:
            params["max_price"] = query.max_price
        
        # Sorting: None=relevance (best results), 1=price low-high, 2=price high-low
        if query.sort_by:
            params["sort_by"] = query.sort_by
        
        # Time filter: qdr:d=24h, qdr:w=week, qdr:m=month, qdr:y=year
        if query.time_period:
            params["tbs"] = query.time_period
        
        # Condition filter: new, used, refurbished
        if query.condition:
            params["condition"] = query.condition
        
        # Free shipping filter
        if query.free_shipping:
            params["free_shipping"] = "true"
        
        # Local sellers only
        if query.local_sellers:
            params["local_sellers"] = "true"
        
        return params
    
    def _parse_product(self, item: Dict[str, Any]) -> Optional[ShoppingProduct]:
        """Parse a single product from API response"""
        try:
            # Extract price - handle various formats
            price = item.get("extracted_price")
            if price is None:
                price_str = item.get("price", "")
                if price_str:
                    # Try to extract numeric value
                    import re
                    match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
                    if match:
                        price = float(match.group())
            
            if price is None or price <= 0:
                return None
            
            # Extract original price
            original_price = item.get("extracted_old_price")
            
            # Create product
            product = ShoppingProduct(
                title=item.get("title", ""),
                product_id=str(item.get("product_id", "")),
                source=item.get("source", "Unknown"),
                price=price,
                original_price=original_price,
                thumbnail=item.get("thumbnail") or item.get("serpapi_thumbnail"),
                product_link=item.get("product_link") or item.get("link"),
                rating=item.get("rating"),
                reviews=item.get("reviews"),
                delivery_info=item.get("delivery"),
                condition=item.get("second_hand_condition"),
            )
            
            # Extract discount info
            if "tag" in item:
                product.discount_tag = item["tag"]
            elif "extensions" in item and item["extensions"]:
                # Look for discount in extensions
                for ext in item["extensions"]:
                    if "OFF" in str(ext).upper() or "%" in str(ext):
                        product.discount_tag = ext
                        break
            
            # Calculate discount percentage
            product.discount_percentage = product.calculate_discount_percentage()
            
            return product
            
        except Exception as e:
            logger.warning(f"Failed to parse product: {e}")
            return None
    
    async def search(self, query: SearchQuery) -> List[ShoppingProduct]:
        """
        Search Google Shopping for products
        
        Args:
            query: Search query parameters
            
        Returns:
            List of ShoppingProduct objects
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        params = self._build_params(query)
        products = []
        
        try:
            logger.info(f"Searching Google Shopping for: {query.keyword}")
            
            response = await self._client.get(
                self.config.base_url,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse shopping results
            shopping_results = data.get("shopping_results", [])
            for item in shopping_results:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            # Also check inline shopping results
            inline_results = data.get("inline_shopping_results", [])
            for item in inline_results:
                product = self._parse_product(item)
                if product:
                    products.append(product)
            
            logger.info(f"Found {len(products)} products for query: {query.keyword}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching for {query.keyword}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching for {query.keyword}: {e}")
            raise
        
        return products
    
    async def search_with_discount_filter(
        self,
        query: SearchQuery,
        min_discount: float = 10.0
    ) -> List[ShoppingProduct]:
        """
        Search and filter for products with significant discounts
        
        Args:
            query: Search query parameters
            min_discount: Minimum discount percentage to include
            
        Returns:
            List of discounted products
        """
        # Ensure on_sale filter is enabled
        query.on_sale = True
        
        products = await self.search(query)
        
        # Filter for products with meaningful discounts
        discounted_products = []
        for product in products:
            if product.has_discount:
                discount = product.calculate_discount_percentage()
                if discount and discount >= min_discount:
                    discounted_products.append(product)
        
        logger.info(
            f"Found {len(discounted_products)} products with >= {min_discount}% discount "
            f"out of {len(products)} total for: {query.keyword}"
        )
        
        return discounted_products
    
    async def search_multiple(
        self,
        queries: List[SearchQuery],
        min_discount: float = 10.0
    ) -> Dict[str, List[ShoppingProduct]]:
        """
        Search multiple queries and aggregate results
        
        Args:
            queries: List of search queries
            min_discount: Minimum discount percentage
            
        Returns:
            Dictionary mapping query keywords to product lists
        """
        results = {}
        
        for query in queries:
            try:
                products = await self.search_with_discount_filter(query, min_discount)
                results[query.keyword] = products
            except Exception as e:
                logger.error(f"Failed to search for {query.keyword}: {e}")
                results[query.keyword] = []
        
        return results
