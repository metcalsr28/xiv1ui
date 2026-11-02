"""Signature icons, group D: COR, PUP, DNC, SCH, GEO, RUN."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K

p, pts, W = K.p, K.pts, K.W


# ---- helpers --------------------------------------------------------------------------------------------------------
def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(c0 + (255,), c1 + (255,), cx, cy, r)


def col(c):
    return c + (255,) if isinstance(c, tuple) and len(c) == 3 else c


def lit(c, m, glowc=None, paint=(255, 255, 255), gr=18, gs=1.2, sh=False, soft=1.2):
    """Glow, optional drop shadow, then the gradient/colour fill of mask m."""
    if glowc:
        K.glow(c, m, col(glowc), gr, gs)
    if sh:
        K.shadow(c, m, 5, 8, 8, 150)
    K.fill(c, K.soften(m, soft), col(paint))


def rot(m, deg, cx=0.5, cy=0.5):
    """Rotate a mask counter-clockwise by deg around unit point (cx, cy)."""
    return m.rotate(deg, resample=Image.BICUBIC, center=p(cx, cy))


def inter(a, b):
    return ImageChops.multiply(a, b)


def minus(a, b):
    return ImageChops.subtract(a, b)


def scale(m, v):
    return m.point(lambda x: int(x * v))


def stroke(d, path, w0, w1=None, fillv=255):
    """A brush stroke: discs along a polyline of unit points, width tapering from w0 to w1."""
    if w1 is None:
        w1 = w0
    n = len(path)
    for i in range(n - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        steps = max(2, int(math.hypot(x1 - x0, y1 - y0) * W / 2))
        for s in range(steps):
            t = (i + s / steps) / (n - 1)
            x, y = x0 + (x1 - x0) * s / steps, y0 + (y1 - y0) * s / steps
            r = (w0 + (w1 - w0) * t) / 2
            d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=fillv)


def arc_path(cx, cy, rx, ry, a0, a1, n=60):
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * rx,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * ry) for i in range(n + 1)]


def star(d, cx, cy, ro, ri, n=5, rot0=-90, fillv=255):
    q = []
    for i in range(n * 2):
        a = math.radians(rot0) + math.pi * i / n
        r = ro if i % 2 == 0 else ri
        q.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(pts(q), fill=fillv)


def arrowhead(d, x, y, ang, size, fillv=255):
    """A triangle pointing along `ang` degrees with its tip at (x, y)."""
    a = math.radians(ang)
    bx, by = x - math.cos(a) * size, y - math.sin(a) * size
    nx, ny = -math.sin(a) * size * 0.62, math.cos(a) * size * 0.62
    d.polygon(pts([(x, y), (bx + nx, by + ny), (bx - nx, by - ny)]), fill=fillv)


def motes(c, seed, n, box, rr, color, glowc=None, alpha=220):
    rnd = random.Random(seed)
    m = K.mask()
    md = ImageDraw.Draw(m)
    for _ in range(n):
        x, y, r = rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]), rnd.uniform(*rr)
        md.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    if glowc:
        K.glow(c, m, col(glowc), 5)
    K.fill(c, scale(m, alpha / 255), col(color))


def sparkles(c, spots, color=(255, 255, 255), glowc=(255, 255, 230)):
    m = K.shape(lambda d: [K.sparkle(d, x, y, r) for x, y, r in spots])
    K.glow(c, m, col(glowc), 8)
    K.fill(c, K.soften(m), col(color))


def rays(c, cx, cy, n, color, width=0.05, length=0.75, alpha=90, blur=8, phase=0.0):
    m = K.mask()
    d = ImageDraw.Draw(m)
    for i in range(n):
        a = math.pi * 2 * i / n + phase
        d.polygon(pts([(cx, cy), (cx + math.cos(a - width) * length, cy + math.sin(a - width) * length),
                       (cx + math.cos(a + width) * length, cy + math.sin(a + width) * length)]), fill=alpha)
    K.fill(c, m.filter(ImageFilter.GaussianBlur(blur)), col(color))


def poly(seq):
    return K.shape(lambda d: d.polygon(pts(seq), fill=255))


def ell(x0, y0, x1, y1):
    return K.shape(lambda d: d.ellipse(pts([(x0, y0), (x1, y1)]), fill=255))


# ---- shared motifs ---------------------------------------------------------------------------------------------------
PIPS = {1: [(.5, .5)], 2: [(.26, .26), (.74, .74)], 3: [(.24, .24), (.5, .5), (.76, .76)],
        4: [(.27, .27), (.73, .27), (.27, .73), (.73, .73)],
        5: [(.25, .25), (.75, .25), (.5, .5), (.25, .75), (.75, .75)],
        6: [(.27, .22), (.27, .5), (.27, .78), (.73, .22), (.73, .5), (.73, .78)]}


def die(c, cx, cy, s, faces=(1, 2, 3), body=((255, 252, 244), (226, 220, 206), (178, 168, 152)),
        pip=(40, 30, 40), ace=(210, 30, 40), glowc=(255, 240, 200), gr=16, gs=1.0):
    """An isometric die, top/left/right faces showing `faces` pips."""
    T, R, L, C = (cx, cy - s), (cx + .87 * s, cy - .5 * s), (cx - .87 * s, cy - .5 * s), (cx, cy)
    B, BL, BR = (cx, cy + s), (cx - .87 * s, cy + .5 * s), (cx + .87 * s, cy + .5 * s)
    whole = poly([T, R, BR, B, BL, L])
    lit(c, whole, glowc, body[1], gr, gs, sh=True, soft=2.5)
    K.fill(c, K.soften(poly([T, R, C, L]), 2), col(body[0]))
    K.fill(c, K.soften(poly([C, R, BR, B]), 2), col(body[2]))
    sub = lambda a, b: (a[0] - b[0], a[1] - b[1])
    frames = [(T, sub(R, T), sub(L, T)), (L, sub(C, L), (0, s)), (C, sub(R, C), (0, s))]
    for (o, e1, e2), n in zip(frames, faces):
        m = K.mask()
        d = ImageDraw.Draw(m)
        r = 0.17 if n == 1 else 0.11
        for a, b in PIPS[n]:
            ring = []
            for k in range(20):
                t = math.pi * 2 * k / 20
                u, v = a + r * math.cos(t), b + r * math.sin(t)
                ring.append((o[0] + u * e1[0] + v * e2[0], o[1] + u * e1[1] + v * e2[1]))
            d.polygon(pts(ring), fill=255)
        K.fill(c, K.soften(m, 1.5), col(ace if n == 1 else pip))


def gear(d, cx, cy, ro, ri, n, hole=0.0, fillv=255):
    q = []
    for i in range(n):
        a = math.pi * 2 * i / n
        w = math.pi / n
        for da, r in ((-0.62, ri), (-0.38, ro), (0.38, ro), (0.62, ri), (1.0, ri)):
            q.append((cx + math.cos(a + da * w) * r, cy + math.sin(a + da * w) * r))
    d.polygon(pts(q), fill=fillv)
    if hole:
        d.ellipse(pts([(cx - hole, cy - hole), (cx + hole, cy + hole)]), fill=0)


def bust(d, cx, cy, s, fillv=255):
    """Head and shoulders, (cx, cy) the neck."""
    d.ellipse(pts([(cx - 0.10 * s, cy - 0.26 * s), (cx + 0.10 * s, cy - 0.04 * s)]), fill=fillv)
    d.chord(pts([(cx - 0.24 * s, cy + 0.0 * s), (cx + 0.24 * s, cy + 0.44 * s)]), 180, 360, fill=fillv)


def crystal(c, cx, cy, w, h, light, mid, dark, glowc, gr=22, gs=1.4):
    """A floating octahedral crystal (the luopan's heart): lighter left facets, darker right."""
    top, bot = (cx, cy - h), (cx, cy + h * 1.15)
    lft, rgt, mdl = (cx - w, cy), (cx + w, cy), (cx + w * 0.15, cy + h * 0.05)
    whole = poly([top, rgt, bot, lft])
    K.glow(c, whole, col(glowc), gr, gs)
    K.fill(c, K.soften(whole), col(mid))
    K.fill(c, K.soften(poly([top, mdl, lft])), col(light))
    K.fill(c, K.soften(poly([top, rgt, mdl])), col(mid))
    K.fill(c, K.soften(poly([lft, mdl, bot])), col(mid))
    K.fill(c, K.soften(poly([mdl, rgt, bot])), col(dark))
    hi = poly([(cx - w * 0.55, cy - h * 0.12), (cx - w * 0.08, cy - h * 0.78), (cx - w * 0.3, cy - h * 0.1)])
    K.fill(c, K.soften(hi, 2), (255, 255, 255, 200))


def aura_ring(c, cx, cy, rx, ry, color, glowc, width=0.03):
    m = K.shape(lambda d: d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255,
                                    width=int(width * W)))
    disc = ell(cx - rx, cy - ry, cx + rx, cy + ry)
    K.fill(c, scale(disc.filter(ImageFilter.GaussianBlur(10)), 0.35), col(glowc))
    K.glow(c, m, col(glowc), 10, 1.4)
    K.fill(c, K.soften(m), col(color))


