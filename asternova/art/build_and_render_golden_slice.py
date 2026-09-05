import bpy
import bmesh
import math
import os
import sys

# Ensure clean state
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

# Texture helper
def find_texture(tex_name):
    paths = [
        os.path.abspath(f"asternova/art/textures/golden_slice/{tex_name}"),
        os.path.abspath(f"art/textures/golden_slice/{tex_name}")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    print(f"WARNING: Texture not found: {tex_name}")
    return None

def create_pbr_material(name, tex_base, base_color_fallback=(0.8, 0.8, 0.8, 1.0), roughness_val=0.7, metallic_val=0.0, uv_scale=(1.0, 1.0), normal_strength=1.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = base_color_fallback
    bsdf.inputs['Roughness'].default_value = roughness_val
    bsdf.inputs['Metallic'].default_value = metallic_val
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Load textures if available
    albedo_path = find_texture(f"{tex_base}_albedo.png")
    normal_path = find_texture(f"{tex_base}_normal.png")
    roughness_path = find_texture(f"{tex_base}_roughness.png")
    ao_path = find_texture(f"{tex_base}_ao.png")
    
    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)
    
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.location = (-600, 0)
    mapping.inputs['Scale'].default_value = (uv_scale[0], uv_scale[1], 1.0)
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    
    # Albedo + AO
    if albedo_path:
        tex_alb = nodes.new(type='ShaderNodeTexImage')
        tex_alb.image = bpy.data.images.load(albedo_path)
        tex_alb.location = (-350, 200)
        links.new(mapping.outputs['Vector'], tex_alb.inputs['Vector'])
        
        if ao_path:
            tex_ao = nodes.new(type='ShaderNodeTexImage')
            tex_ao.image = bpy.data.images.load(ao_path)
            tex_ao.image.colorspace_settings.name = 'Non-Color'
            tex_ao.location = (-350, -50)
            links.new(mapping.outputs['Vector'], tex_ao.inputs['Vector'])
            
            mix_ao = nodes.new(type='ShaderNodeMix')
            mix_ao.data_type = 'RGBA'
            mix_ao.blend_type = 'MULTIPLY'
            mix_ao.inputs['Factor'].default_value = 0.8
            mix_ao.location = (-50, 150)
            links.new(tex_alb.outputs['Color'], mix_ao.inputs[6])
            links.new(tex_ao.outputs['Color'], mix_ao.inputs[7])
            links.new(mix_ao.outputs[2], bsdf.inputs['Base Color'])
        else:
            links.new(tex_alb.outputs['Color'], bsdf.inputs['Base Color'])
            
    # Roughness
    if roughness_path:
        tex_rough = nodes.new(type='ShaderNodeTexImage')
        tex_rough.image = bpy.data.images.load(roughness_path)
        tex_rough.image.colorspace_settings.name = 'Non-Color'
        tex_rough.location = (-350, -300)
        links.new(mapping.outputs['Vector'], tex_rough.inputs['Vector'])
        links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])
        
    # Normal
    if normal_path:
        tex_nor = nodes.new(type='ShaderNodeTexImage')
        tex_nor.image = bpy.data.images.load(normal_path)
        tex_nor.image.colorspace_settings.name = 'Non-Color'
        tex_nor.location = (-350, -550)
        links.new(mapping.outputs['Vector'], tex_nor.inputs['Vector'])
        
        nor_map = nodes.new(type='ShaderNodeNormalMap')
        nor_map.inputs['Strength'].default_value = normal_strength
        nor_map.location = (-50, -450)
        links.new(tex_nor.outputs['Color'], nor_map.inputs['Color'])
        links.new(nor_map.outputs['Normal'], bsdf.inputs['Normal'])
        
    return mat

