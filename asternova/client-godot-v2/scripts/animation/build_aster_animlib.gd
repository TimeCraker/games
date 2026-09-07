extends SceneTree
## Aster 动作库重定向构建器（无头运行）：
##   godot --headless --path client-godot-v2 -s scripts/animation/build_aster_animlib.gd
## 将 MeleeLib/ShooterLib（SkeletonProfileHumanoid 标准骨名）一键重定向到 Aster 43 骨。
## 精确全局空间重定向（UE5 IK Retargeter 同款）：
##   M(b) = D_gr(b) · S_gr(b)⁻¹；  q_out = [M(parent)·src_global(parent,t)]⁻¹ · M(b)·src_global(b,t)
## 源 rest S_gr 严格取自源库内 TPose（MeleeLib）/ tpose（ShooterLib）静态帧 —— 严禁用
## idle 冒充 rest（会注入 50°~70° 初始残差，导致仰躺/前伸腿/腿相位错乱）。
## 输出 res://art/animations/aster_animlib.res。

const OUT_PATH := "res://art/animations/aster_animlib.res"

var _aster_scene_root: Node = null  # 持有 glb 实例，防止 Skeleton3D 被连带释放

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

# 循环播放剪辑（其余保持源 loop 设置）
const LOOP_CLIPS := [
	"idle", "walk", "run_067", "crouch-idle", "crouch-run", "fall", "fall-landing",
	"idle-guard", "sneak-idle", "sneak-walk", "sneak-run", "strafe-l", "strafe-r",
	"wall-slide-front", "wall-slide-back", "wall-back-idle",
	"LightIdle", "LightWalking", "LightRunning", "Sprint",
	"HeavyIdle", "HeavyWalking", "HeavyRunning", "Guarding", "HurtIdle",
]

const SKIP_PREFIX := "root-"  # root-motion 变体不收


func _initialize() -> void:
	var aster_skel: Skeleton3D = _load_aster_skeleton()
	if aster_skel == null:
		quit(1)
		return
	var melee_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var shooter_lib: AnimationLibrary = load("res://art/animations/ShooterLib.res")
	var src_rest_q := _build_source_global_rests(melee_lib, shooter_lib)
	var dst_rest_q := {}
	var dst_rest_pos := {}
	for src_bone: String in BONE_MAP:
		var dst_bone: String = BONE_MAP[src_bone]
		var idx := aster_skel.find_bone(dst_bone)
		if idx < 0:
			push_error("Aster 缺少目标骨骼: " + dst_bone)
			quit(1)
			return
		var gt := aster_skel.get_bone_global_rest(idx)
		dst_rest_q[src_bone] = gt.basis.get_rotation_quaternion()
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
					dst_rest_q, aster_skel.name)
			if out_anim == null:
				continue
			if anim_name in LOOP_CLIPS:
				out_anim.loop_mode = Animation.LOOP_LINEAR
			out_lib.add_animation(anim_name, out_anim)
			total_tracks += out_anim.get_track_count()
			converted += 1
		print("%s -> %d clips" % [src_lib.resource_path.get_file(), converted])

	# 保存前 FK 自洽门禁：重定向后的 TPose 必须精确还原 Aster rest（含左右语义）
	if not _validate_tpose(out_lib, aster_skel):
		push_error("TPose FK 自洽验证 FAIL —— 拒绝保存，检查源 rest 标定")
		quit(1)
		return

	var err := ResourceSaver.save(out_lib, OUT_PATH)
	print("saved %s clips=%d tracks=%d err=%d" % [
		OUT_PATH, out_lib.get_animation_list().size(), total_tracks, err])
	quit(0 if err == OK else 1)

