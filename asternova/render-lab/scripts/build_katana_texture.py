"""
Build Katana Texture Atlas for Aster's weapon '星霜月华' (Seisou Gekka)
Compliant with STYLE.md and weapon-turnaround-final.png

Atlas Quadrants (Blender UV Space where (0,0) is bottom-left, (1,1) is top-right):
- Top-Left     (U: 0.0..0.5, V: 0.5..1.0 | PIL Y:    0..1024): Tsuka (Handle Wrap & Diamonds)
- Top-Right    (U: 0.5..1.0, V: 0.5..1.0 | PIL Y:    0..1024): Saya (Ivory Pearl Lacquer & Star Engravings)
- Bottom-Left  (U: 0.0..0.5, V: 0.0..0.5 | PIL Y: 1024..2048): Blade (Steel, Shinogi, Hamon wave line)
- Bottom-Right (U: 0.5..1.0, V: 0.0..0.5 | PIL Y: 1024..2048): Metal Gold, Blue Ribbon, Cyan Gemstones
"""

import math
import os
from PIL import Image, ImageDraw, ImageFilter

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

COLOR_SAYA = hex_to_rgb("E0E0E8")        # Ivory white scabbard
COLOR_RIBBON = hex_to_rgb("AED1FA")      # Light sky blue ribbon
COLOR_GOLD = hex_to_rgb("EBC57A")        # Champagne gold metal
COLOR_GOLD_LIGHT = hex_to_rgb("F7E4B2")  # Light gold highlight
COLOR_GOLD_DARK = hex_to_rgb("C99E4D")   # Deep gold shadow
COLOR_BLADE = hex_to_rgb("E8EEF5")       # Blade silver steel
COLOR_HAMON = hex_to_rgb("C8E2FA")       # Cool light blue hamon edge
COLOR_HAMON_GLOW = hex_to_rgb("92C1F5")  # Hamon deep glow
COLOR_TSUKA_WHITE = hex_to_rgb("F4F5FA") # White handle wrap
COLOR_TSUKA_BLUE = hex_to_rgb("9ABEF0")  # Blue diamond underlay
COLOR_GEM_CORE = hex_to_rgb("5FD2EE")    # Cyan gem core
COLOR_GEM_DEEP = hex_to_rgb("223E75")    # Deep sapphire rim

