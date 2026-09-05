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

# 贴图检索优先级：nextgen_pbr 真实扫描贴图优先
TEXTURE_BASE_DIRS = [
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\nextgen_pbr",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\models\environment\textures",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\golden_slice",
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

def apply_road_uv(obj, road_width=8.0, y_start=12.0, y_length=16.0):
    """为日式道路专门展开 UV：横向 X 映射到 U [0..1]，纵向 Y 对应标线位置（斑马线、减速菱形、停止线）"""
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
            v = (co.y - y_start) / y_length
            uv_layer.data[loop_idx].uv = (u, v)

def apply_tower_facade_uv(obj, width=20.0, height=40.0, floors=12, bays=8):
    """为高层大厦立面展开 UV，确保每层高度约 3.2m 且窗口比例完全对应"""
    bpy.context.view_layer.objects.active = obj
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    if not uv_layer:
        uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        normal = poly.normal
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            co = mesh.vertices[v_idx].co
            if abs(normal.z) > 0.7:
                # 顶部/底部屋顶：使用平铺石材
                u = co.x / 4.0
                v = co.y / 4.0
            elif abs(normal.y) >= abs(normal.x):
                # 南北立面
                u = (co.x / width) * (bays / 12.0)
                v = (co.z / height) * (floors / 16.0)
            else:
                # 东西立面
                u = (co.y / width) * (bays / 12.0)
                v = (co.z / height) * (floors / 16.0)
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
    """生成符合重力悬链线物理特性的三维自然下垂电缆曲线，并转为真实网格确保 glTF 完整导出"""
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
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.collection.objects.unlink(obj)
    if material:
        obj.data.materials.append(material)
    return obj

# ==============================================================================
# 标准 glTF 2.0 / Godot 4 兼容原生 PBR 材质创建器
# ==============================================================================
def create_gltf_pbr_material(name, albedo_file, normal_file=None, roughness_file=None, ao_file=None, emissive_file=None, 
                             fallback_color=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, normal_strength=1.5,
                             emissive_strength=1.0):
    """直接使用标准 Principled BSDF 连接，确保 Blender glTF 导出器 100% 正确嵌入纹理"""
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
    
    # 1. Albedo (直接连接到 Base Color，确保 glTF 2.0 导出器原生识别)
    if albedo_file:
        alb_p = find_tex(albedo_file)
        if alb_p:
            tex_alb = nodes.new('ShaderNodeTexImage')
            tex_alb.image = bpy.data.images.load(alb_p)
            links.new(tex_alb.outputs['Color'], bsdf.inputs['Base Color'])
            
    # 2. Roughness
    if roughness_file:
        rgh_p = find_tex(roughness_file)
        if rgh_p:
            r_node = nodes.new('ShaderNodeTexImage')
            r_node.image = bpy.data.images.load(rgh_p)
            r_node.image.colorspace_settings.name = 'Non-Color'
            links.new(r_node.outputs['Color'], bsdf.inputs['Roughness'])
            
    # 3. Normal Map
    if normal_file:
        nrm_p = find_tex(normal_file)
        if nrm_p:
            n_node = nodes.new('ShaderNodeTexImage')
            n_node.image = bpy.data.images.load(nrm_p)
            n_node.image.colorspace_settings.name = 'Non-Color'
            
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
    """日式双滑轨铝合金推拉窗：
       1. 挤压型材外窗框 (Top, Bot, Left, Right)
       2. 双导轨 (上下双导轨槽)
       3. 内外重叠推拉窗扇框架与双层中空玻璃
       4. 窗台倾斜 3.5 度冲压金属滴水板 (向室外挑出)
       5. 室内深色吸光腔体 (严格收纳在建筑内部深处)
    """
    depth_val = abs(recess_depth)
    inner_x = center_x - depth_val
    frame_thick = 0.05
    
    # 1. 外窗框
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z + height * 0.5 - frame_thick * 0.5))
    f_top = bpy.context.active_object
    f_top.name = f"{name}_Frame_Top"
    f_top.scale = (0.08, width, frame_thick)
    bpy.ops.object.transform_apply(scale=True)
    f_top.data.materials.append(mats['aluminum_dark'])
    apply_bevel(f_top, width=0.005, segments=2)
    col.objects.link(f_top)
    bpy.context.collection.objects.unlink(f_top)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z - height * 0.5 + frame_thick * 0.5))
    f_bot = bpy.context.active_object
    f_bot.name = f"{name}_Frame_Bot"
    f_bot.scale = (0.08, width, frame_thick)
    bpy.ops.object.transform_apply(scale=True)
    f_bot.data.materials.append(mats['aluminum_dark'])
    apply_bevel(f_bot, width=0.005, segments=2)
    col.objects.link(f_bot)
    bpy.context.collection.objects.unlink(f_bot)
    
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

    # 2. 双滑轨轨道
    for tz in [center_z - height * 0.5 + 0.045, center_z + height * 0.5 - 0.045]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, tz))
        track = bpy.context.active_object
        track.scale = (0.05, width - frame_thick * 2.0, 0.012)
        bpy.ops.object.transform_apply(scale=True)
        track.data.materials.append(mats['aluminum_silver'])
        col.objects.link(track)
        bpy.context.collection.objects.unlink(track)

    # 3. 左右重叠推拉窗扇
    half_w = (width - frame_thick * 2.0) * 0.5 + 0.03
    sash_offsets = [
        ("LeftSash", inner_x - 0.018, center_y - (width - frame_thick * 2.0) * 0.25),
        ("RightSash", inner_x + 0.018, center_y + (width - frame_thick * 2.0) * 0.25)
    ]
    sash_inner_h = height - frame_thick * 2.0 - 0.03
    for s_name, sx, sy in sash_offsets:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z + sash_inner_h * 0.5 - 0.02))
        s_top = bpy.context.active_object
        s_top.scale = (0.032, half_w, 0.04)
        bpy.ops.object.transform_apply(scale=True)
        s_top.data.materials.append(mats['aluminum_dark'])
        col.objects.link(s_top)
        bpy.context.collection.objects.unlink(s_top)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z - sash_inner_h * 0.5 + 0.02))
        s_bot = bpy.context.active_object
        s_bot.scale = (0.032, half_w, 0.04)
        bpy.ops.object.transform_apply(scale=True)
        s_bot.data.materials.append(mats['aluminum_dark'])
        col.objects.link(s_bot)
        bpy.context.collection.objects.unlink(s_bot)
        
        for st_sign, st_sub in [(-1, "L"), (1, "R")]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy + st_sign * (half_w * 0.5 - 0.02), center_z))
            s_stile = bpy.context.active_object
            s_stile.scale = (0.032, 0.04, sash_inner_h)
            bpy.ops.object.transform_apply(scale=True)
            s_stile.data.materials.append(mats['aluminum_dark'])
            col.objects.link(s_stile)
            bpy.context.collection.objects.unlink(s_stile)
            
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, center_z))
        glass = bpy.context.active_object
        glass.scale = (0.012, half_w - 0.07, sash_inner_h - 0.07)
        bpy.ops.object.transform_apply(scale=True)
        glass.data.materials.append(mats['glass'])
        col.objects.link(glass)
        bpy.context.collection.objects.unlink(glass)

    # 4. 金属滴水板
    sill_x = center_x - (depth_val * 0.5) + 0.04
    sill_w = width + 0.12
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sill_x, center_y, center_z - height * 0.5 - 0.015))
    sill = bpy.context.active_object
    sill.name = f"{name}_Metal_Sill_Drip"
    sill.scale = (depth_val + 0.08, sill_w, 0.025)
    bpy.ops.object.transform_apply(scale=True)
    sill.rotation_euler = (0.0, math.radians(-3.5), 0.0)
    sill.data.materials.append(mats['aluminum_dark'])
    apply_bevel(sill, width=0.005, segments=2)
    col.objects.link(sill)
    bpy.context.collection.objects.unlink(sill)

    # 5. 室内深色吸光腔体
    cavity_x = inner_x - 0.22
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cavity_x, center_y, center_z))
    room = bpy.context.active_object
    room.name = f"{name}_RoomCavity"
    room.scale = (0.35, width - 0.08, height - 0.08)
    bpy.ops.object.transform_apply(scale=True)
    room.data.materials.append(mats['interior'])
    col.objects.link(room)
    bpy.context.collection.objects.unlink(room)

