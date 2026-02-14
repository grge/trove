#!/usr/bin/env python3
"""
Check 1917 Bertie Dickeson article
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

from trove import TroveClient

client = TroveClient.from_env()

with client:
    article_resource = client.resources.get_newspaper_resource()
    text = article_resource.get_full_text("15741918")
    
    if text:
        print("1917 ARTICLE - BERTIE DICKESON:")
        print("="*80)
        print(text[:1500])
    else:
        print("No text available")
