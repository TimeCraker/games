"""Aster 蒙皮权重外科手术 —— glb 二进制原位改写（纯 Python，非 Blender 回路）。

为什么不用 Blender 导出回路：Blender 5.2 glTF 导出器会拆顶点（56975→56982）并追加
修正骨骼（43→44），破坏拓扑严整。本脚本直接解析 glb（JSON+BIN chunk），只原位改写
Aster_Body 的 JOINTS_0/WEIGHTS_0 数据字节（BIN 等长），骨架/网格/材质零改动。

手术配方（针对三大硬伤）：
  0) 桥接三角切除（撕裂面元凶）：凡静置姿态下 max边长>0.02 且顶点主导分支跨
     {躯干,左腿,右腿} 的三角形（裙布被自动蒙皮分给腿骨所致），其腿骨主导顶点
     一律清空改挂 Hip=1.0（裙布随骨盆刚体化，迭代 4 轮至收敛）。
     V8 真实步幅下大腿摆幅 ±30°，任何腿骨污染的裙布都会被撕成半米巨面。
  1) 双鞋/腿单侧隔离（y<0.85）：按 X 符号清对侧腿骨组全部权重并归一化；
     清空后权重总和为 0 的顶点回植：
     y<0.45（踝/鞋饰）仅限同侧 Calf/Foot 择近者【铁律：绝不可回植 Thigh——
     跨关节回植是大腿迈步时把踝部装饰拉扯出撕裂面的元凶】；
     y≥0.45（大腿皮肤）回植同侧 Thigh 组。
  2) 长发粘腰：后背长发带(0.82<y<1.32 且 z>0.045)顶点清空
     Spine01/Spine02/Waist/Hip/Pelvis/L_Thigh*/R_Thigh* 全部权重，
     被剥离权重 100% 汇入 Head，再整体归一化。

用法:
  python clean_aster_skinning.py <model.glb>            # 只读分析，打印污染统计
  python clean_aster_skinning.py <model.glb> --apply    # 执行手术并回写
  python clean_aster_skinning.py <model.glb> --hierarchy # 打印骨骼树(重定向映射用)
"""
import json
import struct
import sys

import numpy as np

LOWER_Y_MAX = 0.45   # 踝/鞋饰与大腿皮的分界（回植池切换）
SIDE_Y_MAX = 0.85    # 左右腿侧隔离带（腿骨全程，含大腿）
SKIRT_Y_MIN = 0.35   # 裙区下界：Hip 化（布料剥离/桥接切除）只允许发生在裙区；
                     # 鞋区(y<SKIRT_Y_MIN)顶点绝不进 Hip，否则迈步拖出白色冻结拖影
HAIR_Y_MIN, HAIR_Y_MIN2, HAIR_Y_MAX = 0.82, 0.82, 1.32
HAIR_Z_MIN = 0.045
BRIDGE_MIN_EDGE = 0.02  # 桥接三角判定：静置最大边长
CLOTH_DIST = 0.11    # 布料剥离：距双腿链超过该距离的下半身顶点视为裙布/下摆
ARM_GUARD_DIST = 0.12  # 臂部豁免：距臂链小于该距离的顶点不参与布料剥离
SEAM_MIN_EDGE = 0.015  # 鞋区跨分支接缝三角判定：静置最大边长

LEG_BONES = ["Thigh", "ThighTwist01", "ThighTwist02", "Calf", "CalfTwist01", "CalfTwist02", "Foot", "ToeBase"]
# 回植池：仅同侧膝下骨。严禁回植 Thigh（跨关节回植 → 迈步撕裂面）
REPLANT_BONES = ["Calf", "Foot"]
HAIR_CLEAR_BONES = ["Spine01", "Spine02", "Waist", "Hip", "Pelvis"] + \
    ["L_" + b for b in LEG_BONES] + ["R_" + b for b in LEG_BONES]


