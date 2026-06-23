# 🌿 Luo World

A photorealistic 3D open-world survival crafting game.

**Style:** Sons of the Forest / photorealistic jungle
**Perspective:** 3rd person
**Engine:** Panda3D + Ursina (Python)
**Physics:** Bullet Physics (built into Panda3D)

---

## 🎮 Gameplay

You spawn in a dense jungle with only 3 items:
- 🪓 A hand-crafted stone axe (flint head + stick handle + vine binding)
- 🥩 3 pieces of cooked cow meat
- 🥤 A wooden cup of water

**Goal:** Survive. Explore. Craft. Discover.

There is **no set ending** — the world is yours to shape through crafting, building, and exploration.

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Move |
| Shift | Run |
| Space | Jump |
| Mouse | Look / Camera orbit |
| Left Click | Attack / Chop / Mine |
| F | Use / Eat / Drink equipped item |
| 1-8 | Select hotbar slot |
| Scroll | Cycle hotbar |
| Tab | Open inventory |
| E | Interact with object |
| Escape | Quit |

---

## 🛠️ Crafting (Session 3+)

Recipes discovered through experimentation:

| Output | Inputs | Tool Needed |
|--------|--------|-------------|
| Stone Axe | 2x Flint + 1x Stick + 1x Vine | None |
| Wooden Spear | 2x Stick + 1x Flint + 1x Vine | None |
| Rope | 3x Vine | None |
| Campfire | 3x Log + 2x Stick + 1x Flint | None |
| Cooked Meat | 1x Raw Meat | Campfire |
| Sticks (x4) | 1x Wood Log | Stone Axe |
| Shelter Frame | 6x Log + 4x Rope | None |

*More recipes unlock as you explore...*

---

## ⚙️ Install & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Generate 3D assets (run once)
python generate_assets.py

# Launch game
python main.py
```

---

## 📁 Project Structure

```
luo-world/
├── main.py                  # Entry point
├── generate_assets.py       # Asset generator (run once)
├── requirements.txt
├── game/
│   ├── player.py            # 3rd person player controller
│   ├── world.py             # Procedural jungle world
│   ├── inventory.py         # Items, crafting, inventory
│   └── hud.py               # HUD: bars, hotbar, crosshair
├── engine/
│   ├── physics.py           # Bullet physics wrapper
│   ├── lighting.py          # Dynamic sun/day-night cycle
│   └── model_gen.py         # Procedural 3D asset generator
├── assets/
│   ├── models/              # Generated .glb files
│   ├── textures/            # PBR textures
│   └── sounds/              # (Session 4+)
├── ui/                      # (Session 3+) Crafting UI
└── data/                    # Save data, config
```

---

## 🗺️ Development Roadmap

- [x] **Session 1** — Engine, world, player, inventory, HUD, 3D assets
- [ ] **Session 2** — Physics collisions, tree chopping, resource pickup, item drops
- [ ] **Session 3** — Full crafting UI, Supabase save system, recipe discovery
- [ ] **Session 4** — Animals, hunting, cooking system, campfire
- [ ] **Session 5** — Shelter building, weather system, day/night survival
- [ ] **Session 6+** — More biomes, caves, water sources, advanced crafting

---

*Built session by session. This project never stops.*