# ==============================================================================
# 屋檐排水天沟与落水管系统
# ==============================================================================
def build_downspout_system(name, gutter_x, gutter_y_range, roof_z, downspout_x, downspout_y, ground_z, mats, col):
    gy_start, gy_end = gutter_y_range
    gy_len = abs(gy_end - gy_start)
    gy_center = (gy_start + gy_end) * 0.5
    
    # 1. 排水天沟
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gutter_x, gy_center, roof_z - 0.05))
    gutter = bpy.context.active_object
    gutter.name = f"{name}_Eaves_Gutter"
    gutter.scale = (0.12, gy_len + 0.15, 0.10)
    bpy.ops.object.transform_apply(scale=True)
    gutter.data.materials.append(mats['aluminum_dark'])
    apply_bevel(gutter, width=0.012, segments=2)
    col.objects.link(gutter)
    bpy.context.collection.objects.unlink(gutter)
    
    # 2. 雨水集水斗
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(downspout_x - 0.05, downspout_y, roof_z - 0.12))
    funnel = bpy.context.active_object
    funnel.name = f"{name}_Downspout_Collector_Funnel"
    funnel.scale = (0.18, 0.22, 0.24)
    bpy.ops.object.transform_apply(scale=True)
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
    
    # 4. 金属固定抱箍
    strap_z = ground_z + 0.8
    while strap_z < roof_z - 0.4:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(downspout_x - 0.04, downspout_y, strap_z))
        strap = bpy.context.active_object
        strap.scale = (0.12, 0.11, 0.035)
        bpy.ops.object.transform_apply(scale=True)
        strap.data.materials.append(mats['aluminum_silver'])
        apply_bevel(strap, width=0.005, segments=2)
        col.objects.link(strap)
        bpy.context.collection.objects.unlink(strap)
        strap_z += 1.6
        
    # 5. 地表排水弯头
    bpy.ops.mesh.primitive_cylinder_add(radius=0.042, depth=0.22, location=(downspout_x + 0.05, downspout_y, ground_z + 0.12))
    elbow = bpy.context.active_object
    elbow.name = f"{name}_Discharge_Elbow"
    elbow.rotation_euler = (0.0, math.radians(40), 0.0)
    elbow.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(elbow)
    bpy.context.collection.objects.unlink(elbow)

# ==============================================================================
# 高精 3D 空调室外机总成
# ==============================================================================
def build_ac_unit(name, center_x, center_y, center_z, mats, col, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y, center_z))
    ac_body = bpy.context.active_object
    ac_body.name = f"{name}_Chassis"
    ac_body.scale = (0.34, 0.82, 0.58)
    bpy.ops.object.transform_apply(scale=True)
    ac_body.rotation_euler = (0.0, 0.0, rot_z)
    ac_body.data.materials.append(mats['concrete_wall'])
    apply_bevel(ac_body, width=0.015, segments=2)
    col.objects.link(ac_body)
    bpy.context.collection.objects.unlink(ac_body)

    for side_y in [-0.32, 0.32]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y + side_y, center_z - 0.31))
        foot = bpy.context.active_object
        foot.scale = (0.36, 0.10, 0.05)
        bpy.ops.object.transform_apply(scale=True)
        foot.data.materials.append(mats['cable_rubber'])
        col.objects.link(foot)
        bpy.context.collection.objects.unlink(foot)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.06, location=(center_x + 0.16, center_y - 0.10, center_z))
    shroud = bpy.context.active_object
    shroud.rotation_euler = (0.0, math.radians(90), 0.0)
    shroud.data.materials.append(mats['aluminum_dark'])
    col.objects.link(shroud)
    bpy.context.collection.objects.unlink(shroud)

    for ang in [0, 120, 240]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x + 0.16, center_y - 0.10, center_z))
        blade = bpy.context.active_object
        blade.scale = (0.012, 0.18, 0.045)
        bpy.ops.object.transform_apply(scale=True)
        blade.rotation_euler = (math.radians(ang), math.radians(90), math.radians(22))
        blade.data.materials.append(mats['aluminum_dark'])
        col.objects.link(blade)
        bpy.context.collection.objects.unlink(blade)

# ==============================================================================
# 次世代现代化高层写字楼/公寓大厦（彻底消灭纯色方块）
# ==============================================================================
def build_articulated_skyscraper(name, cx, cy, width_x, length_y, height_z, mats, col, has_billboard=True, billboard_text="HOSHINO HEAVY IND"):
    """构建具备商业裙楼 + 16层幕墙主塔楼 + 屋顶冷水塔/水箱/霓虹招牌的三段式高精度都市摩天楼"""
    # 1. 裙楼 (Podium，0 ~ 6.5m)：下层商业街铺面与石材立面
    podium_h = 6.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, podium_h * 0.5))
    podium = bpy.context.active_object
    podium.name = f"{name}_Commercial_Podium"
    podium.scale = (width_x + 1.2, length_y + 1.2, podium_h)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(podium, uv_scale=0.8) # 商业面砖
    podium.data.materials.append(mats['brick_commercial'])
    apply_bevel(podium, width=0.04, segments=2)
    col.objects.link(podium)
    bpy.context.collection.objects.unlink(podium)
    
    # 裙楼顶部装饰压顶横梁
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, podium_h + 0.15))
    cornice = bpy.context.active_object
    cornice.scale = (width_x + 1.6, length_y + 1.6, 0.30)
    bpy.ops.object.transform_apply(scale=True)
    cornice.data.materials.append(mats['aluminum_dark'])
    apply_bevel(cornice, width=0.03, segments=2)
    col.objects.link(cornice)
    bpy.context.collection.objects.unlink(cornice)
    
    # 2. 塔楼主楼 (Tower Body)：16层规整玻璃幕墙与铝合金立柱
    tower_h = height_z - podium_h - 3.5
    tower_cz = podium_h + tower_h * 0.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, tower_cz))
    tower = bpy.context.active_object
    tower.name = f"{name}_Tower_Body"
    tower.scale = (width_x, length_y, tower_h)
    bpy.ops.object.transform_apply(scale=True)
    # 按建筑真实层高映射窗户贴图
    apply_tower_facade_uv(tower, width=max(width_x, length_y), height=tower_h, floors=int(tower_h / 3.0), bays=int(max(width_x, length_y) / 2.5))
    tower.data.materials.append(mats['skyline_facade'])
    col.objects.link(tower)
    bpy.context.collection.objects.unlink(tower)
    
    # 水平腰线层板 (每隔 6.4m 一道突出挑檐，打破平面感)
    hz = podium_h + 6.4
    while hz < height_z - 5.0:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, hz))
        spandrel = bpy.context.active_object
        spandrel.scale = (width_x + 0.35, length_y + 0.35, 0.18)
        bpy.ops.object.transform_apply(scale=True)
        spandrel.data.materials.append(mats['aluminum_silver'])
        col.objects.link(spandrel)
        bpy.context.collection.objects.unlink(spandrel)
        hz += 6.4

    # 3. 屋顶女儿墙与机械设备 (Rooftop Penthouse, Water Tank & Chiller)
    roof_z = podium_h + tower_h
    # 女儿墙 (Parapet)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, roof_z + 0.6))
    parapet = bpy.context.active_object
    parapet.scale = (width_x + 0.2, length_y + 0.2, 1.2)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(parapet, uv_scale=1.0)
    parapet.data.materials.append(mats['concrete_wall'])
    col.objects.link(parapet)
    bpy.context.collection.objects.unlink(parapet)
    
    # 电梯机房 (Penthouse)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx - width_x * 0.15, cy, roof_z + 1.8))
    penthouse = bpy.context.active_object
    penthouse.scale = (width_x * 0.45, length_y * 0.45, 2.8)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(penthouse, uv_scale=1.0)
    penthouse.data.materials.append(mats['concrete_wall'])
    apply_bevel(penthouse, width=0.03, segments=2)
    col.objects.link(penthouse)
    bpy.context.collection.objects.unlink(penthouse)

    # 冷却塔 (Cooling Tower)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx + width_x * 0.22, cy - length_y * 0.2, roof_z + 1.3))
    chiller = bpy.context.active_object
    chiller.scale = (3.2, 2.8, 2.0)
    bpy.ops.object.transform_apply(scale=True)
    chiller.data.materials.append(mats['aluminum_dark'])
    apply_bevel(chiller, width=0.02, segments=2)
    col.objects.link(chiller)
    bpy.context.collection.objects.unlink(chiller)

    # 不锈钢蓄水罐 (Water Tank)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=2.4, location=(cx + width_x * 0.22, cy + length_y * 0.2, roof_z + 1.6))
    wtank = bpy.context.active_object
    wtank.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(wtank)
    bpy.context.collection.objects.unlink(wtank)

    # 4. 大型都市工业广告牌 (Rooftop Billboard)
    if has_billboard:
        bb_x = cx
        bb_y = cy - length_y * 0.42
        bb_z = roof_z + 2.8
        # 支撑桁架
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bb_x, bb_y, bb_z))
        b_frame = bpy.context.active_object
        b_frame.scale = (width_x * 0.75, 0.4, 3.2)
        bpy.ops.object.transform_apply(scale=True)
        b_frame.data.materials.append(mats['aluminum_dark'])
        col.objects.link(b_frame)
        bpy.context.collection.objects.unlink(b_frame)
        
        # 发光广告板
        b_face = create_vertical_display_plane(f"{name}_Billboard_Face", (bb_x - 0.25, bb_y, bb_z), width_x * 0.72, 3.0, mats['store_sign'])
        col.objects.link(b_face)

