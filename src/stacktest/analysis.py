"""Analysis of AST test data: degradation rates, polarization curve fits,
voltage loss breakdown and a rule based root cause classification.
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .cell_model import CellParams, overpotentials


def degradation_rates(log: pd.DataFrame, i_ref: float) -> pd.DataFrame:
    """Voltage degradation rate of every cell at the reference current, in uV/h,
    from a least squares line through all logged points at that current."""
    d = log[np.isclose(log["i_a_cm2"], i_ref)]
    out = []
    for col in [c for c in d.columns if c.startswith("v_cell_")]:
        slope, v0 = np.polyfit(d["hours"], d[col], 1)
        out.append({"cell": int(col[-2:]), "v_bol": v0, "rate_uv_h": slope * 1e6})
    return pd.DataFrame(out)


def fit_polcurve(i, v, base: CellParams, fit_ilim: bool = False) -> CellParams:
    """Fit i0 and total ASR (and optionally i_lim) to one polarization curve.

    E_rev, Tafel slope (temperature) and the mass transport coefficient are
    held at their known values. i0 is fitted in log space for conditioning.
    i_lim is held fixed by default: with points only up to 2.5 A/cm2 it
    trades off against the ASR and inflates the ohmic scatter (see README).
    The fitted total ASR is stored as membrane ASR with zero contact ASR,
    because a polarization curve alone cannot separate the two.
    """
    def model(i, log_i0, asr, i_lim):
        p = base.with_(i0=10 ** log_i0, asr_membrane=asr, asr_contact=0.0, i_lim=i_lim)
        ov = overpotentials(i, p)
        return p.e_rev + ov["activation"] + ov["ohmic"] + ov["mass_transport"]

    i, v = np.asarray(i), np.asarray(v)
    if fit_ilim:
        x0 = (np.log10(base.i0), base.asr_total, base.i_lim)
        bounds = ([-6, 0.01, max(i) * 1.02], [0, 1.0, 10.0])
        popt, _ = curve_fit(model, i, v, p0=x0, bounds=bounds)
        i_lim = popt[2]
    else:
        f2 = lambda i, a, b: model(i, a, b, base.i_lim)  # noqa: E731
        popt, _ = curve_fit(f2, i, v, p0=(np.log10(base.i0), base.asr_total),
                            bounds=([-6, 0.01], [0, 1.0]))
        i_lim = base.i_lim
    return base.with_(i0=10 ** popt[0], asr_membrane=popt[1], asr_contact=0.0, i_lim=i_lim)


def loss_breakdown(pol: pd.DataFrame, base: CellParams, i_ref: float,
                   fit_ilim: bool = False) -> pd.DataFrame:
    """Fit begin of life and end of life curves of every cell and split the
    voltage increase at i_ref into kinetic, ohmic and mass transport parts."""
    t0, t1 = pol["hours"].min(), pol["hours"].max()
    out = []
    for cell, g in pol.groupby("cell"):
        fits = {}
        for tag, t in (("bol", t0), ("eol", t1)):
            s = g[g["hours"] == t]
            fits[tag] = fit_polcurve(s["i_a_cm2"].values, s["v_cell"].values, base, fit_ilim)
        ob = overpotentials(i_ref, fits["bol"])
        oe = overpotentials(i_ref, fits["eol"])
        out.append({
            "cell": cell,
            "asr_bol": fits["bol"].asr_membrane, "asr_eol": fits["eol"].asr_membrane,
            "i0_bol": fits["bol"].i0, "i0_eol": fits["eol"].i0,
            "dv_kinetic_mv": 1e3 * float(oe["activation"] - ob["activation"]),
            "dv_ohmic_mv": 1e3 * float(oe["ohmic"] - ob["ohmic"]),
            "dv_mass_transport_mv": 1e3 * float(oe["mass_transport"] - ob["mass_transport"]),
        })
    return pd.DataFrame(out)


def classify_root_cause(breakdown: pd.DataFrame, leaks: pd.DataFrame,
                        leak_limit: float, factor: float = 3.0) -> pd.DataFrame:
    """Rule based root cause per cell.

    1. Post test leak rate above the limit            -> seal
    2. Ohmic increase above factor x stack median     -> membrane (or contact)
    3. Kinetic increase above factor x stack median   -> electrode
    4. Otherwise                                      -> nominal ageing
    Rules are checked in this order because a failed seal also loses
    compression and therefore raises the contact (ohmic) resistance.
    """
    df = breakdown.merge(leaks, on="cell")
    med_ohm = df["dv_ohmic_mv"].median()
    med_kin = df["dv_kinetic_mv"].median()
    causes = []
    for _, r in df.iterrows():
        if r["leak_eol_mbar_l_s"] > leak_limit:
            causes.append("seal")
        elif r["dv_ohmic_mv"] > factor * med_ohm:
            causes.append("membrane")
        elif r["dv_kinetic_mv"] > factor * med_kin:
            causes.append("electrode")
        else:
            causes.append("nominal ageing")
    df["root_cause"] = causes
    return df
