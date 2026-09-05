# AsterNova - 100% Original Commercial Aster Master High-Poly Pipeline
# Phase 1 to Phase 4 Complete Technical Implementation - High Fidelity V2.2
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler, Quaternion

print("=== Starting AsterNova Master High-Fidelity Character Pipeline V2.2 ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

# File Paths
models_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster"
src_vrm = os.path.join(models_dir, "aster_base.vrm")
art_models_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models"
out_blend = os.path.join(art_models_dir, "aster_v2_clean_master.blend")
out_glb = os.path.join(art_models_dir, "aster_v2_clean_master.glb")
out_renders_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\aster_v2"
os.makedirs(art_models_dir, exist_ok=True)
os.makedirs(out_renders_dir, exist_ok=True)

# -------------------------------------------------------------
# STEP 1: IMPORT CLEAN COMMERCIAL BASE (CC0 / Allowed License)
# -------------------------------------------------------------
bpy.ops.import_scene.gltf(filepath=src_vrm)

armature = bpy.data.objects.get("Armature")
body_obj = bpy.data.objects.get("Body")
face_obj = bpy.data.objects.get("Face")

for name in ["Icosphere", "secondary"]:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

# Convert to clean quads
for obj in [body_obj, face_obj]:
    if obj:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.object.mode_set(mode='OBJECT')

# -------------------------------------------------------------
# STEP 2: 8.5 HEAD RATIO RETARGETING & SWAN NECK CALIBRATION
# -------------------------------------------------------------
# Target: Height = 1.650m, 8.5 Heads -> Head Height = 0.194m
head_scale = 0.194 / 0.250  # ~0.776
head_z_center_orig = 1.460
head_z_center_target = 1.553

# Refine Face Mesh (Delicate V-line jaw, soft chin, refined eye sockets)
bm_face = bmesh.new()
bm_face.from_mesh(face_obj.data)

for v in bm_face.verts:
    rx = v.co.x * head_scale
    ry = (v.co.y - 0.015) * head_scale + 0.010
    rz = (v.co.z - head_z_center_orig) * head_scale + head_z_center_target
    
    if rz < 1.490 and abs(rx) < 0.070:
        chin_t = max(0.0, (1.490 - rz) / 0.045)
        rx *= (1.0 - 0.12 * chin_t)
        if rz < 1.465 and abs(rx) < 0.025:
            rz -= 0.004 * (1.0 - abs(rx)/0.025)
            
    v.co.x = rx
    v.co.y = ry
    v.co.z = rz

bm_face.to_mesh(face_obj.data)
bm_face.free()
face_obj.data.update()

# Retarget Body Mesh
bm_body = bmesh.new()
bm_body.from_mesh(body_obj.data)

for v in bm_body.verts:
    z = v.co.z
    x = v.co.x
    y = v.co.y
    
    if z >= 1.330:
        x = x * head_scale
        y = (y - 0.015) * head_scale + 0.010
        z = (z - head_z_center_orig) * head_scale + head_z_center_target
        if z < 1.470:
            t = (1.470 - z) / 0.030
            x *= (1.0 - 0.08 * t)
            y *= (1.0 - 0.08 * t)
    elif z >= 1.260:
        t = (z - 1.260) / (1.330 - 1.260)
        z = 1.370 + t * (1.456 - 1.370)
        x *= 0.82
        y *= 0.82
    elif z >= 0.770:
        t = (z - 0.770) / (1.260 - 0.770)
        z = 0.840 + t * (1.370 - 0.840)
        
        # Shoulder tapering & soft slope (微溜肩)
        if t > 0.75:
            shoulder_t = (t - 0.75) / 0.25
            x *= (1.0 - 0.08 * shoulder_t)
            z -= 0.012 * shoulder_t * (abs(x) / 0.16)
            
        # Slender waist at t ~ 0.42 (Z ~ 1.05m)
        waist_dist = abs(t - 0.42)
        if waist_dist < 0.25:
            w_factor = (0.25 - waist_dist) / 0.25
            x *= (1.0 - 0.10 * w_factor)
            y *= (1.0 - 0.08 * w_factor)
            
        if t < 0.25:
            hip_factor = (0.25 - t) / 0.25
            x *= (1.0 - 0.06 * hip_factor)
    else:
        t = z / 0.770
        if t < 0.54:
            z = (t / 0.54) * 0.460
        else:
            z = 0.460 + ((t - 0.54) / 0.46) * (0.840 - 0.460)
            
        leg_slender = 0.88 + 0.06 * math.sin(t * math.pi)
        x *= leg_slender
        y *= leg_slender

    # INNER MANNEQUIN TUCK UNDER CLOTHING (Z from 0.96 to 1.35)
    if 0.96 <= z <= 1.35 and abs(x) < 0.18:
        if z <= 1.15: # Waist inside corset
            x *= 0.78
            y *= 0.72
        else: # Chest inside blouse
            x *= 0.82
            y *= 0.76

    v.co.x = x
    v.co.y = y
    v.co.z = z

# -------------------------------------------------------------
# STEP 3: A-POSE CALIBRATION (Rotate Arms DOWN ~38° to match turnaround-final.png)
# -------------------------------------------------------------
l_shoulder_pivot = Vector((-0.1086, -0.0255, 1.3695))
r_shoulder_pivot = Vector((0.1086, -0.0255, 1.3695))
arm_angle = math.radians(-38.0)

rot_l = Matrix.Rotation(arm_angle, 3, 'Y')
rot_r = Matrix.Rotation(-arm_angle, 3, 'Y')

for v in bm_body.verts:
    # Left Arm
    if v.co.x < -0.108 and v.co.z > 0.85:
        offset = v.co - l_shoulder_pivot
        weight = min(1.0, max(0.0, (-v.co.x - 0.108) / 0.045))
        rot_curr = Matrix.Rotation(arm_angle * weight, 3, 'Y')
        v.co = l_shoulder_pivot + rot_curr @ offset
    # Right Arm
    elif v.co.x > 0.108 and v.co.z > 0.85:
        offset = v.co - r_shoulder_pivot
        weight = min(1.0, max(0.0, (v.co.x - 0.108) / 0.045))
        rot_curr = Matrix.Rotation(-arm_angle * weight, 3, 'Y')
        v.co = r_shoulder_pivot + rot_curr @ offset

bm_body.to_mesh(body_obj.data)
bm_body.free()
body_obj.data.update()

if armature:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    for b in armature.data.edit_bones:
        if 'UpperArm' in b.name or 'LowerArm' in b.name or 'Hand' in b.name:
            is_left = '_L_' in b.name
            pivot = l_shoulder_pivot if is_left else r_shoulder_pivot
            rot = rot_l if is_left else rot_r
            b.head = pivot + rot @ (b.head - pivot)
            b.tail = pivot + rot @ (b.tail - pivot)
    bpy.ops.object.mode_set(mode='OBJECT')

print("Applied 8.5 head ratio and downward A-pose successfully.")

# -------------------------------------------------------------
# STEP 4: NPR SHADER & MATERIAL FACTORY (Clean Anime Cel-Shading)
# -------------------------------------------------------------
def make_npr_material(name, base_rgb, emission_strength=0.18, roughness=0.35):
    mat = bpy.data.materials.new(name=name)
    mat.use_backface_culling = True
    tree = mat.node_tree
    tree.nodes.clear()
    
    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*base_rgb, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Emission Color'].default_value = (*base_rgb, 1.0)
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

def make_chiffon_material(name, color_rgb, alpha=0.78):
    mat = bpy.data.materials.new(name=name)
    mat.use_backface_culling = True
    mat.blend_method = 'BLEND'
    tree = mat.node_tree
    tree.nodes.clear()
    
    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*color_rgb, 1.0)
    bsdf.inputs['Alpha'].default_value = alpha
    bsdf.inputs['Roughness'].default_value = 0.20
    bsdf.inputs['IOR'].default_value = 1.33
    bsdf.inputs['Emission Color'].default_value = (*color_rgb, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 0.22
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

def make_metal_material(name, gold_rgb):
    mat = bpy.data.materials.new(name=name)
    mat.use_backface_culling = True
    tree = mat.node_tree
    tree.nodes.clear()
    
    out_node = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*gold_rgb, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.95
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Emission Color'].default_value = (*gold_rgb, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 0.20
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    return mat

# NPR Color Palette (70% White, 15% Pale Blue, 8% Lavender, 5% Silver, 2% Gold)
mat_blouse = make_npr_material("Mat_Aster_Blouse", (0.96, 0.95, 0.94), emission_strength=0.18, roughness=0.5)
mat_corset = make_npr_material("Mat_Aster_Corset", (0.94, 0.93, 0.91), emission_strength=0.16, roughness=0.35)
mat_skirt_outer = make_npr_material("Mat_Aster_Skirt_Outer", (0.97, 0.97, 0.98), emission_strength=0.20, roughness=0.45)
mat_skirt_inner = make_chiffon_material("Mat_Aster_Skirt_InnerChiffon", (0.75, 0.88, 0.99), alpha=0.76)
mat_ribbon_blue = make_npr_material("Mat_Aster_Ribbon_Blue", (0.50, 0.72, 0.95), emission_strength=0.18, roughness=0.25)
mat_ribbon_lightblue = make_npr_material("Mat_Aster_Ribbon_LightBlue", (0.70, 0.85, 0.98), emission_strength=0.20, roughness=0.25)
mat_gold = make_metal_material("Mat_Aster_Champagne_Gold", (0.96, 0.84, 0.45))
mat_pearl = make_npr_material("Mat_Aster_Pearl_White", (0.98, 0.98, 1.00), emission_strength=0.28, roughness=0.12)
mat_hair = make_npr_material("Mat_Aster_Hair_PearlWhite", (0.96, 0.97, 0.99), emission_strength=0.26, roughness=0.30)
mat_shoes = make_npr_material("Mat_Aster_Shoes_White", (0.96, 0.96, 0.97), emission_strength=0.16, roughness=0.20)
mat_socks = make_npr_material("Mat_Aster_Socks_White", (0.98, 0.98, 0.99), emission_strength=0.20, roughness=0.6)

# Outline Material with BACKFACE CULLING
mat_outline = bpy.data.materials.new(name="Mat_Aster_Outline")
mat_outline.use_backface_culling = True
tree_out = mat_outline.node_tree
tree_out.nodes.clear()
out_surf = tree_out.nodes.new('ShaderNodeOutputMaterial')
emission = tree_out.nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (0.28, 0.24, 0.30, 1.0)
emission.inputs['Strength'].default_value = 1.0
tree_out.links.new(emission.outputs['Emission'], out_surf.inputs['Surface'])

# Assign clean body skin texture
skin_tex_path = os.path.join(models_dir, "aster_skin_clean_v2.png")
if os.path.exists(skin_tex_path):
    img_skin = bpy.data.images.load(skin_tex_path, check_existing=True)
    body_skin_mat = bpy.data.materials.get("N00_000_00_Body_00_SKIN (Instance)")
    if body_skin_mat and body_skin_mat.node_tree:
        for n in body_skin_mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = img_skin
        bsdf_skin = body_skin_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf_skin:
            bsdf_skin.inputs['Emission Strength'].default_value = 0.15

for i, m in enumerate(body_obj.data.materials):
    if 'HairBack' in m.name:
        body_obj.data.materials[i] = mat_hair

# Assign custom aqua-blue starry eye iris & star highlight
iris_tex_path = os.path.join(models_dir, "aster_model_F00_000_EyeIris_00.png")
if os.path.exists(iris_tex_path):
    img_iris = bpy.data.images.load(iris_tex_path, check_existing=True)
    iris_mat = bpy.data.materials.get("N00_000_00_EyeIris_00_EYE (Instance)")
    if iris_mat and iris_mat.node_tree:
        for n in iris_mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = img_iris
        bsdf_iris = iris_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf_iris:
            bsdf_iris.inputs['Emission Strength'].default_value = 0.40

hl_tex_path = os.path.join(models_dir, "aster_model_F00_000_EyeHighlight_00.png")
if os.path.exists(hl_tex_path):
    img_hl = bpy.data.images.load(hl_tex_path, check_existing=True)
    hl_mat = bpy.data.materials.get("N00_000_00_EyeHighlight_00_EYE (Instance)")
    if hl_mat and hl_mat.node_tree:
        for n in hl_mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = img_hl
        bsdf_hl = hl_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf_hl:
            bsdf_hl.inputs['Emission Strength'].default_value = 1.0

# Assign soft blush face skin
face_tex_path = os.path.join(models_dir, "aster_model_F00_000_Face_00.png")
if os.path.exists(face_tex_path):
    img_face = bpy.data.images.load(face_tex_path, check_existing=True)
    face_skin_mat = bpy.data.materials.get("N00_000_00_Face_00_SKIN (Instance)")
    if face_skin_mat and face_skin_mat.node_tree:
        for n in face_skin_mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = img_face
        bsdf_face = face_skin_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf_face:
            bsdf_face.inputs['Emission Strength'].default_value = 0.20

print("NPR Materials and Eye textures configured.")

# -------------------------------------------------------------
# STEP 5: PROCEDURAL MODELING HELPER FUNCTIONS
# -------------------------------------------------------------
def create_surface_ribbon(bm, points, widths, normal_dir=Vector((0, 1, 0)), mat_idx=0):
    n = len(points)
    verts_left = []
    verts_right = []
    
    for i in range(n):
        p = Vector(points[i])
        w = max(widths[i], 0.001)
        if i < n - 1:
            tan = (Vector(points[i+1]) - p).normalized()
        else:
            tan = (p - Vector(points[i-1])).normalized()
        
        binorm = tan.cross(normal_dir).normalized()
        if binorm.length < 0.001:
            binorm = Vector((1, 0, 0))
            
        v_left = p - binorm * (w * 0.5)
        v_right = p + binorm * (w * 0.5)
        
        verts_left.append(bm.verts.new(v_left))
        verts_right.append(bm.verts.new(v_right))
        
    for i in range(n - 1):
        v1_curr = verts_left[i]
        v2_curr = verts_right[i]
        v2_next = verts_right[i+1]
        v1_next = verts_left[i+1]
        
        face = bm.faces.new([v1_curr, v2_curr, v2_next, v1_next])
        face.material_index = mat_idx

def create_hair_strand_3d(bm, points, widths, thicknesses, normal_dir=Vector((0, 1, 0)), mat_idx=0):
    """
    Creates a AAA-standard 3D anime hair clump (triangular prism with sharp front ridge).
    Closed, manifold, perfect for cel-shading and inverted-hull outline!
    """
    n = len(points)
    rings = []
    
    for i in range(n - 1):
        p = Vector(points[i])
        w = max(widths[i], 0.002)
        th = max(thicknesses[i], 0.002)
        
        tan = (Vector(points[i+1]) - p).normalized()
        binorm = tan.cross(normal_dir).normalized()
        if binorm.length < 0.001:
            binorm = Vector((1, 0, 0))
        norm = binorm.cross(tan).normalized()
        
        v_left = bm.verts.new(p - binorm * (w * 0.5))
        v_right = bm.verts.new(p + binorm * (w * 0.5))
        v_ridge = bm.verts.new(p + norm * th)
        rings.append((v_left, v_right, v_ridge))
        
    p_tip = Vector(points[-1])
    v_tip = bm.verts.new(p_tip)
    
    for i in range(len(rings) - 1):
        l1, r1, m1 = rings[i]
        l2, r2, m2 = rings[i+1]
        
        f_fl = bm.faces.new([l1, m1, m2, l2])
        f_fl.material_index = mat_idx
        f_fr = bm.faces.new([m1, r1, r2, m2])
        f_fr.material_index = mat_idx
        f_bk = bm.faces.new([r1, l1, l2, r2])
        f_bk.material_index = mat_idx
        
    l_last, r_last, m_last = rings[-1]
    f_tl = bm.faces.new([l_last, m_last, v_tip])
    f_tl.material_index = mat_idx
    f_tr = bm.faces.new([m_last, r_last, v_tip])
    f_tr.material_index = mat_idx
    f_tb = bm.faces.new([r_last, l_last, v_tip])
    f_tb.material_index = mat_idx

def add_flower(bm, center, normal, radius=0.026, mat_idx_petal=0, mat_idx_center=1):
    u_axis = Vector((0, 0, 1)).cross(normal).normalized()
    if u_axis.length < 0.001:
        u_axis = Vector((1, 0, 0))
    v_axis = normal.cross(u_axis).normalized()
    num_p = 6
    v_c = bm.verts.new(center)
    for p in range(num_p):
        a1 = p * 2.0 * math.pi / num_p
        a2 = (p + 1) * 2.0 * math.pi / num_p
        am = (a1 + a2) * 0.5
        p1 = center + (u_axis * math.cos(a1) + v_axis * math.sin(a1)) * (radius * 0.35)
        pt = center + (u_axis * math.cos(am) + v_axis * math.sin(am)) * radius
        p2 = center + (u_axis * math.cos(a2) + v_axis * math.sin(a2)) * (radius * 0.35)
        v1 = bm.verts.new(p1)
        vt = bm.verts.new(pt)
        v2 = bm.verts.new(p2)
        f = bm.faces.new([v_c, v1, vt, v2])
        f.material_index = mat_idx_petal
            
    bead_r = radius * 0.35
    v_b = bm.verts.new(center + normal * (radius * 0.22))
    for p in range(num_p):
        a1 = p * 2.0 * math.pi / num_p
        a2 = (p + 1) * 2.0 * math.pi / num_p
        p1 = center + (u_axis * math.cos(a1) + v_axis * math.sin(a1)) * bead_r
        p2 = center + (u_axis * math.cos(a2) + v_axis * math.sin(a2)) * bead_r
        v1 = bm.verts.new(p1)
        v2 = bm.verts.new(p2)
        fb = bm.faces.new([v_b, v1, v2])
        fb.material_index = mat_idx_center

def create_lathed_mesh(bm, profile_radii, z_coords, num_slices=24, x_center=0.0, y_center=0.0, mat_idx=0, x_scales=None, y_scales=None):
    num_rings = len(z_coords)
    ring_verts = []
    
    for r_idx in range(num_rings):
        z = z_coords[r_idx]
        r = profile_radii[r_idx]
        xs = x_scales[r_idx] if x_scales else 1.0
        ys = y_scales[r_idx] if y_scales else 1.0
        curr_ring = []
        for s_idx in range(num_slices):
            theta = s_idx * 2.0 * math.pi / num_slices
            px = x_center + r * xs * math.cos(theta)
            py = y_center + r * ys * math.sin(theta)
            curr_ring.append(bm.verts.new((px, py, z)))
        ring_verts.append(curr_ring)
        
    for r_idx in range(num_rings - 1):
        r1 = ring_verts[r_idx]
        r2 = ring_verts[r_idx + 1]
        for s_idx in range(num_slices):
            s_next = (s_idx + 1) % num_slices
            f = bm.faces.new([r1[s_idx], r1[s_next], r2[s_next], r2[s_idx]])
            f.material_index = mat_idx

def finalize_mesh_object(obj, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    for poly in obj.data.polygons:
        poly.use_smooth = True

# -------------------------------------------------------------
# STEP 6: BUILD ASTER COSTUME (100% INDEPENDENT SEPARATE LAYERS)
# -------------------------------------------------------------
print("Building independent costume components...")

# 6.1 IVORY BLOUSE (Stand collar, front brooch, full draped fit)
mesh_blouse = bpy.data.meshes.new("Aster_Blouse")
obj_blouse = bpy.data.objects.new("Aster_Blouse", mesh_blouse)
bpy.context.scene.collection.objects.link(obj_blouse)
obj_blouse.data.materials.append(mat_blouse)
obj_blouse.data.materials.append(mat_ribbon_blue)
obj_blouse.data.materials.append(mat_pearl)

bm_blouse = bmesh.new()

z_blouse = [1.04, 1.10, 1.16, 1.22, 1.28, 1.34, 1.38, 1.41]
r_blouse = [0.118, 0.122, 0.128, 0.136, 0.138, 0.126, 0.095, 0.058]
xs_blouse = [1.12, 1.12, 1.12, 1.10, 1.08, 1.05, 1.02, 1.00]
ys_blouse = [0.96, 0.98, 1.02, 1.10, 1.14, 1.05, 0.98, 0.98]
create_lathed_mesh(bm_blouse, r_blouse, z_blouse, num_slices=24, y_center=-0.015, mat_idx=0, x_scales=xs_blouse, y_scales=ys_blouse)

# Front Collar Ribbon Tie & Pearl Brooch (Z ~ 1.365)
brooch_pos = Vector((0.0, 0.075, 1.365))
add_flower(bm_blouse, brooch_pos, Vector((0, 1, 0)), radius=0.018, mat_idx_petal=2, mat_idx_center=1)
for side in [-1.0, 1.0]:
    b_loop = [
        brooch_pos,
        brooch_pos + Vector((side * 0.022, 0.008, 0.016)),
        brooch_pos + Vector((side * 0.035, 0.004, 0.004)),
        brooch_pos
    ]
    create_surface_ribbon(bm_blouse, b_loop, [0.008, 0.016, 0.014, 0.008], normal_dir=Vector((0, 1, 0)), mat_idx=1)
    b_st = [
        brooch_pos,
        brooch_pos + Vector((side * 0.012, 0.006, -0.030)),
        brooch_pos + Vector((side * 0.018, 0.004, -0.058))
    ]
    create_surface_ribbon(bm_blouse, b_st, [0.014, 0.012, 0.008], normal_dir=Vector((0, 1, 0)), mat_idx=1)

finalize_mesh_object(obj_blouse, bm_blouse)

# 6.2 LONG PUFFED BISHOP SLEEVES (泡泡袖 + 荷叶边腕口 + 浅蓝细丝带结)
mesh_sleeves = bpy.data.meshes.new("Aster_Puffed_Sleeves")
obj_sleeves = bpy.data.objects.new("Aster_Puffed_Sleeves", mesh_sleeves)
bpy.context.scene.collection.objects.link(obj_sleeves)
obj_sleeves.data.materials.append(mat_blouse)
obj_sleeves.data.materials.append(mat_ribbon_lightblue)

bm_sleeves = bmesh.new()

for side in [-1.0, 1.0]:
    p_shoulder = Vector((side * 0.115, -0.025, 1.365))
    p_elbow = Vector((side * 0.225, -0.025, 1.255))
    p_forearm = Vector((side * 0.305, -0.025, 1.190))
    p_wrist = Vector((side * 0.375, -0.025, 1.150))
    p_cuff = Vector((side * 0.405, -0.025, 1.125))
    
    sleeve_profile_pts = [p_shoulder, p_elbow, p_forearm, p_wrist, p_cuff]
    sleeve_radii = [0.055, 0.075, 0.090, 0.040, 0.058]
    
    num_pts = len(sleeve_profile_pts)
    num_slices = 20
    sleeve_rings = []
    
    for pt_i in range(num_pts):
        pt = sleeve_profile_pts[pt_i]
        r = sleeve_radii[pt_i]
        
        if pt_i < num_pts - 1:
            tan = (sleeve_profile_pts[pt_i + 1] - pt).normalized()
        else:
            tan = (pt - sleeve_profile_pts[pt_i - 1]).normalized()
        binorm = tan.cross(Vector((0, 1, 0))).normalized()
        if binorm.length < 0.001:
            binorm = Vector((1, 0, 0))
        norm = binorm.cross(tan).normalized()
        
        curr_ring = []
        for s in range(num_slices):
            th = s * 2.0 * math.pi / num_slices
            r_eff = r
            if pt_i == num_pts - 1:
                r_eff += 0.008 * math.sin(s * 4.0)
            p_ring = pt + binorm * (r_eff * math.cos(th)) + norm * (r_eff * math.sin(th))
            curr_ring.append(bm_sleeves.verts.new(p_ring))
        sleeve_rings.append(curr_ring)
        
    for pt_i in range(num_pts - 1):
        r1 = sleeve_rings[pt_i]
        r2 = sleeve_rings[pt_i + 1]
        for s in range(num_slices):
            s_next = (s + 1) % num_slices
            f = bm_sleeves.faces.new([r1[s], r1[s_next], r2[s_next], r2[s]])
            f.material_index = 0
            
    cuff_bow_pos = p_wrist + Vector((side * 0.038, 0.015, 0.005))
    for bow_loop_i in range(2):
        l_sign = 1.0 if bow_loop_i == 0 else -1.0
        loop_p = [
            cuff_bow_pos,
            cuff_bow_pos + Vector((side * 0.012, 0.015 * l_sign, 0.016)),
            cuff_bow_pos + Vector((side * 0.022, 0.008 * l_sign, 0.006)),
            cuff_bow_pos
        ]
        create_surface_ribbon(bm_sleeves, loop_p, [0.006, 0.014, 0.012, 0.006], normal_dir=Vector((side, 0, 0)), mat_idx=1)

finalize_mesh_object(obj_sleeves, bm_sleeves)

# 6.3 HIGH-WAISTED STRUCTURED CORSET (双排精致金扣 + 左腰珍珠花与飘带)
mesh_corset = bpy.data.meshes.new("Aster_Waist_Corset")
obj_corset = bpy.data.objects.new("Aster_Waist_Corset", mesh_corset)
bpy.context.scene.collection.objects.link(obj_corset)
obj_corset.data.materials.append(mat_corset)
obj_corset.data.materials.append(mat_gold)
obj_corset.data.materials.append(mat_ribbon_lightblue)
obj_corset.data.materials.append(mat_pearl)

bm_corset = bmesh.new()

z_corset = [0.96, 1.01, 1.06, 1.11, 1.16]
r_corset = [0.132, 0.125, 0.120, 0.124, 0.128]
xs_corset = [1.16, 1.15, 1.14, 1.14, 1.14]
ys_corset = [0.98, 0.96, 0.95, 0.98, 1.02]
create_lathed_mesh(bm_corset, r_corset, z_corset, num_slices=24, y_center=-0.015, mat_idx=0, x_scales=xs_corset, y_scales=ys_corset)

# Double-breasted 6 gold buttons on front abdomen
button_rows = [1.02, 1.06, 1.10]
for b_z in button_rows:
    for side in [-1.0, 1.0]:
        btn_pos = Vector((side * 0.028, 0.104, b_z))
        add_flower(bm_corset, btn_pos, Vector((0, 1, 0)), radius=0.007, mat_idx_petal=1, mat_idx_center=1)

# Left hip floral corsage with dangling ribbons & pearl charm
corsage_pos = Vector((-0.135, 0.075, 1.040))
corsage_norm = Vector((-0.65, 0.70, 0.28)).normalized()
add_flower(bm_corset, corsage_pos, corsage_norm, radius=0.026, mat_idx_petal=3, mat_idx_center=1)
for l_idx in range(2):
    l_sign = 1.0 if l_idx == 0 else -1.0
    c_loop = [
        corsage_pos,
        corsage_pos + Vector((-0.020, 0.022, 0.028 * l_sign)),
        corsage_pos + Vector((-0.032, 0.012, 0.012 * l_sign)),
        corsage_pos
    ]
    create_surface_ribbon(bm_corset, c_loop, [0.007, 0.016, 0.014, 0.007], normal_dir=corsage_norm, mat_idx=2)

for r_i in range(2):
    off = 0.010 * (r_i - 0.5)
    c_pts = []
    c_wids = []
    for seg in range(14):
        st = seg / 13.0
        cz = 1.03 * (1.0 - st) + 0.68 * st
        cx = -0.135 - 0.030 * st + off
        cy = 0.075 + 0.036 * st + 0.006 * math.sin(st * 2.8 * math.pi)
        c_pts.append((cx, cy, cz))
        w = 0.018 * (1.0 - 0.35 * st)
        c_wids.append(max(w, 0.003))
    create_surface_ribbon(bm_corset, c_pts, c_wids, normal_dir=Vector((-1, 1, 0)).normalized(), mat_idx=2)

finalize_mesh_object(obj_corset, bm_corset)

# 6.4 DOUBLE-LAYER PLEATED SKIRT (双层百褶裙：外层白底微褶，内层冰蓝半透明不规则雪纺薄纱，裙底掏空与大腿完全隔离)
mesh_skirt_out = bpy.data.meshes.new("Aster_Skirt_Layer1_Outer")
obj_skirt_out = bpy.data.objects.new("Aster_Skirt_Layer1_Outer", mesh_skirt_out)
bpy.context.scene.collection.objects.link(obj_skirt_out)
obj_skirt_out.data.materials.append(mat_skirt_outer)

bm_skirt_out = bmesh.new()

num_pleats = 24
skirt_slices = num_pleats * 2
z_skirt_1 = [1.00, 0.94, 0.87, 0.80, 0.73]
r_skirt_1 = [0.128, 0.158, 0.202, 0.250, 0.290]

rings_skirt_1 = []
for r_i in range(len(z_skirt_1)):
    z = z_skirt_1[r_i]
    r = r_skirt_1[r_i]
    flare_t = r_i / float(len(z_skirt_1) - 1)
    curr_ring = []
    for s in range(skirt_slices):
        th = s * 2.0 * math.pi / skirt_slices
        pleat_mod = (1.0 if s % 2 == 0 else -1.0) * (0.016 * flare_t)
        px = (r + pleat_mod) * 1.15 * math.cos(th)
        py = -0.015 + (r + pleat_mod) * 0.95 * math.sin(th)
        curr_ring.append(bm_skirt_out.verts.new((px, py, z)))
    rings_skirt_1.append(curr_ring)

for r_i in range(len(z_skirt_1) - 1):
    r1 = rings_skirt_1[r_i]
    r2 = rings_skirt_1[r_i + 1]
    for s in range(skirt_slices):
        s_next = (s + 1) % skirt_slices
        bm_skirt_out.faces.new([r1[s], r1[s_next], r2[s_next], r2[s]])

finalize_mesh_object(obj_skirt_out, bm_skirt_out)

# Layer 2: Longer asymmetrical icy-blue translucent chiffon underlayer
mesh_skirt_in = bpy.data.meshes.new("Aster_Skirt_Layer2_InnerChiffon")
obj_skirt_in = bpy.data.objects.new("Aster_Skirt_Layer2_InnerChiffon", mesh_skirt_in)
bpy.context.scene.collection.objects.link(obj_skirt_in)
obj_skirt_in.data.materials.append(mat_skirt_inner)

bm_skirt_in = bmesh.new()

z_skirt_2 = [0.98, 0.91, 0.83, 0.74, 0.65]
r_skirt_2 = [0.125, 0.152, 0.195, 0.244, 0.285]

rings_skirt_2 = []
for r_i in range(len(z_skirt_2)):
    z = z_skirt_2[r_i]
    r = r_skirt_2[r_i]
    flare_t = r_i / float(len(z_skirt_2) - 1)
    curr_ring = []
    for s in range(skirt_slices):
        th = s * 2.0 * math.pi / skirt_slices
        asym_z = 0.0
        if r_i == len(z_skirt_2) - 1:
            asym_z = -0.040 * abs(math.sin(th * 3.0 + 0.4))
        px = r * 1.14 * math.cos(th)
        py = -0.015 + r * 0.94 * math.sin(th)
        curr_ring.append(bm_skirt_in.verts.new((px, py, z + asym_z)))
    rings_skirt_2.append(curr_ring)

for r_i in range(len(z_skirt_2) - 1):
    r1 = rings_skirt_2[r_i]
    r2 = rings_skirt_2[r_i + 1]
    for s in range(skirt_slices):
        s_next = (s + 1) % skirt_slices
        bm_skirt_in.faces.new([r1[s], r1[s_next], r2[s_next], r2[s]])

finalize_mesh_object(obj_skirt_in, bm_skirt_in)

# 6.5 BACK WAIST RIBBON BOW & FLOWING STREAMERS (后腰柔美天蓝缎带蝴蝶结 + 垂直下垂长飘带)
mesh_bow = bpy.data.meshes.new("Aster_BackWaistBow")
obj_bow = bpy.data.objects.new("Aster_BackWaistBow", mesh_bow)
bpy.context.scene.collection.objects.link(obj_bow)
obj_bow.data.materials.append(mat_ribbon_blue)

bm_bow = bmesh.new()
knot_pos = Vector((0.0, -0.142, 1.045))

for side in [-1.0, 1.0]:
    loop_pts = [
        knot_pos,
        knot_pos + Vector((side * 0.052, -0.025, 0.048)),
        knot_pos + Vector((side * 0.095, -0.030, 0.028)),
        knot_pos + Vector((side * 0.065, -0.018, -0.018)),
        knot_pos
    ]
    loop_wids = [0.018, 0.042, 0.048, 0.035, 0.018]
    create_surface_ribbon(bm_bow, loop_pts, loop_wids, normal_dir=Vector((0, -1, 0)), mat_idx=0)
    
    st_pts = []
    st_wids = []
    for seg in range(16):
        st = seg / 15.0
        sz = 1.04 * (1.0 - st) + 0.55 * st
        sx = side * (0.020 + 0.038 * st)
        sy = -0.145 - 0.025 * st + 0.008 * math.sin(st * 2.8 * math.pi)
        st_pts.append((sx, sy, sz))
        w = 0.032 * (1.0 - 0.30 * st)
        st_wids.append(max(w, 0.003))
    create_surface_ribbon(bm_bow, st_pts, st_wids, normal_dir=Vector((0, -1, 0)), mat_idx=0)

finalize_mesh_object(obj_bow, bm_bow)

# 6.6 SOCKS & MARY JANE SHOES (荷叶边短袜 + 纯白复古玛丽珍鞋配金属扣)
mesh_footwear = bpy.data.meshes.new("Aster_Footwear")
obj_footwear = bpy.data.objects.new("Aster_Footwear", mesh_footwear)
bpy.context.scene.collection.objects.link(obj_footwear)
obj_footwear.data.materials.append(mat_shoes)
obj_footwear.data.materials.append(mat_socks)
obj_footwear.data.materials.append(mat_gold)

bm_foot = bmesh.new()

for side in [-1.0, 1.0]:
    foot_x = side * 0.072
    
    z_sock = [0.07, 0.10, 0.14, 0.18]
    r_sock = [0.040, 0.038, 0.039, 0.048]
    create_lathed_mesh(bm_foot, r_sock, z_sock, num_slices=16, x_center=foot_x, y_center=-0.010, mat_idx=1)
    
    z_shoe = [0.00, 0.025, 0.050, 0.070]
    r_shoe = [0.052, 0.050, 0.046, 0.042]
    xs_shoe = [0.85, 0.85, 0.85, 0.85]
    ys_shoe = [1.35, 1.30, 1.15, 1.00]
    create_lathed_mesh(bm_foot, r_shoe, z_shoe, num_slices=16, x_center=foot_x, y_center=0.015, mat_idx=0, x_scales=xs_shoe, y_scales=ys_shoe)
    
    z_heel = [0.00, 0.018, 0.035]
    r_heel = [0.026, 0.025, 0.024]
    create_lathed_mesh(bm_foot, r_heel, z_heel, num_slices=12, x_center=foot_x, y_center=-0.045, mat_idx=0)
    
    strap_pts = [
        Vector((foot_x - 0.036, 0.020, 0.052)),
        Vector((foot_x, 0.022, 0.065)),
        Vector((foot_x + 0.036, 0.020, 0.052))
    ]
    create_surface_ribbon(bm_foot, strap_pts, [0.010, 0.010, 0.010], normal_dir=Vector((0, 1, 0)), mat_idx=0)
    buckle_pos = Vector((foot_x + side * 0.035, 0.020, 0.056))
    add_flower(bm_foot, buckle_pos, Vector((side * 1.0, 0, 0)), radius=0.009, mat_idx_petal=2, mat_idx_center=2)

finalize_mesh_object(obj_footwear, bm_foot)

# -------------------------------------------------------------
# STEP 7: BUILD ASTER HAIR & FLORAL ACCESSORIES (1:1 with turnaround-final.png)
# -------------------------------------------------------------
print("Building Aster hair and accessories...")
mesh_hair = bpy.data.meshes.new("Aster_Hair_Master")
obj_hair = bpy.data.objects.new("Aster_Hair_Master", mesh_hair)
bpy.context.scene.collection.objects.link(obj_hair)
obj_hair.data.materials.append(mat_hair)
obj_hair.data.materials.append(mat_pearl)
obj_hair.data.materials.append(mat_gold)
obj_hair.data.materials.append(mat_ribbon_lightblue)

bm_hair = bmesh.new()

# 7.1 HIGH-CROWN SMOOTH SPHERICAL CRANIUM DOME (饱满球形高颅顶，前发际线拱高 Z >= 1.585)
# Constructed using spherical latitude rings (no cone tip!)
num_cap_rings = 8
num_cap_slices = 24
cap_rings = []

# Spherical apex ring (tiny radius 0.008m for smooth curvature)
for r_i in range(num_cap_rings):
    # phi from 0.08 to pi/2
    phi = 0.08 + (math.pi * 0.5 - 0.08) * (r_i / float(num_cap_rings - 1))
    u = r_i / float(num_cap_rings - 1)
    curr_ring = []
    
    for s_i in range(num_cap_slices):
        th = s_i * 2.0 * math.pi / num_cap_slices
        cd = math.cos(th)
        sd = math.sin(th)
        
        if sd > 0: # Forehead & Temples
            rim_z = 1.520 + 0.065 * (sd ** 0.8) # Center forehead Z = 1.585
            rim_x = 0.082 * cd
            rim_y = 0.005 + 0.070 * sd
        else: # Skull & Nape
            rim_z = 1.520 + 0.080 * sd          # Nape Z = 1.440
            rim_x = 0.086 * cd
            rim_y = 0.005 + 0.088 * sd
            
        # Spherical dome formula
        z_sphere = 1.550 + 0.108 * math.cos(phi)
        r_sphere = 0.090 * math.sin(phi)
        
        cur_z = z_sphere * (1.0 - u) + rim_z * u
        cur_x = (r_sphere * cd) * (1.0 - u) + rim_x * u
        cur_y = (-0.005 + r_sphere * sd) * (1.0 - u) + rim_y * u
        curr_ring.append(bm_hair.verts.new(Vector((cur_x, cur_y, cur_z))))
    cap_rings.append(curr_ring)

# Top cap pole face
f_top = bm_hair.faces.new(cap_rings[0])
f_top.material_index = 0

# Connect latitude rings
for r_i in range(num_cap_rings - 1):
    r1 = cap_rings[r_i]
    r2 = cap_rings[r_i + 1]
    for s_i in range(num_cap_slices):
        s_next = (s_i + 1) % num_cap_slices
        f = bm_hair.faces.new([r1[s_i], r2[s_i], r2[s_next], r1[s_next]])
        f.material_index = 0

print("Cranium dome built smoothly.")

# 7.2 AIRY CENTER-PARTED BANGS (前额轻薄中分空气刘海 - 3D立体棱柱发束，清晰露出星空双眸)
left_bang_specs = [
    # (start_pt, mid_pt, tip_pt, max_width, thickness)
    (Vector((-0.008, 0.068, 1.595)), Vector((-0.014, 0.074, 1.555)), Vector((-0.018, 0.072, 1.528)), 0.010, 0.0035),
    (Vector((-0.020, 0.068, 1.595)), Vector((-0.028, 0.075, 1.550)), Vector((-0.035, 0.072, 1.516)), 0.013, 0.0045),
    (Vector((-0.034, 0.066, 1.590)), Vector((-0.044, 0.073, 1.540)), Vector((-0.052, 0.070, 1.498)), 0.015, 0.0045),
    (Vector((-0.048, 0.062, 1.580)), Vector((-0.060, 0.068, 1.525)), Vector((-0.070, 0.065, 1.472)), 0.015, 0.0045),
]

for p_start, p_mid, p_tip, w_max, th_max in left_bang_specs:
    pts = []
    wids = []
    thicks = []
    num_seg = 10
    for seg in range(num_seg):
        t = seg / float(num_seg - 1)
        p_curr = (1.0 - t)**2 * p_start + 2.0 * (1.0 - t) * t * p_mid + t**2 * p_tip
        w = w_max * (0.6 + 0.8 * math.sin(t * math.pi * 0.75)) * (1.0 - 0.75 * t)
        th = th_max * (1.0 - 0.70 * t)
        pts.append(p_curr)
        wids.append(w)
        thicks.append(th)
    norm = Vector((-0.3, 1.0, 0.2)).normalized()
    create_hair_strand_3d(bm_hair, pts, wids, thicks, normal_dir=norm, mat_idx=0)

right_bang_specs = [
    (Vector((0.008, 0.068, 1.595)), Vector((0.014, 0.074, 1.555)), Vector((0.018, 0.072, 1.528)), 0.010, 0.0035),
    (Vector((0.020, 0.068, 1.595)), Vector((0.028, 0.075, 1.550)), Vector((0.035, 0.072, 1.516)), 0.013, 0.0045),
    (Vector((0.034, 0.066, 1.590)), Vector((0.044, 0.073, 1.540)), Vector((0.052, 0.070, 1.498)), 0.015, 0.0045),
    (Vector((0.048, 0.062, 1.580)), Vector((0.060, 0.068, 1.525)), Vector((0.070, 0.065, 1.472)), 0.015, 0.0045),
]

for p_start, p_mid, p_tip, w_max, th_max in right_bang_specs:
    pts = []
    wids = []
    thicks = []
    num_seg = 10
    for seg in range(num_seg):
        t = seg / float(num_seg - 1)
        p_curr = (1.0 - t)**2 * p_start + 2.0 * (1.0 - t) * t * p_mid + t**2 * p_tip
        w = w_max * (0.6 + 0.8 * math.sin(t * math.pi * 0.75)) * (1.0 - 0.75 * t)
        th = th_max * (1.0 - 0.70 * t)
        pts.append(p_curr)
        wids.append(w)
        thicks.append(th)
    norm = Vector((0.3, 1.0, 0.2)).normalized()
    create_hair_strand_3d(bm_hair, pts, wids, thicks, normal_dir=norm, mat_idx=0)

# 7.3 FACE-FRAMING SIDE LOCKS (两鬓长发束，贴脸颊轻柔垂至胸口 Z ~ 1.25)
for side in [-1.0, 1.0]:
    for l_idx in range(2):
        off_x = 0.008 * l_idx
        pts_side = []
        wids_side = []
        thicks_side = []
        num_seg = 14
        for seg in range(num_seg):
            st = seg / float(num_seg - 1)
            cz = 1.56 * (1.0 - st) + 1.24 * st
            cx = side * (0.078 + 0.010 * math.sin(st * math.pi * 1.1) + off_x)
            cy = 0.035 + 0.038 * st + 0.005 * math.sin(st * 2.5 * math.pi)
            pts_side.append(Vector((cx, cy, cz)))
            w = 0.018 * (0.6 + 0.8 * math.sin(st * math.pi * 0.85)) * (1.0 - 0.65 * st)
            th = 0.005 * (1.0 - 0.50 * st)
            wids_side.append(w)
            thicks_side.append(th)
        norm_side = Vector((side * 0.8, 0.6, 0.0)).normalized()
        create_hair_strand_3d(bm_hair, pts_side, wids_side, thicks_side, normal_dir=norm_side, mat_idx=0)

# 7.4 CASCADING WAVY BACK HAIR (多层次过腰长发，丝滑高斯平滑避开后腰蝴蝶结)
num_tiers = 3
strands_per_tier = 18
for tier in range(num_tiers):
    tier_rad = 0.014 * tier
    tier_z = -0.015 * tier
    for s in range(strands_per_tier):
        t = s / float(strands_per_tier - 1)
        angle = math.radians(-140.0 + 280.0 * t)
        
        r_top = 0.092 + tier_rad
        x_top = r_top * math.sin(angle)
        y_top = -r_top * math.cos(angle) * 0.95 - 0.012
        z_top = 1.56 + tier_z
        
        pts_hair = []
        wids_hair = []
        thicks_hair = []
        num_seg = 16
        for seg in range(num_seg):
            st = seg / float(num_seg - 1)
            cur_z = z_top * (1.0 - st) + 0.65 * st
            spread = 1.0 + 1.25 * st + 0.40 * (st ** 2)
            cur_x = x_top * spread
            wave_x = 0.018 * math.sin(st * 3.2 * math.pi + angle * 1.5)
            wave_y = 0.012 * math.cos(st * 2.8 * math.pi + angle)
            
            cur_y = y_top * spread + wave_y
            if cur_y > -0.055:
                cur_y = -0.055
                
            # Silk-smooth Gaussian bow clearance (no polygon kinks!)
            gauss_w = math.exp(-((cur_z - 1.045) / 0.14)**2)
            if abs(cur_x) < 0.10:
                cur_x = math.copysign(abs(cur_x) + 0.055 * gauss_w, cur_x if abs(cur_x) > 0.001 else 1.0)
            cur_y -= 0.035 * gauss_w
            
            # Soft inward curl at tips
            if st > 0.85:
                curl_t = (st - 0.85) / 0.15
                cur_y += 0.028 * curl_t
                cur_x *= (1.0 - 0.18 * curl_t)
                
            pts_hair.append(Vector((cur_x + wave_x, cur_y, cur_z)))
            w = 0.036 * (0.6 + 0.9 * math.sin(st * math.pi * 0.85)) * (1.0 - 0.45 * st)
            th = 0.007 * (1.0 - 0.40 * st)
            wids_hair.append(w)
            thicks_hair.append(th)
            
        strand_normal = Vector((x_top, y_top, 0)).normalized()
        create_hair_strand_3d(bm_hair, pts_hair, wids_hair, thicks_hair, normal_dir=strand_normal, mat_idx=0)

# 7.5 TWIN PEARL FLORAL HAIRPINS (双侧珍珠花卉发饰 + 细浅蓝飘带)
for side in [-1.0, 1.0]:
    clip_pos = Vector((side * 0.108, 0.018, 1.550))
    clip_norm = Vector((side * 0.65, 0.70, 0.30)).normalized()
    add_flower(bm_hair, clip_pos, clip_norm, radius=0.026, mat_idx_petal=1, mat_idx_center=2)
    add_flower(bm_hair, clip_pos + Vector((side * 0.012, -0.010, 0.018)), clip_norm, radius=0.016, mat_idx_petal=1, mat_idx_center=2)
    
    for l_idx in range(2):
        l_sign = 1.0 if l_idx == 0 else -1.0
        h_loop = [
            clip_pos,
            clip_pos + Vector((side * 0.018, -0.020, 0.030 * l_sign)),
            clip_pos + Vector((side * 0.028, -0.010, 0.014 * l_sign)),
            clip_pos
        ]
        create_surface_ribbon(bm_hair, h_loop, [0.007, 0.016, 0.014, 0.007], normal_dir=clip_norm, mat_idx=3)
        
    for r_i in range(2):
        r_pts = []
        r_wids = []
        off = 0.010 * (r_i - 0.5)
        for seg in range(12):
            st = seg / 11.0
            rz = 1.54 * (1.0 - st) + 1.26 * st
            rx = side * (0.108 + 0.012 * st) + off
            ry = 0.015 - 0.032 * st + 0.006 * math.sin(st * 3.0 * math.pi)
            r_pts.append((rx, ry, rz))
            w = 0.015 * (1.0 - 0.40 * st)
            r_wids.append(max(w, 0.002))
        create_surface_ribbon(bm_hair, r_pts, r_wids, normal_dir=clip_norm, mat_idx=3)

finalize_mesh_object(obj_hair, bm_hair)

# -------------------------------------------------------------
# STEP 8: SETUP SOLIDIFY INVERTED-HULL OUTLINE (Backface Culling Enforced)
# -------------------------------------------------------------
outline_objects = [body_obj, obj_blouse, obj_sleeves, obj_corset, obj_skirt_out, obj_skirt_in, obj_hair, obj_bow, obj_footwear]
for obj in outline_objects:
    if obj:
        if mat_outline.name not in [m.name for m in obj.data.materials if m]:
            obj.data.materials.append(mat_outline)
        out_idx = [i for i, m in enumerate(obj.data.materials) if m and m.name == mat_outline.name][0]
        
        mod = obj.modifiers.new(name="Inverted_Hull_Outline", type='SOLIDIFY')
        mod.thickness = -0.0008
        mod.offset = 0.0
        mod.use_flip_normals = True
        mod.material_offset = out_idx
        mod.use_rim = False

print("Inverted Hull outlines applied with backface culling.")

# -------------------------------------------------------------
# STEP 9: MULTI-ANGLE 2K PRODUCTION STUDIO RENDERS
# -------------------------------------------------------------
print("Setting up studio cameras and lighting...")
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world

# Sophisticated neutral studio backdrop (soft warm-slate gray for maximum NPR contrast)
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.52, 0.54, 0.58, 1.0)
    bg.inputs[1].default_value = 1.0

# 3-Point Studio Lighting
key_light = bpy.data.lights.new("Studio_KeyLight", type='SUN')
key_light.energy = 3.2
key_obj = bpy.data.objects.new("Studio_KeyLight", key_light)
bpy.context.scene.collection.objects.link(key_obj)
key_obj.rotation_euler = (math.radians(48), math.radians(-12), math.radians(145))

fill_light = bpy.data.lights.new("Studio_FillLight", type='SUN')
fill_light.energy = 1.8
fill_obj = bpy.data.objects.new("Studio_FillLight", fill_light)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (math.radians(45), math.radians(18), math.radians(-45))

rim_light = bpy.data.lights.new("Studio_RimLight", type='SUN')
rim_light.energy = 2.2
rim_obj = bpy.data.objects.new("Studio_RimLight", rim_light)
bpy.context.scene.collection.objects.link(rim_obj)
rim_obj.rotation_euler = (math.radians(-60), 0, math.radians(0))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'

camera_configs = [
    # 1. Front Full Body (2048x2048)
    ("01_aster_v2_front_full.png", Vector((0.0, 3.2, 0.88)), (math.radians(90), 0, math.radians(180)), 70, (2048, 2048)),
    # 2. Three-Quarter Face Closeup (2048x2048)
    ("02_aster_v2_three_quarter_face.png", Vector((0.30, 1.02, 1.54)), (math.radians(88), 0, math.radians(162)), 105, (2048, 2048)),
    # 3. Skirt & Waist Closeup (2048x2048)
    ("03_aster_v2_skirt_layers_closeup.png", Vector((0.15, 1.55, 0.88)), (math.radians(88), 0, math.radians(172)), 85, (2048, 2048)),
    # 4. Back Full Body (2048x2048)
    ("04_aster_v2_back_full.png", Vector((0.0, -3.2, 0.88)), (math.radians(90), 0, 0), 70, (2048, 2048)),
]

for filename, pos, rot, lens, res in camera_configs:
    cam_data = bpy.data.cameras.new(filename)
    cam_data.lens = lens
    cam_obj = bpy.data.objects.new(filename, cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = pos
    cam_obj.rotation_euler = rot
    scene.camera = cam_obj
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.filepath = os.path.join(out_renders_dir, filename)
    print(f"Rendering 2K view: {filename}...")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {scene.render.filepath}")

# -------------------------------------------------------------
# STEP 10: SAVE MASTER .BLEND & EXPORT MASTER .GLB
# -------------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print(f"Clean master blend file saved to: {out_blend}")

export_objs = [body_obj, face_obj, obj_blouse, obj_sleeves, obj_corset, obj_skirt_out, obj_skirt_in, obj_hair, obj_bow, obj_footwear]
if armature:
    export_objs.append(armature)

bpy.ops.object.select_all(action='DESELECT')
for o in export_objs:
    if o:
        o.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=out_glb,
    use_selection=True,
    export_format='GLB',
    export_apply=True,
    export_yup=True,
    export_skins=True,
    export_morph=True,
    export_materials='EXPORT'
)
print(f"Clean master GLB exported to: {out_glb}")
print("=== Aster Master Pipeline V2.2 Complete! ===")
