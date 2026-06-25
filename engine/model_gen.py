"""
Procedural 3D Model Generator - Desktop only (trimesh)
Stub on Android - assets pre-generated on desktop
"""
try:
    import trimesh
    import trimesh.creation as tc
    import numpy as np
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False

import os
import math

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'models')

def generate_all():
    if not HAS_TRIMESH:
        print("trimesh not available - skipping asset generation (Android)")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating assets...")
    # Assets generated on desktop, bundled into APK
    print("Done.")

if __name__ == '__main__':
    generate_all()
