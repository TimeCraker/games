import bpy
import json
import math
import os
import sys
from mathutils import Matrix, Quaternion, Vector

# 加载母带
BLEND_PATH = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\work\aster_assembled_v2.blend"
MOCAP_PATH = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\art\models\work\mocap_dump.json"
OUT_DIR = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova\scratch"

# 引入原烘焙逻辑
data = json.load(open(MOCAP_PATH, encoding="utf-8"))
clips = data["clips"]
tpose = data["tpose"]

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

def q_from_json(a):
    return Quaternion((a[3], a[0], a[1], a[2]))

def qmul(a, b):
    return Quaternion((
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    ))

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
dst_rest_rot = {src_bone: pb.matrix.to_quaternion() for src_bone, pb in pb_map.items()}

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

HEAD_CLAMP = {"Head": 0.35, "Neck": 0.40}
src_rest_used = src_rest["melee"] if "melee" in src_rest else src_rest["shooter"]

# 采样某一帧
def sample_src_frame(clip, t, lib_rest):
    rot = {}
    composed = {}
    for bone in SRC_PARENTS:
        parent = SRC_PARENTS[bone]
        keys = clip["tracks"].get(bone, {}).get("r")
        local = q_from_json(keys[0][1:]) if keys else (lib_rest[bone] if bone in lib_rest else Quaternion())
        composed[bone] = qmul(composed[parent] if parent != "" else Quaternion(), local)
        if bone in BONE_MAP:
            rot[bone] = composed[bone]
    return rot

# 应用帧与补偿测试
def apply_frame_tuned(src_rot, r_upper_offset=None, r_fore_offset=None, l_upper_offset=None, l_fore_offset=None, lean_deg=0.0):
    grot = {}
    gpos = {}
    dst_global_rot = {}
    
    # 挺拔前倾四元数（绕全局 X 轴负向微倾）
    q_lean = Quaternion(Vector((1.0, 0.0, 0.0)), -math.radians(lean_deg)) if lean_deg != 0.0 else None

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
            
            # 躯干前倾
            if q_lean is not None and name in ("Waist", "Spine01"):
                dg = qmul(q_lean, dg)

            limit = HEAD_CLAMP.get(src)
            basis = qmul(rl_rot.inverted(), qmul(pq.inverted(), dg))
            
            # 手臂姿态补偿（局部 basis 层面调整）
            if name == "R_Upperarm" and r_upper_offset is not None:
                basis = qmul(basis, r_upper_offset)
                dg = qmul(pq, qmul(rl_rot, basis))
            elif name == "R_Forearm" and r_fore_offset is not None:
                basis = qmul(basis, r_fore_offset)
                dg = qmul(pq, qmul(rl_rot, basis))
            elif name == "L_Upperarm" and l_upper_offset is not None:
                basis = qmul(basis, l_upper_offset)
                dg = qmul(pq, qmul(rl_rot, basis))
            elif name == "L_Forearm" and l_fore_offset is not None:
                basis = qmul(basis, l_fore_offset)
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

    # 扭骨插值
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

# 相机与渲染设置
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1200

def render_view(cam_pos, look_at, out_name):
    cam_data = bpy.data.cameras.new("TestCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("TestCamObj", cam_data)
    scene.collection.objects.link(cam)
    cam.location = cam_pos
    cam.rotation_euler = (look_at - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT_DIR, out_name)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.cameras.remove(cam_data, do_unlink=True)
    print("Rendered:", out_name)

# 采样 LightIdle
clip = clips["LightIdle"]
src_rot = sample_src_frame(clip, 0.5, src_rest_used)

# 测试几种右手大臂旋转
# 右大臂局部轴：需要向外/下方展开约 35° ~ 40°
# 测试 1: 基准（无补偿）
apply_frame_tuned(src_rot)
bpy.context.view_layer.update()
render_view(Vector((0.0, 2.2, 1.0)), Vector((0.0, 0.0, 0.9)), "test_idle_front_orig.png")
render_view(Vector((1.8, -1.2, 1.0)), Vector((0.0, 0.0, 0.9)), "test_idle_side_orig.png")

print("TUNE_DONE")
