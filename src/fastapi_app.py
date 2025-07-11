from fastapi import FastAPI, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import uuid, os, torch, gc, traceback
from glob import glob
from PIL import Image

from mesh_editor import run_mesh_editor
from prompt_planner import plan_and_rewrite_prompts
from feedback_rewriter import rewrite_prompt_for_omnigen_editing
from sd_generator import SanaGenerator, CarGenerator, StableDiffusionGenerator, ControlNetBasedGenerator, OmniGenImageEditGenerator
from image_to_3d import MVSGenerator, MeshGenerator
from custom_utils import convert_obj_to_glb


app = FastAPI()

# ─────────────────────────────────────────
# 모델 맵핑
# ─────────────────────────────────────────
GENERATOR_MAP = {
    "Sana": SanaGenerator,
    "Car": CarGenerator,
    "Stable Diffusion": StableDiffusionGenerator,
}

STATUS_MAP = {}
GLOBAL_UID = 0
PRE_PROMPT = ""

# ─────────────────────────────────────────
# 백그라운드 메쉬 생성 함수
# ─────────────────────────────────────────
def generate_mesh(prompt: str, model: str, output_dir: str, uid: str):
    global PRE_PROMPT
    try:
        STATUS_MAP[uid] = "pending"

        with torch.no_grad():
            # 1. 이미지 생성
            generator = GENERATOR_MAP[model]()
            prompt = plan_and_rewrite_prompts(prompt)
            PRE_PROMPT = prompt
            gen_image = generator.generate(prompt)[0]
            image_path = os.path.join(output_dir, "gen_image.png")
            gen_image.save(image_path)
            generator.pipe.to("cpu")
            del generator
            torch.cuda.empty_cache()
            gc.collect()

            # 2. MVS 이미지 생성
            mvs = MVSGenerator(input_image_path=image_path)
            mv_images, _ = mvs.excute()
            mv_image_path = os.path.join(output_dir, "mvs_image.png")
            mv_images.save(mv_image_path)
            mvs.pipeline.to("cpu")
            del mvs
            torch.cuda.empty_cache()
            gc.collect()

            # 3. 메쉬 생성
            mesh_dir = os.path.join(output_dir, "mesh")
            os.makedirs(mesh_dir, exist_ok=True)
            mesh_generator = MeshGenerator()
            mesh_generator.excute(mv_images, mesh_dir,uid)
            obj_path = glob(os.path.join(mesh_dir, "*.obj"))[0]
            mesh_generator.model.to("cpu")
            del mesh_generator
            torch.cuda.empty_cache()
            gc.collect()

            # 4. GLB 변환
            glb_path = convert_obj_to_glb(obj_path)
            os.rename(glb_path, os.path.join(output_dir, "mesh.glb"))

            STATUS_MAP[uid] = "done"
    except Exception:
        STATUS_MAP[uid] = "error"
        traceback.print_exc()
    finally:
        torch.cuda.empty_cache()
        gc.collect()

def generate_mesh_edit(prompt: str,image_path:str,output_dir: str,uid):
    global PRE_PROMPT
    try:
        with torch.no_grad():
            # 1. 이미지 Editing - improved prompt 기반
            edit_net = OmniGenImageEditGenerator()
            input_image = Image.open(image_path)
            out_image_path = os.path.join(output_dir, "gen_image.png")
            output = edit_net.generate(prompt,input_image)
            output.save(out_image_path)
            del edit_net
            torch.cuda.empty_cache()
            gc.collect()

            # 2. MVS 이미지 생성
            mvs = MVSGenerator(input_image_path=out_image_path)
            mv_images, _ = mvs.excute()
            mv_image_path = os.path.join(output_dir, "mvs_image.png")
            mv_images.save(mv_image_path)
            mvs.pipeline.to("cpu")
            del mvs
            torch.cuda.empty_cache()
            gc.collect()

            # 3. 메쉬 생성
            mesh_dir = os.path.join(output_dir, "mesh")
            os.makedirs(mesh_dir, exist_ok=True)
            mesh_generator = MeshGenerator()
            mesh_generator.excute(mv_images, mesh_dir,uid)
            obj_path = glob(os.path.join(mesh_dir, "*.obj"))[0]
            mesh_generator.model.to("cpu")
            del mesh_generator
            torch.cuda.empty_cache()
            gc.collect()

            # 4. GLB 변환
            glb_path = convert_obj_to_glb(obj_path)
            os.rename(glb_path, os.path.join(output_dir, "mesh.glb"))
    except Exception:
        traceback.print_exc()
    finally:
        torch.cuda.empty_cache()
        gc.collect()

