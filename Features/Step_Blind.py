"""Machining feature: cut a blind (non-through) step into a prismatic part."""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero

def blind_step_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Cut a shallow corner step into a random stock face of a prismatic part.

    Like the through-step but with a limited depth so it does not break through
    the opposite side. Returns the modified shape.
    """
    #print("blind_step_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))

    multiplier_1 = random.uniform(0.01,0.8)
    multiplier_2 = random.uniform(0.01,0.8)

    if bbx == 0.0:
        depth = x_length 
        first_direction  = bby
        second_direction = bbz
        random_first_direction = first_direction/2 * random.choice([-1, 1])
        random_second_direction = second_direction/2 * random.choice([-1, 1])
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        depth = y_length
        first_direction  = bbx
        second_direction = bbz
        random_first_direction = first_direction/2 * random.choice([-1, 1])
        random_second_direction = second_direction/2 * random.choice([-1, 1])
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        depth = z_length
        first_direction  = bbx
        second_direction = bby
        random_first_direction = first_direction/2 * random.choice([-1, 1])
        random_second_direction = second_direction/2 * random.choice([-1, 1])
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = (1,0,0)
    else:
        random_first_direction = 0.0
        random_second_direction = 0.0
        first_direction = 0.0
        second_direction = 0.0


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).rect(multiplier_1*first_direction, multiplier_2*second_direction).extrude(depth/np.random.uniform(1.5, 10))
    return shape.cut(wp, clean=False)