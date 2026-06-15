"""Machining feature: mill an obround (circular-end / slot-shaped) pocket.

A circular-end pocket is a rectangle capped by a semicircle at each end -- the
classic shape left by an end mill. ``*_polygon`` cuts it into a prismatic part,
``*_cylinder`` into a cylindrical part.
"""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero
from utils.plane_direction import plane_direction

def circular_end_pocket_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Mill a blind obround pocket into a random stock face of a prismatic part.

    Returns the modified shape.
    """
    #print("circular_end_pocket_polygon")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))

    multiplier_1 = np.random.uniform(5, 10)
    multiplier_2 = np.random.uniform(5, 10)


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

    length_rad_selector = random.choice(['length_first', 'length_second'])
    if length_rad_selector == 'length_first':
        length = first_direction / multiplier_1
        radius = second_direction / multiplier_2
    elif length_rad_selector == 'length_second':
        radius = second_direction / multiplier_2
        length = first_direction / multiplier_1
    else:
        pass


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt()))
    pocket_profile = (wp.moveTo(-length/2, radius)
                      .lineTo(length/2, radius)  
                      .threePointArc((length/2 + radius, 0), (length/2, -radius)) 
                      .lineTo(-length/2, -radius)  
                      .threePointArc((-length/2 -radius, 0), (-length/2, radius))  
                     )

    pocket = pocket_profile.close().extrude(depth/np.random.uniform(4, 10))
    return shape.cut(pocket, clean=True)



def circular_end_pocket_cylinder(shape, seg_dict):
    """Mill a blind obround pocket into a face of a cylindrical part.

    Returns ``(shape, None)``.
    """
    #print("circular_end_pocket_cylinder")
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
        multiplier_1 = np.random.uniform(5, 10)
        multiplier_2 = np.random.uniform(5, 10)
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
            multiplier_1 = random.uniform(3, 8)
            multiplier_2 = random.uniform(3, 8)
            normal = cq.Vector(0, 1, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
            depth = first_direction / np.random.uniform(4, 10)
        elif random_direction == 'second':
            first_direction  = bby
            second_direction = bbz
            direction = cq.Vector(0, 1, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            multiplier_1 = random.uniform(3, 8)
            multiplier_2 = random.uniform(3, 8)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth = first_direction / np.random.uniform(4, 10)


    length_rad_selector = random.choice(['length_first', 'length_second'])
    if length_rad_selector == 'length_first':
        length = first_direction / multiplier_1
        radius = second_direction / multiplier_2
    elif length_rad_selector == 'length_second':
        radius = second_direction / multiplier_2
        length = first_direction / multiplier_1
    else:
        pass


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal))
    pocket_profile = (wp.moveTo(-length/2, radius)
                      .lineTo(length/2, radius)  
                      .threePointArc((length/2 + radius, 0), (length/2, -radius)) 
                      .lineTo(-length/2, -radius)  
                      .threePointArc((-length/2 -radius, 0), (-length/2, radius))  
                     )
    pocket = pocket_profile.close().extrude(depth)
    return shape.cut(pocket, clean=True), None