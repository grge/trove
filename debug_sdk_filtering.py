#!/usr/bin/env python3
"""
Debug script to check what the SDK receives from Trove API
vs. what it returns to us.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient
from trove.params import SearchParameters, SortBy
import json

client = TroveClient.from_env()

target_ids = {"6457391", "40766865", "73247276"}

print("="*100)
print("SDK DEBUG: Intercepting what SDK receives from API")
print("="*100)

with client:
    search_resource = client.resources.get_search_resource()
    
    params = SearchParameters()
    params.q = '"Mark Dickeson"'
    params.category = ['newspaper']
    params.sortby = SortBy.DATE_ASC
    params.n = 50
    params.reclevel = 'brief'
    
    # Monkey-patch the _parse_search_response method to see raw data
    original_parse = search_resource._parse_search_response
    
    raw_data_received = []
    
    def debug_parse(response_data, params):
        """Wrapper that logs what we receive"""
        print(f"\n>>> RAW RESPONSE FROM API")
        print(f"    Response keys: {list(response_data.keys())}")
        
        if 'category' in response_data:
            categories = response_data['category']
            print(f"    Categories: {len(categories)}")
            
            for cat in categories:
                if cat.get('name') == 'newspaper':
                    records = cat.get('records', {})
                    article_list = records.get('article', [])
                    if not isinstance(article_list, list):
                        article_list = [article_list]
                    
                    print(f"    Newspaper zone: {len(article_list)} articles")
                    print(f"    First 5 article IDs in raw response:")
                    for i, article in enumerate(article_list[:5]):
                        print(f"      [{i+1}] {article.get('id')}")
                    
                    # Check for targets
                    found_in_raw = []
                    for article in article_list:
                        if article.get('id') in target_ids:
                            found_in_raw.append(article.get('id'))
                    
                    if found_in_raw:
                        print(f"    ✓ TARGETS IN RAW RESPONSE: {found_in_raw}")
                    else:
                        print(f"    ✗ TARGETS NOT IN RAW RESPONSE")
                    
                    raw_data_received.append({
                        'total': len(article_list),
                        'found': found_in_raw
                    })
        
        # Call original method
        return original_parse(response_data, params)
    
    # Replace the method
    search_resource._parse_search_response = debug_parse
    
    # Now do the search
    try:
        result = search_resource.page(params=params)
        
        print(f"\n>>> AFTER SDK PROCESSING")
        print(f"    Total results reported: {result.total_results}")
        print(f"    Categories in result: {len(result.categories)}")
        
        for category in result.categories:
            if category.get('name') == 'newspaper':
                records = category.get('records', {})
                article_list = records.get('article', [])
                if not isinstance(article_list, list):
                    article_list = [article_list]
                
                print(f"    Articles in SDK result: {len(article_list)}")
                print(f"    First 5 article IDs in SDK result:")
                for i, article in enumerate(article_list[:5]):
                    print(f"      [{i+1}] {article.get('id')}")
                
                # Check for targets
                found_in_result = []
                for article in article_list:
                    if article.get('id') in target_ids:
                        found_in_result.append(article.get('id'))
                
                if found_in_result:
                    print(f"    ✓ TARGETS IN SDK RESULT: {found_in_result}")
                else:
                    print(f"    ✗ TARGETS NOT IN SDK RESULT")
        
        print(f"\n{'='*100}")
        print("ANALYSIS")
        print(f"{'='*100}")
        
        if raw_data_received:
            print(f"Raw API response had: {raw_data_received[0]['total']} articles")
            print(f"Targets in raw API: {raw_data_received[0]['found']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
