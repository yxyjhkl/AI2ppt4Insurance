from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile
import asyncio
import uuid
from utils.compat import to_thread

router = APIRouter()


class URLConvertRequest(BaseModel):
    url: str
    output_format: str = "md"


class ExcelUploadResponse(BaseModel):
    file_id: str
    filename: str
    filepath: str
    sheet_names: list[str] = []
    preview: str = ""
    row_count: int = 0


@router.post("/file")
async def convert_file(file: UploadFile = File(...), output_format: str = "md"):
    suffix = os.path.splitext(file.filename or "")[1].lower()
    supported = {".pdf", ".docx", ".doc", ".md", ".txt", ".pptx", ".html", ".htm", ".epub"}

    if suffix not in supported:
        raise HTTPException(400, f"Unsupported format: {suffix}")

    content = await file.read()
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(413, f"File too large. Maximum size is {max_size // (1024*1024)}MB")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        md_content = await to_thread(convert_to_markdown, tmp_path, suffix)
        return {"filename": file.filename, "markdown": md_content, "format": suffix}
    except Exception as e:
        raise HTTPException(500, f"Conversion failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/url")
async def convert_url(req: URLConvertRequest):
    try:
        from converters.url_converter import url_to_markdown
        md_content = await to_thread(url_to_markdown, req.url)
        return {"url": req.url, "markdown": md_content}
    except Exception as e:
        raise HTTPException(500, f"URL conversion failed: {str(e)}")


@router.post("/excel", response_model=ExcelUploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in (".xlsx", ".xls"):
        raise HTTPException(400, f"Unsupported Excel format: {suffix}. Please upload .xlsx or .xls files.")

    content = await file.read()
    max_size = 50 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(413, f"File too large. Maximum size is 50MB")

    upload_dir = os.path.join(tempfile.gettempdir(), "aippt_excel_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_id = uuid.uuid4().hex[:12]
    safe_filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(upload_dir, safe_filename)

    with open(filepath, "wb") as f:
        f.write(content)

    try:
        from data_driven.excel_parser import parse_excel
        excel_data = parse_excel(filepath)

        preview_lines = []
        for sheet in excel_data.sheets:
            preview_lines.append(f"Sheet: {sheet.name} ({sheet.row_count}行 × {sheet.col_count}列)")
            preview_lines.append(" | ".join(sheet.headers[:8]))
            for row in sheet.rows[:5]:
                preview_lines.append(" | ".join(str(v)[:20] if v is not None else "" for v in row[:8]))

        return ExcelUploadResponse(
            file_id=file_id,
            filename=file.filename or "unknown.xlsx",
            filepath=filepath,
            sheet_names=[s.name for s in excel_data.sheets],
            preview="\n".join(preview_lines),
            row_count=excel_data.total_rows,
        )
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(500, f"Excel parsing failed: {str(e)}")


@router.get("/excel/{file_id}/preview")
async def excel_preview(file_id: str):
    upload_dir = os.path.join(tempfile.gettempdir(), "aippt_excel_uploads")
    for fname in os.listdir(upload_dir):
        if fname.startswith(file_id):
            filepath = os.path.join(upload_dir, fname)
            from data_driven.excel_parser import parse_excel, to_prompt_summary
            excel_data = parse_excel(filepath)
            return {
                "file_id": file_id,
                "filename": fname.split("_", 1)[1] if "_" in fname else fname,
                "summary": to_prompt_summary(excel_data),
                "headers": {s.name: s.headers for s in excel_data.sheets},
                "row_count": excel_data.total_rows,
            }
    raise HTTPException(404, f"Excel file not found: {file_id}")


def convert_to_markdown(filepath: str, suffix: str) -> str:
    if suffix == ".pdf":
        from converters.pdf_converter import pdf_to_markdown
        return pdf_to_markdown(filepath)
    elif suffix == ".docx":
        from converters.docx_converter import docx_to_markdown
        return docx_to_markdown(filepath)
    elif suffix in (".md", ".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    elif suffix == ".html":
        from converters.url_converter import html_to_markdown
        with open(filepath, "r", encoding="utf-8") as f:
            return html_to_markdown(f.read())
    else:
        raise ValueError(f"No converter for {suffix}")
