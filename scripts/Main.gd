extends Spatial

onready var world  = $World
onready var player = $Player
onready var hud    = $HUD

var _nearest: Dictionary = {}
var _nearest_plot: Dictionary = {}

func _ready():
	if hud.has_node("Bottom/Actions/AttackBtn"):
		hud.get_node("Bottom/Actions/AttackBtn").connect("pressed", self, "_on_attack")
	if hud.has_node("Bottom/Actions/InteractBtn"):
		hud.get_node("Bottom/Actions/InteractBtn").connect("pressed", self, "_on_interact")
	if hud.has_node("Bottom/Actions/UseBtn"):
		hud.get_node("Bottom/Actions/UseBtn").connect("pressed", self, "_on_use")
	if hud.has_node("Bottom/Actions/JumpBtn"):
		hud.get_node("Bottom/Actions/JumpBtn").connect("pressed", player, "jump")
	if hud.has_node("Bottom/Actions/InventoryBtn"):
		hud.get_node("Bottom/Actions/InventoryBtn").connect("pressed", self, "_on_inventory")

func _notification(what):
	if what == MainLoop.NOTIFICATION_WM_GO_BACK_REQUEST \
	or what == MainLoop.NOTIFICATION_APP_PAUSED \
	or what == MainLoop.NOTIFICATION_WM_QUIT_REQUEST:
		SaveManager.save_game()

func _on_inventory():
	GameState.inventory_open = !GameState.inventory_open

func _process(delta):
	player.joy_move = hud.joy_move
	player.joy_cam  = hud.joy_cam
	player.update_camera(delta)
	world.player_pos = player.global_transform.origin

	_nearest = world.nearest_object(player.global_transform.origin, player.reach)
	_nearest_plot = Farming.nearest_plot(player.global_transform.origin, 3.0)

	if not _nearest_plot.empty():
		hud.set_prompt(Farming.get_prompt(_nearest_plot))
	else:
		hud.set_prompt(_get_prompt())

func _get_prompt() -> String:
	if _nearest.empty(): return ""
	match _nearest.get("type",""):
		"tree":         return "Chop Tree"
		"rock":         return "Mine Rock"
		"water_source": return "Fill cup with water [E]"
		"item":
			var n = Items.get_item(_nearest.get("item_id","")).get("name","item")
			return "Pick up " + n + " [E]"
		"animal":
			var a = _nearest.get("animal_type","animal").capitalize()
			return "Hunt " + a
	return ""

func _input(event):
	if event is InputEventKey and event.pressed:
		match event.scancode:
			KEY_E:   _on_interact()
			KEY_F:   _on_use()
			KEY_TAB: GameState.inventory_open = !GameState.inventory_open
			KEY_C:   GameState.crafting_open = !GameState.crafting_open
			KEY_1,KEY_2,KEY_3,KEY_4,KEY_5,KEY_6,KEY_7,KEY_8:
				GameState.equipped_slot = event.scancode - KEY_1
	if event is InputEventMouseButton and event.pressed and event.button_index == BUTTON_LEFT:
		_on_attack()

func _on_attack():
	player.play_attack_swing()
	if _nearest.empty(): return
	var equipped = GameState.get_equipped()
	var dmg = 5
	if equipped.item_id != "":
		dmg = Items.get_item(equipped.item_id).get("damage", 5)

	_nearest["health"] = _nearest.get("health",3) - dmg
	if _nearest["health"] <= 0:
		var drops = world.destroy_object(_nearest)
		for d in drops:
			GameState.add_item(d[0], d[1])
			GameState.notify("Got %dx %s" % [d[1], Items.get_item(d[0]).get("name",d[0])])
		_nearest = {}

	if equipped.item_id != "":
		var slot = GameState.slots[GameState.equipped_slot]
		if slot.durability > 0:
			slot.durability -= 1
			if slot.durability <= 0:
				GameState.notify("⚠️ %s broke!" % Items.get_item(slot.item_id).get("name",""))
				GameState.remove_item(slot.item_id, 1)

func _on_interact():
	if not _nearest_plot.empty():
		Farming.interact(_nearest_plot)
		return
	if _nearest.empty(): return
	match _nearest.get("type",""):
		"item":
			var iid = _nearest.get("item_id","")
			var cnt = _nearest.get("count",1)
			GameState.add_item(iid, cnt)
			GameState.notify("Picked up %dx %s" % [cnt, Items.get_item(iid).get("name",iid)])
			world.remove_object(_nearest); _nearest = {}
		"water_source":
			if GameState.count_item("wooden_cup_empty") > 0:
				GameState.remove_item("wooden_cup_empty",1)
				GameState.add_item("wooden_cup",1)
				GameState.notify("💧 Filled wooden cup")
			else:
				GameState.notify("Need an empty wooden cup")
		"tree","rock":
			_on_attack()

func _on_use():
	var equipped = GameState.get_equipped()
	if equipped.item_id == "farm_plot":
		_place_farm_plot()
		return
	GameState.use_equipped()
	SaveManager.save_game()

func _place_farm_plot():
	var fwd = Vector3(sin(player.rotation.y), 0, cos(player.rotation.y))
	var place_pos = player.global_transform.origin + fwd * 1.8
	place_pos.y = world.get_height(place_pos.x, place_pos.z)
	Farming.place_plot(world, place_pos)
	GameState.remove_item("farm_plot", 1)
	GameState.notify("🟫 Farm plot placed")
