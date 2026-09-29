"""Music Agent — fetches and synthesizes background music matched by mood.

Integrates:
  1. Jamendo API (primary — CC licensed full tracks)
  2. Freesound API (secondary — CC audio previews)
  3. Algorithmic ambient soundbed generator (guaranteed fallback)

MusicBrainz is used for genre tag intelligence to improve search quality.
"""

import os
import math
import wave
import struct
import random
import logging
import requests
from typing import Optional, List

from backend.core.config import JAMENDO_CLIENT_ID, FREESOUND_API_KEY, TEMP_DIR
from backend.agents.musicbrainz import MusicBrainzClient

logger = logging.getLogger(__name__)

# Mood → Jamendo tag mappings for targeted search
JAMENDO_MOOD_TAGS = {
    "Suspense": "dark+ambient+cinematic",
    "Chill": "chill+lofi+ambient",
    "Epic": "epic+orchestral+cinematic",
    "Dark": "dark+horror+atmospheric",
    "Ethereal": "ethereal+dream+ambient",
    "Dramatic": "dramatic+piano+classical",
    "Melancholy": "melancholy+sad+piano",
    "Mysterious": "mysterious+ambient+electronic",
    "Uplifting": "uplifting+inspiring+acoustic",
    "Cyberpunk": "synthwave+electronic+retro",
    "Intense": "intense+action+percussion",
    "Whimsical": "playful+acoustic+folk",
}

# Expanded 12 Mood queries for Freesound
MOOD_QUERIES = {
    "Suspense": [
        "suspense cinematic tension",
        "dark ambient drone thriller",
        "investigative tension background",
        "deep cinematic rumble",
    ],
    "Chill": [
        "chill ambient lofi background",
        "calm atmospheric acoustic",
        "peaceful cinematic meditation",
        "warm downtempo background",
    ],
    "Epic": [
        "epic cinematic orchestral",
        "dramatic trailer brass strings",
        "powerful symphonic background",
        "triumphant cinematic percussion",
    ],
    "Dark": [
        "dark ambient horror atmosphere",
        "creepy eerie cinematic drone",
        "industrial dark soundscape",
        "ominous cinematic background",
    ],
    "Ethereal": [
        "ethereal dream ambient pad",
        "celestial choir atmospheric",
        "shimmering cosmic soundscape",
        "floating spiritual atmosphere",
    ],
    "Dramatic": [
        "dramatic piano cinematic strings",
        "emotional classical soundtrack",
        "intense drama film score",
        "poignant orchestral background",
    ],
    "Melancholy": [
        "melancholy sad piano solo",
        "somber cinematic ambient cello",
        "nostalgic emotional melody",
        "reflective acoustic slow",
    ],
    "Mysterious": [
        "mysterious investigative ambient",
        "enigma esoteric soundscape",
        "curious puzzle background",
        "subtle eerie synth atmosphere",
    ],
    "Uplifting": [
        "uplifting inspiring corporate",
        "hopeful acoustic guitar piano",
        "positive energetic bright",
        "motivational cinematic swell",
    ],
    "Cyberpunk": [
        "synthwave retro cyberpunk",
        "darksynth electronic bassline",
        "futuristic neon arpeggio",
        "cyber electronic industrial",
    ],
    "Intense": [
        "heavy action percussion trailer",
        "fast aggressive cinematic beat",
        "high energy chase rhythm",
        "relentless driving percussion",
    ],
    "Whimsical": [
        "playful acoustic pizzicato",
        "quirky lighthearted melody",
        "whimsical animation background",
        "cheerful fantasy acoustic",
    ],
}

DEFAULT_QUERIES = ["cinematic background music", "ambient atmospheric soundscape"]

# Base fundamental frequencies (Hz) for mood-tailored synthetic drones
MOOD_CHORDS = {
    "Suspense": [55.0, 77.78, 110.0],
    "Dark": [43.65, 61.74, 87.31],
    "Epic": [65.41, 98.00, 130.81],
    "Chill": [110.0, 137.5, 165.0],
    "Ethereal": [130.81, 164.81, 196.0],
    "Dramatic": [73.42, 87.31, 110.0],
    "Melancholy": [55.0, 65.41, 82.41],
    "Mysterious": [65.41, 92.50, 130.81],
    "Cyberpunk": [65.41, 110.0, 146.83],
    "Intense": [48.99, 73.42, 98.00],
    "Uplifting": [130.81, 164.81, 196.0],
    "Whimsical": [146.83, 185.00, 220.0],
}


