import gradio as gr
from sd_generator import SanaGenerator, DiffusionGenerator, CarGenerator
from image_to_3d import MVSGenerator, MeshGenerator
from PIL import Image
import os
import uuid
from glob import glob
from custom_utils import convert_obj_to_glb

# 모델 선택 매핑
GENERATOR_MAP = {
    "Sana (Default SDXL)": SanaGenerator,
    "Car": CarGenerator,
    "Stable Diffusion": DiffusionGenerator,
}

# 모델 초기화
sd_gen = SanaGenerator()
mesh_gen = MeshGenerator()

# 전체 파이프라인 함수
def generate_pipeline(prompt, generator_name="Sana (Default SDXL)"):
    uid = str(uuid.uuid4())[:8]
    output_dir = f"./output/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    # 선택한 클래스 인스턴스화
    generator_class = GENERATOR_MAP[generator_name]
    sd_gen = generator_class()

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
    gr.Markdown("## 🧠 Text → 3D Generator with Texture")
    gr.Markdown("Prompt → Image → Mesh")

    with gr.Row():
        prompt_input = gr.Textbox(label="Prompt", placeholder="e.g., a fantasy sword, white background")
        model_selector = gr.Dropdown(
            choices=["Sana (Default SDXL)", "Car", "Stable Diffusion"],
            value="Sana (Default SDXL)",
            label="Generator Style"
        )
        submit_btn = gr.Button("Generate")

    with gr.Row():
        gen_img = gr.Image(label="Generated Image")
        mvs_img = gr.Image(label="Multi-View Image")
        mesh_3d = gr.Model3D(label="Rendered 3D Model (.glb)")

    mesh_dir = gr.Textbox(label="Mesh Output Path")

    submit_btn.click(
        fn=generate_pipeline,
        inputs=[prompt_input, model_selector],  # ✅ 두 개의 입력
        outputs=[gen_img, mvs_img, mesh_3d, mesh_dir]
    )

if __name__ == "__main__":
    demo.launch(allowed_paths=["./output"])
