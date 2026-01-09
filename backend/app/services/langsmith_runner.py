"""
LangSmith-based evaluation service for SPIN scoring assessment.

This module provides service functions for integrating with LangSmith
for experiment tracking and visualization.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

try:
    from langsmith import Client, evaluate
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

from app.services.scorer import score_transcript
from app.services.langsmith_evaluators import (
    create_spin_evaluators,
    spin_summary_evaluator,
    overall_quality_evaluator
)


def create_scorer_wrapper(organization_id: Optional[uuid.UUID] = None, db: Optional[Session] = None):
    """
    Create a wrapper function for score_transcript that matches LangSmith's expected signature.

    LangSmith's evaluate() expects a function that takes inputs dict and returns outputs dict.
    Our scorer takes a transcript string and returns (data, model, version).

    Args:
        organization_id: Organization UUID for prompt template lookup
        db: Database session

    Returns:
        Wrapper function compatible with LangSmith evaluate()
    """
    def scorer_wrapper(inputs: Dict) -> Dict:
        """
        Wrap score_transcript for LangSmith compatibility.

        Args:
            inputs: Dict with "transcript" key

        Returns:
            Dict with "scores" and "coaching" keys
        """
        transcript = inputs.get("transcript", "")

        # Call scorer
        assessment_data, model_name, prompt_version = score_transcript(
            transcript,
            organization_id=organization_id,
            db=db
        )

        # Extract scores (this is what evaluators will compare against ground truth)
        return {
            "scores": assessment_data["scores"],
            "coaching": assessment_data["coaching"],
            "metadata": {
                "model_name": model_name,
                "prompt_version": prompt_version
            }
        }

    return scorer_wrapper


def run_langsmith_evaluation(
    dataset_name: str,
    experiment_name: Optional[str] = None,
    description: Optional[str] = None,
    include_row_evaluators: bool = True,
    include_summary_evaluators: bool = True,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
):
    """
    Run evaluation using LangSmith framework.

    Args:
        dataset_name: Name of LangSmith dataset to evaluate against
        experiment_name: Name for this evaluation run (default: auto-generated)
        description: Optional description for the experiment
        include_row_evaluators: Include per-example evaluators (default: True)
        include_summary_evaluators: Include summary/aggregate evaluators (default: True)
        organization_id: Organization UUID for prompt template lookup
        db: Database session

    Returns:
        EvaluationResults object from LangSmith

    Raises:
        ValueError: If LANGCHAIN_API_KEY not set or dataset doesn't exist
        ImportError: If langsmith package not installed
    """
    if not LANGSMITH_AVAILABLE:
        raise ImportError(
            "langsmith package not installed. Install with: pip install langsmith>=0.2.0"
        )

    # Initialize client
    try:
        client = Client()
    except Exception as e:
        raise ValueError(
            f"Failed to initialize LangSmith client. "
            f"Ensure LANGCHAIN_API_KEY is set. Error: {e}"
        )

    # Verify dataset exists
    try:
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"Found dataset: {dataset.name} (ID: {dataset.id})")
        print(f"  Description: {dataset.description}")
        print(f"  Examples: {dataset.example_count}")
    except Exception as e:
        raise ValueError(
            f"Dataset '{dataset_name}' not found. "
            f"Create it with upload_eval_dataset.py script.\n"
            f"Error: {e}"
        )

    # Generate experiment name if not provided
    if experiment_name is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"spin_eval_{timestamp}"

    # Build evaluators list
    evaluators = []
    summary_evaluators = []

    if include_row_evaluators:
        # Add per-dimension evaluators
        evaluators.extend(create_spin_evaluators())
        # Add overall quality evaluator
        evaluators.append(overall_quality_evaluator)
        print(f"Using {len(evaluators)} row-level evaluators")

    if include_summary_evaluators:
        # Add summary evaluator for aggregate metrics
        summary_evaluators.append(spin_summary_evaluator)
        print(f"Using {len(summary_evaluators)} summary evaluators")

    # Create scorer wrapper
    scorer = create_scorer_wrapper(organization_id=organization_id, db=db)

    # Run evaluation
    print(f"\nStarting evaluation: {experiment_name}")
    print(f"Dataset: {dataset_name}")
    print("-" * 60)

    results = evaluate(
        scorer,
        data=dataset_name,
        evaluators=evaluators if evaluators else None,
        summary_evaluators=summary_evaluators if summary_evaluators else None,
        experiment_prefix=experiment_name,
        description=description or f"SPIN scoring evaluation on {dataset_name}",
        metadata={
            "evaluation_type": "spin_scoring",
            "dataset_name": dataset_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    print("-" * 60)
    print(f"✓ Evaluation complete!")
    print(f"\nResults:")
    print(f"  Experiment: {experiment_name}")
    print(f"  Examples evaluated: {dataset.example_count}")

    # Display summary metrics if available
    if hasattr(results, "aggregate_metrics") and results.aggregate_metrics:
        print(f"\n  Summary Metrics:")
        for key, value in results.aggregate_metrics.items():
            if "macro_avg" in key:
                print(f"    {key}: {value:.3f}")

    # Provide link to view results
    print(f"\n  View results in LangSmith:")
    print(f"  https://smith.langchain.com/")

    return results

