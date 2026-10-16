# Pre test checklist

Template for this project, not validated on hardware. Any item marked NO stops the test.

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Build sheet complete and signed | review | YES / NO |
| 2 | Stack height within compression spec | caliper at 4 corners | YES / NO |
| 3 | Leak test passed, every cell | pressure decay, `stacktest.leak_test` | YES / NO |
| 4 | Cell voltage sense leads connected and read correctly | open circuit reading per cell | YES / NO |
| 5 | Safety limits set in the stand software | compare with `SafetyLimits` | YES / NO |
| 6 | Emergency stop tested | press and confirm trip | YES / NO |
| 7 | Gas detection and ventilation on | panel check | YES / NO |
| 8 | Test protocol and file names logged | test log | YES / NO |

The leak test applies 500 mbar overpressure, holds for 600 s and accepts the cell when the
fitted leak rate is at or below 5e-3 mbar L/s. The values are placeholders set in `LeakTestSpec`.
