"""
Pexels Video API Integration & Moving Footage Provider
Fetches, crops, and caches real 1080p moving cricket footage from Pexels Video API.
Falls back to built-in moving stock footage when API key is not present or query returns empty.
"""

import os
import re
import json
import hashlib
import logging
import subprocess
from typing import Optional, Dict, Any, List, Tuple
import requests

logger = logging.getLogger("cricket_shorts.pexels")

CACHE_DIR = "assets/footage_cache"
ATTRIBUTION_FILE = "assets/footage_cache/attribution.json"
PEXELS_ENDPOINT = "https://api.pexels.com/videos/search"


class PexelsVideoProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY", "")
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._init_attribution()

    def _init_attribution(self):
        if not os.path.exists(ATTRIBUTION_FILE):
            with open(ATTRIBUTION_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def fetch_footage_for_scene(
        self,
        query: str,
        target_duration: float,
        scene_type: str = "general"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Retrieves real moving video footage for a scene.
        Returns: (success, video_path, metadata)
        """
        # 1. Check if cached clip exists for this normalized query
        cache_hit = self._get_cached_clip(query, target_duration)
        if cache_hit:
            logger.info(f"Using cached moving footage for '{query}': {cache_hit}")
            return True, cache_hit, {"source": "cache", "query": query}

        # 2. Try Pexels Video API if API key is configured
        if self.api_key and len(self.api_key) > 8:
            success, clip_path, meta = self._search_and_download_pexels(query, target_duration)
            if success:
                return True, clip_path, meta

        # 3. Fallback to built-in moving cricket stock video
        logger.info(f"Using built-in moving stock footage for scene '{scene_type}' (query: '{query}').")
        fallback_path, meta = self._get_stock_fallback(query, scene_type)
        return True, fallback_path, meta

    def _search_and_download_pexels(
        self,
        query: str,
        target_duration: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": 8,
            "size": "large"
        }

        try:
            resp = requests.get(PEXELS_ENDPOINT, headers=headers, params=params, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"Pexels API error {resp.status_code}: {resp.text}")
                return False, "", {}

            data = resp.json()
            videos = data.get("videos", [])
            if not videos:
                # Try broader query
                simplified_query = "cricket " + " ".join([w for w in query.split() if w.lower() in ("stadium", "bowler", "batsman", "ball", "match", "crowd")])
                params["query"] = simplified_query
                resp2 = requests.get(PEXELS_ENDPOINT, headers=headers, params=params, timeout=12)
                if resp2.status_code == 200:
                    videos = resp2.json().get("videos", [])

            if not videos:
                logger.warning(f"No Pexels videos found for query: '{query}'")
                return False, "", {}

            # Pick best video: prefer 1080p or highest resolution
            best_video = videos[0]
            video_files = best_video.get("video_files", [])

            # Sort files by resolution (width * height)
            video_files.sort(key=lambda x: (x.get("width") or 0) * (x.get("height") or 0), reverse=True)
            chosen_file = video_files[0]
            download_url = chosen_file.get("link")

            if not download_url:
                return False, "", {}

            vid_id = best_video.get("id")
            raw_path = os.path.join(CACHE_DIR, f"pexels_raw_{vid_id}.mp4")

            # Download video
            dl_resp = requests.get(download_url, stream=True, timeout=30)
            if dl_resp.status_code == 200:
                with open(raw_path, "wb") as f:
                    for chunk in dl_resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

                # Process video to exact 1080x1920 30fps
                processed_path = os.path.join(CACHE_DIR, f"pexels_1080x1920_{vid_id}.mp4")
                crop_ok = self._transcode_to_shorts_aspect(raw_path, processed_path, target_duration)
                if crop_ok:
                    # Save attribution
                    meta = {
                        "source": "Pexels",
                        "video_id": vid_id,
                        "url": best_video.get("url", ""),
                        "photographer": best_video.get("user", {}).get("name", "Unknown"),
                        "photographer_url": best_video.get("user", {}).get("url", ""),
                        "query": query
                    }
                    self._save_attribution(f"pexels_1080x1920_{vid_id}.mp4", meta)
                    return True, processed_path, meta

        except Exception as e:
            logger.error(f"Error querying Pexels Video API: {e}")

        return False, "", {}

    def _transcode_to_shorts_aspect(self, input_path: str, output_path: str, duration: float) -> bool:
        """
        Crops/scales any incoming video into a high-quality 1080x1920 9:16 portrait video.
        Uses intelligent center framing and subtle documentary color curve.
        """
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "fps=30,"
            "eq=contrast=1.06:saturation=1.12"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-t", str(max(2.0, duration + 1.0)),
            "-an",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0 and os.path.exists(output_path)

    def _get_cached_clip(self, query: str, duration: float) -> Optional[str]:
        q_hash = hashlib.md5(query.lower().strip().encode("utf-8")).hexdigest()[:10]
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".mp4") and q_hash in f:
                return os.path.join(CACHE_DIR, f)
        return None

    def _get_stock_fallback(self, query: str, scene_type: str) -> Tuple[str, Dict[str, Any]]:
        stock_dir = "assets/stock_footage"
        q = f"{query} {scene_type}".lower()

        if any(k in q for k in ["bowl", "fast", "pace", "seam", "delivery"]):
            clip_name = "bowler_runup.mp4"
        elif any(k in q for k in ["bat", "crease", "six", "four", "run", "chase"]):
            clip_name = "batsman_crease.mp4"
        elif any(k in q for k in ["wicket", "out", "stump", "bail", "caught", "strike"]):
            clip_name = "wicket_crash.mp4"
        elif any(k in q for k in ["ball", "spin", "reverse", "trajectory"]):
            clip_name = "cricket_ball_spin.mp4"
        elif any(k in q for k in ["umpire", "decision", "drs", "law", "rule", "mcc"]):
            clip_name = "umpire_decision.mp4"
        elif any(k in q for k in ["crowd", "celebration", "trophy", "fans", "cheer"]):
            clip_name = "stadium_celebration.mp4"
        elif any(k in q for k in ["record", "history", "milestone", "legend", "vault"]):
            clip_name = "historic_vault.mp4"
        else:
            clip_name = "stadium_floodlights.mp4"

        path = os.path.join(stock_dir, clip_name)
        if not os.path.exists(path):
            path = os.path.join(stock_dir, "stadium_floodlights.mp4")

        return path, {"source": "builtin_stock", "clip": clip_name, "query": query}

    def _save_attribution(self, filename: str, meta: Dict[str, Any]):
        try:
            with open(ATTRIBUTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[filename] = meta
            with open(ATTRIBUTION_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save attribution: {e}")
