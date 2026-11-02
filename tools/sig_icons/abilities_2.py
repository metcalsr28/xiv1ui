"""Signature icons, round 2: job abilities (list 2) -- job-point abilities, SP2 abilities and the later merits.
Painted with make_signature_icons' kit; reuses round 1's helpers (group_a .. group_d) without changing them."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_a as A
import group_b as B
import group_c as C
import group_d as D

W = K.W
p, pts, mask, shape, soften = K.p, K.pts, K.mask, K.shape, K.soften
bg, lit, rot, inter, minus, scale = D.bg, D.lit, D.rot, D.inter, D.minus, D.scale
stroke, arc_path, star, arrowhead, motes, sparkles, rays = (D.stroke, D.arc_path, D.star, D.arrowhead, D.motes,
                                                            D.sparkles, D.rays)
poly, ell, col = D.poly, D.ell, D.col


def lin(c0, c1, angle=90):
    return K.linear(col(c0), col(c1), angle)


def rad(c0, c1, cx=0.5, cy=0.5, r=0.5):
    return K.radial(col(c0), col(c1), cx, cy, r)


def union(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def metal_paint(top=(255, 255, 255), bot=(150, 160, 185), angle=90):
    return lin(top, bot, angle)


def gold_paint(angle=90):
    return lin((255, 242, 170), (206, 136, 46), angle)


def disc(cx, cy, r):
    return ell(cx - r, cy - r, cx + r, cy + r)


def ring(cx, cy, r, w, ry=None):
    ry = r if ry is None else ry
    return shape(lambda d: d.ellipse(pts([(cx - r, cy - ry), (cx + r, cy + ry)]), outline=255, width=int(w * W)))


def streak_lines(c, lines, color, w=0.02, alpha=150, blur=3):
    C.streaks(c, lines, col(color), w, alpha, blur)


# ---- shared motifs ---------------------------------------------------------------------------------------------------
def hand(d, cx, cy, s, fillv=255):
    """An open right hand, palm to the viewer, fingers up; (cx, cy) the middle of the palm."""
    d.rounded_rectangle(pts([(cx - 0.15 * s, cy - 0.10 * s), (cx + 0.15 * s, cy + 0.17 * s)]), radius=0.07 * s * W,
                        fill=fillv)
    for i, top in enumerate((-0.33, -0.40, -0.38, -0.30)):
        x = cx - 0.112 * s + i * 0.075 * s
        d.rounded_rectangle(pts([(x - 0.034 * s, cy + top * s), (x + 0.034 * s, cy + 0.0 * s)]),
                            radius=0.034 * s * W, fill=fillv)
    stroke(d, [(cx - 0.11 * s, cy + 0.08 * s), (cx - 0.22 * s, cy - 0.02 * s), (cx - 0.27 * s, cy - 0.13 * s)],
           0.075 * s, 0.065 * s, fillv)
    d.rectangle(pts([(cx - 0.11 * s, cy + 0.12 * s), (cx + 0.11 * s, cy + 0.42 * s)]), fill=fillv)


def rapier(d, x0, y0, x1, y1, w=0.024):
    """A rapier from the pommel (x0, y0) to the tip (x1, y1): needle blade, cup hilt, quillons."""
    L, f = C.frame(x0, y0, x1, y1)
    g = 0.15
    d.polygon(pts([f(g, -w), f(L, 0), f(g, w)]), fill=255)
    d.polygon(pts([f(0.02, -0.018), f(g, -0.018), f(g, 0.018), f(0.02, 0.018)]), fill=255)
    x, y = f(g - 0.01, 0)
    d.ellipse(pts([(x - 0.055, y - 0.055), (x + 0.055, y + 0.055)]), fill=255)
    stroke(d, [f(g + 0.01, -0.11), f(g + 0.03, 0), f(g + 0.01, 0.11)], 0.022)
    x, y = f(0.0, 0)
    d.ellipse(pts([(x - 0.032, y - 0.032), (x + 0.032, y + 0.032)]), fill=255)


def chain(d, x0, y0, x1, y1, n, h=0.05, w=0.018):
    """A chain of n links from (x0, y0) to (x1, y1); links alternate face-on and edge-on."""
    L, f = C.frame(x0, y0, x1, y1)
    step = L / n
    for i in range(n):
        u = step * (i + 0.5)
        ry = h if i % 2 == 0 else h * 0.32
        rx = step * 0.66
        ring_pts = [f(u + math.cos(2 * math.pi * k / 28) * rx, math.sin(2 * math.pi * k / 28) * ry)
                    for k in range(29)]
        d.line(pts(ring_pts), fill=255, width=int(w * W), joint='curve')


def hood(d, cx, cy, s, fillv=255):
    """A hooded head and shoulders; (cx, cy) the middle of the face opening."""
    d.polygon(pts([(cx, cy - 0.40 * s), (cx + 0.16 * s, cy - 0.30 * s), (cx + 0.24 * s, cy - 0.08 * s),
                   (cx + 0.25 * s, cy + 0.14 * s), (cx + 0.42 * s, cy + 0.32 * s), (cx + 0.46 * s, cy + 0.60 * s),
                   (cx - 0.46 * s, cy + 0.60 * s), (cx - 0.42 * s, cy + 0.32 * s), (cx - 0.25 * s, cy + 0.14 * s),
                   (cx - 0.24 * s, cy - 0.08 * s), (cx - 0.16 * s, cy - 0.30 * s)]), fill=fillv)


def face_hole(cx, cy, s):
    return ell(cx - 0.14 * s, cy - 0.18 * s, cx + 0.14 * s, cy + 0.14 * s)


def eyes(c, cx, cy, s, color, glowc, rx=0.045, ry=0.02):
    """Two glinting eyes, (cx, cy) between them."""
    m = shape(lambda d: [d.ellipse(pts([(cx + sx * 0.065 * s - rx * s, cy - ry * s),
                                        (cx + sx * 0.065 * s + rx * s, cy + ry * s)]), fill=255) for sx in (-1, 1)])
    K.glow(c, m, col(glowc), 8, 1.8)
    K.fill(c, soften(m, 1.0), col(color))


def puppet_head(d, cx, cy, s, fillv=255):
    """An automaton's head: an egg-shaped mask with a crest fin and a jaw line."""
    d.ellipse(pts([(cx - 0.20 * s, cy - 0.26 * s), (cx + 0.20 * s, cy + 0.26 * s)]), fill=fillv)
    d.polygon(pts([(cx - 0.05 * s, cy - 0.22 * s), (cx, cy - 0.42 * s), (cx + 0.05 * s, cy - 0.22 * s)]), fill=fillv)
    d.rectangle(pts([(cx - 0.07 * s, cy + 0.22 * s), (cx + 0.07 * s, cy + 0.36 * s)]), fill=fillv)


def puppet_face(c, cx, cy, s, eyec=(120, 230, 255), glowc=(120, 230, 255)):
    """The painted details of puppet_head: dark eye diamonds (lit), a mouth seam, a forehead jewel."""
    sock = shape(lambda d: [d.polygon(pts([(cx + sx * 0.10 * s - 0.065 * s, cy - 0.02 * s),
                                           (cx + sx * 0.10 * s, cy - 0.08 * s),
                                           (cx + sx * 0.10 * s + 0.065 * s, cy - 0.02 * s),
                                           (cx + sx * 0.10 * s, cy + 0.06 * s)]), fill=255) for sx in (-1, 1)])
    K.fill(c, soften(sock), (30, 20, 40, 255))
    e = shape(lambda d: [d.ellipse(pts([(cx + sx * 0.10 * s - 0.022 * s, cy - 0.03 * s),
                                        (cx + sx * 0.10 * s + 0.022 * s, cy + 0.01 * s)]), fill=255)
                         for sx in (-1, 1)])
    K.glow(c, e, col(glowc), 6, 1.8)
    K.fill(c, soften(e, 1), col(eyec))
    seam = shape(lambda d: d.line(pts([(cx - 0.09 * s, cy + 0.15 * s), (cx + 0.09 * s, cy + 0.15 * s)]), fill=255,
                                  width=max(2, int(0.014 * s * W))))
    K.fill(c, soften(seam), (60, 40, 50, 220))
    j = shape(lambda d: D.star(d, cx, cy - 0.15 * s, 0.045 * s, 0.02 * s, 4))
    K.glow(c, j, (255, 120, 120, 255), 5)
    K.fill(c, soften(j, 1), (255, 90, 110, 255))


# ---- WAR -------------------------------------------------------------------------------------------------------------
def blood_rage():
    """A great drop of blood burning in a red rage: the party's blood is up (critical hit rate)."""
    c = bg((170, 22, 30), (26, 2, 6), cy=0.58)
    rays(c, 0.5, 0.58, 16, (255, 120, 90), alpha=70)
    fl = shape(lambda d: [A.flame(d, 0.5, 0.92, 0.32, 0.82, 0.02), A.flame(d, 0.25, 0.90, 0.14, 0.46, -0.08),
                          A.flame(d, 0.75, 0.90, 0.14, 0.50, 0.08)])
    lit(c, fl, (255, 60, 30), lin((255, 190, 70), (210, 34, 20), 270), 26, 1.3)
    drop = poly(D.drop_pts(0.5, 0.26, 0.84, 0.20))
    lit(c, drop, (255, 40, 50), rad((255, 120, 120), (140, 0, 18), 0.44, 0.62, 0.32), 16, 1.3, sh=True)
    K.fill(c, soften(ell(0.40, 0.56, 0.46, 0.70), 3), (255, 220, 220, 190))
    motes(c, 41, 12, (0.15, 0.1, 0.85, 0.5), (0.006, 0.014), (255, 210, 160), (255, 90, 50))
    return K.finish(c)


def axe(d, cx, cy, s):
    """A double-bitted greataxe, standing up; (cx, cy) the middle of the haft."""
    d.rounded_rectangle(pts([(cx - 0.026 * s, cy - 0.40 * s), (cx + 0.026 * s, cy + 0.42 * s)]),
                        radius=0.02 * s * W, fill=255)
    for side in (-1, 1):
        outer = [(cx + side * (0.15 + 0.17 * math.sin(math.pi * t) ** 0.6) * s, cy + (-0.42 + 0.40 * t) * s)
                 for t in (i / 24 for i in range(25))]
        d.polygon(pts([(cx, cy - 0.30 * s)] + outer + [(cx, cy - 0.10 * s)]), fill=255)
    d.polygon(pts([(cx - 0.03 * s, cy - 0.40 * s), (cx, cy - 0.52 * s), (cx + 0.03 * s, cy - 0.40 * s)]), fill=255)


def war_helm(d, cx, cy, s, fillv=255):
    """A warrior's closed helm seen from the front (no horns); (cx, cy) the eye slit."""
    d.ellipse(pts([(cx - 0.20 * s, cy - 0.24 * s), (cx + 0.20 * s, cy + 0.16 * s)]), fill=fillv)
    d.polygon(pts([(cx - 0.20 * s, cy - 0.04 * s), (cx + 0.20 * s, cy - 0.04 * s), (cx + 0.18 * s, cy + 0.24 * s),
                   (cx + 0.08 * s, cy + 0.34 * s), (cx - 0.08 * s, cy + 0.34 * s), (cx - 0.18 * s, cy + 0.24 * s)]),
              fill=fillv)


def brazen_rush():
    """SP: a horned bronze war helm charging out of a wall of fire: every blow strikes twice."""
    c = bg((236, 120, 36), (44, 8, 4), cy=0.5, r=0.75)
    rays(c, 0.5, 0.5, 22, (255, 230, 160), alpha=100, width=0.045, phase=0.1)
    fl = shape(lambda d: [A.flame(d, 0.5, 1.0, 0.44, 0.90, 0.0), A.flame(d, 0.18, 0.98, 0.16, 0.56, -0.10),
                          A.flame(d, 0.82, 0.98, 0.16, 0.58, 0.10)])
    K.glow(c, fl, (255, 90, 20, 255), 24, 1.2)
    K.fill(c, scale(soften(fl, 3), 0.9), lin((255, 220, 100), (220, 60, 20), 270))
    horns = shape(lambda d: [stroke(d, [(0.5 + sx * 0.16, 0.46), (0.5 + sx * 0.30, 0.42), (0.5 + sx * 0.38, 0.32),
                                        (0.5 + sx * 0.40, 0.20), (0.5 + sx * 0.36, 0.10)], 0.11, 0.015)
                             for sx in (-1, 1)])
    K.glow(c, horns, (255, 230, 170, 255), 10, 1.2)
    K.shadow(c, horns, 4, 7, 6, 160)
    K.fill(c, soften(horns), lin((255, 250, 230), (190, 160, 120), 90))
    m = shape(lambda d: war_helm(d, 0.5, 0.52, 1.02))
    K.glow(c, m, (255, 200, 100, 255), 16, 1.3)
    K.shadow(c, m, 5, 9, 8, 170)
    K.fill(c, soften(m), lin((255, 226, 160), (160, 84, 34), 60))
    slit = shape(lambda d: [d.rounded_rectangle(pts([(0.35, 0.495), (0.65, 0.555)]), radius=0.02 * W, fill=255),
                            d.rectangle(pts([(0.475, 0.52), (0.525, 0.80)]), fill=255)])
    K.fill(c, soften(slit), (30, 10, 6, 255))
    eye = shape(lambda d: [d.ellipse(pts([(x - 0.03, 0.508), (x + 0.03, 0.542)]), fill=255) for x in (0.41, 0.59)])
    K.glow(c, eye, (255, 80, 30, 255), 8, 2.0)
    K.fill(c, soften(eye, 1), (255, 220, 120, 255))
    ridge = shape(lambda d: d.rectangle(pts([(0.488, 0.30), (0.512, 0.48)]), fill=255))
    K.fill(c, soften(ridge), (255, 246, 210, 210))
    sparkles(c, [(0.80, 0.70, 0.07), (0.22, 0.72, 0.05)], glowc=(255, 210, 120))
    return K.finish(c)


def impetus():
    """A fist driving forward, a stack of rising chevrons beside it: each blow builds the next."""
    c = bg((214, 120, 40), (40, 14, 4), cx=0.4, cy=0.55)
    streak_lines(c, [(0.02, 0.50, 0.24, 0.50), (0.04, 0.62, 0.22, 0.62), (0.06, 0.74, 0.26, 0.74)],
                 (255, 230, 180), 0.022, 170, 3)
    f = shape(lambda d: K.fist_front(d, 0.42, 0.62, 0.80))
    K.glow(c, f, (255, 190, 100, 255), 18, 1.3)
    K.shadow(c, f, 5, 8, 8, 150)
    K.fill(c, soften(f), lin((255, 232, 196), (222, 146, 92)))
    ln = shape(lambda d: K.fist_lines(d, 0.42, 0.62, 0.80))
    K.fill(c, scale(soften(ln, 1.5), 0.7), (120, 60, 36, 255))
    for i, (y, s, a) in enumerate(((0.62, 0.11, 0.55), (0.45, 0.13, 0.8), (0.26, 0.15, 1.0))):
        ch = shape(lambda d, y=y, s=s: stroke(d, [(0.76 - s, y + s * 0.6), (0.76, y), (0.76 + s, y + s * 0.6)], 0.05))
        K.glow(c, ch, (255, 220, 120, 255), 10, 1.2 * a)
        K.fill(c, scale(soften(ch), a), (255, 250, 220, 255))
    return K.finish(c)


def lotus_figure(d, cx, cy, s, fillv=255):
    """A monk sitting cross-legged in meditation; (cx, cy) the chest."""
    d.ellipse(pts([(cx - 0.075 * s, cy - 0.30 * s), (cx + 0.075 * s, cy - 0.14 * s)]), fill=fillv)
    d.polygon(pts([(cx - 0.06 * s, cy - 0.15 * s), (cx + 0.06 * s, cy - 0.15 * s), (cx + 0.17 * s, cy - 0.08 * s),
                   (cx + 0.14 * s, cy + 0.22 * s), (cx - 0.14 * s, cy + 0.22 * s), (cx - 0.17 * s, cy - 0.08 * s)]),
              fill=fillv)
    d.polygon(pts([(cx - 0.17 * s, cy - 0.08 * s), (cx - 0.25 * s, cy + 0.12 * s), (cx - 0.06 * s, cy + 0.24 * s),
                   (cx - 0.10 * s, cy + 0.14 * s)]), fill=fillv)
    d.polygon(pts([(cx + 0.17 * s, cy - 0.08 * s), (cx + 0.25 * s, cy + 0.12 * s), (cx + 0.06 * s, cy + 0.24 * s),
                   (cx + 0.10 * s, cy + 0.14 * s)]), fill=fillv)
    d.ellipse(pts([(cx - 0.34 * s, cy + 0.16 * s), (cx + 0.34 * s, cy + 0.34 * s)]), fill=fillv)


def inner_strength():
    """SP: a monk in meditation, a towering golden aura and a blazing heart within (max HP soars)."""
    c = bg((120, 30, 24), (16, 2, 2), cy=0.6)
    rays(c, 0.5, 0.56, 18, (255, 220, 140), alpha=110, width=0.05)
    aura = shape(lambda d: [A.flame(d, 0.5, 0.94, 0.40, 0.90, 0.0), A.flame(d, 0.24, 0.92, 0.16, 0.56, -0.08),
                            A.flame(d, 0.76, 0.92, 0.16, 0.58, 0.08)])
    K.glow(c, aura, (255, 170, 40, 255), 28, 1.5)
    K.fill(c, soften(aura, 4), lin((255, 250, 200), (250, 130, 20), 270))
    inner = shape(lambda d: A.flame(d, 0.5, 0.92, 0.26, 0.66, 0.0))
    K.fill(c, scale(soften(inner, 6), 0.6), (255, 252, 220, 255))
    fig = shape(lambda d: lotus_figure(d, 0.5, 0.54, 1.15))
    K.glow(c, fig, (255, 250, 210, 255), 8, 1.6)
    K.fill(c, soften(fig), lin((80, 30, 20), (36, 10, 8)))
    h = shape(lambda d: B.heart(d, 0.5, 0.55, 0.20))
    lit(c, h, (255, 80, 60), rad((255, 220, 200), (240, 40, 40), 0.48, 0.52, 0.09), 16, 2.2)
    sparkles(c, [(0.80, 0.24, 0.07), (0.22, 0.30, 0.05)], glowc=(255, 210, 120))
    return K.finish(c)


# ---- WHM -------------------------------------------------------------------------------------------------------------
def feather(d, x0, y0, x1, y1, w, bend=0.06):
    """A feather from the quill end (x0, y0) to the tip (x1, y1), the vane notched once on each side."""
    L, f = C.frame(x0, y0, x1, y1)
    top, bot = [], []
    for i in range(41):
        t = i / 40
        b = bend * math.sin(math.pi * t)
        hw = w * (math.sin(math.pi * min(1.0, (t - 0.12) / 0.88)) ** 0.55 if t > 0.12 else 0.0)
        nt = 0.45 if abs(t - 0.55) < 0.03 else 1.0
        nb = 0.45 if abs(t - 0.38) < 0.03 else 1.0
        top.append(f(L * t, b - hw * nt))
        bot.append(f(L * t, b + hw * nb))
    d.polygon(pts(top + bot[::-1]), fill=255)


