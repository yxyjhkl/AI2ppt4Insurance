from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Any
import os
from utils.json_utils import extract_json, estimate_slide_count
import json
import uuid
import base64
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    scene: str = "report"
    meeting_type: Optional[str] = None
    content: str = Field("", max_length=200000)
    template: str = "professional-blue"
    model: Optional[str] = None
    slide_count: int = Field(10, ge=1, le=50)
    language: str = "zh-CN"
    include_notes: bool = True
    include_images: bool = True
    temperature: float = 0.7
    ai_mode: str = "auto"
    auto_mode: bool = False
    canvas_format: str = Field("16:9", pattern=r"^(16:9|4:3|3:4|1:1)$")
    animation_effect: Optional[str] = None
    transition_effect: Optional[str] = None
    animation_duration: int = 500
    stagger_ms: int = 200
    include_animation: bool = False
    excel_filepath: Optional[str] = None
    custom_style: Optional[str] = None
    task_id: Optional[str] = None

class SlideResponse(BaseModel):
    page_number: int
    layout_type: str
    title: str
    subtitle: Optional[str] = None
    body_items: list[dict] = Field(default_factory=list)
    images: list[dict] = Field(default_factory=list)
    tables: list[dict] = Field(default_factory=list)
    code_block: Optional[str] = None
    notes: str = ""
    svg_preview: str = ""


class QAItem(BaseModel):
    severity: str
    category: str
    slide: int
    message: str
    detail: Optional[str] = None


class GenerateResponse(BaseModel):
    project_id: str
    title: str
    scene: str
    template_id: str
    mode: str
    message: str = ""
    slide_count: int
    slides: list[SlideResponse]
    qa_results: list[QAItem]
    preview_slides: list[str]
    pptx_base64: Optional[str] = None


@router.post("/pptx", response_model=GenerateResponse)
async def generate_pptx(req: GenerateRequest):
    try:
        from slide_builder.pipeline import run_pipeline
        from api.key_store import get_api_key
        from api.routes.progress import send_progress

        model_id = req.model or "gpt-4o"
        stored = get_api_key(model_id)

        progress_callback = None
        if req.task_id:
            async def on_progress(data: dict):
                try:
                    await send_progress(req.task_id, data)
                except Exception:
                    pass
            progress_callback = on_progress

        result = await run_pipeline(
            input_text=req.content,
            scene=req.scene,
            template_id=req.template,
            ai_mode=req.ai_mode,
            auto_mode=req.auto_mode,
            model=model_id,
            api_key=stored.get("api_key"),
            base_url=stored.get("base_url"),
            canvas_format=req.canvas_format,
            meeting_type=req.meeting_type,
            excel_filepath=req.excel_filepath,
            custom_style=req.custom_style,
            progress_callback=progress_callback,
        )

        if req.include_animation and result.pptx_bytes:
            try:
                from slide_builder.animation_engine import AnimationEngine
                import io
                from pptx import Presentation

                prs = Presentation(io.BytesIO(result.pptx_bytes))

                engine = AnimationEngine(prs)

                if req.transition_effect:
                    for i in range(len(prs.slides)):
                        engine.apply_slide_transition(i, req.transition_effect)

                if req.animation_effect:
                    for i in range(len(prs.slides)):
                        engine.apply_entrance_to_all_shapes(
                            i, req.animation_effect,
                            duration_ms=req.animation_duration,
                            stagger_ms=req.stagger_ms,
                        )

                buf = io.BytesIO()
                prs.save(buf)
                buf.seek(0)
                result.pptx_bytes = buf.read()
            except Exception as anim_err:
                import logging
                logging.getLogger(__name__).warning(f"Animation apply failed: {anim_err}, using original PPTX")

        slides_response = []
        for s, svg in zip(result.slides, result.svg_contents):
            clean_tables = []
            for t in (s.tables or []):
                if isinstance(t, dict):
                    clean_tables.append(t)
                elif isinstance(t, list):
                    if t and all(isinstance(r, list) for r in t):
                        header = t[0]
                        rows = ["| " + " | ".join(str(c) for c in header) + " |"]
                        rows.append("|" + "|".join(["---"] * len(header)) + "|")
                        for row in t[1:]:
                            cols = [str(c) for c in row]
                            while len(cols) < len(header):
                                cols.append("")
                            rows.append("| " + " | ".join(cols[:len(header)]) + " |")
                        clean_tables.append({"markdown": "\n".join(rows)})
                    else:
                        rows = ["| " + " | ".join(str(c) for c in t) + " |"]
                        clean_tables.append({"markdown": "\n".join(rows)})
                elif isinstance(t, str) and t.strip():
                    clean_tables.append({"markdown": t})
            slides_response.append(SlideResponse(
                page_number=s.page_number,
                layout_type=s.layout_type,
                title=s.title,
                subtitle=s.subtitle if s.subtitle else None,
                body_items=s.body_items if s.body_items else [],
                images=s.images if s.images else [],
                tables=clean_tables,
                code_block=s.code_block,
                notes=s.notes,
                svg_preview=svg or "",
            ))

        qa_items = [QAItem(**q) for q in result.qa_results]

        project_id = f"proj_{uuid.uuid4().hex[:12]}"

        # Save PPTX to temp if generated
        pptx_b64 = None
        if result.pptx_bytes:
            pptx_b64 = base64.b64encode(result.pptx_bytes).decode("utf-8")

        return GenerateResponse(
            project_id=project_id,
            title=result.title,
            scene=req.scene,
            template_id=req.template,
            mode=result.mode,
            message=result.message,
            slide_count=len(result.slides),
            slides=slides_response,
            qa_results=qa_items,
            preview_slides=result.svg_contents,
            pptx_base64=pptx_b64,
        )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Generation error:\n{tb}")
        raise HTTPException(500, f"Generation failed: {type(e).__name__}: {str(e)}")




