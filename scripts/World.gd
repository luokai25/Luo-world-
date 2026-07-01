extends Spatial
# Procedural 512x512 jungle world
# Trees, rocks, water, animals, biomes

const WORLD_SIZE   = 512
const HALF_SIZE    = 256
const TREE_COUNT   = 600
const ROCK_COUNT   = 300
const VINE_COUNT   = 200
const ANIMAL_COUNT = 195

var rng: RandomNumberGenerator
var objects: Array = []   # {type, pos, health, drops, node}
var animals: Array = []   # {type, pos, health, drops, node, vel}

func _ready():
	rng = RandomNumberGenerator.new()
	rng.seed = 42
	_build_terrain()
	_build_water()
	_place_trees()
	_place_rocks()
	_place_vines()
	_spawn_animals()
	_build_skybox()

# ── TERRAIN ───────────────────────────────────
func _build_terrain():
	var mesh_inst = MeshInstance.new()
	var plane     = PlaneMesh.new()
	plane.size    = Vector2(WORLD_SIZE, WORLD_SIZE)
	plane.subdivide_width  = 64
	plane.subdivide_depth  = 64
	mesh_inst.mesh = plane

	var mat = SpatialMaterial.new()
	mat.albedo_color          = Color(0.18, 0.42, 0.14)
	mat.roughness             = 0.9
	mat.metallic              = 0.0
	mesh_inst.material_override = mat
	add_child(mesh_inst)

	# Static collision body for ground
	var static_body = StaticBody.new()
	var col_shape   = CollisionShape.new()
	var box         = BoxShape.new()
	box.extents     = Vector3(HALF_SIZE, 0.5, HALF_SIZE)
	col_shape.shape = box
	static_body.add_child(col_shape)
	static_body.translation = Vector3(0, -0.5, 0)
	add_child(static_body)

# ── WATER ─────────────────────────────────────
func _build_water():
	# River
	for i in range(60):
		var t = float(i) / 60.0
		var x = sin(t * PI * 2) * 80.0 - 20.0
		var z = t * WORLD_SIZE - HALF_SIZE
		_spawn_water_marker(x, 0.05, z, "river")

	# Ponds
	for i in range(8):
		var x = rng.randf_range(-HALF_SIZE + 20, HALF_SIZE - 20)
		var z = rng.randf_range(-HALF_SIZE + 20, HALF_SIZE - 20)
		if abs(x) < 15 and abs(z) < 15:
			continue
		_spawn_water_marker(x, 0.05, z, "pond")

func _spawn_water_marker(x, y, z, wtype):
	var obj = {
		"type": "water_source", "pos": Vector3(x, y, z),
		"health": 999, "drops": [], "water_type": wtype, "node": null
	}
	objects.append(obj)
	# Visual quad
	var mi  = MeshInstance.new()
	var qm  = QuadMesh.new()
	qm.size = Vector2(6, 6) if wtype == "pond" else Vector2(3, 3)
	mi.mesh = qm
	var mat = SpatialMaterial.new()
	mat.albedo_color    = Color(0.12, 0.38, 0.72, 0.8)
	mat.flags_transparent = true
	mi.material_override = mat
	mi.translation = Vector3(x, y, z)
	mi.rotation_degrees = Vector3(-90, 0, 0)
	add_child(mi)
	obj.node = mi

# ── TREES ─────────────────────────────────────
func _place_trees():
	for i in range(TREE_COUNT):
		var x = rng.randf_range(-HALF_SIZE + 5, HALF_SIZE - 5)
		var z = rng.randf_range(-HALF_SIZE + 5, HALF_SIZE - 5)
		if abs(x) < 12 and abs(z) < 12:
			continue
		_spawn_tree(x, 0, z)

