"""Visual Agent — searches and downloads stock video clips.

Primary: Pexels API
Fallback: Pixabay API
"""

import os
import logging
import requests
from typing import Optional

from backend.core.config import PEXELS_API_KEY, PIXABAY_API_KEY

logger = logging.getLogger(__name__)


class VisualAgent:
    """Fetches royalty-free stock video clips for video scenes."""

    def __init__(self):
        self.pexels_key = PEXELS_API_KEY
        self.pixabay_key = PIXABAY_API_KEY

    def download_video(
        self,
        query: str,
        filepath: str,
        fallback_context: str,
    ) -> Optional[str]:
        """Download a stock video clip matching the query.

        Tries: clean query → single noun → context fallback → generic.
        Uses Pexels first, then Pixabay as backup source.
        """
        clean_query = " ".join(query.strip().split()[:3]) if query else fallback_context

        if self._try_download(clean_query, filepath):
            return filepath

        first_word = clean_query.split()[0] if clean_query else ""
        if len(first_word) > 3 and first_word != clean_query:
            if self._try_download(first_word, filepath):
                return filepath

        if self._try_download(fallback_context, filepath):
            return filepath

        if self._try_download("Cinematic Atmosphere", filepath):
            return filepath

        return None

    def _try_download(self, query: str, filepath: str) -> bool:
        """Try downloading from Pexels, then Pixabay."""
        if not query:
            return False
        if self.pexels_key and self._try_pexels(query, filepath):
            return True
        if self.pixabay_key and self._try_pixabay(query, filepath):
            return True
        return False

    def _try_pexels(self, query: str, filepath: str) -> bool:
        """Search and download from Pexels API."""
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": self.pexels_key},
                params={
                    "query": query,
                    "per_page": 4,
                    "orientation": "portrait",
                    "size": "medium",
                },
                timeout=15,
            )
            if r.status_code != 200:
                return False

            videos = r.json().get("videos", [])
            for video in videos:
                v_files = sorted(
                    video.get("video_files", []),
                    key=lambda x: (x.get("height", 0) > x.get("width", 0), x.get("width", 0)),
                    reverse=True,
                )
                for vf in v_files:
                    link = vf.get("link")
                    if link and self._download_file(link, filepath):
                        return True
            return False
        except requests.RequestException as e:
            logger.debug(f"Pexels request failed for query '{query}': {e}")
            return False

    def _try_pixabay(self, query: str, filepath: str) -> bool:
        """Search and download from Pixabay API (fallback)."""
        try:
            r = requests.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": self.pixabay_key,
                    "q": query,
                    "per_page": 4,
                    "video_type": "film",
                },
                timeout=15,
            )
            if r.status_code != 200:
                return False

            hits = r.json().get("hits", [])
            for hit in hits:
                videos = hit.get("videos", {})
                for quality in ("medium", "small", "tiny"):
                    url = videos.get(quality, {}).get("url")
                    if url and self._download_file(url, filepath):
                        return True
            return False
        except requests.RequestException as e:
            logger.debug(f"Pixabay request failed for query '{query}': {e}")
            return False

    def _download_file(self, url: str, filepath: str) -> bool:
        """Download a file and validate minimum size."""
        try:
            r = requests.get(url, stream=True, timeout=45)
            if r.status_code != 200:
                return False

            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 10240:
                return True

            self._cleanup(filepath)
            return False
        except Exception as e:
            logger.debug(f"Failed download from {url}: {e}")
            self._cleanup(filepath)
            return False

    @staticmethod
    def _cleanup(filepath: str):
        """Remove a file if it exists."""
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass
