"""Symbols for xiv1ui's action icons: small drawings placed in a box (centre cx, cy and radius r, in 0..1 icon units)
on one of an icon's two masks. tools/icon_families.py combines them with frames (a Bar- shield, an Indi- ring, a
song's note ...) into the icons for whole families of spells and abilities.

Each symbol is sym(d, cx, cy, r) where d is an ImageDraw on a mask (255 draws, 0 cuts).
"""
import math
import os

from PIL import ImageFont

import make_art as A

S = 44
W = S * A.SS
FONT = os.path.join(os.path.dirname(__file__), '..', 'addons', 'xiv1ui', 'fonts', 'XIV1UI-SerifBold.ttf')


def P(pts):
    return [(x * W, y * W) for x, y in pts]


def L(w):
    return max(1, int(w * W))


def at(cx, cy, r, pts):
    """Points given in a unit box (-1..1) placed at cx, cy with radius r."""
    return P([(cx + x * r, cy + y * r) for x, y in pts])


def ell(d, cx, cy, rx, ry, **kw):
    d.ellipse(P([(cx - rx, cy - ry), (cx + rx, cy + ry)]), **kw)


# ---- elements -----------------------------------------------------------------------------------------------------
def fire(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.35, -0.45), (0.25, -0.15), (0.6, -0.4), (0.75, 0.25), (0.45, 0.85),
                             (-0.45, 0.85), (-0.75, 0.25), (-0.5, -0.25), (-0.25, 0.05), (-0.2, -0.55)]), fill=255)
    d.polygon(at(cx, cy, r, [(0, -0.05), (0.3, 0.4), (0.2, 0.8), (-0.2, 0.8), (-0.3, 0.4)]), fill=0)


def ice(d, cx, cy, r):
    for k in range(3):
        t = math.radians(90 + k * 60)
        ux, uy = math.cos(t), math.sin(t)
        d.line(at(cx, cy, r, [(-ux, -uy), (ux, uy)]), fill=255, width=L(r * 0.22))
        for s in (-1, 1):
            bx, by = ux * 0.55 * s, uy * 0.55 * s
            for side in (-1, 1):
                t2 = t + side * math.radians(40)
                d.line(at(cx, cy, r, [(bx, by), (bx + math.cos(t2) * 0.35 * s, by + math.sin(t2) * 0.35 * s)]),
                       fill=255, width=L(r * 0.16))


def wind(d, cx, cy, r):
    w = L(r * 0.20)
    d.arc(at(cx, cy, r, [(-0.9, -0.9), (0.9, 0.9)]), 200, 470, fill=255, width=w)
    d.arc(at(cx, cy, r, [(-0.5, -0.5), (0.5, 0.5)]), 230, 470, fill=255, width=w)
    d.line(at(cx, cy, r, [(-1.0, 0.9), (0.2, 0.9)]), fill=255, width=w)


def earth(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.85, 0.75), (-0.55, -0.2), (-0.1, -0.85), (0.6, -0.55), (0.9, 0.5), (0.3, 0.85)]),
              fill=255)
    d.line(at(cx, cy, r, [(-0.1, -0.85), (0.05, 0.1), (0.9, 0.5)]), fill=0, width=L(r * 0.10))


def thunder(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0.15, -1), (-0.6, 0.15), (-0.05, 0.15), (-0.3, 1), (0.6, -0.25), (0.05, -0.25)]),
              fill=255)


def water(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.62, 0.15), (-0.62, 0.15)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.66, -0.25), (0.66, 0.95)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.35, 0.15), (-0.1, 0.5)]), fill=0)


def light(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.22, -0.22), (1, 0), (0.22, 0.22), (0, 1), (-0.22, 0.22), (-1, 0),
                             (-0.22, -0.22)]), fill=255)


def dark(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.9, -0.9), (0.9, 0.9)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.45, -1.05), (1.15, 0.6)]), fill=0)


ELEMENTS = {'fire': fire, 'ice': ice, 'wind': wind, 'earth': earth, 'thunder': thunder, 'water': water,
            'light': light, 'dark': dark}
# the accent colour of each element (keys of make_action_icons.ACCENTS)
ELEMENT_ACCENT = {'fire': 'fire', 'ice': 'blue', 'wind': 'wind', 'earth': 'earth', 'thunder': 'violet',
                  'water': 'blue', 'light': 'holy', 'dark': 'dark'}


# ---- statuses -----------------------------------------------------------------------------------------------------
def haste(d, cx, cy, r):
    for k in (-0.55, 0.15):
        d.polygon(at(cx, cy, r, [(k - 0.25, -0.8), (k + 0.35, 0), (k - 0.25, 0.8), (k - 0.05, 0), ]), fill=255)
    d.line(at(cx, cy, r, [(-1, -0.4), (-0.7, -0.4)]), fill=255, width=L(r * 0.12))
    d.line(at(cx, cy, r, [(-1, 0.4), (-0.7, 0.4)]), fill=255, width=L(r * 0.12))


def slow(d, cx, cy, r):
    # an hourglass
    d.polygon(at(cx, cy, r, [(-0.6, -0.9), (0.6, -0.9), (0.08, 0), (0.6, 0.9), (-0.6, 0.9), (-0.08, 0)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.38, -0.75), (0.38, -0.75), (0, -0.2)]), fill=0)
    d.line(at(cx, cy, r, [(-0.75, -0.95), (0.75, -0.95)]), fill=255, width=L(r * 0.14))
    d.line(at(cx, cy, r, [(-0.75, 0.95), (0.75, 0.95)]), fill=255, width=L(r * 0.14))


def paralyze(d, cx, cy, r):
    thunder(d, cx, cy - r * 0.15, r * 0.8)
    d.arc(at(cx, cy, r, [(-1, 0.45), (1, 1.05)]), 0, 360, fill=255, width=L(r * 0.12))