def shield_pts(cx, top, w, h):
    """A heater shield: slightly arched top, straight sides, curving to the point."""
    q = []
    for i in range(11):
        t = i / 10
        q.append((cx - w + 2 * w * t, top - 0.03 * math.sin(math.pi * t)))
    side = top + h * 0.42
    for i in range(16):
        t = i / 15
        q.append((cx + w * math.cos(math.pi / 2 * t), side + (top + h - side) * math.sin(math.pi / 2 * t)))
    for i in range(15, -1, -1):
        t = i / 15
        q.append((cx - w * math.cos(math.pi / 2 * t), side + (top + h - side) * math.sin(math.pi / 2 * t)))
    return q


def rune_glyph(d, cx, cy, s, w=0.05):
    """An angular rune (algiz-like with a crossbar): stem, two up-strokes, a lower chevron."""
    stroke(d, [(cx, cy - 0.30 * s), (cx, cy + 0.32 * s)], w)
    stroke(d, [(cx, cy + 0.02 * s), (cx - 0.20 * s, cy - 0.22 * s)], w)
    stroke(d, [(cx, cy + 0.02 * s), (cx + 0.20 * s, cy - 0.22 * s)], w)
    stroke(d, [(cx - 0.16 * s, cy + 0.30 * s), (cx, cy + 0.14 * s), (cx + 0.16 * s, cy + 0.30 * s)], w)


def sword(d, cx, top, bottom, bw, fillv=255):
    """A broad sword pointing up: blade, crossguard, grip, pommel."""
    L = bottom - top
    guard = top + L * 0.70
    d.polygon(pts([(cx, top), (cx + bw, top + bw * 1.6), (cx + bw, guard), (cx - bw, guard),
                   (cx - bw, top + bw * 1.6)]), fill=fillv)
    d.rounded_rectangle(pts([(cx - bw * 2.6, guard), (cx + bw * 2.6, guard + L * 0.05)]), radius=0.01 * W,
                        fill=fillv)
    d.rectangle(pts([(cx - bw * 0.55, guard), (cx + bw * 0.55, bottom - L * 0.05)]), fill=fillv)
    d.ellipse(pts([(cx - bw * 0.9, bottom - L * 0.08), (cx + bw * 0.9, bottom + L * 0.01)]), fill=fillv)


ELEM_RGB = [(255, 90, 50), (140, 215, 255), (110, 230, 110), (235, 190, 80),
            (210, 120, 255), (70, 120, 255), (255, 252, 225), (120, 70, 150)]


# ---- COR -------------------------------------------------------------------------------------------------------------
def wild_card():
    c = bg((128, 56, 170), (22, 8, 36))
    rays(c, 0.5, 0.5, 14, (230, 190, 255), alpha=70)
    back = rot(K.shape(lambda d: d.rounded_rectangle(pts([(0.33, 0.20), (0.63, 0.74)]), radius=0.04 * W,
                                                    fill=255)), 22, 0.48, 0.47)
    lit(c, back, (40, 10, 60), linear_v((150, 40, 60), (90, 16, 40)), 10, 1.0, sh=True)
    cx, cy = 0.55, 0.52
    card = K.shape(lambda d: d.rounded_rectangle(pts([(cx - 0.17, cy - 0.29), (cx + 0.17, cy + 0.29)]),
                                                radius=0.045 * W, fill=255))
    card = rot(card, -12, cx, cy)
    lit(c, card, (240, 210, 255), linear_v((255, 254, 248), (226, 218, 236)), 18, 1.2, sh=True)
    border = K.shape(lambda d: d.rounded_rectangle(pts([(cx - 0.135, cy - 0.255), (cx + 0.135, cy + 0.255)]),
                                                  radius=0.03 * W, outline=255, width=int(0.012 * W)))
    K.fill(c, K.soften(rot(border, -12, cx, cy)), (206, 160, 70, 255))
    st = rot(K.shape(lambda d: star(d, cx, cy + 0.01, 0.15, 0.065)), -12, cx, cy)
    K.glow(c, st, (255, 200, 80, 255), 8)
    K.fill(c, K.soften(st), K.radial((255, 236, 140, 255), (226, 120, 30, 255), cx, cy - 0.04, 0.16))
    sparkles(c, [(0.24, 0.26, 0.07), (0.80, 0.80, 0.05)])
    return K.finish(c)


