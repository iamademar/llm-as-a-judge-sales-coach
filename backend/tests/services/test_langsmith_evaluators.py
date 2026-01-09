"""
Tests for LangSmith custom evaluators.

Tests the evaluator wrappers that integrate our existing metrics
(Pearson r, QWK, ±1 accuracy) with LangSmith's evaluation framework.
"""

import pytest
from unittest.mock import Mock

from app.services.langsmith_evaluators import (
    create_dimension_evaluator,
    create_spin_evaluators,
    spin_summary_evaluator,
    overall_quality_evaluator,
    DIMENSIONS
)


class TestDimensionEvaluator:
    """Tests for dimension-specific evaluators"""

    def test_exact_match(self):
        """Exact match should return distance=0, exact_match=1, within_one=1"""
        evaluator = create_dimension_evaluator("situation")

        result = evaluator(
            outputs={"scores": {"situation": 4}},
            reference_outputs={"situation": 4}
        )

        # Should return list of dicts
        assert isinstance(result, list)
        assert len(result) == 3

        # Check metrics
        metrics = {r["key"]: r["score"] for r in result}
        assert metrics["situation_exact_match"] == 1.0
        assert metrics["situation_within_one"] == 1.0
        assert metrics["situation_distance"] == 0.0

    def test_off_by_one(self):
        """Off by 1 should return distance=1, exact_match=0, within_one=1"""
        evaluator = create_dimension_evaluator("problem")

        result = evaluator(
            outputs={"scores": {"problem": 3}},
            reference_outputs={"problem": 4}
        )

        metrics = {r["key"]: r["score"] for r in result}
        assert metrics["problem_exact_match"] == 0.0
        assert metrics["problem_within_one"] == 1.0
        assert metrics["problem_distance"] == 1.0

    def test_off_by_two(self):
        """Off by 2 should return distance=2, exact_match=0, within_one=0"""
        evaluator = create_dimension_evaluator("implication")

        result = evaluator(
            outputs={"scores": {"implication": 2}},
            reference_outputs={"implication": 4}
        )

        metrics = {r["key"]: r["score"] for r in result}
        assert metrics["implication_exact_match"] == 0.0
        assert metrics["implication_within_one"] == 0.0
        assert metrics["implication_distance"] == 2.0

    def test_missing_score_in_outputs(self):
        """Missing score in outputs should return error metric"""
        evaluator = create_dimension_evaluator("flow")

        result = evaluator(
            outputs={"scores": {}},  # Missing flow
            reference_outputs={"flow": 4}
        )

        assert len(result) == 1
        assert result[0]["key"] == "flow_error"
        assert result[0]["score"] == 0

    def test_missing_score_in_reference(self):
        """Missing score in reference should return error metric"""
        evaluator = create_dimension_evaluator("tone")

        result = evaluator(
            outputs={"scores": {"tone": 4}},
            reference_outputs={}  # Missing tone
        )

        assert len(result) == 1
        assert result[0]["key"] == "tone_error"
        assert result[0]["score"] == 0


class TestCreateSpinEvaluators:
    """Tests for evaluator factory function"""

    def test_creates_all_dimension_evaluators(self):
        """Should create evaluators for all 7 dimensions"""
        evaluators = create_spin_evaluators()

        assert len(evaluators) == 7
        assert all(callable(e) for e in evaluators)

    def test_evaluator_names(self):
        """Each evaluator should have descriptive name"""
        evaluators = create_spin_evaluators()
        names = [e.__name__ for e in evaluators]

        expected_names = [f"{dim}_evaluator" for dim in DIMENSIONS]
        assert names == expected_names