def silence(d, cx, cy, r):
    # a speech bubble with an X in it
    d.rounded_rectangle(at(cx, cy, r, [(-0.95, -0.8), (0.95, 0.45)]), radius=L(r * 0.3), fill=255)
    d.polygon(at(cx, cy, r, [(-0.55, 0.3), (-0.7, 0.95), (-0.1, 0.4)]), fill=255)
    for a, b in (((-0.35, -0.5), (0.35, 0.15)), ((0.35, -0.5), (-0.35, 0.15))):
        d.line(at(cx, cy, r, [a, b]), fill=0, width=L(r * 0.17))


def sleep(d, cx, cy, r):
    for x, y, s in ((-0.45, 0.45, 0.55), (0.25, -0.05, 0.42), (0.7, -0.55, 0.3)):
        d.line(at(cx, cy, r, [(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x - s / 2, y + s / 2),
                              (x + s / 2, y + s / 2)]), fill=255, width=L(r * 0.15))


def bind(d, cx, cy, r):
    for k, (x, y) in enumerate(((-0.5, -0.5), (0, 0), (0.5, 0.5))):
        d.ellipse(at(cx, cy, r, [(x - 0.42, y - 0.28), (x + 0.42, y + 0.28)]), outline=255, width=L(r * 0.15))


def gravity(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.55, -0.15), (0.55, -0.15), (0.75, 0.85), (-0.75, 0.85)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.25, -0.55), (0.25, -0.1)]), outline=255, width=L(r * 0.13))
    d.polygon(at(cx, cy, r, [(-0.2, 0.15), (0.2, 0.15), (0, 0.55)]), fill=0)


def blind(d, cx, cy, r):
    d.chord(at(cx, cy, r, [(-1, -0.55), (1, 0.75)]), 200, 340, fill=255)
    d.chord(at(cx, cy, r, [(-1, -0.75), (1, 0.55)]), 20, 160, fill=255)
    d.ellipse(at(cx, cy, r, [(-0.32, -0.32), (0.32, 0.32)]), fill=0)
    d.line(at(cx, cy, r, [(-0.85, 0.85), (0.85, -0.85)]), fill=0, width=L(r * 0.30))
    d.line(at(cx, cy, r, [(-0.85, 0.85), (0.85, -0.85)]), fill=255, width=L(r * 0.12))


def poison(d, cx, cy, r):
    water(d, cx, cy, r)
    d.ellipse(at(cx, cy, r, [(-0.32, 0.05), (0.32, 0.55)]), fill=0)
    d.ellipse(at(cx, cy, r, [(-0.18, 0.18), (0.18, 0.45)]), fill=255)


def petrify(d, cx, cy, r):
    # a stone figure, cracked
    d.ellipse(at(cx, cy, r, [(-0.3, -1), (0.3, -0.45)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.6, -0.35), (0.6, -0.35), (0.45, 1), (-0.45, 1)]), fill=255)
    d.line(at(cx, cy, r, [(-0.1, -0.35), (0.15, 0.1), (-0.15, 0.5), (0.1, 1)]), fill=0, width=L(r * 0.11))


def virus(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.55, -0.55), (0.55, 0.55)]), fill=255)
    for k in range(8):
        t = k * math.pi / 4
        d.line(at(cx, cy, r, [(0.5 * math.cos(t), 0.5 * math.sin(t)), (0.9 * math.cos(t), 0.9 * math.sin(t))]),
               fill=255, width=L(r * 0.13))
        d.ellipse(at(cx, cy, r, [(0.9 * math.cos(t) - 0.12, 0.9 * math.sin(t) - 0.12),
                                 (0.9 * math.cos(t) + 0.12, 0.9 * math.sin(t) + 0.12)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.22, -0.22), (0.22, 0.22)]), fill=0)


def curse(d, cx, cy, r):
    # a wisp / ghost
    d.pieslice(at(cx, cy, r, [(-0.7, -1), (0.7, 0.4)]), 180, 360, fill=255)
    d.polygon(at(cx, cy, r, [(-0.7, -0.3), (0.7, -0.3), (0.7, 0.9), (0.35, 0.6), (0, 0.95), (-0.35, 0.6),
                             (-0.7, 0.9)]), fill=255)
    for x in (-0.3, 0.3):
        d.ellipse(at(cx, cy, r, [(x - 0.13, -0.5), (x + 0.13, -0.2)]), fill=0)


def amnesia(d, cx, cy, r):
    d.arc(at(cx, cy, r, [(-0.6, -1), (0.6, 0.15)]), 180, 70, fill=255, width=L(r * 0.25))
    d.line(at(cx, cy, r, [(0.15, 0.0), (0.0, 0.25), (0.0, 0.45)]), fill=255, width=L(r * 0.25))
    d.ellipse(at(cx, cy, r, [(-0.17, 0.65), (0.17, 0.98)]), fill=255)


def stun(d, cx, cy, r):
    for k in range(5):
        t = -math.pi / 2 + k * 2 * math.pi / 5
        x, y = 0.62 * math.cos(t), 0.62 * math.sin(t)
        light(d, cx + x * r, cy + y * r, r * 0.38)


def regen(d, cx, cy, r):
    d.rectangle(at(cx, cy, r, [(-0.16, -0.55), (0.16, 0.55)]), fill=255)
    d.rectangle(at(cx, cy, r, [(-0.55, -0.16), (0.55, 0.16)]), fill=255)
    d.arc(at(cx, cy, r, [(-1, -1), (1, 1)]), 200, 500, fill=255, width=L(r * 0.12))
    d.polygon(at(cx, cy, r, [(0.55, 0.62), (1.05, 0.55), (0.75, 1.0)]), fill=255)


