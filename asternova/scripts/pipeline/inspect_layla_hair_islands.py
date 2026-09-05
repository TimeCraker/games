import bpy, addon_utils, bmesh, os
addon_utils.enable('mmd_tools')

# Let's inspect Layla Mat 10 (髮) and Mat 13 (侧髮) islands
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

layla_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\layla\layla.pmx'
bpy.ops.mmd_tools.import_model(filepath=layla_path, types={'MESH'})
obj = bpy.data.objects['layla_mesh']

for mat_idx in [10]:
    mat_name = obj.data.materials[mat_idx].name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    faces = [f for f in bm.faces if f.material_index == mat_idx]
    
    # find islands
    visited = set()
    islands = []
    for f in faces:
        if f in visited:
            continue
        island = []
        queue = [f]
        visited.add(f)
        while queue:
            curr = queue.pop()
            island.append(curr)
            for edge in curr.edges:
                for linked_face in edge.link_faces:
                    if linked_face.material_index == mat_idx and linked_face not in visited:
                        visited.add(linked_face)
                        queue.append(linked_face)
        islands.append(island)
    
    print(f"\nMaterial {mat_idx} ({mat_name}): {len(faces)} faces, {len(islands)} islands")
    for i, isl in enumerate(islands):
        min_x = min(v.co.x for f in isl for v in f.verts)
        max_x = max(v.co.x for f in isl for v in f.verts)
        min_y = min(v.co.y for f in isl for v in f.verts)
        max_y = max(v.co.y for f in isl for v in f.verts)
        min_z = min(v.co.z for f in isl for v in f.verts)
        max_z = max(v.co.z for f in isl for v in f.verts)
        print(f"  Island {i}: {len(isl)} faces | X: [{min_x:.3f}, {max_x:.3f}], Y: [{min_y:.3f}, {max_y:.3f}], Z: [{min_z:.3f}, {max_z:.3f}]")
