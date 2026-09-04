extends Node3D

@export var target_node: Node3D
@export var target_offset: Vector3 = Vector3(0, 1.15, 0)
@export var min_distance: float = 1.0
@export var max_distance: float = 6.0
@export var default_distance: float = 2.6
@export var zoom_speed: float = 0.4
@export var rotate_speed: float = 0.005

@onready var camera: Camera3D = $Camera3D

var _current_distance: float = 2.6
var _yaw: float = 0.0
var _pitch: float = -0.1
var _is_dragging: bool = false

func _ready() -> void:
	_current_distance = default_distance
	_update_camera_transform()

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT or event.button_index == MOUSE_BUTTON_RIGHT:
			_is_dragging = event.pressed
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_current_distance = clamp(_current_distance - zoom_speed, min_distance, max_distance)
			_update_camera_transform()
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_current_distance = clamp(_current_distance + zoom_speed, min_distance, max_distance)
			_update_camera_transform()

	elif event is InputEventMouseMotion and _is_dragging:
		_yaw -= event.relative.x * rotate_speed
		_pitch = clamp(_pitch - event.relative.y * rotate_speed, -1.2, 0.8)
		_update_camera_transform()

func _process(_delta: float) -> void:
	if target_node:
		global_position = target_node.global_position + target_offset
	_update_camera_transform()

func _update_camera_transform() -> void:
	rotation.y = _yaw
	rotation.x = _pitch
	if camera:
		camera.position = Vector3(0, 0, _current_distance)
