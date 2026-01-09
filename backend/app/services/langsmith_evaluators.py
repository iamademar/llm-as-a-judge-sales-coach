"""
LangSmith custom evaluators for SPIN scoring assessment.

This module wraps existing evaluation metrics (Pearson r, QWK, ±1 accuracy)
into LangSmith-compatible evaluators. Supports both row-level evaluators
(per-dimension scoring) and summary evaluators (macro averages across all examples).

LangSmith Integration:
    - Row evaluators: Called once per example, return per-dimension metrics
    - Summary evaluators: Called once per experiment, compute aggregate metrics
    - Format: [{"key": "metric_name", "score": float_value}, ...]

Usage:
    from langsmith import evaluate
    from app.services.langsmith_evaluators import create_spin_evaluators, spin_summary_evaluator

    results = evaluate(
        score_transcript_wrapper,
        data="sales-eval-dataset",
        evaluators=create_spin_evaluators(),
        summary_evaluators=[spin_summary_evaluator],
        experiment_prefix="prompt-v2"
    )
"""

from typing import Dict, List, Any
from app.services.evaluation_metrics import pearson_r, quadratic_weighted_kappa, plus_minus_one_accuracy


# Dimension names for SPIN scoring framework
DIMENSIONS = [
    "situation",
    "problem",
    "implication",
    "need_payoff",
    "flow",
    "tone",
    "engagement"
]


