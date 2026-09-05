import bpy

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

proxy = bpy.data.objects.get('Hair_Sphere_Normal_Proxy')
if proxy:
    print(f"Proxy found: loc={proxy.location}, scale={proxy.scale}, bbox={[f'{min(v.co[i] for v in proxy.data.vertices):.2f}..{max(v.co[i] for v in proxy.data.vertices):.2f}' for i in range(3)]}")
    # World bbox
    mw = proxy.matrix_world
    world_coords = [mw @ v.co for v in proxy.data.vertices]
    print(f"World BBox: X[{min(v.x for v in world_coords):.2f}..{max(v.x for v in world_coords):.2f}], Y[{min(v.y for v in world_coords):.2f}..{max(v.y for v in world_coords):.2f}], Z[{min(v.z for v in world_coords):.2f}..{max(v.z for v in world_coords):.2f}]")
