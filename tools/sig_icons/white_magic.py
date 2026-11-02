"""Signature icons, round 2: white magic and its relatives (status removal, bar-spells, en-spells, storms, Boost-/Gain-,
warps, enhancing and enfeebling white spells). See tools/make_signature_icons.py for the kit."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_b as GB

W = K.W
p, pts, mask, shape, soften = K.p, K.pts, K.mask, K.shape, K.soften
star_pts, leaf, bezier, heater, flame, rotated = GA.star_pts, GA.leaf, GA.bezier, GA.heater, GA.flame, GA.rotated
arc_arrow, cross = GA.arc_arrow, GA.cross


# ---- helpers --------------------------------------------------------------------------------------------------------
def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(c0 + (255,), c1 + (255,), cx, cy, r)


def solid(c, m, top, bot, glow_col=None, gr=16, gs=1.3, sh=True, ang=90):
    """The usual treatment of a motif: drop shadow, glow, gradient fill."""
    if sh:
        K.shadow(c, m, 5, 8, 8, 160)
    if glow_col:
        K.glow(c, m, glow_col + (255,), gr, gs)
    K.fill(c, soften(m), K.linear(top + (255,), bot + (255,), ang))


def faint(m, k):
    return m.point(lambda v: int(v * k))


def motes(c, seed, n, box, rr, glow_col, col=(255, 255, 255)):
    GA.motes(c, seed, n, box, rr, glow_col + (255,), col + (230,))


def sparkles(c, spots, glow_col=(255, 255, 255)):
    GA.sparkles(c, spots, glow_col + (255,))


def ell_m(x0, y0, x1, y1):
    return shape(lambda d: d.ellipse(pts([(x0, y0), (x1, y1)]), fill=255))


def ring_m(x0, y0, x1, y1, w):
    return shape(lambda d: d.ellipse(pts([(x0, y0), (x1, y1)]), outline=255, width=int(w * W)))


def party_ring(c, col, glow_col, y=0.76, rx=0.36, ry=0.09, pips=True):
    """The area mark used by -ga / -ra / Boost-: a glowing ellipse on the ground with three party pips."""
    r = ring_m(0.5 - rx, y - ry, 0.5 + rx, y + ry, 0.024)
    K.glow(c, r, glow_col + (255,), 12, 1.4)
    K.fill(c, soften(r, 2), col + (255,))
    if pips:
        pm = shape(lambda d: [d.ellipse(pts([(x - 0.05, yy - 0.05), (x + 0.05, yy + 0.05)]), fill=255)
                              for x, yy in ((0.5 - rx * 0.72, y + ry * 0.62), (0.5, y + ry * 0.9),
                                            (0.5 + rx * 0.72, y + ry * 0.62))])
        K.glow(c, pm, glow_col + (255,), 8, 1.6)
        K.fill(c, soften(pm), (255, 255, 255, 255))


def hues(base, table):
    """VARIANTS entry: members painted at hue `base` turned to their own target hue."""
    out = {}
    for name, h in table.items():
        if isinstance(h, tuple):        # K.LIGHT / K.DARK: (turn from a fire-hued base, saturation, brightness)
            out[name] = ((h[0] + 8 - base) % 360,) + tuple(h[1:])
        else:
            out[name] = None if (h - base) % 360 == 0 else (h - base) % 360
    return out


def robed(d, cx, cy, s, fill=255):
    """A hooded, robed mage seen from the front (local height ~0.8 s)."""
    d.polygon(pts([(cx, cy - 0.44 * s), (cx + 0.13 * s, cy - 0.20 * s), (cx - 0.13 * s, cy - 0.20 * s)]), fill=fill)
    d.ellipse(pts([(cx - 0.12 * s, cy - 0.34 * s), (cx + 0.12 * s, cy - 0.12 * s)]), fill=fill)
    d.polygon(pts([(cx - 0.12 * s, cy - 0.18 * s), (cx + 0.12 * s, cy - 0.18 * s), (cx + 0.26 * s, cy + 0.38 * s),
                   (cx - 0.26 * s, cy + 0.38 * s)]), fill=fill)


def person(d, cx, cy, s, fill=255):
    """A stiff standing figure, arms out (paralysed)."""
    lw = int(0.075 * s * W)
    d.ellipse(pts([(cx - 0.09 * s, cy - 0.44 * s), (cx + 0.09 * s, cy - 0.26 * s)]), fill=fill)
    d.rounded_rectangle(pts([(cx - 0.11 * s, cy - 0.24 * s), (cx + 0.11 * s, cy + 0.08 * s)]), radius=0.04 * s * W,
                        fill=fill)
    d.line(pts([(cx - 0.09 * s, cy - 0.20 * s), (cx - 0.32 * s, cy - 0.02 * s)]), fill=fill, width=lw)
    d.line(pts([(cx + 0.09 * s, cy - 0.20 * s), (cx + 0.32 * s, cy - 0.30 * s)]), fill=fill, width=lw)
    d.line(pts([(cx - 0.06 * s, cy + 0.04 * s), (cx - 0.16 * s, cy + 0.40 * s)]), fill=fill, width=lw)
    d.line(pts([(cx + 0.06 * s, cy + 0.04 * s), (cx + 0.14 * s, cy + 0.40 * s)]), fill=fill, width=lw)


def zigzag(d, x0, y0, x1, y1, n, amp, width, seed):
    rnd = random.Random(seed)
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    seq = []
    for i in range(n + 1):
        t = i / n
        a = 0 if i in (0, n) else amp * (1 if i % 2 else -1) * rnd.uniform(0.6, 1.0)
        seq.append((x0 + (x1 - x0) * t + nx * a, y0 + (y1 - y0) * t + ny * a))
    d.line(pts(seq), fill=255, width=int(width * W), joint='curve')


def ankh(d, cx, top, s):
    d.ellipse(pts([(cx - 0.13 * s, top), (cx + 0.13 * s, top + 0.34 * s)]), outline=255, width=int(0.065 * s * W))
    d.rounded_rectangle(pts([(cx - 0.26 * s, top + 0.31 * s), (cx + 0.26 * s, top + 0.40 * s)]), radius=0.03 * s * W,
                        fill=255)
    d.polygon(pts([(cx - 0.04 * s, top + 0.34 * s), (cx + 0.04 * s, top + 0.34 * s), (cx + 0.08 * s, top + 0.76 * s),
                   (cx - 0.08 * s, top + 0.76 * s)]), fill=255)


def wing(d, side, bx, by, s=1.0, n=5, spread=55, base=-12):
    """Feathered wing from (bx, by); side=1 right, -1 left."""
    for i in range(n):
        t = i / (n - 1)
        ang = math.radians(base - spread * t)
        if side < 0:
            ang = math.pi - ang
        length = (0.34 - 0.07 * t) * s
        ex, ey = bx + math.cos(ang) * length, by + math.sin(ang) * length
        nx, ny = -math.sin(ang) * 0.042 * s, math.cos(ang) * 0.042 * s
        d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)


def gem_parts(cx, cy, s):
    """A brilliant-cut gem: outline and the facet lines."""
    out = [(cx - 0.24 * s, cy - 0.10 * s), (cx - 0.13 * s, cy - 0.24 * s), (cx + 0.13 * s, cy - 0.24 * s),
           (cx + 0.24 * s, cy - 0.10 * s), (cx, cy + 0.30 * s)]
    table = [(cx - 0.11 * s, cy - 0.10 * s), (cx - 0.06 * s, cy - 0.24 * s), (cx + 0.06 * s, cy - 0.24 * s),
             (cx + 0.11 * s, cy - 0.10 * s)]
    return out, table


def gem(c, cx, cy, s, light, dark, glow_col, sh=True):
    out, table = gem_parts(cx, cy, s)
    m = shape(lambda d: d.polygon(pts(out), fill=255))
    solid(c, m, light, dark, glow_col, 18 * s, 1.3, sh)
    crown = shape(lambda d: d.polygon(pts(out[:4] + [(cx + 0.24 * s, cy - 0.10 * s)]), fill=255))
    K.fill(c, soften(faint(crown, 0.45)), (255, 255, 255, 255))
    tab = shape(lambda d: d.polygon(pts([table[0], table[1], table[2], table[3]]), fill=255))
    K.fill(c, soften(faint(tab, 0.5)), (255, 255, 255, 255))
    lines = shape(lambda d: [d.line(pts([table[0], (cx, cy + 0.30 * s)]), fill=255, width=int(0.012 * W * s)),
                             d.line(pts([table[3], (cx, cy + 0.30 * s)]), fill=255, width=int(0.012 * W * s)),
                             d.line(pts([(cx - 0.24 * s, cy - 0.10 * s), (cx + 0.24 * s, cy - 0.10 * s)]), fill=255,
                                    width=int(0.012 * W * s))])
    K.fill(c, soften(faint(lines, 0.55)), dark + (255,))
    sparkles(c, [(cx - 0.10 * s, cy - 0.16 * s, 0.07 * s)])


def up_arrow(d, cx, top, w, h):
    d.polygon(pts([(cx, top), (cx + w, top + w * 1.05), (cx + w * 0.42, top + w * 1.05), (cx + w * 0.42, top + h),
                   (cx - w * 0.42, top + h), (cx - w * 0.42, top + w * 1.05), (cx - w, top + w * 1.05)]), fill=255)


# ---- status removal ----------------------------------------------------------------------------------------------
AILMENT = {'Poisona': 290, 'Paralyna': 52, 'Blindna': 228, 'Silena': 185, 'Stona': 28, 'Viruna': 110, 'Cursna': 335}


def cleanse():
    """An ailment orb (its colour names the ailment) cracking open as cleansing light pours out of it."""
    c = bg((120, 50, 150), (16, 4, 24), 0.5, 0.55, 0.74)
    frags = [(-2.5, 0.33, 0.05), (-0.7, 0.34, 0.06), (0.5, 0.33, 0.045), (2.4, 0.32, 0.04)]
    sh = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a + k) * (r + s * f), 0.54 + math.sin(a + k) * (r + s * f))
                                         for k, f in ((0, 0), (0.22, 0.6), (0.05, 1.6), (-0.16, 0.9))]), fill=255)
                          for a, r, s in frags])
    K.glow(c, sh, (220, 120, 255, 255), 8, 1.2)
    K.fill(c, soften(sh), K.linear((250, 210, 255, 255), (170, 70, 220, 255), 90))
    orb = ell_m(0.24, 0.28, 0.76, 0.80)
    K.shadow(c, orb, 5, 8, 8, 170)
    K.glow(c, orb, (190, 80, 255, 255), 22, 1.2)
    K.fill(c, soften(orb), K.radial((236, 160, 255, 255), (96, 16, 140, 255), 0.42, 0.42, 0.36))

    def cracks(d):
        for (x1, y1), sd in (((0.30, 0.34), 1), ((0.74, 0.36), 2), ((0.58, 0.80), 3), ((0.24, 0.62), 4)):
            zigzag(d, 0.5, 0.54, x1, y1, 3, 0.025, 0.026, sd)
    cr = ImageChops.multiply(shape(cracks), ell_m(0.23, 0.27, 0.77, 0.81))
    K.glow(c, cr, (255, 255, 255, 255), 12, 1.7)
    K.fill(c, soften(cr), (255, 255, 255, 255))
    core = ell_m(0.42, 0.46, 0.58, 0.62)
    K.glow(c, core, (255, 255, 255, 255), 20, 1.8)
    K.fill(c, soften(core), (255, 255, 255, 255))
    sparkles(c, [(0.78, 0.20, 0.10)])
    return K.finish(c)


def erase():
    """A broad stroke of white light wiping dark ailment blots off the page, sparkles where it has passed."""
    c = bg((50, 130, 170), (6, 16, 30), 0.55, 0.45, 0.74)
    blots = mask()
    bd = ImageDraw.Draw(blots)
    for x, y, r in ((0.24, 0.36, 0.09), (0.36, 0.26, 0.06), (0.20, 0.56, 0.07), (0.34, 0.46, 0.05)):
        bd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    K.shadow(c, blots, 3, 5, 5, 120)
    K.glow(c, blots, (190, 80, 230, 255), 10)
    K.fill(c, soften(blots), K.radial((170, 80, 200, 255), (60, 10, 80, 255), 0.26, 0.38, 0.22))

    def stroke(d):
        seq = bezier((0.30, 0.86), (0.48, 0.44), (0.86, 0.30), 30)
        for i in range(len(seq) - 1):
            t = i / (len(seq) - 1)
            w = 0.05 + 0.10 * math.sin(math.pi * min(1, t * 1.1)) ** 0.7
            d.line(pts([seq[i], seq[i + 1]]), fill=255, width=int(w * W))
            r = w / 2
            d.ellipse(pts([(seq[i][0] - r, seq[i][1] - r), (seq[i][0] + r, seq[i][1] + r)]), fill=255)
    m = shape(stroke)
    K.shadow(c, m, 5, 8, 8, 150)
    K.glow(c, m, (180, 255, 255, 255), 18, 1.4)
    K.fill(c, soften(m), K.linear((255, 255, 255, 255), (150, 230, 250, 255), 45))
    dust = dots(12, 12, 0.56, 0.90, 0.44, 0.84, 0.008, 0.016)
    K.glow(c, dust, (180, 120, 230, 255), 5)
    K.fill(c, dust, (220, 190, 255, 255))
    sparkles(c, [(0.72, 0.62, 0.08), (0.58, 0.80, 0.05)], (200, 255, 255))
    return K.finish(c)


def esuna():
    """A drop of holy water in a halo, the party's ailments (coloured orbs) dissolving around it."""
    c = bg((70, 80, 170), (8, 8, 30), 0.5, 0.48, 0.72)
    halo = ring_m(0.20, 0.20, 0.80, 0.80, 0.02)
    K.glow(c, halo, (200, 220, 255, 255), 10, 1.0)
    K.fill(c, soften(faint(halo, 0.7)), (230, 240, 255, 255))
    cols = [(180, 80, 230), (240, 220, 60), (60, 200, 230), (120, 210, 70), (230, 110, 60), (230, 70, 130)]
    for i, col in enumerate(cols):
        a = math.pi * 2 * i / 6 - math.pi / 2 + 0.5
        x, y = 0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30
        o = ell_m(x - 0.05, y - 0.05, x + 0.05, y + 0.05)
        K.glow(c, o, col + (255,), 8, 1.3)
        K.fill(c, soften(o), K.radial((255, 255, 255, 255), col + (255,), x - 0.015, y - 0.015, 0.06))

    def drop(d):
        d.ellipse(pts([(0.37, 0.44), (0.63, 0.70)]), fill=255)
        d.polygon(pts([(0.5, 0.20), (0.625, 0.53), (0.375, 0.53)]), fill=255)
    m = shape(drop)
    solid(c, m, (255, 255, 255), (170, 200, 255), (200, 220, 255), 22, 1.5)
    hl = ell_m(0.42, 0.50, 0.47, 0.62)
    K.fill(c, soften(hl, 4), (255, 255, 255, 255))
    crs = shape(lambda d: cross(d, 0.5, 0.58, 0.22))
    K.fill(c, soften(crs), (120, 160, 240, 255))
    return K.finish(c)


