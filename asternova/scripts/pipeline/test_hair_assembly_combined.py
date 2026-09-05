import bpy, addon_utils, bmesh, os, math

addon_utils.enable('mmd_tools')

m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'
bpy.ops.wm.open_mainfile(filepath=m1_blend)

head_obj = bpy.data.objects['Head_Base']

# 1. Import Columbina Back Hair
columbina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=columbina_path, types={'MESH'})
c_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

# In Columbina, keep Mat 8 (髮 - back long hair flow)
bm = bmesh.new()
bm.from_mesh(c_obj.data)
del_faces = [f for f in bm.faces if f.material_index != 8]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(c_obj.data)
bm.free()
c_obj.data.update()
c_obj.name = "Hair_Layer3_Back"

# 2. Import Kokomi Front Hair & Side Hair
kokomi_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\kokomi\kokomi.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=kokomi_path, types={'MESH'})
k_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

# In Kokomi, keep Mat 12 (前髪) and Mat 13 (侧髪)
bm = bmesh.new()
bm.from_mesh(k_obj.data)
del_faces = [f for f in bm.faces if f.material_index not in [12, 13]]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(k_obj.data)
bm.free()
k_obj.data.update()
k_obj.name = "Hair_Layer1_2_FrontSide"

# 3. Import Aster Accessories & Ahoge from aster_model.glb
glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
existing_objs = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb_path)
new_objs = [o for o in bpy.data.objects if o not in existing_objs]

keep_acc_names = [
    'Aster_Ahoge', 'Aster_HairFlower', 'Aster_HairFlower_Center',
    'Aster_HairLoop_1', 'Aster_HairLoop_2',
    'Aster_HairStreamer_1', 'Aster_HairStreamer_2',
    'Aster_RightHairPin', 'Aster_RightHairPin_Center',
    'Hair_Sphere_Normal_Proxy'
]

acc_objs = []
for o in new_objs:
    base_name = o.name.split('.')[0]
    if base_name in keep_acc_names:
        acc_objs.append(o)
    else:
        if o.type == 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)

proxy = bpy.data.objects.get('Hair_Sphere_Normal_Proxy')
if proxy:
    proxy.hide_render = True
    print("Hair_Sphere_Normal_Proxy hide_render set to True")


# Setup Camera for front view
cam = bpy.data.objects.get('Camera')
if not cam:
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, -0.75, 1.45)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 65

# Setup Key Light
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
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_hair_front_combined.png')
bpy.ops.render.render(write_still=True)
print("FRONT COMBINED RENDERED")

# Render Back View
cam.location = (0, 0.9, 1.35)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_hair_back_combined.png')
bpy.ops.render.render(write_still=True)
print("BACK COMBINED RENDERED")
