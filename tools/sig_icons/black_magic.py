"""Signature icons, round 2: black magic. The elemental nukes in all their series (base, -ra, -ga, -ja, ancient
magic), helixes, elemental DoTs, Absorb-*, spikes, the black enfeebles and the showpieces (Meteor, Comet, Death,
Impact, Kaustra, Klimaform ...). See tools/make_signature_icons.py for the kit.

Visual language for the elemental series, so they part on one bar:
  base (Fire, Aero ..)   one element motif
  -ra (Fira ..)          the motif hovering over a glowing target circle on the ground
  -ga (Firaga ..)        a trio of the motif (the same trio marks the -ga enfeebles: Sleepga, Graviga ..)
  -ja (Firaja ..)        the motif on a white-hot starburst inside a shockwave ring
  ancient magic          a painting of its own (Flare's nova, Freeze's glacier, Tornado's funnel ..)
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_d as GD

W = K.W
p, pts, mask, shape, soften = K.p, K.pts, K.mask, K.shape, K.soften
FIRE, EARTH, LIGHT, WIND, ICE, WATER, THUNDER, DARK = 8, K.EARTH, 50, 120, 190, 225, K.THUNDER, 275    # (Earth dark brown, Thunder golden orange, Dark purple)


# ---- helpers --------------------------------------------------------------------------------------------------------
def C(c):
    return c + (255,) if len(c) == 3 else c


def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(C(c0), C(c1), cx, cy, r)


def T(seq, cx, cy, s):
    """Unit points drawn for a full-size motif centred on (0.5, 0.5) -> placed at (cx, cy), scale s."""
    return [(cx + (x - 0.5) * s, cy + (y - 0.5) * s) for x, y in seq]


def box(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return pts([(cx - rx, cy - ry), (cx + rx, cy + ry)])


def sh(c, m, dx=6, dy=10, r=10, a=170):
    K.shadow(c, m, int(round(dx)), int(round(dy)), max(1, r), a)


def glow(c, m, col, r, st=1.0):
    K.glow(c, m, C(col), max(2, r), st)


def fill(c, m, paint, soft=1.2):
    K.fill(c, soften(m, soft) if soft else m, C(paint) if isinstance(paint, tuple) else paint)


def sc(m, v):
    return m.point(lambda x: int(x * v))


def blur(m, r):
    return m.filter(ImageFilter.GaussianBlur(r))


def vgrad(top, bot, y0=0.0, y1=1.0):
    """A vertical gradient from `top` at y0 to `bot` at y1 (unit coords), flat beyond."""
    h = max(2, int((y1 - y0) * W))
    g = Image.linear_gradient('L').resize((W, h))
    m = Image.new('L', (W, W), 0)
    m.paste(255, (0, max(0, int(y1 * W)), W, W))
    m.paste(g, (0, int(y0 * W)))
    return Image.composite(Image.new('RGBA', (W, W), C(bot)), Image.new('RGBA', (W, W), C(top)), m)


def rgrad(c0, c1, cx, cy, r):
    return K.radial(C(c0), C(c1), cx, cy, r)


def dots(seed, n, x0, x1, y0, y1, r0, r1):
    return GA.dots(seed, n, x0, x1, y0, y1, r0, r1)


def motes(c, seed, n, bx, rr, glow_col, col):
    m = dots(seed, n, bx[0], bx[2], bx[1], bx[3], rr[0], rr[1])
    glow(c, m, glow_col, 6)
    K.fill(c, m, C(col))


def sparkles(c, spots, glow_col=(255, 255, 255)):
    GA.sparkles(c, spots, C(glow_col))


def rays(c, cx, cy, n, length, col, alpha=90, w=0.05, blur_r=8, phase=0.0):
    m = mask()
    d = ImageDraw.Draw(m)
    for i in range(n):
        a = math.pi * 2 * i / n + phase
        d.polygon(pts([(cx, cy), (cx + math.cos(a - w) * length, cy + math.sin(a - w) * length),
                       (cx + math.cos(a + w) * length, cy + math.sin(a + w) * length)]), fill=alpha)
    K.fill(c, blur(m, blur_r), C(col))


def star(cx, cy, n, r1, r2, rot=-math.pi / 2):
    return GA.star_pts(cx, cy, n, r1, r2, rot)


def jagged_star(cx, cy, n, r1, r2, seed, jit=0.25, rot=-math.pi / 2):
    rnd = random.Random(seed)
    out = []
    for i in range(n * 2):
        a = math.pi * i / n + rot + rnd.uniform(-0.12, 0.12)
        r = (r1 if i % 2 == 0 else r2) * (1 + rnd.uniform(-jit, jit) * (1 if i % 2 == 0 else 0.4))
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


def stroke(d, path, w0, w1=None, fillv=255):
    GD.stroke(d, path, w0, w1, fillv)


def bez(p0, p1, p2, n=24):
    return GA.bezier(p0, p1, p2, n)


def bez3(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def down_badge(c, cx=0.74, cy=0.72, s=1.0, col=(255, 90, 80), glow_col=(255, 60, 60)):
    """The small red 'down' arrow that marks a stat-lowering enfeeble."""
    m = shape(lambda d: d.polygon(pts([(cx - 0.05 * s, cy - 0.13 * s), (cx + 0.05 * s, cy - 0.13 * s),
                                       (cx + 0.05 * s, cy - 0.01 * s), (cx + 0.11 * s, cy - 0.01 * s),
                                       (cx, cy + 0.12 * s), (cx - 0.11 * s, cy - 0.01 * s),
                                       (cx - 0.05 * s, cy - 0.01 * s)]), fill=255))
    sh(c, m, 3, 5, 5, 200)
    glow(c, m, glow_col, 8, 1.2)
    fill(c, m, vgrad((255, 210, 200), col, cy - 0.13 * s, cy + 0.12 * s))


def trio(c, motif, big=0.64, small=0.46, y_big=0.42, y_small=0.64, dx=0.24):
    """The -ga mark: two small copies behind, one large in front."""
    motif(c, 0.5 - dx, y_small, small)
    motif(c, 0.5 + dx, y_small, small)
    motif(c, 0.5, y_big, big)


# ---- element motifs (each paints onto c at (cx, cy), scale s; s=1 is the base spell's full size) -----------------
def m_fire(c, cx, cy, s, sparks=True):
    def f(d, x, base, w, h, lean):
        GA.flame(d, cx + (x - 0.5) * s, cy + (base - 0.5) * s, w * s, h * s, lean * s)
    outer = shape(lambda d: [f(d, .5, .86, .27, .70, .04), f(d, .33, .86, .12, .40, -.06),
                             f(d, .67, .86, .12, .44, .07)])
    mid = shape(lambda d: f(d, .5, .86, .18, .52, .03))
    core = shape(lambda d: f(d, .5, .86, .10, .32, .01))
    y0, y1 = cy - 0.36 * s, cy + 0.36 * s
    glow(c, outer, (255, 110, 30), 30 * s, 1.3)
    fill(c, outer, vgrad((255, 200, 70), (230, 60, 20), y0, y1))
    fill(c, mid, vgrad((255, 236, 140), (255, 140, 40), y0, y1))
    glow(c, core, (255, 255, 220), 10 * s)
    fill(c, core, (255, 252, 230))
    if sparks:
        motes(c, 7, int(12 * s) + 2, (cx - .25 * s, cy - .42 * s, cx + .25 * s, cy - .1 * s),
              (0.006 * s + .002, 0.014 * s + .002), (255, 180, 80), (255, 230, 160))


def m_ice(c, cx, cy, s):
    def flake(d):
        wd = max(2, int(0.05 * W * s))
        for i in range(6):
            a = math.pi * 2 * i / 6 - math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            d.line(pts([(cx, cy), (cx + ux * 0.38 * s, cy + uy * 0.38 * s)]), fill=255, width=wd)
            for r, L in ((0.22, 0.11), (0.31, 0.07)):
                bx, by = cx + ux * r * s, cy + uy * r * s
                for sg in (-1, 1):
                    b = a + sg * math.radians(55)
                    d.line(pts([(bx, by), (bx + math.cos(b) * L * s, by + math.sin(b) * L * s)]), fill=255,
                           width=max(2, int(0.035 * W * s)))
            tx, ty = cx + ux * 0.40 * s, cy + uy * 0.40 * s
            q = 0.04 * s
            d.polygon(pts([(tx + ux * q, ty + uy * q), (tx - uy * q * .75, ty + ux * q * .75),
                           (tx - ux * q * .75, ty - uy * q * .75), (tx + uy * q * .75, ty - ux * q * .75)]), fill=255)
        d.polygon(pts(star(cx, cy, 6, 0.11 * s, 0.07 * s)), fill=255)
    m = shape(flake)
    sh(c, m, 4 * s, 6 * s, 6 * s, 140)
    glow(c, m, (150, 220, 255), 18 * s, 1.4)
    fill(c, m, vgrad((255, 255, 255), (170, 220, 250), cy - .4 * s, cy + .4 * s))
    fill(c, shape(lambda d: d.ellipse(box(cx, cy, .05 * s), fill=255)), (120, 190, 240))


BOLT = [(0.58, 0.08), (0.30, 0.50), (0.47, 0.50), (0.36, 0.92), (0.74, 0.40), (0.55, 0.40), (0.70, 0.08)]


def m_thunder(c, cx, cy, s, tip_sparkle=True):
    m = shape(lambda d: d.polygon(pts(T(BOLT, cx, cy, s)), fill=255))
    glow(c, m, (255, 230, 100), 30 * s, 1.4)
    glow(c, m, (255, 255, 200), 10 * s, 1.2)
    fill(c, m, vgrad((255, 255, 236), (255, 210, 60), cy - .42 * s, cy + .42 * s))
    if tip_sparkle:
        x, y = T([(0.36, 0.92)], cx, cy, s)[0]
        sparkles(c, [(x, y, 0.08 * s)], (255, 240, 160))


ROCKS = [
    [(0.30, 0.38), (0.46, 0.22), (0.64, 0.24), (0.74, 0.40), (0.70, 0.60), (0.52, 0.68), (0.34, 0.60)],
    [(0.12, 0.62), (0.20, 0.52), (0.32, 0.54), (0.36, 0.68), (0.26, 0.76), (0.14, 0.72)],
    [(0.68, 0.66), (0.78, 0.56), (0.90, 0.62), (0.88, 0.76), (0.74, 0.78)],
    [(0.20, 0.24), (0.27, 0.18), (0.32, 0.25), (0.26, 0.31)],
    [(0.76, 0.16), (0.84, 0.14), (0.86, 0.22), (0.79, 0.25)],
]


def m_earth(c, cx, cy, s, n=5):
    rocks = [T(r, cx, cy, s) for r in ROCKS[:n]]
    m = shape(lambda d: [d.polygon(pts(r), fill=255) for r in rocks])
    sh(c, m, 6 * s, 10 * s, 8 * s, 220)
    glow(c, m, (255, 230, 140), 10 * s, 0.8)
    fill(c, m, vgrad((196, 170, 140), (84, 62, 46), cy - .35 * s, cy + .3 * s))
    facets = shape(lambda d: [d.polygon(pts([r[0], r[1], r[2], ((r[0][0] + r[2][0]) / 2 + 0.01 * s,
                                                                (r[0][1] + r[2][1]) / 2 + 0.06 * s)]), fill=255)
                              for r in rocks[:3]])
    fill(c, sc(ImageChops.multiply(facets, m), 0.7), (255, 244, 210))
    cr = T([(0.50, 0.30), (0.54, 0.42), (0.48, 0.50), (0.56, 0.62)], cx, cy, s)
    cracks = shape(lambda d: d.line(pts(cr), fill=255, width=max(2, int(0.012 * W * s))))
    fill(c, sc(cracks, 0.7), (80, 50, 24))


def wind_blades(d, cx, cy, s, n=3, rot=0.0, r0=0.06, r1=0.40, sweep=2.3, w=0.075):
    """Tapered crescent blades spiralling out of (cx, cy): a pinwheel of wind."""
    for k in range(n):
        a0 = rot + k * 2 * math.pi / n
        outer, inner = [], []
        for i in range(41):
            t = i / 40
            a = a0 + t * sweep
            r = (r0 + (r1 - r0) * t) * s
            ww = w * s * math.sin(math.pi * t ** 0.9) ** 0.8
            ux, uy = math.cos(a), math.sin(a)
            outer.append((cx + ux * (r + ww), cy + uy * (r + ww)))
            inner.append((cx + ux * (r - ww * 0.35), cy + uy * (r - ww * 0.35)))
        d.polygon(pts(outer + inner[::-1]), fill=255)


def m_wind(c, cx, cy, s, leaves=True):
    m = shape(lambda d: wind_blades(d, cx, cy, s))
    sh(c, m, 4 * s, 7 * s, 7 * s, 140)
    glow(c, m, (140, 255, 170), 20 * s, 1.4)
    fill(c, m, rgrad((250, 255, 245), (110, 220, 140), cx, cy, 0.42 * s))
    eye = shape(lambda d: d.ellipse(box(cx, cy, 0.06 * s), fill=255))
    glow(c, eye, (220, 255, 230), 10 * s, 1.3)
    fill(c, eye, (250, 255, 250))
    if leaves:
        lv = shape(lambda d: [GA.leaf(d, cx + x * s, cy + y * s, a, 0.13 * s, 0.035 * s)
                              for x, y, a in ((0.30, -0.33, 2.6), (-0.36, 0.22, -0.6), (0.20, 0.34, 0.3))])
        sh(c, lv, 3 * s, 4 * s, 4 * s, 120)
        fill(c, lv, (140, 230, 110))


def m_water(c, cx, cy, s, splash=False):
    r = 0.27 * s
    if splash:
        drops = []
        for i in range(9):
            a = -math.pi / 2 + (i - 4) * 0.36
            L = (0.36 + 0.06 * (i % 2)) * s
            drops.append((cx + math.cos(a) * L, cy + math.sin(a) * L * 1.0, (0.030 - 0.004 * (i % 2)) * s))
        dm = shape(lambda d: [d.ellipse(box(x, y, rr), fill=255) for x, y, rr in drops])
        glow(c, dm, (120, 200, 255), 8 * s, 1.3)
        fill(c, dm, (220, 245, 255))
    orb = shape(lambda d: d.ellipse(box(cx, cy, r), fill=255))
    sh(c, orb, 5 * s, 8 * s, 8 * s, 160)
    glow(c, orb, (90, 180, 255), 22 * s, 1.3)
    fill(c, orb, rgrad((190, 236, 255), (20, 80, 200), cx - .3 * r, cy - .35 * r, r * 1.7))
    # a wave curling inside the sphere
    wave = shape(lambda d: d.arc(box(cx + .05 * r, cy + .1 * r, r * .62), 150, 350, fill=255,
                                 width=max(2, int(0.13 * r * W))))
    curl = shape(lambda d: d.ellipse(box(cx + .26 * r, cy + .02 * r, r * .17), fill=255))
    fill(c, sc(ImageChops.lighter(wave, curl), 0.75), (235, 250, 255))
    hi = shape(lambda d: d.ellipse(pts([(cx - .62 * r, cy - .72 * r), (cx - .18 * r, cy - .38 * r)]), fill=255))
    fill(c, sc(hi, 0.9), (255, 255, 255), 3 * s + 1)


ELEM = {
    'fire': dict(m=m_fire, bg=((150, 46, 18), (24, 4, 6)), glow=(255, 120, 40), light=(255, 220, 150)),
    'ice': dict(m=m_ice, bg=((100, 180, 236), (6, 20, 44)), glow=(150, 220, 255), light=(235, 250, 255)),
    'wind': dict(m=m_wind, bg=((70, 166, 96), (6, 30, 14)), glow=(150, 255, 170), light=(235, 255, 235)),
    'earth': dict(m=m_earth, bg=((214, 170, 50), (34, 20, 4)), glow=(255, 220, 120), light=(255, 240, 200)),
    'thunder': dict(m=m_thunder, bg=((70, 60, 160), (8, 6, 26)), glow=(255, 230, 100), light=(255, 250, 210)),
    'water': dict(m=m_water, bg=((26, 112, 196), (4, 12, 40)), glow=(100, 190, 255), light=(220, 242, 255)),
}


# ---- base nukes -----------------------------------------------------------------------------------------------------
def aero():
    """A pinwheel of wind blades whipping leaves around."""
    c = bg(*ELEM['wind']['bg'])
    gust = shape(lambda d: [d.arc(box(0.5, 0.5, r), a, a + 90, fill=255, width=int(0.014 * W))
                            for r, a in ((0.44, 200), (0.44, 20), (0.36, 110), (0.36, 290))])
    fill(c, sc(blur(gust, 3), 0.5), (210, 255, 220), 0)
    m_wind(c, 0.5, 0.5, 1.0)
    return K.finish(c)


def water():
    """A sphere of water with a wave curling inside, droplets bursting off its crown."""
    c = bg(*ELEM['water']['bg'])
    motes(c, 5, 14, (0.1, 0.1, 0.9, 0.9), (0.005, 0.011), (140, 210, 255), (230, 245, 255))
    m_water(c, 0.5, 0.56, 1.05, splash=True)
    return K.finish(c)


# ---- -ra: the motif over a target circle -----------------------------------------------------------------------------
def ra(elem):
    e = ELEM[elem]

    def paint():
        c = bg(*e['bg'], cy=0.5)
        pool = shape(lambda d: d.ellipse(box(0.5, 0.76, 0.36, 0.12), fill=255))
        fill(c, sc(blur(pool, 16), 0.55), e['glow'], 0)
        ring = shape(lambda d: [d.ellipse(box(0.5, 0.76, 0.37, 0.12), outline=255, width=int(0.026 * W)),
                                d.ellipse(box(0.5, 0.76, 0.22, 0.068), outline=255, width=int(0.016 * W))])
        ticks = shape(lambda d: [d.polygon(pts(q), fill=255) for q in (
            [(0.06, 0.76), (0.15, 0.735), (0.15, 0.785)], [(0.94, 0.76), (0.85, 0.735), (0.85, 0.785)],
            [(0.5, 0.92), (0.47, 0.86), (0.53, 0.86)])])
        rm = ImageChops.lighter(ring, ticks)
        glow(c, rm, e['glow'], 10, 1.5)
        fill(c, rm, e['light'])
        col = shape(lambda d: d.polygon(pts([(0.36, 0.76), (0.42, 0.30), (0.58, 0.30), (0.64, 0.76)]), fill=255))
        fill(c, sc(blur(col, 14), 0.35), e['light'], 0)
        e['m'](c, 0.5, 0.42, 0.66)
        return K.finish(c)
    return paint


# ---- -ga: a trio of the motif ----------------------------------------------------------------------------------------
def ga(elem):
    e = ELEM[elem]

    def paint():
        c = bg(*e['bg'], cy=0.55)
        if elem == 'earth':
            trio(c, lambda c, x, y, s: m_earth(c, x, y, s, 1), 0.92, 0.70, 0.42, 0.66, 0.25)
        elif elem == 'thunder':
            trio(c, lambda c, x, y, s: m_thunder(c, x, y, s, False), 0.68, 0.50, 0.44, 0.60, 0.26)
        elif elem == 'wind':
            trio(c, lambda c, x, y, s: m_wind(c, x, y, s, False), 0.62, 0.46, 0.40, 0.66, 0.25)
        elif elem == 'water':
            trio(c, m_water, 0.72, 0.52, 0.40, 0.66, 0.25)
        elif elem == 'fire':
            trio(c, lambda c, x, y, s: m_fire(c, x, y, s, False), 0.66, 0.50, 0.42, 0.62, 0.25)
        else:
            trio(c, m_ice, 0.62, 0.46, 0.40, 0.64, 0.25)
        return K.finish(c)
    return paint


# ---- -ja: the motif on a starburst inside a shockwave ring -------------------------------------------------------------
def ja(elem):
    e = ELEM[elem]

    def paint():
        c0, c1 = e['bg']
        c = bg(tuple(min(255, int(v * 1.25)) for v in c0), c1, r=0.68)
        rays(c, 0.5, 0.5, 16, 0.7, e['light'], 110, 0.06, 6)
        burst = shape(lambda d: d.polygon(pts(star(0.5, 0.5, 8, 0.40, 0.17, -math.pi / 2 + math.pi / 8)), fill=255))
        glow(c, burst, e['glow'], 22, 1.3)
        fill(c, sc(burst, 0.8), rgrad((255, 255, 250), e['glow'], 0.5, 0.5, 0.42))
        ring = shape(lambda d: [d.ellipse(box(0.5, 0.5, 0.415), outline=255, width=int(0.03 * W)),
                                d.ellipse(box(0.5, 0.5, 0.355), outline=255, width=int(0.012 * W))])
        glow(c, ring, e['glow'], 12, 1.6)
        fill(c, ring, (255, 255, 245))
        dark = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.25), fill=255))
        fill(c, sc(blur(dark, 16), 0.55), tuple(int(v * 0.5) for v in c1), 0)
        if elem == 'earth':
            m_earth(c, 0.5, 0.5, 0.78, 3)
        elif elem == 'wind':
            m_wind(c, 0.5, 0.5, 0.72, False)
        elif elem == 'thunder':
            m_thunder(c, 0.5, 0.5, 0.72, False)
        elif elem == 'fire':
            m_fire(c, 0.5, 0.48, 0.74, False)
        elif elem == 'water':
            m_water(c, 0.5, 0.5, 0.86)
        else:
            m_ice(c, 0.5, 0.5, 0.74)
        return K.finish(c)
    return paint


# ---- ancient magic --------------------------------------------------------------------------------------------------
def flare():
    """A nova: a white-hot core erupting in a corona of fire inside a blazing shock ring."""
    c = bg((170, 50, 10), (20, 2, 2), r=0.66)
    ring = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.40), outline=255, width=int(0.05 * W)))
    glow(c, ring, (255, 120, 30), 24, 1.6)
    fill(c, sc(blur(ring, 4), 0.85), (255, 190, 90), 0)
    corona = shape(lambda d: d.polygon(pts(jagged_star(0.5, 0.5, 14, 0.36, 0.20, 3, 0.25)), fill=255))
    glow(c, corona, (255, 90, 20), 26, 1.4)
    fill(c, corona, rgrad((255, 240, 160), (230, 60, 10), 0.5, 0.5, 0.38), 3)
    inner = shape(lambda d: d.polygon(pts(jagged_star(0.5, 0.5, 10, 0.26, 0.17, 9, 0.2)), fill=255))
    fill(c, inner, rgrad((255, 255, 230), (255, 160, 40), 0.5, 0.5, 0.26), 3)
    core = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.13), fill=255))
    glow(c, core, (255, 255, 230), 22, 1.8)
    fill(c, core, (255, 255, 250), 3)
    motes(c, 13, 16, (0.1, 0.1, 0.9, 0.9), (0.006, 0.014), (255, 160, 60), (255, 230, 170))
    return K.finish(c)


def freeze():
    """A glacier of ice crystals bursting up out of the ground."""
    c = bg((80, 160, 220), (4, 16, 40), cy=0.6, r=0.7)
    mist = shape(lambda d: d.ellipse(box(0.5, 0.86, 0.46, 0.14), fill=255))
    fill(c, sc(blur(mist, 18), 0.8), (210, 240, 255), 0)

    def shard(cx, base, w, h, lean):
        tip = (cx + lean, base - h)
        return [(cx - w, base), (cx - w * 0.85, base - h * 0.62), tip, (cx + w * 0.85, base - h * 0.62), (cx + w, base)]
    shards = [(0.24, 0.84, 0.07, 0.42, -0.07), (0.76, 0.84, 0.07, 0.46, 0.08), (0.37, 0.86, 0.08, 0.58, -0.03),
              (0.63, 0.86, 0.08, 0.60, 0.04), (0.5, 0.88, 0.11, 0.78, 0.0)]
    for cx, base, w, h, lean in shards:
        q = shard(cx, base, w, h, lean)
        m = shape(lambda d: d.polygon(pts(q), fill=255))
        sh(c, m, 4, 6, 6, 150)
        glow(c, m, (150, 220, 255), 12, 1.0)
        fill(c, m, vgrad((250, 255, 255), (90, 170, 230), base - h, base))
        lf = shape(lambda d: d.polygon(pts([q[0], q[1], q[2], (cx + lean * 0.4, base)]), fill=255))
        fill(c, sc(lf, 0.55), (255, 255, 255))
        edge = shape(lambda d: d.line(pts([q[2], (cx + lean * 0.3, base)]), fill=255, width=int(0.008 * W)))
        fill(c, sc(edge, 0.6), (60, 130, 200))
    sparkles(c, [(0.50, 0.12, 0.08), (0.80, 0.34, 0.05), (0.20, 0.40, 0.045)], (200, 240, 255))
    return K.finish(c)


def tornado():
    """A towering funnel of wind tearing up debris."""
    c = bg((90, 150, 110), (8, 22, 14), cy=0.4, r=0.74)
    dust = dots(29, 10, 0.2, 0.8, 0.78, 0.92, 0.06, 0.1)
    fill(c, sc(blur(dust, 12), 0.6), (150, 170, 130), 0)
    rings = []
    for i in range(10):
        t = i / 9
        y = 0.15 + t * 0.68
        rx = 0.37 * (1 - t) ** 1.15 + 0.03
        cx = 0.5 + 0.07 * math.sin(t * 3.2)
        rings.append((cx, y, rx, rx * 0.24))
    body = shape(lambda d: [d.ellipse(box(x, y, rx, ry + 0.03), fill=255) for x, y, rx, ry in rings] +
                 [d.polygon(pts([(rings[i][0] - rings[i][2], rings[i][1]), (rings[i][0] + rings[i][2], rings[i][1]),
                                 (rings[i + 1][0] + rings[i + 1][2], rings[i + 1][1]),
                                 (rings[i + 1][0] - rings[i + 1][2], rings[i + 1][1])]), fill=255)
                  for i in range(9)])
    glow(c, body, (170, 255, 190), 22, 1.2)
    fill(c, sc(body, 0.55), vgrad((200, 236, 210), (90, 140, 110), 0.12, 0.86))
    # wind bands sweeping diagonally round the funnel
    bands = mask()
    bd = ImageDraw.Draw(bands)
    for k in range(7):
        path = []
        for i in range(30):
            t = i / 29
            u = (k + t * 1.2) / 7.6
            if u > 1:
                break
            x0, y0, rx0, ry0 = rings[0]
            idx = min(8.999, u * 9)
            j = int(idx)
            f = idx - j
            cx = rings[j][0] + (rings[j + 1][0] - rings[j][0]) * f
            y = rings[j][1] + (rings[j + 1][1] - rings[j][1]) * f
            rx = rings[j][2] + (rings[j + 1][2] - rings[j][2]) * f
            a = math.pi * (0.1 + 0.8 * t)
            path.append((cx - math.cos(a) * rx, y + math.sin(a) * rx * 0.24))
        if len(path) > 2:
            stroke(bd, path, 0.012, 0.03)
    sh(c, bands, 3, 4, 4, 120)
    glow(c, bands, (230, 255, 235), 6, 1.2)
    fill(c, bands, (250, 255, 250))
    top = shape(lambda d: d.ellipse(box(rings[0][0], rings[0][1], rings[0][2], rings[0][3]), outline=255,
                                    width=int(0.02 * W)))
    fill(c, sc(top, 0.8), (240, 255, 240))
    deb = shape(lambda d: [d.polygon(pts([(x, y), (x + .035, y - .014), (x + .028, y + .024)]), fill=255)
                           for x, y in ((0.12, 0.32), (0.84, 0.22), (0.80, 0.58), (0.16, 0.62), (0.88, 0.42))])
    sh(c, deb, 2, 3, 3, 150)
    fill(c, deb, (110, 86, 60))
    lv = shape(lambda d: [GA.leaf(d, x, y, a, 0.09, 0.025) for x, y, a in ((0.20, 0.46, 2.4), (0.76, 0.76, -0.4))])
    fill(c, lv, (150, 230, 110))
    return K.finish(c)


def burst():
    """A sphere of lightning crackling with arcs that leap out in every direction."""
    c = bg((90, 50, 170), (8, 4, 24), r=0.7)
    rnd = random.Random(21)
    arcs = mask()
    ad = ImageDraw.Draw(arcs)
    for k in range(8):
        a = k * math.pi / 4 + rnd.uniform(-0.2, 0.2)
        x, y, path = 0.5, 0.5, [(0.5, 0.5)]
        for i in range(5):
            r = 0.18 + i * 0.06
            aa = a + rnd.uniform(-0.28, 0.28)
            path.append((0.5 + math.cos(aa) * r, 0.5 + math.sin(aa) * r))
        stroke(ad, path, 0.026, 0.008)
        fx, fy = path[2]
        b = a + (0.6 if k % 2 else -0.6)
        stroke(ad, [(fx, fy), (fx + math.cos(b) * 0.08, fy + math.sin(b) * 0.08),
                    (fx + math.cos(b + 0.3) * 0.13, fy + math.sin(b + 0.3) * 0.13)], 0.014, 0.004)
    glow(c, arcs, (200, 160, 255), 14, 1.6)
    fill(c, arcs, (250, 245, 255))
    orb = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.20), fill=255))
    glow(c, orb, (220, 170, 255), 26, 1.6)
    fill(c, orb, rgrad((255, 255, 255), (160, 100, 255), 0.46, 0.44, 0.24))
    inner = shape(lambda d: stroke(d, [(0.42, 0.40), (0.52, 0.48), (0.46, 0.52), (0.58, 0.62)], 0.022, 0.012))
    fill(c, sc(inner, 0.9), (255, 250, 200))
    return K.finish(c)


def flood():
    """A great wave rearing up and curling over to crash down."""
    c = bg((40, 120, 200), (4, 12, 40), cx=0.4, cy=0.35, r=0.75)
    motes(c, 17, 10, (0.1, 0.06, 0.6, 0.4), (0.006, 0.012), (160, 220, 255), (230, 245, 255))
    outer = ([(0.02, 0.98), (0.02, 0.74)] + bez3((0.02, 0.74), (0.20, 0.66), (0.36, 0.26), (0.66, 0.16)) +
             bez3((0.66, 0.16), (0.86, 0.12), (0.98, 0.30), (0.88, 0.44)) +
             bez3((0.88, 0.44), (0.82, 0.52), (0.70, 0.46), (0.72, 0.38)) +
             bez3((0.72, 0.38), (0.74, 0.32), (0.62, 0.30), (0.56, 0.42)) +
             bez3((0.56, 0.42), (0.50, 0.56), (0.66, 0.76), (0.98, 0.80)) + [(0.98, 0.98)])
    wave = shape(lambda d: d.polygon(pts(outer), fill=255))
    sh(c, wave, 6, 8, 10, 170)
    glow(c, wave, (90, 190, 255), 18, 1.2)
    fill(c, wave, vgrad((170, 230, 255), (10, 50, 140), 0.14, 0.92))
    face = shape(lambda d: d.polygon(pts(bez3((0.56, 0.42), (0.50, 0.56), (0.66, 0.76), (0.98, 0.80)) +
                                         [(0.98, 0.98), (0.6, 0.98)]), fill=255))
    fill(c, sc(ImageChops.multiply(face, wave), 0.6), (6, 30, 90), 6)
    foam = shape(lambda d: [stroke(d, bez3((0.12, 0.70), (0.28, 0.58), (0.38, 0.26), (0.66, 0.19)), 0.02, 0.045),
                            stroke(d, bez3((0.66, 0.19), (0.84, 0.16), (0.94, 0.30), (0.86, 0.41)), 0.045, 0.03)])
    glow(c, foam, (220, 245, 255), 8, 1.2)
    fill(c, foam, (250, 254, 255))
    spray = shape(lambda d: [d.ellipse(box(x, y, r), fill=255) for x, y, r in (
        (0.92, 0.50, 0.022), (0.80, 0.56, 0.016), (0.95, 0.60, 0.014), (0.86, 0.64, 0.012), (0.76, 0.12, 0.016),
        (0.88, 0.14, 0.012), (0.70, 0.08, 0.010))])
    glow(c, spray, (200, 240, 255), 6, 1.3)
    fill(c, spray, (240, 250, 255))
    return K.finish(c)


ICONS_ELEM = {}
for _el, _base, _ra, _ga, _ja in (('fire', None, 'Fira', 'Firaga', 'Firaja'),
                                  ('ice', None, 'Blizzara', 'Blizzaga', 'Blizzaja'),
                                  ('wind', 'Aero', 'Aera', 'Aeroga', 'Aeroja'),
                                  ('earth', None, 'Stonera', 'Stonega', 'Stoneja'),
                                  ('thunder', None, 'Thundara', 'Thundaga', 'Thundaja'),
                                  ('water', 'Water', 'Watera', 'Waterga', 'Waterja')):
    ICONS_ELEM[('ma', _ra)] = ra(_el)
    ICONS_ELEM[('ma', _ga)] = ga(_el)
    ICONS_ELEM[('ma', _ja)] = ja(_el)

ICONS = {
    ('ma', 'Aero'): aero,
    ('ma', 'Water'): water,
}
ICONS.update(ICONS_ELEM)
ICONS.update({
    ('ma', 'Flare'): flare,
    ('ma', 'Freeze'): freeze,
    ('ma', 'Tornado'): tornado,
    ('ma', 'Burst'): burst,
    ('ma', 'Flood'): flood,
})
COVERS = {}
VARIANTS = {}


# ---- small motifs shared by an enfeeble and its -ga ---------------------------------------------------------------
def disc(cx, cy, rx, ry=None):
    return shape(lambda d: d.ellipse(box(cx, cy, rx, ry), fill=255))


def m_gravity(c, cx, cy, s, chevrons=True):
    r = 0.22 * s
    rings = shape(lambda d: [d.ellipse(box(cx, cy + 0.28 * s, rr * s, rr * s * 0.26), outline=255,
                                       width=max(2, int(0.02 * W * s))) for rr in (0.22, 0.34)])
    glow(c, rings, (200, 130, 255), 8 * s, 1.5)
    fill(c, rings, (235, 215, 255))
    if chevrons:
        def chev(d, x, y):
            q = 0.075 * s
            d.polygon(pts([(x - q, y), (x, y + q * 0.8), (x + q, y), (x + q, y + q * 0.62), (x, y + q * 1.45),
                           (x - q, y + q * 0.62)]), fill=255)
        ch = shape(lambda d: [chev(d, x, y) for x in (cx - 0.35 * s, cx + 0.35 * s)
                              for y in (cy - 0.24 * s, cy - 0.06 * s)])
        sh(c, ch, 3 * s, 5 * s, 4 * s, 150)
        glow(c, ch, (210, 150, 255), 8 * s, 1.4)
        fill(c, ch, vgrad((255, 245, 255), (200, 160, 255), cy - 0.24 * s, cy + 0.06 * s))
    orb = disc(cx, cy - 0.02 * s, r)
    sh(c, orb, 5 * s, 9 * s, 8 * s, 190)
    glow(c, orb, (190, 110, 255), 24 * s, 1.9)
    fill(c, orb, rgrad((215, 170, 255), (20, 0, 40), cx - 0.35 * r, cy - 0.45 * r, r * 1.6))
    core = disc(cx, cy - 0.02 * s, r * 0.45)
    fill(c, sc(blur(core, 6 * s + 1), 0.8), (12, 0, 24), 0)
    rim = shape(lambda d: d.arc(box(cx, cy - 0.02 * s, r * 0.84), 190, 260, fill=255, width=max(2, int(0.025 * W * s))))
    fill(c, sc(rim, 0.9), (245, 230, 255), 2)


def m_venom(c, cx, cy, s):
    r = 0.15 * s
    m = shape(lambda d: GB_drop(d, cx, cy + 0.05 * s, r))
    sh(c, m, 4 * s, 6 * s, 6 * s, 160)
    glow(c, m, (140, 255, 80), 16 * s, 1.4)
    fill(c, m, vgrad((220, 255, 140), (40, 140, 30), cy - 0.32 * s, cy + 0.2 * s))
    hi = disc(cx - 0.05 * s, cy + 0.02 * s, 0.03 * s, 0.05 * s)
    fill(c, sc(hi, 0.9), (255, 255, 240), 2 * s + 1)


def GB_drop(d, x, y, r):
    """A teardrop, point up, its round belly centred on (x, y)."""
    d.ellipse(box(x, y, r), fill=255)
    d.polygon(pts([(x - r * 0.95, y - r * 0.3), (x, y - r * 2.4), (x + r * 0.95, y - r * 0.3)]), fill=255)


def eye_lens(cx, cy, rx, ry):
    """An almond eye shape: the overlap of two big circles."""
    R = (rx * rx + ry * ry) / (2 * ry)
    a = shape(lambda d: d.ellipse(box(cx, cy - ry + R, R), fill=255))
    b = shape(lambda d: d.ellipse(box(cx, cy + ry - R, R), fill=255))
    return ImageChops.multiply(a, b)


def m_blind(c, cx, cy, s):
    lens = eye_lens(cx, cy, 0.30 * s, 0.17 * s)
    sh(c, lens, 4 * s, 6 * s, 6 * s, 150)
    glow(c, lens, (200, 200, 255), 12 * s, 1.0)
    fill(c, lens, vgrad((255, 255, 255), (190, 196, 220), cy - 0.17 * s, cy + 0.17 * s))
    iris = ImageChops.multiply(disc(cx, cy, 0.12 * s), lens)
    fill(c, iris, rgrad((130, 180, 255), (20, 50, 130), cx, cy, 0.12 * s))
    fill(c, ImageChops.multiply(disc(cx, cy, 0.055 * s), lens), (6, 6, 16))
    fill(c, disc(cx - 0.04 * s, cy - 0.04 * s, 0.025 * s), (255, 255, 255))
    band = shape(lambda d: d.polygon(pts([(cx - 0.44 * s, cy - 0.02 * s), (cx + 0.40 * s, cy - 0.22 * s),
                                          (cx + 0.44 * s, cy - 0.06 * s), (cx - 0.40 * s, cy + 0.14 * s)]), fill=255))
    sh(c, band, 4 * s, 7 * s, 6 * s, 200)
    fill(c, band, vgrad((70, 56, 84), (22, 16, 30), cy - 0.2 * s, cy + 0.12 * s))
    edge = shape(lambda d: d.line(pts([(cx - 0.43 * s, cy - 0.005 * s), (cx + 0.41 * s, cy - 0.205 * s)]), fill=255,
                                  width=max(2, int(0.014 * W * s))))
    fill(c, sc(edge, 0.7), (150, 130, 170))


def m_bust(c, cx, cy, s):
    """A stone bust, cracked: (cx, cy) the middle of the figure."""
    m = shape(lambda d: GD.bust(d, cx, cy + 0.05 * s, 1.5 * s))
    sh(c, m, 5 * s, 8 * s, 8 * s, 200)
    glow(c, m, (220, 210, 170), 10 * s, 0.9)
    fill(c, m, vgrad((226, 220, 206), (110, 104, 96), cy - 0.36 * s, cy + 0.38 * s))
    lit_ = shape(lambda d: d.polygon(pts([(cx - 0.5 * s, cy - 0.5 * s), (cx + 0.02 * s, cy - 0.5 * s),
                                          (cx - 0.5 * s, cy + 0.5 * s)]), fill=255))
    fill(c, sc(ImageChops.multiply(lit_, m), 0.35), (255, 252, 240))
    cr = shape(lambda d: [d.line(pts(seq), fill=255, width=max(2, int(0.012 * W * s)), joint='curve') for seq in (
        [(cx + 0.02 * s, cy - 0.34 * s), (cx - 0.03 * s, cy - 0.24 * s), (cx + 0.03 * s, cy - 0.16 * s)],
        [(cx - 0.20 * s, cy + 0.20 * s), (cx - 0.10 * s, cy + 0.27 * s), (cx - 0.13 * s, cy + 0.36 * s)],
        [(cx + 0.14 * s, cy + 0.14 * s), (cx + 0.22 * s, cy + 0.24 * s), (cx + 0.30 * s, cy + 0.26 * s)])])
    fill(c, sc(ImageChops.multiply(cr, m), 0.85), (60, 52, 46), 1)


def boot(d, cx, cy, s):
    """A boot in profile, toe to the right; (cx, cy) its middle."""
    q = [(-0.12, -0.30), (0.07, -0.30), (0.08, 0.02), (0.14, 0.07), (0.27, 0.11), (0.31, 0.17), (0.31, 0.25),
         (-0.15, 0.25), (-0.15, 0.12), (-0.13, 0.0)]
    d.polygon([p(cx + x * s, cy + y * s) for x, y in q], fill=255)


def m_shackle(c, cx, cy, s, chain=True):
    """A boot clamped at the ankle by a frosted iron shackle, chained down."""
    metal = vgrad((245, 250, 255), (100, 116, 140), cy - 0.16 * s, cy + 0.04 * s)
    rx, ry, ay = 0.15 * s, 0.055 * s, cy - 0.10 * s
    ax = cx - 0.025 * s
    wd = max(3, int(0.042 * W * s))
    back = shape(lambda d: d.arc(box(ax, ay, rx, ry), 180, 360, fill=255, width=wd))
    fill(c, back, (70, 80, 100))
    b = shape(lambda d: boot(d, cx, cy, s))
    sh(c, b, 4 * s, 7 * s, 7 * s, 190)
    fill(c, b, vgrad((150, 100, 70), (60, 34, 24), cy - 0.3 * s, cy + 0.25 * s))
    sole = shape(lambda d: d.rectangle(pts([(cx - 0.15 * s, cy + 0.20 * s), (cx + 0.31 * s, cy + 0.25 * s)]), fill=255))
    fill(c, ImageChops.multiply(sole, b), (40, 24, 18))
    frost = ImageChops.multiply(b, vgrad((255, 255, 255), (0, 0, 0), cy - 0.3 * s, cy + 0.1 * s).convert('L'))
    fill(c, sc(frost, 0.45), (200, 235, 255))
    if chain:
        links = shape(lambda d: [d.ellipse(box(x, y, 0.045 * s, 0.03 * s), outline=255, width=max(2, int(0.02 * W * s)))
                                 for x, y in ((ax - 0.20 * s, ay + 0.05 * s), (ax - 0.27 * s, ay + 0.15 * s),
                                              (ax - 0.32 * s, ay + 0.26 * s))])
        sh(c, links, 3 * s, 4 * s, 4 * s, 170)
        fill(c, links, metal)
    front = shape(lambda d: d.arc(box(ax, ay, rx, ry), 0, 180, fill=255, width=wd))
    glow(c, ImageChops.lighter(front, back), (140, 220, 255), 14 * s, 1.6)
    sh(c, front, 3 * s, 5 * s, 4 * s, 170)
    fill(c, front, metal)
    hi = shape(lambda d: d.arc(box(ax, ay + 0.01 * s, rx * 0.9, ry * 0.7), 40, 140, fill=255,
                               width=max(2, int(0.012 * W * s))))
    fill(c, sc(hi, 0.9), (255, 255, 255), 1)


def m_cracked_ring(c, cx, cy, s):
    """A rune circle split by a crack, its two halves knocked apart."""
    def ring(d):
        d.ellipse(box(cx, cy, 0.30 * s), outline=255, width=max(3, int(0.04 * W * s)))
        d.ellipse(box(cx, cy, 0.21 * s), outline=255, width=max(2, int(0.016 * W * s)))
        for i in range(6):
            a = math.pi * 2 * i / 6 + 0.3
            x, y = cx + math.cos(a) * 0.255 * s, cy + math.sin(a) * 0.255 * s
            d.polygon(pts([(x, y - 0.03 * s), (x + 0.02 * s, y), (x, y + 0.03 * s), (x - 0.02 * s, y)]), fill=255)
        d.polygon(pts(star(cx, cy, 4, 0.13 * s, 0.04 * s)), fill=255)
    m = shape(ring)
    crack = [(cx + 0.06 * s, cy - 0.45 * s), (cx - 0.04 * s, cy - 0.16 * s), (cx + 0.05 * s, cy - 0.02 * s),
             (cx - 0.05 * s, cy + 0.14 * s), (cx + 0.03 * s, cy + 0.45 * s)]
    left = shape(lambda d: d.polygon(pts([(cx - 0.6 * s, cy - 0.6 * s)] + crack + [(cx - 0.6 * s, cy + 0.6 * s)]),
                                     fill=255))
    gap = shape(lambda d: d.line(pts(crack), fill=255, width=max(3, int(0.05 * W * s))))
    m = ImageChops.subtract(m, gap)
    lm = ImageChops.multiply(m, left)
    rm = ImageChops.subtract(m, left)
    lm = lm.rotate(8, resample=Image.BICUBIC, center=p(cx, cy + 0.3 * s))
    rm = ImageChops.offset(rm, int(0.03 * s * W), int(-0.02 * s * W))
    both = ImageChops.lighter(lm, rm)
    glow(c, both, (120, 255, 230), 14 * s, 1.5)
    fill(c, both, (230, 255, 250))
    fl = shape(lambda d: d.line(pts(crack), fill=255, width=max(2, int(0.012 * W * s))))
    glow(c, fl, (255, 255, 255), 8 * s, 1.4)
    shards = shape(lambda d: [d.polygon(pts([(cx + x * s, cy + y * s), (cx + (x + a) * s, cy + (y - 0.02) * s),
                                             (cx + (x + 0.01) * s, cy + (y + 0.04) * s)]), fill=255)
                              for x, y, a in ((0.10, -0.40, 0.05), (-0.12, -0.36, -0.05), (0.14, 0.30, 0.04),
                                              (-0.16, 0.38, -0.04))])
    fill(c, shards, (200, 255, 245))


def m_moon(c, cx, cy, s):
    d0 = disc(cx - 0.02 * s, cy, 0.24 * s)
    bite = disc(cx + 0.08 * s, cy - 0.08 * s, 0.21 * s)
    moon = ImageChops.subtract(d0, bite)
    glow(c, moon, (255, 230, 150), 20 * s, 1.4)
    fill(c, moon, vgrad((255, 250, 220), (240, 200, 110), cy - 0.24 * s, cy + 0.24 * s))

    def z(d, x, y, q):
        t = 0.2 * q
        d.polygon(pts([(x, y), (x + q, y), (x + q, y + t), (x + t * 1.3, y + q - t), (x + q, y + q - t), (x + q, y + q),
                       (x, y + q), (x, y + q - t), (x + q - t * 1.3, y + t), (x, y + t)]), fill=255)
    zs = shape(lambda d: [z(d, cx + 0.10 * s, cy - 0.04 * s, 0.15 * s), z(d, cx + 0.22 * s, cy - 0.22 * s, 0.10 * s)])
    sh(c, zs, 3 * s, 4 * s, 4 * s, 150)
    fill(c, zs, (240, 244, 255))


# ---- enfeebles --------------------------------------------------------------------------------------------------------
def gravity():
    """A crushing dark orb pressing the ground into rings, the air heavy with falling chevrons."""
    c = bg((110, 60, 170), (10, 4, 24), cy=0.42)
    m_gravity(c, 0.5, 0.42, 1.0)
    return K.finish(c)


def graviga():
    c = bg((110, 60, 170), (10, 4, 24), cy=0.5)
    trio(c, lambda c, x, y, s: m_gravity(c, x, y, s, False), 0.78, 0.56, 0.38, 0.62, 0.25)
    return K.finish(c)


def poison():
    """Twin fangs dripping green venom."""
    c = bg((120, 44, 150), (16, 4, 24), cy=0.42)
    motes(c, 61, 12, (0.15, 0.5, 0.85, 0.9), (0.012, 0.026), (140, 255, 80), (190, 255, 140))

    def fang(d, x0, sg):
        right = bez3((x0 + 0.085, 0.06), (x0 + 0.085, 0.24), (x0 + 0.03 * sg + 0.02, 0.38), (x0 + 0.02 * sg, 0.50))
        left = bez3((x0 + 0.02 * sg, 0.50), (x0 - 0.04 + 0.02 * sg, 0.36), (x0 - 0.085, 0.22), (x0 - 0.085, 0.06))
        d.polygon(pts(right + left), fill=255)
    fangs = shape(lambda d: [fang(d, 0.32, 1), fang(d, 0.68, -1)])
    sh(c, fangs, 4, 7, 6, 190)
    glow(c, fangs, (230, 255, 200), 10, 0.8)
    fill(c, fangs, vgrad((255, 255, 245), (200, 190, 160), 0.06, 0.50))
    sheen = shape(lambda d: [d.line(pts([(x, 0.10), (x + dx, 0.36)]), fill=255, width=int(0.014 * W))
                             for x, dx in ((0.28, 0.02), (0.64, 0.0))])
    fill(c, sc(sheen, 0.8), (255, 255, 255), 2)
    drips = shape(lambda d: [GB_drop(d, x, 0.57, 0.022) for x in (0.34, 0.66)])
    glow(c, drips, (140, 255, 80), 6, 1.3)
    fill(c, drips, (200, 255, 130))
    m_venom(c, 0.5, 0.74, 0.86)
    return K.finish(c)


def poisonga():
    c = bg((120, 44, 150), (16, 4, 24), cy=0.55)
    fog = dots(62, 12, 0.1, 0.9, 0.62, 0.9, 0.06, 0.12)
    fill(c, sc(blur(fog, 16), 0.5), (120, 220, 80), 0)
    motes(c, 63, 14, (0.1, 0.12, 0.9, 0.9), (0.010, 0.022), (140, 255, 80), (190, 255, 140))
    trio(c, m_venom, 1.15, 0.88, 0.48, 0.66, 0.24)
    return K.finish(c)


def bio():
    """A rotting black-green spore oozing miasma: Dia's dark twin."""
    c = bg((84, 104, 34), (8, 12, 4), cy=0.42)
    wisps = shape(lambda d: [stroke(d, bez3((x, 0.62), (x - 0.12, 0.44), (x + 0.12, 0.30), (x - 0.02, 0.10)), 0.05, 0.01)
                             for x in (0.28, 0.5, 0.72)])
    fill(c, sc(blur(wisps, 6), 0.55), (170, 230, 90), 0)
    ooze = shape(lambda d: [GB_drop(d, x, y, r) for x, y, r in ((0.40, 0.76, 0.035), (0.58, 0.82, 0.045),
                                                                (0.70, 0.70, 0.028))] +
                 [d.polygon(pts([(x - r * 0.9, 0.58), (x + r * 0.9, 0.58), (x, y)]), fill=255)
                  for x, y, r in ((0.40, 0.76, 0.035), (0.58, 0.82, 0.045), (0.70, 0.70, 0.028))])
    orb = disc(0.5, 0.46, 0.26)
    m = ImageChops.lighter(orb, ooze)
    sh(c, m, 5, 8, 8, 190)
    glow(c, m, (150, 230, 60), 22, 1.4)
    fill(c, m, rgrad((120, 150, 50), (14, 24, 6), 0.42, 0.38, 0.40))
    spots = shape(lambda d: [d.ellipse(box(x, y, r), fill=255) for x, y, r in (
        (0.40, 0.40, 0.05), (0.60, 0.36, 0.035), (0.58, 0.56, 0.055), (0.38, 0.58, 0.03), (0.50, 0.47, 0.025))])
    glow(c, spots, (190, 255, 90), 6, 1.4)
    fill(c, ImageChops.multiply(spots, orb), rgrad((230, 255, 140), (110, 190, 40), 0.5, 0.48, 0.2))
    hi = shape(lambda d: d.arc(box(0.5, 0.46, 0.22), 200, 260, fill=255, width=int(0.02 * W)))
    fill(c, sc(hi, 0.6), (220, 255, 180), 2)
    return K.finish(c)


def virus():
    """A sickly spiked germ, smaller spores drifting off it."""
    c = bg((130, 40, 60), (18, 4, 10), cy=0.45)

    def germ(cx, cy, r, n, rot=0.0):
        def dr(d):
            for i in range(n):
                a = math.pi * 2 * i / n + rot
                ux, uy = math.cos(a), math.sin(a)
                d.line(pts([(cx, cy), (cx + ux * r * 1.55, cy + uy * r * 1.55)]), fill=255,
                       width=max(2, int(0.06 * r * W)))
                d.ellipse(box(cx + ux * r * 1.6, cy + uy * r * 1.6, r * 0.2), fill=255)
            d.ellipse(box(cx, cy, r), fill=255)
        m = shape(dr)
        sh(c, m, 4, 6, 6, 170)
        glow(c, m, (220, 255, 80), 14 * r / 0.2, 1.3)
        fill(c, m, rgrad((250, 255, 170), (120, 170, 20), cx - r * 0.3, cy - r * 0.35, r * 1.8))
        bl = shape(lambda d: [d.ellipse(box(cx + dx * r, cy + dy * r, rr * r), fill=255)
                              for dx, dy, rr in ((-0.35, 0.10, 0.22), (0.30, -0.25, 0.16), (0.20, 0.40, 0.14))])
        fill(c, sc(bl, 0.6), (90, 130, 10))
    germ(0.80, 0.24, 0.06, 7, 0.3)
    germ(0.20, 0.78, 0.05, 7, 0.1)
    germ(0.47, 0.52, 0.20, 11)
    return K.finish(c)


