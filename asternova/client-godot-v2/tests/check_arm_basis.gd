extends SceneTree

func _initialize() -> void:
	var skel_scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = skel_scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	var m_lib: AnimationLibrary = load("res://art/animations/MeleeLib.res")
	var tpose: Animation = m_lib.get_animation("TPose")
	var idle: Animation = m_lib.get_animation("LightIdle")
	
	for b in ["L_Upperarm", "R_Upperarm", "L_Clavicle", "R_Clavicle"]:
		var idx := skel.find_bone(b)
		var rest := skel.get_bone_global_rest(idx)
		print("Aster ", b, " rest basis:\n  X=", rest.basis.x, "\n  Y=", rest.basis.y, "\n  Z=", rest.basis.z)
		
	quit(0)
