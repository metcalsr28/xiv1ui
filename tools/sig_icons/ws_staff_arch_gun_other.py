"""Signature icons, round 2: staff, archery and marksmanship weapon skills, plus the later weapon skills of
assorted weapons (prime, merit, empyrean/relic/mythic, campaign and the NPC-only ones)."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_b as GB
import group_c as GC
import group_d as GD

p, pts, W = K.p, K.pts, K.W
mask, shape, fill, glow, shadow, soften, finish = K.mask, K.shape, K.fill, K.glow, K.shadow, K.soften, K.finish
lit, poly, ell, scale, minus, rot, col = GD.lit, GD.poly, GD.ell, GD.scale, GD.minus, GD.rot, GD.col
frame, tstroke, arc, sparkles, motes, rays, brush = GC.frame, GC.stroke, GC.arc, GD.sparkles, GD.motes, GD.rays, GD.stroke


# ---- helpers ---------------------------------------------------------------------------------------------------------
def bg(c0, c1, cx=0.5, cy=0.45, r=0.72):
    return K.radial(c0 + (255,), c1 + (255,), cx, cy, r)


def lin(c0, c1, angle=90):
    return K.linear(col(c0), col(c1), angle)


def rad(c0, c1, cx=0.5, cy=0.5, r=0.4):
    return K.radial(col(c0), col(c1), cx, cy, r)


def T0(seq, cx, cy, s=1.0, ang=0.0):
    """Local points -> unit points: scale s, rotate ang degrees (clockwise on screen), move to (cx, cy)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in seq]


T = T0


