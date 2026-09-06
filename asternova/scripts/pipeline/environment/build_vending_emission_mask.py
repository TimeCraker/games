# -*- coding: utf-8 -*-
"""AsterNova - Build the showcase-window emission mask for the dual vending machine.

Rasterizes the calibrated glb's triangles into UV space, then keeps only texels
that pass ALL geometric + color gates, so the machine body / coin slot / recycle
bin can never leak emission - only the drink-showcase interior lights up:

  1. front-facing geometry  (world normal z < FRONT_MAX_NZ, front = glTF -Z)
  2. showcase vertical band (WINDOW_BAND_Y, excludes dispensing bin / red logo strip)
  3. Calpis machine only    (world x >= CALPIS_MIN_X, excludes the KAKE touchscreen
     on the white machine and the recycle bin)
  4. albedo color candidate (saturated drink colors, or warm-lit interior strip)

Run: python build_vending_emission_mask.py
Inputs : art/models/neighborhood/props/vending_machine/vending_machine_dual.glb
         render-lab/models/environment/vending_machine_dual_4k_albedo.jpg
Outputs: render-lab/models/environment/vending_machine_dual_emission_mask.png (1024, L)
         %TEMP%/vm_mask_overlay.jpg (debug: mask in red over albedo)
"""
import json
import os
import struct

import numpy as np
from PIL import Image

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
GLB = os.path.join(REPO, r"art\models\neighborhood\props\vending_machine\vending_machine_dual.glb")
ALBEDO = os.path.join(REPO, r"render-lab\models\environment\vending_machine_dual_4k_albedo.jpg")
OUT_MASK = os.path.join(REPO, r"render-lab\models\environment\vending_machine_dual_emission_mask.png")
OUT_OVERLAY = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "vm_mask_overlay.jpg")

RES = 1024
FRONT_MAX_NZ = -0.35          # world-space geometric normal z gate (front faces -Z)
WINDOW_BAND_Y = (0.86, 1.64)  # meters, showcase window vertical band
CALPIS_MIN_X = 0.02           # meters, only the blue Calpis machine may glow


def log(msg):
    print("[vm_mask] " + str(msg), flush=True)


# ----------------------------------------------------------------------------
# 1. Parse glb: positions / uvs / indices (node transform is identity, verified)
# ----------------------------------------------------------------------------
data = open(GLB, "rb").read()
clen = struct.unpack("<I", data[12:16])[0]
gltf = json.loads(data[20:20 + clen])
bin_off = 20 + clen + 8

for node in gltf["nodes"]:
    if any(k in node for k in ("translation", "rotation", "scale", "matrix")):
        raise RuntimeError("node transform is not identity; add transform handling")

prim = gltf["meshes"][0]["primitives"][0]
acc = gltf["accessors"]
views = gltf["bufferViews"]


def read_attr(attr_idx, dtype, comps):
    attr = acc[attr_idx]
    view = views[attr["bufferView"]]
    start = bin_off + view.get("byteOffset", 0) + attr.get("byteOffset", 0)
    arr = np.frombuffer(data, dtype=dtype, count=attr["count"] * comps, offset=start)
    return arr.reshape(attr["count"], comps)


positions = read_attr(prim["attributes"]["POSITION"], "<f4", 3)
uvs = read_attr(prim["attributes"]["TEXCOORD_0"], "<f4", 2)
idx_acc = acc[prim["indices"]]
idx_dtype = {5121: "<u1", 5123: "<u2", 5125: "<u4"}[idx_acc["componentType"]]
indices = read_attr(prim["indices"], idx_dtype, 1).reshape(-1)
log(f"verts={len(positions)} tris={len(indices) // 3}")

# ----------------------------------------------------------------------------
# 2. Rasterize per-triangle flat attributes into UV space (glTF uv: origin top-left)
# ----------------------------------------------------------------------------
nz_buf = np.full((RES, RES), np.nan, dtype=np.float32)  # face normal z (world)
wy_buf = np.full((RES, RES), np.nan, dtype=np.float32)  # face centroid world y
wx_buf = np.full((RES, RES), np.nan, dtype=np.float32)  # face centroid world x

