"""Offline Rule Engine - replaces AI Strategist + Executor with deterministic algorithms.

Pipeline: parse → segment → match_layout → fill_svg → collect_slides
"""
from __future__ import annotations
import os
import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List

from utils.theme_utils import load_theme, resolve_template_dir, DEFAULT_THEME

logger = logging.getLogger(__name__)


@dataclass
class ContentBlock:
    type: str  # h1-h6, paragraph, list_item, ordered_item, table, code, image, quote, hr
    text: str
    level: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class SlideUnit:
    layout_type: str = "content"
    title: str = ""
    subtitle: Optional[str] = None
    body_items: list[ContentBlock] = field(default_factory=list)
    images: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    code_block: Optional[str] = None
    page_number: int = 0


class OfflineRuleEngine:
    LAYOUT_MAP = {
        "cover": "01_cover.svg",
        "toc": "02_toc.svg",
        "chapter": "02_chapter.svg",
        "content": "03_content.svg",
        "content_two_col": "03a_content_two_col.svg",
        "content_three_col": "03b_content_three_col.svg",
        "content_table": "03c_content_table.svg",
        "content_code": "03d_content_code.svg",
        "content_quote": "03f_content_quote.svg",
        "content_compare": "03g_content_compare.svg",
        "content_kpi": "03h_content_kpi.svg",
        "ending": "04_ending.svg",
    }

    def __init__(self, template_id: str = "professional-blue"):
        self.template_id = template_id
        self.template_dir = resolve_template_dir(template_id, os.path.dirname(__file__))
        self.theme = load_theme(self.template_dir)

    def process(self, markdown_text: str) -> list[dict]:
        blocks = self._parse_blocks(markdown_text)
        slides = self._segment_slides(blocks)
        slides = self._handle_plain_text_fallback(slides, blocks, markdown_text)
        slides = self._add_bookend_slides(slides)
        result = []
        for i, slide in enumerate(slides):
            slide.page_number = i + 1
            layout_svg = self._match_layout(slide)
            svg_path = os.path.join(self.template_dir, layout_svg)
            result.append({
                "page_number": slide.page_number,
                "title": slide.title,
                "layout_type": slide.layout_type,
                "layout_svg_path": svg_path if os.path.exists(svg_path) else None,
                "body_items": [{"type": b.type, "text": b.text, "level": b.level} for b in slide.body_items],
                "code_block": slide.code_block,
                "images": slide.images,
                "tables": slide.tables,
            })
        return result

    def _parse_blocks(self, md: str) -> list[ContentBlock]:
        blocks = []
        lines = md.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]

            # Heading
            h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if h_match:
                level = len(h_match.group(1))
                blocks.append(ContentBlock(type=f"h{level}", text=h_match.group(2).strip(), level=level))
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^[-*_]{3,}\s*$", line):
                blocks.append(ContentBlock(type="hr", text=""))
                i += 1
                continue

            # Code block
            if line.startswith("```"):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                i += 1
                blocks.append(ContentBlock(type="code", text="\n".join(code_lines)))
                continue

            # Image
            img_match = re.match(r"!\[(.*?)\]\((.+?)\)", line)
            if img_match:
                blocks.append(ContentBlock(type="image", text=img_match.group(2),
                                           metadata={"alt": img_match.group(1)}))
                i += 1
                continue

            # Table
            if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-:| ]+\|$", lines[i + 1]):
                table_lines = []
                while i < len(lines) and lines[i].startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                blocks.append(ContentBlock(type="table", text="\n".join(table_lines)))
                continue

            # Quote
            if line.startswith(">"):
                blocks.append(ContentBlock(type="quote", text=re.sub(r"^>\s?", "", line)))
                i += 1
                continue

            # List item
            li_match = re.match(r"^(\s*)[-*•+]\s+(.+)$", line)
            if li_match:
                indent = len(li_match.group(1))
                blocks.append(ContentBlock(type="list_item", text=li_match.group(2).strip(),
                                           level=indent // 2))
                i += 1
                continue

            # Ordered list
            oi_match = re.match(r"^\s*\d+[.、)]\s+(.+)$", line)
            if oi_match:
                blocks.append(ContentBlock(type="ordered_item", text=oi_match.group(1).strip()))
                i += 1
                continue

            # Paragraph (non-empty)
            if line.strip():
                blocks.append(ContentBlock(type="paragraph", text=line.strip()))
                i += 1
                continue

            i += 1

        return blocks

    def _segment_slides(self, blocks: list[ContentBlock]) -> list[SlideUnit]:
        slides = []
        current = SlideUnit()

        def commit():
            nonlocal current
            if current.title or current.body_items or current.tables or current.code_block or current.images:
                slides.append(current)
            current = SlideUnit()

        for block in blocks:
            if block.type == "hr":
                commit()
                continue

            if block.type == "h1":
                commit()
                current = SlideUnit(layout_type="cover" if not slides else "chapter", title=block.text)
                continue

            if block.type == "h2":
                commit()
                current = SlideUnit(layout_type="content", title=block.text)
                continue

            if block.type in ("h3", "h4", "h5", "h6"):
                if not current.subtitle:
                    current.subtitle = block.text
                else:
                    current.body_items.append(block)
                continue

            if block.type == "image":
                current.images.append({"src": block.text, "alt": block.metadata.get("alt", "")})
                continue

            if block.type == "table":
                current.tables.append({"markdown": block.text})
                current.layout_type = "content_table"
                continue

            if block.type == "code":
                current.code_block = block.text
                current.layout_type = "content_code"
                continue

            if block.type == "quote":
                current.layout_type = "content_quote"
                current.body_items.append(block)
                continue

            current.body_items.append(block)

        commit()
        return slides

    def _handle_plain_text_fallback(self, slides: list[SlideUnit],
                                     blocks: list[ContentBlock],
                                     raw_text: str) -> list[SlideUnit]:
        has_headings = any(b.type.startswith("h") for b in blocks)

        if has_headings and len(slides) > 1:
            return slides

        if has_headings and len(slides) == 1:
            slide = slides[0]
            total_items = len(slide.body_items)
            if total_items <= 5:
                return slides
            logger.info(f"Single heading slide has {total_items} items, splitting...")

        if not slides or not slides[0].body_items:
            title = self._smart_truncate_title(raw_text.strip().split("\n")[0]) if raw_text.strip() else "Untitled"
            return [SlideUnit(layout_type="cover", title=title)]

        slide = slides[0]
        paragraphs = [b.text for b in slide.body_items if b.text.strip()]

        if len(paragraphs) <= 2 and any(len(p) > 300 for p in paragraphs):
            paragraphs = self._split_long_paragraphs(paragraphs)
            logger.info(f"Long paragraph split into {len(paragraphs)} segments")

        if len(paragraphs) <= 2:
            if not slide.title:
                slide.title = self._smart_truncate_title(paragraphs[0]) if paragraphs else self._smart_truncate_title(raw_text.strip())
                if len(paragraphs) > 1:
                    slide.body_items = [ContentBlock(type="paragraph", text=paragraphs[1])]
            return [slide]

        new_slides = []
        preserved_title = slide.title if (has_headings and slide.title) else self._smart_truncate_title(paragraphs[0])
        new_slides.append(SlideUnit(
            layout_type="cover",
            title=preserved_title,
            body_items=[]
        ))

        body_count = len(paragraphs) - (0 if has_headings else 1)
        if body_count <= 2:
            items_per_slide = body_count
        elif body_count <= 6:
            items_per_slide = 3
        else:
            target_slides = max(2, body_count // 4)
            items_per_slide = max(3, body_count // target_slides + 1)
        body_start = 0 if has_headings else 1

        while body_start < len(paragraphs):
            chunk_end = min(body_start + items_per_slide, len(paragraphs))
            chunk_paragraphs = paragraphs[body_start:chunk_end]

            if not chunk_paragraphs:
                break

            new_slides.append(SlideUnit(
                layout_type="content",
                title=self._smart_truncate_title(chunk_paragraphs[0]),
                body_items=[ContentBlock(type="paragraph", text=t) for t in chunk_paragraphs[1:]] if len(chunk_paragraphs) > 1 else []
            ))

            body_start = chunk_end

        logger.info(f"Plain text split: {len(paragraphs)} paragraphs -> {len(new_slides)} slides")
        return new_slides

    def _split_long_paragraphs(self, paragraphs: list[str]) -> list[str]:
        result = []
        for para in paragraphs:
            if len(para) <= 300:
                result.append(para)
                continue
            sentences = re.split(r"(?<=[。！？；\n])\s*", para)
            sentences = [s.strip() for s in sentences if s.strip()]
            grouped = []
            for i in range(0, len(sentences), 3):
                chunk = "".join(sentences[i:i+3])
                if chunk:
                    grouped.append(chunk)
            result.extend(grouped if grouped else [para])
        return result

    def _add_bookend_slides(self, slides: list[SlideUnit]) -> list[SlideUnit]:
        if not slides:
            return slides

        if slides[0].layout_type != "cover" and slides[0].title:
            slides[0].layout_type = "cover"

        if len(slides) > 3 and slides[-1].layout_type != "ending":
            slides.append(SlideUnit(layout_type="ending", title="Thank You"))

        return slides

    def _smart_truncate_title(self, text: str, max_length: int = 30) -> str:
        text = text.strip()
        if len(text) <= max_length:
            return text

        punctuation = "。！？；，.!?;,：:—…"
        best = max_length
        for p in punctuation:
            idx = text.rfind(p, 0, max_length + 5)
            if idx >= 8:
                if idx + 1 < best:
                    best = idx + 1

        if best == max_length:
            idx = text.rfind(" ", 0, max_length)
            if idx >= 8:
                best = idx

        if best < 8:
            return text[:max_length].rstrip() + "…"

        return text[:best].strip()

    def _match_layout(self, slide: SlideUnit) -> str:
        if slide.layout_type in self.LAYOUT_MAP:
            return self.LAYOUT_MAP[slide.layout_type]

        if slide.code_block:
            return self.LAYOUT_MAP["content_code"]
        if slide.tables:
            return self.LAYOUT_MAP["content_table"]
        if slide.images:
            n = len(slide.body_items)
            return self.LAYOUT_MAP["content_two_col"] if n <= 3 else self.LAYOUT_MAP["content_three_col"]

        n = len(slide.body_items)
        total_chars = sum(len(b.text) for b in slide.body_items)

        if n <= 4 and total_chars <= 200:
            return self.LAYOUT_MAP["content"]
        if n <= 7 and total_chars <= 400:
            return self.LAYOUT_MAP["content_two_col"]
        if n > 7 or total_chars > 400:
            return self.LAYOUT_MAP["content"]

        return self.LAYOUT_MAP["content"]
