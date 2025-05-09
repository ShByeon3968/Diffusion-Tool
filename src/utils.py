# Modified from: https://github.com/TencentARC/InstantMesh
# Original Author: Tencent ARC Lab
# Modifications by: [Sanghyun Byun] (https://github.com/ShByeon3968)
# License: Apache License 2.0

import rembg
from PIL import Image
from typing import *
import numpy as np
import importlib
import torch
import torch.nn.functional as F
import xatlas
import trimesh
import cv2
import nvdiffrast.torch as dr
from PIL import Image

## ---- inference utils ----
def remove_background(image: Image.Image,
    rembg_session: Any = None,
    force: bool = False,
    **rembg_kwargs,
) -> Image.Image:
    do_remove = True
    if image.mode == "RGBA" and image.getextrema()[3][0] < 255:
        do_remove = False
    do_remove = do_remove or force
    if do_remove:
        image = rembg.remove(image, session=rembg_session, **rembg_kwargs)
    return image

def resize_foreground(
    image: Image.Image,
    ratio: float,
) -> Image.Image:
    image = np.array(image)
    assert image.shape[-1] == 4
    alpha = np.where(image[..., 3] > 0)
    y1, y2, x1, x2 = (
        alpha[0].min(),
        alpha[0].max(),
        alpha[1].min(),
        alpha[1].max(),
    )
    # crop the foreground
    fg = image[y1:y2, x1:x2]
    # pad to square
    size = max(fg.shape[0], fg.shape[1])
    ph0, pw0 = (size - fg.shape[0]) // 2, (size - fg.shape[1]) // 2
    ph1, pw1 = size - fg.shape[0] - ph0, size - fg.shape[1] - pw0
    new_image = np.pad(
        fg,
        ((ph0, ph1), (pw0, pw1), (0, 0)),
        mode="constant",
        constant_values=((0, 0), (0, 0), (0, 0)),
    )

    # compute padding according to the ratio
    new_size = int(new_image.shape[0] / ratio)
    # pad to size, double side
    ph0, pw0 = (new_size - size) // 2, (new_size - size) // 2
    ph1, pw1 = new_size - size - ph0, new_size - size - pw0
    new_image = np.pad(
        new_image,
        ((ph0, ph1), (pw0, pw1), (0, 0)),
        mode="constant",
        constant_values=((0, 0), (0, 0), (0, 0)),
    )
    new_image = Image.fromarray(new_image)
    return new_image
## ---------------------------------

## ---- train utils ----

def count_params(model, verbose=False):
    total_params = sum(p.numel() for p in model.parameters())
    if verbose:
        print(f"{model.__class__.__name__} has {total_params*1.e-6:.2f} M params.")
    return total_params


def instantiate_from_config(config):
    if not "target" in config:
        if config == '__is_first_stage__':
            return None
        elif config == "__is_unconditional__":
            return None
        raise KeyError("Expected key `target` to instantiate.")
    return get_obj_from_str(config["target"])(**config.get("params", dict()))


def get_obj_from_str(string, reload=False):
    module, cls = string.rsplit(".", 1)
    if reload:
        module_imp = importlib.import_module(module)
        importlib.reload(module_imp)
    return getattr(importlib.import_module(module, package=None), cls)
## ----------------------------------

## ---- Camera utils ---
def pad_camera_extrinsics_4x4(extrinsics):
    if extrinsics.shape[-2] == 4:
        return extrinsics
    padding = torch.tensor([[0, 0, 0, 1]]).to(extrinsics)
    if extrinsics.ndim == 3:
        padding = padding.unsqueeze(0).repeat(extrinsics.shape[0], 1, 1)
    extrinsics = torch.cat([extrinsics, padding], dim=-2)
    return extrinsics


def center_looking_at_camera_pose(camera_position: torch.Tensor, look_at: torch.Tensor = None, up_world: torch.Tensor = None):
    """
    Create OpenGL camera extrinsics from camera locations and look-at position.

    camera_position: (M, 3) or (3,)
    look_at: (3)
    up_world: (3)
    return: (M, 3, 4) or (3, 4)
    """
    # by default, looking at the origin and world up is z-axis
    if look_at is None:
        look_at = torch.tensor([0, 0, 0], dtype=torch.float32)
    if up_world is None:
        up_world = torch.tensor([0, 0, 1], dtype=torch.float32)
    if camera_position.ndim == 2:
        look_at = look_at.unsqueeze(0).repeat(camera_position.shape[0], 1)
        up_world = up_world.unsqueeze(0).repeat(camera_position.shape[0], 1)

    # OpenGL camera: z-backward, x-right, y-up
    z_axis = camera_position - look_at
    z_axis = F.normalize(z_axis, dim=-1).float()
    x_axis = torch.linalg.cross(up_world, z_axis, dim=-1)
    x_axis = F.normalize(x_axis, dim=-1).float()
    y_axis = torch.linalg.cross(z_axis, x_axis, dim=-1)
    y_axis = F.normalize(y_axis, dim=-1).float()

    extrinsics = torch.stack([x_axis, y_axis, z_axis, camera_position], dim=-1)
    extrinsics = pad_camera_extrinsics_4x4(extrinsics)
    return extrinsics


