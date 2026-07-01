extends Spatial
# Main scene - wires everything together

onready var world:  Spatial     = $World
onready var player: KinematicBody = $Player
onready var hud:    CanvasLayer = $HUD

var _nearest: Dictionary = {}

func _ready():
	# Connect player signals
	player.connect("attack_pressed", self, "_on_attack")

func _process(delta):
	# Push joystick input to player
	player.joy_move = hud.joy_move
	player.joy_cam  = hud.joy_cam
	player._update_camera(delta)

	# Interaction scan
	_nearest = world.nearest_object(player.global_transform.origin, player.reach)
	hud.set_prompt(_get_prompt())

	# Day/night sun rotation
	var sun = $World/Sun if $World.has_node("Sun") else null

func _get_prompt() -> String:
	if _nearest.empty():
		return ""
	var t = _nearest.get("type", "")
	match t:
		"tree":         return "[E] Chop Tree   [LMB] Attack"
		"rock":         return "[E] Mine Rock   [LMB] Attack"
		"water_source": return "[E] Fill cup with water"
		"item":
			var name = Items.get_item(_nearest.get("item_id","")).get("name","item")
			return "[E] Pick up " + name
		"animal":
			var atype = _nearest.get("animal_type","animal").capitalize()
			return "[LMB] Hunt " + atype + "  HP:" + str(_nearest.get("health","?"))
		"campfire":
			return "[E] Campfire  [C] Cook"
	return ""

func _input(event):
	# Keyboard interact
	if event is InputEventKey and event.pressed:
		match event.scancode:
			KEY_E:
				_on_interact()
			KEY_F:
				GameState.use_equipped()
			KEY_TAB:
				GameState.inventory_open = !GameState.inventory_open
			KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
				GameState.equipped_slot = event.scancode - KEY_1
			KEY_SPACE:
				player.jump()

	# Mouse click = attack
	if event is InputEventMouseButton and event.pressed and event.button_index == BUTTON_LEFT:
		_on_attack()

func _on_attack():
	if _nearest.empty():
		return

	var equipped = GameState.get_equipped()
	var damage   = 5
	if equipped.item_id != "":
		damage = Items.get_item(equipped.item_id).get("damage", 5)

	_nearest["health"] = _nearest.get("health", 3) - damage

	if _nearest["health"] <= 0:
		var drops = world.destroy_object(_nearest)
		for drop in drops:
			GameState.add_item(drop[0], drop[1])
			var name = Items.get_item(drop[0]).get("name", drop[0])
			GameState.notify("Got %dx %s" % [drop[1], name])
		_nearest = {}

	# Durability loss
	if equipped.item_id != "":
		var slot = GameState.slots[GameState.equipped_slot]
		if slot.durability > 0:
			slot.durability -= 1
			if slot.durability <= 0:
				var name = Items.get_item(slot.item_id).get("name","")
				GameState.remove_item(slot.item_id, 1)
				GameState.notify("⚠️ %s broke!" % name)

func _on_interact():
	if _nearest.empty():
		return
	var t = _nearest.get("type","")

	match t:
		"item":
			var iid   = _nearest.get("item_id","")
			var count = _nearest.get("count", 1)
			GameState.add_item(iid, count)
			var name = Items.get_item(iid).get("name", iid)
			GameState.notify("Picked up %dx %s" % [count, name])
			world.remove_object(_nearest)
			_nearest = {}

		"water_source":
			if GameState.count_item("wooden_cup_empty") > 0:
				GameState.remove_item("wooden_cup_empty", 1)
				GameState.add_item("wooden_cup", 1)
				GameState.notify("💧 Filled wooden cup")
			else:
				GameState.notify("Need an empty wooden cup")

		"tree":
			_on_attack()

		"rock":
			_on_attack()

		"campfire":
			GameState.notify("🔥 Campfire — press C to cook")
