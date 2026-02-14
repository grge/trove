#!/usr/bin/env python3
"""
Extract and analyze specific article IDs from Mark Dickeson research.
Usage: ./extract_specific_ids.py <id1> <id2> <id3> ...
or pass via stdin/file
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
import json
from datetime import datetime

def extract_articles(article_ids):
    """Extract full text and metadata for specific article IDs"""
    
    client = TroveClient.from_env()
    
    results = []
    
    print(f"\nExtracting {len(article_ids)} articles...\n")
    print("="*100)
    
    with client:
        newspaper_resource = client.resources.get_newspaper_resource()
        
        for idx, article_id in enumerate(article_ids, 1):
            article_id = article_id.strip()
            if not article_id:
                continue
            
            print(f"\n[{idx}] Extracting ID: {article_id}")
            
            try:
                # Get metadata
                article_metadata = newspaper_resource.get_article(article_id)
                
                # Get full text
                full_text = newspaper_resource.get_full_text(article_id)
                
                date = article_metadata.get('date', 'unknown')
                title = article_metadata.get('heading', 'unknown')
                url = f"https://trove.nla.gov.au/newspaper/article/{article_id}"
                
                article_data = {
                    'id': article_id,
                    'date': date,
                    'title': title,
                    'url': url,
                    'text_length': len(full_text) if full_text else 0,
                    'full_text': full_text,
                    'extracted_at': datetime.now().isoformat()
                }
                
                results.append(article_data)
                
                print(f"  Date: {date}")
                print(f"  Title: {title}")
                print(f"  Text length: {len(full_text)} chars")
                print(f"  Preview: {full_text[:150]}...")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                results.append({
                    'id': article_id,
                    'error': str(e),
                    'extracted_at': datetime.now().isoformat()
                })
    
    # Save results
    output_file = Path(__file__).parent / "extracted_articles.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*100}")
    print(f"Successfully extracted: {len([r for r in results if 'error' not in r])} articles")
    print(f"Failed: {len([r for r in results if 'error' in r])} articles")
    print(f"Results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    # Get article IDs from command line
    if len(sys.argv) > 1:
        article_ids = sys.argv[1:]
    else:
        print("Usage: ./extract_specific_ids.py <id1> <id2> <id3> ...")
        print("Example: ./extract_specific_ids.py 206520274 87311094 90911670")
        sys.exit(1)
    
    extract_articles(article_ids)
