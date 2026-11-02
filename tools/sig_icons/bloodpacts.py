"""Signature icons, round 2: summoner Blood Pacts (Rage and Ward) of every avatar and spirit, plus the wyvern's
breaths. Each avatar keeps its own palette and emblem (as round 1's summon portraits in group_c): Carbuncle cyan with
its ruby, Cait Sith royal purple and gold, Fenrir midnight blue and the moon, Ifrit red, Titan earth, Leviathan sea
blue, Garuda green, Shiva ice, Ramuh violet thunder, Diabolos dark purple, Siren sea-green and coral, Atomos time.
Astral flow pacts are the showpieces."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_b as GB
import group_c as GC
import group_d as GD

W = K.W
p, pts = K.p, K.pts
xf = GB.xf
bg, lit, rot, minus, inter, scale, poly = GD.bg, GD.lit, GD.rot, GD.minus, GD.inter, GD.scale, GD.poly
sparkles, motes, rays, streaks = GD.sparkles, GD.motes, GD.rays, GC.streaks
arc = GC.arc
brush = GD.stroke           # brush(d, path, w0, w1): round-jointed stroke of discs
taper = GC.stroke           # taper(curve, w0, w1) -> polygon points
sh = K.shape


def col(c):
    return c + (255,) if len(c) == 3 else c


def lin(a, b, ang=90):
    return K.linear(col(a), col(b), ang)


def rad(a, b, cx=0.5, cy=0.5, r=0.4):
    return K.radial(col(a), col(b), cx, cy, r)


def add(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def circ(cx, cy, r, ry=None):
    ry = r if ry is None else ry
    return GD.ell(cx - r, cy - ry, cx + r, cy + ry)


def ring(cx, cy, r, w, ry=None):
    ry = r if ry is None else ry
    return sh(lambda d: d.ellipse(pts([(cx - r, cy - ry), (cx + r, cy + ry)]), outline=255, width=max(1, int(w * W))))


def swell(curve, w):
    """A stroke that swells from nothing to w and back (a slash, a claw mark, a gust)."""
    n = len(curve)
    left, right = [], []
    for i, (x, y) in enumerate(curve):
        a, b = curve[max(0, i - 1)], curve[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        t = i / (n - 1)
        h = w / 2 * math.sin(math.pi * t) ** 0.7
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    return left + right[::-1]


def bow(x0, y0, x1, y1, b=0.08, n=30):
    """A curve from (x0, y0) to (x1, y1) bowed sideways by b."""
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    return [(x0 + (x1 - x0) * t + nx * b * math.sin(math.pi * t), y0 + (y1 - y0) * t + ny * b * math.sin(math.pi * t))
            for t in (i / n for i in range(n + 1))]


def slashes(c, lines, w, glowc, paint, gr=14, gs=1.3, shadow=True):
    m = sh(lambda d: [d.polygon(pts(swell(bow(*l), w)), fill=255) for l in lines])
    lit(c, m, glowc, paint, gr, gs, sh=shadow)
    return m


def zigzag(x0, y0, x1, y1, n=5, amp=0.06, seed=1):
    rnd = random.Random(seed)
    out = [(x0, y0)]
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    for i in range(1, n):
        t = i / n
        s = amp * (1 if i % 2 else -1) * rnd.uniform(0.6, 1.2)
        out.append((x0 + (x1 - x0) * t + nx * s, y0 + (y1 - y0) * t + ny * s))
    out.append((x1, y1))
    return out


def bolt(c, path, w0, w1, glowc=(200, 170, 255), paint=(255, 255, 255), gr=16, gs=1.5, core=True):
    m = sh(lambda d: brush(d, path, w0, w1))
    lit(c, m, glowc, paint, gr, gs)
    return m


def ztext(c, spec, paint=(240, 240, 255), glowc=(180, 180, 255)):
    """Sleep Zs: (x, y, size) each."""
    def z(d, x, y, s):
        brush(d, [(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x - s / 2, y + s / 2), (x + s / 2, y + s / 2)],
              s * 0.22)
    m = sh(lambda d: [z(d, *t) for t in spec])
    lit(c, m, glowc, paint, 8, 1.3)


def teardrop(d, cx, cy, r, up=True):
    tip = (cx, cy - 2.3 * r) if up else (cx, cy + 2.3 * r)
    a = arc(cx, cy, r, -18, 198, 30) if up else arc(cx, cy, r, 162, 378, 30)
    d.polygon(pts([tip] + a), fill=255)


def ruby(c, cx, cy, s, glowc=(255, 50, 80), gr=16, gs=1.6, shadow=True):
    """Carbuncle's ruby: a brilliant-cut gem (table, crown, pavilion), lit from the upper left."""
    def q(seq):
        return [(cx + x * s, cy + y * s) for x, y in seq]
    outline = q([(-0.5, -0.12), (-0.3, -0.36), (0.3, -0.36), (0.5, -0.12), (0, 0.5)])
    whole = poly(outline)
    lit(c, whole, glowc, lin((255, 120, 130), (150, 0, 30)), gr, gs, sh=shadow)
    K.fill(c, K.soften(poly(q([(-0.3, -0.36), (0.3, -0.36), (0.18, -0.12), (-0.18, -0.12)]))), (255, 150, 160, 255))
    K.fill(c, K.soften(poly(q([(-0.5, -0.12), (-0.3, -0.36), (-0.18, -0.12)]))), (255, 110, 125, 255))
    K.fill(c, K.soften(poly(q([(0.5, -0.12), (0.3, -0.36), (0.18, -0.12)]))), (200, 30, 60, 255))
    K.fill(c, K.soften(poly(q([(-0.5, -0.12), (-0.18, -0.12), (0, 0.5)]))), (230, 50, 75, 255))
    K.fill(c, K.soften(poly(q([(0.5, -0.12), (0.18, -0.12), (0, 0.5)]))), (130, 0, 28, 255))
    K.fill(c, K.soften(poly(q([(-0.18, -0.12), (0.18, -0.12), (0, 0.5)]))), (190, 16, 48, 255))
    hi = poly(q([(-0.22, -0.31), (0.05, -0.31), (-0.06, -0.18), (-0.30, -0.18)]))
    K.fill(c, K.soften(hi, 2), (255, 236, 240, 200))
    return whole


def crown(d, cx, cy, s):
    """A three-pointed crown, its band at cy."""
    d.polygon(pts([(cx + x * s, cy + y * s) for x, y in
                   [(-0.30, 0.10), (-0.34, -0.22), (-0.16, -0.04), (0, -0.30), (0.16, -0.04), (0.34, -0.22),
                    (0.30, 0.10)]]), fill=255)
    for x, y in ((-0.34, -0.25), (0, -0.33), (0.34, -0.25)):
        r = 0.05 * s
        d.ellipse(pts([(cx + x * s - r, cy + y * s - r), (cx + x * s + r, cy + y * s + r)]), fill=255)


def cat_head(d, cx, cy, s, fillv=255):
    d.ellipse(pts([(cx - 0.30 * s, cy - 0.24 * s), (cx + 0.30 * s, cy + 0.26 * s)]), fill=fillv)
    for sx in (-1, 1):
        d.polygon(pts([(cx + sx * 0.28 * s, cy - 0.02 * s), (cx + sx * 0.30 * s, cy - 0.42 * s),
                       (cx + sx * 0.06 * s, cy - 0.20 * s)]), fill=fillv)


def wolf_head(d, cx, cy, s, ang=0.0, open_=False, fillv=255, flip=False):
    """A wolf's head in profile facing right (left when flip), origin at the back of the jaw."""
    if open_:
        q = [(0.44, -0.02), (0.20, -0.10), (0.06, -0.18), (0.02, -0.24), (-0.06, -0.46), (-0.14, -0.22),
             (-0.26, -0.16), (-0.36, 0.02), (-0.46, 0.34), (-0.30, 0.30), (-0.12, 0.34), (0.0, 0.22), (0.18, 0.24),
             (0.38, 0.22), (0.36, 0.16), (0.16, 0.10), (0.30, 0.04), (0.44, 0.04)]
    else:
        q = [(0.44, 0.0), (0.20, -0.08), (0.06, -0.18), (0.02, -0.24), (-0.06, -0.46), (-0.14, -0.22),
             (-0.26, -0.16), (-0.36, 0.02), (-0.46, 0.34), (-0.30, 0.30), (-0.12, 0.34), (0.0, 0.18), (0.22, 0.12),
             (0.42, 0.07)]
    if flip:
        q = [(-x, y) for x, y in q]
        ang = -ang
    d.polygon(xf(q, cx, cy, s, ang), fill=fillv)


def moon(c, cx, cy, r, glowc=(200, 210, 255), gr=30, gs=1.4, light=(255, 255, 248), dark=(196, 200, 228)):
    m = circ(cx, cy, r)
    K.glow(c, m, col(glowc), gr, gs)
    K.fill(c, K.soften(m), rad(light, dark, cx - r * 0.25, cy - r * 0.25, r * 1.2))
    cr = sh(lambda d: [d.ellipse(pts([(cx + a * r - b * r, cy + e * r - b * r), (cx + a * r + b * r, cy + e * r + b * r)]),
                                 fill=255) for a, e, b in ((0.3, 0.2, 0.18), (-0.25, 0.35, 0.12), (0.05, -0.35, 0.1),
                                                          (-0.4, -0.1, 0.08))])
    K.fill(c, scale(K.soften(inter(cr, m), 3), 0.35), col(dark))
    return m


def fist(c, cx, cy, s, glowc, skin=((255, 226, 190), (200, 120, 80)), line=(100, 40, 20), ang=0, gr=20, gs=1.3,
         knuckle=None):
    """A clenched fist from the front, shaded: lit knuckles, darker folded fingers, bold creases."""
    m = rot(sh(lambda d: K.fist_front(d, cx, cy, s)), ang, cx, cy)
    lit(c, m, glowc, lin(*skin), gr, gs, sh=True)
    low = rot(sh(lambda d: d.rectangle(pts([(cx - s, cy + 0.0 * s), (cx + s, cy + s)]), fill=255)), ang, cx, cy)
    K.fill(c, scale(K.soften(inter(m, low), 3), 0.3), col(line))
    kn = rot(sh(lambda d: [d.ellipse(pts([(cx + (-0.165 + i * 0.11 - 0.035) * s, cy - 0.205 * s),
                                          (cx + (-0.165 + i * 0.11 + 0.035) * s, cy - 0.15 * s)]), fill=255)
                           for i in range(4)]), ang, cx, cy)
    K.fill(c, scale(K.soften(kn, 3), 0.75), col(knuckle or skin[0]))
    ln = rot(sh(lambda d: [brush(d, [(cx + (-0.11 + i * 0.11) * s, cy - 0.13 * s), (cx + (-0.11 + i * 0.11) * s,
                                                                                  cy + 0.0 * s)], 0.02 * s)
                           for i in range(3)] + [brush(d, [(cx - 0.22 * s, cy + 0.02 * s), (cx + 0.10 * s, cy + 0.02 * s),
                                                           (cx + 0.12 * s, cy + 0.07 * s)], 0.02 * s)]), ang, cx, cy)
    K.fill(c, scale(K.soften(ln, 1.2), 0.85), col(line))
    return m


def flames(d, spec):
    for cx, base, w, h, lean in spec:
        GD_flame(d, cx, base, w, h, lean)


def GD_flame(d, cx, base, w, h, lean=0.0):
    left, right = [], []
    for i in range(41):
        t = i / 40
        half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
        x = cx + lean * t * t
        left.append((x - half, base - h * t))
        right.append((x + half, base - h * t))
    d.polygon(pts(left + right[::-1]), fill=255)


def fire_paint(c, outer, mid=None, core=None, glowc=(255, 110, 30)):
    K.glow(c, outer, col(glowc), 26, 1.3)
    K.fill(c, K.soften(outer), lin((255, 200, 70), (230, 60, 20), 270))
    if mid is not None:
        K.fill(c, K.soften(mid), lin((255, 236, 140), (255, 140, 40), 270))
    if core is not None:
        K.glow(c, core, (255, 255, 220, 255), 10)
        K.fill(c, K.soften(core), (255, 252, 230, 255))


def rock(d, cx, cy, r, seed=1, n=9, ry=None, fillv=255):
    rnd = random.Random(seed)
    ry = r if ry is None else ry
    q = []
    for i in range(n):
        a = math.pi * 2 * i / n + rnd.uniform(-0.2, 0.2)
        k = rnd.uniform(0.78, 1.0)
        q.append((cx + math.cos(a) * r * k, cy + math.sin(a) * ry * k))
    d.polygon(pts(q), fill=fillv)


def stone_paint(c, m, glowc=(255, 190, 110), top=(236, 204, 150), bot=(90, 58, 34), gr=14, gs=1.1, seed=1):
    """Stone: lit from the upper left of its own bounds, speckled, a bright upper edge and a dark lower one."""
    bb = m.getbbox() or (0, 0, W, W)
    x0, y0, x1, y1 = (v / W for v in bb)
    w, h = x1 - x0, y1 - y0
    lit(c, m, glowc, rad(top, bot, x0 + w * 0.3, y0 + h * 0.25, max(w, h) * 0.95), gr, gs, sh=True)
    rnd = random.Random(seed)
    sp = sh(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                       for x, y, r in [(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(0.004, 0.012))
                                       for _ in range(int(60 * w * h / 0.1) + 6)]])
    K.fill(c, scale(inter(sp, m), 0.3), (40, 24, 12, 255))
    hi = minus(m, ImageChops.offset(m, 7, 9))
    K.fill(c, scale(K.soften(hi, 2), 0.75), (255, 244, 220, 255))
    lo = minus(m, ImageChops.offset(m, -7, -9))
    K.fill(c, scale(K.soften(lo, 2), 0.55), (30, 16, 6, 255))


def snowflake(d, cx, cy, r, w=0.03, branches=True):
    for i in range(6):
        a = math.pi / 3 * i - math.pi / 2
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        brush(d, [(cx, cy), (ex, ey)], w, w * 0.6)
        if branches:
            for t, L in ((0.55, 0.32), (0.8, 0.2)):
                bx, by = cx + math.cos(a) * r * t, cy + math.sin(a) * r * t
                for da in (-0.9, 0.9):
                    brush(d, [(bx, by), (bx + math.cos(a + da) * r * L, by + math.sin(a + da) * r * L)], w * 0.7,
                          w * 0.4)


def shard(d, cx, cy, L, wd, ang):
    """A long ice shard / crystal pointing along ang (degrees)."""
    q = [(-L / 2, 0), (-L / 2 + wd, -wd), (L / 2 - wd * 1.6, -wd * 0.8), (L / 2, 0), (L / 2 - wd * 1.6, wd * 0.8),
         (-L / 2 + wd, wd)]
    d.polygon(xf(q, cx, cy, 1, ang), fill=255)


def ice_paint(c, m, glowc=(190, 240, 255), gr=16, gs=1.3, shadow=True):
    lit(c, m, glowc, lin((255, 255, 255), (130, 196, 240), 30), gr, gs, sh=shadow)


def droplet(d, cx, cy, r):
    teardrop(d, cx, cy, r, True)


def wave_crest(cx, cy, s, curl=1.0):
    """A breaking wave's crest (local, facing right): the lip curls over at the top."""
    q = [(-0.5, 0.3), (-0.42, 0.06), (-0.26, -0.16), (-0.04, -0.30), (0.18, -0.34), (0.34, -0.28), (0.42, -0.16),
         (0.36, -0.04), (0.24, -0.06), (0.24 - 0.10 * curl, -0.14), (0.12, -0.10), (0.0, 0.02), (-0.06, 0.18),
         (0.0, 0.30)]
    return [(cx + x * s, cy + y * s) for x, y in q]


def wing(d, cx, cy, s, side, n=6, spread=70, a0=-70, length=0.46, feather=0.06):
    """A feathered wing from (cx, cy), side 1 = right, -1 = left."""
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(a0 + spread * t)
        L = (length - 0.14 * t) * s
        ex, ey = cx + side * math.cos(a) * L, cy + math.sin(a) * L
        nx, ny = -math.sin(a) * feather * s, math.cos(a) * feather * s
        d.polygon(pts([(cx + side * nx, cy + ny), (ex, ey), (cx - side * nx, cy - ny)]), fill=255)


def at(x, y, cx, cy, s=1.0, ang=0.0):
    """A local point -> unit coords (as xf, without the pixel scaling)."""
    a = math.radians(ang)
    return (cx + (x * math.cos(a) - y * math.sin(a)) * s, cy + (x * math.sin(a) + y * math.cos(a)) * s)


def shield_shape(cx, top, w, h):
    return poly(GD.shield_pts(cx, top, w, h))


def hexagon(cx, cy, r, rot0=90):
    return [(cx + math.cos(math.radians(rot0 + 60 * i)) * r, cy + math.sin(math.radians(rot0 + 60 * i)) * r)
            for i in range(6)]


def hourglass(d, cx, cy, s):
    d.polygon(pts([(cx - 0.22 * s, cy - 0.40 * s), (cx + 0.22 * s, cy - 0.40 * s), (cx + 0.03 * s, cy),
                   (cx + 0.22 * s, cy + 0.40 * s), (cx - 0.22 * s, cy + 0.40 * s), (cx - 0.03 * s, cy)]), fill=255)


def up_arrow(d, cx, cy, s):
    d.polygon(pts([(cx, cy - 0.22 * s), (cx + 0.17 * s, cy - 0.02 * s), (cx + 0.06 * s, cy - 0.02 * s),
                   (cx + 0.06 * s, cy + 0.20 * s), (cx - 0.06 * s, cy + 0.20 * s), (cx - 0.06 * s, cy - 0.02 * s),
                   (cx - 0.17 * s, cy - 0.02 * s)]), fill=255)


def down_arrow(d, cx, cy, s):
    d.polygon(pts([(cx, cy + 0.22 * s), (cx + 0.17 * s, cy + 0.02 * s), (cx + 0.06 * s, cy + 0.02 * s),
                   (cx + 0.06 * s, cy - 0.20 * s), (cx - 0.06 * s, cy - 0.20 * s), (cx - 0.06 * s, cy + 0.02 * s),
                   (cx - 0.17 * s, cy + 0.02 * s)]), fill=255)


def sound_waves(c, cx, cy, radii, a0, a1, w, color, glowc, alpha=1.0):
    m = sh(lambda d: [d.polygon(pts(swell(arc(cx, cy, r, a0, a1, 30), w)), fill=255) for r in radii])
    K.glow(c, m, col(glowc), 10, 1.2 * alpha)
    K.fill(c, scale(K.soften(m), alpha), col(color))


def cross_m(cx, cy, s, t=0.09):
    return sh(lambda d: [d.rounded_rectangle(pts([(cx - t * s, cy - 0.32 * s), (cx + t * s, cy + 0.32 * s)]),
                                             radius=t * 0.5 * s * W, fill=255),
                         d.rounded_rectangle(pts([(cx - 0.32 * s, cy - t * s), (cx + 0.32 * s, cy + t * s)]),
                                             radius=t * 0.5 * s * W, fill=255)])


def burst_pts(cx, cy, n, r1, r2, rot0=-90, seed=None):
    rnd = random.Random(seed) if seed is not None else None
    out = []
    for i in range(n * 2):
        a = math.radians(rot0) + math.pi * i / n
        r = r1 if i % 2 == 0 else r2
        if rnd:
            r *= rnd.uniform(0.8, 1.1)
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


# =====================================================================================================================
# ---- Carbuncle: cyan night, the ruby ---------------------------------------------------------------------------------
def poison_nails():
    c = bg((40, 140, 120), (4, 22, 24), cy=0.4)
    lines = [(0.20, 0.20, 0.52, 0.80, 0.06), (0.36, 0.14, 0.68, 0.74, 0.06), (0.52, 0.10, 0.84, 0.66, 0.06)]
    slashes(c, lines, 0.10, (150, 255, 110), lin((250, 255, 230), (150, 230, 90), 60), 16, 1.5)
    drips = sh(lambda d: [teardrop(d, x, y, 0.035, False) for x, y in ((0.50, 0.84), (0.68, 0.79), (0.84, 0.72))])
    lit(c, drips, (120, 255, 80), lin((200, 255, 140), (60, 170, 40)), 10, 1.4)
    motes(c, 5, 12, (0.15, 0.6, 0.85, 0.95), (0.006, 0.014), (190, 120, 255), (150, 80, 255))
    ruby(c, 0.22, 0.70, 0.22, gr=10)
    return K.finish(c)


def meteorite():
    c = bg((30, 90, 140), (2, 10, 26), cx=0.35, cy=0.65)
    motes(c, 12, 18, (0.05, 0.05, 0.95, 0.6), (0.003, 0.008), (220, 240, 255), None, 200)
    trail = poly([(0.34, 0.44), (0.56, 0.66), (1.04, 0.06), (0.86, -0.08)])
    K.glow(c, trail, (120, 230, 255, 255), 26, 1.2)
    K.fill(c, K.soften(trail, 10), lin((140, 230, 255, 0), (230, 250, 255, 255), 135))
    streaks(c, [(0.60, 0.20, 0.96, -0.10), (0.48, 0.30, 0.76, 0.0), (0.66, 0.36, 1.0, 0.10)], (200, 245, 255, 255),
            0.012, 170, 3)
    head = circ(0.42, 0.58, 0.19)
    K.glow(c, head, (150, 240, 255, 255), 40, 1.8)
    K.fill(c, K.soften(head, 3), rad((255, 255, 255), (130, 220, 255), 0.38, 0.54, 0.2))
    ruby(c, 0.42, 0.58, 0.26, glowc=(255, 80, 110), gr=10, shadow=False)
    sparkles(c, [(0.22, 0.76, 0.07)], glowc=(170, 240, 255))
    return K.finish(c)


def carbuncle_body(d, cx, cy, s):
    for sx in (-1, 1):
        L, f = GC.frame(cx + sx * 0.12 * s, cy - 0.10 * s, cx + sx * 0.30 * s, cy - 0.44 * s)
        d.polygon(pts([f(0, -0.06 * s), f(L * 0.5, -0.07 * s), f(L, 0), f(L * 0.5, 0.07 * s), f(0, 0.06 * s)]),
                  fill=255)
    d.ellipse(pts([(cx - 0.23 * s, cy - 0.20 * s), (cx + 0.23 * s, cy + 0.22 * s)]), fill=255)
    d.ellipse(pts([(cx - 0.20 * s, cy + 0.10 * s), (cx + 0.20 * s, cy + 0.42 * s)]), fill=255)
    d.polygon(pts(taper([(cx + 0.16 * s, cy + 0.36 * s), (cx + 0.36 * s, cy + 0.30 * s), (cx + 0.44 * s, cy + 0.12 * s),
                         (cx + 0.40 * s, cy - 0.02 * s)], 0.10 * s, 0.02 * s)), fill=255)


