"""
GameState - Platform-agnostic game logic
Handles: player, world, crafting, interactions, time
"""

import math
import random
from game.inventory import Inventory, ITEMS
from game.android_player import AndroidPlayer
from game.android_world import AndroidWorld


class GameState:
    def __init__(self, seed=42):
        self.seed      = seed
        self.rng       = random.Random(seed)
        self.player    = AndroidPlayer()
        self.inventory = Inventory(player=self.player)
        self.world     = AndroidWorld(seed=seed)

        self.time_of_day  = 10.0
        self.day_number   = 1
        self.day_speed    = 0.5

        self.interact_prompt = ''
        self._nearest        = None
        self._running        = False

        # Notifications
        self.notifications   = []   # [(text, timer)]
        self._notif_duration = 3.0

    def start(self):
        self.inventory.give_starting_items()
        self._running = True
        self.notify("🌿 Welcome to Luo World")
        self.notify("You wake up in the jungle...")

    def notify(self, text):
        self.notifications.append([text, self._notif_duration])

    def update(self, dt, move_x=0, move_z=0, cam_x=0, cam_y=0):
        if not self._running:
            return

        # Time
        self.time_of_day += dt * self.day_speed / 60.0
        if self.time_of_day >= 24.0:
            self.time_of_day = 0.0
            self.day_number  += 1
            self.notify(f"🌅 Day {self.day_number}")

        # Night warning
        h = int(self.time_of_day)
        if h == 20:
            self.notify("🌙 Night is falling...")

        # Player
        running = abs(move_x) + abs(move_z) > 0.8
        self.player.move(move_x, move_z, dt,
                         get_height=self.world.get_height,
                         running=running)
        self.player.rotate_camera(cam_x, cam_y, dt)
        self.player.update_stats(dt)

        # World - pass player position for animal AI
        self.world.set_player_pos(self.player.x, self.player.z)
        self.world.update(dt)

        # Interaction
        self._nearest = self.world.nearest_object(
            self.player.x, self.player.z, radius=3.5)
        self.interact_prompt = self._get_prompt()

        # Notifications decay
        self.notifications = [
            [t, timer - dt] for t, timer in self.notifications
        ]
        self.notifications = [
            n for n in self.notifications if n[1] > 0
        ]

        # Stat warnings
        if int(self.player.hunger) == 20:
            self.notify("🍖 You are hungry!")
        if int(self.player.thirst) == 20:
            self.notify("💧 You are thirsty!")

    def _get_prompt(self):
        if not self._nearest:
            return ''
        t = self._nearest.get('type', '')
        if t == 'tree':
            return '[⚔] Chop Tree    [E] Inspect'
        elif t == 'rock':
            return '[⚔] Mine Rock    [E] Inspect'
        elif t == 'animal':
            atype = self._nearest.get('animal_type', 'animal')
            return f'[⚔] Hunt {atype.capitalize()}'
        elif t == 'water_source':
            return '[E] Fill cup with water'
        elif t == 'bush':
            return '[E] Pick berries'
        elif t == 'item':
            name = ITEMS.get(self._nearest.get('item_id', ''), {}).get('name', 'item')
            return f'[E] Pick up {name}'
        return ''

    def player_attack(self):
        equipped = self.inventory.equipped
        damage = 5
        if equipped:
            damage = ITEMS.get(equipped.item_id, {}).get('damage', 5)

        target = self._nearest
        if not target:
            return

        t = target.get('type', '')

        # Damage target
        ref = target.get('_ref')
        if ref:
            ref.health -= damage
            if ref.health <= 0:
                drops, pos = self.world.destroy_object(target)
                for item_id, count in drops:
                    self.inventory.add_item(item_id, count)
                    item_name = ITEMS.get(item_id, {}).get('name', item_id)
                    self.notify(f"Got {count}x {item_name}")

        # Durability loss
        if equipped and equipped.durability is not None:
            equipped.durability -= 1
            if equipped.durability <= 0:
                item_name = ITEMS.get(equipped.item_id, {}).get('name', '')
                self.inventory.remove_item(equipped.item_id, 1)
                self.notify(f"⚠️ {item_name} broke!")

    def player_interact(self):
        target = self._nearest
        if not target:
            return

        t = target.get('type', '')

        if t == 'item' or t == 'bush':
            item_id = target.get('item_id')
            drops   = target.get('drops', [])
            if drops:
                for did, dcount in drops:
                    self.inventory.add_item(did, dcount)
                    name = ITEMS.get(did, {}).get('name', did)
                    self.notify(f"Picked up {dcount}x {name}")
            elif item_id:
                self.inventory.add_item(item_id, target.get('count', 1))
                name = ITEMS.get(item_id, {}).get('name', item_id)
                self.notify(f"Picked up {name}")
            self.world.remove_object(target)

        elif t == 'water_source':
            # Fill empty cup if player has one
            if self.inventory.count_item('wooden_cup_empty') > 0:
                self.inventory.remove_item('wooden_cup_empty', 1)
                self.inventory.add_item('wooden_cup', 1)
                self.notify("💧 Filled wooden cup with water")
            else:
                self.notify("Need an empty wooden cup to fill")

    def use_item(self):
        slot = self.inventory.slots[self.inventory.equipped_slot]
        if slot.empty:
            self.notify("Nothing equipped")
            return
        item_data = ITEMS.get(slot.item_id, {})
        cat = item_data.get('category', '')

        if cat == 'food':
            nutrition = item_data.get('nutrition', 0)
            hydration = item_data.get('hydration', 0)
            self.player.eat(nutrition)
            self.player.drink(hydration)
            becomes = item_data.get('becomes')
            self.inventory.remove_item(slot.item_id, 1)
            if becomes:
                self.inventory.add_item(becomes, 1)
            self.notify(f"Ate {item_data['name']} (+{nutrition} hunger)")

        elif cat == 'drink':
            hydration = item_data.get('hydration', 0)
            self.player.drink(hydration)
            becomes = item_data.get('becomes')
            self.inventory.remove_item(slot.item_id, 1)
            if becomes:
                self.inventory.add_item(becomes, 1)
            self.notify(f"Drank {item_data['name']} (+{hydration} thirst)")
        else:
            self.notify(f"Can't use {item_data.get('name','that')} directly")

    def toggle_inventory(self):
        self.inventory.is_open = not self.inventory.is_open

    def try_craft(self, recipe_id):
        success = self.inventory.craft(recipe_id)
        if success:
            from game.inventory import RECIPES
            recipe = RECIPES[recipe_id]
            name = recipe['output'][0]
            self.notify(f"✅ Crafted {name}")
        else:
            self.notify("❌ Missing materials")
        return success

    @property
    def time_str(self):
        h = int(self.time_of_day)
        m = int((self.time_of_day - h) * 60)
        if h < 6 or h >= 20:
            icon = '🌙'
        elif h < 8 or h >= 18:
            icon = '🌅'
        else:
            icon = '☀️'
        return f'Day {self.day_number}  {h:02d}:{m:02d} {icon}'

    @property
    def current_notification(self):
        if self.notifications:
            return self.notifications[-1][0]
        return ''
