import os
import math
import numpy as np
from PIL import Image, ImageFilter

hina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\textures\hina_hair_texture.png'
out_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\textures\aster_hair_texture.png'

hina_img = Image.open(hina_path).convert('RGB')
arr = np.array(hina_img, dtype=float)
h, w, _ = arr.shape

mask = (arr.sum(axis=2) > 25)
is_clip = mask & (arr[:,:,0] > 180) & (arr[:,:,1] > 140) & (arr[:,:,2] < 120)
is_hair = mask & ~is_clip

# Calculate normalized luminance for hair: 0 to 1
lum = (0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2])
norm_lum = np.clip((lum - 20.0) / (238.0 - 20.0), 0.0, 1.0)

# Apply contrast curve: preserve delicate strand brush strokes and enhance deep shadows
# S-curve expansion
s_lum = np.where(norm_lum < 0.5, 2.0 * norm_lum * norm_lum, 1.0 - 2.0 * (1.0 - norm_lum) ** 2)
t_lum = 0.30 * norm_lum + 0.70 * s_lum

# Palette control points for Aster's hair
# Exactly sampled from turnaround-final.png:
# Deepest crease: [100, 110, 150] (#646E96)
# Cool inner shadow: [142, 154, 192] (#8E9AC0)
# Periwinkle midtone: [186, 198, 230] (#BAC6E6)
# Celestial silver-lilac body: [222, 228, 244] (#DEE4F4)
# Bright hair surface: [242, 245, 252] (#F2F5FC)
# Crisp starlight highlight: [255, 255, 255] (#FFFFFF)

c_crevice = np.array([100.0, 110.0, 150.0])
c_shadow  = np.array([142.0, 154.0, 192.0])
c_mid     = np.array([186.0, 198.0, 230.0])
c_body    = np.array([222.0, 228.0, 244.0])
c_bright  = np.array([242.0, 245.0, 252.0])
c_white   = np.array([255.0, 255.0, 255.0])

out_arr = np.zeros_like(arr)
t = t_lum[:, :, np.newaxis]

f0 = np.clip(t / 0.22, 0.0, 1.0)
col0 = c_crevice * (1.0 - f0) + c_shadow * f0

f1 = np.clip((t - 0.22) / 0.25, 0.0, 1.0)
col1 = c_shadow * (1.0 - f1) + c_mid * f1

f2 = np.clip((t - 0.47) / 0.28, 0.0, 1.0)
col2 = c_mid * (1.0 - f2) + c_body * f2

f3 = np.clip((t - 0.75) / 0.15, 0.0, 1.0)
col3 = c_body * (1.0 - f3) + c_bright * f3

f4 = np.clip((t - 0.90) / 0.10, 0.0, 1.0)
col4 = c_bright * (1.0 - f4) + c_white * f4

hair_color = np.where(t < 0.22, col0,
             np.where(t < 0.47, col1,
             np.where(t < 0.75, col2,
             np.where(t < 0.90, col3, col4))))

hair_color = np.clip(hair_color, 0, 255)
out_arr[is_hair] = hair_color[is_hair]

# For clips: soft baby blue & pearl
clip_lum = lum[is_clip] / 255.0
clip_r = np.clip(165 + 75 * clip_lum, 0, 255)
clip_g = np.clip(195 + 50 * clip_lum, 0, 255)
clip_b = np.clip(238 + 17 * clip_lum, 0, 255)
out_arr[is_clip, 0] = clip_r
out_arr[is_clip, 1] = clip_g
out_arr[is_clip, 2] = clip_b

result_img = Image.fromarray(out_arr.astype(np.uint8))
result_img.save(out_path)
print('Successfully generated natural flowing aster_hair_texture.png')
