#!/usr/bin/env python3
"""NutPop promo video generator (1080x1920, 30 fps).

Builds a vertical promo from the store screenshots in assets/screens, the logos in
assets/, and the voice-over lines in assets/vo (see make_voiceover.py). Motion
graphics, music and sound effects are generated procedurally with Pillow + numpy,
and the result is encoded with ffmpeg.

Usage: python3 make_nutpop_promo.py [output.mp4]
"""
import glob
import math
import os
import random
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

W, H = 1080, 1920
FPS = 30
SR = 44100
SS = 4  # supersampling factor for procedural sprites

FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

NAVY = (36, 26, 64)
PILL = (255, 220, 80)
PLAY_URL = "play.google.com/store/apps/details?id=com.grknstudios.nutpop"

NUT_COLORS = [(235, 60, 70), (40, 110, 240), (250, 200, 30), (60, 190, 70),
              (240, 80, 150), (30, 190, 210), (250, 130, 30), (140, 80, 240)]

SCREENS = sorted(glob.glob(os.path.join(ASSETS, "screens", "*.png")))
VO_DIR = os.path.join(ASSETS, "vo")
SHOT_KEYS = [f"s{i + 1:02d}" for i in range(len(SCREENS))]

BG_PURPLE = ((104, 60, 235), (128, 88, 255))  # (base, ray)


# ---------------------------------------------------------------- timeline
def vo_len(key):
    with wave.open(os.path.join(VO_DIR, f"{key}.wav")) as wf:
        return wf.getnframes() / wf.getframerate()


VO_LEAD = 0.3  # voice starts this long after a segment begins
XF = 0.35      # transition length


def build_timeline():
    segs = []
    t = 0.0
    plan = [("grkn", "grkn", 0.7), ("intro", "intro", 0.55)]
    plan += [(f"shot{i}", k, 0.55) for i, k in enumerate(SHOT_KEYS)]
    plan += [("cta", "cta", 2.4)]
    for name, key, tail in plan:
        d = VO_LEAD + vo_len(key) + tail
        if name.startswith("shot"):
            d = max(d, 2.6)
        segs.append({"name": name, "vo": key, "start": t, "end": t + d})
        t += d
    return segs, t


SEGS, DURATION = build_timeline()
NFRAMES = int(DURATION * FPS)


# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.9):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def shade(c, f):
    return tuple(int(clamp(v * f, 0, 255)) for v in c)


def lighten(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


@lru_cache(None)
def text_sprite(text, path, size, fill, stroke=0, stroke_fill=NAVY, shadow=0):
    f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = stroke + shadow + 8
    img = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        d.text((pad - l, pad - t + shadow), text, font=f, fill=NAVY + (255,),
               stroke_width=stroke, stroke_fill=NAVY + (255,))
    d.text((pad - l, pad - t), text, font=f, fill=fill, stroke_width=stroke,
           stroke_fill=stroke_fill)
    return img


def paste_center(canvas, spr, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))),
                         Image.BILINEAR)
    if angle:
        spr = spr.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        spr = spr.copy()
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))


def draw_text(canvas, text, cx, cy, size, fill=(255, 255, 255), path=FONT_BLACK,
              stroke=0, stroke_fill=NAVY, shadow=0, scale=1.0, alpha=1.0, angle=0.0):
    paste_center(canvas, text_sprite(text, path, size, fill, stroke, stroke_fill, shadow),
                 cx, cy, scale, alpha, angle)


