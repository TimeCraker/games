extends SceneTree

func _initialize() -> void:
	var glb_path := "c:/Users/TimeCraker/Desktop/my_workspace/games/asternova/art/models/source/aster_tripo_39caf44b/aster_source.glb"
	var gltf := GLTFDocument.new()
	var state := GLTFState.new()
	gltf.append_from_file(glb_path, state)
	var char_root := gltf.generate_scene(state)
	
	var mi: MeshInstance3D = char_root.find_child("tripo_node*", true, false) as MeshInstance3D
	if mi:
		var aabb := mi.get_aabb()
		print("原厂网格 AABB: pos=", aabb.position, " size=", aabb.size)
		print("网格材质: ", mi.mesh.surface_get_material(0))
		var mat = mi.mesh.surface_get_material(0)
		if mat is StandardMaterial3D:
			var sm := mat as StandardMaterial3D
			print("  albedo_color: ", sm.albedo_color)
			print("  albedo_texture: ", sm.albedo_texture)
			print("  roughness: ", sm.roughness)
			print("  cull_mode: ", sm.cull_mode)
	
	var sk: Skeleton3D = char_root.find_child("Skeleton3D", true, false) as Skeleton3D
	if sk:
		print("骨骼总数: ", sk.get_bone_count())
		for i in sk.get_bone_count():
			print(i, ": ", sk.get_bone_name(i), " rest_origin=", sk.get_bone_rest(i).origin)
	quit(0)
