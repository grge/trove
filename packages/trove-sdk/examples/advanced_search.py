#!/usr/bin/env python3
"""Advanced search examples demonstrating comprehensive Trove SDK functionality.

This example showcases all the advanced search features implemented in Stage 2:
- Complete parameter support (60+ parameters)
- Single and multi-category pagination
- Enhanced caching with statistics
- Parameter builders and validation
- Async operations

Before running:
    export TROVE_API_KEY=your_api_key_here
    
Or create .env file in project root:
    TROVE_API_KEY=your_api_key_here
"""

import asyncio
import os
from pathlib import Path
from trove import (
    TroveConfig, TroveTransport, SearchResource, SearchParameters, 
    ParameterBuilder, create_cache
)


def demonstrate_basic_search():
    """Demonstrate basic search functionality."""
    print("=== Basic Search Examples ===")
    
    # Setup
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Simple search
    print("\n1. Simple book search:")
    result = search.page(
        category=['book'],
        q='Australian history',
        n=5
    )
    print(f"Found {result.total_results} books about Australian history")
    if result.categories[0]['records']['work']:
        first_book = result.categories[0]['records']['work'][0]
        print(f"First result: {first_book.get('title', 'Untitled')}")
    
    # Multi-category search
    print("\n2. Multi-category search:")
    result = search.page(
        category=['book', 'image'],
        q='Sydney Harbour Bridge',
        n=3
    )
    print(f"Total results across categories: {result.total_results}")
    for category in result.categories:
        cat_total = category['records'].get('total', 0)
        print(f"  {category['name']}: {cat_total} results")
    
    transport.close()


def demonstrate_advanced_parameters():
    """Demonstrate advanced parameter usage."""
    print("\n=== Advanced Parameter Examples ===")
    
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Complex book search with multiple filters
    print("\n1. Complex book search with filters:")
    result = search.page(
        category=['book'],
        q='Australian literature',
        l_decade=['200'],  # 2000s
        l_availability=['y/f'],  # Free online
        l_australian='y',  # Australian content
        l_language=['English'],
        facet=['decade', 'format', 'language'],
        include=['tags', 'comments'],
        reclevel='full',
        n=10
    )
    print(f"Found {result.total_results} Australian literature books from 2000s")
    
    # Check facets
    if result.categories[0].get('facets', {}).get('facet'):
        print("Available facets:")
        for facet in result.categories[0]['facets']['facet']:
            print(f"  {facet['name']}: {len(facet.get('term', []))} values")
    
    # Newspaper search with dependencies
    print("\n2. Newspaper search with date dependencies:")
    try:
        result = search.page(
            category=['newspaper'],
            q='federation',
            l_decade=['190'],  # 1900s (required for newspapers)
            l_year=['1901'],   # Federation year
            l_month=['01'],    # January
            l_state=['NSW', 'VIC'],  # Multiple states
            l_artType=['newspaper'],  # Only newspapers, not gazettes
            l_illustrated=True,  # Only illustrated articles
            n=5
        )
        print(f"Found {result.total_results} illustrated newspaper articles about federation")
    except Exception as e:
        print(f"Search failed: {e}")
    
    # People search
    print("\n3. People search with biographical filters:")
    result = search.page(
        category=['people'],
        q='Australian authors',
        l_birth=['1850'],  # Born in 1850
        l_occupation=['Author', 'Writer'],
        l_place=['Sydney', 'Melbourne'],
        l_firstAustralians='y',  # First Australians content
        n=5
    )
    print(f"Found {result.total_results} Australian authors born in 1850")
    
    transport.close()


