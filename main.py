import os
import json
import asyncio
import requests
import random
import time
import shutil
import re
import gc
from dotenv import load_dotenv

# Import Video Tools
from moviepy.editor import *
from moviepy.audio.fx.all import audio_loop
import edge_tts
from groq import Groq

# --- CONFIGURATION ---
load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

# 🔴 PATHS
OUTPUT_FOLDER = os.getenv("OUTPUT_PATH", r"D:\Aivideos")
MUSIC_FOLDER = os.getenv("MUSIC_PATH", r"D:\Aivideos\music")

print(f"📂 Output configured to: {OUTPUT_FOLDER}")
print(f"🎵 Music configured to: {MUSIC_FOLDER}")

if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)
if not os.path.exists(MUSIC_FOLDER): os.makedirs(MUSIC_FOLDER)

# Initialize Groq Client
client = Groq(api_key=GROQ_KEY)

# --- HELPER: CONTEXT DETECTOR (NEW FIX) ---
def get_visual_context(topic):
    """Determines the visual theme based on the topic keywords."""
    t = topic.lower()
    if any(x in t for x in ['sea', 'ocean', 'water', 'lake', 'river', 'island', 'beach', 'ship', 'boat']):
        return "Underwater"
    if any(x in t for x in ['space', 'star', 'galaxy', 'universe', 'planet', 'moon', 'sky', 'solar']):
        return "Space"
    if any(x in t for x in ['history', 'ancient', 'ruin', 'civilization', 'temple', 'egypt', 'rome']):
        return "Ancient Ruins"
    if any(x in t for x in ['tech', 'robot', 'future', 'ai', 'cyber', 'simulation', 'glitch']):
        return "Technology"
    if any(x in t for x in ['forest', 'jungle', 'nature', 'mountain']):
        return "Forest"
    return "Dark Atmosphere" # A better generic fallback than "Abstract"

# --- HELPER: VERTICAL RESIZE ---
def resize_to_vertical(clip, width=1080, height=1920):
    target_ratio = width / height
    clip_ratio = clip.w / clip.h
    
    if clip_ratio > target_ratio:
        clip = clip.resize(height=height)
        clip = clip.crop(x1=(clip.w/2 - width/2), width=width, height=height)
    else:
        clip = clip.resize(width=width)
        if clip.h > height:
            clip = clip.crop(y1=(clip.h/2 - height/2), width=width, height=height)
    return clip

# --- 1. TOPIC AGENT ---
class TopicAgent:
    def generate_viral_topic(self):
        niches = [
            "A terrifying Space Anomaly",
            "A Dark Psychology Fact",
            "A Bizarre Historical Event",
            "A Deep Sea Mystery",
            "A Glitch in the Simulation",
            "A Future Technology Prediction",
            "A Serial Killer Fact",
            "An Ancient Civilization Mystery"
        ]
        selected_niche = random.choice(niches)
        
        print(f"🧠 Topic Agent: Brainstorming about '{selected_niche}'...")
        
        prompt = f"""
        Generate ONE catchy, viral topic for a YouTube Short about: {selected_niche}.
        Make it sound shocking or mysterious.
        Output ONLY the raw topic text. No quotes.
        """
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.9, 
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Topic Error: {e}")
            return "The Bloop Mystery"

