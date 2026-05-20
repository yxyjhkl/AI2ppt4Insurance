"""TTS Engine - converts speaker notes to narration audio.

Uses edge-tts (Microsoft Edge TTS) with fallback to pyttsx3 (offline SAPI5).
"""
from __future__ import annotations
import os
import asyncio
import json
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

VOICES = {
    "zh-CN-XiaoxiaoNeural":  "zh-CN (Female)",
    "zh-CN-YunxiNeural":     "zh-CN (Male)",
    "zh-CN-XiaoyiNeural":    "zh-CN (Female, Young)",
    "en-US-JennyNeural":     "en-US (Female)",
    "en-US-GuyNeural":       "en-US (Male)",
    "en-GB-SoniaNeural":     "en-GB (Female)",
    "ja-JP-NanamiNeural":    "ja-JP (Female)",
    "ko-KR-SunHiNeural":     "ko-KR (Female)",
}

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
FALLBACK_VOICE = "en-US-JennyNeural"


class TTSEngine:
    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = "+0%",
                 volume: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self._edge_available = self._check_edge_tts()

    def _check_edge_tts(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    async def generate_async(self, text: str, output_path: str) -> str:
        if self._edge_available:
            try:
                return await self._generate_edge(text, output_path)
            except Exception as e:
                logger.warning(f"Edge TTS failed: {e}")
                return self._generate_offline(text, output_path)
        else:
            return self._generate_offline(text, output_path)

    async def _generate_edge(self, text: str, output_path: str) -> str:
        import edge_tts
        communicate = edge_tts.Communicate(text, self.voice)
        communicate.pitch = self.pitch
        communicate.rate = self.rate
        communicate.volume = self.volume
        await communicate.save(output_path)
        return output_path

    def _generate_offline(self, text: str, output_path: str) -> str:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.setProperty("rate", 180)
            if voices:
                voice_id = None
                for v in voices:
                    lang = v.languages[0].lower() if v.languages and len(v.languages) > 0 else ""
                    if "chinese" in v.name.lower() or "zh" in lang:
                        voice_id = v.id
                        break
                if voice_id:
                    engine.setProperty("voice", voice_id)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            return output_path
        except ImportError:
            logger.error("pyttsx3 not available, writing placeholder")
            with open(output_path + ".txt", "w", encoding="utf-8") as f:
                f.write(text)
            return output_path + ".txt"

    async def generate_slide_audio_async(self, slide_notes: list[tuple[int, str]],
                                          output_dir: str) -> list[dict]:
        """Generate one audio file per slide with speaker notes."""
        import asyncio
        results = []
        os.makedirs(output_dir, exist_ok=True)
        tasks = []
        for page_num, notes_text in slide_notes:
            if not notes_text.strip():
                continue
            filename = f"slide_{page_num:03d}.mp3"
            filepath = os.path.join(output_dir, filename)
            tasks.append(self._generate_single_audio(page_num, notes_text, filepath))

        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for r in completed:
                if isinstance(r, dict):
                    results.append(r)
        return results

    async def _generate_single_audio(self, page_num: int, text: str, filepath: str) -> dict:
        try:
            await self.generate_async(text, filepath)
            return {"page": page_num, "file": filepath}
        except Exception as e:
            logger.error(f"TTS failed for slide {page_num}: {e}")
            return {"page": page_num, "file": "", "error": str(e)}

    @staticmethod
    async def list_voices_async() -> list[dict]:
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return [
                {"name": v["Name"], "locale": v["Locale"],
                 "gender": v["Gender"], "friendly": VOICES.get(v["Name"], v["ShortName"])}
                for v in voices if v["Name"] in VOICES or len(voices) < 20
            ]
        except Exception:
            return [{"name": DEFAULT_VOICE, "locale": "zh-CN",
                     "gender": "Female", "friendly": "Chinese (Default)"}]

    @staticmethod
    def list_voices() -> list[dict]:
        return [{"name": DEFAULT_VOICE, "locale": "zh-CN",
                 "gender": "Female", "friendly": "Chinese (Default)"}]