# ==============================================================================
# 00. 天际线封闭与高层大厦群（消除所有纯色方块）
# ==============================================================================
def build_environment_skyline(mats):
    col = bpy.data.collections.new('00_Environment_Skyline')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 北侧山顶神社高台与朱红大鸟居 (山顶门楣，标高 Z: 7.0m, Y: -25.0 ~ -45.0m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -35.0, 6.9))
    ground = bpy.context.active_object
    ground.name = 'North_Shrine_Plateau'
    ground.scale = (50.0, 20.0, 0.40)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(ground, uv_scale=0.833)
    ground.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ground)
    bpy.context.collection.objects.unlink(ground)
    
    # 北侧挡土石墙 (Retaining Wall, 标高 0 ~ 7m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -25.0, 3.5))
    wall = bpy.context.active_object
    wall.name = 'North_Retaining_Wall'
    wall.scale = (36.0, 1.2, 7.0)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall, uv_scale=1.0)
    wall.data.materials.append(mats['concrete_wall'])
    apply_bevel(wall, width=0.06, segments=2)
    col.objects.link(wall)
    bpy.context.collection.objects.unlink(wall)

    # 山顶神社朱红大鸟居 (Torii Gate)
    for side_x in [-4.5, 4.5]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=8.5, location=(side_x, -28.0, 11.25))
        t_col = bpy.context.active_object
        t_col.data.materials.append(mats['torii_red'])
        bpy.ops.object.shade_smooth()
        col.objects.link(t_col)
        bpy.context.collection.objects.unlink(t_col)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -28.0, 15.6))
    t_beam1 = bpy.context.active_object
    t_beam1.scale = (12.8, 0.75, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    t_beam1.data.materials.append(mats['torii_black'])
    apply_bevel(t_beam1, width=0.04, segments=2)
    col.objects.link(t_beam1)
    bpy.context.collection.objects.unlink(t_beam1)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -28.0, 14.2))
    t_beam2 = bpy.context.active_object
    t_beam2.scale = (11.2, 0.6, 0.6)
    bpy.ops.object.transform_apply(scale=True)
    t_beam2.data.materials.append(mats['torii_red'])
    col.objects.link(t_beam2)
    bpy.context.collection.objects.unlink(t_beam2)

    # 2. 南侧轻轨高架桥与黄色列车 (跨越 Y: 34.0, 标高 Z: 8.2m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 34.0, 8.2))
    rail_deck = bpy.context.active_object
    rail_deck.name = 'Monorail_Deck'
    rail_deck.scale = (85.0, 6.0, 1.2)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(rail_deck, uv_scale=1.0)
    rail_deck.data.materials.append(mats['concrete_wall'])
    apply_bevel(rail_deck, width=0.08, segments=2)
    col.objects.link(rail_deck)
    bpy.context.collection.objects.unlink(rail_deck)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, 34.0, 10.2))
    train = bpy.context.active_object
    train.name = 'Monorail_Train'
    train.scale = (24.0, 3.2, 3.4)
    bpy.ops.object.transform_apply(scale=True)
    train.data.materials.append(mats['train_yellow'])
    apply_bevel(train, width=0.1, segments=2)
    col.objects.link(train)
    bpy.context.collection.objects.unlink(train)
    
    for px in [-24.0, 0.0, 24.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, 34.0, 3.8))
        pillar = bpy.context.active_object
        pillar.scale = (3.2, 3.6, 7.6)
        bpy.ops.object.transform_apply(scale=True)
        apply_box_uv(pillar, uv_scale=1.0)
        pillar.data.materials.append(mats['concrete_wall'])
        apply_bevel(pillar, width=0.06, segments=2)
        col.objects.link(pillar)
        bpy.context.collection.objects.unlink(pillar)

    # 3. 现代化高层摩天楼群（彻底消灭纯色方块，360° 封闭天际线）
    # 北侧山顶背景摩天楼（衬托鸟居，封死北向视线）
    build_articulated_skyscraper("North_Tower_West", -24.0, -52.0, 18.0, 16.0, 36.0, mats, col, has_billboard=True, billboard_text="NEPS POLICE")
    build_articulated_skyscraper("North_Tower_Center", 0.0, -56.0, 24.0, 18.0, 42.0, mats, col, has_billboard=True, billboard_text="HOSHINO HEAVY IND")
    build_articulated_skyscraper("North_Tower_East", 24.0, -52.0, 18.0, 16.0, 34.0, mats, col, has_billboard=False)

    # 南侧远景大厦群 (封死南向视线)
    build_articulated_skyscraper("South_Tower_West", -26.0, 48.0, 18.0, 14.0, 32.0, mats, col, has_billboard=True, billboard_text="DAILY MART 24H")
    build_articulated_skyscraper("South_Tower_Center", 0.0, 52.0, 22.0, 15.0, 38.0, mats, col, has_billboard=False)
    build_articulated_skyscraper("South_Tower_East", 26.0, 48.0, 18.0, 14.0, 28.0, mats, col, has_billboard=False)

    # 西侧都市公寓天际线 (X = -28.0)
    build_articulated_skyscraper("West_Mansion_South", -28.0, -20.0, 14.0, 16.0, 28.0, mats, col, has_billboard=False)
    build_articulated_skyscraper("West_Mansion_Center", -28.0, 0.0, 15.0, 18.0, 32.0, mats, col, has_billboard=True, billboard_text="DAILY MART 24H")
    build_articulated_skyscraper("West_Mansion_North", -28.0, 20.0, 14.0, 15.0, 28.0, mats, col, has_billboard=False)

    # 东侧高层住宅群 (X = 22.0)
    build_articulated_skyscraper("East_Skyline_South", 22.0, -20.0, 14.0, 15.0, 26.0, mats, col, has_billboard=False)
    build_articulated_skyscraper("East_Skyline_Center", 22.0, 0.0, 15.0, 18.0, 30.0, mats, col, has_billboard=True, billboard_text="LUMINA METRO")
    build_articulated_skyscraper("East_Skyline_North", 22.0, 20.0, 14.0, 15.0, 28.0, mats, col, has_billboard=False)

    return col

