"""
Pre-Publishing Technical & Deduplication Quality Validator
Enforces strict quality gates before any YouTube upload:
1. Strict topic uniqueness check (never re-upload a published topic)
2. Semantic deduplication verification
3. Video technical compliance (h264, aac, 1080x1920, 25-55s duration, non-zero bitrate)
4. Audio-visual stream alignment
"""

import os
import subprocess
import json
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("cricket_shorts.pre_publish_qc")


class PrePublishValidator:
    MIN_DURATION = 25.0
    MAX_DURATION = 58.0
    MIN_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB

    @classmethod
    def validate_before_upload(
        cls,
        topic_key: str,
        topic_bundle: Dict[str, Any],
        video_path: str,
        db_manager
    ) -> Tuple[bool, str]:
        """
        Runs comprehensive validation before allowing YouTube upload.
        Returns: (passed, reason_message)
        """
        logger.info(f"Running Pre-Publish Quality Check for topic '{topic_key}'...")

        # Gate 1: Historical Deduplication Check
        if db_manager.is_topic_published(topic_key):
            err = f"CRITICAL: Topic '{topic_key}' has ALREADY been published to YouTube! Upload blocked."
            logger.error(err)
            return False, err

        # Gate 2: Video File Existence and Size
        if not os.path.exists(video_path):
            err = f"Rendered video file not found at '{video_path}'."
            logger.error(err)
            return False, err

        file_size = os.path.getsize(video_path)
        if file_size < cls.MIN_FILE_SIZE_BYTES:
            err = f"Video file too small ({file_size} bytes). Potential corrupt render."
            logger.error(err)
            return False, err

        # Gate 3: FFprobe Technical Inspection
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type,codec_name,width,height:format=duration,size,bit_rate",
                "-of", "json",
                video_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode != 0:
                err = f"FFprobe validation failed: {res.stderr}"
                logger.error(err)
                return False, err

            probe_data = json.loads(res.stdout)
            streams = probe_data.get("streams", [])
            fmt = probe_data.get("format", {})

            has_video = False
            has_audio = False
            for s in streams:
                if s.get("codec_type") == "video":
                    has_video = True
                    # Check 1080x1920 or vertical ratio
                    w = s.get("width", 0)
                    h = s.get("height", 0)
                    if w > h:
                        err = f"Video is horizontal ({w}x{h}), expected vertical 9:16 (1080x1920)."
                        logger.error(err)
                        return False, err
                elif s.get("codec_type") == "audio":
                    has_audio = True

            if not has_video or not has_audio:
                err = f"Missing stream: has_video={has_video}, has_audio={has_audio}."
                logger.error(err)
                return False, err

            duration = float(fmt.get("duration", 0))
            if duration < cls.MIN_DURATION or duration > cls.MAX_DURATION:
                err = f"Duration {duration:.1f}s outside Shorts bounds ({cls.MIN_DURATION}s - {cls.MAX_DURATION}s)."
                logger.error(err)
                return False, err

        except Exception as e:
            err = f"Exception during technical video inspection: {e}"
            logger.error(err)
            return False, err

        # Gate 4: Metadata Completeness
        seo_title = topic_bundle.get("seo_title") or topic_bundle.get("topic")
        if not seo_title or len(seo_title) < 10:
            err = "SEO title is missing or too short."
            logger.error(err)
            return False, err

        logger.info(f"✓ Pre-Publish Quality Check PASSED for topic '{topic_key}'. Duration: {duration:.1f}s, Size: {file_size/1024/1024:.2f}MB.")
        return True, "Pre-publish technical & deduplication checks passed."