def create_glass_material(name="M_Glass"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.92, 0.96, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    bsdf.inputs['IOR'].default_value = 1.52
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_interior_material(name="M_InteriorRoom"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.05, 0.06, 0.07, 1.0) # Dim interior room cavity
    bsdf.inputs['Roughness'].default_value = 0.90
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_aluminum_material(name="M_Aluminum", dark=True):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    if dark:
        bsdf.inputs['Base Color'].default_value = (0.12, 0.13, 0.14, 1.0) # Anodized charcoal
    else:
        bsdf.inputs['Base Color'].default_value = (0.65, 0.68, 0.70, 1.0) # Silver brushed
    bsdf.inputs['Metallic'].default_value = 0.88
    bsdf.inputs['Roughness'].default_value = 0.32
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_insulator_porcelain_material(name="M_Porcelain"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.28, 0.14, 0.08, 1.0) # Classic glazed brown
    bsdf.inputs['Roughness'].default_value = 0.12 # Glossy ceramic glaze
    bsdf.inputs['Specular IOR Level'].default_value = 0.7
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_cable_material(name="M_CableRubber"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.08, 0.08, 0.09, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.65
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_transformer_material(name="M_Transformer"):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.32, 0.34, 0.35, 1.0) # Weather-beaten matte gray iron paint
    bsdf.inputs['Metallic'].default_value = 0.70
    bsdf.inputs['Roughness'].default_value = 0.65 # Industrial weathered matte
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

# Geometry construction functions
def apply_bevel(obj, width=0.03, segments=3):
    bev = obj.modifiers.new(name="Bevel", type='BEVEL')
    bev.width = width
    bev.segments = segments
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(35)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def build_catenary_curve(name, p_start, p_end, sag=0.35, segments=32, radius=0.012, material=None):
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
        # Linear interpolation in X and Y
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        # Linear base in Z plus parabolic catenary droop
        # sag is maximum at t = 0.5
        droop = 4.0 * sag * t * (1.0 - t)
        z = z1 + t * (z2 - z1) - droop
        polyline.points[i].co = (x, y, z, 1.0)
        
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj

# -------------------------------------------------------------
# 1. GROUND, CURB, SIDEWALK, TACTILE, MANHOLE, DRAIN
# -------------------------------------------------------------
def build_ground_patch(mats):
    col = bpy.data.collections.new("01_Ground_Sidewalk")
    bpy.context.scene.collection.children.link(col)
    
    # 1. Asphalt Roadway: X in [-4.5, 0.5], Y in [-7.5, 7.5], Z = 0.0
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-2.0, 0.0, 0.0))
    road = bpy.context.active_object
    road.name = "Asphalt_Roadway"
    road.scale = (5.0, 15.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    road.data.materials.append(mats['asphalt_road'])
    # Explicit planar UV mapping: align textures perfectly along road length
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(road.data)
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            u = (vert.co.x + 4.5) / 5.0
            v = (vert.co.y + 7.5) / 15.0
            loop[uv_layer].uv = (u, v)
    bmesh.update_edit_mesh(road.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    col.objects.link(road)
    bpy.context.collection.objects.unlink(road)
    
    # 2. Concrete Curb: X in [0.5, 0.7], Y in [-7.5, 7.5], Z from 0.0 to 0.15
    # Beveled edge facing road
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.6, 0.0, 0.075))
    curb = bpy.context.active_object
    curb.name = "Concrete_Curb"
    curb.scale = (0.2, 15.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    curb.data.materials.append(mats['concrete_curb'])
    apply_bevel(curb, width=0.02, segments=3)
    col.objects.link(curb)
    bpy.context.collection.objects.unlink(curb)
    
    # 3. Sidewalk Stone Pavers: X in [0.7, 3.5], Y in [-7.5, 7.5], Z = 0.15
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.1, 0.0, 0.075))
    sidewalk = bpy.context.active_object
    sidewalk.name = "Sidewalk_Pavers"
    sidewalk.scale = (2.8, 15.0, 0.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sidewalk.data.materials.append(mats['sidewalk_tiles'])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    col.objects.link(sidewalk)
    bpy.context.collection.objects.unlink(sidewalk)
    
    # 4. Yellow Tactile Paving Strip: X in [1.0, 1.6], Y in [-7.5, 7.5], Z = 0.152
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(1.3, 0.0, 0.152))
    tactile = bpy.context.active_object
    tactile.name = "Tactile_Paving_Strip"
    tactile.scale = (0.6, 15.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tactile.data.materials.append(mats['tactile_paving'])
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    col.objects.link(tactile)
    bpy.context.collection.objects.unlink(tactile)
    
    # Add actual 3D blister dots and guide ribs along the tactile path for physical closeups!
    # A 3m detailed section near Y = 0.5 where camera 4 zooms in!
    dot_col = bpy.data.collections.new("Tactile_3D_Domes")
    col.children.link(dot_col)
    dome_mesh = None
    for y_idx in range(16):
        y_pos = -0.5 + y_idx * 0.12
        for x_idx in range(4):
            x_pos = 1.12 + x_idx * 0.12
            if dome_mesh is None:
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=(x_pos, y_pos, 0.156))
                dome = bpy.context.active_object
                dome.scale = (1.0, 1.0, 0.35)
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                dome.data.materials.append(mats['tactile_paving'])
                bpy.ops.object.shade_smooth()
                dome_mesh = dome.data
                dot_col.objects.link(dome)
                bpy.context.collection.objects.unlink(dome)
            else:
                d_obj = bpy.data.objects.new(f"BlisterDot_{y_idx}_{x_idx}", dome_mesh)
                d_obj.location = (x_pos, y_pos, 0.156)
                dot_col.objects.link(d_obj)
                
    # 5. Circular Cast Iron Manhole Cover with 1cm physical sunken recess (沉降凹槽)
    # Concrete / asphalt recessed depression ring collar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.022, location=(-1.1, 0.5, -0.007))
    manhole_depress = bpy.context.active_object
    manhole_depress.name = "Manhole_Depression_Collar"
    manhole_depress.data.materials.append(mats['concrete_curb'])
    apply_bevel(manhole_depress, width=0.012, segments=2)
    col.objects.link(manhole_depress)
    bpy.context.collection.objects.unlink(manhole_depress)
    
    # Cast iron outer frame ring (sunken by 1cm)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.020, location=(-1.1, 0.5, -0.005))
    manhole_rim = bpy.context.active_object
    manhole_rim.name = "Manhole_Outer_Rim"
    manhole_rim.data.materials.append(mats['metal_manhole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(manhole_rim)
    bpy.context.collection.objects.unlink(manhole_rim)
    
    # Cast iron manhole cover lid with recessed annular slot
    bpy.ops.mesh.primitive_cylinder_add(radius=0.34, depth=0.022, location=(-1.1, 0.5, -0.004))
    manhole_lid = bpy.context.active_object
    manhole_lid.name = "Manhole_Cover_Lid"
    manhole_lid.data.materials.append(mats['metal_manhole'])
    apply_bevel(manhole_lid, width=0.008, segments=2)
    col.objects.link(manhole_lid)
    bpy.context.collection.objects.unlink(manhole_lid)
    
    # 6. Slotted Cast Iron Roadside Drain Grate with 1.5cm Gutter Depression & Dark Sewer Void Pit (暗沟透空感)
    # Deep sewer cavity pit underneath the grate
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, -0.1, -0.08))
    sewer_pit = bpy.context.active_object
    sewer_pit.name = "Drain_Sewer_Void_Pit"
    sewer_pit.scale = (0.26, 0.82, 0.16)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sewer_pit.data.materials.append(mats['interior']) # Pitch black cavity
    col.objects.link(sewer_pit)
    bpy.context.collection.objects.unlink(sewer_pit)
    
    # Gutter depressed concrete basin collar (1.5cm below curb road edge)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, -0.1, -0.008))
    grate_recess = bpy.context.active_object
    grate_recess.name = "Drain_Gutter_Recess"
    grate_recess.scale = (0.32, 0.92, 0.02)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    grate_recess.data.materials.append(mats['concrete_curb'])
    apply_bevel(grate_recess, width=0.01, segments=2)
    col.objects.link(grate_recess)
    bpy.context.collection.objects.unlink(grate_recess)
    
    # Outer cast iron frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, -0.1, -0.004))
    grate_frame = bpy.context.active_object
    grate_frame.name = "Drain_Grate_Frame"
    grate_frame.scale = (0.28, 0.85, 0.016)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    grate_frame.data.materials.append(mats['metal_manhole'])
    apply_bevel(grate_frame, width=0.008, segments=2)
    col.objects.link(grate_frame)
    bpy.context.collection.objects.unlink(grate_frame)
    
    # Drain slots (cast iron ribs) with open air gaps looking through into sewer void
    for s in range(8):
        sy = -0.42 + s * 0.105
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, sy, 0.002))
        bar = bpy.context.active_object
        bar.scale = (0.22, 0.024, 0.012)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bar.data.materials.append(mats['metal_manhole'])
        col.objects.link(bar)
        bpy.context.collection.objects.unlink(bar)
        
    return col

