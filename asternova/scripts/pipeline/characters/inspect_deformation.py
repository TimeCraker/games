"""Sample real Blender deformations; report stretched edges for visual triage."""
import argparse
import json
import pathlib
import sys

import bpy
import numpy as np


def positions(mesh):
    values = np.empty(len(mesh.vertices)*3, dtype=np.float64)
    mesh.vertices.foreach_get('co', values)
    return values.reshape(-1, 3)


def inspect(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = bpy.data.objects['CharacterRig']
    rows = []
    cache = {}
    for name in ['Body', 'Outfit', 'Hair']:
        mesh = bpy.data.objects[name].data
        edges = np.empty(len(mesh.edges)*2, dtype=np.int32)
        mesh.edges.foreach_get('vertices', edges)
        edges = edges.reshape(-1, 2)
        co = positions(mesh)
        lengths = np.linalg.norm(co[edges[:, 0]]-co[edges[:, 1]], axis=1)
        cache[name] = edges, lengths
    for action in bpy.data.actions:
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        first, last = action.frame_range
        for frame in np.linspace(first, last, 7):
            bpy.context.scene.frame_set(int(frame), subframe=float(frame % 1))
            graph = bpy.context.evaluated_depsgraph_get()
            for name, (edges, rest) in cache.items():
                obj = bpy.data.objects[name].evaluated_get(graph)
                mesh = obj.to_mesh()
                co = positions(mesh)
                lengths = np.linalg.norm(co[edges[:, 0]]-co[edges[:, 1]], axis=1)
                suspect = (rest > .003) & (lengths > rest*5) & (lengths > .03)
                rows.append({'clip': action.name, 'frame': round(float(frame), 2),
                             'mesh': name, 'edges_over_5x_and_3cm': int(suspect.sum()),
                             'largest_edge_m': round(float(lengths.max()), 4)})
                obj.to_mesh_clear()
    return {'character': path.stem, 'note': 'Diagnostic, not an artistic acceptance test. Seven samples per clip; no collision or cloth simulation.', 'samples': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=pathlib.Path, required=True)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    result = [inspect(args.directory/f'{name}_master.blend') for name in ['white', 'orange', 'purple']]
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    for character in result:
        worst = sorted(character['samples'], key=lambda row: row['edges_over_5x_and_3cm'], reverse=True)[:3]
        print(character['character'], worst)
