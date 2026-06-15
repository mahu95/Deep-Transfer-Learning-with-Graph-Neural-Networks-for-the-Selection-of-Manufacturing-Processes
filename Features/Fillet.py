"""Machining feature: fillet (round) a random edge of the part."""
import cadquery as cq
import random
import numpy as np

def fillet(shape, seg_dict):
    """Fillet one randomly chosen edge of a stock face by a random radius.

    Picks a face still labelled as stock, selects one of its edges and applies a
    fillet with a random radius, retrying until CadQuery accepts the edge.
    Returns the modified shape.
    """
    #print("fillet")
    faces = []
    for face, value in seg_dict.items():
        if value == 0:
            faces.append(face)
    selected_face = random.choice(faces)
    wp = cq.Workplane().newObject([selected_face])
    edges = wp.edges().vals()
    boolean = True
    while boolean:
        try:
            random_edge = random.choice(edges)
            parameter = np.random.uniform(0.1,10)
            shape = shape.newObject([random_edge]).fillet(parameter)
            boolean = False
        except:
            boolean = True


    return shape



