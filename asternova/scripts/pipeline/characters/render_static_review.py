"""Render fixed views of an authored blend without saving or rebuilding it."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


VIEWS = {
    'front': ((0, -4, .88), (0, 0, .88), 1.94),
    'left': ((-4, 0, .88), (0, 0, .88), 1.94),
    'right': ((4, 0, .88), (0, 0, .88), 1.94),
    'back': ((0, 4, .88), (0, 0, .88), 1.94),
    'threequarter': ((2, -4, .88), (0, 0, .88), 1.94),
    'head': ((0, -4, 1.53), (0, 0, 1.53), .43),
    'head_side': ((4, 0, 1.53), (0, 0, 1.53), .43),
    'head_threequarter': ((3, -4, 1.53), (0, 0, 1.53), .43),
    'clay': ((0, -4, .88), (0, 0, .88), 1.94),
    'head_clay': ((3, -4, 1.53), (0, 0, 1.53), .43),
}


def mesh_signature(obj):
    """Hash authored positions and UV corners, separately from render normals."""
    data = obj.data
    payload = {
        'positions': [list(v.co) for v in data.vertices],
        'faces': [list(p.vertices) for p in data.polygons],
        'uv': [list(v.uv) for v in data.uv_layers.active.data],
    }
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blend', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--views', nargs='+', choices=VIEWS, default=list(VIEWS))
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source_hash = hashlib.sha256(args.blend.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    scene = bpy.context.scene
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    args.output.mkdir(parents=True, exist_ok=True)
    neutral = bpy.data.materials.new('ReviewNeutralOnly')
    neutral.use_nodes = True
    shader = neutral.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (.55, .57, .61, 1)
    shader.inputs['Roughness'].default_value = .7
    for name in args.views:
        position, target, scale = VIEWS[name]
        scene.camera.location = position
        scene.camera.rotation_euler = (Vector(target) - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera.data.type = 'ORTHO'
        scene.camera.data.ortho_scale = scale
        bpy.context.view_layer.material_override = neutral if 'clay' in name else None
        scene.render.filepath = str((args.output / (name + '.png')).resolve())
        bpy.ops.render.render(write_still=True)
    bpy.context.view_layer.material_override = None
    head = bpy.data.objects.get('Head_Work')
    original = bpy.data.objects.get('Head_BeforeForeheadCleanup')
    report = {
        'source_sha256': source_hash,
        'source_unchanged': source_hash == hashlib.sha256(args.blend.read_bytes()).hexdigest(),
        'resolution': [800, 1000],
        'views': {name: VIEWS[name] for name in args.views},
        'head_signature': mesh_signature(head) if head else None,
        'original_head_signature': mesh_signature(original) if original else None,
        'face_geometry_uv_unchanged': bool(head and original and mesh_signature(head) == mesh_signature(original)),
        'art_approved': False,
    }
    (args.output / 'render_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
