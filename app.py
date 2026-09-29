"""Hugging Face Spaces entrypoint for Chimera (Gradio SDK + ZeroGPU)."""
import os
import gradio as gr
import spaces
from backend.server import app

# ZeroGPU requires at least one @spaces.GPU decorated function connected to Gradio
@spaces.GPU
def gpu_compute():
    return "GPU Ready"

# Create Gradio interface
with gr.Blocks(title="Chimera AI Video Studio") as demo:
    btn = gr.Button(visible=False)
    out = gr.Textbox(visible=False)
    btn.click(gpu_compute, outputs=out)

    gr.HTML(
        """
        <iframe src="/app" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;"></iframe>
        """
    )

# Mount our custom FastAPI app inside Gradio so all APIs and frontend exist
demo.mount(app, path="/app")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, ssr_mode=False)
