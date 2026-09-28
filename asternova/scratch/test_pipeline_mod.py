import bpy
import json
import math
import os
import sys
from mathutils import Matrix, Quaternion, Vector

# 测试用完整的 bake 逻辑，并加入姿态补偿层
MOCAP_JSON = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\work\mocap_dump.json"
QC_DIR = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\scratch\qc_tune"
os.makedirs(QC_DIR, exist_ok=True)

FPS = 30
BONE_MAP = {
	"Hips": "Hip", "Spine": "Waist", "Chest": "Spine01", "UpperChest": "Spine02",
	"Neck": "NeckTwist01", "Head": "Head",
	"LeftShoulder": "L_Clavicle", "RightShoulder": "R_Clavicle",
	"LeftUpperArm": "L_Upperarm", "RightUpperArm": "R_Upperarm",
	"LeftLowerArm": "L_Forearm", "RightLowerArm": "R_Forearm",
	"LeftHand": "L_Hand", "RightHand": "R_Hand",
	"LeftUpperLeg": "L_Thigh", "RightUpperLeg": "R_Thigh",
	"LeftLowerLeg": "L_Calf", "RightLowerLeg": "R_Calf",
	"LeftFoot": "L_Foot", "RightFoot": "R_Foot",
	"LeftToes": "L_ToeBase", "RightToes": "R_ToeBase",
}
BONE_MAP_INV = {v: k for k, v in BONE_MAP.items()}

SRC_PARENTS = {
	"Root": "", "Hips": "Root", "Spine": "Hips", "Chest": "Spine", "UpperChest": "Chest",
	"Neck": "UpperChest", "Head": "Neck",
	"LeftShoulder": "UpperChest", "RightShoulder": "UpperChest",
	"LeftUpperArm": "LeftShoulder", "RightUpperArm": "RightShoulder",
	"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
	"LeftHand": "LeftLowerArm", "RightHand": "RightLowerArm",
	"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips",
	"LeftLowerLeg": "LeftUpperLeg", "RightLowerLeg": "RightUpperLeg",
	"LeftFoot": "LeftLowerLeg", "RightFoot": "RightLowerLeg",
	"LeftToes": "LeftFoot", "RightToes": "RightFoot",
}

def gvec_to_b(v):
    return Vector((v[0], -v[2], v[1]))

def q_from_json(a):
    return Quaternion((a[3], a[0], a[1], a[2]))

def qmul(a, b):
    return Quaternion((
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    ))

data = json.load(open(MOCAP_JSON, encoding="utf-8"))
clips = data["clips"]
tpose = data["tpose"]

src_rest = {}
for lib_key, calib in tpose.items():
    composed = {}
    for bone in SRC_PARENTS:
        parent = SRC_PARENTS[bone]
        local = q_from_json(calib[bone]) if bone in calib else Quaternion()
        composed[bone] = qmul(composed[parent] if parent != "" else Quaternion(), local)
    src_rest[lib_key] = composed

body = bpy.data.objects["Aster_Body"]
arm = bpy.data.objects["Aster_Armature"]
pb_map = {src_bone: arm.pose.bones[dst_bone] for src_bone, dst_bone in BONE_MAP.items()}

dst_rest_rot = {}
dst_rest_local_pos = {}
dst_rest_local_rot = {}
for src_bone, pb in pb_map.items():
    dst_rest_rot[src_bone] = pb.matrix.to_quaternion()
    parent_pb = pb.parent
    if parent_pb is not None:
        inv = parent_pb.matrix.inverted()
        dst_rest_local_pos[src_bone] = (inv @ pb.matrix).to_translation()
        dst_rest_local_rot[src_bone] = (inv @ pb.matrix).to_quaternion()
    else:
        dst_rest_local_pos[src_bone] = pb.matrix.to_translation()
        dst_rest_local_rot[src_bone] = pb.matrix.to_quaternion()

HEAD_CLAMP = {"Head": 0.35, "Neck": 0.40}

