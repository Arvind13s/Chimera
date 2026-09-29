---
title: Chimera AI Video Studio
emoji: 🦁
colorFrom: red
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: Autonomous multi-agent pipeline for short-form video
---

# 🦁 Chimera v3.0 — Autonomous AI Video Creation Studio

**Chimera** is an autonomous multi-agent AI system that generates viral short-form videos (YouTube Shorts, Instagram Reels, TikTok) end-to-end. Six specialized AI agents collaborate in real-time: brainstorming topics, writing scripts, generating voiceovers, sourcing music, finding stock footage, and rendering cinematic videos.

## ✨ Features

- **🧠 Topic Agent** — Generates unique, high-retention viral topics using Groq LLM across 60+ niches
- **📝 Script Agent** — Crafts scene-by-scene documentary scripts with optimized pacing and visual cues
- **🎙️ Audio Agent** — Neural voiceover generation via Edge-TTS with 8 voice options
- **🎵 Music Agent** — Mood-matched music from Jamendo, Freesound, and synthetic fallback
- **👁️ Visual Agent** — Parallel stock video search across Pexels and Pixabay
- **🎬 Editor Agent** — Composites everything into a polished 9:16 Short/Reel (1080×1920 MP4)

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Plain HTML, CSS, and JavaScript + Tailwind CDN |
| **Backend** | FastAPI + Uvicorn |
| **LLM** | Groq API |
| **TTS** | Edge-TTS (Neural Voices) |
| **Video** | MoviePy + FFmpeg |
| **Music** | Jamendo API, Freesound API, MusicBrainz |
| **Stock Video** | Pexels API, Pixabay API |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- FFmpeg installed and in PATH

### 1. Clone & Install

```bash
git clone https://github.com/Arvind13s/Chimera.git
cd Chimera

# Backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

**Required:**
- `GROQ_API_KEY` — Get at [console.groq.com](https://console.groq.com/keys)
- `PEXELS_API_KEY` — Get at [pexels.com/api](https://www.pexels.com/api/)

**Optional (recommended):**
- `PIXABAY_API_KEY` — Fallback video source
- `JAMENDO_CLIENT_ID` — CC-licensed music
- `FREESOUND_API_KEY` — Additional music source

### 3. Run

**Run the application:**

```bash
.venv\Scripts\python.exe -m backend.server
```

Open [http://localhost:8000](http://localhost:8000) in your browser. The FastAPI server serves the frontend from `backend/frontend`.

**CLI Mode:**

```bash
.venv\Scripts\python.exe cli.py
.venv\Scripts\python.exe cli.py --topic "The mystery of the Bermuda Triangle"
```

## 📁 Project Structure

```
Chimera/
├── backend/           # FastAPI server and static frontend
│   ├── agents/        # 6 AI agents (topic, script, audio, music, visual, editor)
│   ├── core/          # Config, LLM, pipeline, auth, utils
│   ├── frontend/      # HTML, CSS, and JavaScript client
│   └── routes/        # REST + SSE API endpoints
├── cli.py             # Command-line runner
├── .env               # API keys (gitignored)
└── requirements.txt   # Python dependencies
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
