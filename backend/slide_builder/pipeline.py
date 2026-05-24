"""Generation Pipeline - AI Planner -> Executor with offline fallback."""
from __future__ import annotations
import os, re, json, yaml, time, asyncio, logging, random
from typing import Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from utils.theme_utils import load_theme, resolve_template_dir, DEFAULT_THEME
from utils.json_utils import extract_json, estimate_slide_count, CANVAS_VIEWBOX

logger = logging.getLogger(__name__)


class SmoothProgressUpdater:
    def __init__(self, notify_callback: Callable[[dict], Any],
                 start_pct: int, end_pct: int, stage: str,
                 base_message: str, duration_estimate: float = 8.0,
                 update_interval: float = 0.3):
        self.notify = notify_callback
        self.start_pct = start_pct
        self.end_pct = end_pct
        self.stage = stage
        self.base_message = base_message
        self.duration_estimate = duration_estimate
        self.update_interval = update_interval
        self._task: Optional[asyncio.Task] = None
        self._done = False
        self._start_time = 0.0
        self._current_pct = start_pct

    async def _simulate_progress(self):
        self._start_time = time.time()
        pct_range = self.end_pct - self.start_pct
        suffixes = ["请稍候...", "正在处理...", "正在生成...", "马上就好..."]
        while not self._done:
            elapsed = time.time() - self._start_time
            progress_ratio = min(elapsed / self.duration_estimate, 0.95)
            if progress_ratio < 0.5:
                curve_ratio = 2 * progress_ratio * progress_ratio
            else:
                curve_ratio = 1 - 2 * (1 - progress_ratio) * (1 - progress_ratio)
            current_pct = int(self.start_pct + pct_range * curve_ratio)
            current_pct = min(current_pct, self.end_pct - 1)
            if current_pct > self._current_pct:
                self._current_pct = current_pct
                suffix = random.choice(suffixes) if current_pct % 10 == 0 else ""
                self.notify({"step": current_pct, "total": 100, "percentage": current_pct,
                             "stage": self.stage, "message": f"{self.base_message}{suffix}"})
            await asyncio.sleep(self.update_interval)

    def start(self):
        self._task = asyncio.create_task(self._simulate_progress())

    def complete(self, final_message: Optional[str] = None):
        self._done = True
        if self._task:
            self._task.cancel()
        self.notify({"step": self.end_pct, "total": 100, "percentage": self.end_pct,
                     "stage": self.stage, "message": final_message or f"{self.base_message}完成"})

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.complete()
        return False


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

    AUTO_SCENE_TEMPLATE_MAP = {
        "report": "professional-blue", "education": "education-warm",
        "proposal": "corporate-navy", "brainstorm": "creative-vibrant",
        "transform": "modern-geometric", "insurance": "professional-blue",
        "enhance": "corporate-navy",
    }
    SCENE_KEYWORD_MAP = {
        "report": ["quarterly", "annual", "summary", "review", "report", "performance", "KPI", "metric"],
        "proposal": ["proposal", "plan", "budget", "strategy", "roadmap"],
        "education": ["training", "course", "learn", "tutorial", "guide", "skill"],
        "brainstorm": ["brainstorm", "creative", "idea", "innovation", "explore"],
        "insurance": ["insurance", "premium", "claim", "policy", "product launch"],
        "transform": ["optimize", "upgrade", "transform", "improve", "migrate"],
    }

    VALID_LAYOUT_TYPES = {
        "cover", "chapter", "toc", "content", "content_two_col",
        "content_three_col", "content_table", "content_code",
        "content_quote", "content_compare", "content_kpi", "ending",
        "content_matrix", "content_timeline", "content_waterfall",
        "content_gauge", "content_ranking", "content_funnel"
    }

    def __init__(self, scene: str = "report", template_id: str = "professional-blue",
                 ai_mode: str = "auto", auto_mode: bool = False,
                 model: Optional[str] = None,
                 api_key: Optional[str] = None, base_url: Optional[str] = None,
                 canvas_format: str = "16:9", meeting_type: Optional[str] = None,
                 excel_filepath: Optional[str] = None, custom_style: Optional[str] = None,
                 include_images: bool = True, progress_callback=None):
        self.scene = scene
        self.meeting_type = meeting_type
        self.excel_filepath = excel_filepath
        self.custom_style = custom_style
        self.include_images = include_images
        self.template_id = template_id
        self.ai_mode = ai_mode
        self.auto_mode = auto_mode
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.canvas_format = canvas_format
        self.template_dir = resolve_template_dir(template_id, os.path.dirname(__file__))
        self.theme = load_theme(self.template_dir)
        self._load_scene_map()
        self._progress_callback = progress_callback
        self._progress_step = 0
        self._total_steps = 100

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

    def _notify_progress(self, stage: str, message: str, pct: int):
        if not self._progress_callback:
            return
        try:
            progress = {"step": int(pct), "total": self._total_steps,
                        "percentage": pct, "stage": stage, "message": message}
            if asyncio.iscoroutinefunction(self._progress_callback):
                asyncio.create_task(self._progress_callback(progress))
            else:
                self._progress_callback(progress)
        except Exception:
            pass

    def _create_smooth_progress(self, start_pct: int, end_pct: int, stage: str,
                                base_message: str, duration_estimate: float = 8.0):
        def callback(progress: dict):
            if self._progress_callback:
                if asyncio.iscoroutinefunction(self._progress_callback):
                    asyncio.create_task(self._progress_callback(progress))
                else:
                    self._progress_callback(progress)
        return SmoothProgressUpdater(callback, start_pct, end_pct, stage,
                                     base_message, duration_estimate)

    def _auto_analyze_content(self, input_text: str) -> dict:
        text_lower = input_text.lower()
        scores = {}
        for scene, keywords in self.SCENE_KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            scores[scene] = score * (1.5 if scene == "insurance" else 1.0)

        best_scene = "report"
        best_score = 0
        for scene, score in scores.items():
            if score > best_score:
                best_score = score
                best_scene = scene

        if best_score == 0:
            best_scene = "report" if len(input_text) > 2000 else "brainstorm"

        best_template = self.AUTO_SCENE_TEMPLATE_MAP.get(best_scene, "professional-blue")
        est_slides = estimate_slide_count(input_text)
        est_slides = min(est_slides + 2, 50)

        logger.info(f"Auto analysis: scene={best_scene}, template={best_template}, slides={est_slides}")
        return {"scene": best_scene, "template": best_template, "slide_count": est_slides}

    async def run(self, input_text: str) -> GenerationResult:
        result = GenerationResult(scene=self.scene, template_id=self.template_id)

        if self.auto_mode:
            self._notify_progress("分析", "正在分析内容类型...", 3)
            await asyncio.sleep(0.1)
            analysis = self._auto_analyze_content(input_text)
            self.scene = analysis["scene"]
            self.meeting_type = self.meeting_type
            self.template_id = analysis["template"]
            self.template_dir = resolve_template_dir(self.template_id, os.path.dirname(__file__))
            self.theme = load_theme(self.template_dir)
            scene_name = self.SCENE_MAP.get(self.scene, {}).get("name", self.scene)
            self._notify_progress("分析",
                f"已识别场景 | 模板:{self.template_id} | 预计{analysis['slide_count']}页", 8)
            result.scene = self.scene
            result.template_id = self.template_id

        if self.excel_filepath and self.meeting_type:
            result.mode = "data_driven"
            return await self._data_driven_execute(input_text)

        self._notify_progress("初始化", "正在分析输入内容...", 3)
        await asyncio.sleep(0.1)
        should_use_ai = await self._decide_ai_mode()
        is_transcript = self._detect_transcript(input_text)
        self._notify_progress("初始化", "初始化完成", 10)

        if is_transcript and should_use_ai:
            result.mode = "transcript"
            result.message = "Meeting transcript processing"
            transcript_result = await self._transcript_execute(input_text)
            if len(transcript_result.slides) < 3:
                logger.warning(f"Transcript only generated {len(transcript_result.slides)} slides, falling back")
                return await self._ai_generate_with_polish(input_text, result)
            return transcript_result

        if should_use_ai:
            return await self._ai_generate_with_polish(input_text, result)
        else:
            result.mode = "offline"
            result.message = "Offline rule engine"
            self._notify_progress("规划", "正在规划内容结构...", 10)
            await asyncio.sleep(0.2)
            slides_data = self._offline_plan_execute(input_text)
            self._notify_progress("规划", "内容规划完成", 25)

        if not slides_data:
            result.qa_results.append({"severity": "error", "message": "未能生成任何幻灯片"})
            return result

        result.slides = slides_data
        result.title = (slides_data[0].title if slides_data else "") or "未命名文稿"
        self._render_and_assemble(result, slides_data);
        return result

    async def _ai_generate_with_polish(self, input_text: str,
                                       result: GenerationResult) -> GenerationResult:
        result.mode = "ai"
        result.message = "AI powered generation"

        progress = self._create_smooth_progress(10, 55, "AI规划",
            "AI 正在设计幻灯片结构...", duration_estimate=12.0)
        progress.start()
        try:
            slides_data = await self._ai_plan_execute(input_text)
        finally:
            progress.complete("内容规划完成")

        if not slides_data:
            result.qa_results.append({"severity": "error", "message": "未能生成任何幻灯片"})
            return result

        slides_data = self._enforce_content_quality(slides_data)
        slides_data = self._enforce_structure(slides_data)

        # Title fix: dedicated short AI pass to rewrite poor titles
        self._notify_progress("标题修正", "AI 正在优化幻灯片标题...", 52)
        await asyncio.sleep(0.1)
        try:
            slides_data = await self._fix_titles(slides_data, input_text)
        except Exception as e:
            logger.warning(f"Title fix failed, continuing: {e}")

        result.slides = slides_data
        result.title = (slides_data[0].title if slides_data else "") or "未命名文稿"

        # Visual check: AI reviews slide quality before rendering
        self._notify_progress("视觉检查", "AI 正在进行视觉质量审查...", 70)
        await asyncio.sleep(0.1)
        try:
            visual_qa = await self._visual_check(slides_data, input_text)
            if visual_qa:
                result.qa_results.extend(visual_qa)
        except Exception as e:
            logger.warning(f"Visual check failed, continuing: {e}")

        self._render_and_assemble(result, slides_data)

        if self.auto_mode:
            self._notify_progress("美化", "AI 正在美化幻灯片...", 92)
            await asyncio.sleep(0.1)
            try:
                slides_data = await self._auto_polish_slides(slides_data, input_text)
                result.slides = slides_data
                result.title = (slides_data[0].title if slides_data else "") or result.title
                pp = self._create_smooth_progress(88, 95, "美化",
                    "AI 正在优化视觉效果...", duration_estimate=6.0)
                pp.start()
                try:
                    svg_contents = self._fill_svg_slides(slides_data)
                finally:
                    pp.complete("美化完成")
                result.svg_contents = svg_contents
                result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)
            except Exception as e:
                logger.warning(f"Auto polish failed, keeping original: {e}")

        return result

    async def _render_and_assemble(self, result: GenerationResult, slides_data: list[SlideData]):
        progress = self._create_smooth_progress(55, 75, "渲染",
            "正在渲染 SVG 预览...", duration_estimate=3.0)
        progress.start()
        try:
            svg_contents = self._fill_svg_slides(slides_data)
        finally:
            progress.complete("渲染完成")
        result.svg_contents = svg_contents

        self._notify_progress("生成", "正在组装 PPTX 文件...", 75)
        await asyncio.sleep(0.2)
        result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)
        self._notify_progress("生成", "PPTX 组装完成", 90)

        self._notify_progress("质检", "正在进行内容质检...", 90)
        await asyncio.sleep(0.1)
        result.qa_results = self._run_qa(slides_data, svg_contents)
        self._notify_progress("质检", "质检完成", 98)
        self._notify_progress("完成", "生成完毕", 100)

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
                    return True
        except Exception:
            pass
        try:
            from ai.provider import AIProviderFactory
            model_id = self.model or "gpt-4o"
            provider = AIProviderFactory.create(model_id=model_id, api_key=self.api_key, base_url=self.base_url)
            if hasattr(provider, 'client') and provider.client is not None:
                return True
        except Exception:
            pass
        return False

    async def _ai_plan_execute(self, input_text: str) -> list[SlideData]:
        try:
            from ai.provider import AIProviderFactory
        except ImportError:
            return self._offline_plan_execute(input_text)

        resolved_scene = self.scene
        if self.scene == "insurance" and self.meeting_type:
            resolved_scene = f"insurance_{self.meeting_type}"

        scene_info = self.SCENE_MAP.get(resolved_scene, {})
        system_prompt = scene_info.get("system_prompt", "You are a professional presentation designer.")
        slide_structure = scene_info.get("slide_structure", "")
        design_req = scene_info.get("design_requirements", "") or "N/A"
        custom_style_txt = self.custom_style or ""

        prompt_template = self._load_prompt_template()
        planner_prompt = prompt_template
        planner_prompt = planner_prompt.replace("{system_prompt}", system_prompt)
        planner_prompt = planner_prompt.replace("{input_text}", input_text[:12000])
        planner_prompt = planner_prompt.replace("{design_req}", design_req)
        planner_prompt = planner_prompt.replace("{custom_style_txt}", custom_style_txt)
        planner_prompt = planner_prompt.replace("{slide_structure}", str(slide_structure))

        if self.include_images:
            planner_prompt += "\n\nInclude relevant images where appropriate. Use the 'images' field with descriptive alt text for each image suggestion."

        provider = AIProviderFactory.create(model_id=self.model or "gpt-4o",
                                            api_key=self.api_key, base_url=self.base_url)
        self._notify_progress("AI生成", "正在调用 AI 模型...", 25)
        try:
            response = await provider.generate_outline(
                scene=self.scene, content=planner_prompt, slide_count=10,
                language="zh-CN", temperature=0.4)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return self._offline_plan_execute(input_text)

        slides_data = self._parse_ai_response(response)
        if not slides_data:
            logger.info("First AI parse failed, retrying...")
            self._notify_progress("AI生成", "AI 正在修正输出格式...", 30)
            try:
                retry_response = await provider.generate_outline(
                    scene=self.scene,
                    content="上次回复格式无效，请返回纯JSON对象包含slides数组。不要markdown标记，不要解释。",
                    slide_count=estimate_slide_count(input_text),
                    language="zh-CN", temperature=0.3)
                slides_data = self._parse_ai_response(retry_response)
            except Exception as e2:
                logger.error(f"AI retry also failed: {e2}")
        if not slides_data:
            return self._offline_plan_execute(input_text)
        return slides_data

    async def _fix_titles(self, slides: list[SlideData], input_text: str) -> list[SlideData]:
        """Title correction: rule-based fix first, then optional AI enhancement."""
        
        # Step 1: Rule-based fixes (always runs, never fails)
        rule_changes = 0
        for s in slides:
            title = (s.title or "").strip()
            if not title:
                # Generate from body content
                body_preview = " ".join(
                    b.get("text", "")[:40] for b in (s.body_items or [])[:2]
                    if isinstance(b, dict) and b.get("text", "").strip()
                )[:40]
                s.title = body_preview or "内容页"
                continue

            # Fix 1: Truncate overly long titles
            if len(title) > 30:
                rule_changes += 1
                for sep in ["，", "。", "、", "；", "：", "——"]:
                    pos = title.find(sep, 8, 28)
                    if pos > 0:
                        title = title[:pos]
                        break
                else:
                    title = title[:28]
                s.title = title

            # Fix 2: Strip weak opening words
            weak_starts = ["根据", "关于", "针对", "对于", "本次", "当前", "目前"]
            for ws in weak_starts:
                if title.startswith(ws) and len(title) > 10:
                    # Try to keep the meaningful part
                    for sep in ["，", "。", "、", "："]:
                        pos = title.find(sep, 4)
                        if pos > 0 and pos < 25:
                            s.title = title[pos+1:].strip()
                            break
                    break

            # Fix 3: If title is just a noun phrase (no conclusion), try to improve
            if "的" in title and "分析" in title and len(title) <= 12:
                # Generic analysis title, need substance
                body = " ".join(
                    b.get("text", "")[:30] for b in (s.body_items or [])[:1]
                    if isinstance(b, dict) and b.get("text", "").strip()
                )
                if body and "：" in body:
                    s.title = body.split("：")[0].strip()[:25]

        if rule_changes > 0:
            logger.info(f"Title rule-fix: {rule_changes} titles adjusted")

        # Step 2: AI enhancement (best-effort)
        try:
            from ai.provider import AIProviderFactory
            provider = AIProviderFactory.create(model_id=self.model or "gpt-4o",
                                                api_key=self.api_key, base_url=self.base_url)

            titles_snapshot = "\n".join(
                f"P{s.page_number} [{s.layout_type}] current='{s.title}' body='{'; '.join(b.get('text','')[:40] for b in (s.body_items or []) if isinstance(b, dict))[:100]}'"
                for s in slides[:12]
            )

            fix_prompt = f"""重写以下{len(slides)}页PPT的标题。每个标题≤20字，高度概括核心结论。

当前标题：
{titles_snapshot}

规则：标题必须是核心结论而非描述。拒绝空洞词如"项目背景""现状分析"。
仅返回JSON数组，每个元素格式：{{"title": "新标题"}}。共{len(slides)}个。

原文摘要：{input_text[:300]}"""

            response = await provider.generate_outline(
                scene="report", content=fix_prompt, slide_count=3,
                language="zh-CN", temperature=0.3)
        except Exception as e:
            logger.warning(f"Title AI fix unavailable: {e}")
            return slides

        json_str = extract_json(response)
        if not json_str:
            return slides

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return slides

        # Handle both formats: [{"title": "..."}] or {"slides": [{"title": "..."}]}
        fixed = data if isinstance(data, list) else data.get("slides", [])
        if not fixed:
            return slides

        ai_changes = 0
        for i, s in enumerate(slides):
            if i < len(fixed) and isinstance(fixed[i], dict):
                new_title = str(fixed[i].get("title", "")).strip()
                if new_title and len(new_title) <= 30:
                    s.title = new_title
                    ai_changes += 1

        if ai_changes > 0:
            logger.info(f"Title AI-fix: {ai_changes} titles enhanced")
        return slides

    async def _visual_check(self, slides: list[SlideData], input_text: str) -> list[dict]:
        """AI visual quality review: check each slide for design issues."""
        try:
            from ai.provider import AIProviderFactory
        except ImportError:
            return []

        slides_snapshot = []
        for s in slides:
            body = " | ".join(b.get("text", "")[:40] for b in (s.body_items or [])
                             if isinstance(b, dict) and b.get("text", "").strip())
            has_table = any(isinstance(t, dict) and t.get("markdown") for t in (s.tables or []))
            slides_snapshot.append(
                f"P{s.page_number} [{s.layout_type}] title='{s.title[:50]}' "
                f"body_items={len([b for b in (s.body_items or []) if isinstance(b, dict) and b.get('text','').strip()])} "
                f"has_table={has_table} preview='{body[:80]}'"
            )
        slides_text = "\n".join(slides_snapshot)

        check_prompt = f"""Review this {len(slides)}-slide PPT for visual quality issues. Check each slide.

Slides:
{slides_text}

Checklist (per slide):
1. TEXT DENSITY: Too much text (>150 chars body)? Too little (<2 items)?
2. LAYOUT FIT: Does the layout match the content type? (data→table/KPI, comparison→two_col, story→content)
3. MISSING ELEMENTS: Should this slide have a table/image/chart but doesn't?
4. TITLE QUALITY: Is the title specific and informative, or vague/generic?
5. READABILITY: Any potential readability issues?

Return JSON with findings (only flag real issues, max 8):
{{"findings": [
  {{"severity": "warning|info|suggestion", "slide": 1, "category": "visual", "message": "Issue description", "detail": "Suggestion"}}
]}}
Only flag pages with actual issues. Return ONLY valid JSON, no explanation."""

        provider = AIProviderFactory.create(model_id=self.model or "gpt-4o",
                                            api_key=self.api_key, base_url=self.base_url)
        try:
            response = await provider.generate_outline(
                scene="report", content=check_prompt, slide_count=3,
                language="zh-CN", temperature=0.2)
        except Exception as e:
            logger.warning(f"Visual check AI call failed: {e}")
            return []

        json_str = extract_json(response)
        if not json_str:
            return []
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return []

        findings = data.get("findings", [])
        severity_to_level = {"error": "P0", "warning": "P1", "info": "P2", "suggestion": "P3"}
        result = []
        for f in findings[:8]:
            if isinstance(f, dict) and f.get("message"):
                sev = f.get("severity", "info")
                result.append({
                    "severity": sev,
                    "level": severity_to_level.get(sev, "P2"),
                    "category": "visual_check",
                    "slide": f.get("slide", 0),
                    "message": str(f.get("message", "")),
                    "detail": str(f.get("detail", "")) if f.get("detail") else None,
                })
        if result:
            logger.info(f"Visual check: {len(result)} findings")
        return result

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "auto_mode_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return "{system_prompt}\n\nCreate a presentation based on:\n{input_text}"

    def _parse_ai_response(self, response: str) -> list[SlideData]:
        json_str = extract_json(response)
        if not json_str:
            return self._offline_fallback("")
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode failed: {e}")
            return self._offline_fallback("")

        slides_raw = data.get("slides", [])
        if not slides_raw:
            return self._offline_fallback(data.get("title", ""))

        slides = []
        for i, s in enumerate(slides_raw):
            slides.append(SlideData(
                layout_type=s.get("layout_type", "content"),
                title=s.get("title", ""),
                subtitle=s.get("subtitle"),
                body_items=s.get("body_items", []),
                images=s.get("images", []),
                tables=self._normalize_tables(s.get("tables", [])),
                code_block=s.get("code_block"),
                notes=s.get("notes", ""),
                page_number=i + 1,
            ))
        return slides

    @staticmethod
    def _normalize_tables(tables_raw) -> list[dict]:
        if not tables_raw or not isinstance(tables_raw, list):
            return []
        normalized = []
        for t in tables_raw:
            if isinstance(t, dict):
                md_val = t.get("markdown")
                if isinstance(md_val, list):
                    md_val = "\n".join(str(line) for line in md_val)
                if md_val and isinstance(md_val, str):
                    normalized.append({"markdown": md_val})
                elif t:
                    rows = [f"| {k} | {v} |" for k, v in t.items() if not isinstance(v, (list, dict))]
                    if rows:
                        normalized.append({"markdown": "\n".join(rows)})
            elif isinstance(t, list) and t:
                if all(isinstance(r, list) for r in t):
                    header = t[0]
                    rows = ["| " + " | ".join(str(c) for c in header) + " |"]
                    rows.append("|" + "|".join(["---"] * len(header)) + "|")
                    for row in t[1:]:
                        cols = [str(c) for c in row]
                        while len(cols) < len(header):
                            cols.append("")
                        rows.append("| " + " | ".join(cols[:len(header)]) + " |")
                    normalized.append({"markdown": "\n".join(rows)})
                else:
                    cols = [str(c) for c in t]
                    rows = ["| " + " | ".join(cols) + " |"]
                    normalized.append({"markdown": "\n".join(rows)})
            elif isinstance(t, str) and t.strip():
                normalized.append({"markdown": t})
        return normalized

    def _enforce_content_quality(self, slides: list[SlideData]) -> list[SlideData]:
        REQUIRES_CONTENT = {
            "content", "content_two_col", "content_three_col", "content_compare",
            "content_kpi", "content_timeline", "content_ranking",
            "content_waterfall", "content_gauge", "content_funnel", "content_matrix",
        }
        layout_types_used = set()
        for s in slides:
            layout_types_used.add(s.layout_type)
            if s.layout_type in REQUIRES_CONTENT:
                body_count = len([b for b in (s.body_items or [])
                                  if isinstance(b, dict) and b.get("text", "").strip()])
                if body_count < 3 and s.layout_type != "content_table":
                    filler = [
                        {"type": "list_item", "text": f"[补充要点] 更多关于 '{s.title}' 的细节", "level": 0},
                        {"type": "list_item", "text": "根据实际情况进一步补充完善", "level": 0},
                        {"type": "list_item", "text": "建议结合具体数据调整优化", "level": 0},
                    ]
                    if s.body_items:
                        s.body_items = list(s.body_items) + filler[max(0, 3 - body_count):]
                    else:
                        s.body_items = filler

            # Title quality check: detect low-quality titles
            if s.title:
                title = s.title.strip()
                bad_patterns = [
                    (len(title) > 35, 'Title too long (>35 chars), likely a text excerpt'),
                    (title.startswith('According') or title.startswith('About'), 'Title starts with weak opening words'),
                    (title.count(',') >= 2 and len(title) > 25, 'Title has multiple commas, likely a sentence fragment'),
                ]
                flagged = [msg for condition, msg in bad_patterns if condition]
                if flagged:
                    logger.warning(f"Title quality flags for P{s.page_number} '{title[:40]}': {'; '.join(flagged)}")

        if len(layout_types_used) < 3 and len(slides) >= 5:
            logger.warning(f"Layout variety low: only {len(layout_types_used)} types used")
        return slides

    def _enforce_structure(self, slides: list[SlideData]) -> list[SlideData]:
        """Auto-fix structure: numbered chapters, TOC with descriptions, two-col conversion."""
        if len(slides) < 3:
            return slides

        # 1. Ensure first slide is cover
        if slides[0].layout_type != "cover":
            slides[0].layout_type = "cover"

        # 2. Detect existing chapters and extract meaningful names
        chapter_titles = []
        chapter_indices = []
        for i, s in enumerate(slides):
            if i == 0 or i == len(slides) - 1:
                continue
            if s.layout_type == "chapter":
                chapter_titles.append(s.title)
                chapter_indices.append(i)

        # 3. If no chapters, auto-generate from slide content
        if not chapter_titles and len(slides) >= 5:
            num_chapters = min(4, max(2, (len(slides) - 2) // 2))
            seg_size = max(1, (len(slides) - 2) // num_chapters)
            
            # Extract chapter names from first slide of each segment
            chapter_names = []
            for ci in range(num_chapters):
                start = 1 + ci * seg_size
                if start < len(slides) - 1:
                    sample = slides[start]
                    # Extract key theme from title and body
                    keywords = []
                    body_text = " ".join(
                        b.get("text","")[:30] for b in (sample.body_items or [])[:2]
                        if isinstance(b, dict) and b.get("text","").strip()
                    )
                    combined = sample.title + " " + body_text
                    
                    # Common business themes to look for
                    theme_map = {
                        "数据": "数据概览", "指标": "核心指标", "达成": "目标达成", "KPI": "核心KPI",
                        "发现": "关键发现", "现状": "现状分析", "概览": "全景概览",
                        "问题": "问题诊断", "挑战": "挑战分析", "瓶颈": "瓶颈识别", "根因": "根因分析",
                        "方案": "解决方案", "策略": "策略规划", "举措": "行动举措",
                        "实施": "实施计划", "时间": "时间规划", "行动": "行动计划", "执行": "执行方案",
                    }
                    for kw, name in theme_map.items():
                        if kw in combined and any(k not in name for k in [n for n in chapter_names]):
                            chapter_names.append(f"{name}: {sample.title[:12]}")
                            break
                    else:
                        chapter_names.append(sample.title[:15])

            # Insert chapter slides
            new_slides = [slides[0]]
            for ci in range(num_chapters):
                cname = chapter_names[ci] if ci < len(chapter_names) else f"主题 {ci+1}"
                ch = SlideData(layout_type="chapter", title=cname, page_number=0)
                new_slides.append(ch)
                chapter_titles.append(cname)
                start = 1 + ci * seg_size
                end = min(1 + (ci + 1) * seg_size, len(slides) - 1) if ci < num_chapters - 1 else len(slides) - 1
                for s in slides[start:end]:
                    new_slides.append(s)
            new_slides.append(slides[-1])
            slides = new_slides

        # 4. Add 01-09 numbering to chapter titles
        num = 1
        for s in slides:
            if s.layout_type == "chapter":
                clean = s.title
                # Remove existing numbering
                for prefix in ["一、", "二、", "三、", "四、", "五、", "六、"]:
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):]
                        break
                clean = clean.strip()
                if len(clean) > 18:
                    clean = clean[:18]
                s.title = f"{num:02d}  {clean}"
                # Update chapter_titles reference
                for i, ct in enumerate(chapter_titles):
                    if ct in s.title or s.title in ct:
                        chapter_titles[i] = s.title
                        break
                num += 1

        # 5. Richer TOC with descriptions extracted from subsequent slides
        if chapter_titles and len(slides) >= 4:
            toc_items = []
            chap_count = 0
            for s in slides:
                if s.layout_type == "chapter":
                    chap_count += 1
                    # Find the first content slide after this chapter for description
                    desc = ""
                    for s2 in slides[slides.index(s)+1:]:
                        if s2.layout_type not in ("chapter", "toc", "cover"):
                            body = " ".join(
                                b.get("text","")[:20] for b in (s2.body_items or [])[:2]
                                if isinstance(b, dict) and b.get("text","").strip()
                            )
                            if body:
                                desc = body[:50]
                            break
                    toc_items.append({
                        "type": "list_item", 
                        "text": f"{s.title}" + (f" — {desc}" if desc else ""),
                        "level": 0
                    })
            
            if toc_items:
                toc = SlideData(layout_type="toc", title="汇报目录",
                              body_items=toc_items, page_number=0)
                # Insert after cover
                insert_pos = 1
                for i, s in enumerate(slides):
                    if s.layout_type == "chapter":
                        insert_pos = i
                        break
                slides.insert(min(insert_pos, len(slides)), toc)

        # 6. Convert suitable content pages to two-col for visual variety
        two_col_count = sum(1 for s in slides if s.layout_type in ("content_two_col", "content_compare"))
        if two_col_count < max(2, len(slides) // 4):
            converted = 0
            for s in slides:
                if converted >= 2:
                    break
                if s.layout_type == "content" and len(s.body_items) >= 4:
                    items = [b for b in s.body_items if isinstance(b, dict) and b.get("text","").strip()]
                    mid = len(items) // 2
                    for j, it in enumerate(items):
                        it["column"] = "left" if j < mid else "right"
                    s.layout_type = "content_two_col"
                    converted += 1
            if converted:
                logger.info(f"Converted {converted} content pages to two-col layout")

        # 7. Ensure proper ending
        last = slides[-1]
        if last.layout_type not in ("ending", "cover"):
            last.layout_type = "ending"
            if len(last.title) > 20 or not last.title:
                last.title = "总结与下一步行动"

        # 8. Renumber
        for i, s in enumerate(slides):
            s.page_number = i + 1

        return slides

    async def _auto_polish_slides(self, slides: list[SlideData],
                                   input_text: str) -> list[SlideData]:
        try:
            from ai.provider import AIProviderFactory
        except ImportError:
            return slides

        slides_snapshot = []
        for s in slides:
            body_text = "\n".join(
                b.get("text", "") for b in (s.body_items or []) if isinstance(b, dict))
            slides_snapshot.append(f"P{s.page_number} [{s.layout_type}] {s.title}\n{body_text}")
        slides_text = "\n---\n".join(slides_snapshot)

        polish_prompt = f"""你是一位顶级PPT美化师。请对以下AI生成的幻灯片内容进行标题修正和内容润色。

=== 原始素材 ===
{input_text[:2000]}

=== 当前幻灯片（共{len(slides)}页） ===
{slides_text}

=== 核心任务：标题重写（最高优先级） ===
当前标题普遍存在问题——多数是截取原文长句，缺乏概括提炼。请逐一检查并重写：

标题质量铁律：
1. 精炼：每个标题 ≤ 25个字，越长越差
2. 概括：标题 = 该页的核心结论，不是描述
3. 有力：用数据说话，用动词驱动

反面教材 → 正面示范：
  "根据第一季度经营数据分析保费收入变化" → "Q1保费达1,280万，同比增长12%"
  "关于本次活动的几个方面介绍" → "三大亮点：客户增长·转化提升·成本下降"
  "项目背景及现状问题分析" → "增员放缓是当前首要瓶颈"
  "2024年工作总结汇报" → "全年业绩突破目标，三大渠道齐增长"

=== 次要任务：内容润色 ===
- 每页保持3-7条要点，稀疏的适当补充
- 数据密集页改为 content_table 或 content_kpi 布局
- 封面标题要有冲击力，副标题点明核心价值
- 结尾必须有明确的行动建议

=== 输出格式 ===
返回纯JSON，不要任何额外文字：
{{
  "title": "优化后的总标题（≤20字）",
  "slides": [
    {{
      "layout_type": "content",
      "title": "优化后的标题（≤25字，高度概括）",
      "subtitle": "",
      "body_items": [{{"type": "list_item", "text": "要点内容", "level": 0}}],
      "tables": [],
      "notes": ""
    }}
  ]
}}

必须保持相同的幻灯片数量（{len(slides)}页），只优化不改结构。
只返回有效JSON，不要markdown标记。"""

        provider = AIProviderFactory.create(model_id=self.model or "gpt-4o",
                                            api_key=self.api_key, base_url=self.base_url)
        self._notify_progress("美化", "AI 正在优化标题和内容...", 88)
        try:
            response = await provider.generate_outline(
                scene=self.scene, content=polish_prompt,
                slide_count=len(slides), language="zh-CN", temperature=0.4)
        except Exception as e:
            logger.warning(f"Polish AI call failed: {e}")
            return slides

        json_str = extract_json(response)
        if not json_str:
            return slides
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return slides

        polished_raw = data.get("slides", [])
        if len(polished_raw) != len(slides):
            return slides

        polished = []
        for i, s in enumerate(slides):
            pr = polished_raw[i]
            polished.append(SlideData(
                layout_type=pr.get("layout_type", s.layout_type),
                title=pr.get("title", s.title),
                subtitle=pr.get("subtitle", s.subtitle),
                body_items=pr.get("body_items", s.body_items),
                images=s.images,
                tables=self._normalize_tables(pr.get("tables", s.tables)),
                code_block=pr.get("code_block"),
                notes=pr.get("notes", s.notes),
                page_number=s.page_number,
            ))
        logger.info(f"Polish: enhanced {len(polished)} slides")
        return polished

    def _detect_transcript(self, input_text: str) -> bool:
        if not input_text or len(input_text.strip()) < 50:
            return False
        strong_keywords = ["meeting", "minutes", "transcript", "attendees", "agenda"]
        dialogue_pattern = r'[\u4e00-\u9fa5]{2,5}[：:]\s'
        dialogues = re.findall(dialogue_pattern, input_text)
        has_keyword = any(kw in input_text.lower() for kw in strong_keywords)
        has_many_dialogues = len(dialogues) >= 5
        return has_keyword and has_many_dialogues

    async def _transcript_execute(self, input_text: str) -> GenerationResult:
        from transcript.processor import TranscriptProcessor
        result = GenerationResult(scene=self.scene, template_id=self.template_id,
                                  mode="transcript", message="Meeting transcript processing")
        self._notify_progress("转写解析", "正在分析会议转写文本...", 10)
        processor = TranscriptProcessor()
        processed = processor.process(input_text)
        self._notify_progress("转写解析", "转写文本分析完成", 20)
        if not processed.chunks:
            result.qa_results.append({"severity": "error", "category": "transcript",
                                       "slide": 0, "message": "Transcript parsing failed"})
            return result

        progress = self._create_smooth_progress(20, 55, "AI解析",
            "正在提取结构化信息...", duration_estimate=12.0)
        progress.start()
        try:
            llm_output = await self._call_llm_for_transcript(processor, processed)
        finally:
            progress.complete("AI解析完成")

        self._notify_progress("交叉验证", "正在进行事实交叉验证...", 55)
        await asyncio.sleep(0.1)
        verification = processor.verify_llm_output(llm_output, processed.all_facts)
        self._notify_progress("交叉验证", "验证完成", 65)

        structured = self._parse_transcript_llm_output(llm_output)
        sections = structured.get("sections", [])
        slides_data = self._transcript_sections_to_slides(structured, sections)
        self._notify_progress("生成幻灯片", "幻灯片结构完成", 75)

        result.slides = slides_data
        result.title = structured.get("title", "Meeting Minutes")
        result.message = f"Transcript parsed | {len(sections)} topics, {len(slides_data)} slides"

        progress = self._create_smooth_progress(75, 88, "渲染",
            "正在渲染SVG预览...", duration_estimate=3.0)
        progress.start()
        try:
            svg_contents = self._fill_svg_slides(slides_data)
        finally:
            progress.complete("渲染完成")
        result.svg_contents = svg_contents

        self._notify_progress("生成", "正在组装PPTX文件...", 88)
        await asyncio.sleep(0.2)
        result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)
        self._notify_progress("生成", "PPTX组装完成", 95)

        self._append_transcript_summary_qa(result, sections, verification)
        self._notify_progress("完成", "生成完毕", 100)
        return result

    def _parse_transcript_llm_output(self, llm_output: str) -> dict:
        try:
            json_str = extract_json(llm_output)
            if not json_str:
                return {"title": "Meeting Minutes", "sections": []}
            return json.loads(json_str)
        except Exception:
            return {"title": "Meeting Minutes", "sections": []}

    async def _call_llm_for_transcript(self, processor, processed) -> str:
        try:
            from ai.provider import AIProviderFactory
            provider = AIProviderFactory.create(model_id=self.model or "gpt-4o",
                                                api_key=self.api_key, base_url=self.base_url)
            prompt = processor.build_llm_prompt(processed)
            response = await provider.generate_outline(
                scene="insurance", content=prompt, slide_count=15,
                language="zh-CN", temperature=0.4)
            return response
        except Exception as e:
            logger.error(f"LLM call failed for transcript: {e}")
            return '{"title": "Meeting Minutes", "sections": []}'

    def _transcript_sections_to_slides(self, structured: dict, sections: list) -> list[SlideData]:
        slides = []
        if structured.get("title"):
            slides.append(SlideData(layout_type="cover",
                title=structured.get("title", "Meeting Minutes"),
                subtitle=structured.get("subtitle"), page_number=1))

        for i, section in enumerate(sections):
            title = section.get("topic", f"Topic {i+1}")
            body_items = []
            for point in section.get("key_points", []):
                body_items.append({"type": "list_item", "text": point, "level": 1})
            for decision in section.get("decisions", []):
                body_items.append({"type": "list_item", "text": f"[Decision] {decision}", "level": 1})
            for action in section.get("action_items", []):
                owner = action.get("owner", "")
                task = action.get("task", "")
                deadline = action.get("deadline", "")
                text = f"[Action] {task}"
                if owner or deadline:
                    text += f" ({owner}"
                    if deadline:
                        text += f", {deadline}"
                    text += ")"
                body_items.append({"type": "list_item", "text": text, "level": 1})

            layout_type = section.get("suggested_layout", "content")
            if layout_type not in self.VALID_LAYOUT_TYPES:
                layout_type = "content"

            slides.append(SlideData(layout_type=layout_type, title=title,
                                    body_items=body_items, page_number=len(slides) + 1))
        return slides

    def _append_transcript_summary_qa(self, result: GenerationResult, sections: list,
                                      verification: dict) -> None:
        coverage = verification.get("coverage_ratio", 0)
        if coverage < 0.5:
            result.qa_results.append({"severity": "warning", "category": "transcript_qa",
                "slide": 0, "message": f"Low fact coverage ({coverage:.0%})"})
        for disc in verification.get("discrepancies", [])[:3]:
            result.qa_results.append({"severity": "info", "category": "transcript_qa",
                "slide": 0, "message": f"Fact mismatch: {disc}"})

    def _data_driven_execute(self, input_text: str) -> GenerationResult:
        from data_driven.excel_parser import parse_excel, ExcelData
        from data_driven.data_mapper import DataMapper
        from data_driven.slide_filler import SlideFiller
        from data_driven.data_validator import validate_numbers

        result = GenerationResult(scene=self.scene, template_id=self.template_id,
            mode="data_driven", message=f"Data-driven: {self.meeting_type}")
        self._notify_progress("解析Excel", "正在解析 Excel 文件...", 10)
        excel_data: ExcelData = parse_excel(self.excel_filepath)
        if not excel_data.sheets:
            result.qa_results.append({"severity": "error", "category": "parse",
                                       "slide": 0, "message": "Excel has no valid data"})
            return result
        self._notify_progress("数据映射", "正在匹配数据到模板字段...", 30)
        mapper = DataMapper()
        summary, mapped, warnings = mapper.match(excel_data, self.meeting_type)
        mapped = mapper.extract_data(excel_data, mapped, self.meeting_type)
        filler = SlideFiller()
        filled_slides, extra_ctx = filler.build_slides(self.meeting_type, mapped, excel_data, {})
        slides_data = []
        for fs in filled_slides:
            slides_data.append(SlideData(layout_type=fs.layout_type, title=fs.title,
                subtitle=fs.subtitle, body_items=fs.body_items or [],
                tables=fs.tables or [], notes=fs.notes or "", page_number=fs.page_number))

        result.slides = slides_data
        result.title = slides_data[0].title if slides_data else "Untitled"
        result.message += f" | Generated {len(slides_data)} slides"

        valid_result = validate_numbers(mapped, slides_data)
        result.qa_results = valid_result.to_qa_list()
        for w in warnings:
            result.qa_results.append({"severity": "warning", "category": "mapping",
                                       "slide": 0, "message": w})

        self._notify_progress("渲染", "正在渲染 SVG 预览...", 65)
        svg_contents = self._fill_svg_slides(slides_data)
        result.svg_contents = svg_contents
        self._notify_progress("生成", "正在组装 PPTX 文件...", 85)
        result.pptx_bytes = self._assemble_pptx(slides_data, svg_contents)
        deck_qa = self._run_qa(slides_data, svg_contents)
        result.qa_results.extend(deck_qa)
        self._notify_progress("完成", "生成完毕", 100)
        return result

    def _offline_plan_execute(self, input_text: str) -> list[SlideData]:
        try:
            from rule_engine.engine import OfflineRuleEngine
            engine = OfflineRuleEngine(self.template_id)
            result = engine.process(input_text)
            slides = []
            for r in result:
                slides.append(SlideData(layout_type=r.get("layout_type", "content"),
                    title=r.get("title", ""), subtitle=r.get("subtitle"),
                    body_items=r.get("body_items", []), images=r.get("images", []),
                    tables=r.get("tables", []), code_block=r.get("code_block"),
                    notes="", page_number=r.get("page_number", 1)))
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
            slides.append(SlideData(layout_type=lt, title=line, body_items=[], page_number=i + 1))
        return slides

    def _fill_svg_slides(self, slides: list[SlideData]) -> list[str]:
        from slide_builder.svg_filler import SVGFiller
        filler = SVGFiller(self.template_dir, self.theme)
        svg_list = []
        VB = {"16:9": (1280, 720), "4:3": (960, 720), "3:4": (720, 960), "1:1": (720, 720)}
        vw, vh = VB.get(self.canvas_format, (1280, 720))
        for slide in slides:
            slide_dict = asdict(slide)
            filled = filler.fill("", slide_dict, slide.page_number)
            svg_list.append(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}">\n{filled}\n</svg>')
        return svg_list

    def _assemble_pptx(self, slides: list[SlideData], svg_contents: list[str]) -> Optional[bytes]:
        try:
            from slide_builder.generator import PPTXGenerator
            generator = PPTXGenerator(self.template_id, self.theme, self.canvas_format)
            slide_dicts = [asdict(s) for s in slides]
            return generator.generate_from_slide_data(slide_dicts)
        except Exception as e:
            logger.error(f"PPTX assembly failed: {e}")
            return None

    def _run_qa(self, slides: list[SlideData], svg_contents: list[str]) -> list[dict]:
        from slide_builder.deck_qa import DeckQA
        qa = DeckQA()
        return qa.check_all(slides)


async def run_pipeline(input_text: str, scene: str = "report",
                       template_id: str = "professional-blue",
                       ai_mode: str = "auto", auto_mode: bool = False,
                       model: Optional[str] = None,
                       api_key: Optional[str] = None, base_url: Optional[str] = None,
                       canvas_format: str = "16:9", meeting_type: Optional[str] = None,
                       excel_filepath: Optional[str] = None,
                       custom_style: Optional[str] = None,
                       include_images: bool = True,
                       progress_callback=None) -> GenerationResult:
    pipeline = GenerationPipeline(scene, template_id, ai_mode, auto_mode,
                                   model, api_key, base_url, canvas_format,
                                   meeting_type, excel_filepath, custom_style,
                                   include_images, progress_callback)
    return await pipeline.run(input_text)
