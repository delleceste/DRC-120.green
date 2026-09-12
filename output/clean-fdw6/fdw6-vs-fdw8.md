# FDW6 versus clean FDW8

Both runs use the same eleven input captures, simultaneous `L+R 120.green`
centre response normalized by -6.0206 dB, X801, target, band limits, and
minimum-phase settings. The FDW8-generated `Target.harman.fuller` was held
fixed for FDW6.

| Acceptance metric | FLX FDW6 | FLX FDW8 | FRX FDW6 | FRX FDW8 |
|---|---:|---:|---:|---:|
| Sharpest feature Q | 10.2 PASS | 8.6 PASS | 3.4 PASS | 9.2 PASS |
| Maximum group-delay excursion | 5.2 ms PASS | 7.8 ms PASS | 7.0 ms PASS | 8.9 ms PASS |
| 79 Hz gated tail | 92 ms PASS | 118 ms FAIL | 55 ms PASS | 82 ms PASS |
| 100 Hz gated tail | 50 ms PASS | 85 ms PASS | 76 ms PASS | 107 ms FAIL |
| Overall | **PASS** | **FAIL** | **PASS** | **FAIL** |

Both versions remain 131072 taps at 48 kHz with the impulse peak at sample
8192. Over 20-225 Hz, FDW6 differs from FDW8 by 0.421 dB RMS / 1.252 dB max
on FLX and 0.431 dB RMS / 1.112 dB max on FRX. Its deepest cuts are gentler:
-4.25 versus -4.52 dB on FLX and -5.70 versus -6.75 dB on FRX.

FDW6 uses a shorter frequency-dependent time window and therefore applies
stronger regularisation. It removes the narrow behaviour responsible for
FDW8's 79 Hz left and 100 Hz right tail failures. The improvement is not
uniform at every test tone, but every FDW6 tone remains within its limit.

`SUM-SP-MP` differs from `SUM-SP` by 1.298 dB at 59.20 Hz, inside the 25-80 Hz
common-correction band. This occurs in a deep response dip. Both the original
and the minimum-phase value are far below target, so division requests boost
and `maxGain = 0 dB` clamps both results to unity. The delivered FLX and FRX
filters measure 0.000 dB throughout 58.6-59.7 Hz. The step-6a warning is real
as an intermediate magnitude-preservation observation but has no effect on
the final filter in this cut-only chain. FDW6 is therefore the stronger
timing candidate of the tested FDW6/7/8 settings.
