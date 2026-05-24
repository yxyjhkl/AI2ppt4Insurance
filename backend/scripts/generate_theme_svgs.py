"""Generate SVG layout templates for all themes by color-replacing from professional-blue."""
import json
import os
import shutil

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "built-in")
SVG_SOURCE = os.path.join(BASE_DIR, "professional-blue")

REPLACE_MAP = {
    "1e40af": "PRIMARY",
    "3b82f6": "SECONDARY",
    "f59e0b": "ACCENT",
    "ffffff": "BACKGROUND",
    "1f2937": "TEXT",
    "f0f4ff": "LIGHT_BG",
    "eff6ff": "LIGHT_BG2",
    "dbeafe": "LIGHT_BG3",
    "bfdbfe": "LIGHT_BG4",
    "93c5fd": "LIGHT_BG5",
    "64748b": "MUTED",
    "94a3b8": "MUTED2",
    "cbd5e1": "MUTED3",
    "334155": "DARK_TEXT",
}


def replace_colors_in_svg(svg_content: str, theme_colors: dict) -> str:
    primary = theme_colors.get("primary", "#1e40af")
    secondary = theme_colors.get("secondary", "#3b82f6")
    accent = theme_colors.get("accent", "#f59e0b")
    background = theme_colors.get("background", "#ffffff")
    text = theme_colors.get("text", "#1f2937")
    light_bg = theme_colors.get("light-bg", "#f0f4ff")

    def lighten(hex_str, factor=0.25):
        h = hex_str.lstrip("#")
        r = min(255, int(int(h[0:2], 16) + (255 - int(h[0:2], 16)) * factor))
        g = min(255, int(int(h[2:4], 16) + (255 - int(h[2:4], 16)) * factor))
        b = min(255, int(int(h[4:6], 16) + (255 - int(h[4:6], 16)) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def darken(hex_str, factor=0.25):
        h = hex_str.lstrip("#")
        r = max(0, int(int(h[0:2], 16) * (1 - factor)))
        g = max(0, int(int(h[2:4], 16) * (1 - factor)))
        b = max(0, int(int(h[4:6], 16) * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def muted(hex_str, alpha=0.45):
        h = hex_str.lstrip("#")
        r = int(int(h[0:2], 16) * alpha + 255 * (1 - alpha))
        g = int(int(h[2:4], 16) * alpha + 255 * (1 - alpha))
        b = int(int(h[4:6], 16) * alpha + 255 * (1 - alpha))
        return f"#{r:02x}{g:02x}{b:02x}"

    replacements = {
        "#1e40af": primary,
        "#1d4ed8": secondary,
        "#3b82f6": secondary,
        "#f59e0b": accent,
        "#d97706": darken(accent),
        "#fbbf24": lighten(accent, 0.5),
        "#ffffff": background,
        "#1f2937": text,
        "#111827": darken(text, 0.5),
        "#374151": darken(text, 0.25),
        "#f0f4ff": light_bg,
        "#eff6ff": lighten(light_bg, 0.3),
        "#dbeafe": muted(primary, 0.6),
        "#bfdbfe": muted(secondary, 0.6),
        "#93c5fd": muted(secondary, 0.4),
        "#64748b": muted(text, 0.7),
        "#94a3b8": muted(text, 0.6),
        "#cbd5e1": muted(text, 0.4),
        "#e2e8f0": muted(text, 0.35),
        "#334155": darken(text, 0.5),
        "#475569": darken(text, 0.35),
        "#0ea5e9": secondary,
        "#0284c7": darken(secondary, 0.3),
        "#22c55e": "#10b981",
        "#16a34a": darken("#10b981", 0.3),
        "#ef4444": "#ef4444",
        "#dc2626": darken("#ef4444", 0.3),
        "#8b5cf6": accent,
        "#7c3aed": darken(accent, 0.3),
        "#ec4899": accent,
        "#db2777": darken(accent, 0.3),
    }

    result = svg_content
    for old_color, new_color in replacements.items():
        result = result.replace(old_color, new_color)
    return result


def generate_svgs_for_theme(theme_name: str, theme_colors: dict):
    theme_dir = os.path.join(BASE_DIR, theme_name)
    os.makedirs(theme_dir, exist_ok=True)

    for svg_name in os.listdir(SVG_SOURCE):
        if not svg_name.endswith(".svg"):
            continue
        svg_path = os.path.join(SVG_SOURCE, svg_name)
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = replace_colors_in_svg(content, theme_colors)

        output_path = os.path.join(theme_dir, svg_name)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    print(f"Generated {sum(1 for f in os.listdir(theme_dir) if f.endswith('.svg'))} SVGs for {theme_name}")


def main():
    for dirname in sorted(os.listdir(BASE_DIR)):
        if dirname == "professional-blue":
            continue

        dir_path = os.path.join(BASE_DIR, dirname)
        if not os.path.isdir(dir_path):
            continue

        theme_path = os.path.join(dir_path, "theme.json")
        if not os.path.exists(theme_path):
            continue

        with open(theme_path, "r", encoding="utf-8") as f:
            theme = json.load(f)

        colors = theme.get("colors", {})
        if not colors.get("primary"):
            continue

        generate_svgs_for_theme(dirname, colors)


if __name__ == "__main__":
    main()
