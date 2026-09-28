extends SceneTree

func _initialize() -> void:
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var runner = IdleBoneInspector.new()
	playground.add_child(runner)

class IdleBoneInspector extends Node:
	var tick: int = 0
	var player: PlayerController = null
	var rig: AsterRig = null
	var skel: Skeleton3D = null

	func _ready() -> void:
		var scene_root := get_parent()
		player = scene_root.get_node_or_null("Player") as PlayerController
		rig = player.visual_root.get_node_or_null("CharacterAster") as AsterRig
		skel = rig.find_child("Skeleton3D", true, false) as Skeleton3D

	func _physics_process(_delta: float) -> void:
		tick += 1
		if tick == 30:
			print("=== 检查 Idle 状态下下肢骨骼旋转 ===")
			for bname in ["Pelvis", "Hip", "L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot", "L_ToeBase", "R_ToeBase"]:
				var idx := skel.find_bone(bname)
				if idx >= 0:
					var pose_q: Quaternion = skel.get_bone_pose_rotation(idx)
					var rest_q: Quaternion = skel.get_bone_rest(idx).basis.get_rotation_quaternion()
					var diff := pose_q * rest_q.inverse()
					var angle := rad_to_deg(diff.get_angle())
					var euler := pose_q.get_euler()
					print("Bone %-10s pose_rot_deg=(%.1f, %.1f, %.1f) diff_from_rest=%.2f°" % [
						bname, rad_to_deg(euler.x), rad_to_deg(euler.y), rad_to_deg(euler.z), angle])
			get_tree().quit(0)