def refresh(d, cx, cy, r):
    water(d, cx, cy, r * 0.62)
    d.arc(at(cx, cy, r, [(-1, -1), (1, 1)]), 200, 500, fill=255, width=L(r * 0.12))
    d.polygon(at(cx, cy, r, [(0.55, 0.62), (1.05, 0.55), (0.75, 1.0)]), fill=255)


def shield(d, cx, cy, r, hollow=True):
    pts = [(-0.8, -0.85), (0.8, -0.85), (0.8, 0.0), (0, 0.95), (-0.8, 0.0)]
    d.polygon(at(cx, cy, r, pts), fill=255)
    if hollow:
        d.polygon(at(cx, cy, r * 0.62, pts), fill=0)


def shell(d, cx, cy, r):
    pts = [(math.cos(math.radians(30 + k * 60)), math.sin(math.radians(30 + k * 60))) for k in range(6)]
    d.polygon(at(cx, cy, r, [(x * 0.95, y * 0.95) for x, y in pts]), fill=255)
    d.polygon(at(cx, cy, r, [(x * 0.62, y * 0.62) for x, y in pts]), fill=0)
    d.polygon(at(cx, cy, r, [(x * 0.32, y * 0.32) for x, y in pts]), fill=255)


def sword(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.16, -0.75), (0.16, 0.35), (-0.16, 0.35), (-0.16, -0.75)]), fill=255)
    d.rectangle(at(cx, cy, r, [(-0.5, 0.35), (0.5, 0.5)]), fill=255)
    d.rectangle(at(cx, cy, r, [(-0.1, 0.5), (0.1, 0.95)]), fill=255)


def target(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.85, -0.85), (0.85, 0.85)]), outline=255, width=L(r * 0.14))
    d.ellipse(at(cx, cy, r, [(-0.25, -0.25), (0.25, 0.25)]), fill=255)
    for x, y in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        d.line(at(cx, cy, r, [(x * 0.55, y * 0.55), (x * 1.05, y * 1.05)]), fill=255, width=L(r * 0.13))


def evasion(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.05, -1), (0.45, -0.5)]), fill=255)
    d.polygon(at(cx, cy, r, [(0.0, -0.4), (0.45, -0.4), (0.55, 0.3), (0.85, 0.95), (0.45, 0.95), (0.2, 0.4),
                             (-0.2, 0.95), (-0.55, 0.95), (-0.1, 0.25)]), fill=255)
    for y in (-0.3, 0.1, 0.5):
        d.line(at(cx, cy, r, [(-1, y), (-0.45, y)]), fill=255, width=L(r * 0.10))


def orb(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.6, -0.6), (0.6, 0.6)]), fill=255)
    for k in range(8):
        t = k * math.pi / 4 + math.pi / 8
        d.line(at(cx, cy, r, [(0.75 * math.cos(t), 0.75 * math.sin(t)), (1.0 * math.cos(t), 1.0 * math.sin(t))]),
               fill=255, width=L(r * 0.12))


def drain(d, cx, cy, r):
    # a heart with a fang biting into it
    d.ellipse(at(cx, cy, r, [(-0.9, -0.75), (0.05, 0.15)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.05, -0.75), (0.9, 0.15)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.85, -0.15), (0.85, -0.15), (0, 0.95)]), fill=255)
    d.polygon(at(cx, cy, r, [(0.2, -0.9), (0.55, -0.9), (0.38, -0.2)]), fill=0)


def aspir(d, cx, cy, r):
    water(d, cx, cy, r)
    d.polygon(at(cx, cy, r, [(0.15, -0.95), (0.6, -0.95), (0.38, -0.15)]), fill=0)


def tp(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.9, -0.9), (0.9, 0.9)]), outline=255, width=L(r * 0.16))
    d.pieslice(at(cx, cy, r, [(-0.6, -0.6), (0.6, 0.6)]), -90, 150, fill=255)


def dispel(d, cx, cy, r):
    d.arc(at(cx, cy, r, [(-0.9, -0.9), (0.9, 0.9)]), 20, 160, fill=255, width=L(r * 0.18))
    d.arc(at(cx, cy, r, [(-0.9, -0.9), (0.9, 0.9)]), 200, 340, fill=255, width=L(r * 0.18))
    light(d, cx, cy, r * 0.45)


def blink(d, cx, cy, r):
    for k, x in enumerate((0.3, -0.3)):
        d.ellipse(at(cx, cy, r, [(x - 0.28, -0.95), (x + 0.28, -0.4)]), fill=255 if k == 0 else 0,
                  outline=255, width=L(r * 0.1))
        d.pieslice(at(cx, cy, r, [(x - 0.6, -0.35), (x + 0.6, 1.4)]), 180, 360, fill=255 if k == 0 else 0,
                   outline=255, width=L(r * 0.1))


def stoneskin(d, cx, cy, r):
    for x, y in ((-0.45, -0.45), (0.45, -0.45), (-0.45, 0.45), (0.45, 0.45)):
        d.rounded_rectangle(at(cx, cy, r, [(x - 0.4, y - 0.4), (x + 0.4, y + 0.4)]), radius=L(r * 0.08), fill=255)


def sparkles(d, cx, cy, r):
    light(d, cx - r * 0.25, cy + r * 0.2, r * 0.7)
    light(d, cx + r * 0.6, cy - r * 0.55, r * 0.4)


def heart(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.9, -0.8), (0.05, 0.1)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.05, -0.8), (0.9, 0.1)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.85, -0.2), (0.85, -0.2), (0, 0.9)]), fill=255)


def arrow_up(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.75, -0.15), (0.3, -0.15), (0.3, 0.95), (-0.3, 0.95), (-0.3, -0.15),
                             (-0.75, -0.15)]), fill=255)


