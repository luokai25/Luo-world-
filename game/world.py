"""
World - Procedural Jungle Generator
Terrain heightmap, tree placement, rocks, water, grass
"""

from ursina import *
import numpy as np
import math
import random


class World:
    def __init__(self, physics=None, seed=42):
        self.physics = physics
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        # Terrain config
        self.chunk_size   = 64      # units per chunk
        self.terrain_size = 128     # total world size
        self.height_scale = 6.0    # max terrain height variation

        # Entity lists
        self.terrain_entity = None
        self.trees    = []
        self.rocks    = []
        self.foliage  = []
        self.water    = None

        # Height cache
        self._height_map = None

        self._generate()

    # ──────────────────────────────────────────
    #  GENERATION
    # ──────────────────────────────────────────
    def _generate(self):
        print("🌿 Generating world...")
        self._gen_heightmap()
        self._build_terrain()
        self._build_water()
        self._place_trees()
        self._place_rocks()
        self._place_grass()
        self._build_skybox()
        print("✅ World ready.")

    def _gen_heightmap(self):
        """Multi-octave Perlin-like noise heightmap"""
        size = self.terrain_size
        hmap = np.zeros((size, size))

        # Layer multiple frequencies
        for octave in range(5):
            freq = 0.02 * (2 ** octave)
            amp  = self.height_scale / (2 ** octave)
            for x in range(size):
                for z in range(size):
                    # Simple sine-based approximation (no external noise lib needed)
                    val = (
                        math.sin(x * freq + self.seed) *
                        math.cos(z * freq * 1.3 + self.seed * 0.7) +
                        math.sin((x + z) * freq * 0.8 + self.seed * 1.2) * 0.5
                    )
                    hmap[x][z] += val * amp

        # Flatten spawn area (5x5 units around center)
        cx, cz = size // 2, size // 2
        for x in range(cx - 8, cx + 8):
            for z in range(cz - 8, cz + 8):
                dist = math.sqrt((x-cx)**2 + (z-cz)**2)
                factor = min(1.0, dist / 8.0)
                hmap[x][z] = lerp(0, hmap[x][z], factor)

        self._height_map = hmap

    def _build_terrain(self):
        """Build terrain mesh from heightmap"""
        size = self.terrain_size
        half = size / 2

        # Build grid of quads
        verts = []
        tris  = []
        colors = []

        step = 2   # sample every N units for performance
        samples = size // step

        for xi in range(samples):
            for zi in range(samples):
                x = xi * step - half
                z = zi * step - half
                y = self._height_map[xi * step][zi * step]

                verts.append([x, y, z])

                # Color based on height + slope
                if y < 0.2:
                    r, g, b = 60, 110, 50    # low wet grass
                elif y < 2.0:
                    r, g, b = 45, 100, 35    # mid jungle floor
                elif y < 4.0:
                    r, g, b = 80, 90, 40     # higher dry grass
                else:
                    r, g, b = 100, 85, 65    # rock/dirt peaks
                noise = self.np_rng.integers(-8, 8)
                colors.append([r+noise, g+noise, b, 255])

        # Triangulate grid
        for xi in range(samples - 1):
            for zi in range(samples - 1):
                i  = xi * samples + zi
                i1 = i + 1
                i2 = (xi + 1) * samples + zi
                i3 = i2 + 1
                tris.append([i, i2, i1])
                tris.append([i1, i2, i3])

        verts_np  = np.array(verts,  dtype=np.float32)
        tris_np   = np.array(tris,   dtype=np.int32)
        colors_np = np.array(colors, dtype=np.uint8)

        # Build Ursina mesh
        terrain_mesh = Mesh(
            vertices=[Vec3(*v) for v in verts_np],
            triangles=tris_np.tolist(),
            colors=[color.rgba(*c) for c in colors_np],
        )

        self.terrain_entity = Entity(
            model=terrain_mesh,
            collider='mesh',
            name='terrain',
        )

        # Physics ground plane as fallback
        if self.physics:
            self.physics.create_ground_plane(y=0)

    def _build_water(self):
        """Flat water plane at y=0.1 - rivers and ponds"""
        self.water = Entity(
            model='quad',
            scale=(self.terrain_size, self.terrain_size),
            rotation_x=90,
            position=(0, 0.05, 0),
            color=color.rgba(30, 80, 160, 120),
        )

    def _place_trees(self):
        """Scatter trees across jungle floor"""
        n_trees = 200
        half = self.terrain_size / 2

        for _ in range(n_trees):
            x = self.rng.uniform(-half + 5, half - 5)
            z = self.rng.uniform(-half + 5, half - 5)

            # Don't spawn within 8 units of player start
            if abs(x) < 8 and abs(z) < 8:
                continue

            y = self.get_height(x, z)
            if y < 0.0:   # skip underwater
                continue

            # Random tree scale
            scale = self.rng.uniform(0.8, 2.5)
            tree_type = self.rng.randint(0, 3)

            tree = self._make_tree(x, y, z, scale, tree_type)
            self.trees.append(tree)

    def _make_tree(self, x, y, z, scale=1.0, tree_type=0):
        """Build a single tree entity"""
        trunk_h = self.rng.uniform(3, 7) * scale
        trunk_r = self.rng.uniform(0.12, 0.25) * scale

        trunk = Entity(
            model='cylinder',
            color=color.rgb(
                self.rng.randint(55, 85),
                self.rng.randint(35, 55),
                self.rng.randint(15, 30)
            ),
            scale=(trunk_r, trunk_h, trunk_r),
            position=(x, y + trunk_h/2, z),
            collider='box',
        )
        trunk.luo_type = 'tree'
        trunk.health = 5
        trunk.drops = [('wood_log', self.rng.randint(2, 5))]

        # Canopy layers
        canopy_colors = [
            color.rgb(20, 90, 25),
            color.rgb(30, 110, 35),
            color.rgb(15, 75, 20),
            color.rgb(40, 130, 45),
        ]
        n_layers = self.rng.randint(2, 4)
        for li in range(n_layers):
            cr = (trunk_r * 8 + li * 0.5) * scale
            cy = y + trunk_h * (0.65 + li * 0.15)
            canopy = Entity(
                model='sphere',
                color=canopy_colors[li % len(canopy_colors)],
                scale=(cr, cr * 0.75, cr),
                position=(x + self.rng.uniform(-0.3,0.3)*scale,
                           cy,
                           z + self.rng.uniform(-0.3,0.3)*scale),
            )

        return trunk

    def _place_rocks(self):
        """Scatter rocks"""
        half = self.terrain_size / 2
        for _ in range(80):
            x = self.rng.uniform(-half + 3, half - 3)
            z = self.rng.uniform(-half + 3, half - 3)
            if abs(x) < 5 and abs(z) < 5:
                continue
            y = self.get_height(x, z)
            s = self.rng.uniform(0.2, 1.2)
            rock = Entity(
                model='sphere',
                color=color.rgb(
                    self.rng.randint(85, 130),
                    self.rng.randint(85, 130),
                    self.rng.randint(75, 115),
                ),
                scale=(s, s*0.65, s*0.9),
                position=(x, y + s*0.3, z),
                collider='sphere',
            )
            rock.luo_type = 'rock'
            rock.health = 3
            rock.drops = [('stone', self.rng.randint(1, 4))]
            self.rocks.append(rock)

    def _place_grass(self):
        """Dense grass patches on jungle floor"""
        half = self.terrain_size / 2
        for _ in range(500):
            x = self.rng.uniform(-half + 2, half - 2)
            z = self.rng.uniform(-half + 2, half - 2)
            y = self.get_height(x, z)
            if y < 0:
                continue
            h = self.rng.uniform(0.15, 0.45)
            grass = Entity(
                model='quad',
                color=color.rgb(
                    self.rng.randint(25, 55),
                    self.rng.randint(90, 140),
                    self.rng.randint(20, 45),
                ),
                scale=(self.rng.uniform(0.2, 0.5), h, 1),
                position=(x, y + h/2, z),
                billboard=True,   # always faces camera
                double_sided=True,
            )
            self.foliage.append(grass)

    def _build_skybox(self):
        """Sky dome - blue with cloud hints"""
        sky = Entity(
            model='sphere',
            color=color.rgb(100, 160, 220),
            scale=500,
            double_sided=True,
        )

    # ──────────────────────────────────────────
    #  RUNTIME
    # ──────────────────────────────────────────
    def get_height(self, x, z):
        """Sample terrain height at world position"""
        if self._height_map is None:
            return 0.0
        half = self.terrain_size / 2
        xi = int((x + half) / self.terrain_size * (self.terrain_size - 1))
        zi = int((z + half) / self.terrain_size * (self.terrain_size - 1))
        xi = max(0, min(self.terrain_size - 1, xi))
        zi = max(0, min(self.terrain_size - 1, zi))
        return float(self._height_map[xi][zi])

    def update(self):
        """Per-frame world updates (wind, ambient, etc.)"""
        # Gentle grass sway
        t = time.time
        for i, grass in enumerate(self.foliage[::5]):  # update every 5th
            grass.rotation_z = math.sin(t * 1.2 + i * 0.5) * 5

    def destroy_object(self, entity):
        """Remove an object from the world and drop its items"""
        drops = getattr(entity, 'drops', [])
        pos = entity.position
        destroy(entity)
        return drops, pos
