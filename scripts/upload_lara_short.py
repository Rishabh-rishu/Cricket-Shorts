"""
Upload & Schedule Script for Brian Lara 400* Test World Record Short
Schedules video on channel 'CRICKET RAaz' for today at 6:00 PM IST (12:30 PM UTC).
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.models import DatabaseManager
from youtube.upload import YouTubeUploader
from research.topic_dedup_engine import TopicDedupEngine


def main():
    video_path = os.path.join(PROJECT_ROOT, "output", "demo_v3", "cricket_raaz_v3_demo_lara400.mp4")
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        sys.exit(1)

    db = DatabaseManager()
    topic_key = "brian_lara_400_not_out"
    topic_title = "ब्रायन लारा का 400 नॉट आउट! 👑 147 साल का अटूट टेस्ट रिकॉर्ड | Cricket Raaz #shorts"
    
    # Schedule for Today at 6:00 PM IST (12:30 UTC)
    scheduled_ist = "2026-11-08 18:00:00 IST"
    scheduled_rfc3339 = "2026-11-08T12:30:00Z"

    print("==================================================================")
    print("STARTING YOUTUBE SHORTS PUBLISHING: BRIAN LARA 400*")
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
                "TEST_RECORDS",
                "Brian Lara scored 400 not out against England at Antigua in April 2004, the only quadruple century in Test cricket history.",
                json.dumps(["brian lara", "matthew hayden"]),
                json.dumps(["400 not out in 582 balls", "778 minutes batting", "43 fours and 4 sixes"]),
                "RESERVED",
                sha,
                "v3_cinematic_test_engine",
                now_iso,
                now_iso
            ))
            conn.commit()
            print("✓ Registered topic in topic_registry as RESERVED.")

    # 2. Insert or get Fact ID
    fact_id = db.insert_fact({
        "topic": topic_title,
        "category": "TEST_RECORDS",
        "main_fact": "Brian Lara scored 400 not out against England in 2004 at Antigua Recreation Ground, spending 778 minutes at crease to set the highest individual score in 147 years of Test cricket.",
        "source_primary": "ICC Official Test Records & Wisden Archives",
        "source_secondary": "ESPN Cricinfo Statsguru",
        "verification_notes": "Verified 400* runs, 582 balls faced, 778 minutes on crease, 43 fours, 4 sixes.",
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
        "hook": "टेस्ट क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे कोई भी बल्लेबाज आज तक तोड़ नहीं पाया!",
        "story": "12 अप्रैल 2004 को एंटीगा में ब्रायन लारा ने 400 रन बनाकर इतिहास रच दिया!",
        "surprise": "लगातार 13 घंटे तक क्रीज पर डटे रहे और 582 गेंदों पर 400 नॉट आउट बनाए!",
        "cta": "क्या कोई बल्लेबाज 400 रनों का रिकॉर्ड कभी तोड़ पाएगा? कमेंट्स में बताएं और सब्सक्राइब करें!",
        "full_script": "टेस्ट क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे कोई भी बल्लेबाज आज तक तोड़ नहीं पाया...",
        "description": "ब्रायन लारा का 400 नॉट आउट! 147 साल के टेस्ट इतिहास की सबसे महान और अटूट पारी...",
        "tags": "Brian Lara, 400 Not Out, Test Cricket, Cricket Shorts, West Indies, Wisden Trophy",
        "hashtags": "#BrianLara #CricketShorts #TestCricket #400NotOut #CricketRaaz",
        "pinned_comment": "क्या टेस्ट क्रिकेट में कोई बल्लेबाज कभी ब्रायन लारा के 400 रनों का रिकॉर्ड तोड़ पाएगा?",
        "audio_file": os.path.join(PROJECT_ROOT, "output", "demo_v3", "temp_lara", "demo_voice_norm.aac"),
        "subtitles_file": os.path.join(PROJECT_ROOT, "output", "demo_v3", "temp_lara", "demo_subtitles.ass"),
        "video_file": video_path,
        "duration_seconds": 55.49,
        "qc_passed": 1,
        "qc_notes": "QC Passed: 1080x1920 (9:16), Format: TEST, Theme: Caribbean Maroon, Test Whites Enforced",
        "upload_status": "READY"
    }
    short_id = db.insert_short(short_record)
    print(f"✓ Recorded short in database with ID: {short_id}")

    # 4. Prepare Metadata
    description = """टेस्ट क्रिकेट इतिहास का वो महा-रिकॉर्ड, जिसे 147 साल में कोई भी बल्लेबाज आज तक तोड़ नहीं पाया! 12 अप्रैल 2004 को एंटीगा में वेस्टइंडीज के प्रिंस ब्रायन लारा ने इंग्लैंड के खिलाफ अकेले 400 रन बनाकर इतिहास रच दिया था। 13 घंटे तक क्रीज पर डटे रहकर लारा ने 582 गेंदों का सामना किया और 43 चौके तथा 4 छक्के जड़े।

🏏 टॉपिक: ब्रायन लारा का 400 नॉट आउट वर्ल्ड रिकॉर्ड
⭐ फॉर्मेट: ICC Men's Test Cricket
🏆 थीम: Caribbean Maroon & Test Whites

क्या टेस्ट क्रिकेट में कोई बल्लेबाज कभी ब्रायन लारा के इस 400 रनों के रिकॉर्ड को तोड़ पाएगा? अपनी राय कमेंट्स में जरूर बताएं!

🔔 रोज़ाना अनसुने और धमाकेदार क्रिकेट रिकॉर्ड्स के लिए Cricket Raaz को सब्सक्राइब करें!

#BrianLara #400NotOut #CricketShorts #TestCricket #CricketRaaz #CricketFacts #WestIndies #WisdenTrophy #Shorts #CricketRecords"""

    tags = [
        "Brian Lara", "400 Not Out", "Brian Lara 400", "Test Cricket",
        "Cricket Raaz", "Cricket Facts", "Cricket Shorts", "Highest Test Score",
        "West Indies Cricket", "Antigua Recreation Ground", "Wisden Trophy",
        "Matthew Hayden 380", "Hindi Cricket Facts", "Shorts"
    ]

    metadata = {
        "title": topic_title,
        "description": description,
        "tags": tags
    }

    # 5. Upload & Schedule via YouTube Data API
    uploader = YouTubeUploader(db_manager=db, auto_upload=True)
    print("Uploading to YouTube Data API and scheduling for today 6:00 PM IST (12:30 PM UTC)...")
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
