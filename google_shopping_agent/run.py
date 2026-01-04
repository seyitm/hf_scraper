#!/usr/bin/env python3
"""
CLI runner for Google Shopping Agent

Usage:
    python run.py
    python run.py --max-queries 30 --min-discount 20
    python run.py --dry-run
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('google_shopping_agent.log')
        ]
    )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Google Shopping Agent for harbifırsat'
    )
    
    parser.add_argument(
        '--max-queries',
        type=int,
        default=20,
        help='Maximum number of search queries to process (default: 20)'
    )
    
    parser.add_argument(
        '--min-discount',
        type=float,
        default=10.0,
        help='Minimum discount percentage to consider (default: 10.0)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating deals in database'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--category',
        type=str,
        help='Search only in specific category'
    )
    
    parser.add_argument(
        '--keyword',
        type=str,
        help='Search for specific keyword only'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Google Shopping Agent for harbifırsat")
    logger.info("=" * 60)
    logger.info(f"Max queries: {args.max_queries}")
    logger.info(f"Min discount: {args.min_discount}%")
    logger.info(f"Dry run: {args.dry_run}")
    
    if args.dry_run:
        logger.warning("DRY RUN MODE - No deals will be created")
    
    try:
        from google_shopping_agent import GoogleShoppingAgent, SearchQuery
        
        agent = GoogleShoppingAgent()
        
        # If specific keyword provided, use that
        if args.keyword:
            from google_shopping_agent import SerpApiClient
            
            logger.info(f"Searching for specific keyword: {args.keyword}")
            
            query = SearchQuery(
                keyword=args.keyword,
                on_sale=True
            )
            
            async with SerpApiClient(agent.config.serp_api) as client:
                products = await client.search_with_discount_filter(
                    query,
                    min_discount=args.min_discount
                )
                
                logger.info(f"Found {len(products)} products with discounts")
                
                for i, product in enumerate(products[:10], 1):
                    logger.info(f"\n{i}. {product.title}")
                    logger.info(f"   Price: ${product.price}")
                    if product.original_price:
                        logger.info(f"   Original: ${product.original_price}")
                    if product.discount_percentage:
                        logger.info(f"   Discount: {product.discount_percentage}%")
                    logger.info(f"   Source: {product.source}")
                    
                    if not args.dry_run and product.product_link:
                        # Create deal
                        agent.supabase.connect()
                        await agent.process_products([product])
        
        else:
            # Run full agent
            result = await agent.run(
                max_queries=args.max_queries,
                min_discount=args.min_discount
            )
            
            # Print summary
            print("\n" + "=" * 60)
            print("EXECUTION SUMMARY")
            print("=" * 60)
            print(f"Queries processed: {result.search_queries_processed}")
            print(f"Products found: {result.products_found}")
            print(f"Products with discount: {result.products_with_discount}")
            print(f"Deals created: {result.deals_created}")
            
            if result.errors:
                print(f"\nErrors ({len(result.errors)}):")
                for error in result.errors[:5]:
                    print(f"  - {error}")
            
            print("=" * 60)
            
            return 0 if result.success else 1
            
    except Exception as e:
        logger.exception(f"Agent failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