func _load_aster_skeleton() -> Skeleton3D:
	var scene: PackedScene = load("res://models/aster/aster_assembled.glb")
	var inst: Node = scene.instantiate()
	var found := inst.find_children("*", "Skeleton3D", true, false)
	if found.is_empty():
		push_error("glb 内未找到 Skeleton3D")
		return null
	var skel: Skeleton3D = found[0]
	_aster_scene_root = inst  # 不 free：skeleton 生命周期挂在实例上
	var chain := skel.get_parent()
	var up := ""
	while chain != null and chain != inst:
		up = String(chain.name) + "/" + up
		chain = chain.get_parent()
	print("skeleton path under glb root: %s%s" % [up, skel.name])
	return skel


func _build_source_global_rests(melee_lib: AnimationLibrary, shooter_lib: AnimationLibrary) -> Dictionary:
	## 源 rest 基准（V8 配方，病灶切除版）：严禁用 idle/LightIdle 冒充 rest！
	## idle 是单脚错步、屈膝持刀的战斗姿势，以其为原点会让全部动作带上 50°~70°
	## 初始残差（仰躺/前伸腿/左右腿相位错乱的根源）。源库内的 TPose（MeleeLib）/
	## tpose（ShooterLib）剪辑才是真源 rest —— 0.001s 静态帧、全骨旋转键齐全，
	## 采样 t=0 即得源局部 rest，逐级合成源全局 rest S_gr。
	var out := {"shooter": {}, "melee": {}}
	for lib_key in [["shooter", shooter_lib, "tpose"], ["melee", melee_lib, "TPose"]]:
		var s_gr_local := {}
		# 大小写不敏感检索，防两库命名大小写差异
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
	out["_hips_len"] = 1.0  # 源 Hips 高度 1.0m（与库内 Hips 位置键实测一致）
	return out


## FK 验证：把重定向后的 TPose 施加到 Aster 骨架副本，断言 T-pose 全局方向
func _validate_tpose(out_lib: AnimationLibrary, aster_skel: Skeleton3D) -> bool:
	var wrapper := Node3D.new()
	var skel := Skeleton3D.new()  # 默认名 Skeleton3D，与轨道前缀一致
	wrapper.add_child(skel)
	root.add_child(wrapper)  # 必须入树，AnimationPlayer 才能解析节点路径
	for i: int in aster_skel.get_bone_count():
		var nm := aster_skel.get_bone_name(i)
		var parent := aster_skel.get_bone_parent(i)
		var idx := skel.add_bone(nm)
		if parent >= 0:
			skel.set_bone_parent(idx, skel.find_bone(aster_skel.get_bone_name(parent)))
		skel.set_bone_rest(idx, aster_skel.get_bone_rest(i))
	skel.reset_bone_poses()  # Godot4 新建骨骼 pose=单位而非 rest，必须显式复位
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
	# 断言1（数学自洽）：重定向后的 TPose 逐骨局部旋转必须精确还原 Aster rest
	var worst_deg := 0.0
	var worst_bone := ""
	for i: int in aster_skel.get_bone_count():
		var idx := skel.find_bone(aster_skel.get_bone_name(i))
		var q_pose: Quaternion = skel.get_bone_pose_rotation(idx)
		var q_rest: Quaternion = aster_skel.get_bone_rest(i).basis.get_rotation_quaternion()
		var dot: float = absf(q_pose.dot(q_rest))
		var deg := rad_to_deg(2.0 * acos(minf(dot, 1.0)))
		if deg > worst_deg:
			worst_deg = deg
			worst_bone = aster_skel.get_bone_name(i)
	var rest_ok := worst_deg < 0.6
	print("  TPose==rest 最大偏差: %.4f° @ %s -> %s" % [worst_deg, worst_bone, "OK" if rest_ok else "FAIL"])
	# 断言2（语义）：T-pose 全局方向 + 左右语义
	var checks := {
		"L_Calf": Vector3.UP, "R_Calf": Vector3.UP, "Head": Vector3.UP,
		"Spine01": Vector3.UP,
		"L_Upperarm": Vector3.LEFT, "R_Upperarm": Vector3.RIGHT,
	}
	var all_ok := true
	for bname: String in checks:
		var idx := skel.find_bone(bname)
		var head_g: Vector3 = skel.get_bone_global_pose(idx).origin
		var child := skel.get_bone_children(idx)
		var dir := Vector3.UP
		if child.size() > 0:
			dir = (skel.get_bone_global_pose(child[0]).origin - head_g).normalized()
		else:
			dir = Vector3(skel.get_bone_global_pose(idx).basis.y)
		var want: Vector3 = checks[bname]
		var dot: float = dir.dot(want)
		var ok := dot > 0.55
		all_ok = all_ok and ok
		print("  TPose FK %s dir=%s want=%s dot=%.2f %s" % [bname, dir, want, dot, "OK" if ok else "FAIL"])
	root.remove_child(wrapper)
	wrapper.free()
	return all_ok and rest_ok


