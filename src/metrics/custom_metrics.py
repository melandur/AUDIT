from collections import Counter

import numpy as np
from numpy import logical_and as l_and
from numpy import logical_not as l_not
from scipy.spatial.distance import directed_hausdorff

HAUS = "haus"
DICE = "dice"
SENS = "sens"
SPEC = "spec"
ACCU = "accu"
JACC = "jacc"
PREC = "prec"
SIZE = "size"
METRICS = [HAUS, DICE, SENS, SPEC, ACCU, JACC, PREC, SIZE]


# TODO: check whether it'd be nice to create a common class called Metric and heritage from it to the rest of metrics.
#  Check how PyMIA was built
def one_hot_encoding(segmentation, labels, skip_background=True):
    """
    Perform one-hot encoding on a segmentation map.

    Parameters:
    - segmentation (np.ndarray): Input segmentation map.
    - labels (list): List of labels to be encoded.
    - skip_background (bool): Flag to skip encoding for the background label (default=True).

    Returns:
    - one_hot_enc (np.ndarray): One-hot encoded segmentation map.
    """

    # initialize list of binary segmentations
    binary_images = []

    for i in labels:
        if skip_background and i == 0:
            continue

        if not isinstance(i, list):
            binary_image = np.where(segmentation == i, 1, 0)
        else:
            binary_image = np.where(np.isin(segmentation, i), 1, 0)
        binary_images.append(binary_image)

    one_hot_enc = np.stack(binary_images)

    return one_hot_enc


def calculate_confusion_matrix_elements(gt, seg):
    """
    Calculate the elements tp, tn, fp, and fn for segmentation evaluation.

    Parameters:
    - gt (np.ndarray): Ground truth segmentation map.
    - seg (np.ndarray): Segmented mask.

    Returns:
    - tp (float): True positives.
    - tn (float): True negatives.
    - fp (float): False positives.
    - fn (float): False negatives.
    """
    #  cardinalities metrics tp, tn, fp, fn
    tp = float(np.sum(l_and(seg, gt)))
    tn = float(np.sum(l_and(l_not(seg), l_not(gt))))
    fp = float(np.sum(l_and(seg, l_not(gt))))
    fn = float(np.sum(l_and(l_not(seg), gt)))

    return tp, tn, fp, fn


def calculate_metrics(
    ground_truth: np.ndarray,
    segmentation: np.ndarray,
    patient: str,
    regions: list,
    skip_background=True,
    spacing: np.array = np.array([1, 1, 1]),
) -> list:
    """
     Calculate evaluation metrics (Jaccard index, Accuracy, Hausdorff, DICE score, Sensitivity, Specificity, and
     Precision) for a segmentation compared to its ground truth.

     Parameters:
     - ground_truth (np.ndarray): Ground truth segmentation data. (R*Z*Y*X)
     - segmentation (np.ndarray): Predicted segmentation data. (R*Z*Y*X)
     - patient (str): Identifier for the patient.
     - regions (list): List of regions to evaluate.
     - skip_background (bool): Flag to skip background region (default=True).

     Returns:
     - metrics_list (list): List of dictionaries containing metrics for each region {metric:value}.
     """
    assert segmentation.shape == ground_truth.shape, "Predicted segmentation and ground truth do not have the same size"

    if skip_background and "BKG" in regions:
        regions.remove("BKG")

    metrics_list = []
    for n, r in enumerate(regions):

        metrics = dict(ID=patient, region=r)

        # Ground truth and segmentation for i-th region
        gt = ground_truth[n]
        seg = segmentation[n]

        #  cardinalities metrics tp, tn, fp, fn
        tp, tn, fp, fn = calculate_confusion_matrix_elements(gt, seg)

        # Computing all metrics
        metrics[HAUS] = hausdorff_distance(gt, seg)
        metrics[DICE] = dice_score(tp, fp, fn, gt, seg)
        metrics[SENS] = sensitivity(tp, fn)
        metrics[SPEC] = specificity(tn, fp)
        metrics[ACCU] = accuracy(tp, tn, fp, fn)
        metrics[JACC] = jaccard_index(tp, fp, fn, gt, seg)
        metrics[PREC] = precision(tp, fp)
        metrics[SIZE] = Counter(seg.flatten()).get(1, np.nan) * spacing.prod()

        metrics_list.append(metrics)

    return metrics_list


def sensitivity(tp: float, fn: float) -> float:
    """
    The sensitivity is intuitively the ability of the classifier to find all tumor voxels.
    """

    if tp == 0:
        sens = np.nan
    else:
        sens = tp / (tp + fn)

    return sens


def specificity(tn: float, fp: float) -> float:
    """
    The specificity is intuitively the ability of the classifier to find all non-tumor voxels.
    """

    spec = tn / (tn + fp)

    return spec


def precision(tp: float, fp: float) -> float:
    """
    Calculates the precision score.

    Parameters:
    - tp (float): Number of true positives.
    - fp (float): Number of false positives.

    Returns:
    - prec (float): Precision score.
    """
    if tp == 0:
        prec = np.nan
    else:
        prec = tp / (tp + fp)

    return prec


def accuracy(tp: float, tn: float, fp: float, fn: float) -> float:
    """
    Calculates the accuracy score.

    Parameters:
    - tp (float): Number of true positives.
    - tn (float): Number of true negatives.
    - fp (float): Number of false positives.
    - fn (float): Number of false negatives.

    Returns:
    - accu (float): Accuracy score.
    """
    accu = (tp + tn) / (tp + tn + fp + fn)

    return accu


def dice_score(tp: float, fp: float, fn: float, gt: np.ndarray, seg: np.ndarray) -> float:
    """
    Computes the Dice coefficient.

    Parameters:
    - tp (float): Number of true positives.
    - fp (float): Number of false positives.
    - fn (float): Number of false negatives.
    - gt (np.ndarray): Ground truth segmentation mask.
    - seg (np.ndarray): Segmented mask.

    Returns:
    - dice (float): Dice coefficient.
    """
    if np.sum(gt) == 0:
        dice = 1 if np.sum(seg) == 0 else 0
    else:
        dice = 2 * tp / (2 * tp + fp + fn)

    return dice


def jaccard_index(tp: float, fp: float, fn: float, gt: np.ndarray, seg: np.ndarray) -> float:
    """
    Computes the Jaccard index.

    Parameters:
    - tp (float): Number of true positives.
    - fp (float): Number of false positives.
    - fn (float): Number of false negatives.
    - gt (np.ndarray): Ground truth segmentation mask.
    - seg (np.ndarray): Segmented mask.

    Returns:
    - jac (float): Jaccard index.
    """
    if np.sum(gt) == 0:
        jac = 1 if np.sum(seg) == 0 else 0
    else:
        jac = tp / (tp + fp + fn)

    return jac


def hausdorff_distance(gt: np.ndarray, seg: np.ndarray) -> float:
    """
    Computes the Hausdorff distance.

    Parameters:
    - gt (np.ndarray): Ground truth segmentation mask.
    - seg (np.ndarray): Segmented mask.

    Returns:
    - hd (float): Hausdorff distance.
    """
    if np.sum(gt) == 0:
        hd = np.nan
    else:
        hd = directed_hausdorff(np.argwhere(seg), np.argwhere(gt))[0]

    return hd
