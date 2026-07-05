extends Node
# SaveManager - persistent cloud save via Supabase
# Uses anonymous auth so there's no login screen - each install gets its own
# save automatically, tied to a token stored locally on the device.

const SUPABASE_URL = "https://dcjgqjuqbrlnoeokfiqd.supabase.co"
const SUPABASE_ANON_KEY = "sb_publishable_weDYBbaPRsidGZbRsGYLag_nx2_-wxS"
const CREDENTIALS_PATH = "user://supabase_credentials.cfg"
const AUTOSAVE_INTERVAL = 60.0   # seconds

var access_token: String = ""
var refresh_token: String = ""
var user_id: String = ""
var is_authenticated: bool = false
var last_save_ok: bool = true

var _http_auth: HTTPRequest
var _http_save: HTTPRequest
var _http_load: HTTPRequest
var _autosave_timer: float = 0.0
var _pending_retry_save: bool = false
var _pending_retry_load: bool = false

signal save_completed(success)
signal load_completed(success, data)
signal auth_ready()

func _ready():
	_http_auth = HTTPRequest.new(); add_child(_http_auth)
	_http_save = HTTPRequest.new(); add_child(_http_save)
	_http_load = HTTPRequest.new(); add_child(_http_load)

	_http_auth.connect("request_completed", self, "_on_auth_completed")
	_http_save.connect("request_completed", self, "_on_save_completed")
	_http_load.connect("request_completed", self, "_on_load_completed")

	_load_local_credentials()
	if access_token == "":
		_sign_in_anonymously()
	else:
		is_authenticated = true
		emit_signal("auth_ready")

func _process(delta):
	if not is_authenticated:
		return
	_autosave_timer += delta
	if _autosave_timer >= AUTOSAVE_INTERVAL:
		_autosave_timer = 0.0
		save_game()

# ── LOCAL CREDENTIAL STORAGE ──────────────────
func _load_local_credentials():
	var cfg = ConfigFile.new()
	if cfg.load(CREDENTIALS_PATH) == OK:
		access_token  = cfg.get_value("auth", "access_token", "")
		refresh_token = cfg.get_value("auth", "refresh_token", "")
		user_id       = cfg.get_value("auth", "user_id", "")

func _save_local_credentials():
	var cfg = ConfigFile.new()
	cfg.set_value("auth", "access_token", access_token)
	cfg.set_value("auth", "refresh_token", refresh_token)
	cfg.set_value("auth", "user_id", user_id)
	cfg.save(CREDENTIALS_PATH)

# ── ANONYMOUS SIGN-IN ──────────────────────────
func _sign_in_anonymously():
	var headers = [
		"apikey: " + SUPABASE_ANON_KEY,
		"Content-Type: application/json",
	]
	var url = SUPABASE_URL + "/auth/v1/signup"
	_http_auth.request(url, headers, true, HTTPClient.METHOD_POST, "{}")

func _on_auth_completed(result, code, headers, body):
	if code != 200 and code != 201:
		var msg = body.get_string_from_utf8()
		print("Supabase auth failed (", code, "): ", msg)
		GameState.notify("⚠️ Cloud save unavailable (offline mode)")
		return

	var json = JSON.parse(body.get_string_from_utf8())
	if json.error:
		return
	var data = json.result
	access_token  = data.get("access_token", "")
	refresh_token = data.get("refresh_token", "")
	var user = data.get("user", {})
	user_id = user.get("id", "")

	if access_token != "" and user_id != "":
		_save_local_credentials()
		is_authenticated = true
		emit_signal("auth_ready")
		load_game()

func _refresh_session():
	if refresh_token == "":
		_sign_in_anonymously()
		return
	var headers = [
		"apikey: " + SUPABASE_ANON_KEY,
		"Content-Type: application/json",
	]
	var url = SUPABASE_URL + "/auth/v1/token?grant_type=refresh_token"
	var body = JSON.print({"refresh_token": refresh_token})
	_http_auth.request(url, headers, true, HTTPClient.METHOD_POST, body)

# ── SAVE ───────────────────────────────────────
func save_game():
	if not is_authenticated or user_id == "":
		return

	var p = GameState
	var inv = []
	for slot in p.slots:
		inv.append({"item_id": slot.item_id, "count": slot.count, "durability": slot.durability})

	var payload = {
		"user_id": user_id,
		"player_x": 0.0, "player_y": 4.0, "player_z": 0.0,
		"health": p.health, "hunger": p.hunger, "thirst": p.thirst, "stamina": p.stamina,
		"day_number": p.day_number, "time_of_day": p.time_of_day,
		"inventory": inv, "equipped_slot": p.equipped_slot,
	}

	var headers = [
		"apikey: " + SUPABASE_ANON_KEY,
		"Authorization: Bearer " + access_token,
		"Content-Type: application/json",
		"Prefer: resolution=merge-duplicates",
	]
	var url = SUPABASE_URL + "/rest/v1/player_saves"
	_http_save.request(url, headers, true, HTTPClient.METHOD_POST, JSON.print(payload))

func _on_save_completed(result, code, headers, body):
	if code == 401 and not _pending_retry_save:
		_pending_retry_save = true
		_refresh_session()
		return
	_pending_retry_save = false
	last_save_ok = (code == 200 or code == 201)
	emit_signal("save_completed", last_save_ok)

# ── LOAD ───────────────────────────────────────
func load_game():
	if not is_authenticated:
		return
	var headers = [
		"apikey: " + SUPABASE_ANON_KEY,
		"Authorization: Bearer " + access_token,
	]
	var url = SUPABASE_URL + "/rest/v1/player_saves?select=*"
	_http_load.request(url, headers, true, HTTPClient.METHOD_GET)

func _on_load_completed(result, code, headers, body):
	if code == 401 and not _pending_retry_load:
		_pending_retry_load = true
		_refresh_session()
		return
	_pending_retry_load = false

	if code != 200:
		emit_signal("load_completed", false, {})
		return

	var json = JSON.parse(body.get_string_from_utf8())
	if json.error:
		emit_signal("load_completed", false, {})
		return

	var rows = json.result
	if rows.size() == 0:
		emit_signal("load_completed", false, {})   # first ever launch, no save yet
		return

	var save = rows[0]
	GameState.health   = save.get("health", 100.0)
	GameState.hunger   = save.get("hunger", 100.0)
	GameState.thirst   = save.get("thirst", 100.0)
	GameState.stamina  = save.get("stamina", 100.0)
	GameState.day_number  = save.get("day_number", 1)
	GameState.time_of_day = save.get("time_of_day", 10.0)
	GameState.equipped_slot = save.get("equipped_slot", 0)

	var inv = save.get("inventory", [])
	for i in range(min(inv.size(), GameState.SLOT_COUNT)):
		var s = inv[i]
		GameState.slots[i] = {
			"item_id": s.get("item_id", ""),
			"count": s.get("count", 0),
			"durability": s.get("durability", -1),
		}
	GameState.emit_signal("inventory_changed")
	GameState.emit_signal("stats_changed")
	GameState.notify("☁️ Save loaded")
	emit_signal("load_completed", true, save)
