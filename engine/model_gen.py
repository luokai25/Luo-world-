"""
Procedural 3D Model Generator
Uses trimesh + numpy to generate detailed game assets:
- Stone axe (detailed flint head + wood handle with bindings)
- Cooked meat (irregular organic shape)
- Wooden water cup
- Trees, rocks, terrain chunks
All exported as .glb for Panda3D / Blender compatibility
"""

import trimesh
import trimesh.creation as tc
import numpy as np
import os
import math

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'models')


def ensure_output():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
#  STONE AXE
# ─────────────────────────────────────────────

def gen_stone_axe():
    """
    Detailed stone hand-axe:
    - Chipped flint head with irregular edges (not smooth)
    - Wooden handle with grain-like geometry
    - Leather binding wraps at junction
    """
    meshes = []

    # --- Flint head ---
    # Start with a box and deform vertices to create chipped stone look
    head = tc.box(extents=[0.06, 0.14, 0.025])
    verts = head.vertices.copy()

    rng = np.random.default_rng(42)
    # Add chip noise — stronger at edges
    for i, v in enumerate(verts):
        edge_factor = (abs(v[0]) / 0.03 + abs(v[1]) / 0.07)
        noise = rng.uniform(-0.008, 0.008) * edge_factor
        verts[i][2] += noise
        verts[i][0] += rng.uniform(-0.003, 0.003) * edge_factor
        verts[i][1] += rng.uniform(-0.003, 0.003) * edge_factor

    # Taper to a blade edge at top
    for i, v in enumerate(verts):
        taper = (v[1] + 0.07) / 0.14   # 0 at bottom, 1 at top
        verts[i][2] *= (1.0 - taper * 0.85)
        verts[i][0] *= (1.0 - taper * 0.3)

    head = trimesh.Trimesh(vertices=verts, faces=head.faces)
    head.apply_translation([0, 0.09, 0])

    # Color: dark grey flint
    head.visual.vertex_colors = [60, 65, 70, 255]
    meshes.append(head)

    # --- Handle ---
    # Cylinder with slight taper and twist for natural wood look
    handle = tc.cylinder(radius=0.012, height=0.38, sections=12)
    hverts = handle.vertices.copy()
    for i, v in enumerate(hverts):
        t = (v[1] + 0.19) / 0.38
        # Slight organic taper
        hverts[i][0] *= (1.0 + t * 0.15)
        hverts[i][2] *= (1.0 + t * 0.08)
        # Wood grain ripple
        grain = math.sin(v[1] * 40) * 0.001
        hverts[i][0] += grain
    handle = trimesh.Trimesh(vertices=hverts, faces=handle.faces)
    handle.apply_translation([0, -0.10, 0])

    # Color: brown wood
    handle.visual.vertex_colors = [101, 67, 33, 255]
    meshes.append(handle)

    # --- Leather bindings (3 rings) ---
    for y_off in [-0.01, 0.02, 0.05]:
        binding = tc.annulus(r_min=0.013, r_max=0.022, height=0.012, sections=16)
        binding.apply_translation([0, y_off, 0])
        binding.visual.vertex_colors = [80, 50, 25, 255]
        meshes.append(binding)

    axe = trimesh.util.concatenate(meshes)
    axe = trimesh.Trimesh(
        vertices=axe.vertices,
        faces=axe.faces,
        vertex_colors=axe.visual.vertex_colors
    )

    path = os.path.join(OUTPUT_DIR, 'stone_axe.glb')
    axe.export(path)
    print(f"✓ Stone axe exported: {path}")
    return path


# ─────────────────────────────────────────────
#  COOKED MEAT
# ─────────────────────────────────────────────

