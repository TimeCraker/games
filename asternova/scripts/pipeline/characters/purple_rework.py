"""Render/export the authored purple source. Never rebuild or save over it.

Run in Blender: --background --python purple_rework.py -- --blend FILE
               --output DIRECTORY --mode render|export [--filename purple_static.glb]
               [--review-profile FILE] [--views front,left,right,back]
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
    'clay_left': ((-4, 0, .88), (0, 0, .88), 1.97),
    'clay_right': ((4, 0, .88), (0, 0, .88), 1.97),
    'clay_back': ((0, 4, .88), (0, 0, .88), 1.97),
    'poster': ((1.6, -4, 1.12), (0, 0, .85), 1.97),
    'face_front': ((0, -4, 1.48), (0, 0, 1.48), .68),
    'face_profile': ((4, 0, 1.48), (0, 0, 1.48), .68),
}


def visible_work():
    collection = bpy.data.collections.get('WORK_Purple')
    if not collection:
        raise RuntimeError('Missing authored WORK_Purple collection')
    return [o for o in collection.all_objects
            if not o.hide_render and o.type in {'MESH', 'CURVE'}]


def apply_review_profile(path):
    """Use the same cameras and lights for source, failed and repaired comparisons."""
    profile = json.loads(path.read_text(encoding='utf-8'))
    scene = bpy.context.scene
    scene.render.engine = profile['engine']
    scene.render.resolution_x, scene.render.resolution_y = profile['resolution']
    scene.eevee.taa_render_samples = profile['samples']
    scene.eevee.shadow_ray_count = profile['shadow_ray_count']
    scene.eevee.shadow_step_count = profile['shadow_step_count']
    for key in ('view_transform', 'look', 'exposure', 'gamma'):
        setattr(scene.view_settings, key, profile[key])
    world = bpy.data.worlds.new('Purple_ReadOnly_Review_World')
    world.use_nodes = True
    background = next(node for node in world.node_tree.nodes if node.type == 'BACKGROUND')
    background.inputs['Color'].default_value = (*profile['world_color'], 1)
    background.inputs['Strength'].default_value = profile['world_strength']
    scene.world = world
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            obj.hide_render = True
    for name, settings in profile['lights'].items():
        data = bpy.data.lights.new(name + '_Review', settings['type'])
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = settings['location']
        obj.rotation_euler = settings['rotation_euler']
        data.energy = settings['energy']
        data.size = settings['size']
        data.use_shadow = settings['use_shadow']
    for name, settings in profile['cameras'].items():
        obj = bpy.data.objects.get('Purple_View_' + name)
        if obj is None:
            data = bpy.data.cameras.new('Purple_View_' + name)
            obj = bpy.data.objects.new(data.name, data)
            scene.collection.objects.link(obj)
        obj.location = settings['location']
        obj.rotation_euler = settings['rotation_euler']
        obj.data.type = 'ORTHO'
        obj.data.ortho_scale = settings['ortho_scale']


def render(output, review_profile=None, views=None):
    scene = bpy.context.scene
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    if review_profile:
        apply_review_profile(review_profile)
    neutral = bpy.data.materials.new('Purple_Review_Neutral')
    neutral.use_nodes = True
    shader = next(node for node in neutral.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (.5, .53, .58, 1)
    shader.inputs['Roughness'].default_value = .75
    for name in views or VIEWS:
        location, target, scale = VIEWS[name]
        camera_name = 'front' if name == 'clay' else name.removeprefix('clay_')
        if name.startswith('face_'):
            camera_name = 'head_side' if name == 'face_profile' else 'head'
        authored_camera = bpy.data.objects.get('Purple_View_' + camera_name)
        camera = authored_camera or scene.camera
        scene.camera = camera
        if authored_camera is None:
            camera.location = location
            camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.ortho_scale = scale
        bpy.context.view_layer.material_override = neutral if name.startswith('clay') else None
        scene.render.filepath = str(output / (name + '.png'))
        hidden = []
        masks = []
        if name.startswith('face_'):
            for obj in visible_work():
                if obj.name.startswith('Body_SourceRepair'):
                    mask = obj.modifiers.get('Embedded_ShortHair_ReversibleMask')
                    if mask:
                        masks.append((mask, mask.show_render))
                        mask.show_render = False
                else:
                    hidden.append((obj, obj.hide_render))
                    obj.hide_render = True
        try:
            bpy.ops.render.render(write_still=True)
        finally:
            for obj, value in hidden:
                obj.hide_render = value
            for mask, value in masks:
                mask.show_render = value
    bpy.context.view_layer.material_override = None


def export(output, filename='purple_static.glb'):
    authored = visible_work()
    if not authored:
        raise RuntimeError('No visible authored purple meshes to export')
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
    path = output / filename
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
    parser.add_argument('--filename', default='purple_static.glb',
                        help='GLB basename; use a distinct name for each candidate lineage')
    parser.add_argument('--review-profile', type=Path,
                        help='Saved camera/light profile for consistent read-only comparisons')
    parser.add_argument('--views', help='Comma-separated render views; defaults to all views')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    args.blend = args.blend.resolve()
    args.output = args.output.resolve()
    if Path(args.filename).name != args.filename or Path(args.filename).suffix.lower() != '.glb':
        parser.error('--filename must be a GLB basename without directories')
    views = args.views.split(',') if args.views else list(VIEWS)
    if any(view not in VIEWS for view in views):
        parser.error('--views contains an unknown review view')
    args.output.mkdir(parents=True, exist_ok=True)
    before = hashlib.sha256(args.blend.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    result = (export(args.output, args.filename) if args.mode == 'export'
              else render(args.output, args.review_profile, views))
    unchanged = before == hashlib.sha256(args.blend.read_bytes()).hexdigest()
    if not unchanged:
        raise RuntimeError('Authored source changed during read-only operation')
    report = {'source': str(args.blend.resolve()), 'source_sha256': before,
              'source_unchanged': unchanged, 'operation': args.mode,
              'art_approved': False, 'result': result,
              'views': views if args.mode == 'render' else None,
              'review_profile': str(args.review_profile.resolve()) if args.review_profile else None,
              'review_profile_sha256': hashlib.sha256(args.review_profile.read_bytes()).hexdigest()
              if args.review_profile else None,
              'face_view_isolation': 'Hide outfit and independent hair; restore source embedded short hair for face inspection'
              if args.mode == 'render' and any(v.startswith('face_') for v in views) else None}
    (args.output / ('purple_' + args.mode + '_report.json')).write_text(
        json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
