import bpy, os, math
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_phase1_calibrated_base.blend")

out_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews\aster_v2"

# 1. Position front camera (looking towards -Y at front of character)
cam = bpy.data.objects.get("Cam_Front")
if not cam:
    cam_data = bpy.data.cameras.new("Cam_Front")
    cam = bpy.data.objects.new("Cam_Front", cam_data)
    bpy.context.scene.collection.objects.link(cam)
cam.data.lens = 85
cam.location = Vector((0.0, 3.4, 0.90))
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
bpy.context.scene.camera = cam

# 2. Lighting for front
sun = bpy.data.objects.get("Sun")
if sun:
    sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(150))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 2048
scene.render.filepath = os.path.join(out_dir, "00_phase1_body_front_true.png")
bpy.ops.render.render(write_still=True)
print("Front rendered to:", scene.render.filepath)

# 3. Also render 3/4 Face Closeup
cam_face_data = bpy.data.cameras.new("Cam_Face")
cam_face = bpy.data.objects.new("Cam_Face", cam_face_data)
bpy.context.scene.collection.objects.link(cam_face)
cam_face_data.lens = 105
# 3/4 angle: X=0.35, Y=1.1, Z=1.55
cam_face.location = Vector((0.35, 1.1, 1.55))
cam_face.rotation_euler = (math.radians(88), 0, math.radians(162))
scene.camera = cam_face
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = os.path.join(out_dir, "00_phase1_face_three_quarter.png")
bpy.ops.render.render(write_still=True)
print("Face rendered to:", scene.render.filepath)
