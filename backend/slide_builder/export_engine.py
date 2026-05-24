"""Export Engine - exports slide decks to PDF, PNG, and HTML formats."""
from __future__ import annotations
import os
import base64
import tempfile
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ExportEngine:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height

    def export_pdf(self, svg_contents: list[str], output_path: str,
                   slide_titles: Optional[list[str]] = None) -> str:
        tmp = tempfile.mkdtemp(prefix="pdf_export_")
        try:
            png_paths = self._svgs_to_pngs(svg_contents, tmp)
            return self._pngs_to_pdf(png_paths, output_path, slide_titles)
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def export_png(self, svg_content: str, output_path: str,
                   index: int = 0) -> str:
        tmp = tempfile.mkdtemp(prefix="png_export_")
        try:
            pngs = self._svgs_to_pngs([svg_content], tmp)
            if pngs:
                shutil.copy(pngs[0], output_path)
                return output_path
            raise RuntimeError("PNG conversion failed")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def export_html(self, svg_contents: list[str], output_path: str,
                    slide_titles: Optional[list[str]] = None,
                    slide_notes: Optional[list[str]] = None) -> str:
        html = self._build_html(svg_contents, slide_titles, slide_notes)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    def _svgs_to_pngs(self, svg_contents: list[str], tmp_dir: str) -> list[str]:
        """将SVG内容转换为PNG图片列表"""
        import re
        import os as os_module
        png_paths = []
        for i, svg in enumerate(svg_contents):
            png_path = os_module.path.join(tmp_dir, f"slide_{i:04d}.png")
            try:
                # 尝试使用 cairosvg
                import cairosvg
                cairosvg.svg2png(
                    bytestring=svg.encode("utf-8"),
                    write_to=png_path,
                    output_width=self.width,
                    output_height=self.height,
                )
                png_paths.append(png_path)
            except Exception:
                # Fallback: 使用 PIL 生成简单 PNG
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    img = Image.new("RGB", (self.width, self.height), "white")
                    draw = ImageDraw.Draw(img)
                    
                    # 查找系统中可用的中文字体
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                        "C:/Windows/Fonts/NotoSansSC-Regular.otf",  # Google Noto
                        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux 文泉驿
                        "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
                    ]
                    title_font = None
                    for font_path in font_paths:
                        if os_module.path.exists(font_path):
                            try:
                                title_font = ImageFont.truetype(font_path, 48)
                                body_font = ImageFont.truetype(font_path, 32)
                                break
                            except Exception:
                                continue
                    
                    if title_font is None:
                        # 最后尝试加载默认字体
                        title_font = ImageFont.load_default()
                        body_font = title_font
                    
                    # 尝试提取标题
                    title_match = re.search(r'font-size="(\d+)"[^>]*>([^<]+)', svg)
                    title = title_match.group(2) if title_match else f"Slide {i + 1}"
                    
                    # 尝试提取正文
                    body_matches = re.findall(r'<text[^>]*>([^<]+)</text>', svg)
                    lines = [m for m in body_matches if len(m.strip()) > 2][1:6]
                    
                    draw.text((80, 60), title, fill="#1e40af", font=title_font)
                    y = 140
                    for line in lines:
                        text = line.strip()
                        if not text:
                            continue
                        draw.text((80, y), text[:50], fill="#333333", font=body_font)
                        y += 40
                    
                    img.save(png_path, "PNG")
                    png_paths.append(png_path)
                except Exception as e:
                    # 最后Fallback: 创建空白PNG
                    from PIL import Image
                    img = Image.new("RGB", (self.width, self.height), "white")
                    img.save(png_path, "PNG")
                    png_paths.append(png_path)
        
        return png_paths

    def _pngs_to_pdf(self, png_paths: list[str], output_path: str,
                     titles: Optional[list[str]] = None) -> str:
        try:
            import img2pdf
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(png_paths))
            return output_path
        except Exception:
            return self._pngs_to_pdf_fallback(png_paths, output_path, titles)

    def _pngs_to_pdf_fallback(self, png_paths: list[str], output_path: str,
                               titles: Optional[list[str]] = None) -> str:
        from fpdf import FPDF
        pdf = FPDF(unit="pt", format=(self.width, self.height))
        for i, png_path in enumerate(png_paths):
            if i > 0:
                pdf.add_page()
            pdf.image(png_path, x=0, y=0, w=self.width, h=self.height)
            if titles and i < len(titles):
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.text(20, 20, titles[i])
        pdf.output(output_path)
        return output_path

    def _build_html(self, svg_contents: list[str],
                    titles: Optional[list[str]] = None,
                    notes: Optional[list[str]] = None) -> str:
        slides_html = []
        for i, svg in enumerate(svg_contents):
            title = titles[i] if titles and i < len(titles) else f"Slide {i+1}"
            note = notes[i] if notes and i < len(notes) else ""
            b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
            slides_html.append(f'''<div class="slide" data-index="{i}">
  <div class="slide-bg">
    <img src="data:image/svg+xml;base64,{b64}" alt="{title}" />
  </div>
  <div class="slide-notes">{note}</div>
</div>''')

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Presentation</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a2e; font-family: -apple-system, sans-serif; }}
.slide {{ display: none; width: 100vw; height: 100vh; position: relative; background: white; }}
.slide.active {{ display: flex; align-items: center; justify-content: center; }}
.slide-bg {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
.slide-bg img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.slide-notes {{ display: none; }}
.nav {{ position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); display: flex; gap: 12px; z-index: 100; }}
.nav button {{ padding: 8px 24px; background: rgba(255,255,255,0.15); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 6px; cursor: pointer; font-size: 14px; backdrop-filter: blur(8px); }}
.nav button:hover {{ background: rgba(255,255,255,0.25); }}
.counter {{ position: fixed; bottom: 24px; right: 24px; color: rgba(255,255,255,0.5); font-size: 13px; z-index: 100; }}
body.dark .slide {{ background: #1a1a2e; }}
</style>
</head>
<body>
{''.join(slides_html)}
<div class="nav"><button id="prev">&#8592; Prev</button><button id="next">Next &#8594;</button></div>
<div class="counter"><span id="current">1</span> / <span id="total">{len(svg_contents)}</span></div>
<script>
var slides = document.querySelectorAll('.slide'), current = 0;
function show(i) {{ slides.forEach(function(s) {{ s.classList.remove('active'); }}); slides[i].classList.add('active'); document.getElementById('current').textContent = i + 1; }}
document.getElementById('prev').onclick = function() {{ if (current > 0) {{ current--; show(current); }} }};
document.getElementById('next').onclick = function() {{ if (current < slides.length - 1) {{ current++; show(current); }} }};
document.addEventListener('keydown', function(e) {{ if (e.key === 'ArrowRight') {{ if (current < slides.length - 1) {{ current++; show(current); }} }} if (e.key === 'ArrowLeft') {{ if (current > 0) {{ current--; show(current); }} }} }});
show(0);
</script>
</body>
</html>'''
