"""Pressure decay leak test, run before and after every durability test.

The cell (or stack) is pressurised with inert gas, isolated, and the
pressure is logged during a hold. For a small leak the decay is linear:

    Q = V * dP/dt      Q in mbar L/s, V in L, dP/dt in mbar/s

The slope is estimated by least squares so sensor noise is averaged out.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LeakTestSpec:
    p_start_mbar: float = 500.0     # test overpressure
    hold_s: float = 600.0           # hold time
    sample_s: float = 5.0           # logging interval
    volume_l: float = 0.05          # gas volume of one isolated cell
    noise_mbar: float = 0.5         # pressure sensor noise (1 sigma)
    limit_mbar_l_s: float = 5.0e-3  # acceptance limit


def simulate_pressure_decay(q_true: float, spec: LeakTestSpec, rng: np.random.Generator):
    t = np.arange(0.0, spec.hold_s + spec.sample_s, spec.sample_s)
    p = spec.p_start_mbar - q_true / spec.volume_l * t
    return t, p + rng.normal(0.0, spec.noise_mbar, t.size)


def evaluate(t, p, spec: LeakTestSpec) -> dict:
    slope, _ = np.polyfit(t, p, 1)
    q = -slope * spec.volume_l
    return {"leak_rate_mbar_l_s": q, "passed": bool(q <= spec.limit_mbar_l_s)}
