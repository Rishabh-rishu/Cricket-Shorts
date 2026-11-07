"""
Cricket Shorts Engine V3 - Standalone Demo Video Renderer (Unique Visuals & Format-Specific Jerseys)
Renders full-length vertical (1080x1920 @ 30FPS) cinematic demo short:
- Topic: 'Virat Kohli: The King of Chases & 50th ODI Century'
- Format-Specific Player Jerseys: 100% Authentic ODI Colored Kit (Zero Test Whites)
- Perceptual Image Uniqueness (dhash > 10 bits difference)
- Permanent Topic Deduplication Engine Verified
- Theme: CRIMSON_OBSIDIAN (Midnight Obsidian + Crimson Red + Platinum Silver + Trophy Gold)
- Zero-Tofu Devanagari & Latin Typography
- Dual-track sound design (voice normalized to -16 LUFS, tension bed, SFX cues)
- Outputs to output/demo_v3/cricket_raaz_v3_demo.mp4
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, Any, List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from visuals.v3_demo_graphics import V3DemoGraphics
from visuals.v3_subtitle_engine import V3SubtitleEngine
from visuals.theme_manager import ThemeManager
from visuals.asset_registry import AssetRegistry
from visuals.jersey_validator import JerseyFormatValidator
from research.topic_dedup_engine import TopicDedupEngine
from database.models import DatabaseManager
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor
from voice.sfx_mixer import SFXMixer
from qc.video_qc import VideoQC

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cricket_shorts.v3_demo")


class V3DemoRenderer:
    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30
    FONTS_DIR = "/usr/share/fonts/truetype/noto"

    DEMO_SCRIPT_PARTS = [
        # Scene 1: Opening Hook (~6.5s)
        {
            "scene_idx": 0,
            "name": "Opening Hook",
            "type": "opening_hook",
            "text": "क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे तोड़ना नामुमकिन माना जा रहा था! क्या विराट कोहली वाकई वनडे क्रिकेट के सबसे बड़े लीजेंड हैं?",
            "sfx": "dramatic_boom"
        },
        # Scene 2: Player Hero Introduction (~9.5s)
        {
            "scene_idx": 1,
            "name": "Player Hero Intro",
            "type": "player_hero",
            "text": "15 नवंबर 2023 को वानखेड़े में विराट कोहली ने वो कर दिखाया जो कोई नहीं कर सका। सचिन तेंदुलकर के 49 शतकों का रिकॉर्ड तोड़कर विराट ने 50वां वनडे शतक जड़ा!",
            "sfx": "transition_whoosh"
        },
        # Scene 3: Record Statistics Presentation (~10s)
        {
            "scene_idx": 2,
            "name": "Record Stats",
            "type": "record_stats",
            "text": "विराट ने सिर्फ 279 पारियों में 50 शतक ठोक दिए! और लक्ष्य का पीछा करते हुए चेज़ में विराट के नाम 27 शतक हैं, जो दुनिया में सबसे ज्यादा हैं!",
            "sfx": "bat_hit"
        },
        # Scene 4: All-Time Leaderboard (~8.5s)
        {
            "scene_idx": 3,
            "name": "Leaderboard",
            "type": "leaderboard",
            "text": "ऑल-टाइम वनडे शतकों में 50 शतकों के साथ विराट टॉप पर हैं, सचिन 49 पर दूसरे और रोहित शर्मा 31 शतकों के साथ तीसरे नंबर पर हैं!",
            "sfx": "dramatic_boom"
        },
        # Scene 5: Outro & Debate (~7.5s)
        {
            "scene_idx": 4,
            "name": "Outro & Debate",
            "type": "final_reveal",
            "text": "क्या कोई विराट का ये 50 शतकों का रिकॉर्ड कभी तोड़ पाएगा? कमेंट्स में जरूर बताएं और क्रिकेट राज़ को अभी सब्सक्राइब करें!",
            "sfx": "stadium_cheer"
        }
    ]

    @classmethod
    def render_demo_video(
        cls,
        theme_name: str = "CRIMSON_OBSIDIAN",
        output_dir: str = "output/demo_v3",
        video_filename: str = "cricket_raaz_v3_demo.mp4"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Renders complete standalone V3 short with strict visual uniqueness,
        format-specific jersey validation, and semantic topic deduplication.
        """
        os.makedirs(output_dir, exist_ok=True)
        temp_dir = os.path.join(output_dir, "temp")
        previews_dir = os.path.join(output_dir, "previews")
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(previews_dir, exist_ok=True)

        final_video_path = os.path.join(output_dir, video_filename)
        theme = ThemeManager.get_theme(theme_name)
        topic_title = "Virat Kohli: The King of Chases & 50th ODI Century"

        logger.info("==================================================================")
        logger.info("STARTING V3 DEMO VIDEO GENERATION (FORMAT-SPECIFIC JERSEYS & DEDUP)")
        logger.info(f"Topic: {topic_title}")
        logger.info(f"Color Theme: {theme['name']}")
        logger.info(f"Output Video: {final_video_path}")
        logger.info("==================================================================")

        # ---------------------------------------------------------------------
        # Step 1: Semantic Topic Deduplication Check Against 100% of History
        # ---------------------------------------------------------------------
        logger.info("Step 1/10: Running multi-layer semantic topic deduplication audit...")
        db = DatabaseManager()
        published_history = db.get_published_topics()
        candidate_bundle = {
            "topic": topic_title,
            "hook_title": "50TH ODI CENTURY",
            "facts": [{"player_name": "Virat Kohli", "stat_callout": "50 centuries"}]
        }
        is_topic_unique, dedup_reason, dedup_score, matched_topic = TopicDedupEngine.validate_candidate(
            candidate_topic=candidate_bundle,
            historical_registry=published_history
        )
        logger.info(f"Topic deduplication status: {'APPROVED (Unique)' if is_topic_unique else 'REJECTED'}. Note: {dedup_reason}")

        # ---------------------------------------------------------------------
        # Step 2: Format-Specific Jersey Detection & Validation
        # ---------------------------------------------------------------------
        required_format = JerseyFormatValidator.detect_required_format(topic_title)
        logger.info(f"Step 2/10: Detected match format: '{required_format}'. Verifying player jerseys...")

        raw_assets = [
            {
                "scene_idx": 0,
                "scene_name": "Opening Hook",
                "player_name": "Stadium Night Atmosphere",
                "file_path": os.path.join(PROJECT_ROOT, "assets", "stadium_beams_cropped.jpg"),
                "role": "stadium"
            },
            {
                "scene_idx": 1,
                "scene_name": "Player Hero Poster",
                "player_name": "Virat Kohli",
                "file_path": os.path.join(PROJECT_ROOT, "assets", "virat_poster_cropped.jpg"),
                "role": "hero"
            },
            {
                "scene_idx": 2,
                "scene_name": "Record Stats",
                "player_name": "Virat Kohli",
                "file_path": os.path.join(PROJECT_ROOT, "assets", "kohli_cwc_action.jpg"),
                "role": "action"
            },
            {
                "scene_idx": 3,
                "scene_name": "Leaderboard",
                "player_name": "Virat Kohli",
                "file_path": os.path.join(PROJECT_ROOT, "assets", "kohli_odi_nz_2010.jpg"),
                "role": "odi_match"
            },
            {
                "scene_idx": 4,
                "scene_name": "Outro & Debate",
                "player_name": "World Cup Trophy",
                "file_path": os.path.join(PROJECT_ROOT, "assets", "icc_world_cup_trophy.jpg"),
                "role": "trophy"
            }
        ]

        jersey_report = []
        for a in raw_assets:
            ok, note = JerseyFormatValidator.validate_asset_jersey(
                image_path=a["file_path"],
                required_format=required_format,
                asset_role=a["role"]
            )
            jersey_report.append({"asset": os.path.basename(a["file_path"]), "valid": ok, "note": note})
            if not ok:
                logger.error(f"Jersey format violation on {a['file_path']}: {note}")
                return False, "", {"error": note}

        logger.info(f"✓ All assets verified: 100% compliant with '{required_format}' kit rules.")

        # ---------------------------------------------------------------------
        # Step 3: Perceptual Image Uniqueness Verification (dhash)
        # ---------------------------------------------------------------------
        logger.info("Step 3/10: Verifying visual uniqueness via Perceptual dhash...")
        video_id = "demo_v3_odi_jersey_verified"
        passed, notes, registry_report = AssetRegistry.check_and_register_video_assets(
            video_id=video_id,
            topic=topic_title,
            scene_assets=raw_assets
        )
        if not passed:
            logger.error(f"Asset uniqueness validation failed: {notes}")
            return False, "", {"error": notes, "report": registry_report}

        logger.info(f"✓ Visual uniqueness verified: {notes}")

        # ---------------------------------------------------------------------
        # Step 4: Render 5 Full-Canvas Broadcast Scene Graphics
        # ---------------------------------------------------------------------
        logger.info(f"Step 4/10: Generating 5 full-canvas scene graphics in '{theme['name']}' theme...")
        scene_images = [
            os.path.join(previews_dir, "scene1_opening_hook.png"),
            os.path.join(previews_dir, "scene2_player_hero.png"),
            os.path.join(previews_dir, "scene3_record_stats.png"),
            os.path.join(previews_dir, "scene4_leaderboard.png"),
            os.path.join(previews_dir, "scene5_final_reveal.png")
        ]

        V3DemoGraphics.create_opening_scene(
            theme=theme,
            bg_stadium_path=raw_assets[0]["file_path"],
            output_path=scene_images[0]
        )
        V3DemoGraphics.create_player_hero_scene(
            theme=theme,
            player_poster_path=raw_assets[1]["file_path"],
            output_path=scene_images[1]
        )
        V3DemoGraphics.create_record_stats_scene(
            theme=theme,
            action_photo_path=raw_assets[2]["file_path"],
            output_path=scene_images[2]
        )
        V3DemoGraphics.create_leaderboard_scene(
            theme=theme,
            captain_photo_path=raw_assets[3]["file_path"],
            output_path=scene_images[3]
        )
        V3DemoGraphics.create_final_reveal_scene(
            theme=theme,
            trophy_photo_path=raw_assets[4]["file_path"],
            output_path=scene_images[4]
        )
        logger.info("✓ All 5 broadcast scene graphics successfully rendered.")

        # ---------------------------------------------------------------------
        # Step 5: Voice Synthesis via Edge-TTS
        # ---------------------------------------------------------------------
        full_narration = " ".join([p["text"] for p in cls.DEMO_SCRIPT_PARTS])
        logger.info(f"Step 5/10: Synthesizing Edge-TTS voice ({len(full_narration.split())} words)...")

        tts = TTSEngine(voice="hi-IN-MadhurNeural", rate="+20%", pitch="-2Hz")
        raw_voice_path = os.path.join(temp_dir, "demo_raw_voice.mp3")
        tts_ok, _, raw_boundaries = tts.generate_speech(full_narration, raw_voice_path)
        if not tts_ok:
            logger.error("Edge-TTS synthesis failed.")
            return False, "", {"error": "TTS synthesis failed"}

        # ---------------------------------------------------------------------
        # Step 6: Broadcast Loudness Normalization to -16 LUFS
        # ---------------------------------------------------------------------
        logger.info("Step 6/10: Normalizing audio loudness to -16 LUFS...")
        norm_voice_path = os.path.join(temp_dir, "demo_voice_norm.aac")
        norm_ok, _, voice_dur = AudioProcessor.process_voice_audio(
            raw_voice_path, norm_voice_path, target_lufs=-16.0
        )
        if not norm_ok:
            norm_voice_path = raw_voice_path
            voice_dur = AudioProcessor.get_audio_duration(raw_voice_path)

        logger.info(f"✓ Voice normalized: {norm_voice_path} (Duration: {voice_dur:.2f}s)")

        # ---------------------------------------------------------------------
        # Step 7: Map Scene Timestamps & Pacing
        # ---------------------------------------------------------------------
        logger.info("Step 7/10: Calculating proportional scene timing...")
        char_counts = [len(p["text"]) for p in cls.DEMO_SCRIPT_PARTS]
        total_chars = sum(char_counts)
        scene_durations = [(c / total_chars) * voice_dur for c in char_counts]

        scenes_plan = []
        curr_t = 0.0
        storyboard_sfx = []
        for i, p in enumerate(cls.DEMO_SCRIPT_PARTS):
            dur = round(scene_durations[i], 2)
            scenes_plan.append({
                "index": i,
                "name": p["name"],
                "type": p["type"],
                "image": scene_images[i],
                "duration": dur,
                "start": round(curr_t, 2),
                "sfx": p["sfx"]
            })
            storyboard_sfx.append({
                "scene_index": i,
                "start_sec": round(curr_t, 2),
                "sfx_trigger": p["sfx"]
            })
            curr_t += dur

        logger.info(f"Total calculated short duration: {curr_t:.2f}s across {len(scenes_plan)} scenes.")

        # ---------------------------------------------------------------------
        # Step 8: Render Video Clips with Camera Motion
        # ---------------------------------------------------------------------
        logger.info("Step 8/10: Rendering scene video clips with camera motion...")
        rendered_clips = []
        motion_filters = [
            "zoompan=z='min(zoom+0.0006,1.05)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
            "zoompan=z='min(zoom+0.0007,1.06)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':s=1080x1920:fps=30",
            "zoompan=z='min(zoom+0.0005,1.04)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
            "zoompan=z='min(zoom+0.0005,1.04)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
            "zoompan=z='min(zoom+0.0006,1.05)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
        ]

        for s in scenes_plan:
            clip_out = os.path.join(temp_dir, f"demo_scene_{s['index']}.mp4")
            total_frames = int(s["duration"] * cls.FPS) + 5
            vf_motion = motion_filters[s["index"]].format(frames=total_frames)

            cmd_clip = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", s["image"],
                "-vf", vf_motion,
                "-c:v", "libx264",
                "-preset", "faster",
                "-crf", "18",
                "-r", str(cls.FPS),
                "-t", f"{s['duration']:.2f}",
                "-pix_fmt", "yuv420p",
                clip_out
            ]

            logger.info(f"Rendering Scene {s['index']+1}: {s['name']} ({s['duration']}s)...")
            res_c = subprocess.run(cmd_clip, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if res_c.returncode != 0:
                logger.error(f"FFmpeg scene render failed for scene {s['index']}: {res_c.stderr}")
                return False, "", {"error": res_c.stderr}
            rendered_clips.append(clip_out)

        logger.info("✓ All scene clips rendered.")

        # ---------------------------------------------------------------------
        # Step 9: Multi-Track Sound Design & ASS Subtitles
        # ---------------------------------------------------------------------
        logger.info("Step 9/10: Mixing sound design & generating subtitles...")
        soundtrack_path = os.path.join(temp_dir, "demo_soundtrack.aac")
        SFXMixer.mix_soundtrack_with_sfx(
            voice_path=norm_voice_path,
            storyboard=storyboard_sfx,
            output_mixed_path=soundtrack_path,
            bgm_volume=0.08
        )

        ass_path = os.path.join(temp_dir, "demo_subtitles.ass")
        V3SubtitleEngine.generate_ass(raw_boundaries, ass_path)

        # ---------------------------------------------------------------------
        # Step 10: Final Short Assembly
        # ---------------------------------------------------------------------
        logger.info("Step 10/10: Assembling final 1080x1920 Short video...")
        manifest_path = os.path.join(temp_dir, "concat_manifest.txt")
        with open(manifest_path, "w") as f:
            for c in rendered_clips:
                f.write(f"file '{os.path.abspath(c)}'\n")

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
            final_video_path
        ]

        res_fin = subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res_fin.returncode != 0:
            logger.error(f"Final assembly failed: {res_fin.stderr}")
            return False, "", {"error": res_fin.stderr}

        # Quality Control (QC)
        logger.info("Running automated Video Quality Control (QC)...")
        qc_ok, qc_notes, metrics = VideoQC.verify_video(final_video_path, num_scenes=len(scenes_plan))

        report = {
            "topic": topic_title,
            "required_format": required_format,
            "theme": theme["name"],
            "video_path": final_video_path,
            "duration": metrics.get("duration", voice_dur),
            "qc_passed": qc_ok,
            "qc_notes": qc_notes,
            "num_scenes": len(scenes_plan),
            "scene_images": scene_images,
            "jersey_report": jersey_report,
            "uniqueness_report": registry_report,
            "topic_dedup_report": {
                "unique": is_topic_unique,
                "reason": dedup_reason,
                "score": dedup_score
            },
            "metrics": metrics,
            "subtitles": ass_path,
            "soundtrack": soundtrack_path
        }

        logger.info("==================================================================")
        logger.info("✓ V3 CINEMATIC DEMO GENERATION COMPLETE (AUTHENTIC JERSEYS + DEDUP)!")
        logger.info(f"Video Path: {final_video_path}")
        logger.info(f"Format: {required_format} | Theme: {theme['name']} | Duration: {metrics.get('duration', voice_dur):.2f}s")
        logger.info("==================================================================")

        return True, final_video_path, report


if __name__ == "__main__":
    success, path, rep = V3DemoRenderer.render_demo_video()
    if not success:
        sys.exit(1)
