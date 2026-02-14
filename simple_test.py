#!/usr/bin/env python3
"""
Simple test to demonstrate Trove SDK functionality.
"""

import sys
sys.path.insert(0, 'packages/trove-sdk')

from trove import TroveClient

def main():
    """Test basic search functionality."""
    print("🔍 Testing Trove API access...")
    
    client = TroveClient.from_env()
    
    with client:
        # Simple search test
        results = (client.search()
                  .text("Alice Springs")
                  .in_("newspaper")
                  .page_size(3)
                  .first_page())
        
        print(f"✅ SUCCESS! Found {results.total_results:,} newspaper articles mentioning Alice Springs")
        
        # Show what categories we got back
        print(f"📊 Response contains {len(results.categories)} categories")
        for cat in results.categories:
            print(f"   - Category: {cat.get('code', 'unknown')}")
            if 'records' in cat:
                for record_type, records in cat['records'].items():
                    if record_type != 'total':
                        print(f"     {record_type}: {len(records) if isinstance(records, list) else records} items")
        
        # Try a book search too
        print("\n📚 Testing book search...")
        book_results = (client.search()
                       .text("Australian history")
                       .in_("book")
                       .page_size(2)
                       .first_page())
        
        print(f"✅ Found {book_results.total_results:,} books about Australian history")
        
    print("\n🎉 Trove SDK is fully functional and ready to use!")

if __name__ == '__main__':
    main()