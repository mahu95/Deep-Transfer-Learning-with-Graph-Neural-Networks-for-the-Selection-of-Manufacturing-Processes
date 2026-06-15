# Deep Transfer Learning with Graph Neural Networks for the Selection of Manufacturing Processes

Synthetic 3D CAD model generation with **face-level manufacturing-process annotations** for graph-based deep learning.

This repository generates a labelled dataset of procedurally created mechanical parts. For every part it produces the solid geometry, a set of synthetic **PMI** (Product and Manufacturing Information) annotations, a per-face **manufacturing-technology label**, and an **attributed graph** suitable for training Graph Neural Networks (GNNs) for machining-feature recognition and manufacturing-process selection.

> 📄 **This code accompanies a research paper. If you use it, please [cite the paper](#citation).**

---

## What it produces

For each generated part with id `N`, the pipeline writes five artefacts under the dataset root (`data/`):

| Folder | File | Contents |
|---|---|---|
| `STEP/` | `N.step` | The B-rep solid geometry (STEP / ISO 10303). |
| `Label/` | `N.xlsx` | Per-face manufacturing-technology label (the segmentation target). |
| `Feature/` | `N.xlsx` | Per-face machining-feature instance id. |
| `PMI/` | `N.xlsx` | Per-face PMI: material, tolerances, surface finish, datums, GD&T. |
| `Graph/` | `N.json` | The attributed graph (AAG + PMI graph + per-face mesh). |

Faces are matched across all modalities by their **centre coordinates**, so the labels, PMI and graph all refer to the same faces.

---

## How it works

The dataset is built by progressively *machining* features into a random stock body and tracking, face by face, how each surface was produced.

```
main.py
  └─ pick random stock (cylinder | cuboid) and a random, rule-constrained
     list of feature ids ("combo")
       └─ ShapeCreator.create_shape(...)
            ├─ apply each feature in turn         (Features/*.py)
            ├─ track per-face labels + features   (utils/Label.py)
            ├─ random rotation augmentation       (utils/Augmentation.py)
            ├─ synthesise PMI and refine labels   (utils/PMI.py)
            ├─ export STEP + Label/Feature/PMI xlsx
            └─ build the attributed graph         (graph_utils/Step_Conversion.py)
```

Crucially, the **PMI feeds back into the labels**: a tight tolerance or fine surface-finish callout upgrades a face's manufacturing technology to a finishing or grinding class (see `utils/PMI.py`). The rules linking PMI (tolerances, surface finish, GD&T) to suitable manufacturing processes are based on the engineering literature listed under [References](#references), together with interviews with experts from the field.

### The graph (`Graph/N.json`)

Each part is encoded as three graphs. Two of them share the **same set of face nodes**, where every face of the part is one node:

* **AAG (Attributed Adjacency Graph)**, faces are nodes, shared B-rep edges are graph edges. Nodes carry geometric face attributes (surface type, centroid, normal, area, …) and edges carry geometric attributes plus **edge convexity** (convex, concave, smooth).
* **PMI graph**, the same face nodes connected by PMI relationships (datum and reference links), with PMI node and edge attributes.

* **Mesh graph**, a graph in exactly the same sense as the other two, but on a **different hierarchy level**. Instead of one graph for the whole part, there is one mesh graph **per face**, whose nodes are the triangulation vertices (with coordinates and normals) and whose edges are the triangle edges. Because there are many such per-face graphs for a single part, they are **batched** into one disjoint graph (the `Mesh Batch Information` records which face each node belongs to), the same way mini-batches of graphs are handled in PyTorch Geometric.

The JSON keys are:

```
Geom Face Attributes      Geom Edge Attributes      Geom Face Adj. Matrix
PMI Face Attributes       PMI Connections           PMI Edge Attributes
Mesh Coordinates          Mesh Connections          Mesh Batch Information
```

---

## Manufacturing-technology labels

The per-face segmentation target (`Label/N.xlsx`), defined in `utils/Label.py`:

| Id | Technology | | Id | Technology |
|---|---|---|---|---|
| 0 | Stock (temporary; removed before export) | | 5 | Finish Milling |
| 1 | Rough Turning | | 6 | Drilling & Reaming |
| 2 | Rough Milling | | 7 | Turning & Grinding |
| 3 | Drilling | | 8 | Milling & Grinding |
| 4 | Finish Turning | | 9 | Drilling & Grinding |

> **Note, label granularity.** The labels produced here are **finer-grained** than in the associated published paper. In the paper the *rough* and *fine* variants of a process are merged into a single class for prediction, whereas here they are kept as distinct, more fine-grained process classes (e.g. *Rough Turning* vs *Finish Turning*, *Rough Milling* vs *Finish Milling*). This follows the recommendations in the references, for example [[48]](#references), which distinguish processes at this finer level based on the GD&T and surface-finish requirements.

---

## Machining-feature catalogue

Features are applied per stock type. `Features/` contains a generator per feature; `ShapeCreator.py` maps feature ids to them via `poly_feat` (prismatic / cuboid stock) and `cyl_feat` (rotational / cylinder stock). The catalogue includes bosses, steps, slots, pockets, through/blind holes, counterbore/countersink holes, passages, grooves, tapers, belts, chamfers and fillets.

---

## Repository layout

```
main.py                  Entry point: generate the dataset
ShapeCreator.py          Assemble stock + features into one labelled part
checkfilenames.py        Keep the dataset sub-folders in sync by file stem
crosscheck.py            Validate geometry/labels/PMI/graph consistency (deletes bad parts)

Features/                One machining-feature generator per file (CadQuery)
graph_utils/             STEP → attributed-graph conversion
  Step_Conversion.py       Top-level graph builder
  Face_Edge_Indexes.py     Index faces / edges / solids
  Vexity_Adjacency.py      Edge convexity + face-adjacency (COO) matrix
  Face_Attr.py             Per-face geometric attributes
  Edge_Attr.py             Per-edge geometric attributes
  Mesh.py                  Per-face triangulation
  PMI_Graph.py             PMI node/edge attributes and connections
  Scaler.py                Bounding-box coordinate normalisation
utils/
  Label.py                 Per-face label tracking across feature operations
  PMI.py                   Synthetic PMI generation + label refinement
  Augmentation.py          Random rotation augmentation
  steputils.py             STEP loading + viewer helpers
  topologyCheker.py        B-rep validity checks (see Attribution)
  occ_utils.py, batch.py, plane_direction.py, round_near_zero.py
data/                    Example output (one part across all five modalities)
```

---

## Installation

The pipeline relies on the OpenCASCADE-based CAD stack. A conda environment is recommended because of `pythonocc-core`:

```bash
conda create -n mfg-gnn python=3.10
conda activate mfg-gnn
conda install -c conda-forge pythonocc-core=7.7.0
pip install cadquery numpy pandas openpyxl torch networkx matplotlib tqdm pyparsing
```

> Tested with Python 3.10. `pythonocc-core` and `cadquery` must share a compatible OpenCASCADE version.

---

## Usage

### 1. Generate parts

Set the number of parts via the `range` in `start_program()` and run:

```bash
python main.py
```

Output is written to a `data/` folder next to the scripts (the path is resolved relative to the script location). Set `display=True` in the `create_shape(...)` call to open the pythonOCC viewers and inspect a part, its labels and its graph.

### 2. Validate the dataset

```bash
python crosscheck.py --dataset data
```

Checks that, for every part, the STEP body is a valid/manifold/closed solid and that the face counts agree across the geometry, labels, PMI and graph. Inconsistent parts are listed and, on confirmation, deleted.

### 3. Re-sync folders

If a modality is missing for some parts, drop the orphans so every remaining part exists in all folders:

```bash
python checkfilenames.py
```

---

## Citation

This code accompanies a research paper. **If you use this code or the generated dataset in your work, please cite the paper.**

Currently available as a preprint on SSRN:

> Hussong, Marco; Simon, Peter; Wagner, Marcel; Kloft, Marius; Aurich, Jan C. *Deep Transfer Learning with Graph Neural Networks for the Selection of Manufacturing Processes* (April 02, 2026). Available at SSRN: <https://ssrn.com/abstract=6509299>

```bibtex
@misc{hussong2026deeptransfer,
  title        = {Deep Transfer Learning with Graph Neural Networks for the Selection of Manufacturing Processes},
  author       = {Hussong, Marco and Simon, Peter and Wagner, Marcel and Kloft, Marius and Aurich, Jan C.},
  year         = {2026},
  month        = apr,
  note         = {Preprint, available at SSRN},
  howpublished = {\url{https://ssrn.com/abstract=6509299}}
}
```

> **Note:** Once the article is published in a peer-reviewed journal, please cite the journal version instead. This section will be updated with the final reference.

---

## Attribution

The B-rep topology validation in [`utils/topologyCheker.py`](utils/topologyCheker.py) is taken from the **AAGNet** project, which itself adapted it from **BRepNet**:

* AAGNet, <https://github.com/whjdark/AAGNet> (`dataset/topologyCheker.py`)
* BRepNet, <https://github.com/AutodeskAILab/BRepNet> (`pipeline/extract_brepnet_data_from_step.py`)

The attributed-adjacency-graph representation and the dataset consistency-checking approach in `crosscheck.py` follow the same line of work.

> Zhang et al., *AAGNet: A graph neural network towards multi-task machining feature recognition*, Journal of Manufacturing Systems, 2024.

---

## References

The rules used to relate PMI (tolerances, surface finish, GD&T) to manufacturing processes, implemented in [`utils/PMI.py`](utils/PMI.py), were derived from the following sources together with interviews with experts from the field:

- **[47]** Swift KG, Booker JD. *Manufacturing Process Selection Handbook*. Elsevier; 2013.
- **[48]** Sormaz D, Gouveia R, Sarkar A. *Rule Based Process Selection of Milling Processes Based on GD&T Requirements*. Journal of Production Engineering 2018;21(2):19–26. <https://doi.org/10.24867/JPE-2018-02-019>.
- **[49]** Grzesik W, Kruszynski B, Ruszaj A. *Surface Integrity of Machined Surfaces*. In: Davim JP, editor. Surface Integrity in Machining. London: Springer London; 2010, p. 143–179.
- **[50]** Oberg E, Jones F, Horton H, Ryffel H. *Machinery's Handbook*. 27th ed. New York: Industrial Press Inc; 2004.
- **[51]** Sormaz DN, Khurana P, Wadatkar A. *Rule-Based Process Selection of Hole Making Operations for Integrated Process Planning*. In: Volume 3: 25th Computers and Information in Engineering Conference, Parts A and B. ASMEDC; 2005, p. 983–988.

---

## License

Released under the **Apache License 2.0**, see [LICENSE](LICENSE).
