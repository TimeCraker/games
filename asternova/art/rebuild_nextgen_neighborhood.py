import os
import sys
import math
import bpy
import bmesh
import mathutils

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)
    for block in bpy.data.textures: bpy.data.textures.remove(block)
    for block in bpy.data.images: bpy.data.images.remove(block)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

# 贴图检索优先级：golden_slice 真实扫描贴图优先
TEXTURE_BASE_DIRS = [
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\golden_slice",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\models\environment\textures",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\nextgen_pbr",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures"
]

def find_tex(filename):
    for d in TEXTURE_BASE_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return None

def apply_box_uv(obj, uv_scale=1.0):
    """为网格按世界/局部尺寸进行物理米制 UV 映射，保证 glTF 导出与 Godot 采样比例真实"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=2.0 / uv_scale, correct_aspect=True, clip_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_road_uv(obj, road_width=8.0, tile_length=12.0):
    """为道路专门展开 UV：横向 X 映射到 U [0..1]，中央虚线对准道路中心 (X=0.0, U=0.5)，纵向 Y 自然平铺"""
    bpy.context.view_layer.objects.active = obj
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    if not uv_layer:
        uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            co = mesh.vertices[v_idx].co
            u = (co.x + (road_width / 2.0)) / road_width
            v = co.y / tile_length
            uv_layer.data[loop_idx].uv = (u, v)

def apply_bevel(obj, width=0.03, segments=2):
    mod = obj.modifiers.new(name='Bevel', type='BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    mod.angle_limit = math.radians(35)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.shade_smooth()
    except:
        pass

def carve_opening(wall_obj, center_x, center_y, center_z, width, height, depth=0.80):
    """墙体物理门窗洞口布尔开切，赋予真正的建筑进深与阴影"""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y, center_z))
    cutter = bpy.context.active_object
    cutter.scale = (depth, width, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = wall_obj.modifiers.new(name="Cutout", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = wall_obj
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        print(f"Boolean carve notice: {e}")
    bpy.data.objects.remove(cutter, do_unlink=True)

def build_catenary_curve(name, p_start, p_end, sag=0.35, segments=32, radius=0.012, material=None):
    """生成符合重力悬链线物理特性的三维自然下垂电缆曲线"""
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.fill_mode = 'FULL'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(segments - 1)
    
    x1, y1, z1 = p_start
    x2, y2, z2 = p_end
    for i in range(segments):
        t = i / (segments - 1)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        droop = 4.0 * sag * t * (1.0 - t)
        z = z1 + t * (z2 - z1) - droop
        polyline.points[i].co = (x, y, z, 1.0)
        
    obj = bpy.data.objects.new(name, curve_data)
    if material:
        obj.data.materials.append(material)
    return obj

# ==============================================================================
# 标准 glTF / Godot 4 兼容 PBR 材质创建器 (真实物理扫描材质)
# ==============================================================================
def create_gltf_pbr_material(name, albedo_file, normal_file=None, roughness_file=None, ao_file=None, emissive_file=None, 
                             fallback_color=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, normal_strength=1.6,
                             emissive_strength=1.2, uv_scale=(1.0, 1.0)):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    out_node = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = fallback_color
    bsdf.inputs['Roughness'].default_value = roughness_val
    bsdf.inputs['Metallic'].default_value = metallic_val
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (uv_scale[0], uv_scale[1], 1.0)
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    
    # 1. Albedo & AO
    if albedo_file:
        alb_p = find_tex(albedo_file)
        if alb_p:
            tex_alb = nodes.new('ShaderNodeTexImage')
            tex_alb.image = bpy.data.images.load(alb_p)
            links.new(mapping.outputs['Vector'], tex_alb.inputs['Vector'])
            
            ao_p = find_tex(ao_file) if ao_file else None
            if ao_p:
                tex_ao = nodes.new('ShaderNodeTexImage')
                tex_ao.image = bpy.data.images.load(ao_p)
                tex_ao.image.colorspace_settings.name = 'Non-Color'
                links.new(mapping.outputs['Vector'], tex_ao.inputs['Vector'])
                
                mix_ao = nodes.new('ShaderNodeMix')
                mix_ao.data_type = 'RGBA'
                mix_ao.blend_type = 'MULTIPLY'
                mix_ao.inputs['Factor'].default_value = 0.85
                links.new(tex_alb.outputs['Color'], mix_ao.inputs[6])
                links.new(tex_ao.outputs['Color'], mix_ao.inputs[7])
                links.new(mix_ao.outputs[2], bsdf.inputs['Base Color'])
            else:
                links.new(tex_alb.outputs['Color'], bsdf.inputs['Base Color'])
                
    # 2. Roughness
    if roughness_file:
        rgh_p = find_tex(roughness_file)
        if rgh_p:
            r_node = nodes.new('ShaderNodeTexImage')
            r_node.image = bpy.data.images.load(rgh_p)
            r_node.image.colorspace_settings.name = 'Non-Color'
            links.new(mapping.outputs['Vector'], r_node.inputs['Vector'])
            links.new(r_node.outputs['Color'], bsdf.inputs['Roughness'])
            
    # 3. Normal Map
    if normal_file:
        nrm_p = find_tex(normal_file)
        if nrm_p:
            n_node = nodes.new('ShaderNodeTexImage')
            n_node.image = bpy.data.images.load(nrm_p)
            n_node.image.colorspace_settings.name = 'Non-Color'
            links.new(mapping.outputs['Vector'], n_node.inputs['Vector'])
            
            n_map = nodes.new('ShaderNodeNormalMap')
            n_map.inputs['Strength'].default_value = normal_strength
            links.new(n_node.outputs['Color'], n_map.inputs['Color'])
            links.new(n_map.outputs['Normal'], bsdf.inputs['Normal'])
            
    # 4. Emissive
    if emissive_file:
        emi_p = find_tex(emissive_file)
        if emi_p:
            e_node = nodes.new('ShaderNodeTexImage')
            e_node.image = bpy.data.images.load(emi_p)
            links.new(mapping.outputs['Vector'], e_node.inputs['Vector'])
            links.new(e_node.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = emissive_strength
            
    return mat

def create_glass_material(name='M_Glass'):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (0.88, 0.94, 0.98, 1.0)
    bsdf.inputs['Alpha'].default_value = 0.22
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Metallic'].default_value = 0.1
    return mat

def create_metal_material(name, color, roughness=0.35, metallic=0.88):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

def create_vertical_display_plane(name, center_pos, width_y, height_z, material):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    obj = bpy.data.objects.new(name, mesh)
    hy = width_y / 2.0
    hz = height_z / 2.0
    cx, cy, cz = center_pos
    verts = [
        (cx, cy + hy, cz - hz),
        (cx, cy + hy, cz + hz),
        (cx, cy - hy, cz + hz),
        (cx, cy - hy, cz - hz)
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    for loop_idx, loop in enumerate(mesh.loops):
        uv_layer.data[loop_idx].uv = uvs[loop_idx]
    obj.data.materials.append(material)
    return obj

# ==============================================================================
# 高精建筑组件生成器：18cm 物理内嵌铝合金推拉窗与金属滴水板
# ==============================================================================
def build_recessed_window(name, center_x, center_y, center_z, width, height, mats, col, recess_depth=0.18):
    """严格按照日式双滑轨铝合金推拉窗构造：
       1. 挤压型材外窗框 (Top, Bot, Left, Right)
       2. 双导轨 (上下双导轨槽)
       3. 内外重叠推拉窗扇框架与双层中空玻璃
       4. 窗台倾斜 3.5 度冲压金属滴水板 (向室外挑出)
       5. 室内深色吸光腔体与浅色窗帘 (严格收纳在建筑内部深处，绝不凸出外墙)
    """
    depth_val = abs(recess_depth)
    inner_x = center_x - depth_val # 建筑内部在 -X 方向，凹入室内的真实深度
    frame_thick = 0.05
    
    # 1. 外窗框 (铝合金深灰型材)
    # Top frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z + height * 0.5 - frame_thick * 0.5))
    f_top = bpy.context.active_object
    f_top.name = f"{name}_Frame_Top"
    f_top.scale = (0.08, width, frame_thick)
    bpy.ops.object.transform_apply(scale=True)
    f_top.data.materials.append(mats['aluminum_dark'])
    apply_bevel(f_top, width=0.005, segments=2)
    col.objects.link(f_top)
    bpy.context.collection.objects.unlink(f_top)
    
    # Bottom frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z - height * 0.5 + frame_thick * 0.5))
    f_bot = bpy.context.active_object
    f_bot.name = f"{name}_Frame_Bot"
    f_bot.scale = (0.08, width, frame_thick)
    bpy.ops.object.transform_apply(scale=True)
    f_bot.data.materials.append(mats['aluminum_dark'])
    apply_bevel(f_bot, width=0.005, segments=2)
    col.objects.link(f_bot)
    bpy.context.collection.objects.unlink(f_bot)
    
    # Left & Right jambs
    for side_sign, s_name in [(-1, "Left"), (1, "Right")]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y + side_sign * (width * 0.5 - frame_thick * 0.5), center_z))
        f_jamb = bpy.context.active_object
        f_jamb.name = f"{name}_Frame_{s_name}"
        f_jamb.scale = (0.08, frame_thick, height - frame_thick * 2.0)
        bpy.ops.object.transform_apply(scale=True)
        f_jamb.data.materials.append(mats['aluminum_dark'])
        apply_bevel(f_jamb, width=0.005, segments=2)
        col.objects.link(f_jamb)
        bpy.context.collection.objects.unlink(f_jamb)

    # 2. 双滑轨轨道 (银白铝合金导向槽)
    for tz in [center_z - height * 0.5 + 0.045, center_z + height * 0.5 - 0.045]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, tz))
        track = bpy.context.active_object
        track.scale = (0.05, width - frame_thick * 2.0, 0.012)
        bpy.ops.object.transform_apply(scale=True)
        track.data.materials.append(mats['aluminum_silver'])
        col.objects.link(track)
        bpy.context.collection.objects.unlink(track)

    # 3. 内外重叠推拉窗扇 (Sash 1 & Sash 2)
    sash_w = (width - frame_thick * 2.0) * 0.53
    sash_h = height - frame_thick * 2.0 - 0.02
    rail_t = 0.04
    
    for s_idx, (offset_x, offset_y) in enumerate([(-0.018, -width * 0.23), (0.018, width * 0.23)]):
        sx = inner_x + offset_x
        sy = center_y + offset_y
        sash_tag = f"{name}_Sash_{s_idx}"
        
        # 窗扇边框 (上下左右)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z + sash_h * 0.5 - rail_t * 0.5))
        s_top = bpy.context.active_object
        s_top.scale = (0.035, sash_w, rail_t)
        bpy.ops.object.transform_apply(scale=True)
        s_top.data.materials.append(mats['aluminum_dark'])
        col.objects.link(s_top)
        bpy.context.collection.objects.unlink(s_top)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z - sash_h * 0.5 + rail_t * 0.5))
        s_bot = bpy.context.active_object
        s_bot.scale = (0.035, sash_w, rail_t)
        bpy.ops.object.transform_apply(scale=True)
        s_bot.data.materials.append(mats['aluminum_dark'])
        col.objects.link(s_bot)
        bpy.context.collection.objects.unlink(s_bot)
        
        for js, jn in [(-1, "L"), (1, "R")]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy + js * (sash_w * 0.5 - rail_t * 0.5), center_z))
            s_stile = bpy.context.active_object
            s_stile.scale = (0.035, rail_t, sash_h - rail_t * 2.0)
            bpy.ops.object.transform_apply(scale=True)
            s_stile.data.materials.append(mats['aluminum_dark'])
            col.objects.link(s_stile)
            bpy.context.collection.objects.unlink(s_stile)
            
        # 中空玻璃
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z))
        glass = bpy.context.active_object
        glass.name = f"{sash_tag}_Glass"
        glass.scale = (0.012, sash_w - rail_t * 1.5, sash_h - rail_t * 1.5)
        bpy.ops.object.transform_apply(scale=True)
        glass.data.materials.append(mats['glass'])
        col.objects.link(glass)
        bpy.context.collection.objects.unlink(glass)

    # 4. 冲压金属滴水板 (向室外挑出 4cm，倾斜 3.5 度排水)
    sill_mid_x = (center_x + inner_x) * 0.5 + 0.02
    sill_z = center_z - height * 0.5 - 0.015
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sill_mid_x, center_y, sill_z))
    sill = bpy.context.active_object
    sill.name = f"{name}_Metal_Sill_Drip"
    sill.scale = (depth_val + 0.08, width + 0.10, 0.025)
    sill.rotation_euler = (0, math.radians(-3.5), 0)
    bpy.ops.object.transform_apply(scale=True)
    sill.data.materials.append(mats['aluminum_dark'])
    apply_bevel(sill, width=0.005, segments=2)
    col.objects.link(sill)
    bpy.context.collection.objects.unlink(sill)

    # 5. 室内深色吸光腔体与浅色窗帘 (严格放置在 inner_x 之后，绝不凸出外墙)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x - 0.22, center_y, center_z))
    room = bpy.context.active_object
    room.name = f"{name}_RoomCavity"
    room.scale = (0.35, width - 0.02, height - 0.02)
    bpy.ops.object.transform_apply(scale=True)
    room.data.materials.append(mats['interior'])
    col.objects.link(room)
    bpy.context.collection.objects.unlink(room)

# ==============================================================================
# 屋檐连续排水天沟与垂直落水管系统 (Downspout & Gutter Assembly)
# ==============================================================================
def build_downspout_system(name, gutter_x, gutter_y_range, roof_z, downspout_x, downspout_y, ground_z, mats, col):
    """真实的日式建筑落水系统：
       - 屋檐 U 型铝合金排水天沟 (Gutter)
       - 转角立体集水斗 (Funnel)
       - 垂直 7.5cm 金属落水管 (Downspout)
       - 金属固定抱箍 (Wall Mounting Straps)
       - 地面 40 度弧形排水喇叭弯头
    """
    gy_start, gy_end = gutter_y_range
    gy_len = abs(gy_end - gy_start)
    gy_center = (gy_start + gy_end) * 0.5
    
    # 1. 排水天沟
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gutter_x, gy_center, roof_z - 0.05))
    gutter = bpy.context.active_object
    gutter.name = f"{name}_Eaves_Gutter"
    gutter.scale = (0.12, gy_len + 0.15, 0.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    gutter.data.materials.append(mats['aluminum_dark'])
    apply_bevel(gutter, width=0.012, segments=2)
    col.objects.link(gutter)
    bpy.context.collection.objects.unlink(gutter)
    
    # 2. 雨水集水斗
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(downspout_x - 0.05, downspout_y, roof_z - 0.12))
    funnel = bpy.context.active_object
    funnel.name = f"{name}_Downspout_Collector_Funnel"
    funnel.scale = (0.18, 0.22, 0.24)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    funnel.data.materials.append(mats['aluminum_dark'])
    apply_bevel(funnel, width=0.012, segments=2)
    col.objects.link(funnel)
    bpy.context.collection.objects.unlink(funnel)
    
    # 3. 垂直落水管
    pipe_len = roof_z - ground_z - 0.35
    pipe_cz = ground_z + pipe_len * 0.5 + 0.22
    bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=pipe_len, location=(downspout_x, downspout_y, pipe_cz))
    pipe = bpy.context.active_object
    pipe.name = f"{name}_Downspout_Pipe"
    pipe.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(pipe)
    bpy.context.collection.objects.unlink(pipe)
    
    # 4. 金属固定抱箍 (每 1.6m 一个)
    strap_z = ground_z + 0.8
    while strap_z < roof_z - 0.4:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(downspout_x - 0.04, downspout_y, strap_z))
        strap = bpy.context.active_object
        strap.scale = (0.12, 0.11, 0.035)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        strap.data.materials.append(mats['aluminum_silver'])
        apply_bevel(strap, width=0.005, segments=2)
        col.objects.link(strap)
        bpy.context.collection.objects.unlink(strap)
        strap_z += 1.6
        
    # 5. 地表排水弯头 (40度倾斜出水)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.042, depth=0.22, location=(downspout_x + 0.05, downspout_y, ground_z + 0.12))
    elbow = bpy.context.active_object
    elbow.name = f"{name}_Discharge_Elbow"
    elbow.rotation_euler = (0.0, math.radians(40), 0.0)
    elbow.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(elbow)
    bpy.context.collection.objects.unlink(elbow)

# ==============================================================================
# 高精 3D 空调室外机总成 (AC Outdoor Unit Assembly)
# ==============================================================================
def build_ac_unit(name, center_x, center_y, center_z, mats, col, rot_z=0.0):
    """绝区零 / CS2 级高精度空调外机：
       - 倒角钣金机壳
       - 减震橡胶脚垫
       - 圆形风扇导流圈与 3 片斜角旋转扇叶
       - 14 层百叶散热栅格
       - 侧面铜管阀门罩与保温棉冷媒弯曲管
       - 穿墙法兰盖与冷凝水排水软管
    """
    ac_sub = bpy.data.collections.new(name)
    col.children.link(ac_sub)
    
    # 1. 钣金机壳 (82cm x 32cm x 56cm)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y, center_z))
    ac_body = bpy.context.active_object
    ac_body.name = f"{name}_Chassis"
    ac_body.scale = (0.32, 0.82, 0.56)
    ac_body.rotation_euler = (0, 0, rot_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_body.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_body, width=0.018, segments=2)
    ac_sub.objects.link(ac_body)
    bpy.context.collection.objects.unlink(ac_body)
    
    # 2. 减震橡胶脚垫 x2
    for fy_offset in [-0.30, 0.30]:
        fy = center_y + fy_offset * math.cos(rot_z)
        fx = center_x - fy_offset * math.sin(rot_z)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(fx, fy, center_z - 0.26))
        foot = bpy.context.active_object
        foot.scale = (0.36, 0.12, 0.05)
        foot.rotation_euler = (0, 0, rot_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        foot.data.materials.append(mats['cable_rubber'])
        apply_bevel(foot, width=0.008, segments=2)
        ac_sub.objects.link(foot)
        bpy.context.collection.objects.unlink(foot)
        
    # 3. 风扇导流圈与扇叶 (朝向 +X)
    front_offset = 0.17
    fan_x = center_x + front_offset * math.cos(rot_z)
    fan_y = center_y + front_offset * math.sin(rot_z) - 0.12
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.03, location=(fan_x, fan_y, center_z))
    shroud = bpy.context.active_object
    shroud.name = f"{name}_Fan_Shroud"
    shroud.rotation_euler = (0, math.radians(90), rot_z)
    shroud.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    ac_sub.objects.link(shroud)
    bpy.context.collection.objects.unlink(shroud)
    
    # 3片立体扇叶
    for b_idx in range(3):
        rot = b_idx * (2.0 * math.pi / 3.0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(fan_x + 0.01, fan_y + 0.08 * math.cos(rot), center_z + 0.08 * math.sin(rot)))
        blade = bpy.context.active_object
        blade.scale = (0.015, 0.06, 0.16)
        blade.rotation_euler = (rot, math.radians(15), rot_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        blade.data.materials.append(mats['aluminum_dark'])
        ac_sub.objects.link(blade)
        bpy.context.collection.objects.unlink(blade)
        
    # 4. 百叶百叶散热栅格 (12片水平条)
    for l_idx in range(12):
        lz = center_z - 0.20 + l_idx * 0.035
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(fan_x + 0.02, fan_y, lz))
        slat = bpy.context.active_object
        slat.scale = (0.012, 0.42, 0.012)
        slat.rotation_euler = (0, 0, rot_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        slat.data.materials.append(mats['props_ac_meter'])
        ac_sub.objects.link(slat)
        bpy.context.collection.objects.unlink(slat)
        
    # 5. 侧面阀门盖
    valve_x = center_x
    valve_y = center_y + 0.42
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(valve_x, valve_y, center_z - 0.06))
    vcov = bpy.context.active_object
    vcov.scale = (0.16, 0.06, 0.22)
    vcov.rotation_euler = (0, 0, rot_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    vcov.data.materials.append(mats['props_ac_meter'])
    apply_bevel(vcov, width=0.008, segments=2)
    ac_sub.objects.link(vcov)
    bpy.context.collection.objects.unlink(vcov)
    
    # 6. 包裹保温棉的弯曲冷媒管 (曲线引向墙面)
    p_curve = bpy.data.curves.new(f'{name}_CopperPipe', type='CURVE')
    p_curve.dimensions = '3D'
    p_curve.fill_mode = 'FULL'
    p_curve.bevel_depth = 0.026
    p_curve.bevel_resolution = 4
    spline = p_curve.splines.new('BEZIER')
    pts = [
        (valve_x, valve_y, center_z - 0.08),
        (valve_x - 0.16, valve_y + 0.10, center_z + 0.10),
        (valve_x - 0.20, valve_y + 0.15, center_z + 0.65),
        (valve_x - 0.22, valve_y + 0.15, center_z + 1.10)
    ]
    spline.bezier_points.add(len(pts) - 1)
    for i, pt in enumerate(pts):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    p_obj = bpy.data.objects.new(f'{name}_CopperPipe', p_curve)
    p_obj.data.materials.append(mats['props_ac_meter'])
    ac_sub.objects.link(p_obj)
    
    # 穿墙法兰盘
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.04, location=(valve_x - 0.22, valve_y + 0.15, center_z + 1.10))
    flange = bpy.context.active_object
    flange.rotation_euler = (0, math.radians(90), 0)
    flange.data.materials.append(mats['props_ac_meter'])
    bpy.ops.object.shade_smooth()
    ac_sub.objects.link(flange)
    bpy.context.collection.objects.unlink(flange)

# ==============================================================================
# 00. 全封闭 360° 天际线与宏观街区
# ==============================================================================
def build_environment_backdrop(mats):
    col = bpy.data.collections.new('00_Environment_Backdrop')
    bpy.context.scene.collection.children.link(col)
    
    # 宏观地面 (160m x 160m)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, -0.05))
    ground = bpy.context.active_object
    ground.name = 'Macro_District_Ground'
    ground.scale = (160.0, 160.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ground, uv_scale=0.5)
    ground.data.materials.append(mats['asphalt_road'])
    col.objects.link(ground)
    bpy.context.collection.objects.unlink(ground)
    
    # 北侧台地护坡与山顶神社住宅群 (Y: -30 to -65)
    for layer_i, ly in enumerate([-32.0, -42.0, -52.0]):
        lz = 6.0 + layer_i * 3.5
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, ly, lz + 1.75))
        wall = bpy.context.active_object
        wall.name = f'North_Retaining_Wall_{layer_i}'
        wall.scale = (70.0, 1.5, 3.5)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(wall, uv_scale=1.0)
        wall.data.materials.append(mats['concrete_curb'])
        apply_bevel(wall, width=0.08, segments=2)
        col.objects.link(wall)
        bpy.context.collection.objects.unlink(wall)
        
        for hx in [-20.0, 0.0, 20.0]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.5, lz + 5.0))
            nh = bpy.context.active_object
            nh.name = f'North_Hill_House_{layer_i}_{hx}'
            nh.scale = (12.0, 7.5, 6.5)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            apply_box_uv(nh, uv_scale=1.0)
            nh.data.materials.append(mats['wall_plaster'])
            apply_bevel(nh, width=0.05, segments=2)
            col.objects.link(nh)
            bpy.context.collection.objects.unlink(nh)
            
            # 屋顶
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.5, lz + 8.5))
            nr = bpy.context.active_object
            nr.scale = (13.0, 8.5, 0.6)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            apply_box_uv(nr, uv_scale=1.5)
            nr.data.materials.append(mats['aluminum_dark'])
            col.objects.link(nr)
            bpy.context.collection.objects.unlink(nr)

    # 北侧山顶神社大鸟居 (朱红漆木，山顶标志地标)
    torii_y = -27.5
    torii_z = 6.2
    for px in [-2.5, 2.5]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=4.2, location=(px, torii_y, torii_z + 2.1))
        t_col = bpy.context.active_object
        t_col.data.materials.append(mats['torii_red'])
        bpy.ops.object.shade_smooth()
        col.objects.link(t_col)
        bpy.context.collection.objects.unlink(t_col)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, torii_y, torii_z + 4.3))
    t_beam1 = bpy.context.active_object
    t_beam1.scale = (6.4, 0.45, 0.35)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    t_beam1.data.materials.append(mats['torii_black'])
    col.objects.link(t_beam1)
    bpy.context.collection.objects.unlink(t_beam1)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, torii_y, torii_z + 3.4))
    t_beam2 = bpy.context.active_object
    t_beam2.scale = (5.6, 0.35, 0.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    t_beam2.data.materials.append(mats['torii_red'])
    col.objects.link(t_beam2)
    bpy.context.collection.objects.unlink(t_beam2)

    # 南侧现代轻轨高架桥与黄色列车
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 42.0, 7.8))
    rail_deck = bpy.context.active_object
    rail_deck.name = 'Monorail_Deck'
    rail_deck.scale = (90.0, 8.5, 1.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(rail_deck, uv_scale=1.0)
    rail_deck.data.materials.append(mats['concrete_curb'])
    apply_bevel(rail_deck, width=0.08, segments=2)
    col.objects.link(rail_deck)
    bpy.context.collection.objects.unlink(rail_deck)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, 42.0, 10.2))
    train = bpy.context.active_object
    train.name = 'Monorail_Train'
    train.scale = (22.0, 3.2, 3.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    train.data.materials.append(mats['train_yellow'])
    apply_bevel(train, width=0.1, segments=2)
    col.objects.link(train)
    bpy.context.collection.objects.unlink(train)
    
    for px in [-24.0, 0.0, 24.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, 42.0, 3.8))
        pillar = bpy.context.active_object
        pillar.scale = (3.2, 3.6, 7.6)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(pillar, uv_scale=1.0)
        pillar.data.materials.append(mats['concrete_curb'])
        apply_bevel(pillar, width=0.06, segments=2)
        col.objects.link(pillar)
        bpy.context.collection.objects.unlink(pillar)

    # 南侧远景大厦群
    for bx, bw, bh in [(-28.0, 20.0, 24.0), (0.0, 24.0, 28.0), (28.0, 20.0, 22.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, 54.0, bh / 2.0))
        tower = bpy.context.active_object
        tower.name = f'South_Tower_{bx}'
        tower.scale = (bw, 14.0, bh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(tower, uv_scale=1.0)
        tower.data.materials.append(mats['wall_plaster'])
        apply_bevel(tower, width=0.05, segments=2)
        col.objects.link(tower)
        bpy.context.collection.objects.unlink(tower)

    # 西侧公寓天际线 (X = -28.0)
    for wy, wh, ww in [(-18.0, 20.0, 14.0), (2.0, 24.0, 16.0), (22.0, 21.0, 14.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-28.0, wy, wh / 2.0))
        mansion = bpy.context.active_object
        mansion.name = f'West_Mansion_{wy}'
        mansion.scale = (14.0, ww, wh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(mansion, uv_scale=1.0)
        mansion.data.materials.append(mats['wall_plaster'])
        apply_bevel(mansion, width=0.05, segments=2)
        col.objects.link(mansion)
        bpy.context.collection.objects.unlink(mansion)

    # 东侧高台边界墙与建筑
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(10.5, 0.0, 2.5))
    e_wall = bpy.context.active_object
    e_wall.name = 'East_Boundary_Wall'
    e_wall.scale = (1.5, 75.0, 5.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(e_wall, uv_scale=1.0)
    e_wall.data.materials.append(mats['concrete_curb'])
    apply_bevel(e_wall, width=0.05, segments=2)
    col.objects.link(e_wall)
    bpy.context.collection.objects.unlink(e_wall)
    
    for ey, eh in [(-16.0, 18.0), (6.0, 22.0), (24.0, 19.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(22.0, ey, eh / 2.0))
        e_house = bpy.context.active_object
        e_house.scale = (14.0, 14.0, eh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(e_house, uv_scale=1.0)
        e_house.data.materials.append(mats['wall_plaster'])
        col.objects.link(e_house)
        bpy.context.collection.objects.unlink(e_house)

    return col

# ==============================================================================
# 01. 道路、40m 跑酷长坡与微表面市政构造 (井盖、透空雨水箅子、3D 导盲砖)
# ==============================================================================
def build_terrain_and_roads(mats):
    col = bpy.data.collections.new('01_Roads_And_Terrain')
    bpy.context.scene.collection.children.link(col)
    
    slope_angle = math.atan2(-6.0, 35.0) # 约 9.8 度
    
    # 1. 南端生活广场主路 (Y: 10.0 to 36.0, X: -4.0 to 4.0)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 23.0, 0.005))
    plz_road = bpy.context.active_object
    plz_road.name = 'Road_South_Plaza'
    plz_road.scale = (8.0, 26.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_road_uv(plz_road, road_width=8.0, tile_length=12.0)
    plz_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(plz_road)
    bpy.context.collection.objects.unlink(plz_road)
    
    # 2. 南端生活广场西侧人行道 (花岗岩石砖)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, 23.0, 0.075))
    plz_sw_w = bpy.context.active_object
    plz_sw_w.name = 'Sidewalk_Plaza_West'
    plz_sw_w.scale = (10.0, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(plz_sw_w, uv_scale=1.0)
    plz_sw_w.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_w)
    bpy.context.collection.objects.unlink(plz_sw_w)
    
    # 3. 倒角路缘石
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.1, 23.0, 0.075))
    curb_w = bpy.context.active_object
    curb_w.name = 'Curb_Plaza_West'
    curb_w.scale = (0.2, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(curb_w, uv_scale=1.0)
    curb_w.data.materials.append(mats['concrete_curb'])
    apply_bevel(curb_w, width=0.02, segments=2)
    col.objects.link(curb_w)
    bpy.context.collection.objects.unlink(curb_w)
    
    # 4. 黄色导盲砖带
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-4.8, 23.0, 0.152))
    plz_tac = bpy.context.active_object
    plz_tac.name = 'Tactile_Plaza_West'
    plz_tac.scale = (0.6, 26.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(plz_tac, uv_scale=2.0)
    plz_tac.data.materials.append(mats['tactile_paving'])
    col.objects.link(plz_tac)
    bpy.context.collection.objects.unlink(plz_tac)
    
    # 在 Shot 2 近景区域铺设真实的 3D 实心导盲凸珠 (BlisterDot)
    dot_col = bpy.data.collections.new("Tactile_3D_Domes")
    col.children.link(dot_col)
    dome_mesh = None
    for y_idx in range(12):
        y_pos = 14.0 + y_idx * 0.15
        for x_idx in range(4):
            x_pos = -4.95 + x_idx * 0.12
            if dome_mesh is None:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=(x_pos, y_pos, 0.156))
                dome = bpy.context.active_object
                dome.scale = (1.0, 1.0, 0.35)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                dome.data.materials.append(mats['tactile_paving'])
                bpy.ops.object.shade_smooth()
                dome_mesh = dome.data
                dot_col.objects.link(dome)
                bpy.context.collection.objects.unlink(dome)
            else:
                d_obj = bpy.data.objects.new(f"BlisterDot_{y_idx}_{x_idx}", dome_mesh)
                d_obj.location = (x_pos, y_pos, 0.156)
                dot_col.objects.link(d_obj)

    # 5. 真实沉降铸铁井盖 (Sunken Cast Iron Manhole) 位于 X: -1.8, Y: 18.0
    # 混凝土沉降环外框
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.025, location=(-1.8, 18.0, 0.002))
    mh_collar = bpy.context.active_object
    mh_collar.name = "Manhole_Collar"
    mh_collar.data.materials.append(mats['concrete_curb'])
    apply_bevel(mh_collar, width=0.015, segments=2)
    col.objects.link(mh_collar)
    bpy.context.collection.objects.unlink(mh_collar)
    
    # 铸铁沉降盘盖 (下沉 1cm，消除贴图悬浮感)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.022, location=(-1.8, 18.0, -0.004))
    mh_lid = bpy.context.active_object
    mh_lid.name = "Manhole_Cover_Lid"
    mh_lid.data.materials.append(mats['metal_manhole'])
    apply_bevel(mh_lid, width=0.008, segments=2)
    col.objects.link(mh_lid)
    bpy.context.collection.objects.unlink(mh_lid)

    # 6. 透空格栅雨水箅子与深色暗沟 (Drain Grate & Sewer Void Pit) 位于路缘石旁 (X: -3.85, Y: 15.5)
    # 暗沟黑洞腔体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.85, 15.5, -0.08))
    sewer_pit = bpy.context.active_object
    sewer_pit.name = "Sewer_Void_Pit"
    sewer_pit.scale = (0.28, 0.85, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sewer_pit.data.materials.append(mats['interior'])
    col.objects.link(sewer_pit)
    bpy.context.collection.objects.unlink(sewer_pit)
    
    # 雨水箅子外铁框
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.85, 15.5, -0.004))
    grate_frame = bpy.context.active_object
    grate_frame.name = "Drain_Grate_Frame"
    grate_frame.scale = (0.28, 0.85, 0.016)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    grate_frame.data.materials.append(mats['metal_manhole'])
    apply_bevel(grate_frame, width=0.008, segments=2)
    col.objects.link(grate_frame)
    bpy.context.collection.objects.unlink(grate_frame)
    
    # 8 根铸铁透空格栅条
    for s in range(8):
        sy = 15.18 + s * 0.10
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.85, sy, 0.002))
        bar = bpy.context.active_object
        bar.scale = (0.22, 0.024, 0.012)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bar.data.materials.append(mats['metal_manhole'])
        col.objects.link(bar)
        bpy.context.collection.objects.unlink(bar)

    # 7. 40m 战术跑酷坡道 (Central Long Ramp, Y: +10.0 to -25.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -7.5, 3.0))
    ramp_road = bpy.context.active_object
    ramp_road.name = 'Road_Central_Slope_Ramp'
    ramp_road.scale = (7.0, 35.5, 0.2)
    ramp_road.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_road_uv(ramp_road, road_width=7.0, tile_length=12.0)
    ramp_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(ramp_road)
    bpy.context.collection.objects.unlink(ramp_road)
    
    # 坡道西侧人行道
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.8, -7.5, 3.12))
    ramp_sw = bpy.context.active_object
    ramp_sw.name = 'Sidewalk_Slope_West'
    ramp_sw.scale = (2.6, 35.5, 0.24)
    ramp_sw.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ramp_sw, uv_scale=1.0)
    ramp_sw.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ramp_sw)
    bpy.context.collection.objects.unlink(ramp_sw)
    
    # 坡道东侧不锈钢防护栏杆
    for ri in range(12):
        ry = 8.0 - ri * 2.8
        rz = (10.0 - ry) * (6.0 / 35.0) + 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.0, location=(3.6, ry, rz))
        post = bpy.context.active_object
        post.data.materials.append(mats['aluminum_silver'])
        col.objects.link(post)
        bpy.context.collection.objects.unlink(post)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.6, -7.5, 3.95))
    rail_h = bpy.context.active_object
    rail_h.scale = (0.05, 35.5, 0.05)
    rail_h.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rail_h.data.materials.append(mats['aluminum_silver'])
    col.objects.link(rail_h)
    bpy.context.collection.objects.unlink(rail_h)

    # 坡道东侧挡土墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.65, -7.5, 1.5))
    ramp_retaining = bpy.context.active_object
    ramp_retaining.name = 'Ramp_East_Retaining_Wall'
    ramp_retaining.scale = (0.3, 35.5, 3.2)
    ramp_retaining.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ramp_retaining, uv_scale=1.0)
    ramp_retaining.data.materials.append(mats['concrete_curb'])
    col.objects.link(ramp_retaining)
    bpy.context.collection.objects.unlink(ramp_retaining)

    # 坡道西侧挡土墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-6.15, -7.5, 1.5))
    ramp_w_retaining = bpy.context.active_object
    ramp_w_retaining.name = 'Ramp_West_Retaining_Wall'
    ramp_w_retaining.scale = (0.3, 35.5, 3.2)
    ramp_w_retaining.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ramp_w_retaining, uv_scale=1.0)
    ramp_w_retaining.data.materials.append(mats['concrete_curb'])
    col.objects.link(ramp_w_retaining)
    bpy.context.collection.objects.unlink(ramp_w_retaining)

    # 西侧住宅区水平平整地基地面
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.0, -7.5, 0.0))
    west_flat_ground = bpy.context.active_object
    west_flat_ground.name = 'West_Residential_Foundation'
    west_flat_ground.scale = (14.0, 40.0, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(west_flat_ground, uv_scale=1.0)
    west_flat_ground.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(west_flat_ground)
    bpy.context.collection.objects.unlink(west_flat_ground)

    # 8. 北侧山顶高台广场 (Y: -25.0 to -35.0, Z: 6.0m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -30.0, 5.9))
    n_plat = bpy.context.active_object
    n_plat.name = 'North_Terrace_Plaza'
    n_plat.scale = (28.0, 12.0, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(n_plat, uv_scale=1.0)
    n_plat.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(n_plat)
    bpy.context.collection.objects.unlink(n_plat)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -30.0, 3.0))
    n_plat_base = bpy.context.active_object
    n_plat_base.name = 'North_Terrace_Base'
    n_plat_base.scale = (32.0, 14.0, 6.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(n_plat_base, uv_scale=1.0)
    n_plat_base.data.materials.append(mats['concrete_curb'])
    col.objects.link(n_plat_base)
    bpy.context.collection.objects.unlink(n_plat_base)

    return col

# ==============================================================================
# 02. 核心建筑 A：日式现代民宅 (物理开窗、18cm 内嵌铝合金窗、天沟、落水管与 3D 空调外机)
# ==============================================================================
def build_house_a(mats):
    col = bpy.data.collections.new('02_House_A')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.25, -5.5
    
    # 1. 混凝土基础基座 (Plinth)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.15))
    plinth = bpy.context.active_object
    plinth.name = "HouseA_Plinth"
    plinth.scale = (7.6, 7.6, 0.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.03, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 2. 1F 主墙体 (X: -14.25, Y: -5.5, Z: 1.85, 深度 7.4m x 宽度 7.4m x 高度 2.8m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 1.85))
    wall_1f = bpy.context.active_object
    wall_1f.name = 'HouseA_Wall_1F'
    wall_1f.scale = (7.4, 7.4, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(wall_1f, uv_scale=1.0)
    wall_1f.data.materials.append(mats['wall_plaster'])
    
    # 墙面物理开洞：
    # 东侧入户门洞 (X: -10.55, Y: -7.5, Z: 1.25, 宽 1.2m x 高 2.2m)
    carve_opening(wall_1f, center_x=-10.55, center_y=-7.5, center_z=1.25, width=1.2, height=2.2, depth=0.8)
    # 东侧 1F 大推拉窗洞 (X: -10.55, Y: -4.2, Z: 1.65, 宽 2.2m x 高 1.4m)
    carve_opening(wall_1f, center_x=-10.55, center_y=-4.2, center_z=1.65, width=2.2, height=1.4, depth=0.8)
    apply_bevel(wall_1f, width=0.03, segments=2)
    col.objects.link(wall_1f)
    bpy.context.collection.objects.unlink(wall_1f)
    
    # 楼层间铝合金水平腰线 (Belt Course)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 3.28))
    belt = bpy.context.active_object
    belt.name = 'HouseA_Mid_Belt'
    belt.scale = (7.45, 7.45, 0.12)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    apply_bevel(belt, width=0.015, segments=2)
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 3. 2F 主墙体 (Z: 4.80, 高度 2.9m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.2, by, 4.80))
    wall_2f = bpy.context.active_object
    wall_2f.name = 'HouseA_Wall_2F'
    wall_2f.scale = (7.0, 7.4, 2.9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(wall_2f, uv_scale=1.0)
    wall_2f.data.materials.append(mats['wall_plaster'])
    
    # 2F 窗洞开切
    carve_opening(wall_2f, center_x=-10.75, center_y=-4.2, center_z=4.75, width=1.8, height=1.3, depth=0.8)
    carve_opening(wall_2f, center_x=-10.75, center_y=-7.5, center_z=4.75, width=1.3, height=1.1, depth=0.8)
    apply_bevel(wall_2f, width=0.03, segments=2)
    col.objects.link(wall_2f)
    bpy.context.collection.objects.unlink(wall_2f)
    
    # 4. 屋檐挑檐压顶 (Roof Fascia)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 6.35))
    roof = bpy.context.active_object
    roof.name = 'HouseA_Roof_Fascia'
    roof.scale = (8.2, 8.2, 0.26)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 5. 18cm 物理内嵌铝合金推拉窗组件
    # 1F 主窗
    build_recessed_window("HouseA_Window_1F", center_x=-10.55, center_y=-4.2, center_z=1.65, width=2.1, height=1.35, mats=mats, col=col, recess_depth=-0.18)
    # 2F 主卧窗
    build_recessed_window("HouseA_Window_2F_1", center_x=-10.75, center_y=-4.2, center_z=4.75, width=1.75, height=1.25, mats=mats, col=col, recess_depth=-0.18)
    # 2F 次卧窗
    build_recessed_window("HouseA_Window_2F_2", center_x=-10.75, center_y=-7.5, center_z=4.75, width=1.25, height=1.05, mats=mats, col=col, recess_depth=-0.18)

    # 6. 入户玄关防盗门与悬挑玻璃雨棚
    # 门框内凹
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.70, -7.5, 1.25))
    door = bpy.context.active_object
    door.name = 'HouseA_Entrance_Door'
    door.scale = (0.06, 1.10, 2.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    door.data.materials.append(mats['aluminum_dark'])
    apply_bevel(door, width=0.01, segments=2)
    col.objects.link(door)
    bpy.context.collection.objects.unlink(door)
    
    # 银白拉丝长把手
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.75, location=(-10.65, -7.1, 1.10))
    handle = bpy.context.active_object
    handle.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(handle)
    bpy.context.collection.objects.unlink(handle)
    
    # 悬挑雨棚 (Canopy)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.05, -7.5, 2.45))
    canopy = bpy.context.active_object
    canopy.name = 'HouseA_Entrance_Canopy'
    canopy.scale = (1.25, 1.6, 0.04)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(mats['aluminum_dark'])
    apply_bevel(canopy, width=0.008, segments=2)
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    # 雨棚夹胶玻璃
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.05, -7.5, 2.48))
    c_glass = bpy.context.active_object
    c_glass.scale = (1.15, 1.5, 0.015)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    c_glass.data.materials.append(mats['glass'])
    col.objects.link(c_glass)
    bpy.context.collection.objects.unlink(c_glass)
    
    # 电表箱 (Electric Meter Box)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.65, -6.5, 1.50))
    meter = bpy.context.active_object
    meter.name = 'HouseA_Meter_Box'
    meter.scale = (0.16, 0.28, 0.38)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    meter.data.materials.append(mats['props_ac_meter'])
    apply_bevel(meter, width=0.01, segments=2)
    col.objects.link(meter)
    bpy.context.collection.objects.unlink(meter)

    # 7. 屋檐排水天沟与垂直落水管系统
    build_downspout_system(
        name="HouseA",
        gutter_x=-10.15,
        gutter_y_range=(-9.2, -1.8),
        roof_z=6.35,
        downspout_x=-10.35,
        downspout_y=-2.0,
        ground_z=0.15,
        mats=mats,
        col=col
    )

    # 8. 真实 3D 空调室外机 (挂接在正面角落 X: -10.35, Y: -2.8, Z: 0.55)
    build_ac_unit("HouseA_AC_Ground", center_x=-10.35, center_y=-2.8, center_z=0.55, mats=mats, col=col, rot_z=0.0)

    # 9. 二楼跑酷阳台与深色型材护栏
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.95, -4.2, 3.25))
    balc = bpy.context.active_object
    balc.name = 'HouseA_Balcony'
    balc.scale = (1.4, 2.8, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc.data.materials.append(mats['concrete_curb'])
    apply_bevel(balc, width=0.015, segments=2)
    col.objects.link(balc)
    bpy.context.collection.objects.unlink(balc)
    
    # 阳台型材护栏
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.28, -4.2, 3.75))
    b_rail = bpy.context.active_object
    b_rail.scale = (0.06, 2.8, 0.90)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b_rail.data.materials.append(mats['aluminum_dark'])
    col.objects.link(b_rail)
    bpy.context.collection.objects.unlink(b_rail)

    return col

# ==============================================================================
# 03. 核心建筑 B：24H 便利店与次世代 3D 货架 + 机械双联自动贩卖机
# ==============================================================================
def build_house_b_convenience_store(mats):
    col = bpy.data.collections.new('03_House_B_Convenience_Store')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.25, 19.5
    
    # 1. 商铺主体上部建筑 (二楼与门楣墙体, Z: 2.7 to 7.0, 高度 4.3m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 4.85))
    store_upper = bpy.context.active_object
    store_upper.name = 'Store_UpperFacade'
    store_upper.scale = (8.6, 11.0, 4.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_upper, uv_scale=1.0)
    store_upper.data.materials.append(mats['wall_plaster'])
    apply_bevel(store_upper, width=0.04, segments=2)
    col.objects.link(store_upper)
    bpy.context.collection.objects.unlink(store_upper)

    # 2. 一楼实墙与室内地面
    # 后墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-18.1, by, 1.35))
    store_back = bpy.context.active_object
    store_back.scale = (0.9, 11.0, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_back, uv_scale=1.0)
    store_back.data.materials.append(mats['wall_plaster'])
    col.objects.link(store_back)
    bpy.context.collection.objects.unlink(store_back)

    # 北侧山墙与南侧山墙
    for sy, sname in [(14.2, "Store_SideWall_N"), (24.8, "Store_SideWall_S")]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, sy, 1.35))
        swall = bpy.context.active_object
        swall.name = sname
        swall.scale = (8.6, 0.8, 2.7)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(swall, uv_scale=1.0)
        swall.data.materials.append(mats['wall_plaster'])
        col.objects.link(swall)
        bpy.context.collection.objects.unlink(swall)

    # 室内地砖
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.05))
    store_floor = bpy.context.active_object
    store_floor.name = 'Store_InteriorFloor'
    store_floor.scale = (8.6, 11.0, 0.1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_floor, uv_scale=1.0)
    store_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(store_floor)
    bpy.context.collection.objects.unlink(store_floor)
    
    # 3. 门头 24H 立体灯箱招牌 (深色铝合金外壳 + 亚克力正面发光面)
    # 外壳框架
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.85, 19.5, 3.4))
    sign_frame = bpy.context.active_object
    sign_frame.name = 'ConvenienceStore_Sign_Frame'
    sign_frame.scale = (0.24, 9.35, 1.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sign_frame.data.materials.append(mats['aluminum_dark'])
    apply_bevel(sign_frame, width=0.015, segments=2)
    col.objects.link(sign_frame)
    bpy.context.collection.objects.unlink(sign_frame)
    
    # 正面发光招牌
    sign_face = create_vertical_display_plane('ConvenienceStore_Sign_Face', (-9.72, 19.5, 3.4), 9.2, 1.1, mats['store_sign'])
    col.objects.link(sign_face)
    
    # 4. 门脸大落地玻璃幕墙与自动门铝合金型材
    # 铝合金立柱框架
    for my in [14.6, 17.5, 21.5, 24.4]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.88, my, 1.35))
        mullion = bpy.context.active_object
        mullion.scale = (0.08, 0.08, 2.65)
        bpy.ops.object.transform_apply(scale=True)
        mullion.data.materials.append(mats['aluminum_dark'])
        col.objects.link(mullion)
        bpy.context.collection.objects.unlink(mullion)
        
    # 高透玻璃
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.88, 19.5, 1.35))
    store_glass = bpy.context.active_object
    store_glass.name = 'Store_Glass'
    store_glass.scale = (0.04, 9.6, 2.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    store_glass.data.materials.append(mats['glass'])
    col.objects.link(store_glass)
    bpy.context.collection.objects.unlink(store_glass)
    
    # 5. 真实三维立体多层金属货架与 3D 商品陈列 (彻底告别 2D 贴图平面！)
    shelf_col = bpy.data.collections.new("ConvenienceStore_3D_Shelves")
    col.children.link(shelf_col)
    
    # 构建 2 组纵深双面货架 (分别位于 X: -11.5 和 X: -13.5，Y: 16.5 到 22.5)
    for sh_idx, shelf_x in enumerate([-11.5, -13.8]):
        # 4 根金属承重立柱
        for post_y in [16.8, 22.2]:
            for post_x in [shelf_x - 0.35, shelf_x + 0.35]:
                bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2.1, location=(post_x, post_y, 1.10))
                p_obj = bpy.context.active_object
                p_obj.data.materials.append(mats['aluminum_dark'])
                shelf_col.objects.link(p_obj)
                bpy.context.collection.objects.unlink(p_obj)
                
        # 4 层金属层板与 3D 物品排布
        for layer_i in range(4):
            layer_z = 0.35 + layer_i * 0.48
            # 金属横板
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(shelf_x, 19.5, layer_z))
            tier = bpy.context.active_object
            tier.scale = (0.75, 5.4, 0.035)
            bpy.ops.object.transform_apply(scale=True)
            tier.data.materials.append(mats['aluminum_dark'])
            apply_bevel(tier, width=0.005, segments=2)
            shelf_col.objects.link(tier)
            bpy.context.collection.objects.unlink(tier)
            
            # 在每层货架上陈列 3D 商品 (易拉罐饮料、水瓶、盒装零食)
            for item_y_idx in range(14):
                item_y = 17.1 + item_y_idx * 0.36
                for row_x_idx in range(2):
                    item_x = shelf_x - 0.20 + row_x_idx * 0.40
                    if layer_i % 2 == 0:
                        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.15, location=(item_x, item_y, layer_z + 0.09))
                        can = bpy.context.active_object
                        mat_can = mats['torii_red'] if (item_y_idx % 3 == 0) else (mats['train_yellow'] if (item_y_idx % 3 == 1) else mats['aluminum_silver'])
                        can.data.materials.append(mat_can)
                        shelf_col.objects.link(can)
                        bpy.context.collection.objects.unlink(can)
                    else:
                        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(item_x, item_y, layer_z + 0.10))
                        box = bpy.context.active_object
                        box.scale = (0.10, 0.18, 0.18)
                        bpy.ops.object.transform_apply(scale=True)
                        mat_box = mats['tactile_paving'] if (item_y_idx % 2 == 0) else mats['props_ac_meter']
                        box.data.materials.append(mat_box)
                        shelf_col.objects.link(box)
                        bpy.context.collection.objects.unlink(box)

    # 6. 次世代机械双联自动贩卖机 (绝区零级工业造型与街头生活气息)
    vm_col = bpy.data.collections.new("NextGen_Dual_Vending_Machine")
    col.children.link(vm_col)
    
    vm_cx, vm_cy = -9.45, 23.5
    # A. 贩卖机主箱体 (带倒角)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx, vm_cy, 1.05))
    vm_body = bpy.context.active_object
    vm_body.name = 'Vending_Machines_Body'
    vm_body.scale = (0.85, 2.4, 1.95)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    vm_body.data.materials.append(mats['aluminum_dark'])
    apply_bevel(vm_body, width=0.025, segments=2)
    vm_col.objects.link(vm_body)
    bpy.context.collection.objects.unlink(vm_body)
    
    # B. 底部黑色减震底座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx, vm_cy, 0.08))
    vm_base = bpy.context.active_object
    vm_base.scale = (0.90, 2.45, 0.14)
    bpy.ops.object.transform_apply(scale=True)
    vm_base.data.materials.append(mats['cable_rubber'])
    apply_bevel(vm_base, width=0.01, segments=2)
    vm_col.objects.link(vm_base)
    bpy.context.collection.objects.unlink(vm_base)
    
    # C. 凹入式物理出货舱 (Pickup Compartment，凹入 15cm)
    for p_sign in [-0.55, 0.55]:
        py = vm_cy + p_sign
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx + 0.32, py, 0.40))
        cavity = bpy.context.active_object
        cavity.scale = (0.16, 0.65, 0.28)
        bpy.ops.object.transform_apply(scale=True)
        cavity.data.materials.append(mats['interior'])
        vm_col.objects.link(cavity)
        bpy.context.collection.objects.unlink(cavity)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx + 0.40, py, 0.42))
        flap = bpy.context.active_object
        flap.scale = (0.02, 0.62, 0.24)
        flap.rotation_euler = (0, math.radians(12), 0)
        bpy.ops.object.transform_apply(scale=True)
        flap.data.materials.append(mats['aluminum_dark'])
        vm_col.objects.link(flap)
        bpy.context.collection.objects.unlink(flap)

    # D. 投币退币机械部件与按键面板 (Coin slot, Change return, Keypad)
    for p_sign in [-0.15, 0.95]:
        my = vm_cy + p_sign
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx + 0.43, my, 1.05))
        c_panel = bpy.context.active_object
        c_panel.scale = (0.04, 0.18, 0.45)
        bpy.ops.object.transform_apply(scale=True)
        c_panel.data.materials.append(mats['aluminum_silver'])
        apply_bevel(c_panel, width=0.008, segments=2)
        vm_col.objects.link(c_panel)
        bpy.context.collection.objects.unlink(c_panel)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_cx + 0.455, my, 1.18))
        slot = bpy.context.active_object
        slot.scale = (0.015, 0.06, 0.012)
        bpy.ops.object.transform_apply(scale=True)
        slot.data.materials.append(mats['interior'])
        vm_col.objects.link(slot)
        bpy.context.collection.objects.unlink(slot)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.04, location=(vm_cx + 0.46, my, 1.10))
        lever = bpy.context.active_object
        lever.rotation_euler = (0, math.radians(90), 0)
        lever.data.materials.append(mats['aluminum_dark'])
        vm_col.objects.link(lever)
        bpy.context.collection.objects.unlink(lever)

    # E. 正面 2K PBR 印刷面 (指向 +X) 与高亮亚克力橱窗护罩
    vm_face = create_vertical_display_plane('Vending_Machines_Front_Panel', (-9.01, 23.5, 1.05), 2.38, 1.92, mats['vending_machine'])
    vm_col.objects.link(vm_face)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.99, 23.5, 1.45))
    vm_glass = bpy.context.active_object
    vm_glass.name = 'Vending_Glass_Shield'
    vm_glass.scale = (0.02, 2.3, 0.92)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    vm_glass.data.materials.append(mats['glass'])
    vm_col.objects.link(vm_glass)
    bpy.context.collection.objects.unlink(vm_glass)

    # F. 侧面日式双孔专用饮料瓶分类垃圾桶 (Can & Bottle Recycle Bin)
    bin_x, bin_y, bin_z = -9.45, 25.05, 0.48
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bin_x, bin_y, bin_z))
    r_bin = bpy.context.active_object
    r_bin.name = 'Bottle_Recycle_Bin'
    r_bin.scale = (0.50, 0.65, 0.85)
    bpy.ops.object.transform_apply(scale=True)
    r_bin.data.materials.append(mats['props_ac_meter'])
    apply_bevel(r_bin, width=0.02, segments=2)
    vm_col.objects.link(r_bin)
    bpy.context.collection.objects.unlink(r_bin)
    
    for hole_y in [bin_y - 0.16, bin_y + 0.16]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.065, depth=0.03, location=(bin_x, hole_y, bin_z + 0.43))
        hole = bpy.context.active_object
        hole.data.materials.append(mats['interior'])
        vm_col.objects.link(hole)
        bpy.context.collection.objects.unlink(hole)

    return col

# ==============================================================================
# 04. 核心建筑 C 与 3.5m 战术夹墙小巷 (Wall Bounce Alleyway)
# ==============================================================================
def build_house_c_and_alleyway(mats):
    col = bpy.data.collections.new('04_House_C_And_Alleyway')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.25, 5.5
    
    # 1. 基础混凝土基座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.15))
    plinth = bpy.context.active_object
    plinth.name = "HouseC_Plinth"
    plinth.scale = (7.6, 7.6, 0.30)
    bpy.ops.object.transform_apply(scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.03, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 2. 1F 墙体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 1.85))
    wall_1f = bpy.context.active_object
    wall_1f.name = 'HouseC_Wall_1F'
    wall_1f.scale = (7.4, 7.4, 2.8)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_1f, uv_scale=1.0)
    wall_1f.data.materials.append(mats['wall_plaster'])
    
    # 窗洞开切：
    # 东侧推拉窗 (X: -10.55, Y: 4.2, Z: 1.65)
    carve_opening(wall_1f, center_x=-10.55, center_y=4.2, center_z=1.65, width=2.0, height=1.35, depth=0.8)
    # 北侧面向小巷的通风高窗 (X: -14.0, Y: 1.80, Z: 2.2)
    carve_opening(wall_1f, center_x=-14.0, center_y=1.80, center_z=2.2, width=0.8, height=0.6, depth=0.8)
    apply_bevel(wall_1f, width=0.03, segments=2)
    col.objects.link(wall_1f)
    bpy.context.collection.objects.unlink(wall_1f)
    
    # 腰线
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 3.28))
    belt = bpy.context.active_object
    belt.scale = (7.45, 7.45, 0.12)
    bpy.ops.object.transform_apply(scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 3. 2F 墙体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 4.80))
    wall_2f = bpy.context.active_object
    wall_2f.name = 'HouseC_Wall_2F'
    wall_2f.scale = (7.4, 7.4, 2.9)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_2f, uv_scale=1.0)
    wall_2f.data.materials.append(mats['wall_plaster'])
    carve_opening(wall_2f, center_x=-10.55, center_y=4.5, center_z=4.75, width=1.6, height=1.2, depth=0.8)
    apply_bevel(wall_2f, width=0.03, segments=2)
    col.objects.link(wall_2f)
    bpy.context.collection.objects.unlink(wall_2f)
    
    # 4. 屋檐压顶
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 6.35))
    roof = bpy.context.active_object
    roof.scale = (8.2, 8.2, 0.26)
    bpy.ops.object.transform_apply(scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 5. 18cm 物理内嵌铝合金窗
    build_recessed_window("HouseC_Window_1F", center_x=-10.55, center_y=4.2, center_z=1.65, width=1.9, height=1.3, mats=mats, col=col, recess_depth=-0.18)
    build_recessed_window("HouseC_Window_2F", center_x=-10.55, center_y=4.5, center_z=4.75, width=1.5, height=1.15, mats=mats, col=col, recess_depth=-0.18)

    # 6. 屋檐天沟与落水管系统
    build_downspout_system(
        name="HouseC",
        gutter_x=-10.15,
        gutter_y_range=(1.8, 9.2),
        roof_z=6.35,
        downspout_x=-10.35,
        downspout_y=2.0,
        ground_z=0.15,
        mats=mats,
        col=col
    )

    # 7. 3.5m 战术小巷地面与矮墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-14.25, 0.0, 0.05))
    alley_floor = bpy.context.active_object
    alley_floor.name = 'Alley_Pavement_Floor'
    alley_floor.scale = (8.5, 3.5, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(alley_floor, uv_scale=1.0)
    alley_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(alley_floor)
    bpy.context.collection.objects.unlink(alley_floor)

    # 小巷东侧入口矮墙 (1.2m高，绝佳跑酷跳跃点)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.3, 0.0, 0.6))
    fence = bpy.context.active_object
    fence.name = 'Alley_Fence_Low'
    fence.scale = (0.35, 1.8, 1.2)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(fence, uv_scale=1.0)
    fence.data.materials.append(mats['concrete_curb'])
    apply_bevel(fence, width=0.03, segments=2)
    col.objects.link(fence)
    bpy.context.collection.objects.unlink(fence)

    # 8. 小巷内两台对立高精 3D 空调室外机
    build_ac_unit("Alley_HouseA_AC", center_x=-12.5, center_y=-1.45, center_z=0.55, mats=mats, col=col, rot_z=math.radians(90))
    build_ac_unit("Alley_HouseC_AC", center_x=-15.0, center_y=1.45, center_z=0.55, mats=mats, col=col, rot_z=math.radians(-90))

    return col

# ==============================================================================
# 05. 电线杆总成、变压器、绝缘瓷瓶与悬链线下垂电缆生态 (绝区零视觉灵魂)
# ==============================================================================
def build_high_precision_utility_pole(name, pole_x, pole_y, base_z, mats, col):
    """构建工业级圆锥台电杆、登杆脚钉、柱上变压器、双层角钢横担与阶梯绝缘瓷瓶"""
    p_col = bpy.data.collections.new(name)
    col.children.link(p_col)
    
    pole_h = 9.60
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=0.17,
        radius2=0.10,
        depth=pole_h
    )
    bm.to_mesh(mesh)
    bm.free()
    pole_obj = bpy.data.objects.new(name, mesh)
    pole_obj.location = (pole_x, pole_y, base_z + pole_h * 0.5)
    pole_obj.data.materials.append(mats['utility_pole'])
    bpy.ops.object.shade_smooth()
    p_col.objects.link(pole_obj)
    
    rung_z_start = base_z + 2.2
    for r in range(12):
        rz = rung_z_start + r * 0.44
        angle = math.radians(45) if (r % 2 == 0) else math.radians(-45)
        t_h = (rz - base_z) / pole_h
        r_pole = 0.17 - t_h * 0.07
        rc = r_pole + 0.03
        rx = pole_x + rc * math.cos(angle)
        ry = pole_y + rc * math.sin(angle)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.24, location=(rx, ry, rz))
        rung = bpy.context.active_object
        rung.rotation_euler = (0, math.radians(90), angle)
        rung.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        p_col.objects.link(rung)
        bpy.context.collection.objects.unlink(rung)
        
        tip_r = r_pole + 0.145
        tip_x = pole_x + tip_r * math.cos(angle)
        tip_y = pole_y + tip_r * math.sin(angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.038, location=(tip_x, tip_y, rz + 0.015))
        hook = bpy.context.active_object
        hook.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        p_col.objects.link(hook)
        bpy.context.collection.objects.unlink(hook)

    trans_z = base_z + 5.90
    trans_x = pole_x - 0.38
    trans_y = pole_y
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x - 0.18, pole_y, trans_z))
    t_bracket = bpy.context.active_object
    t_bracket.scale = (0.28, 0.42, 0.06)
    bpy.ops.object.transform_apply(scale=True)
    t_bracket.data.materials.append(mats['transformer'])
    p_col.objects.link(t_bracket)
    bpy.context.collection.objects.unlink(t_bracket)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.31, depth=0.88, location=(trans_x, trans_y, trans_z))
    t_body = bpy.context.active_object
    t_body.data.materials.append(mats['transformer'])
    bpy.ops.object.shade_smooth()
    p_col.objects.link(t_body)
    bpy.context.collection.objects.unlink(t_body)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.05, location=(trans_x, trans_y, trans_z + 0.45))
    t_lid = bpy.context.active_object
    t_lid.data.materials.append(mats['transformer'])
    apply_bevel(t_lid, width=0.008, segments=2)
    p_col.objects.link(t_lid)
    bpy.context.collection.objects.unlink(t_lid)
    
    for fin_idx in range(6):
        f_rot = math.radians(135 + fin_idx * 16)
        fx = trans_x + 0.32 * math.cos(f_rot)
        fy = trans_y + 0.32 * math.sin(f_rot)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(fx, fy, trans_z))
        fin = bpy.context.active_object
        fin.scale = (0.012, 0.09, 0.70)
        fin.rotation_euler = (0, 0, f_rot)
        bpy.ops.object.transform_apply(scale=True)
        fin.data.materials.append(mats['transformer'])
        p_col.objects.link(fin)
        bpy.context.collection.objects.unlink(fin)
        
    for b_idx in range(3):
        by = trans_y - 0.18 + b_idx * 0.18
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.16, location=(trans_x, by, trans_z + 0.55))
        bushing = bpy.context.active_object
        bushing.data.materials.append(mats['insulator_porcelain'])
        bpy.ops.object.shade_smooth()
        p_col.objects.link(bushing)
        bpy.context.collection.objects.unlink(bushing)
        
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(trans_x - 0.32, trans_y, trans_z))
    plaque = bpy.context.active_object
    plaque.rotation_euler = (0, math.radians(90), 0)
    plaque.scale = (0.24, 0.16, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    plaque.data.materials.append(mats['tactile_paving'])
    p_col.objects.link(plaque)
    bpy.context.collection.objects.unlink(plaque)

    arm_z1 = base_z + 8.30
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x, pole_y, arm_z1))
    crossarm1 = bpy.context.active_object
    crossarm1.name = f"{name}_Crossarm_Primary"
    crossarm1.scale = (0.12, 2.40, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    crossarm1.data.materials.append(mats['aluminum_silver'])
    apply_bevel(crossarm1, width=0.01, segments=2)
    p_col.objects.link(crossarm1)
    bpy.context.collection.objects.unlink(crossarm1)
    
    for ip_idx, iy_off in enumerate([-0.95, 0.0, 0.95]):
        ix = pole_x
        iy = pole_y + iy_off
        iz = arm_z1 + 0.14
        for s_lvl in [0.0, 0.09]:
            bpy.ops.mesh.primitive_cone_add(radius1=0.085, radius2=0.035, depth=0.08, location=(ix, iy, iz + s_lvl))
            bell = bpy.context.active_object
            bell.data.materials.append(mats['insulator_porcelain'])
            bpy.ops.object.shade_smooth()
            p_col.objects.link(bell)
            bpy.context.collection.objects.unlink(bell)

    arm_curve = bpy.data.curves.new(f'{name}_StreetLampArm', type='CURVE')
    arm_curve.dimensions = '3D'
    arm_curve.fill_mode = 'FULL'
    arm_curve.bevel_depth = 0.028
    a_spline = arm_curve.splines.new('BEZIER')
    a_pts = [
        (pole_x, pole_y, base_z + 7.35),
        (pole_x + 0.60, pole_y + 0.10, base_z + 7.50),
        (pole_x + 1.20, pole_y + 0.15, base_z + 7.20)
    ]
    a_spline.bezier_points.add(len(a_pts) - 1)
    for i, pt in enumerate(a_pts):
        bp = a_spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    a_obj = bpy.data.objects.new(f'{name}_StreetLampArm', arm_curve)
    a_obj.data.materials.append(mats['aluminum_dark'])
    p_col.objects.link(a_obj)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x + 1.20, pole_y + 0.15, base_z + 7.18))
    led_head = bpy.context.active_object
    led_head.scale = (0.42, 0.18, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    led_head.data.materials.append(mats['aluminum_dark'])
    apply_bevel(led_head, width=0.01, segments=2)
    p_col.objects.link(led_head)
    bpy.context.collection.objects.unlink(led_head)

    return p_col

def build_street_props_ecosystem(mats):
    col = bpy.data.collections.new('05_Street_Props_Ecosystem')
    bpy.context.scene.collection.children.link(col)
    
    poles = [
        ("Utility_Pole_South", -4.2, 14.0, 0.15),
        ("Utility_Pole_Mid", -4.2, -4.0, 2.40),
        ("Utility_Pole_North", -4.2, -20.0, 5.15)
    ]
    for p_name, px, py, pz in poles:
        build_high_precision_utility_pole(p_name, px, py, pz, mats, col)
        
    cables_col = bpy.data.collections.new("Catenary_Cables_Network")
    col.children.link(cables_col)
    
    p1_z = 0.15 + 8.52
    p2_z = 2.40 + 8.52
    for c_idx, iy_off in enumerate([-0.95, 0.0, 0.95]):
        c1 = build_catenary_curve(
            f"HV_Cable_Seg1_{c_idx}",
            (-4.2, 14.0 + iy_off, p1_z),
            (-4.2, -4.0 + iy_off, p2_z),
            sag=0.42,
            radius=0.014,
            material=mats['cable_rubber']
        )
        cables_col.objects.link(c1)
        
    p3_z = 5.15 + 8.52
    for c_idx, iy_off in enumerate([-0.95, 0.0, 0.95]):
        c2 = build_catenary_curve(
            f"HV_Cable_Seg2_{c_idx}",
            (-4.2, -4.0 + iy_off, p2_z),
            (-4.2, -20.0 + iy_off, p3_z),
            sag=0.45,
            radius=0.014,
            material=mats['cable_rubber']
        )
        cables_col.objects.link(c2)
        
    s_drop = build_catenary_curve(
        "Service_Drop_HouseA",
        (-4.2, 14.0, 0.15 + 7.20),
        (-10.55, -4.2, 5.10),
        sag=0.55,
        radius=0.011,
        material=mats['cable_rubber']
    )
    cables_col.objects.link(s_drop)

    bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.02, depth=0.72, location=(-3.9, 11.5, 0.44))
    cone = bpy.context.active_object
    cone.data.materials.append(mats['train_yellow'])
    bpy.ops.object.shade_smooth()
    col.objects.link(cone)
    bpy.context.collection.objects.unlink(cone)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.8, 16.5, 0.65))
    pbox = bpy.context.active_object
    pbox.name = "Japanese_Post_Box"
    pbox.scale = (0.45, 0.65, 0.95)
    bpy.ops.object.transform_apply(scale=True)
    pbox.data.materials.append(mats['torii_red'])
    apply_bevel(pbox, width=0.02, segments=2)
    col.objects.link(pbox)
    bpy.context.collection.objects.unlink(pbox)

    return col

# ==============================================================================
# 主执行入口：材质绑定、场景组装与 glb 导出
# ==============================================================================
def main():
    print("==================================================================")
    print("Starting Next-Gen Urban Neighborhood Rebuild (CS2 PBR + ZZZ Details)")
    print("==================================================================")
    clean_scene()
    
    mats = {
        'asphalt_road': create_gltf_pbr_material(
            "M_AsphaltRoad",
            "asphalt_road_albedo.png",
            normal_file="asphalt_road_normal.png",
            roughness_file="asphalt_road_roughness.png",
            ao_file="asphalt_road_ao.png",
            fallback_color=(0.18, 0.18, 0.19, 1.0),
            roughness_val=0.88,
            normal_strength=2.2
        ),
        'concrete_curb': create_gltf_pbr_material(
            "M_ConcreteCurb",
            "concrete_curb_albedo.png",
            normal_file="concrete_curb_normal.png",
            roughness_file="concrete_curb_roughness.png",
            ao_file="concrete_curb_ao.png",
            fallback_color=(0.58, 0.59, 0.60, 1.0),
            roughness_val=0.72,
            normal_strength=1.5
        ),
        'sidewalk_tiles': create_gltf_pbr_material(
            "M_SidewalkTiles",
            "sidewalk_tiles_albedo.png",
            normal_file="sidewalk_tiles_normal.png",
            roughness_file="sidewalk_tiles_roughness.png",
            ao_file="sidewalk_tiles_ao.png",
            fallback_color=(0.65, 0.66, 0.68, 1.0),
            roughness_val=0.68,
            normal_strength=1.6
        ),
        'tactile_paving': create_gltf_pbr_material(
            "M_TactilePaving",
            "tactile_paving_albedo.png",
            normal_file="tactile_paving_normal.png",
            roughness_file="tactile_paving_roughness.png",
            ao_file="tactile_paving_ao.png",
            fallback_color=(0.94, 0.72, 0.05, 1.0),
            roughness_val=0.52,
            normal_strength=2.2
        ),
        'metal_manhole': create_gltf_pbr_material(
            "M_MetalManhole",
            "metal_manhole_albedo.png",
            normal_file="metal_manhole_normal.png",
            roughness_file="metal_manhole_roughness.png",
            ao_file="metal_manhole_ao.png",
            fallback_color=(0.16, 0.17, 0.18, 1.0),
            roughness_val=0.45,
            metallic_val=0.85,
            normal_strength=2.4
        ),
        'wall_plaster': create_gltf_pbr_material(
            "M_WallPlaster",
            "wall_plaster_albedo.png",
            normal_file="wall_plaster_normal.png",
            roughness_file="wall_plaster_roughness.png",
            ao_file="wall_plaster_ao.png",
            fallback_color=(0.82, 0.81, 0.78, 1.0),
            roughness_val=0.82,
            normal_strength=1.8
        ),
        'utility_pole': create_gltf_pbr_material(
            "M_UtilityPole",
            "utility_pole_albedo.png",
            normal_file="utility_pole_normal.png",
            roughness_file="utility_pole_roughness.png",
            ao_file="utility_pole_ao.png",
            fallback_color=(0.61, 0.62, 0.63, 1.0),
            roughness_val=0.78,
            normal_strength=1.4
        ),
        'props_ac_meter': create_gltf_pbr_material(
            "M_PropsACMeter",
            "props_ac_meter_albedo.png",
            normal_file="props_ac_meter_normal.png",
            roughness_file="props_ac_meter_roughness.png",
            ao_file="props_ac_meter_ao.png",
            fallback_color=(0.86, 0.87, 0.88, 1.0),
            roughness_val=0.42,
            normal_strength=1.5
        ),
        'vending_machine': create_gltf_pbr_material(
            "M_VendingMachine",
            "vending_machine_2k_diffuse.png",
            normal_file="vending_machine_2k_normal.png",
            roughness_file="vending_machine_2k_roughness.png",
            emissive_file="vending_machine_2k_emissive.png",
            fallback_color=(0.9, 0.1, 0.1, 1.0),
            roughness_val=0.35,
            metallic_val=0.4,
            normal_strength=1.4,
            emissive_strength=1.2
        ),
        'store_sign': create_gltf_pbr_material(
            "M_StoreSign",
            "convenience_store_sign_2k_albedo.png",
            emissive_file="convenience_store_sign_2k_emissive.png",
            fallback_color=(0.95, 0.95, 0.95, 1.0),
            roughness_val=0.25,
            emissive_strength=1.5
        ),
        'store_shelves': create_gltf_pbr_material(
            "M_StoreShelves",
            "convenience_store_interior_2k.png",
            fallback_color=(0.85, 0.85, 0.85, 1.0),
            roughness_val=0.45
        ),
        'transformer': create_metal_material("M_Transformer", (0.32, 0.34, 0.35, 1.0), roughness=0.65, metallic=0.70),
        'glass': create_glass_material("M_Glass"),
        'aluminum_dark': create_metal_material("M_Aluminum_Dark", (0.12, 0.13, 0.14, 1.0), roughness=0.32, metallic=0.88),
        'aluminum_silver': create_metal_material("M_Aluminum_Silver", (0.75, 0.78, 0.80, 1.0), roughness=0.28, metallic=0.92),
        'insulator_porcelain': create_metal_material("M_InsulatorPorcelain", (0.28, 0.14, 0.08, 1.0), roughness=0.12, metallic=0.10),
        'cable_rubber': create_metal_material("M_CableRubber", (0.08, 0.08, 0.09, 1.0), roughness=0.65, metallic=0.0),
        'interior': create_metal_material("M_InteriorRoom", (0.04, 0.05, 0.06, 1.0), roughness=0.92, metallic=0.0),
        'torii_red': create_metal_material("M_Torii_Red", (0.85, 0.15, 0.08, 1.0), roughness=0.45, metallic=0.05),
        'torii_black': create_metal_material("M_Torii_Black", (0.06, 0.06, 0.07, 1.0), roughness=0.35, metallic=0.10),
        'train_yellow': create_metal_material("M_Train_Yellow", (0.95, 0.65, 0.05, 1.0), roughness=0.35, metallic=0.10)
    }

    print("Building 00: Environment Backdrop & Skyline...")
    build_environment_backdrop(mats)
    
    print("Building 01: Terrain, Roads, Manhole & Sewer Grates...")
    build_terrain_and_roads(mats)
    
    print("Building 02: House A (Recessed Windows, Downspout, AC Unit)...")
    build_house_a(mats)
    
    print("Building 03: Convenience Store, 3D Shelves & Dual Vending Machine...")
    build_house_b_convenience_store(mats)
    
    print("Building 04: House C & 3.5m Tactical Alleyway...")
    build_house_c_and_alleyway(mats)
    
    print("Building 05: High-Precision Utility Poles & Catenary Cables...")
    build_street_props_ecosystem(mats)
    
    blend_path = os.path.abspath(r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\nextgen_pbr\modern_japan_neighborhood.blend")
    ensure_dir(os.path.dirname(blend_path))
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved Blender project to: {blend_path}")
    
    glb_out = os.path.abspath(r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\models\environment\modern_japan_neighborhood.glb")
    ensure_dir(os.path.dirname(glb_out))
    try:
        bpy.ops.export_scene.gltf(filepath=glb_out, export_format='GLB', export_materials='EXPORT', export_cameras=True)
        print(f"Exported GLB asset directly to Godot scene dir: {glb_out}")
    except Exception as e:
        print(f"GLB export note: {e}")

    glb_mirror = os.path.abspath(r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\nextgen_pbr\modern_japan_neighborhood.glb")
    ensure_dir(os.path.dirname(glb_mirror))
    try:
        bpy.ops.export_scene.gltf(filepath=glb_mirror, export_format='GLB', export_materials='EXPORT')
        print(f"Mirrored GLB asset to art repo: {glb_mirror}")
    except Exception as e:
        print(f"GLB mirror note: {e}")

    print("==================================================================")
    print("Next-Gen Neighborhood Generation Completed Successfully!")
    print("==================================================================")

if __name__ == "__main__":
    main()