def spherical_camera_pose(azimuths: np.ndarray, elevations: np.ndarray, radius=2.5):
    azimuths = np.deg2rad(azimuths)
    elevations = np.deg2rad(elevations)

    xs = radius * np.cos(elevations) * np.cos(azimuths)
    ys = radius * np.cos(elevations) * np.sin(azimuths)
    zs = radius * np.sin(elevations)

    cam_locations = np.stack([xs, ys, zs], axis=-1)
    cam_locations = torch.from_numpy(cam_locations).float()

    c2ws = center_looking_at_camera_pose(cam_locations)
    return c2ws


def get_circular_camera_poses(M=120, radius=2.5, elevation=30.0):
    # M: number of circular views
    # radius: camera dist to center
    # elevation: elevation degrees of the camera
    # return: (M, 4, 4)
    assert M > 0 and radius > 0

    elevation = np.deg2rad(elevation)

    camera_positions = []
    for i in range(M):
        azimuth = 2 * np.pi * i / M
        x = radius * np.cos(elevation) * np.cos(azimuth)
        y = radius * np.cos(elevation) * np.sin(azimuth)
        z = radius * np.sin(elevation)
        camera_positions.append([x, y, z])
    camera_positions = np.array(camera_positions)
    camera_positions = torch.from_numpy(camera_positions).float()
    extrinsics = center_looking_at_camera_pose(camera_positions)
    return extrinsics


def FOV_to_intrinsics(fov, device='cpu'):
    """
    Creates a 3x3 camera intrinsics matrix from the camera field of view, specified in degrees.
    Note the intrinsics are returned as normalized by image size, rather than in pixel units.
    Assumes principal point is at image center.
    """
    focal_length = 0.5 / np.tan(np.deg2rad(fov) * 0.5)
    intrinsics = torch.tensor([[focal_length, 0, 0.5], [0, focal_length, 0.5], [0, 0, 1]], device=device)
    return intrinsics


def get_zero123plus_input_cameras(batch_size=1, radius=4.0, fov=30.0):
    """
    Get the input camera parameters.
    """
    azimuths = np.array([30, 90, 150, 210, 270, 330]).astype(float)
    elevations = np.array([20, -10, 20, -10, 20, -10]).astype(float)
    
    c2ws = spherical_camera_pose(azimuths, elevations, radius)
    c2ws = c2ws.float().flatten(-2)

    Ks = FOV_to_intrinsics(fov).unsqueeze(0).repeat(6, 1, 1).float().flatten(-2)

    extrinsics = c2ws[:, :12]
    intrinsics = torch.stack([Ks[:, 0], Ks[:, 4], Ks[:, 2], Ks[:, 5]], dim=-1)
    cameras = torch.cat([extrinsics, intrinsics], dim=-1)

    return cameras.unsqueeze(0).repeat(batch_size, 1, 1)
## ----------------------------------

## --------- Mesh utils --------

# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# NVIDIA CORPORATION & AFFILIATES and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION & AFFILIATES is strictly prohibited.

def save_obj(pointnp_px3, facenp_fx3, colornp_px3, fpath):

    pointnp_px3 = pointnp_px3 @ np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]])
    facenp_fx3 = facenp_fx3[:, [2, 1, 0]]

    mesh = trimesh.Trimesh(
        vertices=pointnp_px3, 
        faces=facenp_fx3, 
        vertex_colors=colornp_px3,
    )
    mesh.export(fpath, 'obj')


def save_glb(pointnp_px3, facenp_fx3, colornp_px3, fpath):

    pointnp_px3 = pointnp_px3 @ np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]])

    mesh = trimesh.Trimesh(
        vertices=pointnp_px3, 
        faces=facenp_fx3, 
        vertex_colors=colornp_px3,
    )
    mesh.export(fpath, 'glb')


def save_obj_with_mtl(pointnp_px3, tcoords_px2, facenp_fx3, facetex_fx3, texmap_hxwx3, fname):
    import os
    fol, na = os.path.split(fname)
    na, _ = os.path.splitext(na)

    matname = '%s/%s.mtl' % (fol, na)
    fid = open(matname, 'w')
    fid.write('newmtl material_0\n')
    fid.write('Kd 1 1 1\n')
    fid.write('Ka 0 0 0\n')
    fid.write('Ks 0.4 0.4 0.4\n')
    fid.write('Ns 10\n')
    fid.write('illum 2\n')
    fid.write('map_Kd %s.png\n' % na)
    fid.close()
    ####

    fid = open(fname, 'w')
    fid.write('mtllib %s.mtl\n' % na)

    for pidx, p in enumerate(pointnp_px3):
        pp = p
        fid.write('v %f %f %f\n' % (pp[0], pp[1], pp[2]))

    for pidx, p in enumerate(tcoords_px2):
        pp = p
        fid.write('vt %f %f\n' % (pp[0], pp[1]))

    fid.write('usemtl material_0\n')
    for i, f in enumerate(facenp_fx3):
        f1 = f + 1
        f2 = facetex_fx3[i] + 1
        fid.write('f %d/%d %d/%d %d/%d\n' % (f1[0], f2[0], f1[1], f2[1], f1[2], f2[2]))
    fid.close()

    # save texture map
    lo, hi = 0, 1
    img = np.asarray(texmap_hxwx3, dtype=np.float32)
    img = (img - lo) * (255 / (hi - lo))
    img = img.clip(0, 255)
    mask = np.sum(img.astype(np.float32), axis=-1, keepdims=True)
    mask = (mask <= 3.0).astype(np.float32)
    kernel = np.ones((3, 3), 'uint8')
    dilate_img = cv2.dilate(img, kernel, iterations=1)
    img = img * (1 - mask) + dilate_img * mask
    img = img.clip(0, 255).astype(np.uint8)
    Image.fromarray(np.ascontiguousarray(img[::-1, :, :]), 'RGB').save(f'{fol}/{na}.png')