def linear_v(c0, c1, angle=90):
    return K.linear(col(c0), col(c1), angle)


def phantom_roll():
    c = bg((30, 150, 140), (4, 26, 30), cy=0.5)
    # a faint phantom echo of the die, then the die itself
    ghost = K.mask()
    gd = ImageDraw.Draw(ghost)
    s = 0.25
    for dx, a in ((-0.12, 60), (-0.06, 110)):
        cx, cy = 0.5 + dx, 0.52 + dx * 0.3
        gd.polygon(pts([(cx, cy - s), (cx + .87 * s, cy - .5 * s), (cx + .87 * s, cy + .5 * s), (cx, cy + s),
                        (cx - .87 * s, cy + .5 * s), (cx - .87 * s, cy - .5 * s)]), fill=a)
    K.fill(c, ghost.filter(ImageFilter.GaussianBlur(5)), (140, 255, 230, 255))
    die(c, 0.54, 0.52, 0.26, (1, 2, 3), glowc=(160, 255, 230), gr=20, gs=1.3)
    sparkles(c, [(0.22, 0.24, 0.07), (0.80, 0.22, 0.05)], glowc=(180, 255, 235))
    return K.finish(c)


def double_up():
    c = bg((40, 130, 70), (4, 26, 12), cy=0.55)
    die(c, 0.36, 0.60, 0.19, (1, 4, 2), glowc=(200, 255, 200), gr=14)
    die(c, 0.64, 0.52, 0.19, (1, 5, 3), glowc=(200, 255, 200), gr=14)
    up = K.shape(lambda d: [d.rectangle(pts([(0.455, 0.20), (0.545, 0.34)]), fill=255),
                            d.polygon(pts([(0.5, 0.06), (0.62, 0.21), (0.38, 0.21)]), fill=255)])
    lit(c, up, (255, 220, 100), linear_v((255, 246, 170), (236, 160, 40)), 12, 1.4, sh=True)
    return K.finish(c)


def quick_draw():
    # painted in fire red-orange; the variants turn its hue per element
    c = bg((210, 64, 20), (30, 6, 4), cx=0.4, cy=0.6)
    cx, cy = 0.58, 0.42
    u, n = (0.7071, -0.7071), (0.7071, 0.7071)

    def at(a, b):
        return (cx + a * u[0] + b * n[0], cy + a * u[1] + b * n[1])
    # the comet trail of the shot, with two thin streaks
    trail = poly([at(-0.16, -0.085), at(-0.16, 0.085), at(-0.62, 0.0)])
    streaks = K.shape(lambda d: [stroke(d, [at(-0.12, b), at(-0.52, b * 1.4)], 0.03, 0.005) for b in (-0.13, 0.13)])
    K.glow(c, trail, (255, 110, 30, 255), 22, 1.4)
    K.fill(c, K.soften(trail, 6), K.linear((255, 120, 30, 0), (255, 230, 150, 255), 315))
    K.fill(c, K.soften(streaks, 2), (255, 210, 140, 200))
    # the bullet: casing, then an ogive nose
    q = [at(-0.20, -0.08), at(0.05, -0.08)]
    q += [at(0.05 + 0.18 * t, -0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(13)]]
    q += [at(0.05 + 0.18 * t, 0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(12, -1, -1)]]
    q += [at(-0.20, 0.08)]
    bullet = poly(q)
    rim = poly([at(-0.21, -0.09), at(-0.16, -0.09), at(-0.16, 0.09), at(-0.21, 0.09)])
    whole = ImageChops.lighter(bullet, rim)
    K.glow(c, whole, (255, 160, 60, 255), 26, 1.7)
    K.shadow(c, whole, 5, 8, 8, 140)
    K.fill(c, K.soften(whole), K.linear((255, 248, 200, 255), (236, 120, 40, 255), 45))
    groove = K.shape(lambda d: stroke(d, [at(0.03, -0.075), at(0.03, 0.075)], 0.014))
    K.fill(c, K.soften(groove), (140, 50, 10, 200))
    hi = K.shape(lambda d: stroke(d, [at(-0.16, -0.045), at(0.12, -0.035)], 0.02))
    K.fill(c, K.soften(hi, 2), (255, 255, 255, 190))
    sparkles(c, [(0.80, 0.20, 0.11), (0.24, 0.30, 0.05)], glowc=(255, 210, 140))
    return K.finish(c)


# ---- PUP -------------------------------------------------------------------------------------------------------------
def overdrive():
    c = bg((210, 90, 20), (36, 8, 4), cy=0.5)
    rays(c, 0.5, 0.5, 18, (255, 220, 140), alpha=80, phase=0.1)
    g = K.shape(lambda d: gear(d, 0.5, 0.5, 0.36, 0.28, 10, hole=0.17))
    K.glow(c, g, (255, 120, 30, 255), 24, 1.4)
    K.shadow(c, g, 5, 8, 8, 140)
    K.fill(c, K.soften(g), K.radial((120, 104, 100, 255), (54, 40, 40, 255), 0.5, 0.4, 0.4))
    edge = minus(g, K.shape(lambda d: gear(d, 0.5, 0.5, 0.335, 0.255, 10, hole=0.195)))
    K.fill(c, K.soften(edge), (255, 160, 70, 220))
    bolt = poly([(0.57, 0.12), (0.35, 0.54), (0.49, 0.54), (0.41, 0.90), (0.67, 0.44), (0.53, 0.44), (0.65, 0.12)])
    lit(c, bolt, (255, 230, 120), linear_v((255, 255, 230), (255, 200, 60)), 16, 1.6, sh=True)
    return K.finish(c)


def activate():
    c = bg((30, 120, 190), (4, 14, 36), cy=0.5)
    g = K.shape(lambda d: gear(d, 0.5, 0.5, 0.44, 0.37, 14, hole=0.33))
    K.fill(c, scale(K.soften(g, 2), 0.35), (120, 200, 255, 255))
    ring = K.shape(lambda d: [stroke(d, arc_path(0.5, 0.53, 0.22, 0.22, -55, 235), 0.085)])
    bar = K.shape(lambda d: stroke(d, [(0.5, 0.18), (0.5, 0.46)], 0.085))
    m = ImageChops.lighter(ring, bar)
    lit(c, m, (120, 230, 255), linear_v((240, 255, 255), (120, 220, 255)), 24, 1.6, sh=True)
    return K.finish(c)


def repair():
    c = bg((110, 150, 60), (14, 26, 6), cy=0.5)
    w = K.shape(lambda d: [d.rounded_rectangle(pts([(0.30, 0.455), (0.84, 0.545)]), radius=0.04 * W, fill=255),
                           d.ellipse(pts([(0.13, 0.36), (0.41, 0.64)]), fill=255)])
    w = minus(w, K.shape(lambda d: [d.rectangle(pts([(0.08, 0.45), (0.27, 0.55)]), fill=255)]))
    w = minus(w, ell(0.765, 0.475, 0.815, 0.525))
    w = rot(w, -40, 0.5, 0.5)
    lit(c, w, (210, 255, 160), linear_v((236, 240, 246), (140, 150, 170), 45), 16, 1.2, sh=True)
    plus = K.shape(lambda d: [d.rounded_rectangle(pts([(0.66, 0.56), (0.74, 0.84)]), radius=0.02 * W, fill=255),
                              d.rounded_rectangle(pts([(0.56, 0.66), (0.84, 0.74)]), radius=0.02 * W, fill=255)])
    lit(c, plus, (120, 255, 140), (220, 255, 210), 14, 1.6)
    motes(c, 9, 12, (0.15, 0.55, 0.9, 0.9), (0.008, 0.018), (220, 255, 200), (140, 255, 140))
    return K.finish(c)


def deploy():
    c = bg((100, 110, 140), (12, 14, 24), cy=0.45)
    cx, cy = 0.60, 0.42
    ret = K.shape(lambda d: [d.ellipse(pts([(cx - 0.24, cy - 0.24), (cx + 0.24, cy + 0.24)]), outline=255,
                                       width=int(0.032 * W)),
                             d.ellipse(pts([(cx - 0.05, cy - 0.05), (cx + 0.05, cy + 0.05)]), fill=255)]
                    + [d.line(pts([(cx + dx * 0.15, cy + dy * 0.15), (cx + dx * 0.33, cy + dy * 0.33)]), fill=255,
                              width=int(0.032 * W)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])
    lit(c, ret, (255, 90, 70), (255, 120, 100), 14, 1.4)
    arr = K.shape(lambda d: [stroke(d, [(0.14, 0.86), (0.44, 0.58)], 0.07, 0.10),
                             arrowhead(d, 0.55, 0.47, -43, 0.19)])
    lit(c, arr, (255, 230, 170), linear_v((255, 246, 220), (220, 176, 110), 45), 16, 1.3, sh=True)
    return K.finish(c)


# ---- DNC -------------------------------------------------------------------------------------------------------------
def trance():
    c = bg((190, 50, 150), (32, 6, 30), cy=0.5)
    rib = K.mask()
    rd = ImageDraw.Draw(rib)
    for k in range(3):
        a0 = k * 120
        path = [(0.5 + math.cos(math.radians(a0 + t * 3.2)) * (0.06 + t * 0.0034),
                 0.5 + math.sin(math.radians(a0 + t * 3.2)) * (0.06 + t * 0.0034)) for t in range(0, 101, 2)]
        stroke(rd, path, 0.02, 0.075)
    K.glow(c, rib, (255, 140, 230, 255), 16, 1.3)
    K.fill(c, K.soften(rib), K.radial((255, 250, 220, 255), (255, 160, 220, 255), 0.5, 0.5, 0.42))
    st = K.shape(lambda d: K.sparkle(d, 0.5, 0.5, 0.17, 0.22))
    lit(c, st, (255, 255, 220), (255, 255, 245), 18, 1.6)
    motes(c, 21, 14, (0.12, 0.12, 0.88, 0.88), (0.007, 0.016), (255, 230, 250), (255, 150, 230))
    return K.finish(c)


def curing_waltz():
    c = bg((40, 160, 150), (4, 28, 30), cy=0.45)
    motes(c, 4, 22, (0.12, 0.2, 0.88, 0.9), (0.008, 0.02), (220, 255, 240), (160, 255, 220))
    heads = ImageChops.lighter(rot(ell(0.22, 0.62, 0.44, 0.78), 22, 0.33, 0.70),
                               rot(ell(0.54, 0.54, 0.76, 0.70), 22, 0.65, 0.62))
    stems = K.shape(lambda d: [d.rectangle(pts([(0.395, 0.27), (0.44, 0.70)]), fill=255),
                               d.rectangle(pts([(0.715, 0.19), (0.76, 0.62)]), fill=255),
                               d.polygon(pts([(0.395, 0.25), (0.76, 0.16), (0.76, 0.26), (0.395, 0.35)]),
                                         fill=255)])
    note = ImageChops.lighter(heads, stems)
    lit(c, note, (150, 255, 210), linear_v((255, 255, 250), (170, 246, 210)), 22, 1.4, sh=True)
    sparkles(c, [(0.22, 0.26, 0.08), (0.82, 0.78, 0.06)], glowc=(190, 255, 220))
    return K.finish(c)


def drop_pts(cx, top, bottom, w):
    q = []
    for i in range(61):
        t = math.pi * 2 * i / 60
        q.append((cx + w * math.sin(t) * math.sin(t / 2) ** 0.9, top + (bottom - top) * (1 - math.cos(t)) / 2))
    return q


def drain_samba():
    c = bg((110, 30, 90), (20, 4, 18), cy=0.5)
    sw = K.shape(lambda d: [stroke(d, arc_path(0.5, 0.54, 0.36, 0.30, 200, 330), 0.02, 0.06),
                            stroke(d, arc_path(0.5, 0.54, 0.36, 0.30, 20, 150), 0.02, 0.06)])
    hd = K.shape(lambda d: [arrowhead(d, *arc_path(0.5, 0.54, 0.36, 0.30, 345, 345, 1)[0], 100, 0.11),
                            arrowhead(d, *arc_path(0.5, 0.54, 0.36, 0.30, 165, 165, 1)[0], 280, 0.11)])
    m = ImageChops.lighter(sw, hd)
    lit(c, m, (255, 120, 200), (255, 210, 240), 14, 1.7)
    drop = poly(drop_pts(0.5, 0.16, 0.80, 0.20))
    lit(c, drop, (255, 60, 70), K.radial((255, 150, 140, 255), (190, 10, 30, 255), 0.44, 0.55, 0.3), 22, 1.4,
        sh=True)
    hi = ell(0.40, 0.52, 0.46, 0.64)
    K.fill(c, K.soften(hi, 3), (255, 230, 230, 200))
    return K.finish(c)


def foot(d, cx, cy, s, mirror=1, fillv=255):
    def q(x, y):
        return (cx + x * s * mirror, cy + y * s)

    def box(a, b):
        return pts([(min(a[0], b[0]), min(a[1], b[1])), (max(a[0], b[0]), max(a[1], b[1]))])
    d.ellipse(box(q(-0.10, -0.16), q(0.10, 0.08)), fill=fillv)          # ball
    d.ellipse(box(q(-0.075, 0.12), q(0.075, 0.28)), fill=fillv)          # heel
    d.polygon(pts([q(-0.09, 0.0), q(0.08, 0.0), q(0.06, 0.18), q(-0.06, 0.18)]), fill=fillv)
    for i, (x, y, r) in enumerate(((-0.075, -0.20, 0.035), (-0.02, -0.235, 0.03), (0.03, -0.23, 0.027),
                                   (0.07, -0.205, 0.024), (0.10, -0.165, 0.021))):
        d.ellipse(box(q(x - r, y - r), q(x + r, y + r)), fill=fillv)


def box_step():
    c = bg((200, 140, 40), (36, 20, 4), cy=0.5)
    sq = pts([(0.20, 0.20), (0.80, 0.80)])
    inside = rot(K.shape(lambda d: d.rounded_rectangle(sq, radius=0.05 * W, fill=255)), 12)
    K.fill(c, K.soften(inside, 4).point(lambda v: int(v * 0.35)), (40, 20, 0, 255))
    box = rot(K.shape(lambda d: d.rounded_rectangle(sq, radius=0.05 * W, outline=255, width=int(0.05 * W))), 12)
    K.glow(c, box, (255, 220, 120, 255), 12, 1.5)
    K.fill(c, K.soften(box), linear_v((255, 250, 220), (250, 200, 110)))
    left = rot(K.shape(lambda d: foot(d, 0.38, 0.58, 0.95, -1)), 10, 0.38, 0.58)
    right = rot(K.shape(lambda d: foot(d, 0.62, 0.42, 0.95, 1)), -10, 0.62, 0.42)
    feet = ImageChops.lighter(left, right)
    lit(c, feet, (255, 200, 100), linear_v((255, 250, 230), (240, 196, 130)), 14, 1.3, sh=True)
    return K.finish(c)


def climactic_flourish():
    c = bg((80, 70, 200), (8, 6, 36), cy=0.48)
    rays(c, 0.5, 0.48, 12, (200, 200, 255), alpha=90, width=0.06)
    rib = K.shape(lambda d: [stroke(d, [(0.5 + math.cos(math.radians(150 + t * 4.2)) * (0.38 - t * 0.0012),
                                         0.5 + math.sin(math.radians(150 + t * 4.2)) * (0.30 - t * 0.0010))
                                        for t in range(0, 61, 2)], 0.025, 0.07)])
    lit(c, rib, (255, 120, 160), linear_v((255, 170, 190), (210, 50, 100), 0), 10, 1.2)
    st = K.shape(lambda d: star(d, 0.5, 0.48, 0.30, 0.13, 5))
    lit(c, st, (255, 220, 120), K.radial((255, 255, 220, 255), (240, 160, 40, 255), 0.5, 0.44, 0.3), 24, 1.5,
        sh=True)
    orbs = K.shape(lambda d: [d.ellipse(pts([(x - 0.035, 0.84 - 0.035), (x + 0.035, 0.84 + 0.035)]), fill=255)
                              for x in (0.38, 0.5, 0.62)])
    lit(c, orbs, (255, 240, 180), (255, 250, 220), 8, 1.4)
    return K.finish(c)


# ---- SCH -------------------------------------------------------------------------------------------------------------
def open_book(left_paint, right_paint, c, glowc, top=0.40, hw=0.38, h=0.34, cover_col=(120, 70, 40)):
    """An open book seen from the front: two curved pages over a cover edge."""
    def page(side):
        edge = [(0.5 + side * hw * t, top - 0.07 * t - 0.05 * math.sin(math.pi * t)) for t in
                [i / 20 for i in range(21)]]
        bot = [(x, y + h) for x, y in edge]
        return poly(edge + bot[::-1])
    lp, rp = page(-1), page(1)
    both = ImageChops.lighter(lp, rp)
    yb = top + h
    cover = poly([(0.5 - hw - 0.02, yb - 0.08), (0.5, yb), (0.5 + hw + 0.02, yb - 0.08), (0.5 + hw + 0.02, yb - 0.02),
                  (0.5, yb + 0.06), (0.5 - hw - 0.02, yb - 0.02)])
    K.glow(c, both, col(glowc), 26, 1.5)
    K.shadow(c, ImageChops.lighter(both, cover), 4, 8, 8, 150)
    K.fill(c, K.soften(cover), col(cover_col))
    K.fill(c, K.soften(lp), left_paint)
    K.fill(c, K.soften(rp), right_paint)
    gutter = K.shape(lambda d: d.line(pts([(0.5, top), (0.5, yb)]), fill=255, width=int(0.012 * W)))
    K.fill(c, gutter.filter(ImageFilter.GaussianBlur(4)), (60, 40, 30, 200))


def light_arts():
    c = bg((236, 176, 70), (60, 30, 8), cy=0.36)
    rays(c, 0.5, 0.30, 16, (255, 250, 220), alpha=120)
    open_book(K.linear((255, 255, 250, 255), (236, 226, 200, 255), 0),
              K.linear((236, 226, 200, 255), (255, 255, 250, 255), 0), c, (255, 240, 180), top=0.52, hw=0.34,
              h=0.26, cover_col=(150, 90, 40))
    cx, cy = 0.5, 0.29
    m = K.shape(lambda d: [d.ellipse(pts([(cx - 0.09, cy - 0.09), (cx + 0.09, cy + 0.09)]), fill=255)]
                + [d.polygon(pts([(cx + math.cos(a - 0.17) * 0.11, cy + math.sin(a - 0.17) * 0.11),
                                  (cx + math.cos(a) * 0.19, cy + math.sin(a) * 0.19),
                                  (cx + math.cos(a + 0.17) * 0.11, cy + math.sin(a + 0.17) * 0.11)]), fill=255)
                   for a in [math.pi * 2 * i / 8 for i in range(8)]])
    lit(c, m, (255, 230, 120), K.radial((255, 255, 230, 255), (255, 180, 40, 255), cx, cy, 0.18), 18, 1.6,
        sh=True)
    return K.finish(c)


def dark_arts():
    c = bg((100, 44, 150), (8, 2, 16), cy=0.36)
    rays(c, 0.5, 0.30, 12, (170, 110, 230), alpha=80)
    open_book(K.linear((70, 50, 110, 255), (150, 120, 200, 255), 0),
              K.linear((150, 120, 200, 255), (70, 50, 110, 255), 0), c, (210, 150, 255), top=0.52, hw=0.34,
              h=0.26, cover_col=(20, 10, 30))
    cx, cy = 0.5, 0.29
    m = minus(ell(cx - 0.15, cy - 0.15, cx + 0.15, cy + 0.15), ell(cx - 0.07, cy - 0.20, cx + 0.21, cy + 0.08))
    lit(c, m, (210, 150, 255), linear_v((250, 236, 255), (180, 120, 250)), 16, 1.6, sh=True)
    sparkles(c, [(0.72, 0.20, 0.06), (0.26, 0.30, 0.04)], color=(240, 220, 255), glowc=(180, 120, 255))
    return K.finish(c)


def tabula_rasa():
    c = bg((40, 120, 140), (4, 18, 26), cy=0.4)
    rays(c, 0.5, 0.5, 14, (220, 255, 255), alpha=120, width=0.07, length=0.7)
    open_book(K.linear((255, 255, 252, 255), (222, 236, 240, 255), 0),
              K.linear((70, 50, 100, 255), (30, 20, 50, 255), 0), c, (220, 255, 255))
    sparkles(c, [(0.5, 0.20, 0.13), (0.78, 0.18, 0.05), (0.22, 0.22, 0.05)], glowc=(200, 255, 255))
    return K.finish(c)


def sublimation():
    c = bg((50, 60, 140), (6, 6, 26), cy=0.5)
    glass = poly([(0.32, 0.22), (0.68, 0.22), (0.66, 0.32), (0.53, 0.48), (0.53, 0.52), (0.66, 0.68),
                  (0.68, 0.78), (0.32, 0.78), (0.34, 0.68), (0.47, 0.52), (0.47, 0.48), (0.34, 0.32)])
    K.glow(c, glass, (160, 200, 255, 255), 22, 1.3)
    K.fill(c, K.soften(glass), (180, 200, 240, 90))
    top_sand = inter(glass, poly([(0.0, 0.33), (1, 0.33), (1, 0.5), (0, 0.5)]))
    K.fill(c, K.soften(top_sand), K.linear((255, 110, 100, 255), (200, 20, 40, 255), 90))
    bot_sand = inter(glass, poly([(0.30, 0.79), (0.38, 0.66), (0.5, 0.58), (0.62, 0.66), (0.70, 0.79)]))
    K.glow(c, bot_sand, (80, 160, 255, 255), 10, 1.2)
    K.fill(c, K.soften(bot_sand), K.linear((140, 210, 255, 255), (40, 90, 230, 255), 90))
    stream = K.shape(lambda d: d.line(pts([(0.5, 0.48), (0.5, 0.60)]), fill=255, width=int(0.016 * W)))
    K.fill(c, K.soften(stream), K.linear((255, 120, 140, 255), (120, 170, 255, 255), 90))
    frame = K.shape(lambda d: [d.rounded_rectangle(pts([(0.24, 0.15), (0.76, 0.23)]), radius=0.02 * W, fill=255),
                               d.rounded_rectangle(pts([(0.24, 0.77), (0.76, 0.85)]), radius=0.02 * W, fill=255),
                               d.rectangle(pts([(0.27, 0.22), (0.30, 0.78)]), fill=255),
                               d.rectangle(pts([(0.70, 0.22), (0.73, 0.78)]), fill=255)])
    K.shadow(c, frame, 4, 6, 6, 130)
    K.fill(c, K.soften(frame), K.linear((255, 230, 160, 255), (180, 120, 50, 255), 90))
    hi = poly([(0.37, 0.25), (0.41, 0.25), (0.37, 0.31)])
    K.fill(c, K.soften(hi, 2), (255, 255, 255, 170))
    return K.finish(c)


# ---- GEO -------------------------------------------------------------------------------------------------------------
def geocolure():
    # painted green (Regen); the variants turn its hue per spell
    c = bg((40, 170, 80), (4, 30, 12), cy=0.6)
    aura_ring(c, 0.5, 0.78, 0.34, 0.10, (200, 255, 200), (90, 255, 130))
    col_m = poly([(0.30, 0.78), (0.70, 0.78), (0.62, 0.15), (0.38, 0.15)])
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(20)), 0.3), (160, 255, 170, 255))
    crystal(c, 0.5, 0.38, 0.19, 0.23, (170, 255, 190), (70, 210, 110), (20, 110, 50), (110, 255, 150))
    motes(c, 13, 16, (0.2, 0.2, 0.8, 0.85), (0.007, 0.016), (220, 255, 220), (120, 255, 150))
    return K.finish(c)


def indicolure():
    # painted green like the geocolure: an aura ring around the caster's feet, light rising through them
    c = bg((40, 170, 80), (4, 30, 12), cy=0.55)
    col_m = poly([(0.18, 0.78), (0.82, 0.78), (0.70, 0.10), (0.30, 0.10)])
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(22)), 0.35), (160, 255, 170, 255))
    back = K.shape(lambda d: d.arc(pts([(0.12, 0.66), (0.88, 0.90)]), 180, 360, fill=255, width=int(0.035 * W)))
    K.glow(c, back, (110, 255, 150, 255), 10, 1.3)
    K.fill(c, K.soften(back), (200, 255, 210, 255))
    motes(c, 17, 14, (0.14, 0.14, 0.86, 0.66), (0.008, 0.016), (220, 255, 220), (120, 255, 150))
    fig = K.shape(lambda d: [d.ellipse(pts([(0.43, 0.19), (0.57, 0.33)]), fill=255),
                             d.polygon(pts([(0.42, 0.36), (0.58, 0.36), (0.74, 0.50), (0.70, 0.56), (0.60, 0.47),
                                            (0.67, 0.80), (0.33, 0.80), (0.40, 0.47), (0.30, 0.56), (0.26, 0.50)]),
                                       fill=255)])
    K.glow(c, fig, (160, 255, 180, 255), 20, 1.5)
    K.fill(c, K.soften(fig), K.linear((240, 255, 240, 255), (100, 210, 130, 255), 90))
    front = K.shape(lambda d: d.arc(pts([(0.12, 0.66), (0.88, 0.90)]), 0, 180, fill=255, width=int(0.04 * W)))
    K.glow(c, front, (110, 255, 150, 255), 14, 1.7)
    K.fill(c, K.soften(front), (220, 255, 225, 255))
    return K.finish(c)


def bolster():
    c = bg((210, 160, 40), (40, 24, 4), cy=0.48)
    rays(c, 0.5, 0.46, 18, (255, 245, 200), alpha=120, width=0.06)
    crystal(c, 0.5, 0.42, 0.17, 0.22, (255, 255, 230), (255, 214, 100), (200, 130, 30), (255, 230, 140), 28, 1.6)
    ch = K.shape(lambda d: [stroke(d, [(0.12 + dx, 0.62), (0.20 + dx, 0.52), (0.28 + dx, 0.62)], 0.05)
                            for dx in (0.0, 0.60)]
                 + [stroke(d, [(0.12 + dx, 0.76), (0.20 + dx, 0.66), (0.28 + dx, 0.76)], 0.05)
                    for dx in (0.0, 0.60)])
    lit(c, ch, (255, 240, 170), (255, 252, 230), 10, 1.4)
    return K.finish(c)


def full_circle():
    c = bg((40, 160, 190), (4, 22, 32), cy=0.5)
    arc = K.shape(lambda d: [stroke(d, arc_path(0.5, 0.5, 0.30, 0.30, -60, 220), 0.03, 0.075),
                             arrowhead(d, *arc_path(0.5, 0.5, 0.30, 0.30, 245, 245, 1)[0], 340, 0.15)])
    lit(c, arc, (140, 240, 255), linear_v((240, 255, 255), (130, 220, 250)), 18, 1.5, sh=True)
    crystal(c, 0.5, 0.48, 0.10, 0.12, (240, 255, 255), (130, 220, 240), (40, 120, 160), (180, 250, 255), 14, 1.2)
    motes(c, 23, 12, (0.18, 0.18, 0.82, 0.82), (0.007, 0.016), (230, 255, 255), (150, 240, 255))
    return K.finish(c)


def entrust():
    c = bg((180, 70, 120), (34, 6, 22), cy=0.5)
    # the ally the Indi- spell is handed to: a whole head-and-shoulders, well inside the rim
    fig = K.shape(lambda d: bust(d, 0.66, 0.50, 0.72))
    aura_ring(c, 0.66, 0.68, 0.19, 0.05, (255, 220, 240), (255, 140, 200))
    K.glow(c, fig, (255, 190, 225, 255), 14, 1.6)
    K.fill(c, K.soften(fig), K.linear((120, 50, 90, 255), (50, 14, 36, 255), 90))
    arr = K.shape(lambda d: [stroke(d, arc_path(0.47, 0.40, 0.21, 0.17, 195, 300), 0.03, 0.06),
                             arrowhead(d, *arc_path(0.47, 0.40, 0.21, 0.17, 318, 318, 1)[0], 30, 0.11)])
    lit(c, arr, (255, 200, 230), (255, 236, 245), 10, 1.3)
    orb = ell(0.16, 0.42, 0.36, 0.62)
    lit(c, orb, (255, 150, 210), K.radial((255, 255, 255, 255), (250, 120, 190, 255), 0.24, 0.49, 0.12), 22, 1.6)
    return K.finish(c)


# ---- RUN -------------------------------------------------------------------------------------------------------------
def runes():
    # painted fire red (Ignis); the variants turn its hue per element
    c = bg((190, 50, 30), (30, 6, 4), cy=0.5)
    stone = K.shape(lambda d: d.polygon(pts([(0.34, 0.16), (0.66, 0.14), (0.74, 0.40), (0.70, 0.82),
                                             (0.32, 0.86), (0.26, 0.50)]), fill=255))
    K.glow(c, stone, (255, 120, 60, 255), 20, 1.2)
    K.shadow(c, stone, 5, 8, 8, 160)
    K.fill(c, K.soften(stone, 2), K.linear((170, 110, 96, 255), (70, 36, 30, 255), 60))
    chip = poly([(0.34, 0.16), (0.66, 0.14), (0.58, 0.24), (0.36, 0.26)])
    K.fill(c, K.soften(chip, 2), (255, 220, 200, 60))
    g = K.shape(lambda d: rune_glyph(d, 0.50, 0.50, 0.80, 0.06))
    K.glow(c, g, (255, 110, 40, 255), 14, 1.8)
    K.fill(c, K.soften(g), (255, 236, 200, 255))
    motes(c, 31, 12, (0.15, 0.15, 0.85, 0.85), (0.007, 0.016), (255, 220, 180), (255, 120, 60))
    return K.finish(c)


def shield_paint(c, cx, top, w, h, glowc, face, glyph=True, gr=18):
    sp = shield_pts(cx, top, w, h)
    m = poly(sp)
    K.glow(c, m, col(glowc), gr, 1.4)
    K.shadow(c, m, 5, 8, 8, 150)
    K.fill(c, K.soften(m), K.linear((246, 226, 170, 255), (170, 120, 50, 255), 90))
    inner = poly(shield_pts(cx, top + h * 0.06, w * 0.82, h * 0.86))
    K.fill(c, K.soften(inner), face)
    if glyph:
        g = K.shape(lambda d: rune_glyph(d, cx, top + h * 0.45, h * 0.95, 0.045 * h / 0.66))
        K.glow(c, g, col(glowc), 8, 1.6)
        K.fill(c, K.soften(g), (240, 252, 255, 255))


def vallation():
    c = bg((40, 80, 180), (4, 10, 34), cy=0.48)
    rays(c, 0.5, 0.5, 12, (170, 210, 255), alpha=70)
    shield_paint(c, 0.5, 0.16, 0.25, 0.70, (140, 200, 255), K.linear((70, 120, 220, 255), (20, 40, 110, 255), 90))
    return K.finish(c)


def valiance():
    c = bg((40, 150, 170), (4, 24, 30), cy=0.48)
    for dx in (-0.21, 0.21):
        shield_paint(c, 0.5 + dx, 0.26, 0.15, 0.46, (140, 255, 240),
                     K.linear((50, 150, 160, 255), (20, 70, 80, 255), 90), glyph=False, gr=10)
    shield_paint(c, 0.5, 0.15, 0.22, 0.66, (160, 255, 240), K.linear((60, 180, 190, 255), (14, 70, 86, 255), 90))
    return K.finish(c)


def swordplay():
    c = bg((150, 40, 40), (28, 4, 6), cy=0.5)
    rays(c, 0.5, 0.42, 10, (255, 200, 170), alpha=70)
    s1 = rot(K.shape(lambda d: sword(d, 0.5, 0.08, 0.92, 0.045)), 38, 0.5, 0.5)
    s2 = rot(K.shape(lambda d: sword(d, 0.5, 0.08, 0.92, 0.045)), -38, 0.5, 0.5)
    for s in (s1, s2):
        lit(c, s, (255, 200, 160), K.linear((250, 252, 255, 255), (150, 160, 180, 255), 30), 14, 1.2, sh=True)
    sparkles(c, [(0.5, 0.40, 0.14)], glowc=(255, 210, 140))
    return K.finish(c)


def elemental_sforzo():
    c = bg((140, 90, 50), (24, 12, 6), cy=0.5)
    for i, rgb in enumerate(ELEM_RGB):
        a = math.pi * 2 * i / 8 - math.pi / 2
        x, y = 0.5 + math.cos(a) * 0.32, 0.5 + math.sin(a) * 0.32
        o = ell(x - 0.07, y - 0.07, x + 0.07, y + 0.07)
        lit(c, o, rgb, K.radial((255, 255, 255, 255), col(rgb), x - 0.015, y - 0.015, 0.06), 10, 1.6)
    ring = K.shape(lambda d: d.ellipse(pts([(0.18, 0.18), (0.82, 0.82)]), outline=255, width=int(0.012 * W)))
    K.fill(c, K.soften(ring).point(lambda v: int(v * 0.5)), (255, 230, 180, 255))
    s = K.shape(lambda d: sword(d, 0.5, 0.10, 0.86, 0.06))
    lit(c, s, (255, 236, 190), K.linear((255, 255, 255, 255), (170, 176, 196, 255), 0), 22, 1.5, sh=True)
    return K.finish(c)


# ---- registry --------------------------------------------------------------------------------------------------------
ICONS = {
    ('ja', 'Wild Card'): wild_card,
    ('ja', 'Phantom Roll'): phantom_roll,
    ('ja', 'Quick Draw'): quick_draw,
    ('ja', 'Double-Up'): double_up,
    ('ja', 'Overdrive'): overdrive,
    ('ja', 'Activate'): activate,
    ('ja', 'Repair'): repair,
    ('ja', 'Deploy'): deploy,
    ('ja', 'Trance'): trance,
    ('ja', 'Curing Waltz'): curing_waltz,
    ('ja', 'Drain Samba'): drain_samba,
    ('ja', 'Box Step'): box_step,
    ('ja', 'Climactic Flourish'): climactic_flourish,
    ('ja', 'Tabula Rasa'): tabula_rasa,
    ('ja', 'Light Arts'): light_arts,
    ('ja', 'Dark Arts'): dark_arts,
    ('ja', 'Sublimation'): sublimation,
    ('ja', 'Bolster'): bolster,
    ('ja', 'Full Circle'): full_circle,
    ('ja', 'Entrust'): entrust,
    ('ma', 'Geocolure'): geocolure,
    ('ma', 'Indicolure'): indicolure,
    ('ja', 'Elemental Sforzo'): elemental_sforzo,
    ('ja', 'Vallation'): vallation,
    ('ja', 'Valiance'): valiance,
    ('ja', 'Swordplay'): swordplay,
    ('ja', 'Rune Enchantment'): runes,
}

ROLLS = ["Phantom Roll", "Fighter's Roll", "Monk's Roll", "Healer's Roll", "Wizard's Roll", "Warlock's Roll",
         "Rogue's Roll", "Gallant's Roll", "Chaos Roll", "Beast Roll", "Choral Roll", "Hunter's Roll",
         "Samurai Roll", "Ninja Roll", "Drachen Roll", "Evoker's Roll", "Magus's Roll", "Corsair's Roll",
         "Puppet Roll", "Dancer's Roll", "Scholar's Roll", "Bolter's Roll", "Caster's Roll", "Courser's Roll",
         "Blitzer's Roll", "Tactician's Roll", "Allies' Roll", "Miser's Roll", "Companion's Roll",
         "Avenger's Roll", "Naturalist's Roll", "Runeist's Roll"]

COVERS = {
    'Phantom Roll': ROLLS,
    'Curing Waltz': ['Curing Waltz', 'Curing Waltz II', 'Curing Waltz III', 'Curing Waltz IV', 'Curing Waltz V',
                     'Divine Waltz', 'Divine Waltz II'],
    'Drain Samba': ['Drain Samba', 'Drain Samba II', 'Drain Samba III'],
}

# Element hues (degrees) for the recoloured variants.
FIRE, EARTH, LIGHT, WIND, ICE, WATER, THUNDER, DARK = 8, K.EARTH, 50, 120, 190, 225, K.THUNDER, 275    # (Earth dark brown, Thunder golden orange, Dark purple)


def shifts(base, targets):
    out = {}
    for name, hue in targets.items():
        if isinstance(hue, tuple):
            # K.LIGHT / K.DARK: (turn from a fire-hued base, saturation, brightness); re-aim the turn at `base`.
            deg, sat_k, val_k = hue
            out[name] = ((FIRE + deg - base) % 360, sat_k, val_k)
            continue
        d = (hue - base) % 360
        out[name] = None if d == 0 else d
    return out


ELEMENT_SHOTS = {'Fire Shot': FIRE, 'Ice Shot': ICE, 'Wind Shot': WIND, 'Earth Shot': EARTH,
                 'Thunder Shot': THUNDER, 'Water Shot': WATER, 'Light Shot': K.LIGHT, 'Dark Shot': K.DARK}
RUNES = {'Ignis': FIRE, 'Gelus': ICE, 'Flabra': WIND, 'Tellus': EARTH, 'Sulpor': THUNDER,
         'Unda': WATER,
         'Lux': K.LIGHT, 'Tenebrae': K.DARK}
# Geomancy by effect: buffs by the stat's element (STR fire, DEX thunder, VIT earth, AGI wind, INT ice, MND water,
# CHR light), the rest by an obvious colour; each debuff sits near the hue of the buff it mirrors.
GEO_EFFECTS = {'Regen': 125, 'Poison': 285, 'Refresh': 215, 'Haste': 160, 'STR': FIRE, 'DEX': THUNDER,
               'VIT': EARTH, 'AGI': WIND, 'INT': ICE, 'MND': WATER, 'CHR': K.LIGHT, 'Fury': 0, 'Barrier': 40,
               'Acumen': 300, 'Fend': 175, 'Precision': 55, 'Voidance': 145, 'Focus': 255, 'Attunement': 200,
               'Wilt': 345, 'Frailty': 25, 'Fade': 320, 'Malaise': 185, 'Slip': 65, 'Torpor': 100, 'Vex': 240,
               'Languor': 210, 'Slow': 30, 'Paralysis': 190, 'Gravity': 265}

QD_BASE = 15
RUNE_BASE = 8
GEO_BASE = 137

VARIANTS = {
    'Quick Draw': shifts(QD_BASE, dict(ELEMENT_SHOTS, **{'Quick Draw': FIRE})),
    'Rune Enchantment': shifts(RUNE_BASE, dict(RUNES, **{'Rune Enchantment': FIRE})),
    'Geocolure': shifts(GEO_BASE, {'Geo-' + k: v for k, v in GEO_EFFECTS.items()}),
    'Indicolure': shifts(GEO_BASE, {'Indi-' + k: v for k, v in GEO_EFFECTS.items()}),
}
