"""Hugging Face Spaces entrypoint — Gradio SDK + ZeroGPU.

How ZeroGPU works:
  1. HF runs `python app.py` (or imports and calls demo.launch).
  2. It scans for @spaces.GPU decorated callables.
  3. demo.launch() must own port 7860.

How we embed our FastAPI backend:
  - gr.mount_gradio_app(fastapi_app, demo, path="/") attaches Gradio at "/"
    of our FastAPI app, returning a combined ASGI app.
  - We then call demo.launch(app=combined_app) so Gradio's server hosts
    both the Gradio UI and all our /api/* + static file routes.
"""
import os
import spaces
import gradio as gr
from backend.server import app as fastapi_app

# ── ZeroGPU: must have at least one @spaces.GPU fn wired into demo ──
@spaces.GPU
def _gpu_ping():
    """Satisfies ZeroGPU startup GPU-function detection."""
    return "ok"

# ── Gradio Blocks — thin shell; real UI served from our FastAPI frontend ──
with gr.Blocks(title="Chimera AI Video Studio") as demo:
    _btn = gr.Button(visible=False)
    _out = gr.Textbox(visible=False)
    _btn.click(_gpu_ping, outputs=_out)
    gr.HTML(
        """<iframe src="/api/health"
                   style="display:none" id="hf-boot"></iframe>
           <script>
             // Redirect the outer Gradio shell to our custom frontend
             if (window.location.pathname === "/" ||
                 window.location.pathname.startsWith("/gradio")) {
               window.location.replace("/frontend/");
             }
           </script>
           <p style="color:#ccc;text-align:center;margin-top:40vh">
             Loading Chimera AI Video Studio…
           </p>"""
    )

# ── Attach Gradio to our FastAPI app; Gradio lives at /gradio ──
# mount_gradio_app returns a new ASGI app that serves FastAPI routes +
# Gradio UI at /gradio; ZeroGPU intercepts the spaces.GPU calls.
combined = gr.mount_gradio_app(fastapi_app, demo, path="/gradio", ssr_mode=False)

# ── Launch — Gradio's server owns port 7860 (required by ZeroGPU) ──
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        app=combined,      # serve the full combined ASGI (FastAPI + Gradio)
        ssr_mode=False,
        show_api=False,
    )