def demonstrate_parameter_builder():
    """Demonstrate fluent parameter builder."""
    print("\n=== Parameter Builder Examples ===")
    
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Using parameter builder for clean, readable code
    print("\n1. Fluent parameter building:")
    params = (search.build_params()
             .categories('book')
             .query('Australian poetry')
             .decade('200')
             .australian_content()
             .page_size(20)
             .record_level('full')
             .facets('decade', 'format', 'language')
             .include_fields('tags', 'comments', 'workversions')
             .build())
    
    result = search.page(params=params)
    print(f"Parameter builder search found {result.total_results} poetry books")
    
    # Complex newspaper search with builder
    print("\n2. Complex newspaper search with builder:")
    params = (ParameterBuilder()
             .categories('newspaper')
             .query('gold rush')
             .decade('185', '186')  # 1850s-1860s
             .state('VIC', 'NSW')
             .illustrated(True)
             .word_count('1000+ Words')  # Long articles only
             .sort('datedesc')  # Newest first
             .page_size(10)
             .build())
    
    result = search.page(params=params)
    print(f"Found {result.total_results} long illustrated gold rush articles")
    
    transport.close()


def demonstrate_pagination():
    """Demonstrate pagination features."""
    print("\n=== Pagination Examples ===")
    
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Single-category pagination
    print("\n1. Single-category page iteration:")
    page_count = 0
    total_records = 0
    
    for page in search.iter_pages(
        category=['book'],
        q='history',
        n=10
    ):
        page_count += 1
        records_in_page = len(page.categories[0]['records'].get('work', []))
        total_records += records_in_page
        print(f"Page {page_count}: {records_in_page} records")
        
        # Limit for demo
        if page_count >= 3:
            print(f"(Stopped after {page_count} pages for demo)")
            break
    
    print(f"Retrieved {total_records} total records from {page_count} pages")
    
    # Individual record iteration
    print("\n2. Individual record iteration:")
    record_count = 0
    
    for record in search.iter_records(
        category=['book'],
        q='Australian poetry',
        n=15
    ):
        record_count += 1
        title = record.get('title', 'Untitled')
        print(f"Record {record_count}: {title[:50]}...")
        
        # Limit for demo
        if record_count >= 20:
            print(f"(Stopped after {record_count} records for demo)")
            break
    
    # Multi-category pagination
    print("\n3. Multi-category pagination:")
    for category_code, page in search.iter_pages_by_category(
        category=['book', 'image'],
        q='Melbourne',
        n=5
    ):
        total = page.total_results
        records = len(page.categories[0]['records'].get(
            'work' if category_code in ['book', 'image'] else 'article', []
        ))
        print(f"{category_code}: {records} records on this page, {total} total")
        
        # Just show first page of each category for demo
        break
    
    transport.close()


def demonstrate_enhanced_caching():
    """Demonstrate enhanced caching with statistics."""
    print("\n=== Enhanced Caching Examples ===")
    
    config = TroveConfig.from_env()
    # Create enhanced cache with statistics
    cache = create_cache("memory", enhanced=True)
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    print("\n1. Cache statistics tracking:")
    
    # First search (cache miss)
    result1 = search.page(
        category=['book'],
        q='cache test query',
        n=5
    )
    print(f"First search: {result1.total_results} results")
    
    # Check initial stats
    if hasattr(cache, 'get_stats'):
        stats = cache.get_stats()
        print(f"Cache stats - Hits: {stats['hits']}, Misses: {stats['misses']}")
    
    # Identical search (cache hit)
    result2 = search.page(
        category=['book'],
        q='cache test query',  # Same query
        n=5
    )
    print(f"Second search: {result2.total_results} results")
    
    # Check updated stats
    if hasattr(cache, 'get_stats'):
        stats = cache.get_stats()
        print(f"Cache stats - Hits: {stats['hits']}, Misses: {stats['misses']}")
        print(f"Hit rate: {stats['hit_rate']:.2%}")
        print(f"Time saved: {stats['cache_savings_seconds']:.1f}s")
    
    # Different TTL examples
    print("\n2. Different caching behavior:")
    
    # Small result set (short TTL)
    small_result = search.page(
        category=['book'],
        q='very specific unique query xyz123',
        n=5
    )
    print(f"Small result set: {small_result.total_results} results (short TTL)")
    
    # Historical search (long TTL)  
    historical_result = search.page(
        category=['book'],
        q='history',
        l_decade=['180'],  # 1800s - historical data
        n=5
    )
    print(f"Historical search: {historical_result.total_results} results (long TTL)")
    
    # Bulk harvest (longest TTL)
    bulk_result = search.page(
        category=['book'],
        q='*',
        l_australian='y',
        bulkHarvest=True,
        n=10
    )
    print(f"Bulk harvest: {bulk_result.total_results} results (longest TTL)")
    
    # Final stats
    if hasattr(cache, 'get_stats'):
        stats = cache.get_stats()
        print(f"\nFinal cache statistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Search requests: {stats['search_requests']}")
        print(f"  Hit rate: {stats['hit_rate']:.2%}")
        print(f"  Time saved: {stats['cache_savings_seconds']:.1f}s")
    
    transport.close()


