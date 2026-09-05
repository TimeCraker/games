import bpy, addon_utils, bmesh
addon_utils.enable('mmd_tools')

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

shenhe_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\shenhe\shenhe.pmx'
bpy.ops.mmd_tools.import_model(filepath=shenhe_path, types={'MESH'})
obj = bpy.data.objects['shenhe_mesh']

for mat_idx in [10]:
    mat_name = obj.data.materials[mat_idx].name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    faces = [f for f in bm.faces if f.material_index == mat_idx]
    
    visited = set()
    islands = []
    for f in faces:
        if f in visited: continue
        isl, q = [], [f]
        visited.add(f)
        while q:
            curr = q.pop()
            isl.append(curr)
            for e in curr.edges:
                for lf in e.link_faces:
                    if lf.material_index == mat_idx and lf not in visited:
                        visited.add(lf); q.append(lf)
        islands.append(isl)
        
    print(f"SHENHE MAT {mat_idx} ({mat_name}): {len(faces)} faces, {len(islands)} islands")
    for i, isl in enumerate(islands):
        if len(isl) > 5:
            min_x = min(v.co.x for f in isl for v in f.verts)
            max_x = max(v.co.x for f in isl for v in f.verts)
            min_y = min(v.co.y for f in isl for v in f.verts)
            max_y = max(v.co.y for f in isl for v in f.verts)
            min_z = min(v.co.z for f in isl for v in f.verts)
            max_z = max(v.co.z for f in isl for v in f.verts)
            print(f"  Island {i}: {len(isl)} faces | X: [{min_x:.3f}, {max_x:.3f}], Y: [{min_y:.3f}, {max_y:.3f}], Z: [{min_z:.3f}, {max_z:.3f}]")
