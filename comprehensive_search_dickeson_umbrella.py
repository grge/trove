#!/usr/bin/env python3
"""
Systematic search for Dickeson umbrella (two words, unquoted)
Looking for business records and references to the umbrella trade
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def search_dickeson_umbrella():
    client = TroveClient.from_env()
    
    search_term = 'Dickeson umbrella'
    print(f"\n{'='*80}")
    print(f"SEARCH: {search_term} (unquoted, two words)")
    print(f"Scope: Pre-1890 only")
    print(f"{'='*80}\n")
    
    with client:
        search = (client.search()
                 .text(search_term)
                 .in_("newspaper")
                 .sort_by("date_asc")
                 .page_size(100))
        
        total_results = search.count()
        print(f"Total results: {total_results}\n")
        
        article_count = 0
        reviewed_articles = []
        
        for page_num, page in enumerate(search.pages(), 1):
            print(f"\n--- PAGE {page_num} ---\n")
            
            for category in page.categories:
                if 'records' in category and 'article' in category['records']:
                    articles = category['records']['article']
                    
                    for article in articles:
                        date = article.get('date', 'unknown')
                        
                        # Stop at 1890+ (post-scope)
                        if date and len(date) >= 4:
                            year = int(date[:4])
                            if year >= 1890:
                                print(f"\n✓ Reached 1890+ scope boundary at {date}")
                                print(f"✓ Total articles reviewed: {article_count}\n")
                                
                                # Save results
                                output_file = Path(__file__).parent / "dickeson_umbrella_results.json"
                                with open(output_file, 'w') as f:
                                    json.dump(reviewed_articles, f, indent=2, default=str)
                                print(f"✓ Results saved to: {output_file}")
                                return reviewed_articles
                        
                        article_count += 1
                        article_id = article.get('id', 'unknown')
                        title = article.get('heading', 'untitled')[:100]
                        
                        # Fetch full text using SDK
                        article_resource = client.resources.get_newspaper_resource()
                        full_text = article_resource.get_full_text(article_id)
                        
                        if full_text:
                            text = full_text if len(full_text) <= 500 else full_text[:500] + "..."
                        else:
                            text = "[Full text not available]"
                        
                        record = {
                            'id': article_id,
                            'date': date,
                            'title': title,
                            'text_snippet': text,
                            'url': f'https://trove.nla.gov.au/newspaper/article/{article_id}',
                            'review_status': 'pending'
                        }
                        reviewed_articles.append(record)
                        
                        print(f"{article_count:2d}. [{date}] {title}")
                        print(f"    ID: {article_id}")
                        if text and text != "[Full text not available]":
                            print(f"    Text: {text[:200]}...")
                        print()

if __name__ == "__main__":
    search_dickeson_umbrella()
