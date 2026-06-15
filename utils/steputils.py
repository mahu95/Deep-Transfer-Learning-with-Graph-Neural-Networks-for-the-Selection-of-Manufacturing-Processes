"""STEP loading and viewer helpers.

A grab-bag of Open CASCADE (pythonOCC) utilities used by the viewers and by the
labelling code: reading STEP files, querying face type/bounding box, finding the
face nearest a point, and colouring or numbering faces in the 3-D display.
"""
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.TopoDS import topods
from OCC.Core.gp import gp_Pnt
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_ColoredShape
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

from OCC.Core.gp import gp_Pnt
from OCC.Core.AIS import AIS_TextLabel
from OCC.Core.Prs3d import Prs3d_TextAspect, Prs3d_Drawer
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.AIS import  AIS_ColoredShape
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere, GeomAbs_Torus

def get_bounding_box(face):
    """Return the ``(xmin, ymin, zmin)`` corner of the face's bounding box."""
    bbox = Bnd_Box()
    brepbndlib.Add(face, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    return xmin, ymin, zmin

def get_face_type(face):
    """Return the surface type of ``face`` as a string (PLANE/CYLINDER/...)."""
    surface = BRepAdaptor_Surface(face)
    surf_type = surface.GetType()

    if surf_type == GeomAbs_Plane:
        return "PLANE"
    elif surf_type == GeomAbs_Cylinder:
        return "CYLINDER"
    elif surf_type == GeomAbs_Cone:
        return "CONE"
    elif surf_type == GeomAbs_Sphere:
        return "SPHERE"
    elif surf_type == GeomAbs_Torus:
        return "TORUS"
    else:
        return "OTHER"

def load_step(filename):
    """Read a STEP file and return the contained shape."""
    shape = read_step_file(filename)
    return shape


def find_closest_face(shape, point):
    """Return the face of ``shape`` whose centroid is nearest ``point``.

    Used to recover the original face (and thus its label) after a part has been
    exported to and re-read from STEP, where only face-centre coordinates remain.
    """
    min_distance = float('inf')
    closest_face = None
    min_center = None
    exp = TopExp_Explorer(shape, TopAbs_FACE)

    while exp.More():
        face = topods.Face(exp.Current())

        props = GProp_GProps()
        brepgprop.SurfaceProperties(face, props)
        centroid = props.CentreOfMass()
        center_x, center_y, center_z = centroid.X(), centroid.Y(), centroid.Z()
        center = gp_Pnt(center_x, center_y, center_z)
        distance = center.Distance(point)

        if distance < min_distance:
            min_distance = distance
            closest_face = face
            min_center = center
        exp.Next()
    
    # print(min_center.X(), min_center.Y(), min_center.Z())
    # print(point.X(), point.Y(), point.Z())
    return closest_face


def apply_color(display, face_to_color, color):
    """Display ``face_to_color`` in the viewer using the given RGB ``color``."""
    ais_shape = AIS_ColoredShape(face_to_color)
    color_obj = Quantity_Color(*color, Quantity_TOC_RGB)
    ais_shape.SetColor(color_obj)
    display.Context.Display(ais_shape, True)


def apply_number(display, face_to_index, index):
    """Draw the text ``index`` at the centre of ``face_to_index`` in the viewer."""
    props = GProp_GProps()
    brepgprop.SurfaceProperties(face_to_index, props)
    centroid = props.CentreOfMass()
    label = AIS_TextLabel()
    label.SetText(TCollection_ExtendedString(index))
    type_face = get_face_type(face_to_index)
    if type_face == "CYLINDER" or type_face == "CONE":
        x, y, z = get_bounding_box(face_to_index)
        label.SetPosition(gp_Pnt(x,y,z))
    else:
        label.SetPosition(centroid)

    drawer = Prs3d_Drawer()
    text_aspect = Prs3d_TextAspect()
    text_aspect.SetColor(Quantity_Color(0, 0, 0, Quantity_TOC_RGB))  # Black text
    text_aspect.SetHeight(20)  # Text height
    drawer.SetTextAspect(text_aspect)
    label.SetAttributes(drawer)
    display.Context.Display(label, True)