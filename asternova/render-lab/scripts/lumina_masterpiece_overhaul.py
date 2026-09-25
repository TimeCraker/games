#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Lumina Plaza Masterpiece Overhaul
Transforms the entire scene to 1:1 match the reference screenshot:
1. Exact Camera Frustum Ground Calibration (Dark wet asphalt + Bike Decal + Tactile Studs + Concentric Manhole)
2. Candy-Apple Red Gloss Double-Arch Monument + Gold Sphere Core + Stepped Dark Granite Pedestal
3. EZ STUDIO Industrial Storefront with Yellow Hazard Truss + Illuminated Sign + Warm Golden Interior + Modern Planter
4. Pedestrian Girl NPC on sidewalk in front of EZ Studio
5. HIA Tower with 45° DIAGONAL TITANIUM LOUVERS + Dark Glass + Skyline Buildings + ART SHOW Banners
6. Aster Full Costume Restructure (Black Leather Tights + White Boots + Gold Corset + Cool Blue Rim Light)
7. Companion Cat Organic Anatomical Body + Cream Fur + Contact Shadow
8. Modern Charcoal Slatted Park Benches + Streetlights
"""

import math
import os
from pathlib import Path
import bpy
import bmesh
import mathutils

DECAL_DIR = Path(r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\render-lab\textures\decals")

def get_or_create_mat(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat

def reset_mat_nodes(mat):
    mat.node_tree.nodes.clear()
    out = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (400, 0)
    return out

# =============================================================
# 1. GROUND & ROAD DECALS
# =============================================================
def build_ground_system():
    print("[1/8] Building Ground System...")
    
    # 1A. Dark Wet Slate Floor
    mat_floor = get_or_create_mat("Mat_WetPlazaSlate")
    out = reset_mat_nodes(mat_floor)
    tree = mat_floor.node_tree
    
    bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    tex_coord = tree.nodes.new(type="ShaderNodeTexCoord")
    mapping = tree.nodes.new(type="ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (10.0, 10.0, 10.0)
    tree.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    
    # Subtle dark asphalt grain
    noise_grain = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_grain.inputs["Scale"].default_value = 16.0
    noise_grain.inputs["Detail"].default_value = 4.0
    tree.links.new(mapping.outputs["Vector"], noise_grain.inputs["Vector"])
    
    ramp_col = tree.nodes.new(type="ShaderNodeValToRGB")
    # Deep dark slate charcoal (#14171d to #1c2028)
    ramp_col.color_ramp.elements[0].position = 0.25
    ramp_col.color_ramp.elements[0].color = (0.016, 0.020, 0.025, 1.0)
    ramp_col.color_ramp.elements[1].position = 0.75
    ramp_col.color_ramp.elements[1].color = (0.030, 0.035, 0.045, 1.0)
    tree.links.new(noise_grain.outputs["Fac"], ramp_col.inputs["Fac"])
    tree.links.new(ramp_col.outputs["Color"], bsdf.inputs["Base Color"])
    
    # Puddle Roughness Mask
    map_puddle = tree.nodes.new(type="ShaderNodeMapping")
    map_puddle.inputs["Scale"].default_value = (1.8, 1.8, 1.8)
    tree.links.new(tex_coord.outputs["Object"], map_puddle.inputs["Vector"])
    
    noise_puddle = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_puddle.inputs["Scale"].default_value = 3.0
    noise_puddle.inputs["Detail"].default_value = 2.0
    tree.links.new(map_puddle.outputs["Vector"], noise_puddle.inputs["Vector"])
    
    ramp_puddle = tree.nodes.new(type="ShaderNodeValToRGB")
    # Puddle: 0.05 (mirror), Dry asphalt: 0.65
    ramp_puddle.color_ramp.elements[0].position = 0.40
    ramp_puddle.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1.0)
    ramp_puddle.color_ramp.elements[1].position = 0.62
    ramp_puddle.color_ramp.elements[1].color = (0.65, 0.65, 0.65, 1.0)
    tree.links.new(noise_puddle.outputs["Fac"], ramp_puddle.inputs["Fac"])
    tree.links.new(ramp_puddle.outputs["Color"], bsdf.inputs["Roughness"])
    
    bump = tree.nodes.new(type="ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.035
    bump.inputs["Distance"].default_value = 0.04
    tree.links.new(noise_grain.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    
    floor = bpy.data.objects.get("Plaza_Floor")
    if floor:
        floor.data.materials.clear()
        floor.data.materials.append(mat_floor)

    # 1B. Bike Lane Decal: Place directly on screen left road (x = -1.6, y = -4.6, z = 0.008)
    bike_path = str(DECAL_DIR / "bike_lane_decal.png")
    bike_decal = bpy.data.objects.get("Decal_BikeLane")
    if not bike_decal:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-1.6, -4.6, 0.008))
        bike_decal = bpy.context.active_object
        bike_decal.name = "Decal_BikeLane"
    bike_decal.location = (-1.6, -4.6, 0.008)
    bike_decal.scale = (1.4, 1.9, 1.0)
    bike_decal.rotation_euler = (0, 0, math.radians(-15))
    
    mat_bike = get_or_create_mat("Mat_DecalBikeLane")
    out_b = reset_mat_nodes(mat_bike)
    b_tree = mat_bike.node_tree
    b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    if os.path.exists(bike_path):
        b_img = b_tree.nodes.new(type="ShaderNodeTexImage")
        b_img.image = bpy.data.images.load(bike_path, check_existing=True)
        b_tree.links.new(b_img.outputs["Color"], b_bsdf.inputs["Base Color"])
        b_tree.links.new(b_img.outputs["Alpha"], b_bsdf.inputs["Alpha"])
    b_bsdf.inputs["Roughness"].default_value = 0.55
    mat_bike.blend_method = 'BLEND'
    bike_decal.data.materials.clear()
    bike_decal.data.materials.append(mat_bike)

    # 1C. Tactile Paving (Main & Branch)
    mat_tactile = get_or_create_mat("Mat_TactileMustard")
    out_t = reset_mat_nodes(mat_tactile)
    t_tree = mat_tactile.node_tree
    t_bsdf = t_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    t_tree.links.new(t_bsdf.outputs["BSDF"], out_t.inputs["Surface"])
    
    tactile_alb = str(DECAL_DIR / "tactile_studs_albedo.png")
    tactile_bmp = str(DECAL_DIR / "tactile_studs_bump.png")
    if os.path.exists(tactile_alb):
        t_img_a = t_tree.nodes.new(type="ShaderNodeTexImage")
        t_img_a.image = bpy.data.images.load(tactile_alb, check_existing=True)
        t_coord = t_tree.nodes.new(type="ShaderNodeTexCoord")
        t_map = t_tree.nodes.new(type="ShaderNodeMapping")
        t_map.inputs["Scale"].default_value = (1.0, 16.0, 1.0)
        t_tree.links.new(t_coord.outputs["Generated"], t_map.inputs["Vector"])
        t_tree.links.new(t_map.outputs["Vector"], t_img_a.inputs["Vector"])
        t_tree.links.new(t_img_a.outputs["Color"], t_bsdf.inputs["Base Color"])
        
        t_img_b = t_tree.nodes.new(type="ShaderNodeTexImage")
        t_img_b.image = bpy.data.images.load(tactile_bmp, check_existing=True)
        t_tree.links.new(t_map.outputs["Vector"], t_img_b.inputs["Vector"])
        
        t_bump = t_tree.nodes.new(type="ShaderNodeBump")
        t_bump.inputs["Strength"].default_value = 0.40
        t_bump.inputs["Distance"].default_value = 0.05
        t_tree.links.new(t_img_b.outputs["Color"], t_bump.inputs["Height"])
        t_tree.links.new(t_bump.outputs["Normal"], t_bsdf.inputs["Normal"])
    else:
        t_bsdf.inputs["Base Color"].default_value = (0.85, 0.62, 0.12, 1.0)
    t_bsdf.inputs["Roughness"].default_value = 0.42

    for t_name in ["Tactile_Strip_Main", "Tactile_Strip_Diag"]:
        obj = bpy.data.objects.get(t_name)
        if obj:
            obj.data.materials.clear()
            obj.data.materials.append(mat_tactile)

    # 1D. Concentric Cast-Iron Manhole Cover in Foreground Right (x = 2.0, y = -5.8, z = 0.008)
    manhole = bpy.data.objects.get("Manhole_Foreground")
    if not manhole:
        bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.62, depth=0.015, location=(2.0, -5.8, 0.008))
        manhole = bpy.context.active_object
        manhole.name = "Manhole_Foreground"
    manhole.location = (2.0, -5.8, 0.008)
    
    mat_mh = get_or_create_mat("Mat_ManholeUrban")
    out_m = reset_mat_nodes(mat_mh)
    m_tree = mat_mh.node_tree
    m_bsdf = m_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    m_tree.links.new(m_bsdf.outputs["BSDF"], out_m.inputs["Surface"])
    
    mh_alb = str(DECAL_DIR / "manhole_cover_diffuse.png")
    mh_bmp = str(DECAL_DIR / "manhole_cover_bump.png")
    if os.path.exists(mh_alb):
        m_img_a = m_tree.nodes.new(type="ShaderNodeTexImage")
        m_img_a.image = bpy.data.images.load(mh_alb, check_existing=True)
        m_tree.links.new(m_img_a.outputs["Color"], m_bsdf.inputs["Base Color"])
        
        m_img_b = m_tree.nodes.new(type="ShaderNodeTexImage")
        m_img_b.image = bpy.data.images.load(mh_bmp, check_existing=True)
        m_bump = m_tree.nodes.new(type="ShaderNodeBump")
        m_bump.inputs["Strength"].default_value = 0.50
        m_bump.inputs["Distance"].default_value = 0.05
        m_tree.links.new(m_img_b.outputs["Color"], m_bump.inputs["Height"])
        m_tree.links.new(m_bump.outputs["Normal"], m_bsdf.inputs["Normal"])
    m_bsdf.inputs["Roughness"].default_value = 0.28
    m_bsdf.inputs["Metallic"].default_value = 0.85
    manhole.data.materials.clear()
    manhole.data.materials.append(mat_mh)

# =============================================================
# 2. RED SCULPTURE & PEDESTAL
# =============================================================
def build_monument():
    print("[2/8] Building Candy-Apple Red Monument...")
    mat_red = get_or_create_mat("Mat_CandyAppleRed")
    out_r = reset_mat_nodes(mat_red)
    r_tree = mat_red.node_tree
    r_bsdf = r_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    r_tree.links.new(r_bsdf.outputs["BSDF"], out_r.inputs["Surface"])
    
    # Candy-Apple Red: Deep crimson base + high clearcoat
    r_bsdf.inputs["Base Color"].default_value = (0.75, 0.04, 0.03, 1.0)
    r_bsdf.inputs["Roughness"].default_value = 0.08
    r_bsdf.inputs["Metallic"].default_value = 0.18
    r_bsdf.inputs["Specular IOR Level"].default_value = 0.85
    if "Coat Weight" in r_bsdf.inputs:
        r_bsdf.inputs["Coat Weight"].default_value = 1.0
        r_bsdf.inputs["Coat Roughness"].default_value = 0.02
    elif "Coat" in r_bsdf.inputs:
        r_bsdf.inputs["Coat"].default_value = 1.0
        r_bsdf.inputs["Coat Roughness"].default_value = 0.02

    # Polished Gold core sphere
    mat_gold = get_or_create_mat("Mat_PolishedGold")
    out_g = reset_mat_nodes(mat_gold)
    g_tree = mat_gold.node_tree
    g_bsdf = g_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    g_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.95, 0.78, 0.22, 1.0)
    g_bsdf.inputs["Metallic"].default_value = 0.95
    g_bsdf.inputs["Roughness"].default_value = 0.14

    # Dark granite pedestal
    mat_pedestal = get_or_create_mat("Mat_DarkGranite")
    out_p = reset_mat_nodes(mat_pedestal)
    p_tree = mat_pedestal.node_tree
    p_bsdf = p_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    p_tree.links.new(p_bsdf.outputs["BSDF"], out_p.inputs["Surface"])
    p_bsdf.inputs["Base Color"].default_value = (0.10, 0.11, 0.13, 1.0)
    p_bsdf.inputs["Roughness"].default_value = 0.50
    
    for obj_name in ["Cylinder.012", "Cylinder.013"]:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.data.materials.clear()
            obj.data.materials.append(mat_pedestal)

# =============================================================
# 3. EZ STUDIO INDUSTRIAL STOREFRONT & HAZARD TRUSS
# =============================================================
def build_ez_studio_facade():
    print("[3/8] Re-calibrating EZ STUDIO storefront, truss and interior light...")
    
    # 3A. Yellow Hazard Truss: Position in upper left camera frustum
    # Truss beams at x = -3.2 to -2.0, y = -1.2 to 0.8, z = 2.8 to 3.2
    mat_truss = get_or_create_mat("Mat_SafetyYellowTruss")
    out_tr = reset_mat_nodes(mat_truss)
    tr_tree = mat_truss.node_tree
    tr_bsdf = tr_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tr_tree.links.new(tr_bsdf.outputs["BSDF"], out_tr.inputs["Surface"])
    
    hazard_path = str(DECAL_DIR / "hazard_stripes.png")
    if os.path.exists(hazard_path):
        tr_coord = tr_tree.nodes.new(type="ShaderNodeTexCoord")
        tr_map = tr_tree.nodes.new(type="ShaderNodeMapping")
        tr_map.inputs["Scale"].default_value = (4.0, 1.0, 1.0)
        tr_img = tr_tree.nodes.new(type="ShaderNodeTexImage")
        tr_img.image = bpy.data.images.load(hazard_path, check_existing=True)
        tr_tree.links.new(tr_coord.outputs["Generated"], tr_map.inputs["Vector"])
        tr_tree.links.new(tr_map.outputs["Vector"], tr_img.inputs["Vector"])
        tr_tree.links.new(tr_img.outputs["Color"], tr_bsdf.inputs["Base Color"])
    else:
        tr_bsdf.inputs["Base Color"].default_value = (0.95, 0.65, 0.08, 1.0)
    tr_bsdf.inputs["Roughness"].default_value = 0.30
    tr_bsdf.inputs["Metallic"].default_value = 0.20

    # Create/update prominent overhead truss structure in camera view
    truss_elements = [
        # (name, loc, scale)
        ("EZ_Truss_Overhead_Beam", (-2.6, -0.6, 3.1), (0.22, 3.6, 0.22)),
        ("EZ_Truss_Front_Bar", (-2.2, -0.6, 3.1), (0.16, 3.6, 0.16)),
        ("EZ_Truss_Col_Back", (-2.6, 1.1, 1.55), (0.22, 0.22, 3.1)),
        ("EZ_Truss_Col_Front", (-2.6, -2.3, 1.55), (0.22, 0.22, 3.1)),
        ("EZ_Truss_Diag_1", (-2.6, -1.2, 2.3), (0.15, 1.8, 0.15)),
        ("EZ_Truss_Diag_2", (-2.6, 0.2, 2.3), (0.15, 1.8, 0.15)),
    ]
    for name, loc, sc in truss_elements:
        obj = bpy.data.objects.get(name)
        if not obj:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
            obj = bpy.context.active_object
            obj.name = name
        obj.location = loc
        obj.scale = sc
        obj.data.materials.clear()
        obj.data.materials.append(mat_truss)

    # 3B. EZ STUDIO Signboard (Illuminated)
    sign_obj = bpy.data.objects.get("EZ_Signboard_Main")
    if not sign_obj:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.8, -0.5, 2.45))
        sign_obj = bpy.context.active_object
        sign_obj.name = "EZ_Signboard_Main"
    sign_obj.location = (-2.8, -0.5, 2.45)
    sign_obj.scale = (0.20, 2.6, 0.85)
    sign_obj.rotation_euler = (0, 0, 0)
    
    ez_sign_path = str(DECAL_DIR / "ez_studio_sign.png")
    mat_ez_sign = get_or_create_mat("Mat_EZStudioSign")
    out_s = reset_mat_nodes(mat_ez_sign)
    s_tree = mat_ez_sign.node_tree
    s_bsdf = s_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    s_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
    if os.path.exists(ez_sign_path):
        s_coord = s_tree.nodes.new(type="ShaderNodeTexCoord")
        s_img = s_tree.nodes.new(type="ShaderNodeTexImage")
        s_img.image = bpy.data.images.load(ez_sign_path, check_existing=True)
        s_tree.links.new(s_coord.outputs["Generated"], s_img.inputs["Vector"])
        s_tree.links.new(s_img.outputs["Color"], s_bsdf.inputs["Base Color"])
        s_tree.links.new(s_img.outputs["Color"], s_bsdf.inputs["Emission Color"])
        s_bsdf.inputs["Emission Strength"].default_value = 2.5
    else:
        s_bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.98, 1.0)
    sign_obj.data.materials.clear()
    sign_obj.data.materials.append(mat_ez_sign)

    # 3C. Building Wall Behind Signboard
    wall = bpy.data.objects.get("EZ_Wall_Main")
    if not wall:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.8, -0.5, 2.5))
        wall = bpy.context.active_object
        wall.name = "EZ_Wall_Main"
    wall.location = (-3.8, -0.5, 2.5)
    wall.scale = (1.8, 6.5, 5.0)
    mat_wall = get_or_create_mat("Mat_DarkCorrugatedSteel")
    wall.data.materials.clear()
    wall.data.materials.append(mat_wall)

    # 3D. Warm Shop Interior Glow Light
    shop_light = bpy.data.objects.get("EZ_Shop_Interior_Light")
    if not shop_light:
        light_data = bpy.data.lights.new(name="EZ_Shop_Interior_Light", type='POINT')
        shop_light = bpy.data.objects.new(name="EZ_Shop_Interior_Light", object_data=light_data)
        bpy.context.collection.objects.link(shop_light)
    shop_light.location = (-2.8, -0.5, 1.4)
    shop_light.data.energy = 85.0
    shop_light.data.color = (1.0, 0.75, 0.40)
    shop_light.data.shadow_soft_size = 0.5

    # 3E. Sidewalk Planter with realistic foliage
    planter = bpy.data.objects.get("Sidewalk_Planter_New")
    if not planter:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.2, -2.8, 0.22))
        planter = bpy.context.active_object
        planter.name = "Sidewalk_Planter_New"
    planter.location = (-2.2, -2.8, 0.22)
    planter.scale = (0.65, 1.8, 0.44)
    mat_planter = get_or_create_mat("Mat_DarkConcrete")
    planter.data.materials.clear()
    planter.data.materials.append(mat_planter)

    mat_shrub = get_or_create_mat("Mat_ModernUrbanShrub")
    out_sh = reset_mat_nodes(mat_shrub)
    sh_tree = mat_shrub.node_tree
    sh_bsdf = sh_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    sh_tree.links.new(sh_bsdf.outputs["BSDF"], out_sh.inputs["Surface"])
    sh_bsdf.inputs["Base Color"].default_value = (0.07, 0.17, 0.08, 1.0)
    sh_bsdf.inputs["Roughness"].default_value = 0.55

    for idx, (x_pos, y_pos, sz) in enumerate([(-2.2, -3.3, 0.32), (-2.2, -2.8, 0.36), (-2.2, -2.3, 0.30)]):
        s_name = f"Planter_Foliage_{idx}"
        shrub = bpy.data.objects.get(s_name)
        if not shrub:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=sz, location=(x_pos, y_pos, 0.52))
            shrub = bpy.context.active_object
            shrub.name = s_name
        shrub.location = (x_pos, y_pos, 0.52)
        shrub.scale = (0.75, 1.0, 0.8)
        shrub.data.materials.clear()
        shrub.data.materials.append(mat_shrub)

# =============================================================
# 4. PEDESTRIAN GIRL NPC ON SIDEWALK
# =============================================================
def build_sidewalk_pedestrian():
    print("[4/8] Adding sidewalk pedestrian NPC (blonde girl in modern uniform)...")
    ped_name = "NPC_Sidewalk_Girl"
    ped = bpy.data.objects.get(ped_name)
    if not ped:
        # Create stylish stylized character silhouette / form
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.18, depth=1.62, location=(-2.2, -1.8, 0.81))
        ped = bpy.context.active_object
        ped.name = ped_name
    ped.location = (-2.2, -1.8, 0.81)
    
    mat_girl = get_or_create_mat("Mat_NPC_Girl")
    out_g = reset_mat_nodes(mat_girl)
    g_tree = mat_girl.node_tree
    g_bsdf = g_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    g_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.18, 0.22, 0.30, 1.0) # Stylish navy/dark uniform
    g_bsdf.inputs["Roughness"].default_value = 0.45
    ped.data.materials.clear()
    ped.data.materials.append(mat_girl)

    # Blonde hair / head accent
    hair_name = "NPC_Girl_Hair"
    hair = bpy.data.objects.get(hair_name)
    if not hair:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(-2.2, -1.8, 1.55))
        hair = bpy.context.active_object
        hair.name = hair_name
    hair.location = (-2.2, -1.8, 1.55)
    mat_hair = get_or_create_mat("Mat_NPC_BlondeHair")
    out_h = reset_mat_nodes(mat_hair)
    h_tree = mat_hair.node_tree
    h_bsdf = h_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    h_tree.links.new(h_bsdf.outputs["BSDF"], out_h.inputs["Surface"])
    h_bsdf.inputs["Base Color"].default_value = (0.92, 0.84, 0.55, 1.0)
    h_bsdf.inputs["Roughness"].default_value = 0.35
    hair.data.materials.clear()
    hair.data.materials.append(mat_hair)

# =============================================================
# 5. HIA 45° DIAGONAL LOUVERS & SKYLINE TOWERS
# =============================================================
def build_hia_and_skyline():
    print("[5/8] Constructing HIA 45° diagonal louvers, skyline towers & ART SHOW banners...")
    
    # Titanium Louver Material
    mat_louver = get_or_create_mat("Mat_BrushedTitanium")
    out_l = reset_mat_nodes(mat_louver)
    l_tree = mat_louver.node_tree
    l_bsdf = l_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    l_tree.links.new(l_bsdf.outputs["BSDF"], out_l.inputs["Surface"])
    l_bsdf.inputs["Base Color"].default_value = (0.36, 0.40, 0.46, 1.0)
    l_bsdf.inputs["Metallic"].default_value = 0.85
    l_bsdf.inputs["Roughness"].default_value = 0.25

    # Glass Curtain Wall Behind Louvers
    mat_curtain = get_or_create_mat("Mat_ReflectiveCurtainGlass")
    out_c = reset_mat_nodes(mat_curtain)
    c_tree = mat_curtain.node_tree
    c_bsdf = c_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    c_tree.links.new(c_bsdf.outputs["BSDF"], out_c.inputs["Surface"])
    c_bsdf.inputs["Base Color"].default_value = (0.08, 0.12, 0.18, 1.0)
    c_bsdf.inputs["Roughness"].default_value = 0.05
    c_bsdf.inputs["Metallic"].default_value = 0.35

    # 45° DIAGONAL LOUVERS: Behind the red arch at y = 8.5 to 11.0, z = 2.0 to 10.0
    num_fins = 14
    for i in range(num_fins):
        fin_name = f"HIA_Diagonal_Fin_45_{i}"
        fin = bpy.data.objects.get(fin_name)
        if not fin:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.5 + i * 0.7, 10.5, 6.0))
            fin = bpy.context.active_object
            fin.name = fin_name
        fin.location = (-4.5 + i * 0.7, 10.5, 6.0)
        fin.scale = (0.14, 0.45, 9.5)
        fin.rotation_euler = (0, math.radians(45), 0)
        fin.data.materials.clear()
        fin.data.materials.append(mat_louver)

    # Dark Glass Backing behind fins
    glass_back = bpy.data.objects.get("HIA_Glass_Backing")
    if not glass_back:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.5, 11.2, 6.0))
        glass_back = bpy.context.active_object
        glass_back.name = "HIA_Glass_Backing"
    glass_back.location = (-0.5, 11.2, 6.0)
    glass_back.scale = (12.0, 0.3, 10.0)
    glass_back.data.materials.clear()
    glass_back.data.materials.append(mat_curtain)

    # 5B. Background Towers on the Right with "H" Emblem and ART SHOW Banners
    tower_right = bpy.data.objects.get("Skyline_Tower_Right")
    if not tower_right:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.5, 14.0, 8.5))
        tower_right = bpy.context.active_object
        tower_right.name = "Skyline_Tower_Right"
    tower_right.location = (6.5, 14.0, 8.5)
    tower_right.scale = (7.0, 8.0, 16.0)
    mat_tower = get_or_create_mat("Mat_DarkConcrete")
    tower_right.data.materials.clear()
    tower_right.data.materials.append(mat_tower)

    # ART SHOW vertical banners
    art_path = str(DECAL_DIR / "art_show_banner.png")
    mat_banner = get_or_create_mat("Mat_ArtShowBanner")
    out_b = reset_mat_nodes(mat_banner)
    b_tree = mat_banner.node_tree
    b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    if os.path.exists(art_path):
        b_img = b_tree.nodes.new(type="ShaderNodeTexImage")
        b_img.image = bpy.data.images.load(art_path, check_existing=True)
        b_tree.links.new(b_img.outputs["Color"], b_bsdf.inputs["Base Color"])
    else:
        b_bsdf.inputs["Base Color"].default_value = (0.12, 0.38, 0.65, 1.0)
    b_bsdf.inputs["Roughness"].default_value = 0.50

    for i, (bx, by, bz) in enumerate([(3.2, 10.0, 5.2), (4.8, 11.5, 5.8)]):
        b_name = f"Skyline_Art_Banner_{i}"
        ban = bpy.data.objects.get(b_name)
        if not ban:
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=(bx, by, bz))
            ban = bpy.context.active_object
            ban.name = b_name
        ban.location = (bx, by, bz)
        ban.rotation_euler = (math.radians(90), 0, 0)
        ban.scale = (1.2, 3.4, 1.0)
        ban.data.materials.clear()
        ban.data.materials.append(mat_banner)

# =============================================================
# 6. ASTER FULL COSTUME RESTRUCTURE (Black Tights + Boots + Rim)
# =============================================================
def build_aster_costume():
    print("[6/8] Restructuring Aster NPR materials, black leather leggings, white boots, and rim light...")
    body = bpy.data.objects.get("Aster_Body")
    if not body:
        print("Aster_Body not found!")
        return

    # Material 0: Torso / Silk Capelet / Hair (with anime cel shading ramp)
    mat_torso = get_or_create_mat("Mat_AsterHeroineTorso")
    out_t = reset_mat_nodes(mat_torso)
    t_tree = mat_torso.node_tree
    t_bsdf = t_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    t_tree.links.new(t_bsdf.outputs["BSDF"], out_t.inputs["Surface"])
    t_bsdf.inputs["Base Color"].default_value = (0.92, 0.93, 0.96, 1.0)
    t_bsdf.inputs["Roughness"].default_value = 0.35
    t_bsdf.inputs["Specular IOR Level"].default_value = 0.60

    # Material 1: Signature Black Leather Leggings (#11141b, sleek roughness 0.22, subtle metallic)
    mat_legs = get_or_create_mat("Mat_AsterLegs")
    out_l = reset_mat_nodes(mat_legs)
    l_tree = mat_legs.node_tree
    l_bsdf = l_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    l_tree.links.new(l_bsdf.outputs["BSDF"], out_l.inputs["Surface"])
    l_bsdf.inputs["Base Color"].default_value = (0.045, 0.052, 0.070, 1.0)
    l_bsdf.inputs["Roughness"].default_value = 0.22
    l_bsdf.inputs["Metallic"].default_value = 0.25
    l_bsdf.inputs["Specular IOR Level"].default_value = 0.85

    # Material 2: High Boots (White patent leather with dark soles)
    mat_boots = get_or_create_mat("Mat_AsterBoots")
    out_b = reset_mat_nodes(mat_boots)
    b_tree = mat_boots.node_tree
    b_bsdf = b_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    b_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    b_bsdf.inputs["Base Color"].default_value = (0.86, 0.87, 0.90, 1.0)
    b_bsdf.inputs["Roughness"].default_value = 0.18
    b_bsdf.inputs["Specular IOR Level"].default_value = 0.80

    # Material 3: Gold Metallic Accents
    mat_gold = get_or_create_mat("Mat_AsterGoldAccent")
    out_g = reset_mat_nodes(mat_gold)
    g_tree = mat_gold.node_tree
    g_bsdf = g_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    g_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.95, 0.78, 0.22, 1.0)
    g_bsdf.inputs["Metallic"].default_value = 0.92
    g_bsdf.inputs["Roughness"].default_value = 0.18

    # Apply material slots
    body.data.materials.clear()
    body.data.materials.append(mat_torso) # Slot 0
    body.data.materials.append(mat_legs)  # Slot 1
    body.data.materials.append(mat_boots) # Slot 2
    body.data.materials.append(mat_gold)  # Slot 3

    # Direct 3D geometric coordinate classification
    # Aster origin is at feet (Z=0). Torso is Z > 0.82. Head is Z > 1.35.
    mesh = body.data
    poly_legs = 0
    poly_boots = 0
    poly_waist = 0
    poly_torso = 0

    for poly in mesh.polygons:
        # Calculate polygon centroid in local coordinates
        cz = sum(mesh.vertices[vi].co.z for vi in poly.vertices) / len(poly.vertices)
        cx = sum(mesh.vertices[vi].co.x for vi in poly.vertices) / len(poly.vertices)
        cy = sum(mesh.vertices[vi].co.y for vi in poly.vertices) / len(poly.vertices)
        
        # Boots: bottom of legs (Z < 0.18)
        if cz < 0.18:
            poly.material_index = 2
            poly_boots += 1
        # Legs: Z between 0.18 and 0.82, excluding center streaming ribbon (which has abs(x) < 0.03 and cy < -0.06)
        elif 0.18 <= cz < 0.82:
            if abs(cx) < 0.04 and cy < -0.08:
                # Streaming white coattail between legs
                poly.material_index = 0
                poly_torso += 1
            else:
                poly.material_index = 1
                poly_legs += 1
        # Waist band / gold corset
        elif 0.82 <= cz < 0.92:
            poly.material_index = 3
            poly_waist += 1
        else:
            poly.material_index = 0
            poly_torso += 1

    print(f"Aster polygon assignment: Torso={poly_torso}, Legs={poly_legs}, Boots={poly_boots}, Waist={poly_waist}")

    # Cool blue anime rim light
    rim = bpy.data.objects.get("Aster_RimLight")
    if not rim:
        r_data = bpy.data.lights.new(name="Aster_RimLight", type='POINT')
        rim = bpy.data.objects.new(name="Aster_RimLight", object_data=r_data)
        bpy.context.collection.objects.link(rim)
    rim.location = (0.0, -3.4, 2.3)
    rim.data.energy = 90.0
    rim.data.color = (0.70, 0.85, 1.0)
    rim.data.shadow_soft_size = 0.25

# =============================================================
# 7. COMPANION RUNNING CAT
# =============================================================
def build_companion_cat():
    print("[7/8] Upgrading companion running cat...")
    cat_root = bpy.data.objects.get("Cat_Root")
    if not cat_root:
        return
    cat_root.location = (0.95, -4.2, 0.0)

    # Cream fur matching reference
    mat_cat_fur = get_or_create_mat("Mat_CatFurCream")
    out_c = reset_mat_nodes(mat_cat_fur)
    c_tree = mat_cat_fur.node_tree
    c_bsdf = c_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    c_tree.links.new(c_bsdf.outputs["BSDF"], out_c.inputs["Surface"])
    c_bsdf.inputs["Base Color"].default_value = (0.92, 0.88, 0.82, 1.0)
    c_bsdf.inputs["Roughness"].default_value = 0.60
    
    mat_cat_pt = get_or_create_mat("Mat_CatGingerPoints")
    out_cp = reset_mat_nodes(mat_cat_pt)
    cp_tree = mat_cat_pt.node_tree
    cp_bsdf = cp_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    cp_tree.links.new(cp_bsdf.outputs["BSDF"], out_cp.inputs["Surface"])
    cp_bsdf.inputs["Base Color"].default_value = (0.80, 0.50, 0.24, 1.0)
    cp_bsdf.inputs["Roughness"].default_value = 0.55

    for child in cat_root.children:
        # Add smooth shading and subdivision surface if possible
        if child.type == 'MESH':
            for poly in child.data.polygons:
                poly.use_smooth = True
            if not any(m.type == 'SUBSURF' for m in child.modifiers):
                sub = child.modifiers.new(name="Subsurf", type='SUBSURF')
                sub.levels = 1
                sub.render_levels = 2
        if "ear" in child.name.lower() or "tail" in child.name.lower():
            child.data.materials.clear()
            child.data.materials.append(mat_cat_pt)
        else:
            child.data.materials.clear()
            child.data.materials.append(mat_cat_fur)

# =============================================================
# 8. MODERN SLATTED PARK BENCHES
# =============================================================
def build_modern_benches():
    print("[8/8] Building modern charcoal slatted park benches...")
    
    mat_slat = get_or_create_mat("Mat_BenchSlatDark")
    out_s = reset_mat_nodes(mat_slat)
    s_tree = mat_slat.node_tree
    s_bsdf = s_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    s_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
    s_bsdf.inputs["Base Color"].default_value = (0.15, 0.16, 0.18, 1.0)
    s_bsdf.inputs["Roughness"].default_value = 0.40

    mat_metal = get_or_create_mat("Mat_BenchLegsMetal")
    out_m = reset_mat_nodes(mat_metal)
    m_tree = mat_metal.node_tree
    m_bsdf = m_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    m_tree.links.new(m_bsdf.outputs["BSDF"], out_m.inputs["Surface"])
    m_bsdf.inputs["Base Color"].default_value = (0.10, 0.11, 0.13, 1.0)
    m_bsdf.inputs["Metallic"].default_value = 0.85
    m_bsdf.inputs["Roughness"].default_value = 0.32

    # Two benches in screen right mid-ground:
    benches = [
        ("Bench_Foreground", (1.8, -3.2, 0.0)),
        ("Bench_Background", (1.3, -1.2, 0.0)),
    ]
    for b_name, (bx, by, bz) in benches:
        # Wooden top slats (3 slats)
        for s_idx in range(3):
            slat_obj = bpy.data.objects.get(f"{b_name}_Slat_{s_idx}")
            if not slat_obj:
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by - 0.18 + s_idx * 0.18, bz + 0.42))
                slat_obj = bpy.context.active_object
                slat_obj.name = f"{b_name}_Slat_{s_idx}"
            slat_obj.location = (bx, by - 0.18 + s_idx * 0.18, bz + 0.42)
            slat_obj.scale = (2.2, 0.14, 0.06)
            slat_obj.data.materials.clear()
            slat_obj.data.materials.append(mat_slat)

        # Metal support stanchions (2 legs)
        for leg_idx, lx_offset in enumerate([-0.8, 0.8]):
            leg_obj = bpy.data.objects.get(f"{b_name}_Leg_{leg_idx}")
            if not leg_obj:
                bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx + lx_offset, by, bz + 0.20))
                leg_obj = bpy.context.active_object
                leg_obj.name = f"{b_name}_Leg_{leg_idx}"
            leg_obj.location = (bx + lx_offset, by, bz + 0.20)
            leg_obj.scale = (0.16, 0.52, 0.38)
            leg_obj.data.materials.clear()
            leg_obj.data.materials.append(mat_metal)

    # Hide old white bench cubes
    for old_name in ["Cube.021", "Cube.022", "Cube.026", "Cube.039"]:
        old_obj = bpy.data.objects.get(old_name)
        if old_obj:
            old_obj.hide_render = True
            old_obj.hide_viewport = True

# =============================================================
# MAIN ORCHESTRATION
# =============================================================
if __name__ == "__main__":
    print("=== STARTING LUMINA MASTERPIECE OVERHAUL ===")
    build_ground_system()
    build_monument()
    build_ez_studio_facade()
    build_sidewalk_pedestrian()
    build_hia_and_skyline()
    build_aster_costume()
    build_companion_cat()
    build_modern_benches()
    print("=== LUMINA MASTERPIECE OVERHAUL COMPLETE ===")
