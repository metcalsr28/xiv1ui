"""Signature icons, round 2: polearm, katana, great katana and club weapon skills.

Each weapon type has its own silhouette (a lance, a short ninja katana, a long tachi, a flanged mace) and each weapon
skill dresses it in its element or effect; the relic / mythic / empyrean / aeonic skills get their own scenes.
"""
import math
import random
from functools import reduce

from PIL import ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_c as GC
import group_d as GD

W = K.W
p, pts, mask, shape, fill, glow, shadow, soften, radial, linear, sparkle, finish = (
    K.p, K.pts, K.mask, K.shape, K.fill, K.glow, K.shadow, K.soften, K.radial, K.linear, K.sparkle, K.finish)
frame = GC.frame
brush = GD.stroke          # brush(d, path, w0, w1): discs along a polyline
poly, ell, scale, minus, inter, rot = GD.poly, GD.ell, GD.scale, GD.minus, GD.inter, GD.rot


# ---- small helpers ---------------------------------------------------------------------------------------------------
def col(c):
    return c + (255,) if len(c) == 3 else c


def paint(v, angle=90):
    """A colour (r, g, b) or a gradient pair ((r, g, b), (r, g, b)) as a fill paint."""
    if isinstance(v[0], tuple):
        return linear(col(v[0]), col(v[1]), angle)
    return col(v)


def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return radial(col(c0), col(c1), cx, cy, r)


def union(*ms):
    return reduce(ImageChops.lighter, ms)


def lit(c, m, color, glowc=None, gr=14, gs=1.2, sh=False, soft=1.2, angle=90):
    if glowc:
        glow(c, m, col(glowc), gr, gs)
    if sh:
        shadow(c, m, 4, 7, 6, 140)
    fill(c, soften(m, soft), paint(color, angle))


def tstroke(curve, w, profile='both'):
    """A stroke polygon along `curve` whose width swells: 'both' tapers at both ends, 'end' only at the end,
    'start' only at the start."""
    n = len(curve)
    left, right = [], []
    for i, (x, y) in enumerate(curve):
        a, b = curve[max(0, i - 1)], curve[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        t = i / max(1, n - 1)
        if profile == 'both':
            k = math.sin(math.pi * t) ** 0.7
        elif profile == 'end':
            k = (1 - t) ** 0.8
        else:
            k = t ** 0.8
        hw = w * k / 2
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    return left + right[::-1]


def slash(c, curve, w, color=(255, 255, 255), glowc=(255, 255, 255), gr=12, gs=1.3, profile='both'):
    m = poly(tstroke(curve, w, profile))
    lit(c, m, color, glowc, gr, gs)


def arc(cx, cy, r, a0, a1, n=48, ry=None):
    return GC.arc(cx, cy, r, a0, a1, n, ry)


def bolt_path(seed, x0, y0, x1, y1, n=7, jag=0.05):
    """A zigzag from (x0, y0) to (x1, y1): alternate kinks of about `jag` across the line."""
    rnd = random.Random(seed)
    L, f = frame(x0, y0, x1, y1)
    out = [(x0, y0)]
    for i in range(1, n):
        side = 1 if i % 2 else -1
        out.append(f(L * (i + rnd.uniform(-0.25, 0.25)) / n, side * jag * rnd.uniform(0.6, 1.2)))
    out.append((x1, y1))
    return out


def lightning(c, paths, w=0.03, glowc=(190, 150, 255), core=(255, 255, 236), gr=14, gs=1.5):
    m = shape(lambda d: [brush(d, path, w * 1.4, w * 0.5) for path in paths])
    glow(c, m, col(glowc), gr * 1.6, gs)
    glow(c, m, col(glowc), gr * 0.5, 1.6)
    fill(c, soften(m), col(core))


def motes(c, seed, n, box, rr, color, glowc=None, alpha=230):
    GD.motes(c, seed, n, box, rr, color, glowc, alpha)


def sparkles(c, spots, color=(255, 255, 255), glowc=(255, 255, 230)):
    GD.sparkles(c, spots, color, glowc)


def rays(c, cx, cy, n, color, width=0.05, length=0.75, alpha=90, blur=8, phase=0.0):
    GD.rays(c, cx, cy, n, color, width, length, alpha, blur, phase)


def smoke(c, seed, n, box, rr, color, alpha=120, blur=14):
    rnd = random.Random(seed)
    m = mask()
    d = ImageDraw.Draw(m)
    for _ in range(n):
        x, y, r = rnd.uniform(box[0], box[2]), rnd.uniform(box[1], box[3]), rnd.uniform(*rr)
        d.ellipse(pts([(x - r, y - r * 0.7), (x + r, y + r * 0.7)]), fill=alpha)
    fill(c, m.filter(ImageFilter.GaussianBlur(blur)), col(color))


def flames(c, specs, outer=((255, 210, 80), (230, 60, 20)), inner=((255, 245, 170), (255, 150, 40)),
           glowc=(255, 110, 30), gr=24, gs=1.2, inner_k=0.6):
    """Flames: specs are (cx, base, w, h, lean)."""
    o = shape(lambda d: [GA.flame(d, *s) for s in specs])
    i = shape(lambda d: [GA.flame(d, s[0], s[1], s[2] * inner_k, s[3] * 0.7, s[4] * 0.7) for s in specs])
    glow(c, o, col(glowc), gr, gs)
    fill(c, soften(o), paint(outer, 270))
    fill(c, soften(i), paint(inner, 270))


def wave_path(x0, x1, y, amp, cycles, phase=0.0, n=60):
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin(phase + 2 * math.pi * cycles * i / n)) for i in range(n + 1)]


def spiral(cx, cy, r0, r1, a0, a1, n=80, squash=1.0):
    out = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        r = r0 + (r1 - r0) * t
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r * squash))
    return out


def shard(d, cx, cy, length, ang, w, fillv=255):
    a = math.radians(ang)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    d.polygon(pts([(cx - ux * length * 0.35, cy - uy * length * 0.35),
                   (cx + nx * w, cy + ny * w),
                   (cx + ux * length * 0.65, cy + uy * length * 0.65),
                   (cx - nx * w, cy - ny * w)]), fill=fillv)


def star_poly(cx, cy, n, r1, r2, rot0=-90):
    return GA.star_pts(cx, cy, n, r1, r2, math.radians(rot0))


# ---- weapons (each returns a dict of masks; `arm` paints them) -------------------------------------------------------
STEEL = ((255, 255, 255), (150, 164, 192))
GOLD = ((255, 236, 170), (196, 130, 46))
WRAP = ((70, 50, 64), (20, 14, 22))
WOOD = ((150, 96, 60), (70, 40, 26))


def katana_m(x0, y0, x1, y1, curve=0.03, hilt=0.27, bw=0.040, tw=0.072):
    """A katana from the pommel (x0, y0) to the tip (x1, y1); blade bows toward +v (the edge side)."""
    L, f = frame(x0, y0, x1, y1)
    h = hilt * L
    top, bot, edge = [], [], []
    n = 30
    for i in range(n + 1):
        t = i / n
        u = h + 0.016 + (L - h - 0.016) * t
        bow = curve * t * t
        half = bw * (1 - 0.25 * t)
        if t > 0.84:
            half *= max(0.0, (1 - t) / 0.16) ** 0.8
        top.append(f(u, bow - half))
        bot.append(f(u, bow + half * 1.15))
        edge.append(f(u, bow + half * 0.45))
    return {
        'grip': poly([f(0, -bw * 0.80), f(h, -bw * 0.88), f(h, bw * 0.88), f(0, bw * 0.80)]),
        'blade': poly(top + bot[::-1]),
        'edge': poly(edge + bot[::-1]),
        'guard': union(poly([f(h - 0.012, -tw), f(h + 0.018, -tw), f(h + 0.018, tw), f(h - 0.012, tw)]),
                       poly([f(-0.012, -bw * 0.9), f(0.016, -bw * 0.9), f(0.016, bw * 0.9), f(-0.012, bw * 0.9)])),
    }


def ninjato(x0, y0, x1, y1, curve=0.018):
    """The ninja's short katana: shorter grip, square guard, a gentle curve."""
    return katana_m(x0, y0, x1, y1, curve=curve, hilt=0.26, bw=0.042, tw=0.068)


def tachi(x0, y0, x1, y1, curve=0.06):
    """The great katana: long, slender, deeply curved."""
    return katana_m(x0, y0, x1, y1, curve=curve, hilt=0.25, bw=0.034, tw=0.062)


def spear_m(x0, y0, x1, y1, w=0.046, head='leaf', hl=0.29):
    """A lance from the butt (x0, y0) to the point (x1, y1)."""
    L, f = frame(x0, y0, x1, y1)
    hb = L - hl
    m = {'shaft': poly([f(0, -w / 2), f(hb, -w / 2), f(hb, w / 2), f(0, w / 2)]),
         'guard': union(poly([f(hb - 0.045, -w * 0.95), f(hb + 0.012, -w * 0.95), f(hb + 0.012, w * 0.95),
                              f(hb - 0.045, w * 0.95)]),
                        poly([f(-0.01, -w * 0.7), f(0.035, -w * 0.7), f(0.035, w * 0.7), f(-0.01, w * 0.7)]))}
    if head == 'leaf':
        hd = poly([f(hb, -0.03), f(hb + hl * 0.32, -0.085), f(L, 0), f(hb + hl * 0.32, 0.085), f(hb, 0.03)])
    elif head == 'broad':
        hd = union(poly([f(hb, -0.03), f(hb + hl * 0.30, -0.10), f(L, 0), f(hb + hl * 0.30, 0.10), f(hb, 0.03)]),
                   poly([f(hb - 0.02, -0.03), f(hb + 0.03, -0.13), f(hb + 0.05, -0.03)]),
                   poly([f(hb - 0.02, 0.03), f(hb + 0.03, 0.13), f(hb + 0.05, 0.03)]))
    elif head == 'gungnir':
        hd = union(poly([f(hb, -0.03), f(hb + hl * 0.24, -0.07), f(L, 0), f(hb + hl * 0.24, 0.07), f(hb, 0.03)]),
                   *[poly([f(hb + 0.01, s * 0.02), f(hb + 0.04, s * 0.06), f(hb - 0.03, s * 0.15), f(hb - 0.05, s * 0.13),
                           f(hb - 0.03, s * 0.02)]) for s in (-1, 1)])
    elif head == 'trident':
        side = []
        for s in (-1, 1):
            side.append(poly(GC.stroke([f(hb + 0.01, 0), f(hb + 0.02, s * 0.08), f(hb + 0.08, s * 0.11),
                                        f(L - 0.09, s * 0.10)], 0.034, 0.012)))
            side.append(poly([f(L - 0.12, s * 0.10 - 0.025), f(L - 0.05, s * 0.105), f(L - 0.12, s * 0.10 + 0.025)]))
        hd = union(poly([f(hb, -0.022), f(hb + hl * 0.4, -0.05), f(L, 0), f(hb + hl * 0.4, 0.05), f(hb, 0.022)]),
                   *side)
    elif head == 'dragon':
        hd = union(poly([f(hb, -0.03), f(hb + hl * 0.35, -0.085), f(L, 0), f(hb + hl * 0.35, 0.085), f(hb, 0.03)]),
                   poly([f(hb + 0.02, -0.03), f(hb - 0.07, -0.12), f(hb - 0.03, -0.03)]),
                   poly([f(hb + 0.02, 0.03), f(hb - 0.07, 0.12), f(hb - 0.03, 0.03)]))
    m['head'] = hd
    return m


