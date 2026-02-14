#!/usr/bin/env python3
"""
OpenClaw MCP Bridge for Trove
Bridge between OpenClaw CLI backend and Trove MCP server
"""
import json
import sys
import asyncio
import subprocess
import tempfile
import os
from pathlib import Path

# Add the trove-sdk to the path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "trove-sdk"))

try:
    from trove import TroveClient
except ImportError:
    print("Error: Could not import Trove SDK", file=sys.stderr)
    sys.exit(1)

async def search_trove(query: str, categories=None, limit=5):
    """Search Trove using the SDK."""
    try:
        client = TroveClient.from_env()
        with client:
            search = client.search().text(query)
            # Default to newspaper if no categories specified
            if categories:
                for cat in categories:
                    search = search.in_(cat)
            else:
                search = search.in_("newspaper")  # Default to newspaper search
            search = search.page_size(limit)
            results = search.first_page()
            
            # Format results for OpenClaw
            formatted_results = []
            formatted_results.append(f"🔍 Found {results.total_results:,} results in Trove for: {query}")
            formatted_results.append("")
            
            for category in results.categories:
                if 'records' in category:
                    cat_name = category.get('category', 'unknown')
                    formatted_results.append(f"📁 {cat_name.title()} Results:")
                    
                    # Handle different record types
                    records = category['records']
                    
                    # Articles (newspapers)
                    if 'article' in records:
                        for article in records['article'][:3]:
                            title = article.get('heading', 'Unknown Title')
                            date = article.get('date', 'Unknown Date')
                            newspaper = 'Unknown Paper'
                            if 'title' in article:
                                if isinstance(article['title'], dict):
                                    newspaper = article['title'].get('value', 'Unknown Paper')
                                else:
                                    newspaper = str(article['title'])
                            formatted_results.append(f"  📰 {title}")
                            formatted_results.append(f"      📅 {date} | {newspaper}")
                    
                    # Works (books, images, etc.)
                    if 'work' in records:
                        for work in records['work'][:3]:
                            title = work.get('title', 'Unknown Title')
                            year = work.get('issued', 'Unknown Year')
                            work_type = work.get('type', 'unknown')
                            formatted_results.append(f"  📚 {title}")
                            formatted_results.append(f"      📅 {year} | Type: {work_type}")
                    
                    # People
                    if 'people' in records:
                        for person in records['people'][:3]:
                            name = person.get('name', 'Unknown Name')
                            dates = person.get('birthDate', 'Unknown dates')
                            formatted_results.append(f"  👤 {name}")
                            formatted_results.append(f"      📅 {dates}")
                    
                    formatted_results.append("")
            
            return "\n".join(formatted_results)
            
    except Exception as e:
        return f"❌ Error searching Trove: {str(e)}"

def parse_openclaw_request(prompt: str):
    """Parse the OpenClaw prompt to extract search intent."""
    # Simple intent detection for Trove searches
    prompt_lower = prompt.lower()
    
    # Check for explicit search requests
    search_triggers = [
        "search trove for", "find in trove", "trove search", 
        "search for", "find articles about", "look up",
        "historical records", "newspaper articles", "australian history"
    ]
    
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
                "alice springs", "australian", "article"
            ]):
                response = await search_trove(query, categories)
            else:
                response = "🔍 This doesn't appear to be a Trove search request. Try asking to 'search Trove for [your topic]' or 'find Australian historical records about [topic]'."
        
        # Return in OpenClaw CLI backend JSON format
        result = {
            "text": response,
            "session_id": f"trove-{hash(prompt) % 10000}"
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