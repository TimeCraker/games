extends Node3D

# --- Node References ---
@onready var camera: Camera3D = $CameraPivot/Camera3D
@onready var camera_pivot: Node3D = $CameraPivot
@onready var weapon_anchor: Node3D = $WeaponAnchor
@onready var ui_root: CanvasLayer = $UI
@onready var info_panel: PanelContainer = $UI/InfoPanel
@onready var control_panel: PanelContainer = $UI/ControlPanel
@onready var help_bar: PanelContainer = $UI/HelpBar
@onready var btn_draw: Button = $UI/ControlPanel/Margin/VBox/BtnDraw
@onready var btn_auto_rotate: Button = $UI/ControlPanel/Margin/VBox/BtnAutoRotate
@onready var btn_reset: Button = $UI/ControlPanel/Margin/VBox/BtnReset

# --- State Variables ---
var blade_mesh: Node3D = null
var scabbard_mesh: Node3D = null

var is_drawn: bool = false
var is_auto_rotating: bool = true
var auto_rotate_speed: float = 0.35 # rad/s
var ui_visible: bool = true

# Camera Orbit State
var target_pivot_pos: Vector3 = Vector3(0, 0, -0.15)
var current_pivot_pos: Vector3 = Vector3(0, 0, -0.15)
var yaw: float = deg_to_rad(35.0)
var pitch: float = deg_to_rad(-12.0)
var distance: float = 1.35
var target_distance: float = 1.35

var is_orbiting: bool = false
var is_panning: bool = false
var mouse_sensitivity: float = 0.0035
var pan_sensitivity: float = 0.0012
var zoom_speed: float = 0.12

# Tweens
var blade_tween: Tween = null
var cam_tween: Tween = null

func _ready() -> void:
	# 1. Load Katana GLB via GLTFDocument
	_load_weapon_model()
	
	# 2. Build Showcase Pedestal & Floor Ring
	_create_showcase_stage()
	
	# 3. Setup Camera initial transform
	_update_camera_instant()
	
	# 4. Apply Modern Cyber-Anime UI Theme
	_apply_ui_theme()
	
	# 5. Connect UI Signals
	if btn_draw:
		btn_draw.pressed.connect(_toggle_draw)
	if btn_auto_rotate:
		btn_auto_rotate.pressed.connect(_toggle_auto_rotate)
	if btn_reset:
		btn_reset.pressed.connect(reset_view)
		
	for i in range(1, 6):
		var btn = get_node_or_null("UI/ControlPanel/Margin/VBox/HBoxPresets/BtnPreset%d" % i)
		if btn:
			var idx = i
			btn.pressed.connect(func(): set_preset_view(idx))

func _load_weapon_model() -> void:
	var gltf = GLTFDocument.new()
	var state = GLTFState.new()
	var art_path = ProjectSettings.globalize_path("res://").path_join("../art/models/weapons/aster_katana/aster_katana.glb").simplify_path()
	var load_path = art_path if FileAccess.file_exists(art_path) else "res://models/weapons/aster_katana/aster_katana.glb"
	var err = gltf.append_from_file(load_path, state)
	if err == OK:
		var katana_root = gltf.generate_scene(state)
		weapon_anchor.add_child(katana_root)
		katana_root.name = "KatanaRoot"
		
		# Locate parts
		for child in katana_root.get_children():
			if "Blade" in child.name:
				blade_mesh = child
			elif "Scabbard" in child.name:
				scabbard_mesh = child
				
		print("Katana loaded successfully! Blade:", blade_mesh, " Scabbard:", scabbard_mesh)
	else:
		push_error("Failed to load Katana GLB!")

func _create_showcase_stage() -> void:
	# Subtle circular ground pedestal
	var pedestal = MeshInstance3D.new()
	pedestal.name = "ShowcasePedestal"
	var cyl = CylinderMesh.new()
	cyl.top_radius = 0.75
	cyl.bottom_radius = 0.85
	cyl.height = 0.04
	cyl.radial_segments = 48
	pedestal.mesh = cyl
	pedestal.position = Vector3(0, -0.45, -0.15)
	
	var mat_ped = StandardMaterial3D.new()
	mat_ped.albedo_color = Color(0.08, 0.09, 0.13, 0.9)
	mat_ped.metallic = 0.6
	mat_ped.roughness = 0.35
	mat_ped.rim_enabled = true
	mat_ped.rim = 0.5
	mat_ped.rim_tint = 0.8
	pedestal.material_override = mat_ped
	add_child(pedestal)
	
	# Outer glowing ring
	var ring = MeshInstance3D.new()
	ring.name = "GlowRing"
	var torus = TorusMesh.new()
	torus.inner_radius = 0.76
	torus.outer_radius = 0.78
	torus.rings = 32
	torus.ring_segments = 3
	ring.mesh = torus
	ring.position = Vector3(0, -0.43, -0.15)
	
	var mat_ring = StandardMaterial3D.new()
	mat_ring.albedo_color = Color(0.4, 0.75, 1.0, 1.0)
	mat_ring.emission_enabled = true
	mat_ring.emission = Color(0.3, 0.65, 0.95)
	mat_ring.emission_energy_multiplier = 1.2
	ring.material_override = mat_ring
	add_child(ring)

