"""
Upload First Video Now to YouTube Shorts (Live Immediate Public Release)
Publishes the master V3 acceptance short featuring the ESPN/Vizrt broadcast cards.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import logging
from dotenv import load_dotenv

load_dotenv()

from database.models import DatabaseManager
from youtube.upload import YouTubeUploader
from research.v3_fact_topics import V3_COLLECTIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cricket_shorts.upload_now")


def upload_first_video() -> bool:
    video_path = os.path.abspath("output/videos/cricket_raaz_v3_wc_records_20261101_232313.mp4")
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False

    bundle = V3_COLLECTIONS["wc_records"]
    metadata = {
        "title": "Cricket World Cup Ke 3 Sabse Unbelievable Records! 😱 #Shorts #CricketRaaz",
        "description": bundle["seo_description"] + "\n\n#Shorts #CricketRaaz #CricketFacts #WorldCupRecords",
        "tags": bundle["tags"] + ["Shorts", "Cricket Raaz", "Cricket Facts", "World Cup"],
        "pinned_comment": "Gavaskar ka 36* ya Rohit Sharma ke 5 centuries—kaun sa record sabse jyada shocking laga? Subscribe to Cricket Raaz!"
    }

    db = DatabaseManager("database/cricket_facts.db")
    uploader = YouTubeUploader(db, auto_upload=True)

    logger.info(f"Starting immediate public YouTube upload for: {video_path}")
    # scheduled_rfc3339=None triggers immediate public publication
    success, yt_id, msg = uploader.upload_short(
        short_id=9,
        video_path=video_path,
        metadata=metadata,
        scheduled_rfc3339=None
    )

    if success and yt_id and not yt_id.startswith("DRYRUN"):
        logger.info(f"✓ Video successfully published live to YouTube! Video ID: {yt_id}")
        print(f"SUCCESS: Video published live! URL: https://youtube.com/shorts/{yt_id}")
        return True
    else:
        logger.warning(f"Upload outcome: {msg}")
        return False


if __name__ == "__main__":
    upload_first_video()