func _spawn_tree(x, y, z):
	var trunk_h = rng.randf_range(3.0, 8.0)
	var trunk_r = rng.randf_range(0.12, 0.28)

	# Trunk
	var trunk_mi  = MeshInstance.new()
	var cyl       = CylinderMesh.new()
	cyl.top_radius    = trunk_r * 0.5
	cyl.bottom_radius = trunk_r
	cyl.height        = trunk_h
	trunk_mi.mesh     = cyl
	var trunk_mat = SpatialMaterial.new()
	trunk_mat.albedo_color = Color(
		rng.randf_range(0.22, 0.35),
		rng.randf_range(0.14, 0.22),
		rng.randf_range(0.06, 0.12)
	)
	trunk_mat.roughness = 0.95
	trunk_mi.material_override = trunk_mat
	trunk_mi.translation = Vector3(x, y + trunk_h * 0.5, z)
	add_child(trunk_mi)

	# Canopy
	var n_layers = rng.randi_range(2, 4)
	for li in range(n_layers):
		var cr = (trunk_r * 8.0 + li * 0.5)
		var cy = y + trunk_h * (0.65 + li * 0.15)
		var leaf_mi   = MeshInstance.new()
		var sphere    = SphereMesh.new()
		sphere.radius = cr
		sphere.height = cr * 1.5
		leaf_mi.mesh  = sphere
		var leaf_mat  = SpatialMaterial.new()
		leaf_mat.albedo_color = Color(
			rng.randf_range(0.05, 0.20),
			rng.randf_range(0.30, 0.55),
			rng.randf_range(0.05, 0.18)
		)
		leaf_mat.roughness = 0.85
		leaf_mi.material_override = leaf_mat
		leaf_mi.translation = Vector3(
			x + rng.randf_range(-0.4, 0.4),
			cy,
			z + rng.randf_range(-0.4, 0.4)
		)
		add_child(leaf_mi)

	# Collision + game object
	var static_body = StaticBody.new()
	var col_shape   = CollisionShape.new()
	var capsule     = CapsuleShape.new()
	capsule.radius  = trunk_r
	capsule.height  = trunk_h
	col_shape.shape = capsule
	static_body.add_child(col_shape)
	static_body.translation = Vector3(x, y + trunk_h * 0.5, z)
	static_body.set_meta("luo_type", "tree")
	add_child(static_body)

	var obj = {
		"type": "tree", "pos": Vector3(x, y, z),
		"health": 5,
		"drops": [["wood_log", rng.randi_range(2, 5)], ["stick", rng.randi_range(1, 3)]],
		"node": static_body
	}
	objects.append(obj)

# ── ROCKS ─────────────────────────────────────
func _place_rocks():
	for i in range(ROCK_COUNT):
		var x = rng.randf_range(-HALF_SIZE + 3, HALF_SIZE - 3)
		var z = rng.randf_range(-HALF_SIZE + 3, HALF_SIZE - 3)
		if abs(x) < 8 and abs(z) < 8:
			continue
		var s  = rng.randf_range(0.3, 1.2)
		var mi = MeshInstance.new()
		var sm = SphereMesh.new()
		sm.radius = s * 0.5
		sm.height = s
		mi.mesh   = sm
		var mat = SpatialMaterial.new()
		var grey = rng.randf_range(0.33, 0.52)
		mat.albedo_color = Color(grey, grey, grey * 0.95)
		mat.roughness    = 0.95
		mi.material_override = mat
		mi.translation = Vector3(x, s * 0.3, z)
		add_child(mi)

		var static_body = StaticBody.new()
		var col         = CollisionShape.new()
		var sp          = SphereShape.new()
		sp.radius       = s * 0.5
		col.shape       = sp
		static_body.add_child(col)
		static_body.translation = Vector3(x, s * 0.3, z)
		static_body.set_meta("luo_type", "rock")
		add_child(static_body)

		var obj = {
			"type": "rock", "pos": Vector3(x, s * 0.3, z),
			"health": 3,
			"drops": [["stone", rng.randi_range(1, 4)], ["flint", rng.randi_range(0, 2)]],
			"node": static_body
		}
		objects.append(obj)

