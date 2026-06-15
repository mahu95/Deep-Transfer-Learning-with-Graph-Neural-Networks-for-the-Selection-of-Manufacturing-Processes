"""Machining feature: turn a circumferential groove into a cylinder end."""
import cadquery as cq
import random
import numpy as np

from utils.round_near_zero import round_near_zero

def groove(shape, face_selector=None):
    """Add a reduced-diameter groove section to one end of a cylinder.

    Selects a top/bottom cylinder face (avoiding ``face_selector`` if given),
    unions a thin small-radius disc followed by a full-radius section to form a
    groove. Returns ``(shape, [selected_face])``.
    """
    #print("groove_cylinder")
    face_selectors = [">Z", "<Z"]
    if face_selector:
        if face_selector in face_selectors:
            face_selectors.remove(face_selector)
    selected_face_selector = random.choice(face_selectors)
    selected_face = shape.faces(selected_face_selector).val()
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))

    radius = np.sqrt(np.square(bbx)/4)
    groove_radius = np.random.uniform(radius/2, radius/1.1)
    groove_heigt  = np.random.uniform(1,3)
    rest_height   = np.random.uniform(5,10)
    normal = selected_face.normalAt()
    origin1 = selected_face.Center()+(groove_heigt/2)*normal
    origin2 = origin1 + (rest_height/2)*normal
    wp1 = cq.Workplane(cq.Plane(origin=origin1, xDir=cq.Vector(1,0,0), normal=normal)).cylinder(height=groove_heigt, radius=groove_radius)
    wp2 = cq.Workplane(cq.Plane(origin=origin2, xDir=cq.Vector(1,0,0), normal=normal)).cylinder(height=rest_height, radius=radius).translate(groove_heigt/2*normal)
    shape = shape.union(wp1)

    return shape.union(wp2), [selected_face]
