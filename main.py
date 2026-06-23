#!/usr/bin/env python3
"""
LUO WORLD - Main Entry Point
A photorealistic 3D survival crafting game
3rd person perspective
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from game.world import World
from game.player import Player
from game.inventory import Inventory
from game.hud import HUD
from engine.physics import PhysicsEngine
from engine.lighting import LightingSystem

def main():
    app = Ursina(
        title='Luo World',
        icon=None,
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        vsync=True,
    )

    # Window settings
    window.title = 'Luo World'
    window.borderless = False
    window.fullscreen = False
    window.exit_button.visible = False
    window.fps_counter.enabled = True

    # Init core systems
    physics = PhysicsEngine()
    lighting = LightingSystem()

    # Build the world
    world = World(physics=physics)

    # Spawn player at origin
    player = Player(world=world, position=(0, 2, 0))

    # Init inventory with starting items
    inventory = Inventory(player=player)
    inventory.give_starting_items()

    # HUD
    hud = HUD(player=player, inventory=inventory)

    # Camera setup - 3rd person
    camera.fov = 75

    def update():
        player.update()
        world.update()
        hud.update()
        physics.update(time.dt)

    def input(key):
        player.handle_input(key)
        inventory.handle_input(key)
        hud.handle_input(key)

        if key == 'escape':
            application.quit()

    app.run()

if __name__ == '__main__':
    main()
