from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import os
import re
import json
import asyncio
import shutil
from utils.compat import to_thread

router = APIRouter()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates")

_VALID_ID_RE = re.compile(r'^[\w\-\.]+$')

def _validate_template_id(template_id: str) -> None:
    if not _VALID_ID_RE.match(template_id) or '..' in template_id:
        raise HTTPException(400, f"无效的模板 ID: {template_id}")


@router.get("/")
async def list_templates():
    return await to_thread(_list_templates_sync)

CATEGORY_MAP = {
    "Report": "报告",
    "Education": "教育",
    "Proposal": "提案",
    "Creative": "创意",
    "Tech": "科技",
    "Business": "商务",
    "Insurance": "保险",
}

def _translate_category(cat: str) -> str:
    return CATEGORY_MAP.get(cat, "其他")

def _list_templates_sync():
    templates = []
    
    built_in_dir = os.path.join(TEMPLATES_DIR, "built-in")
    if os.path.exists(built_in_dir):
        for name in os.listdir(built_in_dir):
            theme_path = os.path.join(built_in_dir, name, "theme.json")
            if os.path.exists(theme_path):
                with open(theme_path, "r", encoding="utf-8") as f:
                    theme = json.load(f)
                theme["category"] = _translate_category(theme.get("category", ""))
                entry = {"id": name, "source": "built-in", **theme}
                entry["preview_svg"] = f"/api/v1/templates/{name}/preview"
                templates.append(entry)
    
    custom_dir = os.path.join(TEMPLATES_DIR, "custom")
    if os.path.exists(custom_dir):
        for name in os.listdir(custom_dir):
            theme_path = os.path.join(custom_dir, name, "theme.json")
            if os.path.exists(theme_path):
                with open(theme_path, "r", encoding="utf-8") as f:
                    theme = json.load(f)
                theme["category"] = _translate_category(theme.get("category", ""))
                entry = {"id": name, "source": "custom", **theme}
                entry["preview_svg"] = f"/api/v1/templates/{name}/preview"
                templates.append(entry)
    
    return templates


@router.get("/{template_id}/preview")
async def get_template_preview(template_id: str):
    _validate_template_id(template_id)
    from slide_builder.template_preview_svg import get_cached_preview
    paths = [
        os.path.join(TEMPLATES_DIR, "built-in", template_id),
        os.path.join(TEMPLATES_DIR, "custom", template_id),
    ]
    for base in paths:
        theme_path = os.path.join(base, "theme.json")
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                theme = json.load(f)
            svg = await to_thread(get_cached_preview, template_id, theme)
            return Response(content=svg, media_type="image/svg+xml")
    raise HTTPException(404, f"模板 {template_id} 不存在")

@router.get("/{template_id}")
async def get_template(template_id: str):
    _validate_template_id(template_id)
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
    raise HTTPException(404, f"模板 {template_id} 不存在")


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    _validate_template_id(template_id)
    custom_path = os.path.join(TEMPLATES_DIR, "custom", template_id)
    if not os.path.exists(custom_path):
        raise HTTPException(404, f"模板 {template_id} 不存在或不是自定义模板")
    
    try:
        shutil.rmtree(custom_path)
        return {"success": True, "message": f"模板 {template_id} 删除成功"}
    except Exception as e:
        raise HTTPException(500, f"删除模板失败: {str(e)}")


@router.post("/import")
async def import_template(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".pptx"):
        raise HTTPException(400, "仅支持 .pptx 文件格式")

    template_name = os.path.splitext(file.filename)[0]
    _validate_template_id(template_name)

    try:
        content = await file.read()
        template_name = os.path.splitext(file.filename)[0]
        target_dir = os.path.join(TEMPLATES_DIR, "custom", template_name)
        
        os.makedirs(target_dir, exist_ok=True)
        if not os.path.exists(target_dir):
            raise Exception(f"无法创建目录: {target_dir}")

        pptx_path = os.path.join(target_dir, "source.pptx")
        with open(pptx_path, "wb") as f:
            f.write(content)

        if not os.path.exists(pptx_path):
            raise Exception(f"无法写入文件: {pptx_path}")

        from slide_builder.template_importer import import_template_from_pptx
        result = await to_thread(import_template_from_pptx, pptx_path, target_dir)
        return {"id": template_name, "message": "模板导入成功", **result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"导入失败: {type(e).__name__}: {str(e)}")