# ---- divine -------------------------------------------------------------------------------------------------------
def holy_cross(d, cx, top, s):
    """A cruciform lance of light pointing down."""
    d.polygon(pts([(cx - 0.05 * s, top), (cx + 0.05 * s, top), (cx + 0.05 * s, top + 0.56 * s), (cx, top + 0.70 * s),
                   (cx - 0.05 * s, top + 0.56 * s)]), fill=255)
    d.polygon(pts([(cx - 0.20 * s, top + 0.13 * s), (cx + 0.20 * s, top + 0.13 * s), (cx + 0.17 * s, top + 0.22 * s),
                   (cx - 0.17 * s, top + 0.22 * s)]), fill=255)


def impact(c, cx, cy, s, col=(255, 230, 140)):
    b = shape(lambda d: d.polygon(pts([(cx + (x - cx), cy + (y - cy) * 0.5) for x, y in
                                       star_pts(cx, cy, 8, 0.22 * s, 0.08 * s, 0)]), fill=255))
    K.glow(c, b, col + (255,), 18, 1.5)
    K.fill(c, soften(b), (255, 252, 230, 255))


def banish():
    """A cruciform lance of holy light driving down into a burst."""
    c = bg((170, 130, 50), (20, 12, 30), 0.5, 0.3, 0.74)
    beam = shape(lambda d: d.rectangle(pts([(0.40, 0.0), (0.60, 0.8)]), fill=255))
    K.fill(c, faint(beam.filter(ImageFilter.GaussianBlur(20)), 0.5), (255, 240, 190, 255))
    impact(c, 0.5, 0.80, 1.3)
    m = shape(lambda d: holy_cross(d, 0.5, 0.10, 1.0))
    solid(c, m, (255, 255, 240), (240, 190, 80), (255, 220, 120), 22, 1.5)
    sparkles(c, [(0.22, 0.30, 0.07), (0.78, 0.44, 0.06)], (255, 230, 160))
    return K.finish(c)


def banishga():
    """Three lances of holy light striking a whole area."""
    c = bg((150, 120, 60), (18, 12, 30), 0.5, 0.3, 0.74)
    party_ring(c, (255, 240, 200), (255, 210, 110), 0.80, 0.38, 0.08, pips=False)
    for cx, top, s in ((0.24, 0.26, 0.66), (0.76, 0.26, 0.66), (0.5, 0.10, 0.92)):
        impact(c, cx, top + 0.70 * s, 0.8 * s)
        m = shape(lambda d, cx=cx, top=top, s=s: holy_cross(d, cx, top, s))
        solid(c, m, (255, 255, 240), (240, 190, 80), (255, 220, 120), 16, 1.4)
    return K.finish(c)


def spiky(c, cx, cy, s):
    spikes = shape(lambda d: d.polygon(pts(star_pts(cx, cy, 12, 0.42 * s, 0.20 * s)), fill=255))
    K.glow(c, spikes, (255, 255, 200, 255), 16 * s, 1.2)
    K.fill(c, soften(spikes), K.radial((255, 255, 230, 255), (230, 220, 140, 255), cx, cy, 0.42 * s))
    orb = ell_m(cx - 0.2 * s, cy - 0.2 * s, cx + 0.2 * s, cy + 0.2 * s)
    K.shadow(c, orb, 3, 5, 6, 100)
    K.glow(c, orb, (255, 255, 255, 255), 12, 1.4)
    K.fill(c, soften(orb), K.radial((255, 255, 255, 255), (250, 240, 170, 255), cx - 0.05 * s, cy - 0.08 * s, 0.22 * s))


def diaga():
    """Dia's stinging orb, three of them over an area."""
    c = bg((30, 100, 160), (4, 12, 30), 0.5, 0.5, 0.74)
    party_ring(c, (220, 255, 250), (140, 255, 230), 0.78, 0.38, 0.09, pips=False)
    spiky(c, 0.27, 0.64, 0.48)
    spiky(c, 0.73, 0.64, 0.48)
    spiky(c, 0.5, 0.40, 0.68)
    return K.finish(c)


# ---- protective barriers ------------------------------------------------------------------------------------------
def bubble(c, x0, y0, x1, y1, col, glow_col):
    b = ell_m(x0, y0, x1, y1)
    K.fill(c, faint(b.filter(ImageFilter.GaussianBlur(10)), 0.28), col + (255,))
    r = ring_m(x0, y0, x1, y1, 0.02)
    K.glow(c, r, glow_col + (255,), 12, 1.3)
    K.fill(c, soften(r, 2), col + (255,))
    hl = shape(lambda d: d.arc(pts([(x0 + 0.04, y0 + 0.04), (x1 - 0.04, y1 - 0.04)]), 200, 250, fill=255,
                               width=int(0.025 * W)))
    K.fill(c, soften(faint(hl, 0.8), 3), (255, 255, 255, 255))


def protect_shield(c, cx, top, w, h):
    m = shape(lambda d: heater(d, cx, top, w, h))
    solid(c, m, (255, 250, 220), (220, 150, 50), (255, 210, 120), 18 * w / 0.19, 1.4)
    inner = shape(lambda d: heater(d, cx, top + h * 0.10, w * 0.72, h * 0.78))
    K.fill(c, soften(inner), K.linear((250, 200, 90, 255), (170, 90, 20, 255), 90))
    st = shape(lambda d: K.sparkle(d, cx, top + h * 0.40, w * 0.62, 0.22))
    K.glow(c, st, (255, 250, 220, 255), 8)
    K.fill(c, soften(st), (255, 255, 245, 255))


def protect_paint(ra):
    """A golden shield of light inside a protective bubble (-ra: three shields, the whole party)."""
    c = bg((180, 116, 40), (30, 14, 4), 0.5, 0.45, 0.72)
    bubble(c, 0.12, 0.14, 0.88, 0.86, (255, 236, 180), (255, 200, 100))
    if ra:
        protect_shield(c, 0.29, 0.40, 0.11, 0.32)
        protect_shield(c, 0.71, 0.40, 0.11, 0.32)
        protect_shield(c, 0.5, 0.22, 0.15, 0.44)
    else:
        protect_shield(c, 0.5, 0.26, 0.19, 0.52)
    return K.finish(c)


def magic_circle(d, cx, cy, r):
    d.ellipse(pts([(cx - r, cy - r), (cx + r, cy + r)]), outline=255, width=int(0.022 * W))
    d.polygon(pts(star_pts(cx, cy, 6, r * 0.92, r * 0.52)), outline=255, width=int(0.018 * W))
    for i in range(6):
        a = math.pi * i / 3
        d.line(pts([(cx + math.cos(a) * r * 0.52, cy + math.sin(a) * r * 0.52),
                    (cx + math.cos(a + math.pi) * r * 0.52, cy + math.sin(a + math.pi) * r * 0.52)]), fill=255,
               width=int(0.010 * W))


