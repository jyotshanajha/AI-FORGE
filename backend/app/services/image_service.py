"""Image generation service using LiteLLM proxy."""
import base64
import json
from datetime import datetime
from pathlib import Path

import httpx

from app.core.config import settings


class ImageService:
    """Service for generating images using Gemini 2.0 via LiteLLM."""

    def __init__(self):
        """Initialize HTTP client for LiteLLM proxy."""
        self.base_url = settings.LITELLM_PROXY_URL.rstrip("/")
        self.api_key = settings.LITELLM_API_KEY

    async def generate_image(
        self, prompt: str, user_email: str, user_id: str
    ) -> dict:
        """
        Generate an image using Gemini image generation model via LiteLLM REST API.

        Args:
            prompt: Text prompt describing the image to generate
            user_email: Email of the requesting user (for tracking)
            user_id: UUID of the requesting user (for file organization)

        Returns:
            Dictionary with:
            - url: Path to the generated image
            - filename: Generated filename
            - mime_type: Always "image/png"
            - original_prompt: The prompt used
        """
        # Create user-specific directory for generated images
        user_dir = Path(settings.UPLOAD_DIR) / "generated" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.png"
        filepath = user_dir / filename

        try:
            print(f"[ImageService] Generating image with prompt: {prompt}")
            print(f"[ImageService] Using model: {settings.IMAGE_GEN_MODEL}")
            print(f"[ImageService] LiteLLM proxy: {self.base_url}")
            
            # Prepare request to LiteLLM image generation endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": settings.IMAGE_GEN_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "url",  # URL-based response
            }
            
            # Try LiteLLM /image/generation endpoint
            url = f"{self.base_url}/image/generation"
            print(f"[ImageService] Sending request to: {url}")
            print(f"[ImageService] Payload: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                print(f"[ImageService] Response status: {response.status_code}")
                print(f"[ImageService] Response data: {result}")
                
                # Handle LiteLLM response format
                if "data" in result and len(result["data"]) > 0:
                    image_data = result["data"][0]
                    image_url = image_data.get("url") or image_data.get("b64_json")
                    
                    if not image_url:
                        raise ValueError(f"No image URL or b64_json in response: {image_data}")
                    
                    # If it's base64, decode it
                    if image_data.get("b64_json"):
                        print(f"[ImageService] Decoding base64 image...")
                        image_bytes = base64.b64decode(image_url)
                    else:
                        # Download from URL
                        print(f"[ImageService] Downloading image from URL...")
                        async with httpx.AsyncClient(timeout=30) as dl_client:
                            img_response = await dl_client.get(image_url)
                            img_response.raise_for_status()
                            image_bytes = img_response.content
                    
                    print(f"[ImageService] Image size: {len(image_bytes)} bytes")
                    
                    # Save to disk
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    
                    print(f"[ImageService] Image saved to {filepath}")
                    
                    return {
                        "url": f"/api/chat/attachments/generated/{user_id}/{filename}",
                        "filename": filename,
                        "mime_type": "image/png",
                        "original_prompt": prompt,
                        "size_bytes": len(image_bytes),
                    }
                else:
                    raise ValueError(f"Unexpected response format: {result}")
            
        except httpx.HTTPError as e:
            print(f"[ImageService] HTTP Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"LiteLLM image generation request failed: {str(e)}")
        except Exception as e:
            print(f"[ImageService] ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Image generation failed: {str(e)}")


# Singleton instance
_image_service = None


def get_image_service() -> ImageService:
    """Get or create ImageService singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service



# Singleton instance
_image_service = None


def get_image_service() -> ImageService:
    """Get or create ImageService singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service



# Singleton instance
_image_service = None


def get_image_service() -> ImageService:
    """Get or create ImageService singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
