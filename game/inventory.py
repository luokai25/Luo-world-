"""
Inventory System
- Item definitions
- Starting items: stone axe, 3x cooked meat, wooden water cup
- Item pickup / drop / use
- Crafting recipe registry (expandable)
"""

try:
    from ursina import *
except ImportError:
    pass
import json
import os


# ──────────────────────────────────────────────
#  ITEM DEFINITIONS
# ──────────────────────────────────────────────

ITEMS = {
    # Starting items
    'stone_axe': {
        'name': 'Stone Axe',
        'description': 'A crude axe chipped from flint and bound to a stick. '
                       'Used for chopping wood and hunting.',
        'icon': '🪓',
        'weight': 0.8,
        'stackable': False,
        'max_stack': 1,
        'category': 'tool',
        'damage': 15,
        'durability': 100,
        'max_durability': 100,
        'use_on': ['tree', 'animal'],
    },
    'cooked_meat': {
        'name': 'Cooked Cow Meat',
        'description': 'A thick slab of cow meat, charred over fire. Restores hunger.',
        'icon': '🥩',
        'weight': 0.4,
        'stackable': True,
        'max_stack': 10,
        'category': 'food',
        'nutrition': 45,
        'hydration': 5,
    },
    'wooden_cup': {
        'name': 'Wooden Cup (Water)',
        'description': 'A hand-carved wooden cup filled with clean water. '
                       'Restores thirst.',
        'icon': '🥤',
        'weight': 0.3,
        'stackable': False,
        'max_stack': 1,
        'category': 'drink',
        'hydration': 60,
        'nutrition': 0,
        'becomes': 'wooden_cup_empty',   # after drinking
    },

    # Resources (collectible)
    'wood_log': {
        'name': 'Wood Log',
        'description': 'A raw log from a jungle tree.',
        'icon': '🪵',
        'weight': 2.0,
        'stackable': True,
        'max_stack': 20,
        'category': 'resource',
    },
    'stone': {
        'name': 'Stone',
        'description': 'A rough chunk of stone.',
        'icon': '🪨',
        'weight': 1.5,
        'stackable': True,
        'max_stack': 30,
        'category': 'resource',
    },
    'stick': {
        'name': 'Stick',
        'description': 'A straight wooden stick.',
        'icon': '|',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 30,
        'category': 'resource',
    },
    'flint': {
        'name': 'Flint',
        'description': 'Sharp flint stone, useful for tools.',
        'icon': '◇',
        'weight': 0.3,
        'stackable': True,
        'max_stack': 20,
        'category': 'resource',
    },
    'vine': {
        'name': 'Vine',
        'description': 'A strong jungle vine, used for binding.',
        'icon': '~',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 20,
        'category': 'resource',
    },
    'raw_meat': {
        'name': 'Raw Meat',
        'description': 'Uncooked animal meat. Must be cooked before eating.',
        'icon': '🫀',
        'weight': 0.5,
        'stackable': True,
        'max_stack': 10,
        'category': 'food_raw',
    },
    'wooden_cup_empty': {
        'name': 'Wooden Cup (Empty)',
        'description': 'An empty wooden cup. Fill it with water.',
        'icon': '🪣',
        'weight': 0.1,
        'stackable': False,
        'max_stack': 1,
        'category': 'tool',
    },
    'campfire': {
        'name': 'Campfire',
        'description': 'A lit campfire. Use to cook food.',
        'icon': '🔥',
        'weight': 0,
        'stackable': False,
        'max_stack': 1,
        'category': 'structure',
    },
    'wooden_spear': {
        'name': 'Wooden Spear',
        'description': 'A sharpened stick. Good for hunting.',
        'icon': '🏹',
        'weight': 0.6,
        'stackable': False,
        'max_stack': 1,
        'category': 'weapon',
        'damage': 20,
        'durability': 60,
        'max_durability': 60,
    },
    'rope': {
        'name': 'Rope',
        'description': 'Twisted vines, strong binding.',
        'icon': '〰',
        'weight': 0.2,
        'stackable': True,
        'max_stack': 10,
        'category': 'resource',
    },
    'shelter_frame': {
        'name': 'Shelter Frame',
        'description': 'Basic frame for a lean-to shelter.',
        'icon': '🏠',
        'weight': 0,
        'stackable': False,
        'max_stack': 1,
        'category': 'structure',
    },

    # ── World collectibles ──
    'fruit': {
        'name': 'Jungle Fruit',
        'description': 'A ripe fruit fallen from the canopy. Sweet and hydrating.',
        'icon': '🍈',
        'weight': 0.3,
        'stackable': True,
        'max_stack': 10,
        'category': 'food',
        'nutrition': 20,
        'hydration': 15,
    },
    'berry': {
        'name': 'Wild Berries',
        'description': 'Small red berries. Good for a quick snack.',
        'icon': '🫐',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 20,
        'category': 'food',
        'nutrition': 10,
        'hydration': 8,
    },
    'mushroom_edible': {
        'name': 'Edible Mushroom',
        'description': 'A safe jungle mushroom. Earthy taste.',
        'icon': '🍄',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 15,
        'category': 'food',
        'nutrition': 15,
        'hydration': 3,
    },
    'mushroom_poisonous': {
        'name': 'Poisonous Mushroom',
        'description': '⚠️ Do NOT eat. Use for crafting poison.',
        'icon': '🍄',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 10,
        'category': 'resource',
    },
    'hide': {
        'name': 'Animal Hide',
        'description': 'Rough animal hide. Can be crafted into clothing.',
        'icon': '🟫',
        'weight': 0.8,
        'stackable': True,
        'max_stack': 10,
        'category': 'resource',
    },
    'feather': {
        'name': 'Feather',
        'description': 'A bird feather. Useful for arrows.',
        'icon': '🪶',
        'weight': 0.05,
        'stackable': True,
        'max_stack': 30,
        'category': 'resource',
    },
    'iron_ore': {
        'name': 'Iron Ore',
        'description': 'Raw iron ore from rocky hills. Smelt it into iron.',
        'icon': '⬛',
        'weight': 2.0,
        'stackable': True,
        'max_stack': 20,
        'category': 'resource',
    },
    'water': {
        'name': 'Water',
        'description': 'Clean water. Used to fill cups.',
        'icon': '💧',
        'weight': 0,
        'stackable': False,
        'max_stack': 1,
        'category': 'resource',
    },
    'mushroom_cooked': {
        'name': 'Cooked Mushroom',
        'description': 'A cooked jungle mushroom. Safe to eat.',
        'icon': '🍄',
        'weight': 0.1,
        'stackable': True,
        'max_stack': 15,
        'category': 'food',
        'nutrition': 25,
        'hydration': 5,
    },
    'roasted_fruit': {
        'name': 'Roasted Fruit',
        'description': 'Sweet roasted jungle fruit. Very hydrating.',
        'icon': '🍈',
        'weight': 0.2,
        'stackable': True,
        'max_stack': 10,
        'category': 'food',
        'nutrition': 30,
        'hydration': 20,
    },
    'torch': {
        'name': 'Torch',
        'description': 'Provides light and warmth at night.',
        'icon': '🔦',
        'weight': 0.3,
        'stackable': False,
        'max_stack': 1,
        'category': 'tool',
        'durability': 300,
        'max_durability': 300,
    },
    'stone_knife': {
        'name': 'Stone Knife',
        'description': 'Sharp stone knife. Fast for skinning animals.',
        'icon': '🔪',
        'weight': 0.3,
        'stackable': False,
        'max_stack': 1,
        'category': 'tool',
        'damage': 10,
        'durability': 80,
        'max_durability': 80,
    },
    'arrow': {
        'name': 'Arrow',
        'description': 'A sharpened arrow for hunting.',
        'icon': '➶',
        'weight': 0.05,
        'stackable': True,
        'max_stack': 30,
        'category': 'ammo',
    },
    'bow': {
        'name': 'Wooden Bow',
        'description': 'A simple hunting bow.',
        'icon': '🏹',
        'weight': 0.5,
        'stackable': False,
        'max_stack': 1,
        'category': 'weapon',
        'damage': 25,
        'durability': 40,
        'max_durability': 40,
    },
    'leather_armor': {
        'name': 'Leather Armor',
        'description': 'Hide armor. Reduces damage taken.',
        'icon': '🥋',
        'weight': 2.0,
        'stackable': False,
        'max_stack': 1,
        'category': 'armor',
        'defense': 10,
    },
}