@lru_cache(None)
def pill_sprite(text, size):
    """Yellow rounded label in the style of the store screenshots."""
    spr = text_sprite(text, FONT_BLACK, size, NAVY + (255,))
    pw, ph = spr.width + 70, spr.height + 30
    img = Image.new("RGBA", (pw * SS, ph * SS), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, pw * SS - 1, ph * SS - 1], radius=ph * SS // 2,
                                          fill=PILL + (255,), outline=NAVY + (255,),
                                          width=7 * SS)
    img = img.resize((pw, ph), Image.LANCZOS)
    img.alpha_composite(spr, ((pw - spr.width) // 2, (ph - spr.height) // 2))
    return img


# ---------------------------------------------------------------- sprites
@lru_cache(None)
def load_rgba(path, width=None, sharpen=False):
    im = Image.open(path).convert("RGBA")
    if width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
        if sharpen:
            a = im.getchannel("A")
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
            im.putalpha(a)
    return im


@lru_cache(None)
def screen(i):
    return Image.open(SCREENS[i]).convert("RGBA").resize((W, H), Image.LANCZOS)


@lru_cache(None)
def hex_nut(ci, size=200):
    """Glossy 3D-ish hex nut seen from slightly above."""
    c = NUT_COLORS[ci % len(NUT_COLORS)]
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = s / 2, s * 0.44
    r = s * 0.42
    depth = s * 0.12

    def hexpts(r_, oy=0.0, sq=0.82):
        return [(cx + r_ * math.cos(math.pi / 6 + k * math.pi / 3),
                 cy + oy + r_ * sq * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]

    top, bot = hexpts(r), hexpts(r, depth)
    for k in range(6):  # visible side walls
        a, b = top[k], top[(k + 1) % 6]
        if a[1] + b[1] < 2 * cy - 1:
            continue
        f = 0.55 + 0.25 * math.cos(math.pi / 6 + k * math.pi / 3 + math.pi / 6)
        d.polygon([a, b, bot[(k + 1) % 6], bot[k]], fill=shade(c, f) + (255,))
    d.polygon(top, fill=c + (255,))
    d.polygon(hexpts(r * 0.86), fill=lighten(c, 0.18) + (255,))
    hr = r * 0.40  # bore with thread rings
    d.ellipse([cx - hr, cy - hr * 0.82, cx + hr, cy + hr * 0.82], fill=shade(c, 0.45) + (255,))
    for k in range(3):
        rr = hr * (0.92 - k * 0.14)
        d.ellipse([cx - rr, cy - rr * 0.82 + k * s * 0.012, cx + rr, cy + rr * 0.82],
                  outline=shade(c, 0.3) + (255,), width=int(s * 0.012))
    d.ellipse([cx - hr * 0.55, cy - hr * 0.35, cx + hr * 0.55, cy + hr * 0.65],
              fill=(20, 14, 30, 255))
    gl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([cx - r * 0.75, cy - r * 0.78, cx - r * 0.05, cy - r * 0.45],
                               fill=(255, 255, 255, 120))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(s * 0.02)))
    return img.resize((size, size), Image.LANCZOS)


@lru_cache(None)
def soft_circle(r, color, alpha=255):
    s = r * 2
    img = Image.new("RGBA", (s, s), color + (0,))
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse([r * 0.3, r * 0.3, s - r * 0.3, s - r * 0.3], fill=alpha)
    img.putalpha(m.filter(ImageFilter.GaussianBlur(r * 0.3)))
    return img


@lru_cache(None)
def hexagon(r, color):
    s = r * 2 * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = [(s / 2 + s / 2 * math.cos(k * math.pi / 3), s / 2 + s / 2 * math.sin(k * math.pi / 3))
           for k in range(6)]
    ImageDraw.Draw(img).polygon(pts, fill=color)
    return img.resize((r * 2, r * 2), Image.LANCZOS)


@lru_cache(None)
def sunburst(base, ray, phase_idx):
    """Ray background; phase_idx selects one of 90 rotation steps."""
    big = int(math.hypot(W, H) * 1.3)
    img = Image.new("RGB", (big, big), base)
    d = ImageDraw.Draw(img)
    n = 18
    off = phase_idx / 90 * (2 * math.pi / n)
    cx = cy = big / 2
    for k in range(n):
        a0 = off + k * 2 * math.pi / n
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + big * math.cos(a0), cy + big * math.sin(a0)),
                   (cx + big * math.cos(a1), cy + big * math.sin(a1))], fill=ray)
    x0, y0 = (big - W) // 2, (big - H) // 2 + 250
    img = img.crop((x0, y0, x0 + W, y0 + H))
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-W * 0.6, -H * 0.25, W * 1.6, H * 1.15], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(200))
    dark = Image.new("RGB", (W, H), shade(base, 0.55))
    return Image.composite(img, dark, v).convert("RGBA")


HEX_P = [(random.Random(i).random(), random.Random(i * 7 + 1).random(),
          random.Random(i * 13 + 2).randint(10, 26), random.Random(i * 3).random())
         for i in range(22)]


def background(t, colors=BG_PURPLE):
    bg = sunburst(colors[0], colors[1], int(t * 12) % 90).copy()
    for bx, by, r, ph in HEX_P:
        x = (bx * W + 40 * math.sin(t * 0.6 + ph * 6)) % W
        y = (by * H - t * (30 + 40 * ph)) % (H + 100) - 50
        paste_center(bg, hexagon(r, (255, 255, 255, 60)), x, y, 1.0, 1.0, t * 20 + ph * 60)
    return bg


