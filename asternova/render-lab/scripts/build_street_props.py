# AsterNova - Procedural street props builder (Blender 5.2 bpy, headless).
# Tier 3 街景高频小道具程序化建模:
#   ac_unit_single / ac_unit_double  外挂空调室外机(百叶+格栅风扇+支架+包扎铜管)
#   utility_pole                     水泥电线杆(横担+绝缘子+变压器箱+踏钉)
#   trash_station_4bin               日式四分类垃圾站(钢架+彩色盖)
#   traffic_cone                     道路警示锥桶
# 全部硬表面倒角工艺(边缘高光), 材质仅命名底色(GLB baseColorFactor 直出,
# Godot 侧由 props_npr_setup.gd 重绑 toon_prop 赛璐璐)。
# Run:
#   blender.exe -b --factory-startup -P scripts/build_street_props.py
# 原点约定:
#   AC 机 = 背板底边中点(墙面贴合点), 电线杆/垃圾站/锥桶 = 底面中心, 全部 +Z 朝上。

import math
import os
import sys

import bmesh
from mathutils import Vector

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "props")

# 命名底色板 (线性空间直出, Godot toon_prop 再做赛璐璐受光)
PALETTE = {
    "Shell":      (0.72, 0.72, 0.70, 1),   # 米白烤漆机壳
    "ShellTop":   (0.66, 0.66, 0.64, 1),
    "Grille":     (0.16, 0.17, 0.19, 1),   # 深灰格栅
    "Fan":        (0.10, 0.11, 0.12, 1),
    "Copper":     (0.45, 0.24, 0.12, 1),   # 包扎前铜管
    "Tape":       (0.78, 0.76, 0.70, 1),   # 白色包扎带
    "Steel":      (0.42, 0.43, 0.45, 1),   # 镀锌支架
    "Rust":       (0.30, 0.19, 0.11, 1),   # 支架锈迹
    "Concrete":   (0.52, 0.53, 0.55, 1),   # 电线杆水泥
    "MetalDark":  (0.16, 0.17, 0.18, 1),   # 变压器箱/横担铁件
    "Insulator":  (0.20, 0.23, 0.28, 1),   # 绝缘子深灰蓝
    "BinBody":    (0.68, 0.69, 0.71, 1),   # 垃圾桶浅灰 body
    "LidBlue":    (0.20, 0.36, 0.52, 1),
    "LidGreen":   (0.22, 0.44, 0.30, 1),
    "LidYellow":  (0.72, 0.58, 0.16, 1),
    "LidGray":    (0.38, 0.40, 0.42, 1),
    "FrameSteel": (0.30, 0.31, 0.33, 1),
    "ConeOrange": (0.78, 0.28, 0.08, 1),
    "ConeWhite":  (0.82, 0.82, 0.80, 1),
    "Rubber":     (0.09, 0.09, 0.10, 1),
}


def _clean_scene():
    bpy = __import__("bpy")
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _set_input(node, names, value):
    for key in names:
        sock = node.inputs.get(key)
        if sock is not None:
            sock.default_value = value
            return


def _mat(name):
    bpy = __import__("bpy")
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:  # 5.x 节点名兜底
            bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        _set_input(bsdf, ("Base Color", "Color"), PALETTE[name])
        _set_input(bsdf, ("Roughness",), 0.55)
        _set_input(bsdf, ("Metallic",), 0.0)
        if name in ("Copper", "Steel", "MetalDark", "FrameSteel", "Rust"):
            _set_input(bsdf, ("Metallic",), 0.65)
            _set_input(bsdf, ("Roughness",), 0.45)
    return m


def _link(obj, mat_name):
    obj.data.materials.append(_mat(mat_name))


def _box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.006, seg=2):
    """Axis-aligned beveled box centered at loc."""
    bpy = __import__("bpy")
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    # primitive_cube_add(size=1) 全边长 1 (±0.5), 缩放 = 目标尺寸
    obj.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        _bevel(obj, bevel, seg)
    if mat:
        _link(obj, mat)
    return obj