class TestSpinSummaryEvaluator:
    """Tests for summary evaluator (aggregate metrics)"""

    def test_perfect_predictions(self):
        """Perfect predictions should yield r=1, qwk=1, ±1acc=1"""
        # Mock runs with perfect predictions
        mock_runs = [
            Mock(outputs={"scores": {"situation": 4, "problem": 3}}),
            Mock(outputs={"scores": {"situation": 5, "problem": 4}})
        ]

        # Mock examples with matching ground truth
        mock_examples = [
            Mock(outputs={"situation": 4, "problem": 3}),
            Mock(outputs={"situation": 5, "problem": 4})
        ]

        result = spin_summary_evaluator(mock_runs, mock_examples)

        # Should return dict with "results" key
        assert "results" in result
        assert isinstance(result["results"], list)

        # Extract metrics
        metrics = {r["key"]: r["score"] for r in result["results"]}

        # Check situation metrics (perfect match)
        assert metrics["situation_pearson_r"] == pytest.approx(1.0, abs=1e-6)
        assert metrics["situation_qwk"] == pytest.approx(1.0, abs=1e-6)
        assert metrics["situation_plus_minus_one_accuracy"] == pytest.approx(1.0, abs=1e-6)

        # Check macro averages
        assert "macro_avg_pearson_r" in metrics
        assert "macro_avg_qwk" in metrics
        assert "macro_avg_plus_minus_one_accuracy" in metrics

    def test_varying_predictions(self):
        """Varying predictions should yield intermediate metrics"""
        # Mock runs with some variation
        mock_runs = [
            Mock(outputs={"scores": {"situation": 3, "problem": 3}}),
            Mock(outputs={"scores": {"situation": 4, "problem": 4}}),
            Mock(outputs={"scores": {"situation": 5, "problem": 5}})
        ]

        # Mock examples with some differences
        mock_examples = [
            Mock(outputs={"situation": 3, "problem": 4}),  # problem off by 1
            Mock(outputs={"situation": 4, "problem": 4}),  # perfect
            Mock(outputs={"situation": 5, "problem": 3})   # problem off by 2
        ]

        result = spin_summary_evaluator(mock_runs, mock_examples)
        metrics = {r["key"]: r["score"] for r in result["results"]}

        # Situation should be perfect (r=1)
        assert metrics["situation_pearson_r"] == pytest.approx(1.0, abs=1e-6)

        # Problem should have correlation (can be negative)
        assert -1.0 <= metrics["problem_pearson_r"] <= 1.0
        assert -1.0 <= metrics["problem_qwk"] <= 1.0

        # ±1 accuracy should be good (2 out of 3 within ±1)
        assert metrics["problem_plus_minus_one_accuracy"] == pytest.approx(0.667, abs=0.01)

    def test_constant_predictions(self):
        """Constant predictions should handle gracefully (no correlation possible)"""
        # All predictions are 3
        mock_runs = [
            Mock(outputs={"scores": {"situation": 3}}),
            Mock(outputs={"scores": {"situation": 3}}),
            Mock(outputs={"scores": {"situation": 3}})
        ]

        # Varying ground truth
        mock_examples = [
            Mock(outputs={"situation": 2}),
            Mock(outputs={"situation": 4}),
            Mock(outputs={"situation": 5})
        ]

        result = spin_summary_evaluator(mock_runs, mock_examples)
        metrics = {r["key"]: r["score"] for r in result["results"]}

        # Should only return ±1 accuracy (no correlation possible)
        assert "situation_plus_minus_one_accuracy" in metrics
        # No pearson_r or qwk when no variance
        assert "situation_pearson_r" not in metrics

    def test_empty_results(self):
        """Empty runs/examples should handle gracefully"""
        result = spin_summary_evaluator([], [])

        assert "results" in result
        assert isinstance(result["results"], list)
        # Should be empty or minimal results
        assert len(result["results"]) == 0

    def test_missing_dimension_in_outputs(self):
        """Missing dimensions should be skipped without failing"""
        mock_runs = [
            Mock(outputs={"scores": {"situation": 4}}),  # Missing other dims
            Mock(outputs={"scores": {"situation": 5}})
        ]

        mock_examples = [
            Mock(outputs={"situation": 4, "problem": 3, "flow": 4}),
            Mock(outputs={"situation": 5, "problem": 4, "flow": 5})
        ]

        result = spin_summary_evaluator(mock_runs, mock_examples)
        metrics = {r["key"]: r["score"] for r in result["results"]}

        # Situation should have metrics
        assert "situation_pearson_r" in metrics

        # Problem and flow should be skipped (no predictions)
        assert "problem_pearson_r" not in metrics
        assert "flow_pearson_r" not in metrics


class TestOverallQualityEvaluator:
    """Tests for overall quality evaluator"""

    def test_perfect_quality(self):
        """All exact matches should return quality=1.0"""
        result = overall_quality_evaluator(
            outputs={"scores": {
                "situation": 4, "problem": 3, "implication": 4,
                "need_payoff": 3, "flow": 4, "tone": 4, "engagement": 3
            }},
            reference_outputs={
                "situation": 4, "problem": 3, "implication": 4,
                "need_payoff": 3, "flow": 4, "tone": 4, "engagement": 3
            }
        )

        assert result["key"] == "overall_quality"
        assert result["score"] == pytest.approx(1.0, abs=1e-6)

    def test_poor_quality(self):
        """Large distances should return low quality"""
        result = overall_quality_evaluator(
            outputs={"scores": {
                "situation": 1, "problem": 1, "implication": 1,
                "need_payoff": 1, "flow": 1, "tone": 1, "engagement": 1
            }},
            reference_outputs={
                "situation": 5, "problem": 5, "implication": 5,
                "need_payoff": 5, "flow": 5, "tone": 5, "engagement": 5
            }
        )

        assert result["key"] == "overall_quality"
        # Max distance is 4, so quality should be 0.0
        assert result["score"] == pytest.approx(0.0, abs=1e-6)

    def test_medium_quality(self):
        """Medium distances should return intermediate quality"""
        result = overall_quality_evaluator(
            outputs={"scores": {
                "situation": 3, "problem": 3, "implication": 3,
                "need_payoff": 3, "flow": 3, "tone": 3, "engagement": 3
            }},
            reference_outputs={
                "situation": 4, "problem": 4, "implication": 4,
                "need_payoff": 4, "flow": 4, "tone": 4, "engagement": 4
            }
        )

        assert result["key"] == "overall_quality"
        # Average distance is 1, so quality = 1 - (1/4) = 0.75
        assert result["score"] == pytest.approx(0.75, abs=1e-6)

    def test_missing_scores(self):
        """Missing scores should return error"""
        result = overall_quality_evaluator(
            outputs={"scores": {}},
            reference_outputs={"situation": 4}
        )

        assert result["key"] == "overall_quality_error"
        assert result["score"] == 0
