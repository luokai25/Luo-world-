extends KinematicBody
# 3rd person player - safe, no crash on missing nodes

export var move_speed: float    = 5.0
export var run_speed: float     = 9.0
export var jump_velocity: float = 7.0
export var gravity: float       = -22.0
export var mouse_sens: float    = 0.003
export var cam_dist: float      = 4.5
export var cam_height: float    = 2.2
export var reach: float         = 3.0

var velocity: Vector3   = Vector3.ZERO
var cam_yaw: float      = 0.0
var cam_pitch: float    = -0.3
var is_grounded: bool   = false

# Set by HUD touch joysticks
var joy_move: Vector2   = Vector2.ZERO
var joy_cam: Vector2    = Vector2.ZERO

onready var cam_pivot = $CameraPivot
onready var camera    = $CameraPivot/Camera

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _physics_process(delta):
	var on_floor = is_on_floor()

	# Gravity
	if not on_floor:
		velocity.y += gravity * delta
	else:
		if velocity.y < 0:
			velocity.y = 0.0

	# Input direction - touch OR keyboard
	var dir = Vector2.ZERO
	if joy_move.length() > 0.1:
		dir = joy_move
	else:
		dir.x = Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left")
		dir.y = Input.get_action_strength("ui_down")  - Input.get_action_strength("ui_up")

	var speed = run_speed if dir.length() > 0.85 else move_speed
	if dir.length() > 0.1:
		var fwd   = Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var right = Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		var move  = (fwd * (-dir.y) + right * dir.x).normalized()
		velocity.x = move.x * speed
		velocity.z = move.z * speed
		var target_angle = atan2(move.x, move.z)
		rotation.y = lerp_angle(rotation.y, target_angle, 12.0 * delta)
		# Stamina drain when running
		if speed == run_speed:
			GameState.stamina = max(0.0, GameState.stamina - 15.0 * delta)
	else:
		velocity.x = lerp(velocity.x, 0.0, 12.0 * delta)
		velocity.z = lerp(velocity.z, 0.0, 12.0 * delta)
		GameState.stamina = min(GameState.max_stamina, GameState.stamina + 8.0 * delta)

	velocity = move_and_slide(velocity, Vector3.UP)

func update_camera(delta: float):
	# Camera from touch joystick or mouse
	if joy_cam.length() > 0.05:
		cam_yaw   -= joy_cam.x * 2.0 * delta
		cam_pitch -= joy_cam.y * 1.5 * delta
	cam_pitch = clamp(cam_pitch, -0.65, 0.8)

	var offset = Vector3(
		-sin(cam_yaw) * cos(cam_pitch) * cam_dist,
		 sin(cam_pitch) * cam_dist + cam_height,
		-cos(cam_yaw) * cos(cam_pitch) * cam_dist
	)
	var target = global_transform.origin + offset
	cam_pivot.global_transform.origin = lerp(cam_pivot.global_transform.origin, target, 12.0 * delta)
	cam_pivot.look_at(global_transform.origin + Vector3.UP * 0.8, Vector3.UP)

func _input(event):
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		cam_yaw   -= event.relative.x * mouse_sens
		cam_pitch -= event.relative.y * mouse_sens
	if event is InputEventKey and event.pressed:
		if event.scancode == KEY_SPACE and is_on_floor():
			jump()
		if event.scancode == KEY_ESCAPE:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func jump():
	if is_on_floor():
		velocity.y = jump_velocity

signal attack_pressed()
