#!/usr/bin/env python3
"""Audit REW exports and probe the documented Gaussian FDW definition.

This is a diagnostic, not a validated REW inversion implementation.
Level offsets below are fitted diagnostics, not microphone calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile


def gaussian_fdw(ir, fs, frequencies, cycles, reference_sample):
    """Evaluate a Gaussian-windowed DTFT; full half-amplitude width = N/f.

    Input must already have the required fixed left/right windows applied.
    Phase is referenced to reference_sample. No calibration or display
    smoothing is applied. Direct evaluation avoids FFT-bin interpolation.
    """
    if cycles <= 0:
        raise ValueError("cycles must be positive")
    t = (np.arange(len(ir), dtype=float) - reference_sample) / fs
    result = np.empty(len(frequencies), dtype=complex)
    for k, f in enumerate(frequencies):
        window = np.exp(-4 * np.log(2) * (t * f / cycles) ** 2)
        result[k] = np.sum(ir * window * np.exp(-2j * np.pi * f * t))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--cycles', type=float, default=8)
    parser.add_argument('--output', type=Path, default=Path('analysis/fdw-probe.json'))
    args = parser.parse_args()
    if not np.isfinite(args.cycles) or args.cycles <= 0:
        parser.error('--cycles must be finite and positive')
    wavs = args.root / '120.green.multipt.FDW8.wavs'
    txts = args.root / '120.green.multipt.FDW8.txts'
    report = {'cycles': args.cycles, 'status': 'unvalidated diagnostic',
              'band_hz': [20, 225], 'channels': {}}
    for channel in 'LR':
        raw_path = wavs / f'{channel}.wav'
        fdw_path = wavs / f'{channel}.0.wav'
        fs, raw = wavfile.read(raw_path)
        fs2, fdw = wavfile.read(fdw_path)
        if raw.ndim != 1 or raw.dtype.kind != 'f':
            raise ValueError(f'{raw_path}: expected mono floating-point WAV')
        ref = np.loadtxt(txts / f'{channel}.0.txt', comments='*')
        ref = ref[(ref[:, 0] >= 20) & (ref[:, 0] <= 225)]
        predicted = gaussian_fdw(raw, fs, ref[:, 0], args.cycles,
                                 int(np.argmax(abs(raw))))
        residual = ref[:, 1] - 20 * np.log10(np.maximum(abs(predicted), 1e-30))
        offset = float(np.median(residual))
        report['channels'][channel] = {
            'raw_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            'fdw_sha256': hashlib.sha256(fdw_path.read_bytes()).hexdigest(),
            'wav_bytes_identical': raw_path.read_bytes() == fdw_path.read_bytes(),
            'wav_samples_identical': fs == fs2 and np.array_equal(raw, fdw),
            'fitted_level_offset_db': offset,
            'residual_rms_db': float(np.sqrt(np.mean((residual - offset) ** 2))),
            'residual_max_abs_db': float(np.max(abs(residual - offset))),
            'reference_smoothing': '1/48 octave; 96 points per octave',
            'limitations': ['fixed windows not independently verified',
                            'microphone calibration not applied',
                            'reference display smoothing not reproduced',
                            'reference time assumed at integer sample peak'],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