def shell_rune(c, cx, cy, r):
    disc = ell_m(cx - r, cy - r, cx + r, cy + r)
    K.fill(c, faint(disc.filter(ImageFilter.GaussianBlur(6)), 0.7), (90, 60, 200, 255))
    m = shape(lambda d: magic_circle(d, cx, cy, r))
    K.glow(c, m, (140, 220, 255, 255), 14 * r / 0.25, 1.5)
    K.fill(c, soften(m), (230, 250, 255, 255))
    core = shape(lambda d: K.sparkle(d, cx, cy, r * 0.42, 0.25))
    K.glow(c, core, (180, 230, 255, 255), 8, 1.4)
    K.fill(c, soften(core), (255, 255, 255, 255))


def shell_paint(ra):
    """A rune circle warding off magic inside a protective bubble (-ra: three runes, the whole party)."""
    c = bg((70, 70, 180), (8, 6, 30), 0.5, 0.45, 0.72)
    bubble(c, 0.12, 0.14, 0.88, 0.86, (200, 230, 255), (120, 170, 255))
    if ra:
        shell_rune(c, 0.30, 0.60, 0.13)
        shell_rune(c, 0.70, 0.60, 0.13)
        shell_rune(c, 0.5, 0.38, 0.17)
    else:
        shell_rune(c, 0.5, 0.5, 0.25)
    return K.finish(c)


def blink():
    """Shadow images: two flickering copies beside the caster take the blows."""
    c = bg((100, 90, 200), (10, 8, 32), 0.5, 0.45, 0.72)
    for dx, a in ((-0.24, 0.45), (0.24, 0.45)):
        g = shape(lambda d, dx=dx: robed(d, 0.5 + dx, 0.57, 0.74))
        K.glow(c, g, (140, 230, 255, 255), 10, 1.0)
        K.fill(c, faint(soften(g, 2), a), (150, 220, 255, 255))
    m = shape(lambda d: robed(d, 0.5, 0.55, 0.88))
    K.shadow(c, m, 5, 8, 8, 160)
    K.glow(c, m, (180, 236, 255, 255), 14, 1.6)
    K.fill(c, soften(m), K.linear((240, 250, 255, 255), (120, 170, 240, 255), 90))
    face = shape(lambda d: d.ellipse(pts([(0.445, 0.27), (0.555, 0.40)]), fill=255))
    K.fill(c, soften(face), (30, 30, 80, 255))
    eyes = shape(lambda d: [d.ellipse(pts([(x - 0.016, 0.322), (x + 0.016, 0.350)]), fill=255) for x in (0.475, 0.525)])
    K.fill(c, soften(eyes), (160, 250, 255, 255))
    sparkles(c, [(0.80, 0.24, 0.07), (0.20, 0.26, 0.05)], (160, 230, 255))
    return K.finish(c)


def stoneskin():
    """A fist turned to stone, plated and cracked, with a golden glint."""
    c = bg((120, 126, 60), (16, 18, 6), 0.5, 0.5, 0.72)
    aura = ell_m(0.18, 0.18, 0.82, 0.82)
    K.fill(c, faint(aura.filter(ImageFilter.GaussianBlur(28)), 0.5), (230, 210, 140, 255))
    m = shape(lambda d: K.fist_front(d, 0.5, 0.54, 1.25))
    solid(c, m, (226, 214, 190), (120, 104, 84), (255, 220, 140), 18, 1.2)
    lines = shape(lambda d: K.fist_lines(d, 0.5, 0.54, 1.25))
    K.fill(c, soften(faint(lines, 0.8), 1.5), (70, 56, 40, 255))

    def cracks(d):
        zigzag(d, 0.30, 0.62, 0.48, 0.70, 3, 0.02, 0.012, 7)
        zigzag(d, 0.58, 0.58, 0.74, 0.74, 3, 0.02, 0.012, 8)
        zigzag(d, 0.40, 0.44, 0.46, 0.56, 2, 0.015, 0.010, 9)
    cr = ImageChops.multiply(shape(cracks), m)
    K.fill(c, soften(faint(cr, 0.8)), (60, 46, 34, 255))
    # a stone-plate sheen
    plates = shape(lambda d: [d.polygon(pts([(0.30, 0.66), (0.40, 0.62), (0.44, 0.74), (0.32, 0.76)]), fill=255),
                              d.polygon(pts([(0.56, 0.66), (0.68, 0.64), (0.70, 0.74), (0.58, 0.76)]), fill=255)])
    K.fill(c, soften(faint(ImageChops.multiply(plates, m), 0.35), 2), (255, 250, 230, 255))
    sparkles(c, [(0.74, 0.30, 0.10)], (255, 220, 130))
    return K.finish(c)


def aquaveil():
    """A veil of flowing water draped around a bright drop."""
    c = bg((30, 130, 180), (4, 16, 32), 0.5, 0.45, 0.72)

    def ribbon(d, x, amp, ph, w):
        left, right = [], []
        for i in range(31):
            t = i / 30
            y = 0.14 + 0.74 * t
            xx = x + amp * math.sin(t * math.pi * 2.2 + ph)
            ww = w * (0.6 + 0.4 * math.sin(math.pi * t))
            left.append((xx - ww, y))
            right.append((xx + ww, y))
        d.polygon(pts(left + right[::-1]), fill=255)
    for x, ph, a in ((0.26, 0.0, 0.55), (0.74, 2.6, 0.55), (0.38, 1.2, 0.7), (0.62, 3.6, 0.7)):
        r = shape(lambda d, x=x, ph=ph: ribbon(d, x, 0.04, ph, 0.05))
        K.glow(c, r, (120, 220, 255, 255), 8, 0.8)
        K.fill(c, faint(soften(r, 2), a), K.linear((230, 250, 255, 255), (60, 160, 230, 255), 90))

    def drop(d):
        d.ellipse(pts([(0.39, 0.46), (0.61, 0.68)]), fill=255)
        d.polygon(pts([(0.5, 0.26), (0.605, 0.54), (0.395, 0.54)]), fill=255)
    m = shape(drop)
    solid(c, m, (240, 252, 255), (40, 140, 230), (140, 230, 255), 18, 1.5)
    K.fill(c, soften(ell_m(0.43, 0.52, 0.47, 0.62), 3), (255, 255, 255, 230))
    motes(c, 13, 10, (0.15, 0.2, 0.85, 0.85), (0.008, 0.016), (140, 230, 255))
    return K.finish(c)


# ---- enfeebling -----------------------------------------------------------------------------------------------------
def hourglass(c, cx, cy, s):
    def glass(d):
        top = [(cx - 0.17 * s, cy - 0.31 * s)] + [(cx + 0.17 * s * (1 - t) ** 1.6 + 0.025 * s * t, cy - 0.31 * s + 0.31 * s * t)
                                                  for t in (i / 12 for i in range(13))]
        topl = [(2 * cx - x, y) for x, y in top[::-1]]
        bot = [(x, 2 * cy - y) for x, y in top]
        botl = [(2 * cx - x, y) for x, y in bot[::-1]]
        d.polygon(pts(top + topl), fill=255)
        d.polygon(pts(bot + botl), fill=255)
    g = shape(glass)
    K.fill(c, soften(faint(g, 0.45)), K.linear((220, 240, 255, 255), (140, 180, 230, 255), 90))
    sand = shape(lambda d: [d.polygon(pts([(cx - 0.09 * s, cy - 0.10 * s), (cx + 0.09 * s, cy - 0.10 * s),
                                           (cx + 0.02 * s, cy - 0.01 * s), (cx - 0.02 * s, cy - 0.01 * s)]), fill=255),
                            d.line(pts([(cx, cy), (cx, cy + 0.26 * s)]), fill=255, width=max(1, int(0.016 * W * s))),
                            d.pieslice(pts([(cx - 0.16 * s, cy + 0.16 * s), (cx + 0.16 * s, cy + 0.44 * s)]), 180, 360,
                                       fill=255)])
    sand = ImageChops.multiply(sand, g)
    K.glow(c, sand, (255, 220, 120, 255), 6, 1.0)
    K.fill(c, soften(sand), K.linear((255, 236, 150, 255), (220, 150, 50, 255), 90))
    gl = shape(lambda d: d.line(pts([(cx - 0.10 * s, cy - 0.26 * s), (cx - 0.05 * s, cy - 0.12 * s)]), fill=255,
                                width=max(1, int(0.018 * W * s))))
    K.fill(c, soften(faint(gl, 0.8), 2), (255, 255, 255, 255))
    frame = shape(lambda d: [d.rounded_rectangle(pts([(cx - 0.25 * s, cy - 0.40 * s), (cx + 0.25 * s, cy - 0.31 * s)]),
                                                 radius=0.03 * W * s, fill=255),
                             d.rounded_rectangle(pts([(cx - 0.25 * s, cy + 0.31 * s), (cx + 0.25 * s, cy + 0.40 * s)]),
                                                 radius=0.03 * W * s, fill=255),
                             d.rectangle(pts([(cx - 0.215 * s, cy - 0.33 * s), (cx - 0.185 * s, cy + 0.33 * s)]), fill=255),
                             d.rectangle(pts([(cx + 0.185 * s, cy - 0.33 * s), (cx + 0.215 * s, cy + 0.33 * s)]), fill=255)])
    solid(c, frame, (255, 226, 160), (160, 96, 40), None, sh=True)


def slow():
    """An hourglass, its sand barely trickling."""
    c = bg((90, 90, 160), (10, 10, 30), 0.5, 0.45, 0.72)
    hourglass(c, 0.5, 0.5, 1.0)
    return K.finish(c)


def slowga():
    c = bg((90, 90, 160), (10, 10, 30), 0.5, 0.45, 0.72)
    party_ring(c, (230, 230, 255), (170, 170, 255), 0.82, 0.38, 0.07, pips=False)
    hourglass(c, 0.24, 0.60, 0.55)
    hourglass(c, 0.76, 0.60, 0.55)
    hourglass(c, 0.5, 0.45, 0.78)
    return K.finish(c)


def paralyzed(c, cx, cy, s, seed):
    m = shape(lambda d: person(d, cx, cy, s))
    K.shadow(c, m, 4, 6, 6, 150)
    K.glow(c, m, (255, 240, 120, 255), 12 * s, 1.2)
    K.fill(c, soften(m), K.linear((236, 220, 250, 255), (150, 120, 190, 255), 90))

    def bolt(d, pts_):
        d.line(pts(pts_), fill=255, width=int(0.035 * s * W), joint='curve')

    def q(x, y):
        return (cx + x * s, cy + y * s)
    bolts = shape(lambda d: [bolt(d, [q(-0.38, -0.30), q(-0.22, -0.22), q(-0.30, -0.12), q(-0.12, -0.04)]),
                             bolt(d, [q(0.40, -0.06), q(0.24, -0.12), q(0.32, 0.02), q(0.14, 0.06)]),
                             bolt(d, [q(-0.34, 0.30), q(-0.20, 0.22), q(-0.24, 0.36), q(-0.08, 0.28)]),
                             bolt(d, [q(0.30, 0.42), q(0.20, 0.30), q(0.30, 0.26), q(0.18, 0.16)])])
    K.glow(c, bolts, (255, 220, 40, 255), 10 * s, 1.8)
    K.fill(c, soften(bolts), (255, 250, 170, 255))


