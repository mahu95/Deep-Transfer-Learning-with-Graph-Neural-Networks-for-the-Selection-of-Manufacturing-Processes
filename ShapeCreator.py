"""Synthetic part generator: assemble a stock body, machine features into it,
label every face, attach PMI, and export the part plus its graph.

This module is the heart of the dataset-generation pipeline. Given a stock
solid (cylinder or cuboid) and a ``combo`` (an ordered list of feature ids),
:func:`create_shape` applies each machining feature in turn, tracks which faces
belong to which feature and manufacturing technology, augments the part with a
random rotation, adds PMI annotations, and writes out the STEP geometry, the
label/feature/PMI spreadsheets and the face-adjacency graph.

Two lookup tables map feature ids to the functions that create them:

* ``poly_feat`` -- features valid on a prismatic (cuboid) stock.
* ``cyl_feat``  -- features valid on a rotational (cylinder) stock.

The ``display_*`` helpers are optional pythonOCC viewers used for visual
debugging (colouring faces by feature or by manufacturing-technology label).
"""
import cadquery as cq
import json
from numpy import number
import pandas as pd
import random

from OCC.Display.SimpleGui import init_display
from OCC.Core.gp import gp_Pnt

from Features.Hole_Through import through_hole_polygon, through_hole_cylinder
from Features.Step_Through import through_step_polygon, through_step_cylinder
from Features.Slot_Through import through_slot_polygon
from Features.Hole_Blind import blind_hole_cylinder_drilled, blind_hole_cylinder_milled, blind_hole_polygon_drilled, blind_hole_polygon_milled
from Features.Slot_Blind import blind_slot_polygon, slot_cylinder
from Features.Step_Blind import blind_step_polygon
from Features.Chamfer import chamfer
from Features.Fillet import fillet
from Features.Boss_Cuboid import cuboid_boss_polygon, cuboid_boss_cylinder
from Features.Boss_Round import round_boss
from Features.Passage import rectangular_passage
from Features.Pocket_Rectangular import rectangular_pocket_polygon, rectangular_pocket_cylinder
from Features.Groove import groove
from Features.Taper import taper
from Features.Step_Belt import step_belt
from Features.Pocket_Circular_End import circular_end_pocket_polygon, circular_end_pocket_cylinder
from Features.Counter_Hole import counterbore_hole_cylinder, countersink_hole_cylinder, counterbore_hole_polygon, countersink_hole_polygon

from utils.Label import updateLabels, correct_stock_faces_cyl, updateCuboidBossCylinderBegin, updateCuboidBossCylinderEnd, remove_stock_labels
from utils.round_near_zero import round_near_zero
from utils.steputils import load_step, find_closest_face, apply_color, apply_number
from utils.PMI import addPMIToShape
from utils.Augmentation import rotation

from graph_utils.Step_Conversion import convert_step

poly_feat = {   1: cuboid_boss_polygon,
                2: round_boss, 
                3: through_step_polygon,
                4: through_slot_polygon,
                5: blind_step_polygon,
                6: blind_slot_polygon,
                7: rectangular_pocket_polygon,
                8: circular_end_pocket_polygon,
                9: blind_hole_polygon_milled,
                10: blind_hole_polygon_drilled,
                11: through_hole_polygon,
                12: countersink_hole_polygon,
                13: counterbore_hole_polygon,
                14: chamfer,
                15: fillet}


cyl_feat = {    1: cuboid_boss_cylinder,
                2: through_step_cylinder,
                3: groove,
                4: step_belt,
                5: taper,
                6: slot_cylinder,
                7: rectangular_pocket_cylinder, 
                8: circular_end_pocket_cylinder,
                9: blind_hole_cylinder_milled,
                10: blind_hole_cylinder_drilled,
                11: through_hole_cylinder,
                12: countersink_hole_cylinder,
                13: counterbore_hole_cylinder,
                14: chamfer, 
                15: fillet}


def display_features(path, centers, features):
    """Open a viewer and colour each face by its feature id (random colours)."""
    max_features = max(features)
    feature_color = {}
    for index in range(0, max_features+1):
        feature_color[index] = (random.uniform(0,1), random.uniform(0,1), random.uniform(0,1))

    display, start_display, add_menu, add_function_to_menu = init_display()
    my_shape = load_step(path)
    #display.DisplayShape(my_shape, update=True)
    index = 0
    for center in centers:
        closest_face = find_closest_face(my_shape, gp_Pnt(center[0], center[1], center[2]))
        apply_color(display, closest_face, feature_color[features[index]])
        index += 1

    start_display()


