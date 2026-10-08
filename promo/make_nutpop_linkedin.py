#!/usr/bin/env python3
"""NutPop LinkedIn cut: 1920x1080 landscape, benefit-led, with voice-over.

Usage: python3 make_nutpop_linkedin.py [output.mp4]
Needs assets/vo_linkedin (python3 make_voiceover.py <model> <voices> linkedin).
Also writes a matching .srt caption file next to the video.
"""
import math
import os
import sys
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

import make_nutpop_promo as P
from make_voiceover import VARIANTS

P.W, P.H = 1920, 1080
W, H = P.W, P.H
P.TRANSITIONS = ["push_left", "fade"]
P.FADE_IN_COLOR = (255, 255, 255)

LINES = VARIANTS["linkedin"]["lines"]

# screenshot indices (assets/screens, sorted)
SORT, NO_TIMER, ICE, PLACES, SETS, PLATE, DAILY, SATISFYING = range(8)

PURPLE = ((104, 60, 235), (118, 78, 246))
ORANGE = ((236, 124, 26), (246, 142, 46))
INDIGO = ((84, 58, 214), (98, 74, 228))
RED = ((214, 64, 78), (226, 82, 94))
TEAL = ((22, 128, 150), (32, 144, 166))
GREEN = ((44, 150, 66), (58, 166, 80))

P.use_timeline([("grkn", "grkn", 0.8), ("hook", "hook", 0.6), ("play", "play", 0.5),
                ("calm", "calm", 0.5), ("fresh", "fresh", 0.5), ("rewards", "rewards", 0.5),
                ("anywhere", "anywhere", 0.5), ("cta", "cta", 3.0)],
               vo_dir=os.path.join(P.ASSETS, "vo_linkedin"), min_len=3.0)

PHONE_BOX = (233, 557, 847, 1896)  # phone mock-up inside the store screenshots


