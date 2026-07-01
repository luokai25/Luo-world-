extends CanvasLayer
# HUD - stat bars, hotbar, crosshair, touch controls, notifications

onready var health_bar  = $StatBars/HealthBar
onready var hunger_bar  = $StatBars/HungerBar
onready var thirst_bar  = $StatBars/ThirstBar
onready var stamina_bar = $StatBars/StaminaBar
onready var notif_label = $NotifLabel
onready var prompt_label= $PromptLabel
onready var time_label  = $TimeLabel
onready var weather_label = $WeatherLabel

# Touch joystick state
var joy_move: Vector2 = Vector2.ZERO
var joy_cam:  Vector2 = Vector2.ZERO
var joy_move_center: Vector2
var joy_cam_center:  Vector2
var joy_move_touch:  int = -1
var joy_cam_touch:   int = -1
const JOY_RADIUS: float = 120.0

func _ready():
	GameState.connect("stats_changed", self, "_update_bars")
	GameState.connect("inventory_changed", self, "_update_hotbar")
	var vp = get_viewport().size
	joy_move_center = Vector2(150, vp.y - 150)
	joy_cam_center  = Vector2(vp.x - 150, vp.y - 150)
	_update_hotbar()

func _update_bars():
	health_bar.value  = GameState.health  / GameState.max_health  * 100.0
	hunger_bar.value  = GameState.hunger  / GameState.max_hunger  * 100.0
	thirst_bar.value  = GameState.thirst  / GameState.max_thirst  * 100.0
	stamina_bar.value = GameState.stamina / GameState.max_stamina * 100.0
	notif_label.text  = GameState.get_current_notification()
	time_label.text   = GameState.get_time_str()

func _update_hotbar():
	for i in range(8):
		var slot_node = get_node_or_null("Hotbar/Slot%d" % i)
		if slot_node == null:
			continue
		var slot = GameState.slots[i]
		var icon_node = slot_node.get_node_or_null("Icon")
		if icon_node == null:
			continue
		if slot.item_id != "":
			var data = Items.get_item(slot.item_id)
			icon_node.text = data.get("icon", "?")
			if slot.count > 1:
				icon_node.text += "\n" + str(slot.count)
		else:
			icon_node.text = ""

func set_prompt(text: String):
	prompt_label.text = text

func set_weather(text: String):
	weather_label.text = text

# ── TOUCH INPUT ───────────────────────────────
func _input(event):
	if event is InputEventScreenTouch:
		_handle_touch(event)
	elif event is InputEventScreenDrag:
		_handle_drag(event)

func _handle_touch(event: InputEventScreenTouch):
	var pos = event.position
	if event.pressed:
		# Left zone = move joystick
		if pos.x < get_viewport().size.x * 0.4:
			joy_move_touch  = event.index
			joy_move_center = pos
			joy_move        = Vector2.ZERO
		# Right zone = camera joystick
		elif pos.x > get_viewport().size.x * 0.6:
			joy_cam_touch   = event.index
			joy_cam_center  = pos
			joy_cam         = Vector2.ZERO
	else:
		if event.index == joy_move_touch:
			joy_move_touch = -1
			joy_move = Vector2.ZERO
		if event.index == joy_cam_touch:
			joy_cam_touch = -1
			joy_cam = Vector2.ZERO

func _handle_drag(event: InputEventScreenDrag):
	if event.index == joy_move_touch:
		var delta = event.position - joy_move_center
		if delta.length() > JOY_RADIUS:
			delta = delta.normalized() * JOY_RADIUS
		joy_move = delta / JOY_RADIUS
	if event.index == joy_cam_touch:
		var delta = event.position - joy_cam_center
		if delta.length() > JOY_RADIUS:
			delta = delta.normalized() * JOY_RADIUS
		joy_cam = delta / JOY_RADIUS

func _draw():
	# Draw joystick circles
	if joy_move_touch >= 0:
		draw_circle(joy_move_center, JOY_RADIUS, Color(1, 1, 1, 0.15))
		draw_circle(joy_move_center + joy_move * JOY_RADIUS, 40, Color(1, 1, 1, 0.4))
	if joy_cam_touch >= 0:
		draw_circle(joy_cam_center, JOY_RADIUS, Color(1, 1, 1, 0.15))
		draw_circle(joy_cam_center + joy_cam * JOY_RADIUS, 40, Color(1, 1, 1, 0.4))
