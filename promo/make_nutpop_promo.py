#!/usr/bin/env python3
"""NutPop promo video generator (1080x1920, 30 fps).

Everything (graphics, animation, music, sound effects) is generated procedurally
with Pillow + numpy and encoded with ffmpeg.

Usage: python3 make_nutpop_promo.py [output.mp4]
"""
import math
import os
import random
import subprocess
import sys
import wave
from collections import deque
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
DURATION = 20.5
NFRAMES = int(DURATION * FPS)
SR = 44100

FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

PLAY_URL = "play.google.com/store/apps/details?id=com.grknstudios.nutpop"

# Scene boundaries (seconds)
T_GAME = 2.8
T_DONE = 11.3
T_FEAT = 13.4
T_CTA = 16.4
XF = 0.3  # crossfade length

NUT_COLORS = [
    (255, 92, 92),    # red
    (255, 196, 40),   # yellow
    (40, 200, 160),   # teal
    (150, 100, 255),  # purple
]

NUT_W, NUT_H = 200, 62
NUT_STEP = 56
CAP = 4
BOLT_ROD_H = CAP * NUT_STEP + 70


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.9):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def shade(c, f):
    return tuple(int(clamp(v * f, 0, 255)) for v in c)


def lighten(c, f):
    return tuple(int(v + (255 - v) * f) for v in c)


# ---------------------------------------------------------------- puzzle
def solve_puzzle():
    """Pick a random start position with a pleasant-length solution."""
    def moves_from(state):
        for i, src in enumerate(state):
            if not src:
                continue
            top = src[-1]
            g = 1
            while g < len(src) and src[-1 - g] == top:
                g += 1
            if g == len(src) and (g == CAP):
                continue  # already solved bolt
            for j, dst in enumerate(state):
                if i == j or len(dst) >= CAP:
                    continue
                if dst and dst[-1] != top:
                    continue
                if not dst and g == len(src):
                    continue  # pointless move of a whole bolt
                k = min(g, CAP - len(dst))
                ns = list(state)
                ns[i] = src[:-k]
                ns[j] = dst + (top,) * k
                yield (i, j, k), tuple(ns)

    def solved(state):
        return all(not b or (len(b) == CAP and len(set(b)) == 1) for b in state)

    rng = random.Random(7)
    for _ in range(4000):
        nuts = [c for c in range(4) for _ in range(CAP)]
        rng.shuffle(nuts)
        bolts = [tuple(nuts[i * CAP:(i + 1) * CAP]) for i in range(4)] + [(), ()]
        start = tuple(bolts)
        if any(len(set(b)) == 1 for b in start if b):
            continue
        prev = {start: None}
        q = deque([start])
        found = None
        while q:
            s = q.popleft()
            if solved(s):
                found = s
                break
            for mv, ns in moves_from(s):
                if ns not in prev:
                    prev[ns] = (s, mv)
                    q.append(ns)
        if not found:
            continue
        path = []
        s = found
        while prev[s] is not None:
            ps, mv = prev[s]
            path.append(mv)
            s = ps
        path.reverse()
        if 10 <= len(path) <= 12:
            return start, path
    raise RuntimeError("no puzzle found")


START, MOVES = solve_puzzle()

# bolt layout: two rows of three
BOLT_X = [W * 0.2, W * 0.5, W * 0.8] * 2
BOLT_BASE = [1160] * 3 + [1660] * 3

G0 = T_GAME + 0.55
G1 = T_DONE - 0.35
MOVE_D = (G1 - G0) / len(MOVES)


def build_timeline():
    states = [START]
    pops = []  # (time, bolt index, color)
    s = START
    for n, (i, j, k) in enumerate(MOVES):
        top = s[i][-1]
        ns = list(s)
        ns[i] = s[i][:-k]
        ns[j] = s[j] + (top,) * k
        s = tuple(ns)
        states.append(s)
        if len(s[j]) == CAP and len(set(s[j])) == 1:
            pops.append((G0 + (n + 1) * MOVE_D - 0.05, j, top))
    return states, pops


STATES, POPS = build_timeline()


# ---------------------------------------------------------------- sprites
SS = 4  # supersampling for sprites