TWIST_MAP = {
	"L_UpperarmTwist01": ("L_Upperarm", "L_Forearm", 1.0 / 3.0),
	"L_UpperarmTwist02": ("L_Upperarm", "L_Forearm", 2.0 / 3.0),
	"R_UpperarmTwist01": ("R_Upperarm", "R_Forearm", 1.0 / 3.0),
	"R_UpperarmTwist02": ("R_Upperarm", "R_Forearm", 2.0 / 3.0),
	"L_ForearmTwist01": ("L_Forearm", "L_Hand", 1.0 / 3.0),
	"L_ForearmTwist02": ("L_Forearm", "L_Hand", 2.0 / 3.0),
	"R_ForearmTwist01": ("R_Forearm", "R_Hand", 1.0 / 3.0),
	"R_ForearmTwist02": ("R_Forearm", "R_Hand", 2.0 / 3.0),
	"L_ThighTwist01": ("L_Thigh", "L_Calf", 1.0 / 3.0),
	"L_ThighTwist02": ("L_Thigh", "L_Calf", 2.0 / 3.0),
	"R_ThighTwist01": ("R_Thigh", "R_Calf", 1.0 / 3.0),
	"R_ThighTwist02": ("R_Thigh", "R_Calf", 2.0 / 3.0),
	"L_CalfTwist01": ("L_Calf", "L_Foot", 1.0 / 3.0),
	"L_CalfTwist02": ("L_Calf", "L_Foot", 2.0 / 3.0),
	"R_CalfTwist01": ("R_Calf", "R_Foot", 1.0 / 3.0),
	"R_CalfTwist02": ("R_Calf", "R_Foot", 2.0 / 3.0),
}
twist_pb_map = {}
twist_rest_local_pos = {}
twist_rest_local_rot = {}
twist_rest_global = {}
for _tname, (_p, _c, _k) in TWIST_MAP.items():
    _pb_t = arm.pose.bones.get(_tname)
    twist_pb_map[_tname] = _pb_t
    twist_rest_local_pos[_tname] = (_pb_t.parent.matrix.inverted() @ _pb_t.matrix).to_translation()
    twist_rest_local_rot[_tname] = (_pb_t.parent.matrix.inverted() @ _pb_t.matrix).to_quaternion()
    twist_rest_global[_tname] = _pb_t.matrix.to_quaternion()

_all_order = []
_pending = list(arm.pose.bones)
while _pending:
    progressed = False
    for _pb in list(_pending):
        if _pb.parent is None or _pb.parent.name in _all_order:
            _all_order.append(_pb.name)
            _pending.remove(_pb)
            progressed = True
    if not progressed:
        break
_all_rest_local_rot = {}
_all_rest_local_pos = {}
for _pb in arm.pose.bones:
    if _pb.parent is not None:
        _inv = _pb.parent.matrix.inverted()
        _all_rest_local_rot[_pb.name] = (_inv @ _pb.matrix).to_quaternion()
        _all_rest_local_pos[_pb.name] = (_inv @ _pb.matrix).to_translation()
    else:
        _all_rest_local_rot[_pb.name] = _pb.matrix.to_quaternion()
        _all_rest_local_pos[_pb.name] = _pb.matrix.to_translation()

hip_pb = pb_map["Hips"]
hip_rest_z = hip_pb.matrix.to_translation().z
src_rest_used = src_rest["melee"] if "melee" in src_rest else src_rest["shooter"]

