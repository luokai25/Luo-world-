"""
Inventory Screen UI
24-slot grid with item details panel
Tap slot to select, tap again to equip/use/drop
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from game.inventory import ITEMS


class SlotWidget(Button):
    """Single inventory slot"""

    def __init__(self, slot_index, inv_slot, on_select, **kwargs):
        super().__init__(**kwargs)
        self.slot_index = slot_index
        self.inv_slot   = inv_slot
        self.on_select  = on_select
        self.selected   = False

        self.size_hint  = (None, None)
        self.size       = (dp(72), dp(72))
        self.background_normal  = ''
        self.background_color   = (0.12, 0.18, 0.12, 0.9)

        self._refresh()
        self.bind(on_press=self._pressed)

    def _refresh(self):
        if self.inv_slot.empty:
            self.text = ''
        else:
            item_data = ITEMS.get(self.inv_slot.item_id, {})
            icon  = item_data.get('icon', '?')
            count = self.inv_slot.count
            dur   = self.inv_slot.durability
            max_dur = item_data.get('max_durability', None)

            self.text = f"{icon}"
            if count > 1:
                self.text += f"\n[size=11]{count}[/size]"
            if dur is not None and max_dur:
                pct = dur / max_dur
                bar = '▓' * int(pct * 5) + '░' * (5 - int(pct * 5))
                self.text += f"\n[size=9][color={'44ff44' if pct>0.5 else 'ffaa00' if pct>0.2 else 'ff4444'}]{bar}[/color][/size]"
        self.markup = True
        self.font_size = dp(24)

    def set_selected(self, sel):
        self.selected = sel
        if sel:
            self.background_color = (0.25, 0.55, 0.20, 1.0)
        else:
            self.background_color = (0.12, 0.18, 0.12, 0.9)

    def _pressed(self, *args):
        self.on_select(self.slot_index)

    def refresh(self, inv_slot):
        self.inv_slot = inv_slot
        self._refresh()


class InventoryScreen(FloatLayout):
    """Full inventory screen - slides up from bottom"""

    def __init__(self, inventory, on_close, on_craft_open, **kwargs):
        super().__init__(**kwargs)
        self.inventory     = inventory
        self.on_close      = on_close
        self.on_craft_open = on_craft_open
        self.is_open       = False
        self._selected     = None
        self._slot_widgets = []

        w, h = Window.size
        panel_h = h * 0.85

        self.panel = FloatLayout(
            size_hint=(None, None),
            size=(w, panel_h),
            pos=(0, -panel_h),
        )
        with self.panel.canvas.before:
            Color(0.07, 0.12, 0.07, 0.97)
            self._bg = Rectangle(pos=self.panel.pos, size=self.panel.size)
            Color(0.25, 0.5, 0.2, 1)
            self._border_top = Line(points=[0, 0, w, 0], width=dp(2))
        self.panel.bind(pos=self._update_bg)

        # Title + buttons
        self._build_header(w, panel_h)
        # Slot grid
        self._build_grid(w, panel_h)
        # Detail panel
        self._build_detail(w, panel_h)

        self.add_widget(self.panel)

    def _build_header(self, w, panel_h):
        hbar = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(w, dp(52)),
            pos=(0, panel_h - dp(52)),
            padding=(dp(16), dp(8)),
        )
        hbar.add_widget(Label(
            text='🎒  INVENTORY',
            font_size=dp(20), bold=True,
            color=(0.85, 0.95, 0.7, 1),
            size_hint=(1, 1),
        ))
        craft_btn = Button(
            text='⚒ CRAFT', font_size=dp(13),
            size_hint=(None, None), size=(dp(90), dp(40)),
            background_color=(0.2, 0.5, 0.15, 0.9),
            background_normal='',
        )
        craft_btn.bind(on_press=lambda x: self.on_craft_open())
        hbar.add_widget(craft_btn)

        close_btn = Button(
            text='✕', font_size=dp(18),
            size_hint=(None, None), size=(dp(44), dp(44)),
            background_color=(0.5, 0.2, 0.2, 0.9),
            background_normal='',
        )
        close_btn.bind(on_press=lambda x: self.close())
        hbar.add_widget(close_btn)
        self.panel.add_widget(hbar)

    def _build_grid(self, w, panel_h):
        scroll_h = panel_h * 0.55
        self.scroll = ScrollView(
            size_hint=(None, None),
            size=(w, scroll_h),
            pos=(0, panel_h - dp(52) - scroll_h),
            do_scroll_x=False,
        )
        self.grid = GridLayout(
            cols=4,
            spacing=dp(6),
            padding=dp(10),
            size_hint_y=None,
        )
        self.grid.bind(minimum_height=self.grid.setter('height'))

        self._slot_widgets = []
        for i, slot in enumerate(self.inventory.slots):
            sw = SlotWidget(
                slot_index=i,
                inv_slot=slot,
                on_select=self._select_slot,
            )
            self.grid.add_widget(sw)
            self._slot_widgets.append(sw)

        self.scroll.add_widget(self.grid)
        self.panel.add_widget(self.scroll)

    def _build_detail(self, w, panel_h):
        detail_h = panel_h * 0.28
        self.detail_panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(w, detail_h),
            pos=(0, 0),
            padding=dp(16),
            spacing=dp(6),
        )
        with self.detail_panel.canvas.before:
            Color(0.09, 0.15, 0.09, 1)
            Rectangle(pos=self.detail_panel.pos, size=self.detail_panel.size)

        self.detail_name = Label(
            text='Select an item',
            font_size=dp(18), bold=True,
            color=(0.9, 0.95, 0.8, 1),
            size_hint=(1, None), height=dp(28),
            halign='left',
        )
        self.detail_desc = Label(
            text='',
            font_size=dp(13),
            color=(0.75, 0.8, 0.7, 1),
            size_hint=(1, None), height=dp(48),
            halign='left', valign='top',
            text_size=(w - dp(32), dp(48)),
        )
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(44),
            spacing=dp(8),
        )
        self.btn_equip = Button(
            text='EQUIP', font_size=dp(14),
            background_color=(0.2, 0.55, 0.15, 1),
            background_normal='',
        )
        self.btn_equip.bind(on_press=self._equip_selected)
        self.btn_use = Button(
            text='USE', font_size=dp(14),
            background_color=(0.15, 0.45, 0.55, 1),
            background_normal='',
        )
        self.btn_use.bind(on_press=self._use_selected)
        self.btn_drop = Button(
            text='DROP', font_size=dp(14),
            background_color=(0.5, 0.2, 0.15, 1),
            background_normal='',
        )
        self.btn_drop.bind(on_press=self._drop_selected)

        btn_row.add_widget(self.btn_equip)
        btn_row.add_widget(self.btn_use)
        btn_row.add_widget(self.btn_drop)

        self.detail_panel.add_widget(self.detail_name)
        self.detail_panel.add_widget(self.detail_desc)
        self.detail_panel.add_widget(btn_row)
        self.panel.add_widget(self.detail_panel)

    def _select_slot(self, idx):
        # Deselect previous
        if self._selected is not None:
            self._slot_widgets[self._selected].set_selected(False)

        if self._selected == idx:
            self._selected = None
            self.detail_name.text = 'Select an item'
            self.detail_desc.text = ''
            return

        self._selected = idx
        self._slot_widgets[idx].set_selected(True)

        slot = self.inventory.slots[idx]
        if slot.empty:
            self.detail_name.text = 'Empty slot'
            self.detail_desc.text = ''
        else:
            item_data = ITEMS.get(slot.item_id, {})
            icon = item_data.get('icon', '')
            self.detail_name.text = f"{icon}  {item_data.get('name','?')}"
            self.detail_desc.text = item_data.get('description', '')
            if slot.durability is not None:
                max_dur = item_data.get('max_durability', slot.durability)
                self.detail_desc.text += f"\nDurability: {slot.durability}/{max_dur}"
            if slot.count > 1:
                self.detail_desc.text += f"\nQuantity: {slot.count}"

    def _equip_selected(self, *args):
        if self._selected is None:
            return
        # Move to first hotbar slot
        slot = self.inventory.slots[self._selected]
        if not slot.empty:
            self.inventory.equipped_slot = self._selected % self.inventory.hotbar_size

    def _use_selected(self, *args):
        if self._selected is None:
            return
        old = self.inventory.equipped_slot
        self.inventory.equipped_slot = self._selected
        self.inventory.use_equipped()
        self.inventory.equipped_slot = old
        self.refresh()

    def _drop_selected(self, *args):
        if self._selected is None:
            return
        slot = self.inventory.slots[self._selected]
        if not slot.empty:
            self.inventory.remove_item(slot.item_id, 1)
            self.refresh()
            self.detail_name.text = 'Select an item'
            self.detail_desc.text = ''
            self._selected = None

    def refresh(self):
        for i, sw in enumerate(self._slot_widgets):
            sw.refresh(self.inventory.slots[i])

    def open(self):
        if self.is_open:
            return
        self.is_open = True
        self.refresh()
        anim = Animation(pos=(0, 0), duration=0.32, t='out_cubic')
        anim.start(self.panel)

    def close(self):
        if not self.is_open:
            return
        self.is_open = False
        _, h = Window.size
        panel_h = h * 0.85
        anim = Animation(pos=(0, -panel_h), duration=0.25, t='in_cubic')
        anim.start(self.panel)
        self.on_close()

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def _update_bg(self, *args):
        self._bg.pos  = self.panel.pos
        self._bg.size = self.panel.size
        w, _ = Window.size
        y = self.panel.pos[1] + self.panel.size[1]
        self._border_top.points = [self.panel.pos[0], y, self.panel.pos[0]+self.panel.size[0], y]
