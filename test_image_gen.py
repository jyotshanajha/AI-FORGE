"""Test script to debug LiteLLM image generation."""
import sys
import asyncio
import json

# Add backend to path
sys.path.insert(0, r'C:\Users\JyotshanaJ\Desktop\AI FORGE\backend')

from app.core.config import settings
import httpx

print(f"LiteLLM URL: {settings.LITELLM_PROXY_URL}")
print(f"LiteLLM API Key: {settings.LITELLM_API_KEY[:10]}...")
print(f"Image Gen Model: {settings.IMAGE_GEN_MODEL}")

async def test_image_generation():
    """Test image generation via LiteLLM REST API."""
    
    headers = {
        "Authorization": f"Bearer {settings.LITELLM_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": settings.IMAGE_GEN_MODEL,
        "prompt": "sunrise in the mountains",
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
    }
    
    url = f"{settings.LITELLM_PROXY_URL}/image/generation"
    
    print(f"\n--- Testing Image Generation via LiteLLM ---")
    print(f"URL: {url}")
    print(f"Model: {settings.IMAGE_GEN_MODEL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            print("Sending request...")
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if "data" in result and len(result["data"]) > 0:
                image_info = result["data"][0]
                if "url" in image_info:
                    print(f"\nImage URL: {image_info['url'][:100]}...")
                elif "b64_json" in image_info:
                    print(f"\nBase64 image size: {len(image_info['b64_json'])} chars")
            
    except httpx.HTTPError as e:
        print(f"\n❌ HTTP Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(f"Response: {e.response.text if hasattr(e, 'response') and e.response else 'N/A'}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()

# Run the test
asyncio.run(test_image_generation())


