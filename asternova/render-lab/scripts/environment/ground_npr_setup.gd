extends Node
## AsterNova - Ground PBR NPR setup (第四执行组 Ground Pavement Pipeline 2.0).
## 对 modern_japan_neighborhood.glb 中现存的广场/坡道地面网格运行时覆盖材质：
## 中性暖灰大方砖 + 暖姜黄盲道 + 冷蓝灰沥青(坡道与广场全程连贯白实线)。
## 贴图来自 process_ground_pbr.py 2.0 程序化分频平铺产出的 2K PBR 套件。
## GLB 地面网格顶面 UV 为退化线性条（只采样贴图一行像素），因此全部启用
## 着色器的世界坐标 XZ 投影（use_world_uv），world_uv_period = 贴图世界尺寸(米)。
## 路面遗留的圆形空洞 Cylinder.086/.087 为无盖空心管（网格无顶盖），
## 运行时在其上加盖铸铁井盖贴花圆盘彻底封堵，圆管侧壁绑铸铁材质。

const SHADER_GROUND := preload("res://shaders/toon_ground_pbr.gdshader")
const TEX_DIR := "res://models/environment/ground/"

# 目标网格名 -> [贴图组, world_uv_period(米), uv_offset, 启用白实线路缘]
const ZONE_MAP := {
	"Plaza_Sidewalk_West": ["tiles", Vector2(2.4, 2.4), Vector2(0.0, 0.0), false],
	"Ramp_Sidewalk_West": ["tiles", Vector2(2.4, 2.4), Vector2(0.0, 0.0), false],
	"Plaza_Tactile_Line": ["tactile", Vector2(0.9, 0.9), Vector2(0.167, 0.0), false],
	"Plaza_Asphalt_Road": ["asphalt", Vector2(2.5, 2.5), Vector2(0.0, 0.0), true],
	"Ramp_Asphalt_Road": ["asphalt", Vector2(2.5, 2.5), Vector2(0.0, 0.0), true],
}

# 路面圆形空洞 (GLB 实测 Cylinder.086 r=0.48 / .087 r=0.41 @ glb(-2.2,-18); 场景实例 z 镜像 -> Godot z=+18)
const MANHOLE_CENTER := Vector3(-2.20, 0.056, 18.00)   # GLB z 镜像后的 Godot 世界坐标
const MANHOLE_COVER_SIZE := 1.01        # 圆盘边长: 贴花圆盘直径 0.956x1.01 ≈ 0.97m 盖住 r=0.48 框圈

var _textures: Dictionary = {}
var _cover_sealed := false          # 086/087 共用一枚井盖圆盘, 防同位双盘 z-fighting

## M1 Forward+ AgX 母版标定: AgX 压中调 + 太阳 45° 直射, 方砖/盲道白场按新响应
## 曲线重标 (0.45 -> 0.24, 乘性材质校准非后期压暗); 沥青取纠偏令区间上沿 1.0。
## Tier 1 地面评审场景 (Filmic + 65° 高阳) 保持默认 false 的历史标定值。
@export var agx_light_master := false


func _ready() -> void:
	_load_textures()
	# 遍历父级（场景根），而非自身子树：本节点只作为独立挂载的驱动器
	_apply(get_parent())


func _load_textures() -> void:
	for group in ["tiles", "tactile", "asphalt"]:
		_textures[group] = {
			"albedo": load(TEX_DIR + "ground_%s_albedo.png" % group),
			"normal": load(TEX_DIR + "ground_%s_normal.png" % group),
			"roughness": load(TEX_DIR + "ground_%s_roughness.png" % group),
		}
	_textures["tiles"]["ao"] = load(TEX_DIR + "ground_tiles_ao.png")
	_textures["stripe"] = load(TEX_DIR + "road_marking_edge_decal.png")


