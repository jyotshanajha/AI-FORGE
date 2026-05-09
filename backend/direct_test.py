#!/usr/bin/env python3
"""Test the endpoint directly."""
import asyncio
import httpx
import json

async def test():
    """Test."""
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "prompt": "test",
    }
    
    # Test without auth first
    async with httpx.AsyncClient() as client:
        print("Testing: http://localhost:8000/api/chat/generate-image")
        response = await client.post(
            "http://localhost:8000/api/chat/generate-image",
            json=payload,
            headers=headers
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")

asyncio.run(test())
