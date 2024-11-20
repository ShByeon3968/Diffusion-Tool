import json
import numpy as np
import cv2
import os

class UtillFuctions():
    @staticmethod
    def json_loader(path: str, type:str):
        # json file 오픈
        with open(path, type) as f:
            json_file = json.load(f)
        return json_file
    
    @staticmethod
    def rename_files(directory_path,frame_numbers:list,new_name_prefix = "frame",dir_num=0):
    # 디렉토리 내 파일 목록 가져오기
        files = os.listdir(directory_path)
        files.sort()  # 파일을 정렬하여 순서대로 이름 변경

        for index, filename in enumerate(files):
            old_file_path = os.path.join(directory_path, filename)
            
            # 파일이 실제 파일인지 확인 (폴더 무시)
            if os.path.isfile(old_file_path) :
                # 원하는 프레임일 경우만 수행
                if index in frame_numbers:
                    file_extension = os.path.splitext(filename)[1]  # 파일 확장자 추출
                    new_file_name = f"{dir_num}_{new_name_prefix}_{index}{file_extension}"
                    new_file_path = os.path.join(directory_path, new_file_name)
                    
                    # 파일 이름 변경
                    os.rename(old_file_path, new_file_path)
                    print(f"Renamed: {filename} -> {new_file_name}")
                else:
                    os.remove(old_file_path)
            

    @staticmethod
    def convert_to_coco(input_file, output_file, frame_numbers, image_height=1280, image_width=720, dir_num=0):
        # JSON 파일 로드
        with open(input_file, 'r') as f:
            data = json.load(f)

        vectors = data['Vectors']
        num_boxes_per_frame = len(vectors) // len(frame_numbers)  # 프레임 수에 따라 바운딩 박스 계산
        annotations = []
        annotation_id = 1

        for frame_index, image_id in enumerate(frame_numbers):  # 프레임 넘버를 사용하여 순환
            for i in range(frame_index * num_boxes_per_frame, (frame_index + 1) * num_boxes_per_frame, 2):
                x_min = min(vectors[i]['X'], vectors[i + 1]['X'])
                y_min = min(vectors[i]['Y'], vectors[i + 1]['Y'])
                x_max = max(vectors[i]['X'], vectors[i + 1]['X'])
                y_max = max(vectors[i]['Y'], vectors[i + 1]['Y'])

                width = x_max - x_min
                height = y_max - y_min
                area = width * height

                annotation = {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 1,  # 카테고리 ID 
                    "bbox": [x_min, y_min, width, height],
                    "area": area,
                    "iscrowd": 0
                }
                annotations.append(annotation)
                annotation_id += 1

        # COCO 형식의 JSON 생성
        coco_format = {
            "info": {
                "description": "Example COCO dataset",
                "version": "1.0",
                "year": 2024,
                "contributor": "Generated",
                "date_created": "2024-11-20"
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Tank Dataset",
                    "url": "http://example.com"
                }
            ],
            "images": [
                {
                    "id": image_id,
                    "file_name": f"{dir_num}_frame_{image_id}.jpg",
                    "height": image_height,
                    "width": image_width
                }
                for image_id in frame_numbers  # 프레임 넘버 기반
            ],
            "annotations": annotations,
            "categories": [
                {
                    "id": 1,
                    "name": "Tank T55A",
                    "supercategory": "none"
                }
            ]
        }

        # JSON 파일로 저장
        with open(output_file, 'w') as json_file:
            json.dump(coco_format, json_file, indent=4)

        print(f"COCO annotation JSON 파일 '{output_file}'이 생성되었습니다.")

    @staticmethod
    def merge_json_files(directory_path, output_file):
        merged_data = []

        # 디렉토리 내 모든 JSON 파일 목록 가져오기
        json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]

        for json_file in json_files:
            file_path = os.path.join(directory_path, json_file)

            # JSON 파일 로드 및 데이터 병합
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged_data.extend(data)  # 리스트 데이터면 병합
                else:
                    merged_data.append(data)  # 단일 객체면 추가

        # 합쳐진 데이터를 출력 파일로 저장
        with open(output_file, 'w') as output_f:
            json.dump(merged_data, output_f, indent=4)

        print(f"모든 JSON 파일이 '{output_file}'로 병합되었습니다.")