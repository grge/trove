#!/usr/bin/env python3
"""
Search for variant names to verify if Bertie is distinct person or nickname
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient

def verify_bertie_variants():
    client = TroveClient.from_env()
    
    search_terms = [
        '"Bertie Dickeson"',
        '"Albert Dickeson"',
        '"Bert Dickeson"',
        'Bertie Dickeson',
        'Albert Mark Dickeson',
    ]
    
    print("\n" + "="*80)
    print("TESTING VARIANT NAMES - BERTIE/ALBERT")
    print("="*80 + "\n")
    
    with client:
        for term in search_terms:
            search = (client.search()
                     .text(term)
                     .in_("newspaper")
                     .sort_by("date_asc"))
            
            try:
                total = search.count()
                print(f"Search: {term:35} → {total:3d} results")
            except Exception as e:
                print(f"Search: {term:35} → ERROR: {str(e)[:40]}")

if __name__ == "__main__":
    verify_bertie_variants()
