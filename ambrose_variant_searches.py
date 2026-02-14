#!/usr/bin/env python3
"""
Try alternate searches for Ambrose Dickeson variants
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient

def try_variant_searches():
    client = TroveClient.from_env()
    
    # Try various search terms that might find Ambrose
    search_terms = [
        '"Ambrose Dickeson"',           # Exact phrase
        '"Ambrose Diekeson"',           # OCR variant 1
        '"Ambrose Dlekeson"',           # OCR variant 2
        '"Ambrose" "Dickeson"',         # Two terms
        'Ambrose Dickeson',             # Unquoted
        '"A. Dickeson" umbrella',       # Initial + surname
        '"A Dickeson" Melbourne',       # Variant format
    ]
    
    print(f"\n{'='*80}")
    print(f"AMBROSE DICKESON - VARIANT SEARCH TEST")
    print(f"{'='*80}\n")
    
    with client:
        for search_term in search_terms:
            search = (client.search()
                     .text(search_term)
                     .in_("newspaper")
                     .sort_by("date_asc"))
            
            try:
                total = search.count()
                print(f"Search: {search_term:40} → {total:3d} results")
            except Exception as e:
                print(f"Search: {search_term:40} → ERROR: {str(e)[:50]}")

if __name__ == "__main__":
    try_variant_searches()
