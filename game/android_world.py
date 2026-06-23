"""
AndroidWorld - Pure Python world simulation
No rendering engine dependency
Tracks objects, terrain heights, resources
"""

import math
import random


class WorldObject:
    def __init__(self, obj_type, x, z, **kwargs):
        self.type   = obj_type
        self.x      = x
        self.z      = z
        self.health = kwargs.get('health', 3)
        self.drops  = kwargs.get('drops', [])
        self.item_id= kwargs.get('item_id', None)
        self.count  = kwargs.get('count', 1)
        self.active = True

    def to_dict(self):
        return {
            'type':    self.type,
            'x':       self.x,
            'z':       self.z,
            'health':  self.health,
            'drops':   self.drops,
            'item_id': self.item_id,
            'count':   self.count,
        }


class AndroidWorld:
    def __init__(self, seed=42):
        self.seed   = seed
        self.rng    = random.Random(seed)
        self.size   = 128
        self.objects = []
        self._dropped_items = []
        self._generate()

    def _generate(self):
        half = self.size / 2
        # Trees
        for _ in range(200):
            x = self.rng.uniform(-half+5, half-5)
            z = self.rng.uniform(-half+5, half-5)
            if abs(x) < 8 and abs(z) < 8:
                continue
            obj = WorldObject(
                'tree', x, z,
                health=5,
                drops=[('wood_log', self.rng.randint(2,5)),
                       ('stick',    self.rng.randint(1,3))]
            )
            self.objects.append(obj)

        # Rocks
        for _ in range(80):
            x = self.rng.uniform(-half+3, half-3)
            z = self.rng.uniform(-half+3, half-3)
            if abs(x) < 5 and abs(z) < 5:
                continue
            obj = WorldObject(
                'rock', x, z,
                health=3,
                drops=[('stone', self.rng.randint(1,4)),
                       ('flint', self.rng.randint(0,2))]
            )
            self.objects.append(obj)

        # Vines on ground
        for _ in range(60):
            x = self.rng.uniform(-half+2, half-2)
            z = self.rng.uniform(-half+2, half-2)
            if abs(x) < 4 and abs(z) < 4:
                continue
            obj = WorldObject(
                'item', x, z,
                item_id='vine',
                count=self.rng.randint(1,3),
                health=1,
                drops=[('vine', self.rng.randint(1,3))]
            )
            self.objects.append(obj)

    def get_height(self, x, z):
        """Simple terrain height via noise approximation"""
        h = (math.sin(x * 0.05) * math.cos(z * 0.05 * 1.3) +
             math.sin((x+z) * 0.04) * 0.5) * 3.0
        # Flatten spawn area
        dist = math.sqrt(x*x + z*z)
        if dist < 8:
            h = h * (dist / 8.0)
        return max(-0.5, h)

    def nearest_object(self, px, pz, radius=3.0):
        """Find nearest active world object within radius"""
        best = None
        best_dist = radius
        for obj in self.objects:
            if not obj.active:
                continue
            d = math.sqrt((obj.x-px)**2 + (obj.z-pz)**2)
            if d < best_dist:
                best_dist = d
                best = obj.to_dict()
                best['_ref'] = obj
        return best

    def destroy_object(self, obj_dict):
        """Remove object and return its drops"""
        ref = obj_dict.get('_ref')
        if ref:
            ref.active = False
        return obj_dict.get('drops', []), (obj_dict['x'], 0, obj_dict['z'])

    def remove_object(self, obj_dict):
        ref = obj_dict.get('_ref')
        if ref:
            ref.active = False

    def drop_item(self, item_id, count, x, z):
        """Drop an item on the ground"""
        obj = WorldObject('item', x, z, item_id=item_id, count=count, health=1)
        self.objects.append(obj)

    def update(self, dt):
        """Per-frame world simulation (respawn, weather, etc.)"""
        pass   # Expand in future sessions

    @property
    def active_objects(self):
        return [o for o in self.objects if o.active]
