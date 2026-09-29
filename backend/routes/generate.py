"""FastAPI routes for video generation — SSE streaming endpoint."""

import json
import logging
import threading
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.core.pipeline import generate_video_stream
from backend.core.auth_manager import UserManager

router = APIRouter(prefix="/api/generate", tags=["generate"])
logger = logging.getLogger(__name__)

_user_manager = None


def _get_manager():
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


@router.get("/stream")
async def generate_stream(
    token: str = Query(..., description="Auth token"),
    niche: Optional[str] = Query(None),
    custom_topic: Optional[str] = Query(None),
    voice: str = Query("Christopher (Male, US)"),
):
    """Stream video generation progress via Server-Sent Events."""
    manager = _get_manager()

    # Verify auth
    email = manager.verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token.")

    # Check rate limit
    usage = manager.check_usage(email)
    if not usage["can_generate"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit reached ({usage['limit']} videos/day).",
        )

    def event_stream():
        try:
            for message, video_path, metadata in generate_video_stream(
                niche=niche,
                custom_topic=custom_topic,
                voice=voice,
            ):
                event_data = {
                    "message": message,
                    "video_path": video_path,
                    "metadata": metadata,
                }

                # Determine current stage from message
                stage = 0
                if "Stage 1" in message:
                    stage = 1
                elif "Stage 2" in message:
                    stage = 2
                elif "Stage 3" in message:
                    stage = 3
                elif "Stage 4" in message:
                    stage = 4
                elif "Stage 5" in message:
                    stage = 5
                elif "Stage 6" in message:
                    stage = 6
                elif "complete" in message.lower() or video_path:
                    stage = 7  # Done

                event_data["stage"] = stage

                yield f"data: {json.dumps(event_data)}\n\n"

            # Record usage on successful completion
            manager.record_usage(email)

        except Exception as e:
            logger.error(f"Generation stream error: {e}", exc_info=True)
            error_data = {"message": f"❌ Error: {str(e)}", "stage": -1}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