def parse_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:4] == b"glTF", "not a glb"
    total = struct.unpack("<I", data[8:12])[0]
    off, js, bin_data = 12, None, None
    while off < total:
        clen, ctype = struct.unpack("<I4s", data[off:off + 8])
        body = data[off + 8:off + 8 + clen]
        if ctype == b"JSON":
            js = json.loads(body.decode("utf-8"))
        elif ctype == b"BIN\x00":
            bin_data = body
        off += 8 + clen
    return js, bin_data


def rebuild_glb(js, bin_data):
    json_bytes = json.dumps(js, separators=(",", ":")).encode("utf-8")
    pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b" " * pad
    bin_pad = (4 - len(bin_data) % 4) % 4
    bin_data += b"\x00" * bin_pad
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    return b"glTF" + struct.pack("<II", 2, total) + \
        struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes + \
        struct.pack("<I4s", len(bin_data), b"BIN") + bin_data


COMP = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_accessor(js, bin_data, acc_idx):
    acc = js["accessors"][acc_idx]
    bv = js["bufferViews"][acc["bufferView"]]
    n, nc = acc["count"], NCOMP[acc["type"]]
    fmt, csize = COMP[acc["componentType"]]
    stride = bv.get("byteStride") or nc * csize
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    if stride == nc * csize:
        out = np.frombuffer(bin_data, dtype=np.dtype(fmt), count=n * nc, offset=base) \
            .reshape(n, nc).astype(np.float64)
    else:
        out = np.zeros((n, nc), dtype=np.float64)
        for i in range(n):
            out[i] = np.frombuffer(bin_data, dtype=np.dtype(fmt), count=nc, offset=base + i * stride)
    if acc.get("normalized"):
        info = np.finfo if fmt == "f" else np.iinfo
        out = out / info(fmt).max
    if "min" in acc and "max" in acc:
        cmn, cmx = out.min(axis=0), out.max(axis=0)
        assert np.allclose(cmn, acc["min"], atol=1e-3) and np.allclose(cmx, acc["max"], atol=1e-3), \
            f"accessor {acc_idx} read mismatch: got [{cmn},{cmx}] declared [{acc['min']},{acc['max']}]"
    return out


def accessor_is_shared(js, acc_idx):
    """ accessor 被多处引用则禁止原位改写。"""
    refs = 0
    for mesh in js.get("meshes", []):
        for prim in mesh.get("primitives", []):
            refs += sum(1 for v in prim.get("attributes", {}).values() if v == acc_idx)
            refs += 1 if prim.get("indices") == acc_idx else 0
    return refs > 1


def bone_maps(js):
    """返回 joint_slot -> bone_name, bone_name -> joint_slot（针对唯一 skin）。"""
    skin = js["skins"][0]
    nodes = js["nodes"]
    slot2name = {s: nodes[ni].get("name", f"node{ni}") for s, ni in enumerate(skin["joints"])}
    return slot2name, {n: s for s, n in slot2name.items()}


