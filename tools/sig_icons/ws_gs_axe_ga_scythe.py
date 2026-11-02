"""Signature icons, round 2: great sword, axe, great axe and scythe weapon skills."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K

p, pts, W = K.p, K.pts, K.W


# ---- helpers --------------------------------------------------------------------------------------------------------
def col(c):
    return c + (255,) if len(c) == 3 else c


def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(col(c0), col(c1), cx, cy, r)


def lin(c0, c1, angle=90):
    return K.linear(col(c0), col(c1), angle)


def rad(c0, c1, cx=0.5, cy=0.5, r=0.5):
    return K.radial(col(c0), col(c1), cx, cy, r)


def scale(m, v):
    return m.point(lambda x: min(255, int(x * v)))


def union(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def minus(a, b):
    return ImageChops.subtract(a, b)


def inter(a, b):
    return ImageChops.multiply(a, b)


def lit(c, m, paint, glowc=None, gr=16, gs=1.2, sh=False, soft=1.2):
    if glowc:
        K.glow(c, m, col(glowc), gr, gs)
    if sh:
        K.shadow(c, m, 5, 8, 8, 160)
    K.fill(c, K.soften(m, soft), col(paint) if isinstance(paint, tuple) else paint)


def xf(seq, cx, cy, s=1.0, ang=0.0):
    """Local points -> canvas pixels: scale s, rotate ang degrees (clockwise), move to (cx, cy)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [p(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in seq]


def xu(x, y, cx, cy, s=1.0, ang=0.0):
    """One local point -> unit coords."""
    a = math.radians(ang)
    return (cx + (x * math.cos(a) - y * math.sin(a)) * s, cy + (x * math.sin(a) + y * math.cos(a)) * s)


def ell(cx, cy, rx, ry, n=36):
    return [(cx + math.cos(2 * math.pi * i / n) * rx, cy + math.sin(2 * math.pi * i / n) * ry) for i in range(n)]


def bez(a, b, c, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0],
                    (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]))
    return out


def arc(cx, cy, r, a0, a1, n=48, ry=None):
    ry = r if ry is None else ry
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * r,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * ry) for i in range(n + 1)]


def ribbon(curve, w0, w1=None, wmid=None):
    """A tapered band along `curve` (unit points): width w0 -> (wmid at the middle) -> w1."""
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
        t = i / max(1, n - 1)
        if wmid is None:
            w = w0 + (w1 - w0) * t
        else:
            w = (w0 + (wmid - w0) * t * 2) if t < 0.5 else (wmid + (w1 - wmid) * (t - 0.5) * 2)
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]


def poly(seq):
    return K.shape(lambda d: d.polygon(pts(seq), fill=255))


def slash(c, cx, cy, r, a0, a1, w, color=(255, 255, 255), glowc=(200, 230, 255), ry=None, gr=14, gs=1.3):
    """A crescent sword-trail along an arc, thin at both ends."""
    m = poly(ribbon(arc(cx, cy, r, a0, a1, 40, ry), 0.0, 0.0, w))
    lit(c, m, color, glowc, gr, gs)
    return m


def line_slash(c, x0, y0, x1, y1, w, color=(255, 255, 255), glowc=(200, 230, 255), gr=12, gs=1.3):
    m = poly(ribbon([(x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * i / 20) for i in range(21)], 0.0, 0.0, w))
    lit(c, m, color, glowc, gr, gs)
    return m


def motes(c, seed, n, box, rr, color, glowc=None, alpha=230):
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


def rays(c, cx, cy, n, color, width=0.05, length=0.75, alpha=90, blur=8, phase=0.0, jitter=0.0, seed=1):
    rnd = random.Random(seed)
    m = K.mask()
    d = ImageDraw.Draw(m)
    for i in range(n):
        a = math.pi * 2 * i / n + phase + rnd.uniform(-jitter, jitter)
        L = length * (1 - rnd.uniform(0, jitter))
        d.polygon(pts([(cx, cy), (cx + math.cos(a - width) * L, cy + math.sin(a - width) * L),
                       (cx + math.cos(a + width) * L, cy + math.sin(a + width) * L)]), fill=alpha)
    K.fill(c, m.filter(ImageFilter.GaussianBlur(blur)), col(color))


def star(d, cx, cy, ro, ri, n=5, rot0=-90, fillv=255):
    q = []
    for i in range(n * 2):
        a = math.radians(rot0) + math.pi * i / n
        r = ro if i % 2 == 0 else ri
        q.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(pts(q), fill=fillv)


def burst(c, cx, cy, ro, ri, n, color, glowc, gr=22, gs=1.3, rot0=-90, inner=None):
    m = K.shape(lambda d: star(d, cx, cy, ro, ri, n, rot0))
    lit(c, m, rad(inner or (255, 255, 240), color, cx, cy, ro), glowc, gr, gs)
    return m


def bolt(d, x0, y0, x1, y1, w, seed=1, segs=6, amp=0.06, fillv=255):
    """A jagged lightning bolt from (x0, y0) to (x1, y1), tapering."""
    rnd = random.Random(seed)
    path = [(x0, y0)]
    for i in range(1, segs):
        t = i / segs
        nx, ny = -(y1 - y0), (x1 - x0)
        L = math.hypot(nx, ny) or 1
        o = rnd.uniform(-amp, amp) * (1 if i % 2 else -1)
        path.append((x0 + (x1 - x0) * t + nx / L * o, y0 + (y1 - y0) * t + ny / L * o))
    path.append((x1, y1))
    d.polygon(pts(ribbon(path, w, w * 0.15)), fill=fillv)


def flame(d, cx, base, w, h, lean=0.0, fillv=255):
    left, right = [], []
    for i in range(41):
        t = i / 40
        y = base - h * t
        half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
        x = cx + lean * t * t
        left.append((x - half, y))
        right.append((x + half, y))
    d.polygon(pts(left + right[::-1]), fill=fillv)


def blaze(c, spec, outer, mid, core, glowc, gr=22):
    """Layered flames: spec = [(cx, base, w, h, lean)]; outer, mid, core = (bottom, top) colour pairs."""
    o = K.shape(lambda d: [flame(d, x, b, w, h, l) for x, b, w, h, l in spec])
    m = K.shape(lambda d: [flame(d, x, b, w * 0.62, h * 0.70, l * 0.7) for x, b, w, h, l in spec])
    k = K.shape(lambda d: [flame(d, x, b, w * 0.32, h * 0.40, l * 0.4) for x, b, w, h, l in spec])
    K.glow(c, o, col(glowc), gr, 1.3)
    K.fill(c, K.soften(o), lin(outer[1], outer[0], 90))
    K.fill(c, K.soften(m), lin(mid[1], mid[0], 90))
    K.fill(c, K.soften(k, 2), lin(core[1], core[0], 90))
    return o


