"""Video Exporter - renders slide decks to MP4 video with optional TTS narration.

Pipeline: SVG → PNG (cairosvg) → MP4 (FFmpeg) + TTS audio overlay.
"""
from __future__ import annotations
import os
import re
import subprocess
import tempfile
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def svgs_to_pngs(svg_contents: list[str], temp_dir: str, width: int, height: int,
                  svg_to_png_one=None, fallback_png=None) -> list[str]:
    png_paths = []
    for i, svg in enumerate(svg_contents):
        png_path = os.path.join(temp_dir, f"slide_{i:04d}.png")
        if svg_to_png_one and svg_to_png_one(svg, png_path, i):
            png_paths.append(png_path)
        elif fallback_png:
            png_paths.append(fallback_png(svg, png_path, i))
        else:
            png_paths.append(png_path)
    return png_paths


class VideoExporter:
    OUTPUT_FORMATS = {
        "mp4":  {"codec": "libx264", "ext": ".mp4"},
        "webm": {"codec": "libvpx",  "ext": ".webm"},
    }

    def __init__(self, fps: int = 30, seconds_per_slide: int = 5,
                 width: int = 1920, height: int = 1080,
                 bg_color: str = "white"):
        self.fps = fps
        self.seconds_per_slide = seconds_per_slide
        self.width = width
        self.height = height
        self.bg_color = bg_color

    def export(self, svg_contents: list[str], output_path: str,
               audio_files: Optional[list[dict]] = None,
               format: str = "mp4") -> str:
        fmt_info = self.OUTPUT_FORMATS.get(format, self.OUTPUT_FORMATS["mp4"])
        if not output_path.lower().endswith(fmt_info["ext"]):
            output_path += fmt_info["ext"]

        temp_dir = tempfile.mkdtemp(prefix="video_export_")
        try:
            png_paths = self._svgs_to_pngs(svg_contents, temp_dir)
            return self._assemble_video(png_paths, output_path, audio_files,
                                        fmt_info["codec"], temp_dir)
        except Exception as e:
            logger.error(f"Video export failed: {e}")
            raise
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _svgs_to_pngs(self, svg_contents: list[str], temp_dir: str) -> list[str]:
        return svgs_to_pngs(svg_contents, temp_dir, self.width, self.height,
                            self._svg_to_png_one, self._fallback_png)

    def _svg_to_png_one(self, svg: str, png_path: str, idx: int) -> bool:
        try:
            import cairosvg
            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                write_to=png_path,
                output_width=self.width,
                output_height=self.height,
            )
            return True
        except Exception as e:
            logger.warning(f"cairosvg failed for slide {idx}: {e}")
            return False

    def _fallback_png(self, svg: str, png_path: str, idx: int) -> str:
        try:
            from PIL import Image, ImageDraw, ImageFont
            import re

            img = Image.new("RGB", (self.width, self.height), "white")
            draw = ImageDraw.Draw(img)

            title_match = re.search(r"font-size=\"(\d+)\"[^>]*>([^<]+)", svg)
            title = title_match.group(2) if title_match else f"Slide {idx + 1}"
            body_match = re.findall(r'<text[^>]*>([^<]+)</text>', svg)
            lines = body_match[1:6] if len(body_match) > 1 else []

            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                body_font = ImageFont.truetype("arial.ttf", 32)
            except (IOError, OSError):
                title_font = ImageFont.load_default()
                body_font = title_font

            draw.text((80, 60), title, fill="#1e40af", font=title_font)
            y = 140
            for line in lines:
                text = line.strip() if isinstance(line, str) else line
                if not text:
                    continue
                draw.text((80, y), text, fill="#333333", font=body_font)
                y += 40

            img.save(png_path, "PNG")
        except Exception as e:
            logger.error(f"Fallback PNG failed for slide {idx}: {e}")
            img = Image.new("RGB", (self.width, self.height), "white")
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((self.width // 4, self.height // 2),
                      f"Slide {idx + 1}", fill="#333333")
            img.save(png_path, "PNG")
        return png_path

    def _assemble_video(self, png_paths: list[str], output_path: str,
                        audio_files: Optional[list[dict]],
                        codec: str, temp_dir: str) -> str:
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Install FFmpeg to export video.")

        frame_count = len(png_paths) * self.fps * self.seconds_per_slide

        if audio_files and len(audio_files) > 0:
            concat_file = os.path.join(temp_dir, "audio_concat.txt")
            audio_path = os.path.join(temp_dir, "narration.mp3")
            self._concat_audio(audio_files, concat_file, audio_path)

            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", os.path.join(temp_dir, "slide_%04d.png"),
                "-i", audio_path,
                "-c:v", codec,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                "-vf", f"pad=ceil(iw/2)*2:ceil(ih/2)*2",
                output_path,
            ]
        else:
            input_pattern = os.path.join(temp_dir, "slide_%04d.png")
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-c:v", codec,
                "-pix_fmt", "yuv420p",
                "-vf", f"fps={self.fps},pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-t", str(len(png_paths) * self.seconds_per_slide),
                output_path,
            ]

        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return output_path

    def _concat_audio(self, audio_files: list[dict],
                      concat_file: str, output_path: str):
        import shlex
        with open(concat_file, "w", encoding="utf-8") as f:
            for af in audio_files:
                file_path = af.get("file", "")
                if not file_path or not os.path.exists(file_path):
                    logger.warning(f"Audio file not found: {file_path}")
                    continue
                escaped = file_path.replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        result = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file, "-c", "copy", output_path
        ], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Audio concat failed: {result.stderr}")

    def _check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(["ffmpeg", "-version"],
                                    capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
