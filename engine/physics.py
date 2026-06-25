"""
Physics Engine - Desktop only (Panda3D Bullet)
On Android this module is imported but does nothing
"""
import os
PLATFORM = 'android' if os.path.exists('/android_storage') else 'desktop'

try:
    from panda3d.bullet import (
        BulletWorld, BulletRigidBodyNode, BulletCapsuleShape,
        BulletBoxShape, BulletPlaneShape, BulletSphereShape,
    )
    from panda3d.core import Vec3
    HAS_PANDA = True
except ImportError:
    HAS_PANDA = False

class PhysicsEngine:
    def __init__(self):
        if not HAS_PANDA:
            self.world = None
            self.bodies = []
            return
        from panda3d.bullet import BulletWorld
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, -19.8, 0))
        self.bodies = []

    def update(self, dt):
        if self.world:
            self.world.doPhysics(dt, 10, 1/180)

    def create_ground_plane(self, y=0):
        if not HAS_PANDA: return None
        from panda3d.bullet import BulletPlaneShape, BulletRigidBodyNode
        from panda3d.core import Vec3
        shape = BulletPlaneShape(Vec3(0,1,0), y)
        body  = BulletRigidBodyNode('ground')
        body.addShape(shape)
        self.world.attachRigidBody(body)
        return body

    def create_capsule_body(self, radius=0.35, height=1.5, mass=75.0,
                             position=(0,0,0), name='capsule'):
        if not HAS_PANDA: return None, None
        return None, None

    def create_box_body(self, size=(0.5,0.5,0.5), mass=1.0,
                         position=(0,0,0), name='box'):
        if not HAS_PANDA: return None, None
        return None, None

    def remove_body(self, body):
        pass
