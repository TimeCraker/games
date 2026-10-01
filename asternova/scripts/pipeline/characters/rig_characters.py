"""Fit a humanoid rig, skin modular parts, and bake licensed source animations.

Uses Blender bone heat and data transfer. The output still needs visual review.
"""
import argparse
import json
import math
import pathlib
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_characters import activate, render_views, import_part

PROJECT = HERE.parents[2]
SOURCE = PROJECT / 'art/characters/animation-source/AnimationLibrary_Godot_Standard.gltf'
CLIPS = {
    'Idle': 'Idle_Loop', 'Walk': 'Walk_Loop', 'Run': 'Jog_Fwd_Loop',
    'Sprint': 'Sprint_Loop', 'Jump': 'Jump_Start', 'Fall': 'Jump_Loop',
    'Land': 'Jump_Land', 'Attack': 'Punch_Jab', 'Talk': 'Idle_Talking_Loop',
}


def make_rig(source, body):
    data = bpy.data.armatures.new('Humanoid')
    rig = bpy.data.objects.new('CharacterRig', data)
    bpy.context.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    definitions = [
        ('root', None, (0, 0, 0), (0, 0.15, 0)),
        ('DEF-hips', 'root', (0, 0, .94), (0, 0, 1.02)),
        ('DEF-spine.001', 'DEF-hips', (0, 0, 1.02), (0, 0, 1.14)),
        ('DEF-spine.002', 'DEF-spine.001', (0, 0, 1.14), (0, 0, 1.26)),
        ('DEF-spine.003', 'DEF-spine.002', (0, 0, 1.26), (0, 0, 1.38)),
        ('DEF-neck', 'DEF-spine.003', (0, 0, 1.38), (0, -.005, 1.46)),
        ('DEF-head', 'DEF-neck', (0, -.005, 1.46), (0, -.005, 1.64)),
    ]
    for side, sign in [('L', 1), ('R', -1)]:
        def p(x, y, z):
            return (x * sign, y, z)
        definitions.extend([
            (f'DEF-shoulder.{side}', 'DEF-spine.003', p(.025, 0, 1.36), p(.135, .012, 1.34)),
            (f'DEF-upper_arm.{side}', f'DEF-shoulder.{side}', p(.135, .012, 1.34), p(.20, .035, 1.13)),
            (f'DEF-forearm.{side}', f'DEF-upper_arm.{side}', p(.20, .035, 1.13), p(.28, .026, .935)),
            (f'DEF-hand.{side}', f'DEF-forearm.{side}', p(.28, .026, .935), p(.305, .02, .82)),
            (f'DEF-thigh.{side}', 'DEF-hips', p(.082, 0, .93), p(.145, .012, .565)),
            (f'DEF-shin.{side}', f'DEF-thigh.{side}', p(.145, .012, .565), p(.201, .032, .165)),
            (f'DEF-foot.{side}', f'DEF-shin.{side}', p(.201, .032, .165), p(.201, -.075, .065)),
            (f'DEF-toe.{side}', f'DEF-foot.{side}', p(.201, -.075, .065), p(.201, -.16, .06)),
        ])
    for name, parent, head, tail in definitions:
        bone = data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent:
            bone.parent = data.edit_bones[parent]
        if name in source.data.bones:
            bone.align_roll(source.data.bones[name].matrix_local.to_3x3() @ Vector((0, 0, 1)))
        bone.use_deform = name != 'root'
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    data.display_type = 'OCTAHEDRAL'
    return rig


