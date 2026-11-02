"""Signature icons, round 2, abilities 1: job abilities across the jobs (WAR..SCH) not painted in round 1.

Pure menu categories (Pet commands, Sambas, Waltzes, Jigs, Steps, Flourishes I/II, Stratagems) never sit on a bar as
actions and are left out.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as GA
import group_b as GB
import group_c as GC
import group_d as GD

W = K.W
p, pts = K.p, K.pts
bg, lit, poly, ell, col, scale, rot = GD.bg, GD.lit, GD.poly, GD.ell, GD.col, GD.scale, GD.rot
sparkles, motes, rays, brush, arc_path = GD.sparkles, GD.motes, GD.rays, GD.stroke, GD.arc_path
xf = GB.xf


# ---- helpers --------------------------------------------------------------------------------------------------------
def lin(c0, c1, angle=90):
    return K.linear(col(c0), col(c1), angle)


def rad(c0, c1, cx=0.5, cy=0.5, r=0.5):
    return K.radial(col(c0), col(c1), cx, cy, r)


def steel():
    return lin((250, 250, 255), (140, 150, 175))


def gold():
    return lin((255, 240, 170), (205, 136, 46))


def fade_down(m, start=0.35, end=0.95):
    """Mask m fading out from y=start to y=end."""
    g = Image.new('L', (W, W), 0)
    px = g.load()
    for y in range(W):
        t = y / W
        v = 255 if t <= start else (0 if t >= end else int(255 * (end - t) / (end - start)))
        for x in range(W):
            px[x, y] = v
    return ImageChops.multiply(m, g)


def fade_along(m, x0, y0, x1, y1):
    """Mask m fading from opaque at (x0, y0) to clear at (x1, y1)."""
    g = Image.new('L', (W // 4, W // 4), 0)
    px = g.load()
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    n = W // 4
    for y in range(n):
        for x in range(n):
            t = ((x / n - x0) * dx + (y / n - y0) * dy) / L2
            px[x, y] = int(255 * max(0.0, min(1.0, 1 - t)))
    return ImageChops.multiply(m, g.resize((W, W), Image.BILINEAR))


def emboss(c, m, light, dark, dx=3, dy=4):
    K.fill(c, K.soften(ImageChops.offset(m, dx, dy), 1.5), col(dark))
    K.fill(c, K.soften(ImageChops.offset(m, -2, -2), 1.2), (255, 255, 255, 120))
    K.fill(c, K.soften(m), col(light) if isinstance(light, tuple) else light)


def block_arrow(d, x0, y0, x1, y1, w=0.07, hw=0.15, hl=0.18):
    L, f = GC.frame(x0, y0, x1, y1)
    d.polygon(pts([f(0, -w / 2), f(L - hl, -w / 2), f(L - hl, -hw), f(L, 0), f(L - hl, hw), f(L - hl, w / 2),
                   f(0, w / 2)]), fill=255)


def burst(cx, cy, n, r1, r2, rot0=0.0):
    return poly(GA.star_pts(cx, cy, n, r1, r2, rot0))


def stun_stars(c, cx, cy, rx, ry, color=(255, 236, 120)):
    m = K.shape(lambda d: [GD.star(d, cx + math.cos(a) * rx, cy + math.sin(a) * ry, 0.055, 0.024)
                           for a in (math.radians(200), math.radians(270), math.radians(340))])
    ring = K.shape(lambda d: d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255,
                                       width=int(0.010 * W)))
    K.fill(c, scale(K.soften(ring, 2), 0.5), col(color))
    lit(c, m, color, (255, 250, 210), 8, 1.3)


def rrect(w, h, r, n=6):
    """Rounded rectangle (local, centred) as points."""
    q = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            q.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return q


AXE_HANDLE = [(-0.032, -0.44), (0.032, -0.44), (0.036, 0.46), (-0.036, 0.46)]
AXE_HEAD = [(0.02, -0.40), (0.14, -0.46), (0.28, -0.52), (0.34, -0.33), (0.30, -0.13), (0.15, -0.19), (0.02, -0.25)]
AXE_SPIKE = [(-0.02, -0.39), (-0.15, -0.33), (-0.02, -0.28)]


def hand_axe(c, cx, cy, s, ang, glowc, alpha=1.0, flat=None):
    head = K.shape(lambda d: [d.polygon(xf(AXE_HEAD, cx, cy, s, ang), fill=255),
                              d.polygon(xf(AXE_SPIKE, cx, cy, s, ang), fill=255)])
    handle = K.shape(lambda d: d.polygon(xf(AXE_HANDLE, cx, cy, s, ang), fill=255))
    if flat:
        K.fill(c, scale(K.soften(ImageChops.lighter(head, handle), 3), alpha), col(flat))
        return
    both = ImageChops.lighter(head, handle)
    K.glow(c, both, col(glowc), 14, 1.2)
    K.shadow(c, both, 5, 8, 8, 160)
    K.fill(c, K.soften(handle), lin((150, 90, 50), (80, 40, 20)))
    K.fill(c, K.soften(head), lin((255, 250, 240), (140, 140, 160)))
    edge = K.shape(lambda d: d.line(xf([(0.28, -0.52), (0.34, -0.33), (0.30, -0.13)], cx, cy, s, ang), fill=255,
                                     width=int(0.016 * W)))
    K.fill(c, scale(K.soften(edge), 0.8), (255, 255, 255, 255))


def wax_seal(c, cx, cy, r, light, dark, glowc, seed=1):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    outline = []
    for i in range(120):
        a = 2 * math.pi * i / 120
        k = 1 + 0.045 * math.sin(7 * a + ph[0]) + 0.03 * math.sin(12 * a + ph[1]) + 0.02 * math.sin(5 * a + ph[2])
        outline.append((cx + math.cos(a) * r * k, cy + math.sin(a) * r * k))
    m = poly(outline)
    K.glow(c, m, col(glowc), 22, 1.3)
    K.shadow(c, m, 5, 8, 8, 170)
    K.fill(c, K.soften(m), rad(light, dark, cx - r * 0.3, cy - r * 0.35, r * 1.7))
    groove = K.shape(lambda d: d.ellipse(pts([(cx - r * 0.78, cy - r * 0.78), (cx + r * 0.78, cy + r * 0.78)]),
                                         outline=255, width=int(0.016 * W)))
    K.fill(c, K.soften(ImageChops.offset(groove, -2, -2)), (255, 255, 255, 90))
    K.fill(c, K.soften(groove), col(dark))


def maple(d, cx, cy, s, ang=0.0):
    q = []
    lobes = [(-90, 1.0), (-35, 0.88), (35, 0.62), (145, 0.62), (215, 0.88)]
    for i, (a, L) in enumerate(lobes):
        a2 = lobes[(i + 1) % 5][0] + (360 if i == 4 else 0)
        for da, rr in ((-14, L * 0.62), (-6, L * 0.75), (0, L), (6, L * 0.75), (14, L * 0.62)):
            q.append((math.cos(math.radians(a + da)) * rr, math.sin(math.radians(a + da)) * rr))
        mid = (a + a2) / 2
        q.append((math.cos(math.radians(mid)) * 0.30, math.sin(math.radians(mid)) * 0.30))
    d.polygon(xf(q, cx, cy, s, ang), fill=255)
    d.polygon(xf([(-0.03, 0.2), (0.03, 0.2), (0.05, 0.75), (0.01, 0.75)], cx, cy, s, ang), fill=255)


# ---- WAR ------------------------------------------------------------------------------------------------------------
def defender():
    """A round steel targe, up-chevrons embossed on its face (defence up)."""
    c = bg((70, 110, 170), (8, 12, 28))
    rays(c, 0.5, 0.52, 12, (200, 225, 255), 0.05, 0.7, 60, 8)
    disc = ell(0.17, 0.19, 0.83, 0.85)
    lit(c, disc, (170, 210, 255), lin((240, 244, 252), (100, 110, 140)), 22, 1.2, sh=True)
    face = ell(0.235, 0.255, 0.765, 0.785)
    K.fill(c, K.soften(face), rad((96, 140, 210), (24, 38, 86), 0.42, 0.38, 0.46))
    rv = K.shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.298 - 0.015, 0.52 + math.sin(a) * 0.298 - 0.015),
                                           (0.5 + math.cos(a) * 0.298 + 0.015, 0.52 + math.sin(a) * 0.298 + 0.015)]),
                                      fill=255) for a in [i * math.pi / 4 + math.pi / 8 for i in range(8)]])
    K.fill(c, K.soften(rv), (255, 236, 190, 255))
    chev = K.shape(lambda d: [d.polygon(pts([(0.5, y0), (0.67, y0 + 0.15), (0.67, y0 + 0.24), (0.5, y0 + 0.09),
                                             (0.33, y0 + 0.24), (0.33, y0 + 0.15)]), fill=255)
                              for y0 in (0.30, 0.48)])
    K.glow(c, chev, (200, 230, 255, 255), 10, 1.3)
    emboss(c, chev, lin((255, 255, 255), (170, 205, 245)), (10, 16, 40))
    return K.finish(c)


def aggressor():
    """A horned war helm, eyes burning in the visor (all-out attack)."""
    c = bg((210, 84, 30), (28, 6, 4), 0.5, 0.5, 0.7)
    motes(c, 21, 16, (0.1, 0.1, 0.9, 0.6), (0.006, 0.013), (255, 200, 120), (255, 120, 40))
    horns = K.shape(lambda d: [d.polygon(pts(GC.stroke([(0.5 + s * 0.17, 0.42), (0.5 + s * 0.31, 0.36),
                                                           (0.5 + s * 0.40, 0.22), (0.5 + s * 0.36, 0.07)],
                                                          0.10, 0.012)), fill=255) for s in (-1, 1)])
    lit(c, horns, (255, 200, 140), lin((255, 250, 232), (180, 150, 110)), 10, 1.0, sh=True)
    helm = ImageChops.lighter(ell(0.29, 0.25, 0.71, 0.70),
                              poly([(0.29, 0.48), (0.71, 0.48), (0.69, 0.80), (0.59, 0.86), (0.555, 0.68),
                                    (0.445, 0.68), (0.41, 0.86), (0.31, 0.80)]))
    lit(c, helm, (255, 150, 80), lin((240, 214, 170), (120, 76, 44)), 18, 1.2, sh=True)
    ridge = K.shape(lambda d: d.rounded_rectangle(pts([(0.485, 0.24), (0.515, 0.48)]), radius=0.01 * W, fill=255))
    K.fill(c, K.soften(ridge), (255, 240, 200, 220))
    visor = K.shape(lambda d: [d.polygon(pts([(0.33, 0.50), (0.67, 0.50), (0.65, 0.57), (0.35, 0.57)]), fill=255),
                               d.rectangle(pts([(0.475, 0.50), (0.525, 0.70)]), fill=255)])
    K.fill(c, K.soften(visor), (20, 6, 4, 255))
    eyes = K.shape(lambda d: [GC.eye_shape(d, x, 0.535, 0.055, 0.018) for x in (0.40, 0.60)])
    K.glow(c, eyes, (255, 60, 20, 255), 10, 1.8)
    K.fill(c, K.soften(eyes), (255, 230, 150, 255))
    return K.finish(c)


def warriors_charge():
    """A war axe mid-swing, two after-images trailing (the next blows land as a flurry)."""
    c = bg((240, 160, 40), (50, 14, 4), 0.55, 0.45, 0.72)
    arcm = K.shape(lambda d: brush(d, arc_path(0.44, 0.66, 0.38, 0.38, 195, 280, 30), 0.012, 0.07))
    K.fill(c, scale(K.soften(arcm, 6), 0.7), (255, 245, 210, 255))
    for ang, a in ((-60, 0.5), (-30, 0.8)):
        hand_axe(c, 0.44, 0.66, 0.78, ang, None, a, (255, 226, 160))
    hand_axe(c, 0.44, 0.66, 0.78, 4, (255, 220, 120))
    motes(c, 4, 12, (0.15, 0.1, 0.85, 0.5), (0.006, 0.012), (255, 240, 200), (255, 160, 60))
    return K.finish(c)


def tomahawk():
    """A hand axe spinning end over end through the air."""
    c = bg((40, 140, 130), (4, 20, 22))
    spin = K.shape(lambda d: [brush(d, arc_path(0.5, 0.5, 0.40, 0.40, a0, a0 + 80, 30), 0.006, 0.04)
                              for a0 in (190, 10)])
    K.glow(c, spin, (200, 255, 240, 255), 8, 1.2)
    K.fill(c, K.soften(spin), (235, 255, 250, 255))
    hand_axe(c, 0.5, 0.54, 0.74, 52, (190, 255, 235))
    streaks = K.shape(lambda d: [d.line(pts([(x0, y0), (x0 + 0.16, y0 - 0.10)]), fill=150, width=int(0.014 * W))
                                 for x0, y0 in ((0.08, 0.66), (0.12, 0.78), (0.20, 0.88))])
    K.fill(c, K.soften(streaks, 3), (220, 255, 245, 255))
    return K.finish(c)


def restraint():
    """A clenched fist bound tight in chains, power building under them."""
    c = bg((150, 34, 96), (18, 4, 14))
    rays(c, 0.5, 0.5, 14, (255, 160, 220), 0.05, 0.7, 70, 8)
    fist = K.shape(lambda d: K.fist_front(d, 0.5, 0.54, 0.95))
    K.glow(c, fist, (255, 120, 200, 255), 24, 1.3)
    K.shadow(c, fist, 5, 8, 8, 150)
    K.fill(c, K.soften(fist), lin((255, 226, 196), (210, 140, 100)))
    ln = K.shape(lambda d: K.fist_lines(d, 0.5, 0.54, 0.95))
    K.fill(c, scale(K.soften(ln, 1.5), 0.7), (120, 60, 40, 255))

    def chain(d, fillv=255):
        for i in range(9):
            x = 0.06 + i * 0.11
            if i % 2 == 0:
                d.ellipse(pts([(x - 0.07, 0.585), (x + 0.07, 0.665)]), outline=fillv, width=int(0.024 * W))
            else:
                d.rounded_rectangle(pts([(x - 0.07, 0.608), (x + 0.07, 0.642)]), radius=0.015 * W, fill=fillv)
    ch = K.shape(chain)
    K.shadow(c, ch, 3, 6, 5, 180)
    K.fill(c, K.soften(ch), lin((250, 250, 255), (120, 120, 140)))
    return K.finish(c)


# ---- MNK ------------------------------------------------------------------------------------------------------------
def dodge():
    """A monk leaning clear, the blow's wake curving past."""
    c = bg((70, 170, 100), (6, 26, 12), 0.55, 0.45)
    sw = K.shape(lambda d: [brush(d, arc_path(0.66, 0.52, r, r, 140, 235, 30), 0.006, w)
                            for r, w in ((0.34, 0.05), (0.42, 0.035), (0.26, 0.03))])
    K.glow(c, sw, (210, 255, 220, 255), 8, 1.2)
    K.fill(c, K.soften(sw), (240, 255, 244, 255))
    fig = rot(K.shape(lambda d: K.figure(d, 0.64, 0.54, 0.82)), -14, 0.64, 0.7)
    K.glow(c, fig, (220, 255, 230, 255), 10, 1.7)
    K.fill(c, K.soften(fig), lin((30, 60, 40), (8, 20, 12)))
    return K.finish(c)


def chi_blast():
    """A ball of ki hurled from the palm, a comet tail behind it."""
    c = bg((30, 120, 190), (4, 14, 34), 0.58, 0.42)
    tail = K.shape(lambda d: d.polygon(pts(GC.stroke([(0.10, 0.90), (0.30, 0.70), (0.58, 0.42)], 0.02, 0.30)),
                                       fill=255))
    K.fill(c, scale(fade_along(tail, 0.58, 0.42, 0.10, 0.90).filter(ImageFilter.GaussianBlur(8)), 0.9),
           (150, 230, 255, 255))
    rays(c, 0.58, 0.42, 14, (210, 245, 255), 0.05, 0.4, 110, 5)
    orb = ell(0.42, 0.26, 0.74, 0.58)
    K.glow(c, orb, (140, 230, 255, 255), 30, 1.6)
    K.fill(c, K.soften(orb, 2), rad((255, 255, 255), (90, 200, 255), 0.55, 0.38, 0.17))
    aura = ImageChops.subtract(burst(0.58, 0.42, 13, 0.25, 0.15, 0.3), ell(0.44, 0.28, 0.72, 0.56))
    K.glow(c, aura, (120, 220, 255, 255), 8, 1.2)
    K.fill(c, scale(K.soften(aura, 2), 0.8), (210, 245, 255, 255))
    sparkles(c, [(0.80, 0.18, 0.07), (0.30, 0.30, 0.05)], (255, 255, 255), (170, 230, 255))
    return K.finish(c)


