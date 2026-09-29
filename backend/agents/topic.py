"""Topic Agent — generates viral video topics using the LLM."""

import random
import logging
from typing import Optional

from backend.core.config import NICHES
from backend.core.llm import get_completion

logger = logging.getLogger(__name__)

# Curated viral angles to prevent repetitive topic phrasing
VIRAL_ANGLES = [
    "Focus on an unsettling, obscure detail that almost nobody knows.",
    "Frame it as a mystery that still terrifies researchers.",
    "Make it sound like a forbidden revelation or classified discovery.",
    "Emphasize the mind-bending scientific or psychological paradox.",
    "Present it as a chilling sequence of real events that defies logic.",
]


class TopicAgent:
    """Brainstorms catchy, viral topics for short-form videos."""

    def generate(self, niche: Optional[str] = None) -> str:
        """Generate a viral topic.

        Args:
            niche: Specific niche string. None = random (Chaos Mode).

        Returns:
            A catchy, high-engagement topic string.
        """
        selected_niche = niche or random.choice(NICHES)
        angle = random.choice(VIRAL_ANGLES)

        prompt = (
            f"You are a top-tier viral YouTube Shorts producer.\n"
            f"Generate ONE incredibly catchy, high-retention topic about: {selected_niche}.\n"
            f"Creative Direction: {angle}\n\n"
            f"Requirements:\n"
            f"- Specific, punchy, and intriguing (5 to 10 words).\n"
            f"- Avoid generic clickbait cliches like 'You won't believe this'.\n"
            f"- Output ONLY the raw topic text. No quotes, no markdown, no numbering."
        )

        try:
            topic = get_completion(prompt, temperature=0.92)
            cleaned = topic.strip().strip('"').strip("'").strip("`")
            # Remove any leading numbered lists like "1. "
            if cleaned and cleaned[0].isdigit() and cleaned[1:3] in [". ", ": "]:
                cleaned = cleaned[3:].strip()
            return cleaned or f"The Mystery of {selected_niche}"
        except Exception as e:
            logger.warning(f"Topic Agent generation error: {e}")
            fallback_options = [
                f"The Terrifying Secret Behind {selected_niche}",
                f"What Scientists Found Inside {selected_niche}",
                f"The Unsolved Enigma of {selected_niche}",
            ]
            return random.choice(fallback_options)