def shard(d, cx, cy, length, w, ang, fillv=255):
    """A long ice crystal pointing along ang degrees from (cx, cy)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    q = [(cx - ux * length * 0.15, cy - uy * length * 0.15), (cx + nx * w, cy + ny * w),
         (cx + ux * length * 0.72 + nx * w * 0.8, cy + uy * length * 0.72 + ny * w * 0.8),
         (cx + ux * length, cy + uy * length),
         (cx + ux * length * 0.72 - nx * w * 0.8, cy + uy * length * 0.72 - ny * w * 0.8),
         (cx - nx * w, cy - ny * w)]
    d.polygon(pts(q), fill=fillv)


def ice(c, spec, glowc=(150, 230, 255), light=(250, 255, 255), dark=(110, 180, 235)):
    """Crystals: spec = [(cx, cy, length, w, ang)]. Lit facet on one side."""
    m = K.shape(lambda d: [shard(d, *s) for s in spec])
    K.glow(c, m, col(glowc), 14, 1.3)
    K.fill(c, K.soften(m), lin(light, dark, 60))
    # a bright facet line down each crystal
    hi = K.shape(lambda d: [shard(d, s[0], s[1], s[2] * 0.9, s[3] * 0.25, s[4]) for s in spec])
    K.fill(c, K.soften(hi, 1.5), (255, 255, 255, 200))
    return m


def snowflake(d, cx, cy, r, w=0.022, fillv=255):
    for i in range(6):
        a = math.pi / 3 * i - math.pi / 2
        ex, ey = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.line(pts([(cx, cy), (ex, ey)]), fill=fillv, width=int(w * W))
        for t, bl in ((0.55, 0.32), (0.80, 0.22)):
            bx, by = cx + math.cos(a) * r * t, cy + math.sin(a) * r * t
            for sgn in (-1, 1):
                b = a + sgn * math.radians(45)
                d.line(pts([(bx, by), (bx + math.cos(b) * r * bl, by + math.sin(b) * r * bl)]), fill=fillv,
                       width=int(w * 0.8 * W))
    d.ellipse(pts([(cx - w * 1.4, cy - w * 1.4), (cx + w * 1.4, cy + w * 1.4)]), fill=fillv)


def rock(d, cx, cy, r, seed, fillv=255):
    rnd = random.Random(seed)
    n = 7
    q = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.25, 0.25)
        rr = r * rnd.uniform(0.7, 1.1)
        q.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts(q), fill=fillv)


def rocks(c, spec, seed=3, top=(200, 170, 130), bot=(90, 66, 44), glowc=None):
    m = K.shape(lambda d: [rock(d, x, y, r, seed + i) for i, (x, y, r) in enumerate(spec)])
    if glowc:
        K.glow(c, m, col(glowc), 10, 1.2)
    K.shadow(c, m, 4, 6, 5, 150)
    K.fill(c, K.soften(m), lin(top, bot, 90))
    hi = minus(m, ImageChops.offset(m, 6, 6))
    K.fill(c, K.soften(hi, 1.5), (255, 240, 210, 120))
    return m


def swirl_wind(c, cx, cy, r, turns, color, glowc, w=0.035, a0=0, ry=None, seed=0):
    """Wind ribbons: a few open arcs of different radii."""
    m = K.mask()
    d = ImageDraw.Draw(m)
    for i in range(turns):
        rr = r * (1 - i * 0.22)
        st = a0 + i * 70
        d.polygon(pts(ribbon(arc(cx, cy, rr, st, st + 230, 40, (ry or rr) * (1 - i * 0.22) if ry else None),
                             0.0, 0.0, w)), fill=255)
    lit(c, m, color, glowc, 10, 1.2)
    return m


def crack(d, x, y, ang, length, w, seed, branches=2, fillv=255):
    rnd = random.Random(seed)
    path = [(x, y)]
    a = math.radians(ang)
    seg = length / 5
    for i in range(5):
        a += rnd.uniform(-0.45, 0.45)
        x, y = x + math.cos(a) * seg, y + math.sin(a) * seg
        path.append((x, y))
    d.polygon(pts(ribbon(path, w, w * 0.1)), fill=fillv)
    for b in range(branches):
        i = 1 + rnd.randrange(3)
        bx, by = path[i]
        ba = a + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.0)
        d.polygon(pts(ribbon([(bx, by), (bx + math.cos(ba) * seg * 1.5, by + math.sin(ba) * seg * 1.5)],
                             w * 0.6, 0.0)), fill=fillv)


def skull(d, cx, cy, s, fillv=255, holes=True):
    d.polygon(xf(ell(0, -0.06, 0.30, 0.28), cx, cy, s), fill=fillv)
    d.polygon(xf([(-0.20, 0.08), (0.20, 0.08), (0.17, 0.32), (-0.17, 0.32)], cx, cy, s), fill=fillv)
    if holes:
        d.polygon(xf(ell(-0.12, 0.02, 0.085, 0.09), cx, cy, s), fill=0)
        d.polygon(xf(ell(0.12, 0.02, 0.085, 0.09), cx, cy, s), fill=0)
        d.polygon(xf([(0, 0.11), (0.04, 0.19), (-0.04, 0.19)], cx, cy, s), fill=0)
        for x in (-0.09, 0.0, 0.09):
            d.polygon(xf([(x - 0.012, 0.24), (x + 0.012, 0.24), (x + 0.012, 0.33), (x - 0.012, 0.33)], cx, cy, s),
                      fill=0)


def crescent(d, cx, cy, r, off=(0.35, -0.2), k=0.85):
    d.ellipse(pts([(cx - r, cy - r), (cx + r, cy + r)]), fill=255)
    ox, oy = cx + off[0] * r, cy + off[1] * r
    d.ellipse(pts([(ox - r * k, oy - r * k), (ox + r * k, oy + r * k)]), fill=0)


def ring(c, cx, cy, r, w, color, glowc, ry=None, alpha=1.0):
    ry = r if ry is None else ry
    m = K.shape(lambda d: d.ellipse(pts([(cx - r, cy - ry), (cx + r, cy + ry)]), outline=255, width=int(w * W)))
    m = scale(m, alpha)
    lit(c, m, color, glowc, 10, 1.3)
    return m


# ---- the weapons ------------------------------------------------------------------------------------------------------
# Each returns {'metal': [...], 'trim': [...], 'wood': [...], 'dark': [...], 'edge': [...]} of local polygons, the
# weapon pointing up, roughly within -0.55..0.5.
def g_greatsword(ornate=False):
    bw = 0.125
    blade = [(0, -0.60), (bw, -0.46), (bw * 0.95, 0.08), (-bw * 0.95, 0.08), (-bw, -0.46)]
    edge = [(0, -0.60), (bw, -0.46), (bw * 0.95, 0.08), (bw * 0.6, 0.08), (bw * 0.62, -0.44), (0, -0.54)]
    fuller = [(-0.020, -0.40), (0.020, -0.40), (0.020, 0.02), (-0.020, 0.02)]
    if ornate:
        guard = [(-0.27, 0.03), (-0.13, 0.08), (0.13, 0.08), (0.27, 0.03), (0.25, 0.13), (0.11, 0.16),
                 (-0.11, 0.16), (-0.25, 0.13)]
    else:
        guard = [(-0.23, 0.08), (0.23, 0.08), (0.26, 0.115), (0.23, 0.15), (-0.23, 0.15), (-0.26, 0.115)]
    grip = [(-0.036, 0.15), (0.036, 0.15), (0.036, 0.42), (-0.036, 0.42)]
    pommel = ell(0, 0.45, 0.056, 0.056, 20)
    out = {'metal': [blade], 'trim': [guard, pommel], 'wood': [grip], 'dark': [fuller], 'edge': [edge]}
    if ornate:
        out['gem'] = [ell(0, 0.115, 0.038, 0.038, 16)]
    return out


def g_axe():
    haft = [(-0.030, -0.44), (0.030, -0.44), (0.036, 0.48), (-0.036, 0.48)]
    edge_curve = bez((0.25, -0.54), (0.42, -0.30), (0.25, -0.06))
    head = [(0.02, -0.42), (0.10, -0.42), (0.25, -0.54)] + edge_curve + [(0.10, -0.24), (0.02, -0.24)]
    edge = edge_curve + [(p_[0] - 0.05, p_[1]) for p_ in edge_curve[::-1]]
    poll = [(-0.02, -0.42), (-0.13, -0.40), (-0.13, -0.26), (-0.02, -0.24)]
    cap = ell(0, 0.48, 0.045, 0.03, 16)
    band = [(-0.040, 0.24), (0.040, 0.24), (0.040, 0.30), (-0.040, 0.30)]
    return {'metal': [head, poll], 'trim': [cap, band], 'wood': [haft], 'edge': [edge], 'dark': []}


def g_greataxe():
    haft = [(-0.030, -0.50), (0.030, -0.50), (0.036, 0.52), (-0.036, 0.52)]
    out_r = bez((0.30, -0.58), (0.50, -0.31), (0.30, -0.04))
    bit_r = [(0.02, -0.40), (0.13, -0.42), (0.30, -0.58)] + out_r + [(0.13, -0.20), (0.02, -0.22)]
    bit_l = [(-x, y) for x, y in bit_r]
    edge_r = out_r + [(q[0] - 0.055, q[1]) for q in out_r[::-1]]
    edge_l = [(-x, y) for x, y in edge_r]
    spike = [(-0.035, -0.46), (0, -0.62), (0.035, -0.46)]
    collar = [(-0.06, -0.42), (0.06, -0.42), (0.06, -0.20), (-0.06, -0.20)]
    cap = ell(0, 0.52, 0.05, 0.03, 16)
    bands = [[(-0.042, y), (0.042, y), (0.042, y + 0.05), (-0.042, y + 0.05)] for y in (0.14, 0.34)]
    return {'metal': [bit_r, bit_l, spike], 'trim': [collar, cap] + bands, 'wood': [haft],
            'edge': [edge_r, edge_l], 'dark': []}


def g_scythe():
    snath = ribbon(bez((0.12, 0.50), (0.03, 0.05), (0.0, -0.30), 20), 0.075, 0.062)
    outer = bez((0.05, -0.42), (-0.40, -0.54), (-0.62, -0.04))
    inner = bez((-0.62, -0.04), (-0.36, -0.28), (0.05, -0.20))
    blade = outer + inner
    edge = inner + [(x + 0.01, y - 0.04) for x, y in inner[::-1]]
    collar = [(-0.050, -0.44), (0.060, -0.44), (0.060, -0.20), (-0.050, -0.20)]
    grip = ribbon([(0.05, 0.10), (0.19, 0.11)], 0.05, 0.05)
    cap = ell(0.12, 0.50, 0.045, 0.03, 16)
    return {'metal': [blade], 'trim': [collar, cap], 'wood': [snath, grip], 'edge': [edge], 'dark': []}


GEOM = {'gs': g_greatsword, 'axe': g_axe, 'ga': g_greataxe, 'scythe': g_scythe}

STEEL = ((248, 250, 255), (120, 132, 160))
DARKSTEEL = ((150, 140, 170), (34, 28, 48))
GOLDM = ((255, 240, 170), (196, 128, 40))
WOOD = ((150, 100, 60), (70, 40, 22))
TRIM = ((255, 226, 150), (170, 110, 40))


ADJ = {'gs': (0.88, 0.0), 'axe': (1.0, 0.0), 'ga': (0.90, 0.05), 'scythe': (0.86, 0.07)}


def weapon_masks(kind, cx, cy, s, ang, **kw):
    g = GEOM[kind](**kw)
    k0, dy = ADJ[kind]
    g = {k: [[(x * k0, y * k0 + dy) for x, y in q] for q in polys] for k, polys in g.items()}
    out = {}
    for k, polys in g.items():
        out[k] = K.shape(lambda d, polys=polys: [d.polygon(xf(q, cx, cy, s, ang), fill=255) for q in polys])
    out['all'] = union(*[out[k] for k in out])
    return out


def weapon(c, kind, cx, cy, s, ang, glowc=None, gr=16, gs=1.2, steel=STEEL, wood=WOOD, trim=TRIM, edgec=None,
           sh=True, bevel=1.0, gem=(230, 40, 50), keyline=False, **kw):
    """Paint a weapon; returns its masks (for clipping effects onto it). keyline: a dark outline first, so the
    weapon separates from a busy or dark field at bar size."""
    m = weapon_masks(kind, cx, cy, s, ang, **kw)
    if glowc:
        K.glow(c, m['all'], col(glowc), gr, gs)
    if sh:
        K.shadow(c, m['all'], 6, 9, 9, 170)
    if keyline:
        K.fill(c, K.soften(m['all'].filter(ImageFilter.MaxFilter(9)), 2), (14, 8, 22, 235))
    K.fill(c, K.soften(m['wood']), lin(*wood))
    K.fill(c, K.soften(m['metal']), lin(steel[0], steel[1], 60))
    K.fill(c, K.soften(m['dark']), (40, 40, 60, 110))
    if edgec is not False:
        e = inter(m['edge'], m['metal'])
        K.fill(c, K.soften(e, 1.5), col(edgec or (255, 255, 255, 170)))
    K.fill(c, K.soften(m['trim']), lin(*trim))
    if 'gem' in m:
        lit(c, m['gem'], col(gem), gem, 6, 1.4)
    # bevel: light on the top-left rims, shade on the bottom-right
    metal = union(m['metal'], m['trim'])
    hi = minus(metal, ImageChops.offset(metal, 5, 5))
    lo = minus(metal, ImageChops.offset(metal, -5, -5))
    K.fill(c, scale(K.soften(hi, 1.5), 0.55 * bevel), (255, 255, 255, 255))
    K.fill(c, scale(K.soften(lo, 1.5), 0.45 * bevel), (10, 6, 20, 255))
    return m


def tint(c, m, color, alpha=0.5, soft=1.2):
    K.fill(c, scale(K.soften(m, soft), alpha), col(color))



# ---- placements -----------------------------------------------------------------------------------------------------
def gs(c, cx=0.5, cy=0.52, s=0.86, ang=40, **kw):
    return weapon(c, 'gs', cx, cy, s, ang, **kw)


def axe(c, cx=0.5, cy=0.54, s=0.88, ang=-25, **kw):
    return weapon(c, 'axe', cx, cy, s, ang, **kw)


def gaxe(c, cx=0.5, cy=0.56, s=0.78, ang=30, **kw):
    return weapon(c, 'ga', cx, cy, s, ang, **kw)


def scy(c, cx=0.60, cy=0.60, s=0.82, ang=18, **kw):
    return weapon(c, 'scythe', cx, cy, s, ang, **kw)


# ---- great sword ----------------------------------------------------------------------------------------------------
def hard_slash():
    """A plain heavy cut: the great sword and the broad white trail of its swing."""
    c = bg((60, 90, 150), (4, 8, 24))
    m = poly(ribbon(arc(0.28, 0.74, 0.46, -62, 12, 40), 0.0, 0.17))
    K.glow(c, m, (150, 200, 255, 255), 18, 1.3)
    K.fill(c, K.soften(m, 2), lin((255, 255, 255), (120, 170, 240), 90))
    gs(c, 0.46, 0.54, 0.86, 45, glowc=(170, 210, 255))
    return K.finish(c)


def power_slash():
    """A crushing blow: blade driving down into a red-orange impact burst."""
    c = bg((180, 50, 30), (26, 4, 4), 0.5, 0.6)
    burst(c, 0.40, 0.66, 0.34, 0.14, 11, (230, 80, 30), (255, 120, 40), 24, 1.4, inner=(255, 250, 200))
    gs(c, 0.58, 0.40, 0.86, 225, glowc=(255, 160, 80))
    motes(c, 4, 12, (0.15, 0.45, 0.65, 0.90), (0.008, 0.016), (255, 230, 160), (255, 140, 60))
    return K.finish(c)


def frostbite():
    """Ice crystals bursting from the blade, frost creeping over it."""
    c = bg((70, 160, 210), (4, 18, 40))
    m = gs(c, 0.5, 0.54, 0.86, 40, glowc=(150, 230, 255), steel=((240, 250, 255), (120, 160, 200)))
    tint(c, inter(m['metal'], poly([(0.5, 0.0), (1.0, 0.0), (1.0, 0.5)])), (190, 240, 255), 0.6)
    spots = []
    for t, side, L in ((0.12, 1, 0.22), (0.20, -1, 0.20), (0.32, 1, 0.17), (0.40, -1, 0.14), (0.04, -1, 0.16)):
        x, y = xu(0, -0.52 + t * 1.2, 0.5, 0.54, 0.86 * 0.88, 40)
        spots.append((x, y, L, 0.036, 40 - 90 + (0 if side > 0 else 180) - side * 30))
    ice(c, spots)
    motes(c, 6, 18, (0.15, 0.10, 0.85, 0.85), (0.006, 0.013), (240, 252, 255), (150, 220, 255))
    return K.finish(c)


def freezebite():
    """Ice and wind: a frost whirlwind around a sideways swing."""
    c = bg((40, 150, 160), (4, 22, 30))
    swirl_wind(c, 0.5, 0.5, 0.40, 3, (220, 255, 255), (120, 230, 240), 0.05, a0=150)
    gs(c, 0.5, 0.52, 0.84, 72, glowc=(160, 240, 255), steel=((240, 255, 255), (110, 160, 190)))
    ice(c, [(0.24, 0.30, 0.13, 0.024, 215), (0.78, 0.72, 0.14, 0.026, 35), (0.70, 0.26, 0.10, 0.02, 300),
            (0.28, 0.76, 0.10, 0.02, 130)])
    return K.finish(c)


def shockwave():
    """The blade planted point-down, a ground-shaking wave rolling out (sleep: drowsy violet)."""
    c = bg((100, 80, 180), (12, 8, 34), 0.5, 0.7)
    for i, (r, a) in enumerate(((0.44, 0.5), (0.32, 0.75), (0.20, 1.0))):
        ring(c, 0.5, 0.80, r, 0.022, (230, 220, 255), (170, 140, 255), ry=r * 0.34, alpha=a)
    gs(c, 0.5, 0.44, 0.78, 180, glowc=(200, 180, 255))
    zz = K.shape(lambda d: [d.line(pts([(x, y), (x + w, y), (x, y + w), (x + w, y + w)]), fill=255,
                                   width=int(0.018 * W), joint='curve')
                            for x, y, w in ((0.70, 0.22, 0.08), (0.80, 0.12, 0.055))])
    lit(c, zz, (240, 235, 255), (180, 160, 255), 6, 1.2)
    return K.finish(c)


def crescent_moon():
    """A great sword before a huge pale crescent moon."""
    c = bg((40, 50, 130), (4, 6, 26), 0.5, 0.4)
    moon = K.shape(lambda d: crescent(d, 0.46, 0.46, 0.34, (0.40, -0.18), 0.86))
    K.glow(c, moon, (255, 230, 160, 255), 22, 1.2)
    K.fill(c, K.soften(moon), lin((255, 248, 210), (230, 190, 110)))
    gs(c, 0.56, 0.54, 0.80, 35, glowc=(255, 236, 180))
    sparkles(c, [(0.78, 0.22, 0.05), (0.22, 0.78, 0.035)])
    return K.finish(c)


def sickle_moon():
    """Two sickle-thin moon slashes crossing behind a level blade."""
    c = bg((40, 110, 120), (4, 16, 22))
    m1 = K.shape(lambda d: crescent(d, 0.40, 0.42, 0.30, (0.24, -0.18), 0.94))
    m2 = K.shape(lambda d: crescent(d, 0.60, 0.58, 0.30, (-0.24, 0.18), 0.94))
    for m in (m1, m2):
        lit(c, m, lin((250, 255, 240), (170, 230, 210)), (170, 255, 220), 14, 1.3)
    gs(c, 0.5, 0.52, 0.84, 62, glowc=(190, 255, 230))
    return K.finish(c)


def spinning_slash():
    """The blade whirled through a full circle of light."""
    c = bg((210, 150, 50), (34, 18, 4))
    trail = poly(ribbon(arc(0.5, 0.5, 0.36, -60, 250, 60), 0.0, 0.10))
    lit(c, trail, lin((255, 255, 230), (255, 190, 80), 0), (255, 200, 90), 16, 1.3)
    gs(c, 0.5, 0.5, 0.80, 300, glowc=(255, 220, 140))
    return K.finish(c)


def ground_strike():
    """The blade slammed into the earth, the ground cracking and stones leaping."""
    c = bg((170, 110, 50), (26, 14, 4), 0.5, 0.75)
    ground = poly([(0.0, 0.70), (0.3, 0.66), (0.7, 0.67), (1.0, 0.71), (1.0, 1.0), (0.0, 1.0)])
    K.fill(c, K.soften(ground, 3), lin((120, 80, 44), (40, 24, 10)))
    cr = K.shape(lambda d: [crack(d, 0.5, 0.70, a, 0.30, 0.026, i + 2) for i, a in enumerate((10, 70, 110, 170))])
    lit(c, cr, (255, 210, 110), (255, 150, 50), 12, 1.6)
    gs(c, 0.5, 0.34, 0.80, 180, glowc=(255, 190, 100))
    rocks(c, [(0.22, 0.52, 0.06), (0.80, 0.46, 0.055), (0.28, 0.30, 0.04), (0.74, 0.24, 0.04)])
    return K.finish(c)


def scourge():
    """Ragnarok: a radiant golden-hilted great sword in a blaze of crimson and gold."""
    c = bg((200, 40, 30), (28, 2, 4), 0.5, 0.45)
    rays(c, 0.5, 0.40, 20, (255, 220, 140), 0.07, 0.8, 170, 5, 0.1)
    sun = K.shape(lambda d: d.ellipse(pts([(0.26, 0.16), (0.74, 0.64)]), fill=255))
    K.fill(c, scale(sun.filter(ImageFilter.GaussianBlur(26)), 0.7), (255, 140, 50, 255))
    ring(c, 0.5, 0.40, 0.26, 0.018, (255, 240, 180), (255, 180, 60))
    gs(c, 0.5, 0.52, 0.94, 0, glowc=(255, 250, 210), gr=14, gs=1.3, ornate=True, trim=GOLDM,
       steel=((255, 255, 255), (150, 160, 200)), gem=(255, 40, 60))
    sparkles(c, [(0.22, 0.30, 0.05), (0.78, 0.36, 0.04)])
    motes(c, 11, 14, (0.12, 0.15, 0.88, 0.85), (0.006, 0.013), (255, 240, 200), (255, 180, 80))
    return K.finish(c)


def herculean_slash():
    """A Herculean ice cleave: a burst of great crystals around an upright blade."""
    c = bg((40, 70, 180), (2, 6, 34))
    spec = []
    for i in range(10):
        a = i * 36 + 18
        L = 0.38 if i % 2 else 0.26
        spec.append((0.5 + math.cos(math.radians(a)) * 0.05, 0.52 + math.sin(math.radians(a)) * 0.05, L, 0.05, a))
    ice(c, spec, (130, 200, 255), (255, 255, 255), (100, 150, 230))
    gs(c, 0.5, 0.52, 0.82, 0, glowc=(220, 240, 255), steel=((250, 255, 255), (130, 160, 220)))
    bl = K.shape(lambda d: [bolt(d, 0.16, 0.56, 0.30, 0.78, 0.02, 3, 4, 0.04),
                            bolt(d, 0.84, 0.30, 0.72, 0.14, 0.018, 5, 4, 0.04)])
    lit(c, bl, (255, 255, 200), (255, 240, 120), 6, 1.4)
    return K.finish(c)


def torcleaver():
    """Caladbolg: a dark violet blade framed by a pillar of light falling from above."""
    c = bg((110, 40, 160), (10, 2, 24), 0.5, 0.4)
    pillar = poly([(0.24, 0.0), (0.76, 0.0), (0.62, 1.0), (0.38, 1.0)])
    K.fill(c, pillar.filter(ImageFilter.GaussianBlur(14)), (255, 214, 160, 255))
    K.fill(c, poly([(0.40, 0.0), (0.60, 0.0), (0.55, 1.0), (0.45, 1.0)]).filter(ImageFilter.GaussianBlur(10)),
           (255, 250, 235, 255))
    gs(c, 0.5, 0.54, 0.94, 0, glowc=(255, 240, 210), gr=16, gs=1.3, ornate=True, trim=GOLDM,
       steel=((200, 170, 245), (40, 20, 80)), edgec=(240, 210, 255, 220), gem=(160, 255, 220))
    sparkles(c, [(0.20, 0.30, 0.04), (0.80, 0.70, 0.035)], glowc=(230, 200, 255))
    return K.finish(c)


def resolution():
    """Lionheart: five lightning-quick strokes fanned around a resolute blade."""
    c = bg((40, 150, 100), (2, 22, 14), 0.5, 0.45)
    for i in range(5):
        a = math.radians(-150 + i * 30)
        x0, y0 = 0.5 + math.cos(a) * 0.40, 0.55 + math.sin(a) * 0.40
        x1, y1 = 0.5 + math.cos(a + math.pi) * 0.08, 0.55 + math.sin(a + math.pi) * 0.08
        line_slash(c, x0, y0, (x0 + x1) / 2 + (x1 - x0) * 0.25, (y0 + y1) / 2 + (y1 - y0) * 0.25, 0.04,
                   (240, 255, 220), (170, 255, 140), 10)
    gs(c, 0.5, 0.56, 0.88, 0, glowc=(220, 255, 170), gr=18, gs=1.5, ornate=True, trim=GOLDM,
       steel=((255, 255, 240), (130, 160, 140)), gem=(80, 220, 120))
    sparkles(c, [(0.5, 0.06, 0.06)], glowc=(220, 255, 170))
    return K.finish(c)


def dimidiation():
    """Halving: a sun of light cut clean in two, its halves sliding apart round the blade."""
    c = bg((190, 50, 100), (26, 2, 16), 0.5, 0.45)
    disc = K.shape(lambda d: d.ellipse(pts([(0.20, 0.18), (0.80, 0.78)]), fill=255))
    left = inter(disc, poly([(0, 0), (0.5, 0), (0.5, 1), (0, 1)]))
    right = minus(disc, left)
    left = ImageChops.offset(left, -int(0.06 * W), -int(0.08 * W))
    right = ImageChops.offset(right, int(0.06 * W), int(0.08 * W))
    for h in (left, right):
        lit(c, h, rad((255, 255, 240), (255, 150, 110), 0.5, 0.48, 0.36), (255, 150, 130), 18, 1.3)
    gs(c, 0.5, 0.52, 0.94, 0, glowc=(255, 245, 250), gr=18, gs=1.7, ornate=True, trim=GOLDM,
       steel=((255, 255, 255), (190, 170, 200)), gem=(255, 90, 160))
    sparkles(c, [(0.86, 0.32, 0.05), (0.14, 0.68, 0.04)])
    return K.finish(c)


def fimbulvetr():
    """The great winter: a vast snowflake and a blizzard behind an upright frost blade."""
    c = bg((120, 130, 210), (8, 10, 40), 0.5, 0.45)
    flake = K.shape(lambda d: snowflake(d, 0.5, 0.46, 0.38, 0.03))
    K.glow(c, flake, (200, 220, 255, 255), 14, 1.3)
    K.fill(c, scale(K.soften(flake), 0.8), (235, 242, 255, 255))
    gs(c, 0.5, 0.52, 0.86, 0, glowc=(220, 235, 255), gr=18, gs=1.5,
       steel=((255, 255, 255), (150, 170, 230)), trim=((230, 240, 255), (120, 140, 200)))
    motes(c, 12, 30, (0.10, 0.08, 0.90, 0.92), (0.006, 0.014), (255, 255, 255), (200, 220, 255))
    return K.finish(c)


# ---- axe ------------------------------------------------------------------------------------------------------------
def ghosts(c, kind, cx, cy, s, angs, color, alpha=(0.35, 0.6)):
    for a, al in zip(angs, alpha):
        m = weapon_masks(kind, cx, cy, s, a)['all']
        K.glow(c, m, col(color), 10, al * 0.8)
        K.fill(c, scale(K.soften(m, 2), al), col(color))


def raging_axe():
    """Two furious chops: the axe and its after-images."""
    c = bg((200, 70, 30), (30, 6, 4))
    ghosts(c, 'axe', 0.5, 0.56, 0.88, (-82, -52), (255, 220, 170), (0.3, 0.5))
    axe(c, 0.5, 0.56, 0.88, -20, glowc=(255, 140, 60))
    return K.finish(c)


def smash_axe():
    """A stunning blow: stars spinning over the point of impact."""
    c = bg((210, 170, 50), (36, 22, 4), 0.4, 0.6)
    burst(c, 0.30, 0.70, 0.26, 0.10, 9, (255, 190, 60), (255, 210, 90), 20, 1.3)
    axe(c, 0.58, 0.46, 0.88, -45, glowc=(255, 230, 140))
    ringm = K.shape(lambda d: d.ellipse(pts([(0.12, 0.20), (0.56, 0.34)]), outline=255, width=int(0.012 * W)))
    K.fill(c, scale(K.soften(ringm, 2), 0.6), (255, 250, 210, 255))
    sparkles(c, [(0.14, 0.27, 0.06), (0.34, 0.20, 0.05), (0.52, 0.32, 0.055)], (255, 255, 220), (255, 230, 120))
    return K.finish(c)


def gale_axe():
    """An axe riding a green gale."""
    c = bg((60, 170, 90), (4, 26, 12))
    swirl_wind(c, 0.5, 0.52, 0.40, 3, (230, 255, 230), (130, 255, 150), 0.05, a0=100)
    axe(c, 0.5, 0.54, 0.86, -25, glowc=(170, 255, 170))
    motes(c, 13, 10, (0.15, 0.15, 0.85, 0.85), (0.006, 0.012), (230, 255, 230), (130, 255, 150))
    return K.finish(c)


def avalanche_axe():
    """Boulders tumbling down behind a downward chop."""
    c = bg((150, 130, 110), (24, 18, 14), 0.5, 0.35)
    streak = K.mask()
    sd = ImageDraw.Draw(streak)
    for x in (0.25, 0.45, 0.65, 0.82):
        sd.line(pts([(x + 0.10, 0.05), (x - 0.10, 0.75)]), fill=150, width=int(0.03 * W))
    K.fill(c, streak.filter(ImageFilter.GaussianBlur(10)), (240, 230, 220, 255))
    rocks(c, [(0.74, 0.22, 0.07), (0.26, 0.30, 0.055), (0.80, 0.56, 0.05), (0.24, 0.66, 0.06), (0.52, 0.82, 0.045)],
          seed=21, top=(210, 190, 160), bot=(90, 70, 52))
    axe(c, 0.52, 0.50, 0.84, -10, glowc=(255, 240, 210))
    return K.finish(c)


def spinning_axe():
    """Three axes in a whirling wheel."""
    c = bg((210, 120, 40), (34, 14, 4))
    trail = poly(ribbon(arc(0.5, 0.5, 0.40, 0, 330, 60), 0.0, 0.07))
    lit(c, trail, (255, 240, 200), (255, 170, 70), 12, 1.3)
    for k in range(3):
        a = k * 120 - 90
        x, y = 0.5 + math.cos(math.radians(a)) * 0.15, 0.5 + math.sin(math.radians(a)) * 0.15
        axe(c, x, y, 0.70, a + 180, glowc=(255, 200, 120), gr=8, keyline=True)
    hub = K.shape(lambda d: d.ellipse(pts([(0.45, 0.45), (0.55, 0.55)]), fill=255))
    lit(c, hub, (255, 250, 220), (255, 220, 140), 10, 1.4)
    return K.finish(c)


def claws(c, n, cx, cy, ang, length, gap, w, color, glowc):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    for i in range(n):
        o = (i - (n - 1) / 2) * gap
        x0, y0 = cx - ux * length / 2 + nx * o, cy - uy * length / 2 + ny * o
        x1, y1 = cx + ux * length / 2 + nx * o, cy + uy * length / 2 + ny * o
        line_slash(c, x0, y0, x1, y1, w, color, glowc, 10)


def rampage():
    """Five savage hits: a rake of red slashes behind the axe."""
    c = bg((150, 20, 40), (20, 2, 6))
    claws(c, 5, 0.5, 0.5, 60, 0.78, 0.10, 0.05, (255, 220, 220), (255, 40, 60))
    axe(c, 0.5, 0.54, 0.86, -30, glowc=(255, 90, 90), steel=((240, 230, 235), (110, 90, 100)))
    return K.finish(c)


def calamity():
    """A dark axe under a ruinous storm: a violet vortex rent by red lightning."""
    c = bg((110, 40, 130), (12, 2, 18), 0.5, 0.35)
    sp = K.mask()
    sd = ImageDraw.Draw(sp)
    for arm in range(3):
        path = []
        for i in range(40):
            t = i / 39
            a = arm * 2 * math.pi / 3 + t * 3.2
            r = 0.04 + 0.36 * t
            path.append((0.5 + math.cos(a) * r, 0.42 + math.sin(a) * r * 0.6))
        sd.polygon(pts(ribbon(path, 0.01, 0.08)), fill=200)
    K.fill(c, sp.filter(ImageFilter.GaussianBlur(5)), (40, 0, 40, 255))
    K.glow(c, sp, (220, 90, 240, 255), 10, 1.0)
    bl = K.shape(lambda d: [bolt(d, 0.50, 0.40, 0.18, 0.84, 0.04, 8, 5, 0.06),
                            bolt(d, 0.50, 0.40, 0.84, 0.76, 0.034, 9, 5, 0.05)])
    lit(c, bl, (255, 230, 230), (255, 40, 60), 14, 1.8)
    axe(c, 0.50, 0.56, 0.90, -20, glowc=(230, 120, 255), gs=1.5, steel=((236, 228, 250), (100, 80, 130)),
        keyline=True)
    return K.finish(c)


def mistral_axe():
    """An axe hurled on a sea wind, streaks trailing behind it."""
    c = bg((40, 160, 150), (2, 22, 26))
    lines = K.mask()
    ld = ImageDraw.Draw(lines)
    for y, x0, a in ((0.36, 0.06, 200), (0.48, 0.02, 255), (0.60, 0.08, 220), (0.70, 0.18, 160)):
        ld.line(pts([(x0, y), (0.52, y - 0.08)]), fill=a, width=int(0.022 * W))
    K.fill(c, lines.filter(ImageFilter.GaussianBlur(4)), (220, 255, 250, 255))
    swirl_wind(c, 0.30, 0.56, 0.16, 2, (230, 255, 250), (120, 240, 230), 0.035, a0=40)
    axe(c, 0.60, 0.46, 0.80, 50, glowc=(170, 255, 240))
    return K.finish(c)


def decimation():
    """Three heavy chops: three axes fanned out in a crimson-violet glow."""
    c = bg((140, 40, 100), (20, 4, 16), 0.5, 0.7)
    rays(c, 0.5, 0.80, 10, (255, 160, 220), 0.08, 0.8, 90, 8, math.pi)
    for a in (-40, 40, 0):
        axe(c, 0.5, 0.56, 0.84, a, glowc=(255, 120, 200), gr=12)
    return K.finish(c)


def onslaught():
    """Guttler: a massive golden axe blazing with fire."""
    c = bg((200, 80, 20), (36, 4, 2), 0.5, 0.6)
    rays(c, 0.5, 0.36, 16, (255, 230, 150), 0.07, 0.8, 140, 6, 0.2)
    blaze(c, [(0.50, 0.98, 0.22, 0.84, 0.03), (0.22, 0.98, 0.13, 0.58, -0.08), (0.78, 0.98, 0.13, 0.62, 0.08)],
          ((230, 60, 10), (255, 150, 40)), ((255, 140, 30), (255, 220, 90)), ((255, 240, 160), (255, 255, 240)),
          (255, 100, 20))
    axe(c, 0.44, 0.62, 1.12, -20, glowc=(255, 250, 200), gr=22, gs=1.6,
        steel=((255, 248, 170), (205, 120, 20)), trim=((255, 120, 80), (160, 20, 20)), edgec=(255, 255, 230, 230))
    sparkles(c, [(0.76, 0.16, 0.07), (0.18, 0.36, 0.04)])
    return K.finish(c)


def primal_rend():
    """Aymur: the axe unleashing a primal blast of white-gold light under an open sky."""
    c = bg((70, 140, 220), (6, 14, 44), 0.36, 0.34)
    rays(c, 0.36, 0.34, 20, (255, 250, 220), 0.06, 0.9, 150, 5)
    ring(c, 0.36, 0.34, 0.24, 0.02, (255, 250, 230), (255, 230, 150))
    orb = K.shape(lambda d: d.ellipse(pts([(0.20, 0.18), (0.52, 0.50)]), fill=255))
    K.glow(c, orb, (255, 245, 200, 255), 40, 2.0)
    K.fill(c, K.soften(orb, 10), rad((255, 255, 255), (255, 230, 150), 0.36, 0.34, 0.16))
    axe(c, 0.48, 0.60, 0.92, 24, glowc=(255, 255, 220), gr=18, gs=1.4, steel=GOLDM,
        trim=((120, 220, 255), (30, 90, 170)), edgec=(255, 255, 240, 230))
    sparkles(c, [(0.36, 0.34, 0.10), (0.20, 0.74, 0.04)])
    return K.finish(c)


def bora_axe():
    """A cold northern wind: the axe frosting over, ice binding the ground."""
    c = bg((90, 170, 220), (6, 22, 44))
    swirl_wind(c, 0.5, 0.40, 0.34, 2, (240, 255, 255), (170, 230, 255), 0.04, a0=200)
    ice(c, [(0.20, 0.88, 0.22, 0.04, -80), (0.36, 0.90, 0.28, 0.045, -95), (0.62, 0.90, 0.24, 0.04, -85),
            (0.80, 0.88, 0.18, 0.035, -100)])
    axe(c, 0.52, 0.48, 0.80, -25, glowc=(200, 240, 255), steel=((250, 255, 255), (120, 170, 210)))
    motes(c, 14, 14, (0.12, 0.10, 0.88, 0.60), (0.005, 0.011), (255, 255, 255), (170, 220, 255))
    return K.finish(c)


def cloud(d, cx, cy, s, fillv=255):
    for x, y, r in ((-0.22, 0.02, 0.13), (-0.06, -0.08, 0.17), (0.14, -0.04, 0.15), (0.28, 0.04, 0.10),
                    (0.0, 0.06, 0.14)):
        d.ellipse(pts([(cx + (x - r) * s, cy + (y - r) * s), (cx + (x + r) * s, cy + (y + r) * s)]), fill=fillv)


def cloudsplitter():
    """Farsha: the thrown axe tearing through storm clouds, lightning in its wake."""
    c = bg((110, 80, 200), (8, 4, 30), 0.5, 0.4)
    cl = K.shape(lambda d: [cloud(d, 0.24, 0.30, 0.9), cloud(d, 0.80, 0.72, 0.9)])
    K.fill(c, cl.filter(ImageFilter.GaussianBlur(6)), (190, 170, 230, 200))
    K.fill(c, K.soften(minus(cl, ImageChops.offset(cl, 0, 14)), 4), (255, 255, 255, 120))
    bl = K.shape(lambda d: [bolt(d, 0.12, 0.10, 0.48, 0.52, 0.04, 3, 6, 0.06),
                            bolt(d, 0.50, 0.50, 0.88, 0.92, 0.034, 4, 6, 0.06)])
    lit(c, bl, (255, 255, 230), (230, 200, 255), 16, 1.6)
    axe(c, 0.52, 0.50, 0.88, 40, glowc=(250, 240, 255), gr=20, gs=1.5,
        steel=((255, 255, 255), (150, 150, 200)), trim=((255, 230, 140), (170, 110, 40)))
    sparkles(c, [(0.74, 0.18, 0.05)], glowc=(220, 200, 255))
    return K.finish(c)


def ruinator():
    """Tri-edge: four crossing cuts in two X's, a ruinous crimson-violet glow."""
    c = bg((150, 30, 100), (20, 2, 16))
    for cx, cy in ((0.34, 0.36), (0.66, 0.64)):
        line_slash(c, cx - 0.22, cy - 0.20, cx + 0.22, cy + 0.20, 0.05, (255, 230, 250), (255, 70, 180), 10)
        line_slash(c, cx + 0.22, cy - 0.20, cx - 0.22, cy + 0.20, 0.05, (255, 230, 250), (255, 70, 180), 10)
    axe(c, 0.5, 0.54, 0.94, -32, glowc=(255, 150, 230), gr=20, gs=1.5,
        steel=((240, 230, 255), (80, 60, 120)), trim=GOLDM)
    sparkles(c, [(0.78, 0.20, 0.05)], glowc=(255, 160, 230))
    return K.finish(c)