@lru_cache(None)
def nut_sprite(ci):
    c = NUT_COLORS[ci]
    w, h = NUT_W * SS, NUT_H * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=16 * SS, fill=255)
    body = Image.new("RGBA", (w, h), c + (255,))
    d = ImageDraw.Draw(body)
    # hex nut side view: three faces
    d.rectangle([0, 0, int(w * 0.24), h], fill=shade(c, 0.78) + (255,))
    d.rectangle([int(w * 0.76), 0, w, h], fill=shade(c, 0.66) + (255,))
    d.rectangle([int(w * 0.24) - SS, 0, int(w * 0.24) + SS, h], fill=lighten(c, 0.25) + (255,))
    d.rectangle([int(w * 0.76) - SS, 0, int(w * 0.76) + SS, h], fill=shade(c, 0.55) + (255,))
    # top bevel highlight + bottom shade
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.rectangle([0, 0, w, int(h * 0.22)], fill=(255, 255, 255, 90))
    hd.rectangle([0, int(h * 0.80), w, h], fill=(0, 0, 0, 70))
    hd.rounded_rectangle([int(w * 0.30), int(h * 0.30), int(w * 0.60), int(h * 0.42)],
                         radius=6 * SS, fill=(255, 255, 255, 110))
    body = Image.alpha_composite(body, hl)
    img.paste(body, (0, 0), mask)
    ImageDraw.Draw(img).rounded_rectangle([SS, SS, w - SS, h - SS], radius=16 * SS,
                                          outline=shade(c, 0.45) + (255,), width=3 * SS)
    return img.resize((NUT_W, NUT_H), Image.LANCZOS)


@lru_cache(None)
def bolt_sprite():
    bw, bh = 250, BOLT_ROD_H + 46
    w, h = bw * SS, bh * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rod_w = 38 * SS
    rx0 = w // 2 - rod_w // 2
    # rod with horizontal metallic gradient
    rod = Image.new("RGBA", (rod_w, BOLT_ROD_H * SS), (0, 0, 0, 0))
    arr = np.zeros((BOLT_ROD_H * SS, rod_w, 4), np.uint8)
    xs = np.linspace(0, 1, rod_w)
    lum = 150 + 95 * np.exp(-((xs - 0.35) ** 2) / 0.03) - 60 * xs
    arr[..., 0] = np.clip(lum * 0.92, 0, 255)
    arr[..., 1] = np.clip(lum * 0.95, 0, 255)
    arr[..., 2] = np.clip(lum * 1.05, 0, 255)
    arr[..., 3] = 255
    rod = Image.fromarray(arr, "RGBA")
    rd = ImageDraw.Draw(rod)
    for y in range(10 * SS, BOLT_ROD_H * SS, 14 * SS):
        rd.line([(0, y + 5 * SS), (rod_w, y)], fill=(90, 95, 115, 160), width=2 * SS)
    rmask = Image.new("L", rod.size, 0)
    ImageDraw.Draw(rmask).rounded_rectangle([0, 0, rod_w - 1, BOLT_ROD_H * SS + 40 * SS],
                                            radius=rod_w // 2, fill=255)
    img.paste(rod, (rx0, 0), rmask)
    # base plate
    by = BOLT_ROD_H * SS - 6 * SS
    d.rounded_rectangle([0, by, w - 1, h - 1], radius=22 * SS, fill=(70, 52, 120, 255))
    d.rounded_rectangle([0, by, w - 1, by + 22 * SS], radius=14 * SS, fill=(120, 96, 190, 255))
    d.rounded_rectangle([SS * 2, by, w - SS * 2, h - SS * 2], radius=22 * SS,
                        outline=(40, 26, 80, 255), width=3 * SS)
    return img.resize((bw, bh), Image.LANCZOS)


@lru_cache(None)
def soft_circle(r, color, alpha=255):
    s = r * 2
    img = Image.new("RGBA", (s, s), color + (0,))
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse([r * 0.35, r * 0.35, s - r * 0.35, s - r * 0.35], fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.28))
    img.putalpha(m)
    return img


@lru_cache(None)
def circle_aa(r, color):
    s = r * 2 * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([0, 0, s - 1, s - 1], fill=color)
    return img.resize((r * 2, r * 2), Image.LANCZOS)


@lru_cache(None)
def gradient(top, bottom):
    t = np.linspace(0, 1, H)[:, None]
    top = np.array(top)[None, None, :]
    bottom = np.array(bottom)[None, None, :]
    arr = (top * (1 - t[..., None]) + bottom * t[..., None]).astype(np.uint8)
    arr = np.repeat(arr, W, axis=1)
    return Image.fromarray(arr, "RGB").convert("RGBA")


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


@lru_cache(None)
def text_sprite(text, path, size, fill, stroke=0, stroke_fill=(0, 0, 0), shadow=0):
    f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    pad = stroke + shadow + 8
    img = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shadow:
        d.text((pad - l, pad - t + shadow), text, font=f, fill=(20, 6, 40, 150),
               stroke_width=stroke, stroke_fill=(20, 6, 40, 150))
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
        a = spr.getchannel("A").point(lambda v: int(v * alpha))
        spr = spr.copy()
        spr.putalpha(a)
    canvas.alpha_composite(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)))