def divine_caress():
    """An open hand, a white feather settling above it: the next cure of an ailment wards against it."""
    c = bg((214, 140, 190), (44, 12, 40), cy=0.42)
    motes(c, 51, 16, (0.15, 0.12, 0.85, 0.7), (0.007, 0.016), (255, 240, 250), (255, 180, 230))
    h = shape(lambda d: hand(d, 0.52, 0.72, 0.78))
    K.glow(c, h, (255, 230, 245, 255), 18, 1.4)
    K.shadow(c, h, 4, 7, 7, 120)
    K.fill(c, soften(h), lin((255, 246, 240), (226, 186, 186)))
    fe = shape(lambda d: feather(d, 0.22, 0.46, 0.82, 0.14, 0.075, -0.05))
    K.glow(c, fe, (255, 255, 255, 255), 14, 1.6)
    K.shadow(c, fe, 3, 6, 6, 110)
    K.fill(c, soften(fe), lin((255, 255, 255), (226, 220, 246), 0))
    q = shape(lambda d: stroke(d, [C.frame(0.22, 0.46, 0.82, 0.14)[1](C.frame(0.22, 0.46, 0.82, 0.14)[0] * t,
                                                                      -0.05 * math.sin(math.pi * t))
                                   for t in (i / 20 for i in range(21))], 0.014, 0.004))
    K.fill(c, soften(q), (180, 140, 190, 230))
    sparkles(c, [(0.80, 0.34, 0.06)], glowc=(255, 200, 240))
    return K.finish(c)


def sacrosanctity():
    """A holy seal of interlaced light around a white cross: magic defense for the whole party."""
    c = bg((60, 110, 210), (6, 10, 36), cy=0.5)
    rays(c, 0.5, 0.5, 12, (200, 230, 255), alpha=70, width=0.06)
    seal = union(ring(0.5, 0.5, 0.36, 0.022), ring(0.5, 0.5, 0.29, 0.012),
                 shape(lambda d: [d.line(pts(D.arc_path(0.5, 0.5, 0.36, 0.36, a, a + 360, 3)), fill=255,
                                         width=int(0.016 * W)) for a in (-90, 90)]))
    K.glow(c, seal, (140, 210, 255, 255), 12, 1.4)
    K.fill(c, soften(seal), (220, 240, 255, 255))
    cross = shape(lambda d: [d.rounded_rectangle(pts([(0.445, 0.27), (0.555, 0.73)]), radius=0.03 * W, fill=255),
                             d.rounded_rectangle(pts([(0.30, 0.40), (0.70, 0.51)]), radius=0.03 * W, fill=255)])
    lit(c, cross, (220, 240, 255), lin((255, 255, 255), (190, 220, 255)), 22, 1.6, sh=True)
    sparkles(c, [(0.80, 0.20, 0.06), (0.20, 0.80, 0.05)], glowc=(180, 220, 255))
    return K.finish(c)


def sanctuary():
    """SP (Asylum): a cathedral window blazing with holy light, rays pouring out over the party."""
    c = bg((236, 196, 110), (60, 34, 12), cy=0.44)
    rays(c, 0.5, 0.48, 18, (255, 252, 230), alpha=140, width=0.055, length=0.8)

    def arch(d, cx, top, w, bottom, fillv=255):
        q = [(cx - w, bottom), (cx - w, top + w * 1.1)]
        for i in range(21):
            t = i / 20
            a = math.radians(180 - 60 * t)
            q.append((cx + w + math.cos(a) * 2 * w, top + w * 1.1 - math.sin(a) * w * 1.7))
        for i in range(21):
            t = i / 20
            a = math.radians(60 - 60 * t)
            q.append((cx - w + math.cos(a) * 2 * w, top + w * 1.1 - math.sin(a) * w * 1.7))
        q.append((cx + w, bottom))
        d.polygon(pts(q), fill=fillv)
    frame_m = shape(lambda d: arch(d, 0.5, 0.12, 0.25, 0.86))
    win = shape(lambda d: arch(d, 0.5, 0.18, 0.19, 0.84))
    K.glow(c, frame_m, (255, 240, 180, 255), 26, 1.4)
    K.shadow(c, frame_m, 4, 8, 8, 150)
    K.fill(c, soften(frame_m), lin((200, 150, 80), (110, 70, 34)))
    K.fill(c, soften(win), rad((255, 255, 250), (255, 222, 140), 0.5, 0.5, 0.42))
    mull = inter(win, shape(lambda d: [d.line(pts([(0.5, 0.2), (0.5, 0.86)]), fill=255, width=int(0.014 * W)),
                                       d.line(pts([(0.3, 0.52), (0.7, 0.52)]), fill=255, width=int(0.014 * W)),
                                       d.ellipse(pts([(0.43, 0.30), (0.57, 0.44)]), outline=255,
                                                 width=int(0.012 * W))]))
    K.fill(c, soften(mull), (200, 150, 70, 200))
    steps = shape(lambda d: [d.rectangle(pts([(0.18, 0.84), (0.82, 0.88)]), fill=255),
                             d.rectangle(pts([(0.12, 0.88), (0.88, 0.94)]), fill=255)])
    K.fill(c, soften(steps), lin((240, 220, 180), (150, 110, 60)))
    sparkles(c, [(0.5, 0.37, 0.10), (0.18, 0.22, 0.05), (0.82, 0.22, 0.05)], glowc=(255, 236, 160))
    return K.finish(c)


# ---- BLM -------------------------------------------------------------------------------------------------------------
def enmity_douse():
    """Water pouring down on a red flame of hatred, which dies to a wisp of smoke: enmity to nothing."""
    c = bg((40, 70, 160), (4, 6, 26), cy=0.45)
    smoke = shape(lambda d: stroke(d, [(0.50, 0.58), (0.44, 0.48), (0.52, 0.38), (0.46, 0.28), (0.52, 0.18)], 0.07,
                                   0.02))
    K.fill(c, scale(soften(smoke, 6), 0.7), (170, 170, 190, 255))
    fl = shape(lambda d: A.flame(d, 0.5, 0.86, 0.17, 0.30, 0.0))
    lit(c, fl, (255, 60, 40), lin((255, 170, 80), (200, 30, 30), 270), 18, 1.2)
    base = shape(lambda d: d.ellipse(pts([(0.28, 0.82), (0.72, 0.90)]), fill=255))
    K.fill(c, soften(base, 3), (80, 30, 30, 200))
    drops = union(*[poly(D.drop_pts(x, y, y + 0.17, 0.06)) for x, y in ((0.30, 0.20), (0.62, 0.10), (0.72, 0.42),
                                                                      (0.40, 0.48))])
    lit(c, drops, (120, 200, 255), rad((240, 252, 255), (60, 150, 250), 0.5, 0.3, 0.5), 12, 1.5, sh=True)
    return K.finish(c)


def manawell():
    """A stone well brimming with glowing blue mana: the next spell draws on it instead of MP."""
    c = bg((70, 50, 170), (8, 4, 28), cy=0.45)
    col_m = poly([(0.30, 0.60), (0.70, 0.60), (0.62, 0.06), (0.38, 0.06)])
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(18)), 0.55), (120, 200, 255, 255))
    motes(c, 61, 16, (0.28, 0.08, 0.72, 0.56), (0.008, 0.018), (220, 245, 255), (120, 200, 255))
    body = shape(lambda d: [d.rectangle(pts([(0.20, 0.60), (0.80, 0.86)]), fill=255),
                            d.ellipse(pts([(0.20, 0.79), (0.80, 0.93)]), fill=255)])
    K.shadow(c, body, 4, 8, 8, 150)
    K.fill(c, soften(body), lin((150, 140, 150), (70, 60, 80), 0))
    bricks = inter(body, shape(lambda d: [d.line(pts([(0.2, y), (0.8, y)]), fill=255, width=int(0.01 * W))
                                          for y in (0.70, 0.79)]
                               + [d.line(pts([(x, y0), (x, y0 + 0.09)]), fill=255, width=int(0.01 * W))
                                  for y0, xs in ((0.61, (0.35, 0.55, 0.72)), (0.70, (0.27, 0.45, 0.65)),
                                                 (0.79, (0.36, 0.56, 0.73))) for x in xs]))
    K.fill(c, soften(bricks), (40, 30, 50, 200))
    rim = ell(0.17, 0.52, 0.83, 0.68)
    K.fill(c, soften(rim), lin((210, 200, 210), (120, 110, 130)))
    water = ell(0.23, 0.555, 0.77, 0.645)
    lit(c, water, (120, 220, 255), rad((240, 255, 255), (60, 140, 255), 0.5, 0.6, 0.28), 18, 1.8)
    sparkles(c, [(0.5, 0.30, 0.11), (0.70, 0.16, 0.05)], glowc=(150, 210, 255))
    return K.finish(c)


def subtle_sorcery():
    """SP: a black mage under his pointed hat, only his yellow eyes showing: spells cast without a ripple of
    enmity."""
    c = bg((96, 44, 150), (8, 2, 18), cy=0.42)
    motes(c, 71, 22, (0.08, 0.1, 0.92, 0.92), (0.006, 0.014), (230, 200, 255), (170, 110, 255), 180)
    sw = shape(lambda d: [stroke(d, D.arc_path(0.5, 0.62, 0.40, 0.30, a, a + 110), 0.01, 0.04)
                          for a in (200, 20)])
    K.fill(c, scale(soften(sw, 3), 0.7), (200, 160, 255, 255))
    hat = shape(lambda d: [d.polygon(pts([(0.26, 0.47), (0.44, 0.20), (0.52, 0.06), (0.64, 0.02), (0.60, 0.10),
                                          (0.58, 0.22), (0.72, 0.47)]), fill=255),
                           d.ellipse(pts([(0.10, 0.42), (0.90, 0.56)]), fill=255)])
    robe = shape(lambda d: d.polygon(pts([(0.30, 0.50), (0.70, 0.50), (0.84, 0.96), (0.16, 0.96)]), fill=255))
    K.glow(c, union(hat, robe), (200, 140, 255, 255), 14, 1.3)
    K.fill(c, soften(robe), lin((60, 60, 110), (20, 20, 40)))
    face = ell(0.33, 0.49, 0.67, 0.73)
    K.fill(c, soften(face, 3), (6, 4, 10, 255))
    K.fill(c, soften(hat), lin((90, 76, 140), (30, 24, 50)))
    band = inter(hat, shape(lambda d: d.polygon(pts([(0.27, 0.40), (0.71, 0.40), (0.72, 0.45), (0.26, 0.45)]),
                                                fill=255)))
    K.fill(c, soften(band), (190, 140, 80, 255))
    e = shape(lambda d: [d.ellipse(pts([(x - 0.045, 0.585), (x + 0.045, 0.635)]), fill=255) for x in (0.42, 0.58)])
    K.glow(c, e, (255, 220, 80, 255), 10, 2.0)
    K.fill(c, soften(e, 1), (255, 240, 140, 255))
    return K.finish(c)


def cascade():
    """A three-tiered fountain overflowing with golden TP: the cascade pours into the next spell."""
    c = bg((30, 110, 170), (4, 14, 30), cy=0.55)
    rays(c, 0.5, 0.30, 12, (200, 240, 255), alpha=60)
    tiers = [(0.5, 0.26, 0.11), (0.5, 0.48, 0.20), (0.5, 0.74, 0.32)]
    for cx, y, w in tiers[::-1]:
        flow = shape(lambda d, y=y, w=w: [stroke(d, [(0.5 + sx * w * 0.95, y + 0.01), (0.5 + sx * (w + 0.03), y + 0.06),
                                                     (0.5 + sx * (w + 0.04), y + 0.20)], 0.035, 0.05)
                                          for sx in (-1, 1)] if y < 0.7 else None)
        K.glow(c, flow, (255, 200, 80, 255), 8, 1.2)
        K.fill(c, soften(flow), lin((255, 250, 200), (255, 170, 40)))
    stem = shape(lambda d: d.rectangle(pts([(0.47, 0.26), (0.53, 0.80)]), fill=255))
    K.fill(c, soften(stem), lin((200, 190, 210), (90, 84, 110), 0))
    for cx, y, w in tiers:
        bowl = shape(lambda d, y=y, w=w: d.chord(pts([(0.5 - w, y - w * 0.45), (0.5 + w, y + w * 0.45)]), 0, 180,
                                                 fill=255))
        K.shadow(c, bowl, 3, 6, 6, 140)
        K.fill(c, soften(bowl), lin((220, 214, 230), (110, 100, 130), 90))
        pool = ell(0.5 - w * 0.92, y - w * 0.14, 0.5 + w * 0.92, y + w * 0.14)
        lit(c, pool, (255, 210, 90), rad((255, 255, 230), (255, 180, 40), 0.5, y, w), 10, 1.4)
    jet = shape(lambda d: stroke(d, [(0.5, 0.25), (0.5, 0.10)], 0.04, 0.012))
    lit(c, jet, (255, 220, 120), (255, 250, 210), 8, 1.4)
    sparkles(c, [(0.5, 0.09, 0.08), (0.20, 0.30, 0.05), (0.80, 0.30, 0.05)], glowc=(255, 220, 120))
    return K.finish(c)


def saboteur():
    """A violet down-arrow of enfeeblement cracked open by a red mage's rapier: enfeebles hit far harder."""
    c = bg((120, 36, 120), (20, 4, 22), cy=0.45)
    arr = poly([(0.40, 0.14), (0.60, 0.14), (0.60, 0.48), (0.76, 0.48), (0.50, 0.86), (0.24, 0.48), (0.40, 0.48)])
    lit(c, arr, (230, 120, 255), lin((250, 210, 255), (150, 60, 210)), 20, 1.4, sh=True)
    crack = shape(lambda d: stroke(d, [(0.44, 0.20), (0.52, 0.34), (0.46, 0.46), (0.55, 0.60), (0.50, 0.74)], 0.022,
                                   0.008))
    K.fill(c, soften(inter(crack, arr)), (70, 10, 90, 255))
    r = shape(lambda d: rapier(d, 0.16, 0.86, 0.86, 0.16))
    K.glow(c, r, (255, 120, 120, 255), 12, 1.2)
    K.shadow(c, r, 4, 7, 6, 150)
    K.fill(c, soften(r), metal_paint(angle=45))
    hilt = shape(lambda d: [d.ellipse(pts([(0.215, 0.70), (0.315, 0.80)]), fill=255)])
    K.fill(c, soften(inter(hilt, r)), lin((255, 210, 120), (190, 110, 40)))
    sparkles(c, [(0.52, 0.48, 0.09)], glowc=(255, 160, 220))
    return K.finish(c)


def spontaneity():
    """A clock face whose hand is a lightning bolt: the next spell is cast in an instant."""
    c = bg((210, 120, 40), (40, 14, 4), cy=0.5)
    streak_lines(c, [(0.10, 0.30, 0.10, 0.70), (0.90, 0.30, 0.90, 0.70)], (255, 230, 170), 0.02, 120, 3)
    face = disc(0.5, 0.5, 0.33)
    K.glow(c, face, (255, 220, 140, 255), 18, 1.2)
    K.shadow(c, face, 4, 7, 7, 150)
    K.fill(c, soften(face), gold_paint())
    inner = disc(0.5, 0.5, 0.28)
    K.fill(c, soften(inner), rad((255, 252, 240), (226, 210, 180), 0.45, 0.42, 0.3))
    ticks = shape(lambda d: [d.line(pts([(0.5 + math.cos(a) * 0.22, 0.5 + math.sin(a) * 0.22),
                                         (0.5 + math.cos(a) * 0.26, 0.5 + math.sin(a) * 0.26)]), fill=255,
                                    width=int(0.018 * W)) for a in [math.pi * i / 6 for i in range(12)]])
    K.fill(c, soften(ticks), (120, 70, 40, 255))
    bolt = poly([(0.60, 0.16), (0.40, 0.50), (0.52, 0.50), (0.42, 0.84), (0.66, 0.44), (0.54, 0.44), (0.66, 0.16)])
    lit(c, bolt, (255, 80, 60), lin((255, 120, 90), (190, 20, 40)), 12, 1.5, sh=True)
    return K.finish(c)


def stymie():
    """SP: a red mage's rapier driven through the heart of a violet seal: the next enfeeble cannot miss."""
    c = bg((190, 30, 44), (30, 2, 8), cy=0.55)
    rays(c, 0.5, 0.60, 16, (255, 180, 200), alpha=100, width=0.05)
    seal = union(ring(0.5, 0.62, 0.34, 0.02, 0.15), ring(0.5, 0.62, 0.24, 0.014, 0.105),
                 ring(0.5, 0.62, 0.13, 0.012, 0.057))
    runes_m = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * 0.29, 0.62 + math.sin(a) * 0.125 - 0.012),
                                              (0.5 + math.cos(a) * 0.29 + 0.012, 0.62 + math.sin(a) * 0.125),
                                              (0.5 + math.cos(a) * 0.29, 0.62 + math.sin(a) * 0.125 + 0.012),
                                              (0.5 + math.cos(a) * 0.29 - 0.012, 0.62 + math.sin(a) * 0.125)]),
                                         fill=255) for a in [math.pi * i / 5 for i in range(10)]])
    K.glow(c, seal, (230, 110, 255, 255), 12, 1.6)
    K.fill(c, soften(union(seal, runes_m)), (250, 210, 255, 255))
    flash = shape(lambda d: star(d, 0.5, 0.62, 0.20, 0.05, 6))
    lit(c, flash, (255, 200, 255), (255, 255, 255), 16, 1.6)
    r = shape(lambda d: rapier(d, 0.5, 0.04, 0.5, 0.64, 0.03))
    K.glow(c, r, (255, 230, 230, 255), 12, 1.3)
    K.shadow(c, r, 4, 7, 6, 160)
    K.fill(c, soften(r), metal_paint((255, 255, 255), (170, 176, 200), 0))
    hilt = shape(lambda d: [d.rectangle(pts([(0.38, 0.0), (0.62, 0.22)]), fill=255)])
    K.fill(c, soften(inter(hilt, r)), lin((255, 220, 130), (190, 110, 40)))
    plume = shape(lambda d: A.leaf(d, 0.52, 0.12, -0.35, 0.36, 0.06))
    lit(c, plume, (255, 255, 255), lin((255, 255, 255), (230, 220, 230), 0), 8, 1.2)
    return K.finish(c)


# ---- THF -------------------------------------------------------------------------------------------------------------
def conspirator():
    """Two hooded figures, heads together, their eyes glinting: a whispered plot lifts the party's aim."""
    c = bg((40, 110, 70), (4, 18, 10), cy=0.4)
    back = shape(lambda d: hood(d, 0.66, 0.40, 0.70))
    K.glow(c, back, (160, 255, 190, 255), 8, 1.2)
    K.fill(c, soften(back), lin((40, 70, 54), (14, 26, 20)))
    K.fill(c, soften(face_hole(0.66, 0.40, 0.70), 2), (4, 6, 6, 255))
    eyes(c, 0.66, 0.41, 0.70, (220, 255, 160), (150, 255, 120))
    front = shape(lambda d: hood(d, 0.38, 0.52, 0.85))
    K.glow(c, front, (170, 255, 200, 255), 12, 1.5)
    K.shadow(c, front, 5, 8, 8, 150)
    K.fill(c, soften(front), lin((70, 110, 84), (20, 36, 28)))
    K.fill(c, soften(face_hole(0.38, 0.52, 0.85), 2), (4, 6, 6, 255))
    eyes(c, 0.38, 0.53, 0.85, (255, 250, 170), (200, 255, 120))
    sparkles(c, [(0.84, 0.16, 0.06)], glowc=(180, 255, 200))
    return K.finish(c)


