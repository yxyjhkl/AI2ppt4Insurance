"""PPTX Generator - Professional grade slide rendering with visual hierarchy."""
from __future__ import annotations
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os, io, re
from typing import Optional
from utils.json_utils import CANVAS_INCHES
from utils.theme_utils import load_theme


class PPTXGenerator:
    DIMENSIONS = {k: (Inches(v[0]), Inches(v[1])) for k, v in CANVAS_INCHES.items()}

    # Professional color palette
    PALETTE = {
        "dark_bg": "065A82",
        "accent": "F96167",
        "accent_gold": "F9E795",
        "white": "FFFFFF",
        "off_white": "F2F8FA",
        "card_bg": "FFFFFF",
        "light_bg": "E8F4F8",
        "text": "1A2332",
        "text_light": "5A6B7B",
        "divider": "D0E4ED",
    }

    def __init__(self, template_id: str = "professional-blue",
                 theme: Optional[dict] = None, canvas_format: str = "16:9"):
        self.template_id = template_id
        self.canvas_format = canvas_format
        self.slide_w, self.slide_h = self.DIMENSIONS.get(canvas_format, self.DIMENSIONS["16:9"])
        self._load_theme_colors(theme)

    def _load_theme_colors(self, theme: Optional[dict]):
        if theme and theme.get("colors"):
            c = theme["colors"]
            self.PALETTE.update({
                "dark_bg": c.get("primary", "065A82").lstrip("#"),
                "accent": c.get("accent", "F96167").lstrip("#"),
            })
            bg = c.get("light-bg", c.get("surface", "F2F8FA")).lstrip("#")
            self.PALETTE["off_white"] = bg
            self.PALETTE["light_bg"] = bg

    def _hex(self, key: str) -> str:
        return self.PALETTE.get(key, "065A82")

    def _rgb(self, hex_str: str) -> RGBColor:
        h = hex_str.lstrip("#")
        if len(h) < 6:
            h = "333333"
        return RGBColor(int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _pc(self, key: str) -> RGBColor:
        return self._rgb(self._hex(key))

    def _lighten(self, hex_str: str, factor: float = 0.7) -> str:
        h = hex_str.lstrip("#")
        try:
            r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            return f"{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "eeeeee"

    def _set_shape_fill(self, shape, color: str, transparency: int = 0):
        shape.fill.solid()
        shape.fill.fore_color.rgb = self._rgb(color)

    def _add_rect(self, slide, x, y, w, h, fill_color: str = None,
                  line_color: str = None, transparency: int = 0):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        if fill_color:
            self._set_shape_fill(shape, fill_color, transparency)
        else:
            shape.fill.background()
        if line_color:
            shape.line.color.rgb = self._rgb(line_color)
        else:
            shape.line.fill.background()
        return shape

    def _add_rounded_rect(self, slide, x, y, w, h, fill_color: str = None):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        if fill_color:
            self._set_shape_fill(shape, fill_color)
        else:
            shape.fill.background()
        shape.line.fill.background()
        try:
            shape.adjustments[0] = 0.05
        except Exception:
            pass
        return shape

    def _add_textbox(self, slide, x, y, w, h):
        return slide.shapes.add_textbox(x, y, w, h)

    def _set_text(self, shape, text: str, size: int = 14, bold: bool = False,
                  color: str = None, font: str = "Microsoft YaHei",
                  align=PP_ALIGN.LEFT, valign=None):
        tf = shape.text_frame
        tf.word_wrap = True
        tf.auto_size = None
        p = tf.paragraphs[0]
        p.text = self._safe(str(text))
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.name = font
        p.font.color.rgb = self._rgb(color or self._hex("text"))
        p.alignment = align

    def _safe(self, text: str, max_len: int = 300) -> str:
        if not text:
            return ""
        return str(text).replace("\x00", "").replace("\r", " ")[:max_len]

    def _build_header(self, slide, title: str):
        H = Inches(0.85)
        self._add_rect(slide, 0, 0, self.slide_w, H, self._hex("dark_bg"))
        self._add_rect(slide, 0, H, self.slide_w, Inches(0.035), self._hex("accent"))
        tb = self._add_textbox(slide, Inches(0.5), Inches(0.08), Inches(9), Inches(0.7))
        self._set_text(tb, title, 26, True, self._hex("white"))

    def _build_footer(self, slide):
        self._add_rect(slide, 0, Inches(7.2), self.slide_w, Inches(0.3), self._hex("off_white"))

    # ==================== COVER ====================
    def _render_cover(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("dark_bg"))
        self._add_rect(slide, 0, 0, Inches(0.1), self.slide_h, self._hex("accent"))
        self._add_rect(slide, Inches(0.1), 0, Inches(9.9), Inches(0.03),
                       self._lighten(self._hex("accent_gold"), 0.3))
        tb = self._add_textbox(slide, Inches(0.7), Inches(1.2), Inches(8.5), Inches(1.2))
        self._set_text(tb, title, 44, True, self._hex("white"))
        self._add_rect(slide, Inches(0.7), Inches(2.5), Inches(2.5), Inches(0.05),
                       self._hex("accent"))
        if subtitle:
            tb2 = self._add_textbox(slide, Inches(0.7), Inches(2.75), Inches(8.5), Inches(0.6))
            self._set_text(tb2, subtitle, 20, False, self._hex("accent_gold"))
        # End footer removed - clean ending

    # ==================== CHAPTER ====================
    def _render_chapter(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("dark_bg"))
        self._add_rect(slide, 0, 0, self.slide_w, Inches(0.035), self._hex("accent"))
        self._add_rect(slide, 0, self.slide_h - Inches(0.035), self.slide_w,
                       Inches(0.035), self._hex("accent"))

        # Extract section number from title (e.g. "01  title" or "01")
        import re as _re
        num_match = _re.match(r'^(\d{2})\s+', title or "")
        section_num = num_match.group(1) if num_match else ""
        section_title = title[num_match.end():].strip() if num_match else title

        # Large section number
        if section_num:
            tb_num = self._add_textbox(slide, Inches(0.6), Inches(1.2), Inches(1.8), Inches(1.5))
            self._set_text(tb_num, section_num, 72, True, self._hex("accent"), font="Arial Black")

        # Title
        title_x = Inches(2.6) if section_num else Inches(0.8)
        tb = self._add_textbox(slide, title_x, Inches(1.8), Inches(7.2), Inches(1.5))
        self._set_text(tb, section_title or title, 38, True, self._hex("white"))

        # Decorative line
        line_y = Inches(3.4) if section_num else Inches(3.4)
        self._add_rect(slide, title_x, line_y, Inches(2.2), Inches(0.05), self._hex("accent"))

        if subtitle:
            tb2 = self._add_textbox(slide, title_x, Inches(3.65), Inches(7.2), Inches(0.45))
            self._set_text(tb2, subtitle, 18, False, self._hex("accent_gold"))

        # Corner decorations
        for cx in [Inches(12.2), Inches(0.4)]:
            self._add_rect(slide, cx, Inches(0.2), Inches(0.5), Inches(0.015), self._hex("accent"))
        self._add_rect(slide, title_x, Inches(6.6), Inches(8.5), Inches(0.008),
                       self._lighten(self._hex("accent"), 0.5))

    # ==================== CONTENT (main layout) ====================
    def _render_content(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        items = [it for it in (body_items or []) if isinstance(it, dict) and it.get("text", "").strip()]
        if not items:
            tb = self._add_textbox(slide, Inches(1), Inches(2.5), Inches(8), Inches(3))
            self._set_text(tb, "暂无内容", 18, False, self._hex("text_light"), align=PP_ALIGN.CENTER)
            return

        kpis = self._detect_kpis(items)
        if len(kpis) >= 2:
            self._render_kpi_cards(slide, kpis)
        else:
            self._render_content_cards(slide, items)

    def _detect_kpis(self, items: list) -> list:
        kpis = []
        for item in items:
            txt = item.get("text", "")
            # Match Chinese KPI format: "label: value unit" or "label：value unit"
            m = re.match(r'^([^0-9:：]+?)[:：]\s*(.+)', txt)
            if m:
                label = m.group(1).strip()
                rest = m.group(2).strip()
                nm = re.search(r'([\d,.]+)\s*(%|万|亿|元|人|个|件|笔|点|倍)?', rest)
                if nm and 2 <= len(label) <= 20:
                    kpis.append({"label": label, "value": nm.group(1), "unit": nm.group(2) or ""})
        return kpis[:6]

    def _render_kpi_cards(self, slide, kpis: list):
        n = len(kpis)
        cols = min(n, 4)
        rows = (n + cols - 1) // cols
        card_w = Inches(2.3)
        card_h = Inches(1.8)
        gap_x = Inches(0.2)
        gap_y = Inches(0.18)
        total_w = card_w * cols + gap_x * (cols - 1)
        start_x = (self.slide_w - total_w) / 2
        start_y = Inches(1.15)

        for idx, kpi in enumerate(kpis):
            row, col = idx // cols, idx % cols
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)
            self._add_rounded_rect(slide, cx, cy, card_w, card_h, self._hex("card_bg"))
            self._add_rect(slide, cx, cy, card_w, Inches(0.05), self._hex("accent"))
            tb1 = self._add_textbox(slide, cx + Inches(0.15), cy + Inches(0.15),
                                    card_w - Inches(0.3), Inches(0.3))
            self._set_text(tb1, kpi["label"], 13, False, self._hex("text_light"))
            val_text = kpi["value"]
            if kpi["unit"]:
                val_text += kpi["unit"]
            tb2 = self._add_textbox(slide, cx + Inches(0.15), cy + Inches(0.55),
                                    card_w - Inches(0.3), Inches(0.9))
            val_size = 44 if len(kpi["value"]) <= 4 else 36
            self._set_text(tb2, val_text, val_size, True, self._hex("dark_bg"))

    def _render_content_cards(self, slide, items: list):
        items = items[:7]
        n = len(items)
        gap = Inches(0.12)
        # Actual available: slide(7.5) - header(0.885) - footer(0.3) = 6.315
        avail_h = Inches(6.15)
        # Content starts after header
        content_top = Inches(1.0)
        colors = [self._hex("dark_bg"), self._hex("accent"),
                  self._hex("accent_gold"), self._lighten(self._hex("dark_bg"), 0.5),
                  "6366F1", "0891B2", "7C3AED"]

        # Font size inversely proportional to item count
        font_sizes = {1: 26, 2: 24, 3: 22, 4: 19, 5: 17, 6: 15, 7: 14}

        # Calculate card height to fill available space
        card_h = (avail_h - gap * (n - 1)) / n
        # Adjust for text density
        if n <= 3:
            max_len = max(len(self._safe(it.get("text", ""))) for it in items)
            lines_needed = max(3, (max_len + 28) // 29)
            ideal_h = lines_needed * 0.38
            card_h = max(card_h, Inches(ideal_h))
        card_h = min(card_h, Inches(2.2))  # cap at reasonable max
        card_h = max(card_h, Inches(0.75))  # floor at readable min

        total_h = card_h * n + gap * (n - 1)
        # Add top/bottom padding
        if total_h < avail_h:
            start_y = content_top + (avail_h - total_h) / 2
        else:
            start_y = content_top + Inches(0.15)

        for idx, item in enumerate(items):
            txt = self._safe(item.get("text", ""))
            y = start_y + idx * (card_h + gap)
            cx, cw = Inches(0.35), Inches(9.3)
            cc = colors[idx % len(colors)]

            # Card background + left accent bar
            self._add_rounded_rect(slide, cx, y, cw, card_h, self._hex("card_bg"))
            self._add_rect(slide, cx, y, Inches(0.06), card_h, cc)

            # Numbered circle (larger for fewer items)
            circle_r = Inches(0.17 if n <= 4 else 0.14)
            circle = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                            cx + Inches(0.18), y + (card_h - circle_r * 2) / 2,
                                            circle_r * 2, circle_r * 2)
            self._set_shape_fill(circle, cc)
            tb_num = self._add_textbox(slide, cx + Inches(0.18),
                                       y + (card_h - circle_r * 2) / 2,
                                       circle_r * 2, circle_r * 2)
            num_size = 13 if n <= 4 else 11
            self._set_text(tb_num, str(idx + 1), num_size, True, self._hex("white"),
                           font="Arial", align=PP_ALIGN.CENTER)

            # Text
            font_size = font_sizes.get(n, 13)
            tb_txt = self._add_textbox(slide, cx + Inches(0.72), y + Inches(0.08),
                                       cw - Inches(0.9), card_h - Inches(0.16))
            self._set_text(tb_txt, txt, font_size, False, self._hex("text"))

        # Bottom line only if cards don't fill the space
        if total_h < avail_h - Inches(0.3):
            self._add_rect(slide, Inches(0.35), Inches(6.85), Inches(9.3), Inches(0.01),
                           self._lighten(self._hex("divider"), 0.5))

    # ==================== TWO COLUMN ====================
    def _render_two_col(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        left, right = [], []
        for it in (body_items or []):
            if isinstance(it, dict):
                col = it.get("column", "left")
                txt = self._safe(it.get("text", ""))
                if col == "right":
                    right.append(txt)
                else:
                    left.append(txt)

        # Auto-split if right is empty (common when AI doesn't set column)
        if not right and len(left) >= 4:
            mid = len(left) // 2
            right = left[mid:]
            left = left[:mid]

        col_w = Inches(4.3)
        col_top = Inches(1.1)
        l_x = Inches(0.35)
        r_x = Inches(5.15)

        # Smart labels from title
        left_label = "现 状"
        right_label = "目 标"
        if title and " vs " in title.lower():
            parts = title.lower().split(" vs ", 1)
            if len(parts) >= 2:
                left_label = parts[0].strip()[:6]
                right_label = parts[1].strip()[:6]
        elif title and "对比" in title:
            left_label = "当 前"
            right_label = "优 化"

        # Left column
        self._add_rounded_rect(slide, l_x, col_top, col_w, Inches(5.5), self._hex("card_bg"))
        self._add_rect(slide, l_x, col_top, col_w, Inches(0.42), self._hex("dark_bg"))
        self._add_rect(slide, l_x, col_top, Inches(0.05), Inches(0.42), self._hex("accent"))
        tb_lh = self._add_textbox(slide, l_x + Inches(0.15), col_top + Inches(0.03),
                                  col_w - Inches(0.3), Inches(0.36))
        self._set_text(tb_lh, left_label, 17, True, self._hex("white"))

        # Right column
        self._add_rounded_rect(slide, r_x, col_top, col_w, Inches(5.5), self._hex("card_bg"))
        self._add_rect(slide, r_x, col_top, col_w, Inches(0.42), self._hex("accent"))
        self._add_rect(slide, r_x, col_top, Inches(0.05), Inches(0.42), self._hex("dark_bg"))
        tb_rh = self._add_textbox(slide, r_x + Inches(0.15), col_top + Inches(0.03),
                                  col_w - Inches(0.3), Inches(0.36))
        self._set_text(tb_rh, right_label, 17, True, self._hex("white"))

        # Divider line between columns
        self._add_rect(slide, Inches(4.7), col_top + Inches(0.6), Inches(0.01), Inches(5.2),
                       self._lighten(self._hex("divider"), 0.5))

        for side, x in [(left, l_x), (right, r_x)]:
            text = "\n".join(f"  {t}" for t in side[:7]) if side else " "
            tb = self._add_textbox(slide, x + Inches(0.15), col_top + Inches(0.6),
                                   col_w - Inches(0.3), Inches(4.8))
            self._set_text(tb, text, 15, False, self._hex("text"))

    _render_compare = _render_two_col

    # ==================== THREE COLUMN ====================
    def _render_three_col(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        cols_data = [[], [], []]
        for it in (body_items or []):
            if isinstance(it, dict):
                col = it.get("column", "left")
                txt = self._safe(it.get("text", ""))
                idx = 1 if col == "center" else (2 if col == "right" else 0)
                cols_data[idx].append(txt)

        col_w = Inches(2.9)
        col_top = Inches(1.15)
        colors = [self._hex("dark_bg"), self._hex("accent"), self._hex("accent_gold")]
        labels = ["板块一", "板块二", "板块三"]

        for ci in range(3):
            cx = Inches(0.35) + ci * (col_w + Inches(0.2))
            self._add_rounded_rect(slide, cx, col_top, col_w, Inches(5.5), self._hex("card_bg"))
            self._add_rect(slide, cx, col_top, col_w, Inches(0.05), colors[ci])
            tb_h = self._add_textbox(slide, cx + Inches(0.15), col_top + Inches(0.15),
                                     col_w - Inches(0.3), Inches(0.3))
            self._set_text(tb_h, labels[ci], 13, True, colors[ci])
            texts = "\n".join(f"  {t}" for t in cols_data[ci][:7]) if cols_data[ci] else " "
            tb_b = self._add_textbox(slide, cx + Inches(0.15), col_top + Inches(0.55),
                                     col_w - Inches(0.3), Inches(4.5))
            self._set_text(tb_b, texts, 11, False, self._hex("text"))

    # ==================== TABLE ====================
    def _render_table(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        headers, rows = ["列1", "列2"], []
        md_table = None
        if isinstance(tables, list):
            for t in tables:
                if isinstance(t, dict):
                    md_val = t.get("markdown")
                    if isinstance(md_val, list):
                        md_val = "\n".join(str(line) for line in md_val)
                    if md_val and isinstance(md_val, str):
                        md_table = md_val
                        break
                elif isinstance(t, str):
                    md_table = t
                    break
        if md_table:
            headers, rows = self._parse_table(md_table)
        if not rows:
            for item in (body_items or []):
                txt = item.get("text", "")
                if "|" in txt:
                    parts = [p.strip() for p in txt.split("|") if p.strip()]
                    if len(parts) >= 2:
                        rows.append(parts)
            if rows and len(rows[0]) > len(headers):
                headers = [f"列{i+1}" for i in range(len(rows[0]))]

        n_cols = min(max(len(headers), 2), 8)
        n_rows = min(len(rows), 20)
        tbl_left = Inches(0.4)
        tbl_top = Inches(1.15)
        tbl_w = Inches(9.2)
        row_h = Inches(0.38)
        header_h = Inches(0.42)
        tbl_h = header_h + row_h * n_rows

        # Build table
        table_shape = slide.shapes.add_table(n_rows + 1, n_cols, tbl_left, tbl_top, tbl_w, tbl_h)
        table = table_shape.table
        col_w_default = int(tbl_w / n_cols)
        for ci in range(n_cols):
            table.columns[ci].width = col_w_default

        for ci, h in enumerate(headers[:n_cols]):
            cell = table.cell(0, ci)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.text = self._safe(h)
            p.font.size = Pt(15)
            p.font.bold = True
            p.font.color.rgb = self._pc("white")
            p.alignment = PP_ALIGN.CENTER
            cell.fill.solid()
            cell.fill.fore_color.rgb = self._pc("dark_bg")

        for ri, row in enumerate(rows[:n_rows]):
            for ci, val in enumerate(row[:n_cols]):
                cell = table.cell(ri + 1, ci)
                cell.text = ""
                p = cell.text_frame.paragraphs[0]
                p.text = self._safe(str(val))
                p.font.size = Pt(13)
                p.font.color.rgb = self._pc("text")
                cell.fill.solid()
                if ri % 2 == 0:
                    cell.fill.fore_color.rgb = self._pc("white")
                else:
                    cell.fill.fore_color.rgb = self._rgb(self._lighten(self._hex("off_white"), 0.5))

    def _parse_table(self, md: str) -> tuple:
        headers, rows = [], []
        if isinstance(md, list):
            md = "\n".join(str(line) for line in md)
        if not isinstance(md, str):
            return ["列1", "列2"], []
        for line in md.strip().split("\n"):
            line = line.strip()
            if not line or "---" in line:
                continue
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]
            if not cells:
                continue
            if not headers:
                headers = cells
            else:
                rows.append(cells)
        if not headers:
            headers = ["列1", "列2"]
        return headers, rows

    # ==================== QUOTE ====================
    def _render_quote(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        quote_text = ""
        quote_author = ""
        for item in (body_items or []):
            txt = item.get("text", "") if isinstance(item, dict) else str(item)
            if txt.startswith("—") or txt.startswith("--"):
                quote_author = txt.lstrip("—").lstrip("-").strip()
            elif not quote_text:
                quote_text = txt

        self._add_rounded_rect(slide, Inches(0.8), Inches(1.5), Inches(8.4), Inches(4.5),
                               self._hex("card_bg"))
        self._add_rect(slide, Inches(0.8), Inches(1.5), Inches(0.07), Inches(4.5),
                       self._hex("dark_bg"))
        tb_q = self._add_textbox(slide, Inches(1.3), Inches(2.0), Inches(7.5), Inches(2.5))
        self._set_text(tb_q, f'"{quote_text}"', 22, False, self._hex("text"))
        if quote_author:
            tb_a = self._add_textbox(slide, Inches(1.3), Inches(4.5), Inches(7.5), Inches(0.4))
            self._set_text(tb_a, f"— {quote_author}", 14, False, self._hex("text_light"))

    # ==================== CODE ====================
    def _render_code(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)

        cd = code_block or ""
        if not cd:
            for item in (body_items or []):
                if isinstance(item, dict):
                    cd += item.get("text", "") + "\n"
        if not cd.strip():
            cd = "// code"

        from pptx.util import Inches as I
        bg = self._add_rounded_rect(slide, I(0.5), I(1.1), I(9), I(5.8), "1E293B")
        tb = self._add_textbox(slide, I(0.8), I(1.3), I(8.4), I(5.4))
        self._set_text(tb, cd, 12, False, "#E5E7EB", font="Consolas")

    # ==================== KPI DASHBOARD ====================
    def _render_kpi_dashboard(self, slide, title, subtitle, body_items, tables, code_block):
        self._render_content(slide, title, subtitle, body_items, tables, code_block)

    # ==================== ENDING ====================
    def _render_ending(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("dark_bg"))
        self._add_rect(slide, 0, 0, Inches(0.1), self.slide_h, self._hex("accent"))
        self._add_rect(slide, Inches(0.1), 0, Inches(9.9), Inches(0.03),
                       self._lighten(self._hex("accent_gold"), 0.3))
        tb = self._add_textbox(slide, Inches(0.8), Inches(1.5), Inches(8.5), Inches(1.0))
        self._set_text(tb, title or "感谢聆听", 40, True, self._hex("white"))
        self._add_rect(slide, Inches(0.8), Inches(2.6), Inches(2.0), Inches(0.05),
                       self._hex("accent"))

        items = [it.get("text", "") for it in (body_items or [])
                 if isinstance(it, dict) and it.get("text", "").strip()][:4]
        if items:
            for i, item in enumerate(items):
                y = Inches(2.9 + i * 0.45)
                tb_i = self._add_textbox(slide, Inches(0.8), y, Inches(8.5), Inches(0.4))
                self._set_text(tb_i, f"  {item}", 13, False,
                               self._hex("accent_gold") if i == 0 else self._hex("white"))

        # Clean ending without footer text

    # ==================== TOC ====================
    def _render_toc(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._add_rect(slide, 0, 0, self.slide_w, Inches(0.85), self._hex("dark_bg"))
        self._add_rect(slide, 0, Inches(0.85), self.slide_w, Inches(0.035), self._hex("accent"))
        tb = self._add_textbox(slide, Inches(0.5), Inches(0.1), Inches(9), Inches(0.65))
        self._set_text(tb, title or "目录", 28, True, self._hex("white"))
        self._build_footer(slide)

        items_raw = [it.get("text", "") for it in (body_items or [])
                     if isinstance(it, dict) and it.get("text", "").strip()][:8]
        if not items_raw:
            return

        items = []
        for t in items_raw:
            num = ""
            chap_title = t
            desc = ""
            if " — " in t:
                parts = t.split(" — ", 1)
                chap_title = parts[0].strip()
                desc = parts[1].strip()[:60]
            num_match = re.match(r'^(\d{2})\s+', chap_title)
            if num_match:
                num = num_match.group(1)
                chap_title = chap_title[num_match.end():].strip()
            items.append({"num": num, "title": chap_title, "desc": desc})

        n = len(items)
        gap = Inches(0.1)
        avail_h = Inches(5.8)
        card_w = Inches(9.3)
        card_x = Inches(0.35)
        card_h = (avail_h - gap * (n - 1)) / n
        card_h = max(Inches(0.8), min(Inches(1.1), card_h))
        total_h = card_h * n + gap * (n - 1)
        start_y = Inches(1.0) + (avail_h - total_h) / 2
        
        num_colors = [self._hex("accent"), self._hex("dark_bg"), self._hex("accent_gold"),
                      self._lighten(self._hex("dark_bg"), 0.4), "6366F1", "0891B2", "7C3AED", "059669"]

        for idx, item in enumerate(items):
            y = start_y + idx * (card_h + gap)
            cc = num_colors[idx % len(num_colors)]

            self._add_rounded_rect(slide, card_x, y, card_w, card_h, self._hex("card_bg"))
            self._add_rect(slide, card_x, y, Inches(0.06), card_h, cc)

            if item["num"]:
                tn = self._add_textbox(slide, card_x + Inches(0.4), y + Inches(0.06),
                                       Inches(0.55), card_h - Inches(0.12))
                self._set_text(tn, item["num"], 26, True, cc, font="Arial Black",
                               align=PP_ALIGN.CENTER)
                title_x = card_x + Inches(1.15)
            else:
                title_x = card_x + Inches(0.35)

            title_w = card_w - Inches(1.6) if item["desc"] else card_w - Inches(0.85)
            tt = self._add_textbox(slide, title_x, y + Inches(0.08),
                                   title_w, card_h - Inches(0.16))
            self._set_text(tt, item["title"], 18, True, self._hex("text"))

            if item["desc"]:
                td = self._add_textbox(slide, title_x, y + card_h - Inches(0.42),
                                       title_w, Inches(0.35))
                self._set_text(td, item["desc"], 10, False, self._hex("text_light"))

    # ==================== TIMELINE ====================
    def _render_timeline(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = [it.get("text","") for it in (body_items or [])[:8] if isinstance(it, dict) and it.get("text","").strip()]
        if not items:
            return

        node_x = Inches(0.8)
        text_x = Inches(1.25)
        node_r = Inches(0.1)
        step = Inches(0.78)
        start_y = Inches(1.2)
        node_colors = [self._hex("accent"), self._hex("dark_bg"), self._hex("accent_gold"),
                       "6366F1", "0891B2", "7C3AED", "059669", "D97706"]

        for i, text in enumerate(items):
            y = start_y + i * step
            if y > Inches(6.5):
                break

            # Node circle
            nc = node_colors[i % len(node_colors)]
            node_cy = y + Inches(0.06)
            circle = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                            node_x - node_r, node_cy - node_r,
                                            node_r * 2, node_r * 2)
            self._set_shape_fill(circle, nc)

            # Connecting line to next node (centered between nodes)
            if i < len(items) - 1:
                line_top = node_cy + node_r
                next_top = (start_y + (i + 1) * step) + Inches(0.06) - node_r
                line_h = next_top - line_top
                self._add_rect(slide, node_x, line_top, Inches(0.01),
                               line_h, self._lighten(self._hex("divider"), 0.3))

            # Label and description
            label, _, desc = text.partition(": ") if ": " in text else (text, "", "")
            tb = self._add_textbox(slide, text_x, y, Inches(8.5), Inches(0.26))
            self._set_text(tb, label.strip(), 15, True, self._hex("dark_bg"))
            if desc.strip():
                tb2 = self._add_textbox(slide, text_x, y + Inches(0.26), Inches(8.5), Inches(0.42))
                self._set_text(tb2, desc.strip(), 12, False, self._hex("text_light"))

    # ==================== MATRIX ====================
    def _render_matrix(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = [it.get("text","") for it in (body_items or [])[:4] if isinstance(it, dict) and it.get("text","").strip()]
        if len(items) < 4:
            items = (items + ["", "", "", ""])[:4]
        labels = ["优势 Strengths", "机会 Opportunities", "劣势 Weaknesses", "威胁 Threats"]
        colors = ["059669", "3B82F6", "DC2626", "D97706"]
        positions = [
            (Inches(0.4), Inches(1.1), Inches(4.5), Inches(2.7)),
            (Inches(5.1), Inches(1.1), Inches(4.5), Inches(2.7)),
            (Inches(0.4), Inches(4.0), Inches(4.5), Inches(2.7)),
            (Inches(5.1), Inches(4.0), Inches(4.5), Inches(2.7)),
        ]
        for i, (x, y, w, h) in enumerate(positions):
            self._add_rounded_rect(slide, x, y, w, h, self._hex("card_bg"))
            self._add_rect(slide, x, y, w, Inches(0.06), colors[i])
            tb_h = self._add_textbox(slide, x + Inches(0.15), y + Inches(0.12), w - Inches(0.3), Inches(0.3))
            self._set_text(tb_h, labels[i], 12, True, colors[i])
            tb_b = self._add_textbox(slide, x + Inches(0.15), y + Inches(0.5), w - Inches(0.3), h - Inches(0.7))
            self._set_text(tb_b, items[i] if i < len(items) else "", 11, False, self._hex("text"))

    # ==================== WATERFALL ====================
    def _render_waterfall(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = []
        for it in (body_items or [])[:8]:
            if isinstance(it, dict):
                txt = it.get("text", "")
                parts = txt.split(": ", 1) if ": " in txt else (txt, "0")
                try:
                    val = float(parts[1].replace(",","").replace("+","").strip())
                    items.append({"label": parts[0].strip()[:12], "value": val})
                except ValueError:
                    pass
        if not items:
            return
        max_val = max(abs(it["value"]) for it in items) or 1
        bar_w = Inches(1.2)
        gap = Inches(0.6)
        base_y = Inches(4.5)
        start_x = Inches(0.6)
        for i, it in enumerate(items):
            cx = start_x + i * (bar_w + gap)
            bh = int(Inches(2.5) * abs(it["value"]) / max_val)
            cy = base_y - bh if it["value"] >= 0 else base_y
            color = "059669" if it["value"] >= 0 else "DC2626"
            self._add_rounded_rect(slide, cx, cy, bar_w, bh, color)
            tb_v = self._add_textbox(slide, cx, cy - Inches(0.25), bar_w, Inches(0.22))
            self._set_text(tb_v, f'{it["value"]:+.0f}', 10, True, color, align=PP_ALIGN.CENTER)
            tb_l = self._add_textbox(slide, cx, base_y + Inches(0.08), bar_w, Inches(0.22))
            self._set_text(tb_l, it["label"], 10, False, self._hex("text"), align=PP_ALIGN.CENTER)
        self._add_rect(slide, start_x, base_y, Inches(9), Inches(0.008), self._hex("divider"))

    # ==================== GAUGE ====================
    def _render_gauge(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = []
        for it in (body_items or [])[:6]:
            if isinstance(it, dict):
                txt = it.get("text", "")
                m = re.match(r'([^:：]+)[:：]\s*([\d.]+)\s*%?', txt)
                if m:
                    items.append({"label": m.group(1).strip()[:12], "value": min(float(m.group(2)), 100)})
        if not items:
            return
        cols = min(len(items), 3)
        cell_w = Inches(3.2)
        start_x = (self.slide_w - cell_w * cols) / 2
        for i, it in enumerate(items):
            cx = start_x + (i % cols) * cell_w + cell_w / 2
            cy = Inches(2.3) + (i // cols) * Inches(2.5)
            self._add_rounded_rect(slide, cx - Inches(1.3), cy - Inches(1.0), Inches(2.6), Inches(2.0), self._hex("card_bg"))
            pct = it["value"]
            color = "059669" if pct >= 80 else ("D97706" if pct >= 60 else "DC2626")
            tb_v = self._add_textbox(slide, cx - Inches(0.8), cy - Inches(0.3), Inches(1.6), Inches(0.6))
            self._set_text(tb_v, f'{pct:.1f}%', 28, True, color, font="Arial", align=PP_ALIGN.CENTER)
            tb_l = self._add_textbox(slide, cx - Inches(1.1), cy + Inches(0.35), Inches(2.2), Inches(0.4))
            self._set_text(tb_l, it["label"], 12, False, self._hex("text"), align=PP_ALIGN.CENTER)

    # ==================== RANKING ====================
    def _render_ranking(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = []
        max_val = 0
        for it in (body_items or [])[:8]:
            if isinstance(it, dict):
                txt = it.get("text", "")
                parts = txt.split(": ", 1) if ": " in txt else (txt, "")
                name = parts[0].strip()[:20]
                try:
                    val = float(parts[1].replace(",","").strip()) if len(parts) > 1 else 0
                    max_val = max(max_val, val)
                    items.append({"name": name, "value": val})
                except ValueError:
                    items.append({"name": name, "value": 0})
        if not items:
            return
        bar_h = Inches(0.45)
        gap = Inches(0.08)
        start_y = Inches(1.2)
        medals = ["1ST", "2ND", "3RD", "4TH", "5TH", "6TH", "7TH", "8TH"]
        bar_colors = ["F59E0B", "94A3B8", "D97706", "3B82F6", "3B82F6", "3B82F6", "3B82F6", "3B82F6"]
        max_w = Inches(7)
        for i, it in enumerate(items):
            y = start_y + i * (bar_h + gap)
            bw = Inches(1.2) + int(max_w * it["value"] / max(max_val, 1)) if max_val > 0 else Inches(3)
            bc = bar_colors[i]
            self._add_rounded_rect(slide, Inches(1.2), y, bw, bar_h, bc)
            tb_n = self._add_textbox(slide, Inches(0.4), y, Inches(0.7), bar_h)
            self._set_text(tb_n, medals[i], 10, True, bc, font="Arial")
            tb_l = self._add_textbox(slide, Inches(1.4), y + Inches(0.05), Inches(4), bar_h - Inches(0.1))
            self._set_text(tb_l, it["name"], 12, True, self._hex("white"))
            tb_v = self._add_textbox(slide, Inches(1.2) + bw - Inches(1.3), y + Inches(0.05), Inches(1.2), bar_h - Inches(0.1))
            self._set_text(tb_v, f'{it["value"]:,.0f}', 12, True, self._hex("white"), align=PP_ALIGN.RIGHT)

    # ==================== FUNNEL ====================
    def _render_funnel(self, slide, title, subtitle, body_items, tables, code_block):
        self._add_rect(slide, 0, 0, self.slide_w, self.slide_h, self._hex("off_white"))
        self._build_header(slide, title)
        self._build_footer(slide)
        items = []
        max_val = 0
        for it in (body_items or [])[:6]:
            if isinstance(it, dict):
                txt = it.get("text", "")
                parts = txt.split(": ", 1) if ": " in txt else (txt, "")
                try:
                    val = float(parts[1].replace(",","").strip()) if len(parts) > 1 else 0
                    max_val = max(max_val, val)
                    items.append({"label": parts[0].strip()[:20], "value": val})
                except ValueError:
                    pass
        if not items:
            return
        colors = ["3B82F6", "6366F1", "8B5CF6", "A855F7", "C084FC", "D8B4FE"]
        each_h = Inches(0.65)
        gap = Inches(0.06)
        start_y = Inches(1.2)
        max_w = Inches(8)
        for i, it in enumerate(items):
            y = start_y + i * (each_h + gap)
            ratio = it["value"] / max(max_val, 1) if max_val > 0 else 1
            w = int(Inches(1.5) + (max_w - Inches(1.5)) * ratio)
            cx = (self.slide_w - w) / 2
            cc = colors[min(i, len(colors)-1)]
            self._add_rounded_rect(slide, cx, y, w, each_h, cc)
            tb = self._add_textbox(slide, cx + Inches(0.2), y + Inches(0.08), w - Inches(1.5), each_h - Inches(0.16))
            self._set_text(tb, it["label"], 12, True, self._hex("white"))
            tb_v = self._add_textbox(slide, cx + w - Inches(1.3), y + Inches(0.08), Inches(1.1), each_h - Inches(0.16))
            self._set_text(tb_v, f'{it["value"]:,.0f}', 14, True, self._hex("white"), align=PP_ALIGN.RIGHT)
    def generate_from_slide_data(self, slides: list[dict]) -> bytes:
        prs = Presentation()
        prs.slide_width, prs.slide_height = self.slide_w, self.slide_h

        dispatch = {
            "cover": self._render_cover,
            "toc": self._render_toc,
            "chapter": self._render_chapter,
            "content": self._render_content,
            "content_two_col": self._render_two_col,
            "content_table": self._render_table,
            "content_code": self._render_code,
            "content_quote": self._render_quote,
            "content_three_col": self._render_three_col,
            "content_compare": self._render_compare,
            "content_kpi": self._render_kpi_dashboard,
            "content_timeline": self._render_timeline,
            "content_matrix": self._render_matrix,
            "content_waterfall": self._render_waterfall,
            "content_gauge": self._render_gauge,
            "content_ranking": self._render_ranking,
            "content_funnel": self._render_funnel,
            "ending": self._render_ending,
        }

        for sd in slides:
            slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
            lt = sd.get("layout_type", "content")
            renderer = dispatch.get(lt, self._render_content)
            renderer(slide,
                     sd.get("title", ""),
                     sd.get("subtitle", ""),
                     sd.get("body_items", []),
                     sd.get("tables", []),
                     sd.get("code_block", ""))

            notes = sd.get("notes", "")
            if notes:
                ns = slide.notes_slide
                ns.notes_text_frame.text = notes

        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        return buf.read()

    def generate(self, markdown: str, output_path: str, include_notes: bool = True) -> str:
        prs = Presentation()
        prs.slide_width, prs.slide_height = self.slide_w, self.slide_h
        lines = markdown.strip().split("\n")
        current_slide = None
        for line in lines:
            if line.startswith("# "):
                current_slide = prs.slides.add_slide(prs.slide_layouts[6])
                tb = current_slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(9), Inches(1))
                self._set_text(tb, line[2:].strip(), 28, True, self._hex("dark_bg"))
            elif line.startswith("## "):
                current_slide = prs.slides.add_slide(prs.slide_layouts[6])
                tb = current_slide.shapes.add_textbox(Inches(0.5), Inches(1), Inches(9), Inches(1))
                self._set_text(tb, line[3:].strip(), 24, True, self._hex("dark_bg"))
            elif line.strip() and current_slide:
                tb = current_slide.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(4))
                self._set_text(tb, line.strip(), 16, False, self._hex("text"))
        prs.save(output_path)
        return output_path
