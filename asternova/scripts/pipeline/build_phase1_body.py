# AsterNova - Phase 1: 8.5 Head-to-Body Commercial Quad Base Mesh Pipeline
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

print("=== Starting Phase 1: 8.5 Head-to-Body Body & Face Alignment ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

models_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster"
src_vrm = os.path.join(models_dir, "aster_base.vrm")
out_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\aster_v2"
os.makedirs(out_dir, exist_ok=True)

bpy.ops.import_scene.gltf(filepath=src_vrm)

armature = bpy.data.objects.get("Armature")
body_obj = bpy.data.objects.get("Body")
face_obj = bpy.data.objects.get("Face")

for name in ["Icosphere", "secondary"]:
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

# 1. Convert Body & Face to Quad Topology
for obj in [body_obj, face_obj]:
    if obj:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.tris_convert_to_quads()
        bpy.ops.object.mode_set(mode='OBJECT')
        quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
        tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
        total = quads + tris
        pct = quads / total * 100.0 if total > 0 else 0.0
        print(f"{obj.name} topology: {quads} quads, {tris} tris (quad ratio: {pct:.1f}%)")

# 2. Body & Face 8.5 Proportional Retargeting
# Target: 1.650m total height, 8.50 heads -> Head height = 0.1941m
head_scale = 0.194 / 0.250  # ~0.776
head_z_center_orig = 1.460
head_z_center_target = 1.553

bm_face = bmesh.new()
bm_face.from_mesh(face_obj.data)

for v in bm_face.verts:
    rx = v.co.x * head_scale
    ry = (v.co.y - 0.015) * head_scale + 0.010
    rz = (v.co.z - head_z_center_orig) * head_scale + head_z_center_target
    
    # Refine V-line jaw & pointed chin
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
        
        # Shoulder tapering & sloping
        if t > 0.75:
            shoulder_t = (t - 0.75) / 0.25
            x *= (1.0 - 0.08 * shoulder_t)
            z -= 0.012 * shoulder_t * (abs(x) / 0.16)
            
        # Slender waist at t ~ 0.42 (Z ~ 1.05)
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
        
    v.co.x = x
    v.co.y = y
    v.co.z = z

bm_body.to_mesh(body_obj.data)
bm_body.free()
body_obj.data.update()

# Retarget Armature Bones if armature exists
if armature:
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    for b in armature.data.edit_bones:
        for end in ['head', 'tail']:
            vec = getattr(b, end)
            oz = vec.z
            if oz >= 1.330:
                vec.x *= head_scale
                vec.y = (vec.y - 0.015) * head_scale + 0.010
                vec.z = (oz - head_z_center_orig) * head_scale + head_z_center_target
            elif oz >= 1.260:
                t = (oz - 1.260) / (1.330 - 1.260)
                vec.z = 1.370 + t * (1.456 - 1.370)
                vec.x *= 0.82
                vec.y *= 0.82
            elif oz >= 0.770:
                t = (oz - 0.770) / (1.260 - 0.770)
                vec.z = 0.840 + t * (1.370 - 0.840)
            else:
                t = oz / 0.770
                if t < 0.54:
                    vec.z = (t / 0.54) * 0.460
                else:
                    vec.z = 0.460 + ((t - 0.54) / 0.46) * (0.840 - 0.460)
    bpy.ops.object.mode_set(mode='OBJECT')

min_z = min(v.co.z for v in body_obj.data.vertices)
max_z = max(max(v.co.z for v in body_obj.data.vertices), max(v.co.z for v in face_obj.data.vertices))
head_min = min(v.co.z for v in face_obj.data.vertices)
head_h = max_z - head_min
ratio = (max_z - min_z) / head_h
print(f"Calibrated Height: {max_z - min_z:.3f}m, Head Height: {head_h:.3f}m -> Ratio: {ratio:.2f} Heads!")

# Save Phase 1 Base Blend
out_blend = os.path.join(models_dir, "aster_phase1_calibrated_base.blend")
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("Phase 1 Base saved to:", out_blend)

# -------------------------------------------------------------
# 3. Setup Camera & Studio Lighting for Inspection
# -------------------------------------------------------------
cam_data = bpy.data.cameras.new("Cam_Front")
cam_data.lens = 85
cam_obj = bpy.data.objects.new("Cam_Front", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = Vector((0.0, -3.4, 0.90))
cam_obj.rotation_euler = (math.radians(90), 0, 0)
bpy.context.scene.camera = cam_obj

world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.92, 0.93, 0.95, 1.0)
    bg.inputs[1].default_value = 1.0

sun_data = bpy.data.lights.new("Sun", type='SUN')
sun_data.energy = 2.5
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), math.radians(15), math.radians(-30))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 2048
scene.render.filepath = os.path.join(out_dir, "00_phase1_body_front_check.png")
bpy.ops.render.render(write_still=True)
print("Phase 1 Preview rendered to:", scene.render.filepath)