def floating_nuts(canvas, t, t0, spots, alpha=1.0):
    """Big glossy nuts that fly out to fixed spots and bob."""
    for k, (x, y, ci, sc) in enumerate(spots):
        p = ease_out_back(prog(t, t0 + k * 0.08, t0 + k * 0.08 + 0.6), 1.6)
        if p <= 0:
            continue
        sx = W / 2 + (x - W / 2) * p
        sy = H / 2 + (y - H / 2) * p + 18 * math.sin(t * 2.2 + k)
        paste_center(canvas, hex_nut(ci), sx, sy, sc * min(1, p), alpha,
                     12 * math.sin(t * 1.3 + k * 2))


def burst(canvas, t, t0, cx, cy, n=26, seed=0, power=1.0):
    p = t - t0
    if p < 0 or p > 1.0:
        return
    rng = random.Random(seed)
    for k in range(n):
        ang = rng.uniform(0, math.tau)
        v = rng.uniform(350, 900) * power
        x = cx + math.cos(ang) * v * p
        y = cy + math.sin(ang) * v * p + 700 * p * p
        col = NUT_COLORS[k % len(NUT_COLORS)] + (255,) if k % 3 else (255, 255, 255, 255)
        paste_center(canvas, hexagon(rng.randint(8, 16), col), x, y, 1.0,
                     1 - clamp((p - 0.5) / 0.5), p * rng.uniform(-500, 500))


def shine(spr, p):
    """Diagonal light sweep across a sprite (p in 0..1)."""
    if p <= 0 or p >= 1:
        return spr
    w, h = spr.size
    band = Image.new("L", (w, h), 0)
    x = -w * 0.4 + p * w * 1.8
    ImageDraw.Draw(band).polygon([(x, 0), (x + w * 0.18, 0), (x + w * 0.18 - h * 0.4, h),
                                  (x - h * 0.4, h)], fill=150)
    band = band.filter(ImageFilter.GaussianBlur(10))
    band = Image.fromarray(np.minimum(np.asarray(band), np.asarray(spr.getchannel("A"))))
    out = spr.copy()
    white = Image.new("L", (w, h), 255)
    out.alpha_composite(Image.merge("RGBA", (white, white, white, band)))
    return out


# ---------------------------------------------------------------- scenes
def seg(name):
    return next(s for s in SEGS if s["name"] == name)


def scene_grkn(t):
    s = seg("grkn")
    lt = t - s["start"]
    img = background(t)
    paste_center(img, soft_circle(460, (255, 255, 255), 90), W / 2, 880,
                 1 + 0.05 * math.sin(t * 4))
    logo = shine(load_rgba(os.path.join(ASSETS, "grkn_logo.png"), 900), prog(lt, 0.7, 1.5))
    p = prog(lt, 0.05, 0.6)
    paste_center(img, logo, W / 2, 880 + 10 * math.sin(lt * 2.5), ease_out_back(p, 1.6),
                 min(1, p * 2))
    q = prog(lt, 0.7, 1.1)
    draw_text(img, "PRESENTS", W / 2, 1360, 64, stroke=10, shadow=8, scale=ease_out_back(q),
              alpha=q)
    return img


INTRO_NUTS = [(150, 330, 0, 0.9), (930, 420, 1, 0.8), (130, 1560, 2, 0.8),
              (950, 1640, 3, 0.95), (900, 1080, 4, 0.55), (170, 1000, 5, 0.55)]


def scene_intro(t):
    s = seg("intro")
    lt = t - s["start"]
    img = background(t)
    floating_nuts(img, t, s["start"] + 0.1, INTRO_NUTS)
    paste_center(img, soft_circle(420, (255, 230, 150), 140), W / 2, 760,
                 1 + 0.06 * math.sin(t * 5))
    logo = shine(load_rgba(os.path.join(ASSETS, "logo.png"), 640, sharpen=True),
                 prog(lt, 0.8, 1.6))
    p = prog(lt, 0.0, 0.6)
    ang = (1 - ease_out_cubic(p)) * -25 + math.sin(lt * 2) * 2
    paste_center(img, logo, W / 2, 760 + 12 * math.sin(lt * 2.4), ease_out_back(p, 2.2),
                 min(1, p * 3), ang)
    q = prog(lt, 0.5, 0.9)
    draw_text(img, "THE SATISFYING", W / 2, 1180, 86, stroke=12, shadow=10,
              scale=ease_out_back(q), alpha=q)
    q2 = prog(lt, 0.7, 1.1)
    paste_center(img, pill_sprite("NUT SORT PUZZLE", 70), W / 2, 1310, ease_out_back(q2), q2)
    burst(img, t, s["start"] + 0.45, W / 2, 760, n=30, seed=4, power=1.2)
    return img