def mantra():
    """Prayer beads around a glowing heart (maximum HP raised for the party)."""
    c = bg((230, 150, 50), (46, 18, 4), 0.5, 0.45)
    rays(c, 0.5, 0.47, 12, (255, 240, 190), 0.05, 0.7, 70, 8)
    beads = K.shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.30 - 0.037, 0.47 + math.sin(a) * 0.30 - 0.037),
                                              (0.5 + math.cos(a) * 0.30 + 0.037, 0.47 + math.sin(a) * 0.30 + 0.037)]),
                                         fill=255)
                               for a in [math.pi / 2 + (i + 0.5) * 2 * math.pi / 17 for i in range(16)]])
    guru = ell(0.45, 0.73, 0.55, 0.83)
    tassel = poly([(0.47, 0.82), (0.53, 0.82), (0.58, 0.96), (0.42, 0.96)])
    K.shadow(c, ImageChops.lighter(beads, guru), 3, 6, 5, 170)
    K.fill(c, K.soften(tassel), lin((255, 120, 60), (170, 40, 20)))
    K.fill(c, K.soften(ImageChops.lighter(beads, guru)), rad((240, 170, 120), (110, 44, 20), 0.5, 0.42, 0.4))
    hl = K.shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.30 - 0.024, 0.47 + math.sin(a) * 0.30 - 0.026),
                                           (0.5 + math.cos(a) * 0.30 - 0.004, 0.47 + math.sin(a) * 0.30 - 0.008)]),
                                      fill=255) for a in [math.pi / 2 + (i + 0.5) * 2 * math.pi / 17 for i in range(16)]])
    K.fill(c, scale(K.soften(hl), 0.7), (255, 240, 220, 255))
    h = K.shape(lambda d: GB.heart(d, 0.5, 0.47, 0.42))
    K.glow(c, h, (255, 230, 160, 255), 22, 1.6)
    K.fill(c, K.soften(h), lin((255, 140, 120), (210, 30, 40)))
    sparkles(c, [(0.56, 0.40, 0.05)], (255, 255, 255), (255, 220, 200))
    return K.finish(c)


def formless_strikes():
    """A fist dissolving into spirit mist (blows that strike past armour)."""
    c = bg((150, 100, 210), (16, 8, 30))
    fist = K.shape(lambda d: K.fist_front(d, 0.5, 0.44, 1.0))
    K.glow(c, fist, (230, 200, 255, 255), 26, 1.5)
    ghost = fade_down(fist, 0.38, 0.74)
    K.fill(c, K.soften(ghost, 2), lin((255, 250, 255), (200, 170, 245)))
    ln = K.shape(lambda d: K.fist_lines(d, 0.5, 0.44, 1.0))
    K.fill(c, scale(K.soften(fade_down(ln, 0.38, 0.74), 1.5), 0.6), (110, 70, 160, 255))
    wisps = K.shape(lambda d: [brush(d, [(x, 0.60), (x + dx * 0.5, 0.72), (x - dx * 0.2, 0.82), (x + dx, 0.92)],
                                     0.04, 0.005) for x, dx in ((0.36, 0.05), (0.46, -0.06), (0.56, 0.06),
                                                                (0.64, -0.04))])
    K.fill(c, scale(K.soften(wisps, 4), 0.7), (235, 220, 255, 255))
    motes(c, 9, 14, (0.22, 0.55, 0.78, 0.92), (0.006, 0.012), (255, 250, 255), (210, 180, 255))
    return K.finish(c)