def create_texture():
    w, h = 2048, 2048
    img = Image.new("RGBA", (w, h), (224, 224, 232, 255))
    draw = ImageDraw.Draw(img)

    # =========================================================================
    # 1. TSUKA QUADRANT (PIL X: 0..1024, Y: 0..1024 | UV U: 0.0..0.5, V: 0.5..1.0)
    # =========================================================================
    draw.rectangle([0, 0, 1024, 1024], fill=COLOR_TSUKA_WHITE)
    
    # Draw 10 repeating diamond rows (柄卷菱形目贯)
    rows = 10
    row_h = 1024 / rows
    dw = 100
    dh = 45

    for cx in [256, 768]:
        for r in range(rows):
            cy = int((r + 0.5) * row_h)
            pts = [
                (cx, cy - dh),
                (cx + dw, cy),
                (cx, cy + dh),
                (cx - dw, cy)
            ]
            draw.polygon(pts, fill=COLOR_TSUKA_BLUE)
            
            # Center gold star in diamond
            star = [
                (cx, cy - 22), (cx + 7, cy - 7),
                (cx + 22, cy), (cx + 7, cy + 7),
                (cx, cy + 22), (cx - 7, cy + 7),
                (cx - 22, cy), (cx - 7, cy - 7)
            ]
            draw.polygon(star, fill=COLOR_GOLD)
            draw.line(pts + [pts[0]], fill=(170, 185, 210, 255), width=4)

    # Diagonal wrap cords
    for r in range(rows + 1):
        y = int(r * row_h)
        draw.line([(0, y), (1024, y)], fill=(205, 210, 225, 255), width=4)
        draw.line([(0, y + int(row_h/2)), (1024, y + int(row_h/2))], fill=(228, 232, 242, 255), width=2)

    # =========================================================================
    # 2. SAYA SCABBARD QUADRANT (PIL X: 1024..2048, Y: 0..1024 | UV U: 0.5..1.0, V: 0.5..1.0)
    # =========================================================================
    draw.rectangle([1024, 0, 2048, 1024], fill=COLOR_SAYA)
    
    # Pearl sheen subtle modulation
    for x in range(1024, 2048):
        factor = 0.5 + 0.5 * math.cos((x - 1536) / 512.0 * math.pi)
        cr = int(COLOR_SAYA[0] + 6 * factor)
        cg = int(COLOR_SAYA[1] + 7 * factor)
        cb = int(COLOR_SAYA[2] + 14 * factor)
        draw.line([(x, 0), (x, 1024)], fill=(min(255, cr), min(255, cg), min(255, cb), 255), width=1)

    # Golden filigree star engravings (细节刻纹)
    def draw_scabbard_star(cx, cy, scale=1.0):
        # 4 pointed elongated star
        star_pts = []
        for i in range(8):
            ang = i * math.pi / 4
            rad = (70 * scale) if (i % 2 == 0) else (18 * scale)
            if i % 4 == 0:
                rad = 130 * scale
            star_pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        draw.polygon(star_pts, fill=COLOR_GOLD)
        # Inner cyan core
        inner = [(cx, cy - 25*scale), (cx + 12*scale, cy), (cx, cy + 25*scale), (cx - 12*scale, cy)]
        draw.polygon(inner, fill=COLOR_GEM_CORE)
        # Delicate filigree circle
        draw.arc([cx - 100*scale, cy - 50*scale, cx + 100*scale, cy + 50*scale],
                 0, 360, fill=COLOR_GOLD, width=3)

    draw_scabbard_star(1350, 512, scale=0.85)
    draw_scabbard_star(1750, 512, scale=1.15)

    # =========================================================================
    # 3. BLADE QUADRANT (PIL X: 0..1024, Y: 1024..2048 | UV U: 0.0..0.5, V: 0.0..0.5)
    # =========================================================================
    draw.rectangle([0, 1024, 1024, 2048], fill=COLOR_BLADE)
    
    # X direction: 0 = spine (mune), 512 = ridge (shinogi), 1024 = edge (ha)
    for x in range(0, 1024):
        t = x / 1024.0
        if t < 0.45:
            # Hira flat spine
            val = int(220 + 25 * t)
            col = (val, val + 5, val + 12, 255)
        elif t < 0.52:
            # Shinogi bright reflection line
            col = (252, 254, 255, 255)
        else:
            # Blade bevel with luminous cool blue Hamon line
            edge_t = (t - 0.52) / 0.48
            wave = 0.03 * math.sin(edge_t * 16.0 * math.pi)
            if edge_t > 0.65 + wave:
                col = (COLOR_HAMON[0], COLOR_HAMON[1], COLOR_HAMON[2], 255)
            elif edge_t > 0.50 + wave:
                col = (COLOR_HAMON_GLOW[0], COLOR_HAMON_GLOW[1], COLOR_HAMON_GLOW[2], 255)
            else:
                val = int(235 + 15 * edge_t)
                col = (val, val + 4, val + 10, 255)
        draw.line([(x, 1024), (x, 2048)], fill=col, width=1)

    # =========================================================================
    # 4. FITTINGS & RIBBONS (PIL X: 1024..2048, Y: 1024..2048 | UV U: 0.5..1.0, V: 0.0..0.5)
    # =========================================================================
    # 4a. Champagne Gold (PIL X: 1024..1536, Y: 1024..1536 | U: 0.50..0.75, V: 0.25..0.50)
    draw.rectangle([1024, 1024, 1536, 1536], fill=COLOR_GOLD)
    for y in range(1024, 1536, 64):
        draw.line([(1024, y), (1536, y)], fill=COLOR_GOLD_LIGHT, width=4)
        draw.line([(1024, y + 32), (1536, y + 32)], fill=COLOR_GOLD_DARK, width=3)

    # 4b. Light Blue Ribbon (PIL X: 1536..2048, Y: 1024..1536 | U: 0.75..1.00, V: 0.25..0.50)
    draw.rectangle([1536, 1024, 2048, 1536], fill=COLOR_RIBBON)
    # Ribbon edges and soft cloth texture
    draw.line([(1536, 1034), (2048, 1034)], fill=(225, 242, 255, 255), width=6)
    draw.line([(1536, 1526), (2048, 1526)], fill=(140, 175, 225, 255), width=6)

    # 4c. Deep Gold / Metal Accents (PIL X: 1024..1536, Y: 1536..2048 | U: 0.50..0.75, V: 0.00..0.25)
    draw.rectangle([1024, 1536, 1536, 2048], fill=COLOR_GOLD_DARK)
    for x in range(1024, 1536, 32):
        draw.line([(x, 1536), (x, 2048)], fill=COLOR_GOLD, width=3)

    # 4d. Cyan Water Gemstones (PIL X: 1536..2048, Y: 1536..2048 | U: 0.75..1.00, V: 0.00..0.25)
    draw.rectangle([1536, 1536, 2048, 2048], fill=COLOR_GEM_DEEP)
    gx, gy = 1792, 1792
    r_out = 160
    draw.polygon([
        (gx, gy - r_out), (gx + r_out, gy),
        (gx, gy + r_out), (gx - r_out, gy)
    ], fill=COLOR_GEM_CORE)
    r_in = 85
    draw.polygon([
        (gx, gy - r_in), (gx + r_in, gy),
        (gx, gy + r_in), (gx - r_in, gy)
    ], fill=(190, 245, 255, 255))
    # Sparkle star
    draw.polygon([
        (gx - 25, gy - 25), (gx + 5, gy - 40),
        (gx + 25, gy - 25), (gx - 5, gy - 10)
    ], fill=(255, 255, 255, 255))

    return img

if __name__ == "__main__":
    out_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\weapons\aster_katana\textures"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "tex_katana_basecolor.png")
    
    tex = create_texture()
    tex.save(out_path)
    print(f"Texture atlas successfully updated at: {out_path}")
