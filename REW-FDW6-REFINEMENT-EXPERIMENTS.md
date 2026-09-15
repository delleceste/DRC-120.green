# REW: refinement experiments for clean-fdw6

Date: 2026-09-13

These are two separate manual parametric-EQ experiments added to the existing
FDW6 correction. They allow the proposed tonal changes to be evaluated without
rebuilding the inversion. The settings are starting points, not optimised or
validated filters. Neither experiment has been implemented or acoustically
measured yet.

## Baseline

The existing chain uses common L/R inversion over 25–80 Hz, per-speaker
inversion over 80–225 Hz, and X801 crossover correction. The band limits have
transition regions; they are not abrupt switches.

The finished filters under
`output/clean-fdw6/clean-fdw6.txts/` pass `../DRC-doc/tools/drc_acceptance.py`.
The left filter's 79 Hz gated-tone tail is 92 ms against a 103 ms limit, with
a 13 ms interquartile spread, so the margin is modest.

The `.filtered.txt` responses are predictions from the original measurements,
not fresh acoustic verification. The L/R raw exports represent the centre
position; the inversion was designed from five positions.

## Starting settings

| Experiment | Filter type | Frequency | Gain | Q | Apply to |
|---|---|---:|---:|---:|---|
| Remaining bass peak | PK / peaking | 82 Hz | −1.0 dB | 2.0 | Both L and R, identically |
| Broad upper-bass/lower-midrange peak | PK / peaking | 530 Hz | −1.5 dB | 2.0 | Both L and R, identically |

Q = 2 gives a broad adjustment. Identical filters on both channels preserve
their existing relative magnitude and phase at each frequency, including
through the common/per-channel transition. Test one experiment at a time first.

## Procedure in REW

1. Select `L.filtered.clean-fdw6`, which already contains the inversion and X801.
2. Open **EQ**, select **Generic** as the equaliser, then open **EQ Filters**.
3. Enter one filter row using the settings above. Disable automatic adjustment
   for that row, and ensure no other unintended EQ rows are enabled.
4. Inspect the **Predicted** response, toggling the filter on and off.
5. Repeat on `R.filtered.clean-fdw6` with identical settings.
6. Evaluate each experiment independently before considering their combination.

REW's manual filter controls expose frequency, gain and Q. The EQ window also
shows predicted impulse response, phase, group delay and waterfall:
[filter controls](https://www.roomeqwizard.com/help/help_en-GB/html/eqfilters.html),
[EQ window](https://www.roomeqwizard.com/help/help_en-GB/html/eqwindow.html).

Entering EQ rows previews the additional correction; it does not modify the
existing exported FIR WAVs or deploy anything to BruteFIR.

## Experiment 1: 82 Hz

The centre-seat response retains sizeable peaks around 79 Hz on R and 85 Hz
on L. Using 1/6-octave power averaging, the approximate peak levels are:

| Feature | Raw | Predicted FDW6 |
|---|---:|---:|
| L peak around 85 Hz | 83.2 dB | 81.6 dB |
| R peak around 79 Hz | 84.6 dB | 83.1 dB |

Start with the common 82 Hz, −1 dB, Q = 2 bell. Check whether reducing these
peaks is worth the additional attenuation of adjacent dips, particularly L
around 70–75 Hz and R around 90 Hz.

Evaluate all five positions after applying the existing channel correction and
the experimental EQ. Do not judge the change solely from the centre seat or
from spatial averages. Compare acoustic decay as well as magnitude, particularly
around 79, 85, 100 and 116 Hz; confirm a promising result with fresh measurements.

If the neighbouring dips suffer too much, the common bell is too blunt. A local
target adjustment inside the inversion is an alternative experiment, described
below.

## Experiment 2: 530 Hz

Both centre-seat responses have a broad, largely untouched peak around
530–535 Hz, approximately 77.9 dB after 1/6-octave power averaging. It also
survives in the saved FDW6 spatial divisors: approximately 72.8/72.7 dB against
a target of 70.1 dB.

Start with the common 530 Hz, −1.5 dB, Q = 2 bell. Inspect roughly 400–700 Hz.
The aim is a small reduction of the broad hump without appreciably deepening
neighbouring valleys. Check the result across all five positions and by listening.

This experiment does not require changing the inversion's 225 Hz upper limit.
It adds one deliberately broad correction above that limit. It does not attempt
to fill the nearby 320–350 Hz depression.

## Incorporation into the finished FIRs

If an experiment is convincing, multiply its filter response into each existing
finished FIR, preserving absolute gain and the relative L/R level:

```text
new FLX = existing FLX × experimental PEQ
new FRX = existing FRX × experimental PEQ
```

Here multiplication means cascading the frequency responses, equivalently
convolving their impulse responses. Apply the same experimental PEQ to both
channels. If both experiments are retained, cascade both PEQs.

X801 is already included in the existing FLX/FRX filters. Do not add it again.

Export the combined filters at 48 kHz with appropriate impulse alignment and
length, and run `../DRC-doc/tools/drc_acceptance.py` on the actual final WAVs before
use. The 82 Hz experiment particularly needs this check because of the existing
79 Hz tail margin. The acceptance script's sharpness and group-delay checks stop
at 200 Hz, so its PASS alone does not validate the 530 Hz experiment; inspect
that region separately and verify acoustically.

## Alternative: change the inversion target locally

The earlier proposal to adjust the target means lowering a copy of the saved
target smoothly around 82 Hz and rebuilding the divisions. Keep the original
target and baseline filters available for comparison.

This is not equivalent to adding the manual PEQ. The spatial divisors, cut-only
clamp and band blending determine where and how much additional attenuation
the inversion produces. Do not lower the entire target simply to alter this
one region.

The manual PEQ trial is the simplest first test of whether the proposed tonal
change is desirable. A target-based rebuild is a subsequent option if a more
selective correction is needed.

## Reproducibility note

`rew_pipeline.toml` still defaults to 8 FDW cycles at the time of this note.
The saved clean-fdw6 run used an override. Explicitly retain 6 cycles when
rebuilding the baseline or testing a target adjustment.

Background procedure: [REW-INVERSION.md](../DRC-doc/REW-INVERSION.md).
