"""Reusable Blender asset-generation library for Luo World."""
import bpy, math, random, bmesh, mathutils

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)

def make_material(name, color, roughness=0.9, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def frame_camera_to_objects(objects, margin=1.35):
    min_c = mathutils.Vector((1e9, 1e9, 1e9))
    max_c = mathutils.Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ mathutils.Vector(corner)
            min_c.x = min(min_c.x, world_co.x); max_c.x = max(max_c.x, world_co.x)
            min_c.y = min(min_c.y, world_co.y); max_c.y = max(max_c.y, world_co.y)
            min_c.z = min(min_c.z, world_co.z); max_c.z = max(max_c.z, world_co.z)
    center = (min_c + max_c) / 2
    size = max((max_c - min_c).length, 0.5) * margin
    cam_pos = center + mathutils.Vector((size*0.75, -size*1.15, size*0.55))
    bpy.ops.object.camera_add(location=cam_pos)
    cam = bpy.context.active_object
    direction = center - cam_pos
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
    cam.data.lens = 35
    bpy.context.scene.camera = cam
    return cam

def setup_render(filepath, res=640):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.55,0.68,0.78,1)
    scene.render.filepath = filepath

def add_sun(energy=4.0):
    bpy.ops.object.light_add(type='SUN', location=(4,-4,6))
    bpy.context.object.data.energy = energy
    bpy.context.object.rotation_euler = (0.85, 0, 0.75)

def export_glb(objects, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLB', use_selection=True)