def bully():
    """A hulking shadow with burning red eyes looming over the viewer, fist raised: the target cowers."""
    c = bg((200, 100, 40), (36, 10, 4), cy=0.3)
    big = shape(lambda d: [d.ellipse(pts([(0.33, 0.16), (0.67, 0.52)]), fill=255),
                           d.polygon(pts([(0.0, 1.0), (0.04, 0.66), (0.22, 0.52), (0.40, 0.48), (0.60, 0.48),
                                          (0.78, 0.52), (0.96, 0.66), (1.0, 1.0)]), fill=255)])
    K.glow(c, big, (255, 190, 110, 255), 12, 1.5)
    K.fill(c, soften(big), lin((50, 26, 20), (12, 6, 6)))
    e = shape(lambda d: [d.polygon(pts([(0.5 + sx * 0.035, 0.37), (0.5 + sx * 0.13, 0.32), (0.5 + sx * 0.12, 0.38),
                                        (0.5 + sx * 0.05, 0.40)]), fill=255) for sx in (-1, 1)])
    K.glow(c, e, (255, 40, 30, 255), 12, 2.2)
    K.fill(c, soften(e, 1), (255, 120, 90, 255))
    f = shape(lambda d: K.fist_front(d, 0.74, 0.72, 0.62))
    K.glow(c, f, (255, 140, 80, 255), 10, 1.2)
    K.fill(c, soften(f), lin((90, 50, 40), (40, 20, 16)))
    ln = shape(lambda d: K.fist_lines(d, 0.74, 0.72, 0.62))
    K.fill(c, scale(soften(ln, 1.5), 0.8), (10, 4, 4, 255))
    return K.finish(c)


def larceny():
    """SP: a gloved hand snatching a glowing golden buff right off the foe."""
    c = bg((120, 60, 170), (16, 6, 28), cx=0.42, cy=0.38)
    streak_lines(c, [(0.62, 0.92, 0.98, 0.74), (0.72, 0.98, 1.02, 0.84), (0.56, 0.82, 0.92, 0.62)],
                 (240, 220, 255), 0.024, 160, 4)
    orb = disc(0.36, 0.33, 0.17)
    lit(c, orb, (255, 220, 100), rad((255, 255, 230), (240, 160, 30), 0.32, 0.28, 0.2), 28, 1.8)
    up = shape(lambda d: [arrowhead(d, 0.36, 0.19, -90, 0.10), d.rectangle(pts([(0.335, 0.23), (0.385, 0.44)]),
                                                                         fill=255)])
    K.fill(c, soften(up), (190, 110, 20, 255))
    h = rot(shape(lambda d: hand(d, 0.62, 0.66, 0.78)), 38, 0.62, 0.66)
    K.glow(c, h, (230, 200, 255, 255), 12, 1.4)
    K.shadow(c, h, 5, 8, 8, 150)
    K.fill(c, soften(h), lin((200, 170, 220), (100, 70, 130)))
    cuff = rot(shape(lambda d: d.rectangle(pts([(0.52, 0.86), (0.72, 0.98)]), fill=255)), 38, 0.62, 0.66)
    K.fill(c, soften(cuff), lin((90, 40, 60), (40, 16, 30)))
    sparkles(c, [(0.14, 0.26, 0.07), (0.20, 0.56, 0.05), (0.60, 0.14, 0.06)], glowc=(255, 220, 120))
    return K.finish(c)


def sepulcher():
    """A tombstone with a holy cross blazing on it: the undead are laid low."""
    c = bg((70, 100, 110), (6, 12, 16), cy=0.3)
    rays(c, 0.5, 0.05, 10, (230, 250, 255), alpha=110, width=0.07, length=1.0)
    stone = shape(lambda d: [d.rectangle(pts([(0.28, 0.40), (0.72, 0.86)]), fill=255),
                             d.ellipse(pts([(0.28, 0.18), (0.72, 0.62)]), fill=255)])
    K.shadow(c, stone, 5, 8, 8, 170)
    K.glow(c, stone, (200, 230, 255, 255), 10, 0.8)
    K.fill(c, soften(stone), lin((170, 176, 186), (80, 84, 96), 30))
    cross = shape(lambda d: [d.rectangle(pts([(0.465, 0.28), (0.535, 0.66)]), fill=255),
                             d.rectangle(pts([(0.38, 0.37), (0.62, 0.44)]), fill=255)])
    lit(c, cross, (255, 240, 170), lin((255, 255, 240), (255, 220, 120)), 14, 1.8)
    ground = shape(lambda d: d.ellipse(pts([(0.04, 0.80), (0.96, 1.04)]), fill=255))
    K.fill(c, soften(ground, 3), lin((40, 70, 50), (10, 20, 14)))
    wisp = shape(lambda d: stroke(d, [(0.80, 0.80), (0.84, 0.66), (0.78, 0.56), (0.84, 0.46)], 0.06, 0.01))
    K.fill(c, scale(soften(wisp, 4), 0.6), (190, 255, 220, 255))
    return K.finish(c)


def palisade():
    """A shield planted before a palisade of sharpened stakes: blocks come easy and hold enmity."""
    c = bg((80, 120, 170), (8, 14, 28), cy=0.4)
    stakes = shape(lambda d: [d.polygon(pts([(x - 0.055, 0.86), (x - 0.055, 0.30 + dy), (x, 0.16 + dy),
                                             (x + 0.055, 0.30 + dy), (x + 0.055, 0.86)]), fill=255)
                              for x, dy in ((0.14, 0.10), (0.27, 0.03), (0.40, 0.0), (0.60, 0.0), (0.73, 0.03),
                                            (0.86, 0.10))])
    K.shadow(c, stakes, 4, 6, 6, 150)
    K.fill(c, soften(stakes), lin((200, 150, 100), (100, 60, 34), 0))
    band = inter(stakes, shape(lambda d: d.rectangle(pts([(0, 0.62), (1, 0.66)]), fill=255)))
    K.fill(c, soften(band), (60, 40, 30, 255))
    sh = shape(lambda d: A.heater(d, 0.5, 0.36, 0.20, 0.52))
    K.glow(c, sh, (180, 220, 255, 255), 14, 1.2)
    K.shadow(c, sh, 5, 8, 8, 170)
    K.fill(c, soften(sh), metal_paint((240, 246, 255), (120, 130, 160)))
    inner = shape(lambda d: A.heater(d, 0.5, 0.41, 0.15, 0.42))
    K.fill(c, soften(inner), lin((60, 100, 190), (20, 30, 90)))
    cross = inter(inner, shape(lambda d: [d.rectangle(pts([(0.48, 0.41), (0.52, 0.84)]), fill=255),
                                          d.rectangle(pts([(0.35, 0.52), (0.65, 0.56)]), fill=255)]))
    K.fill(c, soften(cross), (240, 220, 150, 255))
    return K.finish(c)


def intervene():
    """SP: a shield slammed forward in a burst of light, the shockwave stripping the foe's attack away."""
    c = bg((230, 180, 70), (50, 26, 6), cx=0.55, cy=0.5)
    rays(c, 0.62, 0.5, 18, (255, 250, 220), alpha=130, width=0.05)
    boom = shape(lambda d: star(d, 0.70, 0.50, 0.30, 0.12, 9, -80))
    lit(c, boom, (255, 255, 220), rad((255, 255, 255), (255, 210, 110), 0.7, 0.5, 0.3), 24, 1.4)
    waves = shape(lambda d: [d.arc(pts([(0.70 - r, 0.5 - r), (0.70 + r, 0.5 + r)]), -50, 50, fill=255,
                                   width=int(0.03 * W)) for r in (0.18, 0.28)])
    K.glow(c, waves, (255, 255, 230, 255), 8, 1.4)
    K.fill(c, soften(waves), (255, 255, 250, 255))
    sh = rot(shape(lambda d: B.draw_shield(d, 0.42, 0.50, 1.05)), -12, 0.42, 0.5)
    K.glow(c, sh, (255, 230, 160, 255), 14, 1.2)
    K.shadow(c, sh, 6, 9, 8, 170)
    K.fill(c, soften(sh), metal_paint((250, 252, 255), (130, 140, 170)))
    inner = rot(shape(lambda d: B.draw_shield(d, 0.42, 0.50, 1.05, inset=0.18)), -12, 0.42, 0.5)
    K.fill(c, soften(inner), lin((70, 100, 200), (20, 30, 90)))
    cross = inter(inner, rot(shape(lambda d: [d.rectangle(pts([(0.40, 0.18), (0.44, 0.86)]), fill=255),
                                              d.rectangle(pts([(0.20, 0.36), (0.64, 0.40)]), fill=255)]), -12, 0.42,
                             0.5))
    K.fill(c, soften(cross), (255, 226, 140, 255))
    return K.finish(c)


def majesty():
    """A golden crown above a white cross: cures and protection spread to the whole party."""
    c = bg((110, 50, 160), (16, 4, 28), cy=0.45)
    rays(c, 0.5, 0.45, 14, (255, 230, 255), alpha=80)
    cross = shape(lambda d: [d.rounded_rectangle(pts([(0.455, 0.50), (0.545, 0.88)]), radius=0.02 * W, fill=255),
                             d.rounded_rectangle(pts([(0.34, 0.60), (0.66, 0.69)]), radius=0.02 * W, fill=255)])
    lit(c, cross, (255, 240, 255), lin((255, 255, 255), (220, 210, 240)), 18, 1.5, sh=True)
    crown = poly([(0.22, 0.48), (0.20, 0.20), (0.34, 0.32), (0.42, 0.14), (0.5, 0.28), (0.58, 0.14), (0.66, 0.32),
                  (0.80, 0.20), (0.78, 0.48)])
    lit(c, crown, (255, 220, 120), gold_paint(), 20, 1.4, sh=True)
    band = inter(crown, poly([(0, 0.40), (1, 0.40), (1, 0.48), (0, 0.48)]))
    K.fill(c, soften(band), (200, 120, 40, 255))
    gems = shape(lambda d: [d.ellipse(pts([(x - 0.025, 0.415), (x + 0.025, 0.465)]), fill=255)
                            for x in (0.34, 0.5, 0.66)])
    lit(c, gems, (255, 80, 120), (255, 60, 110), 6, 1.4)
    tips = shape(lambda d: [d.ellipse(pts([(x - 0.022, y - 0.022), (x + 0.022, y + 0.022)]), fill=255)
                            for x, y in ((0.20, 0.20), (0.42, 0.14), (0.58, 0.14), (0.80, 0.20))])
    lit(c, tips, (255, 255, 220), (255, 250, 220), 6, 1.5)
    return K.finish(c)


# ---- DRK -------------------------------------------------------------------------------------------------------------
def arcane_crest():
    """A dark iron crest bearing an arcane eye, split by a crimson slash: arcana are weakened."""
    c = bg((70, 46, 120), (8, 4, 18), cy=0.45)
    sh = poly(D.shield_pts(0.5, 0.16, 0.27, 0.70))
    K.glow(c, sh, (170, 120, 255, 255), 14, 1.2)
    K.shadow(c, sh, 5, 8, 8, 170)
    K.fill(c, soften(sh), lin((120, 110, 140), (40, 34, 56)))
    inner = poly(D.shield_pts(0.5, 0.21, 0.22, 0.60))
    K.fill(c, soften(inner), lin((110, 70, 170), (40, 20, 70)))
    sig = union(ring(0.5, 0.46, 0.13, 0.024),
                shape(lambda d: d.line(pts([(0.5, 0.31), (0.62, 0.53), (0.38, 0.53), (0.5, 0.31)]), fill=255,
                                       width=int(0.022 * W), joint='curve')))
    K.glow(c, sig, (210, 150, 255, 255), 14, 2.0)
    K.fill(c, soften(sig), (230, 200, 255, 255))
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.47, 0.05, 0.026))
    K.fill(c, soften(e), (255, 230, 120, 255))
    sl = poly([(0.20, 0.26), (0.23, 0.23), (0.80, 0.74), (0.76, 0.76)])
    lit(c, sl, (255, 30, 50), lin((255, 160, 160), (220, 20, 40), 45), 14, 1.6)
    return K.finish(c)


def scarlet_delirium():
    """A crimson whirlpool around a mad red eye: every wound taken feeds the dark knight's fury."""
    c = bg((180, 20, 40), (24, 0, 6), cy=0.5)
    sp = shape(lambda d: [stroke(d, [(0.5 + math.cos(math.radians(a0 + t * 6)) * (0.06 + t * 0.0062),
                                      0.5 + math.sin(math.radians(a0 + t * 6)) * (0.06 + t * 0.0062))
                                     for t in range(0, 61, 2)], 0.012, 0.07) for a0 in (0, 180)])
    K.glow(c, sp, (255, 40, 50, 255), 16, 1.3)
    K.fill(c, soften(sp), lin((255, 140, 140), (160, 10, 30)))
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.5, 0.17, 0.10))
    K.glow(c, e, (255, 60, 60, 255), 16, 1.6)
    K.shadow(c, e, 4, 6, 6, 150)
    K.fill(c, soften(e), (255, 236, 230, 255))
    iris = disc(0.5, 0.5, 0.085)
    K.fill(c, soften(inter(iris, e)), rad((255, 90, 70), (140, 0, 20), 0.5, 0.5, 0.09))
    pupil = ell(0.49, 0.43, 0.51, 0.57)
    K.fill(c, soften(inter(pupil, e), 1), (20, 0, 4, 255))
    motes(c, 91, 12, (0.12, 0.12, 0.88, 0.88), (0.007, 0.015), (255, 160, 150), (255, 40, 50))
    return K.finish(c)


def soul_enslavement():
    """SP: a wailing soul bound in black chains to the dark knight's scythe: every blow drains the foe's TP."""
    c = bg((90, 40, 130), (10, 2, 18), cy=0.5)
    sc = shape(lambda d: [stroke(d, D.arc_path(0.64, 0.66, 0.50, 0.46, 200, 268), 0.012, 0.09),
                          d.rectangle(pts([(0.60, 0.18), (0.66, 0.98)]), fill=255)])
    K.glow(c, sc, (190, 110, 255, 255), 12, 1.2)
    K.fill(c, soften(sc), lin((120, 110, 140), (30, 26, 40), 0))
    soul_pts = [(0.40, 0.18), (0.54, 0.24), (0.58, 0.42), (0.54, 0.60), (0.46, 0.72), (0.40, 0.86), (0.34, 0.70),
                (0.28, 0.56), (0.24, 0.40), (0.28, 0.24)]
    soul = shape(lambda d: [d.polygon(pts(soul_pts), fill=255), d.ellipse(pts([(0.24, 0.16), (0.58, 0.48)]),
                                                                          fill=255)])
    soul = soul.filter(ImageFilter.GaussianBlur(5)).point(lambda v: 255 if v > 120 else int(v * 2))
    K.glow(c, soul, (120, 255, 210, 255), 22, 1.4)
    K.fill(c, soften(soul, 2), rad((240, 255, 250), (80, 210, 180), 0.40, 0.32, 0.38))
    face = shape(lambda d: [d.ellipse(pts([(0.31, 0.28), (0.37, 0.36)]), fill=255),
                            d.ellipse(pts([(0.43, 0.28), (0.49, 0.36)]), fill=255),
                            d.ellipse(pts([(0.36, 0.40), (0.44, 0.50)]), fill=255)])
    K.fill(c, soften(face, 1.5), (20, 40, 50, 255))
    ch = shape(lambda d: [chain(d, 0.10, 0.36, 0.92, 0.58, 9, 0.04, 0.016),
                          chain(d, 0.14, 0.74, 0.90, 0.30, 9, 0.04, 0.016)])
    K.shadow(c, ch, 3, 5, 4, 170)
    K.fill(c, soften(ch), lin((150, 140, 170), (50, 44, 64)))
    return K.finish(c)


def consume_mana():
    """A dark greatsword drinking in a spiral of blue mana: all MP poured into the next strike."""
    c = bg((40, 50, 140), (4, 4, 22), cy=0.5)
    sp = shape(lambda d: [stroke(d, [(0.5 + math.cos(math.radians(a0 + t * 7)) * (0.40 - t * 0.0058),
                                      0.58 + math.sin(math.radians(a0 + t * 7)) * (0.18 - t * 0.0026))
                                     for t in range(0, 61, 2)], 0.05, 0.012) for a0 in (20, 200)])
    K.glow(c, sp, (90, 170, 255, 255), 14, 1.4)
    K.fill(c, soften(sp), lin((210, 240, 255), (80, 140, 255)))
    s = shape(lambda d: D.sword(d, 0.5, 0.06, 0.94, 0.075))
    K.glow(c, s, (120, 140, 255, 255), 16, 1.3)
    K.shadow(c, s, 5, 8, 8, 170)
    K.fill(c, soften(s), lin((90, 90, 120), (24, 22, 36), 0))
    edge = minus(s, shape(lambda d: D.sword(d, 0.5, 0.10, 0.94, 0.05)))
    edge = inter(edge, poly([(0, 0), (1, 0), (1, 0.72), (0, 0.72)]))
    K.fill(c, soften(edge), (160, 200, 255, 255))
    orbs = union(disc(0.20, 0.30, 0.05), disc(0.82, 0.38, 0.04), disc(0.28, 0.80, 0.035))
    lit(c, orbs, (120, 190, 255), rad((240, 255, 255), (70, 140, 255), 0.5, 0.5, 0.5), 10, 1.6)
    return K.finish(c)


# ---- BST -------------------------------------------------------------------------------------------------------------
def unleash():
    """SP: three blazing claw gashes, the beast's chain snapped apart: its abilities pour out without pause."""
    c = bg((200, 70, 24), (30, 4, 2), cy=0.5)
    rays(c, 0.5, 0.5, 16, (255, 200, 130), alpha=90)
    for (x0, y0, x1, y1) in ((0.04, 0.44, 0.34, 0.10), (0.96, 0.58, 0.68, 0.92)):
        ch = shape(lambda d, x0=x0, y0=y0, x1=x1, y1=y1: chain(d, x0, y0, x1, y1, 4, 0.05, 0.02))
        K.shadow(c, ch, 3, 5, 4, 160)
        K.fill(c, soften(ch), lin((210, 200, 190), (90, 80, 80)))
    gash = shape(lambda d: [stroke(d, [(0.30 + dx, 0.18 + dx * 0.25), (0.46 + dx, 0.48 + dx * 0.2),
                                       (0.54 + dx, 0.82 + dx * 0.1)], 0.03, 0.008)
                            for dx in (-0.12, 0.0, 0.12)])
    gash = union(gash, shape(lambda d: [stroke(d, [(0.30 + dx, 0.18 + dx * 0.25), (0.40 + dx, 0.34 + dx * 0.2),
                                                   (0.48 + dx, 0.56 + dx * 0.2)], 0.016, 0.10)
                                        for dx in (-0.12, 0.0, 0.12)]))
    K.glow(c, gash, (255, 150, 40, 255), 22, 2.0)
    K.fill(c, soften(gash), lin((255, 255, 250), (255, 220, 120)))
    sparkles(c, [(0.80, 0.22, 0.09), (0.20, 0.78, 0.06)], glowc=(255, 200, 120))
    return K.finish(c)


