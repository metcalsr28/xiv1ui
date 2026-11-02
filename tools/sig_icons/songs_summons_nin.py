"""Signature icons, round 2: bard songs, the remaining summons and the remaining ninjutsu.

Songs keep round 1's language (group_b: a note plus an effect symbol). Summons match group_c's portraits. Elemental
ninjutsu match group_c's Katon (an element rising from an open scroll).
"""
import math
import random

from PIL import ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_b as GB
import group_c as GC

W = K.W
p, pts, mask, shape, fill, glow, shadow, soften, radial, linear, sparkle, finish = (
    K.p, K.pts, K.mask, K.shape, K.fill, K.glow, K.shadow, K.soften, K.radial, K.linear, K.sparkle, K.finish)
xf, ell, stroke, arc = GB.xf, GB.ell, GC.stroke, GC.arc
lighter = ImageChops.lighter


# ---- shared helpers ---------------------------------------------------------------------------------------------------
def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return radial(c0 + (255,), c1 + (255,), cx, cy, r)


def stars(c, spec, halo=(220, 230, 255, 255)):
    GC.stars(c, spec, (255, 255, 255, 255), halo)


def motes(c, seed, n, box, rr, color, core=(255, 255, 255, 220), blur=5):
    GC.motes(c, seed, n, box, rr, color, core, blur)


CREAM = ((255, 252, 240, 255), (226, 214, 190, 255))


def song_note(c, x=0.32, y=0.78, s=0.82, flags=1, paint=None, halo=(255, 220, 140, 255), ang=0.0):
    """The bard's note in front of the effect symbol (gold by default), kept clear of the rim."""
    x, y = max(x, 0.31), min(y, 0.79)
    nt = shape(lambda d: GB.note(d, x, y, s, flags, ang))
    glow(c, nt, halo, 16, 1.4)
    shadow(c, nt, 4, 7, 7, 160)
    fill(c, soften(nt), paint if paint is not None else GB.gold())
    return nt


def cream_note(c, x=0.32, y=0.78, s=0.82, flags=1, halo=(255, 160, 120, 255)):
    """A pale note for hue-shifted families (gold would turn odd colours)."""
    return song_note(c, x, y, s, flags, linear(*CREAM, 90), halo)


def crystal_poly(cx, cy, w, h):
    return [(cx, cy - h), (cx + w, cy - h * 0.38), (cx + w * 0.82, cy + h * 0.52), (cx, cy + h),
            (cx - w * 0.82, cy + h * 0.52), (cx - w, cy - h * 0.38)]


def elem_crystal(c, cx, cy, w, h, light, dark, halo):
    """An FFXI elemental crystal: lit left face, shaded right face, a bright edge."""
    cr = shape(lambda d: d.polygon(pts(crystal_poly(cx, cy, w, h)), fill=255))
    glow(c, cr, halo, 22, 1.4)
    shadow(c, cr, 5, 8, 7, 150)
    fill(c, soften(cr), linear(light, dark, 90))
    right = shape(lambda d: d.polygon(pts([(cx, cy - h), (cx + w, cy - h * 0.38), (cx + w * 0.82, cy + h * 0.52),
                                           (cx, cy + h)]), fill=255))
    fill(c, soften(right).point(lambda v: int(v * 0.45)), (60, 10, 6, 255))
    edge = shape(lambda d: d.line(pts([(cx, cy - h), (cx, cy + h)]), fill=255, width=int(0.010 * W)))
    fill(c, soften(edge).point(lambda v: int(v * 0.7)), (255, 250, 230, 255))
    hi = shape(lambda d: d.polygon(pts([(cx - w * 0.75, cy - h * 0.30), (cx - w * 0.25, cy - h * 0.70),
                                        (cx - w * 0.30, cy - h * 0.05)]), fill=255))
    fill(c, soften(hi, 3).point(lambda v: int(v * 0.6)), (255, 255, 255, 255))
    return cr


def chevrons(c, x0, y0, color=(255, 255, 220, 255), halo=(255, 255, 180, 255), n=3, gap=0.12, size=0.20, w=0.05):
    ch = mask()
    d = ImageDraw.Draw(ch)
    for i in range(n):
        x = x0 + i * gap
        d.line(pts([(x, y0 - size), (x + size * 0.6, y0), (x, y0 + size)]), fill=110 + int(145 * i / max(1, n - 1)),
               width=int(w * W), joint='curve')
    glow(c, ch, halo, 10, 1.2)
    fill(c, soften(ch), color)


def reticle(c, cx, cy, r, color=(255, 240, 220, 255), halo=(255, 120, 80, 255)):
    ring = shape(lambda d: [d.ellipse(pts([(cx - r, cy - r), (cx + r, cy + r)]), outline=255, width=int(0.028 * W)),
                            d.ellipse(pts([(cx - r * 0.5, cy - r * 0.5), (cx + r * 0.5, cy + r * 0.5)]), outline=255,
                                      width=int(0.020 * W)),
                            d.rectangle(pts([(cx - 0.012, cy - r * 1.25), (cx + 0.012, cy - r * 0.62)]), fill=255),
                            d.rectangle(pts([(cx - 0.012, cy + r * 0.62), (cx + 0.012, cy + r * 1.25)]), fill=255),
                            d.rectangle(pts([(cx - r * 1.25, cy - 0.012), (cx - r * 0.62, cy + 0.012)]), fill=255),
                            d.rectangle(pts([(cx + r * 0.62, cy - 0.012), (cx + r * 1.25, cy + 0.012)]), fill=255)])
    glow(c, ring, halo, 10, 1.3)
    fill(c, soften(ring), color)


def hourglass(d, cx, cy, s):
    def q(seq):
        return pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.rounded_rectangle(q([(-0.24, -0.40), (0.24, -0.33)]), radius=0.02 * W * s, fill=255)
    d.rounded_rectangle(q([(-0.24, 0.33), (0.24, 0.40)]), radius=0.02 * W * s, fill=255)
    d.polygon(q([(-0.19, -0.33), (0.19, -0.33), (0.19, -0.26), (0.035, -0.02), (0.035, 0.02), (0.19, 0.26),
                 (0.19, 0.33), (-0.19, 0.33), (-0.19, 0.26), (-0.035, 0.02), (-0.035, -0.02), (-0.19, -0.26)]),
              fill=255)


def hourglass_sand(d, cx, cy, s):
    def q(seq):
        return pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.polygon(q([(-0.10, -0.14), (0.10, -0.14), (0.02, -0.03), (-0.02, -0.03)]), fill=255)   # upper sand
    d.polygon(q([(0.0, 0.08), (0.15, 0.30), (-0.15, 0.30)]), fill=255)                         # lower heap
    d.rectangle(q([(-0.008, -0.03), (0.008, 0.22)]), fill=255)                                  # falling stream


def leaf(d, cx, cy, L, wd, ang):
    seq = []
    for i in range(41):
        t = i / 40
        seq.append((t * L, -wd * math.sin(math.pi * t) ** 0.8))
    for i in range(40, -1, -1):
        t = i / 40
        seq.append((t * L, wd * math.sin(math.pi * t) ** 0.8))
    d.polygon(xf(seq, cx, cy, 1.0, ang), fill=255)


def rose(c, cx, cy, r, col=(240, 60, 110), dark=(120, 10, 50)):
    bloom = shape(lambda d: [d.ellipse(pts([(cx - r * math.cos(a) * 0.0 + math.cos(a) * r * 0.45 - r * 0.62,
                                             cy + math.sin(a) * r * 0.45 - r * 0.62),
                                            (cx + math.cos(a) * r * 0.45 + r * 0.62,
                                             cy + math.sin(a) * r * 0.45 + r * 0.62)]), fill=255)
                             for a in [math.pi * 2 * i / 5 - math.pi / 2 for i in range(5)]])
    glow(c, bloom, col + (255,), 16, 1.3)
    shadow(c, bloom, 4, 7, 7, 150)
    fill(c, soften(bloom), radial(tuple(min(255, v + 70) for v in col) + (255,), dark + (255,), cx - r * 0.2,
                                  cy - r * 0.3, r * 1.4))
    sw = mask()
    sd = ImageDraw.Draw(sw)
    for k in range(3):
        sp = arc(cx, cy, r * (0.22 + 0.22 * k), 200 + 70 * k, 470 + 70 * k, 30)
        sd.line(pts(sp), fill=255, width=int(0.012 * W))
    fill(c, soften(sw).point(lambda v: int(v * 0.6)), dark + (255,))


# ---- BRD: songs ---------------------------------------------------------------------------------------------------
def foe_requiem():
    """A skull in a pall of grave-smoke behind the note: the song of lingering death."""
    c = bg((110, 50, 140), (16, 4, 24))
    rnd = random.Random(14)
    smoke = mask()
    sd = ImageDraw.Draw(smoke)
    for _ in range(16):
        x, y, r = rnd.uniform(0.3, 0.9), rnd.uniform(0.15, 0.7), rnd.uniform(0.06, 0.12)
        sd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=110)
    fill(c, smoke.filter(ImageFilter.GaussianBlur(14)), (190, 255, 200, 255))
    sk = shape(lambda d: GB.skull(d, 0.62, 0.40, 0.95))
    glow(c, sk, (150, 255, 170, 255), 18, 1.2)
    shadow(c, sk, 4, 7, 7, 150)
    fill(c, soften(sk), linear((250, 246, 230, 255), (180, 170, 150, 255), 90))
    eyes = shape(lambda d: [d.polygon(xf(ell(-0.12, 0.02, 0.05, 0.05), 0.62, 0.40, 0.95), fill=255),
                            d.polygon(xf(ell(0.12, 0.02, 0.05, 0.05), 0.62, 0.40, 0.95), fill=255)])
    glow(c, eyes, (120, 255, 150, 255), 8, 1.6)
    fill(c, soften(eyes), (210, 255, 220, 255))
    song_note(c, 0.28, 0.82, 0.80, 1, halo=(170, 255, 190, 255))
    return finish(c)


def horde_lullaby():
    """A small moon over a scatter of notes: sleep for the whole pack."""
    c = bg((40, 110, 140), (2, 12, 26), 0.5, 0.40)
    motes(c, 41, 16, (0.10, 0.10, 0.90, 0.55), (0.004, 0.010), (200, 240, 255, 255))
    moon = shape(lambda d: GB.crescent(d, 0.36, 0.33, 0.21, (0.42, -0.30)))
    glow(c, moon, (220, 240, 200, 255), 18, 1.3)
    fill(c, soften(moon), linear((255, 252, 220, 255), (220, 200, 120, 255), 90))
    for x, y, s in ((0.70, 0.52, 0.48), (0.48, 0.80, 0.50), (0.80, 0.86, 0.42)):
        nt = shape(lambda d, x=x, y=y, s=s: GB.note(d, x, y, s, 1))
        glow(c, nt, (160, 230, 255, 255), 10, 1.3)
        shadow(c, nt, 3, 5, 5, 140)
        fill(c, soften(nt), linear((245, 252, 255, 255), (150, 210, 230, 255), 90))
    z = shape(lambda d: [d.line(pts([(0.56, 0.18), (0.66, 0.18), (0.56, 0.28), (0.66, 0.28)]), fill=255,
                                width=int(0.022 * W), joint='curve'),
                         d.line(pts([(0.70, 0.08), (0.76, 0.08), (0.70, 0.14), (0.76, 0.14)]), fill=255,
                                width=int(0.016 * W), joint='curve')])
    glow(c, z, (200, 240, 255, 255), 6)
    fill(c, soften(z), (240, 250, 255, 255))
    return finish(c)


def armys_paeon():
    """A note in front of a soft green cross of renewal, motes rising: regen."""
    c = bg((70, 160, 80), (6, 28, 10))
    motes(c, 52, 22, (0.15, 0.15, 0.88, 0.9), (0.007, 0.018), (170, 255, 170, 255), (235, 255, 230, 220))
    cr = shape(lambda d: [d.rounded_rectangle(pts([(0.54, 0.12), (0.72, 0.62)]), radius=0.04 * W, fill=255),
                          d.rounded_rectangle(pts([(0.38, 0.28), (0.88, 0.46)]), radius=0.04 * W, fill=255)])
    glow(c, cr, (140, 255, 150, 255), 26, 1.3)
    fill(c, soften(cr), linear((240, 255, 236, 255), (120, 220, 130, 255), 90))
    song_note(c, 0.28, 0.82, 0.82, 1, halo=(200, 255, 160, 255))
    return finish(c)


def knights_minne():
    """A note before a knight's shield: the song of defence."""
    c = bg((70, 100, 180), (6, 10, 36))
    sh = shape(lambda d: GB.draw_shield(d, 0.60, 0.44, 0.92))
    glow(c, sh, (170, 210, 255, 255), 18, 1.2)
    shadow(c, sh, 5, 8, 8, 160)
    fill(c, soften(sh), GB.metal())
    inner = shape(lambda d: GB.draw_shield(d, 0.60, 0.44, 0.92, inset=0.18))
    fill(c, soften(inner), linear((80, 120, 220, 255), (24, 40, 110, 255), 90))
    cross = shape(lambda d: [d.rectangle(pts([(0.585, 0.24), (0.615, 0.66)]), fill=255),
                             d.rectangle(pts([(0.47, 0.36), (0.73, 0.39)]), fill=255)])
    fill(c, soften(cross), (240, 210, 120, 255))
    song_note(c, 0.28, 0.82, 0.80, 1)
    return finish(c)


def madrigal(two=False):
    def paint():
        c = bg((200, 70, 90), (34, 6, 14)) if two else bg((200, 130, 50), (36, 18, 4))
        reticle(c, 0.60, 0.40, 0.24, halo=(255, 140, 90, 255))
        if two:
            sw = shape(lambda d: [GB.draw_sword(d, 0.60, 0.42, 0.86, 35, blade_w=0.09, guard_w=0.28),
                                  GB.draw_sword(d, 0.60, 0.42, 0.86, -35, blade_w=0.09, guard_w=0.28)])
        else:
            sw = shape(lambda d: GB.draw_sword(d, 0.60, 0.42, 0.90, 20, blade_w=0.10, guard_w=0.30))
        glow(c, sw, (255, 220, 190, 255), 12, 1.2)
        shadow(c, sw, 4, 7, 7, 150)
        fill(c, soften(sw), GB.metal((255, 255, 255, 255), (170, 166, 180, 255)))
        song_note(c, 0.26, 0.82, 0.80, 1)
        return finish(c)
    return paint


def prelude(bow=False):
    def paint():
        c = bg((150, 150, 40), (24, 26, 4)) if bow else bg((40, 150, 120), (2, 24, 20))
        reticle(c, 0.62, 0.38, 0.22, halo=(255, 240, 160, 255) if bow else (140, 255, 220, 255))
        if bow:
            b = shape(lambda d: d.polygon(pts(stroke(arc(0.40, 0.56, 0.42, -78, 8, 40), 0.045, 0.045)), fill=255))
            glow(c, b, (255, 230, 150, 255), 10, 1.2)
            shadow(c, b, 4, 7, 7, 150)
            fill(c, soften(b), linear((230, 170, 90, 255), (120, 70, 30, 255), 90))
            strg = shape(lambda d: d.line(pts([(0.49, 0.15), (0.82, 0.62)]), fill=255, width=int(0.008 * W)))
            fill(c, soften(strg), (255, 250, 230, 255))
            ar = shape(lambda d: GC.arrow(d, 0.40, 0.58, 0.80, 0.22))
        else:
            ar = shape(lambda d: GC.arrow(d, 0.24, 0.76, 0.74, 0.28))
            GC.streaks(c, [(0.10, 0.80, 0.30, 0.62), (0.18, 0.92, 0.36, 0.74)], (200, 255, 240, 255), 0.014, 150)
        glow(c, ar, (255, 255, 230, 255), 10, 1.2)
        shadow(c, ar, 4, 7, 6, 150)
        fill(c, soften(ar), linear((255, 255, 255, 255), (190, 200, 210, 255), 90))
        song_note(c, 0.24, 0.84, 0.74, 1)
        return finish(c)
    return paint


