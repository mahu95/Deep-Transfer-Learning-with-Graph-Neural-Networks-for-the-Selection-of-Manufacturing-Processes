"""Coordinate normalisation helpers for graph attributes.

To make parts of different sizes comparable, all positional attributes are
normalised into roughly ``[-1, 1]`` based on the part's bounding box, with each
axis additionally weighted by its size relative to the largest dimension so the
overall aspect ratio is preserved.
"""
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib

def get_bounding_box_val(shape):
    """Return the part's axis-aligned bounding box as ``[xmin, xmax, ..., zmax]``."""
    bounding_box = Bnd_Box()
    brepbndlib.Add(shape, bounding_box)
    xmin, ymin, zmin, xmax, ymax, zmax = bounding_box.Get()
    return [xmin, xmax, ymin, ymax, zmin, zmax]


def get_ratio_to_scale_largest_dim(bbx_val):
    """Return per-axis ratios of each box dimension to the largest dimension."""
    xmin = bbx_val[0]
    xmax = bbx_val[1]
    ymin = bbx_val[2]
    ymax = bbx_val[3] 
    zmin = bbx_val[4]
    zmax = bbx_val[5]   
    x_length = xmax - xmin
    y_length = ymax - ymin
    z_length = zmax - zmin

    if x_length >= y_length and x_length >= z_length:
        parameter_max = xmax
        parameter_min = xmin
    elif y_length >= x_length and y_length >= z_length:
        parameter_max = ymax
        parameter_min = ymin
    elif z_length >= x_length and z_length >= y_length:
        parameter_min = zmin
        parameter_max = zmax

    max_length = parameter_max - parameter_min

    x_ratio = x_length / max_length
    y_ratio = y_length / max_length
    z_ratio = z_length / max_length

    return [x_ratio, y_ratio, z_ratio]

def scale(min_val, max_val, ratio, value):
    """Map ``value`` from ``[min_val, max_val]`` to ``[-1, 1]`` scaled by ``ratio``."""
    scaled_val = (2 * (value - min_val) / (max_val - min_val) - 1)
    return scaled_val * ratio

def scale_dict_val(dict, column):
    """Min-max normalise one ``column`` across all entries of ``dict`` in place."""
    max_val = 0.0
    min_val = float('inf')
    for key, values in dict.items():
        if values[column] > max_val:
            max_val = values[column]
        if values[column] < min_val:
            min_val = values[column]

    for key, values in dict.items():
        scaled_val = scale(min_val, max_val, 1, values[column])
        values[column] = scaled_val
        dict[key] = values

    return dict