def scene_shot(i):
    def render(t):
        s = seg(f"shot{i}")
        lt = t - s["start"]
        dur = s["end"] - s["start"]
        sc = 1.0 + 0.07 * ease_in_out(lt / (dur + XF))
        im = screen(i)
        if sc > 1.0:
            nw, nh = int(W * sc), int(H * sc)
            x0, y0 = (nw - W) // 2, int((nh - H) * 0.42)
            im = im.resize((nw, nh), Image.BILINEAR).crop((x0, y0, x0 + W, y0 + H))
        else:
            im = im.copy()
        burst(im, t, s["start"] + 0.15, W / 2, 300, n=22, seed=10 + i)
        return im
    return render


CTA_NUTS = [(120, 250, 2, 0.75), (960, 300, 0, 0.7), (110, 1250, 3, 0.6), (975, 1230, 1, 0.65)]


@lru_cache(None)
def badge():
    bw, bh = 700, 200
    s = SS
    img = Image.new("RGBA", (bw * s, bh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw * s - 1, bh * s - 1], radius=36 * s, fill=(0, 0, 0, 255),
                        outline=(170, 170, 170, 255), width=4 * s)
    ox, oy, tw, th = 50 * s, 38 * s, 108 * s, 124 * s
    A, B, C = (ox, oy), (ox, oy + th), (ox + tw, oy + th / 2)
    M = (ox + tw * 0.5, oy + th / 2)
    P1, P2 = (ox + tw * 0.72, oy + th * 0.37), (ox + tw * 0.72, oy + th * 0.63)
    d.polygon([A, M, B], fill=(0, 160, 255))
    d.polygon([A, P1, M], fill=(0, 220, 120))
    d.polygon([B, M, P2], fill=(255, 60, 70))
    d.polygon([P1, C, P2, M], fill=(255, 205, 0))
    img = img.resize((bw, bh), Image.LANCZOS)
    dd = ImageDraw.Draw(img)
    dd.text((200, 34), "GET IT ON", font=font(FONT_SEMI, 40), fill=(255, 255, 255))
    dd.text((196, 80), "Google Play", font=font(FONT_BOLD, 84), fill=(255, 255, 255))
    return img


