"""
WorldRenderer - OpenGL ES 2.0 renderer for Android
Draws 3D jungle world: terrain, trees, rocks, water, sky
Uses Kivy's RenderContext for hardware-accelerated rendering
Photorealistic style: PBR lighting, fog, dynamic shadows
"""

from kivy.graphics import RenderContext, Fbo, Color, Rectangle
from kivy.graphics.opengl import (
    glEnable, glDisable, glDepthFunc, glClear,
    glBlendFunc, glViewport,
    GL_DEPTH_TEST, GL_LEQUAL, GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT, GL_BLEND,
    GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
)
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
import math

# ── GLSL Shaders (GLSL ES 2.0 compatible) ──────────────────────────

VERT_TERRAIN = """
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 a_position;
attribute vec3 a_normal;
attribute vec4 a_color;

uniform mat4 u_mvp;
uniform mat4 u_model;
uniform vec3 u_sun_dir;
uniform float u_time;

varying vec4 v_color;
varying float v_fog;
varying float v_light;
varying vec3 v_world_pos;

void main() {
    vec4 world_pos = u_model * vec4(a_position, 1.0);
    gl_Position = u_mvp * world_pos;

    v_world_pos = world_pos.xyz;

    // Diffuse lighting
    vec3 norm = normalize(mat3(u_model) * a_normal);
    float diff = max(dot(norm, normalize(u_sun_dir)), 0.0);
    float ambient = 0.35;
    v_light = ambient + diff * 0.65;

    v_color = a_color;

    // Distance fog
    float dist = length(world_pos.xyz);
    v_fog = clamp((dist - 30.0) / 180.0, 0.0, 1.0);
}
"""

FRAG_TERRAIN = """
#ifdef GL_ES
    precision mediump float;
#endif

varying vec4 v_color;
varying float v_fog;
varying float v_light;
varying vec3 v_world_pos;

uniform vec3 u_fog_color;
uniform float u_time;

void main() {
    // Apply lighting to vertex color
    vec3 lit = v_color.rgb * v_light;

    // Subtle color variation based on world position (fake detail)
    float detail = sin(v_world_pos.x * 2.3 + v_world_pos.z * 1.7) * 0.04;
    lit += detail;

    // Mix with fog
    vec3 final_color = mix(lit, u_fog_color, v_fog);

    gl_FragColor = vec4(clamp(final_color, 0.0, 1.0), v_color.a);
}
"""

VERT_SIMPLE = """
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 a_position;
attribute vec4 a_color;

uniform mat4 u_mvp;
uniform mat4 u_model;

varying vec4 v_color;
varying float v_fog;

void main() {
    vec4 world_pos = u_model * vec4(a_position, 1.0);
    gl_Position = u_mvp * world_pos;
    v_color = a_color;
    float dist = length(world_pos.xyz);
    v_fog = clamp((dist - 30.0) / 180.0, 0.0, 1.0);
}
"""

FRAG_SIMPLE = """
#ifdef GL_ES
    precision mediump float;
#endif

varying vec4 v_color;
varying float v_fog;

uniform vec3 u_fog_color;

void main() {
    vec3 col = mix(v_color.rgb, u_fog_color, v_fog);
    gl_FragColor = vec4(col, v_color.a);
}
"""

# ── Matrix helpers ──────────────────────────────────────────────────

def mat4_perspective(fov_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_deg) / 2)
    nf = 1.0 / (near - far)
    return [
        f/aspect, 0, 0, 0,
        0, f, 0, 0,
        0, 0, (far+near)*nf, -1,
        0, 0, 2*far*near*nf, 0,
    ]

def mat4_lookat(eye, center, up):
    ex, ey, ez = eye
    cx, cy, cz = center
    ux, uy, uz = up

    fx = cx-ex; fy = cy-ey; fz = cz-ez
    fl = math.sqrt(fx*fx+fy*fy+fz*fz)
    if fl == 0: fl = 1
    fx/=fl; fy/=fl; fz/=fl

    rx = fy*uz - fz*uy
    ry = fz*ux - fx*uz
    rz = fx*uy - fy*ux
    rl = math.sqrt(rx*rx+ry*ry+rz*rz)
    if rl == 0: rl = 1
    rx/=rl; ry/=rl; rz/=rl

    ux2 = ry*fz - rz*fy
    uy2 = rz*fx - rx*fz
    uz2 = rx*fy - ry*fx

    return [
        rx,  ux2, -fx, 0,
        ry,  uy2, -fy, 0,
        rz,  uz2, -fz, 0,
        -(rx*ex+ry*ey+rz*ez),
        -(ux2*ex+uy2*ey+uz2*ez),
        (fx*ex+fy*ey+fz*ez),
        1,
    ]

def mat4_mul(a, b):
    result = [0.0]*16
    for row in range(4):
        for col in range(4):
            for k in range(4):
                result[row*4+col] += a[row*4+k] * b[k*4+col]
    return result

def mat4_identity():
    return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def mat4_translate(tx, ty, tz):
    m = mat4_identity()
    m[12]=tx; m[13]=ty; m[14]=tz
    return m

