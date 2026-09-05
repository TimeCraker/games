import bpy
import bmesh
import math
import os
import sys

# -------------------------------------------------------------
# 0. SETUP & MATERIAL HELPERS
# -------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def find_texture(tex_name):
    paths = [
        os.path.abspath(f"asternova/art/textures/golden_slice/{tex_name}"),
        os.path.abspath(f"art/textures/golden_slice/{tex_name}")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def create_pbr_material(name, tex_base, base_color_fallback=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, uv_scale=(1.0, 1.0), normal_strength=1.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = base_color_fallback
    bsdf.inputs['Roughness'].default_value = roughness_val
    bsdf.inputs['Metallic'].default_value = metallic_val
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    albedo_path = find_texture(f"{tex_base}_albedo.png")
    normal_path = find_texture(f"{tex_base}_normal.png")
    roughness_path = find_texture(f"{tex_base}_roughness.png")
    ao_path = find_texture(f"{tex_base}_ao.png")
    
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (uv_scale[0], uv_scale[1], 1.0)
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    
    if albedo_path:
        tex_alb = nodes.new(type='ShaderNodeTexImage')
        tex_alb.image = bpy.data.images.load(albedo_path)
        links.new(mapping.outputs['Vector'], tex_alb.inputs['Vector'])
        if ao_path:
            tex_ao = nodes.new(type='ShaderNodeTexImage')
            tex_ao.image = bpy.data.images.load(ao_path)
            tex_ao.image.colorspace_settings.name = 'Non-Color'
            links.new(mapping.outputs['Vector'], tex_ao.inputs['Vector'])
            mix_ao = nodes.new(type='ShaderNodeMix')
            mix_ao.data_type = 'RGBA'
            mix_ao.blend_type = 'MULTIPLY'
            mix_ao.inputs['Factor'].default_value = 0.8
            links.new(tex_alb.outputs['Color'], mix_ao.inputs[6])
            links.new(tex_ao.outputs['Color'], mix_ao.inputs[7])
            links.new(mix_ao.outputs[2], bsdf.inputs['Base Color'])
        else:
            links.new(tex_alb.outputs['Color'], bsdf.inputs['Base Color'])
            
    if roughness_path:
        tex_rough = nodes.new(type='ShaderNodeTexImage')
        tex_rough.image = bpy.data.images.load(roughness_path)
        tex_rough.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], tex_rough.inputs['Vector'])
        links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])
        
    if normal_path:
        tex_nor = nodes.new(type='ShaderNodeTexImage')
        tex_nor.image = bpy.data.images.load(normal_path)
        tex_nor.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping.outputs['Vector'], tex_nor.inputs['Vector'])
        nor_map = nodes.new(type='ShaderNodeNormalMap')
        nor_map.inputs['Strength'].default_value = normal_strength
        links.new(tex_nor.outputs['Color'], nor_map.inputs['Color'])
        links.new(nor_map.outputs['Normal'], bsdf.inputs['Normal'])
        
    return mat