def curse():
    """A hollow-eyed wraith wreathed in violet hexfire."""
    c = bg((90, 40, 120), (10, 2, 16), cy=0.42)
    fl = shape(lambda d: [GA.flame(d, x, 0.92, w, h, l) for x, w, h, l in
                          ((0.5, 0.36, 0.86, 0.0), (0.24, 0.14, 0.5, -0.06), (0.76, 0.14, 0.5, 0.06))])
    glow(c, fl, (190, 80, 255), 20, 1.0)
    fill(c, sc(fl, 0.55), vgrad((210, 140, 255), (90, 20, 140), 0.1, 0.9))

    def ghost(d):
        d.ellipse(box(0.5, 0.40, 0.21, 0.22), fill=255)
        q = [(0.29, 0.40)]
        for i in range(31):
            t = i / 30
            x = 0.29 + 0.42 * t
            y = 0.78 + 0.05 * math.sin(t * math.pi * 3.0) + 0.04 * t
            q.append((x, y))
        q.append((0.71, 0.40))
        d.polygon(pts(q), fill=255)
        d.polygon(pts([(0.30, 0.48), (0.16, 0.62), (0.22, 0.66), (0.33, 0.56)]), fill=255)
        d.polygon(pts([(0.70, 0.48), (0.84, 0.62), (0.78, 0.66), (0.67, 0.56)]), fill=255)
    g = shape(ghost)
    glow(c, g, (220, 170, 255), 18, 1.4)
    fill(c, g, vgrad((250, 240, 255), (170, 120, 220), 0.2, 0.86))
    face = shape(lambda d: [d.ellipse(box(0.42, 0.40, 0.045, 0.065), fill=255),
                            d.ellipse(box(0.58, 0.40, 0.045, 0.065), fill=255),
                            d.ellipse(box(0.5, 0.55, 0.04, 0.055), fill=255)])
    fill(c, face, (30, 6, 46))
    pupils = shape(lambda d: [d.ellipse(box(x, 0.41, 0.014), fill=255) for x in (0.42, 0.58)])
    glow(c, pupils, (255, 80, 200), 5, 1.6)
    fill(c, pupils, (255, 160, 230))
    return K.finish(c)


