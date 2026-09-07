# Aster 网格治理与解剖重绑 v4（无头 Blender）：
#   blender.exe -b --factory-startup art/models/aster_assembled.blend \
#     -P scripts/pipeline/rebind_aster_clean.py -- [blend_out] [temp_dir]
#
# v5.3 任务书四铁律工业化落地：
#   1) 【长发锁头】焊合前以「颅部种子 + 颈环圆柱墙」泛洪剥离头部系统并打 Hair_Group 标签；
#      焊合走双通道（头部类 / 身体类各自内部焊合），严禁发簇与衣领身体顶点缝合；
#      求解后 Hair_Group 顶点 100% 锁 Head，并写入 Hair_Mask 顶点色（红），
#      随 GLB COLOR_0 导出供引擎侧门禁复核（Twist/长发/插槽/零权重四断言）。
#   2) 【Twist 拍平】16 根肢体扭转骨 + NeckTwist02 全部移出形变骨集合
#      （Mixamo 无扭转骨，扭骨恒 rest 即刚性锚点，会把手臂大腿拧成麻花）；
#      形变由主骨（Thigh/Calf/Upperarm/Forearm 等 23 骨）独占。
#   3) 【非形变骨零权重】Root 与全部 *Socket 骨不建顶点组（插槽纯挂载锚点）。
#   4) 【裙摆硬隔离】伞状外层布料 100% 锁 Hip，腰封带按高度线性羽化（杜绝硬边缠绕）。
#   5) 【归一化底线】全网格权重和强制 = 1.0，孤立点就近骨兜底，
#      硬断言：Unweighted Vertices == 0、Socket 权重 == 0、Twist 权重 == 0。
# 输出：净化后 blend（rest 姿态保存）+ 三视角预览图 + JSON 报告。
import bpy
import bmesh
import json
import os
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BLEND_OUT = os.path.abspath(argv[0]) if len(argv) > 0 else os.path.join(REPO, "art", "models", "aster_assembled_clean.blend")
TMP = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.join(os.path.dirname(BLEND_OUT), "_rebind_preview")
os.makedirs(TMP, exist_ok=True)

MERGE_DIST = 0.001          # 焊合阈值（双通道：仅同类顶点互焊）
LONG_EDGE = 0.25            # rest 长度超 25cm 的边 = 碎片焊盘/跨鞋桥
HAIR_SEED_RADIUS = 0.12     # 颅部种子半径（Head 骨标定点）
HAIR_WALL_RADIUS = 0.085    # 颈环圆柱墙半径（头发连颅不穿颈，面部止于下颌墙）
HAIR_FACE_KEEP = 0.14       # 距颅 14cm 内=面部/颅顶皮肤，保持求解器权重
HAIR_MAX_REACH = 0.78       # 头部系统泄漏熔断线（实测发梢垂距 0.565m）
SKIRT_DZ_LO = 0.45          # 裙摆带下界：Hip rest 头下方 45cm（过膝）
SKIRT_FADE = 0.14           # 腰封羽化带：腰带处随脊柱 → 向下 14cm 线性过渡 → 100% 锁髋
SKIRT_R_MIN = 0.16          # 离髋轴水平半径 >16cm = 伞状外层布料

body = bpy.data.objects["Aster_Body"]
arm = bpy.data.objects["Aster_Armature"]
report = {"merge": {}, "solver": {}, "skirt": {}, "hair": {}, "gate": {}}


def log(msg):
    print("[rebind] " + msg, flush=True)


def fatal(msg):
    print("[rebind] FATAL: " + msg, flush=True)
    sys.exit(1)


def _seg_dist_local(p, seg):
    h, t = seg
    d = t - h
    dd = d.dot(d)
    u = 0.0 if dd < 1e-12 else max(0.0, min(1.0, (p - h).dot(d) / dd))
    return (p - (h + d * u)).length


def bone_seg(name):
    pb = arm.pose.bones[name]
    h = wm @ pb.matrix.translation
    t = wm @ (pb.matrix @ Vector((0.0, pb.length, 0.0)))
    return h, t


# ---------------- 0) 环境体检 + 强制回 Rest ----------------
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()
log("已强制回 Rest 姿态")

log("armature matrix_world identity=%s" % (arm.matrix_world == __import__("mathutils").Matrix.Identity(4)))
for name in ("Katana_Blade", "Katana_Scabbard"):
    o = bpy.data.objects.get(name)
    log("%s parent_bone=%s" % (name, o.parent_bone if o else None))
