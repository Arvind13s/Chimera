🦁 Project Chimera

**Hey guys, meet Chimera.**

Chimera is an **Agentic AI** that lives in your terminal. It autonomously creates 50-60s vertical videos with its own brain, voice, and eyes.

I didn’t write the script. I didn’t pick the clips. I didn’t edit a single frame.
I just hit "Run," and Chimera took over.

---

## 🤖 How It Works

It’s not just a script; it’s a **Multi-Agent System** where four distinct AI "employees" work together to build a video from scratch:

* 🧠 **The Brain (Groq + Llama 3):** It brainstorms its own viral concepts (using "Chaos Mode" for randomness) and writes a structured story.
* 👁️ **The Eyes (Pexels API):** It scours stock footage libraries using a custom **Context-Aware** search engine (so it knows "Blue" means "Ocean," not "Blue Shirt").
* 🎙️ **The Voice (Edge-TTS):** It generates human-quality neural voiceovers in real-time.
* 🎬 **The Hands (MoviePy):** It edits, resizes, crops, and renders the final video file completely on its own.

---

## 🚀Features

- 🧠 Hyper‑fast scriptwriting via Groq (`llama-3.3-70b-versatile`).
- 🌪️ Chaos Mode: random niches (Space, Dark Psychology, Ancient History, etc.).
- 👁️ Smart visual search: converts abstract ideas into concrete, stock‑searchable visuals.
- 🛡️ Crash‑proofing: validates downloads and skips corrupt/empty clips before editing.
- 💾 Memory‑safe rendering: MoviePy with `preset="ultrafast"` and `threads=1`.
- 📄 Auto‑metadata: generates Title, Description, and Hashtags `.txt` per video.

---

## Tech Stack (Agentic Workflow)

| Component   | Technology                            | Role                                     |
|-------------|----------------------------------------|------------------------------------------|
| Brain       | Groq API (Llama‑3.3‑70B)               | Topic ideation + JSON script generation  |
| Voice       | Edge‑TTS (Microsoft Neural)            | Human‑like voiceover synthesis           |
| Eyes        | Pexels Videos API                      | Royalty‑free stock footage               |
| Hands       | MoviePy + FFmpeg                       | Editing, resizing, mixing, rendering     |
| Ears        | Local music library (mp3)              | Mood‑based background music              |

---

## Prerequisites

- Python 3.9–3.11 (Dockerfile uses 3.9)
- API keys:
  - `GROQ_API_KEY` (Groq chat completions)
  - `PEXELS_API_KEY` (Pexels Videos API)
- FFmpeg (bundled via `imageio-ffmpeg` and also installed in Docker image). If MoviePy cannot find FFmpeg, install system ffmpeg and ensure it’s on PATH.

Paths are configurable via environment variables (with Windows defaults):
- `OUTPUT_PATH` (default: `D:\\Aivideos`)
- `MUSIC_PATH` (default: `D:\\Aivideos\\music`)
The app prints the active paths on startup.

---

## Installation

1) Create a virtual environment and install dependencies

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Provide API keys and optional paths

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_key_here
PEXELS_API_KEY=your_pexels_key_here
# Optional overrides (otherwise defaults are used)
OUTPUT_PATH=D:\\Aivideos
MUSIC_PATH=D:\\Aivideos\\music
```

Or set them for the current PowerShell session:

```powershell
$env:GROQ_API_KEY = "your_groq_key_here"
$env:PEXELS_API_KEY = "your_pexels_key_here"
$env:OUTPUT_PATH = "D:\\Aivideos"
$env:MUSIC_PATH = "D:\\Aivideos\\music"
```

3) Organize your music library (recommended)

```
D:\Aivideos\
  └── music\
      ├── Suspense\   # Put tense/scary mp3s here
      ├── Chill\      # Calm/lofi mp3s
      ├── Epic\       # Intense mp3s
      └── Dark\       # Horror mp3s
```

You can change the paths via `.env` (`OUTPUT_PATH`, `MUSIC_PATH`) without editing code. Edit `main.py` only if you need different defaults.

---

## Usage

Run the main script:

```powershell
python main.py
```

What happens:
- Topic Agent picks a random niche (e.g., “Deep Sea Mystery”).
- Script Agent asks Groq for a strict‑JSON, scene‑based script with concrete visuals and mood.
- Visual Agent fetches portrait stock videos from Pexels per scene.
- Audio Agent generates a voiceover using `en-US-ChristopherNeural` (Edge‑TTS).
- Music Agent picks a track from your local library matching the mood.
- Editor Agent resizes to 1080×1920, stitches scenes, mixes audio, and renders MP4.

Output:
- Final video and an `_INFO.txt` metadata file are saved to your `OUTPUT_PATH` (defaults to `D:\\Aivideos`).

The app runs in a loop (cooldown between runs). Press Ctrl+C to stop.

---

## Docker (optional)

A minimal Dockerfile is provided and installs FFmpeg and ImageMagick.

Important: paths default to Windows style. For Linux‑based containers, set `OUTPUT_PATH` and `MUSIC_PATH` to Linux paths (e.g., `/data`) before building/running.

Build:

```bash
docker build -t chimera .
```

Run (after setting `OUTPUT_PATH=/data`):

```bash
docker run --rm -it \
  -e GROQ_API_KEY=your_groq_key_here \
  -e PEXELS_API_KEY=your_pexels_key_here \
  -e OUTPUT_PATH=/data \
  -e MUSIC_PATH=/data/music \
  -v /host/path/aivideos:/data \
  chimera
```

---

## Configuration Tips

- Change TTS voice: edit `edge_tts.Communicate(text, "en-US-ChristopherNeural")` in `main.py`.
- Adjust canvas size: update `resize_to_vertical(width=1080, height=1920)`.
- Music loudness: tweak `music_clip.volumex(0.12)`.
- Model/creativity: adjust `model` and `temperature` in Topic/Script agents.
- Paths: prefer `OUTPUT_PATH` and `MUSIC_PATH` env vars; defaults are set in `main.py`.

---

## Troubleshooting

- MoviePy/FFmpeg issues: ensure `imageio-ffmpeg` works or install `ffmpeg` on PATH.
- “No music found”: add `.mp3` files under your music folder (mood subfolders optional).
- Pexels empty results: verify API key/quotas; project falls back to an abstract search when needed.
- Memory constraints: rendering uses single thread and ultrafast preset; reduce scenes or script length if needed.

---

## Environment Variables

- `GROQ_API_KEY`: Groq API key for chat completions
- `PEXELS_API_KEY`: Pexels Videos API key
- `OUTPUT_PATH`: output directory for rendered videos and metadata (default `D:\\Aivideos`)
- `MUSIC_PATH`: root directory for local music library (default `D:\\Aivideos\\music`)

## Rate Limits (FYI)

- Groq: Free tier is generous but limited (varies by model).
- Pexels: Typically ~200 requests/hour.

---

## Roadmap

- Chaos Mode (randomized topics)
- Corruption‑proofing for downloads
- Automatic metadata generation
- Configurable output paths via environment variables

---

## Contributing

Contributions welcome! Improvements to prompts, visual selection logic, or MoviePy render parameters are especially helpful. Please open an issue or submit a PR.

---

## Disclaimer

This tool is for educational purposes. Always review generated content before publishing and ensure you comply with YouTube policies, content rights, and attribution requirements (e.g., Pexels license). The author is not responsible for misuse.