def paralyze():
    """A figure locked stiff, crackling yellow bolts crawling over it."""
    c = bg((110, 50, 140), (14, 4, 22), 0.5, 0.45, 0.72)
    paralyzed(c, 0.5, 0.52, 1.0, 3)
    return K.finish(c)


def paralyga():
    c = bg((110, 50, 140), (14, 4, 22), 0.5, 0.45, 0.72)
    party_ring(c, (255, 250, 200), (255, 230, 90), 0.82, 0.38, 0.07, pips=False)
    paralyzed(c, 0.24, 0.62, 0.55, 11)
    paralyzed(c, 0.76, 0.62, 0.55, 14)
    paralyzed(c, 0.5, 0.48, 0.74, 17)
    return K.finish(c)


def silenced(c, cx, cy, s):
    def bub(d):
        d.ellipse(pts([(cx - 0.32 * s, cy - 0.24 * s), (cx + 0.32 * s, cy + 0.20 * s)]), fill=255)
        d.polygon(pts([(cx - 0.16 * s, cy + 0.12 * s), (cx - 0.02 * s, cy + 0.16 * s), (cx - 0.24 * s, cy + 0.34 * s)]),
                  fill=255)
    m = shape(bub)
    solid(c, m, (255, 255, 255), (190, 220, 235), (190, 250, 255), 14 * s, 1.2)
    dots = shape(lambda d: [d.ellipse(pts([(cx + x * s - 0.045 * s, cy - 0.065 * s), (cx + x * s + 0.045 * s,
                                                                                         cy + 0.025 * s)]), fill=255)
                            for x in (-0.15, 0.0, 0.15)])
    K.fill(c, soften(dots), (70, 110, 140, 255))
    sl = shape(lambda d: d.line(pts([(cx - 0.34 * s, cy + 0.30 * s), (cx + 0.34 * s, cy - 0.34 * s)]), fill=255,
                                width=int(0.07 * s * W)))
    K.shadow(c, sl, 3, 5, 5, 160)
    K.glow(c, sl, (255, 60, 60, 255), 10 * s, 1.3)
    K.fill(c, soften(sl), K.linear((255, 120, 110, 255), (200, 20, 30, 255), 90))


def silence():
    """A speech bubble struck through."""
    c = bg((40, 140, 160), (4, 18, 24), 0.5, 0.45, 0.72)
    silenced(c, 0.5, 0.5, 1.0)
    return K.finish(c)


def silencega():
    c = bg((40, 140, 160), (4, 18, 24), 0.5, 0.45, 0.72)
    party_ring(c, (220, 255, 255), (120, 240, 255), 0.84, 0.36, 0.06, pips=False)
    silenced(c, 0.28, 0.66, 0.52)
    silenced(c, 0.72, 0.66, 0.52)
    silenced(c, 0.5, 0.36, 0.72)
    return K.finish(c)


def repose():
    """A white feather drifting down under a halo: a gentle, holy sleep."""
    c = bg((170, 110, 180), (24, 10, 34), 0.5, 0.42, 0.72)
    halo = ring_m(0.32, 0.14, 0.68, 0.26, 0.026)
    K.glow(c, halo, (255, 236, 160, 255), 10, 1.4)
    K.fill(c, soften(halo), (255, 240, 180, 255))
    m = shape(lambda d: leaf(d, 0.30, 0.82, math.radians(-58), 0.62, 0.11))
    solid(c, m, (255, 255, 255), (220, 210, 240), (255, 240, 255), 16, 1.3)
    quill = shape(lambda d: d.line(pts([(0.27, 0.87), (0.30 + math.cos(math.radians(-58)) * 0.58,
                                                       0.82 + math.sin(math.radians(-58)) * 0.58)]), fill=255,
                                   width=int(0.014 * W)))
    K.fill(c, soften(quill), (190, 170, 220, 255))
    barbs = shape(lambda d: [d.line(pts([(0.30 + math.cos(math.radians(-58)) * t, 0.82 + math.sin(math.radians(-58)) * t),
                                         (0.30 + math.cos(math.radians(-58)) * t + 0.08, 0.82 + math.sin(math.radians(-58)) * t + 0.02)]),
                                    fill=255, width=int(0.008 * W)) for t in (0.22, 0.36)])
    K.fill(c, soften(faint(ImageChops.multiply(barbs, m), 0.6)), (190, 170, 220, 255))

    def zz(d, x, y, s):
        d.line(pts([(x, y), (x + s, y), (x, y + s), (x + s, y + s)]), fill=255, width=int(0.016 * W))
    z = shape(lambda d: [zz(d, 0.64, 0.50, 0.08), zz(d, 0.75, 0.38, 0.055)])
    K.glow(c, z, (255, 220, 255, 255), 6)
    K.fill(c, soften(z), (255, 255, 255, 255))
    return K.finish(c)


def hastega():
    """Haste's double chevrons, cast over the whole party."""
    c = bg((210, 160, 40), (40, 22, 4), 0.42, 0.45, 0.74)
    party_ring(c, (255, 250, 220), (255, 220, 110), 0.76, 0.36, 0.08)
    streaks = shape(lambda d: [d.rounded_rectangle(pts([(x0, y - 0.014), (x1, y + 0.014)]), radius=0.014 * W, fill=255)
                               for x0, x1, y in ((0.10, 0.32, 0.30), (0.06, 0.28, 0.44), (0.10, 0.32, 0.58))])
    K.glow(c, streaks, (255, 240, 170, 255), 8)
    K.fill(c, faint(soften(streaks), 0.8), (255, 250, 220, 255))

    def chev(d, x):
        d.polygon(pts([(x, 0.20), (x + 0.12, 0.20), (x + 0.27, 0.44), (x + 0.12, 0.68), (x, 0.68), (x + 0.15, 0.44)]),
                  fill=255)
    m = shape(lambda d: [chev(d, 0.30), chev(d, 0.48)])
    solid(c, m, (255, 255, 240), (240, 150, 40), (255, 230, 120), 16, 1.3)
    return K.finish(c)


# ---- bar-spells ---------------------------------------------------------------------------------------------------
BAR_ELEMENT = {'Fire': 8, 'Blizzard': 190, 'Aero': 120, 'Stone': K.EARTH, 'Thunder': K.THUNDER, 'Water': 225}
BAR_STATUS = {'sleep': 250, 'poison': 290, 'paralyze': 52, 'blind': 215, 'silence': 180, 'petrify': 28,
              'virus': 110, 'amnesia': 335}


def bar_element_paint(ra):
    """An elemental comet breaking against a shimmering dome (hue: which element; -ra: the party under it)."""
    c = bg((170, 60, 20), (22, 4, 4), 0.32, 0.30, 0.80)
    box = (0.10, 0.44, 0.90, 1.24)
    dome = shape(lambda d: d.pieslice(pts([box[:2], box[2:]]), 180, 360, fill=255))
    K.fill(c, faint(dome.filter(ImageFilter.GaussianBlur(8)), 0.45), (255, 190, 150, 255))
    hexes = shape(lambda d: [d.line(pts([(x, 0.86), (x, 0.50)]), fill=255, width=int(0.012 * W))
                             for x in (0.30, 0.50, 0.70)] +
                  [d.arc(pts([(0.22, 0.58), (0.78, 1.14)]), 180, 360, fill=255, width=int(0.012 * W))])
    K.fill(c, soften(faint(ImageChops.multiply(hexes, dome), 0.35)), (255, 230, 200, 255))
    if ra:
        pm = shape(lambda d: [d.ellipse(pts([(x - 0.055, 0.70 - 0.055), (x + 0.055, 0.70 + 0.055)]), fill=255)
                              for x in (0.30, 0.5, 0.70)])
        K.glow(c, pm, (255, 200, 160, 255), 8, 1.6)
        K.fill(c, soften(pm), (255, 255, 255, 255))
    shell = shape(lambda d: d.arc(pts([box[:2], box[2:]]), 180, 360, fill=255, width=int(0.055 * W)))
    K.glow(c, shell, (255, 170, 110, 255), 16, 1.5)
    K.fill(c, soften(shell), K.linear((255, 255, 245, 255), (255, 190, 140, 255), 90))
    ix, iy = 0.5, 0.44
    tail = shape(lambda d: d.polygon(pts([(0.10, 0.06), (ix - 0.08, iy - 0.16), (ix + 0.02, iy - 0.08)]), fill=255))
    K.glow(c, tail, (255, 120, 40, 255), 14, 1.1)
    K.fill(c, soften(tail, 4), K.linear((255, 120, 40, 40), (255, 230, 160, 255), 35))
    splash = shape(lambda d: d.polygon(pts([(ix + (x - ix), iy + (y - iy) * 0.55) for x, y in
                                            star_pts(ix, iy, 8, 0.22, 0.06, 0.0)]), fill=255))
    K.glow(c, splash, (255, 160, 60, 255), 14, 1.5)
    K.fill(c, soften(splash), (255, 236, 180, 255))
    orb = ell_m(ix - 0.12, iy - 0.25, ix + 0.08, iy - 0.05)
    K.glow(c, orb, (255, 120, 30, 255), 18, 1.6)
    K.fill(c, soften(orb), K.radial((255, 252, 230, 255), (250, 90, 20, 255), ix - 0.05, iy - 0.18, 0.12))
    return K.finish(c)


def ward(c, cx, top, w, h):
    m = shape(lambda d: heater(d, cx, top, w, h))
    K.shadow(c, m, 5, 8, 8, 160)
    K.glow(c, m, (220, 120, 255, 255), 18 * w / 0.25, 1.3)
    K.fill(c, soften(m), K.linear((150, 70, 190, 255), (60, 14, 90, 255), 90))
    edge = ImageChops.subtract(m, shape(lambda d: heater(d, cx, top + h * 0.07, w * 0.84, h * 0.86)))
    K.fill(c, soften(edge), K.linear((255, 255, 255, 255), (230, 180, 255, 255), 90))
    sk = shape(lambda d: GB.skull(d, cx, top + h * 0.46, w * 1.9))
    K.glow(c, sk, (255, 220, 255, 255), 6, 1.0)
    K.fill(c, soften(sk), K.linear((255, 245, 255, 255), (210, 180, 235, 255), 90))
    sl = shape(lambda d: d.line(pts([(cx - w * 0.85, top + h * 0.80), (cx + w * 0.85, top + h * 0.10)]), fill=255,
                                width=int(0.042 * W * w / 0.25)))
    sl = ImageChops.multiply(sl, m)
    K.fill(c, soften(sl.filter(ImageFilter.MaxFilter(9))), (40, 0, 60, 255))
    K.fill(c, soften(sl), (255, 255, 255, 255))


def bar_status_paint(ra):
    """A ward shield bearing a skull that is struck out: protection against an ailment (hue: which one;
    -ra: the party under the ward)."""
    c = bg((150, 60, 170), (18, 4, 24), 0.5, 0.45, 0.72)
    if ra:
        ward(c, 0.5, 0.14, 0.21, 0.54)
        pm = shape(lambda d: [d.ellipse(pts([(x - 0.055, y - 0.055), (x + 0.055, y + 0.055)]), fill=255)
                              for x, y in ((0.30, 0.76), (0.5, 0.80), (0.70, 0.76))])
        K.glow(c, pm, (230, 160, 255, 255), 8, 1.6)
        K.fill(c, soften(pm), (255, 255, 255, 255))
    else:
        ward(c, 0.5, 0.18, 0.25, 0.66)
    return K.finish(c)


