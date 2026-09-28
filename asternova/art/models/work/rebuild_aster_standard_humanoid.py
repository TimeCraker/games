import bpy
import mathutils
import math
import os

print("=== 开始执行 Aster 标准 Humanoid 终极归正与重构 (精确 +90° 前向对齐) ===")

# 1. 彻底清空当前 Blender 场景对象与网格数据
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh, do_unlink=True)
for arm in list(bpy.data.armatures):
    bpy.data.armatures.remove(arm, do_unlink=True)

# 2. 导入原厂纯净源模
source_glb = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\source\aster_tripo_39caf44b\aster_source.glb"
print(f"正在导入纯净源模: {source_glb}")
bpy.ops.import_scene.gltf(filepath=source_glb)

arm = None
mesh_obj = None
for o in list(bpy.context.scene.objects):
    if o.type == 'ARMATURE':
        arm = o
    elif o.type == 'MESH':
        if len(o.data.vertices) > 20000:
            mesh_obj = o
        else:
            print(f"移除无关辅助网格: {o.name} ({len(o.data.vertices)} 顶点)")
            bpy.data.objects.remove(o, do_unlink=True)

assert arm is not None and mesh_obj is not None, "未找到导入的 Armature 或 Mesh!"
print(f"导入成功: Armature={arm.name}, Mesh={mesh_obj.name} (verts={len(mesh_obj.data.vertices)}, polys={len(mesh_obj.data.polygons)})")

# 规范重命名
arm.name = "Aster_Armature"
arm.data.name = "Aster_Armature"
mesh_obj.name = "Aster_Body"
mesh_obj.data.name = "Aster_Body"

# 3. 坐标系归正与身高缩放（数学复合变换矩阵法）
# 原模特征：头顶 +Z，脸朝 +X，左手 +Y，右手 -Y，高约 0.9995m
# 正确的标准 Humanoid 映射（脸面向 glTF -Z，头 +Y，右手 +X，左手 -X）：
# 需要在 Blender 空间绕 Z 轴逆时针旋转 +90° (+pi/2)！
# 旋转后：脸在 +Y（glTF Z = -Y = -1），左手在 -X，右手在 +X，高 1.65m，脚底 Z=0
z_min = min(v.co.z for v in mesh_obj.data.vertices)
z_max = max(v.co.z for v in mesh_obj.data.vertices)
orig_h = z_max - z_min
target_h = 1.65
scale_factor = target_h / orig_h
print(f"原始高度: {orig_h:.4f}m, 目标高度: {target_h:.2f}m, 缩放比: {scale_factor:.6f}")

R = mathutils.Matrix.Rotation(math.pi / 2.0, 4, 'Z')
S = mathutils.Matrix.Diagonal((scale_factor, scale_factor, scale_factor, 1.0))
RS = S @ R

min_z = min((RS @ v.co).z for v in mesh_obj.data.vertices)
T = mathutils.Matrix.Translation((0.0, 0.0, -min_z))
M = T @ RS

# 彻底将变换应用到网格顶点与骨骼 rest pose
mesh_obj.data.transform(M)
mesh_obj.data.update()

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for eb in arm.data.edit_bones:
    eb.transform(M)

print("数学复合变换 M 应用完成 (旋转 +90°，缩放 1.65m，接地 Z=0)")
bpy.context.view_layer.update()

# 4. 骨骼 Edit 模式：对齐脊柱基底 / Root 归零
eb_root = arm.data.edit_bones.get('Root')
eb_hip = arm.data.edit_bones.get('Hip')
eb_pelvis = arm.data.edit_bones.get('Pelvis')

if eb_root:
    eb_root.head = (0.0, 0.0, 0.0)
    eb_root.tail = (0.0, 0.0, 0.1)
    eb_root.roll = 0.0