def searing_light():
    c = bg((255, 200, 120), (120, 30, 20), cy=0.42, r=0.62)
    rays(c, 0.5, 0.42, 20, (255, 255, 230), width=0.07, alpha=150, blur=6)
    rays(c, 0.5, 0.42, 20, (255, 210, 120), width=0.03, alpha=130, blur=3, phase=math.pi / 20)
    sun = circ(0.5, 0.42, 0.22)
    K.glow(c, sun, (255, 255, 230, 255), 40, 1.6)
    K.fill(c, K.soften(sun, 8), (255, 255, 245, 255))
    body = sh(lambda d: carbuncle_body(d, 0.5, 0.62, 0.95))
    K.glow(c, body, (255, 250, 220, 255), 10, 1.4)
    K.fill(c, K.soften(body), lin((70, 30, 50), (20, 6, 16)))
    ruby(c, 0.5, 0.52, 0.12, glowc=(255, 60, 60), gr=16, gs=2.2, shadow=False)
    gl = sh(lambda d: K.sparkle(d, 0.5, 0.515, 0.16, 0.12))
    lit(c, gl, (255, 120, 120), (255, 245, 235), 10, 1.6)
    return K.finish(c)


def holy_mist():
    c = bg((150, 220, 220), (20, 60, 80), cy=0.3)
    rays(c, 0.5, -0.1, 9, (255, 255, 240), width=0.05, length=1.2, alpha=110, blur=10)
    rnd = random.Random(4)
    mist = sh(lambda d: [d.ellipse(pts([(x - r, y - r * 0.5), (x + r, y + r * 0.5)]), fill=255)
                         for x, y, r in [(rnd.uniform(0.05, 0.95), rnd.uniform(0.5, 0.92), rnd.uniform(0.12, 0.22))
                                         for _ in range(14)]])
    K.fill(c, scale(mist.filter(ImageFilter.GaussianBlur(14)), 0.9), (240, 255, 255, 255))
    mist2 = sh(lambda d: [d.ellipse(pts([(x - r, y - r * 0.45), (x + r, y + r * 0.45)]), fill=255)
                          for x, y, r in ((0.25, 0.62, 0.16), (0.70, 0.70, 0.2), (0.45, 0.80, 0.22))])
    K.fill(c, scale(mist2.filter(ImageFilter.GaussianBlur(8)), 0.7), (255, 255, 255, 255))
    st = sh(lambda d: K.sparkle(d, 0.5, 0.36, 0.24, 0.13))
    lit(c, st, (255, 250, 200), (255, 255, 250), 22, 1.6)
    sparkles(c, [(0.22, 0.30, 0.05), (0.78, 0.44, 0.06), (0.66, 0.20, 0.04)], glowc=(220, 255, 255))
    ruby(c, 0.5, 0.36, 0.1, gr=8, shadow=False)
    return K.finish(c)


def healing_ruby():
    c = bg((60, 180, 150), (4, 30, 26), cy=0.45)
    motes(c, 3, 22, (0.15, 0.15, 0.85, 0.9), (0.006, 0.016), (220, 255, 230), (150, 255, 180))
    cr = cross_m(0.5, 0.36, 0.78)
    K.glow(c, cr, (140, 255, 170, 255), 30, 1.3)
    K.fill(c, scale(K.soften(cr, 3), 0.75), lin((255, 255, 245), (170, 250, 190)))
    ruby(c, 0.5, 0.62, 0.42, glowc=(255, 90, 110))
    sparkles(c, [(0.74, 0.26, 0.07)])
    return K.finish(c)


def healing_ruby_ii():
    c = bg((50, 170, 170), (4, 26, 32), cy=0.5)
    aura = ring(0.5, 0.56, 0.36, 0.03, 0.24)
    lit(c, aura, (160, 255, 220), (220, 255, 240), 12, 1.4)
    for x, y, s in ((0.26, 0.34, 0.36), (0.74, 0.34, 0.36), (0.5, 0.25, 0.42)):
        cr = cross_m(x, y, s)
        lit(c, cr, (140, 255, 170), (240, 255, 240), 12, 1.4)
    ruby(c, 0.5, 0.60, 0.40, glowc=(255, 90, 110))
    motes(c, 8, 14, (0.15, 0.55, 0.85, 0.9), (0.006, 0.014), (220, 255, 230), (150, 255, 180))
    return K.finish(c)


def shining_ruby():
    c = bg((50, 120, 190), (4, 14, 40), cy=0.5)
    hx = sh(lambda d: d.polygon(pts(hexagon(0.5, 0.5, 0.38)), outline=255, width=int(0.035 * W)))
    inner = poly(hexagon(0.5, 0.5, 0.37))
    K.fill(c, scale(K.soften(inner, 4), 0.28), (160, 230, 255, 255))
    lit(c, hx, (140, 220, 255), lin((240, 255, 255), (120, 200, 255)), 16, 1.5)
    lines = sh(lambda d: [d.line(pts([(0.5, 0.5), v]), fill=255, width=int(0.008 * W)) for v in hexagon(0.5, 0.5, 0.37)])
    K.fill(c, scale(K.soften(lines), 0.4), (200, 240, 255, 255))
    ruby(c, 0.5, 0.52, 0.40, glowc=(255, 100, 140))
    sparkles(c, [(0.64, 0.38, 0.08)])
    return K.finish(c)


def glittering_ruby():
    c = bg((40, 110, 140), (4, 12, 30), cy=0.5)
    cols = [(255, 90, 60), (255, 200, 80), (120, 240, 120), (110, 220, 255), (120, 140, 255), (220, 120, 255),
            (255, 255, 230)]
    for i, cc in enumerate(cols):
        a = math.pi * 2 * i / 7 - math.pi / 2
        x, y = 0.5 + math.cos(a) * 0.33, 0.52 + math.sin(a) * 0.31
        st = sh(lambda d, x=x, y=y: K.sparkle(d, x, y, 0.085 if i % 2 == 0 else 0.065))
        K.glow(c, st, col(cc), 10, 1.6)
        K.fill(c, K.soften(st), col(tuple(min(255, v + 80) for v in cc)))
    ruby(c, 0.5, 0.54, 0.40, glowc=(255, 110, 150), gs=2.0)
    sparkles(c, [(0.42, 0.40, 0.06)])
    return K.finish(c)


def soothing_ruby():
    c = bg((70, 150, 200), (6, 18, 44), cy=0.5)
    rib = sh(lambda d: [d.polygon(pts(swell([(0.5 + math.cos(math.radians(a0 + t * 2.6)) * (0.40 - t * 0.0016),
                                              0.52 + math.sin(math.radians(a0 + t * 2.6)) * (0.30 - t * 0.0012))
                                             for t in range(0, 101, 4)], 0.07)), fill=255) for a0 in (0, 180)])
    lit(c, rib, (170, 230, 255), lin((255, 255, 255), (160, 220, 255)), 14, 1.3)
    # dark ailments drifting away and fading
    for i, (x, y, r) in enumerate(((0.18, 0.22, 0.04), (0.82, 0.20, 0.035), (0.86, 0.80, 0.03), (0.14, 0.78, 0.03))):
        m = sh(lambda d, x=x, y=y, r=r: d.polygon(pts(burst_pts(x, y, 4, r * 1.6, r * 0.6)), fill=255))
        K.fill(c, scale(K.soften(m, 2), 0.6), (150, 80, 180, 255))
    ruby(c, 0.5, 0.52, 0.40, glowc=(255, 100, 130))
    sparkles(c, [(0.62, 0.34, 0.07)], glowc=(200, 240, 255))
    return K.finish(c)


def pacifying_ruby():
    c = bg((90, 160, 170), (8, 24, 36), cy=0.6)
    rip = sh(lambda d: [d.ellipse(pts([(0.5 - r, 0.78 - r * 0.22), (0.5 + r, 0.78 + r * 0.22)]), outline=255,
                                  width=int(0.016 * W)) for r in (0.16, 0.27, 0.38)])
    lit(c, rip, (180, 240, 255), (220, 250, 255), 10, 1.2)
    calm = sh(lambda d: [d.polygon(pts(swell(arc(0.5, 0.72, r, 200, 340, 30), 0.03)), fill=255)
                         for r in (0.30, 0.40)])
    K.fill(c, scale(K.soften(calm, 2), 0.5), (230, 255, 255, 255))
    ruby(c, 0.5, 0.48, 0.42, glowc=(255, 140, 160), gs=1.3)
    ch = sh(lambda d: [brush(d, [(0.40, y), (0.5, y + 0.06), (0.60, y)], 0.03) for y in (0.10, 0.17)])
    lit(c, ch, (200, 255, 240), (240, 255, 250), 8, 1.2)
    return K.finish(c)


# ---- Cait Sith: royal purple and gold ---------------------------------------------------------------------------------
GOLD = ((255, 244, 180), (214, 150, 50))


def gold_crown(c, cx, cy, s, gr=12):
    m = sh(lambda d: crown(d, cx, cy, s))
    lit(c, m, (255, 220, 120), lin(*GOLD), gr, 1.3, sh=True)
    gem = circ(cx, cy - 0.01 * s, 0.045 * s)
    K.fill(c, K.soften(gem), (220, 40, 80, 255))


def regal_scratch():
    c = bg((150, 60, 160), (22, 6, 34), cy=0.5)
    lines = [(0.22, 0.30, 0.48, 0.88, 0.05), (0.38, 0.24, 0.66, 0.84, 0.05), (0.54, 0.22, 0.82, 0.76, 0.05)]
    slashes(c, lines, 0.10, (255, 210, 120), lin((255, 255, 236), (240, 190, 90), 60), 16, 1.5)
    gold_crown(c, 0.26, 0.20, 0.40)
    return K.finish(c)


def regal_gash():
    c = bg((170, 40, 90), (26, 4, 20), cy=0.5)
    m = slashes(c, [(0.16, 0.18, 0.84, 0.86, 0.04), (0.84, 0.20, 0.16, 0.86, -0.04)], 0.15, (255, 80, 100),
                lin((255, 250, 236), (255, 150, 140), 90), 22, 1.6)
    motes(c, 4, 14, (0.3, 0.5, 0.7, 0.95), (0.008, 0.018), (220, 30, 60), (255, 60, 80))
    gold_crown(c, 0.5, 0.22, 0.42)
    return K.finish(c)


def mewing_lullaby():
    c = bg((110, 70, 170), (14, 8, 34), cy=0.55)
    head = sh(lambda d: cat_head(d, 0.46, 0.60, 0.95))
    lit(c, head, (220, 190, 255), lin((250, 240, 255), (180, 160, 220)), 16, 1.3, sh=True)
    eyes = sh(lambda d: [d.polygon(pts(swell(arc(x, 0.60, 0.07, 20, 160, 20), 0.03)), fill=255) for x in (0.36, 0.56)])
    K.fill(c, K.soften(eyes, 0.8), (50, 30, 80, 255))
    nose = poly([(0.44, 0.67), (0.48, 0.67), (0.46, 0.70)])
    K.fill(c, K.soften(nose), (230, 120, 160, 255))
    gold_crown(c, 0.46, 0.34, 0.34)
    n = sh(lambda d: GB.note(d, 0.76, 0.40, 0.42, 1, 10))
    lit(c, n, (255, 220, 255), (255, 250, 255), 10, 1.3)
    ztext(c, [(0.74, 0.16, 0.08), (0.86, 0.08, 0.05)])
    return K.finish(c)


def eerie_eye():
    c = bg((90, 40, 130), (8, 2, 18), cy=0.5)
    rays(c, 0.5, 0.5, 12, (200, 255, 160), alpha=60)
    eye = sh(lambda d: GC.eye_shape(d, 0.5, 0.5, 0.40, 0.22))
    lit(c, eye, (180, 255, 120), rad((255, 255, 170), (110, 200, 40), 0.5, 0.5, 0.34), 26, 1.4)
    pupil = sh(lambda d: GC.eye_shape(d, 0.5, 0.5, 0.21, 0.045, vertical=True))
    K.fill(c, K.soften(pupil), (10, 6, 18, 255))
    hi = circ(0.58, 0.42, 0.03)
    K.fill(c, K.soften(hi), (255, 255, 255, 230))
    return K.finish(c)


def qmark(d, cx, cy, s, w=0.07):
    brush(d, arc(cx, cy - 0.12 * s, 0.14 * s, 190, 400, 30) + [(cx, cy + 0.08 * s), (cx, cy + 0.14 * s)], w * s)
    r = w * 0.75 * s
    d.ellipse(pts([(cx - r, cy + 0.30 * s - r), (cx + r, cy + 0.30 * s + r)]), fill=255)


def level_holy():
    c = bg((240, 200, 130), (70, 30, 80), cy=0.45)
    rays(c, 0.5, 0.48, 16, (255, 255, 230), width=0.05, alpha=120)
    # the die Cait Sith rolls, and the question it asks
    GD.die(c, 0.5, 0.56, 0.30, (1, 4, 6), glowc=(255, 250, 220), gr=22, gs=1.3)
    q = sh(lambda d: qmark(d, 0.5, 0.36, 0.95))
    lit(c, q, (255, 230, 120), lin((255, 250, 220), (240, 170, 40)), 14, 1.6, sh=True)
    sparkles(c, [(0.20, 0.24, 0.07), (0.80, 0.22, 0.05)])
    return K.finish(c)


def soul_wings(c, cx, cy, s, glowc, paint):
    w = sh(lambda d: [wing(d, cx - 0.04 * s, cy, s * 0.8, -1, 5, 60, -50, 0.42, 0.05),
                      wing(d, cx + 0.04 * s, cy, s * 0.8, 1, 5, 60, -50, 0.42, 0.05)])
    lit(c, w, glowc, paint, 14, 1.3)
    orb = circ(cx, cy, 0.09 * s)
    lit(c, orb, (255, 255, 230), rad((255, 255, 255), (255, 230, 160), cx - 0.02, cy - 0.02, 0.1 * s), 18, 1.6)


def raise_ii():
    c = bg((190, 120, 200), (30, 10, 40), cy=0.6)
    pillar = poly([(0.36, 1.0), (0.64, 1.0), (0.58, 0.0), (0.42, 0.0)])
    K.fill(c, scale(pillar.filter(ImageFilter.GaussianBlur(14)), 0.6), (255, 250, 220, 255))
    motes(c, 6, 16, (0.34, 0.1, 0.66, 0.95), (0.006, 0.014), (255, 250, 220), (255, 230, 150))
    soul_wings(c, 0.5, 0.44, 1.0, (255, 230, 150), lin((255, 255, 250), (240, 210, 150)))
    ar = sh(lambda d: [up_arrow(d, 0.5, 0.80, 0.55)])
    lit(c, ar, (255, 220, 120), lin(*GOLD), 10, 1.3)
    return K.finish(c)


def reraise_ii():
    c = bg((130, 90, 190), (16, 8, 40), cy=0.5)
    loop = sh(lambda d: GA_arc_arrow(d, 0.5, 0.5, 0.35, 120, 420, 0.05))
    lit(c, loop, (255, 220, 140), lin(*GOLD), 14, 1.4, sh=True)
    soul_wings(c, 0.5, 0.52, 0.8, (255, 230, 170), lin((255, 255, 250), (240, 220, 170)))
    halo = ring(0.5, 0.33, 0.09, 0.02, 0.03)
    lit(c, halo, (255, 240, 160), (255, 245, 190), 8, 1.4)
    return K.finish(c)


def GA_arc_arrow(d, cx, cy, r, a0, a1, width):
    import group_a as GA
    GA.arc_arrow(d, cx, cy, r, a0, a1, width)


def altanas_favor():
    c = bg((255, 200, 150), (90, 40, 110), cy=0.62, r=0.7)
    rays(c, 0.5, 0.62, 24, (255, 250, 220), width=0.05, length=0.9, alpha=150, blur=6)
    sun = circ(0.5, 0.62, 0.16)
    K.glow(c, sun, (255, 250, 220, 255), 44, 1.8)
    K.fill(c, K.soften(sun, 4), rad((255, 255, 255), (255, 230, 170), 0.5, 0.6, 0.18))
    horizon = sh(lambda d: d.rectangle(pts([(0, 0.70), (1, 1)]), fill=255))
    K.fill(c, K.soften(horizon, 6), lin((150, 70, 120), (40, 14, 50)))
    hl = sh(lambda d: d.line(pts([(0.04, 0.70), (0.96, 0.70)]), fill=255, width=int(0.012 * W)))
    lit(c, hl, (255, 240, 200), (255, 250, 230), 10, 1.4)
    w = sh(lambda d: [wing(d, 0.44, 0.48, 1.0, -1, 7, 85, -75, 0.44, 0.05), wing(d, 0.56, 0.48, 1.0, 1, 7, 85, -75, 0.44, 0.05)])
    lit(c, w, (255, 240, 200), lin((255, 255, 255), (250, 220, 180)), 16, 1.4, sh=True)
    gold_crown(c, 0.5, 0.26, 0.36)
    sparkles(c, [(0.5, 0.62, 0.14)], glowc=(255, 240, 200))
    return K.finish(c)


# ---- Fenrir: midnight blue, the moon ---------------------------------------------------------------------------------
WOLF_LEAP = [(0.62, -0.06), (0.48, -0.12), (0.38, -0.18), (0.36, -0.24), (0.31, -0.40), (0.25, -0.22),
             (0.16, -0.17), (0.0, -0.15), (-0.20, -0.14), (-0.34, -0.11), (-0.42, -0.10), (-0.64, -0.22),
             (-0.68, -0.15), (-0.44, -0.01), (-0.44, 0.04), (-0.60, 0.20), (-0.66, 0.28), (-0.57, 0.29), (-0.36, 0.14),
             (-0.22, 0.11), (0.10, 0.10), (0.20, 0.10), (0.42, 0.24), (0.53, 0.26), (0.50, 0.19), (0.31, 0.04),
             (0.36, 0.0), (0.48, -0.02), (0.60, -0.03)]
WOLF_SIT = [(0.34, -0.58), (0.22, -0.50), (0.14, -0.42), (0.10, -0.44), (0.02, -0.60), (-0.04, -0.38), (-0.10, -0.30),
            (-0.18, -0.12), (-0.26, 0.10), (-0.34, 0.30), (-0.38, 0.46), (-0.50, 0.50), (-0.62, 0.58), (-0.46, 0.61),
            (-0.36, 0.60), (0.24, 0.60), (0.24, 0.55), (0.16, 0.53), (0.14, 0.20), (0.18, 0.0), (0.18, -0.14),
            (0.16, -0.26), (0.20, -0.36), (0.32, -0.48), (0.22, -0.46), (0.34, -0.54)]


def leaping_wolf(d, cx, cy, s):
    """A wolf in full leap, facing right: body, two pairs of stretched legs, a bushy tail, the head."""
    def q(seq):
        return [(cx + x * s, cy + y * s) for x, y in seq]
    d.polygon(pts(q([(0.34, -0.12), (0.10, -0.15), (-0.14, -0.13), (-0.32, -0.08), (-0.36, 0.02), (-0.24, 0.10),
                     (0.0, 0.10), (0.20, 0.12), (0.34, 0.04)])), fill=255)
    for path, w0, w1 in (([(0.22, 0.04), (0.38, 0.14), (0.56, 0.14)], 0.09, 0.04),
                         ([(0.16, 0.06), (0.30, 0.20), (0.48, 0.24)], 0.08, 0.035),
                         ([(-0.24, 0.02), (-0.40, 0.12), (-0.58, 0.14)], 0.10, 0.04),
                         ([(-0.20, 0.04), (-0.32, 0.18), (-0.50, 0.26)], 0.09, 0.035)):
        brush(d, q(path), w0 * s, w1 * s)
    d.polygon(pts(taper(q([(-0.30, -0.06), (-0.46, -0.12), (-0.66, -0.10)]), 0.10 * s, 0.03 * s)), fill=255)
    wolf_head(d, cx + 0.36 * s, cy - 0.10 * s, s * 0.44, 8)


def moonlit_charge():
    """Fenrir in full leap, a black silhouette across a huge moon."""
    c = bg((50, 60, 140), (4, 6, 24), cx=0.5, cy=0.42)
    moon(c, 0.50, 0.44, 0.38, gr=36, gs=1.5)
    streaks(c, [(0.0, y, 0.30, y - 0.10) for y in (0.50, 0.60, 0.80)], (200, 214, 255, 255), 0.018, 120, 3)
    def wolf(d):
        # the head and shoulders of the wolf lunging out of the moon, the body trailing away behind
        d.polygon(pts(taper([(0.04, 0.74), (0.22, 0.66), (0.42, 0.56)], 0.10, 0.22)), fill=255)
        brush(d, [(0.44, 0.62), (0.58, 0.72), (0.74, 0.74)], 0.08, 0.045)                       # foreleg reaching
        wolf_head(d, 0.50, 0.50, 0.66, -16, open_=True)
    w = sh(wolf)
    w = K.soften(w, 2).point(lambda v: 255 if v > 110 else int(v * 2.3))
    K.glow(c, w, (230, 236, 255, 255), 10, 2.2)
    K.fill(c, K.soften(w), lin((40, 44, 84), (8, 8, 24)))
    rimw = minus(w, ImageChops.offset(w, int(0.012 * W), int(0.016 * W)))
    K.fill(c, scale(K.soften(rimw, 1.5), 0.7), (200, 214, 255, 255))
    eye = circ(0.55, 0.40, 0.016)
    K.glow(c, eye, (255, 220, 120, 255), 5, 1.6)
    K.fill(c, K.soften(eye, 0.8), (255, 240, 160, 255))
    motes(c, 4, 9, (0.10, 0.10, 0.90, 0.90), (0.005, 0.010), (230, 236, 255), (180, 200, 255))
    return K.finish(c)


def crescent_fang():
    c = bg((60, 50, 150), (6, 4, 26), cy=0.5)
    cres = minus(circ(0.5, 0.5, 0.36), circ(0.64, 0.38, 0.32))
    K.glow(c, cres, (200, 200, 255, 255), 26, 1.4)
    K.fill(c, K.soften(cres), lin((255, 255, 250), (190, 190, 230), 120))
    fangs = sh(lambda d: [d.polygon(pts([(0.36, 0.30), (0.50, 0.40), (0.38, 0.42)]), fill=255),
                          d.polygon(pts([(0.36, 0.72), (0.52, 0.62), (0.40, 0.60)]), fill=255)])
    fangs = minus(fangs, cres)
    lit(c, fangs, (255, 255, 255), (250, 250, 255), 8, 1.2)
    slash = sh(lambda d: d.polygon(pts(swell(bow(0.62, 0.20, 0.86, 0.80, 0.08), 0.06)), fill=255))
    lit(c, slash, (180, 160, 255), (240, 236, 255), 10, 1.3)
    return K.finish(c)


def eclipse_bite():
    c = bg((70, 40, 120), (6, 2, 18), cy=0.5)
    corona = circ(0.5, 0.48, 0.27)
    K.glow(c, corona, (200, 190, 255, 255), 40, 2.0)
    K.fill(c, K.soften(ring(0.5, 0.48, 0.27, 0.02), 2), (255, 250, 255, 255))
    K.fill(c, K.soften(circ(0.5, 0.48, 0.255)), rad((40, 30, 60), (8, 4, 16), 0.45, 0.42, 0.26))
    teeth = sh(lambda d: [d.polygon(pts([(0.5 + i * 0.09 - 0.04, 0.22 if up else 0.74),
                                         (0.5 + i * 0.09 + 0.04, 0.22 if up else 0.74),
                                         (0.5 + i * 0.09, 0.40 if up else 0.56)]), fill=255)
                          for i in (-2, -1, 0, 1, 2) for up in (True, False)])
    teeth = inter(teeth, circ(0.5, 0.48, 0.30))
    lit(c, teeth, (255, 240, 240), lin((255, 255, 255), (210, 200, 220)), 10, 1.2, sh=True)
    return K.finish(c)


