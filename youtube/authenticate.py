"""
YouTube Data API v3 OAuth 2.0 Authentication Engine
Handles OAuth flow, secure token caching, and token auto-refresh.
"""

import os
import pickle
import logging
from typing import Optional
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

logger = logging.getLogger("cricket_shorts.youtube_auth")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

DEFAULT_CLIENT_SECRETS = "client_secrets.json"
DEFAULT_TOKEN_FILE = "token.pickle"


class YouTubeAuthenticator:
    @classmethod
    def get_authenticated_service(
        cls,
        client_secrets_path: str = DEFAULT_CLIENT_SECRETS,
        token_path: str = DEFAULT_TOKEN_FILE
    ) -> Optional[Resource]:
        """
        Retrieves an authorized YouTube API service.
        Returns None if credentials are not configured or user hasn't authorized yet.
        """
        credentials = None

        # Load existing pickled token
        if os.path.exists(token_path):
            try:
                with open(token_path, "rb") as token_file:
                    credentials = pickle.load(token_file)
            except Exception as e:
                logger.error(f"Failed to read existing token file: {e}")

        # Check if valid credentials exist
        if credentials and credentials.valid:
            return build("youtube", "v3", credentials=credentials)

        # Refresh if expired
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                with open(token_path, "wb") as token_file:
                    pickle.dump(credentials, token_file)
                logger.info("YouTube OAuth token successfully refreshed.")
                return build("youtube", "v3", credentials=credentials)
            except Exception as e:
                logger.error(f"Failed to refresh YouTube token: {e}")

        # Initiate interactive flow if client_secrets.json exists
        if os.path.exists(client_secrets_path):
            try:
                logger.info(f"Initiating OAuth flow using {client_secrets_path}")
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
                credentials = flow.run_local_server(port=8088, prompt="consent")
                with open(token_path, "wb") as token_file:
                    pickle.dump(credentials, token_file)
                logger.info(f"Authorized new YouTube token and saved to {token_path}")
                return build("youtube", "v3", credentials=credentials)
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                return None

        logger.warning(
            f"YouTube client secrets file '{client_secrets_path}' not found. "
            "System running in offline / dry-run mode until configured."
        )
        return None
