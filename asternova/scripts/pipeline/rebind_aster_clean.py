# Aster 网格治理与干净重绑 v2（无头 Blender）：
#   blender.exe -b --factory-startup art/models/aster_assembled.blend \
#     -P scripts/pipeline/rebind_aster_clean.py -- [blend_out] [temp_dir]
#
# 根除断肢与拉丝的工业化管线：
#   1) 网格净化：顶点极微距离焊合(0.001) + 删孤立点/线 + 删零面积退化面
#   2) 权重科学重绑：AI 碎片壳非流形拓扑会毒死 Blender 热权重求解器（实测
#      24k/56k 顶点全军覆没），故走「流形捐赠者」中转——
#        复制网格 → Make Manifold 修成流形（仅作权重捐赠者，不动本体）
#        → 捐赠者上跑原生自动权重(ARMATURE_AUTO，真·Bone Heat)
#        → Data Transfer 最近面插值把权重转回本体
#      捐赠者热权重仍失败则降级：包络权重 + 连通平滑
#   3) 定向防污染：长发簇 100% Head（杜绝粘腰）；左右侧锁（鞋/腿跨骨权重归零）
#   4) 零权重顶点就近骨兜底 + 全量归一化，另存 aster_assembled_clean.blend
# 输出：净化后 blend + 三视角预览图 + JSON 报告（人眼复核用）。
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

MERGE_DIST = 0.001          # 任务书规定：极微距离焊合阈值
LONG_EDGE = 0.25            # rest 长度超 25cm 的边 = 碎片焊盘/跨鞋桥（真实布片边 <5cm）
SIDE_ISLAND_THRESH = 0.06   # 岛质心离中线超过 6cm 视作单侧岛（鞋/腿/臂）
SIDE_BONE_THRESH = 0.02     # 骨头离中线超过 2cm 才参与侧锁（脊柱/骨盆保持中立）
HAIR_SKULL_RADIUS = 0.22    # 岛上任一顶点距颅心 <22cm 判定连着头（发簇）
HAIR_MAX_ISLAND = 512       # 且岛尺寸 ≤512（把主体岛的面部/颈部皮肤排除在外）
COHERENCE_DIST = 0.45       # 岛内权重骨距支配骨段中心 >45cm = 跨区污染，清除

body = bpy.data.objects["Aster_Body"]
arm = bpy.data.objects["Aster_Armature"]
report = {"merge": {}, "donor": {}, "hair": {}, "sidelock": {}, "fallback": {}}


def log(msg):
    print("[rebind] " + msg, flush=True)


def bucket_hist(sizes):
    edges = [(1, 1), (4, "2-4"), (16, "5-16"), (64, "17-64"), (256, "65-256"), (1024, "257-1024")]
    out = {}
    for s in sizes:
        k = ">1024"
        for cap, name in edges:
            if s <= cap:
                k = name
                break
        out[k] = out.get(k, 0) + 1
    return out


# ---------------- 0) 环境体检 ----------------
log("armature matrix_world identity=%s" % (arm.matrix_world == __import__("mathutils").Matrix.Identity(4)))
for name in ("Katana_Blade", "Katana_Scabbard"):
    o = bpy.data.objects.get(name)
    log("%s parent_bone=%s" % (name, o.parent_bone if o else None))
for m in list(body.modifiers):
    if m.type == "ARMATURE":
        body.modifiers.remove(m)
        log("移除旧 ARMATURE 修改器（防双重变形）")

# ---------------- 1) 网格净化与碎片焊合 ----------------
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(body.data)
n_v0, n_f0 = len(bm.verts), len(bm.faces)

bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=MERGE_DIST)

# 长桥接面清除：AI 生成的跨鞋/跨区焊盘桥在迈步时被撕成米级拉丝
# （实测：左右鞋之间存在 1.26m 的拉丝边与并行焊盘条）
bad_edges = [e for e in bm.edges if e.calc_length() > LONG_EDGE]
bad_faces = set()
for e in bad_edges:
    bad_faces.update(e.link_faces)
