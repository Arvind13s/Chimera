"""MusicBrainz metadata client — provides genre tag intelligence for mood-aware music search."""

import logging
import time
from typing import Dict, List, Optional

import musicbrainzngs

from backend.core.config import (
    MUSICBRAINZ_APP_NAME,
    MUSICBRAINZ_APP_VERSION,
    MUSICBRAINZ_CONTACT,
)

logger = logging.getLogger(__name__)

# Mood → fallback genre/tag keywords when MusicBrainz returns nothing
MOOD_FALLBACK_TAGS: Dict[str, List[str]] = {
    "Suspense": ["dark ambient", "tension", "thriller"],
    "Chill": ["lo-fi", "ambient", "downtempo"],
    "Epic": ["orchestral", "cinematic", "trailer"],
    "Dark": ["dark ambient", "industrial", "doom"],
    "Ethereal": ["ambient", "dream pop", "shoegaze"],
    "Dramatic": ["classical", "soundtrack", "symphonic"],
    "Melancholy": ["sad", "piano", "post-rock"],
    "Mysterious": ["ambient", "experimental", "electronic"],
    "Uplifting": ["indie pop", "acoustic", "folk"],
    "Cyberpunk": ["synthwave", "darksynth", "retrowave"],
    "Intense": ["metal", "industrial", "drum and bass"],
    "Whimsical": ["folk", "acoustic", "indie"],
}


class MusicBrainzClient:
    """Lightweight MusicBrainz tag lookup with in-memory caching."""

    def __init__(self):
        self._cache: Dict[str, List[str]] = {}
        musicbrainzngs.set_useragent(
            MUSICBRAINZ_APP_NAME,
            MUSICBRAINZ_APP_VERSION,
            MUSICBRAINZ_CONTACT,
        )

    def get_enhanced_keywords(self, mood: str) -> List[str]:
        """Get enriched search keywords for a given mood.

        Uses MusicBrainz tag search with in-memory caching and
        graceful fallback to static tag maps.
        """
        cache_key = mood.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = musicbrainzngs.search_tags(query=cache_key, limit=5)
            tags = result.get("tag-list", [])
            keywords = [
                tag["name"]
                for tag in tags
                if tag.get("name") and len(tag["name"]) > 2
            ][:5]

            if keywords:
                self._cache[cache_key] = keywords
                return keywords

        except musicbrainzngs.WebServiceError as e:
            logger.debug(f"MusicBrainz API error for '{mood}': {e}")
        except Exception as e:
            logger.debug(f"MusicBrainz unexpected error: {e}")

        # Graceful fallback
        fallback = MOOD_FALLBACK_TAGS.get(mood.strip().capitalize(), ["ambient", "cinematic"])
        self._cache[cache_key] = fallback
        return fallback