# 消除 Hip 向后翘的残差：让 Hip 的朝向与 roll 与 Pelvis/Waist/Spine 绝对共线同向！
# 这样整条脊柱链 Hip -> Pelvis -> Waist -> Spine01 -> Spine02 -> Head 基底 100% 连贯，
# 彻底根除因骨骼轴向断层导致的 180° 反转与 57° 后仰！
if eb_hip and eb_pelvis:
    eb_hip.tail = eb_hip.head + (eb_pelvis.tail - eb_pelvis.head)
    eb_hip.roll = eb_pelvis.roll

# 5. 装配两个 0 权重武器插槽骨
# 右手在 X > 0 侧
eb_r_hand = arm.data.edit_bones.get('R_Hand')
assert eb_r_hand is not None, "未找到 R_Hand 骨骼!"

eb_hand_socket = arm.data.edit_bones.new('Hand_R_Weapon_Socket')
eb_hand_socket.parent = eb_r_hand
eb_hand_socket.use_deform = False
eb_hand_socket.head = eb_r_hand.tail
eb_hand_socket.tail = eb_r_hand.tail + mathutils.Vector((0.0, 0.1, 0.0))
eb_hand_socket.roll = 0.0

# 左腰侧在 X < 0 侧 (标准人体：左侧 X < 0, 脸朝 +Y, 后背 -Y)
eb_scab_socket = arm.data.edit_bones.new('Pelvis_L_Scabbard_Socket')
eb_scab_socket.parent = eb_pelvis if eb_pelvis else eb_hip
eb_scab_socket.use_deform = False
pelvis_ref_z = eb_pelvis.head.z if eb_pelvis else 0.90
# 挂载在左腰外侧 (X < 0)，顺着大腿外侧向下顺垂
eb_scab_socket.head = mathutils.Vector((-0.155, 0.015, pelvis_ref_z - 0.02))
eb_scab_socket.tail = eb_scab_socket.head + mathutils.Vector((-0.02, -0.06, -0.16))
eb_scab_socket.roll = 0.0

print(f"骨骼编辑完成，总骨骼数: {len(arm.data.edit_bones)}")
bpy.ops.object.mode_set(mode='OBJECT')

# 6. 网格物理分腿（仅在 Z < 0.40m 鞋底接地安全区清除跨 X=0 融接面）
# 裙摆（Z >= 0.40m）100% 绝对保护，零删面、零切割！
mesh = mesh_obj.data
faces_to_remove = []
for p in mesh.polygons:
    p_verts = [mesh.vertices[vi] for vi in p.vertices]
    if all(v.co.z < 0.40 for v in p_verts):
        xs = [v.co.x for v in p_verts]
        if min(xs) < -0.003 and max(xs) > 0.003:
            faces_to_remove.append(p.index)

print(f"在 Z < 0.40m 鞋底安全区发现跨 X=0 粘连面: {len(faces_to_remove)} 个 (裙摆 100% 完整无损)")

import bmesh
bm = bmesh.new()
bm.from_mesh(mesh)
bm.faces.ensure_lookup_table()

del_faces = [bm.faces[fi] for fi in faces_to_remove]
bmesh.ops.delete(bm, geom=del_faces, context='FACES_ONLY')

verts_to_delete = [v for v in bm.verts if len(v.link_faces) == 0 and v.co.z < 0.40]
bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')

bm.to_mesh(mesh)
bm.free()
mesh.update()
print(f"分腿清理完成: 剩余顶点数={len(mesh.vertices)}, 剩余面数={len(mesh.polygons)}")