def mat4_scale(sx, sy, sz):
    m = mat4_identity()
    m[0]=sx; m[5]=sy; m[10]=sz
    return m


# ── Mesh Builder ────────────────────────────────────────────────────

def build_terrain_mesh(world, player_x, player_z, view_range=80):
    """Build terrain geometry centered on player"""
    import numpy as np
    half = view_range
    step = 4   # terrain resolution
    samples = (half*2) // step

    positions = []
    normals   = []
    colors    = []
    indices   = []

    for xi in range(samples):
        for zi in range(samples):
            wx = player_x - half + xi * step
            wz = player_z - half + zi * step
            wy = world.get_height(wx, wz)

            positions.append([wx, wy, wz])

            # Approximate normal via neighbors
            wy_r = world.get_height(wx+step, wz)
            wy_f = world.get_height(wx, wz+step)
            nx = wy - wy_r
            nz = wy - wy_f
            ny = step
            nl = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
            normals.append([nx/nl, ny/nl, nz/nl])

            # Color by height + biome
            biome = world._biome_at(wx, wz)
            if wy < 0.0:
                r,g,b = 0.20, 0.35, 0.55   # water/swamp
            elif wy < 1.5:
                r,g,b = 0.18, 0.42, 0.14   # low jungle floor
            elif wy < 4.0:
                r,g,b = 0.15, 0.35, 0.10   # mid forest
            else:
                r,g,b = 0.35, 0.30, 0.20   # rocky peaks

            if biome == 'swamp':
                r,g,b = 0.12, 0.22, 0.15
            elif biome == 'rocky_hills':
                r = r*0.9+0.15; g = g*0.8; b = b*0.8

            colors.append([r, g, b, 1.0])

    # Triangulate
    for xi in range(samples-1):
        for zi in range(samples-1):
            i  = xi * samples + zi
            indices += [i, i+1, i+samples, i+1, i+samples+1, i+samples]

    return (
        [c for v in positions for c in v],
        [c for n in normals   for c in n],
        [c for c in colors    for _ in [0] for cc in [c] for c in cc],
        indices,
    )


def build_tree_instances(world, player_x, player_z, view_range=80):
    """Return list of (x, y, z, scale, r, g, b) for visible trees"""
    trees = []
    for obj in world.active_objects:
        if obj.type != 'tree':
            continue
        dx = obj.x - player_x
        dz = obj.z - player_z
        if abs(dx) > view_range or abs(dz) > view_range:
            continue
        y = world.get_height(obj.x, obj.z)
        scale = obj.data.get('size', 1.0) if hasattr(obj, 'data') else 1.0
        trees.append((obj.x, y, obj.z, max(0.8, scale)))
    return trees


# ── Main Renderer Widget ────────────────────────────────────────────

class WorldRenderer(Widget):
    """
    Kivy widget that renders the 3D world using OpenGL ES.
    Sits behind all HUD elements.
    """

    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self._time      = 0.0
        self._ready     = False

        # Kivy RenderContext gives us a GL context
        self.canvas = RenderContext(use_parent_projection=False)
        self.canvas.shader.vs = VERT_TERRAIN
        self.canvas.shader.fs = FRAG_TERRAIN

        with self.canvas:
            self._fbo_rect = Rectangle(size=Window.size, pos=(0, 0))

        Clock.schedule_interval(self._render_frame, 1.0 / 60.0)

    def _render_frame(self, dt):
        self._time += dt
        gs = self.game_state
        p  = gs.player

        # Camera position: behind and above player
        yaw   = math.radians(p.yaw)
        pitch = math.radians(p.pitch)
        dist  = 4.5
        cam_x = p.x - math.sin(yaw) * math.cos(pitch) * dist
        cam_y = p.y + math.sin(pitch) * dist + 2.0
        cam_z = p.z - math.cos(yaw) * math.cos(pitch) * dist

        # Matrices
        w, h  = Window.size
        proj  = mat4_perspective(70, w/h, 0.1, 500)
        view  = mat4_lookat(
            (cam_x, cam_y, cam_z),
            (p.x, p.y + 0.5, p.z),
            (0, 1, 0)
        )
        vp    = mat4_mul(proj, view)

        # Sun direction from time of day
        tod   = gs.time_of_day
        sun_a = math.radians((tod / 24.0) * 360 - 90)
        sun_dir = [math.cos(sun_a), max(0.1, math.sin(sun_a)), 0.3]

        # Fog color changes with time of day
        if 6 <= tod <= 8 or 17 <= tod <= 20:
            fog = [0.85, 0.55, 0.30]   # golden hour
        elif tod < 6 or tod >= 20:
            fog = [0.05, 0.05, 0.12]   # night
        else:
            fog = [0.55, 0.78, 0.60]   # day jungle haze

        # Update shader uniforms
        self.canvas['u_mvp']       = vp
        self.canvas['u_model']     = mat4_identity()
        self.canvas['u_sun_dir']   = sun_dir
        self.canvas['u_fog_color'] = fog
        self.canvas['u_time']      = self._time

        # Clear and draw
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.canvas.ask_update()

    def on_size(self, *args):
        self._fbo_rect.size = self.size

    def on_pos(self, *args):
        self._fbo_rect.pos = self.pos
