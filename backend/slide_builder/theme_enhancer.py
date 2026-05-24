"""主题增强器 - 添加丰富的视觉元素和渐变效果"""
import json
import os
from typing import Dict, List, Optional


class ThemeEnhancer:
    """增强主题配置，添加丰富的视觉效果"""
    
    def __init__(self, theme: dict):
        self.theme = theme
        self._enhance_theme()
    
    def _enhance_theme(self):
        """增强主题配置"""
        self._add_gradient_palette()
        self._add_decoration_elements()
        self._add_card_styles()
        self._add_icon_colors()
        self._add_background_patterns()
    
    def _add_gradient_palette(self):
        """添加渐变色配色方案"""
        colors = self.theme.get("colors", {})
        primary = colors.get("primary", "#1e40af")
        secondary = colors.get("secondary", "#3b82f6")
        accent = colors.get("accent", "#f59e0b")
        
        self.theme["gradients"] = {
            "primary": f"{primary} 0%, {secondary} 100%",
            "accent": f"{accent} 0%, {self._lighten_color(accent, 0.3)} 100%",
            "hero": f"{primary} 0%, {accent} 100%",
            "soft": f"{self._lighten_color(primary, 0.7)} 0%, {self._lighten_color(secondary, 0.7)} 100%",
            "subtle": f"{colors.get('background', '#ffffff')} 0%, {self._lighten_color(primary, 0.9)} 100%",
        }
        
        self.theme["color_variants"] = {
            "primary_light": self._lighten_color(primary, 0.2),
            "primary_dark": self._darken_color(primary, 0.2),
            "secondary_light": self._lighten_color(secondary, 0.2),
            "secondary_dark": self._darken_color(secondary, 0.2),
            "accent_light": self._lighten_color(accent, 0.3),
            "accent_dark": self._darken_color(accent, 0.2),
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
        }
    
    def _add_decoration_elements(self):
        """添加装饰元素配置"""
        colors = self.theme.get("colors", {})
        self.theme["decorations"] = {
            "header_bar": {
                "height": 8,
                "gradient": self.theme.get("gradients", {}).get("primary", f"{colors.get('primary')} 0%, {colors.get('secondary')} 100%"),
                "rounded": True,
            },
            "footer_bar": {
                "height": 4,
                "color": colors.get("primary"),
                "style": "solid",
            },
            "side_border": {
                "width": 3,
                "color": colors.get("accent"),
                "position": "left",
            },
            "corner_ribbon": {
                "enabled": False,
                "color": colors.get("accent"),
                "position": "top-right",
            },
            "divider_line": {
                "height": 1,
                "color": self._lighten_color(colors.get("text", "#1f2937"), 0.7),
                "style": "dashed",
            },
        }
    
    def _add_card_styles(self):
        """添加卡片样式配置"""
        colors = self.theme.get("colors", {})
        self.theme["card_styles"] = {
            "default": {
                "background": colors.get("background", "#ffffff"),
                "border_color": self._lighten_color(colors.get("primary", "#1e40af"), 0.5),
                "border_width": 1,
                "corner_radius": 8,
                "shadow": {
                    "enabled": True,
                    "depth": 2,
                    "blur": 8,
                    "color": "rgba(0,0,0,0.1)",
                },
                "padding": {"top": 20, "right": 24, "bottom": 20, "left": 24},
            },
            "accent": {
                "background": self._lighten_color(colors.get("primary", "#1e40af"), 0.9),
                "border_color": colors.get("primary"),
                "border_width": 2,
                "corner_radius": 8,
                "shadow": {
                    "enabled": True,
                    "depth": 3,
                    "blur": 12,
                    "color": "rgba(0,0,0,0.15)",
                },
                "padding": {"top": 24, "right": 28, "bottom": 24, "left": 28},
            },
            "kpi": {
                "background": f"linear-gradient(135deg, {colors.get('primary')}, {colors.get('secondary')})",
                "border_color": "transparent",
                "border_width": 0,
                "corner_radius": 12,
                "shadow": {
                    "enabled": True,
                    "depth": 4,
                    "blur": 16,
                    "color": f"rgba({self._hex_to_rgb(colors.get('primary'))}, 0.3)",
                },
                "padding": {"top": 28, "right": 32, "bottom": 28, "left": 32},
            },
        }
    
    def _add_icon_colors(self):
        """添加图标配色方案"""
        colors = self.theme.get("colors", {})
        self.theme["icon_colors"] = {
            "primary": colors.get("primary"),
            "secondary": colors.get("secondary"),
            "accent": colors.get("accent"),
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
            "text": colors.get("text"),
            "muted": self._lighten_color(colors.get("text", "#1f2937"), 0.5),
        }
    
    def _add_background_patterns(self):
        """添加背景图案配置"""
        self.theme["background_patterns"] = {
            "gradient_diagonal": {
                "type": "linear",
                "angle": 135,
                "colors": [
                    {"stop": 0, "color": "#ffffff"},
                    {"stop": 100, "color": self._lighten_color(self.theme.get("colors", {}).get("primary", "#1e40af"), 0.95)},
                ],
            },
            "gradient_radial": {
                "type": "radial",
                "center": "50% 50%",
                "radius": "50%",
                "colors": [
                    {"stop": 0, "color": self._lighten_color(self.theme.get("colors", {}).get("primary", "#1e40af"), 0.9)},
                    {"stop": 100, "color": "#ffffff"},
                ],
            },
            "subtle_grid": {
                "type": "grid",
                "size": 40,
                "color": self._lighten_color(self.theme.get("colors", {}).get("text", "#1f2937"), 0.85),
                "line_width": 1,
            },
            "none": {
                "type": "solid",
                "color": "#ffffff",
            },
        }
    
    @staticmethod
    def _lighten_color(hex_str: str, factor: float = 0.15) -> str:
        """提亮颜色"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) < 6:
            return "#eeeeee"
        try:
            r, g, b = int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#eeeeee"
    
    @staticmethod
    def _darken_color(hex_str: str, factor: float = 0.15) -> str:
        """变暗颜色"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) < 6:
            return "#333333"
        try:
            r, g, b = int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#333333"
    
    @staticmethod
    def _hex_to_rgb(hex_str: str) -> str:
        """将十六进制颜色转换为RGB字符串"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) >= 6:
            r, g, b = int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            return f"{r}, {g}, {b}"
        return "0, 0, 0"
    
    def get_enhanced_theme(self) -> dict:
        """获取增强后的主题"""
        return self.theme


def enhance_all_themes(input_dir: str, output_dir: str):
    """增强所有主题文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    for dirname in os.listdir(input_dir):
        dir_path = os.path.join(input_dir, dirname)
        if not os.path.isdir(dir_path):
            continue
        
        theme_path = os.path.join(dir_path, "theme.json")
        if not os.path.exists(theme_path):
            continue
        
        with open(theme_path, "r", encoding="utf-8") as f:
            theme = json.load(f)
        
        enhancer = ThemeEnhancer(theme)
        enhanced_theme = enhancer.get_enhanced_theme()
        
        output_dir_path = os.path.join(output_dir, dirname)
        os.makedirs(output_dir_path, exist_ok=True)
        output_path = os.path.join(output_dir_path, "theme.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_theme, f, ensure_ascii=False, indent=2)
        
        print(f"Enhanced: {dirname}/theme.json")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        enhance_all_themes(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python theme_enhancer.py <input_dir> <output_dir>")
