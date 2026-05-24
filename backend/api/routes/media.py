"""Media routes - TTS narration and video export."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import base64
import os
import json
import uuid
import asyncio
import tempfile
from utils.compat import to_thread

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = ""
    slides: Optional[list[dict]] = None
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    volume: str = "+0%"


class TTSResponse(BaseModel):
    files: list[dict]
    output_dir: str


@router.post("/tts", response_model=TTSResponse)
async def generate_tts(req: TTSRequest):
    try:
        from slide_builder.tts_engine import TTSEngine
        engine = TTSEngine(voice=req.voice, rate=req.rate, volume=req.volume)

        if req.slides:
            slide_notes = []
            for s in req.slides:
                page = s.get("page_number", 0)
                notes = s.get("notes", "")
                if notes:
                    slide_notes.append((page, notes))
        else:
            slide_notes = [(1, req.text)]

        output_dir = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex[:8]}")
        results = await engine.generate_slide_audio_async(slide_notes, output_dir)

        return TTSResponse(files=results, output_dir=output_dir)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"TTS failed: {str(e)}")


class VideoExportRequest(BaseModel):
    slides: list[dict] = Field(..., description="Slide data with svg_preview")
    audio_files: Optional[list[dict]] = None
    seconds_per_slide: int = 5
    fps: int = 30
    width: int = 1920
    height: int = 1080
    format: str = "mp4"


class VideoExportResponse(BaseModel):
    output_path: str
    duration_s: float


@router.post("/export/video", response_model=VideoExportResponse)
async def export_video(req: VideoExportRequest):
    try:
        from slide_builder.video_exporter import VideoExporter

        svg_contents = [s.get("svg_preview", "") for s in req.slides]
        if not svg_contents or all(not s for s in svg_contents):
            raise HTTPException(400, "No SVG content in slides")

        output_path = os.path.join(tempfile.gettempdir(),
                                   f"video_{uuid.uuid4().hex[:8]}.{req.format}")

        exporter = VideoExporter(
            fps=req.fps,
            seconds_per_slide=req.seconds_per_slide,
            width=req.width,
            height=req.height,
        )

        result = await asyncio.to_thread(
            lambda: exporter.export(
                svg_contents=svg_contents,
                output_path=output_path,
                audio_files=req.audio_files,
                format=req.format,
            )
        )

        duration = len(svg_contents) * req.seconds_per_slide
        return VideoExportResponse(output_path=result, duration_s=duration)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Video export failed: {str(e)}")


class VoiceListResponse(BaseModel):
    voices: list[dict]




class ImageSearchRequest(BaseModel):
    query: str
    count: int = Field(5, ge=1, le=20)
    orientation: str = "landscape"

class ImageResult(BaseModel):
    id: str; url: str; thumbnail: str; photographer: str; width: int; height: int

class ImageSearchResponse(BaseModel):
    results: list[ImageResult]; total: int; query: str

@router.post("/image-search", response_model=ImageSearchResponse)
async def search_images(req: ImageSearchRequest):
    try:
        import httpx
        pexels_key = os.environ.get("PEXELS_API_KEY")
        if pexels_key:
            headers = {"Authorization": pexels_key}
            params = {"query": req.query, "per_page": min(req.count, 20), "orientation": req.orientation}
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = [ImageResult(id=str(p["id"]), url=p["src"]["large"], thumbnail=p["src"]["medium"], photographer=p["photographer"], width=p["width"], height=p["height"]) for p in data.get("photos", [])[:req.count]]
                    return ImageSearchResponse(results=results, total=data.get("total_results", 0), query=req.query)
        return ImageSearchResponse(results=[], total=0, query=req.query)
    except Exception as e:
        raise HTTPException(500, f"Image search failed: {e}")

class TTSNarrateRequest(BaseModel):
    notes: list[str] = Field(default_factory=list)
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"

class TTSNarrateResponse(BaseModel):
    audio_base64: str; format: str = "mp3"; duration_seconds: float = 0

@router.post("/tts-narrate", response_model=TTSNarrateResponse)
async def tts_narrate(req: TTSNarrateRequest):
    try:
        from slide_builder.tts_engine import TTSEngine
        engine = TTSEngine(voice=req.voice, rate=req.rate)
        texts = [n for n in req.notes if n.strip()]
        if not texts:
            raise HTTPException(400, "No speaker notes available")
        full_text = "\n\n".join(f"Page {i+1}. {t}" for i, t in enumerate(texts))
        output = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex[:8]}.mp3")
        await engine.generate_async(full_text, output)
        with open(output, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        os.unlink(output)
        return TTSNarrateResponse(audio_base64=audio_b64)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {e}")

class CoverGenRequest(BaseModel):
    title: str; subtitle: str = ""; theme: str = "professional-blue"; style: str = "wechat"

class CoverGenResponse(BaseModel):
    svg: str; width: int; height: int; style: str

@router.post("/cover", response_model=CoverGenResponse)
async def generate_cover(req: CoverGenRequest):
    try:
        from slide_builder.svg_filler import SVGFiller
        from utils.theme_utils import load_theme, resolve_template_dir
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        tpl_dir = resolve_template_dir(req.theme, base_dir)
        theme = load_theme(tpl_dir)
        filler = SVGFiller(tpl_dir, theme)
        sizes = {"wechat": (900, 383), "xiaohongshu": (720, 960), "share": (720, 720)}
        w, h = sizes.get(req.style, (720, 720))
        slide_data = {"layout_type": "cover", "title": req.title, "subtitle": req.subtitle, "body_items": [], "tables": [], "code_block": "", "page_number": 1}
        filled = filler.fill("", slide_data, 1)
        svg = f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">\n{filled}\n</svg>'
        return CoverGenResponse(svg=svg, width=w, height=h, style=req.style)
    except Exception as e:
        raise HTTPException(500, f"Cover generation failed: {e}")

@router.get("/voices", response_model=VoiceListResponse)
async def list_voices():
    try:
        from slide_builder.tts_engine import TTSEngine
        voices = await TTSEngine.list_voices_async()
        return VoiceListResponse(voices=voices)
    except Exception as e:
        raise HTTPException(500, f"Failed to list voices: {str(e)}")