# -------------------------------------------------------------
# 2. MODERN 2F JAPANESE HOUSE
# -------------------------------------------------------------
def build_japanese_house(mats):
    col = bpy.data.collections.new("02_House_2F")
    bpy.context.scene.collection.children.link(col)
    
    # House positioning: front wall at X = 3.2, back at X = 10.4 (depth 7.2m)
    # Width along Y: from -3.6 to +3.6 (width 7.2m)
    # Ground floor level: Z = 0.15 to 3.35 (height 3.2m)
    # Second floor level: Z = 3.35 to 6.35 (height 3.0m)
    
    # 1. Concrete Foundation Plinth (Baseboard / 基础抬高)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.8, 0.0, 0.30))
    plinth = bpy.context.active_object
    plinth.name = "House_Foundation_Plinth"
    plinth.scale = (7.25, 7.25, 0.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plinth.data.materials.append(mats['concrete_curb'])
    apply_bevel(plinth, width=0.025, segments=3)
    col.objects.link(plinth)
    bpy.context.collection.objects.unlink(plinth)
    
    # 2. Main Building Volumes (1F & 2F)
    def carve_opening(wall_obj, center_x, center_y, center_z, width, height, depth=0.60):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(center_x, center_y, center_z))
        cutter = bpy.context.active_object
        cutter.scale = (depth, width, height)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mod = wall_obj.modifiers.new(name="Cutout", type='BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cutter
        mod.solver = 'EXACT'
        bpy.context.view_layer.objects.active = wall_obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)

    # 1F Body:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.8, 0.0, 1.85))
    bldg_1f = bpy.context.active_object
    bldg_1f.name = "House_1F_Main_Wall"
    bldg_1f.scale = (7.2, 7.2, 2.8)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_1f.data.materials.append(mats['wall_plaster'])
    
    # Carve physical openings in 1F wall:
    # A. Entrance door opening at Y = -1.80, Z = 1.20
    carve_opening(bldg_1f, center_x=3.20, center_y=-1.80, center_z=1.20, width=1.15, height=2.25, depth=0.60)
    # B. Main 1F Window opening at Y = 1.30, Z = 1.65 (2.2m x 1.4m)
    carve_opening(bldg_1f, center_x=3.20, center_y=1.30, center_z=1.65, width=2.26, height=1.46, depth=0.60)
    apply_bevel(bldg_1f, width=0.03, segments=2)
    col.objects.link(bldg_1f)
    bpy.context.collection.objects.unlink(bldg_1f)
    
    # Mid-floor decorative horizontal band / belt course (铝合金/木色腰线)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.78, 0.0, 3.28))
    belt = bpy.context.active_object
    belt.name = "House_Mid_Belt_Course"
    belt.scale = (7.26, 7.26, 0.12)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    belt.data.materials.append(mats['aluminum_dark'])
    apply_bevel(belt, width=0.015, segments=2)
    col.objects.link(belt)
    bpy.context.collection.objects.unlink(belt)
    
    # 2F Body (with a setback balcony on front left):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.9, 0.0, 4.80))
    bldg_2f = bpy.context.active_object
    bldg_2f.name = "House_2F_Main_Wall"
    bldg_2f.scale = (7.0, 7.2, 2.9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bldg_2f.data.materials.append(mats['wall_plaster'])
    
    # Carve physical openings in 2F wall:
    carve_opening(bldg_2f, center_x=3.40, center_y=1.30, center_z=4.75, width=1.86, height=1.36, depth=0.60)
    carve_opening(bldg_2f, center_x=3.40, center_y=-1.80, center_z=4.75, width=1.36, height=1.16, depth=0.60)
    apply_bevel(bldg_2f, width=0.03, segments=2)
    col.objects.link(bldg_2f)
    bpy.context.collection.objects.unlink(bldg_2f)
    
    # 3. Roof Eaves & Parapet (屋顶挑檐与排水天沟)
    # Roof slab overhangs 0.45m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(6.75, 0.0, 6.35))
    roof = bpy.context.active_object
    roof.name = "House_Roof_Fascia"
    roof.scale = (7.7, 7.7, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    roof.data.materials.append(mats['aluminum_dark'])
    apply_bevel(roof, width=0.03, segments=3)
    col.objects.link(roof)
    bpy.context.collection.objects.unlink(roof)
    
    # Roof Gutter (屋檐排水槽): continuous U-channel along front edge (X = 2.86, Z = 6.26)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.86, 0.0, 6.26))
    gutter = bpy.context.active_object
    gutter.name = "Roof_Eaves_Gutter"
    gutter.scale = (0.12, 7.75, 0.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    gutter.data.materials.append(mats['aluminum_dark'])
    apply_bevel(gutter, width=0.015, segments=2)
    col.objects.link(gutter)
    bpy.context.collection.objects.unlink(gutter)
    
    # Rainwater Collector Box / Funnel (雨水斗) at corner (X = 2.92, Y = 3.65, Z = 6.20)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.94, 3.65, 6.20))
    funnel = bpy.context.active_object
    funnel.name = "Downspout_Collector_Funnel"
    funnel.scale = (0.18, 0.22, 0.24)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    funnel.data.materials.append(mats['aluminum_dark'])
    apply_bevel(funnel, width=0.015, segments=2)
    col.objects.link(funnel)
    bpy.context.collection.objects.unlink(funnel)
    
    # Downspout (垂直外露落水管): 7.5cm diameter running vertically straight to ground
    bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=5.95, location=(3.02, 3.65, 3.15))
    downspout = bpy.context.active_object
    downspout.name = "Downspout_Vertical_Pipe"
    downspout.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(downspout)
    bpy.context.collection.objects.unlink(downspout)
    
    # Downspout Wall Mounting Straps (金属抱箍) at 4 heights
    for h in [0.8, 2.2, 3.8, 5.4]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.10, 3.65, h))
        strap = bpy.context.active_object
        strap.scale = (0.16, 0.11, 0.035)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        strap.data.materials.append(mats['aluminum_silver'])
        apply_bevel(strap, width=0.005, segments=2)
        col.objects.link(strap)
        bpy.context.collection.objects.unlink(strap)
        
    # Downspout bottom curved discharge elbow (喇叭口排水弯头) at ground level
    bpy.ops.mesh.primitive_cylinder_add(radius=0.042, depth=0.25, location=(2.96, 3.65, 0.22))
    elbow = bpy.context.active_object
    elbow.rotation_euler = (0.0, math.radians(40), 0.0)
    elbow.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(elbow)
    bpy.context.collection.objects.unlink(elbow)
    
    # -------------------------------------------------------------
    # 4. PHYSICAL INSET WINDOWS (严格 18cm 物理内嵌深度 + 双滑轨 + 双层玻璃 + 金属滴水板)
    # -------------------------------------------------------------
    # Helper to build an authentic Japanese recessed window assembly with framed sashes
    def build_window_sash(sash_name, sash_x, sash_y, sash_z, sash_w, sash_h, mats, w_col):
        rail_thick = 0.045
        depth = 0.035
        # 4 perimeter aluminum rails
        # Top
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sash_x, sash_y, sash_z + sash_h * 0.5 - rail_thick * 0.5))
        top = bpy.context.active_object
        top.name = f"{sash_name}_TopRail"
        top.scale = (depth, sash_w, rail_thick)
        bpy.ops.object.transform_apply(scale=True)
        top.data.materials.append(mats['aluminum_dark'])
        apply_bevel(top, width=0.005, segments=2)
        w_col.objects.link(top)
        bpy.context.collection.objects.unlink(top)
        
        # Bottom
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sash_x, sash_y, sash_z - sash_h * 0.5 + rail_thick * 0.5))
        bot = bpy.context.active_object
        bot.name = f"{sash_name}_BotRail"
        bot.scale = (depth, sash_w, rail_thick)
        bpy.ops.object.transform_apply(scale=True)
        bot.data.materials.append(mats['aluminum_dark'])
        apply_bevel(bot, width=0.005, segments=2)
        w_col.objects.link(bot)
        bpy.context.collection.objects.unlink(bot)
        
        # Left stile
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sash_x, sash_y - sash_w * 0.5 + rail_thick * 0.5, sash_z))
        left = bpy.context.active_object
        left.name = f"{sash_name}_LeftStile"
        left.scale = (depth, rail_thick, sash_h - rail_thick * 2.0)
        bpy.ops.object.transform_apply(scale=True)
        left.data.materials.append(mats['aluminum_dark'])
        apply_bevel(left, width=0.005, segments=2)
        w_col.objects.link(left)
        bpy.context.collection.objects.unlink(left)
        
        # Right stile
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sash_x, sash_y + sash_w * 0.5 - rail_thick * 0.5, sash_z))
        right = bpy.context.active_object
        right.name = f"{sash_name}_RightStile"
        right.scale = (depth, rail_thick, sash_h - rail_thick * 2.0)
        bpy.ops.object.transform_apply(scale=True)
        right.data.materials.append(mats['aluminum_dark'])
        apply_bevel(right, width=0.005, segments=2)
        w_col.objects.link(right)
        bpy.context.collection.objects.unlink(right)
        
        # Central double glazing glass pane
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sash_x, sash_y, sash_z))
        glass = bpy.context.active_object
        glass.name = f"{sash_name}_Glass"
        glass.scale = (0.012, sash_w - rail_thick * 1.6, sash_h - rail_thick * 1.6)
        bpy.ops.object.transform_apply(scale=True)
        glass.data.materials.append(mats['glass'])
        w_col.objects.link(glass)
        bpy.context.collection.objects.unlink(glass)

    def build_recessed_window(name, center_x, center_y, center_z, width, height, recess_depth=0.18):
        w_col = bpy.data.collections.new(name)
        col.children.link(w_col)
        
        # A. Extruded Aluminum Outer Perimeter Window Frame (at inner recess depth)
        inner_x = center_x + recess_depth
        frame_thick = 0.05
        # Top frame
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z + height * 0.5 - frame_thick * 0.5))
        f_top = bpy.context.active_object
        f_top.scale = (0.08, width, frame_thick)
        bpy.ops.object.transform_apply(scale=True)
        f_top.data.materials.append(mats['aluminum_dark'])
        apply_bevel(f_top, width=0.005, segments=2)
        w_col.objects.link(f_top)
        bpy.context.collection.objects.unlink(f_top)
        
        # Bottom frame (sill track)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, center_z - height * 0.5 + frame_thick * 0.5))
        f_bot = bpy.context.active_object
        f_bot.scale = (0.08, width, frame_thick)
        bpy.ops.object.transform_apply(scale=True)
        f_bot.data.materials.append(mats['aluminum_dark'])
        apply_bevel(f_bot, width=0.005, segments=2)
        w_col.objects.link(f_bot)
        bpy.context.collection.objects.unlink(f_bot)
        
        # Left jamb
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y - width * 0.5 + frame_thick * 0.5, center_z))
        f_left = bpy.context.active_object
        f_left.scale = (0.08, frame_thick, height - frame_thick * 2.0)
        bpy.ops.object.transform_apply(scale=True)
        f_left.data.materials.append(mats['aluminum_dark'])
        apply_bevel(f_left, width=0.005, segments=2)
        w_col.objects.link(f_left)
        bpy.context.collection.objects.unlink(f_left)
        
        # Right jamb
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y + width * 0.5 - frame_thick * 0.5, center_z))
        f_right = bpy.context.active_object
        f_right.scale = (0.08, frame_thick, height - frame_thick * 2.0)
        bpy.ops.object.transform_apply(scale=True)
        f_right.data.materials.append(mats['aluminum_dark'])
        apply_bevel(f_right, width=0.005, segments=2)
        w_col.objects.link(f_right)
        bpy.context.collection.objects.unlink(f_right)
        
        # Dual sliding tracks (extruded silver aluminum center guide rails top & bottom)
        for tz in [center_z - height * 0.5 + 0.05, center_z + height * 0.5 - 0.05]:
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x, center_y, tz))
            track = bpy.context.active_object
            track.scale = (0.06, width - frame_thick * 2.0, 0.015)
            bpy.ops.object.transform_apply(scale=True)
            track.data.materials.append(mats['aluminum_silver'])
            w_col.objects.link(track)
            bpy.context.collection.objects.unlink(track)
            
        # B. Two Overlapping Framed Sliding Sashes (内外双扇)
        sash_w = (width - frame_thick * 2.0) * 0.53
        sash_h = height - frame_thick * 2.0 - 0.02
        
        # Sash 1 (Left, forward outer track at inner_x - 0.018)
        sash1_y = center_y - width * 0.23
        build_window_sash(f"{name}_Sash1", inner_x - 0.018, sash1_y, center_z, sash_w, sash_h, mats, w_col)
        
        # Sash 2 (Right, inner track at inner_x + 0.018)
        sash2_y = center_y + width * 0.23
        build_window_sash(f"{name}_Sash2", inner_x + 0.018, sash2_y, center_z, sash_w, sash_h, mats, w_col)
        
        # C. Window Sill Extruded Sheet Metal Drip Edge (窗台冲压金属滴水板)
        # Projects 3cm forward, downward drip hem lip to shed rainwater
        sill_x = center_x - 0.02
        sill_z = center_z - height * 0.5 - 0.015
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sill_x + recess_depth * 0.5, center_y, sill_z))
        sill = bpy.context.active_object
        sill.name = f"{name}_Metal_Sill_Drip"
        sill.scale = (recess_depth + 0.08, width + 0.10, 0.025)
        sill.rotation_euler = (0, math.radians(3.5), 0) # 3.5 deg slope drainage
        bpy.ops.object.transform_apply(scale=True)
        sill.data.materials.append(mats['aluminum_dark'])
        apply_bevel(sill, width=0.005, segments=2)
        w_col.objects.link(sill)
        bpy.context.collection.objects.unlink(sill)
        
        # D. Interior Room Cavity (深色室内腔体与软质浅米色窗帘)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(inner_x + 0.35, center_y, center_z))
        room = bpy.context.active_object
        room.name = f"{name}_RoomCavity"
        room.scale = (0.60, width + 0.20, height + 0.20)
        bpy.ops.object.transform_apply(scale=True)
        room.data.materials.append(mats['interior'])
        w_col.objects.link(room)
        bpy.context.collection.objects.unlink(room)
        
        # Soft warm cream curtain drape along one side
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(inner_x + 0.08, center_y - width * 0.25, center_z))
        curtain = bpy.context.active_object
        curtain.rotation_euler = (0, math.radians(90), 0)
        curtain.scale = (sash_h * 0.95, sash_w * 0.85, 1.0)
        bpy.ops.object.transform_apply(scale=True)
        curtain.data.materials.append(mats['wall_plaster'])
        w_col.objects.link(curtain)
        bpy.context.collection.objects.unlink(curtain)
        
    # Build the 1F Main Window (Large 2.2m x 1.4m sliding window at Y = 1.3, Z = 1.65)
    build_recessed_window("Window_1F_Main", center_x=3.18, center_y=1.30, center_z=1.65, width=2.20, height=1.40, recess_depth=0.18)
    
    # Build 2F Windows (1.8m x 1.3m and 1.2m x 1.1m)
    build_recessed_window("Window_2F_Master", center_x=3.38, center_y=1.30, center_z=4.75, width=1.80, height=1.30, recess_depth=0.18)
    build_recessed_window("Window_2F_Bed2", center_x=3.38, center_y=-1.80, center_z=4.75, width=1.30, height=1.10, recess_depth=0.18)
    
    # -------------------------------------------------------------
    # 5. ENTRANCE SYSTEM (DOOR, CANTILEVER AWNING, SCONCE, METER BOX)
    # -------------------------------------------------------------
    # A. Recessed Entrance Door Alcove (20cm recess at Y = -1.8, Z = 1.2)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.30, -1.80, 1.20))
    door_alcove = bpy.context.active_object
    door_alcove.name = "Door_Alcove"
    door_alcove.scale = (0.24, 1.30, 2.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    door_alcove.data.materials.append(mats['aluminum_dark'])
    col.objects.link(door_alcove)
    bpy.context.collection.objects.unlink(door_alcove)
    
    # Entrance Door leaf (Modern panel door)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.40, -1.80, 1.18))
    door = bpy.context.active_object
    door.name = "Entrance_Door"
    door.scale = (0.06, 1.05, 2.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    door.data.materials.append(mats['aluminum_dark'])
    apply_bevel(door, width=0.01, segments=2)
    col.objects.link(door)
    bpy.context.collection.objects.unlink(door)
    
    # Long brushed aluminum bar handle
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.75, location=(3.34, -1.35, 1.05))
    handle = bpy.context.active_object
    handle.name = "Door_Bar_Handle"
    handle.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(handle)
    bpy.context.collection.objects.unlink(handle)
    
    # B. Cantilever Entrance Awning / Canopy (入户悬挑雨棚) at Z = 2.45
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.55, -1.80, 2.45))
    canopy = bpy.context.active_object
    canopy.name = "Entrance_Awning_Canopy"
    canopy.scale = (1.35, 1.65, 0.04)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy.data.materials.append(mats['aluminum_dark'])
    apply_bevel(canopy, width=0.008, segments=2)
    col.objects.link(canopy)
    bpy.context.collection.objects.unlink(canopy)
    
    # Canopy tempered glass insert
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.55, -1.80, 2.48))
    canopy_glass = bpy.context.active_object
    canopy_glass.scale = (1.25, 1.55, 0.015)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    canopy_glass.data.materials.append(mats['glass'])
    col.objects.link(canopy_glass)
    bpy.context.collection.objects.unlink(canopy_glass)
    
    # C. Porch Waterproof Wall Sconce (入户壁灯) at Y = -0.95, Z = 2.15
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.18, location=(3.12, -0.95, 2.15))
    lamp = bpy.context.active_object
    lamp.name = "Porch_Sconce_Lamp"
    lamp.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    col.objects.link(lamp)
    bpy.context.collection.objects.unlink(lamp)
    
    # D. Utility Electric Meter Box (入户电表箱) at Y = -0.65, Z = 1.45
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.12, -0.65, 1.45))
    meter = bpy.context.active_object
    meter.name = "Electric_Meter_Box"
    meter.scale = (0.16, 0.28, 0.38)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    meter.data.materials.append(mats['props_ac_meter'])
    apply_bevel(meter, width=0.01, segments=2)
    col.objects.link(meter)
    bpy.context.collection.objects.unlink(meter)
    
    # Meter glass inspection viewport
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.03, -0.65, 1.50))
    m_glass = bpy.context.active_object
    m_glass.scale = (0.02, 0.18, 0.18)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m_glass.data.materials.append(mats['glass'])
    col.objects.link(m_glass)
    bpy.context.collection.objects.unlink(m_glass)
    
    # Conduit pipe running from meter into wall
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.45, location=(3.12, -0.65, 1.15))
    conduit = bpy.context.active_object
    conduit.data.materials.append(mats['aluminum_silver'])
    bpy.ops.object.shade_smooth()
    col.objects.link(conduit)
    bpy.context.collection.objects.unlink(conduit)
    
    # -------------------------------------------------------------
    # 6. HIGH-PRECISION AC OUTDOOR UNIT (空调室外机高精微细节)
    # -------------------------------------------------------------
    ac_col = bpy.data.collections.new("AC_Outdoor_Unit_Assembly")
    col.children.link(ac_col)
    
    # Position: near ground, corner of front wall (X = 2.95, Y = 2.70, Z = 0.44)
    # AC Main Chassis (82cm width x 32cm depth x 56cm height)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.95, 2.70, 0.44))
    ac_body = bpy.context.active_object
    ac_body.name = "AC_Main_Chassis"
    ac_body.scale = (0.32, 0.82, 0.56)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ac_body.data.materials.append(mats['props_ac_meter'])
    apply_bevel(ac_body, width=0.018, segments=3)
    ac_col.objects.link(ac_body)
    bpy.context.collection.objects.unlink(ac_body)
    
    # Rubber Mounting Feet (防震脚垫) x2
    for fy in [2.40, 3.00]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.95, fy, 0.18))
        foot = bpy.context.active_object
        foot.scale = (0.36, 0.12, 0.05)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        foot.data.materials.append(mats['cable_rubber'])
        apply_bevel(foot, width=0.008, segments=2)
        ac_col.objects.link(foot)
        bpy.context.collection.objects.unlink(foot)
        
    # Front Circular Fan Shroud (风扇导流圈) recessed in front panel
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.03, location=(2.78, 2.58, 0.44))
    fan_shroud = bpy.context.active_object
    fan_shroud.name = "AC_Fan_Shroud"
    fan_shroud.rotation_euler = (0, math.radians(90), 0)
    fan_shroud.data.materials.append(mats['aluminum_dark'])
    bpy.ops.object.shade_smooth()
    ac_col.objects.link(fan_shroud)
    bpy.context.collection.objects.unlink(fan_shroud)
    
    # Hint of 3 Axial Fan Blades inside
    for b_idx in range(3):
        rot = b_idx * (2.0 * math.pi / 3.0)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.80, 2.58 + 0.09 * math.cos(rot), 0.44 + 0.09 * math.sin(rot)))
        blade = bpy.context.active_object
        blade.name = f"AC_Fan_Blade_{b_idx}"
        blade.scale = (0.015, 0.06, 0.16)
        blade.rotation_euler = (rot, math.radians(15), 0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        blade.data.materials.append(mats['aluminum_dark'])
        ac_col.objects.link(blade)
        bpy.context.collection.objects.unlink(blade)
        
    # Fine Horizontal Louver Slats (百叶散热栅格) across fan face
    for l_idx in range(14):
        lz = 0.26 + l_idx * 0.026
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.77, 2.58, lz))
        slat = bpy.context.active_object
        slat.scale = (0.012, 0.42, 0.012)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        slat.data.materials.append(mats['props_ac_meter'])
        ac_col.objects.link(slat)
        bpy.context.collection.objects.unlink(slat)
        
    # Side Valve Protection Cover (侧面铜管阀门罩)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.98, 3.12, 0.38))
    valve_cov = bpy.context.active_object
    valve_cov.name = "AC_Valve_Cover"
    valve_cov.scale = (0.16, 0.06, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    valve_cov.data.materials.append(mats['props_ac_meter'])
    apply_bevel(valve_cov, width=0.008, segments=2)
    ac_col.objects.link(valve_cov)
    bpy.context.collection.objects.unlink(valve_cov)
    
    # Insulated Copper Pipes (包裹米白色保温棉的弯曲铜管)
    # Bends gracefully from valve cover up along the wall into wall penetration cap
    pipe_curve = bpy.data.curves.new('AC_Insulated_Pipes', type='CURVE')
    pipe_curve.dimensions = '3D'
    pipe_curve.fill_mode = 'FULL'
    pipe_curve.bevel_depth = 0.026 # Insulated foam diameter ~5.2cm
    pipe_curve.bevel_resolution = 4
    
    spline = pipe_curve.splines.new('BEZIER')
    # 4 control points for organic S-curve up wall
    pts = [
        (2.98, 3.12, 0.36), # exit valve
        (3.14, 3.22, 0.45), # bend towards wall
        (3.15, 3.28, 1.10), # climb up wall
        (3.18, 3.28, 1.65)  # enter wall penetration cap
    ]
    spline.bezier_points.add(len(pts) - 1)
    for i, pt in enumerate(pts):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
        
    p_obj = bpy.data.objects.new('AC_Insulated_Pipes', pipe_curve)
    p_obj.data.materials.append(mats['props_ac_meter'])
    ac_col.objects.link(p_obj)
    
    # Wall Penetration Cap / Sleeve Flange (穿墙密封盖) at (3.18, 3.28, 1.65)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.04, location=(3.18, 3.28, 1.65))
    flange = bpy.context.active_object
    flange.rotation_euler = (0, math.radians(90), 0)
    flange.data.materials.append(mats['props_ac_meter'])
    bpy.ops.object.shade_smooth()
    ac_col.objects.link(flange)
    bpy.context.collection.objects.unlink(flange)
    
    # Condensation Drain Hose (冷凝水塑料波纹软管) dangling down to ground
    drain_curve = bpy.data.curves.new('AC_Condensate_Drain_Hose', type='CURVE')
    drain_curve.dimensions = '3D'
    drain_curve.fill_mode = 'FULL'
    drain_curve.bevel_depth = 0.010
    d_spline = drain_curve.splines.new('BEZIER')
    d_pts = [
        (2.98, 3.14, 0.32),
        (3.04, 3.18, 0.24),
        (3.06, 3.22, 0.16)
    ]
    d_spline.bezier_points.add(len(d_pts) - 1)
    for i, pt in enumerate(d_pts):
        bp = d_spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    d_obj = bpy.data.objects.new('AC_Condensate_Drain_Hose', drain_curve)
    d_obj.data.materials.append(mats['cable_rubber'])
    ac_col.objects.link(d_obj)
    
    return col

# -------------------------------------------------------------
# 3. HIGH-PRECISION UTILITY POLE ASSEMBLY
# -------------------------------------------------------------
def build_utility_pole_assembly(mats):
    col = bpy.data.collections.new("03_Utility_Pole_Assembly")
    bpy.context.scene.collection.children.link(col)
    
    pole_x = 0.95
    pole_y = -3.20
    base_z = 0.15
    pole_h = 9.60
    
    # 1. Tapered Concrete Pole Body (圆锥台混凝土杆)
    # Base radius 0.17m, top radius 0.10m
    mesh = bpy.data.meshes.new("Concrete_Utility_Pole")
    bm = bmesh.new()
    # Create cone / tapered cylinder
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=0.17,
        radius2=0.10,
        depth=pole_h
    )
    bm.to_mesh(mesh)
    bm.free()
    pole_obj = bpy.data.objects.new("Concrete_Utility_Pole", mesh)
    pole_obj.location = (pole_x, pole_y, base_z + pole_h * 0.5)
    pole_obj.data.materials.append(mats['utility_pole'])
    bpy.ops.object.shade_smooth()
    col.objects.link(pole_obj)
    
    # 2. Metal Climbing Rungs (登杆脚钉)
    # Staggered every 44cm from Z = 2.2 to Z = 8.2, embedded securely into concrete pole
    rung_col = bpy.data.collections.new("Climbing_Rungs")
    col.children.link(rung_col)
    rung_z_start = 2.2
    rung_count = 14
    for r in range(rung_count):
        rz = rung_z_start + r * 0.44
        # Stagger alternating angles: +45 deg vs -45 deg
        angle = math.radians(45) if (r % 2 == 0) else math.radians(-45)
        # Pole radius at this height:
        t_h = (rz - base_z) / pole_h
        r_pole = 0.17 - t_h * 0.07
        
        # Rung total length 0.24m: 0.09m penetrates into concrete pole, 0.15m steps out
        depth_rung = 0.24
        rc = r_pole + 0.03 # Radial center of rod
        rx = pole_x + rc * math.cos(angle)
        ry = pole_y + rc * math.sin(angle)
        
        # Align along radial direction: rotate around Y by 90 deg, then around Z by angle
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=depth_rung, location=(rx, ry, rz))
        rung = bpy.context.active_object
        rung.name = f"Climbing_Rung_{r}"
        rung.rotation_euler = (0, math.radians(90), angle)
        rung.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        rung_col.objects.link(rung)
        bpy.context.collection.objects.unlink(rung)
        
        # Japanese utility pole rung upward safety hook tab (3.5cm high at outer tip)
        tip_r = r_pole + 0.145
        tip_x = pole_x + tip_r * math.cos(angle)
        tip_y = pole_y + tip_r * math.sin(angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.038, location=(tip_x, tip_y, rz + 0.015))
        hook = bpy.context.active_object
        hook.name = f"Climbing_Rung_Hook_{r}"
        hook.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        rung_col.objects.link(hook)
        bpy.context.collection.objects.unlink(hook)
        
    # 3. Pole-Mounted Heavy-Duty Transformer (柱上金属变压器) at Z = 5.9m
    trans_z = 5.90
    trans_x = pole_x - 0.38
    trans_y = pole_y
    
    # Mounting steel saddle bracket to pole
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x - 0.18, pole_y, trans_z))
    t_bracket = bpy.context.active_object
    t_bracket.name = "Transformer_Mount_Bracket"
    t_bracket.scale = (0.28, 0.42, 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    t_bracket.data.materials.append(mats['transformer'])
    col.objects.link(t_bracket)
    bpy.context.collection.objects.unlink(t_bracket)
    
    # Cylindrical Transformer Body (直径 62cm, 高 88cm)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.31, depth=0.88, location=(trans_x, trans_y, trans_z))
    t_body = bpy.context.active_object
    t_body.name = "Transformer_Cylinder_Body"
    t_body.data.materials.append(mats['transformer'])
    bpy.ops.object.shade_smooth()
    col.objects.link(t_body)
    bpy.context.collection.objects.unlink(t_body)
    
    # Top lid flange
    bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.05, location=(trans_x, trans_y, trans_z + 0.45))
    t_lid = bpy.context.active_object
    t_lid.name = "Transformer_Top_Lid"
    t_lid.data.materials.append(mats['transformer'])
    apply_bevel(t_lid, width=0.008, segments=2)
    col.objects.link(t_lid)
    bpy.context.collection.objects.unlink(t_lid)
    
    # Radiator Cooling Fins (散热鳍片) on sides
    fin_col = bpy.data.collections.new("Transformer_Cooling_Fins")
    col.children.link(fin_col)
    for fin_idx in range(8):
        f_rot = math.radians(135 + fin_idx * 13)
        fx = trans_x + 0.32 * math.cos(f_rot)
        fy = trans_y + 0.32 * math.sin(f_rot)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(fx, fy, trans_z))
        fin = bpy.context.active_object
        fin.scale = (0.012, 0.09, 0.70)
        fin.rotation_euler = (0, 0, f_rot)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        fin.data.materials.append(mats['transformer'])
        fin_col.objects.link(fin)
        bpy.context.collection.objects.unlink(fin)
        
    # Lifting Lugs (吊装挂耳) x2
    for ly in [trans_y - 0.28, trans_y + 0.28]:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.012, location=(trans_x, ly, trans_z + 0.46))
        lug = bpy.context.active_object
        lug.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        col.objects.link(lug)
        bpy.context.collection.objects.unlink(lug)
        
    # 3 High-Voltage Porcelain Bushings on Top (顶部高压套管与接线柱)
    for b_idx in range(3):
        by = trans_y - 0.18 + b_idx * 0.18
        # Stepped porcelain bushing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.16, location=(trans_x, by, trans_z + 0.55))
        bushing = bpy.context.active_object
        bushing.data.materials.append(mats['insulator_porcelain'])
        bpy.ops.object.shade_smooth()
        col.objects.link(bushing)
        bpy.context.collection.objects.unlink(bushing)
        
        # Copper terminal stud
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.08, location=(trans_x, by, trans_z + 0.66))
        stud = bpy.context.active_object
        stud.data.materials.append(mats['aluminum_silver'])
        col.objects.link(stud)
        bpy.context.collection.objects.unlink(stud)
        
    # Yellow Danger High Voltage Plaque (高压危险标牌)
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(trans_x - 0.32, trans_y, trans_z))
    plaque = bpy.context.active_object
    plaque.name = "Warning_Plaque"
    plaque.rotation_euler = (0, math.radians(90), 0)
    plaque.scale = (0.24, 0.16, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plaque.data.materials.append(mats['tactile_paving']) # Vibrant warning yellow
    col.objects.link(plaque)
    bpy.context.collection.objects.unlink(plaque)
    
    # 4. Galvanized Steel Crossarms & Ribbed Porcelain Insulators (角钢横担与阶梯瓷瓶)
    # Primary Upper Crossarm at Z = 8.3m (2.4m length spanning along Y)
    arm_z1 = 8.30
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x, pole_y, arm_z1))
    crossarm1 = bpy.context.active_object
    crossarm1.name = "Crossarm_Primary_L_Steel"
    crossarm1.scale = (0.12, 2.40, 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    crossarm1.data.materials.append(mats['aluminum_silver'])
    apply_bevel(crossarm1, width=0.01, segments=2)
    col.objects.link(crossarm1)
    bpy.context.collection.objects.unlink(crossarm1)
    
    # Diagonal angle-steel bracing struts (斜撑) x2
    for s_sign in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=1.10, location=(pole_x, pole_y + s_sign * 0.55, arm_z1 - 0.45))
        strut = bpy.context.active_object
        strut.rotation_euler = (s_sign * math.radians(35), 0, 0)
        strut.data.materials.append(mats['aluminum_silver'])
        bpy.ops.object.shade_smooth()
        col.objects.link(strut)
        bpy.context.collection.objects.unlink(strut)
        
    # 3 Sets of Stepped Ribbed Porcelain Bell Insulators on Crossarm 1
    # Positions along Y: -0.95, 0.0, +0.95
    insulator_positions = [
        (pole_x, pole_y - 0.95, arm_z1 + 0.18),
        (pole_x, pole_y + 0.00, arm_z1 + 0.18),
        (pole_x, pole_y + 0.95, arm_z1 + 0.18)
    ]
    ins_col = bpy.data.collections.new("Porcelain_Insulators")
    col.children.link(ins_col)
    
    for ip_idx, (ix, iy, iz) in enumerate(insulator_positions):
        # Stepped double bell disc skirts
        for s_lvl in [0.0, 0.10]:
            bpy.ops.mesh.primitive_cone_add(radius1=0.085, radius2=0.035, depth=0.09, location=(ix, iy, iz + s_lvl))
            bell = bpy.context.active_object
            bell.name = f"InsulatorBell_{ip_idx}_{s_lvl}"
            bell.data.materials.append(mats['insulator_porcelain'])
            bpy.ops.object.shade_smooth()
            ins_col.objects.link(bell)
            bpy.context.collection.objects.unlink(bell)
            
        # Top pin / wire tie collar
        bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.08, location=(ix, iy, iz + 0.18))
        pin = bpy.context.active_object
        pin.data.materials.append(mats['aluminum_silver'])
        ins_col.objects.link(pin)
        bpy.context.collection.objects.unlink(pin)
        
    # Secondary Lower Crossarm at Z = 7.1m (1.4m length for comms & low voltage)
    arm_z2 = 7.10
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x, pole_y, arm_z2))
    crossarm2 = bpy.context.active_object
    crossarm2.name = "Crossarm_Secondary"
    crossarm2.scale = (0.10, 1.40, 0.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    crossarm2.data.materials.append(mats['aluminum_silver'])
    apply_bevel(crossarm2, width=0.008, segments=2)
    col.objects.link(crossarm2)
    bpy.context.collection.objects.unlink(crossarm2)
    
    # 2 Spool Insulators on Crossarm 2
    for s_idx, sy in enumerate([pole_y - 0.50, pole_y + 0.50]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.12, location=(pole_x, sy, arm_z2 + 0.10))
        spool = bpy.context.active_object
        spool.data.materials.append(mats['insulator_porcelain'])
        bpy.ops.object.shade_smooth()
        ins_col.objects.link(spool)
        bpy.context.collection.objects.unlink(spool)
        
    # 5. Pole-Top Fixtures & Municipal Accessories
    # A. Curved Street Light Arm & Modern LED Luminaire (挑臂路灯) at Z = 7.4m extending towards road (-X)
    arm_curve = bpy.data.curves.new('Street_Lamp_Arm', type='CURVE')
    arm_curve.dimensions = '3D'
    arm_curve.fill_mode = 'FULL'
    arm_curve.bevel_depth = 0.028
    a_spline = arm_curve.splines.new('BEZIER')
    a_pts = [
        (pole_x, pole_y, 7.35),
        (pole_x - 0.60, pole_y + 0.10, 7.50),
        (pole_x - 1.20, pole_y + 0.15, 7.20)
    ]
    a_spline.bezier_points.add(len(a_pts) - 1)
    for i, pt in enumerate(a_pts):
        bp = a_spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    a_obj = bpy.data.objects.new('Street_Lamp_Arm', arm_curve)
    a_obj.data.materials.append(mats['aluminum_dark'])
    col.objects.link(a_obj)
    
    # LED Luminaire Head at (pole_x - 1.20, pole_y + 0.15, 7.20)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x - 1.20, pole_y + 0.15, 7.18))
    led_head = bpy.context.active_object
    led_head.name = "Street_Lamp_LED_Head"
    led_head.scale = (0.42, 0.18, 0.08)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    led_head.data.materials.append(mats['aluminum_dark'])
    apply_bevel(led_head, width=0.01, segments=2)
    col.objects.link(led_head)
    bpy.context.collection.objects.unlink(led_head)
    
    # B. Weatherproof Junction Box at Z = 4.8m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x + 0.16, pole_y, 4.80))
    jbox = bpy.context.active_object
    jbox.name = "Junction_Box"
    jbox.scale = (0.12, 0.22, 0.32)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    jbox.data.materials.append(mats['props_ac_meter'])
    apply_bevel(jbox, width=0.01, segments=2)
    col.objects.link(jbox)
    bpy.context.collection.objects.unlink(jbox)
    
    # C. Compact CCTV Security Camera at Z = 6.4m
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(pole_x - 0.24, pole_y + 0.18, 6.40))
    cctv = bpy.context.active_object
    cctv.name = "CCTV_Camera"
    cctv.scale = (0.16, 0.08, 0.08)
    cctv.rotation_euler = (0, math.radians(20), math.radians(-35))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cctv.data.materials.append(mats['aluminum_silver'])
    apply_bevel(cctv, width=0.008, segments=2)
    col.objects.link(cctv)
    bpy.context.collection.objects.unlink(cctv)
    
    # -------------------------------------------------------------
    # 6. CATENARY HANGING CABLES (悬链线真实重力下垂电缆)
    # -------------------------------------------------------------
    cables_col = bpy.data.collections.new("Catenary_Cables")
    col.children.link(cables_col)
    
    # 3 High-Voltage Main Conductors spanning along Y from -7.5 to +7.5
    # Connecting through the 3 insulator tops at Z ~ 8.52m
    for c_idx, iy in enumerate([-0.95, 0.0, 0.95]):
        py = pole_y + iy
        # Cable segment 1: from street start Y = -7.5 to insulator
        p_start1 = (pole_x, -7.5, 8.70)
        p_end1 = (pole_x, py, 8.52)
        c1 = build_catenary_curve(f"HV_Cable_{c_idx}_Part1", p_start1, p_end1, sag=0.28, radius=0.012, material=mats['cable_rubber'])
        cables_col.objects.link(c1)
        bpy.context.collection.objects.unlink(c1)
        
        # Cable segment 2: from insulator to street end Y = +7.5
        p_start2 = (pole_x, py, 8.52)
        p_end2 = (pole_x, 7.5, 8.70)
        c2 = build_catenary_curve(f"HV_Cable_{c_idx}_Part2", p_start2, p_end2, sag=0.36, radius=0.012, material=mats['cable_rubber'])
        cables_col.objects.link(c2)
        bpy.context.collection.objects.unlink(c2)
        
    # 2 Service Drop Wires branching from pole to house 2F meter entry
    # Pole end at (pole_x, pole_y - 0.50, 7.20)
    # House 2F entry at (3.18, 0.60, 5.10)
    s_drop1 = build_catenary_curve(
        "Service_Drop_Wire_1",
        (pole_x, pole_y - 0.50, 7.20),
        (3.18, 0.50, 5.15),
        sag=0.32,
        radius=0.010,
        material=mats['cable_rubber']
    )
    cables_col.objects.link(s_drop1)
    bpy.context.collection.objects.unlink(s_drop1)
    
    s_drop2 = build_catenary_curve(
        "Service_Drop_Wire_2",
        (pole_x, pole_y + 0.50, 7.20),
        (3.18, 0.70, 5.05),
        sag=0.35,
        radius=0.010,
        material=mats['cable_rubber']
    )
    cables_col.objects.link(s_drop2)
    bpy.context.collection.objects.unlink(s_drop2)
    
    # Jumper wires connecting transformer bushings to crossarm lines
    for j_idx in range(3):
        by = trans_y - 0.18 + j_idx * 0.18
        p_bush = (trans_x, by, trans_z + 0.68)
        p_line = (pole_x, pole_y - 0.95 + j_idx * 0.95, arm_z1 + 0.10)
        jw = build_catenary_curve(f"Transformer_Jumper_{j_idx}", p_bush, p_line, sag=-0.15, segments=16, radius=0.008, material=mats['cable_rubber'])
        cables_col.objects.link(jw)
        bpy.context.collection.objects.unlink(jw)
        
    return col

