import bpy

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

print("=== ASTER_MODEL.GLB OBJECTS ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mats = [m.name for m in obj.data.materials if m]
        bbox = [f"{min(v.co[i] for v in obj.data.vertices):.2f}..{max(v.co[i] for v in obj.data.vertices):.2f}" for i in range(3)]
        print(f"Mesh: {obj.name}, verts: {len(obj.data.vertices)}, polys: {len(obj.data.polygons)}, BBox: X[{bbox[0]}], Y[{bbox[1]}], Z[{bbox[2]}], Mats: {mats}")