def loadobj(meshfile):
    v = []
    f = []
    meshfp = open(meshfile, 'r')
    for line in meshfp.readlines():
        data = line.strip().split(' ')
        data = [da for da in data if len(da) > 0]
        if len(data) != 4:
            continue
        if data[0] == 'v':
            v.append([float(d) for d in data[1:]])
        if data[0] == 'f':
            data = [da.split('/')[0] for da in data]
            f.append([int(d) for d in data[1:]])
    meshfp.close()

    # torch need int64
    facenp_fx3 = np.array(f, dtype=np.int64) - 1
    pointnp_px3 = np.array(v, dtype=np.float32)
    return pointnp_px3, facenp_fx3


def loadobjtex(meshfile):
    v = []
    vt = []
    f = []
    ft = []
    meshfp = open(meshfile, 'r')
    for line in meshfp.readlines():
        data = line.strip().split(' ')
        data = [da for da in data if len(da) > 0]
        if not ((len(data) == 3) or (len(data) == 4) or (len(data) == 5)):
            continue
        if data[0] == 'v':
            assert len(data) == 4

            v.append([float(d) for d in data[1:]])
        if data[0] == 'vt':
            if len(data) == 3 or len(data) == 4:
                vt.append([float(d) for d in data[1:3]])
        if data[0] == 'f':
            data = [da.split('/') for da in data]
            if len(data) == 4:
                f.append([int(d[0]) for d in data[1:]])
                ft.append([int(d[1]) for d in data[1:]])
            elif len(data) == 5:
                idx1 = [1, 2, 3]
                data1 = [data[i] for i in idx1]
                f.append([int(d[0]) for d in data1])
                ft.append([int(d[1]) for d in data1])
                idx2 = [1, 3, 4]
                data2 = [data[i] for i in idx2]
                f.append([int(d[0]) for d in data2])
                ft.append([int(d[1]) for d in data2])
    meshfp.close()

    # torch need int64
    facenp_fx3 = np.array(f, dtype=np.int64) - 1
    ftnp_fx3 = np.array(ft, dtype=np.int64) - 1
    pointnp_px3 = np.array(v, dtype=np.float32)
    uvs = np.array(vt, dtype=np.float32)
    return pointnp_px3, facenp_fx3, uvs, ftnp_fx3

def convert_obj_to_glb(obj_path):
    mesh = trimesh.load(obj_path, force='mesh')
    glb_path = obj_path.replace(".obj", ".glb")
    mesh.export(glb_path)
    return glb_path


# ==============================================================================================
def interpolate(attr, rast, attr_idx, rast_db=None):
    return dr.interpolate(attr.contiguous(), rast, attr_idx, rast_db=rast_db, diff_attrs=None if rast_db is None else 'all')


def xatlas_uvmap(ctx, mesh_v, mesh_pos_idx, resolution):
    vmapping, indices, uvs = xatlas.parametrize(mesh_v.detach().cpu().numpy(), mesh_pos_idx.detach().cpu().numpy())

    # Convert to tensors
    indices_int64 = indices.astype(np.uint64, casting='same_kind').view(np.int64)

    uvs = torch.tensor(uvs, dtype=torch.float32, device=mesh_v.device)
    mesh_tex_idx = torch.tensor(indices_int64, dtype=torch.int64, device=mesh_v.device)
    # mesh_v_tex. ture
    uv_clip = uvs[None, ...] * 2.0 - 1.0

    # pad to four component coordinate
    uv_clip4 = torch.cat((uv_clip, torch.zeros_like(uv_clip[..., 0:1]), torch.ones_like(uv_clip[..., 0:1])), dim=-1)

    # rasterize
    rast, _ = dr.rasterize(ctx, uv_clip4, mesh_tex_idx.int(), (resolution, resolution))

    # Interpolate world space position
    gb_pos, _ = interpolate(mesh_v[None, ...], rast, mesh_pos_idx.int())
    mask = rast[..., 3:4] > 0
    return uvs, mesh_tex_idx, gb_pos, mask