def blitz():
    """Lightning-fast: an axe flashing past in a blur of amber speed lines."""
    c = bg((40, 60, 150), (2, 6, 30))
    lines = K.mask()
    ld = ImageDraw.Draw(lines)
    for y, x0, w in ((0.30, 0.08, 0.05), (0.46, 0.02, 0.07), (0.62, 0.10, 0.05)):
        ld.polygon(pts(ribbon([(x0 + t * 0.5, y + 0.08 - t * 0.12) for t in [i / 10 for i in range(11)]], 0.0, w)),
                   fill=255)
    K.glow(c, lines, (255, 190, 60, 255), 10, 1.2)
    K.fill(c, K.soften(lines), lin((255, 200, 80, 120), (255, 250, 220, 255), 0))
    axe(c, 0.60, 0.52, 0.86, -18, glowc=(255, 210, 90))
    bl = K.shape(lambda d: [bolt(d, 0.82, 0.62, 0.92, 0.42, 0.024, 7, 3, 0.03)])
    lit(c, bl, (255, 250, 220), (255, 210, 80), 6, 1.4)
    return K.finish(c)


# ---- great axe ------------------------------------------------------------------------------------------------------
def shield_pts(cx, top, w, h):
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


def shield_break():
    """The great axe biting into a shield, splitting it."""
    c = bg((60, 100, 170), (6, 10, 30))
    sh = poly(shield_pts(0.42, 0.40, 0.25, 0.50))
    K.shadow(c, sh, 5, 8, 8, 160)
    K.fill(c, K.soften(sh), lin((80, 130, 200), (30, 50, 110)))
    inner = poly(shield_pts(0.42, 0.44, 0.20, 0.42))
    K.fill(c, K.soften(minus(sh, inner)), lin((240, 220, 160), (170, 120, 50)))
    cr = K.shape(lambda d: [crack(d, 0.52, 0.48, 120, 0.36, 0.03, 4, 2)])
    K.fill(c, K.soften(inter(cr, sh)), (10, 10, 20, 255))
    gaxe(c, 0.58, 0.40, 0.66, 40, glowc=(200, 220, 255))
    burst(c, 0.50, 0.48, 0.10, 0.04, 8, (255, 230, 150), (255, 240, 200), 10, 1.2)
    return K.finish(c)