# --- 2. SCRIPT AGENT (CONTEXT AWARE) ---
class ScriptAgent:
    def create_script(self, topic, visual_context):
        print(f"📝 Script Agent: Writing script for '{topic}' (Context: {visual_context})...")
        
        # We force the AI to use the context in its search terms
        prompt = f"""
        You are a YouTube Expert. Create a 30-second YouTube Shorts script about '{topic}' strictly in JSON format.
        
        CRITICAL VISUAL INSTRUCTIONS:
        1. The "visual" field must be a 1-2 word search term for Pexels.
        2. CONTEXT RULE: If the topic is about the Ocean, EVERY visual must be related to water (e.g., "Underwater", "Shark", "Ship"). NEVER use "City" or "Street".
        3. If the topic is Space, EVERY visual must be space-related.
        4. Current Context: {visual_context}
        
        Structure Example:
        {{
            "title": "Viral Title",
            "description": "Video description...",
            "tags": ["#Tag1", "#Tag2"],
            "mood": "Suspense",
            "scenes": [
                {{"text": "Hook sentence.", "visual": "{visual_context}"}}, 
                {{"text": "Body sentence.", "visual": "Dark {visual_context}"}}
            ]
        }}
        """
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}, 
                temperature=0.75
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            print(f"❌ Script Error: {e}")
            return {
                "title": topic, 
                "description": f"Amazing facts about {topic}",
                "tags": ["#Shorts"],
                "mood": "Suspense",
                "scenes": [{"text": f"Did you know this about {topic}?", "visual": visual_context}]
            }

# --- 3. AUDIO AGENT ---
class AudioAgent:
    async def generate_voice(self, text, filename):
        print(f"🎙️ Audio Agent: Speaking...")
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(filename)
        return filename

# --- 4. MUSIC AGENT ---
class MusicAgent:
    def get_music_by_mood(self, mood):
        mood = mood.strip().capitalize()
        target_folder = os.path.join(MUSIC_FOLDER, mood)
        if os.path.exists(target_folder):
            songs = [f for f in os.listdir(target_folder) if f.endswith(".mp3")]
            if songs: return os.path.join(target_folder, random.choice(songs))
        
        all_songs = []
        for root, dirs, files in os.walk(MUSIC_FOLDER):
            for file in files:
                if file.endswith(".mp3"): all_songs.append(os.path.join(root, file))
        if all_songs: return random.choice(all_songs)
        return None

# --- 5. VISUAL AGENT (SMART FALLBACK) ---
class VisualAgent:
    def __init__(self, api_key):
        self.headers = {"Authorization": api_key}

    def download_video(self, query, filename, fallback_context):
        # Clean query
        simple_query = query.split(" ")[0]
        
        # 1. Try the specific query from the script
        print(f"👁️ Visual Agent: Searching Pexels for '{simple_query}'...")
        if self._try_download(simple_query, filename):
            return filename
            
        # 2. If that fails, try the CONTEXT (e.g., "Underwater" instead of "City")
        print(f"⚠️ Search failed. Retrying with Context: '{fallback_context}'...")
        if self._try_download(fallback_context, filename):
            return filename
            
        # 3. Last Resort
        print(f"⚠️ Context failed. Using generic fallback...")
        if self._try_download("Dark Atmosphere", filename):
            return filename
            
        return None

    def _try_download(self, query, filename):
        url = "https://api.pexels.com/videos/search"
        params = {"query": query, "per_page": 1, "orientation": "portrait", "size": "medium"}
        try:
            r = requests.get(url, headers=self.headers, params=params)
            data = r.json()
            if data.get('videos'):
                video_url = data['videos'][0]['video_files'][0]['link']
                with requests.get(video_url, stream=True) as r_vid:
                    with open(filename, 'wb') as f:
                        for chunk in r_vid.iter_content(chunk_size=1024):
                            f.write(chunk)
                
                if os.path.exists(filename) and os.path.getsize(filename) > 5000:
                    return True
        except: pass
        return False

