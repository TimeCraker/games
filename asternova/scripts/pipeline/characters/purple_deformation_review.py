"""Sample authored purple runtime deformations; statistics do not approve art."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np


def coordinates(mesh):
    result = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', result)
    return result.reshape((-1, 3))


def inspect(source, count):
    bpy.ops.wm.open_mainfile(filepath=str(source))
    rig = bpy.data.objects['Purple_RuntimeRig']
    cache = {}
    for obj in bpy.data.collections['RUNTIME_Purple'].objects:
        if obj.type != 'MESH':
            continue
        edges = np.empty(len(obj.data.edges) * 2, dtype=np.int32)
        obj.data.edges.foreach_get('vertices', edges)
        edges = edges.reshape((-1, 2))
        co = coordinates(obj.data)
        lengths = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
        cache[obj.name] = edges, lengths
    rows = []
    for action in bpy.data.actions:
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        first, last = action.frame_range
        for frame in np.linspace(first, last, count):
            bpy.context.scene.frame_set(int(frame), subframe=float(frame % 1))
            graph = bpy.context.evaluated_depsgraph_get()
            for name, (edges, rest) in cache.items():
                evaluated = bpy.data.objects[name].evaluated_get(graph)
                mesh = evaluated.to_mesh()
                co = coordinates(mesh)
                lengths = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1)
                suspect = (rest > .003) & (lengths > rest * 5) & (lengths > .03)
                rows.append({'clip': action.name, 'frame': round(float(frame), 3),
                             'mesh': name, 'edges_over_5x_and_3cm': int(suspect.sum()),
                             'largest_edge_m': round(float(lengths.max()), 4)})
                evaluated.to_mesh_clear()
    return {'note': 'Diagnostic only. Sampled frames, no collision/cloth test or visual approval.',
            'samples_per_clip': count, 'art_approved': False,
            'deformation_approved': False, 'samples': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blend', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=7)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source = args.blend.resolve()
    report = args.report.resolve()
    if args.samples < 2:
        parser.error('--samples must be at least 2')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = inspect(source, args.samples)
    result['source'] = str(source)
    result['source_sha256'] = digest
    result['source_unchanged'] = digest == hashlib.sha256(source.read_bytes()).hexdigest()
    if not result['source_unchanged']:
        raise RuntimeError('Read-only review changed its source')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    worst = sorted(result['samples'], key=lambda row: row['edges_over_5x_and_3cm'], reverse=True)
    print('PURPLE_DEFORMATION_REVIEW', json.dumps(worst[:12]), flush=True)


if __name__ == '__main__':
    main()
