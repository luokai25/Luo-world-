extends Spatial
# 512x512 procedural jungle world - photorealistic with GLB assets

const WORLD_SIZE = 512
const HALF       = 256

var rng: RandomNumberGenerator
var objects: Array = []
var animals: Array = []

func _ready():
	rng = RandomNumberGenerator.new()
	rng.seed = 42
	_build_lighting()
	_build_terrain()
	_build_water()
	_place_trees()
	_place_rocks()
	_place_collectibles()
	_spawn_animals()

# ── LIGHTING ─────────────────────────────────
func _build_lighting():
	# Sun
	var sun = DirectionalLight.new()
	sun.name = "Sun"
	sun.rotation_degrees  = Vector3(-52, 30, 0)
	sun.light_color       = Color(1.0, 0.97, 0.86)
	sun.light_energy      = 1.3
	sun.shadow_enabled    = true
	sun.shadow_bias       = 0.1
	add_child(sun)

	# Ambient fill
	var env_node = WorldEnvironment.new()
	var env      = Environment.new()
	env.background_mode   = Environment.BG_SKY
	var sky = ProceduralSky.new()
	sky.sky_top_color       = Color(0.12, 0.24, 0.42)
	sky.sky_horizon_color   = Color(0.40, 0.62, 0.38)
	sky.sky_curve           = 0.22
	sky.sky_energy          = 1.0
	sky.ground_bottom_color = Color(0.08, 0.18, 0.08)
	sky.ground_horizon_color= Color(0.20, 0.36, 0.18)
	sky.sun_color           = Color(1.0, 0.97, 0.86)
	sky.sun_energy          = 16.0
	sky.sun_latitude        = 52.0
	env.background_sky      = sky
	env.background_energy   = 1.2
	env.ambient_light_color   = Color(0.20, 0.32, 0.20)
	env.ambient_light_energy  = 0.55
	env.fog_enabled           = true
	env.fog_color             = Color(0.55, 0.74, 0.48)
	env.fog_sun_color         = Color(1.0, 0.85, 0.60)
	env.fog_sun_amount        = 0.4
	env.fog_depth_enabled     = true
	env.fog_depth_begin       = 30.0
	env.fog_depth_end         = 220.0
	env.fog_depth_curve       = 1.0
	env.tonemap_mode          = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure      = 1.1
	env.tonemap_white         = 1.0
	env_node.environment      = env
	add_child(env_node)

# ── TERRAIN ──────────────────────────────────
func _build_terrain():
	var mi = MeshInstance.new()
	mi.name = "Terrain"
	var plane = PlaneMesh.new()
	plane.size = Vector2(WORLD_SIZE, WORLD_SIZE)
	plane.subdivide_width  = 32
	plane.subdivide_depth  = 32
	mi.mesh = plane
	var mat = SpatialMaterial.new()
	mat.albedo_color = Color(0.15, 0.38, 0.12)
	mat.roughness    = 0.95
	mat.metallic     = 0.0
	mi.material_override = mat
	add_child(mi)

	var sb  = StaticBody.new()
	var cs  = CollisionShape.new()
	var box = BoxShape.new()
	box.extents = Vector3(HALF, 0.5, HALF)
	cs.shape    = box
	sb.add_child(cs)
	sb.translation = Vector3(0, -0.5, 0)
	add_child(sb)

# ── WATER ────────────────────────────────────
func _build_water():
	# River
	for i in range(40):
		var t = float(i) / 40.0
		var x = sin(t * PI * 2) * 80.0 - 20.0
		var z = t * WORLD_SIZE - HALF
		_add_water_plane(x, z, Vector2(6, 6))

	# Ponds
	for i in range(8):
		var x = rng.randf_range(-HALF+30, HALF-30)
		var z = rng.randf_range(-HALF+30, HALF-30)
		if abs(x)<15 and abs(z)<15: continue
		_add_water_plane(x, z, Vector2(25, 25))
		objects.append({"type":"water_source","pos":Vector3(x,0,z),"health":999,"drops":[],"node":null})

func _add_water_plane(x, z, size):
	var mi  = MeshInstance.new()
	var qm  = QuadMesh.new()
	qm.size = size
	mi.mesh = qm
	var mat = SpatialMaterial.new()
	mat.albedo_color     = Color(0.10, 0.35, 0.72, 0.82)
	mat.flags_transparent = true
	mat.roughness         = 0.05
	mat.metallic          = 0.3
	mi.material_override  = mat
	mi.translation        = Vector3(x, 0.08, z)
	mi.rotation_degrees   = Vector3(-90, 0, 0)
	add_child(mi)

# ── TREES ────────────────────────────────────
func _place_trees():
	var tree_models = []
	for i in range(6):
		var path = "res://assets/models/tree_%d.glb" % i
		var loaded = load(path)
		if loaded:
			tree_models.append(loaded)

	for i in range(600):
		var x = rng.randf_range(-HALF+5, HALF-5)
		var z = rng.randf_range(-HALF+5, HALF-5)
		if abs(x)<12 and abs(z)<12: continue

		var mi: Spatial
		if tree_models.size() > 0:
			var model = tree_models[rng.randi() % tree_models.size()]
			mi = model.instance()
		else:
			mi = _make_fallback_tree()

		mi.translation = Vector3(x, 0, z)
		mi.rotation_degrees.y = rng.randf_range(0, 360)
		var s = rng.randf_range(0.8, 2.0)
		mi.scale = Vector3(s, s, s)
		add_child(mi)

		var sb = StaticBody.new()
		var cs = CollisionShape.new()
		var cap= CapsuleShape.new()
		cap.radius = 0.25 * s; cap.height = 4.0 * s
		cs.shape = cap
		sb.translation = Vector3(x, 2.0*s, z)
		sb.add_child(cs)
		sb.set_meta("luo_type","tree")
		add_child(sb)
		objects.append({
			"type":"tree","pos":Vector3(x,0,z),"health":5,
			"drops":[["wood_log",rng.randi_range(2,5)],["stick",rng.randi_range(1,3)]],
			"node":sb
		})

