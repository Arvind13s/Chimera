"""Hugging Face Spaces entrypoint for Chimera (Gradio SDK + ZeroGPU)."""
import os
import gradio as gr
from backend.server import app

# Create a minimal Gradio interface that routes directly to our frontend or mounts FastAPI
with gr.Blocks(title="Chimera AI Video Studio", css="footer {visibility: hidden}") as demo:
    gr.HTML(
        """
        <iframe src="/" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;"></iframe>
        """
    )

# Mount the FastAPI backend onto the Gradio app so all /api/* routes and static files are served seamlessly
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
