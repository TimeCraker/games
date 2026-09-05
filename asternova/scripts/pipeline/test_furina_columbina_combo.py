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

bm = bmesh.new()
bm.from_mesh(c_obj.data)
del_faces = [f for f in bm.faces if f.material_index != 8]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(c_obj.data)
bm.free()
c_obj.data.update()
c_obj.name = "Hair_Layer3_ColumbinaBack"

# 2. Import Furina Front Bangs & Crown (Layer 1 & Layer 2)
furina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx'
existing_objs = set(bpy.data.objects)
bpy.ops.mmd_tools.import_model(filepath=furina_path, types={'MESH'})
f_obj = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH'][0]

bm = bmesh.new()
bm.from_mesh(f_obj.data)
# Keep only Mat 10
del_faces = [f for f in bm.faces if f.material_index != 10]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')

# Find islands in Furina hair
visited = set()
islands = []
for f in bm.faces:
    if f in visited: continue
    isl, q = [], [f]
    visited.add(f)
    while q:
        curr = q.pop()
        isl.append(curr)
        for e in curr.edges:
            for lf in e.link_faces:
                if lf not in visited:
                    visited.add(lf); q.append(lf)
    islands.append(isl)

# Filter out:
# 1) Furina's giant ahoge (Z max > 1.60 and Y < -0.02)
# 2) Furina's back short curls (Y > 0.05)
del_islands = []
for isl in islands:
    max_z = max(v.co.z for f in isl for v in f.verts)
    min_y = min(v.co.y for f in isl for v in f.verts)
    max_y = max(v.co.y for f in isl for v in f.verts)
    center_y = sum(v.co.y for f in isl for v in f.verts) / sum(len(f.verts) for f in isl)
    # Ahoge check:
    if max_z > 1.60:
        del_islands.append(isl)
    # Back short curls check:
    elif center_y > 0.045:
        del_islands.append(isl)

del_faces = [f for isl in del_islands for f in isl]
bmesh.ops.delete(bm, geom=del_faces, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(f_obj.data)
bm.free()
f_obj.data.update()
f_obj.location.z = 0.012
f_obj.name = "Hair_Layer1_2_FurinaFront"

# 3. Import Aster Accessories & Ahoge
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

for o in new_objs:
    base_name = o.name.split('.')[0]
    if base_name not in keep_acc_names and o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)

# Adjust Aster Ahoge to plant on top of head (head top is ~1.54)
ahoge = bpy.data.objects.get('Aster_Ahoge')
if ahoge:
    # shift ahoge slightly so root enters skull
    ahoge.location.z -= 0.07
    ahoge.location.y -= 0.02

# Hide proxy from render
proxy = bpy.data.objects.get('Hair_Sphere_Normal_Proxy')
if proxy:
    proxy.hide_render = True

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
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_furina_columbina_front.png')
bpy.ops.render.render(write_still=True)
print("COMBO FRONT RENDERED")

# Render Back View
cam.location = (0, 0.9, 1.35)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_furina_columbina_back.png')
bpy.ops.render.render(write_still=True)
print("COMBO BACK RENDERED")

# Render 3/4 Side View
cam.location = (-0.55, -0.55, 1.48)
cam.rotation_euler = (math.radians(90), 0, math.radians(-45))
bpy.context.scene.render.filepath = os.path.join(out_dir, 'test_furina_columbina_three_quarter.png')
bpy.ops.render.render(write_still=True)
print("COMBO 3/4 RENDERED")
