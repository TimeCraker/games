class_name TrainingDummy
extends StaticBody3D

## 被动受击测试木桩（检验分级单体卡肉、漫反射闪白、伤害飘字与后仰击退）

const FLASH_DURATION := 0.06 ## 受击漫反射闪白时长(秒)

@onready var mesh_root: Node3D = $MeshRoot
@onready var info_label: Label3D = $InfoLabel
@onready var post_mesh: MeshInstance3D = $MeshRoot/PostMesh

var total_damage: float = 0.0
var hit_count: int = 0
var original_mesh_pos: Vector3 = Vector3.ZERO
var reset_timer: float = 0.0
var dummy_mat: StandardMaterial3D = null

# 单体局部卡肉：仅冻结自身后仰结算，全局时间不受影响
var freeze_timer: float = 0.0
var _pending_knock_offset: Vector3 = Vector3.ZERO
var _knock_tween: Tween = null
var _flash_tween: Tween = null
var _orig_albedo: Color = Color(1, 1, 1, 1)

func _ready() -> void:
	add_to_group("target_dummy")
	original_mesh_pos = mesh_root.position
	if post_mesh and post_mesh.mesh and post_mesh.mesh.material:
		dummy_mat = post_mesh.mesh.material as StandardMaterial3D
		_orig_albedo = dummy_mat.albedo_color
	update_info_display()

func _process(delta: float) -> void:
	# 冻结期间挂起后仰恢复与计数重置倒计时
	if freeze_timer > 0.0:
		freeze_timer -= delta
		if freeze_timer <= 0.0:
			_apply_pending_knock()
		return

	if reset_timer > 0.0:
		reset_timer -= delta
		if reset_timer <= 0.0:
			total_damage = 0.0
			hit_count = 0
			update_info_display()

func take_hit(damage: float, hit_dir: Vector3, is_heavy: bool, freeze_time: float = 0.0, knock_dist: float = -1.0, flash_time: float = FLASH_DURATION) -> void:
	total_damage += damage
	hit_count += 1
	reset_timer = 4.0
	update_info_display()

	# 生成伤害飘字（即时反馈）
	spawn_damage_number(damage, is_heavy)

	# 受击漫反射闪白：叠纯白高光后线性衰减回原材质
	flash_albedo(flash_time)

	# 后仰击退：单体冻结结束后才开始位移计算
	var knock_scale: float = knock_dist if knock_dist > 0.0 else (0.35 if is_heavy else 0.15)
	var knock_offset: Vector3 = hit_dir * knock_scale
	knock_offset.y = 0.0
	_pending_knock_offset = knock_offset
	apply_freeze(freeze_time)
	if freeze_timer <= 0.0:
		_apply_pending_knock()

func apply_freeze(duration: float) -> void:
	## 单体局部卡肉：冻结自身后仰与位移计算
	if duration <= 0.0:
		return
	freeze_timer = maxf(freeze_timer, duration)
	if _knock_tween and _knock_tween.is_valid():
		_knock_tween.kill()
		_knock_tween = null

func flash_albedo(duration: float) -> void:
	if dummy_mat == null:
		return
	if _flash_tween and _flash_tween.is_valid():
		_flash_tween.kill()
	# 漫反射叠纯白高光：白化系数 1 -> 0 线性衰减
	_flash_tween = create_tween()
	_flash_tween.tween_method(_set_albedo_flash, 1.0, 0.0, maxf(duration, 0.01))

func _set_albedo_flash(flash_factor: float) -> void:
	if dummy_mat:
		dummy_mat.albedo_color = _orig_albedo.lerp(Color(1, 1, 1, 1), flash_factor)

func _apply_pending_knock() -> void:
	if _knock_tween and _knock_tween.is_valid():
		_knock_tween.kill()
	_knock_tween = create_tween()
	_knock_tween.tween_property(mesh_root, "position", original_mesh_pos + _pending_knock_offset, 0.04)
	_knock_tween.tween_property(mesh_root, "position", original_mesh_pos, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)

func spawn_damage_number(damage: float, is_heavy: bool) -> void:
	var text_node: FloatingDamageText = FloatingDamageText.new()
	add_child(text_node)
	text_node.setup(damage, is_heavy, global_position + Vector3(0, 1.8, 0))

func update_info_display() -> void:
	if info_label:
		info_label.text = "【受击测试木桩】\n连击: %d 次 | 总伤: %d" % [hit_count, int(total_damage)]
