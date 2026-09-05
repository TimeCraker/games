import os
import math
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def height_to_normal(height, strength=2.0):
    """
    Computes tangent space normal map from 2D height array using Sobel filter.
    Returns RGB uint8 image array (X -> R, Y -> G, Z -> B).
    In Blender / OpenGL normal map convention:
    R: -dx (pointing right is positive X, red)
    G: -dy (pointing up is positive Y, green)
    B: dz
    """
    h = height.astype(np.float32)
    pad_h = np.pad(h, pad_width=1, mode='wrap')
    
    dx = (
        (pad_h[0:-2, 2:] + 2.0 * pad_h[1:-1, 2:] + pad_h[2:, 2:]) -
        (pad_h[0:-2, 0:-2] + 2.0 * pad_h[1:-1, 0:-2] + pad_h[2:, 0:-2])
    ) * (strength / 8.0)
    
    dy = (
        (pad_h[0:-2, 0:-2] + 2.0 * pad_h[0:-2, 1:-1] + pad_h[0:-2, 2:]) -
        (pad_h[2:, 0:-2] + 2.0 * pad_h[2:, 1:-1] + pad_h[2:, 2:])
    ) * (strength / 8.0)
    
    dz = np.ones_like(dx)
    
    length = np.sqrt(dx * dx + dy * dy + dz * dz)
    length = np.maximum(length, 1e-6)
    
    nx = -dx / length
    ny = dy / length
    nz = dz / length
    
    r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    
    return np.stack([r, g, b], axis=-1)

def compute_ao(height, radius=8, strength=1.5):
    """
    Computes approximate ambient occlusion from height field.
    """
    h = height.astype(np.float32)
    from PIL import ImageFilter
    im = Image.fromarray((np.clip(h, 0.0, 1.0) * 255.0).astype(np.uint8))
    blur1 = np.array(im.filter(ImageFilter.GaussianBlur(radius=radius))).astype(np.float32) / 255.0
    blur2 = np.array(im.filter(ImageFilter.GaussianBlur(radius=radius * 2.5))).astype(np.float32) / 255.0
    
    diff1 = h - blur1
    diff2 = h - blur2
    
    ao = 1.0 + (diff1 * 0.6 + diff2 * 0.4) * strength
    ao = np.clip(ao, 0.15, 1.0)
    return (ao * 255.0).astype(np.uint8)

def save_texture_set(name, out_dirs, albedo, normal, roughness, ao):
    for d in out_dirs:
        ensure_dir(d)
        Image.fromarray(albedo).save(os.path.join(d, f"{name}_albedo.png"))
        Image.fromarray(normal).save(os.path.join(d, f"{name}_normal.png"))
        Image.fromarray(roughness).save(os.path.join(d, f"{name}_roughness.png"))
        Image.fromarray(ao).save(os.path.join(d, f"{name}_ao.png"))
    print(f"Generated texture set: {name} (2048x2048)")

def generate_wall_plaster(size=2048, out_dirs=None):
    print("Generating wall_plaster...")
    np.random.seed(42)
    im_noise1 = Image.fromarray((np.random.normal(0.5, 0.15, (size, size)) * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)
    from PIL import ImageFilter
    n_fine = np.array(im_noise1.filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255.0
    
    im_macro = Image.fromarray((np.random.normal(0.5, 0.2, (64, 64)) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)
    n_macro = np.array(im_macro.filter(ImageFilter.GaussianBlur(15.0))).astype(np.float32) / 255.0
    
    height = n_fine * 0.6 + n_macro * 0.4
    height = np.clip(height, 0.0, 1.0)
    
    r = np.clip(204 + (n_macro - 0.5) * 14 + (n_fine - 0.5) * 8, 180, 224).astype(np.uint8) # RGB ~ 0.80
    g = np.clip(201 + (n_macro - 0.5) * 14 + (n_fine - 0.5) * 8, 177, 221).astype(np.uint8) # RGB ~ 0.79
    b = np.clip(194 + (n_macro - 0.5) * 14 + (n_fine - 0.5) * 8, 170, 214).astype(np.uint8) # RGB ~ 0.76
    albedo = np.stack([r, g, b], axis=-1)
    
    normal = height_to_normal(height, strength=2.2)
    roughness = np.clip((0.82 + (n_fine - 0.5) * 0.12) * 255.0, 0, 255).astype(np.uint8)
    ao = compute_ao(height, radius=6, strength=1.2)
    
    save_texture_set("wall_plaster", out_dirs, albedo, normal, roughness, ao)

def generate_asphalt_road(size=2048, out_dirs=None):
    print("Generating asphalt_road...")
    np.random.seed(101)
    
    # 1. Crushed aggregate micro-gravel (CS2 style high-frequency stone facets)
    noise_fine = np.random.uniform(0.1, 0.9, (size, size)).astype(np.float32)
    im_fine = Image.fromarray((noise_fine * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    gravel_fine = np.array(im_fine).astype(np.float32) / 255.0
    
    noise_coarse = np.random.uniform(0.2, 0.8, (size // 2, size // 2)).astype(np.float32)
    im_coarse = Image.fromarray((noise_coarse * 255).astype(np.uint8)).resize((size, size), Image.NEAREST).filter(ImageFilter.GaussianBlur(1.2))
    gravel_coarse = np.array(im_coarse).astype(np.float32) / 255.0
    
    gravel_h = gravel_fine * 0.65 + gravel_coarse * 0.35
    
    # Macro undulations
    im_macro = Image.fromarray((np.random.normal(0.5, 0.15, (32, 32)) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)
    macro_h = np.array(im_macro.filter(ImageFilter.GaussianBlur(30.0))).astype(np.float32) / 255.0
    
    height = gravel_h * 0.75 + macro_h * 0.25
    
    # 2. Realistic organic asphalt fracture / crack sealing lines
    # Subtle longitudinal road stress cracks with slight branching
    tar_img = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(tar_img)
    
    # Branching crack 1
    t = np.linspace(0, 1, 120)
    cx1 = (0.32 + 0.03 * np.sin(t * 12.0) + 0.015 * np.cos(t * 31.0)) * size
    cy1 = t * size
    pts1 = list(zip(cx1, cy1))
    draw.line(pts1, fill=255, width=6)
    
    # Branching crack 2
    cx2 = (0.58 + 0.025 * np.cos(t * 9.0) + 0.012 * np.sin(t * 26.0)) * size
    cy2 = t * size
    pts2 = list(zip(cx2, cy2))
    draw.line(pts2, fill=255, width=5)
    
    # Side twigs branching out from main cracks
    np.random.seed(55)
    for _ in range(8):
        idx = np.random.randint(15, 105)
        sx, sy = pts1[idx]
        ex = sx + np.random.uniform(-45, 45)
        ey = sy + np.random.uniform(-35, 35)
        draw.line([(sx, sy), (ex, ey)], fill=255, width=4)
        
    for _ in range(6):
        idx = np.random.randint(15, 105)
        sx, sy = pts2[idx]
        ex = sx + np.random.uniform(-40, 40)
        ey = sy + np.random.uniform(-30, 30)
        draw.line([(sx, sy), (ex, ey)], fill=255, width=4)
        
    tar_mask = np.array(tar_img.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
    
    # 3. White boundary marking line (Japanese road border edge stripe)
    white_line_mask = np.zeros((size, size), dtype=np.float32)
    x_start = int(size * 0.88)
    x_end = int(size * 0.94)
    white_line_mask[:, x_start:x_end] = 1.0
    
    wear_noise = np.random.uniform(0.0, 1.0, (size, size))
    im_wear = Image.fromarray((wear_noise * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.8))
    wear_val = np.array(im_wear).astype(np.float32) / 255.0
    white_line_mask = white_line_mask * np.clip((wear_val - 0.22) * 2.2, 0.0, 1.0)
    
    # Tar seal is physically depressed (0.08凹陷) into asphalt
    height = height - tar_mask * 0.08 + white_line_mask * 0.12
    height = np.clip(height, 0.0, 1.0)
    
    # Neutral warm dark charcoal asphalt (suppressed blue tint)
    base_grey = 42 + (gravel_h - 0.5) * 20
    r_asp = np.clip(base_grey * 1.02, 22, 75)
    g_asp = np.clip(base_grey * 1.00, 22, 75)
    b_asp = np.clip(base_grey * 0.96, 20, 72) # Suppressed blue
    
    tar_color = np.array([18, 18, 19], dtype=np.float32)
    white_color = np.array([215, 216, 210], dtype=np.float32)
    
    albedo = np.stack([r_asp, g_asp, b_asp], axis=-1).astype(np.float32)
    albedo = albedo * (1.0 - tar_mask[:, :, None]) + tar_color * tar_mask[:, :, None]
    albedo = albedo * (1.0 - white_line_mask[:, :, None]) + white_color * white_line_mask[:, :, None]
    albedo = np.clip(albedo, 0, 255).astype(np.uint8)
    
    normal = height_to_normal(height, strength=3.2)
    
    # Roughness: 0.88 for aggregate, 0.55 for weathered tar seal tape
    roughness = (0.88 + (gravel_h - 0.5) * 0.10)
    roughness = roughness * (1.0 - tar_mask) + 0.55 * tar_mask
    roughness = roughness * (1.0 - white_line_mask) + 0.70 * white_line_mask
    roughness = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    
    ao = compute_ao(height, radius=6, strength=1.3)
    
    save_texture_set("asphalt_road", out_dirs, albedo, normal, roughness, ao)

def generate_sidewalk_tiles(size=2048, out_dirs=None):
    print("Generating sidewalk_tiles...")
    np.random.seed(202)
    tile_divs = 4
    tile_size = size // tile_divs
    grout_width = 10
    
    grout_mask = np.zeros((size, size), dtype=np.float32)
    for i in range(tile_divs + 1):
        pos = i * tile_size
        y1, y2 = max(0, pos - grout_width // 2), min(size, pos + grout_width // 2)
        grout_mask[y1:y2, :] = 1.0
        x1, x2 = max(0, pos - grout_width // 2), min(size, pos + grout_width // 2)
        grout_mask[:, x1:x2] = 1.0
        
    grout_mask = np.array(Image.fromarray((grout_mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255.0
    
    tile_tone = np.zeros((size, size), dtype=np.float32)
    for ty in range(tile_divs):
        for tx in range(tile_divs):
            shift = np.random.uniform(-0.08, 0.08)
            y1, y2 = ty * tile_size, (ty + 1) * tile_size
            x1, x2 = tx * tile_size, (tx + 1) * tile_size
            tile_tone[y1:y2, x1:x2] = shift
            
    stone_grain = np.random.normal(0.5, 0.1, (size, size)).astype(np.float32)
    im_stone = Image.fromarray((stone_grain * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    stone_h = np.array(im_stone).astype(np.float32) / 255.0
    
    height = stone_h * 0.8 * (1.0 - grout_mask * 0.7)
    height = np.clip(height, 0.0, 1.0)
    
    base_r = 165 + tile_tone * 50 + (stone_h - 0.5) * 20
    base_g = 167 + tile_tone * 50 + (stone_h - 0.5) * 20
    base_b = 171 + tile_tone * 50 + (stone_h - 0.5) * 20
    
    r = base_r * (1.0 - grout_mask) + 80 * grout_mask
    g = base_g * (1.0 - grout_mask) + 80 * grout_mask
    b = base_b * (1.0 - grout_mask) + 82 * grout_mask
    albedo = np.clip(np.stack([r, g, b], axis=-1), 0, 255).astype(np.uint8)
    
    normal = height_to_normal(height, strength=2.5)
    
    roughness = (0.68 + (stone_h - 0.5) * 0.12) * (1.0 - grout_mask) + 0.92 * grout_mask
    roughness = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    
    ao = compute_ao(height, radius=8, strength=1.5)
    
    save_texture_set("sidewalk_tiles", out_dirs, albedo, normal, roughness, ao)

def generate_tactile_paving(size=2048, out_dirs=None):
    print("Generating tactile_paving...")
    np.random.seed(303)
    half = size // 2
    height = np.zeros((size, size), dtype=np.float32)
    
    rib_pitch = 64
    for x in range(0, half, rib_pitch):
        cx = x + rib_pitch // 2
        for offset in range(-14, 15):
            px = cx + offset
            if 0 <= px < half:
                val = math.cos((offset / 14.0) * (math.pi / 2.0))
                height[:, px] = np.maximum(height[:, px], val * 0.85)
                
    dot_pitch = 64
    for y in range(dot_pitch // 2, size, dot_pitch):
        for x in range(half + dot_pitch // 2, size, dot_pitch):
            rad = 14
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= rad:
                        py = y + dy
                        px = x + dx
                        if 0 <= py < size and half <= px < size:
                            dome = math.cos((dist / rad) * (math.pi / 2.0))
                            height[py, px] = np.maximum(height[py, px], dome * 0.9)
                            
    grit = np.random.normal(0.0, 0.04, (size, size)).astype(np.float32)
    height = np.clip(height + grit, 0.0, 1.0)
    
    base_r = 240 + grit * 40 + height * 12
    base_g = 186 + grit * 40 + height * 10
    base_b = 8 + np.clip(grit * 20, 0, 30)
    
    albedo = np.clip(np.stack([base_r, base_g, base_b], axis=-1), 0, 255).astype(np.uint8)
    normal = height_to_normal(height, strength=3.5)
    
    roughness = 0.55 - height * 0.20 + np.random.normal(0.0, 0.02, (size, size))
    roughness = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    
    ao = compute_ao(height, radius=6, strength=1.6)
    
    save_texture_set("tactile_paving", out_dirs, albedo, normal, roughness, ao)

def generate_concrete_curb(size=2048, out_dirs=None):
    print("Generating concrete_curb...")
    np.random.seed(404)
    height = np.zeros((size, size), dtype=np.float32)
    
    for y in range(size):
        if y < size * 0.35:
            height[y, :] = 0.85
        elif y < size * 0.42:
            t = (y - size * 0.35) / (size * 0.07)
            height[y, :] = 0.85 - t * 0.4
        else:
            height[y, :] = 0.45
            
    joint_width = 8
    for jx in range(0, size, 512):
        x1, x2 = max(0, jx - joint_width // 2), min(size, jx + joint_width // 2)
        height[:, x1:x2] -= 0.35
        
    pore_noise = np.random.normal(0.5, 0.12, (size, size)).astype(np.float32)
    im_pore = Image.fromarray((pore_noise * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    pores = np.array(im_pore).astype(np.float32) / 255.0
    
    height = np.clip(height + (pores - 0.5) * 0.12, 0.0, 1.0)
    
    r = np.clip(148 + (pores - 0.5) * 20, 110, 185)
    g = np.clip(150 + (pores - 0.5) * 20, 112, 187)
    b = np.clip(153 + (pores - 0.5) * 20, 115, 190)
    albedo = np.stack([r, g, b], axis=-1).astype(np.uint8)
    
    normal = height_to_normal(height, strength=2.2)
    roughness = np.clip((0.72 + (pores - 0.5) * 0.15) * 255.0, 0, 255).astype(np.uint8)
    ao = compute_ao(height, radius=8, strength=1.4)
    
    save_texture_set("concrete_curb", out_dirs, albedo, normal, roughness, ao)

def generate_metal_manhole(size=2048, out_dirs=None):
    print("Generating metal_manhole...")
    np.random.seed(505)
    cx, cy = size // 2, size // 2
    r_outer = int(size * 0.46)
    r_rim = int(size * 0.42)
    r_inner = int(size * 0.39)
    
    Y, X = np.ogrid[:size, :size]
    dist_sq = (X - cx)**2 + (Y - cy)**2
    dist = np.sqrt(dist_sq)
    
    height = np.zeros((size, size), dtype=np.float32)
    mask_outer = (dist <= r_outer) & (dist > r_rim)
    height[mask_outer] = 0.5
    
    mask_gap = (dist <= r_rim) & (dist > r_inner)
    height[mask_gap] = 0.2
    
    mask_cover = dist <= r_inner
    height[mask_cover] = 0.55
    
    for r_ring in range(120, r_inner - 40, 90):
        ring_band = np.abs(dist - r_ring) <= 12
        height[mask_cover & ring_band] += 0.25
        
    grid_size = 48
    stud_mask = ((X % grid_size < 16) & (Y % grid_size < 16)) & mask_cover & (dist > 180)
    height[stud_mask] += 0.25
    
    center_circle = dist <= 160
    height[center_circle] = 0.65
    center_ring = np.abs(dist - 140) <= 8
    height[center_ring] += 0.2
    
    hole1 = ((X - (cx - 100))**2 + (Y - cy)**2) <= 24**2
    hole2 = ((X - (cx + 100))**2 + (Y - cy)**2) <= 24**2
    height[hole1 | hole2] = 0.05
    
    cast_grain = np.random.normal(0.5, 0.08, (size, size)).astype(np.float32)
    height = np.clip(height + (cast_grain - 0.5) * 0.08, 0.0, 1.0)
    
    edge_wear = np.clip((height - 0.65) * 2.5, 0.0, 1.0)
    iron_base = 40 + edge_wear * 35 + (cast_grain - 0.5) * 10
    r = np.clip(iron_base * 0.98, 20, 110).astype(np.uint8)
    g = np.clip(iron_base * 1.00, 20, 110).astype(np.uint8)
    b = np.clip(iron_base * 1.02, 20, 110).astype(np.uint8)
    albedo = np.stack([r, g, b], axis=-1)
    
    normal = height_to_normal(height, strength=3.2)
    roughness = 0.55 - edge_wear * 0.25 + (1.0 - height) * 0.20
    roughness = np.clip(roughness * 255.0, 0, 255).astype(np.uint8)
    
    ao = compute_ao(height, radius=9, strength=1.6)
    
    save_texture_set("metal_manhole", out_dirs, albedo, normal, roughness, ao)

def generate_props_ac_meter(size=2048, out_dirs=None):
    print("Generating props_ac_meter...")
    np.random.seed(606)
    height = np.ones((size, size), dtype=np.float32) * 0.5
    half = size // 2
    
    Y, X = np.ogrid[:half, :half]
    fcx, fcy = half // 2, half // 2
    fdist = np.sqrt((X - fcx)**2 + (Y - fcy)**2)
    fan_circle = fdist <= (half * 0.42)
    height[:half, :half][fan_circle] = 0.35
    
    louver_pitch = 18
    louver_mask = (Y % louver_pitch) < 8
    height[:half, :half][fan_circle & louver_mask] = 0.65
    
    foam_wrap = np.random.normal(0.5, 0.15, (half, half)).astype(np.float32)
    im_foam = Image.fromarray((foam_wrap * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.8))
    foam_h = np.array(im_foam).astype(np.float32) / 255.0
    height[half:, :half] = foam_h * 0.7 + 0.2
    
    height[half:, half:] = 0.5
    win_y1, win_y2 = half + int(half * 0.2), half + int(half * 0.65)
    win_x1, win_x2 = half + int(half * 0.2), half + int(half * 0.8)
    height[win_y1:win_y2, win_x1:win_x2] = 0.25
    
    normal = height_to_normal(height, strength=2.6)
    
    albedo = np.zeros((size, size, 3), dtype=np.uint8)
    albedo[:half, :] = [220, 222, 225]
    albedo[:half, :half][fan_circle] = [50, 52, 55]
    albedo[:half, :half][fan_circle & louver_mask] = [180, 182, 185]
    
    r_f = np.clip(215 + (foam_h - 0.5) * 30, 180, 240).astype(np.uint8)
    g_f = np.clip(204 + (foam_h - 0.5) * 30, 170, 230).astype(np.uint8)
    b_f = np.clip(182 + (foam_h - 0.5) * 30, 150, 210).astype(np.uint8)
    albedo[half:, :half] = np.stack([r_f, g_f, b_f], axis=-1)
    
    albedo[half:, half:] = [190, 192, 195]
    albedo[win_y1:win_y2, win_x1:win_x2] = [240, 242, 238]
    
    roughness = np.zeros((size, size), dtype=np.uint8)
    roughness[:half, :] = 110
    roughness[half:, :half] = 215
    roughness[half:, half:] = 125
    roughness[win_y1:win_y2, win_x1:win_x2] = 25
    
    ao = compute_ao(height, radius=7, strength=1.4)
    
    save_texture_set("props_ac_meter", out_dirs, albedo, normal, roughness, ao)

def generate_utility_pole(size=2048, out_dirs=None):
    print("Generating utility_pole...")
    np.random.seed(707)
    height = np.zeros((size, size), dtype=np.float32)
    
    c_noise = np.random.normal(0.5, 0.1, (size, size)).astype(np.float32)
    im_c = Image.fromarray((c_noise * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    c_h = np.array(im_c).astype(np.float32) / 255.0
    height = c_h * 0.6 + 0.3
    
    cx = size // 2
    seam_mask = np.abs(np.arange(size) - cx) <= 6
    height[:, seam_mask] += 0.25
    
    normal = height_to_normal(height, strength=2.2)
    
    r = np.clip(155 + (c_h - 0.5) * 25, 120, 190).astype(np.uint8)
    g = np.clip(158 + (c_h - 0.5) * 25, 123, 193).astype(np.uint8)
    b = np.clip(160 + (c_h - 0.5) * 25, 125, 195).astype(np.uint8)
    albedo = np.stack([r, g, b], axis=-1)
    
    roughness = np.clip((0.80 + (c_h - 0.5) * 0.15) * 255.0, 0, 255).astype(np.uint8)
    ao = compute_ao(height, radius=8, strength=1.3)
    
    save_texture_set("utility_pole", out_dirs, albedo, normal, roughness, ao)

def main():
    target_dirs = [
        os.path.abspath("asternova/art/textures/golden_slice"),
        os.path.abspath("art/textures/golden_slice")
    ]
    print("Output target directories:", target_dirs)
    
    generate_wall_plaster(2048, target_dirs)
    generate_asphalt_road(2048, target_dirs)
    generate_sidewalk_tiles(2048, target_dirs)
    generate_tactile_paving(2048, target_dirs)
    generate_concrete_curb(2048, target_dirs)
    generate_metal_manhole(2048, target_dirs)
    generate_props_ac_meter(2048, target_dirs)
    generate_utility_pole(2048, target_dirs)
    print("All 8 PBR 2K texture sets successfully generated!")

if __name__ == "__main__":
    main()