func _retarget_anim(src: Animation, s_gr: Dictionary, dst_rest_q: Dictionary,
		skel_name: StringName) -> Animation:
	## 精确全局空间重定向（UE5 IK Retargeter 同款）：
	##   M(b) = D_gr_global(b) · S_gr_global(b)⁻¹   （两侧 rest 帧差，逐骨补偿坐标系约定差）
	##   src_global(b,t) = src_global(parent,t) · q_src(b,t)   （源运行时姿态按层级递推）
	##   q_out(b,t) = [M(parent)·src_global(parent,t)]⁻¹ · M(b)·src_global(b,t)
	## rest 时 q_out 严格还原 Aster 局部 rest；运动按全局姿态 1:1 守恒。
	## 仅收旋转轨道（髋高恒 rest 0.904m，Root 朝向由 visual_root 驱动）。
	var out := Animation.new()
	out.length = src.length
	out.step = src.step
	out.loop_mode = src.loop_mode

	# 源旋转轨道索引缓存 + 拓扑序（SRC_PARENTS 父先子后）
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
			# 父不在输出集（如 Root，被剔除不输出）即视作根级，可直接处理
			if parent == "" or not src_track.has(parent) or parent in order:
				order.append(bone)
		if order.size() == src_track.size():
			break

	for bone in order:
		var tb: int = src_track[bone]
		var parent: String = SRC_PARENTS[bone]
		var m_bone := _safe(dst_rest_q[bone] * _safe(s_gr[bone]).inverse())
		# 父骨 M 与「父骨源全局姿态」逐键评估：父链逐级向源轨道采样
		var m_parent := Quaternion.IDENTITY
		var ancestors: Array[String] = []
		var walk: String = parent
		while walk != "":
			ancestors.push_front(walk)
			walk = SRC_PARENTS[walk]
		var nt := out.add_track(Animation.TYPE_ROTATION_3D)
		out.track_set_path(nt, NodePath("%s:%s" % [skel_name, BONE_MAP[bone]]))
		for k: int in src.track_get_key_count(tb):
			var time: float = src.track_get_key_time(tb, k)
			# 源全局：从根到父累积
			var sg_parent := Quaternion.IDENTITY
			for a in ancestors:
				if src_track.has(a):
					sg_parent = sg_parent * _safe(src.rotation_track_interpolate(src_track[a], time))
			var sg_bone := sg_parent * _safe(src.rotation_track_interpolate(tb, time))
			if parent != "":
				m_parent = _safe(dst_rest_q[parent] * _safe(s_gr[parent]).inverse())
				var dst_parent_global := m_parent * sg_parent
				out.rotation_track_insert_key(nt, time, dst_parent_global.inverse() * (m_bone * sg_bone))
			else:
				out.rotation_track_insert_key(nt, time, m_bone * sg_bone)
	return out

func _safe(q: Quaternion) -> Quaternion:
	# 防御归一化：零/未初始化四元数（.res 里的占位键）按单位处理，杜绝 NaN 进骨骼
	return q.normalized() if q.length_squared() > 0.5 else Quaternion.IDENTITY