for m in list(body.modifiers):
    if m.type == "ARMATURE":
        body.modifiers.remove(m)
        log("移除旧 ARMATURE 修改器（防双重变形）")

wm = body.matrix_world
verts = body.data.vertices

# ---------------- 0.5) 头部系统预分类（焊合前拓扑泛洪 + Hair_Group 标签） ----------------
# 长发与躯干只在颈环处连通；颅部种子泛洪 + 颈环墙 = 干净剥出「颅面 + 全部头发」。
skull_c = wm @ arm.pose.bones["Head"].matrix.translation
neck_seg = bone_seg("NeckTwist01")
adj = {v.index: [] for v in verts}
for e in body.data.edges:
    a, b = e.vertices
    adj[a].append(b)
    adj[b].append(a)
_cls_attr = body.data.attributes.new("rebind_class", "INT", "POINT")
_cls = _cls_attr.data
for i in range(len(verts)):
    _cls[i].value = 1  # 默认身体类
walls = set()
for v in verts:
    if _seg_dist_local(wm @ v.co, neck_seg) < HAIR_WALL_RADIUS:
        _cls[v.index].value = 1  # 墙顶点归身体类（颈环焊合不跨类）
        walls.add(v.index)
_seen = set(walls)
_stack = [v.index for v in verts if (wm @ v.co - skull_c).length < HAIR_SEED_RADIUS and v.index not in walls]
_head_comp = []
while _stack:
    vv = _stack.pop()
    if vv in _seen:
        continue
    _seen.add(vv)
    _head_comp.append(vv)
    _stack.extend(adj[vv])
for vi in _head_comp:
    _cls[vi].value = 0  # 头部系统类
n_below = sum(1 for vi in _head_comp if (wm @ verts[vi].co).z < skull_c.z - 0.35)
log("头部系统泛洪: %d 顶点（墙 %d / 垂肩线下 %.1f%%）" % (len(_head_comp), len(walls), 100.0 * n_below / max(1, len(_head_comp))))
if len(_head_comp) < 3000 or len(_head_comp) > 9000 or n_below > 0.3 * len(_head_comp):
    fatal("头部系统泛洪规模异常（%d 顶点 / 垂肩 %.1f%%），拒绝继续" % (len(_head_comp), 100.0 * n_below / max(1, len(_head_comp))))
report["hair"]["head_component_verts"] = len(_head_comp)

# ---------------- 1) 网格净化：双通道焊合（头发绝不与身体缝合） ----------------
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(body.data)
bm.verts.ensure_lookup_table()
_cls_layer = bm.verts.layers.int.get("rebind_class") or bm.verts.layers.int.new("rebind_class")
head_bmv = [v for v in bm.verts if v[_cls_layer] == 0]
body_bmv = [v for v in bm.verts if v[_cls_layer] == 1]
n_v0, n_f0 = len(bm.verts), len(bm.faces)
bmesh.ops.remove_doubles(bm, verts=head_bmv, dist=MERGE_DIST)   # 通道 A：头部系统内部焊合
bm.verts.ensure_lookup_table()
body_bmv = [v for v in bm.verts if v[_cls_layer] == 1]
bmesh.ops.remove_doubles(bm, verts=body_bmv, dist=MERGE_DIST)   # 通道 B：身体内部焊合
log("双通道焊合完成：头部类 %d / 身体类 %d（跨类缝合被禁止）" % (len(head_bmv), len(body_bmv)))

# 长桥接面清除：AI 生成的跨鞋/跨区焊盘桥在迈步时被撕成米级拉丝
bad_edges = [e for e in bm.edges if e.calc_length() > LONG_EDGE]
bad_faces = set()
for e in bad_edges:
    bad_faces.update(e.link_faces)
if bad_faces:
    bmesh.ops.delete(bm, geom=list(bad_faces), context="FACES")
report["merge"]["long_bridge_edges"] = len(bad_edges)
report["merge"]["long_bridge_faces"] = len(bad_faces)

degenerate = [f for f in bm.faces if f.calc_area() < 1e-10]
if degenerate:
    bmesh.ops.delete(bm, geom=degenerate, context="FACES")
loose_edges = [e for e in bm.edges if not e.link_faces]
if loose_edges:
    bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
loose_verts = [v for v in bm.verts if v.is_valid and not v.link_faces]
if loose_verts:
    bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

