"""Render/export the authored purple source. Never rebuild or save over it.

Run in Blender: --background --python purple_rework.py -- --blend FILE
               --output DIRECTORY --mode render|export
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

VIEWS = {
    'front': ((0, -4, .88), (0, 0, .88), 1.97),
    'left': ((-4, 0, .88), (0, 0, .88), 1.97),
    'right': ((4, 0, .88), (0, 0, .88), 1.97),
    'back': ((0, 4, .88), (0, 0, .88), 1.97),
    'threequarter': ((2.0, -4, .92), (0, 0, .88), 1.97),
    'head': ((0, -4, 1.56), (0, 0, 1.56), .55),
    'head_side': ((4, 0, 1.56), (0, 0, 1.56), .55),
    'clay': ((0, -4, .88), (0, 0, .88), 1.97),
}


def visible_work():
    collection = bpy.data.collections.get('WORK_Purple')
    if not collection:
        raise RuntimeError('Missing authored WORK_Purple collection')
    return [o for o in collection.all_objects
            if not o.hide_render and o.type in {'MESH', 'CURVE'}]


def render(output):
    scene = bpy.context.scene
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    neutral = bpy.data.materials.new('Purple_Review_Neutral')
    neutral.use_nodes = True
    shader = neutral.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.5, .53, .58, 1)
    shader.inputs['Roughness'].default_value = .75
    for name, (location, target, scale) in VIEWS.items():
        camera = scene.camera
        camera.location = location
        camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = scale
        bpy.context.view_layer.material_override = neutral if name == 'clay' else None
        scene.render.filepath = str(output / (name + '.png'))
        bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None


def export(output):
    authored = visible_work()
    export_collection = bpy.data.collections.new('EXPORT_Purple')
    bpy.context.scene.collection.children.link(export_collection)
    copies = []
    graph = bpy.context.evaluated_depsgraph_get()
    for original in authored:
        evaluated = original.evaluated_get(graph)
        mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=graph)
        obj = bpy.data.objects.new(original.name, mesh)
        export_collection.objects.link(obj)
        obj.matrix_world = original.matrix_world.copy()
        copies.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in copies:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    path = output / 'purple_static.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB',
                              use_selection=True, export_animations=False,
                              export_image_format='AUTO')
    return {'path': str(path), 'meshes': len(copies),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blend', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['render', 'export'], required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    args.blend = args.blend.resolve()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    before = hashlib.sha256(args.blend.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    result = export(args.output) if args.mode == 'export' else render(args.output)
    unchanged = before == hashlib.sha256(args.blend.read_bytes()).hexdigest()
    if not unchanged:
        raise RuntimeError('Authored source changed during read-only operation')
    report = {'source': str(args.blend.resolve()), 'source_sha256': before,
              'source_unchanged': unchanged, 'operation': args.mode,
              'art_approved': False, 'result': result,
              'views': VIEWS if args.mode == 'render' else None}
    (args.output / ('purple_' + args.mode + '_report.json')).write_text(
        json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
