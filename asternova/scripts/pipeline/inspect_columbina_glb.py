import bpy

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

c = bpy.data.objects.get('columbina.001')
if c:
    print(f"columbina.001: verts={len(c.data.vertices)}, polys={len(c.data.polygons)}, mats={[m.name for m in c.data.materials]}")
    bbox = [f"{min(v.co[i] for v in c.data.vertices):.2f}..{max(v.co[i] for v in c.data.vertices):.2f}" for i in range(3)]
    print(f"BBox: X[{bbox[0]}], Y[{bbox[1]}], Z[{bbox[2]}]")
