"""Signature icons, round 2: hand-to-hand, dagger and sword weapon skills.

Each weapon type keeps one silhouette (wrapped fist / kicking leg, a short dagger, a long-bladed sword); the WS's
element and effect decide the background mood and what surrounds the weapon. Relic, mythic, empyrean and aeonic
weapon skills get the richest paintings.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_b as GB
import group_d as GD

W = K.W
p, pts, shape, soften, mask = K.p, K.pts, K.shape, K.soften, K.mask
xf, ell = GB.xf, GB.ell
stroke, arc_path, star = GD.stroke, GD.arc_path, GD.star


# ---- helpers --------------------------------------------------------------------------------------------------------
def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(rgba(c0), rgba(c1), cx, cy, r)


def paint(x):
    """A colour, a (top, bottom) pair for a vertical gradient, or an image."""
    if isinstance(x, Image.Image):
        return x
    if isinstance(x[0], tuple):
        return K.linear(rgba(x[0]), rgba(x[1]), 90)
    return rgba(x)


def lit(c, m, fillp, glowc=None, gr=14, gs=1.2, sh=False, soft=1.2):
    if glowc:
        K.glow(c, m, rgba(glowc), gr, gs)
    if sh:
        K.shadow(c, m, 5, 8, 8, 160)
    K.fill(c, soften(m, soft), paint(fillp))


def inter(a, b):
    return ImageChops.multiply(a, b)


def minus(a, b):
    return ImageChops.subtract(a, b)


def scale(m, v):
    return m.point(lambda x: int(x * v))


def tfill(c, m, color):
    """Fill colour through a soft or partial mask without darkening its edges (K.fill blends with black)."""
    layer = Image.new('RGBA', (W, W), rgba(color, 0))
    a = m if len(color) < 4 or color[3] == 255 else m.point(lambda v: v * color[3] // 255)
    layer.putalpha(a)
    c.alpha_composite(layer)


def rot(m, deg, cx=0.5, cy=0.5):
    """Rotate a mask counter-clockwise by deg around unit point (cx, cy)."""
    return m.rotate(deg, resample=Image.BICUBIC, center=p(cx, cy))


def sparkles(c, spots, glowc=(255, 255, 255)):
    st = shape(lambda d: [K.sparkle(d, x, y, r) for x, y, r in spots])
    K.glow(c, st, rgba(glowc), 8, 1.2)
    K.fill(c, soften(st), (255, 255, 255, 255))


def motes(c, seed, n, box, rr, color, glowc):
    rnd = random.Random(seed)
    m = mask()
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(*rr)
        d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    K.glow(c, m, rgba(glowc), 5)
    K.fill(c, m, rgba(color))


def rays(c, cx, cy, n, length, color, alpha=90, w=0.05, blur=8, phase=0.0):
    GB.rays(c, cx, cy, n, length, rgba(color), alpha, w, blur, phase)


def swoosh(d, cx, cy, r, a0, a1, w, taper='mid', n=48, fillv=255):
    """A crescent slash along a circle of radius r from a0 to a1 degrees (clockwise on screen)."""
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        if taper == 'mid':
            ww = w * math.sin(math.pi * t) ** 0.7
        else:                                          # thin tail, fat head, sharp tip
            ww = w * (t ** 0.8) * (1 - t) ** 0.25 * 1.6
        outer.append((cx + math.cos(a) * (r + ww / 2), cy + math.sin(a) * (r + ww / 2)))
        inner.append((cx + math.cos(a) * (r - ww / 2), cy + math.sin(a) * (r - ww / 2)))
    d.polygon(pts(outer + inner[::-1]), fill=fillv)


def slash(d, x0, y0, x1, y1, w, fillv=255):
    """A straight lens-shaped cut."""
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    a, b = [], []
    for i in range(25):
        t = i / 24
        ww = w / 2 * math.sin(math.pi * t) ** 0.8
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        a.append((x + nx * ww, y + ny * ww))
        b.append((x - nx * ww, y - ny * ww))
    d.polygon(pts(a + b[::-1]), fill=fillv)


def bolt_path(x0, y0, x1, y1, seed, n=7, jag=0.06):
    rnd = random.Random(seed)
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    out = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        o = rnd.uniform(-jag, jag) * (1 if i % 2 else -1)
        out.append((x0 + (x1 - x0) * t + nx * abs(o) * (1 if i % 2 else -1), y0 + (y1 - y0) * t + ny * abs(o) * (1 if i % 2 else -1)))
    out.append((x1, y1))
    return out


def burst(d, cx, cy, ro, ri, n=10, rot0=-90, fillv=255):
    star(d, cx, cy, ro, ri, n, rot0, fillv)


def spiral(d, cx, cy, r0, r1, turns, w0, w1, a0=0.0, n=90, ry=1.0):
    path = []
    for i in range(n + 1):
        t = i / n
        a = a0 + t * turns * 2 * math.pi
        r = r0 + (r1 - r0) * t
        path.append((cx + math.cos(a) * r, cy + math.sin(a) * r * ry))
    stroke(d, path, w0, w1)


STEEL = ((252, 252, 255), (140, 150, 178))
GOLD = ((255, 242, 176), (204, 132, 44))
SKIN = ((255, 228, 192), (214, 140, 90))
CLOTH = ((250, 246, 236), (190, 178, 160))


# ---- weapons ----------------------------------------------------------------------------------------------------------
def sword_masks(cx, cy, s, ang, length=1.0, blade_w=0.08, guard_w=0.32):
    parts = GB.sword_parts(length, blade_w, guard_w)
    full = shape(lambda d: [d.polygon(xf(q, cx, cy, s, ang), fill=255) for q in parts])
    blade = shape(lambda d: d.polygon(xf(parts[0], cx, cy, s, ang), fill=255))
    hilt = shape(lambda d: [d.polygon(xf(q, cx, cy, s, ang), fill=255) for q in parts[1:]])
    fuller = shape(lambda d: d.polygon(xf([(-0.009, -0.40 * length), (0.009, -0.40 * length), (0.009, 0.13),
                                           (-0.009, 0.13)], cx, cy, s, ang), fill=255))
    return full, blade, hilt, fuller


def outline(c, m, px=9, color=(14, 10, 24, 235)):
    """A dark keyline around a weapon so a slim blade still separates from a busy field at bar size."""
    K.fill(c, soften(m.filter(ImageFilter.MaxFilter(px)), 2), color)


def sword(c, cx, cy, s, ang, glowc=None, blade=STEEL, hilt=GOLD, gr=14, gs=1.2, sh=True, fuller=(110, 120, 150),
          gem=None, keyline=False, **kw):
    full, bl, hl, fu = sword_masks(cx, cy, s, ang, **kw)
    if glowc:
        K.glow(c, full, rgba(glowc), gr, gs)
    if sh:
        K.shadow(c, full, 5, 8, 8, 165)
    if keyline:
        outline(c, full)
    K.fill(c, soften(bl), paint(blade))
    if fuller:
        K.fill(c, soften(fu, 1.5), rgba(fuller, 170))
    K.fill(c, soften(hl), paint(hilt))
    if gem:
        g = shape(lambda d: d.polygon(xf(ell(0, 0.18, 0.03, 0.03, 16), cx, cy, s, ang), fill=255))
        lit(c, g, gem, gem, 4, 1.2)
    return full


def dagger_masks(cx, cy, s, ang, wide=1.0):
    parts = [[(x * wide, y) for x, y in q] for q in GB.dagger_parts()]
    full = shape(lambda d: [d.polygon(xf(q, cx, cy, s, ang), fill=255) for q in parts])
    blade = shape(lambda d: d.polygon(xf(parts[0], cx, cy, s, ang), fill=255))
    hilt = shape(lambda d: [d.polygon(xf(q, cx, cy, s, ang), fill=255) for q in parts[1:]])
    edge = shape(lambda d: d.polygon(xf([(0, -0.44), (0.012 * wide, -0.36), (0.012 * wide, 0.07), (-0.004, 0.07),
                                         (-0.004, -0.36)], cx, cy, s, ang), fill=255))
    return full, blade, hilt, edge


def dagger(c, cx, cy, s, ang, glowc=None, blade=STEEL, hilt=((150, 96, 60), (70, 36, 20)), gr=14, gs=1.2, sh=True,
           edge=(255, 255, 255), wide=1.0, keyline=False):
    full, bl, hl, ed = dagger_masks(cx, cy, s, ang, wide)
    if glowc:
        K.glow(c, full, rgba(glowc), gr, gs)
    if sh:
        K.shadow(c, full, 5, 8, 8, 165)
    if keyline:
        outline(c, full)
    K.fill(c, soften(bl), paint(blade))
    if edge:
        K.fill(c, soften(ed, 1.5), rgba(edge, 150))
    K.fill(c, soften(hl), paint(hilt))
    return full


def fist_masks(cx, cy, s, deg=0.0, wrist=True):
    """A fist seen from the front (knuckles up), with a cloth-wrapped wrist below; deg turns it counter-clockwise."""
    f = shape(lambda d: K.fist_front(d, cx, cy, s))
    w = shape(lambda d: d.rounded_rectangle(pts([(cx - 0.16 * s, cy + 0.12 * s), (cx + 0.14 * s, cy + 0.50 * s)]),
                                            radius=0.03 * W * s, fill=255)) if wrist else mask()
    ln = shape(lambda d: K.fist_lines(d, cx, cy, s))
    wl = shape(lambda d: [d.line(pts([(cx - 0.16 * s, cy + y * s), (cx + 0.14 * s, cy + (y - 0.06) * s)]), fill=255,
                                 width=max(1, int(0.016 * W * s))) for y in (0.26, 0.36, 0.46)]) if wrist else mask()
    if deg:
        f, w, ln, wl = (rot(m, deg, cx, cy) for m in (f, w, ln, wl))
    return f, w, ln, wl


def fist(c, cx, cy, s, deg=0.0, glowc=None, skin=SKIN, cloth=CLOTH, gr=18, gs=1.3, sh=True, wrist=True,
         line=(120, 60, 36)):
    f, w, ln, wl = fist_masks(cx, cy, s, deg, wrist)
    full = ImageChops.lighter(f, w)
    if glowc:
        K.glow(c, full, rgba(glowc), gr, gs)
    if sh:
        K.shadow(c, full, 5, 8, 8, 160)
    if wrist:
        K.fill(c, soften(w), paint(cloth))
        K.fill(c, soften(inter(wl, w), 1.4), (120, 100, 80, 150))
    K.fill(c, soften(f), paint(skin))
    tfill(c, scale(soften(ln, 1.5), 0.7), rgba(line))
    return full


LEG = [(x, y * 1.45) for x, y in ((-0.50, -0.075), (0.05, -0.07), (0.12, -0.11), (0.23, -0.10), (0.33, -0.055),
                                  (0.37, 0.0), (0.345, 0.045), (0.12, 0.075), (0.03, 0.08), (-0.50, 0.085))]


def leg(c, cx, cy, s, ang, glowc=None, skin=SKIN, cloth=CLOTH, gr=16, gs=1.3, sh=True):
    """A bare kicking leg, foot at the +x end (turned clockwise by ang degrees), a wrap at the ankle."""
    m = shape(lambda d: d.polygon(xf(LEG, cx, cy, s, ang), fill=255))
    band = shape(lambda d: d.polygon(xf([(-0.10, -0.2), (0.04, -0.2), (0.04, 0.2), (-0.10, 0.2)], cx, cy, s, ang),
                                     fill=255))
    if glowc:
        K.glow(c, m, rgba(glowc), gr, gs)
    if sh:
        K.shadow(c, m, 5, 8, 8, 160)
    K.fill(c, soften(m), paint(skin))
    K.fill(c, soften(inter(band, m)), paint(cloth))
    return m


def wind_curls(c, spec, color=(235, 255, 245), glowc=(150, 255, 200), alpha=255):
    """Wind: tapered arcs (cx, cy, r, a0, a1, w)."""
    m = shape(lambda d: [swoosh(d, cx, cy, r, a0, a1, w, 'end') for cx, cy, r, a0, a1, w in spec])
    K.glow(c, m, rgba(glowc), 10, 1.3)
    tfill(c, scale(soften(m), alpha / 255), rgba(color))


def flames(d, spec):
    for cx, base, w, h, lean in spec:
        GA.flame(d, cx, base, w, h, lean)


def fire_aura(c, spec, outer=((255, 200, 70), (230, 60, 20)), glowc=(255, 110, 30), core=None):
    m = shape(lambda d: flames(d, spec))
    K.glow(c, m, rgba(glowc), 26, 1.3)
    K.fill(c, soften(m, 2), K.linear(rgba(outer[0]), rgba(outer[1]), 270))
    if core:
        cm = shape(lambda d: flames(d, core))
        K.glow(c, cm, (255, 240, 200, 255), 10)
        K.fill(c, soften(cm, 2), K.linear((255, 250, 220, 255), (255, 170, 60, 255), 270))


def stun_stars(c, cx, cy, rx, ry, n=3, color=(255, 240, 120), phase=0.0):
    m = mask()
    d = ImageDraw.Draw(m)
    ring = shape(lambda dd: dd.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255,
                                       width=int(0.012 * W)))
    tfill(c, scale(soften(ring, 2), 0.55), rgba(color))
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        star(d, cx + math.cos(a) * rx, cy + math.sin(a) * ry, 0.065, 0.028, 5)
    K.glow(c, m, rgba(color), 8, 1.4)
    K.fill(c, soften(m), K.linear((255, 255, 230, 255), rgba(color), 90))


def note(c, cx, cy, s, flags=1, glowc=(220, 230, 255), fillp=((255, 255, 255), (190, 200, 240)), ang=0.0):
    m = shape(lambda d: GB.note(d, cx, cy, s, flags, ang))
    lit(c, m, fillp, glowc, 10, 1.3, sh=True)


# ---- hand-to-hand ---------------------------------------------------------------------------------------------------
def combo():
    """A fist and three bright hits landing in a row."""
    c = bg((60, 120, 200), (6, 14, 36))
    st = mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.62, 0.06), (0.74, 0.10), (0.86, 0.18)):
        sd.rounded_rectangle(pts([(x0, y - 0.016), (0.30, y + 0.016)]), radius=0.016 * W, fill=170)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (220, 236, 255, 255))
    hits = [(0.70, 0.66, 0.10), (0.76, 0.44, 0.12), (0.66, 0.22, 0.14)]
    for i, (x, y, r) in enumerate(hits):
        b = shape(lambda d, x=x, y=y, r=r: burst(d, x, y, r, r * 0.45, 8, -90 + i * 12))
        lit(c, b, K.radial((255, 255, 230, 255), (255, 190, 70, 255), x, y, r), (255, 210, 120), 12, 1.3)
    fist(c, 0.40, 0.48, 0.80, -28, (160, 210, 255))
    num = shape(lambda d: [d.ellipse(pts([(x - 0.022, y - 0.022), (x + 0.022, y + 0.022)]), fill=255)
                           for x, y, _ in hits])
    K.fill(c, soften(num), (255, 255, 255, 255))
    return K.finish(c)


def shoulder_tackle():
    """A charging body leading with an armoured shoulder, slamming into a burst of impact; stun stars above."""
    c = bg((150, 96, 30), (24, 12, 2), 0.66, 0.5)
    b = shape(lambda d: burst(d, 0.76, 0.46, 0.30, 0.12, 11, -80))
    lit(c, b, K.radial((255, 255, 230, 255), (255, 160, 40, 255), 0.76, 0.46, 0.3), (255, 220, 120), 20, 1.4)
    st = mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.38, 0.06), (0.52, 0.03), (0.66, 0.07)):
        sd.rounded_rectangle(pts([(x0, y - 0.02), (0.26, y + 0.02)]), radius=0.02 * W, fill=200)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (255, 236, 190, 255))

    def body(d):
        stroke(d, [(0.36, 0.60), (0.24, 0.72), (0.12, 0.86)], 0.13, 0.08)                   # back leg, driving
        stroke(d, [(0.40, 0.62), (0.52, 0.72), (0.48, 0.88)], 0.12, 0.08)                   # front leg, bent
        d.polygon(pts([(0.28, 0.56), (0.50, 0.36), (0.66, 0.46), (0.46, 0.68), (0.32, 0.68)]), fill=255)  # torso
        d.ellipse(pts([(0.40, 0.26), (0.54, 0.40)]), fill=255)                                # head, ducked
    m = shape(body)
    lit(c, m, ((150, 160, 190), (52, 56, 84)), (255, 230, 160), 10, 1.4, sh=True)
    pad = shape(lambda d: d.chord(pts([(0.48, 0.32), (0.74, 0.58)]), -150, 60, fill=255))
    lit(c, pad, K.linear((255, 244, 190, 255), (200, 120, 30, 255), 120), (255, 240, 180), 8, 1.3, sh=True)
    rim = shape(lambda d: d.arc(pts([(0.48, 0.32), (0.74, 0.58)]), -150, 60, fill=255, width=int(0.016 * W)))
    tfill(c, soften(rim, 1.5), (120, 60, 10, 220))
    stun_stars(c, 0.66, 0.18, 0.16, 0.05, 3, (255, 236, 110), 0.4)
    return K.finish(c)


def one_inch_punch():
    """Knuckles a hair from the target, a shockwave rippling out (defence ignored)."""
    c = bg((40, 150, 140), (4, 24, 24), 0.62, 0.5)
    rings = mask()
    rd = ImageDraw.Draw(rings)
    for r, a in ((0.12, 255), (0.21, 200), (0.30, 140), (0.39, 90)):
        rd.arc(pts([(0.66 - r, 0.5 - r), (0.66 + r, 0.5 + r)]), -70, 70, fill=a, width=int(0.03 * W))
    K.glow(c, rings, (150, 255, 230, 255), 10, 1.3)
    K.fill(c, soften(rings, 2), (230, 255, 248, 255))
    core = shape(lambda d: d.ellipse(pts([(0.60, 0.44), (0.72, 0.56)]), fill=255))
    K.glow(c, core, (255, 255, 255, 255), 16, 1.6)
    K.fill(c, soften(core, 5), (255, 255, 255, 255))
    fist(c, 0.40, 0.50, 0.86, -90, (160, 255, 230))
    return K.finish(c)


def backhand_blow():
    """A fist whipping back in a wide arc, a critical spark at the end."""
    c = bg((130, 70, 190), (18, 6, 34))
    arc = shape(lambda d: swoosh(d, 0.5, 0.52, 0.32, 330, 170, 0.14, 'end'))
    K.glow(c, arc, (210, 160, 255, 255), 14, 1.2)
    K.fill(c, soften(arc), K.linear((255, 240, 255, 255), (190, 140, 255, 255), 0))
    fist(c, 0.30, 0.54, 0.72, 70, (220, 180, 255))
    sparkles(c, [(0.20, 0.30, 0.10), (0.80, 0.24, 0.06)], (230, 200, 255))
    return K.finish(c)


def raging_fists():
    """Two fists in a roaring red rage."""
    c = bg((180, 24, 24), (24, 2, 4), 0.5, 0.62, 0.66)
    fire_aura(c, [(0.5, 0.94, 0.40, 0.86, 0.0), (0.22, 0.94, 0.14, 0.52, -0.08), (0.78, 0.94, 0.14, 0.56, 0.08)],
              ((255, 150, 60), (190, 20, 20)), (240, 40, 30))
    fist(c, 0.34, 0.50, 0.62, 18, (255, 120, 60))
    fist(c, 0.64, 0.46, 0.68, -14, (255, 120, 60))
    motes(c, 5, 14, (0.18, 0.08, 0.82, 0.4), (0.006, 0.013), (255, 210, 160), (255, 90, 50))
    return K.finish(c)


def spinning_attack():
    """A fist at the eye of a whirling ring of blows (hits all around)."""
    c = bg((70, 160, 70), (6, 26, 6))
    whirl = shape(lambda d: [swoosh(d, 0.5, 0.5, 0.34, a, a + 100, 0.10, 'end') for a in (0, 120, 240)])
    K.glow(c, whirl, (200, 255, 170, 255), 14, 1.3)
    K.fill(c, soften(whirl), (240, 255, 225, 255))
    for a in (100, 220, 340):
        x, y = 0.5 + math.cos(math.radians(a)) * 0.34, 0.5 + math.sin(math.radians(a)) * 0.34
        b = shape(lambda d, x=x, y=y: burst(d, x, y, 0.07, 0.03, 6))
        lit(c, b, (255, 255, 220), (255, 240, 150), 8, 1.4)
    fist(c, 0.5, 0.46, 0.58, 0, (200, 255, 170))
    return K.finish(c)


def howling_fist():
    """A fist thrust up against a great moon, howling rings of ki around it."""
    c = bg((50, 60, 160), (4, 6, 28), 0.5, 0.35)
    moon = shape(lambda d: d.ellipse(pts([(0.46, 0.10), (0.84, 0.48)]), fill=255))
    K.glow(c, moon, (255, 240, 170, 255), 26, 1.3)
    K.fill(c, soften(moon), K.radial((255, 250, 220, 255), (240, 200, 110, 255), 0.60, 0.24, 0.3))
    crat = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                            for x, y, r in ((0.58, 0.24, 0.04), (0.72, 0.20, 0.03), (0.72, 0.36, 0.05))])
    tfill(c, scale(soften(crat, 4), 0.35), (190, 140, 60, 255))
    rings = mask()
    rd = ImageDraw.Draw(rings)
    for r in (0.20, 0.29, 0.38):
        rd.arc(pts([(0.38 - r, 0.56 - r), (0.38 + r, 0.56 + r)]), 190, 250, fill=255, width=int(0.024 * W))
        rd.arc(pts([(0.38 - r, 0.56 - r), (0.38 + r, 0.56 + r)]), 100, 150, fill=255, width=int(0.024 * W))
    K.glow(c, rings, (150, 170, 255, 255), 8, 1.3)
    K.fill(c, soften(rings), (230, 236, 255, 255))
    fist(c, 0.40, 0.56, 0.70, -22, (120, 140, 255), skin=((250, 214, 180), (180, 110, 70)))
    return K.finish(c)


def dragon_kick():
    """A flying kick with a golden fire-dragon racing alongside: a short wavy body and a big open-jawed head."""
    c = bg((190, 70, 24), (30, 6, 2), 0.55, 0.45)
    path = [(0.06 + 0.40 * t, 0.50 - 0.10 * t + math.sin(t * math.pi * 1.5) * 0.08) for t in (i / 59 for i in range(60))]
    trail = shape(lambda d: stroke(d, path, 0.04, 0.20))
    K.glow(c, trail, (255, 160, 30, 255), 18, 1.5)
    K.fill(c, soften(trail, 2), K.linear((255, 236, 140, 255), (220, 80, 16, 255), 180))
    hx, hy, hs, ha = 0.58, 0.34, 1.2, 8
    upper = [(-0.14, 0.04), (-0.12, -0.10), (0.00, -0.11), (0.12, -0.09), (0.26, -0.07), (0.29, -0.01),
             (0.20, 0.01), (0.18, 0.04), (0.15, 0.01), (0.02, 0.02)]
    lower = [(-0.13, 0.065), (0.02, 0.065), (0.21, 0.12), (0.19, 0.17), (-0.04, 0.17), (-0.14, 0.12)]
    horns = [[(-0.08, -0.08), (-0.30, -0.20), (-0.02, -0.10)], [(-0.12, -0.04), (-0.34, -0.06), (-0.12, 0.0)]]
    head = shape(lambda d: [d.polygon(xf(q, hx, hy, hs, ha), fill=255) for q in [upper, lower] + horns])
    lit(c, head, ((255, 248, 180), (232, 126, 30)), (255, 200, 80), 12, 1.6, sh=True)
    eye = shape(lambda d: d.polygon(xf(ell(0.0, -0.05, 0.03, 0.02, 16), hx, hy, hs, ha), fill=255))
    K.fill(c, soften(eye), (140, 20, 6, 255))
    leg(c, 0.38, 0.70, 0.80, -14, (255, 200, 120))
    return K.finish(c)


def asuran_fists():
    """Asura's many arms fanned out behind a central fist, every hand clenched."""
    c = bg((210, 120, 40), (40, 12, 4), 0.5, 0.55)
    rays(c, 0.5, 0.56, 16, 0.8, (255, 230, 170), 80, 0.06, 6)
    halo = shape(lambda d: d.ellipse(pts([(0.16, 0.16), (0.84, 0.84)]), outline=255, width=int(0.022 * W)))
    K.glow(c, halo, (255, 200, 100, 255), 10, 1.2)
    K.fill(c, soften(halo), (255, 230, 160, 255))
    for a in (-155, -25, -112, -68):
        ar = math.radians(a)
        ex, ey = 0.5 + math.cos(ar) * 0.31, 0.60 + math.sin(ar) * 0.31
        arm = shape(lambda d, ex=ex, ey=ey: stroke(d, [(0.5, 0.66), (ex, ey)], 0.07, 0.09))
        lit(c, arm, ((230, 170, 120), (150, 80, 50)), (255, 200, 110), 6, 1.0, sh=True)
        fist(c, ex, ey, 0.36, -(a + 90), (255, 210, 120), gr=8, sh=True, wrist=False,
             skin=((250, 210, 170), (200, 120, 70)))
    fist(c, 0.5, 0.60, 0.56, 0, (255, 230, 150), gr=16, gs=1.4)
    return K.finish(c)


