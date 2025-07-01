import torch
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
from huggingface_hub import hf_hub_download
from torch.ao.quantization import quantize_dynamic
import torch

def quantize_unet_model():
    # ① 파이프라인 로딩 (float16, GPU X)
    pipeline = DiffusionPipeline.from_pretrained("sudo-ai/zero123plus-v1.2", custom_pipeline="src/InstantMesh/zero123plus",torch_dtype=torch.float16)
    pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(pipeline.scheduler.config, timestep_spacing='trailing')
    unet_ckpt_path = hf_hub_download(repo_id="TencentARC/InstantMesh",filename="diffusion_pytorch_model.bin",repo_type="model")
    state_dict = torch.load(unet_ckpt_path, map_location="cpu")
    pipeline.unet.load_state_dict(state_dict, strict=True)

    # ② UNet 모델 추출
    unet = pipeline.unet.eval().cpu()
    return unet

unet = quantize_unet_model()

# 입력값 구성 (UNet forward signature에 맞춰야 함)
latent = torch.randn(1, 4, 64, 64).half()  # float16
timestep = torch.tensor([0], dtype=torch.long)  # timestep은 int64로 유지
encoder_hidden_states = torch.randn(1, 77, 1024).half()

# ONNX export
torch.onnx.export(
    unet,
    (latent, timestep, encoder_hidden_states),
    "unet_zero123plus.onnx",
    input_names=["latent", "timestep", "encoder_hidden_states"],
    output_names=["pred"],
    opset_version=17,
    do_constant_folding=True,
    dynamic_axes={
        "latent": {0: "batch", 2: "height", 3: "width"},
        "encoder_hidden_states": {0: "batch", 1: "sequence"}
    }
)
print("UNet successfully exported to ONNX")