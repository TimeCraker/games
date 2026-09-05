"""
Update generate_trim_sheet.py to increase contrast and readability of tile grout lines,
concrete formwork lines, window frames, and textures for CS2-level clarity from distance.
"""

import math
import os
import numpy as np
from PIL import Image, ImageDraw

OUTPUT_DIR = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\textures"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SIZE = 2048

def create_trim_sheet():
    print("Generating High-Contrast 2K Modern Japan Trim Sheet...")
    albedo = Image.new("RGB", (SIZE, SIZE), (160, 155, 145))
    height_map = np.zeros((SIZE, SIZE), dtype=np.float32)
    roughness = np.full((SIZE, SIZE), 180, dtype=np.uint8)
    
    draw = ImageDraw.Draw(albedo)
    
    # -------------------------------------------------------------
    # Strip 1 [Y: 0 ~ 512]: 米白防水瓷砖 (Off-white Japanese Ceramic Tiles)
    # -------------------------------------------------------------
    tile_w = 96
    tile_h = 32
    grout_w = 4
    y_start, y_end = 0, 512
    
    # Grout: darker charcoal-beige for high readability
    draw.rectangle([0, y_start, SIZE, y_end], fill=(140, 135, 128))
    height_map[y_start:y_end, :] = 0.15
    roughness[y_start:y_end, :] = 230
    
    rng = np.random.RandomState(42)
    
    for row_idx, y in enumerate(range(y_start, y_end, tile_h)):
        if y + tile_h > y_end:
            break
        row_offset = (tile_w // 2) if (row_idx % 2 == 1) else 0
        for col_idx, x in enumerate(range(-row_offset, SIZE + tile_w, tile_w)):
            variation = rng.randint(-12, 13)
            # Modern off-white / pale cream tile
            base_r = int(np.clip(238 + variation, 215, 252))
            base_g = int(np.clip(234 + variation, 210, 248))
            base_b = int(np.clip(226 + variation, 200, 242))
            
            tx1 = max(0, x + grout_w // 2)
            ty1 = y + grout_w // 2
            tx2 = min(SIZE, x + tile_w - grout_w // 2)
            ty2 = min(y_end, y + tile_h - grout_w // 2)
            
            if tx2 > tx1 and ty2 > ty1:
                draw.rectangle([tx1, ty1, tx2, ty2], fill=(base_r, base_g, base_b))
                # Tile bevel highlight and shadow
                draw.line([tx1, ty1, tx2, ty1], fill=(255, 255, 255), width=1)
                draw.line([tx1, ty2-1, tx2, ty2-1], fill=(180, 175, 165), width=1)
                draw.line([tx1, ty1, tx1, ty2], fill=(255, 255, 255), width=1)
                draw.line([tx2-1, ty1, tx2-1, ty2], fill=(180, 175, 165), width=1)
                
                height_map[ty1:ty2, tx1:tx2] = 0.9
                height_map[ty1:ty1+2, tx1:tx2] = 0.5
                height_map[ty2-2:ty2, tx1:tx2] = 0.5
                roughness[ty1:ty2, tx1:tx2] = int(np.clip(95 + variation * 2, 70, 130))

    # -------------------------------------------------------------
    # Strip 2 [Y: 512 ~ 920]: 浅灰平滑清水混凝土 (Architectural Concrete)
    # -------------------------------------------------------------
    y_start, y_end = 512, 920
    noise = rng.normal(0, 4.0, (y_end - y_start, SIZE, 3))
    base_color = np.array([195, 200, 206], dtype=np.float32)
    concrete_rgb = np.clip(base_color + noise, 170, 228).astype(np.uint8)
    
    concrete_img = Image.fromarray(concrete_rgb, "RGB")
    cdraw = ImageDraw.Draw(concrete_img)
    
    seam_color = (130, 135, 142)
    seam_highlight = (240, 245, 250)
    
    mid_y = (y_end - y_start) // 2
    cdraw.line([0, mid_y, SIZE, mid_y], fill=seam_color, width=3)
    cdraw.line([0, mid_y + 3, SIZE, mid_y + 3], fill=seam_highlight, width=1)
    
    for sx in range(0, SIZE, 512):
        cdraw.line([sx, 0, sx, y_end - y_start], fill=seam_color, width=3)
        cdraw.line([sx + 3, 0, sx + 3, y_end - y_start], fill=seam_highlight, width=1)
        for py in [mid_y // 2, mid_y + mid_y // 2]:
            for px in [sx + 64, sx + 512 - 64]:
                if px < SIZE:
                    cdraw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(130, 135, 142), outline=(100, 105, 112))
                    cdraw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(70, 75, 80))
                    height_map[y_start + py - 8 : y_start + py + 8, px - 8 : px + 8] = 0.2
                    
    albedo.paste(concrete_img, (0, y_start))
    height_map[y_start:y_end, :] = np.clip(height_map[y_start:y_end, :] + 0.6, 0.0, 1.0)
    roughness[y_start:y_end, :] = 160

    # -------------------------------------------------------------
    # Strip 3 [Y: 920 ~ 1330]: 深灰/青色日式屋顶瓦片 (Kawara Roof Tiles)
    # -------------------------------------------------------------
    y_start, y_end = 920, 1330
    draw.rectangle([0, y_start, SIZE, y_end], fill=(30, 36, 44))
    
    course_h = 36
    kawara_w = 48
    for row_idx, y in enumerate(range(y_start, y_end, course_h)):
        if y + course_h > y_end:
            break
        draw.line([0, y, SIZE, y], fill=(70, 85, 102), width=3)
        draw.line([0, y + course_h - 2, SIZE, y + course_h - 2], fill=(12, 15, 20), width=4)
        
        offset = (kawara_w // 2) if (row_idx % 2 == 1) else 0
        for x in range(-offset, SIZE + kawara_w, kawara_w):
            kx1 = max(0, x)
            kx2 = min(SIZE, x + kawara_w)
            if kx2 > kx1:
                draw.line([kx1, y, kx1, y + course_h], fill=(16, 20, 26), width=3)
                for wx in range(kx1, kx2):
                    norm_x = (wx - x) / kawara_w
                    scallop = math.sin(norm_x * math.pi)
                    height_map[y : y + course_h, wx] = 0.3 + 0.6 * scallop
        
        height_map[y + course_h - 4 : y + course_h, :] = 0.15
        roughness[y_start:y_end, :] = 120

    # -------------------------------------------------------------
    # Strip 4 [Y: 1330 ~ 1600]: 铝合金窗框与天空反射玻璃 (Aluminum Window Frame & Glass)
    # -------------------------------------------------------------
    y_start, y_end = 1330, 1600
    draw.rectangle([0, y_start, SIZE, y_end], fill=(28, 30, 34))
    
    bay_w = 512
    for b in range(4):
        bx = b * bay_w
        # frame border
        draw.rectangle([bx + 12, y_start + 12, bx + bay_w - 12, y_end - 12], fill=(20, 22, 25), outline=(60, 65, 72), width=2)
        # Glass
        gx1, gy1 = bx + 24, y_start + 24
        gx2, gy2 = bx + bay_w - 24, y_end - 24
        for gy in range(gy1, gy2):
            t = (gy - gy1) / max(1, (gy2 - gy1))
            gr = int(140 - t * 75)
            gg = int(185 - t * 70)
            gb = int(225 - t * 60)
            draw.line([gx1, gy, gx2, gy], fill=(gr, gg, gb), width=1)
            
        # Interior mullion bar
        mx = (gx1 + gx2) // 2
        draw.line([mx - 4, gy1, mx - 4, gy2], fill=(22, 24, 27), width=8)
        draw.line([gx1, (gy1 + gy2) // 2, gx2, (gy1 + gy2) // 2], fill=(22, 24, 27), width=6)
        
        height_map[gy1:gy2, gx1:gx2] = 0.5
        roughness[gy1:gy2, gx1:gx2] = 20

    # -------------------------------------------------------------
    # Strip 5 [Y: 1600 ~ 1840]: 二楼不锈钢拉丝护栏与金属格栅 (Balcony Railing)
    # -------------------------------------------------------------
    y_start, y_end = 1600, 1840
    draw.rectangle([0, y_start, SIZE, y_end], fill=(185, 192, 200))
    # Top handrail
    draw.rectangle([0, y_start + 8, SIZE, y_start + 38], fill=(240, 245, 250))
    draw.line([0, y_start + 8, SIZE, y_start + 8], fill=(255, 255, 255), width=3)
    draw.line([0, y_start + 38, SIZE, y_start + 38], fill=(120, 128, 138), width=3)
    
    # Bottom rail
    draw.rectangle([0, y_end - 42, SIZE, y_end - 18], fill=(215, 222, 230))
    
    for vx in range(0, SIZE, 48):
        draw.rectangle([vx + 16, y_start + 38, vx + 32, y_end - 42], fill=(230, 235, 242))
        draw.line([vx + 16, y_start + 38, vx + 16, y_end - 42], fill=(255, 255, 255), width=2)
        draw.line([vx + 32, y_start + 38, vx + 32, y_end - 42], fill=(130, 138, 148), width=2)
        height_map[y_start+38:y_end-42, vx+16:vx+32] = 0.95
        roughness[y_start+38:y_end-42, vx+16:vx+32] = 45

    # -------------------------------------------------------------
    # Strip 6 [Y: 1840 ~ 2048]: 深灰水泥踢脚线与勒脚基座 (Base Trim)
    # -------------------------------------------------------------
    y_start, y_end = 1840, 2048
    draw.rectangle([0, y_start, SIZE, y_end], fill=(75, 80, 88))
    draw.line([0, y_start, SIZE, y_start], fill=(145, 152, 162), width=4)
    draw.line([0, y_start + 14, SIZE, y_start + 14], fill=(45, 48, 54), width=3)
    
    for ej in range(0, SIZE, 256):
        draw.line([ej, y_start, ej, y_end], fill=(35, 38, 44), width=5)
        draw.line([ej + 5, y_start, ej + 5, y_end], fill=(120, 126, 136), width=2)
        
    height_map[y_start:y_end, :] = 0.7
    roughness[y_start:y_end, :] = 210

    # Save Albedo
    albedo_path = os.path.join(OUTPUT_DIR, "trim_modern_japan_2k.png")
    albedo.save(albedo_path, quality=95)
    print(f"Saved: {albedo_path}")

    # Normal map
    print("Computing normal map...")
    dy, dx = np.gradient(height_map * 9.0)
    dz = np.ones_like(dx)
    norm = np.sqrt(dx**2 + dy**2 + dz**2)
    nx = (-dx / norm) * 0.5 + 0.5
    ny = (-dy / norm) * 0.5 + 0.5
    nz = (dz / norm) * 0.5 + 0.5
    normal_rgb = np.stack([(nx * 255).astype(np.uint8),
                           (ny * 255).astype(np.uint8),
                           (nz * 255).astype(np.uint8)], axis=-1)
    normal_img = Image.fromarray(normal_rgb, "RGB")
    normal_path = os.path.join(OUTPUT_DIR, "trim_modern_japan_2k_normal.png")
    normal_img.save(normal_path)
    print(f"Saved: {normal_path}")
    
    # Roughness
    roughness_img = Image.fromarray(roughness, "L")
    roughness_path = os.path.join(OUTPUT_DIR, "trim_modern_japan_2k_roughness.png")
    roughness_img.save(roughness_path)
    print(f"Saved: {roughness_path}")

if __name__ == "__main__":
    create_trim_sheet()