def mambo(dragon=False):
    def paint():
        if dragon:
            c = bg((50, 150, 150), (2, 24, 26))
            w = shape(lambda d: GC.wyvern(d, 0.62, 0.40, 1.0))
            glow(c, w, (140, 255, 230, 255), 14, 1.3)
            fill(c, soften(w), linear((150, 230, 220, 255), (40, 120, 120, 255), 90))
            ghost = (150, 255, 230, 255)
        else:
            c = bg((180, 120, 210), (26, 8, 40))
            sp = [(0.66 + math.cos(a) * r, 0.34 + math.sin(a) * r)
                  for a, r in [(math.radians(-150 + 540 * i / 50), 0.24 * (1 - i / 60)) for i in range(51)]]
            horn = shape(lambda d: d.polygon(pts(stroke(sp, 0.12, 0.03)), fill=255))
            glow(c, horn, (255, 220, 255, 255), 12, 1.2)
            shadow(c, horn, 4, 7, 6, 150)
            fill(c, soften(horn), linear((255, 244, 220, 255), (190, 160, 130, 255), 90))
            ridges = shape(lambda d: [d.line(pts([sp[i], sp[i + 1]]), fill=255, width=int(0.10 * W))
                                      for i in range(2, 44, 6)])
            fill(c, soften(ImageChops.multiply(ridges, horn)).point(lambda v: int(v * 0.25)), (110, 80, 60, 255))
            ghost = (255, 190, 255, 255)
        # after-images: the note has already danced aside
        for dx, a in ((-0.22, 90), (-0.11, 160)):
            g = shape(lambda d, dx=dx: GB.note(d, 0.54 + dx, 0.78, 0.78, 1, -12))
            fill(c, soften(g, 2).point(lambda v, a=a: int(v * a / 255)), ghost)
        arcs = shape(lambda d: [d.polygon(pts(stroke(arc(0.58, 0.60, r, 150, 230, 20), 0.004, 0.024)), fill=255)
                                for r in (0.34, 0.42)])
        fill(c, soften(arcs), (255, 255, 255, 255))
        song_note(c, 0.54, 0.78, 0.78, 1, ang=-12)
        return finish(c)
    return paint


def fowl_aubade():
    """Dawn breaking over the horizon behind the note: the song that wards off sleep."""
    c = bg((240, 150, 90), (50, 16, 40), 0.5, 0.75, 0.8)
    GB.rays(c, 0.5, 0.70, 14, 0.7, (255, 240, 190, 255), 120, 0.06, 6)
    sun = shape(lambda d: d.ellipse(pts([(0.26, 0.46), (0.74, 0.94)]), fill=255))
    sun = ImageChops.subtract(sun, shape(lambda d: d.rectangle(pts([(0, 0.70), (1, 1)]), fill=255)))
    glow(c, sun, (255, 200, 120, 255), 26, 1.4)
    fill(c, soften(sun), linear((255, 250, 210, 255), (255, 170, 70, 255), 90))
    ground = shape(lambda d: d.rectangle(pts([(0, 0.70), (1, 1)]), fill=255))
    fill(c, soften(ground, 3), linear((110, 40, 70, 255), (30, 8, 26, 255), 90))
    line = shape(lambda d: d.line(pts([(0.02, 0.70), (0.98, 0.70)]), fill=255, width=int(0.010 * W)))
    glow(c, line, (255, 220, 160, 255), 6)
    fill(c, soften(line), (255, 240, 200, 255))
    song_note(c, 0.56, 0.62, 0.66, 1, paint=linear((255, 255, 255, 255), (255, 214, 160, 255), 90),
              halo=(255, 180, 100, 255))
    return finish(c)


def herb_pastoral():
    """A note under a broad green herb leaf: the song that wards off poison."""
    c = bg((120, 170, 60), (12, 30, 6))
    lf = shape(lambda d: [leaf(d, 0.30, 0.66, 0.62, 0.17, -50), leaf(d, 0.44, 0.70, 0.40, 0.10, -10)])
    glow(c, lf, (200, 255, 150, 255), 16, 1.2)
    shadow(c, lf, 4, 7, 7, 150)
    fill(c, soften(lf), linear((190, 240, 120, 255), (50, 130, 40, 255), 90))
    vein = shape(lambda d: [d.line(xf([(0, 0), (0.58, 0)], 0.30, 0.66, 1.0, -50), fill=255, width=int(0.010 * W)),
                            d.line(xf([(0, 0), (0.36, 0)], 0.44, 0.70, 1.0, -10), fill=255, width=int(0.008 * W))])
    fill(c, soften(vein).point(lambda v: int(v * 0.6)), (230, 255, 200, 255))
    song_note(c, 0.30, 0.84, 0.70, 1, halo=(220, 255, 160, 255))
    return finish(c)


def chocobo_head(d, cx, cy, s):
    def q(seq):
        return pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.ellipse(q([(-0.18, -0.24), (0.14, 0.06)]), fill=255)                                         # head
    d.polygon(q([(-0.12, -0.02), (0.10, -0.02), (0.14, 0.40), (-0.16, 0.40)]), fill=255)            # neck
    d.polygon(q([(0.08, -0.16), (0.34, -0.08), (0.36, -0.03), (0.10, -0.02)]), fill=255)            # beak
    d.polygon(q([(-0.14, -0.20), (-0.30, -0.42), (-0.06, -0.24)]), fill=255)                        # crest
    d.polygon(q([(-0.04, -0.23), (-0.06, -0.46), (0.06, -0.22)]), fill=255)
    d.polygon(q([(-0.18, -0.12), (-0.40, -0.20), (-0.17, -0.04)]), fill=255)


def chocobo_hum():
    """A chocobo humming along: its head in profile beside the note."""
    c = bg((90, 160, 200), (6, 22, 40))
    ch = shape(lambda d: chocobo_head(d, 0.60, 0.44, 0.95))
    glow(c, ch, (255, 240, 150, 255), 16, 1.3)
    shadow(c, ch, 5, 8, 7, 150)
    fill(c, soften(ch), linear((255, 236, 120, 255), (230, 160, 30, 255), 90))
    beak = shape(lambda d: d.polygon(xf([(0.08, -0.16), (0.34, -0.08), (0.36, -0.03), (0.10, -0.02)], 0.60, 0.44,
                                        0.95), fill=255))
    fill(c, soften(beak), (240, 140, 40, 255))
    eye = shape(lambda d: d.ellipse(pts([(0.62, 0.30), (0.67, 0.35)]), fill=255))
    fill(c, soften(eye, 0.8), (30, 20, 10, 255))
    song_note(c, 0.24, 0.84, 0.70, 1, paint=linear((255, 255, 255, 255), (200, 225, 245, 255), 90),
              halo=(200, 235, 255, 255))
    return finish(c)


def shining_fantasia():
    """A radiant open eye behind the note: the song that wards off blindness."""
    c = bg((230, 190, 80), (50, 30, 4))
    GB.rays(c, 0.58, 0.40, 16, 0.7, (255, 255, 230, 255), 110, 0.05, 6)
    eye = shape(lambda d: GC.eye_shape(d, 0.58, 0.40, 0.30, 0.17))
    glow(c, eye, (255, 250, 200, 255), 22, 1.4)
    fill(c, soften(eye), linear((255, 255, 250, 255), (240, 225, 180, 255), 90))
    iris = shape(lambda d: d.ellipse(pts([(0.48, 0.30), (0.68, 0.50)]), fill=255))
    fill(c, soften(iris), radial((120, 200, 255, 255), (20, 70, 170, 255), 0.58, 0.40, 0.10))
    pupil = shape(lambda d: d.ellipse(pts([(0.555, 0.37), (0.605, 0.43)]), fill=255))
    fill(c, soften(pupil), (10, 14, 30, 255))
    hi = shape(lambda d: d.ellipse(pts([(0.59, 0.34), (0.625, 0.375)]), fill=255))
    fill(c, soften(hi), (255, 255, 255, 255))
    song_note(c, 0.26, 0.84, 0.76, 1, halo=(255, 240, 160, 255))
    stars(c, [(0.84, 0.70, 0.08)], (255, 240, 170, 255))
    return finish(c)


def scops_operetta():
    """A minstrel's lyre and a note: the song that keeps voices free of silence."""
    c = bg((100, 80, 190), (10, 6, 36))
    frame_ = shape(lambda d: [d.polygon(pts(stroke([(0.44, 0.70), (0.38, 0.50), (0.42, 0.30), (0.50, 0.18),
                                                    (0.46, 0.10)], 0.055, 0.03)), fill=255),
                              d.polygon(pts(stroke([(0.80, 0.70), (0.86, 0.50), (0.82, 0.30), (0.74, 0.18),
                                                    (0.78, 0.10)], 0.055, 0.03)), fill=255),
                              d.rounded_rectangle(pts([(0.40, 0.66), (0.84, 0.76)]), radius=0.03 * W, fill=255),
                              d.rounded_rectangle(pts([(0.44, 0.22), (0.80, 0.27)]), radius=0.02 * W, fill=255)])
    glow(c, frame_, (255, 220, 140, 255), 14, 1.3)
    shadow(c, frame_, 4, 7, 7, 150)
    fill(c, soften(frame_), GB.gold())
    strings = shape(lambda d: [d.line(pts([(x, 0.27), (x, 0.66)]), fill=255, width=int(0.008 * W))
                               for x in (0.54, 0.60, 0.66, 0.72)])
    glow(c, strings, (220, 210, 255, 255), 6)
    fill(c, soften(strings), (250, 248, 255, 255))
    song_note(c, 0.20, 0.84, 0.72, 1, paint=linear((255, 255, 255, 255), (200, 196, 240, 255), 90),
              halo=(200, 180, 255, 255))
    return finish(c)


def puppets_operetta():
    """A note dangling from a marionette's cross-bar like a puppet."""
    c = bg((190, 100, 60), (34, 12, 6))
    bar = shape(lambda d: [d.polygon(xf([(-0.28, -0.03), (0.28, -0.03), (0.28, 0.03), (-0.28, 0.03)], 0.5, 0.24, 1.0,
                                        -8), fill=255),
                           d.polygon(xf([(-0.03, -0.12), (0.03, -0.12), (0.03, 0.12), (-0.03, 0.12)], 0.5, 0.24, 1.0,
                                        -8), fill=255)])
    shadow(c, bar, 4, 7, 6, 150)
    fill(c, soften(bar), linear((230, 170, 110, 255), (120, 70, 30, 255), 90))
    strings = shape(lambda d: [d.line(pts([(0.24, 0.28), (0.34, 0.76)]), fill=255, width=int(0.010 * W)),
                               d.line(pts([(0.50, 0.36), (0.46, 0.27)]), fill=255, width=int(0.010 * W)),
                               d.line(pts([(0.76, 0.21), (0.66, 0.50)]), fill=255, width=int(0.010 * W))])
    glow(c, strings, (255, 240, 220, 255), 5)
    fill(c, soften(strings), (255, 250, 236, 255))
    song_note(c, 0.36, 0.80, 0.86, 1, halo=(255, 220, 160, 255), ang=8)
    stars(c, [(0.82, 0.72, 0.07)], (255, 220, 170, 255))
    return finish(c)


def jesters_operetta():
    """A three-pointed jester's cap with bells, and a note."""
    c = bg((180, 50, 110), (30, 4, 22))
    hat = shape(lambda d: [d.polygon(pts(stroke([(0.42, 0.52), (0.36, 0.34), (0.22, 0.24), (0.14, 0.30)], 0.12,
                                                0.02)), fill=255),
                           d.polygon(pts(stroke([(0.60, 0.52), (0.60, 0.30), (0.66, 0.14), (0.74, 0.12)], 0.12,
                                                0.02)), fill=255),
                           d.polygon(pts(stroke([(0.74, 0.54), (0.82, 0.38), (0.92, 0.36), (0.94, 0.44)], 0.12,
                                                0.02)), fill=255),
                           d.ellipse(pts([(0.34, 0.42), (0.86, 0.64)]), fill=255)])
    glow(c, hat, (255, 180, 220, 255), 14, 1.2)
    shadow(c, hat, 4, 7, 7, 150)
    fill(c, soften(hat), linear((255, 120, 170, 255), (150, 20, 80, 255), 0))
    right = ImageChops.multiply(hat, shape(lambda d: d.rectangle(pts([(0.61, 0), (1, 1)]), fill=255)))
    fill(c, soften(right), linear((140, 120, 255, 255), (50, 30, 160, 255), 0))
    band = shape(lambda d: d.rounded_rectangle(pts([(0.34, 0.56), (0.86, 0.64)]), radius=0.03 * W, fill=255))
    fill(c, soften(band), GB.gold())
    bells = shape(lambda d: [d.ellipse(pts([(x - 0.04, y - 0.04), (x + 0.04, y + 0.04)]), fill=255)
                             for x, y in ((0.14, 0.31), (0.75, 0.12), (0.95, 0.45))])
    glow(c, bells, (255, 230, 140, 255), 8, 1.4)
    fill(c, soften(bells), GB.gold())
    song_note(c, 0.24, 0.86, 0.66, 1)
    return finish(c)


def gold_capriccio():
    """A golden note bursting out of a cracking stone tablet: the song that wards off petrification."""
    c = bg((140, 120, 90), (24, 18, 12))
    slab = shape(lambda d: d.rounded_rectangle(pts([(0.30, 0.12), (0.86, 0.70)]), radius=0.05 * W, fill=255))
    bite = shape(lambda d: d.polygon(pts([(0.20, 0.40), (0.42, 0.36), (0.52, 0.50), (0.48, 0.80), (0.20, 0.80)]),
                                     fill=255))
    slab = ImageChops.subtract(slab, bite)
    shadow(c, slab, 5, 8, 7, 170)
    fill(c, soften(slab), linear((214, 208, 196, 255), (120, 112, 100, 255), 90))
    cracks = shape(lambda d: [d.line(pts([(0.42, 0.36), (0.56, 0.30), (0.62, 0.18), (0.70, 0.12)]), fill=255,
                                     width=int(0.014 * W), joint='curve'),
                              d.line(pts([(0.52, 0.50), (0.66, 0.48), (0.74, 0.58), (0.86, 0.56)]), fill=255,
                                     width=int(0.014 * W), joint='curve'),
                              d.line(pts([(0.62, 0.30), (0.74, 0.36)]), fill=255, width=int(0.010 * W))])
    glow(c, cracks, (255, 220, 120, 255), 6, 1.4)
    fill(c, soften(ImageChops.multiply(cracks, slab.filter(ImageFilter.MaxFilter(5)))), (255, 230, 150, 255))
    frags = shape(lambda d: [d.polygon(pts([(x, y), (x + s, y - s * 0.4), (x + s * 0.7, y + s * 0.8)]), fill=255)
                             for x, y, s in ((0.18, 0.30, 0.07), (0.12, 0.50, 0.05), (0.24, 0.18, 0.04),
                                             (0.54, 0.84, 0.05))])
    shadow(c, frags, 3, 5, 5, 150)
    fill(c, soften(frags), linear((200, 194, 182, 255), (110, 104, 94, 255), 90))
    GB.rays(c, 0.36, 0.62, 10, 0.4, (255, 230, 150, 255), 110, 0.07, 6, 0.4)
    nt = song_note(c, 0.36, 0.78, 0.84, 1, halo=(255, 220, 110, 255))
    glow(c, nt, (255, 230, 120, 255), 26, 0.7)
    return finish(c)


def devotee_serenade():
    """A heart sealed in a warding ring: the song that wards off charm."""
    c = bg((200, 80, 120), (34, 6, 20))
    ring = shape(lambda d: d.ellipse(pts([(0.34, 0.16), (0.88, 0.70)]), outline=255, width=int(0.035 * W)))
    glow(c, ring, (200, 230, 255, 255), 14, 1.4)
    fill(c, soften(ring), linear((255, 255, 255, 255), (190, 220, 255, 255), 90))
    ht = shape(lambda d: GB.heart(d, 0.61, 0.43, 0.46))
    glow(c, ht, (255, 140, 190, 255), 16, 1.3)
    shadow(c, ht, 4, 6, 6, 150)
    fill(c, soften(ht), linear((255, 190, 215, 255), (210, 30, 100, 255), 90))
    song_note(c, 0.24, 0.84, 0.74, 1)
    return finish(c)


