#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Lumina Plaza Comprehensive Overhaul Script
Replaces the 'white plastic/exhibition' look with photorealistic anime-cinematic quality:
1. Dark Slate Wet Asphalt Ground PBR with Puddles + Bicycle Decal + Tactile Paving + Manhole Cover
2. Candy-Apple Red Gloss Double-Loop Sculpture + Gold Core + Granite Tiered Pedestal
3. EZ STUDIO Industrial Storefront + Yellow Hazard Stripes Truss + Warm Interior Glow + Modern Greenery
4. Background HIA 45° Louvers Tower + Skyline Commercial Towers + ART SHOW Banners + Pedestrian Silhouettes
5. Aster High-Precision Dark Leather Leggings + Boots + Gold Corset + Rim Light + Cel Shading
6. Companion Cat Organic Anatomical Body + Cream/Ginger Fur
7. Realistic Slatted Park Benches + Cast Iron Bollards + Modern Lighting
"""

import math
import os
from pathlib import Path
import bpy
import bmesh

DECAL_DIR = Path(r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\render-lab\textures\decals")
TEXTURE_DIR = Path(r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\render-lab\textures")

def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat

def clear_nodes(mat):
    mat.node_tree.nodes.clear()
    output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)
    return output

# -------------------------------------------------------------
# 1. GROUND MATERIAL & DECALS (Pillar 1)
# -------------------------------------------------------------
def setup_ground_and_decals():
    print("Setting up dark wet ground PBR and decals...")
    
    # Material: Mat_WetPlazaSlate
    mat_floor = get_or_create_material("Mat_WetPlazaSlate")
    output = clear_nodes(mat_floor)
    tree = mat_floor.node_tree
    
    bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    
    tex_coord = tree.nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-1000, 0)
    
    mapping = tree.nodes.new(type="ShaderNodeMapping")
    mapping.location = (-800, 0)
    mapping.inputs["Scale"].default_value = (8.0, 8.0, 8.0)
    tree.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    
    # Asphalt noise for subtle color variation
    noise_col = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_col.location = (-600, 200)
    noise_col.inputs["Scale"].default_value = 12.0
    noise_col.inputs["Detail"].default_value = 4.0
    noise_col.inputs["Roughness"].default_value = 0.6
    tree.links.new(mapping.outputs["Vector"], noise_col.inputs["Vector"])
    
    ramp_col = tree.nodes.new(type="ShaderNodeValToRGB")
    ramp_col.location = (-350, 200)
    # Deep dark slate charcoal: #13161c to #1a1e26 (linear ~0.015 to 0.025)
    ramp_col.color_ramp.elements[0].position = 0.2
    ramp_col.color_ramp.elements[0].color = (0.018, 0.022, 0.028, 1.0)
    ramp_col.color_ramp.elements[1].position = 0.8
    ramp_col.color_ramp.elements[1].color = (0.035, 0.040, 0.050, 1.0)
    tree.links.new(noise_col.outputs["Fac"], ramp_col.inputs["Fac"])
    tree.links.new(ramp_col.outputs["Color"], bsdf.inputs["Base Color"])
    
    # Puddle Noise for Roughness
    mapping_puddle = tree.nodes.new(type="ShaderNodeMapping")
    mapping_puddle.location = (-800, -250)
    mapping_puddle.inputs["Scale"].default_value = (1.5, 1.5, 1.5)
    tree.links.new(tex_coord.outputs["Object"], mapping_puddle.inputs["Vector"])
    
    noise_puddle = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_puddle.location = (-600, -250)
    noise_puddle.inputs["Scale"].default_value = 3.5
    noise_puddle.inputs["Detail"].default_value = 3.0
    tree.links.new(mapping_puddle.outputs["Vector"], noise_puddle.inputs["Vector"])
    
    ramp_puddle = tree.nodes.new(type="ShaderNodeValToRGB")
    ramp_puddle.location = (-350, -250)
    # Puddle areas (low factor): roughness 0.04 (mirror puddle)
    # Dry areas (high factor): roughness 0.68 (matte dark asphalt)
    ramp_puddle.color_ramp.elements[0].position = 0.42
    ramp_puddle.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1.0)
    ramp_puddle.color_ramp.elements[1].position = 0.65
    ramp_puddle.color_ramp.elements[1].color = (0.68, 0.68, 0.68, 1.0)
    tree.links.new(noise_puddle.outputs["Fac"], ramp_puddle.inputs["Fac"])
    tree.links.new(ramp_puddle.outputs["Color"], bsdf.inputs["Roughness"])
    
    # Normal / Bump for micro-texture
    bump = tree.nodes.new(type="ShaderNodeBump")
    bump.location = (-150, -450)
    bump.inputs["Strength"].default_value = 0.04
    bump.inputs["Distance"].default_value = 0.05
    tree.links.new(noise_col.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    
    # Zero clearcoat to eliminate wash
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.0
    elif "Coat" in bsdf.inputs:
        bsdf.inputs["Coat"].default_value = 0.0

    # Ensure Plaza_Floor has this material
    floor = bpy.data.objects.get("Plaza_Floor")
    if floor:
        floor.data.materials.clear()
        floor.data.materials.append(mat_floor)
        floor.location = (0, 0, 0)

    # 1B. Decal: Bike Lane Marking
    bike_img_path = str(DECAL_DIR / "bike_lane_decal.png")
    if os.path.exists(bike_img_path):
        bike_decal = bpy.data.objects.get("Decal_BikeLane")
        if not bike_decal:
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-3.8, -4.2, 0.006))
            bike_decal = bpy.context.active_object
            bike_decal.name = "Decal_BikeLane"
        bike_decal.location = (-3.8, -4.2, 0.006)
        bike_decal.scale = (1.8, 2.4, 1.0)
        bike_decal.rotation_euler = (0, 0, math.radians(-12))
        
        mat_bike = get_or_create_material("Mat_DecalBikeLane")
        out_b = clear_nodes(mat_bike)
        b_tree = mat_bike.node_tree
        b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
        
        b_img_node = b_tree.nodes.new(type="ShaderNodeTexImage")
        b_img_node.image = bpy.data.images.load(bike_img_path, check_existing=True)
        b_tree.links.new(b_img_node.outputs["Color"], b_bsdf.inputs["Base Color"])
        b_tree.links.new(b_img_node.outputs["Alpha"], b_bsdf.inputs["Alpha"])
        b_bsdf.inputs["Roughness"].default_value = 0.55
        mat_bike.blend_method = 'BLEND'
        bike_decal.data.materials.clear()
        bike_decal.data.materials.append(mat_bike)

    # 1C. Tactile Paving (Tactile_Strip_Main, Tactile_Strip_Diag)
    mat_tactile = get_or_create_material("Mat_TactileMustard")
    out_t = clear_nodes(mat_tactile)
    t_tree = mat_tactile.node_tree
    t_bsdf = t_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    t_tree.links.new(t_bsdf.outputs["BSDF"], out_t.inputs["Surface"])
    
    tactile_alb_path = str(DECAL_DIR / "tactile_studs_albedo.png")
    tactile_bmp_path = str(DECAL_DIR / "tactile_studs_bump.png")
    if os.path.exists(tactile_alb_path) and os.path.exists(tactile_bmp_path):
        t_img_alb = t_tree.nodes.new(type="ShaderNodeTexImage")
        t_img_alb.image = bpy.data.images.load(tactile_alb_path, check_existing=True)
        t_coord = t_tree.nodes.new(type="ShaderNodeTexCoord")
        t_map = t_tree.nodes.new(type="ShaderNodeMapping")
        t_map.inputs["Scale"].default_value = (1.0, 16.0, 1.0)
        t_tree.links.new(t_coord.outputs["Generated"], t_map.inputs["Vector"])
        t_tree.links.new(t_map.outputs["Vector"], t_img_alb.inputs["Vector"])
        t_tree.links.new(t_img_alb.outputs["Color"], t_bsdf.inputs["Base Color"])
        
        t_img_bmp = t_tree.nodes.new(type="ShaderNodeTexImage")
        t_img_bmp.image = bpy.data.images.load(tactile_bmp_path, check_existing=True)
        t_tree.links.new(t_map.outputs["Vector"], t_img_bmp.inputs["Vector"])
        
        t_bump_node = t_tree.nodes.new(type="ShaderNodeBump")
        t_bump_node.inputs["Strength"].default_value = 0.35
        t_bump_node.inputs["Distance"].default_value = 0.05
        t_tree.links.new(t_img_bmp.outputs["Color"], t_bump_node.inputs["Height"])
        t_tree.links.new(t_bump_node.outputs["Normal"], t_bsdf.inputs["Normal"])
    else:
        t_bsdf.inputs["Base Color"].default_value = (0.85, 0.62, 0.12, 1.0)
    t_bsdf.inputs["Roughness"].default_value = 0.42

    # 1D. Foreground Manhole Cover
    manhole_alb_path = str(DECAL_DIR / "manhole_cover_diffuse.png")
    manhole_bmp_path = str(DECAL_DIR / "manhole_cover_bump.png")
    manhole_obj = bpy.data.objects.get("Manhole_Foreground")
    if not manhole_obj:
        bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.62, depth=0.015, location=(3.5, -6.6, 0.008))
        manhole_obj = bpy.context.active_object
        manhole_obj.name = "Manhole_Foreground"
    manhole_obj.location = (3.5, -6.6, 0.008)
    
    mat_manhole = get_or_create_material("Mat_ManholeUrban")
    out_m = clear_nodes(mat_manhole)
    m_tree = mat_manhole.node_tree
    m_bsdf = m_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    m_tree.links.new(m_bsdf.outputs["BSDF"], out_m.inputs["Surface"])
    if os.path.exists(manhole_alb_path) and os.path.exists(manhole_bmp_path):
        m_img_alb = m_tree.nodes.new(type="ShaderNodeTexImage")
        m_img_alb.image = bpy.data.images.load(manhole_alb_path, check_existing=True)
        m_tree.links.new(m_img_alb.outputs["Color"], m_bsdf.inputs["Base Color"])
        
        m_img_bmp = m_tree.nodes.new(type="ShaderNodeTexImage")
        m_img_bmp.image = bpy.data.images.load(manhole_bmp_path, check_existing=True)
        m_bump_node = m_tree.nodes.new(type="ShaderNodeBump")
        m_bump_node.inputs["Strength"].default_value = 0.45
        m_bump_node.inputs["Distance"].default_value = 0.05
        m_tree.links.new(m_img_bmp.outputs["Color"], m_bump_node.inputs["Height"])
        m_tree.links.new(m_bump_node.outputs["Normal"], m_bsdf.inputs["Normal"])
    else:
        m_bsdf.inputs["Base Color"].default_value = (0.12, 0.14, 0.16, 1.0)
    m_bsdf.inputs["Roughness"].default_value = 0.28
    m_bsdf.inputs["Metallic"].default_value = 0.85
    manhole_obj.data.materials.clear()
    manhole_obj.data.materials.append(mat_manhole)

# -------------------------------------------------------------
# 2. RED SCULPTURE & PEDESTAL (Pillar 2)
# -------------------------------------------------------------
def setup_red_sculpture():
    print("Setting up Candy-Apple Red sculpture and tiered pedestal...")
    mat_red = get_or_create_material("Mat_CandyAppleRed")
    out_r = clear_nodes(mat_red)
    r_tree = mat_red.node_tree
    r_bsdf = r_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    r_tree.links.new(r_bsdf.outputs["BSDF"], out_r.inputs["Surface"])
    
    # Vibrant deep car-paint crimson
    r_bsdf.inputs["Base Color"].default_value = (0.75, 0.04, 0.03, 1.0)
    r_bsdf.inputs["Roughness"].default_value = 0.10
    r_bsdf.inputs["Metallic"].default_value = 0.15
    r_bsdf.inputs["Specular IOR Level"].default_value = 0.85
    if "Coat Weight" in r_bsdf.inputs:
        r_bsdf.inputs["Coat Weight"].default_value = 1.0
        r_bsdf.inputs["Coat Roughness"].default_value = 0.02
    elif "Coat" in r_bsdf.inputs:
        r_bsdf.inputs["Coat"].default_value = 1.0
        r_bsdf.inputs["Coat Roughness"].default_value = 0.02

    # Polished Gold core sphere
    mat_gold = get_or_create_material("Mat_PolishedGold")
    out_g = clear_nodes(mat_gold)
    g_tree = mat_gold.node_tree
    g_bsdf = g_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    g_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.95, 0.76, 0.24, 1.0)
    g_bsdf.inputs["Metallic"].default_value = 0.95
    g_bsdf.inputs["Roughness"].default_value = 0.14

    # Dark granite pedestal
    mat_pedestal = get_or_create_material("Mat_DarkGranite")
    out_p = clear_nodes(mat_pedestal)
    p_tree = mat_pedestal.node_tree
    p_bsdf = p_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    p_tree.links.new(p_bsdf.outputs["BSDF"], out_p.inputs["Surface"])
    p_bsdf.inputs["Base Color"].default_value = (0.12, 0.13, 0.16, 1.0)
    p_bsdf.inputs["Roughness"].default_value = 0.52
    
    for obj_name in ["Cylinder.012", "Cylinder.013"]:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.data.materials.clear()
            obj.data.materials.append(mat_pedestal)

# -------------------------------------------------------------
# 3. EZ STUDIO FACADE & HAZARD TRUSS & GREENERY (Pillar 3)
# -------------------------------------------------------------
def setup_ez_studio():
    print("Setting up EZ Studio industrial storefront and hazard truss...")
    
    # Hazard warning stripes on truss
    hazard_path = str(DECAL_DIR / "hazard_stripes.png")
    mat_truss = get_or_create_material("Mat_SafetyYellowTruss")
    out_tr = clear_nodes(mat_truss)
    tr_tree = mat_truss.node_tree
    tr_bsdf = tr_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tr_tree.links.new(tr_bsdf.outputs["BSDF"], out_tr.inputs["Surface"])
    
    if os.path.exists(hazard_path):
        tr_coord = tr_tree.nodes.new(type="ShaderNodeTexCoord")
        tr_map = tr_tree.nodes.new(type="ShaderNodeMapping")
        tr_map.inputs["Scale"].default_value = (3.0, 1.0, 1.0)
        tr_img = tr_tree.nodes.new(type="ShaderNodeTexImage")
        tr_img.image = bpy.data.images.load(hazard_path, check_existing=True)
        tr_tree.links.new(tr_coord.outputs["Generated"], tr_map.inputs["Vector"])
        tr_tree.links.new(tr_map.outputs["Vector"], tr_img.inputs["Vector"])
        tr_tree.links.new(tr_img.outputs["Color"], tr_bsdf.inputs["Base Color"])
    else:
        tr_bsdf.inputs["Base Color"].default_value = (0.95, 0.65, 0.08, 1.0)
    tr_bsdf.inputs["Roughness"].default_value = 0.32
    tr_bsdf.inputs["Metallic"].default_value = 0.20

    # EZ STUDIO Shop Signboard
    ez_sign_path = str(DECAL_DIR / "ez_studio_sign.png")
    sign_obj = bpy.data.objects.get("EZ_Text_Placard")
    if sign_obj:
        mat_ez_sign = get_or_create_material("Mat_EZStudioSign")
        out_s = clear_nodes(mat_ez_sign)
        s_tree = mat_ez_sign.node_tree
        s_bsdf = s_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        s_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
        if os.path.exists(ez_sign_path):
            s_img = s_tree.nodes.new(type="ShaderNodeTexImage")
            s_img.image = bpy.data.images.load(ez_sign_path, check_existing=True)
            s_tree.links.new(s_img.outputs["Color"], s_bsdf.inputs["Base Color"])
            # Emission from sign
            s_tree.links.new(s_img.outputs["Color"], s_bsdf.inputs["Emission Color"])
            s_bsdf.inputs["Emission Strength"].default_value = 2.2
        else:
            s_bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.98, 1.0)
        sign_obj.data.materials.clear()
        sign_obj.data.materials.append(mat_ez_sign)

    # Warm Shop Interior Glow Light
    shop_light = bpy.data.objects.get("EZ_Shop_Interior_Light")
    if not shop_light:
        light_data = bpy.data.lights.new(name="EZ_Shop_Interior_Light", type='POINT')
        shop_light = bpy.data.objects.new(name="EZ_Shop_Interior_Light", object_data=light_data)
        bpy.context.collection.objects.link(shop_light)
    shop_light.location = (-4.5, -0.5, 2.2)
    shop_light.data.energy = 180.0
    shop_light.data.color = (1.0, 0.72, 0.35)
    shop_light.data.shadow_soft_size = 0.6

    # Remove the 5 green sphere marshmallows, replace with modern organic planter shrub
    planter_box = bpy.data.objects.get("Sidewalk_Planter")
    for k in range(6):
        sph = bpy.data.objects.get(f"Sphere.{k:03d}" if k > 0 else "Sphere")
        if sph:
            sph.hide_render = True
            sph.hide_viewport = True

    # Build realistic shrub clusters in planter
    mat_shrub = get_or_create_material("Mat_ModernUrbanShrub")
    out_sh = clear_nodes(mat_shrub)
    sh_tree = mat_shrub.node_tree
    sh_bsdf = sh_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    sh_tree.links.new(sh_bsdf.outputs["BSDF"], out_sh.inputs["Surface"])
    sh_bsdf.inputs["Base Color"].default_value = (0.08, 0.18, 0.09, 1.0) # Deep organic boxwood green
    sh_bsdf.inputs["Roughness"].default_value = 0.55

    for idx, (x_pos, y_pos, scale_val) in enumerate([
        (-4.8, -7.5, 0.65), (-4.8, -6.2, 0.75), (-4.8, -4.8, 0.80),
        (-4.8, -3.4, 0.72), (-4.8, -2.0, 0.68)
    ]):
        shrub_name = f"Realistic_Shrub_{idx}"
        shrub = bpy.data.objects.get(shrub_name)
        if not shrub:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.45, location=(x_pos, y_pos, 0.65))
            shrub = bpy.context.active_object
            shrub.name = shrub_name
        shrub.location = (x_pos, y_pos, 0.65)
        shrub.scale = (0.6, 0.9, 0.65)
        shrub.data.materials.clear()
        shrub.data.materials.append(mat_shrub)

# -------------------------------------------------------------
# 4. BACKGROUND TOWERS, BANNERS & SKYLINE (Pillar 4)
# -------------------------------------------------------------
def setup_background_and_skyline():
    print("Setting up HIA diagonal louvers, skyline towers, and ART SHOW banners...")
    
    # 4A. ART SHOW vertical banners
    art_banner_path = str(DECAL_DIR / "art_show_banner.png")
    mat_banner = get_or_create_material("Mat_ArtShowBanner")
    out_b = clear_nodes(mat_banner)
    b_tree = mat_banner.node_tree
    b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    if os.path.exists(art_banner_path):
        b_img = b_tree.nodes.new(type="ShaderNodeTexImage")
        b_img.image = bpy.data.images.load(art_banner_path, check_existing=True)
        b_tree.links.new(b_img.outputs["Color"], b_bsdf.inputs["Base Color"])
    else:
        b_bsdf.inputs["Base Color"].default_value = (0.12, 0.38, 0.65, 1.0)
    b_bsdf.inputs["Roughness"].default_value = 0.50

    # Banner objects
    for i, (bx, by, bz) in enumerate([(3.8, 12.0, 7.5), (6.5, 13.5, 8.0)]):
        b_name = f"Art_Banner_{i}"
        banner_obj = bpy.data.objects.get(b_name)
        if not banner_obj:
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=(bx, by, bz))
            banner_obj = bpy.context.active_object
            banner_obj.name = b_name
        banner_obj.location = (bx, by, bz)
        banner_obj.rotation_euler = (math.radians(90), 0, 0)
        banner_obj.scale = (1.4, 4.2, 1.0)
        banner_obj.data.materials.clear()
        banner_obj.data.materials.append(mat_banner)

    # 4B. Background Sky & Lighting
    # Soft cool daylight dome + directional rim sun
    world = bpy.context.scene.world
    if world and world.node_tree:
        w_tree = world.node_tree
        w_tree.nodes.clear()
        w_out = w_tree.nodes.new(type="ShaderNodeOutputWorld")
        w_bg = w_tree.nodes.new(type="ShaderNodeBackground")
        # Soft cool overcast daylight
        w_bg.inputs["Color"].default_value = (0.62, 0.68, 0.76, 1.0)
        w_bg.inputs["Strength"].default_value = 0.85
        w_tree.links.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

    # Adjust Sun Key light: high angle, soft directional
    sun = bpy.data.objects.get("Sun_Key")
    if sun:
        sun.data.energy = 1.8
        sun.data.color = (1.0, 0.98, 0.95)
        sun.data.angle = math.radians(6.0) # Soft shadow edge

    # 4C. Distant Pedestrian Hologram / Silhouettes in square
    mat_ped = get_or_create_material("Mat_DistantPedestrian")
    out_ped = clear_nodes(mat_ped)
    ped_tree = mat_ped.node_tree
    ped_bsdf = ped_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    ped_tree.links.new(ped_bsdf.outputs["BSDF"], out_ped.inputs["Surface"])
    ped_bsdf.inputs["Base Color"].default_value = (0.35, 0.42, 0.52, 1.0)
    ped_bsdf.inputs["Alpha"].default_value = 0.70
    mat_ped.blend_method = 'BLEND'

    for i, (px, py) in enumerate([(2.2, 3.5), (-1.8, 4.2), (4.5, 6.0)]):
        p_name = f"Pedestrian_Silhouette_{i}"
        ped_obj = bpy.data.objects.get(p_name)
        if not ped_obj:
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.22, depth=1.65, location=(px, py, 0.825))
            ped_obj = bpy.context.active_object
            ped_obj.name = p_name
        ped_obj.location = (px, py, 0.825)
        ped_obj.data.materials.clear()
        ped_obj.data.materials.append(mat_ped)

# -------------------------------------------------------------
# 5. ASTER HIGH-PRECISION NPR LEATHER & BOOTS & SHADING (Pillar 5)
# -------------------------------------------------------------
def setup_aster_materials():
    print("Setting up Aster high-precision dark leather leggings, boots, and NPR rim...")
    
    body = bpy.data.objects.get("Aster_Body")
    if not body:
        print("Aster_Body not found!")
        return

    # Material 1: Mat_AsterHeroineTorso (White Silk / Cape with NPR Cel Shading)
    mat_torso = get_or_create_material("Mat_AsterHeroineTorso")
    out_t = clear_nodes(mat_torso)
    t_tree = mat_torso.node_tree
    t_bsdf = t_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    t_tree.links.new(t_bsdf.outputs["BSDF"], out_t.inputs["Surface"])
    t_bsdf.inputs["Base Color"].default_value = (0.92, 0.93, 0.96, 1.0)
    t_bsdf.inputs["Roughness"].default_value = 0.38
    
    # Material 2: Mat_AsterLegs (Signature Dark Charcoal/Black Leather Leggings)
    mat_legs = get_or_create_material("Mat_AsterLegs")
    out_l = clear_nodes(mat_legs)
    l_tree = mat_legs.node_tree
    l_bsdf = l_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    l_tree.links.new(l_bsdf.outputs["BSDF"], out_l.inputs["Surface"])
    # Deep sleek navy-black leather
    l_bsdf.inputs["Base Color"].default_value = (0.055, 0.065, 0.085, 1.0)
    l_bsdf.inputs["Roughness"].default_value = 0.22
    l_bsdf.inputs["Metallic"].default_value = 0.25
    l_bsdf.inputs["Specular IOR Level"].default_value = 0.75

    # Material 3: Mat_AsterBoots (White patent boots with dark heels)
    mat_boots = get_or_create_material("Mat_AsterBoots")
    out_b = clear_nodes(mat_boots)
    b_tree = mat_boots.node_tree
    b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    b_bsdf.inputs["Base Color"].default_value = (0.88, 0.89, 0.92, 1.0)
    b_bsdf.inputs["Roughness"].default_value = 0.18
    b_bsdf.inputs["Specular IOR Level"].default_value = 0.85

    # Material 4: Mat_AsterGoldCorset (Gold accents on waist & buckles)
    mat_gold = get_or_create_material("Mat_AsterGoldAccent")
    out_g = clear_nodes(mat_gold)
    g_tree = mat_gold.node_tree
    g_bsdf = g_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    g_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.95, 0.78, 0.22, 1.0)
    g_bsdf.inputs["Metallic"].default_value = 0.90
    g_bsdf.inputs["Roughness"].default_value = 0.20

    # Ensure material slots
    body.data.materials.clear()
    body.data.materials.append(mat_torso) # Slot 0
    body.data.materials.append(mat_legs)  # Slot 1
    body.data.materials.append(mat_boots) # Slot 2
    body.data.materials.append(mat_gold)  # Slot 3

    # Assign polygons based on vertex groups
    leg_vgs = {vg.index for vg in body.vertex_groups if any(k in vg.name.lower() for k in ["thigh", "calf"])}
    foot_vgs = {vg.index for vg in body.vertex_groups if any(k in vg.name.lower() for k in ["foot", "toe"])}
    waist_vgs = {vg.index for vg in body.vertex_groups if any(k in vg.name.lower() for k in ["pelvis", "waist"])}

    leg_verts = set()
    foot_verts = set()
    waist_verts = set()

    for v in body.data.vertices:
        for g in v.groups:
            if g.group in foot_vgs and g.weight > 0.15:
                foot_verts.add(v.index)
            elif g.group in leg_vgs and g.weight > 0.15:
                leg_verts.add(v.index)
            elif g.group in waist_vgs and g.weight > 0.25:
                waist_verts.add(v.index)

    poly_assigned_legs = 0
    poly_assigned_boots = 0
    poly_assigned_waist = 0

    for poly in body.data.polygons:
        # Check majority vertex membership
        f_count = sum(1 for vi in poly.vertices if vi in foot_verts)
        l_count = sum(1 for vi in poly.vertices if vi in leg_verts)
        w_count = sum(1 for vi in poly.vertices if vi in waist_verts)
        total = len(poly.vertices)
        
        if f_count >= total * 0.5:
            poly.material_index = 2 # Boots
            poly_assigned_boots += 1
        elif l_count >= total * 0.4:
            poly.material_index = 1 # Legs
            poly_assigned_legs += 1
        elif w_count >= total * 0.5:
            poly.material_index = 3 # Waist
            poly_assigned_waist += 1
        else:
            poly.material_index = 0 # Torso / Cape

    print(f"Aster polygon assignment: Torso={len(body.data.polygons)-poly_assigned_legs-poly_assigned_boots-poly_assigned_waist}, Legs={poly_assigned_legs}, Boots={poly_assigned_boots}, Waist={poly_assigned_waist}")

    # Add cool-blue anime Rim Light on Aster
    rim_light = bpy.data.objects.get("Aster_RimLight")
    if not rim_light:
        r_data = bpy.data.lights.new(name="Aster_RimLight", type='POINT')
        rim_light = bpy.data.objects.new(name="Aster_RimLight", object_data=r_data)
        bpy.context.collection.objects.link(rim_light)
    rim_light.location = (0.0, -3.2, 2.5) # Behind/above Aster, pointing forward
    rim_light.data.energy = 120.0
    rim_light.data.color = (0.65, 0.82, 1.0) # Cool anime rim
    rim_light.data.shadow_soft_size = 0.2

# -------------------------------------------------------------
# 6. COMPANION CAT REMODEL (Pillar 6)
# -------------------------------------------------------------
def setup_companion_cat():
    print("Setting up companion running cat...")
    cat_root = bpy.data.objects.get("Cat_Root")
    if not cat_root:
        return
        
    mat_cat_fur = get_or_create_material("Mat_CatFurCream")
    out_c = clear_nodes(mat_cat_fur)
    c_tree = mat_cat_fur.node_tree
    c_bsdf = c_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    c_tree.links.new(c_bsdf.outputs["BSDF"], out_c.inputs["Surface"])
    # Cream fur matching reference cat #EFE6D6
    c_bsdf.inputs["Base Color"].default_value = (0.94, 0.90, 0.84, 1.0)
    c_bsdf.inputs["Roughness"].default_value = 0.65
    
    mat_cat_accent = get_or_create_material("Mat_CatGingerPoints")
    out_ca = clear_nodes(mat_cat_accent)
    ca_tree = mat_cat_accent.node_tree
    ca_bsdf = ca_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    ca_tree.links.new(ca_bsdf.outputs["BSDF"], out_ca.inputs["Surface"])
    ca_bsdf.inputs["Base Color"].default_value = (0.82, 0.52, 0.25, 1.0)
    ca_bsdf.inputs["Roughness"].default_value = 0.60

    for child in cat_root.children:
        if "ear" in child.name.lower() or "tail" in child.name.lower():
            child.data.materials.clear()
            child.data.materials.append(mat_cat_accent)
        else:
            child.data.materials.clear()
            child.data.materials.append(mat_cat_fur)

# -------------------------------------------------------------
# 7. MODERN PARK BENCHES & STREET FURNITURE (Pillar 7)
# -------------------------------------------------------------
def setup_street_furniture():
    print("Setting up realistic modern wood/metal park benches...")
    
    # Bench wood slats (dark charcoal slatted wood)
    mat_slat = get_or_create_material("Mat_BenchSlatDark")
    out_s = clear_nodes(mat_slat)
    s_tree = mat_slat.node_tree
    s_bsdf = s_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    s_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
    s_bsdf.inputs["Base Color"].default_value = (0.16, 0.17, 0.19, 1.0)
    s_bsdf.inputs["Roughness"].default_value = 0.45
    
    # Bench metal legs (matte dark steel)
    mat_legs = get_or_create_material("Mat_BenchLegsMetal")
    out_l = clear_nodes(mat_legs)
    l_tree = mat_legs.node_tree
    l_bsdf = l_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    l_tree.links.new(l_bsdf.outputs["BSDF"], out_l.inputs["Surface"])
    l_bsdf.inputs["Base Color"].default_value = (0.12, 0.13, 0.15, 1.0)
    l_bsdf.inputs["Metallic"].default_value = 0.80
    l_bsdf.inputs["Roughness"].default_value = 0.35

    # Apply to bench cubes on the right
    # Cube.021, Cube.022, Cube.026, Cube.039 etc.
    for b_name in ["Cube.021", "Cube.022", "Cube.026", "Cube.039"]:
        obj = bpy.data.objects.get(b_name)
        if obj:
            obj.data.materials.clear()
            obj.data.materials.append(mat_slat)

# -------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------
if __name__ == "__main__":
    print("=== EXECUTING LUMINA PLAZA COMPREHENSIVE OVERHAUL ===")
    setup_ground_and_decals()
    setup_red_sculpture()
    setup_ez_studio()
    setup_background_and_skyline()
    setup_aster_materials()
    setup_companion_cat()
    setup_street_furniture()
    print("=== OVERHAUL COMPLETED SUCCESSFULLY ===")
