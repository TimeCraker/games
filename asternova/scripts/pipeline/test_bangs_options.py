import bpy, addon_utils, bmesh, os, math

addon_utils.enable('mmd_tools')

# Open milestone 1 model
m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'
bpy.ops.wm.open_mainfile(filepath=m1_blend)

head_obj = bpy.data.objects['Head_Base']
# Head bbox
min_z = min(v.co.z for v in head_obj.data.vertices)
max_z = max(v.co.z for v in head_obj.data.vertices)
print(f"Milestone 1 Head_Base Z: [{min_z:.3f}, {max_z:.3f}]")

# Let's test Layla's bangs (Mat 10) on Head_Base
layla_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\layla.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=layla_path, types={'MESH'})
new_objs = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH']
layla_obj = new_objs[0]
print(f"Imported layla mesh: {layla_obj.name}")

# Keep only Mat 10 (bangs) and Mat 13 (side locks)
keep_mats = [10, 13]
bm = bmesh.new()
bm.from_mesh(layla_obj.data)
del_faces = [f for f in bm.faces if f.material_index not in keep_mats]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(layla_obj.data)
bm.free()
layla_obj.data.update()
layla_obj.name = "Layla_Hair_Front_Side"

# Setup camera for face closeup
cam = bpy.data.objects.get('Camera')
if not cam:
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, -0.65, 1.48)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 70

# Setup light
light = bpy.data.objects.get('KeyLight')
if not light:
    light_data = bpy.data.lights.new('KeyLight', type='SUN')
    light = bpy.data.objects.new('KeyLight', light_data)
    bpy.context.scene.collection.objects.link(light)
light.location = (0.5, -1.0, 2.0)
light.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
light.data.energy = 3.0

out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews'
os.makedirs(out_dir, exist_ok=True)
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_layla_bangs.png')
bpy.ops.render.render(write_still=True)
print("TEST LAYLA BANGS RENDERED")
