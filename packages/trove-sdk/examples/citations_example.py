#!/usr/bin/env python3
"""
Example demonstrating Trove citation functionality.

This example shows how to:
1. Extract citation information from search results
2. Generate BibTeX and CSL-JSON citations
3. Resolve PIDs and URLs to complete citations
4. Generate bibliographies for multiple items

Prerequisites:
- Set TROVE_API_KEY environment variable
- Install the trove-sdk package

Usage:
    python examples/citations_example.py
"""

import os
from trove import TroveClient
from trove.citations import RecordType

def main():
    """Demonstrate citation functionality."""
    
    print("🔍 Trove Citations Demo")
    print("=" * 50)
    
    # Create client - this will automatically find .env files
    try:
        client = TroveClient.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return
    
    try:
        # 1. Extract citations from search results
        print("\n1. Extracting citations from search results...")
        
        search = (client.search()
                 .text("Australian literature")
                 .in_("book")
                 .page_size(3))
        
        search_result = search.first_page()
        
        citations = []
        print(f"Found {search_result.total_results} results")
        
        # Access records from first page
        record_count = 0
        for record in search.records():
            try:
                citation = client.citations.extract_from_record(record, RecordType.WORK)
                citations.append(citation)
                record_count += 1
                print(f"  {record_count}. {citation.display_title}")
                if citation.primary_creator:
                    print(f"     Author: {citation.primary_creator}")
                if citation.publication_date:
                    print(f"     Year: {citation.publication_date}")
                print()
                
                if record_count >= 3:  # Limit to 3 records for demo
                    break
            except Exception as e:
                print(f"  Error extracting citation: {e}")
                record_count += 1
                if record_count >= 3:
                    break
                
        # 2. Generate individual citations
        if citations:
            print("\n2. Generating BibTeX citation...")
            bibtex = client.citations.cite_bibtex(citations[0])
            print(bibtex)
            
            print("\n3. Generating CSL-JSON citation...")
            csl_json = client.citations.cite_csl_json(citations[0])
            print("CSL-JSON fields:")
            for key, value in csl_json.items():
                print(f"  {key}: {value}")
        
        # 3. Demonstrate PID/URL resolution
        print("\n4. Testing PID/URL resolution...")
        
        # Try to resolve some common patterns
        test_identifiers = [
            # Numeric IDs that might exist
            "123456",
            "1000001",
        ]
        
        for identifier in test_identifiers:
            try:
                print(f"\nTrying to resolve: {identifier}")
                resolved = client.citations.resolve_identifier(identifier)
                if resolved:
                    print(f"  ✓ Resolved to: {resolved.display_title}")
                    print(f"    Type: {resolved.record_type.value}")
                    print(f"    ID: {resolved.record_id}")
                else:
                    print(f"  ✗ Could not resolve identifier")
            except Exception as e:
                print(f"  ✗ Error resolving: {e}")
        
        # 4. Generate bibliography
        if len(citations) > 1:
            print("\n5. Generating BibTeX bibliography...")
            bibliography = client.citations.bibliography_bibtex(citations[:3])
            print(f"Generated bibliography with {len(citations[:3])} entries:")
            print(bibliography[:500] + "..." if len(bibliography) > 500 else bibliography)
            
            print("\n6. Generating CSL-JSON bibliography...")
            csl_bibliography = client.citations.bibliography_csl_json(citations[:3])
            print(f"Generated CSL-JSON with {len(csl_bibliography)} entries")
            for i, entry in enumerate(csl_bibliography):
                print(f"  {i+1}. {entry.get('title', 'No title')}")
        
        # 5. Test with different record types
        print("\n7. Testing with newspaper articles...")
        try:
            article_search = (client.search()
                            .text("federation")
                            .in_("newspaper")
                            .page_size(1))
            
            for record in article_search.records():
                article_citation = client.citations.extract_from_record(record, RecordType.ARTICLE)
                print(f"Article: {article_citation.display_title}")
                if article_citation.newspaper_title:
                    print(f"Newspaper: {article_citation.newspaper_title}")
                if article_citation.publication_date:
                    print(f"Date: {article_citation.publication_date}")
                
                # Generate article citation
                article_bibtex = client.citations.cite_bibtex(article_citation)
                print(f"\nBibTeX:\n{article_bibtex}")
                break
                
        except Exception as e:
            print(f"Error with article citation: {e}")
        
        print("\n✅ Citation demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during citation demo: {e}")
        
    finally:
        # Clean up
        client.close()

if __name__ == "__main__":
    main()