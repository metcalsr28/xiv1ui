"""Signature icons, group C: RNG, SAM, NIN, DRG, SMN, BLU. Painted with make_signature_icons' kit."""
import math
import random

from PIL import ImageDraw, ImageFilter

import make_signature_icons as K

W = K.W
p, pts, mask, shape, fill, glow, shadow, soften, radial, linear, sparkle, finish = (
    K.p, K.pts, K.mask, K.shape, K.fill, K.glow, K.shadow, K.soften, K.radial, K.linear, K.sparkle, K.finish)


# ---- local helpers --------------------------------------------------------------------------------------------------
def frame(x0, y0, x1, y1):
    """Local axis from (x0, y0) to (x1, y1): returns (length, to_unit(u, v)) where u runs along it, v across."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux

    def f(u, v):
        return (x0 + ux * u + nx * v, y0 + uy * u + ny * v)
    return L, f


def stroke(curve, w0, w1=None):
    """A tapered stroke along `curve` (unit points), width w0 at the start to w1 at the end."""
    if w1 is None:
        w1 = w0
    n = len(curve)
    left, right = [], []
    for i, (x, y) in enumerate(curve):
        a = curve[max(0, i - 1)]
        b = curve[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def arc(cx, cy, r, a0, a1, n=48, ry=None):
    ry = r if ry is None else ry
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * ry) for i in range(n + 1)]


def motes(c, seed, n, box, rr, color, core=(255, 255, 255, 220), blur=5):
    rnd = random.Random(seed)
    m = mask()
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(*rr)
        d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    glow(c, m, color, blur)
    fill(c, m, core)


def stars(c, spec, color=(255, 255, 255, 255), halo=(220, 230, 255, 255)):
    st = shape(lambda d: [sparkle(d, x, y, r) for x, y, r in spec])
    glow(c, st, halo, 8)
    fill(c, soften(st), color)


def streaks(c, lines, color, width=0.012, alpha=150, blur=3):
    m = mask()
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1) in lines:
        d.line(pts([(x0, y0), (x1, y1)]), fill=alpha, width=int(width * W))
    fill(c, m.filter(ImageFilter.GaussianBlur(blur)), color)


def arrow(d, x0, y0, x1, y1, w=0.04, hl=0.16, hw=0.085, fl=0.14, fw=0.065):
    """An arrow from tail (x0, y0) to tip (x1, y1)."""
    L, f = frame(x0, y0, x1, y1)
    d.polygon(pts([f(fl * 0.3, -w / 2), f(L - hl * 0.7, -w / 2), f(L - hl * 0.7, w / 2), f(fl * 0.3, w / 2)]), fill=255)
    d.polygon(pts([f(L - hl, -hw), f(L, 0), f(L - hl, hw), f(L - hl * 0.8, 0)]), fill=255)
    for s in (-1, 1):
        d.polygon(pts([f(0, s * fw), f(fl * 0.55, s * fw), f(fl, s * w / 2), f(fl * 0.3, s * w / 2)]), fill=255)


def katana(d, x0, y0, x1, y1, curve=0.035, part='all', k=1.0):
    """A katana from the pommel (x0, y0) to the tip (x1, y1); the blade bows toward +v."""
    L, f = frame(x0, y0, x1, y1)
    hilt = 0.27 * L
    if part in ('all', 'blade'):
        top, bot = [], []
        n = 24
        for i in range(n + 1):
            t = i / n
            u = hilt + 0.02 + (L - hilt - 0.02) * t
            bow = curve * t * t
            half = 0.042 * k * (1 - 0.3 * t)
            if t > 0.86:
                half *= (1 - t) / 0.14
            top.append(f(u, bow - half))
            bot.append(f(u, bow + half * 1.2))
        d.polygon(pts(top + bot[::-1]), fill=255)
    if part in ('all', 'hilt'):
        d.polygon(pts([f(0, -0.034 * k), f(hilt, -0.036 * k), f(hilt, 0.036 * k), f(0, 0.034 * k)]), fill=255)
        d.polygon(pts([f(hilt - 0.016 * k, -0.085 * k), f(hilt + 0.026 * k, -0.085 * k), f(hilt + 0.026 * k, 0.085 * k),
                       f(hilt - 0.016 * k, 0.085 * k)]), fill=255)


def lance(d, x0, y0, x1, y1, w=0.045, part='all', hs=1.0):
    """A dragoon's lance from butt (x0, y0) to point (x1, y1); hs scales the head and its collar."""
    L, f = frame(x0, y0, x1, y1)
    hb = L - 0.28 * hs
    if part in ('all', 'shaft'):
        d.polygon(pts([f(0, -w / 2), f(hb, -w / 2), f(hb, w / 2), f(0, w / 2)]), fill=255)
        d.polygon(pts([f(hb - 0.04 * hs, -0.10 * hs), f(hb + 0.02 * hs, -0.04 * hs), f(hb + 0.02 * hs, 0.04 * hs),
                       f(hb - 0.04 * hs, 0.10 * hs), f(hb - 0.01 * hs, 0)]), fill=255)
    if part in ('all', 'head'):
        d.polygon(pts([f(hb, -0.04 * hs), f(hb + 0.08 * hs, -0.08 * hs), f(L, 0), f(hb + 0.08 * hs, 0.08 * hs),
                       f(hb, 0.04 * hs)]), fill=255)


def eye_shape(d, cx, cy, rx, ry, vertical=False):
    top, bot = [], []
    n = 40
    for i in range(n + 1):
        t = -1 + 2 * i / n
        h = ry * (1 - t * t) ** 0.9
        top.append((cx + t * rx, cy - h))
        bot.append((cx + t * rx, cy + h))
    poly = top + bot[::-1]
    if vertical:
        poly = [(cx + (y - cy), cy + (x - cx)) for x, y in poly]
    d.polygon(pts(poly), fill=255)


def wyvern(d, cx, cy, s):
    """A wyvern seen from the front, wings spread."""
    def q(seq):
        return pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.ellipse(q([(-0.085, -0.08), (0.085, 0.16)]), fill=255)                                       # body
    d.polygon(q([(-0.045, -0.04), (0.045, -0.04), (0.035, -0.20), (-0.035, -0.20)]), fill=255)       # neck
    d.polygon(q([(0, -0.34), (0.075, -0.25), (0.03, -0.13), (-0.03, -0.13), (-0.075, -0.25)]), fill=255)  # head
    for sx in (-1, 1):
        d.polygon(q([(sx * 0.05, -0.31), (sx * 0.16, -0.43), (sx * 0.075, -0.26)]), fill=255)         # horn
        d.polygon(q([(sx * 0.04, -0.06), (sx * 0.20, -0.24), (sx * 0.47, -0.36), (sx * 0.43, -0.10),
                     (sx * 0.34, -0.15), (sx * 0.29, 0.02), (sx * 0.21, -0.04), (sx * 0.15, 0.10),
                     (sx * 0.07, 0.06)]), fill=255)                                                    # wing
        d.polygon(q([(sx * 0.04, 0.10), (sx * 0.11, 0.24), (sx * 0.06, 0.25), (sx * 0.02, 0.14)]), fill=255)  # leg
    d.polygon(q(stroke([(0, 0.12), (0.02, 0.24), (0.07, 0.33), (0.15, 0.37)], 0.07, 0.01)), fill=255)    # tail