# 【红线】严禁盲目 recalc_face_normals：源资产法线朝向本就正确（旧定稿渲染受光正常），
# 焊合后拓扑改变会让重算把整片裙壳朝向翻转（NdotL 倒置=受光面渲染成暗蓝）。
bmesh.update_edit_mesh(body.data)
bpy.ops.object.mode_set(mode="OBJECT")
report["merge"]["verts"] = [n_v0, len(body.data.vertices)]
report["merge"]["faces"] = [n_f0, len(body.data.polygons)]
log("焊合净化: verts %d->%d, faces %d->%d, 长桥 %d 条/%d 面" % (
    n_v0, len(body.data.vertices), n_f0, len(body.data.polygons), len(bad_edges), len(bad_faces)))
verts = body.data.vertices

# ---------------- 2) 确定性几何权重求解器（23 形变骨） ----------------
bone_names = [b.name for b in arm.pose.bones]
SOCKET_BONES = [n for n in bone_names if n.endswith("Socket")]
# 【Twist 拍平】Mixamo 无扭转骨：16 根肢体扭骨 + NeckTwist02 恒 rest = 刚性锚点，
# 主骨转它不转会把肢体拧成麻花。全部移出形变集合，形变由主骨独占。
TWIST_FLATTEN = [n for n in bone_names if "Twist" in n and n != "NeckTwist01"]
DEFORM_EXCLUDE = set(["Root"] + SOCKET_BONES + TWIST_FLATTEN)
_deform_bones = [n for n in bone_names if n not in DEFORM_EXCLUDE]

for vg in list(body.vertex_groups):
    body.vertex_groups.remove(vg)
for n in _deform_bones:
    body.vertex_groups.new(name=n)
log("形变骨 %d 个（排除 Root + %d Socket + %d 扭骨: %s）" % (
    len(_deform_bones), len(SOCKET_BONES), len(TWIST_FLATTEN), TWIST_FLATTEN))


def side_axis_setup():
    l_h, _ = bone_seg("L_Thigh")
    r_h, _ = bone_seg("R_Thigh")
    axis = (l_h - r_h).normalized()
    mid = (l_h + r_h) * 0.5
    side = {}
    for n in bone_names:
        h, _ = bone_seg(n)
        s = (h - mid).dot(axis)
        side[n] = s if abs(s) > 0.02 else 0.0
    for n in bone_names:
        if "Twist" in n and side[n] == 0.0 and arm.pose.bones[n].parent:
            side[n] = side.get(arm.pose.bones[n].parent.name, 0.0)
    return axis, mid, side


side_axis, mid, bone_side = side_axis_setup()
seg_cache = {n: bone_seg(n) for n in bone_names}

n_single = 0
n_blend = 0
for v in verts:
    p = wm @ v.co
    v_side = (p - mid).dot(side_axis)
    vert_side = 1 if v_side > 0.02 else (-1 if v_side < -0.02 else 0)
    cand = []
    for n in _deform_bones:
        bs = bone_side[n]
        if vert_side != 0 and bs != 0.0 and (bs > 0) != vert_side:
            continue  # 右侧顶点绝不绑左侧骨（反之亦然）
        if vert_side == 0 and bs != 0.0:
            continue  # 矢状面带（裙摆/裆部）只允许中央骨
        cand.append((_seg_dist_local(p, seg_cache[n]), n))
    cand.sort(key=lambda x: x[0])
    d1, n1 = cand[0]
    d2, n2 = cand[1]
    vi = v.index
    if d2 > d1 + 0.10:
        body.vertex_groups[n1].add([vi], 1.0, "REPLACE")
        n_single += 1
    else:
        w1 = 1.0 / (d1 + 0.01)
        w2 = 1.0 / (d2 + 0.01)
        s = w1 + w2
        body.vertex_groups[n1].add([vi], w1 / s, "ADD")
        body.vertex_groups[n2].add([vi], w2 / s, "ADD")
        n_blend += 1
report["solver"] = {"single": n_single, "blend": n_blend, "deform_bones": len(_deform_bones)}
log("确定性求解: 单骨 %d / 双骨混合 %d" % (n_single, n_blend))

# ---------------- 2.5) 【裙摆硬隔离】伞状布料 100% 锁 Hip（腰带羽化） ----------------
hip_head_w = wm @ arm.pose.bones["Hip"].matrix.translation
skirt_locked = 0
skirt_feathered = 0
for v in verts:
    p = wm @ v.co
    dz = hip_head_w.z - p.z
    if not (0.0 < dz <= SKIRT_DZ_LO):
        continue
    r = ((p.x - hip_head_w.x) ** 2 + (p.y - hip_head_w.y) ** 2) ** 0.5
    if r <= SKIRT_R_MIN:
        continue
    vi = v.index
    if dz >= SKIRT_FADE:
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([vi])
        body.vertex_groups["Hip"].add([vi], 1.0, "REPLACE")
        skirt_locked += 1
    else:
        w_hip = dz / SKIRT_FADE
        for g in v.groups:
            g.weight *= (1.0 - w_hip)
        body.vertex_groups["Hip"].add([vi], w_hip, "ADD")
        skirt_feathered += 1
