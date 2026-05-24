"""Batch enhance all basic themes with visual_rules, elements, and animation."""
import json
import os
import colorsys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "built-in")

def hex_to_hls(hex_str: str):
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
    return colorsys.rgb_to_hls(r, g, b)

def hls_to_hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def derive_icon_set(primary_hex: str, theme_name: str) -> str:
    dark_themes = {"dark-modern", "pitch-dark", "financial-dark", "cyber-neon", "modern-geometric"}
    elegant_themes = {"elegant-serif", "luxury-gold", "academic-defense"}
    creative_themes = {"creative-vibrant", "gradient-sunset", "tech-startup"}
    if theme_name in dark_themes:
        return "minimal"
    if theme_name in elegant_themes:
        return "elegant"
    if theme_name in creative_themes:
        return "creative"
    return "business"

def enhance_theme(theme_path: str):
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)

    if "visual_rules" in theme and theme.get("elements"):
        return

    colors = theme.get("colors", {})
    primary = colors.get("primary", "#1e40af")
    secondary = colors.get("secondary", "#3b82f6")
    accent = colors.get("accent", "#f59e0b")
    bg = colors.get("background", "#ffffff")
    h, l, s = hex_to_hls(primary)
    is_dark_bg = hex_to_hls(bg)[1] < 0.25

    theme_name = os.path.basename(os.path.dirname(theme_path))

    theme.setdefault("spacing", {
        "margin-x": 40,
        "margin-y": 30,
        "title-size": 32,
        "body-size": 20,
    })

    theme.setdefault("visual_rules", {
        "title_size": 36 if not is_dark_bg else 40,
        "subtitle_size": 20,
        "body_size": 16,
        "caption_size": 12,
        "corner_radius": 4,
        "card_elevation": 2,
        "shadow_enabled": True,
        "gradient_bg": is_dark_bg,
        "section_divider": True,
        "page_number": True,
        "header_enabled": True,
        "icon_set": derive_icon_set(primary, theme_name),
    })

    theme.setdefault("animation", {
        "type": "none",
        "title_animation": "fade_in",
        "duration": 0.3,
    })

    theme.setdefault("elements", {
        "bullet_style": "disc",
        "table_stripe": True,
        "chart_colors": [
            primary,
            secondary,
            accent,
            hls_to_hex(h, min(1.0, l + 0.15), s),
        ],
        "progress_bar": True,
        "kpi_card_style": "rounded" if not is_dark_bg else "glass",
    })

    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(theme, f, ensure_ascii=False, indent=2)


def main():
    for dirname in sorted(os.listdir(BASE_DIR)):
        dir_path = os.path.join(BASE_DIR, dirname)
        if not os.path.isdir(dir_path):
            continue
        theme_path = os.path.join(dir_path, "theme.json")
        if not os.path.exists(theme_path):
            continue
        enhance_theme(theme_path)
        print(f"Enhanced: {dirname}/theme.json")


if __name__ == "__main__":
    main()