# ---- RNG ------------------------------------------------------------------------------------------------------------
def eagle_eye_shot():
    c = radial((40, 140, 150, 255), (4, 22, 30, 255), 0.5, 0.5, 0.72)
    eye = shape(lambda d: eye_shape(d, 0.5, 0.5, 0.36, 0.20))
    glow(c, eye, (180, 250, 255, 255), 20, 1.2)
    fill(c, soften(eye), linear((255, 246, 214, 255), (210, 190, 140, 255), 90))
    iris = shape(lambda d: d.ellipse(pts([(0.38, 0.38), (0.62, 0.62)]), fill=255))
    fill(c, soften(iris), radial((255, 210, 70, 255), (190, 90, 10, 255), 0.5, 0.5, 0.12))
    pupil = shape(lambda d: d.ellipse(pts([(0.455, 0.43), (0.545, 0.57)]), fill=255))
    fill(c, soften(pupil), (16, 10, 6, 255))
    hi = shape(lambda d: d.ellipse(pts([(0.52, 0.43), (0.56, 0.47)]), fill=255))
    fill(c, soften(hi), (255, 255, 255, 255))
    streaks(c, [(0.04, 0.88, 0.40, 0.66), (0.10, 0.96, 0.42, 0.74), (0.02, 0.78, 0.36, 0.60)],
            (180, 250, 255, 255), 0.012, 160)
    ar = shape(lambda d: arrow(d, 0.10, 0.90, 0.88, 0.14))
    shadow(c, ar, 4, 7, 6, 160)
    glow(c, ar, (230, 255, 255, 255), 8, 1.2)
    fill(c, soften(ar), linear((255, 255, 255, 255), (180, 200, 210, 255), 90))
    stars(c, [(0.86, 0.14, 0.09)])
    return finish(c)


def barrage():
    c = radial((120, 150, 54, 255), (18, 26, 6, 255), 0.4, 0.6, 0.72)
    spec = []
    for k in range(3):
        o = (k - 1) * 0.19
        lead = 0.06 if k == 1 else -0.02
        spec.append((0.16 + o - lead, 0.84 + o + lead, 0.80 + o + lead, 0.20 + o - lead))
    streaks(c, [(x0 - 0.16, y0 + 0.16, x0 + 0.04, y0 - 0.04) for x0, y0, _, _ in spec],
            (240, 255, 190, 255), 0.03, 130, 6)
    ars = shape(lambda d: [arrow(d, *a) for a in spec])
    glow(c, ars, (240, 255, 170, 255), 16, 1.2)
    shadow(c, ars, 4, 7, 6, 150)
    fill(c, soften(ars), linear((255, 255, 236, 255), (214, 196, 140, 255), 90))
    stars(c, [(0.83, 0.16, 0.07)], halo=(240, 255, 190, 255))
    return finish(c)


def sharpshot():
    c = radial((50, 70, 150, 255), (6, 8, 30, 255), 0.5, 0.5, 0.72)
    ring = shape(lambda d: [d.ellipse(pts([(0.18, 0.18), (0.82, 0.82)]), outline=255, width=int(0.035 * W)),
                            d.ellipse(pts([(0.33, 0.33), (0.67, 0.67)]), outline=255, width=int(0.025 * W)),
                            d.rectangle(pts([(0.485, 0.08), (0.515, 0.30)]), fill=255),
                            d.rectangle(pts([(0.485, 0.70), (0.515, 0.92)]), fill=255),
                            d.rectangle(pts([(0.08, 0.485), (0.30, 0.515)]), fill=255),
                            d.rectangle(pts([(0.70, 0.485), (0.92, 0.515)]), fill=255)])
    glow(c, ring, (255, 90, 70, 255), 14, 1.3)
    fill(c, soften(ring), (255, 196, 170, 255))
    dot = shape(lambda d: d.ellipse(pts([(0.46, 0.46), (0.54, 0.54)]), fill=255))
    glow(c, dot, (255, 240, 200, 255), 14, 1.6)
    fill(c, soften(dot), (255, 255, 240, 255))
    ar = shape(lambda d: arrow(d, 0.94, 0.80, 0.53, 0.53))
    shadow(c, ar, 4, 6, 6, 150)
    fill(c, soften(ar), linear((255, 255, 255, 255), (190, 200, 220, 255), 90))
    return finish(c)


def scavenge():
    """Spent arrows planted in the ground, picked back up."""
    c = radial((170, 120, 60, 255), (20, 10, 4, 255), 0.5, 0.36, 0.72)
    mound = shape(lambda d: d.ellipse(pts([(0.02, 0.68), (0.98, 1.12)]), fill=255))
    fill(c, soften(mound, 3), linear((96, 60, 30, 255), (30, 16, 6, 255), 90))
    # arrows planted tip-down in the ground (top end, ground end); the fletching is a red chevron of vanes
    ars = [(0.22, 0.22, 0.32, 0.84), (0.52, 0.14, 0.50, 0.86), (0.82, 0.24, 0.70, 0.84)]
    shafts = shape(lambda d: [d.polygon(pts(stroke([(x0, y0), (x1, y1)], 0.05)), fill=255) for x0, y0, x1, y1 in ars])

    def vanes(d):
        for x0, y0, x1, y1 in ars:
            L, f = frame(x0, y0, x1, y1)
            for k in range(2):
                u = 0.02 + k * 0.075
                d.polygon(pts([f(u, 0), f(u + 0.06, -0.075), f(u + 0.11, -0.075), f(u + 0.05, 0),
                               f(u + 0.11, 0.075), f(u + 0.06, 0.075)]), fill=255)
    fl = shape(vanes)
    cut = shape(lambda d: d.ellipse(pts([(0.02, 0.72), (0.98, 1.16)]), fill=255))
    from PIL import ImageChops
    shafts = ImageChops.subtract(shafts, cut)
    both = ImageChops.lighter(shafts, fl)
    glow(c, both, (255, 220, 150, 255), 14, 1.6)
    shadow(c, both, 4, 6, 6, 170)
    fill(c, soften(shafts), linear((255, 252, 236, 255), (236, 196, 130, 255), 90))
    fill(c, soften(fl), linear((255, 120, 90, 255), (190, 40, 30, 255), 90))
    stars(c, [(0.66, 0.46, 0.08)], halo=(255, 220, 140, 255))
    motes(c, 21, 10, (0.15, 0.64, 0.85, 0.76), (0.008, 0.015), (255, 210, 140, 255))
    return finish(c)


