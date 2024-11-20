import json

class UtillFuctions():
    @staticmethod
    def json_loader(path: str, type:str):
        with open(path, type) as f:
            json_file = json.load(f)
        return json_file
    @staticmethod
    def convert_to_coco(input_file, output_file, frame_numbers, image_height=1280, image_width=720):
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
                    "file_name": f"frame_{image_id}.jpg",
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
