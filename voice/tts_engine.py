"""
Unified Hindi Text-to-Speech Engine
Supports:
1. Primary: Edge-TTS (Deep male neural voice 'hi-IN-MadhurNeural' with rate/pitch control)
2. Fallback: Piper TTS (Local offline ONNX model 'hi_IN-rohan-medium')
"""

import os
import asyncio
import subprocess
import logging
from typing import Tuple, List, Dict, Any
import edge_tts

logger = logging.getLogger("cricket_shorts.voice")


class TTSEngine:
    def __init__(
        self,
        engine: str = "edge-tts",
        voice: str = "hi-IN-MadhurNeural",
        rate: str = "+20%",
        pitch: str = "-2Hz",
        piper_model: str = "assets/models/hi_IN-rohan-medium.onnx",
        piper_config: str = "assets/models/hi_IN-rohan-medium.onnx.json"
    ):
        self.engine = engine
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.piper_model = piper_model
        self.piper_config = piper_config

    def generate_speech(self, text: str, output_audio_path: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Generates spoken audio and timing boundaries.
        Returns: (success, final_audio_path, boundaries_list)
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)

        if self.engine == "edge-tts":
            try:
                boundaries = asyncio.run(self._synthesize_edge_tts(text, output_audio_path))
                logger.info(f"Edge-TTS synthesized successfully: {output_audio_path}")
                return True, output_audio_path, boundaries
            except Exception as e:
                logger.error(f"Edge-TTS failed: {e}. Falling back to local Piper TTS.")

        # Fallback to local Piper TTS
        try:
            boundaries = self._synthesize_piper(text, output_audio_path)
            logger.info(f"Piper TTS synthesized successfully: {output_audio_path}")
            return True, output_audio_path, boundaries
        except Exception as e:
            logger.error(f"Piper TTS failed: {e}")
            return False, "", []

    async def _synthesize_edge_tts(self, text: str, output_path: str) -> List[Dict[str, Any]]:
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )

        boundaries = []
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    start_sec = chunk["offset"] / 10000000.0
                    duration_sec = chunk["duration"] / 10000000.0
                    boundaries.append({
                        "start": start_sec,
                        "end": start_sec + duration_sec,
                        "text": chunk["text"].strip()
                    })

        return boundaries

    def _synthesize_piper(self, text: str, output_path: str) -> List[Dict[str, Any]]:
        # Piper outputs wav directly
        wav_path = output_path if output_path.endswith(".wav") else output_path.rsplit(".", 1)[0] + ".wav"
        cmd = [
            "piper",
            "-m", self.piper_model,
            "-c", self.piper_config,
            "-f", wav_path,
            "--length-scale", "0.83" # 1.2x speed
        ]
        # Run piper process
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=text)
        if process.returncode != 0:
            raise RuntimeError(f"Piper error: {stderr}")

        # Basic sentence estimation if using Piper
        sentences = [s.strip() for s in text.replace('?', '।').replace('!', '।').split('।') if s.strip()]
        boundaries = []
        # Estimate ~0.25s per word
        curr = 0.1
        for s in sentences:
            dur = max(1.5, len(s.split()) * 0.28)
            boundaries.append({"start": curr, "end": curr + dur, "text": s})
            curr += dur + 0.1

        return boundaries
