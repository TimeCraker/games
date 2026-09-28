import bpy
import bmesh
import mathutils
import math
import shutil

print("=== [BlenderMCP Master Pipeline] Aster 终极无损高精重构 ===")

# 1. 清空当前场景
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m, do_unlink=True)
for a in list(bpy.data.armatures):
    bpy.data.armatures.remove(a, do_unlink=True)

# 2. 导入纯净源模
source_glb = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\source\aster_tripo_39caf44b\aster_source.glb"
print(f"导入纯净源模: {source_glb}")
bpy.ops.import_scene.gltf(filepath=source_glb)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.vertices) > 20000][0]

for o in list(bpy.data.objects):
    if o != arm and o != mesh_obj:
        print(f"清理多余源对象: {o.name}")
        bpy.data.objects.remove(o, do_unlink=True)

arm.name = "Aster_Armature"
arm.data.name = "Aster_Armature"
mesh_obj.name = "Aster_Body"
mesh_obj.data.name = "Aster_Body"
mesh = mesh_obj.data
print(f"源模导入成功: verts={len(mesh.vertices)}, polys={len(mesh.polygons)}")

# 3. 几何骨骼线段与左右归属算法
def dist_to_segment(p, a, b):
    ab = b - a
    lsq = ab.length_squared
    if lsq < 1e-8:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / lsq))
    return (p - (a + t * ab)).length

l_segments = [
    (arm.data.bones['L_Thigh'].head_local, arm.data.bones['L_Thigh'].tail_local),
    (arm.data.bones['L_Calf'].head_local, arm.data.bones['L_Calf'].tail_local),
    (arm.data.bones['L_Foot'].head_local, arm.data.bones['L_Foot'].tail_local)
]
r_segments = [
    (arm.data.bones['R_Thigh'].head_local, arm.data.bones['R_Thigh'].tail_local),
    (arm.data.bones['R_Calf'].head_local, arm.data.bones['R_Calf'].tail_local),
    (arm.data.bones['R_Foot'].head_local, arm.data.bones['R_Foot'].tail_local)
]

vert_is_left = []
for v in mesh.vertices:
    d_l = min(dist_to_segment(v.co, a, b) for a, b in l_segments)
    d_r = min(dist_to_segment(v.co, a, b) for a, b in r_segments)
    vert_is_left.append(d_l < d_r)

# 4. 精准斩断跨腿连体边 (彻底消除残留铁丝 Wire Edges，杜绝腿分裂与拉丝)
bm = bmesh.new()
bm.from_mesh(mesh)
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# 4a. 找出下半身 (Z < 0.45) 跨越左右腿的所有边 (一端为 Left，一端为 Right)
cross_edges = []
for e in bm.edges:
    v1, v2 = e.verts[0], e.verts[1]
    if v1.co.z < 0.45 and v2.co.z < 0.45:
        if vert_is_left[v1.index] != vert_is_left[v2.index]:
            cross_edges.append(e)

print(f"检测到下肢跨腿连体交界边: {len(cross_edges)} 条，执行彻底切断(EDGES context)...")
if cross_edges:
    bmesh.ops.delete(bm, geom=cross_edges, context='EDGES')

# 4b. 清理因斩断跨界边产生的孤立线段 (Wire Edges) 与浮空孤儿点
wire_edges = [e for e in bm.edges if len(e.link_faces) == 0]
if wire_edges:
    print(f"清理孤立铁丝线 (Wire Edges): {len(wire_edges)} 条")
    bmesh.ops.delete(bm, geom=wire_edges, context='EDGES')

loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
if loose_verts:
    print(f"清理孤立浮空点: {len(loose_verts)} 个")
    bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')

bm.to_mesh(mesh)
bm.free()
mesh.update()
print(f"跨腿连体边彻底斩断完成！当前 verts={len(mesh.vertices)}, polys={len(mesh.polygons)}")

# 5. 权重深度重构
l_vgs = {vg.name for vg in mesh_obj.vertex_groups if vg.name.startswith('L_')}
r_vgs = {vg.name for vg in mesh_obj.vertex_groups if vg.name.startswith('R_')}

# 重新计算当前所有顶点的几何归属
vert_is_left = []
for v in mesh.vertices:
    d_l = min(dist_to_segment(v.co, a, b) for a, b in l_segments)
    d_r = min(dist_to_segment(v.co, a, b) for a, b in r_segments)
    vert_is_left.append(d_l < d_r)

vert_weights = []
for v in mesh.vertices:
    vert_weights.append({mesh_obj.vertex_groups[g.group].name: g.weight for g in v.groups})

