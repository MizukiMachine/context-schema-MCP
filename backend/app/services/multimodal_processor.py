"""Multimodal processor service

Handles image processing with Pillow and Gemini Vision API.
"""

import io
from typing import Any

from PIL import Image
import google.generativeai as genai

from app.config import settings


class MultimodalProcessor:
    """
    Process images using PIL and analyze with Gemini Vision.
    """

    def __init__(self) -> None:
        """Initialize the multimodal processor."""
        self.gemini_api_key = settings.Gemini_api_key
        self._model = None

        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash-exp")

    async def process_image(self, image_data: bytes) -> dict[str, Any]:
        """
        Process image and extract metadata and AI analysis.

        Args:
            image_data: Raw image bytes

        Returns:
            Dictionary with image metadata and AI analysis
        """
        # Extract basic metadata using PIL
        image = Image.open(io.BytesIO(image_data))

        metadata = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_data),
        }

        # Use Gemini Vision for AI analysis
        analysis_text = ""
        tokens_estimate = 0

        if self._model:
            try:
                pil_image = Image.open(io.BytesIO(image_data))
                response = self._model.generate_content([
                    "Analyze this image and describe in detail:",
                    "1. Main content and visual elements",
                    "2. Text visible (OCR if any)",
                    "3. Key elements and objects, people, colors, actions",
                    "4. Overall purpose or context of the image",
                    pil_image,
                ])

                analysis_text = response.text
                tokens_estimate = len(response.text) // 4
            except Exception as e:
                analysis_text = f"Gemini Vision analysis failed: {e}"
                tokens_estimate = 0

        metadata["analysis"] = analysis_text
        metadata["tokens_estimate"] = tokens_estimate

        return metadata

    async def extract_text_ocr(self, image_data: bytes) -> str:
        """
        Extract text from image using Gemini Vision OCR.

        Args:
            image_data: Raw image bytes

        Returns:
            Extracted text as string
        """
        if not self._model:
            raise ValueError("Gemini API key not configured")

        try:
            image = Image.open(io.BytesIO(image_data))
            response = self._model.generate_content([
                "Extract all visible text from this image. "
                "Return only the text content, nothing else.",
                image,
            ])

            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}") from e

    def get_image_metadata(self, image_data: bytes) -> dict[str, Any]:
        """
        Extract basic image metadata without AI analysis.

        Args:
            image_data: Raw image bytes

        Returns:
            Dictionary with basic image metadata
        """
        image = Image.open(io.BytesIO(image_data))

        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_data),
            "has_transparency": "transparency" in image.info or image.mode == "RGBA",
            "palette": image.palette if image.mode == "P" else None,
        }
