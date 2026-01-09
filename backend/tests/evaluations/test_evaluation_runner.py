"""
Smoke tests for evaluation CLI runner.

Tests the end-to-end evaluation flow with a small CSV fixture,
mocking the scorer to emit known values, and verifying report structure.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.services.evaluation_runner import run_evaluation


@pytest.fixture
def eval_csv_fixture(tmp_path):
    """Create a small 3-row CSV fixture for testing"""
    csv_content = """id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hi there\\nBuyer: Hello",4,3,4,3,4,4,3
2,"Rep: How's business?\\nBuyer: Good thanks",3,4,3,4,3,4,4
3,"Rep: Tell me about challenges\\nBuyer: We need better tools",5,4,5,4,5,4,5
"""
    csv_path = tmp_path / "eval_data.csv"
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def output_json_path(tmp_path):
    """Create temporary output path for JSON report"""
    return tmp_path / "eval_report.json"


def test_evaluation_runs_and_produces_report(eval_csv_fixture, output_json_path):
    """
    Smoke test: evaluation runs end-to-end and produces valid JSON report
    """
    # Mock scorer to return known values
    mock_assessment_data = {
        "scores": {
            "situation": 4,
            "problem": 3,
            "implication": 4,
            "need_payoff": 3,
            "flow": 4,
            "tone": 4,
            "engagement": 3
        },
        "coaching": {
            "summary": "Good performance",
            "wins": ["Clear opening"],
            "gaps": ["Need more probing"],
            "next_actions": ["Practice implication questions"]
        }
    }

    with patch("app.eval.run.score_transcript") as mock_scorer:
        # Configure mock to return consistent scores for all rows
        mock_scorer.return_value = (
            mock_assessment_data,
            "gpt-4o-mini",
            "spin_v1"
        )

        # Run evaluation
        run_evaluation(
            input_csv=str(eval_csv_fixture),
            output_json=str(output_json_path)
        )

        # Verify scorer was called 3 times (once per row)
        assert mock_scorer.call_count == 3

    # Verify report was created
    assert output_json_path.exists()

    # Load and validate report structure
    with open(output_json_path) as f:
        report = json.load(f)

    # Check top-level keys
    assert "model_name" in report
    assert "prompt_version" in report
    assert "timestamp" in report
    assert "n_samples" in report
    assert "per_dimension_metrics" in report
    assert "macro_averages" in report

    # Check metadata
    assert report["model_name"] == "gpt-4o-mini"
    assert report["prompt_version"] == "spin_v1"
    assert report["n_samples"] == 3

    # Check per-dimension metrics structure
    dimensions = [
        "situation", "problem", "implication", "need_payoff",
        "flow", "tone", "engagement"
    ]
    for dim in dimensions:
        assert dim in report["per_dimension_metrics"]
        metrics = report["per_dimension_metrics"][dim]
        assert "pearson_r" in metrics
        assert "qwk" in metrics
        assert "plus_minus_one_accuracy" in metrics

    # Check macro averages structure
    assert "pearson_r" in report["macro_averages"]
    assert "qwk" in report["macro_averages"]
    assert "plus_minus_one_accuracy" in report["macro_averages"]


def test_evaluation_with_varying_scores(eval_csv_fixture, output_json_path):
    """
    Test evaluation with mock returning different scores per call
    """
    # Mock scorer to return different values each time
    mock_responses = [
        # First row: exact match to ground truth [4,3,4,3,4,4,3]
        ({
            "scores": {
                "situation": 4, "problem": 3, "implication": 4,
                "need_payoff": 3, "flow": 4, "tone": 4, "engagement": 3
            },
            "coaching": {"summary": "Row 1", "wins": [], "gaps": [], "next_actions": []}
        }, "gpt-4o-mini", "spin_v1"),
        # Second row: off by 1 from ground truth [3,4,3,4,3,4,4]
        ({
            "scores": {
                "situation": 2, "problem": 3, "implication": 2,
                "need_payoff": 3, "flow": 2, "tone": 3, "engagement": 3
            },
            "coaching": {"summary": "Row 2", "wins": [], "gaps": [], "next_actions": []}
        }, "gpt-4o-mini", "spin_v1"),
        # Third row: some matches from ground truth [5,4,5,4,5,4,5]
        ({
            "scores": {
                "situation": 5, "problem": 4, "implication": 5,
                "need_payoff": 4, "flow": 5, "tone": 4, "engagement": 5
            },
            "coaching": {"summary": "Row 3", "wins": [], "gaps": [], "next_actions": []}
        }, "gpt-4o-mini", "spin_v1"),
    ]

    with patch("app.eval.run.score_transcript") as mock_scorer:
        mock_scorer.side_effect = mock_responses

        # Run evaluation
        run_evaluation(
            input_csv=str(eval_csv_fixture),
            output_json=str(output_json_path)
        )

    # Load report
    with open(output_json_path) as f:
        report = json.load(f)

    # Verify metrics are calculated (non-zero)
    # With exact match on row 1 and 3, should have good correlation
    for dim in ["situation", "problem", "implication"]:
        metrics = report["per_dimension_metrics"][dim]
        # Should have some reasonable correlation
        assert -1.0 <= metrics["pearson_r"] <= 1.0
        assert 0.0 <= metrics["qwk"] <= 1.0
        assert 0.0 <= metrics["plus_minus_one_accuracy"] <= 1.0


def test_evaluation_handles_missing_columns(tmp_path, output_json_path):
    """
    Test that evaluation fails gracefully with missing required columns
    """
    # CSV missing score columns
    bad_csv_content = """id,transcript
