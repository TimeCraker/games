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

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def find_texture(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, 'textures'),
        os.path.join(script_dir, 'textures', 'golden_slice'),
        os.path.join(os.path.dirname(script_dir), 'client-godot-v2', 'textures'),
        os.path.join(os.path.dirname(script_dir), 'art', 'textures'),
        os.path.join(os.path.dirname(script_dir), 'art', 'textures', 'golden_slice'),
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\textures\golden_slice',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\client-godot-v2\textures',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\art\textures',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\art\textures\golden_slice',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\client-godot-v2\textures',
        r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\textures'
    ]
    for c in candidates:
        p = os.path.join(c, filename)
        if os.path.exists(p):
            return p
    return None

def create_vertical_display_plane(name, center_pos, width_y, height_z, material):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    obj = bpy.data.objects.new(name, mesh)
    hy = width_y / 2.0
    hz = height_z / 2.0
    cx, cy, cz = center_pos
    # 严格确保法线指向 +X（朝向街道相机，绝对杜绝背面透射镜像）
    verts = [
        (cx, cy + hy, cz - hz),  # 0: 左下 (+Y, -Z)
        (cx, cy + hy, cz + hz),  # 1: 左上 (+Y, +Z)
        (cx, cy - hy, cz + hz),  # 2: 右上 (-Y, +Z)
        (cx, cy - hy, cz - hz)   # 3: 右下 (-Y, -Z)
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    # 相机面朝 -X，左侧为 -Y，右侧为 +Y；因此 +Y 对应 U=1.0，-Y 对应 U=0.0，杜绝文字镜像
    uvs = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    for loop_idx, loop in enumerate(mesh.loops):
        uv_layer.data[loop_idx].uv = uvs[loop_idx]
    obj.data.materials.append(material)
    return obj

def build_recessed_window(name, center_pos, width_y, height_z, depth_x=0.18, mats=None, parent_col=None):
    cx, cy, cz = center_pos
    # 1. 18cm 物理内嵌窗洞套框 (深色氟碳铝合金)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx - depth_x / 2.0, cy, cz))
    frame_box = bpy.context.active_object
    frame_box.name = name + '_Recessed_Box'
    frame_box.scale = (depth_x, width_y + 0.08, height_z + 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    frame_box.data.materials.append(mats['aluminum_dark'])
    if parent_col:
        parent_col.objects.link(frame_box)
        bpy.context.collection.objects.unlink(frame_box)
    
    # 2. 内嵌铝合金窗扇滑轨外框
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx - depth_x + 0.02, cy, cz))
    sash_frame = bpy.context.active_object
    sash_frame.name = name + '_Sash'
    sash_frame.scale = (0.04, width_y, height_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sash_frame.data.materials.append(mats['aluminum_dark'])
    if parent_col:
        parent_col.objects.link(sash_frame)
        bpy.context.collection.objects.unlink(sash_frame)
    
    # 3. 中隔垂直竖挺
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx - depth_x + 0.025, cy, cz))
    mullion = bpy.context.active_object
    mullion.name = name + '_Mullion'
    mullion.scale = (0.05, 0.05, height_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mullion.data.materials.append(mats['aluminum_dark'])
    if parent_col:
        parent_col.objects.link(mullion)
        bpy.context.collection.objects.unlink(mullion)
    
    # 4. 双层反射玻璃
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx - depth_x + 0.03, cy, cz))
    glass_pane = bpy.context.active_object
    glass_pane.name = name + '_Glass'
    glass_pane.scale = (0.015, width_y - 0.06, height_z - 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    glass_pane.data.materials.append(mats['glass'])
    if parent_col:
        parent_col.objects.link(glass_pane)
        bpy.context.collection.objects.unlink(glass_pane)
    
    # 5. 窗台下沿金属滴水板 (Sill Drip Ledge)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx + 0.02, cy, cz - height_z / 2.0 - 0.02))
    sill = bpy.context.active_object
    sill.name = name + '_Sill'
    sill.scale = (depth_x + 0.06, width_y + 0.12, 0.03)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sill.data.materials.append(mats['aluminum_silver'])
    if parent_col:
        parent_col.objects.link(sill)
        bpy.context.collection.objects.unlink(sill)

def build_downspout(name, p_top, height, mats, parent_col=None):
    tx, ty, tz = p_top
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=height, location=(tx, ty, tz - height / 2.0))
    spout = bpy.context.active_object
    spout.name = name
    spout.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    if parent_col:
        parent_col.objects.link(spout)
        bpy.context.collection.objects.unlink(spout)
    for ring_i in range(1, 4):
        rz = tz - (height / 4.0) * ring_i
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.03, location=(tx, ty, rz))
        ring = bpy.context.active_object
        ring.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        if parent_col:
            parent_col.objects.link(ring)
            bpy.context.collection.objects.unlink(ring)

def build_entrance_door(name, center_pos, mats, parent_col=None):
    cx, cy, cz = center_pos
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, cz))
    door = bpy.context.active_object
    door.name = name
    door.scale = (0.08, 1.05, 2.20)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    door.data.materials.append(mats['aluminum_dark'])
    if parent_col:
        parent_col.objects.link(door)
        bpy.context.collection.objects.unlink(door)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.45, location=(cx + 0.05, cy - 0.35, cz))
    handle = bpy.context.active_object
    handle.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    if parent_col:
        parent_col.objects.link(handle)
        bpy.context.collection.objects.unlink(handle)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx + 0.35, cy, cz + 1.25))
    canopy = bpy.context.active_object
    canopy.scale = (0.75, 1.30, 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(mats['aluminum_dark'])
    if parent_col:
        parent_col.objects.link(canopy)
        bpy.context.collection.objects.unlink(canopy)

def create_pbr_material(name, tex_prefix, fallback_color=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, uv_scale=(1.0, 1.0), normal_strength=1.5):
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
    
    alb_path = find_texture(f'{tex_prefix}_albedo.png') or find_texture(f'{tex_prefix}_2k.png') or find_texture(f'{tex_prefix}.png')
    if alb_path:
        img_node = nodes.new('ShaderNodeTexImage')
        img_node.image = bpy.data.images.load(alb_path)
        links.new(mapping.outputs['Vector'], img_node.inputs['Vector'])
        links.new(img_node.outputs['Color'], bsdf.inputs['Base Color'])
        
    rgh_path = find_texture(f'{tex_prefix}_roughness.png') or find_texture(f'{tex_prefix}_2k_roughness.png')
    if rgh_path:
        r_node = nodes.new('ShaderNodeTexImage')
        r_node.image = bpy.data.images.load(rgh_path)
        r_node.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], r_node.inputs['Vector'])
        links.new(r_node.outputs['Color'], bsdf.inputs['Roughness'])
        
    nrm_path = find_texture(f'{tex_prefix}_normal.png') or find_texture(f'{tex_prefix}_2k_normal.png')
    if nrm_path:
        n_node = nodes.new('ShaderNodeTexImage')
        n_node.image = bpy.data.images.load(nrm_path)
        n_node.image.colorspace_settings.name = 'Non-Color'
        n_map = nodes.new('ShaderNodeNormalMap')
        n_map.inputs['Strength'].default_value = normal_strength
        links.new(mapping.outputs['Vector'], n_node.inputs['Vector'])
        links.new(n_node.outputs['Color'], n_map.inputs['Color'])
        links.new(n_map.outputs['Normal'], bsdf.inputs['Normal'])
        
    return mat

