"""Machining feature: turn a raised belt (step up then down) onto a cylinder."""
import cadquery as cq
import random
import numpy as np

from utils.round_near_zero import round_near_zero

def step_belt(shape, face_selector=None):
    """Turn a belt onto a cylinder end: a narrower band between two cones.

    Selects a top/bottom cylinder face (avoiding ``face_selector`` if given) and
    builds a tapered-down section, a reduced-diameter band, a tapered-up section
    and a full-radius remainder. Returns ``(shape, None)``.
    """
    #print("step_belt_cylinder")
    face_selectors = [">Z", "<Z"]
    if face_selector:
        if face_selector in face_selectors:
            face_selectors.remove(face_selector)
    selected_face_selector = random.choice(face_selectors)
    selected_face = shape.faces(selected_face_selector).val()
    bb = selected_face.BoundingBox()
    #print(bb.zmax, bb.zmin)
    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
    bby = round_near_zero(abs(bb.ymax-bb.ymin))
    bbz = round_near_zero(abs(bb.zmax-bb.zmin))
    #print(bbx, bby, bbz)

    radius1 = np.sqrt(np.square(bbx)/4)
    radius2 = np.random.uniform(radius1/2, radius1/1.1)
    height  = np.random.uniform(2,5)
    rest_height   = np.random.uniform(3,5)
    rest_height_2   = np.random.uniform(5,10)
    normal_z = selected_face.normalAt()
    if normal_z == cq.Vector(0,0,-1):
        normal = cq.Vector(0,1,0)
    else:
        normal = cq.Vector(0,-1,0)
    center  = selected_face.Center()
    origin2 = center + normal_z*height
    origin3 = origin2 + normal_z*rest_height/2
    origin4 = origin3 + normal_z*height

    path1 = cq.Workplane(cq.Plane(origin=center, xDir=cq.Vector(1,0,0), normal=normal)).lineTo(radius1, 0).lineTo(radius2, height).lineTo(0, height).lineTo(0, 0).wire()
    cone1 = path1.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
    shape = shape.union(cone1)
    wp2 = cq.Workplane(cq.Plane(origin=origin2, xDir=cq.Vector(1,0,0), normal=normal_z)).cylinder(height=rest_height, radius=radius2).translate(rest_height/2*normal_z)
    shape = shape.union(wp2)
    path2 = cq.Workplane(cq.Plane(origin=origin3, xDir=cq.Vector(1,0,0), normal=normal)).lineTo(radius2, 0).lineTo(radius1, height).lineTo(0, height).lineTo(0, 0).wire()
    cone2 = path2.revolve(angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,1,0))
    shape = shape.union(cone2)
    wp3 = cq.Workplane(cq.Plane(origin=origin4, xDir=cq.Vector(1,0,0), normal=normal_z)).cylinder(height=rest_height_2, radius=radius1).translate(rest_height_2/2*normal_z)

    return shape.union(wp3), None