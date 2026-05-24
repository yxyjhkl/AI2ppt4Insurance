"""Export routes - PDF, PNG, HTML, PPTX export."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os
import json
import asyncio
import tempfile
import shutil
import base64
import io
from utils.compat import to_thread

router = APIRouter()


class ExportRequest(BaseModel):
    format: str = "pdf"  # "pdf", "png", "html"
    slides: list[dict] = Field(..., description="Slide data with svg_preview")
    titles: Optional[list[str]] = None
    notes: Optional[list[str]] = None
    width: int = 1280
    height: int = 720


class ExportResponse(BaseModel):
    output_path: str
    data_base64: Optional[str] = None


class PptxExportRequest(BaseModel):
    slides: list[dict] = Field(..., description="Full slide data (title, body_items, tables, notes, etc.)")
    template: str = "professional-blue"
    canvas_format: str = Field("16:9", pattern=r"^(16:9|4:3|3:4|1:1)$")
    project_title: str = "演示文稿"


@router.post("/export", response_model=ExportResponse)
async def export_deck(req: ExportRequest):
    try:
        from slide_builder.export_engine import ExportEngine

        svg_contents = [s.get("svg_preview", "") for s in req.slides]
        if not svg_contents or all(not s for s in svg_contents):
            raise HTTPException(400, "幻灯片中没有 SVG 内容")

        engine = ExportEngine(width=req.width, height=req.height)
        output = os.path.join(tempfile.gettempdir(), f"export_{os.urandom(4).hex()}.{req.format}")

        if req.format == "pdf":
            await to_thread(engine.export_pdf, svg_contents, output, req.titles)
        elif req.format == "html":
            await to_thread(engine.export_html, svg_contents, output, req.titles, req.notes)
        elif req.format == "png":
            if len(svg_contents) == 0:
                raise HTTPException(400, "生成 PNG 需要至少一张幻灯片")
            await to_thread(engine.export_png, svg_contents[0], output, 0)
        elif req.format == "pngs":
            if len(svg_contents) == 0:
                raise HTTPException(400, "生成 PNG 需要至少一张幻灯片")
            import zipfile
            png_dir = tempfile.mkdtemp(prefix="pngs_export_")
            try:
                for i, svg in enumerate(svg_contents):
                    png_out = os.path.join(png_dir, f"slide_{i+1:02d}.png")
                    await to_thread(engine.export_png, svg, png_out, i)
                with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fname in sorted(os.listdir(png_dir)):
                        zf.write(os.path.join(png_dir, fname), fname)
            finally:
                shutil.rmtree(png_dir, ignore_errors=True)
        else:
            raise HTTPException(400, f"不支持的格式: {req.format}")

        with open(output, "rb") as f:
            data_b64 = base64.b64encode(f.read()).decode("utf-8")

        return ExportResponse(output_path=output, data_base64=data_b64)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"导出失败: {str(e)}")


@router.post("/export/pptx")
async def export_pptx(req: PptxExportRequest):
    try:
        from slide_builder.generator import PPTXGenerator
        from utils.theme_utils import load_theme, resolve_template_dir

        api_dir = os.path.dirname(__file__)
        base_dir = os.path.join(api_dir, "..", "..")
        template_dir = resolve_template_dir(req.template, base_dir)
        theme = load_theme(template_dir)
        generator = PPTXGenerator(req.template, theme, req.canvas_format)

        slide_dicts = []
        for s in req.slides:
            slide_dicts.append({
                "layout_type": s.get("layout_type", "content"),
                "title": s.get("title", ""),
                "subtitle": s.get("subtitle"),
                "body_items": s.get("body_items", []),
                "tables": s.get("tables", []),
                "images": s.get("images", []),
                "code_block": s.get("code_block"),
                "notes": s.get("notes", ""),
                "canvas_elements": s.get("canvas_elements", []),
            })

        pptx_bytes = generator.generate_from_slide_data(slide_dicts)
        pptx_b64 = base64.b64encode(pptx_bytes).decode("utf-8")

        return {"pptx_base64": pptx_b64, "title": req.project_title}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"PPTX 导出失败: {str(e)}")


class ChartRequest(BaseModel):
    chart_type: str = "bar"  # "bar", "line", "pie", "area"
    data: list[dict] = Field(default_factory=list)
    title: str = ""
    width: int = 600
    height: int = 400


class ChartResponse(BaseModel):
    svg: str
    chart_type: str


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(req: ChartRequest):
    try:
        from slide_builder.chart_engine import ChartEngine
        engine = ChartEngine()
        svg = engine.generate(req.chart_type, req.data, req.title, req.width, req.height)
        return ChartResponse(svg=svg, chart_type=req.chart_type)
    except Exception as e:
        raise HTTPException(500, f"图表生成失败: {str(e)}")
