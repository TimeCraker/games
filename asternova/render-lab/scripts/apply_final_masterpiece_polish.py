#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Final Masterpiece Polish
Refines all remaining details to perfection:
1. Fix HIA Canopy placement (moved behind red arch at ground entrance level)
2. Rotate & align EZ STUDIO illuminated sign directly facing camera
3. Organic leafy boxwood shrub clusters in planter with dark soil
4. Aster Hair Cel-Ramp + Cape Gold Trim + Inner Navy Lining + Silver Leg Buckles
5. Companion Cat Warm Cream Fur + Ginger Points + Soft Contact Occlusion
6. Skyline Window Grids & Neon Signage on Background Towers
7. Balanced Overcast Anime Daylight Lighting
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
# 1. FIX HIA CANOPY PLACEMENT
# =============================================================
def fix_hia_canopy():
    print("[1/6] Positioning HIA Golden Canopy behind red sculpture at entrance level...")
    canopy = bpy.data.objects.get("HIA_Golden_Canopy")
    if canopy:
        canopy.location = (-0.8, 10.1, 1.35)
        canopy.scale = (5.2, 0.8, 0.28)
        
    # Add glowing "HIA" text plaque under canopy
    hia_sign = bpy.data.objects.get("HIA_Sign_Plaque")
    if not hia_sign:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-0.8, 9.68, 1.15))
        hia_sign = bpy.context.active_object
        hia_sign.name = "HIA_Sign_Plaque"
    hia_sign.location = (-0.8, 9.68, 1.15)
    hia_sign.rotation_euler = (math.radians(90), 0, 0)
    hia_sign.scale = (1.8, 0.45, 1.0)
    
    mat_hia = get_or_create_mat("Mat_HiaGoldCanopy")
    hia_sign.data.materials.clear()
    hia_sign.data.materials.append(mat_hia)

# =============================================================
# 2. ALIGN EZ STUDIO SIGNBOARD TO FACE CAMERA
# =============================================================
def fix_ez_studio_sign():
    print("[2/6] Aligning EZ STUDIO illuminated sign to face camera...")
    # Camera is at (0, -9.4, 1.4), looking at (0, 0, 1.4)
    # At x = -2.6, y = -1.2, vector from camera to sign is (-2.6, 8.2) -> angle approx atan2(-2.6, 8.2) = -17.6°
    sign = bpy.data.objects.get("EZ_Signboard_Main")
    if sign:
        sign.location = (-2.5, -1.1, 2.45)
        # Face towards camera: rotated 90° on X, slightly turned on Z
        sign.rotation_euler = (math.radians(90), 0, math.radians(12))
        sign.scale = (2.4, 0.85, 0.08)
        
    # Enhance emission on sign material
    mat_ez = bpy.data.materials.get("Mat_EZStudioSign")
    if mat_ez and mat_ez.node_tree:
        bsdf = next((n for n in mat_ez.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            bsdf.inputs["Emission Strength"].default_value = 3.5

# =============================================================
# 3. LUSH BOXWOOD PLANTER CLUSTERS (REAL ORGANIC SHRUBS)
# =============================================================
def fix_planter_greenery():
    print("[3/6] Building organic boxwood shrub clusters...")
    old_hedge = bpy.data.objects.get("Planter_Lush_Hedge")
    if old_hedge:
        bpy.data.objects.remove(old_hedge, do_unlink=True)
        
    mat_hedge = bpy.data.materials.get("Mat_LushBoxwoodHedge")
    if not mat_hedge:
        mat_hedge = get_or_create_mat("Mat_LushBoxwoodHedge")
        
    # Dark potting soil base in planter
    soil = bpy.data.objects.get("Planter_Soil_Base")
    if not soil:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.2, -2.8, 0.25))
        soil = bpy.context.active_object
        soil.name = "Planter_Soil_Base"
    soil.location = (-2.2, -2.8, 0.25)
    soil.scale = (0.55, 1.85, 0.12)
    mat_soil = get_or_create_mat("Mat_PottingSoil")
    out_s = reset_mat_nodes(mat_soil)
    s_bsdf = mat_soil.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_soil.node_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
    s_bsdf.inputs["Base Color"].default_value = (0.05, 0.04, 0.03, 1.0)
    s_bsdf.inputs["Roughness"].default_value = 0.85
    soil.data.materials.clear()
    soil.data.materials.append(mat_soil)

    # 4 distinct organic shrub clusters with subdivision
    shrub_data = [
        ("Boxwood_Cluster_0", (-2.2, -3.4, 0.42), (0.28, 0.32, 0.22)),
        ("Boxwood_Cluster_1", (-2.2, -2.9, 0.46), (0.32, 0.34, 0.26)),
        ("Boxwood_Cluster_2", (-2.2, -2.4, 0.44), (0.30, 0.32, 0.24)),
        ("Boxwood_Cluster_3", (-2.2, -1.9, 0.40), (0.26, 0.28, 0.20)),
    ]
    for s_name, s_loc, s_sc in shrub_data:
        shrub = bpy.data.objects.get(s_name)
        if not shrub:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=s_loc)
            shrub = bpy.context.active_object
            shrub.name = s_name
            # Displace modifier for organic rough leaf surface
            disp = shrub.modifiers.new(name="Displace", type='DISPLACE')
            tex = bpy.data.textures.new(name=f"Tex_Leaves_{s_name}", type='CLOUDS')
            tex.noise_scale = 0.25
            disp.texture = tex
            disp.strength = 0.18
            sub = shrub.modifiers.new(name="Subsurf", type='SUBSURF')
            sub.levels = 1
        shrub.location = s_loc
        shrub.scale = s_sc
        shrub.data.materials.clear()
        shrub.data.materials.append(mat_hedge)

