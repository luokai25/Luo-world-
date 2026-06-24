"""
LUO WORLD - Main Entry Point v0.2.0
Session 3: Crafting UI + Inventory Screen + Minimap + Sound
"""

__version__ = '0.2.0'

import sys
import os

try:
    from android import mActivity
    PLATFORM = 'android'
except ImportError:
    PLATFORM = 'desktop'


# ─────────────────────────────────────────────────
#  ANDROID / KIVY
# ─────────────────────────────────────────────────
if PLATFORM == 'android':
    os.environ['KIVY_NO_ENV_CONFIG'] = '1'
    os.environ['KIVY_NO_CONSOLELOG'] = '1'

    from kivy.config import Config
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('kivy', 'log_level', 'warning')

    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import dp
    import math

    sys.path.insert(0, os.path.dirname(__file__))

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
            self.delta        = (0, 0)
            self.radius       = dp(75)
            self.bind(pos=self._reset_center, size=self._reset_center)

        def _reset_center(self, *args):
            self.center_pos = (self.center_x, self.center_y)
            self.stick_pos  = self.center_pos

        def on_touch_down(self, touch):
            if self.collide_point(*touch.pos):
                self.active_touch = touch.uid
                self.center_pos   = touch.pos
                self.stick_pos    = touch.pos
                self.delta        = (0, 0)
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
                self.stick_pos = (cx + dx, cy + dy)
                self.delta = (dx / self.radius, dy / self.radius)
                return True

        def on_touch_up(self, touch):
            if touch.uid == self.active_touch:
                self.active_touch = None
                self.stick_pos    = self.center_pos
                self.delta        = (0, 0)
                return True

        def draw(self, canvas):
            with canvas:
                Color(0.2, 0.4, 0.2, 0.3)
                r = self.radius
                Ellipse(pos=(self.center_pos[0]-r, self.center_pos[1]-r),
                        size=(r*2, r*2))
                Color(0.5, 0.9, 0.4, 0.6)
                sr = dp(28)
                Ellipse(pos=(self.stick_pos[0]-sr, self.stick_pos[1]-sr),
                        size=(sr*2, sr*2))


    class HUD(FloatLayout):
        """All HUD elements: bars, hotbar, notifications, joysticks, buttons"""

        def __init__(self, game_state, **kwargs):
            super().__init__(**kwargs)
            self.gs  = game_state
            self.inv = game_state.inventory

            w, h = Window.size

            # Joysticks
            self.joy_move = VirtualJoystick(
                pos=(dp(10), dp(10)), size=(dp(220), dp(220)))
            self.joy_cam = VirtualJoystick(
                pos=(w - dp(230), dp(10)), size=(dp(220), dp(220)))
            self.add_widget(self.joy_move)
            self.add_widget(self.joy_cam)

            # Action buttons
            self._build_action_buttons(w, h)
            # Stat bars
            self._build_stat_bars(h)
            # Hotbar
            self._build_hotbar(w)
            # Notification
            self.notif_label = Label(
                text='', pos=(w//2 - dp(200), h - dp(60)),
                size=(dp(400), dp(40)), font_size=dp(16),
                color=(1, 1, 0.8, 1), halign='center',
                bold=True,
            )
            self.add_widget(self.notif_label)
            # Interact prompt
            self.prompt_label = Label(
                text='', pos=(w//2 - dp(220), h//2 - dp(120)),
                size=(dp(440), dp(36)), font_size=dp(15),
                color=(1, 1, 1, 0.9), halign='center',
            )
            self.add_widget(self.prompt_label)
            # Time display
            self.time_label = Label(
                text='', pos=(w - dp(200), h - dp(50)),
                size=(dp(190), dp(35)), font_size=dp(16),
                color=(1, 0.95, 0.7, 1), halign='right',
            )
            self.add_widget(self.time_label)

        def _build_action_buttons(self, w, h):
            configs = [
                ('⚔',  (w-dp(310), dp(170)), (0.75, 0.2, 0.2, 0.88), 'attack'),
                ('E',  (w-dp(210), dp(230)), (0.2,  0.5, 0.75, 0.88), 'interact'),
                ('USE',(w-dp(420), dp(170)), (0.2,  0.65,0.2,  0.88), 'use'),
                ('↑',  (w-dp(210), dp(330)), (0.4,  0.4, 0.4,  0.88), 'jump'),
            ]
            for text, pos, col, action in configs:
                btn = Button(
                    text=text, font_size=dp(18), bold=True,
                    pos=pos, size=(dp(82), dp(82)),
                    background_color=col, background_normal='',
                )
                btn.luo_action = action
                btn.bind(on_press=self._action_press)
                self.add_widget(btn)

        def _action_press(self, btn):
            action = btn.luo_action
            if action == 'attack':   self.gs.player_attack()
            elif action == 'interact': self.gs.player_interact()
            elif action == 'use':    self.gs.use_item()
            elif action == 'jump':   self.gs.player.jump()

        def _build_stat_bars(self, h):
            self.bar_labels = {}
            configs = [
                ('health',  '❤',  (1, 0.3, 0.3, 1),    h - dp(38)),
                ('hunger',  '🍖', (1, 0.65,0.1, 1),    h - dp(62)),
                ('thirst',  '💧', (0.3, 0.6, 1, 1),    h - dp(86)),
                ('stamina', '⚡', (0.7, 1, 0.25, 1),   h - dp(110)),
            ]
            for key, icon, col, y in configs:
                lbl = Label(
                    text=f'{icon} 100',
                    pos=(dp(10), y), size=(dp(140), dp(22)),
                    font_size=dp(14), color=col, halign='left',
                )
                self.bar_labels[key] = lbl
                self.add_widget(lbl)

        def _build_hotbar(self, w):
            self.hotbar_labels = []
            n = 6
            slot_w = dp(68)
            gap    = dp(5)
            total  = n * slot_w + (n-1) * gap
            sx     = w/2 - total/2
            y      = dp(10)
            for i in range(n):
                x = sx + i * (slot_w + gap)
                bg = FloatLayout(pos=(x, y), size=(slot_w, slot_w))
                with bg.canvas.before:
                    Color(0.1, 0.15, 0.1, 0.75)
                    RoundedRectangle(pos=(x, y), size=(slot_w, slot_w), radius=[dp(6)])
                self.add_widget(bg)
                lbl = Label(
                    text='', pos=(x, y), size=(slot_w, slot_w),
                    font_size=dp(22), halign='center', valign='middle',
                )
                self.hotbar_labels.append(lbl)
                self.add_widget(lbl)

        def update(self):
            gs  = self.gs
            inv = self.inv
            p   = gs.player

            self.bar_labels['health'].text  = f'❤  {int(p.health)}'
            self.bar_labels['hunger'].text  = f'🍖 {int(p.hunger)}'
            self.bar_labels['thirst'].text  = f'💧 {int(p.thirst)}'
            self.bar_labels['stamina'].text = f'⚡ {int(p.stamina)}'

            for i, lbl in enumerate(self.hotbar_labels):
                slot = inv.slots[i]
                if slot.empty:
                    lbl.text = ''
                else:
                    item = ITEMS.get(slot.item_id, {})
                    icon = item.get('icon', '?')
                    lbl.text = f"{icon}\n[size=10]{slot.count if slot.count>1 else ''}[/size]"
                    lbl.markup = True

            self.prompt_label.text = gs.interact_prompt
            self.time_label.text   = gs.time_str
            self.notif_label.text  = gs.current_notification

            # Draw joysticks
            self.canvas.after.clear()
            self.joy_move.draw(self.canvas.after)
            self.joy_cam.draw(self.canvas.after)


    class GameWidget(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.gs    = GameState()
            self.sound = SoundManager()
            self.gs.start()

            # Sky background
            with self.canvas.before:
                self._sky_color = Color(0.35, 0.60, 0.40, 1)
                self._sky_rect  = Rectangle(pos=(0, 0), size=Window.size)

            # HUD
            self.hud = HUD(game_state=self.gs)
            self.add_widget(self.hud)

            # Minimap
            self.minimap = MinimapWidget(game_state=self.gs)
            self.add_widget(self.minimap)

            # Inventory screen
            self.inv_screen = InventoryScreen(
                inventory=self.gs.inventory,
                on_close=lambda: None,
                on_craft_open=self._open_craft,
            )
            self.add_widget(self.inv_screen)

            # Crafting UI
            self.craft_ui = CraftingUI(
                inventory=self.gs.inventory,
                on_craft=self._do_craft,
            )
            self.add_widget(self.craft_ui)

            # Inventory button (top left)
            w, h = Window.size
            inv_btn = Button(
                text='🎒', font_size=dp(22),
                pos=(w - dp(55), h - dp(200)),
                size=(dp(50), dp(50)),
                background_color=(0.2, 0.3, 0.2, 0.85),
                background_normal='',
            )
            inv_btn.bind(on_press=lambda x: self.inv_screen.toggle())
            self.add_widget(inv_btn)

            Clock.schedule_interval(self.update, 1.0 / 60.0)

        def _open_craft(self):
            self.craft_ui.open()

        def _do_craft(self, recipe_id):
            self.gs.try_craft(recipe_id)
            self.sound.on_craft()
            self.inv_screen.refresh()
            self.craft_ui.refresh()

        def update(self, dt):
            gs = self.gs
            dx, dz = self.hud.joy_move.delta
            cx, cy = self.hud.joy_cam.delta

            gs.update(dt, move_x=dx, move_z=-dz, cam_x=cx, cam_y=cy)

            # Sky color from time of day
            tod = gs.time_of_day
            if tod < 6 or tod >= 20:
                self._sky_color.rgb = (0.04, 0.04, 0.12)
            elif 6 <= tod < 8 or 17 <= tod < 20:
                self._sky_color.rgb = (0.70, 0.45, 0.25)
            else:
                self._sky_color.rgb = (0.38, 0.65, 0.42)

            self.hud.update()

            # Sound
            moving = abs(dx) + abs(dz) > 0.1
            running = abs(dx) + abs(dz) > 0.8
            self.sound.update(dt, moving, running, tod)


    class LuoWorldApp(App):
        def build(self):
            Window.clearcolor = (0.08, 0.15, 0.08, 1)
            return GameWidget()
        def on_pause(self): return True
        def on_resume(self): pass

    if __name__ == '__main__':
        LuoWorldApp().run()


# ─────────────────────────────────────────────────
#  DESKTOP / URSINA
# ─────────────────────────────────────────────────
else:
    from ursina import *
    from game.world import World
    from game.player import Player
    from game.inventory import Inventory
    from game.hud import HUD
    from engine.physics import PhysicsEngine
    from engine.lighting import LightingSystem

    def main():
        app = Ursina(title='Luo World', borderless=False,
                     fullscreen=False, size=(1280, 720), vsync=True)
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        physics   = PhysicsEngine()
        lighting  = LightingSystem()
        world     = World(physics=physics)
        player    = Player(world=world, position=(0, 2, 0))
        inventory = Inventory(player=player)
        inventory.give_starting_items()
        hud = HUD(player=player, inventory=inventory)
        camera.fov = 75

        def update():
            player.update()
            world.update()
            hud.update()
            physics.update(time.dt)
            lighting.update()

        def input(key):
            player.handle_input(key)
            inventory.handle_input(key)
            hud.handle_input(key)
            if key == 'escape':
                application.quit()

        app.run()

    if __name__ == '__main__':
        main()
