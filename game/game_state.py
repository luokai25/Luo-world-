"""
GameState - Platform-agnostic game logic
Used by both Kivy (Android) and Ursina (Desktop) frontends
Handles: player simulation, world state, time, interactions
"""

import math
import random
from game.inventory import Inventory, ITEMS
from game.android_player import AndroidPlayer
from game.android_world import AndroidWorld


class GameState:
    def __init__(self, seed=42):
        self.seed = seed
        self.rng = random.Random(seed)

        self.player = AndroidPlayer()
        self.inventory = Inventory(player=self.player)
        self.world = AndroidWorld(seed=seed)

        self.time_of_day = 10.0      # 10 AM
        self.day_number  = 1
        self.day_speed   = 0.5       # game minutes per real second
        self.interact_prompt = ''
        self._running = False

    def start(self):
        self.inventory.give_starting_items()
        self._running = True

    def update(self, dt, move_x=0, move_z=0, cam_x=0, cam_y=0):
        if not self._running:
            return

        # Advance time
        self.time_of_day += dt * self.day_speed / 60.0
        if self.time_of_day >= 24.0:
            self.time_of_day = 0.0
            self.day_number += 1

        # Player movement
        self.player.move(move_x, move_z, dt,
                         get_height=self.world.get_height)
        self.player.rotate_camera(cam_x, cam_y, dt)
        self.player.update_stats(dt)

        # Interaction check
        self.interact_prompt = self._check_interact()

        # World update
        self.world.update(dt)

    def _check_interact(self):
        """Check if player is near something interactable"""
        px, py, pz = self.player.x, self.player.y, self.player.z
        nearest = self.world.nearest_object(px, pz, radius=3.0)
        if nearest:
            obj_type = nearest.get('type', '')
            if obj_type == 'tree':
                return '[E] Chop Tree   [⚔] Attack'
            elif obj_type == 'rock':
                return '[E] Mine Rock'
            elif obj_type == 'item':
                name = ITEMS.get(nearest.get('item_id',''),{}).get('name','Item')
                return f'[E] Pick up {name}'
        return ''

    def player_attack(self):
        """Player swings equipped item"""
        equipped = self.inventory.equipped
        if not equipped:
            return
        item_data = ITEMS.get(equipped.item_id, {})
        damage = item_data.get('damage', 5)

        px, py, pz = self.player.x, self.player.y, self.player.z
        target = self.world.nearest_object(px, pz, radius=self.player.reach)
        if target:
            target['health'] = target.get('health', 3) - damage
            if target['health'] <= 0:
                drops, pos = self.world.destroy_object(target)
                for item_id, count in drops:
                    self.inventory.add_item(item_id, count)
                    print(f"Got {count}x {item_id}")

        # Durability
        if equipped.durability is not None:
            equipped.durability -= 1
            if equipped.durability <= 0:
                self.inventory.remove_item(equipped.item_id, 1)

    def player_interact(self):
        """E button - pick up / interact"""
        px, py, pz = self.player.x, self.player.y, self.player.z
        target = self.world.nearest_object(px, pz, radius=self.player.reach)
        if target:
            obj_type = target.get('type', '')
            if obj_type == 'item':
                self.inventory.add_item(target['item_id'], target.get('count', 1))
                self.world.remove_object(target)

    def use_item(self):
        """Use currently equipped item (eat/drink)"""
        self.inventory.use_equipped()

    def toggle_inventory(self):
        self.inventory.is_open = not self.inventory.is_open

    @property
    def time_str(self):
        h = int(self.time_of_day)
        m = int((self.time_of_day - h) * 60)
        icon = '🌙' if (h < 6 or h >= 20) else '🌤' if h < 18 else '🌅'
        return f'Day {self.day_number}  {h:02d}:{m:02d} {icon}'
