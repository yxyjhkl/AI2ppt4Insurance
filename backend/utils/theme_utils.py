import os
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_THEME = {
    "colors": {
        "primary": "#1e40af",
        "secondary": "#3b82f6",
        "accent": "#f59e0b",
        "background": "#ffffff",
        "text": "#1f2937",
    },
    "fonts": {
        "title": "Arial",
        "body": "Microsoft YaHei",
    },
}


def resolve_template_dir(template_id: str, base_dir: str = None) -> str:
    if base_dir is None:
        base_dir = os.path.dirname(__file__)

    builtin = os.path.join(base_dir, "..", "templates", "built-in", template_id)
    if os.path.exists(builtin):
        return builtin

    custom = os.path.join(base_dir, "..", "templates", "custom", template_id)
    if os.path.exists(custom):
        return custom

    return ""


def load_theme(template_dir: str) -> dict:
    if not template_dir:
        return dict(DEFAULT_THEME)

    theme_path = os.path.join(template_dir, "theme.json")
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                theme = json.load(f)
            theme.setdefault("colors", {})
            for key, default_val in DEFAULT_THEME["colors"].items():
                theme["colors"].setdefault(key, default_val)
            theme.setdefault("fonts", {})
            for key, default_val in DEFAULT_THEME["fonts"].items():
                theme["fonts"].setdefault(key, default_val)
            _enhance_theme(theme)
            return theme
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load theme from {theme_path}: {e}")

    return dict(DEFAULT_THEME)


def _enhance_theme(theme: dict):
    try:
        from slide_builder.theme_enhancer import ThemeEnhancer
        enhancer = ThemeEnhancer(theme)
    except Exception:
        pass