def weld(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(mesh.data)
    bm.free()


def components(mesh):
    adjacency = [[] for _ in mesh.data.vertices]
    for edge in mesh.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen = set()
    result = []
    for vertex in mesh.data.vertices:
        if vertex.index in seen:
            continue
        stack = [vertex.index]
        seen.add(vertex.index)
        group = []
        while stack:
            index = stack.pop()
            group.append(index)
            for neighbor in adjacency[index]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        result.append(group)
    return result


def assign(mesh, vertex, weights):
    for group in list(vertex.groups):
        mesh.vertex_groups[group.group].remove([vertex.index])
    total = sum(weights.values())
    for name, value in weights.items():
        if value > 0:
            mesh.vertex_groups[name].add([vertex.index], value/total, 'REPLACE')


def smooth_weights(mesh):
    activate(mesh)
    for v in mesh.data.vertices:
        v.select = True
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=.5, repeat=4)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)


def smooth_surface_weights(mesh, radius=.025, z_range=None):
    """Average in physical space so dense AI seams have consistent weights."""
    vertices = mesh.data.vertices
    tree = KDTree(len(vertices))
    weights = np.zeros((len(vertices), len(mesh.vertex_groups)), dtype=np.float64)
    for v in vertices:
        tree.insert(v.co, v.index)
        for g in v.groups:
            weights[v.index, g.group] = g.weight
    tree.balance()
    names = [g.name for g in mesh.vertex_groups]
    for v in vertices:
        if z_range and not z_range[0] < v.co.z < z_range[1]:
            continue
        neighbours = tree.find_range(v.co, radius)
        indices = [index for _, index, _ in neighbours]
        kernel = np.array([math.exp(-4*(distance/radius)**2) for _, _, distance in neighbours])
        average = (weights[indices]*kernel[:, None]).sum(axis=0)/kernel.sum()
        assign(mesh, v, {name: float(value) for name, value in zip(names, average) if value > 1e-6})


