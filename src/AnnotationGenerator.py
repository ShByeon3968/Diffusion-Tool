from utils import UtillFuctions
import os

output_json_path = "Resource/tank_annotations.json"  # 출력 파일 경로
frame_numbers = [59, 119, 179, 239,299,359,419,479,539,599,659,719,779,839,899,959,1019,1079,1139,1199]   # 프레임 번호 리스트
input_json_path = ['Resource/json/' + str(frame) + ".json" for frame in frame_numbers]
print(input_json_path)
# dirnum 변경필요
UtillFuctions.convert_to_coco(input_json_path, output_json_path, frame_numbers,dir_num=14)