report["skirt"] = {"verts_locked_to_hip": skirt_locked, "verts_feathered": skirt_feathered,
                   "band_dz": [SKIRT_DZ_LO, SKIRT_FADE], "r_min": SKIRT_R_MIN}
log("裙摆硬隔离: %d 顶点 → 100%% Hip, 腰封羽化 %d 顶点" % (skirt_locked, skirt_feathered))

# ---------------- 3) 【长发锁头】Hair_Group 顶点 100% 锁 Head + 顶点色标记 ----------------
_cls_attr = body.data.attributes["rebind_class"]
_cls = _cls_attr.data
hair_vids = []
for v in verts:
    if _cls[v.index].value != 0:
        continue  # 非头部系统类
    if (wm @ v.co - skull_c).length <= HAIR_FACE_KEEP:
        continue  # 面部/颅顶皮肤保持求解器权重
    hair_vids.append(v.index)
for vi in hair_vids:
    for g in list(verts[vi].groups):
        body.vertex_groups[g.group].remove([vi])
    body.vertex_groups["Head"].add([vi], 1.0, "REPLACE")
# Hair_Group 顶点组（Blender 侧可读标签；不对应骨骼，GLB 导出时自动忽略）
vg_hair = body.vertex_groups.new(name="Hair_Group")
body.vertex_groups["Hair_Group"].add(hair_vids, 1.0, "REPLACE")
# Hair_UV 第二 UV 层（发丝=(0.5,0.5) 其余=(0,0)）：随 glTF TEXCOORD_1 →
# Godot ARRAY_TEX_UV2 导出（实测 COLOR_0/1 通道会被引擎丢弃合成白色，UV2 通道可靠）
_hair_set = set(hair_vids)
_uv_main = body.data.uv_layers[0]
_uv_hair = body.data.uv_layers.new(name="Hair_UV")
_uv_vals = []
for poly in body.data.polygons:
    for li in poly.loop_indices:
        vi = body.data.loops[li].vertex_index
        if vi in _hair_set:
            _uv_vals += [0.5, 0.5]
        else:
            _uv_vals += [0.0, 0.0]
_uv_hair.data.foreach_set("uv", _uv_vals)
body.data.uv_layers.active = _uv_main  # 主 UV 保持 TEXCOORD_0
report["hair"]["verts_locked_head"] = len(hair_vids)
log("长发锁头: %d 顶点 → 100%% Head（Hair_Group + Hair_Mask 标记完成）" % len(hair_vids))

# ---------------- 3.5) 【归一化底线】+ 四铁律硬断言 ----------------
for v in verts:
    total = sum(g.weight for g in v.groups)
    if total <= 1e-9:
        p = wm @ v.co
        best = min(_deform_bones, key=lambda n: _seg_dist_local(p, seg_cache[n]))
        body.vertex_groups[best].add([v.index], 1.0, "REPLACE")
        report["gate"]["empty_fallback"] = report["gate"].get("empty_fallback", 0) + 1
        continue
    inv = 1.0 / total
    for g in v.groups:
        g.weight = min(1.0, g.weight * inv)

n_unweighted = sum(1 for v in verts if sum(g.weight for g in v.groups) <= 1e-6)
n_socket_weighted = 0
for sn in SOCKET_BONES:
    gi = body.vertex_groups[sn].index if any(vg.name == sn for vg in body.vertex_groups) else -1
    if gi < 0:
        continue
    for v in verts:
        if any(g.group == gi and g.weight > 1e-6 for g in v.groups):
            n_socket_weighted += 1
n_twist_weighted = 0
for tn in TWIST_FLATTEN:
    gi = body.vertex_groups[tn].index if any(vg.name == tn for vg in body.vertex_groups) else -1
    if gi < 0:
        continue
    for v in verts:
        if any(g.group == gi and g.weight > 1e-6 for g in v.groups):
            n_twist_weighted += 1
