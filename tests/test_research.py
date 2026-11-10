"""
Unit tests for Fact Research, Verification, Scoring, and Deduplication.
"""

import unittest
import os
import tempfile
from research.fact_scorer import FactScorer
from research.verify_facts import FactVerifier
from database.models import DatabaseManager


class TestResearchAndVerification(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db = DatabaseManager(self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_fact_scoring_pass(self):
        sample_fact = {
            "topic": "MCC Law 28.3 Helmet Penalty",
            "category": "Hidden cricket rules and laws",
            "main_fact": "मैदान पर रखे हेलमेट से गेंद टकराने पर बल्लेबाजी टीम को 5 पेनल्टी रन मिलते हैं.",
            "source_primary": "https://www.lords.org/mcc/the-laws-of-cricket/fielders-protective-equipment",
            "source_secondary": "https://www.espncricinfo.com/story/mcc-law-28",
            "verification_notes": "MCC Law 28.3.2 specifically mandates 5 penalty runs."
        }
        scores, approved, notes = FactScorer.score_fact(sample_fact)
        self.assertTrue(approved)
        self.assertGreaterEqual(scores["total_score"], 80.0)
        self.assertGreaterEqual(scores["reliability_score"], 30.0)

    def test_fact_scoring_rejection_for_unverified(self):
        unverified_fact = {
            "topic": "Rumored match rumor",
            "category": "General",
            "main_fact": "कुछ लोगों का कहना है कि यह हुआ था.",
            "source_primary": "",
            "source_secondary": ""
        }
        scores, approved, notes = FactScorer.score_fact(unverified_fact)
        self.assertFalse(approved)
        self.assertLess(scores["total_score"], 80.0)

    def test_speculation_rejection(self):
        speculative_fact = {
            "topic": "Speculation match",
            "category": "Rare cricket facts",
            "main_fact": "शायद यह खिलाड़ी उस मैच में खेलने वाला था.",
            "source_primary": "https://www.espncricinfo.com",
            "source_secondary": ""
        }
        is_valid, msg, _ = FactVerifier.verify(speculative_fact)
        self.assertFalse(is_valid)
        self.assertIn("speculation", msg.lower())

    def test_duplicate_prevention(self):
        fact = {
            "topic": "Unique Fact Topic",
            "category": "Unbelievable IPL records",
            "main_fact": "एक अनोखा रिकॉर्ड जो पहले कभी नहीं बना.",
            "source_primary": "https://www.iplt20.com",
            "source_secondary": "https://www.espncricinfo.com",
            "verification_notes": "Official IPL scorecard verified.",
            "reliability_score": 40.0,
            "uniqueness_score": 25.0,
            "curiosity_score": 20.0,
            "visual_score": 15.0
        }
        # First insertion should succeed
        id1 = self.db.insert_fact(fact)
        self.assertIsNotNone(id1)

        # Second insertion of same fact should be blocked
        id2 = self.db.insert_fact(fact)
        self.assertIsNone(id2)

    def test_duplicate_fact_return_existing_and_short_linking(self):
        fact = {
            "topic": "Super Over Madness",
            "category": "Curated Records",
            "main_fact": "3 craziest super overs in cricket history",
            "source_primary": "https://www.espncricinfo.com",
            "source_secondary": "https://www.icc-cricket.com",
            "verification_notes": "ICC Super Over match records verified.",
            "reliability_score": 40.0,
            "uniqueness_score": 25.0,
            "curiosity_score": 20.0,
            "visual_score": 15.0
        }
        # First insertion should return integer ID
        id1 = self.db.insert_fact(fact)
        self.assertIsNotNone(id1)

        # Default duplicate insertion returns None
        id_dup = self.db.insert_fact(fact)
        self.assertIsNone(id_dup)

        # Duplicate insertion with return_existing=True returns the original ID
        id_existing = self.db.insert_fact(fact, return_existing=True)
        self.assertEqual(id1, id_existing)

        # get_fact_by_hash returns the original ID
        fact_hash = self.db.compute_fact_hash(fact["topic"], fact["main_fact"])
        id_hash = self.db.get_fact_by_hash(fact_hash)
        self.assertEqual(id1, id_hash)

        # insert_short with valid fact_id succeeds
        short_id = self.db.insert_short({
            "fact_id": id_existing,
            "title": "Super Over Short",
            "hook": "Crazy match!",
            "story": "Story details"
        })
        self.assertIsNotNone(short_id)

        # insert_short with None fact_id raises ValueError
        with self.assertRaises(ValueError):
            self.db.insert_short({
                "fact_id": None,
                "title": "Invalid Short"
            })


if __name__ == "__main__":
    unittest.main()
