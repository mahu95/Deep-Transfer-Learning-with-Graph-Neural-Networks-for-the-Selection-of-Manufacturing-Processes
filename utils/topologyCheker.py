# -*- coding: utf-8 -*-
"""Topological validity checks for B-rep solids.

``TopologyChecker`` validates that an Open CASCADE (pythonOCC) ``TopoDS``
body is suitable for graph construction: non-empty, geometrically valid,
manifold, closed, and without duplicated coedges. It is used to reject
malformed solids before they are turned into a face-adjacency graph.

Attribution
-----------
This module is taken, essentially verbatim, from the AAGNet project:
    AAGNet (whjdark) -- dataset/topologyCheker.py
    https://github.com/whjdark/AAGNet/blob/main/dataset/topologyCheker.py

AAGNet in turn adapted it from BRepNet:
    BRepNet (Autodesk AI Lab) -- pipeline/extract_brepnet_data_from_step.py
    https://github.com/AutodeskAILab/BRepNet/blob/master/pipeline/extract_brepnet_data_from_step.py

Reference:
    Zhang et al., "AAGNet: A graph neural network towards multi-task
    machining feature recognition", Journal of Manufacturing Systems, 2024.
"""
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Extend import TopologyUtils



class TopologyChecker():
    """Validate a B-rep body's topology before graph extraction.

    Adapted from AAGNet (``dataset/topologyCheker.py``), which itself
    modified it from BRepNet. See the module docstring for full citations.
    """
    # Source: AAGNet -- https://github.com/whjdark/AAGNet/blob/main/dataset/topologyCheker.py
    # which was modified from BRepNet: https://github.com/AutodeskAILab/BRepNet/blob/master/pipeline/extract_brepnet_data_from_step.py
    def __init__(self):
        pass

    def find_edges_from_wires(self, top_exp):
        """Return the set of edges reachable by walking every wire."""
        edge_set = set()
        for wire in top_exp.wires():
            wire_exp = TopologyUtils.WireExplorer(wire)
            for edge in wire_exp.ordered_edges():
                edge_set.add(edge)
        return edge_set

    def find_edges_from_top_exp(self, top_exp):
        """Return the set of all edges reported by the topology explorer."""
        edge_set = set(top_exp.edges())
        return edge_set

    def check_closed(self, body):
        """Return True if every edge belongs to a wire (no open/dangling edges)."""
        # In Open Cascade, unlinked (open) edges can be identified
        # as they appear in the edges iterator when ignore_orientation=False
        # but are not present in any wire
        top_exp = TopologyUtils.TopologyExplorer(body, ignore_orientation=False)
        edges_from_wires = self.find_edges_from_wires(top_exp)
        edges_from_top_exp = self.find_edges_from_top_exp(top_exp)
        missing_edges = edges_from_top_exp - edges_from_wires
        return len(missing_edges) == 0

    def check_manifold(self, top_exp):
        """Return True if no face is shared by more than one shell (manifold)."""
        faces = set()
        for shell in top_exp.shells():
            for face in top_exp._loop_topo(TopAbs_FACE, shell):
                if face in faces:
                    return False
                faces.add(face)
        return True

    def check_unique_coedges(self, top_exp):
        """Return True if no (edge, orientation) coedge is reused across loops."""
        coedge_set = set()
        for loop in top_exp.wires():
            wire_exp = TopologyUtils.WireExplorer(loop)
            for coedge in wire_exp.ordered_edges():
                orientation = coedge.Orientation()
                tup = (coedge, orientation)
                # We want to detect the case where the coedges
                # are not unique
                if tup in coedge_set:
                    return False
                coedge_set.add(tup)
        return True

    def __call__(self, body):
        """Run all checks on ``body`` and return True only if every one passes."""
        top_exp = TopologyUtils.TopologyExplorer(body, ignore_orientation=True)
        if top_exp.number_of_faces() == 0:
            print('Empty shape') 
            return False
        # OCC.BRepCheck, perform topology and geometricals check
        analyzer = BRepCheck_Analyzer(body)
        if not analyzer.IsValid(body):
            print('BRepCheck_Analyzer found defects') 
            return False
        # other topology check
        if not self.check_manifold(top_exp):
            print("Non-manifold bodies are not supported")
            return False
        if not self.check_closed(body):
            print("Bodies which are not closed are not supported")
            return False
        if not self.check_unique_coedges(top_exp):
            print("Bodies where the same coedge is uses in multiple loops are not supported")
            return False
        return True