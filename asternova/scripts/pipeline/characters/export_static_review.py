"""Export the authored EXPORT_White collection; never reconstruct geometry.

blender -b --python-exit-code 1 -P export_static_review.py --
  --blend <white_rework_working.blend> --output <white_static.glb>
"""
import argparse
from pathlib import Path
import sys
import hashlib
import json
import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blend', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.blend.resolve() == args.output.resolve():
        raise ValueError('Output must differ from authored source')
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    collection = bpy.data.collections.get('EXPORT_White')
    if collection is None:
        raise ValueError('Missing EXPORT_White authored collection')
    bpy.ops.object.select_all(action='DESELECT')
    objects = [o for o in collection.all_objects
               if o.type in {'MESH', 'CURVE'} and not o.hide_render and not o.hide_get()]
    if not objects:
        raise ValueError('Empty export collection')
    temporary = []
    for obj in objects:
        if obj.type == 'CURVE':
            curve_copy = obj.copy()
            curve_copy.data = obj.data.copy()
            collection.objects.link(curve_copy)
            bpy.context.view_layer.objects.active = curve_copy
            curve_copy.select_set(True)
            bpy.ops.object.convert(target='MESH')
            temporary.append(bpy.context.view_layer.objects.active)
            bpy.ops.object.select_all(action='DESELECT')
    for obj in [o for o in objects if o.type == 'MESH'] + temporary:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(o for o in objects if o.type == 'MESH')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(args.output.resolve()), export_format='GLB',
                              use_selection=True, export_apply=True, export_animations=False)
    report = {'source': str(args.blend.resolve()),
              'source_sha256': hashlib.sha256(args.blend.read_bytes()).hexdigest(),
              'objects': [o.name for o in objects],
              'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'art_approved': False}
    args.output.with_suffix('.export.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for obj in temporary:
        bpy.data.objects.remove(obj, do_unlink=True)
    print('EXPORTED_AUTHORED_STATIC', len(objects), args.output)


if __name__ == '__main__':
    main()