def create_glass_material(name='M_Glass', tint=(0.94, 0.97, 0.99, 1.0)):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out_node = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = tint
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    bsdf.inputs['IOR'].default_value = 1.52
    return mat

def create_emissive_material(name, color=(1.0, 0.95, 0.85, 1.0), strength=3.0, tex_name=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out_node = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Strength'].default_value = strength
    links.new(emit.outputs['Emission'], out_node.inputs['Surface'])
    if tex_name:
        p = find_texture(tex_name)
        if p:
            img = nodes.new('ShaderNodeTexImage')
            img.image = bpy.data.images.load(p)
            links.new(img.outputs['Color'], emit.inputs['Color'])
            return mat
    emit.inputs['Color'].default_value = color
    return mat

def create_custom_colored_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

def apply_bevel(obj, width=0.02, segments=2):
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

# ==============================================================================
# 构建全封闭宏观街区底座与背景建筑群 (Eliminate Black Void & Cliff)
# ==============================================================================
def build_environment_backdrop(mats):
    col = bpy.data.collections.new('00_Environment_Backdrop')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 180m x 180m 宏观连续地坪，彻底杜绝悬浮岛断崖
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, -0.05))
    ground = bpy.context.active_object
    ground.name = 'Macro_District_Ground'
    ground.scale = (180.0, 180.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ground.data.materials.append(mats['asphalt_road'])
    col.objects.link(ground)
    bpy.context.collection.objects.unlink(ground)
    
    # 2. 北侧神社与高台护坡挡墙 (Y: -35 to -70)
    for layer_i, ly in enumerate([-36.0, -46.0, -56.0]):
        lz = 6.0 + layer_i * 4.0
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, ly, lz + 2.0))
        wall = bpy.context.active_object
        wall.name = f'North_Retaining_Wall_{layer_i}'
        wall.scale = (60.0, 1.5, 4.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        wall.data.materials.append(mats['concrete_curb'])
        apply_bevel(wall, width=0.08, segments=2)
        col.objects.link(wall)
        bpy.context.collection.objects.unlink(wall)
        
        for hx in [-18.0, 0.0, 18.0]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.0, lz + 5.5))
            nh = bpy.context.active_object
            nh.name = f'North_Hill_House_{layer_i}_{hx}'
            nh.scale = (11.0, 8.0, 7.0)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            nh.data.materials.append(mats['wall_plaster'])
            apply_bevel(nh, width=0.05, segments=2)
            col.objects.link(nh)
            bpy.context.collection.objects.unlink(nh)
            
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.0, lz + 9.2))
            nr = bpy.context.active_object
            nr.scale = (11.8, 8.8, 0.5)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            nr.data.materials.append(mats['aluminum_dark'])
            col.objects.link(nr)
            bpy.context.collection.objects.unlink(nr)

    # 3. 南侧商业轻轨高架桥与商厦立面 (对标 ZZZ 参考图 12，阻断南向视线)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 42.0, 7.5))
    rail_deck = bpy.context.active_object
    rail_deck.name = 'Monorail_Overpass_Deck'
    rail_deck.scale = (80.0, 8.0, 1.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rail_deck.data.materials.append(mats['concrete_curb'])
    apply_bevel(rail_deck, width=0.06, segments=2)
    col.objects.link(rail_deck)
    bpy.context.collection.objects.unlink(rail_deck)
    
    for py in [38.2, 45.8]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, py, 8.6))
        barrier = bpy.context.active_object
        barrier.scale = (80.0, 0.25, 1.2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        barrier.data.materials.append(mats['aluminum_silver'])
        col.objects.link(barrier)
        bpy.context.collection.objects.unlink(barrier)
        
    for px in [-22.0, 0.0, 22.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, 42.0, 3.5))
        pillar = bpy.context.active_object
        pillar.name = f'Monorail_Pillar_{px}'
        pillar.scale = (2.8, 3.2, 7.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        pillar.data.materials.append(mats['concrete_curb'])
        apply_bevel(pillar, width=0.05, segments=2)
        col.objects.link(pillar)
        bpy.context.collection.objects.unlink(pillar)

    for bx, bw, bh in [(-25.0, 18.0, 22.0), (0.0, 22.0, 26.0), (26.0, 18.0, 20.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, 52.0, bh / 2.0))
        tower = bpy.context.active_object
        tower.name = f'South_Commercial_Tower_{bx}'
        tower.scale = (bw, 12.0, bh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        tower.data.materials.append(mats['wall_plaster'])
        apply_bevel(tower, width=0.05, segments=2)
        col.objects.link(tower)
        bpy.context.collection.objects.unlink(tower)

    # 4. 西侧高层公寓住宅群 (West Skyline, X = -28.0)
    for wy, wh, ww in [(-18.0, 18.0, 14.0), (0.0, 22.0, 16.0), (20.0, 19.0, 14.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-28.0, wy, wh / 2.0))
        mansion = bpy.context.active_object
        mansion.name = f'West_Mansion_Tower_{wy}'
        mansion.scale = (12.0, ww, wh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mansion.data.materials.append(mats['wall_plaster'])
        apply_bevel(mansion, width=0.05, segments=2)
        col.objects.link(mansion)
        bpy.context.collection.objects.unlink(mansion)

    # 5. 东侧护坡挡墙 (East Wall, X = +9.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(9.0, 0.0, 2.0))
    e_wall = bpy.context.active_object
    e_wall.name = 'East_District_Boundary_Wall'
    e_wall.scale = (1.2, 70.0, 4.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    e_wall.data.materials.append(mats['concrete_curb'])
    apply_bevel(e_wall, width=0.04, segments=2)
    col.objects.link(e_wall)
    bpy.context.collection.objects.unlink(e_wall)
    
    return col

# ==============================================================================
# 道路、坡道与人行道系统
# ==============================================================================
def build_terrain_and_roads(mats):
    col = bpy.data.collections.new('01_Roads_And_Terrain')
    bpy.context.scene.collection.children.link(col)
    
    slope_angle = math.atan2(-6.0, 35.0)
    
    # 南端生活广场主路 (Y: 10.0 to 36.0, X: -4.0 to 4.0)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 23.0, 0.005))
    plz_road = bpy.context.active_object
    plz_road.name = 'Road_South_Plaza'
    plz_road.scale = (8.0, 26.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(plz_road)
    bpy.context.collection.objects.unlink(plz_road)
    
    # 南端西侧人行道
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, 23.0, 0.075))
    plz_sw_w = bpy.context.active_object
    plz_sw_w.name = 'Sidewalk_Plaza_West'
    plz_sw_w.scale = (10.0, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_sw_w.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_w)
    bpy.context.collection.objects.unlink(plz_sw_w)
    
    # 人行道路缘石
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.1, 23.0, 0.075))
    curb_w = bpy.context.active_object
    curb_w.name = 'Curb_Plaza_West'
    curb_w.scale = (0.2, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    curb_w.data.materials.append(mats['concrete_curb'])
    apply_bevel(curb_w, width=0.02, segments=2)
    col.objects.link(curb_w)
    bpy.context.collection.objects.unlink(curb_w)
    
    # 导盲道
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-4.8, 23.0, 0.152))
    plz_tac = bpy.context.active_object
    plz_tac.name = 'Tactile_Plaza_West'
    plz_tac.scale = (0.6, 26.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_tac.data.materials.append(mats['tactile_paving'])
    col.objects.link(plz_tac)
    bpy.context.collection.objects.unlink(plz_tac)
    
    # 40m 自然长坡道 (Central Long Ramp, Y: +10.0 to -25.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -7.5, 3.0))
    ramp_road = bpy.context.active_object
    ramp_road.name = 'Road_Central_Slope_Ramp'
    ramp_road.scale = (7.0, 35.5, 0.2)
    ramp_road.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(ramp_road)
    bpy.context.collection.objects.unlink(ramp_road)
    
    # 坡道西侧人行道
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.0, -7.5, 3.12))
    ramp_sw = bpy.context.active_object
    ramp_sw.name = 'Sidewalk_Central_Slope_West'
    ramp_sw.scale = (2.6, 35.5, 0.2)
    ramp_sw.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_sw.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ramp_sw)
    bpy.context.collection.objects.unlink(ramp_sw)
    
    # 坡道西侧路缘石
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.6, -7.5, 3.10))
    ramp_curb = bpy.context.active_object
    ramp_curb.name = 'Curb_Central_Slope_West'
    ramp_curb.scale = (0.2, 35.5, 0.25)
    ramp_curb.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_curb.data.materials.append(mats['concrete_curb'])
    apply_bevel(ramp_curb, width=0.02, segments=2)
    col.objects.link(ramp_curb)
    bpy.context.collection.objects.unlink(ramp_curb)

    # 坡道东侧对称人行道 (消除右侧空缺断崖)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.0, -7.5, 3.12))
    ramp_sw_e = bpy.context.active_object
    ramp_sw_e.name = 'Sidewalk_Central_Slope_East'
    ramp_sw_e.scale = (2.6, 35.5, 0.2)
    ramp_sw_e.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_sw_e.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ramp_sw_e)
    bpy.context.collection.objects.unlink(ramp_sw_e)
    
    # 坡道东侧路缘石
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.6, -7.5, 3.10))
    ramp_curb_e = bpy.context.active_object
    ramp_curb_e.name = 'Curb_Central_Slope_East'
    ramp_curb_e.scale = (0.2, 35.5, 0.25)
    ramp_curb_e.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_curb_e.data.materials.append(mats['concrete_curb'])
    apply_bevel(ramp_curb_e, width=0.02, segments=2)
    col.objects.link(ramp_curb_e)
    bpy.context.collection.objects.unlink(ramp_curb_e)

    # 南端东侧人行道与路缘石
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.5, 23.0, 0.075))
    plz_sw_e = bpy.context.active_object
    plz_sw_e.name = 'Sidewalk_Plaza_East'
    plz_sw_e.scale = (5.0, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_sw_e.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_e)
    bpy.context.collection.objects.unlink(plz_sw_e)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.1, 23.0, 0.075))
    curb_e = bpy.context.active_object
    curb_e.name = 'Curb_Plaza_East'
    curb_e.scale = (0.2, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    curb_e.data.materials.append(mats['concrete_curb'])
    apply_bevel(curb_e, width=0.02, segments=2)
    col.objects.link(curb_e)
    bpy.context.collection.objects.unlink(curb_e)

    # 日式白色钢管防护栏杆 (沿东侧人行道外延排布)
    m_white_guard = create_custom_colored_material('M_GuardrailWhite', (0.92, 0.93, 0.94, 1.0), roughness=0.35)
    for gr_y in range(-24, 8, 4):
        gr_z = 3.0 + (gr_y + 7.5) * (-6.0 / 35.0)
        # 立柱
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.85, location=(6.2, gr_y, gr_z + 0.55))
        post = bpy.context.active_object
        post.rotation_euler = (slope_angle, 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        post.data.materials.append(m_white_guard)
        bpy.ops.object.shade_smooth()
        col.objects.link(post)
        bpy.context.collection.objects.unlink(post)
    # 横管
    for beam_dz in [0.45, 0.75]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=33.0, location=(6.2, -8.0, 3.0 + beam_dz))
        beam = bpy.context.active_object
        beam.rotation_euler = (slope_angle + math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        beam.data.materials.append(m_white_guard)
        bpy.ops.object.shade_smooth()
        col.objects.link(beam)
        bpy.context.collection.objects.unlink(beam)
    
    # 坡顶北侧高台露台 (Y: -25.0 to -36.0, Z = 6.0m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -30.5, 5.9))
    terrace = bpy.context.active_object
    terrace.name = 'North_High_Terrace_Platform'
    terrace.scale = (32.0, 11.0, 0.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    terrace.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(terrace)
    bpy.context.collection.objects.unlink(terrace)
    
    # 红色鸟居
    torii_col = bpy.data.collections.new('High_Terrace_Torii')
    col.children.link(torii_col)
    m_vermilion = create_custom_colored_material('M_ToriiVermilion', (0.85, 0.18, 0.08, 1.0), roughness=0.45)
    m_black_cap = create_custom_colored_material('M_ToriiBlackCap', (0.08, 0.08, 0.09, 1.0), roughness=0.50)
    
    for p_x in [-1.5, 1.5]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=3.8, location=(p_x, -32.0, 8.0))
        post = bpy.context.active_object
        post.data.materials.append(m_vermilion)
        bpy.ops.object.shade_smooth()
        torii_col.objects.link(post)
        bpy.context.collection.objects.unlink(post)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.24, depth=0.35, location=(p_x, -32.0, 6.25))
        pl = bpy.context.active_object
        pl.data.materials.append(m_black_cap)
        torii_col.objects.link(pl)
        bpy.context.collection.objects.unlink(pl)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -32.0, 9.9))
    kasagi = bpy.context.active_object
    kasagi.scale = (4.4, 0.36, 0.28)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    kasagi.data.materials.append(m_vermilion)
    apply_bevel(kasagi, width=0.04, segments=2)
    torii_col.objects.link(kasagi)
    bpy.context.collection.objects.unlink(kasagi)

    # 人行横道斑马线 (Y = 10.0)
    m_white_paint = create_custom_colored_material('M_WhiteRoadPaint', (0.88, 0.89, 0.88, 1.0), roughness=0.65)
    for z_i in range(8):
        zx = -3.0 + z_i * 0.85
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(zx, 10.0, 0.01))
        stripe = bpy.context.active_object
        stripe.name = f'Zebra_Stripe_{z_i}'
        stripe.scale = (0.45, 2.8, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stripe.data.materials.append(m_white_paint)
        col.objects.link(stripe)
        bpy.context.collection.objects.unlink(stripe)
        
    # 铸铁井盖
    bpy.ops.mesh.primitive_cylinder_add(radius=0.40, depth=0.02, location=(-1.2, 16.0, 0.01))
    mh = bpy.context.active_object
    mh.name = 'Plaza_Manhole'
    mh.data.materials.append(mats['metal_manhole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(mh)
    bpy.context.collection.objects.unlink(mh)
    
    # 排水篦子
    for d_idx, dy in enumerate([2.0, -8.0, -18.0]):
        dz = 3.0 + (dy + 7.5) * (-6.0 / 35.0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.4, dy, dz + 0.02))
        dg = bpy.context.active_object
        dg.name = f'Slope_Drain_Grate_{d_idx}'
        dg.scale = (0.28, 0.85, 0.02)
        dg.rotation_euler = (slope_angle, 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        dg.data.materials.append(mats['metal_manhole'])
        col.objects.link(dg)
        bpy.context.collection.objects.unlink(dg)

    return col

# ==============================================================================
# 房屋 A：现代标准住宅 (House_A with Balcony & Carport)
# ==============================================================================
def build_house_a(mats):
    col = bpy.data.collections.new('02_House_A_Standard')
    bpy.context.scene.collection.children.link(col)
    
    hx = -14.25
    hy = -5.25
    hz_base = 2.5
    
    # 0. 地基加深下延 (深埋入土，绝不悬空)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base - 0.2))
    plinth = bpy.context.active_object
    plinth.scale = (7.6, 10.6, 1.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.03, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 1. 1F 主体外墙 (东外立面位于 X = -10.55)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 1.9))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = 'House_A_1F_Wall'
    bldg_1f.scale = (7.4, 10.4, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    # 2. 楼层深色铝合金腰线
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 3.35))
    belt = bpy.context.active_object
    belt.scale = (7.5, 10.5, 0.14)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 3. 2F 主体外墙 (东外立面位于 X = -10.95)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx - 0.4, hy, hz_base + 4.8))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = 'House_A_2F_Wall'
    bldg_2f.scale = (6.6, 10.4, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    # 4. 屋顶挑檐
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 6.3))
    roof = bpy.context.active_object
    roof.scale = (8.0, 11.0, 0.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 5. 二楼挑檐阳台 (X: -9.7, Y: -5.25, Z: 4.45m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.7, hy, 4.45))
    balc_slab = bpy.context.active_object
    balc_slab.name = 'House_A_Balcony_Floor'
    balc_slab.scale = (1.6, 4.4, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc_slab.data.materials.append(mats['concrete_curb'])
    apply_bevel(balc_slab, width=0.02, segments=2)
    col.objects.link(balc_slab)
    bpy.context.collection.objects.unlink(balc_slab)
    
    # 阳台金属扶手
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=4.4, location=(-8.92, hy, 5.50))
    front_rail = bpy.context.active_object
    front_rail.rotation_euler = (math.radians(90), 0, 0)
    front_rail.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(front_rail)
    bpy.context.collection.objects.unlink(front_rail)
    
    # 磨砂玻璃栏板
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.92, hy, 4.95))
    balc_glass = bpy.context.active_object
    balc_glass.scale = (0.02, 4.3, 0.85)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc_glass.data.materials.append(mats['glass'])
    col.objects.link(balc_glass)
    bpy.context.collection.objects.unlink(balc_glass)

    # 6. 次世代 18cm 物理内嵌窗户与门洞系统
    # 1F 临街客厅大推拉窗 (深度18cm，带铝合金内外滑轨窗框套与滴水窗台)
    build_recessed_window('House_A_1F_Front_Win', (-10.55, -2.8, hz_base + 1.8), width_y=2.2, height_z=1.6, depth_x=0.18, mats=mats, parent_col=col)
    
    # 2F 临街主卧推拉窗
    build_recessed_window('House_A_2F_Front_Win', (-10.95, -2.2, hz_base + 4.8), width_y=1.8, height_z=1.4, depth_x=0.18, mats=mats, parent_col=col)
    
    # 2F 通往阳台的推拉落地玻璃门
    build_recessed_window('House_A_2F_Balcony_Door', (-10.95, -5.25, hz_base + 4.6), width_y=2.4, height_z=2.1, depth_x=0.14, mats=mats, parent_col=col)
    
    # 1F 日式现代入户防盗大门与防雨门檐 (带金属把手)
    build_entrance_door('House_A_Main_Entrance', (-10.55, -7.5, hz_base + 1.2), mats=mats, parent_col=col)

    # 墙角垂直落水雨水管
    build_downspout('House_A_Downspout_Front', (-10.50, -0.15, hz_base + 6.3), height=5.5, mats=mats, parent_col=col)
    
    # 7. 侧方车位
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, -8.3, 2.75))
    cp_pad = bpy.context.active_object
    cp_pad.scale = (3.4, 4.8, 0.12)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cp_pad.data.materials.append(mats['concrete_curb'])
    col.objects.link(cp_pad)
    bpy.context.collection.objects.unlink(cp_pad)
    
    m_polycarb = create_custom_colored_material('M_PolycarbonateCanopy', (0.15, 0.18, 0.20, 0.85), roughness=0.15)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, -8.3, 5.1))
    canopy = bpy.context.active_object
    canopy.scale = (3.2, 4.6, 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(m_polycarb)
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    m_rubber = create_custom_colored_material('M_RubberWheelStop', (0.10, 0.10, 0.10, 1.0), roughness=0.85)
    for ws_x in [-9.5, -8.5]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ws_x, -10.2, 2.86))
        ws = bpy.context.active_object
        ws.scale = (0.18, 0.65, 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ws.data.materials.append(m_rubber)
        col.objects.link(ws)
        bpy.context.collection.objects.unlink(ws)
        
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.3, -2.0, 3.22))
    ac_body = bpy.context.active_object
    ac_body.name = 'House_A_AC_Unit'
    ac_body.scale = (0.35, 0.85, 0.64)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_body.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_body, width=0.02, segments=2)
    col.objects.link(ac_body)
    bpy.context.collection.objects.unlink(ac_body)
    
    return col

