#!/usr/bin/env python3
"""Park Pop vertical cut: 1080x1920 version of the Park Pop LinkedIn video.

Same voice-over, scenes and copy as make_parkpop_linkedin.py, laid out for portrait.
Usage: python3 make_parkpop_vertical.py [output.mp4]
"""
import math
import os
import sys

import make_nutpop_promo as P
import make_nutpop_linkedin as L
import make_parkpop_linkedin as PL  # sets screenshots, logo, timeline, colours

P.W, P.H = 1080, 1920
W, H = P.W, P.H
SORT, NO_TIMERS, ICE, SEASONS, SETS, BONUS, DAILY, SATISFYING = range(8)


def centered_text(img, text, y, size, alpha=1.0, dy=0.0, **kw):
    P.draw_text(img, text, W / 2, y + dy, size, alpha=alpha, **kw)


def brand_footer(img, lt):
    a = P.prog(lt, 0.3, 0.8)
    logo = P.load_rgba(L.BRAND_LOGO, 84, sharpen=True)
    spr = P.text_sprite("Out now on Google Play", P.FONT_BOLD, 34, (255, 255, 255))
    total = logo.width + 16 + spr.width
    x0 = W / 2 - total / 2
    P.paste_center(img, logo, x0 + logo.width / 2, H - 70, 1.0, a)
    P.paste_center(img, spr, x0 + logo.width + 16 + spr.width / 2, H - 70, 1.0, a * 0.95)


def scene_grkn(t):
    s = P.seg("grkn")
    lt = t - s["start"]
    img = P.Image.new("RGBA", (W, H), (255, 255, 255, 255))
    logo = P.shine(P.load_rgba(os.path.join(P.ASSETS, "grkn_logo.png"), 820), P.prog(lt, 0.8, 1.7))
    p = P.prog(lt, 0.05, 0.75)
    P.paste_center(img, logo, W / 2, 860 + 6 * math.sin(lt * 2), 0.9 + 0.1 * P.ease_out_cubic(p),
                   P.ease_out_cubic(p))
    q = P.prog(lt, 0.7, 1.2)
    centered_text(img, "P R E S E N T S", 1320, 40, alpha=q, dy=(1 - P.ease_out_cubic(q)) * 20,
                  fill=P.NAVY + (255,), path=P.FONT_BOLD)
    return img


def scene_hook(t):
    s = P.seg("hook")
    lt = t - s["start"]
    img = P.background(t, L.BRAND_BG)
    P.paste_center(img, P.soft_circle(420, (255, 230, 150), 120), W / 2, 620,
                   1 + 0.05 * math.sin(t * 4))
    logo = P.shine(P.load_rgba(L.BRAND_LOGO, 560, sharpen=True), P.prog(lt, 0.9, 1.7))
    p = P.prog(lt, 0.0, 0.6)
    P.paste_center(img, logo, W / 2, 620 + 10 * math.sin(lt * 2.2), P.ease_out_back(p, 2.0),
                   min(1, p * 3), (1 - P.ease_out_cubic(p)) * -20)
    q = P.prog(lt, 0.4, 0.8)
    centered_text(img, L.HOOK_TEXT[0], 1080, 82, alpha=q, dy=(1 - P.ease_out_cubic(q)) * 40,
                  stroke=10, shadow=8)
    q2 = P.prog(lt, 0.6, 1.0)
    centered_text(img, L.HOOK_TEXT[1], 1205, 112, alpha=q2, dy=(1 - P.ease_out_cubic(q2)) * 40,
                  fill=P.PILL, stroke=12, shadow=10)
    tm = s["start"] + P.VO_LEAD + P.vo_len("hook") * L.MEET_AT  # "Meet Park Pop"
    m = P.prog(t, tm, tm + 0.35)
    P.paste_center(img, P.pill_sprite(f"Meet {L.APP_NAME} →", 60), W / 2, 1390,
                   P.ease_out_back(m, 2.2), m)
    P.burst(img, t, tm, W / 2, 620, n=30, seed=7, power=1.1)
    return img


def feature(name, colors, kicker, headline, sub, shots):
    """Copy at the top, phones / cards rising in below.

    shots: [(kind, screen idx, cx, cy, height, angle)], kind "phone" or "card".
    """
    def render(t):
        s = P.seg(name)
        lt = t - s["start"]
        img = P.background(t, colors)
        k = P.prog(lt, 0.15, 0.5)
        P.paste_center(img, P.pill_sprite(kicker, 38), W / 2, 200 + (1 - P.ease_out_cubic(k)) * -30,
                       1.0, k)
        for j, line in enumerate(headline):
            q = P.prog(lt, 0.25 + j * 0.12, 0.65 + j * 0.12)
            centered_text(img, line, 330 + j * 120, 108, alpha=q,
                          dy=(1 - P.ease_out_cubic(q)) * 40, stroke=10, shadow=9)
        sy = 330 + len(headline) * 120 + 15
        for j, line in enumerate(sub):
            q = P.prog(lt, 0.6 + j * 0.1, 1.0 + j * 0.1)
            centered_text(img, line, sy + j * 54, 38, alpha=q * 0.95, path=P.FONT_SEMI,
                          fill=(255, 255, 255))
        for j, (kind, idx, cx, cy, h, ang) in enumerate(shots):
            q = P.ease_out_back(P.prog(lt, 0.2 + j * 0.14, 0.85 + j * 0.14), 1.3)
            spr = L.phone(idx, h) if kind == "phone" else L.card(idx, h)
            P.paste_center(img, spr, cx, cy + (1 - q) * 1100 + 10 * math.sin(t * 1.6 + j * 1.7),
                           1.0, min(1, q * 2) if q > 0 else 0, ang + 1.5 * math.sin(t + j))
        brand_footer(img, lt)
        return img
    return render