def arrow_down(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, 1), (0.75, 0.15), (0.3, 0.15), (0.3, -0.95), (-0.3, -0.95), (-0.3, 0.15),
                             (-0.75, 0.15)]), fill=255)


def crystal(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.45, -0.35), (0.3, 0.95), (-0.3, 0.95), (-0.45, -0.35)]), fill=255)
    d.line(at(cx, cy, r, [(0, -1), (0, 0.95)]), fill=0, width=L(r * 0.07))


def portal(d, cx, cy, r):
    for k, rr in enumerate((1.0, 0.68, 0.36)):
        d.arc(at(cx, cy, r, [(-rr, -rr * 0.7), (rr, rr * 0.7)]), 30 + k * 40, 330 + k * 40, fill=255,
              width=L(r * 0.13))


def wings(d, cx, cy, r):
    for side in (-1, 1):
        for k in range(3):
            x0 = side * (0.2 + k * 0.25)
            d.polygon(at(cx, cy, r, [(side * 0.15, 0.2), (x0 + side * 0.35, -0.7 + k * 0.25),
                                     (x0 + side * 0.42, -0.4 + k * 0.25), (side * 0.2, 0.5)]), fill=255)


def figure(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.3, -1), (0.3, -0.4)]), fill=255)
    d.pieslice(at(cx, cy, r, [(-0.75, -0.3), (0.75, 1.9)]), 180, 360, fill=255)


def footprints(d, cx, cy, r):
    for x, y in ((-0.4, 0.45), (0.35, -0.35)):
        d.ellipse(at(cx, cy, r, [(x - 0.25, y - 0.45), (x + 0.25, y + 0.3)]), fill=255)
        d.ellipse(at(cx, cy, r, [(x - 0.18, y + 0.38), (x + 0.18, y + 0.62)]), fill=255)


def flower(d, cx, cy, r):
    for k in range(5):
        t = -math.pi / 2 + k * 2 * math.pi / 5
        ell(d, cx + 0.5 * r * math.cos(t), cy + 0.5 * r * math.sin(t), 0.33 * r, 0.33 * r, fill=255)
    ell(d, cx, cy, 0.25 * r, 0.25 * r, fill=0)


def scales(d, cx, cy, r):
    d.line(at(cx, cy, r, [(0, -0.9), (0, 0.85)]), fill=255, width=L(r * 0.12))
    d.line(at(cx, cy, r, [(-0.9, -0.55), (0.9, -0.55)]), fill=255, width=L(r * 0.12))
    for x in (-0.65, 0.65):
        d.chord(at(cx, cy, r, [(x - 0.35, -0.35), (x + 0.35, 0.3)]), 0, 180, fill=255)
    d.rectangle(at(cx, cy, r, [(-0.45, 0.8), (0.45, 0.95)]), fill=255)


def eye(d, cx, cy, r):
    d.chord(at(cx, cy, r, [(-1, -0.55), (1, 0.75)]), 200, 340, fill=255)
    d.chord(at(cx, cy, r, [(-1, -0.75), (1, 0.55)]), 20, 160, fill=255)
    d.ellipse(at(cx, cy, r, [(-0.35, -0.35), (0.35, 0.35)]), fill=0)
    d.ellipse(at(cx, cy, r, [(-0.15, -0.15), (0.15, 0.15)]), fill=255)


def burst(d, cx, cy, r):
    pts = []
    for k in range(16):
        t = k * math.pi / 8
        rr = 1.0 if k % 2 == 0 else 0.5
        pts.append((rr * math.cos(t), rr * math.sin(t)))
    d.polygon(at(cx, cy, r, pts), fill=255)


def ring(d, cx, cy, r, w=0.14):
    d.ellipse(at(cx, cy, r, [(-1, -1), (1, 1)]), outline=255, width=L(r * w))


def text(d, cx, cy, r, s):
    """Letters (a stat's abbreviation ...) fitted into the box."""
    size = int(W * r * 0.95)
    while True:
        f = ImageFont.truetype(FONT, size)
        x0, y0, x1, y1 = d.textbbox((0, 0), s, font=f)
        if x1 - x0 <= W * r * 2 * 0.95 or size < 8:
            break
        size -= 2
    d.text((cx * W - (x0 + x1) / 2, cy * W - (y0 + y1) / 2), s, font=f, fill=255)


def stat(name):
    return lambda d, cx, cy, r: text(d, cx, cy, r, name)


STATUSES = {
    'haste': haste, 'slow': slow, 'paralyze': paralyze, 'silence': silence, 'sleep': sleep, 'bind': bind,
    'gravity': gravity, 'blind': blind, 'poison': poison, 'petrify': petrify, 'virus': virus, 'curse': curse,
    'amnesia': amnesia, 'stun': stun, 'regen': regen, 'refresh': refresh, 'shield': shield, 'shell': shell,
    'sword': sword, 'target': target, 'evasion': evasion, 'orb': orb, 'drain': drain, 'aspir': aspir, 'tp': tp,
    'dispel': dispel, 'blink': blink, 'stoneskin': stoneskin, 'sparkles': sparkles, 'heart': heart,
    'up': arrow_up, 'down': arrow_down, 'crystal': crystal, 'portal': portal, 'wings': wings, 'figure': figure,
    'footprints': footprints, 'flower': flower, 'scales': scales, 'eye': eye, 'burst': burst,
}
STATUSES.update(ELEMENTS)
for _s in ('STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR', 'ACC', 'TP', 'HP', 'MP'):
    STATUSES[_s] = stat(_s)


# ---- weapons (drawn on a diagonal, hilt at the lower left) -----------------------------------------------------
def _diag(d, cx, cy, r, w, a0=-0.85, a1=0.85):
    d.line(at(cx, cy, r, [(a0, -a0), (a1, -a1)]), fill=255, width=L(r * w))


