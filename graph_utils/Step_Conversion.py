"""Turn a saved STEP part into the JSON graph consumed by the GNN.

:func:`convert_step` is the top-level graph builder. For one part it reads the
STEP geometry plus the label/PMI spreadsheets and assembles an attributed graph
with two parallel structures over the same set of face nodes:

* the **AAG** (attributed adjacency graph) -- faces are nodes connected by their
  shared B-rep edges, with geometric face and edge attribute vectors, and
* the **PMI graph** -- the same face nodes connected by PMI relationships
  (datum/reference links), with PMI face and edge attributes.

It also attaches a batched surface mesh per face. The whole thing is serialised
to ``<targetdir>/<filename>.json``. When ``visualize`` is True it additionally
renders the part and both graphs with pythonOCC / matplotlib for inspection.
"""
from turtle import color
from networkx import center
from pyparsing import col
from graph_utils.Edge_Attr         import create_edge_attr_matrix
from graph_utils.Face_Attr         import create_face_attr_matrix
from graph_utils.Face_Edge_Indexes import create_face_edge_index
from graph_utils.Vexity_Adjacency  import vexity_adjacency_algo
from graph_utils.PMI_Graph         import create_pmi_attr_matrix
from graph_utils.Scaler            import get_bounding_box_val, get_ratio_to_scale_largest_dim, scale_dict_val

from utils.batch import batch_mesh

import torch
import os
import json
import ast
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

import torch
import os
import json
import pandas as pd
from OCC.Display.SimpleGui import init_display

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import  AIS_ColoredShape

import logging
logging.getLogger("matplotlib").setLevel(logging.ERROR)

import numpy as np, networkx as nx, matplotlib.pyplot as plt
from matplotlib.collections import LineCollection






