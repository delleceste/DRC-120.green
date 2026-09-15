# REW automation status

**Verified and working**, driven live against a running REW instance and
cross-checked with `../open-media-drc/scripts/new_filter_design.py --dry-run`.

## What it does

`../DRC-doc/tools/rew-pipeline/rew_pipeline.py` drives REW's own REST API through every step of
`../DRC-doc/REW-INVERSION.md` (window/FDW, spatial average, minimum phase,
divide, minimum phase again, bake in the crossover, trim) for a chosen FDW
cycle count, then runs `../DRC-doc/tools/drc_acceptance.py` on the result. It does
**not** reimplement REW's FDW windowing or minimum-phase transform -- it asks
the running REW instance to do each step, the same operations a person would
trigger from the GUI, and reads back the resulting impulse responses. This
replaced an earlier, abandoned approach of independently reconstructing the
numerics (`build_filters.py`, `rew_fdw_probe.py`, `output/candidate-fdw8/`,
still present for reference only -- their empirical Gaussian FDW width and
independent minimum-phase code were never validated against REW, and are not
part of the current approach).

- `../DRC-doc/tools/rew-pipeline/rew_client.py` -- REST client. Every mutating call returns the affected
  measurement's **UUID**, never its index: index numbers shift on every
  add/delete, which happens throughout this pipeline (see the note in
  `find()`'s docstring -- getting this wrong once produced a real bug where a
  stored reference silently pointed at the wrong measurement after a later
  deletion).
- `../DRC-doc/tools/rew-pipeline/rew_pipeline.py` -- the pipeline itself, `output/` -- example runs.

## Input naming convention

A centre pair `L0`/`R0` (override with `--center-l`/`--center-r`), optionally
1-4 more position pairs `L1`/`R1` .. `L4`/`R4` (`--pos-l-pattern`/
`--pos-r-pattern`, `--num-positions`). A real simultaneous sweep `L0+R0` is
used as the centre mono sum if present (normalised -6.0206 dB per
REW-INVERSION.md 3c); otherwise it's `L0` vector-averaged with `R0`, same as
every other position. For the `120.green.multipt.FDW8` reference session the
actual titles are `L.0`/`R.0` and `L 120.green.{n}`/`R 120.green.{n}` -- pass
those as overrides (see the example below).

## Ground truth extracted from the reference `120.green.multipt.FDW8` session

Read directly from the shipped measurements' own notes/window fields, not
guessed -- these are every DSP flag's default:

- FDW 8 cycles, applied to the 10 raw captures (`L.0`/`R.0` = centre,
  `L/R 120.green.1..4` = the four +-10 cm positions) before any averaging.
- Minimum phase #1 (`LX-MP`, `RX-MP`, `SUM-SP-MP`): cal file effects
  **included**, LF tail from **16 Hz at 12 dB/oct**, no HF tail.
- X801: REW SPL calibration offset **3.0 dB**. A fresh WAV import in the
  tested REW build arrives at 120 dB, so the pipeline explicitly executes
  **Add SPL offset -117 dB** before either multiplication and verifies that
  `|LX| = |L-SP|` and `|RX| = |R-SP|` over 20-225 Hz.
  Its reference IR windows are also set explicitly to **Tukey 0.25,
  100 ms left / 500 ms right, FDW off**. The current API import default was
  rectangular 500/1000 ms; letting that propagate made the trimmed filters
  262144 taps with their peak at sample 24000 instead of the reference
  131072 taps / sample 8192.
- Division: `F.common = Target / SUM-MP`, band **25-80 Hz**; `Fper_L`/`Fper_R
  = Target / LX-MP`/`RX-MP`, band **80-225 Hz**; both max gain **0 dB**.
- Minimum phase #2 (`LFilter`, `RFilter`): cal file effects **excluded**, LF
  tail from **16 Hz at 0 dB/oct**, no HF tail.
