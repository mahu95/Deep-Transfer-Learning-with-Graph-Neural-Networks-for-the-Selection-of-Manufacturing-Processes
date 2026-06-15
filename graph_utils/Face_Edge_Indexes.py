"""Index the faces, edges and solids of a STEP part for graph construction.

This is the first step of :func:`graph_utils.Step_Conversion.convert_step`. It
collects the solids, builds id->edge and id->face lookups (preferring the STEP
entity id, falling back to a hash code), and records which edges bound each
face. Faces are matched to their saved label rows via their centre coordinates
(see :func:`utils.steputils.find_closest_face`).
"""

from OCC.Core.gp import *
from OCC.Core.ShapeFix import  ShapeFix_Solid
from OCC.Core.TopoDS import topods
from OCC.Core.TopAbs import TopAbs_EDGE, TopAbs_SOLID
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.StepRepr import StepRepr_RepresentationItem
from OCC.Core.gp import gp_Pnt
from OCC.Core.AIS import AIS_TextLabel
from OCC.Core.Graphic3d import Graphic3d_HTA_CENTER, Graphic3d_VTA_CENTER
from OCC.Core.Prs3d import Prs3d_TextAspect, Prs3d_Drawer
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.AIS import AIS_Shape,  AIS_ColoredShape
from OCC.Core.Geom import Geom_Curve
from OCC.Core.BRep import BRep_Tool

from utils.steputils import find_closest_face



def create_face_edge_index(shape, tr, model, display, centers):
    """Index a part's topology for the graph builder.

    Returns ``(faces_dic, edges_dic, faces_edges, solids)``:

    * ``faces_dic`` -- face id -> ``TopoDS_Face`` (ids follow the label order,
      recovered by nearest centre to ``centers``),
    * ``edges_dic`` -- edge id -> ``TopoDS_Edge``,
    * ``faces_edges`` -- face id -> {edge id: edge} bounding that face,
    * ``solids`` -- list of the part's solids.
    """
    topExp = TopExp_Explorer()

    topExp.Init(shape, TopAbs_SOLID)
    solids = []
    index = 0
                    
    while topExp.More():
        sol = topods.Solid(topExp.Current())
        ShapeFix_Solid(sol)
        solids.append(sol)
        index += 1
        topExp.Next()


    topExp.Init(shape, TopAbs_EDGE)
    edges_dic   = {}
    Edge_to_ID  = {}
    index = 0
    
    integer = 2147483647  

    while topExp.More():
        e    = topExp.Current()
        edge = topods.Edge(e)
        try:
            geom_curve, _, _ = BRep_Tool.Curve(edge)
        except:
            geom_curve, _ = BRep_Tool.Curve(edge)
        if isinstance(geom_curve, Geom_Curve):
            item = tr.EntityFromShapeResult(e, 1)
            item = StepRepr_RepresentationItem.DownCast(item)
            edge_ID   = model.IdentLabel(item)
            if edge_ID == 0:
                edge_ID = e.HashCode(integer)

            # curve_ada = BRepAdaptor_Curve(edge)
            # midpoint_param = (curve_ada.FirstParameter() + curve_ada.LastParameter()) / 2
            # edge_center_point = curve_ada.Value(midpoint_param)

            # ais_shape = AIS_ColoredShape(edge)
            # ais_shape.SetColor(Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB))
            # display.Context.Display(ais_shape, True)

        # Text-Label for Edges
        # label = AIS_TextLabel()
        # label.SetText(TCollection_ExtendedString(edge_ID))
        # label.SetPosition(edge_center_point)
        # drawer = Prs3d_Drawer()
        # text_aspect = Prs3d_TextAspect()
        # text_aspect.SetColor(Quantity_Color(0, 0, 0, Quantity_TOC_RGB))  # Black text
        # text_aspect.SetHeight(20)  # Text height
        # drawer.SetTextAspect(text_aspect)
        # label.SetAttributes(drawer)
        # display.Context.Display(label, False)
 
            edges_dic[edge_ID] = edge
            Edge_to_ID[edge] = edge_ID


        topExp.Next()
        index += 1


    faces_dic = {}
    faces_edges = {}
    for face_ID in range(0,len(centers)):
        center = centers[face_ID]
        closest_face = find_closest_face(shape, gp_Pnt(center[0], center[1], center[2]))
        faces_dic[face_ID] = closest_face

        # ais_shape = AIS_ColoredShape(face)
        # ais_shape.SetColor(Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB))
        # display.Context.Display(ais_shape, True)

        ed = TopologyExplorer(closest_face)           
        for e in ed.edges():
            try:
                geom_curve, _, _ = BRep_Tool.Curve(e)
            except:
                geom_curve, _ = BRep_Tool.Curve(e)
            if isinstance(geom_curve, Geom_Curve):
                edge_ID = Edge_to_ID[e]
                if face_ID in faces_edges:
                    if edge_ID not in faces_edges[face_ID]:
                        faces_edges[face_ID][edge_ID] = e
                else:
                    dic = {}
                    dic[edge_ID] = e
                    faces_edges[face_ID] = dic

            topExp.Next()

    # print(faces_dic)
    # print('###########')
    # print(edges_dic)
    # print('###########')
    # print(faces_edges)
    # print('###########')
    # print(solids)
    return faces_dic, edges_dic, faces_edges, solids    