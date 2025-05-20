import unreal
import requests
import os
import tempfile

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
    task = unreal.AssetImportTask()
    task.filename = glb_path
    task.destination_path = destination
    task.automated = True
    task.save = True

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    asset_name = os.path.splitext(os.path.basename(glb_path))[0]
    asset_path = f"{destination}/{asset_name}"
    unreal.log(f"[GLB] Imported asset at {asset_path}")
    return asset_path

def spawn_actor(asset_path: str, location=unreal.Vector(0, 0, 100)):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, location)
        unreal.log(f"[GLB] Spawned actor: {actor}")
    else:
        unreal.log_error(f"[GLB] Failed to load asset at {asset_path}")