def warding_round():
    """A note at the heart of a turning ring of ward-marks: the song that wards off curses."""
    c = bg((90, 70, 170), (10, 6, 34), 0.5, 0.5)
    rg = mask()
    rd = ImageDraw.Draw(rg)
    rd.ellipse(pts([(0.12, 0.12), (0.88, 0.88)]), outline=255, width=int(0.022 * W))
    for i in range(8):
        a = math.pi * 2 * i / 8
        x, y = 0.5 + math.cos(a) * 0.38, 0.5 + math.sin(a) * 0.38
        sparkle(rd, x, y, 0.06)
    for i in range(3):
        sp = arc(0.5, 0.5, 0.29, i * 120 + 10, i * 120 + 90, 20)
        rd.polygon(pts(stroke(sp, 0.035, 0.005)), fill=255)
    glow(c, rg, (200, 170, 255, 255), 14, 1.5)
    fill(c, soften(rg), (245, 238, 255, 255))
    song_note(c, 0.43, 0.70, 0.62, 1, halo=(220, 200, 255, 255))
    return finish(c)


def goblin_gavotte():
    """A chain link snapping apart behind the note: the song that wards off bind."""
    c = bg((150, 130, 60), (26, 22, 4))

    def link(d, cx, cy, ang, rx=0.15, ry=0.085, w=0.05, gap=0.0):
        L, f = GC.frame(cx, cy, cx + math.cos(math.radians(ang)), cy + math.sin(math.radians(ang)))
        n = 60
        a0 = gap
        ring = [f(math.cos(t) * rx, math.sin(t) * ry)
                for t in [a0 + (math.pi * 2 - 2 * gap) * i / n for i in range(n + 1)]]
        d.polygon(pts(stroke(ring, w, w)), fill=255)
    lk = shape(lambda d: [link(d, 0.50, 0.40, -30, gap=0.35), link(d, 0.78, 0.22, -30, gap=0.0),
                          link(d, 0.30, 0.58, -30, gap=0.0)])
    glow(c, lk, (255, 240, 180, 255), 12, 1.1)
    shadow(c, lk, 4, 7, 7, 160)
    fill(c, soften(lk), GB.metal((240, 240, 236, 255), (120, 120, 120, 255)))
    burst = mask()
    bd = ImageDraw.Draw(burst)
    star = []
    for i in range(16):
        a = math.pi * i / 8
        r = 0.12 if i % 2 == 0 else 0.04
        star.append((0.63 + math.cos(a) * r, 0.36 + math.sin(a) * r))
    bd.polygon(pts(star), fill=255)
    glow(c, burst, (255, 220, 120, 255), 10, 1.5)
    fill(c, soften(burst), (255, 250, 220, 255))
    song_note(c, 0.24, 0.86, 0.72, 1)
    return finish(c)


def cactuar(d, cx, cy, s):
    def q(seq):
        return pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.rounded_rectangle(q([(-0.11, -0.36), (0.11, 0.18)]), radius=0.11 * W * s, fill=255)        # body
    d.polygon(q(stroke([(-0.08, -0.08), (-0.20, -0.10), (-0.28, -0.24)], 0.08, 0.06)), fill=255)  # arm up
    d.polygon(q(stroke([(0.08, -0.02), (0.20, 0.02), (0.28, 0.14)], 0.08, 0.06)), fill=255)       # arm down
    d.polygon(q(stroke([(-0.05, 0.14), (-0.12, 0.30), (-0.20, 0.36)], 0.08, 0.06)), fill=255)     # legs
    d.polygon(q(stroke([(0.05, 0.14), (0.14, 0.26), (0.16, 0.38)], 0.08, 0.06)), fill=255)


def cactuar_fugue():
    """A cactuar caught mid-dance beside the note."""
    c = bg((230, 180, 90), (50, 24, 6), 0.5, 0.6)
    ct = shape(lambda d: cactuar(d, 0.62, 0.46, 1.0))
    glow(c, ct, (220, 255, 160, 255), 14, 1.3)
    shadow(c, ct, 5, 8, 7, 150)
    fill(c, soften(ct), linear((170, 230, 110, 255), (50, 130, 40, 255), 0))
    face = shape(lambda d: [d.ellipse(pts([(0.585, 0.18), (0.61, 0.22)]), fill=255),
                            d.ellipse(pts([(0.635, 0.18), (0.66, 0.22)]), fill=255),
                            d.ellipse(pts([(0.605, 0.25), (0.64, 0.31)]), fill=255)])
    fill(c, soften(face, 0.8), (30, 50, 20, 255))
    song_note(c, 0.22, 0.84, 0.70, 1, paint=linear((255, 255, 255, 255), (255, 220, 170, 255), 90),
              halo=(255, 200, 120, 255))
    return finish(c)


def honor_march():
    """A crowned march: chevrons under a golden crown, the note leading."""
    c = bg((130, 60, 180), (18, 4, 34))
    chevrons(c, 0.50, 0.58, (255, 240, 255, 255), (230, 180, 255, 255), size=0.16)
    crown = shape(lambda d: d.polygon(pts([(0.46, 0.34), (0.44, 0.14), (0.53, 0.24), (0.60, 0.08), (0.67, 0.24),
                                           (0.76, 0.14), (0.74, 0.34)]), fill=255))
    glow(c, crown, (255, 220, 120, 255), 14, 1.4)
    shadow(c, crown, 3, 6, 6, 150)
    fill(c, soften(crown), GB.gold())
    gems = shape(lambda d: [d.ellipse(pts([(x - 0.018, 0.27), (x + 0.018, 0.306)]), fill=255)
                            for x in (0.52, 0.60, 0.68)])
    fill(c, soften(gems, 0.8), (220, 30, 60, 255))
    song_note(c, 0.26, 0.84, 0.82, 1)
    return finish(c)


def victory_march():
    """A march ringed in a victor's laurel: the strongest haste song."""
    c = bg((210, 90, 40), (40, 10, 4))

    def laurel(d):
        cx, cy, R = 0.56, 0.46, 0.34
        for sx in (-1, 1):
            for i in range(7):
                a = math.radians(90 + sx * (25 + 115 * i / 6))
                x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
                leaf(d, x, y, 0.12, 0.035, math.degrees(a) + sx * 90 - sx * 25)
            a0, a1 = (90 - 140, 90 - 20) if sx < 0 else (110, 230)
            d.line(pts(arc(cx, cy, R, a0, a1, 30)), fill=255, width=int(0.012 * W))
    lr = shape(laurel)
    lr = ImageChops.subtract(lr, shape(lambda d: d.rectangle(pts([(0, 0), (1, 0.12)]), fill=255)))
    glow(c, lr, (255, 220, 120, 255), 10, 1.2)
    fill(c, soften(lr), GB.gold())
    chevrons(c, 0.50, 0.44, size=0.15, gap=0.11)
    song_note(c, 0.26, 0.84, 0.82, 1, paint=linear((255, 255, 255, 255), (255, 210, 160, 255), 90))
    return finish(c)


def aria_of_passion():
    """A heart wreathed in flame behind the note: the song of passion."""
    c = bg((200, 40, 80), (34, 2, 14))

    def flame(d, cx, base, w, h, lean=0.0):
        left, right = [], []
        for i in range(41):
            t = i / 40
            half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
            x = cx + lean * t * t
            left.append((x - half, base - h * t))
            right.append((x + half, base - h * t))
        d.polygon(pts(left + right[::-1]), fill=255)
    fl = shape(lambda d: [flame(d, 0.60, 0.70, 0.26, 0.66, 0.02), flame(d, 0.42, 0.66, 0.10, 0.36, -0.06),
                          flame(d, 0.80, 0.66, 0.10, 0.40, 0.06)])
    glow(c, fl, (255, 120, 60, 255), 22, 1.3)
    fill(c, soften(fl), linear((255, 220, 120, 255), (240, 70, 40, 255), 270))
    ht = shape(lambda d: GB.heart(d, 0.60, 0.50, 0.50))
    shadow(c, ht, 4, 6, 6, 150)
    fill(c, soften(ht), linear((255, 150, 170, 255), (190, 10, 50, 255), 90))
    shine = shape(lambda d: d.ellipse(pts([(0.50, 0.42), (0.56, 0.47)]), fill=255))
    fill(c, soften(shine, 4), (255, 255, 255, 255))
    song_note(c, 0.26, 0.84, 0.76, 1)
    return finish(c)


def elegy(level):
    """An hourglass behind the note (slow). Battlefield plain, Carnage bloodied, Massacre with a skull."""
    cols = {1: ((120, 130, 80), (20, 22, 8)), 2: ((180, 50, 50), (30, 4, 6)), 3: ((100, 40, 120), (14, 4, 20))}

    def paint():
        c = bg(*cols[level])
        hg = shape(lambda d: hourglass(d, 0.62, 0.42, 0.90))
        glow(c, hg, (255, 230, 170, 255), 14, 1.2)
        shadow(c, hg, 5, 8, 7, 160)
        glass = shape(lambda d: d.polygon(xf([(-0.19, -0.33), (0.19, -0.33), (0.19, -0.26), (0.035, -0.02),
                                              (0.035, 0.02), (0.19, 0.26), (0.19, 0.33), (-0.19, 0.33),
                                              (-0.19, 0.26), (-0.035, 0.02), (-0.035, -0.02), (-0.19, -0.26)],
                                             0.62, 0.42, 0.90), fill=255))
        fill(c, soften(glass), linear((210, 230, 240, 200), (120, 150, 170, 200), 0))
        caps = ImageChops.subtract(hg, glass)
        fill(c, soften(caps), linear((220, 160, 90, 255), (110, 60, 26, 255), 90))
        sand = shape(lambda d: hourglass_sand(d, 0.62, 0.42, 0.90))
        sand_col = (200, 30, 40, 255) if level == 2 else (255, 220, 140, 255)
        fill(c, soften(sand), sand_col)
        if level == 3:
            sk = shape(lambda d: GB.skull(d, 0.62, 0.58, 0.32))
            fill(c, soften(sk), (250, 245, 230, 255))
        if level == 2:
            drops = shape(lambda d: [GB.heart_drop(d, 0.82, 0.70, 0.03), GB.heart_drop(d, 0.88, 0.80, 0.022)])
            glow(c, drops, (255, 60, 60, 255), 6, 1.2)
            fill(c, soften(drops), (230, 40, 50, 255))
        song_note(c, 0.26, 0.84, 0.76, 1)
        return finish(c)
    return paint


def magic_finale():
    """A ward bubble bursting into shards behind the note: the song that dispels."""
    c = bg((60, 140, 190), (4, 16, 36))
    rnd = random.Random(61)
    shards = mask()
    sd = ImageDraw.Draw(shards)
    for i in range(10):
        a = math.pi * 2 * i / 10 + rnd.uniform(-0.15, 0.15)
        r0, r1 = rnd.uniform(0.24, 0.28), rnd.uniform(0.36, 0.44)
        L, f = GC.frame(0.58, 0.42, 0.58 + math.cos(a), 0.42 + math.sin(a))
        sd.polygon(pts([f(r0, -0.05), f(r1, -0.02), f(r1 + 0.03, 0.03), f(r0 + 0.02, 0.05)]), fill=255)
    glow(c, shards, (160, 230, 255, 255), 12, 1.4)
    fill(c, soften(shards), linear((240, 252, 255, 255), (130, 200, 240, 255), 90))
    ring = shape(lambda d: d.ellipse(pts([(0.40, 0.24), (0.76, 0.60)]), outline=255, width=int(0.016 * W)))
    fill(c, soften(ring, 3).point(lambda v: int(v * 0.5)), (200, 240, 255, 255))
    GB.rays(c, 0.58, 0.42, 10, 0.32, (255, 255, 255, 255), 140, 0.05, 4, 0.3)
    song_note(c, 0.26, 0.84, 0.76, 1)
    return finish(c)


def goddess_hymnus():
    """A note borne on angel wings under a halo: the song of reraise."""
    c = bg((230, 200, 140), (60, 40, 30), 0.5, 0.40)
    GB.rays(c, 0.5, 0.42, 16, 0.7, (255, 250, 220, 255), 100, 0.05, 8)

    def wing(d, side):
        for i in range(5):
            t = i / 4
            ang = math.radians(-15 - 45 * t) if side > 0 else math.radians(195 + 45 * t)
            length = 0.36 - 0.06 * t
            bx, by = 0.5 + side * 0.10, 0.56
            ex, ey = bx + math.cos(ang) * length, by + math.sin(ang) * length
            nx, ny = -math.sin(ang) * 0.045, math.cos(ang) * 0.045
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    wings = shape(lambda d: [wing(d, 1), wing(d, -1)])
    glow(c, wings, (255, 255, 230, 255), 14)
    fill(c, soften(wings), linear((255, 255, 252, 255), (230, 214, 170, 255), 90))
    halo = shape(lambda d: d.ellipse(pts([(0.38, 0.10), (0.62, 0.20)]), outline=255, width=int(0.028 * W)))
    glow(c, halo, (255, 230, 140, 255), 10, 1.3)
    fill(c, soften(halo), (255, 240, 170, 255))
    song_note(c, 0.44, 0.80, 0.74, 1, halo=(255, 250, 200, 255))
    return finish(c)


def chocobo_mazurka():
    """A chocobo feather racing along speed lines beside the note: movement speed."""
    c = bg((80, 170, 120), (6, 30, 16))
    GC.streaks(c, [(0.06, 0.30, 0.40, 0.30), (0.02, 0.46, 0.36, 0.46), (0.10, 0.62, 0.40, 0.62)],
               (230, 255, 220, 255), 0.02, 170, 4)
    fe = shape(lambda d: [leaf(d, 0.34, 0.70, 0.62, 0.12, -48)])
    glow(c, fe, (255, 240, 140, 255), 14, 1.3)
    shadow(c, fe, 4, 7, 7, 150)
    fill(c, soften(fe), linear((255, 244, 150, 255), (230, 160, 30, 255), 90))
    barbs = shape(lambda d: [d.line(xf([(t, 0), (t + 0.06, s * 0.09)], 0.34, 0.70, 1.0, -48), fill=255,
                                    width=int(0.006 * W)) for t in (0.14, 0.24, 0.34, 0.44) for s in (-1, 1)] +
                  [d.line(xf([(-0.06, 0), (0.56, 0)], 0.34, 0.70, 1.0, -48), fill=255, width=int(0.012 * W))])
    fill(c, soften(barbs).point(lambda v: int(v * 0.6)), (170, 100, 20, 255))
    song_note(c, 0.22, 0.86, 0.66, 1, paint=linear((255, 255, 255, 255), (200, 240, 210, 255), 90),
              halo=(200, 255, 210, 255))
    return finish(c)


def raptor_mazurka():
    """Raptor claw-tracks dashing off behind the note: the faster mount song."""
    c = bg((170, 90, 40), (28, 8, 2))
    GC.streaks(c, [(0.06, 0.30, 0.34, 0.30), (0.02, 0.42, 0.30, 0.42), (0.10, 0.54, 0.32, 0.54)],
               (255, 230, 200, 255), 0.02, 150, 4)

    def track(d, cx, cy, s, ang):
        for a in (-38, 0, 38):
            d.polygon(xf(stroke([(0, -0.05), (0.0, -0.30)], 0.075, 0.02), cx, cy, s, ang + a), fill=255)
        d.polygon(xf(ell(0, 0.035, 0.055, 0.05), cx, cy, s, ang), fill=255)
    tr = shape(lambda d: [track(d, 0.60, 0.56, 1.25, 40), track(d, 0.80, 0.27, 0.75, 40)])
    shadow(c, tr, 4, 7, 6, 200)
    glow(c, tr, (170, 255, 140, 255), 10, 1.0)
    fill(c, soften(tr), linear((235, 255, 215, 255), (110, 210, 90, 255), 90))
    song_note(c, 0.22, 0.86, 0.66, 1)
    return finish(c)


def maidens_virelai():
    """A rose offered with the note: the song that charms a foe."""
    c = bg((220, 110, 170), (40, 6, 30))
    stem = shape(lambda d: [d.polygon(pts(stroke([(0.60, 0.42), (0.62, 0.62), (0.70, 0.86)], 0.03, 0.025)),
                                      fill=255), leaf(d, 0.64, 0.66, 0.18, 0.05, 20)])
    fill(c, soften(stem), linear((120, 200, 90, 255), (30, 100, 40, 255), 90))
    rose(c, 0.60, 0.34, 0.15)
    song_note(c, 0.24, 0.84, 0.76, 1)
    motes(c, 71, 10, (0.12, 0.12, 0.88, 0.6), (0.006, 0.012), (255, 170, 210, 255))
    return finish(c)