twist_fold = {
    'L_ThighTwist01': 'L_Thigh', 'L_ThighTwist02': 'L_Thigh',
    'R_ThighTwist01': 'R_Thigh', 'R_ThighTwist02': 'R_Thigh',
    'L_CalfTwist01': 'L_Calf',   'L_CalfTwist02': 'L_Calf',
    'R_CalfTwist01': 'R_Calf',   'R_CalfTwist02': 'R_Calf',
    'L_UpperarmTwist01': 'L_Upperarm', 'L_UpperarmTwist02': 'L_Upperarm',
    'R_UpperarmTwist01': 'R_Upperarm', 'R_UpperarmTwist02': 'R_Upperarm',
    'L_ForearmTwist01': 'L_Forearm',   'L_ForearmTwist02': 'L_Forearm',
    'R_ForearmTwist01': 'R_Forearm',   'R_ForearmTwist02': 'R_Forearm',
    'NeckTwist02': 'NeckTwist01',
    'L_ToeBase': 'L_Foot', 'R_ToeBase': 'R_Foot',
}

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)

for i, v in enumerate(mesh.vertices):
    co = v.co
    w_map = vert_weights[i]

    if co.z < 0.45:
        is_left = vert_is_left[i]

        # 彻底清除对侧骨骼权重
        for k in list(w_map.keys()):
            if is_left and k in r_vgs:
                del w_map[k]
            elif (not is_left) and k in l_vgs:
                del w_map[k]

        target_foot = 'L_Foot' if is_left else 'R_Foot'
        target_calf = 'L_Calf' if is_left else 'R_Calf'

        # 玛丽珍鞋刚性包裹：源模 Z <= 0.075 包含鞋底、鞋跟、鞋帮、蝴蝶结、搭扣 100% 随 Foot 刚性驱动
        if co.z <= 0.075:
            w_map.clear()
            w_map[target_foot] = 1.0

        # 袜子脚踝顺滑过渡段 (0.075 < Z < 0.14)
        elif 0.075 < co.z < 0.14:
            for k in ['L_ToeBase', 'R_ToeBase', 'L_Thigh', 'R_Thigh']:
                w_map.pop(k, None)
            t = smoothstep(0.075, 0.14, co.z)
            w_map.clear()
            w_map[target_foot] = 1.0 - t
            w_map[target_calf] = t

        # 小腿及以上区域 (Z >= 0.14): 彻底脱钩 Foot 与 ToeBase
        elif co.z >= 0.14:
            for k in ['L_Foot', 'R_Foot', 'L_ToeBase', 'R_ToeBase']:
                w_map.pop(k, None)

    # 折叠 Twist 骨骼
    for tw, main in twist_fold.items():
        if tw in w_map:
            w_map[main] = w_map.get(main, 0.0) + w_map[tw]
            del w_map[tw]

    # 归一化
    tot = sum(w_map.values())
    if tot > 0.0001:
        for k in w_map:
            w_map[k] /= tot
    else:
        # 保底
        target = 'L_Foot' if (co.y > -0.007) else 'R_Foot'
        w_map[target] = 1.0

# 拓扑平滑邻接修复孤立点 (若有)
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
for i, v in enumerate(mesh.vertices):
    if len(vert_weights[i]) == 0 or sum(vert_weights[i].values()) < 0.001:
        bv = bm.verts[i]
        for e in bv.link_edges:
            other = e.other_vert(bv)
            if len(vert_weights[other.index]) > 0:
                vert_weights[i] = dict(vert_weights[other.index])
                break
bm.free()

mesh_obj.vertex_groups.clear()
all_groups = set()
for wm in vert_weights:
    all_groups.update(wm.keys())
vg_objects = {name: mesh_obj.vertex_groups.new(name=name) for name in sorted(all_groups)}
for i, wm in enumerate(vert_weights):
    for grp_name, weight in wm.items():
        if weight > 0.0001:
            vg_objects[grp_name].add([i], weight, 'REPLACE')
mesh.update()
print("权重深度清洗与刚性重构完成！")

# 6. 复合变换 M (旋转+90°, 居中Pelvis至X=0,Y=0, 接地Z=0, 缩放1.65m)
scale_factor = 1.65 / (max(v.co.z for v in mesh.vertices) - min(v.co.z for v in mesh.vertices))
R = mathutils.Matrix.Rotation(math.pi / 2.0, 4, 'Z')
S = mathutils.Matrix.Diagonal((scale_factor, scale_factor, scale_factor, 1.0))
RS = S @ R
pelvis_ref = arm.data.bones.get('Pelvis') or arm.data.bones.get('Hip')
center_xy = RS @ pelvis_ref.head_local
min_z = min((RS @ v.co).z for v in mesh.vertices)
M = mathutils.Matrix.Translation((-center_xy.x, -center_xy.y, -min_z)) @ RS

mesh.transform(M)
mesh.update()

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for eb in arm.data.edit_bones:
    eb.transform(M)
bpy.ops.object.mode_set(mode='OBJECT')
print("复合变换 M 应用完成 (身高 1.65m，骨盆中轴居中，脚底接地 0)")