def howling_wolf(d, cx, cy, s):
    body = [(-0.04, -0.14), (0.10, -0.06), (0.14, 0.20), (0.18, 0.52), (0.10, 0.54), (0.04, 0.32), (-0.04, 0.46),
            (-0.20, 0.54), (-0.40, 0.56), (-0.40, 0.46), (-0.30, 0.26), (-0.18, 0.02)]
    d.polygon(xf(body, cx, cy, s), fill=255)
    d.polygon(pts(taper([(cx - 0.36 * s, cy + 0.50 * s), (cx - 0.52 * s, cy + 0.46 * s), (cx - 0.60 * s, cy + 0.36 * s)],
                        0.08 * s, 0.03 * s)), fill=255)
    wolf_head(d, cx + 0.06 * s, cy - 0.16 * s, s * 0.46, -55, open_=True)


def howling_moon():
    c = bg((60, 70, 170), (4, 4, 24), cx=0.5, cy=0.40)
    moon(c, 0.50, 0.42, 0.34, glowc=(210, 220, 255), gr=44, gs=1.6)
    motes(c, 6, 18, (0.05, 0.05, 0.95, 0.7), (0.003, 0.007), (230, 240, 255), None, 220)
    crag = poly([(0.20, 1.0), (0.36, 0.86), (0.52, 0.80), (0.74, 0.82), (0.92, 0.90), (1.0, 1.0)])
    w = sh(lambda d: d.polygon(xf(WOLF_SIT, 0.54, 0.48, 0.58), fill=255))
    both = add(crag, w)
    K.glow(c, both, (220, 230, 255, 255), 8, 2.0)
    K.fill(c, K.soften(both), lin((30, 30, 60), (6, 6, 16)))
    sound_waves(c, 0.74, 0.14, (0.08, 0.14), 250, 340, 0.02, (220, 230, 255), (160, 180, 255), 0.9)
    return K.finish(c)


def lunar_bay():
    c = bg((50, 80, 170), (4, 8, 28), cy=0.3)
    beam = poly([(0.40, 0.0), (0.60, 0.0), (0.66, 0.70), (0.34, 0.70)])
    K.glow(c, beam, (190, 210, 255, 255), 24, 1.2)
    K.fill(c, K.soften(beam, 6), lin((255, 255, 255, 120), (220, 230, 255, 255), 90))
    for r, a in ((0.36, 0.5), (0.26, 0.7), (0.16, 1.0)):
        rp = ring(0.5, 0.74, r, 0.018, r * 0.28)
        lit(c, rp, (180, 200, 255), (230, 240, 255), 8, a)
    cres = minus(circ(0.5, 0.20, 0.12), circ(0.56, 0.15, 0.11))
    lit(c, cres, (230, 236, 255), (255, 255, 250), 14, 1.6)
    motes(c, 2, 14, (0.3, 0.3, 0.7, 0.9), (0.005, 0.012), (230, 240, 255), (170, 190, 255))
    return K.finish(c)


def impact():
    c = bg((70, 40, 120), (4, 2, 14), cy=0.5)
    rnd = random.Random(8)
    shards = sh(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * r0, 0.5 + math.sin(a) * r0),
                                          (0.5 + math.cos(a + 0.12) * r1, 0.5 + math.sin(a + 0.12) * r1),
                                          (0.5 + math.cos(a - 0.10) * r1 * 0.9, 0.5 + math.sin(a - 0.10) * r1 * 0.9)]),
                                     fill=255)
                           for a, r0, r1 in [(math.pi * 2 * i / 11 + rnd.uniform(-0.2, 0.2), 0.20, rnd.uniform(0.36, 0.46))
                                             for i in range(11)]])
    lit(c, shards, (190, 120, 255), lin((230, 200, 255), (120, 60, 200)), 14, 1.3, sh=True)
    orb = circ(0.5, 0.5, 0.20)
    K.glow(c, orb, (170, 90, 255, 255), 30, 1.8)
    K.fill(c, K.soften(orb), rad((20, 0, 30), (90, 40, 170), 0.5, 0.5, 0.22))
    rim = ring(0.5, 0.5, 0.20, 0.018)
    lit(c, rim, (220, 180, 255), (240, 220, 255), 8, 1.4)
    cres = minus(circ(0.5, 0.5, 0.11), circ(0.55, 0.46, 0.10))
    K.fill(c, K.soften(cres), (210, 210, 255, 220))
    return K.finish(c)


def lunar_cry():
    c = bg((70, 60, 160), (6, 4, 26), cy=0.5)
    cres = minus(circ(0.40, 0.5, 0.25), circ(0.50, 0.42, 0.23))
    lit(c, cres, (210, 210, 255), lin((255, 255, 250), (190, 190, 230), 120), 20, 1.4)
    sound_waves(c, 0.40, 0.5, (0.24, 0.34, 0.44), -50, 50, 0.04, (230, 230, 255), (170, 160, 255))
    ar = sh(lambda d: [down_arrow(d, 0.76, 0.26, 0.42), down_arrow(d, 0.76, 0.74, 0.42)])
    lit(c, ar, (255, 90, 90), lin((255, 170, 160), (210, 40, 50)), 8, 1.3, sh=True)
    return K.finish(c)


def lunar_roar():
    c = bg((60, 80, 170), (4, 6, 28), cx=0.35, cy=0.5)
    sound_waves(c, 0.50, 0.52, (0.18, 0.28, 0.38), -40, 40, 0.05, (230, 236, 255), (150, 170, 255))
    head = sh(lambda d: wolf_head(d, 0.32, 0.50, 0.62, -6, open_=True))
    lit(c, head, (200, 210, 255), lin((220, 224, 245), (110, 116, 160)), 14, 1.3, sh=True)
    eye = poly([(0.335, 0.42), (0.37, 0.415), (0.355, 0.43)])
    K.fill(c, K.soften(eye, 0.8), (255, 220, 100, 255))
    # buffs blown away
    for x, y in ((0.86, 0.26), (0.90, 0.72)):
        m = sh(lambda d, x=x, y=y: up_arrow(d, x, y, 0.3))
        K.fill(c, scale(K.soften(m, 3), 0.55), (200, 255, 200, 255))
    return K.finish(c)


def phases(c, cx, cy, R, r, glowc=(210, 220, 255)):
    """A ring of the moon's eight phases, new moon at the top."""
    for i in range(8):
        a = math.pi * 2 * i / 8 - math.pi / 2
        x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
        full = circ(x, y, r)
        K.fill(c, K.soften(full), (40, 44, 90, 255))
        if i == 0:
            continue
        k = i if i <= 4 else 8 - i
        dx = 2.1 * r * k / 4 * (-1 if i <= 4 else 1)
        lightm = full if i == 4 else minus(full, circ(x + dx, y, r))
        K.glow(c, lightm, col(glowc), 6, 1.0)
        K.fill(c, K.soften(lightm), (250, 250, 240, 255))


def ecliptic_growl():
    c = bg((70, 60, 150), (6, 4, 24), cy=0.5)
    phases(c, 0.5, 0.5, 0.33, 0.065)
    ar = sh(lambda d: up_arrow(d, 0.5, 0.52, 1.0))
    lit(c, ar, (255, 210, 120), lin((255, 240, 170), (230, 140, 40)), 16, 1.4, sh=True)
    return K.finish(c)


def ecliptic_howl():
    c = bg((40, 70, 150), (2, 6, 22), cy=0.5)
    m = circ(0.5, 0.48, 0.26)
    K.glow(c, m, (200, 220, 255, 255), 36, 1.6)
    K.fill(c, K.soften(m), rad((255, 255, 250), (200, 205, 230), 0.4, 0.4, 0.3))
    shadowm = circ(0.62, 0.42, 0.24)
    K.fill(c, K.soften(inter(shadowm, m), 3), (20, 24, 56, 255))
    eyes = sh(lambda d: [d.polygon(pts([(x - 0.07, 0.40), (x + 0.07, 0.38), (x + 0.03, 0.44)]), fill=255)
                         for x in (0.56, 0.74)])
    eyes = inter(eyes, shadowm)
    lit(c, eyes, (120, 220, 255), (220, 250, 255), 10, 1.8)
    sparkles(c, [(0.22, 0.76, 0.08), (0.80, 0.78, 0.06)], glowc=(200, 220, 255))
    return K.finish(c)


def heavenward_howl():
    c = bg((60, 90, 180), (4, 6, 28), cy=0.2)
    beam = poly([(0.66, -0.1), (0.90, -0.1), (0.80, 0.16), (0.68, 0.16)])
    K.fill(c, scale(beam.filter(ImageFilter.GaussianBlur(16)), 0.9), (230, 240, 255, 255))
    w = sh(lambda d: d.polygon(xf(WOLF_SIT, 0.42, 0.66, 0.92), fill=255))
    lit(c, w, (170, 200, 255), lin((236, 240, 255), (120, 130, 180)), 16, 1.4, sh=True)
    eye = circ(0.535, 0.245, 0.016)
    K.fill(c, K.soften(eye, 0.8), (60, 70, 140, 255))
    motes(c, 9, 14, (0.60, 0.0, 0.92, 0.20), (0.006, 0.014), (240, 250, 255), (180, 200, 255))
    cres = minus(circ(0.24, 0.20, 0.09), circ(0.29, 0.17, 0.085))
    lit(c, cres, (230, 236, 255), (255, 255, 250), 12, 1.5)
    return K.finish(c)


# ---- Ifrit: fire red -------------------------------------------------------------------------------------------------
def fire_bg():
    return bg((200, 60, 30), (30, 4, 2), cy=0.55)


def flame_field(c, seed, base=0.98, n=9, hmin=0.18, hmax=0.36, x0=0.08, x1=0.92, alpha=1.0):
    rnd = random.Random(seed)
    m = sh(lambda d: [GD_flame(d, x0 + (x1 - x0) * i / (n - 1), base, 0.09, rnd.uniform(hmin, hmax),
                               rnd.uniform(-0.05, 0.05)) for i in range(n)])
    K.glow(c, m, (255, 120, 30, 255), 18, 1.2 * alpha)
    K.fill(c, scale(K.soften(m, 2), alpha), lin((255, 220, 110), (230, 70, 20), 270))
    return m


def punch():
    c = fire_bg()
    fl = sh(lambda d: [GD_flame(d, x, 0.72, w, h, l) for x, w, h, l in ((0.5, 0.26, 0.62, 0.0), (0.26, 0.10, 0.36, -0.08),
                                                                         (0.74, 0.10, 0.38, 0.08))])
    fire_paint(c, fl)
    streaks(c, [(0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30, 0.5 + math.cos(a) * 0.46, 0.5 + math.sin(a) * 0.46)
                for a in [math.pi * 2 * k / 12 for k in range(12)]], (255, 220, 160, 255), 0.014, 150, 3)
    fist(c, 0.5, 0.56, 0.95, (255, 160, 60), skin=((255, 190, 110), (150, 30, 14)), line=(60, 8, 2), knuckle=(255, 230, 160))
    return K.finish(c)


def burning_strike():
    c = bg((180, 50, 30), (26, 4, 4), cx=0.65, cy=0.65)
    trail = poly([(0.0, 0.10), (0.18, -0.02), (0.72, 0.52), (0.52, 0.72)])
    K.glow(c, trail, (255, 120, 30, 255), 28, 1.3)
    K.fill(c, K.soften(trail, 10), lin((255, 90, 20, 0), (255, 220, 120, 255), 45))
    fl = sh(lambda d: [GD_flame(d, x, y, 0.06, 0.18, -0.04) for x, y in ((0.30, 0.34), (0.42, 0.44), (0.20, 0.22))])
    K.fill(c, scale(K.soften(fl, 2), 0.8), (255, 210, 120, 255))
    fist(c, 0.64, 0.64, 0.80, (255, 170, 60), skin=((255, 190, 110), (150, 30, 14)), line=(60, 8, 2), knuckle=(255, 230, 160), ang=40)
    burst = poly(burst_pts(0.80, 0.80, 8, 0.16, 0.07))
    lit(c, burst, (255, 220, 120), (255, 250, 220), 14, 1.4)
    return K.finish(c)


def double_punch():
    c = bg((210, 90, 40), (34, 8, 4), cy=0.5)
    rays(c, 0.5, 0.5, 16, (255, 220, 160), alpha=70)
    fist(c, 0.36, 0.40, 0.72, (255, 150, 60), skin=((255, 190, 110), (150, 30, 14)), line=(60, 8, 2), knuckle=(255, 230, 160), ang=-15)
    fist(c, 0.62, 0.62, 0.82, (255, 170, 70), skin=((255, 190, 110), (150, 30, 14)), line=(60, 8, 2), knuckle=(255, 230, 160), ang=10)
    st = sh(lambda d: [d.polygon(pts(burst_pts(0.80, 0.24, 6, 0.10, 0.04)), fill=255),
                       d.polygon(pts(burst_pts(0.18, 0.78, 6, 0.08, 0.03)), fill=255)])
    lit(c, st, (255, 230, 120), (255, 250, 220), 10, 1.3)
    return K.finish(c)


def flaming_crush():
    c = bg((170, 50, 20), (24, 4, 2), cy=0.75)
    ground = poly([(0, 0.78), (1, 0.78), (1, 1), (0, 1)])
    K.fill(c, K.soften(ground, 3), lin((90, 30, 16), (30, 8, 4)))
    erupt = sh(lambda d: [GD_flame(d, x, 0.84, w, h, l) for x, w, h, l in
                          ((0.22, 0.13, 0.46, -0.14), (0.78, 0.13, 0.46, 0.14), (0.38, 0.10, 0.34, -0.06),
                           (0.62, 0.10, 0.34, 0.06), (0.08, 0.07, 0.24, -0.08), (0.92, 0.07, 0.24, 0.08))])
    mid = sh(lambda d: [GD_flame(d, x, 0.84, 0.07, 0.30, l) for x, l in ((0.22, -0.1), (0.78, 0.1))])
    fire_paint(c, erupt, mid)
    cracks = sh(lambda d: [brush(d, zigzag(0.5, 0.80, x, 0.98, 3, 0.03, k), 0.02, 0.008) for k, x in
                           enumerate((0.20, 0.42, 0.62, 0.84))])
    lit(c, cracks, (255, 160, 40), (255, 230, 140), 8, 1.4)
    fist(c, 0.5, 0.42, 0.80, (255, 160, 60), skin=((255, 190, 110), (150, 30, 14)), line=(60, 8, 2), knuckle=(255, 230, 160), ang=180)
    flash = circ(0.5, 0.80, 0.22, 0.07)
    lit(c, flash, (255, 230, 150), (255, 250, 220), 20, 1.4)
    streaks(c, [(0.30, 0.02, 0.30, 0.24), (0.70, 0.02, 0.70, 0.24), (0.5, -0.05, 0.5, 0.14)], (255, 230, 180, 255),
            0.02, 160, 3)
    return K.finish(c)


def meteor(c, cx, cy, r, ang, length, glowc=(255, 120, 30), seed=2):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    tail = poly([(cx + nx * r, cy + ny * r), (cx - nx * r, cy - ny * r), (cx - ux * length, cy - uy * length)])
    K.glow(c, tail, col(glowc), 26, 1.3)
    K.fill(c, K.soften(tail, 8), lin((255, 240, 160), (255, 90, 20), ang + 180))
    rk = sh(lambda d: rock(d, cx, cy, r, seed, 10))
    K.glow(c, rk, (255, 200, 80, 255), 18, 1.6)
    K.fill(c, K.soften(rk), rad((255, 240, 180), (170, 60, 20), cx + ux * r * 0.3, cy + uy * r * 0.3, r * 1.3))
    cr = sh(lambda d: [d.ellipse(pts([(cx + x * r - 0.2 * r, cy + y * r - 0.15 * r), (cx + x * r + 0.2 * r,
                                                                                     cy + y * r + 0.15 * r)]), fill=255)
                       for x, y in ((-0.3, -0.2), (0.2, 0.3), (-0.1, 0.45))])
    K.fill(c, scale(K.soften(cr, 2), 0.5), (90, 20, 10, 255))


def meteor_strike():
    c = bg((150, 40, 60), (20, 2, 10), cx=0.7, cy=0.75)
    motes(c, 4, 14, (0.05, 0.05, 0.95, 0.5), (0.003, 0.007), (255, 230, 210), None, 200)
    impact_ = circ(0.80, 0.90, 0.20, 0.08)
    K.glow(c, impact_, (255, 160, 60, 255), 30, 1.4)
    meteor(c, 0.58, 0.60, 0.22, 45, 0.80)
    return K.finish(c)


def horns(d, cx, cy, s, w=0.10):
    for sx in (-1, 1):
        cur = [(cx + sx * x * s, cy + y * s) for x, y in [(0.10, 0.10), (0.22, 0.04), (0.30, -0.08), (0.34, -0.20),
                                                          (0.31, -0.30), (0.24, -0.36)]]
        d.polygon(pts(taper(cur, w * s, 0.01)), fill=255)


def inferno():
    c = bg((255, 120, 30), (60, 4, 2), cy=0.62, r=0.66)
    # the hellfire column rising, the sky burning, Ifrit's horns crowning it
    sw = sh(lambda d: [d.polygon(pts(taper([(0.5 + math.cos(math.radians(a0 + t * 4)) * (0.06 + t * 0.0028),
                                             0.86 - t * 0.0062) for t in range(0, 101, 4)], 0.03, 0.10)), fill=255)
                       for a0 in (0, 120, 240)])
    flame_field(c, 9, 1.02, 11, 0.24, 0.50, 0.0, 1.0)
    big = sh(lambda d: [GD_flame(d, 0.5, 0.96, 0.30, 0.86, 0.0), GD_flame(d, 0.26, 0.96, 0.14, 0.52, -0.08),
                        GD_flame(d, 0.74, 0.96, 0.14, 0.52, 0.08)])
    mid = sh(lambda d: GD_flame(d, 0.5, 0.96, 0.19, 0.62, 0.0))
    core = sh(lambda d: GD_flame(d, 0.5, 0.96, 0.10, 0.40, 0.0))
    fire_paint(c, big, mid)
    K.fill(c, scale(K.soften(core, 6), 0.6), (255, 250, 210, 255))
    h = sh(lambda d: horns(d, 0.5, 0.30, 1.1, 0.11))
    lit(c, h, (255, 230, 150), lin((255, 250, 220), (190, 120, 70)), 14, 1.4, sh=True)
    eyes = sh(lambda d: [d.polygon(pts([(0.40, 0.40), (0.47, 0.44), (0.41, 0.45)]), fill=255),
                         d.polygon(pts([(0.60, 0.40), (0.53, 0.44), (0.59, 0.45)]), fill=255)])
    lit(c, eyes, (255, 255, 160), (255, 255, 230), 8, 1.8)
    motes(c, 6, 16, (0.1, 0.05, 0.9, 0.45), (0.005, 0.012), (255, 240, 180), (255, 160, 60))
    return K.finish(c)


def conflag_strike():
    c = bg((230, 90, 30), (40, 4, 4), cy=0.5)
    shock = ring(0.5, 0.52, 0.40, 0.03, 0.40)
    lit(c, shock, (255, 200, 120), (255, 236, 200), 12, 1.0)
    b = poly(burst_pts(0.5, 0.52, 12, 0.42, 0.20, seed=3))
    K.glow(c, b, (255, 120, 30, 255), 26, 1.4)
    K.fill(c, K.soften(b, 2), rad((255, 255, 220), (240, 80, 20), 0.5, 0.52, 0.42))
    b2 = poly(burst_pts(0.5, 0.52, 9, 0.24, 0.12, rot0=-70, seed=5))
    K.fill(c, K.soften(b2, 2), (255, 255, 236, 255))
    slash = sh(lambda d: d.polygon(pts(swell(bow(0.10, 0.84, 0.90, 0.16, -0.06), 0.09)), fill=255))
    lit(c, slash, (255, 240, 180), (255, 255, 245), 10, 1.4)
    motes(c, 13, 16, (0.05, 0.05, 0.95, 0.95), (0.006, 0.014), (255, 220, 140), (255, 120, 40))
    return K.finish(c)


def ifrit_face(d, cx, cy, s):
    d.polygon(pts([(cx + x * s, cy + y * s) for x, y in [(-0.17, -0.14), (0.17, -0.14), (0.20, 0.06), (0.10, 0.26),
                                                         (0, 0.32), (-0.10, 0.26), (-0.20, 0.06)]]), fill=255)


def crimson_howl():
    c = bg((210, 30, 40), (30, 2, 6), cy=0.5)
    rays(c, 0.5, 0.52, 14, (255, 160, 120), alpha=80)
    sound_waves(c, 0.5, 0.56, (0.30, 0.40), 10, 170, 0.04, (255, 200, 170), (255, 80, 60))
    h = sh(lambda d: horns(d, 0.5, 0.40, 0.95, 0.10))
    face = sh(lambda d: ifrit_face(d, 0.5, 0.48, 1.0))
    both = add(h, face)
    K.shadow(c, both, 5, 8, 8, 160)
    K.glow(c, both, (255, 120, 60, 255), 18, 1.3)
    K.fill(c, K.soften(h), lin((255, 236, 200), (170, 110, 70)))
    K.fill(c, K.soften(face), lin((160, 40, 20), (60, 10, 6)))
    mouth = poly([(0.40, 0.60), (0.60, 0.60), (0.56, 0.72), (0.5, 0.75), (0.44, 0.72)])
    lit(c, mouth, (255, 120, 40), rad((255, 200, 80), (120, 10, 4), 0.5, 0.68, 0.1), 6, 1.2)
    fangs = sh(lambda d: [d.polygon(pts([(x - 0.025, 0.60), (x + 0.025, 0.60), (x, 0.67)]), fill=255) for x in (0.44, 0.56)])
    K.fill(c, K.soften(fangs, 0.8), (255, 250, 236, 255))
    eyes = sh(lambda d: [d.polygon(pts([(0.38, 0.45), (0.47, 0.50), (0.40, 0.51)]), fill=255),
                         d.polygon(pts([(0.62, 0.45), (0.53, 0.50), (0.60, 0.51)]), fill=255)])
    lit(c, eyes, (255, 230, 80), (255, 250, 200), 8, 1.6)
    return K.finish(c)


def inferno_howl():
    c = bg((190, 60, 20), (28, 6, 2), cy=0.5)
    blade = sh(lambda d: GD.sword(d, 0.5, 0.10, 0.92, 0.055))
    fl = sh(lambda d: [GD_flame(d, 0.5 + dx, 0.74, 0.10, 0.62, l) for dx, l in ((-0.08, -0.06), (0.08, 0.06),
                                                                                 (0.0, 0.0))])
    K.glow(c, fl, (255, 120, 30, 255), 22, 1.3)
    K.fill(c, K.soften(fl, 2), lin((255, 220, 100), (230, 70, 20), 270))
    lit(c, blade, (255, 240, 180), lin((255, 255, 245), (255, 190, 120), 0), 12, 1.4, sh=True)
    h = sh(lambda d: horns(d, 0.5, 0.80, 0.70, 0.10))
    lit(c, h, (255, 200, 120), lin((255, 236, 200), (170, 110, 70)), 10, 1.2)
    return K.finish(c)