func _apply_ui_theme() -> void:
	# Panel background style
	var style_panel = StyleBoxFlat.new()
	style_panel.bg_color = Color(0.05, 0.07, 0.12, 0.85)
	style_panel.border_width_left = 1
	style_panel.border_width_top = 1
	style_panel.border_width_right = 1
	style_panel.border_width_bottom = 1
	style_panel.border_color = Color(0.35, 0.55, 0.85, 0.45)
	style_panel.corner_radius_top_left = 8
	style_panel.corner_radius_top_right = 8
	style_panel.corner_radius_bottom_right = 8
	style_panel.corner_radius_bottom_left = 8
	
	info_panel.add_theme_stylebox_override("panel", style_panel)
	control_panel.add_theme_stylebox_override("panel", style_panel)
	help_bar.add_theme_stylebox_override("panel", style_panel)
	
	# Button styles
	var btn_normal = StyleBoxFlat.new()
	btn_normal.bg_color = Color(0.12, 0.16, 0.25, 0.85)
	btn_normal.border_width_left = 1
	btn_normal.border_width_top = 1
	btn_normal.border_width_right = 1
	btn_normal.border_width_bottom = 1
	btn_normal.border_color = Color(0.35, 0.5, 0.75, 0.5)
	btn_normal.corner_radius_top_left = 6
	btn_normal.corner_radius_top_right = 6
	btn_normal.corner_radius_bottom_right = 6
	btn_normal.corner_radius_bottom_left = 6
	
	var btn_hover = btn_normal.duplicate()
	btn_hover.bg_color = Color(0.18, 0.26, 0.40, 0.95)
	btn_hover.border_color = Color(0.5, 0.75, 1.0, 0.8)
	
	var btn_pressed = btn_normal.duplicate()
	btn_pressed.bg_color = Color(0.25, 0.35, 0.55, 1.0)
	btn_pressed.border_color = Color(0.6, 0.85, 1.0, 1.0)
	
	var buttons = [btn_draw, btn_auto_rotate, btn_reset]
	for i in range(1, 6):
		var btn = get_node_or_null("UI/ControlPanel/Margin/VBox/HBoxPresets/BtnPreset%d" % i)
		if btn: buttons.append(btn)
		
	for b in buttons:
		if b:
			b.add_theme_stylebox_override("normal", btn_normal)
			b.add_theme_stylebox_override("hover", btn_hover)
			b.add_theme_stylebox_override("pressed", btn_pressed)

func _process(delta: float) -> void:
	# Auto rotation
	if is_auto_rotating and not is_orbiting and not is_panning:
		yaw += auto_rotate_speed * delta
		if yaw > PI * 2:
			yaw -= PI * 2
			
	# Smooth interpolate camera distance and pivot position
	distance = lerp(distance, target_distance, 12.0 * delta)
	current_pivot_pos = current_pivot_pos.lerp(target_pivot_pos, 10.0 * delta)
	
	_apply_camera_transform()

func _unhandled_input(event: InputEvent) -> void:
	# Mouse Drag Orbit
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			is_orbiting = event.pressed
		elif event.button_index == MOUSE_BUTTON_RIGHT or event.button_index == MOUSE_BUTTON_MIDDLE:
			is_panning = event.pressed
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			target_distance = clamp(target_distance - zoom_speed, 0.22, 3.5)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			target_distance = clamp(target_distance + zoom_speed, 0.22, 3.5)
			
	elif event is InputEventMouseMotion:
		if is_orbiting:
			yaw -= event.relative.x * mouse_sensitivity
			pitch = clamp(pitch - event.relative.y * mouse_sensitivity, deg_to_rad(-82.0), deg_to_rad(82.0))
		elif is_panning:
			var right = camera.global_transform.basis.x
			var up = camera.global_transform.basis.y
			target_pivot_pos -= (right * event.relative.x - up * event.relative.y) * pan_sensitivity * distance
			
	# Keyboard Shortcuts
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE:
				_toggle_draw()
			KEY_R:
				_toggle_auto_rotate()
			KEY_1:
				set_preset_view(1)
			KEY_2:
				set_preset_view(2)
			KEY_3:
				set_preset_view(3)
			KEY_4:
				set_preset_view(4)
			KEY_5:
				set_preset_view(5)
			KEY_C:
				reset_view()
			KEY_TAB:
				# Toggle UI overlay visibility
				ui_visible = not ui_visible
				ui_root.visible = ui_visible
			KEY_ESCAPE:
				get_tree().quit()