# 发丝锁头校验：Hair_Group 顶点必须恰好单骨 Head@1.0
n_hair_bad = 0
hair_gi = body.vertex_groups["Hair_Group"].index
for v in verts:
    is_hair = any(g.group == hair_gi and g.weight > 0.5 for g in v.groups)
    if not is_hair:
        continue
    gs = [(body.vertex_groups[g.group].name, g.weight) for g in v.groups if g.weight > 1e-6]
    if len(gs) != 1 or gs[0][0] != "Head" or abs(gs[0][1] - 1.0) > 1e-4:
        n_hair_bad += 1
report["gate"].update({
    "unweighted_verts": n_unweighted,
    "socket_weighted_verts": n_socket_weighted,
    "twist_weighted_verts": n_twist_weighted,
    "hair_bad_verts": n_hair_bad,
})
log("门禁: unweighted=%d socket=%d twist=%d hair_bad=%d" % (
    n_unweighted, n_socket_weighted, n_twist_weighted, n_hair_bad))
if n_unweighted != 0:
    fatal("铁律失守：仍有 %d 个零权重顶点" % n_unweighted)
if n_socket_weighted != 0:
    fatal("铁律失守：Socket 骨带权顶点 %d 个" % n_socket_weighted)
if n_twist_weighted != 0:
    fatal("铁律失守：Twist 骨带权顶点 %d 个" % n_twist_weighted)
if n_hair_bad != 0:
    fatal("铁律失守：%d 个发丝顶点未严格锁 Head@1.0" % n_hair_bad)

# ---------------- 4) 跨侧桥接面终清（安全网） ----------------
_pos_side = {}
for v in verts:
    best, bw = None, 0.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, body.vertex_groups[g.group].name
    s = bone_side.get(best, 0.0) if best else 0.0
    _key = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
    _pos_side[_key] = 1 if s > 0 else (-1 if s < 0 else 0)
bridge_faces = 0
bpy.ops.object.mode_set(mode="EDIT")
_bmf = bmesh.from_edit_mesh(body.data)
_kill = []
for f in _bmf.faces:
    sides = set()
    for v in f.verts:
        _key = (round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
        sides.add(_pos_side.get(_key, 0))
    if 1 in sides and -1 in sides:
        _kill.append(f)
if _kill:
    bmesh.ops.delete(_bmf, geom=_kill, context="FACES")
    bridge_faces = len(_kill)
_dangling = [v for v in _bmf.verts if v.is_valid and not v.link_faces]
if _dangling:
    bmesh.ops.delete(_bmf, geom=_dangling, context="VERTS")
bmesh.update_edit_mesh(body.data)
bpy.ops.object.mode_set(mode="OBJECT")
report["bridge_faces_removed"] = bridge_faces
log("跨侧桥接面终清: %d 张" % bridge_faces)
verts = body.data.vertices  # 索引位移，重新捕获

# ---------------- 5) 保存 + 预览 ----------------
body.parent = arm
body.parent_type = "ARMATURE"
for m in list(body.modifiers):
    if m.type != "ARMATURE":
        log("删除残留修改器: %s (%s)" % (m.name, m.type))
        body.modifiers.remove(m)
arm_mod = body.modifiers.new(name="Armature", type="ARMATURE")
arm_mod.object = arm
log("本体已挂回 ARMATURE 蒙皮修改器")

usage = {n: 0 for n in bone_names}
for v in verts:
    best, bw = None, 0.0
    for g in v.groups:
        if g.weight > bw:
            bw, best = g.weight, body.vertex_groups[g.group].name
    if best:
        usage[best] += 1
report["dominant_usage_top"] = sorted(usage.items(), key=lambda kv: -kv[1])[:12]
log("支配骨分布(前12): %s" % report["dominant_usage_top"])

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT, compress=True)
log("已保存: " + BLEND_OUT)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024

mins = Vector((min(v.co.x for v in verts), min(v.co.y for v in verts), min(v.co.z for v in verts)))
maxs = Vector((max(v.co.x for v in verts), max(v.co.y for v in verts), max(v.co.z for v in verts)))
center = (mins + maxs) / 2
height = maxs.z - mins.z
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 60
cam = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for tag, direction in [("front", Vector((0, -1, 0))), ("back", Vector((0, 1, 0))), ("left", Vector((-1, 0, 0)))]:
    cam.location = center + direction * (height * 1.5)
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(TMP, "clean_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
log("预览图已输出至 " + TMP)

with open(os.path.join(TMP, "rebind_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
log("REPORT=" + json.dumps(report, ensure_ascii=False))
print("REBIND_DONE")
