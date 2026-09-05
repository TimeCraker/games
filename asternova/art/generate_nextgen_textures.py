import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TEXTURES_DIR = os.path.abspath("asternova/client-godot-v2/textures")
TEXTURES_DIR2 = os.path.abspath("asternova/art/textures")
TEXTURES_DIR3 = os.path.abspath("render-lab/textures")

for d in [TEXTURES_DIR, TEXTURES_DIR2, TEXTURES_DIR3]:
    os.makedirs(d, exist_ok=True)

def save_texture_all(name, img):
    for d in [TEXTURES_DIR, TEXTURES_DIR2, TEXTURES_DIR3]:
        p = os.path.join(d, name)
        img.save(p, quality=95)
    print(f"Saved texture: {name} (Size: {img.size})")

jp_font_path = "C:/Windows/Fonts/msgothic.ttc"
def get_font(size):
    if os.path.exists(jp_font_path):
        try:
            return ImageFont.truetype(jp_font_path, size)
        except:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

def get_bold_font(size):
    # msgothic usually has single weight, but we can pass index or fallback
    if os.path.exists(jp_font_path):
        try:
            return ImageFont.truetype(jp_font_path, size)
        except:
            pass
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        return get_font(size)

print("--- Regenerating Next-Gen Photorealistic PBR Textures with Japanese Fonts ---")

# ==============================================================================
# 1. VENDING MACHINE ATLAS (2048 x 2048)
# ==============================================================================
W, H = 2048, 2048
vm_diff = Image.new("RGBA", (W, H), (230, 232, 235, 255))
vm_emis = Image.new("RGBA", (W, H), (0, 0, 0, 255))
vm_rough = Image.new("L", (W, H), 90)
vm_norm = Image.new("RGBA", (W, H), (128, 128, 255, 255))

d_diff = ImageDraw.Draw(vm_diff)
d_emis = ImageDraw.Draw(vm_emis)
d_rough = ImageDraw.Draw(vm_rough)
d_norm = ImageDraw.Draw(vm_norm)

# Header
header_box = (40, 20, 984, 240)
d_diff.rectangle(header_box, fill=(20, 24, 30, 255), outline=(60, 65, 75, 255), width=6)
d_diff.rectangle((50, 30, 974, 230), fill=(245, 248, 255, 255))
d_emis.rectangle((50, 30, 974, 230), fill=(255, 250, 235, 240))
d_rough.rectangle((50, 30, 974, 230), fill=20)

f_header = get_bold_font(64)
f_sub = get_bold_font(30)
d_diff.text((90, 55), "COLD & HOT DRINKS", fill=(15, 30, 140, 255), font=f_header)
d_diff.text((220, 140), "自動販売機 / 24H REFRESHMENT", fill=(180, 20, 20, 255), font=f_sub)
d_emis.text((90, 55), "COLD & HOT DRINKS", fill=(100, 150, 255, 255), font=f_header)

# Drinks Window
win_box = (30, 260, 994, 1150)
d_diff.rectangle(win_box, fill=(18, 22, 28, 255), outline=(40, 45, 52, 255), width=8)
d_diff.rectangle((45, 275, 979, 1135), fill=(228, 232, 238, 255))
d_rough.rectangle((45, 275, 979, 1135), fill=12)

for gy in range(290, 1100, 40):
    d_diff.line([(55, gy), (969, gy)], fill=(210, 215, 222, 255), width=1)
d_emis.rectangle((50, 280, 974, 1130), fill=(60, 65, 75, 120))

drink_colors = [
    ("BOSS COFFEE", (25, 25, 28), (212, 175, 55), "HOT", 140),
    ("POCARI SWEAT", (0, 105, 185), (255, 255, 255), "COLD", 160),
    ("綾鷹 緑茶", (45, 125, 50), (230, 245, 220), "COLD", 140),
    ("COLA CLASSIC", (190, 15, 20), (255, 255, 255), "COLD", 150),
    ("コーンポタージュ", (220, 160, 30), (255, 245, 200), "HOT", 140),
    ("MILK TEA", (140, 40, 45), (245, 225, 180), "HOT", 150),
    ("ENERGY SPARK", (210, 80, 10), (255, 240, 50), "COLD", 200),
    ("天然水 WATER", (70, 165, 225), (255, 255, 255), "COLD", 120),
]

