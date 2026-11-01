"""
Master Automation Orchestrator - Cricket Facts YouTube Shorts Factory (Engine V2)
Coordinates research, Gemini AI scene planning, Pexels moving footage acquisition,
voice synthesis, cinematic editing, sound design, QC inspection, and scheduled YouTube publication.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime
import pytz
import schedule
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from database.models import DatabaseManager
from research.discover_facts import FactDiscoverer
from scripts.generate_script import ScriptGenerator
from scripts.generate_metadata import MetadataGenerator
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor
from visuals.subtitle_generator import SubtitleGenerator
from visuals.gemini_storyboard import GeminiStoryboardPlanner
from editor.cinematic_renderer import CinematicVideoRenderer
from editor.countdown_renderer import CountdownVideoRenderer
from editor.v3_cinematic_engine import V3CinematicEngine
from research.countdown_topics import TOP_5_COLLECTIONS
from research.v3_fact_topics import V3_COLLECTIONS
from qc.video_qc import VideoQC
from youtube.scheduler import PublicationScheduler
from youtube.upload import YouTubeUploader
from youtube.authenticate import YouTubeAuthenticator
from dashboard.cli_report import DashboardReporter

# Logging setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"logs/cricket_shorts_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cricket_shorts.main")


class CricketShortsFactory:
    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.db = DatabaseManager(self.config["database"]["path"])
        self.auto_upload = os.getenv("AUTO_UPLOAD", str(self.config["publishing"]["auto_upload"])).lower() == "true"
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")

        self.tts = TTSEngine(
            voice=self.config.get("voice", {}).get("voice_name", "hi-IN-MadhurNeural")
        )
        self.storyboard_planner = GeminiStoryboardPlanner(api_key=self.gemini_key)
        self.uploader = YouTubeUploader(self.db, auto_upload=self.auto_upload)
        self.reporter = DashboardReporter(self.db)

    def produce_daily_shorts(self, count: int = 2) -> list:
        """
        Executes daily production run for 2 premium sports broadcast cricket shorts:
        Renders V3 3-Connected-Facts documentary shorts with Pic 2 broadcast cards,
        stadium night lighting, moving footage, and acoustic sound design.
        """
        logger.info(f"Starting broadcast production run for {count} unique cricket shorts.")
        produced_shorts = []
        topics = list(V3_COLLECTIONS.keys())

        # Identify recently produced topics to avoid immediate duplicates
        with self.db.get_connection() as conn:
            c = conn.cursor()
            rows = c.execute("SELECT story FROM shorts ORDER BY id DESC LIMIT 10").fetchall()
            recent_stories = [r[0] for r in rows if r[0]]

        selected_topics = []
        for t in topics:
            t_title = V3_COLLECTIONS[t]["topic"]
            if not any(t_title in s for s in recent_stories):
                selected_topics.append(t)
            if len(selected_topics) >= count:
                break

        # If all topics used, cycle back
        if len(selected_topics) < count:
            for t in topics:
                if t not in selected_topics:
                    selected_topics.append(t)
                if len(selected_topics) >= count:
                    break

        while len(selected_topics) < count:
            selected_topics.append(topics[len(selected_topics) % len(topics)])

        for idx in range(count):
            t_key = selected_topics[idx]
            logger.info(f"--- Producing Daily Broadcast Short {idx+1}/{count}: '{t_key}' ---")
            try:
                res = self.produce_v3_short(topic_key=t_key)
                if res:
                    produced_shorts.append(res)
            except Exception as e:
                logger.error(f"Error producing V3 short for topic '{t_key}': {e}", exc_info=True)

        logger.info(f"Daily production cycle completed. {len(produced_shorts)}/{count} shorts generated.")
        self.reporter.show_dashboard()
        return produced_shorts

    def _produce_single_short(self, fact: dict, slot_time: datetime, rfc3339_slot: str) -> dict:
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        fact_id = fact["id"]
        base_dir = os.path.abspath(f"output/run_{fact_id}_{timestamp_slug}")
        os.makedirs(base_dir, exist_ok=True)

        # Step A: Script & Metadata Generation
        logger.info("Generating script and SEO metadata...")
        script_data = ScriptGenerator.generate(fact)
        metadata = MetadataGenerator.generate(fact, script_data)

        # Step B: Voice Synthesis
        raw_audio_path = os.path.join(base_dir, "raw_voice.mp3")
        success, _, boundaries = self.tts.generate_speech(script_data["full_script"], raw_audio_path)
        if not success:
            raise RuntimeError("TTS voice generation failed.")

        # Step C: Audio Processing (Silence Trimming & Normalization to -16 LUFS)
        processed_audio_path = os.path.join(base_dir, "voice_normalized.aac")
        _, _, voice_dur = AudioProcessor.process_voice_audio(raw_audio_path, processed_audio_path)

        # Step D: Gemini AI Storyboard & Scene Planning (6 to 8 visual segments)
        logger.info("Planning multi-scene visual storyboard with footage search queries...")
        storyboard = self.storyboard_planner.create_storyboard(fact, script_data, boundaries, voice_dur)
        logger.info(f"Planned {len(storyboard)} visual segments for narration.")

        # Step E: Subtitle Generation (ASS with Devanagari styling & keyword highlight)
        ass_path = os.path.join(base_dir, "subtitles.ass")
        srt_path = os.path.join(base_dir, "subtitles.srt")
        SubtitleGenerator.generate_ass(boundaries, ass_path)
        SubtitleGenerator.generate_srt(boundaries, srt_path)

        # Step F: Cinematic Video Rendering (Moving footage + SFX + minimal overlays)
        final_video_path = os.path.join("output/videos", f"cricket_short_{fact_id}_{timestamp_slug}.mp4")
        temp_render_dir = os.path.join(base_dir, "temp_render")
        rend_ok, vpath, meta_report = CinematicVideoRenderer.render_cinematic_short(
            storyboard=storyboard,
            voice_path=processed_audio_path,
            subtitles_ass_path=ass_path,
            output_video_path=final_video_path,
            temp_dir=temp_render_dir,
            pexels_key=self.pexels_key
        )
        if not rend_ok:
            raise RuntimeError(f"Cinematic rendering failed: {meta_report.get('error')}")

        # Step G: Strict Technical & Aesthetic Quality Control
        logger.info("Running automated technical Quality Control (QC)...")
        qc_passed, qc_notes, metrics = VideoQC.verify_video(final_video_path, num_scenes=len(storyboard))
        if not qc_passed:
            raise RuntimeError(f"Quality Control failed: {qc_notes}")

        # Step H: Record in Database
        short_record = {
            "fact_id": fact_id,
            "title": metadata["title"],
            "hook": script_data["hook"],
            "story": script_data["story"],
            "surprise": script_data["surprise"],
            "cta": script_data["cta"],
            "full_script": script_data["full_script"],
            "description": metadata["description"],
            "tags": ",".join(metadata["tags"]),
            "hashtags": metadata["hashtags"],
            "pinned_comment": metadata["pinned_comment"],
            "audio_file": processed_audio_path,
            "subtitles_file": ass_path,
            "video_file": final_video_path,
            "duration_seconds": metrics["duration"],
            "qc_passed": 1 if qc_passed else 0,
            "qc_notes": qc_notes,
            "upload_status": "QC_PASSED"
        }
        with self.db.get_connection() as conn:
            c = conn.cursor()
            existing_short = c.execute("SELECT id FROM shorts WHERE fact_id = ?", (fact_id,)).fetchone()
            if existing_short:
                short_id = existing_short[0]
                c.execute("""
                UPDATE shorts SET
                    title = ?, hook = ?, story = ?, surprise = ?, cta = ?,
                    full_script = ?, description = ?, tags = ?, hashtags = ?,
                    pinned_comment = ?, video_file = ?, duration_seconds = ?,
                    qc_passed = 1, qc_notes = ?
                WHERE id = ?
                """, (
                    short_record["title"], short_record["hook"], short_record["story"],
                    short_record["surprise"], short_record["cta"], short_record["full_script"],
                    short_record["description"], short_record["tags"], short_record["hashtags"],
                    short_record["pinned_comment"], short_record["video_file"],
                    short_record["duration_seconds"], short_record["qc_notes"], short_id
                ))
                conn.commit()
            else:
                short_id = self.db.insert_short(short_record)

        # Step I: YouTube Upload / Scheduled Publishing (Dry-run by default)
        upload_ok, yt_id, up_msg = self.uploader.upload_short(
            short_id=short_id,
            video_path=final_video_path,
            metadata=metadata,
            scheduled_rfc3339=rfc3339_slot
        )

        logger.info(f"Short {fact_id} complete. YouTube Status: {up_msg}")

        return {
            "short_id": short_id,
            "fact_topic": fact["topic"],
            "title": metadata["title"],
            "video_path": final_video_path,
            "duration": metrics["duration"],
            "scheduled_time": rfc3339_slot,
            "youtube_id": yt_id,
            "storyboard": storyboard,
            "footage_sources": meta_report.get("footage_sources", []),
            "qc_notes": qc_notes
        }

    def produce_countdown_short(self, topic_key: str = "rare_records") -> dict:
        """
        Executes Top 5 Countdown production:
        Renders countdown format (5 down to 1) with moving Pexels footage,
        official brand overlays, multi-layer SFX, and Devanagari subtitles.
        """
        logger.info(f"Starting Top 5 Countdown production for collection '{topic_key}'...")
        if topic_key not in TOP_5_COLLECTIONS:
            logger.warning(f"Collection '{topic_key}' not found, falling back to 'rare_records'.")
            topic_key = "rare_records"

        bundle = TOP_5_COLLECTIONS[topic_key]
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join("output/videos", f"cricket_raaz_top5_{topic_key}_{timestamp_slug}.mp4")
        temp_render_dir = os.path.abspath(f"output/run_countdown_{topic_key}_{timestamp_slug}")

        slot_time, rfc3339_slot = PublicationScheduler.get_immediate_or_next_slot()

        rend_ok, vpath, meta_report = CountdownVideoRenderer.render_countdown_short(
            bundle=bundle,
            output_video_path=final_video_path,
            temp_dir=temp_render_dir,
            pexels_key=self.pexels_key,
            tts_rate="+25%"
        )

        if not rend_ok:
            raise RuntimeError(f"Countdown rendering failed: {meta_report.get('error')}")

        fact_hash = self.db.compute_fact_hash(bundle["topic"], bundle["hook_text"])
        with self.db.get_connection() as conn:
            c = conn.cursor()
            row = c.execute("SELECT id FROM facts WHERE fact_hash = ?", (fact_hash,)).fetchone()
            if row:
                fact_id = row[0]
            else:
                fact_id = self.db.insert_fact({
                    "topic": bundle["topic"],
                    "category": bundle["category"],
                    "main_fact": bundle["hook_text"],
                    "source_primary": bundle["records"][0]["source_primary"],
                    "source_secondary": bundle["records"][0].get("source_secondary"),
                    "verification_notes": "Top 5 Countdown bundle verified",
                    "reliability_score": 40.0,
                    "uniqueness_score": 25.0,
                    "curiosity_score": 20.0,
                    "visual_score": 15.0,
                    "total_score": 100.0,
                    "is_approved": 1
                })

        short_record = {
            "fact_id": fact_id,
            "title": bundle["seo_title"],
            "hook": bundle["hook_text"],
            "story": "Top 5 Countdown (5 down to 1)",
            "surprise": bundle["records"][-1]["narration"],
            "cta": bundle["cta_text"],
            "full_script": bundle["seo_description"],
            "description": bundle["seo_description"],
            "tags": ",".join(bundle["tags"]),
            "hashtags": "#Shorts #CricketRaaz #Top5CricketRecords",
            "pinned_comment": "Which of these 5 records shocked you the most? Subscribe to Cricket Raaz!",
            "audio_file": os.path.join(temp_render_dir, "voice_normalized.aac"),
            "subtitles_file": os.path.join(temp_render_dir, "subtitles_countdown.ass"),
            "video_file": final_video_path,
            "duration_seconds": meta_report.get("duration", 0),
            "qc_passed": 1,
            "qc_notes": "Passed all countdown QC checks",
            "upload_status": "QC_PASSED"
        }
        with self.db.get_connection() as conn:
            c = conn.cursor()
            existing_short = c.execute("SELECT id FROM shorts WHERE fact_id = ?", (fact_id,)).fetchone()
            if existing_short:
                short_id = existing_short[0]
                c.execute("""
                UPDATE shorts SET
                    title = ?, hook = ?, story = ?, surprise = ?, cta = ?,
                    full_script = ?, description = ?, tags = ?, hashtags = ?,
                    pinned_comment = ?, video_file = ?, duration_seconds = ?,
                    qc_passed = 1, qc_notes = ?
                WHERE id = ?
                """, (
                    short_record["title"], short_record["hook"], short_record["story"],
                    short_record["surprise"], short_record["cta"], short_record["full_script"],
                    short_record["description"], short_record["tags"], short_record["hashtags"],
                    short_record["pinned_comment"], short_record["video_file"],
                    short_record["duration_seconds"], short_record["qc_notes"], short_id
                ))
                conn.commit()
            else:
                short_id = self.db.insert_short(short_record)

        upload_ok, yt_id, up_msg = self.uploader.upload_short(
            short_id=short_id,
            video_path=final_video_path,
            metadata={
                "title": bundle["seo_title"],
                "description": bundle["seo_description"],
                "tags": bundle["tags"],
                "hashtags": "#Shorts #CricketRaaz",
                "pinned_comment": short_record["pinned_comment"]
            },
            scheduled_rfc3339=rfc3339_slot
        )
        logger.info(f"Countdown Short '{bundle['topic']}' produced. YouTube Status: {up_msg}")
        self.reporter.show_dashboard()
        return meta_report

    def produce_v3_short(self, topic_key: str = "wc_records") -> dict:
        """
        Executes V3 3-Connected-Facts Documentary Short production:
        Renders 8 dynamic scenes (Hook + 3 Facts with Ken Burns presentation cards & moving action footage + Outro),
        multi-track sound design (-16 LUFS voice + ambient tension bed + SFX cues),
        and Devanagari bold subtitles.
        """
        logger.info(f"Starting V3 3-Connected-Facts production for collection '{topic_key}'...")
        if topic_key not in V3_COLLECTIONS:
            logger.warning(f"V3 Collection '{topic_key}' not found, falling back to 'wc_records'.")
            topic_key = "wc_records"

        bundle = V3_COLLECTIONS[topic_key]
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join("output/videos", f"cricket_raaz_v3_{topic_key}_{timestamp_slug}.mp4")
        temp_render_dir = os.path.abspath(f"output/run_v3_{topic_key}_{timestamp_slug}")

        slot_time, rfc3339_slot = PublicationScheduler.get_immediate_or_next_slot()

        rend_ok, vpath, meta_report = V3CinematicEngine.render_v3_short(
            bundle=bundle,
            output_video_path=final_video_path,
            temp_dir=temp_render_dir,
            pexels_key=self.pexels_key,
            tts_rate="+22%"
        )

        if not rend_ok:
            raise RuntimeError(f"V3 Cinematic rendering failed: {meta_report.get('error')}")

        fact_hash = self.db.compute_fact_hash(bundle["topic"], bundle["hook_narration"])
        with self.db.get_connection() as conn:
            c = conn.cursor()
            row = c.execute("SELECT id FROM facts WHERE fact_hash = ?", (fact_hash,)).fetchone()
            if row:
                fact_id = row[0]
            else:
                fact_id = self.db.insert_fact({
                    "topic": bundle["topic"],
                    "category": bundle["category"],
                    "main_fact": bundle["hook_narration"],
                    "source_primary": bundle["facts"][0]["source_primary"],
                    "source_secondary": bundle["facts"][1].get("source_primary"),
                    "verification_notes": "V3 3-Connected-Facts bundle verified",
                    "reliability_score": 40.0,
                    "uniqueness_score": 25.0,
                    "curiosity_score": 20.0,
                    "visual_score": 15.0,
                    "total_score": 100.0,
                    "is_approved": 1
                })

        short_record = {
            "fact_id": fact_id,
            "title": bundle["seo_title"],
            "hook": bundle["hook_narration"],
            "story": f"V3 3-Connected-Facts: {bundle['topic']}",
            "surprise": bundle["facts"][-1]["narration"],
            "cta": bundle["outro_narration"],
            "full_script": bundle["seo_description"],
            "description": bundle["seo_description"],
            "tags": ",".join(bundle["tags"]),
            "hashtags": "#Shorts #CricketRaaz #CricketFacts",
            "pinned_comment": f"Which of these 3 records shocked you the most? Subscribe to Cricket Raaz!",
            "audio_file": os.path.join(temp_render_dir, "voice_normalized.aac"),
            "subtitles_file": meta_report.get("subtitles", ""),
            "video_file": final_video_path,
            "duration_seconds": meta_report.get("duration", 0),
            "qc_passed": 1 if meta_report.get("qc_passed") else 0,
            "qc_notes": meta_report.get("qc_notes", "Passed V3 QC"),
            "upload_status": "QC_PASSED"
        }

        with self.db.get_connection() as conn:
            c = conn.cursor()
            existing_short = c.execute("SELECT id FROM shorts WHERE fact_id = ?", (fact_id,)).fetchone()
            if existing_short:
                short_id = existing_short[0]
                c.execute("""
                UPDATE shorts SET
                    title = ?, hook = ?, story = ?, surprise = ?, cta = ?,
                    full_script = ?, description = ?, tags = ?, hashtags = ?,
                    pinned_comment = ?, video_file = ?, duration_seconds = ?,
                    qc_passed = 1, qc_notes = ?
                WHERE id = ?
                """, (
                    short_record["title"], short_record["hook"], short_record["story"],
                    short_record["surprise"], short_record["cta"], short_record["full_script"],
                    short_record["description"], short_record["tags"], short_record["hashtags"],
                    short_record["pinned_comment"], short_record["video_file"],
                    short_record["duration_seconds"], short_record["qc_notes"], short_id
                ))
                conn.commit()
            else:
                short_id = self.db.insert_short(short_record)

        upload_ok, yt_id, up_msg = self.uploader.upload_short(
            short_id=short_id,
            video_path=final_video_path,
            metadata={
                "title": bundle["seo_title"],
                "description": bundle["seo_description"],
                "tags": bundle["tags"],
                "hashtags": "#Shorts #CricketRaaz",
                "pinned_comment": short_record["pinned_comment"]
            },
            scheduled_rfc3339=rfc3339_slot
        )
        logger.info(f"V3 Short '{bundle['topic']}' produced. YouTube Status: {up_msg}")
        self.reporter.show_dashboard()
        return meta_report


def run_scheduler(factory: CricketShortsFactory):
    """Runs automated daily scheduler independent of external tools."""
    logger.info("Cricket Shorts Factory Scheduler started. Target: 2 Shorts Daily.")
    logger.info("Production triggers for 12:00 PM IST & 06:00 PM IST daily uploads.")

    # Run daily at 10:00 AM IST to pre-render and schedule for 12:00 PM and 18:00 IST
    schedule.every().day.at("10:00").do(factory.produce_daily_shorts, count=2)

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Cricket Facts YouTube Shorts Factory (Engine V3)")
    parser.add_argument("--v3", action="store_true", help="Generate V3 3-Connected-Facts Short")
    parser.add_argument("--v3-topic", type=str, default="wc_records", help="V3 collection topic key (wc_records, test_bowling, rare_india)")
    parser.add_argument("--run", action="store_true", help="Generate 2 daily shorts immediately")
    parser.add_argument("--single", action="store_true", help="Generate 1 short for testing")
    parser.add_argument("--countdown", action="store_true", help="Generate Top 5 Countdown short")
    parser.add_argument("--topic", type=str, default="rare_records", help="Countdown collection topic key")
    parser.add_argument("--dashboard", action="store_true", help="Display system dashboard")
    parser.add_argument("--schedule", action="store_true", help="Run background scheduler service")
    parser.add_argument("--auth", action="store_true", help="Authorize YouTube API with OAuth")

    args = parser.parse_args()
    factory = CricketShortsFactory()

    if args.dashboard:
        factory.reporter.show_dashboard()
    elif args.auth:
        service = YouTubeAuthenticator.get_authenticated_service()
        if service:
            print("✓ YouTube authentication successful! OAuth token cached.")
        else:
            print("✗ Authentication failed. Please verify client_secrets.json is present.")
    elif args.v3:
        factory.produce_v3_short(topic_key=args.v3_topic)
    elif args.countdown:
        factory.produce_countdown_short(topic_key=args.topic)
    elif args.single:
        factory.produce_daily_shorts(count=1)
    elif args.schedule:
        run_scheduler(factory)
    elif args.run:
        factory.produce_daily_shorts(count=2)
    else:
        # Default: show dashboard and brief usage
        factory.reporter.show_dashboard()
        parser.print_help()


if __name__ == "__main__":
    main()
