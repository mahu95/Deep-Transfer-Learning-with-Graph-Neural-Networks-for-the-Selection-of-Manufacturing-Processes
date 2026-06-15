"""Machining feature: cut a rectangular through-passage in a prismatic part."""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero
from utils.plane_direction import plane_direction

def rectangular_passage(shape, x_length, y_length, z_length, seg_dict):
    """Cut a rectangular passage straight through a randomly chosen stock face.

    ``x_length``/``y_length``/``z_length`` are the part's bounding dimensions,
    used as the cut depth so the passage goes all the way through. Returns the
    modified shape.
    """
    #print("rectangular_passage_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))

    multiplier_1 = np.random.uniform(3, 10)
    multiplier_2 = np.random.uniform(3, 10)

    if bbx == 0.0:
        depth = x_length 
        first_direction  = bby
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
        random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        depth = y_length
        first_direction  = bbx
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
        random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        depth = z_length
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
        random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = cq.Vector(1,0,0)
    else:
        origin = selected_face.Center()
        direction = plane_direction(selected_face.normalAt())


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).rect(first_direction/multiplier_1, second_direction/multiplier_2).extrude(depth)
    return shape.cut(wp, clean=False)