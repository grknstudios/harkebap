#!/usr/bin/env python3
"""Split one continuous voice-over recording into per-line WAV files.

Usage: python3 split_voiceover.py <recording> <out_dir> key=start [key=start ...]
Each line runs from its start time to the next line's start (the last one to the
end of the file); leading and trailing silence is trimmed from every piece.
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

SR = 44100


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim(sig, thr=0.01, pad=0.02):
    idx = np.where(np.abs(sig) > thr)[0]
    if len(idx) == 0:
        return sig
    p = int(pad * SR)
    return sig[max(0, idx[0] - p): idx[-1] + 4 * p]


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    marks = [(k, float(v)) for k, v in (a.split("=") for a in sys.argv[3:])]
    audio = load(src)
    os.makedirs(out_dir, exist_ok=True)
    for i, (key, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(audio) / SR
        piece = trim(audio[int(start * SR): int(end * SR)])
        sf.write(os.path.join(out_dir, f"{key}.wav"), piece, SR, subtype="PCM_16")
        print(f"{key}: {start:6.2f}-{end:6.2f}  -> {len(piece) / SR:.2f}s")


if __name__ == "__main__":
    main()