def create_dimension_evaluator(dimension: str):
    """
    Create a row-level evaluator for a specific scoring dimension.

    This factory function creates an evaluator that compares predicted scores
    to ground truth for a single dimension. Returns all three metrics
    (Pearson r, QWK, ±1 accuracy) but at the row level they're just comparing
    two single values (no correlation possible).

    For LangSmith, row-level evaluators primarily track exact matches and
    distance, while summary evaluators compute meaningful correlations.

    Args:
        dimension: Scoring dimension name (e.g., "situation", "problem")

    Returns:
        Evaluator function compatible with LangSmith

    Examples:
        >>> situation_eval = create_dimension_evaluator("situation")
        >>> result = situation_eval(
        ...     outputs={"scores": {"situation": 4, ...}},
        ...     reference_outputs={"situation": 4}
        ... )
        >>> result[0]["key"]
        'situation_exact_match'
    """
    def evaluator(outputs: Dict[str, Any], reference_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a single example for this dimension.

        Args:
            outputs: Model output containing "scores" dict with dimension scores
            reference_outputs: Ground truth scores by dimension

        Returns:
            List of metric dicts with keys: key, score
        """
        # Extract predicted score for this dimension
        predicted_score = outputs.get("scores", {}).get(dimension)
        ground_truth_score = reference_outputs.get(dimension)

        # Validate scores exist
        if predicted_score is None or ground_truth_score is None:
            return [
                {"key": f"{dimension}_error", "score": 0, "comment": f"Missing score for {dimension}"}
            ]

        # Calculate metrics
        exact_match = 1.0 if predicted_score == ground_truth_score else 0.0
        within_one = 1.0 if abs(predicted_score - ground_truth_score) <= 1 else 0.0
        distance = abs(predicted_score - ground_truth_score)

        return [
            {"key": f"{dimension}_exact_match", "score": round(float(exact_match), 4)},
            {"key": f"{dimension}_within_one", "score": round(float(within_one), 4)},
            {"key": f"{dimension}_distance", "score": round(float(distance), 4)},
        ]

    # Set function name for LangSmith UI
    evaluator.__name__ = f"{dimension}_evaluator"
    return evaluator


def create_spin_evaluators() -> List[callable]:
    """
    Create all row-level evaluators for SPIN scoring dimensions.

    Returns a list of evaluator functions, one per dimension, that can be
    passed to langsmith.evaluate().

    Returns:
        List of evaluator functions for all SPIN dimensions

    Examples:
        >>> evaluators = create_spin_evaluators()
        >>> len(evaluators)
        7
        >>> evaluators[0].__name__
        'situation_evaluator'
    """
    return [create_dimension_evaluator(dim) for dim in DIMENSIONS]


def spin_summary_evaluator(runs: List[Any], examples: List[Any]) -> Dict[str, Any]:
    """
    Summary evaluator for computing aggregate metrics across all examples.

    This evaluator computes Pearson correlation, QWK, and ±1 accuracy for
    each dimension across the entire dataset, plus macro averages.

    LangSmith calls this once per evaluation run with all examples.

    Args:
        runs: List of Run objects containing outputs from the model
        examples: List of Example objects containing ground truth data

    Returns:
        Dict with aggregate metric results

    Examples:
        >>> # Mock runs and examples
        >>> runs = [MockRun(outputs={"scores": {"situation": 4, ...}}), ...]
        >>> examples = [MockExample(outputs={"situation": 4, ...}), ...]
        >>> result = spin_summary_evaluator(runs, examples)
        >>> "situation_pearson_r" in result["key"]
        True
    """
    # Collect predictions and ground truth by dimension
    predictions = {dim: [] for dim in DIMENSIONS}
    ground_truth = {dim: [] for dim in DIMENSIONS}

    for run, example in zip(runs, examples):
        # Extract scores from run outputs
        run_scores = run.outputs.get("scores", {})

        # Extract ground truth from example reference outputs
        example_scores = example.outputs

        # Collect per dimension
        for dim in DIMENSIONS:
            pred = run_scores.get(dim)
            truth = example_scores.get(dim)

            # Only include if both values present
            if pred is not None and truth is not None:
                predictions[dim].append(pred)
                ground_truth[dim].append(truth)

    # Compute metrics per dimension
    results = []

    for dim in DIMENSIONS:
        pred = predictions[dim]
        truth = ground_truth[dim]

        # Skip if no data for this dimension
        if len(pred) == 0 or len(truth) == 0:
            continue

        # Skip if not enough variance (need at least 2 unique values for correlation)
        if len(set(truth)) < 2 or len(set(pred)) < 2:
            # Can still compute ±1 accuracy
            pm1_acc = plus_minus_one_accuracy(truth, pred)
            results.append({"key": f"{dim}_plus_minus_one_accuracy", "score": round(float(pm1_acc), 4)})
            continue

        # Compute all metrics
        try:
            r = pearson_r(truth, pred)
            qwk = quadratic_weighted_kappa(truth, pred)
            pm1_acc = plus_minus_one_accuracy(truth, pred)

            results.extend([
                {"key": f"{dim}_pearson_r", "score": round(float(r), 4)},
                {"key": f"{dim}_qwk", "score": round(float(qwk), 4)},
                {"key": f"{dim}_plus_minus_one_accuracy", "score": round(float(pm1_acc), 4)},
            ])
        except Exception as e:
            # Log error but don't fail entire evaluation
            results.append({
                "key": f"{dim}_error",
                "score": 0,
                "comment": f"Error computing metrics: {str(e)}"
            })

    # Compute macro averages across dimensions
    # Only include dimensions that have all three metrics
    complete_dims = []
    for dim in DIMENSIONS:
        has_all = all(
            any(r["key"] == f"{dim}_{metric}" for r in results)
            for metric in ["pearson_r", "qwk", "plus_minus_one_accuracy"]
        )
        if has_all:
            complete_dims.append(dim)

    if complete_dims:
        # Calculate macro averages
        avg_r = sum(
            next(r["score"] for r in results if r["key"] == f"{dim}_pearson_r")
            for dim in complete_dims
        ) / len(complete_dims)

        avg_qwk = sum(
            next(r["score"] for r in results if r["key"] == f"{dim}_qwk")
            for dim in complete_dims
        ) / len(complete_dims)

        avg_pm1 = sum(
            next(r["score"] for r in results if r["key"] == f"{dim}_plus_minus_one_accuracy")
            for dim in complete_dims
        ) / len(complete_dims)

        results.extend([
            {"key": "macro_avg_pearson_r", "score": round(float(avg_r), 4)},
            {"key": "macro_avg_qwk", "score": round(float(avg_qwk), 4)},
            {"key": "macro_avg_plus_minus_one_accuracy", "score": round(float(avg_pm1), 4)},
        ])

    # LangSmith expects dict with "results" key for summary evaluators
    return {"results": results}


def overall_quality_evaluator(outputs: Dict[str, Any], reference_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple row-level evaluator for overall quality assessment.

    Computes average distance across all dimensions to give a single
    overall quality score per example.

    Args:
        outputs: Model outputs with scores dict
        reference_outputs: Ground truth scores

    Returns:
        Dict with overall quality metrics
    """
    predicted_scores = outputs.get("scores", {})

    distances = []
    for dim in DIMENSIONS:
        pred = predicted_scores.get(dim)
        truth = reference_outputs.get(dim)

        if pred is not None and truth is not None:
            distances.append(abs(pred - truth))

    if not distances:
        return {"key": "overall_quality_error", "score": 0}

    avg_distance = sum(distances) / len(distances)

    # Convert to quality score (inverse of distance, normalized to [0, 1])
    # Distance ranges from 0 (perfect) to 4 (worst: 1 vs 5 or vice versa)
    quality_score = 1.0 - (avg_distance / 4.0)

    return {"key": "overall_quality", "score": round(float(quality_score), 4)}

