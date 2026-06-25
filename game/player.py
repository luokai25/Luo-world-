"""
Player - Desktop only (Ursina)
Stub on Android - Android uses AndroidPlayer in android_player.py
"""
try:
    from ursina import *
    HAS_URSINA = True
except ImportError:
    HAS_URSINA = False

import math

class Player(Entity if HAS_URSINA else object):
    def __init__(self, world=None, position=(0,2,0)):
        if HAS_URSINA:
            super().__init__()
        self.world = world
        self.max_health = 100; self.health = 100
        self.max_stamina = 100; self.stamina = 100
        self.max_hunger = 100; self.hunger = 100
        self.max_thirst = 100; self.thirst = 100
        self.is_alive = True
        self.move_speed = 5.0; self.run_speed = 9.0
        self.jump_height = 5.0; self.gravity = 20.0
        self.velocity_y = 0; self.is_grounded = False
        self.cam_yaw = 0.0; self.cam_pitch = -15.0
        self.mouse_sens = 40.0
        self.held_item = None
        self._hunger_timer = 0; self._thirst_timer = 0
        if HAS_URSINA:
            self._build_model(position)
            self._setup_camera()
            mouse.locked = True

    def _build_model(self, position):
        if not HAS_URSINA: return
        px,py,pz = position
        self.pivot = Entity(position=(px,py,pz))
        self.body  = Entity(parent=self.pivot, model='cube',
                            color=color.rgb(60,90,60), scale=(0.5,0.65,0.28))
        self.head_node = Entity(parent=self.pivot, model='sphere',
                                color=color.rgb(210,170,120),
                                scale=(0.35,0.35,0.35), position=(0,0.55,0))
        self.arm_r = Entity(parent=self.pivot, model='cube',
                            color=color.rgb(210,170,120),
                            scale=(0.15,0.55,0.15), position=(0.35,-0.02,0))
        self.arm_l = Entity(parent=self.pivot, model='cube',
                            color=color.rgb(210,170,120),
                            scale=(0.15,0.55,0.15), position=(-0.35,-0.02,0))
        self.leg_l = Entity(parent=self.pivot, model='cube',
                            color=color.rgb(50,70,100),
                            scale=(0.18,0.58,0.18), position=(-0.16,-0.63,0))
        self.leg_r = Entity(parent=self.pivot, model='cube',
                            color=color.rgb(50,70,100),
                            scale=(0.18,0.58,0.18), position=(0.16,-0.63,0))

    def _setup_camera(self):
        if not HAS_URSINA: return
        camera.parent   = scene
        camera.position = self.pivot.position + Vec3(0,2,-4.5)
        camera.look_at(self.pivot.position + Vec3(0,0.5,0))

    def update(self):
        if not HAS_URSINA or not self.is_alive: return
        self._handle_movement()
        self._update_camera()
        self._update_survival_stats()

    def _handle_movement(self):
        if not HAS_URSINA: return
        dt    = time.dt
        speed = self.run_speed if held_keys['shift'] else self.move_speed
        yaw   = math.radians(self.cam_yaw)
        fwd   = Vec3(math.sin(yaw),0,math.cos(yaw))
        right = Vec3(math.cos(yaw),0,-math.sin(yaw))
        move  = Vec3(0,0,0)
        if held_keys['w']: move += fwd
        if held_keys['s']: move -= fwd
        if held_keys['a']: move -= right
        if held_keys['d']: move += right
        if move.length() > 0:
            move = move.normalized() * speed * dt
        if not self.is_grounded:
            self.velocity_y -= self.gravity * dt
        else:
            if self.velocity_y < 0: self.velocity_y = 0
        new_pos = self.pivot.position + move
        new_pos.y += self.velocity_y * dt
        ground_y = self._get_ground_y(new_pos.x, new_pos.z)
        if new_pos.y <= ground_y:
            new_pos.y = ground_y; self.is_grounded = True; self.velocity_y = 0
        else:
            self.is_grounded = False
        self.pivot.position = new_pos

    def _get_ground_y(self, x, z):
        if self.world: return self.world.get_height(x, z)
        return 0.0

    def _update_camera(self):
        if not HAS_URSINA: return
        dt = time.dt
        self.cam_yaw   += mouse.velocity[0] * self.mouse_sens
        self.cam_pitch -= mouse.velocity[1] * self.mouse_sens
        self.cam_pitch  = clamp(self.cam_pitch, -40, 60)
        yaw   = math.radians(self.cam_yaw)
        pitch = math.radians(self.cam_pitch)
        ox = math.sin(yaw)*math.cos(pitch)*4.5
        oy = math.sin(pitch)*4.5 + 2.0
        oz = math.cos(yaw)*math.cos(pitch)*4.5
        target = self.pivot.position + Vec3(-ox,oy,-oz)
        camera.position = lerp(camera.position, target, 12*dt)
        camera.look_at(self.pivot.position + Vec3(0,0.5,0))

    def _update_survival_stats(self):
        if not HAS_URSINA: return
        dt = time.dt
        self._hunger_timer += dt
        self._thirst_timer += dt
        if self._hunger_timer >= 6.0:
            self.hunger = max(0, self.hunger-1); self._hunger_timer = 0
        if self._thirst_timer >= 4.0:
            self.thirst = max(0, self.thirst-1); self._thirst_timer = 0

    def handle_input(self, key):
        if not HAS_URSINA: return
        if key == 'space' and self.is_grounded:
            self.velocity_y = self.jump_height

    def eat(self, n):   self.hunger  = min(self.max_hunger, self.hunger+n)
    def drink(self, h): self.thirst  = min(self.max_thirst, self.thirst+h)
    def heal(self, a):  self.health  = min(self.max_health, self.health+a)

    @property
    def position(self):
        return self.pivot.position if HAS_URSINA else (0,0,0)