def mace_m(x0, y0, x1, y1, r=0.12, head='flanged', hw=0.040):
    """A club from the butt (x0, y0) to its head's centre (x1, y1)."""
    L, f = frame(x0, y0, x1, y1)
    cx, cy = x1, y1
    m = {'grip': poly([f(0, -hw / 2), f(L - r * 0.5, -hw / 2), f(L - r * 0.5, hw / 2), f(0, hw / 2)])}
    pom = ell(x0 - hw * 0.9, y0 - hw * 0.9, x0 + hw * 0.9, y0 + hw * 0.9)
    band = poly([f(L - r * 1.25, -hw * 0.95), f(L - r * 0.95, -hw * 0.95), f(L - r * 0.95, hw * 0.95),
                 f(L - r * 1.25, hw * 0.95)])
    m['guard'] = union(pom, band)
    if head == 'flanged':
        # a flanged mace seen from the side: side flanges (darker) behind a bright front flange and a spike
        m['fins'] = union(*[poly([f(L - r * 1.05, s * r * 0.15), f(L - r * 0.75, s * r * 0.78),
                                  f(L - r * 0.25, s * r * 0.62), f(L + r * 0.30, s * r * 0.80),
                                  f(L + r * 1.0, s * r * 0.15)]) for s in (-1, 1)])
        m['head'] = poly([f(L - r * 1.15, 0), f(L - r * 0.3, -r * 0.26), f(L + r * 0.9, -r * 0.20), f(L + r * 1.6, 0),
                          f(L + r * 0.9, r * 0.20), f(L - r * 0.3, r * 0.26)])
        m['edge'] = poly([f(L - r * 0.7, -r * 0.03), f(L + r * 1.4, -r * 0.01), f(L + r * 1.4, r * 0.03),
                          f(L - r * 0.7, r * 0.08)])
    elif head == 'spiked':
        m['head'] = union(poly(star_poly(cx, cy, 8, r, r * 0.66, 0)), ell(cx - r * 0.7, cy - r * 0.7, cx + r * 0.7,
                                                                           cy + r * 0.7))
    elif head == 'hammer':
        # Mjollnir-like: a stout block whose striking faces flare, gold-banded near each face
        m['head'] = poly([f(L - r * 0.62, -r * 1.12), f(L + r * 0.62, -r * 1.12), f(L + r * 0.50, -r * 0.9),
                          f(L + r * 0.50, r * 0.9), f(L + r * 0.62, r * 1.12), f(L - r * 0.62, r * 1.12),
                          f(L - r * 0.50, r * 0.9), f(L - r * 0.50, -r * 0.9)])
        m['guard'] = union(m['guard'], *[poly([f(L - r * 0.52, s * r * 0.62), f(L + r * 0.52, s * r * 0.62),
                                               f(L + r * 0.52, s * r * 0.78), f(L - r * 0.52, s * r * 0.78)])
                                         for s in (-1, 1)],
                           ell(cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2))
    elif head == 'orb':
        m['head'] = ell(cx - r * 0.75, cy - r * 0.75, cx + r * 0.75, cy + r * 0.75)
        m['guard'] = union(m['guard'], poly(GC.stroke(arc(cx, cy, r * 0.95, 0, 360, 60), 0.022, 0.022)))
    return m


def arm(c, m, glowc=None, gr=14, gs=1.2, sh=True, blade=STEEL, grip=WRAP, guard=GOLD, edge=(255, 255, 255, 150),
        angle=0, shaft=None, keyline=False):
    """Paint a weapon's masks: glow and shadow under the whole, then grip/shaft, fins, blade/head, edge, guard.
    keyline: a dark outline first, so a slim weapon separates from a busy field at bar size."""
    whole = union(*m.values())
    if glowc:
        glow(c, whole, col(glowc), gr, gs)
    if sh:
        shadow(c, whole, 4, 7, 6, 140)
    if keyline:
        fill(c, soften(whole.filter(ImageFilter.MaxFilter(9)), 2), (14, 10, 24, 235))
    if 'grip' in m:
        fill(c, soften(m['grip']), paint(grip, angle))
    if 'shaft' in m:
        fill(c, soften(m['shaft']), paint(shaft or WOOD, angle))
    if 'fins' in m:
        lo = blade[1] if isinstance(blade[0], tuple) else blade
        hi = blade[0] if isinstance(blade[0], tuple) else blade
        fill(c, soften(m['fins'].filter(ImageFilter.MaxFilter(7)), 2), (20, 16, 30, 220))
        fill(c, soften(m['fins']), paint((tuple(int(v * 0.9) for v in hi[:3]), tuple(int(v * 0.62) for v in lo[:3])),
                                         angle))
        fill(c, soften(m['head'].filter(ImageFilter.MaxFilter(11)), 2), (20, 16, 30, 230))
    for k in ('blade', 'head'):
        if k in m:
            fill(c, soften(m[k]), paint(blade, angle))
    if 'edge' in m and edge:
        fill(c, soften(m['edge']), col(edge))
    if 'guard' in m:
        fill(c, soften(m['guard']), paint(guard, angle))
    return whole


# ---- element / effect motifs ----------------------------------------------------------------------------------------
def ice_shards(c, spec, glowc=(150, 220, 255)):
    m = shape(lambda d: [shard(d, *s) for s in spec])
    glow(c, m, col(glowc), 14, 1.3)
    fill(c, soften(m), linear((250, 254, 255, 255), (130, 200, 245, 255), 90))
    hi = shape(lambda d: [shard(d, x - 0.006, y - 0.006, l * 0.6, a, w * 0.35) for x, y, l, a, w in spec])
    fill(c, soften(hi, 2), (255, 255, 255, 200))


def rocks(c, spec, glowc=(220, 160, 80)):
    """Jagged earth spires: spec (cx, base, w, h)."""
    def draw(d):
        for cx, base, w, h in spec:
            d.polygon(pts([(cx - w, base), (cx - w * 0.6, base - h * 0.55), (cx - w * 0.15, base - h),
                           (cx + w * 0.35, base - h * 0.7), (cx + w, base)]), fill=255)
    m = shape(draw)
    glow(c, m, col(glowc), 12, 1.0)
    fill(c, soften(m), linear((236, 190, 120, 255), (110, 70, 38, 255), 90))
    lights = shape(lambda d: [d.polygon(pts([(cx - w * 0.6, base - h * 0.55), (cx - w * 0.15, base - h),
                                             (cx - w * 0.05, base - h * 0.4), (cx - w * 0.5, base)]), fill=255)
                              for cx, base, w, h in spec])
    fill(c, soften(lights).point(lambda v: int(v * 0.5)), (255, 230, 180, 255))


def gust(c, paths, w=0.04, color=(220, 255, 230), glowc=(120, 240, 150)):
    m = shape(lambda d: [d.polygon(pts(tstroke(path, w, 'both')), fill=255) for path in paths])
    glow(c, m, col(glowc), 12, 1.3)
    fill(c, soften(m), col(color))


def water_band(c, paths, w=0.06, color=((220, 245, 255), (60, 140, 230)), glowc=(90, 170, 255)):
    m = shape(lambda d: [d.polygon(pts(tstroke(path, w, 'both')), fill=255) for path in paths])
    glow(c, m, col(glowc), 14, 1.2)
    fill(c, soften(m), paint(color, 90))


def dark_aura(c, cx, cy, r, core=(40, 0, 50), glowc=(170, 60, 220)):
    m = ell(cx - r, cy - r, cx + r, cy + r)
    glow(c, m, col(glowc), 30, 1.3)
    fill(c, soften(m, 10), radial(col(core), (110, 30, 150, 255), cx, cy, r * 1.1))


def stun_stars(c, cx, cy, rx, ry, n=4, s=0.05, color=(255, 236, 120), phase=0):
    ring = shape(lambda d: d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255,
                                     width=int(0.012 * W)))
    fill(c, soften(ring, 2).point(lambda v: int(v * 0.55)), col(color))
    m = shape(lambda d: [GD.star(d, cx + math.cos(math.radians(phase + 360 * i / n)) * rx,
                                 cy + math.sin(math.radians(phase + 360 * i / n)) * ry, s, s * 0.45)
                         for i in range(n)])
    glow(c, m, col(color), 8, 1.3)
    fill(c, soften(m), col(color))


def moon(c, cx, cy, r, off=(0.38, -0.22), color=((255, 255, 240), (220, 220, 200)), glowc=(220, 230, 255), gr=22):
    full = ell(cx - r, cy - r, cx + r, cy + r)
    bite = ell(cx - r + off[0] * r * 2, cy - r + off[1] * r * 2, cx + r + off[0] * r * 2, cy + r + off[1] * r * 2)
    m = minus(full, bite) if off else full
    lit(c, m, color, glowc, gr, 1.3)
    return m


def impact(c, cx, cy, r, color=(255, 240, 200), glowc=(255, 200, 120), n=8, inner=0.4):
    m = poly(star_poly(cx, cy, n, r, r * inner, -90 + 180 / n))
    lit(c, m, color, glowc, 16, 1.4)


# ======================================================================================================================
# POLEARM
# ======================================================================================================================
def double_thrust():
    c = bg((40, 120, 170), (4, 18, 34))
    streaks = shape(lambda d: [brush(d, [(x0, y0), (x0 + 0.30, y0 - 0.30)], 0.012, 0.03)
                               for x0, y0 in ((0.06, 0.62), (0.20, 0.78), (0.30, 0.92))])
    fill(c, soften(streaks, 4).point(lambda v: int(v * 0.6)), (200, 240, 255, 255))
    arm(c, spear_m(0.08, 0.70, 0.66, 0.12, w=0.066, hl=0.32), (160, 220, 255), angle=0,
        blade=((220, 240, 255), (110, 140, 190)), shaft=((150, 104, 70), (70, 40, 24)), keyline=True)
    arm(c, spear_m(0.30, 0.94, 0.88, 0.36, w=0.066, hl=0.32), (200, 240, 255), angle=0, keyline=True)
    sparkles(c, [(0.66, 0.12, 0.09), (0.88, 0.36, 0.11)], glowc=(170, 230, 255))
    return finish(c)


def zbolt(cx, cy, h, ang=0.0, w=1.0):
    """A bold lightning-bolt glyph (sharp zigzag, wide at the top, a needle point at the bottom), height h, turned
    clockwise by ang degrees."""
    q = [(0.02, -0.50), (0.24, -0.50), (0.08, -0.10), (0.24, -0.10), (-0.14, 0.50), (-0.02, 0.04), (-0.18, 0.04)]
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return poly([(cx + (x * w * ca - y * sa) * h, cy + (x * w * sa + y * ca) * h) for x, y in q])


