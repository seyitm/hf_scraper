"""
Supabase client for harbifırsat database operations
"""
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

from config import SupabaseConfig
from models import DealToCreate, SearchQuery

logger = logging.getLogger(__name__)


class HarbiSupabaseClient:
    """Client for interacting with harbifırsat Supabase database"""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self._client: Optional[Client] = None
    
    def connect(self) -> "HarbiSupabaseClient":
        """Initialize Supabase client"""
        key = self.config.service_role_key or self.config.anon_key
        self._client = create_client(self.config.url, key)
        return self
    
    @property
    def client(self) -> Client:
        if not self._client:
            raise RuntimeError("Client not connected. Call connect() first.")
        return self._client
    
    async def get_active_deal_alerts(self) -> List[SearchQuery]:
        """
        Get active deal alerts to use as search queries
        
        Returns:
            List of SearchQuery objects from deal alerts
        """
        try:
            response = self.client.table('deal_alerts') \
                .select('*, categories(name, slug), stores(name), tags(name)') \
                .eq('is_active', True) \
                .execute()
            
            queries = []
            for alert in response.data:
                # Build search query from alert
                keyword_parts = []
                
                if alert.get('name'):
                    keyword_parts.append(alert['name'])
                
                if alert.get('categories') and alert['categories'].get('name'):
                    keyword_parts.append(alert['categories']['name'])
                
                if alert.get('tags') and alert['tags'].get('name'):
                    keyword_parts.append(alert['tags']['name'])
                
                if keyword_parts:
                    queries.append(SearchQuery(
                        keyword=" ".join(keyword_parts),
                        category_id=alert.get('category_id'),
                        category_name=alert.get('categories', {}).get('name') if alert.get('categories') else None,
                        min_price=None,
                        max_price=float(alert['max_price']) if alert.get('max_price') else None,
                        on_sale=True,
                        priority=1  # Deal alerts have priority
                    ))
            
            return queries
            
        except Exception as e:
            logger.error(f"Error fetching deal alerts: {e}")
            return []
    
    async def get_trending_keywords(self, limit: int = 20) -> List[str]:
        """
        Get trending keywords from recent popular deals
        
        Returns:
            List of keyword strings
        """
        try:
            # Get recent popular deals
            response = self.client.table('deals') \
                .select('title') \
                .eq('status', 'approved') \
                .order('click_count', desc=True) \
                .order('votes_total', desc=True) \
                .limit(limit * 2) \
                .execute()
            
            # Extract keywords from titles
            keywords = set()
            stop_words = {'ve', 'ile', 'için', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'}
            
            for deal in response.data:
                title = deal.get('title', '')
                # Simple keyword extraction - take words longer than 3 chars
                words = title.split()
                for word in words:
                    clean_word = word.strip('.,!?()[]{}').lower()
                    if len(clean_word) > 3 and clean_word not in stop_words:
                        keywords.add(clean_word)
            
            return list(keywords)[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching trending keywords: {e}")
            return []
    
    async def get_or_create_store(self, store_name: str) -> Optional[str]:
        """
        Get store ID by name, or create if doesn't exist
        
        Args:
            store_name: Name of the store
            
        Returns:
            Store UUID or None
        """
        try:
            # Normalize store name
            normalized_name = store_name.strip()
            slug = normalized_name.lower().replace(' ', '-').replace('.', '')
            
            # Check if store exists
            response = self.client.table('stores') \
                .select('id') \
                .eq('name', normalized_name) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            
            # Create new store
            response = self.client.table('stores') \
                .insert({
                    'name': normalized_name,
                    'slug': slug,
                    'is_active': True
                }) \
                .execute()
            
            if response.data:
                logger.info(f"Created new store: {normalized_name}")
                return response.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating store {store_name}: {e}")
            return None
    
    async def check_deal_exists(self, product_id: str) -> bool:
        """
        Check if a deal already exists for this product
        
        Args:
            product_id: Google Shopping product ID
            
        Returns:
            True if deal exists
        """
        try:
            # Check by product_id in affiliate_url or title
            response = self.client.table('deals') \
                .select('id') \
                .ilike('affiliate_url', f'%{product_id}%') \
                .limit(1) \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking deal existence: {e}")
            return False
    
    async def create_deal(self, deal: DealToCreate) -> Optional[str]:
        """
        Create a new deal in the database
        
        Args:
            deal: Deal data to insert
            
        Returns:
            Created deal UUID or None
        """
        try:
            # Generate slug from title
            import re
            import uuid
            
            slug_base = re.sub(r'[^a-z0-9]+', '-', deal.title.lower())
            slug = f"{slug_base[:50]}-{uuid.uuid4().hex[:8]}"
            
            data = deal.to_dict()
            data['slug'] = slug
            
            response = self.client.table('deals') \
                .insert(data) \
                .execute()
            
            if response.data:
                logger.info(f"Created deal: {deal.title}")
                return response.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return None
    
    async def get_category_by_name(self, name: str) -> Optional[str]:
        """
        Get category ID by name
        
        Args:
            name: Category name
            
        Returns:
            Category UUID or None
        """
        try:
            response = self.client.table('categories') \
                .select('id') \
                .ilike('name', f'%{name}%') \
                .limit(1) \
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
            
        except Exception as e:
            logger.error(f"Error getting category: {e}")
            return None
