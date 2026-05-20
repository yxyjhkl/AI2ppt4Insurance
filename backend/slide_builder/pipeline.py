"""Generation Pipeline - AI Planner -> Executor with offline fallback.

Coordinates: content input -> AI or rule engine planning -> SVG filling -> PPTX assembly.
Supports multiple scenes (report, education, proposal, transform, brainstorm) and
data-driven mode (Excel parsing -> template mapping -> mechanical slide filling).
"""
from __future__ import annotations
import os
import re
import json
import yaml
import logging
from typing import Optional
from dataclasses import dataclass, field, asdict

from utils.theme_utils import load_theme, resolve_template_dir, DEFAULT_THEME

logger = logging.getLogger(__name__)


@dataclass
class SlideData:
    layout_type: str = "content"
    title: str = ""
    subtitle: Optional[str] = None
    body_items: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    code_block: Optional[str] = None
    notes: str = ""
    page_number: int = 0


@dataclass
class GenerationResult:
    slides: list[SlideData] = field(default_factory=list)
    title: str = ""
    scene: str = ""
    template_id: str = ""
    svg_contents: list[str] = field(default_factory=list)
    pptx_bytes: Optional[bytes] = None
    qa_results: list[dict] = field(default_factory=list)
    mode: str = "offline"
    message: str = ""


