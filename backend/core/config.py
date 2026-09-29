"""Centralized configuration for Chimera v3.0."""

import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# ── Groq LLM API Key ───────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.8"))

# ── Stock Video APIs ─────────────────────────────────────────
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# ── Music APIs ───────────────────────────────────────────────
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID", "")
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")
FMA_API_KEY = os.getenv("FMA_API_KEY", "")

# ── MusicBrainz API Config ──────────────────────────────────
MUSICBRAINZ_APP_NAME = os.getenv("MUSICBRAINZ_APP_NAME", "Chimera-AI-Video-Generator")
MUSICBRAINZ_APP_VERSION = os.getenv("MUSICBRAINZ_APP_VERSION", "3.0.0")
MUSICBRAINZ_CONTACT = os.getenv("MUSICBRAINZ_CONTACT", "https://github.com/Arvind13s/Chimera")
MUSICBRAINZ_API_KEY = os.getenv("MUSICBRAINZ_API_KEY", "")

# ── Authentication & OAuth ───────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "chimera_super_secret_auth_key_2026")

# ── Email & OTP Verification ─────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip() or SMTP_USER or "noreply@chimera.ai"
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Chimera Studio")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes") or SMTP_PORT == 465
OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", "600"))  # 10 minutes
OTP_RESEND_COOLDOWN = int(os.getenv("OTP_RESEND_COOLDOWN", "30"))  # 30 seconds

# ── Paths ────────────────────────────────────────────────────
# PROJECT_ROOT = .../Chimera/backend  (the backend package directory)
# REPO_ROOT    = .../Chimera          (the repository top-level directory)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
TEMP_DIR = os.path.join(tempfile.gettempdir(), "chimera_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(REPO_ROOT, "outputs"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Video Config ─────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 24
VIDEO_THREADS = int(os.getenv("VIDEO_THREADS", str(min(4, os.cpu_count() or 1))))

# ── Categorized Content Niches (60+ Unique Niches) ───────────
NICHE_CATEGORIES = {
    "🌌 Deep Space & Cosmic Horrors": [
        "A terrifying Space Anomaly",
        "A rogue planet wandering the void",
        "A catastrophic Gamma-Ray Burst approaching Earth",
        "The mysterious Great Attractor pulling galaxies",
        "The haunting sound recorded near a supermassive black hole",
        "The Fermi Paradox and the Dark Forest Theory",
        "An eerie signal detected from deep space",
    ],
    "🧠 Dark Psychology & Mind Anomalies": [
        "A Dark Psychology Fact that chills you",
        "The psychological phenomenon of False Awakening",
        "The terrifying reality of Cotard's Delusion",
        "How optical illusions hijack your subconscious mind",
        "The Capgras Delusion where loved ones seem replaced",
        "The Bystander Effect pushed to terrifying extremes",
        "The bizarre neuroscience of Sleep Paralysis demons",
    ],
    "📜 Bizarre & Forgotten History": [
        "A Bizarre Historical Event lost to modern time",
        "The Dancing Plague that baffled medieval physicians",
        "The bizarre London Beer Flood catastrophe",
        "The uncontacted North Sentinel Island mystery",
        "The ancient Roman city that vanished overnight",
        "The secret submarine disaster of the Cold War",
        "The 1908 Tunguska event that leveled 80 million trees",
    ],
    "🌊 Abyssal Deep Sea Mysteries": [
        "A Deep Sea Mystery from the bottom of Mariana Trench",
        "The unidentified submarine sound known as 'The Bloop'",
        "The vanishing crew of the Mary Celeste ghost ship",
        "Colossal underwater waterfalls hidden under the ocean",
        "Bioluminescent creatures lurking in the midnight zone",
        "The submerged prehistoric continent of Zealandia",
        "Underwater sinkholes holding toxic ancient bacteria",
    ],
    "👾 Simulation Theory & Quantum Paradoxes": [
        "A Glitch in the Simulation caught in real life",
        "The Quantum Double Slit experiment breaking reality",
        "The Mandela Effect that convinced millions of people",
        "Schrödinger's Cat and parallel branching universes",
        "Boltzmann Brains floating in an infinite universe",
        "The Holographic Universe principle explained simply",
        "Time dilation near black holes where seconds equal decades",
    ],
    "🤖 Emerging & Rogue Future Tech": [
        "A Future Technology Prediction that feels terrifying",
        "Neural lace brain implants altering human consciousness",
        "Autonomous AI drones developing unexpected emergent tactics",
        "Quantum computing breaking all modern global encryption",
        "Synthetic biology creating resurrecting organism genomes",
        "Dyson Spheres and megastructures harvesting star energy",
        "Cryonics patients waking up into an unrecognizable world",
    ],
    "🕵️ Unsolved Crimes & Cryptic Codes": [
        "A Serial Killer Fact police kept hidden",
        "The cryptic Zodiac Cipher that took decades to crack",
        "The impossible D.B. Cooper airborne hijacking escape",
        "The mysterious disappearance of the Flannan Isle lighthouse keepers",
        "The unsolved Voynich Manuscript written in an alien alphabet",
        "The Somerton Man code found inside a hidden pocket",
    ],
    "🏛️ Ancient Lost Civilizations & Megaliths": [
        "An Ancient Civilization Mystery baffling modern archeologists",
        "The astronomical genius behind the Antikythera Mechanism",
        "The 11,000-year-old stone temple complex of Göbekli Tepe",
        "The lost underground labyrinth city of Derinkuyu",
        "The sonic resonance acoustics engineered inside Mayan pyramids",
        "The unexplained disappearance of the Indus Valley civilization",
    ],
    "🌲 Extreme Nature & Bio-Anomalies": [
        "A biological anomaly that defies the laws of evolution",
        "The immortal jellyfish that reverts its own age indefinitely",
        "Carnivorous fungi that turn insects into parasitic zombies",
        "Perpetual volcanic lightning storms in remote mountain peaks",
        "Blood-red waterfalls pouring over Antarctic glaciers",
        "Hyper-resilient Tardigrades surviving the vacuum of outer space",
    ],
    "👁️ Paranormal & Government Declassifications": [
        "A Paranormal Encounter verified by multiple witnesses",
        "A Conspiracy That Turned Out True after declassification",
        "Project MKUltra's declassified mind control experiments",
        "The Dyatlov Pass Incident where hikers fled their tent in terror",
        "The Skinwalker Ranch anomalous radiation anomalies",
        "The Wow! Signal detected in 1977 that never repeated",
    ],
}

# Flat list for Chaos Mode
NICHES = [niche for sublist in NICHE_CATEGORIES.values() for niche in sublist]

# ── Voice Options (Edge-TTS Neural Voices) ───────────────────
VOICES = {
    "Christopher (Male, US)": "en-US-ChristopherNeural",
    "Guy (Male, US)": "en-US-GuyNeural",
    "Eric (Male, US)": "en-US-EricNeural",
    "Andrew (Male, US)": "en-US-AndrewNeural",
    "Jenny (Female, US)": "en-US-JennyNeural",
    "Aria (Female, US)": "en-US-AriaNeural",
    "Ryan (Male, UK)": "en-GB-RyanNeural",
    "Sonia (Female, UK)": "en-GB-SoniaNeural",
}

# ── Mood Options ─────────────────────────────────────────────
MOODS = [
    "Suspense", "Chill", "Epic", "Dark", "Ethereal", "Dramatic",
    "Melancholy", "Mysterious", "Uplifting", "Cyberpunk", "Intense", "Whimsical",
]

# ── Auth / Rate Limiting ─────────────────────────────────────
DAILY_LIMIT = 3
