"""
HUD - Desktop only (Ursina)
Stub on Android - Android uses Kivy HUD in main.py
"""
try:
    from ursina import *
    HAS_URSINA = True
except ImportError:
    HAS_URSINA = False

from game.inventory import ITEMS

class HUD:
    def __init__(self, player=None, inventory=None):
        self.player    = player
        self.inventory = inventory
        if not HAS_URSINA:
            return
        self._build_crosshair()
        self._build_stat_bars()
        self._build_hotbar()
        self._build_interaction_prompt()
        self._build_time_display()

    def _build_crosshair(self):
        if not HAS_URSINA: return
        size = 0.012; thickness = 0.002; col = color.rgba(255,255,255,200)
        self.ch_h = Entity(parent=camera.ui, model='quad', color=col,
                           scale=(size,thickness), position=(0,0,-0.1))
        self.ch_v = Entity(parent=camera.ui, model='quad', color=col,
                           scale=(thickness,size), position=(0,0,-0.1))

    def _build_stat_bars(self):
        if not HAS_URSINA: return
        pass

    def _build_hotbar(self):
        if not HAS_URSINA: return
        pass

    def _build_interaction_prompt(self):
        if not HAS_URSINA: return
        self.interact_text = Text('', parent=camera.ui,
                                  position=(0,-0.12,-0.1), scale=1.4,
                                  origin=(0,0), background=True)

    def _build_time_display(self):
        if not HAS_URSINA: return
        self.time_text = Text('10:00', parent=camera.ui,
                              position=(0.78,0.46,-0.1), scale=1.2, origin=(0,0))

    def update(self):
        pass

    def set_interact_prompt(self, text):
        if HAS_URSINA and hasattr(self, 'interact_text'):
            self.interact_text.text = text

    def handle_input(self, key):
        pass
