extends Node
# Global game state - autoloaded singleton

signal notification_added(text)
signal stats_changed()
signal inventory_changed()
signal interact_prompt_changed(text)

# ── Time ──────────────────────────────────────
var time_of_day: float = 10.0
var day_number: int = 1
var day_speed: float = 0.5

# ── Player stats ──────────────────────────────
var health: float   = 100.0
var max_health: float = 100.0
var hunger: float   = 100.0
var max_hunger: float = 100.0
var thirst: float   = 100.0
var max_thirst: float = 100.0
var stamina: float  = 100.0
var max_stamina: float = 100.0
var body_temp: float = 37.0

# ── Inventory ─────────────────────────────────
var slots: Array = []         # Array of {item_id, count, durability}
const SLOT_COUNT = 24
const HOTBAR_SIZE = 8
var equipped_slot: int = 0
var inventory_open: bool = false
var crafting_open: bool = false

# ── World state ───────────────────────────────
var interact_prompt: String = ""
var weather: String = "clear"
var campfires: Array = []

# ── Notifications ─────────────────────────────
var notifications: Array = []
const NOTIF_DURATION = 3.5

# ── Timers ────────────────────────────────────
var _hunger_timer: float = 0.0
var _thirst_timer: float = 0.0
var _warn_timer: float   = 0.0

func _ready():
	# Init empty slots
	for i in range(SLOT_COUNT):
		slots.append({"item_id": "", "count": 0, "durability": -1})
	give_starting_items()

func give_starting_items():
	add_item("stone_axe", 1, 100)
	add_item("cooked_meat", 3)
	add_item("wooden_cup", 1)
	notify("🌿 Welcome to Luo World")
	notify("You wake up deep in the jungle...")

func _process(delta):
	# Time
	time_of_day += delta * day_speed / 60.0
	if time_of_day >= 24.0:
		time_of_day = 0.0
		day_number += 1
		notify("🌅 Day %d" % day_number)

	# Hunger
	_hunger_timer += delta
	if _hunger_timer >= 6.0:
		hunger = max(0.0, hunger - 1.0)
		_hunger_timer = 0.0
		if hunger == 0:
			health = max(0.0, health - 0.5)
		elif hunger < 20.0:
			_warn_once("🍖 You are very hungry!", 30.0)

	# Thirst
	_thirst_timer += delta
	if _thirst_timer >= 4.0:
		thirst = max(0.0, thirst - 1.0)
		_thirst_timer = 0.0
		if thirst == 0:
			health = max(0.0, health - 1.0)
		elif thirst < 20.0:
			_warn_once("💧 You are very thirsty!", 30.0)

	# Notifications decay
	for i in range(notifications.size() - 1, -1, -1):
		notifications[i][1] -= delta
		if notifications[i][1] <= 0:
			notifications.remove(i)

	_warn_timer -= delta
	emit_signal("stats_changed")

func _warn_once(text: String, cooldown: float):
	if _warn_timer <= 0:
		notify(text)
		_warn_timer = cooldown

# ── INVENTORY ─────────────────────────────────
func add_item(item_id: String, count: int = 1, durability: int = -1) -> bool:
	var data = Items.get_item(item_id)
	if data.empty():
		return false

	# Stack into existing slot
	if data.get("stackable", false):
		for i in range(SLOT_COUNT):
			var s = slots[i]
			if s.item_id == item_id and s.count < data.get("max_stack", 99):
				var add = min(count, data.get("max_stack", 99) - s.count)
				slots[i].count += add
				count -= add
				if count <= 0:
					emit_signal("inventory_changed")
					return true

	# Find empty slot
	if count > 0:
		for i in range(SLOT_COUNT):
			if slots[i].item_id == "":
				slots[i].item_id   = item_id
				slots[i].count     = count
				slots[i].durability = durability if durability >= 0 else data.get("max_durability", -1)
				emit_signal("inventory_changed")
				return true

	notify("Inventory full!")
	return false

func remove_item(item_id: String, count: int = 1) -> bool:
	var removed = 0
	for i in range(SLOT_COUNT):
		if slots[i].item_id == item_id:
			var take = min(count - removed, slots[i].count)
			slots[i].count -= take
			removed += take
			if slots[i].count <= 0:
				slots[i] = {"item_id": "", "count": 0, "durability": -1}
			if removed >= count:
				emit_signal("inventory_changed")
				return true
	return false

func count_item(item_id: String) -> int:
	var total = 0
	for s in slots:
		if s.item_id == item_id:
			total += s.count
	return total

func has_items(requirements: Dictionary) -> bool:
	for k in requirements:
		if count_item(k) < requirements[k]:
			return false
	return true

func get_equipped() -> Dictionary:
	return slots[equipped_slot]

func use_equipped():
	var slot = slots[equipped_slot]
	if slot.item_id == "":
		return
	var data = Items.get_item(slot.item_id)
	var cat = data.get("category", "")

	if cat == "food":
		eat(data.get("nutrition", 0))
		drink_water(data.get("hydration", 0))
		var becomes = data.get("becomes", "")
		remove_item(slot.item_id, 1)
		if becomes != "":
			add_item(becomes, 1)
		notify("Ate %s (+%d hunger)" % [data["name"], data.get("nutrition", 0)])
	elif cat == "drink":
		drink_water(data.get("hydration", 0))
		var becomes = data.get("becomes", "")
		remove_item(slot.item_id, 1)
		if becomes != "":
			add_item(becomes, 1)
		notify("Drank %s (+%d thirst)" % [data["name"], data.get("hydration", 0)])
	else:
		notify("Can't use %s directly" % data.get("name", "that"))

func can_craft(recipe_id: String) -> bool:
	var recipe = Items.get_recipe(recipe_id)
	if recipe.empty():
		return false
	return has_items(recipe["inputs"])

func craft(recipe_id: String) -> bool:
	if not can_craft(recipe_id):
		notify("❌ Missing materials")
		return false
	var recipe = Items.get_recipe(recipe_id)
	for item_id in recipe["inputs"]:
		remove_item(item_id, recipe["inputs"][item_id])
	var out = recipe["output"]
	add_item(out[0], out[1])
	notify("✅ Crafted %s" % recipe["name"])
	return true

# ── STATS ─────────────────────────────────────
func eat(amount: float):
	hunger = min(max_hunger, hunger + amount)

func drink_water(amount: float):
	thirst = min(max_thirst, thirst + amount)

func heal(amount: float):
	health = min(max_health, health + amount)

func take_damage(amount: float):
	health = max(0.0, health - amount)

# ── NOTIFY ────────────────────────────────────
func notify(text: String):
	notifications.append([text, NOTIF_DURATION])
	emit_signal("notification_added", text)

func get_current_notification() -> String:
	if notifications.size() > 0:
		return notifications[notifications.size() - 1][0]
	return ""

# ── TIME ──────────────────────────────────────
func get_time_str() -> String:
	var h = int(time_of_day)
	var m = int((time_of_day - h) * 60)
	var icon = "🌙" if (h < 6 or h >= 20) else ("🌅" if (h < 8 or h >= 18) else "☀️")
	return "Day %d  %02d:%02d %s" % [day_number, h, m, icon]