def foe_sirvente():
    """A war-banner raised behind the note: the knight's song that holds the foe's attention."""
    c = bg((200, 70, 40), (36, 6, 4))
    pole = shape(lambda d: d.polygon(pts([(0.46, 0.08), (0.49, 0.08), (0.49, 0.80), (0.46, 0.80)]), fill=255))
    shadow(c, pole, 4, 6, 6, 150)
    fill(c, soften(pole), linear((240, 210, 150, 255), (130, 90, 40, 255), 0))
    tip = shape(lambda d: d.polygon(pts([(0.475, 0.02), (0.50, 0.09), (0.45, 0.09)]), fill=255))
    fill(c, soften(tip), GB.gold())
    flag = []
    for i in range(21):
        t = i / 20
        flag.append((0.49 + 0.40 * t, 0.12 + 0.03 * math.sin(t * 6)))
    for i in range(20, -1, -1):
        t = i / 20
        flag.append((0.49 + 0.40 * t, 0.50 + 0.03 * math.sin(t * 6) - (0.08 if i == 20 else 0)))
    flag[-21] = (0.80, 0.31)
    fl = shape(lambda d: d.polygon(pts(flag), fill=255))
    glow(c, fl, (255, 200, 120, 255), 14, 1.2)
    shadow(c, fl, 4, 7, 7, 150)
    fill(c, soften(fl), linear((240, 60, 50, 255), (130, 10, 20, 255), 0))
    trim = ImageChops.subtract(fl, shape(lambda d: d.polygon(
        pts([(x, y + (0.035 if j < 21 else -0.035)) for j, (x, y) in enumerate(flag)]), fill=255)))
    fill(c, soften(trim), GB.gold())
    mark = shape(lambda d: [d.rounded_rectangle(pts([(0.64, 0.17), (0.70, 0.35)]), radius=0.02 * W, fill=255),
                            d.ellipse(pts([(0.64, 0.38), (0.70, 0.44)]), fill=255)])
    fill(c, soften(mark), (255, 240, 200, 255))
    song_note(c, 0.24, 0.86, 0.72, 1)
    return finish(c)


def adventurers_dirge():
    """A quiet candle guttering beside the note: the mournful song that draws less enmity."""
    c = bg((70, 90, 130), (6, 8, 20), 0.6, 0.35)
    smoke = shape(lambda d: d.polygon(pts(stroke([(0.66, 0.30), (0.62, 0.20), (0.68, 0.12), (0.64, 0.02)], 0.03,
                                                 0.07)), fill=255))
    fill(c, soften(smoke, 8).point(lambda v: int(v * 0.4)), (220, 230, 255, 255))
    cand = shape(lambda d: [d.rounded_rectangle(pts([(0.58, 0.44), (0.74, 0.84)]), radius=0.02 * W, fill=255),
                            d.ellipse(pts([(0.50, 0.80), (0.82, 0.90)]), fill=255)])
    shadow(c, cand, 4, 7, 6, 150)
    fill(c, soften(cand), linear((250, 244, 226, 255), (180, 170, 150, 255), 0))
    drip = shape(lambda d: d.polygon(pts([(0.60, 0.44), (0.64, 0.44), (0.635, 0.56), (0.615, 0.58)]), fill=255))
    fill(c, soften(drip), (255, 250, 236, 255))
    fl = shape(lambda d: d.polygon(pts([(0.66, 0.26), (0.70, 0.36), (0.68, 0.43), (0.64, 0.43), (0.62, 0.36)]),
                                   fill=255))
    glow(c, fl, (255, 200, 120, 255), 22, 1.3)
    fill(c, soften(fl), linear((255, 255, 230, 255), (255, 170, 60, 255), 270))
    song_note(c, 0.24, 0.84, 0.76, 1, paint=linear((240, 244, 255, 255), (160, 170, 210, 255), 90),
              halo=(170, 190, 255, 255))
    return finish(c)


def sentinels_scherzo():
    """A jagged heavy blow broken on a curved ward: the song that blunts big hits."""
    c = bg((60, 120, 160), (4, 14, 30))
    burst = mask()
    bd = ImageDraw.Draw(burst)
    star = []
    for i in range(18):
        a = math.pi * i / 9
        r = 0.20 if i % 2 == 0 else 0.08
        star.append((0.78 + math.cos(a) * r, 0.26 + math.sin(a) * r))
    bd.polygon(pts(star), fill=255)
    glow(c, burst, (255, 120, 80, 255), 12, 1.3)
    fill(c, soften(burst), linear((255, 220, 140, 255), (230, 60, 40, 255), 90))
    ward = shape(lambda d: d.polygon(pts(stroke(arc(0.38, 0.62, 0.36, -80, 10, 40), 0.07, 0.07)), fill=255))
    glow(c, ward, (140, 220, 255, 255), 18, 1.5)
    fill(c, soften(ward), linear((240, 252, 255, 255), (120, 200, 250, 255), 90))
    song_note(c, 0.28, 0.84, 0.76, 1)
    return finish(c)


def pining_nocturne():
    """A drooping flower under the night stars beside the note: casting slowed, magic accuracy dulled."""
    c = bg((100, 50, 140), (12, 4, 26), 0.6, 0.35)
    motes(c, 81, 14, (0.10, 0.08, 0.90, 0.40), (0.004, 0.010), (230, 210, 255, 255))
    stem = shape(lambda d: d.polygon(pts(stroke([(0.78, 0.90), (0.80, 0.60), (0.76, 0.38), (0.68, 0.32),
                                                 (0.62, 0.36)], 0.035, 0.02)), fill=255))
    fill(c, soften(stem), linear((140, 200, 140, 255), (40, 90, 60, 255), 90))
    bloom = shape(lambda d: [d.polygon(xf([(0, 0), (-0.09, 0.10), (-0.05, 0.22), (0, 0.16), (0.05, 0.22),
                                           (0.09, 0.10)], 0.62, 0.36, 1.3, 25), fill=255)])
    glow(c, bloom, (220, 160, 255, 255), 12, 1.3)
    fill(c, soften(bloom), linear((240, 210, 255, 255), (150, 80, 210, 255), 90))
    tear = shape(lambda d: GB.heart_drop(d, 0.56, 0.68, 0.03))
    glow(c, tear, (180, 200, 255, 255), 6, 1.4)
    fill(c, soften(tear), (220, 230, 255, 255))
    song_note(c, 0.22, 0.86, 0.70, 1, paint=linear((250, 240, 255, 255), (190, 160, 230, 255), 90),
              halo=(200, 160, 255, 255))
    stars(c, [(0.80, 0.18, 0.06), (0.30, 0.20, 0.045)], (220, 200, 255, 255))
    return finish(c)


# ---- BRD: hue-shifted families (bases painted red-orange, hue ~8) ------------------------------------------------
def etude(greater=False):
    """A sheet of music with a rising arrow: a stat raised. The greater etudes add a laurel and a star."""
    def paint():
        c = bg((210, 60, 40), (36, 6, 4))
        if greater:
            GB.rays(c, 0.58, 0.40, 14, 0.7, (255, 200, 170, 255), 110, 0.06, 6)
        sheet_ = shape(lambda d: d.polygon(xf([(-0.20, -0.26), (0.20, -0.26), (0.20, 0.26), (-0.20, 0.26)], 0.60, 0.42,
                                              1.0, 10), fill=255))
        shadow(c, sheet_, 4, 7, 7, 150)
        fill(c, soften(sheet_), linear((255, 236, 220, 255), (220, 170, 150, 255), 90))
        staff = shape(lambda d: [d.line(xf([(-0.16, y), (0.16, y)], 0.60, 0.42, 1.0, 10), fill=255,
                                        width=int(0.008 * W)) for y in (-0.16, -0.10, -0.04, 0.02, 0.08)])
        fill(c, soften(staff).point(lambda v: int(v * 0.6)), (150, 40, 30, 255))
        up = shape(lambda d: [d.polygon(xf([(-0.05, 0.24), (0.05, 0.24), (0.05, -0.06), (0.13, -0.06), (0, -0.28),
                                            (-0.13, -0.06), (-0.05, -0.06)], 0.70, 0.40, 1.0, 0), fill=255)] +
                   ([d.polygon(xf([(0.13, 0.06), (0, -0.16), (-0.13, 0.06), (-0.13, 0.13), (0, -0.07), (0.13, 0.13)],
                                  0.70, 0.40, 1.0, 0), fill=0),
                     d.polygon(xf([(0.13, 0.13), (0, -0.09), (-0.13, 0.13), (-0.13, 0.20), (0, -0.0), (0.13, 0.20)],
                                  0.70, 0.40, 1.0, 0), fill=255)] if greater else []))
        glow(c, up, (255, 120, 80, 255), 12, 1.4)
        shadow(c, up, 3, 5, 5, 150)
        fill(c, soften(up), linear((255, 160, 120, 255), (220, 30, 20, 255), 90))
        if greater:
            st = shape(lambda d: sparkle(d, 0.80, 0.14, 0.10))
            glow(c, st, (255, 220, 160, 255), 10, 1.5)
            fill(c, soften(st), (255, 255, 240, 255))
            lr = shape(lambda d: [leaf(d, 0.42 + 0.025 * i, 0.94 - 0.11 * i, 0.10, 0.03, -120 + 12 * i)
                                  for i in range(6)])
            fill(c, soften(lr), linear((255, 200, 120, 255), (200, 80, 30, 255), 90))
        cream_note(c, 0.26, 0.84, 0.78, 2 if greater else 1)
        return finish(c)
    return paint


def carol():
    """An elemental crystal circled by a guarding ring, the note before it: element resistance up."""
    c = bg((200, 50, 30), (32, 4, 2))
    back = shape(lambda d: d.ellipse(pts([(0.32, 0.30), (0.92, 0.58)]), outline=255, width=int(0.04 * W)))
    back = ImageChops.multiply(back, shape(lambda d: d.rectangle(pts([(0, 0), (1, 0.44)]), fill=255)))
    glow(c, back, (255, 160, 120, 255), 8, 1.2)
    fill(c, soften(back).point(lambda v: int(v * 0.8)), (255, 210, 180, 255))
    elem_crystal(c, 0.62, 0.40, 0.13, 0.27, (255, 190, 150, 255), (220, 40, 20, 255), (255, 90, 50, 255))
    front = shape(lambda d: d.ellipse(pts([(0.32, 0.30), (0.92, 0.58)]), outline=255, width=int(0.04 * W)))
    front = ImageChops.subtract(front, shape(lambda d: d.rectangle(pts([(0, 0), (1, 0.44)]), fill=255)))
    glow(c, front, (255, 180, 140, 255), 10, 1.4)
    fill(c, soften(front), (255, 236, 220, 255))
    stars(c, [(0.88, 0.40, 0.06), (0.36, 0.38, 0.04)], (255, 180, 150, 255))
    cream_note(c, 0.26, 0.84, 0.76, 1)
    return finish(c)


def threnody():
    """A cracked elemental crystal sinking, a down-arrow beside it: element resistance down."""
    c = bg((140, 36, 30), (22, 2, 4), 0.5, 0.5)
    elem_crystal(c, 0.58, 0.44, 0.13, 0.27, (240, 160, 130, 255), (170, 30, 20, 255), (220, 70, 40, 255))
    crack = shape(lambda d: d.line(pts([(0.55, 0.18), (0.60, 0.30), (0.55, 0.40), (0.62, 0.50), (0.57, 0.62)]),
                                   fill=255, width=int(0.016 * W), joint='curve'))
    fill(c, soften(crack), (40, 4, 6, 255))
    dn = shape(lambda d: d.polygon(pts([(0.80, 0.14), (0.86, 0.14), (0.86, 0.40), (0.92, 0.40), (0.83, 0.54),
                                        (0.74, 0.40), (0.80, 0.40)]), fill=255))
    glow(c, dn, (255, 120, 90, 255), 10, 1.3)
    fill(c, soften(dn), linear((255, 230, 220, 255), (240, 120, 100, 255), 90))
    shards = shape(lambda d: [d.polygon(pts([(0.48, 0.78), (0.52, 0.76), (0.51, 0.82)]), fill=255),
                              d.polygon(pts([(0.66, 0.80), (0.70, 0.79), (0.68, 0.85)]), fill=255)])
    fill(c, soften(shards), (240, 150, 120, 255))
    cream_note(c, 0.24, 0.84, 0.72, 1, halo=(255, 120, 100, 255))
    return finish(c)


# ---- SMN: elemental spirits (one wisp, hue-shifted) ---------------------------------------------------------------
def spirit():
    """An elemental spirit: a bright wisp-core with ribbons of light orbiting it."""
    c = bg((190, 50, 30), (30, 4, 2), 0.5, 0.5)
    rb = mask()
    d = ImageDraw.Draw(rb)
    for k, (rx, ry, a0) in enumerate(((0.36, 0.14, -20), (0.32, 0.12, 40), (0.34, 0.10, 100))):
        L, f = GC.frame(0.5, 0.5, 0.5 + math.cos(math.radians(a0)), 0.5 + math.sin(math.radians(a0)))
        seq = [f(math.cos(t) * rx, math.sin(t) * ry) for t in [math.pi * 2 * i / 50 * 0.75 + k for i in range(51)]]
        d.polygon(pts(stroke(seq, 0.006, 0.04)), fill=255)
    glow(c, rb, (255, 120, 60, 255), 14, 1.3)
    fill(c, soften(rb), linear((255, 220, 180, 255), (255, 110, 60, 255), 90))
    tail = shape(lambda d: d.polygon(pts(stroke([(0.5, 0.48), (0.46, 0.66), (0.54, 0.78), (0.48, 0.90)], 0.18,
                                                0.01)), fill=255))
    glow(c, tail, (255, 100, 40, 255), 16, 1.1)
    fill(c, soften(tail, 4).point(lambda v: int(v * 0.7)), (255, 150, 90, 255))
    core = shape(lambda d: d.ellipse(pts([(0.36, 0.34), (0.64, 0.62)]), fill=255))
    glow(c, core, (255, 120, 60, 255), 34, 1.5)
    glow(c, core, (255, 210, 160, 255), 14, 1.2)
    fill(c, soften(core, 3), radial((255, 255, 250, 255), (255, 120, 60, 255), 0.47, 0.44, 0.18))
    eyes = shape(lambda d: [d.ellipse(pts([(0.445, 0.45), (0.475, 0.50)]), fill=255),
                            d.ellipse(pts([(0.525, 0.45), (0.555, 0.50)]), fill=255)])
    fill(c, soften(eyes, 0.8), (110, 20, 10, 255))
    motes(c, 91, 14, (0.12, 0.12, 0.88, 0.88), (0.006, 0.013), (255, 140, 80, 255))
    return finish(c)


# ---- SMN: avatars (portraits, matching group_c's Ifrit/Shiva/Garuda/Carbuncle) -----------------------------------
def titan():
    c = bg((180, 120, 50), (30, 16, 4), 0.5, 0.5)
    rnd = random.Random(101)
    rocks = mask()
    rd = ImageDraw.Draw(rocks)
    for x, y, s in ((0.16, 0.30, 0.05), (0.84, 0.26, 0.06), (0.12, 0.62, 0.04), (0.88, 0.66, 0.05),
                    (0.24, 0.12, 0.03)):
        rd.polygon(pts([(x + math.cos(a) * s * rnd.uniform(0.7, 1.1), y + math.sin(a) * s * rnd.uniform(0.7, 1.1))
                        for a in [math.pi * 2 * i / 5 for i in range(5)]]), fill=255)
    shadow(c, rocks, 3, 5, 5, 140)
    fill(c, soften(rocks), linear((220, 190, 140, 255), (110, 80, 50, 255), 90))
    head = shape(lambda d: d.polygon(pts([(0.30, 0.22), (0.42, 0.14), (0.58, 0.14), (0.70, 0.22), (0.74, 0.46),
                                          (0.68, 0.62), (0.32, 0.62), (0.26, 0.46)]), fill=255))
    beard = shape(lambda d: d.polygon(pts([(0.28, 0.50), (0.36, 0.60), (0.64, 0.60), (0.72, 0.50), (0.70, 0.70),
                                           (0.62, 0.84), (0.56, 0.80), (0.50, 0.92), (0.44, 0.80), (0.38, 0.84),
                                           (0.30, 0.70)]), fill=255))
    both = lighter(head, beard)
    glow(c, both, (255, 210, 120, 255), 16, 1.1)
    shadow(c, both, 5, 8, 7, 170)
    fill(c, soften(head), linear((240, 200, 130, 255), (160, 110, 60, 255), 90))
    fill(c, soften(beard), linear((150, 120, 90, 255), (70, 50, 34, 255), 90))
    brow = shape(lambda d: d.polygon(pts([(0.30, 0.34), (0.48, 0.38), (0.52, 0.38), (0.70, 0.34), (0.70, 0.29),
                                          (0.30, 0.29)]), fill=255))
    shadow(c, brow, 0, 5, 4, 150)
    fill(c, soften(brow), linear((200, 160, 100, 255), (120, 80, 44, 255), 90))
    eyes = shape(lambda d: [d.polygon(pts([(0.35, 0.40), (0.46, 0.42), (0.37, 0.45)]), fill=255),
                            d.polygon(pts([(0.65, 0.40), (0.54, 0.42), (0.63, 0.45)]), fill=255)])
    glow(c, eyes, (255, 220, 90, 255), 8, 1.6)
    fill(c, soften(eyes, 0.8), (255, 250, 200, 255))
    cracks = shape(lambda d: [d.line(pts([(0.40, 0.16), (0.44, 0.22), (0.41, 0.27)]), fill=255, width=int(0.008 * W)),
                              d.line(pts([(0.66, 0.46), (0.61, 0.52), (0.63, 0.57)]), fill=255, width=int(0.008 * W)),
                              d.line(pts([(0.50, 0.44), (0.50, 0.53)]), fill=255, width=int(0.012 * W))])
    fill(c, soften(cracks).point(lambda v: int(v * 0.6)), (90, 50, 20, 255))
    motes(c, 102, 10, (0.15, 0.70, 0.85, 0.95), (0.006, 0.012), (255, 200, 120, 255))
    return finish(c)


