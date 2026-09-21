# -*- coding: utf-8 -*-
"""Slice the convenience store concept sheet into Tripo-ready assets.

Outputs (relative to asternova/):
  art/references/convenience_store/convenience_store_45_tripo.png  (45° view, centered, 40px padding)
  art/references/convenience_store/convenience_store_front.png     (front orthographic view)
Plus a copy of the Tripo image to C:/Users/TimeCraker/Downloads/.
"""
import os
import shutil

import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
src_path = os.path.join(BASE, "art/references/convenience_store/convenience_store_concept_sheet.png")
out_dir = os.path.join(BASE, "art/references/convenience_store")
os.makedirs(out_dir, exist_ok=True)

img = Image.open(src_path).convert("RGB")


def trim_to_content(region, thr):
    """Bounding box of non-near-white pixels inside region (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = region
    arr = np.asarray(img.crop(region)).astype(int)
    ys, xs = np.where((255 - arr).max(axis=2) > thr)
    return (x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1)


# 1. 45° isometric building (upper half of the sheet). The sheet has no corner
#    label here, so trim straight to the subject (thr=2 keeps even the faintest
#    ground-shadow halo): the subject lands perfectly centered with an exact
#    40px white margin on every side, which fixed coordinates cannot guarantee.
bbox_45 = trim_to_content((0, 0, img.width, 555), thr=2)
crop_45 = img.crop(bbox_45)

w, h = crop_45.size
padded_45 = Image.new("RGB", (w + 80, h + 80), (255, 255, 255))
padded_45.paste(crop_45, (40, 40))

out_45 = os.path.join(out_dir, "convenience_store_45_tripo.png")
padded_45.save(out_45, quality=100)

# Sync to Downloads for direct drag-and-drop upload to Tripo
downloads_copy = r"C:\Users\TimeCraker\Downloads\convenience_store_45_tripo.png"
shutil.copy2(out_45, downloads_copy)
print(f"[OK] 便利店 45° 建模专用图已生成并同步至 Downloads: {padded_45.size} (content {crop_45.size})")

# 2. Front orthographic view (bottom-left section, its label included). Trim
#    keeps the real bottom edge (y≈706) — the naive y=690 guide would clip it —
#    while the x<=380 cap avoids bleeding into the adjacent Right View section.
bbox_front = trim_to_content((0, 560, 380, 715), thr=10)
margin = 10
crop_front = img.crop(
    (bbox_front[0] - margin, bbox_front[1] - margin, bbox_front[2] + margin, bbox_front[3] + margin)
)
out_front = os.path.join(out_dir, "convenience_store_front.png")
crop_front.save(out_front, quality=100)
print(f"[OK] 正面参考图已导出: {crop_front.size} (content bbox {bbox_front})")
