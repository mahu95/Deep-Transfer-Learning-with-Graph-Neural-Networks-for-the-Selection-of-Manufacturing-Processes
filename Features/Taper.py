"""Machining feature: turn a tapered (conical) section onto a cylinder end."""
import cadquery as cq
import random
import numpy as np

from utils.round_near_zero import round_near_zero

def taper(shape, face_selector = None):
    """Add a conical taper plus a reduced-diameter section to a cylinder end.

    Selects a top/bottom cylinder face (avoiding ``face_selector`` if given),
    revolves a profile into a cone and unions a smaller cylinder onto its small
    end. Returns ``(shape, None)``.
    """
    #print("taper_cylinder")
    face_selectors = [">Z", "<Z"]
    if face_selector:
        if face_selector in face_selectors:
            face_selectors.remove(face_selector)
    selected_face_selector = random.choice(face_selectors)
    selected_face = shape.faces(selected_face_selector).val()
    bb = selected_face.BoundingBox()
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))


    radius1 = np.sqrt(np.square(bbx)/4)
    radius2 = np.random.uniform(radius1/1.8, radius1/1.1)
    height  = np.random.uniform(3,5)
    rest_height   = np.random.uniform(5,10)
    normal_z = selected_face.normalAt()
    if normal_z == cq.Vector(0,0,-1):
        normal = cq.Vector(0,1,0)
    else:
        normal = cq.Vector(0,-1,0)
    center  = selected_face.Center()
    origin2 = center + normal_z*height

    path = cq.Workplane(cq.Plane(origin=center, xDir=cq.Vector(1,0,0), normal=normal)).lineTo(radius1, 0).lineTo(radius2, height).lineTo(0, height).lineTo(0, 0).wire()
    cone = path.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
    shape = shape.union(cone)
    wp2 = cq.Workplane(cq.Plane(origin=origin2, xDir=cq.Vector(1,0,0), normal=normal_z)).cylinder(height=rest_height, radius=radius2).translate(height/2*normal_z)

    return shape.union(wp2), None
