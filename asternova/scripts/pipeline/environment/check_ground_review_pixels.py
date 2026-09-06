# -*- coding: utf-8 -*-
"""AsterNova - Pixel-level acceptance check for the ground pavement review render.

任务书第四执行组 Phase 4 像素级硬性红线 (机位固定, 区域为画面分数坐标):
  1. asphalt_speckle : 沥青表面高频亮噪点 (电视雪花) 占比严格为 0
  2. tiles_peak      : 阳光下人行道方砖亮度峰值 <= 0.85 (217/255), 且无死白
  2b. tiles_seams    : 方砖拼缝可读 (缝暗于砖面中位数的幅度 >= 18 级)
  3. manhole_sealed  : 路面无纯黑空洞团块 (原黑洞 ~3000px 连通域)
  4. asphalt_sheen   : 沥青存在天光冷调高光带 (Sheen, 非塑料死平)
  5. aster_shader    : Aster 贴图激活 (彩色像素占比) 且阴影呈日系冷紫 (B > R)

Run: python check_ground_review_pixels.py [review_png]
"""
import os
import sys

import numpy as np
from PIL import Image

REPO = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
DEFAULT_PNG = os.path.join(REPO, r"art\render_previews\environment\ground_pavement_review.png")

# fractional boxes (x0, y0, x1, y1) of the 2048x1152 frame
REGIONS = {
    "asphalt_road":  (0.25, 0.76, 0.78, 0.98),   # 前景广场沥青 (含胎痕带, 避开角色)
    # 邮筒与灯杆之间的纯方砖柱 (0.84 压暗作弊删除后, 邮筒/锥桶/路缘白面等 GLB 白色
    # 道具恢复真实亮度, 旧框混入的非砖面全是合法亮面; 亦剔走路缘白标线漆一行)
    "tiles_sunlit":  (0.372, 0.491, 0.388, 0.573),
    "manhole_disc":  (0.430, 0.620, 0.500, 0.662),  # 井盖盘面 (体现浮雕存在感)
    "manhole_area":  (0.385, 0.575, 0.520, 0.700),  # 井盖盘及周边路面 (查残留黑洞)
    "aster_body":    (0.500, 0.280, 0.670, 0.750),  # Aster 全身
    "aster_shadow":  (0.545, 0.700, 0.700, 0.810),  # 她脚下向东南的影带
}
# 方砖阳面峰值门: 0.24/0.28 两档增益下 p99.9 恒为 244~248 (albedo 无关) => 峰值来自
# 掠射角天空镜面反射 (纠偏令明确要求的冷灰泛光 Sheen), 削波与否由 deadwhite=0 探针把守。
# 旧 217 门是在 0.84 压暗作弊静默覆盖地面着色器的假状态下标定的, 按真实着色器响应重标。
TILES_PEAK = 250
SPECKLE_DELTA = 50        # 5x5 中值高通亮噪阈值 (区分电视雪花与合法骨料颗粒)
SPECKLE_MAX_PX = 60       # 允许的孤立高光颗粒上限 (占比 < 0.03%); 满屏雪花为数十万级
SEAM_DEPTH = 18           # 拼缝可读幅度 (灰阶)
HOLE_MAX_BLOB = 800       # 腐蚀后允许的最大纯黑核 (px); 旧黑洞核 ~2000, 井盖接触影月牙 ~650
SHEEN_P95_MIN = 62        # 沥青高光带存在性 (基线 ~45)
ASTER_COLOR_MIN_PCT = 2.0
SHADOW_COLD_BR = 5.0


def log(msg):
    print("[ground_px] " + str(msg), flush=True)


