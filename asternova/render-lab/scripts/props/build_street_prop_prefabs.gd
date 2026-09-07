extends SceneTree
## AsterNova - Headless prefab builder for Tier 3 street props (生活道具预制体).
## 将 build_street_props.py 产出的 GLB 逐个包装为:
##   StaticBody3D -> CollisionShape3D(BoxShape3D from AABB) + GLB 实例
## NPR 由 street_prop_npr_setup.gd 在运行时绑定 (convenience_store.tscn 同模式)。
## Run (after `--import`):
##   Godot_v4.7.2-stable_win64_console.exe --headless --path render-lab \
##       --script res://scripts/props/build_street_prop_prefabs.gd

const NPR_SCRIPT := "res://scripts/props/street_prop_npr_setup.gd"
const PROPS := {
	"ac_unit_single": "ACUnitSingle",
	"ac_unit_double": "ACUnitDouble",
	"utility_pole": "UtilityPole",
	"trash_station_4bin": "TrashStation4Bin",
	"traffic_cone": "TrafficCone",
}


func _initialize() -> void:
	var failures := 0
	for glb_name in PROPS:
		if not _build(glb_name, PROPS[glb_name]):
			failures += 1
	quit(1 if failures > 0 else 0)


func _build(glb_name: String, node_name: String) -> bool:
	var glb_path := "res://models/props/%s.glb" % glb_name
	var out_path := "res://scenes/entities/props/%s.tscn" % node_name
	var packed: PackedScene = load(glb_path)
	if packed == null:
		push_error("[build] cannot load " + glb_path)
		return false
	var inst := packed.instantiate()

	# 求 GLB 全体网格的世界 AABB (碰撞盒)
	var bounds := _accum_aabb(inst, inst)
	if bounds.is_empty():
		push_error("[build] no MeshInstance3D inside " + glb_path)
		inst.free()
		return false
	var aabb := AABB(bounds[0], bounds[1] - bounds[0])
	print("[build] %s AABB pos=%s size=%s" % [glb_name, aabb.position, aabb.size])

	var root := StaticBody3D.new()
	root.name = node_name
	root.set_script(load(NPR_SCRIPT))

	var cs := CollisionShape3D.new()
	cs.name = "CollisionShape3D"
	var box := BoxShape3D.new()
	box.size = aabb.size
	cs.shape = box
	cs.position = aabb.get_center()

	var body := inst
	body.name = "Mesh"

	root.add_child(cs)
	root.add_child(body)
	cs.owner = root
	_set_owner_recursive(body, root)

	var ps := PackedScene.new()
	var err := ps.pack(root)
	if err != OK:
		push_error("[build] pack failed: %d (%s)" % [err, out_path])
		return false
	DirAccess.make_dir_recursive_absolute(out_path.get_base_dir())
	err = ResourceSaver.save(ps, out_path)
	if err != OK:
		push_error("[build] scene save failed: %d (%s)" % [err, out_path])
		return false
	print("[build] prefab saved: " + out_path)
	root.free()
	return true


## 返回 [min_corner, max_corner]; 空数组 = 子树无网格
func _accum_aabb(root: Node, node: Node) -> Array:
	var mn := Vector3(INF, INF, INF)
	var mx := -mn
	if node is MeshInstance3D:
		var xf := _rel_xf(root, node)
		var ab := (node as MeshInstance3D).mesh.get_aabb()
		for i in 8:
			var corner := xf * (ab.position + Vector3(
					ab.size.x * float(i & 1), ab.size.y * float((i >> 1) & 1),
					ab.size.z * float((i >> 2) & 1)))
			mn = mn.min(corner)
			mx = mx.max(corner)
	for child in node.get_children():
		var sub := _accum_aabb(root, child)
		if sub.is_empty():
			continue
		mn = mn.min(sub[0])
		mx = mx.max(sub[1])
	if mn.x > mx.x:
		return []
	return [mn, mx]


func _rel_xf(root: Node, node: Node3D) -> Transform3D:
	var xf := node.transform
	var parent := node.get_parent()
	while parent != null and parent != root:
		if parent is Node3D:
			xf = (parent as Node3D).transform * xf
		parent = parent.get_parent()
	return xf


func _set_owner_recursive(node: Node, owner: Node) -> void:
	node.owner = owner
	for child in node.get_children():
		_set_owner_recursive(child, owner)
