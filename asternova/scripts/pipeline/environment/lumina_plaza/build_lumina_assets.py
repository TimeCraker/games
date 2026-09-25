#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsterNova Pipeline: Lumina Plaza Modular Asset Builder
Generates high-precision modular 3D assets for the Lumina Plaza urban slice using Blender 5.2.1.
Outputs glTF / GLB binary files to asternova/art/models/lumina_plaza/
"""

import math
import os
import sys
from pathlib import Path
import bpy
import bmesh

# Setup output directory
OUTPUT_DIR = Path(r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\lumina_plaza")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def reset_scene():
    """Clear all objects, meshes, curves, and materials in the current scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_pbr_material(name, base_color, roughness=0.5, metallic=0.0, specular=0.5, emissive_color=None, emissive_strength=1.0):
    """Creates a Principled BSDF material using version-independent node inspection."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    
    # Find Principled BSDF node by type
    bsdf = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        bsdf = tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        output = next((n for n in tree.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if not output:
            output = tree.nodes.new(type="ShaderNodeOutputMaterial")
        tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    def set_input(node, name_options, value):
        for opt in name_options:
            if opt in node.inputs:
                node.inputs[opt].default_value = value
                return True
        return False

    set_input(bsdf, ["Base Color", "Color"], base_color)
    set_input(bsdf, ["Roughness"], roughness)
    set_input(bsdf, ["Metallic"], metallic)
    set_input(bsdf, ["Specular IOR Level", "Specular"], specular)
    
    if emissive_color:
        set_input(bsdf, ["Emission Color", "Emission"], emissive_color)
        set_input(bsdf, ["Emission Strength"], emissive_strength)

    return mat

def export_glb(filepath):
    """Exports all scene objects to a GLB file."""
    bpy.ops.export_scene.gltf(
        filepath=str(filepath),
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported: {filepath} ({os.path.getsize(filepath):,} bytes)")

# -------------------------------------------------------------
# 1. Monument Red Ring Sculpture (Central Landmark)
# -------------------------------------------------------------
def build_monument_red_ring():
    reset_scene()
    print("Building Monument Red Ring...")
    
    mat_pedestal = create_pbr_material("Mat_PlazaPedestal", (0.72, 0.74, 0.78, 1.0), roughness=0.50, metallic=0.05)
    mat_red = create_pbr_material("Mat_MonumentRed", (0.78, 0.08, 0.06, 1.0), roughness=0.22, metallic=0.25, specular=0.8)
    mat_gold = create_pbr_material("Mat_MonumentGold", (0.92, 0.75, 0.35, 1.0), roughness=0.28, metallic=0.85, specular=0.9)
    mat_dark = create_pbr_material("Mat_DarkAccent", (0.12, 0.14, 0.16, 1.0), roughness=0.45, metallic=0.3)

    # Base Pedestal (2 tiers)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=3.6, depth=0.22, location=(0, 0, 0.11))
    base1 = bpy.context.active_object
    base1.name = "Pedestal_Tier1"
    base1.data.materials.append(mat_pedestal)
    
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=2.8, depth=0.22, location=(0, 0, 0.33))
    base2 = bpy.context.active_object
    base2.name = "Pedestal_Tier2"
    base2.data.materials.append(mat_pedestal)

    # Inner dark base ring
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=2.2, depth=0.10, location=(0, 0, 0.49))
    base3 = bpy.context.active_object
    base3.name = "Pedestal_Core"
    base3.data.materials.append(mat_dark)

    # Red Twin Arches / Toroid Structure
    curve_data = bpy.data.curves.new(name="RedRing_Curve", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.28
    curve_data.bevel_resolution = 6
    curve_data.use_fill_caps = True
    
    spline = curve_data.splines.new(type='BEZIER')
    pts = [
        (-1.4, 0.0, 0.5),
        (-1.8, 0.0, 2.8),
        (0.0, 0.0, 6.2),
        (1.8, 0.0, 2.8),
        (1.4, 0.0, 0.5),
        (0.8, 0.0, 0.5),
        (1.0, 0.0, 2.5),
        (0.0, 0.0, 5.2),
        (-1.0, 0.0, 2.5),
        (-0.8, 0.0, 0.5),
    ]
    spline.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = spline.bezier_points[i]
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    spline.use_cyclic_u = True

    curve_obj = bpy.data.objects.new("RedArch_Structure", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.data.materials.append(mat_red)

    # Secondary red cross-ring tilted at 30 degrees
    curve_data2 = bpy.data.curves.new(name="RedRing_Cross", type='CURVE')
    curve_data2.dimensions = '3D'
    curve_data2.bevel_depth = 0.18
    curve_data2.bevel_resolution = 6
    curve_data2.use_fill_caps = True
    spline2 = curve_data2.splines.new(type='BEZIER')
    pts2 = [
        (-1.1, -0.6, 1.2),
        (0.0, -0.9, 3.8),
        (1.1, -0.6, 1.2),
        (0.0, -0.3, 2.5),
    ]
    spline2.bezier_points.add(len(pts2) - 1)
    for i, p in enumerate(pts2):
        bp = spline2.bezier_points[i]
        bp.co = p
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    spline2.use_cyclic_u = True

    curve_obj2 = bpy.data.objects.new("RedArch_Accent", curve_data2)
    bpy.context.collection.objects.link(curve_obj2)
    curve_obj2.data.materials.append(mat_red)

    # Inner Gold Core / Spheres
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.45, location=(0, 0, 3.6))
    gold_sphere = bpy.context.active_object
    gold_sphere.name = "Gold_Core_Orb"
    gold_sphere.data.materials.append(mat_gold)

    # Top Finial Crown
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.35, depth=0.8, location=(0, 0, 6.7))
    crown = bpy.context.active_object
    crown.name = "Crown_Finial"
    crown.data.materials.append(mat_gold)

    export_glb(OUTPUT_DIR / "monument_red_ring.glb")

# -------------------------------------------------------------
# 2. Building: EZ STUDIO (Left Industrial Storefront)
# -------------------------------------------------------------
def build_ez_studio():
    reset_scene()
    print("Building EZ STUDIO Building...")
    
    mat_dark_panel = create_pbr_material("Mat_DarkCorrugated", (0.16, 0.18, 0.22, 1.0), roughness=0.60, metallic=0.45)
    mat_concrete = create_pbr_material("Mat_PlazaConcrete", (0.76, 0.78, 0.82, 1.0), roughness=0.68, metallic=0.05)
    mat_yellow_steel = create_pbr_material("Mat_IndustrialYellow", (0.94, 0.62, 0.12, 1.0), roughness=0.38, metallic=0.25)
    mat_door_metal = create_pbr_material("Mat_RollupDoor", (0.28, 0.30, 0.34, 1.0), roughness=0.42, metallic=0.7)
    mat_glass = create_pbr_material("Mat_ShopGlass", (0.10, 0.14, 0.18, 1.0), roughness=0.08, metallic=0.1, specular=0.95)
    mat_sign_bg = create_pbr_material("Mat_SignboardDark", (0.08, 0.09, 0.10, 1.0), roughness=0.35, metallic=0.2)
    mat_sign_text = create_pbr_material("Mat_SignboardText", (0.95, 0.96, 0.98, 1.0), roughness=0.25, metallic=0.1, emissive_color=(0.95, 0.96, 0.98, 1.0), emissive_strength=1.8)

    # Main Building Shell (14m wide x 6m deep x 9m high)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 4.5))
    shell = bpy.context.active_object
    shell.name = "EZ_Building_Shell"
    shell.scale = (14.0, 6.0, 9.0)
    bpy.ops.object.transform_apply(scale=True)
    shell.data.materials.append(mat_dark_panel)

    # Upper Architectural Overhang / Cornice
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.3, 9.2))
    cornice = bpy.context.active_object
    cornice.name = "EZ_Cornice"
    cornice.scale = (14.8, 6.6, 0.6)
    bpy.ops.object.transform_apply(scale=True)
    cornice.data.materials.append(mat_concrete)

    # Recessed Storefront Entrance Cavity
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.5, -2.85, 2.1))
    entrance = bpy.context.active_object
    entrance.name = "EZ_Storefront_Doorway"
    entrance.scale = (7.5, 0.6, 4.2)
    bpy.ops.object.transform_apply(scale=True)
    entrance.data.materials.append(mat_door_metal)

    # Large Glass Show Windows
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, -2.9, 2.1))
    window = bpy.context.active_object
    window.name = "EZ_Shop_Window"
    window.scale = (3.6, 0.2, 4.2)
    bpy.ops.object.transform_apply(scale=True)
    window.data.materials.append(mat_glass)

    # Prominent Fascia Board / Signage Background
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.5, -3.2, 4.5))
    fascia = bpy.context.active_object
    fascia.name = "EZ_Sign_Board"
    fascia.scale = (8.0, 0.3, 1.2)
    bpy.ops.object.transform_apply(scale=True)
    fascia.data.materials.append(mat_sign_bg)

    # Sign placard
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.5, -3.4, 4.5))
    text_bar = bpy.context.active_object
    text_bar.name = "EZ_STUDIO_Text_Placard"
    text_bar.scale = (6.8, 0.15, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    text_bar.data.materials.append(mat_sign_text)

    # Yellow Industrial Truss / Overhead Framework
    truss_pts = [
        (-5.5, -3.0, 7.5),
        (-5.5, -5.2, 7.5),
        (2.5, -5.2, 7.5),
        (2.5, -3.0, 7.5),
    ]
    for i in range(len(truss_pts) - 1):
        p1 = truss_pts[i]
        p2 = truss_pts[i+1]
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
        dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=mid)
        beam = bpy.context.active_object
        beam.name = f"Truss_Beam_{i}"
        if abs(p2[0]-p1[0]) > abs(p2[1]-p1[1]):
            beam.scale = (dist, 0.25, 0.25)
        else:
            beam.scale = (0.25, dist, 0.25)
        bpy.ops.object.transform_apply(scale=True)
        beam.data.materials.append(mat_yellow_steel)

    # Diagonal Braces for Yellow Truss
    diagonals = [
        ((-5.5, -3.0, 6.0), (-5.5, -5.2, 7.5)),
        ((2.5, -3.0, 6.0), (2.5, -5.2, 7.5)),
    ]
    for i, (d1, d2) in enumerate(diagonals):
        mid = ((d1[0]+d2[0])/2, (d1[1]+d2[1])/2, (d1[2]+d2[2])/2)
        dist = math.sqrt((d2[0]-d1[0])**2 + (d2[1]-d1[1])**2 + (d2[2]-d1[2])**2)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=dist, location=mid)
        brace = bpy.context.active_object
        brace.name = f"Truss_Strut_{i}"
        brace.rotation_euler = (math.atan2(d2[1]-d1[1], d2[2]-d1[2]), 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
        brace.data.materials.append(mat_yellow_steel)

    # Upper Floor Louvers
    for k in range(5):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.0 + k * 1.8, -3.05, 6.8))
        louver = bpy.context.active_object
        louver.name = f"ZZZ_Louver_{k}"
        louver.scale = (1.2, 0.15, 2.2)
        bpy.ops.object.transform_apply(scale=True)
        louver.data.materials.append(mat_dark_panel)

    export_glb(OUTPUT_DIR / "building_ez_studio.glb")

# -------------------------------------------------------------
# 3. Building: HIA Modern Tower (45° Diagonal Slatted Facade)
# -------------------------------------------------------------
def build_hia_tower():
    reset_scene()
    print("Building HIA Tower with 45° Louvers...")
    
    mat_tower_concrete = create_pbr_material("Mat_HiaConcrete", (0.80, 0.82, 0.86, 1.0), roughness=0.62, metallic=0.08)
    mat_louver_metal = create_pbr_material("Mat_HiaLouverTitanium", (0.42, 0.46, 0.52, 1.0), roughness=0.35, metallic=0.65)
    mat_tower_glass = create_pbr_material("Mat_HiaCurtainGlass", (0.12, 0.18, 0.24, 1.0), roughness=0.06, metallic=0.15, specular=0.98)
    mat_hia_gold = create_pbr_material("Mat_HiaGoldLogo", (0.96, 0.78, 0.20, 1.0), roughness=0.30, metallic=0.80, emissive_color=(0.96, 0.78, 0.20, 1.0), emissive_strength=1.5)

    # Main Tower Mass (18m wide x 10m deep x 18m high)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 9.0))
    tower = bpy.context.active_object
    tower.name = "HIA_Tower_Main"
    tower.scale = (18.0, 10.0, 18.0)
    bpy.ops.object.transform_apply(scale=True)
    tower.data.materials.append(mat_tower_concrete)

    # Recessed Central Glass Curtain Wall
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -4.95, 10.0))
    glass_wall = bpy.context.active_object
    glass_wall.name = "HIA_Glass_Facade"
    glass_wall.scale = (14.0, 0.2, 14.0)
    bpy.ops.object.transform_apply(scale=True)
    glass_wall.data.materials.append(mat_tower_glass)

    # Iconic 45° Diagonal Louver Fins
    louver_count = 14
    for i in range(louver_count):
        y_pos = -5.15
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-6.0 + i * 1.0, y_pos, 10.0))
        fin = bpy.context.active_object
        fin.name = f"HIA_Diagonal_Fin_{i}"
        fin.scale = (0.22, 0.45, 15.0)
        fin.rotation_euler = (0, math.radians(45), 0)
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        fin.data.materials.append(mat_louver_metal)

    # Horizontal Balcony / Canopy
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -5.5, 3.2))
    balcony = bpy.context.active_object
    balcony.name = "HIA_Ground_Canopy"
    balcony.scale = (18.8, 2.2, 0.6)
    bpy.ops.object.transform_apply(scale=True)
    balcony.data.materials.append(mat_tower_concrete)

    # HIA Emblem / Logo Sign
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -5.6, 2.2))
    logo = bpy.context.active_object
    logo.name = "HIA_Logo_Plaque"
    logo.scale = (3.5, 0.2, 1.2)
    bpy.ops.object.transform_apply(scale=True)
    logo.data.materials.append(mat_hia_gold)

    export_glb(OUTPUT_DIR / "building_hia_tower.glb")

# -------------------------------------------------------------
# 4. Street Furniture & Props (Bench, Planter, Lamp, Bollard)
# -------------------------------------------------------------
def build_street_props():
    reset_scene()
    print("Building Street Props...")
    
    mat_concrete = create_pbr_material("Mat_BenchConcrete", (0.75, 0.77, 0.80, 1.0), roughness=0.65)
    mat_wood_slat = create_pbr_material("Mat_BenchWoodSlat", (0.24, 0.26, 0.28, 1.0), roughness=0.45, metallic=0.1)
    mat_metal_black = create_pbr_material("Mat_BollardBlack", (0.12, 0.13, 0.15, 1.0), roughness=0.35, metallic=0.85)
    mat_foliage = create_pbr_material("Mat_PlanterBush", (0.18, 0.38, 0.22, 1.0), roughness=0.75)
    mat_lamp_glass = create_pbr_material("Mat_LampLight", (0.95, 0.98, 1.0, 1.0), roughness=0.1, emissive_color=(0.95, 0.98, 1.0, 1.0), emissive_strength=3.0)
    mat_manhole = create_pbr_material("Mat_ManholeIron", (0.22, 0.24, 0.26, 1.0), roughness=0.38, metallic=0.90)

    # A. Modern Long Bench
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.18))
    bench_base = bpy.context.active_object
    bench_base.name = "Prop_Bench_Base"
    bench_base.scale = (2.4, 0.55, 0.36)
    bpy.ops.object.transform_apply(scale=True)
    bench_base.data.materials.append(mat_concrete)

    for s in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.18 + s * 0.18, 0.40))
        slat = bpy.context.active_object
        slat.name = f"Prop_Bench_Slat_{s}"
        slat.scale = (2.5, 0.14, 0.08)
        bpy.ops.object.transform_apply(scale=True)
        slat.data.materials.append(mat_wood_slat)

    # B. Urban Tree Planter Box
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(4.0, 0, 0.28))
    planter = bpy.context.active_object
    planter.name = "Prop_Planter_Box"
    planter.scale = (3.2, 1.1, 0.56)
    bpy.ops.object.transform_apply(scale=True)
    planter.data.materials.append(mat_concrete)

    for b in range(4):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(3.0 + b * 0.65, 0, 0.72))
        bush = bpy.context.active_object
        bush.name = f"Prop_Planter_Bush_{b}"
        bush.scale = (1.1, 1.0, 0.85)
        bpy.ops.object.transform_apply(scale=True)
        bush.data.materials.append(mat_foliage)

    # C. Minimalist Street Light
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(8.0, 0, 2.75))
    pole = bpy.context.active_object
    pole.name = "Prop_StreetLight_Pole"
    pole.scale = (0.16, 0.16, 5.5)
    bpy.ops.object.transform_apply(scale=True)
    pole.data.materials.append(mat_metal_black)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(8.4, 0, 5.42))
    arm = bpy.context.active_object
    arm.name = "Prop_StreetLight_Arm"
    arm.scale = (0.9, 0.16, 0.16)
    bpy.ops.object.transform_apply(scale=True)
    arm.data.materials.append(mat_metal_black)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(8.7, 0, 5.30))
    lum = bpy.context.active_object
    lum.name = "Prop_StreetLight_Emitter"
    lum.scale = (0.55, 0.22, 0.08)
    bpy.ops.object.transform_apply(scale=True)
    lum.data.materials.append(mat_lamp_glass)

    # D. Black Bollard
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.10, depth=0.85, location=(-3.0, 0, 0.425))
    bollard = bpy.context.active_object
    bollard.name = "Prop_Bollard"
    bollard.data.materials.append(mat_metal_black)

    # E. Circular Cast-Iron Manhole Plate
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.48, depth=0.03, location=(-5.0, 0, 0.015))
    manhole = bpy.context.active_object
    manhole.name = "Prop_Manhole"
    manhole.data.materials.append(mat_manhole)

    export_glb(OUTPUT_DIR / "props_street_set.glb")

# -------------------------------------------------------------
# 5. Companion Anime Cat (White & Amber running cat)
# -------------------------------------------------------------
def build_companion_cat():
    reset_scene()
    print("Building Companion Cat in running stride...")
    
    mat_cat_white = create_pbr_material("Mat_CatFurWhite", (0.95, 0.94, 0.92, 1.0), roughness=0.60)
    mat_cat_ginger = create_pbr_material("Mat_CatFurGinger", (0.88, 0.52, 0.22, 1.0), roughness=0.60)
    mat_cat_eyes = create_pbr_material("Mat_CatEyes", (0.25, 0.75, 0.85, 1.0), roughness=0.10, specular=0.9)
    mat_cat_nose = create_pbr_material("Mat_CatNosePink", (0.95, 0.70, 0.75, 1.0), roughness=0.40)

    # Cat Torso
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, 0.28))
    torso = bpy.context.active_object
    torso.name = "Cat_Body_Torso"
    torso.scale = (0.9, 1.9, 0.85)
    bpy.ops.object.transform_apply(scale=True)
    torso.data.materials.append(mat_cat_white)

    # Cat Chest & Neck
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0.22, 0.32))
    chest = bpy.context.active_object
    chest.name = "Cat_Chest"
    chest.scale = (0.85, 1.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    chest.data.materials.append(mat_cat_white)

    # Cat Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0, 0.38, 0.38))
    head = bpy.context.active_object
    head.name = "Cat_Head"
    head.scale = (1.0, 0.95, 0.90)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(mat_cat_white)

    # Snout
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0, 0.46, 0.34))
    snout = bpy.context.active_object
    snout.name = "Cat_Snout"
    snout.data.materials.append(mat_cat_nose)

    # Alert Ears
    for side, x in [("L", -0.06), ("R", 0.06)]:
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.04, depth=0.09, location=(x, 0.38, 0.48))
        ear = bpy.context.active_object
        ear.name = f"Cat_Ear_{side}"
        ear.rotation_euler = (math.radians(-15), math.radians(15 if side=="L" else -15), 0)
        bpy.ops.object.transform_apply(rotation=True)
        ear.data.materials.append(mat_cat_ginger)

    # Eyes
    for side, x in [("L", -0.05), ("R", 0.05)]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(x, 0.44, 0.39))
        eye = bpy.context.active_object
        eye.name = f"Cat_Eye_{side}"
        eye.data.materials.append(mat_cat_eyes)

    # Dynamic Running Legs
    # Front-Right
    bpy.ops.mesh.primitive_cylinder_add(radius=0.032, depth=0.22, location=(0.07, 0.26, 0.18))
    fr = bpy.context.active_object
    fr.name = "Cat_Leg_Front_R"
    fr.rotation_euler = (math.radians(35), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    fr.data.materials.append(mat_cat_white)

    # Front-Left
    bpy.ops.mesh.primitive_cylinder_add(radius=0.032, depth=0.20, location=(-0.07, 0.10, 0.17))
    fl = bpy.context.active_object
    fl.name = "Cat_Leg_Front_L"
    fl.rotation_euler = (math.radians(-25), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    fl.data.materials.append(mat_cat_white)

    # Rear-Left
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.24, location=(-0.08, -0.32, 0.16))
    rl = bpy.context.active_object
    rl.name = "Cat_Leg_Rear_L"
    rl.rotation_euler = (math.radians(-40), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    rl.data.materials.append(mat_cat_white)

    # Rear-Right
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.22, location=(0.08, -0.12, 0.16))
    rr = bpy.context.active_object
    rr.name = "Cat_Leg_Rear_R"
    rr.rotation_euler = (math.radians(20), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    rr.data.materials.append(mat_cat_white)

    # Tail
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.28, location=(0, -0.32, 0.40))
    tail = bpy.context.active_object
    tail.name = "Cat_Tail"
    tail.rotation_euler = (math.radians(50), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    tail.data.materials.append(mat_cat_ginger)

    export_glb(OUTPUT_DIR / "companion_cat.glb")

# -------------------------------------------------------------
# 6. Plaza Ground Mesh (with Curb, Blind Strip & PBR Mapping)
# -------------------------------------------------------------
def build_plaza_ground_mesh():
    reset_scene()
    print("Building Plaza Ground Mesh with Curbs & Blind Lane...")
    
    mat_plaza_paver = create_pbr_material("Mat_PlazaPaverWet", (0.35, 0.38, 0.42, 1.0), roughness=0.32, metallic=0.08, specular=0.75)
    mat_sidewalk = create_pbr_material("Mat_SidewalkStone", (0.58, 0.60, 0.64, 1.0), roughness=0.55, metallic=0.02)
    mat_curb = create_pbr_material("Mat_CurbStone", (0.68, 0.70, 0.74, 1.0), roughness=0.50)
    mat_tactile = create_pbr_material("Mat_TactileYellow", (0.92, 0.72, 0.18, 1.0), roughness=0.45, metallic=0.05)
    mat_bike_line = create_pbr_material("Mat_RoadMarkingWhite", (0.90, 0.92, 0.95, 1.0), roughness=0.40)

    # Main Plaza Floor: 40m x 45m
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(5.0, 0, 0))
    plaza = bpy.context.active_object
    plaza.name = "Plaza_Main_Pavement"
    plaza.scale = (40.0, 45.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    plaza.data.materials.append(mat_plaza_paver)

    # Left Raised Sidewalk (Height +0.15m, Width 8m x 45m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-15.0, 0, 0.075))
    sidewalk = bpy.context.active_object
    sidewalk.name = "Plaza_Sidewalk_Raised"
    sidewalk.scale = (8.0, 45.0, 0.15)
    bpy.ops.object.transform_apply(scale=True)
    sidewalk.data.materials.append(mat_sidewalk)

    # Curb Stone Edge (Width 0.35m, Height 0.18m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-11.0, 0, 0.09))
    curb = bpy.context.active_object
    curb.name = "Plaza_Curb_Stone"
    curb.scale = (0.35, 45.0, 0.18)
    bpy.ops.object.transform_apply(scale=True)
    curb.data.materials.append(mat_curb)

    # Tactile Paving Strip (Yellow Blind Lane)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.5, 0, 0.012))
    tactile_strip = bpy.context.active_object
    tactile_strip.name = "Tactile_Blind_Lane_Main"
    tactile_strip.scale = (0.60, 45.0, 0.024)
    bpy.ops.object.transform_apply(scale=True)
    tactile_strip.data.materials.append(mat_tactile)

    # Diagonal branch towards center plaza
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.0, -2.0, 0.012))
    tactile_diag = bpy.context.active_object
    tactile_diag.name = "Tactile_Blind_Lane_Branch"
    tactile_diag.scale = (0.60, 14.0, 0.024)
    tactile_diag.rotation_euler = (0, 0, math.radians(-35))
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    tactile_diag.data.materials.append(mat_tactile)

    # Bike Lane Graphic Decal / Line
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-6.0, 0, 0.010))
    bike_line = bpy.context.active_object
    bike_line.name = "Road_White_Line"
    bike_line.scale = (0.15, 45.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    bike_line.data.materials.append(mat_bike_line)

    export_glb(OUTPUT_DIR / "plaza_ground_mesh.glb")

# -------------------------------------------------------------
# Main Execution Entry
# -------------------------------------------------------------
if __name__ == "__main__":
    print("=== STARTING LUMINA PLAZA ASSET GENERATION ===")
    build_monument_red_ring()
    build_ez_studio()
    build_hia_tower()
    build_street_props()
    build_companion_cat()
    build_plaza_ground_mesh()
    print("=== ALL LUMINA PLAZA ASSETS GENERATED SUCCESSFULLY ===")
