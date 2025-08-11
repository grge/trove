#!/usr/bin/env python3
"""Examples demonstrating the ergonomic search interface.

This script shows various ways to use the fluent search API for common
research workflows.
"""

import asyncio
from trove import TroveClient


def basic_search_example():
    """Basic search example."""
    print("=== Basic Search Example ===")
    client = TroveClient.from_env()
    
    # Simple search
    result = (client.search()
             .text("Australian poetry")
             .in_("book")
             .page_size(10)
             .first_page())
    
    print(f"Found {result.total_results} results")
    
    # Access records from the first category
    if result.categories:
        category = result.categories[0]
        records = category.get('records', {})
        works = records.get('work', [])
        
        print("\nFirst few results:")
        for i, work in enumerate(works[:5]):
            title = work.get('title', 'Untitled')
            date = work.get('date', 'Unknown date')
            print(f"{i+1}. {title} ({date})")
    
    client.close()


def filtered_search_example():
    """Advanced filtering example."""
    print("\n=== Filtered Search Example ===")
    client = TroveClient.from_env()
    
    # Complex search with multiple filters
    search = (client.search()
             .text("federation")
             .in_("newspaper")
             .decade("190")  # 1900s
             .state("NSW", "VIC")  # NSW and Victoria
             .illustrated()
             .sort_by("date_desc")
             .with_facets("year", "title"))
             
    print("Search explanation:")
    explanation = search.explain()
    print(f"  Categories: {explanation['categories']}")
    print(f"  Query: {explanation['query']}")
    print(f"  Filters: {len(explanation['filters'])} filters applied")
    for filter_info in explanation['filters']:
        print(f"    - {filter_info['param']}: {filter_info['values']}")
    
    result = search.first_page()
    print(f"\nFound {result.total_results} articles")
    
    # Show facet information
    if result.categories and 'facets' in result.categories[0]:
        facets_data = result.categories[0]['facets']
        if 'facet' in facets_data:
            facet_list = facets_data['facet']
            if isinstance(facet_list, dict):
                facet_list = [facet_list]
            
            print("\nAvailable facets:")
            for facet in facet_list:
                facet_name = facet.get('name', 'Unknown')
                terms = facet.get('term', [])
                if isinstance(terms, dict):
                    terms = [terms]
                print(f"  {facet_name}: {len(terms)} values")
                
                # Show top few values
                for term in terms[:3]:
                    display = term.get('display', term.get('search', 'Unknown'))
                    count = term.get('count', 0)
                    print(f"    - {display} ({count})")
    
    client.close()


def research_workflow_example():
    """Research workflow example."""
    print("\n=== Research Workflow Example ===")
    client = TroveClient.from_env()
    
    # Systematic data collection
    search = (client.search()
             .text("women's suffrage")
             .in_("newspaper")
             .decade("190", "191")  # 1900s-1910s
             .state("NSW")
             .harvest()  # Enable bulk harvest mode
             .page_size(20))
             
    print("Collecting articles about women's suffrage (1900s-1910s, NSW)...")
    
    collected = 0
    for record in search.records():
        # Process each record
        article_title = record.get('heading', record.get('title', 'Untitled'))
        article_date = record.get('date', 'Unknown date')
        
        print(f"  {collected+1}. {article_title} ({article_date})")
        
        collected += 1
        if collected >= 50:  # Limit for demo
            break
            
    print(f"\nCollected {collected} articles")
    client.close()


