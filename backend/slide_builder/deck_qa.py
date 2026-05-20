"""Deck QA - quality checks for generated slide decks.

Detects: empty slides, duplicate titles, content overflow, missing notes,
inconsistent formatting, low text density, layout conflicts.
"""
from __future__ import annotations
import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class QAReport:
    severity: str  # error, warning, info
    category: str
    slide: int
    message: str
    detail: Optional[str] = None


class DeckQA:
    MIN_BODY_ITEMS = 1
    MAX_TITLE_LENGTH = 120
    MAX_BODY_CHARS = 2000

    def check_all(self, slides: list) -> list[dict]:
        if not slides:
            return [{"severity": "error", "category": "empty_deck",
                      "slide": 0, "message": "Deck has no slides"}]

        reports = []
        seen_titles = {}

        for i, slide in enumerate(slides):
            page = i + 1
            reports.extend(self._check_empty(slide, page))
            reports.extend(self._check_duplicate_title(slide, page, seen_titles))
            reports.extend(self._check_overflow(slide, page))
            reports.extend(self._check_title_length(slide, page))
            reports.extend(self._check_layout_conflict(slide, page))
            reports.extend(self._check_missing_notes(slide, page))
            reports.extend(self._check_low_density(slide, page))

        reports.extend(self._check_deck_structure(slides))

        return [r.__dict__ if hasattr(r, '__dict__') else r for r in reports]

    def _check_empty(self, slide, page: int) -> list[QAReport]:
        reports = []
        title = self._safe(slide, "title")
        body = self._safe(slide, "body_items", [])
        img = self._safe(slide, "images", [])
        tbl = self._safe(slide, "tables", [])
        code = self._safe(slide, "code_block")

        has_content = bool(title or body or img or tbl or code)
        if not has_content:
            reports.append(QAReport("error", "empty_slide", page,
                                    f"Slide {page} is completely empty"))
        elif not body and not img and not tbl and not code:
            reports.append(QAReport("warning", "empty_content", page,
                                    f"Slide {page} has a title but no body content"))
        return reports

    def _check_duplicate_title(self, slide, page: int, seen: dict) -> list[QAReport]:
        title = self._safe(slide, "title")
        if not title:
            return []

        title_lower = title.lower().strip()
        if title_lower in seen:
            prev = seen[title_lower]
            return [QAReport("warning", "duplicate_title", page,
                             f"Title '{title}' already used on slide {prev}")]
        seen[title_lower] = page
        return []

    def _check_title_length(self, slide, page: int) -> list[QAReport]:
        title = self._safe(slide, "title", "")
        if len(title) > self.MAX_TITLE_LENGTH:
            return [QAReport("info", "long_title", page,
                             f"Title is {len(title)} characters (max {self.MAX_TITLE_LENGTH})")]
        return []

    def _check_overflow(self, slide, page: int) -> list[QAReport]:
        body = self._safe(slide, "body_items", [])
        total_chars = sum(len(self._safe(b, "text", "")) for b in body)

        items = len(body)

        item_count_warn = items > 10
        char_warn = total_chars > self.MAX_BODY_CHARS

        reports = []
        if item_count_warn:
            reports.append(QAReport("warning", "overflow_items", page,
                                    f"{items} body items may overflow slide layout (recommend ≤ 10)"))
        if char_warn:
            reports.append(QAReport("warning", "overflow_chars", page,
                                    f"{total_chars} chars may overflow (recommend ≤ {self.MAX_BODY_CHARS})"))
        return reports

    def _check_layout_conflict(self, slide, page: int) -> list[QAReport]:
        layout = self._safe(slide, "layout_type", "content")
        code = self._safe(slide, "code_block")
        tables = self._safe(slide, "tables", [])
        images = self._safe(slide, "images", [])

        reports = []
        if layout == "content_table" and not tables:
            reports.append(QAReport("info", "layout_mismatch", page,
                                    f"Layout is '{layout}' but no table data found"))
        if layout == "content_code" and not code:
            reports.append(QAReport("info", "layout_mismatch", page,
                                    f"Layout is '{layout}' but no code block found"))
        if layout == "cover" and page > 2:
            reports.append(QAReport("info", "cover_position", page,
                                    f"Cover slide is not at the beginning (page {page})"))
        return reports

    def _check_missing_notes(self, slide, page: int) -> list[QAReport]:
        notes = self._safe(slide, "notes", "")
        if not notes:
            body = self._safe(slide, "body_items", [])
            if len(body) >= 2:
                return [QAReport("info", "missing_notes", page,
                                 "Slide has content but no speaker notes")]
        return []

    def _check_low_density(self, slide, page: int) -> list[QAReport]:
        body = self._safe(slide, "body_items", [])
        if not body:
            return []

        if len(body) < self.MIN_BODY_ITEMS:
            return [QAReport("info", "low_density", page,
                             f"Only {len(body)} body item(s) — consider adding more detail")]
        return []

    def _check_deck_structure(self, slides) -> list[QAReport]:
        reports = []
        if len(slides) < 3:
            reports.append(QAReport("warning", "too_few_slides", 0,
                                    f"Only {len(slides)} slides — presentations typically need 5+"))

        has_cover = slides[0].layout_type == "cover" if hasattr(slides[0], 'layout_type') else False
        if not has_cover:
            reports.append(QAReport("info", "missing_cover", 0,
                                    "No cover slide detected"))

        has_ending = slides[-1].layout_type == "ending" if hasattr(slides[-1], 'layout_type') else False
        if not has_ending and len(slides) > 2:
            reports.append(QAReport("info", "missing_ending", len(slides),
                                    "No ending/thank-you slide detected"))

        return reports

    @staticmethod
    def _safe(obj, attr, default=""):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