def lighter(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def keyline(c, m, px=9, color=(14, 10, 24, 235)):
    """A dark outline under a slim weapon so it separates from a busy field at bar size."""
    fill(c, soften(m.filter(ImageFilter.MaxFilter(px)), 2), color)


def star_poly(cx, cy, n, ro, ri, rot0=-90):
    q = []
    for i in range(n * 2):
        a = math.radians(rot0) + math.pi * i / n
        r = ro if i % 2 == 0 else ri
        q.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return q


def burst(c, cx, cy, ro, ri, n, inner, outer, glowc, gr=22, gs=1.3, rot0=-90):
    m = poly(star_poly(cx, cy, n, ro, ri, rot0))
    glow(c, m, col(glowc), gr, gs)
    fill(c, soften(m), rad(inner, outer, cx, cy, ro))
    return m


def swoosh(c, cx, cy, r, a0, a1, w, color, alpha=1.0, glowc=None, ry=None):
    """A motion arc: tapered from nothing at a0 to w at a1."""
    m = poly(tstroke(arc(cx, cy, r, a0, a1, 48, ry), 0.0, w))
    if glowc:
        glow(c, m, col(glowc), 12, 1.0)
    fill(c, scale(soften(m, 2), alpha), col(color))
    return m


def ring(cx, cy, r, w, ry=None):
    ry = r if ry is None else ry
    return shape(lambda d: d.ellipse(pts([(cx - r, cy - ry), (cx + r, cy + ry)]), outline=255, width=max(1, int(w * W))))


def disc(cx, cy, r, ry=None):
    ry = r if ry is None else ry
    return ell(cx - r, cy - ry, cx + r, cy + ry)


def streaks(c, lines, color, width=0.012, alpha=150, blur=3):
    GC.streaks(c, lines, col(color), width, alpha, blur)


def metal(c, m, top=(255, 255, 255), bot=(140, 150, 175), angle=90):
    fill(c, soften(m), lin(top, bot, angle))


GOLD = ((255, 236, 160), (176, 112, 36))
WOOD = ((176, 112, 60), (84, 46, 22))
STEEL = ((255, 255, 255), (140, 150, 175))
GUNMETAL = ((150, 156, 176), (44, 46, 60))


def skull_eyes(cx, cy, s, grow=1.0):
    """The eye sockets of group_b's skull at (cx, cy), scale s."""
    r = 0.085 * s * grow
    return lighter(disc(cx - 0.12 * s, cy + 0.02 * s, r, r * 1.06), disc(cx + 0.12 * s, cy + 0.02 * s, r, r * 1.06))


# ---- staves ----------------------------------------------------------------------------------------------------------
def staff_masks(x0, y0, x1, y1, w=0.046, head='claw', orb_r=0.07):
    """A mage's staff from the butt (x0, y0) to the head (x1, y1). Returns (shaft, fittings, orb, orb centre)."""
    L, f = frame(x0, y0, x1, y1)
    shaft = poly([f(0, -w * 0.35), f(L - 0.05, -w / 2), f(L - 0.05, w / 2), f(0, w * 0.35)])
    fit = shape(lambda d: [d.polygon(pts([f(L - 0.10, -w * 0.62), f(L - 0.06, -w * 0.62), f(L - 0.06, w * 0.62),
                                          f(L - 0.10, w * 0.62)]), fill=255),
                           d.polygon(pts([f(0.0, -w * 0.5), f(0.05, -w * 0.5), f(0.05, w * 0.5), f(0.0, w * 0.5)]),
                                     fill=255)])
    oc = f(L + orb_r * 0.6, 0)
    if head == 'claw':
        claws = shape(lambda d: [d.polygon(pts(tstroke([f(L - 0.07, s * 0.02), f(L - 0.02, s * 0.075),
                                                        f(L + 0.06, s * (orb_r + 0.035)),
                                                        f(L + 0.13, s * (orb_r + 0.005)),
                                                        f(L + 0.16, s * 0.012)], 0.034, 0.012)), fill=255)
                                 for s in (-1, 1)])
        fit = lighter(fit, claws)
    elif head == 'knob':
        oc = f(L - 0.02, 0)
        fit = lighter(fit, disc(*f(0.0, 0), w * 0.75))
    orb = disc(oc[0], oc[1], orb_r)
    return shaft, fit, orb, oc


def paint_staff(c, x0, y0, x1, y1, orb=((255, 255, 240), (120, 170, 255)), orb_glow=(150, 200, 255), w=0.046,
                head='claw', orb_r=0.07, wood=WOOD, gold=GOLD, glowc=None, sh=True):
    shaft, fit, o, oc = staff_masks(x0, y0, x1, y1, w, head, orb_r)
    whole = lighter(shaft, fit, o)
    if glowc:
        glow(c, whole, col(glowc), 14, 1.1)
    if sh:
        shadow(c, whole, 5, 8, 8, 150)
    fill(c, soften(shaft), lin(wood[0], wood[1], 0))
    fill(c, soften(fit), lin(gold[0], gold[1], 90))
    if head != 'knob':
        glow(c, o, col(orb_glow), 16, 1.6)
        fill(c, soften(o), rad(orb[0], orb[1], oc[0] - orb_r * 0.3, oc[1] - orb_r * 0.3, orb_r * 1.4))
        hi = disc(oc[0] - orb_r * 0.35, oc[1] - orb_r * 0.35, orb_r * 0.25)
        fill(c, soften(hi, 2), (255, 255, 255, 220))
    return oc


def heavy_swing():
    c = bg((196, 128, 50), (34, 16, 6), 0.55, 0.40)
    swoosh(c, 0.50, 0.58, 0.34, 150, 290, 0.12, (255, 236, 190), 0.75, (255, 200, 120))
    swoosh(c, 0.50, 0.58, 0.26, 175, 285, 0.06, (255, 236, 190), 0.5)
    burst(c, 0.74, 0.26, 0.17, 0.06, 8, (255, 255, 230), (255, 170, 60), (255, 190, 90), 18)
    paint_staff(c, 0.16, 0.90, 0.72, 0.26, head='knob', w=0.085)
    return finish(c)


def rock_crusher():
    c = bg((214, 150, 70), (40, 20, 6), 0.5, 0.40)
    rnd = random.Random(4)
    chunks = mask()
    d = ImageDraw.Draw(chunks)
    for i in range(7):
        a = math.radians(-150 + i * 40 + rnd.uniform(-10, 10))
        r = 0.22 + rnd.uniform(0, 0.08)
        x, y = 0.50 + math.cos(a) * r, 0.62 + math.sin(a) * r * 0.8
        s = rnd.uniform(0.035, 0.06)
        d.polygon(pts([(x + math.cos(t + i) * s * rnd.uniform(0.7, 1.2), y + math.sin(t + i) * s * rnd.uniform(0.7, 1.2))
                       for t in [k * math.pi * 2 / 5 for k in range(5)]]), fill=255)
    lit(c, chunks, (255, 190, 100), lin((214, 170, 120), (110, 76, 46)), 8, 1.0, sh=True)
    rock = poly([(0.30, 0.86), (0.28, 0.66), (0.40, 0.52), (0.58, 0.50), (0.72, 0.62), (0.72, 0.86)])
    shadow(c, rock, 4, 6, 6, 160)
    fill(c, soften(rock), lin((150, 120, 100), (60, 44, 36)))
    cracks = shape(lambda d: [brush(d, q, 0.018, 0.006) for q in
                              ([(0.50, 0.52), (0.47, 0.62), (0.52, 0.70), (0.46, 0.84)],
                               [(0.48, 0.60), (0.36, 0.66), (0.32, 0.76)],
                               [(0.51, 0.68), (0.64, 0.72), (0.70, 0.80)])])
    glow(c, cracks, (255, 170, 60, 255), 8, 1.5)
    fill(c, soften(cracks), (255, 230, 150, 255))
    burst(c, 0.50, 0.50, 0.14, 0.05, 8, (255, 255, 230), (255, 180, 70), (255, 200, 110), 14)
    paint_staff(c, 0.90, 0.10, 0.60, 0.42, head='knob', w=0.075, sh=True, wood=((230, 170, 100), (110, 60, 24)),
                glowc=(255, 230, 170))
    return finish(c)


def earth_crusher():
    c = bg((206, 140, 50), (40, 20, 6), 0.5, 0.62)
    ground = poly([(0, 0.62), (1, 0.62), (1, 1), (0, 1)])
    fill(c, soften(ground, 3), lin((120, 74, 34), (40, 22, 8)))
    cracks = shape(lambda d: [brush(d, [(0.5, 0.70), (0.5 + math.cos(a) * 0.20, 0.70 + math.sin(a) * 0.08),
                                         (0.5 + math.cos(a) * 0.46, 0.70 + math.sin(a) * 0.20)], 0.03, 0.008)
                              for a in [math.radians(x) for x in (-170, -10, 20, 60, 120, 160, 90)]])
    glow(c, cracks, (255, 150, 40, 255), 12, 1.6)
    fill(c, soften(cracks), (255, 226, 140, 255))
    # rocks thrown up in a ring
    rnd = random.Random(9)
    rocks = mask()
    d = ImageDraw.Draw(rocks)
    for i, (x, y) in enumerate([(0.18, 0.48), (0.30, 0.34), (0.70, 0.32), (0.82, 0.46), (0.42, 0.24), (0.60, 0.20)]):
        s = 0.065 if i < 4 else 0.045
        d.polygon(pts([(x + math.cos(k * 1.3 + i) * s * rnd.uniform(0.7, 1.2),
                        y + math.sin(k * 1.3 + i) * s * rnd.uniform(0.7, 1.2)) for k in range(5)]), fill=255)
    lit(c, rocks, (255, 190, 90), lin((230, 190, 130), (120, 80, 40)), 10, 1.0, sh=True)
    dust = shape(lambda d: d.ellipse(pts([(0.18, 0.56), (0.82, 0.80)]), fill=150))
    fill(c, dust.filter(ImageFilter.GaussianBlur(16)), (255, 200, 120, 160))
    paint_staff(c, 0.50, 0.74, 0.50, 0.20, orb=((255, 250, 210), (220, 140, 40)), orb_glow=(255, 190, 80))
    return finish(c)


def starburst():
    c = bg((70, 50, 120), (8, 4, 20), 0.5, 0.45)
    light = poly([(0, 0), (1, 0), (0, 1)])
    fill(c, scale(soften(light, 30), 0.55), (255, 214, 120, 255))
    rays(c, 0.52, 0.45, 16, (255, 240, 200), alpha=70)
    st = poly(star_poly(0.52, 0.45, 8, 0.34, 0.11, -90))
    glow(c, st, (255, 240, 200, 255), 22, 1.3)
    half_a = ImageChops.multiply(st, poly([(0, 0), (1, 0), (0, 1)]))
    half_b = ImageChops.multiply(st, poly([(1, 0), (1, 1), (0, 1)]))
    fill(c, soften(half_a), rad((255, 255, 240), (255, 190, 60), 0.52, 0.45, 0.34))
    fill(c, soften(half_b), rad((255, 220, 255), (110, 40, 170), 0.52, 0.45, 0.34))
    core = disc(0.52, 0.45, 0.06)
    glow(c, core, (255, 255, 255, 255), 14, 1.6)
    fill(c, soften(core), (255, 255, 255, 255))
    paint_staff(c, 0.14, 0.92, 0.36, 0.64, orb=((255, 255, 250), (200, 170, 255)), orb_glow=(220, 200, 255),
                orb_r=0.06)
    sparkles(c, [(0.80, 0.78, 0.06), (0.22, 0.22, 0.05)])
    return finish(c)


def sunburst():
    c = bg((236, 150, 40), (40, 10, 30), 0.5, 0.40)
    rays(c, 0.5, 0.40, 20, (255, 236, 160), alpha=90, width=0.06)
    sun = disc(0.5, 0.40, 0.21)
    glow(c, sun, (255, 210, 90, 255), 34, 1.6)
    fill(c, soften(sun), rad((255, 255, 236), (255, 170, 40), 0.5, 0.40, 0.21))
    moon = disc(0.60, 0.33, 0.15)
    shade = ImageChops.multiply(moon, sun)
    fill(c, soften(shade, 2), rad((80, 30, 110), (24, 6, 40), 0.62, 0.31, 0.16))
    rimm = minus(ring(0.60, 0.33, 0.15, 0.012), minus(mask().point(lambda v: 255), sun))
    fill(c, soften(rimm), (220, 170, 255, 200))
    paint_staff(c, 0.50, 0.96, 0.50, 0.68, orb=((255, 250, 220), (255, 160, 60)), orb_glow=(255, 200, 100),
                orb_r=0.055)
    return finish(c)


def shell_crusher():
    c = bg((40, 140, 110), (4, 24, 18), 0.5, 0.55)
    shell = shape(lambda d: d.chord(pts([(0.16, 0.38), (0.84, 1.02)]), 180, 360, fill=255))
    shadow(c, shell, 4, 8, 8, 170)
    fill(c, soften(shell), lin((150, 196, 110), (54, 92, 44)))
    plates = shape(lambda d: [d.polygon(pts(T([(math.cos(k * math.pi / 3) * 0.07,
                                                            math.sin(k * math.pi / 3) * 0.07) for k in range(6)],
                                              x, y)), outline=255, width=int(0.012 * W))
                              for x, y in ((0.50, 0.52), (0.35, 0.62), (0.65, 0.62))])
    fill(c, soften(ImageChops.multiply(plates, shell)), (36, 64, 28, 230))
    crack = shape(lambda d: [brush(d, [(0.50, 0.36), (0.46, 0.48), (0.53, 0.56), (0.47, 0.70)], 0.026, 0.008),
                             brush(d, [(0.47, 0.48), (0.36, 0.52), (0.28, 0.60)], 0.018, 0.006),
                             brush(d, [(0.53, 0.56), (0.66, 0.58)], 0.016, 0.006)])
    crack = ImageChops.multiply(crack, shell)
    glow(c, crack, (255, 240, 160, 255), 10, 1.6)
    fill(c, soften(crack), (255, 255, 220, 255))
    burst(c, 0.50, 0.36, 0.13, 0.05, 8, (255, 255, 240), (255, 220, 110), (255, 240, 170), 14)
    paint_staff(c, 0.88, 0.06, 0.58, 0.32, orb=((240, 255, 230), (80, 200, 150)), orb_glow=(150, 255, 200),
                orb_r=0.055)
    return finish(c)


def full_swing():
    c = bg((190, 40, 40), (30, 4, 8), 0.5, 0.5)
    swoosh(c, 0.5, 0.5, 0.36, -80, 250, 0.13, (255, 220, 180), 0.8, (255, 120, 80))
    swoosh(c, 0.5, 0.5, 0.25, -60, 230, 0.06, (255, 220, 180), 0.45)
    paint_staff(c, 0.16, 0.66, 0.82, 0.32, orb=((255, 250, 230), (255, 110, 60)), orb_glow=(255, 150, 100),
                head='claw', orb_r=0.06)
    sparkles(c, [(0.84, 0.82, 0.06)], glowc=(255, 180, 140))
    return finish(c)


def spirit_taker():
    c = bg((40, 70, 170), (4, 6, 30), 0.6, 0.35)
    oc = (0.66, 0.30)
    m = mask()
    d = ImageDraw.Draw(m)
    for k in range(4):
        a0 = k * 90
        path = [(oc[0] + math.cos(math.radians(a0 + t * 300)) * (0.42 - 0.34 * t),
                 oc[1] + 0.05 * (1 - t) + math.sin(math.radians(a0 + t * 300)) * (0.42 - 0.34 * t) * 0.9)
                for t in [i / 40 for i in range(41)]]
        d.polygon(pts(tstroke(path, 0.01, 0.045)), fill=200)
    glow(c, m, (120, 200, 255, 255), 12, 1.2)
    fill(c, soften(m, 2), lin((200, 240, 255), (90, 140, 255)))
    motes(c, 6, 16, (0.1, 0.1, 0.9, 0.9), (0.006, 0.013), (210, 240, 255), (120, 190, 255))
    paint_staff(c, 0.24, 0.92, 0.62, 0.36, orb=((255, 255, 255), (80, 150, 255)), orb_glow=(140, 200, 255), orb_r=0.08)
    return finish(c)


def retribution():
    c = bg((150, 20, 50), (24, 2, 10), 0.5, 0.65)
    shock = shape(lambda d: [d.ellipse(pts([(0.5 - r, 0.80 - r * 0.32), (0.5 + r, 0.80 + r * 0.32)]), outline=255,
                                       width=int(0.03 * W)) for r in (0.20, 0.34)])
    glow(c, shock, (255, 60, 80, 255), 14, 1.4)
    fill(c, soften(shock, 1.5), (255, 190, 190, 255))
    spikes = poly(star_poly(0.5, 0.80, 10, 0.30, 0.07, -90))
    spikes = ImageChops.multiply(spikes, poly([(0, 0), (1, 0), (1, 0.82), (0, 0.82)]))
    glow(c, spikes, (255, 60, 70, 255), 16, 1.3)
    fill(c, soften(spikes), lin((255, 240, 220), (220, 40, 60)))
    paint_staff(c, 0.50, 0.80, 0.50, 0.14, orb=((255, 230, 230), (210, 20, 50)), orb_glow=(255, 70, 90), orb_r=0.07,
                glowc=(255, 120, 120))
    return finish(c)


def gate_of_tartarus():
    """Claustrum before the open gate of the underworld, hellfire spilling out."""
    c = bg((60, 20, 60), (6, 2, 10), 0.5, 0.45)
    arch = poly([(0.14, 0.92), (0.14, 0.40)] + arc(0.5, 0.40, 0.36, 180, 360, 30) + [(0.86, 0.92)])
    inner = poly([(0.27, 0.92), (0.27, 0.44)] + arc(0.5, 0.44, 0.23, 180, 360, 30) + [(0.73, 0.92)])
    stone = minus(arch, inner)
    fill(c, soften(inner), rad((255, 210, 120), (170, 20, 20), 0.5, 0.72, 0.42))
    fl = shape(lambda d: [GA.flame(d, x, 0.94, w, h, l) for x, w, h, l in
                          ((0.36, 0.08, 0.30, -0.02), (0.50, 0.11, 0.42, 0.02), (0.64, 0.08, 0.32, 0.03))])
    fl = ImageChops.multiply(fl, inner)
    fill(c, soften(fl, 2), lin((255, 250, 210), (255, 120, 30), 270))
    glow(c, inner, (255, 80, 40, 255), 30, 1.1)
    shadow(c, stone, 4, 6, 8, 170)
    fill(c, soften(stone), lin((110, 90, 110), (40, 30, 46)))
    blocks = shape(lambda d: [d.line(pts([(0.14, y), (0.27, y)]), fill=255, width=int(0.008 * W)) for y in (0.56, 0.72)]
                   + [d.line(pts([(0.73, y), (0.86, y)]), fill=255, width=int(0.008 * W)) for y in (0.56, 0.72)]
                   + [d.line(pts([(0.5 + math.cos(math.radians(a)) * 0.23, 0.42 + math.sin(math.radians(a)) * 0.23),
                                  (0.5 + math.cos(math.radians(a)) * 0.36, 0.40 + math.sin(math.radians(a)) * 0.36)]),
                             fill=255, width=int(0.008 * W)) for a in (215, 250, 290, 325)])
    fill(c, soften(blocks), (20, 10, 24, 220))
    edge = minus(ring(0.5, 0.44, 0.23, 0.014), poly([(0, 0.44), (1, 0.44), (1, 1), (0, 1)]))
    fill(c, soften(edge), (255, 150, 90, 230))
    key = poly([(0.46, 0.06), (0.54, 0.06), (0.52, 0.17), (0.48, 0.17)])
    lit(c, key, (255, 120, 80), lin((255, 210, 150), (160, 60, 40)), 8, 1.0)
    # Claustrum: a dark staff with a crimson orb in a gold cage
    paint_staff(c, 0.50, 0.97, 0.50, 0.40, orb=((255, 220, 200), (180, 10, 40)), orb_glow=(255, 60, 60),
                wood=((90, 60, 90), (30, 20, 34)), orb_r=0.07, glowc=(255, 120, 90))
    motes(c, 13, 12, (0.30, 0.50, 0.70, 0.90), (0.006, 0.012), (255, 200, 120), (255, 100, 50))
    return finish(c)


def vidohunir():
    """Laevateinn's dark beam: a black sun with a violet corona, the crescent-headed staff before it."""
    c = bg((90, 30, 140), (8, 2, 20), 0.55, 0.38)
    rays(c, 0.58, 0.36, 12, (200, 120, 255), alpha=110, width=0.07, length=0.8, phase=0.12)
    corona = disc(0.58, 0.36, 0.24)
    glow(c, corona, (190, 90, 255, 255), 30, 1.8)
    fill(c, soften(corona, 6), rad((255, 220, 255), (150, 50, 230), 0.58, 0.36, 0.24))
    core = disc(0.58, 0.36, 0.17)
    fill(c, soften(core, 2), rad((40, 10, 60), (4, 0, 10), 0.56, 0.34, 0.18))
    beam = poly([(0.47, 0.44), (0.69, 0.44), (0.98, 1.0), (0.18, 1.0)])
    beam = minus(beam, core)
    fill(c, scale(soften(beam, 14), 0.45), (190, 110, 255, 255))
    # Laevateinn: dark shaft, a big golden crescent head
    L, f = frame(0.18, 0.94, 0.40, 0.46)
    shaft = poly([f(0, -0.024), f(L, -0.03), f(L, 0.03), f(0, 0.024)])
    cres = minus(disc(*f(L + 0.10, 0), 0.14), disc(*f(L + 0.18, 0.0), 0.12))
    gem = disc(*f(L + 0.02, 0), 0.035)
    whole = lighter(shaft, cres, gem)
    glow(c, whole, (230, 170, 255, 255), 12, 1.2)
    shadow(c, whole, 5, 8, 8, 160)
    fill(c, soften(shaft), lin((200, 170, 220), (90, 60, 110), 0))
    fill(c, soften(cres), lin(*GOLD))
    glow(c, gem, (255, 90, 200, 255), 10, 1.6)
    fill(c, soften(gem), rad((255, 230, 255), (220, 40, 160), *f(L + 0.01, -0.01), 0.04))
    sparkles(c, [(0.84, 0.16, 0.07), (0.86, 0.66, 0.04)], glowc=(220, 160, 255))
    return finish(c)


def garland_of_bliss():
    """Nirvana's light: a wreath of glowing blossoms around the radiant head of the staff."""
    c = bg((236, 140, 170), (60, 16, 50), 0.5, 0.42)
    rays(c, 0.5, 0.40, 18, (255, 250, 220), alpha=80)
    cx, cy, R = 0.5, 0.40, 0.25
    vine = ring(cx, cy, R, 0.022)
    fill(c, soften(vine), (120, 190, 110, 255))
    leaves = shape(lambda d: [GA.leaf(d, cx + math.cos(a) * R, cy + math.sin(a) * R, a + 1.9, 0.07, 0.025)
                              for a in [math.radians(k * 45 + 22) for k in range(8)]])
    fill(c, soften(leaves), lin((170, 236, 140), (60, 140, 70)))
    for k in range(8):
        a = math.radians(k * 45)
        x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
        petals = shape(lambda d, x=x, y=y, k=k: [d.ellipse(pts([(x + math.cos(t) * 0.028 - 0.026,
                                                                 y + math.sin(t) * 0.028 - 0.026),
                                                                (x + math.cos(t) * 0.028 + 0.026,
                                                                 y + math.sin(t) * 0.028 + 0.026)]), fill=255)
                                                 for t in [math.radians(j * 72 + k * 10) for j in range(5)]])
        glow(c, petals, (255, 240, 200, 255), 8, 1.0)
        fill(c, soften(petals), rad((255, 255, 250), (255, 160, 200), x, y, 0.06))
        fill(c, soften(disc(x, y, 0.017)), (255, 220, 90, 255))
    paint_staff(c, 0.50, 0.98, 0.50, 0.36, orb=((255, 255, 255), (255, 200, 120)), orb_glow=(255, 250, 200),
                wood=((250, 240, 225), (180, 160, 140)), orb_r=0.075, glowc=(255, 250, 220))
    return finish(c)


def omniscience():
    """Tupsimati's knowledge: a stone tablet with a glowing, all-seeing eye glyph amid orbiting runes."""
    c = bg((40, 110, 130), (4, 14, 24), 0.5, 0.45)
    orbit = ring(0.5, 0.48, 0.40, 0.012, 0.16)
    fill(c, scale(soften(orbit, 2), 0.7), (150, 255, 240, 255))
    tab = shape(lambda d: d.rounded_rectangle(pts([(0.31, 0.16), (0.69, 0.84)]), radius=0.08 * W, fill=255))
    shadow(c, tab, 5, 8, 8, 170)
    glow(c, tab, (120, 255, 230, 255), 16, 0.9)
    fill(c, soften(tab), lin((160, 150, 140), (70, 62, 60)))
    edge = minus(tab, shape(lambda d: d.rounded_rectangle(pts([(0.34, 0.19), (0.66, 0.81)]), radius=0.06 * W,
                                                         fill=255)))
    fill(c, soften(edge), lin((210, 200, 190), (110, 100, 96)))
    eye = shape(lambda d: GC.eye_shape(d, 0.5, 0.40, 0.12, 0.065))
    glow(c, eye, (150, 255, 240, 255), 14, 1.6)
    fill(c, soften(eye), (200, 255, 248, 255))
    fill(c, soften(disc(0.5, 0.40, 0.04)), (30, 40, 80, 255))
    fill(c, soften(disc(0.5, 0.40, 0.016)), (170, 120, 255, 255))
    lines = shape(lambda d: [d.line(pts([(0.39, y), (0.61 - 0.04 * (i % 2), y)]), fill=255, width=int(0.016 * W))
                             for i, y in enumerate((0.56, 0.63, 0.70, 0.76))])
    glow(c, lines, (140, 255, 230, 255), 6, 1.2)
    fill(c, soften(lines), (190, 255, 245, 255))
    front = ImageChops.multiply(orbit, poly([(0, 0.48), (1, 0.48), (1, 1), (0, 1)]))
    fill(c, soften(front, 2), (190, 255, 245, 255))
    runes = shape(lambda d: [GD.rune_glyph(d, x, y, 0.16, 0.022) for x, y in ((0.14, 0.50), (0.86, 0.46))])
    glow(c, runes, (130, 255, 230, 255), 8, 1.4)
    fill(c, soften(runes), (220, 255, 250, 255))
    sparkles(c, [(0.78, 0.18, 0.05)], glowc=(170, 255, 240))
    return finish(c)


def cataclysm():
    c = bg((80, 30, 100), (6, 2, 12), 0.5, 0.30)
    dome = shape(lambda d: d.chord(pts([(0.04, 0.50), (0.96, 1.20)]), 180, 360, fill=255))
    glow(c, dome, (200, 80, 255, 255), 30, 1.3)
    fill(c, soften(dome, 4), rad((255, 220, 255), (120, 30, 160), 0.5, 0.86, 0.45))
    ground = poly([(0, 0.84), (1, 0.84), (1, 1), (0, 1)])
    fill(c, soften(ground, 3), (20, 6, 26, 255))
    trail = poly(tstroke([(0.92, 0.04), (0.70, 0.30), (0.52, 0.56)], 0.02, 0.15))
    glow(c, trail, (180, 70, 255, 255), 16, 1.0)
    fill(c, soften(trail, 6), lin((80, 20, 120), (230, 160, 255), 135))
    met = disc(0.52, 0.58, 0.09)
    glow(c, met, (230, 140, 255, 255), 16, 1.6)
    fill(c, soften(met), rad((90, 30, 110), (20, 4, 30), 0.49, 0.55, 0.1))
    fill(c, soften(ring(0.52, 0.58, 0.09, 0.012)), (255, 200, 255, 230))
    rnd = random.Random(2)
    debris = shape(lambda d: [d.polygon(pts(T([(-1, -0.6), (1, -0.8), (0.6, 0.8), (-0.8, 0.6)],
                                             0.5 + rnd.uniform(-0.40, 0.40), rnd.uniform(0.62, 0.80),
                                             rnd.uniform(0.012, 0.024), rnd.uniform(0, 90))), fill=255)
                              for _ in range(12)])
    fill(c, soften(debris), (30, 10, 40, 255))
    return finish(c)


def myrkr():
    """Hvergelmir's dark wellspring pouring mana back into the caster."""
    c = bg((40, 30, 110), (4, 2, 18), 0.5, 0.65)
    pool = disc(0.5, 0.82, 0.38, 0.10)
    glow(c, pool, (120, 140, 255, 255), 20, 1.2)
    fill(c, soften(pool, 2), rad((60, 60, 160), (10, 8, 40), 0.5, 0.82, 0.38))
    fill(c, soften(ring(0.5, 0.82, 0.28, 0.012, 0.07)), (150, 170, 255, 200))
    fill(c, soften(ring(0.5, 0.82, 0.16, 0.010, 0.04)), (150, 170, 255, 160))
    m = mask()
    d = ImageDraw.Draw(m)
    for k in range(2):
        path = [(0.5 + math.sin(t * 7 + k * math.pi) * 0.17 * (1 - 0.5 * t), 0.82 - 0.66 * t)
                for t in [i / 50 for i in range(51)]]
        d.polygon(pts(tstroke(path, 0.06, 0.012)), fill=230)
    glow(c, m, (90, 170, 255, 255), 14, 1.3)
    fill(c, soften(m, 1.5), lin((220, 245, 255), (70, 120, 255), 270))
    paint_staff(c, 0.5, 0.90, 0.5, 0.20, orb=((230, 240, 255), (40, 40, 140)), orb_glow=(130, 160, 255),
                wood=((60, 60, 90), (16, 16, 30)), orb_r=0.06, sh=False)
    motes(c, 31, 18, (0.15, 0.10, 0.85, 0.75), (0.006, 0.014), (200, 230, 255), (90, 160, 255))
    return finish(c)


def shattersoul():
    """Khatvanga, its skull-topped staff, and a violet soul shattering into shards."""
    c = bg((130, 40, 120), (14, 2, 16), 0.58, 0.40)
    rnd = random.Random(17)
    cx, cy = 0.62, 0.38
    sh = mask()
    d = ImageDraw.Draw(sh)
    for k in range(11):
        a = k * math.pi * 2 / 11 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(0.16, 0.30)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        s = rnd.uniform(0.025, 0.05)
        d.polygon(pts(T([(0, -1.6), (0.7, 0), (0, 1.0), (-0.6, 0)], x, y, s, math.degrees(a) + 90)), fill=255)
    glow(c, sh, (255, 120, 240, 255), 10, 1.3)
    fill(c, soften(sh), lin((255, 230, 255), (200, 80, 220)))
    soul = poly([(cx, cy - 0.15), (cx + 0.10, cy), (cx, cy + 0.15), (cx - 0.10, cy)])
    glow(c, soul, (255, 120, 255, 255), 24, 1.6)
    fill(c, soften(soul), rad((255, 255, 255), (220, 90, 240), cx - 0.02, cy - 0.04, 0.15))
    cr = shape(lambda d: brush(d, [(cx - 0.02, cy - 0.15), (cx + 0.02, cy - 0.04), (cx - 0.03, cy + 0.04),
                                   (cx + 0.01, cy + 0.15)], 0.018, 0.008))
    fill(c, soften(cr), (60, 10, 70, 255))
    # the khatvanga: a pale shaft with a skull on top
    L, f = frame(0.16, 0.94, 0.36, 0.50)
    shaft = poly([f(0, -0.02), f(L, -0.024), f(L, 0.024), f(0, 0.02)])
    hx, hy = f(L + 0.06, 0)
    skull_m = shape(lambda d: GB.skull(d, hx, hy, 0.40))
    whole = lighter(shaft, skull_m)
    shadow(c, whole, 5, 8, 8, 160)
    fill(c, soften(shaft), lin((240, 220, 190), (150, 120, 90), 0))
    lit(c, skull_m, (255, 160, 255), lin((255, 252, 240), (200, 190, 170)), 10, 1.1)
    holes = skull_eyes(hx, hy, 0.40)
    glow(c, holes, (255, 80, 255, 255), 6, 1.2)
    fill(c, soften(holes), (70, 10, 70, 255))
    return finish(c)


# ---- bows ------------------------------------------------------------------------------------------------------------
def bow_masks(cx, cy, h, ang, bend=0.12, draw=0.0, w=0.045, flick=0.05, arrow_len=None, grip_off=0.0):
    """A recurve bow; the arrow flies along `ang` (degrees, clockwise from +x). (cx, cy) is the grip.
    Returns (limbs, string, arrow or None, grip, tip of the arrow)."""
    n = 40
    spine = []
    for i in range(n + 1):
        t = -1 + 2 * i / n
        y = t * h / 2 + grip_off
        x = -bend * t * t + flick * max(0.0, abs(t) - 0.75) ** 2 * 16
        spine.append((x, y))
    left, right = [], []
    for i, (x, y) in enumerate(spine):
        a = spine[max(0, i - 1)]
        b = spine[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        t = abs(-1 + 2 * i / n)
        hw = (w * (1 - 0.65 * t)) / 2
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    limbs = poly(T(left + right[::-1], cx, cy, 1, ang))
    top, bot = spine[0], spine[-1]
    nock = (top[0] - draw, grip_off * 0.0)
    string = shape(lambda d: d.line(pts(T([top, nock, bot], cx, cy, 1, ang)), fill=255, width=max(2, int(0.008 * W))))
    grip = poly(T([(-0.03, grip_off - 0.06), (0.025, grip_off - 0.06), (0.025, grip_off + 0.06),
                   (-0.03, grip_off + 0.06)], cx, cy, 1, ang))
    ar, tip = None, None
    if arrow_len:
        x0 = nock[0]
        x1 = x0 + arrow_len
        (ax0, ay0), (ax1, ay1) = T([(x0, 0), (x1, 0)], cx, cy, 1, ang)
        ar = shape(lambda d: GC.arrow(d, ax0, ay0, ax1, ay1, w=0.026, hl=0.11, hw=0.055, fl=0.10, fw=0.045))
        tip = (ax1, ay1)
    return limbs, string, ar, grip, tip


def paint_bow(c, cx, cy, h, ang, bend=0.12, draw=0.0, w=0.045, flick=0.05, arrow_len=None, wood=WOOD,
              string_col=(250, 240, 220), arrow_paint=None, arrow_glow=None, glowc=None, grip_col=GOLD, sh=True):
    limbs, string, ar, grip, tip = bow_masks(cx, cy, h, ang, bend, draw, w, flick, arrow_len)
    whole = lighter(limbs, grip) if ar is None else lighter(limbs, grip, ar)
    if glowc:
        glow(c, whole, col(glowc), 14, 1.1)
    if sh:
        shadow(c, whole, 5, 8, 8, 150)
    fill(c, soften(string), col(string_col))
    fill(c, soften(limbs), lin(wood[0], wood[1], 0))
    fill(c, soften(grip), lin(grip_col[0], grip_col[1]))
    if ar is not None:
        if arrow_glow:
            glow(c, ar, col(arrow_glow), 12, 1.4)
        fill(c, soften(ar), arrow_paint or lin((255, 255, 250), (200, 180, 140)))
    return tip


def arrow_m(x0, y0, x1, y1, w=0.04, hl=0.16, hw=0.085, fl=0.14, fw=0.065):
    return shape(lambda d: GC.arrow(d, x0, y0, x1, y1, w, hl, hw, fl, fw))


def paint_arrow(c, x0, y0, x1, y1, glowc=None, paint=None, sh=True, **kw):
    m = arrow_m(x0, y0, x1, y1, **kw)
    if sh:
        shadow(c, m, 4, 7, 6, 150)
    if glowc:
        glow(c, m, col(glowc), 12, 1.3)
    fill(c, soften(m), paint or lin((255, 255, 250), (196, 180, 140)))
    return m


def flaming_arrow():
    c = bg((200, 60, 20), (30, 4, 4), 0.4, 0.6)
    L, f = frame(0.88, 0.16, 0.12, 0.84)
    tail = poly([f(0.30, -0.10), f(0.30, 0.10), f(0.98, 0.0)])
    glow(c, tail, (255, 110, 30, 255), 20, 1.3)
    fill(c, soften(tail, 8), K.linear((255, 240, 160, 255), (255, 80, 20, 0), 135))
    fl = shape(lambda d: [d.polygon(pts(tstroke([f(0.08, v * 0.5), f(0.22, v * 1.2 + 0.02 * k),
                                                  f(0.34 + 0.06 * k, v * 1.6)], 0.11 - 0.015 * k, 0.0)), fill=255)
                          for k in range(3) for v in (-0.06, 0.0, 0.06)])
    glow(c, fl, (255, 120, 30, 255), 12, 1.3)
    fill(c, soften(fl, 2), (255, 210, 110, 255))
    paint_arrow(c, 0.16, 0.84, 0.88, 0.16)
    head = disc(*f(0.10, 0), 0.07)
    glow(c, head, (255, 160, 40, 255), 18, 1.6)
    fill(c, scale(soften(head, 6), 0.8), (255, 250, 200, 255))
    motes(c, 3, 14, (0.25, 0.35, 0.85, 0.85), (0.006, 0.013), (255, 220, 140), (255, 120, 30))
    return finish(c)


def piercing_arrow():
    c = bg((60, 90, 140), (6, 10, 24), 0.45, 0.5)
    plate = shape(lambda d: d.rounded_rectangle(pts([(0.44, 0.22), (0.58, 0.80)]), radius=0.03 * W, fill=255))
    plate = rot(plate, -15, 0.51, 0.51)
    shadow(c, plate, 5, 8, 8, 160)
    fill(c, soften(plate), lin((200, 210, 226), (90, 100, 120), 0))
    rivets = shape(lambda d: [d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
                              for x, y in ((0.49, 0.28), (0.55, 0.30), (0.47, 0.72), (0.53, 0.74))])
    fill(c, soften(rivets), (60, 66, 80, 255))
    hole = poly(star_poly(0.51, 0.51, 7, 0.07, 0.03))
    glow(c, hole, (180, 230, 255, 255), 10, 1.4)
    fill(c, soften(hole), (20, 26, 40, 255))
    back = arrow_m(0.06, 0.62, 0.51, 0.51, w=0.04, hl=0.0001, hw=0.0, fl=0.14)
    fill(c, soften(back), lin((255, 255, 250), (196, 180, 140)))
    front = ImageChops.multiply(arrow_m(0.06, 0.62, 0.92, 0.41), poly([(0.53, 0), (1, 0), (1, 1), (0.53, 1)]))
    glow(c, front, (180, 230, 255, 255), 10, 1.3)
    fill(c, soften(front), lin((255, 255, 255), (170, 190, 220)))
    streaks(c, [(0.62, 0.40, 0.82, 0.35), (0.62, 0.52, 0.84, 0.46)], (200, 240, 255), 0.01, 160)
    sparkles(c, [(0.56, 0.48, 0.06)], glowc=(180, 230, 255))
    return finish(c)


def dulling_arrow():
    c = bg((110, 90, 140), (16, 12, 26), 0.5, 0.5)
    haze = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.6), (x + r, y + r * 0.6)]), fill=120)
                            for x, y, r in ((0.30, 0.66, 0.16), (0.50, 0.70, 0.18), (0.70, 0.60, 0.14),
                                            (0.60, 0.30, 0.12))])
    fill(c, haze.filter(ImageFilter.GaussianBlur(18)), (200, 190, 220, 255))
    sp = shape(lambda d: brush(d, [(0.62 + math.cos(t) * 0.02 * t, 0.34 + math.sin(t) * 0.02 * t)
                                   for t in [i / 8 for i in range(0, 100)]], 0.022, 0.012))
    glow(c, sp, (230, 200, 255, 255), 8, 1.0)
    fill(c, soften(sp), (240, 230, 255, 255))
    # a blunted arrow: a dull rounded head
    L, f = frame(0.12, 0.86, 0.58, 0.40)
    m = arrow_m(0.12, 0.86, 0.58, 0.40, w=0.064, hl=0.0001, hw=0.0, fl=0.16, fw=0.09)
    knob = disc(*f(L, 0), 0.075)
    whole = lighter(m, knob)
    shadow(c, whole, 4, 7, 6, 150)
    keyline(c, whole)
    fill(c, soften(m), lin((240, 236, 230), (170, 160, 150)))
    fill(c, soften(knob), rad((200, 200, 210), (90, 90, 110), *f(L - 0.02, -0.02), 0.06))
    stars = shape(lambda d: [GD.star(d, x, y, 0.04, 0.016) for x, y in ((0.74, 0.20), (0.84, 0.40), (0.58, 0.16))])
    fill(c, soften(stars), (255, 240, 170, 230))
    return finish(c)


