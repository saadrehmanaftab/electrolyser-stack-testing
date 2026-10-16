"""Virtual test stand that runs an accelerated stress test (AST) protocol.

The protocol is a square wave between a low and a high current density with
periodic polarization curves for diagnosis. The stand logs per cell voltages
at every logging interval, checks safety limits on every sample and trips
to a safe state if a limit is exceeded, as a real stand interlock would.

All data produced here is synthetic. Sensor noise is added so that the
analysis code has to work on data that looks like a real test log.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .cell_model import CellParams, cell_voltage
from .degradation import DegradationRates, aged_params


@dataclass(frozen=True)
class ASTProtocol:
    i_low: float = 0.2              # A/cm2
    i_high: float = 2.0             # A/cm2
    half_cycle_s: float = 60.0      # dwell at each level
    duration_h: float = 500.0
    log_every_h: float = 1.0
    polcurve_every_h: float = 250.0
    polcurve_points: tuple = (0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5)

    @property
    def cycles_per_hour(self) -> float:
        return 3600.0 / (2.0 * self.half_cycle_s)


@dataclass(frozen=True)
class SafetyLimits:
    v_cell_max: float = 2.40        # V, trip if any cell exceeds this
    v_cell_min: float = 1.20        # V, trip on reversal or short
    temp_max_c: float = 70.0


@dataclass
class TestStand:
    cells: list                     # list of (CellParams, DegradationRates)
    protocol: ASTProtocol = field(default_factory=ASTProtocol)
    limits: SafetyLimits = field(default_factory=SafetyLimits)
    v_noise: float = 0.002          # V, voltage sensing noise
    temp_set_c: float = 60.0
    seed: int = 1

    def _state(self, hours):
        cycles = hours * self.protocol.cycles_per_hour
        return [aged_params(p, d, hours, cycles) for p, d in self.cells]

    def run(self):
        """Run the AST. Returns (time series log, polarization curves, events)."""
        rng = np.random.default_rng(self.seed)
        pr, lim = self.protocol, self.limits
        n = len(self.cells)
        rows, pol, events = [], [], []
        hours = np.arange(0.0, pr.duration_h + 1e-9, pr.log_every_h)
        for h in hours:
            params = self._state(h)
            if h % pr.polcurve_every_h < 1e-9:
                for k, p in enumerate(params):
                    for i in pr.polcurve_points:
                        v = float(cell_voltage(i, p)) + rng.normal(0, self.v_noise)
                        pol.append({"hours": h, "cell": k + 1, "i_a_cm2": i, "v_cell": v})
            temp = self.temp_set_c + rng.normal(0, 0.3)
            for i in (pr.i_low, pr.i_high):
                v = np.array([float(cell_voltage(i, p)) for p in params]) + rng.normal(0, self.v_noise, n)
                rows.append({"hours": h, "i_a_cm2": i, "temp_c": temp,
                             **{f"v_cell_{k + 1:02d}": v[k] for k in range(n)}})
                bad = np.where((v > lim.v_cell_max) | (v < lim.v_cell_min))[0]
                if bad.size or temp > lim.temp_max_c:
                    events.append({"hours": h, "event": "TRIP",
                                   "detail": f"limit exceeded, cells {list(bad + 1)}, T={temp:.1f} C"})
                    return pd.DataFrame(rows), pd.DataFrame(pol), pd.DataFrame(events)
        events.append({"hours": float(hours[-1]), "event": "END", "detail": "protocol completed"})
        return pd.DataFrame(rows), pd.DataFrame(pol), pd.DataFrame(events)
