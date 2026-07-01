extends Node
# Item definitions and crafting recipes - global singleton

const ITEMS = {
	"stone_axe": {
		"name": "Stone Axe", "icon": "🪓", "category": "tool",
		"damage": 15, "durability": 100, "stackable": false, "max_stack": 1,
		"description": "Hand-chipped flint head bound to a stick with vine."
	},
	"cooked_meat": {
		"name": "Cooked Cow Meat", "icon": "🥩", "category": "food",
		"nutrition": 45, "hydration": 5, "stackable": true, "max_stack": 10,
		"description": "A thick charred slab of beef. Restores hunger."
	},
	"wooden_cup": {
		"name": "Wooden Cup (Water)", "icon": "🥤", "category": "drink",
		"hydration": 60, "stackable": false, "max_stack": 1,
		"becomes": "wooden_cup_empty",
		"description": "A hand-carved cup full of clean water."
	},
	"wooden_cup_empty": {
		"name": "Wooden Cup (Empty)", "icon": "🪣", "category": "tool",
		"stackable": false, "max_stack": 1,
		"description": "Fill this at a river or pond."
	},
	"wood_log": {
		"name": "Wood Log", "icon": "🪵", "category": "resource",
		"stackable": true, "max_stack": 20,
		"description": "A rough log from a jungle tree."
	},
	"stick": {
		"name": "Stick", "icon": "|", "category": "resource",
		"stackable": true, "max_stack": 30,
		"description": "A straight wooden stick."
	},
	"stone": {
		"name": "Stone", "icon": "🪨", "category": "resource",
		"stackable": true, "max_stack": 30,
		"description": "A rough chunk of stone."
	},
	"flint": {
		"name": "Flint", "icon": "◇", "category": "resource",
		"stackable": true, "max_stack": 20,
		"description": "Sharp flint, useful for tools."
	},
	"vine": {
		"name": "Vine", "icon": "~", "category": "resource",
		"stackable": true, "max_stack": 20,
		"description": "A strong jungle vine for binding."
	},
	"raw_meat": {
		"name": "Raw Meat", "icon": "🫀", "category": "food_raw",
		"stackable": true, "max_stack": 10,
		"description": "Must be cooked before eating."
	},
	"rope": {
		"name": "Rope", "icon": "〰", "category": "resource",
		"stackable": true, "max_stack": 10,
		"description": "Twisted vines, strong binding."
	},
	"hide": {
		"name": "Animal Hide", "icon": "🟫", "category": "resource",
		"stackable": true, "max_stack": 10,
		"description": "Rough animal hide for clothing."
	},
	"feather": {
		"name": "Feather", "icon": "🪶", "category": "resource",
		"stackable": true, "max_stack": 30,
		"description": "A bird feather. Useful for arrows."
	},
	"iron_ore": {
		"name": "Iron Ore", "icon": "⬛", "category": "resource",
		"stackable": true, "max_stack": 20,
		"description": "Raw iron ore from rocky hills."
	},
	"fruit": {
		"name": "Jungle Fruit", "icon": "🍈", "category": "food",
		"nutrition": 20, "hydration": 15, "stackable": true, "max_stack": 10,
		"description": "A ripe fruit from the jungle canopy."
	},
	"berry": {
		"name": "Wild Berries", "icon": "🫐", "category": "food",
		"nutrition": 10, "hydration": 8, "stackable": true, "max_stack": 20,
		"description": "Small wild berries. Quick snack."
	},
	"mushroom_edible": {
		"name": "Edible Mushroom", "icon": "🍄", "category": "food",
		"nutrition": 15, "hydration": 3, "stackable": true, "max_stack": 15,
		"description": "A safe jungle mushroom."
	},
	"mushroom_cooked": {
		"name": "Cooked Mushroom", "icon": "🍄", "category": "food",
		"nutrition": 25, "hydration": 5, "stackable": true, "max_stack": 15,
		"description": "A cooked jungle mushroom."
	},
	"wooden_spear": {
		"name": "Wooden Spear", "icon": "🏹", "category": "weapon",
		"damage": 20, "durability": 60, "stackable": false, "max_stack": 1,
		"description": "A sharpened stick for hunting."
	},
	"bow": {
		"name": "Wooden Bow", "icon": "🏹", "category": "weapon",
		"damage": 25, "durability": 40, "stackable": false, "max_stack": 1,
		"description": "A simple hunting bow."
	},
	"arrow": {
		"name": "Arrow", "icon": "➶", "category": "ammo",
		"stackable": true, "max_stack": 30,
		"description": "A sharpened arrow."
	},
	"leather_armor": {
		"name": "Leather Armor", "icon": "🥋", "category": "armor",
		"defense": 10, "stackable": false, "max_stack": 1,
		"description": "Hide armor, reduces damage."
	},
	"torch": {
		"name": "Torch", "icon": "🔦", "category": "tool",
		"durability": 300, "stackable": false, "max_stack": 1,
		"description": "Provides light and warmth at night."
	},
	"stone_knife": {
		"name": "Stone Knife", "icon": "🔪", "category": "tool",
		"damage": 10, "durability": 80, "stackable": false, "max_stack": 1,
		"description": "Sharp stone knife for skinning."
	},
	"campfire": {
		"name": "Campfire", "icon": "🔥", "category": "structure",
		"stackable": false, "max_stack": 1,
		"description": "A lit campfire. Cook food here."
	},
	"shelter_frame": {
		"name": "Shelter Frame", "icon": "🏠", "category": "structure",
		"stackable": false, "max_stack": 1,
		"description": "Basic frame for a lean-to shelter."
	},
}

