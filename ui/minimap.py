"""
Minimap - Live top-down world overview
Shows: player position, trees, rocks, water, animals, POIs
Tap to open fullscreen map
"""

from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import (
    Color, Ellipse, Rectangle, Line,
    RoundedRectangle, PushMatrix, PopMatrix, Translate, Scale
)
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
import math


# Color palette for map features
MAP_COLORS = {
    'tree':         (0.15, 0.55, 0.15, 0.9),
    'rock':         (0.55, 0.55, 0.55, 0.9),
    'water_source': (0.2,  0.5,  0.9,  0.85),
    'bush':         (0.2,  0.7,  0.2,  0.8),
    'item':         (0.9,  0.85, 0.2,  0.9),
    'deer':         (0.8,  0.65, 0.3,  0.9),
    'boar':         (0.6,  0.35, 0.2,  0.9),
    'rabbit':       (0.85, 0.75, 0.6,  0.85),
    'bird':         (0.7,  0.8,  0.9,  0.85),
}

BIOME_COLORS = {
    'dense_jungle': (0.08, 0.22, 0.08),
    'rainforest':   (0.06, 0.28, 0.10),
    'clearing':     (0.22, 0.32, 0.12),
    'rocky_hills':  (0.22, 0.20, 0.16),
    'swamp':        (0.10, 0.18, 0.14),
}


class MinimapWidget(Widget):
    """
    Small always-visible minimap (top-right corner).
    Shows player dot + nearby objects + compass.
    """

    MAP_SIZE   = dp(160)
    MAP_RADIUS = dp(80)

    def __init__(self, game_state, **kwargs):
        super().__init__(**kwargs)
        self.game_state   = game_state
        self.world_size   = 512
        self.view_range   = 120    # world units shown on minimap
        self._expanded    = False

        w, h = Window.size
        self.size      = (self.MAP_SIZE, self.MAP_SIZE)
        self.pos       = (w - self.MAP_SIZE - dp(8), h - self.MAP_SIZE - dp(8))

        Clock.schedule_interval(self._redraw, 1.0 / 10.0)  # 10fps is fine for minimap
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        gs  = self.game_state
        px  = gs.player.x
        pz  = gs.player.z
        pyw = gs.player.yaw

        cx = self.center_x
        cy = self.center_y
        r  = self.MAP_RADIUS

        with self.canvas:
            # ── Background circle ──
            Color(0.05, 0.1, 0.05, 0.88)
            Ellipse(pos=(cx - r, cy - r), size=(r*2, r*2))

            # ── Border ──
            Color(0.3, 0.6, 0.25, 1)
            Line(circle=(cx, cy, r - dp(1)), width=dp(1.5))

            # ── Draw world objects in range ──
            half_range = self.view_range / 2
            scale = r / half_range

            for obj in gs.world.active_objects:
                ox = obj.x - px
                oz = obj.z - pz
                if abs(ox) > half_range or abs(oz) > half_range:
                    continue

                sx = cx + ox * scale
                sy = cy - oz * scale   # Z is depth in world → Y on screen

                # Skip if outside circle
                if math.sqrt((sx-cx)**2 + (sy-cy)**2) > r:
                    continue

                col = MAP_COLORS.get(obj.type, (0.8, 0.8, 0.8, 0.7))
                Color(*col)

                if obj.type == 'tree':
                    dot_r = dp(2.5)
                elif obj.type == 'rock':
                    dot_r = dp(2)
                elif obj.type == 'water_source':
                    dot_r = dp(3)
                else:
                    dot_r = dp(1.8)

                Ellipse(pos=(sx - dot_r, sy - dot_r), size=(dot_r*2, dot_r*2))

            # ── Animals ──
            for animal in gs.world.active_animals:
                ox = animal.x - px
                oz = animal.z - pz
                if abs(ox) > half_range or abs(oz) > half_range:
                    continue
                sx = cx + ox * scale
                sy = cy - oz * scale
                if math.sqrt((sx-cx)**2 + (sy-cy)**2) > r:
                    continue
                col = MAP_COLORS.get(animal.type, (0.8, 0.7, 0.3, 0.9))
                Color(*col)
                dot_r = dp(2.2)
                Ellipse(pos=(sx-dot_r, sy-dot_r), size=(dot_r*2, dot_r*2))

            # ── Player dot + direction arrow ──
            Color(1, 1, 1, 1)
            pd = dp(4)
            Ellipse(pos=(cx - pd, cy - pd), size=(pd*2, pd*2))

            # Direction indicator
            yaw_rad = math.radians(pyw)
            ax = cx + math.sin(yaw_rad) * dp(10)
            ay = cy + math.cos(yaw_rad) * dp(10)
            Color(1, 0.9, 0.2, 1)
            Line(points=[cx, cy, ax, ay], width=dp(1.5))

            # ── Compass N ──
            Color(1, 0.4, 0.4, 1)
            # North dot (top of minimap = north)
            nd = dp(3)
            Ellipse(pos=(cx - nd, cy + r - dp(10) - nd),
                    size=(nd*2, nd*2))

        # Compass label drawn via canvas
        # (Text requires Label widget; add as overlay)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._toggle_expand()
            return True

    def _toggle_expand(self):
        self._expanded = not self._expanded
        w, h = Window.size
        if self._expanded:
            anim_size = (min(w, h) * 0.9, min(w, h) * 0.9)
            new_pos = (w/2 - anim_size[0]/2, h/2 - anim_size[1]/2)
            self.MAP_RADIUS = anim_size[0] / 2 - dp(4)
            self.view_range = 300
        else:
            anim_size = (self.MAP_SIZE, self.MAP_SIZE)
            new_pos = (w - self.MAP_SIZE - dp(8), h - self.MAP_SIZE - dp(8))
            self.MAP_RADIUS = dp(80)
            self.view_range = 120
        self.size = anim_size
        self.pos  = new_pos
        self._redraw()
