"""
Google Shopping Agent for HarbiFırsat

Google Shopping üzerinden indirimli ürün arayan ve
HarbiFırsat platformuna gönderen agent.

Usage:
    from google_shopping_agent import GoogleShoppingAgent, run_agent
    
    # Async usage
    result = await run_agent(max_queries=20, min_discount=15.0)
    
    # Or with custom config
    agent = GoogleShoppingAgent(config)
    result = await agent.run()
"""

from config import AgentConfig, SerpApiConfig, SupabaseConfig, load_config
from models import (
    ShoppingProduct,
    SearchQuery,
    DealToCreate,
    AgentResult,
    DealStatus
)
from serp_api_client import SerpApiClient
from supabase_client import HarbiSupabaseClient
from agent import GoogleShoppingAgent, run_agent

__all__ = [
    # Config
    "AgentConfig",
    "SerpApiConfig", 
    "SupabaseConfig",
    "load_config",
    
    # Models
    "ShoppingProduct",
    "SearchQuery",
    "DealToCreate",
    "AgentResult",
    "DealStatus",
    
    # Clients
    "SerpApiClient",
    "HarbiSupabaseClient",
    
    # Agent
    "GoogleShoppingAgent",
    "run_agent",
]

__version__ = "2.0.0"