const RECIPES = {
	"stone_axe": {
		"name": "Stone Axe", "inputs": {"flint": 2, "stick": 1, "vine": 1},
		"output": ["stone_axe", 1], "time": 3.0
	},
	"wooden_spear": {
		"name": "Wooden Spear", "inputs": {"stick": 2, "flint": 1, "vine": 1},
		"output": ["wooden_spear", 1], "time": 2.0
	},
	"rope": {
		"name": "Rope", "inputs": {"vine": 3},
		"output": ["rope", 1], "time": 1.0
	},
	"campfire": {
		"name": "Campfire", "inputs": {"wood_log": 3, "stick": 2, "flint": 1},
		"output": ["campfire", 1], "time": 5.0
	},
	"stick": {
		"name": "Sticks x4", "inputs": {"wood_log": 1},
		"output": ["stick", 4], "time": 1.5
	},
	"wooden_cup_empty": {
		"name": "Wooden Cup", "inputs": {"wood_log": 1, "stick": 1},
		"output": ["wooden_cup_empty", 1], "time": 4.0
	},
	"arrow": {
		"name": "Arrows x5", "inputs": {"stick": 3, "flint": 2, "feather": 3},
		"output": ["arrow", 5], "time": 2.0
	},
	"bow": {
		"name": "Wooden Bow", "inputs": {"stick": 3, "vine": 2},
		"output": ["bow", 1], "time": 5.0
	},
	"leather_armor": {
		"name": "Leather Armor", "inputs": {"hide": 5, "vine": 3},
		"output": ["leather_armor", 1], "time": 15.0
	},
	"torch": {
		"name": "Torch", "inputs": {"stick": 1, "vine": 1},
		"output": ["torch", 1], "time": 1.5
	},
	"stone_knife": {
		"name": "Stone Knife", "inputs": {"flint": 2, "stick": 1},
		"output": ["stone_knife", 1], "time": 2.0
	},
	"shelter_frame": {
		"name": "Shelter Frame", "inputs": {"wood_log": 6, "rope": 4},
		"output": ["shelter_frame", 1], "time": 20.0
	},
}

func get_item(id: String) -> Dictionary:
	return ITEMS.get(id, {})

func get_recipe(id: String) -> Dictionary:
	return RECIPES.get(id, {})
