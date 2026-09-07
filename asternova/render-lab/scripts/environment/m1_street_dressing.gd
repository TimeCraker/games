extends Node
## AsterNova - M1 street dressing driver (街区生活烟火气装配驱动器).
## 三块职责: ① Tier 3 生活道具落位(空调外机群/电线杆/垃圾站/锥桶)
##          ② 架空跨街电缆(悬链线抛物近似, 破除头顶晴空生硬空洞)
##          ③ 建筑外立面二阶微表面 Decal(拼缝/防撞警示/雨水风化, 克制清爽)
## 所有坐标取自 m1_street_inventory.gd 无头标定 dump (2026-09-07):
##   Ramp_East_Retaining_Wall 西立面 x=4.0 (z -25..15, 顶 y=5.5);
##   HouseA/B 东墙 1F x=-10.6 / 2F x=-10.9;
##   坡道顶面 y(z) = -0.04611 + (14.71785 - z) * 0.179856;
##   西侧既有电线杆 x=-4.8 (横担 z=14.5 @ y 9.2~9.85 / z=-5 @ y 12.65~13.35)。
## 空调外机 GLB 原点 = 背板底边中点, 机头朝本地 -Z, 宽度沿本地 X。

const PREFAB_AC_SINGLE := preload("res://scenes/entities/props/ACUnitSingle.tscn")
const PREFAB_AC_DOUBLE := preload("res://scenes/entities/props/ACUnitDouble.tscn")
const PREFAB_POLE := preload("res://scenes/entities/props/UtilityPole.tscn")
const PREFAB_TRASH := preload("res://scenes/entities/props/TrashStation4Bin.tscn")
const PREFAB_CONE := preload("res://scenes/entities/props/TrafficCone.tscn")

const TEX_DIR := "res://models/environment/decals/"

# 坡道顶面高度 (Ramp_Asphalt_Road AABB 线性拟合)
const RAMP_TOP_Z := 14.71785
const RAMP_Y0 := -0.04611
const RAMP_SLOPE := 0.179856

# 杆顶绝缘子挂点世界高度 (墙顶 5.5 + 杆局部 8.035)
const E_POLE_TOP_Y := 13.535

## 道具落位表: [prefab, 原点, yaw_deg, 缩放]
## AC 朝向: 机头 -Z; HouseA/B 东墙(法线 +X)用 -90, 东挡墙西立面(法线 -X)用 +90
const PROPS := [
	# --- HouseA/B 东墙 2F 檐下 (y=5.55: 西挡墙顶 5.5 之上的唯一可见带) ---
	[PREFAB_AC_DOUBLE, Vector3(-10.9, 5.55, 2.2), -90.0, 1.0],
	[PREFAB_AC_SINGLE, Vector3(-10.9, 5.55, 6.6), -90.0, 1.0],
	[PREFAB_AC_SINGLE, Vector3(-10.9, 5.55, -2.6), -90.0, 1.0],
	[PREFAB_AC_DOUBLE, Vector3(-10.9, 5.55, -6.0), -90.0, 1.0],
	# --- 东挡墙西立面 (主镜头右半幅最可见墙面) ---
	[PREFAB_AC_SINGLE, Vector3(4.0, 4.3, 2.0), 90.0, 1.0],
	[PREFAB_AC_DOUBLE, Vector3(4.0, 4.6, -3.5), 90.0, 1.0],
	# --- 西挡墙东立面 (主镜头左中景暗墙, 贴墙单机) ---
	[PREFAB_AC_SINGLE, Vector3(-6.8, 4.5, 10.5), -90.0, 1.0],
	# --- 东侧电线杆 x2 (立于挡墙顶 y=5.5, x=墙中线 4.6) ---
	[PREFAB_POLE, Vector3(4.6, 5.5, 9.0), 0.0, 1.0],
	[PREFAB_POLE, Vector3(4.6, 5.5, -12.0), 0.0, 1.0],
	# --- 日式四分类垃圾站 (西人行道, 贩卖机群南侧留白) ---
	[PREFAB_TRASH, Vector3(-6.9, 0.2, 20.4), -12.0, 1.0],
	# --- 警示锥桶 (贩卖机东北角 x1 + 东路肩 x2) ---
	[PREFAB_CONE, Vector3(-7.8, 0.2, 17.7), 15.0, 1.0],
	[PREFAB_CONE, Vector3(3.55, 0.0, 20.6), -8.0, 1.0],
	[PREFAB_CONE, Vector3(3.5, 0.0, 24.4), 22.0, 1.0],
]

