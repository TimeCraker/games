extends SceneTree

## 诊断：dump aster_assembled.glb 导入后的节点树 / 骨骼 / 插槽 / 网格 AABB

func _initialize() -> void:
	var packed: PackedScene = load("res://models/aster/aster_assembled.glb")
	if not packed:
		printerr("FAIL: glb load")
		quit(1)
		return
	var root: Node = packed.instantiate()
	root.name = "InspectRoot"
	get_root().add_child(root)
	_dump(root, 0)
	quit(0)

func _dump(node: Node, depth: int) -> void:
	var pad := "  ".repeat(depth)
	var extra := ""
	if node is Node3D:
		extra = " pos=%s rot_deg=%s scale=%s" % [
			(node as Node3D).position, (node as Node3D).rotation_degrees, (node as Node3D).scale]
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		extra += " aabb=%s surfaces=%d" % [mi.get_aabb(), mi.mesh.get_surface_count() if mi.mesh else 0]
	if node is BoneAttachment3D:
		extra += " bone=%s" % (node as BoneAttachment3D).bone_name
	print("%s%s (%s)%s" % [pad, node.name, node.get_class(), extra])
	if node is Skeleton3D:
		var sk := node as Skeleton3D
		print("%s  [bones %d]" % [pad, sk.get_bone_count()])
		for i in sk.get_bone_count():
			var parent := sk.get_bone_parent(i)
			print("%s    %d: %s (parent=%s) rest_origin=%s" % [pad, i, sk.get_bone_name(i),
				sk.get_bone_name(parent) if parent >= 0 else "-",
				sk.get_bone_rest(i).origin])
	for child in node.get_children():
		_dump(child, depth + 1)
