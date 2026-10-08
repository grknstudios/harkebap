#!/usr/bin/env python3
"""Generate the NutPop promo voice-over lines with Kokoro TTS (kokoro-onnx).

Usage: python3 make_voiceover.py <kokoro-v1.0.int8.onnx> <voices-v1.0.bin> [variant ...]
Writes assets/<vo dir>/<key>.wav (24 kHz mono) for each variant (default: all).
The video scripts read these files.

Model files: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""
import os
import sys

import numpy as np

VARIANTS = {
    # main promo (make_nutpop_promo.py)
    "main": {
        "dir": "vo",
        "voice": "af_heart",
        "lang": "en-us",
        "speed": 1.08,
        "lines": {
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
        },
    },
    # TikTok hook cut (make_nutpop_hook.py)
    "hook": {
        "dir": "vo_hook",
        "voice": "am_michael",
        "lang": "en-us",
        "speed": 1.12,
        "lines": {
            "h1": "Stop scrolling! You have to see this satisfying puzzle.",
            "h2": "Tap a bolt, and stack the nuts by colour.",
            "h3": "Clear the board, and... pop! Perfect!",
            "h4": "No timer. No stress. And no WiFi needed.",
            "h5": "Twenty places to explore, and nine nut sets to collect.",
            "cta": "It's called NutPop. Get it now on Google Play!",
        },
    },
    # "5 reasons" countdown (make_nutpop_top5.py)
    "top5": {
        "dir": "vo_top5",
        "voice": "bf_emma",
        "lang": "en-gb",
        "speed": 1.05,
        "lines": {
            "title": "Five reasons you'll love NutPop!",
            "r5": "Number five: no timer, and no stress. Every level is solvable.",
            "r4": "Number four: twenty places to explore.",
            "r3": "Number three: nine nut sets to collect.",
            "r2": "Number two: ice, locks and bombs keep things fresh.",
            "r1": "And number one: daily rewards, a lucky spin and a star chest!",
            "cta": "NutPop is out now on Google Play. Download it today!",
        },
    },
    # LinkedIn landscape cut (make_nutpop_linkedin.py)
    "linkedin": {
        "dir": "vo_linkedin",
        "voice": "af_heart",
        "lang": "en-us",
        "speed": 1.0,
        "lines": {
            "grkn": "G R K N Studios presents.",
            "hook": "Need a five-minute break that actually clears your head? Meet NutPop.",
            "play": "NutPop is a calm, satisfying puzzle. Tap a bolt, and stack the nuts by colour.",
            "calm": "There's no timer, and no stress. Every single level is solvable.",
            "fresh": "Ice, locks and bombs keep every level fresh, across twenty beautiful places.",
            "rewards": "Collect nine nut sets, spin for daily rewards, and unlock a bonus puzzle "
                       "every ten levels.",
            "anywhere": "And with no WiFi needed, you can play anywhere: on your commute, "
                        "or between meetings.",
            "cta": "NutPop is out now on Google Play. Give your brain a break, "
                   "and download it today!",
        },
    },
    # Park Pop LinkedIn landscape cut (make_parkpop_linkedin.py)
    "parkpop_linkedin": {
        "dir": "parkpop/vo_linkedin",
        "voice": "af_heart",
        "lang": "en-us",
        "speed": 1.0,
        "lines": {
            "grkn": "G R K N Studios presents.",
            "hook": "Stuck in traffic? Here's one jam you'll actually enjoy. Meet Park Pop.",
            "play": "Park Pop is a colourful car parking puzzle. Tap a lane, drive the cars, "
                    "and park them by colour.",
            "calm": "There are no timers, and no lives. Every level is solvable, "
                    "and one hundred percent fair.",
            "fresh": "Ice, locks and bombs bring new twists, across four seasons "
                     "and thirteen scenes.",
            "rewards": "Collect twenty car sets, claim free daily rewards, and unlock "
                       "a bonus escape puzzle every ten levels.",
            "anywhere": "And with no WiFi needed, you can play anywhere: on your commute, "
                        "or between meetings.",
            "cta": "Park Pop is out now on Google Play. Clear the jam, and download it today!",
        },
    },
}


def trim(sig, thr=0.01):
    idx = np.where(np.abs(sig) > thr)[0]
    if len(idx) == 0:
        return sig
    return sig[max(0, idx[0] - 240): idx[-1] + 2400]


def main():
    import soundfile as sf
    from kokoro_onnx import Kokoro

    model, voices = sys.argv[1], sys.argv[2]
    names = sys.argv[3:] or list(VARIANTS)
    k = Kokoro(model, voices)
    for name in names:
        v = VARIANTS[name]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", v["dir"])
        os.makedirs(out_dir, exist_ok=True)
        for key, text in v["lines"].items():
            sig, sr = k.create(text, voice=v["voice"], speed=v["speed"], lang=v["lang"])
            sig = trim(np.asarray(sig, dtype=np.float32))
            sf.write(os.path.join(out_dir, f"{key}.wav"), sig, sr)
            print(f"{name}/{key}: {len(sig) / sr:.2f}s  {text}")


if __name__ == "__main__":
    main()
