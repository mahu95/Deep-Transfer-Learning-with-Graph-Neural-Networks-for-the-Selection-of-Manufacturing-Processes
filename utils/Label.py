"""Per-face labelling: track which manufacturing technology produced each face.

As each machining feature is applied, faces are created, split or left
untouched. This module maintains two dictionaries keyed by face:

* the *segmentation* dict -- maps a face to a manufacturing-technology class id
  (see :data:`Label_Technology_dict`), and
* the *feature* dict -- maps a face to the running feature instance number.

It does so by matching faces before and after each feature operation (exact and
partial vertex/normal matches), propagating old labels onto surviving faces and
assigning the new technology/feature id to freshly created faces. A few helpers
fix up special cases (cylinder stock faces, cuboid-boss-on-cylinder) and convert
left-over stock faces into their final class.
"""
import cadquery as cq

from utils.round_near_zero import round_near_zero

Label_Technology_dict = {0 : "Stock",
                         1 : "Rough Turning",
                         2 : "Rough Milling",
                         3 : "Drilling",
                         4 : "Finish Turning",
                         5 : "Finish Milling", 
                         6 : "Drilling & Reaming",
                         7 : "Turning & Grinding",
                         8 : "Milling & Grinding",
                         9 : "Drilling & Grinding",}


def get_segmentation_labels(new_generated_faces, fmap, old_seg_map, technology, first=False):
    """Build the label map for a part after a feature operation.

    Faces carried over from the previous shape inherit their old label (via
    ``fmap``), while newly created faces are assigned ``technology``. When
    ``first`` is True every face is treated as new (used to seed the stock).
    """
    new_seg_map = {}
    if first == True:
        for face in new_generated_faces:
            new_seg_map[face] = technology
    else:
        for old_face, new_faces in fmap.items():
            for new_face in new_faces:
                class_ind = old_seg_map[old_face]
                new_seg_map[new_face] = class_ind

        for face in new_generated_faces:
            new_seg_map[face] = technology

    return new_seg_map






def map_faces_before_and_after_feat(old_shape, new_shape, add=None):
    """Match faces of ``old_shape`` to ``new_shape`` across a feature operation.

    Returns ``(fmap, new_faces)`` where ``fmap`` maps each surviving old face to
    the new face(s) it became (exact and partial vertex/normal matches) and
    ``new_faces`` is the list of genuinely new faces created by the feature.
    ``add`` lets a matched old face be reclassified as newly generated.
    """
    fmap_exact = {}
    fmap_partial = {}
    old_faces = old_shape.faces().vals()
    new_faces = new_shape.faces().vals()

    for old_face in old_faces:
        for new_face in new_faces:
            exact_match = find_exact_matches(old_face, new_face)
            if exact_match == True:
                fmap_exact[old_face] = new_face
                old_faces.remove(old_face)
                new_faces.remove(new_face)

    for old_face in old_faces:
        fmap_partial[old_face] = []
        for new_face in new_faces:
            partial_match = find_partial_matches(old_face, new_face)
            if partial_match == True:
                fmap_partial[old_face].append(new_face)

    for _, new_faces_list in fmap_partial.items():
        for face in new_faces_list:
            if face in new_faces:
                new_faces.remove(face)

    for old_face, new_face in fmap_exact.items():
            fmap_partial[old_face] = [new_face]

    if add:
        for face in add:
            new_selected_face = fmap_partial[face]
            del fmap_partial[face]
            new_faces.append(new_selected_face[0])

    return fmap_partial, new_faces


def find_exact_matches(face1, face2):
    """Return True if the two faces share all vertices and the same normal."""
    vertices1 = {v.toTuple() for v in face1.Vertices()}
    vertices2 = {v.toTuple() for v in face2.Vertices()}
    exact_match = vertices1 == vertices2 and face1.normalAt() == face2.normalAt()
    return exact_match


def find_partial_matches(face1, face2):
    """Return True if the faces share at least one vertex and the same normal."""
    vertices1 = {v.toTuple() for v in face1.Vertices()}
    vertices2 = {v.toTuple() for v in face2.Vertices()}
    partial_match = not vertices1.isdisjoint(vertices2) and face1.normalAt() == face2.normalAt()
    return partial_match