def w_fist(d, cx, cy, r):
    d.rounded_rectangle(at(cx, cy, r, [(-0.6, -0.55), (0.6, 0.25)]), radius=L(r * 0.15), fill=255)
    for k in range(3):
        x = -0.3 + k * 0.3
        d.line(at(cx, cy, r, [(x, -0.55), (x, -0.25)]), fill=0, width=L(r * 0.06))
    d.rectangle(at(cx, cy, r, [(-0.4, 0.2), (0.45, 0.85)]), fill=255)
    d.rounded_rectangle(at(cx, cy, r, [(-0.85, -0.3), (-0.45, 0.15)]), radius=L(r * 0.1), fill=255)


def _blade(d, cx, cy, r, length, width, guard=0.45):
    # tip at upper right, hilt at lower left
    tip, base = (0.85 * length, -0.85 * length), (-0.35, 0.35)
    px, py = 0.707, 0.707
    d.polygon(at(cx, cy, r, [tip, (base[0] + px * width, base[1] + py * width),
                             (base[0] - px * width, base[1] - py * width)]), fill=255)
    d.line(at(cx, cy, r, [(base[0] + px * guard, base[1] + py * guard), (base[0] - px * guard, base[1] - py * guard)]),
           fill=255, width=L(r * 0.14))
    d.line(at(cx, cy, r, [base, (-0.85, 0.85)]), fill=255, width=L(r * 0.13))


def w_dagger(d, cx, cy, r):
    _blade(d, cx, cy, r, 0.7, 0.12, 0.35)


def w_sword(d, cx, cy, r):
    _blade(d, cx, cy, r, 1.0, 0.14)


def w_greatsword(d, cx, cy, r):
    _blade(d, cx, cy, r, 1.1, 0.28, 0.55)


def w_axe(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.13)
    d.polygon(at(cx, cy, r, [(0.25, -0.55), (0.9, -0.95), (1.0, -0.2), (0.55, -0.1)]), fill=255)


def w_greataxe(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.14)
    d.polygon(at(cx, cy, r, [(0.15, -0.45), (0.75, -1.0), (1.0, -0.1), (0.5, 0.05)]), fill=255)
    d.polygon(at(cx, cy, r, [(0.45, -0.75), (0.05, -1.0), (-0.1, -0.55), (0.25, -0.5)]), fill=255)


def w_scythe(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.12)
    d.chord(at(cx, cy, r, [(-0.6, -1.2), (1.0, -0.2)]), 180, 330, fill=255)
    d.chord(at(cx, cy, r, [(-0.45, -1.0), (1.0, -0.05)]), 180, 330, fill=0)


def w_polearm(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.1, -0.95, 0.6)
    d.polygon(at(cx, cy, r, [(0.95, -0.95), (0.45, -0.75), (0.75, -0.45)]), fill=255)


def _katana(d, cx, cy, r, length, width):
    # a slim single-edged blade, a round guard, a long grip
    tip, base = (0.9 * length, -0.9 * length), (-0.3, 0.3)
    d.polygon(at(cx, cy, r, [tip, (base[0] + 0.707 * width, base[1] + 0.707 * width),
                             (base[0] - 0.707 * width * 0.4, base[1] - 0.707 * width * 0.4)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.48, 0.12), (-0.12, 0.48)]), fill=255)
    d.line(at(cx, cy, r, [(-0.3, 0.3), (-0.95, 0.95)]), fill=255, width=L(r * 0.12))


def w_katana(d, cx, cy, r):
    _katana(d, cx, cy, r, 1.0, 0.13)


def w_greatkatana(d, cx, cy, r):
    _katana(d, cx, cy, r, 1.12, 0.2)


def w_club(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.14, -0.85, 0.3)
    d.ellipse(at(cx, cy, r, [(0.1, -0.95), (0.9, -0.15)]), fill=255)


def w_staff(d, cx, cy, r):
    _diag(d, cx, cy, r, 0.1, -0.95, 0.65)
    d.ellipse(at(cx, cy, r, [(0.45, -1.0), (1.0, -0.45)]), outline=255, width=L(r * 0.12))


def w_bow(d, cx, cy, r):
    d.arc(at(cx, cy, r, [(-1.2, -1.0), (0.6, 1.0)]), 270, 90, fill=255, width=L(r * 0.13))
    d.line(at(cx, cy, r, [(-0.3, -1.0), (-0.3, 1.0)]), fill=255, width=L(r * 0.05))
    d.line(at(cx, cy, r, [(-0.6, 0), (1.0, 0)]), fill=255, width=L(r * 0.08))
    d.polygon(at(cx, cy, r, [(1.05, 0), (0.75, -0.18), (0.75, 0.18)]), fill=255)


def w_gun(d, cx, cy, r):
    d.rectangle(at(cx, cy, r, [(-0.9, -0.3), (0.9, -0.05)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.85, -0.05), (-0.35, -0.05), (-0.45, 0.75), (-0.9, 0.7)]), fill=255)
    d.rectangle(at(cx, cy, r, [(0.5, -0.45), (0.65, -0.3)]), fill=255)


WEAPONS = {'h2h': w_fist, 'dagger': w_dagger, 'sword': w_sword, 'greatsword': w_greatsword, 'axe': w_axe,
           'greataxe': w_greataxe, 'scythe': w_scythe, 'polearm': w_polearm, 'katana': w_katana,
           'greatkatana': w_greatkatana, 'club': w_club, 'staff': w_staff, 'bow': w_bow, 'gun': w_gun}


# ---- job things -----------------------------------------------------------------------------------------------------
def die(d, cx, cy, r):
    d.rounded_rectangle(at(cx, cy, r, [(-0.8, -0.8), (0.8, 0.8)]), radius=L(r * 0.25), fill=255)
    for x, y in ((-0.4, -0.4), (0.4, -0.4), (0, 0), (-0.4, 0.4), (0.4, 0.4)):
        d.ellipse(at(cx, cy, r, [(x - 0.13, y - 0.13), (x + 0.13, y + 0.13)]), fill=0)


