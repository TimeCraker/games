import bpy, addon_utils, bmesh

addon_utils.enable('mmd_tools')

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

columbina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\columbina\columbina.pmx'
bpy.ops.mmd_tools.import_model(filepath=columbina_path, types={'MESH'})
c_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

print("=== COLUMBINA MATERIALS ===")
for i, m in enumerate(c_obj.data.materials):
    count = sum(1 for p in c_obj.data.polygons if p.material_index == i)
    print(f"Mat {i}: '{m.name}' -> {count} faces")
