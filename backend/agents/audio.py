"""Audio Agent — generates voiceover using Edge-TTS neural voices."""

import asyncio
import concurrent.futures

import edge_tts

from backend.core.config import VOICES


class AudioAgent:
    """Generates human-quality neural voiceovers via Edge-TTS."""

    async def _generate_async(self, text, filepath, voice_id):
        """Internal async TTS generation."""
        communicate = edge_tts.Communicate(text, voice_id)
        await communicate.save(filepath)
        return filepath

    def generate_voice(self, text, filepath,
                       voice="Christopher (Male, US)"):
        """Generate a voiceover audio file.

        Args:
            text: The narration text.
            filepath: Output path (.mp3).
            voice: Voice name from config.VOICES.

        Returns:
            Path to the generated audio file.
        """
        voice_id = VOICES.get(voice, "en-US-ChristopherNeural")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self._generate_async(text, filepath, voice_id),
                )
                return future.result(timeout=120)
        else:
            return asyncio.run(
                self._generate_async(text, filepath, voice_id)
            )