def final_heaven():
    """Relic (Spharai): a fist driven straight up into a pillar of heavenly light."""
    c = bg((90, 150, 230), (10, 18, 50), 0.5, 0.3, 0.8)
    rays(c, 0.5, 0.26, 20, 0.75, (255, 246, 200), 110, 0.05, 6)
    pillar = shape(lambda d: d.polygon(pts([(0.40, 0.0), (0.60, 0.0), (0.56, 0.60), (0.44, 0.60)]), fill=255))
    K.glow(c, pillar, (255, 240, 170, 255), 28, 1.3)
    K.fill(c, soften(pillar, 10), K.linear((255, 255, 250, 255), (255, 220, 140, 180), 90))
    cloud = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.6), (x + r, y + r * 0.6)]), fill=255)
                             for x, y, r in ((0.18, 0.84, 0.14), (0.36, 0.88, 0.16), (0.64, 0.88, 0.16),
                                             (0.82, 0.84, 0.14), (0.5, 0.92, 0.18))])
    K.fill(c, soften(cloud, 6), K.linear((255, 255, 255, 255), (190, 200, 240, 255), 90))
    fist(c, 0.5, 0.50, 0.80, 0, (255, 230, 140), skin=((255, 240, 200), (230, 160, 80)), gr=24, gs=1.5,
         cloth=((255, 246, 210), (230, 190, 100)))
    sparkles(c, [(0.24, 0.24, 0.09), (0.78, 0.36, 0.07), (0.70, 0.12, 0.05)], (255, 230, 140))
    return K.finish(c)


