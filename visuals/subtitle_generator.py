"""
Synchronized Hindi Subtitle Generator
Generates advanced ASS (Advanced SubStation Alpha) and SRT subtitles
with custom Devanagari styling, yellow/gold keyword highlighting, and mobile-safe boundaries.
"""

import os
import re
from typing import List, Dict, Any


class SubtitleGenerator:
    DEFAULT_FONT = "Noto Sans Devanagari"
    FONT_SIZE = 56
    MARGIN_BOTTOM = 350 # Pixels from bottom (above YouTube shorts UI)

    @classmethod
    def generate_ass(
        cls,
        boundaries: List[Dict[str, Any]],
        output_ass_path: str,
        font_name: str = DEFAULT_FONT,
        font_size: int = FONT_SIZE
    ) -> str:
        """
        Creates an ASS subtitle file formatted with bold Devanagari styling,
        drop shadow, and yellow highlight color for key cricket terms.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_ass_path)), exist_ok=True)

        ass_header = f"""[Script Info]
Title: Cricket Facts Factory Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.8,1.8,2,60,60,{cls.MARGIN_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for item in boundaries:
            start_str = cls._format_ass_time(item["start"])
            end_str = cls._format_ass_time(item["end"])
            text = item["text"]

            # Highlight numbers, records, and key English cricket keywords in Gold/Yellow (&H00D7FF&)
            styled_text = cls._highlight_keywords(text)

            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{styled_text}")

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        return output_ass_path

    @classmethod
    def generate_srt(cls, boundaries: List[Dict[str, Any]], output_srt_path: str) -> str:
        """Generates standard SRT subtitles."""
        os.makedirs(os.path.dirname(os.path.abspath(output_srt_path)), exist_ok=True)
        lines = []
        for idx, item in enumerate(boundaries, 1):
            s_str = cls._format_srt_time(item["start"])
            e_str = cls._format_srt_time(item["end"])
            lines.append(f"{idx}\n{s_str} --> {e_str}\n{item['text']}\n")

        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return output_srt_path

    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int(round((seconds - int(seconds)) * 1000))
        if millisecs >= 1000:
            millisecs = 999
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    @staticmethod
    def _highlight_keywords(text: str) -> str:
        r"""
        Wraps numbers and high-impact cricket terms in ASS yellow color tags {\c&H00D7FF&}...{\c&HFFFFFF&}.
        """
        # Split words while preserving punctuation
        words = text.split()
        styled_words = []
        # Cricket highlight targets
        highlight_targets = [
            "5", "6", "35", "36", "60", "413", "800", "229", "1975", "1987", "1997", "1999", "2009", "2022", "2023",
            "पेनल्टी", "हेलमेट", "डेड", "टाइम", "आउट", "गावस्कर", "तेंदुलकर", "रोहित", "धोनी", "बुमराह", "मुरलीधरन",
            "penalty", "helmet", "ipl", "icc", "mcc", "law", "record", "world cup"
        ]

        for w in words:
            clean_w = re.sub(r'[^\w\s]', '', w).lower()
            if clean_w in highlight_targets or re.match(r'^\d+$', clean_w):
                styled_words.append(f"{{\\c&H00D7FF&}}{w}{{\\c&HFFFFFF&}}")
            else:
                styled_words.append(w)

        return " ".join(styled_words)