if bad_faces:
    bmesh.ops.delete(bm, geom=list(bad_faces), context="FACES")
report["merge"]["long_bridge_edges"] = len(bad_edges)
report["merge"]["long_bridge_faces"] = len(bad_faces)
log("长桥清除: %d 条长边 / %d 张桥接面" % (len(bad_edges), len(bad_faces)))

degenerate = [f for f in bm.faces if f.calc_area() < 1e-10]
if degenerate:
    bmesh.ops.delete(bm, geom=degenerate, context="FACES")
loose_edges = [e for e in bm.edges if not e.link_faces]
if loose_edges:
    bmesh.ops.delete(bm, geom=loose_edges, context="EDGES")
loose_verts = [v for v in bm.verts if v.is_valid and not v.link_faces]
if loose_verts:
    bmesh.ops.delete(bm, geom=loose_verts, context="VERTS")

island_sizes = []
_seen = set()
for f in bm.faces:
    if f.index in _seen:
        continue
    stack, comp = [f], 0
    while stack:
        cur = stack.pop()
        if cur.index in _seen:
            continue
        _seen.add(cur.index)
        comp += 1
        for e in cur.edges:
            for nf in e.link_faces:
                if nf.index not in _seen:
                    stack.append(nf)
    island_sizes.append(comp)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.update_edit_mesh(body.data)
bpy.ops.object.mode_set(mode="OBJECT")
report["merge"] = {
    "verts": [n_v0, len(body.data.vertices)],
    "faces": [n_f0, len(body.data.polygons)],
    "degenerate_faces": len(degenerate),
    "loose_verts": len(loose_verts),
    "loose_edges": len(loose_edges),
    "island_count": len(island_sizes),
    "island_hist_buckets": bucket_hist(island_sizes),
}
log("焊合净化: verts %d->%d, faces %d->%d, islands=%d" % (
    n_v0, len(body.data.vertices), n_f0, len(body.data.polygons), len(island_sizes)))

# ---------------- 2) 权重科学重绑（流形捐赠者中转） ----------------
for vg in list(body.vertex_groups):
    body.vertex_groups.remove(vg)
log("已清除全部脏权重顶点组")

bone_names = [b.name for b in arm.pose.bones]
for n in bone_names:  # 预建 43 个空组（与捐赠者同名，供 Data Transfer 对位）
    body.vertex_groups.new(name=n)

# ---------------- 2) 确定性几何权重求解器 ----------------
# 不用热权重/代理/转移（AI 双壳网格会毒死热方程，转移链路启发式互相打架）。
# 每顶点：43 骨段距离排序 → 侧别/Root 过滤 → 最近两骨反距离混合；
# 深区域（第二近远 10cm 以上）单骨刚性。规则天然满足：无跨侧、无 Root、≤2 骨。
def _seg_dist_local(p, seg):
    h, t = seg
    d = t - h
    dd = d.dot(d)
    u = 0.0 if dd < 1e-12 else max(0.0, min(1.0, (p - h).dot(d) / dd))
    return (p - (h + d * u)).length


wm = body.matrix_world
verts = body.data.vertices


def bone_seg(name):
    pb = arm.pose.bones[name]
    h = wm @ pb.matrix.translation
    t = wm @ (pb.matrix @ Vector((0.0, pb.length, 0.0)))
    return h, t


L_H, _ = bone_seg("L_Thigh")
R_H, _ = bone_seg("R_Thigh")
side_axis = (L_H - R_H).normalized()
mid = (L_H + R_H) * 0.5
bone_side = {}
for n in bone_names:
    h, _ = bone_seg(n)
    s = (h - mid).dot(side_axis)
    bone_side[n] = s if abs(s) > 0.02 else 0.0