def bind_body(body, rig, character):
    weld(body)
    # Bone heat needs a closed volume. AI meshes contain detached cloth/boots
    # and open head surfaces; use a temporary voxel proxy only for solving.
    config = json.loads((HERE/'characters.json').read_text(encoding='utf-8'))
    spec = config['characters'][character]
    path = pathlib.Path(body.get('source_path', str(pathlib.Path(config['source_root'])/spec['directory']/'3D模型'/spec['body'])))
    proxy = import_part(path, 'WeightSolveProxy', [spec['height']]*3, [0, 0, 0])
    activate(proxy)
    remesh = proxy.modifiers.new('ClosedWeightVolume', 'REMESH')
    remesh.mode = 'VOXEL'
    remesh.voxel_size = .009
    remesh.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    # Bone heat is sensitive to very small triangles. Solve in centimeters,
    # then return both rest skeleton and proxy geometry to meters.
    proxy.data.transform(Matrix.Scale(100, 4))
    rig.data.transform(Matrix.Scale(100, 4))
    bpy.context.view_layer.update()
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    rig.data.transform(Matrix.Scale(.01, 4))
    proxy.data.transform(Matrix.Scale(.01, 4))
    bpy.context.view_layer.update()
    if sum(bool(v.groups) for v in proxy.data.vertices) < len(proxy.data.vertices)*.9:
        print('PROXY_WEIGHT_COUNTS',len(proxy.data.vertices),sum(bool(v.groups) for v in proxy.data.vertices), flush=True)
        raise RuntimeError('Native bone heat did not solve the closed proxy')
    activate(body)
    for g in proxy.vertex_groups:
        body.vertex_groups.new(name=g.name)
    transfer = body.modifiers.new('SolvedBodyWeights', 'DATA_TRANSFER')
    transfer.object = proxy
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    body.parent = rig
    body.modifiers.new('HumanoidDeform', 'ARMATURE').object = rig
    bpy.data.objects.remove(proxy, do_unlink=True)
    # Keep head rigid; facial animation requires authored shape keys later.
    group = body.vertex_groups.get('DEF-head')
    for v in body.data.vertices:
        if v.co.z > 1.47:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            group.add([v.index], 1.0, 'REPLACE')
        elif v.co.z < .29:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            side = 'L' if v.co.x > 0 else 'R'
            t = max(0.0, min(1.0, (.29-v.co.z)/.10))
            body.vertex_groups['DEF-foot.'+side].add([v.index], t, 'REPLACE')
            body.vertex_groups['DEF-shin.'+side].add([v.index], 1-t, 'REPLACE')
        elif v.co.z < .945 and abs(v.co.x) > .25:
            for g in list(v.groups):
                body.vertex_groups[g.group].remove([v.index])
            side = 'L' if v.co.x > 0 else 'R'
            body.vertex_groups['DEF-hand.'+side].add([v.index], 1.0, 'REPLACE')
    missing = [v for v in body.data.vertices if not v.groups]
    if missing:
        from mathutils.kdtree import KDTree
        valid = [v for v in body.data.vertices if v.groups]
        tree = KDTree(len(valid))
        for v in valid:
            tree.insert(v.co, v.index)
        tree.balance()
        for v in missing:
            _, index, distance = tree.find(v.co)
            if distance > .06:
                raise RuntimeError(f'Unresolved disconnected mesh at {v.co[:]}')
            for g in body.data.vertices[index].groups:
                body.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')
        print(f'HEAT_DETACHED_SURFACE_REPAIR {len(missing)}', flush=True)
    for v in body.data.vertices:
        if .94 < v.co.z < 1.37 and abs(v.co.x) < .14:
            allowed = {'DEF-hips', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003', 'DEF-neck'}
            weights = {body.vertex_groups[g.group].name:g.weight for g in v.groups if body.vertex_groups[g.group].name in allowed}
            assign(body, v, weights or {'DEF-spine.001':1})
    smooth_weights(body)
    smooth_surface_weights(body, .018)


def transfer_clothing(body, outfit, rig):
    weld(outfit)
    activate(outfit)
    for group in body.vertex_groups:
        outfit.vertex_groups.new(name=group.name)
    transfer = outfit.modifiers.new('BodySurfaceWeights', 'DATA_TRANSFER')
    transfer.object = body
    transfer.use_vert_data = True
    transfer.data_types_verts = {'VGROUP_WEIGHTS'}
    transfer.vert_mapping = 'POLYINTERP_NEAREST'
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    modifier = outfit.modifiers.new('HumanoidDeform', 'ARMATURE')
    modifier.object = rig
    outfit.parent = rig


def add_secondary(rig, hair, outfit, character):
    activate(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, parent, head, tail in [
        ('HairBack', 'DEF-head', (0, .08, 1.56), (0, .12, 1.30)),
        ('HairTip', 'HairBack', (0, .12, 1.30), (0, .14, 1.07)),
        ('Coat.L', 'DEF-hips', (.15, .02, .93), (.23, .04, .40)),
        ('Coat.R', 'DEF-hips', (-.15, .02, .93), (-.23, .04, .40)),
    ]:
        b = rig.data.edit_bones.new(name)
        b.head, b.tail = head, tail
        b.parent = rig.data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for name in ['DEF-head', 'HairBack', 'HairTip']:
        hair.vertex_groups.new(name=name)
    for v in hair.data.vertices:
        z = v.co.z
        if z >= 1.48:
            weights = {'DEF-head': 1.0}
        elif z > 1.30:
            t = (1.48 - z) / .18
            weights = {'DEF-head': 1-t, 'HairBack': t}
        else:
            t = min(1.0, (1.30-z)/.20)
            weights = {'HairBack': 1-t, 'HairTip': t}
        for name, weight in weights.items():
            if weight > 0:
                hair.vertex_groups[name].add([v.index], weight, 'REPLACE')
    hair.parent = rig
    hair.modifiers.new('HumanoidDeform', 'ARMATURE').object = rig
    for name in ['Coat.L', 'Coat.R']:
        outfit.vertex_groups.new(name=name)
    arm_vertices = set()
    garment_components = components(outfit)
    for group in garment_components:
        coords = [outfit.data.vertices[i].co for i in group]
        minimum_z, maximum_z = min(v.z for v in coords), max(v.z for v in coords)
        minimum_x = min(abs(v.x) for v in coords)
        if (minimum_z > .75 and maximum_z > 1.25) or (minimum_z > .60 and minimum_x > .17 and maximum_z > .90):
            arm_vertices.update(group)
    for v in outfit.data.vertices:
        is_arm = (v.index in arm_vertices and abs(v.co.x) > .16) or (v.co.z > 1.0 and abs(v.co.x) > .19)
        side = 'L' if v.co.x >= 0 else 'R'
        # Lower hanging panels must not copy a nearby calf or opposite leg.
        if v.co.z < .88 and not is_arm:
            side = 'L' if v.co.x >= 0 else 'R'
            t = max(0.0, min(1.0, (.88-v.co.z)/.20))
            for g in list(v.groups):
                outfit.vertex_groups[g.group].remove([v.index])
            outfit.vertex_groups['DEF-hips'].add([v.index], 1-t, 'REPLACE')
            outfit.vertex_groups['Coat.'+side].add([v.index], t, 'REPLACE')
        elif v.co.z < 1.045 and not is_arm:
            for g in list(v.groups):
                outfit.vertex_groups[g.group].remove([v.index])
            outfit.vertex_groups['DEF-hips'].add([v.index], 1.0, 'REPLACE')
        if character == 'white' and v.co.z < 1.045 and is_arm:
            t = max(0.0, min(1.0, (1.035-v.co.z)/.085))
            assign(outfit, v, {'DEF-hand.'+side:t, 'DEF-forearm.'+side:1-t})
        elif is_arm:
            t = max(0.0, min(1.0, (1.23-v.co.z)/.12))
            assign(outfit, v, {'DEF-forearm.'+side:t, 'DEF-upper_arm.'+side:1-t})
        if v.co.z > 1.37:
            assign(outfit, v, {'DEF-spine.003':1})
        elif 1.045 < v.co.z < 1.34 and abs(v.co.x) < .15:
            allowed = {'DEF-hips','DEF-spine.001','DEF-spine.002','DEF-spine.003'}
            weights = {outfit.vertex_groups[g.group].name:g.weight for g in v.groups if outfit.vertex_groups[g.group].name in allowed}
            assign(outfit, v, weights or {'DEF-spine.002':1})
    smooth_weights(outfit)
    # Smooth uneven shoulder seams physically; cuffs and coat panels retain
    # separate assignments even when close together in the rest pose.
    smooth_surface_weights(outfit, z_range=(1.045, 1.37))
    # Disconnected buckles, straps and hard accessories move as intact pieces.
    for group in garment_components:
        if len(group) < 120:
            totals = {}
            for index in group:
                for g in outfit.data.vertices[index].groups:
                    name = outfit.vertex_groups[g.group].name
                    totals[name] = totals.get(name, 0) + g.weight
            best = max(totals, key=totals.get)
            for index in group:
                assign(outfit, outfit.data.vertices[index], {best:1})


def mask_covered_body(body, character):
    """Reversible in source: hide arm regions covered by fitted sleeves/gloves."""
    bm = bmesh.new()
    bm.from_mesh(body.data)
    faces = []
    for f in bm.faces:
        c = f.calc_center_median()
        # Keep hands for outfits that do not contain gloves. White has its own.
        # Only the white garment has a complete glove/sleeve cover. Keep the
        # whole arms on open purple/orange sleeves, including bent elbows.
        if character == 'white' and .70 < c.z < 1.335 and abs(c.x) > (.14 if c.z > 1.15 else .17):
            faces.append(f)
        elif .88 < c.z < .995 and abs(c.x) < .17:
            faces.append(f)
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(body.data)
    bm.free()


def normalize(mesh):
    activate(mesh)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    missing, error, influences = 0, 0.0, 0
    for v in mesh.data.vertices:
        weights = [g.weight for g in v.groups if g.weight > 0.000001]
        missing += int(not weights)
        error = max(error, abs(sum(weights)-1))
        influences = max(influences, len(weights))
    if missing or error > .001 or influences > 4:
        raise RuntimeError(f'Invalid skin {mesh.name}: {missing}, {error}, {influences}')
    return {'vertices': len(mesh.data.vertices), 'triangles': sum(len(p.vertices)-2 for p in mesh.data.polygons), 'unweighted': missing, 'max_weight_sum_error': error, 'max_influences': influences}


def bake(source, rig):
    scene = bpy.context.scene
    scene.render.fps = 30
    source.animation_data_create()
    for track in source.animation_data.nla_tracks:
        track.mute = True
    rig.animation_data_create()
    source_actions = {k: bpy.data.actions.get(v) for k, v in CLIPS.items()}
    actions = {}
    target_bones = [p for p in rig.pose.bones if p.name in source.pose.bones]
    scale = rig.data.bones['DEF-hips'].head_local.z / source.data.bones['DEF-hips'].head_local.z
    source.animation_data.action = bpy.data.actions['A_TPose']
    source.animation_data.action_slot = source.animation_data.action.slots[0]
    scene.frame_set(0)
    reference = {p.name: p.matrix.copy() for p in source.pose.bones}
    target_reference = {}
    for pb in target_bones:
        rotation = pb.bone.matrix_local.to_quaternion()
        if any(part in pb.name for part in ['upper_arm', 'forearm', 'hand']):
            direction = pb.bone.tail_local - pb.bone.head_local
            t_direction = Vector((1 if pb.name.endswith('.L') else -1, 0, 0))
            rotation = direction.rotation_difference(t_direction) @ rotation
        target_reference[pb.name] = rotation
    for label, action in source_actions.items():
        if action is None:
            raise RuntimeError(f'Missing action {CLIPS[label]}')
        source.animation_data.action = action
        source.animation_data.action_slot = action.slots[0]
        target_action = bpy.data.actions.new(label)
        rig.animation_data.action = target_action
        # Original glTF sampler times were imported at the default 24 FPS.
        first, last = action.frame_range
        frames = max(2, round((last-first)/24*30)+1)
        for frame in range(frames):
            source_frame = first + frame/30*24
            scene.frame_set(math.floor(source_frame), subframe=source_frame % 1)
            for pb in target_bones:
                rest = pb.bone.matrix_local
                if pb.parent:
                    origin = pb.parent.matrix @ pb.parent.bone.matrix_local.inverted() @ rest.translation
                else:
                    origin = rest.translation.copy()
                if pb.name == 'DEF-hips':
                    delta = source.pose.bones[pb.name].matrix.translation-reference[pb.name].translation
                    origin += delta*scale
                rotation = source.pose.bones[pb.name].matrix.to_quaternion() @ reference[pb.name].to_quaternion().inverted() @ target_reference[pb.name]
                # Calibrated T-pose delta, using armature-space matrices. Bone
                # y_axis/z_axis properties are parent-local and cannot be used
                # as world-space axes for retargeting or roll alignment.
                pb.matrix = Matrix.LocRotScale(origin, rotation, Vector((1, 1, 1)))
                bpy.context.view_layer.update()
                pb.rotation_mode = 'QUATERNION'
                pb.keyframe_insert(data_path='rotation_quaternion', frame=frame+1, group=pb.name)
                if pb.name in ['root', 'DEF-hips']:
                    pb.keyframe_insert(data_path='location', frame=frame+1, group=pb.name)
            # Coat follows each thigh conservatively, preventing rigid boards
            # through the leading leg. Hair chains are stable, ready for physics.
            for side in ['L', 'R']:
                coat = rig.pose.bones['Coat.'+side]
                base = coat.parent.matrix @ coat.parent.bone.matrix_local.inverted() @ coat.bone.matrix_local
                leg = rig.pose.bones['DEF-thigh.'+side]
                follow = leg.matrix @ leg.bone.matrix_local.inverted() @ coat.bone.matrix_local
                rotation = base.to_quaternion().slerp(follow.to_quaternion(), .8)
                coat.matrix = Matrix.LocRotScale(base.translation, rotation, Vector((1,1,1)))
                coat.rotation_mode = 'QUATERNION'
                coat.keyframe_insert(data_path='rotation_quaternion', frame=frame+1, group=coat.name)
        target_action.use_fake_user = True
        actions[label] = target_action
        print(f'BAKED {label} {frames} frames', flush=True)
    rig.animation_data.action = None
    for label, action in actions.items():
        track = rig.animation_data.nla_tracks.new()
        track.name = label
        strip = track.strips.new(label, 1, action)
        track.mute = True
    return actions


def prepare_master(rig):
    activate(rig)
    rig.show_in_front = True
    rig.data.display_type = 'STICK'
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_location = Vector((0, 0, .90))
                area.spaces.active.region_3d.view_distance = 3.0
                area.spaces.active.region_3d.view_rotation = Vector((0, 1, 0)).to_track_quat('-Z', 'Y')
    bpy.ops.file.pack_all()
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--assembly', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--character', required=True, choices=['white', 'orange', 'purple'])
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out = pathlib.Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(args.assembly).resolve()))
    body, outfit, hair = [bpy.data.objects[n] for n in ['Body', 'Outfit', 'Hair']]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    imported = set(bpy.data.objects)-before
    source = next(o for o in imported if o.type == 'ARMATURE')
    for o in imported:
        if o.type != 'ARMATURE':
            bpy.data.objects.remove(o, do_unlink=True)
    source.animation_data.action = None
    for t in source.animation_data.nla_tracks:
        t.mute = True
    rig = make_rig(source, body)
    bind_body(body, rig, args.character)
    transfer_clothing(body, outfit, rig)
    add_secondary(rig, hair, outfit, args.character)
    mask_covered_body(body, args.character)
    stats = {m.name: normalize(m) for m in [body, outfit, hair]}
    actions = bake(source, rig)
    bpy.data.objects.remove(source, do_unlink=True)
    for action in list(bpy.data.actions):
        if action not in actions.values():
            bpy.data.actions.remove(action)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    activate(rig)
    for mesh in [body, outfit, hair]:
        mesh.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/f'{args.character}.glb'), export_format='GLB', use_selection=True,
        export_animations=True, export_animation_mode='ACTIONS', export_all_influences=False, export_def_bones=True)
    rig.animation_data.action = actions['Idle']
    rig.animation_data.action_slot = actions['Idle'].slots[0]
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = int(actions['Idle'].frame_range[1])
    prepare_master(rig)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{args.character}_master.blend'))
    render_views(out, args.character+'_idle')
    for clip, frame in [('Walk', 10), ('Run', 8), ('Attack', 16)]:
        rig.animation_data.action = actions[clip]
        rig.animation_data.action_slot = actions[clip].slots[0]
        if clip == 'Attack':
            frame = round(actions[clip].frame_range[1]*.4)
        bpy.context.scene.frame_set(frame)
        camera = bpy.context.scene.camera
        camera.location = (2.7, -4, 1.1)
        camera.rotation_euler = (Vector((0, 0, .9))-camera.location).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.render.filepath = str(out/f'{args.character}_{clip.lower()}.png')
        bpy.ops.render.render(write_still=True)
    (out/f'{args.character}_skin_report.json').write_text(json.dumps({'character': args.character, 'bones': len(rig.data.bones), 'meshes': stats, 'clips': list(actions)}, indent=2), encoding='utf-8')
    print('RIG_EXPORT_COMPLETE', args.character, flush=True)


if __name__ == '__main__':
    main()