func _apply(root: Node) -> void:
	for child in root.get_children():
		# 自管 gameplay 预制体 (便利店/贩卖机等 StaticBody3D, 自带 NPR 脚本) 整树跳过:
		# 防止本驱动的日景熄灯/材质处理污染其橱窗自发光与 toon 绑定
		if child is StaticBody3D:
			continue
		if child is MeshInstance3D:
			var node_name := String(child.name)
			for zone_name in ZONE_MAP:
				# GLB 节点在 Godot 导入后名字保持，模糊匹配防实例化改名
				if node_name.findn(zone_name) >= 0:
					_setup_mesh(child, zone_name)
			if _is_manhole_hole(node_name):
				_seal_manhole_hole(child)
			# 日景评审: 压掉楼群窗灯自发光 (招牌/贩卖机/广告牌保留夜景功能光)
			if node_name.findn("Store") < 0 and node_name.findn("Vending") < 0 \
					and node_name.findn("Sign") < 0 and node_name.findn("Billboard") < 0:
				_suppress_emission(child)
			# 悬空伪影按节点名消灭 (纠偏令, 禁用 AABB 世界坐标猜测):
			# 交通凸面镜/环/圆环道具, 以及 Cylinder_16/17/18/19/Cylinder_2 开头的
			# 电线杆悬空装饰圆柱片 (红环本体), 一律隐藏。
			# Cylinder_086/087 (井盖洞) 以 Cylinder_0 开头, 不受影响。
			if node_name.findn("Mirror") >= 0 or node_name.findn("Ring") >= 0 \
					or node_name.findn("Torus") >= 0 \
					or node_name.begins_with("Cylinder_16") \
					or node_name.begins_with("Cylinder_17") \
					or node_name.begins_with("Cylinder_18") \
					or node_name.begins_with("Cylinder_19") \
					or node_name.begins_with("Cylinder_2"):
				child.visible = false
				print("[ground_npr] hide artifact prop: ", node_name)
		_apply(child)


func _suppress_emission(mi: MeshInstance3D) -> void:
	for i in mi.mesh.get_surface_count():
		var mat := mi.mesh.surface_get_material(i)
		if mat is StandardMaterial3D and mat.emission_enabled:
			var off: StandardMaterial3D = mat.duplicate()
			off.emission_enabled = false
			mi.set_surface_override_material(i, off)


## GLB 源节点名为 "Cylinder.086/.087", Godot 导入后规范化为 "Cylinder_086/_087"
func _is_manhole_hole(node_name: String) -> bool:
	return node_name.findn("Cylinder") == 0 \
			and (node_name.ends_with("086") or node_name.ends_with("087"))


