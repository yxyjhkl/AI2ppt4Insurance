"""SVG Filler - replaces placeholders in template SVGs with formatted content.

Takes a template SVG + structured slide data and produces a filled SVG
that can be converted to native PPTX shapes via svg_to_pptx.

Rewritten to generate professional card-based layouts, tables, comparisons,
and quote blocks instead of plain text stacking.
"""
from __future__ import annotations
import re
import os
from typing import Optional


class SVGFiller:
    PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")

    def __init__(self, template_dir: str, theme: dict):
        self.template_dir = template_dir
        self.theme = theme
        self.colors = theme.get("colors", {})
        self.fonts = theme.get("fonts", {})
        self.spacing = theme.get("spacing", {
            "margin-x": 48, "margin-y": 30,
            "title-size": 32, "body-size": 18,
            "line-height": 1.6,
        })

    def fill(self, svg_path: str, slide_data: dict, page_num: int) -> str:
        layout = slide_data.get("layout_type", "content")
        title = str(slide_data.get("title", ""))
        subtitle = str(slide_data.get("subtitle", ""))
        body_items = slide_data.get("body_items", []) or []
        tables = slide_data.get("tables", []) or []

        primary = self.colors.get("primary", "#1e40af")
        accent = self.colors.get("accent", "#f59e0b")
        text_color = self.colors.get("text", "#1f2937")
        bg = self.colors.get("background", "#ffffff")
        font_body = self.fonts.get("body", "Microsoft YaHei")

        parts = [self._header_bar(primary, accent, title, subtitle, font_body)]

        if layout in ("cover",):
            parts.append(self._render_cover(title, subtitle, primary, accent, bg))
        elif layout in ("toc", "chapter"):
            parts.append(self._render_toc(title, body_items, primary, text_color, font_body))
        elif layout in ("content_table",) and tables:
            parts.append(self._render_pro_table(tables, primary, accent, text_color, font_body))
        elif layout in ("content_table",) and body_items:
            parts.append(self._render_card_list(body_items, primary, text_color, font_body))
        elif layout in ("content_compare",):
            parts.append(self._render_compare(title, body_items, primary, accent, text_color, font_body))
        elif layout in ("content_two_col",):
            parts.append(self._render_two_col(title, body_items, primary, accent, text_color, font_body))
        elif layout in ("content_three_col",):
            parts.append(self._render_three_col(title, body_items, primary, text_color, font_body))
        elif layout in ("content_kpi",):
            parts.append(self._render_kpi_grid(title, body_items, primary, accent, text_color, font_body))
        elif layout in ("content_quote",):
            parts.append(self._render_quote(title, body_items, primary, text_color, font_body))
        elif layout in ("ending",):
            parts.append(self._render_ending(title, subtitle, primary, accent, bg))
        else:
            parts.append(self._render_card_list(body_items, primary, text_color, font_body))

        parts.append(self._footer_bar(primary, page_num, font_body))

        return "\n".join(parts)

    def _header_bar(self, primary: str, accent: str, title: str, subtitle: str, font_body: str) -> str:
        sub_line = ""
        if subtitle:
            sub_line = (
                f'<text x="24" y="52" font-family="{font_body}" font-size="13" fill="#94a3b8">'
                f'{self._esc(subtitle)}</text>'
            )
        return (
            f'<rect width="1280" height="64" fill="{primary}"/>'
            f'<rect y="0" width="6" height="64" fill="{accent}"/>'
            f'<text x="24" y="38" font-family="{font_body}" font-size="22" font-weight="bold" fill="#ffffff">'
            f'{self._esc(title)}</text>'
            f'{sub_line}'
        )

    def _footer_bar(self, primary: str, page_num: int, font_body: str) -> str:
        return (
            f'<rect y="692" width="1280" height="28" fill="#f0f4ff"/>'
            f'<text x="1256" y="712" text-anchor="end" font-family="{font_body}" font-size="11" fill="#94a3b8">'
            f'{page_num}</text>'
        )

    def _render_cover(self, title: str, subtitle: str, primary: str, accent: str, bg: str) -> str:
        lines = []
        lines.append(f'<rect width="1280" height="720" fill="{bg}"/>')
        lines.append(f'<rect y="0" width="1280" height="280" fill="{primary}" opacity="0.95"/>')
        lines.append(f'<rect y="280" width="1280" height="4" fill="{accent}"/>')
        lines.append(
            f'<text x="80" y="120" font-family="Microsoft YaHei" font-size="44" font-weight="bold" fill="#ffffff">'
            f'{self._esc(title)}</text>'
        )
        if subtitle:
            lines.append(
                f'<text x="80" y="175" font-family="Microsoft YaHei" font-size="20" fill="#cbd5e1">'
                f'{self._esc(subtitle)}</text>'
            )
        lines.append(f'<line x1="80" y1="200" x2="240" y2="200" stroke="{accent}" stroke-width="4"/>')
        lines.append(
            f'<text x="80" y="340" font-family="Microsoft YaHei" font-size="18" fill="#475569">'
            f'数据驱动 · 专业对标 · 持续改善</text>'
        )
        auth = "AI PPT Desktop"
        lines.append(
            f'<text x="80" y="380" font-family="Microsoft YaHei" font-size="14" fill="#94a3b8">'
            f'{self._esc(auth)} — {self._today()}</text>'
        )
        for i in range(3):
            cx, cy = 1020 + i * 60, 360
            colors = [primary, accent, "#94a3b8"]
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="{colors[i]}" opacity="0.3"/>')
        return "\n".join(lines)

    def _render_toc(self, title: str, body_items: list, primary: str, text_color: str, font_body: str) -> str:
        lines = []
        lines.append(
            f'<text x="70" y="110" font-family="{font_body}" font-size="20" font-weight="bold" fill="{primary}">'
            f'{self._esc(title)}</text>'
        )
        lines.append(f'<line x1="70" y1="126" x2="180" y2="126" stroke="{primary}" stroke-width="2"/>')
        y = 160
        idx = 1
        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if not text.strip():
                continue
            lines.append(
                f'<rect x="70" y="{y-6}" width="36" height="28" rx="14" fill="{primary}" opacity="0.12"/>'
            )
            lines.append(
                f'<text x="78" y="{y+14}" font-family="{font_body}" font-size="14" font-weight="bold" fill="{primary}" '
                f'text-anchor="middle">{idx}</text>'
            )
            lines.append(
                f'<text x="120" y="{y+14}" font-family="{font_body}" font-size="17" fill="{text_color}">'
                f'{self._esc(text[:50])}</text>'
            )
            y += 45
            idx += 1
            if idx > 10:
                break
        return "\n".join(lines)

    def _render_pro_table(self, tables: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        md_table = None
        for t in tables:
            if isinstance(t, dict) and t.get("markdown"):
                md_table = t["markdown"]
                break
            elif isinstance(t, str):
                md_table = t
                break
        if not md_table:
            return ""

        headers, rows_data = self._parse_md(md_table)
        num_cols = max(len(headers), 1)
        row_count = min(len(rows_data), 14)

        col_widths = []
        total_w = 1170
        min_w = 80
        for ci in range(num_cols):
            w = total_w // num_cols
            col_widths.append(max(w, min_w))

        x_offsets = [58]
        for w in col_widths[:-1]:
            x_offsets.append(x_offsets[-1] + w)

        header_h = 36
        row_h = 34
        table_y = 90
        lines = []

        lines.append(
            f'<rect x="50" y="{table_y}" width="{sum(col_widths)}" height="{header_h}" rx="4" fill="{primary}"/>'
        )
        for ci, h in enumerate(headers):
            cx = x_offsets[ci] + col_widths[ci] // 2
            lines.append(
                f'<text x="{cx}" y="{table_y + header_h // 2 + 5}" font-family="{font_body}" '
                f'font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">'
                f'{self._esc(h)}</text>'
            )

        for ri, row in enumerate(rows_data):
            ry = table_y + header_h + ri * row_h
            row_bg = "#f8fafc" if ri % 2 == 0 else "#ffffff"
            lines.append(
                f'<rect x="50" y="{ry}" width="{sum(col_widths)}" height="{row_h}" fill="{row_bg}"/>'
            )
            for ci in range(num_cols):
                cell_val = row[ci] if ci < len(row) else ""
                cx = x_offsets[ci] + col_widths[ci] // 2
                cell_color = text_color
                if "🟢" in cell_val:
                    cell_color = "#16a34a"
                elif "🔴" in cell_val:
                    cell_color = "#dc2626"
                elif "🟡" in cell_val:
                    cell_color = "#d97706"
                lines.append(
                    f'<text x="{cx}" y="{ry + row_h // 2 + 5}" font-family="{font_body}" '
                    f'font-size="13" fill="{cell_color}" text-anchor="middle">'
                    f'{self._esc(cell_val)}</text>'
                )
            if ri < len(rows_data) - 1:
                lines.append(
                    f'<line x1="50" y1="{ry + row_h}" x2="{50 + sum(col_widths)}" '
                    f'y2="{ry + row_h}" stroke="#e2e8f0" stroke-width="0.5"/>'
                )

        return "\n".join(lines)

    def _render_card_list(self, body_items: list, primary: str, text_color: str, font_body: str) -> str:
        if not body_items:
            body_items = [{"type": "paragraph", "text": ""}]
        lines = []
        y = 96
        idx = 1

        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            item_type = item.get("type", "list_item") if isinstance(item, dict) else "list_item"
            if not text.strip():
                continue

            card_w = 1170
            lines.append(
                f'<rect x="55" y="{y}" width="{card_w}" height="48" rx="6" fill="#f8fafc" '
                f'stroke="#e2e8f0" stroke-width="1"/>'
            )
            lines.append(
                f'<rect x="55" y="{y}" width="4" height="48" rx="2" fill="{primary}"/>'
            )

            prefix = ""
            if item_type == "list_item":
                prefix = ""
            pil_idx = item.get("level", 0) + 1

            lines.append(
                f'<rect x="70" y="{y+14}" width="22" height="22" rx="11" fill="{primary}" opacity="0.15"/>'
            )
            lines.append(
                f'<text x="81" y="{y+30}" font-family="{font_body}" font-size="12" font-weight="bold" '
                f'fill="{primary}" text-anchor="middle">{idx}</text>'
            )
            lines.append(
                f'<text x="106" y="{y+30}" font-family="{font_body}" font-size="16" fill="{text_color}">'
                f'{self._esc(text[:70])}</text>'
            )
            y += 58
            idx += 1
            if y > 660:
                break

        return "\n".join(lines)

    def _render_compare(self, title: str, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        left_items = []
        right_items = []
        for item in body_items:
            col = item.get("column", "left") if isinstance(item, dict) else "left"
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if col == "right":
                right_items.append(text)
            else:
                left_items.append(text)

        lines = []
        y = 96
        left_title = "当前状态"
        right_title = "目标 / 对比"
        if title and " vs " in title:
            parts = title.split(" vs ", 1)
            left_title, right_title = parts[0], parts[1]

        left_color = self.colors.get("secondary", "#dc2626")
        right_color = self.colors.get("success", "#16a34a")

        lines.append(f'<line x1="640" y1="85" x2="640" y2="680" stroke="#e2e8f0" stroke-width="1"/>')

        lines.append(
            f'<rect x="55" y="{y}" width="560" height="32" rx="4" fill="{left_color}" opacity="0.1"/>'
        )
        lines.append(
            f'<text x="70" y="{y+22}" font-family="{font_body}" font-size="15" font-weight="bold" '
            f'fill="{left_color}">{self._esc(left_title)}</text>'
        )
        y += 42
        for i, text in enumerate(left_items[:7]):
            if not text.strip():
                continue
            lines.append(
                f'<rect x="55" y="{y}" width="560" height="36" rx="4" fill="#fef2f2"/>'
            )
            lines.append(f'<rect x="55" y="{y}" width="3" height="36" rx="2" fill="{left_color}"/>')
            lines.append(
                f'<text x="72" y="{y+24}" font-family="{font_body}" font-size="14" fill="{text_color}">'
                f'{self._esc(text[:60])}</text>'
            )
            y += 46

        y = 138
        lines.append(
            f'<rect x="665" y="{y}" width="560" height="32" rx="4" fill="{right_color}" opacity="0.1"/>'
        )
        lines.append(
            f'<text x="680" y="{y+22}" font-family="{font_body}" font-size="15" font-weight="bold" '
            f'fill="{right_color}">{self._esc(right_title)}</text>'
        )
        y += 42
        for i, text in enumerate(right_items[:7]):
            if not text.strip():
                continue
            lines.append(
                f'<rect x="665" y="{y}" width="560" height="36" rx="4" fill="#f0fdf4"/>'
            )
            lines.append(f'<rect x="665" y="{y}" width="3" height="36" rx="2" fill="{right_color}"/>')
            lines.append(
                f'<text x="682" y="{y+24}" font-family="{font_body}" font-size="14" fill="{text_color}">'
                f'{self._esc(text[:60])}</text>'
            )
            y += 46

        return "\n".join(lines)

    def _render_two_col(self, title: str, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        left_items = []
        right_items = []
        for item in body_items:
            col = item.get("column", "left") if isinstance(item, dict) else "left"
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if col == "right":
                right_items.append(text)
            else:
                left_items.append(text)

        lines = []
        lines.append(f'<line x1="640" y1="85" x2="640" y2="680" stroke="#e2e8f0" stroke-width="1"/>')

        y = 96
        lines.append(
            f'<text x="70" y="{y}" font-family="{font_body}" font-size="16" font-weight="bold" '
            f'fill="{primary}">▎左列</text>'
        )
        y += 30
        for i, text in enumerate(left_items[:8]):
            if not text.strip():
                continue
            lines.append(
                f'<rect x="55" y="{y}" width="560" height="34" rx="4" fill="#f8fafc"/>'
            )
            lines.append(f'<rect x="55" y="{y}" width="3" height="34" rx="2" fill="{accent}"/>')
            lines.append(
                f'<text x="72" y="{y+23}" font-family="{font_body}" font-size="14" fill="{text_color}">'
                f'{self._esc(text[:60])}</text>'
            )
            y += 42

        y = 96
        lines.append(
            f'<text x="680" y="{y}" font-family="{font_body}" font-size="16" font-weight="bold" '
            f'fill="{primary}">▎右列</text>'
        )
        y += 30
        for i, text in enumerate(right_items[:8]):
            if not text.strip():
                continue
            lines.append(
                f'<rect x="665" y="{y}" width="560" height="34" rx="4" fill="#f8fafc"/>'
            )
            lines.append(f'<rect x="665" y="{y}" width="3" height="34" rx="2" fill="{accent}"/>')
            lines.append(
                f'<text x="682" y="{y+23}" font-family="{font_body}" font-size="14" fill="{text_color}">'
                f'{self._esc(text[:60])}</text>'
            )
            y += 42

        return "\n".join(lines)

    def _render_three_col(self, title: str, body_items: list, primary: str, text_color: str, font_body: str) -> str:
        cols = [[], [], []]
        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            col = item.get("column", "left") if isinstance(item, dict) else "left"
            if col == "center":
                cols[1].append(text)
            elif col == "right":
                cols[2].append(text)
            else:
                cols[0].append(text)

        lines = []
        col_x = [55, 465, 875]
        col_w = 380
        colors = [self.colors.get("primary", "#1e40af"), self.colors.get("accent", "#f59e0b"), self.colors.get("secondary", "#dc2626")]
        labels = ["列一", "列二", "列三"]

        for ci in range(3):
            cx, cw = col_x[ci], col_w
            lines.append(f'<rect x="{cx}" y="90" width="{cw}" height="28" rx="4" fill="{colors[ci]}" opacity="0.12"/>')
            lines.append(
                f'<text x="{cx+12}" y="110" font-family="{font_body}" font-size="14" font-weight="bold" '
                f'fill="{colors[ci]}">{labels[ci]}</text>'
            )
            y = 130
            for text in cols[ci][:8]:
                if not text.strip():
                    continue
                lines.append(f'<rect x="{cx}" y="{y}" width="{cw}" height="32" rx="4" fill="#f8fafc"/>')
                lines.append(f'<rect x="{cx}" y="{y}" width="3" height="32" rx="2" fill="{colors[ci]}"/>')
                lines.append(
                    f'<text x="{cx+16}" y="{y+22}" font-family="{font_body}" font-size="13" fill="{text_color}">'
                    f'{self._esc(text[:50])}</text>'
                )
                y += 40
            if ci < 2:
                lines.append(f'<line x1="{cx+cw+10}" y1="85" x2="{cx+cw+10}" y2="680" stroke="#e2e8f0" stroke-width="1"/>')

        return "\n".join(lines)

    def _render_quote(self, title: str, body_items: list, primary: str, text_color: str, font_body: str) -> str:
        quote_text = ""
        quote_author = ""
        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if text.startswith("—") or text.startswith("--"):
                quote_author = text.lstrip("—").lstrip("-").strip()
            elif not quote_text:
                quote_text = text

        lines = []
        y_center = 360
        lines.append(
            f'<rect x="120" y="{y_center-120}" width="1040" height="240" rx="12" fill="#f8fafc" '
            f'stroke="{primary}" stroke-width="1" opacity="0.3"/>'
        )
        lines.append(f'<rect x="120" y="{y_center-120}" width="6" height="240" rx="3" fill="{primary}"/>')
        lines.append(
            f'<text x="64" y="{y_center-20}" font-family="Georgia, serif" font-size="72" fill="{primary}" '
            f'opacity="0.2">"</text>'
        )
        lines.append(
            f'<text x="180" y="{y_center-10}" font-family="{font_body}" font-size="20" fill="{text_color}" '
            f'font-style="italic">{self._esc(quote_text[:100])}</text>'
        )
        if quote_author:
            lines.append(
                f'<text x="180" y="{y_center+50}" font-family="{font_body}" font-size="15" fill="#64748b">'
                f'— {self._esc(quote_author)}</text>'
            )
        return "\n".join(lines)

    def _render_kpi_grid(self, title: str, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        import re as _re
        if not body_items:
            return ""
        kpis = []
        for item in body_items:
            txt = item.get("text", "") if isinstance(item, dict) else str(item)
            m = _re.match(r'^([^0-9:：]+)[:：]?\s*(.*)', txt)
            if m:
                lbl = m.group(1).strip()
                vp = m.group(2).strip()
                nm = _re.search(r'([\d,.]+)\s*(%|万|亿|元|人|个)?', vp)
                if nm:
                    kpis.append({"label": lbl, "value": nm.group(1), "unit": nm.group(2) or ""})

        if not kpis:
            return self._render_card_list(body_items, primary, text_color, font_body)

        cols = min(len(kpis), 4)
        card_w = 275
        card_h = 185
        gap_x = 25
        gap_y = 18
        total_w = card_w * cols + gap_x * (cols - 1)
        start_x = (1280 - total_w) // 2

        lines = []
        card_colors = [primary, accent, "#6366f1", "#0891b2", "#059669", "#7c3aed", "#dc2626", "#d97706"]

        for idx, kpi in enumerate(kpis):
            row = idx // cols
            col = idx % cols
            cx = start_x + col * (card_w + gap_x)
            cy = 95 + row * (card_h + gap_y)
            cc = card_colors[idx % len(card_colors)]

            lines.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" rx="8" fill="#ffffff" stroke="#e5e7eb" stroke-width="1"/>')
            lines.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="6" rx="3" fill="{cc}"/>')
            lines.append(f'<text x="{cx+14}" y="{cy+28}" font-family="{font_body}" font-size="11" fill="#64748b">{self._esc(kpi["label"])}</text>')

            val_size = "32" if len(kpi["value"]) <= 4 else "24"
            if kpi["unit"] == "%":
                try:
                    pct = float(kpi["value"].replace(",", ""))
                    bar_color = "#059669" if pct >= 80 else ("#d97706" if pct >= 60 else "#dc2626")
                    lines.append(f'<text x="{cx+14}" y="{cy+70}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{bar_color}">{self._esc(kpi["value"])}%</text>')
                    bar_y = cy + 120
                    bar_w = card_w - 28
                    lines.append(f'<rect x="{cx+14}" y="{bar_y}" width="{bar_w}" height="8" rx="4" fill="#e5e7eb"/>')
                    fill_w = int(bar_w * min(pct / 100, 1.0))
                    if fill_w > 0:
                        lines.append(f'<rect x="{cx+14}" y="{bar_y}" width="{fill_w}" height="8" rx="4" fill="{bar_color}"/>')
                except (ValueError, TypeError):
                    lines.append(f'<text x="{cx+14}" y="{cy+70}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{cc}">{self._esc(kpi["value"])}%</text>')
            else:
                lines.append(f'<text x="{cx+14}" y="{cy+70}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{cc}">{self._esc(kpi["value"])}</text>')
                if kpi["unit"]:
                    lines.append(f'<text x="{cx+14}" y="{cy+120}" font-family="{font_body}" font-size="12" fill="#64748b">{self._esc(kpi["unit"])}</text>')

        return "\n".join(lines)

    def _render_ending(self, title: str, subtitle: str, primary: str, accent: str, bg: str) -> str:
        lines = []
        y_center = 360
        lines.append(f'<rect width="1280" height="720" fill="{bg}"/>')
        lines.append(f'<rect y="{y_center-120}" width="1280" height="240" fill="{primary}" opacity="0.05"/>')
        lines.append(f'<line x1="480" y1="{y_center-60}" x2="800" y2="{y_center-60}" stroke="{accent}" stroke-width="2"/>')
        lines.append(
            f'<text x="640" y="{y_center-30}" font-family="Microsoft YaHei" font-size="36" font-weight="bold" '
            f'fill="{primary}" text-anchor="middle">{self._esc(title or "Thank You")}</text>'
        )
        if subtitle:
            lines.append(
                f'<text x="640" y="{y_center+30}" font-family="Microsoft YaHei" font-size="18" fill="#64748b" '
                f'text-anchor="middle">{self._esc(subtitle)}</text>'
            )
        lines.append(
            f'<text x="640" y="{y_center+90}" font-family="Microsoft YaHei" font-size="14" fill="#94a3b8" '
            f'text-anchor="middle">数据驱动决策 · 持续改善追踪</text>'
        )
        return "\n".join(lines)

    def _replace_basic(self, svg: str, slide: dict, page_num: int) -> str:
        title = str(slide.get("title", ""))
        subtitle = str(slide.get("subtitle", ""))

        replacements = {
            "TITLE": title or "Presentation Title",
            "SUBTITLE": subtitle or "",
            "AUTHOR": "AI PPT Desktop",
            "DATE": self._today(),
            "COMPANY": "",
            "PAGE_TITLE": title or "Slide",
            "PAGE_NUM": str(page_num),
            "SECTION_NAME": "",
            "SECTION_NUM": str(page_num),
            "CHAPTER_NUM": str(page_num),
            "CHAPTER_TITLE": title or "",
            "CHAPTER_DESC": subtitle or "",
            "THANK_YOU": "Thank You",
            "ENDING_SUBTITLE": "Questions & Discussion",
            "CONTACT_INFO": "",
            "EMAIL": "",
            "COPYRIGHT": "Generated by AI PPT Desktop",
            "LOGO": "",
            "KEY_MESSAGE": "",
            "SOURCE": "",
        }
        for key, val in replacements.items():
            svg = svg.replace("{{" + key + "}}", self._esc(val))
        return svg

    def _replace_content_area(self, svg: str, slide: dict) -> str:
        return svg

    def _parse_md(self, md: str):
        rows = [r.strip() for r in md.strip().split("\n") if r.strip() and not r.startswith("|--")]
        if not rows:
            return ["列1", "列2"], []
        headers = [c.strip() for c in rows[0].split("|") if c.strip()]
        data = []
        for row in rows[1:]:
            data.append([c.strip() for c in row.split("|") if c.strip()])
        return headers, data

    def _render_body(self, items: list[dict]) -> str:
        return ""

    def _render_side_content(self, slide: dict) -> str:
        return ""

    def _render_table(self, slide: dict) -> str:
        return ""

    def _word_wrap(self, text: str, max_width_px: int, font_size: int) -> list[str]:
        avg_char_width = font_size * 0.65
        max_chars = max(1, int(max_width_px / avg_char_width))
        lines = []
        for paragraph in text.split("\n"):
            while len(paragraph) > max_chars:
                break_idx = paragraph.rfind(" ", 0, max_chars)
                if break_idx == -1:
                    break_idx = max_chars
                lines.append(paragraph[:break_idx])
                paragraph = paragraph[break_idx:].strip()
            lines.append(paragraph)
        return lines

    def _esc(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        return text

    def _escape_xml(self, text: str) -> str:
        return self._esc(text)

    def _today(self) -> str:
        from datetime import date
        return date.today().strftime("%Y-%m-%d")

    def _fallback_svg(self, slide: dict) -> str:
        title = str(slide.get("title", "Slide"))
        body = "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in (slide.get("body_items") or [])
        )
        primary = self.colors.get("primary", "#1e40af")
        text_color = self.colors.get("text", "#1f2937")
        font_body = self.fonts.get("body", "Microsoft YaHei")
        return (
            f'<rect width="1280" height="64" fill="{primary}"/>'
            f'<text x="24" y="38" font-family="{font_body}" font-size="22" font-weight="bold" fill="#ffffff">{self._esc(title)}</text>'
            f'<text x="70" y="130" font-family="{font_body}" font-size="18" fill="{text_color}">{self._esc(body)}</text>'
        )

    @staticmethod
    def generate_output_svg(slide: dict, page_num: int, svg_content: str) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">\n'
            + svg_content + '\n'
            '</svg>'
        )