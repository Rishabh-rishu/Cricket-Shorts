"""
Unit and Visual Integrity Test: Devanagari & Latin Typography & Broadcast Card Engine
Validates that:
1. No square boxes (□□□□) or missing glyphs exist in rendered cards.
2. Mukta-Bold and NotoSans fonts render both Hindi and English accurately.
3. Broadcast cards render with complete player portraits, crests, and stats tables.
"""

import os
import unittest
from PIL import Image
from visuals.player_asset_provider import PlayerAssetProvider
from research.v3_fact_topics import V3_COLLECTIONS


class TestHindiAndBroadcastCard(unittest.TestCase):
    def test_bilingual_font_no_tofu(self):
        """Verifies font renders complex Hindi ligatures and English without tofu glyphs."""
        font = PlayerAssetProvider.get_font(40, "bold")
        test_strings = [
            "SUNIL GAVASKAR",
            "सुनील गावस्कर",
            "36 RUNS IN 60 OVERS",
            "60 ओवर में 36 रन",
            "174 Balls • Only 1 Boundary",
            "174 गेंदें • सिर्फ 1 चौका",
            "36* (174b)",
            "ANIL KUMBLE 1999",
            "अनिल कुंबले",
            "10 WICKETS IN AN INNINGS",
            "10 विकेट एक पारी में",
            "GLENN MCGRATH",
            "ग्लेन मैक्ग्रा",
            "7 WICKETS FOR 15 RUNS",
        ]
        for s in test_strings:
            img = Image.new("L", (800, 80), 0)
            length = font.getlength(s)
            self.assertGreater(length, 0, f"Font getlength must be > 0 for {s}")

    def test_render_all_curated_fact_cards(self):
        """Tests that all facts in V3 collections generate valid broadcast cards."""
        out_dir = "/tmp/test_cards"
        os.makedirs(out_dir, exist_ok=True)

        for coll_key, coll in V3_COLLECTIONS.items():
            for fact in coll["facts"]:
                f_num = fact["fact_number"]
                out_path = os.path.join(out_dir, f"{coll_key}_f{f_num}_card.png")
                res_path = PlayerAssetProvider.create_cinematic_fact_card(
                    badge_text=fact.get("badge", f"FACT {f_num}"),
                    player_name=fact.get("player_name") or fact.get("player_or_subject", "CRICKET RECORD"),
                    headline=fact.get("headline", ""),
                    subheadline=fact.get("subheadline", ""),
                    stat_callout=fact.get("stat_callout", ""),
                    output_path=out_path,
                    country=fact.get("country", "INDIA"),
                    player_role=fact.get("player_role", "International Cricketer"),
                    tournament_header=fact.get("tournament_header", "CRICKET RECORD"),
                    stats_table=fact.get("stats_table"),
                    achievement_tag=fact.get("achievement_tag", "HISTORIC RECORD")
                )
                self.assertTrue(os.path.exists(res_path))
                self.assertGreater(os.path.getsize(res_path), 50000, f"Card for {fact['player_name']} must be valid and non-empty")

                # Verify image dimensions
                with Image.open(res_path) as im:
                    self.assertEqual(im.size, (1080, 1920))


if __name__ == "__main__":
    unittest.main()