func _setup_mesh(mi: MeshInstance3D, zone_name: String) -> void:
	var cfg: Array = ZONE_MAP[zone_name]
	var group: String = cfg[0]
	var period: Vector2 = cfg[1]
	var uv_off: Vector2 = cfg[2]
	var edge_stripe: bool = cfg[3]
	var tex: Dictionary = _textures[group]
	# 沥青法线深度 0.8~1.0 (纠偏令: 骨料咬合感 + SSAO); 方砖/盲道保持 0.14 细腻微倒角
	var normal_depth := 0.9 if group == "asphalt" else 0.14
	# 地面材质增益按官方母版 (AgX 4 + 曝光 1.0 + 太阳 1.1) 标定:
	# 方砖白场阳面目标 ~205 (STYLE #D5D8DC~#E0E0E8), 沥青深灰骨料 #34373D 取
	# 纠偏令区间上沿的直射可读值; 只动本材质参数, 严禁改官方灯光/环境
	var gain: float
	if agx_light_master:
		gain = 1.35 if group == "asphalt" else 0.30
	elif group == "tactile":
		gain = 0.33
	else:
		gain = 0.85 if group == "asphalt" else 0.28
	var fill: float
	if agx_light_master:
		fill = 0.55 if group == "asphalt" else 0.15
	else:
		fill = 1.4 if group == "asphalt" else 0.15
	for i in mi.mesh.get_surface_count():
		var mat := ShaderMaterial.new()
		mat.shader = SHADER_GROUND
		mat.set_shader_parameter("albedo_texture", tex["albedo"])
		mat.set_shader_parameter("normal_texture", tex["normal"])
		mat.set_shader_parameter("roughness_texture", tex["roughness"])
		mat.set_shader_parameter("ao_texture", tex.get("ao"))
		mat.set_shader_parameter("use_world_uv", true)
		mat.set_shader_parameter("world_uv_period", period)
		mat.set_shader_parameter("uv_offset", uv_off)
		mat.set_shader_parameter("normal_depth", normal_depth)
		mat.set_shader_parameter("diffuse_gain", gain)
		mat.set_shader_parameter("ambient_fill", fill)
		if edge_stripe:
			# 车道两侧 0.2m 白实线沿世界 x=±4 路缘, 坡道与广场共用同一世界坐标
			# => 全程连贯无接缝断口; 白漆 #E8ECF0 rough 0.55, 贴花纵向周期 0.8m
			mat.set_shader_parameter("edge_stripe_texture", _textures["stripe"])
			mat.set_shader_parameter("edge_stripe_line_width", 0.2)
			mat.set_shader_parameter("edge_stripe_center", 0.0)
			mat.set_shader_parameter("edge_stripe_half_width", 4.0)
			mat.set_shader_parameter("edge_stripe_world_period", 0.8)
			mat.set_shader_parameter("edge_stripe_roughness", 0.55)
			mat.set_shader_parameter("edge_stripe_feather", 0.02)
			# 坡道底部横向过街斑马线 (世界 z≈13.5, 纵深 2.6m, 0.45m 白条/0.45m 空隙)
			mat.set_shader_parameter("crosswalk_center_z", 13.5)
			mat.set_shader_parameter("crosswalk_depth", 2.6)
			mat.set_shader_parameter("crosswalk_span_half", 3.6)
			mat.set_shader_parameter("crosswalk_stripe_w", 0.45)
			mat.set_shader_parameter("crosswalk_gap", 0.45)
			mat.set_shader_parameter("crosswalk_roughness", 0.55)
			mat.set_shader_parameter("crosswalk_feather", 0.025)
		mi.set_surface_override_material(i, mat)
	print("[ground_npr] %s -> %s (world_uv_period=%s, offset=%s, edge_stripe=%s)" % [
			zone_name, group, period, uv_off, edge_stripe])


func _seal_manhole_hole(mi: MeshInstance3D) -> void:
	# 空心管侧壁: 深色铸铁材质 (StandardMaterial3D 接收反射探针与天光)
	var iron := StandardMaterial3D.new()
	iron.albedo_color = Color(0.204, 0.216, 0.239)      # #34373D
	iron.metallic = 0.45
	iron.roughness = 0.42
	for i in mi.mesh.get_surface_count():
		mi.set_surface_override_material(i, iron)

	# 井盖圆盘: 一枚覆盖 086/087 双框圈, 贴花正圆 + alpha_scissor 零排序开销
	if _cover_sealed:
		print("[ground_npr] %s: 铸铁侧壁材质 (井盖圆盘已由首洞放置)" % mi.name)
		return
	_cover_sealed = true
	var cover := MeshInstance3D.new()
	cover.name = "ManholeCover_%s" % mi.name
	var plane := PlaneMesh.new()
	plane.size = Vector2(MANHOLE_COVER_SIZE, MANHOLE_COVER_SIZE)
	cover.mesh = plane

	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load(TEX_DIR + "manhole_cover_decal.png")
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.normal_enabled = true
	mat.normal_texture = load(TEX_DIR + "manhole_cover_decal_normal.png")
	mat.normal_scale = 0.7
	mat.roughness_texture = load(TEX_DIR + "manhole_cover_decal_roughness.png")
	mat.metallic_texture = load(TEX_DIR + "manhole_cover_decal_metallic.png")
	mat.metallic = 0.66          # 贴花金属度 0.45 x 0.66: 保漫反射可读, 阴影里不成黑板
	cover.material_override = mat

	# _ready 阶段场景树仍在装配, add_child 必须延迟; 入树后再写世界坐标
	get_tree().current_scene.add_child.call_deferred(cover)
	_place_cover.call_deferred(cover)
	print("[ground_npr] %s: 铸铁侧壁材质 + 井盖圆盘封堵 @ %s" % [mi.name, MANHOLE_CENTER])


func _place_cover(cover: MeshInstance3D) -> void:
	if cover.is_inside_tree():
		cover.global_position = MANHOLE_CENTER
