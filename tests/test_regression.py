import pytest

from src.api.services.regression_service import _classify_change, _percentage_change


class TestPercentageChange:
    def test_increase(self):
        result = _percentage_change(current=1.2, baseline=1.0)
        assert result == pytest.approx(20.0)

    def test_decrease(self):
        result = _percentage_change(current=0.8, baseline=1.0)
        assert result == pytest.approx(-20.0)

    def test_no_change(self):
        result = _percentage_change(current=1.0, baseline=1.0)
        assert result == pytest.approx(0.0)

    def test_baseline_zero_returns_none(self):
        assert _percentage_change(current=1.0, baseline=0) is None

    def test_baseline_none_returns_none(self):
        assert _percentage_change(current=1.0, baseline=None) is None

    def test_current_none_returns_none(self):
        assert _percentage_change(current=None, baseline=1.0) is None

    def test_both_none_returns_none(self):
        assert _percentage_change(current=None, baseline=None) is None


class TestClassifyChange:
    """Test that the time-based regression/improvement classification is correct."""

    THRESHOLD = 5.0

    def _classify(self, baseline: float, target: float) -> tuple[bool, bool]:
        change = _percentage_change(current=target, baseline=baseline)
        return _classify_change(change, self.THRESHOLD)

    def test_small_time_increase_not_regression(self):
        is_regression, _ = self._classify(baseline=1.0, target=1.03)
        assert not is_regression

    def test_large_time_increase_is_regression(self):
        is_regression, _ = self._classify(baseline=1.0, target=1.20)
        assert is_regression

    def test_time_just_below_threshold_not_regression(self):
        is_regression, _ = self._classify(baseline=1.0, target=1.049)
        assert not is_regression

    def test_time_above_threshold_is_regression(self):
        is_regression, _ = self._classify(baseline=1.0, target=1.051)
        assert is_regression

    def test_large_time_decrease_is_improvement(self):
        is_regression, is_improvement = self._classify(baseline=1.0, target=0.80)
        assert is_improvement and not is_regression

    def test_small_time_decrease_not_improvement(self):
        _, is_improvement = self._classify(baseline=1.0, target=0.97)
        assert not is_improvement

    def test_regression_and_improvement_mutually_exclusive(self):
        is_regression, is_improvement = self._classify(baseline=1.0, target=1.20)
        assert is_regression and not is_improvement

    def test_none_change_is_neither(self):
        is_regression, is_improvement = _classify_change(None, self.THRESHOLD)
        assert not is_regression and not is_improvement
