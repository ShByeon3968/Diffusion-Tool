from abc import *
from diffusers import StableDiffusionXLPipeline,SanaPipeline,StableDiffusion3Pipeline, StableDiffusionControlNetImg2ImgPipeline, ControlNetModel, UniPCMultistepScheduler,OmniGenPipeline
import torch
from PIL import Image
from transformers import CLIPTextModel, CLIPTokenizer, pipelines
from safetensors.torch import load_file
import numpy as np

class DiffusionGenerator(metaclass=ABCMeta):
    def __init__(self):
        pass
    
    @abstractmethod
    def generate(self):
        NotImplementedError()

class StableDiffusionGenerator(DiffusionGenerator):
    def __init__(self, model_name='stabilityai/stable-diffusion-3-medium-diffusers',device='cuda'):
        self.pipe = StableDiffusion3Pipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe = self.pipe.to(device)
        self.pipe.safety_checker = None

    def generate(self,prompt, negative_prompt="low quality, worst quality, blurry",guidance_scale=7.0, num_inference_steps=28):
        result = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=guidance_scale,
                           num_inference_steps=num_inference_steps).images
        return result
    
class CarGenerator(DiffusionGenerator):
    def __init__(self, model_name='stabilityai/stable-diffusion-xl-base-1.0',device='cuda'):
        self.pipe = StableDiffusionXLPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
        self.pipe.load_lora_weights('checkpoint/HT_Monaro-000004.safetensors')
        self.pipe = self.pipe.to(device)
        self.pipe.safety_checker = None

    def generate(self,prompt, negative_prompt="low quality, worst quality, blurry",guidance_scale=7.5, num_inference_steps=30):
        result = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=guidance_scale,
                           num_inference_steps=num_inference_steps).images
        return result
    
class SanaGenerator(DiffusionGenerator):
    def __init__(self,model_name='Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers',device='cuda'):
        self.pipe = SanaPipeline.from_pretrained(model_name,torch_dtype=torch.bfloat16)
        self.pipe.to(device)
        self.pipe.vae.to(torch.bfloat16)
        self.pipe.text_encoder.to(torch.bfloat16)

    def generate(self,prompt, negative_prompt="low quality, worst quality, blurry",guidance_scale=7.5, num_inference_steps=30):
        image = self.pipe(
                prompt=prompt,
                height=1024,
                width=1024,
                guidance_scale=4.5,
                num_inference_steps=20,
                negative_prompt= negative_prompt,
                generator=torch.Generator(device="cuda").manual_seed(42),
            )
        return image[0]

class ControlNetBasedGenerator(DiffusionGenerator):
    def __init__(self,depth_model_name ="lllyasviel/control_v11f1p_sd15_depth"
                 ,sd_model="stable-diffusion-v1-5/stable-diffusion-v1-5",device='cuda'):
        super().__init__()
        self.controlnet = ControlNetModel(depth_model_name,torch_dtype=torch.float16,use_safetensors=True)
        self.pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(sd_model,controlnet=self.controlnet, torch_dtype=torch.float16,use_safetensors=True)
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.to(device)
        
    def get_depthmap(self,input_image):
        depth_estimator = pipelines("depth-estimation")
        image = depth_estimator(input_image)["depth"]
        image = np.array(image)
        image = image[:, :, None]
        image = np.concatenate([image, image, image], axis=2)
        detected_map = torch.from_numpy(image).float() / 255.0
        depth_map = detected_map.permute(2, 0, 1)
        return depth_map
    
    def generate(self,prompt,input_image):
        depth_map = self.get_depthmap(input_image)
        output = self.pipe(prompt=prompt,negative_prompt="low quality, worst quality, blurry",image=input_image,control_image=depth_map,
                           num_inference_steps=50).images[0]
        return output
    
class OmniGenImageEditGenerator(DiffusionGenerator):
    def __init__(self,model_name="Shitao/OmniGen-v1-diffusers",device='cuda'):
        super().__init__()
        self.pipe = OmniGenPipeline.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16
        )
        self.generator = torch.Generator(device="cpu").manual_seed(42)
    def generate(self,prompt,input_images):
        image = self.pipe(
            prompt=prompt, 
            input_images=input_images, 
            guidance_scale=2, 
            img_guidance_scale=1.6,
            use_input_image_size_as_output=True,
            generator=self.generator
        ).images[0]
        return image