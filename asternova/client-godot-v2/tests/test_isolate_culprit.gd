extends SceneTree

func _init() -> void:
	var scene = load("res://scenes/entities/player.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(5):
		await process_frame
		
	var rig = scene.get_node_or_null("VisualRoot/CharacterAster")
	rig.set_locomotion_blend(2.4)
	
	for i in range(20):
		await physics_frame
		
	# Move camera closer to Aster to see clearly
	var cam: Camera3D = scene.find_child("Camera3D", true, false)
	if cam:
		cam.fov = 40.0
		
	await process_frame
	var img1 = root.get_viewport().get_texture().get_image()
	img1.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/culprit_normal.png")
	
	# Test 2: Hide Katana
	var k_blade = rig.find_child("Katana_Blade", true, false)
	var k_scabbard = rig.find_child("Katana_Scabbard", true, false)
	if k_blade: k_blade.visible = false
	if k_scabbard: k_scabbard.visible = false
	await process_frame
	var img2 = root.get_viewport().get_texture().get_image()
	img2.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/culprit_no_katana.png")
	
	# Test 3: Stop animation (bind pose)
	if k_blade: k_blade.visible = true
	if k_scabbard: k_scabbard.visible = true
	var at = rig.find_child("AnimationTree", true, false)
	if at: at.active = false
	var ap = rig.find_child("AnimationPlayer", true, false)
	if ap: ap.stop()
	var skel: Skeleton3D = rig.skeleton
	if skel:
		for b in range(skel.get_bone_count()):
			skel.set_bone_pose_position(b, skel.get_bone_rest(b).origin)
			skel.set_bone_pose_rotation(b, skel.get_bone_rest(b).basis.get_rotation_quaternion())
			skel.set_bone_pose_scale(b, skel.get_bone_rest(b).basis.get_scale())
			
	await process_frame
	var img3 = root.get_viewport().get_texture().get_image()
	img3.save_png("C:/Users/TimeCraker/.gemini/antigravity/brain/e2a54378-0bc7-4ac4-812a-63fffb6115fa/inspect_motion/culprit_bind_pose.png")
	
	print("Screenshots saved: culprit_normal, culprit_no_katana, culprit_bind_pose")
	quit()