def ascetics_fury():
    """Mythic (Glanzfaust): a fist ringed by prayer beads, ablaze with a monk's fury."""
    c = bg((170, 30, 80), (26, 2, 14), 0.5, 0.55)
    fire_aura(c, [(0.5, 0.92, 0.34, 0.84, 0.0), (0.28, 0.90, 0.13, 0.50, -0.08), (0.72, 0.90, 0.13, 0.54, 0.08)],
              ((255, 190, 90), (210, 30, 60)), (255, 60, 90))
    beads = mask()
    bd = ImageDraw.Draw(beads)
    for i in range(18):
        a = 2 * math.pi * i / 18
        x, y = 0.5 + math.cos(a) * 0.33, 0.50 + math.sin(a) * 0.33
        r = 0.042 if i % 6 else 0.058
        bd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    K.shadow(c, beads, 3, 5, 5, 150)
    K.fill(c, soften(beads), K.linear((255, 236, 170, 255), (180, 110, 40, 255), 90))
    shine = shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(2 * math.pi * i / 18) * 0.33 - 0.024,
                                              0.5 + math.sin(2 * math.pi * i / 18) * 0.33 - 0.03),
                                             (0.5 + math.cos(2 * math.pi * i / 18) * 0.33 - 0.004,
                                              0.5 + math.sin(2 * math.pi * i / 18) * 0.33 - 0.01)]), fill=255)
                             for i in range(18)])
    K.fill(c, soften(shine), (255, 255, 240, 220))
    fist(c, 0.5, 0.46, 0.66, 0, (255, 140, 90), gr=20, gs=1.5)
    return K.finish(c)