func _make_fallback_tree() -> Spatial:
	var root = Spatial.new()
	var mi  = MeshInstance.new()
	var cyl = CylinderMesh.new()
	cyl.top_radius=0.1; cyl.bottom_radius=0.25; cyl.height=5.0
	mi.mesh = cyl
	var mat = SpatialMaterial.new()
	mat.albedo_color = Color(0.28,0.17,0.07)
	mat.roughness=0.9
	mi.material_override=mat
	root.add_child(mi)
	return root

# ── ROCKS ────────────────────────────────────
func _place_rocks():
	var rock_models = []
	for i in range(4):
		var loaded = load("res://assets/models/rock_%d.glb" % i)
		if loaded: rock_models.append(loaded)

	for i in range(300):
		var x = rng.randf_range(-HALF+3, HALF-3)
		var z = rng.randf_range(-HALF+3, HALF-3)
		if abs(x)<8 and abs(z)<8: continue
		var s = rng.randf_range(0.4, 1.4)

		var mi: Spatial
		if rock_models.size() > 0:
			mi = rock_models[rng.randi() % rock_models.size()].instance()
		else:
			mi = _make_fallback_rock(s)

		mi.translation = Vector3(x, s*0.25, z)
		mi.rotation_degrees.y = rng.randf_range(0,360)
		mi.scale = Vector3(s,s,s)
		add_child(mi)

		var sb = StaticBody.new()
		var cs = CollisionShape.new()
		var sp = SphereShape.new(); sp.radius = s*0.5
		cs.shape=sp; sb.translation=Vector3(x,s*0.25,z)
		sb.add_child(cs); sb.set_meta("luo_type","rock")
		add_child(sb)
		objects.append({
			"type":"rock","pos":Vector3(x,s*0.25,z),"health":3,
			"drops":[["stone",rng.randi_range(1,4)],["flint",rng.randi_range(0,2)]],
			"node":sb
		})

func _make_fallback_rock(s) -> Spatial:
	var root = Spatial.new()
	var mi = MeshInstance.new()
	var sm = SphereMesh.new(); sm.radius=s*0.5; sm.height=s
	mi.mesh=sm
	var mat=SpatialMaterial.new()
	mat.albedo_color=Color(0.42,0.42,0.40); mat.roughness=0.95
	mi.material_override=mat
	root.add_child(mi)
	return root

# ── COLLECTIBLES ─────────────────────────────
func _place_collectibles():
	for i in range(200):
		var x = rng.randf_range(-HALF+2, HALF-2)
		var z = rng.randf_range(-HALF+2, HALF-2)
		if abs(x)<5 and abs(z)<5: continue
		objects.append({
			"type":"item","pos":Vector3(x,0.1,z),
			"item_id":"vine","count":rng.randi_range(1,3),
			"health":1,"drops":[["vine",rng.randi_range(1,3)]],"node":null
		})
	for i in range(80):
		var x=rng.randf_range(-HALF+2,HALF-2); var z=rng.randf_range(-HALF+2,HALF-2)
		objects.append({"type":"item","pos":Vector3(x,0.1,z),"item_id":"fruit",
			"count":rng.randi_range(1,2),"health":1,"drops":[["fruit",1]],"node":null})

# ── ANIMALS ──────────────────────────────────
func _spawn_animals():
	var configs=[["deer",50,30,[["raw_meat",3],["hide",1]]],
		["boar",25,50,[["raw_meat",4],["hide",2]]],
		["rabbit",80,10,[["raw_meat",1]]],["bird",40,5,[["feather",2]]]]
	for cfg in configs:
		for i in range(cfg[1]):
			var x=rng.randf_range(-HALF+10,HALF-10)
			var z=rng.randf_range(-HALF+10,HALF-10)
			if abs(x)<15 and abs(z)<15: continue
			animals.append({"type":"animal","animal_type":cfg[0],"pos":Vector3(x,0,z),
				"health":cfg[2],"drops":cfg[3],"target":Vector3(x,0,z),
				"wander_t":rng.randf_range(3,8),"node":null})

# ── RUNTIME ──────────────────────────────────
func _physics_process(delta):
	for a in animals:
		a.wander_t -= delta
		if a.wander_t <= 0:
			a.target = Vector3(rng.randf_range(-HALF,HALF),0,rng.randf_range(-HALF,HALF))
			a.wander_t = rng.randf_range(5,15)

func nearest_object(player_pos: Vector3, radius: float) -> Dictionary:
	var best={}; var best_d=radius
	for obj in objects:
		var d=player_pos.distance_to(obj.pos)
		if d<best_d: best_d=d; best=obj
	for a in animals:
		var d=player_pos.distance_to(a.pos)
		if d<best_d: best_d=d; best=a
	return best

func destroy_object(obj: Dictionary) -> Array:
	var drops=obj.get("drops",[])
	if obj.get("node") and is_instance_valid(obj.node): obj.node.queue_free()
	var idx=objects.find(obj)
	if idx>=0: objects.remove(idx)
	return drops

func remove_object(obj: Dictionary):
	if obj.get("node") and is_instance_valid(obj.node): obj.node.queue_free()
	var idx=objects.find(obj)
	if idx>=0: objects.remove(idx)
