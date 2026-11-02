"""Signature icons, round 2: Blue Magic. Monster moves the BLU learns, composed from a small kit of BLU motifs
(slash, beam, breath, burst, bloom, aura, mist, impact, projectile) in element colours, each with a monster touch."""
import colorsys
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_b as GB
import group_d as GD

W = K.W
p, pts = K.p, K.pts


# ---- colour ---------------------------------------------------------------------------------------------------------
def A(c):
    return tuple(c) + (255,) if len(c) == 3 else tuple(c)


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s)), max(0, min(1, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


class E:
    """An element's paint: hi (core), mid, lo (deep), glow."""
    def __init__(self, hi, mid, lo, glow, h):
        self.hi, self.mid, self.lo, self.glow, self.h = hi, mid, lo, glow, h


EL = {
    'fire': E((255, 244, 180), (255, 130, 40), (200, 40, 16), (255, 110, 40), 12),
    'ice': E((250, 255, 255), (160, 222, 255), (70, 140, 220), (140, 214, 255), 200),
    'wind': E((240, 255, 230), (130, 232, 140), (34, 150, 76), (120, 245, 150), 130),
    'earth': E((255, 236, 186), (226, 170, 80), (130, 86, 36), (240, 190, 90), 36),
    'thunder': E((255, 250, 235), (214, 150, 255), (126, 64, 220), (190, 130, 255), 275),
    'water': E((230, 246, 255), (96, 166, 255), (30, 70, 200), (80, 150, 255), 220),
    'light': E((255, 255, 248), (255, 238, 160), (220, 176, 70), (255, 240, 170), 50),
    'dark': E((236, 204, 255), (156, 84, 210), (64, 20, 104), (170, 80, 230), 290),
    'blu': E((235, 252, 255), (100, 210, 240), (30, 110, 176), (90, 210, 255), 195),
    'heal': E((240, 255, 240), (140, 245, 176), (40, 160, 100), (130, 255, 176), 150),
    'poison': E((240, 255, 200), (170, 230, 70), (80, 140, 30), (170, 240, 80), 85),
    'blood': E((255, 210, 200), (230, 50, 60), (130, 10, 24), (255, 60, 70), 355),
    'gold': E((255, 252, 220), (255, 214, 110), (190, 130, 40), (255, 210, 120), 42),
}


def bg(h, s=0.72, v=0.62, cx=0.5, cy=0.45, r=0.72, dv=0.10):
    """A radial background in hue h (degrees)."""
    return K.radial(A(hsv(h, s, v)), A(hsv(h + 6, min(1, s + 0.12), dv)), cx, cy, r)


# ---- masks ----------------------------------------------------------------------------------------------------------
M = K.shape
soften = K.soften


def poly(seq):
    return M(lambda d: d.polygon(pts(seq), fill=255))


def ell(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return M(lambda d: d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), fill=255))


def ring(cx, cy, rx, ry, w):
    return M(lambda d: d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255, width=int(w * W)))


def add(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def sub(a, b):
    return ImageChops.subtract(a, b)


def mul(a, b):
    return ImageChops.multiply(a, b)


def sc(m, v):
    return m.point(lambda x: int(x * v))


def rot(m, deg, cx=0.5, cy=0.5):
    """Rotate a mask counter-clockwise by deg around (cx, cy)."""
    return m.rotate(deg, resample=Image.BICUBIC, center=p(cx, cy))


def blur(m, r):
    return m.filter(ImageFilter.GaussianBlur(r))


def xf(seq, cx, cy, s=1.0, ang=0.0, mirror=1):
    """Local points -> unit points: mirror x, scale, rotate ang degrees (clockwise on screen), move."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x * mirror * ca - y * sa) * s, cy + (x * mirror * sa + y * ca) * s) for x, y in seq]


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


def tube(path, w0, w1=None, taper=None):
    """A polygon along `path`: width w0 -> w1, or with taper='both' pointed at both ends (max w0), 'end' pointed
    at the end."""
    w1 = w0 if w1 is None else w1
    n = len(path)
    left, right = [], []
    for i, (x, y) in enumerate(path):
        a = path[max(0, i - 1)]
        b = path[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        t = i / max(1, n - 1)
        if taper == 'both':
            w = w0 * math.sin(math.pi * t) ** 0.7
        else:
            w = w0 + (w1 - w0) * t
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]


def tubem(path, w0, w1=None, taper=None):
    return poly(tube(path, w0, w1, taper))


def arcp(cx, cy, rx, ry, a0, a1, n=48):
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * rx,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * ry) for i in range(n + 1)]


def star_pts(cx, cy, n, r1, r2, rot0=-90, jitter=0.0, seed=1):
    rnd = random.Random(seed)
    out = []
    for i in range(n * 2):
        a = math.radians(rot0) + math.pi * i / n
        r = (r1 if i % 2 == 0 else r2) * (1 + rnd.uniform(-jitter, jitter))
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


def dots(seed, n, box, rr):
    rnd = random.Random(seed)
    m = K.mask()
    d = ImageDraw.Draw(m)
    for _ in range(n):
        x, y, r = rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]), rnd.uniform(*rr)
        d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    return m


# ---- paint ----------------------------------------------------------------------------------------------------------
def grad(top, bot=None, ang=90):
    if bot is None:
        return A(top)
    return K.linear(A(top), A(bot), ang)


def rgrad(c0, c1, cx=0.5, cy=0.45, r=0.3):
    return K.radial(A(c0), A(c1), cx, cy, r)


def lit(c, m, top, bot=None, glowc=None, gr=16, gs=1.2, sh=False, soft=1.2, ang=90):
    """Glow, optional drop shadow, then a gradient fill of mask m."""
    if glowc:
        K.glow(c, m, A(glowc), gr, gs)
    if sh:
        K.shadow(c, m, 5, 8, 8, 150)
    K.fill(c, soften(m, soft), top if isinstance(top, Image.Image) else grad(top, bot, ang))


def wash(c, m, color, r=10, a=1.0):
    """A soft translucent fill (clouds, mist, shading)."""
    K.fill(c, sc(blur(m, r), a), A(color))


def motes(c, seed, n, box, rr, color, glowc=None, a=1.0):
    m = dots(seed, n, box, rr)
    if glowc:
        K.glow(c, m, A(glowc), 5)
    K.fill(c, sc(m, a), A(color))


def sparkles(c, spots, glowc=(255, 255, 240)):
    m = M(lambda d: [K.sparkle(d, x, y, r) for x, y, r in spots])
    K.glow(c, m, A(glowc), 8)
    K.fill(c, soften(m), (255, 255, 255, 255))


def rays(c, cx, cy, n, color, width=0.05, length=0.75, alpha=90, blur_r=8, phase=0.0):
    GD.rays(c, cx, cy, n, color, width, length, alpha, blur_r, phase)


def shine(c, m, dx=-0.03, dy=-0.04, a=0.55, r=4):
    """A highlight on the upper-left of mask m (m minus itself shifted)."""
    sh = sub(m, ImageChops.offset(m, int(-dx * W), int(-dy * W)))
    K.fill(c, sc(blur(sh, r), a), (255, 255, 255, 255))


def shade(c, m, dx=0.04, dy=0.05, a=0.45, r=6, col=(10, 10, 30)):
    """Shade the lower-right of mask m."""
    s = sub(m, ImageChops.offset(m, int(-dx * W), int(-dy * W)))
    K.fill(c, sc(blur(mul(s, m), r), a), A(col))


# ---- motifs ---------------------------------------------------------------------------------------------------------
def beam(c, x0, y0, x1, y1, e, w0=0.06, w1=0.16, core=0.5):
    """A widening beam of energy."""
    path = [(x0 + (x1 - x0) * t / 20, y0 + (y1 - y0) * t / 20) for t in range(21)]
    m = tubem(path, w0, w1)
    K.glow(c, m, A(e.glow), 22, 1.4)
    lit(c, m, e.mid, soft=3)
    inner = tubem(path, w0 * core, w1 * core)
    K.glow(c, inner, A(e.hi), 8)
    lit(c, inner, e.hi, soft=3)


def cone(c, x0, y0, ang, L, spread, e, seed=1, n=34, r0=0.03, r1=0.14, dens=1.0):
    """A breath / gas cloud fanning out from (x0, y0) along `ang` degrees."""
    rnd = random.Random(seed)
    outer, inner = K.mask(), K.mask()
    do, di = ImageDraw.Draw(outer), ImageDraw.Draw(inner)
    a0 = math.radians(ang)
    for i in range(n):
        t = rnd.uniform(0.05, 1.0) ** 0.8
        a = a0 + rnd.uniform(-spread, spread) * math.radians(1) * t ** 0.3
        x, y = x0 + math.cos(a) * L * t, y0 + math.sin(a) * L * t
        r = r0 + (r1 - r0) * t * rnd.uniform(0.7, 1.1)
        do.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
        if t < 0.75:
            ri = r * 0.55
            di.ellipse(pts([(x - ri, y - ri), (x + ri, y + ri)]), fill=255)
    K.glow(c, outer, A(e.glow), 24, 1.2 * dens)
    wash(c, outer, e.lo, 8, 0.9 * dens)
    wash(c, outer, e.mid, 14, 0.85 * dens)
    wash(c, inner, e.hi, 10, 0.8 * dens)
    return outer


def cloud(c, seed, box, e, n=12, rr=(0.07, 0.13), dens=1.0, hi=True):
    m = dots(seed, n, box, rr)
    K.glow(c, m, A(e.glow), 20, 0.8 * dens)
    wash(c, m, e.lo, 6, 0.9 * dens)
    wash(c, sub(m, ImageChops.offset(m, 0, int(0.04 * W))), e.mid, 8, 0.9 * dens)
    if hi:
        wash(c, sub(m, ImageChops.offset(m, int(-0.02 * W), int(-0.07 * W))), e.hi, 6, 0.7 * dens)
    return m


def burst(c, cx, cy, r1, r2, n, e, seed=3, jitter=0.25, rot0=-90, core=True):
    m = poly(star_pts(cx, cy, n, r1, r2, rot0, jitter, seed))
    K.glow(c, m, A(e.glow), 24, 1.4)
    lit(c, m, rgrad(e.hi, e.mid, cx, cy, r1 * 0.9))
    if core:
        k = ell(cx, cy, r2 * 0.8)
        K.glow(c, k, A(e.hi), 14, 1.4)
        lit(c, k, (255, 255, 255), soft=4)
    return m


def waves(c, cx, cy, ang, radii, e, spread=50, w=0.04):
    m = M(lambda d: [d.arc(pts([(cx - r, cy - r), (cx + r, cy + r)]), ang - spread, ang + spread, fill=255,
                           width=int(w * W)) for r in radii])
    lit(c, m, e.hi, glowc=e.glow, gr=12, gs=1.4, soft=1.6)
    return m


def vortex(c, cx, cy, r, arms, e, turns=0.9, w=0.07, rot0=0, ry=1.0, hi=True):
    def arm(k):
        out = []
        for i in range(41):
            t = i / 40
            a = math.radians(rot0 + 360 * k / arms) + turns * 2 * math.pi * t
            rr = r * (0.12 + 0.88 * t)
            out.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * ry))
        return out
    m = M(lambda d: [d.polygon(pts(tube(arm(k), w * 0.25, w)), fill=255) for k in range(arms)])
    K.glow(c, m, A(e.glow), 16, 1.3)
    lit(c, m, rgrad(e.hi, e.mid, cx, cy, r))
    if hi:
        k = ell(cx, cy, r * 0.16, r * 0.16 * ry)
        lit(c, k, e.hi, glowc=e.hi, gr=10, gs=1.5)
    return m


def slash(c, x0, y0, x1, y1, bend, e, w=0.06, glowc=None):
    """A crescent slash (both ends pointed) from (x0, y0) to (x1, y1), bowing by `bend` across."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    path = bez((x0, y0), (mx + nx * bend * 2, my + ny * bend * 2), (x1, y1), 30)
    m = tubem(path, w, taper='both')
    lit(c, m, e.hi, glowc=glowc or e.glow, gr=14, gs=1.5)
    return m


def claws(c, n, x0, y0, x1, y1, e, gap=0.11, bend=0.03, w=0.07):
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ms = []
    for i in range(n):
        o = (i - (n - 1) / 2) * gap
        ms.append(slash(c, x0 + nx * o, y0 + ny * o, x1 + nx * o, y1 + ny * o, bend, e, w))
    return add(*ms)


def speed(c, ang, lines, color, w=0.014, a=0.7):
    """Speed streaks along `ang` degrees: lines = [(x, y, length)] ending at (x, y)."""
    r = math.radians(ang)
    m = M(lambda d: [d.polygon(pts(tube([(x - math.cos(r) * L, y - math.sin(r) * L), (x, y)], 0.002, w)),
                               fill=255) for x, y, L in lines])
    K.fill(c, sc(soften(m, 2), a), A(color))


def impact(c, cx, cy, r, e, n=9, seed=5, inner=0.45):
    return burst(c, cx, cy, r, r * inner, n, e, seed, 0.3, core=False)


def shockring(c, cx, cy, rx, ry, e, w=0.03):
    m = ring(cx, cy, rx, ry, w)
    lit(c, m, e.hi, glowc=e.glow, gr=12, gs=1.4)
    return m


def bubble(c, cx, cy, r, e, a=0.35):
    """A translucent barrier sphere."""
    d = ell(cx, cy, r)
    K.fill(c, sc(blur(d, 6), a * 0.6), A(e.mid))
    rim = sub(d, ell(cx - r * 0.06, cy - r * 0.06, r * 0.86))
    K.glow(c, ring(cx, cy, r, r, 0.02), A(e.glow), 12, 1.2)
    K.fill(c, sc(blur(rim, 6), 0.7), A(e.hi))
    hi = ell(cx - r * 0.42, cy - r * 0.45, r * 0.22, r * 0.13)
    K.fill(c, sc(blur(rot(hi, 35, cx - r * 0.42, cy - r * 0.45), 4), 0.85), (255, 255, 255, 255))


def arrow_mark(c, x, y, s, up, e):
    """A small stat-up / stat-down chevron arrow."""
    k = -1 if up else 1
    seq = [(0, k * 0.5), (0.45, 0), (0.18, 0), (0.18, -k * 0.45), (-0.18, -k * 0.45), (-0.18, 0), (-0.45, 0)]
    m = poly(xf(seq, x, y, s))
    lit(c, m, e.hi, e.mid, glowc=e.glow, gr=8, gs=1.3, sh=True)


# ---- monster bits ---------------------------------------------------------------------------------------------------
def maw(c, mx, my, s, ang=0, mirror=1, skin=((70, 90, 120), (20, 26, 44)), eyec=(255, 220, 90), horns=True,
        rimc=(150, 220, 255)):
    """A beast head in profile, jaws open, mouth at (mx, my), facing +x (mirror=-1 faces -x)."""
    head = [(-0.66, -0.10), (-0.56, -0.30), (-0.38, -0.34), (-0.20, -0.25), (0.03, -0.14), (0.01, -0.05),
            (-0.28, -0.01), (-0.03, 0.10), (-0.06, 0.18), (-0.36, 0.20), (-0.64, 0.14), (-1.4, 0.4), (-1.4, -0.1)]
    hm = poly(xf(head, mx, my, s, ang, mirror))
    if horns:
        hm = add(hm, poly(xf([(-0.46, -0.30), (-0.86, -0.56), (-0.60, -0.40), (-0.36, -0.32)], mx, my, s, ang,
                             mirror)))
    teeth = []
    for i in range(4):
        x = -0.24 + i * 0.06
        y = -0.02 - 0.03 * (i / 3)
        teeth += [poly(xf([(x - 0.022, y), (x + 0.022, y - 0.01), (x + 0.004, y + 0.06)], mx, my, s, ang, mirror))]
        yl = 0.04 + 0.05 * (i / 3)
        teeth += [poly(xf([(x - 0.02, yl + 0.04), (x + 0.025, yl + 0.04), (x + 0.0, yl - 0.02)], mx, my, s, ang,
                          mirror))]
    K.glow(c, hm, A(rimc), 10, 1.0)
    K.shadow(c, hm, 5, 8, 8, 150)
    lit(c, hm, skin[0], skin[1])
    shine(c, hm, -0.0, -0.025, 0.35, 3)
    lit(c, add(*teeth), (255, 252, 240), (210, 200, 180), soft=1)
    eye = poly(xf([(-0.36, -0.22), (-0.26, -0.24), (-0.30, -0.18)], mx, my, s, ang, mirror))
    lit(c, eye, eyec, glowc=eyec, gr=6, gs=1.6)
    return hm


def eye(c, cx, cy, rx, ry, iris, pupil=(10, 6, 20), slit=True, lid=(40, 20, 60), white=(255, 250, 240),
        glowc=None, ir=None):
    m = M(lambda d: _eye_shape(d, cx, cy, rx, ry))
    if glowc:
        K.glow(c, m, A(glowc), 18, 1.4)
    K.shadow(c, m, 4, 6, 6, 140)
    lit(c, m, white, (200, 196, 210))
    ir = ir or ry * 0.95
    i = mul(ell(cx, cy, ir), m)
    lit(c, i, rgrad(tuple(min(255, v + 90) for v in iris), iris, cx - ir * 0.2, cy - ir * 0.3, ir * 1.2))
    if slit:
        pm = mul(ell(cx, cy, ir * 0.22, ir * 0.9), m)
    else:
        pm = ell(cx, cy, ir * 0.42)
    lit(c, pm, pupil, soft=1)
    lit(c, ell(cx - ir * 0.35, cy - ir * 0.4, ir * 0.18), (255, 255, 255), soft=1)
    outline = sub(M(lambda d: _eye_shape(d, cx, cy, rx * 1.06, ry * 1.18)), m)
    lit(c, outline, lid, soft=1.5)
    return m


def _eye_shape(d, cx, cy, rx, ry):
    top, bot = [], []
    for i in range(41):
        t = -1 + 2 * i / 40
        h = ry * (1 - t * t) ** 0.85
        top.append((cx + t * rx, cy - h))
        bot.append((cx + t * rx, cy + h))
    d.polygon(pts(top + bot[::-1]), fill=255)


def horn(cx, cy, s, ang=0, mirror=1, curl=0.3, length=0.55, w=0.16):
    """A curved horn mask from base (cx, cy) curving up (local -y) and outward."""
    path = bez((0, 0), (curl * 0.9, -length * 0.6), (curl * 0.2 + 0.1, -length), 30)
    return poly(xf(tube(path, w, 0.005), cx, cy, s, ang, mirror))


def feather(c, cx, cy, s, ang, e, vane=(255, 255, 255), vane2=(190, 210, 235), glowc=None):
    """A feather, quill at (cx, cy) pointing local -y, rotated `ang`."""
    outline = []
    for i in range(31):
        t = i / 30
        outline.append((0.12 * math.sin(math.pi * t ** 0.8) * (1 - 0.2 * t), -0.1 - 0.85 * t))
    right = outline
    left = [(-x * 0.8, y) for x, y in outline][::-1]
    m = poly(xf(right + left, cx, cy, s, ang))
    notch = M(lambda d: [d.line(pts(xf([(0.13, -0.40 - k * 0.12), (0.0, -0.32 - k * 0.12)], cx, cy, s, ang)),
                                fill=255, width=max(1, int(0.02 * W * s))) for k in range(3)])
    lit(c, m, vane, vane2, glowc=glowc or e.glow, gr=10, gs=1.0, sh=True)
    K.fill(c, sc(soften(mul(notch, m), 1.5), 0.8), A(e.lo))
    q = M(lambda d: d.line(pts(xf([(0, 0.02), (0, -0.9)], cx, cy, s, ang)), fill=255, width=max(1, int(0.022 * W * s))))
    lit(c, q, e.lo, soft=1)
    return m


def leafm(cx, cy, ang, length, width):
    return M(lambda d: GA.leaf(d, cx, cy, math.radians(ang), length, width))


def flower(c, cx, cy, r, petal, petal2, centre=(255, 220, 90), n=6, rot0=-90, glowc=None, w=0.45):
    m = add(*[leafm(cx, cy, rot0 + 360 * k / n, r, r * w) for k in range(n)])
    lit(c, m, rgrad(petal, petal2, cx, cy, r), glowc=glowc or petal, gr=14, gs=1.2, sh=True)
    veins = M(lambda d: [d.line(pts([(cx, cy), (cx + math.cos(math.radians(rot0 + 360 * k / n)) * r * 0.8,
                                                 cy + math.sin(math.radians(rot0 + 360 * k / n)) * r * 0.8)]),
                                fill=255, width=int(0.008 * W)) for k in range(n)])
    K.fill(c, sc(soften(veins), 0.35), A(petal2))
    k = ell(cx, cy, r * 0.28)
    lit(c, k, rgrad((255, 255, 220), centre, cx - r * 0.08, cy - r * 0.1, r * 0.3), glowc=centre, gr=8)
    return m


def bomb(c, cx, cy, r, body=((255, 190, 90), (200, 70, 30)), face=(70, 20, 10), flame=True, angry=False):
    """An FFXI bomb: a round fiery body with a grinning face."""
    if flame:
        fl = M(lambda d: [GA.flame(d, cx, cy - r * 0.4, r * 0.85, r * 1.9, 0.0),
                          GA.flame(d, cx - r * 0.62, cy - r * 0.3, r * 0.45, r * 1.2, -0.04),
                          GA.flame(d, cx + r * 0.62, cy - r * 0.3, r * 0.45, r * 1.2, 0.04)])
        K.glow(c, fl, (255, 140, 40, 255), 14, 1.2)
        lit(c, fl, (255, 236, 140), (255, 110, 30), ang=270)
    m = ell(cx, cy, r)
    K.glow(c, m, (255, 130, 40, 255), 18, 1.2)
    lit(c, m, rgrad((255, 246, 200), body[0], cx - r * 0.3, cy - r * 0.35, r * 0.7), sh=True)
    shade(c, m, 0.05, 0.06, 0.6, 10, body[1])
    # face
    ey = cy - r * 0.12
    if angry:
        eyes = add(poly([(cx - r * 0.55, ey - r * 0.2), (cx - r * 0.12, ey), (cx - r * 0.5, ey + r * 0.12)]),
                   poly([(cx + r * 0.55, ey - r * 0.2), (cx + r * 0.12, ey), (cx + r * 0.5, ey + r * 0.12)]))
    else:
        eyes = add(ell(cx - r * 0.32, ey, r * 0.13, r * 0.18), ell(cx + r * 0.32, ey, r * 0.13, r * 0.18))
    mouth = M(lambda d: d.chord(pts([(cx - r * 0.5, cy - r * 0.1), (cx + r * 0.5, cy + r * 0.62)]), 10, 170,
                                fill=255))
    lit(c, add(eyes, mouth), face, soft=1.5)
    return m


def drop(cx, top, bottom, w):
    return poly(GD.drop_pts(cx, top, bottom, w))


def fist(c, cx, cy, s, glowc=(255, 200, 120), skin=((255, 232, 196), (222, 146, 92)), ang=0):
    m = M(lambda d: K.fist_front(d, cx, cy, s))
    ln = M(lambda d: K.fist_lines(d, cx, cy, s))
    if ang:
        m, ln = rot(m, ang, cx, cy), rot(ln, ang, cx, cy)
    lit(c, m, skin[0], skin[1], glowc=glowc, gr=16, gs=1.2, sh=True)
    K.fill(c, sc(soften(ln, 1.5), 0.7), (120, 60, 36, 255))
    return m


def skull(c, cx, cy, s, top=(255, 252, 236), bot=(196, 186, 160), glowc=(200, 255, 220)):
    m = M(lambda d: GB.skull(d, cx, cy, s))
    lit(c, m, top, bot, glowc=glowc, gr=14, gs=1.2, sh=True)
    return m


def note(c, cx, cy, s, top=(255, 255, 255), bot=(200, 220, 255), glowc=(160, 220, 255), flags=1, ang=0):
    m = M(lambda d: GB.note(d, cx, cy, s, flags, ang))
    lit(c, m, top, bot, glowc=glowc, gr=10, gs=1.3, sh=True)
    return m


def zzz(c, x, y, s, color=(240, 240, 255), glowc=(180, 160, 255)):
    def z(d, cx, cy, k):
        w = 0.11 * k
        d.line(pts([(cx - w, cy - w), (cx + w, cy - w), (cx - w, cy + w), (cx + w, cy + w)]), fill=255,
               width=int(0.03 * k * W), joint='curve')
    m = M(lambda d: [z(d, x, y, s), z(d, x + 0.14 * s, y - 0.20 * s, s * 0.7), z(d, x + 0.26 * s, y - 0.36 * s, s * 0.5)])
    lit(c, m, color, glowc=glowc, gr=8, gs=1.3)


def spike_ring(cx, cy, r0, r1, n, w=0.35, rot0=-90):
    return poly(star_pts(cx, cy, n, r1, r0, rot0))


# ---- painters -------------------------------------------------------------------------------------------------------
SPELLS = {}


def nautilus(c, cx, cy, r, ang=0, body=((255, 236, 210), (196, 140, 110)), stripe=(150, 70, 50), glowc=None):
    """A spiral nautilus shell, opening toward +x."""
    def rr(t):
        return r * math.exp(-0.30 * (2.3 * math.pi - t))
    outer = [(math.cos(t + math.radians(ang)) * rr(t), math.sin(t + math.radians(ang)) * rr(t))
             for t in [2.3 * math.pi * i / 120 for i in range(121)]]
    m = poly([(cx + x, cy + y) for x, y in outer])
    lit(c, m, rgrad(body[0], body[1], cx - r * 0.3, cy - r * 0.3, r * 1.1), glowc=glowc, gr=14, sh=True)
    st = M(lambda d: [d.line(pts([(cx, cy), (cx + math.cos(t + math.radians(ang)) * rr(t) * 1.1,
                                             cy + math.sin(t + math.radians(ang)) * rr(t) * 1.1)]),
                             fill=255, width=int(0.022 * W)) for t in [0.9 + 0.62 * k for k in range(9)]])
    K.fill(c, sc(soften(mul(st, m), 2), 0.75), A(stripe))
    sp = M(lambda d: d.line(pts([(cx + math.cos(t + math.radians(ang)) * rr(t) * 0.55,
                                  cy + math.sin(t + math.radians(ang)) * rr(t) * 0.55) for t in
                                 [2.3 * math.pi * i / 80 for i in range(20, 81)]]), fill=255, width=int(0.016 * W)))
    K.fill(c, sc(soften(mul(sp, m), 1.5), 0.6), A(body[1]))
    shine(c, m, -0.02, -0.03, 0.45)
    return m


def venom_shell():
    """A nautilus shell spewing a cloud of venom."""
    c = bg(285, 0.6, 0.45)
    e = EL['poison']
    cone(c, 0.46, 0.50, -30, 0.48, 34, e, 4, 44, 0.03, 0.10)
    motes(c, 4, 16, (0.5, 0.1, 0.9, 0.6), (0.008, 0.016), (230, 255, 160), e.glow)
    nautilus(c, 0.40, 0.58, 0.36, 160, body=((255, 226, 200), (190, 110, 100)), glowc=(200, 240, 140))
    drips = add(drop(0.62, 0.70, 0.84, 0.035), drop(0.74, 0.62, 0.74, 0.03))
    lit(c, drips, e.hi, e.mid, glowc=e.glow, gr=8)
    return K.finish(c)


def maelstrom():
    """A churning whirlpool dragging everything down."""
    c = bg(215, 0.8, 0.55)
    e = EL['water']
    wash(c, ell(0.5, 0.52, 0.42, 0.30), (10, 30, 90), 18, 0.8)
    vortex(c, 0.5, 0.52, 0.42, 4, e, 1.1, 0.09, 20, 0.62, hi=False)
    vortex(c, 0.5, 0.52, 0.24, 3, EL['ice'], 0.9, 0.05, 70, 0.62, hi=False)
    core = ell(0.5, 0.52, 0.07, 0.045)
    K.fill(c, soften(core, 3), (4, 10, 40, 255))
    motes(c, 7, 14, (0.1, 0.12, 0.9, 0.4), (0.006, 0.013), (220, 240, 255), e.glow)
    return K.finish(c)


def metallic_body():
    """A body turned to gleaming chrome, light glancing off it."""
    c = bg(220, 0.70, 0.30, cy=0.36)
    rays(c, 0.5, 0.40, 16, (210, 236, 255), alpha=90)
    m = M(lambda d: GD.bust(d, 0.5, 0.50, 1.55))
    out = m.filter(ImageFilter.MaxFilter(9))
    K.glow(c, out, (170, 220, 255, 255), 20, 1.5)
    K.shadow(c, out, 5, 8, 8, 170)
    K.fill(c, soften(out, 1.5), (10, 16, 34, 255))
    # chrome: hard bands of sky and ground reflected
    env = Image.new('RGBA', (W, W))
    ed = ImageDraw.Draw(env)
    bands = [(0.0, (250, 252, 255)), (0.30, (170, 200, 236)), (0.40, (60, 76, 110)), (0.47, (230, 240, 255)),
             (0.60, (120, 140, 176)), (0.74, (40, 50, 80)), (0.82, (190, 210, 240)), (1.0, (90, 106, 140))]
    for y in range(W):
        t = y / W
        for k in range(len(bands) - 1):
            if bands[k][0] <= t <= bands[k + 1][0]:
                u = (t - bands[k][0]) / (bands[k + 1][0] - bands[k][0])
                ca, cb = bands[k][1], bands[k + 1][1]
                ed.line([(0, y), (W, y)], fill=tuple(int(ca[i] + (cb[i] - ca[i]) * u) for i in range(3)) + (255,))
                break
    K.fill(c, soften(m), env)
    seam = M(lambda d: [d.line(pts(arcp(0.5, 0.50, 0.24, 0.10, 200, 340)), fill=255, width=int(0.014 * W)),
                        d.line(pts([(0.5, 0.60), (0.5, 0.98)]), fill=255, width=int(0.012 * W))])
    K.fill(c, sc(soften(mul(seam, m), 1.2), 0.7), (20, 30, 60, 255))
    shine(c, m, -0.02, -0.025, 0.8, 3)
    sparkles(c, [(0.62, 0.20, 0.10), (0.30, 0.58, 0.07), (0.74, 0.66, 0.05)])
    return K.finish(c)


def screwdriver():
    """A twisted spiral horn driving in."""
    c = bg(190, 0.7, 0.5)
    impact(c, 0.70, 0.30, 0.22, EL['gold'], 9, 2)
    path = [(0.22 + 0.48 * t / 30, 0.78 - 0.48 * t / 30) for t in range(31)]
    m = tubem(path, 0.20, 0.01)
    lit(c, m, (255, 248, 230), (170, 150, 120), glowc=(150, 220, 255), sh=True)
    bands = M(lambda d: [d.line(pts([(x - 0.06, y - 0.06 + 0.02), (x + 0.07, y + 0.07 - 0.03)]), fill=255,
                                width=int(0.025 * W)) for x, y in [path[i] for i in (4, 9, 14, 19, 24)]])
    K.fill(c, sc(soften(mul(bands, m), 1.5), 0.7), (110, 80, 60, 255))
    speed(c, -45, [(0.20, 0.66, 0.2), (0.32, 0.80, 0.18), (0.14, 0.86, 0.12)], (220, 245, 255))
    return K.finish(c)


def mp_drainkiss():
    """A kiss that draws mana out in blue droplets."""
    c = bg(320, 0.55, 0.50)
    e = EL['blu']
    # lips
    up = poly(bez3((0.18, 0.56), (0.30, 0.36), (0.42, 0.40), (0.5, 0.46), 20) +
              bez3((0.5, 0.46), (0.58, 0.40), (0.70, 0.36), (0.82, 0.56), 20) + [(0.5, 0.58)])
    lo = poly(bez3((0.18, 0.56), (0.32, 0.82), (0.68, 0.82), (0.82, 0.56), 30) + [(0.5, 0.60)])
    lips = add(up, lo)
    lit(c, lips, (255, 140, 190), (170, 30, 90), glowc=(255, 120, 200), gr=14, sh=True)
    shine(c, lo, 0, -0.04, 0.5, 5)
    # drops rising in
    for x, y, s in ((0.32, 0.12, 0.06), (0.52, 0.18, 0.05), (0.70, 0.10, 0.07)):
        lit(c, drop(x, y, y + s * 2.2, s * 0.7), e.hi, e.mid, glowc=e.glow, gr=10)
    return K.finish(c)


def ahriman(c, cx, cy, s, iris=(200, 40, 40)):
    """A floating eye with bat wings."""
    for m_ in (1, -1):
        wing = poly(xf([(0.18, -0.05), (0.55, -0.35), (0.62, -0.10), (0.52, -0.02), (0.50, 0.10), (0.40, 0.06),
                        (0.34, 0.16), (0.18, 0.08)], cx, cy, s, 0, m_))
        lit(c, wing, (110, 70, 140), (40, 20, 60), glowc=(200, 140, 255), gr=8, sh=True)
    body = ell(cx, cy, 0.24 * s)
    lit(c, body, rgrad((150, 120, 170), (50, 30, 70), cx - 0.06 * s, cy - 0.08 * s, 0.26 * s), sh=True)
    eye(c, cx, cy + 0.01 * s, 0.17 * s, 0.13 * s, iris, slit=True, lid=(40, 20, 50))


def death_ray():
    """An ahriman's gaze firing a ray of death."""
    c = bg(275, 0.55, 0.35)
    e = EL['dark']
    beam(c, 0.40, 0.42, 0.92, 0.86, e, 0.05, 0.22)
    ahriman(c, 0.38, 0.38, 0.82)
    return K.finish(c)


def sandspin():
    """A whirling column of sand."""
    c = bg(34, 0.6, 0.55)
    e = EL['earth']
    wash(c, ell(0.5, 0.86, 0.36, 0.08), (255, 220, 160), 10, 0.6)
    m = M(lambda d: [d.polygon(pts(tube(arcp(0.5, 0.18 + k * 0.13, 0.33 - k * 0.055, 0.06, 180, 540, 60),
                                        0.03, 0.06)), fill=255) for k in range(5)])
    lit(c, m, e.hi, e.mid, glowc=e.glow, gr=14)
    motes(c, 9, 40, (0.14, 0.14, 0.86, 0.86), (0.005, 0.012), (255, 240, 200), e.glow)
    return K.finish(c)


def smite_of_rage():
    """A furious overhead smash, red with rage."""
    c = bg(355, 0.75, 0.45)
    impact(c, 0.5, 0.66, 0.32, EL['fire'], 11, 9)
    speed(c, 90, [(0.30, 0.36, 0.2), (0.70, 0.36, 0.2), (0.5, 0.14, 0.12)], (255, 200, 180))
    fist(c, 0.5, 0.42, 0.85, glowc=(255, 70, 40), skin=((255, 210, 180), (210, 100, 70)), ang=180)
    anger(c, 0.76, 0.24, 0.13)
    return K.finish(c)


def anger(c, cx, cy, r, col=(255, 60, 50)):
    """The popping-vein anger mark: four curved ticks around a point."""
    m = M(lambda d: [d.polygon(pts(tube(bez((cx + math.cos(a) * r * 0.25 + math.cos(a + 0.8) * r * 0.45,
                                             cy + math.sin(a) * r * 0.25 + math.sin(a + 0.8) * r * 0.45),
                                            (cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75),
                                            (cx + math.cos(a) * r * 0.25 + math.cos(a - 0.8) * r * 0.45,
                                             cy + math.sin(a) * r * 0.25 + math.sin(a - 0.8) * r * 0.45), 12),
                                        r * 0.32, taper='both')), fill=255)
                     for a in [math.pi / 4 + math.pi / 2 * k for k in range(4)]])
    lit(c, m, (255, 150, 130), col, glowc=(255, 40, 30), gr=8, gs=1.4, sh=True)


def club(cx, cy, s, ang):
    seq = [(-0.03, 0.45), (0.03, 0.45), (0.06, 0.0), (0.12, -0.25), (0.10, -0.42), (0.0, -0.48), (-0.10, -0.42),
           (-0.12, -0.25), (-0.06, 0.0)]
    m = poly(xf(seq, cx, cy, s, ang))
    sp = add(*[poly(xf([(sx * 0.10, y - 0.03), (sx * 0.20, y), (sx * 0.10, y + 0.03)], cx, cy, s, ang))
               for y in (-0.36, -0.22, -0.08) for sx in (-1, 1)])
    return m, sp


def bludgeon():
    """A great spiked club coming down."""
    c = bg(25, 0.55, 0.45)
    impact(c, 0.66, 0.36, 0.28, EL['gold'], 10, 4)
    m, sp = club(0.45, 0.56, 0.95, 40)
    lit(c, sp, (240, 240, 245), (130, 130, 150), sh=True)
    lit(c, m, (210, 150, 100), (100, 56, 30), glowc=(255, 200, 120), gr=12, sh=True)
    shine(c, m, -0.02, -0.02, 0.4)
    speed(c, 40, [(0.34, 0.20, 0.16), (0.24, 0.30, 0.14)], (255, 240, 200))
    return K.finish(c)


SPELLS.update({
    'Venom Shell': venom_shell, 'Maelstrom': maelstrom, 'Metallic Body': metallic_body, 'Screwdriver': screwdriver,
    'MP Drainkiss': mp_drainkiss, 'Death Ray': death_ray, 'Sandspin': sandspin, 'Smite of Rage': smite_of_rage,
    'Bludgeon': bludgeon,
})
def refueling():
    """Showpiece: a drop of glowing fuel with a blue flame at its heart, ringed by racing haste arrows."""
    c = bg(188, 0.75, 0.45, cy=0.5)
    rays(c, 0.5, 0.52, 16, (140, 240, 255), alpha=60)
    arcs = M(lambda d: [GA.arc_arrow(d, 0.5, 0.54, 0.38, 200, 320, 0.045, 0.06),
                        GA.arc_arrow(d, 0.5, 0.54, 0.38, 20, 140, 0.045, 0.06)])
    lit(c, arcs, (230, 255, 255), (120, 220, 255), glowc=(80, 220, 255), gr=12, gs=1.5)
    d = drop(0.5, 0.14, 0.82, 0.25)
    lit(c, d, rgrad((255, 250, 200), (240, 150, 40), 0.44, 0.55, 0.32), glowc=(255, 190, 80), gr=24, gs=1.4, sh=True)
    shade(c, d, 0.04, 0.05, 0.5, 8, (150, 60, 10))
    fl = M(lambda d_: [GA.flame(d_, 0.5, 0.74, 0.11, 0.34, 0.01)])
    lit(c, fl, (255, 255, 255), (110, 200, 255), glowc=(120, 220, 255), gr=10, gs=1.5, ang=270)
    lit(c, ell(0.41, 0.50, 0.03, 0.06), (255, 255, 255), soft=4)
    sparkles(c, [(0.80, 0.22, 0.07), (0.20, 0.80, 0.05)], (160, 240, 255))
    return K.finish(c)


def ice_break():
    """Ice shards bursting out of a cracked core."""
    c = bg(205, 0.7, 0.5)
    e = EL['ice']
    rays(c, 0.5, 0.52, 12, (200, 240, 255), alpha=70)
    shards = []
    rnd = random.Random(8)
    for k in range(7):
        a = math.radians(-90 + k * 360 / 7 + rnd.uniform(-12, 12))
        L = rnd.uniform(0.30, 0.42)
        w = rnd.uniform(0.06, 0.09)
        nx, ny = -math.sin(a), math.cos(a)
        bx, by = 0.5 + math.cos(a) * 0.08, 0.52 + math.sin(a) * 0.08
        shards.append([(bx + nx * w, by + ny * w), (0.5 + math.cos(a) * L, 0.52 + math.sin(a) * L),
                       (bx - nx * w, by - ny * w)])
    m = add(*[poly(s_) for s_ in shards])
    lit(c, m, (255, 255, 255), (120, 190, 240), glowc=e.glow, gr=16, gs=1.3, sh=True)
    half = add(*[poly([s_[0], s_[1], ((s_[0][0] + s_[2][0]) / 2, (s_[0][1] + s_[2][1]) / 2)]) for s_ in shards])
    K.fill(c, sc(soften(half), 0.5), (60, 120, 200, 255))
    core = poly(star_pts(0.5, 0.52, 6, 0.12, 0.07, -90, 0.2, 2))
    lit(c, core, (255, 255, 255), (190, 236, 255), glowc=(255, 255, 255), gr=12, gs=1.5)
    return K.finish(c)


def blitzstrahl():
    """A pillar of lightning hammering the ground."""
    c = bg(265, 0.7, 0.42, cy=0.7)
    e = EL['thunder']
    pil = poly([(0.40, 0.0), (0.60, 0.0), (0.56, 0.78), (0.44, 0.78)])
    K.glow(c, pil, A(e.glow), 26, 1.2)
    K.fill(c, sc(blur(pil, 10), 0.7), A(e.mid))
    bolt = poly([(0.53, 0.02), (0.42, 0.30), (0.52, 0.32), (0.40, 0.56), (0.50, 0.57), (0.45, 0.80), (0.62, 0.48),
                 (0.53, 0.47), (0.64, 0.24), (0.55, 0.23), (0.62, 0.02)])
    lit(c, bolt, (255, 255, 255), (255, 236, 150), glowc=(255, 240, 180), gr=12, gs=1.5)
    shockring(c, 0.5, 0.80, 0.30, 0.08, e, 0.03)
    shockring(c, 0.5, 0.80, 0.18, 0.045, e, 0.025)
    sparkles(c, [(0.26, 0.66, 0.06), (0.76, 0.70, 0.07)], e.glow)
    return K.finish(c)


def self_destruct():
    """A bomb swelling as it goes off."""
    c = bg(20, 0.85, 0.55, cy=0.5)
    burst(c, 0.5, 0.52, 0.47, 0.30, 12, EL['fire'], 4, 0.25)
    bomb(c, 0.5, 0.56, 0.24, angry=True, flame=False)
    sparkles(c, [(0.22, 0.24, 0.07), (0.80, 0.76, 0.06)], (255, 200, 120))
    return K.finish(c)


def mysterious_light():
    """A strange prism of light splitting into every colour."""
    c = bg(250, 0.45, 0.35)
    m = K.mask()
    d = ImageDraw.Draw(m)
    for k, h in enumerate((0, 40, 60, 120, 190, 230, 280)):
        a0 = math.radians(-12 + k * 8)
        layer = poly([(0.48, 0.52), (0.5 + math.cos(a0 - 0.05) * 0.6, 0.52 + math.sin(a0 - 0.05) * 0.6),
                      (0.5 + math.cos(a0 + 0.05) * 0.6, 0.52 + math.sin(a0 + 0.05) * 0.6)])
        K.fill(c, sc(blur(layer, 4), 0.85), A(hsv(h, 0.7, 1.0)))
    inc = tubem([(0.0, 0.66), (0.46, 0.53)], 0.03, 0.04)
    lit(c, inc, (255, 255, 255), glowc=(255, 255, 255), gr=8)
    pr = poly([(0.46, 0.30), (0.62, 0.64), (0.30, 0.64)])
    lit(c, pr, rgrad((255, 255, 255), (170, 190, 255), 0.42, 0.42, 0.3), glowc=(220, 230, 255), gr=18, gs=1.4,
        sh=True)
    K.fill(c, sc(soften(poly([(0.46, 0.30), (0.46, 0.64), (0.30, 0.64)])), 0.35), (120, 140, 230, 255))
    sparkles(c, [(0.46, 0.30, 0.08), (0.80, 0.24, 0.05)])
    return K.finish(c)


def flake(c, cx, cy, r, e=None, glowc=(170, 230, 255)):
    m = M(lambda d: [d.line(pts([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)]), fill=255,
                            width=max(2, int(0.16 * r * W))) for a in [math.pi / 3 * k for k in range(6)]] +
          [d.line(pts([(cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6),
                       (cx + math.cos(a) * r * 0.6 + math.cos(a + s_) * r * 0.32,
                        cy + math.sin(a) * r * 0.6 + math.sin(a + s_) * r * 0.32)]), fill=255,
                  width=max(2, int(0.12 * r * W))) for a in [math.pi / 3 * k for k in range(6)] for s_ in (-0.9, 0.9)])
    lit(c, m, (255, 255, 255), (190, 230, 255), glowc=glowc, gr=8, gs=1.3)
    return m


def cold_wave():
    """A freezing wave rolling across, sapping agility."""
    c = bg(195, 0.65, 0.5)
    e = EL['ice']
    for k, y in enumerate((0.34, 0.52, 0.70)):
        path = [(0.08 + 0.84 * t / 40, y + 0.06 * math.sin(t / 40 * math.pi * 2.2 + k)) for t in range(41)]
        m = tubem(path, 0.02, 0.07)
        lit(c, m, e.hi, e.mid, glowc=e.glow, gr=12, gs=1.3)
    for x, y, r in ((0.30, 0.20, 0.07), (0.72, 0.84, 0.06), (0.20, 0.82, 0.05)):
        flake(c, x, y, r)
    arrow_mark(c, 0.78, 0.18, 0.18, False, EL['blood'])
    return K.finish(c)


def poison_breath():
    """A gout of poisonous breath."""
    c = bg(110, 0.55, 0.35)
    e = EL['poison']
    cone(c, 0.46, 0.52, -8, 0.52, 30, e, 3)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((120, 150, 90), (30, 50, 20)), eyec=(255, 240, 80), rimc=(200, 255, 120))
    motes(c, 6, 10, (0.5, 0.2, 0.9, 0.8), (0.008, 0.015), (240, 255, 180), e.glow)
    return K.finish(c)


def stinking_gas():
    """Billowing clouds of foul gas and stink lines."""
    c = bg(70, 0.6, 0.38)
    e = EL['poison']
    cloud(c, 21, (0.18, 0.44, 0.82, 0.82), e, 14, (0.09, 0.15))
    st = M(lambda d: [d.line(pts([(x + 0.03 * math.sin(t / 6 * math.pi * 2), 0.42 - 0.26 * t / 6) for t in range(7)]),
                             fill=255, width=int(0.03 * W), joint='curve') for x in (0.34, 0.5, 0.66)])
    lit(c, st, (255, 255, 200), (200, 220, 90), glowc=(220, 255, 120), gr=8, gs=1.3)
    return K.finish(c)


def memento_mori():
    """A skull wreathed in violet magic: the caster's power swells."""
    c = bg(275, 0.65, 0.40, cy=0.6)
    fl = M(lambda d: [GA.flame(d, 0.5, 0.86, 0.34, 0.80), GA.flame(d, 0.26, 0.86, 0.12, 0.48, -0.06),
                      GA.flame(d, 0.74, 0.86, 0.12, 0.50, 0.06)])
    K.glow(c, fl, (200, 100, 255, 255), 24, 1.2)
    K.fill(c, sc(soften(fl, 4), 0.75), K.linear((250, 200, 255, 255), (120, 40, 200, 255), 270))
    skull(c, 0.5, 0.56, 0.95, glowc=(220, 160, 255))
    eyes = add(ell(0.5 - 0.114, 0.56 + 0.019, 0.04), ell(0.5 + 0.114, 0.56 + 0.019, 0.04))
    lit(c, eyes, (255, 230, 255), (220, 100, 255), glowc=(230, 120, 255), gr=8, gs=1.6)
    return K.finish(c)


def ghost_hand(cx, cy, s, ang=0):
    """A long-fingered clawed hand reaching up (local), palm at (cx, cy)."""
    parts = [poly(xf([(-0.19, -0.04), (0.19, -0.04), (0.16, 0.26), (-0.14, 0.28)], cx, cy, s, ang)),
             ell(*xf([(0.0, 0.0)], cx, cy, s, ang)[0], 0.19 * s, 0.16 * s),
             poly(xf([(-0.11, 0.24), (0.12, 0.24), (0.10, 0.7), (-0.10, 0.7)], cx, cy, s, ang))]
    for k, (fx, a) in enumerate(((-0.15, -28), (-0.055, -9), (0.055, 8), (0.15, 26))):
        L = 0.36 if k in (1, 2) else 0.30
        path = [(fx + math.sin(math.radians(a)) * L * t / 12 + 0.035 * math.sin(t / 12 * 2.8) * (1 if a > 0 else -1),
                 -0.04 - math.cos(math.radians(a)) * L * t / 12) for t in range(13)]
        parts.append(poly(xf(tube(path, 0.09, 0.012), cx, cy, s, ang)))
    th = [(0.17 + 0.18 * t / 10, 0.14 - 0.14 * t / 10 - 0.05 * math.sin(t / 10 * 3)) for t in range(11)]
    parts.append(poly(xf(tube(th, 0.085, 0.012), cx, cy, s, ang)))
    return add(*parts)


def terror_touch():
    """A spectral claw reaching out of the dark."""
    c = bg(270, 0.5, 0.30, cy=0.6)
    e = EL['dark']
    wash(c, ell(0.5, 0.8, 0.45, 0.25), (130, 60, 200), 30, 0.7)
    h = ghost_hand(0.5, 0.56, 1.0)
    K.glow(c, h, A((150, 255, 210)), 20, 1.3)
    lit(c, h, (230, 255, 245), (90, 170, 160))
    motes(c, 13, 16, (0.15, 0.1, 0.85, 0.9), (0.006, 0.013), (200, 255, 230), (120, 255, 200))
    arrow_mark(c, 0.80, 0.76, 0.16, False, EL['blood'])
    return K.finish(c)


def spinal_cleave():
    """A spine cleft in two by one red stroke."""
    c = bg(355, 0.70, 0.36, cy=0.45)
    vs = bez((0.12, 0.90), (0.40, 0.50), (0.90, 0.16), 9)

    def column(seq):
        ms = []
        for i, (x, y) in enumerate(seq):
            a = math.degrees(math.atan2(seq[min(i + 1, len(seq) - 1)][1] - seq[max(i - 1, 0)][1],
                                        seq[min(i + 1, len(seq) - 1)][0] - seq[max(i - 1, 0)][0]))
            body = poly(xf([(-0.032, -0.07), (0.032, -0.07), (0.04, 0.0), (0.032, 0.07), (-0.032, 0.07),
                            (-0.04, 0.0)], x, y, 1.45, a))
            wings = add(*[ell(*xf([(0.0, sy * 0.10)], x, y, 1.45, a)[0], 0.034) for sy in (-1, 1)])
            ms.append(add(body, wings))
        return add(*ms)
    sp = column(vs)
    upper = poly([(0, 0.066), (0, 0), (1, 0), (1, 1.096)])
    lower = sub(sp, upper)
    top = ImageChops.offset(mul(sp, upper), int(0.035 * W), int(-0.035 * W))
    for part in (top, lower):
        out = part.filter(ImageFilter.MaxFilter(7))
        K.shadow(c, out, 5, 8, 8, 170)
        K.fill(c, soften(out, 1.2), (50, 10, 10, 255))
        lit(c, part, (255, 250, 236), (196, 170, 130))
        shade(c, part, 0.02, 0.02, 0.5, 3, (120, 80, 50))
    slash(c, 0.10, 0.08, 0.92, 0.96, -0.04, EL['blood'], 0.10, glowc=(255, 40, 50))
    core = tubem(bez((0.16, 0.14), (0.52, 0.50), (0.86, 0.90), 30), 0.03, taper='both')
    lit(c, core, (255, 255, 255), glowc=(255, 200, 200), gr=6)
    drops = add(drop(0.26, 0.20, 0.30, 0.035), drop(0.18, 0.34, 0.42, 0.028), drop(0.76, 0.74, 0.84, 0.03))
    lit(c, drops, (255, 120, 120), (170, 10, 30), glowc=(255, 40, 60), gr=6)
    return K.finish(c)


def blood_saber():
    """A crescent blade of blood, droplets flying."""
    c = bg(345, 0.7, 0.32)
    e = EL['blood']
    slash(c, 0.16, 0.74, 0.80, 0.14, -0.14, e, 0.14, glowc=(255, 40, 60))
    slash(c, 0.24, 0.66, 0.74, 0.20, -0.10, EL['light'], 0.04, glowc=(255, 160, 160))
    ds = add(drop(0.70, 0.52, 0.66, 0.045), drop(0.80, 0.64, 0.76, 0.035), drop(0.60, 0.70, 0.82, 0.03))
    lit(c, ds, (255, 160, 150), (180, 10, 30), glowc=(255, 50, 60), gr=8)
    return K.finish(c)


def digest():
    """A gaping ooze swallowing a glowing morsel of life."""
    c = bg(160, 0.6, 0.38)
    body = poly(bez3((0.12, 0.84), (0.10, 0.30), (0.38, 0.20), (0.56, 0.24), 20) +
                bez3((0.56, 0.24), (0.86, 0.30), (0.92, 0.70), (0.88, 0.84), 20))
    lit(c, body, rgrad((200, 255, 210), (40, 150, 110), 0.40, 0.36, 0.5), glowc=(120, 255, 190), gr=16, sh=True)
    mouth = ell(0.50, 0.58, 0.20, 0.14)
    lit(c, mouth, (30, 10, 30), (60, 20, 40))
    orb = ell(0.50, 0.58, 0.07)
    lit(c, orb, (255, 255, 255), glowc=(255, 120, 140), gr=14, gs=1.5)
    for x, y in ((0.36, 0.40), (0.62, 0.40)):
        lit(c, ell(x, y, 0.035), (255, 255, 230), soft=1)
        lit(c, ell(x + 0.01, y + 0.005, 0.016), (20, 20, 20), soft=1)
    shine(c, body, -0.02, -0.04, 0.5)
    motes(c, 14, 10, (0.15, 0.1, 0.85, 0.4), (0.008, 0.016), (220, 255, 230), (120, 255, 190))
    return K.finish(c)


def mandible(cx, cy, s, mirror, ang=0):
    seq = (bez3((0.0, 0.0), (-0.08, -0.34), (0.10, -0.56), (0.34, -0.50), 24) +
           bez3((0.34, -0.50), (0.18, -0.44), (0.10, -0.26), (0.14, 0.02), 18))
    teeth = [(0.11, -0.16), (0.11, -0.26), (0.14, -0.36)]
    m = poly(xf(seq, cx, cy, s, ang, mirror))
    t = add(*[poly(xf([(x - 0.01, y - 0.03), (x + 0.07, y), (x - 0.01, y + 0.03)], cx, cy, s, ang, mirror))
              for x, y in teeth])
    return add(m, t)


def mandibular_bite():
    """Antlion mandibles snapping shut on a burst of impact."""
    c = bg(185, 0.60, 0.40, cy=0.38)
    burst(c, 0.5, 0.34, 0.26, 0.09, 10, EL['gold'], 3)

    def jaw(sx):
        f = lambda seq: [(x, 1.0 - y) for x, y in seq]
        seq = bez3((0.5 + sx * 0.16, 0.04), (0.5 + sx * 0.46, 0.14), (0.5 + sx * 0.40, 0.58), (0.5 + sx * 0.02, 0.68), 30)
        inner = bez3((0.5 + sx * 0.02, 0.68), (0.5 + sx * 0.30, 0.54), (0.5 + sx * 0.32, 0.20), (0.5 + sx * 0.04, 0.04), 24)
        m = poly(f(seq + inner))
        teeth = add(*[poly(f([(0.5 + sx * (dx - 0.02), y - 0.035), (0.5 + sx * (dx - 0.09), y),
                              (0.5 + sx * (dx - 0.02), y + 0.035)])) for dx, y in ((0.31, 0.26), (0.30, 0.38), (0.25, 0.50))])
        return add(m, teeth)
    m = add(jaw(-1), jaw(1))
    out = m.filter(ImageFilter.MaxFilter(9))
    K.glow(c, out, (255, 214, 140, 255), 14, 1.3)
    K.shadow(c, out, 5, 8, 8, 170)
    K.fill(c, soften(out, 1.5), (40, 16, 4, 255))
    lit(c, m, rgrad((255, 236, 180), (170, 90, 30), 0.5, 0.40, 0.55))
    shine(c, m, -0.02, -0.03, 0.6, 3)
    shade(c, m, 0.03, 0.03, 0.5, 5, (90, 40, 10))
    return K.finish(c)


def cursed_sphere():
    """A sphere of black water ringed with curses."""
    c = bg(200, 0.6, 0.32)
    e = EL['water']
    rr = ring(0.5, 0.5, 0.40, 0.14, 0.022)
    back = mul(rr, poly([(0, 0), (1, 0), (1, 0.5), (0, 0.5)]))
    lit(c, back, (200, 160, 255), glowc=(170, 100, 255), gr=10)
    o = ell(0.5, 0.5, 0.26)
    lit(c, o, rgrad((140, 200, 255), (20, 30, 90), 0.42, 0.40, 0.30), glowc=(90, 120, 255), gr=22, gs=1.4, sh=True)
    sw = M(lambda d: d.line(pts([(0.5 + math.cos(t / 20 * 5) * 0.16 * t / 20, 0.5 + math.sin(t / 20 * 5) * 0.16 * t / 20)
                                 for t in range(21)]), fill=255, width=int(0.02 * W)))
    K.fill(c, sc(soften(sw, 2), 0.7), (200, 140, 255, 255))
    lit(c, ell(0.42, 0.40, 0.05, 0.03), (255, 255, 255), soft=4)
    front = mul(rr, poly([(0, 0.5), (1, 0.5), (1, 1), (0, 1)]))
    lit(c, front, (220, 190, 255), glowc=(170, 100, 255), gr=10)
    for a in (200, 270, 340, 30, 100):
        x, y = 0.5 + math.cos(math.radians(a)) * 0.40, 0.5 + math.sin(math.radians(a)) * 0.14
        lit(c, poly(star_pts(x, y, 4, 0.035, 0.012)), (255, 230, 255), glowc=(200, 120, 255), gr=6)
    return K.finish(c)


def sickle_slash():
    """A mantis's sickle arm and its crescent cut."""
    c = bg(100, 0.6, 0.38)
    slash(c, 0.20, 0.20, 0.82, 0.70, 0.12, EL['light'], 0.08, glowc=(220, 255, 160))
    arm = poly(tube(bez3((0.82, 0.92), (0.72, 0.56), (0.50, 0.40), (0.30, 0.46), 30), 0.10, 0.01))
    lit(c, arm, (200, 250, 140), (60, 130, 40), glowc=(200, 255, 140), gr=10, sh=True)
    teeth = add(*[poly(xf([(0, 0), (0.025, 0.05), (-0.02, 0.04)], x, y, 1.0)) for x, y in
                  ((0.42, 0.47), (0.50, 0.46), (0.58, 0.49), (0.65, 0.54))])
    lit(c, teeth, (250, 255, 220), (150, 190, 100), soft=1)
    shine(c, arm, 0, -0.02, 0.45)
    return K.finish(c)


def cocoon():
    """Showpiece: a silk cocoon shining with protection."""
    c = bg(255, 0.45, 0.42, cy=0.5)
    rays(c, 0.5, 0.52, 14, (255, 240, 200), alpha=60)
    thread = tubem([(0.5, 0.0), (0.5, 0.18)], 0.012)
    lit(c, thread, (255, 255, 255), glowc=(255, 255, 255), gr=6)
    shape_ = [(0.5 + 0.21 * math.sin(math.pi * t / 40) ** 0.8 * (1 - 0.15 * t / 40), 0.16 + 0.70 * t / 40)
              for t in range(41)]
    body = poly(shape_ + [(1 - x, y) for x, y in shape_[::-1]])
    lit(c, body, rgrad((255, 255, 245), (210, 190, 160), 0.44, 0.40, 0.36), glowc=(255, 230, 170), gr=24, gs=1.4,
        sh=True)
    wraps = M(lambda d: [d.line(pts([(0.27, 0.22 + k * 0.085 + 0.05), (0.73, 0.22 + k * 0.085 - 0.03)]), fill=255,
                                width=int(0.016 * W)) for k in range(8)])
    K.fill(c, sc(soften(mul(wraps, body), 2), 0.45), (150, 120, 90, 255))
    shade(c, body, 0.05, 0.03, 0.4, 10, (120, 90, 80))
    K.fill(c, sc(blur(mul(ell(0.42, 0.40, 0.06, 0.18), body), 8), 0.7), (255, 255, 255, 255))
    gl = ring(0.5, 0.52, 0.40, 0.40, 0.012)
    lit(c, gl, (255, 240, 200), glowc=(255, 220, 140), gr=10, gs=1.2)
    sparkles(c, [(0.78, 0.26, 0.07), (0.22, 0.72, 0.06)], (255, 230, 170))
    return K.finish(c)


def filamented_hold():
    """Sticky filaments strung across, dewed and binding."""
    c = bg(230, 0.45, 0.35)
    cx, cy = 0.48, 0.46
    spokes = [math.radians(a) for a in range(-80, 280, 45)]
    m = M(lambda d: [d.line(pts([(cx, cy), (cx + math.cos(a) * 0.6, cy + math.sin(a) * 0.6)]), fill=255,
                            width=int(0.014 * W)) for a in spokes] +
          [d.line(pts([(cx + math.cos(spokes[k % 8]) * r * (1 + 0.1 * (k % 2)), cy + math.sin(spokes[k % 8]) * r)
                       for k in range(9)]), fill=255, width=int(0.012 * W)) for r in (0.12, 0.22, 0.32, 0.42)])
    lit(c, m, (255, 255, 255), (200, 220, 255), glowc=(180, 220, 255), gr=6, gs=1.3)
    dw = dots(5, 12, (0.15, 0.12, 0.85, 0.85), (0.012, 0.02))
    lit(c, mul(dw, blur(m, 6).point(lambda v: 255 if v > 30 else 0)), (255, 255, 255), glowc=(200, 240, 255), gr=6)
    return K.finish(c)


def pollen():
    """A blossom shedding healing pollen."""
    c = bg(140, 0.6, 0.45)
    motes(c, 3, 30, (0.12, 0.08, 0.88, 0.6), (0.007, 0.016), (255, 250, 180), (255, 230, 90))
    flower(c, 0.5, 0.58, 0.30, (255, 220, 240), (240, 110, 170), (255, 200, 60), 5)
    lv = add(leafm(0.5, 0.80, -160, 0.26, 0.07), leafm(0.5, 0.80, -20, 0.26, 0.07))
    lit(c, lv, (170, 240, 140), (50, 140, 60), sh=True)
    flower(c, 0.5, 0.58, 0.30, (255, 230, 245), (240, 110, 170), (255, 200, 60), 5)
    K.fill(c, sc(soften(M(lambda d: GA.cross(d, 0.80, 0.22, 0.30))), 1.0), (230, 255, 230, 255))
    K.glow(c, M(lambda d: GA.cross(d, 0.80, 0.22, 0.30)), (120, 255, 160, 255), 10, 1.2)
    return K.finish(c)


def power_attack():
    """A beetle's horn ramming home."""
    c = bg(40, 0.6, 0.40)
    impact(c, 0.70, 0.34, 0.24, EL['gold'], 9, 7)
    shell_ = ell(0.36, 0.64, 0.25, 0.20)
    hornm = poly(tube(bez((0.48, 0.58), (0.60, 0.50), (0.70, 0.34)), 0.12, 0.01))
    m = add(rot(shell_, 30, 0.36, 0.64), hornm)
    legs = M(lambda d: [d.line(pts([(x, y), (x - 0.06, y + 0.12), (x - 0.10, y + 0.14)]), fill=255,
                               width=int(0.02 * W)) for x, y in ((0.30, 0.76), (0.42, 0.74), (0.52, 0.68))])
    lit(c, legs, (40, 60, 40), (10, 20, 10))
    lit(c, m, rgrad((150, 255, 190), (10, 70, 50), 0.30, 0.52, 0.35), glowc=(255, 210, 140), gr=12, sh=True)
    K.fill(c, sc(soften(tubem([(0.20, 0.52), (0.46, 0.80)], 0.012)), 0.7), (20, 10, 40, 255))
    shine(c, m, -0.02, -0.03, 0.5)
    speed(c, -35, [(0.16, 0.48, 0.14), (0.22, 0.86, 0.12)], (255, 240, 200))
    return K.finish(c)


def crab_claw(cx, cy, s, ang=0, gape=1.0):
    """A crab claw opening toward +x: palm, fixed lower finger, movable upper finger, arm off to the lower left."""
    palm = poly(xf(arcp(0, 0, 0.22, 0.17, 0, 360, 40), cx, cy, s, ang))
    up = poly(xf(tube(bez((0.06, -0.08), (0.34, -0.30 * gape), (0.56, -0.08 * gape), 20), 0.16, 0.01), cx, cy, s, ang))
    lo = poly(xf(tube(bez((0.08, 0.08), (0.34, 0.24), (0.54, 0.08), 20), 0.15, 0.01), cx, cy, s, ang))
    arm = poly(xf(tube([(-0.12, 0.08), (-0.40, 0.34)], 0.14, 0.12), cx, cy, s, ang))
    teeth = add(*[poly(xf([(x - 0.025, y), (x, y + dy), (x + 0.025, y)], cx, cy, s, ang))
                  for x, y, dy in ((0.22, -0.12 * gape - 0.03, 0.06), (0.32, -0.10 * gape - 0.02, 0.05),
                                   (0.22, 0.09, -0.05), (0.32, 0.075, -0.045))])
    return add(palm, up, lo, arm), teeth


def death_scissors():
    """A crab's great pincers scissoring shut."""
    c = bg(195, 0.6, 0.38)
    m, t = crab_claw(0.32, 0.58, 1.0, -12, 1.7)
    lit(c, m, (255, 150, 110), (170, 40, 30), glowc=(255, 140, 100), gr=12, sh=True)
    lit(c, t, (255, 240, 220), (220, 160, 130), soft=1)
    shine(c, m, -0.01, -0.025, 0.5)
    shade(c, m, 0.02, 0.04, 0.4, 6, (90, 10, 10))
    sparkles(c, [(0.80, 0.40, 0.10)], (255, 240, 200))
    return K.finish(c)


def magnet(cx, cy, s, ang=0):
    arc_ = arcp(0, 0, 0.22, 0.22, 180, 360, 30)
    outer = [(-0.22, 0.25)] + arc_ + [(0.22, 0.25)]
    pathm = poly(xf(tube(outer, 0.14), cx, cy, s, ang))
    tips = add(poly(xf([(-0.29, 0.10), (-0.15, 0.10), (-0.15, 0.30), (-0.29, 0.30)], cx, cy, s, ang)),
               poly(xf([(0.15, 0.10), (0.29, 0.10), (0.29, 0.30), (0.15, 0.30)], cx, cy, s, ang)))
    return pathm, tips


def magnetite_cloud():
    """A cloud of magnetic dust around a lodestone magnet."""
    c = bg(30, 0.45, 0.32)
    e = EL['earth']
    cloud(c, 31, (0.12, 0.20, 0.88, 0.85), e, 16, (0.08, 0.13), 0.8)
    field = M(lambda d: [d.arc(pts([(0.5 - r, 0.50 - r * 0.7), (0.5 + r, 0.50 + r * 0.7)]), 200, 340, fill=255,
                               width=int(0.012 * W)) for r in (0.32, 0.40)])
    lit(c, field, (255, 240, 200), glowc=(255, 210, 140), gr=6)
    pm, tips = magnet(0.5, 0.48, 1.0)
    lit(c, pm, (255, 110, 100), (160, 20, 30), glowc=(255, 210, 140), gr=12, sh=True)
    lit(c, tips, (250, 250, 255), (150, 160, 180))
    shine(c, pm, -0.01, -0.02, 0.45)
    return K.finish(c)


def eyes_on_me():
    """A hypnotic eye whose gaze wounds."""
    c = bg(300, 0.6, 0.35)
    rays(c, 0.5, 0.5, 16, (255, 160, 230), alpha=70)
    eye(c, 0.5, 0.50, 0.36, 0.20, (220, 40, 160), slit=False, lid=(60, 10, 50), glowc=(255, 120, 220), ir=0.15)
    sw = M(lambda d: d.line(pts([(0.5 + math.cos(t / 30 * 9) * 0.13 * t / 30, 0.5 + math.sin(t / 30 * 9) * 0.13 * t / 30)
                                 for t in range(31)]), fill=255, width=int(0.016 * W)))
    K.fill(c, sc(soften(sw, 1.5), 0.85), (255, 220, 250, 255))
    return K.finish(c)


SPELLS.update({
    'Refueling': refueling, 'Ice Break': ice_break, 'Blitzstrahl': blitzstrahl, 'Self-Destruct': self_destruct,
    'Mysterious Light': mysterious_light, 'Cold Wave': cold_wave, 'Poison Breath': poison_breath,
    'Stinking Gas': stinking_gas, 'Memento Mori': memento_mori, 'Terror Touch': terror_touch,
    'Spinal Cleave': spinal_cleave, 'Blood Saber': blood_saber, 'Digest': digest, 'Mandibular Bite': mandibular_bite,
    'Cursed Sphere': cursed_sphere, 'Sickle Slash': sickle_slash, 'Cocoon': cocoon, 'Filamented Hold': filamented_hold,
    'Pollen': pollen, 'Power Attack': power_attack, 'Death Scissors': death_scissors,
    'Magnetite Cloud': magnetite_cloud, 'Eyes On Me': eyes_on_me,
})
def frenetic_rip():
    """A frenzy of ripping claws, three rakes over three."""
    c = bg(350, 0.75, 0.38)
    e = EL['blood']
    wash(c, ell(0.5, 0.5, 0.36), (255, 60, 60), 30, 0.5)
    claws(c, 3, 0.70, 0.12, 0.26, 0.80, EL['light'], 0.10, 0.03, 0.05)
    claws(c, 3, 0.20, 0.20, 0.78, 0.76, e, 0.13, -0.04, 0.09)
    sparkles(c, [(0.80, 0.80, 0.06), (0.20, 0.82, 0.05)], (255, 120, 120))
    return K.finish(c)


def frightful_roar():
    """A beast's roar that shakes its foes' guard loose."""
    c = bg(330, 0.5, 0.36)
    waves(c, 0.42, 0.52, -10, (0.18, 0.29, 0.40), EL['gold'], 45, 0.04)
    maw(c, 0.46, 0.54, 1.0, -12, skin=((200, 140, 110), (80, 40, 30)), eyec=(255, 230, 80), rimc=(255, 200, 140))
    arrow_mark(c, 0.78, 0.78, 0.16, False, EL['blood'])
    return K.finish(c)


def hecatomb_wave():
    """A towering crescent of wind sweeping all before it."""
    c = bg(150, 0.6, 0.38)
    e = EL['wind']
    for k, (r, w) in enumerate(((0.40, 0.11), (0.28, 0.07), (0.17, 0.04))):
        path = arcp(0.62, 0.62, r, r, 150, 330, 40)
        m = tubem(path, 0.01, w)
        lit(c, m, e.hi, e.mid, glowc=e.glow, gr=14, gs=1.3)
    speed(c, 200, [(0.20, 0.80, 0.2), (0.36, 0.88, 0.18)], (220, 255, 230))
    motes(c, 18, 12, (0.1, 0.1, 0.9, 0.9), (0.006, 0.012), (230, 255, 240), e.glow)
    return K.finish(c)


def body_slam():
    """A huge body crashing down, the ground cracking beneath."""
    c = bg(210, 0.5, 0.40, cy=0.75)
    e = EL['earth']
    impact(c, 0.5, 0.80, 0.40, EL['gold'], 12, 6, 0.3)
    shockring(c, 0.5, 0.82, 0.42, 0.10, EL['gold'], 0.03)
    cr = M(lambda d: [d.line(pts([(0.5, 0.82), (0.5 + math.cos(a) * 0.36, 0.82 + math.sin(a) * 0.09)]), fill=255,
                             width=int(0.014 * W)) for a in [math.pi * k / 4 for k in range(8)]])
    K.fill(c, sc(soften(cr), 0.8), (40, 20, 10, 255))
    body = sub(ell(0.5, 0.48, 0.34, 0.30), poly([(0, 0.72), (1, 0.72), (1, 1), (0, 1)]))
    lit(c, body, rgrad((150, 230, 220), (20, 80, 90), 0.40, 0.34, 0.42), glowc=(160, 255, 230), gr=14, sh=True)
    scales = M(lambda d: [d.arc(pts([(x - 0.05, y - 0.03), (x + 0.05, y + 0.05)]), 0, 180, fill=255,
                                width=int(0.01 * W)) for x in (0.3, 0.4, 0.5, 0.6, 0.7) for y in (0.36, 0.48, 0.60)])
    K.fill(c, sc(soften(mul(scales, body)), 0.35), (10, 40, 50, 255))
    belly = mul(ell(0.5, 0.66, 0.22, 0.14), body)
    K.fill(c, sc(soften(belly, 6), 0.7), (240, 230, 190, 255))
    shine(c, body, -0.02, -0.04, 0.4)
    arms = add(rot(ell(0.17, 0.52, 0.10, 0.05), -30, 0.17, 0.52), rot(ell(0.83, 0.52, 0.10, 0.05), 30, 0.83, 0.52))
    lit(c, arms, (150, 230, 220), (20, 80, 90), sh=True)
    sq = M(lambda d: [d.line(pts([(0.36, 0.30), (0.43, 0.34), (0.36, 0.38)]), fill=255, width=int(0.022 * W)),
                      d.line(pts([(0.64, 0.30), (0.57, 0.34), (0.64, 0.38)]), fill=255, width=int(0.022 * W))])
    lit(c, sq, (10, 30, 40), soft=1)
    speed(c, 90, [(0.16, 0.36, 0.2), (0.84, 0.36, 0.2), (0.24, 0.20, 0.15), (0.76, 0.20, 0.15)], (230, 240, 255))
    rocks = add(poly([(0.12, 0.72), (0.18, 0.64), (0.22, 0.72)]), poly([(0.80, 0.70), (0.86, 0.62), (0.90, 0.72)]))
    lit(c, rocks, (230, 200, 160), (120, 90, 60))
    return K.finish(c)


def radiant_breath():
    """A wyrm's breath of searing light."""
    c = bg(45, 0.55, 0.42)
    e = EL['light']
    cone(c, 0.46, 0.52, -8, 0.52, 28, e, 7)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((240, 220, 180), (130, 100, 60)), eyec=(140, 230, 255), rimc=(255, 240, 200))
    sparkles(c, [(0.82, 0.30, 0.07), (0.74, 0.74, 0.05)], (255, 240, 180))
    return K.finish(c)


def bird(cx, cy, s, ang, wing=1.0):
    """A falcon in a stoop, wings folded back: local +x is forward (the beak)."""
    body = (bez3((0.42, 0.0), (0.30, -0.12), (0.0, -0.13), (-0.40, -0.04), 20) + [(-0.56, -0.10), (-0.52, 0.0),
                                                                                (-0.56, 0.10)] +
            bez3((-0.40, 0.04), (0.0, 0.12), (0.30, 0.11), (0.42, 0.0), 20))
    w = bez3((0.10, -0.06), (-0.10, -0.40 * wing), (-0.40, -0.40 * wing), (-0.66, -0.30 * wing), 20) + \
        bez3((-0.66, -0.30 * wing), (-0.40, -0.22 * wing), (-0.20, -0.10), (-0.10, -0.02), 12)
    beak = [(0.40, -0.04), (0.52, 0.03), (0.38, 0.05)]
    return add(poly(xf(body, cx, cy, s, ang)), poly(xf(w, cx, cy, s, ang)), poly(xf(beak, cx, cy, s, ang)))


def helldive():
    """A bird of prey plunging, trailing fire."""
    c = bg(15, 0.7, 0.40, cx=0.7, cy=0.7)
    e = EL['fire']
    trail = poly(tube([(0.10, 0.10), (0.56, 0.58)], 0.02, 0.22))
    K.glow(c, trail, A(e.glow), 20, 1.2)
    K.fill(c, sc(blur(trail, 8), 0.8), K.linear(A(e.lo), A(e.hi), 45))
    impact(c, 0.74, 0.76, 0.18, EL['gold'], 8, 3)
    m = bird(0.52, 0.52, 0.80, 45, 1.0)
    lit(c, m, (255, 250, 235), (200, 160, 120), glowc=(255, 220, 150), gr=12, gs=1.3, sh=True)
    shade(c, m, 0.02, -0.03, 0.55, 5, (110, 50, 20))
    lit(c, ell(0.665, 0.635, 0.016), (30, 10, 10), soft=1)
    shine(c, m, -0.01, -0.02, 0.4)
    return K.finish(c)


def jet_stream():
    """Three jets of wind tearing past at once."""
    c = bg(175, 0.6, 0.40)
    e = EL['wind']
    for k, y in enumerate((0.30, 0.50, 0.70)):
        x0 = 0.12 + 0.06 * (k % 2)
        m = poly(tube([(x0 + 0.70 * t / 20, y - 0.10 + 0.20 * t / 20 - 0.04 * math.sin(math.pi * t / 20))
                       for t in range(21)], 0.01, 0.08))
        lit(c, m, e.hi, e.mid, glowc=e.glow, gr=12, gs=1.3, ang=0)
        tip = ell(x0 + 0.70, y + 0.10, 0.04)
        lit(c, tip, (255, 255, 255), glowc=(255, 255, 255), gr=8, gs=1.4)
    return K.finish(c)


def bat(cx, cy, s):
    body = ell(cx, cy, 0.10 * s, 0.13 * s)
    ears = add(poly(xf([(-0.08, -0.08), (-0.06, -0.22), (-0.01, -0.10)], cx, cy, s)),
               poly(xf([(0.08, -0.08), (0.06, -0.22), (0.01, -0.10)], cx, cy, s)))
    wings = []
    for m_ in (1, -1):
        wings.append(poly(xf([(0.06, -0.06), (0.30, -0.18), (0.48, -0.10), (0.46, 0.04), (0.38, 0.0), (0.34, 0.10),
                              (0.24, 0.04), (0.18, 0.12), (0.06, 0.06)], cx, cy, s, 0, m_)))
    return add(body, ears, *wings)


def blood_drain():
    """A bat's fangs drawing a drop of blood."""
    c = bg(340, 0.65, 0.35)
    m = bat(0.5, 0.36, 1.25)
    lit(c, m, (110, 70, 120), (30, 15, 40), glowc=(255, 100, 120), gr=12, sh=True)
    eyes = add(ell(0.465, 0.33, 0.016), ell(0.535, 0.33, 0.016))
    lit(c, eyes, (255, 80, 80), glowc=(255, 60, 60), gr=4, gs=1.5)
    fangs = add(poly([(0.465, 0.42), (0.485, 0.42), (0.475, 0.49)]), poly([(0.515, 0.42), (0.535, 0.42), (0.525, 0.49)]))
    lit(c, fangs, (255, 255, 255), soft=1)
    d = drop(0.5, 0.52, 0.86, 0.13)
    lit(c, d, rgrad((255, 150, 150), (180, 10, 30), 0.46, 0.68, 0.18), glowc=(255, 40, 60), gr=16, gs=1.3, sh=True)
    lit(c, ell(0.47, 0.70, 0.02, 0.04), (255, 230, 230), soft=3)
    return K.finish(c)


def sound_blast():
    """A bat's shriek blasting out in rings."""
    c = bg(230, 0.55, 0.38)
    waves(c, 0.36, 0.56, -10, (0.22, 0.34, 0.46, 0.58), EL['blu'], 40, 0.035)
    m = bat(0.30, 0.56, 0.80)
    lit(c, m, (190, 160, 220), (60, 40, 90), glowc=(160, 200, 255), gr=10, sh=True)
    lit(c, add(ell(0.282, 0.535, 0.012), ell(0.318, 0.535, 0.012)), (255, 240, 120), soft=1)
    arrow_mark(c, 0.80, 0.80, 0.15, False, EL['blood'])
    return K.finish(c)


def feather_tickle():
    """A feather tickling until the foe loses its edge."""
    c = bg(320, 0.45, 0.48)
    sq = M(lambda d: [d.line(pts([(x + 0.04 * math.sin(t / 8 * math.pi * 2), y - 0.12 * t / 8) for t in range(9)]),
                             fill=255, width=int(0.016 * W)) for x, y in ((0.24, 0.40), (0.34, 0.30))])
    lit(c, sq, (255, 255, 255), glowc=(255, 200, 240), gr=6)
    feather(c, 0.70, 0.80, 0.75, -40, EL['blu'], (255, 255, 255), (230, 170, 220), glowc=(255, 220, 255))
    sparkles(c, [(0.24, 0.62, 0.07), (0.42, 0.18, 0.05)], (255, 200, 240))
    arrow_mark(c, 0.20, 0.82, 0.13, False, EL['gold'])
    return K.finish(c)


def feather_barrier():
    """A fan of feathers spread as a shield."""
    c = bg(195, 0.5, 0.45, cy=0.55)
    e = EL['blu']
    for a in (-60, -30, 0, 30, 60):
        feather(c, 0.5, 0.84, 0.78, a, e, (255, 255, 255), (170, 210, 240))
    bubble(c, 0.5, 0.52, 0.42, e, 0.25)
    return K.finish(c)


def jettatura():
    """The evil eye: a glare that strikes terror."""
    c = bg(0, 0.55, 0.25)
    rays(c, 0.5, 0.5, 12, (255, 70, 60), alpha=110, width=0.08)
    eye(c, 0.5, 0.50, 0.34, 0.18, (255, 210, 40), slit=True, lid=(80, 10, 10), glowc=(255, 60, 40), ir=0.15)
    sparkles(c, [(0.20, 0.22, 0.06), (0.80, 0.78, 0.05)], (255, 80, 60))
    return K.finish(c)


def yawn():
    """A great yawn that drowses everyone near."""
    c = bg(250, 0.45, 0.42)
    face = ell(0.44, 0.56, 0.30, 0.28)
    lit(c, face, rgrad((240, 220, 200), (170, 130, 110), 0.38, 0.46, 0.34), glowc=(200, 190, 255), gr=12, sh=True)
    mouth = ell(0.44, 0.64, 0.12, 0.14)
    lit(c, mouth, (90, 20, 40), (40, 6, 20))
    tongue = ell(0.44, 0.73, 0.08, 0.05)
    K.fill(c, soften(mul(tongue, mouth), 2), (230, 100, 120, 255))
    lids = M(lambda d: [d.arc(pts([(x - 0.06, 0.40), (x + 0.06, 0.48)]), 20, 160, fill=255, width=int(0.018 * W))
                        for x in (0.34, 0.54)])
    lit(c, lids, (60, 30, 30), soft=1)
    zzz(c, 0.70, 0.36, 0.9)
    return K.finish(c)


def foot_kick():
    """A rabbit's hind foot snapping out in a kick."""
    c = bg(90, 0.45, 0.45)
    impact(c, 0.72, 0.36, 0.22, EL['gold'], 8, 11)
    leg = poly(tube(bez((0.16, 0.90), (0.26, 0.60), (0.50, 0.50)), 0.20, 0.13))
    foot_ = poly(tube(bez((0.46, 0.52), (0.60, 0.44), (0.70, 0.34)), 0.13, 0.09))
    toes = add(*[ell(0.70 + dx, 0.34 + dy, 0.04) for dx, dy in ((-0.02, -0.03), (0.02, 0.0), (0.0, 0.04))])
    m = add(leg, foot_, toes)
    lit(c, m, (255, 236, 210), (190, 140, 100), glowc=(255, 240, 200), gr=10, sh=True)
    shade(c, m, 0.03, 0.04, 0.4, 6, (120, 80, 50))
    fur = M(lambda d: [d.line(pts([(x, y), (x - 0.03, y + 0.04)]), fill=255, width=int(0.01 * W))
                       for x, y in ((0.24, 0.70), (0.30, 0.62), (0.38, 0.56), (0.22, 0.80))])
    K.fill(c, sc(soften(mul(fur, m)), 0.5), (150, 100, 60, 255))
    speed(c, -30, [(0.30, 0.40, 0.16), (0.36, 0.30, 0.14)], (255, 255, 230))
    return K.finish(c)


def carrot(c, cx, cy, s, ang=0):
    body = poly(xf([(-0.11, -0.20), (0.11, -0.20), (0.02, 0.36), (-0.02, 0.36)], cx, cy, s, ang))
    lit(c, body, (255, 190, 90), (220, 90, 20), glowc=(255, 170, 80), gr=10, sh=True)
    rings = M(lambda d: [d.line(pts(xf([(-0.09 + 0.02 * k, -0.06 + 0.1 * k), (-0.02, -0.04 + 0.1 * k)], cx, cy, s, ang)),
                                fill=255, width=int(0.012 * W * s)) for k in range(3)])
    K.fill(c, sc(soften(rings), 0.6), (170, 60, 10, 255))
    top = add(*[leafm(*xf([(0, -0.20)], cx, cy, s, ang)[0], -90 + a + ang, 0.26 * s, 0.05 * s) for a in (-30, 0, 30)])
    lit(c, top, (170, 250, 140), (40, 140, 50), sh=True)


def wild_carrot():
    """A wild carrot full of healing goodness."""
    c = bg(130, 0.55, 0.45)
    motes(c, 9, 18, (0.12, 0.1, 0.88, 0.9), (0.007, 0.016), (230, 255, 230), (130, 255, 170))
    carrot(c, 0.48, 0.52, 1.2, 25)
    cr = M(lambda d: GA.cross(d, 0.78, 0.24, 0.32))
    lit(c, cr, (255, 255, 255), (170, 250, 190), glowc=(120, 255, 160), gr=10, gs=1.3)
    return K.finish(c)


def voracious_trunk():
    """A trunk siphoning away a foe's blessings."""
    c = bg(185, 0.45, 0.38)
    path = bez3((0.10, 0.10), (0.30, 0.20), (0.30, 0.70), (0.62, 0.66), 30)
    m = tubem(path, 0.18, 0.10)
    lit(c, m, (200, 190, 220), (100, 90, 120), glowc=(160, 230, 255), gr=12, sh=True)
    folds = M(lambda d: [d.line(pts([(path[i][0] - 0.07, path[i][1]), (path[i][0] + 0.07, path[i][1] + 0.02)]), fill=255,
                                width=int(0.012 * W)) for i in (6, 10, 14, 18)])
    K.fill(c, sc(soften(mul(folds, m), 1.5), 0.5), (60, 50, 80, 255))
    tip = ell(0.63, 0.66, 0.035, 0.05)
    lit(c, tip, (40, 20, 40))
    for x, y, r in ((0.74, 0.62, 0.035), (0.82, 0.54, 0.045), (0.86, 0.40, 0.04)):
        lit(c, poly(star_pts(x, y, 4, r * 1.6, r * 0.5)), (255, 255, 230), glowc=(255, 230, 120), gr=8, gs=1.4)
    return K.finish(c)


def healing_breeze():
    """A gentle healing breeze carrying leaves."""
    c = bg(145, 0.6, 0.48)
    e = EL['heal']
    for k, (y, a) in enumerate(((0.32, 1.0), (0.52, 0.9), (0.72, 0.8))):
        path = [(0.10 + 0.80 * t / 30, y + 0.05 * math.sin(t / 30 * math.pi * 2 + k)) for t in range(31)]
        lit(c, tubem(path, 0.04, taper='both'), e.hi, glowc=e.glow, gr=10, gs=1.2)
    for x, y, a in ((0.30, 0.42, -30), (0.62, 0.30, 20), (0.70, 0.62, -60)):
        lit(c, leafm(x, y, a, 0.14, 0.045), (210, 255, 170), (60, 170, 70), sh=True)
    cr = M(lambda d: GA.cross(d, 0.5, 0.5, 0.36))
    lit(c, cr, (255, 255, 255), (180, 255, 200), glowc=(120, 255, 170), gr=14, gs=1.4)
    return K.finish(c)


def chaotic_eye():
    """A whirling eye whose gaze steals the voice."""
    c = bg(200, 0.55, 0.30)
    rays(c, 0.5, 0.5, 10, (120, 255, 220), alpha=70, phase=0.2)
    eye(c, 0.5, 0.48, 0.34, 0.18, (40, 200, 160), slit=False, lid=(10, 50, 50), glowc=(80, 255, 210), ir=0.15)
    sw = M(lambda d: d.line(pts([(0.5 + math.cos(-t / 30 * 9) * 0.13 * t / 30, 0.48 + math.sin(-t / 30 * 9) * 0.13 * t / 30)
                                 for t in range(31)]), fill=255, width=int(0.016 * W)))
    K.fill(c, sc(soften(sw, 1.5), 0.85), (200, 255, 240, 255))
    # silence: a hushed mouth-line, crossed
    sl = M(lambda d: [d.line(pts([(0.66, 0.70), (0.86, 0.86)]), fill=255, width=int(0.03 * W)),
                      d.line(pts([(0.86, 0.70), (0.66, 0.86)]), fill=255, width=int(0.03 * W))])
    lit(c, sl, (255, 200, 200), (230, 60, 60), glowc=(255, 60, 60), gr=6, sh=True)
    return K.finish(c)


def sheep(c, cx, cy, s):
    wool = add(*[ell(cx + math.cos(a) * 0.20 * s, cy + math.sin(a) * 0.16 * s, 0.10 * s)
                 for a in [math.pi * 2 * k / 9 for k in range(9)]], ell(cx, cy, 0.22 * s, 0.18 * s))
    lit(c, wool, (255, 255, 255), (200, 196, 210), glowc=(255, 240, 255), gr=12, sh=True)
    face = ell(cx + 0.02 * s, cy + 0.06 * s, 0.09 * s, 0.12 * s)
    lit(c, face, (90, 70, 70), (40, 28, 30))
    ears = add(rot(ell(cx - 0.11 * s, cy + 0.0, 0.06 * s, 0.025 * s), 20, cx - 0.11 * s, cy),
               rot(ell(cx + 0.15 * s, cy + 0.0, 0.06 * s, 0.025 * s), -20, cx + 0.15 * s, cy))
    lit(c, ears, (90, 70, 70), (40, 28, 30))
    eyes = M(lambda d: [d.arc(pts([(cx + x * s - 0.025 * s, cy + 0.02 * s), (cx + x * s + 0.025 * s, cy + 0.06 * s)]),
                              200, 340, fill=255, width=max(2, int(0.008 * W * s))) for x in (-0.02, 0.06)])
    lit(c, eyes, (255, 255, 255), soft=0.8)


def sheep_song():
    """A sheep's lullaby lulling foes to sleep."""
    c = bg(265, 0.45, 0.45)
    sheep(c, 0.50, 0.62, 1.10)
    note(c, 0.16, 0.44, 0.30, flags=1, ang=-10)
    note(c, 0.74, 0.40, 0.26, flags=2, ang=10)
    zzz(c, 0.50, 0.24, 0.55)
    return K.finish(c)


SPELLS.update({
    'Frenetic Rip': frenetic_rip, 'Frightful Roar': frightful_roar, 'Hecatomb Wave': hecatomb_wave,
    'Body Slam': body_slam, 'Radiant Breath': radiant_breath, 'Helldive': helldive, 'Jet Stream': jet_stream,
    'Blood Drain': blood_drain, 'Sound Blast': sound_blast, 'Feather Tickle': feather_tickle,
    'Feather Barrier': feather_barrier, 'Jettatura': jettatura, 'Yawn': yawn, 'Foot Kick': foot_kick,
    'Wild Carrot': wild_carrot, 'Voracious Trunk': voracious_trunk, 'Healing Breeze': healing_breeze,
    'Chaotic Eye': chaotic_eye, 'Sheep Song': sheep_song,
})
def curl_horn(cx, cy, r, turns=1.25, w=0.13, mirror=1, rot0=0):
    """A ram's spiral horn coiling inward around (cx, cy)."""
    path = []
    for i in range(61):
        t = i / 60
        a = math.radians(rot0) + t * turns * 2 * math.pi
        rr = r * (1 - 0.72 * t)
        path.append((cx + math.cos(a) * rr * mirror, cy + math.sin(a) * rr))
    return poly(tube(path, w, w * 0.25))


def ram_charge():
    """A ram lowering its curled horns and charging."""
    c = bg(30, 0.55, 0.40, cx=0.7)
    impact(c, 0.80, 0.50, 0.22, EL['gold'], 9, 2)
    speed(c, 0, [(0.30, 0.30, 0.22), (0.24, 0.50, 0.2), (0.30, 0.72, 0.22)], (255, 240, 210))
    head = poly([(0.40, 0.36), (0.62, 0.36), (0.80, 0.52), (0.78, 0.62), (0.64, 0.66), (0.44, 0.62)])
    lit(c, head, (255, 245, 235), (190, 170, 150), glowc=(255, 230, 190), gr=10, sh=True)
    h = curl_horn(0.50, 0.46, 0.20, 1.15, 0.12, -1, -60)
    lit(c, h, (240, 210, 160), (130, 90, 50), glowc=(255, 220, 160), gr=10, sh=True)
    ridges = M(lambda d: [d.line(pts([(0.50 + math.cos(a) * 0.12, 0.46 + math.sin(a) * 0.12),
                                      (0.50 + math.cos(a) * 0.24, 0.46 + math.sin(a) * 0.24)]), fill=255,
                                 width=int(0.01 * W)) for a in [math.radians(x) for x in range(-180, 120, 30)]])
    K.fill(c, sc(soften(mul(ridges, h)), 0.5), (100, 60, 30, 255))
    lit(c, ell(0.70, 0.50, 0.018), (40, 20, 10))
    return K.finish(c)


def claw_cyclone():
    """Claws whirling into a cutting cyclone."""
    c = bg(160, 0.55, 0.36)
    e = EL['wind']
    vortex(c, 0.5, 0.5, 0.40, 3, e, 0.6, 0.05, 30, hi=False)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cx, cy = 0.5 + math.cos(a) * 0.24, 0.5 + math.sin(a) * 0.24
        tx, ty = -math.sin(a), math.cos(a)
        slash(c, cx - tx * 0.16, cy - ty * 0.16, cx + tx * 0.16, cy + ty * 0.16, -0.04, EL['light'], 0.06,
              glowc=(160, 255, 200))
    return K.finish(c)


def bull_head(c, cx, cy, s, skin=((200, 170, 140), (90, 60, 40)), hornc=((255, 250, 235), (180, 160, 130))):
    hornm = add(*[poly(xf(tube(bez((0.10, -0.10), (0.42, -0.10), (0.40, -0.40)), 0.12, 0.01), cx, cy, s, 0, m_))
                  for m_ in (1, -1)])
    lit(c, hornm, hornc[0], hornc[1], glowc=(255, 255, 220), gr=8, sh=True)
    face = poly(xf([(-0.20, -0.18), (0.20, -0.18), (0.16, 0.12), (0.10, 0.30), (-0.10, 0.30), (-0.16, 0.12)], cx, cy, s))
    ears = add(*[poly(xf([(0.18, -0.14), (0.34, -0.06), (0.18, -0.02)], cx, cy, s, 0, m_)) for m_ in (1, -1)])
    m = add(face, ears)
    lit(c, m, skin[0], skin[1], sh=True)
    muzzle = ell(cx, cy + 0.22 * s, 0.12 * s, 0.09 * s)
    lit(c, muzzle, (230, 190, 180), (160, 110, 100))
    lit(c, add(ell(cx - 0.05 * s, cy + 0.23 * s, 0.022 * s), ell(cx + 0.05 * s, cy + 0.23 * s, 0.022 * s)), (40, 20, 20))
    return m


def lowing():
    """A bull's mournful lowing that carries plague."""
    c = bg(80, 0.45, 0.32)
    e = EL['poison']
    cloud(c, 41, (0.10, 0.62, 0.90, 0.92), e, 10, (0.08, 0.12), 0.8, hi=False)
    waves(c, 0.5, 0.62, 90, (0.24, 0.34), e, 35, 0.035)
    bull_head(c, 0.5, 0.42, 0.95)
    eyes = add(ell(0.44, 0.40, 0.025), ell(0.56, 0.40, 0.025))
    lit(c, eyes, (220, 255, 120), glowc=(200, 255, 80), gr=5, gs=1.5)
    return K.finish(c)


def dimensional_death():
    """A rift between worlds, a dead hand reaching through."""
    c = bg(280, 0.5, 0.22)
    rift = ell(0.5, 0.50, 0.22, 0.40)
    K.glow(c, rift, (200, 100, 255, 255), 30, 1.5)
    lit(c, rift, rgrad((20, 0, 30), (140, 60, 220), 0.5, 0.5, 0.42))
    vortex(c, 0.5, 0.5, 0.20, 3, EL['dark'], 1.0, 0.04, 0, ry=1.8, hi=False)
    h = ghost_hand(0.5, 0.62, 0.62, 0)
    lit(c, h, (240, 230, 255), (150, 120, 190), glowc=(220, 180, 255), gr=10, gs=1.2)
    edge = ring(0.5, 0.5, 0.22, 0.40, 0.02)
    lit(c, edge, (255, 220, 255), glowc=(220, 120, 255), gr=10, gs=1.4)
    return K.finish(c)


def heat_breath():
    """A wyrm's searing breath of fire."""
    c = bg(8, 0.75, 0.38)
    e = EL['fire']
    cone(c, 0.46, 0.52, -8, 0.52, 28, e, 11)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((150, 60, 50), (50, 14, 14)), eyec=(255, 230, 80), rimc=(255, 140, 60))
    motes(c, 16, 12, (0.5, 0.1, 0.95, 0.9), (0.006, 0.013), (255, 230, 150), e.glow)
    return K.finish(c)


def blank_gaze():
    """A pupil-less stare that blanks out magic."""
    c = bg(220, 0.4, 0.40)
    rays(c, 0.5, 0.5, 14, (230, 240, 255), alpha=70)
    m = M(lambda d: _eye_shape(d, 0.5, 0.48, 0.36, 0.20))
    lit(c, m, rgrad((255, 255, 255), (190, 200, 230), 0.5, 0.48, 0.3), glowc=(220, 235, 255), gr=22, gs=1.5, sh=True)
    outline = sub(M(lambda d: _eye_shape(d, 0.5, 0.48, 0.38, 0.235)), m)
    lit(c, outline, (60, 70, 110), soft=1.5)
    for x, y, r in ((0.22, 0.78, 0.04), (0.34, 0.86, 0.03), (0.70, 0.80, 0.035), (0.80, 0.70, 0.03)):
        lit(c, poly(star_pts(x, y, 4, r * 1.5, r * 0.4, -90 + 45)), (255, 255, 255), glowc=(200, 220, 255), gr=6)
    return K.finish(c)


def magic_fruit():
    """Showpiece: a glowing magical fruit brimming with healing."""
    c = bg(150, 0.65, 0.45, cy=0.5)
    rays(c, 0.5, 0.54, 16, (220, 255, 200), alpha=70)
    halo = ell(0.5, 0.56, 0.36)
    K.fill(c, sc(blur(halo, 30), 0.5), (255, 240, 170, 255))
    body = add(ell(0.40, 0.58, 0.20, 0.24), ell(0.60, 0.58, 0.20, 0.24))
    lit(c, body, rgrad((255, 250, 210), (240, 80, 120), 0.40, 0.48, 0.34), glowc=(255, 160, 180), gr=22, gs=1.4,
        sh=True)
    K.fill(c, sc(soften(tubem(bez((0.5, 0.40), (0.47, 0.58), (0.5, 0.80)), 0.012)), 0.5), (170, 30, 70, 255))
    shade(c, body, 0.05, 0.05, 0.45, 10, (130, 20, 60))
    stem = tubem(bez((0.5, 0.40), (0.50, 0.30), (0.56, 0.24)), 0.03)
    lit(c, stem, (150, 100, 60), (90, 50, 30))
    lv = leafm(0.52, 0.34, -30, 0.24, 0.07)
    lit(c, lv, (190, 255, 150), (40, 150, 60), sh=True)
    lit(c, ell(0.36, 0.48, 0.05, 0.08), (255, 255, 255), soft=6)
    cr = M(lambda d: GA.cross(d, 0.78, 0.26, 0.26))
    lit(c, cr, (255, 255, 255), (180, 255, 200), glowc=(120, 255, 170), gr=12, gs=1.4)
    sparkles(c, [(0.22, 0.30, 0.07), (0.80, 0.78, 0.05)], (255, 240, 180))
    return K.finish(c)


def uppercut():
    """A rising uppercut, launched from the hip."""
    c = bg(25, 0.6, 0.42, cy=0.3)
    impact(c, 0.58, 0.24, 0.22, EL['gold'], 9, 4)
    arc_ = M(lambda d: GA.arc_arrow(d, 0.62, 0.62, 0.34, 100, 230, 0.04, 0.06))
    lit(c, arc_, (255, 250, 220), glowc=(255, 200, 120), gr=10, gs=1.3)
    fist(c, 0.52, 0.46, 0.80, glowc=(255, 170, 90))
    speed(c, -90, [(0.40, 0.92, 0.2), (0.52, 0.96, 0.22), (0.64, 0.92, 0.2)], (255, 230, 190))
    return K.finish(c)


def cactuar(c, cx, cy, s, body=((190, 250, 130), (60, 150, 50))):
    """The cactuar's running pose."""
    head = ell(cx, cy - 0.20 * s, 0.11 * s, 0.14 * s)
    torso = ell(cx, cy + 0.02 * s, 0.10 * s, 0.14 * s)
    arm1 = tubem(xf([(-0.06, -0.04), (-0.22, -0.20)], cx, cy, s), 0.07 * s, 0.06 * s)
    arm2 = tubem(xf([(0.06, 0.02), (0.22, 0.12)], cx, cy, s), 0.07 * s, 0.06 * s)
    leg1 = tubem(xf([(-0.04, 0.12), (-0.18, 0.34)], cx, cy, s), 0.08 * s, 0.07 * s)
    leg2 = tubem(xf([(0.05, 0.12), (0.12, 0.36)], cx, cy, s), 0.08 * s, 0.07 * s)
    m = add(head, torso, arm1, arm2, leg1, leg2)
    lit(c, m, body[0], body[1], glowc=(220, 255, 160), gr=12, sh=True)
    face = add(ell(cx - 0.045 * s, cy - 0.24 * s, 0.022 * s, 0.03 * s), ell(cx + 0.045 * s, cy - 0.24 * s, 0.022 * s, 0.03 * s),
               ell(cx, cy - 0.15 * s, 0.025 * s, 0.035 * s))
    lit(c, face, (30, 50, 20), soft=1)
    return m


def thousand_needles():
    """A cactuar loosing a thousand needles."""
    c = bg(90, 0.55, 0.42)
    nd = M(lambda d: [d.polygon(pts(tube([(0.5 + math.cos(a) * 0.20, 0.52 + math.sin(a) * 0.20),
                                          (0.5 + math.cos(a) * (0.36 + 0.08 * (k % 2)),
                                           0.52 + math.sin(a) * (0.36 + 0.08 * (k % 2)))], 0.018, 0.004)), fill=255)
                      for k, a in enumerate([math.pi * 2 * i / 28 for i in range(28)])])
    lit(c, nd, (255, 255, 240), (230, 220, 160), glowc=(255, 250, 180), gr=8, gs=1.4)
    cactuar(c, 0.5, 0.54, 0.95)
    return K.finish(c)


def pinecone(c, cx, cy, s, ang=0):
    m = poly(xf([(0, -0.30)] + [(0.18 * math.sin(math.pi * t / 20) ** 0.7, -0.30 + 0.58 * t / 20) for t in range(21)] +
                [(-0.18 * math.sin(math.pi * t / 20) ** 0.7, -0.30 + 0.58 * (20 - t) / 20) for t in range(21)],
                cx, cy, s, ang))
    lit(c, m, (210, 150, 90), (100, 56, 26), glowc=(255, 200, 120), gr=10, sh=True)
    sc_ = M(lambda d: [d.arc(pts(xf([(x - 0.06, y - 0.04)], cx, cy, s, ang) + xf([(x + 0.06, y + 0.05)], cx, cy, s, ang)),
                             0, 180, fill=255, width=max(2, int(0.014 * W * s)))
                       for x, y in ((-0.06, -0.14), (0.06, -0.14), (0.0, -0.06), (-0.09, 0.02), (0.09, 0.02), (0.0, 0.10),
                                    (-0.06, 0.18), (0.06, 0.18))])
    K.fill(c, sc(soften(mul(sc_, m)), 0.7), (70, 34, 14, 255))
    shine(c, m, -0.02, -0.02, 0.35)
    return m


def pinecone_bomb():
    """A pinecone lobbed to burst and lull."""
    c = bg(110, 0.45, 0.36, cx=0.7, cy=0.7)
    burst(c, 0.72, 0.70, 0.24, 0.14, 10, EL['fire'], 6, 0.3, core=False)
    trail = M(lambda d: d.line(pts(bez((0.12, 0.82), (0.20, 0.20), (0.50, 0.34), 20)), fill=255, width=int(0.02 * W)))
    K.fill(c, sc(blur(trail, 4), 0.6), (255, 240, 200, 255))
    pinecone(c, 0.46, 0.40, 0.95, 30)
    return K.finish(c)


def sprout(c, cx, cy, s):
    stem = tubem(xf(bez((0, 0.30), (0.03, 0.10), (0, -0.05)), cx, cy, s), 0.06 * s)
    lv = add(leafm(*xf([(0, -0.03)], cx, cy, s)[0], -150, 0.30 * s, 0.11 * s),
             leafm(*xf([(0, -0.05)], cx, cy, s)[0], -30, 0.34 * s, 0.12 * s))
    m = add(stem, lv)
    lit(c, m, (210, 255, 160), (60, 160, 60), glowc=(200, 255, 150), gr=10, sh=True)
    return m


def sprout_smack():
    """A sapling swinging its leafy head in a smack."""
    c = bg(55, 0.5, 0.42)
    impact(c, 0.30, 0.30, 0.20, EL['gold'], 8, 9)
    m = sprout(c, 0.58, 0.56, 1.1)
    arc_ = M(lambda d: d.arc(pts([(0.24, 0.22), (0.84, 0.82)]), 190, 250, fill=255, width=int(0.03 * W)))
    lit(c, arc_, (255, 255, 230), glowc=(255, 230, 150), gr=8)
    pot = poly([(0.40, 0.82), (0.76, 0.82), (0.70, 0.96), (0.46, 0.96)])
    lit(c, pot, (220, 140, 90), (130, 60, 30), sh=True)
    return K.finish(c)


def soporific():
    """A drowsy flower puffing out sleep-spores."""
    c = bg(270, 0.5, 0.40)
    motes(c, 23, 26, (0.15, 0.08, 0.85, 0.5), (0.008, 0.018), (240, 220, 255), (200, 150, 255))
    st = tubem(bez((0.5, 0.95), (0.46, 0.80), (0.5, 0.62)), 0.04)
    lit(c, st, (160, 230, 120), (50, 120, 50))
    flower(c, 0.5, 0.56, 0.24, (240, 200, 255), (150, 60, 200), (255, 230, 120), 6, -90)
    zzz(c, 0.70, 0.30, 0.6)
    return K.finish(c)


def mushroom(c, cx, cy, s, cap=((240, 120, 255), (120, 30, 150)), spots=(255, 255, 230)):
    stem = poly(xf([(-0.08, 0.0), (0.08, 0.0), (0.10, 0.30), (-0.10, 0.30)], cx, cy, s))
    lit(c, stem, (255, 250, 235), (200, 186, 160), sh=True)
    capm = M(lambda d: d.chord(pts(xf([(-0.30, -0.26)], cx, cy, s) + xf([(0.30, 0.10)], cx, cy, s)), 180, 360, fill=255))
    capm = add(capm, poly(xf([(-0.30, -0.08), (0.30, -0.08), (0.28, 0.02), (-0.28, 0.02)], cx, cy, s)))
    lit(c, capm, rgrad(tuple(min(255, v + 60) for v in cap[0]), cap[1], cx - 0.08 * s, cy - 0.2 * s, 0.32 * s),
        glowc=cap[0], gr=14, gs=1.2, sh=True)
    sp = add(*[ell(cx + x * s, cy + y * s, r * s) for x, y, r in ((-0.15, -0.12, 0.05), (0.04, -0.20, 0.06),
                                                                  (0.18, -0.08, 0.045))])
    lit(c, mul(sp, capm), spots, soft=1.5)
    return capm


def queasyshroom():
    """A sickly toadstool loosing poison spores."""
    c = bg(105, 0.5, 0.32)
    e = EL['poison']
    cloud(c, 51, (0.14, 0.12, 0.86, 0.42), e, 10, (0.06, 0.1), 0.8)
    mushroom(c, 0.5, 0.58, 1.05, ((170, 230, 70), (60, 110, 20)), (250, 230, 255))
    motes(c, 52, 14, (0.12, 0.1, 0.88, 0.5), (0.007, 0.014), (230, 255, 160), e.glow)
    return K.finish(c)


SPELLS.update({
    'Ram Charge': ram_charge, 'Claw Cyclone': claw_cyclone, 'Lowing': lowing,
    'Dimensional Death': dimensional_death, 'Heat Breath': heat_breath, 'Blank Gaze': blank_gaze,
    'Magic Fruit': magic_fruit, 'Uppercut': uppercut, '1000 Needles': thousand_needles,
    'Pinecone Bomb': pinecone_bomb, 'Sprout Smack': sprout_smack, 'Soporific': soporific,
    'Queasyshroom': queasyshroom,
})
def seed_shot(c, items, col=((255, 240, 180), (190, 140, 60)), ang=-30, trail=0.14, size=(0.05, 0.028),
              glowc=(255, 230, 150)):
    """Grains / seeds flying along `ang` with short trails."""
    r = math.radians(ang)
    speed(c, ang, [(x - math.cos(r) * size[0], y - math.sin(r) * size[0], trail) for x, y in items], (255, 250, 220))
    m = add(*[rot(ell(x, y, size[0], size[1]), -ang, x, y) for x, y in items])
    lit(c, m, col[0], col[1], glowc=glowc, gr=8, gs=1.2, sh=True)
    return m


def wild_oats():
    """A volley of oat grains flung from the stalk, stinging enough to weaken."""
    c = bg(55, 0.70, 0.52, cx=0.35, cy=0.55)
    stalk = tubem(bez((0.10, 1.0), (0.14, 0.72), (0.28, 0.52)), 0.04)
    lit(c, stalk, (230, 210, 120), (130, 100, 40), sh=True)
    for x, y, a in ((0.28, 0.50, -55), (0.22, 0.60, -150), (0.31, 0.62, -25), (0.17, 0.72, -150), (0.24, 0.76, -30)):
        g = rot(ell(x, y, 0.065, 0.030), -a, x, y)
        out = g.filter(ImageFilter.MaxFilter(5))
        K.fill(c, soften(out, 1), (70, 46, 10, 255))
        lit(c, g, (255, 244, 180), (206, 156, 60), sh=True)
    for x, y in ((0.70, 0.26), (0.84, 0.46), (0.62, 0.48), (0.48, 0.30)):
        tr = tubem([(x - 0.24, y + 0.10), (x, y)], 0.004, 0.05)
        K.fill(c, sc(soften(tr, 3), 0.6), (255, 250, 220, 255))
        g = rot(ell(x, y, 0.075, 0.036), 22, x, y)
        out = g.filter(ImageFilter.MaxFilter(5))
        K.glow(c, g, (255, 230, 140, 255), 10, 1.4)
        K.fill(c, soften(out, 1), (70, 46, 10, 255))
        lit(c, g, rgrad((255, 252, 220), (220, 160, 50), x - 0.02, y - 0.015, 0.08), sh=True)
    arrow_mark(c, 0.78, 0.76, 0.20, False, EL['blood'])
    return K.finish(c)


def bad_breath():
    """A malboro's infamous breath: every ailment at once."""
    c = bg(110, 0.55, 0.30, cx=0.6)
    for k, (h, a) in enumerate(((100, -30), (290, -5), (60, 20), (180, -18))):
        e = E(hsv(h, 0.2, 1.0), hsv(h, 0.65, 0.95), hsv(h, 0.8, 0.5), hsv(h, 0.7, 1.0), h)
        cone(c, 0.44, 0.56, a, 0.54, 14, e, 30 + k, 16, 0.04, 0.12, 1.0)
    body = ell(0.28, 0.62, 0.28, 0.26)
    lit(c, body, rgrad((150, 200, 110), (40, 90, 40), 0.20, 0.52, 0.3), glowc=(180, 255, 120), gr=12, sh=True)
    mouth = rot(ell(0.38, 0.60, 0.15, 0.12), 20, 0.38, 0.60)
    lit(c, mouth, (90, 20, 40), (30, 4, 14))
    teeth = add(*[poly([(x, 0.50 + (x - 0.26) * 0.3), (x + 0.035, 0.50 + (x - 0.26) * 0.3), (x + 0.017, 0.56 + (x - 0.26) * 0.3)])
                  for x in (0.28, 0.34, 0.40, 0.46)])
    lit(c, teeth, (255, 255, 230), soft=1)
    tent = M(lambda d: [d.polygon(pts(tube([(0.10 + 0.05 * k + 0.03 * math.sin(t / 10 * 4 + k), 0.40 - 0.24 * t / 10)
                                            for t in range(11)], 0.05, 0.02)), fill=255) for k in range(4)])
    lit(c, tent, (160, 210, 120), (60, 110, 50), sh=True)
    return K.finish(c)


def geist_wall():
    """A wall of wailing spirits that strips away magic."""
    c = bg(230, 0.35, 0.28)
    wall = poly([(0.14, 0.18), (0.86, 0.18), (0.86, 0.86), (0.14, 0.86)])
    K.fill(c, sc(blur(wall, 8), 0.5), (170, 200, 255, 255))
    for x, y, s in ((0.32, 0.40, 0.8), (0.62, 0.34, 0.7), (0.48, 0.66, 0.9)):
        g = add(ell(x, y, 0.10 * s, 0.11 * s), poly([(x - 0.10 * s, y), (x + 0.10 * s, y), (x + 0.08 * s, y + 0.22 * s),
                                                       (x + 0.02 * s, y + 0.18 * s), (x - 0.04 * s, y + 0.24 * s),
                                                       (x - 0.10 * s, y + 0.18 * s)]))
        lit(c, g, (255, 255, 255), (170, 200, 240), glowc=(200, 230, 255), gr=12, gs=1.3)
        face = add(ell(x - 0.035 * s, y - 0.01 * s, 0.018 * s, 0.03 * s), ell(x + 0.035 * s, y - 0.01 * s, 0.018 * s, 0.03 * s),
                   ell(x, y + 0.06 * s, 0.025 * s, 0.035 * s))
        lit(c, face, (40, 40, 80), soft=1)
    for x, y in ((0.18, 0.22), (0.84, 0.70), (0.80, 0.20)):
        lit(c, poly(star_pts(x, y, 4, 0.05, 0.012)), (255, 255, 255), glowc=(200, 220, 255), gr=6)
    return K.finish(c)


def awful_eye():
    """A baleful eye that saps the target's strength."""
    c = bg(300, 0.45, 0.26)
    rays(c, 0.5, 0.46, 10, (200, 120, 255), alpha=80)
    eye(c, 0.5, 0.46, 0.34, 0.20, (130, 220, 60), slit=True, lid=(50, 20, 60), glowc=(190, 120, 255), ir=0.15)
    vein = M(lambda d: [d.line(pts([(x, y), (x + dx, y + dy)]), fill=255, width=int(0.01 * W))
                        for x, y, dx, dy in ((0.20, 0.46, 0.08, -0.02), (0.20, 0.46, 0.07, 0.04), (0.80, 0.46, -0.08, 0.03))])
    K.fill(c, sc(soften(vein), 0.7), (220, 40, 60, 255))
    arrow_mark(c, 0.76, 0.78, 0.16, False, EL['blood'])
    return K.finish(c)


def frost_breath():
    """A wyrm's freezing breath."""
    c = bg(205, 0.65, 0.40)
    e = EL['ice']
    cone(c, 0.46, 0.52, -8, 0.52, 28, e, 13)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((200, 230, 255), (60, 100, 160)), eyec=(140, 255, 255), rimc=(200, 240, 255))
    flake(c, 0.80, 0.30, 0.07)
    flake(c, 0.86, 0.62, 0.05)
    return K.finish(c)


def infrasonics():
    """Waves below hearing that unsettle every footing."""
    c = bg(250, 0.5, 0.32)
    e = EL['blu']
    for k, y in enumerate((0.30, 0.50, 0.70)):
        path = [(0.08 + 0.84 * t / 60, y + (0.08 - 0.02 * k) * math.sin(t / 60 * math.pi * 3 + k * 0.6)) for t in range(61)]
        lit(c, tubem(path, 0.035, taper='both'), (240, 230, 255), glowc=(170, 140, 255), gr=12, gs=1.4)
    arrow_mark(c, 0.80, 0.82, 0.14, False, EL['blood'])
    return K.finish(c)


def disseverment():
    """Five venomous cuts in quick succession."""
    c = bg(120, 0.5, 0.30)
    e = EL['poison']
    for k in range(5):
        a = -60 + k * 30
        r = math.radians(a)
        cx, cy = 0.5, 0.5
        dx, dy = math.cos(r) * 0.36, math.sin(r) * 0.36
        slash(c, cx - dx, cy - dy, cx + dx, cy + dy, 0.02, e if k % 2 else EL['light'], 0.05 + 0.01 * (k % 2),
              glowc=(170, 255, 90))
    lit(c, add(drop(0.24, 0.72, 0.86, 0.035), drop(0.76, 0.18, 0.30, 0.03)), e.hi, e.mid, glowc=e.glow, gr=8)
    return K.finish(c)


def actinic_burst():
    """A flash bright enough to blind."""
    c = bg(50, 0.5, 0.55)
    rays(c, 0.5, 0.5, 20, (255, 255, 230), alpha=110, width=0.05)
    burst(c, 0.5, 0.5, 0.42, 0.10, 8, EL['light'], 7, 0.1)
    lit(c, ell(0.5, 0.5, 0.12), (255, 255, 255), glowc=(255, 255, 255), gr=30, gs=1.8)
    return K.finish(c)


def reactor_cool():
    """A frozen core venting cold: ice spikes and hardened defenses."""
    c = bg(195, 0.6, 0.36)
    e = EL['ice']
    sp = poly(star_pts(0.5, 0.5, 12, 0.44, 0.26, -90, 0.12, 4))
    lit(c, sp, (255, 255, 255), (130, 190, 240), glowc=e.glow, gr=14, sh=True)
    hexm = poly([(0.5 + math.cos(math.radians(60 * k + 30)) * 0.22, 0.5 + math.sin(math.radians(60 * k + 30)) * 0.22)
                 for k in range(6)])
    lit(c, hexm, rgrad((255, 255, 255), (60, 150, 230), 0.46, 0.44, 0.24), glowc=(150, 230, 255), gr=12, sh=True)
    flake(c, 0.5, 0.5, 0.13)
    return K.finish(c)


def saline_coat():
    """A coat of salt crystals shielding against magic."""
    c = bg(185, 0.4, 0.42)
    bubble(c, 0.5, 0.52, 0.40, EL['blu'], 0.3)
    rnd = random.Random(6)
    for k in range(9):
        a = math.radians(-90 + k * 40 + rnd.uniform(-8, 8))
        x, y = 0.5 + math.cos(a) * 0.30, 0.52 + math.sin(a) * 0.30
        s_ = rnd.uniform(0.045, 0.07)
        cube = rot(poly([(x - s_, y - s_), (x + s_, y - s_), (x + s_, y + s_), (x - s_, y + s_)]), rnd.uniform(0, 90), x, y)
        lit(c, cube, (255, 255, 255), (190, 210, 230), glowc=(230, 245, 255), gr=6, sh=True)
    m = M(lambda d: GD.star(d, 0.5, 0.52, 0.15, 0.06, 4, -90))
    lit(c, m, (255, 255, 255), glowc=(200, 240, 255), gr=12, gs=1.4)
    return K.finish(c)


def plasma_charge():
    """A ball of plasma crackling with charge: shock spikes."""
    c = bg(275, 0.6, 0.28)
    e = EL['thunder']
    o = ell(0.5, 0.5, 0.22)
    lit(c, o, rgrad((255, 255, 255), (170, 100, 255), 0.46, 0.44, 0.24), glowc=e.glow, gr=26, gs=1.6)
    rnd = random.Random(12)
    arcs = K.mask()
    d = ImageDraw.Draw(arcs)
    for k in range(7):
        a = math.radians(k * 360 / 7 + rnd.uniform(-10, 10))
        path = [(0.5 + math.cos(a) * 0.20, 0.5 + math.sin(a) * 0.20)]
        for t in range(1, 5):
            r = 0.20 + 0.06 * t
            j = rnd.uniform(-0.25, 0.25)
            path.append((0.5 + math.cos(a + j) * r, 0.5 + math.sin(a + j) * r))
        d.line(pts(path), fill=255, width=int(0.016 * W), joint='curve')
    lit(c, arcs, (255, 255, 255), glowc=(220, 170, 255), gr=8, gs=1.5)
    return K.finish(c)


def clock(c, cx, cy, r, face=((255, 250, 230), (200, 180, 140)), rimc=((255, 230, 150), (170, 120, 40))):
    rim = ell(cx, cy, r)
    lit(c, rim, rimc[0], rimc[1], glowc=(200, 220, 255), gr=14, sh=True)
    f = ell(cx, cy, r * 0.84)
    lit(c, f, rgrad(face[0], face[1], cx - r * 0.2, cy - r * 0.2, r))
    ticks = M(lambda d: [d.line(pts([(cx + math.cos(a) * r * 0.66, cy + math.sin(a) * r * 0.66),
                                     (cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78)]), fill=255,
                                width=int(0.016 * W)) for a in [math.pi / 6 * k for k in range(12)]])
    K.fill(c, soften(ticks), (90, 70, 50, 255))
    return f


def temporal_shift():
    """Time lurches: a clock face torn by a warp that halts all nearby."""
    c = bg(230, 0.5, 0.35)
    vortex(c, 0.5, 0.5, 0.46, 4, EL['thunder'], 0.6, 0.04, 0, hi=False)
    f = clock(c, 0.5, 0.5, 0.30)
    hands = M(lambda d: [d.line(pts([(0.5, 0.5), (0.5, 0.30)]), fill=255, width=int(0.022 * W)),
                         d.line(pts([(0.5, 0.5), (0.64, 0.58)]), fill=255, width=int(0.022 * W))])
    lit(c, hands, (40, 30, 60), soft=1)
    crack = M(lambda d: d.line(pts([(0.30, 0.30), (0.42, 0.42), (0.38, 0.52), (0.52, 0.62), (0.50, 0.74), (0.62, 0.80)]),
                               fill=255, width=int(0.016 * W)))
    lit(c, mul(crack, ell(0.5, 0.5, 0.30)), (255, 255, 255), glowc=(220, 170, 255), gr=8, gs=1.5)
    return K.finish(c)


def axe(cx, cy, s, ang):
    haft = poly(xf([(-0.03, -0.42), (0.03, -0.42), (0.03, 0.46), (-0.03, 0.46)], cx, cy, s, ang))
    head = poly(xf([(0.02, -0.40), (0.18, -0.42), (0.34, -0.56)] + bez((0.34, -0.56), (0.46, -0.30), (0.34, -0.02), 12) +
                   [(0.18, -0.16), (0.02, -0.18)], cx, cy, s, ang))
    return haft, head


def vertical_cleave():
    """An axe brought straight down in a cleaving arc."""
    c = bg(30, 0.55, 0.36)
    slash(c, 0.62, 0.06, 0.62, 0.94, 0.05, EL['light'], 0.10, glowc=(255, 220, 160))
    haft, head = axe(0.36, 0.56, 0.95, -15)
    lit(c, haft, (170, 110, 70), (80, 44, 24), sh=True)
    lit(c, head, (255, 255, 255), (130, 140, 170), glowc=(220, 230, 255), gr=12, sh=True)
    shine(c, head, -0.02, -0.02, 0.5)
    return K.finish(c)


def blastbomb():
    """A bomb hurled to burst, pinning foes in place."""
    c = bg(345, 0.55, 0.32, cx=0.65, cy=0.65)
    burst(c, 0.64, 0.64, 0.34, 0.20, 11, EL['fire'], 8, 0.3, core=False)
    trail = M(lambda d: d.line(pts(bez((0.08, 0.22), (0.24, 0.10), (0.40, 0.30), 20)), fill=255, width=int(0.03 * W)))
    K.fill(c, sc(blur(trail, 5), 0.6), (255, 220, 160, 255))
    bomb(c, 0.40, 0.36, 0.16, angry=True)
    return K.finish(c)


def battle_dance():
    """Twin blades whirling in a war dance."""
    c = bg(330, 0.55, 0.38)
    ring_ = M(lambda d: [GA.arc_arrow(d, 0.5, 0.5, 0.40, 160, 300, 0.035, 0.05), GA.arc_arrow(d, 0.5, 0.5, 0.40, -20, 120, 0.035, 0.05)])
    lit(c, ring_, (255, 220, 240), glowc=(255, 120, 200), gr=10, gs=1.3)
    m = add(M(lambda d: GB.draw_sword(d, 0.5, 0.5, 0.80, 40)), M(lambda d: GB.draw_sword(d, 0.5, 0.5, 0.80, -40)))
    lit(c, m, (255, 255, 255), (150, 160, 190), glowc=(255, 200, 230), gr=12, sh=True)
    arrow_mark(c, 0.80, 0.80, 0.14, False, EL['blood'])
    return K.finish(c)


def sandspray():
    """A spray of sand flung in the eyes."""
    c = bg(40, 0.55, 0.42)
    e = EL['earth']
    cone(c, 0.12, 0.30, 20, 0.62, 18, e, 17, 30, 0.02, 0.10, 1.3)
    motes(c, 61, 50, (0.20, 0.15, 0.80, 0.70), (0.006, 0.014), (255, 240, 200), e.glow)
    m = M(lambda d: d.arc(pts([(0.52, 0.62), (0.86, 0.80)]), 200, 340, fill=255, width=int(0.03 * W)))
    lit(c, m, (60, 30, 10), soft=1.5)
    lash = M(lambda d: [d.line(pts([(0.69 + dx, 0.66), (0.69 + dx * 1.4, 0.74)]), fill=255, width=int(0.016 * W))
                        for dx in (-0.10, 0.0, 0.10)])
    lit(c, lash, (60, 30, 10), soft=1)
    tear = drop(0.80, 0.70, 0.84, 0.03)
    lit(c, tear, (220, 240, 255), (100, 160, 255))
    return K.finish(c)


def grand_slam():
    """Fists hammered into the earth, the shock spreading wide."""
    c = bg(25, 0.5, 0.36, cy=0.8)
    e = EL['earth']
    impact(c, 0.5, 0.76, 0.40, EL['gold'], 13, 21, 0.3)
    shockring(c, 0.5, 0.80, 0.44, 0.09, EL['gold'], 0.025)
    rocks = add(*[poly(star_pts(x, y, 3, r, r * 0.7, a, 0.2, int(x * 100))) for x, y, r, a in
                  ((0.18, 0.62, 0.05, 0), (0.82, 0.60, 0.06, 30), (0.30, 0.48, 0.035, 10), (0.72, 0.44, 0.04, 50))])
    lit(c, rocks, (240, 210, 170), (120, 80, 50), sh=True)
    fist(c, 0.50, 0.42, 0.95, glowc=(255, 190, 110), ang=180)
    return K.finish(c)


def head_butt():
    """A horned head ramming home, stars flying."""
    c = bg(15, 0.5, 0.40)
    impact(c, 0.70, 0.40, 0.22, EL['gold'], 9, 14)
    head = ell(0.40, 0.56, 0.26, 0.24)
    hornm = poly(tube(bez((0.48, 0.38), (0.62, 0.34), (0.70, 0.20)), 0.10, 0.01))
    hornm2 = poly(tube(bez((0.32, 0.36), (0.32, 0.22), (0.44, 0.14)), 0.09, 0.01))
    lit(c, add(hornm, hornm2), (255, 250, 230), (190, 170, 130), glowc=(255, 240, 200), gr=8, sh=True)
    lit(c, head, rgrad((170, 220, 120), (50, 110, 40), 0.34, 0.46, 0.3), glowc=(220, 255, 160), gr=10, sh=True)
    lit(c, ell(0.52, 0.54, 0.035, 0.03), (255, 255, 230), soft=1)
    lit(c, ell(0.53, 0.54, 0.016), (20, 20, 20), soft=1)
    sparkles(c, [(0.84, 0.24, 0.06), (0.86, 0.56, 0.05), (0.66, 0.16, 0.04)], (255, 240, 160))
    speed(c, -20, [(0.12, 0.70, 0.1), (0.14, 0.82, 0.08)], (255, 255, 230))
    return K.finish(c)


SPELLS.update({
    'Wild Oats': wild_oats, 'Bad Breath': bad_breath, 'Geist Wall': geist_wall, 'Awful Eye': awful_eye,
    'Frost Breath': frost_breath, 'Infrasonics': infrasonics, 'Disseverment': disseverment,
    'Actinic Burst': actinic_burst, 'Reactor Cool': reactor_cool, 'Saline Coat': saline_coat,
    'Plasma Charge': plasma_charge, 'Temporal Shift': temporal_shift, 'Vertical Cleave': vertical_cleave,
    'Blastbomb': blastbomb, 'Battle Dance': battle_dance, 'Sandspray': sandspray, 'Grand Slam': grand_slam,
    'Head Butt': head_butt,
})
def bomb_toss():
    """A lit bomb lobbed in a high arc."""
    c = bg(195, 0.6, 0.40)
    path = bez((0.10, 0.88), (0.40, -0.10), (0.86, 0.80), 30)
    dash = M(lambda d: [d.line(pts(path[i:i + 2]), fill=255, width=int(0.035 * W)) for i in range(0, 30, 3)])
    impact(c, 0.84, 0.82, 0.16, EL['fire'], 8, 3)
    bomb(c, 0.40, 0.40, 0.15)
    lit(c, mul(dash, sub(K.mask().point(lambda v: 255), ell(0.40, 0.40, 0.17))), (255, 250, 220),
        glowc=(255, 210, 140), gr=6)
    return K.finish(c)


def frypan():
    """A goblin's trusty frying pan, clanging off a skull."""
    c = bg(200, 0.4, 0.42)
    impact(c, 0.36, 0.34, 0.24, EL['gold'], 10, 5)
    pan = ell(0.42, 0.42, 0.24, 0.22)
    handle = tubem([(0.58, 0.58), (0.86, 0.88)], 0.07)
    lit(c, handle, (150, 90, 50), (70, 36, 20), sh=True)
    lit(c, pan, rgrad((150, 150, 160), (30, 30, 40), 0.34, 0.34, 0.3), glowc=(255, 230, 170), gr=12, sh=True)
    inner = ring(0.42, 0.42, 0.19, 0.175, 0.012)
    K.fill(c, sc(soften(inner), 0.8), (200, 200, 210, 255))
    lit(c, rot(ell(0.34, 0.33, 0.08, 0.03), 40, 0.34, 0.33), (255, 255, 255), soft=4)
    sparkles(c, [(0.16, 0.20, 0.06), (0.70, 0.18, 0.05)], (255, 240, 160))
    return K.finish(c)


def flying_hip_press():
    """A great rump dropping from the sky in a gale."""
    c = bg(140, 0.45, 0.40, cy=0.8)
    e = EL['wind']
    shockring(c, 0.5, 0.84, 0.40, 0.09, e, 0.03)
    shockring(c, 0.5, 0.84, 0.26, 0.055, e, 0.025)
    rump = add(ell(0.38, 0.46, 0.18, 0.20), ell(0.62, 0.46, 0.18, 0.20))
    lit(c, rump, rgrad((240, 200, 160), (140, 90, 60), 0.36, 0.38, 0.3), glowc=(200, 255, 200), gr=12, sh=True)
    K.fill(c, sc(soften(tubem([(0.5, 0.34), (0.5, 0.64)], 0.012)), 0.6), (110, 60, 40, 255))
    tail = ell(0.5, 0.30, 0.04)
    lit(c, tail, (255, 240, 220), (200, 170, 140))
    speed(c, 90, [(0.24, 0.24, 0.18), (0.76, 0.24, 0.18), (0.5, 0.12, 0.1)], (230, 255, 230))
    return K.finish(c)


def hydro_shot():
    """A high-pressure bolt of water."""
    c = bg(210, 0.65, 0.38)
    e = EL['water']
    beam(c, 0.10, 0.80, 0.70, 0.36, e, 0.03, 0.10)
    o = ell(0.70, 0.36, 0.12)
    lit(c, o, rgrad((255, 255, 255), (60, 140, 255), 0.66, 0.32, 0.13), glowc=e.glow, gr=16, gs=1.4)
    spl = add(*[drop(0.70 + math.cos(a) * 0.18, 0.36 + math.sin(a) * 0.18 - 0.03, 0.36 + math.sin(a) * 0.18 + 0.04, 0.025)
                for a in [math.radians(x) for x in (-80, -30, 20, 70)]])
    lit(c, spl, e.hi, e.mid, glowc=e.glow, gr=6)
    return K.finish(c)


def gem(c, cx, cy, w, h, body=((255, 255, 255), (150, 210, 255)), dark=(90, 150, 220), glowc=(180, 230, 255)):
    """A brilliant-cut gem: crown above a girdle, pavilion to the point."""
    top, gir, bot = cy - h * 0.40, cy - h * 0.10, cy + h * 0.60
    whole = poly([(cx - w * 0.6, top), (cx + w * 0.6, top), (cx + w, gir), (cx, bot), (cx - w, gir)])
    lit(c, whole, body[0], body[1], glowc=glowc, gr=24, gs=1.5, sh=True)
    facets = [([(cx - w * 0.6, top), (cx - w * 0.2, top), (cx - w * 0.45, gir), (cx - w, gir)], 0.0),
              ([(cx - w * 0.2, top), (cx + w * 0.2, top), (cx, gir)], 1.0),
              ([(cx + w * 0.2, top), (cx + w * 0.6, top), (cx + w, gir), (cx + w * 0.45, gir)], 0.35),
              ([(cx - w, gir), (cx - w * 0.45, gir), (cx, bot)], 0.15),
              ([(cx - w * 0.45, gir), (cx, gir), (cx, bot)], 0.85),
              ([(cx, gir), (cx + w * 0.45, gir), (cx, bot)], 0.5),
              ([(cx + w * 0.45, gir), (cx + w, gir), (cx, bot)], 0.0)]
    for f, t in facets:
        col = tuple(int(dark[i] + (body[0][i] - dark[i]) * t) for i in range(3))
        K.fill(c, sc(soften(poly(f), 1.5), 0.85), A(col))
    edges = M(lambda d: [d.line(pts(f + [f[0]]), fill=255, width=max(2, int(0.008 * W))) for f, _ in facets])
    K.fill(c, sc(soften(mul(edges, whole)), 0.6), (255, 255, 255, 255))
    return whole


def diamondhide():
    """Showpiece: skin turned to diamond, a brilliant gem shielding the party."""
    c = bg(200, 0.55, 0.40, cy=0.5)
    rays(c, 0.5, 0.48, 16, (210, 240, 255), alpha=90, width=0.05)
    for a in (0, 120, 240):
        r = math.radians(a + 90)
        x, y = 0.5 + math.cos(r) * 0.34, 0.50 + math.sin(r) * 0.30
        if a == 0:
            continue
        gem(c, x, y + 0.04, 0.09, 0.16, glowc=(160, 220, 255))
    gem(c, 0.5, 0.46, 0.26, 0.48)
    sparkles(c, [(0.36, 0.30, 0.09), (0.70, 0.56, 0.06), (0.82, 0.24, 0.05)], (200, 240, 255))
    return K.finish(c)


def enervation():
    """Dark tendrils sapping a foe's guard and wards."""
    c = bg(285, 0.5, 0.25)
    e = EL['dark']
    sh_ = M(lambda d: GB.draw_shield(d, 0.5, 0.50, 0.90))
    lit(c, sh_, (190, 190, 210), (80, 80, 110), glowc=(170, 100, 255), gr=12, sh=True)
    crack = M(lambda d: d.line(pts([(0.46, 0.14), (0.52, 0.30), (0.44, 0.42), (0.56, 0.56), (0.50, 0.72)]), fill=255,
                               width=int(0.02 * W)))
    K.fill(c, soften(mul(crack, sh_)), (30, 10, 40, 255))
    for k in range(3):
        x0 = 0.18 + 0.32 * k
        path = [(x0 + 0.06 * math.sin(t / 10 * 5 + k), 0.98 - 0.50 * t / 10) for t in range(11)]
        lit(c, tubem(path, 0.07, 0.01), (220, 160, 255), (110, 40, 170), glowc=(170, 80, 255), gr=10, gs=1.3)
    arrow_mark(c, 0.80, 0.22, 0.14, False, EL['blood'])
    return K.finish(c)


def light_of_penance():
    """A searing glyph of judgement that blinds and humbles."""
    c = bg(45, 0.45, 0.45)
    rays(c, 0.5, 0.5, 12, (255, 250, 220), alpha=110, width=0.07)
    hal = ring(0.5, 0.5, 0.30, 0.30, 0.03)
    lit(c, hal, (255, 250, 220), glowc=(255, 240, 180), gr=14, gs=1.4)
    m = M(lambda d: [GA.cross(d, 0.5, 0.5, 0.80)])
    m = rot(m, 45)
    lit(c, m, (255, 255, 255), (255, 230, 150), glowc=(255, 240, 180), gr=22, gs=1.5, sh=True)
    lit(c, ell(0.5, 0.5, 0.06), (255, 255, 255), glowc=(255, 255, 255), gr=12, gs=1.6)
    return K.finish(c)


def warm_up():
    """A flexed arm steaming with readiness: sharper aim and footwork."""
    c = bg(15, 0.55, 0.45)
    heat = M(lambda d: [d.line(pts([(x + 0.03 * math.sin(t / 8 * 6), 0.40 - 0.28 * t / 8) for t in range(9)]), fill=255,
                               width=int(0.025 * W), joint='curve') for x in (0.30, 0.46, 0.62)])
    lit(c, heat, (255, 230, 200), glowc=(255, 150, 90), gr=8, gs=1.2)
    upper = tubem([(0.16, 0.82), (0.50, 0.72)], 0.16, 0.18)
    fore = tubem([(0.50, 0.74), (0.62, 0.44)], 0.15, 0.13)
    bicep = ell(0.36, 0.68, 0.14, 0.11)
    fistm = ell(0.64, 0.40, 0.09, 0.08)
    m = add(upper, fore, bicep, fistm)
    lit(c, m, (255, 220, 180), (200, 120, 80), glowc=(255, 160, 100), gr=12, sh=True)
    shade(c, m, 0.02, 0.04, 0.4, 6, (120, 50, 30))
    arrow_mark(c, 0.82, 0.70, 0.14, True, EL['gold'])
    arrow_mark(c, 0.82, 0.46, 0.12, True, EL['gold'])
    return K.finish(c)


def firespit():
    """A gob of fire spat in a blazing arc."""
    c = bg(5, 0.7, 0.35)
    e = EL['fire']
    fl = M(lambda d: GA.flame(d, 0.0, 0.0, 0.0, 0.0))
    glob = add(ell(0.62, 0.40, 0.14), poly([(0.52, 0.30), (0.14, 0.86), (0.18, 0.88), (0.72, 0.50)]))
    K.glow(c, glob, A(e.glow), 24, 1.3)
    lit(c, sub(glob, ell(0.62, 0.40, 0.14)), rgrad(e.hi, e.lo, 0.62, 0.40, 0.7), soft=6)
    lit(c, ell(0.62, 0.40, 0.14), rgrad((255, 255, 230), e.mid, 0.58, 0.36, 0.16), glowc=e.glow, gr=16, gs=1.4)
    motes(c, 71, 14, (0.2, 0.3, 0.8, 0.8), (0.008, 0.016), (255, 230, 150), e.glow)
    return K.finish(c)


def feather_storm():
    """A storm of poisoned feathers."""
    c = bg(150, 0.45, 0.35)
    vortex(c, 0.5, 0.5, 0.44, 3, EL['poison'], 0.7, 0.04, 10, hi=False)
    for x, y, a, s_ in ((0.30, 0.40, -40, 0.45), (0.66, 0.30, 30, 0.40), (0.54, 0.70, 110, 0.45), (0.28, 0.76, -120, 0.35),
                        (0.78, 0.62, 60, 0.35)):
        feather(c, x, y + 0.2 * s_, s_, a, EL['poison'], (255, 255, 240), (200, 230, 150))
    return K.finish(c)


def tail_slap():
    """A scaly tail whipping round with stunning force."""
    c = bg(35, 0.6, 0.40)
    sparkles(c, [(0.74, 0.22, 0.07), (0.84, 0.36, 0.05), (0.62, 0.16, 0.05)], (255, 240, 140))
    path = bez3((0.06, 0.90), (0.40, 0.84), (0.80, 0.70), (0.70, 0.30), 40)
    m = tubem(path, 0.22, 0.02)
    lit(c, m, (200, 255, 150), (60, 150, 50), glowc=(220, 255, 160), gr=12, sh=True)
    scales = M(lambda d: [d.arc(pts([(x - 0.04, y - 0.03), (x + 0.04, y + 0.03)]), 200, 340, fill=255,
                                width=int(0.01 * W)) for x, y in path[3:36:4]])
    K.fill(c, sc(soften(mul(scales, m)), 0.5), (30, 70, 20, 255))
    shine(c, m, 0, -0.03, 0.4)
    arc_ = M(lambda d: d.arc(pts([(0.40, 0.10), (0.96, 0.66)]), 260, 350, fill=255, width=int(0.022 * W)))
    lit(c, arc_, (255, 255, 230), glowc=(255, 240, 160), gr=8)
    return K.finish(c)


def hysteric_barrage():
    """A hysterical flurry of five blows."""
    c = bg(330, 0.6, 0.42)
    burst(c, 0.5, 0.5, 0.40, 0.24, 14, EL['gold'], 10, 0.3, core=False)
    for k, (x, y, s_) in enumerate(((0.24, 0.32, 0.45), (0.76, 0.32, 0.45), (0.22, 0.70, 0.45), (0.78, 0.70, 0.45))):
        g = M(lambda d, x=x, y=y, s_=s_: K.fist_front(d, x, y, s_))
        K.fill(c, sc(soften(g, 3), 0.6), (255, 220, 200, 255))
    fist(c, 0.5, 0.52, 0.80, glowc=(255, 140, 200))
    return K.finish(c)


def amplification():
    """Resonant rings swelling magic's power and wards."""
    c = bg(250, 0.55, 0.35)
    for r, a in ((0.42, 0.5), (0.32, 0.7), (0.22, 0.9)):
        m = ring(0.5, 0.52, r, r, 0.022)
        K.glow(c, m, (150, 140, 255, 255), 10, 1.2)
        K.fill(c, sc(soften(m), a), (230, 220, 255, 255))
    o = ell(0.5, 0.52, 0.12)
    lit(c, o, rgrad((255, 255, 255), (130, 110, 255), 0.47, 0.48, 0.13), glowc=(160, 140, 255), gr=18, gs=1.5)
    arrow_mark(c, 0.5, 0.16, 0.16, True, EL['gold'])
    return K.finish(c)


def cannonball():
    """An iron cannonball bursting from a cloud of smoke."""
    c = bg(30, 0.45, 0.36, cx=0.3, cy=0.7)
    smoke = EL['phys'] if 'phys' in EL else E((255, 255, 255), (200, 200, 210), (110, 110, 130), (230, 230, 240), 0)
    cloud(c, 81, (0.06, 0.60, 0.40, 0.92), smoke, 8, (0.07, 0.11), 0.9)
    speed(c, -35, [(0.48, 0.52, 0.22), (0.56, 0.66, 0.2), (0.38, 0.46, 0.16)], (255, 230, 180))
    b = ell(0.62, 0.40, 0.18)
    lit(c, b, rgrad((200, 200, 220), (20, 20, 30), 0.56, 0.32, 0.22), glowc=(255, 160, 80), gr=14, sh=True)
    lit(c, ell(0.56, 0.32, 0.05, 0.03), (255, 255, 255), soft=4)
    return K.finish(c)


def brain(c, cx, cy, s, col=((255, 200, 230), (200, 90, 150)), glowc=(255, 140, 220)):
    m = add(ell(cx - 0.12 * s, cy, 0.20 * s, 0.17 * s), ell(cx + 0.12 * s, cy, 0.20 * s, 0.17 * s),
            ell(cx, cy - 0.04 * s, 0.24 * s, 0.17 * s))
    lit(c, m, rgrad(col[0], col[1], cx - 0.08 * s, cy - 0.08 * s, 0.30 * s), glowc=glowc, gr=16, gs=1.3, sh=True)
    folds = M(lambda d: [d.line(pts([(cx + x * s + 0.03 * s * math.sin(t / 6 * 6), cy + (y + 0.05 * t / 6) * s)
                                     for t in range(7)]), fill=255, width=max(2, int(0.012 * W * s)))
                         for x, y in ((-0.18, -0.12), (-0.08, -0.15), (0.08, -0.15), (0.18, -0.10), (-0.14, 0.02), (0.14, 0.02))])
    K.fill(c, sc(soften(mul(folds, m), 1.5), 0.6), A(tuple(v // 2 for v in col[1])))
    K.fill(c, sc(soften(mul(tubem([(cx, cy - 0.20 * s), (cx, cy + 0.16 * s)], 0.012 * s), m)), 0.7),
           A(tuple(v // 2 for v in col[1])))
    return m


def mind_blast():
    """A psychic blast from a mind flayer: the brain crackles and paralyzes."""
    c = bg(280, 0.5, 0.30)
    e = EL['thunder']
    waves(c, 0.5, 0.48, -90, (0.30, 0.40), e, 40, 0.03)
    waves(c, 0.5, 0.48, 90, (0.30, 0.40), e, 40, 0.03)
    brain(c, 0.5, 0.48, 1.05)
    for x, y, a in ((0.18, 0.40, 0), (0.82, 0.56, 180)):
        bolt = poly(xf([(-0.08, -0.04), (0.02, -0.02), (-0.01, 0.0), (0.08, 0.04), (-0.02, 0.02), (0.01, 0.0)], x, y, 1.2, a))
        lit(c, bolt, (255, 255, 220), glowc=(255, 230, 120), gr=6, gs=1.5)
    return K.finish(c)


def snake(cx, cy, s, w=0.10, ang=0, wav=1.0):
    path = [(cx + (-0.36 + 0.72 * t / 40) * s, cy + 0.16 * wav * s * math.sin(t / 40 * math.pi * 2.2)) for t in range(41)]
    path = [((x - cx) * math.cos(math.radians(ang)) - (y - cy) * math.sin(math.radians(ang)) + cx,
             (x - cx) * math.sin(math.radians(ang)) + (y - cy) * math.cos(math.radians(ang)) + cy) for x, y in path]
    body = tubem(path, w * 0.25 * s, w * s)
    head = ell(path[-1][0], path[-1][1], w * 0.8 * s, w * 0.6 * s)
    return add(body, head), path


def exuviation():
    """A serpent sloughing its old skin, renewed and cleansed."""
    c = bg(120, 0.5, 0.40)
    old, _ = snake(0.46, 0.64, 1.0, 0.12, -10)
    K.fill(c, sc(blur(old, 3), 0.55), (240, 240, 210, 255))
    m, path = snake(0.52, 0.42, 1.0, 0.12, -10)
    lit(c, m, (170, 255, 160), (30, 140, 90), glowc=(160, 255, 180), gr=14, sh=True)
    pat = M(lambda d: [d.ellipse(pts([(x - 0.015, y - 0.015), (x + 0.015, y + 0.015)]), fill=255) for x, y in path[8:38:5]])
    K.fill(c, sc(soften(pat), 0.6), (20, 80, 50, 255))
    hx, hy = path[-1]
    lit(c, ell(hx + 0.02, hy - 0.02, 0.014), (255, 240, 80), soft=1)
    sparkles(c, [(0.20, 0.24, 0.07), (0.84, 0.80, 0.05)], (200, 255, 200))
    return K.finish(c)


def magic_hammer():
    """A hammer that knocks the mana right out of its target."""
    c = bg(215, 0.55, 0.40)
    e = EL['blu']
    impact(c, 0.68, 0.70, 0.22, e, 9, 3)
    head = rot(poly([(0.26, 0.20), (0.66, 0.20), (0.66, 0.42), (0.26, 0.42)]), -30, 0.46, 0.31)
    haft = tubem([(0.40, 0.36), (0.18, 0.88)], 0.06)
    lit(c, haft, (150, 100, 70), (80, 44, 24), sh=True)
    lit(c, head, (210, 240, 255), (70, 110, 170), glowc=(120, 210, 255), gr=14, sh=True)
    shine(c, head, -0.02, -0.02, 0.5)
    for x, y, s_ in ((0.84, 0.52, 0.04), (0.82, 0.84, 0.035), (0.56, 0.90, 0.03)):
        lit(c, drop(x, y - s_ * 1.4, y + s_ * 0.9, s_ * 0.7), e.hi, e.mid, glowc=e.glow, gr=6)
    return K.finish(c)


def zephyr_mantle():
    """A mantle of wind that conjures shadow images."""
    c = bg(160, 0.45, 0.42)
    e = EL['wind']
    def cloak(cx):
        return poly([(cx - 0.06, 0.20), (cx + 0.06, 0.20), (cx + 0.22, 0.84), (cx + 0.08, 0.78), (cx, 0.86),
                     (cx - 0.10, 0.78), (cx - 0.22, 0.84)])
    for dx, a in ((-0.20, 0.35), (0.20, 0.35)):
        K.fill(c, sc(blur(cloak(0.5 + dx), 3), a), (200, 255, 230, 255))
    m = cloak(0.5)
    lit(c, m, (180, 255, 210), (40, 140, 100), glowc=e.glow, gr=14, sh=True)
    hood = ell(0.5, 0.22, 0.09)
    lit(c, hood, (160, 240, 200), (40, 120, 90), sh=True)
    vortex(c, 0.5, 0.56, 0.44, 2, e, 0.5, 0.03, 200, ry=0.5, hi=False)
    return K.finish(c)


def frog(c, cx, cy, s, skin=((170, 240, 120), (40, 130, 50))):
    head = ell(cx, cy, 0.30 * s, 0.20 * s)
    eyes_ = add(ell(cx - 0.16 * s, cy - 0.17 * s, 0.09 * s), ell(cx + 0.16 * s, cy - 0.17 * s, 0.09 * s))
    m = add(head, eyes_)
    lit(c, m, skin[0], skin[1], glowc=(180, 255, 160), gr=12, sh=True)
    for x in (-0.16, 0.16):
        lit(c, ell(cx + x * s, cy - 0.17 * s, 0.055 * s), (255, 250, 200), soft=1)
        lit(c, ell(cx + x * s, cy - 0.16 * s, 0.03 * s, 0.045 * s), (20, 20, 20), soft=1)
    return m


def regurgitation():
    """A frog spewing a torrent of water."""
    c = bg(200, 0.55, 0.40)
    e = EL['water']
    cone(c, 0.5, 0.56, 90, 0.40, 26, e, 91, 26, 0.04, 0.14)
    frog(c, 0.5, 0.44, 1.0)
    mouth = M(lambda d: d.chord(pts([(0.36, 0.40), (0.64, 0.62)]), 0, 180, fill=255))
    lit(c, mouth, (120, 30, 50), (60, 10, 20))
    return K.finish(c)


def seedspray():
    """A pod bursting into a spray of hard seeds."""
    c = bg(75, 0.5, 0.38)
    for a in (-70, -40, -10):
        r = math.radians(a)
        items = [(0.34 + math.cos(r) * d_, 0.62 + math.sin(r) * d_) for d_ in (0.28, 0.48)]
        seed_shot(c, items, ((255, 230, 160), (170, 110, 40)), a, 0.12, (0.06, 0.04))
    pod = rot(ell(0.26, 0.70, 0.20, 0.12), 40, 0.26, 0.70)
    lit(c, pod, (170, 230, 100), (60, 120, 30), glowc=(220, 255, 140), gr=10, sh=True)
    slit = rot(ell(0.30, 0.66, 0.12, 0.035), 40, 0.30, 0.66)
    lit(c, slit, (60, 40, 10), soft=1.5)
    return K.finish(c)


def corrosive_ooze():
    """An ooze dripping acid that eats through armor."""
    c = bg(90, 0.5, 0.30)
    e = EL['poison']
    blob = poly(bez3((0.12, 0.50), (0.14, 0.12), (0.86, 0.12), (0.88, 0.50), 30) +
                [(0.84, 0.56), (0.78, 0.72), (0.72, 0.56), (0.62, 0.60), (0.56, 0.84), (0.50, 0.60), (0.38, 0.62),
                 (0.30, 0.76), (0.24, 0.56)])
    lit(c, blob, rgrad((230, 255, 160), (90, 160, 30), 0.42, 0.30, 0.45), glowc=e.glow, gr=16, sh=True)
    shine(c, blob, -0.02, -0.04, 0.5)
    ds = add(drop(0.78, 0.78, 0.90, 0.03), drop(0.56, 0.86, 0.96, 0.025), drop(0.30, 0.80, 0.90, 0.028))
    lit(c, ds, e.hi, e.mid, glowc=e.glow, gr=6)
    holes = add(ell(0.38, 0.36, 0.05, 0.04), ell(0.62, 0.36, 0.05, 0.04))
    lit(c, holes, (40, 60, 10), soft=2)
    fumes = M(lambda d: [d.line(pts([(x + 0.02 * math.sin(t / 5 * 6), 0.18 - 0.1 * t / 5) for t in range(6)]), fill=255,
                                width=int(0.015 * W)) for x in (0.40, 0.60)])
    lit(c, fumes, (240, 255, 200), glowc=e.glow, gr=5)
    arrow_mark(c, 0.84, 0.84, 0.12, False, EL['blood'])
    return K.finish(c)


def spiral_spin():
    """A dizzying spiral spin that throws off aim."""
    c = bg(300, 0.5, 0.40)
    m = M(lambda d: d.line(pts([(0.5 + math.cos(t / 60 * 4 * math.pi) * 0.40 * (1 - t / 70),
                                  0.5 + math.sin(t / 60 * 4 * math.pi) * 0.40 * (1 - t / 70)) for t in range(61)]),
                           fill=255, width=int(0.05 * W), joint='curve'))
    lit(c, m, (255, 230, 255), (230, 120, 220), glowc=(255, 140, 240), gr=12, gs=1.3)
    sparkles(c, [(0.5, 0.5, 0.08)], (255, 200, 255))
    arrow_mark(c, 0.82, 0.82, 0.13, False, EL['blood'])
    return K.finish(c)


SPELLS.update({
    'Bomb Toss': bomb_toss, 'Frypan': frypan, 'Flying Hip Press': flying_hip_press, 'Hydro Shot': hydro_shot,
    'Diamondhide': diamondhide, 'Enervation': enervation, 'Light of Penance': light_of_penance, 'Warm-Up': warm_up,
    'Firespit': firespit, 'Feather Storm': feather_storm, 'Tail Slap': tail_slap, 'Hysteric Barrage': hysteric_barrage,
    'Amplification': amplification, 'Cannonball': cannonball, 'Mind Blast': mind_blast, 'Exuviation': exuviation,
    'Magic Hammer': magic_hammer, 'Zephyr Mantle': zephyr_mantle, 'Regurgitation': regurgitation,
    'Seedspray': seedspray, 'Corrosive Ooze': corrosive_ooze, 'Spiral Spin': spiral_spin,
})
def asuran_claws():
    """Six arms' worth of claws raking at once."""
    c = bg(15, 0.7, 0.36)
    e = EL['fire']
    wash(c, ell(0.5, 0.5, 0.30), (255, 140, 60), 30, 0.6)
    for k in range(6):
        a = math.radians(-90 + 60 * k + 15)
        tx, ty = -math.sin(a), math.cos(a)
        cx, cy = 0.5 + math.cos(a) * 0.27, 0.5 + math.sin(a) * 0.27
        slash(c, cx - tx * 0.13, cy - ty * 0.13, cx + tx * 0.13, cy + ty * 0.13, 0.03,
              EL['light'] if k % 2 else EL['gold'], 0.07, glowc=(255, 120, 50))
    lit(c, poly(star_pts(0.5, 0.5, 6, 0.12, 0.05, -90)), (255, 250, 220), glowc=(255, 160, 80), gr=10, gs=1.4)
    return K.finish(c)


def sub_zero_smash():
    """A fist of ice smashing down in shards."""
    c = bg(200, 0.6, 0.40)
    e = EL['ice']
    for k in range(6):
        a = math.radians(-180 + k * 36)
        sh = poly([(0.5 + math.cos(a - 0.12) * 0.18, 0.72 + math.sin(a - 0.12) * 0.10),
                   (0.5 + math.cos(a) * 0.44, 0.72 + math.sin(a) * 0.40),
                   (0.5 + math.cos(a + 0.12) * 0.18, 0.72 + math.sin(a + 0.12) * 0.10)])
        lit(c, sh, (255, 255, 255), (120, 190, 240), glowc=e.glow, gr=10, sh=True)
    fist(c, 0.5, 0.46, 0.85, glowc=(160, 230, 255), skin=((250, 255, 255), (120, 180, 230)), ang=180)
    return K.finish(c)


def roar_head(c, cx, cy, s, skin=((255, 210, 120), (170, 100, 30)), mane=((255, 170, 60), (150, 60, 10)),
              glowc=(255, 210, 120)):
    """A lion-like head roaring straight at us."""
    mn = poly(star_pts(cx, cy, 14, 0.34 * s, 0.25 * s, -90, 0.08, 5))
    lit(c, mn, mane[0], mane[1], glowc=glowc, gr=16, gs=1.2, sh=True)
    f = ell(cx, cy + 0.02 * s, 0.21 * s, 0.22 * s)
    lit(c, f, rgrad(skin[0], skin[1], cx, cy - 0.06 * s, 0.24 * s), sh=True)
    mouth = ell(cx, cy + 0.10 * s, 0.11 * s, 0.10 * s)
    lit(c, mouth, (110, 20, 30), (50, 6, 14))
    fangs = add(poly([(cx - 0.08 * s, cy + 0.03 * s), (cx - 0.04 * s, cy + 0.03 * s), (cx - 0.06 * s, cy + 0.10 * s)]),
                poly([(cx + 0.08 * s, cy + 0.03 * s), (cx + 0.04 * s, cy + 0.03 * s), (cx + 0.06 * s, cy + 0.10 * s)]))
    lit(c, fangs, (255, 255, 240), soft=1)
    brows = add(poly([(cx - 0.15 * s, cy - 0.12 * s), (cx - 0.03 * s, cy - 0.06 * s), (cx - 0.13 * s, cy - 0.04 * s)]),
                poly([(cx + 0.15 * s, cy - 0.12 * s), (cx + 0.03 * s, cy - 0.06 * s), (cx + 0.13 * s, cy - 0.04 * s)]))
    lit(c, brows, (255, 240, 120), glowc=(255, 230, 100), gr=4, gs=1.5)
    return mn


def triumphant_roar():
    """A victorious roar that whips allies into fury."""
    c = bg(40, 0.65, 0.45)
    rays(c, 0.5, 0.48, 16, (255, 240, 180), alpha=90)
    roar_head(c, 0.5, 0.52, 1.05)
    arrow_mark(c, 0.82, 0.22, 0.15, True, EL['gold'])
    return K.finish(c)


def acrid_stream():
    """A stream of acid that eats away magical defense."""
    c = bg(160, 0.55, 0.32)
    e = E((240, 255, 220), (120, 230, 170), (30, 120, 90), (120, 255, 190), 150)
    path = bez((0.12, 0.30), (0.56, 0.06), (0.74, 0.78), 30)
    m = tubem(path, 0.05, 0.12)
    lit(c, m, e.hi, e.mid, glowc=e.glow, gr=16, gs=1.3)
    K.fill(c, sc(soften(tubem(path, 0.015, 0.04), 2), 0.9), (255, 255, 255, 255))
    spl = M(lambda d: [d.ellipse(pts([(0.74 + math.cos(a) * 0.12 - 0.025, 0.80 + math.sin(a) * 0.06 - 0.025),
                                      (0.74 + math.cos(a) * 0.12 + 0.025, 0.80 + math.sin(a) * 0.06 + 0.025)]), fill=255)
                       for a in [math.radians(x) for x in (180, 220, 270, 320, 0)]])
    lit(c, spl, e.hi, e.mid, glowc=e.glow, gr=6)
    fumes = M(lambda d: [d.line(pts([(x + 0.02 * math.sin(t / 5 * 6), 0.70 - 0.12 * t / 5) for t in range(6)]),
                                fill=255, width=int(0.014 * W)) for x in (0.66, 0.80)])
    lit(c, fumes, (230, 255, 240), glowc=e.glow, gr=5)
    return K.finish(c)


def blazing_bound():
    """A fiery pounce that leaves a trail of flame."""
    c = bg(20, 0.7, 0.38)
    e = EL['fire']
    trail = M(lambda d: [GA.flame(d, x, 0.92, 0.07 + 0.02 * k, 0.24 + 0.08 * k, 0.03) for k, x in enumerate((0.18, 0.32, 0.46))])
    lit(c, trail, (255, 240, 150), (255, 90, 30), glowc=e.glow, gr=16, ang=270)
    arc_ = tubem(bez((0.12, 0.80), (0.40, 0.04), (0.80, 0.50), 30), 0.02, 0.10)
    lit(c, arc_, e.hi, e.mid, glowc=e.glow, gr=16, gs=1.3)
    pawm = M(lambda d: GB.paw(d, 0.74, 0.54, 0.55))
    lit(c, pawm, (255, 250, 220), (255, 160, 60), glowc=(255, 200, 120), gr=12, gs=1.3, sh=True)
    return K.finish(c)


def plenilune_embrace():
    """The full moon's embrace: healing light and a stirring of strength."""
    c = bg(240, 0.5, 0.30, cy=0.4)
    motes(c, 101, 22, (0.1, 0.1, 0.9, 0.9), (0.005, 0.011), (230, 240, 255), (180, 200, 255))
    moon = ell(0.5, 0.40, 0.22)
    lit(c, moon, rgrad((255, 255, 250), (200, 210, 240), 0.44, 0.34, 0.25), glowc=(220, 230, 255), gr=30, gs=1.6)
    craters = add(ell(0.44, 0.36, 0.04), ell(0.56, 0.46, 0.03), ell(0.54, 0.30, 0.025))
    K.fill(c, sc(soften(craters, 2), 0.3), (150, 160, 200, 255))
    arms = M(lambda d: [d.polygon(pts(tube(arcp(0.5, 0.48, 0.34, 0.32, a0, a1, 30), 0.02, 0.07)), fill=255)
                        for a0, a1 in ((100, 200), (80, -20))])
    lit(c, arms, (255, 240, 250), (220, 170, 240), glowc=(240, 200, 255), gr=12, gs=1.3)
    cr = M(lambda d: GA.cross(d, 0.5, 0.80, 0.26))
    lit(c, cr, (255, 255, 255), (190, 255, 210), glowc=(140, 255, 180), gr=10, gs=1.3)
    return K.finish(c)


def demoralizing_roar():
    """A roar that breaks the foe's will to attack."""
    c = bg(260, 0.45, 0.30)
    roar_head(c, 0.5, 0.46, 0.95, skin=((200, 190, 230), (90, 70, 140)), mane=((150, 110, 200), (60, 30, 100)),
              glowc=(190, 150, 255))
    m = M(lambda d: GB.draw_sword(d, 0.0, 0.0, 0.0, 0.0)) if False else None
    sw = M(lambda d: GB.draw_sword(d, 0.78, 0.76, 0.42, 30))
    gap = rot(poly([(0.70, 0.66), (0.90, 0.66), (0.90, 0.70), (0.70, 0.73)]), 30, 0.78, 0.76)
    lit(c, sub(sw, gap), (255, 255, 255), (150, 160, 190), glowc=(255, 120, 120), gr=8, sh=True)
    arrow_mark(c, 0.20, 0.80, 0.13, False, EL['blood'])
    return K.finish(c)


def bug(c, cx, cy, s, ang=0, shell_=((255, 120, 90), (140, 20, 20))):
    body = rot(ell(cx, cy, 0.14 * s, 0.18 * s), -ang, cx, cy)
    head = rot(ell(cx, cy - 0.20 * s, 0.07 * s, 0.06 * s), -ang, cx, cy)
    legs = rot(M(lambda d: [d.line(pts([(cx + sx * 0.10 * s, cy + y * s), (cx + sx * 0.22 * s, cy + (y - 0.04) * s),
                                        (cx + sx * 0.26 * s, cy + (y + 0.04) * s)]), fill=255, width=max(2, int(0.02 * W * s)))
                         for sx in (-1, 1) for y in (-0.08, 0.02, 0.12)]), -ang, cx, cy)
    lit(c, legs, (60, 40, 30), (20, 10, 10))
    lit(c, add(body, head), rgrad(shell_[0], shell_[1], cx - 0.04 * s, cy - 0.06 * s, 0.2 * s), sh=True)
    K.fill(c, sc(soften(mul(rot(tubem([(cx, cy - 0.16 * s), (cx, cy + 0.18 * s)], 0.012 * s), -ang, cx, cy), body)), 0.8),
           (30, 10, 10, 255))
    shine(c, body, -0.01, -0.02, 0.5)
    return body


def cimicine_discharge():
    """A bug's foul discharge that slows all it touches."""
    c = bg(55, 0.5, 0.36)
    e = EL['poison']
    cone(c, 0.40, 0.56, -10, 0.52, 30, e, 111, 26, 0.04, 0.13)
    bug(c, 0.30, 0.58, 1.2, -100, ((140, 110, 80), (60, 40, 20)))
    hg = poly([(0.70, 0.70), (0.86, 0.70), (0.78, 0.79), (0.86, 0.88), (0.70, 0.88), (0.78, 0.79)])
    lit(c, hg, (255, 250, 220), (200, 170, 100), glowc=(255, 220, 150), gr=6, sh=True)
    return K.finish(c)


def animating_wail():
    """A wailing spirit whose cry quickens its allies."""
    c = bg(185, 0.5, 0.36)
    g = add(ell(0.44, 0.40, 0.18, 0.20), poly([(0.26, 0.40), (0.62, 0.40), (0.60, 0.84), (0.52, 0.74), (0.44, 0.86),
                                                 (0.36, 0.74), (0.28, 0.84)]))
    lit(c, g, (255, 255, 255), (170, 220, 240), glowc=(160, 240, 255), gr=14, gs=1.3, sh=True)
    face = add(ell(0.38, 0.38, 0.03, 0.045), ell(0.50, 0.38, 0.03, 0.045), ell(0.44, 0.52, 0.045, 0.07))
    lit(c, face, (30, 40, 70), soft=1)
    waves(c, 0.56, 0.50, -20, (0.18, 0.28), EL['blu'], 35, 0.03)
    note(c, 0.80, 0.42, 0.22, flags=2)
    arrow_mark(c, 0.80, 0.80, 0.13, True, EL['gold'])
    return K.finish(c)


def battery_charge():
    """Recharging: a battery brimming with mana."""
    c = bg(175, 0.6, 0.36)
    body = poly([(0.30, 0.24), (0.70, 0.24), (0.70, 0.86), (0.30, 0.86)])
    cap = poly([(0.42, 0.16), (0.58, 0.16), (0.58, 0.24), (0.42, 0.24)])
    lit(c, add(body, cap), (220, 230, 240), (100, 110, 130), glowc=(120, 255, 240), gr=16, sh=True)
    inner = poly([(0.35, 0.30), (0.65, 0.30), (0.65, 0.80), (0.35, 0.80)])
    lit(c, inner, (20, 40, 60))
    for k in range(4):
        y0 = 0.68 - k * 0.12
        seg = poly([(0.37, y0), (0.63, y0), (0.63, y0 + 0.10), (0.37, y0 + 0.10)])
        lit(c, seg, (200, 255, 250), (60, 220, 200), glowc=(100, 255, 230), gr=6)
    bolt = poly([(0.54, 0.30), (0.42, 0.56), (0.50, 0.56), (0.44, 0.78), (0.60, 0.48), (0.52, 0.48), (0.58, 0.30)])
    lit(c, bolt, (255, 255, 230), (255, 230, 120), glowc=(255, 240, 160), gr=8, gs=1.3)
    return K.finish(c)


def leafstorm():
    """A whirlwind of razor leaves."""
    c = bg(110, 0.55, 0.38)
    vortex(c, 0.5, 0.5, 0.44, 3, EL['wind'], 0.7, 0.035, 60, hi=False)
    rnd = random.Random(121)
    for k in range(8):
        a = math.radians(k * 45 + rnd.uniform(-15, 15))
        r = rnd.uniform(0.16, 0.36)
        x, y = 0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r
        lit(c, leafm(x, y, math.degrees(a) + 100, 0.16, 0.05), (210, 255, 150), (60, 160, 50), sh=True)
    return K.finish(c)


def regeneration():
    """A lizard's lost tail growing back, life steadily returning."""
    c = bg(135, 0.55, 0.40)
    arc_ = M(lambda d: GA.arc_arrow(d, 0.5, 0.52, 0.38, 120, 400, 0.03, 0.05))
    lit(c, arc_, (240, 255, 220), glowc=(170, 255, 170), gr=8)
    path = bez3((0.20, 0.36), (0.50, 0.30), (0.70, 0.56), (0.48, 0.74), 30)
    old = tubem(path[:16], 0.16, 0.10)
    new = tubem(path[15:], 0.10, 0.01)
    lit(c, old, (200, 220, 140), (90, 120, 50), sh=True)
    K.fill(c, sc(soften(M(lambda d: [d.arc(pts([(x - 0.03, y - 0.02), (x + 0.03, y + 0.03)]), 200, 340, fill=255,
                                             width=int(0.01 * W)) for x, y in path[2:15:3]])), 0.6), (60, 80, 30, 255))
    lit(c, new, (230, 255, 220), (120, 240, 160), glowc=(140, 255, 180), gr=12, gs=1.5)
    motes(c, 131, 10, (0.4, 0.5, 0.7, 0.85), (0.007, 0.013), (230, 255, 230), (130, 255, 170))
    return K.finish(c)


def final_sting():
    """The hornet's last, all-consuming sting."""
    c = bg(50, 0.7, 0.45)
    rays(c, 0.66, 0.70, 12, (255, 240, 180), alpha=70)
    ab = rot(ell(0.38, 0.38, 0.24, 0.15), -40, 0.38, 0.38)
    stripes = rot(M(lambda d: [d.rectangle(pts([(x, 0.2), (x + 0.05, 0.6)]), fill=255) for x in (0.26, 0.36, 0.46)]), -40,
                  0.38, 0.38)
    lit(c, ab, (255, 220, 60), (200, 130, 10), glowc=(255, 220, 100), gr=12, sh=True)
    K.fill(c, soften(mul(stripes, ab), 1.5), (30, 20, 10, 255))
    st = poly([(0.50, 0.46), (0.86, 0.86), (0.56, 0.54)])
    lit(c, st, (255, 255, 255), (150, 150, 170), glowc=(255, 80, 60), gr=12, gs=1.5, sh=True)
    sparkles(c, [(0.86, 0.86, 0.08)], (255, 120, 80))
    shine(c, ab, -0.02, -0.03, 0.4)
    return K.finish(c)


def goblin_head(c, cx, cy, s):
    """A goblin's head: hooded, masked, long-nosed."""
    hood = poly(xf([(-0.26, 0.20), (-0.24, -0.10), (-0.12, -0.28), (0.0, -0.36), (0.12, -0.28), (0.24, -0.10), (0.26, 0.20)],
                   cx, cy, s))
    lit(c, hood, (170, 120, 80), (80, 50, 30), glowc=(255, 210, 150), gr=10, sh=True)
    face = ell(cx, cy + 0.02 * s, 0.17 * s, 0.17 * s)
    lit(c, face, (140, 170, 110), (70, 100, 50))
    mask_ = poly(xf([(-0.17, -0.06), (0.17, -0.06), (0.15, 0.04), (-0.15, 0.04)], cx, cy, s))
    lit(c, mask_, (220, 200, 160), (140, 110, 70))
    lit(c, add(ell(cx - 0.07 * s, cy - 0.01 * s, 0.03 * s, 0.025 * s), ell(cx + 0.07 * s, cy - 0.01 * s, 0.03 * s, 0.025 * s)),
        (255, 220, 80), glowc=(255, 200, 60), gr=4, gs=1.5)
    nose = poly(xf([(-0.03, 0.02), (0.03, 0.02), (0.0, 0.18)], cx, cy, s))
    lit(c, nose, (160, 190, 130), (80, 110, 60), soft=1)


def goblin_rush():
    """A goblin's three-stab dagger rush."""
    c = bg(95, 0.45, 0.36)
    for k, (x, y) in enumerate(((0.62, 0.30), (0.74, 0.50), (0.62, 0.70))):
        slash(c, x - 0.10, y - 0.06, x + 0.14, y + 0.06, 0.0, EL['light'], 0.05)
    goblin_head(c, 0.32, 0.52, 0.95)
    dg = M(lambda d: GB.draw_dagger(d, 0.66, 0.52, 0.42, 90))
    lit(c, dg, (255, 255, 255), (150, 160, 190), glowc=(255, 255, 220), gr=8, sh=True)
    return K.finish(c)


def vanity_dive():
    """A plunging dive that lands in a crown of spray."""
    c = bg(215, 0.55, 0.36, cy=0.8)
    e = EL['water']
    crown = M(lambda d: [d.polygon(pts([(0.5 + x - 0.03, 0.80), (0.5 + x * 1.3, 0.80 - h), (0.5 + x + 0.03, 0.80)]), fill=255)
                         for x, h in ((-0.30, 0.16), (-0.18, 0.26), (-0.06, 0.32), (0.06, 0.32), (0.18, 0.26), (0.30, 0.16))])
    lit(c, crown, e.hi, e.mid, glowc=e.glow, gr=10, gs=1.3)
    shockring(c, 0.5, 0.82, 0.38, 0.07, e, 0.025)
    m = bird(0.5, 0.36, 0.55, 90, 0.9)
    lit(c, m, (255, 230, 255), (190, 120, 200), glowc=(255, 200, 255), gr=10, sh=True)
    speed(c, 90, [(0.36, 0.16, 0.14), (0.64, 0.16, 0.14)], (230, 240, 255))
    return K.finish(c)


def magic_barrier():
    """A shimmering hexagonal ward against magic."""
    c = bg(250, 0.5, 0.36)
    hexes = []
    for q, r_ in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]:
        x = 0.5 + 0.17 * (q + r_ / 2)
        y = 0.5 + 0.147 * r_
        hexes.append(poly([(x + math.cos(math.radians(60 * k + 30)) * 0.088, y + math.sin(math.radians(60 * k + 30)) * 0.088)
                           for k in range(6)]))
    hm = add(*hexes)
    lit(c, hm, rgrad((230, 220, 255), (120, 100, 230), 0.4, 0.4, 0.4), glowc=(170, 150, 255), gr=18, gs=1.3)
    edges = M(lambda d: [d.polygon(pts([(0.5 + 0.17 * (q + r_ / 2) + math.cos(math.radians(60 * k + 30)) * 0.088,
                                        0.5 + 0.147 * r_ + math.sin(math.radians(60 * k + 30)) * 0.088) for k in range(6)]),
                                   outline=255, width=int(0.012 * W))
                         for q, r_ in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]])
    lit(c, edges, (255, 255, 255), glowc=(220, 210, 255), gr=6)
    sparkles(c, [(0.40, 0.38, 0.07)], (220, 210, 255))
    return K.finish(c)


def whirl_of_rage():
    """A raging whirl of blows that leaves foes reeling."""
    c = bg(355, 0.6, 0.36)
    vortex(c, 0.5, 0.52, 0.44, 3, EL['blood'], 0.9, 0.07, 0, ry=0.75, hi=False)
    lit(c, ell(0.5, 0.52, 0.10, 0.07), (255, 230, 220), glowc=(255, 100, 80), gr=14, gs=1.4)
    sparkles(c, [(0.32, 0.20, 0.06), (0.50, 0.14, 0.05), (0.68, 0.20, 0.06)], (255, 240, 140))
    anger(c, 0.82, 0.78, 0.12)
    return K.finish(c)


SPELLS.update({
    'Asuran Claws': asuran_claws, 'Sub-zero Smash': sub_zero_smash, 'Triumphant Roar': triumphant_roar,
    'Acrid Stream': acrid_stream, 'Blazing Bound': blazing_bound, 'Plenilune Embrace': plenilune_embrace,
    'Demoralizing Roar': demoralizing_roar, 'Cimicine Discharge': cimicine_discharge,
    'Animating Wail': animating_wail, 'Battery Charge': battery_charge, 'Leafstorm': leafstorm,
    'Regeneration': regeneration, 'Final Sting': final_sting, 'Goblin Rush': goblin_rush,
    'Vanity Dive': vanity_dive, 'Magic Barrier': magic_barrier, 'Whirl of Rage': whirl_of_rage,
})
def tentacle(path, w0=0.08):
    return tubem(path, w0, 0.008)


def benthic_typhoon():
    """A typhoon churned up from the sea bed, tentacles lashing."""
    c = bg(225, 0.65, 0.28)
    e = EL['water']
    vortex(c, 0.5, 0.5, 0.44, 4, e, 1.0, 0.06, 0, hi=False)
    for k in range(3):
        a = math.radians(-60 + 120 * k)
        path = [(0.5 + math.cos(a + t / 20 * 2.2) * (0.06 + 0.32 * t / 20), 0.5 + math.sin(a + t / 20 * 2.2) * (0.06 + 0.32 * t / 20))
                for t in range(21)]
        m = tentacle(path, 0.09)
        lit(c, m, (220, 140, 230), (110, 40, 140), glowc=(220, 140, 255), gr=8, sh=True)
        suck = add(*[ell(x, y, 0.012) for x, y in path[3:18:3]])
        K.fill(c, soften(mul(suck, m)), (255, 220, 255, 255))
    lit(c, ell(0.5, 0.5, 0.06), (30, 10, 40), glowc=(160, 100, 255), gr=10)
    return K.finish(c)


def auroral_drape():
    """A shimmering aurora drawn over the foe's eyes and voice."""
    c = bg(235, 0.6, 0.20, cy=0.3)
    motes(c, 141, 26, (0.08, 0.08, 0.92, 0.92), (0.004, 0.009), (255, 255, 255), (200, 220, 255))
    for k, (h, x0) in enumerate(((140, 0.20), (170, 0.38), (290, 0.56), (150, 0.72))):
        path = [(x0 + 0.06 * math.sin(t / 20 * math.pi * 2 + k), 0.12 + 0.70 * t / 20) for t in range(21)]
        m = tubem(path, 0.16, 0.02)
        K.glow(c, m, A(hsv(h, 0.7, 1.0)), 16, 1.0)
        K.fill(c, sc(soften(m, 6), 0.75), K.linear(A(hsv(h, 0.25, 1.0)), (0, 0, 0, 0), 90))
    return K.finish(c)


def osmosis():
    """A membrane soaking a blessing out of its target."""
    c = bg(300, 0.45, 0.28)
    cell = ell(0.42, 0.56, 0.30, 0.28)
    K.fill(c, sc(blur(cell, 6), 0.55), (160, 90, 200, 255))
    edge = ring(0.42, 0.56, 0.30, 0.28, 0.025)
    lit(c, edge, (240, 210, 255), glowc=(200, 120, 255), gr=12, gs=1.3)
    nuc = ell(0.38, 0.58, 0.10, 0.09)
    lit(c, nuc, rgrad((255, 220, 255), (150, 60, 190), 0.36, 0.55, 0.1), glowc=(220, 150, 255), gr=8)
    for x, y, r in ((0.80, 0.24, 0.045), (0.70, 0.36, 0.035), (0.62, 0.46, 0.03)):
        lit(c, poly(star_pts(x, y, 4, r * 1.6, r * 0.45)), (255, 255, 220), glowc=(255, 230, 120), gr=8, gs=1.4)
    return K.finish(c)


def quad_continuum():
    """Four blows in an unbroken chain."""
    c = bg(180, 0.5, 0.36)
    arc_ = M(lambda d: GA.arc_arrow(d, 0.5, 0.5, 0.32, -100, 230, 0.03, 0.05))
    lit(c, arc_, (220, 255, 250), glowc=(120, 255, 230), gr=8)
    for k in range(4):
        a = math.radians(-60 + 90 * k)
        x, y = 0.5 + math.cos(a) * 0.32, 0.5 + math.sin(a) * 0.32
        burst(c, x, y, 0.12, 0.05, 6, EL['gold'], k + 2, 0.2, core=False)
    lit(c, poly(star_pts(0.5, 0.5, 4, 0.13, 0.04)), (255, 255, 255), glowc=(160, 255, 230), gr=10, gs=1.4)
    return K.finish(c)


def fantod():
    """A startled fit of nerves that sharpens the next blow."""
    c = bg(15, 0.65, 0.42)
    m = M(lambda d: [d.polygon(pts(tube([(0.5 + math.cos(a) * 0.22, 0.5 + math.sin(a) * 0.22),
                                          (0.5 + math.cos(a + 0.12) * 0.30, 0.5 + math.sin(a + 0.12) * 0.30),
                                          (0.5 + math.cos(a - 0.08) * 0.38, 0.5 + math.sin(a - 0.08) * 0.38),
                                          (0.5 + math.cos(a + 0.06) * 0.45, 0.5 + math.sin(a + 0.06) * 0.45)], 0.035, 0.01)),
                               fill=255) for a in [math.pi * 2 * k / 10 for k in range(10)]])
    lit(c, m, (255, 250, 200), glowc=(255, 200, 80), gr=10, gs=1.4)
    ex = add(poly([(0.44, 0.22), (0.56, 0.22), (0.53, 0.60), (0.47, 0.60)]), ell(0.5, 0.71, 0.055))
    lit(c, ex, (255, 255, 255), (255, 210, 120), glowc=(255, 120, 60), gr=16, gs=1.4, sh=True)
    return K.finish(c)


def thermal_pulse():
    """A red-hot core throbbing out searing pulses."""
    c = bg(10, 0.7, 0.30)
    e = EL['fire']
    for r, w in ((0.42, 0.02), (0.32, 0.03), (0.22, 0.035)):
        shockring(c, 0.5, 0.5, r, r, e, w)
    o = ell(0.5, 0.5, 0.12)
    lit(c, o, rgrad((255, 255, 230), (255, 90, 20), 0.48, 0.47, 0.13), glowc=e.glow, gr=22, gs=1.6)
    return K.finish(c)


def empty_thrash():
    """A thrash from the Empty: void-black and edged in eerie light."""
    c = bg(195, 0.35, 0.18)
    e = E((230, 255, 250), (110, 220, 210), (20, 80, 90), (90, 240, 220), 175)
    slash(c, 0.12, 0.70, 0.88, 0.40, -0.12, e, 0.16, glowc=(90, 240, 220))
    slash(c, 0.18, 0.36, 0.80, 0.80, 0.08, e, 0.10, glowc=(90, 240, 220))
    o = ell(0.5, 0.54, 0.11)
    lit(c, o, (10, 10, 20), glowc=(90, 240, 220), gr=16, gs=1.6)
    lit(c, ell(0.5, 0.54, 0.035), (200, 255, 250), glowc=(150, 255, 240), gr=6)
    return K.finish(c)


def dream_flower():
    """A blossom whose scent carries everyone off to dreams."""
    c = bg(320, 0.5, 0.42)
    sw = M(lambda d: [d.line(pts([(x + math.cos(t / 20 * 7) * 0.05 * t / 20, y + math.sin(t / 20 * 7) * 0.05 * t / 20)
                                  for t in range(21)]), fill=255, width=int(0.014 * W)) for x, y in ((0.22, 0.24), (0.78, 0.26), (0.80, 0.74))])
    lit(c, sw, (255, 230, 250), glowc=(255, 160, 230), gr=6)
    flower(c, 0.48, 0.54, 0.34, (255, 230, 245), (240, 90, 160), (255, 240, 150), 8, -90, w=0.32)
    flower(c, 0.48, 0.54, 0.18, (255, 250, 255), (250, 140, 200), (255, 230, 120), 8, -67, w=0.4)
    zzz(c, 0.20, 0.80, 0.45)
    return K.finish(c)


def mage_figure(cx, cy, s):
    """A hooded, robed blue mage silhouette."""
    hood = add(ell(cx, cy - 0.26 * s, 0.10 * s, 0.11 * s), poly(xf([(-0.02, -0.40), (0.08, -0.30), (-0.06, -0.30)], cx, cy, s)))
    robe = poly(xf([(-0.10, -0.18), (0.10, -0.18), (0.24, 0.36), (0.0, 0.40), (-0.24, 0.36)], cx, cy, s))
    sleeves = add(poly(xf([(0.08, -0.14), (0.30, 0.04), (0.24, 0.10), (0.06, -0.02)], cx, cy, s)),
                  poly(xf([(-0.08, -0.14), (-0.30, 0.04), (-0.24, 0.10), (-0.06, -0.02)], cx, cy, s)))
    return add(hood, robe, sleeves)


def occultation():
    """Showpiece: the blue mage wrapped in a fan of shadow images that soak up blows."""
    c = bg(225, 0.75, 0.26, cy=0.5)
    rays(c, 0.5, 0.52, 14, (150, 230, 255), alpha=50)
    for dx, a in ((-0.27, 0.35), (0.27, 0.35), (-0.15, 0.6), (0.15, 0.6)):
        g = mage_figure(0.5 + dx, 0.60, 0.80)
        K.glow(c, g, (90, 220, 255, 255), 8, 0.9 * a)
        K.fill(c, sc(soften(g, 2), a), K.linear((160, 240, 255, 255), (30, 110, 200, 255), 90))
        K.fill(c, sc(soften(sub(g, ImageChops.offset(g, int(0.012 * W), int(0.012 * W))), 2), a), (230, 255, 255, 255))
    m = mage_figure(0.5, 0.58, 0.90)
    lit(c, m, (230, 252, 255), (60, 150, 230), glowc=(140, 230, 255), gr=14, gs=1.5, sh=True)
    face = ell(0.5, 0.345, 0.055, 0.06)
    lit(c, face, (10, 20, 50), soft=1.5)
    lit(c, add(ell(0.482, 0.345, 0.011), ell(0.518, 0.345, 0.011)), (160, 240, 255), glowc=(120, 230, 255), gr=4, gs=1.6)
    sparkles(c, [(0.20, 0.24, 0.07), (0.80, 0.22, 0.06), (0.82, 0.78, 0.05)], (150, 230, 255))
    return K.finish(c)


def charged_whisker():
    """A cat's whiskers crackling with gathered lightning."""
    c = bg(270, 0.55, 0.32)
    e = EL['thunder']
    head = ell(0.5, 0.56, 0.26, 0.22)
    ears = add(poly([(0.28, 0.46), (0.30, 0.18), (0.46, 0.38)]), poly([(0.72, 0.46), (0.70, 0.18), (0.54, 0.38)]))
    m = add(head, ears)
    lit(c, m, (90, 80, 120), (30, 24, 50), glowc=e.glow, gr=12, sh=True)
    eyes = add(ell(0.41, 0.52, 0.045, 0.035), ell(0.59, 0.52, 0.045, 0.035))
    lit(c, eyes, (255, 240, 120), glowc=(255, 230, 100), gr=6, gs=1.4)
    lit(c, add(ell(0.41, 0.52, 0.01, 0.03), ell(0.59, 0.52, 0.01, 0.03)), (20, 10, 10), soft=1)
    wh = M(lambda d: [d.line(pts([(0.5 + sx * 0.10, 0.64 + dy * 0.3), (0.5 + sx * 0.25, 0.62 + dy), (0.5 + sx * 0.32, 0.66 + dy * 1.4),
                                  (0.5 + sx * 0.44, 0.62 + dy * 1.8)]), fill=255, width=int(0.014 * W))
                      for sx in (-1, 1) for dy in (-0.06, 0.0, 0.06)])
    lit(c, wh, (255, 255, 255), glowc=(220, 170, 255), gr=8, gs=1.6)
    nose = poly([(0.47, 0.60), (0.53, 0.60), (0.5, 0.64)])
    lit(c, nose, (255, 150, 180), soft=1)
    return K.finish(c)


def winds_of_promyvion():
    """The winds of Promyvion, scouring away ailments."""
    c = bg(180, 0.4, 0.28)
    e = E((255, 255, 255), (200, 240, 250), (100, 160, 190), (190, 240, 255), 190)
    vortex(c, 0.5, 0.5, 0.44, 4, e, 0.8, 0.04, 15, hi=False)
    for a in (30, 150, 270):
        r = math.radians(a)
        x, y = 0.5 + math.cos(r) * 0.28, 0.5 + math.sin(r) * 0.28
        lit(c, ell(x, y, 0.05), rgrad((255, 255, 255), (150, 220, 230), x - 0.01, y - 0.01, 0.05), glowc=(180, 255, 255), gr=10, gs=1.4)
    lit(c, ell(0.5, 0.5, 0.09), rgrad((255, 255, 255), (170, 230, 240), 0.48, 0.48, 0.1), glowc=(200, 255, 255), gr=16, gs=1.5)
    return K.finish(c)


def delta_thrust():
    """Showpiece: a thrust that drives a triangle of force through the foe."""
    c = bg(200, 0.7, 0.36, cx=0.6, cy=0.4)
    e = EL['blu']
    tri = poly([(0.5, 0.12), (0.88, 0.76), (0.12, 0.76)])
    tri_in = poly([(0.5, 0.26), (0.76, 0.69), (0.24, 0.69)])
    edge = sub(tri, tri_in)
    lit(c, edge, (230, 255, 255), (90, 200, 240), glowc=(90, 220, 255), gr=18, gs=1.4)
    K.fill(c, sc(blur(tri_in, 10), 0.35), (120, 220, 255, 255))
    path = [(0.12, 0.92), (0.72, 0.32)]
    beam(c, 0.06, 0.98, 0.50, 0.54, e, 0.02, 0.06)
    lm = M(lambda d: GC_lance(d, 0.14, 0.88, 0.72, 0.30))
    lit(c, lm, (255, 255, 255), (150, 170, 200), glowc=(200, 240, 255), gr=10, sh=True)
    burst(c, 0.72, 0.30, 0.16, 0.06, 8, EL['light'], 3, 0.2)
    return K.finish(c)


def GC_lance(d, x0, y0, x1, y1):
    import group_c as GC
    GC.lance(d, x0, y0, x1, y1, 0.04)


def tonberry_lantern(c, cx, cy, s):
    ring_ = ring(cx, cy - 0.22 * s, 0.05 * s, 0.05 * s, 0.015 * s)
    lit(c, ring_, (200, 180, 140), (110, 90, 60))
    cap = poly(xf([(-0.12, -0.16), (0.12, -0.16), (0.08, -0.22), (-0.08, -0.22)], cx, cy, s))
    base = poly(xf([(-0.13, 0.16), (0.13, 0.16), (0.10, 0.22), (-0.10, 0.22)], cx, cy, s))
    glass = poly(xf([(-0.10, -0.16), (0.10, -0.16), (0.12, 0.16), (-0.12, 0.16)], cx, cy, s))
    K.glow(c, glass, (255, 200, 80, 255), 30, 1.6)
    lit(c, glass, rgrad((255, 255, 220), (255, 170, 40), cx, cy, 0.16 * s))
    fl = M(lambda d: GA.flame(d, cx, cy + 0.10 * s, 0.05 * s, 0.20 * s))
    lit(c, fl, (255, 255, 255), (255, 220, 120), ang=270)
    bars = M(lambda d: [d.line(pts(xf([(x, -0.16), (x * 1.2, 0.16)], cx, cy, s)), fill=255, width=max(2, int(0.016 * W * s)))
                        for x in (-0.10, 0.0, 0.10)])
    lit(c, add(cap, base, bars), (120, 100, 80), (60, 40, 30), sh=True)


def everyones_grudge():
    """A tonberry's lantern burning with everyone's grudge."""
    c = bg(130, 0.35, 0.20, cy=0.5)
    for x, y in ((0.20, 0.30), (0.80, 0.28), (0.18, 0.72), (0.82, 0.70)):
        f = add(ell(x - 0.035, y, 0.02, 0.012), ell(x + 0.035, y, 0.02, 0.012))
        lit(c, f, (255, 220, 120), glowc=(255, 180, 60), gr=6, gs=1.5)
    tonberry_lantern(c, 0.5, 0.52, 1.35)
    return K.finish(c)


def reaving_wind():
    """A howling wind that tears blessings away."""
    c = bg(95, 0.45, 0.32)
    e = EL['wind']
    for k, y in enumerate((0.30, 0.50, 0.70)):
        path = [(0.06 + 0.70 * t / 30, y + 0.07 * math.sin(t / 30 * math.pi * 1.6 + k)) for t in range(31)]
        lit(c, tubem(path, 0.07, 0.01), e.hi, e.mid, glowc=e.glow, gr=12, gs=1.3)
    for x, y, r in ((0.80, 0.30, 0.04), (0.86, 0.52, 0.035), (0.76, 0.72, 0.04)):
        shard = rot(poly(star_pts(x, y, 4, r * 1.6, r * 0.45)), 20, x, y)
        lit(c, shard, (255, 255, 220), glowc=(255, 230, 120), gr=8, gs=1.4)
    return K.finish(c)


def barrier_tusk():
    """Showpiece: twin great tusks crossed before a shimmering hexagonal ward."""
    c = bg(210, 0.7, 0.30, cy=0.5)
    hexm = poly([(0.5 + math.cos(math.radians(60 * k + 30)) * 0.40, 0.5 + math.sin(math.radians(60 * k + 30)) * 0.40)
                 for k in range(6)])
    K.glow(c, hexm, (90, 200, 255, 255), 24, 1.2)
    lit(c, hexm, rgrad((150, 230, 255), (20, 70, 150), 0.42, 0.36, 0.5))
    cells = M(lambda d: [d.polygon(pts([(x + math.cos(math.radians(60 * k + 30)) * 0.075, y + math.sin(math.radians(60 * k + 30)) * 0.075)
                                        for k in range(6)]), outline=255, width=int(0.01 * W))
                         for x in (0.24, 0.37, 0.50, 0.63, 0.76) for y in (0.27, 0.50, 0.73)] +
          [d.polygon(pts([(x + math.cos(math.radians(60 * k + 30)) * 0.075, y + math.sin(math.radians(60 * k + 30)) * 0.075)
                          for k in range(6)]), outline=255, width=int(0.01 * W))
           for x in (0.305, 0.435, 0.565, 0.695) for y in (0.385, 0.615)])
    K.fill(c, sc(soften(mul(cells, hexm)), 0.5), (220, 250, 255, 255))
    rim = sub(hexm, poly([(0.5 + math.cos(math.radians(60 * k + 30)) * 0.36, 0.5 + math.sin(math.radians(60 * k + 30)) * 0.36)
                          for k in range(6)]))
    lit(c, rim, (230, 252, 255), (120, 210, 255), glowc=(150, 230, 255), gr=8)
    for m_ in (1, -1):
        path = bez3((0.5 - m_ * 0.34, 0.86), (0.5 - m_ * 0.20, 0.50), (0.5 + m_ * 0.06, 0.26), (0.5 + m_ * 0.34, 0.16), 30)
        t = tubem(path, 0.14, 0.01)
        lit(c, t, (255, 252, 240), (200, 176, 130), glowc=(255, 250, 220), gr=12, gs=1.2, sh=True)
        bands = M(lambda d, path=path: [d.line(pts([(path[i][0] - 0.06, path[i][1] - 0.03 * m_), (path[i][0] + 0.06, path[i][1] + 0.03 * m_)]),
                                               fill=255, width=int(0.014 * W)) for i in (3, 6)])
        K.fill(c, sc(soften(mul(bands, t)), 0.85), (190, 130, 50, 255))
        shine(c, t, -0.01 * m_, -0.02, 0.45)
    sparkles(c, [(0.50, 0.40, 0.07), (0.82, 0.30, 0.05)], (200, 240, 255))
    return K.finish(c)


def mortal_ray():
    """A ray that seals the target's doom."""
    c = bg(285, 0.45, 0.20)
    e = EL['dark']
    beam(c, 0.30, 0.30, 0.84, 0.84, e, 0.04, 0.16)
    ahriman(c, 0.30, 0.28, 0.60, (40, 220, 120))
    skull(c, 0.74, 0.74, 0.40, glowc=(200, 120, 255))
    return K.finish(c)


def water_bomb():
    """A sphere of water that bursts in a deluge."""
    c = bg(210, 0.65, 0.38)
    e = EL['water']
    burst(c, 0.5, 0.5, 0.44, 0.28, 12, e, 9, 0.3, core=False)
    o = ell(0.5, 0.5, 0.22)
    lit(c, o, rgrad((240, 250, 255), (40, 110, 230), 0.44, 0.42, 0.26), glowc=e.glow, gr=18, gs=1.3, sh=True)
    lit(c, ell(0.43, 0.42, 0.06, 0.035), (255, 255, 255), soft=4)
    wave = M(lambda d: d.line(pts([(0.30 + 0.40 * t / 20, 0.54 + 0.03 * math.sin(t / 20 * math.pi * 3)) for t in range(21)]),
                              fill=255, width=int(0.015 * W)))
    K.fill(c, sc(soften(mul(wave, o)), 0.6), (255, 255, 255, 255))
    for a in (-120, -60, 30, 150):
        r = math.radians(a)
        x, y = 0.5 + math.cos(r) * 0.36, 0.5 + math.sin(r) * 0.36
        lit(c, drop(x, y - 0.04, y + 0.04, 0.025), e.hi, e.mid, glowc=e.glow, gr=6)
    return K.finish(c)


def heavy_strike():
    """A massive iron maul swung with all its weight."""
    c = bg(220, 0.30, 0.34)
    impact(c, 0.70, 0.70, 0.26, EL['gold'], 11, 6)
    haft = tubem([(0.18, 0.18), (0.60, 0.60)], 0.065)
    lit(c, haft, (170, 120, 80), (80, 50, 30), sh=True)
    head = rot(poly([(0.50, 0.46), (0.82, 0.46), (0.82, 0.70), (0.50, 0.70)]), 45, 0.62, 0.62)
    lit(c, head, (230, 235, 250), (80, 90, 120), glowc=(220, 230, 255), gr=12, sh=True)
    studs = add(*[ell(0.62 + dx, 0.62 + dy, 0.02) for dx, dy in ((-0.06, 0.0), (0.0, -0.06), (0.06, 0.0), (0.0, 0.06))])
    lit(c, studs, (255, 255, 255), (150, 150, 170), soft=1)
    shine(c, head, -0.02, -0.02, 0.5)
    speed(c, 45, [(0.30, 0.10, 0.14), (0.14, 0.30, 0.14)], (230, 240, 255))
    return K.finish(c)


def dark_orb():
    """An orb of pure darkness."""
    c = bg(275, 0.5, 0.25)
    e = EL['dark']
    tend = M(lambda d: [d.polygon(pts(tube([(0.5 + math.cos(a + t / 10 * 0.6) * (0.20 + 0.24 * t / 10),
                                             0.5 + math.sin(a + t / 10 * 0.6) * (0.20 + 0.24 * t / 10)) for t in range(11)], 0.06, 0.005)),
                                  fill=255) for a in [math.pi * 2 * k / 7 for k in range(7)]])
    lit(c, tend, (200, 120, 255), (90, 30, 160), glowc=e.glow, gr=10, gs=1.3)
    o = ell(0.5, 0.5, 0.22)
    K.glow(c, o, (180, 80, 255, 255), 28, 1.6)
    lit(c, o, rgrad((90, 40, 130), (8, 0, 16), 0.44, 0.42, 0.24))
    rim = sub(o, ell(0.47, 0.47, 0.21))
    K.fill(c, sc(soften(rim, 3), 0.9), (230, 180, 255, 255))
    return K.finish(c)


def white_wind():
    """A pure white wind that heals all it touches."""
    c = bg(195, 0.45, 0.48)
    e = E((255, 255, 255), (220, 245, 255), (140, 200, 230), (230, 250, 255), 195)
    vortex(c, 0.5, 0.5, 0.42, 3, e, 0.7, 0.07, 0, hi=False)
    cr = M(lambda d: GA.cross(d, 0.5, 0.5, 0.46))
    lit(c, cr, (255, 255, 255), (180, 255, 210), glowc=(130, 255, 180), gr=18, gs=1.4, sh=True)
    motes(c, 151, 14, (0.12, 0.12, 0.88, 0.88), (0.006, 0.012), (255, 255, 255), (200, 240, 255))
    return K.finish(c)


def sudden_lunge():
    """Showpiece: a lightning-fast lunge whose point stuns."""
    c = bg(185, 0.7, 0.36, cx=0.7, cy=0.35)
    rays(c, 0.72, 0.30, 12, (200, 255, 255), alpha=70)
    speed(c, -40, [(0.40, 0.66, 0.34), (0.52, 0.74, 0.30), (0.34, 0.54, 0.26), (0.58, 0.84, 0.2)], (200, 255, 250), 0.02, 0.8)
    path = [(0.14, 0.92), (0.72, 0.30)]
    sp = M(lambda d: GC_lance(d, 0.10, 0.96, 0.72, 0.30))
    lit(c, sp, (255, 255, 255), (130, 170, 200), glowc=(160, 255, 240), gr=14, gs=1.3, sh=True)
    burst(c, 0.74, 0.28, 0.17, 0.06, 7, EL['gold'], 7, 0.2)
    sparkles(c, [(0.86, 0.16, 0.06), (0.90, 0.40, 0.05), (0.62, 0.12, 0.05)], (255, 240, 140))
    return K.finish(c)


def quadrastrike():
    """Four strikes crossing in two great X's."""
    c = bg(25, 0.6, 0.38)
    e = EL['light']
    for (x0, y0, x1, y1) in ((0.16, 0.20, 0.62, 0.66), (0.62, 0.20, 0.16, 0.66), (0.38, 0.34, 0.84, 0.80),
                             (0.84, 0.34, 0.38, 0.80)):
        slash(c, x0, y0, x1, y1, 0.02, e, 0.07, glowc=(255, 190, 90))
    return K.finish(c)


def vapor_spray():
    """A hissing spray of scalding vapor."""
    c = bg(205, 0.40, 0.42)
    e = E((255, 255, 255), (220, 235, 245), (150, 170, 190), (230, 240, 255), 200)
    cone(c, 0.18, 0.70, -35, 0.70, 26, e, 161, 30, 0.03, 0.14)
    noz = rot(poly([(0.06, 0.66), (0.22, 0.66), (0.22, 0.76), (0.06, 0.76)]), 35, 0.16, 0.71)
    lit(c, noz, (120, 210, 255), (40, 100, 180), glowc=(140, 220, 255), gr=8, sh=True)
    motes(c, 162, 16, (0.4, 0.1, 0.9, 0.6), (0.008, 0.016), (255, 255, 255), (200, 230, 255))
    return K.finish(c)


def thunder_breath():
    """A wyvern's crackling breath of lightning."""
    c = bg(265, 0.6, 0.30)
    e = EL['thunder']
    cone(c, 0.46, 0.52, -8, 0.52, 28, e, 171)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((160, 130, 220), (50, 30, 100)), eyec=(255, 250, 120), rimc=(210, 160, 255))
    for x, y, a in ((0.78, 0.30, 30), (0.84, 0.66, -20)):
        bolt = poly(xf([(-0.06, -0.06), (0.02, -0.01), (-0.02, 0.0), (0.06, 0.06), (-0.02, 0.01), (0.02, 0.0)], x, y, 1.0, a))
        lit(c, bolt, (255, 255, 220), glowc=(255, 240, 140), gr=6, gs=1.5)
    return K.finish(c)


def o_counterstance():
    """An orcish shield raised, ready to hit back."""
    c = bg(30, 0.55, 0.36)
    arcs = M(lambda d: [GA.arc_arrow(d, 0.5, 0.5, 0.40, 120, 230, 0.04, 0.05), GA.arc_arrow(d, 0.5, 0.5, 0.40, -60, 50, 0.04, 0.05)])
    lit(c, arcs, (255, 240, 220), glowc=(255, 140, 90), gr=10, gs=1.3)
    sh = ell(0.5, 0.5, 0.26)
    lit(c, sh, rgrad((200, 140, 90), (100, 56, 26), 0.44, 0.42, 0.3), glowc=(255, 200, 140), gr=12, sh=True)
    planks = M(lambda d: [d.line(pts([(x, 0.24), (x, 0.76)]), fill=255, width=int(0.012 * W)) for x in (0.40, 0.50, 0.60)])
    K.fill(c, sc(soften(mul(planks, sh)), 0.6), (60, 30, 10, 255))
    rim = ring(0.5, 0.5, 0.25, 0.25, 0.03)
    lit(c, rim, (220, 220, 230), (120, 120, 140))
    spikes = add(*[poly(star_pts(0.5 + math.cos(a) * 0.15, 0.5 + math.sin(a) * 0.15, 4, 0.04, 0.015))
                   for a in [math.pi / 2 * k + math.pi / 4 for k in range(4)]])
    lit(c, spikes, (255, 255, 255), (150, 150, 170), soft=1)
    boss = ell(0.5, 0.5, 0.06)
    lit(c, boss, (230, 230, 240), (110, 110, 130), sh=True)
    return K.finish(c)


def amorphic_spikes():
    """A shapeless mass erupting in spikes."""
    c = bg(300, 0.45, 0.30)
    sp = poly(star_pts(0.5, 0.52, 9, 0.44, 0.20, -90, 0.25, 17))
    lit(c, sp, (240, 220, 255), (140, 90, 200), glowc=(220, 160, 255), gr=12, sh=True)
    blob = poly([(0.5 + math.cos(t) * (0.24 + 0.03 * math.sin(3 * t)), 0.52 + math.sin(t) * (0.22 + 0.03 * math.cos(4 * t)))
                 for t in [math.pi * 2 * k / 60 for k in range(60)]])
    lit(c, blob, rgrad((230, 190, 255), (90, 40, 140), 0.44, 0.44, 0.28), glowc=(200, 140, 255), gr=10, sh=True)
    shine(c, blob, -0.02, -0.04, 0.5)
    return K.finish(c)


def wind_breath():
    """A wyrm's howling breath of wind."""
    c = bg(140, 0.55, 0.32)
    e = EL['wind']
    cone(c, 0.46, 0.52, -8, 0.52, 28, e, 181, 26, 0.03, 0.12, 0.8)
    vortex(c, 0.76, 0.48, 0.18, 3, e, 0.8, 0.03, 0, hi=False)
    maw(c, 0.46, 0.52, 1.0, -10, skin=((150, 220, 160), (30, 90, 50)), eyec=(255, 240, 120), rimc=(170, 255, 190))
    return K.finish(c)


def barbed_crescent():
    """A barbed crescent blade that throws off the foe's aim."""
    c = bg(230, 0.5, 0.32)
    cr = M(lambda d: GB.crescent(d, 0.46, 0.50, 0.34, (0.38, -0.18)))
    barbs = add(*[poly(star_pts(0.46 + math.cos(a) * 0.33, 0.50 + math.sin(a) * 0.33, 3, 0.07, 0.03,
                                math.degrees(a), 0.0)) for a in [math.radians(x) for x in (110, 150, 190, 230)]])
    m = add(cr, barbs)
    lit(c, m, (255, 255, 255), (150, 170, 210), glowc=(180, 210, 255), gr=14, gs=1.3, sh=True)
    shine(c, m, -0.02, -0.02, 0.5)
    arrow_mark(c, 0.80, 0.80, 0.14, False, EL['blood'])
    return K.finish(c)


def meditator(cx, cy, s):
    head = ell(cx, cy - 0.28 * s, 0.075 * s)
    body = poly(xf([(-0.10, -0.18), (0.10, -0.18), (0.16, 0.06), (-0.16, 0.06)], cx, cy, s))
    legs = ell(cx, cy + 0.10 * s, 0.30 * s, 0.10 * s)
    arms = add(tubem(xf([(-0.10, -0.14), (-0.20, 0.02), (-0.06, 0.08)], cx, cy, s), 0.05 * s),
               tubem(xf([(0.10, -0.14), (0.20, 0.02), (0.06, 0.08)], cx, cy, s), 0.05 * s))
    return add(head, body, legs, arms)


def nat_meditation():
    """Showpiece: a still, meditating form drawing up a blazing aura of power."""
    c = bg(15, 0.7, 0.36, cy=0.6)
    rays(c, 0.5, 0.52, 14, (255, 210, 140), alpha=60)
    aura = M(lambda d: [GA.flame(d, 0.5, 0.86, 0.36, 0.80), GA.flame(d, 0.24, 0.86, 0.12, 0.46, -0.06),
                        GA.flame(d, 0.76, 0.86, 0.12, 0.48, 0.06)])
    K.glow(c, aura, (255, 120, 40, 255), 24, 1.2)
    K.fill(c, sc(soften(aura, 6), 0.65), K.linear((255, 240, 170, 255), (230, 70, 20, 255), 270))
    orb = ell(0.5, 0.58, 0.30, 0.32)
    K.fill(c, sc(blur(orb, 20), 0.8), (255, 220, 140, 255))
    lotus = add(*[leafm(0.5, 0.86, a, 0.20, 0.055) for a in (-175, -145, -35, -5)])
    lit(c, lotus, (255, 230, 220), (240, 130, 140), sh=True)
    halo = ring(0.5, 0.35, 0.13, 0.13, 0.02)
    lit(c, halo, (255, 250, 200), glowc=(255, 230, 120), gr=8, gs=1.4)
    m = meditator(0.5, 0.66, 1.05)
    K.glow(c, m, (255, 250, 220, 255), 8, 1.8)
    lit(c, m, (60, 20, 16), (20, 6, 6))
    arrow_mark(c, 0.82, 0.22, 0.13, True, EL['gold'])
    return K.finish(c)


SPELLS.update({
    'Benthic Typhoon': benthic_typhoon, 'Auroral Drape': auroral_drape, 'Osmosis': osmosis,
    'Quad. Continuum': quad_continuum, 'Fantod': fantod, 'Thermal Pulse': thermal_pulse,
    'Empty Thrash': empty_thrash, 'Dream Flower': dream_flower, 'Occultation': occultation,
    'Charged Whisker': charged_whisker, 'Winds of Promy.': winds_of_promyvion, 'Delta Thrust': delta_thrust,
    'Evryone. Grudge': everyones_grudge, 'Reaving Wind': reaving_wind, 'Barrier Tusk': barrier_tusk,
    'Mortal Ray': mortal_ray, 'Water Bomb': water_bomb, 'Heavy Strike': heavy_strike, 'Dark Orb': dark_orb,
    'White Wind': white_wind, 'Sudden Lunge': sudden_lunge, 'Quadrastrike': quadrastrike,
    'Vapor Spray': vapor_spray, 'Thunder Breath': thunder_breath, 'O. Counterstance': o_counterstance,
    'Amorphic Spikes': amorphic_spikes, 'Wind Breath': wind_breath, 'Barbed Crescent': barbed_crescent,
    'Nat. Meditation': nat_meditation,
})
def rock(cx, cy, r, seed, n=7):
    rnd = random.Random(seed)
    return poly([(cx + math.cos(a) * r * rnd.uniform(0.7, 1.1), cy + math.sin(a) * r * rnd.uniform(0.7, 1.1))
                 for a in [math.pi * 2 * k / n + rnd.uniform(-0.2, 0.2) for k in range(n)]])


def paint_rocks(c, ms, top=(240, 210, 170), bot=(110, 80, 50)):
    m = add(*ms)
    lit(c, m, top, bot, glowc=(255, 230, 170), gr=6, gs=0.8, sh=True)
    shine(c, m, -0.01, -0.015, 0.4, 2)
    return m


def tem_upheaval():
    """A tempest tearing the ground up into the sky."""
    c = bg(125, 0.45, 0.32)
    e = EL['wind']
    ground = poly([(0, 0.80), (0.36, 0.76), (0.42, 0.84), (0.58, 0.82), (0.64, 0.76), (1, 0.80), (1, 1), (0, 1)])
    lit(c, ground, (170, 140, 100), (70, 50, 30))
    m = M(lambda d: [d.polygon(pts(tube(arcp(0.5, 0.20 + k * 0.13, 0.12 + k * 0.05, 0.05, 180, 540, 60), 0.025, 0.05)), fill=255)
                     for k in range(5)])
    m = ImageChops.lighter(m, m)
    lit(c, m, e.hi, e.mid, glowc=e.glow, gr=14)
    paint_rocks(c, [rock(0.22, 0.36, 0.05, 1), rock(0.78, 0.30, 0.06, 2), rock(0.30, 0.18, 0.035, 3), rock(0.70, 0.56, 0.04, 4)])
    return K.finish(c)


def rending_deluge():
    """A crashing wave that rips away a foe's protections."""
    c = bg(215, 0.65, 0.36)
    e = EL['water']
    wave = poly(bez3((0.06, 0.88), (0.10, 0.30), (0.60, 0.10), (0.80, 0.40), 30) +
                bez3((0.80, 0.40), (0.62, 0.30), (0.50, 0.46), (0.60, 0.60), 16) +
                bez3((0.60, 0.60), (0.40, 0.48), (0.30, 0.70), (0.40, 0.88), 16))
    lit(c, wave, rgrad(e.hi, e.lo, 0.40, 0.26, 0.6), glowc=e.glow, gr=16, sh=True)
    foam = tubem(bez3((0.10, 0.60), (0.18, 0.24), (0.60, 0.12), (0.80, 0.40), 30), 0.012, 0.04)
    lit(c, foam, (255, 255, 255), soft=2)
    for x, y, r in ((0.80, 0.70, 0.04), (0.70, 0.84, 0.03), (0.88, 0.54, 0.03)):
        shard = poly(star_pts(x, y, 4, r * 1.6, r * 0.45, -45))
        lit(c, shard, (255, 255, 230), glowc=(255, 230, 120), gr=8, gs=1.4)
    return K.finish(c)


def embalming_earth():
    """Wrappings of earth that bind and slow."""
    c = bg(35, 0.45, 0.30)
    e = EL['earth']
    fig = add(ell(0.5, 0.24, 0.09, 0.10), poly([(0.38, 0.32), (0.62, 0.32), (0.60, 0.90), (0.40, 0.90)]))
    lit(c, fig, (220, 200, 160), (130, 100, 60), glowc=(255, 220, 150), gr=12, sh=True)
    wraps = M(lambda d: [d.line(pts([(0.34, 0.20 + k * 0.09 + 0.04), (0.66, 0.20 + k * 0.09 - 0.02)]), fill=255,
                                width=int(0.03 * W)) for k in range(8)])
    lit(c, mul(wraps, blur(fig, 1).point(lambda v: 255 if v > 10 else 0)), (240, 225, 190), (170, 140, 90), sh=False)
    K.fill(c, sc(soften(mul(M(lambda d: [d.line(pts([(0.34, 0.20 + k * 0.09 + 0.055), (0.66, 0.20 + k * 0.09 - 0.005)]),
                                                     fill=255, width=int(0.008 * W)) for k in range(8)]), fig)), 0.6),
           (90, 60, 30, 255))
    sand = dots(181, 30, (0.12, 0.60, 0.88, 0.95), (0.005, 0.012))
    lit(c, sand, (255, 230, 170), glowc=e.glow, gr=4)
    return K.finish(c)


def paralyzing_triad():
    """Showpiece: three crackling stingers converging on one point, locking the foe in place."""
    c = bg(270, 0.6, 0.36)
    e = E((255, 255, 230), (255, 230, 90), (190, 140, 20), (255, 230, 100), 52)
    rays(c, 0.5, 0.5, 12, (255, 245, 170), alpha=60)
    tri = poly([(0.5 + math.cos(math.radians(a)) * 0.38, 0.5 + math.sin(math.radians(a)) * 0.38) for a in (-90, 30, 150)])
    edge = sub(tri, poly([(0.5 + math.cos(math.radians(a)) * 0.33, 0.5 + math.sin(math.radians(a)) * 0.33) for a in (-90, 30, 150)]))
    shockring(c, 0.5, 0.5, 0.20, 0.20, e, 0.02)
    for a in (-90, 30, 150):
        r = math.radians(a + 180)
        bx, by = 0.5 + math.cos(r) * 0.40, 0.5 + math.sin(r) * 0.40
        tx, ty = 0.5 + math.cos(r) * 0.07, 0.5 + math.sin(r) * 0.07
        st = poly(tube([(bx, by), (tx, ty)], 0.15, 0.004))
        lit(c, st, (255, 252, 210), (230, 160, 30), glowc=e.glow, gr=14, gs=1.4, sh=True)
        K.fill(c, sc(soften(poly(tube([(bx, by), (tx, ty)], 0.04, 0.002)), 2), 0.6), (160, 90, 10, 255))
    rnd = random.Random(191)
    arcs = K.mask()
    d = ImageDraw.Draw(arcs)
    for k in range(6):
        a = math.radians(k * 60 + 30)
        path = [(0.5 + math.cos(a) * 0.08, 0.5 + math.sin(a) * 0.08)]
        for t in range(1, 4):
            j = rnd.uniform(-0.35, 0.35)
            path.append((0.5 + math.cos(a + j) * (0.08 + 0.07 * t), 0.5 + math.sin(a + j) * (0.08 + 0.07 * t)))
        d.line(pts(path), fill=255, width=int(0.014 * W))
    lit(c, arcs, (255, 255, 255), glowc=(255, 240, 120), gr=8, gs=1.6)
    burst(c, 0.5, 0.5, 0.12, 0.05, 8, e, 4, 0.2)
    return K.finish(c)


def foul_waters():
    """A drop of rotten water, a skull drowned in it, bubbles rising."""
    c = bg(285, 0.60, 0.34, cy=0.50)
    dr = drop(0.5, 0.08, 0.90, 0.40)
    K.glow(c, dr, (140, 230, 120, 255), 22, 1.4)
    K.shadow(c, dr, 5, 8, 8, 170)
    lit(c, dr, rgrad((200, 240, 150), (40, 90, 40), 0.42, 0.60, 0.40))
    skull(c, 0.5, 0.66, 0.32, (236, 246, 214), (130, 160, 110), glowc=(90, 160, 80))
    for x, y, r in ((0.40, 0.46, 0.04), (0.58, 0.38, 0.032), (0.50, 0.28, 0.022), (0.64, 0.52, 0.026)):
        b = ring(x, y, r, r, 0.014)
        lit(c, b, (240, 255, 220), glowc=(170, 240, 150), gr=4)
    shine(c, dr, -0.03, -0.03, 0.7, 4)
    return K.finish(c)


def glutinous_dart():
    """Showpiece: a dart trailing sticky strands that weigh the target down."""
    c = bg(285, 0.55, 0.32, cx=0.65, cy=0.4)
    e = E((250, 255, 220), (210, 240, 110), (110, 150, 30), (210, 255, 90), 75)
    glue = tubem(bez((0.10, 0.90), (0.30, 0.62), (0.56, 0.46), 20), 0.05, 0.10)
    K.glow(c, glue, A(e.glow), 14, 1.0)
    lit(c, glue, e.hi, e.mid, soft=4)
    strands = M(lambda d: [d.line(pts(bez((x, y), (x + 0.02, y + 0.10), (x - 0.02, y + 0.20), 10)), fill=255,
                                  width=int(0.014 * W)) for x, y in ((0.26, 0.70), (0.40, 0.58), (0.50, 0.52))])
    lit(c, strands, e.hi, e.mid, glowc=e.glow, gr=6)
    dr = add(drop(0.26, 0.86, 0.96, 0.03), drop(0.40, 0.76, 0.86, 0.025), drop(0.48, 0.70, 0.80, 0.022))
    lit(c, dr, e.hi, e.mid, glowc=e.glow, gr=6)
    shaft = tubem([(0.44, 0.56), (0.74, 0.26)], 0.04)
    lit(c, shaft, (240, 220, 255), (130, 90, 180), sh=True)
    fl = add(poly([(0.44, 0.56), (0.34, 0.58), (0.40, 0.52)]), poly([(0.44, 0.56), (0.42, 0.66), (0.48, 0.60)]))
    lit(c, fl, (255, 150, 220), (190, 50, 140), sh=True)
    tip = poly([(0.70, 0.24), (0.88, 0.12), (0.76, 0.30)])
    lit(c, tip, (255, 255, 255), (150, 160, 190), glowc=(255, 255, 220), gr=8, sh=True)
    blob = ell(0.62, 0.40, 0.07, 0.05)
    lit(c, rot(blob, 45, 0.62, 0.40), e.hi, e.mid, glowc=e.glow, gr=8)
    shine(c, rot(blob, 45, 0.62, 0.40), -0.01, -0.015, 0.7, 2)
    arrow_mark(c, 0.80, 0.78, 0.14, False, EL['blood'])
    return K.finish(c)


def retinal_glare():
    """A glare of light that burns the eyes."""
    c = bg(40, 0.45, 0.30)
    rays(c, 0.5, 0.5, 8, (255, 250, 220), alpha=150, width=0.03)
    flare = add(poly([(0.5, 0.04), (0.53, 0.47), (0.5, 0.96), (0.47, 0.53)]), poly([(0.04, 0.5), (0.47, 0.47), (0.96, 0.5), (0.53, 0.53)]))
    lit(c, flare, (255, 255, 255), glowc=(255, 240, 180), gr=14, gs=1.4)
    eye(c, 0.5, 0.5, 0.26, 0.14, (255, 210, 80), slit=False, lid=(120, 80, 20), glowc=(255, 250, 200), ir=0.11)
    lit(c, ell(0.5, 0.5, 0.05), (255, 255, 255), glowc=(255, 255, 255), gr=16, gs=1.8)
    for x, r in ((0.70, 0.04), (0.80, 0.025), (0.26, 0.03)):
        K.fill(c, sc(soften(ring(x, x * 0.4 + 0.5 * 0.6, r, r, 0.008)), 0.6), (255, 240, 200, 255))
    return K.finish(c)


def subduction():
    """Showpiece: one plate of earth forced beneath another, dragged down by a crushing wind."""
    c = bg(120, 0.45, 0.30, cy=0.75)
    e = EL['wind']
    vortex(c, 0.5, 0.62, 0.40, 4, e, 0.9, 0.045, 0, ry=0.45, hi=False)
    seam = poly([(0.36, 0.56), (0.62, 0.50), (0.64, 0.58), (0.40, 0.66)])
    K.glow(c, seam, (255, 140, 40, 255), 18, 1.6)
    lit(c, seam, (255, 230, 140), (255, 110, 20))
    left = poly([(0.04, 0.42), (0.56, 0.38), (0.66, 0.50), (0.40, 0.58), (0.04, 0.62)])
    right = poly([(0.96, 0.52), (0.62, 0.48), (0.40, 0.60), (0.30, 0.74), (0.60, 0.74), (0.96, 0.70)])
    lit(c, right, (170, 140, 100), (80, 56, 30), sh=True)
    lit(c, left, (210, 180, 130), (110, 80, 40), glowc=(220, 255, 220), gr=10, sh=True)
    grass = poly([(0.04, 0.42), (0.56, 0.38), (0.60, 0.43), (0.04, 0.47)])
    lit(c, grass, (170, 230, 120), (80, 150, 60))
    strata = M(lambda d: [d.line(pts([(0.04, y), (0.52, y - 0.02)]), fill=255, width=int(0.008 * W)) for y in (0.51, 0.56)])
    K.fill(c, sc(soften(mul(strata, left)), 0.5), (90, 60, 30, 255))
    arr = M(lambda d: GD.arrowhead(d, 0.42, 0.88, 120, 0.10))
    lit(c, add(arr, tubem([(0.56, 0.70), (0.44, 0.86)], 0.035)), (240, 255, 230), glowc=e.glow, gr=10, gs=1.3)
    motes(c, 201, 12, (0.1, 0.1, 0.9, 0.36), (0.006, 0.014), (230, 255, 230), e.glow)
    return K.finish(c)


def morning_star(c, cx, cy, r, glowc=(255, 160, 80)):
    sp = poly(star_pts(cx, cy, 10, r * 1.45, r * 0.8, -90))
    lit(c, sp, (255, 255, 255), (140, 150, 170), glowc=glowc, gr=14, gs=1.4, sh=True)
    b = ell(cx, cy, r)
    lit(c, b, rgrad((230, 230, 245), (60, 60, 80), cx - r * 0.3, cy - r * 0.35, r * 1.2))
    lit(c, ell(cx - r * 0.35, cy - r * 0.4, r * 0.25, r * 0.15), (255, 255, 255), soft=3)


def thrashing_assault():
    """Showpiece: two spiked flails thrashing in, each trailing a comet of force."""
    c = bg(15, 0.65, 0.34)
    for (p0, p1, p2), (ix, iy) in (((0.04, 0.30), (0.40, 0.00), (0.66, 0.36)), (0.66, 0.36)), \
                                   (((0.96, 0.70), (0.60, 1.00), (0.34, 0.64)), (0.34, 0.64)):
        tr = tubem(bez(p0, p1, p2, 24), 0.01, 0.22)
        K.glow(c, tr, (255, 140, 60, 255), 18, 1.4)
        K.fill(c, sc(soften(tr, 5), 0.95), K.linear((255, 120, 40, 255), (255, 240, 180, 255), 0))
    impact(c, 0.5, 0.5, 0.20, EL['gold'], 9, 5)
    morning_star(c, 0.66, 0.36, 0.11)
    morning_star(c, 0.34, 0.64, 0.11)
    return K.finish(c)


def butterfly(c, cx, cy, s, wings=((255, 240, 160), (255, 90, 30)), body=(60, 20, 10), glowc=(255, 150, 60), ang=0):
    up = [poly(xf([(0.02, -0.02), (0.18, -0.34), (0.42, -0.36), (0.44, -0.18), (0.22, 0.02)], cx, cy, s, ang, m_)) for m_ in (1, -1)]
    lo = [poly(xf([(0.02, 0.02), (0.26, 0.06), (0.32, 0.24), (0.16, 0.34), (0.04, 0.14)], cx, cy, s, ang, m_)) for m_ in (1, -1)]
    w = add(*up, *lo)
    lit(c, w, rgrad(wings[0], wings[1], cx, cy, 0.42 * s), glowc=glowc, gr=16, gs=1.4, sh=True)
    spots = add(*[ell(*xf([(x * m_, y)], cx, cy, s, ang)[0], 0.045 * s) for m_ in (1, -1) for x, y in ((0.30, -0.22), (0.18, 0.18))])
    lit(c, mul(spots, w), (255, 255, 230), glowc=(255, 255, 200), gr=4)
    veins = M(lambda d: [d.line(pts(xf([(0.02, 0), (x * m_, y)], cx, cy, s, ang)), fill=255, width=max(2, int(0.008 * W * s)))
                         for m_ in (1, -1) for x, y in ((0.40, -0.30), (0.30, -0.10), (0.24, 0.26))])
    K.fill(c, sc(soften(mul(veins, w)), 0.5), A(wings[1]))
    b = poly(xf([(-0.03, -0.12), (0.03, -0.12), (0.025, 0.22), (0, 0.26), (-0.025, 0.22)], cx, cy, s, ang))
    lit(c, b, body, soft=1)
    ant = M(lambda d: [d.line(pts(xf([(0, -0.12), (0.10 * m_, -0.26)], cx, cy, s, ang)), fill=255, width=max(2, int(0.01 * W * s)))
                       for m_ in (1, -1)])
    lit(c, ant, body, soft=1)
    return w


def erratic_flutter():
    """Showpiece: a blazing moth darting in erratic loops, quickening its flight."""
    c = bg(20, 0.75, 0.36, cx=0.6, cy=0.4)
    e = EL['fire']
    loop = [(0.14 + 0.62 * t / 60 + 0.10 * math.cos(t / 60 * math.pi * 6), 0.80 - 0.40 * t / 60 + 0.10 * math.sin(t / 60 * math.pi * 6))
            for t in range(61)]
    tr = tubem(loop, 0.005, 0.05)
    K.glow(c, tr, A(e.glow), 12, 1.2)
    lit(c, tr, (255, 240, 180), (255, 140, 50), soft=2)
    motes(c, 211, 18, (0.1, 0.4, 0.7, 0.95), (0.006, 0.014), (255, 230, 150), e.glow)
    butterfly(c, 0.64, 0.36, 0.95, ang=15)
    arrow_mark(c, 0.20, 0.22, 0.13, True, EL['gold'])
    return K.finish(c)


def restoral():
    """A wreath of renewal: health restored and ailments lifted."""
    c = bg(110, 0.5, 0.42)
    rays(c, 0.5, 0.5, 12, (230, 255, 200), alpha=70)
    lv = add(*[leafm(0.5 + math.cos(a) * 0.32, 0.5 + math.sin(a) * 0.32, math.degrees(a) + 100 * (1 if k < 5 else -1), 0.12, 0.04)
               for k, a in enumerate([math.radians(100 + 32 * i) for i in range(5)] + [math.radians(80 - 32 * i) for i in range(5)])])
    lit(c, lv, (210, 255, 150), (60, 160, 50), glowc=(200, 255, 140), gr=8, sh=True)
    cr = M(lambda d: GA.cross(d, 0.5, 0.48, 0.52))
    lit(c, cr, (255, 255, 255), (255, 230, 150), glowc=(255, 240, 160), gr=18, gs=1.5, sh=True)
    sparkles(c, [(0.76, 0.22, 0.06), (0.24, 0.24, 0.05)], (255, 255, 200))
    return K.finish(c)


def rail_cannon():
    """A cannon of light firing a searing rail."""
    c = bg(50, 0.35, 0.28)
    e = EL['light']
    beam(c, 0.40, 0.58, 1.0, 0.24, e, 0.10, 0.16, 0.45)
    barrel = rot(poly([(0.08, 0.56), (0.44, 0.56), (0.44, 0.72), (0.08, 0.72)]), 30, 0.26, 0.64)
    lit(c, barrel, (230, 230, 240), (90, 90, 110), glowc=(255, 250, 200), gr=10, sh=True)
    bands = rot(M(lambda d: [d.rectangle(pts([(x, 0.55), (x + 0.03, 0.73)]), fill=255) for x in (0.16, 0.28, 0.40)]), 30, 0.26, 0.64)
    lit(c, bands, (255, 230, 150), (170, 120, 40))
    burst(c, 0.44, 0.56, 0.12, 0.05, 8, e, 2)
    return K.finish(c)


def diffusion_ray():
    """A ray split through a lens into a spray of beams."""
    c = bg(55, 0.45, 0.30)
    e = EL['light']
    for a in (-40, -20, 0, 20, 40):
        r = math.radians(a)
        beam(c, 0.42, 0.50, 0.42 + math.cos(r) * 0.60, 0.50 + math.sin(r) * 0.60, e, 0.03, 0.08)
    beam(c, 0.0, 0.50, 0.36, 0.50, e, 0.05, 0.05)
    lens = ell(0.40, 0.50, 0.07, 0.20)
    lit(c, lens, rgrad((255, 255, 255), (190, 220, 255), 0.38, 0.44, 0.2), glowc=(220, 240, 255), gr=12, sh=True)
    return K.finish(c)


def sinker_drill():
    """Showpiece: a spiralled drill bit grinding down into the foe."""
    c = bg(195, 0.55, 0.32, cy=0.8)
    burst(c, 0.5, 0.88, 0.30, 0.12, 10, EL['gold'], 23, 0.3, core=False)
    paint_rocks(c, [rock(0.20, 0.82, 0.05, 31), rock(0.80, 0.80, 0.05, 32), rock(0.30, 0.66, 0.03, 33), rock(0.72, 0.64, 0.03, 34)])
    body = poly([(0.30, 0.16), (0.70, 0.16), (0.5, 0.88)])
    lit(c, body, K.linear((150, 160, 190, 255), (240, 245, 255, 255), 0), glowc=(200, 240, 255), gr=14, sh=True)
    flutes = M(lambda d: [d.polygon(pts([(0.30 + 0.04 * (k * 0.9) + 0.0, 0.16 + 0.12 * k), (0.70 - 0.04 * k * 0.9, 0.16 + 0.12 * k + 0.06),
                                         (0.70 - 0.04 * (k + 0.5) * 0.9, 0.16 + 0.12 * k + 0.10), (0.30 + 0.04 * (k + 0.5) * 0.9, 0.16 + 0.12 * k + 0.04)]),
                                    fill=255) for k in range(6)])
    K.fill(c, sc(soften(mul(flutes, body), 1.5), 0.65), (40, 50, 80, 255))
    collar = poly([(0.26, 0.08), (0.74, 0.08), (0.74, 0.17), (0.26, 0.17)])
    lit(c, collar, (255, 220, 120), (170, 110, 30), sh=True)
    speed(c, 0, [(0.22, 0.40, 0.1), (0.86, 0.36, -0.1)], (255, 255, 255))
    arcs = M(lambda d: [GA.arc_arrow(d, 0.5, 0.30, 0.26, 200, 330, 0.025, 0.04)])
    lit(c, arcs, (230, 250, 255), glowc=(150, 220, 255), gr=6)
    return K.finish(c)


def molting_plumage():
    """A burst of shed plumage, glittering as it strips away magic."""
    c = bg(180, 0.45, 0.36)
    for k in range(7):
        a = -90 + k * 360 / 7
        r = math.radians(a)
        feather(c, 0.5 + math.cos(r) * 0.12, 0.5 + math.sin(r) * 0.12, 0.40, a + 90, EL['blu'], (255, 255, 255), (150, 220, 240))
    lit(c, ell(0.5, 0.5, 0.07), (255, 255, 255), glowc=(180, 240, 255), gr=14, gs=1.6)
    return K.finish(c)


def nectarous_deluge():
    """A flood of sticky, poisonous nectar."""
    c = bg(35, 0.6, 0.30)
    e = E((255, 250, 210), (255, 200, 60), (190, 110, 10), (255, 200, 80), 42)
    flood = poly([(0.14, 0.0), (0.86, 0.0), (0.80, 0.30), (0.74, 0.50), (0.66, 0.40), (0.60, 0.66), (0.52, 0.48), (0.44, 0.74),
                  (0.36, 0.46), (0.28, 0.56), (0.22, 0.30)])
    lit(c, flood, e.hi, e.mid, glowc=e.glow, gr=16, sh=True)
    shine(c, flood, -0.02, 0.0, 0.5)
    pool = ell(0.5, 0.86, 0.36, 0.08)
    lit(c, pool, e.mid, e.lo, glowc=e.glow, gr=10)
    comb = M(lambda d: [d.polygon(pts([(x + math.cos(math.radians(60 * k)) * 0.05, y + math.sin(math.radians(60 * k)) * 0.05)
                                       for k in range(6)]), outline=255, width=int(0.01 * W))
                        for x, y in ((0.40, 0.14), (0.49, 0.19), (0.58, 0.14), (0.49, 0.09))])
    K.fill(c, sc(soften(comb), 0.6), (170, 100, 10, 255))
    motes(c, 221, 8, (0.2, 0.6, 0.8, 0.9), (0.008, 0.015), (200, 255, 120), (170, 240, 80))
    return K.finish(c)


def sweeping_gouge():
    """A long, low sweep of claws gouging across."""
    c = bg(160, 0.5, 0.30)
    for k, (y, w) in enumerate(((0.38, 0.06), (0.52, 0.07), (0.66, 0.06))):
        slash(c, 0.08, y + 0.10, 0.92, y - 0.06, 0.07, EL['light'] if k == 1 else EL['blu'], w, glowc=(120, 255, 230))
    speed(c, -8, [(0.20, 0.30, 0.1), (0.16, 0.80, 0.1)], (220, 255, 250))
    return K.finish(c)


def atra_libations():
    """A dark libation poured out, draining the foe's life."""
    c = bg(320, 0.45, 0.22)
    e = E((255, 220, 240), (170, 40, 100), (70, 0, 40), (230, 60, 140), 330)
    stream = tubem(bez((0.40, 0.30), (0.60, 0.40), (0.62, 0.86)), 0.05, 0.03)
    lit(c, stream, e.mid, e.lo, glowc=e.glow, gr=10)
    pool = ell(0.62, 0.86, 0.20, 0.05)
    lit(c, pool, e.mid, e.lo, glowc=e.glow, gr=10)
    bowl = M(lambda d: d.chord(pts([(0.12, 0.04), (0.52, 0.40)]), 0, 180, fill=255))
    cup = rot(add(bowl, poly([(0.30, 0.38), (0.34, 0.38), (0.34, 0.54), (0.30, 0.54)]), poly([(0.22, 0.54), (0.42, 0.54), (0.42, 0.58), (0.22, 0.58)])),
              -35, 0.32, 0.30)
    lit(c, cup, (255, 230, 150), (170, 110, 30), glowc=(255, 200, 120), gr=12, sh=True)
    shine(c, cup, -0.01, -0.02, 0.5)
    for x, y in ((0.80, 0.50), (0.84, 0.66)):
        lit(c, drop(x, y - 0.06, y + 0.04, 0.035), (255, 150, 160), (180, 10, 50), glowc=(255, 60, 100), gr=6)
    return K.finish(c)


def lizard(c, cx, cy, s, ang, skin=((180, 230, 140), (60, 120, 50))):
    body = poly(xf(tube([(-0.30, 0), (-0.10, 0.02), (0.12, 0), (0.30, 0)], 0.14, 0.10), cx, cy, s, ang))
    head = poly(xf([(0.28, -0.06), (0.46, -0.02), (0.48, 0.02), (0.28, 0.07)], cx, cy, s, ang))
    tail = poly(xf(tube(bez((-0.30, 0.0), (-0.52, 0.06), (-0.64, -0.10)), 0.10, 0.01), cx, cy, s, ang))
    legs = add(*[poly(xf(tube([(x, 0), (x + 0.08 * sx, 0.16 * sy), (x + 0.14 * sx, 0.18 * sy)], 0.045, 0.03), cx, cy, s, ang))
                 for x, sx, sy in ((0.16, 1, 1), (0.16, 1, -1), (-0.18, -1, 1), (-0.18, -1, -1))])
    m = add(body, head, tail, legs)
    lit(c, m, skin[0], skin[1], glowc=(220, 255, 180), gr=10, sh=True)
    shine(c, m, -0.01, -0.02, 0.4)
    return m


def saurian_slide():
    """A lizard skidding in on its belly, kicking up dust."""
    c = bg(40, 0.5, 0.40)
    e = EL['earth']
    cloud(c, 231, (0.06, 0.56, 0.46, 0.90), e, 8, (0.05, 0.09), 0.8)
    speed(c, -30, [(0.40, 0.62, 0.22), (0.46, 0.74, 0.2), (0.34, 0.50, 0.16)], (255, 240, 210))
    lizard(c, 0.58, 0.48, 0.80, -30)
    return K.finish(c)


def palling_salvo():
    """A salvo of shrouded dark shots."""
    c = bg(270, 0.4, 0.22)
    e = EL['dark']
    for x, y, r in ((0.70, 0.30, 0.10), (0.54, 0.56, 0.12), (0.30, 0.76, 0.08)):
        tr = tubem([(x - 0.30, y - 0.10 * 0), (x, y)], 0.01, r * 1.5)
        tr = tubem([(x - 0.34, y + 0.20), (x, y)], 0.01, r * 1.4)
        K.glow(c, tr, A(e.glow), 12, 1.0)
        K.fill(c, sc(soften(tr, 5), 0.6), A(e.mid))
        o = ell(x, y, r)
        K.glow(c, o, (170, 80, 255, 255), 18, 1.5)
        lit(c, o, rgrad((220, 170, 255), (30, 0, 60), x - r * 0.3, y - r * 0.3, r * 1.1))
    return K.finish(c)


def thunderbolt():
    """A colossal thunderbolt that stuns everything around."""
    c = bg(250, 0.55, 0.26, cy=0.3)
    cloud(c, 241, (0.08, 0.02, 0.92, 0.22), E((230, 230, 255), (140, 130, 190), (50, 40, 90), (160, 150, 230), 250), 12,
          (0.08, 0.12), 0.9)
    bolt_pts = [(0.56, 0.12), (0.30, 0.52), (0.46, 0.52), (0.34, 0.92), (0.72, 0.42), (0.55, 0.42), (0.68, 0.12)]
    m = poly(bolt_pts)
    lit(c, m, (255, 255, 255), (255, 230, 90), glowc=(255, 240, 140), gr=26, gs=1.5)
    side = M(lambda d: [d.line(pts([(0.40, 0.36), (0.24, 0.42), (0.18, 0.56)]), fill=255, width=int(0.016 * W)),
                        d.line(pts([(0.64, 0.42), (0.80, 0.50), (0.84, 0.66)]), fill=255, width=int(0.016 * W))])
    lit(c, side, (255, 255, 230), glowc=(255, 230, 120), gr=8, gs=1.4)
    sparkles(c, [(0.34, 0.92, 0.09)], (255, 240, 160))
    return K.finish(c)


def harden_shell():
    """A tortoise's shell hardened like stone."""
    c = bg(100, 0.45, 0.34)
    sh = M(lambda d: d.chord(pts([(0.14, 0.28), (0.86, 0.96)]), 180, 360, fill=255))
    lit(c, sh, rgrad((200, 220, 140), (70, 100, 40), 0.42, 0.40, 0.4), glowc=(220, 255, 170), gr=16, sh=True)
    hexes = M(lambda d: [d.polygon(pts([(x + math.cos(math.radians(60 * k)) * 0.09, y + math.sin(math.radians(60 * k)) * 0.08)
                                        for k in range(6)]), outline=255, width=int(0.018 * W))
                         for x, y in ((0.5, 0.42), (0.34, 0.52), (0.66, 0.52), (0.5, 0.58), (0.22, 0.60), (0.78, 0.60))])
    K.fill(c, sc(soften(mul(hexes, sh)), 0.75), (50, 70, 20, 255))
    rim = poly([(0.10, 0.60), (0.90, 0.60), (0.86, 0.68), (0.14, 0.68)])
    lit(c, rim, (220, 200, 150), (130, 100, 60), sh=True)
    shine(c, sh, -0.02, -0.04, 0.5)
    arrow_mark(c, 0.80, 0.22, 0.14, True, EL['gold'])
    return K.finish(c)


def absolute_terror():
    """A dragon's stare of absolute terror."""
    c = bg(0, 0.7, 0.22)
    rays(c, 0.5, 0.5, 14, (255, 60, 40), alpha=100, width=0.06)
    scales = M(lambda d: [d.arc(pts([(x - 0.07, y - 0.04), (x + 0.07, y + 0.06)]), 0, 180, fill=255, width=int(0.012 * W))
                          for x in (0.16, 0.30, 0.44, 0.58, 0.72, 0.86) for y in (0.18, 0.80)])
    K.fill(c, sc(soften(scales), 0.4), (255, 120, 80, 255))
    eye(c, 0.5, 0.5, 0.40, 0.17, (255, 150, 20), slit=True, lid=(60, 0, 0), glowc=(255, 60, 30), ir=0.16)
    return K.finish(c)


SPELLS.update({
    'Tem. Upheaval': tem_upheaval, 'Rending Deluge': rending_deluge, 'Embalming Earth': embalming_earth,
    'Paralyzing Triad': paralyzing_triad, 'Foul Waters': foul_waters, 'Glutinous Dart': glutinous_dart,
    'Retinal Glare': retinal_glare, 'Subduction': subduction, 'Thrashing Assault': thrashing_assault,
    'Erratic Flutter': erratic_flutter, 'Restoral': restoral, 'Rail Cannon': rail_cannon,
    'Diffusion Ray': diffusion_ray, 'Sinker Drill': sinker_drill, 'Molting Plumage': molting_plumage,
    'Nectarous Deluge': nectarous_deluge, 'Sweeping Gouge': sweeping_gouge, 'Atra. Libations': atra_libations,
    'Saurian Slide': saurian_slide, 'Palling Salvo': palling_salvo, 'Thunderbolt': thunderbolt,
    'Harden Shell': harden_shell, 'Absolute Terror': absolute_terror,
})
def searing_tempest():
    """Showpiece: a tornado of fire, flames whipping around a white-hot eye."""
    c = bg(12, 0.85, 0.36, cy=0.55)
    e = EL['fire']
    rays(c, 0.5, 0.52, 14, (255, 180, 90), alpha=60)
    for k in range(6):
        y = 0.18 + k * 0.12
        rx = 0.10 + 0.06 * (5 - k) * 0.9 if False else 0.40 - k * 0.05
        path = arcp(0.5, y, rx, 0.06, 200 + k * 25, 470 + k * 25, 40)
        m = tubem(path, 0.012, 0.075)
        K.glow(c, m, A(e.glow), 14, 1.3)
        lit(c, m, (255, 248, 190), (255, 110, 30), soft=2)
    fl = M(lambda d: [GA.flame(d, 0.5, 0.92, 0.10, 0.50), GA.flame(d, 0.38, 0.92, 0.05, 0.22, -0.03),
                      GA.flame(d, 0.62, 0.92, 0.05, 0.24, 0.03)])
    lit(c, fl, (255, 255, 230), (255, 150, 40), glowc=(255, 200, 100), gr=14, gs=1.4, ang=270)
    motes(c, 251, 22, (0.1, 0.1, 0.9, 0.9), (0.006, 0.014), (255, 230, 150), e.glow)
    return K.finish(c)


def blinding_fulgor():
    """Showpiece: a blinding flare of holy brilliance, haloed in rings of light."""
    c = bg(48, 0.55, 0.50, cy=0.5)
    rays(c, 0.5, 0.5, 24, (255, 255, 230), alpha=120, width=0.035)
    for r, w in ((0.40, 0.012), (0.30, 0.018)):
        lit(c, ring(0.5, 0.5, r, r, w), (255, 255, 240), glowc=(255, 240, 170), gr=8, gs=1.3)
    st = poly(star_pts(0.5, 0.5, 4, 0.46, 0.06))
    lit(c, st, (255, 255, 255), (255, 240, 180), glowc=(255, 250, 200), gr=24, gs=1.6)
    st2 = rot(poly(star_pts(0.5, 0.5, 4, 0.26, 0.05)), 45)
    lit(c, st2, (255, 255, 255), glowc=(255, 240, 180), gr=10, gs=1.4)
    lit(c, ell(0.5, 0.5, 0.10), (255, 255, 255), glowc=(255, 255, 255), gr=26, gs=2.0)
    return K.finish(c)


def spectral_floe():
    """Showpiece: spectral ice floes erupting from the ground, a ghostly chill haunting them."""
    c = bg(200, 0.7, 0.32, cy=0.7)
    e = EL['ice']
    wash(c, ell(0.5, 0.40, 0.34, 0.26), (170, 255, 230), 30, 0.55)
    sk = M(lambda d: GB.skull(d, 0.5, 0.36, 0.62))
    K.fill(c, sc(blur(sk, 4), 0.45), (210, 255, 240, 255))
    spires = [(0.50, 0.88, 0.13, 0.62), (0.30, 0.90, 0.10, 0.46), (0.70, 0.90, 0.10, 0.48), (0.16, 0.92, 0.07, 0.28),
              (0.84, 0.92, 0.07, 0.30)]
    for x, base, w, h in sorted(spires, key=lambda s_: s_[3]):
        sp = poly([(x - w, base), (x - w * 0.6, base - h * 0.7), (x, base - h), (x + w * 0.7, base - h * 0.65), (x + w, base)])
        lit(c, sp, (255, 255, 255), (90, 170, 230), glowc=(150, 240, 255), gr=12, gs=1.2, sh=True)
        K.fill(c, sc(soften(poly([(x, base - h), (x + w * 0.7, base - h * 0.65), (x + w, base), (x + w * 0.1, base)])), 0.45),
               (40, 100, 180, 255))
    floor = ell(0.5, 0.92, 0.46, 0.06)
    lit(c, floor, (230, 250, 255), (120, 190, 230), glowc=e.glow, gr=8)
    sparkles(c, [(0.30, 0.30, 0.06), (0.80, 0.22, 0.05)], (180, 255, 240))
    return K.finish(c)


def scouring_spate():
    """A spate of rushing flood water, spiralling up and scouring all."""
    c = bg(220, 0.7, 0.30)
    e = EL['water']
    for k in range(3):
        path = [(0.5 + math.cos(t / 40 * math.pi * 3 + k * 2.1) * (0.36 - 0.24 * t / 40), 0.90 - 0.76 * t / 40) for t in range(41)]
        m = tubem(path, 0.13, 0.03)
        lit(c, m, rgrad(e.hi, e.mid, 0.5, 0.3, 0.6), glowc=e.glow, gr=14, gs=1.2, sh=True)
        K.fill(c, sc(soften(tubem(path, 0.03, 0.008)), 0.8), (255, 255, 255, 255))
    for x, y in ((0.20, 0.24), (0.82, 0.30), (0.76, 0.12)):
        lit(c, drop(x, y - 0.04, y + 0.04, 0.025), e.hi, e.mid, glowc=e.glow, gr=6)
    return K.finish(c)


def anvil_lightning():
    """Showpiece: lightning hammering down onto an anvil, sparks exploding outward."""
    c = bg(270, 0.65, 0.28, cy=0.4)
    e = EL['thunder']
    rays(c, 0.5, 0.52, 14, (230, 190, 255), alpha=70)
    bolt = poly([(0.54, 0.0), (0.40, 0.22), (0.50, 0.24), (0.38, 0.46), (0.48, 0.47), (0.44, 0.58), (0.60, 0.38), (0.52, 0.37),
                 (0.64, 0.18), (0.56, 0.17), (0.64, 0.0)])
    lit(c, bolt, (255, 255, 255), (255, 235, 140), glowc=(240, 200, 255), gr=22, gs=1.6)
    burst(c, 0.47, 0.58, 0.30, 0.10, 12, E((255, 255, 255), (255, 240, 160), (200, 150, 50), (255, 220, 140), 50), 9, 0.4)
    anvil = poly([(0.12, 0.60), (0.80, 0.60), (0.80, 0.66), (0.70, 0.70), (0.62, 0.70), (0.58, 0.78), (0.70, 0.86), (0.70, 0.92),
                  (0.26, 0.92), (0.26, 0.86), (0.38, 0.78), (0.34, 0.70), (0.24, 0.70), (0.12, 0.64)])
    horn_ = poly(bez3((0.12, 0.60), (0.04, 0.60), (0.02, 0.62), (0.0, 0.64), 8) + [(0.12, 0.66)])
    m = add(anvil, horn_)
    lit(c, m, (200, 200, 220), (40, 40, 60), glowc=(200, 160, 255), gr=12, sh=True)
    top = poly([(0.12, 0.60), (0.80, 0.60), (0.80, 0.63), (0.12, 0.63)])
    lit(c, top, (255, 255, 255), (220, 200, 255), glowc=(255, 255, 255), gr=6, gs=1.4)
    for x, y, r in ((0.20, 0.44, 0.05), (0.76, 0.42, 0.06), (0.86, 0.56, 0.04), (0.14, 0.54, 0.035)):
        sparkles(c, [(x, y, r)], (255, 230, 140))
    return K.finish(c)


def silent_storm():
    """A hushed, howling storm that steals the voice."""
    c = bg(150, 0.35, 0.26)
    e = E((235, 250, 240), (150, 210, 180), (50, 110, 80), (140, 230, 190), 150)
    vortex(c, 0.5, 0.48, 0.44, 4, e, 1.0, 0.055, 0, ry=0.8, hi=False)
    bub = add(ell(0.5, 0.46, 0.17, 0.13), poly([(0.44, 0.56), (0.40, 0.68), (0.52, 0.58)]))
    lit(c, bub, (255, 255, 255), (200, 220, 220), glowc=(200, 255, 230), gr=10, sh=True)
    dots_ = add(ell(0.43, 0.46, 0.02), ell(0.5, 0.46, 0.02), ell(0.57, 0.46, 0.02))
    lit(c, dots_, (60, 80, 80), soft=1)
    x = M(lambda d: [d.line(pts([(0.34, 0.30), (0.66, 0.62)]), fill=255, width=int(0.035 * W)),
                     d.line(pts([(0.66, 0.30), (0.34, 0.62)]), fill=255, width=int(0.035 * W))])
    lit(c, x, (255, 140, 140), (220, 40, 40), glowc=(255, 60, 60), gr=8, sh=True)
    return K.finish(c)


def entomb():
    """Showpiece: jagged stone erupting from the earth to close over its victim like a tomb."""
    c = bg(28, 0.75, 0.24, cy=0.62)
    e = EL['earth']
    rays(c, 0.5, 0.62, 16, (255, 210, 130), alpha=90)
    glowm = ell(0.5, 0.60, 0.26, 0.30)
    K.glow(c, glowm, (255, 190, 90, 255), 40, 1.6)
    burst(c, 0.5, 0.62, 0.34, 0.12, 12, E((255, 250, 220), (255, 200, 110), (200, 120, 40), (255, 180, 80), 36), 5, 0.4)
    fig = add(ell(0.5, 0.36, 0.06, 0.065), poly([(0.40, 0.46), (0.60, 0.46), (0.56, 0.86), (0.44, 0.86)]),
              tubem([(0.41, 0.48), (0.34, 0.60), (0.32, 0.70)], 0.05), tubem([(0.59, 0.48), (0.66, 0.60), (0.68, 0.70)], 0.05))
    out = fig.filter(ImageFilter.MaxFilter(7))
    K.fill(c, soften(out, 1.5), (40, 22, 10, 255))
    lit(c, fig, (220, 200, 170), (120, 100, 80))
    shards = [((0.04, 0.94), (0.30, 0.94), (0.42, 0.18)), ((0.70, 0.94), (0.96, 0.94), (0.58, 0.16)),
              ((0.20, 0.94), (0.42, 0.94), (0.45, 0.50)), ((0.58, 0.94), (0.80, 0.94), (0.55, 0.48))]
    for k, (a, b, tip) in enumerate(shards):
        mid = ((a[0] + b[0]) / 2 + (tip[0] - (a[0] + b[0]) / 2) * 0.5 + (0.03 if k % 2 else -0.03),
               (a[1] + tip[1]) / 2)
        m = poly([a, mid, tip, b])
        out = m.filter(ImageFilter.MaxFilter(7))
        K.shadow(c, out, 5, 8, 8, 180)
        K.fill(c, soften(out, 1.2), (30, 16, 6, 255))
        lit(c, m, rgrad((250, 220, 170), (110, 70, 36), tip[0], tip[1] + 0.10, 0.6))
        facet = poly([mid, tip, b])
        K.fill(c, sc(soften(facet, 1.2), 0.45), (60, 36, 16, 255))
    cracks = M(lambda d: [d.line(pts(seq), fill=255, width=int(0.012 * W)) for seq in
                          (((0.30, 0.86), (0.33, 0.70), (0.30, 0.60)), ((0.70, 0.86), (0.67, 0.72), (0.70, 0.62)),
                           ((0.14, 0.88), (0.17, 0.76)))])
    lit(c, cracks, (255, 250, 210), (255, 190, 90), glowc=(255, 180, 60), gr=8, gs=1.6)
    ground = poly([(0.0, 0.90), (0.30, 0.88), (0.5, 0.92), (0.70, 0.88), (1.0, 0.90), (1, 1), (0, 1)])
    lit(c, ground, (150, 100, 50), (50, 30, 12))
    paint_rocks(c, [rock(0.18, 0.30, 0.045, 41), rock(0.82, 0.32, 0.05, 42), rock(0.30, 0.14, 0.03, 43),
                    rock(0.72, 0.12, 0.035, 44)])
    motes(c, 7, 14, (0.10, 0.20, 0.90, 0.85), (0.006, 0.012), (255, 230, 170), (255, 190, 90))
    return K.finish(c)


def tenebral_crush():
    """Showpiece: a sphere of darkness crashing down, crushing the ground and the foe's guard."""
    c = bg(285, 0.55, 0.22, cy=0.75)
    e = EL['dark']
    imp = poly(star_pts(0.5, 0.80, 12, 0.46, 0.14, -90, 0.3, 13))
    K.glow(c, imp, (190, 80, 255, 255), 22, 1.3)
    lit(c, imp, rgrad((255, 220, 255), (120, 40, 200), 0.5, 0.80, 0.4))
    shockring(c, 0.5, 0.82, 0.44, 0.08, e, 0.025)
    speed(c, 90, [(0.30, 0.30, 0.22), (0.70, 0.30, 0.22), (0.40, 0.16, 0.14), (0.60, 0.16, 0.14)], (220, 170, 255), 0.02, 0.8)
    o = ell(0.5, 0.50, 0.24)
    K.glow(c, o, (180, 80, 255, 255), 24, 1.7)
    lit(c, o, rgrad((120, 60, 170), (10, 0, 20), 0.44, 0.42, 0.26), sh=True)
    rim = sub(o, ell(0.47, 0.47, 0.23))
    K.fill(c, sc(soften(rim, 3), 0.9), (240, 190, 255, 255))
    swirl = M(lambda d: d.line(pts([(0.5 + math.cos(t / 30 * 8) * 0.16 * t / 30, 0.50 + math.sin(t / 30 * 8) * 0.16 * t / 30)
                                    for t in range(31)]), fill=255, width=int(0.016 * W)))
    K.fill(c, sc(soften(swirl, 2), 0.6), (200, 120, 255, 255))
    arrow_mark(c, 0.84, 0.22, 0.12, False, EL['blood'])
    return K.finish(c)


def gates_of_hades():
    """The gates of Hades thrown open on a sea of flame."""
    c = bg(5, 0.8, 0.26)
    e = EL['fire']
    inner = poly([(0.30, 0.86), (0.30, 0.40)] + arcp(0.5, 0.40, 0.20, 0.22, 180, 360, 20) + [(0.70, 0.86)])
    lit(c, inner, rgrad((255, 250, 200), (255, 90, 20), 0.5, 0.60, 0.4), glowc=e.glow, gr=20, gs=1.4)
    fl = M(lambda d: [GA.flame(d, x, 0.88, 0.07, h) for x, h in ((0.36, 0.40), (0.50, 0.52), (0.64, 0.42))])
    lit(c, fl, (255, 255, 230), (255, 170, 60), ang=270)
    gate = sub(poly([(0.20, 0.90), (0.20, 0.40)] + arcp(0.5, 0.40, 0.30, 0.32, 180, 360, 24) + [(0.80, 0.90)]), inner)
    lit(c, gate, (110, 80, 80), (30, 16, 20), glowc=(255, 80, 30), gr=10, sh=True)
    spikes = add(*[poly([(x - 0.03, 0.12 + abs(x - 0.5) * 0.4), (x, 0.04 + abs(x - 0.5) * 0.4), (x + 0.03, 0.12 + abs(x - 0.5) * 0.4)])
                   for x in (0.32, 0.5, 0.68)])
    lit(c, spikes, (130, 100, 100), (40, 20, 20))
    skull(c, 0.5, 0.15, 0.20, (240, 220, 200), (150, 120, 100), glowc=(255, 100, 40))
    return K.finish(c)


def tourbillion():
    """Showpiece: a roaring whirlwind funnel, debris flung outward."""
    c = bg(145, 0.70, 0.32, cy=0.40)
    e = EL['wind']
    rays(c, 0.5, 0.30, 12, (190, 255, 210), alpha=60)
    n = 9
    back, front = K.mask(), K.mask()
    bd, fd = ImageDraw.Draw(back), ImageDraw.Draw(front)
    for k in range(n):
        t = k / (n - 1)
        cy = 0.14 + 0.74 * t
        cx = 0.5 + 0.06 * math.sin(t * 3.2)
        rx = 0.40 * (1 - t) ** 1.3 + 0.05
        ry = rx * 0.26
        w = int((0.034 - 0.018 * t) * W)
        box = pts([(cx - rx, cy - ry), (cx + rx, cy + ry)])
        bd.arc(box, 180, 360, fill=255, width=w)
        fd.arc(box, 0, 180, fill=255, width=w)
        fd.arc(box, 180, 215, fill=255, width=w)
    funnel = poly([(0.10, 0.14), (0.90, 0.14), (0.58, 0.86), (0.52, 0.92), (0.48, 0.86)])
    K.glow(c, funnel, A(e.glow), 26, 0.9)
    wash(c, funnel, e.lo, 10, 0.7)
    lit(c, back, e.mid, e.lo, glowc=e.glow, gr=8, gs=1.0)
    K.fill(c, sc(blur(funnel, 14), 0.35), A(e.mid))
    lit(c, front, (255, 255, 255), e.hi, glowc=e.glow, gr=12, gs=1.5)
    for x, y, a, s in ((0.14, 0.42, 30, 0.035), (0.86, 0.56, -40, 0.03), (0.22, 0.70, 60, 0.025), (0.80, 0.30, 10, 0.03)):
        lf = rot(ell(x, y, s * 1.6, s * 0.7), a, x, y)
        lit(c, lf, (220, 255, 180), (60, 160, 60), glowc=(160, 255, 160), gr=4)
    speed(c, 200, [(0.10, 0.48, 0.12), (0.12, 0.60, 0.10)], (230, 255, 235), 0.016, 0.7)
    speed(c, -20, [(0.92, 0.40, 0.12), (0.88, 0.66, 0.10)], (230, 255, 235), 0.016, 0.7)
    return K.finish(c)


def pyric_bulwark():
    """A bulwark of fire: a burning shield that turns aside blows."""
    c = bg(15, 0.7, 0.30)
    fl = M(lambda d: [GA.flame(d, 0.5, 0.92, 0.38, 0.86), GA.flame(d, 0.22, 0.92, 0.12, 0.50, -0.06),
                      GA.flame(d, 0.78, 0.92, 0.12, 0.52, 0.06)])
    K.glow(c, fl, (255, 100, 30, 255), 22, 1.2)
    K.fill(c, sc(soften(fl, 4), 0.85), K.linear((255, 230, 140, 255), (230, 50, 20, 255), 270))
    sh_ = M(lambda d: GB.draw_shield(d, 0.5, 0.52, 0.98))
    lit(c, sh_, (255, 240, 200), (190, 110, 40), glowc=(255, 220, 140), gr=12, sh=True)
    inner = M(lambda d: GB.draw_shield(d, 0.5, 0.53, 0.98, inset=0.22))
    lit(c, inner, rgrad((255, 230, 120), (220, 60, 20), 0.5, 0.44, 0.3))
    f2 = M(lambda d: GA.flame(d, 0.5, 0.70, 0.08, 0.30))
    lit(c, f2, (255, 255, 230), (255, 180, 60), ang=270)
    return K.finish(c)


def anchor(cx, cy, s, ang=0):
    shank = poly(xf([(-0.03, -0.30), (0.03, -0.30), (0.03, 0.30), (-0.03, 0.30)], cx, cy, s, ang))
    ringm = poly(xf(tube(arcp(0, -0.36, 0.07, 0.07, 0, 360, 24), 0.035), cx, cy, s, ang))
    bar = poly(xf([(-0.16, -0.22), (0.16, -0.22), (0.16, -0.17), (-0.16, -0.17)], cx, cy, s, ang))
    arms = poly(xf(tube(arcp(0, 0.06, 0.26, 0.26, 20, 160, 24), 0.06), cx, cy, s, ang))
    flukes = add(poly(xf([(0.18, 0.12), (0.34, 0.08), (0.26, 0.26)], cx, cy, s, ang)),
                 poly(xf([(-0.18, 0.12), (-0.34, 0.08), (-0.26, 0.26)], cx, cy, s, ang)))
    return add(shank, ringm, bar, arms, flukes)


def bilgestorm():
    """A pirate's anchor swung through a storm of bilge water."""
    c = bg(200, 0.6, 0.28)
    e = EL['water']
    vortex(c, 0.5, 0.5, 0.44, 3, E((220, 240, 230), (100, 170, 160), (30, 80, 80), (100, 200, 190), 180), 0.8, 0.05, 0, hi=False)
    m = anchor(0.5, 0.52, 1.0, 25)
    lit(c, m, (230, 235, 245), (90, 100, 120), glowc=(160, 230, 255), gr=12, sh=True)
    shine(c, m, -0.01, -0.02, 0.45)
    for x, y in ((0.20, 0.30), (0.80, 0.70), (0.24, 0.76)):
        lit(c, drop(x, y - 0.04, y + 0.04, 0.025), e.hi, e.mid, glowc=e.glow, gr=6)
    return K.finish(c)


def bloodrake():
    """Showpiece: a rake of crimson claws whose wounds bleed into the caster."""
    c = bg(350, 0.75, 0.26)
    e = EL['blood']
    wash(c, ell(0.5, 0.50, 0.40), (200, 20, 40), 30, 0.6)
    claws(c, 3, 0.22, 0.14, 0.62, 0.82, e, 0.14, 0.05, 0.11)
    claws(c, 3, 0.26, 0.18, 0.58, 0.76, EL['light'], 0.14, 0.04, 0.035)
    # the blood flows back in a spiral to a pulsing heart
    path = [(0.78 + math.cos(t / 30 * 4.5) * 0.14 * (1 - t / 34), 0.70 + math.sin(t / 30 * 4.5) * 0.14 * (1 - t / 34)) for t in range(31)]
    lit(c, tubem(path, 0.015, 0.035), (255, 160, 170), (200, 20, 40), glowc=(255, 40, 60), gr=8)
    hm = M(lambda d: GB.heart(d, 0.78, 0.70, 0.30))
    lit(c, hm, rgrad((255, 160, 170), (170, 0, 30), 0.75, 0.66, 0.12), glowc=(255, 40, 60), gr=14, gs=1.5, sh=True)
    for x, y in ((0.70, 0.30), (0.84, 0.42), (0.40, 0.86)):
        lit(c, drop(x, y - 0.05, y + 0.03, 0.025), (255, 150, 150), (170, 10, 30), glowc=(255, 40, 60), gr=6)
    return K.finish(c)


def droning_whirlwind():
    """A whirlwind abuzz with droning insect wings, stripping away blessings."""
    c = bg(70, 0.45, 0.30)
    vortex(c, 0.5, 0.52, 0.44, 3, EL['wind'], 0.9, 0.05, 0, ry=0.85, hi=False)
    for x, y, a in ((0.50, 0.48, 0), (0.24, 0.30, -20), (0.78, 0.70, 30)):
        s_ = 1.0 if x == 0.5 else 0.5
        w = add(*[rot(ell(x + m_ * 0.10 * s_, y - 0.06 * s_, 0.10 * s_, 0.05 * s_), m_ * 30 - a, x + m_ * 0.10 * s_, y - 0.06 * s_)
                  for m_ in (1, -1)])
        K.fill(c, sc(soften(w, 2), 0.7), (230, 250, 255, 255))
        lit(c, sub(w, ImageChops.offset(w, 0, int(0.01 * W))), (255, 255, 255), soft=1)
        b = rot(ell(x, y + 0.02 * s_, 0.05 * s_, 0.09 * s_), -a, x, y)
        lit(c, b, (255, 220, 60), (150, 90, 10), sh=True)
        st = mul(rot(M(lambda d, x=x, y=y, s_=s_: [d.line(pts([(x - 0.05 * s_, y + yy * s_), (x + 0.05 * s_, y + yy * s_)]),
                                                        fill=255, width=max(2, int(0.02 * W * s_))) for yy in (0.02, 0.07)]), -a, x, y), b)
        K.fill(c, soften(st), (30, 20, 10, 255))
    waves(c, 0.5, 0.48, -90, (0.20,), EL['gold'], 30, 0.02)
    return K.finish(c)


def shark(c, cx, cy, s, ang=0):
    body = poly(xf(bez3((0.46, 0.0), (0.30, -0.14), (-0.10, -0.14), (-0.40, -0.02), 20) + [(-0.56, -0.14), (-0.50, 0.0), (-0.56, 0.12)] +
                   bez3((-0.40, 0.02), (-0.10, 0.10), (0.30, 0.12), (0.46, 0.0), 20), cx, cy, s, ang))
    fin = poly(xf([(0.0, -0.12), (-0.08, -0.32), (-0.14, -0.12)], cx, cy, s, ang))
    pec = poly(xf([(0.10, 0.06), (0.0, 0.22), (-0.04, 0.08)], cx, cy, s, ang))
    m = add(body, fin, pec)
    lit(c, m, (200, 220, 240), (70, 90, 130), glowc=(160, 230, 255), gr=12, sh=True)
    belly = mul(poly(xf([(0.46, 0.0), (-0.40, 0.0), (-0.40, 0.2), (0.46, 0.2)], cx, cy, s, ang)), body)
    K.fill(c, sc(soften(belly, 3), 0.8), (250, 250, 255, 255))
    lit(c, ell(*xf([(0.26, -0.04)], cx, cy, s, ang)[0], 0.016 * s / 0.8), (20, 20, 30), soft=1)
    gills = M(lambda d: [d.line(pts(xf([(x, -0.06), (x - 0.02, 0.04)], cx, cy, s, ang)), fill=255, width=max(2, int(0.008 * W * s)))
                         for x in (0.14, 0.10, 0.06)])
    K.fill(c, sc(soften(gills), 0.6), (60, 70, 100, 255))
    return m


def carcharian_verve():
    """A shark's predatory verve: fury and a veil of water."""
    c = bg(205, 0.7, 0.36)
    e = EL['water']
    spl = M(lambda d: [d.polygon(pts([(0.5 + x - 0.03, 0.78), (0.5 + x * 1.3, 0.78 - h), (0.5 + x + 0.03, 0.78)]), fill=255)
                       for x, h in ((-0.30, 0.14), (-0.18, 0.22), (0.18, 0.22), (0.30, 0.14))])
    lit(c, spl, e.hi, e.mid, glowc=e.glow, gr=8)
    shark(c, 0.48, 0.48, 0.85, -30)
    wave = M(lambda d: d.line(pts([(0.04 + 0.92 * t / 30, 0.80 + 0.03 * math.sin(t / 30 * math.pi * 4)) for t in range(31)]), fill=255,
                              width=int(0.03 * W)))
    lit(c, wave, e.hi, e.mid, glowc=e.glow, gr=8)
    arrow_mark(c, 0.82, 0.22, 0.14, True, EL['gold'])
    return K.finish(c)


def blistering_roar():
    """A roar so fierce it blisters."""
    c = bg(25, 0.75, 0.32)
    fl = M(lambda d: [GA.flame(d, x, 0.96, 0.10, h, l) for x, h, l in ((0.22, 0.50, -0.04), (0.5, 0.70, 0), (0.78, 0.50, 0.04))])
    lit(c, fl, (255, 220, 120), (230, 60, 20), glowc=(255, 120, 40), gr=14, ang=270)
    roar_head(c, 0.5, 0.48, 1.0, skin=((255, 150, 110), (170, 40, 20)), mane=((255, 110, 50), (140, 20, 10)), glowc=(255, 150, 60))
    return K.finish(c)


def uproot():
    """A tree's roots torn up from the earth to lash out."""
    c = bg(95, 0.45, 0.28, cy=0.8)
    ground = poly([(0, 0.70), (0.30, 0.66), (0.40, 0.72), (0.60, 0.70), (0.70, 0.64), (1, 0.70), (1, 1), (0, 1)])
    lit(c, ground, (150, 110, 70), (60, 40, 20))
    for k, (x, a, L) in enumerate(((0.24, -110, 0.50), (0.42, -80, 0.60), (0.60, -100, 0.56), (0.76, -60, 0.46))):
        r = math.radians(a)
        path = [(x + math.cos(r) * L * t / 20 + 0.04 * math.sin(t / 20 * 5 + k), 0.72 + math.sin(r) * L * t / 20) for t in range(21)]
        root = tubem(path, 0.09, 0.008)
        lit(c, root, (220, 180, 130), (110, 70, 30), glowc=(220, 255, 160), gr=8, sh=True)
    paint_rocks(c, [rock(0.16, 0.62, 0.04, 51), rock(0.84, 0.56, 0.035, 52), rock(0.50, 0.30, 0.03, 53)])
    return K.finish(c)


def crashing_thunder():
    """Thunder crashing down in a ring of bolts."""
    c = bg(280, 0.55, 0.26, cy=0.75)
    e = EL['thunder']
    shockring(c, 0.5, 0.80, 0.42, 0.10, e, 0.03)
    for x, top, s_ in ((0.24, 0.10, 0.7), (0.76, 0.12, 0.7), (0.5, 0.0, 1.0)):
        b = poly(xf([(0.02, 0.0), (-0.10, 0.34), (0.0, 0.34), (-0.08, 0.76), (0.12, 0.26), (0.02, 0.26), (0.10, 0.0)], x, top, s_))
        lit(c, b, (255, 255, 240), (255, 220, 110), glowc=(220, 170, 255), gr=16, gs=1.5)
    burst(c, 0.5, 0.80, 0.16, 0.06, 8, EL['light'], 3, 0.2)
    return K.finish(c)


def polar_roar():
    """A polar beast's frozen roar."""
    c = bg(205, 0.6, 0.38)
    e = EL['ice']
    waves(c, 0.5, 0.56, 90, (0.32, 0.42), e, 40, 0.03)
    ears = add(ell(0.30, 0.24, 0.07), ell(0.70, 0.24, 0.07))
    head = ell(0.5, 0.46, 0.26, 0.24)
    m = add(ears, head)
    lit(c, m, rgrad((255, 255, 255), (170, 200, 230), 0.44, 0.36, 0.3), glowc=(180, 230, 255), gr=12, sh=True)
    muzzle = ell(0.5, 0.58, 0.13, 0.10)
    lit(c, muzzle, (240, 245, 255), (190, 210, 230))
    mouth = ell(0.5, 0.62, 0.08, 0.07)
    lit(c, mouth, (120, 30, 50), (50, 10, 20))
    lit(c, ell(0.5, 0.52, 0.04, 0.025), (30, 30, 40), soft=1)
    lit(c, add(ell(0.40, 0.42, 0.02), ell(0.60, 0.42, 0.02)), (30, 30, 50), soft=1)
    fangs = add(poly([(0.45, 0.57), (0.47, 0.57), (0.46, 0.62)]), poly([(0.53, 0.57), (0.55, 0.57), (0.54, 0.62)]))
    lit(c, fangs, (255, 255, 255), soft=1)
    flake(c, 0.18, 0.62, 0.07)
    flake(c, 0.82, 0.64, 0.06)
    return K.finish(c)


def mighty_guard():
    """Showpiece: a radiant guard of every blessing at once: protect, shell, haste and regen."""
    c = bg(42, 0.7, 0.42, cy=0.5)
    rays(c, 0.5, 0.5, 20, (255, 240, 180), alpha=90, width=0.05)
    emblems = ((-135, (120, 200, 255)), (-45, (200, 140, 255)), (45, (130, 255, 160)), (135, (255, 220, 120)))
    for a, col in emblems[:0]:
        r = math.radians(a)
        x, y = 0.5 + math.cos(r) * 0.30, 0.50 + math.sin(r) * 0.30
        o = ell(x, y, 0.085)
        lit(c, o, rgrad((255, 255, 255), col, x - 0.02, y - 0.02, 0.09), glowc=col, gr=12, gs=1.4, sh=True)
    sh_ = M(lambda d: GB.draw_shield(d, 0.5, 0.50, 0.90))
    lit(c, sh_, (255, 250, 220), (200, 140, 50), glowc=(255, 230, 150), gr=22, gs=1.5, sh=True)
    inner = M(lambda d: GB.draw_shield(d, 0.5, 0.51, 0.90, inset=0.2))
    lit(c, inner, rgrad((120, 220, 255), (20, 70, 170), 0.46, 0.40, 0.3))
    st = M(lambda d: GD.star(d, 0.5, 0.48, 0.15, 0.065, 4, -90))
    lit(c, st, (255, 255, 255), (255, 240, 180), glowc=(255, 250, 220), gr=10, gs=1.5)
    for a, col in emblems:
        r = math.radians(a)
        x, y = 0.5 + math.cos(r) * 0.32, 0.50 + math.sin(r) * 0.32
        o = ell(x, y, 0.075)
        lit(c, o, rgrad((255, 255, 255), col, x - 0.02, y - 0.02, 0.08), glowc=col, gr=12, gs=1.5, sh=True)
    return K.finish(c)


def cruel_joke():
    """A jester's cruel joke: a grin with doom behind it."""
    c = bg(300, 0.45, 0.22)
    hat = add(poly(bez((0.26, 0.40), (0.10, 0.24), (0.10, 0.10), 10) + [(0.40, 0.34)]),
              poly(bez((0.74, 0.40), (0.90, 0.24), (0.90, 0.10), 10) + [(0.60, 0.34)]),
              poly([(0.40, 0.36), (0.50, 0.08), (0.60, 0.36)]))
    lit(c, hat, (230, 80, 160), (120, 20, 80), glowc=(255, 120, 200), gr=10, sh=True)
    bells = add(ell(0.10, 0.10, 0.035), ell(0.90, 0.10, 0.035), ell(0.50, 0.08, 0.035))
    lit(c, bells, (255, 240, 150), (200, 150, 40))
    face = ell(0.5, 0.58, 0.22, 0.24)
    lit(c, face, rgrad((255, 255, 255), (200, 200, 220), 0.46, 0.50, 0.26), glowc=(220, 180, 255), gr=12, sh=True)
    eyes = add(poly([(0.36, 0.52), (0.46, 0.50), (0.44, 0.56)]), poly([(0.64, 0.52), (0.54, 0.50), (0.56, 0.56)]))
    lit(c, eyes, (40, 0, 40), soft=1)
    grin = M(lambda d: d.arc(pts([(0.36, 0.52), (0.64, 0.74)]), 20, 160, fill=255, width=int(0.025 * W)))
    lit(c, grin, (60, 0, 40), soft=1)
    tears = add(drop(0.40, 0.58, 0.66, 0.015), drop(0.60, 0.58, 0.66, 0.015))
    lit(c, tears, (200, 120, 255), soft=1)
    skull(c, 0.80, 0.82, 0.22, (240, 220, 255), (160, 120, 200), glowc=(200, 100, 255))
    return K.finish(c)


def cesspool():
    """A sickening cesspool swirling with filth."""
    c = bg(70, 0.45, 0.22)
    e = E((230, 230, 180), (150, 150, 70), (60, 60, 20), (170, 170, 80), 60)
    pool = ell(0.5, 0.60, 0.42, 0.30)
    lit(c, pool, rgrad((140, 130, 70), (50, 40, 10), 0.5, 0.58, 0.42), glowc=e.glow, gr=12)
    vortex(c, 0.5, 0.60, 0.34, 3, E((220, 230, 160), (150, 160, 80), (70, 70, 20), (170, 190, 80), 70), 0.9, 0.035, 0, ry=0.7, hi=False)
    for x, y, r in ((0.32, 0.42, 0.04), (0.66, 0.38, 0.03), (0.60, 0.72, 0.035)):
        lit(c, ring(x, y, r, r, 0.01), (230, 240, 190), glowc=(190, 210, 120), gr=4)
    fumes = M(lambda d: [d.line(pts([(x + 0.03 * math.sin(t / 6 * 6), 0.30 - 0.20 * t / 6) for t in range(7)]), fill=255,
                                width=int(0.025 * W)) for x in (0.40, 0.56)])
    lit(c, fumes, (220, 240, 170), glowc=(180, 220, 100), gr=6)
    return K.finish(c)


def tearing_gust():
    """A gust sharp enough to tear like claws."""
    c = bg(165, 0.5, 0.32)
    e = EL['wind']
    for k, y in enumerate((0.30, 0.50, 0.70)):
        path = [(0.06 + 0.86 * t / 30, y - 0.10 + 0.20 * t / 30 + 0.04 * math.sin(t / 30 * math.pi * 2 + k)) for t in range(31)]
        lit(c, tubem(path, 0.07, taper='both'), e.hi, e.mid, glowc=e.glow, gr=12, gs=1.3)
    for x, y in ((0.70, 0.30), (0.78, 0.56)):
        shred = poly([(x - 0.04, y - 0.05), (x + 0.05, y - 0.02), (x + 0.02, y + 0.02), (x + 0.06, y + 0.06), (x - 0.03, y + 0.03)])
        lit(c, shred, (255, 255, 240), (200, 200, 180), sh=True)
    return K.finish(c)


SPELLS.update({
    'Searing Tempest': searing_tempest, 'Blinding Fulgor': blinding_fulgor, 'Spectral Floe': spectral_floe,
    'Scouring Spate': scouring_spate, 'Anvil Lightning': anvil_lightning, 'Silent Storm': silent_storm,
    'Entomb': entomb, 'Tenebral Crush': tenebral_crush, 'Gates of Hades': gates_of_hades, 'Tourbillion': tourbillion,
    'Pyric Bulwark': pyric_bulwark, 'Bilgestorm': bilgestorm, 'Bloodrake': bloodrake,
    'Droning Whirlwind': droning_whirlwind, 'Carcharian Verve': carcharian_verve, 'Blistering Roar': blistering_roar,
    'Uproot': uproot, 'Crashing Thunder': crashing_thunder, 'Polar Roar': polar_roar, 'Mighty Guard': mighty_guard,
    'Cruel Joke': cruel_joke, 'Cesspool': cesspool, 'Tearing Gust': tearing_gust,
})
# ---- tail ----
ICONS = {('ma', n): f for n, f in SPELLS.items()}
