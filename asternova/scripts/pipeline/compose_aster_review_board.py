# -*- coding: utf-8 -*-
"""Compose the Aster assembly review board: 2D reference vs 3 Blender studio renders.

Layout: 2x2 grid on near-white background, each cell 1024x1024 -> 2048x2048 board.
  [0,0] turnaround_front.png (2D truth)   [0,1] aster_assembly_front.png
  [1,0] aster_assembly_three_quarter.png  [1,1] aster_assembly_back.png
Run: python compose_aster_review_board.py
"""
from PIL import Image, ImageDraw

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
PREV = REPO + r"\art\render_previews\characters\aster"
CELL = 1024
PAD = 8

CELLS = [
    (REPO + r"\art\characters\aster\turnaround_front.png", "2D Reference (turnaround_front)"),
    (PREV + r"\aster_assembly_front.png", "Blender Assembled - Front"),
    (PREV + r"\aster_assembly_three_quarter.png", "Blender Assembled - 3/4 View"),
    (PREV + r"\aster_assembly_back.png", "Blender Assembled - Back"),
]


def fit(img, w, h, bg=(250, 250, 252)):
    img = img.convert("RGB")
    scale = min(w / img.width, h / img.height)
    img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), bg)
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


board = Image.new("RGB", (CELL * 2 + PAD * 3, CELL * 2 + PAD * 3), (238, 239, 244))
draw = ImageDraw.Draw(board)
for i, (path, label) in enumerate(CELLS):
    col, row = i % 2, i // 2
    x = PAD + col * (CELL + PAD)
    y = PAD + row * (CELL + PAD)
    board.paste(fit(Image.open(path), CELL, CELL - 44), (x, y))
    draw.rectangle([x, y + CELL - 40, x + CELL, y + CELL], fill=(40, 44, 60))
    draw.text((x + 14, y + CELL - 30), label, fill=(240, 242, 248))
out = PREV + r"\aster_assembly_review.png"
board.save(out)
print("board saved:", out, board.size)
