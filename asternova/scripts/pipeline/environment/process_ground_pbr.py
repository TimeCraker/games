#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asternova 地面铺装 PBR 管线 (Ground Pavement Pipeline · 第四执行组).

输入 (art/references/ground/):
    raw_ground_tiles_01.png   4x4 商业街地砖顶视概念漫反射
    raw_tactile_yellow_01.png 3x3 黄色盲道砖顶视概念漫反射
    raw_asphalt_stripe_01.png 密实沥青 + 左侧白色车道实线

输出 (render-lab/models/environment/ground/ 与 client-godot-v2/art/textures/ground/):
    ground_tiles_albedo/normal/roughness/ao.png        米白防滑方砖 PBR 套件
    ground_tactile_albedo/normal/roughness.png         暖姜黄盲道砖 PBR 套件
    ground_asphalt_albedo/normal/roughness.png         深灰沥青 PBR 套件
    asphalt_clean_albedo.png / asphalt_white_stripe.png (+ _roughness) 无缝沥青与车道边缘 Trim 条带
    ground_trim_sheet_2k.png                           2048x2048 工业集成条带图

审美处方 (总架构师拍板):
    地砖   bilateral 去水泥噪点, 亮度 +10%, 暖米灰 #E2E0D8~#DDD9D0,
           砖面 rough 0.70 / 缝隙 0.92, Sobel 16-bit OpenGL(+Y 上) 内凹法线
    盲道   饱和度 -28%, 色相微移至日式暖姜黄 #E5B23B, 4 条圆弧倒角凸条,
           凸条 rough 0.50 / 底板 0.68
    沥青   右侧 75% 纯净区四向无缝, 左侧白实线 Trim 条带 (仅纵向无缝, 保住白线),
           沥青 rough 0.82 / 白漆 0.58
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]          # .../asternova
REF_DIR = ROOT / "art" / "references" / "ground"
OUT_DIRS = [
    ROOT / "render-lab" / "models" / "environment" / "ground",
    ROOT / "client-godot-v2" / "art" / "textures" / "ground",
]
QA_DIR = ROOT / "art" / "render_previews" / "environment" / "ground_qa"

OUT_SIZE = 2048            # 2K 主输出
TRIM_SIZE = 2048           # trim sheet 边长
GUTTER = 24                # trim sheet 分隔留白

# ---- 处方目标色 (sRGB 0-255) ----
TILE_WARM_A = np.array([0xE2, 0xE0, 0xD8], dtype=np.float32)     # 亮部暖米灰
TILE_WARM_B = np.array([0xDD, 0xD9, 0xD0], dtype=np.float32)     # 暗部暖米灰
TACTILE_TARGET = np.array([0xE5, 0xB2, 0x3B], dtype=np.float32)  # 日式暖姜黄


# ----------------------------------------------------------------------------- utils
def load(name: str) -> np.ndarray:
    img = cv2.imread(str(REF_DIR / name), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"missing input: {REF_DIR / name}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def to_16bit_normal(height: np.ndarray, strength: float) -> np.ndarray:
    """Sobel 高度场 -> 16-bit 切线空间法线 (OpenGL 绿通道 +V 向上, 凹陷内凹/凸起外翻).

    高度场 H(u,v), v 向上 = 图像 -y:  n ∝ (-dH/du, -dH/dv, 1);
    dH/dv = -dH/dy_img  =>  n = (-dH/dx, +dH/dy, 1) 归一化.
    """
    h = height.astype(np.float32)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3)
    gx /= 8.0          # 3x3 Sobel 核对线性斜坡有 8 倍增益, 归一后 strength = 真实斜率系数
    gy /= 8.0
    nx, ny, nz = -gx * strength, gy * strength, np.ones_like(h)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    normal = np.stack(
        [(nx * 0.5 + 0.5) * 65535.0, (ny * 0.5 + 0.5) * 65535.0, (nz * 0.5 + 0.5) * 65535.0],
        axis=-1,
    )
    return np.clip(normal, 0, 65535).astype(np.uint16)


