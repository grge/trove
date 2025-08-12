#!/usr/bin/env python3
"""Quick test of the new Pydantic models."""

from trove.models import Work, Article, People, TroveList, parse_record

def test_work_model():
    """Test Work model creation."""
    work_data = {
        'id': '123456',
        'title': 'Test Work',
        'contributor': ['Author, Test'],
        'issued': '2020',
        'type': ['Book'],
        'subject': ['Australian history'],
        'publisher': ['Test Publisher'],
        'troveUrl': 'https://trove.nla.gov.au/work/123456'
    }
    
    work = Work(**work_data)
    
    print("=== Work Model Test ===")
    print(f"ID: {work.id}")
    print(f"Title: {work.primary_title}")
    print(f"Contributors: {work.contributor}")
    print(f"Publication year: {work.publication_year}")
    print(f"Dict access (title): {work['title']}")
    print(f"Raw data keys: {list(work.raw.keys())}")
    print(f"Backward compatibility: {'title' in work}")
    print()

def test_article_model():
    """Test Article model creation."""
    article_data = {
        'id': '789123',
        'heading': 'Test Article Headline',
        'articleText': 'This is the full text of the article...',
        'date': '1920-05-15',
        'illustrated': 'Y',
        'wordCount': '150',
        'title': {
            'id': '456',
            'title': 'The Sydney Morning Herald'
        },
        'troveUrl': 'https://trove.nla.gov.au/newspaper/article/789123'
    }
    
    article = Article(**article_data)
    
    print("=== Article Model Test ===")
    print(f"ID: {article.id}")
    print(f"Heading: {article.display_title}")
    print(f"Newspaper: {article.newspaper_title}")
    print(f"Has full text: {article.has_full_text}")
    print(f"Is illustrated: {article.is_illustrated}")
    print(f"Word count: {article.word_count}")
    print(f"Dict access (heading): {article['heading']}")
    print()

def test_model_parsing():
    """Test automatic model parsing."""
    work_data = {
        'id': '555666',
        'title': 'Parsed Work',
        'contributor': ['Automatic, Parser'],
        'issued': '2023'
    }
    
    parsed_work = parse_record(work_data, 'work')
    
    print("=== Model Parsing Test ===")
    print(f"Parsed type: {type(parsed_work)}")
    print(f"Title: {parsed_work.primary_title if parsed_work else 'None'}")
    print(f"Dict access still works: {parsed_work['title'] if parsed_work else 'N/A'}")
    print()

def test_backward_compatibility():
    """Test that dict-like access still works."""
    work_data = {
        'id': '999888',
        'title': 'Compatibility Test',
        'someNewField': 'This field might be added to the API in the future'
    }
    
    work = Work(**work_data)
    
    print("=== Backward Compatibility Test ===")
    print(f"Model title: {work.title}")
    print(f"Dict access title: {work['title']}")
    print(f"New field via dict: {work.get('someNewField', 'Not found')}")
    print(f"New field in raw: {work.raw.get('someNewField', 'Not found')}")
    print(f"Has new field: {'someNewField' in work}")
    print()

if __name__ == "__main__":
    test_work_model()
    test_article_model()
    test_model_parsing()
    test_backward_compatibility()
    print("All model tests completed!")