def card(d, cx, cy, r):
    d.rounded_rectangle(at(cx, cy, r, [(-0.6, -0.9), (0.6, 0.9)]), radius=L(r * 0.15), fill=255)
    d.polygon(at(cx, cy, r, [(0, -0.5), (0.3, 0), (0, 0.5), (-0.3, 0)]), fill=0)


def gear(d, cx, cy, r):
    for k in range(8):
        t = k * math.pi / 4
        d.polygon(at(cx, cy, r, [(0.95 * math.cos(t - 0.2), 0.95 * math.sin(t - 0.2)),
                                 (0.95 * math.cos(t + 0.2), 0.95 * math.sin(t + 0.2)),
                                 (0.6 * math.cos(t + 0.3), 0.6 * math.sin(t + 0.3)),
                                 (0.6 * math.cos(t - 0.3), 0.6 * math.sin(t - 0.3))]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.72, -0.72), (0.72, 0.72)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.3, -0.3), (0.3, 0.3)]), fill=0)


def book(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.95, -0.7), (-0.05, -0.55), (-0.05, 0.85), (-0.95, 0.7)]), fill=255)
    d.polygon(at(cx, cy, r, [(0.95, -0.7), (0.05, -0.55), (0.05, 0.85), (0.95, 0.7)]), fill=255)


def fan(d, cx, cy, r):
    d.pieslice(at(cx, cy, r, [(-1, -0.7), (1, 1.3)]), 200, 340, fill=255)
    d.pieslice(at(cx, cy, r, [(-0.35, -0.05), (0.35, 0.65)]), 200, 340, fill=0)
    for k in range(5):
        t = math.radians(205 + k * 32.5)
        d.line(at(cx, cy, r, [(0, 0.3), (0.95 * math.cos(t), 0.3 + 0.95 * math.sin(t))]), fill=0, width=L(r * 0.05))
    d.line(at(cx, cy, r, [(0, 0.3), (0, 0.95)]), fill=255, width=L(r * 0.12))


def rune(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(0, -1), (0.7, 0), (0, 1), (-0.7, 0)]), fill=255)
    d.line(at(cx, cy, r, [(0, -0.6), (0, 0.6)]), fill=0, width=L(r * 0.12))
    d.line(at(cx, cy, r, [(0, -0.1), (0.3, -0.4)]), fill=0, width=L(r * 0.12))


def wyvern(d, cx, cy, r):
    # a small dragon's head in profile, facing right
    d.polygon(at(cx, cy, r, [(-0.8, 0.9), (-0.6, -0.1), (-0.2, -0.6), (0.4, -0.55), (0.95, -0.2), (0.95, 0.05),
                             (0.3, 0.1), (0.0, 0.4), (-0.2, 0.9)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.3, -0.55), (-0.55, -1.0), (-0.05, -0.6)]), fill=255)
    d.ellipse(at(cx, cy, r, [(0.15, -0.4), (0.3, -0.25)]), fill=0)


def jump(d, cx, cy, r):
    d.arc(at(cx, cy, r, [(-0.9, -0.9), (0.9, 1.5)]), 200, 340, fill=255, width=L(r * 0.16))
    d.polygon(at(cx, cy, r, [(0.95, 0.35), (0.55, 0.15), (0.95, -0.05)]), fill=255)
    d.line(at(cx, cy, r, [(-0.9, 0.95), (0.95, 0.95)]), fill=255, width=L(r * 0.1))


def paw(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.5, -0.05), (0.5, 0.85)]), fill=255)
    for x, y in ((-0.75, -0.25), (-0.3, -0.75), (0.3, -0.75), (0.75, -0.25)):
        d.ellipse(at(cx, cy, r, [(x - 0.22, y - 0.25), (x + 0.22, y + 0.25)]), fill=255)


def circle_glyph(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-1, -1), (1, 1)]), outline=255, width=L(r * 0.1))
    pts = [(math.cos(-math.pi / 2 + k * 4 * math.pi / 5), math.sin(-math.pi / 2 + k * 4 * math.pi / 5))
           for k in range(5)]
    d.line(at(cx, cy, r, pts + [pts[0]]), fill=255, width=L(r * 0.08))


STATUSES.update({'die': die, 'card': card, 'gear': gear, 'book': book, 'fan': fan, 'rune': rune, 'wyvern': wyvern,
                 'jump': jump, 'paw': paw, 'circle': circle_glyph, 'fist': w_fist})
STATUSES.update({'w_' + k: v for k, v in WEAPONS.items()})


# ---- monster motifs (Blue Magic) -----------------------------------------------------------------------------------
def claw(d, cx, cy, r):
    for k in (-0.5, 0, 0.5):
        d.polygon(at(cx, cy, r, [(k - 0.35, -0.95), (k - 0.15, -0.95), (k + 0.35, 0.95), (k + 0.15, 0.95)]), fill=255)


def fang(d, cx, cy, r):
    # open jaws: two rows of teeth
    d.chord(at(cx, cy, r, [(-1, -1), (1, 0.2)]), 0, 180, fill=255)
    d.chord(at(cx, cy, r, [(-1, -0.2), (1, 1)]), 180, 360, fill=255)
    for k in range(4):
        x = -0.6 + k * 0.4
        d.polygon(at(cx, cy, r, [(x - 0.14, -0.4), (x + 0.14, -0.4), (x, 0.05)]), fill=0)
        if k < 3:
            d.polygon(at(cx, cy, r, [(x, 0.4), (x + 0.2, -0.05), (x + 0.4, 0.4)]), fill=0)