def updateLabels(shape_old, shape_new, segmentation_dict, technology, feature_dict, feature_num, add=None):
    """Update both the segmentation and feature dicts after one feature step.

    Returns the updated ``(segmentation_dict, feature_dict)`` with new faces
    labelled by ``technology`` and ``feature_num`` respectively.
    """
    f_map, rest = map_faces_before_and_after_feat(shape_old, shape_new, add)
    segmentation_dict = get_segmentation_labels(rest, f_map, segmentation_dict, technology)
    feature_dict = get_segmentation_labels(rest, f_map, feature_dict, feature_num)
    return segmentation_dict, feature_dict



def updateLabelsStock(shape_new, segmentation_dict, features_dict):
    """Seed the label dicts for a fresh stock body (every face is class 0)."""
    faces = shape_new.faces().vals()
    segmentation_dict = get_segmentation_labels(faces, None, segmentation_dict, 0, True)
    features_dict = get_segmentation_labels(faces, None, features_dict, 0, True)
    return segmentation_dict, features_dict


def correct_stock_faces_cyl(shape, seg_dict, feat_dict):
    """Relabel the outer barrel and end faces of a cylinder stock back to stock."""
    solid = shape.val()
    bbs = solid.BoundingBox()
    bbxs = round_near_zero(abs(bbs.xmax-bbs.xmin))
    bbys = round_near_zero(abs(bbs.ymax-bbs.ymin))
    max_dim_s = max(bbxs, bbys)

    faces = shape.faces().vals()
    for face in faces:
        bb = face.BoundingBox()
        bbx = round_near_zero(abs(bb.xmax-bb.xmin))
        bby = round_near_zero(abs(bb.ymax-bb.ymin))
        bbz = round_near_zero(abs(bb.zmax-bb.zmin))
        if bby == max_dim_s or bbx == max_dim_s:
            if bbz != 0.0:
                if round_near_zero(face.normalAt().z, 0.1) == 0:
                    seg_dict[face] = 0
                    feat_dict[face] = 0
        
    faces = shape.faces(">Z").vals()
    for face in faces:
        seg_dict[face] = 0
        feat_dict[face] = 0

    faces = shape.faces("<Z").vals()
    for face in faces:
        seg_dict[face] = 0
        feat_dict[face] = 0

    return seg_dict, feat_dict



def updateCuboidBossCylinderBegin(shape, seg_dict, feat_dict):
    """Swap stock/feature labels when a cuboid boss starts a cylinder part.

    For the special case where a cuboid boss is the first feature on cylinder
    stock, this flips the boss and stock labels and tags the boss side faces.
    """
    for face, value in seg_dict.items():
        if value == 1:
                seg_dict[face] = 0
                feat_dict[face] = 0
        elif value == 0:
                seg_dict[face] = 1
                feat_dict[face] = 1

    faces = shape.faces().vals()
    for face in faces:
        bb = face.BoundingBox()
        bbz = round_near_zero(abs(bb.zmax-bb.zmin), 0.1)
        if bbz == 0.0:
            seg_dict[face] = 1
            feat_dict[face] = 1


    return seg_dict, feat_dict


def updateCuboidBossCylinderEnd(shape, seg_dict, feat_dict, selector):
    """Relabel the selected end face of the cuboid-boss-on-cylinder back to stock."""
    for index in [">Z", "<Z"]:
        if index == selector:
            faces = shape.faces(index).vals()
            for face in faces:
                seg_dict[face] = 0
                feat_dict[face] = 0

    return seg_dict, feat_dict


def remove_stock_labels(segmentation_dict, stock, combo):
    """Convert remaining raw-stock faces (class 0) to their final finish class.

    Depending on the stock type and feature combo, leftover stock faces become
    turning (1) or milling (2) finished surfaces, so no face keeps the temporary
    stock label in the exported dataset.
    """
    if stock == 'cylinder' and 1 in combo:
        for key, value in segmentation_dict.items():
            if value == 0:
                segmentation_dict[key] = 2
    elif stock == 'cylinder' and 1 not in combo:
        for key, value in segmentation_dict.items():
            if value == 0:
                segmentation_dict[key] = 1
    else:
        for key, value in segmentation_dict.items():
            if value == 0:
                segmentation_dict[key] = 2

    return segmentation_dict