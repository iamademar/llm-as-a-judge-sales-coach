#!/usr/bin/env python3
"""
CLI wrapper for running offline evaluations.

This script provides a command-line interface for evaluating LLM scorer
performance against ground truth labels from CSV files.

Usage:
    python scripts/run_evaluation.py --input eval_data.csv --output report.json

    # With database storage
    python scripts/run_evaluation.py --input eval_data.csv --template-id <uuid> --dataset-id <uuid>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.evaluation_runner import run_evaluation, run_evaluation_with_storage
from app.database import SessionLocal


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Evaluate LLM scorer against ground truth labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation with JSON output
  python scripts/run_evaluation.py --input eval_data.csv --output report.json

  # Evaluation with database storage
  python scripts/run_evaluation.py \\
    --input eval_data.csv \\
    --template-id <uuid> \\
    --dataset-id <uuid> \\
    --org-id <uuid>

  # With experiment name
  python scripts/run_evaluation.py \\
    --input eval_data.csv \\
    --template-id <uuid> \\
    --dataset-id <uuid> \\
    --experiment prompt-v2
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input CSV file with ground truth labels"
    )

    parser.add_argument(
        "--output", "-o",
        help="Path to output JSON report file (optional if using database storage)"
    )

    parser.add_argument(
        "--template-id",
        help="Prompt template UUID (for database storage)"
    )

    parser.add_argument(
        "--dataset-id",
        help="Evaluation dataset UUID (for database storage)"
    )

    parser.add_argument(
        "--experiment",
        help="Experiment name for tracking iterations"
    )

    parser.add_argument(
        "--org-id",
        help="Organization UUID (required for database storage)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.template_id and not args.org_id:
        print("Error: --org-id is required when using --template-id")
        sys.exit(1)

    try:
        # Run with or without database storage
        if args.template_id:
            # Database storage mode
            import uuid
            db = SessionLocal()
            try:
                eval_run = run_evaluation_with_storage(
                    csv_path=args.input,
                    prompt_template_id=uuid.UUID(args.template_id),
                    dataset_id=uuid.UUID(args.dataset_id) if args.dataset_id else None,
                    experiment_name=args.experiment,
                    organization_id=uuid.UUID(args.org_id),
                    db=db,
                )
                print(f"\n✓ Results stored in database (run_id={eval_run.id})")

                # Optionally also save JSON
                if args.output:
                    report = {
                        "run_id": str(eval_run.id),
                        "model_name": eval_run.model_name,
                        "timestamp": eval_run.created_at.isoformat(),
                        "n_samples": eval_run.num_examples,
                        "per_dimension_metrics": eval_run.per_dimension_metrics,
                        "macro_averages": {
                            "pearson_r": eval_run.macro_pearson_r,
                            "qwk": eval_run.macro_qwk,
                            "plus_minus_one_accuracy": eval_run.macro_plus_minus_one,
                        },
                        "runtime_seconds": eval_run.runtime_seconds,
                    }
                    save_json_report(report, args.output)
            finally:
                db.close()
        else:
            # File-based mode (no database)
            rows, per_dimension_metrics, macro_averages, model_name, prompt_version, runtime = run_evaluation(
                csv_path=args.input
            )

            if args.output:
                report = {
                    "model_name": model_name,
                    "prompt_version": prompt_version,
                    "timestamp": datetime.utcnow().isoformat(),
                    "n_samples": len(rows),
                    "per_dimension_metrics": per_dimension_metrics,
                    "macro_averages": macro_averages,
                    "runtime_seconds": runtime,
                }
                save_json_report(report, args.output)
            else:
                print("\nNote: No output file specified. Results not saved.")

    except Exception as e:
        print(f"\nError: {e}")
        raise


def save_json_report(report: dict, output_path: str):
    """Save evaluation report to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Report saved to {output_path}")


if __name__ == "__main__":
    main()

