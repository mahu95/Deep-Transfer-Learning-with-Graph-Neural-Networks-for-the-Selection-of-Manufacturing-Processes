"""Machining feature: drill/mill blind holes (flat- and conical-bottomed).

A blind hole stops part-way into the material. The ``*_milled`` variants leave a
flat bottom (end-mill), while the ``*_drilled`` variants leave the conical tip a
twist drill produces. Each has a ``*_polygon`` (prismatic) and ``*_cylinder``
(rotational) form.
"""
import cadquery as cq
import random
import numpy as np

from utils.plane_direction import plane_direction
from utils.round_near_zero import round_near_zero

def blind_hole_polygon_milled(shape, x_length, y_length, z_length, seg_dict):
    """Mill a flat-bottomed blind hole into a random prismatic stock face.

    Returns the modified shape.
    """
    #print("blind_hole_polygon_milled")
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
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bby -  diameter )/2
        second_direction = (bbz - diameter )/2
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = (0,1,0)
    elif bby == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bbz)
        depth = y_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/2
        second_direction = (bbz - diameter )/2
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = (1,0,0)
    elif bbz == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bby)
        depth = z_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/2
        second_direction = (bby - diameter)/2
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

    if diameter < depth:
        depth = diameter / np.random.uniform(1,4)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).circle(diameter/2).extrude(depth*np.random.uniform(0.1, 0.8))
    return shape.cut(wp, clean=True)






def blind_hole_cylinder_milled(shape, seg_dict):
    """Mill a flat-bottomed blind hole into a face of a cylindrical part.

    Returns ``(shape, None)``.
    """
    #print("blind_hole_cylinder_milled")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    boolean = True
    while boolean:
        selected_face = random.choice(faces)
        bb = selected_face.BoundingBox()
        bbx = round_near_zero(abs(bb.xmax-bb.xmin))
        bby = round_near_zero(abs(bb.ymax-bb.ymin))
        bbz = round_near_zero(abs(bb.zmax-bb.zmin))
        if bbz != 0:
            boolean = False


    if bbz == 0.0:
        solid = shape.val() 
        bb = solid.BoundingBox()
        depth = abs(bb.zmax-bb.zmin) * np.random.uniform(0.1, 0.8)
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/6, first_direction/6)
        random_second_direction = np.random.uniform(-1*second_direction/6, second_direction/6)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        normal = selected_face.normalAt()
        direction = (1,0,0)
        diameter = second_direction / np.random.uniform(4, 20)
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
            depth = first_direction * np.random.uniform(0.1, 0.8)
            diameter = second_direction / np.random.uniform(4, 20)
        elif random_direction == 'second':
            first_direction  = bby
            second_direction = bbz
            direction = cq.Vector(0, 1, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth  = first_direction * np.random.uniform(0.1, 0.8)
            diameter = second_direction / np.random.uniform(4, 20)

    if diameter > 20:
        diameter = np.random.uniform(5,20)

    if diameter < depth:
        depth = diameter / np.random.uniform(1,2)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal)).circle(diameter/2).extrude(depth)
    return shape.cut(wp, clean=True), None






def blind_hole_polygon_drilled(shape, x_length, y_length, z_length, seg_dict):
    """Drill a conical-bottomed blind hole into a random prismatic stock face.

    Returns the modified shape.
    """
    #print("blind_hole_polygon_drilled")
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
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bby -  diameter )/2
        second_direction = (bbz - diameter )/2
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bbz)
        depth = y_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/2
        second_direction = (bbz - diameter )/2
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bby)
        depth = z_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.5*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/2
        second_direction = (bby - diameter)/2
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = cq.Vector(1,0,0)
    else:
        origin = selected_face.Center()
        diameter = np.random.uniform(5, 20)
        depth   = np.random.uniform(0.5, 1)
        direction = plane_direction(selected_face.normalAt())
    
    if diameter > 20:
        diameter = np.random.uniform(5,20)

    if diameter > depth:
        diameter = depth / np.random.uniform(1,2)

    normal = -1*selected_face.normalAt()
    depth = depth*np.random.uniform(0.1, 0.6)
    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=normal)).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    triangle = cq.Workplane(cq.Plane(origin=origin+depth*normal, xDir=direction, normal=direction.cross(normal))).lineTo(diameter/2, 0).lineTo(0, (diameter/2)*(np.sqrt(3)/3)).lineTo(0,0).close()
    cone = triangle.revolve(angleDegrees=360, axisStart=(0, 0), axisEnd=(0,1))

    return shape.cut(cone, clean=True)






def blind_hole_cylinder_drilled(shape, seg_dict):
    """Drill a conical-bottomed blind hole into a face of a cylindrical part.

    Returns ``(shape, None)``.
    """
    #print("blind_hole_cylinder_drilled")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    boolean = True
    while boolean:
        selected_face = random.choice(faces)
        bb = selected_face.BoundingBox()
        bbx = round_near_zero(abs(bb.xmax-bb.xmin))
        bby = round_near_zero(abs(bb.ymax-bb.ymin))
        bbz = round_near_zero(abs(bb.zmax-bb.zmin))
        if bbz != 0:
            boolean = False


    if bbz == 0.0:
        solid = shape.val() 
        bb = solid.BoundingBox()
        depth = abs(bb.zmax-bb.zmin) / np.random.uniform(2,5)
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/6, first_direction/6)
        random_second_direction = np.random.uniform(-1*second_direction/6, second_direction/6)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        normal = selected_face.normalAt()
        direction = (1,0,0)
        diameter = second_direction / np.random.uniform(4, 8)
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
            depth = first_direction / np.random.uniform(2,5)
            diameter = second_direction / np.random.uniform(4, 8)
        elif random_direction == 'second':
            first_direction  = bby
            second_direction = bbz
            direction = cq.Vector(0, 1, 0)
            surface_direction = random.choice([-1, 1])
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth  = first_direction / np.random.uniform(2,5)
            diameter = second_direction / np.random.uniform(4, 8)

    if diameter > 20:
        diameter = np.random.uniform(5,20)

    if diameter > depth:
        diameter = depth / np.random.uniform(1,2)

    normal = -normal
    depth = depth*np.random.uniform(0.1, 0.6)
    x = 20
    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=normal)).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    triangle = cq.Workplane(cq.Plane(origin=origin+depth*normal, xDir=direction, normal=direction.cross(normal))).lineTo(diameter/2, 0).lineTo(0, (diameter/2)*(np.sqrt(3)/3)).lineTo(0,0).close()
    cone = triangle.revolve(angleDegrees=360, axisStart=(0, 0), axisEnd=(0,1))
    wp3 = cq.Workplane(cq.Plane(origin=cq.Vector(0,0,0)+x/2*cq.Vector(1,0,0), xDir=cq.Vector(1,0,0), normal=cq.Vector(0,0,1))).box(x, 100, 100)
    shape = shape.cut(cone, clean=True)

    return shape, None