def draw_text(canvas, text, cx, cy, size, fill=(255, 255, 255), path=FONT_BLACK,
              stroke=0, stroke_fill=(40, 12, 70), shadow=0, scale=1.0, alpha=1.0, angle=0.0):
    spr = text_sprite(text, path, size, fill, stroke, stroke_fill, shadow)
    paste_center(canvas, spr, cx, cy, scale, alpha, angle)


# ---------------------------------------------------------------- shared FX
BOKEH = [(random.Random(i).random(), random.Random(i * 7 + 1).random(),
          random.Random(i * 13 + 2).randint(40, 120), random.Random(i * 3).random())
         for i in range(14)]


def background(t, top=(36, 12, 78), bottom=(150, 40, 140)):
    bg = gradient(top, bottom).copy()
    for i, (bx, by, r, ph) in enumerate(BOKEH):
        x = (bx * W + 30 * math.sin(t * 0.7 + ph * 6)) % W
        y = (by * H - t * (25 + 20 * ph)) % (H + 300) - 150
        col = NUT_COLORS[i % 4]
        paste_center(bg, soft_circle(r, col, 70), x, y)
    return bg


def falling_nuts(canvas, t, seed=3, n=12, speed=1.0, alpha=0.55):
    rng = random.Random(seed)
    for i in range(n):
        x = rng.uniform(60, W - 60)
        sp = rng.uniform(160, 320) * speed
        off = rng.uniform(0, H + 300)
        rot0 = rng.uniform(-40, 40)
        rs = rng.uniform(-60, 60)
        sc = rng.uniform(0.45, 0.8)
        y = (off + t * sp) % (H + 300) - 150
        paste_center(canvas, nut_sprite(i % 4), x, y, sc, alpha, rot0 + rs * t)


def burst(canvas, t, t0, cx, cy, color, n=34, seed=0, power=1.0):
    p = t - t0
    if p < 0 or p > 1.1:
        return
    rng = random.Random(seed)
    # shockwave ring
    if p < 0.45:
        rr = int(40 + 420 * ease_out_cubic(p / 0.45) * power)
        ring = Image.new("RGBA", (rr * 2 + 20, rr * 2 + 20), (0, 0, 0, 0))
        a = int(220 * (1 - p / 0.45))
        ImageDraw.Draw(ring).ellipse([10, 10, rr * 2 + 10, rr * 2 + 10],
                                     outline=(255, 255, 255, a), width=10)
        canvas.alpha_composite(ring, (int(cx - rr - 10), int(cy - rr - 10)))
    for k in range(n):
        ang = rng.uniform(0, math.tau)
        v = rng.uniform(380, 900) * power
        x = cx + math.cos(ang) * v * p
        y = cy + math.sin(ang) * v * p + 900 * p * p
        r = rng.randint(7, 16)
        col = color if k % 3 else (255, 255, 255)
        fade = 1 - clamp((p - 0.5) / 0.6)
        if fade > 0:
            paste_center(canvas, circle_aa(r, col + (255,)), x, y, 1.0, fade)


def confetti(canvas, t, t0, seed=11, n=80):
    p = t - t0
    if p < 0:
        return
    rng = random.Random(seed)
    for k in range(n):
        x0 = rng.uniform(0, W)
        vy = rng.uniform(380, 760)
        y = -60 - rng.uniform(0, 700) + vy * p
        if y > H + 40:
            continue
        x = x0 + 40 * math.sin(p * rng.uniform(2, 5) + k)
        col = NUT_COLORS[k % 4] if k % 5 else (255, 255, 255)
        w_, h_ = rng.randint(14, 22), rng.randint(24, 34)
        piece = Image.new("RGBA", (w_, h_), col + (255,))
        paste_center(canvas, piece, x, y, 1.0, 1.0, rng.uniform(0, 360) + p * rng.uniform(-400, 400))


def star_shape(r, color):
    s = r * 2 * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = (r if i % 2 == 0 else r * 0.48) * SS
        pts.append((s / 2 + rr * math.cos(a), s / 2 + rr * math.sin(a)))
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=color, outline=(120, 60, 0, 255))
    return img.resize((r * 2, r * 2), Image.LANCZOS)


STAR = None


def get_star():
    global STAR
    if STAR is None:
        STAR = star_shape(80, (255, 210, 40, 255))
    return STAR