def leviathan():
    """The sea serpent rearing from the waves: one smooth head, a single swept crest, a burning eye."""
    c = bg((40, 110, 200), (2, 10, 40), 0.5, 0.40)
    neck = [(0.80, 1.02), (0.74, 0.78), (0.62, 0.58), (0.52, 0.44), (0.44, 0.36)]
    nk = shape(lambda d: d.polygon(pts(stroke(neck, 0.26, 0.14)), fill=255))
    head = shape(lambda d: d.polygon(pts([(0.56, 0.46), (0.52, 0.31), (0.38, 0.26), (0.22, 0.29), (0.09, 0.37),
                                          (0.20, 0.45), (0.40, 0.49)]), fill=255))
    fins = shape(lambda d: [d.polygon(pts([(0.40, 0.29), (0.72, 0.10), (0.60, 0.30), (0.55, 0.40)]), fill=255),
                            d.polygon(pts([(0.68, 0.70), (0.86, 0.60), (0.76, 0.76)]), fill=255)])
    body = lighter(lighter(nk, head), fins)
    glow(c, body, (120, 220, 255, 255), 16, 1.2)
    shadow(c, body, 5, 8, 7, 170)
    fill(c, soften(fins), linear((170, 245, 255, 255), (40, 120, 200, 255), 90))
    fill(c, soften(lighter(nk, head)), linear((100, 190, 240, 255), (20, 60, 140, 255), 0))
    belly = shape(lambda d: d.polygon(pts(stroke([(0.86, 1.02), (0.80, 0.80), (0.68, 0.62)], 0.08, 0.04)), fill=255))
    fill(c, soften(ImageChops.multiply(belly, nk)), (200, 240, 255, 255))
    mouth = shape(lambda d: d.line(pts([(0.11, 0.38), (0.30, 0.41)]), fill=255, width=int(0.016 * W)))
    fill(c, soften(mouth), (10, 30, 70, 255))
    eye = shape(lambda d: d.ellipse(pts([(0.31, 0.315), (0.38, 0.355)]), fill=255))
    glow(c, eye, (255, 230, 120, 255), 8, 1.8)
    fill(c, soften(eye, 0.8), (255, 250, 210, 255))
    waves = mask()
    wd = ImageDraw.Draw(waves)
    seq = [(-0.05 + i * 0.02, 0.86 + 0.03 * math.sin(i * 0.6)) for i in range(64)]
    wd.polygon(pts(seq + [(1.2, 1.2), (-0.05, 1.2)]), fill=255)
    glow(c, waves, (150, 230, 255, 255), 10, 1.1)
    fill(c, soften(waves), linear((180, 240, 255, 255), (20, 80, 170, 255), 90))
    return finish(c)


def ramuh():
    c = bg((120, 80, 200), (12, 6, 36), 0.5, 0.42)
    bolt = shape(lambda d: d.polygon(pts([(0.86, 0.06), (0.74, 0.34), (0.82, 0.34), (0.70, 0.62), (0.76, 0.62),
                                          (0.62, 0.94), (0.92, 0.50), (0.84, 0.50), (0.94, 0.28), (0.86, 0.28),
                                          (0.94, 0.06)]), fill=255))
    glow(c, bolt, (200, 200, 255, 255), 18, 1.6)
    fill(c, soften(bolt), linear((255, 255, 255, 255), (200, 210, 255, 255), 90))
    hood = shape(lambda d: d.polygon(pts([(0.40, 0.10), (0.24, 0.30), (0.20, 0.70), (0.30, 0.90), (0.70, 0.90),
                                          (0.76, 0.62), (0.70, 0.26), (0.54, 0.10)]), fill=255))
    shadow(c, hood, 5, 8, 7, 170)
    fill(c, soften(hood), linear((90, 70, 170, 255), (30, 20, 70, 255), 90))
    face = shape(lambda d: d.ellipse(pts([(0.32, 0.24), (0.62, 0.56)]), fill=255))
    fill(c, soften(face), linear((240, 200, 170, 255), (190, 140, 110, 255), 90))
    beard = shape(lambda d: d.polygon(pts([(0.30, 0.44), (0.38, 0.50), (0.56, 0.50), (0.64, 0.44), (0.62, 0.66),
                                           (0.54, 0.84), (0.47, 0.92), (0.40, 0.84), (0.32, 0.66)]), fill=255))
    brows = shape(lambda d: [d.polygon(pts([(0.32, 0.33), (0.46, 0.35), (0.44, 0.38), (0.30, 0.38)]), fill=255),
                             d.polygon(pts([(0.62, 0.33), (0.48, 0.35), (0.50, 0.38), (0.64, 0.38)]), fill=255),
                             d.polygon(pts([(0.40, 0.44), (0.47, 0.42), (0.54, 0.44), (0.47, 0.47)]), fill=255)])
    wh = lighter(beard, brows)
    glow(c, wh, (220, 220, 255, 255), 10, 1.2)
    fill(c, soften(wh), linear((255, 255, 255, 255), (200, 200, 220, 255), 90))
    eyes = shape(lambda d: [d.ellipse(pts([(0.37, 0.385), (0.41, 0.41)]), fill=255),
                            d.ellipse(pts([(0.53, 0.385), (0.57, 0.41)]), fill=255)])
    glow(c, eyes, (180, 200, 255, 255), 5, 1.6)
    fill(c, soften(eyes, 0.8), (240, 240, 255, 255))
    motes(c, 121, 10, (0.08, 0.10, 0.40, 0.40), (0.005, 0.011), (210, 210, 255, 255))
    return finish(c)


def fenrir():
    def wf(seq):
        return pts([(0.10 + x * 0.78, 0.26 + y * 0.78) for x, y in seq])
    c = bg((60, 80, 160), (4, 4, 20), 0.6, 0.35)
    moon = shape(lambda d: d.ellipse(pts([(0.40, 0.08), (0.88, 0.56)]), fill=255))
    glow(c, moon, (220, 220, 255, 255), 30, 1.4)
    fill(c, soften(moon), radial((255, 255, 250, 255), (200, 205, 235, 255), 0.58, 0.26, 0.28))
    craters = shape(lambda d: [d.ellipse(pts([(0.70, 0.18), (0.78, 0.25)]), fill=255),
                               d.ellipse(pts([(0.74, 0.36), (0.80, 0.41)]), fill=255)])
    fill(c, soften(craters, 3).point(lambda v: int(v * 0.25)), (120, 120, 170, 255))
    wolf = shape(lambda d: [d.polygon(wf([(0.34, 1.0), (0.40, 0.76), (0.46, 0.60), (0.54, 0.48), (0.62, 0.38),
                                           (0.70, 0.30), (0.74, 0.25), (0.72, 0.21), (0.66, 0.22), (0.60, 0.22),
                                           (0.52, 0.24), (0.46, 0.22), (0.44, 0.10), (0.40, 0.04), (0.37, 0.14),
                                           (0.35, 0.20), (0.30, 0.10), (0.27, 0.06), (0.26, 0.20), (0.24, 0.30),
                                           (0.16, 0.44), (0.08, 0.62), (0.02, 0.80), (0.0, 1.0), (0.0, 1.4), (0.34, 1.4)]), fill=255),
                            d.polygon(wf([(0.42, 0.62), (0.36, 0.70), (0.44, 0.68), (0.40, 0.78), (0.46, 0.72)]),
                                      fill=255)])
    glow(c, wolf, (170, 180, 255, 255), 12, 1.8)
    fill(c, soften(wolf), linear((44, 46, 90, 255), (8, 8, 22, 255), 90))
    mouth = shape(lambda d: d.line(wf([(0.73, 0.25), (0.62, 0.30), (0.56, 0.30)]), fill=255, width=int(0.008 * W)))
    fill(c, soften(mouth), (120, 130, 200, 255))
    eye = shape(lambda d: d.polygon(wf([(0.46, 0.27), (0.52, 0.26), (0.50, 0.29)]), fill=255))
    glow(c, eye, (140, 200, 255, 255), 6, 1.8)
    fill(c, soften(eye, 0.8), (230, 250, 255, 255))
    stars(c, [(0.20, 0.24, 0.05), (0.84, 0.70, 0.04)])
    return finish(c)


def diabolos():
    c = bg((120, 40, 140), (12, 2, 20), 0.5, 0.50)
    wings = mask()
    wd = ImageDraw.Draw(wings)
    for sx in (-1, 1):
        wd.polygon(pts([(0.5 + sx * 0.12, 0.42), (0.5 + sx * 0.30, 0.16), (0.5 + sx * 0.46, 0.14),
                        (0.5 + sx * 0.44, 0.34), (0.5 + sx * 0.38, 0.30), (0.5 + sx * 0.40, 0.48),
                        (0.5 + sx * 0.32, 0.44), (0.5 + sx * 0.30, 0.60), (0.5 + sx * 0.20, 0.54)]), fill=255)
    glow(c, wings, (220, 100, 255, 255), 14, 1.2)
    fill(c, soften(wings), linear((110, 50, 140, 255), (30, 8, 44, 255), 90))
    head = shape(lambda d: [d.polygon(pts([(0.38, 0.30), (0.62, 0.30), (0.66, 0.50), (0.58, 0.72), (0.50, 0.78),
                                           (0.42, 0.72), (0.34, 0.50)]), fill=255),
                            d.polygon(pts(stroke([(0.40, 0.32), (0.32, 0.20), (0.34, 0.08)], 0.08, 0.01)), fill=255),
                            d.polygon(pts(stroke([(0.60, 0.32), (0.68, 0.20), (0.66, 0.08)], 0.08, 0.01)), fill=255)])
    shadow(c, head, 5, 8, 7, 170)
    fill(c, soften(head), linear((70, 40, 90, 255), (18, 6, 26, 255), 90))
    eyes = shape(lambda d: [d.polygon(pts([(0.39, 0.44), (0.48, 0.48), (0.41, 0.50)]), fill=255),
                            d.polygon(pts([(0.61, 0.44), (0.52, 0.48), (0.59, 0.50)]), fill=255)])
    glow(c, eyes, (255, 80, 220, 255), 10, 1.8)
    fill(c, soften(eyes, 0.8), (255, 220, 250, 255))
    grin = shape(lambda d: d.polygon(pts([(0.42, 0.60), (0.46, 0.63), (0.48, 0.61), (0.50, 0.64), (0.52, 0.61),
                                          (0.54, 0.63), (0.58, 0.60), (0.54, 0.67), (0.46, 0.67)]), fill=255))
    glow(c, grin, (255, 120, 230, 255), 6, 1.3)
    fill(c, soften(grin, 0.8), (255, 200, 245, 255))
    moon = shape(lambda d: GB.crescent(d, 0.5, 0.88, 0.07, (0.4, -0.3)))
    fill(c, soften(moon), (240, 220, 255, 255))
    motes(c, 131, 12, (0.12, 0.12, 0.88, 0.88), (0.005, 0.011), (230, 140, 255, 255))
    return finish(c)


def odin():
    c = bg((70, 80, 110), (6, 6, 16), 0.5, 0.40)
    blade = shape(lambda d: GC.katana(d, 0.20, 0.96, 0.92, 0.06, curve=-0.05, part='blade'))
    glow(c, blade, (230, 240, 255, 255), 14, 1.4)
    fill(c, soften(blade), linear((255, 255, 255, 255), (170, 180, 200, 255), 0))
    helm = shape(lambda d: [d.polygon(pts([(0.30, 0.30), (0.36, 0.20), (0.50, 0.16), (0.64, 0.20), (0.70, 0.30),
                                           (0.68, 0.60), (0.58, 0.76), (0.50, 0.80), (0.42, 0.76), (0.32, 0.60)]),
                                      fill=255),
                            d.polygon(pts(stroke([(0.34, 0.30), (0.20, 0.22), (0.14, 0.06)], 0.08, 0.01)), fill=255),
                            d.polygon(pts(stroke([(0.66, 0.30), (0.80, 0.22), (0.86, 0.06)], 0.08, 0.01)), fill=255)])
    shadow(c, helm, 5, 8, 7, 180)
    fill(c, soften(helm), linear((120, 120, 150, 255), (30, 30, 46, 255), 90))
    crest = shape(lambda d: d.polygon(pts([(0.48, 0.16), (0.52, 0.16), (0.52, 0.56), (0.50, 0.60), (0.48, 0.56)]),
                                      fill=255))
    fill(c, soften(crest), GB.gold())
    visor = shape(lambda d: d.polygon(pts([(0.34, 0.40), (0.66, 0.40), (0.64, 0.46), (0.36, 0.46)]), fill=255))
    fill(c, soften(visor), (6, 4, 10, 255))
    eyes = shape(lambda d: [d.ellipse(pts([(0.38, 0.415), (0.45, 0.445)]), fill=255),
                            d.ellipse(pts([(0.55, 0.415), (0.62, 0.445)]), fill=255)])
    glow(c, eyes, (255, 60, 40, 255), 8, 1.8)
    fill(c, soften(eyes, 0.8), (255, 200, 170, 255))
    trim = shape(lambda d: d.line(pts([(0.30, 0.30), (0.36, 0.20), (0.50, 0.16), (0.64, 0.20), (0.70, 0.30)]),
                                  fill=255, width=int(0.014 * W), joint='curve'))
    fill(c, soften(trim), GB.gold())
    return finish(c)


