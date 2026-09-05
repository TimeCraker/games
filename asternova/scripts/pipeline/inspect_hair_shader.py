import bpy

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

glb_path = r'c:\Users\TimeCraker\Desktop\my-workspace\games\asternova\render-lab\models\aster\aster_model.glb'
bpy.ops.import_scene.gltf(filepath=glb_path)

mat = bpy.data.materials.get('Aster_Cel_Hair_v2')
if not mat:
    mat = [m for m in bpy.data.materials if 'hair' in m.name.lower()][0]

print(f"Material: {mat.name}, use_nodes={mat.use_nodes}")
if mat.use_nodes:
    for node in mat.node_tree.nodes:
        print(f"  Node: {node.name} ({node.type})")
        if node.type == 'BSDF_PRINCIPLED':
            print(f"    Base Color: {node.inputs['Base Color'].default_value[:]}")
            print(f"    Roughness: {node.inputs['Roughness'].default_value}")
