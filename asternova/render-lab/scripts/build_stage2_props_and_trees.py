"""
build_stage2_props_and_trees.py
Blender 5.2 脚本：阶段 2 二次元块面樱花树与现代街景小道具制作与装配
- 二次元块面樱花树 (Normal Transfer 球面法线重定向，彻底消除碎黑阴影，面数 ≤ 2,500)
- 现代街道道具 5 件套：
  1. 灰色水泥电线杆 (带圆筒变压器、横担绝缘子与带实体截面的天空架空拉线)
  2. 红蓝现代自动贩卖机 (带自发光冷饮展示橱窗与分类回收桶)
  3. 道路转角黄色凸面反光镜 (橙黄色柱身、大圆形凸面反光镜)
  4. 空调室外机 (挂载于民居外立面)
  5. 不锈钢转角人行护栏与柏油马路标线
- 导出独立资产 GLB 与完整街区整合 GLB
- 渲染 3 张 1080p 阶段 2 自检截图
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

BASE_DIR = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab"
TEXTURES_DIR = os.path.join(BASE_DIR, "textures")
MODELS_DIR = os.path.join(BASE_DIR, "models", "environment")
SCREENS_DIR = os.path.join(BASE_DIR, "screenshots", "stage2")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SCREENS_DIR, exist_ok=True)

def point_camera_at(cam_obj, target_pos):
    loc = cam_obj.location
    direction = Vector(target_pos) - loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def create_prop_materials():
    mats = {}
    
    # 1. 樱花树花瓣材质
    mat_sakura = bpy.data.materials.new("Mat_Sakura_Petal")
    mat_sakura.use_nodes = True
    snodes = mat_sakura.node_tree.nodes
    slinks = mat_sakura.node_tree.links
    snodes.clear()
    s_out = snodes.new('ShaderNodeOutputMaterial')
    s_bsdf = snodes.new('ShaderNodeBsdfPrincipled')
    s_bsdf.inputs['Base Color'].default_value = (1.0, 0.72, 0.84, 1.0) # 饱满通透樱粉
    s_bsdf.inputs['Roughness'].default_value = 0.80
    s_bsdf.inputs['Subsurface Weight'].default_value = 0.35
    s_bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.4, 0.4)
    slinks.new(s_bsdf.outputs['BSDF'], s_out.inputs['Surface'])
    mats['sakura'] = mat_sakura
    
    # 2. 樱花树树干
    mat_bark = bpy.data.materials.new("Mat_Cherry_Bark")
    mat_bark.use_nodes = True
    bnodes = mat_bark.node_tree.nodes
    blinks = mat_bark.node_tree.links
    bnodes.clear()
    b_out = bnodes.new('ShaderNodeOutputMaterial')
    b_bsdf = bnodes.new('ShaderNodeBsdfPrincipled')
    b_bsdf.inputs['Base Color'].default_value = (0.28, 0.20, 0.16, 1.0)
    b_bsdf.inputs['Roughness'].default_value = 0.78
    blinks.new(b_bsdf.outputs['BSDF'], b_out.inputs['Surface'])
    mats['bark'] = mat_bark
    
    # 3. 电线杆混凝土
    mat_pole = bpy.data.materials.new("Mat_Utility_Pole")
    mat_pole.use_nodes = True
    pnodes = mat_pole.node_tree.nodes
    plinks = mat_pole.node_tree.links
    pnodes.clear()
    p_out = pnodes.new('ShaderNodeOutputMaterial')
    p_bsdf = pnodes.new('ShaderNodeBsdfPrincipled')
    p_bsdf.inputs['Base Color'].default_value = (0.64, 0.66, 0.68, 1.0)
    p_bsdf.inputs['Roughness'].default_value = 0.70
    plinks.new(p_bsdf.outputs['BSDF'], p_out.inputs['Surface'])
    mats['pole'] = mat_pole
    
    # 4. 变压器
    mat_trans = bpy.data.materials.new("Mat_Transformer")
    mat_trans.use_nodes = True
    tnodes = mat_trans.node_tree.nodes
    tlinks = mat_trans.node_tree.links
    tnodes.clear()
    t_out = tnodes.new('ShaderNodeOutputMaterial')
    t_bsdf = tnodes.new('ShaderNodeBsdfPrincipled')
    t_bsdf.inputs['Base Color'].default_value = (0.22, 0.28, 0.25, 1.0)
    t_bsdf.inputs['Metallic'].default_value = 0.7
    t_bsdf.inputs['Roughness'].default_value = 0.45
    tlinks.new(t_bsdf.outputs['BSDF'], t_out.inputs['Surface'])
    mats['transformer'] = mat_trans
    
    # 5. 贩卖机红色
    mat_vend_red = bpy.data.materials.new("Mat_Vending_Red")
    mat_vend_red.use_nodes = True
    vrnodes = mat_vend_red.node_tree.nodes
    vrlinks = mat_vend_red.node_tree.links
    vrnodes.clear()
    vr_out = vrnodes.new('ShaderNodeOutputMaterial')
    vr_bsdf = vrnodes.new('ShaderNodeBsdfPrincipled')
    vr_bsdf.inputs['Base Color'].default_value = (0.86, 0.12, 0.14, 1.0)
    vr_bsdf.inputs['Roughness'].default_value = 0.32
    vrlinks.new(vr_bsdf.outputs['BSDF'], vr_out.inputs['Surface'])
    mats['vend_red'] = mat_vend_red
    
    # 6. 贩卖机蓝色
    mat_vend_blue = bpy.data.materials.new("Mat_Vending_Blue")
    mat_vend_blue.use_nodes = True
    vbnodes = mat_vend_blue.node_tree.nodes
    vblinks = mat_vend_blue.node_tree.links
    vbnodes.clear()
    vb_out = vbnodes.new('ShaderNodeOutputMaterial')
    vb_bsdf = vbnodes.new('ShaderNodeBsdfPrincipled')
    vb_bsdf.inputs['Base Color'].default_value = (0.10, 0.44, 0.90, 1.0)
    vb_bsdf.inputs['Roughness'].default_value = 0.32
    vrlinks.new(vb_bsdf.outputs['BSDF'], vb_out.inputs['Surface'])
    mats['vend_blue'] = mat_vend_blue
    
    # 7. 贩卖机自发光冷饮橱窗
    mat_vend_glow = bpy.data.materials.new("Mat_Vending_Glow")
    mat_vend_glow.use_nodes = True
    vgnodes = mat_vend_glow.node_tree.nodes
    vglinks = mat_vend_glow.node_tree.links
    vgnodes.clear()
    vg_out = vgnodes.new('ShaderNodeOutputMaterial')
    vg_bsdf = vgnodes.new('ShaderNodeBsdfPrincipled')
    vg_bsdf.inputs['Base Color'].default_value = (0.94, 0.97, 1.0, 1.0)
    vg_bsdf.inputs['Emission Color'].default_value = (0.85, 0.96, 1.0, 1.0)
    vg_bsdf.inputs['Emission Strength'].default_value = 2.4
    vg_bsdf.inputs['Roughness'].default_value = 0.15
    vglinks.new(vg_bsdf.outputs['BSDF'], vg_out.inputs['Surface'])
    mats['vend_glow'] = mat_vend_glow
    
    # 8. 凸面镜黄色
    mat_mirror_yellow = bpy.data.materials.new("Mat_Mirror_Yellow")
    mat_mirror_yellow.use_nodes = True
    mynodes = mat_mirror_yellow.node_tree.nodes
    mylinks = mat_mirror_yellow.node_tree.links
    mynodes.clear()
    my_out = mynodes.new('ShaderNodeOutputMaterial')
    my_bsdf = mynodes.new('ShaderNodeBsdfPrincipled')
    my_bsdf.inputs['Base Color'].default_value = (0.98, 0.58, 0.05, 1.0)
    my_bsdf.inputs['Roughness'].default_value = 0.35
    mylinks.new(my_bsdf.outputs['BSDF'], my_out.inputs['Surface'])
    mats['mirror_yellow'] = mat_mirror_yellow
    
    # 9. 凸面镜镜面
    mat_mirror_face = bpy.data.materials.new("Mat_Mirror_Face")
    mat_mirror_face.use_nodes = True
    mfnodes = mat_mirror_face.node_tree.nodes
    mflinks = mat_mirror_face.node_tree.links
    mfnodes.clear()
    mf_out = mfnodes.new('ShaderNodeOutputMaterial')
    mf_bsdf = mfnodes.new('ShaderNodeBsdfPrincipled')
    mf_bsdf.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1.0)
    mf_bsdf.inputs['Metallic'].default_value = 1.0
    mf_bsdf.inputs['Roughness'].default_value = 0.04
    mflinks.new(mf_bsdf.outputs['BSDF'], mf_out.inputs['Surface'])
    mats['mirror_face'] = mat_mirror_face
    
    # 10. 空调室外机
    mat_ac = bpy.data.materials.new("Mat_AC_Unit")
    mat_ac.use_nodes = True
    acnodes = mat_ac.node_tree.nodes
    aclinks = mat_ac.node_tree.links
    acnodes.clear()
    ac_out = acnodes.new('ShaderNodeOutputMaterial')
    ac_bsdf = acnodes.new('ShaderNodeBsdfPrincipled')
    ac_bsdf.inputs['Base Color'].default_value = (0.84, 0.86, 0.88, 1.0)
    ac_bsdf.inputs['Roughness'].default_value = 0.55
    aclinks.new(ac_bsdf.outputs['BSDF'], ac_out.inputs['Surface'])
    mats['ac'] = mat_ac
    
    # 11. 不锈钢护栏
    mat_guardrail = bpy.data.materials.new("Mat_Guardrail")
    mat_guardrail.use_nodes = True
    grnodes = mat_guardrail.node_tree.nodes
    grlinks = mat_guardrail.node_tree.links
    grnodes.clear()
    gr_out = grnodes.new('ShaderNodeOutputMaterial')
    gr_bsdf = grnodes.new('ShaderNodeBsdfPrincipled')
    gr_bsdf.inputs['Base Color'].default_value = (0.88, 0.90, 0.92, 1.0)
    gr_bsdf.inputs['Metallic'].default_value = 0.9
    gr_bsdf.inputs['Roughness'].default_value = 0.28
    grlinks.new(gr_bsdf.outputs['BSDF'], gr_out.inputs['Surface'])
    mats['guardrail'] = mat_guardrail

    # 12. 细黑电线
    mat_wire = bpy.data.materials.new("Mat_Black_Wire")
    mat_wire.use_nodes = True
    wnodes = mat_wire.node_tree.nodes
    wlinks = mat_wire.node_tree.links
    wnodes.clear()
    w_out = wnodes.new('ShaderNodeOutputMaterial')
    w_bsdf = wnodes.new('ShaderNodeBsdfPrincipled')
    w_bsdf.inputs['Base Color'].default_value = (0.12, 0.12, 0.14, 1.0)
    w_bsdf.inputs['Roughness'].default_value = 0.8
    wlinks.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])
    mats['wire'] = mat_wire

    return mats

def build_cherry_blossom_tree(name, location, scale=1.0, is_ancient=False, mats=None):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    
    mesh_trunk = bpy.data.meshes.new(f"{name}_Trunk_Mesh")
    bm = bmesh.new()
    
    trunk_h = 6.8 * scale if is_ancient else 5.2 * scale
    rad_base = 0.45 * scale if is_ancient else 0.28 * scale
    
    segs = 6
    layers = []
    for s in range(segs + 1):
        t = s / segs
        z = t * trunk_h
        bend_x = math.sin(t * math.pi * 0.7) * (1.2 * scale if is_ancient else 0.6 * scale)
        bend_y = (math.cos(t * math.pi * 0.8) - 1.0) * (0.8 * scale if is_ancient else 0.4 * scale)
        r = rad_base * (1.0 - t * 0.6)
        
        verts_ring = []
        n_radial = 8
        for i in range(n_radial):
            angle = i * 2.0 * math.pi / n_radial
            vx = bend_x + r * math.cos(angle)
            vy = bend_y + r * math.sin(angle)
            verts_ring.append(bm.verts.new((vx, vy, z)))
        layers.append(verts_ring)
        
    for s in range(segs):
        for i in range(8):
            v1 = layers[s][i]
            v2 = layers[s][(i + 1) % 8]
            v3 = layers[s + 1][(i + 1) % 8]
            v4 = layers[s + 1][i]
            bm.faces.new((v1, v2, v3, v4))
            
    bm.faces.new(layers[0])
    bm.to_mesh(mesh_trunk)
    bm.free()
    
    trunk_obj = bpy.data.objects.new(f"{name}_Trunk", mesh_trunk)
    trunk_obj.location = location
    trunk_obj.data.materials.append(mats['bark'])
    col.objects.link(trunk_obj)
    
    cluster_offsets = [
        (0.2, 0.0, trunk_h * 0.95, 2.2 * scale),
        (-1.5 * scale, 0.8 * scale, trunk_h * 0.80, 1.8 * scale),
        (1.6 * scale, -0.6 * scale, trunk_h * 0.78, 1.9 * scale),
        (-0.8 * scale, -1.4 * scale, trunk_h * 0.70, 1.7 * scale),
        (1.2 * scale, 1.2 * scale, trunk_h * 0.72, 1.6 * scale),
    ]
    if is_ancient:
        cluster_offsets.append((0.0, 2.2 * scale, trunk_h * 0.65, 2.0 * scale))
        
    canopy_objs = []
    tree_center_z = location[2] + trunk_h * 0.82
    
    for c_idx, (cx, cy, cz, c_rad) in enumerate(cluster_offsets):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=c_rad,
            location=(location[0] + cx, location[1] + cy, location[2] + cz)
        )
        c_obj = bpy.context.active_object
        c_obj.name = f"{name}_Canopy_Clump_{c_idx}"
        c_obj.scale = (1.1, 0.95, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        c_obj.data.materials.append(mats['sakura'])
        canopy_objs.append(c_obj)
        col.objects.link(c_obj)
        bpy.context.scene.collection.objects.unlink(c_obj)
        
    bpy.ops.object.select_all(action='DESELECT')
    for co in canopy_objs:
        co.select_set(True)
    bpy.context.view_layer.objects.active = canopy_objs[0]
    bpy.ops.object.join()
    canopy_merged = bpy.context.active_object
    canopy_merged.name = f"{name}_Canopy"
    
    # Normal Edit (RADIAL)
    target_empty = bpy.data.objects.new(f"{name}_Normal_Center", None)
    target_empty.location = (location[0], location[1], tree_center_z)
    col.objects.link(target_empty)
    
    ne_mod = canopy_merged.modifiers.new(name="NormalEdit_Radial", type='NORMAL_EDIT')
    ne_mod.mode = 'RADIAL'
    ne_mod.target = target_empty
    bpy.context.view_layer.objects.active = canopy_merged
    bpy.ops.object.modifier_apply(modifier=ne_mod.name)
    bpy.data.objects.remove(target_empty, do_unlink=True)
    
    # 简易树干碰撞体
    bpy.ops.mesh.primitive_cylinder_add(
        radius=rad_base * 0.9,
        depth=trunk_h,
        location=(location[0], location[1], location[2] + trunk_h / 2)
    )
    t_col = bpy.context.active_object
    t_col.name = f"{name}_Col-colonly"
    t_col.display_type = 'WIRE'
    col.objects.link(t_col)
    bpy.context.scene.collection.objects.unlink(t_col)
    
    return col

def build_utility_pole_with_wires(name, location, mats, wire_endpoints=[]):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    
    # 混凝土杆身
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=8.5, location=(location[0], location[1], location[2] + 4.25))
    pole = bpy.context.active_object
    pole.name = f"{name}_Pole"
    pole.data.materials.append(mats['pole'])
    col.objects.link(pole)
    bpy.context.scene.collection.objects.unlink(pole)
    
    # 横担支架
    for arm_z in [location[2] + 7.2, location[2] + 8.1]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(location[0], location[1], arm_z))
        arm = bpy.context.active_object
        arm.scale = (1.8, 0.10, 0.10)
        bpy.ops.object.transform_apply(scale=True)
        arm.data.materials.append(mats['guardrail'])
        col.objects.link(arm)
        bpy.context.scene.collection.objects.unlink(arm)
        for ix in [-0.75, 0.0, 0.75]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.22, location=(location[0] + ix, location[1], arm_z + 0.16))
            ins = bpy.context.active_object
            ins.data.materials.append(mats['ac'])
            col.objects.link(ins)
            bpy.context.scene.collection.objects.unlink(ins)
            
    # 圆筒变压器
    trans_x = location[0] + 0.35
    trans_z = location[2] + 6.0
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.9, location=(trans_x, location[1], trans_z))
    trans = bpy.context.active_object
    trans.name = f"{name}_Transformer"
    trans.data.materials.append(mats['transformer'])
    col.objects.link(trans)
    bpy.context.scene.collection.objects.unlink(trans)
    
    # 碰撞体
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=8.5, location=(location[0], location[1], location[2] + 4.25))
    p_col = bpy.context.active_object
    p_col.name = f"{name}-colonly"
    p_col.display_type = 'WIRE'
    col.objects.link(p_col)
    bpy.context.scene.collection.objects.unlink(p_col)
    
    # 实心多边形截面架空电线 (3D Tubed Wire: 可以在 GLB 与渲染中正常显示)
    wire_start = Vector((location[0], location[1], location[2] + 8.1))
    wire_rad = 0.018 # 1.8cm 粗细
    for ep_idx, ep in enumerate(wire_endpoints):
        p_a = wire_start
        p_b = Vector(ep)
        w_segs = 8
        mesh_w = bpy.data.meshes.new(f"{name}_Wire_{ep_idx}_Mesh")
        bm = bmesh.new()
        
        prev_ring = None
        for wi in range(w_segs + 1):
            wt = wi / w_segs
            center = p_a.lerp(p_b, wt)
            sag = math.sin(wt * math.pi) * 0.45
            center.z -= sag
            
            # 4 边形截面环
            ring = []
            for k in range(4):
                ang = k * math.pi / 2
                rx = center.x + wire_rad * math.cos(ang)
                ry = center.y
                rz = center.z + wire_rad * math.sin(ang)
                ring.append(bm.verts.new((rx, ry, rz)))
            if prev_ring:
                for k in range(4):
                    bm.faces.new((prev_ring[k], prev_ring[(k + 1) % 4], ring[(k + 1) % 4], ring[k]))
            prev_ring = ring
            
        bm.to_mesh(mesh_w)
        bm.free()
        w_obj = bpy.data.objects.new(f"{name}_Wire_{ep_idx}", mesh_w)
        w_obj.data.materials.append(mats['wire'])
        col.objects.link(w_obj)
        
    return col

def build_vending_machines(location, mats):
    col = bpy.data.collections.new("Vending_Machines")
    bpy.context.scene.collection.children.link(col)
    
    for v_idx, (color_mat, name_sfx, offset_x) in enumerate([
        (mats['vend_red'], "Red", -0.55),
        (mats['vend_blue'], "Blue", +0.55)
    ]):
        vx = location[0] + offset_x
        vy = location[1]
        vz = location[2]
        
        # 外壳
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vx, vy, vz + 0.975))
        vm = bpy.context.active_object
        vm.name = f"Vending_{name_sfx}_Body"
        vm.scale = (0.95, 0.75, 1.95)
        bpy.ops.object.transform_apply(scale=True)
        vm.data.materials.append(color_mat)
        col.objects.link(vm)
        bpy.context.scene.collection.objects.unlink(vm)
        
        # 顶部白色招牌
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vx, vy - 0.38, vz + 1.80))
        top_sign = bpy.context.active_object
        top_sign.scale = (0.85, 0.05, 0.22)
        bpy.ops.object.transform_apply(scale=True)
        top_sign.data.materials.append(mats['vend_glow'])
        col.objects.link(top_sign)
        bpy.context.scene.collection.objects.unlink(top_sign)
        
        # 自发光冷饮展示橱窗
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vx, vy - 0.38, vz + 1.25))
        win = bpy.context.active_object
        win.name = f"Vending_{name_sfx}_Display_Window"
        win.scale = (0.82, 0.05, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        win.data.materials.append(mats['vend_glow'])
        col.objects.link(win)
        bpy.context.scene.collection.objects.unlink(win)
        
        # 饮料罐排布
        for r_row in range(3):
            for c_col in range(5):
                can_x = vx - 0.32 + c_col * 0.16
                can_z = vz + 0.98 + r_row * 0.24
                bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.12, location=(can_x, vy - 0.35, can_z))
                can = bpy.context.active_object
                can.data.materials.append(color_mat if (r_row + c_col) % 2 == 0 else mats['vend_glow'])
                col.objects.link(can)
                bpy.context.scene.collection.objects.unlink(can)
                
        # 取物挡板口
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vx, vy - 0.38, vz + 0.35))
        disp = bpy.context.active_object
        disp.scale = (0.70, 0.05, 0.35)
        bpy.ops.object.transform_apply(scale=True)
        disp.data.materials.append(mats['wire'])
        col.objects.link(disp)
        bpy.context.scene.collection.objects.unlink(disp)
        
    # 分类回收垃圾桶
    bin_x = location[0] + 1.45
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bin_x, location[1], location[2] + 0.50))
    rbin = bpy.context.active_object
    rbin.name = "Vending_Recycle_Bin"
    rbin.scale = (0.50, 0.55, 1.00)
    bpy.ops.object.transform_apply(scale=True)
    rbin.data.materials.append(mats['pole'])
    col.objects.link(rbin)
    bpy.context.scene.collection.objects.unlink(rbin)
    
    # 碰撞体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(location[0] + 0.35, location[1], location[2] + 0.975))
    v_col = bpy.context.active_object
    v_col.name = "Vending_Group-colonly"
    v_col.scale = (2.8, 0.85, 1.95)
    bpy.ops.object.transform_apply(scale=True)
    v_col.display_type = 'WIRE'
    v_col.hide_render = True
    col.objects.link(v_col)
    bpy.context.scene.collection.objects.unlink(v_col)
    
    return col

def build_convex_traffic_mirror(location, mats):
    col = bpy.data.collections.new("Convex_Mirror")
    bpy.context.scene.collection.children.link(col)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.2, location=(location[0], location[1], location[2] + 1.6))
    post = bpy.context.active_object
    post.name = "Mirror_Post"
    post.data.materials.append(mats['mirror_yellow'])
    col.objects.link(post)
    bpy.context.scene.collection.objects.unlink(post)
    
    mirror_z = location[2] + 3.1
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.08, location=(location[0], location[1] + 0.25, mirror_z))
    rim = bpy.context.active_object
    rim.name = "Mirror_Rim"
    rim.rotation_euler = (math.radians(-25), 0, 0)
    rim.data.materials.append(mats['mirror_yellow'])
    col.objects.link(rim)
    bpy.context.scene.collection.objects.unlink(rim)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.41, depth=0.04, location=(location[0], location[1] + 0.21, mirror_z - 0.02))
    face = bpy.context.active_object
    face.name = "Mirror_Reflective_Face"
    face.rotation_euler = (math.radians(-25), 0, 0)
    face.data.materials.append(mats['mirror_face'])
    col.objects.link(face)
    bpy.context.scene.collection.objects.unlink(face)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.20, depth=3.2, location=(location[0], location[1], location[2] + 1.6))
    m_col = bpy.context.active_object
    m_col.name = "Mirror_Post-colonly"
    m_col.display_type = 'WIRE'
    m_col.hide_render = True
    col.objects.link(m_col)
    bpy.context.scene.collection.objects.unlink(m_col)
    
    return col

def build_ac_outdoor_units(mats):
    col = bpy.data.collections.new("AC_Units")
    bpy.context.scene.collection.children.link(col)
    
    unit_positions = [
        ((-12.0, -0.2, 1.8), (0, 0, 0)),
        ((-10.3, -4.0, 4.8), (0, 0, math.radians(90))),
        ((-10.3, +4.0, 1.5), (0, 0, math.radians(90))),
    ]
    
    for i, (pos, rot) in enumerate(unit_positions):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos)
        ac = bpy.context.active_object
        ac.name = f"AC_Unit_{i+1}"
        ac.scale = (0.85, 0.35, 0.62)
        ac.rotation_euler = rot
        bpy.ops.object.transform_apply(scale=True)
        ac.data.materials.append(mats['ac'])
        col.objects.link(ac)
        bpy.context.scene.collection.objects.unlink(ac)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.03, location=(pos[0], pos[1] - 0.18, pos[2]))
        grille = bpy.context.active_object
        grille.rotation_euler = (math.radians(90), 0, 0)
        grille.data.materials.append(mats['wire'])
        col.objects.link(grille)
        bpy.context.scene.collection.objects.unlink(grille)
        
    return col

def build_guardrails(mats):
    col = bpy.data.collections.new("Guardrails")
    bpy.context.scene.collection.children.link(col)
    
    rail_pos = [(4.2, 14.5, 0.18), (5.5, 14.5, 0.0), (6.8, 14.5, 0.0)]
    for r_idx, (rx, ry, rz) in enumerate(rail_pos):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.2, location=(rx, ry, rz + 0.80))
        top_bar = bpy.context.active_object
        top_bar.rotation_euler = (0, math.radians(90), 0)
        top_bar.data.materials.append(mats['guardrail'])
        col.objects.link(top_bar)
        bpy.context.scene.collection.objects.unlink(top_bar)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.2, location=(rx, ry, rz + 0.45))
        mid_bar = bpy.context.active_object
        mid_bar.rotation_euler = (0, math.radians(90), 0)
        mid_bar.data.materials.append(mats['guardrail'])
        col.objects.link(mid_bar)
        bpy.context.scene.collection.objects.unlink(mid_bar)
        
        for post_x in [rx - 0.55, rx + 0.55]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.85, location=(post_x, ry, rz + 0.425))
            r_post = bpy.context.active_object
            r_post.data.materials.append(mats['guardrail'])
            col.objects.link(r_post)
            bpy.context.scene.collection.objects.unlink(r_post)
            
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(rx, ry, rz + 0.425))
        gr_col = bpy.context.active_object
        gr_col.name = f"Guardrail_Col_{r_idx}-colonly"
        gr_col.scale = (1.2, 0.15, 0.85)
        bpy.ops.object.transform_apply(scale=True)
        gr_col.display_type = 'WIRE'
        gr_col.hide_render = True
        col.objects.link(gr_col)
        bpy.context.scene.collection.objects.unlink(gr_col)
        
    return col

def render_stage2_inspection_views():
    scene = bpy.context.scene
    
    # 隐藏所有 -colonly 碰撞体在渲染中的显示
    for obj in bpy.data.objects:
        if "-colonly" in obj.name:
            obj.hide_render = True
            
    cam_data = bpy.data.cameras.new('Stage2Cam')
    cam_data.lens = 26 # 26mm 广角，视野完整
    cam_obj = bpy.data.objects.new('Stage2Cam', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    views = [
        (
            "stage2_view1_street_props.png",
            (0.0, 16.0, 1.4),        # 站在广场前侧路面
            (4.0, 19.5, 1.2)         # 正对红蓝贩卖机自发光与黄色凸面镜
        ),
        (
            "stage2_view2_cherry_tree_close.png",
            (-1.5, -4.5, 3.5),       # 仰视视角近景
            (4.3, -5.0, 5.0)         # 聚焦樱花树冠与通透球形法线
        ),
        (
            "stage2_view3_slope_with_wires.png",
            (0.0, 15.0, 1.5),        # 坡底正中
            (0.0, -15.0, 6.0)        # 纵览长坡、樱花树、电线杆与天空电线
        )
    ]
    
    print("=== Rendering Stage 2 Inspection Screenshots ===")
    for fname, loc, target in views:
        cam_obj.location = Vector(loc)
        point_camera_at(cam_obj, target)
        out_path = os.path.join(SCREENS_DIR, fname)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Captured: {out_path}")
        
    bpy.data.objects.remove(cam_obj, do_unlink=True)

def main():
    print("Starting Stage 2 Build: Sakura Trees and Modern Street Props...")
    
    blend_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.blend")
    if os.path.exists(blend_path):
        bpy.ops.wm.open_mainfile(filepath=blend_path)
        print("Loaded Stage 1 blend file.")
    else:
        print("Warning: Stage 1 blend file not found.")
        
    mats = create_prop_materials()
    
    # 1. 建造 A 区北端高台苍劲古樱花树
    print("Building Ancient Cherry Tree at North Landmark...")
    build_cherry_blossom_tree("Tree_Ancient_A", location=(3.8, -30.5, 8.0), scale=1.35, is_ancient=True, mats=mats)
    
    # 2. 建造 B 区大滑道两侧现代街区樱花树 3 棵
    print("Building 3 Street Cherry Trees along Slope...")
    build_cherry_blossom_tree("Tree_Street_1", location=(-4.3, -18.0, 4.95), scale=0.95, mats=mats)
    build_cherry_blossom_tree("Tree_Street_2", location=(+4.3, -5.0, 3.0), scale=1.05, mats=mats)
    build_cherry_blossom_tree("Tree_Street_3", location=(-4.3, +7.0, 1.2), scale=1.0, mats=mats)
    
    # 3. 建造灰色水泥电线杆 (带变压器与横跨天空拉线)
    print("Building Utility Poles and Overhead Power Lines...")
    wire_targets = [
        (-9.0, -4.5, 6.0),
        (-4.3, 10.0, 7.5),
        (4.2, 17.5, 7.5)
    ]
    build_utility_pole_with_wires("Utility_Pole_1", location=(4.2, 2.0, 1.95), mats=mats, wire_endpoints=wire_targets)
    build_utility_pole_with_wires("Utility_Pole_2", location=(4.2, 17.5, 0.0), mats=mats, wire_endpoints=[(-4.5, 17.5, 7.0)])
    
    # 4. 建造红蓝自动贩卖机与回收箱
    print("Building Modern Vending Machines...")
    build_vending_machines(location=(4.0, 19.5, 0.0), mats=mats)
    
    # 5. 建造道路转角黄色凸面反光镜
    print("Building Convex Traffic Mirror...")
    build_convex_traffic_mirror(location=(-4.8, 15.2, 0.18), mats=mats)
    
    # 6. 建造空调室外机
    print("Building AC Outdoor Units on house facades...")
    build_ac_outdoor_units(mats=mats)
    
    # 7. 建造不锈钢人行护栏
    print("Building Pedestrian Safety Guardrails...")
    build_guardrails(mats=mats)
    
    # 8. 保存与导出资产
    print("Saving updated Blend and exporting integrated GLB...")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    glb_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported integrated GLB: {glb_path}")
    
    # 9. 渲染阶段 2 验证截图
    render_stage2_inspection_views()
    print("Stage 2 Build Completed Successfully!")

if __name__ == "__main__":
    main()
