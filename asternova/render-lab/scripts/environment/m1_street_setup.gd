extends Node
## AsterNova - M1 Endfield street sandbox scenery purge (M1 终极街区沙盒).
## 按节点名 (GLB 源名, 禁止 AABB 世界坐标猜测) 铲除两类违章体块:
## 1. 背景死黑马赛克方块楼: 四组远景塔楼群 (Tower_Body/Podium/Billboard 全家桶)
##    + West_Mansion 的 6 片铝板楼板 (Cube_65..70), 露出开阔双半球天光地平线;
## 2. 旧街区内置便利店空心砖壳 (无内部, 被 Tier 2 折角便利店整体替换):
##    ConvenienceStore_Front_Glass/Sign_Face/Sign_Housing + 砖墙/台阶 Cube_141..218。
## 自管 StaticBody3D 预制体 (便利店/贩卖机) 与 Tier 1 地面五网格不受影响。

## 塔楼残骸楼板 (GLB 实测逐节点归类, 按种类+编号隐藏, 鸟居 Cylinder_001 不受影响):
## Cube 5..50 = 北塔/南塔楼板环板, 65..89 = 西豪宅/东天际楼板; Cylinder 2..7 = 北/南塔
## 屋顶水箱, 10..13 = 西豪宅/东天际水箱。141..218 = 旧便利店砖壳/地台/入口踏步。
const HIDE_CUBE_RANGES := [Vector2i(5, 50), Vector2i(65, 89), Vector2i(141, 218)]
const HIDE_CYLINDER_RANGES := [Vector2i(2, 7), Vector2i(10, 13)]
const HIDE_PREFIXES := ["East_Skyline", "North_Tower", "South_Tower", "West_Mansion"]
const HIDE_NAMES := [
	"ConvenienceStore_Front_Glass",
	"ConvenienceStore_Sign_Face",
	"ConvenienceStore_Sign_Housing",
]


func _ready() -> void:
	_apply(get_parent())


func _apply(root: Node) -> void:
	for child in root.get_children():
		# 自管 gameplay 预制体 (自带 NPR 脚本) 整树跳过
		if child is StaticBody3D:
			continue
		if child is MeshInstance3D:
			var node_name := String(child.name)
			if _should_hide(node_name):
				child.visible = false
				print("[m1_street] purge: ", node_name)
		_apply(child)


func _should_hide(node_name: String) -> bool:
	for prefix in HIDE_PREFIXES:
		if node_name.begins_with(prefix):
			return true
	for target in HIDE_NAMES:
		if node_name == target:
			return true
	# GLB "Cube.141" -> Godot 导入规范化为 "Cube_141" (前导零保留, "Cube_065")
	if node_name.begins_with("Cube_") or node_name.begins_with("Cylinder_"):
		var kind_len := 5 if node_name.begins_with("Cube_") else 9
		var suffix := node_name.substr(kind_len)
		if suffix.is_valid_int():
			var id := suffix.to_int()
			var ranges: Array = HIDE_CUBE_RANGES if kind_len == 5 else HIDE_CYLINDER_RANGES
			for range_v: Vector2i in ranges:
				if id >= range_v.x and id <= range_v.y:
					return true
	return false
