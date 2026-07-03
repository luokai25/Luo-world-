extends Spatial
# 512x512 procedural jungle world - heightmapped terrain, live animals

const WORLD_SIZE  = 512
const HALF        = 256
const TERRAIN_RES = 129   # grid samples per side

var rng: RandomNumberGenerator
var objects: Array = []
var animals: Array = []
var height_data: PoolRealArray = PoolRealArray()
var player_pos: Vector3 = Vector3.ZERO

func _ready():
	rng = RandomNumberGenerator.new()
	rng.seed = 42
	_generate_heightmap()
	_build_lighting()
	_build_terrain()
	_build_water()
	_place_trees()
	_place_rocks()
	_place_collectibles()
	_spawn_animals()

# ── HEIGHTMAP ────────────────────────────────
func _generate_heightmap():
	var noise = OpenSimplexNoise.new()
	noise.seed        = 42
	noise.octaves     = 4
	noise.period      = 140.0
	noise.persistence = 0.45

	height_data.resize(TERRAIN_RES * TERRAIN_RES)
	for zi in range(TERRAIN_RES):
		for xi in range(TERRAIN_RES):
			var wx = (float(xi) / float(TERRAIN_RES - 1) - 0.5) * WORLD_SIZE
			var wz = (float(zi) / float(TERRAIN_RES - 1) - 0.5) * WORLD_SIZE
			var h  = noise.get_noise_2d(wx, wz) * 9.0
			var dist = sqrt(wx*wx + wz*wz)
			if dist < 16.0:
				h *= clamp(dist / 16.0, 0.0, 1.0)
			height_data[zi * TERRAIN_RES + xi] = h

func _height_at_grid(xi: int, zi: int) -> float:
	xi = clamp(xi, 0, TERRAIN_RES - 1)
	zi = clamp(zi, 0, TERRAIN_RES - 1)
	return height_data[zi * TERRAIN_RES + xi]

func _grid_to_world(xi: int, zi: int) -> Vector3:
	var wx = (float(xi) / float(TERRAIN_RES - 1) - 0.5) * WORLD_SIZE
	var wz = (float(zi) / float(TERRAIN_RES - 1) - 0.5) * WORLD_SIZE
	return Vector3(wx, _height_at_grid(xi, zi), wz)

func get_height(x: float, z: float) -> float:
	var u = (x / WORLD_SIZE + 0.5) * (TERRAIN_RES - 1)
	var v = (z / WORLD_SIZE + 0.5) * (TERRAIN_RES - 1)
	u = clamp(u, 0.0, float(TERRAIN_RES - 1))
	v = clamp(v, 0.0, float(TERRAIN_RES - 1))
	var x0 = int(floor(u)); var x1 = min(x0 + 1, TERRAIN_RES - 1)
	var z0 = int(floor(v)); var z1 = min(z0 + 1, TERRAIN_RES - 1)
	var fx = u - float(x0)
	var fz = v - float(z0)
	var h00 = _height_at_grid(x0, z0)
	var h10 = _height_at_grid(x1, z0)
	var h01 = _height_at_grid(x0, z1)
	var h11 = _height_at_grid(x1, z1)
	var h0 = lerp(h00, h10, fx)
	var h1 = lerp(h01, h11, fx)
	return lerp(h0, h1, fz)

# ── LIGHTING ─────────────────────────────────
func _build_lighting():
	var sun = DirectionalLight.new()
	sun.name = "Sun"
	sun.rotation_degrees  = Vector3(-52, 30, 0)
	sun.light_color       = Color(1.0, 0.97, 0.86)
	sun.light_energy      = 1.3
	sun.shadow_enabled    = true
	sun.shadow_bias       = 0.1
	add_child(sun)

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
	env.tonemap_mode          = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure      = 1.1
	env_node.environment      = env
	add_child(env_node)

# ── TERRAIN (heightmapped) ────────────────────
func _build_terrain():
	var st = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for zi in range(TERRAIN_RES - 1):
		for xi in range(TERRAIN_RES - 1):
			var p00 = _grid_to_world(xi,   zi)
			var p10 = _grid_to_world(xi+1, zi)
			var p01 = _grid_to_world(xi,   zi+1)
			var p11 = _grid_to_world(xi+1, zi+1)
			_add_tri(st, p00, p10, p01)
			_add_tri(st, p10, p11, p01)
	st.generate_normals()
	var mesh = st.commit()

	var mi = MeshInstance.new()
	mi.name = "Terrain"
	mi.mesh = mesh
	var mat = SpatialMaterial.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.95
	mi.material_override = mat
	add_child(mi)

	_build_terrain_collision()