def blind():
    """An eye bound by a dark blindfold, smoke curling round it."""
    c = bg((90, 92, 120), (8, 8, 16), cy=0.45)
    smoke = dots(71, 12, 0.08, 0.92, 0.12, 0.9, 0.06, 0.12)
    fill(c, sc(blur(smoke, 18), 0.6), (20, 18, 30), 0)
    m_blind(c, 0.5, 0.5, 1.15)
    return K.finish(c)


def blindga():
    """Blind for an area: one large blindfolded eye, two plain blindfolded eye-shapes below it."""
    c = bg((90, 92, 120), (8, 8, 16), cy=0.5)
    for x in (0.25, 0.75):
        lens = eye_lens(x, 0.77, 0.15, 0.085)
        band = shape(lambda d, x=x: d.polygon(pts([(x - 0.19, 0.78), (x + 0.18, 0.69), (x + 0.19, 0.75),
                                                   (x - 0.18, 0.84)]), fill=255))
        glow(c, lens, (190, 190, 255), 10, 1.2)
        fill(c, ImageChops.subtract(lens, band), (220, 224, 245))
        fill(c, band, (40, 32, 52))
    m_blind(c, 0.5, 0.40, 0.95)
    return K.finish(c)


def break_():
    """A figure turned to cracked stone, flakes of rock crumbling away."""
    c = bg((150, 170, 110), (14, 20, 8), cy=0.42)
    gaze = disc(0.5, 0.44, 0.34)
    fill(c, sc(blur(gaze, 22), 0.45), (190, 255, 150), 0)
    m_bust(c, 0.5, 0.5, 1.0)
    crumbs = shape(lambda d: [d.polygon(pts([(x, y), (x + .03, y + .01), (x + .01, y + .03)]), fill=255)
                              for x, y in ((0.20, 0.70), (0.80, 0.66), (0.26, 0.84), (0.74, 0.82), (0.68, 0.30))])
    fill(c, crumbs, (170, 164, 150))
    return K.finish(c)