def sample_local_rot(track_keys, t):
    if not track_keys:
        return None
    if t <= track_keys[0][0]:
        return q_from_json(track_keys[0][1:])
    if t >= track_keys[-1][0]:
        return q_from_json(track_keys[-1][1:])
    lo, hi = 0, len(track_keys) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if track_keys[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    k0, k1 = track_keys[lo], track_keys[hi]
    u = (t - k0[0]) / max(1e-9, k1[0] - k0[0])
    return q_from_json(k0[1:]).slerp(q_from_json(k1[1:]), u)

def sample_src_frame(clip, t, lib_rest):
    rot = {}
    composed = {}
    for bone in SRC_PARENTS:
        parent = SRC_PARENTS[bone]
        keys = clip["tracks"].get(bone, {}).get("r")
        local = sample_local_rot(keys, t) if keys else (lib_rest[bone] if bone in lib_rest else Quaternion())
        composed[bone] = qmul(composed[parent] if parent != "" else Quaternion(), local)
        if bone in BONE_MAP:
            rot[bone] = composed[bone]
    hp_keys = clip["tracks"].get("Hips", {}).get("p")
    hips_pos = None
    if hp_keys:
        if t <= hp_keys[0][0]:
            hips_pos = hp_keys[0][1:]
        elif t >= hp_keys[-1][0]:
            hips_pos = hp_keys[-1][1:]
        else:
            lo, hi = 0, len(hp_keys) - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if hp_keys[mid][0] <= t:
                    lo = mid
                else:
                    hi = mid
            k0, k1 = hp_keys[lo], hp_keys[hi]
            u = (t - k0[0]) / max(1e-9, k1[0] - k0[0])
            a, b = k0[1:], k1[1:]
            hips_pos = [a[i] + (b[i] - a[i]) * u for i in range(3)]
    return rot, hips_pos

# ==================== 姿态补偿定义 ====================
# 1. 挺拔前倾补偿：行走与跑步剪辑中，对 Waist 注入 +6.8° 前倾
Q_LEAN_FORWARD = Quaternion(Vector((1.0, 0.0, 0.0)), -math.radians(6.8))

# 2. 双臂舒展补偿（针对待命与常规移动）：
# 右手大臂：从胸前架剑位置向外侧/下方展开约 38°
# 在局部基底上：绕局部轴外展与下垂
# L_Upperarm / R_Upperarm 局部姿态调整
Q_R_UPPER_RELAX = Quaternion(Vector((0.0, 0.3, 0.95)).normalized(), math.radians(38.0))
# 右手小臂微放松伸展
Q_R_FORE_RELAX = Quaternion(Vector((0.0, 0.0, 1.0)), math.radians(-15.0))
# 左手大臂自然下垂搭鞘
Q_L_UPPER_RELAX = Quaternion(Vector((0.0, -0.3, 0.95)).normalized(), math.radians(-25.0))
Q_L_FORE_RELAX = Quaternion(Vector((0.0, 0.0, 1.0)), math.radians(10.0))

LOCOMOTION_CLIPS = {"LightWalking", "LightRunning", "Sprint", "crouch-run"}
ARM_RELAX_CLIPS = {"LightIdle", "idle", "LightWalking", "LightRunning"}

def apply_frame(src_rot, hips_delta_b, clip_name=""):
    grot = {}
    gpos = {}
    dst_global_rot = {}
    for name in _all_order:
        pb = arm.pose.bones[name]
        par = pb.parent
        if par is not None:
            pq = grot[par.name]
            pp = gpos[par.name]
        else:
            pq = Quaternion()
            pp = Vector((0.0, 0.0, 0.0))
        rl_rot = _all_rest_local_rot[name]
        rl_pos = _all_rest_local_pos[name]
        src = BONE_MAP_INV.get(name)
        if src is not None:
            m_b = qmul(dst_rest_rot[src], src_rest_used[src].inverted())
            dg = qmul(m_b, src_rot[src])
            
            # --- 姿态补偿注入 ---
            # 1. 挺拔前倾补偿
            if clip_name in LOCOMOTION_CLIPS and name in ("Waist", "Spine01"):
                dg = qmul(Q_LEAN_FORWARD, dg)

            limit = HEAD_CLAMP.get(src)
            basis = qmul(rl_rot.inverted(), qmul(pq.inverted(), dg))

            # 2. 双臂舒展补偿（局部 basis 调整）
            if clip_name in ARM_RELAX_CLIPS:
                if name == "R_Upperarm":
                    basis = qmul(basis, Q_R_UPPER_RELAX)
                    dg = qmul(pq, qmul(rl_rot, basis))
                elif name == "R_Forearm":
                    basis = qmul(basis, Q_R_FORE_RELAX)
                    dg = qmul(pq, qmul(rl_rot, basis))
                elif name == "L_Upperarm":
                    basis = qmul(basis, Q_L_UPPER_RELAX)
                    dg = qmul(pq, qmul(rl_rot, basis))
                elif name == "L_Forearm":
                    basis = qmul(basis, Q_L_FORE_RELAX)
                    dg = qmul(pq, qmul(rl_rot, basis))

            if limit is not None and basis.angle > limit:
                basis = Quaternion(basis.axis, limit)
            pb.location = rl_pos
            pb.rotation_quaternion = basis
            grot[name] = dg
            gpos[name] = pp + pq @ rl_pos
            dst_global_rot[src] = dg
            dst_global_rot[name] = dg
        elif name in TWIST_MAP:
            grot[name] = qmul(pq, rl_rot)
            gpos[name] = pp + pq @ rl_pos
        else:
            grot[name] = qmul(pq, rl_rot)
            gpos[name] = pp + pq @ rl_pos
    if hips_delta_b is not None:
        hip_pb = pb_map["Hips"]
        root_pb = hip_pb.parent
        root_inv = root_pb.matrix.inverted() if root_pb else Matrix.Identity(4)
        hip_pb.location = hip_pb.location + (root_inv.to_3x3() @ hips_delta_b)
    # 扭骨跟随
    for tname, (p, c, k) in TWIST_MAP.items():
        src_p = BONE_MAP_INV[p]
        src_c = BONE_MAP_INV[c]
        delta_P = qmul(dst_global_rot[p], dst_rest_rot[src_p].inverted())
        delta_C = qmul(dst_global_rot[c], dst_rest_rot[src_c].inverted())
        delta_T = delta_P.slerp(delta_C, k)
        qt = qmul(delta_T, twist_rest_global[tname])
        pb_t = twist_pb_map[tname]
        par_q = grot[pb_t.parent.name]
        basis_t = qmul(twist_rest_local_rot[tname].inverted(),
                       qmul(par_q.inverted(), qt))
        pb_t.location = twist_rest_local_pos[tname]
        pb_t.rotation_quaternion = basis_t
        grot[tname] = qt

# 渲染相机
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1200

def qc_render_cam(tag, out_file, cam_offset):
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = body.evaluated_get(dg)
    corners = [ob_eval.matrix_world @ Vector(c) for c in ob_eval.bound_box]
    center = sum(corners, Vector((0, 0, 0))) / 8.0
    cam_data = bpy.data.cameras.new("CamData")
    cam_data.lens = 50
    cam = bpy.data.objects.new("CamObj", cam_data)
    scene.collection.objects.link(cam)
    cam.location = center + cam_offset
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(QC_DIR, out_file)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data, do_unlink=True)
    print("Rendered:", out_file)

