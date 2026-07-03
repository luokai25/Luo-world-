extends Control
# Crafting panel - toggled by GameState.crafting_open
# Recipe list built at runtime from Items.RECIPES

onready var list_container = $Panel/Scroll/List
onready var close_btn      = $Panel/CloseBtn

var recipe_refs: Dictionary = {}   # recipe_id -> {"ing_label":..., "craft_btn":..., "icon":...}

func _ready():
	visible = false
	close_btn.connect("pressed", self, "_on_close")
	_build_recipes()
	GameState.connect("inventory_changed", self, "_refresh_all")

func _build_recipes():
	for recipe_id in Items.RECIPES.keys():
		_make_recipe_row(recipe_id)

func _make_recipe_row(recipe_id: String):
	var recipe = Items.RECIPES[recipe_id]
	var out_id = recipe["output"][0]

	var row = PanelContainer.new()
	row.rect_min_size = Vector2(0, 76)

	var hbox = HBoxContainer.new()
	hbox.rect_min_size = Vector2(0, 76)
	hbox.size_flags_horizontal = SIZE_EXPAND_FILL

	var icon = TextureRect.new()
	icon.texture = load(Items.get_icon_path(out_id))
	icon.rect_min_size = Vector2(56, 56)
	icon.expand = true
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	hbox.add_child(icon)

	var info_vbox = VBoxContainer.new()
	info_vbox.size_flags_horizontal = SIZE_EXPAND_FILL
	info_vbox.rect_min_size = Vector2(420, 0)

	var name_lbl = Label.new()
	name_lbl.text = recipe["name"]
	info_vbox.add_child(name_lbl)

	var ing_lbl = RichTextLabel.new()
	ing_lbl.bbcode_enabled = true
	ing_lbl.fit_content_height = true
	ing_lbl.rect_min_size = Vector2(0, 26)
	ing_lbl.scroll_active = false
	info_vbox.add_child(ing_lbl)

	hbox.add_child(info_vbox)

	var craft_btn = Button.new()
	craft_btn.text = "CRAFT"
	craft_btn.rect_min_size = Vector2(100, 56)
	craft_btn.connect("pressed", self, "_on_craft_pressed", [recipe_id])
	hbox.add_child(craft_btn)

	row.add_child(hbox)
	list_container.add_child(row)

	recipe_refs[recipe_id] = {"ing_label": ing_lbl, "craft_btn": craft_btn}
	_refresh_row(recipe_id)

func _process(_delta):
	if GameState.crafting_open != visible:
		visible = GameState.crafting_open
		if visible:
			_refresh_all()
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		else:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _refresh_all():
	for recipe_id in recipe_refs:
		_refresh_row(recipe_id)

func _refresh_row(recipe_id: String):
	var recipe = Items.RECIPES[recipe_id]
	var refs = recipe_refs[recipe_id]
	var text = ""
	var can = true
	for item_id in recipe["inputs"]:
		var need = recipe["inputs"][item_id]
		var have = GameState.count_item(item_id)
		if have < need:
			can = false
		var color = "88ff88" if have >= need else "ff6666"
		var iname = Items.get_item(item_id).get("name", item_id)
		text += "[color=#%s]%s %d/%d[/color]   " % [color, iname, have, need]
	refs.ing_label.bbcode_text = text
	refs.craft_btn.disabled = not can
	refs.craft_btn.text = "CRAFT" if can else "MISSING"

func _on_craft_pressed(recipe_id: String):
	GameState.craft(recipe_id)
	_refresh_row(recipe_id)

func _on_close():
	GameState.crafting_open = false