@lru_cache(None)
def button():
    bw, bh = 820, 170
    img = Image.new("RGBA", (bw * SS, bh * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 14 * SS, bw * SS - 1, bh * SS - 1], radius=78 * SS,
                        fill=(20, 140, 80, 255))
    d.rounded_rectangle([0, 0, bw * SS - 1, (bh - 14) * SS], radius=78 * SS,
                        fill=(40, 200, 110, 255), outline=(255, 255, 255, 255), width=7 * SS)
    img = img.resize((bw, bh), Image.LANCZOS)
    spr = text_sprite("DOWNLOAD NOW", FONT_BLACK, 80, (255, 255, 255), 8, (15, 90, 50))
    img.alpha_composite(spr, ((bw - spr.width) // 2, (bh - 14 - spr.height) // 2))
    return img


def scene_cta(t):
    s = seg("cta")
    lt = t - s["start"]
    img = background(t)
    floating_nuts(img, t, s["start"] + 0.1, CTA_NUTS)
    paste_center(img, soft_circle(360, (255, 230, 150), 130), W / 2, 400,
                 1 + 0.05 * math.sin(t * 5))
    logo = shine(load_rgba(os.path.join(ASSETS, "logo.png"), 470, sharpen=True),
                 prog(lt, 0.6, 1.4))
    p = prog(lt, 0.0, 0.5)
    paste_center(img, logo, W / 2, 400 + 10 * math.sin(lt * 2.4), ease_out_back(p, 2.0),
                 min(1, p * 3))
    q = prog(lt, 0.3, 0.7)
    draw_text(img, "OUT NOW ON", W / 2, 715, 74, stroke=10, shadow=8, scale=ease_out_back(q),
              alpha=q)
    draw_text(img, "GOOGLE PLAY!", W / 2, 815, 100, fill=PILL, stroke=12, shadow=10,
              scale=ease_out_back(q), alpha=q)
    b = prog(lt, 0.6, 1.0)
    pulse = 1 + 0.04 * math.sin(lt * 7) if b >= 1 else 1
    paste_center(img, badge(), W / 2, 1015, ease_out_back(b) * pulse, b)
    d = prog(lt, 0.9, 1.3)
    bp = 1 + 0.06 * max(0, math.sin(lt * 9)) if d >= 1 else 1
    paste_center(img, button(), W / 2, 1230, ease_out_back(d) * bp, d)
    if d >= 1:  # tap hint
        tp = ((lt - 1.3) % 1.1) / 1.1
        px, py = W / 2 + 330, 1295 + 20 * math.sin(tp * math.tau)
        rr = int(30 + 60 * tp)
        ring = Image.new("RGBA", (rr * 2 + 10, rr * 2 + 10), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([5, 5, rr * 2 + 5, rr * 2 + 5],
                                     outline=(255, 255, 255, int(230 * (1 - tp))), width=7)
        img.alpha_composite(ring, (int(px - rr - 5), int(py - rr - 5)))
        paste_center(img, soft_circle(40, (255, 255, 255), 255), px, py)
    sp = prog(lt, 1.2, 1.6)
    paste_center(img, pill_sprite("No WiFi needed • No timer • No stress", 40),
                 W / 2, 1390, 1, sp)
    draw_text(img, "Search “NutPop” on Google Play", W / 2, 1480, 50, path=FONT_BOLD,
              stroke=6, alpha=sp)
    draw_text(img, PLAY_URL, W / 2, 1545, 30, path=FONT_SEMI, fill=(235, 225, 255), alpha=sp)
    g = prog(lt, 1.5, 2.0)
    paste_center(img, load_rgba(os.path.join(ASSETS, "grkn_logo.png"), 300), W / 2, 1745,
                 ease_out_back(g), g)
    return img


SCENE_FN = {"grkn": scene_grkn, "intro": scene_intro, "cta": scene_cta}
for _i in range(len(SCREENS)):
    SCENE_FN[f"shot{_i}"] = scene_shot(_i)


# ---------------------------------------------------------------- compositing
def scaled(img, scale, angle=0.0, under=None):
    """img scaled/rotated about the frame centre, over `under` (or dark)."""
    out = under.copy() if under is not None else Image.new("RGBA", (W, H), (20, 10, 40, 255))
    spr = img.resize((max(1, int(W * scale)), max(1, int(H * scale))), Image.BILINEAR)
    if angle:
        spr = spr.rotate(angle, resample=Image.BICUBIC, expand=True)
    out.paste(spr, (int(W / 2 - spr.width / 2), int(H / 2 - spr.height / 2)), spr)
    return out


def render_frame(fi):
    t = fi / FPS
    k = next(j for j, s in enumerate(SEGS) if t < s["end"] or j == len(SEGS) - 1)
    s = SEGS[k]
    img = SCENE_FN[s["name"]](t)
    lt = t - s["start"]
    if k > 0 and lt < XF:
        prev = SCENE_FN[SEGS[k - 1]["name"]](t)
        e = ease_in_out(lt / XF)
        kind = k % 4
        if kind == 0:    # push left
            out = Image.new("RGBA", (W, H))
            out.paste(prev, (int(-W * e), 0))
            out.paste(img, (int(W * (1 - e)), 0))
            img = out
        elif kind == 1:  # zoom punch with flash
            img = Image.blend(prev, scaled(img, 1.25 - 0.25 * ease_out_cubic(lt / XF)), e)
            fl = int(170 * (1 - abs(lt / XF - 0.5) * 2))
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, max(0, fl))))
        elif kind == 2:  # push up
            out = Image.new("RGBA", (W, H))
            out.paste(prev, (0, int(-H * e)))
            out.paste(img, (0, int(H * (1 - e))))
            img = out
        else:            # spin in over the darkened previous scene
            dark = prev.copy()
            dark.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(160 * e))))
            q = ease_out_back(lt / XF, 1.2)
            img = scaled(img, 0.6 + 0.4 * q, 14 * (1 - q), under=dark)
    fade = min(prog(t, 0, 0.3), 1 - prog(t, DURATION - 0.5, DURATION))
    if fade < 1:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fade)))))
    return img.convert("RGB").tobytes()


# ---------------------------------------------------------------- audio
def read_wav(path):
    with wave.open(path) as wf:
        sr = wf.getframerate()
        width = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
        ch = wf.getnchannels()
    data = np.frombuffer(raw, dtype=np.int16 if width == 2 else np.int32).astype(float)
    data /= 32768 if width == 2 else 2 ** 31
    if ch == 2:
        data = data.reshape(-1, 2).mean(1)
    if sr != SR:
        data = np.interp(np.arange(int(len(data) * SR / sr)) / SR, np.arange(len(data)) / sr, data)
    return data


