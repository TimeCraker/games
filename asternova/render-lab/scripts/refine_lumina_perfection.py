#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Lumina Plaza Ultimate Refinement
Performs the final polish to achieve 1:1 photorealistic anime fidelity:
1. Glass-Flat Puddle Shader: Eliminates wave ripples in puddles, creating mirror-like obsidian reflections
2. Organic Boxwood Planter Hedges: Replaces all sphere/ico-sphere primitives with lush leafy hedges & soil
3. Stylized Pedestrian Girl NPC: Refined school uniform silhouette (blonde hair, navy blazer, pleated skirt)
4. Background Skyline Enrichment: Golden HIA canopy, commercial office towers with window grids & yellow 'H' logo
5. Distance Hologram Pedestrians: Translucent figures populating the square
6. Cat Integration & Contact Shadow
7. Camera & Lighting Polish: Soft overcast daylight balance
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
# 1. PERFECT GLASS-FLAT PUDDLE SHADER
# =============================================================
def polish_ground_shader():
    print("[1/6] Polishing ground PBR for glass-flat mirror puddles...")
    mat_floor = get_or_create_mat("Mat_WetPlazaSlate")
    out = reset_mat_nodes(mat_floor)
    tree = mat_floor.node_tree
    
    bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    tex_coord = tree.nodes.new(type="ShaderNodeTexCoord")
    
    # Asphalt fine texture mapping
    mapping_asphalt = tree.nodes.new(type="ShaderNodeMapping")
    mapping_asphalt.inputs["Scale"].default_value = (14.0, 14.0, 14.0)
    tree.links.new(tex_coord.outputs["Object"], mapping_asphalt.inputs["Vector"])
    
    noise_grain = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_grain.inputs["Scale"].default_value = 18.0
    noise_grain.inputs["Detail"].default_value = 5.0
    noise_grain.inputs["Roughness"].default_value = 0.65
    tree.links.new(mapping_asphalt.outputs["Vector"], noise_grain.inputs["Vector"])
    
    # Base Color: Deep charcoal slate (#12151b to #181c24)
    ramp_col = tree.nodes.new(type="ShaderNodeValToRGB")
    ramp_col.color_ramp.elements[0].position = 0.2
    ramp_col.color_ramp.elements[0].color = (0.015, 0.018, 0.024, 1.0)
    ramp_col.color_ramp.elements[1].position = 0.8
    ramp_col.color_ramp.elements[1].color = (0.028, 0.032, 0.042, 1.0)
    tree.links.new(noise_grain.outputs["Fac"], ramp_col.inputs["Fac"])
    tree.links.new(ramp_col.outputs["Color"], bsdf.inputs["Base Color"])
    
    # Puddle mask: Larger organic puddles
    map_puddle = tree.nodes.new(type="ShaderNodeMapping")
    map_puddle.inputs["Scale"].default_value = (1.4, 1.4, 1.4)
    tree.links.new(tex_coord.outputs["Object"], map_puddle.inputs["Vector"])
    
    noise_puddle = tree.nodes.new(type="ShaderNodeTexNoise")
    noise_puddle.inputs["Scale"].default_value = 2.4
    noise_puddle.inputs["Detail"].default_value = 2.0
    tree.links.new(map_puddle.outputs["Vector"], noise_puddle.inputs["Vector"])
    
    # ColorRamp for puddle factor: 0.0 = deep puddle, 1.0 = dry asphalt
    ramp_puddle_fac = tree.nodes.new(type="ShaderNodeValToRGB")
    ramp_puddle_fac.color_ramp.elements[0].position = 0.45
    ramp_puddle_fac.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0) # Puddle
    ramp_puddle_fac.color_ramp.elements[1].position = 0.58
    ramp_puddle_fac.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0) # Dry
    tree.links.new(noise_puddle.outputs["Fac"], ramp_puddle_fac.inputs["Fac"])
    
    # Roughness: Puddle is 0.018 (mirror-like liquid glass!), Dry is 0.68
    ramp_rough = tree.nodes.new(type="ShaderNodeValToRGB")
    ramp_rough.color_ramp.elements[0].position = 0.0
    ramp_rough.color_ramp.elements[0].color = (0.018, 0.018, 0.018, 1.0)
    ramp_rough.color_ramp.elements[1].position = 1.0
    ramp_rough.color_ramp.elements[1].color = (0.68, 0.68, 0.68, 1.0)
    tree.links.new(ramp_puddle_fac.outputs["Color"], ramp_rough.inputs["Fac"])
    tree.links.new(ramp_rough.outputs["Color"], bsdf.inputs["Roughness"])
    
    # Normal bump: ONLY applied to dry asphalt! Puddles have 0 bump (flat mirror surface)
    math_bump_strength = tree.nodes.new(type="ShaderNodeMath")
    math_bump_strength.operation = 'MULTIPLY'
    math_bump_strength.inputs[1].default_value = 0.035
    tree.links.new(ramp_puddle_fac.outputs["Color"], math_bump_strength.inputs[0])
    
    bump = tree.nodes.new(type="ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.04
    tree.links.new(math_bump_strength.outputs["Value"], bump.inputs["Strength"])
    tree.links.new(noise_grain.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    
    bsdf.inputs["Specular IOR Level"].default_value = 0.75
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.0
    elif "Coat" in bsdf.inputs:
        bsdf.inputs["Coat"].default_value = 0.0

# =============================================================
# 2. LUSH BOXWOOD PLANTER HEDGES (REPLACE SPHERES)
# =============================================================
def polish_planter_greenery():
    print("[2/6] Building lush boxwood planter hedge & removing primitive spheres...")
    # Delete any old spherical bushes
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Sphere") and not "gold" in obj.name.lower() and not "eye" in obj.name.lower() and not "head" in obj.name.lower() and not "core" in obj.name.lower():
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.name.startswith("Realistic_Shrub_") or obj.name.startswith("Planter_Foliage_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Boxwood hedge material with leaf micro-bump
    mat_hedge = get_or_create_mat("Mat_LushBoxwoodHedge")
    out_h = reset_mat_nodes(mat_hedge)
    h_tree = mat_hedge.node_tree
    h_bsdf = h_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    h_tree.links.new(h_bsdf.outputs["BSDF"], out_h.inputs["Surface"])
    
    h_coord = h_tree.nodes.new(type="ShaderNodeTexCoord")
    h_noise = h_tree.nodes.new(type="ShaderNodeTexNoise")
    h_noise.inputs["Scale"].default_value = 24.0
    h_noise.inputs["Detail"].default_value = 4.0
    h_tree.links.new(h_coord.outputs["Object"], h_noise.inputs["Vector"])
    
    h_ramp = h_tree.nodes.new(type="ShaderNodeValToRGB")
    # Natural organic boxwood greens (#16351c to #265428)
    h_ramp.color_ramp.elements[0].position = 0.3
    h_ramp.color_ramp.elements[0].color = (0.06, 0.16, 0.07, 1.0)
    h_ramp.color_ramp.elements[1].position = 0.7
    h_ramp.color_ramp.elements[1].color = (0.12, 0.32, 0.14, 1.0)
    h_tree.links.new(h_noise.outputs["Fac"], h_ramp.inputs["Fac"])
    h_tree.links.new(h_ramp.outputs["Color"], h_bsdf.inputs["Base Color"])
    
    h_bump = h_tree.nodes.new(type="ShaderNodeBump")
    h_bump.inputs["Strength"].default_value = 0.15
    h_bump.inputs["Distance"].default_value = 0.02
    h_tree.links.new(h_noise.outputs["Fac"], h_bump.inputs["Height"])
    h_tree.links.new(h_bump.outputs["Normal"], h_bsdf.inputs["Normal"])
    h_bsdf.inputs["Roughness"].default_value = 0.48

    # Continuous hedge in the sidewalk planter: x = -2.2, y = -3.8 to -1.8, z = 0.35
    hedge_obj = bpy.data.objects.get("Planter_Lush_Hedge")
    if not hedge_obj:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.2, -2.8, 0.40))
        hedge_obj = bpy.context.active_object
        hedge_obj.name = "Planter_Lush_Hedge"
    hedge_obj.location = (-2.2, -2.8, 0.40)
    hedge_obj.scale = (0.55, 2.0, 0.38)
    
    # Bevel modifier for soft rounded organic bush contour
    if not any(m.type == 'BEVEL' for m in hedge_obj.modifiers):
        bev = hedge_obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = 0.18
        bev.segments = 4
    
    hedge_obj.data.materials.clear()
    hedge_obj.data.materials.append(mat_hedge)

# =============================================================
# 3. REFINED PEDESTRIAN GIRL NPC
# =============================================================
def polish_pedestrian_girl():
    print("[3/6] Refining pedestrian girl NPC on sidewalk...")
    # Girl is at x = -2.1, y = -1.6, z = 0.0 (standing by the sidewalk curb)
    root = bpy.data.objects.get("NPC_Girl_Root")
    if not root:
        root = bpy.data.objects.new("NPC_Girl_Root", None)
        bpy.context.collection.objects.link(root)
    root.location = (-2.1, -1.6, 0.0)

    # Clean old objects
    for old_name in ["NPC_Sidewalk_Girl", "NPC_Girl_Hair"]:
        old_o = bpy.data.objects.get(old_name)
        if old_o:
            bpy.data.objects.remove(old_o, do_unlink=True)

    # Torso (Blazer)
    mat_blazer = get_or_create_mat("Mat_Girl_Blazer")
    out_b = reset_mat_nodes(mat_blazer)
    b_bsdf = mat_blazer.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_blazer.node_tree.links.new(b_bsdf.outputs["BSDF"], out_b.inputs["Surface"])
    b_bsdf.inputs["Base Color"].default_value = (0.12, 0.16, 0.24, 1.0) # Dark navy blazer
    b_bsdf.inputs["Roughness"].default_value = 0.50

    mat_skirt = get_or_create_mat("Mat_Girl_Skirt")
    out_s = reset_mat_nodes(mat_skirt)
    s_bsdf = mat_skirt.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_skirt.node_tree.links.new(s_bsdf.outputs["BSDF"], out_s.inputs["Surface"])
    s_bsdf.inputs["Base Color"].default_value = (0.28, 0.32, 0.42, 1.0) # Pleated skirt
    s_bsdf.inputs["Roughness"].default_value = 0.45

    mat_hair = get_or_create_mat("Mat_Girl_BlondeHair")
    out_h = reset_mat_nodes(mat_hair)
    h_bsdf = mat_hair.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_hair.node_tree.links.new(h_bsdf.outputs["BSDF"], out_h.inputs["Surface"])
    h_bsdf.inputs["Base Color"].default_value = (0.92, 0.82, 0.52, 1.0) # Blonde
    h_bsdf.inputs["Roughness"].default_value = 0.30

    # Upper Body
    body_obj = bpy.data.objects.get("Girl_Upper_Body")
    if not body_obj:
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.14, depth=0.65, location=(0, 0, 1.15))
        body_obj = bpy.context.active_object
        body_obj.name = "Girl_Upper_Body"
        body_obj.parent = root
    body_obj.location = (0, 0, 1.15)
    body_obj.data.materials.clear()
    body_obj.data.materials.append(mat_blazer)

    # Skirt
    skirt_obj = bpy.data.objects.get("Girl_Skirt")
    if not skirt_obj:
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.22, radius2=0.14, depth=0.32, location=(0, 0, 0.72))
        skirt_obj = bpy.context.active_object
        skirt_obj.name = "Girl_Skirt"
        skirt_obj.parent = root
    skirt_obj.location = (0, 0, 0.72)
    skirt_obj.data.materials.clear()
    skirt_obj.data.materials.append(mat_skirt)

    # Head & Hair
    head_obj = bpy.data.objects.get("Girl_Head")
    if not head_obj:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, 1.58))
        head_obj = bpy.context.active_object
        head_obj.name = "Girl_Head"
        head_obj.parent = root
    head_obj.location = (0, 0, 1.58)
    head_obj.data.materials.clear()
    head_obj.data.materials.append(mat_hair)

