"""Chart Engine - generates SVG charts (bar, line, pie, area) from data.

Output is SVG that can be embedded directly into slides.
"""
from __future__ import annotations
import math
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ChartEngine:
    # 专业商务配色方案
    COLORS = [
        "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
        "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
    ]
    
    # 渐变配色方案
    GRADIENT_COLORS = {
        "blue": ["#3b82f6", "#60a5fa"],
        "green": ["#10b981", "#34d399"],
        "red": ["#ef4444", "#f87171"],
        "orange": ["#f59e0b", "#fbbf24"],
        "purple": ["#8b5cf6", "#a78bfa"],
        "pink": ["#ec4899", "#f472b6"],
    }

    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "").replace("%", "").strip())
            except (ValueError, TypeError):
                return default
        return default

    def generate(self, chart_type: str, data: list[dict],
                 title: str = "", width: int = 600, height: int = 400,
                 theme: Optional[dict] = None) -> str:
        if chart_type == "bar":
            return self._bar_chart(data, title, width, height, theme)
        elif chart_type == "line":
            return self._line_chart(data, title, width, height, theme)
        elif chart_type == "pie":
            return self._pie_chart(data, title, width, height, theme)
        elif chart_type == "area":
            return self._area_chart(data, title, width, height, theme)
        elif chart_type == "donut":
            return self._donut_chart(data, title, width, height, theme)
        elif chart_type == "radar":
            return self._radar_chart(data, title, width, height, theme)
        elif chart_type == "funnel":
            return self._funnel_chart(data, title, width, height, theme)
        elif chart_type == "gauge":
            return self._gauge_chart(data, title, width, height, theme)
        elif chart_type == "progress":
            return self._progress_chart(data, title, width, height, theme)
        return self._bar_chart(data, title, width, height, theme)

    def _bar_chart(self, data: list[dict], title: str,
                   w: int, h: int, theme: Optional[dict]) -> str:
        labels = [d.get("label", "") for d in data]
        values = [self._safe_float(d.get("value", 0)) for d in data]
        if not values:
            return self._empty_svg(w, h, title)

        max_val = max(values) * 1.15 or 1
        cols = len(values)
        margin = {"t": 50, "r": 20, "b": 50, "l": 60}
        chart_w = w - margin["l"] - margin["r"]
        chart_h = h - margin["t"] - margin["b"]
        bar_w = max(8, chart_w / cols * 0.65)
        gap = chart_w / cols

        parts = [self._svg_header(w, h, title, theme)]
        parts.append(f'<line x1="{margin["l"]}" y1="{h - margin["b"]}" x2="{w - margin["r"]}" y2="{h - margin["b"]}" stroke="#d1d5db" stroke-width="1"/>')
        parts.append(f'<line x1="{margin["l"]}" y1="{margin["t"]}" x2="{margin["l"]}" y2="{h - margin["b"]}" stroke="#d1d5db" stroke-width="1"/>')

        grid_lines = 4
        for i in range(grid_lines + 1):
            y = h - margin["b"] - (chart_h * i / grid_lines)
            val = max_val * i / grid_lines
            parts.append(f'<line x1="{margin["l"]}" y1="{y}" x2="{w - margin["r"]}" y2="{y}" stroke="#f3f4f6" stroke-width="1"/>')
            parts.append(f'<text x="{margin["l"] - 8}" y="{y + 4}" text-anchor="end" font-size="11" fill="#6b7280">{self._fmt(val)}</text>')

        for i, (label, val) in enumerate(zip(labels, values)):
            x = margin["l"] + i * gap + (gap - bar_w) / 2
            bar_h = (val / max_val) * chart_h
            y = h - margin["b"] - bar_h
            color = self.COLORS[i % len(self.COLORS)]
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{color}" rx="2"><title>{label}: {self._fmt(val)}</title></rect>')
            parts.append(f'<text x="{margin["l"] + i * gap + gap / 2}" y="{h - margin["b"] + 16}" text-anchor="end" transform="rotate(-30, {margin["l"] + i * gap + gap / 2}, {h - margin["b"] + 16})" font-size="10" fill="#6b7280">{self._truncate(label)}</text>')

        parts.append("</svg>")
        return "\n".join(parts)

    def _line_chart(self, data: list[dict], title: str,
                    w: int, h: int, theme: Optional[dict]) -> str:
        labels = [d.get("label", "") for d in data]
        values = [self._safe_float(d.get("value", 0)) for d in data]
        if not values:
            return self._empty_svg(w, h, title)

        max_val = max(values) * 1.15 or 1
        margin = {"t": 50, "r": 20, "b": 50, "l": 60}
        chart_w = w - margin["l"] - margin["r"]
        chart_h = h - margin["t"] - margin["b"]
        n = len(values)

        parts = [self._svg_header(w, h, title, theme)]
        parts.append(f'<line x1="{margin["l"]}" y1="{h - margin["b"]}" x2="{w - margin["r"]}" y2="{h - margin["b"]}" stroke="#d1d5db" stroke-width="1"/>')

        grid_lines = 4
        for i in range(grid_lines + 1):
            y = h - margin["b"] - (chart_h * i / grid_lines)
            val = max_val * i / grid_lines
            parts.append(f'<line x1="{margin["l"]}" y1="{y}" x2="{w - margin["r"]}" y2="{y}" stroke="#f3f4f6" stroke-width="1"/>')
            parts.append(f'<text x="{margin["l"] - 8}" y="{y + 4}" text-anchor="end" font-size="11" fill="#6b7280">{self._fmt(val)}</text>')

        pts = []
        for i, val in enumerate(values):
            x = margin["l"] + (chart_w * i / max(1, n - 1))
            y = h - margin["b"] - (val / max_val) * chart_h
            pts.append(f"{x},{y}")

        points_str = " ".join(pts)
        parts.append(f'<polyline points="{points_str}" fill="none" stroke="{self.COLORS[0]}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')

        for i, (label, val) in enumerate(zip(labels, values)):
            x = margin["l"] + (chart_w * i / max(1, n - 1))
            y = h - margin["b"] - (val / max_val) * chart_h
            parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="white" stroke="{self.COLORS[0]}" stroke-width="2"><title>{label}: {self._fmt(val)}</title></circle>')
            parts.append(f'<text x="{x}" y="{h - margin["b"] + 16}" text-anchor="end" transform="rotate(-30, {x}, {h - margin["b"] + 16})" font-size="10" fill="#6b7280">{self._truncate(label)}</text>')

        parts.append("</svg>")
        return "\n".join(parts)

    def _area_chart(self, data: list[dict], title: str,
                    w: int, h: int, theme: Optional[dict]) -> str:
        labels = [d.get("label", "") for d in data]
        values = [self._safe_float(d.get("value", 0)) for d in data]
        if not values:
            return self._empty_svg(w, h, title)

        max_val = max(values) * 1.15 or 1
        margin = {"t": 50, "r": 20, "b": 50, "l": 60}
        chart_w = w - margin["l"] - margin["r"]
        chart_h = h - margin["t"] - margin["b"]
        n = len(values)

        parts = [self._svg_header(w, h, title, theme)]
        base_y = h - margin["b"]

        pts = []
        for i, val in enumerate(values):
            x = margin["l"] + (chart_w * i / max(1, n - 1))
            y = base_y - (val / max_val) * chart_h
            pts.append(f"{x},{y}")

        last_x = margin["l"] + chart_w
        poly_pts = " ".join(pts) + f" {last_x},{base_y} {margin['l']},{base_y}"
        parts.append(f'<polygon points="{poly_pts}" fill="{self.COLORS[0]}" fill-opacity="0.2" stroke="{self.COLORS[0]}" stroke-width="2"/>')

        for i, (label, val) in enumerate(zip(labels, values)):
            x = margin["l"] + (chart_w * i / max(1, n - 1))
            y = base_y - (val / max_val) * chart_h
            parts.append(f'<text x="{x}" y="{y - 8}" text-anchor="middle" font-size="10" fill="#6b7280">{self._fmt(val)}</text>')

        parts.append("</svg>")
        return "\n".join(parts)

    def _pie_chart(self, data: list[dict], title: str,
                   w: int, h: int, theme: Optional[dict]) -> str:
        items = [(d.get("label", ""), max(0, self._safe_float(d.get("value", 0)))) for d in data if self._safe_float(d.get("value", 0)) > 0]
        if not items:
            return self._empty_svg(w, h, title)

        total = sum(v for _, v in items)
        cx, cy, r = w // 2, h // 2 + 10, min(w, h) // 2 - 40
        parts = [self._svg_header(w, h, title, theme)]

        angle = -90
        for i, (label, val) in enumerate(items):
            frac = val / total
            sweep = frac * 360
            end_angle = angle + sweep
            color = self.COLORS[i % len(self.COLORS)]

            rad_start = math.radians(angle)
            rad_end = math.radians(end_angle)
            x1 = cx + r * math.cos(rad_start)
            y1 = cy + r * math.sin(rad_start)
            x2 = cx + r * math.cos(rad_end)
            y2 = cy + r * math.sin(rad_end)

            large = 1 if sweep > 180 else 0
            d = f"M {cx},{cy} L {x1},{y1} A {r},{r} 0 {large},1 {x2},{y2} Z"
            parts.append(f'<path d="{d}" fill="{color}" stroke="white" stroke-width="1.5"><title>{label}: {self._fmt(val)} ({frac*100:.1f}%)</title></path>')

            mid_angle = math.radians(angle + sweep / 2)
            lx = cx + (r + 20) * math.cos(mid_angle)
            ly = cy + (r + 20) * math.sin(mid_angle)
            if 90 < (angle + sweep / 2) % 360 < 270:
                lx -= len(f"{label} {frac*100:.0f}%") * 4
            parts.append(f'<text x="{lx}" y="{ly + 4}" font-size="11" fill="#374151">{label} {frac*100:.0f}%</text>')

            angle = end_angle

        parts.append("</svg>")
        return "\n".join(parts)

    def _svg_header(self, w: int, h: int, title: str, theme: Optional[dict]) -> str:
        title_y = 28
        title_el = f'<text x="{w//2}" y="{title_y}" text-anchor="middle" font-size="18" font-weight="bold" fill="#1f2937">{self._esc(title)}</text>' if title else ""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="white" rx="4"/>
{title_el}'''

    def _empty_svg(self, w: int, h: int, title: str) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="white" rx="4"/>
<text x="{w//2}" y="{h//2}" text-anchor="middle" font-size="14" fill="#9ca3af">No data available</text>
</svg>'''

    @staticmethod
    def _fmt(val: float) -> str:
        if val >= 1_000_000_000:
            return f"{val/1_000_000_000:.1f}B"
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        if val >= 1_000:
            return f"{val/1_000:.1f}K"
        if val == int(val):
            return str(int(val))
        return f"{val:.1f}"

    @staticmethod
    def _truncate(s: str, max_len: int = 12) -> str:
        return s if len(s) <= max_len else s[:max_len-1] + "…"

    @staticmethod
    def _esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _donut_chart(self, data: list[dict], title: str, w: int, h: int, theme: Optional[dict]) -> str:
        """环形图 - 现代美观的数据展示"""
        labels = [d.get("label", "") for d in data]
        values = [self._safe_float(d.get("value", 0)) for d in data]
        if not values:
            return self._empty_svg(w, h, title)
        
        total = sum(values)
        if total == 0:
            return self._empty_svg(w, h, title)
        
        cx, cy = w // 2, h // 2 - 10
        outer_r = min(w, h) // 2 - 50
        inner_r = outer_r * 0.6
        
        parts = [self._svg_header(w, h, title, theme)]
        
        angle = -90
        for i, (label, val) in enumerate(zip(labels, values)):
            frac = val / total
            sweep = frac * 360
            color = self.COLORS[i % len(self.COLORS)]
            
            start_rad = math.radians(angle)
            end_rad = math.radians(angle + sweep)
            
            x1 = cx + outer_r * math.cos(start_rad)
            y1 = cy + outer_r * math.sin(start_rad)
            x2 = cx + outer_r * math.cos(end_rad)
            y2 = cy + outer_r * math.sin(end_rad)
            x3 = cx + inner_r * math.cos(end_rad)
            y3 = cy + inner_r * math.sin(end_rad)
            x4 = cx + inner_r * math.cos(start_rad)
            y4 = cy + inner_r * math.sin(start_rad)
            
            large = 1 if sweep > 180 else 0
            d = f"M {x1},{y1} A {outer_r},{outer_r} 0 {large},1 {x2},{y2} L {x3},{y3} A {inner_r},{inner_r} 0 {large},0 {x4},{y4} Z"
            parts.append(f'<path d="{d}" fill="{color}" stroke="white" stroke-width="2"><title>{label}: {frac*100:.1f}%</title></path>')
            
            # 添加标签
            mid_angle = angle + sweep / 2
            label_r = outer_r + 25
            lx = cx + label_r * math.cos(math.radians(mid_angle))
            ly = cy + label_r * math.sin(math.radians(mid_angle))
            if 90 < mid_angle % 360 < 270:
                lx -= 40
            parts.append(f'<text x="{lx}" y="{ly}" font-size="11" fill="#374151" text-anchor="middle">{label} {frac*100:.0f}%</text>')
            
            angle += sweep
        
        # 中心显示总数
        parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="24" font-weight="bold" fill="#1f2937">{self._fmt(total)}</text>')
        parts.append(f'<text x="{cx}" y="{cy+20}" text-anchor="middle" font-size="12" fill="#6b7280">总计</text>')
        
        parts.append("</svg>")
        return "\n".join(parts)

    def _progress_chart(self, data: list[dict], title: str, w: int, h: int, theme: Optional[dict]) -> str:
        """进度条图表 - 适合展示完成率/目标"""
        parts = [self._svg_header(w, h, title, theme)]
        
        margin = {"t": 50, "l": 20, "r": 20, "b": 20}
        bar_h = 30
        gap = 20
        
        for i, item in enumerate(data):
            label = item.get("label", "")
            value = self._safe_float(item.get("value", 0))
            target = self._safe_float(item.get("target", 100))
            progress = min(value / target * 100, 100) if target > 0 else 0
            
            y = margin["t"] + i * (bar_h + gap)
            
            # 标签
            parts.append(f'<text x="0" y="{y + 20}" font-size="13" fill="#374151" font-weight="500">{label}</text>')
            
            # 背景条
            parts.append(f'<rect x="80" y="{y}" width="{w - 160}" height="{bar_h}" rx="6" fill="#e5e7eb"/>')
            
            # 进度条
            bar_w = (w - 160) * progress / 100
            color = self.COLORS[i % len(self.COLORS)]
            if progress >= 100:
                color = "#10b981"  # 绿色表示完成
            elif progress >= 70:
                color = self.COLORS[i % len(self.COLORS)]
            else:
                color = "#f59e0b"  # 黄色表示进行中
            
            parts.append(f'<rect x="80" y="{y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{color}"/>')
            
            # 百分比文字
            parts.append(f'<text x="{w - 80}" y="{y + 20}" font-size="12" fill="#6b7280" text-anchor="end">{progress:.0f}%</text>')
        
        parts.append("</svg>")
        return "\n".join(parts)

    def _funnel_chart(self, data: list[dict], title: str, w: int, h: int, theme: Optional[dict]) -> str:
        """漏斗图 - 适合展示转化流程"""
        parts = [self._svg_header(w, h, title, theme)]
        
        if not data:
            return self._empty_svg(w, h, title)
        
        max_val = max(self._safe_float(d.get("value", 0)) for d in data)
        if max_val == 0:
            return self._empty_svg(w, h, title)
        
        margin = {"t": 50, "b": 30}
        total_h = h - margin["t"] - margin["b"]
        item_h = total_h / len(data)
        center_x = w // 2
        
        for i, item in enumerate(data):
            label = item.get("label", "")
            value = self._safe_float(item.get("value", 0))
            ratio = value / max_val
            
            y = margin["t"] + i * item_h
            top_w = (w - 40) * (1 - i / len(data)) * ratio + 40
            bottom_w = (w - 40) * (1 - (i + 1) / len(data)) * ratio + 40 if i < len(data) - 1 else 40
            
            points = f"{center_x - top_w/2},{y} {center_x + top_w/2},{y} {center_x + bottom_w/2},{y + item_h} {center_x - bottom_w/2},{y + item_h}"
            
            color = self.COLORS[i % len(self.COLORS)]
            parts.append(f'<polygon points="{points}" fill="{color}" opacity="0.85"><title>{label}: {self._fmt(value)}</title></polygon>')
            
            # 标签
            parts.append(f'<text x="{center_x}" y="{y + item_h/2 + 5}" text-anchor="middle" font-size="13" fill="white" font-weight="500">{label} ({self._fmt(value)})</text>')
        
        parts.append("</svg>")
        return "\n".join(parts)

    def _radar_chart(self, data: list[dict], title: str, w: int, h: int, theme: Optional[dict]) -> str:
        """雷达图 - 适合多维度对比"""
        parts = [self._svg_header(w, h, title, theme)]
        
        if not data:
            return self._empty_svg(w, h, title)
        
        cx, cy = w // 2, h // 2 - 10
        r = min(w, h) // 2 - 80
        n = len(data)
        angle_step = 2 * math.pi / n
        
        # 绘制网格
        for level in [0.25, 0.5, 0.75, 1.0]:
            points = []
            for i in range(n):
                angle = i * angle_step - math.pi / 2
                x = cx + r * level * math.cos(angle)
                y = cy + r * level * math.sin(angle)
                points.append(f"{x},{y}")
            parts.append(f'<polygon points="{" ".join(points)}" fill="none" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4,4"/>')
        
        # 绘制轴线
        for i in range(n):
            angle = i * angle_step - math.pi / 2
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        
        # 绘制数据区域
        points = []
        for i, item in enumerate(data):
            value = self._safe_float(item.get("value", 0)) / 100
            angle = i * angle_step - math.pi / 2
            x = cx + r * value * math.cos(angle)
            y = cy + r * value * math.sin(angle)
            points.append(f"{x},{y}")
        
        parts.append(f'<polygon points="{" ".join(points)}" fill="#3b82f6" opacity="0.3" stroke="#3b82f6" stroke-width="2"/>')
        
        # 添加标签
        for i, item in enumerate(data):
            label = item.get("label", "")
            angle = i * angle_step - math.pi / 2
            x = cx + (r + 20) * math.cos(angle)
            y = cy + (r + 20) * math.sin(angle)
            anchor = "middle" if abs(angle) < 0.1 or abs(angle - math.pi) < 0.1 else ("end" if angle > 0 and angle < math.pi else "start")
            parts.append(f'<text x="{x}" y="{y+4}" text-anchor="{anchor}" font-size="11" fill="#374151">{label}</text>')
        
        parts.append("</svg>")
        return "\n".join(parts)

    def _gauge_chart(self, data: list[dict], title: str, w: int, h: int, theme: Optional[dict]) -> str:
        """仪表盘图表 - 适合展示单一指标"""
        parts = [self._svg_header(w, h, title, theme)]
        
        if not data:
            return self._empty_svg(w, h, title)
        
        item = data[0]
        value = self._safe_float(item.get("value", 0))
        max_val = self._safe_float(item.get("max", 100))
        progress = min(value / max_val * 100, 100) if max_val > 0 else 0
        
        cx, cy = w // 2, h // 2 + 30
        r = min(w, h) // 2 - 60
        
        # 背景弧
        start_angle = 135
        end_angle = 405
        sweep = 270
        
        # 绘制背景弧
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)
        parts.append(f'<path d="M {x1},{y1} A {r},{r} 0 1,1 {x2},{y2}" fill="none" stroke="#e5e7eb" stroke-width="20" stroke-linecap="round"/>')
        
        # 进度弧
        progress_sweep = sweep * progress / 100
        progress_end = start_angle + progress_sweep
        progress_rad = math.radians(progress_end)
        px = cx + r * math.cos(progress_rad)
        py = cy + r * math.sin(progress_rad)
        
        color = "#10b981" if progress >= 80 else ("#f59e0b" if progress >= 50 else "#ef4444")
        parts.append(f'<path d="M {x1},{y1} A {r},{r} 0 1,1 {px},{py}" fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round"/>')
        
        # 中心数值
        parts.append(f'<text x="{cx}" y="{cy-10}" text-anchor="middle" font-size="36" font-weight="bold" fill="#1f2937">{value:.0f}</text>')
        parts.append(f'<text x="{cx}" y="{cy+15}" text-anchor="middle" font-size="14" fill="#6b7280">/ {max_val:.0f}</text>')
        
        # 标签
        label = item.get("label", "完成率")
        parts.append(f'<text x="{cx}" y="{cy+45}" text-anchor="middle" font-size="14" fill="#374151" font-weight="500">{label}</text>')
        
        parts.append("</svg>")
        return "\n".join(parts)
