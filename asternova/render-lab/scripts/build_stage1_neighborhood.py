"""
build_stage1_neighborhood.py
Blender 5.2 脚本：构建现代日本晴空住宅街区与 CS2 级沙盒第一阶段资产
- 现代外墙 Trim Sheet UV 贴图与材质映射
- 住宅 1 (二层独栋带 4.5m 阳台)
- 住宅 2 (平房带开放式车库)
- 住宅 3 (转角独栋)
- 3.5m 战术小巷 (供 3 次折返蹬墙跳)
- 2.2m 混凝土院墙 (供一段跳翻越与空中下砸)
- 40m 长、6.5m 宽 15° 自然下坡大滑道 (供 M2 滑铲重力加速实测)
- 坡顶 +8m 高台微型朱红鸟居 (高 3.8m) 与古朴小神龛
- CS2 级平滑隐形碰撞体 (-colonly 跑酷防卡脚标准)
- 精确 look_at 摄像机靶向自检渲染 3 张 1080p 预览截图
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

BASE_DIR = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab"
TEXTURES_DIR = os.path.join(BASE_DIR, "textures")
MODELS_DIR = os.path.join(BASE_DIR, "models", "environment")
SCREENS_DIR = os.path.join(BASE_DIR, "screenshots", "stage1")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(SCREENS_DIR, exist_ok=True)

TRIM_ALBEDO = os.path.join(TEXTURES_DIR, "trim_modern_japan_2k.png")
TRIM_NORMAL = os.path.join(TEXTURES_DIR, "trim_modern_japan_2k_normal.png")
TRIM_ROUGH  = os.path.join(TEXTURES_DIR, "trim_modern_japan_2k_roughness.png")
ROAD_ALBEDO = os.path.join(TEXTURES_DIR, "asphalt_road_2k.png")

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    # AgX color management for clean highlights
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'None'

def create_materials():
    materials = {}
    
    # 1. Trim Sheet Material
    mat_trim = bpy.data.materials.new(name="Mat_Trim_Modern_Japan")
    mat_trim.use_nodes = True
    nodes = mat_trim.node_tree.nodes
    links = mat_trim.node_tree.links
    nodes.clear()
    
    node_out = nodes.new('ShaderNodeOutputMaterial')
    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Specular IOR Level'].default_value = 0.5
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])
    
    if os.path.exists(TRIM_ALBEDO):
        img_alb = bpy.data.images.load(TRIM_ALBEDO)
        node_alb = nodes.new('ShaderNodeTexImage')
        node_alb.image = img_alb
        links.new(node_alb.outputs['Color'], node_bsdf.inputs['Base Color'])
        
    if os.path.exists(TRIM_ROUGH):
        img_rou = bpy.data.images.load(TRIM_ROUGH)
        img_rou.colorspace_settings.name = 'Non-Color'
        node_rou = nodes.new('ShaderNodeTexImage')
        node_rou.image = img_rou
        links.new(node_rou.outputs['Color'], node_bsdf.inputs['Roughness'])
        
    if os.path.exists(TRIM_NORMAL):
        img_nor = bpy.data.images.load(TRIM_NORMAL)
        img_nor.colorspace_settings.name = 'Non-Color'
        node_nor_tex = nodes.new('ShaderNodeTexImage')
        node_nor_tex.image = img_nor
        node_nor_map = nodes.new('ShaderNodeNormalMap')
        node_nor_map.inputs['Strength'].default_value = 0.85
        links.new(node_nor_tex.outputs['Color'], node_nor_map.inputs['Color'])
        links.new(node_nor_map.outputs['Normal'], node_bsdf.inputs['Normal'])
        
    materials['trim'] = mat_trim
    
    # 2. Road Material
    mat_road = bpy.data.materials.new(name="Mat_Asphalt_Road")
    mat_road.use_nodes = True
    rnodes = mat_road.node_tree.nodes
    rlinks = mat_road.node_tree.links
    rnodes.clear()
    
    rout = rnodes.new('ShaderNodeOutputMaterial')
    rbsdf = rnodes.new('ShaderNodeBsdfPrincipled')
    rbsdf.inputs['Roughness'].default_value = 0.85
    rlinks.new(rbsdf.outputs['BSDF'], rout.inputs['Surface'])
    
    if os.path.exists(ROAD_ALBEDO):
        img_road = bpy.data.images.load(ROAD_ALBEDO)
        node_road = rnodes.new('ShaderNodeTexImage')
        node_road.image = img_road
        rlinks.new(node_road.outputs['Color'], rbsdf.inputs['Base Color'])
    materials['road'] = mat_road
    
    # 3. Torii Vermilion (朱红)
    mat_torii = bpy.data.materials.new(name="Mat_Torii_Vermilion")
    mat_torii.use_nodes = True
    tnodes = mat_torii.node_tree.nodes
    tlinks = mat_torii.node_tree.links
    tnodes.clear()
    tout = tnodes.new('ShaderNodeOutputMaterial')
    tbsdf = tnodes.new('ShaderNodeBsdfPrincipled')
    tbsdf.inputs['Base Color'].default_value = (0.85, 0.18, 0.12, 1.0)
    tbsdf.inputs['Roughness'].default_value = 0.40
    tlinks.new(tbsdf.outputs['BSDF'], tout.inputs['Surface'])
    materials['torii'] = mat_torii
    
    # 4. Shrine Wood (古木)
    mat_shrine = bpy.data.materials.new(name="Mat_Shrine_Wood")
    mat_shrine.use_nodes = True
    snodes = mat_shrine.node_tree.nodes
    slinks = mat_shrine.node_tree.links
    snodes.clear()
    sout = snodes.new('ShaderNodeOutputMaterial')
    sbsdf = snodes.new('ShaderNodeBsdfPrincipled')
    sbsdf.inputs['Base Color'].default_value = (0.26, 0.20, 0.16, 1.0)
    sbsdf.inputs['Roughness'].default_value = 0.80
    slinks.new(sbsdf.outputs['BSDF'], sout.inputs['Surface'])
    materials['shrine'] = mat_shrine
    
    # 5. Stone Base
    mat_stone = bpy.data.materials.new(name="Mat_Stone_Base")
    mat_stone.use_nodes = True
    stnodes = mat_stone.node_tree.nodes
    stlinks = mat_stone.node_tree.links
    stnodes.clear()
    stout = stnodes.new('ShaderNodeOutputMaterial')
    stbsdf = stnodes.new('ShaderNodeBsdfPrincipled')
    stbsdf.inputs['Base Color'].default_value = (0.50, 0.52, 0.55, 1.0)
    stbsdf.inputs['Roughness'].default_value = 0.85
    stlinks.new(stbsdf.outputs['BSDF'], stout.inputs['Surface'])
    materials['stone'] = mat_stone

    return materials

# UV Strips (V inverted from PIL top-down)
UV_WHITE_TILE = (0.0, 0.750, 1.0, 1.000)
UV_CONCRETE   = (0.0, 0.551, 1.0, 0.750)
UV_ROOF_TILE  = (0.0, 0.350, 1.0, 0.551)
UV_WINDOW     = (0.0, 0.219, 1.0, 0.350)
UV_RAILING    = (0.0, 0.102, 1.0, 0.219)
UV_BASE_TRIM  = (0.0, 0.000, 1.0, 0.102)

def build_box(name, size, location, mat, uv_strip=None, u_rep=1.0, v_rep=1.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    if mat:
        obj.data.materials.append(mat)
        
    if uv_strip and len(obj.data.uv_layers) > 0:
        mesh = obj.data
        u_min, v_min, u_max, v_max = uv_strip
        uv_data = mesh.uv_layers.active.data
        
        # World aligned UV mapping for each face
        for poly in mesh.polygons:
            normal = poly.normal
            for i, loop_idx in enumerate(poly.loop_indices):
                vert_idx = poly.vertices[i]
                v_local = mesh.vertices[vert_idx].co
                
                # If vertical face (wall)
                if abs(normal.z) < 0.5:
                    horiz_coord = v_local.x if abs(normal.y) > 0.5 else v_local.y
                    u = u_min + ((horiz_coord + 50.0) * 0.5 * u_rep) % (u_max - u_min)
                    v = v_min + ((v_local.z + 50.0) * 0.5 * v_rep) % (v_max - v_min)
                else:
                    # Horizontal face (roof / floor)
                    u = u_min + ((v_local.x + 50.0) * 0.5 * u_rep) % (u_max - u_min)
                    v = v_min + ((v_local.y + 50.0) * 0.5 * v_rep) % (v_max - v_min)
                    
                uv_data[loop_idx].uv = (u, v)
                
    return obj

def build_house_1(materials):
    col_group = bpy.data.collections.new("House_1")
    bpy.context.scene.collection.children.link(col_group)
    
    # 1. 踢脚线
    plinth = build_box("H1_Plinth", (7.5, 10.0, 0.6), (-14.25, -5.0, 0.3), materials['trim'], UV_BASE_TRIM)
    col_group.objects.link(plinth)
    bpy.context.scene.collection.objects.unlink(plinth)
    
    # 2. 一层主墙体 (米白瓷砖)
    body1 = build_box("H1_Body1", (7.5, 10.0, 3.0), (-14.25, -5.0, 2.1), materials['trim'], UV_WHITE_TILE, u_rep=2.0, v_rep=2.0)
    col_group.objects.link(body1)
    bpy.context.scene.collection.objects.unlink(body1)
    
    # 3. 分隔腰线
    belt = build_box("H1_Belt", (7.7, 10.2, 0.25), (-14.25, -5.0, 3.6), materials['trim'], UV_BASE_TRIM)
    col_group.objects.link(belt)
    bpy.context.scene.collection.objects.unlink(belt)
    
    # 4. 二层主墙体
    body2 = build_box("H1_Body2", (7.5, 10.0, 3.4), (-14.25, -5.0, 5.3), materials['trim'], UV_WHITE_TILE, u_rep=2.0, v_rep=2.0)
    col_group.objects.link(body2)
    bpy.context.scene.collection.objects.unlink(body2)
    
    # 5. 屋顶坡面
    mesh = bpy.data.meshes.new("H1_Roof_Mesh")
    bm = bmesh.new()
    v1 = bm.verts.new((-18.4, -10.3, 7.0))
    v2 = bm.verts.new((-10.1, -10.3, 7.0))
    v3 = bm.verts.new((-10.1, 0.3, 7.0))
    v4 = bm.verts.new((-18.4, 0.3, 7.0))
    r1 = bm.verts.new((-14.25, -9.5, 8.8))
    r2 = bm.verts.new((-14.25, -0.5, 8.8))
    
    bm.faces.new((v1, v2, r1))
    bm.faces.new((v2, v3, r2, r1))
    bm.faces.new((v3, v4, r2))
    bm.faces.new((v4, v1, r1, r2))
    bm.to_mesh(mesh)
    bm.free()
    
    roof_obj = bpy.data.objects.new("H1_Roof", mesh)
    roof_obj.data.materials.append(materials['trim'])
    col_group.objects.link(roof_obj)
    
    mesh.uv_layers.new(name="UVMap")
    uv_data = mesh.uv_layers.active.data
    u_min, v_min, u_max, v_max = UV_ROOF_TILE
    for poly in mesh.polygons:
        for i, loop_idx in enumerate(poly.loop_indices):
            uv_data[loop_idx].uv = (u_min + (i % 2) * (u_max - u_min) * 2.0, v_min + ((i // 2) % 2) * (v_max - v_min) * 2.0)
            
    # 6. 二楼 4.5m 阳台 (供二段跳翻越与俯瞰)
    balcony_floor = build_box("H1_Balcony_Floor", (1.6, 4.6, 0.25), (-9.7, -5.25, 4.4), materials['trim'], UV_CONCRETE)
    col_group.objects.link(balcony_floor)
    bpy.context.scene.collection.objects.unlink(balcony_floor)
    
    rail_e = build_box("H1_Rail_East", (0.08, 4.6, 1.0), (-8.95, -5.25, 5.0), materials['trim'], UV_RAILING, u_rep=3.0)
    rail_n = build_box("H1_Rail_North", (1.6, 0.08, 1.0), (-9.7, -7.5, 5.0), materials['trim'], UV_RAILING)
    rail_s = build_box("H1_Rail_South", (1.6, 0.08, 1.0), (-9.7, -3.0, 5.0), materials['trim'], UV_RAILING)
    for r in [rail_e, rail_n, rail_s]:
        col_group.objects.link(r)
        bpy.context.scene.collection.objects.unlink(r)
        
    # 7. 铝合金窗户
    win1 = build_box("H1_Win_East_1F", (0.12, 2.5, 1.6), (-10.45, -3.5, 2.0), materials['trim'], UV_WINDOW)
    win2 = build_box("H1_Win_East_2F", (0.12, 2.5, 1.6), (-10.45, -5.25, 5.5), materials['trim'], UV_WINDOW)
    win_south = build_box("H1_Win_South", (3.0, 0.12, 1.6), (-14.25, -0.05, 5.5), materials['trim'], UV_WINDOW)
    for w in [win1, win2, win_south]:
        col_group.objects.link(w)
        bpy.context.scene.collection.objects.unlink(w)
        
    # 8. CS2 跑酷隐形碰撞体 (-colonly)
    h1_col = build_box("H1_Main-colonly", (7.5, 10.0, 7.0), (-14.25, -5.0, 3.5), None)
    h1_bal_col = build_box("H1_Balcony-colonly", (1.6, 4.6, 4.5), (-9.7, -5.25, 2.25), None)
    for c in [h1_col, h1_bal_col]:
        c.display_type = 'WIRE'
        col_group.objects.link(c)
        bpy.context.scene.collection.objects.unlink(c)

def build_house_2(materials):
    col_group = bpy.data.collections.new("House_2")
    bpy.context.scene.collection.children.link(col_group)
    
    # 住宅 2：带开放式车库平房 (Y: +3.5 至 +13.5，与住宅 1 严格相距 3.5m！)
    north_wing = build_box("H2_North_Wing", (7.5, 1.5, 4.2), (-14.25, +4.25, 2.1), materials['trim'], UV_CONCRETE, u_rep=2.0)
    south_wing = build_box("H2_South_Wing", (7.5, 4.0, 4.2), (-14.25, +11.5, 2.1), materials['trim'], UV_CONCRETE, u_rep=2.0)
    garage_back = build_box("H2_Garage_Back", (2.5, 4.5, 4.2), (-16.75, +7.25, 2.1), materials['trim'], UV_CONCRETE)
    garage_roof = build_box("H2_Garage_Ceiling", (5.0, 4.5, 1.2), (-13.0, +7.25, 3.6), materials['trim'], UV_CONCRETE)
    garage_floor = build_box("H2_Garage_Floor", (5.0, 4.5, 0.15), (-13.0, +7.25, 0.075), materials['trim'], UV_BASE_TRIM)
    coping = build_box("H2_Parapet", (7.7, 10.2, 0.25), (-14.25, +8.5, 4.3), materials['trim'], UV_BASE_TRIM)
    win_south = build_box("H2_Win_South", (0.12, 2.4, 1.5), (-10.45, +11.5, 2.0), materials['trim'], UV_WINDOW)
    
    for obj in [north_wing, south_wing, garage_back, garage_roof, garage_floor, coping, win_south]:
        col_group.objects.link(obj)
        bpy.context.scene.collection.objects.unlink(obj)
        
    # 车库内部碰撞体
    col_n = build_box("H2_Col_North-colonly", (7.5, 1.5, 4.2), (-14.25, +4.25, 2.1), None)
    col_s = build_box("H2_Col_South-colonly", (7.5, 4.0, 4.2), (-14.25, +11.5, 2.1), None)
    col_b = build_box("H2_Col_Back-colonly", (2.5, 4.5, 4.2), (-16.75, +7.25, 2.1), None)
    col_r = build_box("H2_Col_Ceiling-colonly", (5.0, 4.5, 1.2), (-13.0, +7.25, 3.6), None)
    for c in [col_n, col_s, col_b, col_r]:
        c.display_type = 'WIRE'
        col_group.objects.link(c)
        bpy.context.scene.collection.objects.unlink(c)

def build_house_3_and_walls(materials):
    col_group = bpy.data.collections.new("House_3_and_Walls")
    bpy.context.scene.collection.children.link(col_group)
    
    # 住宅 3：转角独栋 (Y: +16.0 至 +25.0)
    h3_body = build_box("H3_Body", (7.5, 9.0, 6.0), (-14.25, +20.5, 3.0), materials['trim'], UV_WHITE_TILE, u_rep=3.0, v_rep=2.0)
    h3_roof = build_box("H3_Roof", (8.0, 9.4, 1.4), (-14.25, +20.5, 6.7), materials['trim'], UV_ROOF_TILE, u_rep=2.0)
    h3_col = build_box("H3_Col-colonly", (7.5, 9.0, 6.0), (-14.25, +20.5, 3.0), None)
    h3_col.display_type = 'WIRE'
    
    for o in [h3_body, h3_roof, h3_col]:
        col_group.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # 2.2m 高混凝土住宅外围院墙 (严格 2.2m，供一段跳翻越与空中下砸)
    wall1 = build_box("Boundary_Wall_1", (0.3, 4.0, 2.2), (-9.0, -8.0, 1.1), materials['trim'], UV_CONCRETE, v_rep=0.8)
    wall2 = build_box("Boundary_Wall_2", (0.3, 1.5, 2.2), (-9.0, +4.25, 1.1), materials['trim'], UV_CONCRETE, v_rep=0.8)
    wall3 = build_box("Boundary_Wall_3", (0.3, 2.5, 2.2), (-9.0, +14.75, 1.1), materials['trim'], UV_CONCRETE, v_rep=0.8)
    
    for i, w in enumerate([wall1, wall2, wall3]):
        coping = build_box(f"Wall_Coping_{i+1}", (w.scale.x + 0.1, w.scale.y, 0.12), (w.location.x, w.location.y, 2.26), materials['trim'], UV_BASE_TRIM)
        wall_col = build_box(f"Wall_Col_{i+1}-colonly", (w.scale.x, w.scale.y, 2.2), (w.location.x, w.location.y, 1.1), None)
        wall_col.display_type = 'WIRE'
        for o in [coping, wall_col, w]:
            col_group.objects.link(o)
            if o.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(o)

def build_central_slope_and_ground(materials):
    col_group = bpy.data.collections.new("Slope_and_Roads")
    bpy.context.scene.collection.children.link(col_group)
    
    # 40m 长、6.5m 宽 15° 自然下坡大滑道
    mesh_road = bpy.data.meshes.new("Slope_Road_Mesh")
    bm = bmesh.new()
    w2 = 3.25
    # Y 从 -25 (高 6.0m) 到 +15 (高 0.0m)
    p1 = bm.verts.new((-w2, -25.0, 6.0))
    p2 = bm.verts.new((+w2, -25.0, 6.0))
    p3 = bm.verts.new((+w2, +15.0, 0.0))
    p4 = bm.verts.new((-w2, +15.0, 0.0))
    
    bm.faces.new((p1, p2, p3, p4))
    bm.to_mesh(mesh_road)
    bm.free()
    
    road_obj = bpy.data.objects.new("Central_Slope_Road", mesh_road)
    road_obj.data.materials.append(materials['road'])
    col_group.objects.link(road_obj)
    
    mesh_road.uv_layers.new(name="UVMap")
    uv_data = mesh_road.uv_layers.active.data
    uv_data[0].uv = (0.0, 1.0)
    uv_data[1].uv = (1.0, 1.0)
    uv_data[2].uv = (1.0, 0.0)
    uv_data[3].uv = (0.0, 0.0)
    
    # 隐形斜坡碰撞盒
    col_mesh = bpy.data.meshes.new("Slope_Col_Mesh")
    cbm = bmesh.new()
    cp1 = cbm.verts.new((-w2, -25.0, 6.0))
    cp2 = cbm.verts.new((+w2, -25.0, 6.0))
    cp3 = cbm.verts.new((+w2, +15.0, 0.0))
    cp4 = cbm.verts.new((-w2, +15.0, 0.0))
    cp5 = cbm.verts.new((-w2, -25.0, -1.0))
    cp6 = cbm.verts.new((+w2, -25.0, -1.0))
    cp7 = cbm.verts.new((+w2, +15.0, -1.0))
    cp8 = cbm.verts.new((-w2, +15.0, -1.0))
    cbm.faces.new((cp1, cp2, cp3, cp4))
    cbm.faces.new((cp8, cp7, cp6, cp5))
    cbm.faces.new((cp1, cp4, cp8, cp5))
    cbm.faces.new((cp2, cp6, cp7, cp3))
    cbm.faces.new((cp1, cp5, cp6, cp2))
    cbm.faces.new((cp4, cp3, cp7, cp8))
    cbm.to_mesh(col_mesh)
    cbm.free()
    
    slope_col_obj = bpy.data.objects.new("Central_Slope-colonly", col_mesh)
    slope_col_obj.display_type = 'WIRE'
    col_group.objects.link(slope_col_obj)
    
    # 人行道
    for side, sign in [("Left", -1), ("Right", 1)]:
        sm = bpy.data.meshes.new(f"Sidewalk_{side}_Mesh")
        sbm = bmesh.new()
        x_in = sign * 3.25
        x_out = sign * 5.0
        sp1 = sbm.verts.new((x_in, -25.0, 6.18))
        sp2 = sbm.verts.new((x_out, -25.0, 6.18))
        sp3 = sbm.verts.new((x_out, +15.0, 0.18))
        sp4 = sbm.verts.new((x_in, +15.0, 0.18))
        sbm.faces.new((sp1, sp2, sp3, sp4) if sign < 0 else (sp2, sp1, sp4, sp3))
        sbm.to_mesh(sm)
        sbm.free()
        
        sobj = bpy.data.objects.new(f"Sidewalk_{side}", sm)
        sobj.data.materials.append(materials['trim'])
        col_group.objects.link(sobj)
        
        sm.uv_layers.new(name="UVMap")
        uvd = sm.uv_layers.active.data
        u_min, v_min, u_max, v_max = UV_CONCRETE
        uvd[0].uv = (u_min, v_min)
        uvd[1].uv = (u_max, v_min)
        uvd[2].uv = (u_max, v_max * 4.0)
        uvd[3].uv = (u_min, v_max * 4.0)
        
        scol = bpy.data.objects.new(f"Sidewalk_{side}-colonly", sm.copy())
        scol.display_type = 'WIRE'
        col_group.objects.link(scol)
        
    # 南端平地生活广场
    plaza = build_box("Plaza_Ground", (40.0, 20.0, 0.5), (0.0, +25.0, -0.25), materials['trim'], UV_CONCRETE, u_rep=8.0, v_rep=4.0)
    plaza_col = build_box("Plaza_Ground-colonly", (40.0, 20.0, 0.5), (0.0, +25.0, -0.25), None)
    plaza_col.display_type = 'WIRE'
    for p in [plaza, plaza_col]:
        col_group.objects.link(p)
        bpy.context.scene.collection.objects.unlink(p)
        
    # 西侧住宅区地面
    res_ground = build_box("Residential_Ground", (17.0, 25.0, 0.5), (-13.5, +2.5, -0.25), materials['trim'], UV_BASE_TRIM, u_rep=4.0, v_rep=6.0)
    res_col = build_box("Residential_Ground-colonly", (17.0, 25.0, 0.5), (-13.5, +2.5, -0.25), None)
    res_col.display_type = 'WIRE'
    for rg in [res_ground, res_col]:
        col_group.objects.link(rg)
        bpy.context.scene.collection.objects.unlink(rg)

def build_landmark_torii_and_shrine(materials):
    col_group = bpy.data.collections.new("Landmark_Torii_and_Shrine")
    bpy.context.scene.collection.children.link(col_group)
    
    # 高台石垣基座 (Z = 8.0m)
    terrace = build_box("A_Stone_Terrace", (32.0, 11.0, 8.0), (0.0, -30.5, 4.0), materials['stone'])
    terrace_col = build_box("A_Stone_Terrace-colonly", (32.0, 11.0, 8.0), (0.0, -30.5, 4.0), None)
    terrace_col.display_type = 'WIRE'
    col_group.objects.link(terrace)
    col_group.objects.link(terrace_col)
    bpy.context.scene.collection.objects.unlink(terrace)
    bpy.context.scene.collection.objects.unlink(terrace_col)
    
    # 坡顶中央石阶
    stairs_col = build_box("A_Stairs_Ramp-colonly", (5.0, 3.0, 2.5), (0.0, -25.5, 7.0), None)
    stairs_col.rotation_euler = (math.radians(-33), 0, 0)
    stairs_col.display_type = 'WIRE'
    col_group.objects.link(stairs_col)
    bpy.context.scene.collection.objects.unlink(stairs_col)
    
    for step in range(8):
        sy = -24.5 - step * 0.3
        sz = 6.0 + (step + 1) * 0.25
        s_obj = build_box(f"Stair_Step_{step+1}", (5.0, 0.35, 0.25), (0.0, sy, sz - 0.125), materials['stone'])
        col_group.objects.link(s_obj)
        bpy.context.scene.collection.objects.unlink(s_obj)
        
    # 微型朱红木质鸟居 (高度 3.8m, 经典笠木/贯/楔结构)
    torii_z0 = 8.0
    torii_y = -28.5
    pillar_dist = 2.8
    pillar_rad = 0.18
    pillar_h = 3.5
    
    for p_side, px in [("Left", -pillar_dist / 2), ("Right", pillar_dist / 2)]:
        kame = build_box(f"Torii_Kamebara_{p_side}", (0.5, 0.5, 0.3), (px, torii_y, torii_z0 + 0.15), materials['stone'])
        bpy.ops.mesh.primitive_cylinder_add(radius=pillar_rad, depth=pillar_h, location=(px, torii_y, torii_z0 + pillar_h / 2 + 0.2))
        pillar = bpy.context.active_object
        pillar.name = f"Torii_Pillar_{p_side}"
        pillar.data.materials.append(materials['torii'])
        incline = 0.035 if px < 0 else -0.035
        pillar.rotation_euler = (0, incline, 0)
        
        p_col = build_box(f"Torii_Pillar_{p_side}-colonly", (0.45, 0.45, pillar_h), (px, torii_y, torii_z0 + pillar_h / 2), None)
        p_col.display_type = 'WIRE'
        
        for o in [kame, pillar, p_col]:
            col_group.objects.link(o)
            if o.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(o)
                
    nuki = build_box("Torii_Nuki", (3.6, 0.22, 0.22), (0.0, torii_y, torii_z0 + 2.7), materials['torii'])
    kasagi = build_box("Torii_Kasagi", (4.2, 0.35, 0.30), (0.0, torii_y, torii_z0 + 3.65), materials['torii'])
    gaku = build_box("Torii_Gakuzuka", (0.22, 0.18, 0.7), (0.0, torii_y, torii_z0 + 3.15), materials['torii'])
    for o in [nuki, kasagi, gaku]:
        col_group.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # 古朴木质小神龛
    shrine_y = -32.5
    s_base1 = build_box("Shrine_Stone_Base_1", (2.4, 2.4, 0.3), (0.0, shrine_y, torii_z0 + 0.15), materials['stone'])
    s_base2 = build_box("Shrine_Stone_Base_2", (1.8, 1.8, 0.4), (0.0, shrine_y, torii_z0 + 0.5), materials['stone'])
    shrine_body = build_box("Shrine_Body", (1.2, 1.1, 1.2), (0.0, shrine_y, torii_z0 + 1.3), materials['shrine'])
    shrine_roof = build_box("Shrine_Roof", (1.8, 1.6, 0.4), (0.0, shrine_y, torii_z0 + 2.0), materials['shrine'])
    katsuogi1 = build_box("Shrine_Katsuogi_1", (0.12, 0.9, 0.12), (0.0, shrine_y, torii_z0 + 2.25), materials['shrine'])
    shrine_col = build_box("Shrine-colonly", (1.8, 1.8, 2.2), (0.0, shrine_y, torii_z0 + 1.1), None)
    shrine_col.display_type = 'WIRE'
    
    for s_item in [s_base1, s_base2, shrine_body, shrine_roof, katsuogi1, shrine_col]:
        col_group.objects.link(s_item)
        bpy.context.scene.collection.objects.unlink(s_item)

def setup_lighting_1430():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky_1430")
    scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    
    wout = wnodes.new('ShaderNodeOutputWorld')
    wbg = wnodes.new('ShaderNodeBackground')
    wbg.inputs['Color'].default_value = (0.42, 0.68, 0.96, 1.0) # 蔚蓝天光
    wbg.inputs['Strength'].default_value = 1.0
    wlinks.new(wbg.outputs['Background'], wout.inputs['Surface'])
    
    sun_data = bpy.data.lights.new(name="Sun_1430", type='SUN')
    sun_data.energy = 2.4 # 自然阳光
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Sun_1430", sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(50), math.radians(15), math.radians(-40))

def point_camera_at(cam_obj, target_pos):
    loc = cam_obj.location
    direction = Vector(target_pos) - loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def render_inspection_views():
    scene = bpy.context.scene
    cam_data = bpy.data.cameras.new('InspectionCam')
    cam_data.lens = 32
    cam_obj = bpy.data.objects.new('InspectionCam', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    # 精确靶向视点：(文件名, 相机位置, 目标注视点)
    views = [
        (
            "stage1_view1_look_up_torii.png",
            (0.0, 12.0, 1.6),        # 坡底中央
            (0.0, -28.5, 9.8)        # 昂首注视北端坡顶朱红鸟居与高台
        ),
        (
            "stage1_view2_narrow_alley.png",
            (-6.5, 1.75, 1.6),       # 战术小巷东入口中轴线
            (-18.0, 1.75, 2.5)       # 平视穿越 3.5m 夹墙小巷深处
        ),
        (
            "stage1_view3_house_facade.png",
            (-3.0, 3.0, 2.8),        # 街道对面人行道机位
            (-12.0, -2.5, 3.8)       # 聚焦住宅 1 米白外立面、4.5m 阳台与住宅 2 车库
        )
    ]
    
    print("=== Rendering Stage 1 Inspection Screenshots (Target-Locked) ===")
    for fname, loc, target in views:
        cam_obj.location = Vector(loc)
        point_camera_at(cam_obj, target)
        out_path = os.path.join(SCREENS_DIR, fname)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Captured: {out_path}")
        
    bpy.data.objects.remove(cam_obj, do_unlink=True)

def export_assets():
    blend_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.blend")
    glb_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.glb")
    
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved Blend file: {blend_path}")
    
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported GLB file: {glb_path}")

def main():
    print("Starting Stage 1 Build: Modern Japan Neighborhood...")
    reset_scene()
    materials = create_materials()
    build_house_1(materials)
    build_house_2(materials)
    build_house_3_and_walls(materials)
    build_central_slope_and_ground(materials)
    build_landmark_torii_and_shrine(materials)
    setup_lighting_1430()
    export_assets()
    render_inspection_views()
    print("Stage 1 Build Completed Successfully!")

if __name__ == "__main__":
    main()
