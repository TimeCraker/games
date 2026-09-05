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
    # 使用立方体投影，cube_size 匹配米制贴图密度
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

# ==============================================================================
# 标准 glTF 兼容 PBR 材质创建器
# ==============================================================================
def create_gltf_pbr_material(name, albedo_file, normal_file=None, roughness_file=None, emissive_file=None, 
                             fallback_color=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, normal_strength=1.5,
                             emissive_strength=1.2):
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
    
    # 1. Albedo
    if albedo_file:
        alb_p = find_tex(albedo_file)
        if alb_p:
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = bpy.data.images.load(alb_p)
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            
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

def create_vertical_display_plane(name, center_pos, width_y, height_z, material):
    mesh = bpy.data.meshes.new(name + '_Mesh')
    obj = bpy.data.objects.new(name, mesh)
    hy = width_y / 2.0
    hz = height_z / 2.0
    cx, cy, cz = center_pos
    # 严格确保法线指向 +X（朝向街道相机，绝不背面镜像）
    verts = [
        (cx, cy + hy, cz - hz),  # 0: (+Y, -Z)
        (cx, cy + hy, cz + hz),  # 1: (+Y, +Z)
        (cx, cy - hy, cz + hz),  # 2: (-Y, +Z)
        (cx, cy - hy, cz - hz)   # 3: (-Y, -Z)
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    # 相机面朝 -X 看向物体：左侧是 +Y（对应贴图左侧 U=0.0），右侧是 -Y（对应贴图右侧 U=1.0）
    uvs = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    for loop_idx, loop in enumerate(mesh.loops):
        uv_layer.data[loop_idx].uv = uvs[loop_idx]
    obj.data.materials.append(material)
    return obj

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
    bsdf.inputs['Base Color'].default_value = (0.85, 0.92, 0.98, 1.0)
    bsdf.inputs['Alpha'].default_value = 0.15
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['Metallic'].default_value = 0.1
    return mat

def create_colored_metal(name, color, roughness=0.35, metallic=0.85):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

# ==============================================================================
# 构建全封闭 360° 天际线与宏观街区 (消除黑虚空与纯白方柱)
# ==============================================================================
def build_environment_backdrop(mats):
    col = bpy.data.collections.new('00_Environment_Backdrop')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 宏观连续地基 (160m x 160m)，确保任何边缘绝不漏黑
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, -0.05))
    ground = bpy.context.active_object
    ground.name = 'Macro_District_Ground'
    ground.scale = (160.0, 160.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(ground, uv_scale=0.5)
    ground.data.materials.append(mats['asphalt_road'])
    col.objects.link(ground)
    bpy.context.collection.objects.unlink(ground)
    
    # 2. 北侧台地护坡与山顶神社神社鸟居 (Y: -30 to -65)
    for layer_i, ly in enumerate([-32.0, -42.0, -52.0]):
        lz = 6.0 + layer_i * 3.5
        # 清水混凝土挡土墙
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
        
        # 山坡日式住宅一户建群 (贴日式米白挂板与和瓦屋顶)
        for hx in [-20.0, 0.0, 20.0]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.5, lz + 5.0))
            nh = bpy.context.active_object
            nh.name = f'North_Hill_House_{layer_i}_{hx}'
            nh.scale = (12.0, 7.5, 6.5)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            apply_box_uv(nh, uv_scale=1.0)
            nh.data.materials.append(mats['japanese_siding'])
            apply_bevel(nh, width=0.05, segments=2)
            col.objects.link(nh)
            bpy.context.collection.objects.unlink(nh)
            
            # 日式和瓦人字挑檐屋顶
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, ly - 4.5, lz + 8.5))
            nr = bpy.context.active_object
            nr.scale = (13.0, 8.5, 0.6)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            apply_box_uv(nr, uv_scale=1.5)
            nr.data.materials.append(mats['japanese_roof'])
            col.objects.link(nr)
            bpy.context.collection.objects.unlink(nr)

    # 北侧山顶神社大鸟居 (朱红漆木，山顶标志地标，对标原画)
    torii_y = -27.5
    torii_z = 6.2
    for px in [-2.5, 2.5]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=4.2, location=(px, torii_y, torii_z + 2.1))
        t_col = bpy.context.active_object
        t_col.data.materials.append(mats['torii_red'])
        bpy.ops.object.shade_smooth()
        col.objects.link(t_col)
        bpy.context.collection.objects.unlink(t_col)
        
    # 鸟居横梁 (笠木与贯)
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

    # 3. 南侧现代轻轨高架桥与商业立面 (阻断南向视线，对标 ZZZ 参考图 12)
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
    
    # 轻轨黄色列车车厢 (标志性日式轻轨)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, 42.0, 10.2))
    train = bpy.context.active_object
    train.name = 'Monorail_Train'
    train.scale = (22.0, 3.2, 3.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    train.data.materials.append(mats['train_yellow'])
    apply_bevel(train, width=0.1, segments=2)
    col.objects.link(train)
    bpy.context.collection.objects.unlink(train)
    
    # 桥墩
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

    # 4. 南侧商业写字楼群 (贴有整齐阳台窗户贴图，杜绝白石碑)
    for bx, bw, bh in [(-28.0, 20.0, 24.0), (0.0, 24.0, 28.0), (28.0, 20.0, 22.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, 54.0, bh / 2.0))
        tower = bpy.context.active_object
        tower.name = f'South_Tower_{bx}'
        tower.scale = (bw, 14.0, bh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(tower, uv_scale=1.0)
        tower.data.materials.append(mats['city_mansion'])
        apply_bevel(tower, width=0.05, segments=2)
        col.objects.link(tower)
        bpy.context.collection.objects.unlink(tower)

    # 5. 西侧日式公寓楼群 (West Skyline, X = -28.0，彻底阻断西向虚空)
    for wy, wh, ww in [(-18.0, 20.0, 14.0), (2.0, 24.0, 16.0), (22.0, 21.0, 14.0)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-28.0, wy, wh / 2.0))
        mansion = bpy.context.active_object
        mansion.name = f'West_Mansion_{wy}'
        mansion.scale = (14.0, ww, wh)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        apply_box_uv(mansion, uv_scale=1.0)
        mansion.data.materials.append(mats['city_mansion'])
        apply_bevel(mansion, width=0.05, segments=2)
        col.objects.link(mansion)
        bpy.context.collection.objects.unlink(mansion)

    # 6. 东侧高台住宅群与挡墙 (X = +10.0 to +30.0，彻底阻断东向虚空)
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
        e_house.data.materials.append(mats['city_mansion'])
        col.objects.link(e_house)
        bpy.context.collection.objects.unlink(e_house)

    return col

# ==============================================================================
# 道路、40m 战术跑酷长坡与人行道系统
# ==============================================================================
def build_terrain_and_roads(mats):
    col = bpy.data.collections.new('01_Roads_And_Terrain')
    bpy.context.scene.collection.children.link(col)
    
    slope_angle = math.atan2(-6.0, 35.0) # 约 9.8 度平缓顺接
    
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
    
    # 2. 南端生活广场西侧人行道 (带花岗岩大砖铺装)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, 23.0, 0.075))
    plz_sw_w = bpy.context.active_object
    plz_sw_w.name = 'Sidewalk_Plaza_West'
    plz_sw_w.scale = (10.0, 26.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(plz_sw_w, uv_scale=1.0)
    plz_sw_w.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_w)
    bpy.context.collection.objects.unlink(plz_sw_w)
    
    # 3. 路缘石 (带倒角法线)
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
    
    # 4. 黄色导盲道
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-4.8, 23.0, 0.152))
    plz_tac = bpy.context.active_object
    plz_tac.name = 'Tactile_Plaza_West'
    plz_tac.scale = (0.6, 26.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(plz_tac, uv_scale=2.0)
    plz_tac.data.materials.append(mats['tactile_paving'])
    col.objects.link(plz_tac)
    bpy.context.collection.objects.unlink(plz_tac)
    
    # 5. 40m 战术跑酷坡道 (Central Long Ramp, Y: +10.0 to -25.0)
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
    # 扶手横杆
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.6, -7.5, 3.95))
    rail_h = bpy.context.active_object
    rail_h.scale = (0.05, 35.5, 0.05)
    rail_h.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rail_h.data.materials.append(mats['aluminum_silver'])
    col.objects.link(rail_h)
    bpy.context.collection.objects.unlink(rail_h)

    # 坡道东侧垂直挡土墙 (消除坡道东侧悬空裂隙)
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

    # 坡道西侧垂直挡土墙 (消除西侧人行道与住宅区标高差裂隙)
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

    # 西侧住宅区水平平整地基地面 (Z: 0.0m 水平展开，绝不上翘遮挡天空)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-13.0, -7.5, 0.0))
    west_flat_ground = bpy.context.active_object
    west_flat_ground.name = 'West_Residential_Foundation'
    west_flat_ground.scale = (14.0, 40.0, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(west_flat_ground, uv_scale=1.0)
    west_flat_ground.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(west_flat_ground)
    bpy.context.collection.objects.unlink(west_flat_ground)

    # 6. 北侧山顶高台广场 (Y: -25.0 to -35.0, Z: 6.0m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -30.0, 5.9))
    n_plat = bpy.context.active_object
    n_plat.name = 'North_Terrace_Plaza'
    n_plat.scale = (28.0, 12.0, 0.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(n_plat, uv_scale=1.0)
    n_plat.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(n_plat)
    bpy.context.collection.objects.unlink(n_plat)

    # 北侧高台实心挡土墙基座 (彻底消除鸟居下方任何透光虚空)
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
# 核心建筑 A：日式现代民宅 (米白挂板、和瓦屋檐、4.5m 阳台与车库)
# ==============================================================================
def build_house_a(mats):
    col = bpy.data.collections.new('02_House_A')
    bpy.context.scene.collection.children.link(col)
    
    bx, by, bz = -14.25, -5.5, 3.5
    # 主建筑体 (带米白挂板, Y 覆盖: -9.25 到 -1.75, 长度 7.5m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bz))
    body = bpy.context.active_object
    body.name = 'HouseA_MainBody'
    body.scale = (7.5, 7.5, 7.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(body, uv_scale=1.0)
    body.data.materials.append(mats['japanese_siding'])
    apply_bevel(body, width=0.04, segments=2)
    col.objects.link(body)
    bpy.context.collection.objects.unlink(body)
    
    # 墨灰波纹和瓦屋顶 (挑出 0.5m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bz + 3.7))
    roof = bpy.context.active_object
    roof.name = 'HouseA_Roof'
    roof.scale = (8.5, 8.5, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(roof, uv_scale=1.5)
    roof.data.materials.append(mats['japanese_roof'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 二楼 4.5m 跑酷战术阳台 (X: -9.7, Y: -5.5, Z: 4.5)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.7, -5.5, 2.25))
    balc_slab = bpy.context.active_object
    balc_slab.name = 'HouseA_BalconySlab'
    balc_slab.scale = (1.6, 4.6, 4.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(balc_slab, uv_scale=1.0)
    balc_slab.data.materials.append(mats['japanese_tile'])
    apply_bevel(balc_slab, width=0.03, segments=2)
    col.objects.link(balc_slab)
    bpy.context.collection.objects.unlink(balc_slab)
    
    # 阳台深色铝合金护栏 (Z: 4.5 to 5.5)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.95, -5.5, 5.0))
    balc_rail = bpy.context.active_object
    balc_rail.scale = (0.08, 4.5, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc_rail.data.materials.append(mats['aluminum_dark'])
    col.objects.link(balc_rail)
    bpy.context.collection.objects.unlink(balc_rail)
    
    # 落地玻璃推拉门 (内嵌于阳台后方)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.45, -5.5, 5.2))
    glass_door = bpy.context.active_object
    glass_door.scale = (0.1, 3.2, 2.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    glass_door.data.materials.append(mats['glass'])
    col.objects.link(glass_door)
    bpy.context.collection.objects.unlink(glass_door)
    
    # 一楼车库半透明遮阳雨棚 (Carport)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.8, -1.2, 2.6))
    canopy = bpy.context.active_object
    canopy.scale = (3.4, 4.0, 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(mats['glass'])
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    # 空调外机 (挂于阳台下方)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.2, -8.5, 1.8))
    ac = bpy.context.active_object
    ac.scale = (0.5, 0.9, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac.data.materials.append(mats['aluminum_silver'])
    apply_bevel(ac, width=0.02, segments=2)
    col.objects.link(ac)
    bpy.context.collection.objects.unlink(ac)

    return col

# ==============================================================================
# 核心建筑 B：24H 便利店与写实双联自动贩卖机 (绝区零级生活气息)
# ==============================================================================
def build_house_b_convenience_store(mats):
    col = bpy.data.collections.new('03_House_B_Convenience_Store')
    bpy.context.scene.collection.children.link(col)
    
    bx, by = -14.25, 19.5
    # 主体商铺二楼及上部门楣墙体 (Z: 2.7 to 7.0, 高度 4.3m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 4.85))
    store_upper = bpy.context.active_object
    store_upper.name = 'Store_UpperFacade'
    store_upper.scale = (8.6, 11.0, 4.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_upper, uv_scale=1.0)
    store_upper.data.materials.append(mats['japanese_tile'])
    apply_bevel(store_upper, width=0.04, segments=2)
    col.objects.link(store_upper)
    bpy.context.collection.objects.unlink(store_upper)

    # 一楼后墙 (X: -18.1)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-18.1, by, 1.35))
    store_back = bpy.context.active_object
    store_back.name = 'Store_BackWall'
    store_back.scale = (0.9, 11.0, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_back, uv_scale=1.0)
    store_back.data.materials.append(mats['japanese_tile'])
    col.objects.link(store_back)
    bpy.context.collection.objects.unlink(store_back)

    # 一楼北侧山墙 (Y: 14.2)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, 14.2, 1.35))
    store_side_n = bpy.context.active_object
    store_side_n.name = 'Store_SideWall_N'
    store_side_n.scale = (8.6, 0.8, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_side_n, uv_scale=1.0)
    store_side_n.data.materials.append(mats['japanese_tile'])
    col.objects.link(store_side_n)
    bpy.context.collection.objects.unlink(store_side_n)

    # 一楼南侧山墙 (Y: 24.8)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, 24.8, 1.35))
    store_side_s = bpy.context.active_object
    store_side_s.name = 'Store_SideWall_S'
    store_side_s.scale = (8.6, 0.8, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_side_s, uv_scale=1.0)
    store_side_s.data.materials.append(mats['japanese_tile'])
    col.objects.link(store_side_s)
    bpy.context.collection.objects.unlink(store_side_s)

    # 一楼室内地面
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.05))
    store_floor = bpy.context.active_object
    store_floor.name = 'Store_InteriorFloor'
    store_floor.scale = (8.6, 11.0, 0.1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(store_floor, uv_scale=1.0)
    store_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(store_floor)
    bpy.context.collection.objects.unlink(store_floor)
    
    # 门头 24H 真实发光灯箱招牌 (面朝街道相机，精准 UV 展开)
    sign_face = create_vertical_display_plane('ConvenienceStore_Sign_Face', (-9.72, 19.5, 3.4), 9.2, 1.1, mats['store_sign'])
    col.objects.link(sign_face)
    
    # 招牌外框深色铝合金
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.85, 19.5, 3.4))
    sign_frame = bpy.context.active_object
    sign_frame.name = 'ConvenienceStore_Sign_Frame'
    sign_frame.scale = (0.24, 9.35, 1.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sign_frame.data.materials.append(mats['aluminum_dark'])
    col.objects.link(sign_frame)
    bpy.context.collection.objects.unlink(sign_frame)
    
    # 落地大玻璃窗 (X: -9.88, Y: 19.5, Z: 1.35)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.88, 19.5, 1.35))
    store_glass = bpy.context.active_object
    store_glass.name = 'Store_Glass'
    store_glass.scale = (0.05, 8.8, 2.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    store_glass.data.materials.append(mats['glass'])
    col.objects.link(store_glass)
    bpy.context.collection.objects.unlink(store_glass)
    
    # 玻璃窗后 1.1m 处内嵌写实商品货架 (高清陈列，面朝街道，室内明亮通透)
    shelf_face = create_vertical_display_plane('Store_Shelves_Display', (-11.0, 19.5, 1.35), 8.6, 2.4, mats['store_shelves'])
    col.objects.link(shelf_face)
    
    # 街角写实双联自动贩卖机 (深色机身 + 正确朝向街道的 2K PBR 印刷面 + 亚克力保护屏)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.45, 23.5, 1.05))
    vm_body = bpy.context.active_object
    vm_body.name = 'Vending_Machines_Body'
    vm_body.scale = (0.85, 2.4, 1.95)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    vm_body.data.materials.append(mats['aluminum_dark'])
    apply_bevel(vm_body, width=0.02, segments=2)
    col.objects.link(vm_body)
    bpy.context.collection.objects.unlink(vm_body)
    
    # 贩卖机正面 2K PBR 印刷面 (指向 +X，绝区零级红蓝双机写实细节)
    vm_face = create_vertical_display_plane('Vending_Machines_Front_Panel', (-9.01, 23.5, 1.05), 2.38, 1.92, mats['vending_machine'])
    col.objects.link(vm_face)
    
    # 贩卖机亚克力展示护罩
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.99, 23.5, 1.45))
    vm_glass = bpy.context.active_object
    vm_glass.name = 'Vending_Glass_Shield'
    vm_glass.scale = (0.02, 2.3, 0.92)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    vm_glass.data.materials.append(mats['glass'])
    col.objects.link(vm_glass)
    bpy.context.collection.objects.unlink(vm_glass)

    return col

# ==============================================================================
# 核心建筑 C 与 3.5m 战术夹墙小巷 (Wall Bounce Alleyway)
# ==============================================================================
def build_house_c_and_alleyway(mats):
    col = bpy.data.collections.new('04_House_C_And_Alleyway')
    bpy.context.scene.collection.children.link(col)
    
    # 住宅 C 位于住宅 A 南侧，相距恰好 3.5m (战术蹬墙跳小巷通道：Y 从 -1.75 到 +1.75，宽 3.5m)
    bx, by, bz = -14.25, 5.5, 3.5
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bz))
    body = bpy.context.active_object
    body.name = 'HouseC_MainBody'
    body.scale = (7.5, 7.5, 7.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(body, uv_scale=1.0)
    body.data.materials.append(mats['japanese_siding'])
    apply_bevel(body, width=0.04, segments=2)
    col.objects.link(body)
    bpy.context.collection.objects.unlink(body)
    
    # 屋顶
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, bz + 3.7))
    roof = bpy.context.active_object
    roof.scale = (8.5, 8.5, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(roof, uv_scale=1.5)
    roof.data.materials.append(mats['japanese_roof'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # 3.5m 战术小巷地面铺装 (细条石砖)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-14.25, 0.0, 0.05))
    alley_floor = bpy.context.active_object
    alley_floor.name = 'Alley_Pavement_Floor'
    alley_floor.scale = (8.5, 3.5, 0.1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(alley_floor, uv_scale=1.0)
    alley_floor.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(alley_floor)
    bpy.context.collection.objects.unlink(alley_floor)

    # 小巷墙面生活细节道具：空调室外机群、电表与金属落水管
    # House A 南墙空调外机
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-12.5, -1.45, 0.65))
    ac1 = bpy.context.active_object
    ac1.name = 'Alley_AC_Unit_1'
    ac1.scale = (0.5, 0.85, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac1.data.materials.append(mats['aluminum_silver'])
    apply_bevel(ac1, width=0.02, segments=2)
    col.objects.link(ac1)
    bpy.context.collection.objects.unlink(ac1)

    # House C 北墙空调外机
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-15.0, 1.45, 0.65))
    ac2 = bpy.context.active_object
    ac2.name = 'Alley_AC_Unit_2'
    ac2.scale = (0.5, 0.85, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac2.data.materials.append(mats['aluminum_silver'])
    apply_bevel(ac2, width=0.02, segments=2)
    col.objects.link(ac2)
    bpy.context.collection.objects.unlink(ac2)

    # 小巷东侧入口矮墙 (高 1.2m，两侧留出自由通道与跳跃战术点)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.3, 0.0, 0.6))
    fence = bpy.context.active_object
    fence.name = 'Alley_Fence_Low'
    fence.scale = (0.35, 1.8, 1.2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_box_uv(fence, uv_scale=1.0)
    fence.data.materials.append(mats['concrete_curb'])
    apply_bevel(fence, width=0.03, segments=2)
    col.objects.link(fence)
    bpy.context.collection.objects.unlink(fence)

    return col

# ==============================================================================
# 街道生活道具生态 (Props Ecosystem: 电线杆、变压器、电线、垃圾箱、反光锥)
# ==============================================================================
def build_street_props_ecosystem(mats):
    col = bpy.data.collections.new('05_Street_Props_Ecosystem')
    bpy.context.scene.collection.children.link(col)
    
    # 1. 水泥电线杆群 (带三相变压器铁箱与爬梯)
    pole_coords = [(-4.2, 12.0, 0.1), (-4.2, -3.0, 2.1), (-4.2, -18.0, 4.8)]
    for idx, (px, py, pz) in enumerate(pole_coords):
        # 混凝土立柱
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=9.5, location=(px, py, pz + 4.75))
        pole = bpy.context.active_object
        pole.name = f'Utility_Pole_{idx}'
        pole.data.materials.append(mats['concrete_curb'])
        bpy.ops.object.shade_smooth()
        col.objects.link(pole)
        bpy.context.collection.objects.unlink(pole)
        
        # 变压器设备箱
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px - 0.45, py, pz + 7.2))
        trans = bpy.context.active_object
        trans.scale = (0.6, 0.8, 1.2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        trans.data.materials.append(mats['aluminum_dark'])
        apply_bevel(trans, width=0.02, segments=2)
        col.objects.link(trans)
        bpy.context.collection.objects.unlink(trans)
        
        # 横担金属梁与绝缘子
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, pz + 8.8))
        cross_arm = bpy.context.active_object
        cross_arm.scale = (1.8, 0.12, 0.12)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        cross_arm.data.materials.append(mats['aluminum_silver'])
        col.objects.link(cross_arm)
        bpy.context.collection.objects.unlink(cross_arm)
        
        for ix in [-0.75, 0.0, 0.75]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.25, location=(px + ix, py, pz + 9.0))
            insul = bpy.context.active_object
            insul.data.materials.append(mats['aluminum_silver'])
            col.objects.link(insul)
            bpy.context.collection.objects.unlink(insul)

    # 2. 空中交错悬垂电缆网 (Catenary Overhead Cables)
    for p_start, p_end in [
        ((-4.2, 12.0, 8.9), (-4.2, -3.0, 10.9)),
        ((-4.2, -3.0, 10.9), (-4.2, -18.0, 13.6)),
        ((-4.2, 12.0, 8.6), (-10.0, 19.5, 6.8)),
        ((-4.2, -3.0, 10.6), (-10.5, -5.0, 6.8))
    ]:
        curve_data = bpy.data.curves.new('CatenaryCable', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.018
        curve_data.bevel_resolution = 3
        
        polyline = curve_data.splines.new('BEZIER')
        polyline.bezier_points.add(2)
        
        p0 = polyline.bezier_points[0]
        p1 = polyline.bezier_points[1]
        p2 = polyline.bezier_points[2]
        
        sx, sy, sz = p_start
        ex, ey, ez = p_end
        mx, my, mz = (sx + ex) / 2.0, (sy + ey) / 2.0, (sz + ez) / 2.0 - 0.45 # 悬垂弧度
        
        p0.co = (sx, sy, sz)
        p1.co = (mx, my, mz)
        p2.co = (ex, ey, ez)
        
        for p in [p0, p1, p2]:
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'
            
        cable_obj = bpy.data.objects.new('Cable_Wire', curve_data)
        cable_obj.data.materials.append(mats['aluminum_dark'])
        col.objects.link(cable_obj)

    # 3. 日式街区分类垃圾箱 (可回收蓝 / 不可燃灰)
    for ti, t_col in [(0, (0.15, 0.45, 0.85, 1.0)), (1, (0.35, 0.38, 0.40, 1.0))]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.8, 14.5 + ti * 0.65, 0.6))
        bin_obj = bpy.context.active_object
        bin_obj.scale = (0.5, 0.55, 0.9)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bin_mat = create_colored_metal(f'M_TrashBin_{ti}', t_col, roughness=0.45, metallic=0.7)
        bin_obj.data.materials.append(bin_mat)
        apply_bevel(bin_obj, width=0.02, segments=2)
        col.objects.link(bin_obj)
        bpy.context.collection.objects.unlink(bin_obj)

    # 4. 黄色反光交通警示锥 (Traffic Cones)
    for c_i, (cx, cy, cz) in enumerate([(-3.8, 18.0, 0.4), (-3.8, 16.5, 0.4), (-3.8, 2.5, 1.6)]):
        bpy.ops.mesh.primitive_cone_add(radius1=0.22, radius2=0.03, depth=0.75, location=(cx, cy, cz))
        cone = bpy.context.active_object
        cone.name = f'TrafficCone_{c_i}'
        cone.data.materials.append(mats['cone_yellow'])
        col.objects.link(cone)
        bpy.context.collection.objects.unlink(cone)
        
        # 黑色防滑橡胶底座
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, cz - 0.35))
        base = bpy.context.active_object
        base.scale = (0.45, 0.45, 0.05)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        base.data.materials.append(mats['aluminum_dark'])
        col.objects.link(base)
        bpy.context.collection.objects.unlink(base)

    # 5. 黄色广角反光凸面镜 (Curved Street Mirror)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=2.8, location=(-4.3, 7.8, 1.5))
    m_post = bpy.context.active_object
    m_post.data.materials.append(mats['cone_yellow'])
    col.objects.link(m_post)
    bpy.context.collection.objects.unlink(m_post)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.08, location=(-4.3, 7.8, 2.75))
    mirror = bpy.context.active_object
    mirror.rotation_euler = (0, math.radians(70), math.radians(45))
    mirror.data.materials.append(mats['aluminum_silver'])
    col.objects.link(mirror)
    bpy.context.collection.objects.unlink(mirror)

    return col

