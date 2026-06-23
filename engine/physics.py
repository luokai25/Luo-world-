"""
Physics Engine - Bullet Physics via Panda3D
Handles gravity, collisions, rigid bodies
"""

from ursina import *
from panda3d.bullet import (
    BulletWorld,
    BulletRigidBodyNode,
    BulletCapsuleShape,
    BulletBoxShape,
    BulletPlaneShape,
    BulletSphereShape,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
    BulletHeightfieldShape,
)
from panda3d.core import Vec3, BitMask32, TransformState
import math


GRAVITY = -19.8          # m/s² (strong for good game feel)
GROUND_FRICTION = 0.8
PLAYER_FRICTION = 0.3


class PhysicsEngine:
    def __init__(self):
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, GRAVITY, 0))
        self.bodies = []
        self.debug_mode = False

    def update(self, dt):
        """Step the physics simulation"""
        self.world.doPhysics(dt, 10, 1/180)

    def add_rigid_body(self, node, shape, mass=0.0, position=(0,0,0),
                       friction=0.5, restitution=0.1):
        """Add a rigid body to the physics world"""
        body = BulletRigidBodyNode(node.name if hasattr(node,'name') else 'body')
        body.addShape(shape)
        body.setMass(mass)
        body.setFriction(friction)
        body.setRestitution(restitution)

        np = render.attachNewNode(body)
        np.setPos(*position)
        self.world.attachRigidBody(body)
        self.bodies.append(body)
        return body, np

    def create_ground_plane(self, y=0):
        """Flat infinite ground plane"""
        shape = BulletPlaneShape(Vec3(0, 1, 0), y)
        body = BulletRigidBodyNode('ground_plane')
        body.addShape(shape)
        body.setFriction(GROUND_FRICTION)
        np = render.attachNewNode(body)
        self.world.attachRigidBody(body)
        return body

    def create_capsule_body(self, radius=0.35, height=1.5, mass=75.0,
                             position=(0,0,0), name='capsule'):
        """Capsule body for player character"""
        shape = BulletCapsuleShape(radius, height, 1)  # axis Y=1
        body = BulletRigidBodyNode(name)
        body.addShape(shape)
        body.setMass(mass)
        body.setFriction(PLAYER_FRICTION)
        body.setLinearDamping(0.3)
        body.setAngularDamping(1.0)   # prevent spinning
        body.setAngularFactor(Vec3(0, 0, 0))  # lock rotation axes
        body.setCcdMotionThreshold(0.001)
        body.setCcdSweptSphereRadius(0.3)

        np = render.attachNewNode(body)
        np.setPos(*position)
        self.world.attachRigidBody(body)
        self.bodies.append(body)
        return body, np

    def create_box_body(self, size=(0.5, 0.5, 0.5), mass=1.0,
                         position=(0,0,0), name='box'):
        """Box body for items/props"""
        shape = BulletBoxShape(Vec3(*[s/2 for s in size]))
        body = BulletRigidBodyNode(name)
        body.addShape(shape)
        body.setMass(mass)
        body.setFriction(0.6)
        body.setRestitution(0.1)

        np = render.attachNewNode(body)
        np.setPos(*position)
        self.world.attachRigidBody(body)
        self.bodies.append(body)
        return body, np

    def raycast(self, origin, direction, distance=100.0):
        """Cast a ray and return hit info"""
        from panda3d.core import Point3
        origin_p3 = Point3(*origin)
        end_p3 = Point3(
            origin[0] + direction[0] * distance,
            origin[1] + direction[1] * distance,
            origin[2] + direction[2] * distance
        )
        result = self.world.rayTestClosest(origin_p3, end_p3)
        return result

    def remove_body(self, body):
        """Remove a rigid body from simulation"""
        if body in self.bodies:
            self.world.removeRigidBody(body)
            self.bodies.remove(body)
