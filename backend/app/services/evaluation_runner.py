"""
Evaluation runner service for offline evaluation and calibration.

This module provides service functions for evaluating LLM scorer performance
against ground truth labels from CSV files or databases. Supports both
file-based and database-driven evaluation workflows.
"""

import csv
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.scorer import score_transcript
from app.services.evaluation_metrics import (
    pearson_r,
    quadratic_weighted_kappa,
    plus_minus_one_accuracy
)


# Dimension names mapping CSV columns to scorer output
DIMENSIONS = [
    "situation",
    "problem",
    "implication",
    "need_payoff",
    "flow",
    "tone",
    "engagement"
]


def load_eval_data(csv_path: str) -> List[Dict]:
    """
    Load evaluation data from CSV file.

    Args:
        csv_path: Path to CSV file with ground truth labels

    Returns:
        List of dictionaries with id, transcript, and ground truth scores

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing or CSV is empty
    """
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Required columns
    required_cols = ["id", "transcript"] + [f"score_{dim}" for dim in DIMENSIONS]

    rows = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate columns
        if not reader.fieldnames:
            raise ValueError("CSV file has no headers")

        missing_cols = set(required_cols) - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Load rows
        for row in reader:
            rows.append(row)

    if len(rows) == 0:
        raise ValueError("CSV contains no data rows")

    return rows


def evaluate_single_transcript(
    transcript: str,
    ground_truth_scores: Dict[str, int],
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
) -> Tuple[Dict[str, int], str, str]:
    """
    Evaluate a single transcript and return model predictions.

    Args:
        transcript: Sales conversation text
        ground_truth_scores: Dictionary of ground truth scores by dimension
        organization_id: Organization UUID for prompt template lookup
        db: Database session

    Returns:
        Tuple of (predicted_scores, model_name, prompt_version)
    """
    # Call scorer
    assessment_data, model_name, prompt_version = score_transcript(
        transcript,
        organization_id=organization_id,
        db=db
    )

    # Extract scores
    predicted_scores = assessment_data["scores"]

    return predicted_scores, model_name, prompt_version


def score_transcripts_batch(
    csv_path: str,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
) -> Tuple[List[Dict], Dict[str, List[int]], Dict[str, List[int]], str, str]:
    """
    Score all transcripts and return predictions + ground truth.
    
    This function extracts the scoring logic to avoid running the LLM twice.
    It scores each transcript once and returns the raw results for both
    local metric computation and LangSmith uploading.
    
    Args:
        csv_path: Path to CSV with ground truth labels
        organization_id: Organization UUID for prompt template lookup
        db: Database session
    
    Returns:
        Tuple of (rows, predictions_by_dim, ground_truth_by_dim, model_name, prompt_version)
    """
    print(f"Loading evaluation data from {csv_path}...")
    rows = load_eval_data(csv_path)
    n_samples = len(rows)
    print(f"Loaded {n_samples} samples")
    
    # Initialize storage for predictions and ground truth
    predictions = {dim: [] for dim in DIMENSIONS}
    ground_truth = {dim: [] for dim in DIMENSIONS}
    
    model_name = None
    prompt_version = None
    
    # Evaluate each transcript ONCE
    print("Scoring transcripts...")
    for i, row in enumerate(rows, 1):
        transcript = row["transcript"]
        
        # Extract ground truth scores
        gt_scores = {
            dim: int(row[f"score_{dim}"])
            for dim in DIMENSIONS
        }
        
        # Score transcript ONCE (this is the expensive LLM call)
        pred_scores, model, prompt = evaluate_single_transcript(
            transcript,
            gt_scores,
            organization_id=organization_id,
            db=db
        )
        
        # Store metadata from first prediction
        if model_name is None:
            model_name = model
            prompt_version = prompt
        
        # Collect predictions and ground truth for each dimension
        for dim in DIMENSIONS:
            predictions[dim].append(pred_scores[dim])
            ground_truth[dim].append(gt_scores[dim])
        
        if i % 10 == 0:
            print(f"  Scored {i}/{n_samples} transcripts...")
    
    print(f"Completed scoring {n_samples} transcripts")
    
    return rows, predictions, ground_truth, model_name, prompt_version


def compute_dimension_metrics(
    y_true: List[int],
    y_pred: List[int]
) -> Dict[str, float]:
    """
    Compute all metrics for a single dimension.

    Args:
        y_true: Ground truth scores
        y_pred: Predicted scores

    Returns:
        Dictionary with pearson_r, qwk, and plus_minus_one_accuracy
    """
    return {
        "pearson_r": pearson_r(y_true, y_pred),
        "qwk": quadratic_weighted_kappa(y_true, y_pred),
        "plus_minus_one_accuracy": plus_minus_one_accuracy(y_true, y_pred)
    }


