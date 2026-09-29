"""Hugging Face Spaces entrypoint for Chimera (Gradio SDK + ZeroGPU)."""
import os
import gradio as gr
import spaces
import uvicorn
from backend.server import app

# ZeroGPU requires at least one @spaces.GPU decorated function connected to Gradio
@spaces.GPU
def gpu_compute():
    return "GPU Ready"

# Create a Gradio interface
with gr.Blocks(title="Chimera AI Video Studio", analytics_enabled=False) as demo:
    hidden_btn = gr.Button(visible=False)
    hidden_out = gr.Textbox(visible=False)
    hidden_btn.click(gpu_compute, outputs=hidden_out)
    
    gr.HTML(
        """
        <iframe src="/" style="position:fixed; top:0; left:0; bottom:0; right:0; width:100%; height:100%; border:none; margin:0; padding:0; overflow:hidden; z-index:999999;"></iframe>
        """
    )

# Mount the Gradio demo onto our FastAPI app at /gradio so ZeroGPU hooks into it
app = gr.mount_gradio_app(app, demo, path="/gradio", ssr_mode=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
