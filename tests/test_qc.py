"""
Unit tests for Video Quality Control (QC) Inspector.
"""

import unittest
import os
import subprocess
import tempfile
from qc.video_qc import VideoQC


class TestVideoQC(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_qc_pass_on_valid_video(self):
        valid_mp4 = os.path.join(self.temp_dir, "valid.mp4")
        # Generate short 1080x1920 video with audio using ffmpeg (32 seconds)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:d=32",
            "-f", "lavfi", "-i", "sine=f=440:d=32",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            valid_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        passed, notes, metrics = VideoQC.verify_video(valid_mp4, num_scenes=6)
        self.assertTrue(passed)
        self.assertEqual(metrics["width"], 1080)
        self.assertEqual(metrics["height"], 1920)
        self.assertEqual(metrics["aspect_ratio"], "9:16")
        self.assertGreaterEqual(metrics["duration"], 25.0)

    def test_qc_fail_on_wrong_resolution(self):
        invalid_mp4 = os.path.join(self.temp_dir, "invalid_res.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=16", # Landscape!
            "-f", "lavfi", "-i", "sine=f=440:d=16",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            invalid_mp4
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        passed, notes, metrics = VideoQC.verify_video(invalid_mp4)
        self.assertFalse(passed)
        self.assertIn("Resolution", notes)


if __name__ == "__main__":
    unittest.main()