def scene_cta(t):
    s = P.seg("cta")
    lt = t - s["start"]
    img = P.background(t, L.BRAND_BG)
    shots = [(SATISFYING, 290, 1430, 560, 8), (ICE, 790, 1430, 560, -8), (SORT, 540, 1420, 620, 0)]
    for j, (idx, cx, cy, h, ang) in enumerate(shots):
        q = P.ease_out_back(P.prog(lt, 0.25 + j * 0.12, 0.9 + j * 0.12), 1.3)
        P.paste_center(img, L.phone(idx, h), cx, cy + (1 - q) * 900 + 8 * math.sin(t * 1.6 + j),
                       1.0, min(1, q * 2) if q > 0 else 0, ang)
    P.paste_center(img, P.soft_circle(300, (255, 230, 150), 110), W / 2, 320,
                   1 + 0.05 * math.sin(t * 4))
    logo = P.shine(P.load_rgba(L.BRAND_LOGO, 380, sharpen=True), P.prog(lt, 0.7, 1.5))
    p = P.prog(lt, 0.0, 0.5)
    P.paste_center(img, logo, W / 2, 320 + 8 * math.sin(lt * 2.2), P.ease_out_back(p, 2.0),
                   min(1, p * 3))
    q = P.prog(lt, 0.3, 0.7)
    centered_text(img, "OUT NOW ON", 600, 72, stroke=9, shadow=7, scale=P.ease_out_back(q), alpha=q)
    centered_text(img, "GOOGLE PLAY", 700, 108, fill=P.PILL, stroke=11, shadow=9,
                  scale=P.ease_out_back(q), alpha=q)
    b = P.prog(lt, 0.6, 1.0)
    pulse = 1 + 0.035 * math.sin(lt * 6) if b >= 1 else 1
    P.paste_center(img, P.badge(), W / 2, 870, 0.9 * P.ease_out_back(b) * pulse, b)
    sp = P.prog(lt, 1.0, 1.4)
    centered_text(img, f"Search “{L.APP_NAME}” on Google Play", 1015, 46,
                  path=P.FONT_BOLD, stroke=5, alpha=sp)
    centered_text(img, P.PLAY_URL, 1070, 27, path=P.FONT_SEMI, fill=(235, 225, 255), alpha=sp)
    g = P.prog(lt, 1.3, 1.8)
    P.paste_center(img, P.load_rgba(os.path.join(P.ASSETS, "grkn_logo.png"), 180), W / 2, 1815,
                   P.ease_out_back(g), g)
    return img


P.SCENE_FN.update({
    "grkn": scene_grkn,
    "hook": scene_hook,
    "play": feature("play", L.ORANGE, "SIMPLE TO PLAY", ["Tap. Drive.", "Park!"],
                    ["Sort the car jam by colour —", "one satisfying move at a time."],
                    [("phone", SORT, 330, 1270, 960, -5), ("phone", NO_TIMERS, 750, 1260, 980, 5)]),
    "calm": feature("calm", L.INDIGO, "ZERO PRESSURE", ["No timers.", "No lives."],
                    ["Every level is solvable —", "100% fair, every time."],
                    [("phone", SATISFYING, 540, 1250, 1020, -3)]),
    "fresh": feature("fresh", L.RED, "ALWAYS FRESH", ["4 seasons,", "13 scenes."],
                     ["Ice, locks & bombs — from snowy", "streets to a neon city."],
                     [("card", ICE, 295, 1260, 860, -4), ("card", SEASONS, 785, 1260, 860, 4)]),
    "rewards": feature("rewards", PL.PINK, "MORE TO UNLOCK", ["Rewards", "every day."],
                       ["20 car sets • Daily lucky spin", "Bonus Escape every 10 levels"],
                       [("phone", SETS, 250, 1290, 820, -7), ("phone", BONUS, 830, 1290, 820, 7),
                        ("phone", DAILY, 540, 1270, 920, 0)]),
    "anywhere": feature("anywhere", L.GREEN, "PLAY ANYWHERE", ["No WiFi", "needed."],
                        ["On the commute, between meetings,", "or on the sofa."],
                        [("card", SORT, 540, 1250, 1020, -3)]),
    "cta": scene_cta,
})


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.HERE, "parkpop_vertical_1080x1920.mp4")
    L.write_srt(out.rsplit(".", 1)[0] + ".srt", PL.LINES)
    P.main(out)