def bar_element():
    return bar_element_paint(False)


def bar_element_ra():
    return bar_element_paint(True)


def bar_status():
    return bar_status_paint(False)


def bar_status_ra():
    return bar_status_paint(True)


# ---- warps ----------------------------------------------------------------------------------------------------------
def recall():
    """A swirling portal gate (hue: which crag)."""
    c = bg((40, 130, 60), (4, 20, 8), 0.5, 0.5, 0.72)
    inner = ell_m(0.28, 0.14, 0.72, 0.86)
    K.fill(c, soften(inner, 4), K.radial((230, 255, 220, 255), (30, 110, 50, 255), 0.5, 0.5, 0.36))
    arms = mask()
    ad = ImageDraw.Draw(arms)
    for k in range(4):
        seq = []
        for i in range(40):
            t = i / 39
            a = k * math.pi / 2 + t * 3.4
            r = 0.02 + 0.30 * t
            seq.append((0.5 + math.cos(a) * r * 0.72, 0.5 + math.sin(a) * r * 1.15))
        ad.line(pts(seq), fill=255, width=int(0.028 * W), joint='curve')
    arms = ImageChops.multiply(arms, inner)
    K.fill(c, soften(faint(arms, 0.7), 2), (240, 255, 230, 255))
    rim = ring_m(0.27, 0.13, 0.73, 0.87, 0.05)
    K.shadow(c, rim, 4, 7, 7, 150)
    K.glow(c, rim, (150, 255, 160, 255), 16, 1.4)
    K.fill(c, soften(rim), K.linear((255, 255, 240, 255), (120, 220, 120, 255), 90))
    core = ell_m(0.45, 0.45, 0.55, 0.55)
    K.glow(c, core, (255, 255, 255, 255), 14, 1.6)
    K.fill(c, soften(core), (255, 255, 255, 255))
    sparkles(c, [(0.80, 0.24, 0.07), (0.20, 0.78, 0.05)], (180, 255, 180))
    return K.finish(c)


def teleport():
    """A towering crystal over a warp ring, a pillar of light behind it (hue: which crystal)."""
    c = bg((40, 120, 190), (4, 14, 34), 0.5, 0.45, 0.72)
    beam = shape(lambda d: d.rectangle(pts([(0.38, 0.0), (0.62, 0.9)]), fill=255))
    K.fill(c, faint(beam.filter(ImageFilter.GaussianBlur(18)), 0.5), (200, 240, 255, 255))
    party_ring(c, (220, 245, 255), (120, 210, 255), 0.80, 0.30, 0.07, pips=False)
    outline = [(0.5, 0.10), (0.64, 0.36), (0.58, 0.70), (0.5, 0.80), (0.42, 0.70), (0.36, 0.36)]
    m = shape(lambda d: d.polygon(pts(outline), fill=255))
    K.shadow(c, m, 4, 7, 7, 150)
    K.glow(c, m, (120, 210, 255, 255), 22, 1.5)
    K.fill(c, soften(m), (60, 150, 230, 255))
    for poly, col in (([(0.5, 0.10), (0.5, 0.80), (0.42, 0.70), (0.36, 0.36)], (190, 235, 255)),
                      ([(0.5, 0.10), (0.36, 0.36), (0.5, 0.42)], (240, 252, 255)),
                      ([(0.5, 0.10), (0.64, 0.36), (0.5, 0.42)], (150, 210, 250)),
                      ([(0.5, 0.42), (0.64, 0.36), (0.58, 0.70), (0.5, 0.80)], (40, 110, 210))):
        f = shape(lambda d, poly=poly: d.polygon(pts(poly), fill=255))
        K.fill(c, soften(faint(f, 0.85)), col + (255,))
    sparkles(c, [(0.62, 0.20, 0.08), (0.26, 0.56, 0.05), (0.76, 0.58, 0.045)], (190, 240, 255))
    return K.finish(c)


# ---- healing -------------------------------------------------------------------------------------------------------
def cura():
    """A cross of healing light pulsing out from the caster in rings."""
    c = bg((50, 160, 120), (4, 26, 18), 0.5, 0.5, 0.72)
    for r, a in ((0.40, 0.45), (0.30, 0.75)):
        rg = ring_m(0.5 - r, 0.5 - r, 0.5 + r, 0.5 + r, 0.022)
        K.glow(c, rg, (140, 255, 200, 255), 10, 1.2)
        K.fill(c, soften(faint(rg, a), 2), (220, 255, 236, 255))
    motes(c, 8, 14, (0.15, 0.15, 0.85, 0.85), (0.006, 0.014), (160, 255, 200))
    m = shape(lambda d: cross(d, 0.5, 0.5, 0.62))
    solid(c, m, (255, 255, 250), (170, 246, 200), (140, 255, 190), 24, 1.5)
    return K.finish(c)


def full_cure():
    """A regal cross of light in a golden halo and star: everything restored."""
    c = bg((30, 130, 90), (2, 20, 12), 0.5, 0.48, 0.74)
    GB.rays(c, 0.5, 0.5, 16, 0.7, (255, 240, 180, 255), 70, 0.06, 8)
    st = shape(lambda d: d.polygon(pts(star_pts(0.5, 0.5, 8, 0.42, 0.24, -math.pi / 2 + math.pi / 8)), fill=255))
    K.glow(c, st, (255, 210, 100, 255), 20, 1.3)
    K.fill(c, soften(st), K.radial((255, 240, 170, 255), (210, 140, 40, 255), 0.5, 0.5, 0.42))
    halo = ring_m(0.22, 0.22, 0.78, 0.78, 0.03)
    K.fill(c, soften(halo), K.linear((255, 250, 210, 255), (200, 130, 40, 255), 90))
    m = shape(lambda d: cross(d, 0.5, 0.5, 0.66))
    solid(c, m, (255, 255, 255), (180, 255, 210), (200, 255, 220), 18, 1.6)
    sparkles(c, [(0.80, 0.20, 0.09), (0.18, 0.80, 0.06)], (255, 240, 180))
    return K.finish(c)


def sacrifice():
    """A pure heart drawing a dark ailment out of an ally and into itself."""
    c = bg((60, 110, 150), (6, 12, 24), 0.42, 0.55, 0.74)
    seq = bezier((0.86, 0.14), (0.78, 0.50), (0.54, 0.50), 30)
    wisp = mask()
    wd = ImageDraw.Draw(wisp)
    for i in range(len(seq) - 1):
        w = 0.10 * (1 - i / len(seq)) + 0.035
        wd.line(pts([seq[i], seq[i + 1]]), fill=255, width=int(w * W))
    K.glow(c, wisp, (220, 140, 255, 255), 14, 1.6)
    K.fill(c, soften(wisp, 3), K.linear((170, 80, 210, 255), (80, 10, 110, 255), 0))
    dark = dots(31, 8, 0.66, 0.90, 0.12, 0.34, 0.015, 0.03)
    K.glow(c, dark, (220, 140, 255, 255), 6, 1.4)
    K.fill(c, soften(dark), (110, 40, 150, 255))
    m = shape(lambda d: GB.heart(d, 0.36, 0.58, 0.66))
    solid(c, m, (255, 255, 255), (255, 180, 200), (255, 230, 240), 22, 1.5)
    taint = ell_m(0.42, 0.50, 0.54, 0.62)
    K.fill(c, soften(faint(ImageChops.multiply(taint, m), 0.6), 6), (130, 60, 170, 255))
    hl = ell_m(0.22, 0.48, 0.30, 0.56)
    K.fill(c, soften(hl, 4), (255, 255, 255, 255))
    return K.finish(c)


def dots(seed, n, x0, x1, y0, y1, r0, r1):
    return GA.dots(seed, n, x0, x1, y0, y1, r0, r1)


def arise():
    """A golden winged ankh rising in light: raise and reraise together."""
    c = bg((110, 150, 220), (10, 16, 40), 0.5, 0.42, 0.74)
    beam = shape(lambda d: d.rectangle(pts([(0.38, 0.0), (0.62, 1.0)]), fill=255))
    K.fill(c, faint(beam.filter(ImageFilter.GaussianBlur(20)), 0.55), (255, 250, 230, 255))
    w = shape(lambda d: [wing(d, 1, 0.58, 0.48, 1.25, 6, 70, 0), wing(d, -1, 0.42, 0.48, 1.25, 6, 70, 0)])
    solid(c, w, (255, 255, 255), (200, 214, 245), (255, 255, 240), 14, 1.3)
    m = shape(lambda d: ankh(d, 0.5, 0.16, 0.92))
    solid(c, m, (255, 250, 210), (220, 160, 60), (255, 220, 140), 18, 1.4)
    sparkles(c, [(0.22, 0.80, 0.06), (0.80, 0.80, 0.06)], (255, 240, 200))
    return K.finish(c)


def reraise():
    """A phoenix feather in a circle of return: you will rise again."""
    c = bg((170, 70, 30), (28, 6, 4), 0.5, 0.5, 0.72)
    arc = shape(lambda d: arc_arrow(d, 0.5, 0.5, 0.37, 130, 420, 0.04, 0.055))
    K.glow(c, arc, (255, 200, 120, 255), 10, 1.3)
    K.fill(c, soften(arc), (255, 240, 210, 255))
    ang = math.radians(-58)
    ux, uy = math.cos(ang), math.sin(ang)
    m = shape(lambda d: leaf(d, 0.34, 0.80, ang, 0.62, 0.13))
    cuts = shape(lambda d: [d.line(pts([(0.34 + ux * t + side * -uy * 0.16, 0.80 + uy * t + side * ux * 0.16),
                                        (0.34 + ux * (t - 0.10) + side * -uy * 0.02,
                                         0.80 + uy * (t - 0.10) + side * ux * 0.02)]),
                                   fill=255, width=int(0.016 * W)) for t in (0.24, 0.40) for side in (-1, 1)])
    m = ImageChops.subtract(m, cuts)
    K.shadow(c, m, 5, 8, 8, 160)
    K.glow(c, m, (255, 140, 40, 255), 18, 1.5)
    K.fill(c, soften(m), K.linear((255, 244, 160, 255), (230, 60, 20, 255), 120))
    quill = shape(lambda d: d.line(pts([(0.31, 0.85), (0.34 + ux * 0.58, 0.80 + uy * 0.58)]), fill=255,
                                   width=int(0.016 * W)))
    K.fill(c, soften(quill), (255, 250, 220, 255))
    motes(c, 17, 12, (0.2, 0.2, 0.8, 0.8), (0.006, 0.014), (255, 160, 60), (255, 240, 200))
    return K.finish(c)


