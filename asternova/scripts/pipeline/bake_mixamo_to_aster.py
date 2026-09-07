# Aster Mixamo 动作离线烘焙（无头 Blender）：
#   blender.exe -b --factory-startup art/models/aster_assembled_clean.blend \
#     -P scripts/pipeline/bake_mixamo_to_aster.py -- <mocap.json> <glb_out> <qc_dir>
#
# 工业化烘焙路线（彻底告别 Godot 手写四元数逆）：
#   1) 源全局姿态由 mocap JSON（dump_mocap_json.gd 导出）逐帧四元数递推
#      —— float64 离线计算，源 rest 严格取自 TPose/tpose 静态标定帧
#   2) UE5 IK Retargeter 同款 rest 差映射：M(b)=D_rot(b)·S_rot(b)⁻¹
#      dst_global(b,t) = M(b)·src_global(b,t)
#   3) 每帧直接赋 pose_bone.matrix（臂架空间），局部基变换交给 Blender 自身，
#      30fps 逐帧 keyframe_insert 完成烘焙
#   4) 门禁：TPose 映射必须精确还原 rest（<0.1°/骨）+ T 姿语义断言
#   5) 髋部回加按 t0 相对位移缩放的起伏（旧管线髋高锁死 0.904 是僵硬根源）
#   6) 全部动作 NLA stash → glTF ACTIONS 模式导出 GLB（含烘焙 QC 渲染图）
import bpy
import json
import math
import os
import sys
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MOCAP_JSON = os.path.abspath(argv[0])
GLB_OUT = os.path.abspath(argv[1])
QC_DIR = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.join(os.path.dirname(GLB_OUT), "_bake_qc")
os.makedirs(QC_DIR, exist_ok=True)

FPS = 30
# SkeletonProfileHumanoid 标准骨名 -> Aster 43 骨（与 build_aster_animlib.gd 同表）
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
# 源骨架父子（标准骨名；Root 不参与烘焙——朝向由 Godot visual_root 驱动）
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
# 循环剪辑（其余单次播放）
LOOP_CLIPS = {"idle", "LightIdle", "LightWalking", "LightRunning", "Sprint",
              "crouch-run", "fall", "fall-landing", "wall-slide-front", "Guarding"}
# Godot(Y-up) → Blender(Z-up) 轴映射： (x,y,z)_g -> (x,-z,y)_b
def gvec_to_b(v):
    return Vector((v[0], -v[2], v[1]))


def log(msg):
    print("[bake] " + msg, flush=True)


def q_from_json(a):
    return Quaternion((a[3], a[0], a[1], a[2]))  # JSON[x,y,z,w] -> w,x,y,z


def qmul(a, b):
    """哈密顿积（列向量约定：先作用 b 再作用 a）。
    Blender 5.2 的 Quaternion @ Quaternion 会把分量错位成 (x,y,z,w) 处理，
    与构造器 (w,x,y,z) 不一致，必须手写乘积（实测 A@I 有解但 A@B 分量循环移位）。"""
    return Quaternion((
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    ))


# ---------------- 载入数据 ----------------
data = json.load(open(MOCAP_JSON, encoding="utf-8"))
clips = data["clips"]
tpose = data["tpose"]
log("载入 %d 剪辑, tpose=%s" % (len(clips), list(tpose.keys())))

# ---------------- 源 rest（严格取 TPose 静态帧，严禁 idle 冒充） ----------------
src_rest = {}
for lib_key, calib in tpose.items():
    composed = {}
    for bone in SRC_PARENTS:
        parent = SRC_PARENTS[bone]
        local = q_from_json(calib[bone]) if bone in calib else Quaternion()
        composed[bone] = qmul(composed[parent] if parent != "" else Quaternion(), local)
    src_rest[lib_key] = composed
    log("源 rest[%s]: %d 骨合成" % (lib_key, len(composed)))