def bestial_loyalty():
    """A paw print inside a heart: the beast answers the call, no jug needed."""
    c = bg((70, 160, 90), (6, 26, 12), cy=0.45)
    rays(c, 0.5, 0.48, 12, (220, 255, 210), alpha=70)
    h = shape(lambda d: B.heart(d, 0.5, 0.52, 1.0))
    lit(c, h, (255, 120, 140), rad((255, 170, 180), (200, 30, 70), 0.4, 0.38, 0.45), 20, 1.4, sh=True)
    pw = shape(lambda d: B.paw(d, 0.5, 0.52, 0.62))
    K.shadow(c, pw, 3, 5, 5, 120)
    K.fill(c, soften(pw), lin((255, 250, 240), (240, 214, 200)))
    sparkles(c, [(0.80, 0.18, 0.06)], glowc=(255, 220, 230))
    return K.finish(c)


# ---- BRD -------------------------------------------------------------------------------------------------------------
def tenuto():
    """A note under a broad tenuto bar, its sound held long: the next song lasts and cannot be overwritten."""
    c = bg((40, 140, 150), (4, 22, 28), cy=0.5)
    streak_lines(c, [(0.56, 0.62, 0.92, 0.62), (0.56, 0.72, 0.96, 0.72), (0.56, 0.82, 0.90, 0.82)],
                 (200, 255, 250), 0.02, 130, 3)
    n = shape(lambda d: B.note(d, 0.40, 0.78, 0.82, 1))
    lit(c, n, (180, 255, 240), lin((255, 255, 255), (190, 240, 235)), 20, 1.4, sh=True)
    bar = shape(lambda d: d.rounded_rectangle(pts([(0.24, 0.13), (0.70, 0.21)]), radius=0.03 * W, fill=255))
    lit(c, bar, (255, 220, 110), gold_paint(), 14, 1.6, sh=True)
    return K.finish(c)


def marcato():
    """A note struck under a bold marcato wedge, sparks flying: the next song rings out far stronger."""
    c = bg((180, 50, 130), (30, 4, 22), cy=0.5)
    rays(c, 0.5, 0.18, 12, (255, 200, 240), alpha=80)
    n = shape(lambda d: B.note(d, 0.40, 0.80, 0.80, 1))
    lit(c, n, (255, 170, 230), lin((255, 255, 255), (250, 210, 236)), 20, 1.4, sh=True)
    wedge = poly([(0.30, 0.30), (0.47, 0.06), (0.64, 0.30), (0.55, 0.30), (0.47, 0.18), (0.39, 0.30)])
    lit(c, wedge, (255, 220, 110), gold_paint(), 14, 1.7, sh=True)
    sparkles(c, [(0.74, 0.14, 0.07), (0.20, 0.18, 0.05)], glowc=(255, 210, 240))
    return K.finish(c)


def clarion_call():
    """SP: a golden clarion with a crimson banner, its blast scattering notes: one more song can be held."""
    c = bg((40, 60, 170), (4, 6, 30), cx=0.6, cy=0.42)
    rays(c, 0.78, 0.40, 16, (220, 230, 255), alpha=90, width=0.06)
    waves = shape(lambda d: [d.arc(pts([(0.70 - r, 0.38 - r), (0.70 + r, 0.38 + r)]), -60, 40, fill=255,
                                   width=int(0.028 * W)) for r in (0.16, 0.25)])
    lit(c, waves, (255, 240, 180), (255, 250, 230), 10, 1.4)

    def trumpet(d):
        d.polygon(pts([(0.10, 0.475), (0.56, 0.47), (0.56, 0.53), (0.10, 0.525)]), fill=255)
        q = [(0.54, 0.47)]
        for i in range(13):
            t = i / 12
            q.append((0.54 + 0.32 * t, 0.47 - 0.20 * t ** 2.2))
        for i in range(12, -1, -1):
            t = i / 12
            q.append((0.54 + 0.32 * t, 0.53 + 0.20 * t ** 2.2))
        d.polygon(pts(q), fill=255)
        d.rounded_rectangle(pts([(0.22, 0.52), (0.50, 0.64)]), radius=0.05 * W, outline=255, width=int(0.022 * W))
        for x in (0.30, 0.36, 0.42):
            d.rectangle(pts([(x - 0.014, 0.40), (x + 0.014, 0.48)]), fill=255)
        d.ellipse(pts([(0.06, 0.45), (0.12, 0.55)]), fill=255)
    tr = rot(shape(trumpet), 14, 0.5, 0.5)
    banner = rot(poly([(0.24, 0.55), (0.48, 0.55), (0.48, 0.84), (0.36, 0.76), (0.24, 0.84)]), 14, 0.5, 0.5)
    K.shadow(c, banner, 4, 6, 6, 140)
    K.fill(c, soften(banner), lin((230, 50, 60), (130, 10, 30)))
    emb = rot(shape(lambda d: star(d, 0.36, 0.66, 0.05, 0.02, 5)), 14, 0.5, 0.5)
    K.fill(c, soften(emb), (255, 220, 120, 255))
    K.glow(c, tr, (255, 210, 110, 255), 16, 1.4)
    K.shadow(c, tr, 5, 8, 8, 160)
    K.fill(c, soften(tr), gold_paint(80))
    bell = rot(ell(0.83, 0.28, 0.89, 0.72), 14, 0.5, 0.5)
    K.fill(c, soften(bell, 2), (150, 90, 30, 255))
    nt = shape(lambda d: [B.note(d, 0.72, 0.22, 0.30, 1, 10), B.note(d, 0.84, 0.86, 0.26, 1, -10)])
    lit(c, nt, (255, 240, 200), (255, 252, 236), 8, 1.4)
    return K.finish(c)


# ---- RNG -------------------------------------------------------------------------------------------------------------
def bounty_shot():
    """An arrow punched through a gold coin: treasure falls more often."""
    c = bg((100, 140, 50), (12, 22, 6), cy=0.45)
    coin = disc(0.5, 0.52, 0.27)
    K.glow(c, coin, (255, 220, 120, 255), 22, 1.5)
    K.shadow(c, coin, 5, 8, 8, 160)
    K.fill(c, soften(coin), gold_paint())
    K.fill(c, soften(ring(0.5, 0.52, 0.21, 0.018)), (180, 110, 30, 255))
    emb = shape(lambda d: star(d, 0.5, 0.53, 0.13, 0.055, 5))
    K.fill(c, soften(emb), lin((255, 250, 210), (220, 160, 60)))
    ar = shape(lambda d: C.arrow(d, 0.08, 0.90, 0.88, 0.12, 0.04, 0.16, 0.085))
    hole = disc(0.5, 0.52, 0.0)
    K.glow(c, ar, (255, 255, 230, 255), 10, 1.2)
    K.shadow(c, ar, 4, 7, 6, 160)
    K.fill(c, soften(ar), lin((250, 246, 236), (170, 140, 110), 45))
    sparkles(c, [(0.22, 0.24, 0.08), (0.80, 0.80, 0.06)], glowc=(255, 230, 140))
    return K.finish(c)


def decoy_shot():
    """A painted wooden decoy duck with a target on it: the foe's anger goes to the decoy, not the ranger."""
    c = bg((50, 140, 170), (4, 22, 30), cy=0.45)
    water = shape(lambda d: [d.arc(pts([(x - 0.10, 0.80), (x + 0.10, 0.86)]), 0, 180, fill=255,
                                   width=int(0.014 * W)) for x in (0.24, 0.50, 0.76)])
    K.fill(c, scale(soften(water), 0.7), (200, 240, 255, 255))
    duck = shape(lambda d: [d.ellipse(pts([(0.16, 0.50), (0.74, 0.82)]), fill=255),
                            d.polygon(pts([(0.18, 0.62), (0.08, 0.50), (0.26, 0.56)]), fill=255),
                            d.ellipse(pts([(0.54, 0.28), (0.76, 0.50)]), fill=255),
                            d.rectangle(pts([(0.58, 0.40), (0.70, 0.58)]), fill=255),
                            d.polygon(pts([(0.74, 0.36), (0.88, 0.40), (0.74, 0.44)]), fill=255)])
    K.glow(c, duck, (220, 255, 240, 255), 12, 1.2)
    K.shadow(c, duck, 5, 8, 8, 160)
    K.fill(c, soften(duck), lin((200, 140, 80), (110, 66, 34)))
    head = inter(duck, ell(0.54, 0.28, 0.76, 0.50))
    K.fill(c, soften(head), lin((70, 150, 90), (30, 80, 50)))
    K.fill(c, soften(disc(0.68, 0.37, 0.018)), (20, 10, 10, 255))
    tgt = union(ring(0.42, 0.66, 0.11, 0.022), disc(0.42, 0.66, 0.035))
    lit(c, tgt, (255, 80, 60), (240, 50, 50), 6, 1.3)
    ar = shape(lambda d: C.arrow(d, 0.06, 0.16, 0.38, 0.56, 0.032, 0.13, 0.07))
    K.shadow(c, ar, 4, 6, 6, 150)
    K.fill(c, soften(ar), lin((255, 250, 240), (170, 150, 130), 45))
    return K.finish(c)


def overkill():
    """SP: a drawn bow loosing a fan of white-hot arrows: every shot multiplies, ammunition never spent."""
    c = bg((236, 90, 30), (40, 6, 4), cx=0.6, cy=0.5)
    rays(c, 0.16, 0.5, 18, (255, 220, 160), alpha=100)
    bow = shape(lambda d: stroke(d, D.arc_path(0.0, 0.5, 0.44, 0.38, -52, 52), 0.026, 0.026))
    bow = union(bow, shape(lambda d: stroke(d, D.arc_path(0.0, 0.5, 0.44, 0.38, -12, 12), 0.05, 0.05)))
    K.shadow(c, bow, 4, 7, 6, 160)
    K.glow(c, bow, (255, 220, 150, 255), 12, 1.4)
    K.fill(c, soften(bow), lin((255, 210, 140), (170, 100, 40)))
    string = shape(lambda d: d.line(pts([(0.27, 0.21), (0.14, 0.5), (0.27, 0.79)]), fill=255, width=int(0.008 * W)))
    K.fill(c, soften(string), (255, 240, 220, 230))
    tips = []
    arrows = K.mask()
    ad = ImageDraw.Draw(arrows)
    for ang in (-24, 0, 24):
        a = math.radians(ang)
        x1, y1 = 0.14 + math.cos(a) * 0.70, 0.5 + math.sin(a) * 0.70
        C.arrow(ad, 0.14, 0.5, x1, y1, 0.034, 0.16, 0.085, 0.11, 0.06)
        tips.append((x1 - math.cos(a) * 0.08, y1 - math.sin(a) * 0.08))
    trail = shape(lambda d: [stroke(d, [(0.14 + (x - 0.14) * 0.3, 0.5 + (y - 0.5) * 0.3), (x, y)], 0.02, 0.12)
                             for x, y in tips])
    K.glow(c, trail, (255, 160, 40, 255), 14, 1.4)
    K.fill(c, scale(soften(trail, 4), 0.8), (255, 220, 120, 255))
    K.glow(c, arrows, (255, 230, 170, 255), 8, 1.2)
    K.shadow(c, arrows, 4, 6, 6, 150)
    K.fill(c, soften(arrows), lin((255, 252, 245), (210, 190, 170), 0))
    sparkles(c, [(0.86, 0.5, 0.08)], glowc=(255, 200, 100))
    return K.finish(c)


def hover_shot():
    """A winged arrow gliding over a circling trail: shots strike harder as the ranger keeps moving."""
    c = bg((80, 170, 230), (6, 24, 46), cy=0.45)
    trail = shape(lambda d: [d.arc(pts([(0.12, 0.58), (0.88, 0.90)]), a, a + 22, fill=255, width=int(0.026 * W))
                             for a in range(0, 360, 36)])
    K.glow(c, trail, (220, 245, 255, 255), 8, 1.2)
    K.fill(c, soften(trail), (240, 250, 255, 255))
    ar = shape(lambda d: C.arrow(d, 0.14, 0.62, 0.88, 0.30, 0.04, 0.16, 0.085))
    K.glow(c, ar, (230, 245, 255, 255), 10, 1.2)
    K.shadow(c, ar, 4, 8, 7, 160)
    K.fill(c, soften(ar), lin((255, 250, 240), (180, 150, 120), 45))

    def wing(d, side):
        for i in range(4):
            ang = math.radians(-120 - side * 0 + i * 18 if side > 0 else 150 + i * 18)
            bx, by = 0.40, 0.50
            L = 0.24 - i * 0.035
            ex, ey = bx + math.cos(ang) * L, by + math.sin(ang) * L
            nx, ny = -math.sin(ang) * 0.035, math.cos(ang) * 0.035
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    w = shape(lambda d: wing(d, 1))
    lit(c, w, (255, 255, 255), lin((255, 255, 255), (200, 225, 245)), 10, 1.2)
    streak_lines(c, [(0.04, 0.70, 0.18, 0.64), (0.06, 0.80, 0.22, 0.72)], (240, 250, 255), 0.018, 160, 3)
    return K.finish(c)


# ---- SAM -------------------------------------------------------------------------------------------------------------
def hamanoha():
    """A drawn katana amid falling crimson leaves: the foe's strength is shed like leaves from the edge."""
    c = bg((160, 34, 44), (24, 2, 8), cy=0.45)
    rnd = random.Random(7)
    leaves = K.mask()
    ld = ImageDraw.Draw(leaves)
    for x, y in ((0.22, 0.24), (0.74, 0.70), (0.30, 0.74), (0.80, 0.30), (0.56, 0.16), (0.16, 0.52)):
        A.leaf(ld, x - 0.07, y, rnd.uniform(-0.8, 0.8), rnd.uniform(0.15, 0.19), 0.055)
    K.glow(c, leaves, (255, 120, 60, 255), 8, 1.2)
    K.fill(c, soften(leaves), lin((255, 170, 70), (210, 50, 30)))
    k = shape(lambda d: C.katana(d, 0.16, 0.88, 0.86, 0.12, 0.05))
    K.glow(c, k, (255, 220, 200, 255), 14, 1.3)
    K.shadow(c, k, 5, 8, 7, 170)
    K.fill(c, soften(k), metal_paint((255, 255, 255), (170, 176, 196), 45))
    hilt = shape(lambda d: C.katana(d, 0.16, 0.88, 0.86, 0.12, 0.05, 'hilt'))
    K.fill(c, soften(hilt), lin((60, 30, 40), (20, 10, 14)))
    sl = shape(lambda d: [A.leaf(d, 0.50, 0.44, -0.9, 0.10, 0.035)])
    K.fill(c, soften(sl), (255, 120, 60, 255))
    return K.finish(c)


def hagakure():
    """A katana half hidden in green leaves: the next weapon skill keeps its TP."""
    c = bg((40, 130, 70), (4, 20, 10), cy=0.45)
    motes(c, 111, 12, (0.12, 0.12, 0.88, 0.88), (0.006, 0.014), (220, 255, 210), (140, 255, 150))
    k = shape(lambda d: C.katana(d, 0.10, 0.66, 0.92, 0.36, 0.05))
    K.glow(c, k, (220, 255, 220, 255), 14, 1.3)
    K.shadow(c, k, 5, 8, 7, 170)
    K.fill(c, soften(k), metal_paint((255, 255, 255), (170, 186, 186), 45))
    hilt = shape(lambda d: C.katana(d, 0.10, 0.66, 0.92, 0.36, 0.05, 'hilt'))
    K.fill(c, soften(hilt), lin((40, 30, 50), (14, 10, 20)))
    lv = K.mask()
    ld = ImageDraw.Draw(lv)
    for bx, by, ang, L, wd in ((0.60, 0.80, -1.6, 0.42, 0.11), (0.62, 0.78, -0.9, 0.34, 0.09),
                               (0.58, 0.80, -2.3, 0.34, 0.09), (0.64, 0.82, -0.3, 0.26, 0.07)):
        A.leaf(ld, bx, by, ang, L, wd)
    K.glow(c, lv, (120, 255, 140, 255), 10, 1.0)
    K.shadow(c, lv, 4, 7, 6, 150)
    K.fill(c, soften(lv), lin((150, 240, 120), (40, 140, 60), 90))
    veins = shape(lambda d: [d.line(pts([(bx, by), (bx + math.cos(a) * L * 0.9, by + math.sin(a) * L * 0.9)]),
                                    fill=255, width=int(0.008 * W))
                             for bx, by, a, L in ((0.60, 0.80, -1.6, 0.42), (0.62, 0.78, -0.9, 0.34),
                                                  (0.58, 0.80, -2.3, 0.34))])
    K.fill(c, soften(veins), (30, 90, 40, 200))
    return K.finish(c)


def konzen_ittai():
    """A brushed ensō, body and spirit one, a katana standing through it: any weapon skill opens a skillchain."""
    c = bg((50, 50, 150), (6, 6, 26), cy=0.5)
    enso = shape(lambda d: stroke(d, D.arc_path(0.5, 0.5, 0.32, 0.32, -70, 255), 0.10, 0.02))
    K.glow(c, enso, (190, 200, 255, 255), 16, 1.3)
    K.fill(c, soften(enso), lin((255, 255, 255), (190, 200, 240)))
    k = shape(lambda d: C.katana(d, 0.5, 0.94, 0.5, 0.06, 0.03))
    K.glow(c, k, (255, 230, 170, 255), 14, 1.4)
    K.shadow(c, k, 5, 8, 7, 170)
    K.fill(c, soften(k), metal_paint((255, 255, 255), (170, 176, 200), 0))
    hilt = shape(lambda d: C.katana(d, 0.5, 0.94, 0.5, 0.06, 0.03, 'hilt'))
    K.fill(c, soften(hilt), lin((200, 60, 60), (100, 20, 30)))
    sparkles(c, [(0.5, 0.50, 0.11)], glowc=(255, 220, 140))
    return K.finish(c)


