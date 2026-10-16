# Failure analysis report, simulated 10 cell stack

Synthetic data from `run_study.py`. Every number below is regenerated on each run.

Test end: END at 500 h (protocol completed).
Pre test leak check: 10 of 10 cells passed.

| cell | rate (uV/h) | dV kinetic (mV) | dV ohmic (mV) | leak EOL (mbar L/s) | root cause | injected |
|---:|---:|---:|---:|---:|---|---|
| 1 | 47 | 9.8 | 14.3 | 1.01e-03 | nominal ageing | nominal ageing |
| 2 | 47 | 11.6 | 10.3 | 9.99e-04 | nominal ageing | nominal ageing |
| 3 | 199 | 11.2 | 87.4 | 1.02e-03 | membrane | membrane |
| 4 | 48 | 9.4 | 15.3 | 9.93e-04 | nominal ageing | nominal ageing |
| 5 | 47 | 7.9 | 15.7 | 1.00e-03 | nominal ageing | nominal ageing |
| 6 | 166 | 68.0 | 14.5 | 1.02e-03 | electrode | electrode |
| 7 | 45 | 7.8 | 13.7 | 9.93e-04 | nominal ageing | nominal ageing |
| 8 | 47 | 9.5 | 13.3 | 1.03e-03 | nominal ageing | nominal ageing |
| 9 | 89 | 9.3 | 36.3 | 1.05e-02 | seal | seal |
| 10 | 48 | 9.4 | 16.1 | 1.01e-03 | nominal ageing | nominal ageing |

## Process impact

CO2 release at 2.0 A/cm²: 2.96 kg/h for the stack.
Specific energy: 1.345 kWh/kg CO2 at BOL, 1.371 kWh/kg at EOL (+2.0 %).

## Teardown actions

Confirm each data based root cause physically with the post test teardown and inspection checklist in `docs/procedures/post_test_teardown_inspection.md`:

* cell 3, membrane: inspect membrane for thinning, pinholes and discolouration; measure thickness
* cell 6, electrode: inspect catalyst layer for delamination and loss; compare mass loading
* cell 9, seal: inspect gasket for compression set, cuts and extrusion; measure thickness at 8 points