def breakga():
    c = bg((150, 170, 110), (14, 20, 8), cy=0.5)
    trio(c, m_bust, 0.80, 0.60, 0.42, 0.64, 0.25)
    return K.finish(c)


def bind():
    """A boot clamped to the ground by a frost-rimed shackle on a binding sigil."""
    c = bg((70, 130, 170), (6, 14, 26), cy=0.45)
    sig = shape(lambda d: [d.ellipse(box(0.5, 0.80, 0.36, 0.10), outline=255, width=int(0.02 * W)),
                           d.ellipse(box(0.5, 0.80, 0.24, 0.065), outline=255, width=int(0.012 * W))])
    glow(c, sig, (120, 220, 255), 10, 1.6)
    fill(c, sig, (220, 245, 255))
    m_shackle(c, 0.52, 0.52, 1.1)
    motes(c, 72, 12, (0.15, 0.1, 0.85, 0.6), (0.005, 0.011), (180, 230, 255), (240, 250, 255))
    sparkles(c, [(0.74, 0.30, 0.06)], (180, 230, 255))
    return K.finish(c)


def bindga():
    c = bg((70, 130, 170), (6, 14, 26), cy=0.5)
    trio(c, lambda c, x, y, s: m_shackle(c, x, y, s, False), 0.90, 0.68, 0.40, 0.66, 0.24)
    return K.finish(c)


def dispel():
    """A rune circle shattering, its magic spilling out."""
    c = bg((40, 110, 120), (4, 10, 16), cy=0.45)
    m_cracked_ring(c, 0.5, 0.5, 1.1)
    return K.finish(c)


def dispelga():
    """Dispel for an area: one large shattering rune circle, two plain broken rings below it."""
    c = bg((40, 110, 120), (4, 10, 16), cy=0.5)
    for x in (0.24, 0.76):
        ring = shape(lambda d, x=x: d.ellipse(box(x, 0.75, 0.105), outline=255, width=int(0.05 * W)))
        gap = shape(lambda d, x=x: d.line(pts([(x + 0.03, 0.62), (x - 0.02, 0.75), (x + 0.02, 0.88)]), fill=255,
                                          width=int(0.045 * W)))
        r = ImageChops.subtract(ring, gap)
        glow(c, r, (120, 255, 230), 10, 1.4)
        fill(c, r, (220, 255, 248))
    m_cracked_ring(c, 0.5, 0.39, 0.86)
    return K.finish(c)


def sleepga():
    c = bg((40, 54, 120), (4, 6, 22), cy=0.5)
    motes(c, 41, 18, (0.1, 0.1, 0.9, 0.9), (0.004, 0.009), (200, 210, 255), (240, 240, 255))
    trio(c, m_moon, 0.92, 0.70, 0.40, 0.64, 0.25)
    return K.finish(c)


def stun():
    """A crackling electric burst with stars reeling round it."""
    c = bg((170, 120, 30), (26, 14, 4), cy=0.5)
    rays(c, 0.5, 0.58, 12, 0.6, (255, 240, 180), 80, 0.06, 8)
    b = shape(lambda d: d.polygon(pts(jagged_star(0.5, 0.58, 9, 0.34, 0.16, 5, 0.22)), fill=255))
    sh(c, b, 5, 8, 8, 170)
    glow(c, b, (255, 220, 80), 20, 1.4)
    fill(c, b, rgrad((255, 255, 240), (255, 170, 30), 0.5, 0.58, 0.34))
    zig = shape(lambda d: stroke(d, [(0.36, 0.50), (0.50, 0.60), (0.46, 0.66), (0.62, 0.74)], 0.04, 0.018))
    fill(c, zig, (150, 70, 200))
    orbit = shape(lambda d: d.ellipse(box(0.5, 0.24, 0.30, 0.085), outline=255, width=int(0.012 * W)))
    fill(c, sc(orbit, 0.7), (255, 250, 220))
    st = shape(lambda d: [d.polygon(pts(star(x, y, 5, r, r * 0.45)), fill=255)
                          for x, y, r in ((0.22, 0.24, 0.06), (0.62, 0.17, 0.05), (0.76, 0.31, 0.065))])
    sh(c, st, 3, 4, 4, 150)
    glow(c, st, (255, 255, 180), 8, 1.4)
    fill(c, st, (255, 252, 210))
    return K.finish(c)


def distract():
    """A dizzying spiral: the target's footwork thrown off (evasion down)."""
    c = bg((200, 110, 40), (30, 12, 4), cy=0.45)
    sp = mask()
    d = ImageDraw.Draw(sp)
    path = []
    for i in range(120):
        t = i / 119
        a = t * math.pi * 5.0
        r = 0.03 + 0.31 * t
        path.append((0.46 + math.cos(a) * r, 0.46 + math.sin(a) * r))
    stroke(d, path, 0.02, 0.06)
    sh(c, sp, 4, 6, 6, 160)
    glow(c, sp, (255, 210, 120), 12, 1.3)
    fill(c, sp, rgrad((255, 255, 240), (255, 170, 70), 0.46, 0.46, 0.36))
    down_badge(c, 0.76, 0.74, 1.0)
    return K.finish(c)


