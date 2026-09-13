# clean-fdw6 baseline versus refinement PEQs

Built 2026-09-13 by `rew_pipeline.py` from a byte-identical copy of
`output/clean-fdw8/clean-fdw8.mdat`.

The pipeline cleared the active REW session, loaded the copy, discarded all
removable non-raw measurements, applied FDW 6 to the ten L/R captures, rebuilt
the target from the raw data, and reconstructed the consolidated correction:

- common L/R inversion: 25–80 Hz, cut-only;
- per-channel inversion: 80–225 Hz, cut-only;
- X801 crossover correction;
- optional common PEQs: 82 Hz, −1.0 dB, Q 2 and 530 Hz, −1.5 dB, Q 2.

REW's API would not delete one locked legacy trace named `L`. It was excluded
from every calculation. All other manual and generated traces from the source
session were removed before the target and filters were rebuilt.

## Side-by-side traces currently loaded in REW

| Result | L | R | L+R |
|---|---|---|---|
| FDW6 baseline | `L.filtered.baseline.clean-fdw6-peq` | `R.filtered.baseline.clean-fdw6-peq` | `LR.filtered.baseline.clean-fdw6-peq` |
| 82 Hz only | `L.filtered.eq82.clean-fdw6-peq` | `R.filtered.eq82.clean-fdw6-peq` | `LR.filtered.eq82.clean-fdw6-peq` |
| 530 Hz only | `L.filtered.eq530.clean-fdw6-peq` | `R.filtered.eq530.clean-fdw6-peq` | `LR.filtered.eq530.clean-fdw6-peq` |
| Both PEQs | `L.filtered.clean-fdw6-peq` | `R.filtered.clean-fdw6-peq` | `LR.filtered.clean-fdw6-peq` |

In **All SPL**, select the four traces from one column and use the same
smoothing and graph limits for comparison. The `LR` group is the clearest
overview; inspect L and R separately afterward.

## Verified change relative to baseline

The changes below are effectively identical for L, R and their vector average:

| Frequency | 82 Hz experiment | 530 Hz experiment | Both |
|---:|---:|---:|---:|
| 40 Hz | −0.093 dB | −0.002 dB | −0.095 dB |
| 82 Hz | −0.999 dB | −0.009 dB | −1.006 dB |
| 116 Hz | −0.337 dB | −0.020 dB | −0.356 dB |
| 225 Hz | −0.042 dB | −0.095 dB | −0.137 dB |
| 530 Hz | −0.006 dB | −1.498 dB | −1.502 dB |
| 1 kHz | −0.002 dB | −0.180 dB | −0.181 dB |

The combined final filters pass all `drc_acceptance.py` tests. The left 79 Hz
tail is 90 ms against a 103 ms limit; the right 79 Hz tail is 56 ms. See
`acceptance.txt` for the complete results.

The deployable exports contain the combined two-PEQ candidate. The baseline
and individual variants remain in the saved REW session for comparison.