for row_idx, start_y in enumerate([320, 700]):
    for col_idx in range(8):
        name, main_c, acc_c, temp_type, price = drink_colors[(row_idx * 4 + col_idx) % len(drink_colors)]
        cx = 75 + col_idx * 114
        cy = start_y
        
        can_box = (cx, cy, cx + 82, cy + 230)
        d_diff.rectangle(can_box, fill=main_c, outline=(180, 185, 195, 255), width=2)
        d_diff.rectangle((cx + 6, cy - 8, cx + 76, cy), fill=(210, 215, 220, 255), outline=(150, 155, 160, 255), width=2)
        d_diff.rectangle((cx + 6, cy + 230, cx + 76, cy + 238), fill=(210, 215, 220, 255), outline=(150, 155, 160, 255), width=2)
        d_diff.rectangle((cx + 4, cy + 60, cx + 78, cy + 170), fill=acc_c)
        f_can = get_bold_font(13)
        words = name.split()
        for wi, w in enumerate(words):
            d_diff.text((cx + 8, cy + 70 + wi * 20), w, fill=(10, 10, 10, 255), font=f_can)
            
        d_rough.rectangle(can_box, fill=45)
        d_rough.rectangle((cx + 6, cy - 8, cx + 76, cy), fill=25)
        
        btn_box = (cx + 4, cy + 252, cx + 78, cy + 295)
        is_hot = (temp_type == "HOT")
        btn_c = (210, 30, 25, 255) if is_hot else (20, 110, 225, 255)
        btn_txt = "あたたかい" if is_hot else "つめたい"
        
        d_diff.rectangle(btn_box, fill=btn_c, outline=(240, 240, 240, 255), width=2)
        d_diff.text((cx + 8, cy + 262), btn_txt, fill=(255, 255, 255, 255), font=get_font(12))
        d_rough.rectangle(btn_box, fill=25)
        
        glow_c = (255, 60, 50, 255) if is_hot else (40, 160, 255, 255)
        d_emis.rectangle(btn_box, fill=glow_c)
        d_emis.text((cx + 8, cy + 262), btn_txt, fill=(255, 255, 255, 255), font=get_font(12))
        
        d_diff.rectangle((cx + 10, cy + 300, cx + 72, cy + 322), fill=(245, 245, 245, 255), outline=(40, 40, 40, 255), width=1)
        f_price = get_bold_font(14)
        d_diff.text((cx + 14, cy + 303), f"¥{price}", fill=(10, 10, 10, 255), font=f_price)
        d_emis.text((cx + 14, cy + 303), f"¥{price}", fill=(200, 200, 200, 255), font=f_price)
        
        d_norm.rectangle(btn_box, fill=(138, 142, 255, 255))

# Console
d_diff.rectangle((40, 1160, 984, 1500), fill=(35, 38, 44, 255), outline=(55, 60, 68, 255), width=4)
d_rough.rectangle((40, 1160, 984, 1500), fill=110)

# LED
d_diff.rectangle((100, 1185, 280, 1255), fill=(10, 12, 15, 255), outline=(70, 75, 85, 255), width=2)
f_led = get_bold_font(38)
d_diff.text((115, 1195), "¥ 000", fill=(30, 220, 50, 255), font=f_led)
d_emis.text((115, 1195), "¥ 000", fill=(40, 255, 60, 255), font=f_led)

# Coin slot
d_diff.rectangle((340, 1185, 450, 1255), fill=(200, 205, 210, 255), outline=(70, 75, 80, 255), width=2)
d_diff.rectangle((390, 1195, 400, 1245), fill=(15, 15, 18, 255))
d_rough.rectangle((340, 1185, 450, 1255), fill=35)
d_norm.rectangle((388, 1195, 402, 1245), fill=(110, 110, 240, 255))
d_diff.text((348, 1238), "10 50 100 500", fill=(30, 30, 30, 255), font=get_font(12))

# Bill slot
d_diff.rectangle((510, 1195, 710, 1245), fill=(18, 20, 24, 255), outline=(100, 105, 115, 255), width=2)
d_diff.rectangle((530, 1215, 690, 1225), fill=(5, 5, 8, 255))
d_diff.text((545, 1198), "千円札挿入口", fill=(200, 205, 215, 255), font=get_font(13))
d_diff.ellipse((730, 1210, 746, 1226), fill=(40, 220, 50, 255))
d_emis.ellipse((730, 1210, 746, 1226), fill=(50, 255, 60, 255))

