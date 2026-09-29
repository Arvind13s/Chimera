"""Hugging Face Spaces entrypoint — Gradio SDK + ZeroGPU.

ZeroGPU detection works by scanning for @spaces.GPU decorators at import time.
Once detected it sends a startup-report to device-api.zero (confirmed 200 OK).
We then run the combined FastAPI+Gradio app via uvicorn on port 7860.
"""
import os
import spaces
import gradio as gr
from backend.server import app as fastapi_app

# ── ZeroGPU: must have @spaces.GPU in this module at import time ──
@spaces.GPU
def _gpu_ping():
    """Required by ZeroGPU supervisor — detected at module import."""
    return "ok"

# ── Gradio Blocks shell (ZeroGPU needs a gr.Blocks connected to @spaces.GPU) ──
with gr.Blocks(title="Chimera AI Video Studio") as demo:
    _btn = gr.Button(visible=False)
    _out = gr.Textbox(visible=False)
    _btn.click(_gpu_ping, outputs=_out)
    gr.HTML("<p style='color:#888;text-align:center;margin-top:40vh'>Loading Chimera…</p>")

# ── Mount Gradio into our FastAPI app at /gradio ──
# Combined ASGI: FastAPI handles /api/* and static files; Gradio at /gradio
combined = gr.mount_gradio_app(fastapi_app, demo, path="/gradio", ssr_mode=False)

# ── Start server — uvicorn owns port 7860 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(combined, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