def make_audio(path):
    n = int(DURATION * SR) + SR
    music, sfx, voice = np.zeros(n), np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(1)

    def add(buf, sig, start):
        i = int(start * SR)
        if 0 <= i < n:
            j = min(n, i + len(sig))
            buf[i:j] += sig[: j - i]

    def env(length, a=0.005, r=0.2):
        tt = np.arange(int(length * SR)) / SR
        return np.minimum(1, tt / a) * np.exp(-tt / r)

    def nf(m):
        return 440 * 2 ** ((m - 69) / 12)

    def noise(length):
        return np.diff(rng.standard_normal(int(length * SR)), prepend=0)

    beat = 60 / 120
    chords = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    for bar in range(int(DURATION / (beat * 4)) + 1):
        root, chord = chords[bar % 4]
        t0 = bar * beat * 4
        for b in range(4):
            tb = t0 + b * beat
            tt = np.arange(int(0.3 * SR)) / SR
            f = 50 + 110 * np.exp(-tt * 30)
            add(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.5, tb)
            if b % 2 == 1:
                add(music, noise(0.18) * env(0.18, 0.002, 0.05) * 0.15, tb)
            add(music, noise(0.06) * env(0.06, 0.001, 0.015) * 0.07, tb + beat / 2)
            L = beat * 0.9
            tt = np.arange(int(L * SR)) / SR
            fb = nf(root - 12)
            add(music, (np.sin(2 * np.pi * fb * tt) + 0.3 * np.sign(np.sin(2 * np.pi * fb * tt)))
                * env(L, 0.01, 0.25) * 0.2, tb)
        for st in range(8):
            m = chord[[0, 1, 2, 1, 2, 0, 2, 1][st]] + (12 if st in (3, 6) else 0)
            tt = np.arange(int(0.3 * SR)) / SR
            fq = nf(m)
            add(music, (np.sin(2 * np.pi * fq * tt) + 0.4 * np.sin(4 * np.pi * fq * tt)
                        + 0.15 * np.sin(6 * np.pi * fq * tt)) * env(0.3, 0.003, 0.09) * 0.09,
                t0 + st * beat / 2)

    for s in SEGS[1:]:  # whoosh into each transition, pop as the new scene lands
        nz = np.convolve(rng.standard_normal(int(0.5 * SR)), np.ones(40) / 40, mode="same")
        add(sfx, nz * np.sin(np.linspace(0, np.pi, len(nz))) ** 2 * 0.6, s["start"] - 0.25)
        tt = np.arange(int(0.3 * SR)) / SR
        f = 300 + 1300 * (1 - np.exp(-tt * 25))
        add(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(0.3, 0.002, 0.07) * 0.35,
            s["start"] + 0.12)

    for s in SEGS:
        add(voice, read_wav(os.path.join(VO_DIR, f"{s['vo']}.wav")), s["start"] + VO_LEAD)
    voice /= max(1e-9, np.max(np.abs(voice)))

    # duck the music under the voice
    k = int(0.15 * SR)
    lvl = np.convolve(np.abs(voice), np.ones(k) / k, mode="same")
    duck = np.convolve(1 - 0.55 * np.clip(lvl / 0.05, 0, 1), np.ones(k) / k, mode="same")
    music /= max(1e-9, np.max(np.abs(music)))
    mix = music * 0.42 * duck + sfx * 0.6 + voice * 0.95
    t_all = np.arange(n) / SR
    mix *= np.minimum(1, t_all / 0.05) * np.clip((DURATION - t_all) / 0.8, 0, 1)
    mix /= max(1e-9, np.max(np.abs(mix))) / 0.95
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((mix * 32767).astype(np.int16).tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "nutpop_promo_1080x1920.mp4")
    wav = out.rsplit(".", 1)[0] + "_audio.wav"
    for s in SEGS:
        print(f"{s['name']:>6}: {s['start']:6.2f} - {s['end']:6.2f}")
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, frame in enumerate(pool.imap(render_frame, range(NFRAMES), chunksize=4)):
            proc.stdin.write(frame)
            if k % 150 == 0:
                print(f"frame {k}/{NFRAMES}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print("wrote", out, f"({DURATION:.1f}s)")


if __name__ == "__main__":
    main()
