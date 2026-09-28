extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	print("Rig current state:", rig.get_current_state_node())
	var ap: AnimationPlayer = rig.find_child("AnimationPlayer", true, false)
	print("AnimationPlayer current anim:", ap.current_animation if ap else "N/A")
	print("AnimationPlayer assigned anim:", ap.assigned_animation if ap else "N/A")
	var cam: Camera3D = scene.find_child("Camera3D", true, false)
	var spring: SpringArm3D = scene.find_child("SpringArm3D", true, false)
	
	# View 1: Back view Idle
	rig.set_locomotion_blend(0.0)
	for f in range(15):
		await physics_frame
	var img1 = root.get_viewport().get_texture().get_image()
	var out_dir := "C:/Users/TimeCraker/.gemini/antigravity/brain/a12a34db-37fe-4516-b01d-a4f467888558/"
	img1.save_png(out_dir + "verify_idle_back.png")
	
	# View 2: Back view Walk (blend 2.4, same as user screenshot)
	rig.set_locomotion_blend(2.4)
	for f in range(15):
		await physics_frame
	var img2 = root.get_viewport().get_texture().get_image()
	img2.save_png(out_dir + "verify_walk_back.png")
	
	# View 3: Side view Walk
	if spring:
		spring.position = Vector3(0, 0.8, 0)
		spring.rotation_degrees = Vector3(0, 90, 0)
		spring.spring_length = 2.5
	for f in range(15):
		await physics_frame
	var img3 = root.get_viewport().get_texture().get_image()
	img3.save_png(out_dir + "verify_walk_side.png")
	
	# View 4: Side view Jog/Run
	rig.set_locomotion_blend(5.0)
	for f in range(15):
		await physics_frame
	var img4 = root.get_viewport().get_texture().get_image()
	img4.save_png(out_dir + "verify_run_side.png")
	
	# View 5: Front view Idle (matching user screenshot)
	rig.set_locomotion_blend(0.0)
	if spring:
		spring.position = Vector3(0, 0.9, 0)
		spring.rotation_degrees = Vector3(-5, 175, 0)
		spring.spring_length = 2.6
	for f in range(15):
		await physics_frame
	var img5 = root.get_viewport().get_texture().get_image()
	img5.save_png(out_dir + "verify_idle_front.png")
	
	print("Saved all 5 verification screenshots!")
	quit()
