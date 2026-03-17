from __future__ import annotations

import io
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from uuid import uuid4

from app.config import Settings, get_settings
from app.schemas.multimodal import (
    AnalysisRequest,
    AnalysisType,
    MultimodalContextCreate,
    MultimodalStatus,
    MultimodalType,
)

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:  # pragma: no cover - optional dependency
    Image = None

    class UnidentifiedImageError(Exception):
        """Fallback exception when Pillow is unavailable."""


try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None


class MultimodalProcessor:
    """Manage multimodal contexts and optional image analysis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.gemini_api_key = self.settings.gemini_api_key
        self._model = None
        self._contexts: dict[str, dict[str, Any]] = {}

        if self.gemini_api_key and genai is not None:
            genai.configure(api_key=self.gemini_api_key)
            self._model = genai.GenerativeModel(self.settings.gemini_model)

    async def create_context(
        self,
        payload: MultimodalContextCreate,
    ) -> dict[str, Any]:
        """Create a multimodal context from JSON payload."""
        if payload.content_type == MultimodalType.TEXT and not payload.text_content:
            raise ValueError("text_content is required when content_type is 'text'")

        now = self._timestamp()
        context_id = str(uuid4())
        context = {
            "id": context_id,
            "content_type": payload.content_type,
            "status": MultimodalStatus.COMPLETED,
            "original_filename": None,
            "text_content": payload.text_content,
            "analysis": None,
            "metadata": dict(payload.metadata),
            "tokens_estimate": len(payload.text_content or "") // 4,
            "created_at": now,
            "updated_at": now,
        }
        self._contexts[context_id] = context
        return self._serialize_context(context)

    async def create_uploaded_context(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        file_bytes: bytes,
    ) -> dict[str, Any]:
        """Create a multimodal context from uploaded image bytes."""
        if not file_bytes:
            raise ValueError("Uploaded file is empty")

        metadata = self.get_image_metadata(file_bytes)
        now = self._timestamp()
        context_id = str(uuid4())
        context = {
            "id": context_id,
            "content_type": MultimodalType.IMAGE,
            "status": MultimodalStatus.PENDING,
            "original_filename": filename,
            "text_content": None,
            "analysis": None,
            "metadata": metadata,
            "tokens_estimate": 0,
            "created_at": now,
            "updated_at": now,
            "_raw_data": file_bytes,
            "_uploaded_content_type": content_type,
        }
        self._contexts[context_id] = context
        return self._serialize_context(context)

    async def get_context(self, context_id: str) -> dict[str, Any] | None:
        """Return a stored context if it exists."""
        context = self._contexts.get(context_id)
        if context is None:
            return None
        return self._serialize_context(context)

    async def analyze_context(
        self,
        context_id: str,
        request: AnalysisRequest,
    ) -> dict[str, Any]:
        """Analyze a stored multimodal context."""
        context = self._contexts.get(context_id)
        if context is None:
            raise KeyError(context_id)

        now = self._timestamp()
        context["status"] = MultimodalStatus.PROCESSING
        context["updated_at"] = now

        try:
            if request.analysis_type == AnalysisType.METADATA_ONLY:
                result = dict(context.get("metadata", {}))
                tokens_estimate = 0
            elif request.analysis_type == AnalysisType.OCR:
                raw_data = context.get("_raw_data")
                if raw_data is None:
                    raise ValueError("No image data available for OCR")
                extracted_text = await self.extract_text_ocr(raw_data)
                result = {"extracted_text": extracted_text}
                tokens_estimate = len(extracted_text) // 4
                context["text_content"] = extracted_text
                context["analysis"] = None
            else:
                raw_data = context.get("_raw_data")
                if raw_data is not None:
                    result = await self.process_image(raw_data, request.custom_prompt)
                    tokens_estimate = int(result.get("tokens_estimate", 0))
                    context["analysis"] = result.get("analysis")
                    context["metadata"].update(
                        {
                            key: value
                            for key, value in result.items()
                            if key not in {"analysis", "tokens_estimate"}
                        }
                    )
                else:
                    result = self._analyze_text_context(context, request.custom_prompt)
                    tokens_estimate = int(result.get("tokens_estimate", 0))
                    context["analysis"] = result.get("summary")

            context["status"] = MultimodalStatus.COMPLETED
            context["tokens_estimate"] = tokens_estimate
            context["updated_at"] = self._timestamp()

            return {
                "context_id": context_id,
                "analysis_type": request.analysis_type,
                "status": context["status"],
                "result": result,
                "tokens_estimate": tokens_estimate,
                "analyzed_at": context["updated_at"],
            }
        except Exception:
            context["status"] = MultimodalStatus.FAILED
            context["updated_at"] = self._timestamp()
            raise

    async def process_image(
        self,
        image_data: bytes,
        custom_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Process an image and optionally ask Gemini for a richer description."""
        metadata = self.get_image_metadata(image_data)
        analysis_text = ""
        tokens_estimate = 0

        if self._model is not None and Image is not None:
            prompt = custom_prompt or (
                "Analyze this image and describe the main content, visible text, "
                "important objects, colors, actions, and likely purpose."
            )
            try:
                image = Image.open(io.BytesIO(image_data))
                response = self._model.generate_content([prompt, image])
                analysis_text = getattr(response, "text", "") or ""
                tokens_estimate = len(analysis_text) // 4
            except Exception as exc:
                analysis_text = f"Gemini Vision analysis failed: {exc}"

        metadata["analysis"] = analysis_text
        metadata["tokens_estimate"] = tokens_estimate
        return metadata

    async def extract_text_ocr(self, image_data: bytes) -> str:
        """Extract OCR text from an image using Gemini when configured."""
        if self._model is None:
            raise RuntimeError("Gemini API key is not configured for OCR analysis")
        if Image is None:
            raise RuntimeError("Pillow is not installed")

        try:
            image = Image.open(io.BytesIO(image_data))
            response = self._model.generate_content(
                [
                    "Extract all visible text from this image. Return only the text.",
                    image,
                ]
            )
            return (getattr(response, "text", "") or "").strip()
        except Exception as exc:
            raise RuntimeError(f"OCR failed: {exc}") from exc

    def get_image_metadata(self, image_data: bytes) -> dict[str, Any]:
        """Extract basic metadata from image bytes."""
        if Image is None:
            raise RuntimeError("Pillow is not installed")

        try:
            image = Image.open(io.BytesIO(image_data))
        except UnidentifiedImageError as exc:
            raise ValueError("Uploaded file is not a valid image") from exc

        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_bytes": len(image_data),
            "has_transparency": "transparency" in image.info or image.mode == "RGBA",
            "palette": str(image.palette) if image.mode == "P" and image.palette else None,
        }

    def _analyze_text_context(
        self,
        context: dict[str, Any],
        custom_prompt: str | None,
    ) -> dict[str, Any]:
        text_content = (context.get("text_content") or "").strip()
        words = [word for word in text_content.split() if word]
        summary = text_content[:200]
        if len(text_content) > 200:
            summary += "..."

        result = {
            "summary": summary or "No text content available.",
            "char_count": len(text_content),
            "word_count": len(words),
            "tokens_estimate": len(text_content) // 4,
        }
        if custom_prompt:
            result["custom_prompt"] = custom_prompt
        return result

    def _serialize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in context.items()
            if not key.startswith("_")
        }

    def _timestamp(self) -> datetime:
        return datetime.now(timezone.utc)


@lru_cache
def get_multimodal_processor() -> MultimodalProcessor:
    """Return a shared multimodal processor instance."""
    return MultimodalProcessor()


__all__ = ["MultimodalProcessor", "get_multimodal_processor"]