# ==============================================================================
# 主执行入口：构建、烘焙材质绑定、导出 GLB
# ==============================================================================
def main():
    print("======================================================================")
    print("★ Asternova 次世代街区沙盒场景全流程重构 (CS2 PBR + ZZZ 生活气息) 启动 ★")
    print("======================================================================")
    clean_scene()
    
    # 实例化全套次世代 2K PBR 材质
    mats = {
        'asphalt_road': create_gltf_pbr_material(
            'M_AsphaltRoad_2K',
            albedo_file='asphalt_road_2k_albedo.png',
            normal_file='asphalt_road_2k_normal.png',
            roughness_file='asphalt_road_2k_roughness.png',
            normal_strength=2.2
        ),
        'sidewalk_tiles': create_gltf_pbr_material(
            'M_SidewalkTiles_2K',
            albedo_file='sidewalk_tiles_2k_albedo.png',
            normal_file='sidewalk_tiles_2k_normal.png',
            roughness_file='sidewalk_tiles_2k_roughness.png',
            normal_strength=2.0
        ),
        'tactile_paving': create_gltf_pbr_material(
            'M_TactilePaving_2K',
            albedo_file='tactile_paving_2k_albedo.png',
            normal_file='tactile_paving_2k_normal.png',
            roughness_file='tactile_paving_2k_roughness.png',
            normal_strength=3.0
        ),
        'concrete_curb': create_gltf_pbr_material(
            'M_ConcreteCurb_2K',
            albedo_file='concrete_curb_2k_albedo.png',
            normal_file='concrete_curb_2k_normal.png',
            roughness_file='concrete_curb_2k_roughness.png',
            normal_strength=1.8
        ),
        'japanese_siding': create_gltf_pbr_material(
            'M_JapaneseSiding_2K',
            albedo_file='japanese_siding_2k_albedo.png',
            normal_file='japanese_siding_2k_normal.png',
            roughness_file='japanese_siding_2k_roughness.png',
            normal_strength=2.0
        ),
        'japanese_tile': create_gltf_pbr_material(
            'M_JapaneseTile_2K',
            albedo_file='japanese_tile_2k_albedo.png',
            normal_file='japanese_tile_2k_normal.png',
            roughness_file='japanese_tile_2k_roughness.png',
            normal_strength=2.2
        ),
        'japanese_roof': create_gltf_pbr_material(
            'M_JapaneseRoof_2K',
            albedo_file='japanese_roof_kawara_2k_albedo.png',
            normal_file='japanese_roof_kawara_2k_normal.png',
            roughness_file='japanese_roof_kawara_2k_roughness.png',
            normal_strength=2.5
        ),
        'store_sign': create_gltf_pbr_material(
            'M_StoreSign_2K',
            albedo_file='convenience_store_sign_2k_albedo.png',
            emissive_file='convenience_store_sign_2k_emissive.png',
            roughness_val=0.25,
            emissive_strength=1.1
        ),
        'store_shelves': create_gltf_pbr_material(
            'M_StoreShelves_2K',
            albedo_file='convenience_store_interior_2k.png',
            emissive_file='convenience_store_interior_2k.png',
            roughness_val=0.35,
            emissive_strength=0.9
        ),
        'vending_machine': create_gltf_pbr_material(
            'M_VendingMachine_2K',
            albedo_file='vending_machine_2k_diffuse.png',
            normal_file='vending_machine_2k_normal.png',
            roughness_file='vending_machine_2k_roughness.png',
            emissive_file='vending_machine_2k_emissive.png',
            metallic_val=0.4,
            normal_strength=2.2,
            emissive_strength=1.35
        ),
        'city_mansion': create_gltf_pbr_material(
            'M_CityMansion_2K',
            albedo_file='city_skyline_mansion_2k_albedo.png',
            normal_file='city_skyline_mansion_2k_normal.png',
            roughness_file='city_skyline_mansion_2k_roughness.png',
            normal_strength=1.8
        ),
        'glass': create_glass_material('M_Glass'),
        'aluminum_dark': create_colored_metal('M_Aluminum_Dark', (0.12, 0.13, 0.14, 1.0), roughness=0.35, metallic=0.85),
        'aluminum_silver': create_colored_metal('M_Aluminum_Silver', (0.75, 0.78, 0.80, 1.0), roughness=0.30, metallic=0.88),
        'torii_red': create_colored_metal('M_ToriiRed', (0.85, 0.18, 0.12, 1.0), roughness=0.45, metallic=0.1),
        'torii_black': create_colored_metal('M_ToriiBlack', (0.10, 0.10, 0.12, 1.0), roughness=0.35, metallic=0.8),
        'train_yellow': create_colored_metal('M_TrainYellow', (0.95, 0.72, 0.08, 1.0), roughness=0.28, metallic=0.6),
        'cone_yellow': create_colored_metal('M_ConeYellow', (0.98, 0.68, 0.02, 1.0), roughness=0.32, metallic=0.2)
    }
    
    print("1. 构建 360° 全封闭天际线与山坡高台 (彻底杜绝黑虚空与白石碑)...")
    build_environment_backdrop(mats)
    
    print("2. 构建平缓顺接 40m 跑酷长坡与铺装路网...")
    build_terrain_and_roads(mats)
    
    print("3. 构建日式住宅 House A (米白防雨挂板、和瓦屋顶、4.5m 跑酷阳台与车库)...")
    build_house_a(mats)
    
    print("4. 构建 24H 便利店与街角双联写实自动贩卖机...")
    build_house_b_convenience_store(mats)
    
    print("5. 构建住宅 House C 与 3.5m 战术夹墙小巷...")
    build_house_c_and_alleyway(mats)
    
    print("6. 构建生活道具生态 (电线杆变压器、悬垂交错电缆、分类垃圾箱、交通锥)...")
    build_street_props_ecosystem(mats)
    
    # 导出目标
    games_root = r'c:\Users\TimeCraker\Desktop\my-workspace\games'
    asternova_root = os.path.join(games_root, 'asternova')
    
    # 保存 .blend
    blend_target = os.path.join(asternova_root, 'art', 'models', 'neighborhood', 'modern_japan_neighborhood.blend')
    ensure_dir(os.path.dirname(blend_target))
    bpy.ops.wm.save_as_mainfile(filepath=blend_target)
    print(f"Saved .blend: {blend_target}")
    
    # 导出 GLB
    glb_targets = [
        os.path.join(asternova_root, 'client-godot-v2', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(games_root, 'client-godot-v2', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(asternova_root, 'render-lab', 'models', 'environment', 'modern_japan_neighborhood.glb'),
        os.path.join(games_root, 'render-lab', 'models', 'environment', 'modern_japan_neighborhood.glb')
    ]
    
    for gp in glb_targets:
        ensure_dir(os.path.dirname(gp))
        # 导出带材质与内嵌贴图的 GLB
        bpy.ops.export_scene.gltf(
            filepath=gp,
            export_format='GLB',
            export_materials='EXPORT',
            export_cameras=False,
            export_apply=True
        )
        print(f"Exported High-Precision GLB: {gp} ({os.path.getsize(gp)} bytes)")
        
    print("======================================================================")
    print("★ Next-Gen Rebuild Script Executed & GLB Exported Successfully! ★")
    print("======================================================================")

if __name__ == '__main__':
    main()
