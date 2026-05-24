"""模板预览生成器 - 生成带有丰富视觉效果的模板预览"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

import json
import os


class TemplatePreviewGenerator:
    """生成模板预览PPT"""
    
    def __init__(self, theme):
        self.theme = theme
        self.colors = theme.get("colors", {})
        self.gradients = theme.get("gradients", {})
        self.decorations = theme.get("decorations", {})
        self.card_styles = theme.get("card_styles", {})
        
    def _hex_to_rgb(self, hex_str):
        if not hex_str or hex_str.lower() == "transparent":
            return RGBColor(0x33, 0x33, 0x33)
        hex_str = hex_str.lstrip("#")
        if len(hex_str) < 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_str):
            return RGBColor(0x33, 0x33, 0x33)
        return RGBColor(int(hex_str[:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    
    def generate_preview(self) -> bytes:
        """生成预览PPT"""
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        
        self._add_cover_slide(prs)
        self._add_color_palette_slide(prs)
        self._add_card_styles_slide(prs)
        self._add_decorations_slide(prs)
        self._add_gradient_showcase_slide(prs)
        self._add_sample_content_slide(prs)
        
        output = io.BytesIO()
        prs.save(output)
        return output.getvalue()
    
    def _add_cover_slide(self, prs):
        """添加封面预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        
        shapes = slide.shapes
        
        header_bar = shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                     left=0, top=0,
                                     width=prs.slide_width,
                                     height=Emu(8 * 9144))
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary", "#1e40af"))
        header_bar.line.fill.background()
        
        title_shape = shapes.title
        title_shape.text = self.theme.get("name", "Template Preview")
        title_shape.text_frame.paragraphs[0].font.size = Pt(44)
        title_shape.text_frame.paragraphs[0].font.color.rgb = self._hex_to_rgb(self.colors.get("text", "#1f2937"))
        
        subtitle = shapes.add_textbox(left=Inches(1), top=Inches(4),
                                     width=prs.slide_width - Inches(2), height=Inches(2))
        subtitle.text = self.theme.get("description", "")
        subtitle.text_frame.paragraphs[0].font.size = Pt(18)
        subtitle.text_frame.paragraphs[0].font.color.rgb = self._hex_to_rgb(self.colors.get("text", "#1f2937"))
        subtitle.text_frame.paragraphs[0].font.italic = True
        
        footer_bar = shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                     left=0, top=prs.slide_height - Emu(4 * 9144),
                                     width=prs.slide_width,
                                     height=Emu(4 * 9144))
        footer_bar.fill.solid()
        footer_bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("accent", "#f59e0b"))
        footer_bar.line.fill.background()
    
    def _add_color_palette_slide(self, prs):
        """添加配色方案预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = "配色方案"
        
        colors = self.colors
        color_items = [
            ("主色调", colors.get("primary")),
            ("辅助色", colors.get("secondary")),
            ("强调色", colors.get("accent")),
            ("背景色", colors.get("background")),
            ("文字色", colors.get("text")),
            ("浅背景", colors.get("light-bg")),
        ]
        
        start_y = Inches(1.5)
        item_height = Inches(0.8)
        
        for i, (name, hex_color) in enumerate(color_items):
            y = start_y + i * item_height
            
            color_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                              left=Inches(1), top=y,
                                              width=Inches(3), height=Inches(0.6))
            color_box.fill.solid()
            color_box.fill.fore_color.rgb = self._hex_to_rgb(hex_color)
            color_box.line.fill.background()
            
            label = slide.shapes.add_textbox(left=Inches(4.5), top=y,
                                             width=Inches(4), height=Inches(0.6))
            label.text = f"{name}: {hex_color}"
            label.text_frame.paragraphs[0].font.size = Pt(14)
            label.text_frame.paragraphs[0].font.color.rgb = self._hex_to_rgb(self.colors.get("text"))
    
    def _add_card_styles_slide(self, prs):
        """添加卡片样式预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = "卡片样式"
        
        card_types = ["default", "accent", "kpi"]
        card_width = Inches(4)
        card_height = Inches(2.5)
        spacing = Inches(0.5)
        
        for i, card_type in enumerate(card_types):
            style = self.card_styles.get(card_type, {})
            x = Inches(0.5) + i * (card_width + spacing)
            y = Inches(2)
            
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                         left=x, top=y,
                                         width=card_width, height=card_height)
            
            bg_color = style.get("background", "#ffffff")
            if "gradient" in bg_color:
                card.fill.solid()
                card.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary"))
            else:
                card.fill.solid()
                card.fill.fore_color.rgb = self._hex_to_rgb(bg_color)
            
            border_color = style.get("border_color", "#ccc")
            card.line.color.rgb = self._hex_to_rgb(border_color)
            card.line.width = Emu(style.get("border_width", 1) * 9144)
            
            card.text = card_type.capitalize() + " Card"
            card.text_frame.paragraphs[0].font.size = Pt(16)
            card.text_frame.paragraphs[0].font.bold = True
            card.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    
    def _add_decorations_slide(self, prs):
        """添加装饰元素预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = "装饰元素"
        
        header_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                           left=0, top=0,
                                           width=prs.slide_width,
                                           height=Emu(8 * 9144))
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary"))
        header_bar.line.fill.background()
        
        side_border = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                             left=0, top=Emu(8 * 9144),
                                             width=Emu(3 * 9144),
                                             height=prs.slide_height - Emu(8 * 9144))
        side_border.fill.solid()
        side_border.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("accent"))
        side_border.line.fill.background()
        
        divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                         left=Inches(1), top=Inches(3),
                                         width=prs.slide_width - Inches(2),
                                         height=Emu(1 * 9144))
        divider.fill.solid()
        divider.fill.fore_color.rgb = self._hex_to_rgb("#ddd")
        divider.line.fill.background()
        
        label = slide.shapes.add_textbox(left=Inches(2), top=Inches(3.2),
                                         width=Inches(6), height=Inches(0.5))
        label.text = "分隔线示例"
        label.text_frame.paragraphs[0].font.size = Pt(14)
    
    def _add_gradient_showcase_slide(self, prs):
        """添加渐变效果预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = "渐变效果"
        
        gradients = self.gradients
        gradient_names = ["primary", "accent", "hero", "soft"]
        
        for i, name in enumerate(gradient_names):
            x = Inches(1)
            y = Inches(2 + i * 1.2)
            
            gradient_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                                  left=x, top=y,
                                                  width=prs.slide_width - Inches(2),
                                                  height=Inches(0.8))
            gradient_box.fill.solid()
            
            if i == 0:
                gradient_box.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary"))
            elif i == 1:
                gradient_box.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("accent"))
            elif i == 2:
                gradient_box.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary"))
            else:
                gradient_box.fill.fore_color.rgb = self._hex_to_rgb("#e8ebf7")
            
            label = slide.shapes.add_textbox(left=Inches(1), top=y + Inches(0.9),
                                             width=Inches(4), height=Inches(0.4))
            label.text = name.capitalize() + " Gradient"
            label.text_frame.paragraphs[0].font.size = Pt(12)
    
    def _add_sample_content_slide(self, prs):
        """添加示例内容预览"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        
        title = slide.shapes.title
        title.text = "示例内容"
        
        kpi_cards = [
            ("收入", "¥1,234万", "+12.5%"),
            ("客户数", "5,678人", "+8.3%"),
            ("转化率", "23.5%", "+3.2%"),
        ]
        
        card_width = Inches(4)
        card_height = Inches(2)
        
        for i, (label, value, change) in enumerate(kpi_cards):
            x = Inches(0.5) + i * (card_width + Inches(0.2))
            y = Inches(2)
            
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                         left=x, top=y,
                                         width=card_width, height=card_height)
            card.fill.solid()
            card.fill.fore_color.rgb = self._hex_to_rgb(self.colors.get("primary"))
            card.line.fill.background()
            
            tf = card.text_frame
            tf.clear()
            
            p = tf.add_paragraph()
            p.text = label
            p.font.size = Pt(12)
            p.font.color.rgb = self._hex_to_rgb("#ffffff")
            
            p = tf.add_paragraph()
            p.text = value
            p.font.size = Pt(24)
            p.font.bold = True
            p.font.color.rgb = self._hex_to_rgb("#ffffff")
            
            p = tf.add_paragraph()
            p.text = change
            p.font.size = Pt(12)
            p.font.color.rgb = self._hex_to_rgb("#10b981")


import io

def generate_template_preview(theme_path: str) -> bytes:
    """生成模板预览"""
    with open(theme_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    
    previewer = TemplatePreviewGenerator(theme)
    return previewer.generate_preview()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        theme_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) >= 3 else "template_preview.pptx"
        
        preview_bytes = generate_template_preview(theme_path)
        with open(output_path, "wb") as f:
            f.write(preview_bytes)
        print(f"Preview saved to: {output_path}")
    else:
        print("Usage: python template_previewer.py <theme.json> [output.pptx]")