# --- 6. EDITOR AGENT ---
class EditorAgent:
    def edit_video(self, audio_path, music_path, video_paths, output_name):
        print("🎬 Editor Agent: Mixing & Rendering...")
        try:
            gc.collect()
            voice_clip = AudioFileClip(audio_path)
            
            final_audio = voice_clip
            if music_path and os.path.exists(music_path):
                music_clip = AudioFileClip(music_path)
                if music_clip.duration < voice_clip.duration:
                    music_clip = audio_loop(music_clip, duration=voice_clip.duration + 2)
                music_clip = music_clip.subclip(0, voice_clip.duration)
                music_clip = music_clip.volumex(0.12)
                final_audio = CompositeAudioClip([voice_clip, music_clip])

            valid_clips = [v for v in video_paths if v and os.path.exists(v)]
            if not valid_clips: raise Exception("No valid videos found!")
            
            clip_duration = voice_clip.duration / len(valid_clips)
            final_clips = []
            
            for v_path in valid_clips:
                clip = VideoFileClip(v_path)
                clip = resize_to_vertical(clip) 
                clip = clip.subclip(0, clip_duration).without_audio()
                final_clips.append(clip)

            final_video = concatenate_videoclips(final_clips, method="compose")
            final_video = final_video.set_audio(final_audio)
            
            temp_output = "temp_render.mp4"
            final_video.write_videofile(temp_output, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=1)
            
            final_video.close()
            voice_clip.close()
            if 'music_clip' in locals(): music_clip.close()
            for c in final_clips: c.close()
            gc.collect()

            final_path = os.path.join(OUTPUT_FOLDER, output_name)
            shutil.move(temp_output, final_path)
            return final_path
        except Exception as e:
            print(f"❌ Editor Failed: {e}")
            if os.path.exists("temp_render.mp4"):
                try:
                    os.remove("temp_render.mp4")
                except:
                    pass
            return None

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name).replace(' ', '_')

# --- MAIN LOOP ---
async def main():
    brain = TopicAgent()
    writer = ScriptAgent()
    speaker = AudioAgent()
    dj = MusicAgent() 
    finder = VisualAgent(PEXELS_KEY)
    editor = EditorAgent()

    # 1. Topic & Context
    topic = brain.generate_viral_topic()
    visual_context = get_visual_context(topic) # <--- NEW INTELLIGENCE
    print(f"🧠 Context Detected: {visual_context}")
    
    # 2. Script
    script_data = writer.create_script(topic, visual_context)
    mood = script_data.get("mood", "Chill")
    
    # 3. Assets
    unique_id = int(time.time())
    audio_file = f"temp_voice_{unique_id}.mp3"
    music_file = dj.get_music_by_mood(mood)
    
    await speaker.generate_voice(" ".join([s['text'] for s in script_data['scenes']]), audio_file)
    
    # 4. Visuals (With Fallback)
    video_files = []
    for i, scene in enumerate(script_data['scenes']):
        v_file = f"temp_clip_{unique_id}_{i}.mp4"
        # We pass the visual_context as the backup plan
        downloaded = finder.download_video(scene['visual'], v_file, visual_context)
        if downloaded: video_files.append(downloaded)
        elif video_files: video_files.append(video_files[-1])

    # 5. Edit
    safe_topic = sanitize_filename(topic)
    final_path = editor.edit_video(audio_file, music_file, video_files, f"{safe_topic}.mp4")
    
    # 6. Save Metadata
    if final_path: 
        print(f"\n✅ SUCCESS! Saved: {final_path}")
        meta_path = os.path.join(OUTPUT_FOLDER, f"{safe_topic}_INFO.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"TITLE: {script_data.get('title', topic)}\n\n")
            f.write(f"DESCRIPTION:\n{script_data.get('description', 'No desc')}\n\n")
            f.write(f"TAGS: {' '.join(script_data.get('tags', []))}")

    # 7. Cleanup
    time.sleep(1)
    try: os.remove(audio_file)
    except: pass
    for v in video_files:
        try: os.remove(v)
        except: pass

if __name__ == "__main__":
    print(f"🚀 AutoTuber Groq Edition (Context Aware) Started!")
    while True:
        try:
            asyncio.run(main())
            print("💤 Cooling down (10 seconds)...") 
            time.sleep(10)
        except KeyboardInterrupt:
            break
        except Exception as e: 
            print(f"Error: {e}")
            time.sleep(60)