def frazzle():
    """A ward of magic fraying apart into sparks (magic evasion down)."""
    c = bg((130, 60, 170), (14, 4, 24), cy=0.45)
    dome = shape(lambda d: [d.arc(box(0.46, 0.50, 0.32), a, a + 40, fill=255, width=int(0.04 * W))
                            for a in (190, 245, 300, 355)])
    sh(c, dome, 4, 6, 6, 160)
    glow(c, dome, (220, 140, 255), 14, 1.5)
    fill(c, dome, (250, 230, 255))
    frays = shape(lambda d: [stroke(d, [(0.46 + math.cos(math.radians(a)) * 0.32, 0.50 + math.sin(math.radians(a)) * 0.32),
                                        (0.46 + math.cos(math.radians(a + 6)) * 0.40,
                                         0.50 + math.sin(math.radians(a + 6)) * 0.40)], 0.018, 0.004)
                             for a in (232, 238, 288, 293, 342, 348, 30, 36)])
    glow(c, frays, (230, 160, 255), 6, 1.4)
    fill(c, frays, (255, 240, 255))
    rune = shape(lambda d: d.polygon(pts(star(0.46, 0.50, 6, 0.15, 0.07)), fill=255))
    glow(c, rune, (200, 120, 255), 12, 1.3)
    fill(c, sc(rune, 0.9), (240, 220, 255))
    sparkles(c, [(0.20, 0.24, 0.05), (0.70, 0.16, 0.045), (0.16, 0.70, 0.04)], (220, 160, 255))
    down_badge(c, 0.76, 0.74, 1.0)
    return K.finish(c)


# ---- showpieces -------------------------------------------------------------------------------------------------------
def night(c, seed, n=26):
    motes(c, seed, n, (0.06, 0.06, 0.94, 0.94), (0.003, 0.008), (220, 220, 255), (250, 250, 255))


def meteor():
    """Burning stones falling out of a night sky."""
    c = bg((70, 36, 120), (6, 2, 18), cx=0.3, cy=0.3, r=0.8)
    night(c, 81)
    ang = math.radians(40)
    ux, uy = math.cos(ang), math.sin(ang)

    def rock(cx, cy, r, trail, seed):
        tail = mask()
        td = ImageDraw.Draw(tail)
        for i in range(40):
            t = i / 39
            rr = r * (1.05 - 0.9 * t)
            td.ellipse(box(cx - ux * trail * t, cy - uy * trail * t, rr), fill=255)
        tail = blur(tail, 5 * r / 0.14 + 1)
        glow(c, tail, (255, 80, 20), 14 * r / 0.14, 1.3)
        fill(c, tail, rgrad((255, 240, 170), (210, 40, 10), cx, cy, trail * 0.9), 0)
        aura = disc(cx, cy, r * 1.22)
        glow(c, aura, (255, 200, 90), 12 * r / 0.14, 1.6)
        fill(c, aura, rgrad((255, 255, 230), (255, 150, 40), cx + ux * r * 0.3, cy + uy * r * 0.3, r * 1.4), 3)
        rk = shape(lambda d: d.polygon(pts(jagged_star(cx - ux * r * 0.12, cy - uy * r * 0.12, 6, r, r * 0.86,
                                                       seed, 0.14)), fill=255))
        fill(c, rk, rgrad((110, 60, 44), (34, 16, 14), cx - ux * r * 0.4, cy - uy * r * 0.4, r * 1.3))
        cr = shape(lambda d: d.line(pts([(cx - r * 0.45, cy - r * 0.05), (cx - r * 0.05, cy + r * 0.12),
                                         (cx + r * 0.15, cy - r * 0.32)]), fill=255, width=max(2, int(r * 0.13 * W))))
        glow(c, ImageChops.multiply(cr, rk), (255, 120, 30), 4, 1.3)
        fill(c, ImageChops.multiply(cr, rk), (255, 190, 80), 1)
    rock(0.78, 0.26, 0.065, 0.26, 2)
    rock(0.26, 0.74, 0.075, 0.30, 3)
    rock(0.60, 0.62, 0.15, 0.60, 1)
    return K.finish(c)


def comet():
    """A single violet star of darkness falling, its long tail behind it."""
    c = bg((90, 30, 120), (6, 2, 14), cx=0.65, cy=0.35, r=0.8)
    night(c, 82, 20)
    hx, hy = 0.36, 0.64
    tail = shape(lambda d: d.polygon(pts([(hx - 0.09, hy - 0.05), (0.98, 0.02), (hx + 0.06, hy + 0.09)]), fill=255))
    glow(c, tail, (190, 90, 255), 18, 1.2)
    fill(c, sc(blur(tail, 8), 0.8), (200, 140, 255), 0)
    streaks = shape(lambda d: [stroke(d, [(hx + dx, hy + dy), (0.92 + dx * 0.5, 0.10 + dy * 2)], 0.03, 0.004)
                               for dx, dy in ((0.0, 0.0), (-0.03, -0.04), (0.04, 0.03))])
    fill(c, sc(streaks, 0.85), (250, 235, 255))
    halo = disc(hx, hy, 0.16)
    fill(c, sc(blur(halo, 16), 0.9), (170, 80, 255), 0)
    head = shape(lambda d: d.polygon(pts(star(hx, hy, 4, 0.18, 0.05, -math.pi / 2 + 0.2)), fill=255))
    glow(c, head, (220, 160, 255), 14, 1.5)
    fill(c, head, (250, 240, 255))
    core = disc(hx, hy, 0.075)
    glow(c, core, (255, 255, 255), 16, 1.6)
    fill(c, core, rgrad((255, 255, 255), (200, 150, 255), hx, hy, 0.075))
    return K.finish(c)


def death():
    """A reaper's scythe raised against a blood-red moon."""
    c = bg((110, 10, 30), (8, 0, 4), cy=0.4)
    moon = disc(0.60, 0.44, 0.25)
    glow(c, moon, (255, 50, 50), 28, 1.2)
    fill(c, moon, rgrad((220, 70, 60), (100, 8, 20), 0.54, 0.36, 0.32))
    craters = shape(lambda d: [d.ellipse(box(x, y, r), fill=255) for x, y, r in
                               ((0.52, 0.36, 0.04), (0.70, 0.50, 0.05), (0.66, 0.30, 0.025), (0.56, 0.58, 0.03))])
    fill(c, sc(ImageChops.multiply(craters, moon), 0.45), (80, 4, 12))
    pole = shape(lambda d: stroke(d, bez((0.26, 0.92), (0.44, 0.56), (0.64, 0.20)), 0.045, 0.036))
    outer = bez3((0.64, 0.20), (0.52, 0.06), (0.22, 0.10), (0.12, 0.44))
    inner = bez3((0.12, 0.44), (0.24, 0.24), (0.44, 0.22), (0.62, 0.31))
    blade = shape(lambda d: d.polygon(pts(outer + inner), fill=255))
    weapon = ImageChops.lighter(pole, blade)
    sh(c, weapon, 5, 8, 8, 230)
    glow(c, blade, (255, 230, 230), 12, 1.2)
    fill(c, pole, vgrad((90, 64, 60), (24, 12, 14), 0.2, 0.92))
    fill(c, blade, vgrad((255, 255, 255), (140, 144, 162), 0.08, 0.44))
    edge = shape(lambda d: d.line(pts(inner), fill=255, width=int(0.014 * W)))
    fill(c, sc(ImageChops.multiply(edge, blade), 0.8), (80, 84, 100))
    collar = shape(lambda d: d.ellipse(box(0.63, 0.22, 0.04), fill=255))
    fill(c, collar, (60, 40, 40))
    wisps = shape(lambda d: [stroke(d, bez3((x, 0.98), (x - 0.08, 0.86), (x + 0.08, 0.78), (x, 0.66)), 0.035, 0.005)
                             for x in (0.62, 0.80, 0.44)])
    fill(c, sc(blur(wisps, 3), 0.7), (30, 0, 8), 0)
    return K.finish(c)


def impact():
    """A shattering explosion of dark force, shards hurled outward from the crater."""
    c = bg((60, 30, 110), (4, 2, 12), r=0.7)
    rings = shape(lambda d: [d.ellipse(box(0.5, 0.5, r), outline=255, width=max(2, int(w * W)))
                             for r, w in ((0.42, 0.012), (0.34, 0.02))])
    glow(c, rings, (180, 110, 255), 10, 1.5)
    fill(c, sc(rings, 0.8), (230, 210, 255))
    rays(c, 0.5, 0.5, 9, 0.7, (200, 150, 255), 90, 0.05, 6, 0.2)
    burst = shape(lambda d: d.polygon(pts(jagged_star(0.5, 0.5, 7, 0.40, 0.12, 11, 0.3)), fill=255))
    glow(c, burst, (190, 100, 255), 22, 1.5)
    fill(c, burst, rgrad((255, 250, 255), (150, 80, 240), 0.5, 0.5, 0.38))
    core = disc(0.5, 0.5, 0.12)
    sh(c, core, 0, 0, 10, 200)
    fill(c, core, rgrad((10, 0, 20), (60, 20, 100), 0.5, 0.5, 0.14))
    cr = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.12), outline=255, width=int(0.014 * W)))
    glow(c, cr, (230, 180, 255), 8, 1.4)
    fill(c, cr, (250, 240, 255))
    shards = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * r0, 0.5 + math.sin(a) * r0),
                                             (0.5 + math.cos(a + 0.12) * (r0 + 0.07), 0.5 + math.sin(a + 0.12) * (r0 + 0.07)),
                                             (0.5 + math.cos(a - 0.05) * (r0 + 0.04), 0.5 + math.sin(a - 0.05) * (r0 + 0.04))]),
                                        fill=255) for a, r0 in ((0.6, 0.30), (2.0, 0.33), (3.3, 0.30), (4.6, 0.32),
                                                                (5.6, 0.31))])
    fill(c, shards, (240, 220, 255))
    return K.finish(c)


def kaustra():
    """A black sun eclipsing, its corona of violet-crimson flame eating at the light."""
    c = bg((120, 30, 80), (8, 0, 8), r=0.7)
    cor = shape(lambda d: d.polygon(pts(jagged_star(0.5, 0.5, 18, 0.40, 0.25, 17, 0.3)), fill=255))
    glow(c, cor, (230, 60, 160), 24, 1.4)
    fill(c, cor, rgrad((255, 200, 240), (170, 30, 120), 0.5, 0.5, 0.40), 4)
    inner = disc(0.5, 0.5, 0.27)
    glow(c, inner, (255, 220, 250), 12, 1.6)
    fill(c, inner, (255, 230, 250), 3)
    sun = disc(0.5, 0.5, 0.245)
    fill(c, sun, rgrad((30, 6, 30), (0, 0, 0), 0.44, 0.44, 0.28), 2)
    sw = shape(lambda d: [d.arc(box(0.5, 0.5, r), a, a + 70, fill=255, width=int(0.012 * W))
                          for r, a in ((0.17, 30), (0.12, 200), (0.20, 250))])
    fill(c, sc(sw, 0.6), (180, 40, 120))
    motes(c, 91, 12, (0.1, 0.1, 0.9, 0.9), (0.006, 0.012), (230, 60, 160), (255, 190, 230))
    return K.finish(c)


def klimaform():
    """Sun, cloud and rain held in a scholar's circle: the weather mastered."""
    c = bg((60, 150, 180), (6, 22, 34), cy=0.45)
    ring = shape(lambda d: [d.ellipse(box(0.5, 0.5, 0.40), outline=255, width=int(0.016 * W))] +
                 [d.ellipse(box(0.5 + math.cos(a) * 0.40, 0.5 + math.sin(a) * 0.40, 0.025), fill=255)
                  for a in (math.pi * 2 * i / 8 for i in range(8))])
    glow(c, ring, (255, 220, 120), 8, 1.3)
    fill(c, ring, (255, 236, 170))
    rays(c, 0.60, 0.38, 12, 0.32, (255, 240, 170), 140, 0.08, 4)
    sun = disc(0.60, 0.38, 0.15)
    glow(c, sun, (255, 210, 80), 18, 1.5)
    fill(c, sun, rgrad((255, 255, 220), (255, 180, 40), 0.56, 0.34, 0.18))
    rain = shape(lambda d: [d.line(pts([(x, y), (x - 0.03, y + 0.08)]), fill=255, width=int(0.016 * W))
                            for x, y in ((0.32, 0.66), (0.44, 0.70), (0.56, 0.66), (0.38, 0.78))])
    fill(c, rain, (180, 230, 255))
    cl = shape(lambda d: [d.ellipse(box(x, y, rx, ry), fill=255) for x, y, rx, ry in (
        (0.30, 0.56, 0.11, 0.08), (0.42, 0.50, 0.12, 0.11), (0.55, 0.55, 0.11, 0.09), (0.42, 0.59, 0.18, 0.06))])
    sh(c, cl, 4, 7, 7, 150)
    fill(c, cl, vgrad((255, 255, 255), (180, 205, 225), 0.40, 0.65))
    return K.finish(c)


