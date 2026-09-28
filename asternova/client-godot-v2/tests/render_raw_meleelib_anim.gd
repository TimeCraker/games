extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1280, 720)
	var scene := Node3D.new()
	root.add_child(scene)
	
	var runner := RawMocapVisualizer.new()
	scene.add_child(runner)

class RawMocapVisualizer extends Node3D:
	var tick: int = 0
	var melee: AnimationLibrary = null
	var anim: Animation = null
	var cam: Camera3D = null
	var skel: Skeleton3D = null
	var anim_player: AnimationPlayer = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

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

	func _ready() -> void:
		melee = load("res://art/animations/MeleeLib.res")
		anim = melee.get_animation("Slash1")
		var tpose: Animation = melee.get_animation("TPose")

		skel = Skeleton3D.new()
		skel.name = "GeneralSkeleton"
		add_child(skel)

		for bname: String in SRC_PARENTS:
			var idx := skel.add_bone(bname)
			var parent_name: String = SRC_PARENTS[bname]
			if parent_name != "":
				skel.set_bone_parent(idx, skel.find_bone(parent_name))

		# 设置 Rest
		for t in tpose.get_track_count():
			if tpose.track_get_type(t) == Animation.TYPE_ROTATION_3D:
				var bname := String(tpose.track_get_path(t).get_subname(0))
				var idx := skel.find_bone(bname)
				if idx >= 0:
					var q: Quaternion = tpose.rotation_track_interpolate(t, 0.0)
					skel.set_bone_rest(idx, Transform3D(Basis(q), Vector3.ZERO))

		# 设置默认骨骼长度
		_set_default_bone_lengths()
		skel.reset_bone_poses()

		anim_player = AnimationPlayer.new()
		anim_player.name = "AnimationPlayer"
		add_child(anim_player)
		var lib := AnimationLibrary.new()
		lib.add_animation("Slash1", anim)
		anim_player.add_animation_library("", lib)

		cam = Camera3D.new()
		cam.fov = 45.0
		cam.position = Vector3(0, 1.0, 3.0)
		cam.look_at(Vector3(0, 0.8, 0), Vector3.UP)
		add_child(cam)
		cam.make_current()

		anim_player.play("Slash1")

	func _set_default_bone_lengths() -> void:
		# 给典型骨骼赋予合理长度，以便可视化骨架
		var offsets := {
			"Hips": Vector3(0, 0.9, 0),
			"Spine": Vector3(0, 0.12, 0),
			"Chest": Vector3(0, 0.12, 0),
			"UpperChest": Vector3(0, 0.12, 0),
			"Neck": Vector3(0, 0.1, 0),
			"Head": Vector3(0, 0.12, 0),
			"LeftShoulder": Vector3(0.08, 0.05, 0),
			"RightShoulder": Vector3(-0.08, 0.05, 0),
			"LeftUpperArm": Vector3(0.12, 0, 0),
			"RightUpperArm": Vector3(-0.12, 0, 0),
			"LeftLowerArm": Vector3(0.25, 0, 0),
			"RightLowerArm": Vector3(-0.25, 0, 0),
			"LeftHand": Vector3(0.22, 0, 0),
			"RightHand": Vector3(-0.22, 0, 0),
			"LeftUpperLeg": Vector3(0.1, -0.05, 0),
			"RightUpperLeg": Vector3(-0.1, -0.05, 0),
			"LeftLowerLeg": Vector3(0, -0.42, 0),
			"RightLowerLeg": Vector3(0, -0.42, 0),
			"LeftFoot": Vector3(0, -0.42, 0),
			"RightFoot": Vector3(0, -0.42, 0),
			"LeftToes": Vector3(0, 0, 0.15),
			"RightToes": Vector3(0, 0, 0.15),
		}
		for bname: String in offsets:
			var idx := skel.find_bone(bname)
			if idx >= 0:
				var t := skel.get_bone_rest(idx)
				t.origin = offsets[bname]
				skel.set_bone_rest(idx, t)

	func _physics_process(_delta: float) -> void:
		tick += 1
		if tick == 10:
			_save(artifact_dir + "/raw_slash1_f10.png")
		elif tick == 20:
			_save(artifact_dir + "/raw_slash1_f20.png")
		elif tick == 35:
			_save(artifact_dir + "/raw_slash1_f35.png")
			get_tree().quit(0)

	func _save(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			img.save_png(path)
			print("Saved raw visual: ", path)
