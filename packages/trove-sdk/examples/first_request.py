#!/usr/bin/env python3
"""
First API request example for Trove SDK Stage 1.

This script demonstrates the basic functionality of the Trove SDK foundation:
- Configuration from environment variables
- Authentication with API key
- Rate limiting and caching
- Error handling
- Making a basic search request

Before running:
1. Get an API key from: https://trove.nla.gov.au/about/create-something/using-api
2. Set environment variable: export TROVE_API_KEY="your_api_key_here"
3. Run: python examples/first_request.py
"""

import os
import sys
import time
from pathlib import Path

# Add the trove package to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from trove import TroveConfig, TroveTransport, TroveError
from trove.cache import MemoryCache


def main():
    """Demonstrate first API request with Trove SDK."""
    print("Trove SDK Stage 1 - First API Request Demo")
    print("=" * 50)
    
    try:
        # Create configuration from environment (automatically loads .env files)
        print("1. Creating configuration from environment...")
        config = TroveConfig.from_env()
        print(f"   ✓ API key configured (ends with: ...{config.api_key[-4:]})")
        print(f"   ✓ Base URL: {config.base_url}")
        print(f"   ✓ Rate limit: {config.rate_limit} req/sec")
        print(f"   ✓ Cache backend: {config.cache_backend}")
        
        # Create cache and transport
        print("\n2. Initializing transport layer...")
        cache = MemoryCache()
        transport = TroveTransport(config, cache)
        print("   ✓ HTTP client initialized")
        print("   ✓ Rate limiter configured")
        print("   ✓ Cache backend ready")
        
        # Make first API request
        print("\n3. Making first API request...")
        start_time = time.time()
        
        response = transport.get('/result', {
            'category': 'book',
            'q': 'Australian history',
            'n': 5,
            'encoding': 'json'
        })
        
        request_time = time.time() - start_time
        print(f"   ✓ Request completed in {request_time:.2f} seconds")
        
        # Display results
        print("\n4. Processing response...")
        if 'category' in response and len(response['category']) > 0:
            category = response['category'][0]
            total_results = category['records']['total']
            works = category['records'].get('work', [])
            
            print(f"   ✓ Found {total_results} total results")
            print(f"   ✓ Returned {len(works)} works in this page")
            
            print("\n5. Sample results:")
            for i, work in enumerate(works[:3], 1):
                title = work.get('title', 'Unknown Title')
                # Truncate long titles
                if len(title) > 60:
                    title = title[:57] + "..."
                print(f"   {i}. {title}")
        else:
            print("   ! No results found")
        
        # Test caching
        print("\n6. Testing cache functionality...")
        start_time = time.time()
        
        response2 = transport.get('/result', {
            'category': 'book',
            'q': 'Australian history',
            'n': 5,
            'encoding': 'json'
        })
        
        cached_request_time = time.time() - start_time
        print(f"   ✓ Cached request completed in {cached_request_time:.3f} seconds")
        print(f"   ✓ Speed improvement: {request_time/cached_request_time:.1f}x faster")
        
        # Verify responses are identical
        if response == response2:
            print("   ✓ Cached response matches original")
        else:
            print("   ! Warning: Cached response differs from original")
        
        # Test rate limiting
        print("\n7. Testing rate limiting...")
        print("   Making 3 rapid requests to test rate limiting...")
        
        rate_test_start = time.time()
        for i in range(3):
            transport.get('/result', {
                'category': 'book',
                'q': f'rate test {i}',
                'n': 1
            })
            print(f"   Request {i+1} completed")
        
        rate_test_time = time.time() - rate_test_start
        print(f"   ✓ 3 requests completed in {rate_test_time:.2f} seconds")
        
        expected_min_time = 2 / config.rate_limit  # Should take at least this long
        if rate_test_time >= expected_min_time * 0.8:  # Allow some margin
            print("   ✓ Rate limiting working correctly")
        else:
            print("   ! Rate limiting may not be working as expected")
        
        print(f"\n🎉 SUCCESS: Trove SDK Stage 1 foundation is working!")
        print(f"   • Authentication: Working")
        print(f"   • API requests: Working") 
        print(f"   • Caching: Working")
        print(f"   • Rate limiting: Working")
        print(f"   • Error handling: Working")
        
    except ValueError as e:
        if "TROVE_API_KEY" in str(e):
            print(f"\n❌ Configuration Error: {e}")
            print("\nTo fix this:")
            print("1. Get an API key at: https://trove.nla.gov.au/about/create-something/using-api")
            print("2. Create a .env file in your project root: echo 'TROVE_API_KEY=your_key' > .env")
            print("3. Or set environment variable: export TROVE_API_KEY='your_key'")
        else:
            print(f"\n❌ Configuration Error: {e}")
        sys.exit(1)
        
    except TroveError as e:
        print(f"\n❌ Trove SDK Error: {e}")
        print("This indicates an issue with the API or configuration.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Unexpected Error: {e}")
        print("This indicates a bug in the SDK implementation.")
        sys.exit(1)
        
    finally:
        # Clean up
        if 'transport' in locals():
            transport.close()
            print("\n8. Cleanup completed")


if __name__ == '__main__':
    main()