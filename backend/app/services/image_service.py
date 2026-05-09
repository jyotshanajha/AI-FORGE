"""Image generation service using LiteLLM proxy."""
import base64
import os
from datetime import datetime
from pathlib import Path

import requests
from openai import OpenAI

from app.core.config import settings


class ImageService:
    """Service for generating images using Gemini 2.0 via LiteLLM."""

    def __init__(self):
        """Initialize OpenAI client pointing to LiteLLM proxy."""
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_PROXY_URL,
        )

    async def generate_image(
        self, prompt: str, user_email: str, user_id: str
    ) -> dict:
        """
        Generate an image using Gemini image generation model.

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
            print(f"[ImageService] LiteLLM proxy: {settings.LITELLM_PROXY_URL}")
            
            # Call Gemini image generation via LiteLLM
            response = self.client.images.generate(
                model=settings.IMAGE_GEN_MODEL,
                prompt=prompt,
                n=1,
                size="1024x1024",
                quality="standard",
                response_format="b64_json",
                user=user_email,
                extra_body={
                    "metadata": {
                        "application": settings.APP_NAME,
                        "environment": settings.ENVIRONMENT,
                    }
                },
            )

            print(f"[ImageService] Response received: {type(response)}")
            print(f"[ImageService] Response data: {response.data}")
            
            # Extract base64 image data
            if hasattr(response.data[0], 'b64_json'):
                image_base64 = response.data[0].b64_json
            elif hasattr(response.data[0], 'url'):
                # If URL response, download the image
                img_response = requests.get(response.data[0].url)
                image_bytes = img_response.content
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                return {
                    "url": f"/api/chat/attachments/generated/{user_id}/{filename}",
                    "filename": filename,
                    "mime_type": "image/png",
                    "original_prompt": prompt,
                    "size_bytes": len(image_bytes),
                }
            else:
                raise ValueError(f"Unexpected response format: {response.data[0]}")

            print(f"[ImageService] Decoding base64 image...")
            
            # Decode and save to disk
            image_bytes = base64.b64decode(image_base64)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            print(f"[ImageService] Image saved to {filepath} ({len(image_bytes)} bytes)")

            # Return metadata
            return {
                "url": f"/api/chat/attachments/generated/{user_id}/{filename}",
                "filename": filename,
                "mime_type": "image/png",
                "original_prompt": prompt,
                "size_bytes": len(image_bytes),
            }

        except Exception as e:
            print(f"[ImageService] ERROR: {str(e)}")
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
