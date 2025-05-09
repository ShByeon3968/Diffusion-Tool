import gradio as gr
import matplotlib.pyplot as plt
from sd_generator import SanaGenerator
from background_remover import BackgroundRemover
from image_to_3d import MVSGenerator, MeshGenerator
from PIL import Image
import os
import uuid
from glob import glob
from utils import convert_obj_to_glb

# 모델 초기화
sd_gen = SanaGenerator()
mesh_gen = MeshGenerator()

# 전체 파이프라인 함수
def generate_pipeline(prompt):
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
    obj_path = glob(os.path.join(mesh_output_dir, "*.obj"))[0]

    # 4. .obj → .glb 변환
    glb_path = convert_obj_to_glb(obj_path)

    return image, mv_images, glb_path, mesh_output_dir

# Gradio 앱 UI
with gr.Blocks(css="body { background-color: black; color: white; }") as demo:
    gr.Markdown("## 🧠 Text → 3D Generator with Texture", elem_id="title")
    gr.Markdown("Prompt → Image → Mesh")

    with gr.Row():
        prompt_input = gr.Textbox(label="Prompt", placeholder="e.g., a fantasy sword, white background")
        submit_btn = gr.Button("Generate")

    with gr.Row():
        gen_img = gr.Image(label="Generated Image")
        mvs_img = gr.Image(label="Multi-View Image")
        mesh_3d = gr.Model3D(label="Rendered 3D Model (.glb)")  # ✅ glb 표시

    mesh_dir = gr.Textbox(label="Mesh Output Path")

    submit_btn.click(
        fn=generate_pipeline,
        inputs=[prompt_input],
        outputs=[gen_img, mvs_img, mesh_3d, mesh_dir]
    )

if __name__ == "__main__":
    demo.launch(allowed_paths=["./output"])
