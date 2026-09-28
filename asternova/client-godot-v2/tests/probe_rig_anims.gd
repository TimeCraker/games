extends SceneTree

func _initialize() -> void:
	print("==================== Aster Rig & Animation Probe ====================")
	# 1. 检查 aster_character.glb
	var glb: PackedScene = load("res://models/aster/aster_character.glb")
	if glb:
		var inst := glb.instantiate()
		print("GLB instantiated successfully. Root node:", inst.name, " class:", inst.get_class())
		_print_tree(inst, "  ")
		inst.free()
	else:
		print("FAIL to load res://models/aster/aster_character.glb")

	# 2. 检查 aster_animlib.res
	var animlib: AnimationLibrary = load("res://art/animations/aster_animlib.res")
	if animlib:
		var anims := animlib.get_animation_list()
		print("aster_animlib.res loaded. Total anims:", anims.size())
		var required := ["idle", "LightIdle", "LightWalking", "LightRunning", "Slash1", "Slash2", "Slash3", "SlashUppercut", "Roll", "jump", "fall", "fall-landing"]
		for req in required:
			var has := animlib.has_animation(req)
			print("  Anim check [%s]: %s" % [req, "EXISTS" if has else "MISSING"])
	else:
		print("FAIL to load res://art/animations/aster_animlib.res")

	# 3. 检查 AsterRig 实例化时的行为
	var rig_script := load("res://scripts/entities/player/aster_rig.gd")
	var rig: AsterRig = AsterRig.new()
	root.add_child(rig)
	print("AsterRig added to tree. anim_player:", rig.anim_player)
	if rig.anim_player:
		print("  anim_player path:", rig.anim_player.get_path())
		print("  anim_player parent:", rig.anim_player.get_parent().name)
		var p_lib := rig.anim_player.get_animation_library("")
		if p_lib:
			print("  anim_player has default lib. anim count:", p_lib.get_animation_list().size())
			for req in ["idle", "LightIdle", "LightWalking", "LightRunning", "Slash1"]:
				print("    anim_player [%s]: %s" % [req, "EXISTS" if p_lib.has_animation(req) else "MISSING"])
	if rig.anim_tree:
		print("  anim_tree active:", rig.anim_tree.active)
		print("  anim_tree root:", rig.anim_tree.tree_root)
	
	rig.queue_free()
	quit(0)

func _print_tree(node: Node, indent: String) -> void:
	print("%s- %s (%s)" % [indent, node.name, node.get_class()])
	for child in node.get_children():
		_print_tree(child, indent + "  ")
