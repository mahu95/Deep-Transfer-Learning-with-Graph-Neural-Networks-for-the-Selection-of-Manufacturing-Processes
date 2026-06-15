"""Machining feature: cut a through-step (corner step) in a prismatic part, or
turn a stepped diameter onto a cylinder."""
import cadquery as cq
import random
import numpy as np
from utils.round_near_zero import round_near_zero
from utils.plane_direction import plane_direction

def through_step_polygon(shape, x_length, y_length, z_length, seg_dict):
    """Cut a step (open rectangular notch along an edge) into a stock face.

    The notch spans the full extent in one face direction and half in the other,
    forming a step at the part corner. Returns the modified shape.
    """
    #print("through_step_polygon")
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
        multiplier_2 = 1
    elif random_direction == 'second':
        multiplier_1 = 1
        multiplier_2 = 2

    if bbx == 0.0:
        depth = x_length 
        first_direction  = bby
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
        random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x, selected_face.Center().y+random_first_direction, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(0,1,0)
    elif bby == 0.0:
        depth = y_length
        first_direction  = bbx
        second_direction = bbz
        random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
        random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y, selected_face.Center().z+random_second_direction)
        direction = cq.Vector(1,0,0)
    elif bbz == 0.0:
        depth = z_length
        first_direction  = bbx
        second_direction = bby
        random_first_direction = np.random.uniform(-1*first_direction/2, first_direction/2)
        random_second_direction = np.random.uniform(-1*second_direction/2, second_direction/2)
        origin = cq.Vector(selected_face.Center().x+random_first_direction, selected_face.Center().y+random_second_direction, selected_face.Center().z)
        direction = (1,0,0)
    else:
        origin = selected_face.Center()
        direction = plane_direction(selected_face.normalAt())


    wp = cq.Workplane(cq.Plane(origin=origin, xDir=direction, normal=-1*selected_face.normalAt())).rect(multiplier_1*first_direction, multiplier_2*second_direction).extrude(depth/np.random.uniform(1.5, 10))
    return shape.cut(wp, clean=False)









def through_step_cylinder(shape, face_selector=None):
    """Turn a reduced-diameter step onto one end of a cylindrical part.

    Selects a top/bottom face (avoiding ``face_selector`` if given) and unions a
    smaller-radius cylinder, creating a shoulder. Returns ``(shape, [selected_face])``.
    """
    #print("through_step_cylinder")
    face_selectors = [">Z", "<Z"]
    if face_selector:
        if face_selector in face_selectors:
            face_selectors.remove(face_selector)
    selected_face_selector = random.choice(face_selectors)
    selected_face = shape.faces(selected_face_selector).val()
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))

    radius = np.sqrt(np.square(bbx)/4)
    step_radius = np.random.uniform(radius/2, radius/1.1)
    step_heigt  = np.random.uniform(3,10)
    normal = selected_face.normalAt()
    origin1 = selected_face.Center()+(step_heigt/2)*normal
    wp1 = cq.Workplane(cq.Plane(origin=origin1, xDir=cq.Vector(1,0,0), normal=normal)).cylinder(height=step_heigt, radius=step_radius)

    return shape.union(wp1), [selected_face]