def create_glass_material(name="M_Glass", tint=(0.92, 0.96, 0.98, 1.0)):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = tint
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    bsdf.inputs['IOR'].default_value = 1.52
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_emissive_material(name, color=(1.0, 0.95, 0.85, 1.0), strength=3.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    emit = nodes.new(type='ShaderNodeEmission')
    emit.inputs['Color'].default_value = color
    emit.inputs['Strength'].default_value = strength
    links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return mat

def create_transformer_material(name="M_Transformer"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.32, 0.34, 0.35, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.70
    bsdf.inputs['Roughness'].default_value = 0.65
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_custom_colored_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def apply_bevel(obj, width=0.03, segments=2):
    bev = obj.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = width
    bev.segments = segments
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(35)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def build_catenary_curve(name, p_start, p_end, sag=0.35, segments=24, radius=0.012, material=None):
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
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj

# -------------------------------------------------------------
# 1. TACTICAL ROAD NETWORK & SLOPED TERRAIN
# -------------------------------------------------------------
def build_terrain_and_roads(mats):
    col = bpy.data.collections.new("01_Roads_And_Terrain")
    bpy.context.scene.collection.children.link(col)
    
    slope_angle = math.atan2(6.0, 35.0) # ~ 9.7 deg / 17% slope
    
    # 1. South Flat Plaza Roadway: Y in [10.0, 30.0], X in [-4.0, 4.0], Z = 0.0
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 20.0, 0.0))
    plaza_road = bpy.context.active_object
    plaza_road.name = "Road_South_Plaza"
    plaza_road.scale = (8.0, 20.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plaza_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(plaza_road)
    bpy.context.collection.objects.unlink(plaza_road)
    
    # South Plaza Sidewalk (West side):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, 20.0, 0.075))
    plz_sw_w = bpy.context.active_object
    plz_sw_w.name = "Sidewalk_Plaza_West"
    plz_sw_w.scale = (10.0, 20.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_sw_w.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(plz_sw_w)
    bpy.context.collection.objects.unlink(plz_sw_w)
    
    # Plaza Curb:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.1, 20.0, 0.075))
    curb_w = bpy.context.active_object
    curb_w.name = "Curb_Plaza_West"
    curb_w.scale = (0.2, 20.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    curb_w.data.materials.append(mats['concrete_curb'])
    apply_bevel(curb_w, width=0.02, segments=2)
    col.objects.link(curb_w)
    bpy.context.collection.objects.unlink(curb_w)
    
    # Plaza Tactile Line:
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-4.8, 20.0, 0.152))
    plz_tac = bpy.context.active_object
    plz_tac.name = "Tactile_Plaza_West"
    plz_tac.scale = (0.6, 20.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plz_tac.data.materials.append(mats['tactile_paving'])
    col.objects.link(plz_tac)
    bpy.context.collection.objects.unlink(plz_tac)
    
    # 2. Central Tactical Long Slope Roadway (40m Long Ramp):
    # Runs from Y = +10.0 (Z = 0.0) up to Y = -25.0 (Z = 6.0m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -7.5, 3.0))
    ramp_road = bpy.context.active_object
    ramp_road.name = "Road_Central_Slope_Ramp"
    ramp_road.scale = (7.0, 35.5, 0.2)
    ramp_road.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_road.data.materials.append(mats['asphalt_road'])
    col.objects.link(ramp_road)
    bpy.context.collection.objects.unlink(ramp_road)
    
    # Slope West Sidewalk:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-5.0, -7.5, 3.12))
    ramp_sw = bpy.context.active_object
    ramp_sw.name = "Sidewalk_Central_Slope_West"
    ramp_sw.scale = (2.6, 35.5, 0.2)
    ramp_sw.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_sw.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(ramp_sw)
    bpy.context.collection.objects.unlink(ramp_sw)
    
    # Slope West Curb:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.6, -7.5, 3.10))
    ramp_curb = bpy.context.active_object
    ramp_curb.name = "Curb_Central_Slope_West"
    ramp_curb.scale = (0.2, 35.5, 0.25)
    ramp_curb.rotation_euler = (slope_angle, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ramp_curb.data.materials.append(mats['concrete_curb'])
    apply_bevel(ramp_curb, width=0.02, segments=2)
    col.objects.link(ramp_curb)
    bpy.context.collection.objects.unlink(ramp_curb)
    
    # 3. North High Terrace Platform: Y in [-38.0, -25.0], Z = 6.0m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -31.5, 5.9))
    terrace = bpy.context.active_object
    terrace.name = "North_High_Terrace_Platform"
    terrace.scale = (26.0, 13.0, 0.4)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    terrace.data.materials.append(mats['sidewalk_tiles'])
    col.objects.link(terrace)
    bpy.context.collection.objects.unlink(terrace)
    
    # Retaining Stone Wall facing South at Y = -25.0:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -25.2, 3.0))
    retaining_wall = bpy.context.active_object
    retaining_wall.name = "North_Terrace_Retaining_Wall"
    retaining_wall.scale = (26.0, 0.6, 6.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    retaining_wall.data.materials.append(mats['concrete_curb'])
    apply_bevel(retaining_wall, width=0.05, segments=2)
    col.objects.link(retaining_wall)
    bpy.context.collection.objects.unlink(retaining_wall)
    
    # Torii Gate on High Terrace at (0.0, -32.0, 6.1):
    torii_col = bpy.data.collections.new("High_Terrace_Torii")
    col.children.link(torii_col)
    m_vermilion = create_custom_colored_material("M_ToriiVermilion", (0.85, 0.18, 0.08, 1.0), roughness=0.45)
    m_black_cap = create_custom_colored_material("M_ToriiBlackCap", (0.08, 0.08, 0.09, 1.0), roughness=0.50)
    
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
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, -32.0, 10.08))
    k_cap = bpy.context.active_object
    k_cap.scale = (4.6, 0.42, 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    k_cap.data.materials.append(m_black_cap)
    torii_col.objects.link(k_cap)
    bpy.context.collection.objects.unlink(k_cap)
    
    # 4. Zebra Crossing Markings at base of slope (Y = 10.0):
    m_white_paint = create_custom_colored_material("M_WhiteRoadPaint", (0.88, 0.89, 0.88, 1.0), roughness=0.65)
    for z_i in range(8):
        zx = -3.0 + z_i * 0.85
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(zx, 10.0, 0.005))
        stripe = bpy.context.active_object
        stripe.name = f"Zebra_Stripe_{z_i}"
        stripe.scale = (0.45, 2.8, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        stripe.data.materials.append(m_white_paint)
        col.objects.link(stripe)
        bpy.context.collection.objects.unlink(stripe)
        
    # 5. Circular Manhole Cover in Plaza:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.40, depth=0.02, location=(-1.2, 16.0, 0.005))
    mh = bpy.context.active_object
    mh.name = "Plaza_Manhole"
    mh.data.materials.append(mats['metal_manhole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(mh)
    bpy.context.collection.objects.unlink(mh)
    
    # 6. Slotted Gutter Drain Grates along slope curb:
    for d_idx, dy in enumerate([2.0, -8.0, -18.0]):
        dz = 3.0 + ((-7.5 - dy) / 35.0) * -6.0
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-3.4, dy, dz + 0.02))
        dg = bpy.context.active_object
        dg.name = f"Slope_Drain_Grate_{d_idx}"
        dg.scale = (0.28, 0.85, 0.02)
        dg.rotation_euler = (slope_angle, 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        dg.data.materials.append(mats['metal_manhole'])
        col.objects.link(dg)
        bpy.context.collection.objects.unlink(dg)
        
    return col

# -------------------------------------------------------------
# 2. HOUSE_A: STANDARD 2F RESIDENCE WITH BALCONY & CARPORT
# -------------------------------------------------------------
def build_house_a(mats):
    col = bpy.data.collections.new("02_House_A_Standard")
    bpy.context.scene.collection.children.link(col)
    
    hx = -14.25
    hy = -5.25
    hz_base = 2.5
    
    # Foundation Plinth:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 0.25))
    plinth = bpy.context.active_object
    plinth.name = "House_A_Plinth"
    plinth.scale = (7.6, 10.6, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.03, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 1F Main Volume:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 1.9))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = "House_A_1F_Wall"
    bldg_1f.scale = (7.4, 10.4, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    # Belt Course Band:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 3.35))
    belt = bpy.context.active_object
    belt.name = "House_A_Belt_Course"
    belt.scale = (7.5, 10.5, 0.14)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 2F Main Volume:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx - 0.4, hy, hz_base + 4.8))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = "House_A_2F_Wall"
    bldg_2f.scale = (6.6, 10.4, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    # Roof Slab & Eaves:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 6.3))
    roof = bpy.context.active_object
    roof.name = "House_A_Roof"
    roof.scale = (8.0, 11.0, 0.25)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # --- 2F Cantilevered Balcony (挑檐阳台) ---
    # Center X = -9.7, Y = -5.25, Floor Z = 4.5. Width along Y = 4.4m, protrusion in X = 1.6m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.7, hy, 4.45))
    balc_slab = bpy.context.active_object
    balc_slab.name = "House_A_Balcony_Floor"
    balc_slab.scale = (1.6, 4.4, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc_slab.data.materials.append(mats['concrete_curb'])
    apply_bevel(balc_slab, width=0.02, segments=2)
    col.objects.link(balc_slab)
    bpy.context.collection.objects.unlink(balc_slab)
    
    # Balcony Handrail
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=4.4, location=(-8.92, hy, 5.50))
    front_rail = bpy.context.active_object
    front_rail.rotation_euler = (math.radians(90), 0, 0)
    front_rail.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(front_rail)
    bpy.context.collection.objects.unlink(front_rail)
    
    # Balcony Glass Panels
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.92, hy, 4.95))
    balc_glass = bpy.context.active_object
    balc_glass.scale = (0.02, 4.3, 0.85)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    balc_glass.data.materials.append(mats['glass'])
    col.objects.link(balc_glass)
    bpy.context.collection.objects.unlink(balc_glass)
    
    # Side Return Railings
    for s_y in [hy - 2.18, hy + 2.18]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.55, location=(-9.7, s_y, 5.50))
        side_rail = bpy.context.active_object
        side_rail.rotation_euler = (0, math.radians(90), 0)
        side_rail.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        col.objects.link(side_rail)
        bpy.context.collection.objects.unlink(side_rail)
        
    # Balcony Sliding Double Glass Doors
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.55, hy, 5.55))
    b_door = bpy.context.active_object
    b_door.name = "House_A_Balcony_Glass_Door"
    b_door.scale = (0.08, 2.4, 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    b_door.data.materials.append(mats['glass'])
    col.objects.link(b_door)
    bpy.context.collection.objects.unlink(b_door)
    
    # --- Side Carport with Polycarbonate Canopy (紧凑车位) ---
    cp_col = bpy.data.collections.new("House_A_Carport")
    col.children.link(cp_col)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, -8.3, 2.75))
    cp_pad = bpy.context.active_object
    cp_pad.scale = (3.4, 4.8, 0.12)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cp_pad.data.materials.append(mats['concrete_curb'])
    cp_col.objects.link(cp_pad)
    bpy.context.collection.objects.unlink(cp_pad)
    
    m_polycarb = create_custom_colored_material("M_PolycarbonateCanopy", (0.15, 0.18, 0.20, 0.85), roughness=0.15)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-9.0, -8.3, 5.1))
    canopy = bpy.context.active_object
    canopy.scale = (3.2, 4.6, 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(m_polycarb)
    cp_col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    for p_y in [-9.8, -6.8]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2.4, location=(-7.5, p_y, 3.95))
        cp_post = bpy.context.active_object
        cp_post.data.materials.append(mats['aluminum_dark'])
        bpy.ops.object.shade_smooth()
        cp_col.objects.link(cp_post)
        bpy.context.collection.objects.unlink(cp_post)
        
    m_rubber = create_custom_colored_material("M_RubberWheelStop", (0.10, 0.10, 0.10, 1.0), roughness=0.85)
    for ws_x in [-9.5, -8.5]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ws_x, -10.2, 2.86))
        ws = bpy.context.active_object
        ws.scale = (0.18, 0.65, 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ws.data.materials.append(m_rubber)
        apply_bevel(ws, width=0.015, segments=2)
        cp_col.objects.link(ws)
        bpy.context.collection.objects.unlink(ws)
        
    # AC Unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.3, -2.0, 3.22))
    ac_body = bpy.context.active_object
    ac_body.name = "House_A_AC_Unit"
    ac_body.scale = (0.35, 0.85, 0.64)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_body.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_body, width=0.02, segments=2)
    col.objects.link(ac_body)
    bpy.context.collection.objects.unlink(ac_body)
    
    return col

