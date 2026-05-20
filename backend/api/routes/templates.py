from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
import asyncio
import shutil
from utils.compat import to_thread

router = APIRouter()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates")


@router.get("/")
async def list_templates():
    return await to_thread(_list_templates_sync)

def _list_templates_sync():
    built_in_dir = os.path.join(TEMPLATES_DIR, "built-in")
    templates = []
    if os.path.exists(built_in_dir):
        for name in os.listdir(built_in_dir):
            theme_path = os.path.join(built_in_dir, name, "theme.json")
            if os.path.exists(theme_path):
                with open(theme_path, "r", encoding="utf-8") as f:
                    theme = json.load(f)
                templates.append({"id": name, **theme})
    return templates


@router.get("/{template_id}")
async def get_template(template_id: str):
    return await to_thread(_get_template_sync, template_id)

def _get_template_sync(template_id: str):
    paths = [
        os.path.join(TEMPLATES_DIR, "built-in", template_id),
        os.path.join(TEMPLATES_DIR, "custom", template_id),
    ]
    for base in paths:
        if os.path.exists(base):
            theme_path = os.path.join(base, "theme.json")
            theme = {}
            if os.path.exists(theme_path):
                with open(theme_path, "r", encoding="utf-8") as f:
                    theme = json.load(f)
            svgs = [f for f in os.listdir(base) if f.endswith(".svg")]
            return {"id": template_id, "path": base, "theme": theme, "layouts": svgs}
    raise HTTPException(404, f"Template {template_id} not found")


@router.post("/import")
async def import_template(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".pptx"):
        raise HTTPException(400, "Only .pptx files supported for template import")

    content = await file.read()
    template_name = os.path.splitext(file.filename)[0]
    target_dir = os.path.join(TEMPLATES_DIR, "custom", template_name)
    os.makedirs(target_dir, exist_ok=True)

    pptx_path = os.path.join(target_dir, "source.pptx")
    with open(pptx_path, "wb") as f:
        f.write(content)

    try:
        from slide_builder.template_importer import import_template_from_pptx
        result = await to_thread(import_template_from_pptx, pptx_path, target_dir)
        return {"id": template_name, "message": "Template imported", **result}
    except Exception as e:
        raise HTTPException(500, f"Import failed: {str(e)}")