def thunder_thrust():
    """A lance thrust flanked by two bold, jagged thunderbolts."""
    c = bg((60, 70, 190), (6, 6, 34))
    bolts = union(zbolt(0.27, 0.32, 0.46, -12), zbolt(0.73, 0.66, 0.46, -12))
    glow(c, bolts, (170, 150, 255, 255), 22, 1.5)
    glow(c, bolts, (220, 210, 255, 255), 7, 1.4)
    fill(c, soften(bolts), linear((255, 255, 236, 255), (255, 226, 120, 255), 90))
    arm(c, spear_m(0.16, 0.88, 0.82, 0.20), (230, 220, 255), angle=0)
    sparkles(c, [(0.82, 0.20, 0.11)], color=(255, 250, 210), glowc=(230, 210, 255))
    return finish(c)


def raiden_thrust():
    c = bg((120, 50, 180), (12, 0, 30), 0.5, 0.3, 0.8)
    smoke(c, 9, 10, (0.05, 0.02, 0.95, 0.2), (0.10, 0.18), (30, 20, 60), 220, 10)
    lightning(c, [bolt_path(11, 0.26, 0.10, 0.20, 0.84, 6, 0.07), bolt_path(12, 0.74, 0.08, 0.82, 0.78, 6, 0.07),
                  bolt_path(14, 0.26, 0.40, 0.10, 0.58, 2, 0.03), bolt_path(15, 0.76, 0.40, 0.92, 0.52, 2, 0.03)],
              0.04, (210, 150, 255), (255, 255, 230), 14, 1.6)
    arm(c, spear_m(0.50, 0.94, 0.50, 0.12), (255, 240, 170), 16, 1.4)
    sparkles(c, [(0.50, 0.12, 0.12)], color=(255, 255, 230), glowc=(255, 230, 140))
    return finish(c)


def leg_sweep():
    c = bg((190, 110, 50), (30, 12, 6), 0.5, 0.55)
    sweep = poly(tstroke(arc(0.5, 0.50, 0.38, 20, 165, 50, 0.30), 0.12, 'start'))
    lit(c, sweep, ((255, 250, 220), (255, 170, 80)), (255, 170, 80), 14, 1.3)
    arm(c, spear_m(0.08, 0.60, 0.92, 0.60, w=0.07, hl=0.32), (255, 220, 150), angle=0, keyline=True)
    stun_stars(c, 0.5, 0.28, 0.22, 0.07, 3, 0.07, (255, 245, 160), -90)
    return finish(c)


def penta_thrust():
    """Five lances thrust out at once in a fan."""
    c = bg((180, 40, 50), (24, 4, 8), 0.5, 0.45)
    cx, cy = 0.5, 0.98
    for a in (-148, -32, -122, -58):
        x1, y1 = cx + math.cos(math.radians(a)) * 0.72, cy + math.sin(math.radians(a)) * 0.72
        arm(c, spear_m(cx, cy, x1, y1, w=0.036, hl=0.24), (255, 140, 120), 8, 1.0, angle=0,
            blade=((255, 220, 210), (170, 110, 120)), shaft=((110, 50, 40), (50, 20, 16)))
    arm(c, spear_m(cx, cy, 0.5, 0.10), (255, 200, 160), 14, 1.3, angle=90)
    sparkles(c, [(0.5, 0.10, 0.09)], glowc=(255, 180, 160))
    return finish(c)


def vorpal_thrust():
    c = bg((100, 10, 30), (12, 0, 6), 0.62, 0.38, 0.8)
    rays(c, 0.62, 0.38, 14, (255, 140, 140), 0.05, 0.8, 80, 6)
    impact(c, 0.62, 0.38, 0.30, (255, 236, 220), (255, 70, 70), 4, 0.16)
    arm(c, spear_m(0.12, 0.88, 0.64, 0.36, head='broad'), (255, 120, 120), angle=0)
    sparkles(c, [(0.64, 0.36, 0.10)], glowc=(255, 160, 160))
    return finish(c)


def skewer():
    c = bg((60, 140, 70), (6, 24, 10))
    rings = [(0.36, 0.60), (0.52, 0.48), (0.68, 0.36)]
    for x, y in rings:
        back = shape(lambda d, x=x, y=y: d.arc(pts([(x - 0.07, y - 0.10), (x + 0.07, y + 0.10)]), 90, 270,
                                                fill=255, width=int(0.03 * W)))
        lit(c, back, ((200, 255, 190), (90, 170, 80)), (160, 255, 150), 8)
    arm(c, spear_m(0.12, 0.78, 0.88, 0.20, w=0.066, hl=0.32), (210, 255, 200), angle=0, keyline=True)
    for x, y in rings:
        front = shape(lambda d, x=x, y=y: d.arc(pts([(x - 0.07, y - 0.10), (x + 0.07, y + 0.10)]), 270, 450,
                                                 fill=255, width=int(0.03 * W)))
        lit(c, front, ((230, 255, 210), (120, 200, 100)), None)
    return finish(c)


def wheeling_thrust():
    c = bg((50, 90, 180), (6, 10, 34))
    ring = poly(tstroke(arc(0.5, 0.5, 0.36, -150, 150, 70), 0.10, 'start'))
    lit(c, ring, ((240, 250, 255), (140, 190, 255)), (140, 190, 255), 16, 1.4)
    ring2 = poly(tstroke(arc(0.5, 0.5, 0.27, 30, 300, 60), 0.04, 'start'))
    fill(c, soften(ring2, 2).point(lambda v: int(v * 0.5)), (200, 225, 255, 255))
    arm(c, spear_m(0.16, 0.84, 0.84, 0.16, w=0.07, hl=0.34), (220, 235, 255), angle=0, keyline=True)
    return finish(c)


def impulse_drive():
    c = bg((210, 120, 40), (40, 12, 4), 0.6, 0.4, 0.8)
    waves = shape(lambda d: [d.arc(pts([(0.60 - r, 0.40 - r), (0.60 + r, 0.40 + r)]), 260, 370, fill=255,
                                   width=int(0.04 * W)) for r in (0.12, 0.21, 0.30)])
    lit(c, waves, (255, 250, 220), (255, 190, 90), 12, 1.4)
    arm(c, spear_m(0.10, 0.92, 0.58, 0.42, head='broad'), (255, 220, 150), angle=0)
    sparkles(c, [(0.58, 0.42, 0.10)], glowc=(255, 220, 140))
    return finish(c)


def geirskogul():
    """Gungnir: the god's spear in gold, a blast of light bursting from its point."""
    c = bg((50, 80, 200), (4, 6, 36), 0.62, 0.38, 0.8)
    rays(c, 0.62, 0.38, 18, (230, 240, 255), 0.05, 0.8, 110, 6)
    halo = ell(0.38, 0.14, 0.86, 0.62)
    fill(c, soften(halo, 20).point(lambda v: int(v * 0.5)), (255, 240, 190, 255))
    ringm = shape(lambda d: d.ellipse(pts([(0.42, 0.18), (0.82, 0.58)]), outline=255, width=int(0.016 * W)))
    lit(c, ringm, (255, 236, 170), (255, 220, 140), 8, 1.2)
    rune = shape(lambda d: [d.line(pts([(0.62 + math.cos(math.radians(a)) * 0.17, 0.38 + math.sin(math.radians(a)) * 0.17),
                                        (0.62 + math.cos(math.radians(a)) * 0.21, 0.38 + math.sin(math.radians(a)) * 0.21)]),
                                   fill=255, width=int(0.014 * W)) for a in range(0, 360, 30)])
    fill(c, soften(rune), (255, 236, 170, 255))
    arm(c, spear_m(0.12, 0.90, 0.66, 0.34, head='gungnir', hl=0.32), (255, 230, 150), 16, 1.4,
        blade=((255, 255, 255), (190, 205, 235)), shaft=((255, 230, 150), (170, 110, 40)), angle=0)
    impact(c, 0.66, 0.34, 0.16, (255, 255, 255), (220, 235, 255), 4, 0.15)
    sparkles(c, [(0.66, 0.34, 0.10), (0.24, 0.30, 0.045), (0.84, 0.74, 0.04)], glowc=(200, 225, 255))
    return finish(c)


def GC_wing(d, cx, cy, side):
    """A swept feathered wing from (cx, cy) toward `side` (perpendicular-ish to the lance)."""
    for i in range(5):
        t = i / 4
        ang = math.radians(-140 + 46 * t) if side < 0 else math.radians(-30 + 60 * t)
        length = 0.26 - 0.07 * t
        ex, ey = cx + math.cos(ang) * length, cy + math.sin(ang) * length
        nx, ny = -math.sin(ang) * 0.035, math.cos(ang) * 0.035
        d.polygon(pts([(cx + nx, cy + ny), (ex, ey), (cx - nx, cy - ny)]), fill=255)


def drakesbane():
    """Ryunohige: a lance before a rearing fire-wyvern."""
    c = bg((190, 50, 30), (24, 2, 4), 0.5, 0.5)
    flames(c, [(0.5, 0.98, 0.40, 0.70, 0.0), (0.20, 0.98, 0.14, 0.40, -0.05), (0.80, 0.98, 0.14, 0.44, 0.05)],
           outer=((255, 170, 60), (180, 30, 10)), inner=((255, 220, 120), (230, 90, 20)), glowc=(255, 90, 20),
           inner_k=0.5)
    wy = shape(lambda d: GC.wyvern(d, 0.50, 0.44, 0.92))
    glow(c, wy, (255, 140, 40, 255), 14, 1.3)
    fill(c, soften(wy), linear((60, 10, 10, 255), (20, 2, 4, 255), 90))
    eyes = shape(lambda d: [d.ellipse(pts([(0.50 + s * 0.035 - 0.012, 0.21), (0.50 + s * 0.035 + 0.012, 0.225)]),
                                      fill=255) for s in (-1, 1)])
    lit(c, eyes, (255, 230, 120), (255, 200, 80), 4)
    arm(c, spear_m(0.14, 0.92, 0.84, 0.20, head='dragon'), (255, 200, 120), 14, 1.3,
        shaft=((200, 40, 40), (90, 10, 14)), angle=0)
    return finish(c)


def sonic_thrust():
    c = bg((40, 170, 170), (2, 26, 30), 0.6, 0.4, 0.8)
    rings = shape(lambda d: [d.ellipse(pts([(0.60 - r, 0.40 - r), (0.60 + r, 0.40 + r)]), outline=255,
                                       width=int(0.028 * W)) for r in (0.10, 0.20, 0.30)])
    glow(c, rings, (120, 255, 240, 255), 10, 1.0)
    fill(c, soften(rings, 2).point(lambda v: int(v * 0.85)), (220, 255, 250, 255))
    arm(c, spear_m(0.14, 0.86, 0.60, 0.40), (200, 255, 250), angle=0)
    sparkles(c, [(0.60, 0.40, 0.08)], glowc=(170, 255, 240))
    return finish(c)


