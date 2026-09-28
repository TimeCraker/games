extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(10):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	var ap: AnimationPlayer = rig.find_child("AnimationPlayer", true, false)
	var at: AnimationTree = rig.find_child("AnimationTree", true, false)
	
	# Disable anim_tree temporarily to directly play Idle on AnimationPlayer
	if at:
		at.active = false
		
	if ap:
		ap.play("Idle")
		ap.seek(0.5, true)
		
	var spring: SpringArm3D = scene.find_child("SpringArm3D", true, false)
	if spring:
		spring.position = Vector3(0, 0.9, 0)
		spring.rotation_degrees = Vector3(-5, 175, 0)
		spring.spring_length = 2.6
		
	for i in range(5):
		await physics_frame
		
	var img = root.get_viewport().get_texture().get_image()
	img.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/pure_idle_front.png")
	print("Saved pure_idle_front.png!")
	quit(0)