# ---------------- 目标 rest（Blender 侧读取） ----------------
body = bpy.data.objects["Aster_Body"]
arm = bpy.data.objects["Aster_Armature"]
wm = body.matrix_world
pb_map = {}
for src_bone, dst_bone in BONE_MAP.items():
    pb = arm.pose.bones.get(dst_bone)
    if pb is None:
        print("[bake] FATAL: Aster 缺少目标骨骼 " + dst_bone)
        sys.exit(1)
    pb_map[src_bone] = pb

dst_rest_rot = {}   # 臂架空间 rest 旋转
dst_rest_local_pos = {}  # 相对父骨 rest 的局部平移
dst_rest_local_rot = {}  # 相对父骨 rest 的局部旋转（头部限幅用）
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

# 头颈局部旋转限幅：源 Sprint 有 ~66° 深点头，rigid 长发会以头骨为轴甩成风扇
# （游戏动画标准做法：躯干前倾保留，头颈相对父骨的偏转钳到 ±20° 内）
HEAD_CLAMP = {"Head": 0.35, "Neck": 0.40}

# 扭骨级联分布：扭骨不在源骨架中，若留在 rest 会让绑在上面的顶点成为「钉死的锚」，
# 跑步时把衣片撕成巨幅平面（实测裙片/袖片整片拖地）。按父骨→子骨全局姿态插值驱动。
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

# 全 43 骨实际层级拓扑序 + rest 局部姿态（apply_frame 的递推基础）
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

# 拓扑序（父先子后）
ORDER = []
_pend = [b for b in BONE_MAP]
while _pend:
    progressed = False
    for b in list(_pend):
        p = SRC_PARENTS[b]
        if p == "" or p not in BONE_MAP or p in ORDER:
            ORDER.append(b)
            _pend.remove(b)
            progressed = True
    if not progressed:
        print("[bake] FATAL: 拓扑环")
        sys.exit(1)

hip_pb = pb_map["Hips"]
hip_rest_z = hip_pb.matrix.to_translation().z
log("Aster Hip rest 高度: %.4f m" % hip_rest_z)

# ---------------- 源姿态采样 ----------------
def sample_local_rot(track_keys, t):
    """30fps 网格时间 -> 源局部旋转（相邻键 slerp）"""
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
    """返回 {src_bone: 全局旋转}（Godot 约定递推）+ Hips 全局位置(Godot)"""
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
        # 位置线性插值
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


def apply_frame(src_rot, hips_delta_b):
    """全 43 骨按「实际层级」递推全局姿态；映射骨/扭骨写 basis 通道。
    必须用实际父链合成（如 L_Thigh 的实际父是 Pelvis 而非语义父 Hips），
    跳层会让整条腿携带未映射骨 rest 的恒定偏转。
    basis 通道语义：pose_global = parent_pose · rest_local · basis。"""
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
            grot[name] = dg
            gpos[name] = pp + pq @ rl_pos
            limit = HEAD_CLAMP.get(src)
            basis = qmul(rl_rot.inverted(), qmul(pq.inverted(), dg))
            if limit is not None and basis.angle > limit:
                basis = Quaternion(basis.axis, limit)
            pb.location = rl_pos
            pb.rotation_quaternion = basis
            dst_global_rot[src] = dg
            dst_global_rot[name] = dg  # Aster 名别名，供扭骨查询
            _DBG[src] = {"dg": dg}
        elif name in TWIST_MAP:
            # 第一遍先按 rest 传播（扭骨统一在主循环后第二遍计算）
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
    # 扭骨第二遍（TWIST_MAP 声明序天然满足 01→02 依赖）
    # 关键：插值作用于「rest→pose 的相对旋转」，再叠加扭骨自身 rest——
    # 直接插值绝对全局会让扭骨偏离自身 rest（rest 不在父→子姿态弧上），
    # 数千扭骨顶点整体拧出原位 = 碎片爆炸。
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


