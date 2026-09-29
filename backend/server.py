"""Chimera v3.0 — FastAPI backend server.

Serves the static frontend (plain HTML/CSS/JS + Three.js, no build step)
and exposes REST + SSE APIs.
"""

import glob
import logging
import os
import sys

# Ensure project root is in sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.config import TEMP_DIR, OUTPUT_DIR, PROJECT_ROOT
from backend.routes.auth import router as auth_router
from backend.routes.generate import router as generate_router
from backend.routes.config_routes import router as config_router

# Hugging Face ZeroGPU compatibility: ZeroGPU checks for @spaces.GPU during startup
try:
    import spaces
    @spaces.GPU
    def _zerogpu_init():
        """Dummy GPU function to satisfy Hugging Face ZeroGPU runner."""
        return True
except Exception:
    pass

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Cleanup stale temp files from crashed runs ──────────────
def _cleanup_stale_temp():
    """Remove stale temp files on startup."""
    try:
        patterns = ["voice_*.mp3", "clip_*.mp4", "synth_*.wav", "jamendo_*.mp3", "freesound_*.mp3"]
        removed = 0
        for pattern in patterns:
            for f in glob.glob(os.path.join(TEMP_DIR, pattern)):
                try:
                    os.remove(f)
                    removed += 1
                except OSError:
                    pass
        if removed:
            logger.info(f"Cleaned up {removed} stale temp files from previous runs.")
    except Exception as e:
        logger.debug(f"Temp cleanup error: {e}")


_cleanup_stale_temp()

# ── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="Chimera AI Video Generator",
    description="Autonomous multi-agent AI video creation studio",
    version="3.0.0",
)

# CORS — kept permissive for local dev tools that hit the API directly
# (e.g. curl, Postman) since the frontend is now served from this same
# origin and no longer needs a cross-origin allowance for a dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(auth_router)
app.include_router(generate_router)
app.include_router(config_router)

# Serve output videos as static files
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

# Serve the static frontend — plain HTML/CSS/JS, no build step.
# StaticFiles(html=True) serves index.html for "/" and for any other
# path that doesn't match a real file, so no manual catch-all route is
# needed. This MUST be mounted last: Starlette checks routes in the
# order they were added, and a mount at "/" matches every path, so
# anything registered after it (like /api/health above) would
# otherwise become unreachable.
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ── Entrypoint ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 7860))
    logger.info(f"Starting Chimera server on port {port}...")
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