def compute_macro_averages(per_dimension_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """
    Compute macro-averaged metrics across all dimensions.

    Args:
        per_dimension_metrics: Metrics for each dimension

    Returns:
        Dictionary with averaged pearson_r, qwk, and plus_minus_one_accuracy
    """
    metric_names = ["pearson_r", "qwk", "plus_minus_one_accuracy"]
    n_dims = len(per_dimension_metrics)

    macro_avg = {}
    for metric in metric_names:
        total = sum(dim_metrics[metric] for dim_metrics in per_dimension_metrics.values())
        macro_avg[metric] = total / n_dims

    return macro_avg


def run_evaluation(
    csv_path: str,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
) -> Tuple[Dict, Dict[str, Dict], Dict[str, float], str, str, float]:
    """
    Run evaluation against CSV file and return results.
    
    This function now uses the efficient single-pass scoring approach
    for consistency with run_dual_evaluation().

    Args:
        csv_path: Path to CSV with ground truth labels
        organization_id: Organization UUID for prompt template lookup
        db: Database session

    Returns:
        Tuple of (
            rows,
            per_dimension_metrics,
            macro_averages,
            model_name,
            prompt_version,
            runtime_seconds
        )
    """
    start_time = time.time()

    # Score transcripts once using efficient batch scoring
    rows, predictions, ground_truth, model_name, prompt_version = score_transcripts_batch(
        csv_path,
        organization_id=organization_id,
        db=db
    )

    # Compute metrics per dimension
    print("Computing metrics...")
    per_dimension_metrics = {}
    for dim in DIMENSIONS:
        per_dimension_metrics[dim] = compute_dimension_metrics(
            ground_truth[dim],
            predictions[dim]
        )

    # Compute macro averages
    macro_averages = compute_macro_averages(per_dimension_metrics)

    runtime_seconds = time.time() - start_time

    return (
        rows,
        per_dimension_metrics,
        macro_averages,
        model_name,
        prompt_version,
        runtime_seconds
    )


def run_evaluation_with_storage(
    csv_path: str,
    prompt_template_id: Optional[uuid.UUID] = None,
    dataset_id: Optional[uuid.UUID] = None,
    experiment_name: Optional[str] = None,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
):
    """
    Run evaluation and optionally store results in database.

    Args:
        csv_path: Path to CSV with ground truth labels
        prompt_template_id: ID of prompt template being evaluated
        dataset_id: ID of evaluation dataset
        experiment_name: Optional name for this experiment
        organization_id: Organization UUID for prompt template lookup
        db: Database session

    Returns:
        EvaluationRun object if stored, None otherwise
    """
    from app.models.evaluation_run import EvaluationRun

    # Run evaluation
    rows, per_dimension_metrics, macro_averages, model_name, prompt_version, runtime = run_evaluation(
        csv_path,
        organization_id=organization_id,
        db=db
    )

    n_samples = len(rows)

    # Store in database if prompt_template_id provided
    eval_run = None
    if prompt_template_id and db:
        eval_run = EvaluationRun(
            prompt_template_id=prompt_template_id,
            dataset_id=dataset_id,
            experiment_name=experiment_name,
            num_examples=n_samples,
            macro_pearson_r=macro_averages["pearson_r"],
            macro_qwk=macro_averages["qwk"],
            macro_plus_minus_one=macro_averages["plus_minus_one_accuracy"],
            per_dimension_metrics=per_dimension_metrics,
            model_name=model_name,
            runtime_seconds=runtime,
        )
        db.add(eval_run)
        db.commit()
        db.refresh(eval_run)

        print(f"\n✓ Evaluation stored in database (run_id={eval_run.id})")

    # Print results
    print("\nEvaluation complete!")
    print(f"  Pearson r: {macro_averages['pearson_r']:.3f}")
    print(f"  QWK: {macro_averages['qwk']:.3f}")
    print(f"  ±1 Accuracy: {macro_averages['plus_minus_one_accuracy']:.3f}")
    print(f"  Runtime: {runtime:.2f}s")

    return eval_run


def construct_langsmith_url(dataset_name: str, experiment_id: str) -> str:
    """
    Construct LangSmith web UI URL for an experiment.
    
    Args:
        dataset_name: LangSmith dataset name
        experiment_id: Experiment/session ID
    
    Returns:
        Full URL to view experiment in LangSmith
    """
    # LangSmith URL format (may need adjustment based on actual LangSmith API)
    return f"https://smith.langchain.com"


def run_dual_evaluation(
    csv_path: str,
    prompt_template_id: uuid.UUID,
    dataset_id: uuid.UUID,
    experiment_name: Optional[str],
    organization_id: uuid.UUID,
    db: Session,
) -> "EvaluationRun":
    """
    Run evaluation once, store results locally and optionally in LangSmith.
    
    This function executes the evaluation pipeline efficiently:
    1. Score all transcripts ONCE (single pass through LLM)
    2. Compute metrics locally
    3. Store in local database
    4. Optionally push results to LangSmith (no re-scoring!)
    
    Args:
        csv_path: Path to CSV with ground truth labels
        prompt_template_id: ID of prompt template being evaluated
        dataset_id: ID of evaluation dataset
        experiment_name: Optional name for this experiment
        organization_id: Organization UUID for prompt template lookup
        db: Database session
    
    Returns:
        EvaluationRun object with local metrics and LangSmith URL (if available)
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is invalid
    """
    from app.models.evaluation_run import EvaluationRun
    from app.models.evaluation_dataset import EvaluationDataset
    
    start_time = time.time()
    
    # Phase 1: Score all transcripts ONCE (the expensive operation)
    print("=" * 60)
    print("Phase 1: Scoring Transcripts")
    print("=" * 60)
    
    rows, predictions, ground_truth, model_name, prompt_version = score_transcripts_batch(
        csv_path,
        organization_id=organization_id,
        db=db
    )
    
    n_samples = len(rows)
    
    # Phase 2: Compute metrics (fast, no LLM calls)
    print("\n" + "=" * 60)
    print("Phase 2: Computing Metrics")
    print("=" * 60)
    print("Calculating Pearson r, QWK, and ±1 accuracy...")
    
    per_dimension_metrics = {}
    for dim in DIMENSIONS:
        per_dimension_metrics[dim] = compute_dimension_metrics(
            ground_truth[dim],
            predictions[dim]
        )
    
    macro_averages = compute_macro_averages(per_dimension_metrics)
    runtime = time.time() - start_time
    
    print(f"✓ Metrics computed for all {len(DIMENSIONS)} dimensions")
    
    # Phase 3: Store in local database (always)
    print("\n" + "=" * 60)
    print("Phase 3: Storing Results Locally")
    print("=" * 60)
    
    eval_run = EvaluationRun(
        prompt_template_id=prompt_template_id,
        dataset_id=dataset_id,
        experiment_name=experiment_name,
        num_examples=n_samples,
        macro_pearson_r=macro_averages["pearson_r"],
        macro_qwk=macro_averages["qwk"],
        macro_plus_minus_one=macro_averages["plus_minus_one_accuracy"],
        per_dimension_metrics=per_dimension_metrics,
        model_name=model_name,
        runtime_seconds=runtime,
    )
    
    # Phase 4: Optionally push to LangSmith (no re-scoring!)
    langsmith_url = None
    langsmith_experiment_id = None
    
    if settings.LANGCHAIN_API_KEY:
        print("\n" + "=" * 60)
        print("Phase 4: Pushing to LangSmith")
        print("=" * 60)
        
        # Get dataset info to find LangSmith dataset name
        dataset = db.query(EvaluationDataset).filter(
            EvaluationDataset.id == dataset_id
        ).first() if dataset_id else None
        
        if dataset and dataset.langsmith_dataset_name:
            try:
                from app.services.langsmith_results_pusher import push_results_to_langsmith
                
                print(f"Pushing pre-computed results to LangSmith...")
                print(f"  Dataset: {dataset.langsmith_dataset_name}")
                print(f"  Experiment: {experiment_name or 'unnamed'}")
                
                langsmith_url = push_results_to_langsmith(
                    dataset_name=dataset.langsmith_dataset_name,
                    experiment_name=experiment_name or f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    rows=rows,
                    predictions=predictions,
                    ground_truth=ground_truth,
                    per_dimension_metrics=per_dimension_metrics,
                    macro_averages=macro_averages,
                )
                
                if langsmith_url:
                    langsmith_experiment_id = experiment_name
                    print(f"✓ Results pushed to LangSmith")
                    print(f"  View at: {langsmith_url}")
                    
            except ImportError:
                print("⚠️  LangSmith package not installed, skipping cloud push")
            except Exception as e:
                print(f"⚠️  LangSmith push failed: {e}")
                print("   Local results are still saved")
        else:
            if not dataset:
                print("⚠️  Dataset not found, skipping LangSmith push")
            elif not dataset.langsmith_dataset_name:
                print("⚠️  Dataset not uploaded to LangSmith yet")
                print("   (Dataset will auto-upload on next creation)")
    else:
        print("\nℹ️  LANGCHAIN_API_KEY not configured - local-only evaluation")
    
    # Store in database with LangSmith info
    eval_run.langsmith_url = langsmith_url
    eval_run.langsmith_experiment_id = langsmith_experiment_id
    
    db.add(eval_run)
    db.commit()
    db.refresh(eval_run)
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Evaluation Complete!")
    print("=" * 60)
    print(f"  Transcripts Scored: {n_samples}")
    print(f"  Pearson r: {macro_averages['pearson_r']:.3f}")
    print(f"  QWK: {macro_averages['qwk']:.3f}")
    print(f"  ±1 Accuracy: {macro_averages['plus_minus_one_accuracy']:.3f}")
    print(f"  Runtime: {runtime:.2f}s")
    print(f"  Run ID: {eval_run.id}")
    if langsmith_url:
        print(f"  LangSmith: {langsmith_url}")
    print("=" * 60)
    
    return eval_run