class OutlineItem(BaseModel):
    index: int
    layout_type: str = "content"
    title: str = ""
    description: str = ""
    key_points: list[str] = Field(default_factory=list)

class OutlineResponse(BaseModel):
    title: str
    slides: list[OutlineItem]
    estimated_count: int
    message: str = ""

@router.post("/outline", response_model=OutlineResponse)
async def generate_outline(req: GenerateRequest):
    try:
        from ai.provider import AIProviderFactory
        from api.key_store import get_api_key
        import yaml
        model_id = req.model or "gpt-4o"
        stored = get_api_key(model_id) if not model_id.startswith("ollama/") else {}
        provider = AIProviderFactory.create(model_id=model_id, api_key=stored.get("api_key"), base_url=stored.get("base_url"))
        scene = f"insurance_{req.meeting_type}" if req.scene == "insurance" and req.meeting_type else req.scene
        scene_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "scenes")
        scene_info = {}
        def ld(d):
            nonlocal scene_info
            for fn in os.listdir(d):
                fp = os.path.join(d, fn)
                if fn.endswith((".yaml", ".yml")):
                    with open(fp, "r", encoding="utf-8") as f2:
                        dd = yaml.safe_load(f2)
                    if dd and dd.get("scene_id") == scene:
                        scene_info = dd
                elif os.path.isdir(fp):
                    ld(fp)
        ld(scene_dir)
        if not req.content or len(req.content) < 20:
            return OutlineResponse(title="未命名", slides=[], estimated_count=0, message="内容过短")
        est = estimate_slide_count(req.content)
        prompt = f"""Generate presentation outline in JSON with ~{est} slides. First=cover, last=ending.
Use layouts: cover, chapter, content, content_table, content_two_col, content_compare, content_kpi.
Each slide needs layout_type, title, description, key_points. Return ONLY valid JSON.
SCENE: {scene_info.get("name", req.scene)}. CONTENT: {req.content[:8000]}"""
        response = await provider.generate_outline(scene=req.scene, content=prompt, slide_count=est, language=req.language or "zh-CN", temperature=0.5)
        
        # 安全地解析 JSON
        json_str = extract_json(response)
        if not json_str:
            logger.warning(f"Failed to extract JSON from response: {response[:200]}")
            # 尝试返回一个基本的响应
            return OutlineResponse(title="未命名", slides=[], estimated_count=est, message="AI 返回格式无效")
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return OutlineResponse(title="未命名", slides=[], estimated_count=est, message="AI 返回格式错误")
        
        items = [OutlineItem(index=s.get("index", i + 1), layout_type=s.get("layout_type", "content"),
            title=s.get("title", f"Page {i+1}"), description=s.get("description", ""),
            key_points=s.get("key_points", []))
            for i, s in enumerate(data.get("slides", []))]
        return OutlineResponse(title=data.get("title", "未命名"), slides=items, estimated_count=est, message="成功")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Outline failed: {e}")

