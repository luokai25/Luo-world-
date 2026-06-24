"""
Weather System
- Clear, Cloudy, Light Rain, Heavy Rain, Storm, Fog
- Changes every ~5-15 real minutes
- Affects: player temperature, fire (rain extinguishes),
  visibility (fog), movement speed (storm)
- Visual: sky color, rain particle hints, lightning flashes
"""

import math
import random


WEATHER_CLEAR       = 'clear'
WEATHER_CLOUDY      = 'cloudy'
WEATHER_LIGHT_RAIN  = 'light_rain'
WEATHER_HEAVY_RAIN  = 'heavy_rain'
WEATHER_STORM       = 'storm'
WEATHER_FOG         = 'fog'
WEATHER_DAWN        = 'dawn'


TRANSITIONS = {
    WEATHER_CLEAR:      [(WEATHER_CLEAR, 0.4), (WEATHER_CLOUDY, 0.4), (WEATHER_FOG, 0.2)],
    WEATHER_CLOUDY:     [(WEATHER_CLEAR, 0.3), (WEATHER_CLOUDY, 0.2), (WEATHER_LIGHT_RAIN, 0.4), (WEATHER_FOG, 0.1)],
    WEATHER_LIGHT_RAIN: [(WEATHER_CLOUDY, 0.3), (WEATHER_LIGHT_RAIN, 0.3), (WEATHER_HEAVY_RAIN, 0.3), (WEATHER_CLEAR, 0.1)],
    WEATHER_HEAVY_RAIN: [(WEATHER_LIGHT_RAIN, 0.3), (WEATHER_HEAVY_RAIN, 0.2), (WEATHER_STORM, 0.4), (WEATHER_CLOUDY, 0.1)],
    WEATHER_STORM:      [(WEATHER_HEAVY_RAIN, 0.5), (WEATHER_STORM, 0.2), (WEATHER_CLOUDY, 0.3)],
    WEATHER_FOG:        [(WEATHER_FOG, 0.3), (WEATHER_CLEAR, 0.4), (WEATHER_CLOUDY, 0.3)],
}

SKY_COLORS = {
    WEATHER_CLEAR:      {'day': (0.38, 0.65, 0.42), 'night': (0.03, 0.04, 0.12), 'dawn': (0.70, 0.45, 0.25)},
    WEATHER_CLOUDY:     {'day': (0.30, 0.40, 0.35), 'night': (0.05, 0.06, 0.10), 'dawn': (0.55, 0.38, 0.28)},
    WEATHER_LIGHT_RAIN: {'day': (0.22, 0.30, 0.32), 'night': (0.04, 0.05, 0.09), 'dawn': (0.38, 0.30, 0.28)},
    WEATHER_HEAVY_RAIN: {'day': (0.15, 0.20, 0.25), 'night': (0.03, 0.04, 0.08), 'dawn': (0.25, 0.22, 0.22)},
    WEATHER_STORM:      {'day': (0.10, 0.12, 0.18), 'night': (0.02, 0.02, 0.06), 'dawn': (0.18, 0.15, 0.18)},
    WEATHER_FOG:        {'day': (0.60, 0.65, 0.58), 'night': (0.12, 0.14, 0.15), 'dawn': (0.65, 0.60, 0.52)},
}


