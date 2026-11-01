"""
Cricket Raaz - Top 5 Countdown Video Renderer
Composes high-retention Top 5 countdown Shorts:
- 7 real moving cricket footage scenes (Hook + Num 5, 4, 3, 2, 1 + Outro CTA)
- Brand-aligned transparent graphics overlays (Midnight Navy, Gold, White, Red)
- Multi-track sound design (normalized voice + ambient bed + 7 acoustic SFX cues)
- Shaper-verified Noto Sans Devanagari subtitles (chunked 3-5 word bursts)
"""

import os
import re
import json
import logging
import subprocess
from typing import Dict, Any, List, Tuple
from visuals.countdown_graphics import CountdownGraphicsEngine
from visuals.pexels_provider import PexelsVideoProvider
from visuals.subtitle_generator import SubtitleGenerator
from voice.audio_processor import AudioProcessor
from voice.tts_engine import TTSEngine
from voice.sfx_mixer import SFXMixer
from qc.video_qc import VideoQC

logger = logging.getLogger("cricket_shorts.countdown_renderer")


class CountdownVideoRenderer:
    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    FONTS_DIR = "/usr/share/fonts/truetype/noto"

    @classmethod
    def render_countdown_short(
        cls,
        bundle: Dict[str, Any],
        output_video_path: str,
        temp_dir: str,
        pexels_key: str = "",
        tts_rate: str = "+18%"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Renders complete Top 5 Countdown Short.
        Returns: (success, video_path, metadata_report)
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        pexels = PexelsVideoProvider(api_key=pexels_key)

        records = bundle["records"]
        hook_text = bundle["hook_text"]
        cta_text = bundle["cta_text"]

        # Step 1: Build full script & individual segment scripts
        segments = []
        # Segment 0: Opening Hook
        segments.append({
            "type": "hook",
            "number": 0,
            "title": bundle.get("hook_title", "TOP 5 RAREST RECORDS"),
            "subtitle": bundle.get("hook_subtitle", "5 सबसे अनसुने क्रिकेट रिकॉर्ड्स"),
            "narration": hook_text,
            "query": "cricket stadium night match",
            "sfx": "transition_whoosh"
        })

        # Segments 1 to 5: Countdown 5 -> 1
        sfx_cycle = ["dramatic_boom", "transition_whoosh", "bat_hit", "dramatic_boom", "transition_whoosh"]
        for i, rec in enumerate(records):
            segments.append({
                "type": f"number_{rec['number']}",
                "number": rec["number"],
                "player_or_team": rec["player_or_team"],
                "record_title": rec["record_title"],
                "key_stat": rec["key_stat"],
                "narration": rec["narration"],
                "query": rec.get("footage_query", "cricket match action"),
                "scene_type": rec.get("scene_type", "general"),
                "sfx": sfx_cycle[i % len(sfx_cycle)]
            })

        # Segment 6: Outro CTA
        segments.append({
            "type": "outro",
            "number": 0,
            "narration": cta_text,
            "query": "cricket stadium crowd celebration",
            "scene_type": "outro",
            "sfx": "stadium_cheer"
        })

        # Combine into complete script with sentence markers
        full_script = " ".join([seg["narration"] for seg in segments])
        full_script = re.sub(r'\s+', ' ', full_script).strip()

        # Step 2: Voiceover Synthesis with Edge-TTS
        raw_voice_path = os.path.join(temp_dir, "raw_voice.mp3")
        normalized_voice_path = os.path.join(temp_dir, "voice_normalized.aac")

        tts = TTSEngine(rate=tts_rate)
        logger.info("Synthesizing Hindi voiceover for countdown...")
        ok_tts, _, boundaries = tts.generate_speech(full_script, raw_voice_path)
        if not ok_tts:
            return False, "", {"error": "TTS synthesis failed"}

        # Normalize audio to -16 LUFS
        _, _, total_voice_dur = AudioProcessor.process_voice_audio(raw_voice_path, normalized_voice_path)
        logger.info(f"Countdown audio synthesized and normalized: {total_voice_dur:.2f}s")

        # Step 3: Compute Segment Timing from speech boundaries
        # Calculate proportional duration per segment based on word count
        total_words = sum(len(seg["narration"].split()) for seg in segments)
        curr_time = 0.0
        storyboard = []

        for idx, seg in enumerate(segments):
            seg_words = len(seg["narration"].split())
            seg_ratio = seg_words / total_words
            seg_dur = total_voice_dur * seg_ratio
            # Minimum 3.0s per segment
            seg_dur = max(3.0, seg_dur)

            seg_start = curr_time
            seg_end = curr_time + seg_dur
            if idx == len(segments) - 1:
                seg_end = total_voice_dur
                seg_dur = max(2.5, seg_end - seg_start)

            storyboard.append({
                "scene_index": idx + 1,
                "start_sec": round(seg_start, 2),
                "end_sec": round(seg_end, 2),
                "duration": round(seg_dur, 2),
                "segment_info": seg,
                "sfx_trigger": seg["sfx"]
            })
            curr_time = seg_end

        # Step 4: Render Overlays & Acquire Moving Footage for all 7 scenes
        scene_clips = []
        footage_sources = []

        logger.info(f"Rendering {len(storyboard)} countdown video scenes...")
        for scene in storyboard:
            s_idx = scene["scene_index"]
            s_info = scene["segment_info"]
            dur = scene["duration"]
            query = s_info["query"]
            s_type = s_info.get("scene_type", "general")

            # A. Fetch moving footage (Pexels API -> Stock fallback)
            ok_f, raw_video_path, f_meta = pexels.fetch_footage_for_scene(
                query=query,
                target_duration=dur,
                scene_type=s_type
            )
            footage_sources.append({
                "scene": s_idx,
                "type": s_info["type"],
                "query": query,
                "source": f_meta.get("source", "pexels"),
                "file": os.path.basename(raw_video_path)
            })

            # B. Generate Countdown Graphic Overlay
            overlay_png = os.path.join(temp_dir, f"overlay_scene_{s_idx}.png")
            if s_info["type"] == "hook":
                CountdownGraphicsEngine.render_hook_overlay(
                    title=s_info["title"],
                    subtitle=s_info["subtitle"],
                    output_path=overlay_png
                )
            elif s_info["type"].startswith("number_"):
                CountdownGraphicsEngine.render_countdown_overlay(
                    number=s_info["number"],
                    player_or_team=s_info["player_or_team"],
                    record_title=s_info["record_title"],
                    key_stat=s_info["key_stat"],
                    output_path=overlay_png
                )
            else: # outro
                CountdownGraphicsEngine.render_outro_overlay(output_path=overlay_png)

            # C. Composite moving video + overlay + documentary grading
            scene_out_mp4 = os.path.join(temp_dir, f"countdown_clip_{s_idx}.mp4")
            vf = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "eq=contrast=1.06:saturation=1.14[bg];"
                "[1:v]scale=1080:1920[ov];"
                "[bg][ov]overlay=0:0,format=yuv420p[v]"
            )

            cmd_scene = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", raw_video_path,
                "-i", overlay_png,
                "-filter_complex", vf,
                "-map", "[v]",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-r", str(cls.FPS),
                "-t", f"{dur:.2f}",
                "-an",
                scene_out_mp4
            ]
            res_s = subprocess.run(cmd_scene, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res_s.returncode != 0:
                logger.error(f"Scene {s_idx} failed: {res_s.stderr}")
                return False, "", {"error": f"Scene {s_idx} failed"}

            scene_clips.append(scene_out_mp4)

        # Step 5: Concat Video Manifest
        concat_txt = os.path.join(temp_dir, "concat_countdown.txt")
        with open(concat_txt, "w") as f:
            for sc in scene_clips:
                f.write(f"file '{os.path.abspath(sc)}'\n")

        # Step 6: Multi-Track Sound Design (Voice + BGM + 7 SFX cues)
        soundtrack_path = os.path.join(temp_dir, "soundtrack_countdown.aac")
        SFXMixer.mix_soundtrack_with_sfx(
            voice_path=normalized_voice_path,
            storyboard=storyboard,
            output_mixed_path=soundtrack_path,
            bgm_volume=0.07 # Subtle ambient bed
        )

        # Step 7: Subtitle Generation (ASS with chunked burst timing)
        ass_path = os.path.join(temp_dir, "subtitles_countdown.ass")
        srt_path = os.path.join(temp_dir, "subtitles_countdown.srt")
        SubtitleGenerator.generate_ass(boundaries, ass_path)
        SubtitleGenerator.generate_srt(boundaries, srt_path)

        # Step 8: Final Assembly & Subtitle Burning
        escaped_ass = ass_path.replace(":", "\\:").replace("'", "\\'")
        escaped_fonts = cls.FONTS_DIR.replace(":", "\\:").replace("'", "\\'")
        video_filters = f"ass={escaped_ass}:fontsdir={escaped_fonts}"

        cmd_final = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-i", soundtrack_path,
            "-vf", video_filters,
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

        logger.info(f"Assembling final Countdown Short: {output_video_path}")
        res_f = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_f.returncode != 0:
            logger.error(f"Final assembly failed: {res_f.stderr}")
            return False, "", {"error": res_f.stderr}

        # Step 9: Extract Thumbnails / Snapshots
        snap_hook = os.path.join("output/snapshots", "countdown_snap_hook.jpg")
        snap_num1 = os.path.join("output/snapshots", "countdown_snap_number1.jpg")
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:02", "-i", output_video_path, "-vframes", "1", "-q:v", "2", snap_hook], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Snap at Number 1 reveal (~32s)
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:32", "-i", output_video_path, "-vframes", "1", "-q:v", "2", snap_num1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Step 10: Run Strict QC Verification
        qc_passed, qc_notes, qc_metrics = VideoQC.verify_video(output_video_path, num_scenes=len(storyboard))
        if not qc_passed:
            logger.error(f"Countdown QC failed: {qc_notes}")
            return False, output_video_path, {"error": f"QC failed: {qc_notes}"}

        metadata_report = {
            "topic": bundle["topic"],
            "title": bundle["seo_title"],
            "description": bundle["seo_description"],
            "tags": bundle["tags"],
            "num_scenes": len(scene_clips),
            "duration": qc_metrics.get("duration", 0),
            "footage_sources": footage_sources,
            "thumbnails": [snap_hook, snap_num1],
            "records": records,
            "qc": qc_metrics
        }
        logger.info(f"Countdown Short successfully created and verified: {output_video_path}")
        return True, output_video_path, metadata_report
