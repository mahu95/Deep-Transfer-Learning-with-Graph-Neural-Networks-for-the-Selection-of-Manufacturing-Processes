"""Generate Product and Manufacturing Information (PMI) for a part.

Real-world manufacturing decisions depend not only on geometry but on tolerances
and surface-finish requirements. This module synthesises a plausible set of PMI
annotations for a labelled part:

* a random workpiece material,
* *direct* PMI on individual faces (surface finish, dimensional tolerance,
  flatness, cylindricity, circularity, straightness), and
* *datum-referenced* geometric tolerances (parallelism, perpendicularity,
  position, angularity, runout) linking a datum face to one or more reference
  faces.

Crucially, the chosen PMI values *feed back* into the segmentation labels: a
tight tolerance or fine surface finish upgrades a face's manufacturing
technology to a finishing/grinding class (e.g. rough milling -> finish milling
or milling & grinding), with the exact thresholds depending on the material.
The result is returned as three DataFrames (PMI, labels, features).

For further reference see also:
[47]	Swift KG, Booker JD. Manufacturing Process Selection Handbook. Elsevier; 2013.
[48]	Sormaz D, Gouveia R, Sarkar A. RULE BASED PROCESS SELECTION OF MILLING PROCESSES BASED ON GD&T REQUIREMENTS. Journal of Production Engineering 2018;21(2):19–26. https://doi.org/10.24867/JPE-2018-02-019.
[49]	Grzesik W, Kruszynski B, Ruszaj A. Surface Integrity of Machined Surfaces. In: Davim JP, editor. Surface Integrity in Machining. London: Springer London; 2010, p. 143–179.
[50]	Oberg E, Jones F, Horton H, Ryffel Henry. Machinery Handbook. 27th ed. New York: Industrial Press Inc; 2004.
[51]	Sormaz DN, Khurana P, Wadatkar A. Rule-Based Process Selection of Hole Making Operations for Integrated Process Planning. In: Volume 3: 25th Computers and Information in Engineering Conference, Parts A and B. ASMEDC; 2005, p. 983–988.

"""
import numpy as np
import random
import pandas as pd
import cadquery as cq

def setMaterialForShape():
    """Return a random material id in 1..10 for the whole part."""
    material = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    return material

def is_point_inside_compound(compound, point, tolerance=1e-7):
    """Return True if ``point`` lies inside any solid of ``compound``.

    Used to distinguish internal cylindrical/conical faces (bores) from external
    ones when deciding which geometric tolerances apply.
    """
    for solid in compound.Solids():
        if isinstance(solid, cq.occ_impl.shapes.Solid):
            if solid.isInside(point, tolerance):
                return True
    return False


