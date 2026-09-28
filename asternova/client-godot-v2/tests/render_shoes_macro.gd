extends SceneTree

func _initialize() -> void:
	root.size = Vector2i(1920, 1080)
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var runner = ShoesMacroCapturer.new()
	playground.add_child(runner)

class ShoesMacroCapturer extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var macro_cam: Camera3D = null
	var artifact_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/fb8af5b9-28ba-4aaa-98c0-017f131c7165"

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		
		# Create a dedicated Camera3D right in front of feet
		macro_cam = Camera3D.new()
		macro_cam.name = "MacroShoesCam"
		add_child(macro_cam)

	func _set_macro_cam(pos: Vector3, look_at_pos: Vector3) -> void:
		macro_cam.global_position = pos
		macro_cam.look_at(look_at_pos, Vector3.UP)
		macro_cam.make_current()

	func _physics_process(_delta: float) -> void:
		tick += 1
		var char_pos: Vector3 = player.global_position
		
		# Shot 1: Rest Pose - Direct Front of Shoes (Height 0.12m, dist 0.45m)
		if tick == 10:
			rig.anim_tree.active = false
			rig.anim_player.stop()
			rig.skeleton.reset_bone_poses()
			_set_macro_cam(char_pos + Vector3(0.0, 0.12, 0.45), char_pos + Vector3(0.0, 0.08, 0.0))
		elif tick == 15:
			_save_frame(artifact_dir + "/macro_shoes_rest_front.png")

		# Shot 2: Rest Pose - 45-degree angled view of right shoe & Mary Jane strap
		elif tick == 20:
			_set_macro_cam(char_pos + Vector3(0.35, 0.16, 0.35), char_pos + Vector3(0.0, 0.06, 0.0))
		elif tick == 25:
			_save_frame(artifact_dir + "/macro_shoes_rest_angle.png")

		# Shot 3: Rest Pose - Back view of heels and socks
		elif tick == 30:
			_set_macro_cam(char_pos + Vector3(0.0, 0.14, -0.45), char_pos + Vector3(0.0, 0.06, 0.0))
		elif tick == 35:
			_save_frame(artifact_dir + "/macro_shoes_rest_back.png")

		# Shot 4: ShooterLib "idle" - Front of Shoes
		elif tick == 40:
			rig.anim_tree.active = false
			rig.anim_player.play("idle")
			_set_macro_cam(char_pos + Vector3(0.0, 0.12, 0.45), char_pos + Vector3(0.0, 0.08, 0.0))
		elif tick == 50:
			_save_frame(artifact_dir + "/macro_shoes_idle_front.png")

		# Shot 5: ShooterLib "idle" - 45-degree angle
		elif tick == 55:
			_set_macro_cam(char_pos + Vector3(0.35, 0.16, 0.35), char_pos + Vector3(0.0, 0.06, 0.0))
		elif tick == 65:
			_save_frame(artifact_dir + "/macro_shoes_idle_angle.png")
			get_tree().quit(0)

	func _save_frame(path: String) -> void:
		var img := get_viewport().get_texture().get_image()
		if img:
			var err := img.save_png(path)
			print("Saved [err=", err, "]: ", path)