def stringing_pummel():
    """A fist hammering down again and again, after-images stacked above it."""
    c = bg((40, 130, 180), (4, 18, 34))
    crack = shape(lambda d: [d.line(pts(bolt_path(0.5, 0.86, x, y, s, 4, 0.03)), fill=255, width=int(0.016 * W))
                             for x, y, s in ((0.18, 0.90, 1), (0.82, 0.92, 2), (0.30, 0.98, 3), (0.70, 1.0, 4))])
    imp = shape(lambda d: burst(d, 0.5, 0.86, 0.26, 0.08, 9, -90))
    lit(c, imp, K.radial((255, 255, 255, 255), (130, 220, 255, 255), 0.5, 0.86, 0.2), (160, 230, 255), 14, 1.3)
    K.fill(c, soften(crack), (230, 250, 255, 255))
    for x, y, dg, a in ((0.38, 0.22, 175, 0.45), (0.64, 0.20, 185, 0.45), (0.25, 0.38, 160, 0.75),
                        (0.75, 0.36, 200, 0.75)):
        f, w, _, _ = fist_masks(x, y, 0.50, dg)
        tfill(c, scale(soften(ImageChops.lighter(f, w), 3), a), (220, 245, 255, 255))
    fist(c, 0.5, 0.52, 0.64, 180, (150, 230, 255))
    return K.finish(c)


def tornado_kick():
    """A kick swept up in a tornado."""
    c = bg((70, 160, 130), (4, 26, 22), 0.5, 0.5)
    tw = mask()
    td = ImageDraw.Draw(tw)
    for i in range(7):
        t = i / 6
        y = 0.18 + t * 0.64
        rx = 0.36 - t * 0.26
        td.arc(pts([(0.5 - rx, y - rx * 0.28), (0.5 + rx, y + rx * 0.28)]), 10 + i * 30, 300 + i * 30, fill=255,
               width=int((0.028 - t * 0.012) * W))
    K.glow(c, tw, (180, 255, 220, 255), 12, 1.3)
    K.fill(c, soften(tw), (235, 255, 245, 255))
    leg(c, 0.46, 0.50, 0.82, -12, (210, 255, 230))
    motes(c, 8, 12, (0.15, 0.15, 0.85, 0.85), (0.006, 0.014), (240, 255, 245), (150, 255, 210))
    return K.finish(c)


def victory_smite():
    """Empyrean (Verethragna): a fist in a golden laurel of victory, a crimson burst behind."""
    c = bg((190, 30, 40), (30, 2, 8), 0.5, 0.45)
    b = shape(lambda d: burst(d, 0.5, 0.46, 0.44, 0.22, 12, -90))
    K.glow(c, b, (255, 120, 60, 255), 20, 1.0)
    K.fill(c, soften(b), K.radial((255, 200, 120, 255), (200, 40, 30, 255), 0.5, 0.46, 0.44))

    def laurel(d, side):
        for i in range(8):
            t = i / 7
            a = math.radians(100 + side * (20 + 120 * t)) if side > 0 else math.radians(80 - (20 + 120 * t))
            a = math.radians(90 + side * (25 + 125 * t))
            x, y = 0.5 + math.cos(a) * 0.34, 0.5 + math.sin(a) * 0.34
            tang = a + side * math.pi / 2
            GA.leaf(d, x, y, tang - side * 0.55, 0.14, 0.035)
        d.arc(pts([(0.16, 0.16), (0.84, 0.84)]), 115 if side > 0 else -90, 270 if side > 0 else 65, fill=255,
              width=int(0.014 * W))
    lr = shape(lambda d: [laurel(d, 1), laurel(d, -1)])
    lit(c, lr, GOLD, (255, 220, 120), 10, 1.3, sh=True)
    fist(c, 0.5, 0.44, 0.66, 0, (255, 220, 140), gr=16, gs=1.4)
    sparkles(c, [(0.78, 0.18, 0.08), (0.22, 0.20, 0.06)], (255, 220, 140))
    return K.finish(c)


def shijin_spiral():
    """Aeonic (Godhands): the four guardian gods' colours spiralling into one fist."""
    c = bg((70, 40, 150), (6, 2, 24), 0.5, 0.5)
    motes(c, 12, 22, (0.1, 0.1, 0.9, 0.9), (0.004, 0.01), (255, 255, 255), (200, 200, 255))
    cols = [((90, 170, 255), (40, 90, 230)), ((255, 120, 60), (220, 40, 30)), ((250, 250, 255), (190, 200, 230)),
            ((90, 220, 160), (20, 120, 100))]
    for k, (cg, cd) in enumerate(cols):
        m = shape(lambda d, k=k: spiral(d, 0.5, 0.5, 0.44, 0.10, 0.9, 0.08, 0.01, k * math.pi / 2))
        K.glow(c, m, rgba(cg), 10, 1.3)
        K.fill(c, soften(m), K.radial(rgba(cg), rgba(cd), 0.5, 0.5, 0.44))
    core = shape(lambda d: d.ellipse(pts([(0.30, 0.30), (0.70, 0.70)]), fill=255))
    K.glow(c, core, (255, 240, 255, 255), 30, 1.2)
    fist(c, 0.5, 0.48, 0.52, 0, (255, 255, 255), gr=14, gs=1.5)
    return K.finish(c)


# ---- dagger ---------------------------------------------------------------------------------------------------------
def wasp_sting():
    """A dagger like a stinger, a green drop of poison at its tip."""
    c = bg((220, 180, 30), (40, 30, 2), 0.5, 0.45)
    stripes = shape(lambda d: [d.polygon(pts([(x, -0.1), (x + 0.10, -0.1), (x + 0.6, 1.1), (x + 0.5, 1.1)]), fill=255)
                               for x in (-0.5, -0.24, 0.02, 0.28, 0.54)])
    tfill(c, scale(soften(stripes, 6), 0.35), (30, 20, 0, 255))
    wings = shape(lambda d: [d.polygon(xf(ell(0.0, -0.13, 0.07, 0.15), 0.58, 0.36, 1.0, a), fill=255)
                             for a in (-50, -20)])
    tfill(c, scale(soften(wings, 2), 0.65), (230, 250, 255, 255))
    dagger(c, 0.58, 0.44, 1.05, 215, (255, 240, 140), hilt=((60, 50, 20), (20, 16, 6)), wide=1.5, keyline=True)
    band = shape(lambda d: [d.polygon(xf([(-0.03, y), (0.03, y), (0.03, y + 0.03), (-0.03, y + 0.03)], 0.58, 0.44,
                                         1.05, 215), fill=255) for y in (0.15, 0.22)])
    K.fill(c, soften(band), (255, 210, 40, 255))
    drop = shape(lambda d: [GB.heart_drop(d, 0.27, 0.80, 0.07), GB.heart_drop(d, 0.17, 0.66, 0.04)])
    lit(c, drop, ((200, 255, 120), (60, 170, 30)), (150, 255, 80), 10, 1.5)
    return K.finish(c)


def viper_bite():
    """A serpent coiled up a dagger, fangs bared."""
    c = bg((50, 130, 70), (4, 22, 8))
    dagger(c, 0.5, 0.54, 1.10, 0, (180, 255, 180))
    path = []
    for i in range(70):
        t = i / 69
        y = 0.80 - 0.50 * t
        x = 0.5 + math.sin(t * math.pi * 3.2) * 0.13
        path.append((x, y))
    sn = shape(lambda d: stroke(d, path, 0.075, 0.05))
    # draw only the front halves of the coils over the blade
    K.shadow(c, sn, 3, 6, 6, 150)
    K.fill(c, soften(sn), K.linear((170, 230, 90, 255), (40, 120, 30, 255), 0))
    belly = shape(lambda d: stroke(d, [(x + 0.012, y + 0.012) for x, y in path], 0.025, 0.015))
    tfill(c, scale(soften(inter(belly, sn), 2), 0.6), (240, 240, 160, 255))
    hx, hy = path[-1]
    head = shape(lambda d: d.polygon(pts([(hx - 0.06, hy + 0.03), (hx - 0.04, hy - 0.06), (hx + 0.08, hy - 0.10),
                                          (hx + 0.14, hy - 0.04), (hx + 0.06, hy + 0.04)]), fill=255))
    lit(c, head, ((170, 230, 90), (40, 120, 30)), (200, 255, 150), 8, 1.2, sh=True)
    fang = shape(lambda d: [d.polygon(pts([(hx + 0.06, hy - 0.02), (hx + 0.08, hy - 0.02), (hx + 0.07, hy + 0.05)]),
                                      fill=255),
                            d.polygon(pts([(hx + 0.10, hy - 0.04), (hx + 0.12, hy - 0.04), (hx + 0.115, hy + 0.03)]),
                                      fill=255)])
    K.fill(c, soften(fang), (255, 255, 255, 255))
    eye = shape(lambda d: d.ellipse(pts([(hx + 0.02, hy - 0.07), (hx + 0.05, hy - 0.04)]), fill=255))
    lit(c, eye, (255, 220, 60), (255, 200, 40), 4)
    return K.finish(c)


def shadowstitch():
    """A dagger pinning a shadow to the ground, stitches binding it."""
    c = bg((100, 90, 150), (10, 8, 24), 0.5, 0.4)
    sh = shape(lambda d: [d.ellipse(pts([(0.14, 0.62), (0.86, 0.90)]), fill=255),
                          d.polygon(pts([(0.30, 0.70), (0.20, 0.34), (0.34, 0.40), (0.42, 0.66)]), fill=255),
                          d.polygon(pts([(0.70, 0.70), (0.80, 0.36), (0.66, 0.42), (0.58, 0.66)]), fill=255)])
    K.glow(c, sh, (170, 150, 255, 255), 12, 1.0)
    K.fill(c, soften(sh, 4), (12, 8, 26, 255))
    st = mask()
    sd = ImageDraw.Draw(st)
    ends = [(0.18, 0.72), (0.26, 0.86), (0.40, 0.90), (0.60, 0.90), (0.74, 0.86), (0.82, 0.72), (0.24, 0.42),
            (0.76, 0.42)]
    for x, y in ends:
        sd.line(pts([(0.5, 0.77), (x, y)]), fill=255, width=int(0.012 * W))
        sd.ellipse(pts([(x - 0.018, y - 0.018), (x + 0.018, y + 0.018)]), fill=255)
    K.glow(c, st, (200, 170, 255, 255), 6, 1.5)
    K.fill(c, soften(st), (240, 230, 255, 255))
    dagger(c, 0.5, 0.44, 1.05, 180, (200, 170, 255), hilt=((140, 100, 200), (50, 20, 90)))
    rip = shape(lambda d: d.ellipse(pts([(0.42, 0.74), (0.58, 0.80)]), fill=255))
    K.glow(c, rip, (220, 200, 255, 255), 8, 1.4)
    return K.finish(c)


