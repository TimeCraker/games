# -*- coding: utf-8 -*-
"""AsterNova - Pixel-level acceptance check for the vending machine review render.

Hard gates (紧急视觉纠偏令):
  1. subject white-area max brightness <= 245 (no 255 clipping anywhere on subjects)
  2. dead-white (RGB > 250) ratio kept tiny in subject regions (incident was 63.68%)
  3. clear cel cold shadows on fronts: enough shadow-band pixels and blue-shifted
     (B > R) so the subjects read as three-dimensional, not flat backlit slabs

Run: python check_review_pixels.py [review_png]
"""
import os
import sys

import numpy as np
from PIL import Image

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
DEFAULT_PNG = os.path.join(REPO, r"art\render_previews\environment\vending_machine_aster_review.png")

# fractional boxes of the 2048x1152 frame: Aster left-of-center, machine right
REGIONS = {
    "aster":   (0.16, 0.24, 0.46, 0.90),
    "machine": (0.50, 0.06, 0.97, 0.90),
}
MAX_L_ALLOW = 245
DEADWHITE_MAX_PCT = 1.0     # % pixels with max(R,G,B) > 250 allowed per subject region
SHADOW_MIN_PCT = 5.0        # % shadow-band pixels required per subject region
SHADOW_BAND = (60, 170)


def log(msg):
    print("[px_check] " + str(msg), flush=True)


def region_stats(arr, box):
    H, W = arr.shape[:2]
    x0, y0, x1, y1 = box
    r = arr[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)].astype(np.int32)
    L = r.max(axis=2)
    dead = (L > 250).mean() * 100.0
    near = (L > MAX_L_ALLOW).mean() * 100.0
    shadow = (L >= SHADOW_BAND[0]) & (L <= SHADOW_BAND[1])
    cold = float((r[..., 2] - r[..., 0])[shadow].mean()) if shadow.any() else 0.0
    return {
        "max_L": int(L.max()),
        "deadwhite_pct": round(float(dead), 3),
        "over245_pct": round(float(near), 3),
        "shadow_pct": round(float(shadow.mean() * 100.0), 3),
        "shadow_cold_BR": round(cold, 2),
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PNG
    arr = np.asarray(Image.open(path).convert("RGB"))
    log(f"checking {path} {arr.shape[1]}x{arr.shape[0]}")

    ok = True
    whole = region_stats(arr, (0.0, 0.0, 1.0, 1.0))
    log(f"whole   : {whole}")
    if whole["max_L"] > 255:
        ok = False
    for name, box in REGIONS.items():
        st = region_stats(arr, box)
        log(f"{name:7s}: {st}")
        if st["max_L"] > MAX_L_ALLOW:
            log(f"FAIL {name}: max brightness {st['max_L']} > {MAX_L_ALLOW}")
            ok = False
        if st["deadwhite_pct"] > DEADWHITE_MAX_PCT:
            log(f"FAIL {name}: dead-white {st['deadwhite_pct']}% > {DEADWHITE_MAX_PCT}%")
            ok = False
        if st["shadow_pct"] < SHADOW_MIN_PCT:
            log(f"FAIL {name}: shadow band only {st['shadow_pct']}% < {SHADOW_MIN_PCT}% (no cel shading)")
            ok = False
        if st["shadow_cold_BR"] < 1.0:
            log(f"FAIL {name}: shadows not cold (B-R={st['shadow_cold_BR']})")
            ok = False
    log("RESULT: " + ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
