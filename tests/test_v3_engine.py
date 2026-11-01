"""
Unit tests for Cricket Shorts Cinematic Video Engine V3.
"""

import os
import unittest
from research.v3_fact_topics import V3_COLLECTIONS
from scripts.generate_script_v3 import ScriptGeneratorV3
from visuals.player_asset_provider import PlayerAssetProvider
from visuals.v3_subtitle_engine import V3SubtitleEngine


class TestV3Engine(unittest.TestCase):
    def test_v3_collections_integrity(self):
        """Validates all V3 collections have hook, 3 facts, and outro."""
        for key, collection in V3_COLLECTIONS.items():
            self.assertIn("topic", collection)
            self.assertIn("hook_narration", collection)
            self.assertIn("outro_narration", collection)
            self.assertEqual(len(collection["facts"]), 3, f"Collection {key} must have exactly 3 facts")
            for f in collection["facts"]:
                self.assertIn("badge", f)
                self.assertIn("headline", f)
                self.assertIn("stat_callout", f)
                self.assertIn("narration", f)

    def test_script_v3_assembly(self):
        """Tests script assembly and word count calibration."""
        bundle = V3_COLLECTIONS["wc_records"]
        full_text = ScriptGeneratorV3.assemble_full_narration(bundle)
        words = full_text.split()
        self.assertGreaterEqual(len(words), 80, "Script should have sufficient length for 35s+ Shorts")
        self.assertLessEqual(len(words), 140, "Script should not exceed 140 words to stay under 50s")

    def test_player_asset_generation(self):
        """Tests that player fact card renders a valid 1080x1920 PNG image."""
        out_png = "/tmp/test_v3_fact_card.png"
        card_path = PlayerAssetProvider.create_cinematic_fact_card(
            badge_text="FACT 1 : GAVASKAR",
            player_name="Sunil Gavaskar",
            headline="36 RUNS IN 60 OVERS",
            subheadline="174 Balls • Only 1 Boundary",
            stat_callout="36* (174b)",
            output_path=out_png
        )
        self.assertTrue(os.path.exists(card_path))
        self.assertGreater(os.path.getsize(card_path), 10000, "Rendered card must be non-empty")
        if os.path.exists(out_png):
            os.remove(out_png)

    def test_v3_subtitle_generation(self):
        """Tests V3 subtitle chunking and ASS header formatting."""
        boundaries = [
            {"start": 0.0, "end": 4.5, "text": "वर्ल्ड कप इतिहास के 3 ऐसे अनसुने रिकॉर्ड्स"},
            {"start": 4.5, "end": 9.0, "text": "फैक्ट नंबर 1 सुनील गावस्कर ने पूरे 60 ओवर बैटिंग की"}
        ]
        out_ass = "/tmp/test_v3_subtitles.ass"
        ass_path = V3SubtitleEngine.generate_ass(boundaries, out_ass)
        self.assertTrue(os.path.exists(ass_path))
        with open(ass_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("[Script Info]", content)
        self.assertIn("Noto Sans Devanagari", content)
        self.assertIn("Dialogue: 0,", content)
        if os.path.exists(out_ass):
            os.remove(out_ass)


if __name__ == "__main__":
    unittest.main()
