"""The material tester must reach every peak of a cyclic protocol."""

from __future__ import annotations

import numpy as np
import openseespy.opensees as ops
import pytest

from apeSees.materials import Steel02
from apeSees.timeseries import ASCE41Protocol, FEMA461Protocol, ModifiedATC24Protocol

pytestmark = pytest.mark.skipif(
    not hasattr(ops, "wipe"), reason="needs a working openseespy (stand-in registered)"
)

PROTOCOLS = [
    FEMA461Protocol(tag=2, max_disp=0.03),
    ASCE41Protocol(tag=2, max_disp=0.03),
    ModifiedATC24Protocol(tag=2, max_disp=0.03),
]


def _assert_every_peak_reached(ts, result, rtol: float = 0.01) -> None:
    t, d = ts.time, ts.disp
    for k in range(1, len(d) - 1):  # every reversal vertex
        window = (result.time >= t[k - 1] - 1e-12) & (result.time <= t[k + 1] + 1e-12)
        reached = np.abs(result.strain[window]).max(initial=0.0)
        assert reached >= (1.0 - rtol) * abs(d[k]), (
            f"{type(ts).__name__}: peak {k} = {d[k]:.4g} sampled at {reached:.4g}"
        )


# 100 is run()'s default, 500 plot()'s and 1000 Material.cyclic_tester()'s.
@pytest.mark.parametrize("number_of_points", [None, 500, 1000])
@pytest.mark.parametrize("ts", PROTOCOLS, ids=lambda ts: type(ts).__name__)
def test_run_reaches_every_peak(ts, number_of_points) -> None:
    tester = Steel02(1, 420.0, 200000.0, 0.01).tester
    kw = {} if number_of_points is None else {"number_of_points": number_of_points}
    result = tester.run(ts, **kw)

    assert result.converged
    _assert_every_peak_reached(ts, result)
