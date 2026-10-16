"""Process engineering view: CO2 release rate and specific energy.

For an electrolyser that releases CO2 from a captured (bicarbonate) state by
proton generation, each transferred electron releases about one CO2
molecule, so per cell

    n_CO2 = FE * I / (z F)        mol/s, z = 1 electron per CO2

The stack cells are in series, so every cell carries the same current and
the stack releases N times the single cell rate. z and the Faradaic
efficiency FE are inputs; change them for another chemistry.
"""
from .cell_model import F

M_CO2 = 44.01e-3  # kg/mol


def co2_rate_kg_h(i_a_cm2, area_cm2, n_cells, fe=0.9, z=1.0):
    current = i_a_cm2 * area_cm2
    return fe * current / (z * F) * n_cells * M_CO2 * 3600.0


def specific_energy_kwh_kg(v_stack, i_a_cm2, area_cm2, n_cells, fe=0.9, z=1.0):
    power_kw = v_stack * i_a_cm2 * area_cm2 / 1e3
    return power_kw / co2_rate_kg_h(i_a_cm2, area_cm2, n_cells, fe, z)
