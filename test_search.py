#!/usr/bin/env python3
"""
Quick test to demonstrate Trove search functionality.
"""

import sys
sys.path.insert(0, 'packages/trove-sdk')

from trove import TroveClient

def main():
    """Test basic search functionality."""
    print("Testing Trove SDK search functionality...")
    
    # Initialize client from environment
    client = TroveClient.from_env()
    
    try:
        with client:
            # Search for Alice Springs history
            print("\n🏜️ Searching for 'Alice Springs' in newspapers...")
            results = (client.search()
                      .text("Alice Springs")
                      .in_("newspaper")
                      .australian_content()
                      .page_size(5)
                      .first_page())
            
            if results.total_results > 0:
                print(f"Found {results.total_results} total newspaper articles about Alice Springs!")
                
                # Get the newspaper category
                for category in results.categories:
                    if category['category'] == 'newspaper':
                        articles = category['records'].get('article', [])
                        print(f"\nFirst {len(articles)} results:")
                        
                        for i, article in enumerate(articles[:3], 1):
                            title = article.get('heading', 'Unknown Title')
                            date = article.get('date', 'Unknown Date') 
                            newspaper = article.get('title', {}).get('value', 'Unknown Paper') if isinstance(article.get('title'), dict) else 'Unknown Paper'
                            print(f"{i}. {title}")
                            print(f"   📅 {date} | 📰 {newspaper}")
                            print()
            
            # Test another search - Australian history books
            print("📚 Searching for 'Australian history' books...")
            results = (client.search()
                      .text("Australian history") 
                      .in_("book")
                      .online()  # Only books with online access
                      .page_size(3)
                      .first_page())
            
            print(f"Found {results.total_results} books with online access!")
            
            for category in results.categories:
                if category['category'] == 'book':
                    books = category['records'].get('work', [])
                    for i, book in enumerate(books[:3], 1):
                        title = book.get('title', 'Unknown Title')
                        print(f"{i}. {title}")
                        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    print("\n✅ Trove SDK is working perfectly!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)