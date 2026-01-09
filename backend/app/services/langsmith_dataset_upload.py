"""
LangSmith dataset upload service.

This module provides functions for uploading evaluation datasets from CSV files
to LangSmith for experiment tracking and visualization.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def slugify_dataset_name(name: str) -> str:
    """
    Convert dataset name to URL-safe slug.
    
    Args:
        name: Dataset name (e.g., "Q4 2024 Golden Set")
    
    Returns:
        Slugified name (e.g., "q4-2024-golden-set")
    
    Examples:
        >>> slugify_dataset_name("Q4 2024 Golden Set")
        'q4-2024-golden-set'
        >>> slugify_dataset_name("Sales Eval V1")
        'sales-eval-v1'
    """
    # Convert to lowercase
    slug = name.lower()
    
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    return slug


def load_csv_data(csv_path: str) -> List[Dict]:
    """
    Load evaluation data from CSV file.
    
    Args:
        csv_path: Path to CSV file with ground truth labels
    
    Returns:
        List of dictionaries with CSV row data
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If required columns are missing or CSV is empty
    """
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
    """
    Convert CSV rows to LangSmith Example format.
    
    Args:
        csv_rows: List of CSV row dictionaries
    
    Returns:
        List of LangSmith example dictionaries
    """
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


def upload_csv_to_langsmith(
    csv_path: str,
    dataset_name: str,
    description: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Upload CSV data to LangSmith as a dataset.
    
    Args:
        csv_path: Path to CSV file with evaluation data
        dataset_name: Name for the dataset in LangSmith (should be slugified)
        description: Optional description for the dataset
    
    Returns:
        Tuple of (langsmith_dataset_name, langsmith_dataset_id)
    
    Raises:
        ImportError: If langsmith package not installed
        ValueError: If LANGCHAIN_API_KEY not set or CSV invalid
        Exception: If dataset upload fails
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

    # Load and convert CSV data
    csv_rows = load_csv_data(csv_path)
    examples = convert_to_langsmith_examples(csv_rows)

    print(f"Loaded {len(examples)} examples from CSV")

    # Check if dataset already exists
    try:
        existing_dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"Dataset '{dataset_name}' already exists (ID: {existing_dataset.id})")
        print(f"Updating with {len(examples)} examples...")
        
        # Upload examples to existing dataset
        for example in examples:
            client.create_example(
                inputs=example["inputs"],
                outputs=example["outputs"],
                metadata=example["metadata"],
                dataset_id=existing_dataset.id
            )
        
        return dataset_name, str(existing_dataset.id)
        
    except Exception:
        # Dataset doesn't exist, create new one
        print(f"Creating new dataset: {dataset_name}")
        
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description or f"Evaluation dataset with {len(examples)} examples"
        )
        
        print(f"Created dataset: {dataset.name} (ID: {dataset.id})")
        
        # Upload examples
        print(f"Uploading {len(examples)} examples...")
        for i, example in enumerate(examples, 1):
            client.create_example(
                inputs=example["inputs"],
                outputs=example["outputs"],
                metadata=example["metadata"],
                dataset_id=dataset.id
            )
            if i % 10 == 0:
                print(f"  Uploaded {i}/{len(examples)} examples...")
        
        print(f"✓ Upload complete!")
        
        return dataset.name, str(dataset.id)

