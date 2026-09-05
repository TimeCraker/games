import bpy, addon_utils

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# 1. Inspect keqing.blend
keqing_blend = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\keqing.blend'
print("=== KEQING OBJECTS ===")
with bpy.data.libraries.load(keqing_blend) as (data_from, data_to):
    print("Objects in keqing.blend:", [n for n in data_from.objects if 'hair' in n.lower() or 'mesh' in n.lower() or 'head' in n.lower()])

# 2. Inspect kokomi.pmx
addon_utils.enable('mmd_tools')
kokomi_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\kokomi\kokomi.pmx'
bpy.ops.mmd_tools.import_model(filepath=kokomi_path, types={'MESH'})
objs = [o for o in bpy.data.objects if o.type == 'MESH']
if objs:
    k_obj = objs[0]
    print(f"\n=== KOKOMI MATERIALS ({k_obj.name}) ===")
    for i, m in enumerate(k_obj.data.materials):
        count = sum(1 for p in k_obj.data.polygons if p.material_index == i)
        print(f"Mat {i}: '{m.name}' -> {count} faces")
