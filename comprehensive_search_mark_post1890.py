#!/usr/bin/env python3
"""
Systematic search for Mark Dickeson POST-1890
Looking for death records, Adelaide activity, business recovery
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def search_mark_post1890():
    client = TroveClient.from_env()
    
    search_term = '"Mark Dickeson"'
    print(f"\n{'='*80}")
    print(f"MARK DICKESON - POST-1890 SEARCH")
    print(f"Search term: {search_term}")
    print(f"Scope: 1890 onwards (death records, Adelaide activity)")
    print(f"{'='*80}\n")
    
    with client:
        search = (client.search()
                 .text(search_term)
                 .in_("newspaper")
                 .sort_by("date_asc")
                 .page_size(100))
        
        total_results = search.count()
        print(f"Total results (all years): {total_results}\n")
        
        article_count = 0
        pre_1890_count = 0
        reviewed_articles = []
        
        for page_num, page in enumerate(search.pages(), 1):
            print(f"\n--- PAGE {page_num} ---\n")
            
            for category in page.categories:
                if 'records' in category and 'article' in category['records']:
                    articles = category['records']['article']
                    
                    for article in articles:
                        date = article.get('date', 'unknown')
                        
                        # Count pre-1890 vs post-1890
                        if date and len(date) >= 4:
                            year = int(date[:4])
                            if year < 1890:
                                pre_1890_count += 1
                                continue  # Skip pre-1890, already reviewed
                        
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
        
        print(f"\n{'='*80}")
        print(f"Summary:")
        print(f"  Pre-1890 articles (already reviewed): {pre_1890_count}")
        print(f"  Post-1890 articles (new): {article_count}")
        print(f"  Total: {pre_1890_count + article_count}")
        print(f"{'='*80}\n")
        
        # Save results
        output_file = Path(__file__).parent / "mark_dickeson_post1890_results.json"
        with open(output_file, 'w') as f:
            json.dump(reviewed_articles, f, indent=2, default=str)
        print(f"✓ Post-1890 results saved to: {output_file}")
        
        return reviewed_articles

if __name__ == "__main__":
    search_mark_post1890()