def gust_slash():
    """Wind: a dagger slicing, a gust curling off its edge."""
    c = bg((90, 190, 160), (6, 30, 26), 0.45, 0.45)
    wind_curls(c, [(0.50, 0.52, 0.34, 200, 330, 0.09), (0.46, 0.58, 0.24, 170, 300, 0.06),
                   (0.54, 0.46, 0.42, 230, 300, 0.05)])
    dagger(c, 0.50, 0.52, 1.10, 45, (190, 255, 230), wide=1.5, keyline=True)
    motes(c, 3, 8, (0.15, 0.55, 0.85, 0.85), (0.006, 0.012), (240, 255, 250), (160, 255, 220))
    return K.finish(c)


def cyclone():
    """Wind, area: a dagger at the eye of a whirling cyclone."""
    c = bg((120, 180, 60), (12, 28, 4))
    sp = mask()
    sd = ImageDraw.Draw(sp)
    for k in range(4):
        spiral(sd, 0.5, 0.5, 0.44, 0.06, 0.85, 0.07, 0.012, k * math.pi / 2)
    K.glow(c, sp, (220, 255, 160, 255), 12, 1.3)
    K.fill(c, soften(sp), K.radial((255, 255, 240, 255), (200, 250, 150, 255), 0.5, 0.5, 0.42))
    eye = shape(lambda d: d.ellipse(pts([(0.38, 0.38), (0.62, 0.62)]), fill=255))
    K.glow(c, eye, (240, 255, 200, 255), 18, 1.2)
    dagger(c, 0.5, 0.52, 0.72, 0, (230, 255, 190))
    leaves = shape(lambda d: [GA.leaf(d, x, y, a, 0.08, 0.025) for x, y, a in ((0.20, 0.30, 0.5), (0.80, 0.70, 3.6),
                                                                            (0.76, 0.22, 2.0))])
    K.fill(c, soften(leaves), K.linear((200, 250, 120, 255), (90, 160, 40, 255), 90))
    return K.finish(c)


def energy_steal():
    """Blue mana drawn off the foe and into the dagger's tip (Energy Drain: the same, recoloured dark)."""
    c = bg((50, 100, 210), (4, 10, 40), 0.62, 0.38)
    for i in range(7):
        a = math.radians(110 + i * 22)
        x0, y0 = 0.68 + math.cos(a) * 0.46, 0.32 + math.sin(a) * 0.46
        path = [(x0 + (0.68 - x0) * t + math.sin(t * 3.0) * 0.04, y0 + (0.32 - y0) * t) for t in
                (j / 20 for j in range(18))]
        m = shape(lambda d, path=path: stroke(d, path, 0.006, 0.03))
        K.glow(c, m, (120, 180, 255, 255), 6, 1.3)
        K.fill(c, soften(m), (210, 230, 255, 255))
    dagger(c, 0.38, 0.62, 0.95, 45, (150, 200, 255), hilt=((80, 110, 200), (20, 30, 90)), gs=1.6, wide=1.5,
           keyline=True)
    orb = shape(lambda d: d.ellipse(pts([(0.60, 0.24), (0.76, 0.40)]), fill=255))
    K.glow(c, orb, (120, 190, 255, 255), 20, 1.8)
    K.fill(c, soften(orb, 3), K.radial((255, 255, 255, 255), (90, 160, 255, 255), 0.67, 0.31, 0.10))
    return K.finish(c)


def dancing_edge():
    """A dagger whirling in a dance, after-images and a ribbon trailing."""
    c = bg((220, 90, 150), (36, 6, 24))
    rib = []
    for i in range(80):
        t = i / 79
        rib.append((0.14 + 0.72 * t, 0.70 - 0.30 * t + math.sin(t * math.pi * 2) * 0.14))
    r = shape(lambda d: stroke(d, rib, 0.03, 0.07))
    K.glow(c, r, (255, 170, 210, 255), 10, 1.2)
    K.fill(c, soften(r), K.linear((255, 220, 240, 255), (240, 90, 160, 255), 0))
    for ang, a in ((-40, 0.25), (-10, 0.45)):
        full, _, _, _ = dagger_masks(0.52, 0.48, 0.95, ang)
        tfill(c, scale(soften(full, 3), a), (255, 230, 245, 255))
    dagger(c, 0.54, 0.48, 0.95, 30, (255, 200, 230), hilt=((240, 120, 170), (120, 30, 70)))
    sparkles(c, [(0.20, 0.26, 0.08), (0.84, 0.70, 0.06)], (255, 200, 230))
    return K.finish(c)


def shark_bite():
    """Jaws snapping shut around a dagger, sea-blue."""
    c = bg((40, 120, 190), (2, 14, 36), 0.5, 0.5)

    def jaw(d, top):
        base = 0.28 if top else 0.72
        tip = 0.46 if top else 0.54
        n = 7
        for i in range(n):
            x0 = 0.16 + i * (0.68 / n)
            x1 = x0 + 0.68 / n
            curve = 0.05 * math.sin(math.pi * (i + 0.5) / n)
            by = base + (curve if top else -curve)
            ty = tip + (curve if top else -curve) * 0.5
            d.polygon(pts([(x0, by), (x1, by), ((x0 + x1) / 2, ty)]), fill=255)
        d.chord(pts([(0.10, base - 0.30), (0.90, base + 0.02)]) if top else
                pts([(0.10, base - 0.02), (0.90, base + 0.30)]), 0 if top else 180, 180 if top else 360, fill=255)
    gums = shape(lambda d: [d.chord(pts([(0.08, -0.04), (0.92, 0.32)]), 0, 180, fill=255),
                            d.chord(pts([(0.08, 0.68), (0.92, 1.04)]), 180, 360, fill=255)])
    K.fill(c, soften(gums, 3), K.linear((150, 30, 50, 255), (60, 6, 20, 255), 90))
    teeth = shape(lambda d: [jaw(d, True), jaw(d, False)])
    teeth = minus(teeth, gums)
    K.glow(c, teeth, (200, 230, 255, 255), 8, 1.0)
    K.fill(c, soften(teeth), K.linear((255, 255, 255, 255), (210, 220, 230, 255), 90))
    dagger(c, 0.50, 0.50, 0.95, 90, (170, 220, 255), hilt=((60, 120, 180), (14, 40, 80)))
    return K.finish(c)


def evisceration():
    """A dagger and five raking red slashes."""
    c = bg((150, 20, 30), (20, 2, 6), 0.5, 0.45)
    sl = shape(lambda d: [slash(d, 0.18 + i * 0.12, 0.16 + (i % 2) * 0.04, 0.10 + i * 0.12 + 0.18, 0.84 - (i % 2) * 0.06,
                                0.05) for i in range(5)])
    K.glow(c, sl, (255, 70, 60, 255), 12, 1.3)
    K.fill(c, soften(sl), K.linear((255, 220, 210, 255), (240, 60, 50, 255), 90))
    dagger(c, 0.40, 0.58, 0.86, 225, (255, 140, 120), hilt=((90, 40, 40), (30, 8, 8)), wide=1.5, keyline=True)
    drops = shape(lambda d: [GB.heart_drop(d, x, y, r) for x, y, r in ((0.78, 0.86, 0.03), (0.66, 0.92, 0.022))])
    lit(c, drops, ((255, 110, 110), (170, 0, 10)), (255, 60, 60), 6)
    return K.finish(c)


def mercy_stroke():
    """Relic (Mandau): a golden blade falling in the finishing blow, a halo of light at the point."""
    c = bg((120, 20, 60), (16, 2, 12), 0.5, 0.65)
    rays(c, 0.5, 0.80, 18, 0.8, (255, 220, 200), 110, 0.05, 6)
    halo = shape(lambda d: d.ellipse(pts([(0.24, 0.66), (0.76, 0.94)]), outline=255, width=int(0.022 * W)))
    K.glow(c, halo, (255, 220, 140, 255), 14, 1.4)
    K.fill(c, soften(halo), (255, 240, 190, 255))
    pt = shape(lambda d: d.ellipse(pts([(0.40, 0.72), (0.60, 0.88)]), fill=255))
    K.glow(c, pt, (255, 255, 230, 255), 24, 1.7)
    K.fill(c, soften(pt, 8), (255, 255, 240, 255))
    # the curved Mandau-like dagger, point down
    full, bl, hl, ed = dagger_masks(0.5, 0.40, 1.15, 180)
    K.glow(c, full, (255, 210, 120, 255), 18, 1.4)
    K.shadow(c, full, 5, 8, 8, 160)
    K.fill(c, soften(bl), K.linear((255, 252, 230, 255), (220, 180, 110, 255), 90))
    K.fill(c, soften(ed, 1.5), (255, 255, 255, 170))
    K.fill(c, soften(hl), paint(GOLD))
    gem = shape(lambda d: d.ellipse(pts([(0.475, 0.24), (0.525, 0.29)]), fill=255))
    lit(c, gem, (230, 30, 60), (255, 60, 80), 5)
    sparkles(c, [(0.22, 0.24, 0.08), (0.80, 0.32, 0.06)], (255, 220, 160))
    return K.finish(c)


