"""
Cricket Shorts Engine V3 - Master Cinematic Video Engine
Coordinates 3-Connected-Facts documentary production:
- 8-Segment dynamic pacing (Hook -> Fact 1 Card/Action -> Fact 2 Card/Action -> Fact 3 Card/Action -> Outro)
- Ken Burns pan/zoom on broadcast player cards
- Pexels moving footage with lower-third overlays
- Multi-track sound design (voice normalized to -16 LUFS, tension drone, acoustic SFX)
- Shaper-verified Noto Sans Devanagari subtitles
"""

import os
import re
import json
import logging
import subprocess
from typing import Dict, Any, List, Tuple
from visuals.v3_asset_provider import V3AssetProvider
from visuals.v3_subtitle_engine import V3SubtitleEngine
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor
from voice.sfx_mixer import SFXMixer
from qc.video_qc import VideoQC
from scripts.generate_script_v3 import ScriptGeneratorV3

logger = logging.getLogger("cricket_shorts.v3_engine")


class V3CinematicEngine:
    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    FONTS_DIR = "/usr/share/fonts/truetype/noto"

    @classmethod
    def render_v3_short(
        cls,
        bundle: Dict[str, Any],
        output_video_path: str,
        temp_dir: str,
        pexels_key: str = "",
        tts_rate: str = "+12%"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Renders complete 3-Connected-Facts documentary short.
        Returns: (success, video_path, metadata_report)
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        asset_provider = V3AssetProvider(pexels_key=pexels_key)
        tts = TTSEngine(voice="hi-IN-MadhurNeural", rate=tts_rate)

        # Step 1: Prepare Narration Script
        full_narration = ScriptGeneratorV3.assemble_full_narration(bundle)
        logger.info(f"V3 Narration ({len(full_narration.split())} words): '{full_narration[:80]}...'")

        # Step 2: Voice Synthesis & Boundary Timing
        raw_voice_path = os.path.join(temp_dir, "raw_voice.mp3")
        tts_ok, _, raw_boundaries = tts.generate_speech(full_narration, raw_voice_path)
        if not tts_ok:
            return False, "", {"error": "TTS synthesis failed"}

        # Step 3: Loudness Normalization to -16 LUFS
        norm_voice_path = os.path.join(temp_dir, "voice_normalized.aac")
        norm_ok, _, voice_dur = AudioProcessor.process_voice_audio(raw_voice_path, norm_voice_path, target_lufs=-16.0)
        if not norm_ok:
            norm_voice_path = raw_voice_path
            voice_dur = AudioProcessor.get_audio_duration(raw_voice_path)

        logger.info(f"Voice narration ready. Total duration: {voice_dur:.2f}s")

        # Step 4: Map Segment Timestamps
        # Narration structure: Hook -> Fact 1 -> Fact 2 -> Fact 3 -> Outro
        parts = [bundle["hook_narration"]] + [f["narration"] for f in bundle["facts"]] + [bundle["outro_narration"]]
        char_counts = [len(p) for p in parts]
        total_chars = sum(char_counts)

        # Distribute total voice duration proportionally by character count
        proportions = [c / total_chars for c in char_counts]
        durations = [p * voice_dur for p in proportions]

        t_hook = durations[0]
        dur_f1 = durations[1]
        dur_f2 = durations[2]
        dur_f3 = durations[3]
        dur_outro = durations[4]

        # Break each fact into Card (45%) and Moving Action Footage (55%)
        scenes = [
            # Scene 0: Hook
            {
                "scene_idx": 0,
                "type": "hook",
                "duration": round(t_hook, 2),
                "data": bundle,
                "sfx": "transition_whoosh"
            },
            # Scene 1: Fact 1 Presentation Card (Ken Burns)
            {
                "scene_idx": 1,
                "type": "fact_card",
                "duration": round(dur_f1 * 0.45, 2),
                "data": bundle["facts"][0],
                "sfx": "dramatic_boom"
            },
            # Scene 2: Fact 1 Action Footage (Moving video + lower-third)
            {
                "scene_idx": 2,
                "type": "footage_overlay",
                "duration": round(dur_f1 * 0.55, 2),
                "data": bundle["facts"][0],
                "sfx": "bat_hit"
            },
            # Scene 3: Fact 2 Presentation Card (Ken Burns)
            {
                "scene_idx": 3,
                "type": "fact_card",
                "duration": round(dur_f2 * 0.45, 2),
                "data": bundle["facts"][1],
                "sfx": "transition_whoosh"
            },
            # Scene 4: Fact 2 Action Footage (Moving video + lower-third)
            {
                "scene_idx": 4,
                "type": "footage_overlay",
                "duration": round(dur_f2 * 0.55, 2),
                "data": bundle["facts"][1],
                "sfx": "dramatic_boom"
            },
            # Scene 5: Fact 3 Presentation Card (Ken Burns Climax)
            {
                "scene_idx": 5,
                "type": "fact_card",
                "duration": round(dur_f3 * 0.45, 2),
                "data": bundle["facts"][2],
                "sfx": "dramatic_boom"
            },
            # Scene 6: Fact 3 Action Footage (Moving video + lower-third)
            {
                "scene_idx": 6,
                "type": "footage_overlay",
                "duration": round(dur_f3 * 0.55, 2),
                "data": bundle["facts"][2],
                "sfx": "bat_hit"
            },
            # Scene 7: Outro CTA (Moving crowd cheer + Subscribe Card)
            {
                "scene_idx": 7,
                "type": "outro",
                "duration": round(dur_outro, 2),
                "data": bundle,
                "sfx": "stadium_cheer"
            }
        ]

        # Calculate exact start timestamps for SFX cues
        curr_time = 0.0
        storyboard_sfx = []
        for s in scenes:
            s["start_sec"] = curr_time
            storyboard_sfx.append({
                "scene_index": s["scene_idx"],
                "start_sec": curr_time,
                "sfx_trigger": s["sfx"]
            })
            curr_time += s["duration"]

        logger.info(f"Planned 8 cinematic scenes. Total video duration: {curr_time:.2f}s")

        # Step 5: Render Each Video Segment
        rendered_clips = []
        for s in scenes:
            clip_path = os.path.join(temp_dir, f"segment_{s['scene_idx']}.mp4")
            logger.info(f"Rendering Segment {s['scene_idx']} ({s['type']}, {s['duration']}s)...")
            ok, _ = asset_provider.generate_scene_video(
                scene_type=s["type"],
                scene_data=s["data"],
                duration=s["duration"],
                output_clip_path=clip_path,
                temp_dir=temp_dir
            )
            if not ok:
                logger.error(f"Failed rendering segment {s['scene_idx']}")
                return False, "", {"error": f"Failed segment {s['scene_idx']}"}
            rendered_clips.append(clip_path)

        # Step 6: Mix Sound Design (Voice + Tension Bed + SFX Cues)
        soundtrack_path = os.path.join(temp_dir, "soundtrack_v3.aac")
        SFXMixer.mix_soundtrack_with_sfx(
            voice_path=norm_voice_path,
            storyboard=storyboard_sfx,
            output_mixed_path=soundtrack_path,
            bgm_volume=0.08
        )

        # Step 7: Subtitle Generation (ASS with Devanagari Gold Highlights)
        ass_path = os.path.join(temp_dir, "subtitles_v3.ass")
        V3SubtitleEngine.generate_ass(raw_boundaries, ass_path)

        # Step 8: Build Concat Manifest
        manifest_path = os.path.join(temp_dir, "concat_manifest.txt")
        with open(manifest_path, "w") as f:
            for c in rendered_clips:
                f.write(f"file '{os.path.abspath(c)}'\n")

        # Step 9: Final Assembly with FFmpeg
        escaped_ass = ass_path.replace(":", "\\:").replace("'", "\\'")
        escaped_fonts = cls.FONTS_DIR.replace(":", "\\:").replace("'", "\\'")
        vf = f"ass={escaped_ass}:fontsdir={escaped_fonts}"

        cmd_final = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", manifest_path,
            "-i", soundtrack_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-r", str(cls.FPS),
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_video_path
        ]

        logger.info(f"Assembling final V3 Cinematic Short: {output_video_path}")
        res_fin = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_fin.returncode != 0:
            logger.error(f"Assembly failed: {res_fin.stderr}")
            return False, "", {"error": res_fin.stderr}

        # Step 10: Strict Technical Quality Control Inspection
        logger.info("Executing automated Technical Quality Control (QC)...")
        qc_ok, qc_notes, metrics = VideoQC.verify_video(output_video_path, num_scenes=len(scenes))
        if not qc_ok:
            logger.warning(f"QC warning: {qc_notes}")

        report = {
            "topic": bundle["topic"],
            "video_path": output_video_path,
            "duration": metrics.get("duration", voice_dur),
            "qc_passed": qc_ok,
            "qc_notes": qc_notes,
            "num_scenes": len(scenes),
            "metrics": metrics,
            "subtitles": ass_path,
            "soundtrack": soundtrack_path
        }

        logger.info(f"✓ V3 Cinematic Short successfully generated! Duration: {metrics.get('duration', voice_dur):.2f}s")
        return True, output_video_path, report
