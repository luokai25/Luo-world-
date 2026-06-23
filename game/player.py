"""
Player - 3rd Person Controller
Handles movement, camera, stamina, health, interaction
"""

from ursina import *
import math


class Player(Entity):
    def __init__(self, world=None, position=(0, 2, 0)):
        super().__init__()
        self.world = world

        # ── Stats ──
        self.max_health = 100
        self.health = 100
        self.max_stamina = 100
        self.stamina = 100
        self.max_hunger = 100
        self.hunger = 100          # decreases over time
        self.max_thirst = 100
        self.thirst = 100          # decreases over time
        self.is_alive = True

        # ── Movement ──
        self.move_speed = 5.0
        self.run_speed = 9.0
        self.jump_height = 5.0
        self.gravity = 20.0
        self.velocity_y = 0
        self.is_grounded = False
        self.is_running = False

        # ── Camera ──
        self.cam_distance = 4.5     # distance behind player
        self.cam_height   = 2.0     # height above player
        self.cam_yaw      = 0.0     # horizontal orbit
        self.cam_pitch    = -15.0   # vertical tilt (degrees)
        self.mouse_sens   = 40.0
        self.cam_min_pitch = -40.0
        self.cam_max_pitch =  60.0

        # ── Interaction ──
        self.reach = 3.0             # how far player can interact
        self.held_item = None        # currently equipped item
        self.is_attacking = False
        self.attack_timer = 0

        # ── Build player visual ──
        self._build_model(position)
        self._setup_camera()

        # Timing
        self._hunger_timer = 0
        self._thirst_timer = 0

        # Lock cursor
        mouse.locked = True
        mouse.visible = False

    # ─────────────────────────────────────────
    #  BUILD CHARACTER MODEL
    # ─────────────────────────────────────────
    def _build_model(self, position):
        """Procedural character: body parts as entities"""
        px, py, pz = position

        # Pivot (invisible, used for movement)
        self.pivot = Entity(position=(px, py, pz))

        # Body
        self.body = Entity(
            parent=self.pivot,
            model='cube',
            color=color.rgb(60, 90, 60),       # jungle clothes
            scale=(0.5, 0.65, 0.28),
            position=(0, 0, 0),
        )
        # Head
        self.head_node = Entity(
            parent=self.pivot,
            model='sphere',
            color=color.rgb(210, 170, 120),    # skin tone
            scale=(0.35, 0.35, 0.35),
            position=(0, 0.55, 0),
        )
        # Left arm
        self.arm_l = Entity(
            parent=self.pivot,
            model='cube',
            color=color.rgb(210, 170, 120),
            scale=(0.15, 0.55, 0.15),
            position=(-0.35, -0.02, 0),
        )
        # Right arm (holds items)
        self.arm_r = Entity(
            parent=self.pivot,
            model='cube',
            color=color.rgb(210, 170, 120),
            scale=(0.15, 0.55, 0.15),
            position=(0.35, -0.02, 0),
        )
        # Left leg
        self.leg_l = Entity(
            parent=self.pivot,
            model='cube',
            color=color.rgb(50, 70, 100),      # dark trousers
            scale=(0.18, 0.58, 0.18),
            position=(-0.16, -0.63, 0),
        )
        # Right leg
        self.leg_r = Entity(
            parent=self.pivot,
            model='cube',
            color=color.rgb(50, 70, 100),
            scale=(0.18, 0.58, 0.18),
            position=(0.16, -0.63, 0),
        )

        # Shadow blob
        self.shadow = Entity(
            parent=self.pivot,
            model='quad',
            color=color.rgba(0, 0, 0, 80),
            scale=(0.9, 0.9, 0.9),
            rotation_x=90,
            position=(0, -0.98, 0),
        )

    # ─────────────────────────────────────────
    #  CAMERA SETUP
    # ─────────────────────────────────────────
    def _setup_camera(self):
        camera.parent = scene
        camera.position = self.pivot.position + Vec3(0, self.cam_height, -self.cam_distance)
        camera.look_at(self.pivot.position + Vec3(0, 0.5, 0))

    # ─────────────────────────────────────────
    #  UPDATE LOOP
    # ─────────────────────────────────────────
    def update(self):
        if not self.is_alive:
            return
        self._handle_movement()
        self._update_camera()
        self._update_survival_stats()
        self._update_animations()
        self._update_attack()

    # ─────────────────────────────────────────
    #  MOVEMENT
    # ─────────────────────────────────────────
    def _handle_movement(self):
        dt = time.dt
        self.is_running = held_keys['shift'] and self.stamina > 0

        speed = self.run_speed if self.is_running else self.move_speed

        # Direction relative to camera yaw
        yaw_rad = math.radians(self.cam_yaw)
        forward = Vec3(math.sin(yaw_rad), 0, math.cos(yaw_rad))
        right   = Vec3(math.cos(yaw_rad), 0, -math.sin(yaw_rad))

        move = Vec3(0, 0, 0)
        moving = False
        if held_keys['w']:
            move += forward
            moving = True
        if held_keys['s']:
            move -= forward
            moving = True
        if held_keys['a']:
            move -= right
            moving = True
        if held_keys['d']:
            move += right
            moving = True

        if move.length() > 0:
            move = move.normalized() * speed * dt

        # Gravity
        if not self.is_grounded:
            self.velocity_y -= self.gravity * dt
        else:
            if self.velocity_y < 0:
                self.velocity_y = 0

        # Ground check (simple Y floor)
        new_pos = self.pivot.position + move
        new_pos.y += self.velocity_y * dt

        ground_y = self._get_ground_y(new_pos.x, new_pos.z)
        if new_pos.y <= ground_y:
            new_pos.y = ground_y
            self.is_grounded = True
            self.velocity_y = 0
        else:
            self.is_grounded = False

        self.pivot.position = new_pos

        # Rotate player toward movement direction
        if moving and move.length() > 0:
            target_rot = math.degrees(math.atan2(move.x, move.z))
            self.pivot.rotation_y = lerp(self.pivot.rotation_y, target_rot, 10 * dt)

        # Stamina drain/regen
        if self.is_running and moving:
            self.stamina = max(0, self.stamina - 15 * dt)
        else:
            self.stamina = min(self.max_stamina, self.stamina + 8 * dt)

    def _get_ground_y(self, x, z):
        """Simple terrain height query - will hook into terrain later"""
        if self.world:
            return self.world.get_height(x, z)
        return 0.0

    # ─────────────────────────────────────────
    #  CAMERA
    # ─────────────────────────────────────────
    def _update_camera(self):
        dt = time.dt

        # Mouse look
        self.cam_yaw   += mouse.velocity[0] * self.mouse_sens
        self.cam_pitch -= mouse.velocity[1] * self.mouse_sens
        self.cam_pitch  = clamp(self.cam_pitch, self.cam_min_pitch, self.cam_max_pitch)

        yaw_rad   = math.radians(self.cam_yaw)
        pitch_rad = math.radians(self.cam_pitch)

        # Orbit position
        offset_x = math.sin(yaw_rad) * math.cos(pitch_rad) * self.cam_distance
        offset_y = math.sin(pitch_rad) * self.cam_distance + self.cam_height
        offset_z = math.cos(yaw_rad) * math.cos(pitch_rad) * self.cam_distance

        target_cam_pos = self.pivot.position + Vec3(-offset_x, offset_y, -offset_z)

        # Smooth follow
        camera.position = lerp(camera.position, target_cam_pos, 12 * dt)
        look_target = self.pivot.position + Vec3(0, 0.5, 0)
        camera.look_at(look_target)

    # ─────────────────────────────────────────
    #  SURVIVAL STATS
    # ─────────────────────────────────────────
    def _update_survival_stats(self):
        dt = time.dt
        self._hunger_timer += dt
        self._thirst_timer += dt

        # Hunger drains every ~10 min real time
        if self._hunger_timer >= 6.0:
            self.hunger = max(0, self.hunger - 1)
            self._hunger_timer = 0
            if self.hunger == 0:
                self.health = max(0, self.health - 0.5)

        # Thirst drains faster
        if self._thirst_timer >= 4.0:
            self.thirst = max(0, self.thirst - 1)
            self._thirst_timer = 0
            if self.thirst == 0:
                self.health = max(0, self.health - 1)

        if self.health <= 0:
            self._die()

    def _die(self):
        self.is_alive = False
        print("Player died.")
        # TODO: death screen

    # ─────────────────────────────────────────
    #  ANIMATIONS (leg/arm swing)
    # ─────────────────────────────────────────
    def _update_animations(self):
        t = time.time
        moving = any([held_keys['w'], held_keys['s'],
                      held_keys['a'], held_keys['d']])
        if moving:
            freq = 8.0 if self.is_running else 5.0
            swing = math.sin(t * freq) * 25
            self.leg_l.rotation_x =  swing
            self.leg_r.rotation_x = -swing
            self.arm_l.rotation_x = -swing * 0.6
            self.arm_r.rotation_x =  swing * 0.6
        else:
            # Idle breathing
            breathe = math.sin(t * 1.5) * 0.5
            self.body.position = Vec3(0, breathe * 0.01, 0)
            self.leg_l.rotation_x = lerp(self.leg_l.rotation_x, 0, 8*time.dt)
            self.leg_r.rotation_x = lerp(self.leg_r.rotation_x, 0, 8*time.dt)
            self.arm_l.rotation_x = lerp(self.arm_l.rotation_x, 0, 8*time.dt)
            self.arm_r.rotation_x = lerp(self.arm_r.rotation_x, 0, 8*time.dt)

    # ─────────────────────────────────────────
    #  ATTACK
    # ─────────────────────────────────────────
    def _update_attack(self):
        if self.is_attacking:
            self.attack_timer -= time.dt
            swing = math.sin((1 - self.attack_timer / 0.4) * math.pi) * -60
            self.arm_r.rotation_x = swing
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_timer = 0

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 0.4

    # ─────────────────────────────────────────
    #  INPUT
    # ─────────────────────────────────────────
    def handle_input(self, key):
        if key == 'space' and self.is_grounded:
            self.velocity_y = self.jump_height

        if key == 'left mouse down':
            self.attack()

        if key == 'tab':
            # Toggle inventory (handled by inventory system)
            pass

    # ─────────────────────────────────────────
    #  PROPERTIES
    # ─────────────────────────────────────────
    @property
    def position(self):
        return self.pivot.position

    @position.setter
    def position(self, val):
        self.pivot.position = val

    def eat(self, nutrition):
        self.hunger = min(self.max_hunger, self.hunger + nutrition)

    def drink(self, hydration):
        self.thirst = min(self.max_thirst, self.thirst + hydration)

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