def mandalic_stab():
    """Mythic (Vajra): a dagger thrust through the heart of a glowing mandala."""
    c = bg((230, 130, 40), (40, 14, 4), 0.5, 0.5)
    m = mask()
    d = ImageDraw.Draw(m)
    d.ellipse(pts([(0.12, 0.12), (0.88, 0.88)]), outline=255, width=int(0.016 * W))
    d.ellipse(pts([(0.24, 0.24), (0.76, 0.76)]), outline=255, width=int(0.012 * W))
    for i in range(12):
        a = 2 * math.pi * i / 12
        GA.leaf(d, 0.5 + math.cos(a) * 0.20, 0.5 + math.sin(a) * 0.20, a, 0.17, 0.045, 0)
        GA.leaf(d, 0.5 + math.cos(a) * 0.20, 0.5 + math.sin(a) * 0.20, a, 0.17, 0.045, 255)
    for i in range(24):
        a = 2 * math.pi * (i + 0.5) / 24
        x, y = 0.5 + math.cos(a) * 0.41, 0.5 + math.sin(a) * 0.41
        d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
    K.glow(c, m, (255, 200, 90, 255), 14, 1.3)
    K.fill(c, soften(m), K.radial((255, 250, 210, 255), (255, 170, 60, 255), 0.5, 0.5, 0.42))
    inner = shape(lambda dd: dd.polygon(pts(GA.star_pts(0.5, 0.5, 8, 0.15, 0.09)), fill=255))
    K.fill(c, soften(inner), (170, 40, 90, 255))
    dagger(c, 0.5, 0.50, 1.00, 0, (255, 230, 160), hilt=GOLD)
    jewel = shape(lambda dd: dd.ellipse(pts([(0.475, 0.555), (0.525, 0.605)]), fill=255))
    lit(c, jewel, (60, 200, 220), (120, 255, 255), 5)
    return K.finish(c)


def mordant_rime():
    """Mythic (Carnwenhan): a bard's dagger singing a cold song, rime and notes about it."""
    c = bg((70, 110, 200), (6, 10, 40), 0.5, 0.42)
    fr = mask()
    fd = ImageDraw.Draw(fr)
    for cx, cy, r in ((0.24, 0.30, 0.09), (0.78, 0.74, 0.07), (0.80, 0.24, 0.05)):
        for k in range(3):
            a = math.pi * k / 3
            fd.line(pts([(cx - math.cos(a) * r, cy - math.sin(a) * r), (cx + math.cos(a) * r, cy + math.sin(a) * r)]),
                    fill=255, width=int(0.014 * W))
    K.glow(c, fr, (180, 230, 255, 255), 8, 1.4)
    K.fill(c, soften(fr), (240, 250, 255, 255))
    motes(c, 6, 14, (0.12, 0.12, 0.88, 0.88), (0.005, 0.011), (240, 250, 255), (150, 210, 255))
    dagger(c, 0.56, 0.48, 1.05, 30, (170, 220, 255), blade=((250, 254, 255), (150, 200, 240)),
           hilt=((120, 80, 200), (40, 20, 90)))
    note(c, 0.30, 0.78, 0.62, 2, (200, 180, 255), ((255, 250, 220), (220, 180, 90)))
    return K.finish(c)


def pyrrhic_kleos():
    """Empyrean (Terpsichore): twin dancer's daggers crossed in a whirl of flame-red ribbon."""
    c = bg((230, 90, 40), (40, 6, 10), 0.5, 0.5)
    rib = []
    for i in range(100):
        t = i / 99
        a = t * math.pi * 3.0 + 0.3
        r = 0.40 - 0.14 * t
        rib.append((0.5 + math.cos(a) * r, 0.52 + math.sin(a) * r * 0.62))
    r = shape(lambda d: stroke(d, rib, 0.02, 0.06))
    K.glow(c, r, (255, 120, 60, 255), 12, 1.3)
    K.fill(c, soften(r), K.linear((255, 230, 150, 255), (230, 40, 60, 255), 90))
    dagger(c, 0.40, 0.50, 0.95, -32, (255, 200, 120), hilt=GOLD)
    dagger(c, 0.60, 0.50, 0.95, 32, (255, 200, 120), hilt=GOLD)
    sparkles(c, [(0.50, 0.18, 0.09), (0.18, 0.70, 0.06), (0.82, 0.70, 0.06)], (255, 210, 140))
    return K.finish(c)


def aeolian_edge():
    """Wind magic, area: blades of wind radiating out from a dagger's swing."""
    c = bg((50, 170, 190), (2, 22, 30), 0.5, 0.5)
    wind_curls(c, [(0.5, 0.5, 0.38, a, a + 70, 0.08) for a in (0, 90, 180, 270)],
               (230, 255, 255), (130, 240, 255))
    wind_curls(c, [(0.5, 0.5, 0.26, a, a + 60, 0.05) for a in (45, 135, 225, 315)],
               (230, 255, 255), (130, 240, 255), 200)
    core = shape(lambda d: d.ellipse(pts([(0.36, 0.36), (0.64, 0.64)]), fill=255))
    K.glow(c, core, (180, 255, 255, 255), 20, 1.1)
    dagger(c, 0.5, 0.50, 0.78, 45, (200, 255, 255))
    return K.finish(c)


def rudras_storm():
    """Empyrean (Twashtar): a dagger lunging out of a black thundercloud, red lightning around it."""
    c = bg((90, 40, 140), (8, 2, 20), 0.5, 0.35)
    cloud = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.7), (x + r, y + r * 0.7)]), fill=255)
                             for x, y, r in ((0.22, 0.24, 0.16), (0.42, 0.16, 0.18), (0.64, 0.18, 0.18),
                                             (0.82, 0.28, 0.14), (0.52, 0.30, 0.20), (0.30, 0.34, 0.14))])
    K.glow(c, cloud, (180, 120, 255, 255), 12, 0.9)
    K.fill(c, soften(cloud, 4), K.linear((70, 60, 100, 255), (20, 12, 34, 255), 90))
    bolts = shape(lambda d: [d.line(pts(bolt_path(x0, y0, x1, y1, s, 6, 0.05)), fill=255, width=int(w * W),
                                    joint='curve')
                             for x0, y0, x1, y1, s, w in ((0.24, 0.34, 0.12, 0.76, 3, 0.03),
                                                          (0.80, 0.34, 0.88, 0.72, 5, 0.03),
                                                          (0.34, 0.40, 0.30, 0.88, 9, 0.02))])
    K.glow(c, bolts, (255, 50, 80, 255), 16, 1.8)
    K.fill(c, soften(bolts), (255, 230, 240, 255))
    dagger(c, 0.56, 0.56, 1.20, 205, (255, 140, 170), gr=18, gs=1.5, hilt=((230, 60, 80), (110, 10, 30)))
    sparkles(c, [(0.36, 0.86, 0.08)], (255, 140, 180))
    return K.finish(c)


# ---- sword ----------------------------------------------------------------------------------------------------------
def fast_blade():
    """A sword and two quick bright cuts."""
    c = bg((60, 140, 220), (4, 14, 40))
    sl = shape(lambda d: [slash(d, 0.16, 0.30, 0.86, 0.46, 0.05), slash(d, 0.14, 0.52, 0.84, 0.70, 0.05)])
    K.glow(c, sl, (180, 230, 255, 255), 12, 1.4)
    K.fill(c, soften(sl), (255, 255, 255, 255))
    sword(c, 0.48, 0.50, 0.95, 50, (170, 220, 255), keyline=True, blade_w=0.12, guard_w=0.36)
    return K.finish(c)


def burning_blade():
    """Fire: a sword wreathed in flame."""
    c = bg((150, 46, 18), (24, 4, 6), 0.5, 0.6, 0.66)
    fire_aura(c, [(0.5, 0.86, 0.22, 0.84, 0.03), (0.36, 0.80, 0.10, 0.46, -0.05), (0.64, 0.80, 0.10, 0.50, 0.06)],
              core=[(0.5, 0.80, 0.11, 0.56, 0.02)])
    sword(c, 0.5, 0.50, 0.95, 0, (255, 150, 60), blade=((255, 240, 200), (240, 120, 50)), fuller=(200, 70, 20))
    motes(c, 7, 14, (0.2, 0.06, 0.8, 0.4), (0.006, 0.014), (255, 230, 160), (255, 160, 60))
    return K.finish(c)


def red_lotus_blade():
    """Fire: a sword rising from a blooming lotus of flame."""
    c = bg((170, 20, 70), (24, 2, 14), 0.5, 0.62)
    fire_aura(c, [(0.5, 0.70, 0.16, 0.66, 0.0)], ((255, 220, 120), (240, 60, 30)), (255, 90, 40))
    sword(c, 0.5, 0.40, 0.80, 0, (255, 200, 120), blade=((255, 250, 235), (250, 170, 100)), fuller=(220, 80, 40),
          sh=False)
    back = [(-160, 0.30, 0.085), (-20, 0.30, 0.085), (-128, 0.34, 0.095), (-52, 0.34, 0.095)]
    front = [(-108, 0.30, 0.09), (-72, 0.30, 0.09), (-90, 0.24, 0.08)]
    for layer, cols in ((back, ((250, 120, 90), (150, 10, 40))), (front, ((255, 236, 170), (240, 70, 50)))):
        for a, L, w in layer:
            pm = shape(lambda dd, a=a, L=L, w=w: GA.leaf(dd, 0.5, 0.80, math.radians(a), L, w))
            K.glow(c, pm, (255, 90, 40, 255), 8, 1.0)
            K.shadow(c, pm, 3, 5, 5, 120)
            K.fill(c, soften(pm), K.linear(rgba(cols[0]), rgba(cols[1]), 270))
            vein = shape(lambda dd, a=a, L=L, w=w: GA.leaf(dd, 0.5, 0.80, math.radians(a), L * 0.85, w * 0.22))
            tfill(c, scale(soften(vein, 2), 0.55), (255, 255, 220, 255))
    motes(c, 17, 12, (0.15, 0.1, 0.85, 0.5), (0.006, 0.012), (255, 230, 180), (255, 120, 60))
    return K.finish(c)


