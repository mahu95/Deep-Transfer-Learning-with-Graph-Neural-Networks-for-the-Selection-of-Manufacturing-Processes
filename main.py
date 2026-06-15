"""Entry point for generating the synthetic machining-feature dataset.

Running this module produces labelled CAD parts: for each part id it picks a
random stock (cylinder or cuboid), randomly assembles a list of machining
features (``combo``), and hands everything to :func:`ShapeCreator.create_shape`,
which machines the features, labels the faces, and exports the geometry, the
label/PMI spreadsheets and the face-adjacency graph.

Adjust the ``range`` in :func:`start_program` to control how many parts are
generated, and ``max_tries`` below to control how many times the whole run is
retried if an exception is raised.
"""
import cadquery as cq
import random
import numpy as np
import os

from utils.Label import updateLabelsStock

from ShapeCreator import create_shape

import time


def start_program():
    """Generate the configured range of parts and write them under ``data/``.

    For each id it chooses a random stock body, builds a randomised but
    rule-constrained list of features, and calls
    :func:`ShapeCreator.create_shape` to machine, label and export the part.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    path = path.replace('\\', '/')

    max_number_features = 10
    min_number_features = 6

    for id in range(1, 2):
        # if os.path.exists(path + '/Graph/' + str(id) + '.json'):
        #     print("Path already exists: " + str(id))
        # else:
            stock_volume = ['cylinder', 'cuboid']
            stock = random.choice(stock_volume)
            segmentation_dict = {}
            features_dict = {}

            if stock == 'cylinder':
                random_height = np.random.randint(5,20)
                random_radius = np.random.randint(5,20)
                shape = cq.Workplane("XY").cylinder(height=random_height, radius=random_radius)
                segmentation_dict, features_dict = updateLabelsStock(shape, segmentation_dict, features_dict)
            elif stock == 'cuboid':
                random_length = np.random.randint(10, 100)
                random_width = np.random.randint(10, 100)
                random_height = np.random.randint(10, 100)
                shape = cq.Workplane("XY").box(random_length, random_width, random_height)
                segmentation_dict, features_dict = updateLabelsStock(shape, segmentation_dict, features_dict)


            combo = []
            number_features = np.random.randint(min_number_features, max_number_features)
            if stock == 'cylinder':
                for _ in range(0, number_features):
                    if 1 in combo:
                        feat_number = np.random.randint(2,15)
                    else:
                        feat_number = np.random.randint(2,15) 
                    combo.append(feat_number)
                combo.sort()
            else:
                for _ in range(0, number_features):
                    feat_number = np.random.randint(2,15)
                    combo.append(feat_number)
                combo.sort()


            if 10 in combo or 11 in combo or 12 in combo or 13 in combo:
                    pass
            else:
                    for _ in range(0,2):
                        hole_number = np.random.randint(10,13)
                        combo.append(hole_number)
                    combo.sort()

            # remove chamfer and fillet from Turn-Mill-Part because of untrackable manufacturing technology for the feature
            if stock == 'cylinder' and 1 in combo:
                combo = [x for x in combo if x != 14]
                combo = [x for x in combo if x != 15]

             
            create_shape(path, shape, segmentation_dict, features_dict, stock, combo, id, include_stock=False, display=True)


if __name__ == '__main__':

    max_tries = 1 # Define the number of reruns

    for attempt in range(max_tries):
        try:
            start_program()
            print("Program started!.")
        except Exception as e:
            print(f"Error occurred on attempt {attempt + 1}/{max_tries}: {e}")
            if attempt < max_tries - 1:
                print("Rerunning the program...")
                time.sleep(5)  # Optional: wait for a second before rerunning
            else:
                print("Max retries reached. Exiting program.")