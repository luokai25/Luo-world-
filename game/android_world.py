"""
AndroidWorld - Pure Python world simulation
512x512 unit world (8x bigger than before)
600 trees, 300 rocks, 200 vines, animals, water sources,
caves, clearings, rivers, fruit trees, berry bushes
"""

import math
import random


class WorldObject:
    def __init__(self, obj_type, x, z, **kwargs):
        self.type    = obj_type
        self.x       = x
        self.z       = z
        self.health  = kwargs.get('health', 3)
        self.drops   = kwargs.get('drops', [])
        self.item_id = kwargs.get('item_id', None)
        self.count   = kwargs.get('count', 1)
        self.active  = True
        self.data    = kwargs   # extra metadata

    def to_dict(self):
        return {
            'type':    self.type,
            'x':       self.x,
            'z':       self.z,
            'health':  self.health,
            'drops':   self.drops,
            'item_id': self.item_id,
            'count':   self.count,
            '_ref':    self,
            **{k: v for k, v in self.data.items()
               if k not in ('drops',)},
        }


class Animal:
    def __init__(self, animal_type, x, z, rng):
        self.type    = animal_type
        self.x       = x
        self.z       = z
        self.active  = True
        self.rng     = rng

        configs = {
            'deer':   {'health': 30, 'speed': 6.0, 'drops': [('raw_meat', 3), ('hide', 1)], 'flee_range': 8.0},
            'boar':   {'health': 50, 'speed': 4.5, 'drops': [('raw_meat', 4), ('hide', 2)], 'flee_range': 5.0},
            'rabbit': {'health': 10, 'speed': 8.0, 'drops': [('raw_meat', 1)],              'flee_range': 12.0},
            'bird':   {'health': 5,  'speed': 10.0,'drops': [('feather', 2)],               'flee_range': 15.0},
        }
        cfg = configs.get(animal_type, configs['deer'])
        self.max_health = cfg['health']
        self.health     = cfg['health']
        self.speed      = cfg['speed']
        self.drops      = cfg['drops']
        self.flee_range = cfg['flee_range']

        # Wander state
        self.target_x  = x
        self.target_z  = z
        self.wander_timer = rng.uniform(2, 8)
        self.fleeing   = False

    def update(self, dt, player_x, player_z, get_height):
        if not self.active:
            return

        # Check if player is close → flee
        dx = self.x - player_x
        dz = self.z - player_z
        dist = math.sqrt(dx*dx + dz*dz)

        if dist < self.flee_range:
            self.fleeing = True
            # Run away from player
            if dist > 0:
                nx = dx / dist
                nz = dz / dist
                flee_speed = self.speed * 1.5
                self.x += nx * flee_speed * dt
                self.z += nz * flee_speed * dt
        else:
            self.fleeing = False
            # Wander
            self.wander_timer -= dt
            if self.wander_timer <= 0:
                # Pick new wander target nearby
                self.target_x = self.x + self.rng.uniform(-20, 20)
                self.target_z = self.z + self.rng.uniform(-20, 20)
                self.wander_timer = self.rng.uniform(3, 10)

            # Move toward target
            tx = self.target_x - self.x
            tz = self.target_z - self.z
            td = math.sqrt(tx*tx + tz*tz)
            if td > 1.0:
                self.x += (tx/td) * self.speed * 0.4 * dt
                self.z += (tz/td) * self.speed * 0.4 * dt

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.active = False
            return True  # dead
        return False

    def to_dict(self):
        return {
            'type': 'animal',
            'animal_type': self.type,
            'x': self.x,
            'z': self.z,
            'health': self.health,
            'drops': self.drops,
            '_ref': self,
        }


