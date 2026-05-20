"""PPTX Generator - produces native DrawingML PPTX from structured slide data."""
from __future__ import annotations
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os
import io
import re
from typing import Optional

from utils.theme_utils import load_theme, DEFAULT_THEME


class PPTXGenerator:
    DIMENSIONS = {
        "16:9": (Inches(13.333), Inches(7.5)),
        "4:3": (Inches(10), Inches(7.5)),
        "3:4": (Inches(7.5), Inches(10)),
        "1:1": (Inches(8), Inches(8)),
    }

    def __init__(self, template_id: str = "professional-blue",
                 theme: Optional[dict] = None,
                 canvas_format: str = "16:9"):
        self.template_id = template_id
        self.theme = theme or load_theme(self._template_dir())
        self.canvas_format = canvas_format
        self.slide_width, self.slide_height = self.DIMENSIONS.get(canvas_format, self.DIMENSIONS["16:9"])

    def _template_dir(self) -> str:
        theme_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "built-in",
            self.template_id, "theme.json"
        )
        if os.path.exists(theme_path):
            return os.path.dirname(theme_path)
        return ""

    def _hex_to_rgb(self, hex_str: str) -> RGBColor:
        hex_str = hex_str.lstrip("#")
        return RGBColor(int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))

    def generate(self, markdown: str, output_path: str, include_notes: bool = True) -> str:
        prs = Presentation()
        prs.slide_width = self.slide_width
        prs.slide_height = self.slide_height

        lines = markdown.strip().split("\n")
        current_slide = None

        for line in lines:
            if line.startswith("# "):
                current_slide = self._add_slide(prs)
                self._add_title(current_slide, line[2:].strip())
            elif line.startswith("## "):
                current_slide = self._add_slide(prs)
                self._add_title(current_slide, line[3:].strip())
            elif line.startswith("### "):
                current_slide = self._add_slide(prs)
                self._add_title(current_slide, line[4:].strip())
            elif line.strip() and current_slide:
                self._add_body(current_slide, line.strip())

        prs.save(output_path)
        return output_path

    def generate_from_slide_data(self, slides: list[dict]) -> bytes:
        prs = Presentation()
        prs.slide_width = self.slide_width
        prs.slide_height = self.slide_height

        for slide_data in slides:
            slide = self._add_slide(prs)
            layout_type = slide_data.get("layout_type", "content")
            title = slide_data.get("title", "")
            subtitle = slide_data.get("subtitle", "")
            body_items = slide_data.get("body_items", [])
            tables = slide_data.get("tables", [])
            images = slide_data.get("images", [])
            notes = slide_data.get("notes", "")
            code_block = slide_data.get("code_block")

            dispatch = {
                "cover": self._render_cover,
                "chapter": self._render_chapter,
                "content": self._render_content,
                "content_two_col": self._render_two_col,
                "content_table": self._render_table,
                "content_code": self._render_code,
                "content_quote": self._render_quote,
                "content_three_col": self._render_three_col,
                "content_compare": self._render_compare,
                "content_kpi": self._render_kpi_dashboard,
                "ending": self._render_ending,
            }

            renderer = dispatch.get(layout_type, self._render_content)
            renderer(slide, title, subtitle, body_items, tables, code_block)

            if notes:
                notes_slide = slide.notes_slide
                tf = notes_slide.notes_text_frame
                tf.text = notes

        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        return buf.read()

    def _add_bg_rect(self, slide, w: int, h: int, color: str):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = self._hex_to_rgb(color)
        shape.line.fill.background()

    def _make_textbox(self, slide, left, top, width, height, text_ops):
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        for op in text_ops:
            text = op.get("t", "")
            size = op.get("s", 18)
            bold = op.get("b", False)
            color = op.get("c", self.theme["colors"]["text"])
            align = op.get("a", None)
            for i, line in enumerate(text.split("\n")):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = line
                p.font.size = Pt(size)
                p.font.bold = bold
                p.font.color.rgb = self._hex_to_rgb(color)
                if align:
                    p.alignment = align

    def _accent_bar(self, slide, left, top, h, color):
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.08), h)
        bar.fill.solid()
        bar.fill.fore_color.rgb = self._hex_to_rgb(color)
        bar.line.fill.background()

    def _parse_markdown_table(self, md: str) -> tuple:
        rows = md.strip().split("\n")
        parsed_rows = []
        for r in rows:
            r = r.strip()
            if not r or r.startswith("|:-") or r.startswith("|-") or r == "|---":
                continue
            if r.startswith("|") and r.endswith("|"):
                cells = [c.strip() for c in r.split("|")]
                cells = [c for c in cells if c != ""]
            else:
                cells = [c.strip() for c in r.split("|") if c.strip()]
            parsed_rows.append(cells)
        if not parsed_rows:
            return ["列1", "列2"], []
        headers = parsed_rows[0]
        data = parsed_rows[1:]
        return headers, data

    def _status_color(self, text: str) -> str:
        if text.startswith("✅") or text.startswith("🟢") or "完成" in text or "达标" in text or text.startswith("↑"):
            return "#059669"
        if text.startswith("⚠️") or text.startswith("🟡") or "进行中" in text or "关注" in text:
            return "#d97706"
        if text.startswith("❌") or text.startswith("🔴") or "延期" in text or "未达标" in text or text.startswith("↓"):
            return "#dc2626"
        return self.theme["colors"]["text"]

    def _is_numeric_cell(self, text: str) -> bool:
        clean = text.replace(",", "").replace("%", "").replace("$", "").replace("¥", "").replace("€", "").replace(" ", "").strip()
        if not clean:
            return False
        return bool(re.match(r'^-?[\d.]+$', clean))

    def _detect_kpi_items(self, body_items: list) -> list:
        kpis = []
        for item in body_items:
            txt = item.get("text", "")
            label_match = re.match(r'^([^0-9:：]+)[:：]?\s*(.*)', txt)
            if label_match:
                label = label_match.group(1).strip()
                value_part = label_match.group(2).strip()
                num_match = re.search(r'([\d,.]+)\s*(%|万|亿|元|美元|美金|人|个|件|笔|万元|亿元)?', value_part)
                if num_match:
                    kpis.append({
                        "label": label,
                        "value": num_match.group(1),
                        "unit": num_match.group(2) or "",
                        "full_text": txt,
                    })
        return kpis

    def _lighten_color(self, hex_str: str, factor: float = 0.15) -> str:
        hex_str = hex_str.lstrip("#")
        r, g, b = int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _render_cover(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")
        secondary = self.theme["colors"].get("secondary", "#3b82f6")

        left_bar_w = Inches(0.1)
        bar1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, left_bar_w, h)
        bar1.fill.solid()
        bar1.fill.fore_color.rgb = self._hex_to_rgb(primary)
        bar1.line.fill.background()

        bar2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_bar_w, 0, Inches(0.06), h)
        bar2.fill.solid()
        bar2.fill.fore_color.rgb = self._hex_to_rgb(acc)
        bar2.line.fill.background()

        bottom_strip_h = Inches(0.35)
        bottom_strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, h - bottom_strip_h, w, bottom_strip_h)
        bottom_strip.fill.solid()
        bottom_strip.fill.fore_color.rgb = self._hex_to_rgb(primary)
        bottom_strip.line.fill.background()

        bottom_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, h - bottom_strip_h, w, Inches(0.04))
        bottom_accent.fill.solid()
        bottom_accent.fill.fore_color.rgb = self._hex_to_rgb(acc)
        bottom_accent.line.fill.background()

        deco1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(11.5), Inches(0.6), Inches(1.5), Inches(0.015))
        deco1.fill.solid()
        deco1.fill.fore_color.rgb = self._hex_to_rgb(acc)
        deco1.line.fill.background()
        deco2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(10.8), Inches(0.8), Inches(2.2), Inches(0.01))
        deco2.fill.solid()
        deco2.fill.fore_color.rgb = self._hex_to_rgb(secondary)
        deco2.line.fill.background()

        tag_text = body_items[0].get("text", "") if body_items and body_items[0].get("text", "").startswith("【") else ""
        tag_label = ""
        if tag_text:
            tag_match = re.match(r"【(.*?)】", tag_text)
            if tag_match:
                tag_label = tag_match.group(1)
        if not tag_label and body_items:
            for item in body_items:
                t = item.get("text", "")
                if "会议" in t or "报告" in t or "汇报" in t or "总结" in t:
                    tag_label = t[:8]
                    break

        if tag_label:
            tag_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(0.45), Inches(2.8), Inches(0.36))
            tag_bg.fill.solid()
            tag_bg.fill.fore_color.rgb = self._hex_to_rgb(self._lighten_color(primary, 0.85))
            tag_bg.line.color.rgb = self._hex_to_rgb(primary)
            tag_bg.line.width = Pt(0.5)
            self._make_textbox(slide, Inches(0.75), Inches(0.46), Inches(2.5), Inches(0.34), [
                {"t": tag_label, "s": 11, "b": True, "c": primary},
            ])

        title_top = Inches(1.8)
        self._make_textbox(slide, Inches(0.6), title_top, Inches(11.8), Inches(1.8), [
            {"t": title, "s": 46, "b": True, "c": primary},
        ])

        accent_line_y = title_top + Inches(2.0)
        accent_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), accent_line_y, Inches(3.5), Inches(0.05))
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = self._hex_to_rgb(acc)
        accent_line.line.fill.background()

        if subtitle:
            self._make_textbox(slide, Inches(0.6), accent_line_y + Inches(0.25), Inches(11.8), Inches(1.5), [
                {"t": subtitle, "s": 20, "c": self.theme["colors"]["text"]},
            ])

        has_date = False
        date_text = ""
        for item in body_items:
            t = item.get("text", "")
            if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', t) or re.search(r'\d{4}\.\d{1,2}\.\d{1,2}', t):
                date_text = t
                has_date = True
                break

        if has_date:
            date_block_x = Inches(10.5)
            date_block_y = h - Inches(0.85)
            date_block_w = Inches(2.5)
            date_block_h = Inches(0.45)
            date_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, date_block_x, date_block_y, date_block_w, date_block_h)
            date_bg.fill.solid()
            date_bg.fill.fore_color.rgb = self._hex_to_rgb("#ffffff")
            date_bg.line.color.rgb = self._hex_to_rgb(primary)
            date_bg.line.width = Pt(0.8)
            date_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, date_block_x, date_block_y, Inches(0.05), date_block_h)
            date_accent.fill.solid()
            date_accent.fill.fore_color.rgb = self._hex_to_rgb(acc)
            date_accent.line.fill.background()
            self._make_textbox(slide, date_block_x + Inches(0.15), date_block_y + Inches(0.05), date_block_w - Inches(0.25), Inches(0.35), [
                {"t": date_text, "s": 12, "c": primary},
            ])

    def _render_chapter(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")
        self._add_bg_rect(slide, w, h, primary)

        deco_top = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.04))
        deco_top.fill.solid()
        deco_top.fill.fore_color.rgb = self._hex_to_rgb(acc)
        deco_top.line.fill.background()

        deco_bottom = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, h - Inches(0.04), w, Inches(0.04))
        deco_bottom.fill.solid()
        deco_bottom.fill.fore_color.rgb = self._hex_to_rgb(acc)
        deco_bottom.line.fill.background()

        self._make_textbox(slide, Inches(1.0), Inches(1.8), Inches(11.3), Inches(1.5), [
            {"t": title, "s": 52, "b": True, "c": "#ffffff"},
        ])
        if subtitle:
            self._make_textbox(slide, Inches(1.0), Inches(3.5), Inches(11.3), Inches(1.0), [
                {"t": subtitle, "s": 22, "c": "#93c5fd"},
            ])

        acc_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(3.3), Inches(2.5), Inches(0.06))
        acc_line.fill.solid()
        acc_line.fill.fore_color.rgb = self._hex_to_rgb(acc)
        acc_line.line.fill.background()

    def _render_content(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")
        surface = self.theme["colors"].get("surface", "#f8fafc")
        light_primary = self._lighten_color(primary, 0.85)

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.75))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()

        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(0.75))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()

        top_deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.75), w, Inches(0.015))
        top_deco.fill.solid()
        top_deco.fill.fore_color.rgb = self._hex_to_rgb(acc)
        top_deco.line.fill.background()

        self._make_textbox(slide, Inches(0.6), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 28, "b": True, "c": "#ffffff"},
        ])
        if subtitle:
            self._make_textbox(slide, Inches(0.6), Inches(0.85), Inches(12), Inches(0.4), [
                {"t": subtitle, "s": 13, "c": self.theme["colors"].get("secondary", "#64748b")},
            ])

        kpis = self._detect_kpi_items(body_items)
        has_kpi = bool(kpis and len(kpis) >= 2)

        if has_kpi:
            self._render_content_kpi_cards(slide, kpis, primary, acc, surface, light_primary, w, h)
        else:
            self._render_content_cards(slide, body_items, primary, acc, surface, light_primary, w, h)

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_content_cards(self, slide, body_items, primary, acc, surface, light_primary, w, h):
        items = [it for it in body_items if it.get("text", "").strip()]
        if not items:
            self._make_textbox(slide, Inches(1.0), Inches(2.5), Inches(11.3), Inches(2.0), [
                {"t": "（暂无内容）", "s": 18, "c": "#9ca3af", "a": PP_ALIGN.CENTER},
            ])
            return

        max_items = 5
        items = items[:max_items]
        n = len(items)
        card_h = Inches(min(1.05, 5.1 / max(n, 1)))
        gap = Inches(0.08)
        start_y = Inches(1.2) if not any(it.get("text", "").startswith("【") for it in items) else Inches(1.15)
        available_h = Inches(5.8)
        total_h = card_h * n + gap * (n - 1)
        if total_h > available_h:
            card_h = int((available_h - gap * (n - 1)) / n)
            total_h = card_h * n + gap * (n - 1)
        start_y = Inches(1.15) + (available_h - total_h) * 0.5

        badge_colors = [primary, acc, "#6366f1", "#0891b2", "#7c3aed"]

        for idx, item in enumerate(items):
            txt = item.get("text", "")
            y_pos = start_y + idx * (card_h + gap)
            card_x = Inches(0.6)
            card_w = Inches(12.1)

            card_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_x, y_pos, card_w, card_h)
            card_bg.fill.solid()
            bg_color = "#ffffff" if idx % 2 == 0 else surface
            card_bg.fill.fore_color.rgb = self._hex_to_rgb(bg_color)
            card_bg.line.color.rgb = self._hex_to_rgb("#e5e7eb")
            card_bg.line.width = Pt(0.5)

            badge_color = badge_colors[idx % len(badge_colors)]
            badge = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_x, y_pos, Inches(0.06), card_h)
            badge.fill.solid()
            badge.fill.fore_color.rgb = self._hex_to_rgb(badge_color)
            badge.line.fill.background()

            num_badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, card_x + Inches(0.2), y_pos + Inches(0.18), Inches(0.32), Inches(0.32))
            num_badge.fill.solid()
            num_badge.fill.fore_color.rgb = self._hex_to_rgb(badge_color)
            num_badge.line.fill.background()
            self._make_textbox(slide, card_x + Inches(0.2), y_pos + Inches(0.18), Inches(0.32), Inches(0.32), [
                {"t": str(idx + 1), "s": 10, "b": True, "c": "#ffffff", "a": PP_ALIGN.CENTER},
            ])

            self._make_textbox(slide, card_x + Inches(0.7), y_pos + Inches(0.08), card_w - Inches(0.9), card_h - Inches(0.16), [
                {"t": txt, "s": 15, "c": self.theme["colors"]["text"]},
            ])

    def _render_content_kpi_cards(self, slide, kpis, primary, acc, surface, light_primary, w, h):
        n = len(kpis)
        cols = min(n, 4)
        rows = (n + cols - 1) // cols
        card_w = Inches(2.95)
        card_h = Inches(1.85)
        gap_x = Inches(0.3)
        gap_y = Inches(0.25)
        total_w = card_w * cols + gap_x * (cols - 1)
        total_h = card_h * rows + gap_y * (rows - 1)
        start_x = (w - total_w) / 2
        start_y = Inches(1.2) + (Inches(5.5) - total_h) / 2

        card_colors = [
            (primary, self._lighten_color(primary, 0.88)),
            (acc, "#fef9e7"),
            ("#6366f1", "#eef2ff"),
            ("#0891b2", "#ecfeff"),
            ("#059669", "#ecfdf5"),
            ("#7c3aed", "#f5f3ff"),
            ("#dc2626", "#fef2f2"),
            ("#d97706", "#fffbeb"),
        ]

        for idx, kpi in enumerate(kpis):
            row = idx // cols
            col = idx % cols
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)

            color_pair = card_colors[idx % len(card_colors)]
            accent_color = color_pair[0]
            bg_color = color_pair[1]

            card_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, card_w, card_h)
            card_bg.fill.solid()
            card_bg.fill.fore_color.rgb = self._hex_to_rgb(bg_color)
            card_bg.line.color.rgb = self._hex_to_rgb("#e5e7eb")
            card_bg.line.width = Pt(0.5)

            top_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, card_w, Inches(0.05))
            top_accent.fill.solid()
            top_accent.fill.fore_color.rgb = self._hex_to_rgb(accent_color)
            top_accent.line.fill.background()

            self._make_textbox(slide, cx + Inches(0.15), cy + Inches(0.15), card_w - Inches(0.3), Inches(0.45), [
                {"t": kpi["label"], "s": 12, "c": "#64748b"},
            ])

            value_text = kpi["value"]
            unit_text = kpi["unit"]
            if unit_text:
                self._make_textbox(slide, cx + Inches(0.15), cy + Inches(0.55), card_w - Inches(0.3), Inches(0.8), [
                    {"t": value_text, "s": 32, "b": True, "c": accent_color},
                ])
                self._make_textbox(slide, cx + Inches(0.15), cy + Inches(1.35), card_w - Inches(0.3), Inches(0.35), [
                    {"t": unit_text, "s": 13, "c": "#64748b"},
                ])
            else:
                self._make_textbox(slide, cx + Inches(0.15), cy + Inches(0.55), card_w - Inches(0.3), Inches(1.0), [
                    {"t": value_text, "s": 32, "b": True, "c": accent_color},
                ])

    def _render_compare(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.75))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(0.75))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        top_deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.75), w, Inches(0.015))
        top_deco.fill.solid()
        top_deco.fill.fore_color.rgb = self._hex_to_rgb(acc)
        top_deco.line.fill.background()
        self._make_textbox(slide, Inches(0.6), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        before = []
        after = []
        for item in body_items:
            col = item.get("column", "left")
            if col == "right":
                after.append(item.get("text", ""))
            else:
                before.append(item.get("text", ""))

        col_w = Inches(5.25)
        b_left = Inches(0.55)
        a_left = Inches(6.08)
        c_top = Inches(1.25)

        b_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, b_left, c_top, col_w, Inches(4.6))
        b_bg.fill.solid()
        b_bg.fill.fore_color.rgb = self._hex_to_rgb("#fef2f2")
        b_bg.line.color.rgb = self._hex_to_rgb("#fca5a5")
        b_bg.line.width = Pt(0.5)
        b_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, b_left, c_top, col_w, Inches(0.55))
        b_bar.fill.solid()
        b_bar.fill.fore_color.rgb = self._hex_to_rgb("#dc2626")
        b_bar.line.fill.background()
        b_top_text = "Before / 现状"
        for item in body_items:
            t = item.get("text", "")
            if re.search(r'【\s*(Before|之前|现状|改善前)', t):
                m = re.match(r"【(.*?)】", t)
                if m:
                    b_top_text = m.group(1)
                    break
        self._make_textbox(slide, b_left + Inches(0.15), c_top + Inches(0.08), col_w - Inches(0.3), Inches(0.4), [
            {"t": b_top_text, "s": 17, "b": True, "c": "#ffffff"},
        ])
        self._make_textbox(slide, b_left + Inches(0.15), c_top + Inches(0.75), col_w - Inches(0.3), Inches(3.5), [
            {"t": "\n".join(f"• {x}" for x in before) if before else " ",
             "s": 13, "c": "#7f1d1d"},
        ])

        a_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, a_left, c_top, col_w, Inches(4.6))
        a_bg.fill.solid()
        a_bg.fill.fore_color.rgb = self._hex_to_rgb("#ecfdf5")
        a_bg.line.color.rgb = self._hex_to_rgb("#6ee7b7")
        a_bg.line.width = Pt(0.5)
        a_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, a_left, c_top, col_w, Inches(0.55))
        a_bar.fill.solid()
        a_bar.fill.fore_color.rgb = self._hex_to_rgb("#059669")
        a_bar.line.fill.background()
        a_top_text = "After / 目标"
        for item in body_items:
            t = item.get("text", "")
            if re.search(r'【\s*(After|之后|目标|改善后)', t):
                m = re.match(r"【(.*?)】", t)
                if m:
                    a_top_text = m.group(1)
                    break
        self._make_textbox(slide, a_left + Inches(0.15), c_top + Inches(0.08), col_w - Inches(0.3), Inches(0.4), [
            {"t": a_top_text, "s": 17, "b": True, "c": "#ffffff"},
        ])
        self._make_textbox(slide, a_left + Inches(0.15), c_top + Inches(0.75), col_w - Inches(0.3), Inches(3.5), [
            {"t": "\n".join(f"• {x}" for x in after) if after else " ",
             "s": 13, "c": "#064e3b"},
        ])

        arrow_x = Inches(5.88)
        arrow_y = c_top + Inches(1.8)
        arrow_bg = slide.shapes.add_shape(MSO_SHAPE.OVAL, arrow_x, arrow_y, Inches(0.48), Inches(0.48))
        arrow_bg.fill.solid()
        arrow_bg.fill.fore_color.rgb = self._hex_to_rgb(self._lighten_color(primary, 0.8))
        arrow_bg.line.color.rgb = self._hex_to_rgb(primary)
        arrow_bg.line.width = Pt(0.8)
        arrow_right = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, arrow_x + Inches(0.09), arrow_y + Inches(0.09), Inches(0.3), Inches(0.3))
        arrow_right.fill.solid()
        arrow_right.fill.fore_color.rgb = self._hex_to_rgb(primary)
        arrow_right.line.fill.background()

        diff_text_parts = []
        for bi, ai in zip(before, after):
            b_num = re.findall(r'[\d,.]+', bi)
            a_num = re.findall(r'[\d,.]+', ai)
            if b_num and a_num:
                try:
                    bv = float(b_num[0].replace(",", ""))
                    av = float(a_num[0].replace(",", ""))
                    if bv != 0:
                        change = ((av - bv) / bv) * 100
                        trend = "↑" if change > 0 else "↓"
                        color = "#059669" if change > 0 else "#dc2626"
                        label_match_b = re.match(r'[^0-9]*', bi)
                        label = label_match_b.group(0).strip().rstrip(":：• ")[:4] if label_match_b else ""
                        diff_text_parts.append(f"{trend} {abs(change):.0f}%")
                        break
                except (ValueError, TypeError):
                    pass

        if diff_text_parts:
            diff_y = c_top + Inches(2.4)
            diff_str = "  ".join(diff_text_parts[:2])
            self._make_textbox(slide, Inches(4.8), diff_y, Inches(2.9), Inches(0.35), [
                {"t": diff_str, "s": 14, "b": True, "c": primary, "a": PP_ALIGN.CENTER},
            ])

        if subtitle:
            sub_y = c_top + Inches(4.9)
            self._make_textbox(slide, Inches(0.55), sub_y, Inches(12.2), Inches(0.35), [
                {"t": subtitle, "s": 12, "c": "#94a3b8", "a": PP_ALIGN.CENTER},
            ])

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_two_col(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.75))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(0.75))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        top_deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.75), w, Inches(0.015))
        top_deco.fill.solid()
        top_deco.fill.fore_color.rgb = self._hex_to_rgb(acc)
        top_deco.line.fill.background()
        self._make_textbox(slide, Inches(0.6), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        left_items = []
        right_items = []
        for item in body_items:
            col = item.get("column", "left")
            txt = item.get("text", "")
            if col == "right":
                right_items.append(txt)
            else:
                left_items.append(txt)

        lh_left = "左侧"
        lh_right = "右侧"
        for item in body_items:
            t = item.get("text", "")
            if t.startswith("【"):
                m = re.match(r"【(.*?)】", t)
                if m:
                    if item.get("column") == "right":
                        lh_right = m.group(1)
                    else:
                        lh_left = m.group(1)
        if subtitle and "vs" in subtitle.lower():
            parts = subtitle.lower().split("vs")
            if len(parts) == 2:
                lh_left = parts[0].strip()
                lh_right = parts[1].strip()

        col_w = Inches(5.55)
        col_l = Inches(0.55)
        col_r = Inches(6.45)
        col_top = Inches(1.15)

        l_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, col_l, col_top, col_w, Inches(5.2))
        l_bg.fill.solid()
        l_bg.fill.fore_color.rgb = self._hex_to_rgb("#ffffff")
        l_bg.line.color.rgb = self._hex_to_rgb("#e5e7eb")
        l_bg.line.width = Pt(0.5)

        lh_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col_l, col_top, col_w, Inches(0.55))
        lh_bg.fill.solid()
        lh_bg.fill.fore_color.rgb = self._hex_to_rgb(primary)
        lh_bg.line.fill.background()
        ab_left = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col_l, col_top, Inches(0.06), Inches(0.55))
        ab_left.fill.solid()
        ab_left.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab_left.line.fill.background()
        self._make_textbox(slide, col_l + Inches(0.2), col_top + Inches(0.08), col_w - Inches(0.35), Inches(0.4), [
            {"t": lh_left, "s": 17, "b": True, "c": "#ffffff"},
        ])

        r_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, col_r, col_top, col_w, Inches(5.2))
        r_bg.fill.solid()
        r_bg.fill.fore_color.rgb = self._hex_to_rgb("#ffffff")
        r_bg.line.color.rgb = self._hex_to_rgb("#e5e7eb")
        r_bg.line.width = Pt(0.5)

        rh_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col_r, col_top, col_w, Inches(0.55))
        rh_bg.fill.solid()
        rh_bg.fill.fore_color.rgb = self._hex_to_rgb(acc)
        rh_bg.line.fill.background()
        ab_right = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, col_r, col_top, Inches(0.06), Inches(0.55))
        ab_right.fill.solid()
        ab_right.fill.fore_color.rgb = self._hex_to_rgb(primary)
        ab_right.line.fill.background()
        self._make_textbox(slide, col_r + Inches(0.2), col_top + Inches(0.08), col_w - Inches(0.35), Inches(0.4), [
            {"t": lh_right, "s": 17, "b": True, "c": "#ffffff"},
        ])

        div_x = Inches(6.12)
        div_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, div_x, col_top + Inches(0.7), Inches(0.015), Inches(4.3))
        div_bar.fill.solid()
        div_bar.fill.fore_color.rgb = self._hex_to_rgb("#e5e7eb")
        div_bar.line.fill.background()

        vs_badge = slide.shapes.add_shape(MSO_SHAPE.OVAL, div_x - Inches(0.16), col_top + Inches(2.5), Inches(0.35), Inches(0.35))
        vs_badge.fill.solid()
        vs_badge.fill.fore_color.rgb = self._hex_to_rgb(primary)
        vs_badge.line.fill.background()
        self._make_textbox(slide, div_x - Inches(0.16), col_top + Inches(2.52), Inches(0.35), Inches(0.3), [
            {"t": "VS", "s": 8, "b": True, "c": "#ffffff", "a": PP_ALIGN.CENTER},
        ])

        self._make_textbox(slide, col_l + Inches(0.2), col_top + Inches(0.75), col_w - Inches(0.35), Inches(4.2), [
            {"t": "\n".join(f"• {x}" for x in left_items) if left_items else " ",
             "s": 13, "c": self.theme["colors"]["text"]},
        ])
        self._make_textbox(slide, col_r + Inches(0.2), col_top + Inches(0.75), col_w - Inches(0.35), Inches(4.2), [
            {"t": "\n".join(f"• {x}" for x in right_items) if right_items else " ",
             "s": 13, "c": self.theme["colors"]["text"]},
        ])

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_table(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.75))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(0.75))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        top_deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.75), w, Inches(0.015))
        top_deco.fill.solid()
        top_deco.fill.fore_color.rgb = self._hex_to_rgb(acc)
        top_deco.line.fill.background()

        self._make_textbox(slide, Inches(0.6), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        headers = ["列1", "列2", "列3", "列4"]
        rows_data = []
        md_table = None

        if isinstance(tables, list) and tables:
            for t in tables:
                if isinstance(t, dict) and t.get("markdown"):
                    md_table = t["markdown"]
                    break
                elif isinstance(t, str):
                    md_table = t
                    break

        if md_table:
            headers, rows_data = self._parse_markdown_table(md_table)

        if not rows_data:
            for item in body_items:
                txt = item.get("text", "")
                if "|" in txt and not txt.startswith("•"):
                    parts = [p.strip() for p in txt.split("|") if p.strip()]
                    if len(parts) >= 2:
                        rows_data.append(parts)
            if rows_data and len(rows_data[0]) > len(headers):
                headers = [f"列{i+1}" for i in range(len(rows_data[0]))]

        n_cols = max(len(headers), 2)
        n_cols = min(n_cols, 8)
        rows_data = rows_data[:18]
        n_rows = len(rows_data)

        tbl_left = Inches(0.6)
        tbl_top = Inches(1.15)
        max_tbl_w = Inches(12.1)
        tbl_h = min(Inches(0.42) * (n_rows + 1), Inches(5.5))

        numeric_cols = set()
        col_max_lens = [len(h) for h in headers[:n_cols]]
        for ri, row in enumerate(rows_data):
            for ci, val in enumerate(row[:n_cols]):
                display_val = val.replace("🟢", "").replace("🟡", "").replace("🔴", "").replace("✅","").replace("⚠️","").replace("❌","").replace("↑","").replace("↓","").strip()
                col_max_lens[ci] = max(col_max_lens[ci], len(display_val) if ci < len(col_max_lens) else 0)
                if self._is_numeric_cell(display_val):
                    numeric_cols.add(ci)

        total_len = sum(col_max_lens)
        if total_len > 0:
            col_widths = []
            for ci in range(n_cols):
                ratio = col_max_lens[ci] / total_len if ci < len(col_max_lens) else 0.1
                col_widths.append(max(int(max_tbl_w * max(ratio, 0.08)), int(Inches(1.2))))
            total_allocated = sum(col_widths)
            if total_allocated > max_tbl_w:
                scale = max_tbl_w / total_allocated
                col_widths = [int(w * scale) for w in col_widths]
            elif total_allocated < max_tbl_w:
                extra = max_tbl_w - total_allocated
                col_widths[0] += extra
        else:
            col_widths = [int(max_tbl_w / n_cols)] * n_cols

        table_shape = slide.shapes.add_table(n_rows + 1, n_cols, tbl_left, tbl_top, max_tbl_w, tbl_h)
        table = table_shape.table

        for ci in range(n_cols):
            table.columns[ci].width = col_widths[ci]

        header_fill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, tbl_left, tbl_top, max_tbl_w, Inches(0.42))
        header_fill.fill.solid()
        header_fill.fill.fore_color.rgb = self._hex_to_rgb(primary)
        header_fill.line.fill.background()

        for ci, header in enumerate(headers[:n_cols]):
            cell = table.cell(0, ci)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.text = header
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = self._hex_to_rgb("#ffffff")
            p.alignment = PP_ALIGN.CENTER
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self._hex_to_rgb(primary)

        striped_colors = ["#ffffff", self.theme["colors"].get("surface", "#f8fafc")]
        status_colors_map = {
            "🟢": "#059669", "✅": "#059669", "↑": "#059669",
            "🟡": "#d97706", "⚠️": "#d97706",
            "🔴": "#dc2626", "❌": "#dc2626", "↓": "#dc2626",
        }

        for ri, row in enumerate(rows_data):
            row_bg_color = striped_colors[ri % 2]
            has_status = any(row[0].startswith(k) for k in status_colors_map if len(row) > 0)
            row_status_color = None
            if has_status and len(row) > 0:
                for k, v in status_colors_map.items():
                    if row[0].startswith(k):
                        row_status_color = v
                        break

            for ci, val in enumerate(row[:n_cols]):
                cell = table.cell(ri + 1, ci)
                display_val = val
                cell.text = ""
                p = cell.text_frame.paragraphs[0]
                p.text = display_val
                p.font.size = Pt(11)

                status_color = None
                for emoji, sc in status_colors_map.items():
                    if display_val.startswith(emoji):
                        status_color = sc
                        break

                if status_color:
                    p.font.color.rgb = self._hex_to_rgb(status_color)
                    p.font.bold = True
                else:
                    clean_val = display_val.replace("🟢","").replace("🟡","").replace("🔴","").replace("✅","").replace("⚠️","").replace("❌","").replace("↑","").replace("↓","").strip()
                    if clean_val and self._is_numeric_cell(clean_val):
                        p.alignment = PP_ALIGN.RIGHT
                        p.font.color.rgb = self._hex_to_rgb(primary)
                        p.font.bold = True
                    else:
                        p.font.color.rgb = self._hex_to_rgb(self.theme["colors"]["text"])

                cell.fill.solid()
                if has_status and row_status_color:
                    r, g, b = int(row_status_color[1:3], 16), int(row_status_color[3:5], 16), int(row_status_color[5:7], 16)
                    bg = RGBColor(min(255, r + 220), min(255, g + 220), min(255, b + 220))
                    cell.fill.fore_color.rgb = bg
                else:
                    cell.fill.fore_color.rgb = self._hex_to_rgb(row_bg_color)

                cell.margin_left = Inches(0.06)
                cell.margin_right = Inches(0.06)

        summary_text = None
        for item in body_items:
            txt = item.get("text", "")
            if txt.startswith("💡") or txt.startswith("📊") or txt.startswith("✨") or "小计" in txt or "合计" in txt:
                summary_text = txt
                break

        if summary_text:
            foot_y = tbl_top + tbl_h + Inches(0.15)
            summary_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, tbl_left, foot_y, max_tbl_w, Inches(0.35))
            summary_bg.fill.solid()
            summary_bg.fill.fore_color.rgb = self._hex_to_rgb(self._lighten_color(primary, 0.9))
            summary_bg.line.fill.background()
            self._make_textbox(slide, tbl_left + Inches(0.15), foot_y + Inches(0.02), max_tbl_w - Inches(0.3), Inches(0.3), [
                {"t": summary_text, "s": 11, "b": True, "c": primary},
            ])

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_code(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.7))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.06), Inches(0.7))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        self._make_textbox(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        cd = code_block or ""
        if not cd:
            for item in body_items:
                cd += item.get("text", "") + "\n"

        code_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.2), Inches(12.1), Inches(5.5))
        code_bg.fill.solid()
        code_bg.fill.fore_color.rgb = self._hex_to_rgb("#1e293b")
        code_bg.line.fill.background()

        self._make_textbox(slide, Inches(1.0), Inches(1.4), Inches(11.3), Inches(5.1), [
            {"t": cd.strip() or "// code", "s": 14, "c": "#e5e7eb"},
        ])

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_quote(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.7))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        acc = self.theme["colors"].get("accent", "#f59e0b")
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.06), Inches(0.7))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        self._make_textbox(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        quote_text = ""
        quote_author = ""
        for item in body_items:
            txt = item.get("text", "")
            if txt.startswith("—") or txt.startswith("--"):
                quote_author = txt.lstrip("—").lstrip("-").strip()
            else:
                quote_text = txt

        if not quote_text and subtitle:
            quote_text = subtitle

        bg_card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.2))
        bg_card.fill.solid()
        bg_card.fill.fore_color.rgb = self._hex_to_rgb(self.theme["colors"].get("surface", "#f8fafc"))
        bg_card.line.fill.background()

        self._accent_bar(slide, Inches(1.0), Inches(1.8), Inches(4.2), primary)

        self._make_textbox(slide, Inches(1.5), Inches(2.2), Inches(10.3), Inches(2.5), [
            {"t": f'"{quote_text}"', "s": 28, "c": primary},
        ])

        if quote_author:
            self._make_textbox(slide, Inches(1.5), Inches(5.0), Inches(10.3), Inches(0.6), [
                {"t": f"— {quote_author}", "s": 18, "c": self.theme["colors"]["text"]},
            ])

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_three_col(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.7))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.06), Inches(0.7))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        self._make_textbox(slide, Inches(0.5), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])

        cols = {"left": [], "center": [], "right": []}
        for item in body_items:
            col = item.get("column", "left")
            txt = item.get("text", "")
            if col in cols:
                cols[col].append(txt)

        col_w = Inches(3.8)
        g = Inches(0.4)
        offsets = [Inches(0.5), Inches(4.7), Inches(8.9)]
        keys = ["left", "center", "right"]

        for idx, key in enumerate(keys):
            cv = cols[key]
            v_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, offsets[idx], Inches(1.2), col_w, Inches(5.2))
            v_bg.fill.solid()
            v_bg.fill.fore_color.rgb = self._hex_to_rgb(self.theme["colors"].get("surface", "#f8fafc"))
            v_bg.line.fill.background()
            if cv:
                self._make_textbox(slide, offsets[idx] + Inches(0.2), Inches(1.4), col_w - Inches(0.4), Inches(4.8), [
                    {"t": "\n\n".join(f"• {x}" for x in cv), "s": 13, "c": self.theme["colors"]["text"]},
                ])
            else:
                self._make_textbox(slide, offsets[idx] + Inches(0.2), Inches(3.5), col_w - Inches(0.4), Inches(0.6), [
                    {"t": "（待补充）", "s": 13, "c": "#9ca3af"},
                ])

        for i in [1, 2]:
            div = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, offsets[i] - Inches(0.05), Inches(1.2), Inches(0.01), Inches(5.2))
            div.fill.solid()
            div.fill.fore_color.rgb = self._hex_to_rgb("#e5e7eb")
            div.line.fill.background()

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_kpi_dashboard(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, w, Inches(0.75))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self._hex_to_rgb(primary)
        top_bar.line.fill.background()
        ab = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(0.75))
        ab.fill.solid()
        ab.fill.fore_color.rgb = self._hex_to_rgb(acc)
        ab.line.fill.background()
        top_deco = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(0.75), w, Inches(0.015))
        top_deco.fill.solid()
        top_deco.fill.fore_color.rgb = self._hex_to_rgb(acc)
        top_deco.line.fill.background()

        self._make_textbox(slide, Inches(0.6), Inches(0.1), Inches(12), Inches(0.6), [
            {"t": title, "s": 26, "b": True, "c": "#ffffff"},
        ])
        if subtitle:
            self._make_textbox(slide, Inches(0.6), Inches(0.85), Inches(12), Inches(0.4), [
                {"t": subtitle, "s": 12, "c": "#94a3b8"},
            ])

        kpis = self._detect_kpi_items(body_items)
        if not kpis:
            self._make_textbox(slide, Inches(1.0), Inches(2.5), Inches(11.3), Inches(2.0), [
                {"t": "（暂无KPI数据）", "s": 18, "c": "#9ca3af", "a": PP_ALIGN.CENTER},
            ])
            return

        n = len(kpis)
        cols = min(n, 4)
        rows = (n + cols - 1) // cols
        card_w = Inches(2.85)
        card_h = Inches(2.0)
        gap_x = Inches(0.3)
        gap_y = Inches(0.2)
        total_w = card_w * cols + gap_x * (cols - 1)
        total_h = card_h * rows + gap_y * (rows - 1)
        start_x = (w - total_w) / 2
        start_y = Inches(1.25) + (Inches(5.3) - total_h) / 2

        card_colors = [
            (primary, self._lighten_color(primary, 0.9)),
            (acc, "#fefce8"),
            ("#6366f1", "#eef2ff"),
            ("#0891b2", "#ecfeff"),
            ("#059669", "#ecfdf5"),
            ("#7c3aed", "#f5f3ff"),
            ("#dc2626", "#fef2f2"),
            ("#d97706", "#fff7ed"),
        ]

        for idx, kpi in enumerate(kpis):
            row = idx // cols
            col = idx % cols
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)

            color_pair = card_colors[idx % len(card_colors)]
            card_accent = color_pair[0]
            card_bg = color_pair[1]

            bg_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, card_w, card_h)
            bg_shape.fill.solid()
            bg_shape.fill.fore_color.rgb = self._hex_to_rgb(card_bg)
            bg_shape.line.color.rgb = self._hex_to_rgb("#e5e7eb")
            bg_shape.line.width = Pt(0.5)

            top_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, cy, card_w, Inches(0.05))
            top_line.fill.solid()
            top_line.fill.fore_color.rgb = self._hex_to_rgb(card_accent)
            top_line.line.fill.background()

            label = kpi["label"]
            value = kpi["value"]
            unit = kpi["unit"]

            trend = ""
            label_display = label
            if label.startswith("↑"):
                trend = "up"
                label_display = label[1:].strip()
            elif label.startswith("↓"):
                trend = "down"
                label_display = label[1:].strip()

            self._make_textbox(slide, cx + Inches(0.12), cy + Inches(0.15), card_w - Inches(0.24), Inches(0.4), [
                {"t": label_display, "s": 11, "c": "#64748b"},
            ])

            value_font_size = 36 if len(value) <= 4 else (28 if len(value) <= 7 else 22)

            if unit == "%":
                pct_val = value.replace(",", "")
                try:
                    pct = float(pct_val)
                    bar_color = "#059669" if pct >= 80 else ("#d97706" if pct >= 60 else "#dc2626")
                    self._make_textbox(slide, cx + Inches(0.12), cy + Inches(0.5), card_w - Inches(0.24), Inches(0.65), [
                        {"t": f"{value}%", "s": value_font_size, "b": True, "c": bar_color},
                    ])
                    bar_y = cy + Inches(1.2)
                    bar_full_w = card_w - Inches(0.24)
                    bar_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + Inches(0.12), bar_y, bar_full_w, Inches(0.1))
                    bar_bg.fill.solid()
                    bar_bg.fill.fore_color.rgb = self._hex_to_rgb("#e5e7eb")
                    bar_bg.line.fill.background()
                    bar_fill_w = int(bar_full_w * min(pct / 100, 1.0))
                    if bar_fill_w > 0:
                        bar_fill = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx + Inches(0.12), bar_y, bar_fill_w, Inches(0.1))
                        bar_fill.fill.solid()
                        bar_fill.fill.fore_color.rgb = self._hex_to_rgb(bar_color)
                        bar_fill.line.fill.background()
                except (ValueError, TypeError):
                    self._make_textbox(slide, cx + Inches(0.12), cy + Inches(0.5), card_w - Inches(0.24), Inches(0.65), [
                        {"t": f"{value}%", "s": value_font_size, "b": True, "c": card_accent},
                    ])
            else:
                self._make_textbox(slide, cx + Inches(0.12), cy + Inches(0.5), card_w - Inches(0.24), Inches(0.65), [
                    {"t": value, "s": value_font_size, "b": True, "c": card_accent},
                ])
                if unit:
                    self._make_textbox(slide, cx + Inches(0.12), cy + Inches(1.25), card_w - Inches(0.24), Inches(0.35), [
                        {"t": unit, "s": 12, "c": "#64748b"},
                    ])

            if trend == "up":
                arrow_shape = slide.shapes.add_shape(MSO_SHAPE.UP_ARROW, cx + card_w - Inches(0.5), cy + Inches(0.18), Inches(0.3), Inches(0.28))
                arrow_shape.fill.solid()
                arrow_shape.fill.fore_color.rgb = self._hex_to_rgb("#059669")
                arrow_shape.line.fill.background()
            elif trend == "down":
                arrow_shape = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, cx + card_w - Inches(0.5), cy + Inches(0.18), Inches(0.3), Inches(0.28))
                arrow_shape.fill.solid()
                arrow_shape.fill.fore_color.rgb = self._hex_to_rgb("#dc2626")
                arrow_shape.line.fill.background()

        foot = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.2), w, Inches(0.3))
        foot.fill.solid()
        foot.fill.fore_color.rgb = self._hex_to_rgb("#f0f4ff")
        foot.line.fill.background()

    def _render_ending(self, slide, title, subtitle, body_items, tables, code_block):
        w, h = self.slide_width, self.slide_height
        primary = self.theme["colors"]["primary"]
        acc = self.theme["colors"].get("accent", "#f59e0b")

        self._add_bg_rect(slide, w, h, self.theme["colors"]["background"])

        left_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), h)
        left_accent.fill.solid()
        left_accent.fill.fore_color.rgb = self._hex_to_rgb(primary)
        left_accent.line.fill.background()

        left_accent2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.12), 0, Inches(0.06), h)
        left_accent2.fill.solid()
        left_accent2.fill.fore_color.rgb = self._hex_to_rgb(acc)
        left_accent2.line.fill.background()

        bottom_strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, h - Inches(0.3), w, Inches(0.3))
        bottom_strip.fill.solid()
        bottom_strip.fill.fore_color.rgb = self._hex_to_rgb(primary)
        bottom_strip.line.fill.background()

        bottom_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, h - Inches(0.3), w, Inches(0.03))
        bottom_accent.fill.solid()
        bottom_accent.fill.fore_color.rgb = self._hex_to_rgb(acc)
        bottom_accent.line.fill.background()

        self._make_textbox(slide, Inches(1.5), Inches(1.8), Inches(10.3), Inches(1.5), [
            {"t": title or "感谢聆听", "s": 48, "b": True, "c": primary, "a": PP_ALIGN.CENTER},
        ])

        if subtitle:
            self._make_textbox(slide, Inches(1.5), Inches(3.3), Inches(10.3), Inches(1.0), [
                {"t": subtitle, "s": 20, "c": self.theme["colors"]["text"], "a": PP_ALIGN.CENTER},
            ])

        deco_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.5), Inches(3.1), Inches(2.3), Inches(0.04))
        deco_line.fill.solid()
        deco_line.fill.fore_color.rgb = self._hex_to_rgb(acc)
        deco_line.line.fill.background()

        body_txt = []
        for item in body_items:
            body_txt.append(item.get("text", ""))
        if body_txt:
            contact_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.0), Inches(4.5), Inches(7.3), Inches(1.8))
            contact_bg.fill.solid()
            contact_bg.fill.fore_color.rgb = self._hex_to_rgb(self._lighten_color(primary, 0.92))
            contact_bg.line.color.rgb = self._hex_to_rgb(primary)
            contact_bg.line.width = Pt(0.5)
            contact_accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3.0), Inches(4.5), Inches(7.3), Inches(0.04))
            contact_accent.fill.solid()
            contact_accent.fill.fore_color.rgb = self._hex_to_rgb(acc)
            contact_accent.line.fill.background()
            self._make_textbox(slide, Inches(3.5), Inches(4.75), Inches(6.3), Inches(1.3), [
                {"t": "\n".join(body_txt), "s": 14, "c": self.theme["colors"]["text"], "a": PP_ALIGN.CENTER},
            ])

    def generate_from_slides(self, slides: list[dict], output_path: str) -> str:
        data = self.generate_from_slide_data(slides)
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path

    def _add_slide(self, prs: Presentation):
        blank_layout = next((l for l in prs.slide_layouts if l.name == "Blank"), prs.slide_layouts[0])
        return prs.slides.add_slide(blank_layout)

    def _add_title(self, slide, text: str):
        left = Inches(0.8)
        top = Inches(0.4)
        width = Inches(11.7)
        height = Inches(0.8)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = self._hex_to_rgb(self.theme["colors"]["primary"])

    def _add_body(self, slide, text: str):
        left = Inches(0.8)
        top = Inches(1.4)
        width = Inches(11.7)
        height = Inches(5.5)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True

        for i, line in enumerate(text.split("\n")):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(18)
            p.font.color.rgb = self._hex_to_rgb(self.theme["colors"]["text"])
            p.space_after = Pt(6)
