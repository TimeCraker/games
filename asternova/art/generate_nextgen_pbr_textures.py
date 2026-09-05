import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

OUTPUT_DIRS = [
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\nextgen_pbr",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\models\environment\textures",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\environment\textures"
]

for d in OUTPUT_DIRS:
    ensure_dir(d)

def save_texture(img, name):
    for out_dir in OUTPUT_DIRS:
        target = os.path.join(out_dir, name)
        img.save(target, quality=95)
    print(f"Saved: {name} ({img.size[0]}x{img.size[1]})")

def height_to_normal(height_arr, strength=2.0):
    """通过 Sobel 卷积将单通道高度图转为切线空间标准 Normal Map (RGB: Normal X, Y, Z)"""
    h, w = height_arr.shape
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    
    pad_h = np.pad(height_arr, 1, mode='edge')
    
    dx = np.zeros_like(height_arr, dtype=np.float32)
    dy = np.zeros_like(height_arr, dtype=np.float32)
    
    for i in range(3):
        for j in range(3):
            dx += sobel_x[i, j] * pad_h[i:i+h, j:j+w]
            dy += sobel_y[i, j] * pad_h[i:i+h, j:j+w]
            
    dx *= (strength / 8.0)
    dy *= (strength / 8.0)
    dz = np.ones_like(height_arr, dtype=np.float32)
    
    norm = np.sqrt(dx*dx + dy*dy + dz*dz)
    norm[norm == 0] = 1.0
    
    nx = dx / norm
    ny = dy / norm
    nz = dz / norm
    
    r = ((nx * 0.5 + 0.5) * 255).astype(np.uint8)
    g = ((ny * 0.5 + 0.5) * 255).astype(np.uint8)
    b = ((nz * 0.5 + 0.5) * 255).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1))

