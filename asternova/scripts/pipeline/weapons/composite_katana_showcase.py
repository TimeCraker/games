"""
Composite Showcase Presentation Board for Aster's Katana '星霜月华'
"""

import os
from PIL import Image, ImageDraw, ImageFont

def composite_showcase():
    base_dir = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\weapons\aster_katana"
    temp_dir = os.path.join(base_dir, "temp_renders")
    out_path = os.path.join(base_dir, "katana_preview.png")

    sheathed_path = os.path.join(temp_dir, "sheathed.png")
    unsheathed_path = os.path.join(temp_dir, "unsheathed.png")
    tsuba_path = os.path.join(temp_dir, "close_tsuba.png")
    tassel_path = os.path.join(temp_dir, "close_tassel.png")
    kissaki_path = os.path.join(temp_dir, "close_kissaki.png")

    # Canvas dimensions
    W, H = 2400, 2150
    board = Image.new("RGBA", (W, H), (20, 22, 29, 255)) # #14161D
    draw = ImageDraw.Draw(board)

    # Fonts
    # Windows system font fallback
    font_large = None
    font_med = None
    font_small = None
    font_title = None

    for font_name in ["msyh.ttc", "simhei.ttf", "arial.ttf"]:
        try:
            font_title = ImageFont.truetype(font_name, 38)
            font_large = ImageFont.truetype(font_name, 26)
            font_med = ImageFont.truetype(font_name, 20)
            font_small = ImageFont.truetype(font_name, 16)
            break
        except Exception:
            continue

    if font_title is None:
        font_title = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # --- 1. Top Header Banner ---
    draw.rectangle([0, 0, W, 110], fill=(26, 28, 38, 255))
    draw.line([(0, 110), (W, 110)], fill=(235, 197, 122, 255), width=3) # Gold divider #EBC57A

    draw.text((60, 22), "ASTER'S KATANA · 专属佩刀「星霜月华」3D 资产验收看板", fill=(245, 247, 255, 255), font=font_title)
    draw.text((60, 68), "完全独立可拔刀双 Mesh 结构 · 统一刀鞘口原点 (0, 0, 0) · 899 三角面 120 FPS 高刷性能极简低模", fill=(174, 209, 250, 255), font=font_med)

    # --- 2. Section 1: Sheathed Form ---
    draw.rectangle([40, 130, W - 40, 670], fill=(28, 30, 41, 255), outline=(50, 54, 70, 255), width=1)
    # Section Label Tag
    draw.rectangle([40, 130, 420, 168], fill=(42, 46, 64, 255))
    draw.text((55, 138), "【佩刀入鞘态】SHEATHED STATE", fill=(235, 197, 122, 255), font=font_small)
    draw.text((440, 140), "Blade_Mesh 与 Scabbard_Mesh 局部坐标与旋转均为 (0, 0, 0) · 刀刃完全藏于鞘内 · 平时挂载于 Aster 左腰", fill=(200, 205, 220, 255), font=font_small)

    if os.path.exists(sheathed_path):
        sheathed_img = Image.open(sheathed_path).convert("RGBA")
        # Resize to fit width comfortably
        s_w, s_h = sheathed_img.size
        target_w = W - 80
        target_h = int(s_h * (target_w / s_w))
        if target_h > 490:
            target_h = 490
            target_w = int(s_w * (target_h / s_h))
        resized_s = sheathed_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        offset_x = (W - target_w) // 2
        board.paste(resized_s, (offset_x, 172), resized_s)

    # --- 3. Section 2: Unsheathed Form ---
    draw.rectangle([40, 690, W - 40, 1410], fill=(28, 30, 41, 255), outline=(50, 54, 70, 255), width=1)
    draw.rectangle([40, 690, 460, 728], fill=(42, 46, 64, 255))
    draw.text((55, 698), "【出鞘刀刃与独立刀鞘】UNSHEATHED STATE", fill=(174, 209, 250, 255), font=font_small)
    draw.text((480, 700), "双网格对象物理分离 · 原生支持居合拔刀、左手握鞘、右手挥刀动作 · 拔刀动画沿 +Z 平移 0.75m 即刻顺滑出鞘", fill=(200, 205, 220, 255), font=font_small)

    if os.path.exists(unsheathed_path):
        unsheathed_img = Image.open(unsheathed_path).convert("RGBA")
        u_w, u_h = unsheathed_img.size
        target_w = W - 80
        target_h = int(u_h * (target_w / u_w))
        if target_h > 670:
            target_h = 670
            target_w = int(u_w * (target_h / u_h))
        resized_u = unsheathed_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        offset_x = (W - target_w) // 2
        board.paste(resized_u, (offset_x, 732), resized_u)

    # --- 4. Section 3: Detail Close-up Cards ---
    card_w = (W - 80 - 40) // 3 # ~746 px
    card_h = 580
    card_y = 1430

    cards_meta = [
        ("四芒星立体护手 (Tsuba 3/4 View)", "香槟金流线外框 + 象牙白花瓣镶嵌 + 水蓝星钻", tsuba_path),
        ("白柄卷目贯与星芒吊坠 (Tsuka & Tassel)", "象牙白菱形编织柄卷 + 双垂丝带 + 金星吊坠", tassel_path),
        ("利落刀尖切先与刃纹 (Kissaki & Hamon)", "微弧 Shinogi-zukuri + 冷天蓝渐变高光线", kissaki_path),
    ]

    for idx, (title, desc, img_path) in enumerate(cards_meta):
        card_x = 40 + idx * (card_w + 20)
        draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], fill=(28, 30, 41, 255), outline=(50, 54, 70, 255), width=1)
        # Card header
        draw.rectangle([card_x, card_y, card_x + card_w, card_y + 44], fill=(36, 40, 56, 255))
        draw.text((card_x + 16, card_y + 12), title, fill=(245, 247, 255, 255), font=font_med)
        
        # Image area
        if os.path.exists(img_path):
            card_img = Image.open(img_path).convert("RGBA")
            # Fit inside card
            cw_avail = card_w - 20
            ch_avail = card_h - 90
            img_w, img_h = card_img.size
            scale = min(cw_avail / img_w, ch_avail / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            resized_c = card_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            px = card_x + (card_w - new_w) // 2
            py = card_y + 50 + (ch_avail - new_h) // 2
            board.paste(resized_c, (px, py), resized_c)
            
        # Card footer desc
        draw.text((card_x + 16, card_y + card_h - 32), desc, fill=(174, 209, 250, 255), font=font_small)

    # --- 5. Bottom Technical Specs Footer ---
    draw.rectangle([0, H - 100, W, H], fill=(16, 18, 24, 255))
    draw.line([(0, H - 100), (W, H - 100)], fill=(50, 54, 70, 255), width=2)

    footer_col1 = "【工程拓扑】整刀总三角面数: 899 面 (刀身 Blade_Mesh: 503 面 | 刀鞘 Scabbard_Mesh: 396 面) —— 严守 120 FPS 高刷性能红线"
    footer_col2 = "【尺寸基准】全长 95.5cm (刀刃约 70cm / 刀柄约 25cm / 刀鞘约 72cm) · 局部原点对齐: 刀鞘口 Koiguchi (0, 0, 0)"
    footer_col3 = "【交付路径】aster_katana.blend | aster_katana.glb | textures/tex_katana_basecolor.png (2048x2048) · 启用 Inverted Hull 描边"

    draw.text((60, H - 85), footer_col1, fill=(235, 197, 122, 255), font=font_small)
    draw.text((60, H - 60), footer_col2, fill=(200, 205, 220, 255), font=font_small)
    draw.text((60, H - 35), footer_col3, fill=(174, 209, 250, 255), font=font_small)

    board.save(out_path, quality=95)
    print(f"Composite showcase board saved successfully at: {out_path}")

if __name__ == "__main__":
    composite_showcase()
