"""
World - Desktop only (Ursina)
Stub on Android - Android uses AndroidWorld in android_world.py
"""
try:
    from ursina import *
    HAS_URSINA = True
except ImportError:
    HAS_URSINA = False

import math, random, numpy as np if False else None

import math
import random

class World:
    def __init__(self, physics=None, seed=42):
        self.physics  = physics
        self.seed     = seed
        self.rng      = random.Random(seed)
        self.size     = 128
        self.trees    = []
        self.rocks    = []
        self.foliage  = []
        self._height_map = None

        if HAS_URSINA:
            self._generate()

    def _generate(self):
        if not HAS_URSINA: return
        self._gen_heightmap()
        self._build_terrain()
        self._build_water()
        self._place_trees()
        self._place_rocks()
        self._build_skybox()

    def _gen_heightmap(self):
        size = self.size
        import numpy as np
        hmap = np.zeros((size, size))
        for octave in range(5):
            freq = 0.02 * (2**octave)
            amp  = 6.0 / (2**octave)
            for x in range(size):
                for z in range(size):
                    hmap[x][z] += (
                        math.sin(x*freq+self.seed) *
                        math.cos(z*freq*1.3+self.seed*0.7) +
                        math.sin((x+z)*freq*0.8+self.seed*1.2)*0.5
                    ) * amp
        cx, cz = size//2, size//2
        for x in range(cx-8, cx+8):
            for z in range(cz-8, cz+8):
                dist = math.sqrt((x-cx)**2+(z-cz)**2)
                hmap[x][z] *= min(1.0, dist/8.0)
        self._height_map = hmap

    def _build_terrain(self):
        if not HAS_URSINA: return
        # Simple flat plane for desktop
        Entity(model='plane', scale=self.size,
               color=color.rgb(45,100,35), collider='box')
        if self.physics:
            self.physics.create_ground_plane(y=0)

    def _build_water(self):
        if not HAS_URSINA: return
        Entity(model='quad', scale=self.size, rotation_x=90,
               position=(0,0.05,0), color=color.rgba(30,80,160,120))

    def _place_trees(self):
        if not HAS_URSINA: return
        half = self.size//2
        for _ in range(80):
            x = self.rng.uniform(-half+5, half-5)
            z = self.rng.uniform(-half+5, half-5)
            if abs(x)<8 and abs(z)<8: continue
            y = self.get_height(x,z)
            h = self.rng.uniform(2,5)
            t = Entity(model='cylinder', color=color.rgb(65,40,18),
                       scale=(0.2,h,0.2), position=(x,y+h/2,z), collider='box')
            t.luo_type = 'tree'; t.health = 5
            t.drops = [('wood_log', self.rng.randint(2,5))]
            self.trees.append(t)
            Entity(model='sphere', color=color.rgb(25,100,30),
                   scale=self.rng.uniform(1.5,3), position=(x,y+h,z))

    def _place_rocks(self):
        if not HAS_URSINA: return
        half = self.size//2
        for _ in range(40):
            x = self.rng.uniform(-half+3, half-3)
            z = self.rng.uniform(-half+3, half-3)
            if abs(x)<5 and abs(z)<5: continue
            y = self.get_height(x,z)
            s = self.rng.uniform(0.3,1.0)
            r = Entity(model='sphere', color=color.rgb(110,110,100),
                       scale=(s,s*0.65,s*0.9), position=(x,y+s*0.3,z), collider='sphere')
            r.luo_type = 'rock'; r.health = 3
            r.drops = [('stone', self.rng.randint(1,4))]
            self.rocks.append(r)

    def _build_skybox(self):
        if not HAS_URSINA: return
        Entity(model='sphere', color=color.rgb(100,160,220),
               scale=500, double_sided=True)

    def get_height(self, x, z):
        if self._height_map is None: return 0.0
        half = self.size//2
        xi = int((x+half)/self.size*(self.size-1))
        zi = int((z+half)/self.size*(self.size-1))
        xi = max(0, min(self.size-1, xi))
        zi = max(0, min(self.size-1, zi))
        return float(self._height_map[xi][zi])

    def update(self):
        pass

    def destroy_object(self, entity):
        drops = getattr(entity, 'drops', [])
        pos   = entity.position if HAS_URSINA else (0,0,0)
        if HAS_URSINA: destroy(entity)
        return drops, pos