def sidewinder():
    c = bg((50, 130, 60), (6, 24, 8), 0.5, 0.5)
    path = [(0.10 + 0.62 * t + math.sin(t * math.pi * 2.0) * 0.12, 0.88 - 0.62 * t + math.sin(t * math.pi * 2.0) * 0.12)
            for t in [i / 60 for i in range(61)]]
    trail = poly(tstroke(path, 0.01, 0.10))
    glow(c, trail, (200, 255, 140, 255), 14, 1.2)
    fill(c, soften(trail, 2), lin((90, 200, 80), (230, 255, 170), 315))
    scales = shape(lambda d: [d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
                              for x, y in path[10:56:5]])
    fill(c, soften(scales), (40, 90, 30, 200))
    x0, y0 = path[-6]
    x1, y1 = path[-1]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    paint_arrow(c, x1 - ux * 0.30, y1 - uy * 0.30, x1 + ux * 0.20, y1 + uy * 0.20, glowc=(220, 255, 170), sh=True)
    return finish(c)


def blast_arrow():
    c = bg((30, 120, 130), (2, 20, 24), 0.62, 0.38)
    burst(c, 0.66, 0.36, 0.30, 0.13, 10, (255, 255, 220), (255, 120, 30), (255, 150, 40), 26, 1.4, -72)
    burst(c, 0.66, 0.36, 0.16, 0.07, 8, (255, 255, 250), (255, 220, 120), (255, 240, 200), 12)
    streaks(c, [(0.10, 0.84, 0.40, 0.58), (0.18, 0.92, 0.46, 0.66)], (200, 255, 255), 0.012, 150)
    paint_arrow(c, 0.12, 0.90, 0.60, 0.42)
    motes(c, 8, 12, (0.40, 0.10, 0.92, 0.62), (0.008, 0.016), (255, 230, 150), (255, 140, 40))
    return finish(c)


def arching_arrow():
    c = bg((90, 120, 200), (20, 14, 40), 0.5, 0.8, 0.9)
    hor = poly([(0, 0.84), (1, 0.84), (1, 1), (0, 1)])
    fill(c, soften(hor, 3), (16, 14, 30, 255))
    path = [(0.08 + 0.80 * t, 0.84 - 1.6 * t * (1 - t) * 0.8) for t in [i / 40 for i in range(41)]]
    dots = shape(lambda d: [d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
                            for x, y in path[2:28:3]])
    glow(c, dots, (255, 230, 160, 255), 8, 1.2)
    fill(c, soften(dots), (255, 245, 210, 255))
    x0, y0 = path[29]
    x1, y1 = path[36]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    paint_arrow(c, x1 - ux * 0.40, y1 - uy * 0.40, x1 + ux * 0.04, y1 + uy * 0.04, glowc=(255, 230, 160))
    sparkles(c, [(0.50, 0.14, 0.06), (0.20, 0.30, 0.04)], glowc=(255, 230, 180))
    return finish(c)