class MusicAgent:
    """Fetches or generates royalty-free background music matching video mood."""

    def __init__(self):
        self.jamendo_client_id = JAMENDO_CLIENT_ID
        self.freesound_key = FREESOUND_API_KEY
        self.freesound_url = "https://freesound.org/apiv2"
        self.mb_client = MusicBrainzClient()

    def get_music_by_mood(self, mood: str, duration: float = 45.0) -> Optional[str]:
        """Search or synthesize background music matching the mood.

        Fallback chain: Jamendo → Freesound → Synthetic drone.
        """
        mood_clean = mood.strip().capitalize()

        # Step 1: Consult MusicBrainz for metadata tag discovery
        mb_tags = self.mb_client.get_enhanced_keywords(mood_clean)
        logger.info(f"MusicBrainz tags for '{mood_clean}': {mb_tags}")

        # Step 2: Try Jamendo API (primary — full CC tracks)
        if self.jamendo_client_id and self.jamendo_client_id.strip():
            try:
                result = self._try_jamendo(mood_clean, mb_tags)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Jamendo API error: {e}")

        # Step 3: Try Freesound API (secondary)
        if self.freesound_key and self.freesound_key.strip():
            queries = list(MOOD_QUERIES.get(mood_clean, DEFAULT_QUERIES))
            if mb_tags:
                queries.append(f"{mood_clean.lower()} {' '.join(mb_tags[:2])}")
            query = random.choice(queries)

            try:
                result = self._search_freesound(query)
                if result:
                    return result

                logger.warning("Primary Freesound search failed. Trying generic...")
                result = self._search_freesound("ambient background music")
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Freesound API error: {e}")

        # Step 4: Guaranteed synthetic ambient drone fallback
        logger.info(f"Generating mood-tailored atmospheric soundbed for '{mood_clean}'...")
        return self._generate_ambient_soundbed(mood_clean, duration=duration)

    # ── Jamendo ──────────────────────────────────────────────

    def _try_jamendo(self, mood: str, mb_tags: List[str]) -> Optional[str]:
        """Search and download from Jamendo API."""
        tags = JAMENDO_MOOD_TAGS.get(mood, "cinematic+ambient")

        # Enrich with MusicBrainz-discovered tags
        if mb_tags:
            extra = "+".join(t.replace(" ", "") for t in mb_tags[:2])
            tags = f"{tags}+{extra}"

        params = {
            "client_id": self.jamendo_client_id,
            "format": "json",
            "limit": 5,
            "fuzzytags": tags,
            "include": "musicinfo",
            "audioformat": "mp32",
            "order": "popularity_total",
            "groupby": "artist_id",
        }

        r = requests.get(
            "https://api.jamendo.com/v3.0/tracks",
            params=params,
            timeout=15,
        )
        if r.status_code != 200:
            logger.debug(f"Jamendo returned {r.status_code}")
            return None

        data = r.json()
        results = data.get("results", [])
        if not results:
            # Retry with simpler tags
            params["fuzzytags"] = JAMENDO_MOOD_TAGS.get(mood, "ambient")
            r = requests.get(
                "https://api.jamendo.com/v3.0/tracks",
                params=params,
                timeout=15,
            )
            if r.status_code != 200:
                return None
            results = r.json().get("results", [])
            if not results:
                return None

        track = random.choice(results)
        audio_url = track.get("audiodownload") or track.get("audio")
        if not audio_url:
            return None

        track_id = track.get("id", random.randint(1000, 9999))
        music_path = os.path.join(TEMP_DIR, f"jamendo_{track_id}.mp3")

        dl = requests.get(audio_url, stream=True, timeout=45)
        if dl.status_code != 200:
            return None

        with open(music_path, "wb") as f:
            for chunk in dl.iter_content(chunk_size=16384):
                if chunk:
                    f.write(chunk)

        if os.path.exists(music_path) and os.path.getsize(music_path) > 5000:
            name = track.get("name", "Unknown")
            artist = track.get("artist_name", "Unknown")
            logger.info(f"Downloaded Jamendo track: '{name}' by {artist}")
            return music_path

        return None

    # ── Freesound ────────────────────────────────────────────

    def _search_freesound(self, query: str) -> Optional[str]:
        """Search Freesound and download a matching preview."""
        params = {
            "query": query,
            "filter": "duration:[25 TO 180]",
            "fields": "id,name,previews,duration,license",
            "sort": "rating_desc",
            "page_size": 5,
            "token": self.freesound_key,
        }

        response = requests.get(
            f"{self.freesound_url}/search/text/",
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        sound = random.choice(results)
        previews = sound.get("previews", {})
        preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")

        if not preview_url:
            return None

        music_path = os.path.join(TEMP_DIR, f"freesound_{sound['id']}.mp3")
        r = requests.get(preview_url, stream=True, timeout=30)
        r.raise_for_status()

        with open(music_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.exists(music_path) and os.path.getsize(music_path) > 1000:
            name = sound.get("name", "Unknown")
            dur = sound.get("duration", 0)
            logger.info(f"Downloaded Freesound audio: '{name}' ({dur:.0f}s)")
            return music_path

        return None

    # ── Synthetic Fallback ───────────────────────────────────

    def _generate_ambient_soundbed(self, mood: str, duration: float = 45.0) -> Optional[str]:
        """Generate a soft, cinematic atmospheric soundbed using pure Python."""
        try:
            sample_rate = 44100
            actual_duration = max(3.0, duration)
            total_samples = int(sample_rate * actual_duration)
            filename = os.path.join(TEMP_DIR, f"synth_ambient_{random.randint(1000, 9999)}.wav")

            frequencies = MOOD_CHORDS.get(mood, [55.0, 82.41, 110.0])
            fade_samples = int(sample_rate * min(3.0, actual_duration / 3.0))

            data = bytearray()
            amp = 3800.0

            for i in range(total_samples):
                if i < fade_samples:
                    env = i / float(fade_samples)
                elif i > total_samples - fade_samples:
                    env = (total_samples - i) / float(fade_samples)
                else:
                    env = 1.0

                lfo = 0.85 + 0.15 * math.sin(2 * math.pi * 0.2 * i / sample_rate)

                left_val = 0.0
                right_val = 0.0

                for idx, freq in enumerate(frequencies):
                    weight = 1.0 / (idx + 1)
                    angle = 2 * math.pi * freq * i / sample_rate
                    left_val += weight * math.sin(angle)
                    right_val += weight * math.sin(angle + 0.3)

                sample_l = int(amp * env * lfo * left_val)
                sample_r = int(amp * env * lfo * right_val)

                sample_l = max(-32767, min(32767, sample_l))
                sample_r = max(-32767, min(32767, sample_r))

                data.extend(struct.pack("<hh", sample_l, sample_r))

            with wave.open(filename, "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(data)

            if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                logger.info(f"Synthesized ambient soundbed ({duration:.1f}s) at {filename}")
                return filename

            return None
        except Exception as e:
            logger.error(f"Failed to generate synthetic soundbed: {e}")
            return None