# ---- Titan: earth, amber ---------------------------------------------------------------------------------------------
def earth_bg(cx=0.5, cy=0.5):
    return bg((214, 150, 60), (40, 20, 4), cx=cx, cy=cy)


def rock_throw():
    c = earth_bg(0.4, 0.6)
    streaks(c, [(0.04, 0.80, 0.40, 0.50), (0.10, 0.92, 0.44, 0.62), (0.0, 0.66, 0.30, 0.44)], (255, 230, 180, 255),
            0.024, 150, 5)
    r = sh(lambda d: rock(d, 0.58, 0.42, 0.25, 4, 9))
    stone_paint(c, r)
    pebbles = sh(lambda d: [rock(d, x, y, rr, k, 6) for k, (x, y, rr) in enumerate(((0.30, 0.70, 0.05),
                                                                                   (0.22, 0.56, 0.035)))])
    stone_paint(c, pebbles, gr=6)
    return K.finish(c)


def rock_buster():
    c = earth_bg()
    rays(c, 0.5, 0.56, 14, (255, 220, 160), alpha=80)
    rnd = random.Random(6)
    frags = sh(lambda d: [rock(d, 0.5 + math.cos(a) * 0.33, 0.56 + math.sin(a) * 0.30, rnd.uniform(0.05, 0.08), k, 6)
                          for k, a in enumerate([math.pi * 2 * i / 7 + 0.3 for i in range(7)])])
    stone_paint(c, frags, gr=8)
    fist(c, 0.5, 0.54, 0.95, (255, 200, 120), skin=((236, 210, 170), (120, 86, 52)), line=(56, 34, 16),
         knuckle=(255, 244, 220))
    return K.finish(c)


def megalith_throw():
    c = earth_bg(0.4, 0.6)
    streaks(c, [(0.0, 0.92, 0.30, 0.66), (0.08, 1.0, 0.40, 0.74), (-0.04, 0.78, 0.22, 0.56)], (255, 230, 180, 255),
            0.03, 150, 5)
    slab = rot(poly([(0.38, 0.12), (0.64, 0.10), (0.68, 0.86), (0.36, 0.88)]), -30, 0.52, 0.48)
    stone_paint(c, slab, top=(200, 186, 160), bot=(90, 76, 60))
    runes = rot(sh(lambda d: [brush(d, [(0.52, 0.22), (0.52, 0.78)], 0.022),
                              brush(d, [(0.52, 0.32), (0.44, 0.40)], 0.02), brush(d, [(0.52, 0.50), (0.60, 0.58)], 0.02),
                              brush(d, [(0.52, 0.66), (0.44, 0.72)], 0.02)]), -30, 0.52, 0.48)
    lit(c, runes, (255, 200, 90), (255, 230, 150), 8, 1.6)
    return K.finish(c)


def mountain_buster():
    c = bg((255, 196, 110), (120, 50, 20), cy=0.3, r=0.8)
    mtn = poly([(0.0, 0.92), (0.24, 0.56), (0.36, 0.62), (0.52, 0.34), (0.70, 0.60), (0.82, 0.52), (1.0, 0.82),
                (1.0, 1.0), (0.0, 1.0)])
    stone_paint(c, mtn, top=(170, 120, 80), bot=(50, 30, 18))
    cap = inter(mtn, poly([(0.40, 0.48), (0.52, 0.34), (0.64, 0.50), (0.56, 0.46), (0.50, 0.52), (0.46, 0.46)]))
    K.fill(c, K.soften(cap), (250, 240, 226, 255))
    cr = sh(lambda d: brush(d, zigzag(0.52, 0.36, 0.48, 0.96, 6, 0.04, 2), 0.035, 0.01))
    lit(c, cr, (255, 200, 80), (255, 240, 180), 12, 1.6)
    fist(c, 0.52, 0.18, 0.56, (255, 220, 150), skin=((236, 210, 170), (120, 86, 52)), line=(56, 34, 16), ang=180)
    burst = poly(burst_pts(0.52, 0.33, 8, 0.12, 0.05))
    lit(c, burst, (255, 230, 150), (255, 250, 230), 10, 1.3)
    return K.finish(c)


def spikes(d, base, spec):
    for x, w, h, lean in spec:
        d.polygon(pts([(x - w, base), (x + lean, base - h), (x + w, base)]), fill=255)


def geocrush():
    c = bg((150, 110, 50), (24, 14, 4), cy=0.4)
    ground = poly([(0, 0.76), (1, 0.70), (1, 1), (0, 1)])
    K.fill(c, K.soften(ground, 3), lin((110, 76, 40), (36, 22, 10)))
    sp = sh(lambda d: spikes(d, 0.86, [(0.5, 0.11, 0.70, 0.0), (0.28, 0.09, 0.48, -0.08), (0.72, 0.09, 0.50, 0.08),
                                       (0.12, 0.06, 0.28, -0.08), (0.88, 0.06, 0.30, 0.08)]))
    stone_paint(c, sp, top=(236, 200, 140), bot=(110, 72, 36), gr=18, gs=1.3)
    facet = inter(sp, poly([(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)]))
    K.fill(c, scale(K.soften(facet), 0.25), (40, 20, 6, 255))
    motes(c, 7, 14, (0.1, 0.1, 0.9, 0.6), (0.006, 0.014), (220, 180, 120), (255, 200, 100))
    return K.finish(c)


def earthen_fury():
    c = bg((255, 236, 150), (200, 80, 10), cy=0.46, r=0.6)
    rays(c, 0.5, 0.66, 20, (255, 255, 230), width=0.05, length=0.9, alpha=170)
    # rock spires bursting outward from a glowing rift, boulders thrown into a blazing sky
    pil = sh(lambda d: [d.polygon(pts([(x0 - w, 0.86), (x1 - w * 0.3, top + 0.03), (x1, top), (x1 + w * 0.3, top + 0.04),
                                       (x0 + w, 0.86)]), fill=255)
                        for x0, x1, w, top in ((0.30, 0.14, 0.05, 0.40), (0.70, 0.86, 0.05, 0.38),
                                               (0.42, 0.34, 0.045, 0.22), (0.58, 0.68, 0.045, 0.26))])
    K.glow(c, pil, (90, 30, 0, 255), 10, 1.2)
    stone_paint(c, pil, glowc=(255, 230, 160), top=(120, 80, 50), bot=(30, 16, 6), gr=6, gs=1.0)
    ground = poly([(0, 0.76), (0.3, 0.80), (0.7, 0.78), (1, 0.74), (1, 1), (0, 1)])
    K.fill(c, K.soften(ground, 3), lin((90, 50, 20), (30, 14, 4)))
    rift = poly([(0.18, 0.80), (0.40, 0.76), (0.5, 0.70), (0.60, 0.76), (0.82, 0.80), (0.60, 0.84), (0.5, 0.92),
                 (0.40, 0.84)])
    K.glow(c, rift, (255, 170, 40, 255), 26, 1.8)
    K.fill(c, K.soften(rift, 2), rad((255, 255, 230), (255, 170, 50), 0.5, 0.80, 0.3))
    fis = sh(lambda d: [brush(d, zigzag(0.5, 0.82, x, 1.0, 3, 0.03, k), 0.03, 0.01) for k, x in
                        enumerate((0.12, 0.34, 0.66, 0.88))])
    lit(c, fis, (255, 180, 60), (255, 240, 180), 8, 1.6)
    br = sh(lambda d: [rock(d, x, y, r, k, 7) for k, (x, y, r) in enumerate(((0.28, 0.16, 0.05), (0.74, 0.12, 0.06),
                                                                             (0.52, 0.08, 0.04)))])
    stone_paint(c, br, glowc=(255, 200, 100), top=(150, 100, 60), bot=(36, 20, 8), gr=8)
    motes(c, 1, 18, (0.15, 0.3, 0.85, 0.75), (0.005, 0.012), (255, 240, 180), (255, 160, 60))
    return K.finish(c)


def crag_throw():
    c = earth_bg(0.35, 0.6)
    rnd = random.Random(9)
    spec = [(0.30 + 0.62 * t, 0.70 - 0.50 * t + rnd.uniform(-0.12, 0.12), 0.07 + 0.03 * rnd.random()) for t in
            (0.15, 0.4, 0.6, 0.85, 0.3, 0.7)]
    streaks(c, [(x - 0.22, y + 0.16, x - 0.06, y + 0.04) for x, y, _ in spec], (255, 220, 170, 255), 0.02, 130, 4)
    sh_ = sh(lambda d: [d.polygon(pts(burst_pts(x, y, 3, r * 1.4, r * 0.6, rot0=rnd.uniform(0, 360))), fill=255)
                        for x, y, r in spec])
    stone_paint(c, sh_, top=(230, 196, 150), bot=(110, 70, 40), gr=10)
    big = sh(lambda d: d.polygon(pts(burst_pts(0.34, 0.66, 4, 0.20, 0.09, rot0=-30)), fill=255))
    stone_paint(c, big, top=(236, 206, 160), bot=(100, 64, 36))
    return K.finish(c)


def earthen_ward():
    c = bg((160, 130, 70), (24, 18, 6), cy=0.45)
    rays(c, 0.5, 0.5, 12, (255, 230, 170), alpha=60)
    s_ = shield_shape(0.5, 0.18, 0.28, 0.66)
    stone_paint(c, s_, top=(210, 180, 130), bot=(100, 70, 40), gr=20, gs=1.4)
    rnd = random.Random(2)
    plates = sh(lambda d: [rock(d, x, y, 0.07, k, 6) for k, (x, y) in enumerate(((0.40, 0.32), (0.60, 0.32),
                                                                                 (0.50, 0.48), (0.38, 0.56),
                                                                                 (0.62, 0.56), (0.50, 0.70)))])
    plates = inter(plates, s_)
    K.fill(c, scale(K.soften(plates, 2), 0.5), (255, 230, 180, 255))
    rim = minus(s_, shield_shape(0.5, 0.22, 0.24, 0.60))
    lit(c, rim, (255, 200, 100), lin(*GOLD), 8, 1.2)
    return K.finish(c)


def earthen_armor():
    c = bg((130, 100, 60), (20, 14, 6), cy=0.45)
    plate = poly([(0.30, 0.20), (0.42, 0.24), (0.5, 0.30), (0.58, 0.24), (0.70, 0.20), (0.86, 0.30), (0.80, 0.48),
                  (0.70, 0.46), (0.68, 0.76), (0.5, 0.86), (0.32, 0.76), (0.30, 0.46), (0.20, 0.48), (0.14, 0.30)])
    stone_paint(c, plate, glowc=(255, 190, 100), top=(200, 170, 120), bot=(80, 56, 32), gr=20, gs=1.4)
    seams = sh(lambda d: [brush(d, [(0.5, 0.32), (0.5, 0.84)], 0.014), brush(d, [(0.33, 0.56), (0.67, 0.56)], 0.014),
                          brush(d, [(0.32, 0.70), (0.5, 0.78), (0.68, 0.70)], 0.014)])
    K.fill(c, scale(K.soften(seams), 0.6), (50, 30, 14, 255))
    gem = poly([(0.5, 0.40), (0.56, 0.47), (0.5, 0.54), (0.44, 0.47)])
    lit(c, gem, (255, 200, 80), lin((255, 240, 170), (210, 130, 30)), 12, 1.6)
    return K.finish(c)


# ---- Leviathan: sea blue ---------------------------------------------------------------------------------------------
def water_bg(cx=0.5, cy=0.45):
    return bg((40, 120, 200), (2, 10, 36), cx=cx, cy=cy)


def water_paint(c, m, glowc=(120, 200, 255), gr=16, gs=1.3, shadow=True):
    lit(c, m, glowc, lin((236, 250, 255), (60, 140, 230), 80), gr, gs, sh=shadow)


SERPENT = [(0.50, 0.02), (0.30, -0.06), (0.12, -0.12), (-0.02, -0.14), (-0.16, -0.10), (-0.26, 0.0), (-0.32, 0.20),
           (-0.34, 0.50), (-0.12, 0.50), (-0.12, 0.24), (-0.04, 0.12), (0.14, 0.10), (0.48, 0.06)]
SERPENT_OPEN = [(0.50, 0.0), (0.30, -0.07), (0.12, -0.12), (-0.02, -0.14), (-0.16, -0.10), (-0.26, 0.0),
                (-0.32, 0.20), (-0.34, 0.50), (-0.12, 0.50), (-0.12, 0.26), (-0.04, 0.16), (0.12, 0.22), (0.40, 0.26),
                (0.38, 0.20), (0.14, 0.08), (0.48, 0.04)]
SERPENT_FINS = [[(0.0, -0.13), (-0.10, -0.40), (-0.10, -0.12)], [(-0.10, -0.11), (-0.28, -0.32), (-0.20, -0.05)],
                [(-0.22, -0.03), (-0.44, -0.16), (-0.30, 0.10)], [(-0.04, 0.08), (-0.26, 0.20), (-0.12, 0.16)]]


def serpent_head(c, cx, cy, s, ang=0, open_=False, glowc=(140, 220, 255)):
    fins = sh(lambda d: [d.polygon(xf(f, cx, cy, s, ang), fill=255) for f in SERPENT_FINS])
    lit(c, fins, glowc, lin((200, 250, 255), (60, 160, 220)), 10, 1.2, sh=True)
    m = sh(lambda d: d.polygon(xf(SERPENT_OPEN if open_ else SERPENT, cx, cy, s, ang), fill=255))
    lit(c, m, glowc, lin((110, 190, 250), (16, 50, 130)), 14, 1.3, sh=True)
    belly = sh(lambda d: d.polygon(xf([(-0.12, 0.50), (-0.12, 0.26), (-0.04, 0.14), (0.10, 0.12), (-0.02, 0.22),
                                       (-0.20, 0.50)], cx, cy, s, ang), fill=255))
    K.fill(c, scale(K.soften(belly, 2), 0.6), (200, 240, 255, 255))
    ex, ey = at(0.14, -0.06, cx, cy, s, ang)
    eye = circ(ex, ey, 0.022 * s / 0.6)
    lit(c, eye, (255, 240, 120), (255, 250, 200), 6, 1.8)
    return m


def barracuda_dive():
    c = water_bg(cy=0.3)
    bub = sh(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), outline=255, width=int(0.01 * W))
                        for x, y, r in ((0.24, 0.30, 0.03), (0.30, 0.18, 0.02), (0.20, 0.12, 0.015),
                                        (0.76, 0.66, 0.025))])
    lit(c, bub, (200, 240, 255), (230, 250, 255), 6, 1.0)
    streaks(c, [(0.20, 0.0, 0.44, 0.40), (0.32, -0.04, 0.56, 0.34), (0.10, 0.08, 0.34, 0.46)], (200, 240, 255, 255),
            0.016, 140, 3)
    fish = [(0.50, 0.0), (0.30, -0.08), (0.0, -0.10), (-0.26, -0.06), (-0.40, -0.02), (-0.52, -0.14), (-0.48, 0.0),
            (-0.52, 0.14), (-0.40, 0.03), (-0.26, 0.07), (0.0, 0.10), (0.30, 0.07)]
    fins = [(0.02, -0.09), (-0.08, -0.20), (-0.12, -0.08)]
    m = sh(lambda d: [d.polygon(xf(fish, 0.56, 0.58, 0.82, 50), fill=255), d.polygon(xf(fins, 0.56, 0.58, 0.82, 50),
                                                                                    fill=255)])
    lit(c, m, (160, 230, 255), lin((236, 246, 255), (80, 120, 170), 140), 16, 1.4, sh=True)
    ex, ey = at(0.32, -0.02, 0.56, 0.58, 0.82, 50)
    K.fill(c, K.soften(circ(ex, ey, 0.018), 0.8), (20, 20, 40, 255))
    splash = sh(lambda d: [GD_flame(d, x, 0.98, 0.04, h, l) for x, h, l in ((0.70, 0.18, 0.05), (0.80, 0.14, 0.08),
                                                                             (0.62, 0.12, -0.04))])
    water_paint(c, splash, gr=8, shadow=False)
    return K.finish(c)


def tail_whip():
    c = water_bg(0.5, 0.5)
    sw = sh(lambda d: [d.polygon(pts(swell(arc(0.62, 0.40, r, 140, 300, 30), 0.05)), fill=255) for r in (0.32, 0.42)])
    lit(c, sw, (200, 240, 255), (240, 252, 255), 10, 1.3)
    tail = [(0.08 + 0.72 * t, 0.94 - 0.70 * t + 0.16 * math.sin(math.pi * 2 * t)) for t in (i / 40 for i in range(41))]
    m = poly(taper(tail, 0.24, 0.04))
    fin = poly([(0.78, 0.26), (0.98, 0.06), (0.92, 0.24), (1.0, 0.40), (0.84, 0.34)])
    finm = poly([(0.80, 0.28), (0.94, 0.12), (0.90, 0.26), (0.96, 0.36)])
    both = add(m, fin)
    lit(c, both, (140, 220, 255), lin((140, 210, 250), (16, 50, 130), 45), 14, 1.3, sh=True)
    K.fill(c, scale(K.soften(finm, 2), 0.6), (200, 245, 255, 255))
    sc = sh(lambda d: [d.polygon(pts(swell(arc(x, y, 0.035, 200, 340, 8), 0.014)), fill=255) for x, y in
                       [tail[i] for i in (6, 12, 18, 24, 30)]])
    K.fill(c, scale(K.soften(sc), 0.7), (220, 250, 255, 255))
    belly = poly(taper([(x + 0.02, y + 0.04) for x, y in tail[:34]], 0.06, 0.01))
    K.fill(c, scale(K.soften(inter(belly, m), 2), 0.5), (200, 240, 255, 255))
    motes(c, 4, 14, (0.5, 0.05, 0.95, 0.5), (0.006, 0.016), (240, 252, 255), (160, 230, 255))
    return K.finish(c)


def spinning_dive():
    c = water_bg(0.5, 0.5)
    sp = sh(lambda d: [d.polygon(pts(taper([(0.5 + math.cos(math.radians(a0 + t * 6)) * (0.03 + t * 0.0040),
                                             0.5 + math.sin(math.radians(a0 + t * 6)) * (0.03 + t * 0.0040))
                                            for t in range(0, 101, 2)], 0.01, 0.09)), fill=255)
                       for a0 in (0, 120, 240)])
    water_paint(c, sp, gr=16, shadow=False)
    core = circ(0.5, 0.5, 0.08)
    K.glow(c, core, (20, 40, 120, 255), 12, 1.4)
    K.fill(c, K.soften(core), (8, 20, 60, 255))
    motes(c, 4, 14, (0.12, 0.12, 0.88, 0.88), (0.005, 0.012), (230, 250, 255), (120, 200, 255))
    return K.finish(c)


def grand_fall():
    c = bg((60, 140, 200), (2, 14, 36), cy=0.8)
    fall = poly([(0.30, 0.0), (0.70, 0.0), (0.66, 0.74), (0.34, 0.74)])
    K.glow(c, fall, (140, 220, 255, 255), 22, 1.2)
    K.fill(c, K.soften(fall, 3), lin((120, 190, 250), (230, 250, 255)))
    lines = sh(lambda d: [brush(d, [(x, 0.0), (x - (x - 0.5) * 0.1, 0.72)], 0.012) for x in
                          (0.36, 0.43, 0.50, 0.57, 0.64)])
    K.fill(c, scale(K.soften(lines), 0.5), (40, 110, 200, 255))
    sp = sh(lambda d: [GD_flame(d, x, 0.90, w, h, l) for x, w, h, l in ((0.5, 0.22, 0.26, 0), (0.24, 0.10, 0.20, -0.1),
                                                                         (0.76, 0.10, 0.20, 0.1))])
    water_paint(c, sp, shadow=False)
    motes(c, 5, 18, (0.1, 0.55, 0.9, 0.95), (0.006, 0.016), (240, 250, 255), (150, 220, 255))
    return K.finish(c)


def tidal_wave():
    c = bg((170, 230, 255), (20, 60, 130), cx=0.7, cy=0.55, r=0.75)
    motes(c, 3, 14, (0.6, 0.4, 0.95, 0.9), (0.004, 0.010), (240, 250, 255), None, 200)
    outer = [(-0.05, 1.05), (-0.05, 0.50), (0.06, 0.30), (0.22, 0.14), (0.42, 0.06), (0.60, 0.08), (0.74, 0.16),
             (0.84, 0.30), (0.86, 0.44), (0.80, 0.50), (0.76, 0.40)]
    inner = [(0.70, 0.32), (0.60, 0.26), (0.48, 0.30), (0.40, 0.42), (0.38, 0.60), (0.46, 0.82), (0.60, 1.05)]
    body = poly(outer + inner)
    K.shadow(c, body, 6, 9, 9, 170)
    K.fill(c, K.soften(body, 2), lin((60, 160, 240), (4, 30, 100), 20))
    # the hollow's light face, the foam lip with its claws, streaks down the back
    face = poly(taper(inner[1:], 0.06, 0.02))
    K.fill(c, scale(K.soften(face, 4), 0.6), (170, 230, 255, 255))
    lip = sh(lambda d: d.polygon(pts(swell(outer[2:10], 0.07)), fill=255))
    claws = sh(lambda d: [d.polygon(pts(taper(bow(x, y, x + 0.02, y + 0.10, -0.03, 8), 0.03, 0.004)), fill=255)
                          for x, y in ((0.80, 0.40), (0.72, 0.20), (0.62, 0.12), (0.84, 0.30))])
    foam = add(lip, claws)
    K.glow(c, foam, (220, 250, 255, 255), 10, 1.4)
    K.fill(c, K.soften(foam), (245, 252, 255, 255))
    back = sh(lambda d: [brush(d, [(0.08 + k * 0.08, 0.40 + k * 0.02), (0.20 + k * 0.06, 0.80)], 0.012)
                         for k in range(4)])
    K.fill(c, scale(K.soften(inter(back, body), 2), 0.4), (200, 240, 255, 255))
    serpent_head(c, 0.62, 0.64, 0.38, 15, open_=True, glowc=(220, 250, 255))
    motes(c, 7, 16, (0.1, 0.0, 0.9, 0.3), (0.006, 0.014), (240, 252, 255), (160, 230, 255))
    return K.finish(c)


def spring_water():
    c = bg((60, 170, 200), (4, 26, 40), cy=0.6)
    jet = sh(lambda d: [d.polygon(pts(taper(bow(0.5, 0.86, x, y, b, 20), 0.07, 0.02)), fill=255)
                        for x, y, b in ((0.5, 0.18, 0), (0.24, 0.48, 0.10), (0.76, 0.48, -0.10))])
    water_paint(c, jet, shadow=False)
    drops = sh(lambda d: [droplet(d, x, y, 0.03) for x, y in ((0.18, 0.66), (0.82, 0.66), (0.36, 0.30), (0.64, 0.30))])
    water_paint(c, drops, gr=6, shadow=False)
    basin = circ(0.5, 0.86, 0.26, 0.06)
    lit(c, basin, (160, 230, 255), lin((200, 240, 255), (60, 140, 220)), 10, 1.2)
    sparkles(c, [(0.5, 0.16, 0.10)], glowc=(180, 255, 220))
    return K.finish(c)


def slowga():
    c = water_bg()
    bubble = circ(0.5, 0.5, 0.38)
    K.fill(c, scale(K.soften(bubble, 6), 0.3), (160, 220, 255, 255))
    rimm = ring(0.5, 0.5, 0.38, 0.02)
    lit(c, rimm, (160, 220, 255), (220, 245, 255), 10, 1.2)
    hg = sh(lambda d: hourglass(d, 0.5, 0.52, 0.80))
    lit(c, hg, (180, 230, 255), lin((236, 246, 255), (120, 170, 220)), 14, 1.3, sh=True)
    sand = sh(lambda d: [d.polygon(pts([(0.40, 0.30), (0.60, 0.30), (0.5, 0.47)]), fill=255),
                         d.polygon(pts([(0.5, 0.62), (0.62, 0.80), (0.38, 0.80)]), fill=255)])
    K.fill(c, K.soften(sand), (40, 100, 190, 255))
    frame_ = sh(lambda d: [d.rounded_rectangle(pts([(0.30, 0.16), (0.70, 0.21)]), radius=0.02 * W, fill=255),
                           d.rounded_rectangle(pts([(0.30, 0.83), (0.70, 0.88)]), radius=0.02 * W, fill=255)])
    lit(c, frame_, (120, 180, 255), lin((140, 200, 255), (30, 70, 150)), 8, 1.0, sh=True)
    sparkles(c, [(0.30, 0.28, 0.05)], glowc=(200, 240, 255))
    return K.finish(c)


def tidal_roar():
    c = water_bg(0.4, 0.4)
    sound_waves(c, 0.56, 0.36, (0.18, 0.27, 0.36), -60, 30, 0.05, (220, 245, 255), (120, 200, 255))
    serpent_head(c, 0.40, 0.42, 0.62, -20, open_=True)
    sea = poly([(0.0, 0.80), (0.3, 0.76), (0.6, 0.80), (1.0, 0.76), (1.0, 1.0), (0.0, 1.0)])
    lit(c, sea, (120, 200, 255), lin((90, 170, 240), (10, 40, 110)), 10, 1.0)
    rip = sh(lambda d: [d.polygon(pts(swell(arc(0.28, 0.80, r, 190, 350, 20, ry=r * 0.25), 0.02)), fill=255)
                        for r in (0.14, 0.22)])
    K.fill(c, K.soften(rip), (220, 245, 255, 255))
    ar = sh(lambda d: down_arrow(d, 0.84, 0.62, 0.36))
    lit(c, ar, (255, 100, 90), lin((255, 170, 160), (210, 40, 50)), 8, 1.3, sh=True)
    return K.finish(c)


def soothing_current():
    c = bg((50, 160, 190), (2, 24, 36), cy=0.5)
    cur = sh(lambda d: [d.polygon(pts(swell([(x, y0 + 0.08 * math.sin(math.pi * 2 * x + ph)) for x in
                                             [0.05 + 0.9 * i / 40 for i in range(41)]], w)), fill=255)
                        for y0, w, ph in ((0.34, 0.08, 0), (0.52, 0.10, 1.2), (0.70, 0.08, 2.4))])
    water_paint(c, cur, glowc=(160, 240, 255), shadow=False)
    motes(c, 6, 18, (0.1, 0.15, 0.9, 0.9), (0.006, 0.016), (230, 255, 240), (150, 255, 210))
    sparkles(c, [(0.76, 0.22, 0.08), (0.24, 0.80, 0.06)], glowc=(180, 255, 230))
    return K.finish(c)


# ---- Garuda: wind green ----------------------------------------------------------------------------------------------
def wind_bg(cx=0.5, cy=0.45):
    return bg((80, 170, 90), (6, 28, 12), cx=cx, cy=cy)


def gusts(c, spec, color=(230, 255, 230), glowc=(160, 255, 170), alpha=1.0):
    """Wind strokes: (cx, cy, r, a0, a1, w) arcs that swell and fade."""
    m = sh(lambda d: [d.polygon(pts(swell(arc(x, y, r, a0, a1, 30), w)), fill=255) for x, y, r, a0, a1, w in spec])
    K.glow(c, m, col(glowc), 10, 1.2 * alpha)
    K.fill(c, scale(K.soften(m), alpha), col(color))
    return m


def talon(d, x0, y0, x1, y1, w, b=0.06):
    """A hooked talon from root (x0, y0) to the tip."""
    d.polygon(pts(taper(bow(x0, y0, x1, y1, b, 20), w, 0.004)), fill=255)


def claw():
    c = wind_bg()
    slashes(c, [(0.20, 0.18, 0.56, 0.86, 0.07), (0.38, 0.12, 0.74, 0.80, 0.07), (0.56, 0.10, 0.88, 0.66, 0.07)], 0.08,
            (200, 255, 190), lin((255, 255, 245), (190, 240, 180), 60), 14, 1.4)
    tl = sh(lambda d: [talon(d, 0.14, 0.40, 0.28, 0.66, 0.07, -0.06), talon(d, 0.22, 0.34, 0.42, 0.60, 0.07, -0.06)])
    lit(c, tl, (255, 240, 180), lin((255, 250, 230), (190, 160, 110)), 10, 1.2, sh=True)
    return K.finish(c)


def predator_claws():
    c = bg((60, 140, 70), (4, 22, 8), cy=0.4)
    gusts(c, [(0.5, 0.5, 0.40, 200, 330, 0.03), (0.5, 0.5, 0.34, 20, 140, 0.025)], alpha=0.8)
    foot = sh(lambda d: [d.polygon(pts(taper([(0.5, 0.06), (0.5, 0.30), (0.5, 0.42)], 0.14, 0.18)), fill=255),
                         d.ellipse(pts([(0.40, 0.36), (0.60, 0.52)]), fill=255)])
    lit(c, foot, (220, 255, 200), lin((240, 220, 160), (150, 110, 60)), 12, 1.2, sh=True)
    scales_ = sh(lambda d: [brush(d, [(0.45, y), (0.5, y + 0.03), (0.55, y)], 0.012) for y in (0.12, 0.19, 0.26)])
    K.fill(c, scale(K.soften(scales_), 0.6), (90, 60, 30, 255))
    tl = sh(lambda d: [talon(d, 0.44, 0.46, 0.16, 0.80, 0.08, 0.08), talon(d, 0.50, 0.50, 0.50, 0.92, 0.09, -0.06),
                       talon(d, 0.56, 0.46, 0.84, 0.80, 0.08, -0.08), talon(d, 0.48, 0.40, 0.24, 0.26, 0.06, -0.06)])
    lit(c, tl, (255, 250, 220), lin((255, 255, 250), (170, 170, 160)), 12, 1.4, sh=True)
    return K.finish(c)


def wind_blade():
    c = wind_bg(0.5, 0.5)
    gusts(c, [(0.5, 0.5, r, 140, 400, 0.02) for r in (0.42,)], alpha=0.5)
    blade = minus(circ(0.46, 0.52, 0.34), circ(0.58, 0.44, 0.32))
    blade = rot(blade, 20)
    lit(c, blade, (200, 255, 200), lin((255, 255, 250), (160, 240, 170), 120), 20, 1.6, sh=True)
    streaks(c, [(0.80, 0.20, 0.96, 0.10), (0.84, 0.34, 1.0, 0.28), (0.70, 0.12, 0.84, 0.0)], (230, 255, 230, 255),
            0.016, 160, 3)
    return K.finish(c)


def tornado(c, cx, top, bot, w0, w1, color=(230, 255, 235), glowc=(170, 255, 180), bands=7, alpha=1.0):
    m = K.mask()
    d = ImageDraw.Draw(m)
    for i in range(bands):
        t = i / (bands - 1)
        y = top + (bot - top) * t
        w = w0 + (w1 - w0) * t
        sway = 0.04 * math.sin(t * 5)
        d.polygon(pts(swell(arc(cx + sway, y, w, 200, 520, 40, ry=w * 0.22), 0.04 * (1 - t * 0.5))), fill=255)
    K.glow(c, m, col(glowc), 12, 1.3 * alpha)
    K.fill(c, scale(K.soften(m), alpha), col(color))
    return m


def aerial_blast():
    c = bg((140, 220, 150), (6, 40, 20), cy=0.4, r=0.75)
    w = sh(lambda d: [wing(d, 0.44, 0.34, 1.15, -1, 7, 90, -70, 0.46, 0.05),
                      wing(d, 0.56, 0.34, 1.15, 1, 7, 90, -70, 0.46, 0.05)])
    funnel = poly([(0.20, 0.10), (0.80, 0.10), (0.56, 0.92), (0.44, 0.92)])
    lit(c, w, (230, 255, 220), lin((255, 255, 245), (150, 220, 150)), 16, 1.4, sh=True)
    K.fill(c, scale(funnel.filter(ImageFilter.GaussianBlur(10)), 0.85), (20, 80, 40, 255))
    tornado(c, 0.5, 0.14, 0.88, 0.32, 0.05, color=(240, 255, 240), glowc=(120, 255, 150), bands=8)
    rnd = random.Random(5)
    deb = sh(lambda d: [rock(d, rnd.uniform(0.15, 0.85), rnd.uniform(0.15, 0.8), rnd.uniform(0.012, 0.025), k, 5)
                        for k in range(9)])
    K.fill(c, K.soften(deb), (40, 70, 40, 255))
    sparkles(c, [(0.5, 0.86, 0.10)], glowc=(200, 255, 200))
    return K.finish(c)


def leafm(d, x, y, ang, L, w):
    import group_a as GA
    GA.leaf(d, x, y, ang, L, w)


def whispering_wind():
    c = bg((110, 190, 140), (8, 34, 22), cy=0.45)
    gusts(c, [(0.30, 0.60, 0.30, 250, 360, 0.05), (0.62, 0.40, 0.30, 70, 180, 0.05), (0.5, 0.5, 0.42, 180, 260, 0.03)])
    lv = sh(lambda d: [leafm(d, x, y, a, 0.18, 0.05) for x, y, a in ((0.28, 0.30, -0.6), (0.62, 0.66, 0.5),
                                                                       (0.70, 0.26, -1.4), (0.22, 0.70, 0.2))])
    lit(c, lv, (190, 255, 160), lin((210, 255, 170), (70, 170, 70)), 10, 1.3, sh=True)
    cr = cross_m(0.5, 0.48, 0.5)
    lit(c, cr, (180, 255, 200), (250, 255, 250), 14, 1.5)
    motes(c, 3, 14, (0.15, 0.15, 0.85, 0.85), (0.005, 0.012), (230, 255, 230), (160, 255, 180))
    return K.finish(c)


def winged_hourglass(c, cx, cy, s, pairs=1, glowc=(200, 255, 200)):
    for k in range(pairs):
        off = k * 0.12 * s
        w = sh(lambda d, off=off: [wing(d, cx - 0.11 * s, cy - 0.02 * s + off, s * (0.8 - 0.15 * k), -1, 5, 60, -60,
                                        0.40, 0.05),
                                   wing(d, cx + 0.11 * s, cy - 0.02 * s + off, s * (0.8 - 0.15 * k), 1, 5, 60, -60,
                                        0.40, 0.05)])
        lit(c, w, glowc, lin((255, 255, 250), (180, 240, 190)), 12, 1.3)
    hg = sh(lambda d: hourglass(d, cx, cy, 0.62 * s))
    lit(c, hg, (255, 230, 150), lin(*GOLD), 12, 1.3, sh=True)
    sand = sh(lambda d: [d.polygon(pts([(cx - 0.08 * s, cy - 0.17 * s), (cx + 0.08 * s, cy - 0.17 * s), (cx, cy - 0.02 * s)]),
                                   fill=255),
                         d.polygon(pts([(cx, cy + 0.08 * s), (cx + 0.10 * s, cy + 0.22 * s), (cx - 0.10 * s, cy + 0.22 * s)]),
                                   fill=255)])
    K.fill(c, K.soften(sand), (120, 70, 20, 255))


def hastega():
    c = wind_bg()
    streaks(c, [(0.04, 0.70, 0.30, 0.70), (0.70, 0.76, 0.96, 0.76), (0.06, 0.82, 0.26, 0.82)], (230, 255, 230, 255),
            0.016, 150, 3)
    winged_hourglass(c, 0.5, 0.52, 1.0)
    return K.finish(c)


def hastega_ii():
    c = bg((60, 160, 140), (4, 28, 26), cy=0.45)
    rays(c, 0.5, 0.5, 14, (220, 255, 230), alpha=60)
    winged_hourglass(c, 0.5, 0.50, 1.0, pairs=2, glowc=(200, 255, 230))
    sparkles(c, [(0.80, 0.22, 0.07), (0.20, 0.22, 0.07)], glowc=(200, 255, 220))
    return K.finish(c)


def aerial_armor():
    c = wind_bg(0.5, 0.5)
    for k, a in enumerate((0, 120, 240)):
        gusts(c, [(0.5, 0.5, 0.36 - k * 0.02, a, a + 150, 0.06)], alpha=0.9)
    fe = sh(lambda d: [leafm(d, 0.5 + math.cos(a) * 0.33, 0.5 + math.sin(a) * 0.33, a + 1.9, 0.16, 0.04)
                       for a in (0.4, 2.5, 4.6)])
    lit(c, fe, (230, 255, 220), lin((255, 255, 250), (170, 230, 170)), 8, 1.2)
    s_ = shield_shape(0.5, 0.30, 0.15, 0.40)
    lit(c, s_, (200, 255, 200), lin((210, 255, 220), (70, 160, 90)), 16, 1.4, sh=True)
    sparkles(c, [(0.46, 0.40, 0.05)])
    return K.finish(c)


def fleet_wind():
    c = bg((90, 180, 120), (6, 30, 16), cx=0.6, cy=0.5)
    streaks(c, [(0.0, y, 0.5, y) for y in (0.36, 0.48, 0.60, 0.72)], (230, 255, 230, 255), 0.02, 150, 4)
    boot = add(poly([(0.46, 0.20), (0.64, 0.20), (0.66, 0.58), (0.46, 0.70)]),
               circ(0.66, 0.68, 0.22, 0.10), circ(0.52, 0.66, 0.08))
    boot = minus(boot, poly([(0, 0.78), (1, 0.78), (1, 1), (0, 1)]))
    lit(c, boot, (220, 255, 210), lin((255, 248, 230), (190, 170, 140)), 14, 1.3, sh=True)
    trim = sh(lambda d: [d.rectangle(pts([(0.45, 0.20), (0.65, 0.26)]), fill=255),
                         d.rectangle(pts([(0.40, 0.74), (0.90, 0.78)]), fill=255)])
    K.fill(c, K.soften(inter(trim, add(boot, trim))), lin(*GOLD))
    w = sh(lambda d: wing(d, 0.48, 0.36, 0.85, -1, 5, 60, -65, 0.44, 0.055))
    lit(c, w, (230, 255, 230), lin((255, 255, 250), (180, 240, 190)), 12, 1.4, sh=True)
    return K.finish(c)


# ---- Shiva: ice ------------------------------------------------------------------------------------------------------
def ice_bg(cx=0.5, cy=0.42):
    return bg((110, 170, 230), (6, 18, 50), cx=cx, cy=cy)


def axe_kick():
    c = ice_bg(0.5, 0.8)
    trail = sh(lambda d: d.polygon(pts(swell(arc(0.62, 0.62, 0.44, 185, 268, 30), 0.16)), fill=255))
    K.glow(c, trail, (190, 240, 255, 255), 20, 1.2)
    K.fill(c, scale(K.soften(trail, 3), 0.75), lin((255, 255, 255), (150, 210, 255), 0))
    leg = poly([(0.40, -0.04), (0.60, -0.04), (0.60, 0.50), (0.74, 0.64), (0.78, 0.72), (0.70, 0.76), (0.46, 0.74),
                (0.38, 0.66), (0.40, 0.40)])
    lit(c, leg, (200, 240, 255), lin((236, 246, 255), (110, 160, 230), 0), 14, 1.4, sh=True)
    cuff = inter(leg, poly([(0, 0.40), (1, 0.40), (1, 0.48), (0, 0.48)]))
    K.fill(c, K.soften(cuff), (60, 110, 200, 255))
    boot = inter(leg, poly([(0, 0.48), (1, 0.48), (1, 1), (0, 1)]))
    K.fill(c, K.soften(boot), lin((150, 200, 255), (40, 80, 170)))
    imp = poly(burst_pts(0.56, 0.84, 8, 0.20, 0.07, rot0=-90))
    lit(c, imp, (220, 245, 255), (255, 255, 255), 14, 1.4)
    shards = sh(lambda d: [shard(d, 0.56 + math.cos(a) * 0.25, 0.86 + math.sin(a) * 0.12, 0.13, 0.024,
                                 math.degrees(a)) for a in (math.pi * 1.0, math.pi * 1.2, math.pi * 1.8, math.pi * 2.0)])
    ice_paint(c, shards, gr=8)
    return K.finish(c)


def palm(d, cx, cy, s, ang=0):
    q = [(-0.16, 0.24), (-0.18, -0.02), (-0.30, -0.14), (-0.27, -0.19), (-0.14, -0.10), (-0.14, -0.40),
         (-0.08, -0.42), (-0.05, -0.16), (-0.04, -0.48), (0.03, -0.48), (0.04, -0.17), (0.07, -0.44), (0.13, -0.43),
         (0.12, -0.14), (0.17, -0.34), (0.22, -0.32), (0.18, -0.02), (0.15, 0.24)]
    d.polygon(xf(q, cx, cy, s, ang), fill=255)


def double_slap():
    c = ice_bg(0.5, 0.5)
    rays(c, 0.5, 0.5, 12, (220, 240, 255), alpha=60)
    for x, y, a, k in ((0.34, 0.52, -18, 0.9), (0.64, 0.50, 18, 1.0)):
        h = sh(lambda d, x=x, y=y, a=a, k=k: palm(d, x, y, k, a))
        lit(c, h, (200, 240, 255), lin((240, 250, 255), (140, 190, 240)), 14, 1.3, sh=True)
    st = sh(lambda d: [d.polygon(pts(burst_pts(0.5, 0.18, 6, 0.08, 0.03)), fill=255)])
    lit(c, st, (255, 255, 255), (255, 255, 255), 8, 1.4)
    return K.finish(c)


def rush():
    c = ice_bg(0.7, 0.5)
    for k, (y, L) in enumerate(((0.30, 0.6), (0.50, 0.8), (0.70, 0.6))):
        tr = poly([(0.86, y - 0.03), (0.86, y + 0.03), (0.86 - L, y)])
        K.fill(c, scale(K.soften(tr, 6), 0.8), (200, 240, 255, 255))
    sp = sh(lambda d: [shard(d, 0.62, y, 0.40 if y == 0.5 else 0.30, 0.05, 0) for y in (0.30, 0.50, 0.70)])
    ice_paint(c, sp, gr=14)
    imp = poly(burst_pts(0.88, 0.50, 7, 0.14, 0.06))
    lit(c, imp, (220, 245, 255), (255, 255, 255), 12, 1.4)
    return K.finish(c)


def heavenly_strike():
    c = bg((140, 190, 240), (10, 24, 60), cy=0.1)
    cloud = sh(lambda d: [d.ellipse(pts([(x - r, 0.10 - r * 0.6), (x + r, 0.10 + r * 0.6)]), fill=255)
                          for x, r in ((0.2, 0.18), (0.45, 0.22), (0.7, 0.2), (0.9, 0.15))])
    K.fill(c, scale(K.soften(cloud, 8), 0.8), (230, 240, 255, 255))
    ic = sh(lambda d: [d.polygon(pts([(x - w, y0), (x + w, y0), (x, y0 + h)]), fill=255)
                       for x, y0, w, h in ((0.5, 0.14, 0.09, 0.68), (0.30, 0.16, 0.06, 0.46), (0.70, 0.16, 0.06, 0.50),
                                           (0.16, 0.22, 0.04, 0.28), (0.84, 0.22, 0.04, 0.30))])
    ice_paint(c, ic, gr=16)
    facet = inter(ic, poly([(0.5, 0), (1, 0), (1, 1), (0.5, 1)]))
    K.fill(c, scale(K.soften(facet), 0.18), (20, 60, 140, 255))
    st = sh(lambda d: d.polygon(pts(burst_pts(0.5, 0.84, 8, 0.12, 0.04)), fill=255))
    lit(c, st, (220, 245, 255), (255, 255, 255), 12, 1.5)
    return K.finish(c)


def diamond_dust():
    c = bg((170, 220, 255), (10, 30, 80), cy=0.5, r=0.7)
    rays(c, 0.5, 0.5, 24, (240, 250, 255), width=0.04, alpha=120, blur=5)
    sf = sh(lambda d: snowflake(d, 0.5, 0.5, 0.40, 0.045))
    ice_paint(c, sf, glowc=(200, 240, 255), gr=22, gs=1.5)
    hexc = poly(hexagon(0.5, 0.5, 0.12, 0))
    lit(c, hexc, (255, 255, 255), lin((255, 255, 255), (170, 220, 255)), 16, 1.6)
    rnd = random.Random(3)
    dia = sh(lambda d: [d.polygon(pts([(x, y - r), (x + r * 0.7, y), (x, y + r), (x - r * 0.7, y)]), fill=255)
                        for x, y, r in [(rnd.uniform(0.12, 0.88), rnd.uniform(0.12, 0.88), rnd.uniform(0.015, 0.03))
                                        for _ in range(16)]])
    lit(c, dia, (220, 250, 255), (255, 255, 255), 6, 1.5)
    sparkles(c, [(0.5, 0.5, 0.16), (0.78, 0.22, 0.07), (0.22, 0.78, 0.06)], glowc=(210, 240, 255))
    return K.finish(c)


def diamond_storm():
    c = ice_bg(0.5, 0.5)
    for a0 in (0, 120, 240):
        gusts(c, [(0.5, 0.5, 0.36, a0, a0 + 130, 0.09), (0.5, 0.5, 0.22, a0 + 60, a0 + 170, 0.06)], (240, 250, 255),
              (170, 220, 255), 1.0)
    spots = [(0.5, 0.5, 0.11), (0.24, 0.30, 0.06), (0.78, 0.34, 0.065), (0.30, 0.76, 0.055), (0.70, 0.18, 0.045),
             (0.16, 0.56, 0.04)]
    dia = sh(lambda d: [d.polygon(pts([(x, y - r), (x + r * 0.75, y - r * 0.25), (x, y + r), (x - r * 0.75, y - r * 0.25)]),
                                  fill=255) for x, y, r in spots])
    ice_paint(c, dia, gr=12, gs=1.5)
    ar = sh(lambda d: down_arrow(d, 0.76, 0.72, 0.34))
    lit(c, ar, (255, 110, 110), lin((255, 180, 170), (210, 50, 60)), 8, 1.3, sh=True)
    return K.finish(c)


def crystal_blessing():
    c = bg((150, 190, 240), (14, 24, 60), cy=0.5)
    rays(c, 0.5, 0.48, 12, (240, 245, 255), alpha=80)
    ribbon = sh(lambda d: [d.polygon(pts(swell([(0.5 + math.cos(t * 0.11) * 0.32, 0.90 - t * 0.0080)
                                                for t in range(0, 101, 4)], 0.035)), fill=255)])
    back = inter(ribbon, poly([(0, 0), (1, 0), (1, 1), (0, 1)]))
    K.fill(c, scale(K.soften(back), 0.4), (255, 220, 140, 255))
    GD.crystal(c, 0.5, 0.44, 0.20, 0.30, (255, 255, 255), (170, 210, 250), (90, 140, 220), (200, 230, 255))
    front = inter(ribbon, poly([(0.5, 0.0), (1, 0), (1, 1), (0.5, 1)]))
    lit(c, front, (255, 230, 150), lin((255, 250, 210), (240, 190, 90)), 8, 1.2)
    motes(c, 7, 14, (0.2, 0.1, 0.8, 0.9), (0.006, 0.013), (255, 245, 210), (255, 220, 140))
    return K.finish(c)


def frost_armor():
    c = ice_bg(0.5, 0.5)
    spk = sh(lambda d: [shard(d, 0.5 + math.cos(a) * 0.30, 0.52 + math.sin(a) * 0.30, 0.22, 0.04, math.degrees(a))
                        for a in [math.pi * 2 * i / 10 + 0.3 for i in range(10)]])
    ice_paint(c, spk, gr=12)
    s_ = shield_shape(0.5, 0.26, 0.20, 0.52)
    lit(c, s_, (200, 240, 255), lin((236, 248, 255), (90, 150, 220)), 16, 1.4, sh=True)
    sf = sh(lambda d: snowflake(d, 0.5, 0.50, 0.11, 0.025, branches=False))
    K.fill(c, K.soften(sf), (40, 90, 170, 255))
    return K.finish(c)


def sleepga_shiva():
    c = bg((80, 120, 200), (4, 10, 36), cy=0.5)
    cres = minus(circ(0.40, 0.52, 0.27), circ(0.52, 0.44, 0.25))
    lit(c, cres, (190, 230, 255), lin((255, 255, 255), (160, 210, 255), 120), 20, 1.5)
    sf = sh(lambda d: [snowflake(d, 0.24, 0.24, 0.07, 0.016, False), snowflake(d, 0.74, 0.80, 0.06, 0.014, False)])
    lit(c, sf, (200, 240, 255), (240, 250, 255), 6, 1.2)
    ztext(c, [(0.64, 0.44, 0.14), (0.78, 0.26, 0.10), (0.86, 0.12, 0.07)], (240, 250, 255), (160, 210, 255))
    return K.finish(c)


# ---- Ramuh: thunder violet -------------------------------------------------------------------------------------------
def thunder_bg(cx=0.5, cy=0.45):
    return bg((120, 80, 200), (10, 4, 30), cx=cx, cy=cy)


def staff(d, x0, y0, x1, y1, w=0.035):
    """Ramuh's staff from its foot to its head: a shaft with a crook and an orb."""
    brush(d, [(x0, y0), (x1, y1)], w)
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    cx, cy = x1 + ux * 0.07, y1 + uy * 0.07
    brush(d, arc(cx, cy, 0.07, math.degrees(math.atan2(uy, ux)) + 180, math.degrees(math.atan2(uy, ux)) + 430, 24),
          w * 0.9)


def staff_paint(c, m):
    lit(c, m, (230, 200, 255), lin((236, 210, 160), (130, 90, 50)), 10, 1.0, sh=True)


def shock_strike():
    c = thunder_bg(0.65, 0.35)
    st = sh(lambda d: staff(d, 0.16, 0.90, 0.56, 0.38, 0.04))
    staff_paint(c, st)
    burst = poly(burst_pts(0.66, 0.28, 9, 0.24, 0.07, seed=2))
    lit(c, burst, (210, 170, 255), rad((255, 255, 255), (200, 170, 255), 0.66, 0.28, 0.2), 20, 1.6)
    for k, (x, y) in enumerate(((0.92, 0.10), (0.94, 0.42), (0.80, 0.0), (0.44, 0.06))):
        bolt(c, zigzag(0.66, 0.28, x, y, 3, 0.03, k), 0.02, 0.006, gr=8)
    orb = circ(0.62, 0.32, 0.05)
    lit(c, orb, (255, 255, 255), (255, 255, 255), 10, 1.6)
    return K.finish(c)


def thunderspark():
    c = thunder_bg(0.5, 0.5)
    for k in range(9):
        a = math.pi * 2 * k / 9 + 0.2
        bolt(c, zigzag(0.5, 0.52, 0.5 + math.cos(a) * 0.42, 0.52 + math.sin(a) * 0.42, 4, 0.04, k), 0.035, 0.008, gr=10)
    core = circ(0.5, 0.52, 0.12)
    lit(c, core, (220, 190, 255), rad((255, 255, 255), (210, 190, 255), 0.5, 0.5, 0.12), 26, 1.8)
    sparkles(c, [(0.5, 0.52, 0.14)], glowc=(230, 200, 255))
    return K.finish(c)


def chaotic_strike():
    c = bg((150, 60, 170), (16, 4, 26), cy=0.5)
    for k, (x0, y0, x1, y1) in enumerate(((0.12, 0.06, 0.62, 0.60), (0.90, 0.10, 0.44, 0.62), (0.50, 0.0, 0.52, 0.58),
                                          (0.04, 0.50, 0.50, 0.60), (0.96, 0.56, 0.56, 0.62))):
        bolt(c, zigzag(x0, y0, x1, y1, 5, 0.05, k + 3), 0.05, 0.015, glowc=(230, 160, 255), gr=12)
    imp = poly(burst_pts(0.52, 0.64, 10, 0.24, 0.10, seed=4))
    lit(c, imp, (255, 200, 255), rad((255, 255, 255), (230, 170, 255), 0.52, 0.64, 0.2), 18, 1.5)
    return K.finish(c)


def storm_cloud(c, cy=0.20, dark=True):
    cl = sh(lambda d: [d.ellipse(pts([(x - r, y - r * 0.7), (x + r, y + r * 0.7)]), fill=255)
                       for x, y, r in ((0.18, cy + 0.04, 0.18), (0.40, cy - 0.04, 0.22), (0.64, cy - 0.02, 0.22),
                                       (0.86, cy + 0.04, 0.17), (0.5, cy + 0.08, 0.24))])
    lit(c, cl, (180, 150, 255), lin((150, 130, 190), (40, 30, 70)), 12, 1.0, sh=True)
    return cl


def thunderstorm_ramuh():
    c = bg((90, 60, 160), (6, 2, 20), cy=0.6)
    rain = sh(lambda d: [brush(d, [(x, y), (x - 0.04, y + 0.12)], 0.008) for x, y in
                         [(0.1 + 0.08 * i, 0.40 + 0.1 * (i % 3)) for i in range(11)]])
    K.fill(c, scale(K.soften(rain), 0.5), (200, 190, 255, 255))
    bolt(c, zigzag(0.40, 0.30, 0.30, 0.90, 5, 0.06, 1), 0.05, 0.015, gr=16)
    bolt(c, zigzag(0.66, 0.30, 0.72, 0.80, 4, 0.05, 2), 0.04, 0.012, gr=12)
    storm_cloud(c, 0.22)
    return K.finish(c)


def judgment_bolt():
    c = bg((210, 180, 255), (30, 10, 70), cy=0.62, r=0.7)
    rays(c, 0.5, 0.80, 20, (255, 250, 255), width=0.05, length=0.9, alpha=120)
    storm_cloud(c, 0.10)
    main = poly([(0.56, 0.12), (0.30, 0.52), (0.46, 0.52), (0.34, 0.92), (0.70, 0.40), (0.53, 0.40), (0.68, 0.12)])
    K.glow(c, main, (200, 150, 255, 255), 30, 1.5)
    K.shadow(c, main, 5, 8, 8, 170)
    K.fill(c, K.soften(main), lin((255, 255, 240), (255, 214, 110)))
    edge = minus(main, ImageChops.offset(main, 6, 0))
    K.fill(c, scale(K.soften(edge), 0.8), (255, 255, 255, 255))
    for k, (x1, y1) in enumerate(((0.18, 0.62), (0.84, 0.56), (0.30, 0.90), (0.72, 0.92))):
        bolt(c, zigzag(0.50, 0.40 + 0.1 * (k % 2), x1, y1, 3, 0.04, k), 0.035, 0.008, gr=10)
    flash = poly(burst_pts(0.36, 0.90, 9, 0.18, 0.06))
    lit(c, flash, (255, 240, 200), (255, 255, 240), 18, 1.5)
    st = sh(lambda d: staff(d, 0.84, 0.98, 0.84, 0.36, 0.035))
    staff_paint(c, st)
    sparkles(c, [(0.84, 0.29, 0.08)], glowc=(230, 200, 255))
    return K.finish(c)


def volt_strike():
    c = thunder_bg(0.5, 0.5)
    rays(c, 0.5, 0.52, 14, (230, 210, 255), alpha=70)
    fist(c, 0.5, 0.54, 0.95, (200, 160, 255), skin=((250, 240, 255), (150, 120, 200)), line=(50, 20, 90),
         knuckle=(255, 255, 255))
    for k, (x0, y0, x1, y1) in enumerate(((0.18, 0.20, 0.36, 0.44), (0.84, 0.22, 0.66, 0.44), (0.20, 0.84, 0.36, 0.64),
                                          (0.82, 0.84, 0.64, 0.66))):
        bolt(c, zigzag(x0, y0, x1, y1, 3, 0.03, k), 0.03, 0.01, gr=10)
    return K.finish(c)


def rolling_thunder():
    c = thunder_bg(0.5, 0.5)
    blade = sh(lambda d: GD.sword(d, 0.5, 0.10, 0.92, 0.055))
    lit(c, blade, (220, 190, 255), lin((255, 255, 255), (190, 180, 220), 0), 14, 1.4, sh=True)
    for k, (x0, y0, x1, y1) in enumerate(((0.30, 0.66, 0.70, 0.40), (0.70, 0.30, 0.30, 0.16), (0.26, 0.40, 0.66, 0.60))):
        bolt(c, zigzag(x0, y0, x1, y1, 5, 0.05, k), 0.03, 0.012, glowc=(200, 150, 255), gr=10, gs=1.6)
    sparkles(c, [(0.5, 0.10, 0.08)], glowc=(220, 190, 255))
    return K.finish(c)


def lightning_armor():
    c = bg((90, 70, 170), (8, 4, 28), cy=0.45)
    plate = poly([(0.30, 0.20), (0.42, 0.24), (0.5, 0.30), (0.58, 0.24), (0.70, 0.20), (0.86, 0.30), (0.80, 0.48),
                  (0.70, 0.46), (0.68, 0.76), (0.5, 0.86), (0.32, 0.76), (0.30, 0.46), (0.20, 0.48), (0.14, 0.30)])
    lit(c, plate, (200, 160, 255), lin((220, 210, 250), (90, 70, 150), 60), 18, 1.3, sh=True)
    b = sh(lambda d: [brush(d, zigzag(0.5, 0.32, 0.5, 0.82, 4, 0.05, 3), 0.04, 0.02)])
    lit(c, b, (255, 230, 120), (255, 250, 200), 10, 1.5)
    for k, (x0, y0, x1, y1) in enumerate(((0.14, 0.30, 0.02, 0.14), (0.86, 0.30, 0.98, 0.16), (0.32, 0.76, 0.18, 0.92),
                                          (0.68, 0.76, 0.82, 0.92))):
        bolt(c, zigzag(x0, y0, x1, y1, 3, 0.025, k), 0.025, 0.008, gr=8)
    return K.finish(c)


def shock_squall():
    c = thunder_bg(0.5, 0.5)
    gusts(c, [(0.5, 0.5, 0.36, 160, 330, 0.07), (0.5, 0.5, 0.26, -20, 150, 0.06)], (240, 230, 255), (180, 140, 255))
    bolt(c, zigzag(0.30, 0.20, 0.66, 0.80, 5, 0.06, 5), 0.06, 0.02, glowc=(220, 180, 255), gr=14)
    stars_ = sh(lambda d: [K.sparkle(d, x, y, r) for x, y, r in ((0.78, 0.26, 0.07), (0.20, 0.70, 0.06),
                                                               (0.84, 0.62, 0.05))])
    lit(c, stars_, (255, 240, 140), (255, 250, 210), 8, 1.4)
    return K.finish(c)


# ---- Diabolos: dark purple, the lord of dreams -----------------------------------------------------------------------
def dark_bg(cx=0.5, cy=0.45):
    return bg((110, 40, 150), (10, 2, 22), cx=cx, cy=cy)


def bat_wings(d, cx, cy, s):
    for sx in (-1, 1):
        q = [(0.04, -0.04), (0.18, -0.20), (0.36, -0.30), (0.50, -0.26), (0.46, -0.12), (0.40, 0.02), (0.34, -0.04),
             (0.28, 0.08), (0.20, 0.02), (0.14, 0.12), (0.04, 0.06)]
        d.polygon(pts([(cx + sx * x * s, cy + y * s) for x, y in q]), fill=255)


def demon_mask(d, cx, cy, s):
    """Diabolos' face: a horned, pointed mask."""
    q = [(-0.20, -0.16), (-0.36, -0.40), (-0.12, -0.22), (0.12, -0.22), (0.36, -0.40), (0.20, -0.16), (0.22, 0.04),
         (0.10, 0.22), (0.0, 0.32), (-0.10, 0.22), (-0.22, 0.04)]
    d.polygon(pts([(cx + x * s, cy + y * s) for x, y in q]), fill=255)


def red_eyes(c, cx, cy, s, glowc=(255, 40, 60)):
    e = sh(lambda d: [d.polygon(pts([(cx + sx * 0.04 * s, cy), (cx + sx * 0.16 * s, cy - 0.04 * s),
                                     (cx + sx * 0.13 * s, cy + 0.02 * s)]), fill=255) for sx in (-1, 1)])
    lit(c, e, glowc, (255, 220, 200), 8, 1.9)


def camisado():
    c = dark_bg(0.5, 0.35)
    cres = minus(circ(0.66, 0.30, 0.16), circ(0.72, 0.25, 0.15))
    lit(c, cres, (220, 180, 255), (250, 240, 255), 14, 1.4)
    slashes(c, [(0.16, 0.20, 0.50, 0.86, 0.07), (0.30, 0.16, 0.66, 0.84, 0.07), (0.46, 0.18, 0.82, 0.80, 0.07)], 0.09,
            (200, 90, 255), lin((250, 220, 255), (170, 80, 230), 60), 18, 1.6)
    red_eyes(c, 0.30, 0.20, 0.7)
    return K.finish(c)


def nether_blast():
    c = dark_bg(0.3, 0.7)
    portal = circ(0.26, 0.74, 0.20, 0.12)
    K.glow(c, portal, (190, 60, 255, 255), 26, 1.5)
    K.fill(c, K.soften(portal), rad((10, 0, 20), (90, 30, 140), 0.26, 0.74, 0.2))
    beam = poly([(0.20, 0.70), (0.32, 0.80), (0.98, 0.18), (0.80, 0.02)])
    K.glow(c, beam, (200, 80, 255, 255), 24, 1.5)
    K.fill(c, K.soften(beam, 4), lin((140, 40, 220), (255, 230, 255), 315))
    corebeam = poly([(0.24, 0.73), (0.29, 0.77), (0.93, 0.14), (0.86, 0.07)])
    K.fill(c, K.soften(corebeam, 3), (255, 250, 255, 255))
    motes(c, 5, 16, (0.3, 0.1, 0.9, 0.7), (0.005, 0.012), (240, 200, 255), (190, 80, 255))
    return K.finish(c)


def cacodemonia():
    c = bg((150, 30, 90), (14, 2, 14), cy=0.45)
    rays(c, 0.5, 0.48, 12, (255, 120, 200), alpha=60)
    m = sh(lambda d: demon_mask(d, 0.5, 0.50, 1.0))
    lit(c, m, (230, 80, 200), lin((90, 40, 110), (30, 8, 40)), 18, 1.4, sh=True)
    red_eyes(c, 0.5, 0.44, 1.0)
    mouth = poly([(0.40, 0.60), (0.60, 0.60), (0.5, 0.70)])
    K.fill(c, K.soften(mouth), (20, 0, 10, 255))
    fangs = sh(lambda d: [d.polygon(pts([(x - 0.02, 0.60), (x + 0.02, 0.60), (x, 0.65)]), fill=255) for x in (0.45, 0.55)])
    K.fill(c, K.soften(fangs, 0.8), (255, 240, 240, 255))
    return K.finish(c)


def ruinous_omen():
    c = bg((90, 10, 50), (6, 0, 8), cy=0.40, r=0.7)
    sun = circ(0.5, 0.40, 0.30)
    K.glow(c, sun, (255, 50, 50, 255), 44, 2.0)
    K.fill(c, K.soften(sun), rad((255, 200, 120), (220, 30, 40), 0.5, 0.40, 0.30))
    K.fill(c, K.soften(circ(0.5, 0.40, 0.27)), rad((40, 4, 24), (10, 0, 10), 0.5, 0.40, 0.27))
    w = sh(lambda d: [d.polygon(pts([(0.5 + sx * x, y) for x, y in
                                     [(0.06, 0.50), (0.16, 0.30), (0.30, 0.18), (0.46, 0.14), (0.48, 0.26),
                                      (0.44, 0.40), (0.38, 0.36), (0.34, 0.50), (0.26, 0.44), (0.20, 0.60),
                                      (0.12, 0.56), (0.08, 0.70)]]), fill=255) for sx in (-1, 1)])
    body = poly([(0.42, 0.98), (0.40, 0.66), (0.44, 0.54), (0.56, 0.54), (0.60, 0.66), (0.58, 0.98)])
    m = sh(lambda d: demon_mask(d, 0.5, 0.48, 0.62))
    both = add(w, m, body)
    K.glow(c, both, (255, 60, 90, 255), 10, 1.6)
    K.fill(c, K.soften(both), lin((60, 16, 60), (12, 2, 14)))
    bones = sh(lambda d: [brush(d, [(0.5 + sx * 0.08, 0.50), (0.5 + sx * 0.46, 0.15)], 0.014) for sx in (-1, 1)] +
               [brush(d, [(0.5 + sx * 0.30, 0.19), (0.5 + sx * a, b)], 0.01) for sx in (-1, 1)
                for a, b in ((0.36, 0.42), (0.24, 0.50), (0.12, 0.62))])
    K.fill(c, scale(K.soften(inter(bones, w), 1.5), 0.8), (150, 40, 90, 255))
    red_eyes(c, 0.5, 0.44, 0.62, (255, 80, 40))
    rnd = random.Random(2)
    shards_ = sh(lambda d: [d.polygon(pts(burst_pts(x, y, 3, 0.035, 0.015, rot0=rnd.uniform(0, 360))), fill=255)
                            for x, y in ((0.22, 0.82), (0.32, 0.90), (0.68, 0.88), (0.78, 0.80))])
    lit(c, shards_, (255, 80, 80), (255, 200, 190), 8, 1.5)
    return K.finish(c)


def night_terror():
    """A shrieking wraith reaching out of the dark."""
    c = dark_bg(0.5, 0.42)
    body = [(0.30, 0.38)]
    for i in range(1, 9):
        t = i / 8
        body.append((0.30 - 0.06 * t + 0.02 * math.sin(t * 3), 0.38 + 0.44 * t))
    for i in range(41):                                    # a ragged, flame-like hem
        t = i / 40
        x = 0.24 + 0.54 * t
        body.append((x, 0.86 + 0.06 * math.sin(t * math.pi * 5) - 0.04 * t))
    for i in range(8, 0, -1):
        t = i / 8
        body.append((0.70 + 0.08 * t - 0.02 * math.sin(t * 3), 0.38 + 0.40 * t))
    gm = add(circ(0.5, 0.36, 0.21), poly(body),
             sh(lambda d: [d.polygon(pts(taper([(0.32, 0.50), (0.20, 0.44), (0.08, 0.32)], 0.10, 0.02)), fill=255),
                           d.polygon(pts(taper([(0.68, 0.50), (0.80, 0.44), (0.92, 0.32)], 0.10, 0.02)), fill=255)]))
    gm = K.soften(gm, 3).point(lambda v: 255 if v > 120 else int(v * 2.1))
    K.glow(c, gm, (190, 120, 255, 255), 24, 1.6)
    K.fill(c, K.soften(gm), lin((246, 236, 255), (130, 80, 200)))
    sd = minus(gm, ImageChops.offset(gm, -int(0.04 * W), -int(0.03 * W)))
    K.fill(c, scale(K.soften(sd, 5), 0.45), (60, 20, 110, 255))
    eyes = sh(lambda d: [d.polygon(pts([(0.5 + sx * 0.03, 0.36), (0.5 + sx * 0.14, 0.28), (0.5 + sx * 0.13, 0.38),
                                        (0.5 + sx * 0.06, 0.40)]), fill=255) for sx in (-1, 1)])
    K.fill(c, K.soften(eyes), (20, 0, 30, 255))
    pup = sh(lambda d: [d.ellipse(pts([(0.5 + sx * 0.095 - 0.022, 0.335), (0.5 + sx * 0.095 + 0.022, 0.375)]),
                                  fill=255) for sx in (-1, 1)])
    lit(c, pup, (255, 60, 80), (255, 220, 200), 8, 2.0)
    mouth = sh(lambda d: d.ellipse(pts([(0.43, 0.46), (0.57, 0.66)]), fill=255))
    K.fill(c, K.soften(mouth, 1.5), (24, 0, 34, 255))
    sound_waves(c, 0.5, 0.56, (0.40,), 200, 240, 0.03, (230, 200, 255), (180, 100, 255), 0.7)
    sound_waves(c, 0.5, 0.56, (0.40,), -60, -20, 0.03, (230, 200, 255), (180, 100, 255), 0.7)
    return K.finish(c)


def blindside():
    c = bg((60, 30, 110), (4, 0, 14), cx=0.7, cy=0.6)
    shadowfig = sh(lambda d: K.figure(d, 0.30, 0.52, 0.8))
    K.fill(c, scale(K.soften(shadowfig, 4), 0.7), (150, 80, 220, 255))
    slash = sh(lambda d: d.polygon(pts(swell(bow(0.30, 0.12, 0.86, 0.80, -0.12), 0.10)), fill=255))
    lit(c, slash, (220, 120, 255), lin((255, 240, 255), (200, 140, 255), 45), 16, 1.5)
    dg = sh(lambda d: GB.draw_dagger(d, 0.60, 0.42, 0.62, 140))
    lit(c, dg, (240, 200, 255), lin((255, 255, 255), (150, 140, 180)), 10, 1.2, sh=True)
    red_eyes(c, 0.30, 0.20, 0.5)
    return K.finish(c)


def somnolence():
    c = dark_bg(0.5, 0.3)
    orb = circ(0.5, 0.40, 0.22)
    K.glow(c, orb, (170, 70, 255, 255), 30, 1.6)
    K.fill(c, K.soften(orb), rad((200, 140, 255), (40, 10, 70), 0.44, 0.34, 0.24))
    ch = sh(lambda d: [brush(d, [(0.30, y), (0.5, y + 0.08), (0.70, y)], 0.045) for y in (0.66, 0.76)])
    lit(c, ch, (200, 120, 255), lin((240, 220, 255), (170, 110, 230)), 10, 1.3)
    ground = poly([(0.1, 0.92), (0.9, 0.92), (0.9, 0.96), (0.1, 0.96)])
    K.fill(c, K.soften(ground, 3), (200, 150, 255, 180))
    ztext(c, [(0.76, 0.22, 0.10), (0.86, 0.10, 0.06)], (240, 220, 255), (190, 120, 255))
    return K.finish(c)


def nightmare():
    c = dark_bg(0.5, 0.5)
    rnd = random.Random(3)
    tend = sh(lambda d: [d.polygon(pts(taper([(0.5 + math.cos(a) * (0.16 + t * 0.003) + 0.04 * math.sin(t * 0.2),
                                                0.52 + math.sin(a) * (0.16 + t * 0.003))
                                               for t in range(0, 101, 5)], 0.06, 0.005)), fill=255)
                         for a in [math.pi * 2 * k / 9 + rnd.uniform(-0.2, 0.2) for k in range(9)]])
    lit(c, tend, (200, 60, 200), lin((140, 40, 160), (40, 6, 60)), 12, 1.2)
    eye = sh(lambda d: GC.eye_shape(d, 0.5, 0.52, 0.24, 0.12))
    lit(c, eye, (255, 80, 160), lin((220, 180, 230), (130, 80, 150)), 16, 1.3, sh=True)
    lid = sh(lambda d: d.polygon(pts(swell(arc(0.5, 0.40, 0.25, 30, 150, 30), 0.05)), fill=255))
    K.fill(c, K.soften(lid), (40, 10, 50, 255))
    lash = sh(lambda d: [brush(d, [(0.5 + math.cos(math.radians(a)) * 0.25, 0.40 + math.sin(math.radians(a)) * 0.25),
                                   (0.5 + math.cos(math.radians(a)) * 0.32, 0.40 + math.sin(math.radians(a)) * 0.32)],
                               0.02) for a in (50, 75, 105, 130)])
    K.fill(c, K.soften(lash), (40, 10, 50, 255))
    ztext(c, [(0.76, 0.20, 0.10), (0.86, 0.09, 0.06)], (255, 210, 240), (255, 80, 180))
    return K.finish(c)


def ultimate_terror():
    c = bg((120, 20, 70), (10, 0, 10), cy=0.5)
    sound_waves(c, 0.5, 0.5, (0.34, 0.42), 0, 360, 0.03, (255, 160, 220), (220, 40, 140), 0.7)
    sk = sh(lambda d: GB.skull(d, 0.5, 0.48, 0.95))
    lit(c, sk, (255, 80, 160), lin((255, 240, 240), (190, 160, 180)), 20, 1.5, sh=True)
    eyes = sh(lambda d: [d.ellipse(pts([(0.37, 0.43), (0.45, 0.51)]), fill=255),
                         d.ellipse(pts([(0.55, 0.43), (0.63, 0.51)]), fill=255)])
    lit(c, eyes, (255, 40, 80), (255, 120, 140), 6, 1.8)
    ar = sh(lambda d: [down_arrow(d, x, 0.84, 0.26) for x in (0.24, 0.5, 0.76)])
    lit(c, ar, (255, 90, 90), lin((255, 170, 160), (200, 40, 50)), 6, 1.2, sh=True)
    return K.finish(c)


def noctoshield():
    c = dark_bg(0.5, 0.45)
    rays(c, 0.5, 0.5, 12, (200, 150, 255), alpha=50)
    s_ = shield_shape(0.5, 0.16, 0.28, 0.70)
    lit(c, s_, (190, 110, 255), lin((110, 60, 160), (30, 10, 50)), 20, 1.5, sh=True)
    rim = minus(s_, shield_shape(0.5, 0.20, 0.24, 0.64))
    lit(c, rim, (220, 170, 255), lin((240, 220, 255), (150, 100, 220)), 8, 1.2)
    cres = minus(circ(0.5, 0.46, 0.14), circ(0.56, 0.41, 0.13))
    lit(c, cres, (230, 200, 255), (250, 245, 255), 12, 1.5)
    sparkles(c, [(0.62, 0.60, 0.05)], glowc=(220, 180, 255))
    return K.finish(c)


def dream_shroud():
    c = bg((90, 60, 170), (6, 4, 26), cy=0.4)
    veil = poly([(0.16, 0.20)] + [(0.16 + 0.68 * t, 0.16 - 0.06 * math.sin(math.pi * t)) for t in
                                  (i / 10 for i in range(11))] +
                [(0.86, 0.82), (0.76, 0.74), (0.66, 0.86), (0.56, 0.76), (0.46, 0.88), (0.36, 0.76), (0.26, 0.86),
                 (0.14, 0.80)])
    K.glow(c, veil, (190, 150, 255, 255), 20, 1.2)
    K.fill(c, scale(K.soften(veil, 2), 0.75), lin((210, 190, 255), (110, 70, 200)))
    folds = sh(lambda d: [brush(d, [(x, 0.22), (x + 0.03, 0.50), (x - 0.01, 0.78)], 0.02) for x in (0.32, 0.5, 0.68)])
    K.fill(c, scale(K.soften(folds, 3), 0.45), (60, 30, 120, 255))
    st = sh(lambda d: [K.sparkle(d, x, y, r) for x, y, r in ((0.38, 0.42, 0.06), (0.62, 0.36, 0.05), (0.52, 0.60, 0.07),
                                                           (0.30, 0.66, 0.04))])
    lit(c, st, (255, 240, 200), (255, 255, 240), 8, 1.4)
    cres = minus(circ(0.5, 0.12, 0.06), circ(0.53, 0.10, 0.055))
    lit(c, cres, (255, 240, 200), (255, 250, 230), 8, 1.4)
    return K.finish(c)


def pavor_nocturnus():
    c = dark_bg(0.5, 0.6)
    hand = sh(lambda d: [d.polygon(pts(taper([(0.5 + dx * 0.4, 0.96), (0.5 + dx * 0.3, 0.6), (0.5 + dx * 0.55, 0.3),
                                              (0.5 + dx * 0.8, 0.18)], 0.07, 0.01)), fill=255)
                         for dx in (-0.5, -0.2, 0.15, 0.45)] + [d.ellipse(pts([(0.30, 0.66), (0.70, 1.02)]), fill=255)])
    lit(c, hand, (190, 80, 255), lin((60, 20, 80), (14, 2, 20)), 14, 1.5)
    rnd = random.Random(7)
    frag = sh(lambda d: [d.polygon(pts(burst_pts(x, y, 3, 0.04, 0.018, rot0=rnd.uniform(0, 360))), fill=255)
                         for x, y in ((0.30, 0.20), (0.50, 0.12), (0.70, 0.22), (0.42, 0.30), (0.62, 0.34))])
    lit(c, frag, (160, 255, 200), (230, 255, 236), 8, 1.3)
    red_eyes(c, 0.5, 0.50, 0.6)
    return K.finish(c)


# ---- Atomos, Odin, Alexander ------------------------------------------------------------------------------------------
def clock_face(c, cx, cy, r, glowc=(140, 255, 220), paint=None, hands=(300, 60)):
    face = circ(cx, cy, r)
    lit(c, face, glowc, paint or rad((250, 246, 226), (180, 160, 120), cx - r * 0.3, cy - r * 0.3, r * 1.4), 18, 1.3,
        sh=True)
    rim = ring(cx, cy, r, 0.03)
    K.fill(c, K.soften(rim), lin(*GOLD))
    ticks = sh(lambda d: [brush(d, [(cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78),
                                    (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9)], 0.018)
                          for a in [math.pi * 2 * k / 12 for k in range(12)]])
    K.fill(c, K.soften(ticks), (60, 40, 30, 255))
    hd = sh(lambda d: [brush(d, [(cx, cy), (cx + math.cos(math.radians(hands[0] - 90)) * r * 0.5,
                                            cy + math.sin(math.radians(hands[0] - 90)) * r * 0.5)], 0.035),
                       brush(d, [(cx, cy), (cx + math.cos(math.radians(hands[1] - 90)) * r * 0.72,
                                            cy + math.sin(math.radians(hands[1] - 90)) * r * 0.72)], 0.025)])
    K.fill(c, K.soften(hd), (40, 26, 20, 255))


def deconstruction():
    c = bg((40, 140, 140), (2, 20, 24), cy=0.5)
    clock_face(c, 0.44, 0.54, 0.30)
    cut = poly([(0.56, 0.0), (1, 0), (1, 1), (0.66, 1), (0.60, 0.70), (0.66, 0.56), (0.58, 0.40), (0.64, 0.24)])
    K.fill(c, K.soften(inter(cut, circ(0.44, 0.54, 0.34)), 2), (6, 30, 34, 255))
    gears = sh(lambda d: [GD.gear(d, x, y, r, r * 0.75, n, r * 0.35) for x, y, r, n in ((0.78, 0.30, 0.10, 8),
                                                                                       (0.82, 0.62, 0.07, 7),
                                                                                       (0.70, 0.84, 0.05, 6))])
    lit(c, gears, (140, 255, 220), lin(*GOLD), 10, 1.3, sh=True)
    motes(c, 4, 18, (0.6, 0.1, 0.95, 0.95), (0.005, 0.012), (200, 255, 240), (120, 255, 220))
    return K.finish(c)


def chronoshift():
    c = bg((60, 120, 180), (4, 12, 34), cy=0.5)
    sp = sh(lambda d: d.polygon(pts(taper([(0.5 + math.cos(math.radians(-60 - t * 3.4)) * (0.42 - t * 0.0006),
                                            0.5 + math.sin(math.radians(-60 - t * 3.4)) * (0.42 - t * 0.0006))
                                           for t in range(0, 101, 2)], 0.01, 0.06)), fill=255))
    lit(c, sp, (140, 220, 255), lin((236, 250, 255), (120, 190, 240)), 12, 1.3)
    tip = sh(lambda d: GD.arrowhead(d, 0.5 + math.cos(math.radians(-400)) * 0.36, 0.5 + math.sin(math.radians(-400)) * 0.36,
                                    -400 - 90, 0.12))
    lit(c, tip, (140, 220, 255), (236, 250, 255), 10, 1.3)
    clock_face(c, 0.5, 0.5, 0.25, (140, 220, 255), hands=(240, 330))
    return K.finish(c)


def zantetsuken():
    """Odin's blade: one stroke that cuts the moon in two."""
    c = bg((80, 40, 96), (4, 2, 10), cy=0.40)
    x0, y0, x1, y1 = 0.08, 0.94, 0.90, 0.12
    upper = poly([(0.0, 0.0), (1.0, 0.0), (1.0, y0 + (y1 - y0) * (1.0 - x0) / (x1 - x0)),
                  (0.0, y0 - (y1 - y0) * x0 / (x1 - x0))])
    m = moon(c, 0.52, 0.42, 0.30, glowc=(210, 214, 250), gr=40, gs=1.5)
    # the upper half of the moon slides up-left along the cut
    off = -int(0.035 * W)
    K.fill(c, K.soften(inter(m, upper)), (0, 0, 0, 255))
    c2 = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    moon(c2, 0.52, 0.42, 0.30, gr=1, gs=0.01)
    c2 = ImageChops.offset(c2, off, off)
    piece = inter(ImageChops.offset(m, off, off), ImageChops.offset(upper, off, off))
    K.fill(c, K.soften(piece), c2)
    slash = sh(lambda d: d.polygon(pts(swell(bow(0.0, 1.02, 1.0, 0.04, 0.0), 0.07)), fill=255))
    lit(c, slash, (255, 110, 140), (255, 255, 255), 18, 1.8)
    blade = sh(lambda d: GC.katana(d, x0 + 0.02, y0 + 0.06, x1, y1, curve=0.05, part='blade'))
    blade = blade.filter(ImageFilter.MaxFilter(5))
    hilt = sh(lambda d: GC.katana(d, x0 + 0.02, y0 + 0.06, x1, y1, curve=0.05, part='hilt'))
    K.shadow(c, add(blade, hilt), 5, 8, 6, 200)
    lit(c, blade, (255, 80, 110), lin((255, 255, 255), (150, 160, 196), 0), 14, 1.5)
    edge = minus(blade, ImageChops.offset(blade, -int(0.012 * W), -int(0.012 * W)))
    K.fill(c, scale(K.soften(edge, 1.5), 0.9), (255, 255, 255, 255))
    hamon = minus(blade, ImageChops.offset(blade, int(0.016 * W), int(0.016 * W)))
    K.fill(c, scale(K.soften(hamon, 2), 0.5), (90, 100, 140, 255))
    K.fill(c, K.soften(hilt), lin((170, 30, 44), (50, 8, 12)))
    motes(c, 9, 10, (0.05, 0.55, 0.95, 0.95), (0.006, 0.012), (220, 30, 50), (255, 40, 60))
    return K.finish(c)


def perfect_defense():
    c = bg((255, 230, 160), (110, 70, 20), cy=0.45, r=0.7)
    rays(c, 0.5, 0.48, 24, (255, 255, 240), width=0.05, length=0.9, alpha=140)
    hx = poly(hexagon(0.5, 0.50, 0.42))
    K.fill(c, scale(K.soften(hx, 6), 0.3), (255, 255, 255, 255))
    hxr = sh(lambda d: d.polygon(pts(hexagon(0.5, 0.50, 0.42)), outline=255, width=int(0.02 * W)))
    lit(c, hxr, (255, 250, 210), (255, 255, 240), 10, 1.4)
    s_ = shield_shape(0.5, 0.20, 0.25, 0.64)
    lit(c, s_, (255, 240, 180), lin((255, 250, 220), (200, 150, 60)), 20, 1.5, sh=True)
    inner = shield_shape(0.5, 0.25, 0.19, 0.54)
    K.fill(c, K.soften(inner), lin((120, 150, 230), (40, 50, 140)))
    cr = cross_m(0.5, 0.48, 0.62, 0.07)
    lit(c, cr, (255, 240, 180), lin(*GOLD), 8, 1.3)
    sparkles(c, [(0.5, 0.48, 0.09), (0.80, 0.20, 0.06), (0.20, 0.20, 0.06)], glowc=(255, 250, 200))
    return K.finish(c)


# ---- Siren: sea-green and coral ---------------------------------------------------------------------------------------
def siren_bg(cx=0.5, cy=0.45, light=(60, 170, 160), dark=(4, 26, 34)):
    return bg(light, dark, cx=cx, cy=cy)


CORAL = ((255, 220, 210), (240, 110, 120))


def harp(d, cx, cy, s, strings=True, fillv=255):
    """A clarsach: curved neck, pillar and soundbox (frame only, strings separate)."""
    def q(x, y):
        return (cx + x * s, cy + y * s)
    neck = [q(-0.30, -0.30), q(-0.10, -0.40), q(0.10, -0.28), q(0.28, -0.34), q(0.32, -0.28)]
    d.polygon(pts(taper(neck, 0.07 * s, 0.05 * s)), fill=fillv)
    d.polygon(pts(taper([q(-0.30, -0.32), q(-0.32, 0.0), q(-0.26, 0.40)], 0.08 * s, 0.06 * s)), fill=fillv)
    d.polygon(pts(taper([q(0.30, -0.30), q(0.10, 0.06), q(-0.24, 0.42)], 0.09 * s, 0.11 * s)), fill=fillv)


def clarsach_call():
    c = bg((90, 220, 200), (10, 40, 70), cy=0.5, r=0.7)
    rays(c, 0.5, 0.5, 20, (255, 250, 230), width=0.05, alpha=120)
    st = sh(lambda d: [brush(d, [(x, -0.30 + (x + 0.30) * 0.05), (x, 0.40 - (x + 0.30) * 0.85)], 0.006)
                       for x in [-0.22 + 0.075 * k for k in range(7)]])
    strings_ = sh(lambda d: [brush(d, [(0.5 + x * 1.0, 0.5 - 0.31 - 0.04 * math.sin((x + 0.3) * 6)),
                                       (0.5 + x * 1.0, 0.5 + 0.40 - (x + 0.30) * 0.86)], 0.011)
                             for x in [-0.22 + 0.07 * k for k in range(7)]])
    lit(c, strings_, (255, 240, 200), (255, 255, 236), 8, 1.5)
    h = sh(lambda d: harp(d, 0.5, 0.5, 1.0))
    lit(c, h, (255, 220, 140), lin(*GOLD), 18, 1.5, sh=True)
    notes = sh(lambda d: [GB.note(d, 0.80, 0.30, 0.34, 1, 15), GB.note(d, 0.20, 0.82, 0.28, 2, -10)])
    lit(c, notes, (255, 160, 170), lin(*CORAL), 10, 1.4)
    sparkles(c, [(0.26, 0.20, 0.07), (0.78, 0.74, 0.05)], glowc=(255, 230, 220))
    return K.finish(c)


def welt():
    c = siren_bg(0.5, 0.5)
    whip = [(0.10 + 0.8 * t, 0.86 - 0.5 * t - 0.3 * math.sin(math.pi * t) + 0.08 * math.sin(math.pi * 3 * t))
            for t in (i / 40 for i in range(41))]
    w = poly(taper(whip, 0.05, 0.012))
    lit(c, w, (255, 180, 170), lin((255, 230, 200), (180, 100, 70)), 12, 1.3, sh=True)
    grip = poly(taper(whip[:6], 0.07, 0.06))
    K.fill(c, K.soften(grip), (90, 40, 30, 255))
    crack = poly(burst_pts(0.86, 0.30, 7, 0.13, 0.05))
    lit(c, crack, (255, 120, 130), (255, 236, 230), 14, 1.6)
    welts = sh(lambda d: [d.polygon(pts(swell(bow(0.56 + k * 0.08, 0.86 - k * 0.02, 0.74 + k * 0.08, 0.58 - k * 0.02, 0.0), 0.035)), fill=255) for k in range(3)])
    lit(c, welts, (255, 60, 80), lin((255, 160, 160), (220, 40, 60)), 8, 1.4)
    return K.finish(c)


def roundhouse():
    c = siren_bg(0.5, 0.5, (70, 160, 180), (4, 20, 34))
    sw = sh(lambda d: d.polygon(pts(swell(arc(0.5, 0.52, 0.32, 150, 470, 50), 0.14)), fill=255))
    lit(c, sw, (200, 255, 240), lin((255, 255, 255), (150, 230, 220)), 16, 1.3)
    inner = sh(lambda d: d.polygon(pts(swell(arc(0.5, 0.52, 0.22, 200, 450, 40), 0.05)), fill=255))
    K.fill(c, scale(K.soften(inner, 2), 0.6), (220, 255, 245, 255))
    foot = poly([(0.70, 0.12), (0.82, 0.10), (0.92, 0.18), (0.94, 0.26), (0.84, 0.26), (0.72, 0.22)])
    lit(c, foot, (255, 200, 190), lin(*CORAL), 10, 1.3, sh=True)
    st = poly(burst_pts(0.92, 0.34, 6, 0.09, 0.035))
    lit(c, st, (255, 240, 200), (255, 255, 240), 8, 1.4)
    return K.finish(c)


def sonic_buffet():
    c = siren_bg(0.3, 0.5, (90, 150, 190), (6, 16, 40))
    sound_waves(c, 0.12, 0.50, (0.20, 0.32, 0.44, 0.56), -40, 40, 0.07, (240, 255, 255), (120, 230, 255))
    st = poly(burst_pts(0.80, 0.50, 9, 0.16, 0.07, seed=3))
    lit(c, st, (255, 160, 170), lin(*CORAL), 14, 1.5)
    motes(c, 3, 12, (0.5, 0.2, 0.95, 0.8), (0.006, 0.012), (255, 230, 230), (255, 140, 160))
    return K.finish(c)


def hysteric_assault():
    c = bg((210, 60, 110), (30, 4, 20), cy=0.5)
    jag = sh(lambda d: [brush(d, zigzag(0.5, 0.5, 0.5 + math.cos(a) * 0.44, 0.5 + math.sin(a) * 0.44, 4, 0.04, k),
                              0.035, 0.01) for k, a in enumerate([math.pi * 2 * i / 10 for i in range(10)])])
    lit(c, jag, (255, 150, 200), (255, 230, 240), 10, 1.4)
    slashes(c, [(0.20, 0.24, 0.80, 0.76, 0.05), (0.80, 0.22, 0.24, 0.80, -0.05), (0.50, 0.10, 0.50, 0.90, 0.05)], 0.09,
            (255, 120, 170), lin((255, 255, 255), (255, 180, 210)), 14, 1.5)
    mouth = sh(lambda d: GC.eye_shape(d, 0.5, 0.5, 0.10, 0.07))
    K.fill(c, K.soften(mouth), (40, 0, 20, 255))
    return K.finish(c)


def katabatic_blades():
    c = siren_bg(0.5, 0.2, (90, 190, 170), (4, 26, 30))
    spec = [(0.70, 0.06, 0.20, 0.66, 0.10), (0.90, 0.20, 0.42, 0.86, 0.10), (0.56, 0.0, 0.08, 0.44, 0.08)]
    streaks(c, [(x0 + 0.06, y0 - 0.10, x0 - 0.06, y0 + 0.06) for x0, y0, _, _, _ in spec], (220, 255, 240, 255), 0.02,
            150, 4)
    m = sh(lambda d: [d.polygon(pts(swell(bow(x0, y0, x1, y1, b, 30), 0.09)), fill=255) for x0, y0, x1, y1, b in spec])
    lit(c, m, (180, 255, 230), lin((255, 255, 255), (150, 240, 210), 30), 14, 1.5, sh=True)
    edge = minus(m, ImageChops.offset(m, -8, 6))
    K.fill(c, scale(K.soften(edge, 1.5), 0.8), (40, 120, 110, 255))
    sparkles(c, [(0.22, 0.70, 0.06), (0.46, 0.90, 0.05)], glowc=(255, 200, 200))
    return K.finish(c)


def lunatic_voice():
    c = siren_bg(0.5, 0.5, (130, 90, 170), (12, 6, 30))
    cres = minus(circ(0.34, 0.46, 0.22), circ(0.42, 0.40, 0.20))
    lit(c, cres, (255, 210, 230), lin((255, 250, 250), (240, 180, 210), 120), 16, 1.5)
    sound_waves(c, 0.36, 0.48, (0.24, 0.34), -60, 60, 0.05, (255, 220, 240), (255, 130, 190))
    n = sh(lambda d: GB.note(d, 0.70, 0.66, 0.40, 1, 10))
    lit(c, n, (255, 140, 190), lin(*CORAL), 10, 1.3, sh=True)
    bar = sh(lambda d: brush(d, [(0.56, 0.78), (0.90, 0.30)], 0.04))
    lit(c, bar, (255, 60, 80), (255, 90, 100), 8, 1.3)
    return K.finish(c)


def chinook():
    c = siren_bg(0.5, 0.5, (190, 150, 90), (30, 20, 10))
    gusts(c, [(0.5, 0.52, 0.34, 190, 330, 0.07), (0.5, 0.52, 0.24, 10, 160, 0.06), (0.5, 0.52, 0.40, 20, 100, 0.04)],
          (255, 250, 220), (255, 200, 120))
    blade = sh(lambda d: GD.sword(d, 0.5, 0.12, 0.90, 0.05))
    lit(c, blade, (200, 255, 220), lin((255, 255, 255), (170, 210, 200), 0), 12, 1.4, sh=True)
    motes(c, 6, 14, (0.15, 0.15, 0.85, 0.85), (0.005, 0.012), (255, 240, 200), (255, 190, 100))
    return K.finish(c)


