"""Scene building blocks shared by the NutPop variant cuts (hook, top5).

Built on top of make_nutpop_promo, which owns the timeline, compositing, audio
mix and the call-to-action scene.
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

import make_nutpop_promo as P

# phone screen area inside the store screenshots (x0, y0, x1, y1)
PHONE = (250, 575, 830, 1870)
HILITE = (255, 220, 80)


def seg(name):
    return P.seg(name)


@lru_cache(None)
def blurred_screen(i):
    im = P.screen(i).filter(ImageFilter.GaussianBlur(28))
    im.alpha_composite(Image.new("RGBA", im.size, (10, 5, 25, 120)))
    return im


@lru_cache(None)
def phone_crop(i):
    x0, y0, x1, y1 = PHONE
    return P.screen(i).crop((x0, y0, x1, y1))


def phone_scene(name, i, pan=(0.25, 0.45), zoom=(1.0, 1.08)):
    """Full-bleed close-up of the phone screen, slowly panning and zooming.

    pan: vertical position of the window inside the phone screen (0 top .. 1 bottom)
    at the start and end of the segment.
    """
    def render(t):
        s = seg(name)
        q = P.ease_in_out((t - s["start"]) / (s["end"] - s["start"] + P.XF))
        crop = phone_crop(i)
        cw, ch = crop.size
        z = zoom[0] + (zoom[1] - zoom[0]) * q
        ww = cw / z
        wh = ww * P.H / P.W
        py = pan[0] + (pan[1] - pan[0]) * q
        x0 = (cw - ww) / 2
        y0 = (ch - wh) * py
        win = crop.resize((P.W, P.H), Image.BICUBIC, box=(x0, y0, x0 + ww, y0 + wh))
        a = win.getchannel("A")
        win = win.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
        win.putalpha(a)
        return win
    return render


def full_shot(name, i, zoom=0.07):
    """Store screenshot with a slow push-in."""
    def render(t):
        s = seg(name)
        q = P.ease_in_out((t - s["start"]) / (s["end"] - s["start"] + P.XF))
        sc = 1.0 + zoom * q
        im = P.screen(i)
        nw, nh = int(P.W * sc), int(P.H * sc)
        x0, y0 = (nw - P.W) // 2, int((nh - P.H) * 0.42)
        return im.resize((nw, nh), Image.BILINEAR).crop((x0, y0, x0 + P.W, y0 + P.H))
    return render


# ---------------------------------------------------------------- captions
def word_times(text, t0, dur):
    """Rough per-word start times, spread over the line by character count."""
    words = text.split()
    weights = [len(w) + 2 for w in words]
    total = sum(weights)
    out, acc = [], 0
    for w, k in zip(words, weights):
        out.append((w, t0 + dur * acc / total))
        acc += k
    return out


def chunks(words, size=3):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == size or w[0][-1] in ".!?,:":
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def captions(img, t, name, text, y=1480, size=88):
    """TikTok-style captions: 1-3 words at a time, active word highlighted."""
    s = seg(name)
    t0 = s["start"] + P.VO_LEAD
    dur = P.vo_len(s["vo"])
    groups = chunks(word_times(text, t0, dur))
    cur = None
    for gi, g in enumerate(groups):
        start = g[0][1]
        end = groups[gi + 1][0][1] if gi + 1 < len(groups) else t0 + dur + 0.4
        if start <= t < end:
            cur = g
            break
    if not cur:
        return
    pop = P.ease_out_back(P.prog(t, cur[0][1], cur[0][1] + 0.15), 2.5)
    active = max(k for k, (_w, ws) in enumerate(cur) if ws <= t or k == 0)
    sprites = []
    for k, (w, _ws) in enumerate(cur):
        col = HILITE if k == active else (255, 255, 255)
        sprites.append(P.text_sprite(w.upper(), P.FONT_BLACK, size, col + (255,), 11, (0, 0, 0)))
    gap = -8
    total = sum(sp.width for sp in sprites) + gap * (len(sprites) - 1)
    scale = min(1.0, (P.W - 80) / total) * pop
    x = P.W / 2 - total * scale / 2
    for sp in sprites:
        P.paste_center(img, sp, x + sp.width * scale / 2, y, scale)
        x += (sp.width + gap) * scale


# ---------------------------------------------------------------- stickers
@lru_cache(None)
def number_badge(label, r=125):
    s = r * 2 * P.SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = []
    for k in range(32):
        a = k * math.pi / 16
        rr = s / 2 * (1.0 if k % 2 == 0 else 0.88)
        pts.append((s / 2 + rr * math.cos(a), s / 2 + rr * math.sin(a)))
    d.polygon(pts, fill=P.NAVY + (255,))
    pts2 = [(s / 2 + (x - s / 2) * 0.9, s / 2 + (y - s / 2) * 0.9) for x, y in pts]
    d.polygon(pts2, fill=P.PILL + (255,))
    img = img.resize((r * 2, r * 2), Image.LANCZOS)
    spr = P.text_sprite(label, P.FONT_BLACK, int(r * 0.95), P.NAVY + (255,))
    img.alpha_composite(spr, ((img.width - spr.width) // 2, (img.height - spr.height) // 2 + 4))
    return img


def flash(img, t, t0, length=0.18, strength=200):
    p = (t - t0) / length
    if 0 <= p < 1:
        img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(strength * (1 - p)))))


def burst(img, t, t0, cx, cy, n=30, seed=0, power=1.2):
    P.burst(img, t, t0, cx, cy, n=n, seed=seed, power=power)
