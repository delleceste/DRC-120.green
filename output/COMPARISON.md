# FDW cycle comparison — 6 / 8 / 9 / 10 / 12

Same base measurements throughout (`L.0`/`R.0` + `L/R 120.green.1..4`, `X801`),
same shared target (`Target.harman.fuller`: Harman/Olive +5 dB LF shelf, no
scoop, LF cutoff 10 Hz @ 24 dB/oct — held fixed across all four runs, per
REW-INVERSION.md §8/§5), same LF-tail settings on both minimum-phase passes
(16 Hz @ 12 dB/oct, then 16 Hz @ 0 dB/oct), same division bands (25/80/225 Hz).
Only `--fdw-cycles` changes. Full per-run logs and files in `output/fdw{8,9,10,12}/`.

## Step 6a — did minimum phase #1 preserve `|H|`? (want ~0.03 dB, guide's own figure)

| FDW cycles | LX-MP | RX-MP | SUM-SP-MP |
|---|---|---|---|
| 6  | 0.027 dB | 0.074 dB | **1.182 dB** ⚠ |
| 8  | 0.026 dB | 0.072 dB | 0.324 dB |
| 9  | 0.025 dB | 0.049 dB | 0.459 dB |
| 10 | 0.024 dB | 0.037 dB | 0.596 dB ⚠ |
| 12 | 0.031 dB | 0.026 dB | 0.700 dB ⚠ |

`LX-MP`/`RX-MP` stay near the guide's expectation throughout, no clear trend.
`SUM-SP-MP` is worth watching: it climbs steadily from 8 to 12 cycles, then
jumps to its highest value of all five at 6. Checked directly (not just from
the acceptance report): the FDW6 deviation is a single sharp spike at
**59.2 Hz** (1.18 dB there, ≤0.02 dB everywhere else 20–225 Hz) — a narrow
feature in the mono sum that a still-wider window resolves more finely than
8–12 cycles do, and REW's minimum-phase transform preserves slightly less
well right at that one point. It sits inside the common filter's 25–80 Hz
band, but 1.18 dB over roughly one bin is well short of step 6b's "narrow
peak" concern (>6 dB), and `drc_acceptance.py` — which runs on the finished
filter, not this intermediate — is clean. Flagged here as the one number in
this run that does not fit either trend, not as a failure.

## `drc_acceptance.py`

| FDW | ch | sharpest feature (Q, limit 12) | group delay 20–200 Hz (limit ±10 ms) | gated-tone worst | verdict |
|---|---|---|---|---|---|
| 6  | L | **PASS** Q 10.2 @ 183 Hz | **PASS** +5.2 ms | **PASS** all within limits | **PASS** |
| 6  | R | **PASS** Q 3.4 @ 117 Hz | **PASS** +7.0 ms | **PASS** all within limits | **PASS** |
| 8  | L | **PASS** Q 8.6 @ 98 Hz  | **PASS** −7.8 ms  | **FAIL** 118 ms @ 79 Hz (limit 103) | FAIL |
| 8  | R | **PASS** Q 9.2 @ 81 Hz  | **PASS** −8.9 ms  | **FAIL** 107 ms @ 100 Hz (limit 100) | FAIL |
| 9  | L | **PASS** Q 8.6 @ 98 Hz  | **PASS** +9.3 ms (close)  | **FAIL** 132 ms @ 79 Hz | FAIL |
| 9  | R | **PASS** Q 9.5 @ 81 Hz  | **FAIL** −11.0 ms | **PASS** all within limits | FAIL |
| 10 | L | **PASS** Q 8.6 @ 98 Hz  | **FAIL** +10.7 ms (barely) | **FAIL** 144 ms @ 79 Hz | FAIL |
| 10 | R | **PASS** Q 9.7 @ 81 Hz  | **FAIL** −12.8 ms | **PASS** all within limits | FAIL |
| 12 | L | **PASS** Q 8.3 @ 98 Hz  | **FAIL** −11.7 ms | **FAIL** 156 ms @ 79 Hz | FAIL |
| 12 | R | **PASS** Q 9.9 @ 81 Hz  | **FAIL** −16.0 ms (worst) | **PASS** all within limits | FAIL |

8/9/10/12 all fail, and not equally badly:

- **The L-channel 79 Hz gated-tone tail gets monotonically worse from 8 to
  12 cycles**: 118 → 132 → 144 → 156 ms, against a 103 ms limit. One specific
  feature that more cycles makes more sharply, more ring-pronely invertible.
- **Group delay degrades monotonically from 8 to 12 cycles, on both
  channels.** 8 is the only one of that set where both channels pass it.
- **The R-channel gated-tone failure is the one thing that improves with
  more cycles** — passes cleanly from 9 up — bought at the price of the
  group-delay failure above.

At **6 cycles both channels pass all three tests**, with the widest margins
of any run here (group delay +5.2/+7.0 ms against a 10 ms gate, versus 8
cycles' already-passing but tighter −7.8/−8.9 ms). This is the same
direction §8 predicts for a persistent single-frequency failure that gets
worse with *more* cycles, not better: pull back to fewer cycles, i.e. a
shorter analysis window at each frequency, i.e. more smoothing.

## Is FDW 6 under-correcting? — the actual filter gain at each octave band

Read directly off `FLX/FRX-trimmed-48k.wav` (not the acceptance report),
1/24-octave-smoothed, at standard third-octave centres, dB:

| FDW | ch | 25 | 31.5 | 40 | 50 | 63 | 80 | 100 | **125** | 160 | 200 | 225 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6  | L | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | −0.5 | −1.5 | **−4.0** | −3.5 | −1.6 | −1.4 |
| 8  | L | −0.1 | 0.00 | 0.00 | 0.00 | 0.00 | −1.3 | −0.9 | **−4.2** | −4.1 | −2.2 | −1.9 |
| 12 | L | −0.3 | 0.00 | 0.00 | 0.00 | 0.00 | −2.5 | −0.4 | **−4.4** | −4.8 | −3.1 | −2.3 |
| 6  | R | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | −1.5 | −1.7 | **−4.9** | −0.1 | −0.0 | −0.3 |
| 8  | R | −0.1 | 0.00 | 0.00 | 0.00 | 0.00 | −2.5 | −1.6 | **−5.3** | −0.4 | −0.4 | −0.6 |
| 12 | R | −0.3 | 0.00 | 0.00 | 0.00 | 0.00 | −4.1 | −1.4 | **−5.5** | −1.3 | −1.7 | −1.0 |

**The correction this room actually needs — the 125 Hz lump the guide's own
analysis of this room identifies (§5, "lumps at 80 and 125 Hz") — is barely
touched by the FDW choice**: −4.0/−4.9 dB at 6 cycles versus −4.4/−5.5 dB at
12, a difference of well under 1 dB, present at every cycle count tested.
**FDW 6 is not throwing away the correction that matters.**

What *does* shrink monotonically from 12 down to 6 cycles is the cut right
at **80 Hz** (R: −4.1 → −2.5 → −1.5 dB) and, on the L channel only, the
160–225 Hz region (−4.8/−3.1/−2.3 → −3.5/−1.6/−1.4 dB). The first of those is
exactly the frequency next to the 79 Hz feature driving every gated-tone
failure above 6 cycles — smoothing it is the fix working as intended, not a
loss. The second is a real, smaller reduction in upper-band correction with
no acceptance-test story behind it; worth a look if you care about that
region specifically, but it is a much smaller effect than the headline 125 Hz
correction, which is essentially unchanged.

## Verdict: FDW 6 passes, and is not the coarse compromise it might look like

It is the only cycle count of the five that clears all three
`drc_acceptance.py` tests on both channels, with the most margin. The one
data-quality flag at 6 cycles — `SUM-SP-MP`'s 1.18 dB deviation at 59.2 Hz
(above) — is narrow, well under the step 6b danger threshold, and does not
show up in the finished filter's own test results. And the depth-of-correction
comparison above says the thing actually worth correcting in this room (the
125 Hz lump) is corrected just as deeply at 6 cycles as at 12 — what changed
is specifically the parts of the correction that were making the filter fail,
plus a modest, band-limited (L-channel, 160–225 Hz) reduction elsewhere.

**Recommendation: use the FDW 6 build** (`output/fdw6/`). Per REW-INVERSION.md
step 11, the next real check is re-measuring with it playing, at more than
one position — not a further scan of cycle counts, now that one has actually
passed.
