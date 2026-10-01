"""Blender character assembly. Run with -- --output DIRECTORY [--character white]."""
import argparse
import json
import math
import pathlib
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def import_part(path, name, scale, location):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = set(bpy.data.objects) - before
    mesh = next(o for o in objects if o.type == 'MESH')
    mesh.name = name
    mesh['source_path'] = str(path.resolve())
    # Source assets face +X, with glTF Y up. Blender importer supplies Z up.
    mesh.matrix_world = Matrix.Rotation(-math.pi / 2, 4, 'Z') @ mesh.matrix_world
    activate(mesh)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mesh.scale = scale
    mesh.location = location
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for polygon in mesh.data.polygons:
        polygon.use_smooth = True
    return mesh


def studio():
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 20
    s.render.resolution_x = 800
    s.render.resolution_y = 1000
    s.render.resolution_percentage = 100
    if s.world is None:
        s.world = bpy.data.worlds.new('StudioWorld')
    s.world.color = (0.55, 0.55, 0.55)
    s.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = 'ReviewCamera'
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 1.95
    s.camera = camera
    for name, loc, power, size in [('Key', (2, -4, 5), 650, 4), ('Fill', (-3, -2, 3), 450, 3), ('Rim', (1, 3, 4), 600, 3)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = 'DISK'
        light.data.size = size
        light.rotation_euler = (Vector((0, 0, 0.9)) - light.location).to_track_quat('-Z', 'Y').to_euler()
    return camera


def fit_outfit(outfit, character):
    # Shoulder remains fixed; sleeve endpoints move onto the body's wrist line.
    for v in outfit.data.vertices:
        x, y, z = v.co
        sleeve = max(0.0, min(1.0, (abs(x) - 0.16) / 0.10))
        sleeve *= max(0.0, min(1.0, (z - 0.72) / 0.15))
        sleeve *= max(0.0, min(1.0, (1.40 - z) / 0.28))
        v.co.y += sleeve * 0.065
        v.co.x -= math.copysign(sleeve * 0.025, x)
        v.co.z -= sleeve * 0.035
        if character in ['orange', 'purple']:
            # Open cuffs are offset forward of the source body's wrists.
            # Align their centres before skinning; weights cannot correct a
            # rest-pose gap between a sleeve opening and the arm inside it.
            cuff = max(0.0, min(1.0, (abs(x)-.17)/.06))
            cuff *= max(0.0, min(1.0, (z-.75)/.10))
            cuff *= max(0.0, min(1.0, (1.28-z)/.14))
            v.co.y += cuff*.065
            v.co.x += (1 if x >= 0 else -1)*cuff*(.03 if character == 'purple' else -.03)
            # Measured arm/sleeve cross-sections differ by character. Align
            # their fore/aft centres along the arm, tapering into the bodice.
            influence = max(0.0, min(1.0, (abs(x)-.14)/.045))
            levels = [.90, 1.0, 1.08, 1.16, 1.23, 1.32, 1.38]
            offsets = [0, -.01, .05, .125, .13, .03, 0] if character == 'purple' else [0, -.085, -.06, -.03, 0, 0, 0]
            v.co.y += influence*float(np.interp(z, levels, offsets))
            lateral = [.0, .025, .015, .02, .015, 0, 0] if character == 'purple' else [0, -.035, -.045, -.025, -.025, 0, 0]
            v.co.x += (1 if x >= 0 else -1)*influence*float(np.interp(z, levels, lateral))
        if character == 'purple':
            hood = max(0.0, min(1.0, (z - 1.35) / 0.12))
            v.co.y += hood * 0.15
            v.co.z -= hood * 0.045


def remove_source_hair(body, character):
    """Remove redundant source hair on the derived mesh, preserving face UVs."""
    material = body.data.materials[0]
    image = next(n.image for n in material.node_tree.nodes if n.type == 'TEX_IMAGE')
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(image.size[1], image.size[0], 4)
    mesh = body.data
    uv = mesh.uv_layers.active.data
    remove = []
    for face in mesh.polygons:
        c = face.center
        if c.z < 1.46:
            continue
        coords = np.array([uv[i].uv[:] for i in face.loop_indices])
        xx = np.clip((coords[:, 0] * image.size[0]).astype(int), 0, image.size[0] - 1)
        yy = np.clip((coords[:, 1] * image.size[1]).astype(int), 0, image.size[1] - 1)
        r, g, b = np.median(pixels[yy, xx, :3], axis=0)
        colored = (r > g * 1.30 and g > b * 1.15) if character == 'orange' else (b > r * 1.015 and b > g * 1.015)
        outside_face = c.z > 1.60 or abs(c.x) > .085 or c.y > .025
        if (colored and outside_face) or c.z > 1.635 or (c.y > 0.025 and c.z > 1.49):
            remove.append(face.index)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in remove], context='FACES')
    bm.to_mesh(mesh)
    bm.free()
    print(f'SOURCE_HAIR_REMOVED {character} {len(remove)}', flush=True)


def render_views(out, prefix):
    camera = bpy.context.scene.camera
    for name, loc in [('front', (0, -4, 0.9)), ('side', (4, 0, 0.9)), ('back', (0, 4, 0.9))]:
        camera.location = loc
        camera.rotation_euler = (Vector((0, 0, 0.9)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.render.filepath = str(out / f'{prefix}_{name}.png')
        bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--character', choices=['white', 'orange', 'purple'])
    parser.add_argument('--source-root', type=pathlib.Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    config = json.loads((HERE / 'characters.json').read_text(encoding='utf-8'))
    if args.source_root:
        config['source_root'] = str(args.source_root.resolve())
    out = pathlib.Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name, spec in config['characters'].items():
        if args.character and args.character != name:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        root = pathlib.Path(config['source_root']) / spec['directory'] / '3D模型'
        body = import_part(root / spec['body'], 'Body', [spec['height']] * 3, [0, 0, 0])
        remove_source_hair(body, name)
        outfit = import_part(root / spec['outfit'], 'Outfit', spec['outfit_scale'], spec['outfit_location'])
        fit_outfit(outfit, name)
        import_part(root / spec['hair'], 'Hair', spec['hair_scale'], spec['hair_location'])
        studio()
        bpy.ops.wm.save_as_mainfile(filepath=str(out / f'{name}_assembly.blend'))
        render_views(out, name)


if __name__ == '__main__':
    main()
