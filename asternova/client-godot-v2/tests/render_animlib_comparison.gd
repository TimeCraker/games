extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(900, 1200)
	var scene := Node3D.new()
	root.add_child(scene)
	
	var runner := AnimlibTester.new()
	scene.add_child(runner)

class AnimlibTester extends Node3D:
	var tick: int = 0
	var aster: Node3D = null
	var anim_player: AnimationPlayer = null
	var cam: Camera3D = null

	func _ready() -> void:
		var ps: PackedScene = load("res://scenes/entities/character_aster.tscn")
		aster = ps.instantiate()
		add_child(aster)

		# 切换为刚刚重构的 aster_animlib.res
		anim_player = aster.get_node_or_null("AnimationPlayer") as AnimationPlayer
		if anim_player == null:
			anim_player = aster.find_child("AnimationPlayer", true, false) as AnimationPlayer
		
		# 确保 root_node 指向 CharacterAster 根节点 (轨道路径已是 Aster_Armature/Skeleton3D:Bone)
		anim_player.root_node = NodePath("..")

		var lib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
		anim_player.remove_animation_library("")
		anim_player.add_animation_library("", lib)

		# 关掉 AnimationTree 干扰
		var anim_tree := aster.find_child("AnimationTree", true, false) as AnimationTree
		if anim_tree != null:
			anim_tree.active = false

		# 创建相机 (正面看 Aster 全身)
		cam = Camera3D.new()
		cam.fov = 32.0
		cam.position = Vector3(0, 0.95, 2.9)
		cam.look_at(Vector3(0, 0.88, 0), Vector3.UP)
		add_child(cam)
		cam.make_current()

		# 灯光
		var light := DirectionalLight3D.new()
		light.position = Vector3(1, 2, 2)
		light.look_at(Vector3.ZERO, Vector3.UP)
		add_child(light)

		var fill_light := DirectionalLight3D.new()
		fill_light.position = Vector3(-1, 1, 1)
		fill_light.look_at(Vector3.ZERO, Vector3.UP)
		fill_light.light_energy = 0.5
		add_child(fill_light)

		# 播放 idle
		if anim_player.has_animation("idle"):
			anim_player.play("idle")
			anim_player.seek(0.8, true)
			print("Playing idle...")

	func _physics_process(_delta: float) -> void:
		tick += 1
		if tick == 10:
			_save("playtest_snapshots/new_animlib_idle_front.png")
		elif tick == 15:
			if anim_player.has_animation("LightWalking"):
				anim_player.play("LightWalking")
				anim_player.seek(0.3, true)
				print("Playing LightWalking...")
		elif tick == 25:
			_save("playtest_snapshots/new_animlib_walk_front.png")
		elif tick == 30:
			if anim_player.has_animation("LightRunning"):
				anim_player.play("LightRunning")
				anim_player.seek(0.2, true)
				print("Playing LightRunning...")
		elif tick == 40:
			_save("playtest_snapshots/new_animlib_run_front.png")
			print("ALL CAPTURES COMPLETED")
			get_tree().quit(0)

	func _save(path: String) -> void:
		var vp: Viewport = get_viewport()
		if vp:
			var img := vp.get_texture().get_image()
			if img and not img.is_empty():
				img.save_png(path)
				print("SAVED: ", path, " size: ", img.get_size())
