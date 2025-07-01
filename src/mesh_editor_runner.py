# mesh_editor_runner.py
import subprocess
import os
import sys

def run_mesh_editor_gui(obj_path):
    script_path = os.path.abspath("mesh_editor.py")  # 위에 작성한 PyQt UI 코드 저장 파일
    result = subprocess.run([sys.executable, script_path, obj_path], check=True)
    
    edited_path = obj_path.replace(".obj", "_edited.ply")
    if os.path.exists(edited_path):
        return edited_path
    else:
        raise FileNotFoundError("편집된 메쉬 파일이 존재하지 않습니다.")
    