# ==============================================================================
# 01. 道路系统、40m 跑酷长坡与微表面市政设施 (斑马线、排水平石、导盲石砖)
# ==============================================================================
def build_terrain_and_roads(mats):
    col = bpy.data.collections.new('01_Roads_And_Terrain')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 南端生活广场主路 (Y: 15.0 ~ 30.0, 宽 8.0m, X: -4.0 ~ 4.0)
    # 采用带有真实斑马线、菱形减速标线与停止线的日式 2K 沥青贴图
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 22.5, -0.05))
    plz_road = bpy.context.active_object
    plz_road.name = 'Plaza_Asphalt_Road'
    plz_road.scale = (8.0, 15.0, 0.10)
    bpy.ops.object.transform_apply(scale=True)
    apply_road_uv(plz_road, road_width=8.0, y_start=15.0, y_length=15.0)
    plz_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(plz_road)
    bpy.context.collection.objects.unlink(plz_road)
    
    # 道路排水平石 (L型混凝土排水侧沟，宽 0.35m，深 0.04m)
    for gutter_side, gx in [(-1, -4.18), (1, 4.18)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, 22.5, -0.04))
        gutter = bpy.context.active_object
        gutter.name = f'Road_Gutter_{gutter_side}'
        gutter.scale = (0.36, 15.0, 0.08)
        bpy.ops.object.transform_apply(scale=True)
        apply_box_uv(gutter, uv_scale=1.0)
        gutter.data.materials.append(mats['concrete_wall'])
        col.objects.link(gutter)
        bpy.context.collection.objects.unlink(gutter)
        
        # 每隔 4m 放置一个铸铁透空格栅雨水箅子
        for gy in [16.0, 20.0, 24.0, 28.0]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(gx, gy, 0.005))
            grate = bpy.context.active_object
            grate.scale = (0.32, 0.65, 0.02)
            bpy.ops.object.transform_apply(scale=True)
            grate.data.materials.append(mats['metal_manhole'])
            col.objects.link(grate)
            bpy.context.collection.objects.unlink(grate)

    # 2. 西侧人行道 (X: -4.36 ~ -10.0, Y: 15.0 ~ 30.0) - 真实板岩石材铺装！彻底终结黑线网格
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.18, 22.5, 0.10))
    plz_sw_w = bpy.context.active_object
    plz_sw_w.name = 'Plaza_Sidewalk_West'
    plz_sw_w.scale = (5.64, 15.0, 0.20)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(plz_sw_w, uv_scale=0.833) # 真实 60cm 预制石材板岩
    plz_sw_w.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_w)
    bpy.context.collection.objects.unlink(plz_sw_w)
    
    # 倒角路缘石 (Curb Stone, 宽 0.20m, 高出路面 0.20m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.46, 22.5, 0.10))
    curb_w = bpy.context.active_object
    curb_w.name = 'Plaza_Curb_West'
    curb_w.scale = (0.20, 15.0, 0.20)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(curb_w, uv_scale=1.0)
    curb_w.data.materials.append(mats['concrete_wall'])
    apply_bevel(curb_w, width=0.03, segments=2)
    col.objects.link(curb_w)
    bpy.context.collection.objects.unlink(curb_w)

    # 斑马线入口处的无障碍降坡切口 (Curb Cut)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.46, 20.0, 0.04))
    curb_cut = bpy.context.active_object
    curb_cut.name = 'Pedestrian_Curb_Cut'
    curb_cut.scale = (0.24, 2.4, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    curb_cut.data.materials.append(mats['concrete_wall'])
    col.objects.link(curb_cut)
    bpy.context.collection.objects.unlink(curb_cut)

    # 黄色导盲道 (Tactile Paving)：沿着人行道笔直延伸，并在斑马线前转折对准人行横道
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.2, 22.5, 0.205))
    plz_tac = bpy.context.active_object
    plz_tac.name = 'Plaza_Tactile_Line'
    plz_tac.scale = (0.6, 15.0, 0.015)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(plz_tac, uv_scale=1.66)
    plz_tac.data.materials.append(mats['tactile_paving'])
    col.objects.link(plz_tac)
    bpy.context.collection.objects.unlink(plz_tac)

    # 斑马线入口转折导盲道 (连接至降坡处)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.8, 20.0, 0.205))
    tac_branch = bpy.context.active_object
    tac_branch.scale = (0.8, 0.6, 0.015)
    bpy.ops.object.transform_apply(scale=True)
    tac_branch.data.materials.append(mats['tactile_paving'])
    col.objects.link(tac_branch)
    bpy.context.collection.objects.unlink(tac_branch)

    # 近景 3D 实心圆点凸珠 (BlisterDots)
    for bx_idx in range(6):
        dot_x = -5.45 + bx_idx * 0.10
        for by_idx in range(12):
            dot_y = 19.45 + by_idx * 0.10
            bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.012, location=(dot_x, dot_y, 0.215))
            dome = bpy.context.active_object
            dome.data.materials.append(mats['tactile_paving'])
            col.objects.link(dome)
            bpy.context.collection.objects.unlink(dome)

    # 3. 下沉式铸铁井盖
    bpy.ops.mesh.primitive_cylinder_add(radius=0.48, depth=0.04, location=(-2.2, 18.0, 0.02))
    mh_collar = bpy.context.active_object
    mh_collar.data.materials.append(mats['concrete_wall'])
    col.objects.link(mh_collar)
    bpy.context.collection.objects.unlink(mh_collar)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.025, location=(-2.2, 18.0, 0.035))
    mh_lid = bpy.context.active_object
    mh_lid.data.materials.append(mats['metal_manhole'])
    apply_bevel(mh_lid, width=0.015, segments=2)
    col.objects.link(mh_lid)
    bpy.context.collection.objects.unlink(mh_lid)

    # 4. 40m 跑酷长坡道 (顺接南端生活广场 Y: 15.0 至北侧神社台地 Y: -25.0，标高顺接 Z: 0.0 ~ 7.0)
    ramp_len = 40.0
    ramp_cy = -5.0
    ramp_cz = 3.5
    ramp_pitch = math.atan2(7.0, 40.0)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, ramp_cy, ramp_cz))
    ramp_road = bpy.context.active_object
    ramp_road.name = 'Ramp_Asphalt_Road'
    ramp_road.scale = (8.0, ramp_len, 0.20)
    ramp_road.rotation_euler = (-ramp_pitch, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ramp_road, uv_scale=0.5)
    ramp_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(ramp_road)
    bpy.context.collection.objects.unlink(ramp_road)

    # 坡道西侧人行步道
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.5, ramp_cy, ramp_cz + 0.15))
    ramp_sw = bpy.context.active_object
    ramp_sw.name = 'Ramp_Sidewalk_West'
    ramp_sw.scale = (3.0, ramp_len, 0.20)
    ramp_sw.rotation_euler = (-ramp_pitch, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ramp_sw, uv_scale=0.833)
    ramp_sw.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ramp_sw)
    bpy.context.collection.objects.unlink(ramp_sw)

    # 坡道防护栏杆 (Guardrail)
    for ry_idx in range(9):
        ry = 15.0 - ry_idx * 5.0
        rz = (15.0 - ry) * (7.0 / 40.0)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=1.0, location=(-4.1, ry, rz + 0.5))
        post = bpy.context.active_object
        post.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        col.objects.link(post)
        bpy.context.collection.objects.unlink(post)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.1, ramp_cy, ramp_cz + 0.95))
    rail_h = bpy.context.active_object
    rail_h.scale = (0.05, ramp_len, 0.06)
    rail_h.rotation_euler = (-ramp_pitch, 0.0, 0.0)
    bpy.ops.object.transform_apply(scale=True)
    rail_h.data.materials.append(mats['aluminum_silver'])
    col.objects.link(rail_h)
    bpy.context.collection.objects.unlink(rail_h)

    # 现浇混凝土挡墙 (东侧与西侧完整封边，杜绝断崖)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.6, ramp_cy, ramp_cz * 0.5))
    ramp_retaining = bpy.context.active_object
    ramp_retaining.name = 'Ramp_East_Retaining_Wall'
    ramp_retaining.scale = (1.2, ramp_len, 7.5)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(ramp_retaining, uv_scale=1.0)
    ramp_retaining.data.materials.append(mats['concrete_wall'])
    apply_bevel(ramp_retaining, width=0.05, segments=2)
    col.objects.link(ramp_retaining)
    bpy.context.collection.objects.unlink(ramp_retaining)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.1, ramp_cy, ramp_cz * 0.5))
    ramp_w_retaining = bpy.context.active_object
    ramp_w_retaining.name = 'Ramp_West_Retaining_Wall'
    ramp_w_retaining.scale = (0.6, ramp_len, 7.5)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(ramp_w_retaining, uv_scale=1.0)
    ramp_w_retaining.data.materials.append(mats['concrete_wall'])
    apply_bevel(ramp_w_retaining, width=0.05, segments=2)
    col.objects.link(ramp_w_retaining)
    bpy.context.collection.objects.unlink(ramp_w_retaining)

    # 5. 西侧民宅与战术小巷地表铺装（彻底杜绝虚空底色与灰地）
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-15.5, 0.0, -0.05))
    res_ground = bpy.context.active_object
    res_ground.name = 'Residential_Stone_Paving_Ground'
    res_ground.scale = (17.0, 32.0, 0.20)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(res_ground, uv_scale=0.833)
    res_ground.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(res_ground)
    bpy.context.collection.objects.unlink(res_ground)

    return col

