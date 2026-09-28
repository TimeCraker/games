extends SceneTree
## 探针：源库 TPose/tpose 剪辑内容体检 —— 键值非全零？臂向水平(T)还是下垂(A)？
func _initialize() -> void:
	for entry in [["MeleeLib", "res://art/animations/MeleeLib.res"], ["ShooterLib", "res://art/animations/ShooterLib.res"]]:
		var lib: AnimationLibrary = load(entry[1])
		var names: PackedStringArray = lib.get_animation_list()
		var hits: Array[String] = []
		for n in names:
			if n.to_lower().contains("tpose") or n.to_lower() == "t-pose" or n.to_lower() == "t_pose":
				hits.append(n)
		print("== %s: %d clips, tpose 命中=%s" % [entry[0], names.size(), hits])
		for hit in hits:
			var a: Animation = lib.get_animation(hit)
			print("  %s len=%.4f tracks=%d" % [hit, a.length, a.get_track_count()])
			# 全局方向合成（局部四元数按 SRC 父链累积，源约定 +Y 上）
			var locals := {}
			for t in a.get_track_count():
				if a.track_get_type(t) != Animation.TYPE_ROTATION_3D:
					continue
				locals[String(a.track_get_path(t).get_subname(0))] = a.rotation_track_interpolate(t, 0.0)
			print("  rot tracks=%d / 全部 tracks" % locals.size())
			var keys := ["Hips", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "LeftFoot",
				"LeftUpperArm", "RightUpperArm", "LeftLowerArm", "Head", "Spine"]
			var parent := {
				"Root": "", "Hips": "Root", "Spine": "Hips", "Head": "Spine",
				"LeftUpperLeg": "Hips", "RightUpperLeg": "Hips",
				"LeftLowerLeg": "LeftUpperLeg", "LeftFoot": "LeftLowerLeg",
				"LeftUpperArm": "Hips", "RightUpperArm": "Hips",
				"LeftLowerArm": "LeftUpperArm", "RightLowerArm": "RightUpperArm",
			}
			var glob := {"": Quaternion.IDENTITY, "Root": locals.get("Root", Quaternion.IDENTITY)}
			for b in ["Hips", "Spine", "Head", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "LeftFoot", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"]:
				var q: Quaternion = glob[parent[b]] * (locals[b] if locals.has(b) else Quaternion.IDENTITY)
				glob[b] = q
				var dir := (q * Vector3.DOWN)
				if b in ["LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"]:
					dir = q * Vector3(1, 0, 0)  # 臂骨惯例沿局部 X 伸展
				print("    %-14s local=%s  global_dir(%s)=%s" % [b,
					_strq(locals[b] if locals.has(b) else Quaternion.IDENTITY),
					"X" if b.contains("Arm") else "-Y", dir.snapped(Vector3(0.05, 0.05, 0.05))])
	quit(0)

func _strq(q: Quaternion) -> String:
	return "(%.3f,%.3f,%.3f,%.3f)" % [q.x, q.y, q.z, q.w]
