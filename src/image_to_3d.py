import torch
import os
from omegaconf import OmegaConf
import tempfile
from tqdm import tqdm
import imageio
model = None
torch.cuda.empty_cache()
import numpy as np
import rembg
from PIL import Image
from pytorch_lightning import seed_everything
from einops import rearrange
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
from torchvision.transforms import v2
from huggingface_hub import hf_hub_download
from utils import *
import uuid

class MVSGenerator:
    '''
    Multi-View Stereopsis (MVS) 생성기
    - DiffusionPipeline: sudo-ai/zero123plus-v1.2
    '''
    def __init__(self,input_image_path:str):
        self.set_pipeline()
        self.image = Image.open(input_image_path)

    def set_pipeline(self):
        self.pipeline = DiffusionPipeline.from_pretrained("sudo-ai/zero123plus-v1.2", custom_pipeline="src/InstantMesh/zero123plus",torch_dtype=torch.float16)
        self.pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipeline.scheduler.config, timestep_spacing='trailing')
        unet_ckpt_path = hf_hub_download(repo_id="TencentARC/InstantMesh",filename="diffusion_pytorch_model.bin",repo_type="model")
        state_dict = torch.load(unet_ckpt_path, map_location="cpu")
        self.pipeline.unet.load_state_dict(state_dict, strict=True)
        self.device = torch.device("cuda")
        self.pipeline = self.pipeline.to(self.device)
        seed_everything(0)

    def preprocess(self,input_image, do_remove_background):
        rembg_session = rembg.new_session() if do_remove_background else None
        if do_remove_background:
            input_image = remove_background(input_image, rembg_session)
            input_image = resize_foreground(input_image, 0.85)
        return input_image

    def generate_mvs(self,input_image,sample_steps, sample_seed):
        seed_everything(sample_seed)
        generator = torch.Generator(device=self.device)
        z123_image = self.pipeline(
            input_image, 
            num_inference_steps=sample_steps, 
            generator=generator,
        ).images[0]
        show_image = np.asarray(z123_image, dtype=np.uint8)
        show_image = torch.from_numpy(show_image)     # (960, 640, 3)
        show_image = rearrange(show_image, '(n h) (m w) c -> (n m) h w c', n=3, m=2)
        show_image = rearrange(show_image, '(n m) h w c -> (n h) (m w) c', n=2, m=3)
        show_image = Image.fromarray(show_image.numpy())
        return z123_image, show_image
    
    def excute(self):
        '''
        preprocess -> generate_mvs 실행
        '''
        # 1. 배경 제거 및 리사이즈
        processed_image = self.preprocess(self.image, do_remove_background=True)
        # 2. MVS 생성
        mv_images, mv_show_image = self.generate_mvs(
            processed_image, 
            sample_steps=75, 
            sample_seed=42
        )
        return mv_images, mv_show_image
    
