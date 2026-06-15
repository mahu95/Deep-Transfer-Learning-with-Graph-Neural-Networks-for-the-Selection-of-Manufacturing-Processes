"""Machining feature: cut a through-slot across a prismatic part face."""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero

def through_slot_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Cut an elongated rectangular slot across a random stock face.

    A random in-plane orientation (``first``/``second``) decides which face
    direction the slot runs along. Returns the modified shape.
    """
    #print("through_slot_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))

    random_direction = random.choice(['first', 'second'])
    if random_direction == 'first':
        multiplier_1 = 2
        multiplier_2 = random.uniform(0.1,0.5)
    elif random_direction == 'second':
        multiplier_1 = random.uniform(0.1,0.5)
        multiplier_2 = 2

    if bbx == 0.0:
        depth = x_length 
        first_direction  = bby
        second_direction = bbz
        if random_direction == 'first':
            random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        elif random_direction == 'second':
            random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
            random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        depth = y_length
        first_direction  = bbx
        second_direction = bbz
        if random_direction == 'first':
            random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        elif random_direction == 'second':
            random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
            random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        depth = z_length
        first_direction  = bbx
        second_direction = bby
        if random_direction == 'first':
            random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        elif random_direction == 'second':
            random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
            random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = (1,0,0)
    else:
        first_direction = 0.0
        second_direction = 0.0

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).rect(multiplier_1*first_direction, multiplier_2*second_direction).extrude(depth/np.random.uniform(1.5, 10))
    return shape.cut(wp, clean=False)







