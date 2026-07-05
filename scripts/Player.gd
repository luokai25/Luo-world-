extends KinematicBody
# 3rd person player - real rigged/skinned/animated human (CesiumMan glTF sample,
# Khronos Group, CC-BY 4.0) replacing the old primitive-box rig.

export var move_speed: float    = 5.0
export var run_speed: float     = 9.0
export var jump_velocity: float = 7.0
export var gravity: float       = -22.0
export var mouse_sens: float    = 0.003
export var cam_dist: float      = 4.8
export var cam_height: float    = 2.2
export var reach: float         = 3.0

# Character is ~1.51m tall natively; scale to a believable adult height
const CHAR_SCALE = 1.16
const CHAR_Y_OFFSET = -0.85   # aligns modeled feet (local y=0) with collision bottom

var velocity: Vector3   = Vector3.ZERO
var cam_yaw: float      = 0.0
var cam_pitch: float    = -0.3
var is_grounded: bool   = false

var joy_move: Vector2   = Vector2.ZERO
var joy_cam: Vector2    = Vector2.ZERO

onready var cam_pivot = $CameraPivot
onready var camera    = $CameraPivot/Camera

var char_root: Spatial
var skeleton: Skeleton
var anim_player: AnimationPlayer
var bone_attach: BoneAttachment

const ARM_SHOULDER = 11
const ARM_ELBOW     = 12
const ARM_WRIST     = 13
const HAND_BONE_NAME = "Skeleton_arm_joint_R__3_"

var _attack_timer: float = 0.0
const ATTACK_DURATION    = 0.4
var _current_playback_speed: float = 0.0

func _ready():
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	_load_character()
	_equip_held_item()

func _load_character():
	var scene = load("res://assets/models/character/CesiumMan.glb")
	if scene == null:
		return
	char_root = scene.instance()
	char_root.scale = Vector3(CHAR_SCALE, CHAR_SCALE, CHAR_SCALE)
	char_root.translation = Vector3(0, CHAR_Y_OFFSET, 0)
	add_child(char_root)

	skeleton    = _find_node_of_type(char_root, "Skeleton")
	anim_player = _find_node_of_type(char_root, "AnimationPlayer")

	if anim_player:
		anim_player.play("Animation")
		anim_player.playback_speed = 0.0

	if skeleton:
		bone_attach = BoneAttachment.new()
		bone_attach.bone_name = HAND_BONE_NAME
		skeleton.add_child(bone_attach)

func _equip_held_item():
	if bone_attach == null:
		return
	var axe_scene = load("res://assets/models/stone_axe.glb")
	if axe_scene:
		var axe = axe_scene.instance()
		axe.scale = Vector3(1, 1, 1) / CHAR_SCALE   # counter parent scale, keep true size
		axe.rotation_degrees = Vector3(90, 0, 100)
		axe.translation = Vector3(0.02, -0.02, 0.05)
		bone_attach.add_child(axe)

func _find_node_of_type(node, class_name_str: String):
	if node.get_class() == class_name_str:
		return node
	for c in node.get_children():
		var r = _find_node_of_type(c, class_name_str)
		if r:
			return r
	return null

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
	if anim_player == null:
		return

	if _attack_timer > 0.0:
		_attack_timer -= delta
		_apply_attack_pose(delta)
		if _attack_timer <= 0.0:
			anim_player.play("Animation")   # resumes from retained position
		return

	var horiz_speed = Vector2(velocity.x, velocity.z).length()
	var target_speed = 0.0
	if horiz_speed > 0.4:
		var ratio = horiz_speed / move_speed
		target_speed = clamp(ratio * 0.9, 0.6, 1.8)
	_current_playback_speed = lerp(_current_playback_speed, target_speed, 6.0 * delta)
	anim_player.playback_speed = _current_playback_speed

func _apply_attack_pose(delta):
	if skeleton == null:
		return
	if anim_player.playback_speed != 0.0:
		anim_player.stop(false)   # freeze locomotion, keep last pose, take manual control
		anim_player.playback_speed = 0.0

	var t = 1.0 - clamp(_attack_timer / ATTACK_DURATION, 0.0, 1.0)
	var swing = sin(t * PI)

	var shoulder_rest = skeleton.get_bone_rest(ARM_SHOULDER)
	var elbow_rest    = skeleton.get_bone_rest(ARM_ELBOW)

	var shoulder_swing = Basis(Vector3(1, 0, 0), -2.0 * swing)
	var elbow_swing     = Basis(Vector3(1, 0, 0), -0.8 * swing)

	skeleton.set_bone_pose(ARM_SHOULDER, Transform(shoulder_rest.basis * shoulder_swing, shoulder_rest.origin))
	skeleton.set_bone_pose(ARM_ELBOW,     Transform(elbow_rest.basis * elbow_swing, elbow_rest.origin))

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
