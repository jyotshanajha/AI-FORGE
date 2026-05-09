"""Image generation service using LiteLLM proxy."""
import base64
import json
from datetime import datetime
from pathlib import Path

import httpx

from app.core.config import settings


class ImageService:
    """Service for generating images via LiteLLM proxy."""

    def __init__(self):
        """Initialize service."""
        self.base_url = settings.LITELLM_PROXY_URL.rstrip("/")
        self.api_key = settings.LITELLM_API_KEY

    async def generate_image(
        self, prompt: str, user_email: str, user_id: str
    ) -> dict:
        """Generate image and return metadata."""
        # Create output directory
        user_dir = Path(settings.UPLOAD_DIR) / "generated" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.png"
        filepath = user_dir / filename

        print(f"\n{'='*60}")
        print(f"[IMAGE_GEN] START")
        print(f"{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"Model: {settings.IMAGE_GEN_MODEL}")
        print(f"LiteLLM URL: {self.base_url}")
        print(f"API Key: {self.api_key[:10]}...")

        try:
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": settings.IMAGE_GEN_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "url",
            }

            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Make request - use correct LiteLLM endpoint
            correct_endpoint = f"{self.base_url}/v1/images/generations"
            print(f"[REQUEST] Using correct LiteLLM endpoint: {correct_endpoint}")
            print(f"[REQUEST] Sending request...")
            
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.post(correct_endpoint, json=payload, headers=headers)

            print(f"[RESPONSE] Status: {response.status_code}")
            print(f"[RESPONSE] Headers: {dict(response.headers)}")

            if response.status_code != 200:
                print(f"[ERROR] Non-200 response!")
                print(f"[ERROR] Body: {response.text[:500]}")
                response.raise_for_status()

            result = response.json()
            print(f"[RESPONSE] Body (first 500 chars): {str(result)[:500]}")

            # Extract image
            if not result.get("data") or len(result["data"]) == 0:
                raise ValueError(f"No image data in response: {result}")

            image_data = result["data"][0]
            print(f"[IMAGE_DATA] Keys: {list(image_data.keys())}")

            # Handle URL or base64
            if image_data.get("url"):
                print(f"[IMAGE_DATA] URL format detected")
                image_url = image_data["url"]
                print(f"[DOWNLOAD] Starting download from: {image_url[:100]}...")

                async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()
                    image_bytes = img_response.content

                print(f"[DOWNLOAD] Downloaded {len(image_bytes)} bytes")

            elif image_data.get("b64_json"):
                print(f"[IMAGE_DATA] Base64 format detected")
                image_base64 = image_data["b64_json"]
                image_bytes = base64.b64decode(image_base64)
                print(f"[DECODE] Decoded to {len(image_bytes)} bytes")

            else:
                raise ValueError(f"No URL or b64_json in image data: {image_data}")

            # Save to disk
            print(f"[SAVE] Writing to: {filepath}")
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            result_data = {
                "url": f"/api/chat/attachments/generated/{user_id}/{filename}",
                "filename": filename,
                "mime_type": "image/png",
                "original_prompt": prompt,
                "size_bytes": len(image_bytes),
            }

            print(f"[SUCCESS] Image generated successfully!")
            print(f"[RESULT] {json.dumps(result_data, indent=2)}")
            print(f"{'='*60}\n")

            return result_data

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            print(f"[HTTP_ERROR] {error_msg}")
            print(f"{'='*60}\n")
            raise Exception(error_msg)

        except httpx.RequestError as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"[REQUEST_ERROR] {error_msg}")
            print(f"{'='*60}\n")
            raise Exception(error_msg)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            raise Exception(f"Image generation failed: {error_msg}")


# Singleton instance
_image_service = None


def get_image_service() -> ImageService:
    """Get or create ImageService singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
