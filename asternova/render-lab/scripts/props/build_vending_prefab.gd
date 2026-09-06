extends SceneTree
## AsterNova - Headless prefab builder for the dual vending machine.
## Extracts the calibrated mesh out of the imported glb, saves it as a binary
## mesh resource, and packs the physics prefab:
##   StaticBody3D -> CollisionShape3D(BoxShape3D from world AABB) + MeshInstance3D
##
## Run (after `--import`):
##   Godot_v4.7.2-stable_win64_console.exe --headless --path render-lab \
##       --script res://scripts/props/build_vending_prefab.gd

const GLB_PATH := "res://models/environment/vending_machine_dual.glb"
const MESH_OUT := "res://models/environment/vending_machine_dual_mesh.res"
const PREFAB_OUT := "res://scenes/entities/props/vending_machine_dual.tscn"
const NPR_SCRIPT := "res://scripts/props/vending_machine_npr_setup.gd"


func _initialize() -> void:
	var packed: PackedScene = load(GLB_PATH)
	if packed == null:
		push_error("cannot load " + GLB_PATH)
		quit(1)
		return
	var inst := packed.instantiate()
	var mi_src: MeshInstance3D = _find_mesh(inst)
	if mi_src == null:
		push_error("no MeshInstance3D inside glb scene")
		quit(1)
		return

	var mesh: Mesh = mi_src.mesh
	var aabb := mesh.get_aabb()
	print("[build] mesh AABB pos=%s size=%s" % [aabb.position, aabb.size])

	var mesh_copy: Mesh = mesh.duplicate(true)
	for i in mesh_copy.get_surface_count():
		if mesh_copy.surface_get_material(i) != null:
			mesh_copy.surface_set_material(i, null)
	var save_err := ResourceSaver.save(mesh_copy, MESH_OUT)
	if save_err != OK:
		push_error("mesh save failed: %s" % save_err)
		quit(1)
		return
	mesh_copy.take_over_path(MESH_OUT)
	var mesh_res: Mesh = load(MESH_OUT)
	print("[build] mesh resource saved: " + MESH_OUT)

	var root := StaticBody3D.new()
	root.name = "VendingMachineDual"
	root.set_script(load(NPR_SCRIPT))

	var cs := CollisionShape3D.new()
	cs.name = "CollisionShape3D"
	var box := BoxShape3D.new()
	box.size = aabb.size
	cs.shape = box
	cs.position = aabb.get_center()

	var mi := MeshInstance3D.new()
	mi.name = "Mesh"
	mi.mesh = mesh_res

	root.add_child(cs)
	root.add_child(mi)
	cs.owner = root
	mi.owner = root

	var ps := PackedScene.new()
	var pack_err := ps.pack(root)
	if pack_err != OK:
		push_error("pack failed: %s" % pack_err)
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(PREFAB_OUT.get_base_dir())
	var scene_err := ResourceSaver.save(ps, PREFAB_OUT)
	if scene_err != OK:
		push_error("scene save failed: %s" % scene_err)
		quit(1)
		return
	print("[build] prefab saved: " + PREFAB_OUT)

	var check: Node = load(PREFAB_OUT).instantiate()
	_dump(check, 0)
	check.free()
	inst.free()
	quit(0)


func _find_mesh(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node
	for child in node.get_children():
		var found := _find_mesh(child)
		if found != null:
			return found
	return null


func _dump(node: Node, depth: int) -> void:
	var extra := ""
	if node is CollisionShape3D and node.shape is BoxShape3D:
		extra = " box_size=%s" % node.shape.size
	print("[build] tree: %s%s %s%s" % ["  ".repeat(depth), node.name, node.get_class(), extra])
	for child in node.get_children():
		_dump(child, depth + 1)
