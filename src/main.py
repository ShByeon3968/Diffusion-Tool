import gradio as gr
import matplotlib.pyplot as plt
from sd_generator import SanaGenerator
from background_remover import BackgroundRemover
from image_to_3d import MVSGenerator, MeshGenerator
from PIL import Image
import os
import uuid

# 모델 초기화
sd_gen = SanaGenerator()
mesh_gen = MeshGenerator()

def generate_pipeline(prompt):
    # Unique ID for session
    uid = str(uuid.uuid4())[:8]
    output_dir = f"./output/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    # 1. 이미지 생성
    image = sd_gen.generate(prompt)[0]
    image_path = os.path.join(output_dir, "gen_image.png")
    image.save(image_path)

    # 2. MVS 이미지 생성
    mvs_gen = MVSGenerator(input_image_path=image_path)
    mv_images, _ = mvs_gen.excute()
    mv_image_path = os.path.join(output_dir, "mvs_image.png")
    mv_images.save(mv_image_path)

    # 3. 메쉬 생성
    mesh_output_dir = os.path.join(output_dir, "mesh/")
    os.makedirs(mesh_output_dir, exist_ok=True)
    mesh_gen.excute(mv_images, mesh_output_dir)

    return image, mv_images, f"{mesh_output_dir} (Check .obj/.mtl files manually)"

# Gradio UI
with gr.Blocks(title="Text-to-3D Generator") as demo:
    gr.Markdown("## 🎮 Text → 3D Object Generator")
    gr.Markdown("Enter a prompt and get a 3D mesh using Stable Diffusion + MVS + Mesh Reconstruction")

    with gr.Row():
        prompt_input = gr.Textbox(label="Prompt", placeholder="e.g., a fantasy sword, white background")
        submit_btn = gr.Button("Generate")

    with gr.Row():
        gen_img = gr.Image(label="Generated Image")
        mvs_img = gr.Image(label="Multi-View Stereo Image")
        mesh_dir = gr.Textbox(label="Mesh Output Directory")

    submit_btn.click(
        fn=generate_pipeline,
        inputs=[prompt_input],
        outputs=[gen_img, mvs_img, mesh_dir]
    )

if __name__ == "__main__":
    demo.launch()


# "a futuristic robot dog,black, isometric, white background"