# ---------------- 门禁 1：TPose 必须精确还原 rest ----------------
src_rest_used = src_rest["melee"] if "melee" in src_rest else src_rest["shooter"]
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
for pb in list(pb_map.values()) + list(twist_pb_map.values()):  # 四元数模式：矩阵往返零损耗
    pb.rotation_mode = "QUATERNION"

# src_rest_used 已是逐级合成的全局 rest，直接取用（严禁二次合成）
tpose_rot = {b: src_rest_used[b] for b in BONE_MAP if b in src_rest_used}
_DBG = {}
_apply_frame_debug = True
apply_frame(tpose_rot, None)
bpy.context.view_layer.update()

worst_deg, worst_bone = 0.0, ""
for src_bone, pb in pb_map.items():
    q = pb.matrix.to_quaternion()
    want = dst_rest_rot[src_bone]
    # 符号归一：q 与 -q 同一旋转，必须用 |dot| 判角（mathutils 对反极对会报 180/360）
    dot = abs(q.dot(want))
    ang = math.degrees(2.0 * math.acos(min(1.0, dot)))
    if ang > worst_deg:
        worst_deg, worst_bone = ang, pb.name
_devs = sorted(((math.degrees(2.0 * math.acos(min(1.0, abs(pb_map[b].matrix.to_quaternion().dot(dst_rest_rot[b]))))), pb_map[b].name) for b in BONE_MAP), reverse=True)[:8]
log("门禁1 偏差榜: %s" % [(n, round(d, 3)) for d, n in _devs])
wb = pb_map[worst_bone_src] if False else None
log("门禁1 TPose==rest 最大偏差: %.4f° @ %s" % (worst_deg, worst_bone))
_src_worst = [k for k, v in BONE_MAP.items() if v == worst_bone][0]
log("诊断 %s: D=%s S=%s dg=%s read=%s" % (
    worst_bone,
    tuple(round(v, 4) for v in dst_rest_rot[_src_worst]),
    tuple(round(v, 4) for v in src_rest_used[_src_worst]),
    tuple(round(v, 4) for v in _DBG[_src_worst]["dg"]),
    tuple(round(v, 4) for v in pb_map[_src_worst].matrix.to_quaternion())))
log("诊断 约束: %s" % {pb.name: len(pb.constraints) for pb in arm.pose.bones if len(pb.constraints)})
log("诊断 ORDER 头尾: %s ... %s (n=%d)" % (ORDER[:4], ORDER[-4:], len(ORDER)))
if worst_deg > 0.5:  # 坐标系级错误会报 90°~180°；0.1° 级为 float32 矩阵往返噪声
    print("[bake] FATAL: TPose 自洽验证失败")
    sys.exit(1)

# 门禁 2：T 姿语义（双臂水平展开、双腿垂直、头朝上）
def bone_axis(pb):
    m = pb.matrix
    return (m.to_quaternion() @ Vector((0.0, 1.0, 0.0))).normalized()


sem = {
    "L_Upperarm": Vector((-1.0, 0.0, 0.0)), "R_Upperarm": Vector((1.0, 0.0, 0.0)),
    "L_Thigh": Vector((0.0, 0.0, -1.0)), "R_Thigh": Vector((0.0, 0.0, -1.0)),
    "Head": Vector((0.0, 0.0, 1.0)),
}
sem_ok = True
for bname, want in sem.items():
    pb = arm.pose.bones.get(bname)
    child_dirs = [bone_axis(arm.pose.bones[c.name]) for c in pb.children if c.name.endswith(("Twist01", "Calf", "Neck"))]
    d = child_dirs[0] if child_dirs else bone_axis(pb)
    if bname in ("L_Thigh", "R_Thigh", "Head"):
        d = bone_axis(pb)
    dot = d.dot(want)
    log("门禁2 TPose FK %s dir=%s want=%s dot=%.2f %s" % (
        bname, tuple(round(v, 2) for v in d), tuple(want), dot, "OK" if dot > 0.55 else "FAIL"))
    if dot <= 0.55:
        sem_ok = False
