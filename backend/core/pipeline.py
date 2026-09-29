"""Pipeline Orchestrator — coordinates all agents to generate a video.

This is a **generator** function: each ``yield`` pushes a progress update
so the FastAPI SSE endpoint can stream updates to the browser frontend.
"""

import os
import time
import logging
import concurrent.futures
from typing import Generator, Tuple, Optional, Dict, Any, List

from backend.core.config import TEMP_DIR
from backend.core.utils import (
    get_visual_context,
    sanitize_filename,
    sanitize_topic_input,
)
from backend.agents.topic import TopicAgent
from backend.agents.script import ScriptAgent
from backend.agents.audio import AudioAgent
from backend.agents.music import MusicAgent
from backend.agents.visual import VisualAgent
from backend.agents.editor import EditorAgent

logger = logging.getLogger(__name__)


def generate_video_stream(
    niche: Optional[str] = None,
    custom_topic: Optional[str] = None,
    voice: str = "Christopher (Male, US)",
) -> Generator[Tuple[str, Optional[str], Optional[Dict[str, Any]]], None, None]:
    """Generate a video through the multi-agent pipeline.

    Yields:
        tuple: (message, video_path | None, metadata | None)
    """
    brain = TopicAgent()
    writer = ScriptAgent()
    speaker = AudioAgent()
    dj = MusicAgent()
    finder = VisualAgent()
    editor = EditorAgent()

    unique_id = int(time.time())
    temp_files = set()

    try:
        # ── Stage 1: Topic ──────────────────────────────────
        yield "🧠 Stage 1/6 — Brainstorming Topic...", None, None

        cleaned_custom = sanitize_topic_input(custom_topic) if custom_topic else None
        if cleaned_custom:
            topic = cleaned_custom
            yield f"📌 Using custom topic: '{topic}'", None, None
        else:
            topic = brain.generate(niche=niche)
            yield f"💡 Generated topic: '{topic}'", None, None

        visual_context = get_visual_context(topic)
        yield f"🎨 Visual theme: {visual_context}", None, None

        # ── Stage 2: Script ─────────────────────────────────
        yield "\n📝 Stage 2/6 — Writing High-Retention Script...", None, None

        script_data = writer.create_script(topic, visual_context)
        mood = script_data.get("mood", "Suspense")
        scenes = script_data.get("scenes", [])
        yield f"🎭 Mood: {mood}  |  Scenes: {len(scenes)}", None, None

        for i, scene in enumerate(scenes):
            text = scene.get("text", "")[:75]
            yield f"   📄 Scene {i + 1}: \"{text}...\"", None, None

        # ── Stage 3: Voiceover ──────────────────────────────
        yield "\n🎙️ Stage 3/6 — Generating Neural Voiceover...", None, None

        full_text = " ".join(s.get("text", "") for s in scenes)
        audio_file = os.path.join(TEMP_DIR, f"voice_{unique_id}.mp3")
        temp_files.add(audio_file)

        speaker.generate_voice(full_text, audio_file, voice=voice)
        yield f"✅ Voiceover generated ({voice}).", None, None

        # ── Stage 4: Background Music ───────────────────────
        yield f"\n🎵 Stage 4/6 — Selecting Atmosphere for '{mood}'...", None, None

        music_file = dj.get_music_by_mood(mood, duration=45.0)
        if music_file and os.path.exists(music_file):
            temp_files.add(music_file)
            yield f"✅ Atmospheric soundtrack ready ({os.path.basename(music_file)}).", None, None
        else:
            yield "⚠️ Audio synthesizer skipped — continuing with voiceover only.", None, None

        # ── Stage 5: Parallel Visual Search & Download ──────
        yield "\n👁️ Stage 5/6 — Fetching Stock Visuals in Parallel...", None, None

        video_files_map = {}

        def _fetch_clip(scene_idx: int, search_term: str, target_file: str):
            res = finder.download_video(search_term, target_file, visual_context)
            return scene_idx, res

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(scenes))) as pool:
            futures = []
            for i, scene in enumerate(scenes):
                vis = scene.get("visual", visual_context)
                v_file = os.path.join(TEMP_DIR, f"clip_{unique_id}_{i}.mp4")
                temp_files.add(v_file)
                futures.append(pool.submit(_fetch_clip, i, vis, v_file))

            for fut in concurrent.futures.as_completed(futures):
                idx, downloaded = fut.result()
                video_files_map[idx] = downloaded
                vis_term = scenes[idx].get("visual", visual_context)
                if downloaded:
                    yield f"   ✅ Scene {idx + 1} ('{vis_term}'): Clip ready.", None, None
                else:
                    yield f"   ⚠️ Scene {idx + 1} ('{vis_term}'): Clip fallback needed.", None, None

        video_files: List[str] = []
        for i in range(len(scenes)):
            clip = video_files_map.get(i)
            if clip and os.path.exists(clip):
                video_files.append(clip)
            elif video_files:
                video_files.append(video_files[-1])
                yield f"   ♻️ Scene {i + 1}: Reusing adjacent scene visual.", None, None

        if not video_files:
            yield "❌ FATAL: Could not download any stock video clips!", None, None
            return

        yield f"\n📦 {len(video_files)} video clips prepared for composition.", None, None

        # ── Stage 6: Rendering ──────────────────────────────
        yield (
            "\n🎬 Stage 6/6 — Rendering Final Video...\n"
            "⏳ Stitching visuals, syncing audio, encoding 1080x1920 MP4...",
            None,
            None,
        )

        safe_topic = sanitize_filename(topic)
        output_name = f"{safe_topic}_{unique_id}.mp4"

        final_path = editor.edit_video(
            audio_file, music_file, video_files, output_name
        )

        if not final_path or not os.path.exists(final_path) or os.path.getsize(final_path) < 10000:
            yield "❌ Video rendering failed during encoding!", None, None
            return

        metadata = {
            "title": script_data.get("title", topic),
            "description": script_data.get("description", ""),
            "tags": script_data.get("tags", ["#Shorts", "#Viral"]),
            "topic": topic,
            "mood": mood,
            "scenes": len(scenes),
        }

        yield (
            f"\n✅ Video successfully rendered!\n"
            f"📁 Saved to: {final_path}\n"
            "🎉 Generation complete!",
            final_path,
            metadata,
        )

    finally:
        for f in temp_files:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except OSError:
                pass
