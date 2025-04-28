from diffusers import StableDiffusionPipeline
import torch

class StableDiffusionGenerator:
    def __init__(self, model_name='stabilityai/stable-diffusion-2-1',device='cuda'):
        self.pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe = self.pipe.to(device)
        self.pipe.safety_checker = None

    def generate(self,prompt, negative_prompt="",guidance_scale=7.5, num_inference_steps=30):
        result = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=guidance_scale,
                           num_inference_steps=num_inference_steps).images[0]
        return result