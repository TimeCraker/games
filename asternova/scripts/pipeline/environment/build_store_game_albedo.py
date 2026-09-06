# -*- coding: utf-8 -*-
"""AsterNova - Build the game albedo for the convenience store with lifted
interior-facing surfaces.

Tripo bakes the store's interior wall / shelf-back panels as dark navy, which
reads as dead-black regions from every interior camera. This script
rasterizes the calibrated glb into UV space, gates texels to interior-facing
geometry (normal points at the store core + inside the volume + near-vertical),
then applies a warm gamma lift to exactly those texels of the 8K albedo.
The raw atlas in art/ stays untouched; render-lab gets a derived game texture
that convenience_store_npr_setup.gd binds instead of the embedded one.

Run: python build_store_game_albedo.py
Inputs : art/models/neighborhood/buildings/convenience_store/convenience_store.glb
         art/models/neighborhood/buildings/convenience_store/textures/tex_convenience_store_basecolor.jpg
Outputs: render-lab/models/environment/convenience_store/convenience_store_albedo_game.jpg
         %TEMP%/cs_interior_mask_overlay.jpg (debug overlay)
"""
import json
import os
import struct

import numpy as np
from PIL import Image

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
GLB = os.path.join(
    REPO, r"art\models\neighborhood\buildings\convenience_store\convenience_store.glb"
)
RAW_ALBEDO = os.path.join(
    REPO, r"art\models\neighborhood\buildings\convenience_store\textures\tex_convenience_store_basecolor.jpg"
)
OUT_ALBEDO = os.path.join(
    REPO, r"render-lab\models\environment\convenience_store\convenience_store_albedo_game.jpg"
)
OUT_OVERLAY = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "cs_interior_mask_overlay.jpg")

RES = 2048
GAMMA = 1.65          # gamma lift exponent for interior texels
WARM = np.array([1.00, 0.96, 0.90], dtype=np.float32)  # warm push
# interior volume gate (glTF space: y-up, front = -Z)
X_LIM = 6.45
Z_RANGE = (-6.8, 5.6)
Y_RANGE = (0.25, 4.75)


def log(msg):
    print("[cs_albedo] " + str(msg), flush=True)


data = open(GLB, "rb").read()
clen = struct.unpack("<I", data[12:16])[0]
gltf = json.loads(data[20:20 + clen])
bin_off = 20 + clen + 8
acc = gltf["accessors"]
views = gltf["bufferViews"]


def read_attr(attr_idx, dtype, comps):
    attr = acc[attr_idx]
    view = views[attr["bufferView"]]
    start = bin_off + view.get("byteOffset", 0) + attr.get("byteOffset", 0)
    arr = np.frombuffer(data, dtype=dtype, count=attr["count"] * comps, offset=start)
    return arr.reshape(attr["count"], comps)


flag_buf = np.zeros((RES, RES), dtype=bool)
up_buf = np.zeros((RES, RES), dtype=bool)

