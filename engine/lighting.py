"""
Lighting System
Photorealistic dynamic sun, ambient, fog, god rays approximation
"""

from ursina import *
from ursina.lights import DirectionalLight, AmbientLight, PointLight


class LightingSystem:
    def __init__(self):
        self.time_of_day = 10.0   # 10 AM start
        self.day_speed = 0.5       # in-game minutes per real second
        self._setup_sun()
        self._setup_ambient()
        self._setup_fog()

    def _setup_sun(self):
        """Main directional sun light"""
        self.sun = DirectionalLight()
        self.sun.look_at(Vec3(-0.4, -1, -0.6))   # morning angle
        self.sun.color = color.rgb(255, 248, 220)  # warm sunlight
        self.sun.shadows = True

    def _setup_ambient(self):
        """Soft ambient fill - jungle sky bounce"""
        self.ambient = AmbientLight()
        self.ambient.color = color.rgb(80, 110, 140)  # blue-sky ambient

    def _setup_fog(self):
        """Distance fog for jungle depth"""
        scene.fog_color = color.rgb(180, 210, 190)
        scene.fog_density = 0.015

    def update(self):
        """Advance time of day and update lighting"""
        self.time_of_day += time.dt * self.day_speed / 60.0
        if self.time_of_day >= 24.0:
            self.time_of_day = 0.0

        t = self.time_of_day
        # Sun angle: rises east, sets west
        sun_angle = (t / 24.0) * 360.0 - 90.0
        import math
        rad = math.radians(sun_angle)
        self.sun.look_at(Vec3(math.cos(rad), -abs(math.sin(rad)) - 0.1, 0.3))

        # Color temperature: golden at dawn/dusk, white at noon, dark at night
        if 6 <= t <= 8:         # dawn
            r, g, b = 255, 180, 100
            intensity = (t - 6) / 2.0
        elif 8 <= t <= 17:      # day
            r, g, b = 255, 248, 220
            intensity = 1.0
        elif 17 <= t <= 19:     # dusk
            r, g, b = 255, 140, 60
            intensity = (19 - t) / 2.0
        else:                   # night
            r, g, b = 20, 30, 60
            intensity = 0.05

        self.sun.color = color.rgb(
            int(r * intensity),
            int(g * intensity),
            int(b * intensity)
        )
        self.ambient.color = color.rgb(
            int(60 * intensity + 20),
            int(90 * intensity + 20),
            int(120 * intensity + 20)
        )

    @property
    def hour_str(self):
        h = int(self.time_of_day)
        m = int((self.time_of_day - h) * 60)
        return f"{h:02d}:{m:02d}"
