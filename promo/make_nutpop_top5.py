#!/usr/bin/env python3
"""NutPop "5 reasons you'll love it" countdown cut.

Usage: python3 make_nutpop_top5.py [output.mp4]
Needs assets/vo_top5 (python3 make_voiceover.py <model> <voices> top5).
"""
import math
import os
import sys

import make_nutpop_promo as P
import promo_parts as X

# screenshot indices (assets/screens, sorted)
SORT, NO_TIMER, ICE, PLACES, SETS, PLATE, DAILY, SATISFYING = range(8)

REASONS = [("r5", "5", NO_TIMER), ("r4", "4", PLACES), ("r3", "3", SETS),
           ("r2", "2", ICE), ("r1", "1", DAILY)]

P.use_timeline([("title", "title", 0.6)] + [(k, k, 0.45) for k, _n, _i in REASONS]
               + [("cta", "cta", 2.4)],
               vo_dir=os.path.join(P.ASSETS, "vo_top5"), min_len=2.4)

TITLE_NUTS = [(140, 300, 0, 0.85), (940, 360, 1, 0.75), (120, 1600, 2, 0.8),
              (960, 1660, 3, 0.9), (930, 1120, 5, 0.5), (150, 1060, 4, 0.5)]


def title(t):
    s = X.seg("title")
    lt = t - s["start"]
    img = P.background(t)
    P.floating_nuts(img, t, s["start"] + 0.1, TITLE_NUTS)
    P.paste_center(img, P.soft_circle(380, (255, 230, 150), 130), P.W / 2, 560,
                   1 + 0.05 * math.sin(t * 5))
    logo = P.load_rgba(os.path.join(P.ASSETS, "logo.png"), 520, sharpen=True)
    p = P.prog(lt, 0.0, 0.5)
    P.paste_center(img, logo, P.W / 2, 560 + 10 * math.sin(lt * 2.4), P.ease_out_back(p, 2.0),
                   min(1, p * 3))
    q = P.prog(lt, 0.25, 0.65)
    P.paste_center(img, X.number_badge("5", 150), P.W / 2 - 300, 1060,
                   P.ease_out_back(q, 2.5), q, -12 + 4 * math.sin(lt * 3))
    P.draw_text(img, "REASONS", P.W / 2 + 110, 1060, 130, fill=P.PILL, stroke=14, shadow=12,
                scale=P.ease_out_back(q), alpha=q)
    r = P.prog(lt, 0.45, 0.85)
    P.draw_text(img, "YOU'LL LOVE IT", P.W / 2, 1250, 104, stroke=13, shadow=12,
                scale=P.ease_out_back(r), alpha=r)
    P.burst(img, t, s["start"] + 0.3, P.W / 2, 560, n=30, seed=8, power=1.2)
    return img


def reason(key, label, idx):
    shot = X.full_shot(key, idx)

    def render(t):
        s = X.seg(key)
        lt = t - s["start"]
        img = shot(t)
        p = P.prog(lt, 0.15, 0.5)
        x = 170 - (1 - P.ease_out_cubic(p)) * 400
        P.paste_center(img, X.number_badge("#" + label, 135), x, 1720,
                       P.ease_out_back(p, 2.2), 1.0, -10 + 5 * math.sin(lt * 3))
        X.burst(img, t, s["start"] + 0.35, 170, 1720, n=18, seed=20 + int(label), power=0.7)
        return img
    return render


P.SCENE_FN["title"] = title
for _k, _n, _i in REASONS:
    P.SCENE_FN[_k] = reason(_k, _n, _i)


if __name__ == "__main__":
    P.main(sys.argv[1] if len(sys.argv) > 1
           else os.path.join(P.HERE, "nutpop_promo_top5_1080x1920.mp4"))
