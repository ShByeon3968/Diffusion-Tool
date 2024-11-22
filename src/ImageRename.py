from utils import UtillFuctions

frame_numbers = [i for i in range(3,150)]  # 프레임 번호 리스트
# Resource 디렉토리와 dirnum 변경필요
UtillFuctions.rename_files('Resource/New/6',frame_numbers,dir_num=6)