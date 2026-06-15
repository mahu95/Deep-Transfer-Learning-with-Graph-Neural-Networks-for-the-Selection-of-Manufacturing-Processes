"""Machining feature: drill a through-hole in a prismatic or cylindrical part."""
import cadquery as cq
import random
import numpy as np

from utils.plane_direction import plane_direction
from utils.round_near_zero import round_near_zero

def through_hole_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Cut a circular through-hole in a random stock face of a prismatic part.

    The cut depth uses the relevant bounding dimension so the hole passes fully
    through. Returns the modified shape.
    """
    #print("through_hole_polygon")
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
        diameter = np.random.uniform(0.01*highest_possible_diameter, 0.25*highest_possible_diameter)
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
        diameter = np.random.uniform(0.01*highest_possible_diameter, 0.25*highest_possible_diameter)
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
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.25*highest_possible_diameter)
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
    
    if diameter > 20:
        diameter = np.random.uniform(5,20)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).circle(diameter/2).extrude(depth)
    return shape.cut(wp, clean=True)








def through_hole_cylinder(shape, seg_dict):
    """Cut a radial or axial through-hole in a cylindrical part.

    Depending on the chosen face the hole runs along the axis or across the
    diameter. Returns ``(shape, None)``.
    """
    #print("through_hole_cylinder")
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
        solid = shape.val() 
        bb = solid.BoundingBox()
        depth = round_near_zero(abs(bb.zmax-bb.zmin))
        first_direction  = bbx
        second_direction = bby
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y, selected_face.Center().z)
        normal = selected_face.normalAt()
        direction = (1,0,0)
        diameter = second_direction / np.random.uniform(8, 16)
    else:
        random_direction = random.choice(['first', 'second'])
        if random_direction == 'first':
            first_direction  = bbx
            second_direction = bbz
            direction = cq.Vector(1, 0, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            normal = cq.Vector(0, 1, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
            depth = first_direction 
            diameter = second_direction / np.random.uniform(4, 10)
        elif random_direction == 'second':
            first_direction  = bby
            second_direction = bbz
            direction = cq.Vector(0, 1, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth  = first_direction 
            diameter = second_direction / np.random.uniform(4, 10)

    if diameter > 20:
        diameter = np.random.uniform(5,20)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal)).circle(diameter/2).extrude(depth)
    return shape.cut(wp, clean=True), None