def yaegasumi():
    """SP: a katana flashing across eight layered banks of pink haze: special attacks are evaded, one and all."""
    c = bg((255, 200, 220), (120, 50, 120), cy=0.2, r=0.9)
    moon = disc(0.68, 0.24, 0.12)
    K.glow(c, moon, (255, 250, 240, 255), 20, 1.2)
    K.fill(c, soften(moon), (255, 252, 246, 255))
    for i in range(8):
        t = i / 7
        top = 0.30 + i * 0.085
        colr = tuple(int(a + (b - a) * t) for a, b in zip((250, 196, 226), (90, 26, 80)))
        ph = i * 1.7
        q = [(x / 40 * 1.2 - 0.1, top + 0.035 * math.sin(x / 40 * 7 + ph) + 0.02 * math.sin(x / 40 * 15 + ph * 2))
             for x in range(41)]
        band = poly(q + [(1.1, 1.1), (-0.1, 1.1)])
        K.fill(c, soften(band, 4), colr + (255,))
        K.fill(c, scale(soften(minus(band, ImageChops.offset(band, 0, int(0.03 * W))), 6), 0.5),
               (255, 236, 246, 255))
    k = shape(lambda d: C.katana(d, 0.14, 0.86, 0.90, 0.20, 0.05))
    K.glow(c, k, (255, 255, 255, 255), 14, 1.8)
    K.shadow(c, k, 5, 8, 7, 170)
    K.fill(c, soften(k), metal_paint((255, 255, 255), (190, 186, 220), 45))
    hilt = shape(lambda d: C.katana(d, 0.14, 0.86, 0.90, 0.20, 0.05, 'hilt'))
    K.fill(c, soften(hilt), lin((90, 20, 50), (30, 6, 20)))
    rnd = random.Random(12)
    petals = shape(lambda d: [A.leaf(d, x, y, rnd.uniform(0, 6.28), 0.05, 0.022)
                              for x, y in ((0.24, 0.30), (0.46, 0.20), (0.80, 0.52), (0.62, 0.70), (0.34, 0.60))])
    lit(c, petals, (255, 200, 230), (255, 236, 244), 6, 1.2)
    return K.finish(c)


def issekigan():
    """A single unblinking eye over a ninja blade turning aside a strike: parries come often and draw enmity."""
    c = bg((30, 120, 120), (4, 18, 20), cy=0.4)
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.36, 0.30, 0.15))
    K.glow(c, e, (160, 255, 240, 255), 18, 1.4)
    K.fill(c, soften(e), (240, 255, 250, 255))
    iris = disc(0.5, 0.36, 0.12)
    K.fill(c, soften(inter(iris, e)), rad((255, 230, 120), (200, 110, 20), 0.5, 0.33, 0.13))
    K.fill(c, soften(inter(ell(0.475, 0.27, 0.525, 0.45), e), 1), (10, 10, 10, 255))
    K.fill(c, soften(disc(0.46, 0.32, 0.02), 1), (255, 255, 255, 230))
    bl = shape(lambda d: A.sword(d, 0.12, 0.78, 0.90, 0.70, 0.04, 0.07, 0.15))
    K.glow(c, bl, (200, 255, 240, 255), 10, 1.2)
    K.shadow(c, bl, 4, 7, 6, 160)
    K.fill(c, soften(bl), metal_paint((255, 255, 255), (150, 170, 180)))
    sparkles(c, [(0.64, 0.70, 0.12)], glowc=(255, 240, 160))
    return K.finish(c)


def mikage():
    """SP: a ninja before the full moon, a ring of shadow selves around him: each shadow lands a blow."""
    c = bg((90, 60, 180), (8, 4, 26), cy=0.4)
    moon = disc(0.5, 0.46, 0.25)
    K.glow(c, moon, (230, 220, 255, 255), 30, 1.3)
    K.fill(c, soften(moon), rad((255, 252, 255), (200, 190, 240), 0.44, 0.40, 0.3))
    for i in range(6):
        a = math.pi * 2 * i / 6 - math.pi / 2
        x, y = 0.5 + math.cos(a) * 0.30, 0.52 + math.sin(a) * 0.28
        g = shape(lambda d, x=x, y=y: K.figure(d, x, y, 0.46))
        K.glow(c, g, (200, 160, 255, 255), 8, 1.5)
        K.fill(c, scale(soften(g, 1.5), 0.9), (110, 70, 190, 255))
    sl = shape(lambda d: [stroke(d, [(0.22, 0.28), (0.78, 0.76)], 0.006, 0.02),
                          stroke(d, [(0.80, 0.26), (0.24, 0.78)], 0.006, 0.02)])
    K.glow(c, sl, (255, 255, 255, 255), 6, 1.2)
    K.fill(c, soften(sl), (255, 255, 255, 230))
    n = shape(lambda d: K.figure(d, 0.52, 0.53, 0.72))
    K.glow(c, n, (240, 230, 255, 255), 10, 1.8)
    K.fill(c, soften(n), lin((30, 20, 50), (8, 4, 16)))
    return K.finish(c)


# ---- DRG -------------------------------------------------------------------------------------------------------------
def dragon_head(d, cx, cy, s):
    """A dragon's head from the front: horned skull, brow ridges, long snout."""
    q = lambda seq: pts([(cx + x * s, cy + y * s) for x, y in seq])
    d.polygon(q([(0, -0.30), (0.16, -0.20), (0.20, 0.0), (0.11, 0.18), (0.07, 0.36), (-0.07, 0.36), (-0.11, 0.18),
                 (-0.20, 0.0), (-0.16, -0.20)]), fill=255)
    for sx in (-1, 1):
        d.polygon(q([(sx * 0.10, -0.24), (sx * 0.32, -0.46), (sx * 0.20, -0.16)]), fill=255)
        d.polygon(q([(sx * 0.18, -0.04), (sx * 0.36, -0.10), (sx * 0.20, 0.06)]), fill=255)


def dragon_breaker():
    """A lance driven down into a roaring dragon's skull, cracks of light spreading: dragons are crippled."""
    c = bg((210, 70, 30), (34, 6, 4), cx=0.55, cy=0.40)
    rays(c, 0.58, 0.40, 14, (255, 210, 150), alpha=70)
    head = poly([(0.10, 0.52), (0.14, 0.46), (0.30, 0.43), (0.44, 0.37), (0.52, 0.31), (0.62, 0.30), (0.76, 0.36),
                 (0.92, 0.42), (0.82, 0.48), (0.94, 0.56), (0.82, 0.60), (0.92, 0.70), (0.80, 0.72), (0.86, 1.0),
                 (0.52, 1.0), (0.50, 0.78), (0.42, 0.70), (0.16, 0.72), (0.15, 0.67), (0.40, 0.60), (0.44, 0.57),
                 (0.14, 0.56)])
    mouth = poly([(0.14, 0.56), (0.46, 0.57), (0.40, 0.61), (0.16, 0.67)])
    lit(c, mouth, None, (110, 10, 16))
    out = head.filter(ImageFilter.MaxFilter(9))
    K.glow(c, out, (255, 190, 110, 255), 16, 1.3)
    K.shadow(c, out, 5, 8, 8, 170)
    K.fill(c, soften(out, 1.5), (10, 24, 16, 255))
    K.fill(c, soften(head), lin((150, 214, 120), (30, 90, 56), 70))
    belly = inter(head, poly([(0.40, 0.70), (0.54, 0.74), (0.60, 1.0), (0.48, 1.0)]))
    K.fill(c, scale(soften(belly, 3), 0.8), (230, 214, 150, 255))
    scales_ = inter(head, shape(lambda d: [d.arc(pts([(x - 0.05, y - 0.03), (x + 0.05, y + 0.05)]), 20, 160,
                                                 fill=255, width=int(0.010 * W))
                                           for x, y in ((0.66, 0.78), (0.74, 0.86), (0.64, 0.90), (0.72, 0.62))]))
    K.fill(c, scale(soften(scales_), 0.6), (20, 60, 36, 255))
    hornm = union(poly([(0.56, 0.32), (0.70, 0.14), (0.86, 0.04), (0.76, 0.18), (0.68, 0.34)]),
                         poly([(0.68, 0.36), (0.86, 0.26), (0.96, 0.24), (0.84, 0.34), (0.76, 0.40)]))
    K.shadow(c, hornm, 4, 6, 6, 150)
    K.fill(c, soften(hornm), lin((255, 248, 220), (170, 140, 100)))
    teeth = shape(lambda d: [d.polygon(pts([(x, 0.56), (x + 0.018, 0.61), (x + 0.036, 0.56)]), fill=255)
                             for x in (0.17, 0.25, 0.33)] +
                            [d.polygon(pts([(x, 0.67 - (x - 0.18) * 0.25), (x + 0.018, 0.62 - (x - 0.18) * 0.25),
                                            (x + 0.036, 0.67 - (x - 0.18) * 0.25)]), fill=255) for x in (0.20, 0.29)])
    K.fill(c, soften(teeth, 1), (255, 252, 236, 255))
    nost = ell(0.15, 0.47, 0.19, 0.50)
    K.fill(c, soften(nost, 1), (10, 30, 20, 255))
    e = poly([(0.40, 0.44), (0.47, 0.40), (0.51, 0.40), (0.47, 0.45)])
    lit(c, e, (255, 60, 30), (255, 230, 90), 8, 1.8)
    # cracks spreading from the wound, lit from inside
    cr = shape(lambda d: [stroke(d, [(0.60, 0.40), (0.68, 0.46), (0.70, 0.56)], 0.022, 0.004),
                          stroke(d, [(0.60, 0.40), (0.54, 0.48), (0.58, 0.56)], 0.020, 0.004),
                          stroke(d, [(0.60, 0.40), (0.72, 0.38), (0.80, 0.44)], 0.020, 0.004)])
    lit(c, inter(cr, head), (255, 230, 150), (255, 250, 220), 8, 1.8)
    ln = shape(lambda d: C.lance(d, 0.08, -0.12, 0.60, 0.40, 0.065))
    K.glow(c, ln, (255, 240, 200, 255), 14, 1.4)
    K.shadow(c, ln, 4, 7, 6, 170)
    K.fill(c, soften(ln), metal_paint((255, 255, 255), (150, 156, 190), 0))
    sparkles(c, [(0.60, 0.40, 0.14)], glowc=(255, 210, 120))
    return K.finish(c)


def soul_jump():
    """A lance plunging earthward in a comet of blue soul-fire: a jump that draws on the wyvern's spirit."""
    c = bg((60, 50, 170), (6, 4, 30), cy=0.4)
    motes(c, 121, 14, (0.1, 0.1, 0.9, 0.9), (0.004, 0.01), (220, 240, 255), (100, 160, 255))
    ux, uy = 0.62, 0.78
    tip = (0.82, 0.86)
    trail = poly([(tip[0] - ux * 0.22 - uy * 0.22, tip[1] - uy * 0.22 + ux * 0.22),
                  (tip[0] - ux * 0.22 + uy * 0.22, tip[1] - uy * 0.22 - ux * 0.22),
                  (tip[0] - ux * 1.05, tip[1] - uy * 1.05)])
    K.glow(c, trail, (70, 140, 255, 255), 26, 2.0)
    K.fill(c, soften(trail, 10), K.linear((40, 80, 255, 60), (120, 190, 255, 255), 52))
    for k in (-1, 1):
        tongue = shape(lambda d, k=k: stroke(d, [(tip[0] - ux * 0.2 + k * uy * 0.12, tip[1] - uy * 0.2 - k * ux * 0.12),
                                                 (tip[0] - ux * 0.45 + k * uy * 0.16, tip[1] - uy * 0.45 - k * ux * 0.16),
                                                 (tip[0] - ux * 0.62 + k * uy * 0.08, tip[1] - uy * 0.62 - k * ux * 0.08)],
                                             0.05, 0.005))
        K.fill(c, soften(tongue, 3), (200, 235, 255, 230))
    streak_lines(c, [(0.06, 0.40, 0.46, 0.80), (0.40, 0.04, 0.72, 0.52)], (200, 230, 255), 0.02, 160, 4)
    imp = shape(lambda d: d.ellipse(pts([(0.60, 0.84), (1.0, 0.98)]), outline=255, width=int(0.022 * W)))
    lit(c, imp, (160, 210, 255), (230, 245, 255), 8, 1.4)
    ln = shape(lambda d: C.lance(d, 0.18, 0.08, tip[0], tip[1], 0.05))
    K.shadow(c, ln, 5, 8, 6, 200)
    K.fill(c, soften(ln), metal_paint((240, 244, 255), (90, 100, 150), 30))
    return K.finish(c)


def fly_high():
    """SP: a dragoon leaping into a blazing sun, lance raised high: jumps come without end."""
    c = bg((250, 180, 80), (90, 30, 60), cy=0.36, r=0.8)
    rays(c, 0.5, 0.36, 22, (255, 250, 220), alpha=150, width=0.05, length=0.8)
    sun = disc(0.5, 0.36, 0.24)
    K.glow(c, sun, (255, 240, 180, 255), 30, 1.4)
    K.fill(c, soften(sun), rad((255, 255, 245), (255, 214, 110), 0.5, 0.36, 0.24))
    clouds = shape(lambda d: [d.ellipse(pts([(x - r, 0.90 - r * 0.45), (x + r, 0.90 + r * 0.45)]), fill=255)
                              for x, r in ((0.14, 0.18), (0.38, 0.20), (0.62, 0.18), (0.86, 0.18))])
    K.fill(c, soften(clouds, 6), lin((255, 220, 220), (190, 120, 150)))
    q = lambda seq: [(0.5 + (x - 0.5) * 1.55, 0.50 + (y - 0.58) * 1.55) for x, y in seq]
    fig = shape(lambda d: [d.ellipse(pts(q([(0.46, 0.40), (0.54, 0.48)])), fill=255),
                           d.polygon(pts(q([(0.45, 0.48), (0.55, 0.48), (0.57, 0.60), (0.64, 0.66), (0.60, 0.76),
                                            (0.57, 0.75), (0.58, 0.68), (0.51, 0.64), (0.46, 0.72), (0.38, 0.70),
                                            (0.42, 0.66), (0.44, 0.60)])), fill=255),
                           d.polygon(pts(q([(0.54, 0.50), (0.62, 0.42), (0.64, 0.32), (0.67, 0.33), (0.66, 0.44),
                                            (0.57, 0.55)])), fill=255),
                           d.polygon(pts(q([(0.46, 0.50), (0.38, 0.56), (0.34, 0.62), (0.37, 0.63), (0.41, 0.58),
                                            (0.47, 0.55)])), fill=255)])
    ln = shape(lambda d: C.lance(d, 0.58, 0.82, 0.78, 0.04, 0.04))
    sil = union(fig, ln)
    K.glow(c, sil, (255, 250, 220, 255), 10, 1.8)
    K.fill(c, soften(sil), lin((70, 30, 50), (26, 10, 20)))
    return K.finish(c)


def spirit_bond():
    """A wyvern sheltered inside a golden heart: dragoon and wyvern share the blows."""
    c = bg((30, 140, 140), (4, 22, 24), cy=0.45)
    h = shape(lambda d: B.heart(d, 0.5, 0.52, 1.05))
    hi = shape(lambda d: B.heart(d, 0.5, 0.53, 0.86))
    rim = minus(h, hi)
    K.fill(c, scale(soften(hi, 6), 0.35), (255, 230, 160, 255))
    lit(c, rim, (255, 220, 120), gold_paint(), 16, 1.6, sh=True)
    w = shape(lambda d: C.wyvern(d, 0.5, 0.56, 0.78))
    K.glow(c, w, (180, 255, 240, 255), 12, 1.4)
    K.shadow(c, w, 4, 7, 6, 150)
    K.fill(c, soften(w), lin((200, 250, 255), (90, 170, 210)))
    return K.finish(c)


# ---- SMN -------------------------------------------------------------------------------------------------------------
def summon_circle(c, cx, cy, rx, ry, color, glowc, w=0.018):
    m = union(ring(cx, cy, rx, w, ry), ring(cx, cy, rx * 0.78, w * 0.7, ry * 0.78),
              shape(lambda d: d.line(pts([(cx + math.cos(math.radians(-90 + 144 * k)) * rx * 0.78,
                                           cy + math.sin(math.radians(-90 + 144 * k)) * ry * 0.78)
                                          for k in range(6)]), fill=255, width=int(w * 0.8 * W), joint='curve')))
    K.glow(c, m, col(glowc), 10, 1.6)
    K.fill(c, soften(m), col(color))


def mana_cede():
    """A stream of blue mana poured from an orb into a summoning seal: the avatar is given power."""
    c = bg((40, 110, 200), (4, 12, 34), cy=0.45)
    summon_circle(c, 0.62, 0.40, 0.27, 0.27, (230, 245, 255), (120, 200, 255), 0.02)
    st = shape(lambda d: stroke(d, [(0.22, 0.78), (0.28, 0.62), (0.40, 0.50), (0.56, 0.42)], 0.07, 0.02))
    lit(c, st, (120, 200, 255), lin((180, 230, 255), (240, 255, 255), 45), 14, 1.5)
    orb = disc(0.22, 0.78, 0.11)
    lit(c, orb, (120, 200, 255), rad((240, 255, 255), (50, 120, 240), 0.19, 0.74, 0.12), 20, 1.6, sh=True)
    sparkles(c, [(0.62, 0.40, 0.11)], glowc=(160, 220, 255))
    motes(c, 131, 10, (0.3, 0.4, 0.6, 0.7), (0.006, 0.013), (230, 245, 255), (120, 190, 255))
    return K.finish(c)


def astral_conduit():
    """SP: a pillar of starlight pouring through a summoning seal: blood pacts flow freely."""
    c = bg((80, 40, 170), (4, 2, 20), cy=0.6)
    motes(c, 141, 30, (0.06, 0.06, 0.94, 0.94), (0.004, 0.011), (255, 255, 255), (200, 180, 255), 230)
    gal = shape(lambda d: [stroke(d, [(0.5 + math.cos(math.radians(a0 + t * 5)) * (0.08 + t * 0.0055),
                                      0.66 + math.sin(math.radians(a0 + t * 5)) * (0.03 + t * 0.002))
                                     for t in range(0, 61, 2)], 0.008, 0.03) for a0 in (0, 120, 240)])
    K.glow(c, gal, (190, 140, 255, 255), 10, 1.2)
    K.fill(c, scale(soften(gal, 2), 0.8), (230, 200, 255, 255))
    summon_circle(c, 0.5, 0.74, 0.36, 0.11, (250, 240, 255), (200, 150, 255), 0.022)
    beam = poly([(0.40, 0.0), (0.60, 0.0), (0.56, 0.74), (0.44, 0.74)])
    K.glow(c, beam, (200, 170, 255, 255), 24, 1.6)
    K.fill(c, soften(beam, 6), lin((255, 255, 255), (220, 200, 255), 0))
    core = poly([(0.47, 0.0), (0.53, 0.0), (0.515, 0.74), (0.485, 0.74)])
    K.fill(c, soften(core, 3), (255, 255, 255, 255))
    sparkles(c, [(0.5, 0.74, 0.16), (0.22, 0.22, 0.06), (0.80, 0.30, 0.05)], glowc=(220, 190, 255))
    return K.finish(c)


