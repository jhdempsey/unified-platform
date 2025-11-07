#!/usr/bin/env python3
"""
Test script for MCP Server
Tests the MCP protocol endpoints
"""
import asyncio
import json

import httpx


async def test_mcp_server(base_url: str = "http://localhost:8000"):
    """Test MCP server endpoints"""

    print("🧪 Testing MCP Server\n")
    print(f"Base URL: {base_url}\n")

    async with httpx.AsyncClient() as client:

        # Test 1: Health check
        print("1️⃣  Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test 2: List tools (convenience endpoint)
        print("2️⃣  Testing /tools endpoint...")
        response = await client.get(f"{base_url}/tools")
        tools_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Tools available: {tools_data['count']}")
        for tool in tools_data["tools"]:
            print(f"     - {tool['name']}: {tool['description'][:60]}...")
        print()

        # Test 3: MCP tools/list
        print("3️⃣  Testing MCP tools/list...")
        mcp_request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        response = await client.post(f"{base_url}/mcp", json=mcp_request)
        mcp_response = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Tools: {len(mcp_response['result']['tools'])}")
        print()

        # Test 4: MCP tools/call - RAG query
        print("4️⃣  Testing MCP tools/call (RAG query)...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "query_documentation",
                "arguments": {
                    "question": "What are the supplier quality requirements?",
                    "max_results": 2,
                },
            },
        }
        response = await client.post(f"{base_url}/mcp", json=mcp_request)
        mcp_response = response.json()
        print(f"   Status: {response.status_code}")

        if "result" in mcp_response:
            content = mcp_response["result"]["content"][0]["text"]
            result = json.loads(content)
            print(f"   Answer: {result.get('answer', 'N/A')[:100]}...")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Sources: {len(result.get('sources', []))}")
        elif "error" in mcp_response:
            print(f"   Error: {mcp_response['error']}")
        print()

        print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