def camlanns_torment():
    """Rhongomiant: driven point-down into the earth; the ground splits and torment pours up."""
    c = bg((120, 30, 90), (14, 0, 16), 0.5, 0.75, 0.8)
    ground = poly([(0, 0.80), (1, 0.76), (1, 1), (0, 1)])
    fill(c, soften(ground, 3), linear((40, 10, 30, 255), (10, 2, 8, 255), 90))
    cracks = shape(lambda d: [brush(d, bolt_path(s, 0.5, 0.80, x, y, 4, 0.03), 0.028, 0.006)
                              for s, x, y in ((1, 0.12, 0.86), (2, 0.86, 0.90), (3, 0.40, 0.98), (4, 0.66, 0.99))])
    lit(c, cracks, (255, 200, 150), (255, 60, 90), 10, 1.5)
    flames(c, [(0.30, 0.82, 0.14, 0.50, -0.06), (0.70, 0.82, 0.14, 0.48, 0.06), (0.5, 0.82, 0.22, 0.34, 0.0)],
           outer=((200, 90, 255), (110, 20, 120)), inner=((255, 160, 220), (200, 50, 140)), glowc=(200, 40, 160),
           gr=20, inner_k=0.4)
    arm(c, spear_m(0.5, 0.06, 0.5, 0.84, head='broad', hl=0.30), (255, 200, 230), 16, 1.4,
        blade=((255, 255, 255), (200, 170, 200)), shaft=((230, 220, 240), (120, 100, 140)), angle=0)
    sparkles(c, [(0.5, 0.80, 0.11)], color=(255, 230, 240), glowc=(255, 100, 160))
    return finish(c)


def stardiver():
    """Trishula: the trident falls from the night sky like a comet."""
    c = bg((60, 50, 150), (4, 4, 22), 0.66, 0.66, 0.8)
    trail = poly(tstroke([(0.02 + 0.66 * t, 0.02 + 0.66 * t) for t in (i / 30 for i in range(31))], 0.34, 'start'))
    fill(c, trail.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.7)), (150, 180, 255, 255))
    rnd = random.Random(21)
    sparkles(c, [(rnd.uniform(0.12, 0.85), rnd.uniform(0.12, 0.85), rnd.uniform(0.02, 0.035)) for _ in range(9)],
             glowc=(170, 190, 255))
    impact(c, 0.72, 0.72, 0.22, (255, 255, 240), (170, 190, 255), 8, 0.35)
    arm(c, spear_m(0.14, 0.14, 0.74, 0.74, head='trident', hl=0.34), (220, 230, 255), 16, 1.4,
        shaft=((180, 190, 240), (70, 70, 150)), angle=45)
    sparkles(c, [(0.74, 0.74, 0.12)], glowc=(230, 235, 255))
    return finish(c)


def diarmuid():
    """Diarmuid's twin spears, the red Gae Dearg and the yellow Gae Buidhe, crossed."""
    c = bg((40, 130, 80), (4, 22, 12))
    rays(c, 0.5, 0.42, 12, (220, 255, 200), 0.05, 0.75, 60, 8)
    arm(c, spear_m(0.14, 0.90, 0.80, 0.14), (255, 120, 100), blade=((255, 210, 200), (220, 60, 50)),
        shaft=((170, 40, 40), (80, 14, 14)), angle=0)
    arm(c, spear_m(0.86, 0.90, 0.20, 0.14), (255, 230, 120), blade=((255, 250, 200), (230, 180, 40)),
        shaft=((200, 150, 50), (110, 70, 20)), angle=0)
    return finish(c)


# ======================================================================================================================
# KATANA (ninja)
# ======================================================================================================================
def blade_rin():
    c = bg((180, 50, 40), (26, 4, 6))
    slash(c, arc(0.62, 0.70, 0.52, 200, 290, 40), 0.07, (255, 250, 240), (255, 150, 120))
    arm(c, ninjato(0.24, 0.82, 0.78, 0.22, 0.02), (255, 210, 190))
    return finish(c)


def blade_retsu():
    c = bg((120, 150, 40), (14, 22, 4))
    arm(c, ninjato(0.22, 0.84, 0.80, 0.22), (230, 255, 160))
    lightning(c, [bolt_path(31, 0.12, 0.40, 0.42, 0.20, 5, 0.04), bolt_path(32, 0.60, 0.80, 0.88, 0.56, 5, 0.04),
                  bolt_path(33, 0.50, 0.50, 0.70, 0.62, 3, 0.03)], 0.022, (210, 255, 90), (250, 255, 200), 10)
    return finish(c)


def blade_teki():
    c = bg((40, 100, 190), (2, 12, 40), 0.5, 0.6)
    water_band(c, [wave_path(0.04, 0.96, 0.70, 0.06, 1.5, 0.5), wave_path(0.10, 0.90, 0.82, 0.04, 2.0, 2.0)], 0.09)
    arm(c, ninjato(0.24, 0.80, 0.76, 0.18), (190, 230, 255))
    motes(c, 6, 12, (0.15, 0.2, 0.85, 0.7), (0.008, 0.02), (220, 240, 255), (100, 170, 255))
    return finish(c)


def blade_to():
    c = bg((60, 150, 200), (4, 20, 40))
    arm(c, ninjato(0.24, 0.82, 0.78, 0.22), (200, 240, 255))
    ice_shards(c, [(0.62, 0.30, 0.22, -110, 0.04), (0.74, 0.44, 0.18, -30, 0.035), (0.46, 0.46, 0.16, -150, 0.03),
                   (0.58, 0.56, 0.14, 60, 0.03), (0.80, 0.24, 0.12, -70, 0.025)])
    sparkles(c, [(0.30, 0.28, 0.05), (0.84, 0.66, 0.04)], glowc=(180, 230, 255))
    return finish(c)


def blade_chi():
    c = bg((150, 100, 50), (26, 14, 6), 0.5, 0.6)
    rocks(c, [(0.24, 0.92, 0.15, 0.42), (0.76, 0.92, 0.15, 0.48)], (255, 190, 100))
    arm(c, ninjato(0.5, 0.10, 0.5, 0.80, 0.0), (255, 220, 160), angle=90)
    rocks(c, [(0.5, 0.96, 0.20, 0.26), (0.36, 0.98, 0.10, 0.16), (0.64, 0.98, 0.10, 0.18)], (255, 190, 100))
    motes(c, 7, 10, (0.2, 0.45, 0.8, 0.7), (0.01, 0.02), (230, 190, 130), None)
    return finish(c)


def blade_ei():
    c = bg((110, 40, 140), (10, 0, 16))
    void = ell(0.30, 0.18, 0.80, 0.68)
    glow(c, void, (200, 90, 255, 255), 26, 1.4)
    fill(c, soften(void, 4), radial((0, 0, 0, 255), (60, 10, 80, 255), 0.55, 0.43, 0.26))
    rim = shape(lambda d: d.ellipse(pts([(0.30, 0.18), (0.80, 0.68)]), outline=255, width=int(0.012 * W)))
    fill(c, soften(rim, 2), (220, 160, 255, 255))
    arm(c, ninjato(0.20, 0.86, 0.80, 0.24), (230, 170, 255), blade=((230, 220, 240), (110, 90, 140)))
    motes(c, 9, 10, (0.2, 0.15, 0.85, 0.75), (0.008, 0.016), (230, 180, 255), (170, 60, 220))
    return finish(c)


def blade_jin():
    c = bg((40, 150, 130), (2, 24, 22))
    for off in (-0.16, 0.0, 0.16):
        slash(c, [(0.14 + off + t * 0.62, 0.18 - off + t * 0.62) for t in (j / 20 for j in range(21))],
              0.05, (240, 255, 250), (140, 255, 220), 10)
    arm(c, katana_m(0.80, 0.86, 0.26, 0.24, -0.02, hilt=0.26, bw=0.060, tw=0.09), (200, 255, 240), keyline=True)
    return finish(c)


def blade_ten():
    c = bg((90, 150, 230), (10, 24, 60), 0.5, 0.2, 0.8)
    beam = poly([(0.40, -0.05), (0.60, -0.05), (0.56, 0.9), (0.44, 0.9)])
    fill(c, beam.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.6)), (255, 250, 220, 255))
    clouds = shape(lambda d: [d.ellipse(pts([(x - r, 0.80 - r * 0.45), (x + r, 0.80 + r * 0.45)]), fill=255)
                              for x, r in ((0.2, 0.16), (0.40, 0.18), (0.62, 0.17), (0.82, 0.15))])
    lit(c, clouds, ((255, 255, 255), (180, 200, 240)), (220, 235, 255), 10, 1.0, soft=6)
    arm(c, ninjato(0.5, 0.86, 0.5, 0.14, 0.0), (255, 250, 210), 16, 1.4, angle=90)
    sparkles(c, [(0.5, 0.14, 0.12)], glowc=(255, 245, 200))
    return finish(c)


def blade_ku():
    """Five strikes from the void: the blade and its four after-images fanned out."""
    c = bg((80, 60, 170), (8, 4, 28), 0.5, 0.8)
    for a, k in ((-64, 0.35), (-32, 0.55), (32, 0.55), (64, 0.35)):
        m = ninjato(0.5, 0.90, 0.5, 0.16, 0.0)
        g = rot(union(m['blade'], m['guard']), a, 0.5, 0.90)
        glow(c, g, (160, 140, 255, 255), 8, 0.8)
        fill(c, soften(g, 2).point(lambda v, k=k: int(v * k)), (220, 210, 255, 255))
    arm(c, ninjato(0.5, 0.90, 0.5, 0.14, 0.0), (210, 190, 255), angle=90)
    sparkles(c, [(0.5, 0.14, 0.08)], glowc=(210, 190, 255))
    return finish(c)


def blade_metsu():
    """Kikoku, the demon-cry blade: black steel bleeding crimson, a cross of ruin behind it."""
    c = bg((150, 10, 20), (14, 0, 4), 0.5, 0.45, 0.7)
    smoke(c, 41, 14, (0.1, 0.1, 0.9, 0.9), (0.08, 0.14), (0, 0, 0), 150, 12)
    slash(c, [(0.12 + t * 0.76, 0.14 + t * 0.72) for t in (i / 20 for i in range(21))], 0.10, (255, 210, 200),
          (255, 30, 40), 16, 1.6)
    slash(c, [(0.88 - t * 0.76, 0.12 + t * 0.76) for t in (i / 20 for i in range(21))], 0.10, (255, 210, 200),
          (255, 30, 40), 16, 1.6)
    arm(c, ninjato(0.24, 0.84, 0.80, 0.20, 0.02), (255, 40, 40), 18, 1.5,
        blade=((90, 80, 90), (20, 14, 20)), edge=(255, 60, 60, 220), guard=((255, 120, 110), (150, 20, 20)),
        grip=((30, 6, 10), (8, 0, 2)))
    motes(c, 42, 12, (0.15, 0.1, 0.85, 0.8), (0.006, 0.014), (255, 160, 140), (255, 40, 40))
    return finish(c)