def joint_global_origins(js):
    """合成每个关节的全局平移（glTF 世界系 = 网格系，Aster_Armature/Body 节点为恒等）。"""
    nodes = js["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i

    def quat_mat(q):
        x, y, z, w = q
        return np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

    cache = {}

    def glob(i):
        if i in cache:
            return cache[i]
        n = nodes[i]
        M = np.eye(4)
        M[:3, :3] = quat_mat(n.get("rotation", [0, 0, 0, 1])) @ np.diag(n.get("scale", [1, 1, 1]))
        M[:3, 3] = n.get("translation", [0, 0, 0])
        if i in parent:
            M = glob(parent[i]) @ M
        cache[i] = M
        return M

    skin = js["skins"][0]
    return {s: glob(ni)[:3, 3].copy() for s, ni in enumerate(skin["joints"])}


def print_hierarchy(js):
    nodes = js["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    name = lambda i: nodes[i].get("name", f"#{i}")

    def tr(i):
        n = nodes[i]
        t = n.get("translation", [0, 0, 0])
        return "T%.3f,%.3f,%.3f" % tuple(t)

    def walk(i, depth):
        print("  " * depth + f"{name(i)}  [{i}] {tr(i)}")
        for c in nodes[i].get("children", []):
            walk(c, depth + 1)
    roots = [i for i in range(len(nodes)) if i not in parent]
    for r in roots:
        walk(r, 0)


def analyze(js, bin_data, verbose=True):
    mesh = next(m for m in js["meshes"] if m.get("name", "").startswith("tripo_mesh")) \
        if any(m.get("name", "").startswith("tripo_mesh") for m in js["meshes"]) else js["meshes"][0]
    prim = mesh["primitives"][0]
    attrs = prim["attributes"]
    pos = read_accessor(js, bin_data, attrs["POSITION"])
    joints = read_accessor(js, bin_data, attrs["JOINTS_0"])
    weights = read_accessor(js, bin_data, attrs["WEIGHTS_0"])
    slot2name, name2slot = bone_maps(js)
    if verbose:
        print(f"verts={pos.shape[0]}  y range=[{pos[:,1].min():.3f},{pos[:,1].max():.3f}]  "
              f"x range=[{pos[:,0].min():.3f},{pos[:,0].max():.3f}]  z range=[{pos[:,2].min():.3f},{pos[:,2].max():.3f}]")
        # 侧向约定自检：L_Foot / R_Foot 权重顶点的平均 X
        for side in ("L", "R"):
            b = side + "_Foot"
            if b in name2slot:
                s = name2slot[b]
                m = np.any(joints == s, axis=1) & np.any(weights > 0.05, axis=1)
                if m.any():
                    print(f"  side-check {b}: n={m.sum()} avg_x={pos[m,0].mean():+.4f}")
        # 污染统计
        lower = pos[:, 1] < LOWER_Y_MAX
        lset = {name2slot["L_" + b] for b in LEG_BONES if "L_" + b in name2slot}
        rset = {name2slot["R_" + b] for b in LEG_BONES if "R_" + b in name2slot}
        # 逐顶点精确统计
        def contaminated(mask, bad_slots):
            cnt = 0
            for i in np.where(mask)[0]:
                if any(weights[i, k] > 1e-4 and int(joints[i, k]) in bad_slots for k in range(4)):
                    cnt += 1
            return cnt
        n_shoe = contaminated(lower & (pos[:, 0] < 0), rset) + contaminated(lower & (pos[:, 0] > 0), lset)
        hair = (pos[:, 1] > HAIR_Y_MIN) & (pos[:, 1] < HAIR_Y_MAX) & (pos[:, 2] > HAIR_Z_MIN)
        clear_slots = {name2slot[b] for b in HAIR_CLEAR_BONES if b in name2slot}
        n_hair = contaminated(hair, clear_slots)
        print(f"  lower-body y<{LOWER_Y_MAX}: {lower.sum()} verts, cross-side contaminated: {n_shoe}")
        print(f"  hair band: {hair.sum()} verts, torso-contaminated: {n_hair}")
        wsum = weights.sum(axis=1)
        print(f"  weight sum: min={wsum.min():.4f} max={wsum.max():.4f} (unnormalized verts={int((np.abs(wsum-1)>1e-3).sum())})")
    return pos, joints, weights, slot2name, name2slot


def operate(js, bin_data, path):
    pos, joints, weights, slot2name, name2slot = analyze(js, bin_data, verbose=True)
    n = pos.shape[0]
    changed_joints = np.zeros(n, dtype=bool)
    stats = {"cloth_fixed": 0, "shoe_fixed": 0, "shoe_replant": 0,
             "hair_fixed": 0, "hair_nohead": 0, "seam_deleted": 0}
    # 关节全局原点（回植择近用）
    origins = joint_global_origins(js)

    def norm(i):
        s = weights[i].sum()
        if s > 1e-6:
            weights[i] /= s

    def set_slot(i, k, bone, w):
        joints[i, k] = name2slot[bone]
        weights[i, k] = w

    def find_slot(i, bone):
        s = name2slot[bone]
        for k in range(4):
            if int(joints[i, k]) == s:
                return k
        return -1

    def weakest_of(i, zeroed):
        return max(zeroed, key=lambda k: -weights[i, k]) if zeroed else 0

    # --- 0) 桥接三角切除：跨 {躯干,左腿,右腿} 分支且静置 max边长>BRIDGE_MIN_EDGE
    #        的三角形（裙布被自动蒙皮分给腿骨），其腿骨主导顶点一律改挂 Hip=1.0，
    #        让裙布随骨盆刚体化。V8 真实步幅（大腿 ±30°）下，任何腿骨污染的裙布
    #        都会被撕出半米巨面。
    #        执行两轮：0a 在侧隔离/回植之前，0b 在其后（回植会给接缝顶点重新带回
    #        腿权重、复活桥接，必须收尾再切一次）。发带区(0.82<y<1.32 且 z>0.045)
    #        豁免转换——该区由长发→Head 规则全权接管。
    leg_l = {name2slot[b] for b in ("L_Thigh", "L_ThighTwist01", "L_ThighTwist02",
            "L_Calf", "L_CalfTwist01", "L_CalfTwist02", "L_Foot", "L_ToeBase")
            if b in name2slot}
    leg_r = {name2slot[b] for b in ("R_Thigh", "R_ThighTwist01", "R_ThighTwist02",
            "R_Calf", "R_CalfTwist01", "R_CalfTwist02", "R_Foot", "R_ToeBase")
            if b in name2slot}
    tris = read_accessor(js, bin_data, js["meshes"][0]["primitives"][0]["indices"]) \
        .astype(int).ravel().reshape(-1, 3)
    edge2 = BRIDGE_MIN_EDGE ** 2
    hair_band_v = (pos[:, 1] > HAIR_Y_MIN) & (pos[:, 1] < HAIR_Y_MAX) & (pos[:, 2] > HAIR_Z_MIN)
    dom = ["T"] * n

    # --- -1) 距离布料剥离：裙布/下摆整体被自动蒙皮分给腿骨（距腿链>0.15 区域
    #     85% 顶点带腿权重、均值 0.73），仅切桥接救不了「纯腿权重三角片离岛」，
    #     迈步时裙摆会整体炸裂。凡 y<0.95、非发带、距双腿链>CLOTH_DIST、
    #     且距双臂链>ARM_GUARD_DIST（保护袖口）的带腿权重顶点，一律改挂 Hip=1.0。
    def seg_dist(pts):
        """各顶点到折线链（骨原点序列）的最近距离，返回 (n,) 数组"""
        out = np.full(n, 1e9)
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a
            denom = float(np.dot(ab, ab)) + 1e-9
            t = np.clip(((pos - a) @ ab) / denom, 0.0, 1.0)
            out = np.minimum(out, np.linalg.norm(pos - (a + t[:, None] * ab), axis=1))
        return np.minimum(out, np.linalg.norm(pos - pts[-1], axis=1))

    def chain_points(bone_names):
        pts = []
        for bn in bone_names:
            if bn in name2slot:
                o = origins[name2slot[bn]]
                pts.append(o[:3])
        return np.array(pts)

    l_leg_pts = chain_points(["L_Thigh", "L_Calf", "L_Foot"])
    r_leg_pts = chain_points(["R_Thigh", "R_Calf", "R_Foot"])
    l_arm_pts = chain_points(["L_Clavicle", "L_Upperarm", "L_Forearm", "L_Hand"])
    r_arm_pts = chain_points(["R_Clavicle", "R_Upperarm", "R_Forearm", "R_Hand"])
    d_leg = np.minimum(seg_dist(l_leg_pts), seg_dist(r_leg_pts))
    d_arm = np.minimum(seg_dist(l_arm_pts), seg_dist(r_arm_pts))

    has_leg_w = np.zeros(n, dtype=bool)
    leg_slots = leg_l | leg_r
    for i in range(n):
        for k in range(4):
            if weights[i, k] > 0.05 and int(joints[i, k]) in leg_slots:
                has_leg_w[i] = True
                break

    cloth_mask = (pos[:, 1] > SKIRT_Y_MIN) & (pos[:, 1] < 0.95) & (~hair_band_v) & \
                 (d_leg > CLOTH_DIST) & (d_arm > ARM_GUARD_DIST) & has_leg_w
    for i in np.where(cloth_mask)[0]:
        for k in range(4):
            weights[i, k] = 0.0
        set_slot(i, 0, "Hip", 1.0)
        changed_joints[i] = True
    print("== 距离布料剥离: %d 个裙布/下摆顶点改挂 Hip ==" % int(cloth_mask.sum()))
    stats["cloth_fixed"] += int(cloth_mask.sum())


    def dom_branch(i):
        bw, bb = 0.0, "T"
        for k in range(4):
            w = weights[i, k]
            if w > bw:
                s = int(joints[i, k])
                bw = w
                bb = "L" if s in leg_l else ("R" if s in leg_r else "T")
        return bb

    def count_bridges():
        cnt = 0
        for t in tris:
            a, b, c = int(t[0]), int(t[1]), int(t[2])
            if len({dom[a], dom[b], dom[c]} & {"T", "L", "R"}) < 2:
                continue
            m2 = max(float(np.sum((pos[a] - pos[b]) ** 2)),
                     float(np.sum((pos[b] - pos[c]) ** 2)),
                     float(np.sum((pos[c] - pos[a]) ** 2)))
            miny = min(pos[a, 1], pos[b, 1], pos[c, 1])
            if m2 > edge2 and SKIRT_Y_MIN < miny < 0.95:
                cnt += 1
        return cnt

    def shoe_seam_excision():
        ## 鞋区(y<SKIRT_Y_MIN)的「纯左右腿跨接」接缝三角删除（dom 集合恰为 {L,R}）：
        ## 双鞋静置近乎贴合（足骨距 3cm），纯跨鞋桥在步幅分开 40cm 时拉成白色拖带。
        ## 【铁律】含躯干主导顶点（T）的跨接三角一律保留——那是腿皮+髋骨混合权重的
        ## 正常皮肤，v6 曾误删导致前腿平头豁口/悬垂断条。
        dom[:] = [dom_branch(i) for i in range(n)]
        keep = np.ones(len(tris), dtype=bool)
        deleted = 0
        for ti in range(len(tris)):
            t = tris[ti]
            a, b, c = int(t[0]), int(t[1]), int(t[2])
            if {dom[a], dom[b], dom[c]} != {"L", "R"}:
                continue
            m2 = max(float(np.sum((pos[a] - pos[b]) ** 2)),
                     float(np.sum((pos[b] - pos[c]) ** 2)),
                     float(np.sum((pos[c] - pos[a]) ** 2)))
            if m2 > SEAM_MIN_EDGE ** 2 and min(pos[a, 1], pos[b, 1], pos[c, 1]) < SKIRT_Y_MIN:
                keep[ti] = False
                deleted += 1
        if deleted == 0:
            print("== 鞋区接缝三角: 无需删除 ==")
            return None
        acc_idx = js["meshes"][0]["primitives"][0]["indices"]
        acc = js["accessors"][acc_idx]
        assert not accessor_is_shared(js, acc_idx), "indices accessor shared, cannot compact"
        assert not acc.get("sparse"), "sparse indices unsupported"
        kept = tris[keep].ravel().astype(np.int64)
        np_dt = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[acc["componentType"]]
        raw = kept.astype(np_dt).tobytes()
        bv2 = js["bufferViews"][acc["bufferView"]]
        base = bv2.get("byteOffset", 0) + acc.get("byteOffset", 0)
        assert len(raw) <= bv2.get("byteLength", len(raw) + 1), "kept indices exceed bufferView"
        bin_data[base:base + len(raw)] = raw
        acc["count"] = int(len(kept))
        acc.pop("min", None)
        acc.pop("max", None)
        bv2["byteLength"] = len(raw)
        print("== 鞋区接缝三角删除: %d 个（索引压缩写回 %d -> %d 三角）==" %
              (deleted, len(tris), len(kept) // 3))
        stats["seam_deleted"] = deleted
        return tris[keep]

    def bridge_excision(tag):
        dom[:] = [dom_branch(i) for i in range(n)]
        print("== 桥接切除%s前: %d 个跨分支撕裂三角 ==" % (tag, count_bridges()))
        total = 0
        # 转换是链式传播（先转的顶点会让邻居三角下一轮才构成跨分支），
        # 4 轮在裙摆褶皱深处不够收敛，12 轮封顶直至 converted==0
        for _ in range(12):
            converted = 0
            for t in tris:
                a, b, c = int(t[0]), int(t[1]), int(t[2])
                if len({dom[a], dom[b], dom[c]} & {"T", "L", "R"}) < 2:
                    continue
                m2 = max(float(np.sum((pos[a] - pos[b]) ** 2)),
                         float(np.sum((pos[b] - pos[c]) ** 2)),
                         float(np.sum((pos[c] - pos[a]) ** 2)))
                miny = min(pos[a, 1], pos[b, 1], pos[c, 1])
                if m2 <= edge2 or miny <= SKIRT_Y_MIN or miny >= 0.95:
                    continue
                for v in (a, b, c):
                    if dom[v] in ("L", "R") and not hair_band_v[v]:
                        for k in range(4):
                            weights[v, k] = 0.0
                        set_slot(v, 0, "Hip", 1.0)
                        dom[v] = "T"
                        changed_joints[v] = True
                        converted += 1
            total += converted
            if converted == 0:
                break
        print("== 桥接切除%s后: %d 个残留（本轮 cloth_fixed=%d）==" %
              (tag, count_bridges(), total))
        return total

    new_tris = shoe_seam_excision()
    if new_tris is not None:
        tris = new_tris
    stats["cloth_fixed"] += bridge_excision("0a")

    for i in range(n):
        x, y, z = pos[i]
        zeroed = []
        # --- 1) 腿部全程单侧隔离（y<SIDE_Y_MAX）---
        if y < SIDE_Y_MAX:
            bad_side = "R" if x < 0 else ("L" if x > 0 else None)
            if bad_side:
                bad = {name2slot[bad_side + "_" + b] for b in LEG_BONES if bad_side + "_" + b in name2slot}
                hit = False
                for k in range(4):
                    if weights[i, k] > 1e-4 and int(joints[i, k]) in bad:
                        weights[i, k] = 0.0
                        zeroed.append(k)
                        hit = True
                if hit:
                    if weights[i].sum() <= 1e-4:
                        # 回植择近（分段铁律）：踝/鞋饰（y<0.45）仅限同侧 Calf/Foot，
                        # 绝不回植 Thigh（跨关节回植会在迈步时拉扯踝部装饰撕裂面）；
                        # 大腿皮肤（y≥0.45）回植同侧 Thigh 组。
                        side = "L" if x < 0 else "R"
                        pool = REPLANT_BONES if y < LOWER_Y_MAX else \
                            ("Thigh", "ThighTwist01", "ThighTwist02")
                        best_bone, best_d = None, 1e9
                        for b in pool:
                            bn = f"{side}_{b}"
                            if bn in name2slot:
                                d = float(np.sum((origins[name2slot[bn]] - pos[i]) ** 2))
                                if d < best_d:
                                    best_bone, best_d = bn, d
                        set_slot(i, weakest_of(i, zeroed or [0]), best_bone, 1.0)
                        stats["shoe_replant"] += 1
                        stats[f"replant->{best_bone}"] = stats.get(f"replant->{best_bone}", 0) + 1
                    else:
                        norm(i)
                    stats["shoe_fixed"] += 1
                    changed_joints[i] = bool(zeroed)
        # --- 2) 长发剥离躯干 → Head ---
        if HAIR_Y_MIN < y < HAIR_Y_MAX and z > HAIR_Z_MIN:
            bad = {name2slot[b] for b in HAIR_CLEAR_BONES if b in name2slot}
            cleared = 0.0
            zeroed2 = []
            for k in range(4):
                if weights[i, k] > 1e-4 and int(joints[i, k]) in bad:
                    cleared += weights[i, k]
                    weights[i, k] = 0.0
                    zeroed2.append(k)
            if cleared > 1e-4:
                hk = find_slot(i, "Head")
                if hk >= 0:
                    weights[i, hk] += cleared
                elif zeroed2:
                    set_slot(i, zeroed2[0], "Head", cleared)
                    changed_joints[i] = True
                else:
                    set_slot(i, int(np.argmax(weights[i])), "Head", cleared)
                    changed_joints[i] = True
                norm(i)
                stats["hair_fixed"] += 1
                if hk < 0:
                    stats["hair_nohead"] += 1

    # --- 0b) 收尾再切一次桥：侧隔离回植会给接缝顶点带回腿权重、复活桥接 ---
    stats["cloth_fixed"] += bridge_excision("0b")
    # --- 0c) 鞋区接缝终删：回植会把跨鞋接缝三角重新接回来，必须在收敛后补一刀 ---
    new_tris = shoe_seam_excision()
    if new_tris is not None:
        tris = new_tris

    # 写回：定位 JOINTS_0 / WEIGHTS_0 访问器字节并原位覆写
    prim = js["meshes"][0]["primitives"][0]
    for acc_idx, arr, fmt_code in ((prim["attributes"]["JOINTS_0"], joints, "B"),
                                   (prim["attributes"]["WEIGHTS_0"], weights, "f")):
        acc = js["accessors"][acc_idx]
        assert not accessor_is_shared(js, acc_idx), f"accessor {acc_idx} is shared, abort"
        assert not acc.get("sparse"), "sparse accessor unsupported"
        bv = js["bufferViews"][acc["bufferView"]]
        assert not bv.get("byteStride"), "strided skin accessor unsupported"
        base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        ncomp = NCOMP[acc["type"]]
        raw = arr.astype(fmt_code if fmt_code == "f" else np.uint8)
        bin_data[base:base + raw.nbytes] = raw.tobytes()

    out = rebuild_glb(js, bin_data)
    with open(path, "wb") as f:
        f.write(out)
    replant_detail = " ".join(f"{k}={v}" for k, v in sorted(stats.items()) if k.startswith("replant->")) or "none"
    print(f"\n== 手术完成: cloth_fixed={stats['cloth_fixed']}, seam_deleted={stats['seam_deleted']}, "
          f"shoe_fixed={stats['shoe_fixed']} (replant={stats['shoe_replant']}: {replant_detail}), "
          f"hair_fixed={stats['hair_fixed']} (no-Head-slot replant={stats['hair_nohead']}) ==")

    # --- 复检：从磁盘重读 ---
    js2, bin2 = parse_glb(path)
    pos2, joints2, weights2, _, name2slot2 = analyze(js2, bin2, verbose=False)
    lower = pos2[:, 1] < SIDE_Y_MAX
    hair = (pos2[:, 1] > HAIR_Y_MIN) & (pos2[:, 1] < HAIR_Y_MAX) & (pos2[:, 2] > HAIR_Z_MIN)
    lset = {name2slot2["L_" + b] for b in LEG_BONES if "L_" + b in name2slot2}
    rset = {name2slot2["R_" + b] for b in LEG_BONES if "R_" + b in name2slot2}
    clear = {name2slot2[b] for b in HAIR_CLEAR_BONES if b in name2slot2}
    resid_shoe = resid_hair = bad_norm = 0
    for i in range(n):
        wsum = weights2[i].sum()
        if abs(wsum - 1.0) > 1e-3:
            bad_norm += 1
        if lower[i]:
            bad = rset if pos2[i, 0] < 0 else lset
            if any(weights2[i, k] > 1e-4 and int(joints2[i, k]) in bad for k in range(4)):
                resid_shoe += 1
        if hair[i] and any(weights2[i, k] > 1e-4 and int(joints2[i, k]) in clear for k in range(4)):
            resid_hair += 1
    # 桥接三角残留复核（T/L/R 跨分支且 max边长>0.02）
    leg_l2 = {name2slot2[b] for b in ("L_Thigh", "L_ThighTwist01", "L_ThighTwist02",
              "L_Calf", "L_CalfTwist01", "L_CalfTwist02", "L_Foot", "L_ToeBase") if b in name2slot2}
    leg_r2 = {name2slot2[b] for b in ("R_Thigh", "R_ThighTwist01", "R_ThighTwist02",
              "R_Calf", "R_CalfTwist01", "R_CalfTwist02", "R_Foot", "R_ToeBase") if b in name2slot2}
    tris2 = read_accessor(js2, bin2, js2["meshes"][0]["primitives"][0]["indices"]) \
        .astype(int).ravel().reshape(-1, 3)

    def dom2(i):
        bw, bb = 0.0, "T"
        for k in range(4):
            w = weights2[i, k]
            if w > bw:
                s = int(joints2[i, k])
                bw = w
                bb = "L" if s in leg_l2 else ("R" if s in leg_r2 else "T")
        return bb

    dom_all2 = [dom2(i) for i in range(n)]
    resid_bridge = 0
    resid_seam = 0
    for t in tris2:
        a, b, c = int(t[0]), int(t[1]), int(t[2])
        dset = {dom_all2[a], dom_all2[b], dom_all2[c]}
        if len(dset & {"T", "L", "R"}) < 2:
            continue
        m2 = max(float(np.sum((pos2[a] - pos2[b]) ** 2)),
                 float(np.sum((pos2[b] - pos2[c]) ** 2)),
                 float(np.sum((pos2[c] - pos2[a]) ** 2)))
        miny = min(pos2[a, 1], pos2[b, 1], pos2[c, 1])
        if m2 <= edge2:
            continue
        if miny < SKIRT_Y_MIN:
            # 鞋区只审纯左右腿跨接（与删除口径一致）；含 T 的是正常皮肤
            if dset == {"L", "R"}:
                resid_seam += 1
        elif miny < 0.95:
            # 发带区豁免语义对齐：腿主导顶点全部位于发带内的桥接由长发规则管辖，不计残桥
            leg_verts = [v for v in (a, b, c) if dom_all2[v] in ("L", "R")]
            if leg_verts and all(hair[i] for i in leg_verts):
                continue
            resid_bridge += 1
    ok = resid_shoe == 0 and resid_hair == 0 and bad_norm == 0 and resid_bridge == 0 and resid_seam == 0
    print(f"== 复检: 跨侧残留={resid_shoe}  长发躯干残留={resid_hair}  未归一顶点={bad_norm}  "
          f"桥接三角残留={resid_bridge}  鞋区接缝残留={resid_seam}  -> {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    path = sys.argv[1]
    js, bin_data = parse_glb(path)
    if "--hierarchy" in sys.argv:
        print_hierarchy(js)
        sys.exit(0)
    print(f"== {path} 手术前分析 ==")
    if "--apply" in sys.argv:
        ok = operate(js, bytearray(bin_data), path)
        sys.exit(0 if ok else 1)
    else:
        analyze(js, bin_data, verbose=True)
        print("\n(dry-run，加 --apply 执行手术)")
