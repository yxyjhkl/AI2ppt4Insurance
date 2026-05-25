"""AI Image Generation Provider — DALL-E / Stability AI integration for slide illustrations."""
from __future__ import annotations
import os
import base64
import logging
from typing import Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)
IMAGE_CACHE_DIR = Path.home() / ".insurdeck" / "image_cache"


class ImageGenProvider:
    """Generate slide illustrations using AI image models."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        ImageGenProvider._ensure_cache()

    @staticmethod
    def _ensure_cache():
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async def generate(self, prompt: str, style: str = "professional", size: str = "1024x1024") -> Optional[str]:
        """Generate an image and return base64 data URL. Returns None on failure."""
        cache_key = hashlib.sha256(f"{prompt}|{style}|{size}|{self.provider}".encode()).hexdigest()[:12]
        cache_file = IMAGE_CACHE_DIR / f"{cache_key}.b64"
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception:
                pass

        if self.provider == "openai":
            result = await self._generate_openai(prompt, size)
        elif self.provider == "stability":
            result = await self._generate_stability(prompt, style, size)
        else:
            return None

        if result:
            try:
                cache_file.write_text(result, encoding="utf-8")
            except Exception:
                pass
        return result

    async def _generate_openai(self, prompt: str, size: str) -> Optional[str]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key or os.environ.get("OPENAI_API_KEY", ""))
            resp = await client.images.generate(
                model="dall-e-3",
                prompt=f"Professional presentation slide illustration: {prompt}. Clean, modern, business style. No text.",
                size=size,
                quality="standard",
                n=1,
            )
            url = resp.data[0].url if resp.data else None
            if url:
                import httpx
                async with httpx.AsyncClient() as http:
                    r = await http.get(url, timeout=30)
                    if r.status_code == 200:
                        b64 = base64.b64encode(r.content).decode("utf-8")
                        return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.warning(f"DALL-E image generation failed: {e}")
        return None

    async def _generate_stability(self, prompt: str, style: str, size: str) -> Optional[str]:
        try:
            api_key = self.api_key or os.environ.get("STABILITY_API_KEY", "")
            import httpx
            w, h = 1024, 1024
            if size == "1792x1024":
                w, h = 1792, 1024
            elif size == "1024x1792":
                w, h = 1024, 1792

            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    "https://api.stability.ai/v2beta/stable-image/generate/core",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"prompt": (None, f"Professional slide illustration: {prompt}. Clean modern design, no text overlays.")},
                    data={"output_format": "png", "width": str(w), "height": str(h)},
                    timeout=60,
                )
                if resp.status_code == 200:
                    b64 = base64.b64encode(resp.content).decode("utf-8")
                    return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.warning(f"Stability AI image generation failed: {e}")
        return None

    async def generate_slide_illustration(self, slide_title: str, slide_body: str = "", layout_type: str = "cover") -> Optional[str]:
        """Generate an illustration prompt from slide content and create an image."""
        prompt = self._build_prompt(slide_title, slide_body, layout_type)
        size = "1792x1024" if layout_type == "cover" else "1024x1024"
        return await self.generate(prompt, size=size)

    def _build_prompt(self, title: str, body: str, layout_type: str) -> str:
        prompts = {
            "cover": f"Elegant abstract background representing '{title}'. Professional business aesthetic, subtle gradients, geometric shapes, no text.",
            "content_kpi": f"Business data visualization concept for '{title}'. Abstract charts, rising arrows, professional metrics theme.",
            "content_table": f"Structured data concept for '{title}'. Clean grid patterns, organized information flow, business reporting aesthetic.",
            "content_compare": f"Side-by-side comparison concept for '{title}'. Split composition, contrast, balance, dual themes.",
            "content_timeline": f"Timeline and journey concept for '{title}'. Flowing path, progression, milestones, forward momentum.",
            "content": f"Professional business illustration for '{title}'. {body[:100] if body else 'Modern abstract business concept'}.",
            "ending": f"Thank you and conclusion illustration. Warm, positive, forward-looking business aesthetic. Abstract celebration theme.",
        }
        return prompts.get(layout_type, prompts["content"])