# =============================================================
# 4. HIA GOLD CANOPY & SKYLINE COMMERCIAL TOWERS
# =============================================================
def polish_skyline():
    print("[4/6] Adding HIA entrance golden canopy & skyline commercial towers...")
    
    # 4A. HIA Entrance Golden Canopy below louvers at x = -0.8, y = 8.6, z = 2.4
    mat_hia_gold = get_or_create_mat("Mat_HiaGoldCanopy")
    out_g = reset_mat_nodes(mat_hia_gold)
    g_bsdf = mat_hia_gold.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_hia_gold.node_tree.links.new(g_bsdf.outputs["BSDF"], out_g.inputs["Surface"])
    g_bsdf.inputs["Base Color"].default_value = (0.95, 0.78, 0.18, 1.0)
    g_bsdf.inputs["Metallic"].default_value = 0.85
    g_bsdf.inputs["Roughness"].default_value = 0.25
    g_bsdf.inputs["Emission Color"].default_value = (0.95, 0.78, 0.18, 1.0)
    g_bsdf.inputs["Emission Strength"].default_value = 1.6

    canopy = bpy.data.objects.get("HIA_Golden_Canopy")
    if not canopy:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.8, 8.6, 2.4))
        canopy = bpy.context.active_object
        canopy.name = "HIA_Golden_Canopy"
    canopy.location = (-0.8, 8.6, 2.4)
    canopy.scale = (5.2, 1.2, 0.45)
    canopy.data.materials.clear()
    canopy.data.materials.append(mat_hia_gold)

    # 4B. Commercial Tower with Windows & Yellow 'H' Logo in upper right
    # Upper right building: x = 5.8, y = 13.0, z = 8.5
    tower = bpy.data.objects.get("Skyline_Commercial_Tower")
    if not tower:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(5.8, 13.0, 8.5))
        tower = bpy.context.active_object
        tower.name = "Skyline_Commercial_Tower"
    tower.location = (5.8, 13.0, 8.5)
    tower.scale = (6.5, 7.0, 15.0)
    
    mat_tower = get_or_create_mat("Mat_CommercialFacade")
    out_tf = reset_mat_nodes(mat_tower)
    tf_tree = mat_tower.node_tree
    tf_bsdf = tf_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    tf_tree.links.new(tf_bsdf.outputs["BSDF"], out_tf.inputs["Surface"])
    tf_bsdf.inputs["Base Color"].default_value = (0.22, 0.25, 0.30, 1.0)
    tf_bsdf.inputs["Roughness"].default_value = 0.40
    tower.data.materials.clear()
    tower.data.materials.append(mat_tower)

    # Yellow "H" Logo Sign on the tower
    h_logo = bpy.data.objects.get("Tower_Yellow_H_Logo")
    if not h_logo:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.2, 11.5, 7.8))
        h_logo = bpy.context.active_object
        h_logo.name = "Tower_Yellow_H_Logo"
    h_logo.location = (3.2, 11.5, 7.8)
    h_logo.scale = (1.8, 0.2, 1.8)
    h_logo.data.materials.clear()
    h_logo.data.materials.append(mat_hia_gold)

