"""FastAPI routes for config data — niches, voices, categories."""

from fastapi import APIRouter

from backend.core.config import NICHE_CATEGORIES, VOICES, MOODS

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/categories")
async def get_categories():
    """Return all niche categories with their topics."""
    return {
        "categories": {
            name: topics for name, topics in NICHE_CATEGORIES.items()
        }
    }


@router.get("/voices")
async def get_voices():
    """Return available voice options."""
    return {"voices": list(VOICES.keys())}


@router.get("/moods")
async def get_moods():
    """Return available mood options."""
    return {"moods": MOODS}
