"""Editor Agent — composites clips, voiceover, and music into final video."""

import os
import math
import shutil
import logging
from typing import List, Optional

try:
    from moviepy import (
        AudioFileClip,
        CompositeAudioClip,
        VideoFileClip,
        concatenate_videoclips,
    )
    from moviepy.audio.fx import AudioLoop
    _MOVIEPY_V2 = True
except (ModuleNotFoundError, ImportError):
    from moviepy.editor import (  # type: ignore[import-not-found]
        AudioFileClip,
        CompositeAudioClip,
        VideoFileClip,
        concatenate_videoclips,
    )
    from moviepy.audio.fx.all import audio_loop  # type: ignore[import-not-found]
    _MOVIEPY_V2 = False

from backend.core.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    VIDEO_THREADS,
    OUTPUT_DIR,
)
from backend.core.utils import resize_to_vertical

logger = logging.getLogger(__name__)


def _subclip(clip, start, end):
    return clip.subclipped(start, end) if _MOVIEPY_V2 else clip.subclip(start, end)


def _without_audio(clip):
    return clip.without_audio() if _MOVIEPY_V2 else clip.without_audio()


def _set_audio(clip, audio):
    return clip.with_audio(audio) if _MOVIEPY_V2 else clip.set_audio(audio)


def _audio_loop(clip, duration):
    if _MOVIEPY_V2:
        return clip.with_effects([AudioLoop(duration=duration)])
    return audio_loop(clip, duration=duration)


def _set_volume(clip, factor: float):
    """Safely adjust audio clip volume across MoviePy v1 and v2."""
    if hasattr(clip, "volumex"):
        return clip.volumex(factor)
    elif hasattr(clip, "multiply_volume"):
        return clip.multiply_volume(factor)
    return clip.with_volume_scaled(factor)


class EditorAgent:
    """Mixes video clips, voiceover, and music into a rendered video."""

    def edit_video(
        self,
        audio_path: str,
        music_path: Optional[str],
        video_paths: List[str],
        output_name: str,
    ) -> Optional[str]:
        """Render the final video.

        Args:
            audio_path: Path to the voiceover audio file.
            music_path: Path to background music (or None).
            video_paths: List of paths to video clips.
            output_name: Filename for the output.

        Returns:
            Path to the final video, or None on failure.
        """
        clips_to_close = []
        temp_output = None

        try:
            voice_clip = AudioFileClip(audio_path)
            clips_to_close.append(voice_clip)
            target_duration = voice_clip.duration

            final_audio = voice_clip
            if music_path and os.path.exists(music_path):
                try:
                    music_clip = AudioFileClip(music_path)
                    clips_to_close.append(music_clip)

                    if music_clip.duration < target_duration:
                        music_clip = _audio_loop(
                            music_clip, duration=target_duration + 2
                        )
                    music_clip = _subclip(music_clip, 0, target_duration)
                    music_clip = _set_volume(music_clip, 0.12)
                    final_audio = CompositeAudioClip([voice_clip, music_clip])
                except Exception as e:
                    logger.warning(
                        f"Editor: Background music mixing skipped ({e}), "
                        "continuing with voiceover."
                    )

            valid_clips = [v for v in video_paths if v and os.path.exists(v)]
            if not valid_clips:
                raise RuntimeError("No valid video clips available to edit!")

            per_clip_duration = target_duration / len(valid_clips)
            final_clips = []

            for v_path in valid_clips:
                try:
                    clip = VideoFileClip(v_path)
                    clips_to_close.append(clip)
                    clip = resize_to_vertical(clip, VIDEO_WIDTH, VIDEO_HEIGHT)

                    if clip.duration < per_clip_duration and clip.duration > 0.5:
                        repeats = int(math.ceil(per_clip_duration / clip.duration))
                        repeated = concatenate_videoclips([clip] * repeats)
                        clips_to_close.append(repeated)
                        scene_clip = _without_audio(
                            _subclip(repeated, 0, per_clip_duration)
                        )
                    else:
                        actual_dur = min(per_clip_duration, clip.duration)
                        scene_clip = _without_audio(_subclip(clip, 0, actual_dur))

                    final_clips.append(scene_clip)
                except Exception as e:
                    logger.warning(f"Editor: Skipping clip {v_path} ({e})")

            if not final_clips:
                raise RuntimeError("All video clips failed to process!")

            final_video = concatenate_videoclips(final_clips, method="compose")
            clips_to_close.append(final_video)

            if final_video.duration < target_duration:
                deficit = target_duration - final_video.duration
                last_clip = final_clips[-1]
                filler = _subclip(last_clip, 0, min(deficit, last_clip.duration))
                final_video = concatenate_videoclips([final_video, filler], method="compose")
                clips_to_close.append(final_video)

            final_video = _set_audio(final_video, final_audio)

            temp_output = os.path.join(OUTPUT_DIR, f"_temp_{output_name}")
            final_video.write_videofile(
                temp_output,
                fps=VIDEO_FPS,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                threads=VIDEO_THREADS,
                logger=None,
            )

            final_path = os.path.join(OUTPUT_DIR, output_name)
            if os.path.exists(final_path):
                os.remove(final_path)
            shutil.move(temp_output, final_path)
            logger.info(f"Video rendered successfully: {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"Editor Agent Failed: {e}", exc_info=True)
            return None
        finally:
            for c in clips_to_close:
                try:
                    c.close()
                except Exception:
                    pass
            if temp_output and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError:
                    pass
