extends SceneTree

func _initialize() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	for i in skel.get_bone_count():
		var bname = skel.get_bone_name(i)
		var p_idx = skel.get_bone_parent(i)
		var pname = skel.get_bone_name(p_idx) if p_idx >= 0 else "-"
		var r = skel.get_bone_rest(i)
		var gr = skel.get_bone_global_rest(i)
		print(bname, " (parent=", pname, "):")
		print("  local_rot_deg=", r.basis.get_euler() * 180.0 / PI)
		print("  global_rot_deg=", gr.basis.get_euler() * 180.0 / PI)
	quit(0)
