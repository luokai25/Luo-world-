extends Control
# Inventory panel - toggled by GameState.inventory_open
# 24 slots built at runtime, tap a slot to swap it into the equipped slot

onready var grid       = $Panel/Scroll/Grid
onready var info_name  = $Panel/InfoName
onready var info_desc  = $Panel/InfoDesc
onready var close_btn  = $Panel/CloseBtn
onready var craft_btn  = $Panel/CraftBtn

var slot_refs: Array = []   # [{ "btn": TextureButton, "count": Label }]

func _ready():
	visible = false
	close_btn.connect("pressed", self, "_on_close")
	craft_btn.connect("pressed", self, "_on_craft_open")
	_build_slots()
	GameState.connect("inventory_changed", self, "_refresh")

func _build_slots():
	for i in range(GameState.SLOT_COUNT):
		var btn = TextureButton.new()
		btn.rect_min_size = Vector2(80, 80)
		btn.expand = true
		btn.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		btn.connect("pressed", self, "_on_slot_pressed", [i])

		var count_lbl = Label.new()
		count_lbl.anchor_left = 1.0
		count_lbl.anchor_top = 1.0
		count_lbl.anchor_right = 1.0
		count_lbl.anchor_bottom = 1.0
		count_lbl.margin_left = -26
		count_lbl.margin_top = -22
		count_lbl.margin_right = -2
		count_lbl.margin_bottom = -2
		count_lbl.align = Label.ALIGN_RIGHT
		count_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		btn.add_child(count_lbl)

		var eq_marker = Label.new()
		eq_marker.name = "EqMarker"
		eq_marker.anchor_left = 0.0
		eq_marker.anchor_top = 0.0
		eq_marker.margin_left = 2
		eq_marker.margin_top = 0
		eq_marker.margin_right = 20
		eq_marker.margin_bottom = 18
		eq_marker.text = ""
		eq_marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
		btn.add_child(eq_marker)

		grid.add_child(btn)
		slot_refs.append({"btn": btn, "count": count_lbl, "marker": eq_marker})

func _process(_delta):
	if GameState.inventory_open != visible:
		visible = GameState.inventory_open
		if visible:
			_refresh()
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		elif not GameState.crafting_open:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _refresh():
	for i in range(slot_refs.size()):
		var slot = GameState.slots[i]
		var refs = slot_refs[i]
		if slot.item_id != "":
			refs.btn.texture_normal = load(Items.get_icon_path(slot.item_id))
			refs.count.text = str(slot.count) if slot.count > 1 else ""
		else:
			refs.btn.texture_normal = null
			refs.count.text = ""
		refs.marker.text = "★" if i == GameState.equipped_slot else ""
	_update_info()

func _update_info():
	var eq = GameState.slots[GameState.equipped_slot]
	if eq.item_id != "":
		var d = Items.get_item(eq.item_id)
		info_name.text = d.get("name", "")
		var desc = d.get("description", "")
		if eq.durability >= 0:
			var maxd = d.get("max_durability", eq.durability)
			desc += "   Durability: %d/%d" % [eq.durability, maxd]
		info_desc.text = desc
	else:
		info_name.text = "Empty slot"
		info_desc.text = ""

func _on_slot_pressed(idx: int):
	if idx != GameState.equipped_slot:
		var tmp = GameState.slots[GameState.equipped_slot]
		GameState.slots[GameState.equipped_slot] = GameState.slots[idx]
		GameState.slots[idx] = tmp
	GameState.emit_signal("inventory_changed")

func _on_close():
	GameState.inventory_open = false

func _on_craft_open():
	GameState.inventory_open = false
	GameState.crafting_open = true