# ==============================================================================
# 1. 沥青路面 (CS2 级粗骨料碎石微表面 + 黑色修补灌缝胶 + 车道线)
# ==============================================================================
def create_asphalt_road_textures(size=2048):
    print("Generating Asphalt Road PBR...")
    np.random.seed(42)
    
    base = np.random.normal(155, 6, (size, size)).clip(135, 180).astype(np.float32)
    fine = np.random.normal(0, 8, (size, size)).clip(-15, 15).astype(np.float32)
    coarse_grid = np.random.normal(0, 12, (size // 8, size // 8))
    coarse_img = Image.fromarray(coarse_grid).resize((size, size), Image.Resampling.BICUBIC)
    coarse = np.array(coarse_img)
    
    asphalt_height = (base + fine * 0.6 + coarse * 0.5).clip(0, 255)
    
    albedo_arr = np.zeros((size, size, 3), dtype=np.uint8)
    for c in range(3):
        albedo_arr[:, :, c] = asphalt_height.astype(np.uint8)
    
    albedo_img = Image.fromarray(albedo_arr)
    draw = ImageDraw.Draw(albedo_img)
    
    # 中央虚线车道分割线 (精确居中于 X=1024)
    for sy in range(0, size, 320):
        draw.rectangle([1005, sy, 1045, min(size, sy + 200)], fill=(240, 242, 245))
        
    # 双侧边缘白色实线标线 (Road Shoulder Lines)
    draw.rectangle([80, 0, 110, size], fill=(235, 238, 240))
    draw.rectangle([1938, 0, 1968, size], fill=(235, 238, 240))
        
    # 黑色灌缝修补胶带 (Tar Sealer - CS2 级深黑沥青微表面对比)
    mask_crack = Image.new('L', (size, size), 0)
    draw_crack = ImageDraw.Draw(mask_crack)
    points = []
    y_step = 25
    cur_x = 620
    for y in range(0, size + y_step, y_step):
        cur_x += int(math.sin(y * 0.012) * 22 + math.cos(y * 0.035) * 15)
        points.append((cur_x, y))
    draw_crack.line(points, fill=255, width=16)
    mask_crack = mask_crack.filter(ImageFilter.GaussianBlur(1.5))
    
    m_arr = np.array(mask_crack) / 255.0
    for c in range(3):
        orig = np.array(albedo_img)[:, :, c].astype(np.float32)
        albedo_arr[:, :, c] = (orig * (1.0 - m_arr * 0.75) + 32.0 * (m_arr * 0.75)).astype(np.uint8)
        
    albedo_final = Image.fromarray(albedo_arr)
    save_texture(albedo_final, "asphalt_road_2k_albedo.png")
    
    roughness = np.full((size, size), 170, dtype=np.uint8)
    roughness = (roughness - fine * 0.8).clip(135, 215).astype(np.uint8)
    roughness = (roughness * (1.0 - m_arr) + 35 * m_arr).astype(np.uint8)
    save_texture(Image.fromarray(roughness), "asphalt_road_2k_roughness.png")
    
    h_map = (asphalt_height / 255.0) + (m_arr * 0.25)
    normal_img = height_to_normal(h_map, strength=3.2)
    save_texture(normal_img, "asphalt_road_2k_normal.png")

# ==============================================================================
# 2. 人行道花岗岩地砖 (ZZZ 01/08 级拼缝法线 + 微反光)
# ==============================================================================
def create_sidewalk_tiles_textures(size=2048):
    print("Generating Sidewalk Pavement PBR...")
    np.random.seed(101)
    
    grid_n = 8
    tile_size = size // grid_n
    
    base = np.random.normal(172, 4, (size, size)).clip(150, 195).astype(np.float32)
    fine = np.random.normal(0, 5, (size, size)).clip(-10, 10).astype(np.float32)
    noise = base + fine
    
    height_map = np.full((size, size), 0.8, dtype=np.float32)
    albedo = np.zeros((size, size, 3), dtype=np.float32)
    roughness = np.full((size, size), 180, dtype=np.uint8)
    
    for c in range(3):
        albedo[:, :, c] = noise
        
    grout_width = 6
    for gi in range(grid_n):
        for gj in range(grid_n):
            var = np.random.uniform(0.93, 1.07)
            x0 = gi * tile_size
            x1 = x0 + tile_size
            y0 = gj * tile_size
            y1 = y0 + tile_size
            
            albedo[y0:y1, x0:x1] *= var
            height_map[y0:y1, x0:x1] += np.random.uniform(-0.04, 0.04)
            albedo[y0:y0+grout_width, x0:x1] *= 0.55
            albedo[y1-grout_width:y1, x0:x1] *= 0.55
            albedo[y0:y1, x0:x0+grout_width] *= 0.55
            albedo[y0:y1, x1-grout_width:x1] *= 0.55
            
            height_map[y0:y0+grout_width, x0:x1] -= 0.35
            height_map[y1-grout_width:y1, x0:x1] -= 0.35
            height_map[y0:y1, x0:x0+grout_width] -= 0.35
            height_map[y0:y1, x1-grout_width:x1] -= 0.35
            
            roughness[y0:y0+grout_width, x0:x1] = 235
            roughness[y1-grout_width:y1, x0:x1] = 235
            roughness[y0:y1, x0:x0+grout_width] = 235
            roughness[y0:y1, x1-grout_width:x1] = 235
            
    albedo = albedo.clip(0, 255).astype(np.uint8)
    save_texture(Image.fromarray(albedo), "sidewalk_tiles_2k_albedo.png")
    save_texture(Image.fromarray(roughness), "sidewalk_tiles_2k_roughness.png")
    save_texture(height_to_normal(height_map, strength=3.5), "sidewalk_tiles_2k_normal.png")

# ==============================================================================
# 3. 日式黄色导盲砖 (Tactile Paving Strips & Dots)
# ==============================================================================
def create_tactile_paving_textures(size=2048):
    print("Generating Tactile Paving PBR...")
    img_alb = Image.new("RGB", (size, size), (225, 172, 28))
    draw_alb = ImageDraw.Draw(img_alb)
    
    height_map = np.full((size, size), 0.5, dtype=np.float32)
    roughness = np.full((size, size), 150, dtype=np.uint8)
    
    bar_w = 110
    spacing = 512
    for b in range(4):
        cx = 256 + b * spacing
        x0 = cx - bar_w // 2
        x1 = cx + bar_w // 2
        draw_alb.rectangle([x0, 0, x1, size], fill=(238, 185, 35))
        draw_alb.line([(x0, 0), (x0, size)], fill=(195, 140, 18), width=8)
        draw_alb.line([(x1, 0), (x1, size)], fill=(195, 140, 18), width=8)
        
        for xi in range(x0, x1):
            rel = (xi - x0) / bar_w
            arch = math.sin(rel * math.pi) * 0.45
            height_map[:, xi] += arch
            roughness[:, xi] = int(120 - arch * 50)
            
    save_texture(img_alb, "tactile_paving_2k_albedo.png")
    save_texture(Image.fromarray(roughness), "tactile_paving_2k_roughness.png")
    save_texture(height_to_normal(height_map, strength=4.5), "tactile_paving_2k_normal.png")

# ==============================================================================
# 4. 日式民宅外墙三件套：米白挂板、浅灰细条砖、墨灰和瓦、清水混凝土
# ==============================================================================
def create_japanese_building_materials(size=2048):
    print("Generating Japanese Architecture PBR Materials...")
    np.random.seed(202)
    
    # 4.1 米白横向防雨挂板 (Siding)
    siding_alb = np.random.normal(218, 4, (size, size)).clip(205, 230).astype(np.float32)
    siding_h = np.full((size, size), 0.5, dtype=np.float32)
    siding_rgh = np.full((size, size), 195, dtype=np.uint8)
    
    plank_h = 128
    for py in range(0, size, plank_h):
        siding_alb[py:py+6, :] *= 0.72
        siding_alb[py+6:py+14, :] *= 0.88
        siding_h[py:py+10, :] -= 0.35
        for y in range(py + 10, min(py + plank_h, size)):
            rel = (y - py) / plank_h
            siding_h[y, :] += rel * 0.12
            
    s_alb_rgb = np.stack([siding_alb, siding_alb * 0.98, siding_alb * 0.94], axis=-1).astype(np.uint8)
    save_texture(Image.fromarray(s_alb_rgb), "japanese_siding_2k_albedo.png")
    save_texture(Image.fromarray(siding_rgh), "japanese_siding_2k_roughness.png")
    save_texture(height_to_normal(siding_h, strength=3.0), "japanese_siding_2k_normal.png")
    
    # 4.2 浅灰细长条砖 (Tiles: 48x256)
    tile_h = 48
    tile_w = 256
    brick_alb = np.random.normal(182, 5, (size, size)).clip(165, 200).astype(np.float32)
    brick_h = np.full((size, size), 0.6, dtype=np.float32)
    brick_rgh = np.full((size, size), 185, dtype=np.uint8)
    
    grout = 5
    row = 0
    for y0 in range(0, size, tile_h):
        y1 = min(y0 + tile_h, size)
        offset = (row % 2) * (tile_w // 2)
        row += 1
        brick_alb[y0:y0+grout, :] *= 0.68
        brick_h[y0:y0+grout, :] -= 0.30
        for x0 in range(-tile_w, size + tile_w, tile_w):
            rx0 = max(0, x0 + offset)
            rx1 = min(size, rx0 + grout)
            if rx0 < size:
                brick_alb[y0:y1, rx0:rx1] *= 0.68
                brick_h[y0:y1, rx0:rx1] -= 0.30
                
    b_alb_rgb = np.stack([brick_alb * 1.02, brick_alb, brick_alb * 0.98], axis=-1).astype(np.uint8)
    save_texture(Image.fromarray(b_alb_rgb), "japanese_tile_2k_albedo.png")
    save_texture(Image.fromarray(brick_rgh), "japanese_tile_2k_roughness.png")
    save_texture(height_to_normal(brick_h, strength=3.8), "japanese_tile_2k_normal.png")
    
    # 4.3 日式墨灰色 J 形波纹瓦 (Roof Kawara)
    kawara_alb = np.random.normal(58, 3, (size, size)).clip(48, 68).astype(np.float32)
    kawara_h = np.zeros((size, size), dtype=np.float32)
    kawara_rgh = np.full((size, size), 108, dtype=np.uint8)
    
    wave_period = 128
    for x in range(size):
        phase = (x % wave_period) / wave_period
        arch = math.sin(phase * math.pi * 2.0)
        kawara_h[:, x] = arch * 0.4
        if arch < -0.6:
            kawara_alb[:, x] *= 0.65
            kawara_rgh[:, x] = 160
            
    k_alb_rgb = np.stack([kawara_alb * 0.92, kawara_alb * 0.96, kawara_alb * 1.02], axis=-1).astype(np.uint8)
    save_texture(Image.fromarray(k_alb_rgb), "japanese_roof_kawara_2k_albedo.png")
    save_texture(Image.fromarray(kawara_rgh), "japanese_roof_kawara_2k_roughness.png")
    save_texture(height_to_normal(kawara_h, strength=4.2), "japanese_roof_kawara_2k_normal.png")

    # 4.4 清水混凝土 (Fair-faced Concrete with Cone Holes)
    conc_alb = np.random.normal(168, 5, (size, size)).clip(150, 185).astype(np.float32)
    conc_h = np.full((size, size), 0.5, dtype=np.float32)
    conc_rgh = np.full((size, size), 160, dtype=np.uint8)
    
    # 对拉螺栓孔 (Cone Holes)
    hole_pitch_x = 512
    hole_pitch_y = 512
    for hy in range(256, size, hole_pitch_y):
        for hx in range(256, size, hole_pitch_x):
            for dy in range(-20, 21):
                for dx in range(-20, 21):
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= 20:
                        rel = dist / 20.0
                        conc_h[hy+dy, hx+dx] -= (1.0 - rel) * 0.4
                        conc_alb[hy+dy, hx+dx] *= (0.4 + rel * 0.5)
                        
    c_alb_rgb = np.stack([conc_alb, conc_alb * 1.01, conc_alb * 0.99], axis=-1).astype(np.uint8)
    save_texture(Image.fromarray(c_alb_rgb), "concrete_curb_2k_albedo.png")
    save_texture(Image.fromarray(conc_rgh), "concrete_curb_2k_roughness.png")
    save_texture(height_to_normal(conc_h, strength=3.5), "concrete_curb_2k_normal.png")

# ==============================================================================
# 5. 便利店 24H 真实写实发光招牌与内部写实货架 (彻底消灭七彩马赛克！)
# ==============================================================================
def create_convenience_store_textures(size=2048):
    print("Generating Realistic 24H Convenience Store PBR Materials...")
    
    w_sign, h_sign = 2048, 512
    sign_alb = Image.new("RGB", (w_sign, h_sign), (245, 247, 248))
    sign_draw = ImageDraw.Draw(sign_alb)
    
    sign_draw.rectangle([0, 0, w_sign, 90], fill=(235, 120, 20))
    sign_draw.rectangle([0, 90, w_sign, 160], fill=(20, 165, 95))
    sign_draw.rectangle([0, h_sign - 45, w_sign, h_sign], fill=(15, 90, 180))
    
    font_large = None
    font_sub = None
    for f_path in [
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\msyh.ttc"
    ]:
        if os.path.exists(f_path):
            try:
                font_large = ImageFont.truetype(f_path, 150)
                font_sub = ImageFont.truetype(f_path, 48)
                break
            except:
                pass
                
    if font_large:
        sign_draw.text((120, 190), "DAILY MART", fill=(18, 128, 68), font=font_large)
        sign_draw.text((1180, 210), "サンシャインマート 24H", fill=(210, 45, 25), font=font_sub)
        sign_draw.text((1180, 280), "コンビニ · 銀行ATM · 酒 · たばこ · 免税 TAX FREE", fill=(60, 65, 70), font=font_sub)
    else:
        sign_draw.rectangle([120, 210, 900, 370], fill=(18, 128, 68))
        sign_draw.rectangle([1180, 210, 1850, 300], fill=(210, 45, 25))
        
    save_texture(sign_alb, "convenience_store_sign_2k_albedo.png")
    
    # 写实内透背光灯箱 (根据招牌各品牌色温发光，保持招牌文字高度清晰)
    alb_arr = np.array(sign_alb).astype(np.float32)
    sign_emit_arr = (alb_arr * 0.7).clip(0, 255).astype(np.uint8)
    sign_emit = Image.fromarray(sign_emit_arr).filter(ImageFilter.GaussianBlur(1))
    save_texture(sign_emit, "convenience_store_sign_2k_emissive.png")
    
    # 货架
    sh_w, sh_h = 2048, 1024
    shelf_img = Image.new("RGB", (sh_w, sh_h), (230, 232, 235))
    sh_draw = ImageDraw.Draw(shelf_img)
    
    layers = 4
    l_h = sh_h // layers
    
    item_palettes = [
        [(15, 35, 95), (25, 140, 65), (185, 20, 25), (35, 145, 215), (235, 130, 15), (240, 235, 210), (10, 10, 15)],
        [(180, 110, 40), (85, 175, 110), (95, 60, 35), (220, 240, 250), (45, 105, 195), (245, 245, 245)],
        [(215, 155, 45), (235, 105, 75), (30, 45, 35), (95, 185, 80), (240, 238, 230), (195, 40, 35)],
        [(225, 45, 35), (85, 45, 25), (235, 230, 220), (55, 115, 65), (240, 175, 25), (65, 85, 155)]
    ]
    
    for l in range(layers):
        y_base = (l + 1) * l_h - 20
        sh_draw.rectangle([0, y_base, sh_w, y_base + 12], fill=(140, 145, 150))
        sh_draw.rectangle([0, y_base + 12, sh_w, y_base + 22], fill=(235, 195, 20))
        
        pal = item_palettes[l % len(item_palettes)]
        x_cur = 40
        while x_cur < sh_w - 60:
            item_w = np.random.randint(26, 45)
            item_h = int(l_h * np.random.uniform(0.65, 0.85))
            y_top = y_base - item_h
            
            c_main = pal[np.random.randint(0, len(pal))]
            c_sub = pal[np.random.randint(0, len(pal))]
            
            sh_draw.rectangle([x_cur, y_top, x_cur + item_w, y_base], fill=c_main)
            sh_draw.rectangle([x_cur, y_top, x_cur + item_w, y_top + 10], fill=(225, 225, 230))
            sh_draw.rectangle([x_cur + 4, y_top + 18, x_cur + item_w - 4, y_base - 14], fill=c_sub)
            
            x_cur += item_w + np.random.randint(4, 9)
            
    shelf_img = shelf_img.filter(ImageFilter.GaussianBlur(0.6))
    save_texture(shelf_img, "convenience_store_interior_2k.png")

# ==============================================================================
# 6. 写实双联自动贩卖机 (Realistic Vending Machines)
# ==============================================================================
def create_realistic_vending_machine_textures(size=2048):
    print("Generating Realistic Japanese Dual Vending Machine PBR...")
    
    vm_alb = Image.new("RGB", (size, size), (220, 222, 225))
    draw = ImageDraw.Draw(vm_alb)
    
    h_map = np.full((size, size), 0.5, dtype=np.float32)
    roughness = np.full((size, size), 90, dtype=np.uint8)
    emissive = Image.new("RGB", (size, size), (0, 0, 0))
    emit_draw = ImageDraw.Draw(emissive)
    
    # 蓝机与红机
    draw.rectangle([80, 80, 980, 1960], fill=(22, 85, 175))
    draw.rectangle([1060, 80, 1960, 1960], fill=(185, 30, 28))
    
    for base_x in [80, 1060]:
        win_box = [base_x + 60, 160, base_x + 840, 1050]
        draw.rectangle(win_box, fill=(240, 245, 250))
        emit_draw.rectangle(win_box, fill=(210, 225, 235))
        h_map[160:1050, base_x+60:base_x+840] -= 0.25
        roughness[160:1050, base_x+60:base_x+840] = 15
        
        for row in range(3):
            ry = 220 + row * 280
            draw.line([(base_x + 65, ry + 210), (base_x + 835, ry + 210)], fill=(120, 125, 130), width=6)
            for col in range(7):
                bx = base_x + 85 + col * 105
                b_color = (25, 140, 70) if (col % 2 == 0) else (210, 135, 20)
                draw.rectangle([bx, ry, bx + 70, ry + 190], fill=b_color)
                draw.rectangle([bx + 8, ry + 35, bx + 62, ry + 150], fill=(245, 245, 248))
                
                btn_y = ry + 220
                btn_col = (20, 110, 220) if row < 2 else (220, 45, 30)
                draw.rectangle([bx + 10, btn_y, bx + 60, btn_y + 35], fill=btn_col)
                emit_draw.rectangle([bx + 15, btn_y + 5, bx + 55, btn_y + 30], fill=(180, 220, 255) if row < 2 else (255, 180, 170))
                h_map[btn_y:btn_y+35, bx+10:bx+60] += 0.20
                
        panel_y = 1120
        draw.rectangle([base_x + 100, panel_y, base_x + 800, panel_y + 260], fill=(35, 38, 42))
        draw.rectangle([base_x + 140, panel_y + 40, base_x + 360, panel_y + 110], fill=(15, 25, 18))
        emit_draw.rectangle([base_x + 140, panel_y + 40, base_x + 360, panel_y + 110], fill=(40, 240, 80))
        draw.rectangle([base_x + 450, panel_y + 50, base_x + 580, panel_y + 90], fill=(160, 165, 170))
        draw.ellipse([base_x + 650, panel_y + 40, base_x + 720, panel_y + 110], fill=(140, 145, 150))
        
        push_y = 1450
        push_box = [base_x + 120, push_y, base_x + 780, push_y + 360]
        draw.rectangle(push_box, fill=(45, 48, 52))
        h_map[push_y:push_y+360, base_x+120:base_x+780] -= 0.15
        roughness[push_y:push_y+360, base_x+120:base_x+780] = 160
        
    save_texture(vm_alb, "vending_machine_2k_diffuse.png")
    save_texture(emissive, "vending_machine_2k_emissive.png")
    save_texture(Image.fromarray(roughness), "vending_machine_2k_roughness.png")
    save_texture(height_to_normal(h_map, strength=4.0), "vending_machine_2k_normal.png")

# ==============================================================================
# 7. 日式天际线高层公寓大楼立面 (彻底消除虚空与白石碑)
# ==============================================================================
def create_city_skyline_textures(size=2048):
    print("Generating City Skyline Facade Textures...")
    np.random.seed(303)
    
    b_alb = np.random.normal(190, 4, (size, size)).clip(175, 210).astype(np.float32)
    b_h = np.full((size, size), 0.5, dtype=np.float32)
    b_rgh = np.full((size, size), 180, dtype=np.uint8)
    
    floor_n = 8
    fl_h = size // floor_n
    bay_n = 6
    bay_w = size // bay_n
    
    for fi in range(floor_n):
        y0 = fi * fl_h
        y1 = y0 + fl_h
        b_alb[y0:y0+16, :] *= 0.75
        b_h[y0:y0+16, :] += 0.15
        for bi in range(bay_n):
            x0 = bi * bay_w
            x1 = x0 + bay_w
            by0 = y0 + 32
            by1 = y1 - 20
            bx0 = x0 + 24
            bx1 = x1 - 24
            
            b_alb[by0:by1, bx0:bx1] = 45.0
            b_rgh[by0:by1, bx0:bx1] = 30
            b_h[by0:by1, bx0:bx1] -= 0.35
            
            fence_y0 = by1 - 70
            b_alb[fence_y0:by1, bx0:bx1] = 145.0
            b_h[fence_y0:by1, bx0:bx1] += 0.25
            
            ac_x0 = bx1 - 80
            ac_y0 = fence_y0 - 65
            b_alb[ac_y0:fence_y0, ac_x0:bx1] = 210.0
            b_h[ac_y0:fence_y0, ac_x0:bx1] += 0.30
            b_rgh[ac_y0:fence_y0, ac_x0:bx1] = 110
            
    alb_rgb = np.stack([b_alb, b_alb * 0.98, b_alb * 0.95], axis=-1).astype(np.uint8)
    save_texture(Image.fromarray(alb_rgb), "city_skyline_mansion_2k_albedo.png")
    save_texture(Image.fromarray(b_rgh), "city_skyline_mansion_2k_roughness.png")
    save_texture(height_to_normal(b_h, strength=4.0), "city_skyline_mansion_2k_normal.png")

if __name__ == "__main__":
    create_asphalt_road_textures(2048)
    create_sidewalk_tiles_textures(2048)
    create_tactile_paving_textures(2048)
    create_japanese_building_materials(2048)
    create_convenience_store_textures(2048)
    create_realistic_vending_machine_textures(2048)
    create_city_skyline_textures(2048)
    print("======================================================================")
    print("★ All Next-Gen 2K PBR Textures Created Successfully! ★")
    print("======================================================================")
