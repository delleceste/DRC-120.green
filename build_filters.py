#!/usr/bin/env python3
"""Experimental independent reconstruction of the supplied REW inversion chain.

Reads raw captures, calibration, timing and target from the .mdat, never uses
the reference filters to synthesize an output. Writes candidate WAVs and a
comparison report. This is not yet a numerically validated REW replacement.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from rew_mdat import load


FS = 48000
N = 131072
F = np.fft.rfftfreq(N, 1 / FS)


def db(x):
    return 20 * np.log10(np.maximum(np.abs(x), 1e-30))


def measurements(path):
    return {o['shortDesc']: o for o in load(path)
            if isinstance(o, dict) and o.get('_class') == 'roomeqwizard.MeasData'}


def log_grid(m, field='rawValues'):
    return m['startFreq'] * m['logStep'] ** np.arange(len(m[field]))


def fdw(m, cycles, coefficient=4.0):
    """Direct frequency-dependent Gaussian DTFT on the fixed-windowed raw IR.

    coefficient=4 is an empirical approximation to this session, NOT a
    verified REW formula. The documented half-amplitude definition instead
    gives coefficient=4*log(2). Both are exposed for comparison.
    The time-domain Gaussian is truncated only below 1e-14 amplitude.
    """
    ir = m['irData']['ir']
    windows = m['irData']['windows']
    for side in ('preType', 'postType'):
        if windows[side]['value'] != 'RECTANGULAR':
            raise ValueError('Raw capture windows must be rectangular for this prototype')
    if m['sampleRate'] != FS:
        raise ValueError('This reconstruction currently requires 48 kHz captures')
    f = m['startFreq'] * 2 ** (np.arange(1023) / 96)
    f = f[f <= FS / 2]
    samples = np.asarray(ir['data'], dtype=float)
    center = windows['winRefIndex']
    t_ref = ir['startTime'] + center / FS
    h = np.empty(len(f), dtype=complex)
    for k, freq in enumerate(f):
        radius = int(np.ceil(cycles / freq * np.sqrt(32.3 / coefficient) * FS))
        lo = max(0, windows['preImpulseIndex'], center - radius)
        hi = min(len(samples), windows['postImpulseIndex'] + 1, center + radius + 1)
        t = (np.arange(lo, hi) - center) / FS
        h[k] = np.sum(samples[lo:hi] * np.exp(-coefficient * (t * freq / cycles) ** 2)
                      * np.exp(-2j * np.pi * freq * t))
    h *= np.exp(-2j * np.pi * f * t_ref)
    # REW's IR SPL offset uses RMS: a unit-amplitude sinusoid is -3.0103 dBFS.
    h *= 10 ** ((m['irData']['splOffset'] - 10 * np.log10(2)) / 20)
    for name in ('meterCal', 'scCal'):
        cal = m.get(name)
        if cal is not None and cal.get('freqArray') is not None:
            gain = np.interp(f, cal['freqArray'], cal['gainArray'])
            phase = (np.interp(f, cal['freqArray'], cal['phaseArray'])
                     if cal.get('phaseArray') is not None else np.zeros_like(f))
            h /= 10 ** (gain / 20) * np.exp(1j * np.deg2rad(phase))
    return f, h


def minimum_phase(magnitude, corner=16.0, slope=0.0):
    """Real-cepstrum minimum phase with an explicit LF magnitude continuation.

    Microphone calibration is applied to captures before spatial averaging;
    it is never applied a second time to the correction filters.
    """
    mag = np.maximum(np.asarray(magnitude, dtype=float), 1e-30).copy()
    low = F < corner
    anchor = np.interp(corner, F, mag)
    mag[low] = anchor * (np.maximum(F[low], F[1]) / corner) ** (slope / (20 * np.log10(2)))
    cep = np.fft.irfft(np.log(mag), N)
    cep[1:N // 2] *= 2
    cep[N // 2 + 1:] = 0
    return np.exp(np.fft.rfft(cep))


def derived_window(h, left=.1, right=.5, alpha=.25):
    """Apply the stored asymmetric Tukey 0.25 windows around t=0."""
    samples = np.fft.irfft(h, N)
    t = np.arange(N, dtype=float) / FS
    t[t > N / (2*FS)] -= N / FS
    duration = np.where(t < 0, left, right)
    u = np.abs(t) / duration
    taper = .5 * (1 + np.cos(np.pi * np.clip((u-(1-alpha))/alpha, 0, 1)))
    return np.fft.rfft(samples * taper)


def ramp(f, edge):
    x = np.clip(np.log2(np.maximum(f, 1e-30) / edge) + .5, 0, 1)
    return .5 - .5 * np.cos(np.pi * x)


def divide(target_db, divisor, low, high):
    weight = ramp(F, low) * (1 - ramp(F, high))
    gain = np.minimum(target_db - db(divisor), 0) * weight
    phase = -np.unwrap(np.angle(divisor)) * weight
    return 10 ** (gain / 20) * np.exp(1j * phase)


def reference_spectrum(m):
    ir = m.get('irData')
    if ir is not None:
        x = np.asarray(ir['ir']['data'], dtype=float)
        h = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / FS)
        h *= np.exp(-2j * np.pi * f * ir['ir']['startTime'])
        h *= 10 ** ((ir['splOffset'] - 10 * np.log10(2)) / 20)
        return f, h
    return log_grid(m), 10 ** (m['rawValues'] / 20)


def compare(f, h, m, band=(20, 225)):
    rf, rh = reference_spectrum(m)
    use = (f >= band[0]) & (f <= band[1])
    delta = db(h[use]) - np.interp(f[use], rf, db(rh))
    return {'rms_db': float(np.sqrt(np.mean(delta ** 2))),
            'max_abs_db': float(np.max(abs(delta)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, default=Path('120.green.multipt.FDW8.mdat'))
    parser.add_argument('--cycles', type=float, default=8)
    parser.add_argument('--gaussian', choices=['empirical', 'documented'], default='empirical')
    parser.add_argument('--lf-corner', type=float, default=16)
    parser.add_argument('--divisor-lf-slope', type=float, default=12.041199826559248)
    parser.add_argument('--filter-lf-slope', type=float, default=0)
    parser.add_argument('--lower', type=float, default=25)
    parser.add_argument('--splice', type=float, default=80)
    parser.add_argument('--upper', type=float, default=225)
    parser.add_argument('--target-offset', type=float, default=0)
    parser.add_argument('--output', type=Path, default=Path('output/candidate-fdw8'))
    parser.add_argument('--acceptance', type=Path, default=Path('../DRC-doc/drc_acceptance.py'))
    args = parser.parse_args()
    numeric = [args.cycles, args.lf_corner, args.lower, args.splice, args.upper,
               args.divisor_lf_slope, args.filter_lf_slope, args.target_offset]
    if not all(np.isfinite(numeric)) or args.cycles <= 0 or not 0 < args.lf_corner < FS/2:
        parser.error('Invalid FDW or LF-tail parameters')
    if not 0 < args.lower < args.splice < args.upper < FS/2:
        parser.error('Require 0 < lower < splice < upper < Nyquist')
    if min(args.divisor_lf_slope, args.filter_lf_slope) < 0:
        parser.error('LF-tail slopes must be nonnegative')
    args.output.mkdir(parents=True, exist_ok=True)
    ms = measurements(args.session)
    report = {'status': 'EXPERIMENTAL — REW equivalence NOT established',
              'parameters': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              'stages': {}, 'target': 'Supplied Target LR.RMS.AVG, held fixed as cycles change',
              'calibration': 'included once on raw captures; excluded from filter minimum phase'}
    channels = {}
    for channel in 'LR':
        rows = []
        for pos in range(5):
            name = f'{channel}.0' if pos == 0 else f'{channel} 120.green.{pos}'
            print(f'FDW {args.cycles:g}: {name}', flush=True)
            f, h = fdw(ms[name], args.cycles, 4 if args.gaussian == 'empirical' else 4*np.log(2))
            rows.append(h)
            ref_f = log_grid(ms[name])
            keep = (f >= 20) & (f <= 225)
            delta = db(h[keep]) - np.interp(f[keep], ref_f, ms[name]['rawValues'])
            report['stages'][name] = {'rms_db': float(np.sqrt(np.mean(delta**2))),
                                      'max_abs_db': float(np.max(abs(delta)))}
        channels[channel] = np.array(rows)
    spatial = {c: np.sqrt(np.mean(abs(channels[c])**2, axis=0)) for c in 'LR'}
    mono = np.sqrt(np.mean(abs((channels['L'] + channels['R']) / 2)**2, axis=0))
    spatial['LR'] = mono
    stages = {}
    for c, mag in spatial.items():
        stages[f'{c}-SP'] = 10 ** (np.interp(F, f, db(mag)) / 20)
        report['stages'][f'{c}-SP'] = compare(f, mag, ms[f'{c}-SP'])
    x = ms['X801']['irData']['ir']
    crossover = np.fft.rfft(np.asarray(x['data'], float), N) * np.exp(-2j*np.pi*F*x['startTime'])
    divisors = {}
    for c in ['L', 'R', 'LR']:
        if c != 'LR':
            # The REW multiplication creates an IR from the magnitude-only
            # spatial average and inherits X801's 100/500 ms Tukey windows.
            hx = stages[f'{c}-SP'] * crossover
            hx[F < f[1]] = 0
            hx = derived_window(hx)
            stages[f'{c}X'] = hx
            mag = abs(hx)
        else:
            mag = stages['LR-SP']
        mp = minimum_phase(mag, args.lf_corner, args.divisor_lf_slope)
        if c != 'LR':
            mp = derived_window(mp)
        divisors[c] = mp
        stages[f'{c}X-MP' if c != 'LR' else 'LR-SP-MP'] = mp
    target = ms['Target LR.RMS.AVG']
    target_db = np.interp(F, log_grid(target), target['rawValues']) + args.target_offset
    common = divide(target_db, divisors['LR'], args.lower, args.splice)
    stages['F.common'] = common
    files = []
    for c in 'LR':
        per = divide(target_db, divisors[c], args.splice, args.upper)
        combined = common * per
        correction = minimum_phase(abs(combined), args.lf_corner, args.filter_lf_slope)
        stages[f'Fper_{c}'] = per
        stages[f'F{c}'] = combined
        stages[f'{c}Filter'] = correction
        final = crossover * correction
        stages[f'F{c}X'] = final
        wav = np.roll(np.fft.irfft(final, N), 8192).astype(np.float32)
        path = args.output / f'F{c}X-trimmed-48k.wav'
        wavfile.write(path, FS, wav)
        files.append(path)
        ref = np.asarray(ms[f'F{c}X-trimmed']['irData']['ir']['data'], float)
        report[f'{c}_sample_relative_rms_error'] = float(np.linalg.norm(wav-ref)/np.linalg.norm(ref))
        report[f'{c}_peak_sample'] = int(np.argmax(abs(wav)))
    for name, h in stages.items():
        if name in ms:
            report['stages'][name] = compare(F, h, ms[name])
    np.savez_compressed(args.output / 'stages.npz', frequency_hz=F, **stages)
    result = subprocess.run([sys.executable, str(args.acceptance.resolve()), *map(str, files)],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (args.output / 'acceptance.txt').write_text(result.stdout)
    report['acceptance_exit_code'] = result.returncode
    (args.output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'])
    print(f'Report: {args.output / "comparison.json"}')
    # Never return success as if this experimental reconstruction met exact matching.
    return 2


if __name__ == '__main__':
    sys.exit(main())