def display_part_labels(path, centers, label):
    """Open a viewer and colour each face by its manufacturing-technology label."""
    display, start_display, add_menu, add_function_to_menu = init_display()
    my_shape = load_step(path)
    #display.DisplayShape(my_shape, update=True)
    index = 0
    for center in centers:
        closest_face = find_closest_face(my_shape, gp_Pnt(center[0], center[1], center[2]))
        if label[index] == 1:
            apply_color(display, closest_face, (0.0, 0.4, 0.0))  #green 1
        elif label[index] == 2:
            apply_color(display, closest_face, (1.0, 0.0, 0.0))  #red 1
        elif label[index] == 3:
            apply_color(display, closest_face, (0.0, 0.0, 0.8))  #blue 1
        elif label[index] == 4:
            apply_color(display, closest_face, (0.0, 0.4, 0.0))  #green 1
        elif label[index] == 5:
            apply_color(display, closest_face, (1.0, 0.0, 0.0))   #red 1 
        elif label[index] == 6:
            apply_color(display, closest_face, (0.3, 0.0, 0.8))   #purple
        elif label[index] == 7:
            apply_color(display, closest_face, (1.0, 1.0, 0.0))   #yellow
        elif label[index] == 8:
            apply_color(display, closest_face, (1.0, 0.2, 0.0))   #orange
        elif label[index] == 9:
            apply_color(display, closest_face, (0.0, 0.4, 0.8))   #light blue
        else:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #darkgrey

        #apply_number(display, closest_face, index+2)

        index += 1

    start_display()


def display_part(path, centers, label):
    """Open a viewer and render the whole part in a single neutral grey colour."""
    display, start_display, add_menu, add_function_to_menu = init_display()
    my_shape = load_step(path)
    #display.DisplayShape(my_shape, update=True)
    index = 0
    for center in centers:
        closest_face = find_closest_face(my_shape, gp_Pnt(center[0], center[1], center[2]))
        if label[index] == 1:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #grey
        elif label[index] == 2:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #grey
        elif label[index] == 3:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #grey
        elif label[index] == 4:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #grey
        elif label[index] == 5:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))  #grey
        elif label[index] == 6:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))   #grey
        elif label[index] == 7:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))   #grey
        elif label[index] == 8:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))   #grey
        elif label[index] == 9:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))   #grey
        else:
            apply_color(display, closest_face, (0.2, 0.2, 0.2))   #grey

        #apply_number(display, closest_face, index+2)

        index += 1

    start_display()



