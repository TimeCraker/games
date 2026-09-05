import os
import sys
import json
import time
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

DEST_DIR = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\nextgen_pbr"
os.makedirs(DEST_DIR, exist_ok=True)

ASSETS = [
    'asphalt_02',
    'precast_stone_paving',
    'rectangular_facade_tiles',
    'grey_roof_tiles',
    'grey_plaster_02',
    'brick_wall_001',
    'concrete_wall_001'
]

def download_polyhaven():
    print("=== Fetching PolyHaven Asset URLs ===")
    for asset in ASSETS:
        try:
            req = urllib.request.Request(f'https://api.polyhaven.com/files/{asset}', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
            for target_name, candidates in [
                ('diffuse', ['Diffuse', 'diffuse']),
                ('normal', ['nor_gl', 'nor_dx']),
                ('roughness', ['Rough', 'rough']),
                ('ao', ['AO', 'ao'])
            ]:
                out_path = os.path.join(DEST_DIR, f"{asset}_{target_name}.jpg")
                if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
                    print(f"  Already exists: {os.path.basename(out_path)}")
                    continue
                    
                map_url = None
                for c in candidates:
                    if c in data:
                        for res in ['2k', '1k']:
                            if res in data[c]:
                                for fmt in ['jpg', 'png']:
                                    if fmt in data[c][res]:
                                        map_url = data[c][res][fmt]['url']
                                        break
                                if map_url: break
                    if map_url: break
                    
                if map_url:
                    print(f"  Downloading {asset}_{target_name} from {map_url[:60]}...")
                    urllib.request.urlretrieve(map_url, out_path)
                else:
                    print(f"  Warning: Map {target_name} not found for {asset}")
        except Exception as e:
            print(f"  Error processing {asset}: {e}")

def create_road_asphalt_with_markings():
    """将扫描的 asphalt_02 贴图与日式道路标线（斑马线、中央虚线、停止线、菱形减速标线）合成"""
    print("=== Generating Japanese Asphalt Road Markings Texture ===")
    asphalt_diff_path = os.path.join(DEST_DIR, "asphalt_02_diffuse.jpg")
    asphalt_norm_path = os.path.join(DEST_DIR, "asphalt_02_normal.jpg")
    asphalt_rgh_path = os.path.join(DEST_DIR, "asphalt_02_roughness.jpg")
    
    if not os.path.exists(asphalt_diff_path):
        print("Error: asphalt_02_diffuse.jpg not found!")
        return
        
    base_img = Image.open(asphalt_diff_path).convert("RGBA").resize((2048, 2048), Image.Resampling.LANCZOS)
    mark_layer = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    draw = ImageDraw.Draw(mark_layer)
    
    W, H = 2048, 2048
    line_white = (235, 238, 240, 215)
    
    # 1. 左右边缘实线
    draw.rectangle([(140, 0), (178, H)], fill=line_white)
    draw.rectangle([(1870, 0), (1908, H)], fill=line_white)
    
    # 2. 中央虚线
    dash_white = (240, 242, 245, 220)
    draw.rectangle([(1010, 80), (1038, 750)], fill=dash_white)
    draw.rectangle([(1010, 1340), (1038, 2010)], fill=dash_white)
    
    # 3. 斑马线 (在 Y: 800 ~ 1300 区域)
    stripe_w = 110
    stripe_gap = 110
    cur_x = 220
    while cur_x + stripe_w <= 1828:
        if not (980 < cur_x < 1060):
            draw.rectangle([(cur_x, 860), (cur_x + stripe_w, 1260)], fill=line_white)
        cur_x += stripe_w + stripe_gap
        
    # 4. 停止线
    draw.rectangle([(220, 1350), (1828, 1410)], fill=line_white)
    
    # 5. 菱形减速预告标线
    def draw_diamond(cx, cy, half_w, half_h):
        pts = [(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)]
        inner_pts = [(cx, cy - half_h + 30), (cx + half_w - 20, cy), (cx, cy + half_h - 30), (cx - half_w + 20, cy)]
        draw.polygon(pts, fill=line_white)
        draw.polygon(inner_pts, fill=(0, 0, 0, 0))
        
    draw_diamond(600, 420, 110, 200)
    draw_diamond(1450, 420, 110, 200)
    
    mark_alpha = mark_layer.split()[3]
    worn_alpha = Image.blend(mark_alpha, Image.eval(mark_alpha, lambda a: int(a * 0.82)), 0.35)
    mark_layer.putalpha(worn_alpha)
    
    final_diff = Image.alpha_composite(base_img, mark_layer).convert("RGB")
    final_diff_path = os.path.join(DEST_DIR, "japanese_asphalt_diffuse.jpg")
    final_diff.save(final_diff_path, quality=95)
    print(f"  Saved {final_diff_path}")
    
    if os.path.exists(asphalt_norm_path):
        base_norm = Image.open(asphalt_norm_path).convert("RGB").resize((2048, 2048), Image.Resampling.LANCZOS)
        norm_np = np.array(base_norm, dtype=np.float32)
        alpha_np = np.array(mark_layer.split()[3], dtype=np.float32) / 255.0
        for c in range(2):
            norm_np[:, :, c] = norm_np[:, :, c] * (1.0 - alpha_np * 0.35) + 128.0 * (alpha_np * 0.35)
        norm_np = np.clip(norm_np, 0, 255).astype(np.uint8)
        final_norm = Image.fromarray(norm_np, mode='RGB')
        final_norm_path = os.path.join(DEST_DIR, "japanese_asphalt_normal.jpg")
        final_norm.save(final_norm_path, quality=95)
        print(f"  Saved {final_norm_path}")
        
    if os.path.exists(asphalt_rgh_path):
        base_rgh = Image.open(asphalt_rgh_path).convert("L").resize((2048, 2048), Image.Resampling.LANCZOS)
        rgh_np = np.array(base_rgh, dtype=np.float32)
        alpha_np = np.array(mark_layer.split()[3], dtype=np.float32) / 255.0
        rgh_np = rgh_np * (1.0 - alpha_np) + 115.0 * alpha_np
        rgh_np = np.clip(rgh_np, 0, 255).astype(np.uint8)
        final_rgh = Image.fromarray(rgh_np, mode='L')
        final_rgh_path = os.path.join(DEST_DIR, "japanese_asphalt_roughness.jpg")
        final_rgh.save(final_rgh_path, quality=95)
        print(f"  Saved {final_rgh_path}")

def create_skyline_facade_textures():
    """生成次世代现代都市高层公寓/写字楼玻璃幕墙与分层立面贴图体系（彻底消灭纯色方块）"""
    print("=== Generating High-Rise Architectural Facade Textures ===")
    W, H = 2048, 2048
    diff = Image.new("RGB", (W, H), (42, 46, 52))
    norm = Image.new("RGB", (W, H), (128, 128, 255))
    rgh = Image.new("L", (W, H), 180)
    emi = Image.new("RGB", (W, H), (0, 0, 0))
    
    draw_d = ImageDraw.Draw(diff)
    draw_n = ImageDraw.Draw(norm)
    draw_r = ImageDraw.Draw(rgh)
    draw_e = ImageDraw.Draw(emi)
    
    floors = 16
    cols = 12
    floor_h = H // floors
    col_w = W // cols
    
    for fl in range(floors):
        y0 = fl * floor_h
        y1 = y0 + floor_h
        
        beam_h = 24
        draw_d.rectangle([(0, y0), (W, y0 + beam_h)], fill=(185, 192, 200))
        draw_r.rectangle([(0, y0), (W, y0 + beam_h)], fill=75)
        
        if fl % 2 == 1:
            draw_d.rectangle([(0, y0 + beam_h), (W, y0 + beam_h + 16)], fill=(80, 85, 92))
            draw_r.rectangle([(0, y0 + beam_h), (W, y0 + beam_h + 16)], fill=200)
            
        for c in range(cols):
            x0 = c * col_w
            x1 = x0 + col_w
            
            mullion_w = 16
            draw_d.rectangle([(x0, y0), (x0 + mullion_w, y1)], fill=(160, 168, 176))
            draw_r.rectangle([(x0, y0), (x0 + mullion_w, y1)], fill=80)
            
            gx0 = x0 + mullion_w + 12
            gy0 = y0 + beam_h + 12
            gx1 = x1 - 12
            gy1 = y1 - 12
            
            if gx1 > gx0 and gy1 > gy0:
                draw_d.rectangle([(gx0, gy0), (gx1, gy1)], fill=(22, 28, 38))
                draw_r.rectangle([(gx0, gy0), (gx1, gy1)], fill=18)
                
                seed = (fl * 37 + c * 19) % 100
                if seed < 28:
                    draw_e.rectangle([(gx0 + 6, gy0 + 6), (gx1 - 6, gy1 - 6)], fill=(255, 215, 140))
                    draw_d.rectangle([(gx0 + 6, gy0 + 6), (gx1 - 6, gy1 - 6)], fill=(120, 105, 80))
                elif seed < 48:
                    draw_e.rectangle([(gx0 + 6, gy0 + 6), (gx1 - 6, gy1 - 6)], fill=(180, 220, 255))
                    draw_d.rectangle([(gx0 + 6, gy0 + 6), (gx1 - 6, gy1 - 6)], fill=(90, 110, 130))
                elif seed < 70:
                    for by in range(gy0 + 6, gy1 - 6, 8):
                        draw_d.line([(gx0 + 6, by), (gx1 - 6, by)], fill=(130, 135, 140), width=3)
                        
    diff_path = os.path.join(DEST_DIR, "skyline_facade_diffuse.jpg")
    norm_path = os.path.join(DEST_DIR, "skyline_facade_normal.jpg")
    rgh_path = os.path.join(DEST_DIR, "skyline_facade_roughness.jpg")
    emi_path = os.path.join(DEST_DIR, "skyline_facade_emissive.jpg")
    
    diff.save(diff_path, quality=95)
    norm.save(norm_path, quality=95)
    rgh.save(rgh_path, quality=95)
    emi.save(emi_path, quality=95)
    print(f"  Saved skyline facade maps: {diff_path}")

def create_convenience_store_posters():
    """生成便利店橱窗促销海报与冷饮冰柜显示贴图"""
    print("=== Generating Convenience Store Poster & Showcase Textures ===")
    W, H = 1024, 1024
    
    poster_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(poster_img)
    
    d.rectangle([(80, 120), (440, 680)], fill=(250, 248, 240, 240), outline=(220, 180, 50), width=6)
    d.rectangle([(80, 120), (440, 240)], fill=(180, 40, 30, 255))
    d.rectangle([(160, 280), (360, 520)], fill=(60, 45, 35, 240))
    
    d.rectangle([(560, 120), (920, 680)], fill=(255, 255, 255, 240), outline=(40, 160, 80), width=6)
    d.rectangle([(560, 120), (920, 240)], fill=(40, 160, 80, 255))
    d.polygon([(740, 320), (640, 480), (840, 480)], fill=(240, 240, 240, 255), outline=(30, 30, 30), width=4)
    d.rectangle([(700, 420), (780, 480)], fill=(20, 20, 20, 255))
    
    poster_path = os.path.join(DEST_DIR, "store_window_posters.png")
    poster_img.save(poster_path)
    print(f"  Saved {poster_path}")
    
    cooler_img = Image.new("RGB", (W, H), (25, 30, 40))
    dc = ImageDraw.Draw(cooler_img)
    col_w = W // 3
    for c in range(3):
        cx0 = c * col_w + 16
        cx1 = (c + 1) * col_w - 16
        dc.rectangle([(cx0, 60), (cx1, H - 60)], fill=(15, 20, 28), outline=(180, 190, 205), width=8)
        dc.rectangle([(cx1 - 25, 350), (cx1 - 12, 650)], fill=(220, 225, 235))
        for shelf in range(1, 5):
            sy = 60 + shelf * ((H - 120) // 5)
            dc.rectangle([(cx0 + 10, sy), (cx1 - 10, sy + 10)], fill=(120, 130, 145))
            for bx in range(cx0 + 15, cx1 - 30, 32):
                color_seed = (c * 17 + shelf * 23 + bx * 7) % 6
                colors = [
                    (220, 40, 40),
                    (40, 140, 220),
                    (40, 190, 80),
                    (240, 180, 30),
                    (240, 240, 245),
                    (130, 70, 180)
                ]
                bot_col = colors[color_seed]
                dc.rectangle([(bx, sy - 65), (bx + 24, sy)], fill=bot_col)
                dc.rectangle([(bx + 4, sy - 78), (bx + 20, sy - 65)], fill=(200, 200, 200))
                
    cooler_path = os.path.join(DEST_DIR, "store_cooler_showcase.jpg")
    cooler_img.save(cooler_path, quality=95)
    print(f"  Saved {cooler_path}")

if __name__ == "__main__":
    download_polyhaven()
    create_road_asphalt_with_markings()
    create_skyline_facade_textures()
    create_convenience_store_posters()
    print("=== All PBR Asset Downloads and Texture Generation Complete ===")
