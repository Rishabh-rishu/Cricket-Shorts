"""
Unit tests for Cricket Visual Scenes & Subtitle Generation.
"""

import unittest
import os
import tempfile
from PIL import Image
from visuals.animation_engine import CricketAnimationEngine
from visuals.subtitle_generator import SubtitleGenerator


class TestVisualsAndSubtitles(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_stadium_background_resolution(self):
        img = CricketAnimationEngine.create_stadium_background()
        self.assertEqual(img.size, (1080, 1920))

    def test_rule_scene_generation(self):
        out_path = os.path.join(self.temp_dir, "rule.png")
        CricketAnimationEngine.create_rule_scene(
            topic="MCC Law 28 - Helmet Penalty",
            highlight_text="मैदान पर रखे हेलमेट से टकराने पर 5 रन पेनल्टी!",
            output_path=out_path
        )
        self.assertTrue(os.path.exists(out_path))
        with Image.open(out_path) as im:
            self.assertEqual(im.size, (1080, 1920))

    def test_scoreboard_scene_generation(self):
        out_path = os.path.join(self.temp_dir, "scoreboard.png")
        CricketAnimationEngine.create_scoreboard_scene(
            title="Jasprit Bumrah Test Record",
            big_metric="35 RUNS",
            metric_label="MOST RUNS IN ONE TEST OVER",
            detail_lines=["Stuart Broad Bowling", "Edgbaston 2022"],
            output_path=out_path
        )
        self.assertTrue(os.path.exists(out_path))

    def test_ass_subtitle_generation(self):
        boundaries = [
            {"start": 0.0, "end": 2.5, "text": "क्रिकेट इतिहास का एक अनोखा नियम!"},
            {"start": 2.5, "end": 5.0, "text": "जिसमें बल्लेबाज को 5 पेनल्टी रन मिलते हैं."}
        ]
        ass_out = os.path.join(self.temp_dir, "test.ass")
        SubtitleGenerator.generate_ass(boundaries, ass_out)
        self.assertTrue(os.path.exists(ass_out))

        with open(ass_out, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Dialogue:", content)
            self.assertIn("Noto Sans Devanagari", content)


if __name__ == "__main__":
    unittest.main()