def empyreal_arrow():
    c = bg((40, 60, 140), (4, 6, 26), 0.5, 0.2)
    col_m = poly([(0.38, 0.0), (0.62, 0.0), (0.56, 1.0), (0.44, 1.0)])
    fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(18)), 0.85), (255, 240, 190, 255))
    clouds = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.45), (x + r, y + r * 0.45)]), fill=255)
                              for x, y, r in ((0.20, 0.16, 0.16), (0.40, 0.12, 0.14), (0.62, 0.13, 0.15),
                                              (0.82, 0.18, 0.15), (0.50, 0.18, 0.12))])
    glow(c, clouds, (255, 230, 170, 255), 14, 1.0)
    fill(c, soften(clouds, 4), lin((255, 250, 235), (190, 180, 210)))
    paint_arrow(c, 0.50, 0.12, 0.50, 0.90, glowc=(255, 240, 180), paint=lin((255, 255, 255), (255, 214, 120)))
    impact = disc(0.5, 0.90, 0.16, 0.05)
    glow(c, impact, (255, 230, 150, 255), 16, 1.5)
    fill(c, soften(impact, 4), (255, 250, 220, 255))
    sparkles(c, [(0.22, 0.44, 0.05), (0.80, 0.56, 0.06)], glowc=(255, 230, 170))
    return finish(c)


def namas_arrow():
    """Yoichinoyumi's homage: the long asymmetric yumi at full draw before a great red sun, petals falling."""
    c = bg((250, 236, 206), (150, 90, 70), 0.5, 0.45)
    sun = disc(0.56, 0.44, 0.27)
    glow(c, sun, (255, 90, 60, 255), 22, 1.0)
    fill(c, soften(sun), rad((250, 70, 50), (190, 20, 30), 0.5, 0.38, 0.3))
    stripes = shape(lambda d: [d.line(pts([(0.0, y), (1.0, y)]), fill=255, width=int(0.016 * W))
                               for y in (0.60, 0.66, 0.72)])
    fill(c, soften(ImageChops.multiply(stripes, sun)), (250, 230, 200, 255))
    # the yumi: tall, grip low; drawn back
    tip = paint_bow(c, 0.36, 0.50, 0.80, -20, bend=0.12, draw=0.16, w=0.05, flick=0.03, arrow_len=0.62,
                    wood=((90, 40, 30), (24, 8, 10)), string_col=(255, 255, 250), glowc=(255, 250, 230),
                    arrow_paint=lin((255, 250, 220), (230, 180, 70)), arrow_glow=(255, 220, 120),
                    grip_col=((250, 250, 245), (190, 40, 40)))
    rnd = random.Random(12)
    pet = shape(lambda d: [GA.leaf(d, rnd.uniform(0.15, 0.9), rnd.uniform(0.15, 0.9), rnd.uniform(0, 6.28), 0.05,
                                   0.022) for _ in range(9)])
    fill(c, soften(pet), lin((255, 220, 230), (240, 140, 170)))
    sparkles(c, [(tip[0], tip[1], 0.08)], glowc=(255, 230, 150))
    return finish(c)


def refulgent_arrow():
    c = bg((70, 120, 180), (8, 14, 34), 0.62, 0.38)
    rays(c, 0.70, 0.30, 14, (255, 255, 230), alpha=90, width=0.05)
    m = arrow_m(0.10, 0.90, 0.72, 0.28, w=0.066, hl=0.20, hw=0.11, fl=0.16, fw=0.085)
    hues = [(255, 120, 120), (255, 220, 120), (140, 255, 160), (120, 200, 255), (220, 150, 255)]
    for k, h in enumerate(hues):
        o = (k - 2) * 0.02
        streak = shape(lambda d, o=o: d.line(pts([(0.04 + o, 0.86 - o), (0.40 + o, 0.50 - o)]), fill=255,
                                             width=int(0.014 * W)))
        fill(c, scale(streak.filter(ImageFilter.GaussianBlur(3)), 0.85), h + (255,))
    glow(c, m, (255, 255, 230, 255), 22, 1.6)
    keyline(c, m, 7, (20, 30, 60, 200))
    fill(c, soften(m), lin((255, 255, 255), (230, 220, 180)))
    sparkles(c, [(0.72, 0.28, 0.16), (0.30, 0.22, 0.05)], glowc=(255, 255, 220))
    return finish(c)


def jishnus_radiance():
    """Gandiva at full draw before a golden mandala, a fan of light-arrows bursting from it."""
    c = bg((90, 30, 110), (12, 4, 20), 0.5, 0.42)
    rays(c, 0.5, 0.42, 24, (255, 210, 120), alpha=90, width=0.04)
    man = shape(lambda d: [d.ellipse(pts([(0.5 - r, 0.42 - r), (0.5 + r, 0.42 + r)]), outline=255,
                                     width=int(0.012 * W)) for r in (0.18, 0.28)])
    pet = shape(lambda d: [GA.leaf(d, 0.5 + math.cos(a) * 0.18, 0.42 + math.sin(a) * 0.18, a, 0.10, 0.04)
                           for a in [k * math.pi / 6 for k in range(12)]])
    glow(c, lighter(man, pet), (255, 190, 70, 255), 12, 1.3)
    fill(c, soften(man), (255, 220, 130, 255))
    fill(c, scale(soften(pet), 0.9), lin((255, 236, 170), (230, 140, 40)))
    fan = shape(lambda d: [GC.arrow(d, 0.5 + math.cos(a) * 0.12, 0.42 + math.sin(a) * 0.12,
                                    0.5 + math.cos(a) * 0.44, 0.42 + math.sin(a) * 0.44, 0.018, 0.07, 0.04, 0.0001, 0.0)
                           for a in [math.radians(-90 + k * 22) for k in (-3, -2, -1, 1, 2, 3)]])
    glow(c, fan, (255, 230, 150, 255), 10, 1.5)
    fill(c, soften(fan), (255, 250, 220, 255))
    tip = paint_bow(c, 0.5, 0.66, 0.70, -90, bend=0.13, draw=0.10, w=0.05, flick=0.06, arrow_len=0.50,
                    wood=((255, 220, 120), (170, 90, 20)), grip_col=((140, 40, 50), (70, 10, 20)),
                    arrow_paint=lin((255, 255, 255), (255, 220, 120)), arrow_glow=(255, 230, 150),
                    glowc=(255, 200, 100))
    sparkles(c, [(tip[0], tip[1], 0.10)], glowc=(255, 240, 180))
    return finish(c)


def apex_arrow():
    c = bg((90, 150, 190), (10, 20, 34), 0.5, 0.3)
    mtn = poly([(0.0, 0.94), (0.30, 0.56), (0.50, 0.30), (0.64, 0.46), (0.76, 0.40), (1.0, 0.82), (1.0, 1), (0, 1)])
    fill(c, soften(mtn, 2), lin((70, 90, 120), (20, 26, 40)))
    snow = poly([(0.40, 0.43), (0.50, 0.30), (0.58, 0.39), (0.53, 0.37), (0.48, 0.42), (0.44, 0.40)])
    fill(c, soften(snow), (240, 248, 255, 255))
    streaks(c, [(0.50, 0.92, 0.50, 0.40)], (255, 250, 200), 0.03, 140, 8)
    paint_arrow(c, 0.50, 0.66, 0.50, 0.12, glowc=(255, 245, 200), paint=lin((255, 255, 255), (255, 214, 120)))
    sparkles(c, [(0.50, 0.12, 0.10)], glowc=(255, 240, 170))
    return finish(c)


def prime_glass(c, m, glowc=(160, 240, 255), top=(255, 255, 255), bot=(140, 200, 240), gr=16, gs=1.4, sh=True):
    """The prime weapons' look: pale crystalline faces with a cyan-gold sheen."""
    glow(c, m, col(glowc), gr, gs)
    if sh:
        shadow(c, m, 5, 8, 8, 140)
    fill(c, soften(m), lin(top, bot, 60))
    facet = ImageChops.multiply(m, poly([(0, 0), (1, 0), (0, 1)]))
    fill(c, scale(soften(facet), 0.35), (255, 255, 255, 255))


def sarv():
    """The prime bow: a crystalline bow loosing a prismatic arrow."""
    c = bg((40, 80, 120), (4, 8, 20), 0.5, 0.45)
    rays(c, 0.62, 0.40, 12, (200, 240, 255), alpha=60)
    limbs, string, ar, grip, tip = bow_masks(0.36, 0.56, 0.80, -35, bend=0.13, draw=0.12, w=0.05, flick=0.07,
                                             arrow_len=0.62)
    fill(c, soften(string), (220, 250, 255, 255))
    prime_glass(c, lighter(limbs, grip))
    fill(c, soften(grip), lin((255, 236, 160), (200, 140, 50)))
    glow(c, ar, (180, 255, 255, 255), 14, 1.6)
    fill(c, soften(ar), lin((255, 255, 255), (170, 230, 255)))
    sparkles(c, [(tip[0], tip[1], 0.12), (0.20, 0.20, 0.05)], glowc=(190, 250, 255))
    return finish(c)


# ---- guns ------------------------------------------------------------------------------------------------------------
def rifle_masks(cx, cy, s, ang, scope=False, th=1.5):
    """A long gun pointing along `ang`; (cx, cy) its middle; th thickens it. Returns (wood, metal, muzzle point)."""
    def P(seq):
        return poly(T([(x, y * th) for x, y in seq], cx, cy, s, ang))
    wood = lighter(P([(-0.50, -0.03), (-0.20, -0.05), (-0.18, 0.04), (-0.30, 0.06), (-0.50, 0.13)]),
                   P([(0.03, -0.005), (0.30, -0.005), (0.28, 0.035), (0.03, 0.04)]),
                   P([(-0.16, 0.03), (-0.10, 0.03), (-0.16, 0.14), (-0.22, 0.13)]))
    met = lighter(P([(-0.21, -0.065), (0.05, -0.065), (0.05, 0.03), (-0.21, 0.035)]),
                  P([(0.03, -0.06), (0.52, -0.05), (0.52, -0.01), (0.03, -0.005)]),
                  P([(0.48, -0.065), (0.53, -0.065), (0.53, 0.0), (0.48, 0.0)]),
                  shape(lambda d: d.line(pts(T([(-0.08, 0.03 * th), (-0.08, 0.08 * th), (-0.02, 0.08 * th),
                                                (-0.01, 0.03 * th)], cx, cy, s, ang)), fill=255,
                                         width=max(2, int(0.016 * W * s)))))
    if scope:
        met = lighter(met, P([(-0.14, -0.13), (0.10, -0.13), (0.10, -0.08), (-0.14, -0.08)]),
                      P([(0.08, -0.145), (0.13, -0.145), (0.13, -0.065), (0.08, -0.065)]),
                      P([(-0.06, -0.08), (-0.03, -0.08), (-0.03, -0.06), (-0.06, -0.06)]))
    mz = T([(0.54, -0.03 * th)], cx, cy, s, ang)[0]
    return wood, met, mz


def pistol_masks(cx, cy, s, ang, revolver=False, ornate=False, mirror=False):
    """A handgun pointing along `ang`, (cx, cy) about its trigger (mirror: pointing the other way, upright).
    Returns (wood grip, metal, muzzle point)."""
    m = -1 if mirror else 1

    def T(seq, cx, cy, s, ang):
        return T0([(x * m, y) for x, y in seq], cx, cy, s, ang)

    def P(seq):
        return poly(T(seq, cx, cy, s, ang))
    met = lighter(P([(-0.16, -0.12), (0.12, -0.12), (0.12, -0.02), (-0.16, -0.01)]),
                  P([(0.10, -0.11), (0.46, -0.105), (0.46, -0.045), (0.10, -0.04)]),
                  P([(0.43, -0.125), (0.47, -0.125), (0.47, -0.04), (0.43, -0.04)]),
                  P([(-0.20, -0.16), (-0.13, -0.15), (-0.12, -0.10), (-0.18, -0.10)]),
                  shape(lambda d: d.line(pts(T([(-0.02, -0.01), (-0.02, 0.06), (0.06, 0.06), (0.08, -0.02)],
                                                cx, cy, s, ang)), fill=255, width=max(2, int(0.018 * W * s)))))
    if revolver:
        met = lighter(met, P([(-0.06, -0.15), (0.10, -0.15), (0.10, 0.02), (-0.06, 0.02)]))
    wood = P([(-0.17, -0.03), (-0.04, -0.03), (-0.08, 0.06), (-0.12, 0.24), (-0.25, 0.22), (-0.20, 0.04)])
    if ornate:
        wood = lighter(wood, P([(-0.27, 0.19), (-0.10, 0.22), (-0.11, 0.27), (-0.27, 0.25)]))
    mz = T([(0.48, -0.075)], cx, cy, s, ang)[0]
    return wood, met, mz


def paint_gun(c, wood, met, wood_col=WOOD, met_col=GUNMETAL, glowc=None, sh=True):
    whole = lighter(wood, met)
    if glowc:
        glow(c, whole, col(glowc), 14, 1.1)
    if sh:
        shadow(c, whole, 5, 8, 8, 160)
    fill(c, soften(wood), lin(wood_col[0], wood_col[1]))
    fill(c, soften(met), lin(met_col[0], met_col[1]))


def muzzle_flash(c, x, y, ang, size, inner=(255, 255, 230), outer=(255, 150, 40), glowc=(255, 170, 60)):
    a = math.radians(ang)
    q = []
    for i in range(14):
        t = math.pi * 2 * i / 14
        r = size * (1.0 if i % 2 == 0 else 0.4)
        lx, ly = math.cos(t) * r * 1.5, math.sin(t) * r * 0.8
        q.append((x + lx * math.cos(a) - ly * math.sin(a) + math.cos(a) * size * 0.9,
                  y + lx * math.sin(a) + ly * math.cos(a) + math.sin(a) * size * 0.9))
    m = poly(q)
    glow(c, m, col(glowc), 20, 1.5)
    fill(c, soften(m), rad(inner, outer, x + math.cos(a) * size * 0.6, y + math.sin(a) * size * 0.6, size * 1.4))
    return m


def bullet_m(x, y, ang, s):
    q = [(-0.20, -0.08), (0.05, -0.08)]
    q += [(0.05 + 0.18 * t, -0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(13)]]
    q += [(0.05 + 0.18 * t, 0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(12, -1, -1)]]
    q += [(-0.20, 0.08)]
    return poly(T(q, x, y, s, ang))


