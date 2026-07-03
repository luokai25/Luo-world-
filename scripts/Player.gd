extends KinematicBody
# 3rd person player - procedural humanoid rig, walk/run/attack/idle animation

export var move_speed: float    = 5.0
export var run_speed: float     = 9.0
export var jump_velocity: float = 7.0
export var gravity: float       = -22.0
export var mouse_sens: float    = 0.003
export var cam_dist: float      = 4.8
export var cam_height: float    = 2.2
export var reach: float         = 3.0

var velocity: Vector3   = Vector3.ZERO
var cam_yaw: float      = 0.0
var cam_pitch: float    = -0.3
var is_grounded: bool   = false

var joy_move: Vector2   = Vector2.ZERO
var joy_cam: Vector2    = Vector2.ZERO

onready var cam_pivot  = $CameraPivot
onready var camera     = $CameraPivot/Camera

onready var torso      = $Rig/Torso
onready var head       = $Rig/Head
onready var arm_l      = $Rig/ArmL
onready var arm_r      = $Rig/ArmR
onready var leg_l      = $Rig/LegL
onready var leg_r      = $Rig/LegR
onready var hand_point = $Rig/ArmR/HandPoint

var _anim_t: float        = 0.0
var _attack_timer: float  = 0.0
const ATTACK_DURATION     = 0.35
var _base_torso_y: float  = 0.0

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	_equip_held_item()
	if torso:
		_base_torso_y = torso.translation.y

func _equip_held_item():
	if hand_point == null:
		return
	var axe_scene = load("res://assets/models/stone_axe.glb")
	if axe_scene:
		var axe = axe_scene.instance()
		axe.rotation_degrees = Vector3(0, 0, 160)
		axe.translation = Vector3(0, -0.06, 0.02)
		hand_point.add_child(axe)

func _physics_process(delta):
	var on_floor = is_on_floor()

	if not on_floor:
		velocity.y += gravity * delta
	else:
		if velocity.y < 0:
			velocity.y = 0.0

	var dir = Vector2.ZERO
	if joy_move.length() > 0.1:
		dir = joy_move
	else:
		dir.x = Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left")
		dir.y = Input.get_action_strength("ui_down")  - Input.get_action_strength("ui_up")

	var running = dir.length() > 0.85
	var speed = run_speed if running else move_speed

	if dir.length() > 0.1:
		var fwd   = Vector3(sin(cam_yaw), 0, cos(cam_yaw))
		var right = Vector3(cos(cam_yaw), 0, -sin(cam_yaw))
		var move  = (fwd * (-dir.y) + right * dir.x).normalized()
		velocity.x = move.x * speed
		velocity.z = move.z * speed
		var target_angle = atan2(move.x, move.z)
		rotation.y = lerp_angle(rotation.y, target_angle, 12.0 * delta)
		if running:
			GameState.stamina = max(0.0, GameState.stamina - 15.0 * delta)
	else:
		velocity.x = lerp(velocity.x, 0.0, 12.0 * delta)
		velocity.z = lerp(velocity.z, 0.0, 12.0 * delta)
		GameState.stamina = min(GameState.max_stamina, GameState.stamina + 8.0 * delta)

	velocity = move_and_slide(velocity, Vector3.UP)

func _process(delta):
	_animate(delta)

func _animate(delta):
	var horiz_speed = Vector2(velocity.x, velocity.z).length()
	var moving = horiz_speed > 0.4

	# Attack swing takes priority over the right arm
	if _attack_timer > 0.0:
		_attack_timer -= delta
		var t = 1.0 - clamp(_attack_timer / ATTACK_DURATION, 0.0, 1.0)
		var swing = sin(t * PI)
		if arm_r:
			arm_r.rotation.x = -1.7 * swing
			arm_r.rotation.z = 0.3 * swing
	elif arm_r:
		arm_r.rotation.z = lerp(arm_r.rotation.z, 0.0, 10.0 * delta)

	if moving:
		var freq = 9.5 if horiz_speed > move_speed + 0.5 else 6.5
		_anim_t += delta * freq
		var swing = sin(_anim_t) * 0.55
		if leg_l: leg_l.rotation.x = swing
		if leg_r: leg_r.rotation.x = -swing
		if arm_l: arm_l.rotation.x = -swing * 0.75
		if _attack_timer <= 0.0 and arm_r:
			arm_r.rotation.x = swing * 0.75
		if torso:
			torso.rotation.z = sin(_anim_t * 2.0) * 0.025
			torso.translation.y = _base_torso_y
		if head:
			head.rotation.z = sin(_anim_t * 2.0) * -0.02
	else:
		_anim_t += delta * 1.4
		var breathe = sin(_anim_t)
		if torso:
			torso.translation.y = _base_torso_y + breathe * 0.012
			torso.rotation.z = lerp(torso.rotation.z, 0.0, 6.0 * delta)
		if head:
			head.rotation.z = lerp(head.rotation.z, 0.0, 6.0 * delta)
		if leg_l: leg_l.rotation.x = lerp(leg_l.rotation.x, 0.0, 8.0 * delta)
		if leg_r: leg_r.rotation.x = lerp(leg_r.rotation.x, 0.0, 8.0 * delta)
		if arm_l: arm_l.rotation.x = lerp(arm_l.rotation.x, 0.0, 8.0 * delta)
		if _attack_timer <= 0.0 and arm_r:
			arm_r.rotation.x = lerp(arm_r.rotation.x, 0.0, 8.0 * delta)

func play_attack_swing():
	_attack_timer = ATTACK_DURATION

func update_camera(delta: float):
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
	cam_pivot.look_at(global_transform.origin + Vector3.UP * 0.9, Vector3.UP)

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