# ---------------------------------------------------------------- logo
def logo(canvas, t, t0, cx, cy, scale=1.0):
    """Animated NUTPOP wordmark; letters drop in from t0."""
    letters = [("N", (255, 196, 40)), ("U", (255, 196, 40)), ("T", (255, 196, 40)),
               ("P", (255, 92, 140)), ("O", (255, 92, 140)), ("P", (255, 92, 140))]
    size = int(190 * scale)
    widths = []
    for ch, _ in letters:
        f = font(FONT_BLACK, size)
        l, _t, r, _b = f.getbbox(ch)
        widths.append(r - l)
    gap = int(-2 * scale)
    total = sum(widths) + gap * (len(letters) - 1)
    x = cx - total / 2
    for i, (ch, col) in enumerate(letters):
        p = prog(t, t0 + i * 0.08, t0 + i * 0.08 + 0.55)
        if p <= 0:
            x += widths[i] + gap
            continue
        yy = cy - (1 - ease_out_back(p, 2.4)) * 260 * scale
        wob = math.sin((t - t0) * 3.0 + i * 0.9) * 8 * scale if p >= 1 else 0
        ang = math.sin((t - t0) * 2.2 + i) * 3 if p >= 1 else 0
        draw_text(canvas, ch, x + widths[i] / 2, yy + wob, size, fill=col,
                  stroke=int(14 * scale), stroke_fill=(40, 12, 70), shadow=int(16 * scale),
                  alpha=min(1, p * 3), angle=ang)
        x += widths[i] + gap


# ---------------------------------------------------------------- scenes
def scene_intro(t):
    img = background(t)
    falling_nuts(img, t, seed=5, n=14, speed=1.2, alpha=0.6)
    # pulsing glow behind logo
    g = 1 + 0.06 * math.sin(t * 6)
    paste_center(img, soft_circle(420, (255, 200, 120), 120), W / 2, 700, g)
    logo(img, t, 0.15, W / 2, 700, 1.0)
    # a bolt at the bottom collecting nuts
    base = 1800
    bs = bolt_sprite()
    by = (1 - ease_out_back(prog(t, 0.3, 0.8))) * 600
    img.alpha_composite(bs, (int(W / 2 - bs.width / 2), int(base - bs.height + 12 + by)))
    for idx in range(CAP):
        a = 0.8 + idx * 0.3
        q = prog(t, a, a + 0.3)
        if q <= 0:
            continue
        x, y = W / 2, base - 34 - NUT_H / 2 - idx * NUT_STEP
        yy = y - (1 - q * q) * 900
        paste_center(img, nut_sprite(1), x, yy + by, 1.0, 1.0)
    burst(img, t, 2.05, W / 2, base - 170, NUT_COLORS[1], seed=99, power=0.8)
    if t >= 2.05:
        paste_center(img, soft_circle(230, NUT_COLORS[1], 150), W / 2, base - 170,
                     1.0, prog(t, 2.05, 2.2))
    p = prog(t, 0.9, 1.3)
    draw_text(img, "THE SATISFYING", W / 2, 960, 64, fill=(255, 255, 255), stroke=8,
              shadow=8, scale=ease_out_back(p), alpha=p)
    p2 = prog(t, 1.1, 1.5)
    draw_text(img, "NUT SORT PUZZLE", W / 2, 1050, 72, fill=(255, 220, 90), stroke=8,
              shadow=8, scale=ease_out_back(p2), alpha=p2)
    p3 = prog(t, 1.6, 2.0)
    draw_text(img, "Can you sort them all?", W / 2, 1200, 56, path=FONT_BOLD,
              fill=(255, 255, 255), stroke=6, alpha=p3,
              scale=0.9 + 0.1 * ease_out_cubic(p3))
    return img


def bolt_nut_pos(b, idx):
    return BOLT_X[b], BOLT_BASE[b] - 34 - NUT_H / 2 - idx * NUT_STEP