# IC Card Touch Pad
ic_box = (350, 1285, 650, 1465)
d_diff.rectangle(ic_box, fill=(15, 25, 45, 255), outline=(0, 160, 230, 255), width=4)
d_diff.text((375, 1305), "交通系電子マネー / IC", fill=(220, 240, 255, 255), font=get_bold_font(18))
d_diff.ellipse((460, 1345, 540, 1425), fill=(0, 110, 180, 255), outline=(100, 200, 255, 255), width=3)
d_diff.text((475, 1365), "IC", fill=(255, 255, 255, 255), font=get_bold_font(32))
d_emis.rectangle(ic_box, fill=(0, 60, 120, 80))
d_emis.ellipse((460, 1345, 540, 1425), fill=(20, 160, 255, 200))
d_rough.rectangle(ic_box, fill=30)

# Lever
d_diff.ellipse((140, 1320, 240, 1420), fill=(180, 185, 192, 255), outline=(70, 75, 80, 255), width=3)
d_diff.line([(190, 1370), (220, 1340)], fill=(30, 30, 35, 255), width=6)
d_diff.text((150, 1430), "返却・釣銭", fill=(200, 200, 200, 255), font=get_font(13))
d_rough.rectangle((140, 1320, 240, 1420), fill=35)

# Flap
flap_box = (60, 1540, 964, 1980)
d_diff.rectangle(flap_box, fill=(28, 30, 34, 255), outline=(60, 65, 72, 255), width=6)
d_diff.rectangle((100, 1570, 924, 1950), fill=(120, 125, 132, 255), outline=(80, 85, 90, 255), width=4)
d_rough.rectangle((100, 1570, 924, 1950), fill=50)

d_diff.rectangle((140, 1640, 884, 1720), fill=(40, 42, 48, 255), outline=(20, 20, 22, 255), width=2)
f_push = get_bold_font(36)
d_diff.text((420, 1655), "PUSH", fill=(240, 242, 245, 255), font=f_push)
d_diff.text((375, 1780), "商品取り出し口", fill=(210, 215, 220, 255), font=get_bold_font(30))
d_diff.text((330, 1840), "⚠ お取り忘れにご注意ください", fill=(240, 200, 20, 255), font=get_font(22))
d_norm.rectangle((100, 1570, 924, 1950), fill=(118, 122, 245, 255))

# Side
d_diff.rectangle((1040, 40, 2008, 2008), fill=(220, 222, 226, 255))
d_rough.rectangle((1040, 40, 2008, 2008), fill=85)

for vy in range(200, 900, 28):
    d_diff.rectangle((1120, vy, 1920, vy + 12), fill=(140, 142, 148, 255), outline=(100, 102, 108, 255), width=1)
    d_norm.rectangle((1120, vy, 1920, vy + 12), fill=(128, 180, 230, 255))
    d_rough.rectangle((1120, vy, 1920, vy + 12), fill=120)

plate_box = (1180, 1080, 1860, 1600)
d_diff.rectangle(plate_box, fill=(245, 245, 240, 255), outline=(150, 150, 145, 255), width=2)
d_rough.rectangle(plate_box, fill=130)
d_diff.rectangle((1200, 1100, 1840, 1160), fill=(210, 30, 20, 255))
d_diff.text((1350, 1115), "⚠ 感電注意 / WARNING", fill=(255, 255, 255, 255), font=get_bold_font(26))
f_plate = get_font(22)
d_diff.text((1220, 1190), "型式: VM-2400-JP 次世代省エネ仕様", fill=(30, 30, 30, 255), font=f_plate)
d_diff.text((1220, 1240), "定格電圧: AC 100V 50/60Hz | 冷媒: R1234yf", fill=(30, 30, 30, 255), font=f_plate)
d_diff.text((1220, 1290), "製造者: 株式会社 アステノバ自動販売機", fill=(30, 30, 30, 255), font=f_plate)
d_diff.text((1220, 1340), "故障・つり銭等のお問い合わせ: 0120-888-777", fill=(30, 30, 30, 255), font=f_plate)
d_diff.text((1220, 1390), "管理番号: ASTR-TOKYO-0742 | 設置年月: 2026.04", fill=(30, 30, 30, 255), font=f_plate)

d_diff.rectangle((1200, 1850, 1480, 1950), fill=(30, 32, 35, 255), outline=(60, 65, 70, 255), width=4)
d_diff.rectangle((1560, 1850, 1840, 1950), fill=(30, 32, 35, 255), outline=(60, 65, 70, 255), width=4)

save_texture_all("vending_machine_2k_diffuse.png", vm_diff)
save_texture_all("vending_machine_2k_emissive.png", vm_emis)
save_texture_all("vending_machine_2k_roughness.png", vm_rough)
save_texture_all("vending_machine_2k_normal.png", vm_norm)