# ---- SAM ------------------------------------------------------------------------------------------------------------
def meikyo_shisui():
    c = radial((70, 70, 160, 255), (6, 6, 26, 255), 0.5, 0.36, 0.75)
    water = shape(lambda d: d.rectangle(pts([(0, 0.58), (1, 1)]), fill=255))
    fill(c, soften(water, 4), linear((40, 50, 110, 255), (6, 8, 30, 255), 90))
    moon = shape(lambda d: d.ellipse(pts([(0.30, 0.12), (0.70, 0.52)]), fill=255))
    glow(c, moon, (200, 210, 255, 255), 30, 1.4)
    fill(c, soften(moon), radial((255, 255, 250, 255), (210, 214, 240, 255), 0.45, 0.28, 0.24))
    # reflection: broken horizontal bands
    refl = mask()
    d = ImageDraw.Draw(refl)
    for i, (y, w) in enumerate([(0.64, 0.17), (0.71, 0.14), (0.78, 0.11), (0.85, 0.08), (0.91, 0.05)]):
        d.rounded_rectangle(pts([(0.5 - w, y - 0.017), (0.5 + w, y + 0.017)]), radius=0.017 * W, fill=230 - i * 30)
    glow(c, refl, (190, 200, 255, 255), 10)
    fill(c, soften(refl), (240, 242, 255, 255))
    line = shape(lambda d: d.line(pts([(0.06, 0.585), (0.94, 0.585)]), fill=255, width=int(0.008 * W)))
    fill(c, soften(line).point(lambda v: int(v * 0.6)), (200, 210, 255, 255))
    stars(c, [(0.80, 0.20, 0.05), (0.18, 0.30, 0.035)])
    return finish(c)


def hasso():
    c = radial((180, 40, 40, 255), (26, 4, 6, 255), 0.5, 0.45, 0.72)
    streaks(c, [(0.24, 0.95, 0.24, 0.40), (0.76, 0.95, 0.76, 0.30), (0.16, 0.80, 0.16, 0.50), (0.84, 0.85, 0.84, 0.55)],
            (255, 180, 120, 255), 0.018, 120, 5)
    kw = dict(curve=-0.05, k=1.75)
    blade = shape(lambda d: katana(d, 0.36, 0.88, 0.62, 0.08, part='blade', **kw))
    hilt = shape(lambda d: katana(d, 0.36, 0.88, 0.62, 0.08, part='hilt', **kw))
    aura = shape(lambda d: d.ellipse(pts([(0.28, 0.10), (0.72, 0.82)]), fill=255))
    glow(c, aura, (255, 150, 80, 255), 40, 0.8)
    glow(c, blade, (255, 230, 200, 255), 18, 1.5)
    shadow(c, blade, 5, 7, 6, 160)
    fill(c, soften(blade), linear((255, 255, 255, 255), (150, 160, 180, 255), 0))
    # the hamon: a bright edge line along the blade's back half
    edge = shape(lambda d: katana(d, 0.36, 0.88, 0.62, 0.08, part='blade', curve=-0.05 - 0.02, k=0.7))
    from PIL import ImageChops
    fill(c, soften(ImageChops.multiply(edge, blade)), (255, 255, 255, 200))
    fill(c, soften(hilt), linear((70, 40, 50, 255), (16, 10, 14, 255), 0))
    L, f = frame(0.36, 0.88, 0.62, 0.08)
    tsuba = shape(lambda d: d.polygon(pts([f(0.27 * L - 0.02, -0.10), f(0.27 * L + 0.035, -0.10),
                                           f(0.27 * L + 0.035, 0.10), f(0.27 * L - 0.02, 0.10)]), fill=255))
    fill(c, soften(tsuba), (236, 196, 100, 255))
    stars(c, [(0.63, 0.09, 0.10)], halo=(255, 220, 180, 255))
    return finish(c)


def seigan():
    c = radial((50, 100, 170, 255), (4, 12, 30, 255), 0.5, 0.5, 0.72)
    shield = shape(lambda d: d.polygon(pts(stroke(arc(0.40, 0.56, 0.40, -62, 62, 40), 0.07, 0.07)), fill=255))
    glow(c, shield, (120, 200, 255, 255), 20, 1.3)
    fill(c, soften(shield, 3).point(lambda v: int(v * 0.7)), (190, 230, 255, 255))
    blade = shape(lambda d: katana(d, 0.08, 0.66, 0.90, 0.48, curve=-0.035, part='blade'))
    hilt = shape(lambda d: katana(d, 0.08, 0.66, 0.90, 0.48, curve=-0.035, part='hilt'))
    glow(c, blade, (220, 240, 255, 255), 12, 1.2)
    shadow(c, blade, 4, 7, 6, 150)
    fill(c, soften(blade), linear((255, 255, 255, 255), (160, 176, 200, 255), 90))
    fill(c, soften(hilt), linear((50, 40, 60, 255), (14, 10, 18, 255), 90))
    stars(c, [(0.80, 0.24, 0.07)])
    return finish(c)


def third_eye():
    c = radial((120, 60, 170, 255), (14, 4, 28, 255), 0.5, 0.5, 0.72)
    rays = mask()
    d = ImageDraw.Draw(rays)
    for i in range(12):
        a = math.pi * 2 * i / 12
        d.polygon(pts([(0.5, 0.5), (0.5 + math.cos(a - 0.08) * 0.6, 0.5 + math.sin(a - 0.08) * 0.6),
                       (0.5 + math.cos(a + 0.08) * 0.6, 0.5 + math.sin(a + 0.08) * 0.6)]), fill=70)
    fill(c, rays.filter(ImageFilter.GaussianBlur(8)), (240, 200, 255, 255))
    eye = shape(lambda d: eye_shape(d, 0.5, 0.5, 0.36, 0.17, vertical=True))
    glow(c, eye, (230, 160, 255, 255), 24, 1.5)
    fill(c, soften(eye), linear((255, 250, 255, 255), (220, 200, 240, 255), 90))
    iris = shape(lambda d: d.ellipse(pts([(0.40, 0.40), (0.60, 0.60)]), fill=255))
    fill(c, soften(iris), radial((255, 120, 200, 255), (130, 20, 120, 255), 0.5, 0.5, 0.11))
    pupil = shape(lambda d: d.ellipse(pts([(0.475, 0.43), (0.525, 0.57)]), fill=255))
    fill(c, soften(pupil), (20, 4, 24, 255))
    hi = shape(lambda d: d.ellipse(pts([(0.52, 0.43), (0.555, 0.465)]), fill=255))
    fill(c, soften(hi), (255, 255, 255, 255))
    return finish(c)


def meditate():
    c = radial((40, 120, 100, 255), (2, 18, 14, 255), 0.5, 0.5, 0.70)
    # an enso, brushed: thick at the start, thinning to a dry tail
    pts_ = arc(0.5, 0.5, 0.29, 120, 120 + 330, 60)
    enso = shape(lambda d: d.polygon(pts(stroke(pts_, 0.15, 0.05)), fill=255))
    glow(c, enso, (190, 255, 220, 255), 18, 1.6)
    shadow(c, enso, 4, 7, 6, 160)
    fill(c, soften(enso), linear((255, 255, 244, 255), (226, 244, 210, 255), 90))
    # TP welling up within the circle: a bright flame-like drop and a few rising motes
    motes(c, 5, 9, (0.38, 0.30, 0.62, 0.70), (0.014, 0.024), (255, 210, 110, 255), (255, 250, 210, 250), 7)
    flame = shape(lambda d: d.polygon(pts([(0.5, 0.30), (0.585, 0.50), (0.56, 0.60), (0.5, 0.64), (0.44, 0.60),
                                           (0.415, 0.50)]), fill=255))
    glow(c, flame, (255, 200, 80, 255), 18, 1.8)
    fill(c, soften(flame), linear((255, 255, 236, 255), (255, 200, 90, 255), 90))
    return finish(c)