def convert_step(sourcedir, targetdir, filename, visualize):
    """Build and save the attributed graph (AAG + PMI) for one STEP part.

    Parameters
    ----------
    sourcedir : str
        Dataset root containing ``STEP/``, ``PMI/`` and ``Label/`` sub-folders.
    targetdir : str
        Folder to write ``<filename>.json`` into (created if missing).
    filename : str
        Part id / file stem (without extension).
    visualize : bool
        If True, render the part and the AAG/PMI graphs before saving.

    The output JSON contains the geometric face/edge attributes and adjacency,
    the PMI face/edge attributes and connections, and the batched face mesh.
    """
    print("Converting " + filename)
    reader = STEPControl_Reader()
    tr = reader.WS().TransferReader()
    reader.ReadFile(sourcedir + '/STEP/' + filename + '.step')
    reader.TransferRoots()
    model = reader.StepModel()
    shape = reader.OneShape()

    bbx_val = get_bounding_box_val(shape)
    ratios  = get_ratio_to_scale_largest_dim(bbx_val)


    pmi = pd.read_excel(sourcedir + '/PMI/' + filename + '.xlsx')
    labels = pd.read_excel(sourcedir + '/Label/' + filename + '.xlsx')

    centers = labels['Face Center'].to_list()
    centers = [ast.literal_eval(item) for item in centers]

    if visualize==True:
        display, start_display, _, _ = init_display(size=(1200, 960))
        display.SetSelectionModeVertex()
    else:
        display = None

    mesh = BRepMesh_IncrementalMesh(shape, 0.1)

    faces_dic, edges_dic, faces_edges, solids = create_face_edge_index(shape, tr, model, display, centers)
    geom_face_adj_matrix, dic_index_ID_face, dic_index_ID_edge, vex_dic = vexity_adjacency_algo(faces_edges, faces_dic, edges_dic, solids, display)
    geom_edge_attr_dic = create_edge_attr_matrix(edges_dic, vex_dic, solids, bbx_val, ratios, display)
    geom_face_attr_dic, face_mesh_coor_dic, face_mesh_conn_dic = create_face_attr_matrix(faces_dic, mesh, solids, bbx_val, ratios, display)
    pmi_face_attr_dic, pmi_face_connections, pmi_edge_attr_dic = create_pmi_attr_matrix(pmi, centers, display)

    if visualize==True:
        ais_shape = AIS_ColoredShape(shape)
        color_obj = Quantity_Color(0.3, 0.3, 0.3, Quantity_TOC_RGB)
        ais_shape.SetColor(color_obj)
        #display.Context.Display(ais_shape, True)
        #display.DisplayShape(shape, update=True)
        start_display()

    # for key, values in pmi_face_attr_dic.items():
    #     print(len(values))

    #geom_edge_attr_dic = scale_dict_val(geom_edge_attr_dic, -1)
    #geom_face_attr_dic = scale_dict_val(geom_face_attr_dic, -1)
    #geom_face_attr_dic = scale_dict_val(geom_face_attr_dic, -2)


    geom_edge_attr_list = []
    for index in dic_index_ID_edge.keys():
        geom_edge_attr_list.append(geom_edge_attr_dic[dic_index_ID_edge[index]])

    pmi_edge_attr_list = []
    for index in pmi_edge_attr_dic.keys():
        pmi_edge_attr_list.append(pmi_edge_attr_dic[index])
        

    geom_face_attr_list = []
    pmi_face_attr_list = []
    index = 0
    while index < len(dic_index_ID_face):
        for face_id, value in dic_index_ID_face.items():
            if value == index:
                geom_face_attr_list.append(geom_face_attr_dic[face_id])
                pmi_face_attr_list.append(pmi_face_attr_dic[face_id])


        index += 1


    geom_face_adj_matrix = torch.tensor(geom_face_adj_matrix)
    geom_face_adj_matrix = geom_face_adj_matrix.tolist()

    face_mesh_coor, face_mesh_conn, face_mesh_batch = batch_mesh(face_mesh_coor_dic, face_mesh_conn_dic)

    print(geom_face_adj_matrix)
    print(pmi_face_connections)

    if visualize == True:
        plt.close('all')
        AAG = nx.Graph()
        num_nodes = len(geom_face_attr_list)
        AAG.add_nodes_from(range(num_nodes))

        starts_AAG = np.asarray(geom_face_adj_matrix[0]).ravel()
        ends_AAG   = np.asarray(geom_face_adj_matrix[1]).ravel()

        edges_AAG = [(int(u), int(v)) for u, v in zip(starts_AAG, ends_AAG)]
        AAG.add_edges_from(edges_AAG)

        fig_1, ax_1 = plt.subplots(figsize=(16, 9))
        pos = nx.spring_layout(AAG, center=(0,0), k=1)
        xy = np.array([pos[n] for n in AAG.nodes()], dtype=float)

        # --- Build edge segments for a LineCollection (same transform=ax.transData) ---
        segments = np.array([ [pos[u], pos[v]] for u, v in AAG.edges() ], dtype=float)
        edge_coll = LineCollection(segments, linewidths=2.0, alpha=0.9, antialiased=True, color='black')
        edge_coll.set_transform(ax_1.transData)   # <— enforce same data transform

        ax_1.add_collection(edge_coll)

        # --- Nodes (PathCollection) shares ax.transData by default ---
        ax_1.scatter(xy[:, 0], xy[:, 1], s=350, zorder=3, color='blue')

        # --- Labels (optional) ---
        for n, (x, y) in pos.items():
            ax_1.text(x, y, str(n), fontsize=10, ha='center', va='center', zorder=4, color='white')

        # --- Tight bounds from data to avoid stale limits ---
        xmin = min(xy[:,0].min(), segments[:,:,0].min())
        xmax = max(xy[:,0].max(), segments[:,:,0].max())
        ymin = min(xy[:,1].min(), segments[:,:,1].min())
        ymax = max(xy[:,1].max(), segments[:,:,1].max())
        padx = 0.05 * (xmax - xmin if xmax > xmin else 1.0)
        pady = 0.05 * (ymax - ymin if ymax > ymin else 1.0)

        ax_1.set_xlim(xmin - padx, xmax + padx)
        ax_1.set_ylim(ymin - pady, ymax + pady)
        ax_1.set_aspect('equal', adjustable='box')
        ax_1.axis('off')

        plt.tight_layout()
        plt.show()

        PMI_GRAPH = nx.Graph()
        PMI_GRAPH.add_nodes_from(range(num_nodes))

        starts_PMI = np.asarray(pmi_face_connections[0]).ravel()
        ends_PMI   = np.asarray(pmi_face_connections[1]).ravel()

        edges_PMI = [(int(u), int(v)) for u, v in zip(starts_PMI, ends_PMI)]
        PMI_GRAPH.add_edges_from(edges_PMI)

        fig_2, ax_2 = plt.subplots(figsize=(16, 9))

        # --- Build edge segments for a LineCollection (same transform=ax.transData) ---
        segments = np.array([ [pos[u], pos[v]] for u, v in PMI_GRAPH.edges() ], dtype=float)
        edge_coll = LineCollection(segments, linewidths=2.0, alpha=0.9, antialiased=True, color='black')
        edge_coll.set_transform(ax_2.transData)   # <— enforce same data transform

        ax_2.add_collection(edge_coll)

        # --- Nodes (PathCollection) shares ax.transData by default ---
        ax_2.scatter(xy[:, 0], xy[:, 1], s=350, zorder=3, color='green')

        # --- Labels (optional) ---
        for n, (x, y) in pos.items():
            ax_2.text(x, y, str(n), fontsize=10, ha='center', va='center', zorder=4, color='white')

        # --- Tight bounds from data to avoid stale limits ---
        xmin = min(xy[:,0].min(), segments[:,:,0].min())
        xmax = max(xy[:,0].max(), segments[:,:,0].max())
        ymin = min(xy[:,1].min(), segments[:,:,1].min())
        ymax = max(xy[:,1].max(), segments[:,:,1].max())
        padx = 0.05 * (xmax - xmin if xmax > xmin else 1.0)
        pady = 0.05 * (ymax - ymin if ymax > ymin else 1.0)

        ax_2.set_xlim(xmin - padx, xmax + padx)
        ax_2.set_ylim(ymin - pady, ymax + pady)
        ax_2.set_aspect('equal', adjustable='box')
        ax_2.axis('off')

        plt.tight_layout()
        plt.show()




    json_dump_dict = {}
    json_dump_dict['Geom Face Attributes']  = geom_face_attr_list
    json_dump_dict['Geom Edge Attributes']  = geom_edge_attr_list
    json_dump_dict['Geom Face Adj. Matrix'] = geom_face_adj_matrix

    json_dump_dict['PMI Face Attributes'] = pmi_face_attr_list
    json_dump_dict['PMI Connections']     = pmi_face_connections
    json_dump_dict['PMI Edge Attributes'] = pmi_edge_attr_list
    
    json_dump_dict['Mesh Coordinates']       = face_mesh_coor
    json_dump_dict['Mesh Connections']       = face_mesh_conn
    json_dump_dict['Mesh Batch Information'] = face_mesh_batch

    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    target_file_path = targetdir + '/' + filename + '.json'
    with open(target_file_path, 'w') as json_file:
        json.dump(json_dump_dict, json_file, indent=1)