def iron_tempest():
    """A storm of iron: the great axe at the heart of a whirling grey tempest."""
    c = bg((120, 120, 140), (14, 14, 22))
    swirl_wind(c, 0.5, 0.52, 0.42, 3, (230, 232, 240), (180, 190, 220), 0.06, a0=30)
    rnd = random.Random(31)
    fr = K.shape(lambda d: [rock(d, 0.5 + math.cos(a) * r, 0.52 + math.sin(a) * r, 0.025, i)
                            for i, (a, r) in enumerate((rnd.uniform(0, 6.3), rnd.uniform(0.25, 0.40))
                                                       for _ in range(10))])
    lit(c, fr, lin((255, 255, 255), (130, 140, 160)), (220, 230, 255), 6, 1.1)
    gaxe(c, 0.5, 0.56, 0.76, 20, glowc=(220, 225, 245))
    return K.finish(c)


def sturmwind():
    """Two twisters flanking the great axe."""
    c = bg((50, 160, 120), (4, 24, 18))
    for x in (0.22, 0.78):
        m = K.mask()
        d = ImageDraw.Draw(m)
        for k in range(6):
            t = k / 5
            y = 0.82 - t * 0.56
            rx = 0.03 + 0.13 * t
            d.ellipse(pts([(x - rx, y - rx * 0.32), (x + rx, y + rx * 0.32)]), outline=255, width=int(0.028 * W))
        lit(c, m, (240, 255, 245), (130, 255, 190), 12, 1.5)
    gaxe(c, 0.5, 0.56, 0.78, 0, glowc=(190, 255, 220))
    return K.finish(c)