def mijin_gakure():
    c = radial((230, 140, 50, 255), (40, 8, 4, 255), 0.5, 0.5, 0.62)
    flash = shape(lambda d: d.ellipse(pts([(0.16, 0.16), (0.84, 0.84)]), fill=255))
    glow(c, flash, (255, 240, 180, 255), 40, 1.2)
    rnd = random.Random(4)
    smoke = mask()
    sd = ImageDraw.Draw(smoke)
    for i in range(14):
        a = math.pi * 2 * i / 14 + rnd.uniform(-0.1, 0.1)
        r = rnd.uniform(0.33, 0.40)
        x, y, s = 0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r, rnd.uniform(0.09, 0.13)
        sd.ellipse(pts([(x - s, y - s), (x + s, y + s)]), fill=255)
    fill(c, soften(smoke, 6), radial((140, 70, 40, 255), (40, 18, 14, 255), 0.5, 0.5, 0.5))
    boom = []
    for i in range(22):
        a = math.pi * i / 11 + 0.1
        r = rnd.uniform(0.36, 0.44) if i % 2 == 0 else rnd.uniform(0.18, 0.24)
        boom.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
    bm = shape(lambda d: d.polygon(pts(boom), fill=255))
    glow(c, bm, (255, 200, 90, 255), 20, 1.3)
    fill(c, soften(bm, 2), radial((255, 255, 236, 255), (255, 150, 50, 255), 0.5, 0.5, 0.42))
    ninja = shape(lambda d: K.figure(d, 0.52, 0.55, 0.78))
    # the ninja breaking apart into ash at the edges
    glow(c, ninja, (255, 255, 230, 255), 12, 1.6)
    fill(c, soften(ninja), linear((40, 20, 20, 255), (10, 6, 6, 255), 90))
    motes(c, 9, 18, (0.12, 0.18, 0.40, 0.70), (0.008, 0.02), (60, 20, 10, 255), (30, 14, 10, 255), 3)
    stars(c, [(0.74, 0.30, 0.08)], halo=(255, 230, 160, 255))
    return finish(c)


def shuriken(d, cx, cy, r, rot=0.0):
    seq = []
    for i in range(8):
        a = math.pi * i / 4 + rot
        rr = r if i % 2 == 0 else r * 0.32
        seq.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts(seq), fill=255)


def yonin():
    c = radial((230, 170, 60, 255), (50, 22, 4, 255), 0.5, 0.5, 0.70)
    rays = mask()
    d = ImageDraw.Draw(rays)
    for i in range(16):
        a = math.pi * 2 * i / 16
        d.polygon(pts([(0.5, 0.5), (0.5 + math.cos(a - 0.07) * 0.6, 0.5 + math.sin(a - 0.07) * 0.6),
                       (0.5 + math.cos(a + 0.07) * 0.6, 0.5 + math.sin(a + 0.07) * 0.6)]), fill=90)
    fill(c, rays.filter(ImageFilter.GaussianBlur(6)), (255, 240, 180, 255))
    sun = shape(lambda d: d.ellipse(pts([(0.22, 0.22), (0.78, 0.78)]), fill=255))
    glow(c, sun, (255, 230, 140, 255), 24, 1.3)
    fill(c, soften(sun), radial((255, 250, 220, 255), (250, 180, 70, 255), 0.45, 0.42, 0.32))
    sh = shape(lambda d: shuriken(d, 0.5, 0.5, 0.33, 0.25))
    shadow(c, sh, 5, 8, 6, 160)
    fill(c, soften(sh), linear((70, 60, 70, 255), (20, 16, 22, 255), 90))
    hole = shape(lambda d: d.ellipse(pts([(0.465, 0.465), (0.535, 0.535)]), fill=255))
    fill(c, soften(hole), (255, 230, 160, 255))
    return finish(c)


def innin():
    c = radial((90, 50, 140, 255), (8, 4, 20, 255), 0.5, 0.45, 0.72)
    from PIL import ImageChops
    moon = ImageChops.subtract(shape(lambda d: d.ellipse(pts([(0.18, 0.12), (0.74, 0.68)]), fill=255)),
                               shape(lambda d: d.ellipse(pts([(0.32, 0.04), (0.88, 0.60)]), fill=255)))
    glow(c, moon, (220, 200, 255, 255), 22, 1.3)
    fill(c, soften(moon), linear((255, 252, 240, 255), (220, 210, 240, 255), 90))
    ninja = shape(lambda d: K.figure(d, 0.60, 0.58, 0.80))
    glow(c, ninja, (190, 150, 255, 255), 10, 1.4)
    fill(c, soften(ninja), linear((30, 20, 46, 255), (8, 4, 14, 255), 90))
    motes(c, 13, 10, (0.12, 0.70, 0.88, 0.92), (0.006, 0.012), (200, 160, 255, 255), (230, 220, 255, 200))
    return finish(c)


def katon():
    c = radial((170, 30, 50, 255), (26, 2, 8, 255), 0.5, 0.48, 0.70)
    # a fire spiral rising from an open scroll
    sp = []
    for i in range(60):
        t = i / 59
        a = math.radians(90 + 600 * t)
        r = 0.05 + 0.24 * t
        sp.append((0.5 + math.cos(a) * r, 0.44 + math.sin(a) * r * 0.9))
    swirl = shape(lambda d: d.polygon(pts(stroke(sp, 0.02, 0.10)), fill=255))
    glow(c, swirl, (255, 120, 40, 255), 24, 1.4)
    fill(c, soften(swirl), radial((255, 250, 200, 255), (240, 90, 30, 255), 0.5, 0.44, 0.30))
    core = shape(lambda d: d.ellipse(pts([(0.44, 0.38), (0.56, 0.50)]), fill=255))
    glow(c, core, (255, 255, 220, 255), 12, 1.5)
    fill(c, soften(core), (255, 255, 240, 255))
    scroll = shape(lambda d: [d.rectangle(pts([(0.22, 0.76), (0.78, 0.86)]), fill=255),
                              d.ellipse(pts([(0.16, 0.74), (0.26, 0.88)]), fill=255),
                              d.ellipse(pts([(0.74, 0.74), (0.84, 0.88)]), fill=255)])
    shadow(c, scroll, 4, 6, 5, 160)
    fill(c, soften(scroll), linear((250, 236, 200, 255), (200, 170, 120, 255), 90))
    ends = shape(lambda d: [d.ellipse(pts([(0.18, 0.765), (0.24, 0.855)]), fill=255),
                            d.ellipse(pts([(0.76, 0.765), (0.82, 0.855)]), fill=255)])
    fill(c, soften(ends), (150, 40, 30, 255))
    motes(c, 17, 10, (0.20, 0.08, 0.80, 0.30), (0.006, 0.013), (255, 160, 60, 255), (255, 230, 160, 255))
    return finish(c)


