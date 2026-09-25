extends SceneTree
## Aster 动作库重定向构建器（无头运行）：
##   godot --headless --path client-godot-v2 -s scripts/animation/build_aster_animlib.gd
## 将 MeleeLib/ShooterLib（SkeletonProfileHumanoid 标准骨名）一键重定向到 Aster 43 骨。
## 精确全局空间重定向（Godot 4 官方规范）：
##   Delta_g(b) = S_g(b) · S_gr(b)⁻¹
##   dst_global(b) = Delta_g(b) · D_gr(b)
##   q_pose(b) = D_lr(b)⁻¹ · [dst_global(parent)⁻¹ · dst_global(b)]
## 输出 res://art/animations/aster_animlib.res。

const OUT_PATH := "res://art/animations/aster_animlib.res"

var _aster_scene_root: Node = null

# SkeletonProfileHumanoid 标准骨名 -> Aster 43 骨名（依据 glb 骨骼层级）
const BONE_MAP := {
	"Root": "Root",
	"Hips": "Hip",
	"Spine": "Waist",
	"Chest": "Spine01",
	"UpperChest": "Spine02",
	"Neck": "NeckTwist01",
	"Head": "Head",
	"LeftShoulder": "L_Clavicle", "RightShoulder": "R_Clavicle",
	"LeftUpperArm": "L_Upperarm", "RightUpperArm": "R_Upperarm",
	"LeftLowerArm": "L_Forearm", "RightLowerArm": "R_Forearm",
	"LeftHand": "L_Hand", "RightHand": "R_Hand",
	"LeftUpperLeg": "L_Thigh", "RightUpperLeg": "R_Thigh",
	"LeftLowerLeg": "L_Calf", "RightLowerLeg": "R_Calf",
	"LeftFoot": "L_Foot", "RightFoot": "R_Foot",
	"LeftToes": "L_ToeBase", "RightToes": "R_ToeBase",
}

