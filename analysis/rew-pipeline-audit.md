# `rew_pipeline.py` audit — 2026-09-12

## Corrected defects

1. A fresh REW import of `X801.wav` carried `splOffsetdB = 120`; the manual
   FDW8 session carries `3.0`. The pipeline now applies `Add SPL offset -117
   dB`, reads the value back, and checks that the LX/RX products have no
   broadband level shift.
2. The imported X801 used REW's current rectangular 500/1000 ms defaults.
   The manual session uses Tukey 0.25, 100/500 ms, FDW off. Because X801 is
   trace A in the final multiplication, the wrong state produced 262144-tap
   filters with the peak at sample 24000. The explicit reference settings
   restore 131072 taps and peak sample 8192.
3. Partial IR-window and target-setting updates used POST. REW's OpenAPI
   schema defines PUT for changing selected fields, so both now use PUT and
   read the result back. This preserves every raw measurement's window widths
   and individual reference time when FDW cycles change.
4. A target generated while X801 had the bad offset could be reused. Existing
   and generated targets now receive an SPL sanity check; the recorded bad
   target was 180 dB SPL.
5. Interrupted runs left tagged measurements loaded until each stage was
   reached again, causing REW's 60-measurement limit to abort reruns. All
   outputs owned by the current tag are now removed at startup.
6. Final corrected L/R traces now fail early if their level is implausible or
   if a cut-only chain adds more than 6 dB.

The two minimum-phase calls were already correct: pass 1 includes microphone
calibration and uses a 16 Hz, 12 dB/oct LF tail with no HF tail; pass 2
excludes microphone calibration and uses a 16 Hz, 0 dB/oct LF tail with no HF
tail.

## Clean FDW8 run

The live session was reduced to L.0, R.0, L/R 120.green.1..4, and
L+R 120.green. `X801.wav` and the Harman Fuller target were then imported or
generated from scratch. The run used the real simultaneous L+R centre trace
with -6.0206 dB normalization.

- X801: 120 dB -> 3 dB (`-117 dB` command)
- target level: 70.93 dB SPL
- corrected L/R medians: 74.62 / 74.19 dB SPL
- maximum corrected gain relative to raw: +0.18 / +0.07 dB
- output: 131072 samples at 48 kHz; both peaks at sample 8192

Artifacts are in `output/clean-fdw8/`, including the saved REW session,
acceptance output, and `manual-comparison.json`.

## Manual WAV comparison, 20–225 Hz

| | Magnitude RMS | Magnitude max | Phase RMS | Phase max | Peak delta |
|---|---:|---:|---:|---:|---:|
| FLX | 0.0361 dB | 0.2002 dB | 0.5202 deg | 3.4319 deg | 0 samples |
| FRX | 0.0415 dB | 0.2324 dB | 0.2776 deg | 1.9557 deg | 0 samples |

The files are not byte-identical. REW's API has no WAV export and exposes
linear impulse samples only as float32 percent; converting that transport
back to unit amplitude loses low sample bits, so byte identity is impossible
even for an identical internal trace. The measured 0.04 dB-scale response
difference is larger than transport quantisation alone. Stage comparison
shows identical L-SP/R-SP inputs and an X801 response matching within 0.00031
dB; the first local differences appear in REW's X801 arithmetic result. The
saved manual session records final window state but not the state/history at
the moment that old arithmetic trace was created. Use the saved clean `.mdat`
and REW's GUI exporter to remove transport differences when comparing REW's
internal result.

Both new and manual filters pass the sharp-feature and group-delay gates and
fail the same gated-tone-tail gate. New versus manual worst tails are 118 vs
117 ms for FLX and 107 vs 103 ms for FRX.
