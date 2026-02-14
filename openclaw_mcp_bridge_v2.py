#!/usr/bin/env python3
"""
OpenClaw MCP Bridge for Trove (Enhanced Version)
Bridge that retrieves full article content and contextual snippets
"""
import json
import sys
import asyncio
import re
from pathlib import Path

# Add the trove-sdk to the path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

try:
    from trove import TroveClient
except ImportError:
    print("Error: Could not import Trove SDK", file=sys.stderr)
    sys.exit(1)

def extract_context_snippet(text: str, search_term: str, context_chars: int = 200) -> str:
    """Extract a snippet around the search term with context."""
    if not text or not search_term:
        return ""
    
    # Find all occurrences of the search term (case insensitive)
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    matches = list(pattern.finditer(text))
    
    if not matches:
        # If exact term not found, return first portion of text
        return text[:context_chars] + ("..." if len(text) > context_chars else "")
    
    # Use the first match for context
    match = matches[0]
    start_pos = max(0, match.start() - context_chars // 2)
    end_pos = min(len(text), match.end() + context_chars // 2)
    
    snippet = text[start_pos:end_pos]
    
    # Add ellipsis if we truncated
    if start_pos > 0:
        snippet = "..." + snippet
    if end_pos < len(text):
        snippet = snippet + "..."
    
    return snippet.strip()

def clean_text(text: str) -> str:
    """Clean OCR text by removing excessive whitespace and fixing common issues."""
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove extra punctuation artifacts
    text = re.sub(r'[|]{2,}', ' ', text)
    # Fix common OCR errors
    text = text.replace(' , ', ', ').replace(' . ', '. ').replace(' ; ', '; ')
    
    return text.strip()

async def search_trove_detailed(query: str, categories=None, limit=3):
    """Search Trove and retrieve full article content with context."""
    try:
        client = TroveClient.from_env()
        with client:
            # Build search
            search = client.search().text(query)
            if categories:
                for cat in categories:
                    search = search.in_(cat)
            else:
                search = search.in_("newspaper")  # Default to newspaper search
            search = search.page_size(limit)
            results = search.first_page()
            
            formatted_results = []
            formatted_results.append(f"🔍 Found {results.total_results:,} results in Trove for: '{query}'")
            formatted_results.append("")
            
            # Process results with full content
            newspaper_resource = client.resources.get_newspaper_resource()
            
            for category in results.categories:
                if 'records' in category and 'article' in category['records']:
                    cat_name = category.get('category', 'unknown')
                    articles = category['records']['article']
                    
                    formatted_results.append(f"📁 {cat_name.title()} Articles with Full Content:")
                    formatted_results.append("")
                    
                    for i, article in enumerate(articles[:limit], 1):
                        article_id = article.get('id')
                        title = article.get('heading', 'Unknown Title')
                        date = article.get('date', 'Unknown Date')
                        
                        # Get newspaper name
                        newspaper = 'Unknown Paper'
                        if 'title' in article:
                            if isinstance(article['title'], dict):
                                newspaper = article['title'].get('value', 'Unknown Paper')
                            elif isinstance(article['title'], str):
                                newspaper = article['title']
                        
                        formatted_results.append(f"📰 **Article {i}: {title}**")
                        formatted_results.append(f"   📅 {date} | 🏛️ {newspaper}")
                        
                        # Try to get full text
                        if article_id:
                            try:
                                full_text = newspaper_resource.get_full_text(article_id)
                                if full_text:
                                    cleaned_text = clean_text(full_text)
                                    context = extract_context_snippet(cleaned_text, query, 300)
                                    
                                    formatted_results.append(f"   📜 **Context:**")
                                    formatted_results.append(f"   \"{context}\"")
                                    
                                    # Add text length info
                                    formatted_results.append(f"   📊 Full article: {len(cleaned_text):,} characters")
                                else:
                                    formatted_results.append("   ❌ Full text not available")
                            except Exception as e:
                                formatted_results.append(f"   ❌ Error retrieving content: {str(e)}")
                        else:
                            formatted_results.append("   ❌ No article ID available")
                        
                        # Add Trove URL for reference
                        if article_id:
                            formatted_results.append(f"   🔗 https://trove.nla.gov.au/newspaper/article/{article_id}")
                        
                        formatted_results.append("")
                
                # Handle other record types (books, people, etc.)
                elif 'records' in category:
                    records = category['records']
                    
                    if 'work' in records:
                        formatted_results.append("📚 Related Books/Works:")
                        for work in records['work'][:2]:
                            title = work.get('title', 'Unknown Title')
                            year = work.get('issued', 'Unknown Year')
                            formatted_results.append(f"   • {title} ({year})")
                        formatted_results.append("")
                    
                    if 'people' in records:
                        formatted_results.append("👤 Related People:")
                        for person in records['people'][:2]:
                            name = person.get('name', 'Unknown Name')
                            dates = person.get('birthDate', 'Unknown dates')
                            formatted_results.append(f"   • {name} ({dates})")
                        formatted_results.append("")
            
            return "\\n".join(formatted_results)
            
    except Exception as e:
        return f"❌ Error searching Trove: {str(e)}"

def parse_openclaw_request(prompt: str):
    """Parse the OpenClaw prompt to extract search intent."""
    prompt_lower = prompt.lower()
    
    categories = []
    query = prompt
    
    # Extract categories if mentioned
    if "newspaper" in prompt_lower or "article" in prompt_lower:
        categories.append("newspaper")
    if "book" in prompt_lower:
        categories.append("book")
    if "image" in prompt_lower or "photo" in prompt_lower:
        categories.append("image")
    if "people" in prompt_lower or "person" in prompt_lower:
        categories.append("people")
    
    # Clean up the query
    search_triggers = [
        "search trove for", "find in trove", "trove search", 
        "search for", "find articles about", "look up",
        "historical records", "newspaper articles"
    ]
    
    for trigger in search_triggers:
        if trigger in prompt_lower:
            query = prompt_lower.replace(trigger, "").strip()
            break
    
    # Remove common prefixes/suffixes  
    query = query.replace("about ", "").replace("for ", "").strip()
    
    return query, categories

async def main():
    """Main function to handle OpenClaw CLI backend requests."""
    try:
        # Read prompt from command line argument or stdin
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
        else:
            prompt = sys.stdin.read().strip()
        
        if not prompt:
            response = "❓ Please provide a search query."
        else:
            # Check if this looks like a Trove search request
            query, categories = parse_openclaw_request(prompt)
            
            if any(trigger in prompt.lower() for trigger in [
                "trove", "search", "find", "historical", "newspaper", 
                "alice springs", "australian", "article", "adelaide"
            ]):
                response = await search_trove_detailed(query, categories, limit=2)  # Limit to 2 for detailed analysis
            else:
                response = "🔍 This doesn't appear to be a Trove search request. Try asking to 'search Trove for [your topic]' or 'find Australian historical records about [topic]'."
        
        # Return in OpenClaw CLI backend JSON format
        result = {
            "text": response,
            "session_id": f"trove-detailed-{hash(prompt) % 10000}"
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "text": f"❌ Trove bridge error: {str(e)}",
            "session_id": "trove-error"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())