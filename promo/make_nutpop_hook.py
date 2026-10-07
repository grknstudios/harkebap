#!/usr/bin/env python3
"""NutPop TikTok "hook" cut: fast close-ups with word-by-word captions.

Usage: python3 make_nutpop_hook.py [output.mp4]
Needs assets/vo_hook (python3 make_voiceover.py <model> <voices> hook).
"""
import os
import sys

import make_nutpop_promo as P
import promo_parts as X
from make_voiceover import VARIANTS

LINES = VARIANTS["hook"]["lines"]

# screenshot indices (assets/screens, sorted)
SORT, NO_TIMER, ICE, PLACES, SETS, PLATE, DAILY, SATISFYING = range(8)

P.use_timeline([("h1", "h1", 0.25), ("h2", "h2", 0.25), ("h3", "h3", 0.35),
                ("h4", "h4", 0.3), ("h5", "h5", 0.3), ("cta", "cta", 2.2)],
               vo_dir=os.path.join(P.ASSETS, "vo_hook"), min_len=2.2)

_h1 = X.phone_scene("h1", SORT, pan=(0.55, 0.35), zoom=(1.25, 1.1))
_h2 = X.phone_scene("h2", NO_TIMER, pan=(0.35, 0.5), zoom=(1.05, 1.15))
_h3 = X.phone_scene("h3", SATISFYING, pan=(0.35, 0.4), zoom=(1.0, 1.1))
_h4 = X.full_shot("h4", NO_TIMER)
_h5a = X.full_shot("h5", PLACES)
_h5b = X.full_shot("h5", SETS)


def h1(t):
    img = _h1(t)
    X.captions(img, t, "h1", LINES["h1"], size=104)
    return img


def h2(t):
    img = _h2(t)
    X.captions(img, t, "h2", LINES["h2"])
    return img


def h3(t):
    img = _h3(t)
    s = X.seg("h3")
    # "pop" lands about 60% into the line
    tp = s["start"] + P.VO_LEAD + P.vo_len("h3") * 0.55
    X.flash(img, t, tp)
    X.burst(img, t, tp, P.W / 2, 700, n=40, seed=3, power=1.5)
    X.captions(img, t, "h3", LINES["h3"])
    return img


def h4(t):
    img = _h4(t)
    X.captions(img, t, "h4", LINES["h4"], y=1500)
    return img


def h5(t):
    s = X.seg("h5")
    mid = s["start"] + P.VO_LEAD + P.vo_len("h5") * 0.5
    img = _h5a(t) if t < mid else _h5b(t)
    X.flash(img, t, mid, 0.15, 150)
    X.captions(img, t, "h5", LINES["h5"], y=1500)
    return img


P.SCENE_FN.update({"h1": h1, "h2": h2, "h3": h3, "h4": h4, "h5": h5})


if __name__ == "__main__":
    P.main(sys.argv[1] if len(sys.argv) > 1
           else os.path.join(P.HERE, "nutpop_promo_hook_1080x1920.mp4"))