def flat_blade():
    """A sword swung flat-side on, the foe seeing stars (stun)."""
    c = bg((170, 170, 50), (26, 26, 4), 0.5, 0.55)
    imp = shape(lambda d: burst(d, 0.5, 0.62, 0.28, 0.12, 10, -90))
    lit(c, imp, K.radial((255, 255, 230, 255), (240, 210, 80, 255), 0.5, 0.62, 0.28), (255, 240, 140), 14, 1.2)
    sword(c, 0.5, 0.62, 0.95, 90, (255, 250, 190), blade_w=0.16, guard_w=0.30)
    stun_stars(c, 0.5, 0.27, 0.22, 0.08, 3, (255, 240, 100), 0.6)
    return K.finish(c)


def shining_blade():
    """Light: a sword blazing with radiance."""
    c = bg((230, 180, 60), (50, 30, 6), 0.5, 0.42)
    rays(c, 0.5, 0.40, 18, 0.75, (255, 255, 230), 130, 0.05, 6)
    core = shape(lambda d: d.ellipse(pts([(0.30, 0.20), (0.70, 0.60)]), fill=255))
    K.glow(c, core, (255, 255, 230, 255), 30, 1.3)
    sword(c, 0.5, 0.50, 0.95, 0, (255, 255, 220), blade=((255, 255, 255), (255, 236, 180)), fuller=(230, 190, 90),
          gr=20, gs=1.6, sh=False)
    sparkles(c, [(0.50, 0.12, 0.14), (0.24, 0.40, 0.07), (0.76, 0.36, 0.07)], (255, 240, 170))
    return K.finish(c)


def seraph_blade():
    """Light: a sword borne on seraph's wings beneath a halo."""
    c = bg((120, 170, 230), (10, 20, 50), 0.5, 0.45)
    rays(c, 0.5, 0.46, 12, 0.7, (255, 255, 255), 70, 0.06, 7)

    def wing(d, side):
        for i in range(6):
            t = i / 5
            ang = math.radians(-10 - 50 * t) if side > 0 else math.radians(190 + 50 * t)
            L = 0.36 - 0.06 * t
            bx, by = 0.5 + side * 0.04, 0.58
            ex, ey = bx + math.cos(ang) * L, by + math.sin(ang) * L
            nx, ny = -math.sin(ang) * 0.045, math.cos(ang) * 0.045
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    wings = shape(lambda d: [wing(d, 1), wing(d, -1)])
    K.glow(c, wings, (255, 255, 255, 255), 14, 1.2)
    K.fill(c, soften(wings), K.linear((255, 255, 255, 255), (200, 220, 245, 255), 90))
    sword(c, 0.5, 0.54, 0.86, 0, (255, 255, 230), blade=((255, 255, 255), (220, 230, 250)), fuller=(170, 190, 230),
          gem=(120, 200, 255))
    halo = shape(lambda d: d.ellipse(pts([(0.38, 0.04), (0.62, 0.13)]), outline=255, width=int(0.024 * W)))
    lit(c, halo, (255, 240, 170), (255, 236, 150), 10, 1.3)
    return K.finish(c)


def circle_blade():
    """Area: a sword sweeping a full circle around itself."""
    c = bg((40, 150, 160), (2, 22, 26))
    ring = shape(lambda d: [swoosh(d, 0.5, 0.5, 0.35, a, a + 170, 0.09, 'end') for a in (0, 180)])
    K.glow(c, ring, (160, 255, 255, 255), 14, 1.4)
    K.fill(c, soften(ring), (235, 255, 255, 255))
    sword(c, 0.5, 0.50, 0.90, 45, (180, 255, 250), keyline=True, blade_w=0.12, guard_w=0.36)
    return K.finish(c)


def spirits_within():
    """A sword with the wielder's own spirits, pale wisps, coiling up around it."""
    c = bg((40, 60, 150), (4, 6, 26), 0.5, 0.5)
    sword(c, 0.5, 0.52, 0.92, 0, (140, 190, 255), blade=((240, 248, 255), (140, 170, 230)), gr=20, gs=1.5)
    for k, (a0, cx) in enumerate(((0.0, 0.5), (2.1, 0.5), (4.2, 0.5))):
        path = []
        for i in range(40):
            t = i / 39
            a = a0 + t * 4.0
            path.append((cx + math.cos(a) * 0.24 * (1 - 0.4 * t), 0.82 - t * 0.66 + math.sin(a) * 0.05))
        tail = shape(lambda d, path=path: stroke(d, path, 0.004, 0.035))
        K.glow(c, tail, (120, 190, 255, 255), 8, 1.3)
        tfill(c, scale(soften(tail, 2), 0.8), (210, 235, 255, 255))
        hx, hy = path[-1]
        head = shape(lambda d, hx=hx, hy=hy: d.ellipse(pts([(hx - 0.04, hy - 0.04), (hx + 0.04, hy + 0.04)]),
                                                       fill=255))
        K.glow(c, head, (160, 220, 255, 255), 12, 1.6)
        K.fill(c, soften(head, 2), (245, 250, 255, 255))
    return K.finish(c)


def vorpal_blade():
    """A sword and four criss-crossed cuts (critical hits)."""
    c = bg((130, 60, 190), (16, 4, 34))
    sl = shape(lambda d: [slash(d, 0.14, 0.24, 0.62, 0.62, 0.05), slash(d, 0.40, 0.14, 0.86, 0.50, 0.05),
                          slash(d, 0.86, 0.26, 0.40, 0.70, 0.05), slash(d, 0.60, 0.18, 0.14, 0.62, 0.05)])
    K.glow(c, sl, (220, 170, 255, 255), 12, 1.4)
    K.fill(c, soften(sl), (255, 250, 255, 255))
    sword(c, 0.5, 0.56, 0.86, -40, (210, 170, 255), gem=(200, 90, 255))
    sparkles(c, [(0.80, 0.80, 0.08)], (230, 190, 255))
    return K.finish(c)


def swift_blade():
    """Three swift strokes, the sword already past them."""
    c = bg((60, 160, 80), (4, 26, 8), 0.55, 0.45)
    sl = shape(lambda d: [slash(d, 0.10, 0.30 + i * 0.16, 0.66, 0.16 + i * 0.16, 0.05) for i in range(3)])
    K.glow(c, sl, (190, 255, 190, 255), 10, 1.3)
    K.fill(c, soften(sl), (245, 255, 245, 255))
    for ang, a in ((40, 0.22), (55, 0.4)):
        full, _, _, _ = sword_masks(0.56, 0.54, 0.92, ang)
        tfill(c, scale(soften(full, 3), a), (230, 255, 230, 255))
    sword(c, 0.56, 0.54, 0.92, 70, (180, 255, 180))
    return K.finish(c)


def savage_blade():
    """A broad sword brought down in a huge overhead arc, slamming into ground that cracks and erupts."""
    c = bg((180, 70, 20), (26, 6, 2), 0.5, 0.42)
    arc = shape(lambda d: swoosh(d, 0.5, 0.62, 0.40, 190, 300, 0.20, 'end'))
    K.glow(c, arc, (255, 140, 40, 255), 20, 1.5)
    K.fill(c, soften(arc), K.linear((255, 140, 50, 255), (255, 250, 210, 255), 0))
    imp = shape(lambda d: burst(d, 0.56, 0.84, 0.30, 0.10, 9, -90))
    lit(c, imp, K.radial((255, 255, 220, 255), (255, 140, 40, 255), 0.56, 0.84, 0.25), (255, 170, 60), 14, 1.4)
    crack = shape(lambda d: [d.line(pts(bolt_path(0.56, 0.86, x, y, s, 4, 0.03)), fill=255, width=int(0.018 * W))
                             for x, y, s in ((0.16, 0.86, 1), (0.94, 0.80, 2), (0.36, 1.0, 3), (0.80, 1.0, 4))])
    K.fill(c, soften(crack), (60, 14, 4, 255))
    rocks = shape(lambda d: [d.polygon(pts([(x - r, y), (x, y - r), (x + r * 0.8, y - r * 0.2), (x + r * 0.4, y + r)]),
                                       fill=255) for x, y, r in ((0.30, 0.66, 0.035), (0.80, 0.62, 0.03),
                                                                 (0.86, 0.48, 0.022))])
    lit(c, rocks, ((150, 90, 60), (60, 30, 20)), (255, 150, 60), 5)
    sword(c, 0.56, 0.42, 0.98, 168, (255, 180, 90), blade=((255, 252, 245), (170, 160, 175)), blade_w=0.14,
          guard_w=0.40, hilt=((210, 60, 40), (90, 20, 14)), gem=(255, 200, 60))
    return K.finish(c)


