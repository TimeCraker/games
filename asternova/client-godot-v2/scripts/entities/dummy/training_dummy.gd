class_name TrainingDummy
extends StaticBody3D

## 被动受击测试木桩（检验分级单体卡肉、漫反射闪白、伤害飘字与顺切线受击推力刹停）

const FLASH_DURATION := 0.05 ## 受击漫反射闪白时长(秒)
const KNOCK_STOP_LIGHT := 0.15 ## 轻击弹性摩擦阻尼刹停时长(秒)
const KNOCK_STOP_HEAVY := 0.20 ## 重击强力推力刹停时长(秒)
const KNOCK_SETTLE_HOLD := 1.2 ## 刹停后驻留时长(秒,随后平滑归位)
const KNOCK_RETURN_TIME := 0.40 ## 驻留结束平滑归位时长(秒,无弹性过冲)
const KNOCK_LIGHT_DISTANCE := 0.35 ## 轻击默认推移距离(米,与 CombatData.knockback_light_distance 对齐)
const KNOCK_HEAVY_DISTANCE := 0.80 ## 重击默认推移距离(米,与 CombatData.knockback_heavy_distance 对齐)
const KNOCK_TANGENT_FACTOR := 0.15 ## 微弱刀锋切向分量系数(与 CombatData.knockback_tangent_factor 对齐)

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

# 顺切线受击推力（解析式二次缓出：速度线性衰减→迅速减速刹停，位移精确无积分漂移）
var _knock_active: bool = false
var _knock_dir: Vector3 = Vector3.ZERO
var _knock_dist: float = 0.0
var _knock_stop_time: float = 0.0
var _knock_elapsed: float = 0.0
var _knock_base_offset: Vector3 = Vector3.ZERO ## 本次推力启动时已有的累计偏移(支持连击叠加)
var _knock_settle_timer: float = 0.0
var _pending_knock_dir: Vector3 = Vector3.ZERO
var _pending_knock_dist: float = 0.0
var _pending_knock_stop: float = 0.0
var _return_tween: Tween = null
var _flash_timer: float = 0.0
var _flash_duration: float = FLASH_DURATION
var _orig_albedo: Color = Color(1, 1, 1, 1)

func _ready() -> void:
	add_to_group("target_dummy")
	original_mesh_pos = mesh_root.position
	if post_mesh and post_mesh.mesh and post_mesh.mesh.material:
		dummy_mat = post_mesh.mesh.material as StandardMaterial3D
		_orig_albedo = dummy_mat.albedo_color
	update_info_display()

func _physics_process(delta: float) -> void:
	# 白闪计时：物理帧固定步长驱动（线性消隐，与战斗门禁 tick 精确同步）
	if _flash_timer > 0.0:
		_flash_timer -= delta
		_set_albedo_flash(maxf(_flash_timer / _flash_duration, 0.0))
		if _flash_timer <= 0.0:
			_set_albedo_flash(0.0)

	# 冻结期间挂起推力与重置倒计时
	if freeze_timer > 0.0:
		freeze_timer -= delta
		if freeze_timer <= 0.0:
			_begin_knockback()
		return

	# 推力进行中：offset(t) = base + dir * dist * (1-(1-k)^2)，速度线性衰减至零刹停
	if _knock_active:
		_knock_elapsed += delta
		var k: float = clampf(_knock_elapsed / _knock_stop_time, 0.0, 1.0)
		var eased: float = 1.0 - (1.0 - k) * (1.0 - k)
		mesh_root.position = original_mesh_pos + _knock_base_offset + _knock_dir * (_knock_dist * eased)
		if k >= 1.0:
			_knock_active = false
			_knock_settle_timer = KNOCK_SETTLE_HOLD
		return

	# 刹停驻留计时，结束后平滑归位
	if _knock_settle_timer > 0.0:
		_knock_settle_timer -= delta
		if _knock_settle_timer <= 0.0:
			_begin_knock_return()
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

	# 顺切线受击推力：径向 = 攻击者→木桩(hit_dir)，叠加微弱刀锋切向分量
	var radial: Vector3 = hit_dir
	radial.y = 0.0
	if radial.length_squared() < 0.01:
		radial = Vector3.FORWARD
	radial = radial.normalized()
	var tangent: Vector3 = Vector3.UP.cross(radial).normalized() * KNOCK_TANGENT_FACTOR
	_pending_knock_dir = (radial + tangent).normalized()
	_pending_knock_dist = knock_dist if knock_dist > 0.0 else (KNOCK_HEAVY_DISTANCE if is_heavy else KNOCK_LIGHT_DISTANCE)
	_pending_knock_stop = KNOCK_STOP_HEAVY if is_heavy else KNOCK_STOP_LIGHT
	apply_freeze(freeze_time)
	if freeze_timer <= 0.0:
		_begin_knockback()

func apply_freeze(duration: float) -> void:
	## 单体局部卡肉：冻结自身推力启动
	if duration <= 0.0:
		return
	freeze_timer = maxf(freeze_timer, duration)

func reset_knockback() -> void:
	## 立即清除推力状态并归位（连击测试辅助；正常连击走叠加基准模型）
	_knock_active = false
	_knock_settle_timer = 0.0
	_knock_base_offset = Vector3.ZERO
	if _return_tween and _return_tween.is_valid():
		_return_tween.kill()
	mesh_root.position = original_mesh_pos

func flash_albedo(duration: float) -> void:
	if dummy_mat == null:
		return
	# 漫反射叠纯白高光：受击当帧立即全亮，随后物理帧线性衰减消隐
	_set_albedo_flash(1.0)
	_flash_duration = maxf(duration, 0.01)
	_flash_timer = _flash_duration

func _set_albedo_flash(flash_factor: float) -> void:
	if dummy_mat:
		dummy_mat.albedo_color = _orig_albedo.lerp(Color(1, 1, 1, 1), flash_factor)

func _begin_knockback() -> void:
	if _pending_knock_dist <= 0.0:
		return
	if _return_tween and _return_tween.is_valid():
		_return_tween.kill()
	# 从当前偏移继续叠加（连击时不瞬移回原点，杜绝抖动）
	_knock_base_offset = mesh_root.position - original_mesh_pos
	_knock_dir = _pending_knock_dir
	_knock_dist = _pending_knock_dist
	_knock_stop_time = maxf(_pending_knock_stop, 0.02)
	_knock_elapsed = 0.0
	_knock_active = true
	_knock_settle_timer = 0.0

func _begin_knock_return() -> void:
	## 刹停驻留结束后平滑归位（QUAD 缓出无过冲，贴地不抖动）
	if _return_tween and _return_tween.is_valid():
		_return_tween.kill()
	_return_tween = create_tween()
	_return_tween.tween_property(mesh_root, "position", original_mesh_pos, KNOCK_RETURN_TIME).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)

func spawn_damage_number(damage: float, is_heavy: bool) -> void:
	var text_node: FloatingDamageText = FloatingDamageText.new()
	add_child(text_node)
	text_node.setup(damage, is_heavy, global_position + Vector3(0, 1.8, 0))

func update_info_display() -> void:
	if info_label:
		info_label.text = "【受击测试木桩】\n连击: %d 次 | 总伤: %d" % [hit_count, int(total_damage)]