class Weather:
    def __init__(self, seed=42):
        self.rng     = random.Random(seed + 999)
        self.current = WEATHER_CLEAR
        self.next    = WEATHER_CLEAR

        self.transition_timer    = 0.0
        self.transition_duration = 60.0   # 60s blend between states
        self.hold_timer          = self.rng.uniform(300, 900)   # how long to hold current

        self.intensity    = 0.0    # 0.0-1.0 blend to next
        self.wind_speed   = 0.5
        self.wind_dir     = 0.0    # radians

        # Lightning state
        self.lightning_timer    = 0.0
        self.lightning_flash    = 0.0    # 0-1 flash intensity
        self.lightning_cooldown = 0.0

        # Rain particles (logical, rendered by game widget)
        self.rain_drops = []
        self._rain_timer = 0.0

    def update(self, dt, time_of_day):
        # Hold current weather
        self.hold_timer -= dt
        if self.hold_timer <= 0:
            self._transition_to_next()

        # Blend transition
        if self.transition_timer > 0:
            self.transition_timer -= dt
            self.intensity = 1.0 - (self.transition_timer / self.transition_duration)
            if self.transition_timer <= 0:
                self.current   = self.next
                self.intensity = 0.0

        # Wind
        self.wind_speed += self.rng.uniform(-0.1, 0.1) * dt
        self.wind_speed  = max(0.1, min(3.0, self.wind_speed))
        self.wind_dir   += self.rng.uniform(-0.05, 0.05) * dt

        # Lightning during storm
        if self.current == WEATHER_STORM or (
           self.next == WEATHER_STORM and self.intensity > 0.5):
            self.lightning_cooldown -= dt
            if self.lightning_cooldown <= 0:
                self.lightning_flash    = 1.0
                self.lightning_cooldown = self.rng.uniform(4, 20)
                self.lightning_timer    = 0.3

        if self.lightning_timer > 0:
            self.lightning_timer -= dt
            self.lightning_flash = self.lightning_timer / 0.3
        else:
            self.lightning_flash = 0.0

    def _transition_to_next(self):
        options = TRANSITIONS.get(self.current, [(WEATHER_CLEAR, 1.0)])
        total   = sum(w for _, w in options)
        r       = self.rng.uniform(0, total)
        cumul   = 0
        for weather, weight in options:
            cumul += weight
            if r <= cumul:
                self.next = weather
                break
        self.transition_timer    = self.transition_duration
        self.hold_timer          = self.rng.uniform(300, 900)
        self.intensity           = 0.0

    def get_sky_color(self, time_of_day):
        """Returns (r,g,b) for current sky"""
        if time_of_day < 6 or time_of_day >= 20:
            key = 'night'
        elif time_of_day < 8 or time_of_day >= 18:
            key = 'dawn'
        else:
            key = 'day'

        c1 = SKY_COLORS.get(self.current, SKY_COLORS[WEATHER_CLEAR])[key]
        c2 = SKY_COLORS.get(self.next,    SKY_COLORS[WEATHER_CLEAR])[key]

        r = c1[0] + (c2[0] - c1[0]) * self.intensity
        g = c1[1] + (c2[1] - c1[1]) * self.intensity
        b = c1[2] + (c2[2] - c1[2]) * self.intensity

        # Lightning flash
        if self.lightning_flash > 0:
            lf = self.lightning_flash * 0.6
            r  = min(1.0, r + lf)
            g  = min(1.0, g + lf)
            b  = min(1.0, b + lf)

        return (r, g, b)

    @property
    def is_raining(self):
        return self.current in (WEATHER_LIGHT_RAIN, WEATHER_HEAVY_RAIN, WEATHER_STORM)

    @property
    def rain_intensity(self):
        base = {
            WEATHER_LIGHT_RAIN: 0.3,
            WEATHER_HEAVY_RAIN: 0.75,
            WEATHER_STORM:      1.0,
        }.get(self.current, 0.0)
        return base

    @property
    def visibility(self):
        """0.0=blind, 1.0=perfect"""
        return {
            WEATHER_CLEAR:      1.0,
            WEATHER_CLOUDY:     0.85,
            WEATHER_LIGHT_RAIN: 0.65,
            WEATHER_HEAVY_RAIN: 0.45,
            WEATHER_STORM:      0.25,
            WEATHER_FOG:        0.20,
        }.get(self.current, 1.0)

    @property
    def move_penalty(self):
        """Speed multiplier from weather"""
        return {
            WEATHER_CLEAR:      1.0,
            WEATHER_CLOUDY:     1.0,
            WEATHER_LIGHT_RAIN: 0.9,
            WEATHER_HEAVY_RAIN: 0.75,
            WEATHER_STORM:      0.55,
            WEATHER_FOG:        0.85,
        }.get(self.current, 1.0)

    @property
    def description(self):
        icons = {
            WEATHER_CLEAR:      '☀️  Clear',
            WEATHER_CLOUDY:     '⛅ Cloudy',
            WEATHER_LIGHT_RAIN: '🌧  Light Rain',
            WEATHER_HEAVY_RAIN: '🌧  Heavy Rain',
            WEATHER_STORM:      '⛈  Storm',
            WEATHER_FOG:        '🌫  Foggy',
        }
        return icons.get(self.current, self.current)

    @property
    def extinguishes_fire(self):
        """Heavy rain + storm put out campfires"""
        return self.current in (WEATHER_HEAVY_RAIN, WEATHER_STORM)