def paint_bullet(c, x, y, ang, s, glowc=(255, 200, 120), paint=None, sh=True):
    m = bullet_m(x, y, ang, s)
    if glowc:
        glow(c, m, col(glowc), 14, 1.4)
    if sh:
        shadow(c, m, 4, 6, 6, 140)
    fill(c, soften(m), paint or lin((255, 240, 200), (190, 120, 50), 45))
    return m


def hot_shot():
    c = bg((190, 70, 20), (30, 6, 4), 0.62, 0.36)
    wood, met, mz = rifle_masks(0.40, 0.62, 0.80, -32)
    trail = poly(tstroke([mz, (0.92, 0.10)], 0.04, 0.16))
    glow(c, trail, (255, 120, 30, 255), 18, 1.3)
    fill(c, soften(trail, 6), lin((255, 140, 30), (255, 240, 170), 315))
    paint_gun(c, wood, met)
    muzzle_flash(c, mz[0], mz[1], -32, 0.10)
    fire = shape(lambda d: GA.flame(d, 0.80, 0.30, 0.10, 0.26, 0.03))
    glow(c, fire, (255, 120, 30, 255), 14, 1.3)
    fill(c, soften(fire), lin((255, 250, 200), (255, 90, 20), 270))
    return finish(c)


def split_shot():
    c = bg((70, 100, 130), (8, 12, 22), 0.45, 0.5)
    for ang in (-24, 0, 24):
        a = math.radians(ang)
        x1, y1 = 0.56 + math.cos(a) * 0.36, 0.50 + math.sin(a) * 0.36
        streaks(c, [(0.50, 0.50, x1, y1)], (210, 236, 255), 0.022, 170, 4)
        paint_bullet(c, x1 - math.cos(a) * 0.04, y1 - math.sin(a) * 0.04, ang, 0.38, glowc=(200, 230, 255),
                     paint=lin((255, 255, 255), (150, 160, 190), 45))
    streaks(c, [(0.06, 0.50, 0.40, 0.50)], (210, 236, 255), 0.04, 140, 6)
    paint_bullet(c, 0.34, 0.50, 0, 0.62)
    sparkles(c, [(0.50, 0.50, 0.10)], glowc=(220, 240, 255))
    return finish(c)


def sniper_shot():
    """The scope's view: a bright brass-rimmed lens, a bold crosshair, a red point on the mark."""
    c = bg((70, 130, 80), (6, 18, 8), 0.5, 0.5)
    ring_m = ring(0.5, 0.5, 0.33, 0.07)
    glow(c, ring_m, (200, 255, 200, 255), 14, 1.3)
    fill(c, soften(ring_m), lin((255, 236, 170), (150, 100, 36)))
    lens = disc(0.5, 0.5, 0.295)
    fill(c, soften(lens, 2), rad((190, 250, 200), (30, 80, 50), 0.42, 0.40, 0.36))
    cross = shape(lambda d: [d.line(pts([(0.5, 0.21), (0.5, 0.79)]), fill=255, width=int(0.022 * W)),
                             d.line(pts([(0.21, 0.5), (0.79, 0.5)]), fill=255, width=int(0.022 * W))])
    gap = disc(0.5, 0.5, 0.07)
    fill(c, soften(minus(cross, gap)), (10, 20, 14, 255))
    bull = disc(0.5, 0.5, 0.04)
    glow(c, bull, (255, 60, 50, 255), 14, 1.8)
    fill(c, soften(bull), rad((255, 220, 200), (240, 40, 30), 0.49, 0.49, 0.045))
    gl = shape(lambda d: d.chord(pts([(0.24, 0.22), (0.62, 0.60)]), 190, 260, fill=255))
    fill(c, scale(soften(gl, 4), 0.5), (255, 255, 255, 255))
    return finish(c)


def slug_shot():
    c = bg((130, 110, 60), (22, 16, 6), 0.62, 0.5)
    plate = poly([(0.72, 0.0), (1.0, 0.0), (1.0, 1.0), (0.72, 1.0)])
    fill(c, soften(plate, 2), lin((150, 140, 120), (70, 64, 54), 0))
    dent = ring(0.72, 0.5, 0.10, 0.03, 0.18)
    glow(c, dent, (255, 220, 140, 255), 14, 1.4)
    fill(c, soften(dent), (255, 240, 200, 255))
    sw = shape(lambda d: [d.arc(pts([(0.72 - r, 0.5 - r), (0.72 + r, 0.5 + r)]), 110, 250, fill=255,
                                width=int(0.02 * W)) for r in (0.18, 0.28, 0.38)])
    glow(c, sw, (255, 220, 140, 255), 10, 1.0)
    fill(c, soften(sw, 1.5), (255, 240, 200, 200))
    streaks(c, [(0.04, 0.5, 0.40, 0.5)], (255, 230, 170), 0.08, 120, 10)
    # a heavy, blunt slug
    sl = shape(lambda d: d.rounded_rectangle(pts([(0.34, 0.40), (0.66, 0.60)]), radius=0.09 * W, fill=255))
    shadow(c, sl, 4, 7, 6, 160)
    fill(c, soften(sl), lin((240, 230, 210), (120, 110, 100)))
    bands = shape(lambda d: [d.line(pts([(x, 0.41), (x, 0.59)]), fill=255, width=int(0.012 * W)) for x in (0.44, 0.50)])
    fill(c, soften(ImageChops.multiply(bands, sl)), (90, 80, 70, 200))
    return finish(c)


def blast_shot():
    c = bg((40, 80, 150), (4, 8, 26), 0.66, 0.4)
    wood, met, mz = rifle_masks(0.36, 0.64, 0.80, -28)
    cone = poly([mz, (mz[0] + 0.50, mz[1] - 0.48), (mz[0] + 0.60, mz[1] - 0.14)])
    glow(c, cone, (255, 160, 60, 255), 20, 1.0)
    fill(c, scale(soften(cone, 10), 0.8), (255, 220, 140, 255))
    rnd = random.Random(5)
    pel = shape(lambda d: [d.ellipse(pts([(x - 0.016, y - 0.016), (x + 0.016, y + 0.016)]), fill=255)
                           for x, y in [(mz[0] + t * math.cos(a), mz[1] + t * math.sin(a))
                                        for t, a in [(rnd.uniform(0.12, 0.42), math.radians(rnd.uniform(-58, -14)))
                                                     for _ in range(14)]]])
    glow(c, pel, (255, 200, 90, 255), 8, 1.4)
    fill(c, soften(pel), (255, 250, 220, 255))
    paint_gun(c, wood, met)
    muzzle_flash(c, mz[0], mz[1], -28, 0.10)
    return finish(c)


def heavy_shot():
    c = bg((150, 110, 70), (20, 12, 6), 0.6, 0.45)
    smoke = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                             for x, y, r in ((0.70, 0.26, 0.12), (0.82, 0.38, 0.09), (0.60, 0.16, 0.08))])
    fill(c, scale(smoke.filter(ImageFilter.GaussianBlur(10)), 0.7), (200, 196, 190, 255))
    wood, met, mz = rifle_masks(0.42, 0.60, 0.96, -30)
    heavy = poly(T([(0.0, -0.15), (0.54, -0.12), (0.54, 0.0), (0.0, 0.0)], 0.42, 0.60, 0.96, -30))
    paint_gun(c, wood, lighter(met, heavy), wood_col=((120, 80, 50), (50, 30, 16)))
    muzzle_flash(c, mz[0], mz[1] - 0.01, -30, 0.10, glowc=(255, 210, 120))
    bands = shape(lambda d: [d.polygon(pts(T([(x, -0.16), (x + 0.03, -0.16), (x + 0.03, 0.01), (x, 0.01)],
                                              0.42, 0.60, 0.96, -30)), fill=255) for x in (0.10, 0.30, 0.50)])
    fill(c, soften(bands), lin(*GOLD))
    return finish(c)


def detonator():
    c = bg((170, 40, 30), (24, 4, 4), 0.55, 0.40)
    burst(c, 0.56, 0.40, 0.42, 0.20, 12, (255, 250, 210), (255, 100, 30), (255, 120, 40), 30, 1.4)
    burst(c, 0.56, 0.40, 0.22, 0.10, 9, (255, 255, 250), (255, 210, 110), (255, 240, 180), 12, 1.0, -60)
    rnd = random.Random(21)
    frag = shape(lambda d: [d.polygon(pts(T([(-1, -0.5), (1, -0.3), (0.3, 0.8)], 0.56 + math.cos(a) * r,
                                              0.40 + math.sin(a) * r, 0.025, rnd.uniform(0, 180))), fill=255)
                            for a, r in [(rnd.uniform(0, 6.28), rnd.uniform(0.30, 0.42)) for _ in range(10)]])
    fill(c, soften(frag), (60, 20, 10, 255))
    paint_bullet(c, 0.24, 0.72, -38, 0.66, glowc=(255, 180, 80))
    return finish(c)


def coronach():
    """A lament for the fallen: Annihilator planted muzzle-down as a grave marker, dark against a setting sun, a
    laurel wreath laid at its foot."""
    c = bg((200, 70, 50), (30, 6, 20), 0.5, 0.5, 0.8)
    sun = disc(0.5, 0.50, 0.33)
    glow(c, sun, (255, 140, 60, 255), 26, 1.3)
    fill(c, soften(sun), rad((255, 244, 180), (255, 110, 40), 0.5, 0.50, 0.33))
    hill = poly([(0, 0.82), (0.3, 0.79), (0.7, 0.79), (1, 0.82), (1, 1), (0, 1)])
    fill(c, soften(hill, 2), (26, 8, 18, 255))

    wood, met, mz = rifle_masks(0.46, 0.50, 0.94, 34, scope=True, th=1.9)   # leaning, muzzle in the earth
    gun = lighter(wood, met)
    glow(c, gun, (255, 220, 160, 255), 8, 1.6)
    shadow(c, gun, 3, 5, 5, 120)
    fill(c, soften(wood), lin((110, 50, 36), (44, 16, 12), 0))
    fill(c, soften(met), lin((96, 90, 106), (26, 22, 32), 0))
    # laurel wreath laid at its foot
    R = 0.10
    wr = shape(lambda d: [GA.leaf(d, 0.70 + math.cos(a) * R * 0.6, 0.70 + math.sin(a) * R, a + 1.8, 0.06, 0.024)
                          for a in [math.radians(k * 30 + 15) for k in range(12)]])
    shadow(c, wr, 3, 5, 5, 140)
    fill(c, soften(wr), lin((220, 230, 120), (70, 110, 40)))
    rib = poly([(0.67, 0.79), (0.73, 0.79), (0.78, 0.90), (0.73, 0.87), (0.70, 0.91), (0.67, 0.87), (0.62, 0.90)])
    fill(c, soften(rib), lin((240, 60, 60), (130, 10, 20)))
    motes(c, 41, 10, (0.1, 0.1, 0.9, 0.4), (0.006, 0.012), (255, 220, 170), (255, 140, 80))
    return finish(c)


def trueflight():
    """Gastraphetes, the crossbow, loosing a bolt of pure light."""
    c = bg((40, 120, 130), (4, 18, 22), 0.6, 0.4)
    L, f = frame(0.14, 0.86, 0.60, 0.40)
    stock = poly([f(-0.04, -0.06), f(L, -0.045), f(L, 0.045), f(0.06, 0.08), f(-0.04, 0.09)])
    pcx, pcy = f(L - 0.06, 0)
    ang = math.degrees(math.atan2(0.40 - 0.86, 0.60 - 0.14))
    limbs, string, _, _, _ = bow_masks(pcx, pcy, 0.56, ang, bend=0.08, draw=0.10, w=0.07, flick=0.03)
    bolt = shape(lambda d: GC.arrow(d, *f(0.10, 0), *f(L + 0.30, 0), w=0.036, hl=0.11, hw=0.07, fl=0.07, fw=0.05))
    beam = poly(tstroke([f(L + 0.05, 0), f(L + 0.60, 0)], 0.04, 0.12))
    glow(c, beam, (255, 250, 200, 255), 16, 1.3)
    fill(c, soften(beam, 6), lin((255, 255, 240), (255, 230, 140), 315))
    whole = lighter(stock, limbs)
    shadow(c, whole, 5, 8, 8, 150)
    keyline(c, whole)
    fill(c, soften(string), (250, 240, 220, 255))
    fill(c, soften(stock), lin(*WOOD))
    fill(c, soften(limbs), lin((230, 236, 250), (120, 130, 160), 0))
    glow(c, bolt, (255, 250, 200, 255), 14, 1.8)
    fill(c, soften(bolt), (255, 255, 245, 255))
    sparkles(c, [f(L + 0.30, 0) + (0.12,)], glowc=(255, 250, 210))
    return finish(c)


def leaden_salute():
    """Death Penalty's dark round: an ornate pistol, a violet shot and a ghost skull in its smoke."""
    c = bg((70, 30, 100), (6, 2, 12), 0.6, 0.38)
    wood, met, mz = pistol_masks(0.38, 0.58, 0.95, -24, ornate=True)
    smoke = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                             for x, y, r in ((0.66, 0.30, 0.16), (0.78, 0.22, 0.10), (0.56, 0.36, 0.10))])
    fill(c, scale(smoke.filter(ImageFilter.GaussianBlur(12)), 0.8), (170, 100, 220, 255))
    sk = shape(lambda d: GB.skull(d, 0.68, 0.28, 0.9))
    fill(c, scale(soften(sk, 4), 0.55), (230, 210, 255, 255))
    fill(c, scale(soften(skull_eyes(0.68, 0.28, 0.9), 3), 0.8), (60, 10, 80, 255))
    orb = disc(mz[0] + 0.05, mz[1] - 0.03, 0.05)
    glow(c, orb, (200, 80, 255, 255), 18, 1.8)
    fill(c, soften(orb), rad((255, 230, 255), (150, 40, 220), mz[0] + 0.04, mz[1] - 0.04, 0.06))
    paint_gun(c, wood, met, wood_col=((250, 150, 140), (190, 70, 80)), met_col=((250, 230, 170), (160, 110, 50)),
              glowc=(200, 120, 255))
    return finish(c)


def numbing_shot():
    c = bg((150, 140, 30), (24, 22, 4), 0.55, 0.45)
    bolts = shape(lambda d: [brush(d, q, 0.02, 0.008) for q in
                             ([(0.56, 0.42), (0.64, 0.30), (0.60, 0.26), (0.70, 0.12)],
                              [(0.60, 0.52), (0.74, 0.56), (0.76, 0.50), (0.90, 0.58)],
                              [(0.54, 0.56), (0.58, 0.70), (0.52, 0.72), (0.56, 0.86)],
                              [(0.62, 0.46), (0.78, 0.36), (0.80, 0.42), (0.92, 0.32)])])
    glow(c, bolts, (255, 255, 120, 255), 12, 1.6)
    fill(c, soften(bolts), (255, 255, 230, 255))
    streaks(c, [(0.04, 0.62, 0.34, 0.52)], (255, 255, 200), 0.05, 130, 8)
    paint_bullet(c, 0.40, 0.52, -18, 0.62, glowc=(255, 255, 140), paint=lin((255, 255, 220), (190, 170, 60), 45))
    return finish(c)


