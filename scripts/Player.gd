extends KinematicBody
# 3rd person player - works with keyboard (desktop) and touch joystick (Android)

export var move_speed: float   = 5.0
export var run_speed: float    = 9.0
export var jump_velocity: float = 7.0
export var gravity: float      = -20.0
export var mouse_sensitivity: float = 0.003
export var cam_distance: float = 4.5
export var cam_height: float   = 2.0
export var reach: float        = 3.0

var velocity: Vector3 = Vector3.ZERO
var cam_yaw: float    = 0.0
var cam_pitch: float  = -0.25
var is_grounded: bool = false

# Touch joystick input (set by HUD)
var joy_move: Vector2 = Vector2.ZERO
var joy_cam: Vector2  = Vector2.ZERO

onready var camera_pivot = $CameraPivot
onready var camera       = $CameraPivot/Camera
onready var body_mesh    = $BodyMesh
onready var head_mesh    = $HeadMesh
onready var anim_timer: float = 0.0

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	camera.translation = Vector3(0, cam_height, cam_distance)
	camera.look_at(global_transform.origin + Vector3.UP * 0.5, Vector3.UP)

func _process(delta):
	anim_timer += delta
	_animate(delta)

func _physics_process(delta):
	var on_floor = is_on_floor()

	# Gravity
	if not on_floor:
		velocity.y += gravity * delta
	else:
		if velocity.y < 0:
			velocity.y = 0.0
		is_grounded = true

	# Movement direction from keyboard OR touch joystick
	var input_dir = Vector2.ZERO
	if joy_move.length() > 0.1:
		input_dir = joy_move
	else:
		input_dir.x = Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left")
		input_dir.y = Input.get_action_strength("ui_down")  - Input.get_action_strength("ui_up")

	var running = input_dir.length() > 0.8 and (Input.is_action_pressed("ui_accept") or input_dir.length() > 0.9)
	var speed   = run_speed if running else move_speed

	if input_dir.length() > 0.1:
		var fwd   = Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var right = Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		var dir   = (fwd * (-input_dir.y) + right * input_dir.x).normalized()
		velocity.x = dir.x * speed
		velocity.z = dir.z * speed
		# Rotate body toward movement
		var target_angle = atan2(dir.x, dir.z)
		rotation.y = lerp_angle(rotation.y, target_angle, 10.0 * delta)
	else:
		velocity.x = lerp(velocity.x, 0.0, 10.0 * delta)
		velocity.z = lerp(velocity.z, 0.0, 10.0 * delta)

	# Stamina
	if running and input_dir.length() > 0.1:
		GameState.stamina = max(0.0, GameState.stamina - 15.0 * delta)
	else:
		GameState.stamina = min(GameState.max_stamina, GameState.stamina + 8.0 * delta)

	velocity = move_and_slide(velocity, Vector3.UP)
	is_grounded = is_on_floor()

func _update_camera(delta):
	# Camera from joystick or mouse
	if joy_cam.length() > 0.05:
		cam_yaw   -= joy_cam.x * 2.5 * delta
		cam_pitch -= joy_cam.y * 1.5 * delta
	cam_pitch = clamp(cam_pitch, -0.7, 0.9)

	# Orbit camera
	var offset = Vector3(
		-sin(cam_yaw) * cos(cam_pitch) * cam_distance,
		 sin(cam_pitch) * cam_distance + cam_height,
		-cos(cam_yaw) * cos(cam_pitch) * cam_distance
	)
	var target_pos = global_transform.origin + offset
	camera_pivot.global_transform.origin = lerp(
		camera_pivot.global_transform.origin,
		target_pos, 12.0 * delta)
	camera_pivot.look_at(global_transform.origin + Vector3.UP * 0.5, Vector3.UP)

func _input(event):
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		cam_yaw   -= event.relative.x * mouse_sensitivity
		cam_pitch -= event.relative.y * mouse_sensitivity
	if event is InputEventKey and event.scancode == KEY_SPACE and event.pressed and is_grounded:
		velocity.y = jump_velocity
	if event is InputEventKey and event.scancode == KEY_ESCAPE and event.pressed:
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func jump():
	if is_grounded:
		velocity.y = jump_velocity

func attack():
	# Signal to world to damage nearest object
	emit_signal("attack_pressed")

func _animate(delta):
	var moving = velocity.length() > 0.5
	if moving:
		var freq  = 8.0 if GameState.stamina > 20.0 else 5.0
		var swing = sin(anim_timer * freq) * 0.4
		if has_node("ArmL"):
			$ArmL.rotation.x = -swing
		if has_node("ArmR"):
			$ArmR.rotation.x = swing
		if has_node("LegL"):
			$LegL.rotation.x = swing
		if has_node("LegR"):
			$LegR.rotation.x = -swing

signal attack_pressed