def faceted_exploration_example():
    """Faceted browsing example."""
    print("\n=== Faceted Exploration Example ===")
    client = TroveClient.from_env()
    
    # Start with broad search
    result = (client.search()
             .text("Aboriginal Australia")
             .in_("book")
             .with_facets("decade", "format", "language")
             .page_size(5)
             .first_page())
    
    print(f"Broad search found {result.total_results} results")
    
    # Explore facets
    if result.categories and 'facets' in result.categories[0]:
        facets_data = result.categories[0]['facets']
        if 'facet' in facets_data:
            facet_list = facets_data['facet']
            if isinstance(facet_list, dict):
                facet_list = [facet_list]
                
            print("\nFacet breakdown:")
            for facet in facet_list:
                facet_name = facet.get('name', 'Unknown')
                terms = facet.get('term', [])
                if isinstance(terms, dict):
                    terms = [terms]
                    
                print(f"\n  {facet_name}:")
                for term in terms[:5]:  # Show top 5 terms
                    display = term.get('display', term.get('search', 'Unknown'))
                    count = term.get('count', 0)
                    print(f"    {display}: {count}")
                    
    # Refine search based on facets
    refined_result = (client.search()
                     .text("Aboriginal Australia")
                     .in_("book")
                     .decade("200")  # Focus on 2000s
                     .format("Book")  # Only books
                     .page_size(5)
                     .first_page())
                     
    print(f"\nRefined search (2000s books): {refined_result.total_results} results")
    
    client.close()


async def async_search_example():
    """Async search example."""
    print("\n=== Async Search Example ===")
    client = TroveClient.from_env()
    
    # Async search
    result = await (client.search()
                   .text("Australian literature")
                   .in_("book")
                   .decade("200")
                   .page_size(10)
                   .afirst_page())
    
    print(f"Async search found {result.total_results} results")
    
    # Async record iteration
    print("\nAsync record iteration:")
    search = (client.search()
             .text("poetry")
             .in_("book")
             .page_size(5))
    
    count = 0
    async for record in search.arecords():
        title = record.get('title', 'Untitled')
        print(f"  {count+1}. {title}")
        count += 1
        if count >= 10:  # Limit for demo
            break
    
    await client.aclose()


def comparison_example():
    """Compare ergonomic vs raw API."""
    print("\n=== Ergonomic vs Raw API Comparison ===")
    client = TroveClient.from_env()
    
    print("Ergonomic API:")
    print("  result = (client.search()")
    print("           .text('Australian history')")
    print("           .in_('book')")
    print("           .decade('200')")
    print("           .online()")
    print("           .page_size(10)")
    print("           .first_page())")
    
    ergonomic_result = (client.search()
                       .text("Australian history")
                       .in_("book")
                       .decade("200")
                       .online()
                       .page_size(10)
                       .first_page())
    
    print("\nRaw API equivalent:")
    print("  result = client.raw_search.page(")
    print("      category=['book'],")
    print("      q='Australian history',")
    print("      l_decade=['200'],")
    print("      l_availability=['y'],")
    print("      n=10")
    print("  )")
    
    raw_result = client.raw_search.page(
        category=['book'],
        q='Australian history',
        l_decade=['200'],
        l_availability=['y'],
        n=10
    )
    
    print(f"\nErgonomic API results: {ergonomic_result.total_results}")
    print(f"Raw API results: {raw_result.total_results}")
    print("Both should return the same results!")
    
    client.close()


def error_handling_example():
    """Demonstrate error handling."""
    print("\n=== Error Handling Example ===")
    client = TroveClient.from_env()
    
    # Show validation errors
    try:
        # Invalid category
        client.search().in_("invalid_category")
    except Exception as e:
        print(f"Invalid category error: {e}")
    
    try:
        # Invalid page size
        client.search().page_size(200)
    except Exception as e:
        print(f"Invalid page size error: {e}")
    
    try:
        # Multi-category pagination
        search = client.search().in_("book", "newspaper")
        list(search.pages())
    except Exception as e:
        print(f"Multi-category pagination error: {e}")
    
    try:
        # No categories specified
        client.search().text("test").first_page()
    except Exception as e:
        print(f"No categories error: {e}")
    
    client.close()


def main():
    """Run all examples."""
    print("Trove SDK - Ergonomic Search Examples")
    print("====================================")
    
    try:
        basic_search_example()
        filtered_search_example()
        research_workflow_example()
        faceted_exploration_example()
        comparison_example()
        error_handling_example()
        
        # Run async example
        asyncio.run(async_search_example())
        
        print("\n=== All Examples Complete ===")
        print("The ergonomic search interface makes research workflows")
        print("more intuitive while maintaining full API access!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure TROVE_API_KEY is set in your environment")


if __name__ == "__main__":
    main()