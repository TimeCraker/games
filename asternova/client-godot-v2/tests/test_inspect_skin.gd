extends SceneTree

func _init() -> void:
	var glb = load("res://models/aster/aster_character.glb").instantiate()
	var body: MeshInstance3D = glb.find_child("Aster_Body", true, false)
	var skel: Skeleton3D = glb.find_child("Skeleton3D", true, false)
	var skin: Skin = body.skin
	print("Body has skin:", skin != null)
	if skin:
		print("Skin bind count:", skin.get_bind_count())
		for i in range(min(skin.get_bind_count(), 20)):
			var bname = skin.get_bind_name(i)
			var bbone = skin.get_bind_bone(i)
			print("Skin [%2d]: name=%-25s bone_idx=%d (skel bone name: %s)" % [i, bname, bbone, skel.get_bone_name(bbone) if bbone >= 0 and bbone < skel.get_bone_count() else "N/A"])
	quit()