# -------------------------------------------------------------
# 3. HOUSE_C: SLOPED RESIDENCE & TACTICAL WALL-BOUNCE ALLEYWAY
# -------------------------------------------------------------
def build_house_c_and_alleyway(mats):
    col = bpy.data.collections.new("03_House_C_And_Alleyway")
    bpy.context.scene.collection.children.link(col)
    
    hx = -14.25
    hy = 8.5
    hz_base = 0.8
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 0.3))
    plinth = bpy.context.active_object
    plinth.name = "House_C_Plinth"
    plinth.scale = (7.6, 9.8, 0.6)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.03, segments=2)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 1F Main Wall: North Face strictly at Y = 3.5 (Wall Bounce South Wall)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 1.85))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = "House_C_1F_Wall"
    bldg_1f.scale = (7.4, 9.6, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 3.25))
    belt = bpy.context.active_object
    belt.scale = (7.5, 9.7, 0.12)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 4.7))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = "House_C_2F_Wall"
    bldg_2f.scale = (7.4, 9.6, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz_base + 6.2))
    roof = bpy.context.active_object
    roof.name = "House_C_Roof"
    roof.scale = (7.9, 10.1, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    apply_bevel(roof, width=0.03, segments=2)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # Perimeter 2.2m Privacy Fence & Iron Gate
    fence_col = bpy.data.collections.new("House_C_Fence")
    col.children.link(fence_col)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.4, 11.0, 0.70))
    fc_base = bpy.context.active_object
    fc_base.scale = (0.24, 4.8, 1.40)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fc_base.data.materials.append(mats['concrete_curb'])
    apply_bevel(fc_base, width=0.02, segments=2)
    fence_col.objects.link(fc_base)
    bpy.context.collection.objects.unlink(fc_base)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.4, 11.0, 1.80))
    fc_grille = bpy.context.active_object
    fc_grille.scale = (0.06, 4.7, 0.80)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fc_grille.data.materials.append(mats['aluminum_dark'])
    fence_col.objects.link(fc_grille)
    bpy.context.collection.objects.unlink(fc_grille)
    
    m_gate = create_custom_colored_material("M_IronGate", (0.16, 0.16, 0.17, 1.0), roughness=0.45, metallic=0.75)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-10.4, 7.2, 1.10))
    gate = bpy.context.active_object
    gate.name = "House_C_Iron_Gate"
    gate.scale = (0.08, 1.15, 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    gate.data.materials.append(m_gate)
    apply_bevel(gate, width=0.015, segments=2)
    fence_col.objects.link(gate)
    bpy.context.collection.objects.unlink(gate)
    
    # Alley AC Unit
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-12.5, 3.65, 2.4))
    ac_alley = bpy.context.active_object
    ac_alley.name = "Alley_AC_Compressor"
    ac_alley.scale = (0.85, 0.35, 0.65)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_alley.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_alley, width=0.02, segments=2)
    col.objects.link(ac_alley)
    bpy.context.collection.objects.unlink(ac_alley)
    
    w1 = build_catenary_curve("Alley_Wire_Crossing", (-15.0, 0.05, 4.6), (-11.0, 3.45, 4.4), sag=0.22, radius=0.008, material=mats['cable_rubber'])
    col.objects.link(w1)
    bpy.context.collection.objects.unlink(w1)
    
    return col

