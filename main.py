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
        Executes complete production run:
        Researches, plans storyboard, acquires moving footage, narrates, edits, and schedules 'count' shorts.
        """
        logger.info(f"Starting cinematic production run for {count} unique cricket shorts.")
        produced_shorts = []

        # 1. Discover, verify, and score facts
        discoverer = FactDiscoverer(self.db)
        discoverer.discover_and_evaluate(min_candidates=10, target_approved=count)

        # 2. Fetch top unhandled approved facts
        approved_facts = self.db.get_unprocessed_approved_facts(limit=count)
        if not approved_facts:
            logger.warning("No new approved facts available to produce.")
            return []

        # 3. Calculate publication slots
        pub_slots = PublicationScheduler.get_next_publication_slots(count=len(approved_facts))

        for idx, fact in enumerate(approved_facts):
            logger.info(f"--- Producing Short {idx+1}/{len(approved_facts)}: '{fact['topic']}' ---")
            slot_time, rfc3339_slot = pub_slots[idx]

            try:
                res = self._produce_single_short(fact, slot_time, rfc3339_slot)
                if res:
                    produced_shorts.append(res)
            except Exception as e:
                logger.error(f"Error producing short for fact '{fact['topic']}': {e}", exc_info=True)

        logger.info(f"Production cycle completed. {len(produced_shorts)}/{count} shorts generated.")
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


def run_scheduler(factory: CricketShortsFactory):
    """Runs automated daily scheduler independent of external tools."""
    logger.info("Cricket Shorts Factory Scheduler started. Target: 2 Shorts Daily.")
    logger.info("Morning production triggers at 08:30 AM IST (to publish at 11:00 AM IST & 07:00 PM IST).")

    # Run daily at 08:30 IST
    schedule.every().day.at("08:30").do(factory.produce_daily_shorts, count=2)

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Cricket Facts YouTube Shorts Factory (Engine V2)")
    parser.add_argument("--run", action="store_true", help="Generate 2 daily shorts immediately")
    parser.add_argument("--single", action="store_true", help="Generate 1 short for testing")
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
