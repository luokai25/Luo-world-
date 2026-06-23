#!/usr/bin/env python3
"""
Run this ONCE before starting the game.
Generates all 3D assets (trees, rocks, items, terrain chunks).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from engine.model_gen import generate_all
generate_all()
print("\n🎮 Assets ready. Run: python main.py")
