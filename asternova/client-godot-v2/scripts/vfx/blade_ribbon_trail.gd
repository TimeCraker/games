class_name BladeRibbonTrail
extends MeshInstance3D

## 太刀动态带状刀光曲面：挥刀激活时每物理帧采样刀根/刀尖世界坐标，
## 构建贝塞尔平滑的 Quad 条带（保留最近 8 个切片），尾迹 0.12s 顺滑淡出。
## 条带使用 top_level 全局空间构建，不随角色骨骼变换。

const MAX_SLICES := 8
const FADE_TIME := 0.12

var _base_marker: Node3D = null
var _tip_marker: Node3D = null
var _skeleton: Skeleton3D = null
var _slices: Array = [] # [{base: Vector3, tip: Vector3, age: float}]
var _active: bool = false
var _trail_shader: Shader = preload("res://shaders/katana_trail.gdshader")

func _ready() -> void:
	top_level = true
	# top_level 会把挂载时的全局变换固化为局部变换，必须清零归位（否则整条刀光平移偏移）
	transform = Transform3D.IDENTITY
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := ShaderMaterial.new()
	mat.shader = _trail_shader
	material_override = mat
	mesh = null
	visible = false

func setup(base_marker: Node3D, tip_marker: Node3D, skeleton: Skeleton3D) -> void:
	_base_marker = base_marker
	_tip_marker = tip_marker
	_skeleton = skeleton

func set_active(active: bool) -> void:
	_active = active
	# 停止采样后保留切片自然淡出，由 _physics_process 自行清空隐藏

func clear_trail() -> void:
	_slices.clear()
	visible = false
	mesh = null

func _physics_process(delta: float) -> void:
	# 切片老化
	for slice in _slices:
		slice.age += delta
	while not _slices.is_empty() and _slices[0].age >= FADE_TIME:
		_slices.pop_front()

	# 挥刀激活时追加原始采样（强制刷新骨骼变换，头部切片与刀身位姿精确贴合）
	if _active and _base_marker and _tip_marker:
		if _skeleton:
			_skeleton.force_update_all_bone_transforms()
		_slices.append({"base": _base_marker.global_position, "tip": _tip_marker.global_position, "age": 0.0})
		while _slices.size() > MAX_SLICES:
			_slices.pop_front()

	if _slices.size() >= 2:
		_rebuild_mesh()
		visible = true
	else:
		visible = false
		mesh = null

## 相邻切片间以相邻中点为控制做二次贝塞尔细分，令条带弧面平滑无折角
func _rebuild_mesh() -> void:
	var points: Array = [] # [{base, tip, t, fade}] t: 0=尾 1=头
	var n := _slices.size()
	for i in n:
		var s: Dictionary = _slices[i]
		var t_head: float = 1.0 - s.age / FADE_TIME
		# 挥刀中条带全亮；停手采样后按 0.12s 线性淡出
		var fade: float = 1.0 if _active else clampf(1.0 - s.age / FADE_TIME, 0.0, 1.0)
		if i == 0 or i == n - 1:
			points.append({"base": s.base, "tip": s.tip, "t": t_head, "fade": fade})
			continue
		var prev: Dictionary = _slices[i - 1]
		var next: Dictionary = _slices[i + 1]
		var ctrl_b: Vector3 = (prev.base + next.base) * 0.5
		var ctrl_t: Vector3 = (prev.tip + next.tip) * 0.5
		points.append({"base": ctrl_b.lerp(s.base, 0.5), "tip": ctrl_t.lerp(s.tip, 0.5), "t": t_head, "fade": fade})

	# 头部桥接：条带末端永远延伸到当前刀根/刀尖实际位置，确保刀光贴合刀身
	if _active and _base_marker and _tip_marker:
		if _skeleton:
			_skeleton.force_update_all_bone_transforms()
		var last: Dictionary = _slices[n - 1]
		var cur_base: Vector3 = _base_marker.global_position
		var cur_tip: Vector3 = _tip_marker.global_position
		if last.base.distance_to(cur_base) > 0.02 or last.tip.distance_to(cur_tip) > 0.02:
			points.append({"base": (last.base + cur_base) * 0.5, "tip": (last.tip + cur_tip) * 0.5, "t": 1.0, "fade": 1.0})
			points.append({"base": cur_base, "tip": cur_tip, "t": 1.0, "fade": 1.0})

	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	var count := points.size()
	for i in count:
		var p: Dictionary = points[i]
		verts.append(p.base)
		verts.append(p.tip)
		uvs.append(Vector2(0.0, p.t))
		uvs.append(Vector2(1.0, p.t))
		var c := Color(1, 1, 1, p.fade)
		colors.append(c)
		colors.append(c)
		if i > 0:
			var a := (i - 1) * 2
			var b := a + 1
			var c_i := i * 2
			var d := c_i + 1
			indices.append_array([a, b, c_i, b, d, c_i])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_COLOR] = colors
	arr[Mesh.ARRAY_INDEX] = indices
	var new_mesh := ArrayMesh.new()
	new_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	mesh = new_mesh
