"""
Push pre-computed evaluation results to LangSmith.

This module pushes already-computed evaluation results to LangSmith
without re-scoring transcripts, avoiding redundant LLM API calls.
"""

from typing import Dict, List, Optional
from datetime import datetime

try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


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


def push_results_to_langsmith(
    dataset_name: str,
    experiment_name: str,
    rows: List[Dict],
    predictions: Dict[str, List[int]],
    ground_truth: Dict[str, List[int]],
    per_dimension_metrics: Dict[str, Dict[str, float]],
    macro_averages: Dict[str, float],
) -> Optional[str]:
    """
    Push pre-computed evaluation results to LangSmith.
    
    This function creates a LangSmith experiment from pre-computed results,
    avoiding the need to re-run the LLM scorer. It uses a mock evaluator
    that simply returns the already-computed predictions.
    
    Args:
        dataset_name: LangSmith dataset name
        experiment_name: Experiment name for tracking
        rows: CSV rows (for transcript text and IDs)
        predictions: Predictions by dimension {dim: [scores]}
        ground_truth: Ground truth by dimension {dim: [scores]}
        per_dimension_metrics: Per-dimension metrics dict
        macro_averages: Macro-averaged metrics dict
    
    Returns:
        LangSmith URL if successful, None otherwise
    
    Raises:
        ImportError: If langsmith package not installed
        Exception: If push to LangSmith fails
    """
    if not LANGSMITH_AVAILABLE:
        raise ImportError("langsmith package not installed")
    
    try:
        from langsmith import Client, evaluate
        from app.services.langsmith_evaluators import (
            create_spin_evaluators,
            spin_summary_evaluator
        )
    except ImportError as e:
        raise ImportError(f"Failed to import LangSmith modules: {e}")
    
    client = Client()
    
    # Verify dataset exists
    try:
        dataset = client.read_dataset(dataset_name=dataset_name)
    except Exception as e:
        raise ValueError(f"LangSmith dataset '{dataset_name}' not found: {e}")
    
    # Create a mock scorer that returns pre-computed predictions
    # This avoids re-running the expensive LLM calls
    def mock_scorer(inputs: Dict) -> Dict:
        """
        Mock scorer that returns pre-computed results.
        
        This allows LangSmith to track the evaluation without
        making actual LLM API calls since we already have the results.
        """
        # Find the index of this transcript in our results
        transcript = inputs.get("transcript", "")
        
        # Find matching row index
        row_idx = None
        for i, row in enumerate(rows):
            if row["transcript"] == transcript:
                row_idx = i
                break
        
        if row_idx is None:
            # Fallback: use sequential index
            # This assumes LangSmith processes examples in order
            row_idx = getattr(mock_scorer, '_current_idx', 0)
            mock_scorer._current_idx = row_idx + 1
        
        # Return pre-computed scores
        return {
            "scores": {
                dim: predictions[dim][row_idx]
                for dim in DIMENSIONS
            }
        }
    
    # Initialize counter for sequential processing
    mock_scorer._current_idx = 0
    
    # Run LangSmith evaluate with mock scorer
    print(f"  Creating experiment in LangSmith...")
    
    try:
        results = evaluate(
            mock_scorer,
            data=dataset_name,
            evaluators=create_spin_evaluators(),
            summary_evaluators=[spin_summary_evaluator],
            experiment_prefix=experiment_name,
            description=f"Evaluation run with pre-computed results",
            metadata={
                "evaluation_type": "spin_scoring",
                "dataset_name": dataset_name,
                "pre_computed": True,
                "num_examples": len(rows),
                "timestamp": datetime.utcnow().isoformat(),
                "macro_pearson_r": macro_averages.get("pearson_r"),
                "macro_qwk": macro_averages.get("qwk"),
                "macro_plus_minus_one": macro_averages.get("plus_minus_one_accuracy"),
            }
        )
        
        # Construct URL (format may vary based on LangSmith version)
        langsmith_url = f"https://smith.langchain.com"
        
        return langsmith_url
        
    except Exception as e:
        raise Exception(f"Failed to create LangSmith experiment: {e}")