def breastplate(d, cx, cy, s, fillv=255):
    q = [(-0.32, -0.34), (-0.12, -0.36), (0, -0.28), (0.12, -0.36), (0.32, -0.34), (0.30, -0.24),
         (0.22, -0.14), (0.20, 0.04), (0.24, 0.30), (0, 0.38), (-0.24, 0.30), (-0.20, 0.04), (-0.22, -0.14),
         (-0.30, -0.24)]
    d.polygon(xf(q, cx, cy, s), fill=fillv)


def armor_break():
    """A steel cuirass cracking open under the great axe."""
    c = bg((180, 100, 40), (26, 10, 2))
    S0, X0, Y0 = 0.78, 0.38, 0.62
    bp = K.shape(lambda d: breastplate(d, X0, Y0, S0))
    K.glow(c, bp, (255, 200, 120, 255), 12, 1.0)
    K.shadow(c, bp, 5, 8, 8, 170)
    edge = minus(bp, bp.filter(ImageFilter.MinFilter(9)))
    K.fill(c, K.soften(bp), lin((235, 240, 252), (110, 120, 150), 60))
    K.fill(c, K.soften(edge), (50, 50, 70, 255))
    lines = K.shape(lambda d: [d.line(xf([(0, -0.24), (0, 0.34)], X0, Y0, S0), fill=255, width=int(0.014 * W)),
                               d.arc(xf([(-0.22, -0.10), (0.22, 0.24)], X0, Y0, S0), 20, 160, fill=255,
                                     width=int(0.014 * W))])
    K.fill(c, scale(K.soften(inter(lines, bp)), 0.6), (40, 40, 60, 255))
    K.fill(c, scale(K.soften(minus(bp, ImageChops.offset(bp, 6, 6)), 1.5), 0.6), (255, 255, 255, 255))
    cr = K.shape(lambda d: [crack(d, 0.46, 0.46, 110, 0.36, 0.035, 9, 3)])
    K.fill(c, K.soften(inter(cr, bp)), (20, 8, 4, 255))
    gaxe(c, 0.62, 0.38, 0.66, 40, glowc=(255, 220, 160))
    burst(c, 0.47, 0.46, 0.10, 0.04, 8, (255, 220, 140), (255, 230, 170), 10, 1.2)
    return K.finish(c)


