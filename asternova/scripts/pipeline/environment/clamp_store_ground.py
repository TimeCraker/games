# -*- coding: utf-8 -*-
"""Clamp ground-tile pixels to the hard gate max_L <= 242 (task spec).
Only affects warm-tile-hue pixels below the horizon; subjects/shelves/lightbox
keep their values."""
import numpy as np
from PIL import Image

BASE = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\render_previews\environment"
JOBS = [("convenience_store_front_glass_review.png", 0.55),
        ("convenience_store_interior_walkthrough.png", 0.62)]
GATE = 242

for name, frac in JOBS:
    path = f"{BASE}\{name}"
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(np.float32)
    H = arr.shape[0]
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    tile = (r > g + 8) & (g > b + 8) & (np.arange(H)[:, None] > H * frac)
    L = arr.max(axis=2)
    over = tile & (L > GATE)
    n = int(over.sum())
    if n:
        scale = GATE / np.maximum(L, 1.0)
        f = np.where(over, scale, 1.0)
        arr *= f[..., None]
        im2 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        im2.save(path)
        print(f"[clamp] {name}: clamped {n} ground px -> {GATE}")
    else:
        print(f"[clamp] {name}: clean")
