"""
Tests for evaluation metrics.

Tests Pearson correlation, Quadratic Weighted Kappa (QWK),
and ±1 band accuracy using synthetic data with known properties.
"""

import pytest
from app.services.evaluation_metrics import pearson_r, quadratic_weighted_kappa, plus_minus_one_accuracy


class TestPearsonCorrelation:
    """Tests for Pearson correlation coefficient calculation"""

    def test_perfect_positive_correlation(self):
        """Perfect linear correlation should return r=1.0"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1, 2, 3, 4, 5]
        r = pearson_r(y_true, y_pred)
        assert r == pytest.approx(1.0, abs=1e-6)

    def test_perfect_negative_correlation(self):
        """Perfect inverse linear correlation should return r=-1.0"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [5, 4, 3, 2, 1]
        r = pearson_r(y_true, y_pred)
        assert r == pytest.approx(-1.0, abs=1e-6)

    def test_no_correlation(self):
        """No correlation should return r≈0"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [3, 3, 3, 3, 3]  # constant prediction
        r = pearson_r(y_true, y_pred)
        # When one array has zero variance, correlation is undefined
        # We expect the function to return 0.0 in this case
        assert r == pytest.approx(0.0, abs=1e-6)

    def test_partial_correlation(self):
        """Partial correlation should return intermediate r value"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [2, 2, 3, 4, 4]  # somewhat correlated
        r = pearson_r(y_true, y_pred)
        assert 0.5 < r < 1.0  # should be positive and strong

    def test_empty_arrays(self):
        """Empty arrays should raise ValueError"""
        with pytest.raises(ValueError, match="at least one element"):
            pearson_r([], [])

    def test_mismatched_lengths(self):
        """Arrays of different lengths should raise ValueError"""
        with pytest.raises(ValueError, match="same length"):
            pearson_r([1, 2, 3], [1, 2])

    def test_single_element(self):
        """Single element arrays should return 0.0"""
        r = pearson_r([3], [3])
        assert r == pytest.approx(0.0, abs=1e-6)


class TestQuadraticWeightedKappa:
    """Tests for Quadratic Weighted Kappa calculation"""

    def test_perfect_agreement(self):
        """Perfect agreement should return QWK=1.0"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1, 2, 3, 4, 5]
        qwk = quadratic_weighted_kappa(y_true, y_pred)
        assert qwk == pytest.approx(1.0, abs=1e-6)

    def test_no_agreement(self):
        """Random agreement should return QWK≈0 or negative"""
        y_true = [1, 1, 1, 1, 1]
        y_pred = [5, 5, 5, 5, 5]  # maximum distance
        qwk = quadratic_weighted_kappa(y_true, y_pred)
        assert qwk < 0.5  # should be poor agreement

    def test_moderate_agreement(self):
        """Close predictions should return positive QWK"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [2, 2, 3, 4, 4]  # off by ±1 in some cases
        qwk = quadratic_weighted_kappa(y_true, y_pred)
        assert 0.5 < qwk < 1.0  # should be good but not perfect

    def test_off_by_one_still_decent(self):
        """Predictions off by 1 should still have decent agreement"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [2, 3, 4, 5, 5]  # mostly off by 1
        qwk = quadratic_weighted_kappa(y_true, y_pred)
        assert qwk > 0.5  # quadratic weighting is lenient for small errors

    def test_empty_arrays(self):
        """Empty arrays should raise ValueError"""
        with pytest.raises(ValueError, match="at least one element"):
            quadratic_weighted_kappa([], [])

    def test_mismatched_lengths(self):
        """Arrays of different lengths should raise ValueError"""
        with pytest.raises(ValueError, match="same length"):
            quadratic_weighted_kappa([1, 2, 3], [1, 2])

    def test_constant_predictions_perfect_agreement(self):
        """All same predictions matching ground truth should return QWK=1.0"""
        y_true = [3, 3, 3, 3]
        y_pred = [3, 3, 3, 3]
        qwk = quadratic_weighted_kappa(y_true, y_pred)
        assert qwk == pytest.approx(1.0, abs=1e-6)


class TestPlusMinusOneAccuracy:
    """Tests for ±1 band accuracy calculation"""

    def test_perfect_match(self):
        """All exact matches should return 100% accuracy"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1, 2, 3, 4, 5]
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(1.0, abs=1e-6)

    def test_all_within_one(self):
        """All predictions within ±1 should return 100% accuracy"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [2, 2, 3, 4, 4]  # off by ±1 or exact
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(1.0, abs=1e-6)

    def test_partial_within_one(self):
        """Mix of within and outside ±1 should return fraction"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1, 2, 5, 4, 5]  # 3->5 is off by 2, others are good
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(0.8, abs=1e-6)  # 4 out of 5

    def test_none_within_one(self):
        """No predictions within ±1 should return 0% accuracy"""
        y_true = [1, 2, 3, 4, 5]
        y_pred = [5, 5, 5, 1, 1]  # all off by 2+
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(0.0, abs=1e-6)

    def test_empty_arrays(self):
        """Empty arrays should raise ValueError"""
        with pytest.raises(ValueError, match="at least one element"):
            plus_minus_one_accuracy([], [])

    def test_mismatched_lengths(self):
        """Arrays of different lengths should raise ValueError"""
        with pytest.raises(ValueError, match="same length"):
            plus_minus_one_accuracy([1, 2, 3], [1, 2])

    def test_off_by_two_boundary(self):
        """Edge case: exactly 2 away should not count"""
        y_true = [1, 2, 3]
        y_pred = [3, 4, 1]  # off by 2 for each
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(0.0, abs=1e-6)

    def test_off_by_one_boundary(self):
        """Edge case: exactly 1 away should count"""
        y_true = [1, 2, 3]
        y_pred = [2, 3, 4]  # off by 1 for each
        acc = plus_minus_one_accuracy(y_true, y_pred)
        assert acc == pytest.approx(1.0, abs=1e-6)