def blade_kamu():
    """Nagi, the calm sea: a still horizon, the blade above it in a divine ring."""
    c = bg((40, 140, 150), (2, 18, 30), 0.5, 0.4)
    sea = poly([(0, 0.66), (1, 0.66), (1, 1), (0, 1)])
    fill(c, soften(sea, 3), linear((30, 110, 130, 255), (4, 20, 34, 255), 90))
    refl = shape(lambda d: [d.rounded_rectangle(pts([(0.5 - w, y - 0.012), (0.5 + w, y + 0.012)]),
                                                radius=0.012 * W, fill=255)
                            for y, w in ((0.71, 0.18), (0.77, 0.13), (0.83, 0.09), (0.89, 0.05))])
    lit(c, refl, (230, 255, 240), (160, 240, 230), 8)
    ring = shape(lambda d: d.ellipse(pts([(0.26, 0.16), (0.74, 0.64)]), outline=255, width=int(0.026 * W)))
    lit(c, ring, ((255, 245, 190), (220, 170, 70)), (255, 230, 150), 14, 1.4)
    arm(c, ninjato(0.5, 0.70, 0.5, 0.08, 0.0), (220, 255, 240), angle=90,
        guard=((150, 240, 220), (40, 130, 120)))
    sparkles(c, [(0.5, 0.08, 0.08), (0.2, 0.24, 0.04), (0.82, 0.30, 0.04)], glowc=(200, 255, 240))
    return finish(c)


def blade_yu():
    c = bg((60, 70, 170), (6, 6, 30))
    drop = poly(GD.drop_pts(0.56, 0.12, 0.84, 0.25))
    lit(c, scale(drop, 0.8), ((180, 230, 255), (40, 90, 220)), (110, 160, 255), 22, 1.3)
    hi = ell(0.42, 0.50, 0.50, 0.62)
    fill(c, soften(hi, 4), (255, 255, 255, 170))
    arm(c, ninjato(0.18, 0.84, 0.76, 0.26), (190, 220, 255))
    motes(c, 11, 10, (0.12, 0.15, 0.9, 0.85), (0.012, 0.026), (210, 230, 255), (100, 150, 255), 200)
    return finish(c)


def blade_hi():
    """Kannagi: a black blade cut against a vast crimson moon."""
    c = bg((60, 10, 30), (8, 0, 6), 0.5, 0.45)
    m = ell(0.16, 0.12, 0.84, 0.80)
    glow(c, m, (255, 60, 60, 255), 30, 1.2)
    fill(c, soften(m, 2), radial((255, 120, 90, 255), (190, 20, 30, 255), 0.42, 0.36, 0.42))
    smoke(c, 51, 6, (0.2, 0.45, 0.8, 0.7), (0.08, 0.14), (120, 0, 10), 120, 10)
    slash(c, [(0.10 + t * 0.80, 0.70 - t * 0.44 - 0.12 * math.sin(math.pi * t)) for t in (i / 30 for i in range(31))],
          0.05, (255, 255, 250), (255, 200, 180), 10)
    blade = ninjato(0.26, 0.86, 0.80, 0.16, 0.02)
    whole = union(*blade.values())
    shadow(c, whole, 4, 7, 6, 150)
    fill(c, soften(whole), (10, 4, 8, 255))
    fill(c, soften(blade['edge']).point(lambda v: int(v * 0.5)), (255, 90, 80, 255))
    return finish(c)


def blade_shun():
    """Heishi Shorinken: five flashing cuts faster than the eye, a star of slashes."""
    c = bg((40, 90, 160), (2, 8, 28))
    for i in range(5):
        a = math.radians(-90 + 144 * i)
        b = math.radians(-90 + 144 * (i + 1))
        x0, y0 = 0.5 + math.cos(a) * 0.38, 0.5 + math.sin(a) * 0.38
        x1, y1 = 0.5 + math.cos(b) * 0.38, 0.5 + math.sin(b) * 0.38
        slash(c, [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for t in (j / 20 for j in range(21))], 0.04,
              (240, 255, 255), (120, 220, 255), 10, 1.3)
    arm(c, ninjato(0.22, 0.84, 0.82, 0.20, 0.02), (200, 245, 255), 16, 1.4,
        guard=((200, 255, 255), (60, 150, 200)))
    sparkles(c, [(0.5 + math.cos(math.radians(-90 + 72 * i)) * 0.38, 0.5 + math.sin(math.radians(-90 + 72 * i)) * 0.38,
                  0.05) for i in range(5)], glowc=(150, 230, 255))
    return finish(c)


def zesho_meppo():
    """The age when the Law decays: a cracked golden dharma wheel behind a dark blade."""
    c = bg((90, 40, 110), (8, 2, 16))
    wheel = shape(lambda d: [d.ellipse(pts([(0.18, 0.18), (0.82, 0.82)]), outline=255, width=int(0.035 * W)),
                             d.ellipse(pts([(0.42, 0.42), (0.58, 0.58)]), fill=255),
                             *[d.line(pts([(0.5, 0.5), (0.5 + math.cos(math.radians(22.5 + 45 * i)) * 0.31,
                                                        0.5 + math.sin(math.radians(22.5 + 45 * i)) * 0.31)]),
                                      fill=255, width=int(0.022 * W)) for i in range(8)]])
    crack = shape(lambda d: brush(d, bolt_path(61, 0.70, 0.12, 0.40, 0.92, 6, 0.05), 0.04, 0.02))
    wheel = minus(wheel, crack)
    lit(c, wheel, GOLD, (255, 200, 90), 14, 1.2)
    arm(c, ninjato(0.22, 0.86, 0.80, 0.18), (190, 120, 255), 16, 1.3, blade=((210, 200, 230), (70, 50, 100)),
        edge=(230, 180, 255, 180))
    return finish(c)


# ======================================================================================================================
# GREAT KATANA (tachi)
# ======================================================================================================================
def swallow(d, cx, cy, s, ang=0):
    """A swallow in flight (forked tail)."""
    q = [(0.30, 0.0), (0.12, -0.06), (0.0, -0.30), (-0.06, -0.06), (-0.22, -0.05), (-0.42, -0.16), (-0.30, 0.0),
         (-0.42, 0.16), (-0.22, 0.05), (-0.06, 0.06), (0.0, 0.30), (0.12, 0.06)]
    a = math.radians(ang)
    d.polygon(pts([(cx + (x * math.cos(a) - y * math.sin(a)) * s, cy + (x * math.sin(a) + y * math.cos(a)) * s)
                   for x, y in q]), fill=255)


def tachi_enpi():
    c = bg((60, 120, 190), (6, 14, 40))
    slash(c, arc(0.16, 0.92, 0.70, -80, -10, 40), 0.06, (240, 250, 255), (160, 210, 255))
    slash(c, arc(0.10, 0.98, 0.58, -82, -12, 40), 0.045, (240, 250, 255), (160, 210, 255))
    arm(c, katana_m(0.16, 0.88, 0.86, 0.22, 0.06, hilt=0.30, bw=0.056, tw=0.085), (210, 230, 255), keyline=True)
    sw = shape(lambda d: swallow(d, 0.70, 0.66, 0.30, -20))
    lit(c, sw, ((60, 70, 110), (14, 16, 30)), (230, 240, 255), 8, 1.4)
    return finish(c)


def tachi_hobaku():
    c = bg((180, 140, 50), (30, 20, 4))
    arm(c, tachi(0.14, 0.86, 0.86, 0.20), (255, 240, 170))
    rope = shape(lambda d: [brush(d, arc(0.50, 0.54, 0.30, a0, a0 + 150, 30, 0.10), 0.024)
                            for a0 in (-10, 170)])
    lit(c, rope, ((255, 240, 210), (190, 150, 90)), (255, 220, 140), 6)
    stun_stars(c, 0.5, 0.20, 0.22, 0.06, 4, 0.055, (255, 245, 160))
    return finish(c)


def tachi_goten():
    c = bg((80, 60, 180), (8, 4, 30))
    lightning(c, [bolt_path(71, 0.24, 0.10, 0.36, 0.52, 4, 0.05), bolt_path(72, 0.84, 0.44, 0.66, 0.88, 4, 0.05)],
              0.032, (200, 160, 255), (255, 255, 220), 12)
    arm(c, tachi(0.16, 0.86, 0.86, 0.18), (220, 190, 255), 16, 1.4)
    lightning(c, [bolt_path(73, 0.40, 0.58, 0.86, 0.18, 6, 0.045)], 0.024, (255, 230, 120), (255, 255, 240), 8)
    return finish(c)


def tachi_kagero():
    c = bg((180, 60, 20), (30, 6, 2), 0.5, 0.65)
    flames(c, [(0.36, 0.96, 0.22, 0.62, 0.05), (0.62, 0.96, 0.20, 0.72, 0.08), (0.84, 0.96, 0.12, 0.44, 0.06),
               (0.16, 0.96, 0.12, 0.38, -0.03)], inner_k=0.5)
    arm(c, tachi(0.14, 0.88, 0.86, 0.20), (255, 200, 120), blade=((255, 250, 230), (210, 150, 110)))
    return finish(c)


def tachi_jinpu():
    c = bg((50, 150, 80), (4, 24, 8))
    gust(c, [spiral(0.50, 0.50, 0.08, 0.38, 0, 300, 60, 0.75), spiral(0.50, 0.50, 0.06, 0.26, 180, 440, 60, 0.75)],
         0.05)
    arm(c, tachi(0.14, 0.86, 0.86, 0.20), (200, 255, 210))
    motes(c, 13, 6, (0.15, 0.15, 0.85, 0.85), (0.01, 0.018), (220, 255, 220), (120, 240, 150))
    return finish(c)


def tachi_koki():
    c = bg((230, 190, 90), (50, 30, 8), 0.5, 0.5)
    rays(c, 0.5, 0.5, 16, (255, 252, 220), 0.06, 0.8, 110, 6)
    sun = ell(0.32, 0.32, 0.68, 0.68)
    lit(c, sun, ((255, 255, 250), (255, 230, 150)), (255, 250, 210), 28, 1.5)
    arm(c, tachi(0.14, 0.86, 0.86, 0.18), (255, 255, 230), angle=0)
    return finish(c)


def tachi_yukikaze():
    c = bg((110, 160, 210), (10, 20, 46))
    gust(c, [wave_path(0.04, 0.96, 0.30, 0.04, 1.0, 0), wave_path(0.04, 0.96, 0.72, 0.04, 1.0, 2)], 0.035,
         (240, 250, 255), (200, 230, 255))

    def flakes(d):
        for x, y, r in ((0.28, 0.22, 0.07), (0.74, 0.70, 0.08), (0.22, 0.66, 0.05), (0.80, 0.30, 0.05)):
            for k in range(3):
                a = math.radians(60 * k)
                d.line(pts([(x - math.cos(a) * r, y - math.sin(a) * r), (x + math.cos(a) * r, y + math.sin(a) * r)]),
                       fill=255, width=int(0.018 * W))
    lit(c, shape(flakes), (255, 255, 255), (200, 230, 255), 8, 1.4)
    arm(c, tachi(0.14, 0.86, 0.86, 0.20), (220, 240, 255))
    motes(c, 14, 14, (0.1, 0.1, 0.9, 0.9), (0.006, 0.014), (255, 255, 255), (200, 230, 255))
    return finish(c)


