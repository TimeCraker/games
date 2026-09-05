import bpy, addon_utils, bmesh, os, math

addon_utils.enable('mmd_tools')

m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'
bpy.ops.wm.open_mainfile(filepath=m1_blend)

existing_objs = set(bpy.data.objects)
kokomi_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\kokomi\kokomi.pmx'
bpy.ops.mmd_tools.import_model(filepath=kokomi_path, types={'MESH'})
k_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

# Keep only Mat 12 (前髪) and Mat 13 (侧髪)
bm = bmesh.new()
bm.from_mesh(k_obj.data)
del_faces = [f for f in bm.faces if f.material_index not in [12, 13]]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(k_obj.data)
bm.free()
k_obj.data.update()

# Align Kokomi's hair to Head_Base
head_obj = bpy.data.objects['Head_Base']
# Check head top Z and hair top Z
head_max_z = max(v.co.z for v in head_obj.data.vertices)
hair_max_z = max(v.co.z for v in k_obj.data.vertices)
print(f"Head max Z: {head_max_z:.3f}, Hair max Z: {hair_max_z:.3f}")

# Setup camera
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
bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_kokomi_bangs.png')
bpy.ops.render.render(write_still=True)
print("TEST KOKOMI BANGS RENDERED")
