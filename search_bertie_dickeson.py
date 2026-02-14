#!/usr/bin/env python3
"""
Get full details on "Bertie Dickeson" results
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def search_bertie():
    client = TroveClient.from_env()
    
    search_term = '"Bertie Dickeson"'
    print(f"\n{'='*80}")
    print(f"SEARCH: {search_term}")
    print(f"{'='*80}\n")
    
    with client:
        search = (client.search()
                 .text(search_term)
                 .in_("newspaper")
                 .sort_by("date_asc")
                 .page_size(50))
        
        total_results = search.count()
        print(f"Total results: {total_results}\n")
        
        for page_num, page in enumerate(search.pages(), 1):
            for category in page.categories:
                if 'records' in category and 'article' in category['records']:
                    articles = category['records']['article']
                    
                    for i, article in enumerate(articles, 1):
                        date = article.get('date', 'unknown')
                        title = article.get('heading', 'untitled')[:100]
                        article_id = article.get('id', 'unknown')
                        
                        print(f"{i}. [{date}] {title}")
                        print(f"   ID: {article_id}")
                        print()

if __name__ == "__main__":
    search_bertie()
