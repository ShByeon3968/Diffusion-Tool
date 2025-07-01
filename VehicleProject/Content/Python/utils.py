import zipfile
import tempfile
import os
import requests

def fetch_and_extract_assets(prompt, model):
    response = requests.post("http://localhost:8000/generate/", data={"prompt": prompt, "model": model})
    if response.status_code == 200:
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "result_bundle.zip")
        with open(zip_path, "wb") as f:
            f.write(response.content)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(temp_dir)

        single = os.path.join(temp_dir, "gen_image.png")
        multi = os.path.join(temp_dir, "mvs_image.png")
        return single, multi  # Blueprint에서 사용할 경로
    else:
        return None, None
    
# 경로를 텍스트 파일로 저장해서 Blueprint가 읽도록
def save_image_paths_for_bp(single_path, multi_path):
    shared_path = "C:/Temp/unreal_image_paths.txt"
    with open(shared_path, "w") as f:
        f.write(single_path + "\n")
        f.write(multi_path + "\n")
    return shared_path