def wildfire():
    """Armageddon unleashed: a gun at the heart of a spiralling firestorm."""
    c = bg((220, 80, 20), (34, 4, 4), 0.5, 0.5)
    m = mask()
    d = ImageDraw.Draw(m)
    for k in range(5):
        a0 = k * 72
        path = [(0.5 + math.cos(math.radians(a0 + t * 220)) * (0.06 + 0.38 * t),
                 0.5 + math.sin(math.radians(a0 + t * 220)) * (0.06 + 0.38 * t)) for t in [i / 40 for i in range(41)]]
        d.polygon(pts(tstroke(path, 0.10, 0.0)), fill=255)
    glow(c, m, (255, 120, 20, 255), 22, 1.4)
    fill(c, soften(m, 2), rad((255, 255, 210), (240, 70, 20), 0.5, 0.5, 0.45))
    core = disc(0.5, 0.5, 0.12)
    glow(c, core, (255, 240, 180, 255), 20, 1.6)
    fill(c, soften(core, 4), (255, 250, 220, 255))
    wood, met, mz = rifle_masks(0.46, 0.56, 0.82, -38)
    paint_gun(c, wood, met, wood_col=((60, 20, 16), (20, 4, 4)), met_col=((255, 200, 120), (150, 60, 20)))
    muzzle_flash(c, mz[0], mz[1], -38, 0.08)
    motes(c, 23, 16, (0.08, 0.08, 0.92, 0.92), (0.006, 0.014), (255, 230, 160), (255, 120, 30))
    return finish(c)


def last_stand():
    """Fomalhaut's twofold shot: two pistols crossed in an X under the lone bright star."""
    c = bg((40, 70, 130), (4, 6, 20), 0.5, 0.25)
    rays(c, 0.5, 0.20, 8, (210, 236, 255), alpha=100, width=0.03, length=0.5)
    st = poly(star_poly(0.5, 0.20, 4, 0.15, 0.03))
    glow(c, st, (200, 230, 255, 255), 18, 1.6)
    fill(c, soften(st), (255, 255, 255, 255))
    for ang, cx, mir in ((-45, 0.37, False), (45, 0.63, True)):        # barrels cross: a clear X, grips out
        wood, met, mz = pistol_masks(cx, 0.68, 0.86, ang, mirror=mir)
        paint_gun(c, wood, met, wood_col=((255, 210, 150), (200, 130, 70)), met_col=((240, 248, 255), (120, 130, 160)),
                  glowc=(150, 200, 255))
    return finish(c)


def terminus():
    """The prime gun: a crystalline revolver firing toward the end of the line."""
    c = bg((40, 100, 120), (4, 12, 18), 0.6, 0.45)
    hor = shape(lambda d: d.line(pts([(0.0, 0.40), (1.0, 0.40)]), fill=255, width=int(0.008 * W)))
    fill(c, scale(soften(hor, 3), 0.6), (190, 250, 255, 255))
    streaks(c, [(0.60, 0.40, 0.98, 0.40)], (220, 255, 255), 0.03, 160, 6)
    wood, met, mz = pistol_masks(0.36, 0.48, 1.0, 0, revolver=True)
    prime_glass(c, lighter(wood, met))
    fill(c, soften(wood), lin((255, 236, 170), (196, 140, 60)))
    cyl = shape(lambda d: [d.line(pts(T([(x, -0.08), (x, 0.01)], 0.36, 0.48)), fill=255, width=int(0.008 * W))
                           for x in (0.0, 0.04, 0.08)])
    fill(c, soften(cyl), (80, 140, 170, 200))
    sparkles(c, [(mz[0] + 0.06, mz[1], 0.12), (0.86, 0.40, 0.05)], glowc=(190, 250, 255))
    return finish(c)


def vulcan_shot():
    c = bg((150, 40, 20), (20, 4, 4), 0.62, 0.62)
    vol = poly([(0.40, 1.0), (0.62, 0.70), (0.76, 0.70), (0.98, 1.0)])
    fill(c, soften(vol, 2), lin((70, 40, 36), (24, 10, 10)))
    lava = shape(lambda d: [brush(d, [(0.69, 0.72), (0.66, 0.84), (0.70, 0.98)], 0.03, 0.012),
                            d.ellipse(pts([(0.60, 0.66), (0.78, 0.74)]), fill=255)])
    glow(c, lava, (255, 100, 20, 255), 14, 1.6)
    fill(c, soften(lava), (255, 200, 80, 255))
    plume = shape(lambda d: GA.flame(d, 0.69, 0.72, 0.10, 0.40, -0.04))
    glow(c, plume, (255, 90, 20, 255), 20, 1.3)
    fill(c, soften(plume, 3), lin((255, 250, 190), (230, 60, 20), 270))
    wood, met, mz = rifle_masks(0.32, 0.50, 0.70, -20)
    trail = poly(tstroke([mz, (0.66, 0.38)], 0.03, 0.08))
    fill(c, soften(trail, 4), (255, 160, 60, 255))
    rock = disc(0.66, 0.36, 0.05)
    glow(c, rock, (255, 120, 30, 255), 12, 1.6)
    fill(c, soften(rock), rad((255, 230, 120), (160, 40, 10), 0.65, 0.35, 0.06))
    paint_gun(c, wood, met)
    muzzle_flash(c, mz[0], mz[1], -20, 0.06)
    return finish(c)


# ---- the others: daggers, swords, fists, clubs and the NPC-only skills ------------------------------------------------
def sword_m(hx, hy, tx, ty, w=0.05, guard=0.11, grip=0.14):
    return shape(lambda d: GA.sword(d, hx, hy, tx, ty, w, guard, grip))


def hilt_m(hx, hy, tx, ty, grip=0.14, guard=0.11):
    """The hilt end of a sword_m (to paint the grip and guard gold)."""
    L = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / L, (ty - hy) / L
    gx, gy = hx + ux * (grip + 0.03), hy + uy * (grip + 0.03)
    return disc((hx + gx) / 2, (hy + gy) / 2, max(guard, grip / 2 + 0.03) + 0.01)


def paint_sword(c, hx, hy, tx, ty, w=0.05, guard=0.11, grip=0.14, glowc=None, blade=STEEL, hilt=GOLD, sh=True):
    m = sword_m(hx, hy, tx, ty, w, guard, grip)
    if glowc:
        glow(c, m, col(glowc), 14, 1.2)
    if sh:
        shadow(c, m, 5, 8, 8, 160)
    fill(c, soften(m), lin(blade[0], blade[1]))
    fill(c, soften(ImageChops.multiply(m, hilt_m(hx, hy, tx, ty, grip, guard))), lin(hilt[0], hilt[1]))
    return m


def dagger_m(cx, cy, s, ang):
    return shape(lambda d: GB.draw_dagger(d, cx, cy, s, ang))


def paint_dagger(c, cx, cy, s, ang, glowc=None, blade=STEEL, hilt=GOLD):
    m = dagger_m(cx, cy, s, ang)
    h = shape(lambda d: GB.draw_dagger(d, cx, cy, s, ang, parts=(1, 2, 3)))
    if glowc:
        glow(c, m, col(glowc), 12, 1.2)
    shadow(c, m, 5, 8, 8, 160)
    fill(c, soften(m), lin(blade[0], blade[1]))
    fill(c, soften(h), lin(hilt[0], hilt[1]))
    return m


def fist_m(cx, cy, s):
    return shape(lambda d: K.fist_front(d, cx, cy, s))


def paint_fist(c, cx, cy, s, glowc=(255, 190, 100), skin=((255, 232, 196), (222, 146, 92)), gr=20):
    m = fist_m(cx, cy, s)
    glow(c, m, col(glowc), gr, 1.3)
    shadow(c, m, 5, 8, 8, 150)
    fill(c, soften(m), lin(skin[0], skin[1]))
    lines = shape(lambda d: K.fist_lines(d, cx, cy, s))
    fill(c, scale(soften(lines, 1.5), 0.7), (120, 60, 36, 255))
    return m


def exenterator():
    c = bg((40, 110, 70), (4, 18, 10), 0.5, 0.5)
    for k in range(4):
        o = (k - 1.5) * 0.09
        m = poly(tstroke([(0.18 + o, 0.14 - o), (0.86 + o, 0.82 - o)], 0.0, 0.03))
        m = lighter(m, poly(tstroke([(0.86 + o, 0.82 - o), (0.18 + o, 0.14 - o)], 0.0, 0.03)))
        glow(c, m, (160, 255, 170, 255), 8, 1.2)
        fill(c, scale(soften(m), 0.75), (220, 255, 220, 255))
    paint_dagger(c, 0.38, 0.50, 0.62, -40, glowc=(160, 255, 170))
    paint_dagger(c, 0.62, 0.50, 0.62, 40, glowc=(160, 255, 170))
    return finish(c)


def chant_du_cygne():
    """Almace's swan song: a raised sword between white swan wings, feathers drifting."""
    c = bg((60, 120, 210), (6, 14, 40), 0.5, 0.42)
    rays(c, 0.5, 0.42, 16, (230, 245, 255), alpha=70)

    def wing(d, side):
        for i in range(6):
            t = i / 5
            ang = math.radians(-15 - 55 * t) if side > 0 else math.radians(195 + 55 * t)
            length = 0.38 - 0.06 * t
            bx, by = 0.5 + side * 0.05, 0.50
            ex, ey = bx + math.cos(ang) * length, by + math.sin(ang) * length + 0.04
            nx, ny = -math.sin(ang) * 0.05, math.cos(ang) * 0.05
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    w = shape(lambda d: [wing(d, 1), wing(d, -1)])
    glow(c, w, (220, 240, 255, 255), 16, 1.2)
    fill(c, soften(w), lin((255, 255, 255), (190, 214, 240)))
    paint_sword(c, 0.5, 0.92, 0.5, 0.08, w=0.05, guard=0.12, glowc=(220, 240, 255), blade=((255, 255, 255), (170, 200, 240)))
    rnd = random.Random(8)
    fe = shape(lambda d: [GA.leaf(d, x, y, rnd.uniform(0, 6.28), 0.06, 0.02) for x, y in
                          ((0.18, 0.78), (0.82, 0.74), (0.28, 0.90), (0.72, 0.88))])
    fill(c, soften(fe), (240, 248, 255, 255))
    return finish(c)


def requiescat():
    c = bg((90, 110, 160), (10, 12, 26), 0.5, 0.40)
    ground = poly([(0, 0.80), (1, 0.80), (1, 1), (0, 1)])
    fill(c, soften(ground, 3), lin((40, 50, 60), (10, 12, 20)))
    halo = ring(0.5, 0.20, 0.13, 0.022, 0.05)
    glow(c, halo, (255, 250, 210, 255), 14, 1.4)
    fill(c, soften(halo), (255, 250, 220, 255))
    rays(c, 0.5, 0.26, 12, (220, 230, 255), alpha=60, length=0.5)
    paint_sword(c, 0.5, 0.18, 0.5, 0.86, w=0.05, guard=0.13, glowc=(210, 220, 255))
    lilies = shape(lambda d: [GA.leaf(d, x, 0.84, a, 0.11, 0.035) for x, a in
                              ((0.30, -2.5), (0.30, -1.9), (0.30, -2.2), (0.70, -0.6), (0.70, -1.2), (0.70, -0.9))])
    glow(c, lilies, (230, 240, 255, 255), 8, 1.2)
    fill(c, soften(lilies), lin((255, 255, 255), (200, 210, 230)))
    motes(c, 19, 12, (0.2, 0.2, 0.8, 0.8), (0.005, 0.011), (230, 236, 255), (180, 200, 255))
    return finish(c)


def knights_of_round():
    """Excalibur's thirteen knights: a round table of swords pointing in, the king's sword at its heart."""
    c = bg((40, 60, 150), (4, 6, 26), 0.5, 0.5)
    rays(c, 0.5, 0.5, 24, (255, 230, 150), alpha=80)
    table = ring(0.5, 0.5, 0.30, 0.02)
    glow(c, table, (255, 210, 110, 255), 12, 1.3)
    fill(c, soften(table), lin(*GOLD))
    ring_sw = mask()
    d = ImageDraw.Draw(ring_sw)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        GA.sword(d, 0.5 + math.cos(a) * 0.42, 0.5 + math.sin(a) * 0.42, 0.5 + math.cos(a) * 0.24,
                 0.5 + math.sin(a) * 0.24, 0.018, 0.04, 0.05)
    glow(c, ring_sw, (255, 230, 160, 255), 8, 1.2)
    fill(c, soften(ring_sw), lin((255, 255, 255), (190, 200, 230)))
    core = disc(0.5, 0.5, 0.18)
    glow(c, core, (255, 220, 120, 255), 20, 1.3)
    fill(c, scale(soften(core, 10), 0.6), (255, 240, 190, 255))
    paint_sword(c, 0.5, 0.80, 0.5, 0.18, w=0.045, guard=0.11, glowc=(255, 230, 140),
                blade=((255, 255, 255), (220, 210, 170)))
    return finish(c)


def final_paradise():
    c = bg((250, 170, 200), (90, 60, 160), 0.5, 0.35)
    bow_ = shape(lambda d: [d.arc(pts([(0.5 - r, 0.70 - r), (0.5 + r, 0.70 + r)]), 180, 360, fill=255,
                                  width=int(0.035 * W)) for r in (0.42,)])
    for k, h in enumerate([(255, 110, 110), (255, 200, 100), (255, 250, 130), (120, 230, 140), (110, 170, 255),
                           (190, 130, 255)]):
        r = 0.44 - k * 0.032
        band = shape(lambda d, r=r: d.arc(pts([(0.5 - r, 0.74 - r), (0.5 + r, 0.74 + r)]), 180, 360, fill=255,
                                          width=int(0.034 * W)))
        fill(c, scale(soften(band, 2), 0.85), h + (255,))
    clouds = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.55), (x + r, y + r * 0.55)]), fill=255)
                              for x, y, r in ((0.14, 0.80, 0.16), (0.32, 0.86, 0.15), (0.54, 0.88, 0.16),
                                              (0.74, 0.84, 0.15), (0.90, 0.78, 0.13))])
    glow(c, clouds, (255, 255, 255, 255), 12, 1.0)
    fill(c, soften(clouds, 3), lin((255, 255, 255), (230, 220, 245)))
    paint_fist(c, 0.5, 0.46, 0.90, glowc=(255, 250, 220), gr=24)
    sparkles(c, [(0.80, 0.22, 0.07), (0.20, 0.26, 0.05)])
    return finish(c)


def fast_blade_ii():
    c = bg((210, 110, 40), (36, 12, 4), 0.5, 0.5)
    for k, (y0, y1) in enumerate(((0.30, 0.14), (0.86, 0.70))):
        m = poly(tstroke([(0.10, y0 + 0.10), (0.50, y0 - 0.02 + (y1 - y0) * 0.3), (0.92, y1)], 0.0, 0.05))
        glow(c, m, (255, 230, 150, 255), 10, 1.3)
        fill(c, soften(m), (255, 250, 220, 255))
    streaks(c, [(0.06, 0.54, 0.30, 0.54), (0.06, 0.62, 0.24, 0.62), (0.10, 0.46, 0.28, 0.46)], (255, 230, 170),
            0.014, 170)
    paint_sword(c, 0.24, 0.52, 0.92, 0.48, w=0.05, guard=0.11, glowc=(255, 210, 120))
    return finish(c)