def bitter_elegy():
    c = siren_bg(0.5, 0.4, (70, 90, 150), (6, 8, 26))
    n = sh(lambda d: GB.note(d, 0.42, 0.66, 0.85, 1, -12))
    crack = sh(lambda d: brush(d, zigzag(0.38, 0.12, 0.52, 0.90, 5, 0.04, 3), 0.025))
    n = minus(n, crack)
    lit(c, n, (180, 200, 255), lin((236, 240, 255), (130, 150, 210)), 14, 1.3, sh=True)
    tears = sh(lambda d: [droplet(d, x, y, 0.03) for x, y in ((0.70, 0.40), (0.76, 0.60), (0.66, 0.78))])
    lit(c, tears, (140, 200, 255), lin((236, 250, 255), (90, 160, 240)), 8, 1.2)
    ar = sh(lambda d: down_arrow(d, 0.80, 0.22, 0.30))
    lit(c, ar, (255, 110, 110), lin((255, 180, 170), (210, 50, 60)), 6, 1.2, sh=True)
    return K.finish(c)


def winds_blessing():
    c = siren_bg(0.5, 0.45, (90, 200, 180), (4, 30, 34))
    rays(c, 0.5, 0.5, 12, (230, 255, 245), alpha=60)
    gusts(c, [(0.5, 0.52, 0.36, 150, 300, 0.05), (0.5, 0.52, 0.36, 330, 480, 0.05)])
    fe = sh(lambda d: leafm(d, 0.36, 0.78, -1.05, 0.62, 0.10))
    lit(c, fe, (230, 255, 240), lin((255, 255, 255), (170, 230, 220)), 14, 1.4, sh=True)
    quill = sh(lambda d: brush(d, [(0.36, 0.80), (0.62, 0.30)], 0.015))
    K.fill(c, K.soften(quill), (120, 160, 160, 255))
    sparkles(c, [(0.72, 0.26, 0.08), (0.26, 0.40, 0.05)], glowc=(255, 220, 220))
    return K.finish(c)


def tornado_ii():
    c = siren_bg(0.5, 0.5, (70, 180, 160), (4, 26, 26))
    funnel = poly([(0.18, 0.10), (0.82, 0.10), (0.56, 0.92), (0.44, 0.92)])
    K.fill(c, scale(funnel.filter(ImageFilter.GaussianBlur(10)), 0.8), (10, 60, 50, 255))
    tornado(c, 0.5, 0.14, 0.88, 0.32, 0.05, color=(236, 255, 250), glowc=(140, 255, 220), bands=8)
    motes(c, 5, 12, (0.1, 0.1, 0.9, 0.8), (0.006, 0.014), (255, 220, 220), (255, 140, 160))
    return K.finish(c)


# ---- The wyvern's breaths (DRG) ---------------------------------------------------------------------------------------
WYVERN = [(0.56, 0.02), (0.44, -0.04), (0.30, -0.06), (0.16, -0.14), (0.04, -0.16), (-0.12, -0.26), (-0.46, -0.34),
          (-0.20, -0.12), (-0.40, -0.14), (-0.22, -0.02), (-0.26, 0.14), (-0.34, 0.50), (-0.10, 0.50), (-0.08, 0.26),
          (0.02, 0.18), (0.18, 0.24), (0.46, 0.26), (0.42, 0.18), (0.18, 0.10), (0.54, 0.08)]


def wyvern_head(c, cx, cy, s, ang=0, glowc=(160, 220, 255)):
    m = sh(lambda d: d.polygon(xf(WYVERN, cx, cy, s, ang), fill=255))
    lit(c, m, glowc, lin((200, 230, 250), (60, 100, 160)), 12, 1.3, sh=True)
    ridge = sh(lambda d: [d.polygon(xf([(x, -0.10 + (x + 0.2) * 0.1), (x - 0.05, -0.20 + (x + 0.2) * 0.1),
                                        (x - 0.07, -0.08 + (x + 0.2) * 0.1)], cx, cy, s, ang), fill=255)
                          for x in (-0.24, -0.30)])
    K.fill(c, K.soften(ridge), (40, 70, 120, 255))
    ex, ey = at(0.10, -0.06, cx, cy, s, ang)
    lit(c, circ(ex, ey, 0.03 * s / 0.5), (255, 80, 40), (255, 120, 60), 4, 1.5)
    return m


def breath_cone(cx, cy, ang, length, spread):
    a = math.radians(ang)
    pts_ = [(cx, cy)]
    for k in range(21):
        t = -spread + 2 * spread * k / 20
        r = length * (1 - 0.06 * math.cos(k))
        pts_.append((cx + math.cos(a + math.radians(t)) * r, cy + math.sin(a + math.radians(t)) * r))
    return poly(pts_)


def healing_breath(tier):
    def paint():
        c = bg((60, 160, 150), (4, 24, 30), cx=0.6, cy=0.5)
        cone = breath_cone(0.40, 0.42, 25, 0.66, 22 + tier * 3)
        K.glow(c, cone, (140, 255, 180, 255), 22, 1.2)
        K.fill(c, K.soften(cone, 8), lin((160, 255, 190, 60), (230, 255, 236, 255), 205))
        motes(c, tier, 10 + tier * 4, (0.45, 0.4, 0.95, 0.95), (0.006, 0.016), (230, 255, 236), (150, 255, 180))
        wyvern_head(c, 0.24, 0.40, 0.48, 25)
        cr = cross_m(0.70, 0.66, 0.52)
        lit(c, cr, (140, 255, 170), (240, 255, 240), 12, 1.5)
        gems = sh(lambda d: [d.polygon(pts([(x, 0.86 - 0.035), (x + 0.03, 0.86), (x, 0.86 + 0.035), (x - 0.03, 0.86)]),
                                       fill=255) for x in [0.5 - 0.045 * (tier - 1) + 0.09 * k for k in range(tier)]])
        lit(c, gems, (140, 255, 170), lin((255, 255, 240), (150, 240, 170)), 6, 1.5)
        return K.finish(c)
    return paint


def wyvern_remove():
    """Purification: the wyvern's breath shattering an ailment (painted green, poison; variants recolour it)."""
    c = bg((60, 150, 80), (4, 24, 10), cx=0.65, cy=0.5)
    cone = breath_cone(0.36, 0.44, 15, 0.56, 22)
    K.glow(c, cone, (200, 255, 210, 255), 20, 1.1)
    K.fill(c, K.soften(cone, 8), lin((200, 255, 210, 40), (240, 255, 240, 255), 195))
    orb = circ(0.74, 0.54, 0.16)
    K.glow(c, orb, (120, 255, 100, 255), 20, 1.4)
    K.fill(c, K.soften(orb), rad((200, 255, 160), (40, 140, 30), 0.70, 0.50, 0.18))
    crack = sh(lambda d: [brush(d, zigzag(0.74, 0.40, 0.72, 0.70, 4, 0.04, 2), 0.022),
                          brush(d, [(0.73, 0.55), (0.86, 0.50)], 0.016)])
    K.fill(c, K.soften(inter(crack, orb)), (250, 255, 240, 255))
    frag = sh(lambda d: [d.polygon(pts(burst_pts(x, y, 3, 0.035, 0.015, rot0=k * 40)), fill=255)
                         for k, (x, y) in enumerate(((0.92, 0.36), (0.94, 0.66), (0.80, 0.80), (0.84, 0.28)))])
    lit(c, frag, (120, 255, 100), (210, 255, 180), 6, 1.3)
    wyvern_head(c, 0.20, 0.40, 0.44, 15, glowc=(200, 255, 210))
    return K.finish(c)


def wyvern_breath():
    """An elemental breath (painted as fire, Flame Breath; the other breaths turn its hue)."""
    c = bg((200, 50, 30), (30, 4, 4), cx=0.65, cy=0.5)
    cone = breath_cone(0.38, 0.40, 28, 0.74, 26)
    K.glow(c, cone, (255, 110, 30, 255), 26, 1.4)
    K.fill(c, K.soften(cone, 6), lin((255, 120, 30, 120), (255, 220, 120, 255), 208))
    inner = breath_cone(0.38, 0.40, 28, 0.56, 13)
    K.fill(c, K.soften(inner, 8), lin((255, 255, 220, 80), (255, 250, 210, 255), 208))
    motes(c, 6, 16, (0.45, 0.35, 0.98, 0.98), (0.006, 0.016), (255, 240, 180), (255, 140, 40))
    wyvern_head(c, 0.24, 0.38, 0.50, 28, glowc=(255, 200, 150))
    return K.finish(c)


def super_climb():
    """The wyvern soaring straight up out of the clouds."""
    c = bg((170, 215, 255), (20, 50, 120), cy=0.2, r=0.8)
    trail = poly([(0.44, 1.0), (0.56, 1.0), (0.53, 0.66), (0.5, 0.58), (0.47, 0.66)])
    K.fill(c, scale(trail.filter(ImageFilter.GaussianBlur(10)), 0.8), (255, 255, 255, 255))
    cl = sh(lambda d: [d.ellipse(pts([(x - r, 0.90 - r * 0.5), (x + r, 0.90 + r * 0.5)]), fill=255)
                       for x, r in ((0.2, 0.16), (0.42, 0.18), (0.64, 0.16), (0.84, 0.14))])
    K.fill(c, scale(K.soften(cl, 8), 0.85), (230, 242, 255, 255))
    w = sh(lambda d: GC.wyvern(d, 0.5, 0.53, 0.92))
    lit(c, w, (240, 250, 255), lin((70, 100, 160), (20, 30, 70)), 12, 1.6, sh=True)
    eyes = sh(lambda d: [d.ellipse(pts([(0.465, 0.285), (0.488, 0.305)]), fill=255),
                         d.ellipse(pts([(0.512, 0.285), (0.535, 0.305)]), fill=255)])
    K.fill(c, K.soften(eyes, 0.8), (230, 60, 30, 255))
    ar = sh(lambda d: up_arrow(d, 0.5, 0.115, 0.38))
    K.fill(c, K.soften(ar.filter(ImageFilter.MaxFilter(7)), 1.5), (60, 30, 10, 255))
    lit(c, ar, (255, 240, 170), lin(*GOLD), 12, 1.8, sh=True)
    return K.finish(c)


# ---- The elemental spirits' spells (Fire II .. Thunder IV, cast by the avatar of that element) ------------------------
SPIRIT = {  # bg light, bg dark, glow, glyph light, glyph dark
    'Fire': ((210, 70, 30), (34, 4, 4), (255, 120, 40), (255, 236, 160), (240, 90, 30)),
    'Stone': ((180, 130, 60), (30, 18, 6), (255, 190, 100), (240, 210, 160), (130, 90, 50)),
    'Water': ((40, 120, 210), (2, 10, 40), (120, 200, 255), (236, 250, 255), (60, 140, 230)),
    'Aero': ((70, 170, 90), (4, 28, 12), (170, 255, 170), (240, 255, 236), (110, 210, 120)),
    'Blizzard': ((110, 180, 240), (6, 20, 56), (190, 240, 255), (255, 255, 255), (130, 196, 240)),
    'Thunder': ((130, 80, 210), (12, 4, 34), (210, 170, 255), (255, 250, 255), (190, 150, 255)),
}


def glyph(elem, cx, cy, s):
    if elem == 'Fire':
        return sh(lambda d: [GD_flame(d, cx, cy + 0.26 * s, 0.17 * s, 0.56 * s, 0.02),
                             GD_flame(d, cx - 0.12 * s, cy + 0.26 * s, 0.07 * s, 0.30 * s, -0.04),
                             GD_flame(d, cx + 0.12 * s, cy + 0.26 * s, 0.07 * s, 0.32 * s, 0.04)])
    if elem == 'Stone':
        return sh(lambda d: rock(d, cx, cy, 0.24 * s, 3, 8))
    if elem == 'Water':
        return sh(lambda d: droplet(d, cx, cy + 0.08 * s, 0.17 * s))
    if elem == 'Aero':
        return sh(lambda d: [d.polygon(pts(taper([(cx + math.cos(math.radians(a0 + t * 3)) * (0.02 + t * 0.0024) * s,
                                                    cy + math.sin(math.radians(a0 + t * 3)) * (0.02 + t * 0.0024) * s)
                                                   for t in range(0, 101, 4)], 0.01, 0.08 * s)), fill=255)
                             for a0 in (0, 180)])
    if elem == 'Blizzard':
        return sh(lambda d: snowflake(d, cx, cy, 0.26 * s, 0.045 * s))
    return sh(lambda d: d.polygon(pts([(cx + x * s, cy + y * s) for x, y in
                                       [(0.06, -0.32), (-0.14, 0.04), (-0.01, 0.04), (-0.08, 0.32), (0.15, -0.06),
                                        (0.02, -0.06), (0.12, -0.32)]]), fill=255))


def spirit_spell(elem, tier):
    light, dark, glowc, g0, g1 = SPIRIT[elem]

    def paint():
        c = bg(light, dark, cy=0.5)
        if tier >= 4:
            rays(c, 0.5, 0.5, 16, glowc, alpha=80)
            # the four-fold circle of the higher tier
            rr = ring(0.5, 0.5, 0.38, 0.02)
            lit(c, rr, glowc, (255, 255, 255), 10, 1.2)
            orbs = sh(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.38 - 0.045, 0.5 + math.sin(a) * 0.38 - 0.045),
                                                (0.5 + math.cos(a) * 0.38 + 0.045, 0.5 + math.sin(a) * 0.38 + 0.045)]),
                                           fill=255) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4,
                                                               7 * math.pi / 4)])
            lit(c, orbs, glowc, rad(g0, g1, 0.5, 0.5, 0.5), 10, 1.5)
        else:
            rr = ring(0.5, 0.5, 0.34, 0.016)
            K.fill(c, scale(K.soften(rr, 2), 0.6), col(g0))
            dots = sh(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.34 - 0.03, 0.5 + math.sin(a) * 0.34 - 0.03),
                                                (0.5 + math.cos(a) * 0.34 + 0.03, 0.5 + math.sin(a) * 0.34 + 0.03)]),
                                           fill=255) for a in (-math.pi / 2, math.pi / 2)])
            lit(c, dots, glowc, col(g0), 8, 1.4)
        orb = circ(0.5, 0.5, 0.25 if tier >= 4 else 0.22)
        K.glow(c, orb, col(glowc), 26, 1.3)
        K.fill(c, scale(K.soften(orb, 4), 0.5), col(dark))
        g = glyph(elem, 0.5, 0.50, 1.15 if tier >= 4 else 1.0)
        if elem == 'Fire':
            K.shadow(c, g, 5, 8, 8, 150)
            fire_paint(c, g)
            core = glyph(elem, 0.5, 0.58, 0.55)
            K.fill(c, K.soften(core, 2), lin((255, 255, 236), (255, 200, 90), 270))
        elif elem == 'Stone':
            stone_paint(c, g, glowc=glowc, gr=16, gs=1.4)
        else:
            lit(c, g, glowc, lin(g0, g1, 90), 16, 1.5, sh=True)
        return K.finish(c)
    return paint


# =====================================================================================================================
ICONS = {
    ('ja', 'Poison Nails'): poison_nails,
    ('ja', 'Meteorite'): meteorite,
    ('ja', 'Searing Light'): searing_light,
    ('ja', 'Holy Mist'): holy_mist,
    ('ja', 'Healing Ruby'): healing_ruby,
    ('ja', 'Healing Ruby II'): healing_ruby_ii,
    ('ja', 'Shining Ruby'): shining_ruby,
    ('ja', 'Glittering Ruby'): glittering_ruby,
    ('ja', 'Soothing Ruby'): soothing_ruby,
    ('ja', 'Pacifying Ruby'): pacifying_ruby,
    ('ja', 'Regal Scratch'): regal_scratch,
    ('ja', 'Regal Gash'): regal_gash,
    ('ja', 'Mewing Lullaby'): mewing_lullaby,
    ('ja', 'Eerie Eye'): eerie_eye,
    ('ja', 'Level ? Holy'): level_holy,
    ('ja', 'Raise II'): raise_ii,
    ('ja', 'Reraise II'): reraise_ii,
    ('ja', "Altana's Favor"): altanas_favor,
    ('ja', 'Moonlit Charge'): moonlit_charge,
    ('ja', 'Crescent Fang'): crescent_fang,
    ('ja', 'Eclipse Bite'): eclipse_bite,
    ('ja', 'Howling Moon'): howling_moon,
    ('ja', 'Lunar Bay'): lunar_bay,
    ('ja', 'Pact: Impact'): impact,
    ('ja', 'Lunar Cry'): lunar_cry,
    ('ja', 'Lunar Roar'): lunar_roar,
    ('ja', 'Ecliptic Growl'): ecliptic_growl,
    ('ja', 'Ecliptic Howl'): ecliptic_howl,
    ('ja', 'Heavenward Howl'): heavenward_howl,
    ('ja', 'Punch'): punch,
    ('ja', 'Burning Strike'): burning_strike,
    ('ja', 'Double Punch'): double_punch,
    ('ja', 'Flaming Crush'): flaming_crush,
    ('ja', 'Meteor Strike'): meteor_strike,
    ('ja', 'Inferno'): inferno,
    ('ja', 'Conflag Strike'): conflag_strike,
    ('ja', 'Crimson Howl'): crimson_howl,
    ('ja', 'Inferno Howl'): inferno_howl,
    ('ja', 'Rock Throw'): rock_throw,
    ('ja', 'Rock Buster'): rock_buster,
    ('ja', 'Megalith Throw'): megalith_throw,
    ('ja', 'Mountain Buster'): mountain_buster,
    ('ja', 'Geocrush'): geocrush,
    ('ja', 'Earthen Fury'): earthen_fury,
    ('ja', 'Crag Throw'): crag_throw,
    ('ja', 'Earthen Ward'): earthen_ward,
    ('ja', 'Earthen Armor'): earthen_armor,
    ('ja', 'Barracuda Dive'): barracuda_dive,
    ('ja', 'Tail Whip'): tail_whip,
    ('ja', 'Spinning Dive'): spinning_dive,
    ('ja', 'Grand Fall'): grand_fall,
    ('ja', 'Tidal Wave'): tidal_wave,
    ('ja', 'Spring Water'): spring_water,
    ('ja', 'Pact: Slowga'): slowga,
    ('ja', 'Tidal Roar'): tidal_roar,
    ('ja', 'Soothing Current'): soothing_current,
    ('ja', 'Claw'): claw,
    ('ja', 'Predator Claws'): predator_claws,
    ('ja', 'Wind Blade'): wind_blade,
    ('ja', 'Aerial Blast'): aerial_blast,
    ('ja', 'Whispering Wind'): whispering_wind,
    ('ja', 'Pact: Hastega'): hastega,
    ('ja', 'Hastega II'): hastega_ii,
    ('ja', 'Aerial Armor'): aerial_armor,
    ('ja', 'Fleet Wind'): fleet_wind,
    ('ja', 'Axe Kick'): axe_kick,
    ('ja', 'Double Slap'): double_slap,
    ('ja', 'Rush'): rush,
    ('ja', 'Heavenly Strike'): heavenly_strike,
    ('ja', 'Diamond Dust'): diamond_dust,
    ('ja', 'Diamond Storm'): diamond_storm,
    ('ja', 'Crystal Blessing'): crystal_blessing,
    ('ja', 'Frost Armor'): frost_armor,
    ('ja', 'Pact: Sleepga'): sleepga_shiva,
    ('ja', 'Shock Strike'): shock_strike,
    ('ja', 'Thunderspark'): thunderspark,
    ('ja', 'Chaotic Strike'): chaotic_strike,
    ('ja', 'Pact: Thunderstorm'): thunderstorm_ramuh,
    ('ja', 'Judgment Bolt'): judgment_bolt,
    ('ja', 'Volt Strike'): volt_strike,
    ('ja', 'Rolling Thunder'): rolling_thunder,
    ('ja', 'Lightning Armor'): lightning_armor,
    ('ja', 'Shock Squall'): shock_squall,
}
ICONS.update({
    ('ja', 'Camisado'): camisado,
    ('ja', 'Nether Blast'): nether_blast,
    ('ja', 'Cacodemonia'): cacodemonia,
    ('ja', 'Ruinous Omen'): ruinous_omen,
    ('ja', 'Night Terror'): night_terror,
    ('ja', 'Blindside'): blindside,
    ('ja', 'Somnolence'): somnolence,
    ('ja', 'Pact: Nightmare'): nightmare,
    ('ja', 'Ultimate Terror'): ultimate_terror,
    ('ja', 'Noctoshield'): noctoshield,
    ('ja', 'Dream Shroud'): dream_shroud,
    ('ja', 'Pavor Nocturnus'): pavor_nocturnus,
    ('ja', 'Deconstruction'): deconstruction,
    ('ja', 'Chronoshift'): chronoshift,
    ('ja', 'Zantetsuken'): zantetsuken,
    ('ja', 'Perfect Defense'): perfect_defense,
    ('ja', 'Clarsach Call'): clarsach_call,
    ('ja', 'Welt'): welt,
    ('ja', 'Roundhouse'): roundhouse,
    ('ja', 'Sonic Buffet'): sonic_buffet,
    ('ja', 'Hysteric Assault'): hysteric_assault,
    ('ja', 'Katabatic Blades'): katabatic_blades,
    ('ja', 'Lunatic Voice'): lunatic_voice,
    ('ja', 'Chinook'): chinook,
    ('ja', 'Bitter Elegy'): bitter_elegy,
    ('ja', "Wind's Blessing"): winds_blessing,
    ('ja', 'Tornado II'): tornado_ii,
    ('ja', 'Healing Breath'): healing_breath(1),
    ('ja', 'Healing Breath II'): healing_breath(2),
    ('ja', 'Healing Breath III'): healing_breath(3),
    ('ja', 'Healing Breath IV'): healing_breath(4),
    ('ja', 'Wyvern Remove'): wyvern_remove,
    ('ja', 'Wyvern Breath'): wyvern_breath,
    ('ja', 'Super Climb'): super_climb,
})
for _e in ('Fire', 'Stone', 'Water', 'Aero', 'Blizzard', 'Thunder'):
    for _t, _n in ((2, 'II'), (4, 'IV')):
        ICONS[('ja', _e + ' ' + _n)] = spirit_spell(_e, _t)
COVERS = {
    'Pact: Impact': ['Impact'],
    'Pact: Slowga': ['Slowga'],
    'Pact: Hastega': ['Hastega'],
    'Pact: Sleepga': ['Sleepga'],
    'Pact: Thunderstorm': ['Thunderstorm'],
    'Pact: Nightmare': ['Nightmare'],
}
VARIANTS = {
    'Wyvern Remove': {'Remove Poison': None, 'Remove Blindness': 100, 'Remove Paralysis': -70, 'Remove Curse': 160,
                      'Remove Disease': -100},
    'Wyvern Breath': {'Flame Breath': None, 'Sand Breath': K.EARTH, 'Gust Breath': 120, 'Frost Breath': 190,
                      'Hydro Breath': 225, 'Lightning Breath': K.THUNDER}  # new Thunder (yellow-orange) from the fire base,
}