def endark():
    """A black blade wreathed in violet shadow-flame."""
    c = bg((90, 40, 130), (10, 2, 18), cy=0.5)
    fl = shape(lambda d: [GA.flame(d, 0.5 + dx, 0.92, w, h, l) for dx, w, h, l in
                          ((0, 0.24, 0.86, 0.0), (-0.12, 0.12, 0.6, -0.08), (0.12, 0.12, 0.62, 0.07))])
    glow(c, fl, (180, 70, 255), 22, 1.3)
    fill(c, sc(fl, 0.7), vgrad((230, 180, 255), (110, 30, 180), 0.1, 0.9))
    sw = shape(lambda d: GA.sword(d, 0.5, 0.92, 0.5, 0.08, 0.055, 0.15, 0.17))
    sh(c, sw, 5, 8, 8, 200)
    glow(c, sw, (220, 150, 255), 10, 1.4)
    fill(c, sw, vgrad((60, 40, 80), (14, 6, 22), 0.08, 0.92))
    edge = shape(lambda d: d.line(pts([(0.5, 0.11), (0.5, 0.70)]), fill=255, width=int(0.012 * W)))
    fill(c, sc(edge, 0.9), (220, 180, 255))
    motes(c, 92, 12, (0.15, 0.1, 0.85, 0.7), (0.006, 0.012), (200, 120, 255), (240, 220, 255))
    return K.finish(c)


# ---- spikes: a dark buckler ringed with elemental spikes ----------------------------------------------------------------
def spikes(kind):
    pal = {
        'blaze': ((170, 50, 16), (24, 4, 4), (255, 120, 30), (255, 230, 150), (240, 70, 20)),
        'ice': ((80, 160, 220), (4, 16, 36), (150, 220, 255), (255, 255, 255), (110, 180, 240)),
        'shock': ((80, 60, 170), (8, 6, 26), (255, 230, 100), (255, 255, 220), (250, 200, 60)),
        'dread': ((110, 10, 30), (8, 0, 4), (255, 40, 60), (120, 100, 120), (20, 10, 24)),
    }[kind]

    def paint():
        c = bg(pal[0], pal[1], cy=0.5)
        n = 10
        sp = mask()
        d = ImageDraw.Draw(sp)
        for i in range(n):
            a = math.pi * 2 * i / n - math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            nx, ny = -uy, ux
            b0, b1 = 0.22, 0.44
            if kind == 'shock':
                path = [(0.5 + ux * b0, 0.5 + uy * b0)]
                for k, off in ((0.30, 0.04), (0.36, -0.04), (0.44, 0.0)):
                    path.append((0.5 + ux * k + nx * off, 0.5 + uy * k + ny * off))
                stroke(d, path, 0.05, 0.012)
            elif kind == 'blaze':
                L = 0.46
                q = []
                for k in range(21):
                    t = k / 20
                    w = 0.06 * (1 - t) ** 0.8
                    wob = 0.03 * math.sin(t * math.pi * 1.5) * t
                    q.append((0.5 + ux * (b0 + (L - b0) * t) + nx * (w + wob), 0.5 + uy * (b0 + (L - b0) * t) + ny * (w + wob)))
                q2 = []
                for k in range(21):
                    t = k / 20
                    w = 0.06 * (1 - t) ** 0.8
                    wob = 0.03 * math.sin(t * math.pi * 1.5) * t
                    q2.append((0.5 + ux * (b0 + (L - b0) * t) - nx * (w - wob), 0.5 + uy * (b0 + (L - b0) * t) - ny * (w - wob)))
                d.polygon(pts(q + q2[::-1]), fill=255)
            elif kind == 'dread':
                q = []
                for k in range(21):
                    t = k / 20
                    bend = 0.07 * t * t
                    w = 0.055 * (1 - t)
                    cxp, cyp = 0.5 + ux * (b0 + (b1 - b0) * t) + nx * bend, 0.5 + uy * (b0 + (b1 - b0) * t) + ny * bend
                    q.append(((cxp + nx * w, cyp + ny * w), (cxp - nx * w, cyp - ny * w)))
                d.polygon(pts([a_ for a_, _ in q] + [b_ for _, b_ in q][::-1]), fill=255)
            else:
                w = 0.05
                d.polygon(pts([(0.5 + ux * b0 + nx * w, 0.5 + uy * b0 + ny * w), (0.5 + ux * b1, 0.5 + uy * b1),
                               (0.5 + ux * b0 - nx * w, 0.5 + uy * b0 - ny * w)]), fill=255)
        sh(c, sp, 4, 7, 6, 170)
        glow(c, sp, pal[2], 16, 1.5)
        fill(c, sp, rgrad(pal[3], pal[4], 0.5, 0.5, 0.46))
        if kind == 'ice':
            half = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * 0.22, 0.5 + math.sin(a) * 0.22),
                                                   (0.5 + math.cos(a) * 0.44, 0.5 + math.sin(a) * 0.44),
                                                   (0.5 + math.cos(a - 0.2) * 0.22, 0.5 + math.sin(a - 0.2) * 0.22)]),
                                              fill=255) for a in (math.pi * 2 * i / n - math.pi / 2 for i in range(n))])
            fill(c, sc(ImageChops.multiply(half, sp), 0.5), (40, 110, 190))
        boss = disc(0.5, 0.5, 0.23)
        sh(c, boss, 5, 8, 8, 200)
        glow(c, boss, pal[2], 12, 1.2)
        if kind == 'dread':
            fill(c, boss, rgrad((70, 50, 70), (10, 4, 12), 0.44, 0.42, 0.28))
        else:
            fill(c, boss, rgrad((120, 124, 140), (24, 24, 34), 0.44, 0.40, 0.28))
        rim = shape(lambda d: d.ellipse(box(0.5, 0.5, 0.21), outline=255, width=int(0.02 * W)))
        fill(c, sc(rim, 0.9), pal[3] if kind != 'dread' else (180, 40, 60))
        if kind == 'dread':
            hd = shape(lambda d: GB_drop(d, 0.5, 0.54, 0.075))
            glow(c, hd, (255, 40, 60), 12, 1.5)
            fill(c, hd, vgrad((255, 120, 120), (150, 0, 20), 0.36, 0.62))
        else:
            em = {'blaze': lambda c: m_fire(c, 0.5, 0.5, 0.36, False),
                  'ice': lambda c: m_ice(c, 0.5, 0.5, 0.40),
                  'shock': lambda c: m_thunder(c, 0.5, 0.5, 0.38, False)}[kind]
            em(c)
        return K.finish(c)
    return paint


# ---- recoloured families ---------------------------------------------------------------------------------------------
def helix():
    """Two strands of element twisting round each other: the helix that keeps burning (painted as fire)."""
    c = bg((170, 60, 20), (22, 4, 4), cy=0.5)
    n = 90

    def strand(ph):
        return [(0.5 + 0.20 * math.sin(t * math.pi * 3.2 + ph), 0.10 + 0.80 * t, math.cos(t * math.pi * 3.2 + ph))
                for t in (i / (n - 1) for i in range(n))]
    a, b = strand(0.0), strand(math.pi)
    rungs = shape(lambda d: [d.line(pts([(a[i][0], a[i][1]), (b[i][0], b[i][1])]), fill=255, width=int(0.014 * W))
                             for i in range(5, n - 5, 9)])
    fill(c, sc(rungs, 0.6), (255, 200, 120))
    for front in (False, True):
        m = mask()
        d = ImageDraw.Draw(m)
        for s in (a, b):
            for x, y, z in s:
                if (z > 0) == front:
                    r = 0.03 + 0.012 * z
                    d.ellipse(box(x, y, r), fill=255)
        if front:
            glow(c, m, (255, 140, 40), 16, 1.5)
            fill(c, m, vgrad((255, 250, 210), (255, 130, 30), 0.1, 0.9))
        else:
            fill(c, m, vgrad((200, 90, 30), (120, 30, 10), 0.1, 0.9))
    motes(c, 93, 12, (0.15, 0.1, 0.85, 0.9), (0.006, 0.012), (255, 160, 60), (255, 230, 170))
    return K.finish(c)


def dot_ail():
    """A victim caught in a ticking ring of element, eaten away over time (painted as Burn)."""
    c = bg((170, 50, 20), (22, 4, 4), cy=0.45)
    haze = disc(0.5, 0.5, 0.28)
    fill(c, sc(blur(haze, 18), 0.4), (255, 110, 30), 0)
    body = shape(lambda d: GD.bust(d, 0.5, 0.54, 1.4))
    sh(c, body, 4, 7, 7, 200)
    glow(c, body, (255, 150, 50), 10, 1.2)
    fill(c, body, vgrad((255, 236, 214), (190, 130, 100), 0.2, 0.86))
    burn = ImageChops.multiply(body, vgrad((0, 0, 0), (255, 255, 255), 0.42, 0.80).convert('L'))
    fill(c, burn, (240, 90, 20), 2)
    lick = shape(lambda d: [GA.flame(d, x, 0.84, w, h, l) for x, w, h, l in
                            ((0.36, 0.07, 0.30, -0.02), (0.5, 0.08, 0.36, 0.01), (0.64, 0.07, 0.28, 0.03))])
    fill(c, ImageChops.multiply(lick, body), vgrad((255, 250, 200), (255, 160, 40), 0.5, 0.84), 2)
    n = 8
    lit_ = mask()
    dim = mask()
    for i in range(n):
        a0 = -90 + i * 360 / n + 6
        (ImageDraw.Draw(lit_) if i < 6 else ImageDraw.Draw(dim)).arc(box(0.5, 0.5, 0.385), a0, a0 + 360 / n - 12,
                                                                     fill=255, width=int(0.06 * W))
    fill(c, dim, (90, 30, 20))
    sh(c, lit_, 3, 5, 5, 150)
    glow(c, lit_, (255, 120, 30), 12, 1.5)
    fill(c, lit_, rgrad((255, 250, 200), (255, 120, 30), 0.5, 0.2, 0.7))
    motes(c, 94, 12, (0.28, 0.14, 0.72, 0.5), (0.008, 0.016), (255, 160, 60), (255, 230, 170))
    return K.finish(c)


def absorb():
    """Streams of a stat's colour pulled in to a bright orb (painted as STR red)."""
    c = bg((60, 36, 44), (8, 4, 8), cy=0.5)
    for k in range(4):
        a0 = k * math.pi / 2 + 0.4
        path = []
        for i in range(30):
            t = i / 29
            a = a0 + t * 1.4
            r = 0.44 - 0.24 * t
            path.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
        m = shape(lambda d: stroke(d, path, 0.008, 0.05))
        tip_a = a0 + 1.4
        tx, ty = 0.5 + math.cos(tip_a) * 0.2, 0.5 + math.sin(tip_a) * 0.2
        dx, dy = -math.sin(tip_a) * 0.6 - math.cos(tip_a) * 0.8, math.cos(tip_a) * 0.6 - math.sin(tip_a) * 0.8
        L = math.hypot(dx, dy)
        dx, dy = dx / L, dy / L
        head = shape(lambda d: d.polygon(pts([(tx + dx * 0.06, ty + dy * 0.06), (tx - dy * 0.05, ty + dx * 0.05),
                                              (tx + dy * 0.05, ty - dx * 0.05)]), fill=255))
        m = ImageChops.lighter(m, head)
        glow(c, m, (255, 80, 60), 10, 1.4)
        fill(c, m, (255, 170, 140))
    orb = disc(0.5, 0.5, 0.15)
    glow(c, orb, (255, 60, 40), 24, 1.7)
    fill(c, orb, rgrad((255, 250, 230), (230, 40, 30), 0.47, 0.45, 0.17))
    motes(c, 95, 10, (0.08, 0.08, 0.92, 0.92), (0.007, 0.014), (255, 80, 60), (255, 200, 180))
    return K.finish(c)