def gen_cooked_meat():
    """
    Irregular organic slab of cooked beef:
    - Lumpy surface (not smooth)
    - Dark charred exterior color
    - Visible texture variation
    """
    meshes = []
    rng = np.random.default_rng(7)

    # Base: squashed sphere for organic meat shape
    meat = tc.icosphere(subdivisions=3, radius=0.06)
    verts = meat.vertices.copy()

    # Squash Y (flat slab), stretch X
    verts[:, 1] *= 0.35
    verts[:, 0] *= 1.4
    verts[:, 2] *= 1.1

    # Add bumpy surface noise
    norms = meat.vertex_normals
    for i in range(len(verts)):
        bump = rng.uniform(0, 0.012)
        verts[i] += norms[i] * bump

    # Sear marks: darken patches
    colors = np.zeros((len(verts), 4), dtype=np.uint8)
    for i, v in enumerate(verts):
        # Base: dark brown cooked meat
        r, g, b = 90, 45, 20
        # Charred spots on top surface
        if v[1] > 0.01:
            char = rng.random()
            if char > 0.6:
                r, g, b = 30, 20, 10
        # Slightly redder inside edges
        if abs(v[1]) < 0.005:
            r = min(r + 30, 255)
        colors[i] = [r, g, b, 255]

    meat = trimesh.Trimesh(vertices=verts, faces=meat.faces, vertex_colors=colors)
    meshes.append(meat)

    # Grill mark lines (flat dark strips)
    for x_off in [-0.03, 0.0, 0.03]:
        mark = tc.box(extents=[0.006, 0.003, 0.09])
        mark.apply_translation([x_off, 0.022, 0])
        mark.visual.vertex_colors = [15, 10, 8, 255]
        meshes.append(mark)

    meat_mesh = trimesh.util.concatenate(meshes)
    path = os.path.join(OUTPUT_DIR, 'cooked_meat.glb')
    meat_mesh.export(path)
    print(f"✓ Cooked meat exported: {path}")
    return path


# ─────────────────────────────────────────────
#  WOODEN WATER CUP
# ─────────────────────────────────────────────

def gen_wooden_cup():
    """
    Hand-carved wooden cup:
    - Slightly irregular cylinder (hand-made look)
    - Wood grain via vertex color variation
    - Open top, thick walls
    """
    meshes = []
    rng = np.random.default_rng(13)

    sections = 18
    outer_r = 0.045
    inner_r = 0.033
    height = 0.08

    # Outer wall
    outer = tc.cylinder(radius=outer_r, height=height, sections=sections)
    # Inner hollow
    inner = tc.cylinder(radius=inner_r, height=height * 0.95, sections=sections)
    inner.apply_translation([0, 0.002, 0])

    # Deform for hand-carved irregularity
    for mesh in [outer, inner]:
        verts = mesh.vertices.copy()
        for i, v in enumerate(verts):
            angle = math.atan2(v[2], v[0])
            wobble = math.sin(angle * 6) * 0.002 + rng.uniform(-0.001, 0.001)
            r = math.sqrt(v[0]**2 + v[2]**2)
            if r > 0:
                verts[i][0] += (v[0]/r) * wobble
                verts[i][2] += (v[2]/r) * wobble
        mesh.vertices = verts

    # Wood color with grain variation
    def wood_colors(mesh):
        colors = np.zeros((len(mesh.vertices), 4), dtype=np.uint8)
        for i, v in enumerate(mesh.vertices):
            grain = math.sin(v[1] * 80 + v[0] * 20) * 15
            r = int(np.clip(120 + grain + rng.uniform(-5, 5), 80, 160))
            g = int(np.clip(80 + grain * 0.7 + rng.uniform(-5, 5), 50, 110))
            b = int(np.clip(40 + grain * 0.3, 20, 60))
            colors[i] = [r, g, b, 255]
        mesh.visual.vertex_colors = colors

    wood_colors(outer)
    wood_colors(inner)

    # Bottom disc
    bottom = tc.cylinder(radius=outer_r * 0.98, height=0.008, sections=sections)
    bottom.apply_translation([0, -height/2 + 0.004, 0])
    wood_colors(bottom)

    # Water surface (subtle blue plane inside)
    water = tc.cylinder(radius=inner_r * 0.95, height=0.003, sections=sections)
    water.apply_translation([0, height/2 - 0.015, 0])
    water.visual.vertex_colors = [40, 100, 180, 200]

    cup = trimesh.util.concatenate([outer, bottom, water])
    path = os.path.join(OUTPUT_DIR, 'wooden_cup.glb')
    cup.export(path)
    print(f"✓ Wooden cup exported: {path}")
    return path


# ─────────────────────────────────────────────
#  JUNGLE TREE
# ─────────────────────────────────────────────

