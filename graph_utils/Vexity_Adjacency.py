"""Build the face-adjacency (COO) matrix and classify edge convexity.

For every shared B-rep edge this module decides whether the edge is *convex*,
*concave* or *smooth/tangent* (its "vexity"). Rather than relying on the often
inaccurate dihedral-angle approach (kept commented out for reference), it
samples a tiny circular probe around the edge, finds the nearest point on each
of the two adjoining faces, takes the midpoint and classifies it against the
solid: a midpoint *outside* the solid means concave, *inside* means convex, and
*on* the boundary means smooth. It also emits the adjacency in COO format
(source/target face-index arrays) used to construct the AAG.
"""
import math
import numpy as np

from OCC.Core.BRep import BRep_Tool
from OCC.Core.gp import gp_Pnt
from OCC.Core.gp import *
from collections import defaultdict
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeVertex
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepClass3d import BRepClass3d_SolidClassifier
from OCC.Core.TopAbs import TopAbs_ON, TopAbs_OUT, TopAbs_IN

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_ColoredShape,  AIS_Point

from OCC.Core.Quantity import Quantity_NOC_BLACK
from OCC.Core.Prs3d import Prs3d_PointAspect
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCC.Core.Aspect import Aspect_TypeOfMarker, Aspect_TOM_BALL, Aspect_TOM_X, Aspect_TOM_PLUS
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.Core.Prs3d import Prs3d_PointAspect, Prs3d_Drawer

from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Section
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import topods
from OCC.Core.TopAbs import TopAbs_VERTEX
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_Orientation