# -------------------------------------------------------------
# 4. HOUSE_B: CORNER 24H CONVENIENCE STORE & VENDING MACHINES
# -------------------------------------------------------------
def build_house_b_convenience_store(mats):
    col = bpy.data.collections.new("04_House_B_Convenience_Store")
    bpy.context.scene.collection.children.link(col)
    
    bx = -13.25
    by = 21.5
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx, by, 0.15))
    plinth = bpy.context.active_object
    plinth.name = "Store_Plinth"
    plinth.scale = (9.4, 11.0, 0.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.5, by, 1.85))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = "Store_1F_Main_Wall"
    bldg_1f.scale = (8.4, 10.6, 3.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    # Storefront Panoramic Glass
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.55, by, 1.75))
    glass_wall = bpy.context.active_object
    glass_wall.name = "Store_Glass_Facade"
    glass_wall.scale = (0.05, 9.8, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    glass_wall.data.materials.append(mats['glass'])
    col.objects.link(glass_wall)
    bpy.context.collection.objects.unlink(glass_wall)
    
    for my in [by - 3.2, by - 1.2, by + 1.2, by + 3.2]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.52, my, 1.75))
        mullion = bpy.context.active_object
        mullion.scale = (0.12, 0.08, 2.85)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mullion.data.materials.append(mats['aluminum_dark'])
        col.objects.link(mullion)
        bpy.context.collection.objects.unlink(mullion)
        
    # Storefront Emissive Sign Lightbox:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-8.42, by, 3.85))
    sign_box = bpy.context.active_object
    sign_box.name = "Store_Sign_Lightbox"
    sign_box.scale = (0.24, 9.8, 1.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m_sign_glow = create_emissive_material("M_ConvenienceStoreSign", (0.20, 0.85, 0.95, 1.0), strength=2.8)
    sign_box.data.materials.append(m_sign_glow)
    apply_bevel(sign_box, width=0.02, segments=2)
    col.objects.link(sign_box)
    bpy.context.collection.objects.unlink(sign_box)
    
    # Awning Canopy:
    m_awning = create_custom_colored_material("M_StoreAwning", (0.12, 0.45, 0.78, 1.0), roughness=0.75)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.95, by, 3.15))
    awning = bpy.context.active_object
    awning.name = "Store_Awning_Canopy"
    awning.scale = (1.10, 8.8, 0.08)
    awning.rotation_euler = (0, math.radians(18), 0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    awning.data.materials.append(m_awning)
    col.objects.link(awning)
    bpy.context.collection.objects.unlink(awning)
    
    # 2F Floor
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.5, by, 5.2))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = "Store_2F_Wall"
    bldg_2f.scale = (8.4, 10.6, 2.7)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx - 0.5, by, 6.65))
    roof = bpy.context.active_object
    roof.scale = (8.8, 11.0, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # Vending Machines
    vm_col = bpy.data.collections.new("Store_Vending_Machines")
    col.children.link(vm_col)
    m_vm_red = create_custom_colored_material("M_Vending_Red", (0.85, 0.12, 0.10, 1.0), roughness=0.35, metallic=0.15)
    m_vm_blue = create_custom_colored_material("M_Vending_Blue", (0.08, 0.35, 0.85, 1.0), roughness=0.35, metallic=0.15)
    m_vm_glass = create_emissive_material("M_Vending_Window", (0.95, 0.98, 1.0, 1.0), strength=2.2)
    
    for vm_idx, (vm_y, vm_mat) in enumerate([(17.5, m_vm_red), (19.0, m_vm_blue)]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.8, vm_y, 1.08))
        vm = bpy.context.active_object
        vm.name = f"Vending_Machine_{vm_idx}"
        vm.scale = (0.75, 0.95, 1.85)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        vm.data.materials.append(vm_mat)
        apply_bevel(vm, width=0.015, segments=2)
        vm_col.objects.link(vm)
        bpy.context.collection.objects.unlink(vm)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.41, vm_y, 1.35))
        disp = bpy.context.active_object
        disp.name = f"Vending_Display_{vm_idx}"
        disp.scale = (0.04, 0.82, 0.90)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        disp.data.materials.append(m_vm_glass)
        vm_col.objects.link(disp)
        bpy.context.collection.objects.unlink(disp)
        
    return col