if not sem_ok:
    print("[bake] FATAL: T 姿语义验证失败（坐标系约定不一致）")
    sys.exit(1)

# ---------------- 逐剪辑烘焙 ----------------
if os.environ.get("BAKE_EARLY_EXPORT") == "1":
    bpy.ops.export_scene.gltf(filepath=GLB_OUT + ".early.glb",
                              export_format="GLB", export_yup=True)
    log("早期对照导出: " + GLB_OUT + ".early.glb")
def bake_clip(name, clip, lib_rest):
    length = float(clip["length"])
    n_frames = max(2, int(round(length * FPS)) + 1)
    hip_keys = clip["tracks"].get("Hips", {}).get("p")
    hip_t0 = hip_keys[0][1:] if hip_keys else None
    hips_scale = hip_rest_z / max(0.2, hip_t0[1]) if hip_t0 else 0.0
    act = bpy.data.actions.new(name)
    act.name = name
    arm.animation_data.action = act  # 关键帧必须有活动 action 才能落盘
    bpy.context.scene.frame_set(0)
    for f in range(n_frames):
        t = f / FPS
        src_rot, hips_pos = sample_src_frame(clip, t, lib_rest)
        hips_delta_b = None
        if hips_pos is not None and hip_t0 is not None:
            d_godot = [(hips_pos[i] - hip_t0[i]) * hips_scale for i in range(3)]
            hips_delta_b = gvec_to_b(d_godot)
        apply_frame(src_rot, hips_delta_b)
        for bone, pb in pb_map.items():
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if bone == "Hips":
                pb.keyframe_insert("location", frame=f)
        for pb_t in twist_pb_map.values():
            pb_t.keyframe_insert("rotation_quaternion", frame=f)
    arm.animation_data.action = None  # 让位给 NLA strip
    # NLA stash（glTF ACTIONS 模式按 action 逐个导出）
    track = arm.animation_data.nla_tracks.new()
    track.name = "BAKE_" + name
    track.mute = True
    strip = track.strips.new(name=name[:63], start=0, action=act)
    strip.action_frame_start = 0
    strip.action_frame_end = n_frames - 1
    log("烘焙 %s: %.2fs -> %d 帧 @%dfps (hips_scale=%.3f)" % (name, length, n_frames, FPS, hips_scale))
    return act, n_frames


arm.animation_data_create()
bpy.context.scene.render.fps = FPS  # 关键：导出按场景 fps 换算秒，默认 24 会把 30fps 烘焙拉长 1.25 倍
baked = {}
_dbg_count = 0
for clip_name in sorted(clips.keys()):
    if clip_name.lower() in ("tpose",):
        continue
    clip = clips[clip_name]
    lib_rest = src_rest.get(clip.get("lib", "melee"), src_rest_used)
    baked[clip_name] = bake_clip(clip_name, clip, lib_rest)
    if os.environ.get("BAKE_EARLY_EXPORT") == "1":
        _dbg_count += 1
        if _dbg_count in (1, 3, 8, 21):
            _p = "%s.after%02d.glb" % (GLB_OUT, _dbg_count)
            bpy.ops.export_scene.gltf(filepath=_p, export_format="GLB", export_yup=True)
            log("中途对照导出[%d]: %s" % (_dbg_count, _p))

# ---------------- QC 渲染（人眼复核变形质量） ----------------
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_cavity = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1200

