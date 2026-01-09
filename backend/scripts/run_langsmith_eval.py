#!/usr/bin/env python3
"""
CLI wrapper for LangSmith-based evaluation.

This script provides a command-line interface for running evaluations
using LangSmith for experiment tracking and visualization.

Usage:
    python scripts/run_langsmith_eval.py --dataset sales-eval-v1 --experiment prompt-v2
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.langsmith_runner import run_langsmith_evaluation, LANGSMITH_AVAILABLE
from app.database import SessionLocal


def main():
    """CLI entry point"""
    if not LANGSMITH_AVAILABLE:
        print("Error: langsmith package not installed.")
        print("Install with: pip install langsmith>=0.2.0")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Run LangSmith-based evaluation for SPIN scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation
  python scripts/run_langsmith_eval.py --dataset sales-eval-v1

  # Named experiment
  python scripts/run_langsmith_eval.py --dataset sales-eval-v1 --experiment prompt-v2

  # With description
  python scripts/run_langsmith_eval.py \\
    --dataset sales-eval-v1 \\
    --experiment prompt-v2 \\
    --description "Testing improved implication question examples"

  # Only summary metrics (faster)
  python scripts/run_langsmith_eval.py \\
    --dataset sales-eval-v1 \\
    --no-row-evaluators

  # With organization context (for database-driven prompts)
  python scripts/run_langsmith_eval.py \\
    --dataset sales-eval-v1 \\
    --org-id <uuid>

Environment Variables:
  LANGCHAIN_API_KEY: Required. Get from https://smith.langchain.com/settings
  MOCK_LLM: Set to "true" for testing without real LLM calls

Workflow:
  1. Create dataset: python scripts/upload_eval_dataset.py --csv data.csv --dataset-name my-eval
  2. Run evaluation: python scripts/run_langsmith_eval.py --dataset my-eval --experiment v1
  3. View results: https://smith.langchain.com/
  4. Iterate on prompts and re-evaluate with new experiment name
  5. Compare experiments in LangSmith web UI
        """
    )

    parser.add_argument(
        "--dataset", "-d",
        required=True,
        help="Name of LangSmith dataset to evaluate against"
    )

    parser.add_argument(
        "--experiment", "-e",
        help="Name for this evaluation run (default: auto-generated with timestamp)"
    )

    parser.add_argument(
        "--description",
        help="Optional description for the experiment"
    )

    parser.add_argument(
        "--no-row-evaluators",
        action="store_true",
        help="Skip per-example evaluators (faster, only summary metrics)"
    )

    parser.add_argument(
        "--no-summary-evaluators",
        action="store_true",
        help="Skip summary evaluators (only per-example metrics)"
    )

    parser.add_argument(
        "--org-id",
        help="Organization UUID (for database-driven prompt lookup)"
    )

    args = parser.parse_args()

    # Setup database session if org_id provided
    db = None
    org_id = None
    if args.org_id:
        import uuid
        org_id = uuid.UUID(args.org_id)
        db = SessionLocal()

    try:
        run_langsmith_evaluation(
            dataset_name=args.dataset,
            experiment_name=args.experiment,
            description=args.description,
            include_row_evaluators=not args.no_row_evaluators,
            include_summary_evaluators=not args.no_summary_evaluators,
            organization_id=org_id,
            db=db,
        )
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()