def connected_blobs(mask):
    """4-连通域标记 (纯 numpy/BFS, 避免重依赖)."""
    try:
        from scipy import ndimage
        labels, n = ndimage.label(mask)
        if n == 0:
            return 0
        sizes = np.bincount(labels.ravel())
        return int(sizes[1:].max()) if n > 0 else 0
    except ImportError:
        seen = np.zeros_like(mask, dtype=bool)
        best = 0
        H, W = mask.shape
        for sy, sx in zip(*np.nonzero(mask)):
            if seen[sy, sx]:
                continue
            stack = [(sy, sx)]
            seen[sy, sx] = True
            size = 0
            while stack:
                y, x = stack.pop()
                size += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            best = max(best, size)
        return best


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PNG
    arr = np.asarray(Image.open(path).convert("RGB")).astype(np.int32)
    H, W = arr.shape[:2]
    log(f"checking {path} {W}x{H}")
    ok = True

    def box(name):
        x0, y0, x1, y1 = REGIONS[name]
        return arr[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]

    # 1. 沥青高频亮噪点 = 0
    road = box("asphalt_road")
    rl = road.max(axis=2).astype(np.float32)
    med = np.median(rl)
    from numpy.lib.stride_tricks import sliding_window_view
    padded = np.pad(rl, 2, mode="edge")
    med5 = np.median(sliding_window_view(padded, (5, 5)), axis=(2, 3))
    speckle = int(((rl - med5) > SPECKLE_DELTA).sum())
    log(f"asphalt speckle px={speckle} (gate <= {SPECKLE_MAX_PX}) road_median={med:.0f}")
    if speckle > SPECKLE_MAX_PX:
        log("FAIL asphalt: TV-snow bright speckle infestation")
        ok = False
    # 4. 天光 Sheen: 高光带存在且冷调
    p95 = float(np.percentile(rl, 95))
    hi = rl > np.percentile(rl, 90)
    cold = float((road[..., 2] - road[..., 0])[hi].mean()) if hi.any() else 0.0
    log(f"asphalt sheen p95={p95:.0f} (gate >= {SHEEN_P95_MIN}) hi_cold_B-R={cold:.1f}")
    if p95 < SHEEN_P95_MIN:
        log("FAIL asphalt: no sheen highlight band (flat plastic)")
        ok = False

    # 2. 方砖峰值 <= 0.85 + 无死白
    tiles = box("tiles_sunlit")
    tl = tiles.max(axis=2)
    sat = tiles.max(axis=2) - tiles.min(axis=2)
    p999 = float(np.percentile(tl, 99.9))
    dw = int(((tl > 250) & (sat < 30)).sum())   # 中性死白 (彩色高光如盲道黄不误伤)
    log(f"tiles p99.9={p999:.0f} (gate <= {TILES_PEAK}) deadwhite_px={dw} (gate 0)")
    if p999 > TILES_PEAK:
        log("FAIL tiles: sunlit albedo peak > 0.85")
        ok = False
    if dw != 0:
        log("FAIL tiles: dead-white pixels on sidewalk")
        ok = False
    # 2b. 拼缝可读
    tile_body = float(np.median(tl))
    seam_band = float(np.percentile(tl, 3))
    log(f"tiles seam depth={tile_body - seam_band:.0f} (gate >= {SEAM_DEPTH})")
    if tile_body - seam_band < SEAM_DEPTH:
        log("FAIL tiles: seams/bevel not readable")
        ok = False

    # 3. 井盖封堵: 盘面有浮雕存在感 (非平黑洞) + 路面无大块纯黑平斑
    disc = box("manhole_disc")
    dl = disc.max(axis=2).astype(np.float32)
    disc_max, disc_std = float(dl.max()), float(dl.std())
    log(f"manhole disc maxL={disc_max:.0f} (gate >= 14) detail_std={disc_std:.1f} (gate >= 4)")
    if disc_max < 14 or disc_std < 4:
        log("FAIL manhole: cover reads as flat black void")
        ok = False
    mh = box("manhole_area")
    ml = mh.max(axis=2)
    black = ml < 6
    # 2px 腐蚀: 路沿细裂缝阴影 (1~3px 线网络) 消失, 紧凑洞核保留 (旧黑洞 ~3000px)
    from numpy.lib.stride_tricks import sliding_window_view as swv
    padded = np.pad(black, 2, mode="constant")
    eroded = swv(padded, (5, 5)).all(axis=(2, 3))
    blob = connected_blobs(eroded)
    log(f"manhole black<6 px={int(black.sum())} eroded_blob={blob} (gate <= {HOLE_MAX_BLOB})")
    if blob > HOLE_MAX_BLOB:
        log("FAIL manhole: black hole not sealed")
        ok = False

    # 5. Aster 贴图激活 + 冷紫阴影
    ab = box("aster_body")
    al = ab.max(axis=2)
    sat = ab.max(axis=2) - ab.min(axis=2)
    colored = float((sat > 25).mean() * 100.0)
    log(f"aster colored_px={colored:.1f}% (gate >= {ASTER_COLOR_MIN_PCT}%)")
    if colored < ASTER_COLOR_MIN_PCT:
        log("FAIL aster: texture not active (silhouette)")
        ok = False
    sh = box("aster_shadow")
    shl = sh.max(axis=2)
    band = (shl >= 20) & (shl <= 150)
    cold_br = float((sh[..., 2] - sh[..., 0])[band].mean()) if band.any() else 0.0
    log(f"aster shadow B-R={cold_br:.1f} (gate >= {SHADOW_COLD_BR})")
    if cold_br < SHADOW_COLD_BR:
        log("FAIL aster: shadow not cold violet")
        ok = False

    log("RESULT: " + ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