def tachi_gekko():
    c = bg((40, 50, 130), (4, 4, 22), 0.6, 0.35)
    moon(c, 0.62, 0.36, 0.26, (0.36, -0.20))
    arm(c, tachi(0.16, 0.90, 0.80, 0.14, 0.07), (220, 230, 255))
    sparkles(c, [(0.24, 0.24, 0.05), (0.84, 0.70, 0.04)], glowc=(210, 220, 255))
    return finish(c)


def tachi_kasha():
    c = bg((150, 30, 20), (20, 2, 4), 0.5, 0.55)
    wheel = shape(lambda d: [d.ellipse(pts([(0.24, 0.26), (0.76, 0.78)]), outline=255, width=int(0.04 * W)),
                             d.ellipse(pts([(0.44, 0.46), (0.56, 0.58)]), fill=255),
                             *[d.line(pts([(0.5, 0.52), (0.5 + math.cos(math.radians(30 * i)) * 0.25,
                                                         0.52 + math.sin(math.radians(30 * i)) * 0.25)]),
                                      fill=255, width=int(0.018 * W)) for i in range(12)]])
    fl = shape(lambda d: [GA.flame(d, 0.5 + math.cos(math.radians(a)) * 0.27, 0.52 + math.sin(math.radians(a)) * 0.27,
                                   0.06, 0.20, -0.05) for a in range(0, 360, 40)])
    glow(c, fl, (255, 120, 30, 255), 16, 1.2)
    fill(c, soften(fl), linear((255, 230, 120, 255), (240, 80, 20, 255), 270))
    lit(c, wheel, ((255, 210, 120), (170, 60, 20)), (255, 140, 40), 10)
    arm(c, tachi(0.14, 0.88, 0.86, 0.18), (255, 200, 140))
    return finish(c)


def tachi_kaiten():
    """Amanomurakumo, sword of the gathering clouds: a vortex of cloud turning about the upright blade."""
    c = bg((60, 120, 210), (6, 14, 50), 0.5, 0.45)
    for r1, a0, alpha in ((0.40, 0, 1.0), (0.34, 120, 0.9), (0.30, 240, 0.8)):
        sp = poly(tstroke(spiral(0.5, 0.48, 0.05, r1, a0, a0 + 330, 80, 0.6), 0.12, 'start'))
        glow(c, sp, (200, 230, 255, 255), 10, 1.0)
        fill(c, soften(sp, 3).point(lambda v, a=alpha: int(v * a)),
             linear((255, 255, 255, 255), (170, 205, 245, 255), 90))
    arm(c, tachi(0.5, 0.92, 0.5, 0.06, 0.05), (255, 240, 180), 18, 1.4, angle=90)
    sparkles(c, [(0.53, 0.07, 0.10)], glowc=(255, 240, 180))
    return finish(c)


def tachi_rana():
    """Kogarasumaru, 'little crow': black crow wings raised behind the blade at dusk."""
    c = bg((210, 100, 120), (20, 4, 24), 0.5, 0.65)

    def wings(d):
        for s in (-1, 1):
            for L0, a0, span, wdt in ((0.44, -178, 62, 0.055), (0.30, -172, 58, 0.07)):
                for i in range(6):
                    t = i / 5
                    a = a0 + span * t
                    ang = math.radians(a) if s < 0 else math.radians(-180 - a)
                    L = L0 - 0.12 * (1 - t)
                    bx, by = 0.5, 0.60
                    ex, ey = bx + math.cos(ang) * L, by + math.sin(ang) * L
                    nx, ny = -math.sin(ang) * wdt, math.cos(ang) * wdt
                    mx, my = bx + math.cos(ang) * L * 0.62, by + math.sin(ang) * L * 0.62
                    d.polygon(pts([(bx, by), (mx + nx, my + ny), (ex, ey), (mx - nx, my - ny)]), fill=255)
    wg = shape(wings)
    glow(c, wg, (255, 190, 210, 255), 16, 1.6)
    fill(c, soften(wg), linear((80, 60, 110, 255), (6, 2, 12, 255), 90))
    arm(c, tachi(0.5, 0.94, 0.5, 0.08, 0.05), (255, 210, 230), 14, 1.3, angle=90)
    return finish(c)


def tachi_ageha():
    """A swallowtail butterfly alighting on the blade (Ageha lowers defense)."""
    c = bg((150, 60, 170), (16, 4, 24))
    arm(c, tachi(0.14, 0.88, 0.86, 0.22), (230, 200, 255))

    def bfly(d):
        cx, cy = 0.56, 0.42
        d.polygon(pts([(cx, cy), (cx - 0.24, cy - 0.20), (cx - 0.26, cy - 0.04), (cx - 0.08, cy + 0.02)]), fill=255)
        d.polygon(pts([(cx, cy), (cx + 0.20, cy - 0.24), (cx + 0.24, cy - 0.06), (cx + 0.08, cy + 0.02)]), fill=255)
        d.polygon(pts([(cx, cy), (cx - 0.16, cy + 0.06), (cx - 0.14, cy + 0.18), (cx - 0.20, cy + 0.26),
                       (cx - 0.06, cy + 0.14)]), fill=255)
        d.polygon(pts([(cx, cy), (cx + 0.14, cy + 0.04), (cx + 0.14, cy + 0.16), (cx + 0.20, cy + 0.26),
                       (cx + 0.06, cy + 0.12)]), fill=255)
    b = shape(bfly)
    lit(c, b, ((255, 230, 120), (230, 120, 30)), (255, 200, 90), 12, 1.3)
    spots = shape(lambda d: [d.ellipse(pts([(x - 0.025, y - 0.025), (x + 0.025, y + 0.025)]), fill=255)
                             for x, y in ((0.40, 0.32), (0.72, 0.30), (0.46, 0.56), (0.68, 0.54))])
    fill(c, soften(spots), (40, 14, 40, 255))
    body = shape(lambda d: d.ellipse(pts([(0.545, 0.32), (0.575, 0.56)]), fill=255))
    fill(c, soften(body), (30, 10, 30, 255))
    return finish(c)


def tachi_fudo():
    """Masamune and Fudo Myo-o's flaming halo: the upright blade before a ring of fire."""
    c = bg((150, 30, 10), (18, 2, 2), 0.5, 0.45)
    ring = shape(lambda d: [GA.flame(d, 0.5 + math.cos(math.radians(a)) * 0.30, 0.46 + math.sin(math.radians(a)) * 0.30
                                     + 0.08, 0.08, 0.24, 0.0) for a in range(0, 360, 30)])
    glow(c, ring, (255, 120, 20, 255), 22, 1.4)
    fill(c, soften(ring), linear((255, 230, 120, 255), (230, 70, 20, 255), 270))
    halo = shape(lambda d: d.ellipse(pts([(0.24, 0.20), (0.76, 0.72)]), outline=255, width=int(0.03 * W)))
    lit(c, halo, GOLD, (255, 200, 80), 10, 1.3)
    inner = ell(0.27, 0.23, 0.73, 0.69)
    fill(c, soften(inner, 6).point(lambda v: int(v * 0.55)), (40, 4, 4, 255))
    arm(c, tachi(0.5, 0.94, 0.5, 0.06, 0.03), (255, 230, 160), 16, 1.5, angle=90,
        edge=(255, 230, 180, 200))
    sparkles(c, [(0.51, 0.08, 0.10)], glowc=(255, 210, 120))
    return finish(c)


def tachi_shoha():
    """Dojikiri Yasutsuna: one colossal crescent cut, a demon-slaying wave of red and gold."""
    c = bg((120, 20, 30), (14, 0, 4), 0.5, 0.5)
    wave = poly(tstroke(arc(0.40, 0.62, 0.46, -95, 20, 60), 0.20, 'both'))
    glow(c, wave, (255, 80, 40, 255), 22, 1.4)
    fill(c, soften(wave, 2), linear((255, 240, 180, 255), (230, 60, 30, 255), 0))
    core = poly(tstroke(arc(0.40, 0.62, 0.46, -88, 12, 60), 0.07, 'both'))
    fill(c, soften(core, 2), (255, 255, 240, 255))
    arm(c, tachi(0.10, 0.92, 0.80, 0.16, 0.06), (255, 180, 120), 14, 1.3, guard=GOLD)
    motes(c, 81, 12, (0.4, 0.1, 0.92, 0.8), (0.006, 0.014), (255, 230, 180), (255, 120, 60))
    return finish(c)


def tachi_suikawari():
    """'Watermelon splitting': the blade comes down and the melon falls open in two halves."""
    c = bg((60, 160, 140), (4, 28, 30), 0.5, 0.4)
    for s in (-1, 1):
        cx, cy, r = 0.5 + s * 0.17, 0.66, 0.18
        half = shape(lambda d, cx=cx, cy=cy, r=r: d.pieslice(pts([(cx - r, cy - r), (cx + r, cy + r)]), 0, 180,
                                                             fill=255))
        face = ell(cx - r, cy - r * 0.32, cx + r, cy + r * 0.32)
        body = union(half, face)
        body = rot(body, -s * 24, cx, cy)
        face = rot(face, -s * 24, cx, cy)
        shadow(c, body, 4, 7, 6, 140)
        fill(c, soften(body), linear((110, 200, 80, 255), (20, 80, 30, 255), 90))
        stripes = shape(lambda d, cx=cx, cy=cy, r=r: [d.line(pts([(cx + k * r, cy), (cx + k * r * 0.7, cy + r)]),
                                                             fill=255, width=int(0.02 * W)) for k in (-0.6, 0, 0.6)])
        fill(c, soften(minus(rot(stripes, -s * 24, cx, cy), face)).point(lambda v: int(v * 0.7)), (20, 60, 20, 255))
        fill(c, soften(face), (250, 250, 230, 255))
        flesh = rot(ell(cx - r * 0.86, cy - r * 0.25, cx + r * 0.86, cy + r * 0.25), -s * 24, cx, cy)
        fill(c, soften(flesh), radial((255, 110, 110, 255), (220, 40, 60, 255), cx, cy, r))
        seeds = shape(lambda d, cx=cx, cy=cy, r=r: [d.ellipse(pts([(cx + k * r - 0.01, cy - 0.008),
                                                                   (cx + k * r + 0.01, cy + 0.008)]), fill=255)
                                                    for k in (-0.5, -0.15, 0.2, 0.5)])
        fill(c, soften(rot(seeds, -s * 24, cx, cy)), (30, 10, 10, 255))
    arm(c, tachi(0.5, 0.02, 0.5, 0.60, 0.0), (255, 255, 230), angle=90)
    motes(c, 91, 10, (0.3, 0.45, 0.7, 0.7), (0.008, 0.016), (255, 160, 170), (255, 80, 100))
    return finish(c)


