"""
Data models for Google Shopping Agent
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DealStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FLAGGED = "flagged"


@dataclass
class ShoppingProduct:
    """Represents a product from Google Shopping API"""
    title: str
    product_id: str
    source: str  # Store name
    price: float
    currency: str = "USD"
    
    # Optional fields
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    thumbnail: Optional[str] = None
    product_link: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    delivery_info: Optional[str] = None
    
    # Discount tag (e.g., "51% OFF")
    discount_tag: Optional[str] = None
    
    # Second hand condition
    condition: Optional[str] = None  # "pre-owned", "refurbished", etc.
    
    @property
    def has_discount(self) -> bool:
        """Check if product has a discount"""
        return (
            self.discount_percentage is not None and self.discount_percentage > 0
        ) or (
            self.original_price is not None and self.price < self.original_price
        ) or (
            self.discount_tag is not None
        )
    
    def calculate_discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if not provided"""
        if self.discount_percentage:
            return self.discount_percentage
        
        if self.original_price and self.original_price > self.price:
            return round(((self.original_price - self.price) / self.original_price) * 100, 2)
        
        # Try to extract from discount_tag
        if self.discount_tag:
            import re
            match = re.search(r'(\d+)%', self.discount_tag)
            if match:
                return float(match.group(1))
        
        return None


@dataclass
class SearchQuery:
    """Represents a search query with metadata"""
    keyword: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    priority: int = 0  # Higher = more important
    
    # Search filters
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    on_sale: bool = True  # Default to searching for discounted items
    sort_by: Optional[str] = None  # None=relevance, '1'=price low-high, '2'=price high-low
    min_rating: Optional[float] = None  # Minimum product rating (e.g., 4.0)
    
    # Metadata
    last_searched: Optional[datetime] = None
    search_count: int = 0


@dataclass
class DealToCreate:
    """Data structure for creating a new deal in Supabase"""
    title: str
    description: str
    original_price: float
    discounted_price: float
    discount_percentage: float
    currency: str
    affiliate_url: str
    image_url: Optional[str] = None
    
    # Foreign keys
    store_id: Optional[str] = None
    category_id: Optional[str] = None
    posted_by: Optional[str] = None
    
    # Status
    status: DealStatus = DealStatus.PENDING
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase insert"""
        return {
            "title": self.title,
            "description": self.description,
            "original_price": self.original_price,
            "discounted_price": self.discounted_price,
            "discount_percentage": self.discount_percentage,
            "currency": self.currency,
            "affiliate_url": self.affiliate_url,
            "image_url": self.image_url,
            "store_id": self.store_id,
            "category_id": self.category_id,
            "posted_by": self.posted_by,
            "status": self.status.value
        }


@dataclass
class AgentResult:
    """Result of agent execution"""
    success: bool
    products_found: int = 0
    products_with_discount: int = 0
    deals_created: int = 0
    errors: List[str] = field(default_factory=list)
    search_queries_processed: int = 0
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "products_found": self.products_found,
            "products_with_discount": self.products_with_discount,
            "deals_created": self.deals_created,
            "errors": self.errors,
            "search_queries_processed": self.search_queries_processed
        }
