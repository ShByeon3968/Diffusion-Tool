import json

def json_loader(path: str, type:str):
    with open(path, type) as f:
        json_file = json.load(f)
    return json_file