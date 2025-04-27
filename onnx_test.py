import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
import torch.onnx
import numpy

# Real-ESRGAN RRDBNet 모델 구조 정의 (4배 업스케일 예시)
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
ckpt = torch.load('RealESRGAN_x4plus.pth', map_location='cpu')
model.load_state_dict(ckpt['params_ema'], strict=True)
model.eval()

# 임의 입력(batch=1, 3채널, 2K(2048), 2K)
dummy_input = torch.randn(1, 3, 2048, 2048)

# ONNX 모델로 변환
torch.onnx.export(
    model, 
    dummy_input, 
    "realesrgan_x4plus.onnx", 
    input_names=['input'], 
    output_names=['output'], 
    opset_version=17,
    dynamic_axes={'input': {0: 'batch', 2: 'height', 3: 'width'},
                  'output': {0: 'batch', 2: 'height', 3: 'width'}}
)
print("ONNX 모델로 저장 완료!")