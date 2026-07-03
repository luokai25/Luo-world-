extends CanvasLayer

# Touch joystick state
var joy_move: Vector2        = Vector2.ZERO
var joy_cam:  Vector2        = Vector2.ZERO
var _joy_move_center: Vector2
var _joy_cam_center:  Vector2
var _joy_move_id: int        = -1
var _joy_cam_id:  int        = -1
const JOY_R: float           = 110.0
var _joy_draw: Control

const ICON_ATTACK    = preload("res://assets/icons/attack.png")
const ICON_INTERACT  = preload("res://assets/icons/interact.png")
const ICON_USE       = preload("res://assets/icons/use.png")
const ICON_JUMP      = preload("res://assets/icons/jump.png")
const ICON_INVENTORY = preload("res://assets/icons/inventory.png")

onready var health_bar   = $Bottom/Stats/HealthBar
onready var hunger_bar   = $Bottom/Stats/HungerBar
onready var thirst_bar   = $Bottom/Stats/ThirstBar
onready var stamina_bar  = $Bottom/Stats/StaminaBar
onready var notif_label  = $Top/Notif
onready var prompt_label = $Center/Prompt
onready var time_label   = $Top/Time

func _ready():
	var vp = get_viewport().size
	_joy_move_center = Vector2(140, vp.y - 140)
	_joy_cam_center  = Vector2(vp.x - 140, vp.y - 140)

	GameState.connect("inventory_changed", self, "_refresh_hotbar")
	_refresh_hotbar()
	_setup_action_icons()

	_joy_draw = Control.new()
	_joy_draw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_joy_draw.set_anchors_and_margins_preset(Control.PRESET_WIDE)
	_joy_draw.connect("draw", self, "_draw_joysticks")
	add_child(_joy_draw)

func _setup_action_icons():
	_set_button_icon("Bottom/Actions/AttackBtn",    ICON_ATTACK)
	_set_button_icon("Bottom/Actions/InteractBtn",  ICON_INTERACT)
	_set_button_icon("Bottom/Actions/UseBtn",       ICON_USE)
	_set_button_icon("Bottom/Actions/JumpBtn",      ICON_JUMP)
	_set_button_icon("Bottom/Actions/InventoryBtn", ICON_INVENTORY)

func _set_button_icon(path: String, tex: Texture):
	var btn = get_node_or_null(path)
	if btn:
		btn.text = ""
		btn.icon = tex

func _process(_delta):
	notif_label.text = GameState.get_current_notification()
	time_label.text  = GameState.get_time_str()
	if health_bar:
		health_bar.value  = GameState.health  / GameState.max_health  * 100.0
		hunger_bar.value  = GameState.hunger  / GameState.max_hunger  * 100.0
		thirst_bar.value  = GameState.thirst  / GameState.max_thirst  * 100.0
		stamina_bar.value = GameState.stamina / GameState.max_stamina * 100.0

func _refresh_hotbar():
	for i in range(8):
		var icon_node  = get_node_or_null("Bottom/Hotbar/Slot%d/Icon"  % i)
		var count_node = get_node_or_null("Bottom/Hotbar/Slot%d/Count" % i)
		if icon_node == null: continue
		var slot = GameState.slots[i]
		if slot.item_id != "":
			icon_node.texture = load(Items.get_icon_path(slot.item_id))
			if count_node:
				count_node.text = str(slot.count) if slot.count > 1 else ""
		else:
			icon_node.texture = null
			if count_node:
				count_node.text = ""

func set_prompt(text: String):
	if prompt_label: prompt_label.text = text

# ── TOUCH ─────────────────────────────────────
func _input(event):
	if event is InputEventScreenTouch:
		_on_touch(event)
	elif event is InputEventScreenDrag:
		_on_drag(event)

func _on_touch(event: InputEventScreenTouch):
	var pos = event.position
	var vp  = get_viewport().size
	if event.pressed:
		if pos.x < vp.x * 0.38:
			_joy_move_id     = event.index
			_joy_move_center = pos
			joy_move         = Vector2.ZERO
		elif pos.x > vp.x * 0.62:
			_joy_cam_id      = event.index
			_joy_cam_center  = pos
			joy_cam          = Vector2.ZERO
	else:
		if event.index == _joy_move_id: _joy_move_id = -1; joy_move = Vector2.ZERO
		if event.index == _joy_cam_id:  _joy_cam_id  = -1; joy_cam  = Vector2.ZERO
	if _joy_draw: _joy_draw.update()

func _on_drag(event: InputEventScreenDrag):
	if event.index == _joy_move_id:
		var d = event.position - _joy_move_center
		if d.length() > JOY_R: d = d.normalized() * JOY_R
		joy_move = d / JOY_R
	if event.index == _joy_cam_id:
		var d = event.position - _joy_cam_center
		if d.length() > JOY_R: d = d.normalized() * JOY_R
		joy_cam  = d / JOY_R
	if _joy_draw: _joy_draw.update()

func _draw_joysticks():
	if _joy_move_id >= 0:
		_joy_draw.draw_circle(_joy_move_center, JOY_R, Color(1,1,1,0.12))
		_joy_draw.draw_circle(_joy_move_center + joy_move * JOY_R, 36, Color(1,1,1,0.40))
	if _joy_cam_id >= 0:
		_joy_draw.draw_circle(_joy_cam_center,  JOY_R, Color(1,1,1,0.12))
		_joy_draw.draw_circle(_joy_cam_center  + joy_cam  * JOY_R, 36, Color(1,1,1,0.40))
