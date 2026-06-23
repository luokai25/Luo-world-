"""
HUD - Heads Up Display
Health, Hunger, Thirst, Stamina bars
Hotbar (8 slots)
Crosshair
Interaction prompt
Time of day
"""

from ursina import *
from ursina.prefabs.health_bar import HealthBar
from game.inventory import ITEMS


class HUD:
    def __init__(self, player=None, inventory=None):
        self.player = player
        self.inventory = inventory
        self.visible = True

        self._build_crosshair()
        self._build_stat_bars()
        self._build_hotbar()
        self._build_interaction_prompt()
        self._build_time_display()

    # ─────────────────────────────────────
    #  CROSSHAIR
    # ─────────────────────────────────────
    def _build_crosshair(self):
        size = 0.012
        thickness = 0.002
        col = color.rgba(255, 255, 255, 200)

        self.ch_h = Entity(
            parent=camera.ui,
            model='quad',
            color=col,
            scale=(size, thickness),
            position=(0, 0, -0.1),
        )
        self.ch_v = Entity(
            parent=camera.ui,
            model='quad',
            color=col,
            scale=(thickness, size),
            position=(0, 0, -0.1),
        )
        # Dot center
        self.ch_dot = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(255, 255, 255, 150),
            scale=(thickness, thickness),
            position=(0, 0, -0.1),
        )

    # ─────────────────────────────────────
    #  STAT BARS (bottom left)
    # ─────────────────────────────────────
    def _build_stat_bars(self):
        bar_w = 0.18
        bar_h = 0.016
        x = -0.82
        y_start = -0.40
        gap = 0.030

        # Health - red
        self.health_bg = self._bar_bg(x, y_start, bar_w, bar_h)
        self.health_bar = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(220, 50, 50),
            scale=(bar_w, bar_h),
            origin=(-0.5, 0),
            position=(x, y_start, -0.1),
        )
        self.health_icon = Text(
            '❤', parent=camera.ui,
            position=(x - 0.025, y_start, -0.1),
            scale=1.1, origin=(0, 0),
        )

        # Hunger - orange
        y = y_start - gap
        self.hunger_bg = self._bar_bg(x, y, bar_w, bar_h)
        self.hunger_bar = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(220, 130, 30),
            scale=(bar_w, bar_h),
            origin=(-0.5, 0),
            position=(x, y, -0.1),
        )
        self.hunger_icon = Text(
            '🍖', parent=camera.ui,
            position=(x - 0.025, y, -0.1),
            scale=1.1, origin=(0, 0),
        )

        # Thirst - blue
        y -= gap
        self.thirst_bg = self._bar_bg(x, y, bar_w, bar_h)
        self.thirst_bar = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(50, 130, 220),
            scale=(bar_w, bar_h),
            origin=(-0.5, 0),
            position=(x, y, -0.1),
        )
        self.thirst_icon = Text(
            '💧', parent=camera.ui,
            position=(x - 0.025, y, -0.1),
            scale=1.1, origin=(0, 0),
        )

        # Stamina - yellow-green
        y -= gap
        self.stamina_bg = self._bar_bg(x, y, bar_w, bar_h)
        self.stamina_bar = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(170, 220, 50),
            scale=(bar_w, bar_h),
            origin=(-0.5, 0),
            position=(x, y, -0.1),
        )
        self.stamina_icon = Text(
            '⚡', parent=camera.ui,
            position=(x - 0.025, y, -0.1),
            scale=1.1, origin=(0, 0),
        )

    def _bar_bg(self, x, y, w, h):
        return Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 120),
            scale=(w, h),
            origin=(-0.5, 0),
            position=(x, y, -0.05),
        )

    # ─────────────────────────────────────
    #  HOTBAR (bottom center)
    # ─────────────────────────────────────
    def _build_hotbar(self):
        self.hotbar_slots = []
        self.hotbar_labels = []
        n = 8
        slot_size = 0.07
        gap = 0.004
        total_w = n * (slot_size + gap)
        start_x = -total_w / 2 + slot_size / 2
        y = -0.44

        for i in range(n):
            x = start_x + i * (slot_size + gap)

            # Slot background
            slot = Entity(
                parent=camera.ui,
                model='quad',
                color=color.rgba(20, 20, 20, 160),
                scale=(slot_size, slot_size),
                position=(x, y, -0.1),
            )
            # Border
            border = Entity(
                parent=camera.ui,
                model='quad',
                color=color.rgba(150, 140, 120, 180),
                scale=(slot_size + 0.003, slot_size + 0.003),
                position=(x, y, -0.08),
            )

            # Item icon label
            label = Text(
                '', parent=camera.ui,
                position=(x, y, -0.15),
                scale=2.2, origin=(0, 0),
            )

            # Number
            num = Text(
                str(i+1), parent=camera.ui,
                position=(x - slot_size*0.35, y + slot_size*0.35, -0.15),
                scale=0.6, color=color.rgba(200, 200, 200, 180),
                origin=(0, 0),
            )

            self.hotbar_slots.append((slot, border, label, num))
            self.hotbar_labels.append(label)

        # Selection highlight
        self.hotbar_select = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(255, 220, 80, 200),
            scale=(slot_size + 0.006, slot_size + 0.006),
            position=(start_x, y, -0.07),
        )
        self._hotbar_start_x = start_x
        self._hotbar_slot_w  = slot_size + gap
        self._hotbar_y       = y

    # ─────────────────────────────────────
    #  INTERACTION PROMPT
    # ─────────────────────────────────────
    def _build_interaction_prompt(self):
        self.interact_text = Text(
            '', parent=camera.ui,
            position=(0, -0.12, -0.1),
            scale=1.4,
            origin=(0, 0),
            color=color.rgba(255, 255, 255, 230),
            background=True,
        )

    # ─────────────────────────────────────
    #  TIME DISPLAY (top right)
    # ─────────────────────────────────────
    def _build_time_display(self):
        self.time_text = Text(
            '10:00', parent=camera.ui,
            position=(0.78, 0.46, -0.1),
            scale=1.2,
            origin=(0, 0),
            color=color.rgba(255, 240, 180, 220),
        )
        self.day_text = Text(
            'Day 1', parent=camera.ui,
            position=(0.78, 0.43, -0.1),
            scale=0.9,
            origin=(0, 0),
            color=color.rgba(200, 200, 200, 180),
        )

    # ─────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────
    def update(self):
        if not self.player:
            return

        p = self.player
        inv = self.inventory

        # Stat bars - scale X
        max_w = 0.18
        self.health_bar.scale_x  = max_w * (p.health / p.max_health)
        self.hunger_bar.scale_x  = max_w * (p.hunger / p.max_hunger)
        self.thirst_bar.scale_x  = max_w * (p.thirst / p.max_thirst)
        self.stamina_bar.scale_x = max_w * (p.stamina / p.max_stamina)

        # Hotbar icons
        if inv:
            for i, (slot_e, border, label, num) in enumerate(self.hotbar_slots):
                inv_slot = inv.slots[i]
                if not inv_slot.empty:
                    item_data = ITEMS.get(inv_slot.item_id, {})
                    icon = item_data.get('icon', '?')
                    count_str = f" x{inv_slot.count}" if inv_slot.count > 1 else ""
                    label.text = icon
                else:
                    label.text = ''

            # Move selection box
            sel_x = self._hotbar_start_x + inv.equipped_slot * self._hotbar_slot_w
            self.hotbar_select.x = sel_x

    def set_interact_prompt(self, text):
        self.interact_text.text = text

    def clear_interact_prompt(self):
        self.interact_text.text = ''

    def handle_input(self, key):
        pass