def aspir():
    """A mana crystal bled dry: dark tendrils coil round it, its blue light streaming off."""
    c = bg((60, 30, 110), (6, 2, 16), cy=0.5)
    stream = shape(lambda d: [stroke(d, bez3((0.5, 0.5), (0.5 + ox, 0.5 + oy), (ex * 0.9, ey * 0.9), (ex, ey)), 0.04, 0.006)
                              for ox, oy, ex, ey in ((0.2, -0.25, 0.86, 0.14), (-0.25, -0.2, 0.14, 0.18),
                                                     (0.1, 0.3, 0.84, 0.86))])
    glow(c, stream, (90, 170, 255), 12, 1.4)
    fill(c, stream, (200, 230, 255))
    GD.crystal(c, 0.5, 0.48, 0.15, 0.22, (230, 245, 255), (90, 160, 255), (30, 60, 180), (90, 160, 255), 22, 1.5)
    for k in range(3):
        a0 = k * 2 * math.pi / 3 + 0.9
        path = []
        for i in range(40):
            t = i / 39
            a = a0 - t * 2.2
            r = 0.46 - 0.18 * t
            path.append((0.5 + math.cos(a) * r, 0.52 + math.sin(a) * r))
        m = shape(lambda d: stroke(d, path, 0.06, 0.008))
        sh(c, m, 3, 5, 5, 180)
        glow(c, m, (200, 110, 255), 10, 1.6)
        fill(c, m, vgrad((150, 80, 200), (60, 20, 100), 0.1, 0.9))
    motes(c, 96, 12, (0.1, 0.06, 0.9, 0.5), (0.006, 0.012), (120, 190, 255), (220, 240, 255))
    return K.finish(c)


# ---- travel -----------------------------------------------------------------------------------------------------------
def person(d, cx, cy, s, fillv=255):
    """A standing figure, (cx, cy) its middle."""
    d.ellipse(box(cx, cy - 0.30 * s, 0.075 * s), fill=fillv)
    d.polygon(pts([(cx - 0.11 * s, cy - 0.18 * s), (cx + 0.11 * s, cy - 0.18 * s), (cx + 0.15 * s, cy + 0.10 * s),
                   (cx + 0.08 * s, cy + 0.10 * s), (cx + 0.07 * s, cy + 0.38 * s), (cx - 0.07 * s, cy + 0.38 * s),
                   (cx - 0.08 * s, cy + 0.10 * s), (cx - 0.15 * s, cy + 0.10 * s)]), fill=fillv)


def warp():
    """A pillar of light lifting the caster away from a glowing circle."""
    c = bg((60, 70, 170), (6, 6, 26), cy=0.5)
    ring = shape(lambda d: [d.ellipse(box(0.5, 0.82, 0.32, 0.10), outline=255, width=int(0.024 * W)),
                            d.ellipse(box(0.5, 0.82, 0.20, 0.06), outline=255, width=int(0.012 * W))])
    glow(c, ring, (140, 200, 255), 10, 1.5)
    fill(c, ring, (230, 245, 255))
    col = shape(lambda d: d.polygon(pts([(0.30, 0.82), (0.36, 0.04), (0.64, 0.04), (0.70, 0.82)]), fill=255))
    fill(c, sc(blur(col, 14), 0.6), (190, 220, 255), 0)
    fill(c, sc(blur(shape(lambda d: d.polygon(pts([(0.42, 0.82), (0.46, 0.0), (0.54, 0.0), (0.58, 0.82)]),
                                               fill=255)), 8), 0.8), (255, 255, 255), 0)
    fig = shape(lambda d: person(d, 0.5, 0.48, 0.9))
    fade = vgrad((255, 255, 255), (0, 0, 0), 0.30, 0.86).convert('L')
    fig = ImageChops.multiply(fig, fade)
    glow(c, fig, (180, 220, 255), 10, 1.3)
    fill(c, fig, (255, 255, 255))
    motes(c, 97, 22, (0.24, 0.06, 0.76, 0.8), (0.006, 0.014), (160, 210, 255), (240, 250, 255))
    sparkles(c, [(0.30, 0.22, 0.05), (0.72, 0.34, 0.06)], (180, 220, 255))
    return K.finish(c)


def escape():
    """A runner diving into a swirling gate out of the dungeon."""
    c = bg((40, 120, 100), (4, 16, 14), cx=0.62, cy=0.45)
    sw = mask()
    sd = ImageDraw.Draw(sw)
    for k in range(4):
        path = []
        for i in range(40):
            t = i / 39
            a = k * math.pi / 2 + t * 3.0
            r = 0.30 - 0.24 * t
            path.append((0.64 + math.cos(a) * r * 0.75, 0.46 + math.sin(a) * r))
        stroke(sd, path, 0.045, 0.006)
    glow(c, sw, (120, 255, 200), 16, 1.5)
    fill(c, sw, rgrad((255, 255, 230), (110, 230, 170), 0.64, 0.46, 0.3))
    hole = disc(0.64, 0.46, 0.06, 0.08)
    glow(c, hole, (255, 255, 230), 14, 1.6)
    fill(c, hole, (255, 255, 240))
    for dx, a in ((-0.16, 70), (-0.08, 130)):
        g = shape(lambda d, dx=dx: K.figure(d, 0.36 + dx, 0.56, 0.72))
        fill(c, sc(g, a / 255), (150, 255, 210), 3)
    run = shape(lambda d: K.figure(d, 0.38, 0.56, 0.72))
    glow(c, run, (200, 255, 230), 8, 1.4)
    fill(c, run, vgrad((30, 50, 46), (8, 14, 12), 0.2, 0.9))
    return K.finish(c)


def tractor():
    """A golden tether drawing a fallen comrade's soul back to the caster."""
    c = bg((150, 110, 60), (20, 12, 6), cx=0.3, cy=0.5)
    soul = shape(lambda d: person(d, 0.68, 0.54, 0.80))
    glow(c, soul, (255, 240, 200), 16, 1.3)
    fill(c, sc(soul, 0.55), vgrad((255, 255, 245), (255, 230, 170), 0.3, 0.86))
    rope = shape(lambda d: stroke(d, bez((0.62, 0.40), (0.42, 0.12), (0.20, 0.44)), 0.035, 0.035))
    head = shape(lambda d: d.polygon(pts([(0.12, 0.54), (0.13, 0.36), (0.29, 0.45)]), fill=255))
    tether = ImageChops.lighter(rope, head)
    sh(c, tether, 4, 6, 6, 170)
    glow(c, tether, (255, 200, 80), 12, 1.5)
    fill(c, tether, vgrad((255, 250, 200), (230, 160, 40), 0.15, 0.55))
    loop = shape(lambda d: d.ellipse(box(0.68, 0.43, 0.13, 0.045), outline=255, width=int(0.022 * W)))
    glow(c, loop, (255, 200, 80), 8, 1.4)
    fill(c, loop, (255, 230, 140))
    motes(c, 98, 10, (0.5, 0.2, 0.9, 0.9), (0.006, 0.012), (255, 230, 160), (255, 250, 230))
    return K.finish(c)


def retrace():
    """An hourglass inside a backward-turning arrow: back to the past."""
    c = bg((150, 110, 60), (22, 14, 6), cy=0.45)
    arr = shape(lambda d: GA.arc_arrow(d, 0.5, 0.5, 0.36, 300, 200 + 360 - 360, 0.04, 0.055))
    arr = arr.transpose(Image.FLIP_LEFT_RIGHT)
    glow(c, arr, (255, 220, 140), 10, 1.4)
    fill(c, arr, (255, 240, 200))
    frame = shape(lambda d: [d.rounded_rectangle(box(0.5, 0.25, 0.17, 0.03), radius=0.015 * W, fill=255),
                             d.rounded_rectangle(box(0.5, 0.75, 0.17, 0.03), radius=0.015 * W, fill=255),
                             d.rectangle(box(0.37, 0.5, 0.012, 0.24), fill=255),
                             d.rectangle(box(0.63, 0.5, 0.012, 0.24), fill=255)])
    glass = shape(lambda d: d.polygon(pts([(0.39, 0.28), (0.61, 0.28), (0.53, 0.48), (0.53, 0.52), (0.61, 0.72),
                                           (0.39, 0.72), (0.47, 0.52), (0.47, 0.48)]), fill=255))
    glow(c, glass, (200, 240, 255), 10, 1.0)
    fill(c, sc(glass, 0.55), (220, 240, 255))
    sand = shape(lambda d: [d.polygon(pts([(0.43, 0.34), (0.57, 0.34), (0.51, 0.47), (0.49, 0.47)]), fill=255),
                            d.polygon(pts([(0.5, 0.60), (0.58, 0.71), (0.42, 0.71)]), fill=255),
                            d.line(pts([(0.5, 0.48), (0.5, 0.62)]), fill=255, width=int(0.008 * W))])
    fill(c, sand, vgrad((255, 230, 150), (220, 160, 60), 0.34, 0.72))
    sh(c, frame, 3, 5, 5, 170)
    fill(c, frame, vgrad((255, 230, 170), (170, 110, 40), 0.2, 0.8))
    return K.finish(c)


ICONS.update({
    ('ma', 'Gravity'): gravity,
    ('ma', 'Graviga'): graviga,
    ('ma', 'Poison'): poison,
    ('ma', 'Poisonga'): poisonga,
    ('ma', 'Bio'): bio,
    ('ma', 'Virus'): virus,
    ('ma', 'Curse'): curse,
    ('ma', 'Blind'): blind,
    ('ma', 'Blindga'): blindga,
    ('ma', 'Break'): break_,
    ('ma', 'Breakga'): breakga,
    ('ma', 'Bind'): bind,
    ('ma', 'Bindga'): bindga,
    ('ma', 'Dispel'): dispel,
    ('ma', 'Dispelga'): dispelga,
    ('ma', 'Sleepga'): sleepga,
    ('ma', 'Stun'): stun,
    ('ma', 'Distract'): distract,
    ('ma', 'Frazzle'): frazzle,
    ('ma', 'Meteor'): meteor,
    ('ma', 'Comet'): comet,
    ('ma', 'Death'): death,
    ('ma', 'Impact'): impact,
    ('ma', 'Kaustra'): kaustra,
    ('ma', 'Klimaform'): klimaform,
    ('ma', 'Endark'): endark,
    ('ma', 'Blaze Spikes'): spikes('blaze'),
    ('ma', 'Ice Spikes'): spikes('ice'),
    ('ma', 'Shock Spikes'): spikes('shock'),
    ('ma', 'Dread Spikes'): spikes('dread'),
    ('ma', 'Pyrohelix'): helix,
    ('ma', 'Burn'): dot_ail,
    ('ma', 'Absorb-STR'): absorb,
    ('ma', 'Aspir'): aspir,
    ('ma', 'Warp'): warp,
    ('ma', 'Escape'): escape,
    ('ma', 'Tractor'): tractor,
    ('ma', 'Retrace'): retrace,
})


def shifts(base, targets):
    out = {}
    for name, hue in targets.items():
        if isinstance(hue, tuple):      # K.LIGHT / K.DARK: (turn from a fire-hued base, saturation, brightness)
            out[name] = ((hue[0] + FIRE - base) % 360,) + tuple(hue[1:])
        else:
            out[name] = None if (hue - base) % 360 == 0 else (hue - base) % 360
    return out


VARIANTS = {
    'Pyrohelix': shifts(20, {'Pyrohelix': FIRE, 'Cryohelix': ICE, 'Anemohelix': WIND, 'Geohelix': EARTH,
                               'Ionohelix': THUNDER, 'Hydrohelix': WATER, 'Luminohelix': K.LIGHT,
                               'Noctohelix': K.DARK}),
    'Burn': shifts(20, {'Burn': FIRE, 'Frost': ICE, 'Choke': WIND, 'Rasp': EARTH, 'Shock': THUNDER,
                          'Drown': WATER}),
    # stats by their element (STR fire, DEX thunder, VIT earth, AGI wind, INT ice, MND water, CHR light);
    # ACC, TP and Attri take the hues still free (ACC gold: CHR is the pale light variant, AGI holds green).
    'Absorb-STR': shifts(FIRE, {'Absorb-STR': FIRE, 'Absorb-DEX': THUNDER, 'Absorb-VIT': EARTH,
                                'Absorb-AGI': WIND, 'Absorb-INT': ICE, 'Absorb-MND': WATER,
                                'Absorb-CHR': K.LIGHT, 'Absorb-ACC': 50, 'Absorb-TP': 85, 'Absorb-Attri': 335}),
}
