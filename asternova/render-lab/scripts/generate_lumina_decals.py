#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Lumina Plaza Decal and Texture Generator
Generates high-resolution 2D decals and PBR texture maps for Lumina Plaza.
"""

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DECAL_DIR = Path(r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\render-lab\textures\decals")
DECAL_DIR.mkdir(parents=True, exist_ok=True)

def create_bike_lane_decal():
    """Generates the iconic white bicycle road marking decal with wear edges."""
    size = (1024, 1024)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer white oval
    bbox = [140, 60, 884, 964]
    draw.ellipse(bbox, outline=(245, 245, 250, 240), width=28)
    
    # Bike Wheels (two circles)
    wheel_radius = 110
    left_wheel = (330, 640)
    right_wheel = (690, 640)
    
    draw.ellipse([left_wheel[0]-wheel_radius, left_wheel[1]-wheel_radius,
                  left_wheel[0]+wheel_radius, left_wheel[1]+wheel_radius],
                 outline=(245, 245, 250, 245), width=24)
    draw.ellipse([right_wheel[0]-wheel_radius, right_wheel[1]-wheel_radius,
                  right_wheel[0]+wheel_radius, right_wheel[1]+wheel_radius],
                 outline=(245, 245, 250, 245), width=24)
    
    # Frame points
    crank = (490, 640) # Bottom bracket
    seat_joint = (440, 470)
    head_joint = (630, 450)
    handlebar = (660, 360)
    seat = (410, 440)
    
    # Lines for frame
    line_color = (245, 245, 250, 245)
    w = 26
    # Chainstay: crank to left wheel
    draw.line([crank, left_wheel], fill=line_color, width=w)
    # Seatstay: left wheel to seat joint
    draw.line([left_wheel, seat_joint], fill=line_color, width=w)
    # Seat tube: crank to seat joint
    draw.line([crank, seat_joint], fill=line_color, width=w)
    # Down tube: crank to head joint
    draw.line([crank, head_joint], fill=line_color, width=w)
    # Top tube: seat joint to head joint
    draw.line([seat_joint, head_joint], fill=line_color, width=w)
    # Fork: head joint to right wheel
    draw.line([head_joint, right_wheel], fill=line_color, width=w)
    # Stem / handlebar
    draw.line([head_joint, handlebar], fill=line_color, width=w)
    draw.line([(handlebar[0]-50, handlebar[1]), (handlebar[0]+40, handlebar[1]-10)], fill=line_color, width=28)
    # Saddle
    draw.line([(seat[0]-35, seat[1]), (seat[0]+50, seat[1])], fill=line_color, width=32)

    # Slight blur for authentic asphalt spray paint look
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    out_path = DECAL_DIR / "bike_lane_decal.png"
    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

def create_tactile_tiles():
    """Generates Japanese mustard-yellow tactile blister tiles with bump map."""
    size = (1024, 1024)
    albedo = Image.new("RGBA", size, (216, 160, 42, 255)) # Warm mustard yellow #D8A02A
    bump = Image.new("L", size, 128) # Neutral mid-grey
    
    draw_alb = ImageDraw.Draw(albedo)
    draw_bump = ImageDraw.Draw(bump)
    
    # 8x8 grid of blister studs
    grid_n = 8
    step = size[0] // grid_n
    stud_r = 34
    
    for row in range(grid_n):
        for col in range(grid_n):
            cx = int((col + 0.5) * step)
            cy = int((row + 0.5) * step)
            
            # Stud highlight / shading in albedo
            draw_alb.ellipse([cx-stud_r, cy-stud_r, cx+stud_r, cy+stud_r], fill=(235, 185, 60, 255), outline=(180, 130, 25, 255), width=3)
            
            # Dome in bump map (bright white center)
            for r in range(stud_r, 0, -2):
                val = int(128 + 120 * math.cos((stud_r - r) / stud_r * (math.pi / 2)))
                draw_bump.ellipse([cx-r, cy-r, cx+r, cy+r], fill=val)
                
    # Border grout lines
    for i in range(grid_n + 1):
        pos = i * step
        draw_alb.line([(pos, 0), (pos, size[1])], fill=(160, 110, 20, 255), width=4)
        draw_alb.line([(0, pos), (size[0], pos)], fill=(160, 110, 20, 255), width=4)
        draw_bump.line([(pos, 0), (pos, size[1])], fill=60, width=4)
        draw_bump.line([(0, pos), (size[0], pos)], fill=60, width=4)

    bump = bump.filter(ImageFilter.GaussianBlur(1.5))
    albedo_path = DECAL_DIR / "tactile_studs_albedo.png"
    bump_path = DECAL_DIR / "tactile_studs_bump.png"
    albedo.save(albedo_path, "PNG")
    bump.save(bump_path, "PNG")
    print(f"Generated: {albedo_path} & {bump_path}")

def create_manhole_cover():
    """Generates the Lumina Plaza cast iron manhole cover with concentric blue & white graphics."""
    size = (1024, 1024)
    albedo = Image.new("RGBA", size, (28, 30, 34, 255)) # Dark cast iron base
    bump = Image.new("L", size, 128)
    
    draw_alb = ImageDraw.Draw(albedo)
    draw_bump = ImageDraw.Draw(bump)
    
    cx, cy = 512, 512
    outer_r = 480
    
    # Outer rim
    draw_alb.ellipse([cx-outer_r, cy-outer_r, cx+outer_r, cy+outer_r], fill=(36, 40, 46, 255), outline=(15, 17, 20, 255), width=18)
    draw_bump.ellipse([cx-outer_r, cy-outer_r, cx+outer_r, cy+outer_r], outline=240, width=18)
    
    # Concentric rings
    for r in range(430, 100, -45):
        draw_alb.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(22, 24, 28, 255), width=6)
        draw_bump.ellipse([cx-r, cy-r, cx+r, cy+r], outline=70, width=6)
        
    # Blue painted arcs / accents (Urban aesthetic from reference)
    blue_color = (40, 130, 210, 230)
    white_color = (240, 242, 245, 230)
    
    draw_alb.arc([cx-380, cy-380, cx+380, cy+380], start=20, end=160, fill=blue_color, width=28)
    draw_alb.arc([cx-380, cy-380, cx+380, cy+380], start=200, end=340, fill=blue_color, width=28)
    draw_alb.arc([cx-310, cy-310, cx+310, cy+310], start=40, end=140, fill=white_color, width=18)
    draw_alb.arc([cx-310, cy-310, cx+310, cy+310], start=220, end=320, fill=white_color, width=18)
    
    # Diamond / radial traction cleats in bump
    num_teeth = 24
    for i in range(num_teeth):
        angle = i * (2 * math.pi / num_teeth)
        x1 = cx + int(340 * math.cos(angle))
        y1 = cy + int(340 * math.sin(angle))
        x2 = cx + int(420 * math.cos(angle))
        y2 = cy + int(420 * math.sin(angle))
        draw_bump.line([(x1, y1), (x2, y2)], fill=220, width=10)
        draw_alb.line([(x1, y1), (x2, y2)], fill=(45, 48, 55, 255), width=8)
        
    # Center crest
    draw_alb.ellipse([cx-90, cy-90, cx+90, cy+90], fill=(22, 25, 30, 255), outline=(50, 140, 220, 255), width=8)
    draw_bump.ellipse([cx-90, cy-90, cx+90, cy+90], fill=190, outline=250, width=8)

    bump = bump.filter(ImageFilter.GaussianBlur(1.0))
    albedo_path = DECAL_DIR / "manhole_cover_diffuse.png"
    bump_path = DECAL_DIR / "manhole_cover_bump.png"
    albedo.save(albedo_path, "PNG")
    bump.save(bump_path, "PNG")
    print(f"Generated: {albedo_path} & {bump_path}")

def create_hazard_stripes():
    """Generates 45-degree yellow and black industrial hazard warning stripes."""
    w, h = 1024, 256
    img = Image.new("RGBA", (w, h), (242, 175, 12, 255)) # Safety Yellow #F2AF0C
    draw = ImageDraw.Draw(img)
    
    stripe_w = 64
    black_color = (25, 27, 30, 255)
    
    for x in range(-h, w + h, stripe_w * 2):
        pts = [
            (x, 0),
            (x + stripe_w, 0),
            (x + stripe_w + h, h),
            (x + h, h)
        ]
        draw.polygon(pts, fill=black_color)
        
    out_path = DECAL_DIR / "hazard_stripes.png"
    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

def create_art_show_banner():
    """Generates the large vertical skyscraper banner 'ART SHOW 文艺精英'."""
    w, h = 512, 1536
    img = Image.new("RGBA", (w, h), (18, 55, 105, 255)) # Deep Cyan-Blue
    draw = ImageDraw.Draw(img)
    
    # Graphic background elements
    draw.rectangle([20, 20, w-20, h-20], outline=(70, 170, 240, 200), width=6)
    draw.polygon([(40, 100), (w-40, 220), (w-40, 360), (40, 240)], fill=(28, 90, 165, 255))
    
    # Geometric circles
    draw.ellipse([w//2-140, 480, w//2+140, 760], outline=(240, 245, 255, 220), width=8)
    draw.ellipse([w//2-110, 510, w//2+110, 730], fill=(235, 170, 25, 240))
    
    # Text placeholder graphics (clean modern tech glyphs)
    # Header: ART SHOW
    draw.rectangle([w//2-160, 180, w//2+160, 230], fill=(255, 255, 255, 240))
    draw.rectangle([w//2-120, 250, w//2+120, 280], fill=(235, 170, 25, 240))
    
    # Middle banner text blocks
    for y in [840, 920, 1000, 1080]:
        draw.rectangle([70, y, w-70, y+45], fill=(245, 248, 255, 230))
        
    # Lower tech details
    for y in range(1200, 1420, 30):
        draw.line([(60, y), (w-60, y)], fill=(80, 180, 245, 180), width=4)

    out_path = DECAL_DIR / "art_show_banner.png"
    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

def create_ez_studio_sign():
    """Generates the EZ STUDIO backlit shopfront logo."""
    w, h = 1024, 384
    img = Image.new("RGBA", (w, h), (20, 22, 26, 255)) # Dark chassis
    draw = ImageDraw.Draw(img)
    
    # Glowing white borders
    draw.rectangle([12, 12, w-12, h-12], outline=(60, 65, 75, 255), width=6)
    
    # Main bold letters EZ (simulated with clean vector polygons)
    # Letter E
    draw.polygon([(180, 60), (340, 60), (340, 110), (250, 110), (250, 145), (320, 145),
                  (320, 195), (250, 195), (250, 230), (340, 230), (340, 280), (180, 280)],
                 fill=(250, 252, 255, 255))
    
    # Letter Z
    draw.polygon([(380, 60), (550, 60), (550, 110), (455, 230), (550, 230), (550, 280),
                  (380, 280), (380, 230), (475, 110), (380, 110)],
                 fill=(250, 252, 255, 255))
    
    # Word 'STUDIO' underneath in clean bars
    draw.rectangle([180, 305, 550, 335], fill=(240, 245, 255, 230))
    
    # Right side graphic badge / warning icon
    draw.polygon([(700, 80), (840, 80), (880, 140), (880, 260), (840, 310), (700, 310), (660, 260), (660, 140)],
                 fill=(245, 175, 15, 255))
    draw.polygon([(715, 105), (825, 105), (855, 155), (855, 245), (825, 285), (715, 285), (685, 245), (685, 155)],
                 fill=(20, 22, 26, 255))
    draw.rectangle([745, 140, 795, 250], fill=(245, 175, 15, 255))

    out_path = DECAL_DIR / "ez_studio_sign.png"
    img.save(out_path, "PNG")
    print(f"Generated: {out_path}")

if __name__ == "__main__":
    print("=== GENERATING LUMINA PLAZA HIGH-PRECISION DECALS ===")
    create_bike_lane_decal()
    create_tactile_tiles()
    create_manhole_cover()
    create_hazard_stripes()
    create_art_show_banner()
    create_ez_studio_sign()
    print("=== ALL DECALS GENERATED SUCCESSFULLY ===")
