"""
AndroidPlayer - Pure Python player simulation
No Panda3D/Ursina dependencies - works on Android too
Position, stats, movement math only
"""

import math


class AndroidPlayer:
    def __init__(self):
        # Position
        self.x = 0.0
        self.y = 1.0
        self.z = 0.0

        # Camera / facing
        self.yaw   = 0.0     # horizontal angle (degrees)
        self.pitch = -15.0   # vertical angle

        # Stats
        self.max_health  = 100
        self.health      = 100
        self.max_hunger  = 100
        self.hunger      = 100
        self.max_thirst  = 100
        self.thirst      = 100
        self.max_stamina = 100
        self.stamina     = 100

        # Physics
        self.velocity_y  = 0.0
        self.is_grounded = True
        self.gravity     = 20.0

        # Config
        self.move_speed  = 5.0
        self.run_speed   = 9.0
        self.jump_height = 7.0
        self.reach       = 3.0
        self.cam_sens    = 80.0

        # Timers
        self._hunger_t = 0.0
        self._thirst_t = 0.0

        self.is_alive = True

    def move(self, dx, dz, dt, get_height=None, running=False):
        """Move player in world space relative to camera yaw"""
        if not self.is_alive:
            return

        speed = self.run_speed if running else self.move_speed

        yaw_rad = math.radians(self.yaw)
        fwd_x = math.sin(yaw_rad)
        fwd_z = math.cos(yaw_rad)
        right_x =  math.cos(yaw_rad)
        right_z = -math.sin(yaw_rad)

        move_x = fwd_x * (-dz) + right_x * dx
        move_z = fwd_z * (-dz) + right_z * dx

        length = math.sqrt(move_x**2 + move_z**2)
        if length > 0:
            move_x = move_x / length * speed * dt
            move_z = move_z / length * speed * dt

            # Stamina drain when moving fast
            if running:
                self.stamina = max(0, self.stamina - 15 * dt)

        # Apply gravity
        if not self.is_grounded:
            self.velocity_y -= self.gravity * dt
        else:
            if self.velocity_y < 0:
                self.velocity_y = 0

        self.x += move_x
        self.y += self.velocity_y * dt
        self.z += move_z

        # Ground check
        ground_y = 0.0
        if get_height:
            ground_y = get_height(self.x, self.z)

        if self.y <= ground_y + 1.0:
            self.y = ground_y + 1.0
            self.is_grounded = True
            self.velocity_y = 0
        else:
            self.is_grounded = False

        # Stamina regen when not running
        if not running:
            self.stamina = min(self.max_stamina, self.stamina + 8 * dt)

    def jump(self):
        if self.is_grounded and self.stamina > 10:
            self.velocity_y = self.jump_height
            self.is_grounded = False
            self.stamina -= 10

    def rotate_camera(self, dx, dy, dt):
        """Rotate camera from joystick input"""
        self.yaw   += dx * self.cam_sens * dt
        self.pitch -= dy * self.cam_sens * dt
        self.pitch  = max(-50.0, min(60.0, self.pitch))

    def update_stats(self, dt):
        """Drain hunger and thirst over time"""
        self._hunger_t += dt
        self._thirst_t += dt

        if self._hunger_t >= 6.0:
            self.hunger = max(0, self.hunger - 1)
            self._hunger_t = 0
            if self.hunger == 0:
                self.health = max(0, self.health - 0.5)

        if self._thirst_t >= 4.0:
            self.thirst = max(0, self.thirst - 1)
            self._thirst_t = 0
            if self.thirst == 0:
                self.health = max(0, self.health - 1)

        if self.health <= 0:
            self.is_alive = False

    def eat(self, nutrition):
        self.hunger = min(self.max_hunger, self.hunger + nutrition)

    def drink(self, hydration):
        self.thirst = min(self.max_thirst, self.thirst + hydration)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    @property
    def position(self):
        return (self.x, self.y, self.z)
