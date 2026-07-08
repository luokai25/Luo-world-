import bpy, sys, os, math, random, bmesh, mathutils
sys.path.insert(0, "/home/claude/luo-world/blender_pipeline")
from lib import clear_scene, make_material, frame_camera_to_objects, setup_render, add_sun, export_glb
from batch_generate import build_tree, build_rock

OUT_MODELS = "/home/claude/luo-world/assets/models"
os.makedirs(OUT_MODELS, exist_ok=True)

tree_specs = [("oak",1),("oak",2),("oak",3),("oak",4),("oak",20),("palm",10),("palm",11),("palm",12)]
for ttype, seed in tree_specs:
    clear_scene()
    root, parts = build_tree(seed, ttype)
    export_glb(parts, f"{OUT_MODELS}/tree_{ttype}_{seed}.glb")
    print(f"EXPORTED tree_{ttype}_{seed}.glb")

for i in range(6):
    clear_scene()
    rock, parts = build_rock(seed=i, size=0.5+i*0.25)
    export_glb(parts, f"{OUT_MODELS}/rock_{i}.glb")
    print(f"EXPORTED rock_{i}.glb")

def build_farm_plot(seed=1):
    rng = random.Random(seed+900)
    parts = []
    bpy.ops.mesh.primitive_plane_add(size=1.8, location=(0,0,0.01))
    soil = bpy.context.active_object
    soil.name = "FarmSoil"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=6)
    bm = bmesh.from_edit_mesh(soil.data)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.co.z += rng.uniform(-0.025, 0.03)
    bmesh.update_edit_mesh(soil.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    soil_mat = make_material("Soil", (0.16, 0.10, 0.06), roughness=1.0)
    soil.data.materials.append(soil_mat)
    bpy.ops.object.shade_flat()
    parts.append(soil)
    for i in range(4):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.08, depth=1.7,
            location=(-0.65+i*0.43, 0, 0.04), rotation=(math.pi/2,0,0))
        ridge = bpy.context.active_object
        ridge.data.materials.append(soil_mat)
        bpy.ops.object.shade_flat()
        parts.append(ridge)
    bpy.ops.object.empty_add(location=(0,0,0))
    root = bpy.context.active_object
    root.name = "FarmPlot"
    for p in parts: p.parent = root
    return root, parts

clear_scene()
root, parts = build_farm_plot()
export_glb(parts, f"{OUT_MODELS}/farm_plot.glb")
print("EXPORTED farm_plot.glb")

def build_crop_stage(stage, seed=1, crop_type="grain"):
    rng = random.Random(seed*10+stage)
    parts = []
    colors = {"grain": (0.55, 0.45, 0.12), "berry_bush": (0.15, 0.35, 0.12)}
    base_col = colors.get(crop_type, (0.2,0.4,0.15))
    if stage == 0:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.04, location=(0,0,0.02))
        p = bpy.context.active_object
        mat = make_material(f"Seed_{seed}", (0.12,0.08,0.05), roughness=1.0)
        p.data.materials.append(mat); bpy.ops.object.shade_flat(); parts.append(p)
    elif stage == 1:
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.03, radius2=0.005, depth=0.15, location=(0,0,0.075))
        p = bpy.context.active_object
        mat = make_material(f"Sprout_{seed}", (0.25,0.55,0.2), roughness=0.8)
        p.data.materials.append(mat); bpy.ops.object.shade_flat(); parts.append(p)
    elif stage == 2:
        for i in range(3):
            ang = i/3*math.pi*2
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.05, radius2=0.008, depth=0.35,
                location=(math.cos(ang)*0.05, math.sin(ang)*0.05, 0.175))
            p = bpy.context.active_object
            p.rotation_euler = (rng.uniform(-0.2,0.2), rng.uniform(-0.2,0.2), ang)
            mat = make_material(f"Young_{seed}_{i}", (0.22,0.5,0.18), roughness=0.8)
            p.data.materials.append(mat); bpy.ops.object.shade_flat(); parts.append(p)
    elif stage == 3:
        for i in range(5):
            ang = i/5*math.pi*2
            h = rng.uniform(0.5,0.65)
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.06, radius2=0.01, depth=h,
                location=(math.cos(ang)*0.08, math.sin(ang)*0.08, h/2))
            p = bpy.context.active_object
            p.rotation_euler = (rng.uniform(-0.15,0.15), rng.uniform(-0.15,0.15), ang)
            mat = make_material(f"Mature_{seed}_{i}", (0.30,0.48,0.15), roughness=0.75)
            p.data.materials.append(mat); bpy.ops.object.shade_flat(); parts.append(p)
    elif stage == 4:
        for i in range(5):
            ang = i/5*math.pi*2
            h = rng.uniform(0.55,0.7)
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.06, radius2=0.01, depth=h,
                location=(math.cos(ang)*0.08, math.sin(ang)*0.08, h/2))
            p = bpy.context.active_object
            p.rotation_euler = (rng.uniform(-0.15,0.15), rng.uniform(-0.15,0.15), ang)
            mat = make_material(f"Ripe_{seed}_{i}", base_col, roughness=0.6)
            p.data.materials.append(mat); bpy.ops.object.shade_flat(); parts.append(p)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.09, location=(0,0,0.65))
        fruit = bpy.context.active_object
        fmat = make_material(f"Fruit_{seed}", (0.75,0.55,0.1), roughness=0.5)
        fruit.data.materials.append(fmat); bpy.ops.object.shade_flat(); parts.append(fruit)
    bpy.ops.object.empty_add(location=(0,0,0))
    root = bpy.context.active_object
    root.name = f"Crop_stage{stage}"
    for p in parts: p.parent = root
    return root, parts

stage_names = ["seed","sprout","young","mature","ripe"]
for stage in range(5):
    clear_scene()
    root, parts = build_crop_stage(stage, seed=1, crop_type="grain")
    export_glb(parts, f"{OUT_MODELS}/crop_grain_{stage_names[stage]}.glb")
    print(f"EXPORTED crop_grain_{stage_names[stage]}.glb")

print("ALL_ASSETS_FINALIZED")
