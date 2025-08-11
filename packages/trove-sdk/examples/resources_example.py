#!/usr/bin/env python3
"""Example demonstrating Stage 3 resource access functionality.

This example shows how to access individual Trove records using the new
resource endpoints: works, articles, people, lists, and titles.
"""

import asyncio
import os
from dotenv import load_dotenv

from trove.config import TroveConfig
from trove.transport import TroveTransport
from trove.cache import MemoryCache
from trove.resources import ResourceFactory
from trove.exceptions import ResourceNotFoundError


async def main():
    """Demonstrate resource access functionality."""
    
    # Load environment variables
    load_dotenv()
    
    # Set up configuration
    config = TroveConfig.from_env()
    cache = MemoryCache()
    transport = TroveTransport(config, cache)
    
    # Create resource factory
    factory = ResourceFactory(transport)
    
    print("Trove Resource Access Examples")
    print("=" * 50)
    
    try:
        # Example 1: Work Resource
        print("\n1. Work Resource Example")
        print("-" * 30)
        
        work_resource = factory.get_work_resource()
        
        # Try to get a work (using a simple ID that might exist)
        work_id = "1"
        try:
            work = work_resource.get(work_id)
            print(f"Found work: {work.get('title', 'No title')}")
            
            # Get additional information
            versions = work_resource.get_versions(work_id)
            print(f"Work has {len(versions)} version(s)")
            
            tags = work_resource.get_tags(work_id)
            print(f"Work has {len(tags)} tag(s)")
            
        except ResourceNotFoundError:
            print(f"Work {work_id} not found")
        
        # Example 2: Newspaper Article Resource
        print("\n2. Newspaper Article Resource Example")
        print("-" * 40)
        
        newspaper_resource = factory.get_newspaper_resource()
        
        # Try the example article from the API documentation
        article_id = "18341291"
        try:
            article = newspaper_resource.get(article_id)
            print(f"Found article: {article.get('heading', 'No heading')}")
            print(f"Published: {article.get('date', 'Unknown date')}")
            
            # Check if full text is available
            full_text = newspaper_resource.get_full_text(article_id)
            if full_text:
                print(f"Full text length: {len(full_text)} characters")
            else:
                print("Full text not available")
            
            # Get PDF URLs
            pdf_urls = newspaper_resource.get_pdf_urls(article_id)
            print(f"Available PDFs: {len(pdf_urls)}")
            
            # Check status
            if newspaper_resource.is_coming_soon(article_id):
                print("Article status: Coming soon")
            elif newspaper_resource.is_withdrawn(article_id):
                print("Article status: Withdrawn")
            else:
                print("Article status: Available")
                
        except ResourceNotFoundError:
            print(f"Article {article_id} not found")
        
        # Example 3: People Resource
        print("\n3. People Resource Example")
        print("-" * 30)
        
        people_resource = factory.get_people_resource()
        
        # Try a simple people ID
        person_id = "1"
        try:
            person = people_resource.get(person_id)
            primary_name = people_resource.get_primary_name(person_id)
            print(f"Found person: {primary_name or 'Unknown name'}")
            
            # Check type
            if people_resource.is_person(person_id):
                print("Type: Person")
                occupations = people_resource.get_occupations(person_id)
                if occupations:
                    print(f"Occupations: {', '.join(occupations)}")
            elif people_resource.is_organization(person_id):
                print("Type: Organization")
            
            # Get alternate names
            alt_names = people_resource.get_alternate_names(person_id)
            if alt_names:
                print(f"Alternate names: {', '.join(alt_names[:3])}{'...' if len(alt_names) > 3 else ''}")
            
        except ResourceNotFoundError:
            print(f"Person {person_id} not found")
        
        # Example 4: List Resource
        print("\n4. List Resource Example")
        print("-" * 25)
        
        list_resource = factory.get_list_resource()
        
        # Try the example list from the API documentation
        list_id = "21922"
        try:
            list_data = list_resource.get(list_id)
            title = list_resource.get_title(list_id)
            creator = list_resource.get_creator(list_id)
            item_count = list_resource.get_item_count(list_id)
            
            print(f"Found list: {title}")
            print(f"Created by: {creator}")
            print(f"Contains {item_count} items")
            
            # Get list items
            items = list_resource.get_items(list_id)
            print(f"Retrieved {len(items)} item details")
            
        except ResourceNotFoundError:
            print(f"List {list_id} not found")
        
        # Example 5: Title Resources
        print("\n5. Title Resources Example")
        print("-" * 30)
        
        newspaper_titles = factory.get_newspaper_title_resource()
        
        # Search for newspaper titles
        try:
            results = newspaper_titles.search(state='nsw', limit=3)
            print("Newspaper title search completed")
            print(f"Search results: {type(results)}")
            
        except Exception as e:
            print(f"Title search failed: {e}")
        
        # Example 6: Async Operations
        print("\n6. Async Operations Example")
        print("-" * 35)
        
        # Demonstrate async resource access
        work_resource = factory.get_work_resource()
        
        try:
            work = await work_resource.aget("1")
            print(f"Async work fetch successful: {bool(work)}")
            
            versions = await work_resource.aget_versions("1")
            print(f"Async versions fetch: {len(versions)} versions")
            
        except ResourceNotFoundError:
            print("Async work fetch: Work not found")
        
        # Example 7: Error Handling
        print("\n7. Error Handling Example")
        print("-" * 35)
        
        # Demonstrate proper error handling
        work_resource = factory.get_work_resource()
        
        try:
            # This should fail with ResourceNotFoundError
            work_resource.get("999999999999")
        except ResourceNotFoundError as e:
            print(f"Expected error caught: {e}")
        
        try:
            # This should fail with ValidationError for invalid include
            work_resource.get("1", include=["invalid_include"])
        except Exception as e:
            print(f"Validation error caught: {type(e).__name__}: {e}")
        
    finally:
        # Clean up
        await transport.aclose()
        transport.close()
    
    print("\n" + "=" * 50)
    print("Resource examples completed!")


if __name__ == "__main__":
    asyncio.run(main())