class MeshGenerator:
    def __init__(self, config_path:str='configs/instant-mesh-base.yaml'):
        self.model = self.set_model(config_path)
        self.device = torch.device('cuda')

    def set_model(self,config_path):
        config = OmegaConf.load(config_path)
        config = OmegaConf.load(config_path)
        config_name = os.path.basename(config_path).replace('.yaml', '')
        model_config = config.model_config
        self.infer_config = config.infer_config
        model_ckpt_path = hf_hub_download(repo_id="TencentARC/InstantMesh", filename="instant_mesh_base.ckpt", repo_type="model")
        model = instantiate_from_config(model_config)
        state_dict = torch.load(model_ckpt_path, map_location='cpu')['state_dict']
        state_dict = {k[14:]: v for k, v in state_dict.items() if k.startswith('lrm_generator.') and 'source_camera' not in k}
        model.load_state_dict(state_dict, strict=True)
        device = torch.device('cuda')
        model = model.to(device)
        self.IS_FLEXICUBES = True if config_name.startswith('instant-mesh') else False
        if self.IS_FLEXICUBES:
            model.init_flexicubes_geometry(device, fovy=30.0)
        model = model.eval()
        return model
    
    def images_to_video(self, images, output_path, fps=30):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        frames = []
        for i in range(images.shape[0]):
            frame = (images[i].permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8).clip(0, 255)
            assert frame.shape[0] == images.shape[2] and frame.shape[1] == images.shape[3], \
                f"Frame shape mismatch: {frame.shape} vs {images.shape}"
            assert frame.min() >= 0 and frame.max() <= 255, \
                f"Frame value out of range: {frame.min()} ~ {frame.max()}"
            frames.append(frame)
        imageio.mimwrite(output_path, np.stack(frames))

    def get_render_cameras(self,batch_size=1, M=120, radius=2.5, elevation=10.0, is_flexicubes=False):
        c2ws = get_circular_camera_poses(M=M, radius=radius, elevation=elevation)
        if is_flexicubes:
            cameras = torch.linalg.inv(c2ws)
            cameras = cameras.unsqueeze(0).repeat(batch_size, 1, 1, 1)
        else:
            extrinsics = c2ws.flatten(-2)
            intrinsics = FOV_to_intrinsics(30.0).unsqueeze(0).repeat(M, 1, 1).float().flatten(-2)
            cameras = torch.cat([extrinsics, intrinsics], dim=-1)
            cameras = cameras.unsqueeze(0).repeat(batch_size, 1, 1)
        return cameras

    def make_mesh(self,mesh_fpath, planes):
        mesh_basename = os.path.basename(mesh_fpath).split('.')[0]
        mesh_dirname = os.path.dirname(mesh_fpath)
        mesh_vis_fpath = os.path.join(mesh_dirname, f"{mesh_basename}.glb")
        with torch.no_grad():
            mesh_out = self.model.extract_mesh(planes, use_texture_map=True, **self.infer_config,)
            vertices, faces, uvs, mesh_tex_idx, tex_map = mesh_out
            # vertices = vertices[:, [1, 2, 0]]
            # vertices[:, -1] *= -1
            # faces = faces[:, [2, 1, 0]]
            save_obj_with_mtl(
                vertices.data.cpu().numpy(),
                uvs.data.cpu().numpy(),
                faces.data.cpu().numpy(),
                mesh_tex_idx.data.cpu().numpy(),
                tex_map.permute(1, 2, 0).data.cpu().numpy(),
                mesh_fpath,
            )
            print(f"Mesh with texmap saved to {mesh_fpath}")
            # vertices, faces, vertex_colors = mesh_out
            # vertices = vertices[:, [1, 2, 0]]
            # vertices[:, -1] *= -1
            # faces = faces[:, [2, 1, 0]]
            # save_obj(vertices, faces, vertex_colors, mesh_fpath)
            # print(f"Mesh saved to {mesh_fpath}")
        return mesh_fpath

    def make3d(self,images,out_dir):
        images = np.asarray(images, dtype=np.float32) / 255.0
        images = torch.from_numpy(images).permute(2, 0, 1).contiguous().float()     # (3, 960, 640)
        images = rearrange(images, 'c (n h) (m w) -> (n m) c h w', n=3, m=2)        # (6, 3, 320, 320)
        input_cameras = get_zero123plus_input_cameras(batch_size=1, radius=4.0).to(self.device)
        render_cameras = self.get_render_cameras(
            batch_size=1, radius=4.5, elevation=20.0, is_flexicubes=self.IS_FLEXICUBES).to(self.device)
        images = images.unsqueeze(0).to(self.device )
        images = v2.functional.resize(images, (320, 320), interpolation=3, antialias=True).clamp(0, 1)
        os.makedirs(out_dir, exist_ok=True)
        
        # 고정된 .obj 경로 생성
        mesh_basename = f"mesh_{uuid.uuid4().hex[:8]}"
        mesh_fpath = os.path.join(out_dir, f"{mesh_basename}.obj")
        video_fpath = os.path.join(out_dir, f"{mesh_basename}.mp4")

        with torch.no_grad():
            planes = self.model.forward_planes(images, input_cameras)
            chunk_size = 20 if self.IS_FLEXICUBES else 1
            render_size = 384
            frames = []
            for i in tqdm(range(0, render_cameras.shape[1], chunk_size)):
                if self.IS_FLEXICUBES:
                    frame = self.model.forward_geometry(
                        planes, render_cameras[:, i:i+chunk_size], render_size=render_size)['img']
                else:
                    frame = self.model.synthesizer(
                        planes, cameras=render_cameras[:, i:i+chunk_size], render_size=render_size)['images_rgb']
                frames.append(frame)
            frames = torch.cat(frames, dim=1)
            self.images_to_video(frames[0], video_fpath, fps=30)
            print(f"Video saved to {video_fpath}")

        mesh_fpath = self.make_mesh(mesh_fpath, planes)
        return video_fpath, mesh_fpath
    
    def excute(self, images,out_dir='./tmp'):
        '''
        images -> make3d 실행
        '''
        video_fpath, mesh_fpath = self.make3d(images,out_dir)
        return video_fpath, mesh_fpath
    

        




