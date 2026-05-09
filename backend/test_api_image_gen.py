#!/usr/bin/env python3
"""Test image generation through the API."""
import asyncio
import httpx
import json
import uuid

async def test_image_generation():
    """Test the image generation endpoint."""
    
    user_id = str(uuid.uuid4())
    
    payload = {
        "prompt": "A beautiful sunset over the ocean",
        "thread_id": None,
    }
    
    headers = {
        "Content-Type": "application/json",
    }
    
    url = "http://localhost:8000/api/chat/generate-image"
    
    print(f"Testing image generation API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("[SENDING] Making request...")
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"[RESPONSE] Status: {response.status_code}")
            print(f"[RESPONSE] Headers: {dict(response.headers)}")
            print(f"[RESPONSE] Body:")
            print(json.dumps(response.json(), indent=2))
            
            if response.status_code == 200:
                print("\n✓ SUCCESS!")
            else:
                print(f"\n✗ FAILED with {response.status_code}")
                
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_generation())
