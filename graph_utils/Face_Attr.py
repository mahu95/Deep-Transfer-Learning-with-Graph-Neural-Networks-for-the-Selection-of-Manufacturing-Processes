"""Compute the per-face geometric attribute vector for each graph node.

Each face becomes a node of the AAG whose feature vector encodes its surface
type, whether its centroid lies inside the solid, the (scaled) centroid
coordinates, the surface normal, the U/V aspect ratio and the surface area.
Coordinates are normalised with :func:`graph_utils.Scaler.scale` so parts of
different sizes are comparable. A surface mesh is also generated per face.
"""
from OCC.Core.gp import *
from OCC.Core.ShapeFix import *
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepClass3d import BRepClass3d_SolidClassifier
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepClass3d import BRepClass3d_SolidClassifier

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_ColoredShape

from graph_utils.Scaler import scale
from graph_utils.Mesh import mesh_face


    
def evaluate_surface(surface, u, v):
    """Return the 3-D point on ``surface`` at parameters ``(u, v)``."""
    props = GeomLProp_SLProps(surface, u, v, 1, 1e-6)
    point = props.Value()
    return point



def create_face_attr_matrix(faces_dic, mesh, solids, bbx_val, ratios, display):
    """Build the geometric face-attribute table (and per-face meshes).

    Returns ``(faces_attr, face_mesh_coor_dic, face_mesh_conn_dic)`` where
    ``faces_attr`` maps each face id to its node feature vector, and the two mesh
    dicts hold the meshed coordinates/connectivity per face. ``bbx_val`` and
    ``ratios`` come from :mod:`graph_utils.Scaler` and drive coordinate scaling.
    """
    faces_attr = {}
    face_mesh_coor_dic = {}
    face_mesh_conn_dic = {}
    for key in faces_dic.keys():
        face = faces_dic[key]

        surface_tool = BRep_Tool.Surface(face)
        surface_ada = BRepAdaptor_Surface(face)

        surface_type = surface_ada.GetType()
        # if surface_type > 0:
        #     ais_shape = AIS_ColoredShape(face)
        #     ais_shape.SetColor(Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB))
        #     display.Context.Display(ais_shape, True)

        props = GProp_GProps()
        brepgprop.SurfaceProperties(face, props)
        area = props.Mass()
        centroid = props.CentreOfMass()
        center_x, center_y, center_z = centroid.X(), centroid.Y(), centroid.Z()

        classifier = BRepClass3d_SolidClassifier(solids[0])
        classifier.Perform(centroid, 1e-3) 
        center_in_part = classifier.State()
        # if center_in_part == 1:
        #     ais_shape = AIS_ColoredShape(face)
        #     ais_shape.SetColor(Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB))
        #     display.Context.Display(ais_shape, True)


        projector = GeomAPI_ProjectPointOnSurf(centroid, surface_tool)
        if projector.IsDone():
            closest_point = projector.NearestPoint()
            u, v = projector.LowerDistanceParameters()
            prop_normal = GeomLProp_SLProps(surface_tool, u, v, 1, 1e-5)
            if prop_normal.IsNormalDefined():
                normal = prop_normal.Normal()
                normal_x, normal_y, normal_z = normal.X(), normal.Y(), normal.Z()
            else:
                normal_x, normal_y, normal_z = 0.0, 0.0, 0.0
        else:
            normal_x, normal_y, normal_z = 0.0, 0.0, 0.0

        u_min, u_max, v_min, v_max = surface_ada.FirstUParameter(), surface_ada.LastUParameter(), surface_ada.FirstVParameter(), surface_ada.LastVParameter()

        u_length = u_max - u_min
        v_length = v_max - v_min

        ratio = u_length / v_length

        point1 = evaluate_surface(surface_tool, u_min, v_min)
        point2 = evaluate_surface(surface_tool, u_max, v_min)
        point3 = evaluate_surface(surface_tool, u_max, v_max)
        point4 = evaluate_surface(surface_tool, u_min, v_max)


        face_mesh_coordinates, face_mesh_connections = mesh_face(face, mesh, bbx_val, ratios, display)
        face_mesh_coor_dic[key] = face_mesh_coordinates
        face_mesh_conn_dic[key] = face_mesh_connections

        faces_attr[key] = [scale(0, 10, 1, surface_type), 
                           scale(0, 3, 1, center_in_part), 
                           scale(bbx_val[0], bbx_val[1], ratios[0], center_x),
                           scale(bbx_val[2], bbx_val[3], ratios[1], center_y),
                           scale(bbx_val[4], bbx_val[5], ratios[2], center_z), 
                           normal_x, 
                           normal_y, 
                           normal_z,
                           #scale(bbx_val[0], bbx_val[1], ratios[0], point1.X()),
                           #scale(bbx_val[2], bbx_val[3], ratios[1], point1.Y()),
                           #scale(bbx_val[4], bbx_val[5], ratios[2], point1.Z()),
                           #scale(bbx_val[0], bbx_val[1], ratios[0], point2.X()),
                           #scale(bbx_val[2], bbx_val[3], ratios[1], point2.Y()),
                           #scale(bbx_val[4], bbx_val[5], ratios[2], point2.Z()),
                           #scale(bbx_val[0], bbx_val[1], ratios[0], point3.X()),
                           #scale(bbx_val[2], bbx_val[3], ratios[1], point3.Y()),
                           #scale(bbx_val[4], bbx_val[5], ratios[2], point3.Z()),
                           #scale(bbx_val[0], bbx_val[1], ratios[0], point4.X()),
                           #scale(bbx_val[2], bbx_val[3], ratios[1], point4.Y()),
                           #scale(bbx_val[4], bbx_val[5], ratios[2], point4.Z()),
                           ratio,                            
                           area]

        # faces_attr[key] = [surface_type, 
        #                    center_in_part, 
        #                    center_x,
        #                    center_y,
        #                    center_z, 
        #                    normal_x, 
        #                    normal_y, 
        #                    normal_z,
        #                    ratio,                            
        #                    area]

    return faces_attr, face_mesh_coor_dic, face_mesh_conn_dic
