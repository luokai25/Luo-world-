"""
LUO WORLD - Main Entry Point
Dual mode: Kivy (Android APK) + Ursina (PC desktop)
Auto-detects platform and launches correct renderer
"""

__version__ = '0.1.0'

import sys
import os

# Detect platform
try:
    from android import mActivity
    PLATFORM = 'android'
except ImportError:
    PLATFORM = 'desktop'

# ─────────────────────────────────────────────────
#  ANDROID / KIVY PATH
# ─────────────────────────────────────────────────
if PLATFORM == 'android':
    os.environ['KIVY_NO_ENV_CONFIG'] = '1'
    os.environ['KIVY_NO_CONSOLELOG'] = '1'

    from kivy.config import Config
    Config.set('graphics', 'width', '1920')
    Config.set('graphics', 'height', '1080')
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('kivy', 'log_level', 'warning')

    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.graphics import Color, Ellipse, Rectangle
    from kivy.clock import Clock
    from kivy.core.window import Window
    import math

    sys.path.insert(0, os.path.dirname(__file__))
    from game.inventory import Inventory, ITEMS
    from game.game_state import GameState

    class VirtualJoystick(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.active_touch = None
            self.center_pos = (0, 0)
            self.stick_pos = (0, 0)
            self.delta = (0, 0)
            self.radius = 80
            self.bind(pos=self._update_center, size=self._update_center)

        def _update_center(self, *args):
            self.center_pos = (self.center_x, self.center_y)
            self.stick_pos = self.center_pos

        def on_touch_down(self, touch):
            if self.collide_point(*touch.pos):
                self.active_touch = touch.uid
                self.center_pos = touch.pos
                self.stick_pos = touch.pos
                self.delta = (0, 0)
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
                self.stick_pos = self.center_pos
                self.delta = (0, 0)
                return True

        def draw(self, canvas):
            with canvas:
                Color(1, 1, 1, 0.25)
                Ellipse(
                    pos=(self.center_pos[0] - self.radius,
                         self.center_pos[1] - self.radius),
                    size=(self.radius*2, self.radius*2)
                )
                Color(1, 1, 1, 0.55)
                sr = 32
                Ellipse(
                    pos=(self.stick_pos[0] - sr,
                         self.stick_pos[1] - sr),
                    size=(sr*2, sr*2)
                )

    class GameWidget(FloatLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.game_state = GameState()
            self.game_state.start()
            w, h = Window.size
            self.joy_move = VirtualJoystick(pos=(20, 20), size=(220, 220))
            self.joy_cam  = VirtualJoystick(pos=(w-240, 20), size=(220, 220))
            self.add_widget(self.joy_move)
            self.add_widget(self.joy_cam)
            self._build_buttons()
            self._build_hud()
            Clock.schedule_interval(self.update, 1.0/60.0)

        def _build_buttons(self):
            w, h = Window.size
            self.btn_attack = Button(
                text='⚔', font_size=36,
                pos=(w-340, 160), size=(90, 90),
                background_color=(0.8, 0.2, 0.2, 0.85))
            self.btn_attack.bind(on_press=lambda x: self.game_state.player_attack())
            self.btn_interact = Button(
                text='E', font_size=28,
                pos=(w-230, 220), size=(90, 90),
                background_color=(0.2, 0.6, 0.8, 0.85))
            self.btn_interact.bind(on_press=lambda x: self.game_state.player_interact())
            self.btn_inventory = Button(
                text='🎒', font_size=30,
                pos=(w-110, h-110), size=(90, 90),
                background_color=(0.3, 0.3, 0.3, 0.85))
            self.btn_inventory.bind(on_press=lambda x: self.game_state.toggle_inventory())
            self.btn_use = Button(
                text='USE', font_size=20,
                pos=(w-450, 160), size=(90, 90),
                background_color=(0.2, 0.7, 0.3, 0.85))
            self.btn_use.bind(on_press=lambda x: self.game_state.use_item())
            for btn in [self.btn_attack, self.btn_interact,
                        self.btn_inventory, self.btn_use]:
                self.add_widget(btn)

        def _build_hud(self):
            w, h = Window.size
            self.lbl_health  = Label(text='❤  100', pos=(10,h-40),  size=(200,30), font_size=18, color=(1,0.3,0.3,1))
            self.lbl_hunger  = Label(text='🍖 100', pos=(10,h-70),  size=(200,30), font_size=18, color=(1,0.65,0.1,1))
            self.lbl_thirst  = Label(text='💧 100', pos=(10,h-100), size=(200,30), font_size=18, color=(0.3,0.6,1,1))
            self.lbl_stamina = Label(text='⚡ 100', pos=(10,h-130), size=(200,30), font_size=18, color=(0.7,1,0.2,1))
            self.lbl_time    = Label(text='10:00 🌤', pos=(w-180,h-40), size=(170,30), font_size=18, color=(1,0.95,0.7,1))
            self.lbl_equipped= Label(text='', pos=(w//2-100,10), size=(200,40), font_size=20, color=(1,1,0.8,1))
            self.lbl_prompt  = Label(text='', pos=(w//2-200,h//2-100), size=(400,40), font_size=22, color=(1,1,1,0.9))
            for lbl in [self.lbl_health, self.lbl_hunger, self.lbl_thirst,
                        self.lbl_stamina, self.lbl_time, self.lbl_equipped, self.lbl_prompt]:
                self.add_widget(lbl)

        def update(self, dt):
            gs = self.game_state
            gs.update(dt,
                      move_x=self.joy_move.delta[0],
                      move_z=-self.joy_move.delta[1],
                      cam_x=self.joy_cam.delta[0],
                      cam_y=self.joy_cam.delta[1])
            p = gs.player
            self.lbl_health.text  = f'❤  {int(p.health)}'
            self.lbl_hunger.text  = f'🍖 {int(p.hunger)}'
            self.lbl_thirst.text  = f'💧 {int(p.thirst)}'
            self.lbl_stamina.text = f'⚡ {int(p.stamina)}'
            equipped = gs.inventory.equipped
            if equipped:
                item = ITEMS.get(equipped.item_id, {})
                self.lbl_equipped.text = f"{item.get('icon','')} {item.get('name','')}"
            else:
                self.lbl_equipped.text = ''
            self.lbl_time.text   = gs.time_str
            self.lbl_prompt.text = gs.interact_prompt
            self.canvas.after.clear()
            self.joy_move.draw(self.canvas.after)
            self.joy_cam.draw(self.canvas.after)

    class LuoWorldApp(App):
        def build(self):
            Window.clearcolor = (0.08, 0.15, 0.08, 1)
            return GameWidget()
        def on_pause(self): return True
        def on_resume(self): pass

    if __name__ == '__main__':
        LuoWorldApp().run()

# ─────────────────────────────────────────────────
#  DESKTOP / URSINA PATH
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
