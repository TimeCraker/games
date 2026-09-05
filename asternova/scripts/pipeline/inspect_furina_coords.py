import bpy, addon_utils

addon_utils.enable('mmd_tools')
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

furina_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx'
bpy.ops.mmd_tools.import_model(filepath=furina_path, types={'MESH'})
f_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

print("=== FURINA MESH ===")
for i, m in enumerate(f_obj.data.materials):
    if '颜' in m.name or '髮' in m.name:
        verts = [v.co for p in f_obj.data.polygons if p.material_index == i for v in [f_obj.data.vertices[vi] for vi in p.vertices]]
        min_z = min(v.z for v in verts)
        max_z = max(v.z for v in verts)
        count = sum(1 for p in f_obj.data.polygons if p.material_index == i)
        print(f"Mat {i}: '{m.name}' -> {count} faces, Z: [{min_z:.3f}, {max_z:.3f}]")
