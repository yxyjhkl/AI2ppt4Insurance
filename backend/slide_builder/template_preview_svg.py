"""模板 SVG 预览生成器 - 从 theme.json 生成彩色 SVG 缩略图"""
import json
import os
import hashlib

PREVIEW_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "preview_cache")

def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) < 6:
        return "200,200,200"
    return f"{int(h[:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

def _lighten(h, f=0.3):
    h = h.lstrip("#")
    if len(h) < 6:
        return "#cccccc"
    r = min(255, int(int(h[:2],16) + (255-int(h[:2],16))*f))
    g = min(255, int(int(h[2:4],16) + (255-int(h[2:4],16))*f))
    b = min(255, int(int(h[4:6],16) + (255-int(h[4:6],16))*f))
    return f"#{r:02x}{g:02x}{b:02x}"

def generate_preview_svg(theme: dict, template_id: str = "") -> str:
    colors = theme.get("colors", {})
    fonts = theme.get("fonts", {})
    name = theme.get("name", template_id or "Template")
    cat = theme.get("category", "")

    primary = colors.get("primary", "#1e40af")
    secondary = colors.get("secondary", "#3b82f6")
    accent = colors.get("accent", "#f59e0b")
    bg = colors.get("background", "#ffffff")
    text_color = colors.get("text", "#1f2937")

    body_font = fonts.get("body_cn") or fonts.get("body") or "Arial"
    title_font = fonts.get("title_cn") or fonts.get("title") or "Arial"

    swatches = []
    for label, c in [("主色", primary), ("辅色", secondary), ("强调", accent), ("背景", bg), ("文字", text_color)]:
        swatches.append(f"""<rect x="{120 + len(swatches)*70}" y="230" width="60" height="60" rx="6" fill="{c}" stroke="#e5e7eb" stroke-width="1"/>
<text x="{150 + (len(swatches)-1)*70}" y="308" text-anchor="middle" font-size="9" fill="#9ca3af" font-family="Arial">{label}</text>""")

    title_bar_bg = primary
    is_dark = sum(int(primary.lstrip("#")[i:i+2],16) for i in (0,2,4)) < 384
    title_text_color = "#ffffff" if is_dark else "#1f2937"
    body_text = "#ffffff" if is_dark else "#374151"

    accent_rgb = _hex_to_rgb(accent)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
  <defs>
    <linearGradient id="hdr" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{primary}"/>
      <stop offset="100%" stop-color="{secondary}"/>
    </linearGradient>
    <linearGradient id="card1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{_lighten(primary,0.85)}"/>
      <stop offset="100%" stop-color="{_lighten(secondary,0.85)}"/>
    </linearGradient>
  </defs>
  <rect width="400" height="300" fill="{bg}" rx="8"/>
  <rect width="400" height="48" fill="url(#hdr)" rx="8"/>
  <rect y="40" width="400" height="8" fill="url(#hdr)"/>
  <text x="20" y="30" font-family="{title_font}" font-size="14" font-weight="bold" fill="{title_text_color}">{name[:24]}</text>
  <rect x="20" y="230" width="360" height="55" rx="8" fill="url(#card1)" stroke="{_lighten(primary,0.6)}" stroke-width="1"/>
  <text x="35" y="252" font-family="{body_font}" font-size="10" font-weight="bold" fill="{body_text}">模板预览 · {cat}</text>
  <text x="35" y="270" font-family="{body_font}" font-size="9" fill="{_lighten(text_color,0.4)}">配色方案</text>
  {"".join(swatches)}
  <rect x="20" y="68" width="170" height="150" rx="6" fill="{_lighten(primary,0.9)}" stroke="{_lighten(primary,0.6)}" stroke-width="1"/>
  <rect x="30" y="78" width="60" height="12" rx="3" fill="{primary}" opacity="0.3"/>
  <rect x="30" y="96" width="150" height="8" rx="2" fill="{text_color}" opacity="0.15"/>
  <rect x="30" y="110" width="140" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="30" y="124" width="145" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="30" y="142" width="120" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="30" y="160" width="90" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="30" y="178" width="130" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="30" y="196" width="100" height="8" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="210" y="68" width="170" height="72" rx="6" fill="{_lighten(secondary,0.9)}" stroke="{_lighten(secondary,0.6)}" stroke-width="1"/>
  <rect x="220" y="80" width="80" height="10" rx="3" fill="{secondary}" opacity="0.3"/>
  <rect x="220" y="96" width="140" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="220" y="108" width="130" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="220" y="120" width="100" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="210" y="150" width="170" height="68" rx="6" fill="{_lighten(accent,0.85)}" stroke="{_lighten(accent,0.5)}" stroke-width="1"/>
  <rect x="220" y="162" width="60" height="10" rx="3" fill="{accent}" opacity="0.3"/>
  <rect x="220" y="178" width="140" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="220" y="190" width="120" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
  <rect x="220" y="202" width="90" height="6" rx="2" fill="{text_color}" opacity="0.12"/>
</svg>"""
    return svg

def get_cached_preview(template_id: str, theme: dict) -> str:
    os.makedirs(PREVIEW_CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(PREVIEW_CACHE_DIR, f"{template_id}.svg")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    svg = generate_preview_svg(theme, template_id)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return svg
