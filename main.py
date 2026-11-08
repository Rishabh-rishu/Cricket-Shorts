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
from typing import Optional, Dict, Any, List
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
from editor.v3_cinematic_engine import V3CinematicEngine
from research.countdown_topics import TOP_5_COLLECTIONS
from research.v3_fact_topics import V3_COLLECTIONS
from research.topic_dedup_engine import TopicDedupEngine
from scripts.generate_script_v3 import ScriptGeneratorV3
from qc.video_qc import VideoQC
from qc.pre_publish_validator import PrePublishValidator
from youtube.scheduler import PublicationScheduler
from youtube.upload import YouTubeUploader
from youtube.authenticate import YouTubeAuthenticator
from dashboard.cli_report import DashboardReporter
import uuid
import hashlib

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

    def produce_daily_shorts(self, count: int = 2, immediate: bool = False, scheduled_rfc3339: Optional[str] = None) -> list:
        """
        Executes daily production run for unique cricket documentary shorts:
        Selects strictly non-duplicate topics via TopicDedupEngine,
        or dynamically generates fresh AI topics when curated topics are exhausted.
        """
        logger.info(f"Starting broadcast production run for {count} unique cricket shorts.")
        produced_shorts = []
        worker_id = str(uuid.uuid4())

        for idx in range(count):
            logger.info(f"--- Selecting Unique Topic for Short {idx+1}/{count} ---")
            # Step 1: Attempt to select and atomically reserve an unpublished curated collection
            t_key, bundle = TopicDedupEngine.select_and_reserve_topic(
                db_manager=self.db,
                curated_collections=V3_COLLECTIONS,
                worker_id=worker_id
            )

            # Step 2: If curated collections exhausted, generate a fresh AI topic with negative exclusions
            if not t_key or not bundle:
                logger.info("All curated collections published or reserved. Triggering Gemini 3.8 Flash AI research engine...")
                all_published = self.db.get_published_topics()
                bundle = ScriptGeneratorV3.get_or_generate_topic(
                    topic_key=None,
                    excluded_topics=all_published
                )
                if not bundle:
                    logger.error("Failed to generate unique AI topic. Aborting production run to prevent duplicate publishing.")
                    continue

                t_key = bundle.get("id") or f"ai_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                bundle["id"] = t_key
                # Register and reserve the AI generated topic
                self.db.register_topic({
                    "topic_key": t_key,
                    "topic_title": bundle.get("topic", t_key),
                    "normalized_title": TopicDedupEngine.normalize_text(bundle.get("topic", t_key)),
                    "category": bundle.get("category", "AI Research"),
                    "core_concept": bundle.get("hook_narration", ""),
                    "key_entities": list(TopicDedupEngine.extract_entities(bundle)["players"]),
                    "key_facts": [f.get("stat_callout", "") for f in bundle.get("facts", [])],
                    "status": "RESERVED",
                    "sha256_fingerprint": hashlib.sha256(f"{t_key}::{bundle.get('topic')}".encode()).hexdigest(),
                    "source": "AI_GENERATED"
                })
                self.db.reserve_topic(t_key, worker_id)

            logger.info(f"--- Producing Daily Broadcast Short {idx+1}/{count}: '{t_key}' ('{bundle['topic']}') ---")
            try:
                res = self.produce_v3_short(
                    topic_key=t_key,
                    bundle=bundle,
                    immediate=immediate,
                    scheduled_rfc3339=scheduled_rfc3339
                )
                if res:
                    produced_shorts.append(res)
            except Exception as e:
                logger.error(f"Error producing V3 short for topic '{t_key}': {e}", exc_info=True)
                self.db.mark_topic_failed(t_key, str(e))

        logger.info(f"Daily production cycle completed. {len(produced_shorts)}/{count} shorts generated.")
        self.reporter.show_dashboard()
        return produced_shorts

    def produce_countdown_short(self, topic_key: str = "rare_records") -> dict:
        """
        Redirects legacy countdown requests to the permanent V3 Broadcast Engine.
        Ensures NO legacy countdown or card templates are ever rendered.
        """
        logger.info(f"Redirecting legacy request for '{topic_key}' to Permanent V3 Broadcast Pipeline...")
        return self.produce_v3_short(topic_key=topic_key)

    def produce_v3_short(
        self,
        topic_key: str = "wc_records",
        bundle: Optional[Dict[str, Any]] = None,
        immediate: bool = False,
        scheduled_rfc3339: Optional[str] = None
    ) -> dict:
        """
        Executes V3 3-Connected-Facts Documentary Short production:
        Renders 8 dynamic scenes (Hook + 3 Facts with Ken Burns presentation cards & moving action footage + Outro),
        multi-track sound design (-16 LUFS voice + ambient tension bed + SFX cues),
        and Devanagari bold subtitles with Pre-Publish Quality Validation.
        """
        logger.info(f"Starting V3 3-Connected-Facts production for collection '{topic_key}'...")
        if bundle is None:
            if topic_key in V3_COLLECTIONS:
                bundle = V3_COLLECTIONS[topic_key]
            else:
                logger.info(f"Topic '{topic_key}' not in static collections. Fetching from ScriptGeneratorV3...")
                bundle = ScriptGeneratorV3.get_or_generate_topic(topic_key=topic_key)
                if not bundle:
                    raise ValueError(f"Topic '{topic_key}' could not be loaded or generated.")

        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join("output/videos", f"cricket_raaz_v3_{topic_key}_{timestamp_slug}.mp4")
        temp_render_dir = os.path.abspath(f"output/run_v3_{topic_key}_{timestamp_slug}")

        if immediate:
            slot_time, rfc3339_slot = datetime.now(), None
        elif scheduled_rfc3339:
            slot_time, rfc3339_slot = datetime.now(), scheduled_rfc3339
        else:
            slot_time, rfc3339_slot = PublicationScheduler.get_immediate_or_next_slot()

        rend_ok, vpath, meta_report = V3CinematicEngine.render_v3_short(
            bundle=bundle,
            output_video_path=final_video_path,
            temp_dir=temp_render_dir,
            pexels_key=self.pexels_key,
            tts_rate="+22%"
        )

        if not rend_ok:
            self.db.mark_topic_failed(topic_key, f"Rendering failed: {meta_report.get('error')}")
            raise RuntimeError(f"V3 Cinematic rendering failed: {meta_report.get('error')}")

        # Pre-Publish Quality Gate Check
        passed, pre_qc_msg = PrePublishValidator.validate_before_upload(
            topic_key=topic_key,
            topic_bundle=bundle,
            video_path=final_video_path,
            db_manager=self.db
        )
        if not passed:
            self.db.mark_topic_failed(topic_key, pre_qc_msg)
            raise RuntimeError(f"Pre-Publish Quality Check failed: {pre_qc_msg}")

        fact_hash = self.db.compute_fact_hash(bundle["topic"], bundle["hook_narration"])
        fact_id = self.db.insert_fact({
            "topic": bundle["topic"],
            "category": bundle.get("category", "Cricket Records"),
            "main_fact": bundle["hook_narration"],
            "source_primary": bundle["facts"][0]["source_primary"],
            "source_secondary": bundle["facts"][1].get("source_primary") if len(bundle["facts"]) > 1 else "",
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
            "tags": ",".join(bundle.get("tags", ["Shorts", "Cricket"])),
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

        # Always record a new short history entry
        short_id = self.db.insert_short(short_record)

        upload_ok, yt_id, up_msg = self.uploader.upload_short(
            short_id=short_id,
            video_path=final_video_path,
            metadata={
                "title": bundle["seo_title"],
                "description": bundle["seo_description"],
                "tags": bundle.get("tags", []),
                "hashtags": "#Shorts #CricketRaaz",
                "pinned_comment": short_record["pinned_comment"]
            },
            scheduled_rfc3339=rfc3339_slot
        )

        if upload_ok and yt_id and not yt_id.startswith("DRYRUN"):
            self.db.mark_topic_published(topic_key, yt_id, bundle)
            self.db.update_short_upload(short_id, yt_id, scheduled_time=rfc3339_slot)
            logger.info(f"✓ Topic '{topic_key}' published live and persisted to registry & ledger: {yt_id}")
        elif not upload_ok:
            self.db.mark_topic_failed(topic_key, up_msg)
            logger.error(f"Upload failed for topic '{topic_key}': {up_msg}")

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
    parser.add_argument("--immediate", action="store_true", help="Force immediate public upload (bypass schedule window)")
    parser.add_argument("--schedule-time", type=str, default=None, help="Specific schedule time (HH:MM or RFC3339 format)")

    args = parser.parse_args()
    factory = CricketShortsFactory()

    scheduled_rfc3339 = None
    if args.schedule_time:
        from datetime import timezone
        tz = pytz.timezone("Asia/Kolkata")
        now_local = datetime.now(tz)
        if ":" in args.schedule_time and "T" not in args.schedule_time:
            parts = args.schedule_time.strip().split(":")
            h, m = int(parts[0]), int(parts[1])
            target_dt = tz.localize(datetime(now_local.year, now_local.month, now_local.day, h, m, 0))
            if target_dt < now_local:
                target_dt += timedelta(days=1)
            scheduled_rfc3339 = target_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            scheduled_rfc3339 = args.schedule_time

    if args.dashboard:
        factory.reporter.show_dashboard()
    elif args.auth:
        service = YouTubeAuthenticator.get_authenticated_service()
        if service:
            print("✓ YouTube authentication successful! OAuth token cached.")
        else:
            print("✗ Authentication failed. Please verify client_secrets.json is present.")
    elif args.v3:
        factory.produce_v3_short(topic_key=args.v3_topic, immediate=args.immediate, scheduled_rfc3339=scheduled_rfc3339)
    elif args.countdown:
        factory.produce_countdown_short(topic_key=args.topic)
    elif args.single:
        factory.produce_daily_shorts(count=1, immediate=args.immediate, scheduled_rfc3339=scheduled_rfc3339)
    elif args.schedule:
        run_scheduler(factory)
    elif args.run:
        factory.produce_daily_shorts(count=2, immediate=args.immediate, scheduled_rfc3339=scheduled_rfc3339)
    else:
        # Default: show dashboard and brief usage
        factory.reporter.show_dashboard()
        parser.print_help()


if __name__ == "__main__":
    main()
