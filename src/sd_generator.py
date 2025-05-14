from abc import *
from diffusers import StableDiffusionXLPipeline,SanaPipeline
import torch
from PIL import Image
from transformers import CLIPTextModel, CLIPTokenizer
from safetensors.torch import load_file


class DiffusionGenerator(metaclass=ABCMeta):
    def __init__(self):
        pass
    
    @abstractmethod
    def generate(self):
        NotImplementedError()

class StableDiffusionGenerator(DiffusionGenerator):
    def __init__(self, model_name='stabilityai/stable-diffusion-xl-base-1.0',device='cuda'):
        self.pipe = StableDiffusionXLPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe = self.pipe.to(device)
        self.pipe.safety_checker = None

    def generate(self,prompt, negative_prompt="",guidance_scale=7.5, num_inference_steps=30):
        result = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=guidance_scale,
                           num_inference_steps=num_inference_steps).images
        return result
    
class CarGenerator(DiffusionGenerator):
    def __init__(self, model_name='stabilityai/stable-diffusion-xl-base-1.0',device='cuda'):
        self.pipe = StableDiffusionXLPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe.load_lora_weights('checkpoint/HT_Monaro-000004.safetensors')
        self.pipe = self.pipe.to(device)
        self.pipe.safety_checker = None

    def generate(self,prompt, negative_prompt="",guidance_scale=7.5, num_inference_steps=30):
        result = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=guidance_scale,
                           num_inference_steps=num_inference_steps).images
        return result
    
class SanaGenerator(DiffusionGenerator):
    def __init__(self,model_name='Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers',device='cuda'):
        self.pipe = SanaPipeline.from_pretrained(model_name,torch_dtype=torch.bfloat16)
        self.pipe.to(device)
        self.pipe.vae.to(torch.bfloat16)
        self.pipe.text_encoder.to(torch.bfloat16)

    def generate(self,prompt, negative_prompt="",guidance_scale=7.5, num_inference_steps=30):
        image = self.pipe(
                prompt=prompt,
                height=1024,
                width=1024,
                guidance_scale=4.5,
                num_inference_steps=20,
                generator=torch.Generator(device="cuda").manual_seed(42),
            )
        return image[0]
