#!/usr/bin/env python3
"""
Comprehensive pagination through all "Mark Dickeson" results with full text extraction.
When Trove API is available, this will retrieve all articles and extract full text.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json

def paginate_all_results():
    """Paginate through all Mark Dickeson results and extract full text"""
    
    client = TroveClient.from_env()
    
    search = (client.search()
        .text('"Mark Dickeson"')
        .in_("newspaper")
        .sort_by("date_asc")
        .page_size(20))
    
    with client:
        total = search.count()
        print(f"Total 'Mark Dickeson' results: {total}\n")
        print("="*100)
        
        all_articles = []
        page_num = 0
        article_count = 0
        
        for page in search.pages():
            page_num += 1
            print(f"\n>>> PAGE {page_num}")
            print("="*100)
            
            for category in page.categories:
                if 'records' in category and 'article' in category['records']:
                    articles = category['records']['article']
                    
                    for article in articles:
                        article_count += 1
                        
                        date = article.get('date', 'unknown')
                        article_id = article.get('id', 'unknown')
                        title = article.get('heading', 'unknown')
                        snippet = article.get('snippet', '[no snippet]')
                        url = f"https://trove.nla.gov.au/newspaper/article/{article_id}"
                        
                        # Try to get full text
                        try:
                            newspaper_resource = client.resources.get_newspaper_resource()
                            full_text = newspaper_resource.get_full_text(article_id)
                        except Exception as e:
                            full_text = f"[Error extracting full text: {str(e)[:50]}]"
                        
                        # Detect what type of record this is
                        record_type = "unknown"
                        if "death" in title.lower() or "obituary" in title.lower():
                            record_type = "death"
                        elif "market" in title.lower() or "dairy" in title.lower() or "advertising" in title.lower():
                            record_type = "advertising"
                        elif "insolv" in title.lower() or "bankrup" in title.lower():
                            record_type = "insolvency"
                        elif "court" in title.lower():
                            record_type = "court"
                        elif "notice" in title.lower():
                            record_type = "notice"
                        
                        article_data = {
                            'num': article_count,
                            'date': date,
                            'id': article_id,
                            'url': url,
                            'title': title,
                            'snippet': snippet[:200],
                            'record_type': record_type,
                            'full_text_preview': (full_text[:300] if full_text else '[empty]')
                        }
                        
                        all_articles.append(article_data)
                        
                        # Print to stdout for browsing
                        print(f"\n[{article_count}] {date} | ID: {article_id}")
                        print(f"    Type: {record_type}")
                        print(f"    Title: {title}")
                        print(f"    Snippet: {snippet[:150]}")
                        
                        # Highlight interesting records
                        if record_type in ["death", "advertising"]:
                            print(f"    *** POTENTIAL MATCH ***")
                            print(f"    Full text preview: {full_text[:200]}")
        
        # Save to JSON for detailed analysis
        output_file = Path(__file__).parent / "mark_dickeson_all_results.json"
        with open(output_file, 'w') as f:
            json.dump(all_articles, f, indent=2, default=str)
        
        print(f"\n\n{'='*100}")
        print(f"SUMMARY")
        print(f"{'='*100}")
        print(f"Total articles found: {article_count}")
        print(f"Total pages: {page_num}")
        print(f"Results saved to: {output_file}")
        
        # Show breakdown by type
        by_type = {}
        for article in all_articles:
            rt = article.get('record_type', 'unknown')
            by_type[rt] = by_type.get(rt, 0) + 1
        
        print(f"\nBreakdown by type:")
        for record_type, count in sorted(by_type.items()):
            print(f"  {record_type}: {count}")
        
        # Highlight potential matches
        potential_matches = [a for a in all_articles if a.get('record_type') in ['death', 'advertising']]
        if potential_matches:
            print(f"\nPotential matches (death/advertising records):")
            for article in potential_matches:
                print(f"  [{article['date']}] {article['id']}: {article['title']}")

if __name__ == "__main__":
    paginate_all_results()
