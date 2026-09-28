extends SceneTree

func _init() -> void:
	var scene: PackedScene = load("res://models/aster/aster_character.glb")
	var inst: Node = scene.instantiate()
	var skel: Skeleton3D = inst.find_children("*", "Skeleton3D", true, false)[0]
	
	print("=== Aster 骨骼 Rest 姿态审计 ===")
	for b in ["Hip", "Pelvis", "L_Thigh", "L_Calf", "L_Foot", "R_Thigh", "R_Calf", "R_Foot", "L_Upperarm", "R_Upperarm"]:
		var idx = skel.find_bone(b)
		if idx >= 0:
			var rest: Transform3D = skel.get_bone_rest(idx)
			var q: Quaternion = rest.basis.get_rotation_quaternion()
			var euler: Vector3 = q.get_euler() * (180.0 / PI)
			var grest: Transform3D = skel.get_bone_global_rest(idx)
			var gq: Quaternion = grest.basis.get_rotation_quaternion()
			var geuler: Vector3 = gq.get_euler() * (180.0 / PI)
			print("  Bone: %-12s Local Euler: (x=%6.1f, y=%6.1f, z=%6.1f) | Global Euler: (x=%6.1f, y=%6.1f, z=%6.1f)" % [
				b, euler.x, euler.y, euler.z, geuler.x, geuler.y, geuler.z
			])
	quit(0)
