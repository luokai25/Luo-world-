"""
LUO WORLD - Main Entry Point
CRITICAL: LuoWorldApp must be at module level for p4a to find it
"""

__version__ = '0.2.0'

import sys
import os

# Detect platform BEFORE any imports
try:
    import android
    PLATFORM = 'android'
except ImportError:
    PLATFORM = 'desktop'

# ─────────────────────────────────────────────────
#  ANDROID / KIVY PATH
# ─────────────────────────────────────────────────
if PLATFORM == 'android':
    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import dp
    from kivy.animation import Animation
    import math

    from game.game_state import GameState
    from game.inventory import ITEMS
    from ui.crafting_ui import CraftingUI
    from ui.inventory_screen import InventoryScreen
    from ui.minimap import MinimapWidget
    from engine.sound_manager import SoundManager

    class VirtualJoystick(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.active_touch = None
            self.center_pos   = (0, 0)
            self.stick_pos    = (0, 0)
            self.delta        = (0.0, 0.0)
            self.radius       = dp(75)
            self.bind(pos=self._reset, size=self._reset)

        def _reset(self, *a):
            self.center_pos = (self.center_x, self.center_y)
            self.stick_pos  = self.center_pos

        def on_touch_down(self, touch):
            if self.collide_point(*touch.pos):
                self.active_touch = touch.uid
                self.center_pos = touch.pos
                self.stick_pos  = touch.pos
                self.delta      = (0.0, 0.0)
                return True

        def on_touch_move(self, touch):
            if touch.uid == self.active_touch:
                cx, cy = self.center_pos
                dx = touch.x - cx
                dy = touch.y - cy
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > self.radius:
                    dx = dx / dist * self.radius
                    dy = dy / dist * self.radius
                self.stick_pos = (cx+dx, cy+dy)
                self.delta = (dx/self.radius, dy/self.radius)
                return True

        def on_touch_up(self, touch):
            if touch.uid == self.active_touch:
                self.active_touch = None
                self.stick_pos = self.center_pos
                self.delta = (0.0, 0.0)
                return True

        def draw(self, canvas):
            with canvas:
                Color(0.2, 0.4, 0.2, 0.3)
                r = self.radius
                Ellipse(pos=(self.center_pos[0]-r, self.center_pos[1]-r),
                        size=(r*2, r*2))
                Color(0.5, 0.9, 0.4, 0.65)
                sr = dp(26)
                Ellipse(pos=(self.stick_pos[0]-sr, self.stick_pos[1]-sr),
                        size=(sr*2, sr*2))


    class GameWidget(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.gs    = GameState()
            self.sound = SoundManager()
            self.gs.start()

            w, h = Window.size

            # Sky background
            with self.canvas.before:
                self._sky_col = Color(0.35, 0.60, 0.40, 1)
                self._sky_rect = Rectangle(pos=(0,0), size=(w,h))

            # Joysticks
            self.joy_move = VirtualJoystick(pos=(dp(10), dp(10)), size=(dp(220), dp(220)))
            self.joy_cam  = VirtualJoystick(pos=(w-dp(230), dp(10)), size=(dp(220), dp(220)))
            self.add_widget(self.joy_move)
            self.add_widget(self.joy_cam)

            # Action buttons
            self._build_buttons(w, h)
            # HUD labels
            self._build_hud(w, h)

            # Minimap
            self.minimap = MinimapWidget(game_state=self.gs)
            self.add_widget(self.minimap)

            # Inventory screen
            self.inv_screen = InventoryScreen(
                inventory=self.gs.inventory,
                on_close=lambda: None,
                on_craft_open=lambda: self.craft_ui.open(),
            )
            self.add_widget(self.inv_screen)

            # Crafting UI
            self.craft_ui = CraftingUI(
                inventory=self.gs.inventory,
                on_craft=self._do_craft,
            )
            self.add_widget(self.craft_ui)

            Clock.schedule_interval(self.update, 1.0/60.0)

        def _build_buttons(self, w, h):
            btns = [
                ('⚔',   (w-dp(310), dp(165)), (0.75,0.2,0.2,0.88),  'attack'),
                ('E',   (w-dp(210), dp(225)), (0.2,0.5,0.75,0.88),  'interact'),
                ('USE', (w-dp(420), dp(165)), (0.2,0.65,0.2,0.88),  'use'),
                ('↑',   (w-dp(210), dp(325)), (0.35,0.35,0.35,0.88),'jump'),
                ('🔥',  (w-dp(420), dp(265)), (0.65,0.35,0.1,0.88), 'fire'),
                ('🎒',  (w-dp(55),  h-dp(200)),(0.2,0.3,0.2,0.85),  'inventory'),
            ]
            for text, pos, col, action in btns:
                btn = Button(
                    text=text, font_size=dp(18 if len(text)>1 else 22), bold=True,
                    pos=pos, size=(dp(82), dp(82)),
                    background_color=col, background_normal='',
                )
                btn.luo_action = action
                btn.bind(on_press=self._btn_press)
                self.add_widget(btn)

        def _btn_press(self, btn):
            a = btn.luo_action
            if a == 'attack':    self.gs.player_attack()
            elif a == 'interact':self.gs.player_interact()
            elif a == 'use':     self.gs.use_item()
            elif a == 'jump':    self.gs.player.jump()
            elif a == 'fire':    self.gs.place_campfire()
            elif a == 'inventory': self.inv_screen.toggle()

        def _build_hud(self, w, h):
            self.lbl = {}
            stats = [
                ('health',  '❤',  (1,0.3,0.3,1),   h-dp(38)),
                ('hunger',  '🍖', (1,0.65,0.1,1),  h-dp(62)),
                ('thirst',  '💧', (0.3,0.6,1,1),   h-dp(86)),
                ('stamina', '⚡', (0.7,1,0.25,1),  h-dp(110)),
                ('temp',    '🌡', (0.8,0.8,0.5,1), h-dp(134)),
            ]
            for key, icon, col, y in stats:
                lbl = Label(text=f'{icon} --', pos=(dp(10),y),
                            size=(dp(160),dp(22)), font_size=dp(13),
                            color=col, halign='left')
                self.lbl[key] = lbl
                self.add_widget(lbl)

            self.lbl['weather'] = Label(
                text='', pos=(dp(10), h-dp(158)),
                size=(dp(160),dp(22)), font_size=dp(12),
                color=(0.8,0.9,1,1), halign='left')
            self.add_widget(self.lbl['weather'])

            self.lbl['time'] = Label(
                text='', pos=(w-dp(200), h-dp(48)),
                size=(dp(190),dp(35)), font_size=dp(15),
                color=(1,0.95,0.7,1), halign='right')
            self.add_widget(self.lbl['time'])

            self.lbl['notify'] = Label(
                text='', pos=(w//2-dp(200), h-dp(70)),
                size=(dp(400),dp(40)), font_size=dp(15),
                color=(1,1,0.8,1), halign='center', bold=True)
            self.add_widget(self.lbl['notify'])

            self.lbl['prompt'] = Label(
                text='', pos=(w//2-dp(220), h//2-dp(120)),
                size=(dp(440),dp(36)), font_size=dp(14),
                color=(1,1,1,0.9), halign='center')
            self.add_widget(self.lbl['prompt'])

            # Hotbar (6 slots center bottom)
            self.hotbar_lbls = []
            n = 6; sw = dp(68); gap = dp(5)
            total = n*sw + (n-1)*gap
            sx = w/2 - total/2
            for i in range(n):
                x = sx + i*(sw+gap)
                with self.canvas:
                    Color(0.1,0.15,0.1,0.75)
                    RoundedRectangle(pos=(x,dp(10)), size=(sw,sw), radius=[dp(6)])
                lbl = Label(text='', pos=(x,dp(10)), size=(sw,sw),
                            font_size=dp(22), halign='center', valign='middle',
                            markup=True)
                self.hotbar_lbls.append(lbl)
                self.add_widget(lbl)

        def _do_craft(self, recipe_id):
            self.gs.try_craft(recipe_id)
            self.sound.on_craft()
            self.inv_screen.refresh()
            self.craft_ui.refresh()

        def update(self, dt):
            gs  = self.gs
            p   = gs.player
            inv = gs.inventory

            dx, dz = self.joy_move.delta
            cx, cy = self.joy_cam.delta
            gs.update(dt, move_x=dx, move_z=-dz, cam_x=cx, cam_y=cy)

            # Sky color from weather + time
            r, g, b = gs.weather.get_sky_color(gs.time_of_day)
            self._sky_col.rgb = (r, g, b)

            # Stats
            self.lbl['health'].text  = f'❤  {int(p.health)}'
            self.lbl['hunger'].text  = f'🍖 {int(p.hunger)}'
            self.lbl['thirst'].text  = f'💧 {int(p.thirst)}'
            self.lbl['stamina'].text = f'⚡ {int(p.stamina)}'
            self.lbl['temp'].text    = gs.temp_str
            self.lbl['weather'].text = gs.weather_str
            self.lbl['time'].text    = gs.time_str
            self.lbl['notify'].text  = gs.current_notification
            self.lbl['prompt'].text  = gs.interact_prompt

            # Hotbar
            for i, lbl in enumerate(self.hotbar_lbls):
                slot = inv.slots[i]
                if slot.empty:
                    lbl.text = ''
                else:
                    item = ITEMS.get(slot.item_id, {})
                    cnt = f'\n[size=10]{slot.count}[/size]' if slot.count > 1 else ''
                    lbl.text = f"{item.get('icon','?')}{cnt}"

            # Sound
            moving  = abs(dx)+abs(dz) > 0.1
            running = abs(dx)+abs(dz) > 0.8
            self.sound.update(dt, moving, running, gs.time_of_day)

            # Joystick draw
            self.canvas.after.clear()
            self.joy_move.draw(self.canvas.after)
            self.joy_cam.draw(self.canvas.after)


    # CRITICAL: App class MUST be at module level for p4a
    class LuoWorldApp(App):
        def build(self):
            Window.clearcolor = (0.08, 0.15, 0.08, 1)
            return GameWidget()

        def on_pause(self):
            return True

        def on_resume(self):
            pass


# ─────────────────────────────────────────────────
#  DESKTOP / URSINA PATH
# ─────────────────────────────────────────────────
else:
    # Desktop uses Ursina — only imported when not on Android
    def _run_desktop():
        from ursina import Ursina, window, camera, time, application, Vec3
        from game.world import World
        from game.player import Player
        from game.inventory import Inventory
        from game.hud import HUD
        from engine.physics import PhysicsEngine
        from engine.lighting import LightingSystem

        app = Ursina(title='Luo World', borderless=False,
                     fullscreen=False, size=(1280,720), vsync=True)
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        physics   = PhysicsEngine()
        lighting  = LightingSystem()
        world     = World(physics=physics)
        player    = Player(world=world, position=(0,2,0))
        inventory = Inventory(player=player)
        inventory.give_starting_items()
        hud = HUD(player=player, inventory=inventory)
        camera.fov = 75

        def update():
            player.update(); world.update()
            hud.update(); physics.update(time.dt); lighting.update()

        def input(key):
            player.handle_input(key); inventory.handle_input(key)
            hud.handle_input(key)
            if key == 'escape': application.quit()

        app.run()


if __name__ == '__main__':
    if PLATFORM == 'android':
        LuoWorldApp().run()
    else:
        _run_desktop()