# ──────────────────────────────────────────────
#  CRAFTING RECIPES
#  "inputs": {item_id: count}, "output": (item_id, count)
# ──────────────────────────────────────────────

RECIPES = {
    'stone_axe': {
        'name': 'Stone Axe',
        'inputs': {'flint': 2, 'stick': 1, 'vine': 1},
        'output': ('stone_axe', 1),
        'required_tool': None,
        'time': 3.0,
    },
    'wooden_spear': {
        'name': 'Wooden Spear',
        'inputs': {'stick': 2, 'flint': 1, 'vine': 1},
        'output': ('wooden_spear', 1),
        'required_tool': None,
        'time': 2.0,
    },
    'rope': {
        'name': 'Rope',
        'inputs': {'vine': 3},
        'output': ('rope', 1),
        'required_tool': None,
        'time': 1.0,
    },
    'campfire': {
        'name': 'Campfire',
        'inputs': {'wood_log': 3, 'stick': 2, 'flint': 1},
        'output': ('campfire', 1),
        'required_tool': None,
        'time': 5.0,
    },
    'cooked_meat': {
        'name': 'Cooked Meat',
        'inputs': {'raw_meat': 1},
        'output': ('cooked_meat', 1),
        'required_tool': 'campfire',
        'time': 8.0,
    },
    'stick': {
        'name': 'Sticks (x4)',
        'inputs': {'wood_log': 1},
        'output': ('stick', 4),
        'required_tool': 'stone_axe',
        'time': 1.5,
    },
    'wooden_cup_empty': {
        'name': 'Wooden Cup',
        'inputs': {'wood_log': 1, 'stick': 1},
        'output': ('wooden_cup_empty', 1),
        'required_tool': 'stone_axe',
        'time': 4.0,
    },
    'shelter_frame': {
        'name': 'Shelter Frame',
        'inputs': {'wood_log': 6, 'rope': 4},
        'output': ('shelter_frame', 1),
        'required_tool': None,
        'time': 20.0,
    },
    'arrow': {
        'name': 'Arrows (x5)',
        'inputs': {'stick': 3, 'flint': 2, 'feather': 3},
        'output': ('arrow', 5),
        'required_tool': None,
        'time': 2.0,
    },
    'torch': {
        'name': 'Torch',
        'inputs': {'stick': 1, 'vine': 1},
        'output': ('torch', 1),
        'required_tool': None,
        'time': 1.5,
    },
    'stone_knife': {
        'name': 'Stone Knife',
        'inputs': {'flint': 2, 'stick': 1},
        'output': ('stone_knife', 1),
        'required_tool': None,
        'time': 2.0,
    },
    'bow': {
        'name': 'Wooden Bow',
        'inputs': {'stick': 3, 'vine': 2},
        'output': ('bow', 1),
        'required_tool': None,
        'time': 5.0,
    },
    'leather_armor': {
        'name': 'Leather Armor',
        'inputs': {'hide': 5, 'vine': 3},
        'output': ('leather_armor', 1),
        'required_tool': None,
        'time': 15.0,
    },
    'wooden_cup_empty': {
        'name': 'Wooden Cup',
        'inputs': {'wood_log': 1, 'stick': 1},
        'output': ('wooden_cup_empty', 1),
        'required_tool': 'stone_axe',
        'time': 4.0,
    },
}