# ---- DRG ------------------------------------------------------------------------------------------------------------
def spirit_surge():
    c = radial((60, 70, 200, 255), (6, 6, 34, 255), 0.5, 0.45, 0.72)
    w = shape(lambda d: wyvern(d, 0.5, 0.50, 1.0))
    glow(c, w, (120, 180, 255, 255), 24, 1.2)
    fill(c, soften(w, 3).point(lambda v: int(v * 0.55)), (150, 200, 255, 255))
    ln = shape(lambda d: lance(d, 0.5, 0.97, 0.5, 0.06, w=0.075, hs=1.45))
    glow(c, ln, (220, 240, 255, 255), 16, 1.7)
    shadow(c, ln, 4, 6, 6, 170)
    fill(c, soften(ln), linear((255, 255, 255, 255), (150, 172, 220, 255), 0))
    stars(c, [(0.24, 0.20, 0.06), (0.78, 0.74, 0.05)])
    return finish(c)


def jump():
    """An angled dive: the lance strikes the ground and bursts."""
    c = radial((80, 150, 220, 255), (8, 22, 50, 255), 0.42, 0.35, 0.78)
    streaks(c, [(0.02, 0.12, 0.34, 0.44), (0.20, -0.02, 0.46, 0.26), (-0.02, 0.34, 0.22, 0.58)],
            (230, 245, 255, 255), 0.03, 160, 4)
    tip = (0.64, 0.68)
    ln = shape(lambda d: lance(d, 0.10, 0.10, tip[0], tip[1], w=0.08, hs=1.4))
    glow(c, ln, (230, 245, 255, 255), 12, 1.3)
    shadow(c, ln, 4, 7, 6, 170)
    fill(c, soften(ln), linear((255, 255, 255, 255), (150, 168, 206, 255), 0))
    # impact: the point buried in a starburst, a shock ring flat on the ground
    ring = shape(lambda d: d.ellipse(pts([(tip[0] - 0.26, tip[1] + 0.04), (tip[0] + 0.22, tip[1] + 0.18)]),
                                     outline=255, width=int(0.028 * W)))
    glow(c, ring, (255, 255, 255, 255), 8, 1.3)
    fill(c, soften(ring), (240, 250, 255, 255))
    burst = shape(lambda d: d.polygon(pts([(tip[0] + math.cos(math.radians(j * 22.5 + 8)) * r,
                                            tip[1] + math.sin(math.radians(j * 22.5 + 8)) * r * 0.85)
                                           for j, r in ((j, 0.28 if j % 4 == 0 else 0.17 if j % 2 == 0 else 0.06)
                                                        for j in range(16))]), fill=255))
    glow(c, burst, (255, 240, 170, 255), 18, 1.8)
    fill(c, soften(burst, 2), K.radial((255, 255, 255, 255), (255, 210, 110, 255), tip[0], tip[1], 0.18))
    return finish(c)


def high_jump():
    """A straight drop from far above the clouds: the lance falls point-down through them, a long trail behind."""
    c = linear((60, 20, 70, 255), (240, 140, 80, 255), 90)
    glow_bg = shape(lambda d: d.ellipse(pts([(0.15, 0.70), (0.85, 1.20)]), fill=255))
    fill(c, soften(glow_bg, 20), (255, 210, 140, 200))
    # cloud bank high up, pierced where the lance came through
    clouds = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.55), (x + r, y + r * 0.55)]), fill=255)
                              for x, y, r in ((0.08, 0.30, 0.16), (0.26, 0.26, 0.15), (0.40, 0.32, 0.12),
                                              (0.60, 0.32, 0.12), (0.74, 0.26, 0.15), (0.92, 0.30, 0.16),
                                              (0.18, 0.36, 0.12), (0.82, 0.36, 0.12))])
    fill(c, soften(clouds, 4), linear((255, 236, 236, 255), (200, 130, 160, 255), 90))
    trail = shape(lambda d: d.polygon(pts([(0.5, -0.05), (0.58, 0.40), (0.5, 0.52), (0.42, 0.40)]), fill=255))
    glow(c, trail, (255, 240, 200, 255), 20, 1.5)
    fill(c, soften(trail, 3), linear((255, 250, 230, 120), (255, 255, 245, 255), 90))
    ln = shape(lambda d: lance(d, 0.5, 0.38, 0.5, 0.92, w=0.08, hs=1.35))
    glow(c, ln, (255, 236, 200, 255), 14, 1.4)
    shadow(c, ln, 4, 7, 6, 170)
    fill(c, soften(ln), linear((255, 255, 255, 255), (170, 160, 186, 255), 0))
    return finish(c)


def call_wyvern():
    c = radial((30, 120, 110, 255), (2, 20, 20, 255), 0.5, 0.45, 0.72)
    rays = mask()
    d = ImageDraw.Draw(rays)
    for i in range(12):
        a = math.pi * 2 * i / 12
        d.polygon(pts([(0.5, 0.48), (0.5 + math.cos(a - 0.09) * 0.6, 0.48 + math.sin(a - 0.09) * 0.6),
                       (0.5 + math.cos(a + 0.09) * 0.6, 0.48 + math.sin(a + 0.09) * 0.6)]), fill=60)
    fill(c, rays.filter(ImageFilter.GaussianBlur(8)), (210, 255, 240, 255))
    w = shape(lambda d: wyvern(d, 0.5, 0.53, 1.0))
    glow(c, w, (140, 255, 220, 255), 16, 1.3)
    shadow(c, w, 5, 8, 7, 170)
    fill(c, soften(w), linear((200, 230, 250, 255), (70, 120, 170, 255), 90))
    eyes = shape(lambda d: [d.ellipse(pts([(0.465, 0.27), (0.49, 0.29)]), fill=255),
                            d.ellipse(pts([(0.51, 0.27), (0.535, 0.29)]), fill=255)])
    fill(c, soften(eyes, 0.8), (230, 60, 30, 255))
    return finish(c)


