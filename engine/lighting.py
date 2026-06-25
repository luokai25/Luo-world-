"""
Lighting System - Desktop only (Ursina)
Stub on Android
"""
try:
    from ursina import *
    from ursina.lights import DirectionalLight, AmbientLight
    HAS_URSINA = True
except ImportError:
    HAS_URSINA = False

import math

class LightingSystem:
    def __init__(self):
        self.time_of_day = 10.0
        self.day_speed   = 0.5
        if not HAS_URSINA:
            return
        self._setup_sun()
        self._setup_ambient()
        self._setup_fog()

    def _setup_sun(self):
        if not HAS_URSINA: return
        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(-0.4,-1,-0.6))
        self.sun.color = color.rgb(255,248,220)
        self.sun.shadows = True

    def _setup_ambient(self):
        if not HAS_URSINA: return
        self.ambient = AmbientLight()
        self.ambient.color = color.rgb(80,110,140)

    def _setup_fog(self):
        if not HAS_URSINA: return
        scene.fog_color   = color.rgb(180,210,190)
        scene.fog_density = 0.015

    def update(self):
        if not HAS_URSINA: return
        self.time_of_day += time.dt * self.day_speed / 60.0
        if self.time_of_day >= 24.0:
            self.time_of_day = 0.0

    @property
    def hour_str(self):
        h = int(self.time_of_day)
        m = int((self.time_of_day - h) * 60)
        return f"{h:02d}:{m:02d}"