# ---- party support -------------------------------------------------------------------------------------------------
def auspice():
    """A golden omen-star streaking down on the party."""
    c = bg((200, 120, 70), (34, 10, 8), 0.6, 0.55, 0.74)
    party_ring(c, (255, 245, 220), (255, 200, 120), 0.76, 0.34, 0.08)
    hx, hy = 0.56, 0.44
    tail = shape(lambda d: d.polygon(pts([(0.08, 0.10), (hx - 0.06, hy - 0.16), (hx + 0.08, hy - 0.02)]), fill=255))
    K.glow(c, tail, (255, 200, 100, 255), 16, 1.2)
    K.fill(c, soften(tail, 4), K.linear((255, 200, 120, 30), (255, 250, 220, 255), 40))
    st = shape(lambda d: d.polygon(pts(star_pts(hx, hy, 5, 0.25, 0.11, -math.pi / 2 + 0.25)), fill=255))
    solid(c, st, (255, 255, 230), (250, 180, 50), (255, 220, 120), 22, 1.6)
    core = ell_m(hx - 0.05, hy - 0.05, hx + 0.05, hy + 0.05)
    K.glow(c, core, (255, 255, 255, 255), 10, 1.4)
    K.fill(c, soften(core), (255, 255, 255, 255))
    sparkles(c, [(0.82, 0.22, 0.07), (0.20, 0.50, 0.05)], (255, 230, 160))
    return K.finish(c)


def embrava():
    """A golden laurel wreath around a radiant star: haste, regen and refresh in one."""
    c = bg((40, 130, 110), (4, 20, 18), 0.5, 0.48, 0.72)

    def wreath(d):
        for side in (-1, 1):
            for i in range(7):
                t = i / 6
                a = math.radians(100 + 150 * t) if side < 0 else math.radians(80 - 150 * t)
                bx, by = 0.5 + math.cos(a) * 0.30, 0.52 + math.sin(a) * 0.30
                tang = a + (math.pi / 2 if side < 0 else -math.pi / 2)
                leaf(d, bx, by, tang + side * 0.5, 0.14, 0.04)
    m = shape(wreath)
    stems = shape(lambda d: [d.arc(pts([(0.20, 0.22), (0.80, 0.82)]), 100, 250, fill=255, width=int(0.016 * W)),
                             d.arc(pts([(0.20, 0.22), (0.80, 0.82)]), -70, 80, fill=255, width=int(0.016 * W))])
    m = ImageChops.lighter(m, stems)
    solid(c, m, (255, 240, 170), (200, 130, 40), (255, 210, 110), 12, 1.2)
    st = shape(lambda d: d.polygon(pts(star_pts(0.5, 0.50, 4, 0.20, 0.06)), fill=255))
    K.glow(c, st, (255, 255, 220, 255), 18, 1.6)
    K.fill(c, soften(st), (255, 255, 250, 255))
    for x, y, col in ((0.5, 0.30, (120, 230, 90)), (0.33, 0.62, (90, 170, 255)), (0.67, 0.62, (255, 210, 80))):
        o = ell_m(x - 0.035, y - 0.035, x + 0.035, y + 0.035)
        K.glow(c, o, col + (255,), 7, 1.4)
        K.fill(c, soften(o), (255, 255, 255, 255))
    return K.finish(c)


def crusade():
    """A crusader's banner: a red cross on white, waving from a golden pole."""
    c = bg((170, 40, 40), (26, 4, 6), 0.55, 0.45, 0.72)

    def flag(d):
        top, bot = [], []
        for i in range(21):
            t = i / 20
            x = 0.33 + 0.50 * t
            wv = 0.035 * math.sin(t * math.pi * 1.8)
            top.append((x, 0.20 + wv))
            bot.append((x, 0.62 + wv))
        notch = (0.73, 0.41 + 0.035 * math.sin(math.pi * 1.8))
        d.polygon(pts(top + [notch] + bot[::-1]), fill=255)
    m = shape(flag)
    solid(c, m, (255, 255, 255), (210, 200, 200), (255, 220, 200), 12, 1.1)
    crs = shape(lambda d: [d.rectangle(pts([(0.49, 0.22), (0.57, 0.64)]), fill=255),
                           d.rectangle(pts([(0.35, 0.37), (0.75, 0.45)]), fill=255)])
    crs = ImageChops.multiply(crs, m)
    K.fill(c, soften(crs), K.linear((240, 60, 50, 255), (170, 20, 30, 255), 90))
    shade = shape(lambda d: [d.rectangle(pts([(0.33 + 0.5 * t, 0.15), (0.33 + 0.5 * t + 0.07, 0.7)]), fill=255)
                             for t in (0.35, 0.85)])
    K.fill(c, soften(faint(ImageChops.multiply(shade, m), 0.18), 12), (60, 20, 30, 255))
    pole = shape(lambda d: [d.rounded_rectangle(pts([(0.29, 0.14), (0.335, 0.90)]), radius=0.02 * W, fill=255),
                            d.ellipse(pts([(0.275, 0.09), (0.35, 0.16)]), fill=255)])
    solid(c, pole, (255, 236, 160), (190, 120, 40), None)
    return K.finish(c)


def animus(up):
    """Enmity turned up (a red blaze, rising arrow) or down (a calm blue mist, falling arrow)."""
    if up:
        c = bg((190, 50, 30), (30, 4, 4), 0.5, 0.55, 0.72)
        aura = shape(lambda d: [flame(d, 0.5, 0.88, 0.30, 0.74), flame(d, 0.28, 0.88, 0.12, 0.42, -0.06),
                                flame(d, 0.72, 0.88, 0.12, 0.44, 0.06)])
        K.glow(c, aura, (255, 100, 40, 255), 20, 1.0)
        K.fill(c, soften(faint(aura, 0.55), 3), K.linear((255, 210, 100, 255), (200, 40, 20, 255), 270))
        m = shape(lambda d: up_arrow(d, 0.5, 0.16, 0.20, 0.64))
        solid(c, m, (255, 255, 230), (255, 150, 60), (255, 120, 60), 16, 1.4)
    else:
        c = bg((40, 90, 170), (4, 10, 30), 0.5, 0.45, 0.72)
        mist = shape(lambda d: [d.ellipse(pts([(x - 0.18, y - 0.06), (x + 0.18, y + 0.06)]), fill=255)
                                for x, y in ((0.32, 0.70), (0.66, 0.74), (0.50, 0.82), (0.30, 0.30), (0.70, 0.26))])
        K.fill(c, faint(mist.filter(ImageFilter.GaussianBlur(14)), 0.6), (190, 220, 255, 255))
        m = shape(lambda d: up_arrow(d, 0.5, 0.16, 0.20, 0.64))
        m = m.transpose(Image.FLIP_TOP_BOTTOM)
        solid(c, m, (240, 250, 255), (90, 150, 230), (140, 200, 255), 16, 1.4)
    return K.finish(c)


def animus_augeo():
    return animus(True)


def animus_minuo():
    return animus(False)


def addle():
    """A dizzying spiral that muddles a caster's mind."""
    c = bg((150, 60, 150), (20, 4, 22), 0.5, 0.5, 0.72)
    seq = []
    for i in range(160):
        t = i / 159
        a = t * math.pi * 5.2
        r = 0.02 + 0.30 * t
        seq.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
    m = shape(lambda d: d.line(pts(seq), fill=255, width=int(0.045 * W), joint='curve'))
    solid(c, m, (255, 230, 255), (210, 110, 220), (255, 160, 255), 14, 1.3)
    stars = shape(lambda d: [d.polygon(pts(star_pts(x, y, 5, r, r * 0.45)), fill=255)
                             for x, y, r in ((0.80, 0.24, 0.07), (0.20, 0.30, 0.055), (0.78, 0.78, 0.05))])
    K.glow(c, stars, (255, 240, 120, 255), 8, 1.4)
    K.fill(c, soften(stars), (255, 250, 200, 255))
    return K.finish(c)


# ---- field magic ----------------------------------------------------------------------------------------------------
def invisible():
    """A see-through hand: only its glowing edge shows, the stars behind it shining through, the wrist dissolving."""
    c = bg((40, 100, 140), (4, 12, 26), 0.5, 0.45, 0.72)
    sparkles(c, [(0.47, 0.42, 0.05), (0.58, 0.60, 0.035), (0.80, 0.24, 0.07)], (170, 230, 255))

    def hand(d):
        d.rounded_rectangle(pts([(0.33, 0.44), (0.67, 0.74)]), radius=0.10 * W, fill=255)
        for x, top in ((0.365, 0.24), (0.455, 0.15), (0.545, 0.17), (0.635, 0.26)):
            d.rounded_rectangle(pts([(x - 0.038, top), (x + 0.038, 0.52)]), radius=0.038 * W, fill=255)
        d.line(pts([(0.37, 0.64), (0.22, 0.46), (0.19, 0.38)]), fill=255, width=int(0.08 * W), joint='curve')
        d.ellipse(pts([(0.15, 0.34), (0.23, 0.42)]), fill=255)
        d.rectangle(pts([(0.39, 0.70), (0.61, 0.96)]), fill=255)
    full = shape(hand)
    vanish = K.linear((255, 255, 255, 255), (0, 0, 0, 255), 90).convert('L').point(
        lambda v: max(0, min(255, int((v - 60) * 1.9))))
    edge = ImageChops.subtract(full, full.filter(ImageFilter.MinFilter(int(0.035 * W) | 1)))
    K.fill(c, faint(ImageChops.multiply(soften(full, 2), vanish), 0.22), (170, 230, 255, 255))
    K.glow(c, ImageChops.multiply(edge, vanish), (120, 220, 255, 255), 12, 2.0)
    K.fill(c, soften(ImageChops.multiply(edge, vanish)), (240, 252, 255, 255))
    motes(c, 23, 16, (0.34, 0.70, 0.66, 0.92), (0.008, 0.016), (140, 220, 255))
    return K.finish(c)


def footprint(d, cx, cy, s, ang):
    seq = [(-0.07, -0.10, 0.075, 0.12), (0.0, 0.12, 0.055, 0.07)]
    for x, y, rx, ry in seq:
        d.polygon(GB.xf(GB.ell(x, y, rx, ry), cx, cy, s, ang), fill=255)
    for x, y, r in ((-0.13, -0.26, 0.035), (-0.06, -0.29, 0.03), (0.0, -0.27, 0.027), (0.05, -0.23, 0.024),
                    (0.08, -0.17, 0.022)):
        d.polygon(GB.xf(GB.ell(x + 0.02, y, r, r), cx, cy, s, ang), fill=255)


def sneak():
    """Tiptoeing footprints, fading as they go: no sound to follow."""
    c = bg((60, 130, 100), (6, 18, 14), 0.5, 0.5, 0.72)
    for cx, cy, s, ang, a in ((0.66, 0.34, 0.85, 16, 0.5), (0.38, 0.62, 1.2, -14, 1.0)):
        m = shape(lambda d, cx=cx, cy=cy, s=s, ang=ang: footprint(d, cx, cy, s, ang))
        if a == 1.0:
            K.shadow(c, m, 4, 7, 7, 150)
        K.glow(c, m, (180, 255, 220, 255), 14, a * 1.4)
        K.fill(c, faint(soften(m), a), K.linear((245, 255, 250, 255), (160, 225, 195, 255), 90))
    motes(c, 6, 8, (0.55, 0.55, 0.85, 0.85), (0.006, 0.012), (180, 255, 220))
    return K.finish(c)


def deodorize():
    """Wisps of scent curling up from a flower and vanishing into clean air."""
    c = bg((100, 150, 70), (12, 22, 6), 0.5, 0.55, 0.72)
    for x0, ph in ((0.36, 0.0), (0.5, 1.5), (0.64, 3.0)):
        seq = [(x0 + 0.06 * math.sin(t * 8 + ph), 0.60 - 0.48 * t) for t in (i / 40 for i in range(41))]
        w = shape(lambda d, seq=seq: d.line(pts(seq), fill=255, width=int(0.045 * W), joint='curve'))
        w = ImageChops.multiply(w, K.linear((60, 60, 60, 255), (255, 255, 255, 255), 90).convert('L'))
        K.glow(c, w, (240, 255, 220, 255), 12, 1.8)
        K.fill(c, soften(w, 2), (255, 255, 245, 255))
    petals = shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.10 - 0.08, 0.72 + math.sin(a) * 0.10 - 0.08),
                                             (0.5 + math.cos(a) * 0.10 + 0.08, 0.72 + math.sin(a) * 0.10 + 0.08)]),
                                        fill=255) for a in (math.pi * 2 * i / 5 - math.pi / 2 for i in range(5))])
    solid(c, petals, (255, 250, 255), (240, 170, 215), (255, 230, 250), 10, 1.2)
    ctr = ell_m(0.455, 0.675, 0.545, 0.765)
    K.fill(c, soften(ctr), (255, 210, 80, 255))
    sparkles(c, [(0.78, 0.22, 0.08), (0.22, 0.28, 0.06)], (230, 255, 210))
    return K.finish(c)


# ---- elemental families ---------------------------------------------------------------------------------------------
STORM = {'Firestorm': 8, 'Sandstorm': K.EARTH, 'Aurorastorm': K.LIGHT, 'Windstorm': 120, 'Hailstorm': 190, 'Rainstorm': 225,
         'Thunderstorm': K.THUNDER, 'Voidstorm': K.DARK}
EN = {'Enfire': 8, 'Enstone': K.EARTH, 'Enlight': K.LIGHT, 'Enaero': 120, 'Enblizzard': 190, 'Enwater': 225, 'Enthunder': K.THUNDER}


def storm():
    """A storm cloud loosing a slanting downpour of its element (hue: which element)."""
    c = bg((150, 50, 20), (22, 4, 4), 0.5, 0.35, 0.74)
    streaks = mask()
    sd = ImageDraw.Draw(streaks)
    rnd = random.Random(9)
    for i in range(9):
        x = 0.20 + i * 0.075 + rnd.uniform(-0.02, 0.02)
        y0 = 0.46 + rnd.uniform(0, 0.06)
        L = rnd.uniform(0.18, 0.34)
        sd.line(pts([(x, y0), (x - L * 0.35, y0 + L)]), fill=255, width=int(0.022 * W))
    K.glow(c, streaks, (255, 140, 60, 255), 8, 1.4)
    K.fill(c, soften(streaks), K.linear((255, 240, 200, 255), (255, 120, 40, 255), 90))
    bolt = shape(lambda d: d.polygon(pts([(0.56, 0.46), (0.48, 0.66), (0.54, 0.66), (0.46, 0.86), (0.64, 0.60),
                                          (0.57, 0.60), (0.63, 0.46)]), fill=255))
    K.glow(c, bolt, (255, 200, 120, 255), 12, 1.5)
    K.fill(c, soften(bolt), (255, 250, 230, 255))

    def cloud(d):
        for x, y, r in ((0.30, 0.38, 0.12), (0.45, 0.28, 0.16), (0.62, 0.32, 0.14), (0.74, 0.40, 0.10),
                        (0.50, 0.42, 0.13)):
            d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
        d.rounded_rectangle(pts([(0.20, 0.38), (0.84, 0.50)]), radius=0.06 * W, fill=255)
    m = shape(cloud)
    solid(c, m, (255, 190, 140), (140, 40, 20), (255, 110, 50), 18, 1.2)
    sw = shape(lambda d: d.arc(pts([(0.36, 0.22), (0.58, 0.44)]), 190, 330, fill=255, width=int(0.02 * W)))
    K.fill(c, soften(faint(sw, 0.6), 2), (255, 240, 220, 255))
    return K.finish(c)


def en_spell():
    """A sword wreathed in elemental aura (hue: which element)."""
    c = bg((140, 44, 20), (20, 4, 4), 0.5, 0.5, 0.72)
    aura = shape(lambda d: [flame(d, 0.5, 0.80, 0.20, 0.72, 0.03), flame(d, 0.36, 0.76, 0.09, 0.38, -0.05),
                            flame(d, 0.64, 0.74, 0.09, 0.42, 0.05)])
    K.glow(c, aura, (255, 110, 30, 255), 24, 1.3)
    K.fill(c, soften(aura, 3), K.linear((255, 220, 110, 255), (230, 60, 20, 255), 270))
    m = shape(lambda d: GA.sword(d, 0.5, 0.90, 0.5, 0.10, 0.05, 0.13, 0.15))
    K.shadow(c, m, 4, 6, 6, 140)
    K.fill(c, soften(m), K.linear((255, 250, 235, 255), (200, 170, 150, 255), 90))
    edge = shape(lambda d: d.line(pts([(0.5, 0.14), (0.5, 0.70)]), fill=255, width=int(0.014 * W)))
    K.fill(c, soften(faint(edge, 0.8)), (255, 170, 80, 255))
    hilt = shape(lambda d: d.rectangle(pts([(0.35, 0.73), (0.65, 0.92)]), fill=255))
    K.fill(c, soften(ImageChops.multiply(m, hilt)), K.linear((230, 180, 120, 255), (120, 60, 30, 255), 90))
    motes(c, 27, 12, (0.2, 0.08, 0.8, 0.5), (0.006, 0.013), (255, 160, 60), (255, 240, 200))
    return K.finish(c)


STAT = {'STR': 8, 'DEX': K.THUNDER, 'VIT': K.EARTH, 'AGI': 120, 'INT': 190, 'MND': 225, 'CHR': K.LIGHT}


def gain():
    """A stat crystal with a rising arrow (hue: which stat)."""
    c = bg((150, 40, 30), (24, 4, 4), 0.5, 0.5, 0.72)
    gem(c, 0.44, 0.52, 1.25, (255, 200, 180), (200, 30, 30), (255, 90, 70))
    m = shape(lambda d: up_arrow(d, 0.74, 0.18, 0.11, 0.40))
    solid(c, m, (255, 255, 240), (255, 200, 120), (255, 230, 160), 10, 1.5)
    return K.finish(c)


def boost_stat():
    """The stat crystal lifted over the whole party (hue: which stat)."""
    c = bg((150, 40, 30), (24, 4, 4), 0.5, 0.5, 0.72)
    party_ring(c, (255, 230, 220), (255, 120, 90), 0.76, 0.36, 0.08)
    gem(c, 0.5, 0.40, 0.95, (255, 200, 180), (200, 30, 30), (255, 90, 70))
    m = shape(lambda d: [up_arrow(d, 0.20, 0.30, 0.07, 0.28), up_arrow(d, 0.80, 0.30, 0.07, 0.28)])
    solid(c, m, (255, 255, 240), (255, 200, 120), (255, 230, 160), 8, 1.5)
    return K.finish(c)


# ---- RDM / SCH / PLD extras ---------------------------------------------------------------------------------------
def temper():
    """A blade glowing red-hot on the anvil: tempered for more strikes."""
    c = bg((60, 70, 110), (8, 8, 20), 0.5, 0.42, 0.72)

    def anvil(d):
        d.polygon(pts([(0.14, 0.62), (0.30, 0.60), (0.80, 0.60), (0.84, 0.68), (0.30, 0.68), (0.22, 0.66)]), fill=255)
        d.polygon(pts([(0.40, 0.68), (0.70, 0.68), (0.64, 0.76), (0.46, 0.76)]), fill=255)
        d.polygon(pts([(0.36, 0.76), (0.74, 0.76), (0.78, 0.86), (0.32, 0.86)]), fill=255)
    a = shape(anvil)
    solid(c, a, (190, 196, 220), (60, 64, 84), None)
    blade = shape(lambda d: GA.sword(d, 0.86, 0.50, 0.16, 0.48, 0.045, 0.09, 0.13))
    K.shadow(c, blade, 4, 6, 6, 160)
    K.glow(c, blade, (255, 110, 30, 255), 20, 1.6)
    K.fill(c, soften(blade), K.linear((255, 250, 200, 255), (255, 110, 30, 255), 0))
    hot = shape(lambda d: d.line(pts([(0.18, 0.485), (0.70, 0.495)]), fill=255, width=int(0.012 * W)))
    K.fill(c, soften(hot), (255, 255, 240, 255))
    motes(c, 41, 22, (0.20, 0.18, 0.70, 0.46), (0.006, 0.016), (255, 150, 40), (255, 240, 170))
    return K.finish(c)


def flurry():
    """Three arrows loosed in quick succession, streaking forward."""
    c = bg((50, 130, 90), (4, 20, 12), 0.45, 0.5, 0.72)
    sp = shape(lambda d: [d.rounded_rectangle(pts([(x0, y - 0.012), (x1, y + 0.012)]), radius=0.012 * W, fill=255)
                          for x0, x1, y in ((0.10, 0.38, 0.28), (0.06, 0.32, 0.52), (0.10, 0.36, 0.76))])
    K.fill(c, soften(faint(sp, 0.7), 2), (230, 255, 230, 255))
    for y, x in ((0.28, 0.28), (0.52, 0.20), (0.76, 0.26)):
        m = shape(lambda d, y=y, x=x: d.polygon(pts([
            (x, y - 0.015), (x + 0.42, y - 0.015), (x + 0.42, y - 0.045), (x + 0.56, y), (x + 0.42, y + 0.045),
            (x + 0.42, y + 0.015), (x, y + 0.015)]), fill=255))
        fl = shape(lambda d, y=y, x=x: [d.polygon(pts([(x - 0.02, y - 0.06), (x + 0.08, y - 0.06), (x + 0.12, y),
                                                       (x + 0.02, y)]), fill=255),
                                        d.polygon(pts([(x - 0.02, y + 0.06), (x + 0.08, y + 0.06), (x + 0.12, y),
                                                       (x + 0.02, y)]), fill=255)])
        solid(c, m, (255, 255, 240), (200, 200, 180), (200, 255, 200), 8, 1.2)
        K.fill(c, soften(fl), K.linear((255, 240, 200, 255), (220, 120, 60, 255), 90))
    return K.finish(c)


