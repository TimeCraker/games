class_name TrainingDummy
extends StaticBody3D

## 被动受击测试木桩（检验普攻4段卡肉、伤害飘字与后仰晃动）

@onready var mesh_root: Node3D = $MeshRoot
@onready var info_label: Label3D = $InfoLabel

var total_damage: float = 0.0
var hit_count: int = 0
var original_mesh_pos: Vector3 = Vector3.ZERO
var reset_timer: float = 0.0

func _ready() -> void:
	add_to_group("target_dummy")
	original_mesh_pos = mesh_root.position
	update_info_display()

func _process(delta: float) -> void:
	if reset_timer > 0.0:
		reset_timer -= delta
		if reset_timer <= 0.0:
			total_damage = 0.0
			hit_count = 0
			update_info_display()

func take_hit(damage: float, hit_dir: Vector3, is_heavy: bool) -> void:
	total_damage += damage
	hit_count += 1
	reset_timer = 4.0
	update_info_display()

	# 生成伤害飘字
	spawn_damage_number(damage, is_heavy)

	# 受击倾斜晃动反馈 (Tween)
	var tween: Tween = create_tween()
	var knock_offset: Vector3 = hit_dir * (0.35 if is_heavy else 0.15)
	knock_offset.y = 0.0
	tween.tween_property(mesh_root, "position", original_mesh_pos + knock_offset, 0.04)
	tween.tween_property(mesh_root, "position", original_mesh_pos, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)

func spawn_damage_number(damage: float, is_heavy: bool) -> void:
	var text_node: FloatingDamageText = FloatingDamageText.new()
	add_child(text_node)
	text_node.setup(damage, is_heavy, global_position + Vector3(0, 1.8, 0))

func update_info_display() -> void:
	if info_label:
		info_label.text = "【受击测试木桩】\n连击: %d 次 | 总伤: %d" % [hit_count, int(total_damage)]
