import bpy

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

keqing_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\keqing.blend'
with bpy.data.libraries.load(keqing_blend) as (data_from, data_to):
    data_to.objects = ['KeQing_mesh']

for o in data_to.objects:
    bpy.context.scene.collection.objects.link(o)

kq = bpy.data.objects['KeQing_mesh']
print("=== KEQING MATERIALS ===")
for i, m in enumerate(kq.data.materials):
    count = sum(1 for p in kq.data.polygons if p.material_index == i)
    print(f"Mat {i}: '{m.name}' -> {count} faces")
