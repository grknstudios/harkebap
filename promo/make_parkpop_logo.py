#!/usr/bin/env python3
"""Draw a Park Pop wordmark (assets/parkpop/logo.png) in the game's UI style.

Font: Lilita One (SIL OFL, assets/fonts). Stand-in until an official logo exists.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "assets", "fonts", "LilitaOne-Regular.woff")
OUT = os.path.join(HERE, "assets", "parkpop", "logo.png")

BROWN = (92, 42, 18)
TOP, BOTTOM = (255, 232, 80), (255, 150, 20)


def word(text, size, stroke):
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    w, h = r - l + 40, b - t + 40
    ox, oy = 20 - l, 20 - t
    # outline + drop shadow
    base = Image.new("RGBA", (w, h + 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.text((ox, oy + 16), text, font=f, fill=BROWN, stroke_width=stroke, stroke_fill=BROWN)
    d.text((ox, oy), text, font=f, fill=BROWN, stroke_width=stroke, stroke_fill=BROWN)
    # gradient fill
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).text((ox, oy), text, font=f, fill=255)
    ys = np.linspace(0, 1, base.height)[:, None, None]
    grad = (np.array(TOP) * (1 - ys) + np.array(BOTTOM) * ys).astype(np.uint8)
    grad = np.repeat(grad, base.width, axis=1)
    fill = Image.fromarray(grad, "RGB").convert("RGBA")
    fill.putalpha(mask)
    base.alpha_composite(fill)
    # glossy highlight on the upper part of the letters
    hl = Image.new("L", base.size, 0)
    ImageDraw.Draw(hl).text((ox, oy - size * 0.06), text, font=f, fill=110)
    hl = Image.fromarray(np.minimum(np.asarray(hl), np.asarray(mask)))
    hl = Image.fromarray((np.asarray(hl) * (np.linspace(1, 0, base.height)[:, None] ** 2.5))
                         .astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    white = Image.new("RGBA", base.size, (255, 255, 255, 0))
    white.putalpha(hl)
    base.alpha_composite(white)
    return base


def parking_sign(size):
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=s // 5, fill=BROWN)
    d.rounded_rectangle([s * 0.05, s * 0.05, s * 0.95, s * 0.95], radius=s // 6, fill=(255, 255, 255))
    d.rounded_rectangle([s * 0.11, s * 0.11, s * 0.89, s * 0.89], radius=s // 8, fill=(36, 110, 235))
    f = ImageFont.truetype(FONT, int(s * 0.72))
    l, t, r, b = f.getbbox("P")
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), "P", font=f, fill=(255, 255, 255))
    return img.resize((size, size), Image.LANCZOS)


def main():
    park, pop = word("Park", 230, 18), word("Pop", 230, 18)
    w = max(park.width, pop.width) + 60
    h = park.height + pop.height - 70
    img = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0))
    img.alpha_composite(pop, ((w - pop.width) // 2 + 30, park.height - 60))
    img.alpha_composite(park, ((w - park.width) // 2, 0))
    sign = parking_sign(150).rotate(12, resample=Image.BICUBIC, expand=True)
    canvas = Image.new("RGBA", (img.width + 60, img.height + 40), (0, 0, 0, 0))
    canvas.alpha_composite(img, (60, 40))
    canvas.alpha_composite(sign, (0, img.height - sign.height + 10))
    canvas = canvas.crop(canvas.getchannel("A").getbbox())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.save(OUT)
    print(OUT, canvas.size)


if __name__ == "__main__":
    main()
