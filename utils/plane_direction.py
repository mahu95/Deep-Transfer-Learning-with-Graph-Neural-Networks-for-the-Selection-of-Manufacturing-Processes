"""Pick an in-plane reference direction for a face given its normal.

Several feature generators need a direction that lies *in* a face (orthogonal to
its normal) to orient slots, steps and similar features. This module projects
the world axes onto the face plane and returns a suitable in-plane vector.
"""
import cadquery as cq
import random

v1 = cq.Vector(1,0,0)
v2 = cq.Vector(0,1,0)
v3 = cq.Vector(0,0,1)
V = [v1, v2, v3]
w1 = 1.0
w2 = 1.0
w3 = 1.0
W = [w1, w2, w3]

def plane_direction(normal):
    """Return a vector lying in the plane whose ``normal`` is given.

    The world axis least aligned with ``normal`` is projected onto the face
    plane and returned, providing a stable in-plane direction for orienting
    features. Ties are broken randomly.
    """
    chosen_v = []
    projection_distance = 100
    for v in V:
        projection_dis = v.dot(normal)
        if projection_dis < projection_distance:
            chosen_v = []
            chosen_v.append(v)
        elif projection_dis == projection_distance:
            chosen_v.append(v)
        else:
            pass

    if len(chosen_v) > 1:
        v = random.choice(chosen_v)
    else:
        v = chosen_v[0]

    dot_product = v.dot(normal)
    projection = normal.multiply(dot_product)
    direction = v - projection
    magnitude = direction.Length
    if magnitude == 0:
        magnitude = 0.001
    normalized_direction = direction.multiply(1.0/magnitude)
    return direction