def dragon_blow():
    c = bg((40, 110, 150), (4, 14, 24), 0.5, 0.5)
    path = [(0.5 + math.cos(t * 2.4 * math.pi) * 0.36 * (1 - t * 0.55), 0.52 + math.sin(t * 2.4 * math.pi) * 0.36 *
             (1 - t * 0.55)) for t in [i / 60 for i in range(61)]]
    body = poly(tstroke(path, 0.10, 0.02))
    glow(c, body, (120, 230, 255, 255), 16, 1.3)
    fill(c, soften(body, 2), lin((210, 250, 255), (60, 160, 220)))
    sc = shape(lambda d: [d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
                          for x, y in path[2:50:4]])
    fill(c, soften(sc), (30, 90, 140, 220))
    hx, hy = path[0]
    head = poly(T([(-0.06, -0.06), (0.10, -0.03), (0.13, 0.02), (0.06, 0.05), (-0.06, 0.07)], hx, hy, 1.0, 90))
    horns = shape(lambda d: [brush(d, [(hx - 0.03 * s, hy + 0.0), (hx - 0.09 * s, hy - 0.08)], 0.02, 0.005)
                             for s in (-1, 1)])
    lit(c, lighter(head, horns), (150, 240, 255), lin((220, 250, 255), (80, 170, 220)), 10, 1.3)
    paint_fist(c, 0.5, 0.54, 0.80, glowc=(140, 230, 255))
    return finish(c)


def maru_kala():
    """The prime fists: a fist before a golden wheel of time."""
    c = bg((30, 30, 70), (4, 4, 12), 0.5, 0.5)
    whl = lighter(ring(0.5, 0.5, 0.36, 0.03), ring(0.5, 0.5, 0.22, 0.02),
                  shape(lambda d: [d.line(pts([(0.5 + math.cos(a) * 0.22, 0.5 + math.sin(a) * 0.22),
                                               (0.5 + math.cos(a) * 0.36, 0.5 + math.sin(a) * 0.36)]), fill=255,
                                          width=int(0.02 * W)) for a in [k * math.pi / 4 + 0.39 for k in range(8)]]))
    glow(c, whl, (255, 200, 90, 255), 16, 1.4)
    fill(c, soften(whl), lin(*GOLD))
    m = fist_m(0.5, 0.52, 0.85)
    prime_glass(c, m, top=(255, 255, 255), bot=(160, 210, 240))
    lines = shape(lambda d: K.fist_lines(d, 0.5, 0.52, 0.85))
    fill(c, scale(soften(lines, 1.5), 0.6), (60, 110, 150, 255))
    sparkles(c, [(0.80, 0.20, 0.06), (0.20, 0.80, 0.05)], glowc=(190, 240, 255))
    return finish(c)


def ruthless_stroke():
    """The prime dagger and three savage crimson rakes."""
    c = bg((120, 20, 40), (16, 2, 6), 0.5, 0.5)
    for k in range(3):
        o = (k - 1) * 0.12
        m = poly(tstroke([(0.20 + o, 0.12), (0.30 + o, 0.50), (0.24 + o, 0.90)], 0.0, 0.05))
        m = lighter(m, poly(tstroke([(0.24 + o, 0.90), (0.30 + o, 0.50), (0.20 + o, 0.12)], 0.0, 0.05)))
        m = rot(m, -20, 0.5, 0.5)
        glow(c, m, (255, 60, 70, 255), 10, 1.4)
        fill(c, soften(m), (255, 200, 200, 255))
    dm = dagger_m(0.66, 0.52, 0.80, 35)
    prime_glass(c, dm, glowc=(255, 160, 170))
    h = shape(lambda d: GB.draw_dagger(d, 0.66, 0.52, 0.80, 35, parts=(1, 2, 3)))
    fill(c, soften(h), lin(*GOLD))
    return finish(c)


def imperator():
    """The prime sword crowned with an emperor's laurel, purple and gold."""
    c = bg((100, 40, 140), (12, 4, 22), 0.5, 0.45)
    rays(c, 0.5, 0.30, 16, (255, 220, 150), alpha=80)
    R = 0.24
    wr = shape(lambda d: [GA.leaf(d, 0.5 + math.cos(a) * R, 0.40 + math.sin(a) * R, a + s * 1.9, 0.07, 0.024)
                          for a, s in [(math.radians(100 + k * 22), 1) for k in range(8)]
                          + [(math.radians(80 - k * 22), -1) for k in range(8)]])
    glow(c, wr, (255, 210, 110, 255), 10, 1.2)
    fill(c, soften(wr), lin(*GOLD))
    m = sword_m(0.5, 0.92, 0.5, 0.10, 0.05, 0.13, 0.15)
    prime_glass(c, m, glowc=(230, 200, 255))
    fill(c, soften(ImageChops.multiply(m, hilt_m(0.5, 0.92, 0.5, 0.10, 0.15, 0.13))), lin(*GOLD))
    gem = disc(0.5, 0.735, 0.022)
    glow(c, gem, (220, 120, 255, 255), 8, 1.4)
    fill(c, soften(gem), (200, 90, 255, 255))
    return finish(c)


def dagda():
    """The prime club: a great maul under a glowing triskelion."""
    c = bg((40, 120, 70), (4, 18, 8), 0.5, 0.40)
    tri = mask()
    d = ImageDraw.Draw(tri)
    for k in range(3):
        a0 = k * 120
        path = [(0.5 + math.cos(math.radians(a0 + t * 400)) * 0.30 * (1 - 0.85 * t) + math.cos(math.radians(a0 - 90))
                 * 0.10, 0.32 + math.sin(math.radians(a0 + t * 400)) * 0.30 * (1 - 0.85 * t) * 0.9)
                for t in [i / 40 for i in range(41)]]
        d.polygon(pts(tstroke(path, 0.012, 0.04)), fill=255)
    tri = shape(lambda d: [brush(d, [(0.5 + math.cos(math.radians(k * 120 + t * 360)) * 0.17 * (1 - t * 0.8) +
                                      math.cos(math.radians(k * 120 + 90)) * 0.10,
                                      0.34 + math.sin(math.radians(k * 120 + t * 360)) * 0.17 * (1 - t * 0.8) +
                                      math.sin(math.radians(k * 120 + 90)) * 0.10)
                                     for t in [i / 30 for i in range(31)]], 0.03, 0.012) for k in range(3)])
    glow(c, tri, (180, 255, 150, 255), 14, 1.5)
    fill(c, soften(tri), (230, 255, 210, 255))
    shaft = poly(T([(-0.022, 0.0), (0.022, 0.0), (0.03, 0.46), (-0.03, 0.46)], 0.50, 0.52, 1, 0))
    head = shape(lambda d: [d.rounded_rectangle(pts([(0.32, 0.46), (0.68, 0.66)]), radius=0.05 * W, fill=255)])
    head = rot(head, 0)
    m = lighter(shaft, head)
    prime_glass(c, m, glowc=(170, 255, 170), bot=(150, 210, 190))
    fill(c, soften(shaft), lin(*WOOD))
    bands = shape(lambda d: [d.rectangle(pts([(x, 0.46), (x + 0.03, 0.66)]), fill=255) for x in (0.38, 0.59)])
    fill(c, soften(bands), lin(*GOLD))
    return finish(c)


def oshala():
    """The prime staff: pale shaft, a pearl prime crystal blazing white and gold."""
    c = bg((60, 150, 160), (6, 20, 26), 0.6, 0.30)
    rays(c, 0.62, 0.30, 16, (255, 250, 220), alpha=90)
    shaft, fit, o, oc = staff_masks(0.20, 0.92, 0.56, 0.42, 0.08, 'claw', 0.11)
    keyline(c, lighter(shaft, fit), 9, (10, 30, 40, 235))
    prime_glass(c, shaft)
    fill(c, soften(fit), lin(*GOLD))
    glow(c, o, (255, 250, 220, 255), 24, 1.8)
    fill(c, soften(o), rad((255, 255, 255), (230, 220, 190), oc[0] - 0.02, oc[1] - 0.02, 0.1))
    sparkles(c, [(oc[0], oc[1], 0.16), (0.24, 0.22, 0.05)], glowc=(255, 250, 220))
    return finish(c)


def uriel_blade():
    c = bg((230, 190, 90), (60, 34, 10), 0.5, 0.36)
    rays(c, 0.5, 0.36, 20, (255, 255, 240), alpha=120, width=0.05)
    burst(c, 0.5, 0.36, 0.36, 0.10, 8, (255, 255, 255), (255, 230, 150), (255, 255, 230), 30, 1.6, -90)
    burst(c, 0.5, 0.36, 0.22, 0.06, 8, (255, 255, 255), (255, 250, 210), (255, 255, 255), 10, 1.0, -67.5)
    paint_sword(c, 0.5, 0.10, 0.5, 0.92, w=0.05, guard=0.12, glowc=(255, 255, 220),
                blade=((255, 255, 255), (200, 196, 180)))
    return finish(c)


def glory_slash():
    c = bg((180, 30, 40), (24, 2, 6), 0.5, 0.5)
    swoosh(c, 0.5, 0.56, 0.38, 170, 370, 0.12, (255, 230, 150), 0.9, (255, 200, 80))
    for k in range(3):
        a = math.radians(200 + k * 70)
        x, y = 0.5 + math.cos(a) * 0.38, 0.56 + math.sin(a) * 0.38
        m = poly(tstroke([(x - 0.06, y - 0.10), (x + 0.06, y + 0.10)], 0.0, 0.04))
        m = lighter(m, poly(tstroke([(x + 0.06, y + 0.10), (x - 0.06, y - 0.10)], 0.0, 0.04)))
        glow(c, m, (255, 240, 180, 255), 8, 1.5)
        fill(c, soften(m), (255, 255, 240, 255))
    paint_sword(c, 0.26, 0.86, 0.74, 0.26, w=0.05, guard=0.11, glowc=(255, 210, 120))
    stars = shape(lambda d: [GD.star(d, x, y, 0.045, 0.018) for x, y in ((0.72, 0.70), (0.84, 0.58), (0.62, 0.82))])
    glow(c, stars, (255, 240, 120, 255), 6, 1.4)
    fill(c, soften(stars), (255, 250, 180, 255))
    return finish(c)


def tartarus_torpor():
    c = bg((50, 40, 120), (6, 4, 20), 0.5, 0.40)
    moon = minus(disc(0.66, 0.26, 0.13), disc(0.72, 0.21, 0.11))
    glow(c, moon, (200, 200, 255, 255), 14, 1.4)
    fill(c, soften(moon), (240, 240, 255, 255))
    mist = shape(lambda d: [d.ellipse(pts([(x - r, y - r * 0.4), (x + r, y + r * 0.4)]), fill=150)
                            for x, y, r in ((0.24, 0.70, 0.2), (0.52, 0.78, 0.24), (0.80, 0.70, 0.2),
                                            (0.40, 0.88, 0.22), (0.70, 0.90, 0.2))])
    fill(c, mist.filter(ImageFilter.GaussianBlur(14)), (170, 120, 255, 255))
    zs = shape(lambda d: [brush(d, [(x - s, y - s), (x + s, y - s), (x - s, y + s), (x + s, y + s)], s * 0.45)
                          for x, y, s in ((0.74, 0.50, 0.035), (0.84, 0.40, 0.025))])
    glow(c, zs, (210, 200, 255, 255), 6, 1.4)
    fill(c, soften(zs), (240, 236, 255, 255))
    paint_staff(c, 0.30, 0.92, 0.42, 0.30, orb=((240, 230, 255), (90, 50, 200)), orb_glow=(170, 130, 255),
                wood=((70, 60, 100), (20, 16, 34)), orb_r=0.065)
    return finish(c)


def netherspikes():
    c = bg((60, 20, 50), (6, 0, 6), 0.5, 0.85, 0.8)
    under = poly([(0, 0.82), (1, 0.82), (1, 1), (0, 1)])
    glow(c, under, (255, 40, 60, 255), 30, 1.0)
    fill(c, soften(under, 3), (20, 4, 10, 255))
    sp = shape(lambda d: [d.polygon(pts([(x - w, 0.86), (x + w * 0.2, y), (x + w, 0.86)]), fill=255)
                          for x, y, w in ((0.50, 0.12, 0.09), (0.30, 0.34, 0.07), (0.70, 0.30, 0.07),
                                          (0.16, 0.56, 0.05), (0.84, 0.54, 0.05), (0.40, 0.52, 0.05),
                                          (0.60, 0.50, 0.05))])
    glow(c, sp, (255, 60, 90, 255), 14, 1.3)
    shadow(c, sp, 4, 6, 6, 150)
    fill(c, soften(sp), lin((150, 110, 170), (30, 10, 40)))
    edge = minus(sp, rot(sp, 0, 0.5, 0.5).transform(sp.size, Image.AFFINE, (1, 0, -6, 0, 1, 0)))
    fill(c, soften(edge), (255, 150, 170, 200))
    return finish(c)


def carnal_nightmare():
    c = bg((120, 10, 30), (8, 0, 4), 0.5, 0.5)
    rnd = random.Random(6)
    ten = mask()
    d = ImageDraw.Draw(ten)
    for k in range(8):
        a = math.radians(k * 45 + 20)
        path = [(0.5 + math.cos(a + math.sin(t * 5) * 0.25) * (0.48 - 0.30 * t),
                 0.5 + math.sin(a + math.sin(t * 5) * 0.25) * (0.48 - 0.30 * t)) for t in [i / 30 for i in range(31)]]
        d.polygon(pts(tstroke(path, 0.05, 0.005)), fill=255)
    fill(c, soften(ten, 2), lin((60, 0, 20), (10, 0, 4)))
    glow(c, ten, (255, 40, 60, 255), 6, 0.6)
    eye = shape(lambda d: GC.eye_shape(d, 0.5, 0.5, 0.26, 0.14))
    glow(c, eye, (255, 60, 60, 255), 24, 1.6)
    fill(c, soften(eye), lin((255, 220, 200), (220, 130, 120)))
    veins = shape(lambda d: [brush(d, [(0.5 + s * 0.24, 0.5 + o), (0.5 + s * 0.15, 0.5 + o * 0.5)], 0.008, 0.004)
                             for s in (-1, 1) for o in (-0.04, 0.03)])
    fill(c, soften(ImageChops.multiply(veins, eye)), (200, 30, 40, 255))
    iris = disc(0.5, 0.5, 0.11)
    fill(c, soften(iris), rad((255, 60, 40), (120, 0, 10), 0.5, 0.5, 0.11))
    pupil = shape(lambda d: d.ellipse(pts([(0.485, 0.40), (0.515, 0.60)]), fill=255))
    fill(c, soften(pupil), (10, 0, 0, 255))
    return finish(c)


