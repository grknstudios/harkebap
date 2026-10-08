#!/usr/bin/env python3
"""Park Pop LinkedIn cut: 1920x1080, same format as the NutPop LinkedIn video.

Usage: python3 make_parkpop_linkedin.py [output.mp4]
Needs assets/parkpop/vo_linkedin
(python3 make_voiceover.py <model> <voices> parkpop_linkedin) and
assets/parkpop/logo.png (python3 make_parkpop_logo.py).
Also writes a matching .srt caption file next to the video.
"""
import glob
import os
import sys

import make_nutpop_promo as P
import make_nutpop_linkedin as L
from make_voiceover import VARIANTS

PP = os.path.join(P.ASSETS, "parkpop")
LINES = VARIANTS["parkpop_linkedin"]["lines"]

P.SCREENS = sorted(glob.glob(os.path.join(PP, "screens", "*.png")))
P.PLAY_URL = "play.google.com/store/apps/details?id=com.grknstudios.park_pop"

# screenshot indices (assets/parkpop/screens, sorted)
SORT, NO_TIMERS, ICE, SEASONS, SETS, BONUS, DAILY, SATISFYING = range(8)

BLUE = ((48, 96, 226), (64, 112, 238))
PINK = ((210, 60, 138), (222, 78, 154))

L.APP_NAME = "Park Pop"
L.BRAND_LOGO = os.path.join(PP, "logo.png")
L.BRAND_BG = BLUE
L.HOOK_TEXT = ("STUCK IN TRAFFIC?", "TRY THIS JAM!")
L.HOOK_NUTS = []
L.PHONE_BOX = (231, 551, 849, 1889)
L.CTA_SHOTS = [(SATISFYING, 1170, 560, 760, 7), (ICE, 1680, 560, 760, -7),
               (SORT, 1425, 545, 840, 0)]

P.use_timeline([("grkn", "grkn", 0.8), ("hook", "hook", 0.6), ("play", "play", 0.5),
                ("calm", "calm", 0.5), ("fresh", "fresh", 0.5), ("rewards", "rewards", 0.5),
                ("anywhere", "anywhere", 0.5), ("cta", "cta", 3.0)],
               vo_dir=os.path.join(PP, "vo_linkedin"), min_len=3.0)

P.SCENE_FN.update({
    "play": L.feature("play", L.ORANGE, "SIMPLE TO PLAY", ["Tap. Drive.", "Park!"],
                      ["Sort the car jam by colour —", "one satisfying move at a time."],
                      [("phone", SORT, 1250, 560, 860, 6), ("phone", NO_TIMERS, 1640, 545, 880, -5)]),
    "calm": L.feature("calm", L.INDIGO, "ZERO PRESSURE", ["No timers.", "No lives."],
                      ["Every level is solvable —", "100% fair, every time."],
                      [("phone", SATISFYING, 1450, 545, 900, -4)]),
    "fresh": L.feature("fresh", L.RED, "ALWAYS FRESH", ["4 seasons,", "13 scenes."],
                       ["Ice, locks & bombs — from snowy", "streets to a neon city."],
                       [("card", ICE, 1225, 545, 860, 5), ("card", SEASONS, 1600, 545, 860, -5)]),
    "rewards": L.feature("rewards", PINK, "MORE TO UNLOCK", ["Rewards", "every day."],
                         ["20 car sets • Daily lucky spin", "Bonus Escape every 10 levels"],
                         [("phone", SETS, 1100, 560, 780, 7), ("phone", BONUS, 1690, 560, 780, -7),
                          ("phone", DAILY, 1395, 545, 860, 0)]),
    "anywhere": L.feature("anywhere", L.GREEN, "PLAY ANYWHERE", ["No WiFi", "needed."],
                          ["On the commute, between meetings,", "or on the sofa."],
                          [("card", SORT, 1450, 545, 900, -4)]),
})


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.HERE, "parkpop_linkedin_1920x1080.mp4")
    L.write_srt(out.rsplit(".", 1)[0] + ".srt", LINES)
    P.main(out)