async def demonstrate_async_operations():
    """Demonstrate async search operations."""
    print("\n=== Async Operations Examples ===")
    
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Async single search
    print("\n1. Async search:")
    result = await search.apage(
        category=['book'],
        q='async search test',
        n=5
    )
    print(f"Async search found {result.total_results} results")
    
    # Async pagination
    print("\n2. Async pagination:")
    page_count = 0
    async for page in search.aiter_pages(
        category=['book'],
        q='literature',
        n=8
    ):
        page_count += 1
        records = len(page.categories[0]['records'].get('work', []))
        print(f"Async page {page_count}: {records} records")
        
        if page_count >= 2:  # Limit for demo
            break
    
    # Async record iteration
    print("\n3. Async record iteration:")
    record_count = 0
    async for record in search.aiter_records(
        category=['book'], 
        q='poetry',
        n=10
    ):
        record_count += 1
        title = record.get('title', 'Untitled')
        print(f"Async record {record_count}: {title[:40]}...")
        
        if record_count >= 15:  # Limit for demo
            break
    
    await transport.aclose()


def demonstrate_error_handling():
    """Demonstrate error handling and validation."""
    print("\n=== Error Handling Examples ===")
    
    config = TroveConfig.from_env()
    cache = create_cache("memory")
    transport = TroveTransport(config, cache)
    search = SearchResource(transport)
    
    # Parameter validation errors
    print("\n1. Parameter validation:")
    
    try:
        # Missing required category
        search.page(q='test query')
    except ValueError as e:
        print(f"Missing category error: {e}")
    
    try:
        # Invalid category
        search.page(category=['invalid_category'], q='test')
    except ValueError as e:
        print(f"Invalid category error: {e}")
    
    try:
        # Parameter dependency violation
        search.page(
            category=['newspaper'],
            l_month=['03']  # Month without year
        )
    except ValueError as e:
        print(f"Parameter dependency error: {e}")
    
    try:
        # Newspaper year without decade
        search.page(
            category=['newspaper'],
            l_year=['2015']  # Year without decade for newspapers
        )
    except ValueError as e:
        print(f"Newspaper dependency error: {e}")
    
    # Pagination errors
    print("\n2. Pagination validation:")
    
    try:
        # Multi-category pagination not supported for iter_pages
        list(search.iter_pages(
            category=['book', 'image'],
            q='test'
        ))
    except Exception as e:
        print(f"Multi-category pagination error: {e}")
    
    # Valid search after errors
    print("\n3. Valid search after handling errors:")
    result = search.page(
        category=['book'],
        q='error handling test',
        n=3
    )
    print(f"Valid search successful: {result.total_results} results")
    
    transport.close()


def main():
    """Run all examples."""
    print("Trove SDK Advanced Search Examples")
    print("=" * 50)
    
    # Check for API key
    if not os.environ.get('TROVE_API_KEY'):
        print("Error: TROVE_API_KEY environment variable not set")
        print("Please set your API key:")
        print("  export TROVE_API_KEY=your_api_key_here")
        return
    
    try:
        # Run sync examples
        demonstrate_basic_search()
        demonstrate_advanced_parameters()
        demonstrate_parameter_builder()
        demonstrate_pagination()
        demonstrate_enhanced_caching()
        demonstrate_error_handling()
        
        # Run async examples
        print("\n" + "=" * 50)
        asyncio.run(demonstrate_async_operations())
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nFor more information, see:")
        print("- API documentation: https://trove.nla.gov.au/about/create-something/using-api")
        print("- SDK documentation in README.md")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\nExample failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()