def knights_of_round():
    """Relic (Excalibur): a golden sword raised in the round of its twelve knights' blades."""
    c = bg((40, 70, 170), (4, 8, 30), 0.5, 0.5)
    rays(c, 0.5, 0.5, 24, 0.7, (255, 240, 190), 90, 0.04, 5)
    ring = shape(lambda d: d.ellipse(pts([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=int(0.02 * W)))
    K.glow(c, ring, (255, 220, 130, 255), 10, 1.3)
    K.fill(c, soften(ring), (255, 236, 170, 255))
    small = mask()
    sd = ImageDraw.Draw(small)
    for i in range(12):
        a = 360 * i / 12
        ar = math.radians(a - 90)
        x, y = 0.5 + math.cos(ar) * 0.33, 0.5 + math.sin(ar) * 0.33
        for q in GB.sword_parts(1.0, 0.10, 0.36):
            sd.polygon(xf(q, x, y, 0.21, a + 180), fill=255)
    K.glow(c, small, (180, 210, 255, 255), 8, 1.5)
    K.shadow(c, small, 3, 5, 5, 140)
    K.fill(c, soften(small), K.radial((255, 255, 255, 255), (200, 210, 240, 255), 0.5, 0.5, 0.42))
    core = shape(lambda d: d.ellipse(pts([(0.32, 0.26), (0.68, 0.62)]), fill=255))
    K.glow(c, core, (255, 240, 180, 255), 26, 1.2)
    sword(c, 0.5, 0.52, 0.76, 0, (255, 220, 120), blade=((255, 255, 245), (230, 210, 150)), hilt=GOLD,
          fuller=(200, 160, 70), gem=(70, 120, 255), gr=18, gs=1.5)
    return K.finish(c)


def death_blossom():
    """Mythic (Murgleis): a slender blade through a dark bloom, petals scattering."""
    c = bg((110, 30, 120), (14, 2, 18), 0.5, 0.5)
    for i in range(5):
        a = 2 * math.pi * i / 5 - math.pi / 2
        pm = shape(lambda dd, a=a: GA.leaf(dd, 0.5 + math.cos(a) * 0.03, 0.5 + math.sin(a) * 0.03, a, 0.34, 0.085))
        K.glow(c, pm, (230, 80, 200, 255), 10, 1.0)
        K.shadow(c, pm, 3, 5, 5, 140)
        K.fill(c, soften(pm), K.radial((50, 0, 40, 255), (240, 110, 200, 255), 0.5, 0.5, 0.36))
    core = shape(lambda dd: dd.polygon(pts(GA.star_pts(0.5, 0.5, 5, 0.09, 0.04, math.pi / 2)), fill=255))
    lit(c, core, (255, 220, 120), (255, 200, 120), 8, 1.3)
    sword(c, 0.5, 0.50, 0.92, 35, (255, 160, 230), blade=((255, 250, 255), (190, 170, 210)), blade_w=0.06,
          hilt=((255, 220, 140), (180, 110, 40)), gem=(220, 40, 120))
    petals = shape(lambda dd: [GA.leaf(dd, x, y, a, 0.07, 0.03) for x, y, a in
                               ((0.20, 0.76, 0.4), (0.30, 0.86, 2.0), (0.82, 0.22, 1.2), (0.16, 0.30, 2.8))])
    lit(c, petals, ((255, 170, 230), (200, 40, 150)), (255, 120, 210), 6)
    return K.finish(c)


def atonement():
    """A paladin's sword planted point-down before a cross of atoning light."""
    c = bg((60, 110, 150), (4, 14, 26), 0.5, 0.42)
    cross = shape(lambda d: [d.rectangle(pts([(0.44, 0.06), (0.56, 0.94)]), fill=255),
                             d.rectangle(pts([(0.14, 0.26), (0.86, 0.38)]), fill=255)])
    K.glow(c, cross, (255, 220, 140, 255), 30, 1.3)
    K.fill(c, soften(cross, 6), K.radial((255, 255, 240, 230), (255, 210, 120, 200), 0.5, 0.32, 0.45))
    ground = shape(lambda d: d.ellipse(pts([(0.24, 0.80), (0.76, 0.92)]), fill=255))
    K.fill(c, soften(ground, 8), (255, 230, 170, 200))
    sword(c, 0.5, 0.46, 0.92, 180, (255, 230, 160), blade=((250, 250, 255), (160, 170, 200)), blade_w=0.10,
          guard_w=0.40, gem=(60, 120, 255))
    motes(c, 23, 10, (0.15, 0.1, 0.85, 0.8), (0.006, 0.012), (255, 250, 220), (255, 220, 140))
    return K.finish(c)


def expiacion():
    """Mythic (Tizona): a blue mage's sword and a burning azure cross cut."""
    c = bg((30, 120, 180), (2, 14, 30), 0.5, 0.5)
    rays(c, 0.5, 0.5, 16, 0.7, (150, 230, 255), 70, 0.05, 6)
    x = shape(lambda d: [slash(d, 0.14, 0.14, 0.86, 0.86, 0.10), slash(d, 0.86, 0.14, 0.14, 0.86, 0.10)])
    K.glow(c, x, (80, 200, 255, 255), 18, 1.6)
    K.fill(c, soften(x), K.radial((255, 255, 255, 255), (120, 220, 255, 255), 0.5, 0.5, 0.4))
    sword(c, 0.5, 0.52, 0.90, 0, (120, 220, 255), blade=((240, 252, 255), (120, 170, 210)),
          hilt=((255, 220, 120), (170, 100, 30)), guard_w=0.38, gem=(30, 210, 255), fuller=(60, 130, 190))
    runes = shape(lambda d: [d.polygon(pts(GA.star_pts(x0, y0, 4, 0.05, 0.015)), fill=255)
                             for x0, y0 in ((0.18, 0.5), (0.82, 0.5))])
    lit(c, runes, (230, 250, 255), (100, 210, 255), 8, 1.4)
    return K.finish(c)


def sanguine_blade():
    """Dark, drains HP: crimson life spiralling into a black sword."""
    c = bg((90, 10, 50), (10, 0, 8), 0.5, 0.5)
    sp = mask()
    sd = ImageDraw.Draw(sp)
    for k in range(3):
        spiral(sd, 0.5, 0.46, 0.44, 0.06, 0.8, 0.07, 0.01, k * 2 * math.pi / 3)
    K.glow(c, sp, (255, 40, 70, 255), 16, 1.3)
    K.fill(c, soften(sp), K.radial((140, 0, 20, 255), (255, 110, 120, 255), 0.5, 0.46, 0.44))
    sword(c, 0.5, 0.50, 0.95, 0, (255, 60, 90), blade=((240, 220, 228), (150, 70, 90)), fuller=(200, 20, 50),
          hilt=((160, 30, 50), (60, 6, 16)), gem=(255, 40, 60), gr=12, gs=1.5)
    motes(c, 4, 10, (0.12, 0.12, 0.88, 0.88), (0.008, 0.016), (255, 200, 200), (255, 50, 70))
    return K.finish(c)


ICONS = {
    ('ja', 'Combo'): combo,
    ('ja', 'Shoulder Tackle'): shoulder_tackle,
    ('ja', 'One Inch Punch'): one_inch_punch,
    ('ja', 'Backhand Blow'): backhand_blow,
    ('ja', 'Raging Fists'): raging_fists,
    ('ja', 'Spinning Attack'): spinning_attack,
    ('ja', 'Howling Fist'): howling_fist,
    ('ja', 'Dragon Kick'): dragon_kick,
    ('ja', 'Asuran Fists'): asuran_fists,
    ('ja', 'Final Heaven'): final_heaven,
    ('ja', "Ascetic's Fury"): ascetics_fury,
    ('ja', 'Stringing Pummel'): stringing_pummel,
    ('ja', 'Tornado Kick'): tornado_kick,
    ('ja', 'Victory Smite'): victory_smite,
    ('ja', 'Shijin Spiral'): shijin_spiral,
    ('ja', 'Wasp Sting'): wasp_sting,
    ('ja', 'Viper Bite'): viper_bite,
    ('ja', 'Shadowstitch'): shadowstitch,
    ('ja', 'Gust Slash'): gust_slash,
    ('ja', 'Cyclone'): cyclone,
    ('ja', 'Energy Steal'): energy_steal,
    ('ja', 'Dancing Edge'): dancing_edge,
    ('ja', 'Shark Bite'): shark_bite,
    ('ja', 'Evisceration'): evisceration,
    ('ja', 'Mercy Stroke'): mercy_stroke,
    ('ja', 'Mandalic Stab'): mandalic_stab,
    ('ja', 'Mordant Rime'): mordant_rime,
    ('ja', 'Pyrrhic Kleos'): pyrrhic_kleos,
    ('ja', 'Aeolian Edge'): aeolian_edge,
    ('ja', "Rudra's Storm"): rudras_storm,
    ('ja', 'Fast Blade'): fast_blade,
    ('ja', 'Burning Blade'): burning_blade,
    ('ja', 'Red Lotus Blade'): red_lotus_blade,
    ('ja', 'Flat Blade'): flat_blade,
    ('ja', 'Shining Blade'): shining_blade,
    ('ja', 'Seraph Blade'): seraph_blade,
    ('ja', 'Circle Blade'): circle_blade,
    ('ja', 'Spirits Within'): spirits_within,
    ('ja', 'Vorpal Blade'): vorpal_blade,
    ('ja', 'Swift Blade'): swift_blade,
    ('ja', 'Savage Blade'): savage_blade,
    ('ja', 'Knights of Round'): knights_of_round,
    ('ja', 'Death Blossom'): death_blossom,
    ('ja', 'Atonement'): atonement,
    ('ja', 'Expiacion'): expiacion,
    ('ja', 'Sanguine Blade'): sanguine_blade,
}
COVERS = {}
# Energy Drain is Energy Steal's darker twin: the same painting turned from mana-blue to dark purple.
VARIANTS = {'Energy Steal': {'Energy Steal': None, 'Energy Drain': 80}}
NAMES = [n for _, n in ICONS]
