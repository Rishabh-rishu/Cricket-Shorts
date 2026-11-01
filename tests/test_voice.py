"""
Unit tests for Voice Synthesis, Silence Trimming, Loudness Normalization.
"""

import unittest
import os
import tempfile
from voice.tts_engine import TTSEngine
from voice.audio_processor import AudioProcessor


class TestVoiceAndAudio(unittest.TestCase):
    def setUp(self):
        self.tts = TTSEngine()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_tts_synthesis_and_duration(self):
        text = "क्रिकेट के नियमों में एक ऐसा नियम भी है जो पूरा मैच पलट सकता है."
        audio_out = os.path.join(self.temp_dir, "test_voice.mp3")

        success, path, boundaries = self.tts.generate_speech(text, audio_out)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(audio_out))
        self.assertGreater(len(boundaries), 0)

        # Audio processing check
        norm_out = os.path.join(self.temp_dir, "test_norm.aac")
        p_ok, p_path, dur = AudioProcessor.process_voice_audio(audio_out, norm_out)
        self.assertTrue(p_ok)
        self.assertGreater(dur, 1.0)
        self.assertLess(dur, 10.0)


if __name__ == "__main__":
    unittest.main()
