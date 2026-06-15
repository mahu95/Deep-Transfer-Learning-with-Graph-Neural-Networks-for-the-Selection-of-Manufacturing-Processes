"""Machining feature: add a raised cuboid boss to a prismatic or cylinder part.

``*_polygon`` variants act on a face of a prismatic (cuboid) stock chosen from
the still-unmachined (label 0) faces; ``*_cylinder`` variants act on a flat end
face of a cylindrical stock.
"""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero
from utils.plane_direction import plane_direction

def cuboid_boss_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Union a small raised cuboid onto a random stock face of a prismatic part.

    Returns ``(shape, [selected_face])`` so the caller can track the host face.
    """
    #print("cuboid_boss_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))


    multiplier_1 = np.random.uniform(2, 5)
    multiplier_2 = np.random.uniform(2, 5)


    if bbx == 0.0:
        depth = x_length 
        first_direction  = bby
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/10, first_direction/10)
        random_second_direction = np.random.uniform(-1*second_direction/10, second_direction/10)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        depth = y_length
        first_direction  = bbx
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/10, first_direction/10)
        random_second_direction = np.random.uniform(-1*second_direction/10, second_direction/10)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        depth = z_length
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/10, first_direction/10)
        random_second_direction = np.random.uniform(-1*second_direction/10, second_direction/10)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = (1,0,0)
    else:
        origin = selected_face.Center()
        direction = plane_direction(selected_face.normalAt())


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=selected_face.normalAt())).rect(first_direction/multiplier_1, second_direction/multiplier_2).extrude(depth/np.random.uniform(10, 20))
    #print(selected_face.Center(), origin, direction, -1*selected_face.normalAt())
    return shape.union(wp, clean=False), [selected_face]


def cuboid_boss_cylinder(shape):
    """Union a cuboid boss onto a random end face of a cylindrical stock.

    Returns ``(shape, selected_face_selector)`` where the selector (``>Z``/``<Z``)
    records which end the boss was placed on.
    """
    #print("cuboid_boss_cylinder")
    face_selectors = [">Z", "<Z"]
    selected_face_selector = random.choice(face_selectors)
    selected_face = shape.faces(selected_face_selector).val()
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))


    radius = np.sqrt(np.square(bbx)/4)
    length = radius * np.random.uniform(3, 6)
    width  = radius * np.random.uniform(3, 6)
    heigth = radius * np.random.uniform(3, 6)
    normal = selected_face.normalAt()
    origin = selected_face.Center() + (heigth/2)*normal
    wp= cq.Workplane(cq.Plane(origin=origin, xDir=cq.Vector(1,0,0), normal=normal)).box(length=length, width=width, height=heigth)

    shape = shape.union(wp, clean = True)

    return shape, selected_face_selector