# ==============================================================================
# 房屋 C 与 3.5m 战术夹墙小巷
# ==============================================================================
def build_house_c_and_alleyway(mats):
    col = bpy.data.collections.new('03_House_C_And_Alleyway')
    bpy.context.scene.collection.children.link(col)
    
    hx = -14.25
    hy = 8.5
    hz_base = 0.8
    
    # 地基加深下延 (深埋入土)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base - 0.2))
    plinth = bpy.context.active_object
    plinth.scale = (7.6, 9.8, 1.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 1F 主体外墙 (北墙严格位于 Y = 3.5m，形成与 House_A 3.5m 夹墙小巷！)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 1.85))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = 'House_C_1F_Wall'
    bldg_1f.scale = (7.4, 9.6, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 4.7))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = 'House_C_2F_Wall'
    bldg_2f.scale = (7.4, 9.6, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    # 2.2m 院墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.4, 11.0, 1.10))
    fc_base = bpy.context.active_object
    fc_base.scale = (0.24, 4.8, 2.20)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fc_base.data.materials.append(mats['concrete_curb'])
    apply_bevel(fc_base, width=0.02, segments=2)
    col.objects.link(fc_base)
    bpy.context.collection.objects.unlink(fc_base)
    
    m_gate = create_custom_colored_material('M_IronGate', (0.16, 0.16, 0.17, 1.0), roughness=0.45, metallic=0.75)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.4, 7.2, 1.10))
    gate = bpy.context.active_object
    gate.name = 'House_C_Iron_Gate'
    gate.scale = (0.08, 1.15, 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    gate.data.materials.append(m_gate)
    col.objects.link(gate)
    bpy.context.collection.objects.unlink(gate)

    # 次世代 18cm 物理内嵌窗户
    build_recessed_window('House_C_1F_Front_Win', (-10.55, 9.5, hz_base + 1.8), width_y=1.8, height_z=1.4, depth_x=0.18, mats=mats, parent_col=col)
    build_recessed_window('House_C_2F_Front_Win', (-10.55, 8.5, hz_base + 4.8), width_y=2.2, height_z=1.5, depth_x=0.18, mats=mats, parent_col=col)
    # 小巷窗户 (在巷道墙面 Y = 3.7 上)
    build_recessed_window('House_C_Alley_Win', (-13.5, 3.7, hz_base + 2.0), width_y=1.2, height_z=1.0, depth_x=0.14, mats=mats, parent_col=col)
    # 落水管
    build_downspout('House_C_Downspout', (-10.50, 4.0, hz_base + 6.2), height=5.5, mats=mats, parent_col=col)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-12.5, 3.65, 2.4))
    ac_alley = bpy.context.active_object
    ac_alley.name = 'Alley_AC_Compressor'
    ac_alley.scale = (0.85, 0.35, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_alley.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_alley, width=0.02, segments=2)
    col.objects.link(ac_alley)
    bpy.context.collection.objects.unlink(ac_alley)

    return col

