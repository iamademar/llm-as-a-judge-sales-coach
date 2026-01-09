#!/usr/bin/env python3
"""
Upload evaluation datasets from CSV to LangSmith.

This script converts CSV files with ground truth labels into LangSmith datasets
that can be used with the evaluate() function.

Usage:
    python scripts/upload_eval_dataset.py --csv eval_data.csv --dataset-name sales-eval-v1
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langsmith import Client
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


# Dimension names mapping CSV columns
DIMENSIONS = [
    "situation",
    "problem",
    "implication",
    "need_payoff",
    "flow",
    "tone",
    "engagement"
]


def load_csv_data(csv_path: str) -> List[Dict]:
    """Load evaluation data from CSV file."""
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    required_cols = ["id", "transcript"] + [f"score_{dim}" for dim in DIMENSIONS]

    rows = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV file has no headers")

        missing_cols = set(required_cols) - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        for row in reader:
            rows.append(row)

    if len(rows) == 0:
        raise ValueError("CSV contains no data rows")

    return rows


def convert_to_langsmith_examples(csv_rows: List[Dict]) -> List[Dict]:
    """Convert CSV rows to LangSmith Example format."""
    examples = []

    for row in csv_rows:
        inputs = {"transcript": row["transcript"]}

        outputs = {}
        for dim in DIMENSIONS:
            score_col = f"score_{dim}"
            if score_col in row:
                outputs[dim] = int(row[score_col])

        metadata = {"id": row.get("id", "")}

        examples.append({
            "inputs": inputs,
            "outputs": outputs,
            "metadata": metadata
        })

    return examples


def upload_dataset(
    csv_path: str,
    dataset_name: str,
    description: str = None,
    overwrite: bool = False
) -> str:
    """Upload CSV data to LangSmith as a dataset."""
    if not LANGSMITH_AVAILABLE:
        raise ImportError(
            "langsmith package not installed. Install with: pip install langsmith>=0.2.0"
        )

    try:
        client = Client()
    except Exception as e:
        raise ValueError(
            f"Failed to initialize LangSmith client. "
            f"Ensure LANGCHAIN_API_KEY is set. Error: {e}"
        )

    print(f"Loading data from {csv_path}...")
    csv_rows = load_csv_data(csv_path)
    print(f"Loaded {len(csv_rows)} examples")

    print("Converting to LangSmith format...")
    examples = convert_to_langsmith_examples(csv_rows)

    # Check if dataset exists
    dataset_exists = False
    try:
        existing_dataset = client.read_dataset(dataset_name=dataset_name)
        dataset_exists = True
        print(f"Dataset '{dataset_name}' already exists")

        if overwrite:
            print(f"Deleting existing dataset...")
            client.delete_dataset(dataset_id=existing_dataset.id)
            dataset_exists = False
        else:
            print(f"Updating existing dataset (adding new examples)...")

    except Exception:
        pass  # Dataset doesn't exist, will create new one

    # Create or get dataset
    if not dataset_exists:
        print(f"Creating new dataset '{dataset_name}'...")
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description or f"SPIN scoring evaluation dataset with {len(examples)} examples"
        )
        print(f"Created dataset with ID: {dataset.id}")
    else:
        dataset = existing_dataset

    # Upload examples
    print(f"Uploading {len(examples)} examples...")
    client.create_examples(
        inputs=[ex["inputs"] for ex in examples],
        outputs=[ex["outputs"] for ex in examples],
        metadata=[ex["metadata"] for ex in examples],
        dataset_id=dataset.id
    )

    print(f"✓ Successfully uploaded {len(examples)} examples to dataset '{dataset_name}'")
    print(f"  Dataset ID: {dataset.id}")
    print(f"  View in LangSmith: https://smith.langchain.com/datasets/{dataset.id}")

    return dataset.id


def main():
    """CLI entry point"""
    if not LANGSMITH_AVAILABLE:
        print("Error: langsmith package not installed.")
        print("Install with: pip install langsmith>=0.2.0")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Upload evaluation CSV to LangSmith dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new dataset
  python scripts/upload_eval_dataset.py --csv eval_data.csv --dataset-name sales-eval-v1

  # Update existing dataset (add examples)
  python scripts/upload_eval_dataset.py --csv new_data.csv --dataset-name sales-eval-v1

  # Overwrite existing dataset
  python scripts/upload_eval_dataset.py --csv eval_data.csv --dataset-name sales-eval-v1 --overwrite

Environment Variables:
  LANGCHAIN_API_KEY: Required. Get from https://smith.langchain.com/settings
        """
    )

    parser.add_argument(
        "--csv", "-c",
        required=True,
        help="Path to CSV file with ground truth labels"
    )

    parser.add_argument(
        "--dataset-name", "-d",
        required=True,
        help="Name for the LangSmith dataset"
    )

    parser.add_argument(
        "--description",
        help="Optional description for the dataset"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate dataset if it exists (default: update/append)"
    )

    args = parser.parse_args()

    try:
        upload_dataset(
            csv_path=args.csv,
            dataset_name=args.dataset_name,
            description=args.description,
            overwrite=args.overwrite
        )
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()