# ---------------------------------------------------------------- sprites
def with_shadow(spr, blur=26, offset=(0, 22), alpha=110):
    pad = blur * 3
    out = Image.new("RGBA", (spr.width + pad * 2, spr.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", spr.size, (10, 5, 30, 0))
    sh.putalpha(spr.getchannel("A").point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(spr, (pad, pad))
    return out


@lru_cache(None)
def src_screen(i):
    return Image.open(P.SCREENS[i]).convert("RGBA")


@lru_cache(None)
def phone(i, height):
    """Phone mock-up cut out of a store screenshot."""
    im = src_screen(i).crop(PHONE_BOX)
    mask = Image.new("L", (im.width * 4, im.height * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, mask.width - 1, mask.height - 1],
                                           radius=78 * 4, fill=255)
    im.putalpha(mask.resize(im.size, Image.LANCZOS))
    w = int(im.width * height / im.height)
    return with_shadow(im.resize((w, height), Image.LANCZOS))


@lru_cache(None)
def card(i, height):
    """Whole store screenshot as a rounded card."""
    im = src_screen(i).copy()
    mask = Image.new("L", (im.width, im.height), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=70,
                                           fill=255)
    im.putalpha(mask)
    w = int(im.width * height / im.height)
    return with_shadow(im.resize((w, height), Image.LANCZOS))


def text_left(img, text, x, y, size, fill=(255, 255, 255), path=P.FONT_BLACK, stroke=0,
              shadow=0, alpha=1.0, dx=0):
    spr = P.text_sprite(text, path, size, fill, stroke, P.NAVY, shadow)
    pad = stroke + shadow + 8
    P.paste_center(img, spr, x - pad + spr.width / 2 + dx, y, 1.0, alpha)


def pill_left(img, text, x, y, size=34, alpha=1.0, dx=0):
    spr = P.pill_sprite(text, size)
    P.paste_center(img, spr, x + spr.width / 2 + dx, y, 1.0, alpha)


def corner_brand(img, t, lt):
    a = P.prog(lt, 0.3, 0.8)
    logo = P.load_rgba(os.path.join(P.ASSETS, "logo.png"), 96, sharpen=True)
    P.paste_center(img, logo, 110, H - 85, 1.0, a)
    text_left(img, "Out now on Google Play", 175, H - 85, 30, path=P.FONT_BOLD, alpha=a * 0.95)


# ---------------------------------------------------------------- scenes
def scene_grkn(t):
    s = P.seg("grkn")
    lt = t - s["start"]
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    logo = P.load_rgba(os.path.join(P.ASSETS, "grkn_logo.png"), 700)
    logo = P.shine(logo, P.prog(lt, 0.8, 1.7))
    p = P.prog(lt, 0.05, 0.75)
    P.paste_center(img, logo, W / 2, 470 + 6 * math.sin(lt * 2), 0.9 + 0.1 * P.ease_out_cubic(p),
                   P.ease_out_cubic(p))
    q = P.prog(lt, 0.7, 1.2)
    P.draw_text(img, "P R E S E N T S", W / 2, 900 + (1 - P.ease_out_cubic(q)) * 20, 34,
                fill=P.NAVY + (255,), path=P.FONT_BOLD, alpha=q)
    return img


HOOK_NUTS = [(190, 190, 0, 0.75), (900, 150, 1, 0.6), (150, 880, 2, 0.7), (1010, 900, 3, 0.55),
             (1820, 160, 4, 0.55), (1800, 930, 5, 0.65)]


def scene_hook(t):
    s = P.seg("hook")
    lt = t - s["start"]
    img = P.background(t, PURPLE)
    P.floating_nuts(img, t, s["start"] + 0.1, HOOK_NUTS)
    P.paste_center(img, P.soft_circle(360, (255, 230, 150), 120), 560, 520,
                   1 + 0.05 * math.sin(t * 4))
    logo = P.load_rgba(os.path.join(P.ASSETS, "logo.png"), 470, sharpen=True)
    logo = P.shine(logo, P.prog(lt, 0.9, 1.7))
    p = P.prog(lt, 0.0, 0.6)
    P.paste_center(img, logo, 560, 520 + 10 * math.sin(lt * 2.2), P.ease_out_back(p, 2.0),
                   min(1, p * 3), (1 - P.ease_out_cubic(p)) * -20)
    q = P.prog(lt, 0.4, 0.8)
    rise = (1 - P.ease_out_cubic(q)) * 40
    P.draw_text(img, "NEED A 5-MINUTE", 1330, 400 + rise, 84, stroke=10, shadow=8, alpha=q)
    q2 = P.prog(lt, 0.6, 1.0)
    P.draw_text(img, "BRAIN BREAK?", 1330, 520 + (1 - P.ease_out_cubic(q2)) * 40, 128,
                fill=P.PILL, stroke=12, shadow=10, alpha=q2)
    tm = s["start"] + P.VO_LEAD + P.vo_len("hook") * 0.72  # "Meet NutPop"
    m = P.prog(t, tm, tm + 0.35)
    P.paste_center(img, P.pill_sprite("Meet NutPop →", 56), 1330, 690,
                   P.ease_out_back(m, 2.2), m)
    P.burst(img, t, tm, 560, 520, n=30, seed=7, power=1.1)
    return img


def feature(name, colors, kicker, headline, sub, shots):
    """Benefit slide: copy on the left, phones / cards flying in on the right.

    shots: [(kind, screen idx, cx, cy, height, angle)], kind "phone" or "card".
    """
    def render(t):
        s = P.seg(name)
        lt = t - s["start"]
        img = P.background(t, colors)
        x0 = 150
        k = P.prog(lt, 0.15, 0.5)
        pill_left(img, kicker, x0, 300, 34, k, dx=-(1 - P.ease_out_cubic(k)) * 60)
        for j, line in enumerate(headline):
            q = P.prog(lt, 0.25 + j * 0.12, 0.65 + j * 0.12)
            text_left(img, line, x0, 420 + j * 125, 112, stroke=10, shadow=9, alpha=q,
                      dx=-(1 - P.ease_out_cubic(q)) * 80)
        sy = 420 + len(headline) * 125 + 20
        for j, line in enumerate(sub):
            q = P.prog(lt, 0.6 + j * 0.1, 1.0 + j * 0.1)
            text_left(img, line, x0 + 4, sy + j * 58, 40, path=P.FONT_SEMI,
                      fill=(255, 255, 255), alpha=q * 0.95)
        for j, (kind, idx, cx, cy, h, ang) in enumerate(shots):
            q = P.ease_out_back(P.prog(lt, 0.2 + j * 0.14, 0.85 + j * 0.14), 1.3)
            spr = phone(idx, h) if kind == "phone" else card(idx, h)
            P.paste_center(img, spr, cx + (1 - q) * 900, cy + 10 * math.sin(t * 1.6 + j * 1.7),
                           1.0, min(1, q * 2) if q > 0 else 0, ang + 1.5 * math.sin(t + j))
        corner_brand(img, t, lt)
        return img
    return render


def scene_cta(t):
    s = P.seg("cta")
    lt = t - s["start"]
    img = P.background(t, PURPLE)
    shots = [(SATISFYING, 1170, 560, 760, 7), (SORT, 1680, 560, 760, -7), (NO_TIMER, 1425, 545, 840, 0)]
    for j, (idx, cx, cy, h, ang) in enumerate(shots):
        q = P.ease_out_back(P.prog(lt, 0.25 + j * 0.12, 0.9 + j * 0.12), 1.3)
        P.paste_center(img, phone(idx, h), cx + (1 - q) * 900, cy + 10 * math.sin(t * 1.6 + j),
                       1.0, min(1, q * 2) if q > 0 else 0, ang)
    cx = 560
    P.paste_center(img, P.soft_circle(280, (255, 230, 150), 110), cx, 200, 1 + 0.05 * math.sin(t * 4))
    logo = P.shine(P.load_rgba(os.path.join(P.ASSETS, "logo.png"), 330, sharpen=True),
                   P.prog(lt, 0.7, 1.5))
    p = P.prog(lt, 0.0, 0.5)
    P.paste_center(img, logo, cx, 195 + 8 * math.sin(lt * 2.2), P.ease_out_back(p, 2.0), min(1, p * 3))
    q = P.prog(lt, 0.3, 0.7)
    P.draw_text(img, "OUT NOW ON", cx, 440, 64, stroke=9, shadow=7, scale=P.ease_out_back(q), alpha=q)
    P.draw_text(img, "GOOGLE PLAY", cx, 530, 100, fill=P.PILL, stroke=11, shadow=9,
                scale=P.ease_out_back(q), alpha=q)
    b = P.prog(lt, 0.6, 1.0)
    pulse = 1 + 0.035 * math.sin(lt * 6) if b >= 1 else 1
    P.paste_center(img, P.badge(), cx, 690, 0.8 * P.ease_out_back(b) * pulse, b)
    sp = P.prog(lt, 1.0, 1.4)
    P.draw_text(img, "Search “NutPop” on Google Play", cx, 815, 44, path=P.FONT_BOLD,
                stroke=5, alpha=sp)
    P.draw_text(img, P.PLAY_URL, cx, 865, 26, path=P.FONT_SEMI, fill=(235, 225, 255), alpha=sp)
    g = P.prog(lt, 1.3, 1.8)
    P.paste_center(img, P.load_rgba(os.path.join(P.ASSETS, "grkn_logo.png"), 150), cx,
                   985, P.ease_out_back(g), g)
    return img


P.SCENE_FN.update({
    "grkn": scene_grkn,
    "hook": scene_hook,
    "play": feature("play", ORANGE, "SIMPLE TO PLAY", ["Tap. Sort.", "Pop!"],
                    ["Stack the nuts by colour —", "one satisfying move at a time."],
                    [("phone", SORT, 1250, 560, 860, 6), ("phone", NO_TIMER, 1640, 545, 880, -5)]),
    "calm": feature("calm", INDIGO, "ZERO PRESSURE", ["No timer.", "No stress."],
                    ["Every level is solvable,", "so every session ends on a win."],
                    [("phone", SATISFYING, 1450, 545, 900, -4)]),
    "fresh": feature("fresh", RED, "ALWAYS FRESH", ["New twists,", "20 places."],
                     ["Ice, locks & bombs — from a candy", "factory to outer space."],
                     [("card", ICE, 1260, 545, 860, 5), ("card", PLACES, 1650, 545, 860, -5)]),
    "rewards": feature("rewards", TEAL, "MORE TO UNLOCK", ["Rewards", "every day."],
                       ["9 nut sets • Lucky spin & star chest",
                        "Plate Drop bonus every 10 levels"],
                       [("phone", SETS, 1100, 560, 780, 7), ("phone", PLATE, 1690, 560, 780, -7),
                        ("phone", DAILY, 1395, 545, 860, 0)]),
    "anywhere": feature("anywhere", GREEN, "PLAY ANYWHERE", ["No WiFi", "needed."],
                        ["On the commute, between meetings,", "or on the sofa."],
                        [("card", SORT, 1450, 545, 900, -4)]),
    "cta": scene_cta,
})


def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as f:
        for n, s in enumerate(P.SEGS, 1):
            a = s["start"] + P.VO_LEAD
            text = LINES[s["vo"]].replace("G R K N", "GRKN")
            f.write(f"{n}\n{ts(a)} --> {ts(a + P.vo_len(s['vo']))}\n{text}\n\n")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(P.HERE, "nutpop_linkedin_1920x1080.mp4")
    write_srt(out.rsplit(".", 1)[0] + ".srt")
    P.main(out)