# -------------------------------------------------------------
# 5. STREET PROPS KIT (DETAILED MUNICIPAL OBJECTS)
# -------------------------------------------------------------
def build_street_props_kit(mats):
    col = bpy.data.collections.new("05_Street_Props_Kit")
    bpy.context.scene.collection.children.link(col)
    
    # 1. Japanese Street Sorting Trash Bins (分类塑料垃圾桶 x3: 蓝/绿/灰)
    m_bin_blue = create_custom_colored_material("M_BinBlue", (0.12, 0.42, 0.82, 1.0), roughness=0.55)
    m_bin_green = create_custom_colored_material("M_BinGreen", (0.18, 0.65, 0.28, 1.0), roughness=0.55)
    m_bin_gray = create_custom_colored_material("M_BinGray", (0.28, 0.30, 0.32, 1.0), roughness=0.55)
    
    for b_idx, (by_off, b_mat, b_type) in enumerate([(0.0, m_bin_blue, "Cans"), (0.50, m_bin_green, "Burnable"), (1.00, m_bin_gray, "Plastic")]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-7.8, 20.6 + by_off, 0.62))
        bin_body = bpy.context.active_object
        bin_body.name = f"TrashBin_{b_type}"
        bin_body.scale = (0.42, 0.42, 0.92)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bin_body.data.materials.append(b_mat)
        apply_bevel(bin_body, width=0.02, segments=2)
        col.objects.link(bin_body)
        bpy.context.collection.objects.unlink(bin_body)
        
    # 2. Fluorescent Traffic Safety Cones (反光锥 x4)
    m_cone_orange = create_custom_colored_material("M_ConeOrange", (0.95, 0.32, 0.04, 1.0), roughness=0.40)
    m_cone_white = create_custom_colored_material("M_ConeReflective", (0.95, 0.95, 0.95, 1.0), roughness=0.20, metallic=0.1)
    m_cone_base = create_custom_colored_material("M_ConeBlackBase", (0.12, 0.12, 0.13, 1.0), roughness=0.85)
    
    cone_coords = [(-3.7, 13.2), (-3.6, 14.1), (-3.8, 15.0), (-3.7, 15.8)]
    for c_i, (cx, cy) in enumerate(cone_coords):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, 0.025))
        c_base = bpy.context.active_object
        c_base.name = f"Traffic_Cone_{c_i}_Base"
        c_base.scale = (0.38, 0.38, 0.05)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        c_base.data.materials.append(m_cone_base)
        col.objects.link(c_base)
        bpy.context.collection.objects.unlink(c_base)
        
        bpy.ops.mesh.primitive_cone_add(radius1=0.15, radius2=0.025, depth=0.70, location=(cx, cy, 0.40))
        cone_body = bpy.context.active_object
        cone_body.name = f"Traffic_Cone_{c_i}_Body"
        cone_body.data.materials.append(m_cone_orange)
        bpy.ops.object.shade_smooth()
        col.objects.link(cone_body)
        bpy.context.collection.objects.unlink(cone_body)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=0.14, location=(cx, cy, 0.45))
        band = bpy.context.active_object
        band.name = f"Traffic_Cone_{c_i}_ReflectiveStripe"
        band.data.materials.append(m_cone_white)
        bpy.ops.object.shade_smooth()
        col.objects.link(band)
        bpy.context.collection.objects.unlink(band)
        
    # 3. Road Corner Convex Safety Mirror (道路转角凸面广角镜)
    mirror_col = bpy.data.collections.new("Convex_Safety_Mirror")
    col.children.link(mirror_col)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=3.2, location=(-4.0, 0.5, 1.75))
    m_pole = bpy.context.active_object
    m_pole.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    mirror_col.objects.link(m_pole)
    bpy.context.collection.objects.unlink(m_pole)
    
    m_mirror_yellow = create_custom_colored_material("M_MirrorYellow", (0.95, 0.75, 0.05, 1.0), roughness=0.35)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.12, location=(-4.0, 0.5, 3.25))
    m_back = bpy.context.active_object
    m_back.rotation_euler = (math.radians(15), math.radians(45), 0)
    m_back.data.materials.append(m_mirror_yellow)
    bpy.ops.object.shade_smooth()
    mirror_col.objects.link(m_back)
    bpy.context.collection.objects.unlink(m_back)
    
    m_chrome_mirror = create_custom_colored_material("M_ChromeMirror", (0.95, 0.95, 0.98, 1.0), roughness=0.02, metallic=0.98)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.42, location=(-3.94, 0.56, 3.28))
    m_face = bpy.context.active_object
    m_face.scale = (1.0, 1.0, 0.25)
    m_face.rotation_euler = (math.radians(15), math.radians(45), 0)
    m_face.data.materials.append(m_chrome_mirror)
    bpy.ops.object.shade_smooth()
    mirror_col.objects.link(m_face)
    bpy.context.collection.objects.unlink(m_face)
    
    # 4. Japanese Red Fire Hydrant Box (消火栓)
    m_hydrant_red = create_custom_colored_material("M_FireHydrantRed", (0.85, 0.10, 0.08, 1.0), roughness=0.42, metallic=0.60)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-4.5, 6.0, 0.75))
    hydrant = bpy.context.active_object
    hydrant.name = "Fire_Hydrant_Cabinet"
    hydrant.scale = (0.35, 0.65, 1.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    hydrant.data.materials.append(m_hydrant_red)
    apply_bevel(hydrant, width=0.02, segments=2)
    col.objects.link(hydrant)
    bpy.context.collection.objects.unlink(hydrant)
    
    m_red_glow = create_emissive_material("M_HydrantBeaconRed", (1.0, 0.05, 0.05, 1.0), strength=3.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.06, location=(-4.5, 6.0, 1.36))
    beacon = bpy.context.active_object
    beacon.data.materials.append(m_red_glow)
    bpy.ops.object.shade_smooth()
    col.objects.link(beacon)
    bpy.context.collection.objects.unlink(beacon)
    
    # 5. Full Utility Pole Assembly with Transformer and Catenary Lines
    pole_x = -3.8
    pole_y = -3.2
    pole_h = 9.6
    base_z = 2.4
    
    mesh = bpy.data.meshes.new("District_Utility_Pole")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=24, radius1=0.17, radius2=0.10, depth=pole_h)
    bm.to_mesh(mesh)
    bm.free()
    pole_obj = bpy.data.objects.new("District_Utility_Pole", mesh)
    pole_obj.location = (pole_x, pole_y, base_z + pole_h * 0.5)
    pole_obj.data.materials.append(mats['utility_pole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(pole_obj)
    
    # Transformer on pole
    trans_z = base_z + 5.5
    bpy.ops.mesh.primitive_cylinder_add(radius=0.30, depth=0.85, location=(pole_x - 0.35, pole_y, trans_z))
    t_body = bpy.context.active_object
    t_body.name = "District_Transformer_Body"
    t_body.data.materials.append(mats['transformer'])
    bpy.ops.object.shade_smooth()
    col.objects.link(t_body)
    bpy.context.collection.objects.unlink(t_body)
    
    # Crossarms
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x, pole_y, base_z + 8.2))
    arm = bpy.context.active_object
    arm.scale = (0.12, 2.4, 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    arm.data.materials.append(mats['aluminum_silver'])
    col.objects.link(arm)
    bpy.context.collection.objects.unlink(arm)
    
    # Overhead Catenary Cable spanning down street
    c1 = build_catenary_curve("District_Main_Cable", (pole_x, -28.0, 11.5), (pole_x, 26.0, 6.8), sag=1.2, radius=0.012, material=mats['cable_rubber'])
    col.objects.link(c1)
    bpy.context.collection.objects.unlink(c1)
    
    return col

# -------------------------------------------------------------
# 6. LIGHTING & ENVIRONMENT
# -------------------------------------------------------------
def setup_lighting():
    world = bpy.data.worlds.new("Neighborhood_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_links = world.node_tree.links
    w_nodes.clear()
    
    w_out = w_nodes.new(type='ShaderNodeOutputWorld')
    bg = w_nodes.new(type='ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.80
    
    sky = w_nodes.new(type='ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(42.0)
    sky.sun_rotation = math.radians(130.0)
    sky.altitude = 10.0
    sky.air_density = 1.0
    sky.aerosol_density = 0.8
    sky.ozone_density = 1.2
    sky.sun_disc = True
    
    w_links.new(sky.outputs['Color'], bg.inputs['Color'])
    w_links.new(bg.outputs['Background'], w_out.inputs['Surface'])
    
    sun_data = bpy.data.lights.new(name="Sun_Key_Light", type='SUN')
    sun_data.energy = 1.6
    sun_data.angle = math.radians(1.2)
    sun_data.color = (1.0, 0.98, 0.94)
    
    sun_obj = bpy.data.objects.new("Sun_Key_Light", sun_data)
    sun_obj.rotation_euler = (math.radians(48), math.radians(22), math.radians(-55))
    bpy.context.scene.collection.objects.link(sun_obj)

# -------------------------------------------------------------
# 7. CAMERAS & INSPECTION VIEWS
# -------------------------------------------------------------
def point_camera_at(cam_obj, target_loc):
    import mathutils
    cam_loc = cam_obj.location
    direction = mathutils.Vector(target_loc) - cam_loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def setup_inspection_cameras():
    cameras = {}
    
    # 01. Panorama
    c1_data = bpy.data.cameras.new("Cam_01_Panorama")
    c1_data.lens = 24
    c1_obj = bpy.data.objects.new("Cam_01_Panorama", c1_data)
    c1_obj.location = (8.5, 34.0, 14.5)
    point_camera_at(c1_obj, (-8.0, 2.0, 3.5))
    bpy.context.scene.collection.objects.link(c1_obj)
    cameras['01_neighborhood_district_panorama'] = c1_obj
    
    # 02. House_A Balcony & Carport
    c2_data = bpy.data.cameras.new("Cam_02_HouseA")
    c2_data.lens = 32
    c2_obj = bpy.data.objects.new("Cam_02_HouseA", c2_data)
    c2_obj.location = (-4.2, -6.5, 4.2)
    point_camera_at(c2_obj, (-10.5, -5.5, 4.4))
    bpy.context.scene.collection.objects.link(c2_obj)
    cameras['02_house_a_balcony_carport'] = c2_obj
    
    # 03. House_B 24H Convenience Store & Vending
    c3_data = bpy.data.cameras.new("Cam_03_HouseB")
    c3_data.lens = 30
    c3_obj = bpy.data.objects.new("Cam_03_HouseB", c3_data)
    c3_obj.location = (-2.5, 20.5, 2.2)
    point_camera_at(c3_obj, (-9.5, 20.0, 2.5))
    bpy.context.scene.collection.objects.link(c3_obj)
    cameras['03_house_b_convenience_store_vending'] = c3_obj
    
    # 04. House_C Slope & Tactical Wall Bounce Alleyway
    c4_data = bpy.data.cameras.new("Cam_04_Alleyway")
    c4_data.lens = 35
    c4_obj = bpy.data.objects.new("Cam_04_Alleyway", c4_data)
    c4_obj.location = (-3.5, 1.75, 2.6)
    point_camera_at(c4_obj, (-13.0, 1.75, 2.8))
    bpy.context.scene.collection.objects.link(c4_obj)
    cameras['04_house_c_slope_alley_wall_bounce'] = c4_obj
    
    # 05. Street Props Kit Closeup
    c5_data = bpy.data.cameras.new("Cam_05_Props")
    c5_data.lens = 45
    c5_obj = bpy.data.objects.new("Cam_05_Props", c5_data)
    c5_obj.location = (-1.5, 14.2, 1.35)
    point_camera_at(c5_obj, (-4.0, 14.5, 0.75))
    bpy.context.scene.collection.objects.link(c5_obj)
    cameras['05_street_props_kit_closeup'] = c5_obj
    
    return cameras

def configure_render_engine(scene):
    bpy.ops.preferences.addon_enable(module='cycles')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    cprefs = bpy.context.preferences.addons['cycles'].preferences
    cprefs.get_devices()
    for t in ['OPTIX', 'CUDA']:
        if any(d.type == t for d in cprefs.devices):
            cprefs.compute_device_type = t
            break
    for d in cprefs.devices:
        if d.type in ['OPTIX', 'CUDA']:
            d.use = True
            
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    
    scene.view_settings.view_transform = 'AgX' if 'AgX' in [c.name for c in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = -0.35

# -------------------------------------------------------------
# 8. MAIN EXECUTION PIPELINE
# -------------------------------------------------------------
def main():
    print("=========================================================")
    print("Phase 2: Building Modular Neighborhood District in Blender 5.2")
    print("=========================================================")
    reset_scene()
    
    mats = {
        'wall_plaster': create_pbr_material("M_WallPlaster", "wall_plaster", base_color_fallback=(0.80, 0.79, 0.76, 1.0), roughness_val=0.82, uv_scale=(4.0, 4.0), normal_strength=1.8),
        'asphalt_road': create_pbr_material("M_AsphaltRoad", "asphalt_road", base_color_fallback=(0.16, 0.16, 0.17, 1.0), roughness_val=0.88, uv_scale=(1.0, 4.0), normal_strength=2.2),
        'sidewalk_tiles': create_pbr_material("M_SidewalkTiles", "sidewalk_tiles", base_color_fallback=(0.65, 0.66, 0.68, 1.0), roughness_val=0.68, uv_scale=(3.0, 6.0), normal_strength=1.6),
        'tactile_paving': create_pbr_material("M_TactilePaving", "tactile_paving", base_color_fallback=(0.94, 0.72, 0.05, 1.0), roughness_val=0.52, uv_scale=(1.0, 12.0), normal_strength=2.2),
        'concrete_curb': create_pbr_material("M_ConcreteCurb", "concrete_curb", base_color_fallback=(0.58, 0.59, 0.60, 1.0), roughness_val=0.72, uv_scale=(1.0, 6.0), normal_strength=1.3),
        'metal_manhole': create_pbr_material("M_MetalManhole", "metal_manhole", base_color_fallback=(0.16, 0.17, 0.18, 1.0), roughness_val=0.45, metallic_val=0.85, uv_scale=(1.0, 1.0), normal_strength=2.4),
        'props_ac_meter': create_pbr_material("M_PropsACMeter", "props_ac_meter", base_color_fallback=(0.86, 0.87, 0.88, 1.0), roughness_val=0.42, uv_scale=(1.0, 1.0), normal_strength=1.5),
        'utility_pole': create_pbr_material("M_UtilityPole", "utility_pole", base_color_fallback=(0.61, 0.62, 0.63, 1.0), roughness_val=0.78, uv_scale=(1.0, 4.0), normal_strength=1.3),
        'transformer': create_transformer_material("M_Transformer"),
        'glass': create_glass_material("M_Glass"),
        'aluminum_dark': create_custom_colored_material("M_Aluminum_Dark", (0.12, 0.13, 0.14, 1.0), roughness=0.32, metallic=0.88),
        'aluminum_silver': create_custom_colored_material("M_Aluminum_Silver", (0.65, 0.68, 0.70, 1.0), roughness=0.32, metallic=0.88),
        'cable_rubber': create_custom_colored_material("M_CableRubber", (0.08, 0.08, 0.09, 1.0), roughness=0.65)
    }
    
    print("Building Asset 1: Sloped Terrain & Roadways...")
    build_terrain_and_roads(mats)
    
    print("Building Asset 2: House_A Standard Residence with Balcony & Carport...")
    build_house_a(mats)
    
    print("Building Asset 3: House_C Sloped Residence & Tactical Alleyway...")
    build_house_c_and_alleyway(mats)
    
    print("Building Asset 4: House_B 24H Convenience Store & Vending Machines...")
    build_house_b_convenience_store(mats)
    
    print("Building Asset 5: Street Props Kit (Cones, Bins, Mirrors, Hydrants)...")
    build_street_props_kit(mats)
    
    setup_lighting()
    cameras = setup_inspection_cameras()
    
    scene = bpy.context.scene
    configure_render_engine(scene)
    
    blend_paths = [
        os.path.abspath("art/models/neighborhood/modern_japan_neighborhood.blend"),
        os.path.abspath("asternova/art/models/neighborhood/modern_japan_neighborhood.blend")
    ]
    for bp in blend_paths:
        ensure_dir(os.path.dirname(bp))
        bpy.ops.wm.save_as_mainfile(filepath=bp)
        print(f"Saved .blend project to: {bp}")
        
    glb_export_targets = [
        os.path.abspath("client-godot-v2/models/environment/modern_japan_neighborhood.glb"),
        os.path.abspath("asternova/client-godot-v2/models/environment/modern_japan_neighborhood.glb"),
        os.path.abspath("render-lab/models/environment/modern_japan_neighborhood.glb"),
        os.path.abspath("asternova/render-lab/models/environment/modern_japan_neighborhood.glb")
    ]
    for gp in glb_export_targets:
        ensure_dir(os.path.dirname(gp))
        try:
            bpy.ops.export_scene.gltf(filepath=gp, export_format='GLB', export_materials='EXPORT', export_cameras=False)
            print(f"Exported neighborhood GLB asset to: {gp}")
        except Exception as e:
            print(f"GLB export note for {gp}: {e}")
            
    screenshot_dirs = [
        os.path.abspath("asternova/render-lab/screenshots/modular_kit"),
        os.path.abspath("render-lab/screenshots/modular_kit")
    ]
    for d in screenshot_dirs:
        ensure_dir(d)
        
    print("\n--- Starting Phase 2 Cycles 2K Rendering (5 Inspection Views) ---")
    for shot_name, cam_obj in cameras.items():
        print(f"Rendering View: {shot_name} (2560x1440 2K)...")
        scene.camera = cam_obj
        out_file1 = os.path.join(screenshot_dirs[0], f"{shot_name}.png")
        scene.render.filepath = out_file1
        bpy.ops.render.render(write_still=True)
        print(f"Saved: {out_file1}")
        
        out_file2 = os.path.join(screenshot_dirs[1], f"{shot_name}.png")
        import shutil
        shutil.copy2(out_file1, out_file2)
        print(f"Mirrored: {out_file2}")
        
    print("\n=========================================================")
    print("Phase 2 Modular Kit Expansion Completed Successfully!")
    print("=========================================================")

if __name__ == "__main__":
    main()
