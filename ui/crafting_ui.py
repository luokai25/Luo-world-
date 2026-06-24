"""
Crafting UI - Android touch-friendly recipe browser
Slide up from bottom, scroll through recipes, tap to craft
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from game.inventory import RECIPES, ITEMS


class RecipeCard(BoxLayout):
    """Single recipe card - shows ingredients + output + craft button"""

    def __init__(self, recipe_id, recipe, inventory, on_craft, **kwargs):
        super().__init__(orientation='vertical', padding=dp(8),
                         spacing=dp(4), size_hint=(None, None),
                         size=(dp(200), dp(160)), **kwargs)
        self.recipe_id  = recipe_id
        self.recipe     = recipe
        self.inventory  = inventory
        self.on_craft   = on_craft

        with self.canvas.before:
            Color(0.12, 0.18, 0.12, 0.92)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(0.3, 0.5, 0.25, 0.8)
            self.border = Line(rounded_rectangle=[*self.pos, *self.size, dp(10)], width=1.2)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Output item
        out_id, out_count = recipe['output']
        out_data = ITEMS.get(out_id, {})
        self.add_widget(Label(
            text=f"{out_data.get('icon','?')} {out_data.get('name','?')}",
            font_size=dp(15), bold=True,
            color=(0.9, 0.95, 0.8, 1),
            size_hint=(1, None), height=dp(26),
        ))

        # Ingredients
        ing_text = ''
        for item_id, count in recipe['inputs'].items():
            have = inventory.count_item(item_id)
            item_data = ITEMS.get(item_id, {})
            color_tag = '[color=88ff88]' if have >= count else '[color=ff6666]'
            ing_text += f"{color_tag}{item_data.get('icon','?')} {item_data.get('name','?')} {have}/{count}[/color]\n"

        self.ing_label = Label(
            text=ing_text.strip(),
            markup=True,
            font_size=dp(11),
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, None), height=dp(60),
            halign='left', valign='top',
            text_size=(dp(184), dp(60)),
        )
        self.add_widget(self.ing_label)

        # Tool required
        tool = recipe.get('required_tool')
        if tool:
            tool_data = ITEMS.get(tool, {})
            self.add_widget(Label(
                text=f"Needs: {tool_data.get('icon','?')} {tool_data.get('name', tool)}",
                font_size=dp(10),
                color=(0.7, 0.7, 0.5, 1),
                size_hint=(1, None), height=dp(18),
            ))

        # Craft button
        can = self._can_craft()
        self.craft_btn = Button(
            text='CRAFT' if can else 'MISSING',
            font_size=dp(13), bold=True,
            size_hint=(1, None), height=dp(34),
            background_color=(0.2, 0.65, 0.2, 1) if can else (0.4, 0.2, 0.2, 1),
            background_normal='',
        )
        self.craft_btn.bind(on_press=self._on_craft_press)
        self.add_widget(self.craft_btn)

    def _can_craft(self):
        return all(
            self.inventory.count_item(k) >= v
            for k, v in self.recipe['inputs'].items()
        )

    def _on_craft_press(self, *args):
        if self._can_craft():
            self.on_craft(self.recipe_id)
            self.refresh()

    def refresh(self):
        can = self._can_craft()
        out_id, _ = self.recipe['output']
        out_data = ITEMS.get(out_id, {})

        ing_text = ''
        for item_id, count in self.recipe['inputs'].items():
            have = self.inventory.count_item(item_id)
            item_data = ITEMS.get(item_id, {})
            color_tag = '[color=88ff88]' if have >= count else '[color=ff6666]'
            ing_text += f"{color_tag}{item_data.get('icon','?')} {item_data.get('name','?')} {have}/{count}[/color]\n"
        self.ing_label.text = ing_text.strip()

        self.craft_btn.text = 'CRAFT' if can else 'MISSING'
        self.craft_btn.background_color = (0.2, 0.65, 0.2, 1) if can else (0.4, 0.2, 0.2, 1)

    def _update_bg(self, *args):
        self.bg.pos  = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = [*self.pos, *self.size, dp(10)]


class CraftingUI(FloatLayout):
    """
    Full crafting screen.
    Slides up from bottom on open, slides down on close.
    Search bar + scrollable recipe grid.
    """

    def __init__(self, inventory, on_craft, **kwargs):
        super().__init__(**kwargs)
        self.inventory = inventory
        self.on_craft  = on_craft
        self.is_open   = False
        self._cards    = []

        w, h = Window.size
        panel_h = h * 0.75

        # Panel (starts below screen)
        self.panel = FloatLayout(
            size_hint=(None, None),
            size=(w, panel_h),
            pos=(0, -panel_h),
        )
        with self.panel.canvas.before:
            Color(0.07, 0.12, 0.07, 0.97)
            self.panel_bg = Rectangle(pos=self.panel.pos, size=self.panel.size)
            Color(0.25, 0.5, 0.2, 1)
            self.panel_top_line = Line(points=[0, panel_h, w, panel_h], width=2)
        self.panel.bind(pos=self._update_panel_bg, size=self._update_panel_bg)

        # Title bar
        title_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(w, dp(50)),
            pos=(0, panel_h - dp(50)),
            padding=(dp(16), dp(8)),
        )
        title_bar.add_widget(Label(
            text='⚒  CRAFTING',
            font_size=dp(20), bold=True,
            color=(0.85, 0.95, 0.7, 1),
            size_hint=(1, 1),
            halign='left',
        ))
        close_btn = Button(
            text='✕', font_size=dp(18),
            size_hint=(None, None), size=(dp(44), dp(44)),
            background_color=(0.5, 0.2, 0.2, 0.9),
            background_normal='',
        )
        close_btn.bind(on_press=lambda x: self.close())
        title_bar.add_widget(close_btn)
        self.panel.add_widget(title_bar)

        # Category filter buttons
        categories = ['All', '⚒ Tools', '🍖 Food', '🏹 Weapons', '🏠 Builds']
        cat_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(w, dp(44)),
            pos=(0, panel_h - dp(98)),
            spacing=dp(6), padding=(dp(8), dp(4)),
        )
        self._active_cat = 'All'
        self._cat_buttons = {}
        for cat in categories:
            btn = Button(
                text=cat, font_size=dp(12),
                background_normal='',
                background_color=(0.2, 0.4, 0.2, 1) if cat == 'All' else (0.15, 0.25, 0.15, 1),
            )
            btn.bind(on_press=lambda x, c=cat: self._filter_category(c))
            cat_bar.add_widget(btn)
            self._cat_buttons[cat] = btn
        self.panel.add_widget(cat_bar)

        # Scroll area for recipe cards
        scroll_h = panel_h - dp(110)
        self.scroll = ScrollView(
            size_hint=(None, None),
            size=(w, scroll_h),
            pos=(0, 0),
            do_scroll_x=False,
            do_scroll_y=True,
        )
        self.grid = GridLayout(
            cols=2,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None,
        )
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.panel.add_widget(self.scroll)

        self.add_widget(self.panel)
        self._build_cards()

    def _build_cards(self, category='All'):
        self.grid.clear_widgets()
        self._cards = []

        cat_map = {
            'All': None,
            '⚒ Tools': ['tool'],
            '🍖 Food': ['food'],
            '🏹 Weapons': ['weapon', 'ammo'],
            '🏠 Builds': ['structure'],
        }
        allowed_cats = cat_map.get(category)

        for recipe_id, recipe in RECIPES.items():
            out_id = recipe['output'][0]
            out_data = ITEMS.get(out_id, {})
            out_cat = out_data.get('category', '')

            if allowed_cats and out_cat not in allowed_cats:
                continue

            card = RecipeCard(
                recipe_id=recipe_id,
                recipe=recipe,
                inventory=self.inventory,
                on_craft=self._craft,
            )
            self.grid.add_widget(card)
            self._cards.append(card)

    def _filter_category(self, cat):
        self._active_cat = cat
        for c, btn in self._cat_buttons.items():
            btn.background_color = (0.2, 0.4, 0.2, 1) if c == cat else (0.15, 0.25, 0.15, 1)
        self._build_cards(cat)

    def _craft(self, recipe_id):
        self.on_craft(recipe_id)
        for card in self._cards:
            card.refresh()

    def open(self):
        if self.is_open:
            return
        self.is_open = True
        w, h = Window.size
        panel_h = h * 0.75
        anim = Animation(pos=(0, 0), duration=0.35, t='out_cubic')
        anim.start(self.panel)
        self._build_cards(self._active_cat)

    def close(self):
        if not self.is_open:
            return
        self.is_open = False
        w, h = Window.size
        panel_h = h * 0.75
        anim = Animation(pos=(0, -panel_h), duration=0.28, t='in_cubic')
        anim.start(self.panel)

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def refresh(self):
        for card in self._cards:
            card.refresh()

    def _update_panel_bg(self, *args):
        self.panel_bg.pos  = self.panel.pos
        self.panel_bg.size = self.panel.size