# ==============================================================================
# 房屋 B：街角 24H 便利店与次世代自动贩卖机 (No Plastic Blocks! Real PBR!)
# ==============================================================================
def build_house_b_convenience_store(mats):
    col = bpy.data.collections.new('04_House_B_Convenience_Store')
    bpy.context.scene.collection.children.link(col)
    
    bx = -13.25
    by = 21.5
    
    # 1. 建筑主体 (两层现代建筑)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.5, by, 1.85))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = 'Store_1F_Main_Wall'
    bldg_1f.scale = (8.4, 10.6, 3.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.5, by, 5.2))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = 'Store_2F_Wall'
    bldg_2f.scale = (8.4, 10.6, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    # 2. 门头发光灯箱招牌 (24H DAILY MART SIGNBOARD)
    m_store_sign = create_pbr_material('M_StoreSign', 'convenience_store_sign', fallback_color=(0.95, 0.95, 0.95, 1.0), roughness_val=0.15)
    sign_emis_path = find_texture('convenience_store_sign_emissive.png')
    if sign_emis_path:
        nodes = m_store_sign.node_tree.nodes
        links = m_store_sign.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        if bsdf:
            e_node = nodes.new('ShaderNodeTexImage')
            e_node.image = bpy.data.images.load(sign_emis_path)
            links.new(e_node.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 2.8
            
    # 招牌外壳
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.42, by, 3.85))
    sign_box = bpy.context.active_object
    sign_box.name = 'Store_Sign_Lightbox'
    sign_box.scale = (0.24, 9.8, 1.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sign_box.data.materials.append(mats['aluminum_dark'])
    apply_bevel(sign_box, width=0.02, segments=2)
    col.objects.link(sign_box)
    bpy.context.collection.objects.unlink(sign_box)
    
    # 招牌正面发光面片 (精准UV)
    sign_face = create_vertical_display_plane('Store_Sign_Face', (-8.29, by, 3.85), 9.76, 1.06, m_store_sign)
    col.objects.link(sign_face)
    
    # 3. 外挑折叠蓝白帆布遮阳篷
    m_store_awning = create_pbr_material('M_StoreAwning', 'convenience_store_awning', fallback_color=(0.12, 0.45, 0.78, 1.0), roughness_val=0.75)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.95, by, 3.15))
    awning = bpy.context.active_object
    awning.name = 'Store_Awning_Canopy'
    awning.scale = (1.10, 8.8, 0.08)
    awning.rotation_euler = (0, math.radians(18), 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    awning.data.materials.append(m_store_awning)
    col.objects.link(awning)
    bpy.context.collection.objects.unlink(awning)
    
    # 4. 落地通透双层玻璃幕墙
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.55, by, 1.75))
    glass_wall = bpy.context.active_object
    glass_wall.name = 'Store_Glass_Facade'
    glass_wall.scale = (0.05, 9.8, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    glass_wall.data.materials.append(mats['glass'])
    col.objects.link(glass_wall)
    bpy.context.collection.objects.unlink(glass_wall)
    
    # 5. 室内货架陈列排面 (发光立面，清晰透出落地窗)
    m_store_interior = create_emissive_material('M_StoreInteriorDisplay', strength=1.8, tex_name='convenience_store_interior_2k.png')
    in_display = create_vertical_display_plane('Store_Interior_Display', (-8.85, by, 1.75), 9.6, 2.7, m_store_interior)
    col.objects.link(in_display)

    # 6. 次世代自动贩卖机组合 (2x Vending Machines with Full 2K PBR)
    m_vm_pbr = bpy.data.materials.new(name='M_VendingMachine_PBR')
    m_vm_pbr.use_nodes = True
    vm_nodes = m_vm_pbr.node_tree.nodes
    vm_links = m_vm_pbr.node_tree.links
    vm_nodes.clear()
    
    out_vm = vm_nodes.new('ShaderNodeOutputMaterial')
    bsdf_vm = vm_nodes.new('ShaderNodeBsdfPrincipled')
    vm_links.new(bsdf_vm.outputs['BSDF'], out_vm.inputs['Surface'])
    
    vm_diff_p = find_texture('vending_machine_2k_diffuse.png')
    if vm_diff_p:
        t_diff = vm_nodes.new('ShaderNodeTexImage')
        t_diff.image = bpy.data.images.load(vm_diff_p)
        vm_links.new(t_diff.outputs['Color'], bsdf_vm.inputs['Base Color'])
        
    vm_emis_p = find_texture('vending_machine_2k_emissive.png')
    if vm_emis_p:
        t_emis = vm_nodes.new('ShaderNodeTexImage')
        t_emis.image = bpy.data.images.load(vm_emis_p)
        vm_links.new(t_emis.outputs['Color'], bsdf_vm.inputs['Emission Color'])
        bsdf_vm.inputs['Emission Strength'].default_value = 2.6
        
    vm_rgh_p = find_texture('vending_machine_2k_roughness.png')
    if vm_rgh_p:
        t_rgh = vm_nodes.new('ShaderNodeTexImage')
        t_rgh.image = bpy.data.images.load(vm_rgh_p)
        t_rgh.image.colorspace_settings.name = 'Non-Color'
        vm_links.new(t_rgh.outputs['Color'], bsdf_vm.inputs['Roughness'])
        
    vm_nrm_p = find_texture('vending_machine_2k_normal.png')
    if vm_nrm_p:
        t_nrm = vm_nodes.new('ShaderNodeTexImage')
        t_nrm.image = bpy.data.images.load(vm_nrm_p)
        t_nrm.image.colorspace_settings.name = 'Non-Color'
        n_map = vm_nodes.new('ShaderNodeNormalMap')
        n_map.inputs['Strength'].default_value = 1.6
        vm_links.new(t_nrm.outputs['Color'], n_map.inputs['Color'])
        vm_links.new(n_map.outputs['Normal'], bsdf_vm.inputs['Normal'])

    # 放置 2 台精细自动贩卖机
    for vm_idx, vm_y in enumerate([17.5, 19.0]):
        # 金属机身主体 (深色冷轧板)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.8, vm_y, 1.08))
        vm = bpy.context.active_object
        vm.name = f'Photoreal_Vending_Machine_{vm_idx}'
        vm.scale = (0.75, 0.95, 1.85)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        vm.data.materials.append(mats['aluminum_dark'])
        apply_bevel(vm, width=0.015, segments=2)
        col.objects.link(vm)
        bpy.context.collection.objects.unlink(vm)
        
        # 精准UV立面印刷面板 (16款冷热饮料、LED按键、投币口、出货口)
        vm_front = create_vertical_display_plane(f'Vending_Front_Panel_{vm_idx}', (-7.41, vm_y, 1.08), 0.94, 1.84, m_vm_pbr)
        col.objects.link(vm_front)
        
        # 透明亚克力展示护罩
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.38, vm_y, 1.40))
        glass_cover = bpy.context.active_object
        glass_cover.name = f'Vending_Glass_Shield_{vm_idx}'
        glass_cover.scale = (0.02, 0.88, 0.92)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        glass_cover.data.materials.append(mats['glass'])
        col.objects.link(glass_cover)
        bpy.context.collection.objects.unlink(glass_cover)

    # 顶部金属防倾倒固定拉杆
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=1.6, location=(-7.8, 18.25, 2.05))
    brace = bpy.context.active_object
    brace.rotation_euler = (math.radians(90), 0, 0)
    brace.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(brace)
    bpy.context.collection.objects.unlink(brace)

    return col