def apogee():
    """A summoned star at the very top of its orbit: the next blood pact is ready at once."""
    c = bg((30, 50, 130), (4, 4, 24), cy=0.4)
    motes(c, 151, 18, (0.08, 0.08, 0.92, 0.92), (0.004, 0.01), (255, 255, 255), (180, 200, 255), 200)
    orb = rot(ring(0.5, 0.56, 0.36, 0.016, 0.22), -10)
    K.glow(c, orb, (150, 190, 255, 255), 8, 1.3)
    K.fill(c, soften(orb), (200, 220, 255, 255))
    arcm = shape(lambda d: stroke(d, D.arc_path(0.5, 0.56, 0.36, 0.22, 200, 262), 0.012, 0.035))
    arcm = rot(arcm, -10)
    lit(c, arcm, (255, 230, 150), (255, 246, 210), 8, 1.4)
    cr = shape(lambda d: B.crescent(d, 0.5, 0.58, 0.10, (0.4, -0.25)))
    lit(c, cr, (200, 220, 255), (230, 236, 255), 12, 1.4)
    x, y = 0.5 + math.cos(math.radians(-90)) * 0.36 * 0 + 0.04, 0.32
    pt = shape(lambda d: K.sparkle(d, 0.56, 0.31, 0.15, 0.2))
    lit(c, pt, (255, 230, 140), (255, 252, 230), 18, 1.8)
    K.fill(c, soften(disc(0.56, 0.31, 0.04)), (255, 255, 255, 255))
    return K.finish(c)


# ---- BLU -------------------------------------------------------------------------------------------------------------
def efflux():
    """A blade riding the crest of a surging azure wave: the next physical blue magic strikes with TP."""
    c = bg((40, 100, 200), (4, 10, 34), cy=0.5)
    wave = shape(lambda d: [stroke(d, [(0.06, 0.90), (0.30, 0.80), (0.56, 0.62), (0.70, 0.42), (0.66, 0.26),
                                       (0.54, 0.22), (0.46, 0.30), (0.52, 0.38)], 0.20, 0.03)])
    K.glow(c, wave, (120, 200, 255, 255), 18, 1.4)
    K.shadow(c, wave, 4, 8, 7, 150)
    K.fill(c, soften(wave), lin((230, 250, 255), (60, 140, 240), 120))
    foam = shape(lambda d: stroke(d, [(0.58, 0.60), (0.68, 0.42), (0.64, 0.28), (0.54, 0.24)], 0.03, 0.01))
    K.fill(c, soften(foam), (255, 255, 255, 230))
    s = shape(lambda d: A.sword(d, 0.20, 0.56, 0.92, 0.10, 0.035, 0.08, 0.13))
    K.glow(c, s, (200, 240, 255, 255), 10, 1.3)
    K.shadow(c, s, 4, 7, 6, 160)
    K.fill(c, soften(s), metal_paint((255, 255, 255), (150, 170, 210), 45))
    motes(c, 161, 14, (0.1, 0.1, 0.9, 0.6), (0.006, 0.014), (230, 250, 255), (120, 200, 255))
    return K.finish(c)


def unbridled_learning():
    """A chain bursting apart in an azure flare: forbidden blue magic is unbound."""
    c = bg((30, 120, 190), (4, 16, 34), cy=0.5)
    rays(c, 0.5, 0.5, 16, (200, 240, 255), alpha=90)
    fl = shape(lambda d: star(d, 0.5, 0.5, 0.22, 0.07, 8))
    lit(c, fl, (120, 220, 255), rad((255, 255, 255), (120, 210, 255), 0.5, 0.5, 0.22), 22, 1.6)
    for x0, y0, x1, y1 in ((0.04, 0.70, 0.40, 0.54), (0.96, 0.30, 0.60, 0.46)):
        ch = shape(lambda d, x0=x0, y0=y0, x1=x1, y1=y1: chain(d, x0, y0, x1, y1, 4, 0.055, 0.022))
        K.shadow(c, ch, 4, 6, 5, 160)
        K.glow(c, ch, (160, 230, 255, 255), 8, 1.0)
        K.fill(c, soften(ch), lin((240, 246, 255), (120, 140, 170)))
    bits = shape(lambda d: [d.polygon(pts([(x - 0.02, y), (x, y - 0.03), (x + 0.02, y), (x, y + 0.03)]), fill=255)
                            for x, y in ((0.40, 0.30), (0.62, 0.70), (0.30, 0.40), (0.70, 0.62))])
    lit(c, bits, (200, 240, 255), (240, 250, 255), 6, 1.4)
    return K.finish(c)


def unbridled_wisdom():
    """SP: a tome thrown open, a great azure eye blazing above it: every unbridled spell is at hand."""
    c = bg((30, 90, 200), (4, 6, 30), cy=0.4)
    rays(c, 0.5, 0.34, 20, (255, 230, 160), alpha=110, width=0.05)
    D.open_book(lin((255, 255, 250), (220, 230, 250), 0), lin((220, 230, 250), (255, 255, 250), 0), c,
                (160, 220, 255), top=0.60, hw=0.34, h=0.24, cover_col=(30, 60, 140))
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.33, 0.26, 0.14))
    K.glow(c, e, (255, 220, 120, 255), 24, 1.6)
    K.fill(c, soften(e), lin((255, 250, 220), (255, 210, 120)))
    iris = disc(0.5, 0.33, 0.10)
    K.fill(c, soften(inter(iris, e)), rad((200, 250, 255), (30, 110, 230), 0.48, 0.30, 0.11))
    K.fill(c, soften(inter(disc(0.5, 0.33, 0.04), e), 1), (6, 14, 40, 255))
    K.fill(c, soften(disc(0.47, 0.30, 0.018), 1), (255, 255, 255, 240))
    motes(c, 171, 16, (0.12, 0.08, 0.88, 0.6), (0.005, 0.012), (255, 245, 210), (255, 210, 120))
    return K.finish(c)



# ---- COR -------------------------------------------------------------------------------------------------------------
def bullet(d, cx, cy, s, ang=0.0):
    """A bullet pointing along ang degrees; (cx, cy) the middle of the casing."""
    a = math.radians(ang)
    u, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))

    def at(x, y):
        return (cx + (x * u[0] + y * n[0]) * s, cy + (x * u[1] + y * n[1]) * s)
    q = [at(-0.20, -0.08), at(0.05, -0.08)]
    q += [at(0.05 + 0.18 * t, -0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(13)]]
    q += [at(0.05 + 0.18 * t, 0.08 * math.cos(math.pi / 2 * t) ** 0.7) for t in [i / 12 for i in range(12, -1, -1)]]
    q += [at(-0.20, 0.08)]
    d.polygon(pts(q), fill=255)
    d.polygon(pts([at(-0.22, -0.09), at(-0.16, -0.09), at(-0.16, 0.09), at(-0.22, 0.09)]), fill=255)


def triple_shot():
    """Three bullets flying side by side out of a muzzle flash: shots may fire three at once."""
    c = bg((40, 110, 150), (4, 14, 26), cx=0.6, cy=0.5)
    streak_lines(c, [(0.12, 0.28, 0.44, 0.28), (0.08, 0.50, 0.40, 0.50), (0.12, 0.72, 0.44, 0.72)],
                 (220, 245, 255), 0.03, 150, 5)
    flash = shape(lambda d: star(d, 0.16, 0.5, 0.20, 0.07, 7, 0))
    lit(c, flash, (255, 180, 60), rad((255, 255, 220), (255, 150, 40), 0.16, 0.5, 0.2), 18, 1.5)
    bl = shape(lambda d: [bullet(d, 0.58 + dx, y, 0.9) for dx, y in ((0.0, 0.28), (0.08, 0.50), (0.0, 0.72))])
    K.glow(c, bl, (255, 220, 140, 255), 14, 1.4)
    K.shadow(c, bl, 4, 7, 6, 150)
    K.fill(c, soften(bl), lin((255, 246, 200), (210, 130, 50), 90))
    hi = shape(lambda d: [stroke(d, [(0.45 + dx, y - 0.035), (0.70 + dx, y - 0.03)], 0.016)
                          for dx, y in ((0.0, 0.28), (0.08, 0.50), (0.0, 0.72))])
    K.fill(c, soften(hi, 2), (255, 255, 255, 190))
    return K.finish(c)


def card(d, cx, cy, w, h, r=0.03):
    d.rounded_rectangle(pts([(cx - w, cy - h), (cx + w, cy + h)]), radius=r * W, fill=255)


def paint_card(c, cx, cy, w, h, ang, pip=None, glowc=(255, 230, 160), back=False):
    m = rot(shape(lambda d: card(d, cx, cy, w, h)), ang, cx, cy)
    K.glow(c, m, col(glowc), 12, 1.0)
    K.shadow(c, m, 4, 7, 6, 150)
    K.fill(c, soften(m), lin((255, 254, 248), (226, 218, 236)) if not back else lin((170, 40, 60), (90, 14, 36)))
    border = rot(shape(lambda d: d.rounded_rectangle(pts([(cx - w * 0.8, cy - h * 0.86), (cx + w * 0.8, cy + h * 0.86)]),
                                                     radius=0.02 * W, outline=255, width=int(0.012 * W))), ang, cx, cy)
    K.fill(c, soften(border), (206, 160, 70, 255))
    if pip:
        pm = rot(shape(lambda d: pip(d, cx, cy)), ang, cx, cy)
        K.fill(c, soften(pm), (200, 30, 50, 255) if not back else (255, 220, 120, 255))
    return m


def spade(d, cx, cy, s=1.0):
    q = []
    for i in range(41):
        t = 2 * math.pi * i / 40
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        q.append((cx + x / 34 * 0.24 * s, cy + y / 34 * 0.24 * s))
    d.polygon(pts(q), fill=255)
    d.polygon(pts([(cx, cy + 0.02 * s), (cx + 0.05 * s, cy + 0.14 * s), (cx - 0.05 * s, cy + 0.14 * s)]), fill=255)


def cutting_cards():
    """SP: a fan of cards sliced clean through by a flashing blade: the party's special abilities come back."""
    c = bg((120, 44, 160), (16, 4, 28), cy=0.5)
    rays(c, 0.5, 0.5, 16, (240, 210, 255), alpha=80)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    for ang, dx, back in ((24, -0.15, True), (-24, 0.15, True), (0, 0.0, False)):
        paint_card(layer, 0.5 + dx, 0.52 + abs(dx) * 0.2, 0.15, 0.25, ang,
                   (lambda d, cx, cy: spade(d, cx, cy + 0.01, 0.9)) if not back else
                   (lambda d, cx, cy: star(d, cx, cy, 0.07, 0.03, 4)), back=back)
    half = poly([(0, 0), (1, 0), (1, 0.30), (0, 0.72)])
    top = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    top.paste(layer, (0, 0), ImageChops.multiply(layer.split()[3], half))
    bot = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    bot.paste(layer, (0, 0), ImageChops.multiply(layer.split()[3], ImageChops.invert(half)))
    c.alpha_composite(bot)
    c.alpha_composite(ImageChops.offset(top, int(-0.03 * W), int(-0.05 * W)))
    sl = poly([(0.02, 0.70), (0.98, 0.29), (0.98, 0.31), (0.02, 0.74)])
    sl = union(sl, shape(lambda d: stroke(d, [(0.06, 0.70), (0.94, 0.32)], 0.005, 0.03)))
    K.glow(c, sl, (255, 220, 120, 255), 14, 2.0)
    K.fill(c, soften(sl), (255, 255, 240, 255))
    sparkles(c, [(0.80, 0.36, 0.09), (0.18, 0.20, 0.05)], glowc=(255, 220, 140))
    return K.finish(c)


def crooked_cards():
    """A bent, crooked card beside a die: the next Phantom Roll is loaded in the corsair's favour."""
    c = bg((40, 130, 80), (4, 22, 12), cy=0.5)
    q = []
    for i in range(21):
        t = i / 20
        q.append((0.20 + 0.32 * t, 0.16 + 0.05 * math.sin(math.pi * t)))
    for i in range(21):
        t = i / 20
        q.append((0.52 + 0.04 * math.sin(math.pi * t), 0.16 + 0.60 * t))
    for i in range(21):
        t = i / 20
        q.append((0.52 - 0.32 * t, 0.76 + 0.05 * math.sin(math.pi * t)))
    for i in range(21):
        t = i / 20
        q.append((0.20 + 0.04 * math.sin(math.pi * t), 0.76 - 0.60 * t))
    m = rot(poly(q), 14, 0.36, 0.46)
    K.glow(c, m, (220, 255, 200, 255), 12, 1.2)
    K.shadow(c, m, 4, 7, 6, 150)
    K.fill(c, soften(m), lin((255, 254, 248), (220, 214, 200)))
    sp = rot(shape(lambda d: spade(d, 0.37, 0.45, 1.0)), 14, 0.36, 0.46)
    K.fill(c, soften(sp), (30, 30, 40, 255))
    D.die(c, 0.68, 0.66, 0.17, (1, 3, 5), glowc=(200, 255, 200), gr=14)
    sparkles(c, [(0.80, 0.22, 0.08)], glowc=(220, 255, 200))
    return K.finish(c)


# ---- PUP -------------------------------------------------------------------------------------------------------------
def tactical_switch():
    """Two arrows chasing each other round a gear, one amber, one blue: master and automaton swap TP."""
    c = bg((60, 110, 150), (6, 14, 24), cy=0.5)
    g = shape(lambda d: D.gear(d, 0.5, 0.5, 0.16, 0.12, 9, hole=0.06))
    K.shadow(c, g, 4, 6, 6, 140)
    K.fill(c, soften(g), rad((200, 196, 200), (90, 86, 100), 0.48, 0.44, 0.2))
    for a0, colr, glowc in ((200, (255, 200, 90), (255, 160, 40)), (20, (130, 220, 255), (60, 170, 255))):
        ar = shape(lambda d, a0=a0: [stroke(d, D.arc_path(0.5, 0.5, 0.32, 0.32, a0, a0 + 130), 0.04, 0.07),
                                     arrowhead(d, *D.arc_path(0.5, 0.5, 0.32, 0.32, a0 + 158, a0 + 158, 1)[0],
                                               a0 + 158 + 90, 0.15)])
        lit(c, ar, glowc, colr, 14, 1.5, sh=True)
    return K.finish(c)


def cooldown():
    """A frosted gear under a snowflake, steam boiling off it: the automaton's heat bleeds away."""
    c = bg((70, 160, 220), (6, 20, 40), cy=0.5)
    steam = shape(lambda d: [stroke(d, [(x, 0.30), (x - 0.04, 0.20), (x + 0.03, 0.10), (x - 0.02, 0.02)], 0.04, 0.01)
                             for x in (0.30, 0.70)])
    K.fill(c, scale(soften(steam, 5), 0.7), (240, 250, 255, 255))
    g = shape(lambda d: D.gear(d, 0.5, 0.56, 0.34, 0.27, 12, hole=0.0))
    K.glow(c, g, (180, 230, 255, 255), 16, 1.2)
    K.shadow(c, g, 5, 8, 8, 150)
    K.fill(c, soften(g), rad((210, 230, 245), (90, 120, 150), 0.45, 0.45, 0.4))
    fr = inter(g, union(*[disc(x, y, r) for x, y, r in ((0.30, 0.36, 0.08), (0.74, 0.70, 0.07), (0.34, 0.80, 0.06),
                                                         (0.76, 0.38, 0.05))]))
    K.fill(c, soften(fr, 4), (250, 255, 255, 200))
    sf = shape(lambda d: [stroke(d, [(0.5 - math.cos(a) * 0.20, 0.56 - math.sin(a) * 0.20),
                                     (0.5 + math.cos(a) * 0.20, 0.56 + math.sin(a) * 0.20)], 0.035)
                          for a in (math.pi / 2, math.pi / 6, -math.pi / 6)]
                 + [stroke(d, [(0.5 + math.cos(a) * 0.10 + math.cos(a + b) * 0.07,
                                0.56 + math.sin(a) * 0.10 + math.sin(a + b) * 0.07),
                               (0.5 + math.cos(a) * 0.10, 0.56 + math.sin(a) * 0.10),
                               (0.5 + math.cos(a) * 0.10 + math.cos(a - b) * 0.07,
                                0.56 + math.sin(a) * 0.10 + math.sin(a - b) * 0.07)], 0.025)
                    for a in [math.pi / 3 * k + math.pi / 2 for k in range(6)] for b in (0.8,)])
    lit(c, sf, (150, 230, 255), (255, 255, 255), 12, 1.6)
    return K.finish(c)


def deus_ex_automata():
    """A harlequin automaton's head descending in a column of golden light, a gear halo behind."""
    c = bg((220, 170, 60), (40, 22, 6), cy=0.3)
    beam = poly([(0.30, 0.0), (0.70, 0.0), (0.78, 1.0), (0.22, 1.0)])
    K.fill(c, scale(beam.filter(ImageFilter.GaussianBlur(16)), 0.6), (255, 250, 220, 255))
    halo = shape(lambda d: D.gear(d, 0.5, 0.48, 0.38, 0.33, 18, hole=0.30))
    lit(c, halo, (255, 230, 140), gold_paint(), 14, 1.4)
    # jester's hat: two drooping lobes, red and blue, gold bells
    lobes = [(-1, (210, 40, 50), (110, 10, 24)), (1, (60, 90, 220), (20, 30, 110))]
    for sx, c0, c1 in lobes:
        lobe = poly([(0.5, 0.20), (0.5 + sx * 0.14, 0.14), (0.5 + sx * 0.30, 0.18), (0.5 + sx * 0.38, 0.30),
                     (0.5 + sx * 0.36, 0.44), (0.5 + sx * 0.30, 0.34), (0.5 + sx * 0.20, 0.30), (0.5 + sx * 0.04, 0.34)])
        K.shadow(c, lobe, 4, 6, 6, 150)
        lit(c, lobe, (255, 240, 200), lin(c0, c1, 90 - sx * 30), 8, 1.0)
        bell = ell(0.5 + sx * 0.36 - 0.045, 0.43, 0.5 + sx * 0.36 + 0.045, 0.52)
        lit(c, bell, (255, 230, 140), rad((255, 255, 220), (200, 130, 40), 0.5 + sx * 0.35, 0.45, 0.06), 8, 1.4)
    band = poly([(0.30, 0.34), (0.40, 0.28), (0.60, 0.28), (0.70, 0.34), (0.66, 0.38), (0.34, 0.38)])
    lit(c, band, None, gold_paint())
    # collar ruff
    ruff = shape(lambda d: [d.ellipse(pts([(0.5 + 0.20 * math.cos(a) - 0.07, 0.80 + 0.06 * math.sin(a) - 0.05),
                                           (0.5 + 0.20 * math.cos(a) + 0.07, 0.80 + 0.06 * math.sin(a) + 0.05)]),
                                      fill=255) for a in [math.pi * k / 5 for k in range(6)]])
    lit(c, ruff, (255, 240, 200), lin((255, 255, 250), (200, 196, 210)), 8, 1.0, sh=True)
    face = ell(0.33, 0.30, 0.67, 0.80)
    K.glow(c, face, (255, 250, 210, 255), 14, 1.3)
    K.shadow(c, face, 5, 8, 8, 150)
    K.fill(c, soften(face), rad((255, 246, 236), (226, 196, 180), 0.44, 0.44, 0.36))
    K.fill(c, soften(band), gold_paint())
    # painted face: diamonds under the eyes, rouge, glowing eyes, a red smile
    dia = shape(lambda d: [d.polygon(pts([(x, 0.53), (x + 0.035, 0.60), (x, 0.67), (x - 0.035, 0.60)]), fill=255)
                           for x in (0.42, 0.58)])
    K.fill(c, soften(dia, 1), (60, 90, 220, 255))
    rouge = shape(lambda d: [d.ellipse(pts([(x - 0.04, 0.60), (x + 0.04, 0.66)]), fill=255) for x in (0.38, 0.62)])
    K.fill(c, scale(soften(rouge, 4), 0.5), (255, 90, 110, 255))
    ey = shape(lambda d: [d.polygon(pts([(x - 0.055, 0.49), (x, 0.455), (x + 0.055, 0.49), (x, 0.515)]), fill=255)
                          for x in (0.42, 0.58)])
    K.fill(c, soften(ey, 1), (30, 20, 40, 255))
    e = shape(lambda d: [d.ellipse(pts([(x - 0.022, 0.47), (x + 0.022, 0.51)]), fill=255) for x in (0.42, 0.58)])
    K.glow(c, e, (120, 230, 255, 255), 6, 1.8)
    K.fill(c, soften(e, 1), (170, 250, 255, 255))
    smile = shape(lambda d: d.arc(pts([(0.42, 0.62), (0.58, 0.72)]), 20, 160, fill=255, width=int(0.022 * W)))
    K.fill(c, soften(smile, 1), (200, 30, 50, 255))
    sparkles(c, [(0.84, 0.82, 0.07), (0.16, 0.80, 0.06)], glowc=(255, 230, 150))
    return K.finish(c)


