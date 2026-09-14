# 120.green `v1.FDW6` correction analysis

**Analysis date:** 2026-09-14

## Conclusion

The `v1.FDW6` filters are worth using with increased attenuation. They reduce a
persistent 100-160 Hz excess at all five measured positions. Combined room
group delay is nearly unchanged, broadband late energy generally falls, and no
strong long pre-echo appears in the predicted corrected responses. The listener
also prefers the result.

The BruteFIR shutdown is a separate gain-staging failure. Offline processing of
the source track reproduces the logged peak within 0.01 dB.

## Exact inputs

Only measurements in `output/clean-fdw6/clean-fdw6.txts` were used:

| Position | Left | Right |
|---|---|---|
| Centre | `L.0.txt` | `R.0.txt` |
| 1, 20 cm forward | `L 120.green.1.txt` | `R 120.green.1.txt` |
| 2, approximately 20 cm back | `L 120.green.2.txt` | `R 120.green.2.txt` |
| 3, 20 cm left | `L 120.green.3.txt` | `R 120.green.3.txt` |
| 4, 20 cm right | `L 120.green.4.txt` | `R 120.green.4.txt` |

Position 2's note says `AHEAD`, but its 4.387 m front-wall distance identifies
it as the rear position. The label does not affect the data.

| Applied filter | SHA-256 |
|---|---|
| `FLX-trimmed-48k.wav` | `9b1d092ff41b436a58bd0e9fef020c1493c8cbb951d2336a2e84017c7c7b6cc8` |
| `FRX-trimmed-48k.wav` | `1af03f6333967b872abd9302030e7126b20739d5d50113eb168132a01cfc787b` |

These match the deployed bundle's source WAVs. All installed RAW coefficient
hashes match its manifest.

## Method

Each complex response was multiplied by the corresponding exact filter. At
each position:

```text
before = (L + R) / 2
after  = (L * FLX + R * FRX) / 2
```

The shared acoustic timing reference preserves inter-channel timing. Common
8192-sample filter latency was removed, while relative phase was retained.
Because measurements start near 15 Hz, time comparisons use identical tapered
analysis windows. These are linear predictions, not fresh corrected sweeps.

## Tonal correction across five positions

Coherent left-plus-right levels are referenced to each position's 500-2000 Hz
mean.

| Band | Before | After | Median change | Position range |
|---|---:|---:|---:|---:|
| 20-80 Hz | +1.56 dB | +1.48 dB | -0.05 dB | -0.11 to +0.01 dB |
| 80-100 Hz | +5.76 dB | +4.61 dB | -1.15 dB | -1.15 to -1.08 dB |
| 100-160 Hz | +6.44 dB | +2.99 dB | **-3.41 dB** | **-3.60 to -3.17 dB** |
| 160-225 Hz | +3.19 dB | +2.18 dB | -1.00 dB | -1.10 to -0.92 dB |

The highest 100-160 Hz value falls by 3.41-4.83 dB at every position, median
4.52 dB. The filter therefore corrects a spatially persistent upper-bass excess
rather than a centre-position accident. It intentionally changes little below
80 Hz.

## Timing in room context

RMS group delay over 20-225 Hz, referenced to 300-500 Hz:

| Position | Before | After | Change |
|---|---:|---:|---:|
| Centre | 27.18 ms | 27.40 ms | +0.22 ms |
| 1 | 22.93 ms | 22.38 ms | -0.55 ms |
| 2 | 33.08 ms | 31.54 ms | -1.55 ms |
| 3 | 30.11 ms | 28.84 ms | -1.27 ms |
| 4 | 25.79 ms | 24.95 ms | -0.84 ms |

Four positions improve slightly; the centre worsens by 0.22 ms. The median is
effectively unchanged at 27.18 to 27.40 ms. The filter's few milliseconds of
phase movement sit inside an existing 23-33 ms room response.

The broadband 20 Hz-15 kHz prediction shows the strongest energy earlier than
1 ms changing from roughly -59 to -64 dB before correction to -41 to -45 dB
after. Earlier than 5 ms, corrected precursor level remains about -64 to -69
dB. Thus the phase correction adds a measurable near-main precursor but no
strong long pre-echo across these positions.