# ─────────────────────────────────────────
# 생성 요청 → UID 반환
# ─────────────────────────────────────────
@app.post("/generate/")
def generate_3d_model(prompt: str = Form(...), model: str = Form(...), background_tasks: BackgroundTasks = None):
    global GLOBAL_UID
    if model not in GENERATOR_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")

    uid = str(uuid.uuid4())[:8]
    GLOBAL_UID = uid
    output_dir = os.path.join("output", "fastapi", uid)
    os.makedirs(output_dir, exist_ok=True)

    STATUS_MAP[uid] = "pending"
    background_tasks.add_task(generate_mesh, prompt, model, output_dir, uid)

    return JSONResponse(status_code=200, content={"uid": uid})

# ─────────────────────────────────────────
# GLB 반환
# ─────────────────────────────────────────
@app.get("/glb/{uid}")
def get_glb(uid: str):
    glb_path = os.path.join("output", "fastapi", uid, "mesh.glb")
    if not os.path.exists(glb_path):
        raise HTTPException(status_code=404, detail="GLB file not found")
    return FileResponse(glb_path, media_type="model/gltf-binary", filename=f"{uid}.glb")

# ─────────────────────────────────────────
# 이미지 반환 (gen or mvs)
# ─────────────────────────────────────────
@app.get("/image/{uid}/{type}")
def get_generated_image_file(uid: str, type: str):
    if type not in ["gen", "mvs"]:
        raise HTTPException(status_code=400, detail="Invalid image type")

    filename = "gen_image.png" if type == "gen" else "mvs_image.png"
    image_path = os.path.join("output", "fastapi", uid, filename)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename=filename  # 다운로드 시 파일 이름 지정
    )

@app.get("/run_mesh_editor")
def run_mesh_editor_gui(uid: str):
    glb_dir = os.path.join("output", "fastapi", uid, "mesh")
    glb_path = glob(os.path.join(glb_dir, "*.glb"))
    if not os.path.exists(glb_path):
        raise HTTPException(status_code=404, detail="GLB file not found")
    
    # Assuming the mesh editor is a local application that can be opened with the GLB file
    run_mesh_editor(glb_path[0], auto_run=True)

# ─────────────────────────────────────────
# 재생성 파이프라인
# ─────────────────────────────────────────

@app.post("/feedback_rewrite")
def rewrite_prompt_and_regenerate(
    feedback: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    global GLOBAL_UID
    if feedback is None:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model}")
    
    prompt = PRE_PROMPT
    rewritten_prompt = rewrite_prompt_for_omnigen_editing(prompt, feedback)
    PRE_PROMPT = rewritten_prompt
    input_image_path = os.path.join("output", "fastapi", GLOBAL_UID, "gen_image.png")

    # uid 재설정
    uid = str(uuid.uuid4())[:8]
    GLOBAL_UID = uid
    output_dir = os.path.join("output", "fastapi", uid)
    os.makedirs(output_dir, exist_ok=True)

    # 재생성 파이프라인 실행
    background_tasks.add_task(generate_mesh_edit, rewritten_prompt, input_image_path, output_dir, uid)
    return JSONResponse(status_code=200, content={"uid": uid})
