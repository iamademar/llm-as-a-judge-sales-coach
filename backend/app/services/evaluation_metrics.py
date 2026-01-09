"""
Evaluation metrics for scorer calibration.

This module implements metrics for comparing model predictions
against ground truth labels:
- Pearson correlation coefficient (r)
- Quadratic Weighted Kappa (QWK)
- ±1 band accuracy
"""

from typing import Sequence
import math


def _validate_arrays(y_true: Sequence[float], y_pred: Sequence[float]) -> None:
    """Validate that input arrays are non-empty and same length"""
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Arrays must contain at least one element")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Arrays must be same length: {len(y_true)} vs {len(y_pred)}")


def pearson_r(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """
    Calculate Pearson correlation coefficient between predictions and ground truth.

    Pearson r measures linear correlation between two variables.
    Returns a value between -1 and 1 where:
    - 1.0 = perfect positive correlation
    - 0.0 = no correlation
    - -1.0 = perfect negative correlation

    Args:
        y_true: Ground truth values
        y_pred: Predicted values

    Returns:
        Pearson correlation coefficient

    Raises:
        ValueError: If arrays are empty, different lengths, or have zero variance

    Examples:
        >>> pearson_r([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        1.0
        >>> pearson_r([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])
        -1.0
    """
    _validate_arrays(y_true, y_pred)

    n = len(y_true)

    # Handle single element case
    if n == 1:
        return 0.0

    # Calculate means
    mean_true = sum(y_true) / n
    mean_pred = sum(y_pred) / n

    # Calculate deviations
    dev_true = [y - mean_true for y in y_true]
    dev_pred = [y - mean_pred for y in y_pred]

    # Calculate covariance and standard deviations
    covariance = sum(dt * dp for dt, dp in zip(dev_true, dev_pred))
    var_true = sum(dt * dt for dt in dev_true)
    var_pred = sum(dp * dp for dp in dev_pred)

    # Handle zero variance case (constant array)
    if var_true == 0.0 or var_pred == 0.0:
        return 0.0

    # Calculate Pearson r
    std_true = math.sqrt(var_true)
    std_pred = math.sqrt(var_pred)

    return covariance / (std_true * std_pred)


def quadratic_weighted_kappa(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """
    Calculate Quadratic Weighted Kappa (QWK) between predictions and ground truth.

    QWK measures agreement between raters with quadratic weighting,
    penalizing larger disagreements more heavily. Commonly used for
    ordinal classification problems like scoring rubrics.

    Returns a value where:
    - 1.0 = perfect agreement
    - 0.0 = agreement expected by chance
    - < 0.0 = worse than random agreement

    Args:
        y_true: Ground truth integer labels
        y_pred: Predicted integer labels

    Returns:
        Quadratic weighted kappa score

    Raises:
        ValueError: If arrays are empty or different lengths

    Examples:
        >>> quadratic_weighted_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        1.0
        >>> quadratic_weighted_kappa([1, 2, 3], [2, 3, 4])  # off by 1
        # Returns positive value > 0.5
    """
    _validate_arrays(y_true, y_pred)

    # Get all unique labels
    labels = sorted(set(y_true) | set(y_pred))
    n_labels = len(labels)

    # Handle case where all predictions are the same single value
    if n_labels == 1:
        # If both ground truth and predictions are the same constant, perfect agreement
        return 1.0

    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    # Build confusion matrix
    conf_mat = [[0] * n_labels for _ in range(n_labels)]
    for yt, yp in zip(y_true, y_pred):
        i = label_to_idx[yt]
        j = label_to_idx[yp]
        conf_mat[i][j] += 1

    # Build weight matrix (quadratic)
    weight_mat = [[0.0] * n_labels for _ in range(n_labels)]
    for i in range(n_labels):
        for j in range(n_labels):
            weight_mat[i][j] = ((i - j) ** 2) / ((n_labels - 1) ** 2)

    # Calculate observed score
    n_samples = len(y_true)
    observed = 0.0
    for i in range(n_labels):
        for j in range(n_labels):
            observed += weight_mat[i][j] * conf_mat[i][j]
    observed /= n_samples

    # Calculate expected score (chance agreement)
    hist_true = [sum(conf_mat[i][j] for j in range(n_labels)) for i in range(n_labels)]
    hist_pred = [sum(conf_mat[i][j] for i in range(n_labels)) for j in range(n_labels)]

    expected = 0.0
    for i in range(n_labels):
        for j in range(n_labels):
            expected += weight_mat[i][j] * hist_true[i] * hist_pred[j]
    expected /= (n_samples * n_samples)

    # Calculate kappa
    if expected == 1.0:
        return 0.0  # No agreement possible

    return 1.0 - (observed / expected)


def plus_minus_one_accuracy(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """
    Calculate accuracy for predictions within ±1 of ground truth.

    This metric is useful for ordinal scoring where predictions
    close to the true value are considered acceptable. A prediction
    is correct if it matches exactly or is off by at most 1.

    Args:
        y_true: Ground truth integer labels
        y_pred: Predicted integer labels

    Returns:
        Fraction of predictions within ±1 band (0.0 to 1.0)

    Raises:
        ValueError: If arrays are empty or different lengths

    Examples:
        >>> plus_minus_one_accuracy([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
        1.0
        >>> plus_minus_one_accuracy([1, 2, 3, 4, 5], [2, 2, 3, 4, 4])
        1.0
        >>> plus_minus_one_accuracy([1, 2, 3, 4, 5], [1, 2, 5, 4, 5])
        0.8
    """
    _validate_arrays(y_true, y_pred)

    n_correct = sum(
        1 for yt, yp in zip(y_true, y_pred)
        if abs(yt - yp) <= 1
    )

    return n_correct / len(y_true)