# 烘焙一个测试 clip
def test_bake(clip_name, f_idx):
    clip = clips[clip_name]
    length = float(clip["length"])
    n_frames = max(2, int(round(length * FPS)) + 1)
    hip_keys = clip["tracks"].get("Hips", {}).get("p")
    hip_t0 = hip_keys[0][1:] if hip_keys else None
    hips_scale = hip_rest_z / max(0.2, hip_t0[1]) if hip_t0 else 0.0
    act = bpy.data.actions.new(clip_name)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = act
    for f in range(n_frames):
        t = f / FPS
        src_rot, hips_pos = sample_src_frame(clip, t, src_rest_used)
        hips_delta_b = None
        if hips_pos is not None and hip_t0 is not None:
            d_godot = [(hips_pos[i] - hip_t0[i]) * hips_scale for i in range(3)]
            hips_delta_b = gvec_to_b(d_godot)
        apply_frame(src_rot, hips_delta_b, clip_name)
        for bone, pb in pb_map.items():
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if bone == "Hips":
                pb.keyframe_insert("location", frame=f)
        for pb_t in twist_pb_map.values():
            pb_t.keyframe_insert("rotation_quaternion", frame=f)
    bpy.context.scene.frame_set(f_idx)
    bpy.context.view_layer.update()
    # 渲染正面、侧面、背后
    qc_render_cam("front", f"{clip_name}_front.png", Vector((0.0, 2.3, 0.0)))
    qc_render_cam("side", f"{clip_name}_side.png", Vector((2.3, 0.0, 0.0)))
    qc_render_cam("back", f"{clip_name}_back.png", Vector((0.0, -2.3, 0.0)))

test_bake("LightIdle", 20)
test_bake("LightWalking", 20)
test_bake("LightRunning", 10)

print("ALL_TEST_BAKES_DONE")
