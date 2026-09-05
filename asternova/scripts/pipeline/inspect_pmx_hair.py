import bpy
import sys
import os

# Add mmd_tools
import addon_utils
addon_utils.enable('mmd_tools')

models_to_check = [
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\shenhe\shenhe.pmx",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\layla.pmx",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\furina\furina_1.pmx",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\ganyu\ganyu.pmx",
    r"c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\ayaka\ayaka.pmx",
]

for model_path in models_to_check:
    name = os.path.basename(os.path.dirname(model_path))
    print(f"\n==================== {name.upper()} ====================")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

    bpy.ops.mmd_tools.import_model(filepath=model_path, types={'MESH'})

    
    # Find mesh objects
    mesh_objs = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    for obj in mesh_objs:
        print(f"Object: {obj.name}, verts: {len(obj.data.vertices)}, polys: {len(obj.data.polygons)}")
        for idx, mat in enumerate(obj.data.materials):
            if mat:
                # count polygons with this material
                count = sum(1 for p in obj.data.polygons if p.material_index == idx)
                print(f"  Mat {idx}: '{mat.name}' -> {count} faces")