func _add_tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3):
	st.add_color(_height_color(a.y)); st.add_vertex(a)
	st.add_color(_height_color(b.y)); st.add_vertex(b)
	st.add_color(_height_color(c.y)); st.add_vertex(c)

func _height_color(h: float) -> Color:
	if h < 0.3:   return Color(0.16, 0.40, 0.13)
	elif h < 3.0: return Color(0.14, 0.33, 0.11)
	elif h < 6.0: return Color(0.30, 0.32, 0.16)
	else:         return Color(0.42, 0.38, 0.30)

func _build_terrain_collision():
	var shape = HeightMapShape.new()
	shape.map_width = TERRAIN_RES
	shape.map_depth = TERRAIN_RES
	shape.map_data  = height_data

	var sb = StaticBody.new()
	var cs = CollisionShape.new()
	cs.shape = shape
	sb.add_child(cs)
	var scale_factor = WORLD_SIZE / float(TERRAIN_RES - 1)
	sb.scale = Vector3(scale_factor, 1.0, scale_factor)
	add_child(sb)

# ── WATER ────────────────────────────────────
func _build_water():
	for i in range(40):
		var t = float(i) / 40.0
		var x = sin(t * PI * 2) * 80.0 - 20.0
		var z = t * WORLD_SIZE - HALF
		_add_water_plane(x, z, Vector2(6, 6))

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
	mat.albedo_color      = Color(0.10, 0.35, 0.72, 0.82)
	mat.flags_transparent = true
	mat.roughness         = 0.05
	mat.metallic          = 0.3
	mi.material_override  = mat
	var y = max(0.3, get_height(x, z) + 0.1)
	mi.translation       = Vector3(x, y, z)
	mi.rotation_degrees  = Vector3(-90, 0, 0)
	add_child(mi)