## 电缆跨表: [起点, 终点, 下垂量 m, 半径 m]
const CABLE_SPANS := [
	[Vector3(-4.8, 9.80, 14.5), Vector3(3.82, E_POLE_TOP_Y, 9.0), 0.60, 0.020],
	[Vector3(-3.85, 9.60, 14.5), Vector3(5.38, E_POLE_TOP_Y, 9.0), 0.50, 0.017],
	[Vector3(-4.8, 13.31, -5.0), Vector3(3.82, E_POLE_TOP_Y, -12.0), 0.70, 0.020],
	[Vector3(3.82, E_POLE_TOP_Y, 9.0), Vector3(3.82, E_POLE_TOP_Y, -12.0), 1.00, 0.022],
	[Vector3(5.38, E_POLE_TOP_Y, 9.0), Vector3(5.38, E_POLE_TOP_Y, -12.0), 0.90, 0.017],
	[Vector3(5.38, E_POLE_TOP_Y, 9.0), Vector3(-4.8, 13.31, -5.0), 0.80, 0.017],
	# 引入线: E1 下部支架 -> HouseA 东墙单担 (含墙担小盒)
	[Vector3(4.74, 9.85, 9.0), Vector3(-10.57, 5.8, -4.0), 0.90, 0.013],
]

## 贴花表: [贴图组, 世界坐标, 贴墙面法线(+X/-X/地面), 尺寸(宽,深,高), 不透明度]
const DECALS := [
	# --- 东挡墙西立面: 拼缝网格 (顶 y=5.5, 下沿随坡道面抬升) ---
	["seam", Vector3(4.0, 3.09, 12.0), Vector3.LEFT, 6.0, 4.42, 1.0],
	["seam", Vector3(4.0, 3.63, 6.0), Vector3.LEFT, 6.0, 3.34, 1.0],
	["seam", Vector3(4.0, 4.17, 0.0), Vector3.LEFT, 6.0, 2.26, 1.0],
	["seam", Vector3(4.0, 4.91, -6.0), Vector3.LEFT, 6.0, 1.18, 1.0],
	# --- 东挡墙: 檐下雨水冲刷痕 (上) + 贴地潮气 (下), 克制 ---
	["rain", Vector3(4.0, 4.35, 10.0), Vector3.LEFT, 4.0, 2.3, 0.8],
	["rain", Vector3(4.0, 4.35, 1.0), Vector3.LEFT, 4.0, 2.3, 0.8],
	["rain", Vector3(4.0, 4.35, -7.0), Vector3.LEFT, 4.0, 2.3, 0.8],
	# --- 东挡墙路口端: 黄黑防撞警示 (护栏角) ---
	["hazard", Vector3(4.0, 0.75, 14.4), Vector3.LEFT, 1.2, 1.5, 1.0],
	# --- HouseB 东墙: 1F 拼缝 + 窗台水痕 + 2F 窗台水痕 ---
	["seam", Vector3(-10.6, 1.85, 4.5), Vector3.RIGHT, 5.0, 2.6, 0.9],
	["rain", Vector3(-10.6, 1.2, 4.5), Vector3.RIGHT, 2.2, 2.0, 0.55],
	["rain", Vector3(-10.9, 2.75, 4.5), Vector3.RIGHT, 1.6, 1.3, 0.55],
	# --- HouseA 东墙: 1F 拼缝 + 2F 窗台水痕 ---
	["seam", Vector3(-10.6, 1.85, -5.5), Vector3.RIGHT, 5.0, 2.6, 0.9],
	["rain", Vector3(-10.9, 2.75, -4.2), Vector3.RIGHT, 1.6, 1.3, 0.55],
	# --- 便利店进门台阶: 黄黑防撞条 (东立面门前地面) ---
	["hazard", Vector3(-9.7, 0.212, 21.9), Vector3.DOWN, 0.9, 2.2, 1.0],
	# --- 空调外机滴水痕 (随外机布位, 低透明度) ---
	["rain", Vector3(-10.9, 4.0, 2.2), Vector3.RIGHT, 0.9, 1.4, 0.5],
	["rain", Vector3(-10.9, 4.0, 6.6), Vector3.RIGHT, 0.9, 1.4, 0.5],
	["rain", Vector3(-10.9, 4.0, -2.6), Vector3.RIGHT, 0.9, 1.4, 0.5],
	["rain", Vector3(-10.9, 4.0, -6.0), Vector3.RIGHT, 0.9, 1.4, 0.5],
	["rain", Vector3(4.0, 3.5, 2.0), Vector3.LEFT, 0.9, 1.4, 0.5],
	["rain", Vector3(4.0, 3.8, -3.5), Vector3.LEFT, 0.9, 1.4, 0.5],
	["rain", Vector3(-6.8, 3.7, 10.5), Vector3.RIGHT, 0.9, 1.4, 0.5],
]

var _decal_textures := {}


func _ready() -> void:
	_load_decal_textures()
	_place_props()
	_build_cables()
	_place_decals()
	print("[m1_dressing] props=%d spans=%d decals=%d" % [
			PROPS.size(), CABLE_SPANS.size(), DECALS.size()])


