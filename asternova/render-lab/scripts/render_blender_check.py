import bpy
import math

print("=== Rendering Blender Inspection Views ===")

bpy.ops.wm.read_factory_settings(use_empty=True)
glb_path = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb"
bpy.ops.import_scene.gltf(filepath=glb_path)

# Workbench or EEVEE
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 768
scene.render.resolution_y = 1024
scene.render.image_settings.file_format = 'PNG'

# World lighting
world = bpy.data.worlds.new("StudioWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.95, 0.95, 0.96, 1.0)
bg.inputs['Strength'].default_value = 1.0

# Add Key Light
light_data = bpy.data.lights.new(name="KeyLight", type='SUN')
light_data.energy = 2.5
light_data.color = (1.0, 0.98, 0.96)
light_obj = bpy.data.objects.new(name="KeyLight", object_data=light_data)
scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(35), math.radians(15), math.radians(25))

# Camera setup
cam_data = bpy.data.cameras.new('RenderCam')
cam_obj = bpy.data.objects.new('RenderCam', cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

views = [
    ("check_front.png", (0, 2.5, 0.95), (math.radians(90), 0, math.radians(180))),
    ("check_back.png", (0, -2.5, 0.95), (math.radians(90), 0, 0)),
    ("check_side.png", (-2.5, 0, 0.95), (math.radians(90), 0, math.radians(-90))),
    ("check_closeup.png", (0, 1.15, 1.38), (math.radians(90), 0, math.radians(180)))
]

out_dir = r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews"

for fname, loc, rot in views:
    cam_obj.location = loc
    cam_obj.rotation_euler = rot
    scene.render.filepath = f"{out_dir}\\{fname}"
    bpy.ops.render.render(write_still=True)
    print(f"Saved {fname}")

print("Blender inspection renders finished.")
