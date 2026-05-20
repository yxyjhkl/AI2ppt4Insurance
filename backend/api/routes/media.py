"""Media routes - TTS narration and video export."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
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


@router.get("/voices", response_model=VoiceListResponse)
async def list_voices():
    try:
        from slide_builder.tts_engine import TTSEngine
        voices = await TTSEngine.list_voices_async()
        return VoiceListResponse(voices=voices)
    except Exception as e:
        raise HTTPException(500, f"Failed to list voices: {str(e)}")
