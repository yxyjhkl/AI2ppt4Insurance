"""AI Provider abstraction layer with lazy imports."""
from abc import ABC, abstractmethod
from typing import Optional
import os


class AIProvider(ABC):
    @abstractmethod
    async def generate_outline(
        self, scene: str, content: str, slide_count: int,
        language: str, temperature: float
    ) -> str:
        ...

    @abstractmethod
    async def generate_slide_content(
        self, outline: str, slide_index: int, slide_title: str
    ) -> str:
        ...

    @staticmethod
    def _scene_prompt(scene: str) -> str:
        prompts = {
            "report": (
                "You are a professional consultant. Structure the content using MECE and "
                "Pyramid Principle. Start with key conclusions, use data-driven arguments. "
                "Output as Markdown with ## for each slide."
            ),
            "education": (
                "You are an instructional designer. Create progressive learning content with "
                "clear objectives, examples, and summaries. Use analogies for complex concepts."
            ),
            "proposal": (
                "You are a solution architect. Use FAB (Feature-Advantage-Benefit) framework. "
                "Each slide: pain point → solution → quantified value."
            ),
            "transform": (
                "You are an information designer. Preserve key information, data points, and "
                "quotes. Restructure for clarity with proper heading hierarchy."
            ),
            "brainstorm": (
                "You are a creative facilitator. Help explore the topic from multiple angles. "
                "Use frameworks like First Principles or Design Thinking to generate structure."
            ),
        }
        return prompts.get(scene, prompts["report"])


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.available = True
        except ImportError:
            self.client = None
            self.available = False
        self.model = model

    async def generate_outline(self, scene: str, content: str, slide_count: int, language: str, temperature: float):
        if not self.available:
            raise RuntimeError("OpenAI package not installed. Run: pip install openai")
        system = self._scene_prompt(scene)
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"{system}\nOutput in {language}. Generate exactly {slide_count} slides."},
                {"role": "user", "content": content or f"Create a {scene} presentation outline"},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    async def generate_slide_content(self, outline: str, slide_index: int, slide_title: str):
        if not self.available:
            raise RuntimeError("OpenAI package not installed")
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Generate detailed content for this slide based on the outline."},
                {"role": "user", "content": f"Outline: {outline}\nSlide {slide_index}: {slide_title}"},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4", base_url: Optional[str] = None):
        try:
            from anthropic import AsyncAnthropic
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = AsyncAnthropic(**kwargs)
            self.available = True
        except ImportError:
            self.client = None
            self.available = False
        self.model = model

    async def generate_outline(self, scene: str, content: str, slide_count: int, language: str, temperature: float):
        if not self.available:
            raise RuntimeError("Anthropic package not installed. Run: pip install anthropic")
        system = self._scene_prompt(scene)
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=f"{system}\nOutput in {language}. Generate exactly {slide_count} slides.",
            messages=[{"role": "user", "content": content or f"Create a {scene} presentation outline"}],
            temperature=temperature,
        )
        return resp.content[0].text if resp.content else ""

    async def generate_slide_content(self, outline: str, slide_index: int, slide_title: str):
        if not self.available:
            raise RuntimeError("Anthropic package not installed")
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="Generate detailed content for this slide based on the outline.",
            messages=[{"role": "user", "content": f"Outline: {outline}\nSlide {slide_index}: {slide_title}"}],
            temperature=0.7,
        )
        return resp.content[0].text if resp.content else ""


class AIProviderFactory:
    _provider_map = {
        "gpt-4": OpenAIProvider,
        "gpt-4o": OpenAIProvider,
        "gpt-4o-mini": OpenAIProvider,
        "gpt-4.1": OpenAIProvider,
        "claude-opus-4": AnthropicProvider,
        "claude-sonnet-4": AnthropicProvider,
        "claude-haiku-3.5": AnthropicProvider,
        "deepseek-chat": OpenAIProvider,
        "deepseek-reasoner": OpenAIProvider,
        "deepseek-v4-flash": OpenAIProvider,
        "deepseek-v4-pro": OpenAIProvider,
        "qwen-max": OpenAIProvider,
        "qwen-plus": OpenAIProvider,
        "qwen-turbo": OpenAIProvider,
        "doubao-seed-1-6-251015": OpenAIProvider,
        "doubao-pro-32k": OpenAIProvider,
        "doubao-lite-32k": OpenAIProvider,
        "custom-model": OpenAIProvider,
    }

    _env_key_aliases = {
        "deepseek-v4-flash": "DEEPSEEK",
        "deepseek-v4-pro": "DEEPSEEK",
        "deepseek-chat": "DEEPSEEK",
        "deepseek-reasoner": "DEEPSEEK",
    }

    @classmethod
    def create(cls, model_id: str, api_key: Optional[str] = None, base_url: Optional[str] = None) -> AIProvider:
        provider_class = cls._provider_map.get(model_id, OpenAIProvider)
        env_alias = cls._env_key_aliases.get(model_id)
        if env_alias:
            env_key = f"{env_alias}_API_KEY"
        else:
            env_key = model_id.upper().replace("-", "_").replace(".", "_")
        resolved_api_key = api_key or os.environ.get(env_key, os.environ.get("OPENAI_API_KEY", ""))
        resolved_base_url = base_url or os.environ.get(f"{env_key.strip('_API_KEY')}_BASE_URL" if env_alias else f"{model_id.upper().replace('-', '_').replace('.', '_')}_BASE_URL", None)
        return provider_class(api_key=resolved_api_key, model=model_id, base_url=resolved_base_url)