def alexander():
    """The holy fortress-giant: a towering armoured colossus in white and gold, its core blazing in its chest."""
    c = bg((70, 92, 176), (6, 8, 30), 0.5, 0.42)
    GB.rays(c, 0.5, 0.52, 16, 0.8, (255, 236, 180, 255), 80, 0.05, 6)

    def giant(d):
        for sx in (1, -1):
            X = lambda x: 0.5 + (x - 0.5) * sx
            d.polygon(pts([(X(0.35), 0.74), (X(0.47), 0.74), (X(0.46), 0.97), (X(0.33), 0.97)]), fill=255)   # leg
            d.polygon(pts([(X(0.31), 0.36), (X(0.10), 0.38), (X(0.07), 0.55), (X(0.30), 0.53)]), fill=255)   # pauldron
            d.polygon(pts([(X(0.15), 0.40), (X(0.18), 0.22), (X(0.21), 0.40)]), fill=255)                    # turret
            d.polygon(pts([(X(0.12), 0.53), (X(0.26), 0.53), (X(0.25), 0.79), (X(0.14), 0.79)]), fill=255)   # arm
            d.rounded_rectangle(pts([(min(X(0.11), X(0.28)), 0.77), (max(X(0.11), X(0.28)), 0.89)]),
                                radius=0.03 * W, fill=255)                                                # fist
            d.polygon(pts([(X(0.44), 0.29), (X(0.37), 0.13), (X(0.47), 0.25)]), fill=255)                    # horn
        d.polygon(pts([(0.30, 0.37), (0.70, 0.37), (0.64, 0.70), (0.36, 0.70)]), fill=255)                  # torso
        d.polygon(pts([(0.33, 0.68), (0.67, 0.68), (0.63, 0.79), (0.37, 0.79)]), fill=255)                  # hips
        d.rounded_rectangle(pts([(0.42, 0.22), (0.58, 0.38)]), radius=0.04 * W, fill=255)                   # helm
        d.polygon(pts([(0.46, 0.24), (0.50, 0.05), (0.54, 0.24)]), fill=255)                                # crest
    m = shape(giant)
    shadow(c, m, 5, 8, 8, 180)
    glow(c, m, (255, 230, 150, 255), 16, 1.1)
    fill(c, soften(m), linear((255, 253, 244, 255), (214, 196, 160, 255), 90))
    edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(int(0.035 * W) | 1)))
    seams = shape(lambda d: [d.line(pts([(0.34, 0.70), (0.66, 0.70)]), fill=255, width=int(0.022 * W)),
                             d.line(pts([(0.08, 0.465), (0.30, 0.455)]), fill=255, width=int(0.02 * W)),
                             d.line(pts([(0.92, 0.465), (0.70, 0.455)]), fill=255, width=int(0.02 * W)),
                             d.line(pts([(0.50, 0.60), (0.50, 0.70)]), fill=255, width=int(0.016 * W))])
    fill(c, soften(lighter(edge, ImageChops.multiply(seams, m))), GB.gold())
    ring = shape(lambda d: d.ellipse(pts([(0.405, 0.425), (0.595, 0.615)]), fill=255))
    fill(c, soften(ring), GB.gold())
    core = shape(lambda d: d.ellipse(pts([(0.43, 0.45), (0.57, 0.59)]), fill=255))
    glow(c, core, (110, 220, 255, 255), 22, 2.2)
    fill(c, soften(core), radial((255, 255, 255, 255), (70, 180, 255, 255), 0.48, 0.50, 0.08))
    visor = shape(lambda d: d.line(pts([(0.455, 0.305), (0.545, 0.305)]), fill=255, width=int(0.026 * W)))
    glow(c, visor, (110, 220, 255, 255), 8, 1.8)
    fill(c, soften(visor), (220, 250, 255, 255))
    return finish(c)


def cait_sith():
    c = bg((200, 80, 150), (34, 6, 30), 0.5, 0.48)
    head = shape(lambda d: [d.ellipse(pts([(0.26, 0.32), (0.74, 0.78)]), fill=255),
                            d.polygon(pts([(0.28, 0.48), (0.26, 0.20), (0.44, 0.36)]), fill=255),
                            d.polygon(pts([(0.72, 0.48), (0.74, 0.20), (0.56, 0.36)]), fill=255)])
    glow(c, head, (255, 180, 230, 255), 16, 1.3)
    shadow(c, head, 5, 8, 7, 160)
    fill(c, soften(head), linear((70, 60, 80, 255), (20, 16, 26, 255), 90))
    muzzle = shape(lambda d: [d.ellipse(pts([(0.36, 0.56), (0.52, 0.72)]), fill=255),
                              d.ellipse(pts([(0.48, 0.56), (0.64, 0.72)]), fill=255)])
    fill(c, soften(muzzle), linear((255, 255, 255, 255), (210, 210, 220, 255), 90))
    nose = shape(lambda d: d.polygon(pts([(0.47, 0.565), (0.53, 0.565), (0.50, 0.60)]), fill=255))
    fill(c, soften(nose, 0.8), (240, 110, 150, 255))
    eyes = shape(lambda d: [d.ellipse(pts([(0.35, 0.44), (0.45, 0.54)]), fill=255),
                            d.ellipse(pts([(0.55, 0.44), (0.65, 0.54)]), fill=255)])
    glow(c, eyes, (255, 230, 100, 255), 6, 1.4)
    fill(c, soften(eyes), (255, 220, 70, 255))
    slits = shape(lambda d: [d.ellipse(pts([(0.39, 0.45), (0.41, 0.53)]), fill=255),
                             d.ellipse(pts([(0.59, 0.45), (0.61, 0.53)]), fill=255)])
    fill(c, soften(slits, 0.8), (20, 10, 6, 255))
    crown = shape(lambda d: d.polygon(pts([(0.38, 0.32), (0.36, 0.14), (0.44, 0.22), (0.50, 0.08), (0.56, 0.22),
                                           (0.64, 0.14), (0.62, 0.32)]), fill=255))
    glow(c, crown, (255, 220, 120, 255), 12, 1.4)
    shadow(c, crown, 3, 5, 5, 150)
    fill(c, soften(crown), GB.gold())
    gem = shape(lambda d: d.ellipse(pts([(0.48, 0.24), (0.52, 0.28)]), fill=255))
    fill(c, soften(gem, 0.8), (200, 20, 60, 255))
    cape = shape(lambda d: d.polygon(pts([(0.30, 0.80), (0.70, 0.80), (0.76, 1.0), (0.24, 1.0)]), fill=255))
    fill(c, soften(cape), linear((230, 40, 60, 255), (120, 10, 30, 255), 90))
    return finish(c)


def siren():
    c = bg((40, 170, 160), (2, 26, 30), 0.5, 0.45)
    hair = mask()
    hd = ImageDraw.Draw(hair)
    for k, (y0, amp) in enumerate(((0.20, 0.05), (0.32, 0.06), (0.44, 0.05), (0.56, 0.04))):
        seq = [(0.60 - 0.55 * t, y0 + 0.10 * t + amp * math.sin(t * 7 + k)) for t in [i / 40 for i in range(41)]]
        hd.polygon(pts(stroke(seq, 0.12, 0.01)), fill=255)
    glow(c, hair, (150, 255, 230, 255), 12, 1.2)
    fill(c, soften(hair), linear((180, 255, 220, 255), (40, 160, 140, 255), 0))
    face = shape(lambda d: d.polygon(pts([(0.56, 0.16), (0.68, 0.20), (0.74, 0.32), (0.76, 0.40), (0.82, 0.46),
                                          (0.76, 0.48), (0.78, 0.54), (0.74, 0.56), (0.76, 0.60), (0.70, 0.68),
                                          (0.62, 0.70), (0.60, 0.82), (0.50, 0.90), (0.48, 0.60), (0.52, 0.26)]),
                                     fill=255))
    glow(c, face, (200, 255, 240, 255), 12, 1.3)
    shadow(c, face, 4, 7, 7, 150)
    fill(c, soften(face), linear((240, 250, 255, 255), (160, 200, 220, 255), 0))
    eye = shape(lambda d: d.polygon(pts([(0.66, 0.37), (0.72, 0.36), (0.70, 0.39)]), fill=255))
    fill(c, soften(eye, 0.8), (20, 60, 70, 255))
    lips = shape(lambda d: d.ellipse(pts([(0.74, 0.545), (0.78, 0.575)]), fill=255))
    fill(c, soften(lips, 0.8), (220, 80, 120, 255))
    for x, y, s in ((0.86, 0.64, 0.30), (0.80, 0.86, 0.24)):
        nt = shape(lambda d, x=x, y=y, s=s: GB.note(d, x, y, s, 1))
        glow(c, nt, (200, 255, 240, 255), 6, 1.4)
        fill(c, soften(nt), (240, 255, 250, 255))
    return finish(c)


def atomos():
    c = bg((70, 140, 100), (4, 16, 10), 0.5, 0.5)
    rim = shape(lambda d: d.ellipse(pts([(0.14, 0.14), (0.86, 0.86)]), fill=255))
    glow(c, rim, (160, 255, 190, 255), 18, 1.2)
    fill(c, soften(rim), linear((140, 120, 90, 255), (60, 46, 30, 255), 90))
    teeth = mask()
    td = ImageDraw.Draw(teeth)
    for i in range(18):
        a = math.pi * 2 * i / 18
        L, f = GC.frame(0.5, 0.5, 0.5 + math.cos(a), 0.5 + math.sin(a))
        td.polygon(pts([f(0.33, -0.045), f(0.22, 0), f(0.33, 0.045)]), fill=255)
    maw = shape(lambda d: d.ellipse(pts([(0.18, 0.18), (0.82, 0.82)]), fill=255))
    fill(c, soften(maw), radial((10, 4, 20, 255), (60, 20, 70, 255), 0.5, 0.5, 0.34))
    sw = mask()
    sd = ImageDraw.Draw(sw)
    for k in range(3):
        sp = []
        for i in range(40):
            t = i / 39
            a = math.radians(k * 120 + 300 * t)
            r = 0.04 + 0.26 * t
            sp.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
        sd.polygon(pts(stroke(sp, 0.01, 0.05)), fill=255)
    glow(c, sw, (170, 120, 255, 255), 10, 1.3)
    fill(c, soften(sw, 2).point(lambda v: int(v * 0.7)), (200, 170, 255, 255))
    fill(c, soften(teeth), linear((255, 252, 236, 255), (200, 190, 160, 255), 90))
    hands = shape(lambda d: [d.polygon(xf([(-0.03, 0.0), (0.03, 0.0), (0.03, -0.10), (0.05, -0.16), (0.02, -0.14),
                                           (0.0, -0.19), (-0.02, -0.14), (-0.05, -0.16), (-0.03, -0.10)],
                                          0.5 + math.cos(a) * 0.40, 0.5 + math.sin(a) * 0.40, 1.0,
                                          math.degrees(a) + 90), fill=255)
                             for a in [math.radians(v) for v in (-150, -30, 90)]])
    shadow(c, hands, 3, 5, 5, 150)
    fill(c, soften(hands), linear((200, 230, 200, 255), (110, 140, 110, 255), 90))
    eye = shape(lambda d: d.ellipse(pts([(0.46, 0.46), (0.54, 0.54)]), fill=255))
    glow(c, eye, (255, 230, 120, 255), 10, 1.6)
    fill(c, soften(eye), (255, 250, 210, 255))
    return finish(c)


# ---- NIN: elemental ninjutsu (an element rising from the open scroll, like Katon) ----------------------------------
def scroll(c, ends=(150, 40, 30, 255)):
    sc = shape(lambda d: [d.rectangle(pts([(0.22, 0.76), (0.78, 0.86)]), fill=255),
                          d.ellipse(pts([(0.16, 0.74), (0.26, 0.88)]), fill=255),
                          d.ellipse(pts([(0.74, 0.74), (0.84, 0.88)]), fill=255)])
    shadow(c, sc, 4, 6, 5, 160)
    fill(c, soften(sc), linear((250, 236, 200, 255), (200, 170, 120, 255), 90))
    e = shape(lambda d: [d.ellipse(pts([(0.18, 0.765), (0.24, 0.855)]), fill=255),
                         d.ellipse(pts([(0.76, 0.765), (0.82, 0.855)]), fill=255)])
    fill(c, soften(e), ends)


def spiral(n=60, turns=600, r0=0.05, r1=0.24, cy=0.44, k=0.0):
    sp = []
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(90 + turns * t + k)
        r = r0 + (r1 - r0) * t
        sp.append((0.5 + math.cos(a) * r, cy + math.sin(a) * r * 0.9))
    return sp


def hyoton():
    c = bg((60, 140, 210), (4, 14, 40), 0.5, 0.48, 0.70)
    shards = mask()
    sd = ImageDraw.Draw(shards)
    sp = spiral(14, 560, 0.08, 0.27)
    for i, (x, y) in enumerate(sp):
        a = math.atan2(y - 0.44, x - 0.5)
        s = 0.03 + 0.05 * i / 13
        L, f = GC.frame(x, y, x + math.cos(a + 1.2), y + math.sin(a + 1.2))
        sd.polygon(pts([f(-s * 1.6, 0), f(0, -s * 0.5), f(s * 1.6, 0), f(0, s * 0.5)]), fill=255)
    glow(c, shards, (160, 230, 255, 255), 16, 1.4)
    fill(c, soften(shards), linear((255, 255, 255, 255), (140, 210, 250, 255), 90))
    core = shape(lambda d: d.polygon(pts(crystal_poly(0.5, 0.44, 0.06, 0.10)), fill=255))
    glow(c, core, (220, 250, 255, 255), 12, 1.5)
    fill(c, soften(core), (250, 255, 255, 255))
    scroll(c, (40, 80, 150, 255))
    motes(c, 141, 10, (0.20, 0.08, 0.80, 0.30), (0.005, 0.012), (200, 240, 255, 255))
    return finish(c)


def huton():
    c = bg((60, 160, 90), (4, 28, 10), 0.5, 0.48, 0.70)
    sw = mask()
    sd = ImageDraw.Draw(sw)
    for k in range(3):
        sd.polygon(pts(stroke(spiral(50, 420, 0.04 + 0.03 * k, 0.24 + 0.04 * k, 0.44, k * 120), 0.01, 0.05)),
                   fill=255 - k * 50)
    glow(c, sw, (190, 255, 200, 255), 16, 1.3)
    fill(c, soften(sw), linear((250, 255, 250, 255), (150, 230, 170, 255), 90))
    lv = shape(lambda d: [leaf(d, 0.22, 0.28, 0.08, 0.03, 30), leaf(d, 0.74, 0.20, 0.07, 0.025, -60),
                          leaf(d, 0.80, 0.58, 0.07, 0.025, 120)])
    fill(c, soften(lv), (200, 255, 160, 255))
    scroll(c, (40, 120, 60, 255))
    return finish(c)


def doton():
    c = bg((170, 120, 60), (30, 16, 4), 0.5, 0.48, 0.70)
    spikes = shape(lambda d: [d.polygon(pts([(0.30, 0.76), (0.36, 0.30), (0.44, 0.76)]), fill=255),
                              d.polygon(pts([(0.40, 0.76), (0.50, 0.14), (0.62, 0.76)]), fill=255),
                              d.polygon(pts([(0.56, 0.76), (0.68, 0.36), (0.74, 0.76)]), fill=255),
                              d.polygon(pts([(0.20, 0.78), (0.24, 0.52), (0.32, 0.78)]), fill=255),
                              d.polygon(pts([(0.70, 0.78), (0.80, 0.56), (0.82, 0.78)]), fill=255)])
    glow(c, spikes, (255, 210, 130, 255), 16, 1.2)
    shadow(c, spikes, 5, 8, 7, 170)
    fill(c, soften(spikes), linear((240, 200, 140, 255), (120, 80, 40, 255), 0))
    facets = shape(lambda d: [d.polygon(pts([(0.50, 0.14), (0.62, 0.76), (0.52, 0.76)]), fill=255),
                              d.polygon(pts([(0.36, 0.30), (0.44, 0.76), (0.38, 0.76)]), fill=255),
                              d.polygon(pts([(0.68, 0.36), (0.74, 0.76), (0.69, 0.76)]), fill=255)])
    fill(c, soften(facets).point(lambda v: int(v * 0.5)), (60, 30, 10, 255))
    rnd = random.Random(151)
    deb = mask()
    dd = ImageDraw.Draw(deb)
    for _ in range(8):
        x, y, r = rnd.uniform(0.18, 0.82), rnd.uniform(0.10, 0.40), rnd.uniform(0.012, 0.025)
        dd.polygon(pts([(x - r, y), (x, y - r), (x + r, y + r * 0.4)]), fill=255)
    fill(c, soften(deb), (230, 190, 130, 255))
    scroll(c, (120, 70, 20, 255))
    return finish(c)


def raiton():
    c = bg((120, 60, 200), (14, 4, 36), 0.5, 0.48, 0.70)
    ring = shape(lambda d: d.polygon(pts(stroke(spiral(50, 500, 0.06, 0.26), 0.006, 0.03)), fill=180))
    glow(c, ring, (200, 170, 255, 255), 10, 1.2)
    fill(c, soften(ring), (230, 220, 255, 255))
    bolt = shape(lambda d: d.polygon(pts([(0.56, 0.06), (0.38, 0.40), (0.50, 0.40), (0.36, 0.76), (0.66, 0.32),
                                          (0.53, 0.32), (0.66, 0.06)]), fill=255))
    glow(c, bolt, (190, 150, 255, 255), 24, 1.6)
    glow(c, bolt, (255, 255, 255, 255), 8)
    fill(c, soften(bolt), linear((255, 255, 255, 255), (220, 210, 255, 255), 90))
    scroll(c, (80, 40, 150, 255))
    motes(c, 161, 10, (0.15, 0.10, 0.85, 0.70), (0.005, 0.011), (220, 200, 255, 255))
    return finish(c)