func _load_decal_textures() -> void:
	for group in ["concrete_seam_grid", "hazard_stripes", "rain_streaks"]:
		var entry := {
			"albedo": load(TEX_DIR + "%s_albedo.png" % group),
			"orm": load(TEX_DIR + "%s_orm.png" % group),
		}
		if group == "concrete_seam_grid":
			entry["normal"] = load(TEX_DIR + "%s_normal.png" % group)
		# DECALS 表内使用短名
		var short: String = {
			"concrete_seam_grid": "seam",
			"hazard_stripes": "hazard",
			"rain_streaks": "rain",
		}[group]
		_decal_textures[short] = entry


func _place_props() -> void:
	for entry in PROPS:
		var prefab: PackedScene = entry[0]
		var node := prefab.instantiate() as Node3D
		node.position = entry[1]
		node.rotation_degrees = Vector3(0, entry[2], 0)
		node.scale = Vector3.ONE * float(entry[3])
		add_child(node)


func _build_cables() -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.145, 0.155, 0.175)   # 深灰铝缆, 非死黑
	mat.metallic = 0.35
	mat.roughness = 0.55
	# HouseA 墙担小盒 (引入线终点锚固件)
	var anchor := MeshInstance3D.new()
	anchor.name = "ServiceAnchorBox"
	var box := BoxMesh.new()
	box.size = Vector3(0.07, 0.12, 0.22)
	anchor.mesh = box
	anchor.material_override = mat
	anchor.position = Vector3(-10.56, 5.8, -4.0)
	add_child(anchor)
	for i in CABLE_SPANS.size():
		var span: Array = CABLE_SPANS[i]
		var mi := MeshInstance3D.new()
		mi.name = "CableSpan%d" % i
		mi.mesh = _catenary_mesh(span[0], span[1], span[2], span[3])
		mi.material_override = mat
		add_child(mi)


## 悬链线抛物近似: y(t) = lerp(y0,y1,t) - sag*4*t*(1-t); 8 棱圆管 32 采样
func _catenary_mesh(a: Vector3, b: Vector3, sag: float, radius: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	const SAMPLES := 32
	const RADIAL := 8
	var prev_ring := PackedVector3Array()
	for s in SAMPLES + 1:
		var t := float(s) / SAMPLES
		var p := a.lerp(b, t)
		p.y -= sag * 4.0 * t * (1.0 - t)
		var tangent := (b - a).normalized()
		tangent.y -= sag * 4.0 * (1.0 - 2.0 * t) / (b - a).length()
		tangent = tangent.normalized()
		var side := tangent.cross(Vector3.UP)
		if side.length() < 0.01:
			side = tangent.cross(Vector3.RIGHT)
		side = side.normalized()
		var up := side.cross(tangent).normalized()
		var ring := PackedVector3Array()
		for r in RADIAL:
			var ang := TAU * float(r) / RADIAL
			ring.append(p + (side * cos(ang) + up * sin(ang)) * radius)
		if s > 0:
			for r in RADIAL:
				var r2 := (r + 1) % RADIAL
				var v0 := prev_ring[r]
				var v1 := prev_ring[r2]
				var v2 := ring[r2]
				var v3 := ring[r]
				st.add_vertex(v0)
				st.add_vertex(v1)
				st.add_vertex(v2)
				st.add_vertex(v0)
				st.add_vertex(v2)
				st.add_vertex(v3)
		prev_ring = ring
	st.generate_normals()
	return st.commit()


## 贴花布设: 法线给投影方向 (Decal 沿本地 -Y 投影);
## 贴墙时 basis: Y=法线, Z=世界上方向, X=Y×Z; 地面 decal 用默认朝向
func _place_decals() -> void:
	for entry in DECALS:
		var group: String = entry[0]
		var normal: Vector3 = entry[2]
		var tex: Dictionary = _decal_textures[group]
		var decal := Decal.new()
		decal.texture_albedo = tex["albedo"]
		decal.texture_orm = tex["orm"]
		if tex.has("normal"):
			decal.texture_normal = tex["normal"]
		var alpha: float = entry[5]
		decal.modulate = Color(1, 1, 1, alpha)
		decal.cull_mask = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4)
		if normal == Vector3.DOWN:
			decal.size = Vector3(entry[3], 0.5, entry[4])
			decal.position = entry[1]
		else:
			var width: float = entry[3]
			var depth: float = entry[4]
			decal.size = Vector3(width, 0.5, depth)
			# basis: Y=墙面外法线(投影沿 -Y 打回墙面), Z=世界上方向(贴花上沿),
			# X=Y×Z (正交右手); 位置沿法线抬升半深度, 留 0.03 咬入墙面
			var y_axis := normal
			var z_axis := Vector3.UP
			var x_axis := y_axis.cross(z_axis)
			decal.basis = Basis(x_axis, y_axis, z_axis)
			decal.position = entry[1] + normal * (decal.size.y * 0.5 - 0.03)
		decal.name = "Decal_%s_%d" % [group, get_child_count()]
		add_child(decal)