# 7. 骨骼基底与插槽装配
bpy.ops.object.mode_set(mode='EDIT')
eb_root = arm.data.edit_bones.get('Root')
eb_hip = arm.data.edit_bones.get('Hip')
eb_pelvis = arm.data.edit_bones.get('Pelvis')

if eb_root:
    eb_root.head = (0.0, 0.0, 0.0)
    eb_root.tail = (0.0, 0.0, 0.1)
    eb_root.roll = 0.0

if eb_hip and eb_pelvis:
    eb_hip.tail = eb_hip.head + (eb_pelvis.tail - eb_pelvis.head)
    eb_hip.roll = eb_pelvis.roll

eb_r_hand = arm.data.edit_bones.get('R_Hand')
eb_hand_socket = arm.data.edit_bones.new('Hand_R_Weapon_Socket')
eb_hand_socket.parent = eb_r_hand
eb_hand_socket.use_deform = False
eb_hand_socket.head = eb_r_hand.tail
eb_hand_socket.tail = eb_r_hand.tail + mathutils.Vector((0.0, 0.1, 0.0))
eb_hand_socket.roll = 0.0

eb_scab_socket = arm.data.edit_bones.new('Pelvis_L_Scabbard_Socket')
eb_scab_socket.parent = eb_pelvis if eb_pelvis else eb_hip
eb_scab_socket.use_deform = False
pelvis_ref_z = eb_pelvis.head.z if eb_pelvis else 0.90
eb_scab_socket.head = mathutils.Vector((-0.155, 0.015, pelvis_ref_z - 0.02))
eb_scab_socket.tail = eb_scab_socket.head + mathutils.Vector((-0.02, -0.06, -0.16))
eb_scab_socket.roll = 0.0

bpy.ops.object.mode_set(mode='OBJECT')

# 8. 装配佩刀与刀鞘
katana_path = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\weapons\aster_katana\aster_katana.glb"
bpy.ops.import_scene.gltf(filepath=katana_path)
blade_obj = bpy.data.objects.get("Blade_Mesh") or bpy.data.objects.get("Katana_Blade")
scab_obj = bpy.data.objects.get("Scabbard_Mesh") or bpy.data.objects.get("Katana_Scabbard")
blade_obj.name = "Katana_Blade"
scab_obj.name = "Katana_Scabbard"

blade_obj.parent = arm
blade_obj.parent_type = 'BONE'
blade_obj.parent_bone = 'Hand_R_Weapon_Socket'
blade_obj.location = (0.0, 0.0, 0.0)
blade_obj.rotation_euler = (0.0, 0.0, 0.0)

scab_obj.parent = arm
scab_obj.parent_type = 'BONE'
scab_obj.parent_bone = 'Pelvis_L_Scabbard_Socket'
scab_obj.location = (0.0, 0.0, 0.0)
scab_obj.rotation_euler = (0.0, 0.0, 0.0)

# 9. 发丝 Hair_UV 通道标记
hair_uv = mesh.uv_layers.get("Hair_UV")
if not hair_uv:
    hair_uv = mesh.uv_layers.new(name="Hair_UV")

head_vg = mesh_obj.vertex_groups.get('Head')
forbidden_bones = {'Spine01', 'Spine02', 'Waist', 'Hip', 'Pelvis', 'L_Thigh', 'R_Thigh', 'L_Calf', 'R_Calf'}
forbidden_group_indices = {mesh_obj.vertex_groups[n].index for n in forbidden_bones if n in mesh_obj.vertex_groups}

head_vert_indices = set()
if head_vg:
    for v in mesh.vertices:
        has_forbidden = any(g.group in forbidden_group_indices and g.weight > 0.0001 for g in v.groups)
        if not has_forbidden:
            for g in v.groups:
                if g.group == head_vg.index and g.weight > 0.2:
                    head_vert_indices.add(v.index)
                    break

for f_idx in forbidden_group_indices:
    mesh_obj.vertex_groups[f_idx].remove(list(head_vert_indices))

for poly in mesh.polygons:
    for loop_idx in poly.loop_indices:
        vi = mesh.loops[loop_idx].vertex_index
        hair_uv.data[loop_idx].uv = (0.5, 0.5) if (vi in head_vert_indices) else (0.0, 0.0)

# 10. 保存工程并导出 GLB
work_blend = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\work\aster_assembled_v2.blend"
bpy.ops.wm.save_as_mainfile(filepath=work_blend)
print(f"Blender 工程已保存: {work_blend}")

primary_export = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\client-godot-v2\models\aster\aster_character.glb"
bpy.ops.export_scene.gltf(
    filepath=primary_export,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_skins=True,
    export_all_influences=False,
    export_def_bones=False
)

for copy_target in [
    r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\client-godot-v2\models\aster\aster_assembled.glb",
    r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\aster_assembled.glb"
]:
    shutil.copyfile(primary_export, copy_target)

print("=== [BlenderMCP Master Pipeline] 构建并导出完成！ ===")