total = 0
for mesh in gltf["meshes"]:
    for prim in mesh["primitives"]:
        if "TEXCOORD_0" not in prim["attributes"] or "indices" not in prim:
            continue
        positions = read_attr(prim["attributes"]["POSITION"], "<f4", 3)
        uvs = read_attr(prim["attributes"]["TEXCOORD_0"], "<f4", 2)
        idx_acc = acc[prim["indices"]]
        idx_dtype = {5121: "<u1", 5123: "<u2", 5125: "<u4"}[idx_acc["componentType"]]
        indices = read_attr(prim["indices"], idx_dtype, 1).reshape(-1)
        total += len(indices) // 3

        tri = indices.reshape(-1, 3)
        p = positions[tri]
        t = uvs[tri]
        ng = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-9)
        fc = p.mean(axis=1)

        in_vol = ((np.abs(fc[:, 0]) < X_LIM)
                  & (fc[:, 1] > Y_RANGE[0]) & (fc[:, 1] < Y_RANGE[1])
                  & (fc[:, 2] > Z_RANGE[0]) & (fc[:, 2] < Z_RANGE[1]))
        keep = in_vol
        if not keep.any():
            continue

        px = np.clip((t[:, :, 0] * RES).astype(np.int32), 0, RES - 1)
        py = np.clip((t[:, :, 1] * RES).astype(np.int32), 0, RES - 1)
        kt = t[keep]
        kpx, kpy = px[keep], py[keep]
        for i in range(kt.shape[0]):
            x0, x1 = kpx[i].min(), kpx[i].max()
            y0, y1 = kpy[i].min(), kpy[i].max()
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            ax, ay = kt[i, 0] * RES
            bx, by = kt[i, 1] * RES
            cx2, cy2 = kt[i, 2] * RES
            den = (by - cy2) * (ax - cx2) + (cx2 - bx) * (ay - cy2)
            if abs(den) < 1e-9:
                continue
            w0 = ((by - cy2) * (gx - cx2) + (cx2 - bx) * (gy - cy2)) / den
            w1 = ((cy2 - ay) * (gx - cx2) + (ax - cx2) * (gy - cy2)) / den
            w2 = 1.0 - w0 - w1
            inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
            if True:
                iy2 = gy[inside].astype(np.int32)
                ix2 = gx[inside].astype(np.int32)
                flag_buf[iy2, ix2] = True
                # 女儿墙/檐口冠部（含竖直面）；豁免招牌文字区（前脸竖直带 |x|<3）
                sign_band = (fc[i, 2] < -5.2 and abs(ng[i, 1]) < 0.35
                             and abs(fc[i, 0]) < 3.0)
                crown = fc[i, 1] > 3.6 and not sign_band
                awning_soffit = (2.6 < fc[i, 1] < 3.6 and fc[i, 2] < -5.0
                                 and ng[i, 1] < -0.15)
                near_flat = abs(ng[i, 1]) > 0.35 and fc[i, 1] > 2.0
                awning_tip = (abs(ng[i, 1]) < 0.35 and fc[i, 1] > 2.5
                              and fc[i, 0] < -3.2)
                if crown or awning_soffit or near_flat or awning_tip:
                    # 全模型高于 2m 的朝上/朝下面（搁板顶/压顶/雨棚顶底/屋顶）：
                    # 原图集为噪点斑驳，统一干净暖灰平色
                    up_buf[iy2, ix2] = True

log(f"tris={total} interior texels={int(flag_buf.sum())} / {RES * RES}")

# clean specks: open then feather
def erode(m):
    c = m.copy()
    c[1:, :] &= m[:-1, :]
    c[:-1, :] &= m[1:, :]
    c[:, 1:] &= m[:, :-1]
    c[:, :-1] &= m[:, 1:]
    return c


def dilate(m):
    c = m.copy()
    c[1:, :] |= m[:-1, :]
    c[:-1, :] |= m[1:, :]
    c[:, 1:] |= m[:, :-1]
    c[:, :-1] |= m[:, 1:]
    return m if False else c


mask = dilate(dilate(erode(erode(flag_buf))))
soft = mask.astype(np.float32)
for _ in range(2):
    soft = (soft + np.roll(soft, 1, 0) + np.roll(soft, -1, 0)
            + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5.0
soft = np.clip(soft * 1.35, 0.0, 1.0)
log(f"soft mask texels: {int((soft > 0.5).sum())}")

# ----------------------------------------------------------------------------
# apply warm gamma lift to masked texels only
# ----------------------------------------------------------------------------
rgb = np.asarray(Image.open(RAW_ALBEDO).convert("RGB").resize((RES, RES), Image.BOX),
                 dtype=np.float32) / 255.0
lifted = np.clip(rgb ** (1.0 / GAMMA) * WARM[None, None, :], 0.0, 1.0)
# 朝上店内面（搁板顶/压顶/机顶）：原图集为噪点斑驳，统一干净暖灰平色
flat = np.zeros_like(rgb)
flat[..., 0] = 0.62
flat[..., 1] = 0.60
flat[..., 2] = 0.57
lifted = lifted * (1.0 - up_buf[..., None]) + flat * up_buf[..., None]
out = rgb * (1.0 - soft[..., None]) + lifted * soft[..., None]

Image.fromarray((out * 255.0).astype(np.uint8)).save(OUT_ALBEDO, quality=92)
log(f"game albedo saved: {OUT_ALBEDO}")

overlay = (out * 0.72 + soft[..., None] * np.array([0.1, 0.9, 0.2]) * 0.45).clip(0, 1)
Image.fromarray((overlay * 255).astype(np.uint8)).save(OUT_OVERLAY, quality=92)
log(f"overlay saved: {OUT_OVERLAY}")
