#!/usr/bin/env python3
"""
Search for records George found that I missed:
1. Dairy advertising near Rising Sun Hotel Melbourne
2. Death notice 1916 Adelaide Advertiser (Norwood)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def search_missed_records():
    client = TroveClient.from_env()
    
    search_terms = [
        '"Mark Dickeson" dairy',
        '"Mark Dickeson" "rising sun"',
        '"Mark Dickeson" Adelaide 1916',
        '"Mark Dickeson" Norwood',
        '"Mark Dickeson" death 1916',
        'Mark Dickeson dairy Melbourne',
    ]
    
    print(f"\n{'='*80}")
    print(f"SEARCHING FOR MISSED RECORDS")
    print(f"{'='*80}\n")
    
    all_results = []
    
    with client:
        for search_term in search_terms:
            print(f"\nSearch: {search_term}")
            search = (client.search()
                     .text(search_term)
                     .in_("newspaper")
                     .sort_by("date_asc")
                     .page_size(50))
            
            try:
                total = search.count()
                print(f"  Results: {total}")
                
                if total > 0:
                    for page_num, page in enumerate(search.pages(), 1):
                        for category in page.categories:
                            if 'records' in category and 'article' in category['records']:
                                articles = category['records']['article']
                                
                                for article in articles:
                                    date = article.get('date', 'unknown')
                                    article_id = article.get('id', 'unknown')
                                    title = article.get('heading', 'unknown')[:100]
                                    
                                    article_resource = client.resources.get_newspaper_resource()
                                    full_text = article_resource.get_full_text(article_id)
                                    
                                    record = {
                                        'search_term': search_term,
                                        'date': date,
                                        'title': title,
                                        'id': article_id,
                                        'url': f'https://trove.nla.gov.au/newspaper/article/{article_id}',
                                        'text': full_text[:500] if full_text else '[No text]'
                                    }
                                    all_results.append(record)
                                    
                                    print(f"    [{date}] {title}")
                                    print(f"      ID: {article_id}")
                        
                        if total > 50:
                            print(f"    (showing first page, {total} total)")
                            break
                            
            except Exception as e:
                print(f"  ERROR: {str(e)[:50]}")
    
    # Save results
    output_file = Path(__file__).parent / "missed_records_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Total new articles found: {len(all_results)}")
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    search_missed_records()
