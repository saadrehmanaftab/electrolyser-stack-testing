"""Steady state polarization model of one membrane electrolyser cell.

Cell voltage is the sum of four terms:

    V = E_rev + eta_act + eta_ohm + eta_mt

    eta_act  activation overpotential, symmetric Butler Volmer (asinh form)
    eta_ohm  ohmic loss, i * (membrane ASR + contact ASR)
    eta_mt   mass transport loss, -c * ln(1 - i / i_lim)

Current density i is in A/cm2, area specific resistance (ASR) in ohm cm2,
voltages in V. Default values are illustrative textbook numbers for a membrane
electrolyser at 60 degC, not data from any real product.
"""
from dataclasses import dataclass, replace

import numpy as np

F = 96485.0      # Faraday constant, C/mol
R = 8.314        # gas constant, J/(mol K)


@dataclass(frozen=True)
class CellParams:
    e_rev: float = 1.23          # reversible voltage, V
    temp_k: float = 333.15       # cell temperature, K
    alpha: float = 0.5           # charge transfer coefficient
    i0: float = 1.0e-3           # exchange current density, A/cm2 (electrode)
    asr_membrane: float = 0.10   # membrane ASR, ohm cm2
    asr_contact: float = 0.05    # contact ASR, ohm cm2 (depends on seal compression)
    c_mt: float = 0.03           # mass transport coefficient, V
    i_lim: float = 3.5           # limiting current density, A/cm2

    @property
    def tafel_b(self) -> float:
        """Tafel coefficient b = RT / (alpha F), in V."""
        return R * self.temp_k / (self.alpha * F)

    @property
    def asr_total(self) -> float:
        return self.asr_membrane + self.asr_contact

    def with_(self, **kw) -> "CellParams":
        return replace(self, **kw)


def overpotentials(i, p: CellParams) -> dict:
    """Return each loss term separately (useful for a loss breakdown)."""
    i = np.asarray(i, dtype=float)
    if np.any(i >= p.i_lim):
        raise ValueError("current density at or above the limiting current")
    act = p.tafel_b * np.arcsinh(i / (2.0 * p.i0))
    ohm = i * p.asr_total
    mt = -p.c_mt * np.log(1.0 - i / p.i_lim)
    return {"activation": act, "ohmic": ohm, "mass_transport": mt}


def cell_voltage(i, p: CellParams):
    ov = overpotentials(i, p)
    return p.e_rev + ov["activation"] + ov["ohmic"] + ov["mass_transport"]
