from utils import UtillFuctions

input_json_path = "OutputBound2D359.json"  # 입력 파일 경로
output_json_path = "tank_annotations.json"  # 출력 파일 경로
frame_numbers = [59, 119, 179, 239,299,359]  # 프레임 번호 리스트
UtillFuctions.convert_to_coco(input_json_path, output_json_path, frame_numbers)