# ==============================================================================
# 02. 独栋日式民宅 A（二丁挂立面瓷砖、和瓦挑檐、18cm 内嵌铝合金推拉窗）
# ==============================================================================
def build_house_a(mats):
    col = bpy.data.collections.new('02_House_A_NextGen')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.2, -5.5
    
    # 1. 清水混凝土防潮地梁基座 (Plinth)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.22))
    plinth = bpy.context.active_object
    plinth.name = 'HouseA_Base_Plinth'
    plinth.scale = (7.6, 7.6, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(plinth, uv_scale=1.0)
    plinth.data.materials.append(mats['concrete_wall'])
    apply_bevel(plinth, width=0.02, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)

    # 2. 1F 主体墙体：铺设经典日式二丁挂窄条立面瓷砖！
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 1.85))
    wall_1f = bpy.context.active_object
    wall_1f.name = 'HouseA_Wall_1F'
    wall_1f.scale = (7.2, 7.2, 2.8)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_1f, uv_scale=1.33) # 真实日式二丁挂尺寸
    wall_1f.data.materials.append(mats['wall_facade_tiles'])
    
    # 物理开洞
    carve_opening(wall_1f, center_x=-10.55, center_y=-4.2, center_z=1.65, width=2.1, height=1.35, depth=0.8)
    carve_opening(wall_1f, center_x=-10.55, center_y=-7.5, center_z=1.25, width=1.1, height=2.15, depth=0.8)
    apply_bevel(wall_1f, width=0.03, segments=2)
    col.objects.link(wall_1f)
    bpy.context.collection.objects.unlink(wall_1f)
    
    # 楼层间铝合金水平腰线板
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 3.28))
    belt = bpy.context.active_object
    belt.name = 'HouseA_Mid_Belt'
    belt.scale = (7.45, 7.45, 0.12)
    bpy.ops.object.transform_apply(scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    apply_bevel(belt, width=0.015, segments=2)
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 3. 2F 主墙体：日式质感涂料
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.2, by, 4.80))
    wall_2f = bpy.context.active_object
    wall_2f.name = 'HouseA_Wall_2F'
    wall_2f.scale = (7.0, 7.4, 2.9)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_2f, uv_scale=1.0)
    wall_2f.data.materials.append(mats['wall_plaster'])
    
    carve_opening(wall_2f, center_x=-10.75, center_y=-4.2, center_z=4.75, width=1.8, height=1.3, depth=0.8)
    carve_opening(wall_2f, center_x=-10.75, center_y=-7.5, center_z=4.75, width=1.3, height=1.1, depth=0.8)
    apply_bevel(wall_2f, width=0.03, segments=2)
    col.objects.link(wall_2f)
    bpy.context.collection.objects.unlink(wall_2f)
    
    # 4. 日式和瓦挑檐坡屋顶 (真实灰瓦排布)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 6.45))
    roof = bpy.context.active_object
    roof.name = 'HouseA_Kawara_Roof'
    roof.scale = (8.4, 8.4, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(roof, uv_scale=1.66)
    roof.data.materials.append(mats['roof_kawara'])
    apply_bevel(roof, width=0.04, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 5. 18cm 物理内嵌铝合金推拉窗组件
    build_recessed_window("HouseA_Window_1F", center_x=-10.55, center_y=-4.2, center_z=1.65, width=2.1, height=1.35, mats=mats, col=col, recess_depth=-0.18)
    build_recessed_window("HouseA_Window_2F_1", center_x=-10.75, center_y=-4.2, center_z=4.75, width=1.75, height=1.25, mats=mats, col=col, recess_depth=-0.18)
    build_recessed_window("HouseA_Window_2F_2", center_x=-10.75, center_y=-7.5, center_z=4.75, width=1.25, height=1.05, mats=mats, col=col, recess_depth=-0.18)

    # 6. 入户木质玄关门与悬挑玻璃雨棚
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.70, -7.5, 1.25))
    door = bpy.context.active_object
    door.name = 'HouseA_Entrance_Door'
    door.scale = (0.06, 1.10, 2.15)
    bpy.ops.object.transform_apply(scale=True)
    door.data.materials.append(mats['aluminum_dark'])
    apply_bevel(door, width=0.01, segments=2)
    col.objects.link(door)
    bpy.context.collection.objects.unlink(door)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.75, location=(-10.65, -7.1, 1.10))
    handle = bpy.context.active_object
    handle.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(handle)
    bpy.context.collection.objects.unlink(handle)
    
    # 悬挑雨棚
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.05, -7.5, 2.45))
    canopy = bpy.context.active_object
    canopy.name = 'HouseA_Entrance_Canopy'
    canopy.scale = (1.25, 1.6, 0.04)
    bpy.ops.object.transform_apply(scale=True)
    canopy.data.materials.append(mats['aluminum_dark'])
    apply_bevel(canopy, width=0.008, segments=2)
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    # 7. 屋檐排水天沟与落水管系统
    build_downspout_system(
        name="HouseA",
        gutter_x=-10.15,
        gutter_y_range=(-9.2, -1.8),
        roof_z=6.45,
        downspout_x=-10.18,
        downspout_y=-9.05,
        ground_z=0.22,
        mats=mats,
        col=col
    )
    
    # 8. 2F 悬挑观景阳台 (带金属百叶护栏)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.15, -4.2, 3.25))
    balc = bpy.context.active_object
    balc.name = 'HouseA_2F_Balcony_Floor'
    balc.scale = (1.2, 2.4, 0.15)
    bpy.ops.object.transform_apply(scale=True)
    balc.data.materials.append(mats['concrete_wall'])
    apply_bevel(balc, width=0.015, segments=2)
    col.objects.link(balc)
    bpy.context.collection.objects.unlink(balc)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.55, -4.2, 3.80))
    b_rail = bpy.context.active_object
    b_rail.scale = (0.04, 2.4, 0.95)
    bpy.ops.object.transform_apply(scale=True)
    b_rail.data.materials.append(mats['aluminum_dark'])
    col.objects.link(b_rail)
    bpy.context.collection.objects.unlink(b_rail)

    return col

