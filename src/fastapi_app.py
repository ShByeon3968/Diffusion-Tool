from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
from sd_generator import SanaGenerator, CarGenerator, DiffusionGenerator
from image_to_3d import MVSGenerator, MeshGenerator
from utils import convert_obj_to_glb
from glob import glob
import traceback

app = FastAPI()

# 모델 선택 매핑
GENERATOR_MAP = {
    "Sana": SanaGenerator,
    "Car": CarGenerator,
    "Stable Diffusion": DiffusionGenerator,
}

@app.post("/generate/")
def generate_3d_model(prompt: str = Form(...), model: str = Form(...)):
    if model not in GENERATOR_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

    uid = str(uuid.uuid4())[:8]
    output_dir = f"./output/fastapi/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 1. 이미지 생성
        generator_class = GENERATOR_MAP[model]
        sd_gen = generator_class()
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
        mesh_gen = MeshGenerator()
        mesh_gen.excute(mv_images, mesh_output_dir)
        obj_path = glob(os.path.join(mesh_output_dir, "*.obj"))[0]

        # 4. .obj → .glb 변환
        glb_path = convert_obj_to_glb(obj_path)

        return FileResponse(glb_path, media_type="model/gltf-binary", filename=f"{prompt}.glb")

    except Exception as e:
        print("❌ Exception occurred:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/image/{uid}/{type}")
def get_generated_image(uid: str, type: str):
    if type not in ["gen", "mvs"]:
        raise HTTPException(status_code=400, detail="Invalid image type")

    filename = "gen_image.png" if type == "gen" else "mvs_image.png"
    image_path = os.path.join("output", "fastapi", uid, filename)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")
