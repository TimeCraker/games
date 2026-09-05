import bpy, bmesh

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

hair_obj = None
for obj in bpy.data.objects:
    if 'hair' in obj.name.lower() and obj.type == 'MESH' and len(obj.data.polygons) > 1000:
        hair_obj = obj
        break

if hair_obj:
    print(f"Found hair mesh: {hair_obj.name}, verts: {len(hair_obj.data.vertices)}, polys: {len(hair_obj.data.polygons)}")
    bm = bmesh.new()
    bm.from_mesh(hair_obj.data)
    
    # Check islands
    islands = []
    visited = set()
    for f in bm.faces:
        if f in visited: continue
        isl, q = [], [f]
        visited.add(f)
        while q:
            curr = q.pop()
            isl.append(curr)
            for e in curr.edges:
                for lf in e.link_faces:
                    if lf not in visited:
                        visited.add(lf); q.append(lf)
        islands.append(isl)
    
    print(f"Total hair islands: {len(islands)}")
    # Sort by face count desc
    islands.sort(key=lambda x: len(x), reverse=True)
    for i in range(min(15, len(islands))):
        isl = islands[i]
        min_x = min(v.co.x for f in isl for v in f.verts)
        max_x = max(v.co.x for f in isl for v in f.verts)
        min_y = min(v.co.y for f in isl for v in f.verts)
        max_y = max(v.co.y for f in isl for v in f.verts)
        min_z = min(v.co.z for f in isl for v in f.verts)
        max_z = max(v.co.z for f in isl for v in f.verts)
        print(f"  Island {i}: {len(isl)} faces | X: [{min_x:.3f}, {max_x:.3f}], Y: [{min_y:.3f}, {max_y:.3f}], Z: [{min_z:.3f}, {max_z:.3f}]")
