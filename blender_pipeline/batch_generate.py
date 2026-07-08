import bpy, sys, os, math, random, bmesh, mathutils
sys.path.insert(0, "/home/claude/luo-world/blender_pipeline")
from lib import clear_scene, make_material, frame_camera_to_objects, setup_render, add_sun, export_glb

OUT = "/home/claude/luo-world/blender_pipeline"

def build_tree(seed, tree_type="oak"):
    rng = random.Random(seed)
    parts = []
    height = rng.uniform(4.2, 6.5) if tree_type != "palm" else rng.uniform(6, 8)
    radius = rng.uniform(0.22, 0.34)
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=radius, depth=height, location=(0,0,height/2))
    trunk = bpy.context.active_object
    trunk.name = "Trunk"
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(trunk.data)
    bm.verts.ensure_lookup_table()
    lean_dir = rng.uniform(0, math.pi*2)
    lean_amt = rng.uniform(0.35, 0.75)
    for v in bm.verts:
        t = (v.co.z + height/2) / height
        if t > 0.5:
            taper = 1.0 - (t-0.5)/0.5 * (0.7 if tree_type=="palm" else 0.6)
            v.co.x *= taper; v.co.y *= taper
        v.co.x += math.cos(lean_dir) * (t*t) * lean_amt
        v.co.y += math.sin(lean_dir) * (t*t) * lean_amt
    bmesh.update_edit_mesh(trunk.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    bark_dark = rng.uniform(0.09, 0.20)
    trunk_mat = make_material(f"Bark_{seed}", (bark_dark, bark_dark*0.65, bark_dark*0.4), roughness=0.95)
    trunk.data.materials.append(trunk_mat)
    bpy.ops.object.shade_flat()
    parts.append(trunk)
    trunk_top = (math.cos(lean_dir)*lean_amt, math.sin(lean_dir)*lean_amt, height)
    canopy_center = (trunk_top[0]*1.25, trunk_top[1]*1.25, trunk_top[2] + (0.7 if tree_type!="palm" else 0.2))

    if tree_type == "palm":
        n_fronds = rng.randint(6, 9)
        for i in range(n_fronds):
            ang = (i / n_fronds) * math.pi * 2 + rng.uniform(-0.2,0.2)
            droop = rng.uniform(0.3, 0.6)
            length = rng.uniform(2.2, 3.2)
            bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.5, radius2=0.02, depth=length,
                location=(canopy_center[0]+math.cos(ang)*length*0.4,
                          canopy_center[1]+math.sin(ang)*length*0.4,
                          canopy_center[2]-droop*length*0.4))
            frond = bpy.context.active_object
            frond.rotation_euler = (math.pi/2 - droop, 0, ang)
            frond.scale = (1, 0.15, 1)
            g = rng.uniform(0.32, 0.45)
            fmat = make_material(f"Frond_{seed}_{i}", (0.06, g, 0.08), roughness=0.8)
            frond.data.materials.append(fmat)
            bpy.ops.object.shade_flat()
            parts.append(frond)
    else:
        cluster_offsets = [(0,0,0,1.5),(0.55,0.25,0.3,1.1),(-0.5,-0.3,0.25,1.05),
                           (0.15,0.55,-0.15,0.95),(-0.4,0.4,-0.25,0.9),(0.35,-0.5,0.05,1.0)]
        n_use = rng.randint(4,6)
        size_mult = rng.uniform(0.85, 1.25)
        for i,(dx,dy,dz,r) in enumerate(cluster_offsets[:n_use]):
            jitter = 0.12
            pos = (canopy_center[0]+dx*size_mult+rng.uniform(-jitter,jitter),
                   canopy_center[1]+dy*size_mult+rng.uniform(-jitter,jitter),
                   canopy_center[2]+dz*size_mult+rng.uniform(-jitter,jitter))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r*size_mult*rng.uniform(0.92,1.08), location=pos)
            leaf = bpy.context.active_object
            leaf.scale = (1,1,0.82)
            g = rng.uniform(0.26, 0.48)
            leaf_mat = make_material(f"Leaf_{seed}_{i}", (0.03+rng.uniform(0,0.05), g, 0.04+rng.uniform(0,0.04)), roughness=0.85)
            leaf.data.materials.append(leaf_mat)
            bpy.ops.object.shade_flat()
            parts.append(leaf)
            bx,by,bz = trunk_top
            length = math.sqrt((pos[0]-bx)**2+(pos[1]-by)**2+(pos[2]-bz)**2)*0.9
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=0.10, radius2=0.035, depth=max(length,0.3),
                location=((bx+pos[0])/2,(by+pos[1])/2,(bz+pos[2])/2))
            branch = bpy.context.active_object
            vec = mathutils.Vector((pos[0]-bx,pos[1]-by,pos[2]-bz))
            branch.rotation_euler = mathutils.Vector((0,0,1)).rotation_difference(vec).to_euler()
            branch.data.materials.append(trunk_mat)
            bpy.ops.object.shade_flat()
            parts.append(branch)

    bpy.ops.object.empty_add(location=(0,0,0))
    root = bpy.context.active_object
    root.name = f"Tree_{tree_type}_{seed}"
    for p in parts: p.parent = root
    return root, parts

def build_rock(seed, size=1.0):
    rng = random.Random(seed+500)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=size*0.5)
    rock = bpy.context.active_object
    rock.name = f"Rock_{seed}"
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(rock.data)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        n = v.co.normalized()
        disp = rng.uniform(-0.18, 0.28) * size
        v.co += n * disp
        if v.co.z < -size*0.15:
            v.co.z = -size*0.15 - rng.uniform(0,0.05)*size
    bmesh.update_edit_mesh(rock.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    base_grey = rng.uniform(0.32, 0.5)
    mat = make_material(f"Stone_{seed}", (base_grey, base_grey*0.97, base_grey*0.92), roughness=0.9)
    rock.data.materials.append(mat)
    moss_mat = make_material(f"Moss_{seed}", (0.10+rng.uniform(0,0.05), rng.uniform(0.28,0.4), 0.08), roughness=0.95)
    rock.data.materials.append(moss_mat)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(rock.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        if f.normal.z > 0.55 and rng.random() > 0.35:
            f.select = True
    bmesh.update_edit_mesh(rock.data)
    bpy.context.object.active_material_index = 1
    bpy.ops.object.material_slot_assign()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_flat()
    return rock, [rock]