def scene_game(t):
    img = background(t, (24, 14, 70), (90, 40, 150))
    # header
    p = prog(t, T_GAME + 0.05, T_GAME + 0.4)
    pill = Image.new("RGBA", (330, 86), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, 329, 85], radius=43, fill=(255, 255, 255, 40),
                                           outline=(255, 255, 255, 120), width=3)
    paste_center(img, pill, W / 2, 230, 1, p)
    draw_text(img, "LEVEL 27", W / 2, 230, 46, path=FONT_BOLD, alpha=p)
    captions = [(T_GAME, G0 + MOVE_D * 4, "SORT THE NUTS!"),
                (G0 + MOVE_D * 4, G0 + MOVE_D * 8, "MATCH THE COLORS"),
                (G0 + MOVE_D * 8, T_DONE - 0.1, "POP EVERY BOLT!")]
    for a, b, txt in captions:
        if a <= t < b:
            pp = prog(t, a, a + 0.35)
            draw_text(img, txt, W / 2, 390, 92, fill=(255, 255, 255), stroke=12, shadow=12,
                      scale=ease_out_back(pp), alpha=pp)
    hp = prog(t, T_GAME + 0.3, T_GAME + 0.7)
    draw_text(img, "Tap a bolt to move the top nuts", W / 2, 500, 40, path=FONT_SEMI,
              fill=(230, 220, 255), alpha=hp * 0.95 * (1 - prog(t, T_DONE - 0.3, T_DONE)))

    # which move is in progress
    n = int((t - G0) // MOVE_D) if t >= G0 else -1
    n = min(n, len(MOVES))
    state = STATES[max(0, min(n, len(MOVES)))]
    moving = None
    if 0 <= n < len(MOVES):
        moving = (MOVES[n], (t - G0 - n * MOVE_D) / MOVE_D)
        state = STATES[n]

    intro = prog(t, T_GAME, T_GAME + 0.5)
    # bolts + glow on completed ones
    for b in range(6):
        bx, base = BOLT_X[b], BOLT_BASE[b]
        dy = (1 - ease_out_back(prog(t, T_GAME + b * 0.04, T_GAME + b * 0.04 + 0.45))) * 500
        full = len(state[b]) == CAP and len(set(state[b])) == 1
        if full and not (moving and moving[0][1] == b):
            paste_center(img, soft_circle(230, NUT_COLORS[state[b][0]], 150), bx,
                         base - 170 + dy)
        bs = bolt_sprite()
        img.alpha_composite(bs, (int(bx - bs.width / 2), int(base - bs.height + 12 + dy)))
        stack = state[b]
        hide = 0
        if moving and moving[0][0] == b:
            hide = moving[0][2]
        for idx, c in enumerate(stack[:len(stack) - hide]):
            x, y = bolt_nut_pos(b, idx)
            paste_center(img, nut_sprite(c), x, y + dy, alpha=intro)

    if moving:
        (i, j, k), q = moving
        state_n = STATES[n]
        color = state_n[i][-1]
        src_top = len(state_n[i]) - k
        dst_top = len(state_n[j])
        hover = hover_j = min(BOLT_BASE[i], BOLT_BASE[j]) - BOLT_ROD_H - 90
        for m in range(k):
            sx, sy = bolt_nut_pos(i, src_top + m)
            ex, ey = bolt_nut_pos(j, dst_top + m)
            hy_i = hover - m * NUT_STEP
            hy_j = hover_j - m * NUT_STEP
            if q < 0.3:
                e = ease_out_cubic(q / 0.3)
                x, y = sx, sy + (hy_i - sy) * e
                ang = 0
            elif q < 0.68:
                e = ease_in_out((q - 0.3) / 0.38)
                x = sx + (ex - sx) * e
                y = hy_i + (hy_j - hy_i) * e - math.sin(e * math.pi) * 110
                ang = math.sin(e * math.pi) * 10 * (1 if ex > sx else -1)
            else:
                e = ease_out_cubic((q - 0.68) / 0.32)
                x, y = ex, hy_j + (ey - hy_j) * e
                ang = 0
            paste_center(img, nut_sprite(color), x, y, 1.06, 1.0, ang)
        # tap ripple on source bolt
        if q < 0.35:
            rp = q / 0.35
            rr = int(50 + 70 * rp)
            ring = Image.new("RGBA", (rr * 2 + 10, rr * 2 + 10), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([5, 5, rr * 2 + 5, rr * 2 + 5],
                                         outline=(255, 255, 255, int(230 * (1 - rp))), width=8)
            img.alpha_composite(ring, (int(BOLT_X[i] - rr - 5), int(BOLT_BASE[i] - 150 - rr - 5)))
            paste_center(img, circle_aa(26, (255, 255, 255, 200)), BOLT_X[i], BOLT_BASE[i] - 150,
                         1.0, 1 - rp)

    # pops
    for k_, (tp, b, c) in enumerate(POPS):
        cx, cy = BOLT_X[b], BOLT_BASE[b] - 170
        burst(img, t, tp, cx, cy, NUT_COLORS[c], seed=k_ + 1)
        pp = t - tp
        if 0 <= pp < 0.9:
            sc = ease_out_back(pp / 0.3, 2.6)
            draw_text(img, "POP!", cx, cy - 250 - pp * 60, 110, fill=lighten(NUT_COLORS[c], 0.3),
                      stroke=12, shadow=10, scale=sc, alpha=1 - clamp((pp - 0.6) / 0.3),
                      angle=-8 + 16 * (k_ % 2))

    # Level complete overlay
    if t >= T_DONE - 0.1:
        lp = prog(t, T_DONE - 0.1, T_DONE + 0.25)
        dim = Image.new("RGBA", (W, H), (20, 6, 40, int(150 * lp)))
        img.alpha_composite(dim)
        confetti(img, t, T_DONE - 0.1)
        bp = ease_out_back(prog(t, T_DONE, T_DONE + 0.45))
        banner = Image.new("RGBA", (980, 260), (0, 0, 0, 0))
        bd = ImageDraw.Draw(banner)
        bd.rounded_rectangle([0, 0, 979, 259], radius=60, fill=(255, 92, 140, 255),
                             outline=(255, 255, 255, 255), width=8)
        paste_center(img, banner, W / 2, 960, bp)
        draw_text(img, "LEVEL", W / 2, 905, 84, stroke=8, shadow=6, scale=bp)
        draw_text(img, "COMPLETE!", W / 2, 1010, 100, fill=(255, 230, 90), stroke=10, shadow=8,
                  scale=bp)
        for s in range(3):
            sp = prog(t, T_DONE + 0.4 + s * 0.18, T_DONE + 0.75 + s * 0.18)
            yoff = -40 if s == 1 else 0
            paste_center(img, get_star(), W / 2 + (s - 1) * 210, 720 + yoff,
                         ease_out_back(sp, 2.8) * (1.15 if s == 1 else 0.95), sp,
                         (s - 1) * -12 + math.sin(t * 4 + s) * 4)
    return img


FEATURES = [
    ("Colorful brain-teasing levels", 0),
    ("Super satisfying POPs", 1),
    ("Easy to learn, hard to master", 2),
    ("Relax & unwind anytime", 3),
]


def scene_features(t):
    img = background(t, (20, 30, 90), (40, 140, 170))
    falling_nuts(img, t, seed=9, n=8, speed=0.6, alpha=0.35)
    p = prog(t, T_FEAT, T_FEAT + 0.4)
    draw_text(img, "WHY PLAYERS", W / 2, 400, 96, stroke=12, shadow=12,
              scale=ease_out_back(p), alpha=p)
    draw_text(img, "LOVE IT", W / 2, 510, 120, fill=(255, 220, 90), stroke=12, shadow=12,
              scale=ease_out_back(p), alpha=p)
    for i, (txt, ci) in enumerate(FEATURES):
        a = T_FEAT + 0.35 + i * 0.4
        q = ease_out_back(prog(t, a, a + 0.45), 1.4)
        x = W / 2 + (1 - q) * W
        y = 760 + i * 210
        card = Image.new("RGBA", (940, 170), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([0, 0, 939, 169], radius=40,
                                               fill=(255, 255, 255, 235))
        paste_center(img, card, x, y)
        paste_center(img, nut_sprite(ci), x - 355, y, 0.62, 1.0,
                     math.sin(t * 3 + i) * 8)
        spr = text_sprite(txt, FONT_BOLD, 46, (40, 20, 80))
        img.alpha_composite(spr, (int(x - 270), int(y - spr.height / 2)))
    return img


def play_badge(scale=1.0):
    bw, bh = 700, 200
    s = SS
    img = Image.new("RGBA", (bw * s, bh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw * s - 1, bh * s - 1], radius=36 * s, fill=(0, 0, 0, 255),
                        outline=(170, 170, 170, 255), width=4 * s)
    # play triangle (4 colours)
    ox, oy, tw, th = 50 * s, 38 * s, 108 * s, 124 * s
    A = (ox, oy)
    B = (ox, oy + th)
    C = (ox + tw, oy + th / 2)
    M = (ox + tw * 0.5, oy + th / 2)
    d.polygon([A, M, B], fill=(0, 160, 255))
    d.polygon([A, (ox + tw * 0.72, oy + th * 0.37), M], fill=(0, 220, 120))
    d.polygon([B, M, (ox + tw * 0.72, oy + th * 0.63)], fill=(255, 60, 70))
    d.polygon([(ox + tw * 0.72, oy + th * 0.37), C, (ox + tw * 0.72, oy + th * 0.63), M],
              fill=(255, 205, 0))
    img = img.resize((bw, bh), Image.LANCZOS)
    dd = ImageDraw.Draw(img)
    dd.text((200, 34), "GET IT ON", font=font(FONT_SEMI, 40), fill=(255, 255, 255))
    dd.text((196, 80), "Google Play", font=font(FONT_BOLD, 84), fill=(255, 255, 255))
    return img


BADGE = None


def scene_cta(t):
    global BADGE
    if BADGE is None:
        BADGE = play_badge()
    img = background(t, (36, 12, 78), (190, 50, 120))
    falling_nuts(img, t, seed=21, n=14, speed=1.0, alpha=0.5)
    paste_center(img, soft_circle(380, (255, 200, 120), 110), W / 2, 470,
                 1 + 0.05 * math.sin(t * 5))
    logo(img, t, T_CTA, W / 2, 470, 0.85)
    p = prog(t, T_CTA + 0.5, T_CTA + 0.85)
    draw_text(img, "OUT NOW ON", W / 2, 760, 70, stroke=8, shadow=8,
              scale=ease_out_back(p), alpha=p)
    draw_text(img, "GOOGLE PLAY!", W / 2, 860, 96, fill=(255, 220, 90), stroke=10, shadow=10,
              scale=ease_out_back(p), alpha=p)
    bp = prog(t, T_CTA + 0.8, T_CTA + 1.2)
    pulse = 1 + 0.045 * math.sin((t - T_CTA) * 7) if bp >= 1 else 1
    paste_center(img, BADGE, W / 2, 1100, ease_out_back(bp) * pulse, bp)
    # "DOWNLOAD NOW" button
    dp = prog(t, T_CTA + 1.1, T_CTA + 1.5)
    btn = Image.new("RGBA", (820, 170), (0, 0, 0, 0))
    ImageDraw.Draw(btn).rounded_rectangle([0, 0, 819, 169], radius=85, fill=(40, 210, 120, 255),
                                          outline=(255, 255, 255, 255), width=8)
    bpulse = 1 + 0.06 * max(0, math.sin((t - T_CTA) * 9)) if dp >= 1 else 1
    paste_center(img, btn, W / 2, 1360, ease_out_back(dp) * bpulse, dp)
    draw_text(img, "DOWNLOAD NOW", W / 2, 1360, 84, stroke=8, stroke_fill=(10, 90, 50),
              scale=ease_out_back(dp) * bpulse, alpha=dp)
    # tap hand-ish pointer
    if dp >= 1:
        tp = ((t - T_CTA - 1.5) % 1.2) / 1.2
        px, py = W / 2 + 360, 1450 + 25 * math.sin(tp * math.tau)
        paste_center(img, circle_aa(34, (255, 255, 255, 230)), px, py)
        rr = int(34 + 60 * tp)
        ring = Image.new("RGBA", (rr * 2 + 10, rr * 2 + 10), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse([5, 5, rr * 2 + 5, rr * 2 + 5],
                                     outline=(255, 255, 255, int(220 * (1 - tp))), width=6)
        img.alpha_composite(ring, (int(px - rr - 5), int(py - rr - 5)))
    sp = prog(t, T_CTA + 1.6, T_CTA + 2.0)
    draw_text(img, "Search “NutPop” on Google Play", W / 2, 1580, 50, path=FONT_BOLD,
              stroke=5, alpha=sp)
    draw_text(img, PLAY_URL, W / 2, 1660, 30, path=FONT_SEMI, fill=(240, 225, 255), alpha=sp)
    draw_text(img, "by GRKN Studios", W / 2, 1790, 40, path=FONT_SEMI,
              fill=(255, 255, 255), alpha=sp * 0.85)
    return img


SCENES = [(0.0, T_GAME, scene_intro), (T_GAME, T_FEAT, scene_game),
          (T_FEAT, T_CTA, scene_features), (T_CTA, DURATION + 1, scene_cta)]


def render_frame(fi):
    t = fi / FPS
    cur = None
    for k, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            cur = k
    img = SCENES[cur][2](t)
    # crossfade from previous scene + white flash
    a = SCENES[cur][0]
    if cur > 0 and t < a + XF:
        prev = SCENES[cur - 1][2](t)
        alpha = ease_in_out((t - a) / XF)
        img = Image.blend(prev, img, alpha)
        flash = int(160 * (1 - abs((t - a) / XF - 0.5) * 2))
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, max(0, flash))))
    # small camera shake on pops
    for tp, _b, _c in POPS:
        if 0 <= t - tp < 0.25:
            amp = 12 * (1 - (t - tp) / 0.25)
            dx = int(amp * math.sin(t * 90))
            dy = int(amp * math.cos(t * 77))
            img = img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy),
                                fillcolor=(30, 10, 60, 255))
    # global fade in/out
    fade = min(prog(t, 0, 0.25), 1 - prog(t, DURATION - 0.35, DURATION))
    if fade < 1:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fade)))))
    return img.convert("RGB").tobytes()