class SupplementRequest(BaseModel):
    slides: list[dict] = Field(..., description="Current slide data")
    instruction: str = ""
    supplement_type: str = "auto"
    model: Optional[str] = None
    language: str = "zh-CN"

class SupplementResponse(BaseModel):
    enhanced_slides: list[dict]
    message: str = ""

@router.post("/supplement", response_model=SupplementResponse)
async def supplement_slides(req: SupplementRequest):
    try:
        from ai.provider import AIProviderFactory
        from api.key_store import get_api_key, list_model_ids
        model_id = req.model or "gpt-4o"
        stored = get_api_key(model_id) if not model_id.startswith("ollama/") else {}
        if not stored.get("api_key") and not model_id.startswith("ollama/"):
            all_ids = list_model_ids()
            if all_ids:
                model_id = all_ids[0]
                stored = get_api_key(model_id)
        if not stored.get("api_key") and not model_id.startswith("ollama/"):
            raise HTTPException(400, "未配置 AI API Key，请先在设置中配置模型密钥")
        provider = AIProviderFactory.create(model_id=model_id, api_key=stored.get("api_key"), base_url=stored.get("base_url"))
        slide_texts = []
        for s in req.slides:
            lt, title = s.get("layout_type", "content"), s.get("title", "")
            body = "\n".join(b.get("text", "") for b in s.get("body_items", []) if isinstance(b, dict))
            slide_texts.append(f"[{lt}] {title}\n{body}")
        type_hints = {"data": "add data metrics", "case": "add case examples", "process": "add process steps", "compare": "add comparison", "auto": "comprehensive supplement"}
        prompt = f"Enhance slides. Type: {type_hints.get(req.supplement_type, 'comprehensive')}. Extra: {req.instruction}. Keep all existing items, add new with prefix. Return: {{\"enhanced_slides\":[...]}}. Content: {chr(10).join(slide_texts)}"
        response = await provider.generate_outline(scene="report", content=prompt, slide_count=len(req.slides), language=req.language, temperature=0.5)
        data = json.loads(extract_json(response))
        return SupplementResponse(enhanced_slides=data.get("enhanced_slides", req.slides), message=f"Supplemented {len(data.get('enhanced_slides',[]))} slides")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Supplement failed: {e}")

@router.get("/preview/{slide_index}")
async def preview_slide(slide_index: int,
                        project: str = Query(...),
                        template: str = Query("professional-blue"),
                        scene: str = Query("report")):
    return {"status": "ok", "slide_index": slide_index}


# ---- Auto Mode Prompt Management ----
import os as _os
import json as _json
_PROMPT_PATH = _os.path.join(_os.path.dirname(__file__), "..", "..", "prompts", "auto_mode_prompt.txt")
_PRESETS_DIR = _os.path.join(_os.path.dirname(__file__), "..", "..", "prompts", "auto_mode_presets")
_CONFIG_PATH = _os.path.join(_os.path.dirname(__file__), "..", "..", "prompts", "auto_mode_config.json")

import re as _re
_VALID_PRESET_RE = _re.compile(r'^[\w\-\.]+$')

