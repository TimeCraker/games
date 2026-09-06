# -*- coding: utf-8 -*-
"""Slice the vending machine concept sheet into Tripo-ready assets.

Outputs (relative to asternova/):
  art/references/vending_machine/vending_combo_45_tripo.png  (45° view, label erased, 40px padding)
  art/references/vending_machine/vending_combo_front.png     (front orthographic view)
Plus a copy of the Tripo image to C:/Users/TimeCraker/Downloads/.
"""
import os
import shutil

from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(BASE, "art/references/vending_machine/vending_machine_concept_sheet.png")
out_dir = os.path.join(BASE, "art/references/vending_machine")
os.makedirs(out_dir, exist_ok=True)

img = Image.open(src_path).convert("RGB")

# 1. Crop the 45° isometric combo (approx. x: 340~950, y: 5~575)
crop_45 = img.crop((340, 5, 950, 575))

# Erase the top-left "45° 透视图 / 45° Isometric View" label so Tripo
# does not turn the floating text into stray 3D geometry.
draw = ImageDraw.Draw(crop_45)
draw.rectangle([0, 0, 210, 42], fill=(255, 255, 255))

# 40px white breathing margin
w, h = crop_45.size
padded_45 = Image.new("RGB", (w + 80, h + 80), (255, 255, 255))
padded_45.paste(crop_45, (40, 40))

out_45 = os.path.join(out_dir, "vending_combo_45_tripo.png")
padded_45.save(out_45, quality=100)

# Sync to Downloads for direct drag-and-drop upload to Tripo
downloads_copy = r"C:\Users\TimeCraker\Downloads\vending_combo_45_tripo.png"
shutil.copy2(out_45, downloads_copy)
print(f"[OK] 45° 建模专用图已生成并同步至 Downloads: {padded_45.size}")

# 2. Crop the front orthographic reference view
crop_front = img.crop((12, 185, 325, 475))
out_front = os.path.join(out_dir, "vending_combo_front.png")
crop_front.save(out_front, quality=100)
print(f"[OK] 正面参考图已导出: {crop_front.size}")