class AndroidWorld:
    WORLD_SIZE = 512   # 8x bigger than before

    def __init__(self, seed=42):
        self.seed    = seed
        self.rng     = random.Random(seed)
        self.size    = self.WORLD_SIZE
        self.objects = []
        self.animals = []
        self._biomes = {}   # track biome zones
        self._generate()

    # ─────────────────────────────────────────
    #  GENERATION
    # ─────────────────────────────────────────
    def _generate(self):
        print("🌿 Generating 512x512 jungle world...")
        self._gen_biomes()
        self._place_trees()
        self._place_rocks()
        self._place_vines()
        self._place_fruits()
        self._place_berries()
        self._place_mushrooms()
        self._place_water_sources()
        self._spawn_animals()
        print(f"✅ World ready: {len(self.objects)} objects, {len(self.animals)} animals")

    def _gen_biomes(self):
        """Divide world into biome zones"""
        # Simple grid-based biomes
        zones = [
            'dense_jungle', 'dense_jungle', 'rainforest',
            'dense_jungle', 'clearing',     'dense_jungle',
            'rainforest',   'dense_jungle', 'rocky_hills',
            'dense_jungle', 'swamp',        'dense_jungle',
        ]
        half = self.size // 2
        zone_size = self.size // 4
        zi = 0
        for gx in range(4):
            for gz in range(3):
                cx = -half + gx * zone_size + zone_size // 2
                cz = -half + gz * zone_size + zone_size // 2
                self._biomes[(gx, gz)] = {
                    'type': zones[zi % len(zones)],
                    'cx': cx, 'cz': cz,
                }
                zi += 1

    def _biome_at(self, x, z):
        half = self.size // 2
        zone_size = self.size // 4
        gx = int((x + half) // zone_size)
        gz = int((z + half) // zone_size)
        gx = max(0, min(3, gx))
        gz = max(0, min(2, gz))
        return self._biomes.get((gx, gz), {}).get('type', 'dense_jungle')

    def _place_trees(self):
        half = self.size // 2
        n = 600
        for _ in range(n):
            x = self.rng.uniform(-half + 5, half - 5)
            z = self.rng.uniform(-half + 5, half - 5)
            # Keep spawn clear
            if abs(x) < 12 and abs(z) < 12:
                continue
            biome = self._biome_at(x, z)
            # More trees in dense jungle, fewer in clearing
            if biome == 'clearing' and self.rng.random() > 0.15:
                continue
            if biome == 'rocky_hills' and self.rng.random() > 0.4:
                continue

            tree_type = self.rng.choice(['oak', 'palm', 'bamboo', 'fruit_tree'])
            if biome == 'swamp':
                tree_type = 'swamp_tree'

            drops = [('wood_log', self.rng.randint(2, 6)),
                     ('stick',    self.rng.randint(1, 4))]
            if tree_type == 'fruit_tree':
                drops.append(('fruit', self.rng.randint(1, 3)))

            obj = WorldObject(
                'tree', x, z,
                health=5,
                drops=drops,
                tree_type=tree_type,
                biome=biome,
            )
            self.objects.append(obj)

    def _place_rocks(self):
        half = self.size // 2
        for _ in range(300):
            x = self.rng.uniform(-half + 3, half - 3)
            z = self.rng.uniform(-half + 3, half - 3)
            if abs(x) < 8 and abs(z) < 8:
                continue
            biome = self._biome_at(x, z)
            # More rocks in rocky_hills
            if biome == 'rocky_hills':
                size_mult = self.rng.uniform(1.0, 3.0)
            else:
                size_mult = self.rng.uniform(0.3, 1.2)

            drops = [('stone', self.rng.randint(1, 4)),
                     ('flint', self.rng.randint(0, 2))]
            # Rare ore in rocky hills
            if biome == 'rocky_hills' and self.rng.random() > 0.7:
                drops.append(('iron_ore', self.rng.randint(1, 2)))

            obj = WorldObject(
                'rock', x, z,
                health=3,
                drops=drops,
                size=size_mult,
                biome=biome,
            )
            self.objects.append(obj)

    def _place_vines(self):
        half = self.size // 2
        for _ in range(200):
            x = self.rng.uniform(-half + 2, half - 2)
            z = self.rng.uniform(-half + 2, half - 2)
            if abs(x) < 5 and abs(z) < 5:
                continue
            obj = WorldObject(
                'item', x, z,
                item_id='vine',
                count=self.rng.randint(1, 3),
                health=1,
                drops=[('vine', self.rng.randint(1, 3))],
            )
            self.objects.append(obj)

    def _place_fruits(self):
        half = self.size // 2
        for _ in range(80):
            x = self.rng.uniform(-half + 2, half - 2)
            z = self.rng.uniform(-half + 2, half - 2)
            obj = WorldObject(
                'item', x, z,
                item_id='fruit',
                count=self.rng.randint(1, 2),
                health=1,
                drops=[('fruit', self.rng.randint(1, 2))],
            )
            self.objects.append(obj)

    def _place_berries(self):
        half = self.size // 2
        for _ in range(100):
            x = self.rng.uniform(-half + 2, half - 2)
            z = self.rng.uniform(-half + 2, half - 2)
            obj = WorldObject(
                'bush', x, z,
                health=2,
                drops=[('berry', self.rng.randint(2, 5))],
                item_id='berry',
            )
            self.objects.append(obj)

    def _place_mushrooms(self):
        half = self.size // 2
        for _ in range(150):
            x = self.rng.uniform(-half + 2, half - 2)
            z = self.rng.uniform(-half + 2, half - 2)
            m_type = self.rng.choice(['edible', 'edible', 'edible', 'poisonous'])
            obj = WorldObject(
                'item', x, z,
                item_id='mushroom_' + m_type,
                count=self.rng.randint(1, 3),
                health=1,
                drops=[('mushroom_' + m_type, self.rng.randint(1, 3))],
            )
            self.objects.append(obj)

    def _place_water_sources(self):
        """Rivers, ponds, waterfalls - can fill wooden cup"""
        half = self.size // 2
        # Main river running through world
        for i in range(60):
            t = i / 60.0
            x = math.sin(t * math.pi * 2) * 80 - 20
            z = t * self.size - half
            obj = WorldObject(
                'water_source', x, z,
                health=999,
                item_id='water',
                drops=[],
                water_type='river',
            )
            self.objects.append(obj)

        # Ponds scattered
        for _ in range(8):
            x = self.rng.uniform(-half + 20, half - 20)
            z = self.rng.uniform(-half + 20, half - 20)
            if abs(x) < 15 and abs(z) < 15:
                continue
            obj = WorldObject(
                'water_source', x, z,
                health=999,
                item_id='water',
                drops=[],
                water_type='pond',
                radius=self.rng.uniform(5, 20),
            )
            self.objects.append(obj)

    def _spawn_animals(self):
        half = self.size // 2
        spawns = [
            ('deer',   50),
            ('boar',   25),
            ('rabbit', 80),
            ('bird',   40),
        ]
        for animal_type, count in spawns:
            for _ in range(count):
                x = self.rng.uniform(-half + 10, half - 10)
                z = self.rng.uniform(-half + 10, half - 10)
                if abs(x) < 15 and abs(z) < 15:
                    continue
                animal = Animal(animal_type, x, z, self.rng)
                self.animals.append(animal)

    # ─────────────────────────────────────────
    #  RUNTIME
    # ─────────────────────────────────────────
    def get_height(self, x, z):
        """Multi-octave terrain height"""
        h = 0.0
        for octave in range(4):
            freq = 0.015 * (2 ** octave)
            amp  = 5.0 / (2 ** octave)
            h += math.sin(x * freq + self.seed) * \
                 math.cos(z * freq * 1.3 + self.seed * 0.7) * amp
            h += math.sin((x + z) * freq * 0.8 + self.seed * 1.2) * amp * 0.5

        # Rocky hills are higher
        biome = self._biome_at(x, z)
        if biome == 'rocky_hills':
            h += 4.0
        elif biome == 'swamp':
            h = min(h, 0.5)

        # Flat spawn zone
        dist = math.sqrt(x*x + z*z)
        if dist < 12:
            h = h * (dist / 12.0)

        return max(-1.0, h)

    def nearest_object(self, px, pz, radius=3.0):
        """Find nearest active world object within radius"""
        best = None
        best_dist = radius

        for obj in self.objects:
            if not obj.active:
                continue
            d = math.sqrt((obj.x - px)**2 + (obj.z - pz)**2)
            if d < best_dist:
                best_dist = d
                best = obj.to_dict()

        # Also check animals
        for animal in self.animals:
            if not animal.active:
                continue
            d = math.sqrt((animal.x - px)**2 + (animal.z - pz)**2)
            if d < best_dist:
                best_dist = d
                best = animal.to_dict()

        return best

    def destroy_object(self, obj_dict):
        ref = obj_dict.get('_ref')
        if ref:
            ref.active = False
        return obj_dict.get('drops', []), (obj_dict['x'], 0, obj_dict['z'])

    def remove_object(self, obj_dict):
        ref = obj_dict.get('_ref')
        if ref:
            ref.active = False

    def drop_item(self, item_id, count, x, z):
        obj = WorldObject('item', x, z,
                          item_id=item_id, count=count, health=1,
                          drops=[(item_id, count)])
        self.objects.append(obj)

    def update(self, dt):
        px = 0; pz = 0  # Will be set by game_state
        for animal in self.animals:
            animal.update(dt, self._player_x, self._player_z,
                          self.get_height)

    # Called by game_state each frame to track player pos
    _player_x = 0.0
    _player_z = 0.0

    def set_player_pos(self, x, z):
        self._player_x = x
        self._player_z = z

    @property
    def active_objects(self):
        return [o for o in self.objects if o.active]

    @property
    def active_animals(self):
        return [a for a in self.animals if a.active]

    def stats(self):
        return {
            'objects': len(self.active_objects),
            'animals': len(self.active_animals),
            'size': f'{self.size}x{self.size}',
        }