- Target: reused as-is if `--target-title` matches an already-loaded one
  (e.g. hand-tuned in REW); otherwise auto-built from `LX`/`RX` -- RMS
  average, target shape **"Full range"** (the four other REW-valid shapes
  are `Bass limited`/`Subwoofer`/`Driver`/`None`; `Subwoofer`, REW's global
  default for a fresh target, silently bakes in a sub crossover and produced
  a visibly worse filter -- Q 12-13, +11..+24 ms group delay -- until this
  was found and fixed), LF cutoff 10 Hz @ 24 dB/oct, then REW's own
  "Calculate target level".

## Validated results (FDW 8, reproducing the reference build)

`../DRC-doc/tools/rew-pipeline/rew_pipeline.py --fdw-cycles 8 --tag fdw8 --output output/fdw8 --center-l L.0 --center-r R.0 --pos-l-pattern 'L 120.green.{n}' --pos-r-pattern 'R 120.green.{n}' --target-title Target.auto`

- Step 6a (|H| preserved by minimum phase): LX-MP 0.026 dB, RX-MP 0.072 dB,
  SUM-SP-MP 0.324 dB max deviation over 20-225 Hz -- all near the guide's
  "~0.03 dB" expectation.
- `../DRC-doc/tools/drc_acceptance.py`: both channels PASS sharpest-feature and group-delay;
  both FAIL the gated-tone test (L 118 ms vs 103 ms limit at 79 Hz, R 107 ms
  vs 100 ms limit at 100 Hz) -- matching the previously-recorded reference
  result (117 ms / 103 ms) to a few ms, with an auto-built target instead of
  the hand-tuned one.
- Diffed the produced `FLX/FRX-trimmed-48k.wav` directly against the
  reference session's own exported WAVs: 0.034-0.04 dB rms / 0.20-0.23 dB max
  magnitude deviation over 20-225 Hz.
- `new_filter_design.py --dry-run` on the output directory: all 10 required
  files resolved by name, both filter TXTs match their WAV to 0.0002 dB /
  0.001 deg RMS (one fixed 8192-sample delay), geometry provenance
  (front-wall/speaker distance, marker colour) recovered from the input
  measurements' notes.

## Output files (open-media-drc's exact naming -- see
`../open-media-drc/FILTERS_AND_DRC.md` and
`scripts/new_filter_design.py`'s `TXT_NAMES`/`AGGREGATE_NAMES`/`WAV_PATTERNS`)

```
output/fdw8/                              --output: one run, and only one run
  DRC-120.green/                          the project: `DRC-` off = the geometry
    120.green.fdw8.mdat                   the session (--save-mdat)
    120.green.fdw8.txts/                  geometry again, so the rest is the design ID
      FLX-trimmed-48k.wav  FRX-trimmed-48k.wav   the two filters (BruteFIR input)
      FLX-trimmed.txt      FRX-trimmed.txt       their frequency response (phase
                                           referenced to the WAV's own peak sample --
                                           REQUIRED for new_filter_design.py's
                                           TXT-vs-WAV check; get this wrong and
                                           residual phase is ~104 deg, not the ~0)
      L.txt  R.txt  LR.txt                measured L/R/vector-average, before correction
      L.filtered.txt  R.filtered.txt  LR.filtered.txt   raw (no-FDW) centre capture x
                                           its filter, and their vector average
  manifest.json                           parameters + every measurement UUID
  acceptance.txt                          tools/drc_acceptance.py output
```

The three directory names are the design's identity, not decoration: the web
UI imports a directory holding exactly one `.txts`/`.mdat` pair (anything else
is "No unique .txts/.mdat pair found"), takes the geometry off the project
directory and the design ID off what follows the geometry in the export name.
Get one of them wrong and the import stops at "cannot infer a known geometry"
or "cannot infer a valid design ID" with both fields left to type in by hand.
`--geometry` and `--export-name` set them; every run prints, at the end,
whether what it just wrote imports and under which identity.

To actually deploy a design once you're happy with it: import
`DRC-120.green/` in the web UI, or point `new_filter_design.py` (no
`--dry-run`) at the `.txts` directory -- with the exports committed to git,
since that step records project/session provenance and is deliberately left to
you, not done by `rew_pipeline.py`. The `.mdat` beside the export folder is
found by name, so `--mdat` is no longer needed.

