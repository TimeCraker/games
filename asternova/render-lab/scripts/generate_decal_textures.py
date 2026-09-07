# AsterNova - Procedural decal texture generator (PIL + numpy).
# 建筑外立面二阶微表面 Decal 贴花贴图组 (克制、清爽, 严禁脏乱):
#   concrete_seam_grid  预制混凝土拼缝网格 (1024px = 4m x 4m, 缝槽 + AO + 面板色差)
#   hazard_stripes      工业黄黑斜纹防撞贴花 (边缘磨损, 哑光)
#   rain_streaks        墙根/檐下雨水风化水渍 (低透明度垂直冲刷痕)
# 产出: albedo(RGBA) + ORM(R=AO,G=rough,B=metal) + seam 法线
# Run: python scripts/generate_decal_textures.py
import os
import random

import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "models", "environment", "decals")
RNG = random.Random(20260907)


def save(arr, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    Image.fromarray(arr).save(path)
    print("[decal] %s %s" % (name, arr.shape))


def seam_grid(n=1024, cells=4):
    """拼缝网格: 缝槽凹线 + 缝侧 AO + 面板色差; 返回 albedo/normal/orm."""
    lum = np.zeros((n, n), np.float32)          # albedo 亮度场
    groove = np.zeros((n, n), np.float32)       # 缝槽遮罩
    height = np.full((n, n), 0.5, np.float32)   # 法线源高度场
    ao = np.zeros((n, n), np.float32)
    for i in range(cells + 1):
        p = int(round(i * n / cells))
        p = min(p, n - 1)
        for s in (-1, 0, 1):
            col = np.clip(p + s, 0, n - 1)
            groove[:, col] = np.maximum(groove[:, col], 1.0 if s == 0 else 0.5)
            ao[:, col] = np.maximum(ao[:, col], 0.42 if s == 0 else 0.22)
            height[:, col] = np.minimum(height[:, col], 0.30 if s == 0 else 0.42)
            row = np.clip(p + s, 0, n - 1)
            groove[row, :] = np.maximum(groove[row, :], 1.0 if s == 0 else 0.5)
            ao[row, :] = np.maximum(ao[row, :], 0.42 if s == 0 else 0.22)
            height[row, :] = np.minimum(height[row, :], 0.30 if s == 0 else 0.42)
    # 缝槽软边 (1px 高斯近似)
    for a in (groove, ao):
        a[:] = (np.roll(a, 1, 0) + a + np.roll(a, -1, 0)) / 3
        a[:] = (np.roll(a, 1, 1) + a + np.roll(a, -1, 1)) / 3
    # 面板逐格色差 (预制件安装色斑, ±6%) + 低频云斑
    base = 0.60   # 混凝土灰
    tint = np.zeros((n, n), np.float32)
    for ci in range(cells):
        for cj in range(cells):
            x0, x1 = int(ci * n / cells), int((ci + 1) * n / cells)
            y0, y1 = int(cj * n / cells), int((cj + 1) * n / cells)
            tint[y0:y1, x0:x1] = RNG.uniform(-0.06, 0.06)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    cloud = (np.sin(xx * 0.011 + 1.7) * np.sin(yy * 0.009 + 0.4)
             + np.sin(xx * 0.023) * 0.5) * 0.016
    lum = base + tint + cloud
    # 缝槽压暗 (凹槽积垢) + 缝侧 AO 压暗
    lum -= groove * 0.45
    lum -= ao * 0.16
    # 雨水轻微冲刷: 缝下方微亮垂痕 (钙质析出, 极淡)
    for i in range(cells + 1):
        p = int(round(i * n / cells))
        for k in range(40):
            cx = p + RNG.randint(-int(n / cells / 2), int(n / cells / 2))
            ln = RNG.randint(60, 260)
            w = RNG.randint(2, 5)
            x0 = min(max(cx, 0), n - 1)
            y0 = min(max(p, 0), n - ln)
            lum[y0:y0 + ln, x0:x0 + w] += RNG.uniform(0.02, 0.05)
    lum = np.clip(lum, 0, 1)
    # albedo RGBA: alpha = max(缝槽, AO*0.7)
    albedo = np.zeros((n, n, 4), np.uint8)
    albedo[..., 0] = np.clip(lum * 255, 0, 255)
    albedo[..., 1] = np.clip(lum * 253, 0, 255)
    albedo[..., 2] = np.clip(lum * 248, 0, 255)
    albedo[..., 3] = np.clip(np.maximum(groove, ao * 0.7) * 255, 0, 255)
    # 法线: 高度场 sobel
    gy, gx = np.gradient(height)
    nz = np.ones((n, n), np.float32)
    normal = np.zeros((n, n, 4), np.uint8)
    normal[..., 0] = np.clip((-gx * 900 + 128), 0, 255)   # 反算强度略压
    normal[..., 1] = np.clip((gy * 900 + 128), 0, 255)
    normal[..., 2] = np.clip(nz * 255, 0, 255)
    normal[..., 3] = 255
    # ORM: R=AO, G=rough(缝粗糙度更高), B=metal 0
    orm = np.zeros((n, n, 4), np.uint8)
    orm[..., 0] = np.clip((1.0 - ao) * 255, 0, 255)
    orm[..., 1] = np.clip((0.62 + ao * 0.25) * 255, 0, 255)
    orm[..., 2] = 0
    orm[..., 3] = 255
    return albedo, normal, orm


def hazard_stripes(n=1024):
    """黄黑 45 度斜纹, 6+6 带, 边缘磨损 + 哑光颗粒."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    stripe = ((xx + yy) / (n / 6.0)) % 2.0          # 6 周期
    band = np.clip((0.5 - np.abs(stripe - 1.0)) * n / 6.0 / 128.0, 0, 1)
    band = np.where(stripe < 1.0, band, 0.0)        # 黄带区
    is_yellow = stripe < 1.0
    # 底色: 黑带 #2A2A2E / 黄带 #D9A827 (禁纯黑)
    col = np.zeros((n, n, 3), np.float32)
    col[..., 0] = np.where(is_yellow, 0.85, 0.165)
    col[..., 1] = np.where(is_yellow, 0.66, 0.165)
    col[..., 2] = np.where(is_yellow, 0.15, 0.18)
    # 带内颗粒磨损 (哑光褪色) + 边缘 alpha 侵蚀
    grain = np.array([[RNG.uniform(-0.04, 0.04) for _ in range(n)] for _ in range(1)])
    grain = np.repeat(grain, n, 0)
    speck = (np.random.default_rng(7).random((n, n)) > 0.995).astype(np.float32) * -0.25
    col = np.clip(col + grain[..., None] + speck[..., None], 0, 1)
    # 斜纹边界羽化
    edge = np.abs(stripe - np.round(stripe))
    soft = np.clip(edge * (n / 6.0) / 10.0, 0, 1)
    alpha = np.where(is_yellow, soft, soft * 0.92)
    # 外缘整体不规则磨损
    wear = np.random.default_rng(9).random((n, n))
    alpha = np.where(wear > 0.985, alpha * 0.35, alpha)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = (col * 255).astype(np.uint8)
    out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    orm = np.zeros((n, n, 4), np.uint8)
    orm[..., 0] = 235
    orm[..., 1] = 168          # 哑光漆 rough ~0.66
    orm[..., 2] = 0
    orm[..., 3] = 255
    return out, orm


def rain_streaks(n=1024, count=13):
    """垂直雨水冲刷痕: 顶部起头随机长度, 低 alpha 收尾渐隐 + 底部潮气带."""
    albedo = np.zeros((n, n, 4), np.float32)
    for _ in range(count):
        cx = RNG.randint(40, n - 40)
        ln = RNG.randint(int(n * 0.45), int(n * 0.95))
        w = RNG.randint(18, 52)
        x0 = min(max(cx - w // 2, 0), n - w)
        strength = RNG.uniform(0.35, 1.0)
        # 中轴亮 (冲刷洁净痕) + 边缘极淡泥痕
        prof = np.exp(-0.5 * ((np.arange(w) - w / 2) / (w / 4.5)) ** 2)
        fall = np.linspace(1.0, 0.05, ln) ** 0.8
        mask = prof[None, :] * fall[:, None]
        # 抖动的侧向支痕
        jitter = np.cumsum(np.random.default_rng(RNG.randint(0, 1 << 30)).normal(
            0, 0.35, ln)).astype(np.float32)
        xs = np.arange(x0, x0 + w)[None, :] + jitter[:, None].astype(int) * 0
        for i in range(ln):
            y = i
            row = xs[i]
            row = np.clip(row, 0, n - 1)
            albedo[y, row, 0] = np.maximum(
                albedo[y, row, 0], mask[i, :] * strength)
            albedo[y, row, 1] = np.maximum(
                albedo[y, row, 1], mask[i, :] * strength * 0.95)
            albedo[y, row, 2] = np.maximum(
                albedo[y, row, 2], mask[i, :] * strength * 0.9)
            albedo[y, row, 3] = np.maximum(
                albedo[y, row, 3], mask[i, :] * 0.34 * strength)
    # 底部水平潮气带 (贴地湿痕, 极淡)
    band_h = int(n * 0.07)
    for i in range(band_h):
        a = (1 - i / band_h) * 0.10
        albedo[n - 1 - i, :, 3] = np.maximum(albedo[n - 1 - i, :, 3], a)
        albedo[n - 1 - i, :, 0] = np.maximum(albedo[n - 1 - i, :, 0], 0.35)
        albedo[n - 1 - i, :, 1] = np.maximum(albedo[n - 1 - i, :, 1], 0.36)
        albedo[n - 1 - i, :, 2] = np.maximum(albedo[n - 1 - i, :, 2], 0.38)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = np.clip(albedo[..., :3] * 255, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(albedo[..., 3] * 255, 0, 255).astype(np.uint8)
    # albedo 用淡灰 (叠加在墙上呈水洗痕)
    out[..., 0] = np.where(out[..., 3] > 0, np.clip(
        150 + out[..., 0].astype(int) // 4, 0, 255).astype(np.uint8), 0)
    out[..., 1] = np.where(out[..., 3] > 0, np.clip(
        155 + out[..., 1].astype(int) // 4, 0, 255).astype(np.uint8), 0)
    out[..., 2] = np.where(out[..., 3] > 0, np.clip(
        162 + out[..., 2].astype(int) // 4, 0, 255).astype(np.uint8), 0)
    orm = np.zeros((n, n, 4), np.uint8)
    orm[..., 0] = 240
    orm[..., 1] = 150
    orm[..., 2] = 0
    orm[..., 3] = 255
    return out, orm


def main():
    a, nrm, orm = seam_grid()
    save(a, "concrete_seam_grid_albedo.png")
    save(nrm, "concrete_seam_grid_normal.png")
    save(orm, "concrete_seam_grid_orm.png")
    a, orm = hazard_stripes()
    save(a, "hazard_stripes_albedo.png")
    save(orm, "hazard_stripes_orm.png")
    a, orm = rain_streaks()
    save(a, "rain_streaks_albedo.png")
    save(orm, "rain_streaks_orm.png")


if __name__ == "__main__":
    main()