# ── TREES ────────────────────────────────────
func _place_trees():
	var tree_models = []
	for i in range(6):
		var loaded = load("res://assets/models/tree_%d.glb" % i)
		if loaded: tree_models.append(loaded)

	for i in range(600):
		var x = rng.randf_range(-HALF+5, HALF-5)
		var z = rng.randf_range(-HALF+5, HALF-5)
		if abs(x)<12 and abs(z)<12: continue
		var y = get_height(x, z)

		var mi: Spatial
		if tree_models.size() > 0:
			mi = tree_models[rng.randi() % tree_models.size()].instance()
		else:
			mi = _make_fallback_tree()

		mi.translation = Vector3(x, y, z)
		mi.rotation_degrees.y = rng.randf_range(0, 360)
		var s = rng.randf_range(0.8, 2.0)
		mi.scale = Vector3(s, s, s)
		add_child(mi)

		var sb = StaticBody.new()
		var cs = CollisionShape.new()
		var cap= CapsuleShape.new()
		cap.radius = 0.25 * s; cap.height = 4.0 * s
		cs.shape = cap
		sb.translation = Vector3(x, y + 2.0*s, z)
		sb.add_child(cs)
		sb.set_meta("luo_type","tree")
		add_child(sb)
		objects.append({
			"type":"tree","pos":Vector3(x,y,z),"health":5,
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
		var y = get_height(x, z)
		var s = rng.randf_range(0.4, 1.4)

		var mi: Spatial
		if rock_models.size() > 0:
			mi = rock_models[rng.randi() % rock_models.size()].instance()
		else:
			mi = _make_fallback_rock(s)

		mi.translation = Vector3(x, y + s*0.25, z)
		mi.rotation_degrees.y = rng.randf_range(0,360)
		mi.scale = Vector3(s,s,s)
		add_child(mi)

		var sb = StaticBody.new()
		var cs = CollisionShape.new()
		var sp = SphereShape.new(); sp.radius = s*0.5
		cs.shape=sp; sb.translation=Vector3(x, y + s*0.25, z)
		sb.add_child(cs); sb.set_meta("luo_type","rock")
		add_child(sb)
		objects.append({
			"type":"rock","pos":Vector3(x,y+s*0.25,z),"health":3,
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
		var y = get_height(x, z)
		objects.append({
			"type":"item","pos":Vector3(x,y+0.1,z),
			"item_id":"vine","count":rng.randi_range(1,3),
			"health":1,"drops":[["vine",rng.randi_range(1,3)]],"node":null
		})
	for i in range(80):
		var x=rng.randf_range(-HALF+2,HALF-2); var z=rng.randf_range(-HALF+2,HALF-2)
		var y = get_height(x, z)
		objects.append({"type":"item","pos":Vector3(x,y+0.1,z),"item_id":"fruit",
			"count":rng.randi_range(1,2),"health":1,"drops":[["fruit",1]],"node":null})

# ── ANIMALS ──────────────────────────────────
var animal_models: Dictionary = {}

func _spawn_animals():
	for key in ["deer","boar","rabbit","bird"]:
		var res = load("res://assets/models/%s.glb" % key)
		if res: animal_models[key] = res

	var configs=[["deer",50,30,[["raw_meat",3],["hide",1]],5.5,9.0],
		["boar",25,50,[["raw_meat",4],["hide",2]],4.5,6.0],
		["rabbit",80,10,[["raw_meat",1]],7.5,14.0],
		["bird",40,5,[["feather",2]],9.0,18.0]]

	for cfg in configs:
		var atype = cfg[0]
		for i in range(cfg[1]):
			var x=rng.randf_range(-HALF+10,HALF-10)
			var z=rng.randf_range(-HALF+10,HALF-10)
			if abs(x)<15 and abs(z)<15: continue
			var y = get_height(x,z)

			var node = null
			if animal_models.has(atype):
				node = animal_models[atype].instance()
				node.translation = Vector3(x,y,z)
				node.rotation_degrees.y = rng.randf_range(0,360)
				add_child(node)

			animals.append({
				"type":"animal","animal_type":atype,"pos":Vector3(x,y,z),
				"health":cfg[2],"drops":cfg[3],"target":Vector3(x,y,z),
				"wander_t":rng.randf_range(3,8),
				"speed":cfg[4],"flee_range":cfg[5],
				"node":node
			})

# ── RUNTIME ──────────────────────────────────
func _physics_process(delta):
	for a in animals:
		var to_player = a.pos - player_pos
		to_player.y = 0
		var dist = to_player.length()

		if dist < a.flee_range and dist > 0.01:
			var dir = to_player.normalized()
			a.pos += dir * a.speed * 1.4 * delta
		else:
			a.wander_t -= delta
			if a.wander_t <= 0:
				var tx = clamp(a.pos.x + rng.randf_range(-15,15), -HALF+5, HALF-5)
				var tz = clamp(a.pos.z + rng.randf_range(-15,15), -HALF+5, HALF-5)
				a.target = Vector3(tx, 0, tz)
				a.wander_t = rng.randf_range(4,10)
			var to_target = a.target - a.pos
			to_target.y = 0
			if to_target.length() > 0.5:
				a.pos += to_target.normalized() * a.speed * 0.4 * delta

		a.pos.y = get_height(a.pos.x, a.pos.z)
		if a.node and is_instance_valid(a.node):
			a.node.translation = a.pos
			var look_dir = to_player if dist < a.flee_range else (a.target - a.pos)
			if look_dir.length() > 0.1:
				a.node.rotation.y = atan2(look_dir.x, look_dir.z) + PI

func nearest_object(p_pos: Vector3, radius: float) -> Dictionary:
	var best={}; var best_d=radius
	for obj in objects:
		var d=p_pos.distance_to(obj.pos)
		if d<best_d: best_d=d; best=obj
	for a in animals:
		var d=p_pos.distance_to(a.pos)
		if d<best_d: best_d=d; best=a
	return best

func destroy_object(obj: Dictionary) -> Array:
	var drops = obj.get("drops", [])
	if obj.get("node") and is_instance_valid(obj.node):
		obj.node.queue_free()
	var idx = objects.find(obj)
	if idx >= 0:
		objects.remove(idx)
	else:
		idx = animals.find(obj)
		if idx >= 0:
			animals.remove(idx)
	return drops

func remove_object(obj: Dictionary):
	if obj.get("node") and is_instance_valid(obj.node):
		obj.node.queue_free()
	var idx = objects.find(obj)
	if idx >= 0:
		objects.remove(idx)
	else:
		idx = animals.find(obj)
		if idx >= 0:
			animals.remove(idx)
