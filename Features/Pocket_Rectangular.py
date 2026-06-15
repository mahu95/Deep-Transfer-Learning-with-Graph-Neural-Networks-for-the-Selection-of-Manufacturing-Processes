"""Machining feature: mill a rectangular pocket into a prismatic or cylinder part."""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero
from utils.plane_direction import plane_direction

def rectangular_pocket_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Mill a blind rectangular pocket into a random stock face of a prismatic part.

    The pocket is centred (with small random offset) on the face and cut to a
    fraction of the part depth. Returns the modified shape.
    """
    #print("rectangular_pocket_polygon")
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


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).rect(first_direction/multiplier_1, second_direction/multiplier_2).extrude(depth/np.random.uniform(4,10))
    return shape.cut(wp, clean=False)







def rectangular_pocket_cylinder(shape, seg_dict):
    """Mill a blind rectangular pocket into a face of a cylindrical part.

    Handles both flat end faces and the curved barrel (where the pocket is cut
    radially). Returns ``(shape, None)``.
    """
    #print("rectangular_pocket_cylinder")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)

    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))


    if bbz == 0.0:
        depth = np.random.uniform(1, 3) 
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/4, first_direction/4)
        random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
        multiplier_1 = np.random.uniform(2, 5)
        multiplier_2 = np.random.uniform(2, 5)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        normal = selected_face.normalAt()
        direction = (1,0,0)
    else:
        random_direction = random.choice(['first', 'second'])
        if random_direction == 'first':
            first_direction  = bbx
            second_direction = bbz
            direction = cq.Vector(1, 0, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            multiplier_1 = random.uniform(2, 4)
            multiplier_2 = random.uniform(3, 4)
            normal = cq.Vector(0, 1, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
            depth = first_direction / np.random.uniform(2, 4)
        elif random_direction == 'second':
            first_direction  = bby
            second_direction = bbz
            direction = cq.Vector(0, 1, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            multiplier_1 = random.uniform(2, 4)
            multiplier_2 = random.uniform(3, 4)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth = first_direction / np.random.uniform(2, 4)



    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal)).rect(first_direction/multiplier_1, second_direction/multiplier_2).extrude(depth/np.random.uniform(4,10))
    return shape.cut(wp, clean=False), None