def addPMIToShape(segmentation_dict, PMI_df, face_center_dict, shape, features_dict, display):
    """Attach synthetic PMI to a part and refine its labels accordingly.

    Builds the PMI table (material, direct face tolerances and datum-referenced
    geometric tolerances), and upgrades face labels in ``segmentation_dict`` to
    finishing/grinding classes wherever the sampled tolerances demand a tighter
    process. Profile-of-a-surface and profile-of-a-line callouts are not modelled.

    Returns
    -------
    (PMI_df, Labels_df, Features_df, display)
        The populated PMI DataFrame, a face-centre/label DataFrame, a
        face-centre/feature DataFrame, and the (possibly updated) ``display`` flag.
    """
    # not considered here Profile of a Surface, Profile of a Line
    material = setMaterialForShape()

    faces_list = []
    centers = []
    materials = []
    for face, Label in segmentation_dict.items():
        center_coor = face_center_dict[face]
        centers.append(center_coor)
        materials.append(material)
        if Label != 0:
            faces_list.append(face)

    PMI_df['Face Centers'] = centers
    PMI_df['Material'] = material

    categories = ['Surface Finish Value', 'Dimensional Tolerance Value', 'Flatness Value', 'Cylindricity Value', 'Circularity Value', 'Straightness Value', 
                  'Datum', 'Perpendicularity Reference', 'Perpendicularity Value', 'Parallelism Reference', 'Parallelism Value', 'Angularity Reference', 'Angularity Value', 
                  'Position Reference', 'Position Value', 'Circular Runout Reference', 'Circular Runout Value', 'Total Runout Reference', 'Total Runout Value']
    
    for category in categories:
        PMI_df[category] = None

    possible_PMI_category_cylinder = ['Surface Finish Value', 'Dimensional Tolerance Value', 'Cylindricity Value', 'Circularity Value']
    possible_PMI_category_flat     = ['Surface Finish Value', 'Dimensional Tolerance Value', 'Flatness Value', 'Straightness Value']
    maxNumberDatums = int((len(faces_list)/5))
    if maxNumberDatums == 0:
        maxNumberDatums = 1

    numberDatums = np.random.randint(1, maxNumberDatums)
    print("Datum PMI: " + str(numberDatums))
    try:
        numberDirectPMI = np.random.randint(0, len(faces_list)-(2*numberDatums))
        #numberDirectPMI = np.random.randint(0, 2) # Zeile entfernen und andere auskommentieren!
    except:
        numberDirectPMI = 1
    print("Direct PMI: " + str(numberDirectPMI))
    for ind in range(0, numberDirectPMI):
        if ind == 0:
            cylinder_face = False
            while cylinder_face == False:
                face = random.choice(faces_list)
                if face.geomType() == 'CYLINDER':
                    cylinder_face = True
        else:
            face = random.choice(faces_list)


        faces_list.remove(face)
        bb = face.BoundingBox()
        bbx = abs(bb.xmax-bb.xmin)
        bby = abs(bb.ymax-bb.ymin)
        if face.geomType() == 'CYLINDER' or face.geomType() == 'CONE': 
            pmi_category = random.choice(possible_PMI_category_cylinder)
        elif face.geomType() == 'PLANE' and bbx != bby: 
            pmi_category = random.choice(possible_PMI_category_flat)
        else:
            #print(face.geomType())
            #display = True
            break

        if pmi_category == 'Surface Finish Value':
            pmi_value = np.random.randint(0, 14)
        elif pmi_category == 'Dimensional Tolerance Value':
            pmi_value = np.random.randint(0, 14)
        elif pmi_category == 'Flatness Value':
            pmi_value = np.random.randint(0, 14)
        elif pmi_category == 'Straightness Value':
            pmi_value = np.random.randint(0, 14)
        elif pmi_category == 'Circularity Value':
            pmi_value = np.random.randint(0, 14)
        elif pmi_category == 'Cylindricity Value':
            pmi_value = np.random.randint(0, 14)

        center_coor = face_center_dict[face]
        for index, row in PMI_df.iterrows():
            if row['Face Centers'] == center_coor: 
                PMI_df.loc[index, pmi_category] = pmi_value 
                break
        
        technology = segmentation_dict[face]
        if technology == 1:
            if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                if pmi_category == 'Surface Finish Value' and pmi_value <= 6:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Surface Finish Value' and pmi_value > 6 and pmi_value <= 9:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 7:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value > 7 and pmi_value <= 10:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Circularity Value' and pmi_value <= 5:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Circularity Value' and pmi_value > 5 and pmi_value <= 8:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Cylindricity Value' and pmi_value <= 4:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Cylindricity Value' and pmi_value > 4 and pmi_value <= 7:	
                    segmentation_dict[face] = technology + 3

            else:

                if pmi_category == 'Surface Finish Value' and pmi_value <= 6+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Surface Finish Value' and pmi_value > 6+1 and pmi_value <= 9+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 7+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value > 7+1 and pmi_value <= 10+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Circularity Value' and pmi_value <= 5+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Circularity Value' and pmi_value > 5+1 and pmi_value <= 8+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Cylindricity Value' and pmi_value <= 4+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Cylindricity Value' and pmi_value > 4+1 and pmi_value <= 7+1:	
                    segmentation_dict[face] = technology + 3

        elif technology == 2:
            if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                if pmi_category == 'Surface Finish Value' and pmi_value <= 7:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Surface Finish Value' and pmi_value > 7 and pmi_value <= 10:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 9:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value > 9 and pmi_value <= 12:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Flatness Value' and pmi_value <= 6:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Flatness Value' and pmi_value > 6 and pmi_value <= 9:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Straightness Value' and pmi_value <= 5:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Straightness Value' and pmi_value > 5 and pmi_value <= 8:
                    segmentation_dict[face] = technology + 3

            else:
                if pmi_category == 'Surface Finish Value' and pmi_value <= 7+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Surface Finish Value' and pmi_value > 7+1 and pmi_value <= 10+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 9+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Dimensional Tolerance Value' and pmi_value > 9+1 and pmi_value <= 12+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Flatness Value' and pmi_value <= 6+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Flatness Value' and pmi_value > 6+1 and pmi_value <= 9+1:
                    segmentation_dict[face] = technology + 3

                elif pmi_category == 'Straightness Value' and pmi_value <= 5+1:
                    segmentation_dict[face] = technology + 6
                elif pmi_category == 'Straightness Value' and pmi_value > 5+1 and pmi_value <= 8+1:
                    segmentation_dict[face] = technology + 3
                
        elif technology == 3: 
            if face.geomType() == 'CYLINDER': 
                if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                    if pmi_category == 'Surface Finish Value' and pmi_value <= 5:  
                        segmentation_dict[face] = technology + 6
                    if pmi_category == 'Surface Finish Value' and pmi_value > 5 and pmi_value <= 8:  
                        segmentation_dict[face] = technology + 3

                    elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 11 and pmi_value > 6:
                        segmentation_dict[face] = technology + 3
                    elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 6:
                        segmentation_dict[face] = technology + 6

                    elif pmi_category == 'Circularity Value' and pmi_value <= 6:
                        segmentation_dict[face] = technology + 3
                    elif pmi_category == 'Cylindricity Value' and pmi_value <= 7:
                        segmentation_dict[face] = technology + 3    
                else:
                    if pmi_category == 'Surface Finish Value' and pmi_value <= 5+1:  
                        segmentation_dict[face] = technology + 6
                    if pmi_category == 'Surface Finish Value' and pmi_value > 5+1 and pmi_value <= 8+1:  
                        segmentation_dict[face] = technology + 3

                    elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 11+1 and pmi_value > 6+1:
                        segmentation_dict[face] = technology + 6
                    elif pmi_category == 'Dimensional Tolerance Value' and pmi_value <= 6+1:
                        segmentation_dict[face] = technology + 3

                    elif pmi_category == 'Circularity Value' and pmi_value <= 6+1:
                        segmentation_dict[face] = technology + 3
                    elif pmi_category == 'Cylindricity Value' and pmi_value <= 7+1:
                        segmentation_dict[face] = technology + 3  

            else:
                PMI_df.loc[index, pmi_category] = None



  
    Datums = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for index1 in range(numberDatums, 0, -1):
        faceDatum = random.choice(faces_list)
        faces_list.remove(faceDatum)
        DatumValue = Datums[numberDatums-index1]
        center_coor = face_center_dict[faceDatum]
        for index, row in PMI_df.iterrows():
            if row['Face Centers'] == center_coor: 
                PMI_df.loc[index, 'Datum'] = DatumValue
                break

        if len(faces_list)-3*index1 >= 0:
            numberReferenceFaces = np.random.randint(1, 3)
        else:
            numberReferenceFaces = 1
        
        ReferenceFace = None
        for _ in range(0, numberReferenceFaces):
            if faceDatum.geomType() == 'CYLINDER' and is_point_inside_compound(shape.val(), faceDatum.Center()):
                for potentialReference in faces_list:   
                    if potentialReference.geomType() == 'CYLINDER' and is_point_inside_compound(shape.val(), potentialReference.Center()): 
                        ReferenceFace = potentialReference
                        faces_list.remove(ReferenceFace)
                        pmi_category = random.choice(['Circular Runout', 'Total Runout'])
                        if pmi_category == 'Circular Runout':
                            pmi_category_1, pmi_category_2 = 'Circular Runout Reference', 'Circular Runout Value'
                        elif pmi_category == 'Total Runout':
                            pmi_category_1, pmi_category_2 = 'Total Runout Reference', 'Total Runout Value'

                    elif potentialReference.geomType() == 'CONE' and is_point_inside_compound(shape.val(), potentialReference.Center()):
                        ReferenceFace = potentialReference
                        faces_list.remove(ReferenceFace)
                        pmi_category_1, pmi_category_2 = 'Angularity Reference', 'Angularity Value'
                        break

                if ReferenceFace is None:
                    ReferenceFace = random.choice(faces_list)
                    faces_list.remove(ReferenceFace)
                    if faceDatum.normalAt() == ReferenceFace.normalAt():
                        pmi_category_1, pmi_category_2 = 'Parallelism Reference', 'Parallelism Value'
                    elif faceDatum.normalAt().dot(ReferenceFace.normalAt()) == 0:
                        pmi_category_1, pmi_category_2 = 'Perpendicularity Reference', 'Perpendicularity Value'
                    else:
                        pmi_category_1, pmi_category_2 = 'Position Reference', 'Position Value'


            elif faceDatum.geomType() == 'CONE' and is_point_inside_compound(shape.val(), faceDatum.Center()):
                for potentialReference in faces_list:
                    if potentialReference.geomType() == 'CYLINDER' and is_point_inside_compound(shape.val(), potentialReference.Center()):
                        ReferenceFace = potentialReference
                        faces_list.remove(ReferenceFace)
                        pmi_category_1, pmi_category_2 = 'Angularity Reference', 'Angularity Value'
                        break

                if ReferenceFace is None:
                    ReferenceFace = random.choice(faces_list)
                    faces_list.remove(ReferenceFace)
                    if faceDatum.normalAt() == ReferenceFace.normalAt():
                        pmi_category_1, pmi_category_2 = 'Parallelism Reference', 'Parallelism Value'
                    elif faceDatum.normalAt().dot(ReferenceFace.normalAt()) == 0:
                        pmi_category_1, pmi_category_2 = 'Perpendicularity Reference', 'Perpendicularity Value'
                    else:
                        pmi_category_1, pmi_category_2 = 'Position Reference', 'Position Value'


            else:
                ReferenceFace = random.choice(faces_list)
                faces_list.remove(ReferenceFace)
                if faceDatum.normalAt() == ReferenceFace.normalAt():
                    pmi_category_1, pmi_category_2 = 'Parallelism Reference', 'Parallelism Value'
                elif faceDatum.normalAt().dot(ReferenceFace.normalAt()) == 0:
                    pmi_category_1, pmi_category_2 = 'Perpendicularity Reference', 'Perpendicularity Value'
                else:
                    pmi_category_1, pmi_category_2 = 'Position Reference', 'Position Value'



            center_coor = face_center_dict[ReferenceFace]
            for index, row in PMI_df.iterrows():
                if row['Face Centers'] == center_coor: 
                    pmi_value = np.random.randint(0,14)
                    PMI_df.loc[index, pmi_category_1] = DatumValue
                    PMI_df.loc[index, pmi_category_2] = pmi_value
                    technology = segmentation_dict[ReferenceFace]

                    if technology == 1:
                        if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 6:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 7:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <=6:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 7:	
                                segmentation_dict[ReferenceFace] = technology + 3

                        else:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 6+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 7+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <= 6+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 7:	
                                segmentation_dict[ReferenceFace] = technology + 3


                    elif technology == 2:
                        if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 7:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 8:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <= 7:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 8:	
                                segmentation_dict[ReferenceFace] = technology + 3

                        else:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 7+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 8+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <= 7+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 7:	
                                segmentation_dict[ReferenceFace] = technology + 3
                
                    elif technology == 3: 
                        if material == 1 or material == 3 or material == 5 or material == 7 or material == 9:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 8:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 9:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <= 8:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 8:	
                                segmentation_dict[ReferenceFace] = technology + 3

                        else:
                            if pmi_category_2 == 'Position Value' and pmi_value <= 8+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Perpendicularity Value' and pmi_value <= 9+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_category_2 == 'Parallelism Value' and pmi_value <= 8+1:
                                segmentation_dict[ReferenceFace] = technology + 3

                            elif pmi_value <= 8:	
                                segmentation_dict[ReferenceFace] = technology + 3

                    break

    
    center_list = []
    label_list = []
    feature_list = []
    for face, Label in segmentation_dict.items():
        center_list.append(face_center_dict[face])
        label_list.append(Label)
        feature_list.append(features_dict[face])

    Labels_df = pd.DataFrame()
    Labels_df['Face Center'] = center_list
    Labels_df['Label'] = label_list

    Features_df = pd.DataFrame()
    Features_df['Face Center'] = center_list
    Features_df['Feature'] = feature_list

    return PMI_df, Labels_df, Features_df, display

