#!/usr/bin/env python3
"""
Comprehensive Dickeson Research Search
Systematically examine ALL results for Mark and Ambrose Dickeson pre-1890
"""
import sys
import asyncio
from pathlib import Path

# Add the trove-sdk to the path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import os

async def comprehensive_search():
    client = TroveClient.from_env()
    
    # Search terms to check comprehensively
    searches = [
        '"Mark Dickeson"',
        '"Ambrose Dickeson"'
    ]
    
    for search_term in searches:
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE SEARCH: {search_term}")
        print(f"{'='*60}")
        
        with client:
            # Build search with chronological sorting - filter dates manually
            search = (client.search()
                     .text(search_term)
                     .in_("newspaper")
                     .sort_by("date_asc")
                     .page_size(50))  # Get more results per page
            
            # Get total count first
            total_results = search.count()
            print(f"Total results for {search_term} pre-1890: {total_results}")
            print()
            
            # Iterate through all pages
            article_count = 0
            for page_num, page in enumerate(search.pages(), 1):
                print(f"--- PAGE {page_num} ---")
                
                for category in page.categories:
                    if 'records' in category and 'article' in category['records']:
                        articles = category['records']['article']
                        
                        for article in articles:
                            date = article.get('date', 'unknown')
                            
                            # Filter to pre-1890 only
                            if date and len(date) >= 4:
                                year = int(date[:4])
                                if year >= 1890:
                                    print(f"Reached 1890+ articles, stopping at: {date}")
                                    return
                            
                            article_count += 1
                            article_id = article.get('id', 'unknown')
                            title = article.get('heading', 'unknown')[:80]
                            
                            print(f"{article_count:2d}. {date} - {title}")
                            print(f"    ID: {article_id}")
                            print(f"    URL: https://trove.nla.gov.au/newspaper/article/{article_id}")
                            print()
                            
                            # Stop if we've found enough for manual review
                            if article_count >= 30:  # Reasonable limit for manual review
                                print("Reached 30 articles limit for manual review")
                                return
                                
                if not hasattr(page, 'categories') or not page.categories:
                    break

if __name__ == "__main__":
    asyncio.run(comprehensive_search())