## Known quirks / things that took real debugging

- **An imported X801 can look flat at 0 dB in REW's Filter response graph
  while still carrying `splOffsetdB = 120`**. REW Trace Arithmetic propagates
  that metadata: the affected saved run had `LX/RX = 236.99 dB`, generated a
  180 dB target, and put the corrected L/R traces around 200 dB. The manual
  reference session's X801 has `splOffsetdB = 3.0`, hence the required
  `-117 dB` adjustment. The pipeline now reads the offset back after changing
  it and refuses to continue if X801 multiplication shifts the band's median
  by more than 0.5 dB. Local extrema are reported but do not gate the run:
  finite IR/window effects can exceed 1 dB locally while the correct manual
  reference has a roughly -0.01 dB median change. The broken calibration
  shifts the median by approximately 117 dB.
- **A target generated during a bad-calibration run is poisoned even after
  X801 is fixed.** An already-loaded target is now checked over 20-225 Hz;
  an implausible one is deleted and rebuilt, and REW's calculated target
  level is checked before division.
- **API-fetched WAV samples cannot be byte-identical to REW's GUI export.**
  The only linear impulse-response unit exposed by this REW API is percent,
  encoded as big-endian float32. Converting `float32(x*100)` back with `/100`
  loses a few low bits. Use `--save-mdat` and export the two trimmed traces in
  the REW GUI when byte identity is required; compare response and timing for
  API-produced WAVs. This transport limitation does not by itself explain a
  larger response difference between separately processed traces.

- **"Response copy" does not carry the source's notes** (only its own "Copy
  of `<title>`" line) -- the pipeline copies them over explicitly
  (`client.set_notes`) so the geometry comments survive into `L.txt`/`R.txt`.
- **"Response copy" does not detach IR-window state either**: making a
  no-FDW snapshot of the centre capture *before* enabling FDW on the
  original resulted in the snapshot showing FDW enabled too, once the
  original was mutated. Fixed by building the *entire* chain first (FDW on
  throughout), and only at the very end turning FDW off on the originals and
  taking the snapshot -- matching what the reference session's own history
  shows it actually did.
- **REW's `/frequency-response` endpoint could not be made to return
  unsmoothed data** here, regardless of a `smoothing=None` query or a
  `Smooth`/`None` command issued first (still came back at 1/48 octave, ppo
  96) -- new_filter_design.py hard-requires a literal `* Smoothing: None`
  header. Worked around by computing the spectrum directly from the
  impulse-response endpoint (a plain rfft is unsmoothed and linear-spaced by
  construction) instead of that endpoint.
- **Target shape must be `"Full range"`**, not `"Flat"` (not a valid value)
  and not REW's default `"Subwoofer"` (bakes in a bass-management crossover
  inappropriate for a full-range target and visibly degrades the filter).
- **Measurement index numbers shift on every add/delete** -- the client was
  rewritten early on to track UUIDs throughout after this produced a real
  bug (a stale index silently pointed at a different, wrong measurement).
- **Clean the current tag before starting a rerun.** Deleting each stale
  stage only when rebuilding that stage leaves later intermediates from an
  interrupted run resident long enough to hit REW's default 60-measurement
  limit. Startup now removes every known pipeline output for the current tag.
- **`ProcessMeasurements` needs `measurementUUIDs`, not `measurementIndices`,
  for UUID input** -- separate fields in the API schema.
- **Use `PUT`, not `POST`, for partial IR-window and target-setting updates.**
  REW's OpenAPI schema describes `POST` as changing the settings object and
  `PUT` as changing only some settings. FDW changes must preserve every
  capture's rectangular widths, shapes, and individual reference time, so
  the client sends only `addFDW`/`fdwWidthCycles` with `PUT`. Target setup
  likewise changes only the explicitly selected Full range/LF fields.

Official API documentation: https://www.roomeqwizard.com/help/help/html/api.html
