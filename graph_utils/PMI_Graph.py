"""Turn the PMI spreadsheet into the PMI graph layer.

The PMI graph shares its face nodes with the AAG but uses a different set of
edges. This module produces, over the same node ordering as the geometry graph:

* per-face *direct* PMI node attributes (material plus surface-finish and form
  tolerances), and
* *datum-referenced* edges connecting each datum face to the faces that cite it
  (perpendicularity, parallelism, angularity, position, runout), each carrying
  the corresponding tolerance values as edge attributes.
"""
import ast
import pandas as pd

def create_pmi_attr_matrix(pmi_df, centers, display):
    """Build PMI node attributes, connections and edge attributes for a part.

    Parameters
    ----------
    pmi_df : pandas.DataFrame
        The part's PMI table (as written by :mod:`utils.PMI`).
    centers : list
        Face-centre coordinates in node order; used to align PMI rows to nodes.

    Returns
    -------
    (pmi_node_attr_dic, pmi_connections, pmi_edge_attr_dic)
        Node id -> direct-PMI vector, the datum/reference edge list in COO form,
        and edge index -> geometric-tolerance value vector.
    """
    pmi_node_attr_dic = {}
    pmi_connections = [[], []]
    pmi_edge_attr_dic = {}
    pmi_df = pmi_df.fillna(0.0)

    direct_pmi_df = pmi_df[['Face Centers', 'Material', 'Surface Finish Value', 'Dimensional Tolerance Value', 'Flatness Value', 'Cylindricity Value', 'Circularity Value', 'Straightness Value']]
    for index in range(0, len(centers)):
        center = centers[index]
        for _, row in direct_pmi_df.iterrows():
            compare_center = ast.literal_eval(row['Face Centers'])
            if compare_center == center: 
                row_to_add = row.to_list()[1:]
                pmi_node_attr_dic[index] = row_to_add
                break

    indirect_pmi_df = pmi_df[['Face Centers', 'Datum', 'Perpendicularity Reference', 'Perpendicularity Value', 'Parallelism Reference', 'Parallelism Value', 'Angularity Reference', 'Angularity Value', 
                                'Position Reference', 'Position Value', 'Circular Runout Reference', 'Circular Runout Value', 'Total Runout Reference', 'Total Runout Value']].copy()
    indirect_pmi_df.loc[:, 'Index'] = 0

    for index2, row in indirect_pmi_df.iterrows():
        compare_center = ast.literal_eval(row['Face Centers'])
        for index1 in range(0, len(centers)):
            center = centers[index1]
            if compare_center == center: 
                indirect_pmi_df.at[index2, 'Index'] = index1
                break

    datum_rows = indirect_pmi_df[indirect_pmi_df['Datum'] != 0.0]
    #pd.set_option('display.max_columns', None)
    #print(indirect_pmi_df.drop('Face Centers', axis=1))
    index0 = 0
    for index1, row1 in datum_rows.iterrows():
        datum = row1['Datum']
        for index2, row2 in indirect_pmi_df.iterrows():
            if datum == row2['Perpendicularity Reference']: 
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1
            elif datum == row2['Parallelism Reference']:
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1
            elif datum == row2['Angularity Reference']:
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1
            elif datum == row2['Position Reference']:
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1
            elif datum == row2['Circular Runout Reference']:
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1
            elif datum == row2['Total Runout Reference']:
                pmi_connections[0].append(row1['Index'])
                pmi_connections[1].append(row2['Index'])
                values = row2[['Perpendicularity Value', 'Parallelism Value', 'Angularity Value', 'Position Value', 'Circular Runout Value', 'Total Runout Value']]
                pmi_edge_attr_dic[index0] = values.to_list()
                index0 += 1

    #print(pmi_node_attr_dic)
    #print(pmi_connections)
    #print(pmi_edge_attr_dic)
        
    return pmi_node_attr_dic, pmi_connections, pmi_edge_attr_dic