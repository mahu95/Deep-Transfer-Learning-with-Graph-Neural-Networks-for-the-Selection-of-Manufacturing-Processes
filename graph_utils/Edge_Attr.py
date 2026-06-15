"""Compute the per-edge attribute vector for each AAG edge.

Each B-rep edge (a graph edge between two face nodes) is described by its
convexity (the ``vexity_dic`` value computed earlier, which this module extends
in place), curve type, closed flag, scaled mid/first/last point coordinates,
tangent direction and arc length. As with the face attributes, positions are
normalised via :func:`graph_utils.Scaler.scale`.
"""
from OCC.Core.gp import *
from OCC.Core.ShapeFix import *
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GCPnts import GCPnts_AbscissaPoint
from OCC.Core.BRep import BRep_Tool
from OCC.Core.GeomLProp import GeomLProp_CLProps
from OCC.Core.TopAbs import TopAbs_Orientation
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_ColoredShape

from graph_utils.Scaler import scale

def create_edge_attr_matrix(edges_dic, vexity_dic, solids, bbx_val, ratios, display):
    """Append geometric attributes to each edge's vexity entry and return it.

    ``vexity_dic`` arrives with one convexity value per edge id; this function
    appends the curve type, closed flag, scaled centre/endpoint coordinates,
    tangent and length, returning the completed edge-attribute dictionary.
    """
    edge_points_dic  = {}
    edge_tangent_dic = {}
    for key in edges_dic.keys():
            
        edge = edges_dic[key]

        curve_ada = BRepAdaptor_Curve(edge)

        curve_type   = curve_ada.GetType()
        rational     = curve_ada.IsRational()
        periodic     = curve_ada.IsPeriodic()
        threedcurve  =  curve_ada.Is3DCurve()
        is_closed    = curve_ada.IsClosed()
        if is_closed == True: 
            edge_closed = 1
            # ais_shape = AIS_ColoredShape(edge)
            # ais_shape.SetColor(Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB))
            # display.Context.Display(ais_shape, True)
        else:
            edge_closed = -1

        first_param = curve_ada.FirstParameter()
        last_param  = curve_ada.LastParameter()
        length = GCPnts_AbscissaPoint.Length(curve_ada, first_param, last_param)
        mid_param = (first_param + last_param) / 2.0
        tangent_vector = gp_Dir()

        try:
            geom_curve, _, _ = BRep_Tool.Curve(edge)
        except:
            geom_curve, _ = BRep_Tool.Curve(edge)

        # Alternativ:
        #geom_curve, _, _ = BRep_Tool_Curve(edge)

        props = GeomLProp_CLProps(geom_curve, mid_param, 1, 1e-6)
        props.Tangent(tangent_vector)
        center_point = props.Value()

        # Alternative:
        # center_point = gp_Pnt()
        # tangent_vector = gp_Dir()
        # geom_curve.D1(mid_param, center_point, tangent_vector)

        if  edge.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
                    tangent_vector.Reverse()

        props = GeomLProp_CLProps(geom_curve, first_param, 1, 1e-6)
        first_point = props.Value()

        props = GeomLProp_CLProps(geom_curve, last_param, 1, 1e-6)
        last_point = props.Value()

        vexity_dic[key].append(scale(0, 8, 1, curve_type))
        vexity_dic[key].append(edge_closed)
        vexity_dic[key].append(scale(bbx_val[0], bbx_val[1], ratios[0], center_point.X()))
        vexity_dic[key].append(scale(bbx_val[2], bbx_val[3], ratios[1], center_point.Y()))
        vexity_dic[key].append(scale(bbx_val[4], bbx_val[5], ratios[2], center_point.Z()))
        vexity_dic[key].append(tangent_vector.X())
        vexity_dic[key].append(tangent_vector.Y())
        vexity_dic[key].append(tangent_vector.Z())
        vexity_dic[key].append(scale(bbx_val[0], bbx_val[1], ratios[0], first_point.X()))
        vexity_dic[key].append(scale(bbx_val[2], bbx_val[3], ratios[1], first_point.Y()))
        vexity_dic[key].append(scale(bbx_val[4], bbx_val[5], ratios[2], first_point.Z()))
        vexity_dic[key].append(scale(bbx_val[0], bbx_val[1], ratios[0], last_point.X()))
        vexity_dic[key].append(scale(bbx_val[2], bbx_val[3], ratios[1], last_point.Y()))
        vexity_dic[key].append(scale(bbx_val[4], bbx_val[5], ratios[2], last_point.Z()))
        vexity_dic[key].append(length)

        # vexity_dic[key].append(curve_type)
        # vexity_dic[key].append(edge_closed)
        # vexity_dic[key].append(center_point.X())
        # vexity_dic[key].append(center_point.Y())
        # vexity_dic[key].append(center_point.Z())
        # vexity_dic[key].append(tangent_vector.X())
        # vexity_dic[key].append(tangent_vector.Y())
        # vexity_dic[key].append(tangent_vector.Z())
        # vexity_dic[key].append(length)


    return vexity_dic