# ──────────────────────────────────────────────
#  INVENTORY CLASS
# ──────────────────────────────────────────────

class InventorySlot:
    def __init__(self, item_id=None, count=0, durability=None):
        self.item_id = item_id
        self.count = count
        self.durability = durability

    @property
    def empty(self):
        return self.item_id is None or self.count == 0

    @property
    def data(self):
        return ITEMS.get(self.item_id, {}) if self.item_id else {}

    def __repr__(self):
        return f"Slot({self.item_id} x{self.count})"


class Inventory:
    SLOTS = 24

    def __init__(self, player=None):
        self.player = player
        self.slots = [InventorySlot() for _ in range(self.SLOTS)]
        self.equipped_slot = 0      # currently selected hotbar slot
        self.is_open = False
        self.hotbar_size = 8

    # ── Give starting items ──
    def give_starting_items(self):
        self.add_item('stone_axe',  1, durability=100)
        self.add_item('cooked_meat', 3)
        self.add_item('wooden_cup',  1)
        print("✅ Starting items given.")

    # ── Add item ──
    def add_item(self, item_id, count=1, durability=None):
        data = ITEMS.get(item_id)
        if not data:
            print(f"Unknown item: {item_id}")
            return False

        if data.get('stackable', False):
            # Try to stack into existing slot
            for slot in self.slots:
                if slot.item_id == item_id and slot.count < data['max_stack']:
                    add = min(count, data['max_stack'] - slot.count)
                    slot.count += add
                    count -= add
                    if count <= 0:
                        return True

        # Find empty slot
        if count > 0:
            for slot in self.slots:
                if slot.empty:
                    slot.item_id = item_id
                    slot.count   = min(count, data.get('max_stack', 1))
                    dur = durability if durability else data.get('max_durability')
                    slot.durability = dur
                    count -= slot.count
                    if count <= 0:
                        return True

        print("Inventory full!")
        return False

    # ── Remove item ──
    def remove_item(self, item_id, count=1):
        removed = 0
        for slot in self.slots:
            if slot.item_id == item_id and not slot.empty:
                take = min(count - removed, slot.count)
                slot.count -= take
                removed += take
                if slot.count <= 0:
                    slot.item_id = None
                    slot.count = 0
                    slot.durability = None
                if removed >= count:
                    return True
        return removed > 0

    # ── Count item ──
    def count_item(self, item_id):
        return sum(s.count for s in self.slots if s.item_id == item_id)

    # ── Has items ──
    def has_items(self, requirements: dict):
        return all(self.count_item(k) >= v for k, v in requirements.items())

    # ── Equipped item ──
    @property
    def equipped(self):
        slot = self.slots[self.equipped_slot]
        return slot if not slot.empty else None

    # ── Use equipped item ──
    def use_equipped(self, target=None):
        slot = self.slots[self.equipped_slot]
        if slot.empty:
            return

        item_data = slot.data
        cat = item_data.get('category')

        if cat == 'food':
            nutrition = item_data.get('nutrition', 0)
            hydration = item_data.get('hydration', 0)
            if self.player:
                self.player.eat(nutrition)
                self.player.drink(hydration)
            becomes = item_data.get('becomes')
            self.remove_item(slot.item_id, 1)
            if becomes:
                self.add_item(becomes, 1)
            print(f"Ate {item_data['name']} (+{nutrition} hunger, +{hydration} thirst)")

        elif cat == 'drink':
            hydration = item_data.get('hydration', 0)
            nutrition = item_data.get('nutrition', 0)
            if self.player:
                self.player.drink(hydration)
                if nutrition:
                    self.player.eat(nutrition)
            becomes = item_data.get('becomes')
            self.remove_item(slot.item_id, 1)
            if becomes:
                self.add_item(becomes, 1)
            print(f"Drank {item_data['name']} (+{hydration} thirst)")

        elif cat in ('tool', 'weapon'):
            # Durability loss on use
            if slot.durability is not None:
                slot.durability -= 1
                if slot.durability <= 0:
                    print(f"{item_data['name']} broke!")
                    self.remove_item(slot.item_id, 1)

    # ── Can craft ──
    def can_craft(self, recipe_id):
        recipe = RECIPES.get(recipe_id)
        if not recipe:
            return False
        return self.has_items(recipe['inputs'])

    # ── Craft ──
    def craft(self, recipe_id):
        if not self.can_craft(recipe_id):
            print(f"Cannot craft {recipe_id}: missing materials")
            return False
        recipe = RECIPES[recipe_id]
        for item_id, count in recipe['inputs'].items():
            self.remove_item(item_id, count)
        out_id, out_count = recipe['output']
        self.add_item(out_id, out_count)
        print(f"✅ Crafted: {recipe['name']}")
        return True

    # ── Input ──
    def handle_input(self, key):
        # Hotbar 1-8
        for i in range(self.hotbar_size):
            if key == str(i + 1):
                self.equipped_slot = i
                print(f"Equipped slot {i+1}: {self.slots[i]}")

        # Use item: F
        if key == 'f':
            self.use_equipped()

        # Toggle inventory: Tab
        if key == 'tab':
            self.is_open = not self.is_open

        # Scroll hotbar
        if key == 'scroll up':
            self.equipped_slot = (self.equipped_slot - 1) % self.hotbar_size
        if key == 'scroll down':
            self.equipped_slot = (self.equipped_slot + 1) % self.hotbar_size

    def __repr__(self):
        items = [s for s in self.slots if not s.empty]
        return f"Inventory({len(items)} items)"