# ==============================================================================
# 2. CONVENIENCE STORE SIGNBOARD (2048 x 512)
# ==============================================================================
SW, SH = 2048, 512
cs_diff = Image.new("RGBA", (SW, SH), (248, 248, 250, 255))
cs_emis = Image.new("RGBA", (SW, SH), (0, 0, 0, 255))
cs_rough = Image.new("L", (SW, SH), 30)
d_cs = ImageDraw.Draw(cs_diff)
d_ce = ImageDraw.Draw(cs_emis)

d_cs.rectangle((0, 0, SW, SH), fill=(245, 246, 248, 255), outline=(45, 48, 55, 255), width=12)
d_cs.rectangle((16, 16, SW-16, 80), fill=(245, 120, 15, 255))
d_cs.rectangle((16, 80, SW-16, 120), fill=(20, 165, 80, 255))
d_cs.rectangle((16, SH-60, SW-16, SH-16), fill=(0, 90, 170, 255))
d_cs.rectangle((16, 120, SW-16, SH-60), fill=(255, 255, 255, 255))
d_ce.rectangle((16, 16, SW-16, SH-16), fill=(255, 250, 240, 220))

f_store_main = get_bold_font(120)
f_store_jp = get_bold_font(42)

d_cs.text((100, 145), "DAILY MART", fill=(20, 140, 60, 255), font=f_store_main)
d_cs.text((1060, 150), "サンシャインマート 24H", fill=(225, 40, 20, 255), font=f_store_jp)
d_cs.text((1060, 225), "コンビニエンスストア / 銀行ATM / 酒・たばこ / 免税 TAX FREE", fill=(50, 55, 65, 255), font=get_font(26))

d_ce.text((100, 145), "DAILY MART", fill=(100, 255, 140, 255), font=f_store_main)
d_ce.text((1060, 150), "サンシャインマート 24H", fill=(255, 100, 80, 255), font=f_store_jp)

d_cs.rectangle((1820, 140, 2000, 230), fill=(220, 25, 20, 255), outline=(255, 255, 255, 255), width=3)
d_cs.text((1845, 155), "24H", fill=(255, 255, 255, 255), font=get_bold_font(38))
d_ce.rectangle((1820, 140, 2000, 230), fill=(255, 60, 50, 255))

save_texture_all("convenience_store_sign_2k.png", cs_diff)
save_texture_all("convenience_store_sign_emissive.png", cs_emis)

# ==============================================================================
# 3. MUNICIPAL TRASH BINS ATLAS (1024 x 1024)
# ==============================================================================
TW, TH = 1024, 1024
bin_img = Image.new("RGBA", (TW, TH), (235, 238, 242, 255))
d_bin = ImageDraw.Draw(bin_img)
f_b = get_bold_font(34)
f_sub_b = get_font(20)

d_bin.rectangle((40, 40, 480, 300), fill=(25, 95, 185, 255), outline=(255, 255, 255, 255), width=4)
d_bin.text((70, 70), "もえるゴミ", fill=(255, 255, 255, 255), font=f_b)
d_bin.text((70, 130), "BURNABLE / 紙・生ゴミ", fill=(230, 240, 255, 255), font=f_sub_b)

d_bin.rectangle((520, 40, 960, 300), fill=(35, 140, 65, 255), outline=(255, 255, 255, 255), width=4)
d_bin.text((550, 70), "プラスチック", fill=(255, 255, 255, 255), font=f_b)
d_bin.text((550, 130), "PLASTIC RECYCLABLE / 包装", fill=(230, 255, 235, 255), font=f_sub_b)

d_bin.rectangle((40, 340, 480, 600), fill=(70, 75, 85, 255), outline=(255, 255, 255, 255), width=4)
d_bin.text((70, 370), "カン・ビン・ペット", fill=(255, 255, 255, 255), font=f_b)
d_bin.text((70, 430), "CANS & PET BOTTLES", fill=(255, 255, 255, 255), font=f_sub_b)

d_bin.rectangle((40, 660, 960, 960), fill=(245, 245, 248, 255))
for py in range(660, 960, 16):
    d_bin.line([(40, py), (960, py)], fill=(210, 212, 218, 255), width=2)
d_bin.text((100, 780), "CONE REFLECTIVE MICRO-PRISM TAPE", fill=(140, 145, 155, 255), font=get_bold_font(28))

save_texture_all("municipal_props_atlas_2k.png", bin_img)
print("Updated all textures with perfect typography!")
