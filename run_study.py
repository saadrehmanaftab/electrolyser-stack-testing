"""End to end degradation study on a simulated 10 cell electrolyser stack.

    python run_study.py

Steps
 1. Build the stack: 10 cells with manufacturing scatter, three injected faults
 2. Pre test leak test on every cell
 3. Run the accelerated stress test (AST) on the virtual test stand
 4. Post test leak test on every cell
 5. Analyse the test data: degradation rates, BOL/EOL polarization fits,
    voltage loss breakdown, root cause per cell
 6. Check the analysis against the injected ground truth
 7. Process engineering: CO2 release rate and specific energy, BOL vs EOL
 8. Write figures, CSV data and a failure analysis report to results/
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from stacktest.analysis import classify_root_cause, degradation_rates, loss_breakdown  # noqa: E402
from stacktest.cell_model import CellParams, cell_voltage, overpotentials  # noqa: E402
from stacktest.degradation import DegradationRates, aged_params, leak_rate  # noqa: E402
from stacktest.leak_test import LeakTestSpec, evaluate, simulate_pressure_decay  # noqa: E402
from stacktest.process import co2_rate_kg_h, specific_energy_kwh_kg  # noqa: E402
from stacktest.test_stand import ASTProtocol, TestStand  # noqa: E402

OUT = Path(__file__).parent / "results"
N_CELLS, AREA_CM2, I_REF = 10, 100.0, 2.0
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7

# Faults injected for the study (cell number -> changed degradation rates)
FAULTS = {
    3: ("membrane", dict(k_membrane=8e-4)),
    6: ("electrode", dict(k_electrode=8e-5)),
    9: ("seal", dict(k_leak=4e-2, k_contact=6e-4)),
}

INK = "#1f2933"
MUTED = "#9aa5b1"
COLORS = {"membrane": "#c2410c", "electrode": "#1d4ed8", "seal": "#047857"}


def build_stack(rng):
    base = CellParams()
    cells = []
    for k in range(1, N_CELLS + 1):
        p = base.with_(i0=base.i0 * rng.normal(1, 0.10),
                       asr_membrane=base.asr_membrane * rng.normal(1, 0.05),
                       asr_contact=base.asr_contact * rng.normal(1, 0.05))
        d = DegradationRates()
        if k in FAULTS:
            d = DegradationRates(**{**d.__dict__, **FAULTS[k][1]})
        cells.append((p, d))
    return base, cells


def leak_campaign(cells, hours, spec, rng):
    rows, traces = [], {}
    for k, (_, d) in enumerate(cells, start=1):
        t, p = simulate_pressure_decay(leak_rate(d, hours), spec, rng)
        r = evaluate(t, p, spec)
        rows.append({"cell": k, **r})
        traces[k] = (t, p)
    return pd.DataFrame(rows), traces


def ground_truth(cells, protocol):
    hours = protocol.duration_h
    cycles = hours * protocol.cycles_per_hour
    out = []
    for k, (p, d) in enumerate(cells, start=1):
        e = aged_params(p, d, hours, cycles)
        ob, oe = overpotentials(I_REF, p), overpotentials(I_REF, e)
        out.append({"cell": k,
                    "true_dv_kinetic_mv": 1e3 * float(oe["activation"] - ob["activation"]),
                    "true_dv_ohmic_mv": 1e3 * float(oe["ohmic"] - ob["ohmic"]),
                    "true_cause": FAULTS.get(k, ("nominal ageing",))[0]})
    return pd.DataFrame(out)


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e4e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def figures(log, pol, breakdown, traces_pre, traces_post, spec):
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})
    fault_of = {k: v[0] for k, v in FAULTS.items()}

    # 1 per cell voltage at the high current level over the AST
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    hi = log[np.isclose(log["i_a_cm2"], I_REF)]
    for k in range(1, N_CELLS + 1):
        col = f"v_cell_{k:02d}"
        if k in fault_of:
            ax.plot(hi["hours"], hi[col], color=COLORS[fault_of[k]], lw=1.6)
            ax.annotate(f"cell {k}, {fault_of[k]}", (hi["hours"].iloc[-1], hi[col].iloc[-1]),
                        xytext=(6, 0), textcoords="offset points", va="center",
                        color=COLORS[fault_of[k]], fontsize=9)
        else:
            ax.plot(hi["hours"], hi[col], color=MUTED, lw=0.8)
    ax.set_xlabel("AST time (h)")
    ax.set_ylabel(f"cell voltage at {I_REF} A/cm² (V)")
    ax.set_title("Per cell voltage during the accelerated stress test", loc="left")
    ax.set_xlim(0, hi["hours"].max() * 1.22)
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_cell_voltage_ast.png", dpi=150)
    plt.close(fig)

    # 2 loss breakdown per cell
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    x = breakdown["cell"].values
    kin, ohm = breakdown["dv_kinetic_mv"].values, breakdown["dv_ohmic_mv"].values
    mt = breakdown["dv_mass_transport_mv"].values
    ax.bar(x, kin, color=COLORS["electrode"], label="kinetic (electrode)")
    ax.bar(x, ohm, bottom=kin, color=COLORS["membrane"], label="ohmic (membrane, contact)")
    if np.abs(mt).max() > 0.5:  # only drawn when i_lim is fitted
        ax.bar(x, mt, bottom=kin + ohm, color=MUTED, label="mass transport")
    ax.margins(y=0.1)
    ax.set_xticks(x)
    ax.set_xlabel("cell")
    ax.set_ylabel(f"voltage increase at {I_REF} A/cm², EOL vs BOL (mV)")
    ax.set_title("Voltage loss breakdown from polarization curve fits", loc="left")
    ax.legend(frameon=False, loc="upper right")
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_loss_breakdown.png", dpi=150)
    plt.close(fig)

    # 3 BOL vs EOL polarization curves of the faulty cells
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 3.4), sharey=True)
    t0, t1 = pol["hours"].min(), pol["hours"].max()
    for ax, (k, (cause, _)) in zip(axes, FAULTS.items()):
        g = pol[pol["cell"] == k]
        for t, ls, lab in ((t0, "--", "BOL"), (t1, "-", "EOL")):
            s = g[g["hours"] == t]
            ax.plot(s["i_a_cm2"], s["v_cell"], ls, marker="o", ms=3, color=COLORS[cause], label=lab)
        ax.set_title(f"cell {k}, {cause}", loc="left", color=COLORS[cause])
        ax.set_xlabel("current density (A/cm²)")
        style(ax)
    axes[0].set_ylabel("cell voltage (V)")
    axes[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_polarization_bol_eol.png", dpi=150)
    plt.close(fig)

    # 4 leak test pressure decay, seal fault cell vs a healthy cell
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for k, color in ((1, MUTED), (9, COLORS["seal"])):
        for tr, ls, lab in ((traces_pre, "--", "pre test"), (traces_post, "-", "post test")):
            t, p = tr[k]
            ax.plot(t, p, ls, color=color, lw=1.2, label=f"cell {k}, {lab}")
    ax.set_xlabel("hold time (s)")
    ax.set_ylabel("pressure (mbar g)")
    ax.set_title(f"Pressure decay leak test, limit {spec.limit_mbar_l_s:g} mbar L/s", loc="left")
    ax.legend(frameon=False, ncol=2)
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_leak_test.png", dpi=150)
    plt.close(fig)


def write_report(rates, rc, truth, leak_pre, events, proc):
    m = rc.merge(rates, on="cell").merge(truth, on="cell")
    lines = [
        "# Failure analysis report, simulated 10 cell stack",
        "",
        "Synthetic data from `run_study.py`. Every number below is regenerated on each run.",
        "",
        f"Test end: {events.iloc[-1]['event']} at {events.iloc[-1]['hours']:.0f} h ({events.iloc[-1]['detail']}).",
        f"Pre test leak check: {int(leak_pre['passed'].sum())} of {len(leak_pre)} cells passed.",
        "",
        "| cell | rate (uV/h) | dV kinetic (mV) | dV ohmic (mV) | leak EOL (mbar L/s) | root cause | injected |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]
    for _, r in m.iterrows():
        lines.append(f"| {r.cell} | {r.rate_uv_h:.0f} | {r.dv_kinetic_mv:.1f} | {r.dv_ohmic_mv:.1f} | "
                     f"{r.leak_eol_mbar_l_s:.2e} | {r.root_cause} | {r.true_cause} |")
    lines += [
        "",
        "## Process impact",
        "",
        f"CO2 release at {I_REF} A/cm²: {proc['co2_kg_h']:.2f} kg/h for the stack.",
        f"Specific energy: {proc['e_bol']:.3f} kWh/kg CO2 at BOL, {proc['e_eol']:.3f} kWh/kg at EOL "
        f"(+{100 * (proc['e_eol'] / proc['e_bol'] - 1):.1f} %).",
        "",
        "## Teardown actions",
        "",
        "Confirm each data based root cause physically with the post test teardown and "
        "inspection checklist in `docs/procedures/post_test_teardown_inspection.md`:",
        "",
    ]
    actions = {"seal": "inspect gasket for compression set, cuts and extrusion; measure thickness at 8 points",
               "membrane": "inspect membrane for thinning, pinholes and discolouration; measure thickness",
               "electrode": "inspect catalyst layer for delamination and loss; compare mass loading"}
    for _, r in m[m["root_cause"] != "nominal ageing"].iterrows():
        lines.append(f"* cell {r.cell}, {r.root_cause}: {actions[r.root_cause]}")
    (OUT / "failure_analysis_report.md").write_text("\n".join(lines) + "\n")
    return m


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    base, cells = build_stack(rng)
    spec, protocol = LeakTestSpec(), ASTProtocol()

    leak_pre, traces_pre = leak_campaign(cells, 0.0, spec, rng)
    if not leak_pre["passed"].all():
        raise SystemExit("pre test leak check failed, test not started")

    stand = TestStand(cells=cells, protocol=protocol, seed=SEED)
    log, pol, events = stand.run()
    leak_post, traces_post = leak_campaign(cells, protocol.duration_h, spec, rng)

    rates = degradation_rates(log, I_REF)
    breakdown = loss_breakdown(pol, base, I_REF)
    leaks = leak_post.rename(columns={"leak_rate_mbar_l_s": "leak_eol_mbar_l_s"})[["cell", "leak_eol_mbar_l_s"]]
    rc = classify_root_cause(breakdown, leaks, spec.limit_mbar_l_s)
    truth = ground_truth(cells, protocol)

    hi = log[np.isclose(log["i_a_cm2"], I_REF)]
    vcols = [c for c in log.columns if c.startswith("v_cell_")]
    v_bol, v_eol = hi[vcols].iloc[0].sum(), hi[vcols].iloc[-1].sum()
    proc = {"co2_kg_h": co2_rate_kg_h(I_REF, AREA_CM2, N_CELLS),
            "e_bol": specific_energy_kwh_kg(v_bol, I_REF, AREA_CM2, N_CELLS),
            "e_eol": specific_energy_kwh_kg(v_eol, I_REF, AREA_CM2, N_CELLS)}

    log.to_csv(OUT / "data" / "ast_log.csv", index=False)
    pol.to_csv(OUT / "data" / "polarization_curves.csv", index=False)
    pd.concat([leak_pre.assign(stage="pre"), leak_post.assign(stage="post")]).to_csv(
        OUT / "data" / "leak_tests.csv", index=False)
    figures(log, pol, breakdown, traces_pre, traces_post, spec)
    m = write_report(rates, rc, truth, leak_pre, events, proc)

    correct = int((m["root_cause"] == m["true_cause"]).sum())
    err_ohm = (m["dv_ohmic_mv"] - m["true_dv_ohmic_mv"]).abs().max()
    err_kin = (m["dv_kinetic_mv"] - m["true_dv_kinetic_mv"]).abs().max()
    print(m[["cell", "rate_uv_h", "dv_kinetic_mv", "dv_ohmic_mv", "leak_eol_mbar_l_s",
             "root_cause", "true_cause"]].round(4).to_string(index=False))
    print(f"\nroot cause correct: {correct} of {len(m)} cells")
    print(f"max error vs ground truth: ohmic {err_ohm:.1f} mV, kinetic {err_kin:.1f} mV")
    print(f"stack voltage at {I_REF} A/cm2: BOL {v_bol:.3f} V, EOL {v_eol:.3f} V")
    print(f"specific energy: BOL {proc['e_bol']:.3f}, EOL {proc['e_eol']:.3f} kWh/kg CO2, "
          f"CO2 {proc['co2_kg_h']:.2f} kg/h")
    print(f"test stand: {events.iloc[-1].to_dict()}")


if __name__ == "__main__":
    main()
