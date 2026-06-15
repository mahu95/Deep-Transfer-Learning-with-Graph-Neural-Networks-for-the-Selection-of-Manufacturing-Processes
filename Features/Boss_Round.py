"""Machining feature: add a raised cylindrical (round) boss to a prismatic part."""
import cadquery as cq
import random
import numpy as np

from utils.plane_direction import plane_direction
from utils.round_near_zero import round_near_zero

def round_boss(shape, x_length, y_length, z_length, seg_dict):
    """Union a small raised cylinder onto a random stock face of a prismatic part.

    The boss diameter is kept well within the host face's extents. Returns
    ``(shape, [selected_face])``.
    """
    #print("round_boss_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))
    diameter_list = []

    if bbx == 0.0:
        diameter_list.append(bby)
        diameter_list.append(bbz)
        depth = x_length 
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.1*highest_possible_diameter, 0.2*highest_possible_diameter)
        first_direction  = (bby -  diameter )/3
        second_direction = (bbz - diameter )/3
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = (0,1,0)
    elif bby == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bbz)
        depth = y_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.1*highest_possible_diameter, 0.2*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/3
        second_direction = (bbz - diameter )/3
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = (1,0,0)
    elif bbz == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bby)
        depth = z_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.1*highest_possible_diameter, 0.2*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/3
        second_direction = (bby - diameter)/3
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = (1,0,0)
    else:
        origin = selected_face.Center()
        diameter = np.random.uniform(0.1, 0.5)
        depth   = np.random.uniform(0.1, 0.9)
        direction = plane_direction(selected_face.normalAt())

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=selected_face.normalAt())).circle(diameter).extrude(depth/np.random.uniform(10, 20))
    #print(selected_face.Center(), origin, direction, -1*selected_face.normalAt())
    return shape.union(wp, clean=True), [selected_face]