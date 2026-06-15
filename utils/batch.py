"""Flatten per-face mesh data into a single batched mesh.

The graph pipeline meshes each face separately, producing per-face node
coordinates and connectivity. :func:`batch_mesh` concatenates all faces into one
big mesh, re-indexing the connectivity so node ids stay unique across faces, and
records which face each node came from (the ``batch`` vector) -- the same idea
as PyTorch-Geometric mini-batching.
"""


def batch_mesh(mesh_coor_dict, mesh_conn_dict):
        """Concatenate per-face meshes into one mesh with global node indices.

        Returns
        -------
        batched_mesh_coor : list
            All face node coordinates concatenated in face order.
        batched_mesh_conn : list[list[int]]
            Edge connectivity (``[start_nodes, end_nodes]``) with node indices
            offset so they refer into ``batched_mesh_coor``.
        batch : list
            For each node, the id of the face it belongs to.
        """
        batched_mesh_coor = []
        batched_mesh_conn = [[], []]
        batch = []  
        
        current_node_index = 0

        for face_id in mesh_coor_dict.keys():
            mesh_coor = mesh_coor_dict[face_id]
            batched_mesh_coor.extend(mesh_coor)
        
            mesh_conn = mesh_conn_dict[face_id]
            adjusted_start_nodes = [start + current_node_index for start in mesh_conn[0]]
            adjusted_end_nodes = [end + current_node_index for end in mesh_conn[1]]

            batched_mesh_conn[0].extend(adjusted_start_nodes)
            batched_mesh_conn[1].extend(adjusted_end_nodes)

            batch.extend([face_id] * len(mesh_coor))

            current_node_index += len(mesh_coor)

        # print(batched_mesh_coor)
        # print("##############################")
        # print(batched_mesh_conn)
        # print("##############################")
        # print(batch)

        return batched_mesh_coor, batched_mesh_conn, batch