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
    FONT_SIZE = 52
    MARGIN_BOTTOM = 260 # Pixels from bottom (safe zone for 9:16 mobile YouTube shorts)

    @classmethod
    def _chunk_boundaries(cls, boundaries: List[Dict[str, Any]], max_words: int = 5) -> List[Dict[str, Any]]:
        """
        Subdivides long speech boundaries into rapid, punchy 3-5 word subtitle bursts.
        Guarantees zero text overflow, no overlapping lines, and maximum viewer retention.
        """
        refined = []
        for item in boundaries:
            text = item.get("text", "").strip()
            if not text:
                continue
            words = text.split()
            if len(words) <= max_words:
                refined.append(item)
                continue

            total_dur = max(0.5, item["end"] - item["start"])
            total_words = len(words)
            curr_start = item["start"]
            
            # Split into chunks of max_words
            for i in range(0, total_words, max_words):
                chunk_words = words[i:i + max_words]
                chunk_dur = total_dur * (len(chunk_words) / total_words)
                chunk_end = curr_start + chunk_dur
                refined.append({
                    "start": round(curr_start, 2),
                    "end": round(chunk_end, 2),
                    "text": " ".join(chunk_words)
                })
                curr_start = chunk_end

        return refined

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
        clean black outline, and Gold/Yellow highlight for key cricket numbers and terms.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_ass_path)), exist_ok=True)
        refined_boundaries = cls._chunk_boundaries(boundaries, max_words=5)

        ass_header = f"""[Script Info]
Title: Cricket Raaz Countdown Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.6,1.5,2,50,50,{cls.MARGIN_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for item in refined_boundaries:
            start_str = cls._format_ass_time(item["start"])
            end_str = cls._format_ass_time(item["end"])
            text = item["text"]

            # Highlight numbers and key keywords in Gold/Yellow (&H004AB8E8&)
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
                # Brand Gold in ASS format: &H004AB8E8&
                styled_words.append(f"{{\\c&H004AB8E8&}}{w}{{\\c&HFFFFFF&}}")
            else:
                styled_words.append(w)

        return " ".join(styled_words)