# ==============================================================================
# 03. 24H 生活广场便利店（Daily Mart）与自动贩卖机
# ==============================================================================
def build_convenience_store(mats):
    col = bpy.data.collections.new('03_Convenience_Store')
    bpy.context.scene.collection.children.link(col)
    
    # 便利店主体建筑 (Y: 15.0 ~ 25.0, X: -10.0 ~ -17.0, Z: 0.0 ~ 4.2)
    # 1. 商业裙楼基座与立面
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.5, 20.0, 0.15))
    store_plinth = bpy.context.active_object
    store_plinth.scale = (7.4, 10.4, 0.30)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(store_plinth, uv_scale=1.0)
    store_plinth.data.materials.append(mats['brick_commercial'])
    col.objects.link(store_plinth)
    bpy.context.collection.objects.unlink(store_plinth)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.5, 20.0, 3.8))
    store_upper = bpy.context.active_object
    store_upper.name = 'Store_Upper_Fascia'
    store_upper.scale = (7.0, 10.0, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    store_upper.data.materials.append(mats['aluminum_dark'])
    apply_bevel(store_upper, width=0.03, segments=2)
    col.objects.link(store_upper)
    bpy.context.collection.objects.unlink(store_upper)
    
    # 后墙与侧墙 (铺设面砖)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-17.0, 20.0, 1.8))
    store_back = bpy.context.active_object
    store_back.scale = (0.5, 10.0, 3.2)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(store_back, uv_scale=1.0)
    store_back.data.materials.append(mats['brick_commercial'])
    col.objects.link(store_back)
    bpy.context.collection.objects.unlink(store_back)
    
    for sy in [15.0, 25.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.5, sy, 1.8))
        swall = bpy.context.active_object
        swall.scale = (7.0, 0.5, 3.2)
        bpy.ops.object.transform_apply(scale=True)
        apply_box_uv(swall, uv_scale=1.0)
        swall.data.materials.append(mats['brick_commercial'])
        col.objects.link(swall)
        bpy.context.collection.objects.unlink(swall)

    # 室内高反光防滑地砖
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.5, 20.0, 0.16))
    store_floor = bpy.context.active_object
    store_floor.scale = (6.8, 9.6, 0.02)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(store_floor, uv_scale=1.5)
    store_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(store_floor)
    bpy.context.collection.objects.unlink(store_floor)

    # 2. 经典三色便利店门头灯箱
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.85, 20.0, 3.4))
    sign_frame = bpy.context.active_object
    sign_frame.name = 'ConvenienceStore_Sign_Housing'
    sign_frame.scale = (0.35, 9.6, 1.25)
    bpy.ops.object.transform_apply(scale=True)
    sign_frame.data.materials.append(mats['aluminum_dark'])
    apply_bevel(sign_frame, width=0.02, segments=2)
    col.objects.link(sign_frame)
    bpy.context.collection.objects.unlink(sign_frame)
    
    sign_face = create_vertical_display_plane('ConvenienceStore_Sign_Face', (-9.66, 20.0, 3.4), 9.4, 1.15, mats['store_sign'])
    col.objects.link(sign_face)

    # 门头下挑檐 (带射灯)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.2, 20.0, 2.75))
    canopy = bpy.context.active_object
    canopy.name = 'Store_Entrance_Canopy'
    canopy.scale = (1.2, 9.8, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    canopy.data.materials.append(mats['aluminum_dark'])
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)

    # 3. 落地玻璃幕墙与立柱 (Mullions)
    for my in [15.2, 17.6, 20.0, 22.4, 24.8]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.95, my, 1.45))
        mullion = bpy.context.active_object
        mullion.scale = (0.12, 0.10, 2.6)
        bpy.ops.object.transform_apply(scale=True)
        mullion.data.materials.append(mats['aluminum_dark'])
        apply_bevel(mullion, width=0.008, segments=2)
        col.objects.link(mullion)
        bpy.context.collection.objects.unlink(mullion)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.96, 20.0, 1.45))
    store_glass = bpy.context.active_object
    store_glass.name = 'ConvenienceStore_Front_Glass'
    store_glass.scale = (0.02, 9.4, 2.5)
    bpy.ops.object.transform_apply(scale=True)
    store_glass.data.materials.append(mats['glass'])
    col.objects.link(store_glass)
    bpy.context.collection.objects.unlink(store_glass)

    # 橱窗促销海报贴纸 (Promo Posters)
    poster_plane = create_vertical_display_plane('Store_Window_Posters', (-9.94, 18.2, 1.55), 1.6, 1.4, mats['store_posters'])
    col.objects.link(poster_plane)

    # 4. 室内发光冷饮展示立柜 (Beverage Cooler Showcase Wall)
    cooler_wall = create_vertical_display_plane('Store_Cooler_Showcase', (-16.7, 21.0, 1.55), 4.2, 2.2, mats['store_cooler'])
    col.objects.link(cooler_wall)

    # 5. 室内 3D 金属货架与琳琅满目的饮料零食陈列
    shelf_x = -12.2
    for py in [17.5, 22.5]:
        for px_off in [-0.65, 0.65]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.8, location=(shelf_x + px_off, py, 1.0))
            p_obj = bpy.context.active_object
            p_obj.data.materials.append(mats['aluminum_dark'])
            col.objects.link(p_obj)
            bpy.context.collection.objects.unlink(p_obj)
            
    for tier_z in [0.45, 0.85, 1.25, 1.65]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(shelf_x, 20.0, tier_z))
        tier = bpy.context.active_object
        tier.scale = (1.35, 5.0, 0.03)
        bpy.ops.object.transform_apply(scale=True)
        tier.data.materials.append(mats['aluminum_dark'])
        col.objects.link(tier)
        bpy.context.collection.objects.unlink(tier)
        
        # 放置高精 3D 商品模型
        for item_y_idx in range(16):
            iy = 17.8 + item_y_idx * 0.28
            bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.15, location=(shelf_x - 0.35, iy, tier_z + 0.09))
            can = bpy.context.active_object
            mat_can = mats['torii_red'] if (item_y_idx % 3 == 0) else (mats['train_yellow'] if (item_y_idx % 3 == 1) else mats['aluminum_dark'])
            can.data.materials.append(mat_can)
            col.objects.link(can)
            bpy.context.collection.objects.unlink(can)
            
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(shelf_x + 0.35, iy, tier_z + 0.10))
            box = bpy.context.active_object
            box.scale = (0.16, 0.18, 0.16)
            bpy.ops.object.transform_apply(scale=True)
            box.data.materials.append(mats['tactile_paving'] if (item_y_idx % 2 == 0) else mats['concrete_wall'])
            col.objects.link(box)
            bpy.context.collection.objects.unlink(box)

    # 6. 立体双联自动贩卖机 (红蓝经典涂装、内凹 15cm 取物舱与分类垃圾桶)
    vm_x = -9.2
    vm_y = 23.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(vm_x, vm_y, 1.05))
    vm_body = bpy.context.active_object
    vm_body.name = 'Vending_Machine_Main_Chassis'
    vm_body.scale = (0.95, 2.45, 2.05)
    bpy.ops.object.transform_apply(scale=True)
    vm_body.data.materials.append(mats['aluminum_dark'])
    apply_bevel(vm_body, width=0.02, segments=2)
    col.objects.link(vm_body)
    bpy.context.collection.objects.unlink(vm_body)

    # 贩卖机展示面板与玻璃
    vm_face = create_vertical_display_plane('Vending_Machines_Front_Panel', (-8.71, vm_y, 1.05), 2.38, 1.95, mats['vending_machine'])
    col.objects.link(vm_face)
    
    # 侧面日式饮料瓶双孔分类垃圾桶 (Can & Bottle Recycling Bin)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.2, 25.2, 0.45))
    r_bin = bpy.context.active_object
    r_bin.name = 'Recycling_Bin_Can_Bottle'
    r_bin.scale = (0.55, 0.75, 0.90)
    bpy.ops.object.transform_apply(scale=True)
    r_bin.data.materials.append(mats['concrete_wall'])
    apply_bevel(r_bin, width=0.02, segments=2)
    col.objects.link(r_bin)
    bpy.context.collection.objects.unlink(r_bin)

    return col

# ==============================================================================
# 04. 3.5m 战术夹墙小巷与民宅 B（对立双室外机与立面微生态）
# ==============================================================================
def build_tactical_alley(mats):
    col = bpy.data.collections.new('04_Tactical_Alley')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.2, 4.5
    
    # 民宅 B 基座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.22))
    plinth = bpy.context.active_object
    plinth.scale = (7.6, 7.6, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(plinth, uv_scale=1.0)
    plinth.data.materials.append(mats['concrete_wall'])
    apply_bevel(plinth, width=0.02, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)

    # 1F 墙体：铺设经典日式二丁挂瓷砖！
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 1.85))
    wall_1f = bpy.context.active_object
    wall_1f.name = 'HouseB_Wall_1F'
    wall_1f.scale = (7.2, 7.2, 2.8)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_1f, uv_scale=1.33)
    wall_1f.data.materials.append(mats['wall_facade_tiles'])
    carve_opening(wall_1f, center_x=-10.55, center_y=4.5, center_z=1.65, width=2.1, height=1.35, depth=0.8)
    apply_bevel(wall_1f, width=0.03, segments=2)
    col.objects.link(wall_1f)
    bpy.context.collection.objects.unlink(wall_1f)
    
    # 2F 墙体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 4.80))
    wall_2f = bpy.context.active_object
    wall_2f.name = 'HouseB_Wall_2F'
    wall_2f.scale = (7.0, 7.4, 2.9)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(wall_2f, uv_scale=1.0)
    wall_2f.data.materials.append(mats['wall_plaster'])
    carve_opening(wall_2f, center_x=-10.55, center_y=4.5, center_z=4.75, width=1.8, height=1.3, depth=0.8)
    apply_bevel(wall_2f, width=0.03, segments=2)
    col.objects.link(wall_2f)
    bpy.context.collection.objects.unlink(wall_2f)
    
    # 和瓦屋顶
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 6.45))
    roof = bpy.context.active_object
    roof.name = 'HouseB_Kawara_Roof'
    roof.scale = (8.4, 8.4, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(roof, uv_scale=1.66)
    roof.data.materials.append(mats['roof_kawara'])
    apply_bevel(roof, width=0.04, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)

    build_recessed_window("HouseB_Window_1F", center_x=-10.55, center_y=4.5, center_z=1.65, width=2.1, height=1.35, mats=mats, col=col, recess_depth=-0.18)
    build_recessed_window("HouseB_Window_2F", center_x=-10.55, center_y=4.5, center_z=4.75, width=1.8, height=1.3, mats=mats, col=col, recess_depth=-0.18)

    # 小巷内部两栋民宅对立双空调外机
    build_ac_unit("Alley_AC_Unit_South", center_x=-13.5, center_y=-1.4, center_z=0.45, mats=mats, col=col, rot_z=0.0)
    build_ac_unit("Alley_AC_Unit_North", center_x=-13.5, center_y=0.4, center_z=0.45, mats=mats, col=col, rot_z=math.radians(180))

    # 小巷地面石材拼铺
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.5, -0.5, 0.10))
    alley_floor = bpy.context.active_object
    alley_floor.scale = (7.0, 3.5, 0.20)
    bpy.ops.object.transform_apply(scale=True)
    apply_box_uv(alley_floor, uv_scale=0.833)
    alley_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(alley_floor)
    bpy.context.collection.objects.unlink(alley_floor)

    return col

