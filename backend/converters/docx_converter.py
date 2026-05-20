"""DOCX to Markdown converter using mammoth + python-docx."""
import mammoth
import os
import json
import hashlib
from PIL import Image
from io import BytesIO


def docx_to_markdown(filepath: str) -> str:
    output_dir = os.path.join(os.path.dirname(filepath), f"{os.path.basename(filepath)}_files")
    os.makedirs(output_dir, exist_ok=True)

    image_manifest = []

    def handle_image(image):
        nonlocal image_manifest
        ext = image.content_type.split("/")[-1] if "/" in image.content_type else "png"
        img_bytes = image.read()
        sha = hashlib.sha256(img_bytes).hexdigest()[:12]
        filename = f"img_{sha}.{ext}"
        img_path = os.path.join(output_dir, filename)
        with open(img_path, "wb") as f:
            f.write(img_bytes)
        try:
            pil_img = Image.open(BytesIO(img_bytes))
            w, h = pil_img.size
        except (IOError, OSError):
            w, h = 0, 0
        image_manifest.append({
            "filename": filename,
            "width": w,
            "height": h,
        })
        return {"src": f"{os.path.basename(output_dir)}/{filename}"}

    with open(filepath, "rb") as f:
        result = mammoth.convert_to_markdown(f, convert_image=mammoth.images.img_element(handle_image))

    manifest_path = os.path.join(output_dir, "image_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(image_manifest, f, ensure_ascii=False, indent=2)

    return result.value