# 源骨架（SkeletonProfileHumanoid 标准骨名）父子结构，用于计算源全局 rest
const SRC_PARENTS := {
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

# 循环播放剪辑
const LOOP_CLIPS := [
	"idle", "walk", "run_067", "crouch-idle", "crouch-run", "fall", "fall-landing",
	"idle-guard", "sneak-idle", "sneak-walk", "sneak-run", "strafe-l", "strafe-r",
	"wall-slide-front", "wall-slide-back", "wall-back-idle",
	"LightIdle", "LightWalking", "LightRunning", "Sprint",
	"HeavyIdle", "HeavyWalking", "HeavyRunning", "Guarding", "HurtIdle",
]

const SKIP_PREFIX := "root-"


func _initialize() -> void:
	var aster_skel: Skeleton3D = _load_aster_skeleton()
	if aster_skel == null:
		quit(1)
		return
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var src_rest_q := _build_source_global_rests(melee_lib, shooter_lib)
	var dst_rest_q := {}
	var dst_rest_local_q := {}
	var dst_rest_pos := {}
	for src_bone: String in BONE_MAP:
		var dst_bone: String = BONE_MAP[src_bone]
		var idx := aster_skel.find_bone(dst_bone)
		if idx < 0:
			push_error("Aster 缺少目标骨骼: " + dst_bone)
			quit(1)
			return
		var gt := aster_skel.get_bone_global_rest(idx)
		var lt := aster_skel.get_bone_rest(idx)
		dst_rest_q[src_bone] = gt.basis.get_rotation_quaternion()
		dst_rest_local_q[src_bone] = lt.basis.get_rotation_quaternion()
		dst_rest_pos[src_bone] = gt.origin
	var hips_scale: float = dst_rest_pos["Hips"].length() / float(src_rest_q["_hips_len"])
	var root_rest_off: Vector3 = dst_rest_pos["Root"]
	print("Aster skeleton=%s bones=%d hips_rest=%.4f m hips_scale=%.4f root_off=%s" % [
		aster_skel.name, aster_skel.get_bone_count(), dst_rest_pos["Hips"].length(), hips_scale, root_rest_off])

	var out_lib := AnimationLibrary.new()
	var total_tracks := 0
	for lib_entry in [[melee_lib, src_rest_q["melee"]], [shooter_lib, src_rest_q["shooter"]]]:
		var src_lib: AnimationLibrary = lib_entry[0]
		var s_gr: Dictionary = lib_entry[1]
		var converted := 0
		for anim_name in src_lib.get_animation_list():
			if anim_name.begins_with(SKIP_PREFIX):
				continue
			if out_lib.has_animation(anim_name):
				push_warning("重名跳过: " + anim_name)
				continue
			var out_anim := _retarget_anim(src_lib.get_animation(anim_name), s_gr,
					dst_rest_q, dst_rest_local_q, aster_skel.name, anim_name)
			if out_anim == null:
				continue
			if anim_name in LOOP_CLIPS:
				out_anim.loop_mode = Animation.LOOP_LINEAR
			out_lib.add_animation(anim_name, out_anim)
			total_tracks += out_anim.get_track_count()
			converted += 1
		print("%s -> %d clips" % [src_lib.resource_path.get_file(), converted])

	if not _validate_tpose(out_lib, aster_skel):
		push_error("TPose FK 自洽验证 FAIL —— 拒绝保存，检查源 rest 标定")
		quit(1)
		return

	var err := ResourceSaver.save(out_lib, OUT_PATH)
	print("saved %s clips=%d tracks=%d err=%d" % [
		OUT_PATH, out_lib.get_animation_list().size(), total_tracks, err])
	quit(0 if err == OK else 1)

func _load_aster_skeleton() -> Skeleton3D:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var found := inst.find_children("*", "Skeleton3D", true, false)
	if found.is_empty():
		push_error("glb 内未找到 Skeleton3D")
		return null
	var skel: Skeleton3D = found[0]
	_aster_scene_root = inst
	var chain := skel.get_parent()
	var up := ""
	while chain != null and chain != inst:
		up = String(chain.name) + "/" + up
		chain = chain.get_parent()
	print("skeleton path under glb root: %s%s" % [up, skel.name])
	return skel


func _build_source_global_rests(melee_lib: AnimationLibrary, shooter_lib: AnimationLibrary) -> Dictionary:
	var out := {"shooter": {}, "melee": {}}
	for lib_key in [["shooter", shooter_lib, "tpose"], ["melee", melee_lib, "TPose"]]:
		var s_gr_local := {}
		var calib: Animation = null
		for anim_name in lib_key[1].get_animation_list():
			if anim_name.to_lower() == String(lib_key[2]).to_lower():
				calib = lib_key[1].get_animation(anim_name)
				break
		if calib == null:
			push_error("源 rest 剪辑缺失（TPose/tpose）: " + str(lib_key[2]))
			continue
		for t: int in calib.get_track_count():
			if calib.track_get_type(t) != Animation.TYPE_ROTATION_3D:
				continue
			var bone := String(calib.track_get_path(t).get_subname(0))
			if bone in SRC_PARENTS:
				s_gr_local[bone] = calib.rotation_track_interpolate(t, 0.0)
		var composed: Dictionary = out[lib_key[0]]
		for src_bone: String in SRC_PARENTS:
			var parent: String = SRC_PARENTS[src_bone]
			var local := _safe(s_gr_local.get(src_bone, Quaternion.IDENTITY))
			composed[src_bone] = (composed[parent] if parent != "" else Quaternion.IDENTITY) * local
	out["_hips_len"] = 1.0
	return out


func _validate_tpose(out_lib: AnimationLibrary, aster_skel: Skeleton3D) -> bool:
	var wrapper := Node3D.new()
	var skel := Skeleton3D.new()
	wrapper.add_child(skel)
	root.add_child(wrapper)
	for i: int in aster_skel.get_bone_count():
		var nm := aster_skel.get_bone_name(i)
		var parent := aster_skel.get_bone_parent(i)
		var idx := skel.add_bone(nm)
		if parent >= 0:
			skel.set_bone_parent(idx, skel.find_bone(aster_skel.get_bone_name(parent)))
		skel.set_bone_rest(idx, aster_skel.get_bone_rest(i))
	skel.reset_bone_poses()
	var player := AnimationPlayer.new()
	wrapper.add_child(player)
	player.root_node = NodePath("..")
	player.add_animation_library("x", out_lib)
	var tpose_name := ""
	for anim_name in out_lib.get_animation_list():
		if anim_name.to_lower() == "tpose":
			tpose_name = anim_name
			break
	if tpose_name == "":
		push_error("输出库中无 TPose 剪辑，无法自洽验证")
		root.remove_child(wrapper)
		wrapper.free()
		return false
	player.play("x/" + tpose_name)
	player.advance(0.0)
	
	var worst_deg := 0.0
	var worst_bone := ""
	for i: int in aster_skel.get_bone_count():
		var bname := aster_skel.get_bone_name(i)
		var idx := skel.find_bone(bname)
		var q_pose_g := skel.get_bone_global_pose(idx).basis.get_rotation_quaternion()
		var q_rest_g := aster_skel.get_bone_global_rest(i).basis.get_rotation_quaternion()
		var dot: float = absf(q_pose_g.dot(q_rest_g))
		var deg := rad_to_deg(2.0 * acos(minf(dot, 1.0)))
		if deg > worst_deg:
			worst_deg = deg
			worst_bone = bname
	var rest_ok := worst_deg < 0.6
	print("  TPose==rest 全局姿态最大偏差: %.4f° @ %s -> %s" % [worst_deg, worst_bone, "OK" if rest_ok else "FAIL"])

	root.remove_child(wrapper)
	wrapper.free()
	return rest_ok


func _retarget_anim(src: Animation, s_gr: Dictionary, dst_rest_q: Dictionary,
		dst_rest_local_q: Dictionary, skel_name: StringName, anim_name: String = "") -> Animation:
	var out := Animation.new()
	out.length = src.length
	out.step = src.step
	out.loop_mode = src.loop_mode

	var src_track := {}
	for t: int in src.get_track_count():
		if src.track_get_type(t) != Animation.TYPE_ROTATION_3D:
			continue
		var bone := String(src.track_get_path(t).get_subname(0))
		if BONE_MAP.has(bone) and bone != "Root":
			src_track[bone] = t
	var order: Array[String] = []
	for pass_i in range(8):
		for bone: String in SRC_PARENTS:
			if not src_track.has(bone) or bone in order:
				continue
			var parent: String = SRC_PARENTS[bone]
			if parent == "" or not src_track.has(parent) or parent in order:
				order.append(bone)
		if order.size() == src_track.size():
			break

	for bone in order:
		var tb: int = src_track[bone]
		var parent: String = SRC_PARENTS[bone]
		var ancestors: Array[String] = []
		var walk: String = parent
		while walk != "":
			ancestors.push_front(walk)
			walk = SRC_PARENTS[walk]
		var nt := out.add_track(Animation.TYPE_ROTATION_3D)
		out.track_set_path(nt, NodePath("%s:%s" % [skel_name, BONE_MAP[bone]]))
		for k: int in src.track_get_key_count(tb):
			var time: float = src.track_get_key_time(tb, k)
			# 1. 源全局姿态：从根到父逐级合成
			var sg_parent := Quaternion.IDENTITY
			for a in ancestors:
				if src_track.has(a):
					sg_parent = sg_parent * _safe(src.rotation_track_interpolate(src_track[a], time))
			var sg_bone := sg_parent * _safe(src.rotation_track_interpolate(tb, time))

			# 2. 骨骼真实全局 Delta：Delta_g = S_g · S_gr⁻¹
			var delta_bone := _safe(sg_bone * _safe(s_gr[bone]).inverse())
			var dst_bone_global := _safe(delta_bone * dst_rest_q[bone])
			
			# 3. 目标局部旋转：q_pose = dst_rest_local⁻¹ · [dst_parent_global⁻¹ · dst_bone_global]
			var q_parent_rel: Quaternion
			if parent != "":
				var delta_parent := _safe(sg_parent * _safe(s_gr[parent]).inverse())
				var dst_parent_global := _safe(delta_parent * dst_rest_q[parent])
				q_parent_rel = _safe(dst_parent_global.inverse() * dst_bone_global)
			else:
				q_parent_rel = dst_bone_global

			# 扣除骨骼自身的 rest_local，得到纯净的 pose_local 旋转增量
			var q_key := _safe(dst_rest_local_q[bone].inverse() * q_parent_rel)

			out.rotation_track_insert_key(nt, time, q_key)

	return out

func _safe(q: Quaternion) -> Quaternion:
	return q.normalized() if q.length_squared() > 0.5 else Quaternion.IDENTITY
