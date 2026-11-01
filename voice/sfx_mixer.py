"""
Cinematic Sound Design & SFX Mixing Engine
Layers voice narration with subtle sports tension background music
and precise SFX triggers (bat hits, crowd cheers, whooshes, dramatic impacts)
aligned with scene transition timestamps.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("cricket_shorts.sfx")

SFX_DIR = "assets/sfx"


class SFXMixer:
    @classmethod
    def mix_soundtrack_with_sfx(
        cls,
        voice_path: str,
        storyboard: List[Dict[str, Any]],
        output_mixed_path: str,
        bgm_volume: float = 0.08
    ) -> Tuple[bool, str]:
        """
        Mixes:
        1. Voice track (normalized primary audio)
        2. Subtle tension drone/BGM (lowered)
        3. SFX at scene transition timestamps via adelay
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_mixed_path)), exist_ok=True)

        # Inspect voice duration
        cmd_dur = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            voice_path
        ]
        res_d = subprocess.run(cmd_dur, stdout=subprocess.PIPE, text=True)
        try:
            voice_dur = float(res_d.stdout.strip())
        except Exception:
            voice_dur = 35.0

        # Build FFmpeg command inputs and filtergraph
        inputs = [
            "-i", voice_path,
            "-f", "lavfi", "-i", f"anoisesrc=d={voice_dur+1}:c=pink:r=44100,lowpass=f=240,volume={bgm_volume*1.2}[noise];sine=f=58:d={voice_dur+1},volume={bgm_volume*0.8}[sub];[noise][sub]amix=inputs=2"
        ]

        filter_parts = ["[0:a]volume=1.0[voice]", "[1:a]volume=1.0[bgm]"]
        mix_inputs = ["[voice]", "[bgm]"]
        input_idx = 2

        for scene in storyboard:
            sfx_name = scene.get("sfx_trigger")
            if not sfx_name:
                continue

            sfx_file = os.path.join(SFX_DIR, f"{sfx_name}.aac")
            if not os.path.exists(sfx_file):
                continue

            start_sec = max(0.0, scene.get("start_sec", 0.0))
            delay_ms = int(start_sec * 1000)

            inputs.extend(["-i", sfx_file])
            sfx_vol = 0.35 if sfx_name in ("transition_whoosh", "bat_hit") else 0.25
            filter_parts.append(
                f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume={sfx_vol}[sfx_{input_idx}]"
            )
            mix_inputs.append(f"[sfx_{input_idx}]")
            input_idx += 1

        all_filter = ";".join(filter_parts) + f";{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[out]"

        cmd_mix = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", all_filter,
            "-map", "[out]",
            "-c:a", "aac",
            "-b:a", "192k",
            output_mixed_path
        ]

        logger.info(f"Mixing {input_idx - 2} SFX cues into sound design bed: {output_mixed_path}")
        res_m = subprocess.run(cmd_mix, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_m.returncode != 0:
            logger.warning(f"SFX mix warning: {res_m.stderr}. Using clean voice audio.")
            return False, voice_path

        return True, output_mixed_path
