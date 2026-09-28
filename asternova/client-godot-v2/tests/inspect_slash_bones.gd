extends SceneTree

func _initialize() -> void:
	var playground = load("res://scenes/levels/combat_playground.tscn").instantiate()
	root.add_child(playground)
	
	var runner = SlashInspector.new()
	playground.add_child(runner)

class SlashInspector extends Node:
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
		if tick == 20:
			rig.draw_sword()
			rig.travel("Combo1")
			print("Triggered Combo1")
		elif tick == 35:
			print("=== 检查 Combo1 挥砍中各骨骼全局/局部旋转 ===")
			for bname in ["Hips", "Pelvis", "L_Thigh", "R_Thigh", "L_Calf", "R_Calf", "L_Foot", "R_Foot"]:
				var idx := skel.find_bone(bname)
				if idx >= 0:
					var p_rot := skel.get_bone_pose_rotation(idx)
					var rest_q := skel.get_bone_rest(idx).basis.get_rotation_quaternion()
					var diff := p_rot * rest_q.inverse()
					var euler := rad_to_deg(diff.get_angle())
					var g_trans := skel.get_bone_global_pose(idx)
					print("Bone %-10s diff_angle=%.1f° global_origin=%s" % [bname, euler, g_trans.origin])
			get_tree().quit(0)
