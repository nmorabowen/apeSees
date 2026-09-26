"""FEMA461Protocol must follow FEMA 461 §2.2.

The loading history is two cycles at each amplitude, amplitudes growing by
about 1.4x per step, ending at the requested ``max_disp``.
"""

from __future__ import annotations

import numpy as np
import pytest

from apeSees.timeseries import FEMA461Protocol


def _ladder(disp: np.ndarray) -> list[tuple[float, int]]:
    """Return ``[(amplitude, cycles), ...]`` from a ``[0, +a, -a, ..., 0]`` history."""
    assert disp[0] == 0.0 and disp[-1] == 0.0
    peaks = disp[1:-1]
    pos, neg = peaks[0::2], peaks[1::2]
    np.testing.assert_allclose(neg, -pos)  # every cycle is fully reversed
    ladder: list[tuple[float, int]] = []
    for a in pos:
        if ladder and np.isclose(a, ladder[-1][0], rtol=1e-9, atol=0.0):
            ladder[-1] = (ladder[-1][0], ladder[-1][1] + 1)
        else:
            ladder.append((float(a), 1))
    return ladder


@pytest.mark.parametrize("max_disp", [1.0, 0.02, 3.7])
def test_reaches_max_disp(max_disp: float) -> None:
    ts = FEMA461Protocol(tag=1, max_disp=max_disp)

    assert np.abs(ts.disp).max() == pytest.approx(max_disp)
    assert _ladder(ts.disp)[-1][0] == pytest.approx(max_disp)


@pytest.mark.parametrize("alpha", [0.4, 0.62])
def test_two_cycles_per_amplitude(alpha: float) -> None:
    ts = FEMA461Protocol(tag=1, max_disp=0.02, alpha=alpha)

    assert {n for _, n in _ladder(ts.disp)} == {2}


def test_default_growth_ratio_is_1_4() -> None:
    ts = FEMA461Protocol(tag=1, max_disp=0.02)
    amps = np.array([a for a, _ in _ladder(ts.disp)])
    ratios = amps[1:] / amps[:-1]

    assert amps[0] == pytest.approx(0.01 * 0.02)  # starts at 1% of max_disp
    np.testing.assert_allclose(ratios[:-1], 1.4)
    # The last step lands on max_disp, so it may be shorter, never longer.
    assert 1.0 < ratios[-1] <= 1.4 + 1e-12


def test_time_is_normalized_constant_slope() -> None:
    ts = FEMA461Protocol(tag=1, max_disp=0.02)

    assert ts.time[0] == 0.0 and ts.time[-1] == pytest.approx(1.0)
    rate = np.abs(np.diff(ts.disp)) / np.diff(ts.time)
    np.testing.assert_allclose(rate, rate[0])
