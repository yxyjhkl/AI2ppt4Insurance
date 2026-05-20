"""Chart Engine - generates SVG charts (bar, line, pie, area) from data.

Output is SVG that can be embedded directly into slides.
"""
from __future__ import annotations
import math
import re
from typing import Optional


class ChartEngine:
    COLORS = [
        "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
        "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
    ]

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
        return self._bar_chart(data, title, width, height, theme)

    def _bar_chart(self, data: list[dict], title: str,
                   w: int, h: int, theme: Optional[dict]) -> str:
        labels = [d.get("label", "") for d in data]
        values = [float(d.get("value", 0)) for d in data]
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
        values = [float(d.get("value", 0)) for d in data]
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
        values = [float(d.get("value", 0)) for d in data]
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
        items = [(d.get("label", ""), max(0, float(d.get("value", 0)))) for d in data if float(d.get("value", 0)) > 0]
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
