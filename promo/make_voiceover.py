#!/usr/bin/env python3
"""Generate the NutPop promo voice-over lines with Kokoro TTS (kokoro-onnx).

Usage: python3 make_voiceover.py <kokoro-v1.0.int8.onnx> <voices-v1.0.bin>
Writes assets/vo/<key>.wav (24 kHz mono). The video script reads these files.

Model files: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""
import os
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

VOICE = "af_heart"
SPEED = 1.08

LINES = {
    "grkn": "G R K N Studios presents...",
    "intro": "NutPop! The satisfying nut sort puzzle!",
    "s01": "Tap a bolt, and stack the nuts by colour.",
    "s02": "No timer. No stress. Every level is solvable.",
    "s03": "Ice, locks and bombs bring new twists as you play.",
    "s04": "Explore twenty places, from a candy factory to outer space!",
    "s05": "Collect nine nut sets: gold, glass, jelly, neon and more.",
    "s06": "Every ten levels, a Plate Drop bonus puzzle!",
    "s07": "Daily rewards, a lucky spin, and a star chest.",
    "s08": "Clear the board, and collect your coins. So satisfying!",
    "cta": "NutPop is out now on Google Play! Search NutPop, and download it today!",
}


def trim(sig, thr=0.01):
    idx = np.where(np.abs(sig) > thr)[0]
    if len(idx) == 0:
        return sig
    return sig[max(0, idx[0] - 240): idx[-1] + 2400]


def main():
    model, voices = sys.argv[1], sys.argv[2]
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vo")
    os.makedirs(out_dir, exist_ok=True)
    k = Kokoro(model, voices)
    for key, text in LINES.items():
        sig, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
        sig = trim(np.asarray(sig, dtype=np.float32))
        sf.write(os.path.join(out_dir, f"{key}.wav"), sig, sr)
        print(f"{key}: {len(sig) / sr:.2f}s  {text}")


if __name__ == "__main__":
    main()