| Broadband energy | Median before | Median after | Across positions |
|---|---:|---:|---|
| Later than 20 ms | 0.459% | 0.411% | lower at all five |
| Later than 50 ms | 0.062% | 0.054% | lower at four, effectively unchanged at one |
| Later than 100 ms | 0.0031% | 0.0028% | lower at all five |

These fractions are not reverberation times. Narrow bass windows have long
symmetric impulses, and EQ changes their spectral weighting, so their raw
pre/post energy must not automatically be labeled audible ringing.

## Filter-only acceptance

Current revision 2 `drc_acceptance.py` passes both source WAVs and installed
192 kHz coefficients. All nine estimator regression tests pass.

| Check | Left | Right | Limit |
|---|---:|---:|---:|
| Feature sharpness | Q 8.8 | Q 3.4 | Q <= 12 |
| Group-delay excursion | +5.2 ms at 78.83 Hz | +7.0 ms at 95.95 Hz | magnitude <= 10 ms |
| Worst tail above control | +79 ms at 79 Hz | +80 ms at 100 Hz | <= 100 ms |

This is a careful bass-resonance screen, not a perceptual certificate. Pre-peak
energy does not enter its verdict, it uses median gate phase, and defaults stop
at 200 Hz. Its 100 ms allowance was calibrated with FDW6 among the references.

## Reproduced overload

The Qobuz bridge selected **Roxy Music - The Space Between** at 15:53:43.
BruteFIR subsequently reported:

```text
peak: 0/58/+4.69 1/66/+4.85
Safety limit exceeded on output (6.17 > 6.00). Aborting.
```

The 44.1 kHz, 16-bit source reaches about -0.004 dBFS during 85-87 seconds but
does not hit integer rails there. SoXR resampling to 192 kHz exposes +0.162
dBFS left and +0.409 dBFS right. Convolution with the exact 192 kHz filters and
configured 1.1 dB attenuation reaches **+6.179 dBFS right at 84.8268 seconds**,
matching the shutdown within 0.01 dB.

The event follows from a near-full-scale master, intersample overshoot and
phase-dependent peak growth. The minimum total attenuation for this event is
about 7.28 dB. Eight dB leaves 0.72 dB; **10 dB total is the safer provisional
setting**, leaving 2.72 dB. More recordings are needed for a universal bound.

Digital attenuation in the 64-bit floating-point, 32-bit-output chain does not
alter phase or create harmonic ringing. Its cost is reduced level relative to
the DAC noise floor.

## Comparison with Dirac Live

Ordinary Dirac Live does not expose this build's user-controlled common
low-frequency plus per-channel construction. That transparency is an advantage:
each component can be inspected and tested independently.

Dirac Live Bass Control is related. Dirac documents a common low-frequency
target, speaker-group-specific higher-frequency targets and cross-channel
optimization, but its filter construction is automated and proprietary.

Dirac says its mixed-phase correction limits pre-ringing by correcting excess
phase only when common across positions. It could produce less near-main
precursor than an unconstrained one-position phase inverse. FDW6 does not use
that kind of inverse: its magnitude divisors are minimum phase and its all-pass
term corrects the known crossover. Five-position prediction shows low long
precursor and stable combined timing.

There is no evidence that Dirac would produce a meaningfully better pre-echo
result here. It might reduce the short precursor, or retain similar crossover
correction because that behavior is common. Only a Dirac filter generated from
the same measurements and tested identically could answer quantitatively.

References:

- [Dirac Live technical overview](https://www.dirac.com/wp-content/uploads/2025/07/Dirac-Live-a-technical-overview-white-paper.pdf)
- [Dirac Live Bass Control filter design](https://helpdesk.dirac.com/en/dirac-bass-control/Filter-Design-c592)

## Final assessment

The intended correction is substantial and spatially consistent. Combined
room delay is essentially unchanged, late broadband energy generally falls,
and the new precursor is short. Filter acceptance passes, and listening favors
the correction. The evidence supports continued use. The required remediation
is gain staging: 1.1 dB attenuation is demonstrably insufficient.