def tachi_mumei():
    """'Nameless': a single ink enso and a plain blade in the mist."""
    c = bg((200, 200, 190), (60, 64, 70), 0.5, 0.45)
    smoke(c, 101, 8, (0.1, 0.5, 0.9, 0.9), (0.10, 0.18), (255, 255, 255), 140, 14)
    enso = poly(tstroke(arc(0.5, 0.48, 0.32, -70, 255, 80), 0.08, 'start'))
    fill(c, soften(enso, 2), (20, 20, 26, 255))
    splat = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                             for x, y, r in ((0.60, 0.14, 0.015), (0.66, 0.12, 0.008))])
    fill(c, soften(splat), (20, 20, 26, 255))
    arm(c, tachi(0.16, 0.86, 0.84, 0.20), (255, 255, 255), 10, 1.0, guard=((90, 90, 100), (40, 40, 50)))
    return finish(c)


# ======================================================================================================================
# CLUB
# ======================================================================================================================
def club(x0=0.22, y0=0.86, x1=0.64, y1=0.38, r=0.15, head='flanged'):
    return mace_m(x0, y0, x1, y1, r, head)


def shining_strike():
    c = bg((210, 170, 70), (40, 24, 6))
    rays(c, 0.62, 0.38, 14, (255, 250, 220), 0.06, 0.7, 100, 6)
    impact(c, 0.62, 0.38, 0.26, (255, 255, 230), (255, 230, 150), 8, 0.4)
    arm(c, club(), (255, 245, 200), angle=0)
    return finish(c)


def angel_wing(cx, cy, s, side):
    """A smooth angel's wing from its root (cx, cy): a curved leading edge and five scalloped feather tips."""
    q = [(0.0, 0.0), (0.06, -0.10), (0.17, -0.18), (0.30, -0.22), (0.42, -0.22), (0.50, -0.18),
         (0.42, -0.10), (0.44, -0.08), (0.36, -0.01), (0.37, 0.02), (0.28, 0.06), (0.28, 0.09), (0.19, 0.10),
         (0.18, 0.13), (0.09, 0.12), (0.0, 0.08)]
    return poly([(cx + side * x * s, cy + y * s) for x, y in q])


def seraph_strike():
    """Light: a club raised on a pair of smooth white seraph's wings beneath a golden halo."""
    c = bg((120, 170, 230), (14, 24, 50), 0.5, 0.42)
    rays(c, 0.52, 0.42, 12, (255, 255, 230), 0.05, 0.75, 80, 8)
    wings = union(angel_wing(0.47, 0.46, 0.92, -1), angel_wing(0.57, 0.46, 0.92, 1))
    glow(c, wings, (255, 250, 220, 255), 14, 1.3)
    shadow(c, wings, 3, 6, 6, 110)
    fill(c, soften(wings), linear((255, 255, 255, 255), (205, 220, 245, 255), 90))
    vanes = shape(lambda d: [d.line(pts([(0.52 + sd * 0.06, 0.47), (0.52 + sd * x, y)]), fill=255,
                                    width=int(0.010 * W))
                             for sd in (-1, 1) for x, y in ((0.36, 0.43), (0.29, 0.51), (0.20, 0.55))])
    fill(c, scale(soften(inter(vanes, wings), 1.5), 0.45), (120, 140, 190, 255))
    arm(c, club(0.30, 0.92, 0.52, 0.40, 0.14), (255, 245, 210), angle=0)
    halo = shape(lambda d: d.ellipse(pts([(0.40, 0.12), (0.64, 0.20)]), outline=255, width=int(0.024 * W)))
    lit(c, halo, GOLD, (255, 230, 150), 8, 1.4)
    return finish(c)


def brainshaker():
    c = bg((200, 110, 40), (34, 12, 4))
    shock = shape(lambda d: [d.arc(pts([(0.66 - r, 0.32 - r), (0.66 + r, 0.32 + r)]), 200, 340, fill=255,
                                   width=int(0.022 * W)) for r in (0.22, 0.30)])
    lit(c, shock, (255, 240, 200), (255, 190, 100), 8)
    arm(c, club(0.18, 0.88, 0.58, 0.48, 0.15, 'spiked'), (255, 220, 160), angle=0)
    stun_stars(c, 0.64, 0.24, 0.20, 0.06, 4, 0.055, (255, 245, 150), 20)
    return finish(c)


def starlight():
    c = bg((50, 80, 170), (4, 8, 30), 0.5, 0.35)
    st = poly(star_poly(0.56, 0.36, 5, 0.24, 0.10))
    lit(c, st, ((255, 255, 240), (170, 210, 255)), (170, 210, 255), 22, 1.5)
    arm(c, club(0.18, 0.90, 0.40, 0.62, 0.11), (200, 220, 255), angle=0)
    motes(c, 111, 12, (0.15, 0.1, 0.9, 0.7), (0.006, 0.014), (230, 240, 255), (150, 190, 255))
    return finish(c)


def moonlight():
    c = bg((40, 60, 120), (4, 6, 24), 0.55, 0.35)
    moon(c, 0.58, 0.36, 0.25, (0.40, -0.16), ((240, 250, 255), (170, 200, 240)), (160, 200, 255))
    motes(c, 121, 14, (0.10, 0.4, 0.9, 0.9), (0.008, 0.016), (200, 230, 255), (120, 170, 255))
    arm(c, club(0.20, 0.90, 0.42, 0.64, 0.11), (190, 210, 255), angle=0)
    return finish(c)


def skullbreaker():
    c = bg((120, 110, 140), (12, 10, 16), 0.45, 0.6)

    def skull(d):
        d.ellipse(pts([(0.22, 0.38), (0.62, 0.74)]), fill=255)
        d.rounded_rectangle(pts([(0.31, 0.64), (0.53, 0.86)]), radius=0.04 * W, fill=255)
    sk = shape(skull)
    lit(c, sk, ((255, 250, 235), (180, 170, 150)), (255, 255, 230), 12, sh=True)

    def holes(d):
        for x in (0.345, 0.495):
            d.ellipse(pts([(x - 0.055, 0.56), (x + 0.055, 0.67)]), fill=255)
        d.polygon(pts([(0.42, 0.68), (0.39, 0.74), (0.45, 0.74)]), fill=255)
        for x in (0.36, 0.40, 0.44, 0.48):
            d.line(pts([(x, 0.78), (x, 0.86)]), fill=255, width=int(0.012 * W))
    fill(c, soften(shape(holes)), (40, 26, 40, 255))
    crack = shape(lambda d: brush(d, bolt_path(131, 0.50, 0.40, 0.40, 0.58, 4, 0.025), 0.022, 0.008))
    fill(c, soften(crack), (40, 26, 40, 255))
    impact(c, 0.52, 0.38, 0.14, (255, 250, 220), (255, 200, 140), 6, 0.35)
    arm(c, club(0.90, 0.72, 0.62, 0.30, 0.12, 'spiked'), (255, 220, 200), angle=0)
    return finish(c)


def GB_skull(d, cx, cy, s):
    d.ellipse(pts([(cx - 0.20 * s * 1.1, cy - 0.30 * s), (cx + 0.20 * s * 1.1, cy + 0.10 * s)]), fill=255)
    d.rounded_rectangle(pts([(cx - 0.12 * s, cy), (cx + 0.12 * s, cy + 0.22 * s)]), radius=0.02 * W, fill=255)


def true_strike():
    c = bg((40, 130, 120), (2, 20, 20))
    tgt = shape(lambda d: [d.ellipse(pts([(0.62 - r, 0.36 - r), (0.62 + r, 0.36 + r)]), outline=255,
                                     width=int(0.02 * W)) for r in (0.12, 0.22)])
    lit(c, tgt, (220, 255, 240), (140, 255, 220), 8)
    impact(c, 0.62, 0.36, 0.18, (255, 255, 240), (160, 255, 220), 4, 0.2)
    arm(c, club(0.16, 0.88, 0.52, 0.46, 0.15), (200, 255, 240), angle=0)
    return finish(c)


def judgment():
    c = bg((140, 40, 50), (18, 4, 8), 0.5, 0.4)
    beam = shape(lambda d: [d.line(pts([(0.5, 0.12), (0.5, 0.56)]), fill=255, width=int(0.02 * W)),
                            d.line(pts([(0.22, 0.20), (0.78, 0.20)]), fill=255, width=int(0.02 * W)),
                            *[d.line(pts([(x, 0.20), (x + dx, 0.40)]), fill=255, width=int(0.008 * W))
                              for x in (0.24, 0.76) for dx in (-0.08, 0.08)],
                            *[d.chord(pts([(x - 0.11, 0.30), (x + 0.11, 0.50)]), 0, 180, fill=255)
                              for x in (0.24, 0.76)],
                            d.ellipse(pts([(0.47, 0.09), (0.53, 0.15)]), fill=255)])
    lit(c, beam, GOLD, (255, 210, 120), 12, 1.2)
    arm(c, club(0.30, 0.94, 0.56, 0.60, 0.14), (255, 220, 170), angle=0)
    return finish(c)


def hexa_strike():
    c = bg((120, 50, 160), (12, 4, 24))
    tri = [[(0.5 + math.cos(math.radians(a + 120 * k)) * 0.38, 0.5 + math.sin(math.radians(a + 120 * k)) * 0.38)
            for k in range(4)] for a in (-90, 90)]
    hexa = shape(lambda d: [brush(d, t, 0.024) for t in tri])
    lit(c, hexa, (240, 220, 255), (200, 140, 255), 10, 1.3)
    sparkles(c, [(0.5 + math.cos(math.radians(-90 + 60 * i)) * 0.38, 0.5 + math.sin(math.radians(-90 + 60 * i)) * 0.38,
                  0.05) for i in range(6)], glowc=(220, 170, 255))
    arm(c, club(0.24, 0.84, 0.58, 0.42, 0.14), (230, 200, 255), angle=0)
    return finish(c)


def black_halo():
    """A mace crowned by a ring of black light."""
    c = bg((130, 90, 180), (8, 2, 16), 0.6, 0.4)
    disc = ell(0.34, 0.10, 0.90, 0.66)
    glow(c, disc, (230, 180, 255, 255), 24, 1.2)
    halo = shape(lambda d: d.ellipse(pts([(0.36, 0.12), (0.88, 0.64)]), outline=255, width=int(0.08 * W)))
    fill(c, soften(halo), linear((40, 20, 60, 255), (0, 0, 6, 255), 90))
    for (a, b) in (((0.36, 0.12), (0.88, 0.64)), ((0.44, 0.20), (0.80, 0.56))):
        rim = shape(lambda d, a=a, b=b: d.ellipse(pts([a, b]), outline=255, width=int(0.012 * W)))
        lit(c, rim, (240, 210, 255), (200, 130, 255), 6, 1.3)
    arm(c, club(0.20, 0.90, 0.58, 0.44, 0.14), (230, 190, 255), angle=0)
    motes(c, 141, 10, (0.3, 0.1, 0.9, 0.7), (0.006, 0.012), (230, 200, 255), (160, 80, 220))
    return finish(c)


