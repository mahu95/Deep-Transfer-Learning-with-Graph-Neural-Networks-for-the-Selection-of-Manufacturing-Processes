"""Machining feature: drill countersink and counterbore holes.

A *countersink* widens a hole's mouth with a cone (for flat-head screws); a
*counterbore* widens it with a cylindrical recess (for socket-head screws).
Each comes in a ``*_polygon`` variant (prismatic stock) and a ``*_cylinder``
variant (cylindrical stock).
"""
import cadquery as cq
import random
import numpy as np

from utils.plane_direction import plane_direction
from utils.round_near_zero import round_near_zero

def countersink_hole_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Drill a hole with a conical countersink into a random prismatic stock face.

    Returns the modified shape.
    """
    #print("countersink_hole_polygon")
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
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.25*highest_possible_diameter)
        first_direction  = (bby -  diameter )/3
        second_direction = (bbz - diameter )/3
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        diameter_list.append(bbx)
        diameter_list.append(bbz)
        depth = y_length
        highest_possible_diameter = min(diameter_list)
        diameter = np.random.uniform(0.05*highest_possible_diameter, 0.25*highest_possible_diameter)
        first_direction  = (bbx -  diameter)/3
        second_direction = (bbz - diameter )/3
        random_first_direction = np.random.uniform(-1*first_direction, first_direction)
        random_second_direction = np.random.uniform(-1*second_direction, second_direction)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
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
        direction = cq.Vector(1,0,0)
    else:
        origin = selected_face.Center()
        diameter = np.random.uniform(0.1, 0.5)
        depth   = np.random.uniform(0.1, 0.9)
        direction = plane_direction(selected_face.normalAt())
    
    if diameter > 20:
        diameter = np.random.uniform(5,20)

    depth_countersink = np.random.uniform(depth/6, depth/3)
    diameter_countersink = np.random.uniform(1.2*diameter, 1.8*diameter)
    normal = selected_face.normalAt()


    if normal.x == 1: #done
        path = cq.Workplane(inPlane='XY', origin=origin).lineTo(0, diameter_countersink/2).lineTo(-depth_countersink, 0).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=normal)
        shape = shape.cut(cone)
    elif normal.y == 1: #done
        path = cq.Workplane(inPlane='XY', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, -depth_countersink).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=normal)
        shape = shape.cut(cone)
    elif normal.z == 1:
        path = cq.Workplane(inPlane='XZ', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, -depth_countersink).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
        shape = shape.cut(cone)
    elif normal.x == -1: #done
        path = cq.Workplane(inPlane='XY', origin=origin).lineTo(0, diameter_countersink/2).lineTo(depth_countersink, 0).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=normal)
        shape = shape.cut(cone)
    elif normal.y == -1: #done
        path = cq.Workplane(inPlane='XY', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, depth_countersink).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=normal)
        shape = shape.cut(cone)
    elif normal.z == -1:
        path = cq.Workplane(inPlane='XZ', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, depth_countersink).lineTo(0, 0).wire()
        cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
        shape = shape.cut(cone)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    return shape
    


def counterbore_hole_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Drill a hole with a cylindrical counterbore into a prismatic stock face.

    Returns the modified shape.
    """
    #print("counterbore_hole_polygon")
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

    depth_counterbore = np.random.uniform(depth/8, depth/4)
    diameter_counterbore = np.random.uniform(1.2*diameter, 2*diameter)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    wp = cq.Workplane(cq.Plane(origin=origin+depth_counterbore/2*-1*selected_face.normalAt(), xDir=direction, normal=-1*selected_face.normalAt())).cylinder(depth_counterbore, diameter_counterbore/2)
    return shape.cut(wp, clean=True)





def countersink_hole_cylinder(shape, seg_dict):
    """Drill a countersunk hole into a face of a cylindrical part.

    Returns ``(shape, None)``.
    """
    #print("countersink_hole_cylinder")
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
    surface_direction = random.choice([-1, 1])

    if bbz == 0.0:
        solid = shape.val() 
        bb = solid.BoundingBox()
        depth = round_near_zero(abs(bb.zmax-bb.zmin))
        first_direction  = bbx
        second_direction = bby
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y, selected_face.Center().z)
        normal = selected_face.normalAt()
        direction = cq.Vector(1,0,0)
        diameter = second_direction / np.random.uniform(8, 16)
    else:
        if random_direction == 'first':
            first_direction  = bbx
            second_direction = bbz
            direction = cq.Vector(1, 0, 0)
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
            random_first_direction = first_direction/2 * surface_direction
            random_second_direction = np.random.uniform(-1*second_direction/4, second_direction/4)
            normal = cq.Vector(1, 0, 0) * surface_direction
            origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
            depth  = first_direction 
            diameter = second_direction / np.random.uniform(4, 10)

    if diameter > 20:
        diameter = np.random.uniform(5,20)

    depth_countersink = np.random.uniform(depth/6, depth/3)
    diameter_countersink = np.random.uniform(1.2*diameter, 1.8*diameter)

    if bbz == 0:
        if selected_face.normalAt().z == 1:
            path = cq.Workplane(inPlane='XZ', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, -depth_countersink).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
            shape = shape.cut(cone)
        else:
            path = cq.Workplane(inPlane='XZ', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, depth_countersink).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
            shape = shape.cut(cone)
    else:
        if random_direction == 'first' and surface_direction == -1: 
            path = cq.Workplane(inPlane='XY', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, depth_countersink).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
            shape = shape.cut(cone)
        elif random_direction == 'first' and surface_direction == 1: 
            path = cq.Workplane(inPlane='XY', origin=origin).lineTo(diameter_countersink/2, 0).lineTo(0, -depth_countersink).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
            shape = shape.cut(cone)
        elif  random_direction == 'second' and surface_direction == 1: 
            path = cq.Workplane(inPlane='XY', origin=origin).lineTo(0, diameter_countersink/2).lineTo(-depth_countersink, 0).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(1,0,0))
            shape = shape.cut(cone)
        elif  random_direction == 'second' and surface_direction == -1: 
            path = cq.Workplane(inPlane='XY', origin=origin).lineTo(0, diameter_countersink/2).lineTo(depth_countersink, 0).lineTo(0, 0).wire()
            cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(1,0,0))
            shape = shape.cut(cone)
        
    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal)).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    return shape, None





def counterbore_hole_cylinder(shape, seg_dict):
    """Drill a counterbored hole into a face of a cylindrical part.

    Returns ``(shape, None)``.
    """
    #print("countersink_hole_cylinder")
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

    depth_counterbore = np.random.uniform(depth/8, depth/4)
    diameter_counterbore = np.random.uniform(1.2*diameter, 2*diameter)

    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-normal)).circle(diameter/2).extrude(depth)
    shape = shape.cut(wp, clean=True)
    wp = cq.Workplane(cq.Plane(origin=origin+depth_counterbore/2*-normal, xDir=direction, normal=-normal)).cylinder(depth_counterbore, diameter_counterbore/2)
    return shape.cut(wp, clean=True), None