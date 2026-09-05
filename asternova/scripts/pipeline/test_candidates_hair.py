import bpy, addon_utils, bmesh, os, math

addon_utils.enable('mmd_tools')

candidates = [
    ('furina', r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx', [10]),
    ('shenhe', r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\shenhe\shenhe.pmx', [10]),
    ('ganyu', r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\ganyu\ganyu.pmx', [10]),
]

out_dir = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\render_previews'
m1_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\art\models\aster_milestone1_head_body.blend'

for name, path, hair_mats in candidates:
    bpy.ops.wm.open_mainfile(filepath=m1_blend)
    existing_objs = set(bpy.data.objects)
    bpy.ops.mmd_tools.import_model(filepath=path, types={'MESH'})
    new_objs = [o for o in bpy.data.objects if o not in existing_objs and o.type == 'MESH']
    hair_obj = new_objs[0]
    
    # Keep only hair mats
    bm = bmesh.new()
    bm.from_mesh(hair_obj.data)
    del_faces = [f for f in bm.faces if f.material_index not in hair_mats]
    bmesh.ops.delete(bm, geom=del_faces, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(hair_obj.data)
    bm.free()
    hair_obj.data.update()
    
    # Check head alignment and scale
    # Milestone 1 head is around Z ~ 1.45, Y ~ 0.0, X ~ 0.0
    head_obj = bpy.data.objects['Head_Base']
    h_min_z = min(v.co.z for v in head_obj.data.vertices)
    h_max_z = max(v.co.z for v in head_obj.data.vertices)
    hair_min_z = min(v.co.z for v in hair_obj.data.vertices)
    hair_max_z = max(v.co.z for v in hair_obj.data.vertices)
    print(f"[{name}] Head Z: [{h_min_z:.2f}, {h_max_z:.2f}], Hair Z: [{hair_min_z:.2f}, {hair_max_z:.2f}]")
    
    # Adjust position if needed (e.g. Shenhe is taller)
    # Head center Z ~ 1.435
    # If hair max Z is significantly different, shift it
    delta_z = 1.54 - hair_max_z
    hair_obj.location.z += delta_z
    
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

    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.render.filepath = os.path.join(out_dir, f'test_{name}_hair.png')
    bpy.ops.render.render(write_still=True)
    print(f"TEST {name} HAIR RENDERED")
