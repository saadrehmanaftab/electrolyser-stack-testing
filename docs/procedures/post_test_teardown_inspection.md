# Post test teardown and inspection

Template for this project, not validated on hardware. Use it after the stack has been
disassembled (`stack_assembly_disassembly.md`, section 4). The goal is to confirm or reject the
root cause that the test data points to (`results/failure_analysis_report.md`).

## Workflow

1. Start with the cells flagged in the failure analysis report, then one healthy reference cell.
2. Inspect each component of the cell with the table below. Photograph before and after cleaning.
3. Compare every measurement with the begin of life value from the build sheet.
4. Write the root cause statement: what failed, the evidence in the data, the evidence at
   teardown, and the likely mechanism.

## Component inspection

| Component | What to look for | Measurement | Data signature it should match |
|---|---|---|---|
| Membrane | thinning, pinholes, discolouration, creep at the seal edge | thickness at 5 points, light table | ohmic loss rise, ASR increase |
| Electrodes | catalyst loss, delamination, cracking, contamination | mass loading by weighing, microscope | kinetic loss rise, i0 decrease |
| Seals | compression set, cuts, extrusion, chemical attack | thickness at 8 points vs begin of life | leak rate rise, contact ASR rise |
| Plates | corrosion, oxide layers, flow field blockage | visual, contact resistance if available | contact ASR rise |

## Root cause statement template

* Cell and position:
* Symptom in the test data (rate, loss breakdown, leak rate):
* Teardown finding:
* Root cause:
* Corrective action and owner:
