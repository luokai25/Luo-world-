"""
GameState - Platform-agnostic game logic v0.3
Session 4: Campfire + Weather + Temperature + Animals
"""

import math
import random
from game.inventory import Inventory, ITEMS, RECIPES
from game.android_player import AndroidPlayer
from game.android_world import AndroidWorld
from game.campfire import CampfireManager
from game.weather import Weather
from game.temperature import Temperature


class GameState:
    def __init__(self, seed=42):
        self.seed        = seed
        self.rng         = random.Random(seed)

        self.player      = AndroidPlayer()
        self.inventory   = Inventory(player=self.player)
        self.world       = AndroidWorld(seed=seed)
        self.campfires   = CampfireManager()
        self.weather     = Weather(seed=seed)
        self.temperature = Temperature()

        self.time_of_day  = 10.0
        self.day_number   = 1
        self.day_speed    = 0.5

        self.interact_prompt = ''
        self._nearest        = None
        self._running        = False

        self.notifications   = []
        self._notif_duration = 3.5
        self._last_notifs    = set()   # prevent spam

    def start(self):
        self.inventory.give_starting_items()
        self._running = True
        self.notify("🌿 Welcome to Luo World")
        self.notify("You wake up deep in the jungle...")

    def notify(self, text, dedupe=True):
        if dedupe and text in self._last_notifs:
            return
        self.notifications.append([text, self._notif_duration])
        self._last_notifs.add(text)
        if len(self._last_notifs) > 20:
            self._last_notifs.pop()

    def update(self, dt, move_x=0, move_z=0, cam_x=0, cam_y=0):
        if not self._running:
            return

        # Time of day
        self.time_of_day += dt * self.day_speed / 60.0
        if self.time_of_day >= 24.0:
            self.time_of_day = 0.0
            self.day_number += 1
            self._last_notifs.clear()
            self.notify(f"🌅 Day {self.day_number}")

        h = int(self.time_of_day)
        if h == 20: self.notify("🌙 Night is falling — find shelter")
        if h == 6:  self.notify("🌅 A new dawn")

        # Weather
        self.weather.update(dt, self.time_of_day)

        # Player movement with weather penalty
        speed_mult = self.weather.move_penalty
        running    = (abs(move_x) + abs(move_z)) > 0.8
        self.player.move(move_x * speed_mult, move_z * speed_mult, dt,
                         get_height=self.world.get_height,
                         running=running)
        self.player.rotate_camera(cam_x, cam_y, dt)
        self.player.update_stats(dt)

        # World
        self.world.set_player_pos(self.player.x, self.player.z)
        self.world.update(dt)

        # Campfires
        cf_events = self.campfires.update(dt)
        for event in cf_events:
            if event[0] == 'fire_out':
                self.notify("🔥 Your campfire burned out")
            elif event[0] == 'cooked':
                _, cf, slot_idx, item_id = event
                result = cf.take_cooked(slot_idx)
                if result:
                    self.inventory.add_item(result, 1)
                    self.notify(f"✅ {ITEMS.get(result,{}).get('name', result)} is ready!")

        # Rain extinguishes fires
        if self.weather.extinguishes_fire:
            for cf in self.campfires.campfires:
                if cf.lit and self.rng.random() < 0.001 * dt:
                    cf.extinguish()
                    self.notify("🌧  Rain put out your campfire!")

        # Temperature
        campfire_warmth = self.campfires.warmth_at(self.player.x, self.player.z)
        has_armor = self.inventory.count_item('leather_armor') > 0
        temp_effects = self.temperature.update(
            dt, self.time_of_day, self.weather, campfire_warmth, has_armor)

        for effect in temp_effects:
            if effect[0] == 'health_drain':
                self.player.health = max(0, self.player.health - effect[1])
            elif effect[0] == 'stamina_drain':
                self.player.stamina = max(0, self.player.stamina - effect[1])
            elif effect[0] == 'health_regen':
                self.player.health = min(self.player.max_health,
                                         self.player.health + effect[1])
            elif effect[0] == 'notify':
                self.notify(effect[1])

        # Stat warnings
        if int(self.player.hunger) == 20:
            self.notify("🍖 Very hungry!", dedupe=False)
        if int(self.player.thirst) == 20:
            self.notify("💧 Very thirsty!", dedupe=False)

        # Interaction check
        self._nearest = self.world.nearest_object(
            self.player.x, self.player.z, radius=3.5)

        # Also check campfires
        nearest_cf = self.campfires.nearest(
            self.player.x, self.player.z, radius=4.0)
        if nearest_cf and (
            self._nearest is None or
            math.sqrt((nearest_cf.x-self.player.x)**2 +
                      (nearest_cf.z-self.player.z)**2) <
            math.sqrt((self._nearest['x']-self.player.x)**2 +
                      (self._nearest['z']-self.player.z)**2)
        ):
            self._nearest = nearest_cf.to_dict()

        self.interact_prompt = self._get_prompt()

        # Notifications decay
        self.notifications = [
            [t, timer-dt] for t, timer in self.notifications
            if timer - dt > 0
        ]

    def _get_prompt(self):
        n = self._nearest
        if not n:
            return ''
        t = n.get('type', '')
        if t == 'tree':         return '[⚔] Chop Tree'
        if t == 'rock':         return '[⚔] Mine Rock'
        if t == 'animal':
            atype = n.get('animal_type', 'animal')
            hp    = n.get('health', '?')
            return f'[⚔] Hunt {atype.capitalize()}  HP:{hp}'
        if t == 'water_source': return '[E] Fill cup with water'
        if t == 'bush':         return '[E] Pick berries'
        if t == 'campfire':
            cf = n.get('_ref')
            if cf:
                fuel = f"{int(cf.fuel_pct*100)}% fuel"
                status = '🔥 Lit' if cf.lit else '⬜ Unlit'
                return f'[E] Campfire ({status}, {fuel})  [C] Cook'
            return '[E] Campfire'
        if t == 'item':
            name = ITEMS.get(n.get('item_id',''),{}).get('name','item')
            return f'[E] Pick up {name}'
        return ''

    def player_attack(self):
        equipped  = self.inventory.equipped
        damage    = 5
        if equipped:
            damage = ITEMS.get(equipped.item_id, {}).get('damage', 5)

        target = self._nearest
        if not target:
            return

        ref = target.get('_ref')
        if ref and hasattr(ref, 'health'):
            ref.health -= damage
            if ref.health <= 0:
                drops, pos = self.world.destroy_object(target)
                for item_id, count in drops:
                    self.inventory.add_item(item_id, count)
                    name = ITEMS.get(item_id,{}).get('name', item_id)
                    self.notify(f"Got {count}x {name}")

        # Durability
        if equipped and equipped.durability is not None:
            equipped.durability -= 1
            if equipped.durability <= 0:
                name = ITEMS.get(equipped.item_id,{}).get('name','')
                self.inventory.remove_item(equipped.item_id, 1)
                self.notify(f"⚠️  {name} broke!")

    def player_interact(self):
        target = self._nearest
        if not target:
            return

        t = target.get('type', '')

        if t in ('item', 'bush'):
            drops   = target.get('drops', [])
            item_id = target.get('item_id')
            if drops:
                for did, dcount in drops:
                    self.inventory.add_item(did, dcount)
                    name = ITEMS.get(did,{}).get('name', did)
                    self.notify(f"Picked up {dcount}x {name}")
            elif item_id:
                self.inventory.add_item(item_id, target.get('count', 1))
                name = ITEMS.get(item_id,{}).get('name', item_id)
                self.notify(f"Picked up {name}")
            self.world.remove_object(target)

        elif t == 'water_source':
            if self.inventory.count_item('wooden_cup_empty') > 0:
                self.inventory.remove_item('wooden_cup_empty', 1)
                self.inventory.add_item('wooden_cup', 1)
                self.notify("💧 Filled wooden cup")
            else:
                self.notify("Need an empty wooden cup")

        elif t == 'campfire':
            cf = target.get('_ref')
            if cf:
                if not cf.lit:
                    if self.inventory.count_item('flint') > 0:
                        cf.light()
                        self.notify("🔥 Campfire lit!")
                    else:
                        self.notify("Need flint to light fire")
                else:
                    # Add fuel
                    if self.inventory.count_item('wood_log') > 0:
                        self.inventory.remove_item('wood_log', 1)
                        cf.add_fuel(120.0)
                        self.notify("🪵 Added wood to fire")
                    else:
                        self.notify(f"🔥 Burning — {int(cf.fuel_pct*100)}% fuel")

    def place_campfire(self):
        """Place campfire at player position if they have materials"""
        needed = {'wood_log': 3, 'stick': 2, 'flint': 1}
        if not self.inventory.has_items(needed):
            missing = [
                f"{ITEMS.get(k,{}).get('name',k)}"
                for k, v in needed.items()
                if self.inventory.count_item(k) < v
            ]
            self.notify(f"Need: {', '.join(missing)}")
            return False
        for k, v in needed.items():
            self.inventory.remove_item(k, v)
        cf = self.campfires.place(
            self.player.x, self.player.y - 0.8, self.player.z)
        self.notify("🔥 Campfire placed and lit!")
        return True

    def cook_on_fire(self, item_id):
        """Put item on nearest campfire to cook"""
        cf = self.campfires.nearest(self.player.x, self.player.z, radius=4.0)
        if not cf:
            self.notify("No campfire nearby")
            return False
        if not cf.lit:
            self.notify("Campfire is not lit")
            return False
        if self.inventory.count_item(item_id) < 1:
            name = ITEMS.get(item_id,{}).get('name', item_id)
            self.notify(f"No {name} to cook")
            return False

        # Find empty slot
        for i in range(2):
            if cf.cooking_slots[i] is None:
                ok, msg = cf.cook(i, item_id)
                if ok:
                    self.inventory.remove_item(item_id, 1)
                    name = ITEMS.get(item_id,{}).get('name', item_id)
                    self.notify(f"🔥 Cooking {name}...")
                    return True
                else:
                    self.notify(msg)
                    return False
        self.notify("Campfire cooking slots full")
        return False

    def use_item(self):
        slot = self.inventory.slots[self.inventory.equipped_slot]
        if slot.empty:
            return
        item_data = ITEMS.get(slot.item_id, {})
        cat = item_data.get('category', '')

        if cat == 'food':
            self.player.eat(item_data.get('nutrition', 0))
            self.player.drink(item_data.get('hydration', 0))
            becomes = item_data.get('becomes')
            self.inventory.remove_item(slot.item_id, 1)
            if becomes:
                self.inventory.add_item(becomes, 1)
            self.notify(f"Ate {item_data['name']} (+{item_data.get('nutrition',0)} hunger)")

        elif cat == 'drink':
            self.player.drink(item_data.get('hydration', 0))
            becomes = item_data.get('becomes')
            self.inventory.remove_item(slot.item_id, 1)
            if becomes:
                self.inventory.add_item(becomes, 1)
            self.notify(f"Drank {item_data['name']} (+{item_data.get('hydration',0)} thirst)")
        else:
            self.notify(f"Can't use {item_data.get('name','that')} directly")

    def toggle_inventory(self):
        self.inventory.is_open = not self.inventory.is_open

    def try_craft(self, recipe_id):
        success = self.inventory.craft(recipe_id)
        if success:
            recipe = RECIPES[recipe_id]
            out_id = recipe['output'][0]
            name   = ITEMS.get(out_id, {}).get('name', out_id)
            self.notify(f"✅ Crafted {name}")
        else:
            self.notify("❌ Missing materials")
        return success

    @property
    def time_str(self):
        h = int(self.time_of_day)
        m = int((self.time_of_day - h) * 60)
        if h < 6 or h >= 20:   icon = '🌙'
        elif h < 8 or h >= 18: icon = '🌅'
        else:                   icon = '☀️'
        return f"Day {self.day_number}  {h:02d}:{m:02d} {icon}"

    @property
    def weather_str(self):
        return self.weather.description

    @property
    def temp_str(self):
        return self.temperature.display

    @property
    def current_notification(self):
        if self.notifications:
            return self.notifications[-1][0]
        return ''
