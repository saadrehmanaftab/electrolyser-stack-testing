# Procedure: assemble and disassemble an electrolyser stack

Template procedure written for this project from public practice for membrane
electrolyser and fuel cell stacks. It has not been validated on hardware. Torque
values, compression targets and materials are placeholders to be replaced by the
stack design documentation.

## 1. Safety

* PPE: safety glasses, nitrile gloves, safety shoes. Lab coat when handling electrolyte.
* Stack disconnected from power, gas and liquid lines, and depressurised. Lock out the test stand.
* Electrolyte wetted parts are rinsed before handling. Follow the SDS of the electrolyte.
* Two people or a lifting aid for stacks above 15 kg.

## 2. Inspect components before you assemble

Record every result in the build sheet (section 5).

| Component | Inspection | Accept if |
|---|---|---|
| Membrane | visual on a light table, thickness at 5 points | no pinholes, creases or contamination; thickness within spec |
| Electrodes | visual, mass loading by weighing | no delamination or cracks; loading within spec |
| Seals and gaskets | visual, thickness at 8 points | no cuts, no flash, no compression set |
| Bipolar plates, flow fields | visual, flatness | no corrosion, no burrs, flat within spec |
| End plates, tie rods | visual, thread condition | clean threads, no deformation |

## 3. Assemble

1. Place the end plate and insulator on the alignment fixture.
2. Stack each repeat unit in order: plate, seal, electrode, membrane, electrode, seal, plate.
   Check the orientation marks and the manifold alignment of every layer.
3. Record each serial number and its cell position in the build sheet.
4. Place the second insulator and end plate. Insert the tie rods.
5. Compress in steps in a star pattern: 30 %, 60 %, 100 % of the target torque.
   Measure the stack height after each step.
6. Run the pre test checklist (`pre_test_checklist.md`) before the stack goes on the stand.

## 4. Disassemble

1. Complete the post test leak test while the stack is still assembled.
2. Drain, rinse and dry the stack. Release the compression in steps, in the reverse star pattern.
3. Remove the repeat units one by one, keeping their order. Photograph each layer as it is exposed.
4. Bag and label each component with the cell position for teardown inspection
   (`post_test_teardown_inspection.md`).

## 5. Build sheet fields

Stack ID, date, operator, component serial numbers per cell position, torque steps, stack height
after each step, deviations, signature.
