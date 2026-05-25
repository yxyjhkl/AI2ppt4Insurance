"""SVG填充器 —— 将结构化幻灯片数据渲染为矢量图形

设计决策：为什么用SVG而不是直接构建PPTX？
  - SVG是纯文本格式，LLM/AI可以理解和生成
  - SVG可在浏览器预览，无需解析PPTX二进制
  - 支持后续通过svg_to_pptx转为原生PPTX形状
  - 模板化：每个layout_type对应一个_render_*方法，生成专业卡片式布局

渲染管线：SlideData → fill() → 17种布局路由 → 返回SVG片段
  封面(cover) → 章节(chapter) → 目录(toc) → 内容(content) → 
  表格(content_table) → 双栏(two_col) → 三栏(three_col) → 对比(compare) →
  代码(content_code) → KPI(content_kpi) → 引用(quote) → 结尾(ending) →
  矩阵(matrix) → 时间轴(timeline) → 瀑布(waterfall) → 
  仪表盘(gauge) → 排行榜(ranking) → 漏斗(funnel)
"""
from __future__ import annotations
import re
import os
from typing import Optional
from utils.json_utils import CANVAS_VIEWBOX


class SVGFiller:
    PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")

    def _wrap_text(self, text: str, font_size: int, max_width: int, font_family: str = "Microsoft YaHei") -> list:
        """将文本自动换行，返回行列表"""
        if not text:
            return [""]

        lines = []
        current_line = ""
        current_width = 0.0

        for char in text:
            # 中文字符约 font_size*0.8 宽，英文约 font_size*0.5
            char_width = font_size * 0.8 if ord(char) > 127 else font_size * 0.5

            if current_width + char_width > max_width and current_line:
                lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width

        if current_line:
            lines.append(current_line)

        return lines if lines else [""]

    def _calculate_text_height(self, text: str, font_size: int, max_width: int, line_height: float = 1.4) -> int:
        """计算文本换行后的总高度"""
        lines = self._wrap_text(text, font_size, max_width)
        return int(len(lines) * font_size * line_height)

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
        # 读取 visual_rules 以实际控制渲染风格
        self.visual_rules = theme.get("visual_rules", {})
        self._apply_visual_rules()

    def _apply_visual_rules(self):
        """应用 visual_rules 中的配置到渲染参数"""
        vr = self.visual_rules

        # 标题和正文字号
        self.title_size = vr.get("title_size", self.spacing.get("title-size", 32))
        self.subtitle_size = vr.get("subtitle_size", self.spacing.get("subtitle-size", 20))
        self.body_size = vr.get("body_size", self.spacing.get("body-size", 18))
        self.caption_size = vr.get("caption_size", 12)

        # 边距设置
        margin = vr.get("margin", {})
        self.margin_top = margin.get("top", 50)
        self.margin_bottom = margin.get("bottom", 40)
        self.margin_left = margin.get("left", 50)
        self.margin_right = margin.get("right", 50)

        # 行间距
        self.line_spacing = vr.get("line_spacing", 1.5)

        # 样式设置
        self.corner_radius = vr.get("corner_radius", 4)
        self.shadow_enabled = vr.get("shadow_enabled", True)
        self.gradient_bg = vr.get("gradient_bg", False)
        self.section_divider = vr.get("section_divider", True)
        self.page_number_enabled = vr.get("page_number", True)
        self.header_enabled = vr.get("header_enabled", True)

        # 元素设置
        elements = self.theme.get("elements", {})
        self.bullet_style = elements.get("bullet_style", "disc")
        self.table_stripe = elements.get("table_stripe", True)
        self.chart_colors = elements.get("chart_colors", ["#1e40af", "#3b82f6", "#60a5fa"])
        self.progress_bar = elements.get("progress_bar", True)
        self.kpi_card_style = elements.get("kpi_card_style", "rounded")

        # 动画设置
        animation = self.theme.get("animation", {})
        self.animation_type = animation.get("type", "none")
        self.title_animation = animation.get("title_animation", "fade_in")

    # ---- 布局分发: 根据layout_type路由到专属渲染方法 ----
    def fill(self, svg_path: str, slide_data: dict, page_num: int) -> str:
        layout = slide_data.get("layout_type", "content")
        title = str(slide_data.get("title", ""))
        subtitle = str(slide_data.get("subtitle", ""))
        body_items = slide_data.get("body_items", []) or []
        tables = slide_data.get("tables", []) or []
        code_block = str(slide_data.get("code_block") or "")

        primary = self.colors.get("primary", "#1e40af")
        accent = self.colors.get("accent", "#f59e0b")
        text_color = self.colors.get("text", "#1f2937")
        bg = self.colors.get("background", "#ffffff")
        font_body = self.fonts.get("body", "Microsoft YaHei")

        # 使用 visual_rules 中的配置
        title_size = self.title_size
        subtitle_size = self.subtitle_size
        body_size = self.body_size

        # 根据视觉规则构建页眉
        if self.header_enabled:
            parts = [self._header_bar(primary, accent, title, subtitle, font_body, title_size)]
        else:
            parts = []

        if layout in ("cover",):
            parts.append(self._render_cover(title, subtitle, primary, accent, bg))
        elif layout in ("toc",):
            parts.append(self._render_toc(title, body_items, primary, text_color, font_body, body_size))
        elif layout in ("chapter",):
            parts.append(self._render_chapter_svg(title, primary, accent, font_body))
        elif layout in ("content_table",) and tables:
            parts.append(self._render_pro_table(tables, primary, accent, text_color, font_body))
        elif layout in ("content_table",) and body_items:
            parts.append(self._render_card_list(body_items, primary, text_color, font_body, body_size))
        elif layout in ("content_compare",):
            parts.append(self._render_compare(title, body_items, primary, accent, text_color, font_body, body_size))
        elif layout in ("content_two_col",):
            parts.append(self._render_two_col(title, body_items, primary, accent, text_color, font_body, body_size))
        elif layout in ("content_three_col",):
            parts.append(self._render_three_col(title, body_items, primary, text_color, font_body, body_size))
        elif layout in ("content_kpi",):
            parts.append(self._render_kpi_grid(title, body_items, primary, accent, text_color, font_body))
        elif layout in ("content_quote",):
            parts.append(self._render_quote(title, body_items, primary, text_color, font_body))
        elif layout in ("ending",):
            parts.append(self._render_ending(title, subtitle, primary, accent, bg))
        elif layout in ("content_code",):
            parts.append(self._render_code(body_items, code_block, primary, text_color, font_body, body_size))
        elif layout in ("content_matrix",):
            parts.append(self._render_matrix(body_items, primary, text_color, font_body, body_size))
        elif layout in ("content_timeline",):
            parts.append(self._render_timeline(body_items, primary, accent, text_color, font_body, body_size))
        elif layout in ("content_waterfall",):
            parts.append(self._render_waterfall(body_items, primary, accent, text_color, font_body))
        elif layout in ("content_gauge",):
            parts.append(self._render_gauge(body_items, primary, accent, text_color, font_body))
        elif layout in ("content_ranking",):
            parts.append(self._render_ranking(body_items, primary, accent, text_color, font_body))
        elif layout in ("content_funnel",):
            parts.append(self._render_funnel(body_items, primary, accent, text_color, font_body))
        else:
            parts.append(self._render_card_list(body_items, primary, text_color, font_body, body_size))

        if self.page_number_enabled:
            parts.append(self._footer_bar(primary, page_num, font_body))

        return "\n".join(parts)

    def _header_bar(self, primary: str, accent: str, title: str, subtitle: str, font_body: str, title_size: int = 22) -> str:
        sub_line = ""
        if subtitle:
            sub_line = (
                f'<text x="640" y="54" font-family="{font_body}" font-size="12" fill="#94a3b8" text-anchor="middle">'
                f'{self._esc(subtitle)}</text>'
            )
        header_height = 64
        title_y = 38
        if self.title_size and self.title_size > 32:
            header_height = 72
            title_y = 42
        return (
            f'<defs><linearGradient id="hdrGrad" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0%" stop-color="{primary}"/><stop offset="100%" stop-color="{primary}" stop-opacity="0.85"/>'
            f'</linearGradient></defs>'
            f'<rect width="1280" height="{header_height}" fill="url(#hdrGrad)"/>'
            f'<rect y="0" width="8" height="{header_height}" fill="{accent}"/>'
            f'<rect y="{header_height - 3}" width="1280" height="3" fill="{accent}" opacity="0.3"/>'
            f'<text x="640" y="{title_y}" font-family="{font_body}" font-size="{title_size}" font-weight="bold" fill="#ffffff" text-anchor="middle">'
            f'{self._esc(title)}</text>'
            f'{sub_line}'
        )

    def _footer_bar(self, primary: str, page_num: int, font_body: str) -> str:
        return (
            f'<rect y="692" width="1280" height="28" fill="#f0f4ff"/>'
            f'<text x="640" y="712" text-anchor="middle" font-family="{font_body}" font-size="11" fill="#94a3b8">'
            f'{page_num}</text>'
        )

    def _render_cover(self, title: str, subtitle: str, primary: str, accent: str, bg: str) -> str:
        lines = []
        # 渐变背景
        lines.append(f'<defs>')
        lines.append(f'<linearGradient id="coverGrad" x1="0" y1="0" x2="1" y2="1">')
        lines.append(f'<stop offset="0%" stop-color="{primary}" stop-opacity="0.95"/>')
        lines.append(f'<stop offset="100%" stop-color="{primary}" stop-opacity="0.75"/>')
        lines.append(f'</linearGradient>')
        lines.append(f'<linearGradient id="coverShine" x1="0" y1="0" x2="0.3" y2="1">')
        lines.append(f'<stop offset="0%" stop-color="#ffffff" stop-opacity="0.08"/>')
        lines.append(f'<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>')
        lines.append(f'</linearGradient>')
        lines.append(f'</defs>')
        lines.append(f'<rect width="1280" height="720" fill="url(#coverGrad)"/>')
        lines.append(f'<rect width="1280" height="720" fill="url(#coverShine)"/>')

        # 左侧装饰竖条
        lines.append(f'<rect x="0" y="0" width="10" height="720" fill="{accent}"/>')
        # 顶部装饰线
        lines.append(f'<rect x="0" y="0" width="1280" height="5" fill="{accent}" opacity="0.6"/>')

        # 几何装饰 - 右下角大圆
        lines.append(f'<circle cx="1150" cy="650" r="300" fill="{accent}" opacity="0.08"/>')
        lines.append(f'<circle cx="1180" cy="680" r="180" fill="{accent}" opacity="0.06"/>')

        # 左上角装饰元素组
        for i in range(3):
            cx = 1100 - i * 80
            cy = 100 + i * 70
            r = 18 - i * 4
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{accent}" opacity="{0.35 - i * 0.1}"/>')

        # 主标题区域
        lines.append(f'<rect x="72" y="180" width="8" height="80" rx="4" fill="{accent}"/>')
        lines.append(
            f'<text x="100" y="210" font-family="Microsoft YaHei" font-size="54" font-weight="bold" fill="#ffffff" letter-spacing="2">'
            f'{self._esc(title)}</text>'
        )
        # 标题下划线
        lines.append(f'<rect x="100" y="248" width="260" height="5" rx="2.5" fill="{accent}"/>')

        if subtitle:
            lines.append(
                f'<text x="100" y="310" font-family="Microsoft YaHei" font-size="24" fill="#cbd5e1" letter-spacing="1">'
                f'{self._esc(subtitle)}</text>'
            )

        # 底部装饰条
        lines.append(f'<rect x="0" y="715" width="1280" height="5" fill="{accent}" opacity="0.4"/>')
        return "\n".join(lines)

    def _render_toc(self, title: str, body_items: list, primary: str, text_color: str, font_body: str, body_size: int = 17) -> str:
        accent = self.colors.get("accent", primary)
        lines = []
        lines.append(
            f'<text x="640" y="100" font-family="{font_body}" font-size="22" font-weight="bold" '
            f'fill="{primary}" text-anchor="middle">{self._esc(title)}</text>'
        )
        lines.append(f'<line x1="540" y1="118" x2="740" y2="118" stroke="{accent}" stroke-width="3"/>')
        card_colors = [accent, primary, "#6366f1", "#0891b2", "#7c3aed", "#059669", "#dc2626", "#d97706"]
        n = len([it for it in body_items if (it.get("text", "") if isinstance(it, dict) else str(it)).strip()])
        n = max(n, 1)
        item_h = min(50, int(480 / n))
        y = 145

        for idx, item in enumerate(body_items):
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if not text.strip():
                continue
            cc = card_colors[idx % len(card_colors)]
            main_text = text
            desc_text = ""
            if " — " in text:
                parts = text.split(" — ", 1)
                main_text = parts[0].strip()
                desc_text = parts[1].strip()[:50]

            num_text = ""
            if len(main_text) >= 2 and main_text[:2].isdigit():
                num_text = main_text[:2]
                main_text = main_text[3:].strip()

            lines.append(f'<rect x="80" y="{y-4}" width="1120" height="{item_h}" rx="8" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>')
            lines.append(f'<rect x="80" y="{y-4}" width="5" height="{item_h}" rx="2" fill="{cc}"/>')

            if num_text:
                lines.append(f'<text x="125" y="{y + item_h//2 + 5}" font-family="Arial" font-size="20" font-weight="bold" fill="{cc}" text-anchor="middle">{num_text}</text>')
                tx = 170
            else:
                tx = 120
                lines.append(f'<text x="125" y="{y + item_h//2 + 5}" font-family="{font_body}" font-size="16" font-weight="bold" fill="{cc}" text-anchor="middle">{idx+1}</text>')

            lines.append(f'<text x="{tx}" y="{y + item_h//2 + 6}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(main_text[:40])}</text>')
            if desc_text:
                lines.append(f'<text x="{tx}" y="{y + item_h//2 + 26}" font-family="{font_body}" font-size="12" fill="#94a3b8">{self._esc(desc_text)}</text>')
            y += item_h + 8
            if y > 650:
                break
        return "\n".join(lines)

    def _render_chapter_svg(self, title: str, primary: str, accent: str, font_body: str) -> str:
        lines = []
        # 渐变背景
        lines.append(f'<defs>')
        lines.append(f'<linearGradient id="chGrad" x1="0" y1="0" x2="1" y2="1">')
        lines.append(f'<stop offset="0%" stop-color="{primary}" stop-opacity="0.95"/>')
        lines.append(f'<stop offset="100%" stop-color="{primary}" stop-opacity="0.7"/>')
        lines.append(f'</linearGradient>')
        lines.append(f'</defs>')
        lines.append(f'<rect width="1280" height="720" fill="url(#chGrad)"/>')

        # 顶部+底部装饰线
        lines.append(f'<rect y="0" width="1280" height="4" fill="{accent}"/>')
        lines.append(f'<rect y="716" width="1280" height="4" fill="{accent}"/>')

        # 左侧大装饰条
        lines.append(f'<rect x="0" y="0" width="12" height="720" fill="{accent}" opacity="0.6"/>')

        # 背景几何装饰
        lines.append(f'<circle cx="1100" cy="600" r="250" fill="{accent}" opacity="0.04"/>')
        lines.append(f'<circle cx="1150" cy="300" r="120" fill="{accent}" opacity="0.03"/>')

        num_match = re.match(r'^(\d{2})\s+', title or "")
        section_num = num_match.group(1) if num_match else ""
        section_title = title[num_match.end():].strip() if num_match else title

        if section_num:
            # 大号数字 — 上方
            lines.append(f'<text x="80" y="280" font-family="Arial Black" font-size="160" font-weight="bold" fill="{accent}" opacity="0.25">{section_num}</text>')
            # 分割线
            lines.append(f'<rect x="100" y="340" width="4" height="60" rx="2" fill="{accent}"/>')
            # 标题 — 下方
            lines.append(f'<text x="130" y="385" font-family="{font_body}" font-size="48" font-weight="bold" fill="#ffffff">{self._esc(section_title or title)}</text>')
        else:
            lines.append(f'<rect x="80" y="340" width="8" height="80" rx="4" fill="{accent}"/>')
            lines.append(f'<text x="110" y="395" font-family="{font_body}" font-size="48" font-weight="bold" fill="#ffffff">{self._esc(title)}</text>')
            lines.append(f'<rect x="110" y="420" width="180" height="4" rx="2" fill="{accent}"/>')

        # 右下角装饰
        for cx in [1050, 1150]:
            lines.append(f'<rect x="{cx}" y="40" width="50" height="3" rx="1.5" fill="{accent}" opacity="0.5"/>')

        return "\n".join(lines)

    def _render_pro_table(self, tables: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        md_table = None
        for t in tables:
            if isinstance(t, dict) and t.get("markdown"):
                md_table = t.get("markdown")
                break
            elif isinstance(t, str):
                md_table = t
                break
        if not md_table:
            return ""

        headers, rows_data = self._parse_md(md_table)
        num_cols = max(len(headers), 1)
        row_count = min(len(rows_data), 22)  # 显示更多行

        col_widths = []
        total_w = 1180
        min_w = 70
        for ci in range(num_cols):
            w = total_w // num_cols
            col_widths.append(max(w, min_w))

        x_offsets = [50]
        for w in col_widths[:-1]:
            x_offsets.append(x_offsets[-1] + w)

        header_h = 48
        row_h = 38
        table_total_h = header_h + row_h * min(len(rows_data), 22)
        available_h = 600 if self.header_enabled else 660
        table_y = 75 + (available_h - table_total_h) // 2
        if table_y < 20:
            table_y = 20
        lines = []

        lines.append(
            f'<rect x="50" y="{table_y}" width="{sum(col_widths)}" height="{header_h}" rx="6" fill="{primary}"/>'
        )
        # 表头底部阴影效果
        lines.append(
            f'<rect x="50" y="{table_y + header_h - 3}" width="{sum(col_widths)}" height="3" fill="{primary}" opacity="0.2"/>'
        )
        for ci, h in enumerate(headers):
            cx = x_offsets[ci] + col_widths[ci] // 2
            lines.append(
                f'<text x="{cx}" y="{table_y + header_h // 2 + 6}" font-family="{font_body}" '
                f'font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">'
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
                    f'<text x="{cx}" y="{ry + row_h // 2 + 6}" font-family="{font_body}" '
                    f'font-size="14" fill="{cell_color}" text-anchor="middle">'
                    f'{self._esc(cell_val)}</text>'
                )
            if ri < len(rows_data) - 1:
                lines.append(
                    f'<line x1="50" y1="{ry + row_h}" x2="{50 + sum(col_widths)}" '
                    f'y2="{ry + row_h}" stroke="#e2e8f0" stroke-width="1"/>'
                )

        return "\n".join(lines)

    def _render_card_list(self, body_items: list, primary: str, text_color: str, font_body: str, body_size: int = 18) -> str:
        if not body_items:
            body_items = [{"type": "paragraph", "text": ""}]
        lines = []
        bg_top = 75 if self.header_enabled else 20
        accent = self.colors.get("accent", primary)

        n = max(1, len(body_items))
        base_card_h = 52
        gap = 10
        max_text_width = 1040
        y = bg_top + 10

        card_colors = [primary, accent, "#6366f1", "#0891b2", "#7c3aed", "#059669", "#dc2626", "#d97706"]

        idx = 1
        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if not text.strip():
                continue
            text_size = min(body_size, 15)
            wrapped_lines = self._wrap_text(text, text_size, max_text_width)
            line_count = len(wrapped_lines)
            card_h = max(base_card_h, line_count * int(text_size * 1.5) + 20)
            cc = card_colors[(idx - 1) % len(card_colors)]

            lines.append(
                f'<rect x="40" y="{y}" width="1200" height="{card_h}" rx="10" fill="#ffffff" '
                f'stroke="#e5e7eb" stroke-width="1"/>'
            )
            # 投影效果
            lines.append(f'<rect x="42" y="{y + 2}" width="1200" height="{card_h}" rx="10" fill="#000000" opacity="0.04"/>')
            lines.append(f'<rect x="40" y="{y}" width="8" height="{card_h}" rx="4" fill="{cc}"/>')

            circle_r = 16
            cy = y + card_h // 2
            lines.append(f'<circle cx="85" cy="{cy}" r="{circle_r}" fill="{cc}"/>')
            lines.append(
                f'<text x="85" y="{cy + 5}" font-family="{font_body}" font-size="12" '
                f'font-weight="bold" fill="#ffffff" text-anchor="middle">{idx}</text>'
            )

            text_x = 120
            text_start_y = cy - (line_count - 1) * text_size * 0.7
            text_elements = []
            for i, line_text in enumerate(wrapped_lines):
                dy = i * int(text_size * 1.5)
                text_elements.append(
                    f'<tspan x="{text_x}" dy="{dy if i == 0 else int(text_size * 1.5)}" '
                    f'font-family="{font_body}" font-size="{text_size}" fill="{text_color}">'
                    f'{self._esc(line_text)}</tspan>'
                )
            lines.append(f'<text x="{text_x}" y="{text_start_y}">{"".join(text_elements)}</text>')
            y += card_h + gap
            idx += 1
            if y > bg_top + 580:
                break
        return "\n".join(lines)

    def _render_compare(self, title: str, body_items: list, primary: str, accent: str, text_color: str, font_body: str, body_size: int = 16) -> str:
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
        left_count = len([it for it in body_items if (it.get("column", "left") if isinstance(it, dict) else "left") != "right"])
        right_count = len(body_items) - left_count
        max_items = max(left_count, right_count, 1)
        base_item_h = 50
        gap = 6
        bg_top = 75 if self.header_enabled else 20
        
        y = bg_top + 10
        
        left_title = "当前状态"
        right_title = "目标 / 对比"
        if title and " vs " in title:
            parts = title.split(" vs ", 1)
            if len(parts) >= 2:
                left_title, right_title = parts[0], parts[1]

        left_color = self.colors.get("secondary", "#dc2626")
        right_color = self.colors.get("success", "#16a34a")

        lines.append(f'<line x1="640" y1="78" x2="640" y2="685" stroke="#e2e8f0" stroke-width="2"/>')

        # 左列标题
        lines.append(
            f'<rect x="55" y="{y}" width="555" height="44" rx="8" fill="{left_color}" opacity="0.15"/>'
        )
        lines.append(
            f'<text x="330" y="{y+28}" font-family="{font_body}" font-size="19" font-weight="bold" '
            f'fill="{left_color}" text-anchor="middle">{self._esc(left_title)}</text>'
        )
        y += 50
        
        # 左列内容 - 带文本换行
        for text in left_items[:10]:
            if not text.strip():
                continue
            wrapped_lines = self._wrap_text(text, body_size, 520)
            line_count = len(wrapped_lines)
            item_h = max(base_item_h, line_count * int(body_size * 1.5) + 16)
            
            lines.append(
                f'<rect x="55" y="{y}" width="555" height="{item_h}" rx="8" fill="#fef2f2"/>'
            )
            lines.append(f'<rect x="55" y="{y}" width="6" height="{item_h}" rx="3" fill="{left_color}"/>')
            
            text_elements = []
            text_start_y = y + item_h // 2 - (line_count - 1) * body_size * 0.7
            for i, line in enumerate(wrapped_lines):
                dy = i * int(body_size * 1.5)
                text_elements.append(
                    f'<tspan x="80" dy="{dy if i == 0 else int(body_size * 1.5)}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(line)}</tspan>'
                )
            lines.append(f'<text x="80" y="{text_start_y}">{"".join(text_elements)}</text>')
            y += item_h + gap

        # 右列标题
        y = bg_top + 10
        lines.append(
            f'<rect x="670" y="{y}" width="555" height="44" rx="8" fill="{right_color}" opacity="0.15"/>'
        )
        lines.append(
            f'<text x="947" y="{y+28}" font-family="{font_body}" font-size="19" font-weight="bold" '
            f'fill="{right_color}" text-anchor="middle">{self._esc(right_title)}</text>'
        )
        y += 50
        
        # 右列内容 - 带文本换行
        for text in right_items[:10]:
            if not text.strip():
                continue
            wrapped_lines = self._wrap_text(text, body_size, 520)
            line_count = len(wrapped_lines)
            item_h = max(base_item_h, line_count * int(body_size * 1.5) + 16)
            
            lines.append(
                f'<rect x="670" y="{y}" width="555" height="{item_h}" rx="8" fill="#f0fdf4"/>'
            )
            lines.append(f'<rect x="670" y="{y}" width="6" height="{item_h}" rx="3" fill="{right_color}"/>')
            
            text_elements = []
            text_start_y = y + item_h // 2 - (line_count - 1) * body_size * 0.7
            for i, line in enumerate(wrapped_lines):
                dy = i * int(body_size * 1.5)
                text_elements.append(
                    f'<tspan x="695" dy="{dy if i == 0 else int(body_size * 1.5)}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(line)}</tspan>'
                )
            lines.append(f'<text x="695" y="{text_start_y}">{"".join(text_elements)}</text>')
            y += item_h + gap

        return "\n".join(lines)

    def _render_two_col(self, title: str, body_items: list, primary: str, accent: str, text_color: str, font_body: str, body_size: int = 16) -> str:
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
        lines.append(f'<line x1="640" y1="78" x2="640" y2="685" stroke="#e2e8f0" stroke-width="2"/>')

        # Smart labels from title
        left_label = "现 状"
        right_label = "目 标"
        if title and " vs " in title.lower():
            parts = title.split(" vs ", 1)
            if len(parts) >= 2:
                left_label = parts[0].strip()[:6]
                right_label = parts[1].strip()[:6]

        gap = 6
        label_h = 32
        bg_top = 75 if self.header_enabled else 20
        y = bg_top + 10
        
        lines.append(
            f'<text x="330" y="{y + 20}" font-family="{font_body}" font-size="19" font-weight="bold" '
            f'fill="{primary}" text-anchor="middle">{self._esc(left_label)}</text>'
        )
        y += label_h + gap
        
        # 左列内容 - 带文本换行
        for text in left_items[:11]:
            if not text.strip():
                continue
            wrapped_lines = self._wrap_text(text, body_size, 520)
            line_count = len(wrapped_lines)
            item_h = max(50, line_count * int(body_size * 1.5) + 16)
            
            lines.append(f'<rect x="55" y="{y}" width="555" height="{item_h}" rx="8" fill="#f8fafc"/>')
            lines.append(f'<rect x="55" y="{y}" width="6" height="{item_h}" rx="3" fill="{accent}"/>')
            
            text_elements = []
            text_start_y = y + item_h // 2 - (line_count - 1) * body_size * 0.7
            for i, line in enumerate(wrapped_lines):
                dy = i * int(body_size * 1.5)
                text_elements.append(
                    f'<tspan x="80" dy="{dy if i == 0 else int(body_size * 1.5)}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(line)}</tspan>'
                )
            lines.append(f'<text x="80" y="{text_start_y}">{"".join(text_elements)}</text>')
            y += item_h + gap

        y = bg_top + 10
        lines.append(
            f'<text x="947" y="{y + 20}" font-family="{font_body}" font-size="19" font-weight="bold" '
            f'fill="{primary}" text-anchor="middle">{self._esc(right_label)}</text>'
        )
        y += label_h + gap
        
        # 右列内容 - 带文本换行
        for text in right_items[:11]:
            if not text.strip():
                continue
            wrapped_lines = self._wrap_text(text, body_size, 520)
            line_count = len(wrapped_lines)
            item_h = max(50, line_count * int(body_size * 1.5) + 16)
            
            lines.append(f'<rect x="670" y="{y}" width="555" height="{item_h}" rx="8" fill="#f8fafc"/>')
            lines.append(f'<rect x="670" y="{y}" width="6" height="{item_h}" rx="3" fill="{accent}"/>')
            
            text_elements = []
            text_start_y = y + item_h // 2 - (line_count - 1) * body_size * 0.7
            for i, line in enumerate(wrapped_lines):
                dy = i * int(body_size * 1.5)
                text_elements.append(
                    f'<tspan x="695" dy="{dy if i == 0 else int(body_size * 1.5)}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(line)}</tspan>'
                )
            lines.append(f'<text x="695" y="{text_start_y}">{"".join(text_elements)}</text>')
            y += item_h + gap

        return "\n".join(lines)

    def _render_three_col(self, title: str, body_items: list, primary: str, text_color: str, font_body: str, body_size: int = 15) -> str:
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
        col_x = [45, 465, 885]
        col_w = 380
        colors = [self.colors.get("primary", "#1e40af"), self.colors.get("accent", "#f59e0b"), self.colors.get("secondary", "#dc2626")]
        labels = ["列一", "列二", "列三"]

        max_items = max(len(cols[0]), len(cols[1]), len(cols[2]), 1)
        item_h = min(48, int(560 / max_items))
        gap = 6
        label_h = 48
        total_h = label_h + gap + (item_h + gap) * max_items
        available_h = 580 if self.header_enabled else 640
        bg_top = 75 if self.header_enabled else 20
        start_y = bg_top + 8 + (available_h - total_h) * 0.4

        for ci in range(3):
            cx, cw = col_x[ci], col_w
            lines.append(f'<rect x="{cx}" y="{start_y}" width="{cw}" height="{label_h}" rx="8" fill="{colors[ci]}" opacity="0.18"/>')
            lines.append(
                f'<text x="{cx+cw//2}" y="{start_y+30}" font-family="{font_body}" font-size="18" font-weight="bold" '
                f'fill="{colors[ci]}" text-anchor="middle">{labels[ci]}</text>'
            )
            y = start_y + label_h + gap
            for text in cols[ci][:11]:
                if not text.strip():
                    continue
                lines.append(f'<rect x="{cx}" y="{y}" width="{cw}" height="{item_h}" rx="8" fill="#f8fafc"/>')
                lines.append(f'<rect x="{cx}" y="{y}" width="6" height="{item_h}" rx="3" fill="{colors[ci]}"/>')
                lines.append(
                    f'<text x="{cx+22}" y="{y + item_h//2 + 5}" font-family="{font_body}" font-size="{body_size}" '
                    f'fill="{text_color}">{self._esc(text[:58])}</text>'
                )
                y += item_h + gap
            if ci < 2:
                lines.append(f'<line x1="{cx+cw+10}" y1="{start_y}" x2="{cx+cw+10}" y2="{start_y + total_h}" stroke="#e2e8f0" stroke-width="2"/>')

        return "\n".join(lines)

    def _render_code(self, body_items: list, code_block: str, primary: str, text_color: str, font_body: str, body_size: int = 16) -> str:
        code_text = code_block
        if not code_text and body_items:
            code_text = "\n".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in body_items
            )
        lines = []
        code_lines = [l for l in code_text.split("\n") if l.strip()][:22]
        n = max(1, len(code_lines))
        block_h = min(520, n * 22 + 50)
        start_y = (720 - block_h) // 2
        lines.append(f'<rect x="40" y="{start_y}" width="1200" height="{block_h}" rx="8" fill="#1e293b"/>')
        lines.append(f'<rect x="40" y="{start_y}" width="1200" height="36" rx="8" fill="{primary}" opacity="0.9"/>')
        dot_colors = ["#ff5f57", "#febc2e", "#28c840"]
        for j, dc in enumerate(dot_colors):
            lines.append(f'<circle cx="{58 + j * 18}" cy="{start_y + 18}" r="5" fill="{dc}"/>')
        y_pos = start_y + 65
        for line_text in code_lines:
            display = self._esc(line_text.rstrip()[:100])
            lines.append(
                f'<text x="60" y="{y_pos}" font-family="Consolas, monospace" font-size="{body_size}" '
                f'fill="#e2e8f0">{display}</text>'
            )
            y_pos += 22
        return "\n".join(lines)

    def _render_matrix(self, body_items: list, primary: str, text_color: str, font_body: str, body_size: int = 14) -> str:
        labels = ["左上", "右上"]
        lines = []
        n = (len(body_items) + 3) // 4 * 4
        padded = body_items + [{"type": "list_item", "text": "", "level": 0}] * (n - len(body_items))
        cell_w, cell_h = 560, 260
        gap = 20
        start_x = 60
        bg_top = 75 if self.header_enabled else 20
        start_y = bg_top + 30

        for ni in range(min(n, 4)):
            row, col = ni // 2, ni % 2
            cx, cy = start_x + col * (cell_w + gap), start_y + row * (cell_h + gap)
            item = padded[ni] if ni < len(body_items) else {"type": "list_item", "text": "", "level": 0}
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            lines.append(f'<rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" rx="8" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1.5"/>')
            lines.append(f'<rect x="{cx}" y="{cy}" width="8" height="{cell_h}" rx="4" fill="{primary}"/>')
            cell_label = ["战略", "运营", "财务", "人才"][ni] if ni < 4 else ""
            lines.append(f'<text x="{cx + 24}" y="{cy + 24}" font-family="{font_body}" font-size="14" font-weight="bold" fill="{primary}">{cell_label}</text>')
            lines.append(f'<text x="{cx + 24}" y="{cy + 50}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}">{self._esc(text[:120])}</text>')
        return "\n".join(lines)

    def _render_timeline(self, body_items: list, primary: str, accent: str, text_color: str, font_body: str, body_size: int = 14) -> str:
        lines = []
        start_y = 120
        for ni, item in enumerate(body_items[:10]):
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if not text.strip(): continue
            y = start_y + ni * 52
            is_left = ni % 2 == 0
            lines.append(f'<circle cx="640" cy="{y + 8}" r="10" fill="{primary}" stroke="{accent}" stroke-width="3"/>')
            if ni < len(body_items) - 1:
                lines.append(f'<line x1="640" y1="{y + 20}" x2="640" y2="{y + 60}" stroke="{accent}" stroke-width="2" stroke-dasharray="6,4"/>')
            tx = 400 if is_left else 680
            ta = "end" if is_left else "start"
            lines.append(f'<text x="{tx}" y="{y + 26}" font-family="{font_body}" font-size="{body_size}" fill="{text_color}" text-anchor="{ta}">{self._esc(text[:80])}</text>')
        lines.append(f'<line x1="80" y1="100" x2="640" y2="100" stroke="{accent}" stroke-width="2"/>')
        lines.append(f'<line x1="640" y1="100" x2="1200" y2="100" stroke="{accent}" stroke-width="2"/>')
        return "\n".join(lines)

    def _render_waterfall(self, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        steps: list[dict] = []
        total = 0
        for item in body_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            label, _, val_str = text.partition(":")
            num = 0
            for part in val_str.split():
                try:
                    n = float(part.replace(",", "").replace("万", "").replace("亿", "").replace("%", "").strip())
                    num = n
                    break
                except ValueError:
                    pass
            if label.strip():
                steps.append({"label": label.strip(), "value": num})
                total = max(total, abs(num))

        if not steps:
            return ""

        lines: list[str] = []
        bar_w = 80
        gap = 30
        max_bar_w = min(180, (1140 - gap) // max(len(steps), 1))
        start_x = 60
        y_base = 420
        scale = max(1, total / 300) if total > 0 else 1

        for ni, s in enumerate(steps):
            cx = start_x + ni * (max_bar_w + gap)
            bh = min(abs(s["value"]) / scale, 300)
            is_pos = s["value"] >= 0
            color = "#10b981" if is_pos else "#ef4444"

            lines.append(f'<rect x="{cx}" y="{y_base - bh}" width="{max_bar_w}" height="{bh}" rx="4" fill="{color}" opacity="0.85"/>')
            lines.append(f'<rect x="{cx}" y="{y_base - bh}" width="{max_bar_w}" height="6" rx="2" fill="{accent}"/>')
            lines.append(f'<text x="{cx + max_bar_w//2}" y="{y_base - bh - 16}" font-family="{font_body}" font-size="13" font-weight="bold" fill="{text_color}" text-anchor="middle">{s["value"]:.0f}</text>')
            lines.append(f'<text x="{cx + max_bar_w//2}" y="{y_base + 20}" font-family="{font_body}" font-size="12" fill="{text_color}" text-anchor="middle">{self._esc(s["label"][:12])}</text>')

        lines.append(f'<line x1="{start_x}" y1="{y_base}" x2="{start_x + len(steps) * (max_bar_w + gap)}" y2="{y_base}" stroke="#94a3b8" stroke-width="2"/>')
        return "\n".join(lines)

    def _render_gauge(self, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        gauges: list[dict] = []
        for item in body_items[:6]:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            label, _, val_str = text.partition(":")
            num = 0
            for part in val_str.split():
                try:
                    n = float(part.replace(",", "").replace("万", "").replace("%", "").strip())
                    num = min(n, 120)
                    break
                except ValueError:
                    pass
            if label.strip() and num > 0:
                gauges.append({"label": label.strip(), "value": num})

        if not gauges:
            return ""

        lines: list[str] = []
        cols = min(len(gauges), 3)
        cell_w = 360
        start_x = (1280 - cols * cell_w) // 2
        radius = 65
        stroke_w = 8
        bg_top = 75 if self.header_enabled else 20

        for ni, g in enumerate(gauges):
            col = ni % cols
            row = ni // cols
            cx = start_x + col * cell_w + cell_w // 2
            cy = bg_top + 50 + row * 160 + 80
            pct = min(g["value"], 100)
            color = "#10b981" if pct >= 80 else ("#f59e0b" if pct >= 60 else "#ef4444")
            circumference = 2 * 3.14159 * radius
            dash = circumference * pct / 100

            lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#e5e7eb" stroke-width="{stroke_w}"/>')
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke_w}" stroke-dasharray="{dash} {circumference - dash}" transform="rotate(-90 {cx} {cy})"/>')
            lines.append(f'<text x="{cx}" y="{cy - 12}" font-family="{font_body}" font-size="22" font-weight="bold" fill="{color}" text-anchor="middle">{g["value"]:.1f}%</text>')
            lines.append(f'<text x="{cx}" y="{cy + 12}" font-family="{font_body}" font-size="11" fill="{text_color}" text-anchor="middle">达成率</text>')
            lines.append(f'<text x="{cx}" y="{cy + 40}" font-family="{font_body}" font-size="13" font-weight="bold" fill="{text_color}" text-anchor="middle">{self._esc(g["label"][:20])}</text>')

        return "\n".join(lines)

    def _render_ranking(self, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        items: list[dict] = []
        max_val = 0
        for item in body_items[:10]:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            parts = [p.strip() for p in text.split(":") if p.strip()]
            if len(parts) >= 2:
                label = parts[0]
                try:
                    val = float(parts[1].replace(",", "").replace("万", "").replace("亿", "").strip())
                    max_val = max(max_val, abs(val))
                    items.append({"label": label, "value": val})
                except ValueError:
                    items.append({"label": parts[0], "value": 0})

        if not items:
            return ""

        lines: list[str] = []
        bar_h = 44
        gap = 6
        max_w = 800
        start_y = 100
        medals = ["🥇", "🥈", "🥉"]

        for ni, it in enumerate(items):
            y = start_y + ni * (bar_h + gap)
            bar_w = max(60, int(max_w * abs(it["value"]) / max(max_val, 1))) if max_val > 0 else 200
            medal = medals[ni] if ni < 3 else f"{ni + 1}"
            badge_colors = ["#f59e0b", "#94a3b8", "#d97706"] + ["#3b82f6"] * 7

            lines.append(f'<text x="40" y="{y + bar_h//2 + 4}" font-family="{font_body}" font-size="15" fill="{badge_colors[min(ni, len(badge_colors)-1)]}" text-anchor="middle">{medal}</text>')
            lines.append(f'<rect x="80" y="{y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{badge_colors[min(ni, len(badge_colors)-1)]}" opacity="0.15"/>')
            lines.append(f'<text x="96" y="{y + bar_h//2 + 5}" font-family="{font_body}" font-size="14" font-weight="bold" fill="{text_color}">{self._esc(it["label"][:30])}</text>')
            lines.append(f'<text x="{80 + bar_w - 8}" y="{y + bar_h//2 + 4}" font-family="{font_body}" font-size="14" font-weight="bold" fill="{primary}" text-anchor="end">{it["value"]:,.1f}</text>')

        return "\n".join(lines)

    def _render_funnel(self, body_items: list, primary: str, accent: str, text_color: str, font_body: str) -> str:
        stages: list[dict] = []
        max_val = 0
        for item in body_items[:8]:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            parts = [p.strip() for p in text.split(":") if p.strip()]
            if len(parts) >= 2:
                try:
                    val = float(parts[1].replace(",", "").strip())
                    max_val = max(max_val, val)
                    stages.append({"label": parts[0], "value": val})
                except ValueError:
                    pass

        if not stages:
            return ""

        lines: list[str] = []
        funnel_colors = ["#3b82f6", "#6366f1", "#8b5cf6", "#a855f7", "#c084fc", "#d8b4fe", "#e9d5ff", "#f3e8ff"]
        start_y = 80
        each_h = 54
        max_w = 800

        for ni, s in enumerate(stages):
            y = start_y + ni * (each_h + 8)
            width = max(120, int(max_w * s["value"] / max(max_val, 1))) if max_val > 0 else 400
            cx = (1280 - width) // 2
            color = funnel_colors[min(ni, len(funnel_colors) - 1)]

            lines.append(f'<rect x="{cx}" y="{y}" width="{width}" height="{each_h}" rx="6" fill="{color}" opacity="0.85"/>')
            lines.append(f'<rect x="{cx}" y="{y}" width="6" height="{each_h}" rx="3" fill="{accent}"/>')
            lines.append(f'<text x="{cx + 20}" y="{y + each_h//2 + 5}" font-family="{font_body}" font-size="14" font-weight="bold" fill="#ffffff">{self._esc(s["label"][:20])}</text>')
            lines.append(f'<text x="{cx + width - 16}" y="{y + each_h//2 + 4}" font-family="{font_body}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="end">{s["value"]:,.0f}</text>')

            if ni < len(stages) - 1:
                next_w = max(120, int(max_w * stages[ni + 1]["value"] / max(max_val, 1))) if max_val > 0 else 400
                next_x = (1280 - next_w) // 2
                ty = y + each_h
                lines.append(f'<polygon points="{cx},{ty} {cx + width},{ty} {next_x + next_w},{ty + 8} {next_x},{ty + 8}" fill="{funnel_colors[min(ni+1, len(funnel_colors)-1)]}" opacity="0.3"/>')

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
            f'<rect x="90" y="{y_center-155}" width="1100" height="310" rx="16" fill="#f8fafc" '
            f'stroke="{primary}" stroke-width="2" opacity="0.45"/>'
        )
        lines.append(f'<rect x="90" y="{y_center-155}" width="8" height="310" rx="4" fill="{primary}"/>')
        lines.append(
            f'<text x="40" y="{y_center-10}" font-family="Georgia, serif" font-size="92" fill="{primary}" '
            f'opacity="0.3">"</text>'
        )
        lines.append(
            f'<text x="640" y="{y_center}" font-family="{font_body}" font-size="26" fill="{text_color}" '
            f'text-anchor="middle" font-style="italic">{self._esc(quote_text[:130])}</text>'
        )
        if quote_author:
            lines.append(
                f'<text x="640" y="{y_center+75}" font-family="{font_body}" font-size="18" fill="#64748b" text-anchor="middle">'
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
                nm = _re.search(r'([\d,.]+)\s*(%|万|亿|元|人|个|倍|‰)?', vp)
                if nm:
                    kpis.append({"label": lbl, "value": nm.group(1), "unit": nm.group(2) or ""})

        if not kpis:
            return self._render_card_list(body_items, primary, text_color, font_body)

        cols = min(len(kpis), 4)
        rows = (len(kpis) + cols - 1) // cols
        card_w = 280
        card_h = 180
        gap = 20
        total_w = card_w * cols + gap * (cols - 1)
        total_h = card_h * rows + gap * (rows - 1)
        start_x = (1280 - total_w) // 2
        available_h = 560 if self.header_enabled else 620
        start_y = (90 if self.header_enabled else 20) + (available_h - total_h) // 2

        lines = []
        card_colors = [
            (primary, accent),
            ("#6366f1", "#818cf8"), ("#0891b2", "#22d3ee"),
            ("#059669", "#34d399"), ("#7c3aed", "#a78bfa"),
            ("#dc2626", "#f87171"), ("#d97706", "#fbbf24"),
            ("#2563eb", "#60a5fa"),
        ]

        for idx, kpi in enumerate(kpis):
            row = idx // cols
            col = idx % cols
            cx = start_x + col * (card_w + gap)
            cy = start_y + row * (card_h + gap)
            bg_c, acc_c = card_colors[idx % len(card_colors)]

            # 卡片背景
            lines.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="{card_h}" rx="14" fill="#ffffff" stroke="#e5e7eb" stroke-width="1.5"/>')
            # 顶部色条
            lines.append(f'<rect x="{cx}" y="{cy}" width="{card_w}" height="6" rx="3" fill="{bg_c}"/>')
            # 标签
            label_size = "13" if len(kpi["label"]) <= 6 else "12"
            lines.append(f'<text x="{cx + 16}" y="{cy + 36}" font-family="{font_body}" font-size="{label_size}" fill="#64748b">{self._esc(kpi["label"])}</text>')

            # 大号数值
            val_size = "44" if len(kpi["value"]) <= 4 else "36" if len(kpi["value"]) <= 6 else "28"
            val_display = f'{self._esc(kpi["value"])}'
            unit_display = kpi["unit"]
            unit_x = cx + 16 + len(kpi["value"]) * int(val_size) * 0.55

            if kpi["unit"] == "%":
                try:
                    pct = float(kpi["value"].replace(",", ""))
                    bar_color = "#059669" if pct >= 80 else ("#d97706" if pct >= 60 else "#dc2626")
                    lines.append(f'<text x="{cx + 16}" y="{cy + 90}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{bar_color}">{val_display}%</text>')
                    # 进度条
                    bar_y = cy + 108
                    bar_w = card_w - 32
                    bar_h = 10
                    lines.append(f'<rect x="{cx + 16}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" fill="#e5e7eb"/>')
                    fill_w = int(bar_w * min(pct / 100, 1.0))
                    if fill_w > 0:
                        lines.append(f'<rect x="{cx + 16}" y="{bar_y}" width="{fill_w}" height="{bar_h}" rx="5" fill="{bar_color}"/>')
                    lines.append(f'<text x="{cx + card_w - 16}" y="{bar_y + bar_h + 14}" font-family="{font_body}" font-size="11" fill="#9ca3af" text-anchor="end">达成率</text>')
                except (ValueError, TypeError):
                    lines.append(f'<text x="{cx + 16}" y="{cy + 90}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{bg_c}">{val_display}%</text>')
            else:
                lines.append(f'<text x="{cx + 16}" y="{cy + 90}" font-family="{font_body}" font-size="{val_size}" font-weight="bold" fill="{bg_c}">{val_display}</text>')
                if unit_display:
                    lines.append(f'<text x="{cx + 16}" y="{cy + 125}" font-family="{font_body}" font-size="16" fill="#64748b">{self._esc(unit_display)}</text>')

        return "\n".join(lines)

    def _render_ending(self, title: str, subtitle: str, primary: str, accent: str, bg: str) -> str:
        lines = []
        # 浅色背景为主，不像封面用深色
        lines.append(f'<defs>')
        lines.append(f'<linearGradient id="endGrad" x1="0" y1="0" x2="0" y2="1">')
        lines.append(f'<stop offset="0%" stop-color="#ffffff"/>')
        lines.append(f'<stop offset="100%" stop-color="{self.colors.get("light-bg", "#f0f4ff")}"/>')
        lines.append(f'</linearGradient>')
        lines.append(f'</defs>')
        lines.append(f'<rect width="1280" height="720" fill="url(#endGrad)"/>')

        # 顶部装饰条
        lines.append(f'<rect y="0" width="1280" height="120" fill="{primary}" opacity="0.06"/>')
        lines.append(f'<rect y="0" width="1280" height="5" fill="{primary}"/>')

        # 中心内容区
        y_center = 320
        # 装饰圆环
        lines.append(f'<circle cx="640" cy="{y_center - 20}" r="70" fill="none" stroke="{primary}" stroke-width="3" opacity="0.15"/>')
        lines.append(f'<circle cx="640" cy="{y_center - 20}" r="55" fill="none" stroke="{accent}" stroke-width="2" opacity="0.2"/>')

        # 主标题
        lines.append(
            f'<text x="640" y="{y_center - 20}" font-family="Microsoft YaHei" font-size="42" '
            f'font-weight="bold" fill="{primary}" text-anchor="middle" letter-spacing="2">{self._esc(title or "感谢聆听")}</text>'
        )
        # 装饰线
        lines.append(f'<rect x="540" y="{y_center + 10}" width="200" height="4" rx="2" fill="{accent}"/>')

        if subtitle:
            lines.append(
                f'<text x="640" y="{y_center + 55}" font-family="Microsoft YaHei" font-size="18" '
                f'fill="#64748b" text-anchor="middle">{self._esc(subtitle)}</text>'
            )

        # 底部装饰
        lines.append(f'<rect y="700" width="1280" height="20" fill="{primary}" opacity="0.08"/>')
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
            return [], []
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
        text = str(text)
        text = text.replace("\x00", "").replace("\r", "")
        text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\t ")
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
            f'<text x="640" y="38" font-family="{font_body}" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle">{self._esc(title)}</text>'
            f'<text x="640" y="130" font-family="{font_body}" font-size="18" fill="{text_color}" text-anchor="middle">{self._esc(body)}</text>'
        )

    @staticmethod
    def generate_output_svg(slide: dict, page_num: int, svg_content: str,
                             canvas_format: str = "16:9") -> str:
        # CANVAS_VIEWBOX 已从 utils.json_utils 导入
        vb_w, vb_h = CANVAS_VIEWBOX.get(canvas_format, (1280, 720))
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}">\n'
            + svg_content + '\n'
            '</svg>'
        )