def suiton():
    c = bg((30, 110, 170), (2, 12, 34), 0.5, 0.48, 0.70)
    wv = shape(lambda d: d.polygon(pts(stroke(spiral(60, 560, 0.04, 0.26), 0.02, 0.12)), fill=255))
    glow(c, wv, (100, 200, 255, 255), 22, 1.3)
    fill(c, soften(wv), radial((240, 252, 255, 255), (40, 120, 220, 255), 0.5, 0.44, 0.30))
    foam = mask()
    fd = ImageDraw.Draw(foam)
    for x, y, r in ((0.74, 0.40, 0.03), (0.78, 0.34, 0.02), (0.70, 0.30, 0.018), (0.28, 0.52, 0.022),
                    (0.32, 0.60, 0.015)):
        fd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    fill(c, soften(foam), (240, 250, 255, 255))
    drops = shape(lambda d: [GB.heart_drop(d, 0.22, 0.30, 0.025), GB.heart_drop(d, 0.80, 0.62, 0.02),
                             GB.heart_drop(d, 0.66, 0.16, 0.018)])
    glow(c, drops, (140, 220, 255, 255), 6, 1.3)
    fill(c, soften(drops), (220, 245, 255, 255))
    scroll(c, (30, 70, 140, 255))
    return finish(c)


# ---- NIN: other ninjutsu --------------------------------------------------------------------------------------------
def jubaku():
    """A sacred rope knotted tight, paralysis sparks crackling along it."""
    c = bg((170, 160, 40), (26, 24, 2), 0.5, 0.48)
    rope = mask()
    rd = ImageDraw.Draw(rope)
    for k in range(2):
        seq = [(0.10 + 0.80 * t, 0.50 + 0.10 * math.sin(t * math.pi * 4 + k * math.pi)) for t in
               [i / 60 for i in range(61)]]
        rd.polygon(pts(stroke(seq, 0.07, 0.07)), fill=255)
    loop = shape(lambda d: d.polygon(pts(stroke(arc(0.5, 0.36, 0.14, 0, 360, 40), 0.06, 0.06)), fill=255))
    rope = lighter(rope, loop)
    glow(c, rope, (255, 255, 160, 255), 12, 1.2)
    shadow(c, rope, 4, 7, 6, 160)
    fill(c, soften(rope), linear((255, 240, 200, 255), (190, 150, 90, 255), 90))
    twist = shape(lambda d: [d.line(pts([(x, 0.44), (x + 0.04, 0.56)]), fill=255, width=int(0.008 * W))
                             for x in [0.12 + 0.06 * i for i in range(13)]])
    fill(c, soften(ImageChops.multiply(twist, rope)).point(lambda v: int(v * 0.5)), (120, 80, 30, 255))
    zig = shape(lambda d: [d.line(pts([(0.18, 0.24), (0.24, 0.32), (0.20, 0.36), (0.28, 0.42)]), fill=255,
                                  width=int(0.016 * W), joint='curve'),
                           d.line(pts([(0.80, 0.70), (0.74, 0.76), (0.80, 0.80), (0.72, 0.88)]), fill=255,
                                  width=int(0.016 * W), joint='curve'),
                           d.line(pts([(0.74, 0.18), (0.70, 0.26), (0.76, 0.28), (0.70, 0.36)]), fill=255,
                                  width=int(0.014 * W), joint='curve')])
    glow(c, zig, (255, 255, 120, 255), 8, 1.6)
    fill(c, soften(zig), (255, 255, 230, 255))
    paper = shape(lambda d: [d.polygon(pts([(0.46, 0.60), (0.54, 0.60), (0.52, 0.70), (0.56, 0.78), (0.48, 0.78),
                                            (0.50, 0.70)]), fill=255)])
    fill(c, soften(paper), (255, 255, 250, 255))
    return finish(c)


def hojo():
    """A snail crawling on: the ninja's slow."""
    c = bg((150, 80, 170), (22, 6, 30), 0.5, 0.48)
    body = shape(lambda d: [d.polygon(pts(stroke([(0.10, 0.74), (0.40, 0.76), (0.70, 0.74), (0.82, 0.62),
                                                  (0.84, 0.50)], 0.10, 0.08)), fill=255),
                            d.line(pts([(0.82, 0.52), (0.80, 0.36)]), fill=255, width=int(0.016 * W)),
                            d.line(pts([(0.86, 0.52), (0.92, 0.38)]), fill=255, width=int(0.016 * W)),
                            d.ellipse(pts([(0.77, 0.33), (0.83, 0.39)]), fill=255),
                            d.ellipse(pts([(0.89, 0.35), (0.95, 0.41)]), fill=255)])
    glow(c, body, (255, 210, 240, 255), 12, 1.2)
    shadow(c, body, 4, 7, 6, 160)
    fill(c, soften(body), linear((230, 210, 190, 255), (150, 120, 110, 255), 90))
    shell = shape(lambda d: d.ellipse(pts([(0.22, 0.30), (0.66, 0.74)]), fill=255))
    shadow(c, shell, 5, 8, 7, 170)
    fill(c, soften(shell), radial((240, 170, 255, 255), (110, 40, 140, 255), 0.40, 0.44, 0.28))
    sp = shape(lambda d: d.polygon(pts(stroke([(0.44 + math.cos(a) * r, 0.52 + math.sin(a) * r)
                                               for a, r in [(math.radians(200 + 640 * i / 50), 0.19 * (1 - i / 50) + 0.01)
                                                            for i in range(51)]], 0.03, 0.008)), fill=255))
    fill(c, soften(sp), (60, 10, 80, 255))
    trail = shape(lambda d: d.line(pts([(0.02, 0.82), (0.20, 0.82)]), fill=255, width=int(0.012 * W)))
    fill(c, soften(trail, 3).point(lambda v: int(v * 0.5)), (230, 210, 255, 255))
    return finish(c)


def kurayami():
    """An eye swallowed by a band of black smoke: blindness."""
    c = bg((90, 100, 120), (8, 8, 14), 0.5, 0.5)
    eye = shape(lambda d: GC.eye_shape(d, 0.5, 0.48, 0.34, 0.18))
    glow(c, eye, (200, 210, 230, 255), 16, 1.0)
    fill(c, soften(eye), linear((240, 240, 236, 255), (180, 180, 176, 255), 90))
    iris = shape(lambda d: d.ellipse(pts([(0.39, 0.37), (0.61, 0.59)]), fill=255))
    fill(c, soften(iris), radial((170, 120, 60, 255), (60, 30, 10, 255), 0.5, 0.48, 0.11))
    rnd = random.Random(171)
    smoke = mask()
    sd = ImageDraw.Draw(smoke)
    for _ in range(26):
        x, y, r = rnd.uniform(0.06, 0.94), rnd.uniform(0.38, 0.58), rnd.uniform(0.05, 0.09)
        sd.ellipse(pts([(x - r, y - r * 0.7), (x + r, y + r * 0.7)]), fill=255)
    smoke = smoke.filter(ImageFilter.GaussianBlur(10))
    glow(c, smoke, (120, 90, 160, 255), 14, 0.6)
    fill(c, smoke, (6, 4, 12, 255))
    wisps = shape(lambda d: [d.polygon(pts(stroke([(0.20, 0.40), (0.14, 0.30), (0.22, 0.20)], 0.06, 0.01)), fill=255),
                             d.polygon(pts(stroke([(0.76, 0.58), (0.84, 0.70), (0.76, 0.80)], 0.06, 0.01)),
                                       fill=255)])
    fill(c, soften(wisps, 4), (10, 6, 16, 255))
    return finish(c)


def dokumori():
    """A kunai dripping green venom: poison."""
    c = bg((90, 150, 70), (8, 24, 6), 0.5, 0.45)
    bubbles = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), outline=255, width=int(0.010 * W))
                               for x, y, r in ((0.24, 0.30, 0.04), (0.78, 0.66, 0.05), (0.20, 0.64, 0.03),
                                               (0.70, 0.22, 0.03))])
    fill(c, soften(bubbles), (200, 255, 160, 255))
    kn = shape(lambda d: [d.polygon(xf([(0, -0.40), (0.08, -0.10), (0.04, 0.06), (-0.04, 0.06), (-0.08, -0.10)],
                                       0.50, 0.50, 1.0, 35), fill=255),
                          d.polygon(xf([(-0.025, 0.06), (0.025, 0.06), (0.025, 0.26), (-0.025, 0.26)], 0.50, 0.50,
                                       1.0, 35), fill=255),
                          d.polygon(xf(stroke(arc(0, 0.32, 0.06, -90, 270, 30), 0.025, 0.025), 0.50, 0.50, 1.0, 35),
                                    fill=255)])
    glow(c, kn, (180, 255, 120, 255), 14, 1.2)
    shadow(c, kn, 5, 8, 7, 160)
    fill(c, soften(kn), GB.metal((240, 250, 240, 255), (100, 110, 110, 255)))
    venom = ImageChops.multiply(kn, shape(lambda d: d.polygon(xf([(-0.2, -0.45), (0.2, -0.45), (0.2, -0.16),
                                                                   (-0.2, -0.24)], 0.50, 0.50, 1.0, 35),
                                                                fill=255)))
    fill(c, soften(venom), linear((200, 255, 120, 255), (60, 170, 40, 255), 90))
    drops = shape(lambda d: [GB.heart_drop(d, 0.74, 0.40, 0.035), GB.heart_drop(d, 0.80, 0.56, 0.025)])
    glow(c, drops, (160, 255, 90, 255), 8, 1.4)
    fill(c, soften(drops), linear((220, 255, 160, 255), (80, 190, 40, 255), 90))
    wrap = shape(lambda d: [d.line(xf([(-0.03, y), (0.03, y + 0.03)], 0.50, 0.50, 1.0, 35), fill=255,
                                   width=int(0.010 * W)) for y in (0.10, 0.15, 0.20)])
    fill(c, soften(wrap), (140, 40, 40, 255))
    return finish(c)


def tonko():
    """A ninja fading away into the air: invisibility."""
    c = bg((50, 150, 160), (2, 24, 28), 0.5, 0.45)
    rnd = random.Random(181)
    dots = mask()
    dd = ImageDraw.Draw(dots)
    for _ in range(60):
        x, y = rnd.uniform(0.25, 0.85), rnd.uniform(0.14, 0.90)
        r = rnd.uniform(0.006, 0.016)
        dd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    ninja = shape(lambda d: K.figure(d, 0.54, 0.54, 0.92))
    fade = linear((255, 255, 255, 255), (0, 0, 0, 255), 0).convert('L')
    body = ImageChops.multiply(ninja, fade)
    outline = ImageChops.subtract(ninja.filter(ImageFilter.MaxFilter(9)), ninja)
    glow(c, ninja, (190, 255, 250, 255), 12, 0.9)
    glow(c, outline, (200, 255, 250, 255), 6, 1.4)
    fill(c, soften(outline, 1.5), (230, 255, 250, 255))
    fill(c, soften(body), linear((20, 50, 60, 255), (6, 16, 20, 255), 90))
    fill(c, soften(ImageChops.multiply(dots, ImageChops.invert(fade))), (220, 255, 250, 255))
    return finish(c)


def monomi():
    """Split-toed tabi prints stealing off into the night: sneak."""
    c = bg((70, 80, 150), (6, 6, 26), 0.5, 0.45)

    def tabi(d, cx, cy, s, ang):
        d.polygon(xf(ell(0, 0.12, 0.05, 0.065), cx, cy, s, ang), fill=255)                         # heel
        d.polygon(xf([(-0.05, 0.12), (-0.07, -0.01), (0.075, -0.01), (0.05, 0.12)], cx, cy, s, ang), fill=255)
        d.polygon(xf(ell(0.003, -0.01, 0.073, 0.045), cx, cy, s, ang), fill=255)                   # ball
        d.polygon(xf(ell(-0.050, -0.115, 0.028, 0.045), cx, cy, s, ang), fill=255)                 # big toe
        d.polygon(xf(ell(0.028, -0.105, 0.050, 0.045), cx, cy, s, ang), fill=255)                  # the other four
    for (x, y, s, ang, a) in ((0.65, 0.33, 1.5, 14, 0.6), (0.38, 0.64, 2.0, -14, 1.0)):
        fp = shape(lambda d, x=x, y=y, s=s, ang=ang: tabi(d, x, y, s, ang))
        cut = shape(lambda d, x=x, y=y, s=s, ang=ang: [
            d.polygon(xf(stroke([(-0.09, -0.065), (0.10, -0.065)], 0.022, 0.022), x, y, s, ang), fill=255),
            d.polygon(xf(stroke([(-0.018, -0.07), (-0.018, -0.17)], 0.018, 0.018), x, y, s, ang), fill=255)])
        fp = ImageChops.subtract(fp, cut)
        if a == 1.0:
            shadow(c, fp, 4, 7, 6, 170)
        glow(c, fp, (170, 180, 255, 255), 9, 1.3 * a)
        fill(c, soften(fp).point(lambda v, a=a: int(v * a)), linear((255, 255, 255, 255), (196, 204, 250, 255), 90))
    stars(c, [(0.80, 0.68, 0.05), (0.22, 0.26, 0.04)])
    return finish(c)


def gekka():
    """A blood-red full moon with a ninja crow across it: the ninjutsu that draws enmity."""
    c = bg((180, 40, 40), (24, 2, 6), 0.5, 0.42)
    moon = shape(lambda d: d.ellipse(pts([(0.18, 0.14), (0.82, 0.78)]), fill=255))
    glow(c, moon, (255, 90, 70, 255), 30, 1.4)
    fill(c, soften(moon), radial((255, 220, 180, 255), (230, 70, 50, 255), 0.44, 0.38, 0.36))
    ninja = shape(lambda d: K.figure(d, 0.50, 0.50, 0.92))
    glow(c, ninja, (255, 200, 160, 255), 8, 1.2)
    fill(c, soften(ninja), linear((40, 10, 14, 255), (10, 2, 4, 255), 90))
    bang = shape(lambda d: [d.rounded_rectangle(pts([(0.80, 0.10), (0.86, 0.30)]), radius=0.02 * W, fill=255),
                            d.ellipse(pts([(0.80, 0.33), (0.86, 0.39)]), fill=255)])
    glow(c, bang, (255, 80, 60, 255), 8, 1.6)
    fill(c, soften(bang), (255, 245, 220, 255))
    return finish(c)


def yain():
    """A moon eclipsed to a thin ring, mist drifting over it: the ninjutsu that sheds enmity."""
    c = bg((60, 70, 100), (4, 4, 12), 0.5, 0.42)
    ring = shape(lambda d: d.ellipse(pts([(0.24, 0.18), (0.76, 0.70)]), fill=255))
    glow(c, ring, (180, 200, 255, 255), 24, 1.5)
    fill(c, soften(ring), (220, 230, 255, 255))
    disc = shape(lambda d: d.ellipse(pts([(0.255, 0.195), (0.745, 0.685)]), fill=255))
    fill(c, soften(disc, 2), radial((14, 14, 24, 255), (4, 4, 10, 255), 0.5, 0.44, 0.24))
    rnd = random.Random(191)
    mist = mask()
    md = ImageDraw.Draw(mist)
    for _ in range(14):
        x, y, r = rnd.uniform(0.05, 0.95), rnd.uniform(0.60, 0.92), rnd.uniform(0.07, 0.12)
        md.ellipse(pts([(x - r, y - r * 0.4), (x + r, y + r * 0.4)]), fill=150)
    fill(c, mist.filter(ImageFilter.GaussianBlur(12)), (150, 170, 210, 255))
    dn = shape(lambda d: d.polygon(pts([(0.47, 0.30), (0.53, 0.30), (0.53, 0.46), (0.58, 0.46), (0.50, 0.56),
                                        (0.42, 0.46), (0.47, 0.46)]), fill=255))
    glow(c, dn, (160, 190, 255, 255), 8, 1.2)
    fill(c, soften(dn), (200, 214, 255, 255))
    return finish(c)