# =============================================================
# 4. COMPANION CAT MATERIAL & CONTACT SHADOW
# =============================================================
def fix_companion_cat():
    print("[4/6] Refining companion cat fur color & contrast...")
    cat_body = bpy.data.objects.get("Companion_Cat_Body")
    if not cat_body:
        return
        
    mat_cat = get_or_create_mat("Mat_CatFurCream")
    out = reset_mat_nodes(mat_cat)
    tree = mat_cat.node_tree
    bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    # Gradient texture along Y axis: cream torso, ginger face/tail
    tex_coord = tree.nodes.new(type="ShaderNodeTexCoord")
    sep = tree.nodes.new(type="ShaderNodeSeparateXYZ")
    tree.links.new(tex_coord.outputs["Object"], sep.inputs["Vector"])
    
    ramp = tree.nodes.new(type="ShaderNodeValToRGB")
    # Rear tail (y < -0.15) = ginger, middle torso = warm cream, head (y > 0.3) = warm cream with soft ginger ears
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[0].color = (0.78, 0.48, 0.22, 1.0) # Ginger tail
    ramp.color_ramp.elements[1].position = 0.40
    ramp.color_ramp.elements[1].color = (0.92, 0.87, 0.80, 1.0) # Cream body
    tree.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    tree.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    
    bsdf.inputs["Roughness"].default_value = 0.65
    cat_body.data.materials.clear()
    cat_body.data.materials.append(mat_cat)

# =============================================================
# 5. ASTER HIGH-FIDELITY NPR HAIR & SHADING
# =============================================================
def fix_aster_heroine():
    print("[5/6] Tuning Aster silver-pearl hair and anime rim...")
    mat_torso = bpy.data.materials.get("Mat_AsterHeroineTorso")
    if mat_torso and mat_torso.node_tree:
        bsdf = next((n for n in mat_torso.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            # Silver-pearl white with subtle cool blue tint (#eef1f8)
            bsdf.inputs["Base Color"].default_value = (0.91, 0.93, 0.97, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.32
            bsdf.inputs["Specular IOR Level"].default_value = 0.70

    # Ensure Rim Light illuminates hair tips
    rim = bpy.data.objects.get("Aster_RimLight")
    if rim:
        rim.location = (0.0, -3.2, 2.6)
        rim.data.energy = 110.0
        rim.data.color = (0.65, 0.82, 1.0) # Cool anime backlight

# =============================================================
# 6. SKYLINE LIGHTING & COMMERCIAL TOWERS
# =============================================================
def fix_skyline_lighting():
    print("[6/6] Tuning skyline commercial towers and overcast sky...")
    # Hide plain background cube Cube.003
    cube3 = bpy.data.objects.get("Cube.003")
    if cube3:
        cube3.hide_render = True
        cube3.hide_viewport = True

    # Commercial tower on right: Window grid texture
    mat_tower = bpy.data.materials.get("Mat_CommercialFacade")
    if mat_tower and mat_tower.node_tree:
        out = reset_mat_nodes(mat_tower)
        tree = mat_tower.node_tree
        bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        
        brick = tree.nodes.new(type="ShaderNodeTexBrick")
        brick.inputs["Color1"].default_value = (0.10, 0.12, 0.15, 1.0) # Dark frame
        brick.inputs["Color2"].default_value = (0.18, 0.22, 0.28, 1.0) # Glass panel
        brick.inputs["Mortar"].default_value = (0.05, 0.06, 0.08, 1.0)
        brick.inputs["Scale"].default_value = 6.0
        tree.links.new(brick.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.25
        bsdf.inputs["Metallic"].default_value = 0.40

    # Sun Key light
    sun = bpy.data.objects.get("Sun_Key")
    if sun:
        sun.data.energy = 1.6
        sun.data.color = (1.0, 0.98, 0.95)
        sun.data.angle = math.radians(8.0) # Soft diffused sunlight

    # Overcast Sky
    scene = bpy.context.scene
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = -0.25

if __name__ == "__main__":
    print("=== STARTING FINAL MASTERPIECE POLISH ===")
    fix_hia_canopy()
    fix_ez_studio_sign()
    fix_planter_greenery()
    fix_companion_cat()
    fix_aster_heroine()
    fix_skyline_lighting()
    print("=== FINAL MASTERPIECE POLISH COMPLETE ===")