def foil():
    """A fencing foil turning a blow aside with a bright parry spark."""
    c = bg((130, 40, 100), (20, 4, 16), 0.5, 0.45, 0.72)
    slash = shape(lambda d: d.arc(pts([(0.06, 0.04), (0.94, 0.92)]), 205, 295, fill=255, width=int(0.05 * W)))
    K.glow(c, slash, (255, 120, 140, 255), 12, 1.3)
    K.fill(c, soften(slash), K.linear((255, 230, 230, 255), (255, 120, 140, 255), 0))
    blade = shape(lambda d: d.polygon(pts([(0.34, 0.62), (0.39, 0.67), (0.88, 0.14), (0.86, 0.12)]), fill=255))
    solid(c, blade, (255, 255, 255), (170, 180, 210), (240, 220, 255), 10, 1.3)
    cup = shape(lambda d: d.chord(pts([(0.20, 0.56), (0.48, 0.84)]), 135, 315, fill=255))
    solid(c, cup, (255, 236, 170), (190, 120, 40), (255, 220, 140), 8, 1.0)
    grip = shape(lambda d: d.line(pts([(0.30, 0.72), (0.16, 0.86)]), fill=255, width=int(0.045 * W)))
    solid(c, grip, (150, 70, 60), (70, 24, 20), None, sh=False)
    pm = ell_m(0.11, 0.83, 0.19, 0.91)
    K.fill(c, soften(pm), K.linear((255, 236, 170, 255), (190, 120, 40, 255), 90))
    spark = shape(lambda d: d.polygon(pts(star_pts(0.64, 0.36, 6, 0.17, 0.05, 0.2)), fill=255))
    K.glow(c, spark, (255, 230, 150, 255), 16, 1.7)
    K.fill(c, soften(spark), (255, 255, 240, 255))
    return K.finish(c)


def inundation():
    """A great curling wave: every blow drowns the foe deeper."""
    c = bg((20, 100, 160), (2, 12, 30), 0.5, 0.4, 0.74)
    crest = ImageChops.subtract(ell_m(0.14, 0.16, 0.84, 0.86), ell_m(0.34, 0.36, 0.78, 0.80))
    crest = ImageChops.multiply(crest, shape(lambda d: d.rectangle(pts([(0, 0), (1, 0.66)]), fill=255)))
    sea = shape(lambda d: d.polygon(pts([(0.0, 0.66)] + [(x, 0.64 + 0.03 * math.sin(x * 18)) for x in
                                                         (i / 30 for i in range(31))] + [(1.0, 1.0), (0.0, 1.0)]),
                                    fill=255))
    m = ImageChops.lighter(crest, sea)
    K.shadow(c, crest, 5, 8, 8, 160)
    K.glow(c, m, (120, 220, 255, 255), 16, 1.2)
    K.fill(c, soften(m), K.linear((230, 250, 255, 255), (20, 90, 200, 255), 300))
    foam = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255) for x, y, r in
                            ((0.76, 0.40, 0.035), (0.80, 0.48, 0.03), (0.70, 0.33, 0.03), (0.62, 0.28, 0.025),
                             (0.80, 0.56, 0.02))])
    K.glow(c, foam, (255, 255, 255, 255), 8, 1.2)
    K.fill(c, soften(foam), (255, 255, 255, 255))
    lines = shape(lambda d: [d.arc(pts([(0.22, 0.24), (0.76, 0.78)]), 170, 290, fill=255, width=int(0.014 * W))])
    K.fill(c, soften(faint(ImageChops.multiply(lines, crest), 0.7)), (255, 255, 255, 255))
    return K.finish(c)


def adloquium():
    """An open grimoire with a rousing golden flame rising from its pages."""
    c = bg((180, 100, 40), (30, 10, 4), 0.5, 0.45, 0.72)
    fl = shape(lambda d: [flame(d, 0.5, 0.62, 0.15, 0.48, 0.02), flame(d, 0.36, 0.62, 0.06, 0.24, -0.04),
                          flame(d, 0.64, 0.62, 0.06, 0.26, 0.04)])
    K.glow(c, fl, (255, 160, 40, 255), 22, 1.4)
    K.fill(c, soften(fl), K.linear((255, 240, 160, 255), (240, 90, 30, 255), 270))
    core = shape(lambda d: flame(d, 0.5, 0.60, 0.07, 0.26, 0.01))
    K.fill(c, soften(core), (255, 252, 230, 255))
    cover = shape(lambda d: d.polygon(pts([(0.10, 0.60), (0.5, 0.68), (0.90, 0.60), (0.92, 0.84), (0.5, 0.90),
                                           (0.08, 0.84)]), fill=255))
    solid(c, cover, (150, 60, 50), (80, 24, 20), None)
    pages = shape(lambda d: [d.polygon(pts([(0.5, 0.66), (0.14, 0.58), (0.14, 0.80), (0.5, 0.87)]), fill=255),
                             d.polygon(pts([(0.5, 0.66), (0.86, 0.58), (0.86, 0.80), (0.5, 0.87)]), fill=255)])
    K.fill(c, soften(pages), K.linear((255, 250, 235, 255), (220, 200, 170, 255), 90))
    txt = shape(lambda d: [d.line(pts([(x0, y), (x1, y + dy)]), fill=255, width=int(0.008 * W))
                           for x0, x1, dy in ((0.20, 0.44, 0.05), (0.56, 0.80, -0.05))
                           for y in (0.66, 0.71, 0.76)])
    K.fill(c, soften(faint(ImageChops.multiply(txt, pages), 0.5)), (120, 90, 70, 255))
    spine = shape(lambda d: d.line(pts([(0.5, 0.66), (0.5, 0.87)]), fill=255, width=int(0.01 * W)))
    K.fill(c, soften(faint(spine, 0.5)), (120, 90, 70, 255))
    return K.finish(c)


def reprisal():
    """A mirror-bright shield throwing an attack back as shafts of light."""
    c = bg((70, 60, 170), (8, 6, 30), 0.45, 0.45, 0.72)
    inc = shape(lambda d: d.polygon(pts([(0.06, 0.20), (0.10, 0.14), (0.44, 0.40), (0.40, 0.46)]), fill=255))
    K.glow(c, inc, (255, 70, 50, 255), 12, 1.4)
    K.fill(c, soften(inc), K.linear((255, 120, 90, 120), (255, 200, 170, 255), 30))
    refl = shape(lambda d: [d.polygon(pts([(0.52, 0.40), (0.92, 0.04 + k * 0.16), (0.94, 0.10 + k * 0.16)]), fill=255)
                            for k in range(3)])
    K.glow(c, refl, (255, 220, 120, 255), 12, 1.5)
    K.fill(c, soften(refl), (255, 250, 220, 255))
    m = shape(lambda d: GB.draw_shield(d, 0.44, 0.60, 0.80))
    solid(c, m, (250, 252, 255), (140, 150, 190), (200, 210, 255), 16, 1.3)
    inner = shape(lambda d: GB.draw_shield(d, 0.44, 0.60, 0.80, inset=0.18))
    K.fill(c, soften(inner), K.linear((230, 240, 255, 255), (80, 100, 200, 255), 120))
    sp = shape(lambda d: K.sparkle(d, 0.50, 0.42, 0.14, 0.2))
    K.glow(c, sp, (255, 240, 180, 255), 12, 1.6)
    K.fill(c, soften(sp), (255, 255, 255, 255))
    return K.finish(c)


# ---- tables -------------------------------------------------------------------------------------------------------
ICONS = {
    ('ma', 'Poisona'): cleanse,
    ('ma', 'Erase'): erase,
    ('ma', 'Esuna'): esuna,
    ('ma', 'Banish'): banish,
    ('ma', 'Banishga'): banishga,
    ('ma', 'Diaga'): diaga,
    ('ma', 'Protect'): lambda: protect_paint(False),
    ('ma', 'Protectra'): lambda: protect_paint(True),
    ('ma', 'Shell'): lambda: shell_paint(False),
    ('ma', 'Shellra'): lambda: shell_paint(True),
    ('ma', 'Blink'): blink,
    ('ma', 'Stoneskin'): stoneskin,
    ('ma', 'Aquaveil'): aquaveil,
    ('ma', 'Slow'): slow,
    ('ma', 'Slowga'): slowga,
    ('ma', 'Paralyze'): paralyze,
    ('ma', 'Paralyga'): paralyga,
    ('ma', 'Silence'): silence,
    ('ma', 'Silencega'): silencega,
    ('ma', 'Repose'): repose,
    ('ma', 'Hastega'): hastega,
    ('ma', 'Barfire'): bar_element,
    ('ma', 'Barfira'): bar_element_ra,
    ('ma', 'Barsleep'): bar_status,
    ('ma', 'Barsleepra'): bar_status_ra,
    ('ma', 'Recall-Jugner'): recall,
    ('ma', 'Teleport-Vahzl'): teleport,
    ('ma', 'Cura'): cura,
    ('ma', 'Full Cure'): full_cure,
    ('ma', 'Sacrifice'): sacrifice,
    ('ma', 'Arise'): arise,
    ('ma', 'Reraise'): reraise,
    ('ma', 'Auspice'): auspice,
    ('ma', 'Embrava'): embrava,
    ('ma', 'Crusade'): crusade,
    ('ma', 'Animus Augeo'): animus_augeo,
    ('ma', 'Animus Minuo'): animus_minuo,
    ('ma', 'Addle'): addle,
    ('ma', 'Invisible'): invisible,
    ('ma', 'Sneak'): sneak,
    ('ma', 'Deodorize'): deodorize,
    ('ma', 'Firestorm'): storm,
    ('ma', 'Enfire'): en_spell,
    ('ma', 'Gain-STR'): gain,
    ('ma', 'Boost-STR'): boost_stat,
    ('ma', 'Temper'): temper,
    ('ma', 'Flurry'): flurry,
    ('ma', 'Foil'): foil,
    ('ma', 'Inundation'): inundation,
    ('ma', 'Adloquium'): adloquium,
    ('ma', 'Reprisal'): reprisal,
}

COVERS = {}

_BAR_RA = {'Fire': 'Barfira', 'Blizzard': 'Barblizzara', 'Aero': 'Baraera', 'Stone': 'Barstonra',
           'Thunder': 'Barthundra', 'Water': 'Barwatera'}
_BARS_RA = {'sleep': 'Barsleepra', 'poison': 'Barpoisonra', 'paralyze': 'Barparalyzra', 'blind': 'Barblindra',
            'silence': 'Barsilencera', 'petrify': 'Barpetra', 'virus': 'Barvira', 'amnesia': 'Baramnesra'}

VARIANTS = {
    'Poisona': hues(290, AILMENT),
    'Barfire': hues(8, {'Bar' + k.lower(): v for k, v in BAR_ELEMENT.items()}),
    'Barfira': hues(8, {_BAR_RA[k]: v for k, v in BAR_ELEMENT.items()}),
    'Barsleep': hues(290, {'Bar' + k: v for k, v in BAR_STATUS.items()}),
    'Barsleepra': hues(290, {_BARS_RA[k]: v for k, v in BAR_STATUS.items()}),
    'Recall-Jugner': hues(130, {'Recall-Jugner': 130, 'Recall-Pashh': 190, 'Recall-Meriph': 40}),
    'Teleport-Vahzl': hues(205, {'Teleport-Holla': 50, 'Teleport-Dem': 330, 'Teleport-Mea': 280,
                                 'Teleport-Yhoat': 150, 'Teleport-Altep': 15, 'Teleport-Vahzl': 205}),
    'Firestorm': hues(8, STORM),
    'Enfire': hues(8, EN),
    'Gain-STR': hues(8, {'Gain-' + k: v for k, v in STAT.items()}),
    'Boost-STR': hues(8, {'Boost-' + k: v for k, v in STAT.items()}),
}
