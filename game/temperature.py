"""
Temperature System
- Body temperature affected by: time of day, weather, campfire proximity,
  armor, being wet (rain), shelter
- Too cold → health drain
- Too hot → stamina drain
- Right temperature → small health regen
"""


class Temperature:
    def __init__(self):
        self.body_temp    = 37.0   # Celsius, ideal
        self.ideal_min    = 35.0
        self.ideal_max    = 39.0
        self.critical_low = 30.0
        self.critical_high= 42.0

        self._wet_level   = 0.0    # 0-1, from rain
        self._warn_timer  = 0.0

    def update(self, dt, time_of_day, weather, campfire_warmth, has_armor):
        # Ambient temperature from time + weather
        if 10 <= time_of_day <= 16:
            ambient = 30.0   # hot jungle day
        elif 6 <= time_of_day < 10 or 16 < time_of_day <= 19:
            ambient = 25.0   # mild
        else:
            ambient = 18.0   # cold night

        weather_mod = {
            'clear':       0.0,
            'cloudy':     -2.0,
            'light_rain': -4.0,
            'heavy_rain': -7.0,
            'storm':     -10.0,
            'fog':        -3.0,
        }.get(weather.current, 0.0)

        ambient += weather_mod

        # Rain makes you wet → colder
        if weather.is_raining:
            self._wet_level = min(1.0, self._wet_level + dt * 0.05)
        else:
            self._wet_level = max(0.0, self._wet_level - dt * 0.02)

        # Effective ambient
        effective_ambient = ambient - self._wet_level * 8.0

        # Campfire warmth
        warmth_boost = campfire_warmth * 15.0   # up to +15°C near fire

        # Armor insulation
        armor_mod = 2.0 if has_armor else 0.0

        # Target temperature
        target = effective_ambient + warmth_boost + armor_mod

        # Body temperature moves toward target slowly
        diff = target - self.body_temp
        self.body_temp += diff * dt * 0.08

        return self._get_effects(dt)

    def _get_effects(self, dt):
        """Return health/stamina effects from temperature"""
        events = []

        if self.body_temp < self.critical_low:
            events.append(('health_drain', 2.0 * dt))
            events.append(('notify', '🥶 Hypothermia! Find warmth!'))
        elif self.body_temp < self.ideal_min:
            events.append(('health_drain', 0.3 * dt))
            if self._warn_timer <= 0:
                events.append(('notify', '❄️  You are cold'))
                self._warn_timer = 30.0

        elif self.body_temp > self.critical_high:
            events.append(('stamina_drain', 3.0 * dt))
            events.append(('notify', '🥵 Overheating!'))
        elif self.body_temp > self.ideal_max:
            events.append(('stamina_drain', 0.5 * dt))

        else:
            # Ideal range → slow health regen
            events.append(('health_regen', 0.05 * dt))

        self._warn_timer -= dt
        return events

    @property
    def display(self):
        t = self.body_temp
        if t < 32:
            return f'🥶 {t:.0f}°C'
        elif t > 40:
            return f'🥵 {t:.0f}°C'
        else:
            return f'🌡  {t:.0f}°C'

    @property
    def color(self):
        t = self.body_temp
        if t < self.ideal_min:
            chill = (self.ideal_min - t) / (self.ideal_min - self.critical_low)
            return (0.3 + chill * 0.1, 0.3 + chill * 0.3, 0.8, 1)
        elif t > self.ideal_max:
            heat = (t - self.ideal_max) / (self.critical_high - self.ideal_max)
            return (0.8 + heat * 0.2, 0.3 - heat * 0.2, 0.1, 1)
        return (0.4, 0.9, 0.4, 1)