def footwork():
    """A wrapped shin and bare foot driving down in a flying kick, an impact burst at the toes."""
    def T(seq, ang=35, cx=0.38, cy=0.42, s=0.95):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        return [(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in seq]
    c = bg((236, 120, 44), (44, 8, 6), 0.70, 0.72, 0.80)
    b = burst(0.70, 0.73, 12, 0.32, 0.12, 0.2)
    lit(c, b, (255, 236, 160), rad((255, 255, 236), (255, 170, 60), 0.70, 0.73, 0.30), 20, 1.5)
    st = K.shape(lambda d: [brush(d, T([(x, -0.95), (x, -0.45)]), 0.004, 0.028) for x in (-0.28, 0.24)] +
                           [brush(d, T([(0.38, -0.70), (0.38, -0.30)]), 0.004, 0.022)])
    K.fill(c, scale(K.soften(st, 2), 0.75), (255, 240, 210, 255))
    leg = poly(T([(0.07, -0.80), (0.075, -0.30), (0.07, -0.08), (0.16, -0.03), (0.30, 0.03), (0.38, 0.06),
                  (0.43, 0.09), (0.43, 0.13), (0.38, 0.15), (0.22, 0.15), (0.10, 0.13), (-0.02, 0.16), (-0.09, 0.15),
                  (-0.12, 0.09), (-0.11, -0.02), (-0.12, -0.20), (-0.15, -0.42), (-0.12, -0.80)]))
    out = leg.filter(ImageFilter.MaxFilter(11))
    K.shadow(c, out, 6, 9, 9, 190)
    K.fill(c, K.soften(out, 1.5), (60, 16, 6, 255))
    K.fill(c, K.soften(leg), lin((255, 230, 196), (214, 140, 96), 0))
    shade = ImageChops.subtract(leg, ImageChops.offset(leg, -int(0.04 * W), -int(0.03 * W)))
    K.fill(c, scale(K.soften(shade, 4), 0.5), (150, 70, 40, 255))
    wrap = ImageChops.multiply(leg, K.shape(lambda d: [d.line(pts(T([(-0.3, y), (0.3, y + 0.03)])), fill=255,
                                                              width=int(0.036 * W)) for y in (-0.44, -0.33, -0.22)]))
    K.fill(c, K.soften(wrap), lin((255, 255, 250), (220, 210, 196)))
    toes = K.shape(lambda d: [d.line(pts(T([(x, 0.07), (x + 0.01, 0.13)])), fill=255, width=int(0.008 * W))
                              for x in (0.33, 0.38)])
    K.fill(c, scale(K.soften(toes), 0.6), (130, 60, 30, 255))
    return K.finish(c)


def perfect_counter():
    """A strike turned straight back on the attacker: a dark blow in, a golden one out."""
    c = bg((190, 44, 44), (28, 4, 6), 0.5, 0.55)
    inc = K.shape(lambda d: block_arrow(d, 0.06, 0.24, 0.42, 0.62, 0.06, 0.11, 0.14))
    K.fill(c, scale(K.soften(fade_along(inc, 0.42, 0.62, 0.0, 0.2), 2), 0.8), (60, 10, 14, 255))
    b = burst(0.46, 0.66, 9, 0.17, 0.07, 0.1)
    lit(c, b, (255, 220, 140), rad((255, 255, 230), (255, 170, 60), 0.46, 0.66, 0.17), 14, 1.3)
    out = K.shape(lambda d: block_arrow(d, 0.46, 0.66, 0.88, 0.16, 0.10, 0.17, 0.20))
    K.glow(c, out, (255, 210, 120, 255), 18, 1.4)
    K.shadow(c, out, 5, 8, 8, 160)
    K.fill(c, K.soften(out), lin((255, 248, 200), (230, 150, 40)))
    sparkles(c, [(0.24, 0.80, 0.06)], (255, 255, 255), (255, 200, 140))
    return K.finish(c)


# ---- seals (WHM, BLM, DRK) ------------------------------------------------------------------------------------------
def divine_seal():
    """A white wax seal stamped with a star of light."""
    c = bg((120, 196, 156), (8, 34, 22), 0.5, 0.45)
    rays(c, 0.5, 0.5, 16, (255, 255, 230), 0.05, 0.75, 80, 8)
    wax_seal(c, 0.5, 0.52, 0.34, (255, 252, 240), (196, 178, 140), (255, 255, 220), 3)
    st = K.shape(lambda d: K.sparkle(d, 0.5, 0.52, 0.20, 0.22))
    emboss(c, st, gold(), (120, 96, 50))
    sparkles(c, [(0.80, 0.20, 0.08), (0.18, 0.78, 0.05)], (255, 255, 255), (220, 255, 230))
    return K.finish(c)


def elemental_seal():
    """A violet wax seal stamped with a hexagram, the six elements studding its rim."""
    c = bg((90, 50, 160), (8, 4, 22), 0.5, 0.45)
    wax_seal(c, 0.5, 0.52, 0.34, (214, 140, 255), (80, 24, 130), (200, 140, 255), 5)
    hexa = K.shape(lambda d: [d.polygon(pts(GA.star_pts(0.5, 0.52, 3, 0.20, 0.10, r)), outline=255,
                                        width=int(0.03 * W)) for r in (-math.pi / 2, math.pi / 2)])
    emboss(c, hexa, lin((255, 240, 255), (220, 180, 255)), (50, 10, 80))
    els = [(255, 90, 50), (140, 215, 255), (110, 230, 110), (235, 190, 80), (210, 120, 255), (70, 120, 255)]
    for i, rgb in enumerate(els):
        a = -math.pi / 2 + i * math.pi / 3 + math.pi / 6
        x, y = 0.5 + math.cos(a) * 0.265, 0.52 + math.sin(a) * 0.265
        gem = ell(x - 0.04, y - 0.04, x + 0.04, y + 0.04)
        K.glow(c, gem, col(rgb), 8, 1.4)
        K.fill(c, K.soften(gem), rad((255, 255, 255), rgb, x - 0.012, y - 0.012, 0.05))
    return K.finish(c)


def dark_seal():
    """A blood-red wax seal stamped with a skull."""
    c = bg((70, 14, 40), (6, 0, 4), 0.5, 0.45)
    wax_seal(c, 0.5, 0.52, 0.34, (210, 50, 60), (70, 6, 14), (200, 60, 160), 9)
    sk = K.shape(lambda d: GB.skull(d, 0.5, 0.51, 0.62))
    emboss(c, sk, lin((255, 200, 200), (210, 110, 110)), (40, 0, 6))
    return K.finish(c)


# ---- WHM ------------------------------------------------------------------------------------------------------------
def martyr():
    """A heart giving its own light away, a ribbon of it flowing to a healing cross."""
    c = bg((196, 80, 100), (28, 6, 12), 0.45, 0.55)
    path = GA.bezier((0.42, 0.52), (0.46, 0.26), (0.66, 0.30), 24)
    rib = K.shape(lambda d: brush(d, path, 0.07, 0.02))
    K.glow(c, rib, (255, 230, 180, 255), 12, 1.3)
    K.fill(c, K.soften(rib, 2), (255, 244, 210, 255))
    h = K.shape(lambda d: GB.heart(d, 0.40, 0.62, 0.56))
    K.glow(c, h, (255, 170, 160, 255), 24, 1.5)
    K.shadow(c, h, 5, 8, 8, 150)
    K.fill(c, K.soften(h), lin((255, 130, 130), (190, 20, 40)))
    hi = ell(0.29, 0.54, 0.35, 0.59)
    K.fill(c, K.soften(hi, 4), (255, 230, 230, 200))
    cr = K.shape(lambda d: [d.rounded_rectangle(pts([(0.665, 0.17), (0.735, 0.43)]), radius=0.02 * W, fill=255),
                            d.rounded_rectangle(pts([(0.57, 0.265), (0.83, 0.335)]), radius=0.02 * W, fill=255)])
    lit(c, cr, (150, 255, 180), lin((255, 255, 250), (160, 245, 180)), 14, 1.5)
    return K.finish(c)


def devotion():
    """Cupped hands offering up a glowing heart (one's own life given as another's MP)."""
    c = bg((50, 90, 220), (4, 8, 34), 0.5, 0.36)
    rays(c, 0.5, 0.36, 16, (200, 220, 255), 0.06, 0.8, 90, 8)
    orb = ell(0.31, 0.06, 0.69, 0.44)
    K.glow(c, orb, (110, 170, 255, 255), 34, 1.6)
    K.fill(c, K.soften(orb, 3), rad((236, 246, 255), (60, 120, 240), 0.5, 0.24, 0.24))

    def heart(d, cx, cy, r):
        d.ellipse(pts([(cx - r * 1.0, cy - r * 0.9), (cx + r * 0.05, cy + r * 0.15)]), fill=255)
        d.ellipse(pts([(cx - r * 0.05, cy - r * 0.9), (cx + r * 1.0, cy + r * 0.15)]), fill=255)
        d.polygon(pts([(cx - r * 0.96, cy - r * 0.2), (cx, cy + r * 1.05), (cx + r * 0.96, cy - r * 0.2)]), fill=255)
    hm_ = K.shape(lambda d: heart(d, 0.5, 0.26, 0.12))
    K.glow(c, hm_, (255, 90, 120, 255), 16, 1.6)
    K.shadow(c, hm_, 3, 5, 5, 120)
    K.fill(c, K.soften(hm_), rad((255, 200, 210), (210, 20, 60), 0.44, 0.20, 0.18))
    K.fill(c, K.soften(ell(0.41, 0.19, 0.46, 0.23), 3), (255, 255, 255, 200))

    def hand(d, sx, v=255):
        cx, cy = 0.5 + sx * 0.17, 0.80
        d.ellipse(pts([(cx - 0.14, cy - 0.12), (cx + 0.14, cy + 0.14)]), fill=v)            # palm
        for k in range(4):                                                                 # fingers, inner first
            fx = cx + sx * (-0.10 + 0.065 * k)
            top = 0.50 + 0.02 * abs(k - 1.3)
            brush(d, [(fx, cy - 0.04), (fx + sx * 0.02 * k, top)], 0.058, 0.052, v)
        brush(d, [(cx + sx * 0.12, cy + 0.02), (cx + sx * 0.24, cy - 0.12)], 0.06, 0.05, v)  # thumb
    hm = K.shape(lambda d: [hand(d, -1), hand(d, 1)])
    out = hm.filter(ImageFilter.MaxFilter(9))
    K.glow(c, out, (190, 214, 255, 255), 14, 1.4)
    K.fill(c, K.soften(out, 1.5), (50, 24, 20, 255))
    K.fill(c, K.soften(hm), lin((255, 238, 218), (226, 166, 126)))
    gaps = K.shape(lambda d: [brush(d, [(0.5 + sx * (0.17 - 0.10 + 0.065 * k + 0.0325) + sx * 0.0, 0.74),
                                        (0.5 + sx * (0.17 - 0.10 + 0.065 * k + 0.0325) + sx * 0.02 * k, 0.53)],
                                     0.010, 0.010) for sx in (-1, 1) for k in range(3)])
    K.fill(c, scale(K.soften(gaps), 0.8), (120, 64, 44, 255))
    motes(c, 13, 14, (0.20, 0.04, 0.80, 0.50), (0.007, 0.014), (230, 240, 255), (100, 160, 255))
    return K.finish(c)


def afflatus_solace():
    """A white dove with an olive sprig (solace: cures that also shield)."""
    c = bg((120, 204, 186), (8, 34, 32), 0.5, 0.45)
    rays(c, 0.5, 0.5, 14, (255, 255, 240), 0.05, 0.7, 70, 8)

    def dove(d):
        d.polygon(xf(GB.ell(0, 0, 0.21, 0.10), 0.50, 0.58, 1.0, -12), fill=255)
        d.ellipse(pts([(0.63, 0.38), (0.77, 0.52)]), fill=255)
        d.polygon(pts([(0.75, 0.43), (0.86, 0.46), (0.75, 0.49)]), fill=255)
        d.polygon(pts([(0.34, 0.60), (0.12, 0.56), (0.10, 0.66), (0.14, 0.72), (0.34, 0.66)]), fill=255)
        GA.leaf(d, 0.50, 0.54, math.radians(-118), 0.40, 0.085)
        GA.leaf(d, 0.56, 0.54, math.radians(-80), 0.36, 0.075)
    dv = K.shape(dove)
    K.glow(c, dv, (255, 255, 255, 255), 18, 1.5)
    K.shadow(c, dv, 4, 7, 7, 120)
    K.fill(c, K.soften(dv), lin((255, 255, 255), (210, 225, 230)))
    eye = ell(0.705, 0.435, 0.725, 0.455)
    K.fill(c, K.soften(eye, 0.8), (30, 30, 40, 255))
    sprig = K.shape(lambda d: [d.line(pts([(0.84, 0.47), (0.92, 0.56)]), fill=255, width=int(0.012 * W)),
                               GA.leaf(d, 0.86, 0.50, math.radians(10), 0.08, 0.025),
                               GA.leaf(d, 0.88, 0.53, math.radians(120), 0.08, 0.025)])
    K.fill(c, K.soften(sprig), (110, 200, 80, 255))
    return K.finish(c)


def afflatus_misery():
    """A crown of thorns, a pale tear of light falling within (power drawn from suffering)."""
    c = bg((110, 44, 130), (14, 4, 20), 0.5, 0.5)
    tear = K.shape(lambda d: GB.heart_drop(d, 0.5, 0.44, 0.10))
    K.glow(c, tear, (230, 200, 255, 255), 20, 1.5)
    K.fill(c, K.soften(tear), lin((255, 255, 255), (200, 170, 255)))

    def crown(d):
        for k in range(3):
            d.ellipse(pts([(0.16, 0.54 + k * 0.012), (0.84, 0.80 - k * 0.012)]), outline=255, width=int(0.028 * W))
        for i in range(16):
            a = 2 * math.pi * i / 16 + 0.15
            x, y = 0.5 + math.cos(a) * 0.34, 0.67 + math.sin(a) * 0.13
            ox, oy = math.cos(a + 0.6 * (1 if i % 2 else -1)), math.sin(a + 0.6 * (1 if i % 2 else -1))
            d.polygon(pts([(x - oy * 0.02, y + ox * 0.02), (x + ox * 0.10, y + oy * 0.07), (x + oy * 0.02,
                                                                                        y - ox * 0.02)]), fill=255)
    cr = K.shape(crown)
    K.glow(c, cr, (220, 150, 255, 255), 10, 1.3)
    K.shadow(c, cr, 4, 6, 6, 170)
    K.fill(c, K.soften(cr), lin((190, 130, 110), (90, 50, 40)))
    return K.finish(c)


# ---- BLM / RDM ------------------------------------------------------------------------------------------------------
def mana_wall():
    """A wall of hexagonal mana plates, brightest where it bears the blow."""
    c = bg((40, 64, 180), (4, 6, 30), 0.5, 0.5)
    r = 0.092
    cells = []
    for row in range(-3, 4):
        for colm in range(-3, 4):
            x = 0.5 + colm * r * 1.73 + (r * 0.865 if row % 2 else 0)
            y = 0.5 + row * r * 1.5
            if math.hypot(x - 0.5, y - 0.5) < 0.40:
                cells.append((x, y))
    for x, y in cells:
        dist = math.hypot(x - 0.5, y - 0.5)
        hexp = [(x + math.cos(math.radians(30 + 60 * i)) * r * 0.92, y + math.sin(math.radians(30 + 60 * i)) * r * 0.92)
                for i in range(6)]
        face = poly(hexp)
        K.fill(c, scale(K.soften(face), 0.55 - dist * 0.8), (120, 200, 255, 255))
        edge = K.shape(lambda d, hexp=hexp: d.polygon(pts(hexp), outline=255, width=int(0.016 * W)))
        K.glow(c, edge, (120, 210, 255, 255), 6, 0.9)
        K.fill(c, scale(K.soften(edge), max(0.3, 1 - dist * 1.6)), (220, 245, 255, 255))
    core = ell(0.40, 0.40, 0.60, 0.60)
    K.glow(c, core, (200, 240, 255, 255), 28, 1.4)
    sparkles(c, [(0.5, 0.5, 0.13)], (255, 255, 255), (170, 230, 255))
    return K.finish(c)


def composure():
    """The red mage's plumed hat, worn with calm assurance."""
    c = bg((70, 50, 130), (8, 6, 24), 0.5, 0.45)
    motes(c, 17, 12, (0.12, 0.1, 0.88, 0.5), (0.006, 0.012), (255, 240, 220), (220, 180, 255))
    feather = K.shape(lambda d: d.polygon(pts(GC.stroke(GA.bezier((0.58, 0.54), (0.84, 0.46), (0.76, 0.16), 24),
                                                         0.05, 0.10)), fill=255))
    tip = K.shape(lambda d: d.polygon(pts(GC.stroke(GA.bezier((0.76, 0.20), (0.74, 0.12), (0.66, 0.10), 10),
                                                     0.09, 0.01)), fill=255))
    fe = ImageChops.lighter(feather, tip)
    K.glow(c, fe, (255, 255, 255, 255), 12, 1.2)
    K.fill(c, K.soften(fe), lin((255, 255, 255), (220, 220, 240)))
    spine = K.shape(lambda d: d.line(pts(GA.bezier((0.60, 0.53), (0.82, 0.46), (0.74, 0.18), 20)), fill=255,
                                     width=int(0.008 * W)))
    K.fill(c, K.soften(spine), (180, 170, 200, 255))
    brim = ell(0.12, 0.56, 0.88, 0.76)
    crown_m = poly([(0.30, 0.66), (0.32, 0.42), (0.40, 0.31), (0.52, 0.29), (0.64, 0.34), (0.70, 0.44), (0.70, 0.66)])
    hat = ImageChops.lighter(brim, crown_m)
    K.glow(c, hat, (255, 120, 120, 255), 18, 1.2)
    K.shadow(c, hat, 5, 8, 8, 170)
    K.fill(c, K.soften(brim), lin((230, 60, 70), (120, 10, 24)))
    K.fill(c, K.soften(crown_m), lin((240, 80, 84), (150, 20, 34), 0))
    band = ImageChops.multiply(crown_m, poly([(0, 0.53), (1, 0.53), (1, 0.61), (0, 0.61)]))
    K.fill(c, K.soften(band), gold())
    gem = ell(0.47, 0.54, 0.53, 0.60)
    K.fill(c, K.soften(gem), (255, 255, 255, 255))
    return K.finish(c)


# ---- THF ------------------------------------------------------------------------------------------------------------
def hide():
    """An empty hood in the shadows, only two eyes showing."""
    c = bg((40, 96, 104), (4, 10, 14), 0.5, 0.4)
    hood = poly([(0.5, 0.10), (0.62, 0.16), (0.74, 0.30), (0.80, 0.48), (0.84, 0.70), (0.86, 0.96), (0.14, 0.96),
                 (0.16, 0.70), (0.20, 0.48), (0.26, 0.30), (0.38, 0.16)])
    hood_f = fade_down(hood, 0.55, 0.98)
    K.glow(c, hood_f, (150, 230, 230, 255), 10, 1.2)
    K.fill(c, K.soften(hood_f), lin((70, 96, 104), (20, 30, 36)))
    opening = ell(0.32, 0.32, 0.68, 0.78)
    K.fill(c, K.soften(fade_down(opening, 0.6, 0.9), 6), (2, 4, 6, 255))
    eyes = K.shape(lambda d: [GC.eye_shape(d, x, 0.52, 0.05, 0.02) for x in (0.42, 0.58)])
    K.glow(c, eyes, (255, 220, 80, 255), 10, 1.8)
    K.fill(c, K.soften(eyes), (255, 250, 200, 255))
    smoke = GD.motes
    smoke(c, 31, 16, (0.12, 0.78, 0.88, 0.98), (0.03, 0.06), (120, 160, 170), None, 50)
    return K.finish(c)


def mug():
    """A dagger stabbed through a gold coin."""
    c = bg((190, 70, 40), (30, 8, 4), 0.45, 0.55)
    coin = ell(0.22, 0.36, 0.70, 0.84)
    lit(c, coin, (255, 220, 120), gold(), 18, 1.3, sh=True)
    ring = K.shape(lambda d: d.ellipse(pts([(0.27, 0.41), (0.65, 0.79)]), outline=255, width=int(0.014 * W)))
    K.fill(c, K.soften(ring), (170, 100, 30, 255))
    mark = K.shape(lambda d: GD.star(d, 0.46, 0.60, 0.11, 0.05))
    emboss(c, mark, (255, 236, 150), (150, 90, 20))
    dag = K.shape(lambda d: GB.draw_dagger(d, 0.60, 0.42, 1.10, 220))
    K.glow(c, dag, (255, 200, 160, 255), 12, 1.2)
    K.shadow(c, dag, 5, 8, 8, 170)
    K.fill(c, K.soften(dag), steel())
    hilt = K.shape(lambda d: GB.draw_dagger(d, 0.60, 0.42, 1.10, 220, (1, 2, 3)))
    K.fill(c, K.soften(hilt), lin((200, 70, 50), (90, 20, 14)))
    b = burst(0.44, 0.62, 8, 0.10, 0.04, 0.3)
    K.fill(c, scale(K.soften(b, 3), 0.8), (255, 255, 230, 255))
    sparkles(c, [(0.20, 0.30, 0.06), (0.82, 0.76, 0.05)], (255, 255, 230), (255, 200, 120))
    return K.finish(c)


def accomplice():
    """A thief's hand-sign pulls the enemy's anger (a red flame) off an ally onto himself."""
    c = bg((84, 64, 180), (10, 6, 30), 0.5, 0.45)
    ally = K.shape(lambda d: GD.bust(d, 0.30, 0.66, 1.1))
    lit(c, ally, (200, 220, 255), lin((200, 214, 250), (110, 126, 180)), 10, 1.2)
    thief = K.shape(lambda d: [GD.bust(d, 0.72, 0.70, 1.2),
                               d.polygon(pts([(0.72, 0.30), (0.83, 0.42), (0.86, 0.62), (0.58, 0.62), (0.61, 0.42)]),
                                         fill=255)])
    K.glow(c, thief, (200, 180, 255, 255), 10, 1.5)
    K.fill(c, K.soften(thief), lin((50, 40, 80), (14, 10, 26)))
    arr = K.shape(lambda d: GA.arc_arrow(d, 0.51, 0.46, 0.22, 205, 320, 0.035))
    K.glow(c, arr, (255, 230, 200, 255), 8, 1.2)
    K.fill(c, K.soften(arr), (255, 246, 230, 255))
    fl = K.shape(lambda d: GA.flame(d, 0.30, 0.40, 0.07, 0.18, 0.02))
    K.glow(c, fl, (255, 60, 40, 255), 14, 1.6)
    K.fill(c, K.soften(fl), lin((255, 230, 140), (240, 40, 30), 270))
    return K.finish(c)


def assassins_charge():
    """Three daggers fanned out as one (the next attack strikes again and again)."""
    c = bg((170, 22, 44), (24, 2, 8), 0.5, 0.5)
    rays(c, 0.5, 0.80, 10, (255, 160, 160), 0.06, 0.8, 70, 8, -math.pi / 2)
    for ang in (-32, 32, 0):
        dag = K.shape(lambda d, ang=ang: GB.draw_dagger(d, 0.5 + math.sin(math.radians(ang)) * 0.26,
                                                        0.80 - math.cos(math.radians(ang)) * 0.26, 1.0, ang))
        K.glow(c, dag, (255, 120, 120, 255), 12, 1.2)
        K.shadow(c, dag, 4, 7, 7, 170)
        K.fill(c, K.soften(dag), steel())
        hilt = K.shape(lambda d, ang=ang: GB.draw_dagger(d, 0.5 + math.sin(math.radians(ang)) * 0.26,
                                                         0.80 - math.cos(math.radians(ang)) * 0.26, 1.0, ang,
                                                         (1, 2, 3)))
        K.fill(c, K.soften(hilt), lin((90, 20, 30), (30, 4, 10)))
    sparkles(c, [(0.5, 0.10, 0.08)], (255, 255, 255), (255, 140, 140))
    return K.finish(c)


def feint():
    """A masquerade mask, a dagger hidden behind it (a false move that leaves the foe open)."""
    c = bg((40, 140, 140), (4, 20, 22), 0.5, 0.45)
    dag = K.shape(lambda d: GB.draw_dagger(d, 0.52, 0.48, 1.15, 40))
    K.glow(c, dag, (180, 255, 240, 255), 10, 1.2)
    K.fill(c, K.soften(dag), steel())
    hilt = K.shape(lambda d: GB.draw_dagger(d, 0.52, 0.48, 1.15, 40, (1, 2, 3)))
    K.fill(c, K.soften(hilt), lin((90, 200, 180), (20, 70, 70)))
    mask_o = poly([(0.12, 0.40), (0.28, 0.34), (0.42, 0.37), (0.50, 0.42), (0.58, 0.37), (0.72, 0.34), (0.88, 0.40),
                   (0.86, 0.54), (0.74, 0.64), (0.58, 0.61), (0.50, 0.55), (0.42, 0.61), (0.26, 0.64), (0.14, 0.54)])
    holes = K.shape(lambda d: [GC.eye_shape(d, x, 0.49, 0.085, 0.042) for x in (0.32, 0.68)])
    mk = ImageChops.subtract(mask_o, holes)
    K.glow(c, mk, (200, 255, 245, 255), 14, 1.2)
    K.shadow(c, mk, 5, 8, 8, 170)
    K.fill(c, K.soften(mk), lin((255, 250, 240), (200, 190, 220)))
    trim = K.shape(lambda d: d.line(pts([(0.12, 0.40), (0.28, 0.34), (0.42, 0.37), (0.50, 0.42), (0.58, 0.37),
                                         (0.72, 0.34), (0.88, 0.40)]), fill=255, width=int(0.02 * W)))
    K.fill(c, K.soften(trim), gold())
    gem = ell(0.475, 0.425, 0.525, 0.475)
    K.fill(c, K.soften(gem), (80, 230, 200, 255))
    return K.finish(c)


def collaborator():
    """Two daggers crossed as partners, the enemy's anger caught where they meet."""
    c = bg((60, 140, 80), (6, 22, 10), 0.5, 0.45)
    for ang, cx in ((-35, 0.40), (35, 0.60)):
        dag = K.shape(lambda d, ang=ang, cx=cx: GB.draw_dagger(d, cx, 0.52, 1.15, ang))
        K.glow(c, dag, (200, 255, 210, 255), 10, 1.2)
        K.shadow(c, dag, 4, 7, 7, 170)
        K.fill(c, K.soften(dag), steel())
        hilt = K.shape(lambda d, ang=ang, cx=cx: GB.draw_dagger(d, cx, 0.52, 1.15, ang, (1, 2, 3)))
        K.fill(c, K.soften(hilt), lin((120, 210, 120), (30, 80, 30)))
    fl = K.shape(lambda d: GA.flame(d, 0.5, 0.44, 0.08, 0.22, 0.0))
    K.glow(c, fl, (255, 60, 40, 255), 16, 1.7)
    K.fill(c, K.soften(fl), lin((255, 236, 150), (240, 40, 30), 270))
    return K.finish(c)


def despoil():
    """A dagger tip prying a jewel loose, a curse left behind as it goes."""
    c = bg((130, 54, 120), (16, 4, 16), 0.5, 0.42)
    motes(c, 41, 16, (0.2, 0.6, 0.8, 0.95), (0.01, 0.022), (200, 120, 255), (150, 60, 200), 160)
    crown_ = poly([(0.30, 0.40), (0.40, 0.28), (0.60, 0.28), (0.70, 0.40)])
    pav = poly([(0.30, 0.40), (0.70, 0.40), (0.50, 0.70)])
    gem = ImageChops.lighter(crown_, pav)
    K.glow(c, gem, (120, 255, 170, 255), 22, 1.5)
    K.shadow(c, gem, 4, 8, 8, 150)
    K.fill(c, K.soften(crown_), lin((210, 255, 220), (80, 220, 130)))
    K.fill(c, K.soften(pav), lin((60, 200, 110), (10, 90, 50)))
    facets = K.shape(lambda d: [d.line(pts(s), fill=255, width=int(0.008 * W)) for s in
                                ([(0.30, 0.40), (0.70, 0.40)], [(0.44, 0.28), (0.40, 0.40), (0.50, 0.70)],
                                 [(0.56, 0.28), (0.60, 0.40), (0.50, 0.70)])])
    K.fill(c, scale(K.soften(facets), 0.7), (230, 255, 240, 255))
    dag = K.shape(lambda d: GB.draw_dagger(d, 0.32, 0.78, 0.9, 40))
    K.shadow(c, dag, 4, 7, 7, 170)
    K.fill(c, K.soften(dag), steel())
    hilt = K.shape(lambda d: GB.draw_dagger(d, 0.32, 0.78, 0.9, 40, (1, 2, 3)))
    K.fill(c, K.soften(hilt), lin((170, 90, 200), (60, 20, 80)))
    sparkles(c, [(0.62, 0.30, 0.07)], (255, 255, 255), (180, 255, 200))
    return K.finish(c)


# ---- PLD ------------------------------------------------------------------------------------------------------------
def holy_circle():
    """A ring of holy light on the ground, a column of it rising, a cross hovering within."""
    c = bg((54, 76, 176), (6, 8, 30), 0.5, 0.6)
    col_m = poly([(0.24, 0.76), (0.76, 0.76), (0.70, 0.0), (0.30, 0.0)])
    col_m = ImageChops.multiply(col_m, fade_down(K.shape(lambda d: d.rectangle(pts([(0, 0), (1, 1)]), fill=255)),
                                                 0.0, 1.0).transpose(Image.FLIP_TOP_BOTTOM))
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(14)), 0.6), (255, 245, 200, 255))
    ring = K.shape(lambda d: [d.ellipse(pts([(0.12, 0.64), (0.88, 0.88)]), outline=255, width=int(0.028 * W)),
                              d.ellipse(pts([(0.22, 0.68), (0.78, 0.84)]), outline=255, width=int(0.012 * W))])
    K.glow(c, ring, (255, 230, 140, 255), 14, 1.6)
    K.fill(c, K.soften(ring), (255, 240, 180, 255))
    cr = K.shape(lambda d: [d.rounded_rectangle(pts([(0.455, 0.16), (0.545, 0.62)]), radius=0.02 * W, fill=255),
                            d.rounded_rectangle(pts([(0.33, 0.28), (0.67, 0.37)]), radius=0.02 * W, fill=255)])
    K.glow(c, cr, (255, 240, 180, 255), 20, 1.6)
    K.fill(c, K.soften(cr), lin((255, 255, 240), (240, 196, 90)))
    motes(c, 7, 14, (0.25, 0.1, 0.75, 0.75), (0.006, 0.012), (255, 255, 230), (255, 230, 150))
    return K.finish(c)


