"""Small Open CASCADE (pythonOCC) helpers shared across the pipeline.

``SURFACE_TYPE`` and ``CURVE_TYPE`` give the canonical ordering of B-rep surface
and curve kinds, used when one-hot encoding face/edge geometry types.
"""
from OCC.Extend.TopologyUtils import TopologyExplorer

SURFACE_TYPE = ['plane', 'cylinder', 'cone', 'sphere', 'torus', 'bezier', 'bspline', 'revolution', 'extrusion', 'offset', 'other']
CURVE_TYPE = ['line', 'circle', 'ellipse', 'hyperbola', 'parabola', 'bezier', 'bspline', 'offset', 'other']


def list_face(shape):
    """Return all faces of ``shape`` as a list of ``TopoDS_Face`` objects."""
    topo = TopologyExplorer(shape)

    return list(topo.faces())