# 扭骨几乎长在肢体轴线上（位置近矢状面），侧别必须继承父主骨，
# 否则小腿扭骨会被当作「中央骨」分给对侧顶点（实测 L_Calf 混入右腿顶点）
for n in bone_names:
    if "Twist" in n and bone_side[n] == 0.0 and arm.pose.bones[n].parent:
        bone_side[n] = bone_side.get(arm.pose.bones[n].parent.name, 0.0)
seg_cache = {n: bone_seg(n) for n in bone_names}
_deform_bones = [n for n in bone_names if n != "Root"]

wm = body.matrix_world
verts = body.data.vertices

n_mixed_cross = 0
n_single = 0
n_blend = 0
for vi, v in enumerate(verts):
    p = wm @ v.co
    v_side = (p - mid).dot(side_axis)
    vert_side = 1 if v_side > 0.02 else (-1 if v_side < -0.02 else 0)
    cand = []
    for n in _deform_bones:
        bs = bone_side[n]
        if vert_side != 0 and bs != 0.0 and (bs > 0) != vert_side:
            continue  # 位置在右侧的顶点绝不绑左侧骨（反之亦然）
        if vert_side == 0 and bs != 0.0:
            continue  # 矢状面带（裙摆/裆部）只允许中央骨：分给左右腿必被步幅撕开
        cand.append((_seg_dist_local(p, seg_cache[n]), n))
    cand.sort(key=lambda x: x[0])
    d1, n1 = cand[0]
    d2, n2 = cand[1]
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
report["solver"] = {"single": n_single, "blend": n_blend}
log("确定性求解: 单骨 %d / 双骨混合 %d" % (n_single, n_blend))

# 归一化（ADD 累加后兜底）
for v in verts:
    total = sum(g.weight for g in v.groups)
    if total <= 1e-9:
        p = wm @ v.co
        best = min(_deform_bones, key=lambda n: _seg_dist_local(p, seg_cache[n]))
        body.vertex_groups[best].add([v.index], 1.0, "REPLACE")
        report["solver"]["empty_fallback"] = report["solver"].get("empty_fallback", 0) + 1
        continue
    inv = 1.0 / total
    for g in v.groups:
        g.weight = min(1.0, g.weight * inv)

# ---------------- 3) 长发防粘腰：连着头的小岛 → 100% Head ----------------
seen_islands = set()
adj = {v.index: [] for v in verts}
for e in body.data.edges:
    a, b = e.vertices
    adj[a].append(b)
    adj[b].append(a)
islands = []
_seen = set()
for v0 in range(len(verts)):
    if v0 in seen_islands:
        continue
    comp = []
    stack = [v0]
    while stack:
        vv = stack.pop()
        if vv in seen_islands:
            continue
        seen_islands.add(vv)
        comp.append(vv)
        stack.extend(adj[vv])
    islands.append(comp)
skull_c = wm @ arm.pose.bones["Head"].matrix.translation
hair_islands = 0
hair_touched = 0
for comp in islands:
    near_skull = any((wm @ verts[vi].co - skull_c).length < 0.22 for vi in comp)
    if not (near_skull and len(comp) <= 512):
        continue
    for vi in comp:
        non_head = {body.vertex_groups[g.group].name for g in verts[vi].groups
                    if body.vertex_groups[g.group].name != "Head"}
        for name in non_head:
            body.vertex_groups[name].remove([vi])
        body.vertex_groups["Head"].add([vi], 1.0, "REPLACE")
    hair_touched += len(comp)
    hair_islands += 1
report["hair"] = {"islands": hair_islands, "verts_forced_head": hair_touched}
log("长发防粘腰: %d 个发簇岛 / %d 顶点 → 100%% Head" % (hair_islands, hair_touched))

# ---------------- 4) 跨侧桥接面终清（安全网） ----------------
# 用「坐标键控」的顶点侧别查表（mesh API 读数与 Godot 一致；bmesh 形变层读数不可靠）
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
# 只保留 ARMATURE 修改器：GN「Smooth by Angle」等残留修改器会在带动画导出时
# 触发 depsgraph 重评估，把跨脚重叠顶点焊接错位、权重改写（实测 521 条跨侧边）
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
