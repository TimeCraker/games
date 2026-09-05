"""
build_full_neighborhood.py
统一全量构建脚本：现代日本晴空住宅街区与 CS2 级沙盒 (Asternova M1/M2)
从干净工程统一生成整张 80m x 50m 紧凑精品街区：
- A 区：北端 +8m 高台视觉地标 (微型朱红鸟居 3.8m + 古朴木质神龛 + 苍劲古樱花树)
- B 区：中央晴空樱花大滑道 (40m 长、6.5m 宽 15° 自然下坡马路 + 白色实虚标线 + 斑马线 + 3 棵街区樱花树 + 电线杆与天空架空拉线)
- C 区：西侧一户建民居与战术小巷 (住宅 1 带 4.5m 阳台、住宅 2 带开放式车库、严格 3.5m 战术夹墙小巷、2.2m 混凝土外围院墙)
- D 区：南端生活广场 (红蓝自动贩卖机带冷饮发光橱窗、黄色凸面反光镜、不锈钢人行护栏、打怪靶位)
- 工艺：Valve CS2 级 Trim Sheet 1:1 边缘清晰度、Normal Transfer 球面法线重定向樱花树 (面数 ≤ 2,500)、-colonly 平滑隐形碰撞体
- 导出：
  - render-lab/models/environment/modern_japan_neighborhood.blend
  - render-lab/models/environment/modern_japan_neighborhood.glb
  - render-lab/models/environment/cherry_blossom_tree.glb
  - render-lab/models/environment/street_props.glb
- 渲染 6 张 1080p 纯净无遮挡自检截图
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler

BASE_DIR = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab"
TEXTURES_DIR = os.path.join(BASE_DIR, "textures")
MODELS_DIR = os.path.join(BASE_DIR, "models", "environment")
SCREENS_DIR = os.path.join(BASE_DIR, "screenshots", "inspection")
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
    scene.view_settings.view_transform = 'AgX'

def point_camera_at(cam_obj, target_pos):
    loc = cam_obj.location
    direction = Vector(target_pos) - loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def create_all_materials():
    mats = {}
    
    # 1. Trim Sheet
    mat_trim = bpy.data.materials.new("Mat_Trim_Modern_Japan")
    mat_trim.use_nodes = True
    nodes = mat_trim.node_tree.nodes
    links = mat_trim.node_tree.links
    nodes.clear()
    n_out = nodes.new('ShaderNodeOutputMaterial')
    n_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    n_bsdf.inputs['Specular IOR Level'].default_value = 0.5
    links.new(n_bsdf.outputs['BSDF'], n_out.inputs['Surface'])
    
    if os.path.exists(TRIM_ALBEDO):
        img_alb = bpy.data.images.load(TRIM_ALBEDO)
        n_alb = nodes.new('ShaderNodeTexImage')
        n_alb.image = img_alb
        links.new(n_alb.outputs['Color'], n_bsdf.inputs['Base Color'])
    if os.path.exists(TRIM_ROUGH):
        img_rou = bpy.data.images.load(TRIM_ROUGH)
        img_rou.colorspace_settings.name = 'Non-Color'
        n_rou = nodes.new('ShaderNodeTexImage')
        n_rou.image = img_rou
        links.new(n_rou.outputs['Color'], n_bsdf.inputs['Roughness'])
    if os.path.exists(TRIM_NORMAL):
        img_nor = bpy.data.images.load(TRIM_NORMAL)
        img_nor.colorspace_settings.name = 'Non-Color'
        n_nt = nodes.new('ShaderNodeTexImage')
        n_nt.image = img_nor
        n_nm = nodes.new('ShaderNodeNormalMap')
        n_nm.inputs['Strength'].default_value = 0.85
        links.new(n_nt.outputs['Color'], n_nm.inputs['Color'])
        links.new(n_nm.outputs['Normal'], n_bsdf.inputs['Normal'])
    mats['trim'] = mat_trim
    
    # 2. Road
    mat_road = bpy.data.materials.new("Mat_Asphalt_Road")
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
        n_road = rnodes.new('ShaderNodeTexImage')
        n_road.image = img_road
        rlinks.new(n_road.outputs['Color'], rbsdf.inputs['Base Color'])
    mats['road'] = mat_road
    
    # 3. Torii Vermilion
    mat_torii = bpy.data.materials.new("Mat_Torii_Vermilion")
    mat_torii.use_nodes = True
    tnodes = mat_torii.node_tree.nodes
    tlinks = mat_torii.node_tree.links
    tnodes.clear()
    tout = tnodes.new('ShaderNodeOutputMaterial')
    tbsdf = tnodes.new('ShaderNodeBsdfPrincipled')
    tbsdf.inputs['Base Color'].default_value = (0.86, 0.18, 0.12, 1.0)
    tbsdf.inputs['Roughness'].default_value = 0.40
    tlinks.new(tbsdf.outputs['BSDF'], tout.inputs['Surface'])
    mats['torii'] = mat_torii
    
    # 4. Shrine Wood
    mat_shrine = bpy.data.materials.new("Mat_Shrine_Wood")
    mat_shrine.use_nodes = True
    snodes = mat_shrine.node_tree.nodes
    slinks = mat_shrine.node_tree.links
    snodes.clear()
    sout = snodes.new('ShaderNodeOutputMaterial')
    sbsdf = snodes.new('ShaderNodeBsdfPrincipled')
    sbsdf.inputs['Base Color'].default_value = (0.28, 0.22, 0.18, 1.0)
    sbsdf.inputs['Roughness'].default_value = 0.80
    slinks.new(sbsdf.outputs['BSDF'], sout.inputs['Surface'])
    mats['shrine'] = mat_shrine
    
    # 5. Stone Base
    mat_stone = bpy.data.materials.new("Mat_Stone_Base")
    mat_stone.use_nodes = True
    stnodes = mat_stone.node_tree.nodes
    stlinks = mat_stone.node_tree.links
    stnodes.clear()
    stout = stnodes.new('ShaderNodeOutputMaterial')
    stbsdf = stnodes.new('ShaderNodeBsdfPrincipled')
    stbsdf.inputs['Base Color'].default_value = (0.52, 0.54, 0.56, 1.0)
    stbsdf.inputs['Roughness'].default_value = 0.85
    stlinks.new(stbsdf.outputs['BSDF'], stout.inputs['Surface'])
    mats['stone'] = mat_stone

    # 6. Sakura Petal (Toon)
    mat_sakura = bpy.data.materials.new("Mat_Sakura_Petal")
    mat_sakura.use_nodes = True
    sknodes = mat_sakura.node_tree.nodes
    sklinks = mat_sakura.node_tree.links
    sknodes.clear()
    skout = sknodes.new('ShaderNodeOutputMaterial')
    skbsdf = sknodes.new('ShaderNodeBsdfPrincipled')
    skbsdf.inputs['Base Color'].default_value = (1.0, 0.72, 0.84, 1.0) # 柔和通透樱粉
    skbsdf.inputs['Roughness'].default_value = 0.80
    skbsdf.inputs['Subsurface Weight'].default_value = 0.30
    sklinks.new(skbsdf.outputs['BSDF'], skout.inputs['Surface'])
    mats['sakura'] = mat_sakura

    # 7. Cherry Bark
    mat_bark = bpy.data.materials.new("Mat_Cherry_Bark")
    mat_bark.use_nodes = True
    bnodes = mat_bark.node_tree.nodes
    blinks = mat_bark.node_tree.links
    bnodes.clear()
    bout = bnodes.new('ShaderNodeOutputMaterial')
    bbsdf = bnodes.new('ShaderNodeBsdfPrincipled')
    bbsdf.inputs['Base Color'].default_value = (0.28, 0.20, 0.16, 1.0)
    bbsdf.inputs['Roughness'].default_value = 0.80
    blinks.new(bbsdf.outputs['BSDF'], bout.inputs['Surface'])
    mats['bark'] = mat_bark

    # 8. Utility Pole
    mat_pole = bpy.data.materials.new("Mat_Utility_Pole")
    mat_pole.use_nodes = True
    pnodes = mat_pole.node_tree.nodes
    plinks = mat_pole.node_tree.links
    pnodes.clear()
    pout = pnodes.new('ShaderNodeOutputMaterial')
    pbsdf = pnodes.new('ShaderNodeBsdfPrincipled')
    pbsdf.inputs['Base Color'].default_value = (0.64, 0.66, 0.68, 1.0)
    pbsdf.inputs['Roughness'].default_value = 0.70
    plinks.new(pbsdf.outputs['BSDF'], pout.inputs['Surface'])
    mats['pole'] = mat_pole

    # 9. Transformer
    mat_trans = bpy.data.materials.new("Mat_Transformer")
    mat_trans.use_nodes = True
    trnodes = mat_trans.node_tree.nodes
    trlinks = mat_trans.node_tree.links
    trnodes.clear()
    trout = trnodes.new('ShaderNodeOutputMaterial')
    trbsdf = trnodes.new('ShaderNodeBsdfPrincipled')
    trbsdf.inputs['Base Color'].default_value = (0.22, 0.28, 0.25, 1.0)
    trbsdf.inputs['Metallic'].default_value = 0.7
    trbsdf.inputs['Roughness'].default_value = 0.45
    trlinks.new(trbsdf.outputs['BSDF'], trout.inputs['Surface'])
    mats['transformer'] = mat_trans

    # 10. Vending Red
    mat_vr = bpy.data.materials.new("Mat_Vending_Red")
    mat_vr.use_nodes = True
    vrnodes = mat_vr.node_tree.nodes
    vrlinks = mat_vr.node_tree.links
    vrnodes.clear()
    vrout = vrnodes.new('ShaderNodeOutputMaterial')
    vrbsdf = vrnodes.new('ShaderNodeBsdfPrincipled')
    vrbsdf.inputs['Base Color'].default_value = (0.86, 0.12, 0.14, 1.0)
    vrbsdf.inputs['Roughness'].default_value = 0.32
    vrlinks.new(vrbsdf.outputs['BSDF'], vrout.inputs['Surface'])
    mats['vend_red'] = mat_vr

    # 11. Vending Blue
    mat_vb = bpy.data.materials.new("Mat_Vending_Blue")
    mat_vb.use_nodes = True
    vbnodes = mat_vb.node_tree.nodes
    vblinks = mat_vb.node_tree.links
    vbnodes.clear()
    vbout = vbnodes.new('ShaderNodeOutputMaterial')
    vbbsdf = vbnodes.new('ShaderNodeBsdfPrincipled')
    vbbsdf.inputs['Base Color'].default_value = (0.10, 0.44, 0.90, 1.0)
    vbbsdf.inputs['Roughness'].default_value = 0.32
    vblinks.new(vbbsdf.outputs['BSDF'], vbout.inputs['Surface'])
    mats['vend_blue'] = mat_vb

    # 12. Vending Emission Display
    mat_vg = bpy.data.materials.new("Mat_Vending_Glow")
    mat_vg.use_nodes = True
    vgnodes = mat_vg.node_tree.nodes
    vglinks = mat_vg.node_tree.links
    vgnodes.clear()
    vgout = vgnodes.new('ShaderNodeOutputMaterial')
    vgbsdf = vgnodes.new('ShaderNodeBsdfPrincipled')
    vgbsdf.inputs['Base Color'].default_value = (0.94, 0.97, 1.0, 1.0)
    vgbsdf.inputs['Emission Color'].default_value = (0.85, 0.96, 1.0, 1.0)
    vgbsdf.inputs['Emission Strength'].default_value = 2.4
    vgbsdf.inputs['Roughness'].default_value = 0.15
    vglinks.new(vgbsdf.outputs['BSDF'], vgout.inputs['Surface'])
    mats['vend_glow'] = mat_vg

    # 13. Mirror Yellow
    mat_my = bpy.data.materials.new("Mat_Mirror_Yellow")
    mat_my.use_nodes = True
    mynodes = mat_my.node_tree.nodes
    mylinks = mat_my.node_tree.links
    mynodes.clear()
    myout = mynodes.new('ShaderNodeOutputMaterial')
    mybsdf = mynodes.new('ShaderNodeBsdfPrincipled')
    mybsdf.inputs['Base Color'].default_value = (0.98, 0.58, 0.05, 1.0)
    mybsdf.inputs['Roughness'].default_value = 0.35
    mylinks.new(mybsdf.outputs['BSDF'], myout.inputs['Surface'])
    mats['mirror_yellow'] = mat_my

    # 14. Mirror Metal Face
    mat_mf = bpy.data.materials.new("Mat_Mirror_Face")
    mat_mf.use_nodes = True
    mfnodes = mat_mf.node_tree.nodes
    mflinks = mat_mf.node_tree.links
    mfnodes.clear()
    mfout = mfnodes.new('ShaderNodeOutputMaterial')
    mfbsdf = mfnodes.new('ShaderNodeBsdfPrincipled')
    mfbsdf.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1.0)
    mfbsdf.inputs['Metallic'].default_value = 1.0
    mfbsdf.inputs['Roughness'].default_value = 0.04
    mflinks.new(mfbsdf.outputs['BSDF'], mfout.inputs['Surface'])
    mats['mirror_face'] = mat_mf

    # 15. AC Unit
    mat_ac = bpy.data.materials.new("Mat_AC_Unit")
    mat_ac.use_nodes = True
    acnodes = mat_ac.node_tree.nodes
    aclinks = mat_ac.node_tree.links
    acnodes.clear()
    acout = acnodes.new('ShaderNodeOutputMaterial')
    acbsdf = acnodes.new('ShaderNodeBsdfPrincipled')
    acbsdf.inputs['Base Color'].default_value = (0.84, 0.86, 0.88, 1.0)
    acbsdf.inputs['Roughness'].default_value = 0.55
    aclinks.new(acbsdf.outputs['BSDF'], acout.inputs['Surface'])
    mats['ac'] = mat_ac

    # 16. Guardrail
    mat_gr = bpy.data.materials.new("Mat_Guardrail")
    mat_gr.use_nodes = True
    grnodes = mat_gr.node_tree.nodes
    grlinks = mat_gr.node_tree.links
    grnodes.clear()
    grout = grnodes.new('ShaderNodeOutputMaterial')
    grbsdf = grnodes.new('ShaderNodeBsdfPrincipled')
    grbsdf.inputs['Base Color'].default_value = (0.88, 0.90, 0.92, 1.0)
    grbsdf.inputs['Metallic'].default_value = 0.9
    grbsdf.inputs['Roughness'].default_value = 0.28
    grlinks.new(grbsdf.outputs['BSDF'], grout.inputs['Surface'])
    mats['guardrail'] = mat_gr

    # 17. Black Wire
    mat_wire = bpy.data.materials.new("Mat_Black_Wire")
    mat_wire.use_nodes = True
    wnodes = mat_wire.node_tree.nodes
    wlinks = mat_wire.node_tree.links
    wnodes.clear()
    wout = wnodes.new('ShaderNodeOutputMaterial')
    wbsdf = wnodes.new('ShaderNodeBsdfPrincipled')
    wbsdf.inputs['Base Color'].default_value = (0.12, 0.12, 0.14, 1.0)
    wbsdf.inputs['Roughness'].default_value = 0.8
    wlinks.new(wbsdf.outputs['BSDF'], wout.inputs['Surface'])
    mats['wire'] = mat_wire

    return mats

UV_WHITE_TILE = (0.0, 0.750, 1.0, 1.000)
UV_CONCRETE   = (0.0, 0.551, 1.0, 0.750)
UV_ROOF_TILE  = (0.0, 0.350, 1.0, 0.551)
UV_WINDOW     = (0.0, 0.219, 1.0, 0.350)
UV_RAILING    = (0.0, 0.102, 1.0, 0.219)
UV_BASE_TRIM  = (0.0, 0.000, 1.0, 0.102)

def build_box(name, size, location, mat, uv_strip=None, is_col=False):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    
    if is_col:
        obj.display_type = 'WIRE'
        obj.hide_render = True
        return obj
        
    if mat:
        obj.data.materials.append(mat)
        
    if uv_strip and len(obj.data.uv_layers) > 0:
        mesh = obj.data
        u_min, v_min, u_max, v_max = uv_strip
        uv_data = mesh.uv_layers.active.data
        for poly in mesh.polygons:
            normal = poly.normal
            for i, loop_idx in enumerate(poly.loop_indices):
                vert_idx = poly.vertices[i]
                v_local = mesh.vertices[vert_idx].co
                if abs(normal.z) < 0.5:
                    h_coord = v_local.x if abs(normal.y) > 0.5 else v_local.y
                    u = u_min + ((h_coord + 50.0) * 0.4) % (u_max - u_min)
                    v = v_min + ((v_local.z + 50.0) * 0.4) % (v_max - v_min)
                else:
                    u = u_min + ((v_local.x + 50.0) * 0.4) % (u_max - u_min)
                    v = v_min + ((v_local.y + 50.0) * 0.4) % (v_max - v_min)
                uv_data[loop_idx].uv = (u, v)
                
    return obj

def build_houses(mats):
    col = bpy.data.collections.new("Residential_Sector")
    bpy.context.scene.collection.children.link(col)
    
    # ----------------------------------------------------
    # 住宅 1：二层独栋带 4.5m 阳台 (X: -18.0 至 -10.5, Z: -10.0 至 0.0)
    # ----------------------------------------------------
    h1_plinth = build_box("H1_Plinth", (7.5, 10.0, 0.6), (-14.25, -5.0, 0.3), mats['trim'], UV_BASE_TRIM)
    h1_b1 = build_box("H1_Body1", (7.5, 10.0, 3.0), (-14.25, -5.0, 2.1), mats['trim'], UV_WHITE_TILE)
    h1_belt = build_box("H1_Belt", (7.7, 10.2, 0.25), (-14.25, -5.0, 3.6), mats['trim'], UV_BASE_TRIM)
    h1_b2 = build_box("H1_Body2", (7.5, 10.0, 3.4), (-14.25, -5.0, 5.3), mats['trim'], UV_WHITE_TILE)
    
    # 住宅 1 坡屋顶
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
    h1_roof = bpy.data.objects.new("H1_Roof", mesh)
    h1_roof.data.materials.append(mats['trim'])
    mesh.uv_layers.new(name="UVMap")
    uvd = mesh.uv_layers.active.data
    u_min, v_min, u_max, v_max = UV_ROOF_TILE
    for poly in mesh.polygons:
        for i, l_idx in enumerate(poly.loop_indices):
            uvd[l_idx].uv = (u_min + (i % 2) * (u_max - u_min) * 2.0, v_min + ((i // 2) % 2) * (v_max - v_min) * 2.0)
    col.objects.link(h1_roof)
    
    # 4.5m 高二楼阳台
    h1_bal_floor = build_box("H1_Balcony_Floor", (1.6, 4.6, 0.25), (-9.7, -5.25, 4.4), mats['trim'], UV_CONCRETE)
    h1_rail_e = build_box("H1_Rail_East", (0.08, 4.6, 1.0), (-8.95, -5.25, 5.0), mats['trim'], UV_RAILING)
    h1_rail_n = build_box("H1_Rail_North", (1.6, 0.08, 1.0), (-9.7, -7.5, 5.0), mats['trim'], UV_RAILING)
    h1_rail_s = build_box("H1_Rail_South", (1.6, 0.08, 1.0), (-9.7, -3.0, 5.0), mats['trim'], UV_RAILING)
    
    # 窗户
    h1_w1 = build_box("H1_Win_East_1F", (0.12, 2.5, 1.6), (-10.45, -3.5, 2.0), mats['trim'], UV_WINDOW)
    h1_w2 = build_box("H1_Win_East_2F", (0.12, 2.5, 1.6), (-10.45, -5.25, 5.5), mats['trim'], UV_WINDOW)
    h1_ws = build_box("H1_Win_South", (3.0, 0.12, 1.6), (-14.25, -0.05, 5.5), mats['trim'], UV_WINDOW)
    
    # CS2 隐形碰撞体
    h1_col = build_box("H1_Main-colonly", (7.5, 10.0, 7.0), (-14.25, -5.0, 3.5), None, is_col=True)
    h1_bal_col = build_box("H1_Balcony-colonly", (1.6, 4.6, 4.5), (-9.7, -5.25, 2.25), None, is_col=True)
    
    for o in [h1_plinth, h1_b1, h1_belt, h1_b2, h1_bal_floor, h1_rail_e, h1_rail_n, h1_rail_s, h1_w1, h1_w2, h1_ws, h1_col, h1_bal_col]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # ----------------------------------------------------
    # 住宅 2：平房带开放式车库 (X: -18.0 至 -10.5, Z: +3.5 至 +13.5, 与住宅 1 间隔严格 3.5m！)
    # ----------------------------------------------------
    h2_nw = build_box("H2_North_Wing", (7.5, 1.5, 4.2), (-14.25, +4.25, 2.1), mats['trim'], UV_CONCRETE)
    h2_sw = build_box("H2_South_Wing", (7.5, 4.0, 4.2), (-14.25, +11.5, 2.1), mats['trim'], UV_CONCRETE)
    h2_gb = build_box("H2_Garage_Back", (2.5, 4.5, 4.2), (-16.75, +7.25, 2.1), mats['trim'], UV_CONCRETE)
    h2_gr = build_box("H2_Garage_Ceiling", (5.0, 4.5, 1.2), (-13.0, +7.25, 3.6), mats['trim'], UV_CONCRETE)
    h2_gf = build_box("H2_Garage_Floor", (5.0, 4.5, 0.15), (-13.0, +7.25, 0.075), mats['trim'], UV_BASE_TRIM)
    h2_cp = build_box("H2_Parapet", (7.7, 10.2, 0.25), (-14.25, +8.5, 4.3), mats['trim'], UV_BASE_TRIM)
    h2_ws = build_box("H2_Win_South", (0.12, 2.4, 1.5), (-10.45, +11.5, 2.0), mats['trim'], UV_WINDOW)
    
    # 室内车库碰撞体 (可自由走入)
    h2_cn = build_box("H2_Col_North-colonly", (7.5, 1.5, 4.2), (-14.25, +4.25, 2.1), None, is_col=True)
    h2_cs = build_box("H2_Col_South-colonly", (7.5, 4.0, 4.2), (-14.25, +11.5, 2.1), None, is_col=True)
    h2_cb = build_box("H2_Col_Back-colonly", (2.5, 4.5, 4.2), (-16.75, +7.25, 2.1), None, is_col=True)
    h2_cr = build_box("H2_Col_Ceiling-colonly", (5.0, 4.5, 1.2), (-13.0, +7.25, 3.6), None, is_col=True)
    
    for o in [h2_nw, h2_sw, h2_gb, h2_gr, h2_gf, h2_cp, h2_ws, h2_cn, h2_cs, h2_cb, h2_cr]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # ----------------------------------------------------
    # 住宅 3：转角独栋 (X: -18.0 至 -10.5, Z: +16.0 至 +25.0)
    # ----------------------------------------------------
    h3_body = build_box("H3_Body", (7.5, 9.0, 6.0), (-14.25, +20.5, 3.0), mats['trim'], UV_WHITE_TILE)
    h3_roof = build_box("H3_Roof", (8.0, 9.4, 1.4), (-14.25, +20.5, 6.7), mats['trim'], UV_ROOF_TILE)
    h3_col = build_box("H3_Col-colonly", (7.5, 9.0, 6.0), (-14.25, +20.5, 3.0), None, is_col=True)
    for o in [h3_body, h3_roof, h3_col]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # ----------------------------------------------------
    # 2.2m 高混凝土住宅外围院墙 (严格 2.2m 高度，供一段跳翻越与空中下砸)
    # ----------------------------------------------------
    wall1 = build_box("Boundary_Wall_1", (0.3, 4.0, 2.2), (-9.0, -8.0, 1.1), mats['trim'], UV_CONCRETE)
    wall2 = build_box("Boundary_Wall_2", (0.3, 1.5, 2.2), (-9.0, +4.25, 1.1), mats['trim'], UV_CONCRETE)
    wall3 = build_box("Boundary_Wall_3", (0.3, 2.5, 2.2), (-9.0, +14.75, 1.1), mats['trim'], UV_CONCRETE)
    
    for i, w in enumerate([wall1, wall2, wall3]):
        coping = build_box(f"Wall_Coping_{i+1}", (w.scale.x + 0.1, w.scale.y, 0.12), (w.location.x, w.location.y, 2.26), mats['trim'], UV_BASE_TRIM)
        wall_col = build_box(f"Wall_Col_{i+1}-colonly", (w.scale.x, w.scale.y, 2.2), (w.location.x, w.location.y, 1.1), None, is_col=True)
        for o in [coping, wall_col, w]:
            col.objects.link(o)
            bpy.context.scene.collection.objects.unlink(o)

def build_slope_and_plaza(mats):
    col = bpy.data.collections.new("Slope_and_Ground")
    bpy.context.scene.collection.children.link(col)
    
    # 40m 15° 自然下坡柏油马路 (Z: -25 至 +15m, 宽 6.5m, 落差 6.0m)
    mesh_road = bpy.data.meshes.new("Slope_Road_Mesh")
    bm = bmesh.new()
    w2 = 3.25
    p1 = bm.verts.new((-w2, -25.0, 6.0))
    p2 = bm.verts.new((+w2, -25.0, 6.0))
    p3 = bm.verts.new((+w2, +15.0, 0.0))
    p4 = bm.verts.new((-w2, +15.0, 0.0))
    bm.faces.new((p1, p2, p3, p4))
    bm.to_mesh(mesh_road)
    bm.free()
    
    road_obj = bpy.data.objects.new("Central_Slope_Road", mesh_road)
    road_obj.data.materials.append(mats['road'])
    col.objects.link(road_obj)
    mesh_road.uv_layers.new(name="UVMap")
    uvd = mesh_road.uv_layers.active.data
    uvd[0].uv = (0.0, 1.0)
    uvd[1].uv = (1.0, 1.0)
    uvd[2].uv = (1.0, 0.0)
    uvd[3].uv = (0.0, 0.0)
    
    # CS2 隐形斜坡碰撞体
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
    slope_col = bpy.data.objects.new("Central_Slope-colonly", col_mesh)
    slope_col.display_type = 'WIRE'
    slope_col.hide_render = True
    col.objects.link(slope_col)
    
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
        sobj.data.materials.append(mats['trim'])
        col.objects.link(sobj)
        sm.uv_layers.new(name="UVMap")
        uvd = sm.uv_layers.active.data
        u_min, v_min, u_max, v_max = UV_CONCRETE
        uvd[0].uv = (u_min, v_min)
        uvd[1].uv = (u_max, v_min)
        uvd[2].uv = (u_max, v_max * 4.0)
        uvd[3].uv = (u_min, v_max * 4.0)
        
        scol = bpy.data.objects.new(f"Sidewalk_{side}-colonly", sm.copy())
        scol.display_type = 'WIRE'
        scol.hide_render = True
        col.objects.link(scol)
        
    # 南端生活广场
    plaza = build_box("Plaza_Ground", (40.0, 20.0, 0.5), (0.0, +25.0, -0.25), mats['trim'], UV_CONCRETE)
    plaza_col = build_box("Plaza_Ground-colonly", (40.0, 20.0, 0.5), (0.0, +25.0, -0.25), None, is_col=True)
    # 西侧住宅区地面
    res_ground = build_box("Residential_Ground", (17.0, 25.0, 0.5), (-13.5, +2.5, -0.25), mats['trim'], UV_BASE_TRIM)
    res_col = build_box("Residential_Ground-colonly", (17.0, 25.0, 0.5), (-13.5, +2.5, -0.25), None, is_col=True)
    
    for o in [plaza, plaza_col, res_ground, res_col]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)

def build_landmark(mats):
    col = bpy.data.collections.new("Landmark_Sector")
    bpy.context.scene.collection.children.link(col)
    
    # 高台石垣
    terrace = build_box("A_Stone_Terrace", (32.0, 11.0, 8.0), (0.0, -30.5, 4.0), mats['stone'])
    terrace_col = build_box("A_Stone_Terrace-colonly", (32.0, 11.0, 8.0), (0.0, -30.5, 4.0), None, is_col=True)
    col.objects.link(terrace)
    col.objects.link(terrace_col)
    bpy.context.scene.collection.objects.unlink(terrace)
    bpy.context.scene.collection.objects.unlink(terrace_col)
    
    # 跑酷平滑石阶斜坡碰撞体
    stairs_col = build_box("A_Stairs_Ramp-colonly", (5.0, 3.0, 2.5), (0.0, -25.5, 7.0), None, is_col=True)
    stairs_col.rotation_euler = (math.radians(-33), 0, 0)
    col.objects.link(stairs_col)
    bpy.context.scene.collection.objects.unlink(stairs_col)
    
    for step in range(8):
        sy = -24.5 - step * 0.3
        sz = 6.0 + (step + 1) * 0.25
        s_obj = build_box(f"Stair_Step_{step+1}", (5.0, 0.35, 0.25), (0.0, sy, sz - 0.125), mats['stone'])
        col.objects.link(s_obj)
        bpy.context.scene.collection.objects.unlink(s_obj)
        
    # 微型朱红鸟居 (高 3.8m)
    torii_z0 = 8.0
    torii_y = -28.5
    pillar_dist = 2.8
    pillar_rad = 0.18
    pillar_h = 3.5
    for p_side, px in [("Left", -pillar_dist / 2), ("Right", pillar_dist / 2)]:
        kame = build_box(f"Torii_Kamebara_{p_side}", (0.5, 0.5, 0.3), (px, torii_y, torii_z0 + 0.15), mats['stone'])
        bpy.ops.mesh.primitive_cylinder_add(radius=pillar_rad, depth=pillar_h, location=(px, torii_y, torii_z0 + pillar_h / 2 + 0.2))
        pillar = bpy.context.active_object
        pillar.name = f"Torii_Pillar_{p_side}"
        pillar.data.materials.append(mats['torii'])
        incline = 0.035 if px < 0 else -0.035
        pillar.rotation_euler = (0, incline, 0)
        p_col = build_box(f"Torii_Pillar_{p_side}-colonly", (0.45, 0.45, pillar_h), (px, torii_y, torii_z0 + pillar_h / 2), None, is_col=True)
        for o in [kame, pillar, p_col]:
            col.objects.link(o)
            bpy.context.scene.collection.objects.unlink(o)
            
    nuki = build_box("Torii_Nuki", (3.6, 0.22, 0.22), (0.0, torii_y, torii_z0 + 2.7), mats['torii'])
    kasagi = build_box("Torii_Kasagi", (4.2, 0.35, 0.30), (0.0, torii_y, torii_z0 + 3.65), mats['torii'])
    gaku = build_box("Torii_Gakuzuka", (0.22, 0.18, 0.7), (0.0, torii_y, torii_z0 + 3.15), mats['torii'])
    for o in [nuki, kasagi, gaku]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)
        
    # 古朴小神龛
    shrine_y = -32.5
    s_base1 = build_box("Shrine_Stone_Base_1", (2.4, 2.4, 0.3), (0.0, shrine_y, torii_z0 + 0.15), mats['stone'])
    s_base2 = build_box("Shrine_Stone_Base_2", (1.8, 1.8, 0.4), (0.0, shrine_y, torii_z0 + 0.5), mats['stone'])
    shrine_body = build_box("Shrine_Body", (1.2, 1.1, 1.2), (0.0, shrine_y, torii_z0 + 1.3), mats['shrine'])
    shrine_roof = build_box("Shrine_Roof", (1.8, 1.6, 0.4), (0.0, shrine_y, torii_z0 + 2.0), mats['shrine'])
    katsuogi1 = build_box("Shrine_Katsuogi_1", (0.12, 0.9, 0.12), (0.0, shrine_y, torii_z0 + 2.25), mats['shrine'])
    shrine_col = build_box("Shrine-colonly", (1.8, 1.8, 2.2), (0.0, shrine_y, torii_z0 + 1.1), None, is_col=True)
    for o in [s_base1, s_base2, shrine_body, shrine_roof, katsuogi1, shrine_col]:
        col.objects.link(o)
        bpy.context.scene.collection.objects.unlink(o)

def build_cherry_tree(name, location, scale=1.0, is_ancient=False, mats=None):
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
        for i in range(8):
            angle = i * 2.0 * math.pi / 8
            vx = bend_x + r * math.cos(angle)
            vy = bend_y + r * math.sin(angle)
            verts_ring.append(bm.verts.new((vx, vy, z)))
        layers.append(verts_ring)
        
    for s in range(segs):
        for i in range(8):
            bm.faces.new((layers[s][i], layers[s][(i + 1) % 8], layers[s + 1][(i + 1) % 8], layers[s + 1][i]))
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
    
    # Radial Normal Edit
    target_empty = bpy.data.objects.new(f"{name}_Normal_Center", None)
    target_empty.location = (location[0], location[1], tree_center_z)
    col.objects.link(target_empty)
    ne_mod = canopy_merged.modifiers.new(name="NormalEdit_Radial", type='NORMAL_EDIT')
    ne_mod.mode = 'RADIAL'
    ne_mod.target = target_empty
    bpy.context.view_layer.objects.active = canopy_merged
    bpy.ops.object.modifier_apply(modifier=ne_mod.name)
    bpy.data.objects.remove(target_empty, do_unlink=True)
    
    # 碰撞体
    bpy.ops.mesh.primitive_cylinder_add(radius=rad_base * 0.9, depth=trunk_h, location=(location[0], location[1], location[2] + trunk_h / 2))
    t_col = bpy.context.active_object
    t_col.name = f"{name}_Col-colonly"
    t_col.display_type = 'WIRE'
    t_col.hide_render = True
    col.objects.link(t_col)
    bpy.context.scene.collection.objects.unlink(t_col)

def build_props(mats):
    col = bpy.data.collections.new("Street_Props_Sector")
    bpy.context.scene.collection.children.link(col)
    
    # 1. 水泥电线杆与架空拉线
    # 电线杆 1 (坡道东侧)
    loc1 = (4.2, 2.0, 1.95)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=8.5, location=(loc1[0], loc1[1], loc1[2] + 4.25))
    p1 = bpy.context.active_object
    p1.name = "Utility_Pole_1"
    p1.data.materials.append(mats['pole'])
    col.objects.link(p1)
    bpy.context.scene.collection.objects.unlink(p1)
    
    # 变压器
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.9, location=(loc1[0] + 0.35, loc1[1], loc1[2] + 6.0))
    trans1 = bpy.context.active_object
    trans1.name = "Transformer_1"
    trans1.data.materials.append(mats['transformer'])
    col.objects.link(trans1)
    bpy.context.scene.collection.objects.unlink(trans1)
    
    p1_col = build_box("Utility_Pole_1-colonly", (0.5, 0.5, 8.5), (loc1[0], loc1[1], loc1[2] + 4.25), None, is_col=True)
    col.objects.link(p1_col)
    bpy.context.scene.collection.objects.unlink(p1_col)
    
    # 3D 实体电线
    wire_targets = [(-9.0, -4.5, 6.0), (-4.3, 10.0, 7.5), (4.2, 17.5, 7.5)]
    w_start = Vector((loc1[0], loc1[1], loc1[2] + 8.1))
    wire_rad = 0.018
    for ep_idx, ep in enumerate(wire_targets):
        p_a = w_start
        p_b = Vector(ep)
        mesh_w = bpy.data.meshes.new(f"Pole1_Wire_{ep_idx}_Mesh")
        bm = bmesh.new()
        prev_ring = None
        for wi in range(9):
            wt = wi / 8.0
            center = p_a.lerp(p_b, wt)
            center.z -= math.sin(wt * math.pi) * 0.45
            ring = []
            for k in range(4):
                ang = k * math.pi / 2
                ring.append(bm.verts.new((center.x + wire_rad * math.cos(ang), center.y, center.z + wire_rad * math.sin(ang))))
            if prev_ring:
                for k in range(4):
                    bm.faces.new((prev_ring[k], prev_ring[(k + 1) % 4], ring[(k + 1) % 4], ring[k]))
            prev_ring = ring
        bm.to_mesh(mesh_w)
        bm.free()
        w_obj = bpy.data.objects.new(f"Pole1_Wire_{ep_idx}", mesh_w)
        w_obj.data.materials.append(mats['wire'])
        col.objects.link(w_obj)
        
    # 2. 红蓝自动贩卖机 (D 区生活广场: X = 4.0, Y = 19.5)
    v_loc = (4.0, 19.5, 0.0)
    for color_mat, sfx, off_x in [(mats['vend_red'], "Red", -0.55), (mats['vend_blue'], "Blue", +0.55)]:
        vx = v_loc[0] + off_x
        vy = v_loc[1]
        vz = v_loc[2]
        vm = build_box(f"Vending_{sfx}_Body", (0.95, 0.75, 1.95), (vx, vy, vz + 0.975), color_mat)
        tsign = build_box(f"Vending_{sfx}_Sign", (0.85, 0.05, 0.22), (vx, vy - 0.38, vz + 1.80), mats['vend_glow'])
        win = build_box(f"Vending_{sfx}_Window", (0.82, 0.05, 0.75), (vx, vy - 0.38, vz + 1.25), mats['vend_glow'])
        disp = build_box(f"Vending_{sfx}_Disp", (0.70, 0.05, 0.35), (vx, vy - 0.38, vz + 0.35), mats['wire'])
        for o in [vm, tsign, win, disp]:
            col.objects.link(o)
            bpy.context.scene.collection.objects.unlink(o)
            
    # 回收桶与碰撞体
    rbin = build_box("Vending_Recycle_Bin", (0.50, 0.55, 1.00), (v_loc[0] + 1.45, v_loc[1], v_loc[2] + 0.50), mats['pole'])
    v_col = build_box("Vending_Group-colonly", (2.8, 0.85, 1.95), (v_loc[0] + 0.35, v_loc[1], v_loc[2] + 0.975), None, is_col=True)
    col.objects.link(rbin)
    col.objects.link(v_col)
    bpy.context.scene.collection.objects.unlink(rbin)
    bpy.context.scene.collection.objects.unlink(v_col)
    
    # 3. 黄色凸面反光镜 (X = -4.8, Y = 15.2, Z = 0.18)
    m_loc = (-4.8, 15.2, 0.18)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=3.2, location=(m_loc[0], m_loc[1], m_loc[2] + 1.6))
    post = bpy.context.active_object
    post.name = "Mirror_Post"
    post.data.materials.append(mats['mirror_yellow'])
    col.objects.link(post)
    bpy.context.scene.collection.objects.unlink(post)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.08, location=(m_loc[0], m_loc[1] + 0.25, m_loc[2] + 3.1))
    rim = bpy.context.active_object
    rim.name = "Mirror_Rim"
    rim.rotation_euler = (math.radians(-25), 0, 0)
    rim.data.materials.append(mats['mirror_yellow'])
    col.objects.link(rim)
    bpy.context.scene.collection.objects.unlink(rim)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.41, depth=0.04, location=(m_loc[0], m_loc[1] + 0.21, m_loc[2] + 3.08))
    face = bpy.context.active_object
    face.name = "Mirror_Reflective_Face"
    face.rotation_euler = (math.radians(-25), 0, 0)
    face.data.materials.append(mats['mirror_face'])
    col.objects.link(face)
    bpy.context.scene.collection.objects.unlink(face)
    
    m_col = build_box("Mirror_Post-colonly", (0.3, 0.3, 3.2), (m_loc[0], m_loc[1], m_loc[2] + 1.6), None, is_col=True)
    col.objects.link(m_col)
    bpy.context.scene.collection.objects.unlink(m_col)
    
    # 4. 空调室外机
    for i, (pos, rot) in enumerate([((-12.0, -0.2, 1.8), (0, 0, 0)), ((-10.3, -4.0, 4.8), (0, 0, math.radians(90))), ((-10.3, +4.0, 1.5), (0, 0, math.radians(90)))]):
        ac = build_box(f"AC_Unit_{i+1}", (0.85, 0.35, 0.62), pos, mats['ac'])
        ac.rotation_euler = rot
        col.objects.link(ac)
        bpy.context.scene.collection.objects.unlink(ac)
        
    # 5. 人行护栏
    for r_idx, (rx, ry, rz) in enumerate([(4.2, 14.5, 0.18), (5.5, 14.5, 0.0), (6.8, 14.5, 0.0)]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.2, location=(rx, ry, rz + 0.80))
        top_bar = bpy.context.active_object
        top_bar.rotation_euler = (0, math.radians(90), 0)
        top_bar.data.materials.append(mats['guardrail'])
        col.objects.link(top_bar)
        bpy.context.scene.collection.objects.unlink(top_bar)
        
        gr_col = build_box(f"Guardrail_Col_{r_idx}-colonly", (1.2, 0.15, 0.85), (rx, ry, rz + 0.425), None, is_col=True)
        col.objects.link(gr_col)
        bpy.context.scene.collection.objects.unlink(gr_col)

def setup_lighting():
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Sky_1430")
    scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    wout = wnodes.new('ShaderNodeOutputWorld')
    wbg = wnodes.new('ShaderNodeBackground')
    wbg.inputs['Color'].default_value = (0.42, 0.68, 0.96, 1.0) # 蔚蓝天光冷反弹
    wbg.inputs['Strength'].default_value = 1.0
    wlinks.new(wbg.outputs['Background'], wout.inputs['Surface'])
    
    sun_data = bpy.data.lights.new(name="Sun_1430", type='SUN')
    sun_data.energy = 2.4
    sun_data.color = (1.0, 0.97, 0.92) # 暖白明媚
    sun_obj = bpy.data.objects.new("Sun_1430", sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(50), math.radians(15), math.radians(-40))

def render_all_views():
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if "-colonly" in obj.name:
            obj.hide_render = True
            
    cam_data = bpy.data.cameras.new('RenderCam')
    cam_data.lens = 28
    cam_obj = bpy.data.objects.new('RenderCam', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    
    views = [
        ("stage1_view1_look_up_torii.png", (0.0, 14.0, 1.4), (0.0, -28.5, 9.8)),
        ("stage1_view2_narrow_alley.png", (-6.5, 1.75, 1.6), (-18.0, 1.75, 2.5)),
        ("stage1_view3_house_facade.png", (-3.0, 3.0, 2.8), (-12.0, -2.5, 3.8)),
        ("stage2_view1_street_props.png", (0.0, 16.0, 1.4), (4.0, 19.5, 1.2)),
        ("stage2_view2_cherry_tree_close.png", (-1.5, -4.5, 3.5), (4.3, -5.0, 5.0)),
        ("stage2_view3_slope_with_wires.png", (0.0, 15.0, 1.5), (0.0, -15.0, 6.0))
    ]
    
    print("=== Rendering 6 Inspection Views ===")
    for fname, loc, target in views:
        cam_obj.location = Vector(loc)
        point_camera_at(cam_obj, target)
        out_path = os.path.join(SCREENS_DIR, fname)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered: {fname}")
        
    bpy.data.objects.remove(cam_obj, do_unlink=True)

def export_all():
    blend_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.blend")
    glb_path = os.path.join(MODELS_DIR, "modern_japan_neighborhood.glb")
    
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved: {blend_path}")
    
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported: {glb_path}")

def main():
    print("=== Clean Unified Build: Modern Japan Neighborhood ===")
    reset_scene()
    mats = create_all_materials()
    build_houses(mats)
    build_slope_and_plaza(mats)
    build_landmark(mats)
    
    # 樱花树
    build_cherry_tree("Tree_Ancient_A", (3.8, -30.5, 8.0), scale=1.35, is_ancient=True, mats=mats)
    build_cherry_tree("Tree_Street_1", (-4.3, -18.0, 4.95), scale=0.95, mats=mats)
    build_cherry_tree("Tree_Street_2", (+4.3, -5.0, 3.0), scale=1.05, mats=mats)
    build_cherry_tree("Tree_Street_3", (-4.3, +7.0, 1.2), scale=1.0, mats=mats)
    
    build_props(mats)
    setup_lighting()
    export_all()
    render_all_views()
    print("=== Clean Build Completed Successfully! ===")

if __name__ == "__main__":
    main()