1,"Rep: Hi\\nBuyer: Hello"
"""
    bad_csv_path = tmp_path / "bad_eval.csv"
    bad_csv_path.write_text(bad_csv_content)

    # Should raise ValueError for missing columns
    with pytest.raises(ValueError, match="Missing required columns"):
        run_evaluation(
            input_csv=str(bad_csv_path),
            output_json=str(output_json_path)
        )


def test_evaluation_handles_empty_csv(tmp_path, output_json_path):
    """
    Test that evaluation fails gracefully with empty CSV
    """
    # Empty CSV (only headers)
    empty_csv_content = """id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
"""
    empty_csv_path = tmp_path / "empty_eval.csv"
    empty_csv_path.write_text(empty_csv_content)

    # Should raise ValueError for empty data
    with pytest.raises(ValueError, match="CSV contains no data rows"):
        run_evaluation(
            input_csv=str(empty_csv_path),
            output_json=str(output_json_path)
        )


def test_evaluation_computes_correct_metrics_simple_case(tmp_path, output_json_path):
    """
    Test with simple case where we can verify metric calculations
    """
    # Simple 2-row CSV with known scores
    simple_csv = """id,transcript,score_situation,score_problem,score_implication,score_need_payoff,score_flow,score_tone,score_engagement
1,"Rep: Hello\\nBuyer: Hi",3,3,3,3,3,3,3
2,"Rep: Tell me\\nBuyer: Sure",5,5,5,5,5,5,5
"""
    csv_path = tmp_path / "simple_eval.csv"
    csv_path.write_text(simple_csv)

    # Mock to return exact matches
    mock_responses = [
        ({
            "scores": {
                "situation": 3, "problem": 3, "implication": 3,
                "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3
            },
            "coaching": {"summary": "", "wins": [], "gaps": [], "next_actions": []}
        }, "test-model", "test_v1"),
        ({
            "scores": {
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
            },
            "coaching": {"summary": "", "wins": [], "gaps": [], "next_actions": []}
        }, "test-model", "test_v1"),
    ]

    with patch("app.eval.run.score_transcript") as mock_scorer:
        mock_scorer.side_effect = mock_responses

        run_evaluation(
            input_csv=str(csv_path),
            output_json=str(output_json_path)
        )

    # Load report
    with open(output_json_path) as f:
        report = json.load(f)

    # With perfect matches, should have perfect metrics
    for dim in ["situation", "problem", "implication", "need_payoff", "flow", "tone", "engagement"]:
        metrics = report["per_dimension_metrics"][dim]
        assert metrics["pearson_r"] == pytest.approx(1.0, abs=1e-6)
        assert metrics["qwk"] == pytest.approx(1.0, abs=1e-6)
        assert metrics["plus_minus_one_accuracy"] == pytest.approx(1.0, abs=1e-6)

    # Macro averages should also be perfect
    assert report["macro_averages"]["pearson_r"] == pytest.approx(1.0, abs=1e-6)
    assert report["macro_averages"]["qwk"] == pytest.approx(1.0, abs=1e-6)
    assert report["macro_averages"]["plus_minus_one_accuracy"] == pytest.approx(1.0, abs=1e-6)