# ==============================================================================
# 街道市政小物件生态 (Street Props Ecosystem)
# ==============================================================================
def build_street_props_kit(mats):
    col = bpy.data.collections.new('05_Street_Props_Kit')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 日本市政分类塑料垃圾桶 (蓝/绿/灰) 绑定真实日本分类标贴
    m_bin_props = create_pbr_material('M_MunicipalTrashBins', 'municipal_props_atlas', fallback_color=(0.3, 0.35, 0.4, 1.0), roughness_val=0.45)
    for b_idx, (by_pos, b_color) in enumerate([
        (16.0, (0.10, 0.40, 0.85, 1.0)),
        (16.6, (0.15, 0.58, 0.25, 1.0)),
        (17.2, (0.28, 0.30, 0.35, 1.0)),
    ]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.2, by_pos, 0.52))
        bin_body = bpy.context.active_object
        bin_body.name = f'Japanese_Trash_Bin_{b_idx}'
        bin_body.scale = (0.42, 0.52, 0.92)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bin_body.data.materials.append(m_bin_props)
        apply_bevel(bin_body, width=0.02, segments=2)
        col.objects.link(bin_body)
        bpy.context.collection.objects.unlink(bin_body)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.2, by_pos, 1.02))
        lid = bpy.context.active_object
        lid.scale = (0.45, 0.55, 0.08)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        lid.data.materials.append(m_bin_props)
        col.objects.link(lid)
        bpy.context.collection.objects.unlink(lid)
        
    # 2. 施工与安全反光路锥
    m_cone_orange = create_custom_colored_material('M_ConeOrange', (0.95, 0.32, 0.04, 1.0), roughness=0.35)
    m_cone_refl = create_custom_colored_material('M_ConeReflective', (0.95, 0.95, 0.95, 1.0), roughness=0.15, metallic=0.2)
    m_cone_base = create_custom_colored_material('M_ConeBlackBase', (0.12, 0.12, 0.13, 1.0), roughness=0.85)
    
    for c_i, (c_x, c_y) in enumerate([(-3.8, 11.5), (-3.8, 13.0), (-3.8, -1.5)]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(c_x, c_y, 0.02))
        cbase = bpy.context.active_object
        cbase.scale = (0.40, 0.40, 0.04)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        cbase.data.materials.append(m_cone_base)
        col.objects.link(cbase)
        bpy.context.collection.objects.unlink(cbase)
        
        bpy.ops.mesh.primitive_cone_add(radius1=0.16, radius2=0.025, depth=0.70, location=(c_x, c_y, 0.38))
        cone_obj = bpy.context.active_object
        cone_obj.data.materials.append(m_cone_orange)
        bpy.ops.object.shade_smooth()
        col.objects.link(cone_obj)
        bpy.context.collection.objects.unlink(cone_obj)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.105, depth=0.15, location=(c_x, c_y, 0.42))
        band = bpy.context.active_object
        band.data.materials.append(m_cone_refl)
        bpy.ops.object.shade_smooth()
        col.objects.link(band)
        bpy.context.collection.objects.unlink(band)

    # 3. 转角道路凸面广角镜
    m_mirror_yellow = create_custom_colored_material('M_MirrorYellow', (0.95, 0.75, 0.05, 1.0), roughness=0.35)
    m_chrome = create_custom_colored_material('M_ChromeMirror', (0.95, 0.95, 0.98, 1.0), roughness=0.02, metallic=0.98)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3.6, location=(-3.9, 9.5, 1.8))
    m_pole = bpy.context.active_object
    m_pole.data.materials.append(m_mirror_yellow)
    bpy.ops.object.shade_smooth()
    col.objects.link(m_pole)
    bpy.context.collection.objects.unlink(m_pole)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.10, location=(-3.9, 9.5, 3.4))
    m_body = bpy.context.active_object
    m_body.rotation_euler = (0, math.radians(75), math.radians(25))
    m_body.data.materials.append(m_mirror_yellow)
    bpy.ops.object.shade_smooth()
    col.objects.link(m_body)
    bpy.context.collection.objects.unlink(m_body)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.02, location=(-3.88, 9.48, 3.4))
    m_lens = bpy.context.active_object
    m_lens.rotation_euler = (0, math.radians(75), math.radians(25))
    m_lens.data.materials.append(m_chrome)
    bpy.ops.object.shade_smooth()
    col.objects.link(m_lens)
    bpy.context.collection.objects.unlink(m_lens)
    
    # 4. 地上消火栓
    m_hydrant_red = create_custom_colored_material('M_FireHydrantRed', (0.85, 0.10, 0.08, 1.0), roughness=0.42, metallic=0.60)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.85, location=(-4.0, 14.5, 0.45))
    hyd = bpy.context.active_object
    hyd.data.materials.append(m_hydrant_red)
    bpy.ops.object.shade_smooth()
    apply_bevel(hyd, width=0.015, segments=2)
    col.objects.link(hyd)
    bpy.context.collection.objects.unlink(hyd)
    
    # 5. 电线杆、变压器与电缆
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=9.5, location=(-3.8, -4.0, 4.75))
    pole = bpy.context.active_object
    pole.data.materials.append(mats['utility_pole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(pole)
    bpy.context.collection.objects.unlink(pole)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.28, depth=0.90, location=(-3.8, -4.0, 7.2))
    trans = bpy.context.active_object
    trans.data.materials.append(mats['transformer'])
    bpy.ops.object.shade_smooth()
    col.objects.link(trans)
    bpy.context.collection.objects.unlink(trans)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.8, -4.0, 8.2))
    crossarm = bpy.context.active_object
    crossarm.scale = (0.12, 1.80, 0.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    crossarm.data.materials.append(mats['aluminum_silver'])
    col.objects.link(crossarm)
    bpy.context.collection.objects.unlink(crossarm)
    
    def build_catenary(name, p_start, p_end, sag=0.28, radius=0.008):
        curve_data = bpy.data.curves.new(name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = radius
        curve_data.bevel_resolution = 3
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(1)
        p0 = spline.bezier_points[0]
        p1 = spline.bezier_points[1]
        p0.co = p_start
        p1.co = p_end
        p0.handle_right = (p_start[0], (p_start[1] + p_end[1])*0.5, p_start[2] - sag)
        p1.handle_left  = (p_end[0],   (p_start[1] + p_end[1])*0.5, p_end[2] - sag)
        p0.handle_left  = p_start
        p1.handle_right = p_end
        c_obj = bpy.data.objects.new(name, curve_data)
        c_obj.data.materials.append(mats['cable_rubber'])
        return c_obj
        
    cable1 = build_catenary('Cable_Street_Main_1', (-3.8, -32.0, 8.5), (-3.8, -4.0, 8.2), sag=0.45)
    col.objects.link(cable1)
    cable2 = build_catenary('Cable_Street_Main_2', (-3.8, -4.0, 8.2), (-3.8, 25.0, 8.0), sag=0.55)
    col.objects.link(cable2)
    
    return col

# ==============================================================================
# 物理天空与机位配置
# ==============================================================================
def setup_lighting():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new('World_Nishita')
        bpy.context.scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_links = world.node_tree.links
    w_nodes.clear()
    
    w_out = w_nodes.new('ShaderNodeOutputWorld')
    sky_node = w_nodes.new('ShaderNodeTexSky')
    sky_node.sky_type = 'MULTIPLE_SCATTERING'
    sky_node.sun_elevation = math.radians(34.0)
    sky_node.sun_rotation = math.radians(45.0)
    sky_node.altitude = 10.0
    sky_node.air_density = 1.0
    sky_node.aerosol_density = 1.0
    sky_node.ozone_density = 1.0
    sky_node.sun_intensity = 0.0
    
    bg = w_nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.45
    w_links.new(sky_node.outputs['Color'], bg.inputs['Color'])
    w_links.new(bg.outputs['Background'], w_out.inputs['Surface'])
    
    sun_data = bpy.data.lights.new(name='SunLight_Key', type='SUN')
    sun_data.energy = 1.35
    sun_data.color = (1.0, 0.98, 0.94)
    sun_data.angle = math.radians(0.8)
    
    sun_obj = bpy.data.objects.new(name='SunLight_Key', object_data=sun_data)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(10.0), math.radians(45.0))
    bpy.context.scene.collection.objects.link(sun_obj)

def create_targeted_camera(name, location, target_pos, lens=28.0):
    c_data = bpy.data.cameras.new(name)
    c_data.lens = lens
    c_data.clip_start = 0.1
    c_data.clip_end = 500.0
    c_obj = bpy.data.objects.new(name, c_data)
    c_obj.location = location
    direction = mathutils.Vector(target_pos) - mathutils.Vector(location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    c_obj.rotation_euler = rot_quat.to_euler()
    bpy.context.scene.collection.objects.link(c_obj)
    return c_obj

def setup_inspection_cameras():
    cameras = {}
    
    # 1. 街区全景鸟瞰机位 (俯视长坡道、西侧民宅群、轻轨高架桥与商厦背景，消除黑虚空)
    c1_obj = create_targeted_camera(
        'Cam_01_Panorama',
        location=(5.0, -31.0, 12.5),
        target_pos=(-2.0, 8.0, 1.5),
        lens=26.0
    )
    cameras['01_neighborhood_district_panorama'] = c1_obj
    
    # 2. 住宅 A 阳台与车位特写 (仰视拍摄挑檐阳台磨砂玻璃扶手与车库雨棚)
    c2_obj = create_targeted_camera(
        'Cam_02_HouseA',
        location=(-3.2, -10.5, 3.2),
        target_pos=(-9.2, -6.5, 4.0),
        lens=30.0
    )
    cameras['02_house_a_balcony_carport'] = c2_obj
    
    # 3. 便利店与自动贩卖机特写 (对标 ZZZ 光映广场，近景拍摄两台自动贩卖机与 24H 门脸货架)
    c3_obj = create_targeted_camera(
        'Cam_03_ConvenienceStore',
        location=(-3.2, 16.8, 1.45),
        target_pos=(-7.8, 19.2, 1.60),
        lens=28.0
    )
    cameras['03_house_b_convenience_store_vending'] = c3_obj
    
    # 4. 3.5m 战术小巷 (贯穿 House A 与 House C 之间的战术通道与跳墙点)
    c4_obj = create_targeted_camera(
        'Cam_04_Alley',
        location=(-5.2, 1.85, 2.0),
        target_pos=(-14.0, 1.85, 2.2),
        lens=24.0
    )
    cameras['04_house_c_slope_alley_wall_bounce'] = c4_obj
    
    # 5. 市政小物件套件 (近焦拍摄黄色广角凸面镜、反光路锥、消火栓与分类垃圾桶)
    c5_obj = create_targeted_camera(
        'Cam_05_Props',
        location=(-1.8, 8.5, 1.5),
        target_pos=(-4.0, 13.0, 1.1),
        lens=32.0
    )
    cameras['05_street_props_kit_closeup'] = c5_obj
    
    return cameras

def configure_render_engine(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium Contrast'
    scene.view_settings.exposure = -0.4
    
    prefs = bpy.context.preferences
    cycles_prefs = prefs.addons['cycles'].preferences
    for compute_type in ['OPTIX', 'CUDA']:
        try:
            cycles_prefs.compute_device_type = compute_type
            cycles_prefs.get_devices()
            for device in cycles_prefs.devices:
                device.use = True
            print(f'Cycles GPU initialized with: {compute_type}')
            break
        except:
            pass

def main():
    print('======================================================================')
    print('★ Asternova M1/M2 CS2 & ZZZ 级次世代街区全封闭终极构建启动 ★')
    print('======================================================================')
    clean_scene()
    
    mats = {
        'wall_plaster': create_pbr_material('M_WallPlaster', 'wall_plaster', fallback_color=(0.80, 0.79, 0.76, 1.0), roughness_val=0.82, uv_scale=(4.0, 4.0), normal_strength=1.8),
        'asphalt_road': create_pbr_material('M_AsphaltRoad', 'asphalt_road', fallback_color=(0.16, 0.16, 0.17, 1.0), roughness_val=0.88, uv_scale=(1.0, 4.0), normal_strength=2.2),
        'sidewalk_tiles': create_pbr_material('M_SidewalkTiles', 'sidewalk_tiles', fallback_color=(0.65, 0.66, 0.68, 1.0), roughness_val=0.68, uv_scale=(3.0, 6.0), normal_strength=1.6),
        'tactile_paving': create_pbr_material('M_TactilePaving', 'tactile_paving', fallback_color=(0.94, 0.72, 0.05, 1.0), roughness_val=0.52, uv_scale=(1.0, 12.0), normal_strength=2.2),
        'concrete_curb': create_pbr_material('M_ConcreteCurb', 'concrete_curb', fallback_color=(0.58, 0.59, 0.60, 1.0), roughness_val=0.72, uv_scale=(1.0, 6.0), normal_strength=1.3),
        'metal_manhole': create_pbr_material('M_MetalManhole', 'metal_manhole', fallback_color=(0.16, 0.17, 0.18, 1.0), roughness_val=0.45, metallic_val=0.85, uv_scale=(1.0, 1.0), normal_strength=2.4),
        'props_ac_meter': create_pbr_material('M_PropsACMeter', 'props_ac_meter', fallback_color=(0.86, 0.87, 0.88, 1.0), roughness_val=0.42, uv_scale=(1.0, 1.0), normal_strength=1.5),
        'utility_pole': create_pbr_material('M_UtilityPole', 'utility_pole', fallback_color=(0.61, 0.62, 0.63, 1.0), roughness_val=0.78, uv_scale=(1.0, 4.0), normal_strength=1.3),
        'transformer': create_pbr_material('M_Transformer', 'props_ac_meter', fallback_color=(0.35, 0.38, 0.40, 1.0), roughness_val=0.65, metallic_val=0.70),
        'glass': create_glass_material('M_Glass'),
        'aluminum_dark': create_custom_colored_material('M_Aluminum_Dark', (0.12, 0.13, 0.14, 1.0), roughness=0.32, metallic=0.88),
        'aluminum_silver': create_custom_colored_material('M_Aluminum_Silver', (0.65, 0.68, 0.70, 1.0), roughness=0.32, metallic=0.88),
        'cable_rubber': create_custom_colored_material('M_CableRubber', (0.08, 0.08, 0.09, 1.0), roughness=0.65)
    }
    
    print('1. Building Environment Backdrop (Eliminate Black Void)...')
    build_environment_backdrop(mats)
    
    print('2. Building Sloped Roadway & Pavements...')
    build_terrain_and_roads(mats)
    
    print('3. Building House_A with Balcony & Carport...')
    build_house_a(mats)
    
    print('4. Building House_C & Tactical Wall-Bounce Alley...')
    build_house_c_and_alleyway(mats)
    
    print('5. Building House_B 24H Store with Real PBR Vending Machines & Signboard...')
    build_house_b_convenience_store(mats)
    
    print('6. Building Street Props Ecosystem (Trash Bins, Cones, Mirrors, Hydrants)...')
    build_street_props_kit(mats)
    
    setup_lighting()
    cameras = setup_inspection_cameras()
    scene = bpy.context.scene
    configure_render_engine(scene)
    
    games_root = r'c:\Users\TimeCraker\Desktop\my-workspace\games'
    asternova_root = os.path.join(games_root, 'asternova')
    
    blend_paths = [
        os.path.join(asternova_root, 'art', 'models', 'neighborhood', 'modern_japan_neighborhood.blend'),
        os.path.join(games_root, 'art', 'models', 'neighborhood', 'modern_japan_neighborhood.blend')
    ]
    for bp in blend_paths:
        ensure_dir(os.path.dirname(bp))
        bpy.ops.wm.save_as_mainfile(filepath=bp)
        print(f'Saved .blend: {bp}')
        
    glb_export_targets = [
        os.path.join(asternova_root, 'client-godot-v2', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(games_root, 'client-godot-v2', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(asternova_root, 'render-lab', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(games_root, 'render-lab', 'models', 'environment', 'modern_japan_neighborhood.glb')
    ]
    for gp in glb_export_targets:
        ensure_dir(os.path.dirname(gp))
        bpy.ops.export_scene.gltf(filepath=gp, export_format='GLB', export_materials='EXPORT', export_cameras=False)
        print(f'Exported High-Precision GLB: {gp}')
        
    screenshot_dirs = [
        os.path.join(asternova_root, 'render-lab', 'screenshots', 'modular_kit'),
        os.path.join(games_root, 'render-lab', 'screenshots', 'modular_kit')
    ]
    for d in screenshot_dirs:
        ensure_dir(d)
        
    print("--- Rendering 5 Next-Gen Inspection Views (2560x1440 2K) ---")
    import shutil
    shot_filter = os.environ.get('SHOT_FILTER', None)
    for shot_name, cam_obj in cameras.items():
        if shot_filter and shot_filter not in shot_name:
            continue
        print(f"Rendering View: {shot_name}...")
        scene.camera = cam_obj
        out_f1 = os.path.join(screenshot_dirs[0], f"{shot_name}.png")
        scene.render.filepath = out_f1
        bpy.ops.render.render(write_still=True)
        print(f"Rendered: {out_f1}")
        
        out_f2 = os.path.join(screenshot_dirs[1], f"{shot_name}.png")
        shutil.copy2(out_f1, out_f2)
        print(f"Mirrored: {out_f2}")
        
    print("======================================================================")
    print("★ Next-Gen Rebuild & Cycles 2K Rendering Completed Successfully! ★")
    print("======================================================================")

if __name__ == '__main__':
    main()
