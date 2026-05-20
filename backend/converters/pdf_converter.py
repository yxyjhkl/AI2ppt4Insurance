"""PDF to Markdown converter using PyMuPDF."""
import fitz
from typing import Optional
import re


def pdf_to_markdown(filepath: str) -> str:
    pages = []

    with fitz.open(filepath) as doc:
        font_sizes = _analyze_font_sizes(doc)
        body_size = font_sizes.get("body", 12)

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            page_text = []
            header_footer_text = _detect_headers_footers(doc, page_num)

            for block in blocks:
                if block["type"] == 0:  # text
                    for line in block["lines"]:
                        text = _extract_line_text(line)
                        if not text.strip():
                            continue
                        if text.strip() in header_footer_text:
                            continue

                        size = line["spans"][0]["size"] if line["spans"] else body_size
                        bold = any(s.get("bold", False) for s in line["spans"])

                        heading_level = _get_heading_level(text, size, font_sizes, bold)
                        if heading_level:
                            page_text.append(f"{'#' * heading_level} {text.strip()}")
                        elif _is_list_item(text):
                            page_text.append(text.strip())
                        else:
                            page_text.append(text.strip())

                elif block["type"] == 1:  # image
                    if _should_keep_image(block):
                        page_text.append(f"![image](page_{page_num + 1}_img.png)")

            pages.append("\n".join(page_text))

    return "\n\n".join(pages)


def _analyze_font_sizes(doc) -> dict:
    from collections import Counter
    sizes = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        sizes[round(span["size"])] += 1
    if not sizes:
        return {"body": 12, "h1": 24, "h2": 18, "h3": 16}

    body = sizes.most_common(1)[0][0]
    sorted_sizes = sorted([s for s in sizes if s > body], reverse=True)
    result = {"body": body}
    for i, level in enumerate(["h1", "h2", "h3"]):
        if i < len(sorted_sizes):
            result[level] = sorted_sizes[i]
    return result


def _get_heading_level(text: str, size: float, font_sizes: dict, bold: bool) -> Optional[int]:
    if size >= font_sizes.get("h1", 999):
        return 1
    if size >= font_sizes.get("h2", 999):
        return 2 if bold else None
    if size >= font_sizes.get("h3", 999):
        return 3 if bold else None
    return None


def _is_list_item(text: str) -> bool:
    return bool(re.match(r"^[•●○◦▪▸►\-\d+.)]\s", text.strip()))


def _detect_headers_footers(doc, current_page: int) -> set:
    noise = set()
    if len(doc) < 3:
        return noise
    page = doc[current_page]
    page_height = page.rect.height
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:
            for line in block["lines"]:
                y = line["bbox"][1]
                if y < page_height * 0.15 or y > page_height * 0.85:
                    text = _extract_line_text(line).strip()
                    if text:
                        noise.add(text)
    return noise


def _extract_line_text(line) -> str:
    return "".join(span["text"] for span in line["spans"])


def _should_keep_image(block: dict) -> bool:
    bbox = block["bbox"]
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    if w < 100 or h < 100:
        return False
    if w * h < 30000:
        return False
    if max(w, h) / min(w, h) > 12:
        return False
    return True