def ancient_circle():
    c = radial((150, 140, 60, 255), (24, 20, 6, 255), 0.5, 0.5, 0.72)
    ring = shape(lambda d: [d.ellipse(pts([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=int(0.035 * W)),
                            d.ellipse(pts([(0.24, 0.24), (0.76, 0.76)]), outline=255, width=int(0.018 * W))])
    runes = mask()
    rd = ImageDraw.Draw(runes)
    for i in range(12):
        a = math.pi * 2 * i / 12
        x, y = 0.5 + math.cos(a) * 0.31, 0.5 + math.sin(a) * 0.31
        L, f = frame(x, y, x + math.cos(a) * 0.01, y + math.sin(a) * 0.01)
        if i % 2:
            rd.polygon(pts([f(-0.03, 0), f(0, 0.025), f(0.03, 0), f(0, -0.025)]), fill=255)
        else:
            rd.line(pts([f(-0.035, -0.01), f(0.035, 0.01)]), fill=255, width=int(0.014 * W))
    star = []
    for i in range(6):
        a = math.pi / 2 + math.pi * 2 * i / 6
        star.append((0.5 + math.cos(a) * 0.25, 0.5 + math.sin(a) * 0.25))
    hexa = shape(lambda d: [d.line(pts([star[i], star[(i + 2) % 6]]), fill=255, width=int(0.016 * W)) for i in range(6)])
    allm = ImageChops_add(ImageChops_add(ring, runes), hexa)
    glow(c, allm, (255, 230, 120, 255), 16, 1.4)
    fill(c, soften(allm), linear((255, 250, 210, 255), (240, 200, 100, 255), 90))
    eye = shape(lambda d: eye_shape(d, 0.5, 0.5, 0.11, 0.07))
    glow(c, eye, (255, 120, 60, 255), 10, 1.4)
    fill(c, soften(eye), (255, 170, 60, 255))
    sl = shape(lambda d: d.ellipse(pts([(0.49, 0.44), (0.51, 0.56)]), fill=255))
    fill(c, soften(sl, 0.8), (40, 10, 4, 255))
    return finish(c)


def ImageChops_add(a, b):
    from PIL import ImageChops
    return ImageChops.lighter(a, b)


# ---- SMN ------------------------------------------------------------------------------------------------------------
def astral_flow():
    c = radial((120, 40, 160, 255), (8, 2, 24, 255), 0.5, 0.5, 0.72)
    arms = mask()
    d = ImageDraw.Draw(arms)
    for k in range(4):
        sp = []
        for i in range(40):
            t = i / 39
            a = math.radians(k * 90 + 220 * t)
            r = 0.04 + 0.38 * t
            sp.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
        d.polygon(pts(stroke(sp, 0.10, 0.01)), fill=255)
    glow(c, arms, (220, 140, 255, 255), 20, 1.3)
    fill(c, soften(arms, 2), linear((255, 230, 255, 255), (190, 130, 255, 255), 90))
    motes(c, 31, 22, (0.12, 0.12, 0.88, 0.88), (0.005, 0.011), (230, 200, 255, 255))
    core = shape(lambda d: d.ellipse(pts([(0.40, 0.40), (0.60, 0.60)]), fill=255))
    glow(c, core, (255, 240, 255, 255), 22, 1.6)
    fill(c, soften(core), (255, 252, 255, 255))
    stars(c, [(0.5, 0.5, 0.20)], halo=(255, 220, 255, 255))
    return finish(c)


def elemental_siphon():
    c = radial((30, 90, 120, 255), (4, 12, 24, 255), 0.5, 0.45, 0.72)
    cols = [(255, 90, 60), (130, 220, 255), (110, 230, 120), (240, 210, 90), (220, 120, 255), (90, 140, 255)]
    for i, col in enumerate(cols):
        a = math.pi * 2 * i / 6 - math.pi / 2
        x, y = 0.5 + math.cos(a) * 0.17, 0.30 + math.sin(a) * 0.12
        o = shape(lambda d, x=x, y=y: d.ellipse(pts([(x - 0.045, y - 0.045), (x + 0.045, y + 0.045)]), fill=255))
        glow(c, o, col + (255,), 8, 1.4)
        fill(c, soften(o), tuple(min(255, v + 60) for v in col) + (255,))
    stream = shape(lambda d: d.polygon(pts(stroke([(0.5, 0.32), (0.56, 0.44), (0.44, 0.54), (0.5, 0.64)], 0.06,
                                                  0.03)), fill=255))
    glow(c, stream, (160, 230, 255, 255), 12, 1.3)
    fill(c, soften(stream, 2), (220, 245, 255, 255))
    drop = shape(lambda d: d.polygon(pts([(0.5, 0.58)] + arc(0.5, 0.76, 0.13, -20, 200, 30)), fill=255))
    glow(c, drop, (100, 170, 255, 255), 18, 1.4)
    fill(c, soften(drop), radial((230, 245, 255, 255), (40, 100, 230, 255), 0.46, 0.70, 0.18))
    return finish(c)


def ifrit():
    c = radial((200, 60, 30, 255), (30, 4, 2, 255), 0.5, 0.55, 0.68)
    rnd = random.Random(2)
    fl = mask()
    d = ImageDraw.Draw(fl)
    for i in range(9):
        x = 0.2 + i * 0.075
        h = rnd.uniform(0.25, 0.42)
        d.polygon(pts([(x - 0.07, 0.62), (x + rnd.uniform(-0.03, 0.03), 0.62 - h), (x + 0.07, 0.62)]), fill=255)
    glow(c, fl, (255, 140, 40, 255), 14, 1.2)
    fill(c, soften(fl, 4).point(lambda v: int(v * 0.8)), (255, 150, 50, 255))
    horns = mask()
    hd = ImageDraw.Draw(horns)
    for sx in (-1, 1):
        cur = [(0.5 + sx * (0.10 + 0.24 * math.sin(t * 1.4)), 0.42 - 0.30 * t + 0.05 * t * t * 4 * (t > 0.7))
               for t in [i / 20 for i in range(21)]]
        cur = [(0.5 + sx * x, y) for x, y in [(0.10, 0.44), (0.20, 0.38), (0.28, 0.28), (0.31, 0.18),
                                               (0.29, 0.10), (0.24, 0.05)]]
        hd.polygon(pts(stroke(cur, 0.10, 0.01)), fill=255)
    head = shape(lambda d: d.polygon(pts([(0.33, 0.36), (0.67, 0.36), (0.70, 0.56), (0.60, 0.76), (0.5, 0.82),
                                          (0.40, 0.76), (0.30, 0.56)]), fill=255))
    both = ImageChops_add(horns, head)
    shadow(c, both, 5, 8, 7, 170)
    fill(c, soften(horns), linear((255, 236, 200, 255), (170, 110, 70, 255), 90))
    fill(c, soften(head), linear((150, 40, 20, 255), (60, 10, 6, 255), 90))
    brow = shape(lambda d: d.polygon(pts([(0.33, 0.47), (0.47, 0.54), (0.53, 0.54), (0.67, 0.47), (0.66, 0.43),
                                          (0.34, 0.43)]), fill=255))
    fill(c, soften(brow), (50, 8, 4, 255))
    eyes = shape(lambda d: [d.polygon(pts([(0.36, 0.52), (0.46, 0.57), (0.38, 0.58)]), fill=255),
                            d.polygon(pts([(0.64, 0.52), (0.54, 0.57), (0.62, 0.58)]), fill=255)])
    glow(c, eyes, (255, 230, 80, 255), 8, 1.6)
    fill(c, soften(eyes, 0.8), (255, 250, 200, 255))
    motes(c, 6, 12, (0.15, 0.10, 0.85, 0.40), (0.006, 0.013), (255, 170, 60, 255), (255, 230, 160, 255))
    return finish(c)


def shiva():
    c = radial((110, 170, 230, 255), (6, 18, 50, 255), 0.5, 0.42, 0.74)

    def crystal(d, cx, base, w, h, lean=0.0):
        d.polygon(pts([(cx - w, base), (cx - w * 0.8 + lean * 0.5, base - h * 0.75), (cx + lean, base - h),
                       (cx + w * 0.8 + lean * 0.5, base - h * 0.75), (cx + w, base)]), fill=255)
    big = shape(lambda d: crystal(d, 0.5, 0.86, 0.11, 0.72))
    side = shape(lambda d: [crystal(d, 0.32, 0.86, 0.075, 0.44, -0.08), crystal(d, 0.68, 0.86, 0.075, 0.48, 0.08)])
    glow(c, ImageChops_add(big, side), (200, 240, 255, 255), 22, 1.3)
    fill(c, soften(side), linear((230, 248, 255, 255), (110, 170, 230, 255), 0))
    fill(c, soften(big), linear((255, 255, 255, 255), (140, 200, 245, 255), 0))
    facet = shape(lambda d: d.polygon(pts([(0.5, 0.14), (0.61, 0.32), (0.61, 0.86), (0.5, 0.86)]), fill=255))
    from PIL import ImageChops
    fill(c, soften(ImageChops.multiply(facet, big)).point(lambda v: int(v * 0.35)), (60, 120, 200, 255))
    stars(c, [(0.24, 0.24, 0.08), (0.76, 0.18, 0.06), (0.52, 0.22, 0.05)])
    motes(c, 8, 14, (0.12, 0.10, 0.88, 0.70), (0.005, 0.01), (220, 240, 255, 255))
    return finish(c)


def garuda():
    c = radial((80, 170, 90, 255), (6, 28, 12, 255), 0.5, 0.45, 0.72)
    wind = mask()
    d = ImageDraw.Draw(wind)
    for r, a0 in ((0.40, 200), (0.34, 20), (0.44, 100)):
        d.polygon(pts(stroke(arc(0.5, 0.5, r, a0, a0 + 110, 30), 0.006, 0.03)), fill=150)
    fill(c, soften(wind, 3), (220, 255, 220, 255))

    def bird(d):
        for sx in (-1, 1):
            seq = [(0.5 + sx * 0.05, 0.40)]
            for i in range(6):
                t = i / 5
                a = math.radians(-60 + 70 * t)
                L = 0.42 - 0.12 * t
                seq.append((0.5 + sx * math.cos(a) * L, 0.46 + math.sin(a) * L))
                a2 = math.radians(-50 + 70 * t)
                seq.append((0.5 + sx * math.cos(a2) * (L - 0.07), 0.46 + math.sin(a2) * (L - 0.07)))
            seq.append((0.5 + sx * 0.06, 0.58))
            d.polygon(pts(seq), fill=255)
        d.ellipse(pts([(0.43, 0.34), (0.57, 0.62)]), fill=255)
        d.ellipse(pts([(0.44, 0.22), (0.56, 0.35)]), fill=255)
        d.polygon(pts([(0.47, 0.30), (0.53, 0.30), (0.5, 0.37)]), fill=255)
        d.polygon(pts([(0.46, 0.25), (0.40, 0.12), (0.50, 0.22), (0.60, 0.12), (0.54, 0.25)]), fill=255)
        d.polygon(pts([(0.45, 0.58), (0.36, 0.86), (0.44, 0.82), (0.5, 0.90), (0.56, 0.82), (0.64, 0.86),
                       (0.55, 0.58)]), fill=255)
    b = shape(bird)
    glow(c, b, (200, 255, 200, 255), 16, 1.3)
    shadow(c, b, 5, 8, 7, 150)
    fill(c, soften(b), linear((240, 255, 230, 255), (100, 190, 110, 255), 90))
    beak = shape(lambda d: d.polygon(pts([(0.475, 0.31), (0.525, 0.31), (0.5, 0.37)]), fill=255))
    fill(c, soften(beak, 0.8), (240, 190, 70, 255))
    return finish(c)


def carbuncle():
    c = radial((60, 170, 190, 255), (4, 26, 40, 255), 0.5, 0.48, 0.72)
    from PIL import ImageChops

    def ear(d, sx):
        L, f = frame(0.5 + sx * 0.12, 0.40, 0.5 + sx * 0.30, 0.06)
        d.polygon(pts([f(0, -0.06), f(L * 0.5, -0.07), f(L, 0), f(L * 0.5, 0.07), f(0, 0.06)]), fill=255)
    body = shape(lambda d: [ear(d, -1), ear(d, 1), d.ellipse(pts([(0.27, 0.30), (0.73, 0.72)]), fill=255),
                            d.ellipse(pts([(0.30, 0.60), (0.70, 0.92)]), fill=255)])
    glow(c, body, (200, 255, 255, 255), 16, 1.3)
    shadow(c, body, 5, 8, 7, 150)
    fill(c, soften(body), linear((236, 255, 250, 255), (120, 200, 210, 255), 90))
    eyes = shape(lambda d: [d.ellipse(pts([(0.35, 0.50), (0.44, 0.61)]), fill=255),
                            d.ellipse(pts([(0.56, 0.50), (0.65, 0.61)]), fill=255)])
    fill(c, soften(eyes, 0.8), (20, 30, 50, 255))
    glint = shape(lambda d: [d.ellipse(pts([(0.385, 0.515), (0.415, 0.545)]), fill=255),
                             d.ellipse(pts([(0.595, 0.515), (0.625, 0.545)]), fill=255)])
    fill(c, soften(glint, 0.6), (255, 255, 255, 255))
    gem = shape(lambda d: d.polygon(pts([(0.5, 0.33), (0.555, 0.40), (0.5, 0.47), (0.445, 0.40)]), fill=255))
    glow(c, gem, (255, 40, 60, 255), 14, 1.8)
    fill(c, soften(gem), linear((255, 140, 150, 255), (200, 10, 40, 255), 90))
    stars(c, [(0.54, 0.35, 0.05)], halo=(255, 160, 170, 255))
    return finish(c)


# ---- BLU ------------------------------------------------------------------------------------------------------------
def azure_lore():
    c = radial((40, 90, 210, 255), (4, 8, 40, 255), 0.5, 0.6, 0.70)

    def flame(d, cx, base, w, h, lean=0.0):
        left, right = [], []
        for i in range(41):
            t = i / 40
            half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
            x = cx + lean * t * t
            left.append((x - half, base - h * t))
            right.append((x + half, base - h * t))
        d.polygon(pts(left + right[::-1]), fill=255)
    outer = shape(lambda d: [flame(d, 0.5, 0.84, 0.26, 0.70, -0.05), flame(d, 0.30, 0.84, 0.11, 0.40, 0.08),
                             flame(d, 0.70, 0.84, 0.11, 0.42, -0.08)])
    mid = shape(lambda d: flame(d, 0.5, 0.84, 0.16, 0.50, -0.03))
    glow(c, outer, (60, 160, 255, 255), 28, 1.4)
    fill(c, soften(outer), linear((140, 230, 255, 255), (30, 80, 230, 255), 270))
    fill(c, soften(mid), linear((230, 250, 255, 255), (90, 170, 255, 255), 270))
    # the blue mage's eye of lore at the flame's heart
    eye = shape(lambda d: eye_shape(d, 0.5, 0.62, 0.10, 0.055))
    fill(c, soften(eye), (20, 40, 120, 255))
    pupil = shape(lambda d: d.ellipse(pts([(0.475, 0.595), (0.525, 0.645)]), fill=255))
    glow(c, pupil, (255, 255, 255, 255), 6, 1.5)
    fill(c, soften(pupil), (240, 250, 255, 255))
    motes(c, 12, 14, (0.25, 0.08, 0.75, 0.40), (0.006, 0.013), (120, 200, 255, 255))
    return finish(c)


def chain_affinity():
    from PIL import ImageChops
    c = radial((30, 130, 160, 255), (2, 20, 30, 255), 0.5, 0.5, 0.72)

    def link(d, cx, cy, ang, rx=0.20, ry=0.11, w=0.06):
        L, f = frame(cx, cy, cx + math.cos(math.radians(ang)), cy + math.sin(math.radians(ang)))
        ring = [f(math.cos(t) * rx, math.sin(t) * ry) for t in [math.pi * 2 * i / 60 for i in range(61)]]
        d.polygon(pts(stroke(ring, w, w)), fill=255)
    a = shape(lambda d: link(d, 0.37, 0.60, -40))
    b = shape(lambda d: link(d, 0.63, 0.40, -40))
    both = ImageChops.lighter(a, b)
    glow(c, both, (140, 240, 255, 255), 18, 1.3)
    shadow(c, both, 5, 8, 7, 150)
    paint = linear((240, 255, 255, 255), (110, 200, 220, 255), 90)
    # interlocked: b lies over a in the upper-left crossing, a over b in the lower-right
    upper = shape(lambda d: d.polygon(pts([(0, 0), (1, 0), (0, 1)]), fill=255))
    fill(c, soften(a), paint)
    b_top = ImageChops.lighter(ImageChops.multiply(b, upper), ImageChops.subtract(b, a))
    seam = ImageChops.multiply(ImageChops.subtract(b_top.filter(ImageFilter.MaxFilter(9)), b_top), a)
    fill(c, soften(seam), (20, 60, 80, 255))
    fill(c, soften(b_top), paint)
    a_top = ImageChops.subtract(ImageChops.multiply(a, b), upper)
    seam2 = ImageChops.multiply(ImageChops.subtract(a_top.filter(ImageFilter.MaxFilter(9)), a_top), b)
    fill(c, soften(seam2), (20, 60, 80, 255))
    fill(c, soften(a_top), paint)
    stars(c, [(0.80, 0.78, 0.05)], halo=(160, 255, 255, 255))
    return finish(c)


def burst_affinity():
    c = radial((170, 40, 160, 255), (24, 4, 30, 255), 0.5, 0.5, 0.70)
    burst = mask()
    d = ImageDraw.Draw(burst)
    n = 10
    for i in range(n):
        a = math.pi * 2 * i / n + 0.2
        r = 0.44 if i % 2 == 0 else 0.33
        L, f = frame(0.5, 0.5, 0.5 + math.cos(a), 0.5 + math.sin(a))
        d.polygon(pts([f(0.08, -0.05), f(r, 0), f(0.08, 0.05)]), fill=255)
    glow(c, burst, (255, 120, 230, 255), 18, 1.3)
    fill(c, soften(burst), linear((255, 230, 255, 255), (230, 110, 220, 255), 90))
    orb = shape(lambda d: d.ellipse(pts([(0.33, 0.33), (0.67, 0.67)]), fill=255))
    glow(c, orb, (140, 200, 255, 255), 20, 1.5)
    fill(c, soften(orb), radial((255, 255, 255, 255), (60, 120, 240, 255), 0.44, 0.42, 0.22))
    stars(c, [(0.45, 0.43, 0.08)])
    return finish(c)


def diffusion():
    c = radial((40, 170, 170, 255), (2, 26, 30, 255), 0.5, 0.5, 0.72)
    sats = []
    for i in range(5):
        a = math.pi * 2 * i / 5 - math.pi / 2
        sats.append((0.5 + math.cos(a) * 0.32, 0.5 + math.sin(a) * 0.32))
    beams = shape(lambda d: [d.polygon(pts(stroke([(0.5, 0.5), s], 0.07, 0.02)), fill=255) for s in sats])
    glow(c, beams, (160, 255, 240, 255), 10, 1.2)
    fill(c, soften(beams, 2).point(lambda v: int(v * 0.8)), (200, 255, 245, 255))
    small = shape(lambda d: [d.ellipse(pts([(x - 0.07, y - 0.07), (x + 0.07, y + 0.07)]), fill=255) for x, y in sats])
    glow(c, small, (120, 255, 230, 255), 12, 1.4)
    fill(c, soften(small), radial((255, 255, 255, 255), (110, 220, 210, 255), 0.5, 0.5, 0.40))
    orb = shape(lambda d: d.ellipse(pts([(0.37, 0.37), (0.63, 0.63)]), fill=255))
    glow(c, orb, (80, 160, 255, 255), 18, 1.5)
    fill(c, soften(orb), radial((255, 255, 255, 255), (50, 110, 230, 255), 0.45, 0.44, 0.17))
    return finish(c)


ICONS = {
    ('ja', 'Eagle Eye Shot'): eagle_eye_shot,
    ('ja', 'Barrage'): barrage,
    ('ja', 'Sharpshot'): sharpshot,
    ('ja', 'Scavenge'): scavenge,
    ('ja', 'Meikyo Shisui'): meikyo_shisui,
    ('ja', 'Hasso'): hasso,
    ('ja', 'Seigan'): seigan,
    ('ja', 'Third Eye'): third_eye,
    ('ja', 'Meditate'): meditate,
    ('ja', 'Mijin Gakure'): mijin_gakure,
    ('ja', 'Yonin'): yonin,
    ('ja', 'Innin'): innin,
    ('ma', 'Katon'): katon,
    ('ja', 'Spirit Surge'): spirit_surge,
    ('ja', 'Jump'): jump,
    ('ja', 'High Jump'): high_jump,
    ('ja', 'Call Wyvern'): call_wyvern,
    ('ja', 'Ancient Circle'): ancient_circle,
    ('ja', 'Astral Flow'): astral_flow,
    ('ja', 'Elemental Siphon'): elemental_siphon,
    ('ma', 'Ifrit'): ifrit,
    ('ma', 'Shiva'): shiva,
    ('ma', 'Garuda'): garuda,
    ('ma', 'Carbuncle'): carbuncle,
    ('ja', 'Azure Lore'): azure_lore,
    ('ja', 'Chain Affinity'): chain_affinity,
    ('ja', 'Burst Affinity'): burst_affinity,
    ('ja', 'Diffusion'): diffusion,
}
NAMES = [n for _, n in ICONS]