def keen_edge():
    """A razor gleam running along the great axe's edge."""
    c = bg((50, 150, 200), (2, 18, 34))
    m = gaxe(c, 0.5, 0.56, 0.80, 0, glowc=(200, 240, 255), edgec=(255, 255, 255, 255))
    K.glow(c, inter(m['edge'], m['metal']), (180, 240, 255, 255), 8, 1.6)
    sparkles(c, [(0.80, 0.24, 0.11), (0.22, 0.44, 0.06)], glowc=(180, 240, 255))
    return K.finish(c)


def weapon_break():
    """A sword snapped in two by the great axe."""
    c = bg((180, 90, 40), (28, 10, 2))
    a = weapon_masks('gs', 0.30, 0.64, 0.55, -50)['all']
    cut = poly([(0.0, 0.0), (0.38, 0.0), (0.26, 1.0), (0.0, 1.0)])
    lower = inter(a, cut)
    upper = ImageChops.offset(minus(a, cut), int(0.07 * W), -int(0.08 * W))
    upper = upper.rotate(-15, resample=Image.BICUBIC, center=p(0.45, 0.30))
    for part in (lower, upper):
        K.shadow(c, part, 4, 6, 6, 150)
        K.fill(c, K.soften(part), lin((240, 240, 250), (120, 120, 140), 60))
    gaxe(c, 0.58, 0.46, 0.70, 30, glowc=(255, 210, 150))
    burst(c, 0.33, 0.47, 0.11, 0.04, 8, (255, 220, 140), (255, 230, 170), 10, 1.2)
    motes(c, 32, 8, (0.22, 0.30, 0.46, 0.60), (0.007, 0.014), (255, 240, 200), (255, 190, 100))
    return K.finish(c)


def raging_rush():
    """Three frenzied swings: the great axe with its after-images."""
    c = bg((190, 30, 30), (26, 2, 4))
    ghosts(c, 'ga', 0.5, 0.58, 0.76, (-60, -31), (255, 210, 180), (0.42, 0.62))
    gaxe(c, 0.5, 0.58, 0.76, 2, glowc=(255, 120, 80))
    return K.finish(c)


def full_break():
    """Everything broken: the great axe amid the shards of shattered gear."""
    c = bg((130, 60, 160), (14, 4, 22))
    rays(c, 0.5, 0.5, 12, (230, 200, 255), 0.05, 0.75, 90, 6)
    rnd = random.Random(41)
    fr = K.mask()
    fd = ImageDraw.Draw(fr)
    for i in range(12):
        a = i * 30 + rnd.uniform(-10, 10)
        r = rnd.uniform(0.28, 0.40)
        x, y = 0.5 + math.cos(math.radians(a)) * r, 0.5 + math.sin(math.radians(a)) * r
        sz = rnd.uniform(0.03, 0.05)
        fd.polygon(pts([(x, y - sz), (x + sz * 0.8, y + sz * 0.3), (x - sz * 0.2, y + sz), (x - sz * 0.9, y)]),
                   fill=255)
    K.shadow(c, fr, 3, 5, 4, 140)
    K.fill(c, K.soften(fr), lin((255, 240, 255), (150, 120, 180)))
    burst(c, 0.5, 0.5, 0.22, 0.09, 10, (230, 150, 255), (220, 160, 255), 16, 1.2)
    gaxe(c, 0.5, 0.56, 0.74, 35, glowc=(240, 210, 255))
    return K.finish(c)


def steel_cyclone():
    """The great axe spinning at the heart of a steel-grey cyclone."""
    c = bg((80, 120, 170), (6, 12, 26))
    m = K.mask()
    d = ImageDraw.Draw(m)
    for k in range(7):
        t = k / 6
        y = 0.86 - t * 0.66
        rx = 0.06 + 0.32 * t
        d.ellipse(pts([(0.5 - rx, y - rx * 0.22), (0.5 + rx, y + rx * 0.22)]), outline=255, width=int(0.022 * W))
    lit(c, m, (235, 245, 255), (150, 190, 255), 12, 1.2)
    gaxe(c, 0.5, 0.52, 0.70, 75, glowc=(210, 230, 255))
    return K.finish(c)


def wing(d, cx, cy, side, s=1.0):
    for i in range(6):
        t = i / 5
        ang = math.radians(-15 - 55 * t) if side > 0 else math.radians(195 + 55 * t)
        length = (0.40 - 0.10 * t) * s
        bx, by = cx, cy
        ex, ey = bx + math.cos(ang) * length, by + math.sin(ang) * length
        nx, ny = -math.sin(ang) * 0.05 * s, math.cos(ang) * 0.05 * s
        d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)


def metatron_torment():
    """Bravura: the great axe borne on angel's wings under a halo, in a blaze of holy light."""
    c = bg((210, 150, 60), (30, 14, 4), 0.5, 0.40)
    rays(c, 0.5, 0.40, 16, (255, 245, 200), 0.06, 0.8, 120, 8)
    wings = K.shape(lambda d: [wing(d, 0.56, 0.52, 1, 1.15), wing(d, 0.44, 0.52, -1, 1.15)])
    K.glow(c, wings, (255, 255, 230, 255), 18, 1.4)
    K.fill(c, K.soften(wings), lin((255, 255, 255), (235, 220, 190)))
    halo = K.shape(lambda d: d.ellipse(pts([(0.36, 0.08), (0.64, 0.17)]), outline=255, width=int(0.03 * W)))
    lit(c, halo, (255, 245, 170), (255, 230, 120), 10, 1.6)
    gaxe(c, 0.5, 0.60, 0.72, 0, glowc=(255, 255, 230), gr=18, gs=1.4,
         steel=((220, 220, 240), (50, 50, 80)), trim=GOLDM)
    return K.finish(c)


def crown(d, cx, cy, s, fillv=255):
    q = [(-0.30, 0.12), (-0.34, -0.16), (-0.16, 0.0), (0, -0.24), (0.16, 0.0), (0.34, -0.16), (0.30, 0.12)]
    d.polygon(xf(q, cx, cy, s), fill=fillv)
    d.rectangle(pts([(cx - 0.30 * s, cy + 0.12 * s), (cx + 0.30 * s, cy + 0.20 * s)]), fill=fillv)


def kings_justice():
    """Conqueror: a royal great axe beneath a golden crown."""
    c = bg((110, 40, 160), (12, 2, 24), 0.5, 0.4)
    rays(c, 0.5, 0.26, 14, (255, 220, 140), 0.06, 0.7, 90, 8)
    gaxe(c, 0.5, 0.62, 0.72, 0, glowc=(255, 220, 150), gr=18, gs=1.3,
         steel=((255, 250, 240), (140, 120, 150)), trim=GOLDM)
    cr = K.shape(lambda d: crown(d, 0.5, 0.20, 0.42))
    lit(c, cr, lin((255, 245, 180), (210, 140, 40)), (255, 220, 120), 14, 1.4, sh=True)
    gems = K.shape(lambda d: [d.ellipse(pts([(x - 0.018, 0.255 - 0.018), (x + 0.018, 0.255 + 0.018)]), fill=255)
                              for x in (0.42, 0.5, 0.58)])
    K.fill(c, K.soften(gems), (230, 40, 70, 255))
    sparkles(c, [(0.5, 0.06, 0.04)])
    return K.finish(c)


def fell_cleave():
    """A sweeping cleave wide enough to fell everything around."""
    c = bg((160, 150, 50), (24, 22, 4), 0.5, 0.6)
    sweep = poly(ribbon(arc(0.5, 0.62, 0.42, 190, 350, 60, 0.30), 0.0, 0.0, 0.14))
    lit(c, sweep, lin((255, 255, 230), (255, 220, 120), 0), (255, 240, 150), 18, 1.3)
    tgt = K.shape(lambda d: [d.ellipse(pts([(x - 0.035, 0.80 - 0.02), (x + 0.035, 0.80 + 0.02)]), fill=255)
                             for x in (0.22, 0.40, 0.60, 0.78)])
    K.fill(c, K.soften(tgt, 3), (40, 30, 0, 160))
    gaxe(c, 0.5, 0.52, 0.72, 80, glowc=(255, 240, 160))
    return K.finish(c)


def ukkos_fury():
    """Ukonvasara: the thunder god's great axe calling down lightning."""
    c = bg((60, 80, 210), (4, 6, 34), 0.5, 0.35)
    cl = K.shape(lambda d: [cloud(d, 0.30, 0.16, 1.0), cloud(d, 0.72, 0.12, 0.9)])
    K.fill(c, cl.filter(ImageFilter.GaussianBlur(8)), (120, 130, 200, 200))
    bl = K.shape(lambda d: [bolt(d, 0.20, 0.10, 0.14, 0.80, 0.045, 11, 6, 0.07),
                            bolt(d, 0.82, 0.10, 0.86, 0.78, 0.04, 12, 6, 0.07),
                            bolt(d, 0.50, 0.04, 0.50, 0.30, 0.04, 13, 3, 0.04)])
    lit(c, bl, (255, 255, 240), (170, 200, 255), 18, 1.7)
    gaxe(c, 0.5, 0.60, 0.78, 0, glowc=(220, 230, 255), gr=22, gs=1.6,
         steel=((255, 255, 255), (120, 140, 200)), trim=GOLDM)
    sparkles(c, [(0.28, 0.40, 0.05), (0.74, 0.46, 0.05)], glowc=(200, 220, 255))
    return K.finish(c)


