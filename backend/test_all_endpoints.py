#!/usr/bin/env python3
"""Test different LiteLLM image generation endpoints."""
import asyncio
import httpx
import json
import os

async def test_endpoint(endpoint_path, payload, headers):
    """Test a single endpoint."""
    url = f"https://litellm.amzur.com{endpoint_path}"
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"Status: {response.status_code}")
            body = response.text[:300]
            print(f"Response: {body}")
            
            if response.status_code == 200:
                print("✓ SUCCESS!")
                return True
            
    except Exception as e:
        print(f"Error: {str(e)[:100]}")
    
    return False

async def main():
    """Test multiple endpoints."""
    api_key = os.getenv("LITELLM_API_KEY", "sk-YLmZIK6subdXeSdRWnyCXg")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "gemini/imagen-4.0-fast-generate-001",
        "prompt": "A beautiful sunrise",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
    }
    
    endpoints = [
        "/image/generation",
        "/image/generations",
        "/v1/image/generation",
        "/v1/image/generations",
        "/v1/images/generations",
        "/images/generations",
        "/images/generate",
        "/generate-image",
        "/api/image/generation",
        "/api/images/generations",
    ]
    
    print(f"Testing {len(endpoints)} different endpoints...")
    print(f"API Key: {api_key[:10]}...")
    
    for endpoint in endpoints:
        result = await test_endpoint(endpoint, payload, headers)
        if result:
            print(f"\n🎉 FOUND WORKING ENDPOINT: {endpoint}")
            return endpoint
    
    print(f"\n❌ No working endpoint found. Trying with different models...")
    
    # Try different models with /image/generation
    models = [
        "dall-e-3",
        "dall-e-2",
        "imagen-3",
        "imagen",
        "gemini/imagen",
        "gpt-4-vision",
    ]
    
    for model in models:
        payload_copy = payload.copy()
        payload_copy["model"] = model
        result = await test_endpoint("/image/generation", payload_copy, headers)
        if result:
            print(f"\n🎉 FOUND WORKING MODEL: {model}")
            return model

if __name__ == "__main__":
    asyncio.run(main())