# 7. 肢体 Twist 扭骨权重安全折叠回主肢骨
twist_map = {
    'L_ThighTwist01': 'L_Thigh', 'L_ThighTwist02': 'L_Thigh',
    'R_ThighTwist01': 'R_Thigh', 'R_ThighTwist02': 'R_Thigh',
    'L_CalfTwist01': 'L_Calf',   'L_CalfTwist02': 'L_Calf',
    'R_CalfTwist01': 'R_Calf',   'R_CalfTwist02': 'R_Calf',
    'L_UpperarmTwist01': 'L_Upperarm', 'L_UpperarmTwist02': 'L_Upperarm',
    'R_UpperarmTwist01': 'R_Upperarm', 'R_UpperarmTwist02': 'R_Upperarm',
    'L_ForearmTwist01': 'L_Forearm',   'L_ForearmTwist02': 'L_Forearm',
    'R_ForearmTwist01': 'R_Forearm',   'R_ForearmTwist02': 'R_Forearm',
    'NeckTwist02': 'NeckTwist01',
}

vg_map = {vg.name: vg for vg in mesh_obj.vertex_groups}

for tw_name, main_name in twist_map.items():
    if tw_name in vg_map and main_name in vg_map:
        tw_vg = vg_map[tw_name]
        main_vg = vg_map[main_name]
        for v in mesh.vertices:
            tw_w = 0.0
            main_w = 0.0
            for g in v.groups:
                if g.group == tw_vg.index:
                    tw_w = g.weight
                elif g.group == main_vg.index:
                    main_w = g.weight
            if tw_w > 0.0:
                main_vg.add([v.index], main_w + tw_w, 'REPLACE')
                tw_vg.remove([v.index])

# 彻底确保 Twist 骨骼权重全为 0
for tw_name in twist_map:
    if tw_name in vg_map:
        tw_vg = vg_map[tw_name]
        for v in mesh.vertices:
            tw_vg.remove([v.index])

# 确保两个插槽骨没有蒙皮顶点权重
for s_name in ['Hand_R_Weapon_Socket', 'Pelvis_L_Scabbard_Socket']:
    if s_name in vg_map:
        mesh_obj.vertex_groups.remove(vg_map[s_name])

print("Twist 扭骨权重折叠完成，插槽骨权重彻底清零")

# 8. 下半身对称骨骼权重清洗（消除左右腿互串污染）
# 现在人体坐标：左腿 X < 0，右腿 X > 0
leg_bones = ['Thigh', 'Calf', 'Foot', 'ToeBase']
for b_base in leg_bones:
    l_name = f"L_{b_base}"
    r_name = f"R_{b_base}"
    if l_name in vg_map and r_name in vg_map:
        l_vg = vg_map[l_name]
        r_vg = vg_map[r_name]
        for v in mesh.vertices:
            if v.co.z < 0.75: # 下半身
                if v.co.x < -0.01: # 明显在左侧 (X < 0)
                    for g in v.groups:
                        if g.group == r_vg.index and g.weight > 0.0:
                            cur_l = 0.0
                            for lg in v.groups:
                                if lg.group == l_vg.index:
                                    cur_l = lg.weight
                            l_vg.add([v.index], cur_l + g.weight, 'REPLACE')
                            r_vg.remove([v.index])
                elif v.co.x > 0.01: # 明显在右侧 (X > 0)
                    for g in v.groups:
                        if g.group == l_vg.index and g.weight > 0.0:
                            cur_r = 0.0
                            for rg in v.groups:
                                if rg.group == r_vg.index:
                                    cur_r = rg.weight
                            r_vg.add([v.index], cur_r + g.weight, 'REPLACE')
                            l_vg.remove([v.index])

print("左右腿跨骨污染清洗完成")

# 9. 会阴部加固与发丝锁头（分配给 Head，标记 Hair_UV）
pelvis_vg = vg_map.get('Pelvis')
if pelvis_vg:
    for v in mesh.vertices:
        if abs(v.co.x) < 0.025 and 0.55 < v.co.z < 0.85:
            pelvis_vg.add([v.index], 0.65, 'ADD')

hair_uv = mesh.uv_layers.get("Hair_UV")
if not hair_uv:
    hair_uv = mesh.uv_layers.new(name="Hair_UV")

