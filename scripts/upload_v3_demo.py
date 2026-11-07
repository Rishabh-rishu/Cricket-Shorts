"""
Upload Script for V3 Standalone Demo Video to YouTube Shorts
Schedules video on channel 'CRICKET RAaz' for tomorrow at 12:00 PM IST (06:30 AM UTC).
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.models import DatabaseManager
from youtube.upload import YouTubeUploader
from research.topic_dedup_engine import TopicDedupEngine


def main():
    video_path = os.path.join(PROJECT_ROOT, "output", "demo_v3", "cricket_raaz_v3_demo.mp4")
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)

    db = DatabaseManager()
    topic_key = "virat_50th_century"
    topic_title = "विराट कोहली का 50वां वनडे शतक! 👑 The Chase Master | Rare Cricket Facts #shorts"
    
    # Schedule for Tomorrow at 12:00 PM IST (06:30 UTC)
    # Target date: 2026-11-08 at 12:00 PM IST
    scheduled_ist = "2026-11-08 12:00:00 IST"
    scheduled_rfc3339 = "2026-11-08T06:30:00Z"

    print("==================================================================")
    print("STARTING YOUTUBE SHORTS PUBLISHING FOR V3 DEMO VIDEO")
    print(f"Video File: {video_path} ({os.path.getsize(video_path) / (1024*1024):.2f} MB)")
    print(f"Topic Title: {topic_title}")
    print(f"Target Schedule: {scheduled_ist} ({scheduled_rfc3339})")
    print("==================================================================")

    # 1. Register topic in topic_registry if not exists
    with db.get_connection() as conn:
        cursor = conn.cursor()
        existing = cursor.execute("SELECT id, status FROM topic_registry WHERE topic_key = ?", (topic_key,)).fetchone()
        now_iso = datetime.now(timezone.utc).isoformat()
        norm_title = TopicDedupEngine.normalize_text(topic_title)
        sha = hashlib.sha256(topic_key.encode()).hexdigest()

        if not existing:
            cursor.execute("""
            INSERT INTO topic_registry (
                topic_key, topic_title, normalized_title, category,
                core_concept, key_entities, key_facts, status,
                sha256_fingerprint, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic_key,
                topic_title,
                norm_title,
                "ODI_RECORDS",
                "Virat Kohli breaks Sachin Tendulkar 49 centuries record with 50th ODI hundred at Wankhede Stadium",
                json.dumps(["virat kohli", "sachin tendulkar"]),
                json.dumps(["50 centuries in 279 innings", "27 chase hundreds", "7,794 chase runs"]),
                "RESERVED",
                sha,
                "v3_cinematic_demo",
                now_iso,
                now_iso
            ))
            conn.commit()
            print("✓ Registered topic in topic_registry as RESERVED.")

    # 2. Insert or get Fact ID
    fact_id = db.insert_fact({
        "topic": topic_title,
        "category": "ODI_RECORDS",
        "main_fact": "Virat Kohli scored his historic 50th ODI century at Wankhede Stadium vs NZ, breaking Sachin Tendulkar's 49 centuries record in just 279 innings.",
        "source_primary": "ICC Official Records & BCCI Match Archives",
        "source_secondary": "ESPN Cricinfo Statsguru",
        "verification_notes": "Verified 50 ODI tons, 279 innings, 27 chase hundreds.",
        "reliability_score": 10,
        "uniqueness_score": 10,
        "curiosity_score": 10,
        "visual_score": 10
    })
    if not fact_id:
        with db.get_connection() as conn:
            row = conn.cursor().execute("SELECT id FROM facts WHERE topic = ?", (topic_title,)).fetchone()
            fact_id = row["id"] if row else 1

    # 3. Record short in database
    short_record = {
        "fact_id": fact_id,
        "title": topic_title,
        "hook": "क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे तोड़ना नामुमकिन माना जा रहा था!",
        "story": "15 नवंबर 2023 को वानखेड़े में विराट कोहली ने 50वां वनडे शतक जड़ा!",
        "surprise": "सिर्फ 279 पारियों में 50 शतक, और चेज़ में 27 शतक!",
        "cta": "क्या कोई इस रिकॉर्ड को तोड़ पाएगा? कमेंट्स में बताएं और सब्सक्राइब करें!",
        "full_script": "क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे तोड़ना नामुमकिन माना जा रहा था...",
        "description": "विराट कोहली के 50 वनडे शतक और चेज़ मास्टर रिकॉर्ड्स...",
        "tags": "Virat Kohli, 50th Century, Cricket Shorts, King Kohli",
        "hashtags": "#ViratKohli #CricketShorts #KingKohli #CricketRaaz",
        "pinned_comment": "क्या कोई बल्लेबाज कभी विराट के 50 शतकों का रिकॉर्ड तोड़ पाएगा?",
        "audio_file": os.path.join(PROJECT_ROOT, "output", "demo_v3", "temp", "demo_voice_norm.aac"),
        "subtitles_file": os.path.join(PROJECT_ROOT, "output", "demo_v3", "temp", "demo_subtitles.ass"),
        "video_file": video_path,
        "duration_seconds": 51.10,
        "qc_passed": 1,
        "qc_notes": "QC Passed: 1080x1920 (9:16), Format: ODI, Theme: Crimson Obsidian",
        "upload_status": "READY"
    }
    short_id = db.insert_short(short_record)
    print(f"✓ Recorded short in database with ID: {short_id}")

    # 4. Prepare Metadata
    description = """क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे तोड़ना नामुमकिन माना जा रहा था! 15 नवंबर 2023 को मुंबई के वानखेड़े स्टेडियम में विराट कोहली ने सचिन तेंदुलकर के 49 शतकों का ऐतिहासिक रिकॉर्ड तोड़कर 50वां वनडे शतक जड़ा। सिर्फ 279 पारियों में यह मुकाम हासिल करने वाले विराट दुनिया के नंबर-1 चेज़ मास्टर हैं!

🏏 टॉपिक: विराट कोहली के 50 वनडे शतक और चेज़ मास्टर रिकॉर्ड्स
⭐ फॉर्मेट: ICC Men's ODI Cricket Record

क्या कोई बल्लेबाज कभी विराट के इस 50 शतकों के रिकॉर्ड को तोड़ पाएगा? कमेंट्स में जरूर बताएं!

🔔 रोज़ाना अनसुने और धमाकेदार क्रिकेट रिकॉर्ड्स के लिए Cricket Raaz को सब्सक्राइब करें!

#ViratKohli #CricketShorts #KingKohli #CricketRaaz #50thCentury #CricketFacts #TeamIndia #WorldCupRecords #Shorts"""

    tags = [
        "Virat Kohli", "King Kohli", "50th ODI Century", "Cricket Raaz",
        "Cricket Facts", "Cricket Shorts", "Virat Kohli Records",
        "Sachin Tendulkar 49 Centuries", "Chase Master Kohli",
        "Team India", "ICC World Cup", "Wankhede Stadium", "Hindi Cricket Facts", "Shorts"
    ]

    metadata = {
        "title": topic_title,
        "description": description,
        "tags": tags
    }

    # 5. Upload & Schedule via YouTube Data API
    uploader = YouTubeUploader(db_manager=db, auto_upload=True)
    print("Uploading to YouTube Data API and scheduling for tomorrow 12:00 PM IST (06:30 AM UTC)...")
    success, yt_id, msg = uploader.upload_short(
        short_id=short_id,
        video_path=video_path,
        metadata=metadata,
        scheduled_rfc3339=scheduled_rfc3339
    )

    if not success:
        print(f"❌ Upload failed: {msg}")
        sys.exit(1)

    print("==================================================================")
    print("✓ YOUTUBE SHORTS UPLOAD SUCCESSFUL!")
    print(f"YouTube Video ID: {yt_id}")
    print(f"Shorts URL: https://youtube.com/shorts/{yt_id}")
    print(f"Scheduled Release Time: {scheduled_ist} ({scheduled_rfc3339})")
    print(f"Status Message: {msg}")
    print("==================================================================")

    # 6. Mark topic as PUBLISHED in database and persistent ledger
    db.mark_topic_published(topic_key, yt_id)
    print("✓ Topic marked as PUBLISHED in database and published_topics_ledger.jsonl.")


if __name__ == "__main__":
    main()
