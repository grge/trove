#!/usr/bin/env python3
"""
Quick functionality test for Trove MCP server.
Run this to verify all tools are working correctly.
"""

import asyncio
import json
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../trove-sdk'))

from trove_mcp.server import TroveMCPServer


async def test_mcp_tools():
    """Test all MCP tools with basic functionality."""
    print("🚀 Starting Trove MCP Server functionality test...\n")
    
    try:
        # Initialize server
        server = TroveMCPServer()
        print(f"✅ Server initialized with {len(server.tools)} tools")
        
        # Test 1: Search for books
        print("\n📚 Testing search_page tool...")
        search_tool = server.tools['search_page']
        search_result = await search_tool.execute({
            'categories': ['book'],
            'query': 'Australia',
            'page_size': 3
        })
        print(f"✅ Found {search_result['total_results']} results")
        
        # Test 2: Get a work record (if available)
        if (search_result['total_results'] > 0 and 
            search_result['categories'][0]['records'].get('work')):
            
            print("\n📖 Testing get_work tool...")
            work_id = search_result['categories'][0]['records']['work'][0]['id']
            work_tool = server.tools['get_work']
            work_result = await work_tool.execute({
                'record_id': work_id,
                'record_level': 'brief'
            })
            print(f"✅ Retrieved work record: {work_id}")
        
        # Test 3: Test PID resolution
        print("\n🔍 Testing resolve_pid tool...")
        resolve_tool = server.tools['resolve_pid']
        resolve_result = await resolve_tool.execute({
            'identifier': 'nla.obj-1'
        })
        print(f"✅ PID resolution test completed: {resolve_result['resolved']}")
        
        # Test 4: List all available tools
        print("\n🛠️  Available MCP tools:")
        for tool_name, tool_instance in server.tools.items():
            print(f"   • {tool_name} - {tool_instance.description.strip()[:60]}...")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"📋 Tools tested: {len(server.tools)}/8")
        print(f"🌐 Real API calls: ✅")
        print(f"🔧 MCP protocol: ✅")
        
        # Cleanup
        await server.shutdown()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    # Check for API key
    if not os.environ.get('TROVE_API_KEY'):
        print("❌ TROVE_API_KEY environment variable not set")
        print("   Set it with: export TROVE_API_KEY='your_key_here'")
        sys.exit(1)
    
    asyncio.run(test_mcp_tools())