def _validate_preset_id(preset_id: str) -> None:
    if not _VALID_PRESET_RE.match(preset_id) or '..' in preset_id:
        raise HTTPException(400, f"无效的预设 ID: {preset_id}")


def _load_config() -> dict:
    if _os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            pass
    return {"active_preset": "business_report", "custom_override": False}


def _save_config(config: dict):
    prompt_dir = _os.path.dirname(_CONFIG_PATH)
    _os.makedirs(prompt_dir, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        _json.dump(config, f, indent=2, ensure_ascii=False)


def _list_presets() -> list[dict]:
    presets = []
    if not _os.path.isdir(_PRESETS_DIR):
        return presets
    for name in sorted(_os.listdir(_PRESETS_DIR)):
        preset_dir = _os.path.join(_PRESETS_DIR, name)
        if not _os.path.isdir(preset_dir):
            continue
        meta_path = _os.path.join(preset_dir, "meta.json")
        prompt_path = _os.path.join(preset_dir, "prompt.txt")
        if not _os.path.exists(meta_path) or not _os.path.exists(prompt_path):
            continue
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = _json.load(f)
            meta["has_prompt"] = True
            presets.append(meta)
        except Exception:
            pass
    presets.sort(key=lambda p: p.get("order", 99))
    return presets


class PromptUpdateRequest(BaseModel):
    content: str


class PresetActivateRequest(BaseModel):
    preset_id: str


@router.get("/prompt/auto-mode")
async def get_auto_mode_prompt():
    config = _load_config()
    content = ""
    if _os.path.exists(_PROMPT_PATH):
        with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    return {
        "content": content,
        "active_preset": config.get("active_preset", ""),
        "custom_override": config.get("custom_override", False),
    }


@router.get("/prompt/presets")
async def list_presets():
    config = _load_config()
    return {
        "presets": _list_presets(),
        "active_preset": config.get("active_preset", ""),
        "custom_override": config.get("custom_override", False),
    }


@router.post("/prompt/presets/activate")
async def activate_preset(req: PresetActivateRequest):
    _validate_preset_id(req.preset_id)
    preset_prompt = _os.path.join(_PRESETS_DIR, req.preset_id, "prompt.txt")
    if not _os.path.exists(preset_prompt):
        raise HTTPException(404, f"Preset not found: {req.preset_id}")

    with open(preset_prompt, "r", encoding="utf-8") as f:
        content = f.read()

    prompt_dir = _os.path.dirname(_PROMPT_PATH)
    _os.makedirs(prompt_dir, exist_ok=True)
    with open(_PROMPT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    _save_config({"active_preset": req.preset_id, "custom_override": False})
    return {"status": "ok", "message": f"已激活预设: {req.preset_id}", "active_preset": req.preset_id}


@router.post("/prompt/auto-mode")
async def update_auto_mode_prompt(req: PromptUpdateRequest):
    prompt_dir = _os.path.dirname(_PROMPT_PATH)
    _os.makedirs(prompt_dir, exist_ok=True)
    with open(_PROMPT_PATH, "w", encoding="utf-8") as f:
        f.write(req.content)
    config = _load_config()
    config["custom_override"] = True
    _save_config(config)
    return {"status": "ok", "message": "Custom prompt saved"}


@router.post("/prompt/auto-mode/reset")
async def reset_auto_mode_prompt():
    config = _load_config()
    active = config.get("active_preset", "business_report")
    preset_prompt = _os.path.join(_PRESETS_DIR, active, "prompt.txt")
    if not _os.path.exists(preset_prompt):
        preset_prompt = _os.path.join(_PRESETS_DIR, "business_report", "prompt.txt")

    if _os.path.exists(preset_prompt):
        with open(preset_prompt, "r", encoding="utf-8") as f:
            content = f.read()
        with open(_PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        _save_config({"active_preset": active, "custom_override": False})
        return {"status": "ok", "message": f"Reset to preset: {active}", "content": content, "active_preset": active}
    return {"status": "error", "message": "Default preset not found"}