def gen_jungle_tree(seed=0):
    """
    Procedural jungle tree:
    - Thick tapered trunk with bark texture via vertex color
    - Branching structure
    - Canopy cluster of leaf spheres
    """
    meshes = []
    rng = np.random.default_rng(seed)

    # Trunk
    trunk_h = rng.uniform(4.0, 8.0)
    trunk_r_base = rng.uniform(0.18, 0.35)
    trunk_r_top = trunk_r_base * rng.uniform(0.4, 0.65)

    trunk = tc.cone(
        radius=trunk_r_base,
        height=trunk_h,
        sections=10
    )
    # Move pivot to base
    trunk.apply_translation([0, trunk_h/2, 0])

    # Bark color: dark brown with variation
    bark_colors = np.zeros((len(trunk.vertices), 4), dtype=np.uint8)
    for i, v in enumerate(trunk.vertices):
        t = v[1] / trunk_h
        grain = math.sin(v[1] * 15 + math.atan2(v[2], v[0]) * 3) * 12
        r = int(np.clip(70 + grain + rng.uniform(-8, 8), 40, 100))
        g = int(np.clip(45 + grain * 0.6, 25, 65))
        b = int(np.clip(20 + grain * 0.2, 10, 35))
        bark_colors[i] = [r, g, b, 255]
    trunk.visual.vertex_colors = bark_colors
    meshes.append(trunk)

    # Canopy: cluster of overlapping leaf spheres
    canopy_y = trunk_h * 0.85
    n_clusters = int(rng.uniform(5, 10))
    for _ in range(n_clusters):
        cr = rng.uniform(0.8, 2.0)
        cx = rng.uniform(-1.5, 1.5)
        cy = canopy_y + rng.uniform(0, 2.5)
        cz = rng.uniform(-1.5, 1.5)
        leaf = tc.icosphere(subdivisions=2, radius=cr)
        leaf.apply_translation([cx, cy, cz])
        # Jungle green variation
        lc = np.zeros((len(leaf.vertices), 4), dtype=np.uint8)
        for i in range(len(leaf.vertices)):
            r = int(rng.uniform(20, 50))
            g = int(rng.uniform(80, 140))
            b = int(rng.uniform(20, 50))
            lc[i] = [r, g, b, 255]
        leaf.visual.vertex_colors = lc
        meshes.append(leaf)

    # Surface roots (buttress)
    for angle in np.linspace(0, 2*math.pi, 5, endpoint=False):
        root_x = math.cos(angle) * trunk_r_base * 2.5
        root_z = math.sin(angle) * trunk_r_base * 2.5
        root = tc.box(extents=[0.06, 0.6, trunk_r_base * 2])
        root.apply_translation([root_x, 0.3, root_z])
        import trimesh.transformations as tft
        root.apply_transform(tft.rotation_matrix(angle, [0,1,0]))
        root.visual.vertex_colors = [65, 40, 18, 255]
        meshes.append(root)

    tree = trimesh.util.concatenate(meshes)
    path = os.path.join(OUTPUT_DIR, f'tree_{seed}.glb')
    tree.export(path)
    print(f"✓ Tree {seed} exported: {path}")
    return path


# ─────────────────────────────────────────────
#  ROCK
# ─────────────────────────────────────────────

def gen_rock(seed=0, size=1.0):
    """Realistic jagged rock with moss patches"""
    rng = np.random.default_rng(seed + 100)
    rock = tc.icosphere(subdivisions=3, radius=size * 0.5)
    verts = rock.vertices.copy()
    norms = rock.vertex_normals.copy()

    for i, v in enumerate(verts):
        noise = rng.uniform(0.85, 1.15)
        high_freq = rng.uniform(-0.04, 0.04) * size
        verts[i] = v * noise + norms[i] * high_freq

    # Flatten bottom
    verts[:, 1] = np.where(verts[:, 1] < -size * 0.2,
                            -size * 0.2, verts[:, 1])

    # Colors: grey stone with green moss on top
    colors = np.zeros((len(verts), 4), dtype=np.uint8)
    for i, v in enumerate(verts):
        if v[1] > size * 0.15 and rng.random() > 0.4:
            # moss
            r, g, b = int(rng.uniform(30, 60)), int(rng.uniform(70, 100)), int(rng.uniform(20, 40))
        else:
            # grey stone
            base = int(rng.uniform(90, 140))
            r, g, b = base, base, int(base * 0.95)
        colors[i] = [r, g, b, 255]

    rock = trimesh.Trimesh(vertices=verts, faces=rock.faces, vertex_colors=colors)
    path = os.path.join(OUTPUT_DIR, f'rock_{seed}.glb')
    rock.export(path)
    print(f"✓ Rock {seed} exported: {path}")
    return path


# ─────────────────────────────────────────────
#  GENERATE ALL ASSETS
# ─────────────────────────────────────────────

def generate_all():
    ensure_output()
    print("\n🌿 Generating Luo World 3D Assets...\n")
    gen_stone_axe()
    gen_cooked_meat()
    gen_wooden_cup()
    for i in range(8):
        gen_jungle_tree(seed=i)
    for i in range(5):
        gen_rock(seed=i, size=0.5 + i * 0.3)
    print("\n✅ All assets generated!\n")


if __name__ == '__main__':
    generate_all()