# -------------------------------------------------------------
# 4. LIGHTING & ENVIRONMENT (NISHITA SKY & PHYSICAL SUN)
# -------------------------------------------------------------
def setup_lighting():
    # World setup with Nishita Sky Texture
    world = bpy.data.worlds.new("GoldenSlice_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_links = world.node_tree.links
    w_nodes.clear()
    
    w_out = w_nodes.new(type='ShaderNodeOutputWorld')
    bg = w_nodes.new(type='ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.80 # Reduced ambient to eliminate overexposure and reveal micro-shadows
    
    sky = w_nodes.new(type='ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(42.0)
    sky.sun_rotation = math.radians(125.0)
    sky.altitude = 10.0
    sky.air_density = 1.0
    sky.aerosol_density = 0.8
    sky.ozone_density = 1.2
    sky.sun_disc = True
    
    w_links.new(sky.outputs['Color'], bg.inputs['Color'])
    w_links.new(bg.outputs['Background'], w_out.inputs['Surface'])
    
    # Add a matching physical Sun Lamp for crisp, defined contact shadows
    sun_data = bpy.data.lights.new(name="Sun_Key_Light", type='SUN')
    sun_data.energy = 1.6 # Balanced CS2 style key light, preventing blowout
    sun_data.angle = math.radians(1.2)
    sun_data.color = (1.0, 0.98, 0.94) # Warm 5500K morning sun
    
    sun_obj = bpy.data.objects.new("Sun_Key_Light", sun_data)
    sun_obj.rotation_euler = (math.radians(48), math.radians(22), math.radians(-55))
    bpy.context.scene.collection.objects.link(sun_obj)

# -------------------------------------------------------------
# 5. CAMERAS & RENDER VIEWS
# -------------------------------------------------------------
def point_camera_at(cam_obj, target_loc):
    import mathutils
    cam_loc = cam_obj.location
    direction = mathutils.Vector(target_loc) - cam_loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

def setup_cameras():
    cameras = {}
    
    # Shot 01: Street View (街道人眼全景视角，展现双层住宅、电线杆与整体空间关系)
    cam1_data = bpy.data.cameras.new("Cam_01_StreetView")
    cam1_data.lens = 28
    cam1_obj = bpy.data.objects.new("Cam_01_StreetView", cam1_data)
    cam1_obj.location = (-6.20, -7.50, 2.40)
    point_camera_at(cam1_obj, (1.80, 0.20, 3.60))
    bpy.context.scene.collection.objects.link(cam1_obj)
    cameras['01_golden_slice_street_view'] = cam1_obj
    
    # Shot 02: Facade & AC Closeup (窗户内嵌深度与空调外机微距特写)
    cam2_data = bpy.data.cameras.new("Cam_02_FacadeAC")
    cam2_data.lens = 32
    cam2_obj = bpy.data.objects.new("Cam_02_FacadeAC", cam2_data)
    cam2_obj.location = (0.50, 3.40, 1.10)
    point_camera_at(cam2_obj, (3.18, 2.05, 1.05))
    bpy.context.scene.collection.objects.link(cam2_obj)
    cameras['02_golden_slice_facade_ac_detail'] = cam2_obj
    
    # Shot 03: Utility Pole Closeup (电线杆变压器、绝缘瓷瓶与悬链线仰视特写)
    cam3_data = bpy.data.cameras.new("Cam_03_UtilityPole")
    cam3_data.lens = 60
    cam3_obj = bpy.data.objects.new("Cam_03_UtilityPole", cam3_data)
    cam3_obj.location = (-1.40, -5.40, 2.40)
    point_camera_at(cam3_obj, (0.85, -3.20, 6.80))
    bpy.context.scene.collection.objects.link(cam3_obj)
    cameras['03_golden_slice_utility_pole_closeup'] = cam3_obj
    
    # Shot 04: Ground & Curb Detail (沥青路面、修补黑胶、导盲砖与下水道井盖特写)
    cam4_data = bpy.data.cameras.new("Cam_04_GroundCurb")
    cam4_data.lens = 42
    cam4_obj = bpy.data.objects.new("Cam_04_GroundCurb", cam4_data)
    cam4_obj.location = (-1.80, -1.20, 1.85)
    point_camera_at(cam4_obj, (0.35, 0.35, 0.12))
    bpy.context.scene.collection.objects.link(cam4_obj)
    cameras['04_golden_slice_ground_curb_detail'] = cam4_obj
    
    return cameras

def configure_render_engine(scene):
    bpy.ops.preferences.addon_enable(module='cycles')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    
    # Preferences GPU device setup
    cprefs = bpy.context.preferences.addons['cycles'].preferences
    cprefs.get_devices()
    # Prioritize OPTIX then CUDA
    optix_found = False
    for t in ['OPTIX', 'CUDA']:
        if any(d.type == t for d in cprefs.devices):
            cprefs.compute_device_type = t
            optix_found = True
            print(f"Cycles compute device type set to: {t}")
            break
            
    for d in cprefs.devices:
        if d.type in ['OPTIX', 'CUDA']:
            d.use = True
            print(f"Enabled GPU compute device: {d.name} ({d.type})")
            
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    # 2K Resolution: 2560 x 1440 (QHD)
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    
    # Color Management for CS2 / Anime-Realism 3A look
    scene.view_settings.view_transform = 'AgX' if 'AgX' in [c.name for c in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = -0.35

def main():
    print("=========================================================")
    print("Starting Golden Slice Unit 3D Construction in Blender 5.2")
    print("=========================================================")
    reset_scene()
    
    # Create Materials
    mats = {
        'wall_plaster': create_pbr_material("M_WallPlaster", "wall_plaster", base_color_fallback=(0.80, 0.79, 0.76, 1.0), roughness_val=0.82, uv_scale=(4.0, 4.0), normal_strength=1.8),
        'asphalt_road': create_pbr_material("M_AsphaltRoad", "asphalt_road", base_color_fallback=(0.16, 0.16, 0.17, 1.0), roughness_val=0.88, uv_scale=(1.0, 2.5), normal_strength=2.2),
        'sidewalk_tiles': create_pbr_material("M_SidewalkTiles", "sidewalk_tiles", base_color_fallback=(0.65, 0.66, 0.68, 1.0), roughness_val=0.68, uv_scale=(3.0, 6.0), normal_strength=1.6),
        'tactile_paving': create_pbr_material("M_TactilePaving", "tactile_paving", base_color_fallback=(0.94, 0.72, 0.05, 1.0), roughness_val=0.52, uv_scale=(1.0, 12.0), normal_strength=2.2),
        'concrete_curb': create_pbr_material("M_ConcreteCurb", "concrete_curb", base_color_fallback=(0.58, 0.59, 0.60, 1.0), roughness_val=0.72, uv_scale=(1.0, 6.0), normal_strength=1.3),
        'metal_manhole': create_pbr_material("M_MetalManhole", "metal_manhole", base_color_fallback=(0.16, 0.17, 0.18, 1.0), roughness_val=0.45, metallic_val=0.85, uv_scale=(1.0, 1.0), normal_strength=2.4),
        'props_ac_meter': create_pbr_material("M_PropsACMeter", "props_ac_meter", base_color_fallback=(0.86, 0.87, 0.88, 1.0), roughness_val=0.42, uv_scale=(1.0, 1.0), normal_strength=1.5),
        'utility_pole': create_pbr_material("M_UtilityPole", "utility_pole", base_color_fallback=(0.61, 0.62, 0.63, 1.0), roughness_val=0.78, uv_scale=(1.0, 4.0), normal_strength=1.3),
        'transformer': create_transformer_material("M_Transformer"),
        'glass': create_glass_material("M_Glass"),
        'aluminum_dark': create_aluminum_material("M_Aluminum_Dark", dark=True),
        'aluminum_silver': create_aluminum_material("M_Aluminum_Silver", dark=False),
        'insulator_porcelain': create_insulator_porcelain_material("M_InsulatorPorcelain"),
        'cable_rubber': create_cable_material("M_CableRubber"),
        'interior': create_interior_material("M_InteriorRoom")
    }
    
    # Build 3 Golden Slice Assets
    print("Building Asset 1: Ground & Sidewalk Patch (8m x 15m)...")
    build_ground_patch(mats)
    
    print("Building Asset 2: Modern 2F Japanese House...")
    build_japanese_house(mats)
    
    print("Building Asset 3: Utility Pole Assembly with Catenary Cables...")
    build_utility_pole_assembly(mats)
    
    # Setup World & Lighting
    print("Setting up Nishita Sky & Physical Sunlight...")
    setup_lighting()
    
    # Setup Cameras
    print("Setting up 4 Technical Review Cameras...")
    cameras = setup_cameras()
    
    # Configure Cycles Engine
    print("Configuring Cycles GPU (OptiX / CUDA) + AgX Color Management...")
    scene = bpy.context.scene
    configure_render_engine(scene)
    
    # Save .blend project
    blend_paths = [
        os.path.abspath("asternova/art/models/golden_slice/golden_slice_unit.blend"),
        os.path.abspath("art/models/golden_slice/golden_slice_unit.blend")
    ]
    for bp in blend_paths:
        ensure_dir(os.path.dirname(bp))
        bpy.ops.wm.save_as_mainfile(filepath=bp)
        print(f"Saved Blender project to: {bp}")
        
    # Export .glb
    glb_paths = [
        os.path.abspath("asternova/art/models/golden_slice/golden_slice_unit.glb"),
        os.path.abspath("art/models/golden_slice/golden_slice_unit.glb")
    ]
    for gp in glb_paths:
        ensure_dir(os.path.dirname(gp))
        try:
            bpy.ops.export_scene.gltf(filepath=gp, export_format='GLB', export_materials='EXPORT', export_cameras=True)
            print(f"Exported GLB asset to: {gp}")
        except Exception as e:
            print(f"GLB export note: {e}")
            
    # Render 4 Shots
    screenshot_dirs = [
        os.path.abspath("asternova/render-lab/screenshots/golden_slice"),
        os.path.abspath("render-lab/screenshots/golden_slice")
    ]
    for d in screenshot_dirs:
        ensure_dir(d)
        
    print("\n--- Starting Cycles 2K Rendering (4 Views) ---")
    for shot_name, cam_obj in cameras.items():
        print(f"\nRendering View: {shot_name} (2560x1440 2K)...")
        scene.camera = cam_obj
        out_file = os.path.join(screenshot_dirs[0], f"{shot_name}.png")
        scene.render.filepath = out_file
        bpy.ops.render.render(write_still=True)
        print(f"Finished rendering: {out_file}")
        
        # Copy to alternate directory
        out_file2 = os.path.join(screenshot_dirs[1], f"{shot_name}.png")
        if os.path.exists(out_file):
            import shutil
            shutil.copy2(out_file, out_file2)
            print(f"Mirrored screenshot to: {out_file2}")
            
    print("\n=========================================================")
    print("Golden Slice Unit successfully built, rendered, and archived!")
    print("=========================================================")

if __name__ == "__main__":
    main()