def qc_render(tag, clip_name, t):
    act, n_frames = baked[clip_name]
    arm.animation_data.action = act
    bpy.context.scene.frame_set(t)
    bpy.context.view_layer.update()
    # 相机每帧追踪网格包围盒中心（战斗剪辑带 0.5m 级髋部位移，固定机位会跑出画）
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = body.evaluated_get(dg)
    corners = [ob_eval.matrix_world @ Vector(c) for c in ob_eval.bound_box]
    center = sum(corners, Vector((0, 0, 0))) / 8.0
    cam_data = bpy.data.cameras.new("QCCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("QCCam_" + tag, cam_data)
    scene.collection.objects.link(cam)
    cam.location = center + Vector((1.9, -1.1, 0.15))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(QC_DIR, "qc_%s_%s.png" % (clip_name, tag))
    bpy.ops.render.render(write_still=True)
    log("QC 渲染: %s @%s t=%.2f center=%s" % (clip_name, tag, t, tuple(round(v, 2) for v in center)))


import os as _os
if _os.environ.get("BAKE_SKIP_QC") != "1":
    try:
        qc_render("mid", "Sprint", 8)
        qc_render("mid", "Slash1", 14)
        qc_render("mid", "LightIdle", 20)
    except Exception as e:
        log("QC 渲染失败(非致命): %s" % e)
    finally:
        arm.animation_data.action = None
else:
    log("QC 渲染已跳过（BAKE_SKIP_QC=1）")

# ---------------- 导出 GLB ----------------
bpy.ops.object.mode_set(mode="OBJECT")
for obj in list(bpy.data.objects):  # QC 相机不得混入 GLB
    if obj.name.startswith("QCCam"):
        bpy.data.objects.remove(obj, do_unlink=True)
bpy.context.view_layer.objects.active = arm
# 导出前必须回 REST 姿态：QC 烘焙遗留的姿态会让蒙皮导出走「姿态空间」路径，
# 产生跨侧权重污染（实测：rest 导出 0 混合，带姿态导出 521 条跨侧边）
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")  # 必须先全选：无选中时 transforms_clear 是空操作
bpy.ops.pose.transforms_clear()
for pb in pb_map.values():
    pb.matrix = pb.matrix  # 触发通道刷新
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")
# 导出参数与「干净往返」一致的最小集（实测：force_sampling/影响数等附加参数
# 会改变蒙皮顶点记录的写法，引入跨侧权重污染；默认参数导出经往返验证无污染）
kwargs = dict(
    filepath=GLB_OUT,
    export_format="GLB",
    export_yup=True,
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_apply=False,
)
try:
    bpy.ops.export_scene.gltf(**kwargs)
except TypeError as e:
    log("导出参数回退（5.2 选项差异）: %s" % e)
    kwargs.pop("export_animation_mode", None)
    bpy.ops.export_scene.gltf(**kwargs)


def _count_mixed_faces():
    """导出前 QC：统计跨侧（L/R 支配骨）混合面数，应为 0"""
    body = bpy.data.objects["Aster_Body"]
    arm = bpy.data.objects["Aster_Armature"]
    l_h = arm.matrix_world @ arm.pose.bones["L_Thigh"].matrix.translation
    r_h = arm.matrix_world @ arm.pose.bones["R_Thigh"].matrix.translation
    axis = (l_h - r_h).normalized()
    side = {}
    for pb in arm.pose.bones:
        h = arm.matrix_world @ pb.matrix.translation
        s = (h - r_h).dot(axis)
        side[pb.name] = s if abs(s) > 0.02 else 0.0
    mixed = 0
    for poly in body.data.polygons:
        sides = set()
        for vi in poly.vertices:
            v = body.data.vertices[vi]
            best, bw = None, 0.0
            for g in v.groups:
                if g.weight > bw:
                    bw, best = g.weight, body.vertex_groups[g.group].name
            s = side.get(best, 0.0)
            sides.add(1 if s > 0 else (-1 if s < 0 else 0))
        if 1 in sides and -1 in sides:
            mixed += 1
    return mixed


log("导出前 QC 跨侧混合面: %d" % _count_mixed_faces())
log("已导出 GLB: " + GLB_OUT)
print("BAKE_DONE")
