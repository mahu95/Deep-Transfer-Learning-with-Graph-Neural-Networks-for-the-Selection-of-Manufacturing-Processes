"""Triangulate individual faces into node coordinates and connectivity.

Beyond the B-rep graph, the dataset stores a light surface mesh per face so the
network can also reason about local geometry. :func:`mesh_face` returns each
triangulation as scaled node coordinates (with per-node normals) and an
edge-connectivity list in COO format. The helpers compute surface normals and,
when a viewer is supplied, draw the points and normals for debugging.
"""

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.gp import gp_Pnt

from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.GeomLProp import GeomLProp_SLProps

from OCC.Display.SimpleGui import init_display
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Dir, gp_Ax1
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeEdge


from graph_utils.Scaler import scale

def calculate_normal(x, y, z, face):
    """
    Calculate the normal vector at a given point on the face.
    """
    # Get the surface of the face
    surface_tool = BRep_Tool.Surface(face)
    
    # Create a point at the given coordinates
    point = gp_Pnt(x, y, z)
    
    projector = GeomAPI_ProjectPointOnSurf(point, surface_tool)
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
    
    return [normal_x, normal_y, normal_z]




def display_point_and_normal(x, y, z, nx, ny, nz, display, scale=5.0):
    """Draw a mesh node and its normal as an arrow in the viewer (debug aid)."""

    # Draw the point
    point = gp_Pnt(x, y, z)
    vertex = BRepBuilderAPI_MakeVertex(point).Shape()
    #display.DisplayShape(vertex, update=False, color="BLUE1")

    # Compute the normal endpoint
    normal_vec = gp_Vec(scale*nx, scale*ny, scale*nz)
    end_point = gp_Pnt(x + normal_vec.X(), y + normal_vec.Y(), z + normal_vec.Z())

    # Create an edge (arrow) from point to end_point
    edge = BRepBuilderAPI_MakeEdge(point, end_point).Shape()
    #display.DisplayShape(edge, update=False, color="GREEN")




def mesh_face(face, mesh, bbx_val, ratios, display):
    """Triangulate one face and return its mesh nodes and edge connectivity.

    Returns ``(node_coordinates, coo_format)`` where each node is a 6-vector of
    scaled ``(x, y, z)`` plus normal, and ``coo_format`` is the deduplicated edge
    list ``[start_indices, end_indices]`` of the triangulation.
    """
    mesh.Perform()
    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)

    if not mesh.IsDone():
        raise Exception("Meshing failed.")
    
    connections = set()
    location = TopLoc_Location()
    triangulation = BRep_Tool.Triangulation(face, location)
    if triangulation:

        triangles = triangulation.Triangles()
        for i in range(1, triangulation.NbTriangles() + 1):
            trian = triangles.Value(i)
            index1, index2, index3 = trian.Get()
            index1 -= 1
            index2 -= 1
            index3 -= 1
            connections.update({(min(index1, index2), max(index1, index2)),
                                (min(index2, index3), max(index2, index3)),
                                (min(index1, index3), max(index1, index3))})
            for j in range(1, 4):
                if j == 1:
                    m = index1
                    n = index2
                elif j == 2:
                    n = index3
                elif j == 3:
                    m = index2
                me = BRepBuilderAPI_MakeEdge(triangulation.Node(m+1), triangulation.Node(n+1))
                if me.IsDone():
                    builder.Add(comp, me.Edge())
            
        connections = sorted(list(connections))  
        coo_format = [[], []]
        for connection in connections:
            coo_format[0].append(connection[0])
            coo_format[1].append(connection[1])

        #print("COO format (connections):", coo_format)

        node_coordinates = []
        display_coordinates = []
        for i in range(1, triangulation.NbNodes() + 1):
            node = triangulation.Node(i)
            node_normals = calculate_normal(node.X(), node.Y(), node.Z(), face)      
            #print(f"Node {i}: Coordinates ({node.X()}, {node.Y()}, {node.Z()}), Normals ({node_normals[0]}, {node_normals[1]}, {node_normals[2]})")
            node_coordinates.append([scale(bbx_val[0], bbx_val[1], ratios[0], node.X()), 
                                    scale(bbx_val[2], bbx_val[3], ratios[1], node.Y()),
                                    scale(bbx_val[4], bbx_val[5], ratios[2], node.Z()), 
                                    node_normals[0],
                                    node_normals[1],
                                    node_normals[2]])
            
            display_coordinates.append([node.X(), node.Y(), node.Z(), node_normals[0], node_normals[1], node_normals[2]])



    else:
        print("No triangulation data available.")

    if display != None:
        display.DisplayShape(comp, update=True)
        for x, y, z, nx, ny, nz in display_coordinates:
            display_point_and_normal(x, y, z, nx, ny, nz, display)



    

    return node_coordinates, coo_format