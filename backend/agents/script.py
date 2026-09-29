"""Script Agent — creates structured scene-by-scene video scripts."""

import logging
from typing import Dict, Any, Optional

from backend.core.config import MOODS
from backend.core.llm import get_json_completion

logger = logging.getLogger(__name__)


class ScriptAgent:
    """Writes scene-by-scene video scripts with visual search cues."""

    def create_script(
        self,
        topic: str,
        visual_context: str,
    ) -> Dict[str, Any]:
        """Create a structured video script.

        Args:
            topic: The video topic.
            visual_context: Visual theme for search queries.

        Returns:
            dict with keys: title, description, tags, mood, scenes.
        """
        mood_options_str = ", ".join(MOODS)

        prompt = f"""You are an elite short-form video documentary scriptwriter.
Create a gripping 40-50 second YouTube Shorts script about: '{topic}'.

CRITICAL PACING & HOOK RULES:
1. DO NOT start with cliches like "Did you know" or "Have you ever wondered".
2. Start immediately with an arrestingly vivid hook statement.
3. Keep the narration conversational, rhythmic, and high-suspense.
4. Structure into 4 to 5 concise narrative scenes.

CRITICAL VISUAL SEARCH RULES:
1. The "visual" field MUST be 1 to 3 words optimized for stock video libraries (Pexels/Pixabay).
2. Use concrete, filmable nouns (e.g., "telescope galaxy", "diver underwater", "ancient temple stone", "neon city rain").
3. NEVER search abstract ideas like "mystery" or "evil".
4. Current Visual Theme: {visual_context}

Return ONLY valid JSON with this exact schema:
{{
    "title": "Short Punchy Viral Title (Max 60 chars)",
    "description": "Engaging 2-sentence description for YouTube Shorts with hashtags.",
    "tags": ["#Shorts", "#Mystery", "#Facts", "#Discovery", "#Viral"],
    "mood": "Suspense",
    "scenes": [
        {{"text": "Hook sentence that stops the viewer from scrolling.", "visual": "{visual_context}"}},
        {{"text": "Second sentence escalating the strange facts or evidence.", "visual": "Dark {visual_context}"}},
        {{"text": "Third sentence detailing the crucial mystery or twist.", "visual": "{visual_context}"}},
        {{"text": "Fourth sentence revealing the chilling conclusion.", "visual": "{visual_context}"}}
    ]
}}

Select the single most fitting mood from this list:
{mood_options_str}"""

        try:
            data = get_json_completion(prompt)

            if not isinstance(data, dict):
                raise ValueError("Script output was not a dictionary")

            scenes = data.get("scenes", [])
            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Script scenes is empty or invalid")

            # Validate mood
            raw_mood = str(data.get("mood", "Suspense")).strip().capitalize()
            if raw_mood not in MOODS:
                raw_mood = "Suspense"
            data["mood"] = raw_mood

            # Sanitize scenes
            sanitized_scenes = []
            for sc in scenes:
                if isinstance(sc, dict) and sc.get("text"):
                    text = str(sc["text"]).strip()
                    vis = str(sc.get("visual", visual_context)).strip() or visual_context
                    sanitized_scenes.append({"text": text, "visual": vis})

            if len(sanitized_scenes) < 2:
                raise ValueError("Insufficient valid scenes in script")

            data["scenes"] = sanitized_scenes
            return data

        except Exception as e:
            logger.warning(f"Script Agent generation error: {e}")
            return {
                "title": topic[:60],
                "description": f"Exploring the incredible truth behind {topic}. #Shorts #Facts",
                "tags": ["#Shorts", "#Facts", "#Viral", "#Mystery"],
                "mood": "Suspense",
                "scenes": [
                    {
                        "text": f"What if everything you believed about {topic} was wrong?",
                        "visual": visual_context,
                    },
                    {
                        "text": "Deep beneath the surface, researchers made an astonishing discovery.",
                        "visual": f"Dark {visual_context}",
                    },
                    {
                        "text": "The evidence they found challenges our entire understanding of reality.",
                        "visual": visual_context,
                    },
                    {
                        "text": "And the most terrifying part is, this is only the beginning.",
                        "visual": visual_context,
                    },
                ],
            }
