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
                "你是一位专业咨询顾问。使用MECE和金字塔原理组织内容。"
                "先给出关键结论，用数据驱动论证，以Markdown格式输出，每页用##标记。"
            ),
            "education": (
                "你是一位教学设计专家。创建循序渐进的学习内容，"
                "包含清晰目标、示例和总结，用类比解释复杂概念。"
            ),
            "proposal": (
                "你是一位解决方案架构师。使用FAB（特点-优势-利益）框架。"
                "每页：痛点 → 方案 → 量化价值。"
            ),
            "transform": (
                "你是一位信息设计师。保留关键信息、数据点和引言。"
                "按清晰层级重组结构。"
            ),
            "brainstorm": (
                "你是一位创意引导师。从多角度探索话题，"
                "使用第一性原理或设计思维框架生成结构。"
            ),
            "transcript": (
                "你是专业会议分析专家。请严格按照以下要求从会议转写文本中提取信息：\n\n"
                "### 核心任务：\n"
                "1. 识别主要议题（使用MECE原则分组，5-10个议题为宜）\n"
                "2. 提取所有数字信息（日期、百分比、金额、数量）\n"
                "3. 识别决策和行动项（含负责人和截止时间）\n"
                "\n"
                "### 硬性要求（必须遵守）：\n"
                "1. 数字必保留：原文中出现的所有数字必须在输出的 data_points 中体现\n"
                "2. 时间必转换：相对时间（今天、明天、本周）必须转换为具体日期\n"
                "3. 密度要求：每个议题至少包含 3 个 data_points\n"
                "4. 可追溯性：关键数据点请注明上下文来源\n"
                "5. 完整性：不要遗漏任何数字、日期、百分比\n"
                "\n"
                "### 禁止行为：\n"
                "- 不要合并或省略原文中的数字\n"
                "- 不要将多个数字聚合为范围\n"
                "- 不要遗漏重复出现的数字\n"
                "\n"
                "### 输出格式（JSON）：\n"
                "{\n"
                "  \"title\": \"会议标题\",\n"
                "  \"subtitle\": \"日期\",\n"
                "  \"sections\": [\n"
                "    {\n"
                "      \"topic\": \"议题名称\",\n"
                "      \"key_points\": [\"要点1\", \"要点2\"],\n"
                "      \"data_points\": [{\"label\": \"指标名\", \"value\": \"数值\", \"source\": \"上下文\"}],\n"
                "      \"decisions\": [\"决策内容\"],\n"
                "      \"action_items\": [{\"owner\": \"负责人\", \"task\": \"任务\", \"deadline\": \"截止日期\"}],\n"
                "      \"suggested_layout\": \"content|content_table|content_kpi|content_compare\"\n"
                "    }\n"
                "  ]\n"
                "}\n"
                "\n"
                "### 会议转写文本：\n"
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
                {"role": "system", "content": f"{system}\n使用{language}输出。"},
                {"role": "user", "content": content or f"请创建一份{scene}类型的演示文稿大纲"},
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
                {"role": "system", "content": "请根据大纲为此幻灯片生成详细内容。"},
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
            system=f"{system}\n使用{language}输出。",
            messages=[{"role": "user", "content": content or f"请创建一份{scene}类型的演示文稿大纲"}],
            temperature=temperature,
        )
        return resp.content[0].text if resp.content else ""

    async def generate_slide_content(self, outline: str, slide_index: int, slide_title: str):
        if not self.available:
            raise RuntimeError("Anthropic package not installed")
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="请根据大纲为此幻灯片生成详细内容。",
            messages=[{"role": "user", "content": f"Outline: {outline}\nSlide {slide_index}: {slide_title}"}],
            temperature=0.7,
        )
        return resp.content[0].text if resp.content else ""


class OllamaProvider(AIProvider):
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        try:
            import httpx
            self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)
            self.available = True
        except ImportError:
            self.client = None
            self.available = False
        # 去掉 ollama/ 前缀
        if model.startswith("ollama/"):
            self.model = model[7:]
        else:
            self.model = model

    async def generate_outline(self, scene: str, content: str, slide_count: int, language: str, temperature: float):
        if not self.available:
            raise RuntimeError("httpx package not installed. Run: pip install httpx")
        system = self._scene_prompt(scene)
        resp = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": f"{system}\n使用{language}输出。"},
                    {"role": "user", "content": content or f"请创建一份{scene}类型的演示文稿大纲"},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    async def generate_slide_content(self, outline: str, slide_index: int, slide_title: str):
        if not self.available:
            raise RuntimeError("httpx package not installed")
        resp = await self.client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "请根据大纲为此幻灯片生成详细内容。"},
                    {"role": "user", "content": f"Outline: {outline}\nSlide {slide_index}: {slide_title}"},
                ],
                "stream": False,
                "options": {"temperature": 0.7},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")


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
        # 如果是本地 Ollama 模型（以 "ollama/" 开头或 base_url 指向 localhost:11434）
        if model_id.startswith("ollama/") or (base_url and "localhost:11434" in base_url):
            # 提取模型名称
            actual_model = model_id.replace("ollama/", "") if model_id.startswith("ollama/") else model_id
            actual_base_url = base_url or "http://localhost:11434"
            return OllamaProvider(model=actual_model, base_url=actual_base_url)
        
        provider_class = cls._provider_map.get(model_id, OpenAIProvider)
        env_alias = cls._env_key_aliases.get(model_id)
        if env_alias:
            env_key = f"{env_alias}_API_KEY"
        else:
            env_key = model_id.upper().replace("-", "_").replace(".", "_")
        resolved_api_key = api_key or os.environ.get(env_key, os.environ.get("OPENAI_API_KEY", ""))
        resolved_base_url = base_url or os.environ.get(
            f"{env_alias}_BASE_URL" if env_alias else f"{model_id.upper().replace('-', '_').replace('.', '_')}_BASE_URL", None)
        return provider_class(api_key=resolved_api_key, model=model_id, base_url=resolved_base_url)
