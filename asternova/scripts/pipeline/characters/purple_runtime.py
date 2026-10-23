"""Bake the licensed nine clips onto a runtime skeleton from authored Rigify bones.

The static and bound production blends are read-only inputs. The resulting
runtime blend is also editable; --mode export only exports that saved source.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_characters import activate
from rig_characters import CLIPS, SOURCE


def parent_name(name):
    if name == 'DEF-spine':
        return None
    if name.startswith('DEF-CoatBack.'):
        index = int(name.rsplit('.', 1)[1])
        return 'DEF-spine' if index == 1 else f'DEF-CoatBack.{index-1:03d}'
    if name.startswith('DEF-spine.'):
        index = int(name.rsplit('.', 1)[1])
        return 'DEF-spine' if index == 1 else f'DEF-spine.{index-1:03d}'
    for side in ['L', 'R']:
        if name.startswith('DEF-HairBack.' + side):
            index = int(name.rsplit('.', 1)[1])
            return 'DEF-spine.006' if index == 1 else f'DEF-HairBack.{side}.{index-1:03d}'
        if name.startswith('DEF-Coat.' + side):
            index = int(name.rsplit('.', 1)[1])
            return 'DEF-spine' if index == 1 else f'DEF-Coat.{side}.{index-1:03d}'
        mapping = {
            f'DEF-pelvis.{side}': 'DEF-spine',
            f'DEF-breast.{side}': 'DEF-spine.003',
            f'DEF-shoulder.{side}': 'DEF-spine.003',
            f'DEF-upper_arm.{side}': f'DEF-shoulder.{side}',
            f'DEF-upper_arm.{side}.001': f'DEF-upper_arm.{side}',
            f'DEF-forearm.{side}': f'DEF-upper_arm.{side}.001',
            f'DEF-forearm.{side}.001': f'DEF-forearm.{side}',
            f'DEF-hand.{side}': f'DEF-forearm.{side}.001',
            f'DEF-thigh.{side}': 'DEF-spine',
            f'DEF-thigh.{side}.001': f'DEF-thigh.{side}',
            f'DEF-shin.{side}': f'DEF-thigh.{side}.001',
            f'DEF-shin.{side}.001': f'DEF-shin.{side}',
            f'DEF-foot.{side}': f'DEF-shin.{side}.001',
            f'DEF-toe.{side}': f'DEF-foot.{side}',
        }
        if name in mapping:
            return mapping[name]
    raise ValueError('Unknown generated deformation bone: ' + name)


def source_name(name):
    spine = {'DEF-spine': 'DEF-hips', 'DEF-spine.001': 'DEF-spine.001',
             'DEF-spine.002': 'DEF-spine.002', 'DEF-spine.003': 'DEF-spine.003',
             'DEF-spine.004': 'DEF-neck', 'DEF-spine.005': 'DEF-neck',
             'DEF-spine.006': 'DEF-head'}
    if name in spine:
        return spine[name]
    if name.endswith('.001') and any(part in name for part in ['upper_arm', 'forearm', 'thigh', 'shin']):
        return name[:-4]
    if any(part in name for part in ['shoulder', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'foot', 'toe']):
        return name
    return None


def bake(output):
    control = bpy.data.objects['Purple_ControlRig']
    control.data.pose_position = 'REST'
    data = bpy.data.armatures.new('Purple_Runtime_Skeleton')
    rig = bpy.data.objects.new('Purple_RuntimeRig', data)
    bpy.context.scene.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in control.data.bones:
        if bone.use_deform:
            dst = data.edit_bones.new(bone.name)
            dst.head, dst.tail = bone.head_local, bone.tail_local
            dst.align_roll(bone.matrix_local.to_3x3() @ Vector((0, 0, 1)))
    for bone in data.edit_bones:
        parent = parent_name(bone.name)
        if parent:
            bone.parent = data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    collection = bpy.data.collections.new('RUNTIME_Purple')
    bpy.context.scene.collection.children.link(collection)
    for obj in list(bpy.data.collections['RIG_Purple'].objects):
        duplicate = obj.copy()
        duplicate.data = obj.data.copy()
        collection.objects.link(duplicate)
        duplicate.name = obj.name.replace('_Skinned', '_Runtime')
        duplicate.parent = rig
        duplicate.matrix_parent_inverse = Matrix.Identity(4)
        for modifier in duplicate.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.object = rig
    bpy.data.collections['RIG_Purple'].hide_render = True
    bpy.data.collections['RIG_Purple'].hide_viewport = True
    control.hide_render = True
    control.hide_set(True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    imported = set(bpy.data.objects) - before
    source = next(obj for obj in imported if obj.type == 'ARMATURE')
    for obj in imported:
        if obj != source:
            bpy.data.objects.remove(obj, do_unlink=True)
    for track in source.animation_data.nla_tracks:
        track.mute = True
    scene = bpy.context.scene
    source.animation_data.action = bpy.data.actions['A_TPose']
    source.animation_data.action_slot = source.animation_data.action.slots[0]
    scene.frame_set(0)
    reference = {p.name: p.matrix.copy() for p in source.pose.bones}
    # The source Idle holds a forward head tilt; use its neutral first head
    # orientation to remove that constant bias, preserving animated changes.
    idle = bpy.data.actions[CLIPS['Idle']]
    source.animation_data.action = idle
    source.animation_data.action_slot = idle.slots[0]
    scene.frame_set(int(idle.frame_range[0]))
    reference['DEF-head'] = source.pose.bones['DEF-head'].matrix.copy()
    target_reference = {}
    for pb in rig.pose.bones:
        rotation = pb.bone.matrix_local.to_quaternion()
        if any(part in pb.name for part in ['upper_arm', 'forearm', 'hand']):
            direction = pb.bone.tail_local - pb.bone.head_local
            sign = 1 if '.L' in pb.name else -1
            rotation = direction.rotation_difference(Vector((sign, 0, 0))) @ rotation
        target_reference[pb.name] = rotation
    scale = data.bones['DEF-spine'].head_local.z / source.data.bones['DEF-hips'].head_local.z
    rig.animation_data_create()
    actions = {}
    scene.render.fps = 30
    def depth(bone):
        return 0 if bone.parent is None else 1 + depth(bone.parent)
    # Coat roots depend on the current thigh pose, not the preceding sample.
    ordered_bones = sorted(rig.pose.bones, key=lambda bone: (
        bone.name.startswith(('DEF-HairBack.', 'DEF-Coat.', 'DEF-CoatBack.')),
        depth(bone)))
    for label, clip in CLIPS.items():
        action = bpy.data.actions[clip]
        source.animation_data.action = action
        source.animation_data.action_slot = action.slots[0]
        target = bpy.data.actions.new(label)
        rig.animation_data.action = target
        first, last = action.frame_range
        frames = max(2, round((last - first) / 24 * 30) + 1)
        for frame in range(frames):
            sample = first + frame / 30 * 24
            scene.frame_set(math.floor(sample), subframe=sample % 1)
            for pb in ordered_bones:
                name = source_name(pb.name)
                rest = pb.bone.matrix_local
                base = (pb.parent.matrix @ pb.parent.bone.matrix_local.inverted() @ rest
                        if pb.parent else rest.copy())
                origin = base.translation
                rotation = base.to_quaternion()
                if name:
                    if pb.name == 'DEF-spine':
                        origin += (source.pose.bones[name].matrix.translation - reference[name].translation) * scale
                    rotation = (source.pose.bones[name].matrix.to_quaternion()
                                @ reference[name].to_quaternion().inverted()
                                @ target_reference[pb.name])
                elif pb.name.startswith('DEF-Coat.') and pb.name.endswith('.001'):
                    side = pb.name.split('.')[1]
                    leg = rig.pose.bones['DEF-thigh.' + side]
                    follow = leg.matrix @ leg.bone.matrix_local.inverted() @ rest
                    rotation = rotation.slerp(follow.to_quaternion(), .65)
                elif pb.name.startswith('DEF-HairBack.') and pb.name.endswith('.001'):
                    # A baked body-follow bias keeps heavy back locks from
                    # swinging rigidly with every head turn. No cloth simulation.
                    chest = rig.pose.bones['DEF-spine.003']
                    stable = chest.matrix @ chest.bone.matrix_local.inverted() @ rest
                    rotation = rotation.slerp(stable.to_quaternion(), .65)
                pb.matrix = Matrix.LocRotScale(origin, rotation, Vector((1, 1, 1)))
                bpy.context.view_layer.update()
                pb.rotation_mode = 'QUATERNION'
                pb.keyframe_insert(data_path='rotation_quaternion', frame=frame+1, group=pb.name)
                if pb.name == 'DEF-spine':
                    pb.keyframe_insert(data_path='location', frame=frame+1, group=pb.name)
            target.use_fake_user = True
        actions[label] = target
        print('PURPLE_BAKED', label, frames, flush=True)
    bpy.data.objects.remove(source, do_unlink=True)
    for action in list(bpy.data.actions):
        if action not in actions.values():
            bpy.data.actions.remove(action)
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    for label, action in actions.items():
        track = rig.animation_data.nla_tracks.new()
        track.name = label
        track.strips.new(label, 1, action)
        track.mute = True
    bpy.context.view_layer.update()
    scene['art_approved'] = False
    scene['runtime_rig'] = rig.name
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'purple_runtime_working.blend'))
    return rig


def export(rig, output):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    activate(rig)
    for obj in bpy.data.collections['RUNTIME_Purple'].objects:
        obj.select_set(True)
    path = output / 'purple_repaired.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_animations=True, export_animation_mode='ACTIONS',
                              export_def_bones=True, export_all_influences=False)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['bake', 'export'], required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.source, args.output = args.source.resolve(), args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    original_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(args.source))
    rig = bake(args.output) if args.mode == 'bake' else bpy.data.objects['Purple_RuntimeRig']
    path = export(rig, args.output)
    unchanged = original_hash == hashlib.sha256(args.source.read_bytes()).hexdigest()
    if not unchanged:
        raise RuntimeError('Authoring source was unexpectedly overwritten')
    (args.output / 'runtime_export_report.json').write_text(json.dumps({
        'source': str(args.source), 'source_sha256': original_hash,
        'source_unchanged': unchanged, 'glb': str(path),
        'glb_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'clips': list(CLIPS), 'art_approved': False, 'deformation_approved': False,
    }, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
