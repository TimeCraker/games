#!/usr/bin/env python3
"""M1 三档画质同框对比看板: 低/中/高三档真机帧横向并排 + 中文标注.

输入: art/render_previews/scenes/qa/m1_qa_tier_{low,medium,high}.png (2048x1152)
输出: art/render_previews/scenes/m1_quality_three_tiers_compare.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]          # asternova/
QA = ROOT / "art/render_previews/scenes/qa"
OUT = ROOT / "art/render_previews/scenes/m1_quality_three_tiers_compare.png"

CELL_W, CELL_H = 1280, 720                         # 单格缩放尺寸
PAD = 24
HEADER_H = 132
CAPTION_H = 76

TIERS = [
    ("m1_qa_tier_low.png", "低档 Low", "60 FPS · 关 MSAA · 关泛光/SSAO/SSR · 樱花粒子 40"),
    ("m1_qa_tier_medium.png", "中档 Medium", "120 FPS · 2x MSAA · 泛光 Softlight 0.25 · 樱花粒子 100"),
    ("m1_qa_tier_high.png", "高档 High", "解锁帧率 · 4x MSAA · 全特效 SSAO/SSR · 樱花粒子 200"),
]

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT = "C:/Windows/Fonts/msyh.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def main() -> None:
    board_w = CELL_W * 3 + PAD * 4
    board_h = HEADER_H + CELL_H + CAPTION_H + PAD * 2
    board = Image.new("RGB", (board_w, board_h), (14, 17, 26))
    draw = ImageDraw.Draw(board)

    draw.text((PAD, 30), "AsterNova · M1 终极街区沙盒 — 三档画质同框对比",
              font=font(52, bold=True), fill=(235, 240, 250))
    draw.text((PAD, 96),
              "Forward+ (Vulkan Clustered) · AgX tonemap · 45° 侧逆阳光 1.3 · 双半球清冷天光 · 2048x1152 真机截图",
              font=font(24), fill=(150, 165, 195))

    for i, (name, title, caption) in enumerate(TIERS):
        x = PAD + i * (CELL_W + PAD)
        frame = Image.open(QA / name).resize((CELL_W, CELL_H), Image.LANCZOS)
        board.paste(frame, (x, HEADER_H))
        draw.rectangle([x - 1, HEADER_H - 1, x + CELL_W, HEADER_H + CELL_H],
                       outline=(70, 82, 110), width=1)
        draw.text((x + 2, HEADER_H + CELL_H + 12), title,
                  font=font(34, bold=True), fill=(120, 220, 170))
        draw.text((x + 2, HEADER_H + CELL_H + 52), caption,
                  font=font(22), fill=(185, 195, 215))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    board.save(OUT)
    print(f"[compose] saved: {OUT} size={board.size}")


if __name__ == "__main__":
    main()