def create_shape(path, shape_1, segmentation_dict, features_dict, stock, combo, ID, include_stock, display=False):
    """Build one labelled part and write it (and its graph) to disk.

    Parameters
    ----------
    path : str
        Dataset root; sub-folders STEP/Label/Feature/PMI/Graph are written here.
    shape_1 : cadquery.Workplane
        The starting stock body (already created as a cylinder or cuboid).
    segmentation_dict, features_dict : dict
        Per-face bookkeeping (face -> technology label, face -> feature id);
        seeded with the stock faces and updated as features are applied.
    stock : str
        Either ``'cylinder'`` or ``'cuboid'``; selects ``cyl_feat``/``poly_feat``.
    combo : list[int]
        Ordered feature ids to machine into the stock, one after another.
    ID : int
        Unique part identifier, used as the output file stem.
    include_stock : bool
        If False, plain stock faces are stripped from the labels before saving.
    display : bool
        If True, open the pythonOCC viewers after generation for inspection.

    Returns
    -------
    None
        The part is exported as STEP plus Label/Feature/PMI spreadsheets and an
        AAG graph; nothing is returned.
    """
    save = True
    number_of_feature = 1
    if stock == 'cylinder':
        if 1 in combo:
            for feat_num in combo:
                if feat_num == 1:
                    shape_2, selector = cyl_feat[feat_num](shape_1)
                    segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=1, feature_dict=features_dict, feature_num=number_of_feature)
                    segmentation_dict, features_dict = updateCuboidBossCylinderBegin(shape_2, segmentation_dict, features_dict)
                    shape_1 = shape_2
                    number_of_feature += 1
                elif feat_num >= 2 and feat_num <= 6:
                    shape_2, add_face = cyl_feat[feat_num](shape_1, selector)
                    if feat_num == 6:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)

                    else:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=1, feature_dict=features_dict, feature_num=number_of_feature)
                    shape_1 = shape_2
                    number_of_feature += 1
                elif feat_num >= 7 and feat_num <= 13:
                    solid = shape_1.val() 
                    bb = solid.BoundingBox()
                    bbx = round_near_zero(abs(bb.xmax-bb.xmin))
                    bby = round_near_zero(abs(bb.ymax-bb.ymin))
                    bbz = round_near_zero(abs(bb.zmax-bb.zmin))
                    shape_2 = poly_feat[feat_num](shape_1, bbx, bby, bbz, segmentation_dict)
                  
                    if feat_num == 10 or feat_num == 11 or feat_num == 12 or feat_num == 13:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=3, feature_dict=features_dict, feature_num=number_of_feature)
                    else:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)
                    shape_1 = shape_2
                    number_of_feature += 1
                else:
                    pass
                    # shape_2 = cyl_feat[feat_num](shape_1, segmentation_dict)
                    # segmentation_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2)
                    # shape_1 = shape_2

            segmentation_dict, features_dict = updateCuboidBossCylinderEnd(shape_2, segmentation_dict, features_dict, selector)
        else:
            for feat_num in combo:
                if feat_num >= 2 and feat_num <= 13:
                    shape_2, add_face = cyl_feat[feat_num](shape_1, segmentation_dict)

                    if feat_num == 10 or feat_num == 11 or feat_num == 12 or feat_num == 13:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=3, feature_dict=features_dict, feature_num=number_of_feature)
                    elif feat_num == 9 or feat_num == 8 or feat_num == 7 or feat_num == 6:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)
                    else:
                        segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=1, feature_dict=features_dict, feature_num=number_of_feature)

                    #segmentation_dict, features_dict = correct_stock_faces_cyl(shape_2, segmentation_dict, features_dict)
                    shape_1 = shape_2
                    number_of_feature += 1
                else:
                    shape_2 = cyl_feat[feat_num](shape_1, segmentation_dict)
                    segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=1, feature_dict=features_dict, feature_num=number_of_feature)
                    shape_1 = shape_2
                    number_of_feature += 1

    else:
        for feat_num in combo:
            if feat_num == 1 or feat_num == 2:
                solid = shape_1.val() 
                bb = solid.BoundingBox()
                bbx = round_near_zero(abs(bb.xmax-bb.xmin))
                bby = round_near_zero(abs(bb.ymax-bb.ymin))
                bbz = round_near_zero(abs(bb.zmax-bb.zmin))
                shape_2, selected_face = poly_feat[feat_num](shape_1, bbx, bby, bbz, segmentation_dict)
                segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)
                shape_1 = shape_2
                number_of_feature += 1
            elif feat_num == 14 or feat_num == 15:
                shape_2 = poly_feat[feat_num](shape_1, segmentation_dict)
                segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)
                shape_1 = shape_2
                number_of_feature += 1
            else:
                solid = shape_1.val() 
                bb = solid.BoundingBox()
                bbx = round_near_zero(abs(bb.xmax-bb.xmin))
                bby = round_near_zero(abs(bb.ymax-bb.ymin))
                bbz = round_near_zero(abs(bb.zmax-bb.zmin))
                shape_2 = poly_feat[feat_num](shape_1, bbx, bby, bbz, segmentation_dict)
                if feat_num == 10 or feat_num == 11 or feat_num == 12 or feat_num == 13:
                    segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=3, feature_dict=features_dict, feature_num=number_of_feature)
                else:
                    segmentation_dict, features_dict = updateLabels(shape_1, shape_2, segmentation_dict, technology=2, feature_dict=features_dict, feature_num=number_of_feature)
                shape_1 = shape_2
                number_of_feature += 1

    shape_2, segmentation_dict, features_dict = rotation(shape_2, segmentation_dict, features_dict)
    face_centers = {}
    for face, class_ind in segmentation_dict.items():
        face_centers[face] = [round_near_zero(face.Center().x), round_near_zero(face.Center().y), round_near_zero(face.Center().z)]

    if include_stock == False:
        segmentation_dict = remove_stock_labels(segmentation_dict, stock, combo)

    PMI   = pd.DataFrame()
    PMI, LABEL, FEATURE, display = addPMIToShape(segmentation_dict, PMI, face_centers, shape_2, features_dict, display)
    #print(PMI.head(100))



    if save == True:
        step_filename = f"{path}/STEP/{ID}.step"
        label_filename = f"{path}/Label/{ID}.xlsx"
        feature_filename = f"{path}/Feature/{ID}.xlsx"
        pmi_filename = f"{path}/PMI/{ID}.xlsx"
        cq.exporters.export(shape_2, step_filename, exportType="STEP")
        PMI.to_excel(pmi_filename, index=False)
        LABEL.to_excel(label_filename, index=False)
        FEATURE.to_excel(feature_filename, index=False)
        graph_folder = f"{path}/Graph/"
        convert_step(path, graph_folder, str(ID), display)

    if display == True:
        centers = LABEL['Face Center'].tolist()
        label_list = LABEL['Label'].tolist()
        feature_list = FEATURE['Feature'].tolist()
        display_part_labels(step_filename, centers, label_list)
        display_part(step_filename, centers, label_list)
        display_features(step_filename, centers, feature_list)