# ==============================================================================
# 05. 混凝土电线杆生态与自然悬链线下垂高压线网络
# ==============================================================================
def build_utility_poles_and_wires(mats):
    col = bpy.data.collections.new('05_Utility_Poles_And_Wires')
    bpy.context.scene.collection.children.link(col)
    
    poles_data = [
        ("Pole_South_Plaza", -4.8, 24.0, 0.2, 9.8),
        ("Pole_Ramp_Base", -4.8, 14.5, 0.2, 9.8),
        ("Pole_Mid_Ramp", -4.8, -5.0, 3.7, 9.8),
        ("Pole_North_Torii", -4.8, -25.0, 7.2, 9.8)
    ]
    
    pole_tops = []
    
    for p_name, px, py, base_z, pole_h in poles_data:
        # 1. 混凝土锥形杆身
        cz = base_z + pole_h * 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=pole_h, location=(px, py, cz))
        pole_obj = bpy.context.active_object
        pole_obj.name = p_name
        pole_obj.data.materials.append(mats['concrete_wall'])
        bpy.ops.object.shade_smooth()
        col.objects.link(pole_obj)
        bpy.context.collection.objects.unlink(pole_obj)
        
        # 2. 12 级金属登杆脚钉
        for r_idx in range(12):
            rz = base_z + 2.2 + r_idx * 0.55
            r_ang = 90.0 if (r_idx % 2 == 0) else -90.0
            bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.28, location=(px, py, rz))
            rung = bpy.context.active_object
            rung.rotation_euler = (0.0, math.radians(r_ang), 0.0)
            rung.data.materials.append(mats['aluminum_silver'])
            col.objects.link(rung)
            bpy.context.collection.objects.unlink(rung)
            
        # 3. 柱上圆柱形三相变压器 (鞍座、套管柱、高压黄色铭牌)
        tz = base_z + pole_h - 2.8
        bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=1.1, location=(px - 0.45, py, tz))
        t_body = bpy.context.active_object
        t_body.data.materials.append(mats['transformer'])
        bpy.ops.object.shade_smooth()
        col.objects.link(t_body)
        bpy.context.collection.objects.unlink(t_body)
        
        for side_b in [-0.22, 0.0, 0.22]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.35, location=(px - 0.45, py + side_b, tz + 0.65))
            bushing = bpy.context.active_object
            bushing.data.materials.append(mats['insulator_porcelain'])
            bpy.ops.object.shade_smooth()
            col.objects.link(bushing)
            bpy.context.collection.objects.unlink(bushing)

        # 4. 双层角钢横担与绝缘子 (横向沿 X 轴展开垂直于街道)
        for arm_layer, arm_z in [(1, base_z + pole_h - 0.8), (2, base_z + pole_h - 0.2)]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, arm_z))
            crossarm1 = bpy.context.active_object
            crossarm1.scale = (2.2, 0.10, 0.10)
            bpy.ops.object.transform_apply(scale=True)
            crossarm1.data.materials.append(mats['aluminum_silver'])
            col.objects.link(crossarm1)
            bpy.context.collection.objects.unlink(crossarm1)
            
            for side_x in [-0.95, 0.0, 0.95]:
                bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.18, location=(px + side_x, py, arm_z + 0.14))
                bell = bpy.context.active_object
                bell.data.materials.append(mats['insulator_porcelain'])
                col.objects.link(bell)
                bpy.context.collection.objects.unlink(bell)
                
        # 5. 挑臂式 LED 路灯 (朝向路中心 +X 侧照明)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=1.6, location=(px + 0.65, py, base_z + pole_h - 3.2))
        a_obj = bpy.context.active_object
        a_obj.rotation_euler = (0.0, math.radians(72), 0.0)
        a_obj.data.materials.append(mats['aluminum_dark'])
        col.objects.link(a_obj)
        bpy.context.collection.objects.unlink(a_obj)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px + 1.45, py, base_z + pole_h - 2.8))
        led_head = bpy.context.active_object
        led_head.scale = (0.45, 0.24, 0.12)
        bpy.ops.object.transform_apply(scale=True)
        led_head.data.materials.append(mats['aluminum_dark'])
        col.objects.link(led_head)
        bpy.context.collection.objects.unlink(led_head)

        pole_tops.append((px, py, base_z + pole_h))

    # 自然重力悬链线高压线网络 (沿街道纵向连接至各杆塔，转为网格几何体)
    for p_idx in range(len(pole_tops) - 1):
        p1 = pole_tops[p_idx]
        p2 = pole_tops[p_idx + 1]
        for off_x in [-0.95, 0.0, 0.95]:
            cable = build_catenary_curve(
                f"HighVoltage_Cable_{p_idx}_{off_x}",
                (p1[0] + off_x, p1[1], p1[2] - 0.2),
                (p2[0] + off_x, p2[1], p2[2] - 0.2),
                sag=0.42,
                segments=24,
                radius=0.014,
                material=mats['cable_rubber']
            )
            col.objects.link(cable)
            
        for off_x in [-0.65, 0.65]:
            low_cable = build_catenary_curve(
                f"Comm_Cable_{p_idx}_{off_x}",
                (p1[0] + off_x, p1[1], p1[2] - 0.8),
                (p2[0] + off_x, p2[1], p2[2] - 0.8),
                sag=0.55,
                segments=24,
                radius=0.011,
                material=mats['cable_rubber']
            )
            col.objects.link(low_cable)

    return col

def build_street_props_ecology(mats):
    col = bpy.data.collections.new('06_Street_Props_Ecology')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 坡道交界处道路安全反光凸面镜 (Curved Convex Mirror)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=3.2, location=(-4.8, 14.5, 1.6))
    post = bpy.context.active_object
    post.name = 'Traffic_Mirror_Post'
    post.data.materials.append(mats['aluminum_silver'])
    col.objects.link(post)
    bpy.context.collection.objects.unlink(post)
    
    # 广角镜橙色外罩
    bpy.ops.mesh.primitive_cylinder_add(radius=0.48, depth=0.08, location=(-4.8, 14.5, 3.0))
    mirror_frame = bpy.context.active_object
    mirror_frame.rotation_euler = (math.radians(-15), math.radians(25), math.radians(45))
    mirror_frame.data.materials.append(mats['torii_red'])
    col.objects.link(mirror_frame)
    bpy.context.collection.objects.unlink(mirror_frame)
    
    # 凸镜银色反射面
    bpy.ops.mesh.primitive_cylinder_add(radius=0.44, depth=0.04, location=(-4.76, 14.54, 3.02))
    mirror_lens = bpy.context.active_object
    mirror_lens.rotation_euler = (math.radians(-15), math.radians(25), math.radians(45))
    mirror_lens.data.materials.append(mats['aluminum_silver'])
    col.objects.link(mirror_lens)
    bpy.context.collection.objects.unlink(mirror_lens)

    # 2. 黄色高强反光交通锥 (Traffic Cones with Reflective Stripe)
    for c_idx, c_y in enumerate([19.2, 21.0]):
        # 底座
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.2, c_y, 0.22))
        c_base = bpy.context.active_object
        c_base.name = f"Traffic_Cone_Base_{c_idx}"
        c_base.scale = (0.42, 0.42, 0.04)
        bpy.ops.object.transform_apply(scale=True)
        c_base.data.materials.append(mats['torii_black'])
        col.objects.link(c_base)
        bpy.context.collection.objects.unlink(c_base)
        
        # 锥体
        bpy.ops.mesh.primitive_cone_add(radius1=0.18, radius2=0.03, depth=0.70, location=(-4.2, c_y, 0.57))
        cone = bpy.context.active_object
        cone.name = f"Traffic_Cone_Body_{c_idx}"
        cone.data.materials.append(mats['train_yellow'])
        col.objects.link(cone)
        bpy.context.collection.objects.unlink(cone)
        
        # 反光白色贴膜环
        bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.14, location=(-4.2, c_y, 0.55))
        c_band = bpy.context.active_object
        c_band.data.materials.append(mats['aluminum_silver'])
        col.objects.link(c_band)
        bpy.context.collection.objects.unlink(c_band)

    # 3. 日式经典双口红色邮政筒 (Japanese Red Mailbox)
    mb_x, mb_y = -5.0, 16.2
    # 黑色铸铁底座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mb_x, mb_y, 0.25))
    mb_base = bpy.context.active_object
    mb_base.scale = (0.40, 0.52, 0.28)
    bpy.ops.object.transform_apply(scale=True)
    mb_base.data.materials.append(mats['aluminum_dark'])
    col.objects.link(mb_base)
    bpy.context.collection.objects.unlink(mb_base)
    
    # 红色主箱体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mb_x, mb_y, 0.85))
    mb_body = bpy.context.active_object
    mb_body.name = "Japanese_Mailbox_Body"
    mb_body.scale = (0.44, 0.65, 0.88)
    bpy.ops.object.transform_apply(scale=True)
    mb_body.data.materials.append(mats['torii_red'])
    apply_bevel(mb_body, width=0.02, segments=2)
    col.objects.link(mb_body)
    bpy.context.collection.objects.unlink(mb_body)
    
    # 双投递口
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mb_x + 0.21, mb_y, 1.10))
    mb_slot = bpy.context.active_object
    mb_slot.scale = (0.05, 0.48, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    mb_slot.data.materials.append(mats['aluminum_dark'])
    col.objects.link(mb_slot)
    bpy.context.collection.objects.unlink(mb_slot)
    
    # 邮筒白色取信时刻牌
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mb_x + 0.22, mb_y, 0.75))
    mb_plate = bpy.context.active_object
    mb_plate.scale = (0.02, 0.32, 0.35)
    bpy.ops.object.transform_apply(scale=True)
    mb_plate.data.materials.append(mats['store_posters'])
    col.objects.link(mb_plate)
    bpy.context.collection.objects.unlink(mb_plate)

    # 4. 日式分类环保垃圾箱 (双联：饮料瓶罐 / 可燃垃圾)
    tb_x, tb_y = -5.3, 17.8
    # 蓝色饮料瓶罐回收箱
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tb_x, tb_y - 0.30, 0.60))
    bin_blue = bpy.context.active_object
    bin_blue.name = "Recycle_Bin_Bottles"
    bin_blue.scale = (0.42, 0.42, 0.88)
    bpy.ops.object.transform_apply(scale=True)
    bin_blue.data.materials.append(mats['vending_machine'])
    apply_bevel(bin_blue, width=0.02, segments=2)
    col.objects.link(bin_blue)
    bpy.context.collection.objects.unlink(bin_blue)
    
    # 投瓶圆孔
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.04, location=(tb_x + 0.20, tb_y - 0.30, 0.85))
    hole = bpy.context.active_object
    hole.rotation_euler = (0.0, math.radians(90), 0.0)
    hole.data.materials.append(mats['aluminum_dark'])
    col.objects.link(hole)
    bpy.context.collection.objects.unlink(hole)
    
    # 灰色可燃垃圾箱
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(tb_x, tb_y + 0.30, 0.60))
    bin_grey = bpy.context.active_object
    bin_grey.name = "Trash_Bin_Burnable"
    bin_grey.scale = (0.42, 0.42, 0.88)
    bpy.ops.object.transform_apply(scale=True)
    bin_grey.data.materials.append(mats['concrete_wall'])
    apply_bevel(bin_grey, width=0.02, segments=2)
    col.objects.link(bin_grey)
    bpy.context.collection.objects.unlink(bin_grey)

    return col

