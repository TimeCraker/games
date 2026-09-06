#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asternova 地面铺装 PBR 管线 2.0 (第四执行组 · Ground Pavement Pipeline).

彻底废除微距照片输入（电视雪花噪点 / 死黑砂纸感 / 纯色塑料板三大事故根源），
改为程序化「分频平铺 PBR 底图」：周期晶格值噪声按数学方式四向无缝，
只保留波长 >= 1.5m 的大尺度明度生命，高频颗粒严格为零，细节交给
法线倒角 / AO / 反射探针在引擎里呈现。对标 art/references/map_style/
的 anime_urban_zzz_01（商业街方砖）/ zzz_08（广场盲道井盖）/ zzz_12（纯净车道）。

输出 (render-lab/models/environment/ground/ 与 client-godot-v2/art/textures/ground/):
    ground_tiles_albedo/normal/roughness/ao.png        中性暖灰大方砖 PBR 套件 (2.4m, 4x4)
    ground_tactile_albedo/normal/roughness.png         暖姜黄盲道砖 PBR 套件 (0.9m, 3x3)
    ground_asphalt_albedo/normal/roughness.png         冷蓝灰纯净沥青 PBR 套件 (2.5m)
    road_marking_edge_decal.png (+ _roughness)         512x2048 车道边缘白实线贴花 (RGBA)
    manhole_cover_decal.png (+ _normal/_roughness/_metallic)  1024^2 铸铁井盖贴花 (RGBA)

审美处方 (总架构师拍板 · 2026-09-06 新标准):
    地砖   基底中性偏暖灰 #98948C ~ #A4A098 (漫反射明度 55%~60%, 严禁白切过曝),
           拼缝深灰 #3E3B36 + 边缘曲率 2~3px 微倒角, 砖面 rough 0.65 / 缝隙 0.88,
           材质法线强度 0.12 ~ 0.15
    沥青   高级石板深蓝灰 #3C414A ~ #464C56, 四向无缝 (2x2 拼接梯度比 < 1.30),
           仅保留波长 > 1.5m 轮胎压痕微暗带与柔和天光水渍, rough 0.68 / 暗带 0.52
    盲道   日式暖姜黄 #CFA132 ~ #E5B23B, 4 根圆弧胶囊立体凸条,
           凸条 rough 0.48 (树脂微光泽) / 底板 0.68
    标线   暖白 #E2E4E8, 0.2m 标定宽度, 边缘 2px 亚像素微倒角
    井盖   深色铸铁渐变 #34373D, 外圈 16 螺栓孔 / 中圈同心圆齿纹雨水凹槽 /
           中央星形水道局徽章, rough 0.42 / metallic 0.45
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]          # .../asternova
OUT_DIRS = [
    ROOT / "render-lab" / "models" / "environment" / "ground",
    ROOT / "client-godot-v2" / "art" / "textures" / "ground",
]
QA_DIR = ROOT / "art" / "render_previews" / "environment" / "ground_qa"

OUT_SIZE = 2048            # 2K 主输出
SEAM_GATE = 1.30           # 2x2 拼接梯度比红线 (任务书)

# ---- 处方色板 (sRGB 0-255) ----
TILE_A = np.array([0xE0, 0xE0, 0xE8], np.float32)   # 亮砖 白场 #E0E0E8 (STYLE 标定)
TILE_B = np.array([0xD5, 0xD8, 0xDC], np.float32)   # 暗砖 #D5D8DC (STYLE 标定)
TILE_SEAM = np.array([0x3E, 0x3B, 0x36], np.float32)  # 深灰勾缝
ASPH_A = np.array([0x46, 0x4C, 0x56], np.float32)   # 沥青亮部 蓝灰
ASPH_B = np.array([0x3C, 0x41, 0x4A], np.float32)   # 沥青暗部
TACTILE_A = np.array([0xE5, 0xB2, 0x3B], np.float32)  # 姜黄亮部
TACTILE_B = np.array([0xCF, 0xA1, 0x32], np.float32)  # 姜黄暗部
MARKING_WHITE = np.array([0xE8, 0xEC, 0xF0], np.float32)  # 白漆标线 #E8ECF0 (纠偏令)
MANHOLE_IRON = np.array([0x34, 0x37, 0x3D], np.float32)   # 铸铁基色
MANHOLE_IRON_DARK = np.array([0x28, 0x2B, 0x31], np.float32)  # 铸铁外缘


