import onnxruntime as ort
import numpy as np

# 1. ONNX 세션 로딩
session = ort.InferenceSession("unet_zero123plus.onnx", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])

# 2. 입력 이름 확인 (debug 용도)
print("Model Input Names:", [i.name for i in session.get_inputs()])
print("Model Output Names:", [o.name for o in session.get_outputs()])