# ==============================================================================
# 主执行入口：全流程构建与 glTF / Blend 导出
# ==============================================================================
def main():
    print("==================================================================")
    print("Starting Next-Gen Urban Neighborhood Rebuild (PolyHaven PBR + ZZZ Details)")
    print("==================================================================")
    clean_scene()
    
    mats = {
        # 1. 扫描级日式沥青道路 (含斑马线、减速菱形标线、停止线)
        'asphalt_road': create_gltf_pbr_material(
            "M_AsphaltRoad",
            "japanese_asphalt_diffuse.jpg",
            normal_file="japanese_asphalt_normal.jpg",
            roughness_file="japanese_asphalt_roughness.jpg",
            fallback_color=(0.24, 0.24, 0.25, 1.0),
            roughness_val=0.86,
            normal_strength=1.8
        ),
        # 2. 真实预制板岩石材人行道地砖 (彻底终结黑线网格)
        'sidewalk_tiles': create_gltf_pbr_material(
            "M_SidewalkTiles",
            "precast_stone_paving_diffuse.jpg",
            normal_file="precast_stone_paving_normal.jpg",
            roughness_file="precast_stone_paving_roughness.jpg",
            fallback_color=(0.68, 0.67, 0.64, 1.0),
            roughness_val=0.68,
            normal_strength=1.6
        ),
        # 3. 现浇清水混凝土墙体与倒角路缘石
        'concrete_wall': create_gltf_pbr_material(
            "M_ConcreteWall",
            "concrete_wall_001_diffuse.jpg",
            normal_file="concrete_wall_001_normal.jpg",
            roughness_file="concrete_wall_001_roughness.jpg",
            fallback_color=(0.60, 0.61, 0.62, 1.0),
            roughness_val=0.74,
            normal_strength=1.5
        ),
        # 4. 日式经典二丁挂立面窄条瓷砖 (民宅 1F)
        'wall_facade_tiles': create_gltf_pbr_material(
            "M_WallFacadeTiles",
            "rectangular_facade_tiles_diffuse.jpg",
            normal_file="rectangular_facade_tiles_normal.jpg",
            roughness_file="rectangular_facade_tiles_roughness.jpg",
            fallback_color=(0.78, 0.77, 0.74, 1.0),
            roughness_val=0.55,
            normal_strength=1.8
        ),
        # 5. 日式住宅质感涂料外墙 (民宅 2F)
        'wall_plaster': create_gltf_pbr_material(
            "M_WallPlaster",
            "grey_plaster_02_diffuse.jpg",
            normal_file="grey_plaster_02_normal.jpg",
            roughness_file="grey_plaster_02_roughness.jpg",
            fallback_color=(0.82, 0.81, 0.78, 1.0),
            roughness_val=0.82,
            normal_strength=1.6
        ),
        # 6. 日式和瓦灰瓦屋顶
        'roof_kawara': create_gltf_pbr_material(
            "M_RoofKawara",
            "grey_roof_tiles_diffuse.jpg",
            normal_file="grey_roof_tiles_normal.jpg",
            roughness_file="grey_roof_tiles_roughness.jpg",
            fallback_color=(0.28, 0.28, 0.30, 1.0),
            roughness_val=0.52,
            normal_strength=2.2
        ),
        # 7. 商业裙楼复古面砖
        'brick_commercial': create_gltf_pbr_material(
            "M_BrickCommercial",
            "brick_wall_001_diffuse.jpg",
            normal_file="brick_wall_001_normal.jpg",
            roughness_file="brick_wall_001_roughness.jpg",
            fallback_color=(0.55, 0.48, 0.42, 1.0),
            roughness_val=0.78,
            normal_strength=1.8
        ),
        # 8. 现代高层大厦 16层幕墙与窗格分层贴图
        'skyline_facade': create_gltf_pbr_material(
            "M_SkylineFacade",
            "skyline_facade_diffuse.jpg",
            normal_file="skyline_facade_normal.jpg",
            roughness_file="skyline_facade_roughness.jpg",
            emissive_file="skyline_facade_emissive.jpg",
            fallback_color=(0.18, 0.20, 0.24, 1.0),
            roughness_val=0.35,
            emissive_strength=1.2
        ),
        # 9. 黄色导盲道
        'tactile_paving': create_gltf_pbr_material(
            "M_TactilePaving",
            "tactile_paving_albedo.png",
            normal_file="tactile_paving_normal.png",
            roughness_file="tactile_paving_roughness.png",
            fallback_color=(0.94, 0.72, 0.05, 1.0),
            roughness_val=0.52,
            normal_strength=2.2
        ),
        # 10. 铸铁井盖与透空格栅
        'metal_manhole': create_gltf_pbr_material(
            "M_MetalManhole",
            "metal_manhole_albedo.png",
            normal_file="metal_manhole_normal.png",
            roughness_file="metal_manhole_roughness.png",
            fallback_color=(0.16, 0.17, 0.18, 1.0),
            roughness_val=0.45,
            metallic_val=0.85,
            normal_strength=2.4
        ),
        # 11. 双联自动贩卖机
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
        # 12. 便利店门头灯箱
        'store_sign': create_gltf_pbr_material(
            "M_StoreSign",
            "convenience_store_sign_2k_albedo.png",
            emissive_file="convenience_store_sign_2k_emissive.png",
            fallback_color=(0.95, 0.95, 0.95, 1.0),
            roughness_val=0.25,
            emissive_strength=1.5
        ),
        # 13. 便利店冷饮立柜
        'store_cooler': create_gltf_pbr_material(
            "M_StoreCooler",
            "store_cooler_showcase.jpg",
            emissive_file="store_cooler_showcase.jpg",
            fallback_color=(0.1, 0.1, 0.15, 1.0),
            roughness_val=0.20,
            emissive_strength=1.6
        ),
        # 14. 橱窗海报
        'store_posters': create_gltf_pbr_material(
            "M_StorePosters",
            "store_window_posters.png",
            fallback_color=(0.95, 0.95, 0.95, 1.0),
            roughness_val=0.40
        ),
        # 辅助金属与玻璃
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
    
    # 构建各大子系统
    build_environment_skyline(mats)
    build_terrain_and_roads(mats)
    build_house_a(mats)
    build_convenience_store(mats)
    build_tactical_alley(mats)
    build_utility_poles_and_wires(mats)
    build_street_props_ecology(mats)
    
    # 导出文件
    blend_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\neighborhood"
    ensure_dir(blend_dir)
    blend_path = os.path.join(blend_dir, "modern_japan_neighborhood.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved .blend project to: {blend_path}")
    
    export_targets = [
        r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\models\environment\modern_japan_neighborhood.glb",
        r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\environment\modern_japan_neighborhood.glb"
    ]
    
    for glb_path in export_targets:
        ensure_dir(os.path.dirname(glb_path))
        print(f"Exporting glTF to: {glb_path} ...")
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            use_selection=False,
            export_apply=True,
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_materials='EXPORT',
            export_image_format='AUTO'
        )
        file_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
        print(f"Successfully exported {glb_path} ({file_size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