def aegis_schism():
    """A great shield split down the middle, light blazing through the rift."""
    c = bg((40, 90, 120), (4, 10, 20), 0.5, 0.5)
    rift = poly([(0.5, 0.06), (0.56, 0.30), (0.48, 0.46), (0.56, 0.62), (0.5, 0.94), (0.44, 0.62), (0.52, 0.46),
                 (0.44, 0.30)])
    glow(c, rift, (170, 220, 255, 255), 26, 1.8)
    sh_m = shape(lambda d: GB.draw_shield(d, 0.5, 0.50, 0.86))
    in_m = shape(lambda d: GB.draw_shield(d, 0.5, 0.50, 0.86, inset=0.16))
    crack = [(0.5, 0.10), (0.53, 0.30), (0.47, 0.46), (0.53, 0.62), (0.5, 0.92)]
    left_side = poly(crack + [(0, 1), (0, 0)])

    def move(m, dx, deg, cx):
        m = m.transform(m.size, Image.AFFINE, (1, 0, -dx * W, 0, 1, 0))
        return m.rotate(deg, resample=Image.BICUBIC, center=p(cx, 0.85))
    for side, dx, deg, cx in ((1, -0.055, 4, 0.42), (0, 0.055, -4, 0.58)):
        half = ImageChops.multiply(sh_m, left_side) if side else minus(sh_m, left_side)
        inner = ImageChops.multiply(in_m, left_side) if side else minus(in_m, left_side)
        half, inner = move(half, dx, deg, cx), move(inner, dx, deg, cx)
        shadow(c, half, 5, 8, 8, 160)
        fill(c, soften(half), lin((230, 236, 250), (110, 120, 150)))
        fill(c, soften(inner), lin((70, 110, 190), (20, 40, 100)))
    bolt = shape(lambda d: brush(d, crack, 0.03, 0.012))
    glow(c, bolt, (190, 235, 255, 255), 14, 1.8)
    fill(c, soften(bolt), (255, 255, 235, 255))
    sparkles(c, [(0.5, 0.48, 0.10)], glowc=(255, 250, 210))
    return finish(c)


def dancing_chains():
    c = bg((40, 120, 120), (4, 18, 20), 0.5, 0.5)
    m = mask()
    d = ImageDraw.Draw(m)
    path = [(0.5 + math.cos(t * 3.2 * math.pi) * 0.34 * (0.35 + 0.65 * t), 0.5 + math.sin(t * 3.2 * math.pi) * 0.34
             * (0.35 + 0.65 * t)) for t in [i / 200 for i in range(201)]]
    acc, last = 0.0, path[0]
    links = []
    for q in path[1:]:
        acc += math.hypot(q[0] - last[0], q[1] - last[1])
        last = q
        if acc > 0.055:
            links.append(q)
            acc = 0
    for i in range(1, len(links)):
        (x0, y0), (x1, y1) = links[i - 1], links[i]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        o = [(math.cos(t) * 0.040, math.sin(t) * (0.022 if i % 2 else 0.010)) for t in
             [k * math.pi / 12 for k in range(24)]]
        iin = [(math.cos(t) * 0.024, math.sin(t) * (0.008 if i % 2 else 0.0)) for t in [k * math.pi / 12 for k in range(24)]]
        d.polygon(pts(T(o, cx, cy, 1, ang)), fill=255)
        if i % 2:
            d.polygon(pts(T(iin, cx, cy, 1, ang)), fill=0)
    glow(c, m, (170, 255, 240, 255), 10, 1.2)
    shadow(c, m, 4, 6, 6, 150)
    fill(c, soften(m), lin(*STEEL))
    swoosh(c, 0.5, 0.5, 0.42, 0, 140, 0.05, (200, 255, 245), 0.6)
    swoosh(c, 0.5, 0.5, 0.42, 180, 320, 0.05, (200, 255, 245), 0.6)
    return finish(c)


def barbed_crescent():
    c = bg((70, 110, 60), (8, 14, 6), 0.5, 0.5)
    cres = minus(disc(0.46, 0.5, 0.34), disc(0.60, 0.46, 0.30))
    bm = shape(lambda d: [d.polygon(pts(T([(0, -0.03), (0.09, 0.0), (0, 0.03)], 0.46 + math.cos(a) * 0.32,
                                           0.5 + math.sin(a) * 0.32, 1, math.degrees(a) + 30)), fill=255)
                          for a in [math.radians(x) for x in (120, 150, 180, 210, 240)]])
    m = lighter(cres, bm)
    glow(c, m, (200, 255, 150, 255), 14, 1.2)
    shadow(c, m, 5, 8, 8, 160)
    fill(c, soften(m), lin((240, 250, 230), (110, 130, 110)))
    edge = minus(cres, disc(0.48, 0.5, 0.31))
    fill(c, soften(edge), (255, 255, 240, 220))
    grip = poly(T([(-0.02, -0.12), (0.02, -0.12), (0.02, 0.12), (-0.02, 0.12)], 0.66, 0.5, 1, 0))
    fill(c, soften(grip), lin(*WOOD))
    dn = shape(lambda d: [GD.arrowhead(d, 0.84, y, 90, 0.06) for y in (0.34, 0.46)])
    fill(c, soften(dn), (255, 120, 100, 230))
    return finish(c)


def shackled_fists():
    c = bg((90, 80, 70), (12, 10, 8), 0.5, 0.45)
    paint_fist(c, 0.5, 0.40, 0.80, glowc=(255, 170, 110))
    cuff = shape(lambda d: d.rounded_rectangle(pts([(0.34, 0.56), (0.66, 0.66)]), radius=0.02 * W, fill=255))
    shadow(c, cuff, 4, 6, 6, 150)
    fill(c, soften(cuff), lin(*GUNMETAL))
    rivs = shape(lambda d: [d.ellipse(pts([(x - 0.012, 0.598), (x + 0.012, 0.622)]), fill=255) for x in (0.38, 0.62)])
    fill(c, soften(rivs), (200, 200, 210, 255))
    links = mask()
    d = ImageDraw.Draw(links)
    for i, (x, y) in enumerate([(0.50, 0.71), (0.45, 0.79), (0.38, 0.85), (0.29, 0.88)]):
        r = (0.045, 0.03) if i % 2 == 0 else (0.03, 0.045)
        d.ellipse(pts([(x - r[0], y - r[1]), (x + r[0], y + r[1])]), outline=255, width=int(0.02 * W))
    shadow(c, links, 3, 5, 5, 150)
    fill(c, soften(links), lin((240, 240, 250), (120, 120, 130)))
    brk = shape(lambda d: [GD.star(d, 0.22, 0.88, 0.06, 0.018, 6)])
    glow(c, brk, (255, 220, 150, 255), 8, 1.4)
    fill(c, soften(brk), (255, 250, 220, 255))
    return finish(c)


def foxfire():
    c = bg((30, 60, 120), (4, 6, 20), 0.5, 0.5)
    # a fox's tail made of ghostly flame, with three foxfire wisps around it
    tail = shape(lambda d: [GA.flame(d, 0.48, 0.92, 0.20, 0.74, 0.20), GA.flame(d, 0.50, 0.92, 0.12, 0.56, 0.15)])
    glow(c, tail, (90, 200, 255, 255), 22, 1.4)
    fill(c, soften(tail), lin((220, 250, 255), (60, 140, 255), 270))
    core = shape(lambda d: GA.flame(d, 0.50, 0.92, 0.07, 0.36, 0.10))
    fill(c, soften(core), (250, 255, 255, 255))
    for x, y, s in ((0.22, 0.30, 0.10), (0.80, 0.24, 0.09), (0.84, 0.66, 0.08)):
        w = shape(lambda d, x=x, y=y, s=s: GA.flame(d, x, y + s * 1.2, s * 0.6, s * 2.2, 0.02))
        glow(c, w, (100, 220, 255, 255), 12, 1.6)
        fill(c, soften(w), lin((240, 255, 255), (90, 190, 255), 270))
    return finish(c)


def grim_halo():
    c = bg((70, 20, 60), (4, 0, 6), 0.5, 0.30)
    hy = 0.25
    halo = ring(0.5, hy, 0.30, 0.045, 0.10)
    spikes = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * 0.30 - 0.022, hy + math.sin(a) * 0.10),
                                             (0.5 + math.cos(a) * 0.30, hy + math.sin(a) * 0.10 - 0.10),
                                             (0.5 + math.cos(a) * 0.30 + 0.022, hy + math.sin(a) * 0.10)]), fill=255)
                              for a in [k * math.pi / 5 + 0.3 for k in range(10)]])
    m = lighter(halo, spikes)
    glow(c, m, (255, 40, 70, 255), 18, 1.6)
    fill(c, soften(m), lin((255, 190, 190), (170, 20, 40)))
    sk = shape(lambda d: GB.skull(d, 0.5, 0.64, 0.95))
    eyes = skull_eyes(0.5, 0.64, 0.95)
    shadow(c, sk, 5, 8, 8, 160)
    glow(c, eyes, (255, 40, 60, 255), 8, 1.6)
    lit(c, sk, (140, 40, 80), lin((235, 225, 215), (130, 120, 115)), 10, 1.0)
    fill(c, soften(eyes), (255, 70, 60, 255))
    return finish(c)


def dimensional_death():
    """A tear in the world, a starfield beyond it, death's skull leering through."""
    c = bg((60, 30, 90), (4, 2, 10), 0.5, 0.5)
    tear = poly([(0.50, 0.04), (0.60, 0.24), (0.56, 0.36), (0.68, 0.52), (0.58, 0.70), (0.62, 0.96), (0.46, 0.76),
                 (0.40, 0.58), (0.32, 0.46), (0.42, 0.30)])
    glow(c, tear, (190, 100, 255, 255), 26, 1.8)
    fill(c, soften(tear), rad((40, 10, 70), (4, 0, 10), 0.5, 0.5, 0.4))
    rnd = random.Random(14)
    stars = shape(lambda d: [d.ellipse(pts([(x - 0.006, y - 0.006), (x + 0.006, y + 0.006)]), fill=255)
                             for x, y in [(rnd.uniform(0.3, 0.7), rnd.uniform(0.05, 0.95)) for _ in range(40)]])
    fill(c, ImageChops.multiply(soften(stars), tear), (255, 240, 255, 255))
    sk = ImageChops.multiply(shape(lambda d: GB.skull(d, 0.5, 0.52, 0.85)), tear)
    fill(c, scale(soften(sk, 2), 0.75), (220, 200, 255, 255))
    edge = minus(soften(tear, 3).point(lambda v: 255 if v > 30 else 0), soften(tear, 3).point(lambda v: 255 if v > 200 else 0))
    fill(c, soften(edge), (240, 200, 255, 255))
    return finish(c)


ICONS = {
    ('ja', 'Heavy Swing'): heavy_swing,
    ('ja', 'Rock Crusher'): rock_crusher,
    ('ja', 'Earth Crusher'): earth_crusher,
    ('ja', 'Starburst'): starburst,
    ('ja', 'Sunburst'): sunburst,
    ('ja', 'Shell Crusher'): shell_crusher,
    ('ja', 'Full Swing'): full_swing,
    ('ja', 'Spirit Taker'): spirit_taker,
    ('ja', 'Retribution'): retribution,
    ('ja', 'Gate of Tartarus'): gate_of_tartarus,
    ('ja', 'Vidohunir'): vidohunir,
    ('ja', 'Garland of Bliss'): garland_of_bliss,
    ('ja', 'Omniscience'): omniscience,
    ('ja', 'Cataclysm'): cataclysm,
    ('ja', 'Myrkr'): myrkr,
    ('ja', 'Shattersoul'): shattersoul,
    ('ja', 'Flaming Arrow'): flaming_arrow,
    ('ja', 'Piercing Arrow'): piercing_arrow,
    ('ja', 'Dulling Arrow'): dulling_arrow,
    ('ja', 'Sidewinder'): sidewinder,
    ('ja', 'Blast Arrow'): blast_arrow,
    ('ja', 'Arching Arrow'): arching_arrow,
    ('ja', 'Empyreal Arrow'): empyreal_arrow,
    ('ja', 'Namas Arrow'): namas_arrow,
    ('ja', 'Refulgent Arrow'): refulgent_arrow,
    ('ja', "Jishnu's Radiance"): jishnus_radiance,
    ('ja', 'Apex Arrow'): apex_arrow,
    ('ja', 'Sarv'): sarv,
    ('ja', 'Hot Shot'): hot_shot,
    ('ja', 'Split Shot'): split_shot,
    ('ja', 'Sniper Shot'): sniper_shot,
    ('ja', 'Slug Shot'): slug_shot,
    ('ja', 'Blast Shot'): blast_shot,
    ('ja', 'Heavy Shot'): heavy_shot,
    ('ja', 'Detonator'): detonator,
    ('ja', 'Coronach'): coronach,
    ('ja', 'Trueflight'): trueflight,
    ('ja', 'Leaden Salute'): leaden_salute,
    ('ja', 'Numbing Shot'): numbing_shot,
    ('ja', 'Wildfire'): wildfire,
    ('ja', 'Last Stand'): last_stand,
    ('ja', 'Terminus'): terminus,
    ('ja', 'Exenterator'): exenterator,
    ('ja', 'Chant du Cygne'): chant_du_cygne,
    ('ja', 'Requiescat'): requiescat,
    ('ja', 'Knights of Rotund'): knights_of_round,
    ('ja', 'Final Paradise'): final_paradise,
    ('ja', 'Fast Blade II'): fast_blade_ii,
    ('ja', 'Dragon Blow'): dragon_blow,
    ('ja', 'Maru Kala'): maru_kala,
    ('ja', 'Ruthless Stroke'): ruthless_stroke,
    ('ja', 'Imperator'): imperator,
    ('ja', 'Dagda'): dagda,
    ('ja', 'Oshala'): oshala,
    ('ja', 'Uriel Blade'): uriel_blade,
    ('ja', 'Glory Slash'): glory_slash,
    ('ja', 'Tartarus Torpor'): tartarus_torpor,
    ('ja', 'Netherspikes'): netherspikes,
    ('ja', 'Carnal Nightmare'): carnal_nightmare,
    ('ja', 'Aegis Schism'): aegis_schism,
    ('ja', 'Dancing Chains'): dancing_chains,
    ('ja', 'Barbed Crescent WS'): barbed_crescent,
    ('ja', 'Shackled Fists'): shackled_fists,
    ('ja', 'Foxfire'): foxfire,
    ('ja', 'Grim Halo'): grim_halo,
    ('ja', 'Vulcan Shot'): vulcan_shot,
    ('ja', 'Dimensional Death WS'): dimensional_death,
}

# 'Barbed Crescent' and 'Dimensional Death' are also Blue Magic spells (painted by blue_magic.py); the weapon skills
# get their own textures so neither painting overwrites the other.
COVERS = {'Barbed Crescent WS': ['Barbed Crescent'], 'Dimensional Death WS': ['Dimensional Death']}