def breath(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-1, -0.35), (-0.5, 0.35)]), fill=255)
    for k, rr in enumerate((0.55, 0.85, 1.15)):
        d.arc(at(cx, cy, r, [(-1.0 - rr + 0.4, -rr), (-0.6 + rr, rr)]), 320, 40, fill=255, width=L(r * 0.15))


def tail(d, cx, cy, r):
    d.arc(at(cx, cy, r, [(-1, -0.7), (0.6, 0.9)]), 180, 360, fill=255, width=L(r * 0.22))
    d.arc(at(cx, cy, r, [(0.2, -0.3), (1.0, 0.5)]), 0, 180, fill=255, width=L(r * 0.16))
    d.polygon(at(cx, cy, r, [(0.2, 0.1), (0.05, -0.3), (0.4, 0.0)]), fill=255)


def horn(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.8, 0.9), (-0.3, 0.9), (0.2, 0.0), (0.95, -0.95), (-0.1, -0.35)]), fill=255)


def feather(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.45, -1.0), (0.45, 0.6)]), fill=255)
    d.line(at(cx, cy, r, [(0, -0.8), (0, 1.0)]), fill=0, width=L(r * 0.08))
    d.line(at(cx, cy, r, [(0, 0.6), (0, 1.0)]), fill=255, width=L(r * 0.1))
    for y in (-0.4, 0.0, 0.3):
        d.line(at(cx, cy, r, [(0, y), (0.4, y - 0.25)]), fill=0, width=L(r * 0.05))


def spores(d, cx, cy, r):
    for x, y, s in ((-0.45, 0.35, 0.42), (0.35, 0.45, 0.32), (0.1, -0.35, 0.38), (-0.55, -0.55, 0.2),
                    (0.7, -0.6, 0.18)):
        d.ellipse(at(cx, cy, r, [(x - s, y - s), (x + s, y + s)]), fill=255)


def needles(d, cx, cy, r):
    for k in range(7):
        t = math.radians(200 + k * 23)
        d.line(at(cx, cy, r, [(-0.6 + 0.2 * math.cos(t), 0.6), (-0.6 + 1.6 * math.cos(t) * 0.9 + 0.6,
                                                                 0.6 + 1.6 * math.sin(t) * 0.9)]),
               fill=255, width=L(r * 0.08))


def beam(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-1, 0.4), (-0.4, 1.0)]), fill=255)
    d.polygon(at(cx, cy, r, [(-0.85, 0.55), (-0.55, 0.85), (1.0, -0.6), (0.6, -1.0)]), fill=255)


def conch(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.9, -0.8), (0.7, 0.8)]), fill=255)
    for k, rr in enumerate((0.55, 0.32)):
        d.arc(at(cx, cy, r, [(-0.1 - rr, -rr), (-0.1 + rr, rr)]), 0, 300, fill=0, width=L(r * 0.1))
    d.polygon(at(cx, cy, r, [(0.5, 0.4), (1.0, 0.95), (0.2, 0.75)]), fill=255)


def bomb(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.8, -0.5), (0.6, 0.9)]), fill=255)
    d.rectangle(at(cx, cy, r, [(0.15, -0.65), (0.45, -0.35)]), fill=255)
    d.arc(at(cx, cy, r, [(0.3, -1.05), (0.9, -0.45)]), 180, 300, fill=255, width=L(r * 0.08))
    light(d, cx + 0.8 * r, cy - 0.85 * r, r * 0.25)


def roar(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-1, -0.3), (-0.55, -0.3), (-0.2, -0.65), (-0.2, 0.65), (-0.55, 0.3), (-1, 0.3)]),
              fill=255)
    for rr in (0.45, 0.8):
        d.arc(at(cx, cy, r, [(-0.2 - rr, -rr), (-0.2 + rr, rr)]), 300, 60, fill=255, width=L(r * 0.13))


def drill(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.55, -0.9), (0.55, -0.9), (0, 1.0)]), fill=255)
    for y in (-0.5, -0.1, 0.3):
        d.line(at(cx, cy, r, [(-0.6, y - 0.15), (0.6, y + 0.15)]), fill=0, width=L(r * 0.08))


def leaf(d, cx, cy, r):
    pts = []
    for k in range(25):
        t = k / 24
        pts.append((-0.85 + 1.7 * t, 0.85 - 1.7 * t - 0.55 * math.sin(math.pi * t)))
    for k in range(25):
        t = 1 - k / 24
        pts.append((-0.85 + 1.7 * t, 0.85 - 1.7 * t + 0.55 * math.sin(math.pi * t)))
    d.polygon(at(cx, cy, r, pts), fill=255)
    d.line(at(cx, cy, r, [(-0.95, 0.95), (0.6, -0.6)]), fill=0, width=L(r * 0.07))


def bug(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.45, -0.3), (0.45, 0.95)]), fill=255)
    d.ellipse(at(cx, cy, r, [(-0.3, -0.75), (0.3, -0.2)]), fill=255)
    d.line(at(cx, cy, r, [(0, -0.3), (0, 0.95)]), fill=0, width=L(r * 0.06))
    for y in (0.05, 0.35, 0.65):
        d.line(at(cx, cy, r, [(-0.95, y - 0.15), (0.95, y - 0.15)]), fill=255, width=L(r * 0.07))
    for s in (-1, 1):
        d.line(at(cx, cy, r, [(s * 0.15, -0.7), (s * 0.5, -1.0)]), fill=255, width=L(r * 0.06))


def tentacle(d, cx, cy, r):
    for x0 in (-0.6, 0.0, 0.6):
        pts = [(x0 + 0.22 * math.sin(k / 10 * 2.6 * math.pi), -0.95 + 1.9 * k / 10) for k in range(11)]
        d.line(at(cx, cy, r, pts), fill=255, width=L(r * (0.2)), joint='curve')
        d.ellipse(at(cx, cy, r, [(pts[-1][0] - 0.12, 0.85), (pts[-1][0] + 0.12, 1.05)]), fill=255)