func _toggle_draw() -> void:
	if blade_mesh == null:
		return
	is_drawn = not is_drawn
	
	if btn_draw:
		btn_draw.text = "收刀入鞘 (Space)" if is_drawn else "拔刀出鞘 (Space)"
		
	if blade_tween and blade_tween.is_running():
		blade_tween.kill()
		
	blade_tween = create_tween()
	blade_tween.set_parallel(true)
	blade_tween.set_trans(Tween.TRANS_CUBIC)
	blade_tween.set_ease(Tween.EASE_OUT)
	
	if is_drawn:
		# Draw out blade: slide along +Z by 0.74m and slightly offset +X for parallel showcase display
		blade_tween.tween_property(blade_mesh, "position", Vector3(0.06, 0.02, 0.74), 0.75)
		blade_tween.tween_property(blade_mesh, "rotation_degrees", Vector3(2.0, 5.0, 0.0), 0.75)
	else:
		# Return to sheathed state at (0, 0, 0)
		blade_tween.tween_property(blade_mesh, "position", Vector3.ZERO, 0.65)
		blade_tween.tween_property(blade_mesh, "rotation_degrees", Vector3.ZERO, 0.65)

func _toggle_auto_rotate() -> void:
	is_auto_rotating = not is_auto_rotating
	if btn_auto_rotate:
		btn_auto_rotate.text = "自动旋转: ON" if is_auto_rotating else "自动旋转: OFF"

func set_preset_view(index: int) -> void:
	var target_y = yaw
	var target_p = pitch
	var target_d = target_distance
	var target_pivot = target_pivot_pos
	
	match index:
		1: # Full Overview
			target_pivot = Vector3(0, 0, -0.15)
			target_d = 1.35
			target_y = deg_to_rad(35.0)
			target_p = deg_to_rad(-12.0)
		2: # Tsuba (Four-Point Star Guard)
			target_pivot = Vector3(0, 0, 0.0)
			target_d = 0.36
			target_y = deg_to_rad(45.0)
			target_p = deg_to_rad(-18.0)
		3: # Kissaki (Blade Tip & Hamon)
			if is_drawn:
				target_pivot = Vector3(0.06, 0.02, 0.05)
			else:
				target_pivot = Vector3(0, 0, -0.68)
			target_d = 0.36
			target_y = deg_to_rad(75.0)
			target_p = deg_to_rad(6.0)
		4: # Tsuka & Charm (Hilt & Pendant)
			if is_drawn:
				target_pivot = Vector3(0.06, 0.02, 0.96)
			else:
				target_pivot = Vector3(0, 0, 0.22)
			target_d = 0.38
			target_y = deg_to_rad(120.0)
			target_p = deg_to_rad(-10.0)
		5: # Sageo (Light Blue Ribbon Bow on Scabbard)
			target_pivot = Vector3(0, 0, -0.08)
			target_d = 0.36
			target_y = deg_to_rad(15.0)
			target_p = deg_to_rad(-15.0)
			
	if cam_tween and cam_tween.is_running():
		cam_tween.kill()
		
	cam_tween = create_tween()
	cam_tween.set_parallel(true)
	cam_tween.set_trans(Tween.TRANS_QUAD)
	cam_tween.set_ease(Tween.EASE_OUT)
	cam_tween.tween_property(self, "target_pivot_pos", target_pivot, 0.6)
	cam_tween.tween_property(self, "target_distance", target_d, 0.6)
	cam_tween.tween_property(self, "yaw", target_y, 0.6)
	cam_tween.tween_property(self, "pitch", target_p, 0.6)

func reset_view() -> void:
	set_preset_view(1)

func _update_camera_instant() -> void:
	current_pivot_pos = target_pivot_pos
	distance = target_distance
	_apply_camera_transform()

func _apply_camera_transform() -> void:
	camera_pivot.position = current_pivot_pos
	camera_pivot.rotation.y = yaw
	camera_pivot.rotation.x = pitch
	camera.position = Vector3(0, 0, distance)