def myoshu():
    """A slender needle flicked true, a pinpoint glint where it strikes: subtle blow."""
    c = bg((60, 170, 140), (2, 26, 22), 0.5, 0.45)
    GC.streaks(c, [(0.06, 0.92, 0.36, 0.62), (0.16, 0.96, 0.42, 0.70), (0.02, 0.80, 0.30, 0.56)],
               (200, 255, 240, 255), 0.010, 140)
    nd = shape(lambda d: [d.polygon(pts(stroke([(0.22, 0.80), (0.74, 0.28)], 0.03, 0.004)), fill=255),
                          d.polygon(pts(stroke([(0.20, 0.82), (0.30, 0.72)], 0.05, 0.05)), fill=255)])
    glow(c, nd, (210, 255, 240, 255), 10, 1.4)
    shadow(c, nd, 4, 6, 6, 150)
    fill(c, soften(nd), GB.metal())
    ring = shape(lambda d: d.ellipse(pts([(0.66, 0.20), (0.84, 0.38)]), outline=255, width=int(0.012 * W)))
    glow(c, ring, (200, 255, 230, 255), 6)
    fill(c, soften(ring), (230, 255, 245, 255))
    stars(c, [(0.75, 0.29, 0.11)], (180, 255, 230, 255))
    return finish(c)


def yurin():
    """Bamboo stalks closing in, leaves whirling: the ninjutsu that stifles a foe's TP."""
    c = bg((100, 150, 60), (8, 22, 6), 0.5, 0.5)
    stalks = mask()
    sd = ImageDraw.Draw(stalks)
    for x, w in ((0.20, 0.07), (0.38, 0.08), (0.62, 0.08), (0.80, 0.07)):
        sd.rounded_rectangle(pts([(x - w / 2, -0.1), (x + w / 2, 1.1)]), radius=0.02 * W, fill=255)
    shadow(c, stalks, 4, 7, 6, 150)
    fill(c, soften(stalks), linear((200, 240, 140, 255), (70, 130, 40, 255), 0))
    nodes = shape(lambda d: [d.rectangle(pts([(x - 0.045, y), (x + 0.045, y + 0.014)]), fill=255)
                             for x, ys in ((0.20, (0.26, 0.62)), (0.38, (0.16, 0.52, 0.86)), (0.62, (0.32, 0.70)),
                                           (0.80, (0.20, 0.56))) for y in ys])
    fill(c, soften(ImageChops.multiply(nodes, stalks)), (60, 100, 30, 255))
    lv = shape(lambda d: [leaf(d, 0.5 + math.cos(a) * 0.20, 0.5 + math.sin(a) * 0.20, 0.13, 0.04,
                               math.degrees(a) + 100) for a in [math.pi * 2 * i / 5 for i in range(5)]])
    glow(c, lv, (220, 255, 170, 255), 10, 1.3)
    fill(c, soften(lv), linear((230, 255, 190, 255), (110, 190, 70, 255), 90))
    sw = shape(lambda d: d.polygon(pts(stroke(arc(0.5, 0.5, 0.12, 0, 300, 30), 0.006, 0.03)), fill=255))
    fill(c, soften(sw), (240, 255, 220, 255))
    return finish(c)


def kakka():
    """A paper lantern glowing ever brighter: the ninjutsu that stores TP."""
    c = bg((210, 120, 40), (40, 14, 2), 0.5, 0.5)
    lan = shape(lambda d: d.ellipse(pts([(0.28, 0.24), (0.72, 0.80)]), fill=255))
    glow(c, lan, (255, 180, 80, 255), 34, 1.4)
    fill(c, soften(lan), radial((255, 250, 210, 255), (240, 110, 40, 255), 0.5, 0.52, 0.26))
    ribs = shape(lambda d: [d.line(pts([(0.5 - math.sqrt(max(0, 1 - ((y - 0.52) / 0.28) ** 2)) * 0.22, y),
                                        (0.5 + math.sqrt(max(0, 1 - ((y - 0.52) / 0.28) ** 2)) * 0.22, y)]),
                                   fill=255, width=int(0.008 * W)) for y in (0.32, 0.40, 0.48, 0.56, 0.64, 0.72)])
    fill(c, soften(ribs).point(lambda v: int(v * 0.5)), (170, 60, 20, 255))
    caps = shape(lambda d: [d.rounded_rectangle(pts([(0.38, 0.20), (0.62, 0.27)]), radius=0.02 * W, fill=255),
                            d.rounded_rectangle(pts([(0.38, 0.77), (0.62, 0.84)]), radius=0.02 * W, fill=255),
                            d.line(pts([(0.5, 0.06), (0.5, 0.20)]), fill=255, width=int(0.012 * W))])
    shadow(c, caps, 3, 5, 5, 150)
    fill(c, soften(caps), linear((60, 40, 30, 255), (20, 12, 8, 255), 90))
    mark = shape(lambda d: [sparkle(d, 0.5, 0.52, 0.09)])
    glow(c, mark, (255, 255, 220, 255), 10, 1.6)
    fill(c, soften(mark), (255, 255, 250, 255))
    motes(c, 201, 12, (0.18, 0.10, 0.82, 0.90), (0.005, 0.012), (255, 200, 100, 255))
    return finish(c)


def migawari():
    """A straw substitute doll, a blade lodged in it in your place."""
    c = bg((170, 140, 70), (28, 20, 6), 0.5, 0.45)
    doll = shape(lambda d: [d.ellipse(pts([(0.38, 0.12), (0.58, 0.32)]), fill=255),
                            d.polygon(pts([(0.40, 0.30), (0.56, 0.30), (0.60, 0.70), (0.36, 0.70)]), fill=255),
                            d.polygon(pts([(0.24, 0.38), (0.72, 0.38), (0.72, 0.44), (0.24, 0.44)]), fill=255),
                            d.polygon(pts([(0.38, 0.68), (0.46, 0.68), (0.40, 0.90), (0.32, 0.90)]), fill=255),
                            d.polygon(pts([(0.50, 0.68), (0.58, 0.68), (0.64, 0.90), (0.56, 0.90)]), fill=255)])
    glow(c, doll, (255, 240, 170, 255), 14, 1.2)
    shadow(c, doll, 5, 8, 7, 170)
    fill(c, soften(doll), linear((250, 220, 140, 255), (170, 120, 50, 255), 90))
    straw = mask()
    sd = ImageDraw.Draw(straw)
    rnd = random.Random(211)
    for _ in range(40):
        x, y = rnd.uniform(0.24, 0.72), rnd.uniform(0.14, 0.90)
        sd.line(pts([(x, y), (x + rnd.uniform(-0.01, 0.01), y + 0.05)]), fill=255, width=int(0.006 * W))
    fill(c, soften(ImageChops.multiply(straw, doll)).point(lambda v: int(v * 0.5)), (120, 80, 20, 255))
    ties = shape(lambda d: [d.rectangle(pts([(0.38, 0.32), (0.58, 0.35)]), fill=255),
                            d.rectangle(pts([(0.37, 0.60), (0.59, 0.63)]), fill=255)])
    fill(c, soften(ties), (180, 30, 30, 255))
    kn = shape(lambda d: GB.draw_dagger(d, 0.66, 0.42, 0.80, -60))
    glow(c, kn, (255, 255, 230, 255), 8, 1.2)
    shadow(c, kn, 4, 6, 6, 160)
    fill(c, soften(kn), GB.metal())
    hilt = shape(lambda d: GB.draw_dagger(d, 0.66, 0.42, 0.80, -60, (1, 2, 3)))
    fill(c, soften(hilt), linear((80, 50, 40, 255), (20, 12, 10, 255), 90))
    return finish(c)


def aisha():
    """A blade snapped in two, a down-arrow: the ninjutsu that saps a foe's attack."""
    c = bg((170, 60, 50), (28, 6, 4), 0.5, 0.45)
    hilt_part = shape(lambda d: [d.polygon(xf([(-0.04, -0.06), (0.04, -0.06), (0.03, 0.12), (-0.04, 0.12)], 0.40,
                                              0.58, 1.0, 30), fill=255),
                                 d.polygon(xf([(-0.13, 0.12), (0.13, 0.12), (0.11, 0.17), (-0.11, 0.17)], 0.40, 0.58,
                                              1.0, 30), fill=255),
                                 d.polygon(xf([(-0.025, 0.17), (0.025, 0.17), (0.025, 0.34), (-0.025, 0.34)], 0.40,
                                              0.58, 1.0, 30), fill=255)])
    tip_part = shape(lambda d: d.polygon(xf([(-0.04, -0.10), (0.04, -0.12), (0.045, 0.14), (0, 0.26),
                                             (-0.045, 0.14)], 0.62, 0.28, 1.0, 210), fill=255))
    both = lighter(hilt_part, tip_part)
    glow(c, both, (255, 200, 170, 255), 10, 1.2)
    shadow(c, both, 4, 7, 6, 160)
    fill(c, soften(both), GB.metal((245, 245, 250, 255), (130, 130, 145, 255)))
    grip = shape(lambda d: d.polygon(xf([(-0.13, 0.12), (0.13, 0.12), (0.11, 0.17), (-0.11, 0.17)], 0.40, 0.58, 1.0,
                                        30), fill=255))
    fill(c, soften(grip), GB.gold())
    burst = shape(lambda d: sparkle(d, 0.52, 0.44, 0.10))
    glow(c, burst, (255, 200, 140, 255), 10, 1.5)
    fill(c, soften(burst), (255, 250, 230, 255))
    dn = shape(lambda d: d.polygon(pts([(0.76, 0.48), (0.84, 0.48), (0.84, 0.66), (0.90, 0.66), (0.80, 0.80),
                                        (0.70, 0.66), (0.76, 0.66)]), fill=255))
    glow(c, dn, (255, 100, 80, 255), 10, 1.4)
    fill(c, soften(dn), linear((255, 230, 220, 255), (230, 80, 60, 255), 90))
    return finish(c)


# ---- registry -------------------------------------------------------------------------------------------------------
ICONS = {
    ('ma', 'Foe Requiem'): foe_requiem,
    ('ma', 'Horde Lullaby'): horde_lullaby,
    ('ma', "Army's Paeon"): armys_paeon,
    ('ma', "Knight's Minne"): knights_minne,
    ('ma', 'Sword Madrigal'): madrigal(False),
    ('ma', 'Blade Madrigal'): madrigal(True),
    ('ma', "Hunter's Prelude"): prelude(False),
    ('ma', "Archer's Prelude"): prelude(True),
    ('ma', 'Sheepfoe Mambo'): mambo(False),
    ('ma', 'Dragonfoe Mambo'): mambo(True),
    ('ma', 'Fowl Aubade'): fowl_aubade,
    ('ma', 'Herb Pastoral'): herb_pastoral,
    ('ma', 'Chocobo Hum'): chocobo_hum,
    ('ma', 'Shining Fantasia'): shining_fantasia,
    ('ma', "Scop's Operetta"): scops_operetta,
    ('ma', "Puppet's Operetta"): puppets_operetta,
    ('ma', "Jester's Operetta"): jesters_operetta,
    ('ma', 'Gold Capriccio'): gold_capriccio,
    ('ma', 'Devotee Serenade'): devotee_serenade,
    ('ma', 'Warding Round'): warding_round,
    ('ma', 'Goblin Gavotte'): goblin_gavotte,
    ('ma', 'Cactuar Fugue'): cactuar_fugue,
    ('ma', 'Honor March'): honor_march,
    ('ma', 'Aria of Passion'): aria_of_passion,
    ('ma', 'Victory March'): victory_march,
    ('ma', 'Battlefield Elegy'): elegy(1),
    ('ma', 'Carnage Elegy'): elegy(2),
    ('ma', 'Massacre Elegy'): elegy(3),
    ('ma', 'Sinewy Etude'): etude(False),
    ('ma', 'Herculean Etude'): etude(True),
    ('ma', 'Fire Carol'): carol,
    ('ma', 'Fire Threnody'): threnody,
    ('ma', 'Magic Finale'): magic_finale,
    ("ma", "Goddess's Hymnus"): goddess_hymnus,
    ('ma', 'Chocobo Mazurka'): chocobo_mazurka,
    ("ma", "Maiden's Virelai"): maidens_virelai,
    ('ma', 'Raptor Mazurka'): raptor_mazurka,
    ('ma', 'Foe Sirvente'): foe_sirvente,
    ("ma", "Adventurer's Dirge"): adventurers_dirge,
    ("ma", "Sentinel's Scherzo"): sentinels_scherzo,
    ('ma', 'Pining Nocturne'): pining_nocturne,
    ('ma', 'Fire Spirit'): spirit,
    ('ma', 'Fenrir'): fenrir,
    ('ma', 'Titan'): titan,
    ('ma', 'Leviathan'): leviathan,
    ('ma', 'Ramuh'): ramuh,
    ('ma', 'Diabolos'): diabolos,
    ('ma', 'Odin'): odin,
    ('ma', 'Alexander'): alexander,
    ('ma', 'Cait Sith'): cait_sith,
    ('ma', 'Siren'): siren,
    ('ma', 'Atomos'): atomos,
    ('ma', 'Hyoton'): hyoton,
    ('ma', 'Huton'): huton,
    ('ma', 'Doton'): doton,
    ('ma', 'Raiton'): raiton,
    ('ma', 'Suiton'): suiton,
    ('ma', 'Jubaku'): jubaku,
    ('ma', 'Hojo'): hojo,
    ('ma', 'Kurayami'): kurayami,
    ('ma', 'Dokumori'): dokumori,
    ('ma', 'Tonko'): tonko,
    ('ma', 'Monomi'): monomi,
    ('ma', 'Gekka'): gekka,
    ('ma', 'Yain'): yain,
    ('ma', 'Myoshu'): myoshu,
    ('ma', 'Yurin'): yurin,
    ('ma', 'Kakka'): kakka,
    ('ma', 'Migawari'): migawari,
    ('ma', 'Aisha'): aisha,
}
COVERS = {}

# Element hues (bases painted at ~8, fire): shift = target - 8.
_ELEM = {'Fire': None, 'Earth': K.EARTH, 'Light': K.LIGHT, 'Wind': 112, 'Ice': 182, 'Water': 217, 'Thunder': K.THUNDER,
         'Dark': K.DARK}
_STAT = {'STR': None, 'DEX': _ELEM['Thunder'], 'VIT': _ELEM['Earth'], 'AGI': _ELEM['Wind'], 'INT': _ELEM['Ice'],
         'MND': _ELEM['Water'], 'CHR': _ELEM['Light']}
VARIANTS = {
    'Sinewy Etude': {'Sinewy Etude': _STAT['STR'], 'Dextrous Etude': _STAT['DEX'], 'Vivacious Etude': _STAT['VIT'],
                     'Quick Etude': _STAT['AGI'], 'Learned Etude': _STAT['INT'], 'Spirited Etude': _STAT['MND'],
                     'Enchanting Etude': _STAT['CHR']},
    'Herculean Etude': {'Herculean Etude': _STAT['STR'], 'Uncanny Etude': _STAT['DEX'], 'Vital Etude': _STAT['VIT'],
                        'Swift Etude': _STAT['AGI'], 'Sage Etude': _STAT['INT'], 'Logical Etude': _STAT['MND'],
                        'Bewitching Etude': _STAT['CHR']},
    'Fire Carol': {'Fire Carol': _ELEM['Fire'], 'Ice Carol': _ELEM['Ice'], 'Wind Carol': _ELEM['Wind'],
                   'Earth Carol': _ELEM['Earth'], 'Lightning Carol': _ELEM['Thunder'], 'Water Carol': _ELEM['Water'],
                   'Light Carol': _ELEM['Light'], 'Dark Carol': _ELEM['Dark']},
    'Fire Threnody': {'Fire Threnody': _ELEM['Fire'], 'Ice Threnody': _ELEM['Ice'], 'Wind Threnody': _ELEM['Wind'],
                      'Earth Threnody': _ELEM['Earth'], 'Ltng. Threnody': _ELEM['Thunder'],
                      'Water Threnody': _ELEM['Water'], 'Light Threnody': _ELEM['Light'],
                      'Dark Threnody': _ELEM['Dark']},
    'Fire Spirit': {'Fire Spirit': _ELEM['Fire'], 'Ice Spirit': _ELEM['Ice'], 'Air Spirit': _ELEM['Wind'],
                    'Earth Spirit': _ELEM['Earth'], 'Thunder Spirit': _ELEM['Thunder'],
                    'Water Spirit': _ELEM['Water'], 'Light Spirit': _ELEM['Light'], 'Dark Spirit': _ELEM['Dark']},
}
NAMES = [n for _, n in ICONS]
