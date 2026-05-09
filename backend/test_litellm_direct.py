#!/usr/bin/env python3
"""Test LiteLLM image generation endpoint."""
import asyncio
import httpx
import json
import os

async def test_litellm_image_gen():
    """Test direct call to LiteLLM image generation."""
    
    url = "https://litellm.amzur.com/image/generation"
    api_key = os.getenv("LITELLM_API_KEY", "sk-YLmZIK6subdXeSdRWnyCXg")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "gemini/imagen-4.0-fast-generate-001",
        "prompt": "A beautiful sunrise over mountains",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
    }
    
    print(f"Testing LiteLLM image generation...")
    print(f"URL: {url}")
    print(f"API Key: {api_key[:10]}...")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            print("[SENDING] Making request...")
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"[RESPONSE] Status: {response.status_code}")
            print(f"[RESPONSE] Headers: {dict(response.headers)}")
            print(f"[RESPONSE] Body:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 200:
                print("\n✓ SUCCESS - Endpoint is working!")
            else:
                print(f"\n✗ FAILED - Got {response.status_code}")
                
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_litellm_image_gen())