def vexity_adjacency_algo(faces_edges, faces_dic, edges_dic, solids, display):
    """Compute edge convexity and the face-adjacency matrix of a solid.

    Parameters
    ----------
    faces_edges : dict
        Mapping face id -> {edge id: ...}, i.e. which edges bound each face.
    faces_dic, edges_dic : dict
        Lookups from id to the corresponding ``TopoDS`` face / edge.
    solids : iterable
        The solid(s) of the part, used to classify probe points as in/out/on.
    display : optional
        pythonOCC viewer for debug drawing (unused unless visualising).

    Returns
    -------
    adj_matrix_coo : numpy.ndarray
        2xN source/target face-index array (the AAG adjacency in COO form).
    face_id_to_index, edge_id_to_index : dict
        Maps between original ids and the contiguous node/edge indices.
    vexity_dic : dict
        Edge id -> ``[1]`` concave, ``[-1]`` convex, or ``[0]`` smooth/border.
    """
    aux_dict = defaultdict(set)

    for outer_key, inner_dict in faces_edges.items():
        for inner_key in inner_dict.keys():
            aux_dict[inner_key].add(outer_key)

    vexity_dic = {}
    for outer_key, faces in aux_dict.items():
        edge = edges_dic[outer_key]
        #print(faces)
        if len(faces) == 1:
            vexity_dic[outer_key] = [0]
            # ais_edge = AIS_ColoredShape(edge)
            # ais_edge.SetColor(Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB))
            # display.Context.Display(ais_edge, True)
        else:
            curve_tool = BRep_Tool.Curve(edge)
            ce_u = (curve_tool[1] + curve_tool[2]) / 2
            ce = gp_Pnt(0, 0, 0)
            tangent = gp_Vec(0, 0, 0)
            curve_tool[0].D1(ce_u, ce, tangent)
            tangent = gp_Dir(tangent)
            if  edge.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
                tangent.Reverse()

            circle = gp_Circ(gp_Ax2(ce, tangent), 1/10)
            profile_edge = BRepBuilderAPI_MakeEdge(circle).Edge()

            ada_profile = BRepAdaptor_Curve(profile_edge)
            tool_profile = BRep_Tool.Curve(profile_edge)[0]

            face1 = faces_dic[list(faces)[0] ]
            face2 = faces_dic[list(faces)[1] ]

            c1 = gp_Pnt(0, 0, 0)
            c2 = gp_Pnt(0, 0, 0)

            try:
                section1 = BRepAlgoAPI_Section(face1, profile_edge, False)
                section1.ComputePCurveOn1(True)
                section1.Build()
                if not section1.IsDone():
                    raise Exception("Section computation failed")
                exp = TopExp_Explorer(section1.Shape(), TopAbs_VERTEX)
                while exp.More():
                    vertex = topods.Vertex(exp.Current())
                    c1 = BRep_Tool.Pnt(vertex)
                    exp.Next()

                section2 = BRepAlgoAPI_Section(face2, profile_edge, False)
                section2.ComputePCurveOn1(True)
                section2.Build()
                if not section2.IsDone():
                    raise Exception("Section computation failed")
                exp = TopExp_Explorer(section2.Shape(), TopAbs_VERTEX)
                while exp.More():
                    vertex = topods.Vertex(exp.Current())
                    c2 = BRep_Tool.Pnt(vertex)
                    exp.Next()
            except:
                lbound = math.ceil(ada_profile.FirstParameter() * 1000)
                ubound = math.ceil(ada_profile.LastParameter() * 1000)
                count_f1_dis = 0
                count_f2_dis = 0
                dist_1_prev = 1
                dist_2_prev = 1
                still_bigger_1 = 0
                still_bigger_2 = 0
                threshold = 1e-3
                    
                for b in range(lbound, ubound, 5):
                    c = b / 1000        
                    c_Pnt = tool_profile.Value(c) 
                    c_ver = BRepBuilderAPI_MakeVertex(c_Pnt).Vertex()
                    f1 = faces_dic[list(faces)[0] ]
                    f2 = faces_dic[list(faces)[1] ]
                    dist_1 = BRepExtrema_DistShapeShape(c_ver, f1).Value()
                    dist_2 = BRepExtrema_DistShapeShape(c_ver, f2).Value()

                    if count_f1_dis == 0:
                        if dist_1 <= threshold:  
                            if dist_1_prev > dist_1:
                                dist_1_prev = dist_1
                                c1_prev = c_Pnt
                                still_bigger_1 += 1
                            elif dist_1_prev < dist_1:
                                c1 = c1_prev
                                count_f1_dis += 1
                    
                    if count_f2_dis == 0:
                        if dist_2 <= threshold:  
                            if dist_2_prev > dist_2:
                                dist_2_prev = dist_2
                                c2_prev = c_Pnt
                                still_bigger_2 += 1
                            elif dist_2_prev < dist_2:
                                c2 = c2_prev
                                count_f2_dis += 1
                    
                    if count_f1_dis == 1 and count_f2_dis == 1:
                        break


            "Alternative zur Bestimmung der Vexität mit Berechnung des Dihedralwinkels (leider ungenau)"
            # surface1 = BRep_Tool.Surface(face1)
            # projector1 = GeomAPI_ProjectPointOnSurf(center_point, surface1)
            # u1, v1 = projector1.LowerDistanceParameters()
            # props1 = GeomLProp_SLProps(surface1, u1, v1, 1, 1e-6)
            # if props1.IsNormalDefined():
            #     normal1 = props1.Normal()
            #     if face1.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
            #         normal1.Reverse()

            # surface2 = BRep_Tool.Surface(face2)
            # projector2 = GeomAPI_ProjectPointOnSurf(center_point, surface2)
            # u2, v2 = projector2.LowerDistanceParameters()
            # props2 = GeomLProp_SLProps(surface2, u2, v2, 1, 1e-6)
            # if props2.IsNormalDefined():
            #     normal2 = props2.Normal()
            #     if face2.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
            #         normal2.Reverse()

            # angle_radians = normal1.Angle(normal2)
            # angle_degrees = math.degrees(angle_radians)

            # try:
            #     direction = normal1.Crossed(normal2)

            #     if direction.Dot(tangent) < 0.0:
            #         angle_degrees = 360 - angle_degrees

            #     if angle_degrees < 180:
            #         vexity_dic[outer_key] = [1]
            #         ais_edge = AIS_ColoredShape(edge)
            #         ais_edge.SetColor(Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB))
            #         display.Context.Display(ais_edge, True)
            #     else:
            #         vexity_dic[outer_key] = [-1]
            #         ais_edge = AIS_ColoredShape(edge)
            #         ais_edge.SetColor(Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB))
            #         display.Context.Display(ais_edge, True)
            # except RuntimeError as e:
            #     if 'Standard_ConstructionError' in str(e):
            #         vexity_dic[outer_key] = [0]
            #         ais_edge = AIS_ColoredShape(edge)
            #         ais_edge.SetColor(Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB))
            #         display.Context.Display(ais_edge, True)
            #         angle_degrees = 180

            # vexity_dic[outer_key] = [scale(0, 360, 1, angle_degrees)]
                    

            if isinstance(c1, gp_Pnt):
                c1 = np.array([c1.X(), c1.Y(), c1.Z()])
            if isinstance(c2, gp_Pnt):
                c2 = np.array([c2.X(), c2.Y(), c2.Z()])


            px = 0.5 * np.add(c1, c2)
            px = gp_Pnt(px[0], px[1], px[2])
            for sol in solids:
                in_solid = BRepClass3d_SolidClassifier(sol, px, 1e-6)
                if in_solid.State() == TopAbs_OUT:
                    #concave
                    vexity_dic[outer_key] = [1]
                    ais_edge = AIS_ColoredShape(edge)
                    ais_edge.SetColor(Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB))
                    #display.Context.Display(ais_edge, True)
                elif in_solid.State() == TopAbs_IN:
                    #convex
                    vexity_dic[outer_key] = [-1]
                    ais_edge = AIS_ColoredShape(edge)
                    ais_edge.SetColor(Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB))
                    #display.Context.Display(ais_edge, True)

                elif in_solid.State() == TopAbs_ON:
                    vexity_dic[outer_key] = [0]
                    ais_edge = AIS_ColoredShape(edge)
                    ais_edge.SetColor(Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB))
                    #display.Context.Display(ais_edge, True)


    face_id_to_index = {}
    index = 0
    for face_id in faces_dic.keys():
        face_id_to_index[face_id] = index
        index += 1

    index = 0
    coo_source = []
    coo_target = []
    edge_id_to_index = {}

    for edge_id, face_ids in aux_dict.items():
        edge_id_to_index[index] = edge_id
        face_indices = [face_id_to_index[face_id] for face_id in face_ids]

        if len(face_indices) == 1:
            coo_source.append(face_indices[0])
            coo_target.append(face_indices[0])

        else:
            coo_source.append(face_indices[0])
            coo_target.append(face_indices[1])
        
        index += 1

    coo_source_np = np.array(coo_source)
    coo_target_np = np.array(coo_target)

    adj_matrix_coo = np.vstack([coo_source_np, coo_target_np])

    return adj_matrix_coo, face_id_to_index, edge_id_to_index, vexity_dic
                    

            # Display-Circle
            # ais_shape = AIS_ColoredShape(profile_edge)
            # line_aspect = Prs3d_LineAspect(Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB), Aspect_TOL_SOLID, 10.0)
            # ais_shape.Attributes().SetLineAspect(line_aspect)
            # display.Context.Display(ais_shape, False)

            # Display Point 1
            # geom_point = Geom_CartesianPoint(point1) 
            # ais_shape = AIS_Point(geom_point)
            # marker_type = Aspect_TOM_X  # You can choose other marker types like Aspect_TOM_POINT, Aspect_TOM_PLUS, etc.
            # marker_color = Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB)  # Black color
            # marker_size = 4.0  # Adjust the size as needed
            # point_aspect = Prs3d_PointAspect(marker_type, marker_color, marker_size)
            # drawer = Prs3d_Drawer()
            # drawer.SetPointAspect(point_aspect)
            # ais_shape.SetAttributes(drawer)
            # display.Context.Display(ais_shape, False) 

            # Display Point 2
            # geom_point = Geom_CartesianPoint(point2) 
            # ais_shape = AIS_Point(geom_point)
            # marker_type = Aspect_TOM_X  # You can choose other marker types like Aspect_TOM_POINT, Aspect_TOM_PLUS, etc.
            # marker_color = Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB)  # Black color
            # marker_size = 4.0  # Adjust the size as needed
            # point_aspect = Prs3d_PointAspect(marker_type, marker_color, marker_size)
            # drawer = Prs3d_Drawer()
            # drawer.SetPointAspect(point_aspect)
            # ais_shape.SetAttributes(drawer)
            # display.Context.Display(ais_shape, False)     
                          
            
            #Display Point 3
            # geom_point = Geom_CartesianPoint(px) 
            # ais_shape = AIS_Point(geom_point)
            # marker_type = Aspect_TOM_PLUS  # You can choose other marker types like Aspect_TOM_POINT, Aspect_TOM_PLUS, etc.
            # marker_color = Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB)  # Black color
            # marker_size = 4.0  # Adjust the size as needed
            # point_aspect = Prs3d_PointAspect(marker_type, marker_color, marker_size)
            # drawer = Prs3d_Drawer()
            # drawer.SetPointAspect(point_aspect)
            # ais_shape.SetAttributes(drawer)
            # display.Context.Display(ais_shape, False)

              
        

                