head_vg = vg_map.get('Head')
forbidden_bones = ['Spine01', 'Spine02', 'Waist', 'Hip', 'Pelvis', 'L_Thigh', 'R_Thigh', 'L_Calf', 'R_Calf']
forbidden_vgs = [vg_map[n] for n in forbidden_bones if n in vg_map]

hair_vert_indices = set()
for v in mesh.vertices:
    is_head = v.co.z > 1.25
    is_cape_hair = (v.co.z > 0.80 and v.co.y < -0.03 and abs(v.co.x) < 0.35) # Y < 0 为后背披肩发
    if is_head or is_cape_hair:
        hair_vert_indices.add(v.index)
        for f_vg in forbidden_vgs:
            f_vg.remove([v.index])
        if head_vg:
            head_vg.add([v.index], 0.8, 'ADD')

for poly in mesh.polygons:
    for loop_idx in poly.loop_indices:
        vi = mesh.loops[loop_idx].vertex_index
        if vi in hair_vert_indices:
            hair_uv.data[loop_idx].uv = (0.5, 0.5)
        else:
            hair_uv.data[loop_idx].uv = (0.0, 0.0)

# 权重归一化与清除零权重顶点
for v in mesh.vertices:
    total_w = sum(g.weight for g in v.groups)
    if total_w > 0.0001:
        for g in v.groups:
            mesh_obj.vertex_groups[g.group].add([v.index], g.weight / total_w, 'REPLACE')
    else:
        if pelvis_vg:
            pelvis_vg.add([v.index], 1.0, 'REPLACE')

print(f"发丝隔离与 Hair_UV 标记完成: 标记发丝顶点数 = {len(hair_vert_indices)}")

# 10. 导入佩刀与刀鞘并装配插槽
katana_path = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\weapons\aster_katana\aster_katana.glb"
print(f"正在导入佩刀武器: {katana_path}")
bpy.ops.import_scene.gltf(filepath=katana_path)

blade_obj = bpy.data.objects.get("Blade_Mesh") or bpy.data.objects.get("Katana_Blade")
scab_obj = bpy.data.objects.get("Scabbard_Mesh") or bpy.data.objects.get("Katana_Scabbard")

assert blade_obj is not None and scab_obj is not None, "未找到 Katana 网格对象!"
blade_obj.name = "Katana_Blade"
scab_obj.name = "Katana_Scabbard"

# 默认拔刀/纳刀初始装配：
# Katana_Blade 挂在 Hand_R_Weapon_Socket 下，供 Godot _locate_katana 初始化检索
blade_obj.parent = arm
blade_obj.parent_type = 'BONE'
blade_obj.parent_bone = 'Hand_R_Weapon_Socket'
blade_obj.location = (0.0, 0.0, 0.0)
blade_obj.rotation_euler = (0.0, 0.0, 0.0)

# Katana_Scabbard 挂在 Pelvis_L_Scabbard_Socket 下
scab_obj.parent = arm
scab_obj.parent_type = 'BONE'
scab_obj.parent_bone = 'Pelvis_L_Scabbard_Socket'
scab_obj.location = (0.0, 0.0, 0.0)
scab_obj.rotation_euler = (0.0, 0.0, 0.0)

print("武器插槽挂载完成")

# 11. 保存工程与导出 GLB
work_blend = r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\work\aster_assembled_v2.blend"
bpy.ops.wm.save_as_mainfile(filepath=work_blend)
print(f"Blender 工程保存至: {work_blend}")

export_targets = [
    r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\client-godot-v2\models\aster\aster_character.glb",
    r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\client-godot-v2\models\aster\aster_assembled.glb",
    r"C:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\aster_assembled.glb"
]

for target in export_targets:
    os.makedirs(os.path.dirname(target), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=target,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_skins=True,
        export_all_influences=False,
        export_def_bones=False
    )
    print(f"成功导出 GLB: {target}")

print("=== Aster 标准 Humanoid 重构与装配圆满完成 ===")
