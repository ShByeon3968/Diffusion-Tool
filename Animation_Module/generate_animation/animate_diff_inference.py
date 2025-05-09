import os
import torch
from diffusers import AnimateDiffPipeline, LCMScheduler, MotionAdapter
from diffusers.utils import export_to_gif
import yaml

class AnimateDiffGenerator:
    def __init__(self,config):
        '''
        AnimateDiff 파이프라인으로 텍스트 기반 프레임 시퀀스 생성
        moition_adapter_id: motion adatper 모델 ID
        animate_model_id: 애니메이션 모델 ID
        '''
        self.motion_adapter_id = config['motion_adapter_id']
        self.animate_model_id = config['animate_model_id']
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_frames = config['num_frames']
        self.fps =config['fps']

        self._set_pipeline()

    def _set_pipeline(self):
        # Load the motion adapter
        self.adapter = MotionAdapter.from_pretrained(self.motion_adapter_id, torch_dtype=torch.float16)
        self.pipe = AnimateDiffPipeline.from_pretrained(self.animate_model_id, motion_adapter=self.adapter, torch_dtype=torch.float16)
        self.pipe.scheduler = LCMScheduler.from_config(self.pipe.scheduler.config, beta_schedule="linear")
        self.pipe.load_lora_weights("wangfuyun/AnimateLCM", weight_name="AnimateLCM_sd15_t2v_lora.safetensors", adapter_name="lcm-lora")
        self.pipe.set_adapters(["lcm-lora"], [0.8])


        # enable memory savings
        self.pipe.enable_vae_slicing()
        self.pipe.enable_model_cpu_offload()

    def generate(self, prompt, negative_prompt=None, seed=42):
        output = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=self.num_frames,
            guidance_scale=7.5,
            num_inference_steps=25,
           
            generator=torch.Generator("cpu").manual_seed(seed),
        )
        return output

# config 파일 로드
def load_config(path="config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    config = load_config("./generate_animation/config.yaml")
    pipeline = AnimateDiffGenerator(config)
    prompt = "A knight swinging a glowing sword in a fantasy world, detailed, dynamic motion, game style"
    negative_prompt = "bad quality, blurry, worse quality"
    output = pipeline.generate(prompt, negative_prompt=negative_prompt, seed=42)

    frames = output.frames[0]
    export_to_gif(frames, "output.gif", fps=pipeline.fps)