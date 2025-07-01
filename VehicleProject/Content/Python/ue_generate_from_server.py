import unreal
import requests
import os
import tempfile
import uuid
from PIL import Image
from io import BytesIO

API_URL = "http://localhost:8000/generate/"  # FastAPI 주소

def request_glb_from_server(prompt: str, model: str) -> str:
    try:
        response = requests.post(API_URL, data={
            "prompt": prompt,
            "model": model
        })

        if response.status_code == 200:
            temp_dir = tempfile.gettempdir()
            glb_path = os.path.join(temp_dir, "generated_model.glb")
            with open(glb_path, "wb") as f:
                f.write(response.content)
            unreal.log(f"[GLB] Received file at {glb_path}")
            return glb_path
        else:
            unreal.log_error(f"[GLB] Server error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        unreal.log_error(f"[GLB] Request failed: {e}")
        return None

def import_glb(glb_path: str, destination="/Game/AIAssets") -> str:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    # 🔽 고유 이름 생성: glb_filename + short uuid
    base_name = os.path.splitext(os.path.basename(glb_path))[0]
    unique_name = f"{base_name}_{uuid.uuid4().hex[:6]}"

    # 🔽 복사해서 이름 바꿔치기 (Unreal import는 파일명 기준)
    temp_dir = os.path.dirname(glb_path)
    unique_glb_path = os.path.join(temp_dir, f"{unique_name}.glb")
    os.rename(glb_path, unique_glb_path)

    # Unreal import task
    task = unreal.AssetImportTask()
    task.filename = unique_glb_path
    task.destination_name = unique_name  # ✅ 이름 명시
    task.destination_path = destination
    task.automated = True
    task.save = True

    asset_tools.import_asset_tasks([task])

    asset_path = f"{destination}/{unique_name}"
    unreal.log(f"[GLB] Imported asset as: {asset_path}")
    return asset_path

def spawn_actor(asset_path: str, location=unreal.Vector(0, 0, 100)):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, location)
        unreal.log(f"[GLB] Spawned actor: {actor}")
    else:
        unreal.log_error(f"[GLB] Failed to load asset at {asset_path}")

def get_project_content_dir() -> str:
    """Unreal 프로젝트의 Content 디렉토리 경로를 반환."""
    return unreal.SystemLibrary.get_project_content_directory()

def get_save_path(uid: str, img_type: str):
    """
    uid, img_type에 따른 저장 경로 반환
    Returns (disk_path, unreal_import_path)
    """
    subfolder = f"AIAssets/{uid}"
    filename = f"{img_type}_image.png"
    disk_dir = os.path.join(get_project_content_dir(), subfolder)
    os.makedirs(disk_dir, exist_ok=True)

    disk_path = os.path.join(disk_dir, filename)
    unreal_path = f"/Game/{subfolder}/{filename}"
    return disk_path, unreal_path

def download_image_from_server(uid: str, img_type: str) -> str:
    assert img_type in ["gen", "mvs"]
    url = f"http://localhost:8000/image/{uid}/{img_type}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            disk_path, unreal_path = get_save_path(uid, img_type)
            img.save(disk_path)

            # Asset Import
            task = unreal.AssetImportTask()
            task.filename = disk_path
            task.destination_path = os.path.dirname(unreal_path)
            task.destination_name = os.path.splitext(os.path.basename(disk_path))[0]
            task.automated = True
            task.save = True

            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            unreal.log(f"[Image] Imported to {unreal_path}")
            return unreal_path
        else:
            unreal.log_error(f"[Image] Failed: {resp.status_code}")
            return None
    except Exception as e:
        unreal.log_error(f"[Image] Exception: {e}")
        return None
    
