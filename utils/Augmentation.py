"""Data augmentation for generated parts (currently random 3-axis rotation)."""

import numpy as np
import cadquery as cq

def rotation(shape, segmentation_dict, feature_dict):
    """Apply a random rotation to a part and its per-face label dictionaries.

    The same random X/Y/Z rotation is applied to the body and to every face key
    so that the segmentation and feature dictionaries stay aligned with the
    rotated geometry. Returns the rotated ``shape`` and rebuilt dictionaries.
    """
    angle_x = np.random.randint(0, 360)
    angle_y = np.random.randint(0, 360)
    angle_z = np.random.randint(0, 360)

    shape = shape.rotate((0, 0, 0), (1, 0, 0), angle_x).rotate((0, 0, 0), (0, 1, 0), angle_y).rotate((0, 0, 0), (0, 0, 1), angle_z)   

    seg_dict = {}
    feat_dict = {}
    for face, label in segmentation_dict.items():
        feat_id = feature_dict[face]
        face = face.rotate((0, 0, 0), (1, 0, 0), angle_x).rotate((0, 0, 0), (0, 1, 0), angle_y).rotate((0, 0, 0), (0, 0, 1), angle_z)   
        seg_dict[face] = label
        feat_dict[face] = feat_id


    return shape, seg_dict, feat_dict

