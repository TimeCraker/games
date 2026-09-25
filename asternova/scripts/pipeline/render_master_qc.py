# -*- coding: utf-8 -*-
"""Master QC Renderer for Aster Skinning Perfection."""
import bpy
import math
import os
from mathutils import Vector

# Hide weapons for character body QC
for o in bpy.data.objects:
    if "Katana" in o.name or "Blade" in o.name or "Scabbard" in o.name:
        o.hide_render = True
        o.hide_viewport = True

# Execute master skinning
exec(open("scripts/pipeline/apply_master_skinning.py", encoding="utf-8").read())

# Set up render engine
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1440

QC_DIR = os.path.abspath("art/models/work/_master_qc")
os.makedirs(QC_DIR, exist_ok=True)

cam_obj = bpy.data.objects.get("QC_Cam_Obj")
if not cam_obj:
    cam_data = bpy.data.cameras.new("QC_Cam")
    cam_data.lens = 65
    cam_obj = bpy.data.objects.new("QC_Cam_Obj", cam_data)
    scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

arm = bpy.data.objects["Aster_Armature"]
body = bpy.data.objects["Aster_Body"]

def render_shot(filename, cam_pos, cam_target):
    cam_obj.location = cam_pos
    direction = (cam_target - cam_pos).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(QC_DIR, filename)
    bpy.ops.render.render(write_still=True)
    print(f"[QC] Rendered {filename}")

def clear_pose():
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.context.view_layer.update()

# --- PART 1: REST POSE ---
clear_pose()
render_shot("01_rest_front.png", Vector((0.0, 2.5, 0.95)), Vector((0.0, 0.0, 0.95)))
render_shot("02_rest_skirt_closeup.png", Vector((0.0, 1.4, 0.68)), Vector((0.0, 0.0, 0.68)))
render_shot("03_rest_right_arm.png", Vector((0.6, 1.2, 1.15)), Vector((0.25, 0.0, 1.15)))
render_shot("04_rest_left_arm.png", Vector((-0.6, 1.2, 1.15)), Vector((-0.25, 0.0, 1.15)))
render_shot("05_rest_shoes.png", Vector((0.0, 1.1, 0.15)), Vector((0.0, 0.0, 0.10)))

# --- PART 2: IDLE POSE ---
clear_pose()
pb_r_arm = arm.pose.bones.get("R_Upperarm")
pb_l_arm = arm.pose.bones.get("L_Upperarm")
pb_r_fa = arm.pose.bones.get("R_Forearm")
pb_l_fa = arm.pose.bones.get("L_Forearm")

# Lower arms naturally by side
if pb_r_arm:
    pb_r_arm.rotation_mode = 'XYZ'
    pb_r_arm.rotation_euler = (math.radians(-5), math.radians(0), math.radians(55))
if pb_l_arm:
    pb_l_arm.rotation_mode = 'XYZ'
    pb_l_arm.rotation_euler = (math.radians(-5), math.radians(0), math.radians(-55))
if pb_r_fa:
    pb_r_fa.rotation_mode = 'XYZ'
    pb_r_fa.rotation_euler = (math.radians(10), math.radians(-5), math.radians(0))
if pb_l_fa:
    pb_l_fa.rotation_mode = 'XYZ'
    pb_l_fa.rotation_euler = (math.radians(10), math.radians(5), math.radians(0))

bpy.context.view_layer.update()

render_shot("06_idle_front.png", Vector((0.0, 2.5, 0.95)), Vector((0.0, 0.0, 0.95)))
render_shot("07_idle_skirt_closeup.png", Vector((0.0, 1.4, 0.68)), Vector((0.0, 0.0, 0.68)))
render_shot("08_idle_right_arm.png", Vector((0.5, 1.2, 1.05)), Vector((0.15, 0.0, 1.00)))
render_shot("09_idle_left_arm.png", Vector((-0.5, 1.2, 1.05)), Vector((-0.15, 0.0, 1.00)))

# --- PART 3: STRIDE / WALK POSE ---
clear_pose()
pb_l_thigh = arm.pose.bones.get("L_Thigh")
pb_r_thigh = arm.pose.bones.get("R_Thigh")
pb_l_calf = arm.pose.bones.get("L_Calf")
pb_r_calf = arm.pose.bones.get("R_Calf")

if pb_l_thigh:
    pb_l_thigh.rotation_mode = 'XYZ'
    pb_l_thigh.rotation_euler = (math.radians(28), 0, 0)
if pb_r_thigh:
    pb_r_thigh.rotation_mode = 'XYZ'
    pb_r_thigh.rotation_euler = (math.radians(-28), 0, 0)
if pb_l_calf:
    pb_l_calf.rotation_mode = 'XYZ'
    pb_l_calf.rotation_euler = (math.radians(-15), 0, 0)
if pb_r_calf:
    pb_r_calf.rotation_mode = 'XYZ'
    pb_r_calf.rotation_euler = (math.radians(25), 0, 0)

if pb_r_arm:
    pb_r_arm.rotation_mode = 'XYZ'
    pb_r_arm.rotation_euler = (math.radians(25), 0, math.radians(35))
if pb_l_arm:
    pb_l_arm.rotation_mode = 'XYZ'
    pb_l_arm.rotation_euler = (math.radians(-25), 0, math.radians(-35))

bpy.context.view_layer.update()

render_shot("10_stride_side_left.png", Vector((-2.2, 0.0, 0.85)), Vector((0.0, 0.0, 0.85)))
render_shot("11_stride_side_right.png", Vector((2.2, 0.0, 0.85)), Vector((0.0, 0.0, 0.85)))
render_shot("12_stride_front.png", Vector((0.0, 2.2, 0.85)), Vector((0.0, 0.0, 0.85)))
render_shot("13_stride_skirt_closeup.png", Vector((0.0, 1.4, 0.68)), Vector((0.0, 0.0, 0.68)))
render_shot("14_stride_shoes_closeup.png", Vector((0.0, 1.2, 0.20)), Vector((0.0, 0.0, 0.15)))

clear_pose()
print("ALL_MASTER_QC_RENDERS_DONE")