# ── VINES / ITEMS ON GROUND ───────────────────
func _place_vines():
	for i in range(VINE_COUNT):
		var x = rng.randf_range(-HALF_SIZE + 2, HALF_SIZE - 2)
		var z = rng.randf_range(-HALF_SIZE + 2, HALF_SIZE - 2)
		if abs(x) < 5 and abs(z) < 5:
			continue
		var obj = {
			"type": "item", "pos": Vector3(x, 0.1, z),
			"health": 1, "item_id": "vine",
			"count": rng.randi_range(1, 3),
			"drops": [["vine", rng.randi_range(1, 3)]],
			"node": null
		}
		objects.append(obj)

# ── ANIMALS ───────────────────────────────────
func _spawn_animals():
	var configs = [
		["deer",   50, 30, [["raw_meat", 3], ["hide", 1]]],
		["boar",   25, 50, [["raw_meat", 4], ["hide", 2]]],
		["rabbit", 80, 10, [["raw_meat", 1]]],
		["bird",   40, 5,  [["feather", 2]]],
	]
	for cfg in configs:
		for i in range(cfg[1]):
			var x = rng.randf_range(-HALF_SIZE + 10, HALF_SIZE - 10)
			var z = rng.randf_range(-HALF_SIZE + 10, HALF_SIZE - 10)
			if abs(x) < 15 and abs(z) < 15:
				continue
			animals.append({
				"type": "animal", "animal_type": cfg[0],
				"pos": Vector3(x, 0, z),
				"health": cfg[2], "drops": cfg[3],
				"vel": Vector3.ZERO, "flee": false,
				"wander_timer": rng.randf_range(3.0, 8.0),
				"target": Vector3(x, 0, z),
				"node": null
			})

# ── SKYBOX ────────────────────────────────────
func _build_skybox():
	var world_env = WorldEnvironment.new()
	var env = Environment.new()
	env.background_mode  = Environment.BG_SKY
	var sky = ProceduralSky.new()
	sky.sky_top_color      = Color(0.15, 0.28, 0.45)
	sky.sky_horizon_color  = Color(0.38, 0.60, 0.42)
	sky.ground_bottom_color= Color(0.10, 0.20, 0.10)
	sky.ground_horizon_color=Color(0.22, 0.38, 0.20)
	sky.sun_color          = Color(1.0, 0.97, 0.86)
	sky.sun_energy         = 16.0
	env.background_sky     = sky
	env.fog_enabled        = true
	env.fog_color          = Color(0.58, 0.76, 0.50)
	env.fog_depth_end      = 180.0
	env.fog_depth_begin    = 25.0
	env.ambient_light_color  = Color(0.22, 0.34, 0.22)
	env.ambient_light_energy = 0.6
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_env.environment = env
	add_child(world_env)

	# Directional sun light
	var sun = DirectionalLight.new()
	sun.rotation_degrees  = Vector3(-55, 30, 0)
	sun.light_color       = Color(1.0, 0.97, 0.86)
	sun.light_energy      = 1.2
	sun.shadow_enabled    = true
	add_child(sun)

# ── RUNTIME ───────────────────────────────────
func _physics_process(delta):
	_update_animals(delta)

func _update_animals(delta):
	pass  # Animals update from HUD/main

func nearest_object(player_pos: Vector3, radius: float = 3.5) -> Dictionary:
	var best = {}
	var best_dist = radius
	for obj in objects:
		var d = player_pos.distance_to(obj.pos)
		if d < best_dist:
			best_dist = d
			best = obj
	for anim in animals:
		var d = player_pos.distance_to(anim.pos)
		if d < best_dist:
			best_dist = d
			best = anim
	return best

func destroy_object(obj: Dictionary) -> Array:
	var drops = obj.get("drops", [])
	if obj.has("node") and obj.node != null:
		obj.node.queue_free()
	objects.erase(obj)
	return drops

func remove_object(obj: Dictionary):
	if obj.has("node") and obj.node != null:
		obj.node.queue_free()
	objects.erase(obj)
