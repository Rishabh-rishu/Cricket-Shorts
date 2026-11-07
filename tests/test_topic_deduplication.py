"""
Comprehensive Test Suite for Multi-Layer Topic Deduplication,
Concurrency Locking, State Transitions, and Pre-Publish Quality Gate.
"""

import os
import tempfile
import unittest
import subprocess
import json
from database.models import DatabaseManager
from research.topic_dedup_engine import TopicDedupEngine
from qc.pre_publish_validator import PrePublishValidator


class TestTopicDeduplicationAndLocking(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_cricket.db")
        self.test_ledger_path = os.path.join(self.temp_dir, "test_ledger.jsonl")

        self.db = DatabaseManager(self.test_db_path)
        self.db.LEDGER_PATH = self.test_ledger_path

        # Seed historical topics in the test database
        self.seed_topics = [
            {
                "topic_key": "wc_records",
                "topic_title": "World Cup Ke 3 Sabse Shocking Records!",
                "normalized_title": TopicDedupEngine.normalize_text("World Cup Ke 3 Sabse Shocking Records!"),
                "category": "World Cup",
                "core_concept": "Sunil Gavaskar 36 runs in 60 overs, Rohit Sharma 5 centuries in 2019 WC, Glenn McGrath 71 wickets.",
                "key_entities": ["sunil gavaskar", "rohit sharma", "glenn mcgrath"],
                "key_facts": ["36* (174)", "5 centuries", "71 wickets"],
                "status": "PUBLISHED",
                "youtube_video_ids": ["vi-KFAv9eCo"],
                "sha256_fingerprint": "hash_wc_records",
                "source": "CURATED"
            },
            {
                "topic_key": "weird_rules",
                "topic_title": "Cricket Ke 3 Aise Rules Jo Fans Ko Nahi Pata!",
                "normalized_title": TopicDedupEngine.normalize_text("Cricket Ke 3 Aise Rules Jo Fans Ko Nahi Pata!"),
                "category": "Rules",
                "core_concept": "Angelo Mathews Timed Out World Cup 2023, 5 Penalty runs for helmet strike, Mandatory appeal law.",
                "key_entities": ["angelo mathews", "timed out", "penalty runs"],
                "key_facts": ["Timed Out", "5 Penalty runs", "Law 31"],
                "status": "PUBLISHED",
                "youtube_video_ids": ["LGdugP65g_A"],
                "sha256_fingerprint": "hash_weird_rules",
                "source": "CURATED"
            },
            {
                "topic_key": "test_bowling",
                "topic_title": "Test Cricket Ke 3 Sabse Unbreakable Bowling Records!",
                "normalized_title": TopicDedupEngine.normalize_text("Test Cricket Ke 3 Sabse Unbreakable Bowling Records!"),
                "category": "Test Cricket",
                "core_concept": "Anil Kumble 10 wickets in an innings, Jasprit Bumrah 35 runs in single over, Muralitharan 800 wickets.",
                "key_entities": ["anil kumble", "jasprit bumrah", "muttiah muralitharan"],
                "key_facts": ["10/74", "35 runs in 1 over", "800 wickets"],
                "status": "PUBLISHED",
                "youtube_video_ids": ["FAYdP0Oxx10"],
                "sha256_fingerprint": "hash_test_bowling",
                "source": "CURATED"
            }
        ]

        for topic in self.seed_topics:
            self.db.register_topic(topic)
            self.db.mark_topic_published(topic["topic_key"], topic["youtube_video_ids"][0])

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    # ---------------------------------------------------------
    # 1. Exact Match Rejection Tests
    # ---------------------------------------------------------
    def test_exact_topic_key_rejection(self):
        candidate = {
            "topic_key": "wc_records",
            "topic": "Different Title Completely",
            "hook_narration": "Some random text"
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertFalse(is_valid)
        self.assertEqual(score, 1.0)
        self.assertIn("EXACT_KEY_MATCH", reason)

    def test_exact_title_match_rejection(self):
        candidate = {
            "topic_key": "brand_new_key_123",
            "topic": "Cricket World Cup Ke 3 Sabse Unbelievable Records!",
            "hook_narration": "Brand new hook"
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertFalse(is_valid)
        self.assertEqual(score, 1.0)
        self.assertIn("EXACT_TITLE_MATCH", reason)

    # ---------------------------------------------------------
    # 2. Semantic Duplicate Detection (Reworded Variations)
    # ---------------------------------------------------------
    def test_semantic_duplicate_gavaskar_reworded(self):
        """Even with completely different phrasing, Sunil Gavaskar 36 runs in 60 overs should be caught."""
        candidate = {
            "topic_key": "gavaskar_slow_batting_story",
            "topic": "Sunil Gavaskar Ki Wo Test Inning Jo Sabse Slow Rahi",
            "hook_narration": "1975 me Sunil Gavaskar ne 60 overs me sirf 36 runs banaye the!",
            "core_concept": "Sunil Gavaskar 36 runs 174 balls 60 overs",
            "facts": [
                {"player_name": "Sunil Gavaskar", "stat_callout": "36 runs in 60 overs"}
            ]
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertFalse(is_valid, "Should reject reworded Sunil Gavaskar 36 runs topic")
        self.assertGreaterEqual(score, 0.85)

    def test_semantic_duplicate_timed_out_reworded(self):
        """Angelo Mathews Timed Out rule variation should be detected as collision."""
        candidate = {
            "topic_key": "cricket_rule_drama",
            "topic": "Cricket Ka Sabse Ajeeb Dismissal Jo Shakib Ne Kiya",
            "hook_narration": "Kya aapko pata hai Angelo Mathews timed out ho gaye the?",
            "core_concept": "Angelo Mathews Timed Out controversy against Bangladesh",
            "facts": [
                {"player_name": "Angelo Mathews", "stat_callout": "Timed out without facing a ball"}
            ]
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertFalse(is_valid, "Should reject Angelo Mathews Timed Out collision")
        self.assertEqual(score, 1.0)
        self.assertIn("RULE_COLLISION", reason)

    # ---------------------------------------------------------
    # 3. Entity & Record Collision Tests
    # ---------------------------------------------------------
    def test_multi_player_collision(self):
        """Candidate mentioning Sunil Gavaskar and Rohit Sharma together should trigger collision."""
        candidate = {
            "topic_key": "indian_openers_milestones",
            "topic": "Indian Openers Ki Great Inning",
            "hook_narration": "Sunil Gavaskar aur Rohit Sharma ke unbelievable records!",
            "facts": [
                {"player_name": "Sunil Gavaskar", "headline": "Legendary Opener"},
                {"player_name": "Rohit Sharma", "headline": "Hitman Sixes"}
            ]
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(score, 0.90)

    # ---------------------------------------------------------
    # 4. Genuinely New Topic Acceptance
    # ---------------------------------------------------------
    def test_genuine_new_topic_acceptance(self):
        """A brand new topic with Rinku Singh 5 sixes or Suryakumar Yadav catch should pass cleanly."""
        candidate = {
            "topic_key": "rinku_ipl_finish",
            "topic": "IPL Ke 3 Sabse Asambhav Last Over Chases!",
            "hook_narration": "Jab aakhiri over me jeetne ke liye 29 runs chahiye the, tab hua chamatkar!",
            "core_concept": "Rinku Singh 5 sixes in 5 balls against Yash Dayal in IPL 2023.",
            "facts": [
                {"player_name": "Rinku Singh", "stat_callout": "5 Sixes in 5 Balls", "headline": "Miracle Finish"}
            ]
        }
        all_topics = self.db.get_all_registered_topics()
        is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate, all_topics)
        self.assertTrue(is_valid, f"Should accept unique Rinku Singh topic, but rejected with: {reason}")
        self.assertLess(score, 0.38)

    # ---------------------------------------------------------
    # 5. Concurrency Protection & Atomic Reservation Locking
    # ---------------------------------------------------------
    def test_atomic_reservation_locking(self):
        new_topic = {
            "topic_key": "test_atomic_lock_key",
            "topic_title": "Cricket Ke 3 Fastest Hattricks",
            "normalized_title": TopicDedupEngine.normalize_text("Cricket Ke 3 Fastest Hattricks"),
            "category": "Bowling",
            "core_concept": "Fastest hattricks in international cricket",
            "status": "AVAILABLE",
            "sha256_fingerprint": "hash_hattrick",
            "source": "CURATED"
        }
        self.db.register_topic(new_topic)

        # Worker A attempts reservation -> Succeeds
        res_a = self.db.reserve_topic("test_atomic_lock_key", "worker-token-A")
        self.assertTrue(res_a, "Worker A must successfully acquire reservation")

        # Worker B attempts reservation -> Fails (Already RESERVED)
        res_b = self.db.reserve_topic("test_atomic_lock_key", "worker-token-B")
        self.assertFalse(res_b, "Worker B must be rejected due to atomic lock")

        # Check DB status
        all_topics = {t["topic_key"]: t for t in self.db.get_all_registered_topics()}
        self.assertEqual(all_topics["test_atomic_lock_key"]["status"], "RESERVED")
        self.assertEqual(all_topics["test_atomic_lock_key"]["reservation_token"], "worker-token-A")

    # ---------------------------------------------------------
    # 6. Recovery from Failure / Cancellation (Unreserve)
    # ---------------------------------------------------------
    def test_topic_failure_and_release_recovery(self):
        new_topic = {
            "topic_key": "super_over_madness",
            "topic_title": "Cricket Ke 3 Sabse Thrilling Super Overs",
            "normalized_title": TopicDedupEngine.normalize_text("Cricket Ke 3 Sabse Thrilling Super Overs"),
            "category": "Super Over",
            "core_concept": "2019 WC Super Over, Rohit Sharma 2 sixes against NZ",
            "status": "AVAILABLE",
            "sha256_fingerprint": "hash_super_over",
            "source": "CURATED"
        }
        self.db.register_topic(new_topic)
        self.db.reserve_topic("super_over_madness", "worker-token-X")

        # Simulate rendering crash or cancellation -> release topic back to AVAILABLE
        released = self.db.release_topic("super_over_madness")
        self.assertTrue(released)

        # Verify it is NOT published
        self.assertFalse(self.db.is_topic_published("super_over_madness"))

        # Verify worker Y can now reserve it
        res_y = self.db.reserve_topic("super_over_madness", "worker-token-Y")
        self.assertTrue(res_y, "Worker Y should be able to acquire released topic")

        # Mark as failed
        self.db.mark_topic_failed("super_over_madness", "Render timeout error")
        self.assertFalse(self.db.is_topic_published("super_over_madness"))

        # FAILED topics can be re-reserved when retried
        res_retry = self.db.reserve_topic("super_over_madness", "worker-token-Z")
        self.assertTrue(res_retry, "Worker Z should be able to re-reserve FAILED topic on retry")

    # ---------------------------------------------------------
    # 7. Pre-Publish Quality Check Gate
    # ---------------------------------------------------------
    def test_pre_publish_gate_duplicate_rejection(self):
        dummy_path = os.path.join(self.temp_dir, "dummy.mp4")
        with open(dummy_path, "wb") as f:
            f.write(b"0" * (2 * 1024 * 1024))  # 2MB file

        # Attempt to publish topic that is ALREADY marked PUBLISHED
        passed, msg = PrePublishValidator.validate_before_upload(
            topic_key="wc_records",
            topic_bundle={"topic": "World Cup Records"},
            video_path=dummy_path,
            db_manager=self.db
        )
        self.assertFalse(passed)
        self.assertIn("ALREADY been published", msg)

    def test_pre_publish_gate_missing_or_small_file(self):
        # Missing file
        passed, msg = PrePublishValidator.validate_before_upload(
            topic_key="new_unique_topic",
            topic_bundle={},
            video_path=os.path.join(self.temp_dir, "non_existent.mp4"),
            db_manager=self.db
        )
        self.assertFalse(passed)
        self.assertIn("not found", msg)

        # Tiny corrupt file (< 1MB)
        small_path = os.path.join(self.temp_dir, "small.mp4")
        with open(small_path, "wb") as f:
            f.write(b"corrupt data 12345")

        passed, msg = PrePublishValidator.validate_before_upload(
            topic_key="new_unique_topic",
            topic_bundle={},
            video_path=small_path,
            db_manager=self.db
        )
        self.assertFalse(passed)
        self.assertIn("too small", msg)

    def test_pre_publish_gate_ffprobe_compliance(self):
        """Generates a valid 1080x1920 30-second video and tests full gate approval."""
        valid_mp4 = os.path.join(self.temp_dir, "valid_shorts.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=s=1080x1920:d=30",
            "-f", "lavfi", "-i", "sine=f=440:d=30",
            "-c:v", "libx264", "-b:v", "1500k", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            valid_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        passed, msg = PrePublishValidator.validate_before_upload(
            topic_key="brand_new_valid_topic",
            topic_bundle={"topic": "Unique Test Topic"},
            video_path=valid_mp4,
            db_manager=self.db
        )
        self.assertTrue(passed, f"Valid Shorts video should pass technical gate: {msg}")
        self.assertIn("passed", msg.lower())


if __name__ == "__main__":
    unittest.main()