def upheaval():
    """Chango: the earth heaving up in jagged slabs over molten light as the great axe rises."""
    c = bg((200, 120, 40), (30, 10, 2), 0.5, 0.75)
    lava = K.shape(lambda d: d.rectangle(pts([(0.0, 0.70), (1.0, 1.0)]), fill=255))
    K.glow(c, lava, (255, 150, 40, 255), 30, 1.6)
    K.fill(c, K.soften(lava, 8), lin((255, 230, 120), (255, 110, 20)))
    slabs = K.shape(lambda d: [d.polygon(pts(q), fill=255) for q in (
        [(0.0, 1.0), (0.06, 0.62), (0.24, 0.56), (0.30, 1.0)],
        [(0.70, 1.0), (0.78, 0.54), (0.94, 0.60), (1.0, 1.0)],
        [(0.30, 1.0), (0.34, 0.76), (0.46, 0.80), (0.46, 1.0)],
        [(0.54, 1.0), (0.56, 0.78), (0.68, 0.74), (0.72, 1.0)])])
    K.shadow(c, slabs, 4, 6, 6, 150)
    K.fill(c, K.soften(slabs), lin((150, 100, 60), (40, 20, 10)))
    K.fill(c, K.soften(minus(slabs, ImageChops.offset(slabs, 7, 7)), 1.5), (255, 220, 160, 170))
    rocks(c, [(0.18, 0.36, 0.045), (0.84, 0.30, 0.04), (0.28, 0.18, 0.03), (0.72, 0.14, 0.032)], seed=51,
          glowc=(255, 150, 60))
    gaxe(c, 0.5, 0.46, 0.74, 0, glowc=(255, 210, 130), gr=18, gs=1.4, trim=GOLDM,
         steel=((255, 250, 235), (150, 120, 90)))
    return K.finish(c)


def disaster():
    """A falling star of ruin: a blazing meteor plunging behind the great axe."""
    c = bg((150, 30, 20), (16, 2, 2), 0.3, 0.3)
    tail = poly(ribbon([(0.95 - t * 0.6, 0.05 + t * 0.5) for t in [i / 20 for i in range(21)]], 0.02, 0.18))
    K.glow(c, tail, (255, 120, 40, 255), 20, 1.2)
    K.fill(c, K.soften(tail, 6), lin((255, 120, 40, 120), (255, 230, 150, 255), 135))
    core = K.shape(lambda d: d.ellipse(pts([(0.26, 0.46), (0.44, 0.64)]), fill=255))
    lit(c, core, rad((255, 255, 230), (255, 160, 60), 0.35, 0.55, 0.09), (255, 180, 80), 20, 1.5)
    gaxe(c, 0.56, 0.58, 0.74, 25, glowc=(255, 160, 100))
    motes(c, 61, 14, (0.12, 0.10, 0.80, 0.80), (0.006, 0.013), (255, 220, 160), (255, 120, 40))
    return K.finish(c)


# ---- scythe ---------------------------------------------------------------------------------------------------------
def slice_():
    """One clean reaping cut."""
    c = bg((50, 130, 80), (2, 18, 8))
    scy(c, glowc=(180, 255, 200))
    m = poly(ribbon(arc(0.10, 0.20, 0.66, 18, 72, 40), 0.0, 0.0, 0.11))
    K.glow(c, m, (130, 255, 170, 255), 16, 1.4)
    K.fill(c, scale(K.soften(m), 0.9), (245, 255, 245, 255))
    return K.finish(c)


def wheat(d, x, y0, h, lean, fillv=255):
    d.line(pts([(x, y0), (x + lean, y0 - h)]), fill=fillv, width=int(0.016 * W))
    for k in range(5):
        t = 0.58 + k * 0.085
        cx, cy = x + lean * t, y0 - h * t
        for sgn in (-1, 1):
            d.polygon(pts(ribbon([(cx, cy), (cx + sgn * 0.045, cy - 0.05)], 0.034, 0.008)), fill=fillv)
    d.polygon(pts(ribbon([(x + lean, y0 - h + 0.01), (x + lean * 1.05, y0 - h - 0.06)], 0.03, 0.0)), fill=fillv)


def dark_harvest():
    """The scythe sweeping through a field of shadow-wheat."""
    c = bg((110, 50, 150), (12, 2, 22), 0.5, 0.75)
    wh = K.shape(lambda d: [wheat(d, x, 1.0, h, l) for x, h, l in ((0.16, 0.46, 0.04), (0.34, 0.54, -0.02),
                                                                   (0.54, 0.44, 0.04), (0.74, 0.50, -0.04))])
    K.glow(c, wh, (220, 120, 255, 255), 10, 1.2)
    K.fill(c, K.soften(wh), lin((250, 220, 160), (150, 70, 170)))
    scy(c, 0.62, 0.52, 0.80, 18, glowc=(220, 160, 255), steel=((230, 220, 245), (80, 60, 110)))
    return K.finish(c)


def hood(d, cx, cy, s, fillv=255):
    q = [(0, -0.42), (0.20, -0.30), (0.28, 0.0), (0.36, 0.44), (-0.36, 0.44), (-0.28, 0.0), (-0.20, -0.30)]
    d.polygon(xf(q, cx, cy, s), fill=fillv)


def shadow_of_death():
    """A hooded death-shadow looming beside the scythe, its eyes burning."""
    c = bg((150, 40, 130), (14, 2, 14), 0.4, 0.6)
    X, Y, S0 = 0.36, 0.62, 0.86
    h = K.shape(lambda d: hood(d, X, Y, S0))
    K.glow(c, h, (255, 80, 220, 255), 18, 1.2)
    K.fill(c, K.soften(h, 3), lin((50, 14, 50), (6, 0, 8)))
    face = K.shape(lambda d: d.polygon(xf(ell(0, -0.16, 0.13, 0.15), X, Y, S0), fill=255))
    K.fill(c, K.soften(face, 6), (0, 0, 0, 240))
    eyes = K.shape(lambda d: [d.polygon(xf(ell(sx, -0.17, 0.035, 0.022), X, Y, S0), fill=255) for sx in (-0.06, 0.06)])
    lit(c, eyes, (255, 230, 250), (255, 60, 200), 8, 2.0)
    scy(c, 0.64, 0.56, 0.86, 15, glowc=(255, 120, 230), gs=1.6, steel=((255, 240, 255), (150, 110, 170)),
        wood=((190, 130, 80), (90, 50, 30)), keyline=True)
    return K.finish(c)


def eye_shape(d, cx, cy, rx, ry, fillv=255):
    up = [(cx - rx + 2 * rx * i / 30, cy - ry * math.sin(math.pi * i / 30)) for i in range(31)]
    dn = [(cx + rx - 2 * rx * i / 30, cy + ry * math.sin(math.pi * i / 30)) for i in range(31)]
    d.polygon(pts(up + dn), fill=fillv)


def nightmare_scythe():
    """A baleful eye opening in the dark above the scythe (blindness)."""
    c = bg((40, 40, 120), (2, 2, 18), 0.5, 0.3)
    e = K.shape(lambda d: eye_shape(d, 0.42, 0.28, 0.26, 0.12))
    K.glow(c, e, (170, 120, 255, 255), 18, 1.4)
    K.fill(c, K.soften(e), lin((240, 230, 255), (170, 150, 220)))
    iris = K.shape(lambda d: d.ellipse(pts([(0.35, 0.21), (0.49, 0.35)]), fill=255))
    K.fill(c, K.soften(inter(iris, e)), rad((255, 80, 120), (120, 0, 60), 0.42, 0.28, 0.07))
    pupil = K.shape(lambda d: d.ellipse(pts([(0.41, 0.215), (0.43, 0.345)]), fill=255))
    K.fill(c, K.soften(pupil), (10, 0, 10, 255))
    scy(c, 0.64, 0.66, 0.74, 15, glowc=(170, 140, 255), steel=((220, 220, 250), (70, 70, 120)))
    return K.finish(c)


def spinning_scythe():
    """The scythe whirled through a full circle."""
    c = bg((40, 140, 140), (2, 20, 22))
    trail = poly(ribbon(arc(0.5, 0.5, 0.38, 100, 420, 60), 0.0, 0.11))
    lit(c, trail, lin((240, 255, 255), (120, 230, 220), 0), (130, 255, 240), 16, 1.3)
    scy(c, 0.58, 0.56, 0.74, 60, glowc=(180, 255, 245))
    return K.finish(c)


def vorpal_scythe():
    """A vorpal gleam: a blinding star on the scythe's edge (critical hits)."""
    c = bg((60, 110, 200), (4, 10, 36))
    m = scy(c, 0.62, 0.62, 0.84, 18, glowc=(200, 230, 255), edgec=(255, 255, 255, 255))
    K.glow(c, inter(m['edge'], m['metal']), (170, 220, 255, 255), 8, 1.6)
    sparkles(c, [(0.30, 0.34, 0.13), (0.62, 0.20, 0.05)], glowc=(170, 220, 255))
    return K.finish(c)


def guillotine():
    """Four falling cuts and a hush (silence): the scythe over grey-crimson."""
    c = bg((140, 50, 60), (18, 4, 8))
    for x in (0.20, 0.36, 0.52, 0.68):
        line_slash(c, x + 0.06, 0.10, x - 0.06, 0.62, 0.035, (255, 235, 235), (255, 90, 100), 8)
    scy(c, 0.62, 0.60, 0.80, 12, glowc=(255, 160, 160), steel=((245, 240, 245), (110, 100, 115)))
    return K.finish(c)


def cross_reaper():
    """Two scythes crossed in an X, a red crossing slash behind them."""
    c = bg((170, 30, 50), (20, 2, 6))
    line_slash(c, 0.14, 0.14, 0.86, 0.86, 0.07, (255, 230, 230), (255, 60, 80), 14)
    line_slash(c, 0.86, 0.14, 0.14, 0.86, 0.07, (255, 230, 230), (255, 60, 80), 14)
    scy(c, 0.58, 0.58, 0.72, 35, glowc=(255, 150, 160))
    # the mirrored scythe: the right-hand one flipped
    flip = weapon_masks('scythe', 0.58, 0.58, 0.72, 35)
    for k in flip:
        flip[k] = flip[k].transpose(Image.FLIP_LEFT_RIGHT)
    K.shadow(c, flip['all'], 6, 9, 9, 170)
    K.fill(c, K.soften(flip['wood']), lin(*WOOD))
    K.fill(c, K.soften(flip['metal']), lin(STEEL[0], STEEL[1], 60))
    K.fill(c, K.soften(inter(flip['edge'], flip['metal']), 1.5), (255, 255, 255, 170))
    K.fill(c, K.soften(flip['trim']), lin(*TRIM))
    metal = union(flip['metal'], flip['trim'])
    K.fill(c, scale(K.soften(minus(metal, ImageChops.offset(metal, 5, 5)), 1.5), 0.55), (255, 255, 255, 255))
    return K.finish(c)