# ---------------------------------------------------------------- audio
def make_audio(path):
    n = int(DURATION * SR)
    out = np.zeros(n)
    t_all = np.arange(n) / SR

    def add(sig, start):
        i = int(start * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        out[i:j] += sig[: j - i]

    def env(length, a=0.005, r=0.2):
        tt = np.arange(int(length * SR)) / SR
        return np.minimum(1, tt / a) * np.exp(-tt / r)

    def note_freq(m):
        return 440 * 2 ** ((m - 69) / 12)

    bpm = 124
    beat = 60 / bpm
    # C  G  Am  F  (midi roots)
    prog_ = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    nbars = int(DURATION / (beat * 4)) + 1
    rng = np.random.default_rng(1)
    for bar in range(nbars):
        root, chord = prog_[bar % 4]
        t0 = bar * beat * 4
        for b in range(4):
            tb = t0 + b * beat
            # kick
            L = 0.3
            tt = np.arange(int(L * SR)) / SR
            f = 50 + 110 * np.exp(-tt * 30)
            kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.55
            if tb > 0.2:
                add(kick, tb)
            # clap on 2 & 4
            if b % 2 == 1:
                L = 0.18
                nz = rng.standard_normal(int(L * SR))
                nz = np.diff(nz, prepend=0) * env(L, 0.002, 0.05) * 0.18
                add(nz, tb)
            # hats offbeat
            L = 0.06
            hz = np.diff(rng.standard_normal(int(L * SR)), prepend=0) * env(L, 0.001, 0.015) * 0.08
            add(hz, tb + beat / 2)
            # bass
            L = beat * 0.9
            tt = np.arange(int(L * SR)) / SR
            fb = note_freq(root - 12 if b % 2 else root - 12)
            bass = (np.sin(2 * np.pi * fb * tt) + 0.3 * np.sign(np.sin(2 * np.pi * fb * tt))) \
                * env(L, 0.01, 0.25) * 0.22
            add(bass, tb)
        # plucky arpeggio (8ths)
        for s in range(8):
            m = chord[[0, 1, 2, 1, 2, 0, 2, 1][s]] + (12 if s in (3, 6) else 0)
            L = 0.3
            tt = np.arange(int(L * SR)) / SR
            fq = note_freq(m)
            pl = (np.sin(2 * np.pi * fq * tt) + 0.4 * np.sin(4 * np.pi * fq * tt)
                  + 0.15 * np.sin(6 * np.pi * fq * tt)) * env(L, 0.003, 0.09) * 0.1
            add(pl, t0 + s * beat / 2)

    # sfx: tap clicks and drops for every move
    for k_ in range(len(MOVES)):
        ts = G0 + k_ * MOVE_D
        L = 0.05
        tt = np.arange(int(L * SR)) / SR
        add(np.sin(2 * np.pi * 1800 * tt) * env(L, 0.001, 0.01) * 0.25, ts)
        L = 0.12
        tt = np.arange(int(L * SR)) / SR
        add(np.sin(2 * np.pi * (520 - 1500 * tt) * tt) * env(L, 0.002, 0.04) * 0.3,
            ts + MOVE_D * 0.95)
    # pops
    for tp, _b, _c in POPS:
        L = 0.35
        tt = np.arange(int(L * SR)) / SR
        f = 300 + 1400 * (1 - np.exp(-tt * 25))
        pop = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(L, 0.002, 0.08) * 0.45
        add(pop, tp)
        add(np.diff(rng.standard_normal(int(0.08 * SR)), prepend=0) * env(0.08, 0.001, 0.02)
            * 0.2, tp)
    add(np.sin(2 * np.pi * np.cumsum(300 + 1400 * (1 - np.exp(-np.arange(int(0.35 * SR)) / SR * 25))) / SR)
        * env(0.35, 0.002, 0.08) * 0.45, 2.05)
    for idx in range(CAP):
        L = 0.12
        tt = np.arange(int(L * SR)) / SR
        add(np.sin(2 * np.pi * (520 - 1500 * tt) * tt) * env(L, 0.002, 0.04) * 0.3, 1.1 + idx * 0.3)
    # whooshes at transitions
    for tt0 in (T_GAME, T_FEAT, T_CTA):
        L = 0.6
        nz = rng.standard_normal(int(L * SR))
        k = np.ones(40) / 40
        nz = np.convolve(nz, k, mode="same")
        e = np.sin(np.linspace(0, np.pi, len(nz))) ** 2
        add(nz * e * 0.5, tt0 - 0.3)
    # level-complete jingle
    for s, m in enumerate([72, 76, 79, 84, 88]):
        L = 0.5
        tt = np.arange(int(L * SR)) / SR
        fq = note_freq(m)
        add((np.sin(2 * np.pi * fq * tt) + 0.3 * np.sin(4 * np.pi * fq * tt))
            * env(L, 0.003, 0.2) * 0.22, T_DONE + s * 0.09)
    # feature card blips
    for i in range(len(FEATURES)):
        L = 0.15
        tt = np.arange(int(L * SR)) / SR
        add(np.sin(2 * np.pi * note_freq(76 + i * 3) * tt) * env(L, 0.002, 0.05) * 0.2,
            T_FEAT + 0.35 + i * 0.4)

    fade = np.minimum(1, t_all / 0.05) * np.minimum(1, (DURATION - t_all) / 0.8)
    out *= fade
    out /= max(1e-9, np.max(np.abs(out))) / 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "nutpop_promo_1080x1920.mp4"
    wav = out.rsplit(".", 1)[0] + "_audio.wav"
    print(f"puzzle moves: {len(MOVES)}, pops at {[round(p[0], 2) for p in POPS]}")
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, frame in enumerate(pool.imap(render_frame, range(NFRAMES), chunksize=4)):
            proc.stdin.write(frame)
            if k % 60 == 0:
                print(f"frame {k}/{NFRAMES}", flush=True)
    proc.stdin.close()
    proc.wait()
    os.remove(wav)
    print("wrote", out)


if __name__ == "__main__":
    main()