def micro_noise(shape: tuple[int, int], amplitude: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, 1.0, shape).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 1.2)
    peak = float(np.abs(noise).max()) + 1e-6
    return noise / peak * amplitude


def make_seamless(img: np.ndarray, margin: int, axes: str = "xy") -> np.ndarray:
    """GIMP 式镜像折叠无缝化: 只折一侧边缘, 用对侧边缘的镜像内容交叉淡化.

    折叠后 out[0] == out[h-1] (逐像素相等), 环绕处严格 C0 连续;
    代价是边缘 1/margin 带内容与对侧镜像重复, 对沥青颗粒噪声不可见.
    """
    out = img.astype(np.float32).copy()
    h, w = out.shape[:2]
    if "y" in axes:
        m = min(margin, h // 4)
        t = np.linspace(1.0, 0.0, m, dtype=np.float32)[:, None, None]
        bottom_mirror = out[::-1, :][:m]           # 行 h-1-j (未修改的底部)
        top_orig = out[:m].copy()
        out[:m] = bottom_mirror * t + top_orig * (1.0 - t)
    if "x" in axes:
        m = min(margin, w // 4)
        t = np.linspace(1.0, 0.0, m, dtype=np.float32)[None, :, None]
        right_mirror = out[:, ::-1][:, :m]         # 列 w-1-j (未修改的右侧)
        left_orig = out[:, :m].copy()
        out[:, :m] = right_mirror * t + left_orig * (1.0 - t)
    return np.clip(out, 0, 255).astype(np.uint8)


def seam_test(img: np.ndarray) -> dict[str, float]:
    """2x2 拼接测试: 环绕接缝处的梯度 vs 全图内部梯度中值 (1.0 = 与内部一致)."""
    gray = cv2.cvtColor(np.tile(img, (2, 2, 1)), cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    grad_x = np.abs(np.diff(gray, axis=1))
    grad_y = np.abs(np.diff(gray, axis=0))
    base_x, base_y = float(np.median(grad_x)) + 1e-6, float(np.median(grad_y)) + 1e-6
    return {
        "h_ratio": float(grad_y[cy - 1 : cy + 1, :].mean()) / base_y,
        "v_ratio": float(grad_x[:, cx - 1 : cx + 1].mean()) / base_x,
    }


def save_png(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = img
    if out.ndim == 3 and out.shape[2] == 3:
        out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)      # cv2.imwrite 期望 BGR (16bit 亦然)
    if not cv2.imwrite(str(path), out):
        raise IOError(f"cv2.imwrite failed: {path}")


# ----------------------------------------------------------------------------- 1. 地砖
def process_tiles() -> dict[str, np.ndarray]:
    rgb = load("raw_ground_tiles_01.png")

    # 1) bilateral 去粗水泥噪点, 保留接缝轮廓
    smooth = cv2.bilateralFilter(rgb, 9, 60, 60)

    # 2) 接缝掩膜: 显著暗于大尺度局部基线
    gray = cv2.cvtColor(smooth, cv2.COLOR_RGB2GRAY).astype(np.float32)
    local_base = cv2.medianBlur(gray.astype(np.uint8), 81).astype(np.float32)
    seam = np.clip((local_base - 6.0 - gray) / 10.0, 0.0, 1.0)
    seam = cv2.morphologyEx(seam, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    seam_soft = cv2.GaussianBlur(seam, (0, 0), 2.2)

    # 3) 调色: 亮度 +10%, 以处方米灰为均值锚点重定基 (压对比 -> 动漫干净感, 深度交给 AO/法线)
    bright = smooth.astype(np.float32) * 1.10
    lum = bright.mean(axis=2, keepdims=True) / 255.0
    target_map = TILE_WARM_B[None, None, :] * (1.0 - lum) + TILE_WARM_A[None, None, :] * lum
    ratio = bright / np.maximum(bright.reshape(-1, 3).mean(axis=0)[None, None, :], 1.0)
    ratio = ratio ** 0.72                              # 压缩明暗比, 消除冰冷毛坯感
    graded = np.clip(target_map * ratio, 0.0, 255.0)
    graded *= (1.0 - seam_soft[..., None] * 0.30)      # 砖缝保持阳光下可读的深色
    albedo = np.clip(graded, 0, 255).astype(np.uint8)

    # 4) AO: 砖缝凹槽遮蔽 (缝芯最深, 边缘柔和)
    ao_soft = cv2.GaussianBlur(seam, (0, 0), 5.0)
    ao_img = (np.clip(1.0 - ao_soft * 0.75, 0, 1) * 255.0).astype(np.uint8)

    # 5) 高度场: 接缝下凹 38% + 低幅砖面微起伏 -> Sobel 16-bit 法线
    detail = gray - cv2.GaussianBlur(gray, (0, 0), 6.0)
    height = np.clip(1.0 - seam_soft * 0.38 + detail / 255.0 * 0.05, 0.0, 1.0)
    normal16 = to_16bit_normal(height, strength=3.2)

    # 6) Roughness: 砖面 0.70 / 缝隙 0.92 + 微噪声防死平
    rough = 0.70 + seam_soft * 0.22 + micro_noise(gray.shape, 0.02, 11)
    rough_img = np.clip(rough * 255.0, 0, 255).astype(np.uint8)

    return {"albedo": albedo, "normal16": normal16, "roughness": rough_img, "ao": ao_img}


# ----------------------------------------------------------------------------- 2. 盲道
def _bar_light_runs(cell_gray: np.ndarray) -> list[tuple[int, int]]:
    """单砖内以列暗度包络定位凸条: 15 分位列剖面在「条间暗隙」下陷, 亮段即条内部."""
    prof = np.percentile(cell_gray, 15, axis=0).astype(np.float32)
    prof = cv2.GaussianBlur(prof[None, :], (0, 0), 3.0)[0]
    base = float(np.percentile(prof, 80))
    dark = prof < base - 6.0
    runs: list[tuple[int, int]] = []
    i = 0
    while i < len(dark):
        if dark[i]:
            j = i
            while j < len(dark) and dark[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    light: list[tuple[int, int]] = []
    prev = 0
    for a, b in runs:
        if a - prev > 12:
            light.append((prev, a))
        prev = b
    if len(dark) - prev > 12:
        light.append((prev, len(dark)))
    return light


def _extract_prescribed_tile(rgb: np.ndarray) -> np.ndarray:
    """从照片提取单砖并按处方重排为 4 条凸起.

    源图每砖实为 5 条 (且底缘带下一行切片), 与处方「4 条」不符;
    取最干净首砖的条 1-4 视窗 (条心距 ≈81px), 水平重映射到整砖宽,
    条距/条宽按 4/5 比例放大, 保留摄影级微细节且与高度掩膜严格对齐.
    """
    cell = 418
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    light = _bar_light_runs(g[4:397, 0:401])
    centers = [(a + b) * 0.5 for a, b in light]
    if len(centers) >= 4:
        pitch = float(np.median(np.diff(centers[:5])))
    else:
        centers, pitch = [50.0, 132.5, 213.5, 296.5, 377.5], 81.9
    x0 = max(int(centers[0] - pitch * 0.5), 0)
    x1 = min(int(centers[3] + pitch * 0.5), rgb.shape[1])
    piece = rgb[4:397, x0:x1]
    return cv2.resize(piece, (cell, cell), interpolation=cv2.INTER_CUBIC)


def process_tactile() -> dict[str, np.ndarray]:
    rgb = load("raw_tactile_yellow_01.png")
    cell = 418
    size = cell * 3

    # 1) 单砖提取 + 3x3 光度抖动合成 (每砖 ±2.5% 亮度, 防Perfect Repeat)
    tile = _extract_prescribed_tile(rgb).astype(np.float32)
    rng = np.random.default_rng(7)
    graded_src = np.empty((size, size, 3), np.float32)
    for ty in range(3):
        for tx in range(3):
            gain = 1.0 + float(rng.uniform(-0.025, 0.025))
            graded_src[ty * cell : (ty + 1) * cell, tx * cell : (tx + 1) * cell] = tile * gain
    # 砖间拼装缝压暗 (albedo)
    yy, xx = np.mgrid[0:size, 0:size]
    fx = np.minimum(xx % cell, cell - 1 - xx % cell)
    fy = np.minimum(yy % cell, cell - 1 - yy % cell)
    frame_soft = cv2.GaussianBlur((np.minimum(fx, fy) < 5).astype(np.float32), (0, 0), 1.8)
    graded_src *= (1.0 - frame_soft[..., None] * 0.30)
    graded_src = np.clip(graded_src, 0, 255).astype(np.uint8)

    # 2) HSV 降饱和 28% + 黄域内色相微移至暖姜黄 #E5B23B
    hsv = cv2.cvtColor(graded_src, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] *= 0.72
    tgt_h = float(cv2.cvtColor(TACTILE_TARGET[None, None, :].astype(np.uint8), cv2.COLOR_RGB2HSV)[0, 0, 0])
    yellow = (hsv[..., 0] > 15) & (hsv[..., 0] < 40)
    delta_h = float(tgt_h - hsv[..., 0][yellow].mean()) if bool(yellow.any()) else 0.0
    hsv[..., 0] = np.where(yellow, hsv[..., 0] + np.clip(delta_h, -6.0, 6.0), hsv[..., 0])
    graded = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB)
    mean_rgb = graded.reshape(-1, 3).mean(axis=0)
    graded = np.clip(graded.astype(np.float32)
                     * (TACTILE_TARGET[None, None, :] / np.maximum(mean_rgb[None, None, :], 1.0)),
                     0, 255).astype(np.uint8)

    # 3) 高度掩膜: 依实测条位 (重映射后条心 0.125/0.376/0.622/0.875 砖宽) 生成
    #    凸起白 / 基底灰 / 外框深黑, 距离场圆弧倒角
    centers = [0.125, 0.376, 0.622, 0.875]
    bar_w = int(cell * 0.105)
    height = np.full((size, size), 0.50, np.float32)
    cys = np.arange(size)
    for ty in range(3):
        y0 = ty * cell
        for cx in centers:
            a = int(cx * cell - bar_w / 2)
            b = a + bar_w
            m = int(cell * 0.09)
            for tx in range(3):
                mask = np.zeros((cell, cell), np.uint8)
                mask[m : cell - m, max(a, 0): min(b, cell)] = 255
                dist = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 3)
                # 平台顶 + 两侧圆弧倒角: dist/bevel 在 |x-c| < 半宽-bevel 处饱和为 1 (平顶),
                # 边缘 bevel 带内线性圆滑降落
                bevel = bar_w * 0.22
                dome = np.clip(dist / bevel, 0.0, 1.0)
                region = height[y0 : y0 + cell, tx * cell : (tx + 1) * cell]
                np.maximum(region, 0.50 + dome * 0.40, out=region)
    height = np.clip(height - frame_soft * 0.42, 0.0, 1.0)
    height_img = (height * 255.0).astype(np.uint8)

    # 4) 圆弧倒角凸条法线 (16-bit): 倒角坡 gx≈0.042/px, 强度 9 -> ~0.35 倾角柔和过渡
    normal16 = to_16bit_normal(height, strength=9.0)

    # 5) Albedo: 凸条顶部依高度微提亮 (磨砂微光)
    lift = (height - 0.5)[..., None] * 0.16
    albedo = np.clip(graded.astype(np.float32) * (1.0 + lift), 0, 255).astype(np.uint8)

    # 6) Roughness: 凸条 0.50 / 底板 0.68
    bar_mask = cv2.GaussianBlur(np.clip((height - 0.62) / 0.28, 0, 1), (0, 0), 2.0)
    rough = 0.68 - bar_mask * 0.18 + micro_noise((size, size), 0.018, 23)
    rough_img = np.clip(rough * 255.0, 0, 255).astype(np.uint8)

    print(f"    [tactile] 单砖提取重排 4 条 (条心 {centers}), 3x3 光度抖动合成")
    return {"albedo": albedo, "normal16": normal16, "roughness": rough_img, "height": height_img}


# ----------------------------------------------------------------------------- 3. 沥青
def process_asphalt() -> dict[str, np.ndarray]:
    rgb = load("raw_asphalt_stripe_01.png")
    h, w = rgb.shape[:2]

    # 1) 右侧 75% 纯净沥青 -> 中心方裁 -> 四向镜像折叠无缝
    clean = rgb[:, int(w * 0.25) :, :]
    ch, cw = clean.shape[:2]
    side = min(ch, cw)
    cy0, cx0 = (ch - side) // 2, (cw - side) // 2
    clean = clean[cy0 : cy0 + side, cx0 : cx0 + side]
    clean = make_seamless(clean, side // 6, axes="xy")
    assert (clean[0] == clean[-1]).all() and (clean[:, 0] == clean[:, -1]).all(), \
        "seamless fold failed: wrap edges must match pixelwise"
    # 抑制 1px 摄影颗粒 -> 真机 2K 放大下呈电视雪花噪点; 保 30% 原始颗粒质感
    grain = clean.astype(np.float32)
    soft = cv2.GaussianBlur(grain, (0, 0), 1.1)
    clean = np.clip(soft * 0.70 + grain * 0.30, 0, 255).astype(np.uint8)
    metrics = seam_test(clean)
    print(f"    [asphalt] seamless 2x2 test: h={metrics['h_ratio']:.2f} "
          f"v={metrics['v_ratio']:.2f} (1.0 = 与内部纹理一致)")

    # 2) PBR: 微粒高度 -> 法线, 沥青基底 rough 0.82
    gray = cv2.cvtColor(clean, cv2.COLOR_RGB2GRAY).astype(np.float32)
    normal16 = to_16bit_normal(gray / 255.0, strength=1.6)
    rough_img = np.clip((0.82 + micro_noise(gray.shape, 0.015, 37)) * 255.0, 0, 255).astype(np.uint8)

    # 3) 左侧白实线 Trim 条带: 仅纵向无缝 (U 向折叠会抹掉贴左缘的白线)
    strip = rgb[:, : int(w * 0.25), :]
    strip = make_seamless(strip, strip.shape[0] // 6, axes="y")
    sgray = cv2.cvtColor(strip, cv2.COLOR_RGB2GRAY)
    paint = cv2.GaussianBlur(np.clip((sgray.astype(np.float32) - 118.0) / 40.0, 0, 1), (0, 0), 2.0)
    s_rough_img = np.clip((0.82 - paint * 0.24) * 255.0, 0, 255).astype(np.uint8)   # 白漆 0.58

    return {
        "albedo": clean, "normal16": normal16, "roughness": rough_img,
        "stripe_albedo": strip, "stripe_roughness": s_rough_img, "_seam_metrics": metrics,
    }


# ----------------------------------------------------------------------------- 4. Trim Sheet
def build_trim_sheet(tiles: np.ndarray, tactile: np.ndarray, asphalt: np.ndarray,
                     stripe: np.ndarray) -> np.ndarray:
    """2048x2048 四象限: 左上地砖 / 右上盲道 / 左下沥青 / 右下白线 Trim 条带."""
    s = TRIM_SIZE
    sheet = np.zeros((s, s, 3), np.uint8)
    q = (s - GUTTER * 3) // 2
    # (py, px): 左上地砖 / 右上盲道 / 左下沥青 / 右下白线 Trim 条带
    slots = [(GUTTER, GUTTER), (GUTTER, GUTTER * 2 + q),
             (GUTTER * 2 + q, GUTTER), (GUTTER * 2 + q, GUTTER * 2 + q)]
    arts = [tiles, tactile, asphalt, None]
    for (py, px), art in zip(slots, arts):
        if art is None:                              # 条带 1:4 等比居中放入右下象限
            sw = max(q // 4, 1)
            piece = cv2.resize(stripe, (sw, q), interpolation=cv2.INTER_AREA)
            sheet[py : py + q, px + (q - sw) // 2 : px + (q - sw) // 2 + sw] = piece
        else:
            sheet[py : py + q, px : px + q] = cv2.resize(art, (q, q), interpolation=cv2.INTER_AREA)
    mid = GUTTER + q + GUTTER // 2                   # 工业分隔线 + 留白带内标注
    sheet[mid - 1 : mid + 1, :] = 38
    sheet[:, mid - 1 : mid + 1] = 38
    cv2.putText(sheet, "TILES", (8, GUTTER + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1)
    cv2.putText(sheet, "TACTILE", (GUTTER * 2 + q + 8, GUTTER + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1)
    cv2.putText(sheet, "ASPHALT", (8, GUTTER * 2 + q + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1)
    cv2.putText(sheet, "WHITE-STRIPE TRIM", (GUTTER * 2 + q + 8, GUTTER * 2 + q + 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 210, 210), 1)
    return sheet


# ----------------------------------------------------------------------------- main
def upscale(img: np.ndarray, size: int = OUT_SIZE) -> np.ndarray:
    interp = cv2.INTER_AREA if img.shape[0] > size else cv2.INTER_CUBIC
    return cv2.resize(img, (size, size), interpolation=interp)


def main() -> None:
    print("[ground-pbr] Phase 1-2: processing ground pavement kits ...")
    tiles = process_tiles()
    tactile = process_tactile()
    asphalt = process_asphalt()

    kits: dict[str, np.ndarray] = {
        "ground_tiles_albedo.png": upscale(tiles["albedo"]),
        "ground_tiles_normal.png": upscale(tiles["normal16"]),
        "ground_tiles_roughness.png": upscale(tiles["roughness"]),
        "ground_tiles_ao.png": upscale(tiles["ao"]),
        "ground_tactile_albedo.png": upscale(tactile["albedo"]),
        "ground_tactile_normal.png": upscale(tactile["normal16"]),
        "ground_tactile_roughness.png": upscale(tactile["roughness"]),
        "ground_asphalt_albedo.png": upscale(asphalt["albedo"]),
        "ground_asphalt_normal.png": upscale(asphalt["normal16"]),
        "ground_asphalt_roughness.png": upscale(asphalt["roughness"]),
        "asphalt_clean_albedo.png": upscale(asphalt["albedo"]),
        "asphalt_white_stripe.png": cv2.resize(asphalt["stripe_albedo"], (512, 2048), interpolation=cv2.INTER_CUBIC),
        "asphalt_white_stripe_roughness.png": cv2.resize(asphalt["stripe_roughness"], (512, 2048), interpolation=cv2.INTER_AREA),
    }
    kits["ground_trim_sheet_2k.png"] = build_trim_sheet(
        kits["ground_tiles_albedo.png"], kits["ground_tactile_albedo.png"],
        kits["ground_asphalt_albedo.png"], kits["asphalt_white_stripe.png"],
    )

    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, img in kits.items():
            save_png(out_dir / name, img)
        print(f"[ground-pbr] wrote {len(kits)} assets -> {out_dir.relative_to(ROOT)}")

    # QA 预览存评审目录 (不进 Godot 工程, 避免 .import 噪声)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    save_png(QA_DIR / "qa_asphalt_seamless_2x2.jpg",
             cv2.resize(np.tile(kits["ground_asphalt_albedo.png"], (2, 2, 1)), (1024, 1024), interpolation=cv2.INTER_AREA))
    contact = np.concatenate(
        [cv2.resize(kits[f"ground_{n}_albedo.png"], (512, 512)) for n in ("tiles", "tactile", "asphalt")], axis=1)
    save_png(QA_DIR / "qa_kits_contact.jpg", contact)
    print(f"[ground-pbr] QA previews -> {QA_DIR.relative_to(ROOT)}")

    m = asphalt["_seam_metrics"]
    verdict = "PASS" if (m["h_ratio"] < 1.6 and m["v_ratio"] < 1.6) else "WARN"
    print(f"[ground-pbr] seamless gate: {verdict} (h={m['h_ratio']:.2f}, v={m['v_ratio']:.2f}, threshold 1.6)")
    print("[ground-pbr] done.")


if __name__ == "__main__":
    main()
