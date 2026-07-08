extends Node
# Farming/Cultivation system - autoload singleton
# Plots progress: EMPTY -> seed -> sprout -> young -> mature -> ripe -> (harvest) -> EMPTY

const STAGE_EMPTY = -1
const STAGE_SEED = 0
const STAGE_SPROUT = 1
const STAGE_YOUNG = 2
const STAGE_MATURE = 3
const STAGE_RIPE = 4

const STAGE_NAMES = ["seed", "sprout", "young", "mature", "ripe"]
const GROWTH_TIME_PER_STAGE = 45.0   # real seconds per stage advance

var plots: Array = []   # [{pos, stage, timer, plot_node, crop_node, world_ref}]
var crop_models: Dictionary = {}
var farm_plot_model = null

signal plot_stage_changed(plot)

func _ready():
	farm_plot_model = load("res://assets/models/farm_plot.glb")
	for stage_name in STAGE_NAMES:
		var path = "res://assets/models/crop_grain_%s.glb" % stage_name
		var res = load(path)
		if res:
			crop_models[stage_name] = res

func _process(delta):
	for plot in plots:
		if plot.stage >= STAGE_SEED and plot.stage < STAGE_RIPE:
			plot.timer += delta
			if plot.timer >= GROWTH_TIME_PER_STAGE:
				plot.timer = 0.0
				_advance_stage(plot)

func _advance_stage(plot):
	plot.stage += 1
	_update_crop_visual(plot)
	emit_signal("plot_stage_changed", plot)
	if plot.stage == STAGE_RIPE:
		GameState.notify("🌾 A crop is ready to harvest!")

func _update_crop_visual(plot):
	if plot.crop_node and is_instance_valid(plot.crop_node):
		plot.crop_node.queue_free()
		plot.crop_node = null
	if plot.stage < STAGE_SEED:
		return
	var stage_name = STAGE_NAMES[plot.stage]
	if crop_models.has(stage_name):
		var node = crop_models[stage_name].instance()
		node.translation = plot.pos + Vector3(0, 0.03, 0)
		plot.world_ref.add_child(node)
		plot.crop_node = node

func place_plot(world, pos: Vector3) -> Dictionary:
	var node = null
	if farm_plot_model:
		node = farm_plot_model.instance()
		node.translation = pos
		world.add_child(node)

	var plot = {
		"pos": pos, "stage": STAGE_EMPTY, "timer": 0.0,
		"plot_node": node, "crop_node": null, "world_ref": world
	}
	plots.append(plot)
	return plot

func nearest_plot(player_pos: Vector3, radius: float = 3.0) -> Dictionary:
	var best = {}
	var best_dist = radius
	for plot in plots:
		var d = player_pos.distance_to(plot.pos)
		if d < best_dist:
			best_dist = d
			best = plot
	return best

func plant(plot: Dictionary) -> bool:
	if plot.empty() or plot.stage != STAGE_EMPTY:
		return false
	if GameState.count_item("wild_seeds") < 1:
		GameState.notify("Need Wild Seeds to plant")
		return false
	GameState.remove_item("wild_seeds", 1)
	plot.stage = STAGE_SEED
	plot.timer = 0.0
	_update_crop_visual(plot)
	GameState.notify("🌱 Planted seeds")
	return true

func harvest(plot: Dictionary) -> bool:
	if plot.empty() or plot.stage != STAGE_RIPE:
		return false
	var amount = randi() % 3 + 2   # 2-4 grain
	GameState.add_item("grain", amount)
	GameState.notify("🌾 Harvested %dx Grain" % amount)
	plot.stage = STAGE_EMPTY
	plot.timer = 0.0
	_update_crop_visual(plot)
	return true

func get_prompt(plot: Dictionary) -> String:
	if plot.empty():
		return ""
	match plot.stage:
		STAGE_EMPTY:
			return "Plant Wild Seeds [E]"
		STAGE_RIPE:
			return "Harvest Grain [E]"
		_:
			var pct = int((plot.timer / GROWTH_TIME_PER_STAGE) * 100)
			return "Growing (%s)... %d%%" % [STAGE_NAMES[plot.stage], pct]

func interact(plot: Dictionary):
	if plot.empty():
		return
	if plot.stage == STAGE_EMPTY:
		plant(plot)
	elif plot.stage == STAGE_RIPE:
		harvest(plot)
	else:
		GameState.notify(get_prompt(plot))