def rampart():
    """A castle battlement, the party's shield emblazoned on it."""
    c = bg((200, 130, 80), (30, 14, 24), 0.5, 0.35)

    def wall(d):
        d.rectangle(pts([(0.16, 0.44), (0.84, 0.88)]), fill=255)
        for x in (0.16, 0.30, 0.44, 0.58, 0.72):
            d.rectangle(pts([(x, 0.30), (x + 0.12, 0.45)]), fill=255)
    w = K.shape(wall)
    K.glow(c, w, (255, 220, 170, 255), 14, 1.0)
    K.shadow(c, w, 5, 8, 8, 180)
    K.fill(c, K.soften(w), lin((200, 196, 196), (100, 96, 110)))
    joints = K.shape(lambda d: [d.line(pts([(0.16, y), (0.84, y)]), fill=255, width=int(0.008 * W))
                                for y in (0.55, 0.66, 0.77)] +
                     [d.line(pts([(x + (0.07 if k % 2 else 0), y0), (x + (0.07 if k % 2 else 0), y0 + 0.11)]), fill=255,
                             width=int(0.008 * W)) for k, y0 in enumerate((0.44, 0.55, 0.66, 0.77))
                      for x in (0.23, 0.37, 0.51, 0.65, 0.79)])
    K.fill(c, scale(K.soften(joints), 0.45), (40, 30, 40, 255))
    sh = poly(GD.shield_pts(0.5, 0.48, 0.15, 0.34))
    K.glow(c, sh, (255, 230, 150, 255), 14, 1.3)
    K.shadow(c, sh, 4, 6, 6, 160)
    K.fill(c, K.soften(sh), gold())
    inner = poly(GD.shield_pts(0.5, 0.505, 0.12, 0.29))
    K.fill(c, K.soften(inner), lin((70, 110, 210), (24, 40, 110)))
    cr = K.shape(lambda d: [d.rectangle(pts([(0.485, 0.53), (0.515, 0.76)]), fill=255),
                            d.rectangle(pts([(0.43, 0.58), (0.57, 0.61)]), fill=255)])
    K.fill(c, K.soften(cr), (255, 236, 160, 255))
    return K.finish(c)


def fealty():
    """A sword planted point-down in an oath, a halo of resolve behind its hilt."""
    c = bg((116, 74, 190), (14, 8, 30), 0.5, 0.35)
    halo = K.shape(lambda d: d.ellipse(pts([(0.26, 0.08), (0.74, 0.56)]), outline=255, width=int(0.03 * W)))
    K.glow(c, halo, (255, 230, 160, 255), 14, 1.5)
    K.fill(c, K.soften(halo), (255, 236, 170, 255))
    rays(c, 0.5, 0.32, 16, (255, 240, 200), 0.05, 0.6, 80, 8)
    sw = K.shape(lambda d: GA.sword(d, 0.5, 0.14, 0.5, 0.90, 0.055, 0.17, 0.16))
    K.glow(c, sw, (230, 210, 255, 255), 16, 1.3)
    K.shadow(c, sw, 5, 8, 8, 170)
    K.fill(c, K.soften(sw), steel())
    hilt = K.shape(lambda d: [d.rectangle(pts([(0.33, 0.28), (0.67, 0.32)]), fill=255),
                              d.rectangle(pts([(0.475, 0.14), (0.525, 0.30)]), fill=255),
                              d.ellipse(pts([(0.45, 0.09), (0.55, 0.19)]), fill=255)])
    K.fill(c, K.soften(hilt), gold())
    ground = K.shape(lambda d: d.ellipse(pts([(0.26, 0.84), (0.74, 0.96)]), fill=255))
    K.fill(c, scale(K.soften(ground, 8), 0.7), (40, 20, 70, 255))
    sparkles(c, [(0.5, 0.30, 0.07)], (255, 255, 255), (255, 230, 160))
    return K.finish(c)


def chivalry():
    """A knight's great helm, its blue plume and mana rising from the fight."""
    c = bg((60, 120, 90), (6, 18, 12), 0.5, 0.45)
    motes(c, 23, 18, (0.15, 0.05, 0.85, 0.5), (0.008, 0.016), (220, 245, 255), (90, 170, 255))
    plume = K.shape(lambda d: d.polygon(pts(GC.stroke(GA.bezier((0.50, 0.28), (0.60, 0.04), (0.86, 0.12), 20),
                                                       0.16, 0.03)), fill=255))
    lit(c, plume, (200, 230, 255), lin((150, 200, 255), (40, 80, 230)), 12, 1.6, sh=True)
    helm = ImageChops.lighter(ell(0.30, 0.20, 0.70, 0.50),
                              K.shape(lambda d: d.rounded_rectangle(pts([(0.30, 0.34), (0.70, 0.86)]),
                                                                    radius=0.05 * W, fill=255)))
    lit(c, helm, (170, 230, 255), lin((250, 250, 255), (110, 120, 150), 0), 18, 1.2, sh=True)
    slit = K.shape(lambda d: [d.rectangle(pts([(0.33, 0.45), (0.47, 0.50)]), fill=255),
                              d.rectangle(pts([(0.53, 0.45), (0.67, 0.50)]), fill=255)])
    K.fill(c, K.soften(slit), (10, 14, 20, 255))
    ridge = K.shape(lambda d: d.rectangle(pts([(0.485, 0.22), (0.515, 0.86)]), fill=255))
    K.fill(c, K.soften(ridge), gold())
    holes = K.shape(lambda d: [d.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
                               for x in (0.58, 0.63) for y in (0.60, 0.67, 0.74)])
    K.fill(c, K.soften(holes), (20, 24, 34, 255))
    return K.finish(c)


def divine_emblem():
    """A gold emblem of the cross within a laurel wreath."""
    c = bg((176, 44, 54), (24, 4, 8), 0.5, 0.45)
    rays(c, 0.5, 0.5, 16, (255, 220, 170), 0.05, 0.7, 80, 8)

    def wreath(d):
        for side in (-1, 1):
            for i in range(7):
                a = math.radians(90 + side * (35 + i * 20))
                x, y = 0.5 + math.cos(a) * 0.34, 0.5 + math.sin(a) * 0.34
                tang = a + side * math.pi / 2 + side * 0.5 + math.pi
                GA.leaf(d, x, y, tang, 0.12, 0.035)
    wr = K.shape(wreath)
    K.glow(c, wr, (200, 255, 160, 255), 8, 1.0)
    K.fill(c, K.soften(wr), lin((190, 240, 130), (60, 140, 40)))
    med = ell(0.27, 0.27, 0.73, 0.73)
    lit(c, med, (255, 220, 120), gold(), 20, 1.4, sh=True)
    inner = ell(0.32, 0.32, 0.68, 0.68)
    K.fill(c, K.soften(inner), rad((255, 250, 220), (230, 170, 60), 0.45, 0.42, 0.3))
    cr = K.shape(lambda d: [d.polygon(pts([(0.5, 0.33), (0.535, 0.47), (0.5, 0.67), (0.465, 0.47)]), fill=255),
                            d.polygon(pts([(0.35, 0.47), (0.5, 0.44), (0.65, 0.47), (0.5, 0.50)]), fill=255)])
    emboss(c, cr, (255, 255, 255), (150, 90, 20))
    return K.finish(c)


# ---- DRK ------------------------------------------------------------------------------------------------------------
def weapon_bash():
    """A great sword's pommel slammed into the foe, leaving it seeing stars."""
    c = bg((140, 44, 32), (20, 4, 4), 0.35, 0.65)
    b = burst(0.28, 0.72, 10, 0.24, 0.10, 0.2)
    lit(c, b, (255, 200, 120), rad((255, 255, 220), (255, 140, 40), 0.28, 0.72, 0.24), 14, 1.3)
    sw = K.shape(lambda d: GA.sword(d, 0.34, 0.66, 0.88, 0.10, 0.06, 0.15, 0.17))
    K.glow(c, sw, (255, 130, 110, 255), 14, 1.2)
    K.shadow(c, sw, 5, 8, 8, 170)
    K.fill(c, K.soften(sw), lin((210, 204, 220), (80, 70, 90)))
    hilt = K.shape(lambda d: [d.ellipse(pts([(0.29, 0.61), (0.39, 0.71)]), fill=255),
                              d.polygon(pts(GC.stroke([(0.34, 0.66), (0.455, 0.545)], 0.04)), fill=255)])
    K.fill(c, K.soften(hilt), lin((150, 40, 40), (60, 10, 10)))
    stun_stars(c, 0.34, 0.30, 0.20, 0.07)
    return K.finish(c)


def diabolic_eye():
    """A demon's slit-pupilled eye opening in the dark."""
    c = bg((130, 10, 44), (16, 0, 6), 0.5, 0.5)
    spikes = burst(0.5, 0.52, 16, 0.46, 0.24, 0.1)
    K.fill(c, scale(K.soften(spikes, 6), 0.55), (40, 0, 14, 255))
    eye = K.shape(lambda d: GC.eye_shape(d, 0.5, 0.52, 0.38, 0.19))
    K.glow(c, eye, (255, 40, 60, 255), 26, 1.6)
    K.fill(c, K.soften(eye), rad((255, 210, 120), (200, 40, 20), 0.5, 0.52, 0.36))
    iris = ell(0.37, 0.39, 0.63, 0.65)
    K.fill(c, K.soften(iris), rad((255, 240, 120), (220, 80, 10), 0.5, 0.5, 0.15))
    pupil = poly([(0.5, 0.38), (0.53, 0.52), (0.5, 0.66), (0.47, 0.52)])
    K.fill(c, K.soften(pupil), (10, 0, 4, 255))
    lid = K.shape(lambda d: [d.line(pts([(0.10, 0.52), (0.30, 0.37), (0.5, 0.33), (0.70, 0.37), (0.90, 0.52)]),
                                    fill=255, width=int(0.02 * W))])
    K.fill(c, K.soften(lid), (30, 0, 8, 255))
    hi = ell(0.53, 0.42, 0.57, 0.46)
    K.fill(c, K.soften(hi), (255, 255, 255, 230))
    return K.finish(c)


def nether_void():
    """A black void with a violet corona, dark power spiralling into it."""
    c = bg((96, 36, 140), (4, 0, 10), 0.5, 0.5)
    sp = K.shape(lambda d: [brush(d, [(0.5 + math.cos(a0 + t * 3.2) * (0.46 - t * 0.26),
                                       0.5 + math.sin(a0 + t * 3.2) * (0.46 - t * 0.26)) for t in
                                      [i / 30 for i in range(31)]], 0.012, 0.04)
                            for a0 in (0.0, 2.1, 4.2)])
    K.glow(c, sp, (200, 120, 255, 255), 8, 1.2)
    K.fill(c, scale(K.soften(sp, 2), 0.85), (230, 190, 255, 255))
    void = ell(0.31, 0.31, 0.69, 0.69)
    K.glow(c, void, (200, 110, 255, 255), 30, 2.6)
    K.glow(c, void, (255, 230, 255, 255), 8, 1.4)
    K.fill(c, K.soften(void, 2), rad((0, 0, 0), (24, 6, 34), 0.5, 0.5, 0.19))
    disc = K.shape(lambda d: d.ellipse(pts([(0.12, 0.44), (0.88, 0.56)]), outline=255, width=int(0.016 * W)))
    disc = rot(disc, 20)
    front = ImageChops.multiply(disc, poly([(0, 0.5), (1, 0.5), (1, 1), (0, 1)]))
    K.fill(c, K.soften(front), (240, 200, 255, 255))
    return K.finish(c)


# ---- BST ------------------------------------------------------------------------------------------------------------
def gauge():
    """A magnifying glass over a paw print (can this beast be charmed?)."""
    c = bg((40, 136, 130), (4, 18, 20), 0.45, 0.45)
    handle = K.shape(lambda d: d.polygon(pts(GC.stroke([(0.60, 0.60), (0.84, 0.86)], 0.075)), fill=255))
    lit(c, handle, None, lin((160, 90, 50), (70, 34, 16)), sh=True)
    lens = ell(0.18, 0.18, 0.66, 0.66)
    K.glow(c, lens, (190, 255, 240, 255), 18, 1.2)
    K.fill(c, K.soften(lens), rad((210, 250, 245), (110, 190, 190), 0.36, 0.34, 0.3))
    pw = K.shape(lambda d: GB.paw(d, 0.42, 0.44, 0.62))
    K.fill(c, K.soften(pw), lin((140, 80, 50), (80, 40, 20)))
    rim = K.shape(lambda d: d.ellipse(pts([(0.18, 0.18), (0.66, 0.66)]), outline=255, width=int(0.04 * W)))
    K.shadow(c, rim, 4, 6, 6, 150)
    K.fill(c, K.soften(rim), gold())
    glint = K.shape(lambda d: d.arc(pts([(0.25, 0.25), (0.59, 0.59)]), 200, 250, fill=255, width=int(0.02 * W)))
    K.fill(c, K.soften(glint, 2), (255, 255, 255, 220))
    return K.finish(c)


def tame():
    """A leather collar with a paw-stamped tag (the beast calmed and held)."""
    c = bg((124, 176, 90), (14, 26, 8), 0.5, 0.45)
    back = K.shape(lambda d: d.arc(pts([(0.14, 0.30), (0.86, 0.66)]), 180, 360, fill=255, width=int(0.08 * W)))
    K.fill(c, K.soften(back), lin((120, 70, 40), (60, 30, 14)))
    front = K.shape(lambda d: d.arc(pts([(0.14, 0.30), (0.86, 0.66)]), 0, 180, fill=255, width=int(0.08 * W)))
    K.shadow(c, front, 4, 7, 7, 170)
    K.fill(c, K.soften(front), lin((200, 130, 80), (120, 64, 30)))
    studs = K.shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.33 - 0.016, 0.48 + math.sin(a) * 0.16 - 0.016),
                                              (0.5 + math.cos(a) * 0.33 + 0.016, 0.48 + math.sin(a) * 0.16 + 0.016)]),
                                         fill=255) for a in [math.radians(x) for x in (20, 50, 130, 160)]])
    K.fill(c, K.soften(studs), (255, 236, 180, 255))
    ringm = K.shape(lambda d: d.ellipse(pts([(0.46, 0.62), (0.54, 0.70)]), outline=255, width=int(0.014 * W)))
    K.fill(c, K.soften(ringm), (230, 200, 120, 255))
    tag = ell(0.37, 0.67, 0.63, 0.93)
    lit(c, tag, (255, 236, 150), gold(), 14, 1.3, sh=True)
    pw = K.shape(lambda d: GB.paw(d, 0.5, 0.81, 0.36))
    emboss(c, pw, (255, 245, 200), (150, 90, 20), 2, 3)
    sparkles(c, [(0.76, 0.22, 0.07)], (255, 255, 255), (230, 255, 200))
    return K.finish(c)


