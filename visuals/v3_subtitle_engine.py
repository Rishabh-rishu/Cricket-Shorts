"""
Cricket Shorts Engine V3 - Subtitle & Devanagari Typography Engine
Generates broadcast-grade ASS & SRT subtitles:
- 3 to 5 word rapid bursts for high retention
- Shaper-verified Noto Sans Devanagari Bold
- Safe 9:16 mobile margins (MarginV=270)
- Highlight styling for numbers and cricket keywords
"""

import os
import re
from typing import List, Dict, Any

FONT_NAME = "Noto Sans Devanagari"
FONT_SIZE = 52
MARGIN_BOTTOM = 270  # Pixels from bottom (above YouTube shorts action buttons)


class V3SubtitleEngine:
    @classmethod
    def chunk_boundaries(cls, boundaries: List[Dict[str, Any]], max_words: int = 4) -> List[Dict[str, Any]]:
        """
        Splits speech boundaries into rapid 3-4 word bursts.
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

            total_dur = max(0.4, item["end"] - item["start"])
            total_words = len(words)
            curr_start = item["start"]

            for i in range(0, total_words, max_words):
                chunk = words[i:i + max_words]
                chunk_dur = total_dur * (len(chunk) / total_words)
                chunk_end = curr_start + chunk_dur
                refined.append({
                    "start": round(curr_start, 2),
                    "end": round(chunk_end, 2),
                    "text": " ".join(chunk)
                })
                curr_start = chunk_end

        return refined

    @classmethod
    def generate_ass(cls, boundaries: List[Dict[str, Any]], output_path: str) -> str:
        """
        Creates ASS subtitle file with yellow/gold highlights on key terms.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        chunks = cls.chunk_boundaries(boundaries, max_words=4)

        header = f"""[Script Info]
Title: Cricket Raaz V3 Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},{FONT_SIZE},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.8,1.8,2,60,60,{MARGIN_BOTTOM},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for c in chunks:
            start_str = cls._sec_to_ass(c["start"])
            end_str = cls._sec_to_ass(c["end"])
            text = cls._highlight(c["text"])
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events) + "\n")

        return output_path

    @classmethod
    def _sec_to_ass(cls, sec: float) -> str:
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        secs = int(sec % 60)
        csec = int(round((sec - int(sec)) * 100))
        if csec >= 100:
            csec = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{csec:02d}"

    @classmethod
    def _highlight(cls, text: str) -> str:
        # Highlight digits (e.g. 1, 2, 3, 36, 174, 800) in gold (&H0038D1F7&)
        text = re.sub(r'(\b\d+[\w]*\b)', r'{\\c&H0038D1F7&}\1{\\c&H00FFFFFF&}', text)
        # Highlight key words like 'वर्ल्ड कप', 'रिकॉर्ड', 'विकेट', 'शतक'
        keywords = ["वर्ल्ड कप", "रिकॉर्ड", "विकेट", "शतक", "टेस्ट", "IPL", "हैट्रिक", "हैरान"]
        for kw in keywords:
            if kw in text and not "{\\c" in text:
                text = text.replace(kw, f"{{\\c&H0038D1F7&}}{kw}{{\\c&H00FFFFFF&}}")
        return text
