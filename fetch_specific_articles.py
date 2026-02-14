#!/usr/bin/env python3
"""
Fetch specific Trove articles with full text extraction
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def fetch_articles():
    client = TroveClient.from_env()
    
    # Search for the missing records - dairy and death notice
    search_terms = [
        ('Mark Dickeson', 'dairy', 'Melbourne'),
        ('Mark Dickeson', 'Rising Sun Hotel'),
        ('Mark Dickeson', '1916', 'Norwood'),
        ('Mark Dickeson', '1916', 'death', 'Adelaide'),
    ]
    
    results = []
    
    with client:
        for search_query in search_terms:
            search_text = ' '.join(search_query)
            print(f"\nSearching: {search_text}")
            
            search = (client.search()
                     .text(search_text)
                     .in_("newspaper")
                     .sort_by("date_asc")
                     .page_size(50))
            
            try:
                count = search.count()
                print(f"Found {count} results")
                
                article_resource = client.resources.get_newspaper_resource()
                
                page_count = 0
                for page in search.pages():
                    page_count += 1
                    print(f"  Page {page_count}")
                    
                    for category in page.categories:
                        if 'records' in category and 'article' in category['records']:
                            articles = category['records']['article']
                            
                            for article in articles:
                                article_id = article.get('id')
                                date = article.get('date')
                                title = article.get('heading', '')[:150]
                                
                                # Get full text
                                try:
                                    full_text = article_resource.get_full_text(article_id)
                                    print(f"    [{date}] {title}")
                                    print(f"      ID: {article_id}, Text length: {len(full_text) if full_text else 0}")
                                except Exception as e:
                                    print(f"    Error fetching text for {article_id}: {str(e)[:50]}")
                                    full_text = None
                                
                                record = {
                                    'search_terms': search_query,
                                    'date': date,
                                    'title': title,
                                    'id': article_id,
                                    'url': f'https://trove.nla.gov.au/newspaper/article/{article_id}',
                                    'full_text': full_text
                                }
                                results.append(record)
                    
                    if page_count >= 2:  # Check first 2 pages
                        break
                        
            except Exception as e:
                print(f"  Search error: {str(e)[:100]}")
    
    # Save results
    output_file = Path(__file__).parent / "missing_articles_with_fulltext.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to: {output_file}")
    print(f"✓ Found {len(results)} articles")
    return results

if __name__ == "__main__":
    fetch_articles()
