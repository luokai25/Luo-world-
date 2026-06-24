"""
Campfire System
- Place campfire in world (requires: 3 logs + 2 sticks + 1 flint)
- Light it with flint
- Cook raw meat on it
- Provides warmth at night
- Burns out after ~10 real minutes, can be refueled
"""

import math
import time as sys_time


class Campfire:
    def __init__(self, x, y, z, world_id=None):
        self.x        = x
        self.y        = y
        self.z        = z
        self.world_id = world_id or id(self)

        self.lit      = False
        self.fuel     = 0.0        # seconds of burn remaining
        self.max_fuel = 600.0      # 10 minutes
        self.warmth_range = 8.0    # units radius

        # Cooking slots (2 slots)
        self.cooking_slots = [None, None]   # each: {item_id, timer, total_time}
        self.active   = True

        # Visual state
        self.flame_intensity = 0.0
        self._flicker_timer  = 0.0

    def light(self, fuel_seconds=600.0):
        """Light the campfire"""
        if not self.lit:
            self.lit  = True
            self.fuel = min(self.fuel + fuel_seconds, self.max_fuel)
            return True
        # Already lit — add fuel
        self.fuel = min(self.fuel + fuel_seconds, self.max_fuel)
        return True

    def extinguish(self):
        self.lit = False

    def add_fuel(self, amount=120.0):
        """Add fuel (wood log = 120s, stick = 30s)"""
        if not self.active:
            return False
        self.fuel = min(self.fuel + amount, self.max_fuel)
        if self.fuel > 0 and not self.lit:
            self.lit = True
        return True

    def cook(self, slot_index, item_id):
        """Start cooking an item in a slot"""
        COOK_TIMES = {
            'raw_meat':  8.0,
            'mushroom_edible': 4.0,
            'fruit': 3.0,
        }
        if not self.lit:
            return False, "Campfire is not lit"
        if slot_index not in (0, 1):
            return False, "Invalid slot"
        if self.cooking_slots[slot_index] is not None:
            return False, "Slot occupied"
        cook_time = COOK_TIMES.get(item_id, 8.0)
        self.cooking_slots[slot_index] = {
            'item_id':    item_id,
            'timer':      0.0,
            'total_time': cook_time,
            'done':       False,
        }
        return True, f"Cooking {item_id}..."

    def take_cooked(self, slot_index):
        """Take finished cooked item from slot"""
        slot = self.cooking_slots[slot_index]
        if slot is None:
            return None
        if not slot['done']:
            return None
        self.cooking_slots[slot_index] = None

        COOKED_RESULT = {
            'raw_meat':      'cooked_meat',
            'mushroom_edible': 'mushroom_cooked',
            'fruit':         'roasted_fruit',
        }
        return COOKED_RESULT.get(slot['item_id'], slot['item_id'] + '_cooked')

    def update(self, dt):
        """Per-frame update"""
        if not self.active:
            return []

        events = []

        if self.lit:
            # Burn fuel
            self.fuel -= dt
            if self.fuel <= 0:
                self.fuel = 0
                self.lit  = False
                events.append(('fire_out', self))

            # Update cooking slots
            for i, slot in enumerate(self.cooking_slots):
                if slot is None or slot['done']:
                    continue
                slot['timer'] += dt
                if slot['timer'] >= slot['total_time']:
                    slot['done'] = True
                    events.append(('cooked', self, i, slot['item_id']))

            # Flicker
            self._flicker_timer += dt
            self.flame_intensity = (
                0.7 + 0.3 * math.sin(self._flicker_timer * 8.3) *
                math.sin(self._flicker_timer * 5.1)
            )
        else:
            self.flame_intensity = 0.0

        return events

    def warmth_at(self, x, z):
        """Warmth contribution at a point"""
        if not self.lit:
            return 0.0
        dist = math.sqrt((x - self.x)**2 + (z - self.z)**2)
        if dist > self.warmth_range:
            return 0.0
        return 1.0 - (dist / self.warmth_range)

    @property
    def fuel_pct(self):
        return self.fuel / self.max_fuel

    @property
    def cooking_progress(self):
        results = []
        for slot in self.cooking_slots:
            if slot is None:
                results.append(None)
            else:
                pct = slot['timer'] / slot['total_time']
                results.append({
                    'item_id': slot['item_id'],
                    'progress': min(1.0, pct),
                    'done': slot['done'],
                })
        return results

    def to_dict(self):
        return {
            'type': 'campfire',
            'x': self.x, 'y': self.y, 'z': self.z,
            'lit': self.lit,
            'fuel_pct': self.fuel_pct,
            'world_id': self.world_id,
            '_ref': self,
        }


class CampfireManager:
    """Manages all placed campfires in the world"""

    def __init__(self):
        self.campfires = []

    def place(self, x, y, z):
        cf = Campfire(x, y, z)
        cf.light()   # auto-light when placed
        self.campfires.append(cf)
        return cf

    def nearest(self, px, pz, radius=5.0):
        """Find nearest campfire within radius"""
        best = None
        best_dist = radius
        for cf in self.campfires:
            if not cf.active:
                continue
            d = math.sqrt((cf.x - px)**2 + (cf.z - pz)**2)
            if d < best_dist:
                best_dist = d
                best = cf
        return best

    def warmth_at(self, px, pz):
        """Total warmth from all fires"""
        return sum(cf.warmth_at(px, pz) for cf in self.campfires if cf.lit)

    def update(self, dt):
        events = []
        for cf in self.campfires:
            events.extend(cf.update(dt))
        return events