def _cyl(name, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), verts=24, mat=None,
         cap=True, bevel=0.004):
    bpy = __import__("bpy")
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot,
                                        end_fill_type="NGON" if cap else "NONE")
    obj = bpy.context.active_object
    obj.name = name
    if bevel > 0:
        _bevel(obj, bevel, 2)
    if mat:
        _link(obj, mat)
    return obj


def _torus(name, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy = __import__("bpy")
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=loc, rotation=rot,
                                     major_segments=28, minor_segments=10)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        _link(obj, mat)
    return obj


def _bevel(obj, width, segments=2):
    bpy = __import__("bpy")
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(48)
    mod.harden_normals = False
    bpy.ops.object.modifier_apply(modifier=mod.name)


def _smooth_by_angle(obj, angle_deg=32):
    bpy = __import__("bpy")
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        pass  # 回退 flat: 倒角面片仍能吃光


def _join(objs, name):
    bpy = __import__("bpy")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _tri_count(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    n = len(bm.calc_loop_triangles())
    bm.free()
    return n


def _export(objs, filename):
    bpy = __import__("bpy")
    root = __import__("bpy").data.objects.new(filename.replace(".glb", ""), None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        o.parent = root
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.abspath(os.path.join(OUT_DIR, filename))
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB",
                              use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT")
    tris = sum(_tri_count(o) for o in objs)
    print("[props] %s -> %s (%d tris)" % (filename, path, tris))
    for o in objs:
        o.parent = None
    bpy.data.objects.remove(root)


# ---------------------------------------------------------------- AC 室外机
def build_ac_unit(double=False):
    bpy = __import__("bpy")
    w = 0.95 if double else 0.80          # 机壳宽
    h = 0.62 if double else 0.56
    d = 0.36 if double else 0.30
    parts = []
    # 主机壳: 背板贴 z=0, 机身向 +y 伸出(Blender Z-up, 导出转 Y-up)
    shell = _box("Shell", (w, d, h), loc=(0, d / 2, h / 2), mat="Shell", bevel=0.010)
    parts.append(shell)
    # 顶盖沿 (深一档的顶部面板, 增加体块分层)
    parts.append(_box("ShellTop", (w + 0.012, d + 0.012, 0.035),
                      loc=(0, d / 2, h - 0.016), mat="ShellTop", bevel=0.008))
    # 前面板风扇凹陷 + 格栅圈 + 扇叶 (机壳正面 = 远离墙面一侧, Blender +Y)
    fans = [(-w / 4, 0.115)] if not double else [(-w / 4 + 0.02, 0.115), (w / 4 - 0.02, 0.115)]
    fr = 0.155
    for i, (fx, fy) in enumerate(fans):
        parts.append(_cyl("FanRecess%d" % i, fr, 0.02,
                          loc=(fx, d - 0.008, h / 2), rot=(math.pi / 2, 0, 0),
                          verts=28, mat="Grille", bevel=0.003))
        for ring in (0.055, 0.100, 0.140):
            parts.append(_torus("FanRing%d_%.0f" % (i, ring * 1000), ring, 0.007,
                                loc=(fx, d + 0.006, h / 2),
                                rot=(math.pi / 2, 0, 0), mat="Grille"))
        parts.append(_cyl("FanHub%d" % i, 0.028, 0.024,
                          loc=(fx, d + 0.010, h / 2), rot=(math.pi / 2, 0, 0),
                          verts=16, mat="Fan", bevel=0.003))
        for b in range(3):
            ang = b * (2 * math.pi / 3) + 0.4
            blade = _box("FanBlade%d_%d" % (i, b), (0.115, 0.012, 0.055),
                         loc=(fx + math.cos(ang) * 0.075, d + 0.014,
                              h / 2 + math.sin(ang) * 0.075),
                         rot=(0, -0.45, ang), mat="Fan", bevel=0.002)
            parts.append(blade)
        # 侧面防护格栅圈 (罩住风扇外缘)
        parts.append(_torus("FanGuard%d" % i, fr + 0.012, 0.008,
                            loc=(fx, d + 0.016, h / 2),
                            rot=(math.pi / 2, 0, 0), mat="Grille"))
    # 侧口百叶 (出风格栅, 机壳两侧各 5 片斜片)
    lx = w / 2 - 0.002
    for s in (-1, 1):
        for i in range(5):
            ly = 0.06 + i * 0.052
            parts.append(_box("Louvre_%d_%d" % (s, i), (0.016, 0.05, d - 0.10),
                              loc=(s * lx, ly, h / 2), rot=(0, s * 0.5, 0),
                              mat="Grille", bevel=0.002))
    # 冷凝翅片背板 (贴墙侧深色进风格栅, 微凸出分层)
    parts.append(_box("CoilFin", (w - 0.06, 0.02, h - 0.10),
                      loc=(0, 0.006, h / 2 - 0.02), mat="Grille", bevel=0.004))
    # 铜管束 + 白色包扎带 (右下侧伸出, 两弯)
    px, pz = w / 2 - 0.07, 0.10
    pipe_curve = __import__("bpy").data.curves.new("PipeCurve", "CURVE")
    pipe_curve.dimensions = "3D"
    pipe_curve.bevel_depth = 0.014
    pipe_curve.bevel_resolution = 3
    sp = pipe_curve.splines.new("BEZIER")
    sp.bezier_points.add(2)
    pts = [(px, d - 0.02, pz), (px + 0.05, d + 0.10, pz + 0.02),
           (px + 0.10, d + 0.16, pz + 0.24), (px + 0.095, d + 0.02, pz + 0.40)]
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    pipe = __import__("bpy").data.objects.new("CopperPipe", pipe_curve)
    bpy.context.scene.collection.objects.link(pipe)
    pipe.data.materials.append(_mat("Copper"))
    parts.append(pipe)
    parts.append(_cyl("PipeTape", 0.023, 0.11,
                      loc=(px + 0.098, d + 0.09, pz + 0.33),
                      rot=(0.12, 0, 0), verts=14, mat="Tape", bevel=0.003))
    # 冷凝水滴管 (细管向左下)
    drain = _cyl("DrainPipe", 0.007, 0.30, loc=(-w / 2 + 0.03, d - 0.05, -0.06),
                 rot=(0, math.radians(18), 0), verts=10, mat="Tape", bevel=0.0)
    parts.append(drain)
    # 外挂镀锌支架 (两只 L 型 + 斜撑, 带锈迹垫木与螺栓)
    for s in (-1, 1):
        bx = s * (w / 2 - 0.09)
        parts.append(_box("BracketArm_%d" % s, (0.05, d + 0.10, 0.05),
                          loc=(bx, d / 2 + 0.02, -0.06), mat="Steel", bevel=0.004))
        parts.append(_box("BracketVert_%d" % s, (0.05, 0.04, 0.34),
                          loc=(bx, d + 0.10, -0.24), mat="Steel", bevel=0.004))
        parts.append(_box("BracketStrut_%d" % s, (0.035, 0.03, 0.38),
                          loc=(bx, d + 0.06, -0.24),
                          rot=(math.radians(-38), 0, 0), mat="Rust", bevel=0.003))
        parts.append(_cyl("BracketBolt_%d" % s, 0.011, 0.03,
                          loc=(bx, d + 0.125, -0.36), rot=(math.pi / 2, 0, 0),
                          verts=10, mat="MetalDark", bevel=0.002))
    root_name = "AC_Unit_Double" if double else "AC_Unit_Single"
    obj = _join(parts, root_name)
    _smooth_by_angle(obj)
    return [obj]


# ---------------------------------------------------------------- 电线杆
def build_utility_pole():
    parts = []
    # 锥形水泥杆: 底 r0.17 顶 r0.12, 高 8.5 (原点底面中心)
    bpy = __import__("bpy")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=18,
                          radius1=0.17, radius2=0.12, depth=8.5)
    mesh = bpy.data.meshes.new("PoleBody")
    bm.to_mesh(mesh)
    bm.free()
    pole = bpy.data.objects.new("PoleBody", mesh)
    bpy.context.scene.collection.objects.link(pole)
    pole.location = (0, 0, 4.25)
    _link(pole, "Concrete")
    parts.append(pole)
    # 基础护墩
    parts.append(_cyl("PoleBase", 0.24, 0.5, loc=(0, 0, 0.25), verts=18,
                      mat="Concrete", bevel=0.01))
    # 踏钉 (两侧交错 4 颗)
    for i in range(4):
        s = 1 if i % 2 == 0 else -1
        parts.append(_cyl("StepBolt_%d" % i, 0.014, 0.10,
                          loc=(s * 0.16, 0, 1.0 + (i // 2) * 0.45),
                          rot=(0, math.radians(90), 0), verts=8,
                          mat="MetalDark", bevel=0.002))
    # 横担 (沿本地 X, 高 7.6) + 斜撑
    parts.append(_box("Crossarm", (2.0, 0.07, 0.12), loc=(0, 0, 7.62),
                      mat="MetalDark", bevel=0.006))
    for s in (-1, 1):
        parts.append(_box("CrossarmBrace_%d" % s, (0.03, 0.03, 0.5),
                          loc=(s * 0.55, 0, 7.36), rot=(0, s * 0.5, 0),
                          mat="MetalDark", bevel=0.003))
        # 绝缘子 (横担两端 + 中间): 颈杆 + 双裙瓷瓶
        for k, px in enumerate((s * 0.78, )):
            parts.append(_cyl("Pin_%d_%d" % (s, k), 0.012, 0.16,
                              loc=(px, 0, 7.76), verts=10, mat="MetalDark",
                              bevel=0.002))
            parts.append(_cyl("InsulatorSkirt1_%d_%d" % (s, k), 0.055, 0.045,
                              loc=(px, 0, 7.90), verts=14, mat="Insulator",
                              bevel=0.006))
            parts.append(_cyl("InsulatorSkirt2_%d_%d" % (s, k), 0.042, 0.04,
                              loc=(px, 0, 7.97), verts=14, mat="Insulator",
                              bevel=0.005))
            parts.append(_cyl("InsulatorCap_%d_%d" % (s, k), 0.020, 0.035,
                              loc=(px, 0, 8.02), verts=10, mat="Insulator",
                              bevel=0.003))
    # 变压器箱 (柱上式圆罐 + 4 片散热翅 + 顶部套管, 挂 y 5.4~6.6)
    ty = 5.95
    parts.append(_cyl("TransformerCan", 0.24, 1.05, loc=(0.36, 0, ty), verts=22,
                      mat="MetalDark", bevel=0.012))
    parts.append(_cyl("TransformerCap", 0.255, 0.06, loc=(0.36, 0, ty + 0.55),
                      verts=22, mat="MetalDark", bevel=0.008))
    for i in range(4):
        ang = i * math.pi / 2 + math.pi / 4
        parts.append(_box("TransformerFin_%d" % i, (0.02, 0.30, 0.85),
                          loc=(0.36 + math.cos(ang) * 0.255,
                               math.sin(ang) * 0.255, ty),
                          rot=(0, 0, ang), mat="MetalDark", bevel=0.004))
    for k in range(2):
        parts.append(_cyl("TransformerBushing_%d" % k, 0.028, 0.16,
                          loc=(0.36 - 0.07 + k * 0.14, 0, ty + 0.66), verts=10,
                          mat="Insulator", bevel=0.004))
    # 挂箍 (变压器与杆身连接带)
    parts.append(_torus("TransformerBand", 0.27, 0.02,
                        loc=(0.18, 0, ty), rot=(math.pi / 2, 0, 0), mat="MetalDark"))
    # 引入线支架 (杆身下部小托架, 朝街道 +X)
    parts.append(_box("ServiceRack", (0.04, 0.34, 0.05), loc=(0.14, 0, 4.35),
                      mat="MetalDark", bevel=0.004))
    obj = _join(parts, "UtilityPole")
    _smooth_by_angle(obj)
    return [obj]


# ---------------------------------------------------------------- 四分类垃圾站
def build_trash_station():
    parts = []
    bw, bd, bh = 0.40, 0.36, 0.72   # 单桶体
    lids = [("LidBlue", -1, -1, 0.10), ("LidGreen", 1, -1, 0.10),
            ("LidYellow", -1, 1, 0.16), ("LidGray", 1, 1, 0.16)]
    for mat, gx, gy, lift in lids:
        cx, cy = gx * (bw / 2 + 0.045), gy * (bd / 2 + 0.045)
        parts.append(_box("BinBody_%s" % mat, (bw, bd, bh), loc=(cx, cy, bh / 2 + 0.06),
                          mat="BinBody", bevel=0.008))
        parts.append(_box("BinLid_%s" % mat, (bw + 0.03, bd + 0.03, 0.05),
                          loc=(cx, cy, bh + 0.085 + lift * 0), mat=mat, bevel=0.010))
        parts.append(_box("BinMouth_%s" % mat, (bw - 0.16, bd - 0.16, 0.02),
                          loc=(cx, cy, bh + 0.118), mat="Rubber", bevel=0.004))
    # 钢架: 四立柱 + 顶框 + 底框 + 分类标牌板
    fx, fy = bw + 0.09, bd + 0.09
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(_cyl("FramePost_%d_%d" % (sx, sy), 0.018, 1.12,
                              loc=(sx * fx / 2, sy * fy / 2, 0.56), verts=10,
                              mat="FrameSteel", bevel=0.002))
    parts.append(_box("FrameTopX1", (fx + 0.05, 0.03, 0.03), loc=(0, -fy / 2, 1.12),
                      mat="FrameSteel", bevel=0.004))
    parts.append(_box("FrameTopX2", (fx + 0.05, 0.03, 0.03), loc=(0, fy / 2, 1.12),
                      mat="FrameSteel", bevel=0.004))
    parts.append(_box("FrameTopY", (0.03, fy + 0.05, 0.03), loc=(-fx / 2, 0, 1.12),
                      mat="FrameSteel", bevel=0.004))
    parts.append(_box("FrameTopY2", (0.03, fy + 0.05, 0.03), loc=(fx / 2, 0, 1.12),
                      mat="FrameSteel", bevel=0.004))
    parts.append(_box("SignPanel", (fx - 0.10, 0.02, 0.16), loc=(0, -fy / 2 - 0.015, 1.02),
                      mat="Shell", bevel=0.005))
    obj = _join(parts, "TrashStation4Bin")
    _smooth_by_angle(obj)
    return [obj]


# ---------------------------------------------------------------- 交通锥
def build_traffic_cone():
    bpy = __import__("bpy")
    parts = []
    # 方形橡胶底座
    parts.append(_box("ConeBase", (0.42, 0.42, 0.045), loc=(0, 0, 0.022),
                      mat="Rubber", bevel=0.010))
    # 锥身 (bmesh 圆台) + 白色反光带
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20,
                          radius1=0.145, radius2=0.035, depth=0.68)
    mesh = bpy.data.meshes.new("ConeBody")
    bm.to_mesh(mesh)
    bm.free()
    cone = bpy.data.objects.new("ConeBody", mesh)
    bpy.context.scene.collection.objects.link(cone)
    cone.location = (0, 0, 0.385)
    _link(cone, "ConeOrange")
    parts.append(cone)
    parts.append(_cyl("ConeBand", 0.093, 0.10, loc=(0, 0, 0.40), verts=20,
                      mat="ConeWhite", bevel=0.004))
    parts.append(_cyl("ConeTop", 0.038, 0.03, loc=(0, 0, 0.735), verts=12,
                      mat="ConeOrange", bevel=0.004))
    obj = _join(parts, "TrafficCone")
    _smooth_by_angle(obj)
    return [obj]


def main():
    _clean_scene()
    _export(build_ac_unit(double=False), "ac_unit_single.glb")
    _clean_scene()
    _export(build_ac_unit(double=True), "ac_unit_double.glb")
    _clean_scene()
    _export(build_utility_pole(), "utility_pole.glb")
    _clean_scene()
    _export(build_trash_station(), "trash_station_4bin.glb")
    _clean_scene()
    _export(build_traffic_cone(), "traffic_cone.glb")
    print("[props] all done")


main()
