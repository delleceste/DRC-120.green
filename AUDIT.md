# DRC-120.green measurement and filter audit

Audit date: 2026-09-10

Reference procedure: `../DRC-doc/REW-INVERSION.md`

Comparison set: `../DRC-120.blue/120.blue.multi.pt.txts/`

## Geometry and measurement set

The green geometry is defined by the loudspeakers being 120 cm from the front
wall and the listener being at the green floor marks. The main listening
position is 4.18 m from the front wall, approximately 33 cm forward of the
4.51 m blue listening position.

The five green microphone positions are internally consistent according to
their recorded distances:

- centre: 4.18 m;
- `.1`: 3.98 m, approximately 20 cm forward;
- `.2`: 4.387 m, approximately 20.7 cm back;
- `.3`: 4.186 m, 20 cm left;
- `.4`: 4.180 m, 20 cm right.

The `.2` L and R comments incorrectly say `AHEAD`. This is a stale copied
label; the distances identify `.2` as the back position. It does not affect
the measurements or averages.

All L and R captures use the same acoustic timing reference,
`DAC8STEREO L`, as required for the position-wise complex L/R sums.

## Procedure audit

### 1. Measurements

The set contains five positions, with separate L and R 512k log sweeps and an
optional simultaneous centre L+R sweep. The microphone geometry and common
timing reference are correct.

The sweeps start at approximately 15 Hz rather than the guide's preferred
12--14 Hz. This is usable, but it puts the minimum-phase LF-tail corner closer
to the 20 Hz correction-band edge.

### 2. FDW

The text exports do not record enough information to prove the FDW setting or
that it was applied to every original capture before averaging. The final
filter sharpness values, Q 8.2 and Q 10.2, strongly indicate that effective
regularisation reached the arithmetic.

The FDW setting should nevertheless be confirmed directly in the REW session.
If it is currently 12 cycles, an 8-cycle rebuild is the documented next
experiment for softening the residual feature around 80 Hz.

### 3. Spatial reduction

The spatial reduction is correct:

- `L.SP` is the RMS magnitude average of the five L positions;
- `R.SP` is the RMS magnitude average of the five R positions;
- `LR.1` through `LR.4` are vector averages of the matching L/R pairs;
- `SUM.C` is the physical centre L+R sweep normalized by -6.0206 dB;
- `LR.SP` is the RMS magnitude average of `SUM.C` and `LR.1` through `LR.4`.

The mono sum was therefore formed position by position while phase was still
meaningful, before RMS averaging across positions.

### 4. First minimum-phase conversion

`LX`, `RX` and `LR.SP` were converted to minimum phase with LF tails enabled,
12 dB/octave slopes and no HF tails. Calibration effects are included at this
stage, as required for measurement-derived divisors.

Magnitude preservation over 20--225 Hz is good:

- `LX` to `LX-MP`: maximum difference approximately 0.035 dB;
- `RX` to `RX-MP`: maximum difference approximately 0.036 dB;
- `LR.SP` to `LR.SP-MP`: approximately 0.04 dB on common exported points.

There is no evidence of the old missing-LF-tail corruption.

### 5. Target

The target is built from the plain RMS magnitude average of `LX` and `RX`, not
from an inappropriate spatial phase average. Its shape matches the blue
Harman-style target. Its approximately 1.02 dB level difference from blue is
consistent with the different session level.

### 6. Division and 80 Hz splice

The final rebuilt construction is correct:

```text
Fcommon = Target / LR.SP-MP, limited to the common bass range
Fper_L  = Target / LX-MP, limited to 80--225 Hz
Fper_R  = Target / RX-MP, limited to 80--225 Hz
FL      = Fcommon * Fper_L
FR      = Fcommon * Fper_R
```

All divisions are cut-only with maximum gain 0 dB.

An earlier version omitted `Fcommon` on the assumption that it did nothing.
That assumption was false: the exported common factor contained up to roughly
1 dB of correction through the transition. The current `FL` and `FR` comments
show that the common multiplication is now present.

The splice is not the primary cause of the left 79 Hz tail. Before adding the
common factor the left tail was 171 ms; afterwards it is 169 ms. The splice
does, however, move the worst group-delay locations toward 80 Hz and worsens
the right result by about 2.7 ms.

### 7. Second minimum-phase conversion

`FL` and `FR` were converted to `L.Filter` and `R.Filter` with:

- calibration effects excluded;
- LF tail enabled;
- 0 dB/octave LF-tail slope;
- no HF tail.

The 0 dB/octave choice is appropriate because these are filters already
designed to return to unity below their active range. It avoids adding an
unrequested subsonic high-pass.

### 8. X801 and final export

X801 is identical to the blue reference and is multiplied last:

```text
FLX = X801 * L.Filter
FRX = X801 * R.Filter
```

The exported arithmetic agrees within 0.001 dB and 0.0002 degrees. Trimming
does not change the exported frequency response.

The final WAV files are 48 kHz, mono, 32-bit IEEE float. They currently contain
262144 samples, whereas the procedure describes 131072-sample exports. This
does not cause the acceptance failures, because the Q criterion is
length-independent, but it doubles nominal filter length and convolution cost.
A 131072-sample export is preferable if REW permits it.

## Acceptance results

The current green filters were tested with `../DRC-doc/drc_acceptance.py`.

| Test | Green L | Green R |
|---|---:|---:|
| sharpest feature, Q <= 12 | pass: Q 8.2 | pass: Q 10.2 |
| group delay, <= 10 ms | fail: +10.7 ms at 77.6 Hz | fail: -14.6 ms at 80.8 Hz |
| gated-tone tails | fail: 169 ms at 79 Hz | pass: 79 ms at 79 Hz |
| overall | fail | fail |

Neither filter passes the procedure's strict build-quality gate. The failures
are nevertheless below the guide's approximate auditory thresholds: the
169 ms bass tail is below the approximate 200--300 ms ringing range, and the
group-delay values are below the approximate auditory threshold around 80 Hz.
The filters are likely listenable, but the procedure does not classify them as
final deployable builds.

## Comparison with DRC-120.blue

The current green and blue multipoint filters are comparable in time-domain
quality. Neither pair passes the complete acceptance suite.

| Result | Green L | Blue L | Green R | Blue R |
|---|---:|---:|---:|---:|
| sharpness Q | 8.2 | 10.3 | 10.2 | 7.5 |
| worst group delay | 10.7 ms | 11.2 ms | 14.6 ms | 15.6 ms |
| 79 Hz tail | 169 ms, fail | 96 ms, noisy/pass | 79 ms, pass | 133 ms, fail |
| overall | fail | fail | fail | fail |

Green is not generally worse. It has slightly better group-delay results on
both channels and a better right-channel tail, while blue has the better
left-channel 79 Hz tail.

## Effect of the 33 cm listener movement

After removing the overall session-level offset, the spatial measurements
differ substantially:

| Band | Spatial L RMS difference | Spatial R RMS difference | Mono-sum RMS difference |
|---|---:|---:|---:|
| 20--40 Hz | 2.31 dB | 1.10 dB | 2.09 dB |
| 40--63 Hz | 1.08 dB | 1.10 dB | 2.17 dB |
| 63--80 Hz | 3.60 dB | 2.73 dB | 2.43 dB |
| 80--100 Hz | 1.22 dB | 3.18 dB | 0.82 dB |
| 100--160 Hz | 1.07 dB | 2.73 dB | 1.57 dB |
| 160--225 Hz | 1.86 dB | 2.79 dB | 2.72 dB |

These differences are real and consistent with moving the listening position
by approximately 33 cm. They are much larger than export or interpolation
error.

Relative to blue, the green room filters apply more correction:

| Band | Green minus blue, L filter | Green minus blue, R filter |
|---|---:|---:|
| 63--80 Hz | -0.14 dB average | -0.71 dB |
| 80--100 Hz | -1.37 dB | -0.77 dB |
| 100--160 Hz | -1.60 dB | -2.26 dB |
| 160--225 Hz | -1.06 dB | -0.66 dB |

Peak filter differences reach approximately 3.7 dB on L and 5.0 dB on R in
the 100--160 Hz region. A blue filter used at the green position would leave
the green upper bass materially less corrected.

Below approximately 63 Hz both filter pairs are effectively unity because the
cut-only target is unreachable there. The useful effect of rebuilding is
therefore mainly in the 70--225 Hz range, especially 100--160 Hz.

## Conclusions

1. The green averages and inversion topology are now correct.
2. The only geometry metadata error is the stale `AHEAD` label on position
   `.2`; the recorded distances are correct.
3. The 33 cm listener movement causes material response changes, so rebuilding
   the filter for the green position was worthwhile.
4. The green filters are more appropriate tonally at the green position than
   the blue filters, particularly from 80 to 225 Hz.
5. Green and blue have broadly comparable time-domain quality; neither passes
   the strict acceptance suite.
6. The remaining green failures are concentrated around 78--81 Hz. They are
   not caused primarily by omitting or adding the common splice, and they are
   likely below audibility, but they remain formal procedure failures.
7. If the current original-capture FDW is 12 cycles, the next controlled
   experiment is an 8-cycle rebuild from step 3 onward. The goal is to retain
   the green-specific broad correction while softening the narrow behavior
   around 80 Hz.

