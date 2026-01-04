"""
Configuration for Google Shopping Agent
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class SerpApiConfig:
    """SERP API Configuration"""
    api_key: str
    base_url: str = "https://serpapi.com/search"
    engine: str = "google_shopping"
    
    # Turkey-specific settings for harbifırsat
    country: str = "tr"  # gl parameter
    language: str = "tr"  # hl parameter
    google_domain: str = "google.com.tr"
    
    # Default search parameters
    default_num_results: int = 40
    timeout: int = 30


@dataclass
class SupabaseConfig:
    """Supabase Configuration"""
    url: str
    anon_key: str
    service_role_key: Optional[str] = None


@dataclass
class AgentConfig:
    """Main Agent Configuration"""
    serp_api: SerpApiConfig
    supabase: SupabaseConfig
    
    # Discount thresholds
    min_discount_percentage: float = 10.0  # Minimum discount to consider


def load_config() -> AgentConfig:
    """Load configuration from environment variables"""
    serp_api_key = os.environ.get("SERP_API_KEY")
    if not serp_api_key:
        raise ValueError("SERP_API_KEY environment variable is required")
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_anon_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
    
    return AgentConfig(
        serp_api=SerpApiConfig(api_key=serp_api_key),
        supabase=SupabaseConfig(
            url=supabase_url,
            anon_key=supabase_anon_key,
            service_role_key=supabase_service_key
        )
    )
