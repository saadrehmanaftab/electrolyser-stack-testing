import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from stacktest.analysis import classify_root_cause, fit_polcurve  # noqa: E402
from stacktest.cell_model import CellParams, cell_voltage  # noqa: E402
from stacktest.degradation import DegradationRates, aged_params, leak_rate  # noqa: E402
from stacktest.leak_test import LeakTestSpec, evaluate, simulate_pressure_decay  # noqa: E402
from stacktest.process import co2_rate_kg_h  # noqa: E402
from stacktest.test_stand import SafetyLimits, TestStand, ASTProtocol  # noqa: E402


def test_voltage_rises_with_current():
    i = np.linspace(0.05, 2.5, 30)
    v = cell_voltage(i, CellParams())
    assert np.all(np.diff(v) > 0)
    assert 1.8 < cell_voltage(2.0, CellParams()) < 2.2


def test_limiting_current_rejected():
    with pytest.raises(ValueError):
        cell_voltage(3.6, CellParams())


def test_fit_recovers_known_parameters():
    p = CellParams().with_(i0=4e-4, asr_membrane=0.18, asr_contact=0.0)
    i = np.array(ASTProtocol().polcurve_points)
    fit = fit_polcurve(i, cell_voltage(i, p), CellParams())
    assert fit.asr_membrane == pytest.approx(0.18, rel=1e-3)
    assert fit.i0 == pytest.approx(4e-4, rel=1e-2)


def test_ageing_increases_voltage():
    p0, d = CellParams(), DegradationRates()
    assert cell_voltage(2.0, aged_params(p0, d, 500, 15000)) > cell_voltage(2.0, p0)
    assert leak_rate(d, 500) > leak_rate(d, 0)


def test_leak_test_pass_and_fail():
    spec, rng = LeakTestSpec(), np.random.default_rng(0)
    for q, ok in ((1e-3, True), (2e-2, False)):
        t, p = simulate_pressure_decay(q, spec, rng)
        r = evaluate(t, p, spec)
        assert r["passed"] is ok
        assert r["leak_rate_mbar_l_s"] == pytest.approx(q, rel=0.15)


def test_safety_interlock_trips():
    bad = (CellParams().with_(asr_membrane=0.5), DegradationRates())
    stand = TestStand(cells=[bad], limits=SafetyLimits(v_cell_max=2.0),
                      protocol=ASTProtocol(duration_h=10))
    _, _, events = stand.run()
    assert events.iloc[-1]["event"] == "TRIP"


def test_root_cause_rules():
    bd = pd.DataFrame({"cell": [1, 2, 3, 4], "dv_kinetic_mv": [8, 8, 60, 8],
                       "dv_ohmic_mv": [10, 80, 10, 30], "dv_mass_transport_mv": 0})
    lk = pd.DataFrame({"cell": [1, 2, 3, 4], "leak_eol_mbar_l_s": [1e-3, 1e-3, 1e-3, 1e-2]})
    rc = classify_root_cause(bd, lk, leak_limit=5e-3)
    assert list(rc["root_cause"]) == ["nominal ageing", "membrane", "electrode", "seal"]


def test_co2_rate_faraday():
    # 1 cell, 100 A, FE 1, z 1 -> 100/96485 mol/s
    assert co2_rate_kg_h(1.0, 100.0, 1, fe=1.0) == pytest.approx(100 / 96485 * 0.04401 * 3600)
