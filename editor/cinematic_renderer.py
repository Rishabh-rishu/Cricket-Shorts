"""
Cinematic Video Composition & Editing Engine V2
Assembles 6-to-10 real moving cricket footage clips, applies minimal broadcast overlays,
mixes multi-layered sound design (voice, tension bed, bat hits, crowd cheers),
and burns verified Devanagari subtitles into professional 1080x1920 30FPS Shorts.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Tuple
from visuals.pexels_provider import PexelsVideoProvider
from visuals.minimal_overlay_engine import MinimalOverlayEngine
from voice.sfx_mixer import SFXMixer

logger = logging.getLogger("cricket_shorts.cinematic_renderer")


class CinematicVideoRenderer:
    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    FONTS_DIR = "/usr/share/fonts/truetype/noto"

    @classmethod
    def render_cinematic_short(
        cls,
        storyboard: List[Dict[str, Any]],
        voice_path: str,
        subtitles_ass_path: str,
        output_video_path: str,
        temp_dir: str,
        pexels_key: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Renders complete cinematic cricket Short using real moving footage.
        Returns: (success, video_path, metadata)
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        pexels_provider = PexelsVideoProvider(api_key=pexels_key)
        scene_clips = []
        footage_sources = []

        logger.info(f"Rendering {len(storyboard)} moving footage segments...")

        # Step 1: Render each scene with moving video + minimal overlay
        for scene in storyboard:
            idx = scene["scene_index"]
            dur = max(2.0, float(scene["duration"]))
            queries = scene.get("footage_search_queries", ["cricket match"])
            top_query = queries[0] if queries else "cricket match"
            scene_type = scene.get("scene_type", "general")

            # A. Fetch moving footage
            success, raw_video_path, meta = pexels_provider.fetch_footage_for_scene(
                query=top_query,
                target_duration=dur,
                scene_type=scene_type
            )
            footage_sources.append({
                "scene": idx,
                "query": top_query,
                "source": meta.get("source", "stock"),
                "file": os.path.basename(raw_video_path)
            })

            # B. Generate minimal transparent overlay
            overlay_png = os.path.join(temp_dir, f"overlay_scene_{idx}.png")
            MinimalOverlayEngine.create_scene_overlay(
                top_badge=scene.get("overlay_headline", "CRICKET FACT"),
                headline=scene.get("overlay_headline", ""),
                metric=scene.get("overlay_metric", "OFFICIAL RECORD"),
                output_path=overlay_png
            )

            # C. Composite moving video + overlay + subtle documentary grade
            scene_out_mp4 = os.path.join(temp_dir, f"scene_clip_{idx}.mp4")
            vf = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,"
                "eq=contrast=1.06:saturation=1.12[bg];"
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
                logger.error(f"Failed rendering scene {idx}: {res_s.stderr}")
                return False, "", {"error": f"Scene {idx} failed: {res_s.stderr}"}

            scene_clips.append(scene_out_mp4)

        # Step 2: Build concat manifest for moving clips
        concat_txt = os.path.join(temp_dir, "concat_scenes.txt")
        with open(concat_txt, "w") as f:
            for sc in scene_clips:
                f.write(f"file '{os.path.abspath(sc)}'\n")

        # Step 3: Mix Sound Design (Voice + BGM + SFX cues)
        soundtrack_path = os.path.join(temp_dir, "soundtrack_with_sfx.aac")
        SFXMixer.mix_soundtrack_with_sfx(
            voice_path=voice_path,
            storyboard=storyboard,
            output_mixed_path=soundtrack_path,
            bgm_volume=0.08
        )

        # Step 4: Final Assembly - Concat video, add audio, burn subtitles
        escaped_ass = subtitles_ass_path.replace(":", "\\:").replace("'", "\\'")
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

        logger.info(f"Assembling cinematic Short: {output_video_path}")
        res_f = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_f.returncode != 0:
            logger.error(f"Final assembly failed: {res_f.stderr}")
            return False, "", {"error": res_f.stderr}

        meta_report = {
            "num_scenes": len(scene_clips),
            "footage_sources": footage_sources,
            "soundtrack": soundtrack_path,
            "subtitles": subtitles_ass_path
        }
        logger.info(f"Cinematic Short successfully rendered: {output_video_path}")
        return True, output_video_path, meta_report
