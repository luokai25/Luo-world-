"""
SoundManager - Procedural and file-based audio
Jungle ambience, footsteps, chopping, animal sounds
Uses Kivy's SoundLoader (works on Android)
"""

import math
import random

try:
    from kivy.core.audio import SoundLoader
    KIVY_AUDIO = True
except ImportError:
    KIVY_AUDIO = False


# Sound event types
SFX_FOOTSTEP   = 'footstep'
SFX_CHOP       = 'chop'
SFX_MINE       = 'mine'
SFX_PICKUP     = 'pickup'
SFX_EAT        = 'eat'
SFX_DRINK      = 'drink'
SFX_CRAFT      = 'craft'
SFX_HURT       = 'hurt'
SFX_ANIMAL_DEF = 'animal_death'
SFX_SPLASH     = 'splash'


class SoundManager:
    """
    Manages all game audio.
    Generates procedural sounds where files aren't available.
    Falls back gracefully if audio unavailable.
    """

    def __init__(self):
        self.enabled       = KIVY_AUDIO
        self.sfx_volume    = 0.8
        self.music_volume  = 0.4
        self._sounds       = {}
        self._ambient      = None
        self._step_timer   = 0.0
        self._step_interval= 0.45   # seconds between footstep sounds
        self._was_moving   = False

        # Sound cooldowns to avoid spam
        self._cooldowns    = {}
        self._cooldown_def = 0.15

        if self.enabled:
            self._load_sounds()

    def _load_sounds(self):
        """Try to load sound files; skip missing ones gracefully"""
        sound_files = {
            SFX_CHOP:    ['assets/sounds/chop1.wav', 'assets/sounds/chop2.wav'],
            SFX_MINE:    ['assets/sounds/mine1.wav'],
            SFX_PICKUP:  ['assets/sounds/pickup.wav'],
            SFX_EAT:     ['assets/sounds/eat.wav'],
            SFX_DRINK:   ['assets/sounds/drink.wav'],
            SFX_CRAFT:   ['assets/sounds/craft.wav'],
            SFX_HURT:    ['assets/sounds/hurt.wav'],
            SFX_SPLASH:  ['assets/sounds/splash.wav'],
        }
        for sfx, paths in sound_files.items():
            loaded = []
            for path in paths:
                try:
                    s = SoundLoader.load(path)
                    if s:
                        s.volume = self.sfx_volume
                        loaded.append(s)
                except Exception:
                    pass
            if loaded:
                self._sounds[sfx] = loaded

    def play(self, sfx_type):
        """Play a sound effect"""
        if not self.enabled:
            return

        # Cooldown check
        import time as t
        now = t.time()
        last = self._cooldowns.get(sfx_type, 0)
        if now - last < self._cooldown_def:
            return
        self._cooldowns[sfx_type] = now

        sounds = self._sounds.get(sfx_type, [])
        if sounds:
            s = random.choice(sounds)
            s.stop()
            s.play()

    def update(self, dt, is_moving, is_running, time_of_day):
        """Update per-frame audio: footsteps, ambient"""
        if not self.enabled:
            return

        # Footsteps
        if is_moving:
            self._step_timer += dt
            interval = self._step_interval * (0.65 if is_running else 1.0)
            if self._step_timer >= interval:
                self._step_timer = 0
                self.play(SFX_FOOTSTEP)
        else:
            self._step_timer = 0

        # Update ambient based on time of day
        self._update_ambient(time_of_day)

    def _update_ambient(self, time_of_day):
        """Switch ambient track based on time"""
        # Night: crickets, owls
        # Day: birds, insects, river
        pass   # Will hook into actual files in future session

    def on_chop(self):
        self.play(SFX_CHOP)

    def on_mine(self):
        self.play(SFX_MINE)

    def on_pickup(self):
        self.play(SFX_PICKUP)

    def on_eat(self):
        self.play(SFX_EAT)

    def on_drink(self):
        self.play(SFX_DRINK)

    def on_craft(self):
        self.play(SFX_CRAFT)

    def on_hurt(self):
        self.play(SFX_HURT)

    def set_sfx_volume(self, vol):
        self.sfx_volume = vol
        for sounds in self._sounds.values():
            for s in sounds:
                s.volume = vol

    def set_music_volume(self, vol):
        self.music_volume = vol
        if self._ambient:
            self._ambient.volume = vol