def feral_howl():
    """A wolf howling against a full moon (the howl that terrorises)."""
    c = bg((60, 66, 150), (6, 6, 22), 0.6, 0.35)
    moon = ell(0.36, 0.12, 0.88, 0.64)
    K.glow(c, moon, (255, 250, 210, 255), 30, 1.3)
    K.fill(c, K.soften(moon), rad((255, 255, 240), (230, 220, 170), 0.58, 0.32, 0.3))
    wolf = poly([(0.82, 0.15), (0.64, 0.26), (0.57, 0.27), (0.52, 0.22), (0.45, 0.08), (0.41, 0.30),
                 (0.35, 0.38), (0.33, 0.44), (0.27, 0.48), (0.31, 0.53), (0.24, 0.62), (0.28, 0.66), (0.20, 0.80),
                 (0.17, 1.0), (0.66, 1.0), (0.63, 0.80), (0.61, 0.62), (0.64, 0.48), (0.70, 0.40), (0.77, 0.31),
                 (0.68, 0.315), (0.80, 0.21)])
    K.glow(c, wolf, (210, 220, 255, 255), 8, 1.8)
    K.fill(c, K.soften(wolf), lin((44, 48, 80), (10, 10, 20)))
    eye = K.shape(lambda d: GC.eye_shape(d, 0.56, 0.31, 0.025, 0.008))
    K.fill(c, K.soften(eye, 0.8), (255, 230, 140, 255))
    sound = K.shape(lambda d: [d.arc(pts([(0.82 - r, 0.17 - r), (0.82 + r, 0.17 + r)]), 280, 350, fill=255,
                                     width=int(0.018 * W)) for r in (0.06, 0.12)])
    K.fill(c, K.soften(sound), (70, 60, 110, 255))
    sparkles(c, [(0.18, 0.24, 0.05), (0.26, 0.12, 0.03)], (255, 255, 255), (200, 210, 255))
    return K.finish(c)


def killer_instinct():
    """Three raking claw marks, red-hot (the pack's killing instinct shared)."""
    c = bg((190, 70, 24), (26, 6, 2), 0.5, 0.5)
    rays(c, 0.5, 0.5, 12, (255, 200, 140), 0.05, 0.7, 60, 8)
    claws = K.shape(lambda d: [d.polygon(pts(_taper(GA.bezier((0.26 + k * 0.17, 0.12), (0.31 + k * 0.17, 0.48),
                                                              (0.18 + k * 0.17, 0.88), 30), 0.075)), fill=255)
                               for k in range(3)])
    K.glow(c, claws, (255, 60, 20, 255), 18, 1.6)
    K.shadow(c, claws, 4, 6, 6, 180)
    K.fill(c, K.soften(claws), (40, 4, 2, 255))
    inner = K.shape(lambda d: [d.polygon(pts(_taper(GA.bezier((0.26 + k * 0.17, 0.12), (0.31 + k * 0.17, 0.48),
                                                              (0.18 + k * 0.17, 0.88), 30), 0.035)), fill=255)
                               for k in range(3)])
    K.fill(c, K.soften(inner), lin((255, 250, 200), (255, 120, 40)))
    return K.finish(c)


