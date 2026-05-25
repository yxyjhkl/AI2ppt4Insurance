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

        providers = {
            "openai": self._generate_openai,
            "stability": self._generate_stability,
            "tongyi": self._generate_tongyi,
            "cogview": self._generate_cogview,
            "ernie": self._generate_ernie,
            "spark": self._generate_spark,
        }
        gen_func = providers.get(self.provider)
        if not gen_func:
            logger.warning(f"Unknown image provider: {self.provider}")
            return None

        result = await gen_func(prompt, style, size)
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

    # ---- 国内供应商 ----

    async def _generate_tongyi(self, prompt: str, style: str, size: str) -> Optional[str]:
        """阿里通义万相 (Tongyi Wanxiang)"""
        try:
            api_key = self.api_key or os.environ.get("DASHSCOPE_API_KEY", "")
            import httpx
            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "wanx2.0-t2i-turbo",
                        "input": {"prompt": f"Professional slide illustration: {prompt[:200]}"},
                        "parameters": {"size": "1024*1024", "n": 1},
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("output", {}).get("results", [])
                    if results:
                        url = results[0].get("url")
                        if url:
                            r = await http.get(url, timeout=30)
                            if r.status_code == 200:
                                return f"data:image/png;base64,{base64.b64encode(r.content).decode('utf-8')}"
        except Exception as e:
            logger.warning(f"通义万相 failed: {e}")
        return None

    async def _generate_cogview(self, prompt: str, style: str, size: str) -> Optional[str]:
        """智谱 CogView"""
        try:
            api_key = self.api_key or os.environ.get("ZHIPU_API_KEY", "")
            import httpx
            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    "https://open.bigmodel.cn/api/paas/v4/images/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": "cogview-3", "prompt": f"Professional slide illustration: {prompt[:200]}"},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    img_data = data.get("data", [{}])
                    if img_data:
                        url = img_data[0].get("url")
                        if url:
                            r = await http.get(url, timeout=30)
                            if r.status_code == 200:
                                return f"data:image/png;base64,{base64.b64encode(r.content).decode('utf-8')}"
        except Exception as e:
            logger.warning(f"智谱CogView failed: {e}")
        return None

    async def _generate_ernie(self, prompt: str, style: str, size: str) -> Optional[str]:
        """百度文心一格 (ERNIE-ViLG)"""
        try:
            api_key = self.api_key or os.environ.get("BAIDU_API_KEY", "")
            secret_key = os.environ.get("BAIDU_SECRET_KEY", "")
            import httpx

            # Get access token
            async with httpx.AsyncClient() as http:
                token_resp = await http.post(
                    "https://aip.baidubce.com/oauth/2.0/token",
                    data={"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key},
                    timeout=15,
                )
                if token_resp.status_code != 200:
                    return None
                token = token_resp.json().get("access_token", "")

                resp = await http.post(
                    f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl?access_token={token}",
                    headers={"Content-Type": "application/json"},
                    json={"prompt": f"Professional slide illustration: {prompt[:200]}", "size": "1024x1024"},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    img_data = data.get("data", [{}])
                    if img_data:
                        b64 = img_data[0].get("b64_image") or img_data[0].get("image")
                        if b64:
                            return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.warning(f"文心一格 failed: {e}")
        return None

    async def _generate_spark(self, prompt: str, style: str, size: str) -> Optional[str]:
        """讯飞星火图像生成"""
        try:
            api_key = self.api_key or os.environ.get("SPARK_API_KEY", "")
            api_secret = os.environ.get("SPARK_API_SECRET", "")
            import httpx

            async with httpx.AsyncClient() as http:
                resp = await http.post(
                    "https://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti",
                    headers={"Authorization": f"Bearer {api_key}:{api_secret}", "Content-Type": "application/json"},
                    json={
                        "header": {"app_id": os.environ.get("SPARK_APP_ID", "")},
                        "payload": {"message": {"text": [{"content": f"Professional slide illustration: {prompt[:150]}"}]}},
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("payload", {}).get("choices", {}).get("image", [])
                    if content:
                        b64 = content[0].get("base64_image") or content[0].get("url")
                        if b64 and not b64.startswith("http"):
                            return f"data:image/png;base64,{b64}"
        except Exception as e:
            logger.warning(f"讯飞星火 failed: {e}")
        return None