def maintenance():
    """A brass oil can tipped over a gear, a golden drop falling: the automaton's ailments are oiled away."""
    c = bg((120, 140, 60), (14, 20, 6), cy=0.45)
    g = shape(lambda d: D.gear(d, 0.64, 0.74, 0.24, 0.19, 10, hole=0.07))
    K.shadow(c, g, 4, 6, 6, 140)
    K.glow(c, g, (220, 240, 180, 255), 8, 0.8)
    K.fill(c, soften(g), rad((220, 220, 214), (100, 96, 90), 0.58, 0.68, 0.26))
    can = shape(lambda d: [d.ellipse(pts([(0.10, 0.34), (0.42, 0.60)]), fill=255),
                           d.polygon(pts([(0.12, 0.44), (0.40, 0.44), (0.30, 0.28), (0.22, 0.28)]), fill=255),
                           d.rectangle(pts([(0.235, 0.20), (0.285, 0.30)]), fill=255),
                           stroke(d, [(0.36, 0.46), (0.54, 0.34), (0.70, 0.24)], 0.05, 0.018),
                           d.arc(pts([(0.02, 0.30), (0.20, 0.52)]), 90, 270, fill=255, width=int(0.028 * W))])
    can = rot(can, -16, 0.26, 0.44)
    K.glow(c, can, (255, 240, 180, 255), 12, 1.2)
    K.shadow(c, can, 5, 8, 8, 160)
    K.fill(c, soften(can), lin((255, 230, 150), (170, 110, 40), 45))
    band = inter(can, rot(shape(lambda d: d.ellipse(pts([(0.10, 0.42), (0.42, 0.50)]), outline=255,
                                                    width=int(0.012 * W))), -16, 0.26, 0.44))
    K.fill(c, soften(band), (130, 80, 30, 230))
    drop = poly(D.drop_pts(0.76, 0.28, 0.44, 0.055))
    lit(c, drop, (255, 220, 100), rad((255, 255, 220), (230, 160, 30), 0.74, 0.36, 0.1), 12, 1.8)
    return K.finish(c)


def heady_artifice():
    """SP: an automaton's head crowned with blazing gears: its head's secret technique unleashed."""
    c = bg((130, 60, 170), (16, 4, 28), cy=0.45)
    rays(c, 0.5, 0.40, 20, (255, 230, 170), alpha=110, width=0.05)
    gears = shape(lambda d: [D.gear(d, 0.24, 0.26, 0.15, 0.115, 9, hole=0.05),
                             D.gear(d, 0.76, 0.26, 0.15, 0.115, 9, hole=0.05),
                             D.gear(d, 0.5, 0.17, 0.17, 0.13, 10, hole=0.06)])
    lit(c, gears, (255, 210, 110), gold_paint(), 16, 1.4, sh=True)
    h = shape(lambda d: puppet_head(d, 0.5, 0.56, 1.05))
    K.glow(c, h, (255, 220, 160, 255), 18, 1.6)
    K.shadow(c, h, 5, 8, 8, 160)
    K.fill(c, soften(h), lin((255, 250, 240), (200, 176, 190)))
    puppet_face(c, 0.5, 0.56, 1.05, (255, 240, 160), (255, 180, 60))
    sparkles(c, [(0.84, 0.70, 0.08), (0.16, 0.72, 0.06)], glowc=(255, 210, 120))
    return K.finish(c)


# ---- DNC -------------------------------------------------------------------------------------------------------------
def grand_pas():
    """SP: a dancer flung into a grand jete, a ribbon streaming: flourishes cost no finishing moves."""
    c = bg((210, 50, 140), (34, 4, 30), cy=0.45)
    rays(c, 0.5, 0.45, 18, (255, 220, 240), alpha=90)
    rib = shape(lambda d: stroke(d, [(0.14 + 0.72 * t, 0.84 - 0.16 * math.sin(math.pi * t) + 0.05 * math.sin(7 * t))
                                     for t in (i / 30 for i in range(31))], 0.012, 0.05))
    lit(c, rib, (255, 200, 120), lin((255, 236, 150), (255, 120, 170), 0), 10, 1.4)
    fig = shape(lambda d: [d.ellipse(pts([(0.525, 0.15), (0.655, 0.28)]), fill=255),                  # head
                           stroke(d, [(0.585, 0.29), (0.54, 0.40), (0.49, 0.50)], 0.115, 0.095),         # torso
                           stroke(d, [(0.52, 0.50), (0.70, 0.46), (0.92, 0.38)], 0.095, 0.04),           # front leg
                           stroke(d, [(0.47, 0.52), (0.30, 0.56), (0.08, 0.64)], 0.095, 0.04),           # back leg
                           stroke(d, [(0.60, 0.33), (0.70, 0.21), (0.78, 0.08)], 0.06, 0.035),           # arm up
                           stroke(d, [(0.55, 0.34), (0.40, 0.27), (0.24, 0.24)], 0.06, 0.035)])          # arm back
    skirt = poly([(0.44, 0.44), (0.58, 0.42), (0.68, 0.56), (0.52, 0.52), (0.36, 0.60)])
    allm = union(fig, skirt)
    out = allm.filter(ImageFilter.MaxFilter(7))
    K.glow(c, out, (255, 240, 250, 255), 16, 1.6)
    K.shadow(c, out, 5, 8, 8, 160)
    K.fill(c, soften(out, 1.5), (90, 10, 60, 255))
    K.fill(c, soften(fig), lin((255, 255, 255), (255, 206, 230)))
    K.fill(c, soften(skirt), lin((255, 236, 140), (240, 120, 70)))
    sparkles(c, [(0.20, 0.20, 0.07), (0.84, 0.70, 0.06), (0.88, 0.20, 0.05)], glowc=(255, 210, 240))
    return K.finish(c)


def contradance():
    """Two dancers facing, hands joined in an arch over a healing sparkle: the next waltz is doubled."""
    c = bg((100, 70, 200), (10, 6, 34), cy=0.5)

    def dancer(d, sx):
        x = 0.5 + sx * 0.20
        d.ellipse(pts([(x - 0.05, 0.24), (x + 0.05, 0.34)]), fill=255)
        stroke(d, [(x, 0.34), (x + sx * 0.01, 0.56)], 0.08, 0.07)
        d.polygon(pts([(x - 0.07, 0.52), (x + 0.07, 0.52), (x + 0.12 * sx + 0.0, 0.84), (x - 0.12 * sx, 0.84)]),
                  fill=255)
        stroke(d, [(x - sx * 0.02, 0.38), (x - sx * 0.10, 0.24), (0.5 + sx * 0.02, 0.16)], 0.035, 0.025)
        stroke(d, [(x + sx * 0.02, 0.38), (x + sx * 0.12, 0.48), (x + sx * 0.16, 0.42)], 0.035, 0.025)
    figs = shape(lambda d: [dancer(d, -1), dancer(d, 1)])
    K.glow(c, figs, (220, 200, 255, 255), 12, 1.5)
    K.shadow(c, figs, 5, 8, 8, 150)
    K.fill(c, soften(figs), lin((255, 250, 255), (210, 190, 240)))
    sp = shape(lambda d: K.sparkle(d, 0.5, 0.56, 0.14, 0.22))
    lit(c, sp, (120, 255, 170), (230, 255, 236), 16, 1.8)
    motes(c, 181, 12, (0.3, 0.3, 0.7, 0.85), (0.006, 0.013), (220, 255, 230), (120, 255, 170))
    return K.finish(c)


# ---- SCH -------------------------------------------------------------------------------------------------------------
def goat_head(d, cx, cy, s, fillv=255):
    """A goat's face from the front, without horns; (cx, cy) between the eyes."""
    d.polygon(pts([(cx - 0.13 * s, cy - 0.12 * s), (cx + 0.13 * s, cy - 0.12 * s), (cx + 0.14 * s, cy + 0.04 * s),
                   (cx + 0.08 * s, cy + 0.26 * s), (cx + 0.04 * s, cy + 0.32 * s), (cx - 0.04 * s, cy + 0.32 * s),
                   (cx - 0.08 * s, cy + 0.26 * s), (cx - 0.14 * s, cy + 0.04 * s)]), fill=fillv)
    d.polygon(pts([(cx - 0.05 * s, cy + 0.30 * s), (cx + 0.05 * s, cy + 0.30 * s), (cx, cy + 0.46 * s)]), fill=fillv)
    for sx in (-1, 1):
        A.leaf(d, cx + sx * 0.12 * s, cy - 0.02 * s, math.pi / 2 - sx * (math.pi / 2 + 0.25), 0.22 * s, 0.05 * s,
               fill=fillv)


def caper_emissarius():
    """SP: a glowing scapegoat bearing a red sigil: the scholar's enmity is laid upon an ally."""
    c = bg((40, 130, 130), (4, 20, 22), cy=0.42)
    rays(c, 0.5, 0.40, 16, (220, 255, 240), alpha=100, width=0.05)
    horns = shape(lambda d: [stroke(d, [(0.5 + sx * 0.06, 0.30), (0.5 + sx * 0.14, 0.16), (0.5 + sx * 0.28, 0.12),
                                        (0.5 + sx * 0.36, 0.22), (0.5 + sx * 0.32, 0.34), (0.5 + sx * 0.24, 0.34)],
                                    0.08, 0.02) for sx in (-1, 1)])
    K.glow(c, horns, (255, 230, 160, 255), 12, 1.3)
    K.shadow(c, horns, 4, 7, 6, 150)
    K.fill(c, soften(horns), lin((255, 240, 200), (170, 130, 80), 90))
    ridges = inter(horns, shape(lambda d: [d.line(pts([(x, 0.08), (x + 0.02, 0.40)]), fill=255, width=int(0.008 * W))
                                           for x in (0.22, 0.27, 0.32, 0.68, 0.73, 0.78)]))
    K.fill(c, soften(ridges), (130, 90, 50, 200))
    h = shape(lambda d: goat_head(d, 0.5, 0.44, 1.15))
    K.glow(c, h, (220, 255, 240, 255), 16, 1.5)
    K.shadow(c, h, 5, 8, 8, 150)
    K.fill(c, soften(h), lin((255, 252, 244), (200, 196, 186)))
    e = shape(lambda d: [d.ellipse(pts([(0.5 + sx * 0.085 - 0.03, 0.43), (0.5 + sx * 0.085 + 0.03, 0.47)]),
                                   fill=255) for sx in (-1, 1)])
    K.fill(c, soften(e, 1), (40, 30, 30, 255))
    nose = shape(lambda d: [d.ellipse(pts([(0.5 + sx * 0.03 - 0.014, 0.74), (0.5 + sx * 0.03 + 0.014, 0.77)]),
                                      fill=255) for sx in (-1, 1)])
    K.fill(c, soften(nose, 1), (90, 70, 70, 255))
    sig = shape(lambda d: star(d, 0.5, 0.33, 0.06, 0.025, 5))
    lit(c, sig, (255, 40, 40), (255, 90, 80), 12, 2.0)
    return K.finish(c)


def libra():
    """Golden scales beneath an all-seeing eye: the target's strengths and weaknesses weighed and revealed."""
    c = bg((50, 80, 170), (6, 8, 30), cy=0.45)
    rays(c, 0.5, 0.20, 12, (220, 230, 255), alpha=70)
    sc = shape(lambda d: [d.rectangle(pts([(0.48, 0.28), (0.52, 0.84)]), fill=255),
                          d.polygon(pts([(0.34, 0.88), (0.66, 0.88), (0.58, 0.82), (0.42, 0.82)]), fill=255),
                          stroke(d, [(0.16, 0.38), (0.5, 0.32), (0.84, 0.38)], 0.03),
                          d.line(pts([(0.16, 0.38), (0.08, 0.62)]), fill=255, width=int(0.01 * W)),
                          d.line(pts([(0.16, 0.38), (0.26, 0.62)]), fill=255, width=int(0.01 * W)),
                          d.line(pts([(0.84, 0.38), (0.74, 0.62)]), fill=255, width=int(0.01 * W)),
                          d.line(pts([(0.84, 0.38), (0.94, 0.62)]), fill=255, width=int(0.01 * W)),
                          d.chord(pts([(0.04, 0.54), (0.30, 0.70)]), 0, 180, fill=255),
                          d.chord(pts([(0.70, 0.54), (0.96, 0.70)]), 0, 180, fill=255)])
    sc = inter(sc, disc(0.5, 0.5, 0.45))
    K.glow(c, sc, (255, 220, 120, 255), 14, 1.4)
    K.shadow(c, sc, 4, 7, 6, 150)
    K.fill(c, soften(sc), gold_paint())
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.20, 0.13, 0.07))
    lit(c, e, (200, 230, 255), (250, 252, 255), 14, 1.6)
    K.fill(c, soften(inter(disc(0.5, 0.20, 0.045), e)), rad((150, 220, 255), (30, 90, 200), 0.5, 0.19, 0.05))
    return K.finish(c)


# ---- GEO -------------------------------------------------------------------------------------------------------------
def luopan(c, cx=0.5, cy=0.46, w=0.15, h=0.19, light=(220, 255, 240), mid=(90, 210, 170), dark=(20, 110, 90),
           glowc=(140, 255, 210), gr=20, gs=1.4):
    D.crystal(c, cx, cy, w, h, light, mid, dark, glowc, gr, gs)


def lasting_emanation():
    """The luopan's crystal held in an endless golden loop: it bleeds its life away far more slowly."""
    c = bg((40, 150, 150), (4, 22, 24), cy=0.5)
    lem = [(0.5 + 0.36 * math.cos(t) / (1 + math.sin(t) ** 2), 0.50 + 0.36 * math.sin(t) * math.cos(t) /
            (1 + math.sin(t) ** 2)) for t in (math.pi * 2 * i / 120 for i in range(121))]
    loop = shape(lambda d: stroke(d, lem, 0.04))
    lit(c, loop, (255, 220, 120), gold_paint(), 14, 1.5, sh=True)
    luopan(c, 0.5, 0.48, 0.10, 0.13)
    motes(c, 191, 12, (0.14, 0.14, 0.86, 0.86), (0.006, 0.013), (230, 255, 245), (140, 255, 220))
    return K.finish(c)


def ecliptic_attrition():
    """The luopan's crystal before a burning eclipse: its power swells while its life drains fast."""
    c = bg((200, 80, 30), (34, 6, 4), cy=0.42)
    cor = disc(0.5, 0.40, 0.26)
    K.glow(c, cor, (255, 200, 90, 255), 30, 1.6)
    K.fill(c, soften(ring(0.5, 0.40, 0.25, 0.03), 3), (255, 240, 190, 255))
    K.fill(c, soften(disc(0.5, 0.40, 0.235), 2), rad((30, 10, 20), (10, 4, 8), 0.5, 0.4, 0.24))
    luopan(c, 0.5, 0.56, 0.14, 0.18, (255, 240, 200), (255, 150, 70), (170, 60, 20), (255, 170, 80), 18, 1.4)
    motes(c, 201, 12, (0.12, 0.6, 0.88, 0.9), (0.006, 0.014), (255, 220, 170), (255, 120, 40))
    return K.finish(c)


def collimated_fervor():
    """Parallel shafts of fierce light driven through the luopan's crystal: the next Cardinal Chant intensifies."""
    c = bg((220, 140, 40), (40, 18, 4), cy=0.5)
    beams = shape(lambda d: [d.rectangle(pts([(0.0, y - 0.022), (1.0, y + 0.022)]), fill=255)
                             for y in (0.30, 0.42, 0.54, 0.66)])
    K.glow(c, beams, (255, 220, 120, 255), 12, 1.3)
    K.fill(c, scale(soften(beams, 3), 0.85), lin((255, 255, 240), (255, 210, 120), 0))
    luopan(c, 0.5, 0.46, 0.17, 0.22, (255, 255, 230), (255, 200, 90), (200, 110, 30), (255, 230, 140), 22, 1.6)
    arr = shape(lambda d: [arrowhead(d, 0.94, y, 0, 0.07) for y in (0.30, 0.42, 0.54, 0.66)])
    lit(c, arr, (255, 230, 150), (255, 252, 230), 8, 1.4)
    return K.finish(c)


def life_cycle():
    """A heart's blood circling round into the luopan's crystal: the geomancer's HP restores the luopan."""
    c = bg((200, 80, 120), (34, 6, 20), cy=0.5)
    cyc = shape(lambda d: [stroke(d, D.arc_path(0.5, 0.5, 0.34, 0.34, a0, a0 + 130), 0.03, 0.06)
                           for a0 in (-20, 160)]
                + [arrowhead(d, *D.arc_path(0.5, 0.5, 0.34, 0.34, a, a, 1)[0], a + 90, 0.12) for a in (130, 310)])
    lit(c, cyc, (255, 170, 200), lin((255, 240, 245), (255, 160, 190)), 12, 1.5, sh=True)
    luopan(c, 0.5, 0.48, 0.12, 0.15, (255, 240, 250), (255, 140, 190), (170, 40, 100), (255, 170, 210), 18, 1.4)
    h = shape(lambda d: B.heart(d, 0.80, 0.80, 0.30))
    lit(c, h, (255, 80, 100), rad((255, 180, 180), (220, 20, 60), 0.78, 0.76, 0.12), 12, 1.6, sh=True)
    return K.finish(c)


def blaze_of_glory():
    """The luopan's crystal wreathed in a blaze of glory: the next luopan comes out far stronger."""
    c = bg((200, 40, 30), (30, 4, 4), cy=0.6)
    fl = shape(lambda d: [A.flame(d, 0.5, 0.92, 0.36, 0.86, 0.0), A.flame(d, 0.24, 0.90, 0.15, 0.50, -0.08),
                          A.flame(d, 0.76, 0.90, 0.15, 0.54, 0.08)])
    K.glow(c, fl, (255, 90, 20, 255), 26, 1.4)
    K.fill(c, soften(fl, 2), lin((255, 230, 120), (230, 60, 20), 270))
    luopan(c, 0.5, 0.54, 0.15, 0.20, (255, 255, 240), (255, 220, 140), (220, 120, 40), (255, 250, 200), 22, 1.6)
    sparkles(c, [(0.5, 0.20, 0.10), (0.20, 0.30, 0.05), (0.80, 0.34, 0.05)], glowc=(255, 210, 120))
    return K.finish(c)