def randgrith():
    """Mjollnir: the thunder god's hammer, lightning crackling from its head."""
    c = bg((140, 70, 30), (18, 6, 4), 0.58, 0.38)
    lightning(c, [bolt_path(151, 0.58, 0.38, 0.14, 0.16, 5, 0.05), bolt_path(152, 0.58, 0.38, 0.90, 0.20, 4, 0.05),
                  bolt_path(153, 0.58, 0.38, 0.88, 0.76, 4, 0.05), bolt_path(154, 0.58, 0.38, 0.30, 0.20, 3, 0.03)],
              0.03, (190, 160, 255), (255, 255, 230), 12)
    arm(c, mace_m(0.24, 0.88, 0.58, 0.38, 0.19, 'hammer'), (255, 220, 140), 18, 1.4,
        blade=((200, 205, 220), (80, 84, 100)), guard=GOLD, grip=((160, 90, 40), (60, 30, 14)), angle=0)
    return finish(c)


def mystic_boon():
    """Yagrush: the club draws mana in blue spirals into a shining orb."""
    c = bg((40, 80, 170), (4, 8, 30), 0.6, 0.4)
    for a0 in (0, 120, 240):
        sp = poly(tstroke(spiral(0.62, 0.38, 0.32, 0.10, a0, a0 + 300, 60), 0.05, 'start'))
        glow(c, sp, (120, 180, 255, 255), 8)
        fill(c, soften(sp), linear((230, 245, 255, 255), (110, 160, 255, 255), 0))
    arm(c, mace_m(0.20, 0.88, 0.62, 0.38, 0.13, 'orb'), (150, 200, 255), 18, 1.5,
        blade=((230, 245, 255), (60, 120, 230)), angle=45)
    hi = ell(0.58, 0.32, 0.62, 0.36)
    fill(c, soften(hi, 3), (255, 255, 255, 230))
    motes(c, 161, 12, (0.2, 0.08, 0.9, 0.7), (0.006, 0.014), (220, 240, 255), (110, 170, 255))
    return finish(c)


def flash_nova():
    c = bg((240, 240, 200), (60, 60, 40), 0.62, 0.38, 0.7)
    rays(c, 0.62, 0.38, 20, (255, 255, 255), 0.05, 0.8, 140, 4)
    impact(c, 0.62, 0.38, 0.34, (255, 255, 250), (255, 255, 220), 12, 0.35)
    burst = ell(0.50, 0.26, 0.74, 0.50)
    lit(c, burst, (255, 255, 255), (255, 255, 230), 20, 1.6, soft=6)
    arm(c, club(0.18, 0.90, 0.54, 0.50, 0.14), (255, 255, 220), angle=0, blade=((240, 240, 230), (110, 110, 120)))
    return finish(c)


def dagan():
    """Gambanteinn: twin streams, life (green) and mind (blue), wind up around the club."""
    c = bg((40, 120, 120), (2, 18, 22), 0.5, 0.5)
    for ph, col_, gl in ((0, (210, 255, 210), (100, 255, 140)), (math.pi, (210, 235, 255), (100, 160, 255))):
        path = [(0.5 + 0.24 * math.sin(ph + t * 2 * math.pi * 1.25), 0.90 - t * 0.78) for t in (i / 60 for i in range(61))]
        sp = poly(tstroke(path, 0.06, 'end'))
        lit(c, sp, col_, gl, 12, 1.3)
    arm(c, mace_m(0.5, 0.90, 0.5, 0.30, 0.14, 'flanged'), (230, 255, 230), 16, 1.3, angle=90,
        blade=((255, 255, 240), (180, 170, 130)), grip=((80, 160, 140), (20, 60, 50)))
    sparkles(c, [(0.30, 0.18, 0.05), (0.72, 0.16, 0.05)], glowc=(200, 255, 220))
    return finish(c)


def realmrazer():
    """Tishtrya: the club falls and the realm's floor shatters, starlight showing through the cracks."""
    c = bg((70, 40, 130), (6, 2, 20), 0.5, 0.7)
    ground = poly([(0, 0.66), (1, 0.62), (1, 1), (0, 1)])
    fill(c, soften(ground, 3), linear((60, 40, 80, 255), (14, 8, 24, 255), 90))
    cracks = shape(lambda d: [brush(d, bolt_path(s, 0.5, 0.66, x, y, 4, 0.04), 0.03, 0.008)
                              for s, x, y in ((171, 0.06, 0.72), (172, 0.94, 0.70), (173, 0.30, 0.98),
                                              (174, 0.70, 0.98), (175, 0.5, 1.0))])
    lit(c, cracks, (240, 230, 255), (170, 130, 255), 12, 1.6)
    shards_ = shape(lambda d: [shard(d, x, y, 0.08, a, 0.025) for x, y, a in
                               ((0.22, 0.52, -60), (0.80, 0.50, -120), (0.34, 0.40, -80), (0.70, 0.40, -100))])
    lit(c, shards_, ((180, 160, 220), (70, 50, 110)), (200, 170, 255), 6)
    impact(c, 0.5, 0.64, 0.20, (255, 255, 255), (190, 160, 255), 10, 0.35)
    arm(c, mace_m(0.5, 0.06, 0.5, 0.52, 0.15, 'flanged'), (220, 200, 255), 16, 1.4, angle=90,
        blade=((240, 230, 255), (120, 100, 170)))
    sparkles(c, [(0.20, 0.82, 0.04), (0.78, 0.86, 0.035), (0.5, 0.92, 0.03)], glowc=(200, 180, 255))
    return finish(c)


def exudation():
    """Idris: the geomancer's club wells over, luminous drops oozing from its head in a geo ring."""
    c = bg((40, 120, 110), (4, 16, 20), 0.6, 0.4)
    GD.aura_ring(c, 0.60, 0.42, 0.34, 0.13, (200, 255, 230), (120, 240, 200), 0.02)
    arm(c, mace_m(0.20, 0.90, 0.60, 0.36, 0.15, 'orb'), (150, 255, 210), 16, 1.4,
        blade=((220, 255, 230), (40, 170, 130)), angle=45)
    drops = shape(lambda d: [d.polygon(pts(GD.drop_pts(x, y, y + h, h * 0.42)), fill=255)
                             for x, y, h in ((0.56, 0.50, 0.12), (0.68, 0.48, 0.16), (0.76, 0.60, 0.10),
                                             (0.62, 0.66, 0.09))])
    lit(c, drops, ((230, 255, 240), (60, 200, 150)), (120, 255, 200), 8, 1.3)
    hi = ell(0.55, 0.29, 0.59, 0.33)
    fill(c, soften(hi, 3), (255, 255, 255, 230))
    return finish(c)


ICONS = {
    # polearm
    ('ja', 'Double Thrust'): double_thrust,
    ('ja', 'Thunder Thrust'): thunder_thrust,
    ('ja', 'Raiden Thrust'): raiden_thrust,
    ('ja', 'Leg Sweep'): leg_sweep,
    ('ja', 'Penta Thrust'): penta_thrust,
    ('ja', 'Vorpal Thrust'): vorpal_thrust,
    ('ja', 'Skewer'): skewer,
    ('ja', 'Wheeling Thrust'): wheeling_thrust,
    ('ja', 'Impulse Drive'): impulse_drive,
    ('ja', 'Geirskogul'): geirskogul,
    ('ja', 'Drakesbane'): drakesbane,
    ('ja', 'Sonic Thrust'): sonic_thrust,
    ('ja', "Camlann's Torment"): camlanns_torment,
    ('ja', 'Stardiver'): stardiver,
    ('ja', 'Diarmuid'): diarmuid,
    # katana
    ('ja', 'Blade: Rin'): blade_rin,
    ('ja', 'Blade: Retsu'): blade_retsu,
    ('ja', 'Blade: Teki'): blade_teki,
    ('ja', 'Blade: To'): blade_to,
    ('ja', 'Blade: Chi'): blade_chi,
    ('ja', 'Blade: Ei'): blade_ei,
    ('ja', 'Blade: Jin'): blade_jin,
    ('ja', 'Blade: Ten'): blade_ten,
    ('ja', 'Blade: Ku'): blade_ku,
    ('ja', 'Blade: Metsu'): blade_metsu,
    ('ja', 'Blade: Kamu'): blade_kamu,
    ('ja', 'Blade: Yu'): blade_yu,
    ('ja', 'Blade: Hi'): blade_hi,
    ('ja', 'Blade: Shun'): blade_shun,
    ('ja', 'Zesho Meppo'): zesho_meppo,
    # great katana
    ('ja', 'Tachi: Enpi'): tachi_enpi,
    ('ja', 'Tachi: Hobaku'): tachi_hobaku,
    ('ja', 'Tachi: Goten'): tachi_goten,
    ('ja', 'Tachi: Kagero'): tachi_kagero,
    ('ja', 'Tachi: Jinpu'): tachi_jinpu,
    ('ja', 'Tachi: Koki'): tachi_koki,
    ('ja', 'Tachi: Yukikaze'): tachi_yukikaze,
    ('ja', 'Tachi: Gekko'): tachi_gekko,
    ('ja', 'Tachi: Kasha'): tachi_kasha,
    ('ja', 'Tachi: Kaiten'): tachi_kaiten,
    ('ja', 'Tachi: Rana'): tachi_rana,
    ('ja', 'Tachi: Ageha'): tachi_ageha,
    ('ja', 'Tachi: Fudo'): tachi_fudo,
    ('ja', 'Tachi: Shoha'): tachi_shoha,
    ('ja', 'Tachi: Suikawari'): tachi_suikawari,
    ('ja', 'Tachi: Mumei'): tachi_mumei,
    # club
    ('ja', 'Shining Strike'): shining_strike,
    ('ja', 'Seraph Strike'): seraph_strike,
    ('ja', 'Brainshaker'): brainshaker,
    ('ja', 'Starlight'): starlight,
    ('ja', 'Moonlight'): moonlight,
    ('ja', 'Skullbreaker'): skullbreaker,
    ('ja', 'True Strike'): true_strike,
    ('ja', 'Judgment'): judgment,
    ('ja', 'Hexa Strike'): hexa_strike,
    ('ja', 'Black Halo'): black_halo,
    ('ja', 'Randgrith'): randgrith,
    ('ja', 'Mystic Boon'): mystic_boon,
    ('ja', 'Flash Nova'): flash_nova,
    ('ja', 'Dagan'): dagan,
    ('ja', 'Realmrazer'): realmrazer,
    ('ja', 'Exudation'): exudation,
}
COVERS = {}
VARIANTS = {}
NAMES = [n for _, n in ICONS]
