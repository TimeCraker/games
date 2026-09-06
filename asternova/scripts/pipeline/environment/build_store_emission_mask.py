# -*- coding: utf-8 -*-
"""AsterNova - Build the storefront lightbox emission mask for the corner
convenience store (24 コンビニ sign band).

Rasterizes the calibrated glb's triangles into UV space and keeps only texels
passing ALL gates, so white kick panels / recycle bins / tile wall / rooftop
equipment can never leak emission - only the fascia lightbox band glows:

  1. front-facing geometry (world normal z < FRONT_MAX_NZ, front = glTF -Z)
  2. sign band vertical band (SIGN_BAND_Y, fascia lightbox incl. 24 board)
  3. storefront x span (X_MAX, excludes the taller tiled wall section)
  4. albedo color candidate (white lightbox, green stripe, orange/red trim)

Run: python build_store_emission_mask.py
Inputs : art/models/neighborhood/buildings/convenience_store/convenience_store.glb
         render-lab/models/environment/convenience_store/tex_convenience_store_basecolor.jpg
Outputs: render-lab/models/environment/convenience_store/convenience_store_emission_mask.png (2048, L)
         %TEMP%/cs_mask_overlay.jpg (debug: mask in red over albedo)
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
ALBEDO = os.path.join(
    REPO, r"render-lab\models\environment\convenience_store\tex_convenience_store_basecolor.jpg"
)
OUT_MASK = os.path.join(
    REPO, r"render-lab\models\environment\convenience_store\convenience_store_emission_mask.png"
)
OUT_OVERLAY = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "cs_mask_overlay.jpg")

RES = 2048
FRONT_MAX_NZ = -0.35          # world normal z gate (front faces glTF -Z)
SIGN_BAND_Y = (2.75, 4.35)    # meters (glTF Y == Blender Z), fascia lightbox
X_MAX = 3.45                  # meters, storefront span (tiled wall starts left of -1.8 in Blender... keep both ends safe)


def log(msg):
    print("[cs_mask] " + str(msg), flush=True)


# ----------------------------------------------------------------------------
# 1. Parse glb: positions / uvs / indices
# ----------------------------------------------------------------------------
data = open(GLB, "rb").read()
clen = struct.unpack("<I", data[12:16])[0]
gltf = json.loads(data[20:20 + clen])
bin_off = 20 + clen + 8

node_transforms = 0
for node in gltf["nodes"]:
    if any(k in node for k in ("translation", "rotation", "scale", "matrix")):
        node_transforms += 1
if node_transforms:
    log(f"WARN: {node_transforms} node(s) carry transforms; gates assume identity")

acc = gltf["accessors"]
views = gltf["bufferViews"]


def read_attr(attr_idx, dtype, comps):
    attr = acc[attr_idx]
    view = views[attr["bufferView"]]
    start = bin_off + view.get("byteOffset", 0) + attr.get("byteOffset", 0)
    arr = np.frombuffer(data, dtype=dtype, count=attr["count"] * comps, offset=start)
    return arr.reshape(attr["count"], comps)


nz_buf = np.full((RES, RES), np.nan, dtype=np.float32)
wy_buf = np.full((RES, RES), np.nan, dtype=np.float32)
wx_buf = np.full((RES, RES), np.nan, dtype=np.float32)

total_tris = 0
for mesh in gltf["meshes"]:
    for prim in mesh["primitives"]:
        if "TEXCOORD_0" not in prim["attributes"] or "indices" not in prim:
            continue
        positions = read_attr(prim["attributes"]["POSITION"], "<f4", 3)
        uvs = read_attr(prim["attributes"]["TEXCOORD_0"], "<f4", 2)
        idx_acc = acc[prim["indices"]]
        idx_dtype = {5121: "<u1", 5123: "<u2", 5125: "<u4"}[idx_acc["componentType"]]
        indices = read_attr(prim["indices"], idx_dtype, 1).reshape(-1)
        total_tris += len(indices) // 3

        tri = indices.reshape(-1, 3)
        p = positions[tri]
        t = uvs[tri]
        ng = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-9)
        fc = p.mean(axis=1)

        px = np.clip((t[:, :, 0] * RES).astype(np.int32), 0, RES - 1)
        py = np.clip((t[:, :, 1] * RES).astype(np.int32), 0, RES - 1)

        for i in range(len(tri)):
            x0, x1 = px[i].min(), px[i].max()
            y0, y1 = py[i].min(), py[i].max()
            if x1 - x0 > RES // 2 or y1 - y0 > RES // 2:
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

log(f"verts covered tris={total_tris}")
covered = ~np.isnan(nz_buf)
log(f"rasterized texels: {int(covered.sum())}")

# ----------------------------------------------------------------------------
# 2. Albedo color gates
# ----------------------------------------------------------------------------
rgb = np.asarray(Image.open(ALBEDO).convert("RGB").resize((RES, RES), Image.BOX),
                 dtype=np.float32) / 255.0
v = rgb.max(axis=2)
mn = rgb.min(axis=2)
s = np.where(v > 1e-4, (v - mn) / np.maximum(v, 1e-4), 0.0)
m = (v - mn) > 1e-4
hue = np.zeros_like(v)
rr, gg, bb = rgb[..., 0][m], rgb[..., 1][m], rgb[..., 2][m]
h = np.where(v[m] == rr, ((gg - bb) / (v[m] - mn[m])) % 6,
             np.where(v[m] == gg, (bb - rr) / (v[m] - mn[m]) + 2,
                      (rr - gg) / (v[m] - mn[m]) + 4)) * 60.0
hue[m] = h

whiteish = (v > 0.72) & (s < 0.28)            # lightbox white + 24 board
green = (hue >= 85.0) & (hue <= 170.0) & (s > 0.25) & (v > 0.25)   # brand stripe
warmtrim = (hue <= 45.0) & (s > 0.45) & (v > 0.35)  # orange/red trim + 24 logo
candidate = whiteish | green | warmtrim

# ----------------------------------------------------------------------------
# 3. Combine gates -> mask, clean specks, feather
# ----------------------------------------------------------------------------
band = (wy_buf >= SIGN_BAND_Y[0]) & (wy_buf <= SIGN_BAND_Y[1])
xspan = wx_buf <= X_MAX
front = nz_buf < FRONT_MAX_NZ
mask = covered & front & band & xspan & candidate
log(f"gated texels: front={int((covered & front).sum())} "
    f"+band={int((covered & front & band).sum())} "
    f"+x={int((covered & front & band & xspan).sum())} "
    f"+color={int(mask.sum())}")


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


mask = dilate(dilate(erode(erode(mask))))
mask = dilate(mask)
soft = mask.astype(np.float32)
for _ in range(2):
    soft = (soft
            + np.roll(soft, 1, 0) + np.roll(soft, -1, 0)
            + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5.0
soft = np.clip(soft * 1.4, 0.0, 1.0)
soft[~covered] = 0.0
log(f"mask texels: {int((soft > 0.5).sum())} / {RES * RES}")

Image.fromarray((soft * 255).astype(np.uint8), mode="L").save(OUT_MASK)
log(f"mask saved: {OUT_MASK}")

overlay = (rgb * 0.55 + soft[..., None] * np.array([1.0, 0.12, 0.12]) * 0.75).clip(0, 1)
Image.fromarray((overlay * 255).astype(np.uint8)).save(OUT_OVERLAY, quality=92)
log(f"overlay saved: {OUT_OVERLAY}")
