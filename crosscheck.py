# -*- coding: utf-8 -*-
"""Dataset consistency checker.

For every part in a generated dataset this script verifies that the STEP
geometry, the label spreadsheet, the PMI spreadsheet and the AAG graph are
mutually consistent: the file stems match, the STEP body is a valid, manifold,
closed ``TopoDS_Solid`` (via :class:`~utils.topologyCheker.TopologyChecker`),
and the number of faces agrees across the geometry, the labels, the PMI and the
graph. Inconsistent parts are collected and, after confirmation, deleted.

Run it with::

    python crosscheck.py --dataset path/to/data

Attribution
-----------
The validation approach (and the bundled ``TopologyChecker``) follows AAGNet:
    https://github.com/whjdark/AAGNet
"""
import pathlib
import argparse
import json
import os
from tqdm import tqdm

from OCC.Core.TopoDS import TopoDS_Solid
from OCC.Core.STEPControl import STEPControl_Reader

from utils.occ_utils import list_face

import pandas as pd

from utils.topologyCheker import TopologyChecker
import torch



def load_body_from_step(step_file):
    """
    Load the body from the step file.  
    We expect only one body in each file
    """
    assert pathlib.Path(step_file).suffix in ['.step', '.stp']
    reader = STEPControl_Reader()
    reader.ReadFile(str(step_file))
    reader.TransferRoots()
    shape = reader.OneShape()
    return shape


def load_json(pathname):
    """Read and return the JSON object stored at ``pathname``."""
    with open(pathname, "r") as fp:
        return json.load(fp)


def get_filenames(path, suffix):
    """Return a sorted list of files under ``path`` matching the glob ``suffix``."""
    path = pathlib.Path(path)
    files = list(
        x for x in path.rglob(suffix)
    )
    files.sort()
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="Path to load the dataset from")
    args = parser.parse_args()
    # load dataset
    aag_path = os.path.join(args.dataset, 'Graph')
    step_path = os.path.join(args.dataset, 'STEP')
    labels_path = os.path.join(args.dataset, 'Label')
    pmi_path = os.path.join(args.dataset, 'PMI')

    step_files = get_filenames(step_path, f"*.st*p")
    labels_files = get_filenames(labels_path, '*.xlsx')
    pmi_files = get_filenames(pmi_path, '*.xlsx')
    graph_files = get_filenames(aag_path, '*.json')

    
    wrong_files = []
    # loop over step_file, label
    topochecker = TopologyChecker()
    for step_file, labels_file, graph_file, pmi_file in tqdm(
        zip(step_files, labels_files, graph_files, pmi_files), total=len(step_files)):
        # check file name
        fn = step_file.stem
        assert fn == labels_file.stem, f'{step_file.stem}, {labels_file.stem}, {graph_file.stem}, {pmi_file.stem},'
        assert fn == graph_file.stem, f'{step_file.stem}, {labels_file.stem}, {graph_file.stem}, {pmi_file.stem},'
        assert fn == pmi_file.stem, f'{step_file.stem}, {labels_file.stem}, {graph_file.stem}, {pmi_file.stem},'
        # load step, label, pmi
        try:
            shape = load_body_from_step(step_file)
        except Exception as e:
            print('file', fn)
            print(e)
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue
        try: 
            label_data = pd.read_excel(labels_file)
        except Exception as e:
            print('file', fn)
            print(e)
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue
        try: 
            pmi_data = pd.read_excel(pmi_file)
        except Exception as e:
            print('file', fn)
            print(e)
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue
        # check shape is TopoDS_Solid
        if not isinstance(shape, TopoDS_Solid):
            print('{} is {}, not supported'.format(fn, type(shape)))
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue
        # check shape topology
        if not topochecker(shape):
            print("{} has wrong topology".format(fn))
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue

        # check number of faces
        faces_list = list_face(shape)
        num_faces = len(faces_list)
        # check length of label
        length_labels = label_data['Face Center'].count()
        # check length of label
        length_pmi = pmi_data['Face Centers'].count()
        # check length of graph
        with open(graph_file, 'r') as json_file:
            data_graph = json.load(json_file)
        face_attr = data_graph['Geom Face Attributes']
        face_attr = torch.tensor(face_attr, dtype=torch.float32)
        length_graph = face_attr.size(0)
        # check map between face id and label
        if num_faces != length_labels or num_faces != length_pmi or num_faces != length_graph:
            print('File {} have wrong number of labels step faces. '.format(fn))
            wrong_files.append((step_file, labels_file, graph_file, pmi_file))
            continue



    if len(wrong_files):
        print('delete following wrong files:')
        print(wrong_files)
        inputs = input('[Y/N]: ')
        if (inputs == 'Y') or (inputs == 'y'):
            for wrong_file in wrong_files:
                graph_f, label_f, step_f, pmi_f = wrong_file
                os.remove(graph_f)
                os.remove(label_f)
                os.remove(step_f)
                os.remove(pmi_f)
                print(step_f ,label_f, graph_f, pmi_f, 'deleted')





    print('Finished')