class GenerationPipeline:
    SCENE_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts", "scenes")
    SCENE_MAP = {}

    def __init__(self, scene: str = "report", template_id: str = "professional-blue",
                 ai_mode: str = "auto", model: Optional[str] = None,
                 api_key: Optional[str] = None, base_url: Optional[str] = None,
                 canvas_format: str = "16:9", meeting_type: Optional[str] = None,
                 excel_filepath: Optional[str] = None):
        self.scene = scene
        self.meeting_type = meeting_type
        self.excel_filepath = excel_filepath
        self.template_id = template_id
        self.ai_mode = ai_mode
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.canvas_format = canvas_format
        self.template_dir = resolve_template_dir(template_id, os.path.dirname(__file__))
        self.theme = load_theme(self.template_dir)
        self._load_scene_map()

    def _load_scene_map(self):
        if not os.path.isdir(self.SCENE_DIR):
            self.SCENE_MAP = {"report": {"name": "Work Report", "description": ""}}
            return

        def _load_yaml(path: str):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "scene_id" in data:
                    self.SCENE_MAP[data["scene_id"]] = data
            except Exception as e:
                logger.warning(f"Failed to load scene {path}: {e}")

        for fname in os.listdir(self.SCENE_DIR):
            fpath = os.path.join(self.SCENE_DIR, fname)
            if fname.endswith((".yaml", ".yml")):
                _load_yaml(fpath)
            elif os.path.isdir(fpath):
                for sub in os.listdir(fpath):
                    if sub.endswith((".yaml", ".yml")):
                        _load_yaml(os.path.join(fpath, sub))

    async def run(self, input_text: str) -> GenerationResult:
        result = GenerationResult(
            scene=self.scene,
            template_id=self.template_id,
        )

        if self.excel_filepath and self.meeting_type:
            logger.info(f"Data-driven mode: Excel={self.excel_filepath}, meeting={self.meeting_type}")
            result.mode = "data_driven"
            return await self._data_driven_execute(input_text)

        should_use_ai = await self._decide_ai_mode()

        if should_use_ai:
            result.mode = "ai"
            result.message = "使用 AI 模型生成"
            slides_data = await self._ai_plan_execute(input_text)
        else:
            if self.ai_mode == "offline":
                result.message = "已手动指定离线模式"
            elif self.ai_mode == "auto":
                result.message = "AI 服务不可用，已自动切换到离线模式"
            else:
                result.message = "使用离线规则引擎生成"
            result.mode = "offline"
            slides_data = self._offline_plan_execute(input_text)

        if not slides_data:
            result.qa_results.append({"severity": "error", "message": "No slides generated"})
            return result

        result.slides = slides_data
        result.title = slides_data[0].title or "Untitled Presentation"
        svg_contents = self._fill_svg_slides(slides_data)
        result.svg_contents = svg_contents

        result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)
        result.qa_results = self._run_qa(slides_data, svg_contents)

        return result

    async def _decide_ai_mode(self) -> bool:
        if self.ai_mode == "offline":
            return False
        if self.ai_mode == "online":
            return True
        return await self._check_ai_available()

    async def _check_ai_available(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get("http://localhost:11434/api/tags", timeout=3)
                if r.status_code == 200 and r.json().get("models"):
                    logger.info(f"Ollama available | models={len(r.json()['models'])}")
                    return True
                logger.info(f"Ollama responded but no models found | status={r.status_code}")
        except Exception:
            logger.info("Ollama not available")

        try:
            from ai.provider import AIProviderFactory
            model_id = self.model or "gpt-4o"
            provider = AIProviderFactory.create(model_id=model_id, api_key=self.api_key, base_url=self.base_url)
            if hasattr(provider, 'client') and provider.client is not None:
                logger.info(f"Cloud AI provider ready | model={model_id}")
                return True
            logger.info(f"Cloud AI provider created but client is None | model={model_id}")
        except ImportError:
            logger.info(f"AI provider package not installed | model={model_id}")
        except Exception as e:
            logger.info(f"AI provider init failed | model={model_id} | error={e}")

        logger.info("AI unavailable - falling back to offline mode")
        return False

    async def _ai_plan_execute(self, input_text: str) -> list[SlideData]:
        try:
            from ai.provider import AIProviderFactory
        except ImportError:
            logger.warning("AI provider not available, falling back to offline")
            return self._offline_plan_execute(input_text)

        resolved_scene = self.scene
        if self.scene == "insurance" and self.meeting_type:
            resolved_scene = f"insurance_{self.meeting_type}"

        scene_info = self.SCENE_MAP.get(resolved_scene, {})
        system_prompt = scene_info.get("system_prompt", "You are a professional presentation designer.")
        slide_structure = scene_info.get("slide_structure", "")

        planner_prompt = f"""{system_prompt}

You are designing a professional, business-grade PowerPoint presentation. Follow the instructions in the XML tags above precisely.

=== OUTPUT REQUIREMENTS ===
Generate a structured presentation in valid JSON format.

LAYOUT TYPE SELECTION RULES:
- "cover": ONLY the first slide. Must include a compelling title and subtitle.
- "chapter": Section dividers. Use before major thematic shifts.
- "content_table": Use for structured data (numbers, metrics, comparisons). Include markdown tables with "markdown" key.
- "content_two_col": Use for comparing two items, A-vs-B, pros-vs-cons. Set "column":"left" or "column":"right".
- "content_quote": Use for important statements, quotes, or key takeaways.
- "content_code": Use for technical content or structured data formats.
- "content_compare": Use for before/after, current-vs-target comparisons.
- "content_three_col": Use for three-pillar frameworks or tripartite comparisons.
- "content_kpi": Use for KPI dashboards with large number cards, progress bars, and trend indicators.
- "content": Default for narrative text, bullet points, and general information.
- "ending": ONLY the last slide. Summary, next steps, or thank you.

VISUAL RULES:
1. Use 🟢/🟡/🔴 or ✅/⚠️/❌ for status indicators
2. Bold key numbers. Use content_table for data comparison
3. Maximum 5-7 body items per slide
4. One key idea per slide
5. Tables MUST use markdown format: column headers and data rows separated by |---
6. Use 【标签】 prefix for structured business analysis

---
SLIDE STRUCTURE FROM SCENE TEMPLATE:
{slide_structure}

---
User input content to transform into presentation:
{input_text}

CRITICAL: Return ONLY the raw JSON object. No ```json markers, no explanation, no additional text.

JSON OUTPUT STRUCTURE:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "layout_type": "cover",
      "title": "Main Title",
      "subtitle": "Subtitle / Date",
      "body_items": [],
      "tables": [],
      "notes": ""
    }},
    {{
      "layout_type": "content_table",
      "title": "Data Table Title",
      "subtitle": "",
      "body_items": [],
      "tables": [{{"markdown": "| Col1 | Col2 | Col3 |\\n|---|---|---|\\n| Val1 | Val2 | Val3 |"}}],
      "notes": ""
    }},
    {{
      "layout_type": "content_two_col",
      "title": "Comparison Title",
      "subtitle": "",
      "body_items": [
        {{"type": "list_item", "text": "Left point", "level": 0, "column": "left"}},
        {{"type": "list_item", "text": "Right point", "level": 0, "column": "right"}}
      ],
      "tables": [],
      "notes": ""
    }},
    {{
      "layout_type": "content",
      "title": "Section Title",
      "subtitle": "",
      "body_items": [
        {{"type": "list_item", "text": "Main point", "level": 0}}
      ],
      "tables": [],
      "notes": ""
    }},
    {{
      "layout_type": "ending",
      "title": "Summary & Next Steps",
      "subtitle": "",
      "body_items": [{{"type": "list_item", "text": "Action item", "level": 0}}],
      "tables": [],
      "notes": ""
    }}
  ]
}}"""

        provider = AIProviderFactory.create(model_id=self.model or "gpt-4o", api_key=self.api_key, base_url=self.base_url)
        try:
            response = await provider.generate_outline(
                scene=self.scene,
                content=planner_prompt,
                slide_count=10,
                language="zh-CN",
                temperature=0.7,
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._offline_plan_execute(input_text)

        slides_data = self._parse_ai_response(response)
        if not slides_data:
            return self._offline_plan_execute(input_text)
        return slides_data

    def _parse_ai_response(self, response: str) -> list[SlideData]:
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in AI response, falling back to offline")
            return self._offline_fallback("")
        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed: {e}")
            return self._offline_fallback("")

        slides_raw = data.get("slides", [])
        if not slides_raw:
            logger.warning("AI response has no slides array, falling back to offline")
            return self._offline_fallback(data.get("title", ""))

        slides = []
        for i, s in enumerate(slides_raw):
            slides.append(SlideData(
                layout_type=s.get("layout_type", "content"),
                title=s.get("title", ""),
                subtitle=s.get("subtitle"),
                body_items=s.get("body_items", []),
                images=s.get("images", []),
                tables=s.get("tables", []),
                code_block=s.get("code_block"),
                notes=s.get("notes", ""),
                page_number=i + 1,
            ))
        return slides

    async def _data_driven_execute(self, input_text: str) -> GenerationResult:
        from data_driven.excel_parser import parse_excel, ExcelData
        from data_driven.data_mapper import DataMapper, MappedField
        from data_driven.slide_filler import SlideFiller
        from data_driven.data_validator import validate_numbers, ValidationResult

        result = GenerationResult(
            scene=self.scene,
            template_id=self.template_id,
            mode="data_driven",
            message=f"数据驱动生成模式: {self.meeting_type}",
        )

        excel_data: ExcelData = parse_excel(self.excel_filepath)
        if excel_data.errors:
            logger.warning(f"Excel parsing warnings: {excel_data.errors}")
            result.message += f" (解析警告: {'; '.join(excel_data.errors[:2])})"

        if not excel_data.sheets:
            result.qa_results.append({"severity": "error", "category": "parse", "slide": 0,
                                       "message": "Excel文件无有效数据", "detail": None})
            return result

        mapper = DataMapper()
        summary, mapped, warnings = mapper.match(excel_data, self.meeting_type)
        mapped = mapper.extract_data(excel_data, mapped, self.meeting_type)

        logger.info(f"Data mapping: {summary}")
        for w in warnings:
            logger.warning(f"Mapping warning: {w}")

        filler = SlideFiller()

        ai_text: dict = {}
        llm_fields = filler.get_fields_needing_llm(self.meeting_type)

        if llm_fields and await self._decide_ai_mode():
            try:
                from ai.provider import AIProviderFactory
                provider = AIProviderFactory.create(
                    model_id=self.model or "gpt-4o",
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
                extra_context = {"fields_with_analysis_needed": llm_fields}
                prompt = filler.generate_analysis_prompt(
                    self.meeting_type, mapped, excel_data, extra_context
                )
                response = await provider.generate_outline(
                    scene="insurance",
                    content=prompt,
                    slide_count=len(llm_fields),
                    language="zh-CN",
                    temperature=0.7,
                )
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    ai_text = json.loads(json_match.group(0))
                    logger.info(f"LLM analysis generated for {len(ai_text)} fields")
            except Exception as e:
                logger.warning(f"LLM analysis generation failed: {e}")

        filled_slides, extra_ctx = filler.build_slides(
            self.meeting_type, mapped, excel_data, ai_text,
        )

        slides_data = []
        for fs in filled_slides:
            slides_data.append(SlideData(
                layout_type=fs.layout_type,
                title=fs.title,
                subtitle=fs.subtitle,
                body_items=fs.body_items or [],
                tables=fs.tables or [],
                notes=fs.notes or "",
                page_number=fs.page_number,
            ))

        result.message += f" | 生成{len(slides_data)}页幻灯片"

        valid_result = validate_numbers(mapped, slides_data)
        result.qa_results = valid_result.to_qa_list()

        if valid_result.errors or valid_result.warnings:
            result.message += f" | 校验: {valid_result.passed_checks}/{valid_result.total_checks}通过"
            if not valid_result.passed:
                result.message += " (有数据不一致风险)"

        for w in warnings:
            result.qa_results.append({
                "severity": "warning",
                "category": "mapping",
                "slide": 0,
                "message": w,
                "detail": None,
            })

        result.slides = slides_data
        result.title = slides_data[0].title if slides_data else "Untitled"

        svg_contents = self._fill_svg_slides(slides_data)
        result.svg_contents = svg_contents
        result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)

        deck_qa = self._run_qa(slides_data, svg_contents)
        result.qa_results.extend(deck_qa)

        return result

    def _offline_plan_execute(self, input_text: str) -> list[SlideData]:
        try:
            from rule_engine.engine import OfflineRuleEngine
            engine = OfflineRuleEngine(self.template_id)
            result = engine.process(input_text)
            slides = []
            for r in result:
                slides.append(SlideData(
                    layout_type=r.get("layout_type", "content"),
                    title=r.get("title", ""),
                    subtitle=r.get("subtitle"),
                    body_items=r.get("body_items", []),
                    images=r.get("images", []),
                    tables=r.get("tables", []),
                    code_block=r.get("code_block"),
                    notes="",
                    page_number=r.get("page_number", 1),
                ))
            return slides
        except Exception as e:
            logger.error(f"Rule engine failed: {e}")
            return self._offline_fallback(input_text)

    def _offline_fallback(self, text: str) -> list[SlideData]:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            lines = ["Untitled Presentation", "Content goes here."]
        slides = []
        for i, line in enumerate(lines):
            lt = "cover" if i == 0 else ("ending" if i == len(lines) - 1 and len(lines) > 2 else "content")
            slides.append(SlideData(
                layout_type=lt,
                title=line,
                body_items=[],
                page_number=i + 1,
            ))
        return slides

    def _fill_svg_slides(self, slides: list[SlideData]) -> list[str]:
        from slide_builder.svg_filler import SVGFiller
        filler = SVGFiller(self.template_dir, self.theme)

        svg_list = []
        CANVAS_VIEWBOX = {
            "16:9": (1280, 720),
            "4:3": (960, 720),
            "3:4": (720, 960),
            "1:1": (720, 720),
        }
        viewbox_w, viewbox_h = CANVAS_VIEWBOX.get(self.canvas_format, (1280, 720))
        for slide in slides:
            slide_dict = asdict(slide)
            filled = filler.fill("", slide_dict, slide.page_number)

            svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {viewbox_w} {viewbox_h}">
{filled}
</svg>'''
            svg_list.append(svg_template)

        return svg_list

    def _assemble_pptx(self, slides: list[SlideData], svg_contents: list[str]) -> Optional[bytes]:
        try:
            from slide_builder.generator import PPTXGenerator
            generator = PPTXGenerator(self.template_id, self.theme, self.canvas_format)
            slide_dicts = [asdict(s) for s in slides]
            pptx_bytes = generator.generate_from_slide_data(slide_dicts)
            return pptx_bytes
        except Exception as e:
            logger.error(f"PPTX assembly failed: {e}")
            return None

    def _run_qa(self, slides: list[SlideData], svg_contents: list[str]) -> list[dict]:
        from slide_builder.deck_qa import DeckQA
        qa = DeckQA()
        return qa.check_all(slides)


async def run_pipeline(input_text: str, scene: str = "report", template_id: str = "professional-blue",
                        ai_mode: str = "auto", model: Optional[str] = None,
                        api_key: Optional[str] = None, base_url: Optional[str] = None,
                        canvas_format: str = "16:9", meeting_type: Optional[str] = None,
                        excel_filepath: Optional[str] = None) -> GenerationResult:
    pipeline = GenerationPipeline(scene, template_id, ai_mode, model, api_key, base_url, canvas_format, meeting_type, excel_filepath)
    return await pipeline.run(input_text)
