#!/usr/bin/env python3
"""Test endpoints."""
import asyncio
import httpx
import json

async def test():
    """Test."""
    
    # Test debug endpoint
    async with httpx.AsyncClient() as client:
        print("1. Testing: /api/chat/debug-test")
        response = await client.post("http://localhost:8000/api/chat/debug-test")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text}\n")
        
        print("2. Testing: /api/chat/generate-image")
        response = await client.post(
            "http://localhost:8000/api/chat/generate-image",
            json={"prompt": "test"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text}\n")
        
        print("3. Testing: /api/chat/stream")
        response = await client.post(
            "http://localhost:8000/api/chat/stream",
            json={"thread_id": None, "message": "test", "attachment_ids": []}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body (first 100 chars): {response.text[:100]}")

asyncio.run(test())