def _taper(curve, wmax):
    """A stroke that is thin at both ends and wmax wide in the middle."""
    n = len(curve)
    left, right = [], []
    for i, (x, y) in enumerate(curve):
        a = curve[max(0, i - 1)]
        b = curve[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = wmax * math.sin(math.pi * i / (n - 1)) ** 0.7 / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


# ---- BRD ------------------------------------------------------------------------------------------------------------
def nightingale():
    """A nightingale singing on a branch, notes rising (songs come faster)."""
    c = bg((40, 116, 150), (4, 14, 26), 0.5, 0.45)
    branch = K.shape(lambda d: brush(d, [(0.04, 0.80), (0.40, 0.76), (0.70, 0.82), (0.96, 0.78)], 0.045, 0.02))
    K.fill(c, K.soften(branch), lin((140, 90, 60), (70, 40, 20)))

    def bird(d):
        d.polygon(xf(GB.ell(0, 0, 0.19, 0.11), 0.40, 0.60, 1.0, -25), fill=255)
        d.ellipse(pts([(0.48, 0.36), (0.64, 0.52)]), fill=255)
        d.polygon(pts([(0.62, 0.41), (0.74, 0.36), (0.63, 0.44)]), fill=255)
        d.polygon(pts([(0.62, 0.46), (0.73, 0.48), (0.62, 0.48)]), fill=255)
        d.polygon(pts([(0.26, 0.64), (0.08, 0.78), (0.14, 0.82), (0.30, 0.70)]), fill=255)
        d.polygon(pts([(0.38, 0.70), (0.40, 0.78), (0.42, 0.70)]), fill=255)
    b = K.shape(bird)
    K.glow(c, b, (255, 230, 170, 255), 14, 1.3)
    K.shadow(c, b, 4, 7, 7, 150)
    K.fill(c, K.soften(b), lin((230, 180, 120), (140, 90, 50)))
    wing = K.shape(lambda d: GA.leaf(d, 0.48, 0.56, math.radians(158), 0.26, 0.06))
    K.fill(c, K.soften(wing), lin((170, 110, 60), (100, 60, 30)))
    eye = ell(0.555, 0.415, 0.575, 0.435)
    K.fill(c, K.soften(eye, 0.8), (20, 10, 6, 255))
    nt = K.shape(lambda d: [GB.note(d, 0.76, 0.36, 0.34), GB.note(d, 0.86, 0.20, 0.24)])
    K.glow(c, nt, (220, 245, 255, 255), 8, 1.4)
    K.fill(c, K.soften(nt), (255, 255, 255, 255))
    return K.finish(c)


def troubadour():
    """A troubadour's lute (songs that last longer)."""
    c = bg((180, 116, 40), (28, 14, 4), 0.5, 0.45)
    rays(c, 0.5, 0.5, 14, (255, 236, 190), 0.05, 0.7, 70, 8)

    def lute(d):
        d.ellipse(pts([(0.30, 0.46), (0.70, 0.90)]), fill=255)
        d.polygon(pts([(0.36, 0.56), (0.46, 0.34), (0.54, 0.34), (0.64, 0.56)]), fill=255)
        d.rectangle(pts([(0.47, 0.12), (0.53, 0.40)]), fill=255)
        d.polygon(pts([(0.46, 0.13), (0.54, 0.13), (0.62, 0.04), (0.57, 0.02), (0.47, 0.10)]), fill=255)
    m = rot(K.shape(lute), 30, 0.5, 0.55)
    K.glow(c, m, (255, 220, 150, 255), 16, 1.2)
    K.shadow(c, m, 5, 8, 8, 170)
    K.fill(c, K.soften(m), lin((230, 160, 90), (130, 66, 24), 0))
    neck = rot(K.shape(lambda d: [d.rectangle(pts([(0.47, 0.12), (0.53, 0.42)]), fill=255),
                                  d.polygon(pts([(0.46, 0.13), (0.54, 0.13), (0.62, 0.04), (0.57, 0.02),
                                                 (0.47, 0.10)]), fill=255)]), 30, 0.5, 0.55)
    K.fill(c, K.soften(neck), lin((90, 50, 30), (40, 20, 10)))
    hole = rot(K.shape(lambda d: d.ellipse(pts([(0.44, 0.58), (0.56, 0.70)]), fill=255)), 30, 0.5, 0.55)
    K.fill(c, K.soften(hole), (30, 14, 6, 255))
    rose = rot(K.shape(lambda d: d.ellipse(pts([(0.425, 0.565), (0.575, 0.715)]), outline=255,
                                           width=int(0.01 * W))), 30, 0.5, 0.55)
    K.fill(c, K.soften(rose), (255, 220, 140, 255))
    strings = rot(K.shape(lambda d: [d.line(pts([(x, 0.13), (x, 0.82)]), fill=255, width=int(0.005 * W))
                                     for x in (0.485, 0.50, 0.515)]), 30, 0.5, 0.55)
    K.fill(c, K.soften(strings, 0.8), (255, 250, 230, 230))
    bridge = rot(K.shape(lambda d: d.rectangle(pts([(0.44, 0.80), (0.56, 0.83)]), fill=255)), 30, 0.5, 0.55)
    K.fill(c, K.soften(bridge), (60, 30, 14, 255))
    return K.finish(c)


def pianissimo():
    """A single hushed note in a narrow beam of light (a song for one)."""
    c = bg((140, 130, 210), (14, 12, 34), 0.5, 0.4)
    beam = poly([(0.44, -0.05), (0.56, -0.05), (0.74, 0.86), (0.26, 0.86)])
    K.fill(c, scale(fade_down(beam, 0.2, 1.0).filter(ImageFilter.GaussianBlur(12)), 0.6), (255, 250, 230, 255))
    pool = ell(0.24, 0.78, 0.76, 0.92)
    K.fill(c, scale(K.soften(pool, 10), 0.7), (255, 250, 230, 255))
    nt = K.shape(lambda d: GB.note(d, 0.44, 0.70, 0.78, 1))
    K.glow(c, nt, (255, 250, 230, 255), 16, 1.3)
    K.fill(c, K.soften(nt), lin((255, 255, 255), (220, 210, 250)))
    motes(c, 3, 10, (0.30, 0.1, 0.70, 0.8), (0.004, 0.009), (255, 255, 255), None, 180)
    return K.finish(c)


# ---- RNG ------------------------------------------------------------------------------------------------------------
def shadowbind():
    """An arrow driven into the foe's shadow, pinning it in place."""
    c = bg((100, 70, 150), (10, 6, 22), 0.5, 0.35)
    fig = K.shape(lambda d: K.figure(d, 0.5, 0.5, 1.15))
    flat = fig.resize((W, int(W * 0.36)), Image.LANCZOS)
    sh = K.mask()
    sh.paste(flat, (0, int(W * 0.55)))
    K.glow(c, sh, (200, 140, 255, 255), 12, 2.2)
    K.fill(c, K.soften(sh, 3), (8, 0, 14, 255))
    rip = K.shape(lambda d: [d.ellipse(pts([(0.5 - r, 0.74 - r * 0.3), (0.5 + r, 0.74 + r * 0.3)]), outline=255,
                                       width=int(0.012 * W)) for r in (0.10, 0.18)])
    K.glow(c, rip, (200, 150, 255, 255), 6, 1.2)
    K.fill(c, K.soften(rip), (230, 200, 255, 255))
    ar = K.shape(lambda d: GC.arrow(d, 0.72, 0.06, 0.50, 0.76))
    K.glow(c, ar, (230, 210, 255, 255), 10, 1.3)
    K.shadow(c, ar, 4, 6, 6, 150)
    K.fill(c, K.soften(ar), lin((255, 255, 255), (180, 170, 210)))
    return K.finish(c)


def camouflage():
    """Eyes peering out from a thicket of leaves."""
    c = bg((70, 130, 56), (6, 18, 4), 0.5, 0.5)
    dark = ell(0.28, 0.32, 0.72, 0.70)
    K.fill(c, K.soften(dark, 14), (4, 10, 2, 255))
    eyes = K.shape(lambda d: [GC.eye_shape(d, x, 0.50, 0.06, 0.024) for x in (0.42, 0.58)])
    K.glow(c, eyes, (255, 240, 140, 255), 8, 1.6)
    K.fill(c, K.soften(eyes), (255, 250, 210, 255))
    rnd = random.Random(12)
    shades = [((150, 210, 90), (60, 120, 30)), ((110, 180, 70), (40, 90, 20)), ((180, 220, 110), (80, 140, 40))]
    for i in range(22):
        a = 2 * math.pi * i / 22 + rnd.uniform(-0.1, 0.1)
        rr = rnd.uniform(0.30, 0.50)
        bx, by = 0.5 + math.cos(a) * rr, 0.5 + math.sin(a) * rr
        ang = a + math.pi + rnd.uniform(-0.6, 0.6)
        Lf = rnd.uniform(0.18, 0.28)
        lf = K.shape(lambda d, bx=bx, by=by, ang=ang, Lf=Lf: GA.leaf(d, bx, by, ang, Lf, Lf * 0.32))
        K.shadow(c, lf, 3, 5, 5, 140)
        top, bot = shades[i % 3]
        K.fill(c, K.soften(lf), lin(top, bot))
        vein = K.shape(lambda d, bx=bx, by=by, ang=ang, Lf=Lf: d.line(
            pts([(bx, by), (bx + math.cos(ang) * Lf * 0.9, by + math.sin(ang) * Lf * 0.9)]), fill=255,
            width=int(0.006 * W)))
        K.fill(c, scale(K.soften(vein), 0.5), (30, 70, 10, 255))
    return K.finish(c)


def _arrow_paint(c, m, glowc, top=(255, 255, 255), bot=(170, 180, 200)):
    K.glow(c, m, col(glowc), 10, 1.3)
    K.shadow(c, m, 4, 7, 6, 150)
    K.fill(c, K.soften(m), lin(top, bot))


def unlimited_shot():
    """An arrow flying through an infinity sign (no ammunition spent)."""
    c = bg((200, 116, 34), (30, 12, 2), 0.5, 0.5)
    inf = [(0.5 + 0.34 * math.cos(t) / (1 + math.sin(t) ** 2), 0.52 + 0.34 * math.sin(t) * math.cos(t) /
            (1 + math.sin(t) ** 2)) for t in [2 * math.pi * i / 120 for i in range(121)]]
    m = K.shape(lambda d: brush(d, inf, 0.065))
    K.glow(c, m, (255, 220, 120, 255), 18, 1.5)
    K.shadow(c, m, 4, 7, 6, 150)
    K.fill(c, K.soften(m), gold())
    hi = K.shape(lambda d: brush(d, [(x, y - 0.012) for x, y in inf], 0.018))
    K.fill(c, scale(K.soften(hi, 2), 0.5), (255, 255, 230, 255))
    ar = K.shape(lambda d: GC.arrow(d, 0.06, 0.70, 0.92, 0.32))
    _arrow_paint(c, ar, (255, 240, 200))
    return K.finish(c)


def stealth_shot():
    """An arrow slipping out of a pall of black smoke (shot from hiding: enmity kept low)."""
    c = bg((120, 150, 210), (8, 10, 24), 0.70, 0.30, 0.80)
    ar = K.shape(lambda d: GC.arrow(d, 0.06, 0.94, 0.86, 0.16, w=0.062, hl=0.26, hw=0.13, fl=0.18, fw=0.10))
    K.glow(c, ar, (160, 220, 255, 255), 16, 1.5)
    K.shadow(c, ar, 4, 7, 6, 150)
    K.fill(c, K.soften(ar), lin((255, 255, 255), (160, 176, 210), 45))
    edge = K.shape(lambda d: d.line(pts([(0.70, 0.30), (0.86, 0.16)]), fill=255, width=int(0.012 * W)))
    K.fill(c, scale(K.soften(edge), 0.8), (255, 255, 255, 255))
    # the smoke the archer hides in swallows the back half of the arrow
    rnd = random.Random(5)
    sm = K.mask()
    sd = ImageDraw.Draw(sm)
    for _ in range(34):
        t = rnd.uniform(0, 1)
        x, y = -0.05 + 0.50 * t + rnd.uniform(-0.12, 0.10), 1.05 - 0.55 * t + rnd.uniform(-0.10, 0.12)
        r = rnd.uniform(0.08, 0.15) * (1.1 - 0.4 * t)
        sd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    sm = sm.filter(ImageFilter.GaussianBlur(7))
    K.glow(c, sm, (90, 110, 170, 255), 18, 0.9)
    K.fill(c, sm, (8, 8, 18, 255))
    rim_ = ImageChops.subtract(sm, ImageChops.offset(sm, int(0.03 * W), int(0.03 * W)))
    K.fill(c, scale(K.soften(rim_, 4), 0.7), (150, 170, 230, 255))
    # wisps trailing off the smoke
    wisp = K.shape(lambda d: [brush(d, [(0.30 + 0.12 * t, 0.56 - 0.10 * t + 0.03 * math.sin(t * 6))
                                        for t in (i / 12 for i in range(13))], 0.03, 0.004),
                              brush(d, [(0.44 + 0.10 * t, 0.70 - 0.04 * t + 0.03 * math.sin(t * 5))
                                        for t in (i / 12 for i in range(13))], 0.025, 0.004)])
    K.fill(c, scale(K.soften(wisp, 3), 0.55), (120, 140, 190, 255))
    return K.finish(c)


def flashy_shot():
    """An arrow trailing a blaze of sparkles (more damage, more attention)."""
    c = bg((196, 60, 150), (24, 4, 20), 0.6, 0.4)
    rnd = random.Random(5)
    spots = []
    for i in range(7):
        t = i / 6
        spots.append((0.16 + 0.56 * t + rnd.uniform(-0.04, 0.04), 0.84 - 0.56 * t + rnd.uniform(-0.04, 0.04),
                      0.03 + 0.03 * t))
    sparkles(c, spots, (255, 250, 220), (255, 200, 120))
    ar = K.shape(lambda d: GC.arrow(d, 0.12, 0.88, 0.80, 0.22))
    _arrow_paint(c, ar, (255, 220, 160), (255, 250, 230), (230, 180, 90))
    b = burst(0.80, 0.22, 8, 0.18, 0.05, 0.2)
    lit(c, b, (255, 220, 120), (255, 255, 230), 16, 1.6)
    return K.finish(c)


def velocity_shot():
    """An arrow tearing through rings of wind."""
    c = bg((40, 156, 124), (4, 22, 18), 0.5, 0.5)
    streaks = K.shape(lambda d: [d.line(pts([(x0, y), (x0 + 0.3, y)]), fill=160, width=int(0.012 * W))
                                 for x0, y in ((0.04, 0.34), (0.06, 0.66), (0.12, 0.26), (0.10, 0.74))])
    K.fill(c, K.soften(streaks, 3), (220, 255, 240, 255))
    rings = K.shape(lambda d: [d.ellipse(pts([(x - 0.05, 0.5 - r), (x + 0.05, 0.5 + r)]), outline=255,
                                         width=int(0.02 * W)) for x, r in ((0.30, 0.14), (0.50, 0.21), (0.70, 0.27))])
    K.glow(c, rings, (180, 255, 220, 255), 8, 1.3)
    K.fill(c, K.soften(rings), (230, 255, 245, 255))
    ar = K.shape(lambda d: GC.arrow(d, 0.06, 0.5, 0.94, 0.5))
    _arrow_paint(c, ar, (230, 255, 240))
    return K.finish(c)


def double_shot():
    """Two arrows loosed side by side."""
    c = bg((176, 34, 54), (24, 2, 8), 0.5, 0.5)
    rays(c, 0.86, 0.14, 10, (255, 200, 200), 0.06, 0.9, 60, 8, 2.0)
    for dx, dy in ((-0.08, -0.08), (0.08, 0.08)):
        ar = K.shape(lambda d, dx=dx, dy=dy: GC.arrow(d, 0.14 + dx, 0.86 + dy, 0.84 + dx, 0.16 + dy))
        _arrow_paint(c, ar, (255, 210, 200))
    sparkles(c, [(0.80, 0.10, 0.06), (0.92, 0.26, 0.06)], (255, 255, 255), (255, 180, 170))
    return K.finish(c)


# ---- SAM ------------------------------------------------------------------------------------------------------------
def warding_circle():
    """A paper ward inside a ring of light (demons kept at bay)."""
    c = bg((116, 44, 96), (16, 4, 14), 0.5, 0.5)
    ring = K.shape(lambda d: [d.ellipse(pts([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=int(0.026 * W)),
                              d.ellipse(pts([(0.20, 0.20), (0.80, 0.80)]), outline=255, width=int(0.010 * W))])
    K.glow(c, ring, (255, 210, 120, 255), 12, 1.5)
    K.fill(c, K.soften(ring), (255, 230, 160, 255))
    ticks = K.shape(lambda d: [d.line(pts([(0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30),
                                           (0.5 + math.cos(a) * 0.36, 0.5 + math.sin(a) * 0.36)]), fill=255,
                                      width=int(0.014 * W)) for a in [i * math.pi / 6 for i in range(12)]])
    K.fill(c, K.soften(ticks), (255, 220, 140, 255))
    paper = poly([(0.40, 0.20), (0.60, 0.20), (0.60, 0.80), (0.40, 0.80)])
    K.glow(c, paper, (255, 240, 200, 255), 14, 1.3)
    K.shadow(c, paper, 4, 7, 7, 160)
    K.fill(c, K.soften(paper), lin((255, 250, 232), (226, 214, 180)))
    glyph = K.shape(lambda d: [brush(d, [(0.44, 0.27), (0.56, 0.27)], 0.022),
                               brush(d, [(0.50, 0.24), (0.50, 0.60)], 0.026, 0.012),
                               brush(d, [(0.44, 0.38), (0.56, 0.42)], 0.02),
                               brush(d, [(0.43, 0.52), (0.50, 0.46), (0.57, 0.54)], 0.02),
                               d.ellipse(pts([(0.455, 0.64), (0.545, 0.73)]), outline=255, width=int(0.014 * W))])
    K.fill(c, K.soften(glyph), (200, 30, 30, 255))
    return K.finish(c)


def shikikoyo():
    """Autumn leaves swirling around a glowing orb of spirit, handed to an ally."""
    c = bg((40, 104, 104), (4, 14, 16), 0.5, 0.5)
    sw = K.shape(lambda d: brush(d, arc_path(0.5, 0.5, 0.32, 0.32, 120, 400, 60), 0.008, 0.04))
    K.fill(c, scale(K.soften(sw, 3), 0.6), (255, 220, 160, 255))
    orb = ell(0.36, 0.40, 0.58, 0.62)
    K.glow(c, orb, (255, 220, 120, 255), 26, 1.6)
    K.fill(c, K.soften(orb, 2), rad((255, 255, 240), (255, 180, 60), 0.44, 0.47, 0.13))
    for (x, y, s, a, cols) in ((0.26, 0.28, 0.22, -30, ((255, 120, 50), (190, 30, 20))),
                               (0.76, 0.36, 0.19, 40, ((255, 190, 60), (220, 90, 20))),
                               (0.62, 0.76, 0.22, 160, ((255, 90, 50), (160, 20, 20)))):
        lf = K.shape(lambda d, x=x, y=y, s=s, a=a: maple(d, x, y, s, a))
        K.shadow(c, lf, 3, 6, 6, 150)
        K.fill(c, K.soften(lf), lin(*cols))
    return K.finish(c)


def blade_bash():
    """A katana's hilt driven into the foe, stunning it."""
    c = bg((50, 92, 146), (6, 12, 24), 0.35, 0.65)
    b = burst(0.27, 0.73, 10, 0.22, 0.09, 0.2)
    lit(c, b, (200, 230, 255), rad((255, 255, 255), (130, 190, 255), 0.27, 0.73, 0.22), 14, 1.3)
    kt = K.shape(lambda d: GC.katana(d, 0.30, 0.70, 0.90, 0.12, 0.05, 'blade'))
    K.glow(c, kt, (200, 230, 255, 255), 12, 1.2)
    K.shadow(c, kt, 4, 7, 7, 160)
    K.fill(c, K.soften(kt), steel())
    hl = K.shape(lambda d: GC.katana(d, 0.30, 0.70, 0.90, 0.12, 0.05, 'hilt'))
    K.fill(c, K.soften(hl), lin((80, 60, 110), (20, 14, 30)))
    stun_stars(c, 0.36, 0.30, 0.20, 0.07, (255, 240, 150))
    return K.finish(c)


def sekkanoki():
    """A drawn katana with a snow-blossom at its edge (the next weapon skill for less)."""
    c = bg((150, 166, 226), (14, 18, 44), 0.6, 0.4)
    kt = K.shape(lambda d: GC.katana(d, 0.08, 0.86, 0.80, 0.30, 0.05, 'blade'))
    K.glow(c, kt, (230, 240, 255, 255), 12, 1.2)
    K.shadow(c, kt, 4, 7, 7, 160)
    K.fill(c, K.soften(kt), steel())
    hl = K.shape(lambda d: GC.katana(d, 0.08, 0.86, 0.80, 0.30, 0.05, 'hilt'))
    K.fill(c, K.soften(hl), lin((60, 60, 120), (14, 14, 34)))

    def flower(d):
        for i in range(6):
            a = math.radians(-90 + 60 * i)
            GA.leaf(d, 0.66, 0.30, a, 0.22, 0.07)
    fl = K.shape(flower)
    K.glow(c, fl, (230, 240, 255, 255), 14, 1.5)
    K.fill(c, K.soften(fl), rad((255, 255, 255), (190, 210, 255), 0.66, 0.30, 0.22))
    cen = ell(0.63, 0.27, 0.69, 0.33)
    K.fill(c, K.soften(cen), (160, 190, 255, 255))
    motes(c, 6, 14, (0.1, 0.05, 0.9, 0.6), (0.006, 0.012), (255, 255, 255), (220, 230, 255))
    return K.finish(c)


def sengikori():
    """An ink-brush ensō, cut through by a bright slash (the foe left open to the chain)."""
    c = bg((250, 150, 70), (90, 20, 6), 0.5, 0.45, 0.6)
    enso = K.shape(lambda d: [brush(d, [(0.5 + math.cos(math.radians(a)) * 0.30,
                                         0.5 + math.sin(math.radians(a)) * 0.30)
                                        for a in [130 + 320 * i / 80 for i in range(81)]][:41], 0.10, 0.075),
                              brush(d, [(0.5 + math.cos(math.radians(a)) * 0.30,
                                         0.5 + math.sin(math.radians(a)) * 0.30)
                                        for a in [130 + 320 * i / 80 for i in range(81)]][40:], 0.075, 0.015)])
    K.shadow(c, enso, 4, 7, 7, 150)
    K.fill(c, K.soften(enso), (24, 10, 8, 255))
    slash = K.shape(lambda d: d.polygon(pts(_taper([(0.08 + 0.86 * t, 0.86 - 0.74 * t) for t in
                                                [i / 30 for i in range(31)]], 0.055)), fill=255))
    K.glow(c, slash, (255, 240, 200, 255), 14, 1.6)
    K.fill(c, K.soften(slash), (255, 255, 240, 255))
    seal = K.shape(lambda d: d.rounded_rectangle(pts([(0.70, 0.70), (0.80, 0.80)]), radius=0.01 * W, fill=255))
    K.fill(c, K.soften(seal), (180, 20, 20, 255))
    return K.finish(c)


# ---- NIN ------------------------------------------------------------------------------------------------------------
def scroll(c, cx, cy, s, ang, paper=((255, 248, 226), (220, 200, 160)), tie=(200, 40, 40)):
    body = K.shape(lambda d: d.polygon(xf([(-0.30, -0.10), (0.30, -0.10), (0.30, 0.10), (-0.30, 0.10)], cx, cy, s,
                                          ang), fill=255))
    rolls = K.shape(lambda d: [d.polygon(xf(rrect(0.09, 0.30, 0.04), cx + math.cos(math.radians(ang)) * 0.31 * s * k,
                                            cy + math.sin(math.radians(ang)) * 0.31 * s * k, s, ang), fill=255)
                               for k in (-1, 1)])
    both = ImageChops.lighter(body, rolls)
    K.glow(c, both, (255, 240, 200, 255), 12, 1.2)
    K.shadow(c, both, 4, 7, 7, 170)
    K.fill(c, K.soften(body), lin(*paper))
    K.fill(c, K.soften(rolls), lin((150, 90, 50), (60, 30, 14), 0))
    glyph = K.shape(lambda d: [d.polygon(xf([(x0, -0.05), (x0 + 0.016, -0.05), (x0 + 0.016, 0.03), (x0, 0.03)],
                                            cx, cy, s, ang), fill=255) for x0 in (-0.20, -0.13, 0.13, 0.20)])
    K.fill(c, scale(K.soften(glyph), 0.7), (60, 40, 30, 255))
    t = K.shape(lambda d: d.polygon(xf([(0.04, -0.11), (0.08, -0.11), (0.08, 0.11), (0.04, 0.11)], cx, cy, s, ang),
                                    fill=255))
    K.fill(c, K.soften(t), col(tie))


def futae():
    """Two ninjutsu scrolls laid one over the other (the next technique doubled)."""
    c = bg((56, 56, 140), (6, 6, 22), 0.5, 0.45)
    rays(c, 0.5, 0.5, 14, (200, 210, 255), 0.05, 0.7, 70, 8)
    scroll(c, 0.5, 0.42, 1.15, -28, ((240, 236, 255), (190, 180, 220)), (60, 120, 220))
    scroll(c, 0.5, 0.60, 1.15, 22)
    sparkles(c, [(0.80, 0.20, 0.07), (0.20, 0.82, 0.05)], (255, 255, 255), (200, 210, 255))
    return K.finish(c)


def sange():
    """A spray of shuriken flung wide (every throw a critical)."""
    c = bg((166, 32, 44), (22, 2, 6), 0.3, 0.7)
    origin = (0.18, 0.82)
    spots = [(0.44, 0.24, 0.14, 0.2), (0.76, 0.30, 0.15, 0.6), (0.74, 0.66, 0.12, 1.1), (0.40, 0.52, 0.10, 0.4)]
    trails = K.shape(lambda d: [d.line(pts([origin, (x, y)]), fill=150, width=int(0.012 * W))
                                for x, y, _, _ in spots])
    K.fill(c, fade_along(trails, origin[0] + 0.5, origin[1] - 0.5, *origin).filter(ImageFilter.GaussianBlur(3)),
           (255, 210, 190, 255))
    for x, y, r, a in spots:
        sh = K.shape(lambda d, x=x, y=y, r=r, a=a: GC.shuriken(d, x, y, r, a))
        hole = ell(x - r * 0.18, y - r * 0.18, x + r * 0.18, y + r * 0.18)
        sh = ImageChops.subtract(sh, hole)
        K.glow(c, sh, (255, 190, 170, 255), 8, 1.3)
        K.shadow(c, sh, 3, 6, 5, 160)
        K.fill(c, K.soften(sh), steel())
    return K.finish(c)


# ---- DRG ------------------------------------------------------------------------------------------------------------
def super_jump():
    """A lance rocketing up through the clouds and out of sight."""
    c = bg((120, 190, 250), (10, 30, 74), 0.5, 0.2, 0.85)
    GC.streaks(c, [(0.26, 1.0, 0.26, 0.50), (0.74, 1.0, 0.74, 0.46), (0.36, 1.0, 0.36, 0.66), (0.64, 1.0, 0.64, 0.62)],
               (255, 250, 230, 255), 0.022, 160, 4)
    ln = K.shape(lambda d: GC.lance(d, 0.5, 0.88, 0.5, 0.05, w=0.065))
    K.glow(c, ln, (255, 240, 180, 255), 18, 1.6)
    K.shadow(c, ln, 4, 7, 6, 150)
    K.fill(c, K.soften(ln), lin((255, 250, 220), (200, 160, 80), 0))
    clouds = K.shape(lambda d: [d.ellipse(pts([(x - r, 0.86 - r * 0.5), (x + r, 0.86 + r * 0.5)]), fill=255)
                                for x, r in ((0.12, 0.16), (0.30, 0.19), (0.70, 0.19), (0.88, 0.16), (0.5, 0.14))])
    K.fill(c, K.soften(clouds, 6), lin((255, 255, 255), (230, 210, 210)))
    sparkles(c, [(0.5, 0.08, 0.12)], (255, 255, 255), (255, 230, 160))
    return K.finish(c)


def spirit_link():
    """A stream of life flowing up from the dragoon to the wyvern."""
    c = bg((150, 176, 64), (14, 22, 6), 0.5, 0.4)
    stream = K.shape(lambda d: brush(d, GA.bezier((0.5, 1.0), (0.32, 0.74), (0.5, 0.56), 30), 0.12, 0.03))
    K.fill(c, scale(stream.filter(ImageFilter.GaussianBlur(10)), 0.8), (200, 255, 170, 255))
    hearts = K.shape(lambda d: [GB.heart(d, x, y, s) for x, y, s in ((0.42, 0.82, 0.12), (0.39, 0.70, 0.10),
                                                                     (0.46, 0.60, 0.08))])
    lit(c, hearts, (220, 255, 200), (255, 255, 240), 8, 1.4)
    wy = K.shape(lambda d: GC.wyvern(d, 0.5, 0.40, 0.90))
    K.glow(c, wy, (230, 255, 210, 255), 16, 1.5)
    K.shadow(c, wy, 4, 7, 7, 140)
    K.fill(c, K.soften(wy), lin((220, 240, 255), (110, 150, 200)))
    return K.finish(c)


def angon():
    """A thrown javelin punching through a shield (the foe's defence broken)."""
    c = bg((190, 100, 36), (28, 10, 2), 0.6, 0.45)
    sh = ell(0.44, 0.24, 0.84, 0.64)
    lit(c, sh, (255, 210, 140), lin((200, 170, 130), (110, 80, 50)), 14, 1.2, sh=True)
    inner = ell(0.49, 0.29, 0.79, 0.59)
    K.fill(c, K.soften(inner), rad((170, 120, 80), (90, 50, 26), 0.6, 0.38, 0.2))
    cracks = K.shape(lambda d: [d.line(pts(seq), fill=255, width=int(0.012 * W)) for seq in (
        [(0.64, 0.44), (0.58, 0.32), (0.60, 0.25)], [(0.64, 0.44), (0.76, 0.40), (0.83, 0.46)],
        [(0.64, 0.44), (0.68, 0.56), (0.62, 0.63)], [(0.64, 0.44), (0.50, 0.48), (0.45, 0.44)])])
    K.fill(c, K.soften(cracks), (30, 10, 4, 255))
    ln = K.shape(lambda d: GC.lance(d, 0.06, 0.94, 0.70, 0.38, w=0.04))
    K.glow(c, ln, (255, 230, 190, 255), 10, 1.3)
    K.shadow(c, ln, 4, 7, 6, 150)
    K.fill(c, K.soften(ln), lin((255, 255, 255), (170, 160, 170), 0))
    b = burst(0.66, 0.42, 8, 0.12, 0.04, 0.3)
    K.fill(c, scale(K.soften(b, 3), 0.85), (255, 255, 220, 255))
    return K.finish(c)


def deep_breathing():
    """The wyvern drawing in a great breath, air spiralling into its maw."""
    c = bg((40, 156, 176), (4, 20, 28), 0.5, 0.4)
    sp = K.shape(lambda d: [brush(d, [(0.5 + math.cos(a0 + t * 4.0) * (0.44 - t * 0.36),
                                       0.24 + math.sin(a0 + t * 4.0) * (0.24 - t * 0.20)) for t in
                                      [i / 40 for i in range(41)]], 0.004, 0.03) for a0 in (0.4, 2.5, 4.6)])
    K.glow(c, sp, (220, 255, 255, 255), 6, 1.2)
    K.fill(c, K.soften(sp), (240, 255, 255, 230))
    wy = K.shape(lambda d: GC.wyvern(d, 0.5, 0.58, 0.95))
    K.glow(c, wy, (200, 250, 255, 255), 14, 1.4)
    K.shadow(c, wy, 4, 7, 7, 140)
    K.fill(c, K.soften(wy), lin((120, 150, 230), (40, 60, 140)))
    chest = ell(0.43, 0.54, 0.57, 0.74)
    K.glow(c, chest, (180, 255, 255, 255), 10, 1.4)
    K.fill(c, scale(K.soften(chest, 4), 0.8), (220, 255, 255, 255))
    return K.finish(c)


def spirit_jump():
    """A lance diving down with the wyvern's spirit wings behind it."""
    c = bg((70, 56, 160), (6, 4, 24), 0.4, 0.4)
    ghost = K.shape(lambda d: GC.wyvern(d, 0.42, 0.42, 1.25))
    K.glow(c, ghost, (170, 230, 255, 255), 16, 0.8)
    K.fill(c, scale(K.soften(ghost, 3), 0.35), (170, 230, 255, 255))
    GC.streaks(c, [(0.08, 0.02, 0.40, 0.40), (0.26, -0.02, 0.54, 0.30)], (210, 240, 255, 255), 0.02, 150, 4)
    ln = K.shape(lambda d: GC.lance(d, 0.14, 0.12, 0.84, 0.86, w=0.05))
    K.glow(c, ln, (200, 240, 255, 255), 14, 1.4)
    K.shadow(c, ln, 4, 7, 6, 150)
    K.fill(c, K.soften(ln), lin((255, 255, 255), (160, 176, 210), 0))
    sparkles(c, [(0.84, 0.86, 0.10)], (255, 255, 255), (170, 230, 255))
    return K.finish(c)


# ---- BLU / COR / PUP ------------------------------------------------------------------------------------------------
def convergence():
    """Arrows of light converging on one point (the next blue magic focused on a single foe)."""
    c = bg((40, 90, 180), (4, 10, 30), 0.5, 0.5)
    lines = K.shape(lambda d: [d.line(pts([(0.5 + math.cos(a) * 0.46, 0.5 + math.sin(a) * 0.46),
                                           (0.5 + math.cos(a) * 0.14, 0.5 + math.sin(a) * 0.14)]), fill=200,
                                      width=int(0.014 * W)) for a in [i * math.pi / 4 for i in range(8)]])
    K.fill(c, K.soften(lines, 2), (200, 230, 255, 255))
    heads = K.shape(lambda d: [GD.arrowhead(d, 0.5 + math.cos(a) * 0.16, 0.5 + math.sin(a) * 0.16,
                                            math.degrees(a) + 180, 0.09) for a in [i * math.pi / 4 for i in range(8)]])
    K.glow(c, heads, (140, 220, 255, 255), 8, 1.3)
    K.fill(c, K.soften(heads), lin((255, 255, 255), (170, 210, 255)))
    core = ell(0.44, 0.44, 0.56, 0.56)
    K.glow(c, core, (255, 120, 220, 255), 18, 1.8)
    K.fill(c, K.soften(core, 2), (255, 240, 255, 255))
    sparkles(c, [(0.5, 0.5, 0.08)], (255, 255, 255), (255, 160, 230))
    return K.finish(c)


def card(c, cx, cy, s, ang, face=True, glowc=(255, 240, 200), suit=(200, 30, 40)):
    body = K.shape(lambda d: d.polygon(xf(rrect(0.40, 0.58, 0.05), cx, cy, s, ang), fill=255))
    K.glow(c, body, col(glowc), 10, 1.0)
    K.shadow(c, body, 4, 7, 7, 170)
    if face:
        K.fill(c, K.soften(body), lin((255, 252, 244), (220, 212, 196)))
        pip = K.shape(lambda d: d.polygon(xf([(0, -0.12), (0.08, 0), (0, 0.12), (-0.08, 0)], cx, cy, s, ang),
                                          fill=255))
        K.fill(c, K.soften(pip), col(suit))
    else:
        K.fill(c, K.soften(body), lin((200, 40, 50), (110, 14, 24)))
        inner = K.shape(lambda d: d.polygon(xf(rrect(0.30, 0.48, 0.03), cx, cy, s, ang), outline=255,
                                            width=int(0.010 * W)))
        K.fill(c, K.soften(inner), (255, 220, 150, 255))
        dia = K.shape(lambda d: d.polygon(xf([(0, -0.10), (0.07, 0), (0, 0.10), (-0.07, 0)], cx, cy, s, ang),
                                          fill=255))
        K.fill(c, K.soften(dia), (255, 220, 150, 255))


def random_deal():
    """Three cards fanned from the dealer's hand, a turning arrow round them (a cooldown reset by chance)."""
    c = bg((40, 130, 76), (4, 20, 10), 0.5, 0.5)
    arr = K.shape(lambda d: GA.arc_arrow(d, 0.5, 0.52, 0.40, 150, 400, 0.03))
    K.glow(c, arr, (255, 240, 180, 255), 8, 1.2)
    K.fill(c, K.soften(arr), (255, 236, 170, 255))
    card(c, 0.36, 0.56, 0.9, -24, False)
    card(c, 0.64, 0.56, 0.9, 24, False)
    card(c, 0.5, 0.50, 0.95, 0, True)
    return K.finish(c)


def snake_eye():
    """A die showing a single pip, the pip a serpent's eye."""
    c = bg((110, 150, 40), (12, 20, 4), 0.5, 0.45)
    face = K.shape(lambda d: d.polygon(xf(rrect(0.56, 0.56, 0.09), 0.5, 0.5, 1.0, -8), fill=255))
    lit(c, face, (220, 255, 160), lin((255, 252, 240), (200, 192, 170)), 16, 1.2, sh=True)
    eye = K.shape(lambda d: GC.eye_shape(d, 0.5, 0.5, 0.17, 0.10))
    K.glow(c, eye, (180, 255, 60, 255), 10, 1.4)
    K.fill(c, K.soften(eye), rad((255, 250, 120), (120, 190, 20), 0.5, 0.5, 0.17))
    pupil = poly([(0.5, 0.40), (0.52, 0.5), (0.5, 0.60), (0.48, 0.5)])
    K.fill(c, K.soften(pupil), (10, 10, 4, 255))
    hi = ell(0.53, 0.44, 0.56, 0.47)
    K.fill(c, K.soften(hi), (255, 255, 255, 230))
    return K.finish(c)


def fold():
    """A card folded down at the corner and laid away (the last roll given up)."""
    c = bg((130, 34, 44), (18, 4, 6), 0.5, 0.45)
    card(c, 0.42, 0.56, 1.05, -10, False, (255, 200, 180))
    body = poly([(0.40, 0.18), (0.80, 0.18), (0.80, 0.52), (0.60, 0.80), (0.40, 0.80)])
    flap = poly([(0.80, 0.52), (0.60, 0.80), (0.56, 0.52)])
    K.glow(c, body, (255, 230, 200, 255), 10, 1.0)
    K.shadow(c, ImageChops.lighter(body, flap), 4, 7, 7, 170)
    K.fill(c, K.soften(body), lin((255, 252, 244), (222, 212, 196)))
    pip = poly([(0.60, 0.32), (0.66, 0.42), (0.60, 0.52), (0.54, 0.42)])
    K.fill(c, K.soften(pip), (200, 30, 40, 255))
    K.fill(c, K.soften(flap), lin((220, 60, 66), (120, 16, 24), 45))
    crease = K.shape(lambda d: d.line(pts([(0.80, 0.52), (0.60, 0.80)]), fill=255, width=int(0.01 * W)))
    K.fill(c, K.soften(crease), (255, 255, 255, 200))
    return K.finish(c)


def role_reversal():
    """Master and automaton trading places (and their health) along two opposing arrows."""
    c = bg((166, 120, 60), (24, 14, 6), 0.5, 0.45)
    master = K.shape(lambda d: GD.bust(d, 0.22, 0.70, 0.95))
    lit(c, master, (255, 230, 190), lin((255, 230, 200), (190, 140, 100)), 10, 1.2, sh=True)
    head = K.shape(lambda d: [d.rounded_rectangle(pts([(0.66, 0.44), (0.90, 0.66)]), radius=0.05 * W, fill=255),
                              d.chord(pts([(0.58, 0.68), (0.98, 1.06)]), 180, 360, fill=255),
                              d.rectangle(pts([(0.75, 0.64), (0.81, 0.70)]), fill=255)])
    lit(c, head, (255, 220, 160), lin((240, 214, 170), (150, 104, 56)), 10, 1.2, sh=True)
    vis = K.shape(lambda d: d.rounded_rectangle(pts([(0.69, 0.52), (0.87, 0.57)]), radius=0.02 * W, fill=255))
    K.glow(c, vis, (120, 220, 255, 255), 6, 1.4)
    K.fill(c, K.soften(vis), (170, 240, 255, 255))
    g = K.shape(lambda d: GD.gear(d, 0.78, 0.44, 0.06, 0.042, 8, 0.018))
    K.fill(c, K.soften(g), gold())
    arr = K.shape(lambda d: [block_arrow(d, 0.16, 0.26, 0.84, 0.26, 0.07, 0.12, 0.14),
                             block_arrow(d, 0.84, 0.40, 0.40, 0.40, 0.07, 0.12, 0.14)])
    K.glow(c, arr, (255, 255, 220, 255), 8, 1.3)
    K.shadow(c, arr, 3, 6, 6, 150)
    K.fill(c, K.soften(arr), lin((255, 255, 240), (240, 200, 120)))
    return K.finish(c)


def ventriloquy():
    """A puppet's hinged jaw dropping open, a speech bubble thrown from it (enmity thrown too)."""
    c = bg((184, 90, 134), (24, 8, 18), 0.45, 0.5)
    face = ell(0.16, 0.28, 0.56, 0.72)
    lit(c, face, (255, 220, 240), lin((255, 240, 220), (220, 180, 150)), 14, 1.2, sh=True)
    jaw = poly([(0.26, 0.62), (0.46, 0.62), (0.44, 0.82), (0.28, 0.82)])
    K.shadow(c, jaw, 3, 6, 6, 160)
    K.fill(c, K.soften(jaw), lin((240, 220, 200), (190, 150, 120)))
    mouth = poly([(0.27, 0.60), (0.45, 0.60), (0.45, 0.66), (0.27, 0.66)])
    K.fill(c, K.soften(mouth), (60, 10, 20, 255))
    lines = K.shape(lambda d: [d.line(pts([(0.27, 0.58), (0.27, 0.70)]), fill=255, width=int(0.01 * W)),
                               d.line(pts([(0.45, 0.58), (0.45, 0.70)]), fill=255, width=int(0.01 * W))])
    K.fill(c, K.soften(lines), (120, 70, 50, 255))
    eyes = K.shape(lambda d: [d.ellipse(pts([(x - 0.03, 0.42), (x + 0.03, 0.48)]), fill=255) for x in (0.29, 0.43)])
    K.fill(c, K.soften(eyes), (30, 20, 40, 255))
    cheeks = K.shape(lambda d: [d.ellipse(pts([(x - 0.035, 0.53), (x + 0.035, 0.57)]), fill=255)
                                for x in (0.23, 0.49)])
    K.fill(c, scale(K.soften(cheeks, 3), 0.8), (240, 110, 130, 255))
    bub = ImageChops.lighter(ell(0.54, 0.14, 0.92, 0.42), poly([(0.60, 0.36), (0.54, 0.50), (0.68, 0.38)]))
    lit(c, bub, (255, 230, 245), (255, 255, 255), 12, 1.3, sh=True)
    dots_ = K.shape(lambda d: [d.ellipse(pts([(x - 0.025, 0.255), (x + 0.025, 0.305)]), fill=255)
                               for x in (0.64, 0.73, 0.82)])
    K.fill(c, K.soften(dots_), (200, 40, 90, 255))
    return K.finish(c)


# ---- DNC ------------------------------------------------------------------------------------------------------------
def saber(d, x0, y0, x1, y1, curve=0.10):
    L, f = GC.frame(x0, y0, x1, y1)
    hilt = 0.22 * L
    top, bot = [], []
    for i in range(25):
        t = i / 24
        u = hilt + (L - hilt) * t
        bow = -curve * math.sin(math.pi * t * 0.9) * t
        half = 0.045 * (1 + 0.5 * t) * (1 if t < 0.85 else (1 - t) / 0.15)
        top.append(f(u, bow - half))
        bot.append(f(u, bow + half * 0.6))
    d.polygon(pts(top + bot[::-1]), fill=255)
    d.polygon(pts([f(0, -0.025), f(hilt, -0.025), f(hilt, 0.025), f(0, 0.025)]), fill=255)
    d.polygon(pts([f(hilt - 0.02, -0.08), f(hilt + 0.01, -0.08), f(hilt + 0.01, 0.08), f(hilt - 0.02, 0.08)]),
              fill=255)


def saber_dance():
    """Two curved sabers crossed in a whirl of silk."""
    c = bg((196, 52, 112), (26, 4, 16), 0.5, 0.5)
    rib = K.shape(lambda d: brush(d, [(0.5 + math.cos(t * 2 * math.pi * 1.2) * (0.40 - t * 0.12),
                                       0.54 + math.sin(t * 2 * math.pi * 1.2) * (0.20 - t * 0.04) - t * 0.10)
                                      for t in [i / 60 for i in range(61)]], 0.05, 0.015))
    K.glow(c, rib, (255, 200, 120, 255), 8, 1.2)
    K.fill(c, K.soften(rib), lin((255, 230, 140), (240, 150, 40)))
    for args in ((0.20, 0.86, 0.84, 0.12), (0.80, 0.86, 0.16, 0.12)):
        sb = K.shape(lambda d, args=args: saber(d, *args, curve=0.10 if args[0] < 0.5 else -0.10))
        K.glow(c, sb, (255, 220, 240, 255), 10, 1.2)
        K.shadow(c, sb, 4, 7, 7, 170)
        K.fill(c, K.soften(sb), steel())
    return K.finish(c)


def fan_dance():
    """An open dancer's fan, petals drifting off it."""
    c = bg((50, 150, 140), (4, 22, 22), 0.5, 0.55)
    cx, cy = 0.5, 0.80
    fan = poly([(cx, cy)] + arc_path(cx, cy, 0.42, 0.42, 200, 340, 40))
    hole = poly([(cx, cy)] + arc_path(cx, cy, 0.12, 0.12, 190, 350, 20))
    fanm = ImageChops.subtract(fan, hole)
    K.glow(c, fanm, (200, 255, 240, 255), 16, 1.3)
    K.shadow(c, fanm, 4, 7, 7, 160)
    K.fill(c, K.soften(fanm), rad((255, 210, 220), (200, 50, 90), cx, cy - 0.2, 0.4))
    for k in range(8):
        a0 = 200 + k * 17.5
        if k % 2 == 0:
            band = poly([(cx, cy)] + arc_path(cx, cy, 0.42, 0.42, a0, a0 + 17.5, 6))
            K.fill(c, scale(K.soften(ImageChops.subtract(band, hole)), 0.25), (255, 255, 255, 255))
    ribs = K.shape(lambda d: [d.line(pts([(cx + math.cos(math.radians(a)) * 0.12, cy + math.sin(math.radians(a)) * 0.12),
                                          (cx + math.cos(math.radians(a)) * 0.42, cy + math.sin(math.radians(a)) * 0.42)]),
                                     fill=255, width=int(0.008 * W)) for a in [200 + 17.5 * i for i in range(9)]])
    K.fill(c, scale(K.soften(ribs), 0.6), (120, 20, 50, 255))
    edge = K.shape(lambda d: d.arc(pts([(cx - 0.42, cy - 0.42), (cx + 0.42, cy + 0.42)]), 200, 340, fill=255,
                                   width=int(0.02 * W)))
    K.fill(c, K.soften(edge), gold())
    pivot = ell(cx - 0.04, cy - 0.04, cx + 0.04, cy + 0.04)
    K.fill(c, K.soften(pivot), gold())
    pet = K.shape(lambda d: [GA.leaf(d, x, y, a, 0.07, 0.03) for x, y, a in ((0.80, 0.24, 0.5), (0.20, 0.20, 2.4),
                                                                            (0.88, 0.40, 1.3))])
    K.fill(c, K.soften(pet), (255, 200, 220, 255))
    return K.finish(c)


def no_foot_rise():
    """A dancer rising en pointe, arms raised, finishing moves welling up around her as orbs of light."""
    c = bg((150, 64, 176), (20, 6, 24), 0.5, 0.45)
    floor = ell(0.30, 0.86, 0.70, 0.96)
    K.fill(c, scale(K.soften(floor, 10), 0.8), (255, 200, 255, 255))

    def dancer(d):
        d.ellipse(pts([(0.445, 0.185), (0.555, 0.295)]), fill=255)
        d.polygon(pts([(0.465, 0.29), (0.535, 0.29), (0.555, 0.47), (0.445, 0.47)]), fill=255)
        d.polygon(pts([(0.44, 0.44), (0.56, 0.44), (0.72, 0.58), (0.64, 0.57), (0.58, 0.60), (0.50, 0.58),
                       (0.42, 0.60), (0.36, 0.57), (0.28, 0.58)]), fill=255)
        brush(d, [(0.47, 0.31), (0.36, 0.22), (0.38, 0.12), (0.47, 0.08)], 0.035, 0.022)
        brush(d, [(0.53, 0.31), (0.64, 0.22), (0.62, 0.12), (0.53, 0.08)], 0.035, 0.022)
        brush(d, [(0.48, 0.56), (0.49, 0.74), (0.50, 0.90)], 0.05, 0.018)
        brush(d, [(0.53, 0.56), (0.66, 0.66), (0.52, 0.74)], 0.045, 0.02)
    m = K.shape(dancer)
    K.glow(c, m, (255, 190, 240, 255), 16, 1.8)
    K.fill(c, K.soften(m), lin((255, 240, 250), (230, 160, 210)))
    for x, y, r in ((0.20, 0.66, 0.05), (0.80, 0.62, 0.05), (0.22, 0.36, 0.045), (0.78, 0.32, 0.045),
                    (0.74, 0.08, 0.035)):
        o = ell(x - r, y - r, x + r, y + r)
        K.glow(c, o, (255, 200, 255, 255), 10, 1.6)
        K.fill(c, K.soften(o), rad((255, 255, 255), (240, 160, 255), x - 0.01, y - 0.01, r))
    return K.finish(c)


def presto():
    """A metronome ticking at full tilt (the next step comes quick)."""
    c = bg((222, 112, 40), (32, 10, 2), 0.5, 0.45)
    body = poly([(0.40, 0.18), (0.60, 0.18), (0.74, 0.86), (0.26, 0.86)])
    lit(c, body, (255, 220, 160), lin((170, 100, 60), (80, 40, 20)), 14, 1.2, sh=True)
    face = poly([(0.43, 0.26), (0.57, 0.26), (0.66, 0.72), (0.34, 0.72)])
    K.fill(c, K.soften(face), lin((255, 240, 210), (220, 190, 150)))
    base = K.shape(lambda d: d.rectangle(pts([(0.24, 0.80), (0.76, 0.88)]), fill=255))
    K.fill(c, K.soften(base), lin((120, 70, 40), (60, 30, 14)))
    piv = (0.5, 0.70)
    for ang, a in ((-34, 0.25), (-22, 0.45), (22, 0.45), (34, 0.25)):
        g = K.shape(lambda d, ang=ang: d.line(pts([piv, (piv[0] + math.sin(math.radians(ang)) * 0.60,
                                                         piv[1] - math.cos(math.radians(ang)) * 0.60)]),
                                              fill=255, width=int(0.022 * W)))
        K.fill(c, scale(K.soften(g, 3), a), (255, 240, 210, 255))
    arm = K.shape(lambda d: d.line(pts([piv, (piv[0] + math.sin(math.radians(-8)) * 0.62,
                                              piv[1] - math.cos(math.radians(-8)) * 0.62)]), fill=255,
                                   width=int(0.024 * W)))
    weight = K.shape(lambda d: d.polygon(xf(rrect(0.10, 0.07, 0.015), piv[0] + math.sin(math.radians(-8)) * 0.40,
                                            piv[1] - math.cos(math.radians(-8)) * 0.40, 1.0, -8), fill=255))
    K.shadow(c, arm, 3, 5, 5, 150)
    K.fill(c, K.soften(arm), lin((255, 240, 200), (200, 150, 70)))
    K.fill(c, K.soften(weight), gold())
    arcm = K.shape(lambda d: d.arc(pts([(piv[0] - 0.56, piv[1] - 0.56), (piv[0] + 0.56, piv[1] + 0.56)]), 236, 304,
                                   fill=255, width=int(0.014 * W)))
    K.fill(c, K.soften(arcm, 2), (255, 250, 230, 230))
    return K.finish(c)


# ---- SCH ------------------------------------------------------------------------------------------------------------
def modus_veritas():
    """A golden balance of truth, weighing the scholar's helix."""
    c = bg((96, 44, 150), (12, 4, 24), 0.5, 0.4)
    rays(c, 0.5, 0.24, 14, (255, 230, 200), 0.05, 0.7, 70, 8)

    def scale_(d):
        d.rectangle(pts([(0.485, 0.20), (0.515, 0.84)]), fill=255)
        d.polygon(pts([(0.36, 0.86), (0.64, 0.86), (0.58, 0.80), (0.42, 0.80)]), fill=255)
        d.polygon(pts(GC.stroke([(0.16, 0.30), (0.5, 0.24), (0.84, 0.30)], 0.03)), fill=255)
        d.ellipse(pts([(0.465, 0.16), (0.535, 0.23)]), fill=255)
        for x in (0.16, 0.84):
            d.line(pts([(x, 0.30), (x - 0.10, 0.58)]), fill=255, width=int(0.008 * W))
            d.line(pts([(x, 0.30), (x + 0.10, 0.58)]), fill=255, width=int(0.008 * W))
            d.chord(pts([(x - 0.14, 0.48), (x + 0.14, 0.68)]), 0, 180, fill=255)
    m = K.shape(scale_)
    K.glow(c, m, (255, 220, 140, 255), 14, 1.3)
    K.shadow(c, m, 4, 7, 7, 160)
    K.fill(c, K.soften(m), gold())
    hx = K.shape(lambda d: [brush(d, [(0.84 + math.sin(t * 10 + ph) * 0.05, 0.50 - t * 0.30)
                                      for t in [i / 30 for i in range(31)]], 0.022, 0.012) for ph in (0, math.pi)])
    K.glow(c, hx, (200, 160, 255, 255), 8, 1.5)
    K.fill(c, K.soften(hx), (240, 220, 255, 255))
    sparkles(c, [(0.16, 0.44, 0.06)], (255, 255, 255), (255, 230, 170))
    return K.finish(c)


def enlightenment():
    """An oil lamp's flame of insight (both arts' secrets opened to the scholar)."""
    c = bg((44, 54, 130), (4, 6, 20), 0.5, 0.35)
    rays(c, 0.5, 0.30, 16, (255, 236, 180), 0.05, 0.75, 90, 8)
    fl = K.shape(lambda d: GA.flame(d, 0.5, 0.52, 0.09, 0.40, 0.02))
    K.glow(c, fl, (255, 200, 80, 255), 30, 1.6)
    K.fill(c, K.soften(fl), lin((255, 255, 230), (255, 150, 40), 270))
    lamp = ImageChops.lighter(ell(0.24, 0.54, 0.76, 0.80),
                              K.shape(lambda d: [d.polygon(pts(GC.stroke([(0.74, 0.62), (0.90, 0.56), (0.88, 0.48)],
                                                                         0.05, 0.03)), fill=255),
                                                 d.polygon(pts([(0.24, 0.66), (0.10, 0.56), (0.08, 0.50),
                                                                (0.26, 0.60)]), fill=255),
                                                 d.polygon(pts([(0.40, 0.78), (0.60, 0.78), (0.66, 0.88), (0.34, 0.88)]),
                                                           fill=255),
                                                 d.ellipse(pts([(0.44, 0.48), (0.56, 0.58)]), fill=255)]))
    K.glow(c, lamp, (255, 200, 100, 255), 14, 1.2)
    K.shadow(c, lamp, 4, 7, 7, 170)
    K.fill(c, K.soften(lamp), gold())
    hi = K.shape(lambda d: d.arc(pts([(0.30, 0.57), (0.70, 0.77)]), 200, 260, fill=255, width=int(0.018 * W)))
    K.fill(c, K.soften(hi, 2), (255, 255, 240, 220))
    return K.finish(c)


# ---- (job-neutral) --------------------------------------------------------------------------------------------------
def enrage():
    """The throbbing anger mark over a blaze of fury."""
    c = bg((222, 92, 30), (36, 6, 2), 0.5, 0.6)
    fl = K.shape(lambda d: [GA.flame(d, 0.5, 0.98, 0.34, 0.80, 0.0), GA.flame(d, 0.24, 0.98, 0.14, 0.46, -0.06),
                            GA.flame(d, 0.76, 0.98, 0.14, 0.48, 0.06)])
    K.fill(c, scale(K.soften(fl, 6), 0.55), lin((255, 210, 80), (200, 30, 10), 270))

    def vein(d):
        g = 0.05
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            cx, cy = 0.5 + sx * (0.13 + g), 0.48 + sy * (0.13 + g)
            a = math.degrees(math.atan2(-sy, -sx))
            brush(d, arc_path(cx, cy, 0.13, 0.13, a - 50, a + 50, 20), 0.07, 0.07)
    v = K.shape(vein)
    K.glow(c, v, (255, 60, 40, 255), 14, 1.6)
    K.shadow(c, v, 4, 7, 7, 170)
    K.fill(c, K.soften(v), lin((255, 120, 110), (190, 10, 20)))
    hi = K.shape(lambda d: [brush(d, arc_path(0.5 + sx * 0.18, 0.48 + sy * 0.18, 0.13, 0.13,
                                              math.degrees(math.atan2(-sy, -sx)) - 30,
                                              math.degrees(math.atan2(-sy, -sx)) + 10, 10), 0.018, 0.018)
                            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1))])
    K.fill(c, scale(K.soften(hi, 2), 0.6), (255, 230, 220, 255))
    return K.finish(c)


ICONS = {
    ('ja', 'Defender'): defender,
    ('ja', 'Aggressor'): aggressor,
    ("ja", "Warrior's Charge"): warriors_charge,
    ('ja', 'Tomahawk'): tomahawk,
    ('ja', 'Restraint'): restraint,
    ('ja', 'Dodge'): dodge,
    ('ja', 'Chi Blast'): chi_blast,
    ('ja', 'Mantra'): mantra,
    ('ja', 'Formless Strikes'): formless_strikes,
    ('ja', 'Footwork'): footwork,
    ('ja', 'Perfect Counter'): perfect_counter,
    ('ja', 'Divine Seal'): divine_seal,
    ('ja', 'Elemental Seal'): elemental_seal,
    ('ja', 'Dark Seal'): dark_seal,
    ('ja', 'Martyr'): martyr,
    ('ja', 'Devotion'): devotion,
    ('ja', 'Afflatus Solace'): afflatus_solace,
    ('ja', 'Afflatus Misery'): afflatus_misery,
    ('ja', 'Mana Wall'): mana_wall,
    ('ja', 'Composure'): composure,
    ('ja', 'Hide'): hide,
    ('ja', 'Mug'): mug,
    ('ja', 'Accomplice'): accomplice,
    ("ja", "Assassin's Charge"): assassins_charge,
    ('ja', 'Feint'): feint,
    ('ja', 'Collaborator'): collaborator,
    ('ja', 'Despoil'): despoil,
    ('ja', 'Holy Circle'): holy_circle,
    ('ja', 'Rampart'): rampart,
    ('ja', 'Fealty'): fealty,
    ('ja', 'Chivalry'): chivalry,
    ('ja', 'Divine Emblem'): divine_emblem,
    ('ja', 'Weapon Bash'): weapon_bash,
    ('ja', 'Diabolic Eye'): diabolic_eye,
    ('ja', 'Nether Void'): nether_void,
    ('ja', 'Gauge'): gauge,
    ('ja', 'Tame'): tame,
    ('ja', 'Feral Howl'): feral_howl,
    ('ja', 'Killer Instinct'): killer_instinct,
    ('ja', 'Nightingale'): nightingale,
    ('ja', 'Troubadour'): troubadour,
    ('ja', 'Pianissimo'): pianissimo,
    ('ja', 'Shadowbind'): shadowbind,
    ('ja', 'Camouflage'): camouflage,
    ('ja', 'Unlimited Shot'): unlimited_shot,
    ('ja', 'Stealth Shot'): stealth_shot,
    ('ja', 'Flashy Shot'): flashy_shot,
    ('ja', 'Velocity Shot'): velocity_shot,
    ('ja', 'Double Shot'): double_shot,
    ('ja', 'Warding Circle'): warding_circle,
    ('ja', 'Shikikoyo'): shikikoyo,
    ('ja', 'Blade Bash'): blade_bash,
    ('ja', 'Sekkanoki'): sekkanoki,
    ('ja', 'Sengikori'): sengikori,
    ('ja', 'Futae'): futae,
    ('ja', 'Sange'): sange,
    ('ja', 'Super Jump'): super_jump,
    ('ja', 'Spirit Link'): spirit_link,
    ('ja', 'Angon'): angon,
    ('ja', 'Deep Breathing'): deep_breathing,
    ('ja', 'Spirit Jump'): spirit_jump,
    ('ja', 'Convergence'): convergence,
    ('ja', 'Random Deal'): random_deal,
    ('ja', 'Snake Eye'): snake_eye,
    ('ja', 'Fold'): fold,
    ('ja', 'Role Reversal'): role_reversal,
    ('ja', 'Ventriloquy'): ventriloquy,
    ('ja', 'Saber Dance'): saber_dance,
    ('ja', 'Fan Dance'): fan_dance,
    ('ja', 'No Foot Rise'): no_foot_rise,
    ('ja', 'Presto'): presto,
    ('ja', 'Modus Veritas'): modus_veritas,
    ('ja', 'Enlightenment'): enlightenment,
    ('ja', 'Enrage'): enrage,
}
COVERS = {}
VARIANTS = {}
