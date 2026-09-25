# -*- coding: utf-8 -*-
"""Verification renderer for targeted surgical cleanup on Aster model."""
import bpy
import math
import os
from mathutils import Vector

# Execute the targeted cleanup
exec(open("scripts/pipeline/test_surgical_cleanup.py", encoding="utf-8").read())

# Set up render engine
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1440

QC_DIR = os.path.abspath("art/models/work/_surgical_qc")
os.makedirs(QC_DIR, exist_ok=True)

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

# Pose Mode
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.context.view_layer.update()

# --- PART 1: REST POSE RENDERS ---
# Shot 1: Rest Pose Full Front
render_shot("01_rest_front.png", Vector((0.0, 2.5, 0.95)), Vector((0.0, 0.0, 0.95)))

# Shot 2: Skirt Front Closeup (Rest)
render_shot("02_skirt_front_closeup.png", Vector((0.0, 1.4, 0.68)), Vector((0.0, 0.0, 0.68)))

# Shot 3: Right Arm Closeup
render_shot("03_right_arm_closeup.png", Vector((0.6, 1.2, 1.15)), Vector((0.25, 0.0, 1.15)))

# Shot 4: Left Arm Closeup
render_shot("04_left_arm_closeup.png", Vector((-0.6, 1.2, 1.15)), Vector((-0.25, 0.0, 1.15)))

# Shot 5: Shoes Closeup (Rest)
render_shot("05_rest_shoes_closeup.png", Vector((0.0, 1.1, 0.15)), Vector((0.0, 0.0, 0.10)))

# --- PART 2: STRIDE POSE RENDERS ---
pb_l_thigh = arm.pose.bones.get("L_Thigh")
pb_r_thigh = arm.pose.bones.get("R_Thigh")
pb_l_calf = arm.pose.bones.get("L_Calf")
pb_r_calf = arm.pose.bones.get("R_Calf")
pb_r_arm = arm.pose.bones.get("R_Upperarm")
pb_l_arm = arm.pose.bones.get("L_Upperarm")

# Apply Stride
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
    pb_r_arm.rotation_euler = (math.radians(25), 0, math.radians(-10))
if pb_l_arm:
    pb_l_arm.rotation_mode = 'XYZ'
    pb_l_arm.rotation_euler = (math.radians(-25), 0, math.radians(10))

bpy.context.view_layer.update()

# Shot 6: Stride Side View (Left)
render_shot("06_stride_side_left.png", Vector((-2.2, 0.0, 0.85)), Vector((0.0, 0.0, 0.85)))

# Shot 7: Stride Side View (Right)
render_shot("07_stride_side_right.png", Vector((2.2, 0.0, 0.85)), Vector((0.0, 0.0, 0.85)))

# Shot 8: Stride Front View
render_shot("08_stride_front.png", Vector((0.0, 2.2, 0.85)), Vector((0.0, 0.0, 0.85)))

# Shot 9: Stride Skirt Front Closeup
render_shot("09_stride_skirt_closeup.png", Vector((0.0, 1.4, 0.68)), Vector((0.0, 0.0, 0.68)))

# Shot 10: Stride Shoes Closeup
render_shot("10_stride_shoes_closeup.png", Vector((0.0, 1.2, 0.20)), Vector((0.0, 0.0, 0.15)))

print("ALL_QC_RENDERS_DONE")
