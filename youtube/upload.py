"""
YouTube Uploader & Publishing Manager
Handles resumable video uploads via YouTube Data API v3,
supports scheduled publishing, exponential backoff retries,
and dry-run safety mode.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from youtube.authenticate import YouTubeAuthenticator
from database.models import DatabaseManager

logger = logging.getLogger("cricket_shorts.youtube_upload")

RETRYABLE_STATUS_CODES = [500, 502, 503, 504, 408]
MAX_RETRIES = 5


class YouTubeUploader:
    def __init__(self, db_manager: DatabaseManager, auto_upload: bool = False):
        self.db = db_manager
        self.auto_upload = auto_upload

    def upload_short(
        self,
        short_id: int,
        video_path: str,
        metadata: Dict[str, Any],
        scheduled_rfc3339: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Uploads or dry-run schedules a short video on YouTube.
        Returns: (success, youtube_video_id, message)
        """
        title = metadata.get("title", "")
        description = metadata.get("description", "")
        tags = metadata.get("tags", [])

        # DRY RUN MODE:
        if not self.auto_upload:
            mock_video_id = f"DRYRUN_{short_id}_{int(time.time())}"
            msg = (
                f"[DRY-RUN] Video '{title}' validated. "
                f"Scheduled for {scheduled_rfc3339 or 'Immediate'}. Auto-upload is disabled."
            )
            logger.info(msg)
            self.db.update_short_upload(short_id, mock_video_id, scheduled_rfc3339)
            return True, mock_video_id, msg

        # LIVE PUBLISHING MODE:
        service = YouTubeAuthenticator.get_authenticated_service()
        if not service:
            err = "YouTube authentication failed or client_secrets.json missing. Cannot upload live."
            logger.error(err)
            return False, "", err

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags[:20],
                "categoryId": "17", # Sports
                "defaultLanguage": "hi",
                "defaultAudioLanguage": "hi"
            },
            "status": {
                "privacyStatus": "private" if scheduled_rfc3339 else "public",
                "selfDeclaredMadeForKids": False
            }
        }

        # If scheduled time provided, add publishAt
        if scheduled_rfc3339:
            body["status"]["publishAt"] = scheduled_rfc3339

        media = MediaFileUpload(
            video_path,
            chunksize=5 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4"
        )

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        retry_count = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploading '{title}': {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in RETRYABLE_STATUS_CODES and retry_count < MAX_RETRIES:
                    retry_count += 1
                    sleep_time = 2 ** retry_count
                    logger.warning(f"HttpError {e.resp.status}. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Fatal YouTube upload error: {e}")
                    return False, "", f"Upload failed: {e}"
            except Exception as e:
                logger.error(f"Unexpected upload exception: {e}")
                return False, "", f"Upload exception: {e}"

        video_id = response.get("id", "")
        video_url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"Upload success! Video ID: {video_id} ({video_url})")

        self.db.update_short_upload(short_id, video_id, scheduled_rfc3339)
        return True, video_id, f"Successfully scheduled on YouTube: {video_url}"
