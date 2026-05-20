from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Any
import json
import uuid
import base64

router = APIRouter()


class GenerateRequest(BaseModel):
    scene: str = "report"
    meeting_type: Optional[str] = None
    content: str = ""
    template: str = "professional-blue"
    model: Optional[str] = None
    slide_count: int = 10
    language: str = "zh-CN"
    include_notes: bool = True
    include_images: bool = True
    temperature: float = 0.7
    ai_mode: str = "auto"
    canvas_format: str = "16:9"
    animation_effect: Optional[str] = None
    transition_effect: Optional[str] = None
    animation_duration: int = 500
    stagger_ms: int = 200
    include_animation: bool = False
    excel_filepath: Optional[str] = None


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

        model_id = req.model or "gpt-4o"
        stored = get_api_key(model_id)

        result = await run_pipeline(
            input_text=req.content,
            scene=req.scene,
            template_id=req.template,
            ai_mode=req.ai_mode,
            model=model_id,
            api_key=stored.get("api_key"),
            base_url=stored.get("base_url"),
            canvas_format=req.canvas_format,
            meeting_type=req.meeting_type,
            excel_filepath=req.excel_filepath,
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
            slides_response.append(SlideResponse(
                page_number=s.page_number,
                layout_type=s.layout_type,
                title=s.title,
                subtitle=s.subtitle if s.subtitle else None,
                body_items=s.body_items if s.body_items else [],
                images=s.images if s.images else [],
                tables=s.tables if s.tables else [],
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
        traceback.print_exc()
        raise HTTPException(500, f"Generation failed: {str(e)}")


@router.get("/preview/{slide_index}")
async def preview_slide(slide_index: int,
                        project: str = Query(...),
                        template: str = Query("professional-blue"),
                        scene: str = Query("report")):
    return {"status": "ok", "slide_index": slide_index}
