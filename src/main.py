import gradio as gr
import matplotlib.pyplot as plt
from sd_generator import SanaGenerator
from background_remover import BackgroundRemover
from image_to_3d import MVSGenerator, MeshGenerator
from PIL import Image
import os
import uuid
import trimesh
import io
from glob import glob
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# 모델 초기화
sd_gen = SanaGenerator()

mesh_gen = MeshGenerator()
def render_mesh_as_image_matplotlib(mesh_path):
    mesh = trimesh.load(mesh_path)

    fig = plt.figure(figsize=(6, 6), facecolor='black')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor("black")

    vertices = mesh.vertices
    faces = mesh.faces
    mesh_poly = Poly3DCollection(vertices[faces], alpha=1.0)
    mesh_poly.set_facecolor((0.7, 0.7, 0.9, 1))
    ax.add_collection3d(mesh_poly)

    scale = vertices.flatten()
    ax.auto_scale_xyz(scale, scale, scale)
    ax.axis('off')

    # 👉 Gradio에서 허용하는 위치에 임시 이미지 저장
    temp_output_path = "./output/temp_render.png"
    plt.savefig(temp_output_path, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

    return Image.open(temp_output_path)


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

    # 4. .obj 시각화
    obj_path = glob(os.path.join(mesh_output_dir, "*.obj"))[0]
    mesh_img = render_mesh_as_image_matplotlib(obj_path)

    return image, mv_images, mesh_img, mesh_output_dir

# Gradio 앱 UI
with gr.Blocks(css="body { background-color: black; color: white; }") as demo:
    gr.Markdown("## 🎮 Text → 3D Object Generator", elem_id="title")
    gr.Markdown("Enter a prompt and get a 3D mesh using Stable Diffusion + MVS + Mesh Reconstruction")

    with gr.Row():
        prompt_input = gr.Textbox(label="Prompt", placeholder="e.g., a fantasy sword, white background")
        submit_btn = gr.Button("Generate")

    with gr.Row():
        gen_img = gr.Image(label="Generated Image")
        mvs_img = gr.Image(label="Multi-View Image")
        mesh_img = gr.Image(label="3D Mesh Rendered View")

    mesh_dir = gr.Textbox(label="Mesh Folder Path")

    submit_btn.click(
        fn=generate_pipeline,
        inputs=[prompt_input],
        outputs=[gen_img, mvs_img, mesh_img, mesh_dir]
    )

if __name__ == "__main__":
    demo.launch()