def dematerialize():
    """The luopan's crystal dissolving into drifting motes, half there and half not: it cannot be harmed."""
    c = bg((70, 150, 170), (6, 20, 26), cy=0.5)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    D.crystal(layer, 0.42, 0.50, 0.18, 0.24, (240, 255, 255), (140, 220, 240), (40, 120, 150), (180, 250, 255), 20, 1.4)
    fade = K.linear((0, 0, 0, 255), (0, 0, 0, 0), 0).split()[3]
    a = ImageChops.multiply(layer.split()[3], fade.point(lambda v: min(255, int(v * 1.6))))
    layer.putalpha(a)
    c.alpha_composite(layer)
    outline = shape(lambda d: d.line(pts([(0.42, 0.26), (0.60, 0.50), (0.42, 0.776), (0.24, 0.50), (0.42, 0.26)]),
                                     fill=255, width=int(0.008 * W)))
    K.fill(c, scale(soften(outline), 0.5), (220, 250, 255, 255))
    rnd = random.Random(5)
    bits = shape(lambda d: [d.rectangle(pts([(x, y), (x + r, y + r)]), fill=255)
                            for x, y, r in [(rnd.uniform(0.50, 0.86), rnd.uniform(0.22, 0.78), rnd.uniform(0.015, 0.04))
                                            for _ in range(26)]])
    K.glow(c, bits, (180, 250, 255, 255), 6, 1.4)
    K.fill(c, soften(bits, 1), (230, 255, 255, 220))
    return K.finish(c)


def theurgic_focus():
    """A lens and crosshair focusing the luopan's power to a white-hot point: -ra spells strike harder."""
    c = bg((120, 50, 170), (14, 4, 28), cy=0.5)
    cone = poly([(0.10, 0.20), (0.90, 0.20), (0.5, 0.62)])
    K.fill(c, scale(cone.filter(ImageFilter.GaussianBlur(14)), 0.5), (230, 200, 255, 255))
    lens = ell(0.10, 0.12, 0.90, 0.28)
    lit(c, lens, (220, 180, 255), lin((250, 240, 255), (170, 130, 230)), 14, 1.3, sh=True)
    luopan(c, 0.5, 0.64, 0.09, 0.11, (255, 240, 255), (220, 140, 255), (120, 40, 170), (230, 170, 255), 14, 1.2)
    ret = union(ring(0.5, 0.64, 0.22, 0.016),
                shape(lambda d: [d.line(pts([(0.5 + dx * 0.15, 0.64 + dy * 0.15), (0.5 + dx * 0.30, 0.64 + dy * 0.30)]),
                                        fill=255, width=int(0.018 * W))
                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]))
    lit(c, ret, (255, 120, 160), (255, 200, 220), 10, 1.4)
    sp = shape(lambda d: K.sparkle(d, 0.5, 0.55, 0.10, 0.2))
    lit(c, sp, (255, 255, 255), (255, 255, 255), 12, 1.8)
    return K.finish(c)


def concentric_pulse():
    """The luopan's crystal bursting in rings of force: it explodes, striking every foe around it."""
    c = bg((60, 60, 170), (6, 6, 30), cy=0.5)
    rings = union(*[ring(0.5, 0.5, r, w, r * 0.9) for r, w in ((0.40, 0.014), (0.31, 0.022), (0.22, 0.03))])
    K.glow(c, rings, (160, 180, 255, 255), 12, 1.6)
    K.fill(c, soften(rings), (230, 236, 255, 255))
    shards = shape(lambda d: [d.polygon(pts([(0.5 + math.cos(a) * 0.12, 0.5 + math.sin(a) * 0.12),
                                             (0.5 + math.cos(a + 0.12) * 0.24, 0.5 + math.sin(a + 0.12) * 0.24),
                                             (0.5 + math.cos(a - 0.08) * 0.20, 0.5 + math.sin(a - 0.08) * 0.20)]),
                                        fill=255) for a in [math.pi * 2 * k / 7 + 0.3 for k in range(7)]])
    lit(c, shards, (170, 200, 255), lin((240, 246, 255), (130, 150, 240)), 10, 1.4)
    burst = shape(lambda d: star(d, 0.5, 0.5, 0.15, 0.06, 8))
    lit(c, burst, (200, 210, 255), rad((255, 255, 255), (170, 190, 255), 0.5, 0.5, 0.15), 18, 1.8)
    return K.finish(c)


def mending_halation():
    """The luopan bursting into a green halo of healing crosses: its last light restores the party's HP."""
    c = bg((40, 150, 70), (4, 24, 8), cy=0.5)
    rays(c, 0.5, 0.5, 16, (220, 255, 210), alpha=110)
    halo = ring(0.5, 0.5, 0.30, 0.04)
    lit(c, halo, (150, 255, 160), (230, 255, 230), 18, 1.6)
    crosses = shape(lambda d: [(d.rectangle(pts([(x - 0.018, y - 0.05), (x + 0.018, y + 0.05)]), fill=255),
                                d.rectangle(pts([(x - 0.05, y - 0.018), (x + 0.05, y + 0.018)]), fill=255))
                               for x, y in [(0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30)
                                            for a in [math.pi * 2 * k / 6 - math.pi / 2 for k in range(6)]]])
    lit(c, crosses, (120, 255, 140), (250, 255, 250), 10, 1.8, sh=True)
    burst = shape(lambda d: star(d, 0.5, 0.5, 0.17, 0.07, 8))
    lit(c, burst, (180, 255, 190), rad((255, 255, 255), (140, 250, 160), 0.5, 0.5, 0.17), 18, 1.6)
    return K.finish(c)


def radial_arcana():
    """The luopan bursting into a radial spray of blue mana drops: its last light restores the party's MP."""
    c = bg((40, 90, 210), (4, 8, 36), cy=0.5)
    rays(c, 0.5, 0.5, 16, (200, 220, 255), alpha=110)
    drops = K.mask()
    dd = ImageDraw.Draw(drops)
    for k in range(8):
        a = math.pi * 2 * k / 8 - math.pi / 2
        cx, cy = 0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30
        m = poly(D.drop_pts(0.5, 0.42, 0.58, 0.045))
        m = m.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC, center=p(0.5, 0.5))
        m = ImageChops.offset(m, int((cx - 0.5) * W), int((cy - 0.5) * W))
        drops = ImageChops.lighter(drops, m)
    lit(c, drops, (120, 190, 255), rad((240, 250, 255), (70, 140, 255), 0.5, 0.5, 0.45), 12, 1.7, sh=True)
    burst = shape(lambda d: star(d, 0.5, 0.5, 0.17, 0.07, 8))
    lit(c, burst, (170, 210, 255), rad((255, 255, 255), (130, 180, 255), 0.5, 0.5, 0.17), 18, 1.6)
    return K.finish(c)


def widened_compass():
    """SP: a great golden compass rose flung wide around the luopan's crystal: every geomancy area grows."""
    c = bg((40, 130, 160), (4, 16, 28), cy=0.5)
    waves = union(ring(0.5, 0.5, 0.42, 0.012), ring(0.5, 0.5, 0.36, 0.008))
    K.glow(c, waves, (160, 240, 255, 255), 8, 1.3)
    K.fill(c, soften(waves), (210, 250, 255, 255))
    rose = shape(lambda d: [star(d, 0.5, 0.5, 0.40, 0.08, 4, -90), star(d, 0.5, 0.5, 0.26, 0.06, 4, -45)])
    K.glow(c, rose, (255, 220, 120, 255), 18, 1.6)
    K.shadow(c, rose, 4, 7, 6, 150)
    K.fill(c, soften(rose), gold_paint())
    half = shape(lambda d: [d.polygon(pts([(0.5, 0.5), (0.5 + math.cos(a) * 0.40, 0.5 + math.sin(a) * 0.40),
                                           (0.5 + math.cos(a + 0.6) * 0.08, 0.5 + math.sin(a + 0.6) * 0.08)]),
                                      fill=255) for a in [math.pi / 2 * k - math.pi / 2 for k in range(4)]])
    K.fill(c, soften(inter(half, rose)), (190, 120, 40, 200))
    arr = shape(lambda d: [arrowhead(d, 0.5 + math.cos(a) * 0.46, 0.5 + math.sin(a) * 0.46, math.degrees(a), 0.07)
                           for a in [math.pi / 2 * k - math.pi / 4 for k in range(4)]])
    lit(c, arr, (180, 250, 255), (230, 255, 255), 8, 1.4)
    luopan(c, 0.5, 0.49, 0.07, 0.09, (240, 255, 255), (120, 220, 240), (30, 110, 150), (180, 250, 255), 14, 1.4)
    return K.finish(c)


# ---- RUN -------------------------------------------------------------------------------------------------------------
def embolden():
    """A blazing heart inscribed with a rune: the next enhancing spell burns far stronger, if briefly."""
    c = bg((190, 70, 40), (30, 6, 4), cy=0.55)
    fl = shape(lambda d: [A.flame(d, 0.5, 0.80, 0.30, 0.72, 0.0), A.flame(d, 0.28, 0.78, 0.12, 0.40, -0.06),
                          A.flame(d, 0.72, 0.78, 0.12, 0.42, 0.06)])
    K.glow(c, fl, (255, 120, 40, 255), 20, 1.2)
    K.fill(c, scale(soften(fl, 3), 0.85), lin((255, 220, 120), (230, 70, 30), 270))
    h = shape(lambda d: B.heart(d, 0.5, 0.58, 0.95))
    K.glow(c, h, (255, 160, 80, 255), 16, 1.4)
    K.shadow(c, h, 5, 8, 8, 160)
    K.fill(c, soften(h), rad((255, 140, 110), (170, 20, 30), 0.42, 0.46, 0.4))
    g = shape(lambda d: D.rune_glyph(d, 0.5, 0.58, 0.62, 0.05))
    K.glow(c, g, (255, 220, 140, 255), 10, 1.8)
    K.fill(c, soften(g), (255, 250, 230, 255))
    return K.finish(c)


def one_for_all():
    """A rune-marked dome of force sheltering the whole party: magic damage taken is cut for all."""
    c = bg((40, 110, 170), (4, 12, 28), cy=0.55)
    ppl = shape(lambda d: [D.bust(d, x, 0.66, s) for x, s in ((0.30, 0.6), (0.70, 0.6), (0.5, 0.75))])
    ppl = inter(ppl, poly([(0, 0), (1, 0), (1, 0.84), (0, 0.84)]))
    K.glow(c, ppl, (160, 220, 255, 255), 10, 1.4)
    K.fill(c, soften(ppl), lin((120, 150, 200), (50, 70, 120)))
    dome = shape(lambda d: d.pieslice(pts([(0.12, 0.20), (0.88, 1.48)]), 180, 360, fill=255))
    dome = inter(dome, poly([(0, 0), (1, 0), (1, 0.84), (0, 0.84)]))
    K.fill(c, scale(dome, 0.32), (170, 230, 255, 255))
    edge = shape(lambda d: d.arc(pts([(0.12, 0.20), (0.88, 1.48)]), 180, 360, fill=255, width=int(0.03 * W)))
    edge = inter(edge, poly([(0, 0), (1, 0), (1, 0.84), (0, 0.84)]))
    lit(c, edge, (140, 220, 255), (230, 248, 255), 16, 1.6)
    ground = shape(lambda d: d.rectangle(pts([(0.08, 0.83), (0.92, 0.86)]), fill=255))
    lit(c, ground, (140, 220, 255), (210, 240, 255), 8, 1.2)
    g = shape(lambda d: D.rune_glyph(d, 0.5, 0.33, 0.30, 0.03))
    lit(c, g, (150, 230, 255), (240, 252, 255), 8, 1.6)
    return K.finish(c)


def odyllic_subterfuge():
    """SP: a veil of runic mist drawn across a foe's eye: its magic loses its aim."""
    c = bg((80, 40, 140), (8, 2, 20), cy=0.5)
    rays(c, 0.5, 0.48, 14, (210, 180, 255), alpha=70)
    e = shape(lambda d: C.eye_shape(d, 0.5, 0.48, 0.32, 0.17))
    K.glow(c, e, (255, 120, 120, 255), 16, 1.2)
    K.fill(c, soften(e), (255, 236, 230, 255))
    K.fill(c, soften(inter(disc(0.5, 0.48, 0.12), e)), rad((255, 150, 90), (180, 30, 30), 0.5, 0.46, 0.13))
    K.fill(c, soften(inter(ell(0.485, 0.38, 0.515, 0.58), e), 1), (20, 0, 4, 255))
    veil = shape(lambda d: [stroke(d, [(x0 + 0.9 * t, 0.28 + 0.48 * t + 0.05 * math.sin(t * 9 + k))
                                       for t in (i / 30 for i in range(31))], 0.07, 0.07)
                            for k, x0 in enumerate((-0.18, 0.02))])
    veil = veil.filter(ImageFilter.GaussianBlur(10))
    K.fill(c, scale(veil, 0.9), (170, 120, 255, 255))
    gl = shape(lambda d: [D.rune_glyph(d, x, y, 0.20, 0.022) for x, y in ((0.24, 0.24), (0.76, 0.74), (0.72, 0.22))])
    lit(c, gl, (200, 160, 255), (240, 230, 255), 10, 1.8)
    motes(c, 211, 14, (0.12, 0.12, 0.88, 0.88), (0.006, 0.013), (230, 220, 255), (170, 120, 255))
    return K.finish(c)


def vivacious_pulse():
    """A heartbeat line racing across a glowing rune stone: HP restored by the power of the runes."""
    c = bg((40, 150, 90), (4, 24, 12), cy=0.5)
    stone = poly([(0.30, 0.18), (0.68, 0.16), (0.76, 0.42), (0.72, 0.84), (0.30, 0.86), (0.24, 0.50)])
    K.glow(c, stone, (150, 255, 180, 255), 16, 1.2)
    K.shadow(c, stone, 5, 8, 8, 160)
    K.fill(c, soften(stone, 2), lin((140, 170, 150), (50, 70, 60), 60))
    g = shape(lambda d: D.rune_glyph(d, 0.50, 0.50, 0.70, 0.05))
    K.fill(c, scale(soften(g), 0.55), (200, 255, 210, 255))
    pulse = shape(lambda d: stroke(d, [(0.04, 0.54), (0.30, 0.54), (0.38, 0.40), (0.46, 0.72), (0.54, 0.26),
                                       (0.62, 0.62), (0.68, 0.54), (0.96, 0.54)], 0.035))
    lit(c, pulse, (120, 255, 150), (240, 255, 240), 14, 1.8)
    return K.finish(c)


# ---- other -----------------------------------------------------------------------------------------------------------
def relinquish():
    """An open hand letting a glowing orb drift free: something held is given up."""
    c = bg((90, 110, 170), (8, 10, 28), cy=0.4)
    h = shape(lambda d: hand(d, 0.5, 0.74, 0.70))
    K.glow(c, h, (220, 230, 255, 255), 14, 1.3)
    K.shadow(c, h, 4, 7, 7, 130)
    K.fill(c, soften(h), lin((240, 236, 246), (180, 176, 200)))
    trail = shape(lambda d: stroke(d, [(0.50, 0.42), (0.46, 0.34), (0.50, 0.26)], 0.02, 0.06))
    K.fill(c, scale(soften(trail, 4), 0.6), (220, 240, 255, 255))
    orb = disc(0.50, 0.20, 0.10)
    lit(c, orb, (180, 220, 255), rad((255, 255, 255), (130, 180, 255), 0.47, 0.17, 0.12), 22, 1.7)
    motes(c, 221, 12, (0.2, 0.06, 0.8, 0.5), (0.006, 0.013), (230, 240, 255), (160, 200, 255))
    return K.finish(c)


ICONS = {}
for _n, _f in [('Blood Rage', blood_rage), ('Brazen Rush', brazen_rush), ('Impetus', impetus),
               ('Inner Strength', inner_strength), ('Divine Caress', divine_caress),
               ('Sacrosanctity', sacrosanctity), ('Sanctuary', sanctuary), ('Enmity Douse', enmity_douse),
               ('Manawell', manawell), ('Subtle Sorcery', subtle_sorcery), ('Cascade', cascade),
               ('Saboteur', saboteur), ('Spontaneity', spontaneity), ('Stymie', stymie),
               ('Conspirator', conspirator), ('Bully', bully), ('Larceny', larceny), ('Sepulcher', sepulcher),
               ('Palisade', palisade), ('Intervene', intervene), ('Majesty', majesty),
               ('Arcane Crest', arcane_crest), ('Scarlet Delirium', scarlet_delirium),
               ('Soul Enslavement', soul_enslavement), ('Consume Mana', consume_mana),
               ('Unleash', unleash), ('Bestial Loyalty', bestial_loyalty), ('Tenuto', tenuto), ('Marcato', marcato),
               ('Clarion Call', clarion_call), ('Bounty Shot', bounty_shot), ('Decoy Shot', decoy_shot),
               ('Overkill', overkill), ('Hover Shot', hover_shot), ('Hamanoha', hamanoha), ('Hagakure', hagakure),
               ('Konzen-ittai', konzen_ittai), ('Yaegasumi', yaegasumi), ('Issekigan', issekigan),
               ('Mikage', mikage), ('Dragon Breaker', dragon_breaker), ('Soul Jump', soul_jump),
               ('Fly High', fly_high), ('Spirit Bond', spirit_bond), ('Mana Cede', mana_cede),
               ('Astral Conduit', astral_conduit), ('Apogee', apogee), ('Efflux', efflux),
               ('Unbridled Learning', unbridled_learning), ('Unbridled Wisdom', unbridled_wisdom),
               ('Triple Shot', triple_shot), ('Cutting Cards', cutting_cards), ('Crooked Cards', crooked_cards),
               ('Tactical Switch', tactical_switch), ('Cooldown', cooldown), ('Deus Ex Automata', deus_ex_automata),
               ('Maintenance', maintenance), ('Heady Artifice', heady_artifice), ('Grand Pas', grand_pas),
               ('Contradance', contradance), ('Caper Emissarius', caper_emissarius), ('Libra', libra),
               ('Lasting Emanation', lasting_emanation), ('Ecliptic Attrition', ecliptic_attrition),
               ('Collimated Fervor', collimated_fervor), ('Life Cycle', life_cycle),
               ('Blaze of Glory', blaze_of_glory), ('Dematerialize', dematerialize),
               ('Theurgic Focus', theurgic_focus), ('Concentric Pulse', concentric_pulse),
               ('Mending Halation', mending_halation), ('Radial Arcana', radial_arcana),
               ('Widened Compass', widened_compass), ('Embolden', embolden), ('One for All', one_for_all),
               ('Odyllic Subterfuge', odyllic_subterfuge), ('Vivacious Pulse', vivacious_pulse),
               ('Relinquish', relinquish)]:
    ICONS[('ja', _n)] = _f