tri = indices.reshape(-1, 3)
p = positions[tri]                     # (T,3,3)
t = uvs[tri]                           # (T,3,2)
ng = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-9)
fc = p.mean(axis=1)                    # face centroid world position

px = np.clip((t[:, :, 0] * RES).astype(np.int32), 0, RES - 1)
py = np.clip((t[:, :, 1] * RES).astype(np.int32), 0, RES - 1)

for i in range(len(tri)):
    x0, x1 = px[i].min(), px[i].max()
    y0, y1 = py[i].min(), py[i].max()
    if x1 - x0 > RES // 2 or y1 - y0 > RES // 2:  # degenerate UV stretch, skip
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    ax, ay = t[i, 0] * RES
    bx, by = t[i, 1] * RES
    cx2, cy2 = t[i, 2] * RES
    den = (by - cy2) * (ax - cx2) + (cx2 - bx) * (ay - cy2)
    if abs(den) < 1e-9:
        continue
    w0 = ((by - cy2) * (gx - cx2) + (cx2 - bx) * (gy - cy2)) / den
    w1 = ((cy2 - ay) * (gx - cx2) + (ax - cx2) * (gy - cy2)) / den
    w2 = 1.0 - w0 - w1
    inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
    if not inside.any():
        continue
    iy = gy[inside].astype(np.int32)
    ix = gx[inside].astype(np.int32)
    nz_buf[iy, ix] = ng[i, 2]
    wy_buf[iy, ix] = fc[i, 1]
    wx_buf[iy, ix] = fc[i, 0]

covered = ~np.isnan(nz_buf)
log(f"rasterized texels: {int(covered.sum())}")

# ----------------------------------------------------------------------------
# 3. Albedo color gates
# ----------------------------------------------------------------------------
rgb = np.asarray(Image.open(ALBEDO).convert("RGB").resize((RES, RES), Image.BOX), dtype=np.float32) / 255.0
v = rgb.max(axis=2)
mn = rgb.min(axis=2)
s = np.where(v > 1e-4, (v - mn) / np.maximum(v, 1e-4), 0.0)
hue = np.zeros_like(v)
m = (v - mn) > 1e-4
rr, gg, bb = r_ch, g_ch, b_ch = rgb[..., 0][m], rgb[..., 1][m], rgb[..., 2][m]
h = np.where(v[m] == rr, ((gg - bb) / (v[m] - mn[m])) % 6,
             np.where(v[m] == gg, (bb - rr) / (v[m] - mn[m]) + 2,
                      (rr - gg) / (v[m] - mn[m]) + 4)) * 60.0
hue[m] = h

colorful = (s > 0.42) & (v > 0.30)
warm = (v > 0.55) & (s > 0.15) & (hue >= 10.0) & (hue <= 60.0)
candidate = colorful | warm

# ----------------------------------------------------------------------------
# 4. Combine gates -> mask, clean specks, feather
# ----------------------------------------------------------------------------
band = (wy_buf >= WINDOW_BAND_Y[0]) & (wy_buf <= WINDOW_BAND_Y[1])
calpis = wx_buf >= CALPIS_MIN_X
front = nz_buf < FRONT_MAX_NZ
mask = covered & front & band & calpis & candidate


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
    return c


mask = dilate(dilate(erode(erode(mask))))  # strong open: kill specks <= ~4px
mask = dilate(mask)                        # regrow 1px to cover triangle edges
soft = mask.astype(np.float32)
for _ in range(2):
    soft = (soft
            + np.roll(soft, 1, 0) + np.roll(soft, -1, 0)
            + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5.0
soft = np.clip(soft * 1.4, 0.0, 1.0)
soft[~covered] = 0.0
log(f"mask texels: {int((soft > 0.5).sum())} / {RES * RES}")

# ----------------------------------------------------------------------------
# 5. Save mask + debug overlay
# ----------------------------------------------------------------------------
Image.fromarray((soft * 255).astype(np.uint8), mode="L").save(OUT_MASK)
log(f"mask saved: {OUT_MASK}")

overlay = (rgb * 0.55 + soft[..., None] * np.array([1.0, 0.12, 0.12]) * 0.75).clip(0, 1)
Image.fromarray((overlay * 255).astype(np.uint8)).save(OUT_OVERLAY, quality=92)
log(f"overlay saved: {OUT_OVERLAY}")