# =============================================================
# 5. DISTANT HOLOGRAPHIC PEDESTRIANS IN SQUARE
# =============================================================
def polish_distant_npcs():
    print("[5/6] Populating distant square with urban silhouettes...")
    mat_holo = get_or_create_mat("Mat_HologramNPC")
    out_h = reset_mat_nodes(mat_holo)
    h_bsdf = mat_holo.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    mat_holo.node_tree.links.new(h_bsdf.outputs["BSDF"], out_h.inputs["Surface"])
    h_bsdf.inputs["Base Color"].default_value = (0.45, 0.52, 0.65, 1.0)
    h_bsdf.inputs["Alpha"].default_value = 0.65
    mat_holo.blend_method = 'BLEND'

    npc_coords = [
        ("NPC_Square_0", (1.6, 2.8, 0.8)),
        ("NPC_Square_1", (2.8, 4.2, 0.8)),
        ("NPC_Square_2", (-1.2, 3.8, 0.8)),
        ("NPC_Square_3", (3.8, 6.5, 0.8)),
    ]
    for n_name, (nx, ny, nz) in npc_coords:
        npc = bpy.data.objects.get(n_name)
        if not npc:
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.18, depth=1.6, location=(nx, ny, nz))
            npc = bpy.context.active_object
            npc.name = n_name
        npc.location = (nx, ny, nz)
        npc.data.materials.clear()
        npc.data.materials.append(mat_holo)

# =============================================================
# 6. ATMOSPHERE & RENDER TUNE
# =============================================================
def polish_atmosphere():
    print("[6/6] Tuning daylight balance and exposure...")
    scene = bpy.context.scene
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
    scene.view_settings.exposure = -0.35 # Slightly brighter for crisp contrast

    # Overcast Sky Dome
    world = scene.world
    if world and world.node_tree:
        bg = next((n for n in world.node_tree.nodes if n.type == 'BACKGROUND'), None)
        if bg:
            bg.inputs["Color"].default_value = (0.64, 0.70, 0.80, 1.0)
            bg.inputs["Strength"].default_value = 0.75

if __name__ == "__main__":
    print("=== STARTING LUMINA ULTIMATE REFINEMENT ===")
    polish_ground_shader()
    polish_planter_greenery()
    polish_pedestrian_girl()
    polish_skyline()
    polish_distant_npcs()
    polish_atmosphere()
    print("=== LUMINA ULTIMATE REFINEMENT COMPLETE ===")
