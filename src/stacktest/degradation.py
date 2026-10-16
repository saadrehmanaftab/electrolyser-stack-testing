"""Degradation laws for the three stack components studied.

Each cell carries its own rates, so a single faulty cell can be injected
into an otherwise healthy stack.

    membrane   ASR grows linearly with operating hours (thinning, contamination)
    electrode  exchange current density decays with load cycles (catalyst loss)
    seal       compression set: leak rate and contact ASR grow with hours

The laws are deliberately simple so the fitted parameters can be checked
against the injected ones. They are not calibrated to a real stack.
"""
from dataclasses import dataclass

import numpy as np

from .cell_model import CellParams


@dataclass(frozen=True)
class DegradationRates:
    k_membrane: float = 1.0e-4    # relative membrane ASR growth per hour
    k_electrode: float = 1.0e-5   # i0 decay constant per load cycle
    k_contact: float = 1.0e-4     # relative contact ASR growth per hour
    leak0: float = 5.0e-4         # leak rate at begin of life, mbar L/s
    k_leak: float = 2.0e-3        # relative leak growth per hour


def aged_params(p0: CellParams, d: DegradationRates, hours: float, cycles: float) -> CellParams:
    """Cell parameters after a given number of hours and load cycles."""
    return p0.with_(
        asr_membrane=p0.asr_membrane * (1.0 + d.k_membrane * hours),
        i0=p0.i0 * np.exp(-d.k_electrode * cycles),
        asr_contact=p0.asr_contact * (1.0 + d.k_contact * hours),
    )


def leak_rate(d: DegradationRates, hours: float) -> float:
    """True leak rate of the cell seals after a given number of hours."""
    return d.leak0 * (1.0 + d.k_leak * hours)