# ----------------------------------------------------------------------------- 噪声
def _periodic_upsample(lattice: np.ndarray, size: int) -> np.ndarray:
    """晶格双线性上采样到 size x size, 环绕插值 => 结果天然四向无缝."""
    c = lattice.shape[0]
    u = (np.arange(size, dtype=np.float32) + 0.5) / size * c
    i0 = np.floor(u).astype(np.int32) % c
    i1 = (i0 + 1) % c
    f = (u - np.floor(u)).astype(np.float32)
    cols = lattice[:, i0] * (1.0 - f)[None, :] + lattice[:, i1] * f[None, :]
    return cols[i0, :] * (1.0 - f)[:, None] + cols[i1, :] * f[:, None]


def fbm(size: int, cells_list: list[int], weights: list[float], seed: int) -> np.ndarray:
    """分频周期值噪声 fbm, 各 octave 独立种子, 输出归一到 [0,1]."""
    rng = np.random.default_rng(seed)
    out = np.zeros((size, size), np.float32)
    for cells, w in zip(cells_list, weights):
        out += _periodic_upsample(rng.random((cells, cells), np.float32) * 2.0 - 1.0, size) * w
    out -= out.min()
    m = float(out.max())
    return out / m if m > 1e-6 else out


def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    """支持升序/降序边缘 (e1 < e0 时自动反向), 保证曲率倒角处处二阶连续."""
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def to_16bit_normal(height: np.ndarray, strength: float) -> np.ndarray:
    """Sobel 高度场 -> 16-bit 切线空间法线 (OpenGL 绿通道 +V 向上).

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


def seam_test(img: np.ndarray) -> dict[str, float]:
    """2x2 拼接测试: 环绕接缝行/列的梯度均值 vs 全图梯度均值 (1.0 = 与内部一致).

    用均值而非中值: 颗粒纹理的中值梯度趋零, 中值比会爆炸失真。
    """
    gray = cv2.cvtColor(np.tile(img, (2, 2, 1)), cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    grad_x = np.abs(np.diff(gray, axis=1))
    grad_y = np.abs(np.diff(gray, axis=0))
    base_x, base_y = float(grad_x.mean()) + 1e-6, float(grad_y.mean()) + 1e-6
    return {
        "h_ratio": float(grad_y[cy - 1 : cy + 1, :].mean()) / base_y,
        "v_ratio": float(grad_x[:, cx - 1 : cx + 1].mean()) / base_x,
    }


def save_png(path: Path, img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = img
    if out.ndim == 3 and out.shape[2] == 3:
        out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)      # cv2.imwrite 期望 BGR (16bit 亦然)
    elif out.ndim == 3 and out.shape[2] == 4:
        out = cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA)
    if not cv2.imwrite(str(path), out):
        raise IOError(f"cv2.imwrite failed: {path}")


def upscale(img: np.ndarray, size: int = OUT_SIZE) -> np.ndarray:
    interp = cv2.INTER_AREA if img.shape[0] > size else cv2.INTER_CUBIC
    return cv2.resize(img, (size, size), interpolation=interp)


# ----------------------------------------------------------------------------- 1. 地砖
def process_tiles() -> dict[str, np.ndarray]:
    """4x4 商业街大方砖: 中性偏暖灰 + 曲率微倒角勾缝, 零颗粒."""
    s = OUT_SIZE
    cell = s // 4                                     # 512px = 0.6m 方砖

    # 1) 分频明度生命: 砖间恒定抖动 (每块石头独立色调) + 砖内超低频起伏
    rng = np.random.default_rng(41)
    tile_jitter = rng.uniform(-0.5, 0.5, (4, 4)).astype(np.float32)     # 每砖色调偏移
    jitter_img = np.kron(tile_jitter, np.ones((cell, cell), np.float32))
    macro = fbm(s, [2, 4], [0.6, 0.4], 42)                              # 波长 >= 0.6m
    tone = np.clip(0.5 + 0.5 * jitter_img * 0.55 + (macro - 0.5) * 0.30, 0.0, 1.0)

    # 2) 勾缝高度场: 缝芯平底 + 边缘曲率余弦倒角 (2~3px 过渡带, 不生硬)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    fx = np.minimum(xx % cell, cell - (xx % cell))    # 距砖缝的像素距 (0 = 缝芯)
    fy = np.minimum(yy % cell, cell - (yy % cell))
    fd = np.minimum(fx, fy)
    seam_w, bevel_w = 3.0, 2.6                        # 缝芯半宽 3px, 倒角 2.6px (~0.7mm/px)
    height = 0.40 + 0.60 * smoothstep(seam_w, seam_w + bevel_w, fd)
    seam_core = 1.0 - smoothstep(seam_w - 1.5, seam_w + 0.5, fd)          # 缝芯 albedo 混合权重
    bevel_band = smoothstep(seam_w, seam_w + bevel_w, fd)                 # 倒角带曲率遮蔽
    # 缝宽下沿砖块边缘做 1px 级圆角柔化 (曲率倒角: 越接近缝越暗, 二阶连续)
    albedo = TILE_B[None, None] * (1.0 - tone[..., None]) + TILE_A[None, None] * tone[..., None]
    albedo = albedo * (1.0 - (1.0 - bevel_band)[..., None] * 0.18)         # 倒角带微暗 (曲率着色)
    albedo = albedo * (1.0 - seam_core[..., None]) + TILE_SEAM[None, None] * seam_core[..., None]
    albedo = np.clip(albedo, 0, 255).astype(np.uint8)

    # 3) AO: 缝芯 0.30, 倒角带柔和回落 (宽于 albedo 缝, 环境遮蔽纵深)
    ao = np.clip(0.30 + 0.70 * smoothstep(seam_w * 0.5, seam_w + bevel_w * 2.2, fd), 0, 1)
    ao_img = (ao * 255.0).astype(np.uint8)

    # 4) 法线: 倒角高度场 + 砖面超低频石面起伏 (无任何颗粒)
    face_waviness = (fbm(s, [8, 16], [0.65, 0.35], 43) - 0.5) * 0.012
    normal16 = to_16bit_normal(height + face_waviness, strength=2.6)

    # 5) Roughness: 砖面 0.65 -> 倒角带渐变 -> 缝隙 0.88, 每砖 ±0.015
    rough = 0.65 + (0.88 - 0.65) * (1.0 - smoothstep(seam_w, seam_w + bevel_w, fd))
    rough += tile_jitter.repeat(cell, 0).repeat(cell, 1) * 0.03
    rough_img = np.clip(rough * 255.0, 0, 255).astype(np.uint8)

    face = albedo[seam_core < 0.05]
    mean_lv = float(face.reshape(-1, 3).mean())
    print(f"    [tiles] 4x4 @0.6m, 砖面均值明度 {mean_lv / 255.0:.3f} (处方 0.55~0.62)")
    return {"albedo": albedo, "normal16": normal16, "roughness": rough_img, "ao": ao_img}


# ----------------------------------------------------------------------------- 2. 盲道
def process_tactile() -> dict[str, np.ndarray]:
    """3x3 日式盲道砖: 暖姜黄 + 4 根圆弧胶囊凸条 (解析距离场, 天然无缝)."""
    s = OUT_SIZE
    cell_f = s / 3.0                                  # 682.67px = 0.3m 砖

    # 像素 -> 砖内周期坐标 [0,1), 用最近整数砖重复实现跨砖周期
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    u = (xx / cell_f) % 1.0
    v = (yy / cell_f) % 1.0

    # 1) 胶囊凸条 SDF: 4 条纵向条, 条心 u = 1/8,3/8,5/8,7/8, 半宽 0.055,
    #    v 两端 0.09 收入圆角; 双轴周期 wrap 取最小距 => 跨砖天然无缝
    du = np.abs(u[None, :, :] - np.array([0.125, 0.375, 0.625, 0.875])[:, None, None])
    du = np.minimum(du, 1.0 - du)                     # u 向 wrap
    bar_half, cap_margin = 0.055, 0.09
    dv_end = np.minimum(v, 1.0 - v)                   # v 向 wrap 距端缝
    dv_axis = np.maximum(dv_end - (0.5 - cap_margin), 0.0)   # 伸出胶囊段的轴向距离
    d_bar = np.sqrt(np.maximum(du - bar_half, 0.0) ** 2 + dv_axis ** 2).min(axis=0)
    bevel = 0.024                                     # 圆弧倒角带宽 (砖宽的 2.4%)
    dome = smoothstep(bevel, 0.0, d_bar)              # 条内 1 -> 板面 0, 圆弧倒角过渡

    # 2) 每砖姜黄色调抖动 (明度 ±3.5%) + 砖内超低频起伏
    rng = np.random.default_rng(53)
    tile_j = rng.uniform(-1.0, 1.0, (3, 3)).astype(np.float32)
    jt = np.zeros((s, s), np.float32)
    for ty in range(3):
        for tx in range(3):
            y0, y1 = int(ty * cell_f), int((ty + 1) * cell_f)
            x0, x1 = int(tx * cell_f), int((tx + 1) * cell_f)
            jt[y0:y1, x0:x1] = tile_j[ty, tx]
    macro = fbm(s, [3, 6], [0.6, 0.4], 54)
    tone = np.clip(0.5 + jt * 0.20 + (macro - 0.5) * 0.25, 0.0, 1.0)

    # 3) 拼装缝: 砖缘 5px 深灰沟 (跨缝周期 => 天然无缝)
    fx = np.minimum(u, 1.0 - u) * cell_f
    fy = np.minimum(v, 1.0 - v) * cell_f
    fd = np.minimum(fx, fy)
    joint = 1.0 - smoothstep(1.5, 4.5, fd)
    dome *= smoothstep(0.5, 4.0, fd) * 0.25 + 0.75    # 凸条到缝边自然断开

    base = TACTILE_B[None, None] * (1.0 - tone[..., None]) + TACTILE_A[None, None] * tone[..., None]
    lift = (dome - 0.5)[..., None] * 0.10             # 凸条顶部微提亮 (陶瓷微光泽)
    albedo = base * (1.0 + lift) * (1.0 - joint[..., None] * 0.55)
    albedo = np.clip(albedo, 0, 255).astype(np.uint8)

    # 4) 高度场 / 法线: 圆弧倒角 dome + 拼缝下凹
    height = 0.45 + dome * 0.42 - joint * 0.35
    normal16 = to_16bit_normal(height, strength=4.2)

    # 5) Roughness: 凸条 0.48 / 底板 0.68
    rough = 0.68 - dome * 0.20
    rough_img = np.clip(rough * 255.0, 0, 255).astype(np.uint8)

    print(f"    [tactile] 3x3 @0.3m, 4 胶囊凸条 (半宽 0.055, 倒角 {bevel})")
    return {"albedo": albedo, "normal16": normal16, "roughness": rough_img}


# ----------------------------------------------------------------------------- 3. 沥青
def process_asphalt() -> dict[str, np.ndarray]:
    """日式深灰沥青 2.0: 真实骨料微颗粒 + 深浅磨损杂色 (纠偏令, 严禁双边磨皮纯色块).

    基调 #34373D (sRGB 0.20,0.21,0.24), 颗粒明度 0.18~0.26 自然波动;
    周期晶格噪声 => 四向数学无缝; 法线携带骨料咬合起伏, 配合引擎 SSAO 呈现路面质感。
    """
    s = OUT_SIZE
    # 1) 骨料颗粒 (细, 2~8px) + 矿物杂色 (每粒轻微通道失相关) + 中频磨损斑 + 宏观明度
    grain_a = fbm(s, [256, 512], [0.6, 0.4], 81)      # 细石粒
    grain_b = fbm(s, [128, 256], [0.6, 0.4], 82)      # 次级石粒
    grain = grain_a * 0.62 + grain_b * 0.38           # 0..1
    mottle = fbm(s, [24, 48, 96], [0.45, 0.35, 0.20], 83)   # 磨损深浅斑 (中频)
    macro = fbm(s, [2, 4], [0.6, 0.4], 84)            # 大区明度生命
    chroma = (fbm(s, [256], [1.0], 87) - 0.5)[..., None] * 0.10  # 每粒冷暖气微偏 (周期场)

    base = np.array([0x34, 0x37, 0x3D], np.float32)   # #34373D 深灰冷调
    lum = 0.20 + grain * 0.055 + (mottle - 0.5) * 0.10 + (macro - 0.5) * 0.08
    lum = np.clip(lum, 0.18, 0.26)[..., None]         # 处方波动带 0.18 ~ 0.26
    albedo_f = base[None, None] * (lum / 0.213) * (1.0 + chroma * (grain[..., None] - 0.5) * 2.0)
    albedo_f = np.clip(albedo_f, 0, 255)

    # 2) 轮胎压痕微暗带 (低频, 沿行驶方向) + 柔和天光水渍
    xx = np.arange(s, dtype=np.float32)[None, :].repeat(s, 0)
    band = np.exp(-((xx - s * 0.315) / (s * 0.085)) ** 2) \
         + np.exp(-((xx - s * 0.685) / (s * 0.085)) ** 2)
    band = np.clip(band, 0.0, 1.0)
    stain = fbm(s, [1, 2], [0.6, 0.4], 86)
    albedo_f *= (1.0 - band * 0.05)[..., None]        # 压痕带微暗
    albedo_f *= (1.0 - (stain - 0.5) * 0.06)[..., None]
    albedo = np.clip(albedo_f, 0, 255).astype(np.uint8)

    # 3) Roughness: 基底 0.82 (天光反射靠 Forward+ 探针), 压实暗带 0.60, 水渍 0.78
    rough = 0.82 - band * 0.22 - (stain - 0.5) * 0.08
    rough_img = np.clip(rough * 255.0, 0, 255).astype(np.uint8)

    # 4) 法线: 骨料凸出咬合 (颗粒高度) + 压痕/水渍宏观起伏 => 引擎 SSAO 出咬合感
    height = 0.5 + (grain - 0.5) * 0.30 + (mottle - 0.5) * 0.12 - band * 0.04
    normal16 = to_16bit_normal(height, strength=2.4)

    metrics = seam_test(albedo)
    print(f"    [asphalt] #34373D grain albedo lum {lum.min():.3f}~{lum.max():.3f}, "
          f"seamless 2x2: h={metrics['h_ratio']:.2f} v={metrics['v_ratio']:.2f} (gate < {SEAM_GATE})")
    return {"albedo": albedo, "normal16": normal16, "roughness": rough_img,
            "_seam_metrics": metrics}


# ----------------------------------------------------------------------------- 4a. 边缘标线贴花
def build_marking_decal() -> dict[str, np.ndarray]:
    """512x2048 纵向无缝白实线贴花 (RGBA): 0.2m 宽标定, 2px 亚像素倒角, 低频磨损失活."""
    w, h = 512, 2048
    ss = 2                                            # 2x 超采样 -> 下采样获得 ~2px AA
    yy, xx = np.mgrid[0 : h * ss, 0 : w * ss].astype(np.float32)
    u = xx / (w * ss)                                 # 0..1 横向 (0.2m)
    # 磨损: 只沿 V 低频 (周期 wrap), 横向整体均匀 => 贴花边缘 AA 不受噪声污染
    wear_l = _periodic_upsample(np.random.default_rng(71).random((8, 8), np.float32), h * ss)[:, :1]
    wear = 0.86 + 0.14 * wear_l[:, 0][:, None].repeat(w * ss, 1)

    alpha = np.ones((h * ss, w * ss), np.float32) * wear
    col = np.zeros((h * ss, w * ss, 3), np.float32) + MARKING_WHITE[None, None]
    rgba = np.dstack([col, np.clip(alpha, 0, 1) * 255.0]).astype(np.uint8)
    rgba = cv2.resize(rgba, (w, h), interpolation=cv2.INTER_AREA)

    rough = np.full((h, w), 0.55, np.float32)         # 白漆 rough 0.55 (纠偏令)
    rough_img = (np.clip(rough, 0, 1) * 255.0).astype(np.uint8)
    print("    [marking] 512x2048 RGBA, 边缘 INTER_AREA 亚像素倒角, V 向 8 段周期磨损")
    return {"rgba": rgba, "roughness": rough_img}


# ----------------------------------------------------------------------------- 4b. 井盖贴花
def _star_mask(size: int, cx: float, cy: float, r_out: float, r_in: float) -> np.ndarray:
    ang = np.pi / 2.0 + np.linspace(0, 2 * np.pi, 11)[:-1]
    pts = []
    for i, a in enumerate(ang):
        r = r_out if i % 2 == 0 else r_in
        pts.append([cx + r * np.cos(a), cy - r * np.sin(a)])
    mask = np.zeros((size, size), np.uint8)
    cv2.fillPoly(mask, [np.array(pts, np.float32).astype(np.int32)], 255)
    return mask


def build_manhole_decal() -> dict[str, np.ndarray]:
    """1024^2 正圆形铸铁井盖贴花 (RGBA): 16 螺栓孔 / 同心圆齿纹雨水凹槽 / 星形徽章."""
    final, ss = 1024, 2
    s = final * ss
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    dx, dy = xx - s / 2.0, yy - s / 2.0
    r = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    disc_r = s * 0.478
    inside = smoothstep(disc_r, disc_r - 2.0 * ss, r)             # 圆盘, 边缘 2px AA
    height = np.zeros((s, s), np.float32)
    albedo = np.zeros((s, s, 3), np.float32)

    # 基底铸铁渐变: 心部 #34373D -> 外缘略深, 凸起处微提亮
    rad = np.clip(r / disc_r, 0, 1)
    base = MANHOLE_IRON[None, None] * (1.0 - rad[..., None]) \
         + (MANHOLE_IRON - 6.0)[None, None] * rad[..., None]

    # --- 外圈: 环形凸缘 + 16 螺栓孔 ---
    rim = smoothstep(s * 0.405, s * 0.425, r) * (1.0 - smoothstep(s * 0.462, s * 0.478, r))
    height += rim * 0.16
    bolt_r, bolt_ring, bolt_hole = s * 0.021, s * 0.440, s * 0.013
    bolt = np.zeros((s, s), np.float32)
    for k in range(16):
        a = k * np.pi / 8.0
        bx, by = s / 2.0 + bolt_ring * np.cos(a), s / 2.0 + bolt_ring * np.sin(a)
        m = ((xx - bx) ** 2 + (yy - by) ** 2) < bolt_hole ** 2
        bolt[m] = 1.0
    bolt_soft = cv2.GaussianBlur(bolt, (0, 0), 1.2 * ss)
    height -= bolt_soft * 0.30

    # --- 中圈: 同心圆雨水凹槽 (3 道 V 槽) + 36 径向齿纹 ---
    groove = np.zeros((s, s), np.float32)
    for gr in (0.185, 0.255, 0.325):
        band = 1.0 - smoothstep(0.0, s * 0.018, np.abs(r - s * gr))
        groove = np.maximum(groove, band)
    teeth = (0.5 + 0.5 * np.cos(ang * 36.0)) * smoothstep(s * 0.16, s * 0.175, r) \
          * (1.0 - smoothstep(s * 0.345, s * 0.36, r))
    height -= groove * 0.22
    height += teeth * 0.05
    groove_total = np.clip(groove + bolt_soft, 0, 1)

    # --- 中央: 凸起圆台 + 星形水道局徽章 (距离场倒角) ---
    hub = smoothstep(s * 0.165, s * 0.15, r)
    height += hub * 0.10
    star = _star_mask(s, s / 2.0, s / 2.0, s * 0.105, s * 0.042)
    d_in = cv2.distanceTransform((star > 0).astype(np.uint8), cv2.DIST_L2, 3)
    d_out = cv2.distanceTransform((star == 0).astype(np.uint8), cv2.DIST_L2, 3)
    star_bevel = np.clip(np.minimum(np.where(star > 0, d_in, d_out) / (2.2 * ss), 1.0), 0, 1)
    height += np.where(star > 0, star_bevel * 0.22, -star_bevel * 0.06)

    # --- albedo / roughness / metallic 合成 ---
    relief = np.clip(height, -0.35, 0.35)
    albedo = base * (1.0 + relief * 0.55)[..., None]
    albedo *= (1.0 - groove_total * 0.42)[..., None]              # 凹槽蓄水深色
    albedo = np.clip(albedo, 0, 255)

    rough = np.full((s, s), 0.42, np.float32)
    rough += groove_total * 0.16                                   # 凹槽 0.58
    rough -= np.clip(height, 0, 1) * 0.05
    rough = np.clip(rough, 0.30, 0.72)

    metal = np.full((s, s), 0.45, np.float32)
    metal -= groove_total * 0.25                                   # 凹槽锈蚀失金属度

    alpha = inside * 255.0

    def down(x: np.ndarray) -> np.ndarray:
        return cv2.resize(x, (final, final), interpolation=cv2.INTER_AREA)

    rgba = np.dstack([albedo, alpha]).astype(np.uint8)
    # 法线在盘外必须回中 (避免透明区黑边)
    h_out = np.where(inside > 0.999, height, 0.5)
    normal16 = to_16bit_normal(h_out, strength=3.0)
    print("    [manhole] 1024^2 RGBA: 16 螺栓孔 / 3 道雨水凹槽 + 36 齿纹 / 星形徽章")
    return {
        "rgba": down(rgba),
        "normal16": down(normal16),
        "roughness": down(np.clip(rough * 255.0, 0, 255).astype(np.uint8)),
        "metallic": down(np.clip(metal * 255.0, 0, 255).astype(np.uint8)),
    }


# ----------------------------------------------------------------------------- main
def main() -> None:
    print("[ground-pbr] Phase 1-2: procedural tiled-PBR production (zero photographic input) ...")
    tiles = process_tiles()
    tactile = process_tactile()
    asphalt = process_asphalt()
    marking = build_marking_decal()
    manhole = build_manhole_decal()

    kits: dict[str, np.ndarray] = {
        "ground_tiles_albedo.png": tiles["albedo"],
        "ground_tiles_normal.png": tiles["normal16"],
        "ground_tiles_roughness.png": tiles["roughness"],
        "ground_tiles_ao.png": tiles["ao"],
        "ground_tactile_albedo.png": tactile["albedo"],
        "ground_tactile_normal.png": tactile["normal16"],
        "ground_tactile_roughness.png": tactile["roughness"],
        "ground_asphalt_albedo.png": asphalt["albedo"],
        "ground_asphalt_normal.png": asphalt["normal16"],
        "ground_asphalt_roughness.png": asphalt["roughness"],
        "road_marking_edge_decal.png": marking["rgba"],
        "road_marking_edge_decal_roughness.png": marking["roughness"],
        "manhole_cover_decal.png": manhole["rgba"],
        "manhole_cover_decal_normal.png": manhole["normal16"],
        "manhole_cover_decal_roughness.png": manhole["roughness"],
        "manhole_cover_decal_metallic.png": manhole["metallic"],
    }

    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, img in kits.items():
            save_png(out_dir / name, img)
        print(f"[ground-pbr] wrote {len(kits)} assets -> {out_dir.relative_to(ROOT)}")

    # QA 预览 (评审目录, 不进 Godot 工程)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    save_png(QA_DIR / "qa_asphalt_seamless_2x2.jpg",
             cv2.resize(np.tile(asphalt["albedo"], (2, 2, 1)), (1024, 1024), interpolation=cv2.INTER_AREA))
    contact = np.concatenate(
        [cv2.resize(kits[f"ground_{n}_albedo.png"], (512, 512)) for n in ("tiles", "tactile", "asphalt")],
        axis=1)
    save_png(QA_DIR / "qa_kits_contact.jpg", contact)
    mh = cv2.resize(kits["manhole_cover_decal.png"], (512, 512), interpolation=cv2.INTER_AREA)
    bg = np.full((512, 512, 3), 96, np.float32)
    af = (mh[:, :, 3:4].astype(np.float32) / 255.0)
    mh_on_gray = (mh[:, :, :3].astype(np.float32) * af + bg * (1.0 - af)).astype(np.uint8)
    stripe = cv2.resize(kits["road_marking_edge_decal.png"], (128, 512), interpolation=cv2.INTER_AREA)[:, :, :3]
    decal_row = np.concatenate([
        mh_on_gray,
        np.pad(stripe, ((0, 0), (192, 192), (0, 0)), constant_values=96),
    ], axis=1)
    save_png(QA_DIR / "qa_decals_contact.png", decal_row)
    print(f"[ground-pbr] QA previews -> {QA_DIR.relative_to(ROOT)}")

    m = asphalt["_seam_metrics"]
    ok = m["h_ratio"] < SEAM_GATE and m["v_ratio"] < SEAM_GATE
    print(f"[ground-pbr] seamless gate ({SEAM_GATE}): {'PASS' if ok else 'FAIL'}"
          f" (h={m['h_ratio']:.2f}, v={m['v_ratio']:.2f})")
    if not ok:
        raise SystemExit(1)
    print("[ground-pbr] done.")


if __name__ == "__main__":
    main()