def hammer(d, cx, cy, r):
    d.line(at(cx, cy, r, [(-0.85, 0.85), (0.3, -0.3)]), fill=255, width=L(r * 0.14))
    d.polygon(at(cx, cy, r, [(0.0, -0.75), (0.45, -1.0), (1.0, -0.45), (0.75, 0.0)]), fill=255)


def impact(d, cx, cy, r):
    d.line(at(cx, cy, r, [(-1, 0.75), (1, 0.75)]), fill=255, width=L(r * 0.12))
    for k in range(5):
        t = math.radians(200 + k * 35)
        d.line(at(cx, cy, r, [(0.3 * math.cos(t), 0.6 + 0.3 * math.sin(t)),
                              (0.95 * math.cos(t), 0.6 + 0.95 * math.sin(t))]), fill=255, width=L(r * 0.1))
    d.ellipse(at(cx, cy, r, [(-0.3, 0.3), (0.3, 0.75)]), fill=255)


def boot(d, cx, cy, r):
    d.polygon(at(cx, cy, r, [(-0.5, -0.95), (0.1, -0.95), (0.1, 0.3), (0.95, 0.45), (0.95, 0.9), (-0.5, 0.9)]),
              fill=255)


def scissors(d, cx, cy, r):
    for s in (-1, 1):
        d.line(at(cx, cy, r, [(s * -0.7, 0.8), (s * 0.7, -0.95)]), fill=255, width=L(r * 0.13))
        d.ellipse(at(cx, cy, r, [(s * -0.7 - 0.25, 0.55), (s * -0.7 + 0.25, 1.05)]), outline=255, width=L(r * 0.1))


def bubble(d, cx, cy, r):
    for x, y, s in ((-0.3, 0.2, 0.62), (0.55, -0.45, 0.35), (0.6, 0.6, 0.22)):
        d.ellipse(at(cx, cy, r, [(x - s, y - s), (x + s, y + s)]), outline=255, width=L(r * 0.12))
    d.arc(at(cx, cy, r, [(-0.7, -0.2), (0.1, 0.6)]), 200, 260, fill=255, width=L(r * 0.1))


def wave(d, cx, cy, r):
    for y in (-0.4, 0.15, 0.7):
        for k in range(3):
            x0 = -1.0 + k * 0.7
            d.arc(at(cx, cy, r, [(x0, y - 0.25), (x0 + 0.7, y + 0.25)]), 180, 360, fill=255, width=L(r * 0.11))


def skull(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.75, -0.95), (0.75, 0.45)]), fill=255)
    d.rectangle(at(cx, cy, r, [(-0.45, 0.2), (0.45, 0.85)]), fill=255)
    for x in (-0.32, 0.32):
        d.ellipse(at(cx, cy, r, [(x - 0.2, -0.45), (x + 0.2, -0.05)]), fill=0)
    for x in (-0.2, 0.0, 0.2):
        d.line(at(cx, cy, r, [(x, 0.5), (x, 0.85)]), fill=0, width=L(r * 0.07))


def mushroom(d, cx, cy, r):
    d.chord(at(cx, cy, r, [(-1, -0.9), (1, 0.6)]), 180, 360, fill=255)
    d.rounded_rectangle(at(cx, cy, r, [(-0.3, -0.15), (0.3, 0.95)]), radius=L(r * 0.1), fill=255)
    for x, y in ((-0.5, -0.45), (0.25, -0.6), (0.6, -0.3)):
        d.ellipse(at(cx, cy, r, [(x - 0.13, y - 0.13), (x + 0.13, y + 0.13)]), fill=0)


def fruit(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.85, -0.55), (0.85, 0.95)]), fill=255)
    d.line(at(cx, cy, r, [(0, -0.5), (0.15, -0.95)]), fill=255, width=L(r * 0.1))
    d.chord(at(cx, cy, r, [(0.1, -1.0), (0.8, -0.5)]), 150, 330, fill=255)


def pan(d, cx, cy, r):
    d.ellipse(at(cx, cy, r, [(-0.95, -0.6), (0.35, 0.7)]), fill=255)
    d.line(at(cx, cy, r, [(0.2, 0.0), (1.0, -0.4)]), fill=255, width=L(r * 0.16))


def tornado(d, cx, cy, r):
    for k, (y, w) in enumerate(((-0.8, 0.95), (-0.4, 0.7), (0.0, 0.5), (0.4, 0.32), (0.75, 0.15))):
        d.line(at(cx, cy, r, [(-w + k * 0.06, y), (w + k * 0.06, y)]), fill=255, width=L(r * 0.15))


def mouth(d, cx, cy, r):
    d.chord(at(cx, cy, r, [(-0.9, -0.6), (0.9, 0.8)]), 0, 180, fill=255)
    d.chord(at(cx, cy, r, [(-0.55, -0.2), (0.55, 0.5)]), 0, 180, fill=0)


STATUSES.update({'claw': claw, 'fang': fang, 'breath': breath, 'tail': tail, 'horn': horn, 'feather': feather,
                 'spores': spores, 'needles': needles, 'beam': beam, 'conch': conch, 'bomb': bomb, 'roar': roar,
                 'drill': drill, 'leaf': leaf, 'bug': bug, 'tentacle': tentacle, 'hammer': hammer, 'impact': impact,
                 'boot': boot, 'scissors': scissors, 'bubble': bubble, 'wave': wave, 'skull': skull,
                 'mushroom': mushroom, 'fruit': fruit, 'pan': pan, 'tornado': tornado, 'mouth': mouth})
