extends SceneTree

## 源动捕库 → JSON 桥（Blender 离线烘焙的数据源，无头运行）：
##   godot --headless --path client-godot-v2 -s scripts/animation/dump_mocap_json.gd -- <out.json>
## MeleeLib/ShooterLib 为 Godot 资源格式，Blender 无法直接读取；
## 本脚本把 Blender 烘焙所需剪辑（含 TPose/tpose 静态标定帧）逐键导出为 JSON。
## 轨道局部值与 build_aster_animlib.gd 同源：rotation/position 键均为骨骼局部空间绝对值。

const MELEE_LIB := "res://art/animations/MeleeLib.res"
const SHOOTER_LIB := "res://art/animations/ShooterLib.res"

## Blender 端烘焙清单（测试门禁 18 + 动画树 crouch-run/Hurt1）
const CLIPS := [
	"idle", "LightIdle", "LightWalking", "LightRunning", "Sprint",
	"jump", "fall", "fall-landing", "Roll",
	"Slash1", "Slash2", "Slash3", "SlashUppercut", "SlashCharge", "SlashRelease",
	"Guarding", "GuardParry", "wall-slide-front", "HeavyJumpAttack",
	"crouch-run", "Hurt1",
]
const CALIB := [["melee", MELEE_LIB, "TPose"], ["shooter", SHOOTER_LIB, "tpose"]]


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var out_path: String = args[0] if args.size() > 0 else "user://mocap_dump.json"

	var libs := {"melee": load(MELEE_LIB) as AnimationLibrary, "shooter": load(SHOOTER_LIB) as AnimationLibrary}
	var dump := {"clips": {}, "tpose": {}}

	# 源 rest 标定帧（严禁用 idle 冒充 rest——历史教训，见 build_aster_animlib.gd）
	for calib in CALIB:
		var anim := _find_clip(libs[calib[0]], calib[2])
		if anim == null:
			push_error("源 rest 剪辑缺失: " + calib[2])
			quit(1)
			return
		dump["tpose"][calib[0]] = _sample_static(anim)

	for clip_name: String in CLIPS:
		var found: Array = []
		for lib_key in ["melee", "shooter"]:
			var anim := _find_clip(libs[lib_key], clip_name)
			if anim != null:
				found.append([lib_key, anim])
		if found.is_empty():
			push_warning("两库均无剪辑，跳过: " + clip_name)
			continue
		if found.size() > 1:
			push_warning("剪辑重名（取 melee 优先）: " + clip_name)
		var entry: Array = found[0]
		dump["clips"][clip_name] = _dump_clip(entry[0], entry[1])

	var f := FileAccess.open(out_path, FileAccess.WRITE)
	if f == null:
		push_error("无法写出: " + out_path)
		quit(1)
		return
	f.store_string(JSON.stringify(dump))
	f.close()
	print("DUMP_OK clips=%d tpose=2 -> %s" % [dump["clips"].size(), out_path])
	quit(0)


func _find_clip(lib: AnimationLibrary, name: String) -> Animation:
	for anim_name in lib.get_animation_list():
		if anim_name.to_lower() == name.to_lower():
			return lib.get_animation(anim_name)
	return null


func _sample_static(anim: Animation) -> Dictionary:
	var out := {}
	for t: int in anim.get_track_count():
		if anim.track_get_type(t) != Animation.TYPE_ROTATION_3D:
			continue
		var bone := String(anim.track_get_path(t).get_subname(0))
		var q := anim.rotation_track_interpolate(t, 0.0)
		out[bone] = [q.x, q.y, q.z, q.w]
	return out


func _dump_clip(lib_key: String, anim: Animation) -> Dictionary:
	var tracks := {}
	for t: int in anim.get_track_count():
		var path := anim.track_get_path(t)
		var bone := String(path.get_subname(0))
		if bone == "":
			bone = String(path.get_name(path.get_name_count() - 1))
		var kind := ""
		match anim.track_get_type(t):
			Animation.TYPE_POSITION_3D: kind = "p"
			Animation.TYPE_ROTATION_3D: kind = "r"
			Animation.TYPE_SCALE_3D: kind = "s"
			_:
				continue  # Blender 端不需要 value/method 轨道
		if not tracks.has(bone):
			tracks[bone] = {}
		if tracks[bone].has(kind):
			push_warning("%s/%s 重复轨道，保留首条" % [anim.resource_name, bone])
			continue
		var keys := []
		var n := anim.track_get_key_count(t)
		for k: int in n:
			var time := float(anim.track_get_key_time(t, k))
			if kind == "p":
				var v: Vector3 = anim.position_track_interpolate(t, time)
				keys.append([snappedf(time, 0.0001), v.x, v.y, v.z])
			elif kind == "r":
				var q: Quaternion = anim.rotation_track_interpolate(t, time)
				keys.append([snappedf(time, 0.0001), q.x, q.y, q.z, q.w])
			else:
				var s: Vector3 = anim.scale_track_interpolate(t, time)
				keys.append([snappedf(time, 0.0001), s.x, s.y, s.z])
		tracks[bone][kind] = keys
	return {"lib": lib_key, "length": anim.length, "tracks": tracks}