def spiral_hell():
    """A hellish red spiral swallowing everything, the scythe at its edge."""
    c = bg((160, 40, 110), (14, 2, 10))
    sp = K.mask()
    sd = ImageDraw.Draw(sp)
    for arm in range(2):
        path = []
        for i in range(60):
            t = i / 59
            a = arm * math.pi + t * 4.4
            r = 0.02 + 0.40 * t
            path.append((0.48 + math.cos(a) * r, 0.48 + math.sin(a) * r))
        sd.polygon(pts(ribbon(path, 0.01, 0.09)), fill=255)
    K.glow(c, sp, (255, 60, 120, 255), 14, 1.2)
    K.fill(c, K.soften(sp), rad((255, 220, 200), (200, 20, 60), 0.48, 0.48, 0.42))
    hole = K.shape(lambda d: d.ellipse(pts([(0.42, 0.42), (0.54, 0.54)]), fill=255))
    K.fill(c, K.soften(hole, 6), (10, 0, 6, 255))
    scy(c, 0.62, 0.62, 0.78, 20, glowc=(255, 150, 190))
    return K.finish(c)


def catastrophe():
    """Apocalypse: a great skull of red mist beside the black-and-crimson scythe, draining life."""
    c = bg((180, 20, 30), (16, 0, 2), 0.4, 0.6)
    X, Y, S0 = 0.36, 0.64, 0.88
    sk = K.shape(lambda d: skull(d, X, Y, S0))
    K.glow(c, sk, (255, 40, 40, 255), 24, 1.3)
    K.fill(c, K.soften(sk, 2), lin((130, 14, 24), (40, 0, 6)))
    eyes = K.shape(lambda d: [d.polygon(xf(ell(sx, 0.02, 0.06, 0.065), X, Y, S0), fill=255) for sx in (-0.12, 0.12)])
    lit(c, eyes, (255, 230, 200), (255, 60, 30), 10, 1.8)
    scy(c, 0.64, 0.56, 0.86, 18, glowc=(255, 70, 70), gr=20, gs=1.5,
        steel=((130, 110, 130), (20, 10, 20)), edgec=(255, 60, 60, 240), trim=((230, 60, 60), (100, 0, 10)),
        wood=((60, 40, 50), (14, 6, 10)))
    sparkles(c, [(0.20, 0.26, 0.045)], (255, 220, 220), (255, 80, 80))
    return K.finish(c)


def insurgency():
    """Liberator: the scythe raised before a rising crimson-gold star of revolt."""
    c = bg((130, 30, 110), (14, 2, 18), 0.5, 0.45)
    rays(c, 0.42, 0.40, 16, (255, 200, 230), 0.05, 0.8, 120, 6)
    burst(c, 0.42, 0.40, 0.34, 0.12, 8, (255, 70, 120), (255, 120, 170), 24, 1.4, rot0=-90, inner=(255, 245, 200))
    burst(c, 0.42, 0.40, 0.20, 0.08, 8, (255, 210, 120), (255, 230, 150), 10, 1.0, rot0=-67.5,
          inner=(255, 255, 240))
    scy(c, 0.60, 0.58, 0.86, 18, glowc=(255, 210, 160), gr=20, gs=1.5,
        steel=((240, 225, 255), (70, 40, 100)), trim=GOLDM, wood=((60, 30, 70), (20, 6, 26)))
    sparkles(c, [(0.80, 0.80, 0.04)], glowc=(255, 160, 230))
    return K.finish(c)


def infernal_scythe():
    """A scythe wreathed in violet hellfire (attack down)."""
    c = bg((110, 20, 70), (12, 0, 10), 0.5, 0.7)
    blaze(c, [(0.46, 0.98, 0.22, 0.86, 0.04), (0.18, 0.98, 0.12, 0.56, -0.08), (0.76, 0.98, 0.13, 0.66, 0.08)],
          ((120, 0, 90), (220, 40, 160)), ((220, 50, 150), (255, 130, 200)), ((255, 200, 230), (255, 250, 250)),
          (230, 30, 150))
    scy(c, 0.60, 0.56, 0.80, 18, glowc=(255, 120, 200), steel=((230, 210, 230), (60, 30, 60)))
    return K.finish(c)


def quietus():
    """Redemption: a black eclipse with a pale corona behind the scythe; all falls silent."""
    c = bg((60, 50, 120), (4, 2, 16), 0.42, 0.40)
    rays(c, 0.42, 0.40, 24, (220, 220, 255), 0.03, 0.55, 140, 4, jitter=0.25, seed=7)
    cor = K.shape(lambda d: d.ellipse(pts([(0.18, 0.16), (0.66, 0.64)]), fill=255))
    K.glow(c, cor, (230, 230, 255, 255), 30, 1.6)
    K.fill(c, K.soften(cor, 4), (245, 245, 255, 255))
    sun = K.shape(lambda d: d.ellipse(pts([(0.21, 0.19), (0.63, 0.61)]), fill=255))
    K.fill(c, K.soften(sun, 2), rad((10, 6, 24), (24, 18, 50), 0.40, 0.38, 0.22))
    scy(c, 0.62, 0.60, 0.86, 18, glowc=(220, 220, 255), gr=18, gs=1.4,
        steel=((250, 250, 255), (110, 110, 150)), trim=GOLDM, wood=((50, 40, 70), (14, 10, 24)))
    sparkles(c, [(0.66, 0.16, 0.05)], glowc=(220, 220, 255))
    return K.finish(c)


def entropy():
    """Anguta: a swirling nebula, the scythe's blade dissolving into drifting motes."""
    c = bg((40, 100, 140), (4, 4, 20), 0.45, 0.45)
    neb = K.mask()
    nd = ImageDraw.Draw(neb)
    for arm in range(2):
        path = []
        for i in range(50):
            t = i / 49
            a = arm * math.pi + t * 3.6
            r = 0.04 + 0.40 * t
            path.append((0.46 + math.cos(a) * r, 0.46 + math.sin(a) * r * 0.8))
        nd.polygon(pts(ribbon(path, 0.03, 0.14)), fill=255)
    K.fill(c, neb.filter(ImageFilter.GaussianBlur(12)), (180, 110, 255, 255))
    K.fill(c, scale(neb.filter(ImageFilter.GaussianBlur(3)), 0.7), (170, 255, 245, 255))
    core = K.shape(lambda d: d.ellipse(pts([(0.39, 0.40), (0.53, 0.52)]), fill=255))
    lit(c, core, (255, 255, 255), (200, 240, 255), 20, 1.8)
    scy(c, 0.62, 0.60, 0.86, 18, glowc=(170, 255, 240), gr=18, gs=1.4,
        steel=((230, 255, 255), (60, 110, 140)), trim=((200, 170, 255), (90, 50, 170)),
        wood=((50, 50, 80), (14, 14, 30)))
    rnd = random.Random(71)
    dm = K.mask()
    dd = ImageDraw.Draw(dm)
    for _ in range(16):
        x, y = rnd.uniform(0.08, 0.40), rnd.uniform(0.18, 0.60)
        r = rnd.uniform(0.012, 0.026)
        dd.polygon(pts([(x, y - r), (x + r, y), (x, y + r), (x - r, y)]), fill=255)
    lit(c, dm, (230, 255, 255), (170, 255, 240), 6, 1.6)
    return K.finish(c)


def origin():
    """A new dawn: the scythe against a rising golden sun and the first light."""
    c = bg((60, 140, 160), (4, 16, 30), 0.4, 0.7)
    sun = K.shape(lambda d: d.ellipse(pts([(0.16, 0.50), (0.64, 0.98)]), fill=255))
    rays(c, 0.40, 0.74, 14, (255, 240, 180), 0.07, 0.8, 120, 6, phase=0.12)
    K.glow(c, sun, (255, 220, 120, 255), 30, 1.5)
    K.fill(c, K.soften(sun), rad((255, 255, 230), (255, 180, 70), 0.40, 0.74, 0.24))
    horizon = K.shape(lambda d: d.rectangle(pts([(0, 0.80), (1, 1)]), fill=255))
    K.fill(c, K.soften(horizon, 3), lin((30, 70, 90), (4, 14, 24)))
    scy(c, 0.62, 0.54, 0.82, 18, glowc=(255, 240, 190), steel=((255, 255, 250), (140, 150, 170)), trim=GOLDM)
    sparkles(c, [(0.76, 0.16, 0.05), (0.20, 0.24, 0.035)])
    return K.finish(c)


ICONS = {('ja', n): f for n, f in (
    ('Hard Slash', hard_slash), ('Power Slash', power_slash), ('Frostbite', frostbite), ('Freezebite', freezebite),
    ('Shockwave', shockwave), ('Crescent Moon', crescent_moon), ('Sickle Moon', sickle_moon),
    ('Spinning Slash', spinning_slash), ('Ground Strike', ground_strike), ('Scourge', scourge),
    ('Herculean Slash', herculean_slash), ('Torcleaver', torcleaver), ('Resolution', resolution),
    ('Dimidiation', dimidiation), ('Fimbulvetr', fimbulvetr),
    ('Raging Axe', raging_axe), ('Smash Axe', smash_axe), ('Gale Axe', gale_axe), ('Avalanche Axe', avalanche_axe),
    ('Spinning Axe', spinning_axe), ('Rampage', rampage), ('Calamity', calamity), ('Mistral Axe', mistral_axe),
    ('Decimation', decimation), ('Onslaught', onslaught), ('Primal Rend', primal_rend), ('Bora Axe', bora_axe),
    ('Cloudsplitter', cloudsplitter), ('Ruinator', ruinator), ('Blitz', blitz),
    ('Shield Break', shield_break), ('Iron Tempest', iron_tempest), ('Sturmwind', sturmwind),
    ('Armor Break', armor_break), ('Keen Edge', keen_edge), ('Weapon Break', weapon_break),
    ('Raging Rush', raging_rush), ('Full Break', full_break), ('Steel Cyclone', steel_cyclone),
    ('Metatron Torment', metatron_torment), ("King's Justice", kings_justice), ('Fell Cleave', fell_cleave),
    ("Ukko's Fury", ukkos_fury), ('Upheaval', upheaval), ('Disaster', disaster),
    ('Slice', slice_), ('Dark Harvest', dark_harvest), ('Shadow of Death', shadow_of_death),
    ('Nightmare Scythe', nightmare_scythe), ('Spinning Scythe', spinning_scythe), ('Vorpal Scythe', vorpal_scythe),
    ('Guillotine', guillotine), ('Cross Reaper', cross_reaper), ('Spiral Hell', spiral_hell),
    ('Catastrophe', catastrophe), ('Insurgency', insurgency), ('Infernal Scythe', infernal_scythe),
    ('Quietus', quietus), ('Entropy', entropy), ('Origin', origin))}
COVERS = {}
VARIANTS = {}
