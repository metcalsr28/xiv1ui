"""Signature icons, round 2: pet commands (BST, SMN, DRG wyvern, PUP), DNC steps/sambas/flourishes/jigs, SCH
stratagems and addenda, RUN wards and effusions."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K
import group_b as GB
import group_d as GD

p, pts, W = K.p, K.pts, K.W
bg, col, lit, rot, inter, minus, scale = GD.bg, GD.col, GD.lit, GD.rot, GD.inter, GD.minus, GD.scale
stroke, arc_path, star, arrowhead, motes, sparkles, rays, poly, ell = (
    GD.stroke, GD.arc_path, GD.star, GD.arrowhead, GD.motes, GD.sparkles, GD.rays, GD.poly, GD.ell)
lin = GD.linear_v


def lighter(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def grad_mask(x0, x1, angle=0):
    """A 0..255 ramp along the x axis between unit x0 and x1 (then rotated by angle degrees)."""
    m = K.mask()
    px = m.load()
    for x in range(W):
        u = x / W
        v = int(max(0.0, min(1.0, (u - x0) / (x1 - x0))) * 255)
        for y in range(W):
            px[x, y] = v
    return m.rotate(angle, resample=Image.BICUBIC, center=p(0.5, 0.5)) if angle else m


def arrow_path(c, path, w0, w1, head, glowc, paint, gr=14, gs=1.4, sh=True):
    """A brush-stroke arrow along a polyline, head at the end."""
    (x0, y0), (x1, y1) = path[-2], path[-1]
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    m = K.shape(lambda d: [stroke(d, path[:-1], w0, w1),
                           arrowhead(d, x1 + math.cos(math.radians(ang)) * head * 0.6,
                                     y1 + math.sin(math.radians(ang)) * head * 0.6, ang, head)])
    lit(c, m, glowc, paint, gr, gs, sh=sh)


def bolt_pts(x, y, s):
    return [(x + 0.07 * s, y - 0.38 * s), (x - 0.15 * s, y + 0.04 * s), (x - 0.01 * s, y + 0.04 * s),
            (x - 0.09 * s, y + 0.40 * s), (x + 0.17 * s, y - 0.08 * s), (x + 0.03 * s, y - 0.08 * s),
            (x + 0.15 * s, y - 0.38 * s)]


# ---- BST: the paw is the pet --------------------------------------------------------------------------------------
def paw_m(cx, cy, s):
    return K.shape(lambda d: GB.paw(d, cx, cy, s))


def cream():
    return lin((255, 250, 232), (226, 168, 92))


def fight():
    """Claws out: three raking slashes over the pet's paw."""
    c = bg((190, 40, 30), (30, 4, 4), cy=0.42)
    pw = paw_m(0.36, 0.64, 0.66)
    lit(c, pw, (255, 170, 110), cream(), 16, 1.2, sh=True)
    sl = K.mask()
    d = ImageDraw.Draw(sl)
    for i in range(3):
        o = (i - 1) * 0.11
        stroke(d, [(0.36 + o, 0.10 + o * 0.2), (0.58 + o, 0.34 + o * 0.2), (0.82 + o, 0.62 + o * 0.2)], 0.02, 0.085)
    lit(c, sl, (255, 90, 50), lin((255, 255, 240), (255, 170, 120)), 16, 1.6, sh=True)
    sparkles(c, [(0.82, 0.18, 0.07)], glowc=(255, 180, 120))
    return K.finish(c)


def heel():
    """Come back: an arrow loops around and returns to the pet's side."""
    c = bg((40, 150, 140), (4, 24, 24), cy=0.5)
    path = arc_path(0.52, 0.50, 0.32, 0.30, -40, 200)
    arrow_path(c, path, 0.03, 0.07, 0.15, (160, 255, 230), lin((240, 255, 250), (130, 220, 200)), 12, 1.4)
    pw = paw_m(0.52, 0.56, 0.62)
    lit(c, pw, (200, 255, 230), cream(), 18, 1.3, sh=True)
    return K.finish(c)


def leave():
    """Set free: the paw fades away into drifting motes."""
    c = bg((110, 100, 160), (14, 10, 30), cy=0.5)
    pw = paw_m(0.44, 0.58, 0.82)
    fade = ImageChops.invert(grad_mask(0.25, 0.85, -35))
    K.glow(c, inter(pw, fade), (230, 220, 255, 255), 18, 1.2)
    K.fill(c, K.soften(inter(pw, fade)), (250, 244, 255, 255))
    K.fill(c, K.soften(inter(pw, scale(grad_mask(0.25, 0.85, -35), 0.25)), 3), (220, 210, 255, 255))
    motes(c, 41, 22, (0.52, 0.10, 0.92, 0.62), (0.008, 0.022), (240, 236, 255), (190, 170, 255))
    arrow_path(c, [(0.60, 0.40), (0.70, 0.30), (0.76, 0.24)], 0.03, 0.05, 0.10, (220, 200, 255),
               (245, 240, 255), 10, 1.2, sh=False)
    return K.finish(c)


def sic():
    """Sic 'em: the pet unleashes its special move - a bolt strikes through the paw."""
    c = bg((220, 120, 30), (40, 14, 2), cy=0.5)
    rays(c, 0.5, 0.5, 16, (255, 230, 170), alpha=80, phase=0.1)
    pw = paw_m(0.44, 0.60, 0.80)
    lit(c, pw, (255, 200, 120), lin((120, 60, 30), (60, 24, 10)), 14, 1.4, sh=True)
    b = poly(bolt_pts(0.60, 0.42, 1.0))
    lit(c, b, (255, 240, 140), lin((255, 255, 235), (255, 200, 60)), 20, 1.8, sh=True)
    return K.finish(c)


def stay():
    """Hold position: the paw planted inside a ground ring, a pause mark over it."""
    c = bg((50, 90, 190), (4, 10, 36), cy=0.55)
    GD.aura_ring(c, 0.5, 0.78, 0.36, 0.10, (210, 230, 255), (120, 170, 255))
    pw = paw_m(0.5, 0.60, 0.80)
    lit(c, pw, (190, 220, 255), cream(), 16, 1.2, sh=True)
    bars = K.shape(lambda d: [d.rounded_rectangle(pts([(0.70, 0.12), (0.75, 0.30)]), radius=0.015 * W, fill=255),
                              d.rounded_rectangle(pts([(0.79, 0.12), (0.84, 0.30)]), radius=0.015 * W, fill=255)])
    lit(c, bars, (180, 210, 255), (240, 248, 255), 10, 1.5)
    return K.finish(c)


def snarl():
    """A bared-fang snarl: the pet draws the foe's hatred."""
    c = bg((150, 30, 70), (24, 2, 12), cy=0.5)
    mouth = poly([(0.10, 0.50), (0.30, 0.30), (0.50, 0.26), (0.70, 0.30), (0.90, 0.50), (0.70, 0.72),
                  (0.50, 0.76), (0.30, 0.72)])
    lit(c, mouth, (255, 80, 110), lin((200, 50, 70), (110, 14, 30)), 20, 1.3, sh=True)
    inner = poly([(0.18, 0.50), (0.34, 0.38), (0.50, 0.35), (0.66, 0.38), (0.82, 0.50), (0.66, 0.63),
                  (0.50, 0.66), (0.34, 0.63)])
    K.fill(c, K.soften(inner, 2), (24, 2, 10, 255))
    teeth = K.shape(lambda d: [d.polygon(pts(t), fill=255) for t in (
        [(0.28, 0.40), (0.38, 0.36), (0.33, 0.60)], [(0.62, 0.36), (0.72, 0.40), (0.67, 0.60)],
        [(0.42, 0.355), (0.49, 0.35), (0.455, 0.44)], [(0.51, 0.35), (0.58, 0.355), (0.545, 0.44)],
        [(0.37, 0.64), (0.45, 0.66), (0.41, 0.48)], [(0.55, 0.66), (0.63, 0.64), (0.59, 0.48)])])
    lit(c, teeth, None, lin((255, 255, 250), (220, 210, 190)), soft=1.0)
    eyes = K.shape(lambda d: [d.polygon(pts([(0.22, 0.20), (0.38, 0.24), (0.24, 0.26)]), fill=255),
                              d.polygon(pts([(0.78, 0.20), (0.62, 0.24), (0.76, 0.26)]), fill=255)])
    lit(c, eyes, (255, 220, 80), (255, 240, 160), 10, 1.8)
    return K.finish(c)


def ready():
    """Charges ready: three glowing pips above the paw."""
    c = bg((90, 160, 60), (8, 26, 6), cy=0.55)
    pw = paw_m(0.5, 0.66, 0.74)
    lit(c, pw, (210, 255, 170), cream(), 16, 1.3, sh=True)
    for x, y in ((0.26, 0.30), (0.5, 0.20), (0.74, 0.30)):
        o = ell(x - 0.07, y - 0.07, x + 0.07, y + 0.07)
        lit(c, o, (220, 255, 140), K.radial((255, 255, 240, 255), (180, 240, 80, 255), x - 0.02, y - 0.02, 0.08),
            14, 1.6)
    return K.finish(c)


def spur():
    """A spiked rowel spinning on its spur: the pet driven on."""
    c = bg((210, 150, 50), (40, 22, 4), cy=0.5)
    band = K.shape(lambda d: stroke(d, arc_path(0.40, 0.56, 0.24, 0.20, 70, 290), 0.065))
    neck = K.shape(lambda d: stroke(d, [(0.46, 0.52), (0.62, 0.44)], 0.05))
    lit(c, lighter(band, neck), (255, 220, 140), lin((240, 240, 250), (130, 130, 150)), 10, 1.0, sh=True)
    r = K.shape(lambda d: [star(d, 0.66, 0.42, 0.27, 0.10, 8, -90)])
    r = minus(r, ell(0.625, 0.385, 0.695, 0.455))
    lit(c, r, (255, 230, 140), K.radial((255, 255, 225, 255), (220, 140, 40, 255), 0.66, 0.38, 0.22), 18, 1.5,
        sh=True)
    motes(c, 7, 10, (0.55, 0.15, 0.92, 0.75), (0.006, 0.014), (255, 240, 200), (255, 200, 100))
    return K.finish(c)


def run_wild():
    """A paw ablaze with a feral, ragged aura."""
    c = bg((150, 40, 170), (22, 4, 30), cy=0.55)
    rnd = random.Random(9)
    q = []
    n = 22
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        r = rnd.uniform(0.34, 0.46) if i % 2 == 0 else 0.22
        if math.sin(a) > 0.4 and i % 2 == 0:
            r *= 0.8
        q.append((0.5 + math.cos(a) * r, 0.54 + math.sin(a) * r))
    aura = poly(q)
    lit(c, aura, (255, 90, 230), K.radial((255, 200, 250, 255), (210, 40, 180, 255), 0.5, 0.54, 0.46), 22, 1.4)
    pw = paw_m(0.5, 0.58, 0.70)
    lit(c, pw, (255, 230, 255), lin((60, 14, 60), (24, 4, 26)), 8, 1.4, sh=True)
    return K.finish(c)


# ---- SMN: the avatar is a spirit orb over the summoning circle ---------------------------------------------------
def ground_ring(c, cx, cy, rx, ry, color, glowc, broken=False):
    m = K.shape(lambda d: [d.ellipse(pts([(cx - rx, cy - ry), (cx + rx, cy + ry)]), outline=255,
                                     width=int(0.026 * W)),
                           d.ellipse(pts([(cx - rx * 0.72, cy - ry * 0.72), (cx + rx * 0.72, cy + ry * 0.72)]),
                                     outline=255, width=int(0.014 * W))])
    if broken:
        gaps = K.shape(lambda d: [d.pieslice(pts([(cx - rx * 1.2, cy - ry * 1.2), (cx + rx * 1.2, cy + ry * 1.2)]),
                                             a, a + 22, fill=255) for a in range(0, 360, 60)])
        m = minus(m, gaps)
    disc = ell(cx - rx, cy - ry, cx + rx, cy + ry)
    K.fill(c, scale(disc.filter(ImageFilter.GaussianBlur(12)), 0.4), col(glowc))
    K.glow(c, m, col(glowc), 10, 1.5)
    K.fill(c, K.soften(m), col(color))


def spirit(c, cx, cy, r, core, glowc, gr=26):
    o = ell(cx - r, cy - r, cx + r, cy + r)
    K.glow(c, o, col(glowc), gr, 1.7)
    K.fill(c, K.soften(o, 3), K.radial((255, 255, 255, 255), col(core), cx - r * 0.25, cy - r * 0.25, r * 1.1))


def assault():
    """The avatar hurled at the foe: a spirit comet leaps from the circle at a target."""
    c = bg((200, 60, 40), (34, 6, 4), cx=0.6, cy=0.4)
    ground_ring(c, 0.30, 0.80, 0.22, 0.07, (255, 220, 200), (255, 120, 80))
    ret = K.shape(lambda d: [d.ellipse(pts([(0.52, 0.12), (0.88, 0.48)]), outline=255, width=int(0.032 * W))]
                  + [d.line(pts([(0.70 + dx * 0.13, 0.30 + dy * 0.13), (0.70 + dx * 0.25, 0.30 + dy * 0.25)]),
                            fill=255, width=int(0.032 * W)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])
    lit(c, ret, (255, 120, 90), (255, 214, 196), 12, 1.5)
    trail = poly([(0.28, 0.80), (0.20, 0.70), (0.60, 0.34), (0.72, 0.46)])
    K.glow(c, trail, (255, 140, 60, 255), 16, 1.0)
    K.fill(c, K.soften(trail, 8), K.linear((255, 120, 60, 0), (255, 230, 170, 255), 315))
    spirit(c, 0.66, 0.40, 0.15, (255, 130, 50), (255, 160, 80), 30)
    return K.finish(c)


def retreat():
    """The avatar called back: the spirit arcs home into its circle."""
    c = bg((50, 100, 200), (4, 10, 36), cy=0.5)
    ground_ring(c, 0.44, 0.78, 0.28, 0.08, (220, 236, 255), (120, 170, 255))
    path = arc_path(0.54, 0.62, 0.30, 0.42, -40, -175)
    arrow_path(c, path + [(0.235, 0.67)], 0.02, 0.07, 0.14, (170, 210, 255), lin((250, 252, 255), (150, 190, 250)),
               12, 1.4)
    spirit(c, 0.76, 0.30, 0.09, (110, 170, 255), (140, 190, 255), 20)
    return K.finish(c)


def release():
    """The pact let go: the circle breaks and the spirit dissolves upward."""
    c = bg((60, 150, 120), (4, 24, 20), cy=0.5)
    ground_ring(c, 0.5, 0.78, 0.32, 0.09, (210, 255, 235), (110, 230, 180), broken=True)
    col_m = poly([(0.32, 0.78), (0.68, 0.78), (0.60, 0.10), (0.40, 0.10)])
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(18)), 0.35), (180, 255, 220, 255))
    spirit(c, 0.5, 0.50, 0.15, (110, 230, 170), (150, 255, 200), 26)
    motes(c, 17, 30, (0.26, 0.06, 0.74, 0.40), (0.010, 0.026), (235, 255, 245), (140, 255, 200))
    sparkles(c, [(0.30, 0.20, 0.06), (0.68, 0.14, 0.05)], glowc=(160, 255, 210))
    return K.finish(c)


def pact_sigil(c, cx, cy, r, color, glowc):
    m = K.shape(lambda d: [d.ellipse(pts([(cx - r, cy - r), (cx + r, cy + r)]), outline=255, width=int(0.022 * W)),
                           d.line(pts([(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r)
                                       for a in (90, 210, 330, 90)]), fill=255, width=int(0.016 * W),
                                  joint='curve')]
                  + [d.ellipse(pts([(cx + math.cos(math.radians(a)) * r - 0.025, cy + math.sin(math.radians(a)) * r
                                     - 0.025), (cx + math.cos(math.radians(a)) * r + 0.025,
                                                cy + math.sin(math.radians(a)) * r + 0.025)]), fill=255)
                     for a in (30, 150, 270)])
    K.glow(c, m, col(glowc), 14, 1.5)
    K.fill(c, K.soften(m), col(color))


def bp_rage():
    """Blood Pact: Rage - a blood drop at the heart of the pact sigil, flaring with fury."""
    c = bg((170, 20, 30), (24, 2, 4), cy=0.5)
    rays(c, 0.5, 0.52, 12, (255, 160, 110), alpha=110, width=0.07)
    pact_sigil(c, 0.5, 0.52, 0.36, (255, 200, 170), (255, 80, 60))
    drop = poly(GD.drop_pts(0.5, 0.20, 0.74, 0.17))
    lit(c, drop, (255, 70, 50), K.radial((255, 160, 140, 255), (180, 0, 20, 255), 0.45, 0.55, 0.26), 22, 1.5, sh=True)
    hi = ell(0.42, 0.52, 0.47, 0.62)
    K.fill(c, K.soften(hi, 3), (255, 230, 230, 200))
    return K.finish(c)


def bp_ward():
    """Blood Pact: Ward - the pact's blood drop set on a guarding shield."""
    c = bg((30, 120, 170), (2, 16, 30), cy=0.5)
    pact_sigil(c, 0.5, 0.52, 0.38, (200, 240, 255), (90, 190, 255))
    sp = GD.shield_pts(0.5, 0.24, 0.22, 0.58)
    sh = poly(sp)
    lit(c, sh, (140, 220, 255), lin((240, 250, 255), (120, 160, 200)), 18, 1.3, sh=True)
    inner = poly(GD.shield_pts(0.5, 0.275, 0.18, 0.50))
    K.fill(c, K.soften(inner), lin((60, 130, 200), (14, 40, 90)))
    drop = poly(GD.drop_pts(0.5, 0.32, 0.66, 0.11))
    lit(c, drop, (255, 80, 70), K.radial((255, 150, 140, 255), (180, 0, 20, 255), 0.46, 0.55, 0.16), 10, 1.3)
    return K.finish(c)


def avatars_favor():
    """The avatar's blessing: a crowned spirit in a pillar of light, sharing its favour."""
    c = bg((180, 160, 60), (30, 24, 4), cy=0.5)
    rays(c, 0.5, 0.42, 18, (255, 250, 210), alpha=100, width=0.05)
    ground_ring(c, 0.5, 0.80, 0.30, 0.08, (255, 250, 220), (255, 220, 120))
    col_m = poly([(0.34, 0.80), (0.66, 0.80), (0.60, 0.10), (0.40, 0.10)])
    K.fill(c, scale(col_m.filter(ImageFilter.GaussianBlur(16)), 0.4), (255, 250, 210, 255))
    spirit(c, 0.5, 0.52, 0.19, (255, 190, 60), (255, 230, 140), 32)
    halo = K.shape(lambda d: d.ellipse(pts([(0.34, 0.16), (0.66, 0.27)]), outline=255, width=int(0.026 * W)))
    lit(c, halo, (255, 230, 140), (255, 246, 200), 10, 1.4)
    sparkles(c, [(0.24, 0.40, 0.06), (0.76, 0.56, 0.07), (0.70, 0.20, 0.05)], glowc=(255, 230, 150))
    return K.finish(c)


# ---- DRG: the wyvern -----------------------------------------------------------------------------------------------
def wyvern_head(cx=0.0, cy=0.0, s=1.0):
    """A wyvern's head in profile, facing right, jaws open; (mask, eye point, mouth point)."""
    def q(seq):
        return [(cx + x * s, cy + y * s) for x, y in seq]
    head = q([(0.06, 0.92), (0.10, 0.60), (0.16, 0.42), (0.26, 0.31), (0.42, 0.28), (0.58, 0.32), (0.72, 0.38),
              (0.78, 0.43), (0.74, 0.47), (0.56, 0.48), (0.44, 0.50), (0.60, 0.56), (0.66, 0.60), (0.60, 0.63),
              (0.44, 0.63), (0.32, 0.70), (0.28, 0.92)])
    horns = [q([(0.24, 0.33), (0.02, 0.16), (0.30, 0.29)]), q([(0.32, 0.30), (0.16, 0.08), (0.40, 0.29)])]
    frill = q([(0.12, 0.50), (0.00, 0.44), (0.06, 0.56), (0.00, 0.62), (0.10, 0.66)])
    m = K.shape(lambda d: [d.polygon(pts(head), fill=255), d.polygon(pts(frill), fill=255)]
                + [d.polygon(pts(h), fill=255) for h in horns])
    return m, (cx + 0.40 * s, cy + 0.37 * s), (cx + 0.62 * s, cy + 0.53 * s)


def wyvern_paint(c, m, eye, glowc, body=((120, 160, 230), (30, 50, 110)), eyec=(255, 230, 120)):
    K.glow(c, m, col(glowc), 14, 1.4)
    K.shadow(c, m, 5, 8, 8, 160)
    K.fill(c, K.soften(m), lin(*body))
    e = poly([(eye[0] - 0.05, eye[1]), (eye[0] + 0.04, eye[1] - 0.025), (eye[0] + 0.03, eye[1] + 0.015)])
    lit(c, e, eyec, (255, 255, 230), 8, 1.8)


def breath(c, mouth, colors, glowc, seed):
    mx, my = mouth
    cone = poly([(mx - 0.02, my), (1.0, my - 0.30), (1.0, my + 0.26)])
    K.glow(c, cone, col(glowc), 24, 1.4)
    K.fill(c, K.soften(cone, 10), K.linear(col(colors[0]), col(colors[1]) [:3] + (120,), 0))
    core = poly([(mx - 0.02, my), (1.0, my - 0.14), (1.0, my + 0.12)])
    K.fill(c, K.soften(core, 8), col(colors[0]))


def smiting_breath():
    """The wyvern's blasting breath, white-hot at the jaw."""
    c = bg((70, 50, 160), (8, 4, 28), cx=0.7, cy=0.55)
    m, eye, mouth = wyvern_head(-0.10, 0.04, 1.0)
    breath(c, mouth, ((255, 250, 220), (255, 120, 40)), (255, 150, 60), 3)
    wyvern_paint(c, m, eye, (180, 170, 255))
    motes(c, 5, 12, (0.62, 0.30, 0.95, 0.80), (0.008, 0.018), (255, 240, 200), (255, 160, 80))
    return K.finish(c)


def restoring_breath():
    """The wyvern's healing breath: a stream of green light and crosses."""
    c = bg((40, 140, 100), (4, 24, 16), cx=0.7, cy=0.55)
    m, eye, mouth = wyvern_head(-0.10, 0.04, 1.0)
    breath(c, mouth, ((235, 255, 235), (90, 230, 130)), (130, 255, 170), 4)
    wyvern_paint(c, m, eye, (180, 255, 210), body=((130, 190, 220), (30, 70, 110)))
    plus = K.shape(lambda d: [d.rectangle(pts([(x - r * 0.3, y - r), (x + r * 0.3, y + r)]), fill=255)
                              for x, y, r in ((0.80, 0.30, 0.07), (0.86, 0.72, 0.05))]
                   + [d.rectangle(pts([(x - r, y - r * 0.3), (x + r, y + r * 0.3)]), fill=255)
                      for x, y, r in ((0.80, 0.30, 0.07), (0.86, 0.72, 0.05))])
    lit(c, plus, (160, 255, 170), (245, 255, 245), 10, 1.5)
    return K.finish(c)


def dismiss():
    """The wyvern sent away: it fades into drifting scales of light."""
    c = bg((110, 70, 150), (14, 6, 26), cy=0.5)
    m, eye, mouth = wyvern_head(0.14, 0.02, 0.88)
    fade = grad_mask(0.10, 0.50, 0)
    mm = inter(m, fade)
    K.glow(c, mm, (210, 180, 255, 255), 14, 1.3)
    K.fill(c, K.soften(mm), lin((150, 170, 230), (50, 50, 120)))
    e = poly([(eye[0] - 0.05, eye[1]), (eye[0] + 0.04, eye[1] - 0.025), (eye[0] + 0.03, eye[1] + 0.015)])
    lit(c, e, (255, 230, 120), (255, 255, 230), 8, 1.8)
    motes(c, 23, 30, (0.06, 0.20, 0.40, 0.90), (0.008, 0.024), (235, 225, 255), (170, 140, 255))
    arrow_path(c, [(0.70, 0.84), (0.50, 0.86), (0.26, 0.84)], 0.02, 0.05, 0.09, (220, 200, 255), (245, 240, 255),
               8, 1.2, sh=False)
    return K.finish(c)


def wing_m(cx, cy, s, ang=0.0):
    def q(seq):
        a = math.radians(ang)
        return [(cx + (x * math.cos(a) - y * math.sin(a)) * s, cy + (x * math.sin(a) + y * math.cos(a)) * s)
                for x, y in seq]
    memb = q([(-0.32, 0.30), (-0.06, -0.40), (0.42, -0.32), (0.08, -0.25), (0.44, -0.04), (0.06, -0.06),
              (0.32, 0.26), (-0.02, 0.12), (-0.10, 0.34)])
    bones = [q([(-0.32, 0.30), (-0.06, -0.40)]), q([(-0.06, -0.40), (0.42, -0.32)]),
             q([(-0.06, -0.40), (0.44, -0.04)]), q([(-0.06, -0.40), (0.32, 0.26)])]
    return poly(memb), K.shape(lambda d: [stroke(d, b, 0.05, 0.016) for b in bones])


def steady_wing():
    """A wyvern wing folded to guard, a stone ward over it."""
    c = bg((150, 110, 50), (26, 16, 4), cy=0.5)
    memb, bones = wing_m(0.44, 0.50, 0.95)
    lit(c, memb, (255, 210, 150), K.radial((130, 170, 240, 255), (30, 40, 110, 255), 0.6, 0.4, 0.5), 16, 1.3,
        sh=True)
    lit(c, bones, (255, 230, 180), lin((255, 246, 220), (210, 180, 130)), 6, 1.0)
    sp = GD.shield_pts(0.70, 0.56, 0.14, 0.34)
    lit(c, poly(sp), (255, 220, 140), lin((255, 236, 170), (190, 130, 50)), 18, 1.5, sh=True)
    inner = poly(GD.shield_pts(0.70, 0.585, 0.11, 0.28))
    K.fill(c, K.soften(inner), lin((200, 140, 70), (110, 66, 30)))
    sparkles(c, [(0.20, 0.80, 0.07)], glowc=(255, 220, 150))
    return K.finish(c)


# ---- PUP -----------------------------------------------------------------------------------------------------------
def power_glyph(c, paint, glowc, gr=22):
    ring = K.shape(lambda d: stroke(d, arc_path(0.5, 0.53, 0.22, 0.22, -55, 235), 0.085))
    bar = K.shape(lambda d: stroke(d, [(0.5, 0.18), (0.5, 0.46)], 0.085))
    lit(c, lighter(ring, bar), glowc, paint, gr, 1.4, sh=True)


def deactivate():
    """The automaton switched off: a dimmed power glyph struck through."""
    c = bg((150, 40, 50), (24, 4, 8), cy=0.5)
    g = K.shape(lambda d: GD.gear(d, 0.5, 0.5, 0.44, 0.37, 14, hole=0.33))
    K.fill(c, scale(K.soften(g, 2), 0.3), (255, 140, 140, 255))
    power_glyph(c, lin((200, 190, 200), (110, 100, 120)), (120, 40, 50), 10)
    sl = K.shape(lambda d: stroke(d, [(0.20, 0.80), (0.80, 0.20)], 0.075))
    lit(c, sl, (255, 80, 60), lin((255, 140, 120), (220, 40, 30)), 14, 1.5, sh=True)
    return K.finish(c)


def retrieve():
    """The automaton recalled: a gear with an arrow sweeping back home."""
    c = bg((60, 150, 90), (4, 26, 12), cy=0.5)
    g = K.shape(lambda d: GD.gear(d, 0.60, 0.44, 0.24, 0.18, 10, hole=0.08))
    K.glow(c, g, (170, 255, 190, 255), 18, 1.2)
    K.shadow(c, g, 5, 8, 8, 150)
    K.fill(c, K.soften(g), K.radial((230, 214, 170, 255), (130, 100, 60, 255), 0.55, 0.38, 0.3))
    path = arc_path(0.50, 0.50, 0.34, 0.32, 20, 160)
    arrow_path(c, path, 0.03, 0.08, 0.15, (200, 255, 210), lin((250, 255, 250), (160, 230, 180)), 12, 1.4)
    return K.finish(c)


def maneuver():
    """An elemental maneuver: a burning element orb held in a ring of cogs (painted fire; variants per element)."""
    c = bg((210, 60, 24), (34, 6, 4), cy=0.5)
    rays(c, 0.5, 0.5, 16, (255, 200, 140), alpha=90, phase=0.1)
    g = K.shape(lambda d: GD.gear(d, 0.5, 0.5, 0.42, 0.35, 16, hole=0.29))
    K.glow(c, g, (255, 120, 50, 255), 16, 1.2)
    K.shadow(c, g, 5, 8, 8, 150)
    K.fill(c, K.soften(g), lin((255, 170, 110), (150, 50, 20)))
    edge = minus(g, K.shape(lambda d: GD.gear(d, 0.5, 0.5, 0.40, 0.33, 16, hole=0.31)))
    K.fill(c, K.soften(edge), (255, 220, 170, 200))
    spirit(c, 0.5, 0.5, 0.18, (255, 90, 30), (255, 120, 40), 26)
    arr = K.shape(lambda d: [stroke(d, arc_path(0.5, 0.5, 0.25, 0.25, a, a + 70), 0.025, 0.045) for a in (200, 20)]
                  + [arrowhead(d, *arc_path(0.5, 0.5, 0.25, 0.25, a + 82, a + 82, 1)[0], a + 82 + 95, 0.07)
                     for a in (200, 20)])
    lit(c, arr, (255, 240, 200), (255, 250, 235), 8, 1.4)
    return K.finish(c)


# ---- DNC -----------------------------------------------------------------------------------------------------------
def samba_swirl(c, glowc, paint):
    sw = K.shape(lambda d: [stroke(d, arc_path(0.5, 0.54, 0.36, 0.30, 200, 330), 0.02, 0.06),
                            stroke(d, arc_path(0.5, 0.54, 0.36, 0.30, 20, 150), 0.02, 0.06)])
    hd = K.shape(lambda d: [arrowhead(d, *arc_path(0.5, 0.54, 0.36, 0.30, 345, 345, 1)[0], 100, 0.11),
                            arrowhead(d, *arc_path(0.5, 0.54, 0.36, 0.30, 165, 165, 1)[0], 280, 0.11)])
    lit(c, lighter(sw, hd), glowc, paint, 14, 1.7)


def aspir_samba():
    """Each blow drinks MP: a mana drop inside the samba's swirl."""
    c = bg((30, 70, 170), (2, 8, 30), cy=0.5)
    samba_swirl(c, (120, 180, 255), (210, 230, 255))
    drop = poly(GD.drop_pts(0.5, 0.16, 0.80, 0.20))
    lit(c, drop, (80, 140, 255), K.radial((190, 230, 255, 255), (20, 60, 200, 255), 0.44, 0.55, 0.3), 22, 1.4,
        sh=True)
    K.fill(c, K.soften(ell(0.40, 0.52, 0.46, 0.64), 3), (240, 250, 255, 200))
    return K.finish(c)


def haste_samba():
    """Quicker blows: speed chevrons inside the samba's swirl."""
    c = bg((150, 170, 40), (20, 26, 2), cy=0.5)
    samba_swirl(c, (230, 255, 140), (250, 255, 220))
    ch = K.shape(lambda d: [stroke(d, [(x, 0.36), (x + 0.12, 0.52), (x, 0.68)], 0.07) for x in (0.34, 0.50)])
    lit(c, ch, (255, 250, 140), lin((255, 255, 240), (240, 210, 60)), 16, 1.5, sh=True)
    return K.finish(c)


def healing_waltz():
    """A cleansing waltz: a bright note scattering the dark motes of ailments."""
    c = bg((130, 90, 190), (18, 8, 34), cy=0.5)
    motes(c, 61, 14, (0.10, 0.10, 0.90, 0.90), (0.014, 0.03), (60, 20, 70), None, 230)
    rays(c, 0.5, 0.5, 14, (255, 240, 255), alpha=110, width=0.05)
    ring = K.shape(lambda d: d.ellipse(pts([(0.20, 0.20), (0.80, 0.80)]), outline=255, width=int(0.02 * W)))
    lit(c, ring, (230, 200, 255), (245, 235, 255), 10, 1.3)
    nt = K.shape(lambda d: GB.note(d, 0.44, 0.66, 0.78, 1))
    lit(c, nt, (255, 230, 255), lin((255, 255, 255), (220, 190, 250)), 20, 1.5, sh=True)
    sparkles(c, [(0.70, 0.30, 0.08), (0.28, 0.32, 0.05)], glowc=(240, 200, 255))
    return K.finish(c)


def feet(c, glowc, paint, lx=0.38, ly=0.58, rx=0.62, ry=0.42, s=0.95, la=10, ra=-10):
    left = rot(K.shape(lambda d: GD.foot(d, lx, ly, s, -1)), la, lx, ly)
    right = rot(K.shape(lambda d: GD.foot(d, rx, ry, s, 1)), ra, rx, ry)
    m = lighter(left, right)
    lit(c, m, glowc, paint, 14, 1.3, sh=True)
    return m


def quickstep():
    """Quick feet leaving speed lines behind."""
    c = bg((40, 120, 210), (2, 12, 36), cy=0.5)
    st = K.mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.36, 0.10), (0.50, 0.06), (0.64, 0.12), (0.78, 0.18)):
        sd.rounded_rectangle(pts([(x0, y - 0.016), (0.36, y + 0.016)]), radius=0.016 * W, fill=180)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (210, 235, 255, 255))
    feet(c, (170, 220, 255), lin((255, 255, 255), (170, 210, 250)), 0.42, 0.60, 0.66, 0.42, 0.78, -25, -25)
    return K.finish(c)


def stutter_step():
    """A stutter in the step: the feet shake in jittering echoes."""
    c = bg((150, 50, 160), (22, 4, 28), cy=0.5)
    for dx, a in ((-0.07, 70), (0.07, 70)):
        g = lighter(rot(K.shape(lambda d, dx=dx: GD.foot(d, 0.38 + dx, 0.58, 0.95, -1)), 10, 0.38 + dx, 0.58),
                    rot(K.shape(lambda d, dx=dx: GD.foot(d, 0.62 + dx, 0.42, 0.95, 1)), -10, 0.62 + dx, 0.42))
        K.fill(c, scale(K.soften(g, 3), a / 255), (255, 170, 250, 255))
    feet(c, (255, 160, 240), lin((255, 250, 255), (230, 170, 230)))
    zz = K.shape(lambda d: [stroke(d, [(0.10, 0.22), (0.16, 0.14), (0.20, 0.24), (0.26, 0.15)], 0.025),
                            stroke(d, [(0.74, 0.86), (0.80, 0.76), (0.84, 0.86), (0.90, 0.77)], 0.025)])
    lit(c, zz, (255, 200, 255), (255, 240, 255), 8, 1.4)
    return K.finish(c)


def feather_pts(cx, cy, L, wdt, ang):
    a = math.radians(ang)
    u, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    q = []
    for i in range(21):
        t = i / 20
        w = wdt * math.sin(math.pi * min(1, t * 1.1)) ** 0.7
        q.append((t, w))
    side1 = [(cx + u[0] * (t - 0.5) * L + n[0] * w, cy + u[1] * (t - 0.5) * L + n[1] * w) for t, w in q]
    side2 = [(cx + u[0] * (t - 0.5) * L - n[0] * w, cy + u[1] * (t - 0.5) * L - n[1] * w) for t, w in q]
    quill = [(cx - u[0] * 0.5 * L, cy - u[1] * 0.5 * L), (cx + u[0] * 0.5 * L, cy + u[1] * 0.5 * L)]
    return side1 + side2[::-1], quill


def feather_step():
    """A light step marked by a feather: crits come easy."""
    c = bg((40, 150, 160), (2, 22, 26), cy=0.5)
    fp = rot(K.shape(lambda d: GD.foot(d, 0.40, 0.56, 1.05, -1)), 14, 0.40, 0.56)
    lit(c, fp, (170, 255, 250), lin((255, 255, 255), (170, 230, 230)), 14, 1.3, sh=True)
    body, quill = feather_pts(0.64, 0.48, 0.62, 0.10, -60)
    fm = poly(body)
    cuts = K.shape(lambda d: [stroke(d, [(0.64 + 0.04 * k, 0.48 - 0.07 * k), (0.70 + 0.04 * k, 0.50 - 0.06 * k)],
                                     0.012) for k in (-2, 1, 3)])
    fm = minus(fm, cuts)
    lit(c, fm, (255, 255, 240), lin((255, 255, 250), (210, 236, 240)), 16, 1.4, sh=True)
    qm = K.shape(lambda d: stroke(d, quill, 0.014, 0.006))
    K.fill(c, K.soften(qm), (120, 160, 170, 255))
    sparkles(c, [(0.82, 0.20, 0.07)], glowc=(200, 255, 250))
    return K.finish(c)


def spectral_jig():
    """A ghostly jig: translucent footsteps vanishing into the dark (sneak and invisible)."""
    c = bg((60, 70, 140), (4, 6, 22), cy=0.5)
    for (x, y, s, a, m, alpha) in ((0.30, 0.76, 0.62, 15, -1, 90), (0.46, 0.58, 0.74, 5, 1, 170),
                                   (0.60, 0.36, 0.88, -5, -1, 255)):
        f = rot(K.shape(lambda d, x=x, y=y, s=s, m=m: GD.foot(d, x, y, s, m)), a, x, y)
        K.glow(c, scale(f, alpha / 255), (150, 190, 255, 255), 18, 1.6)
        K.fill(c, scale(K.soften(f, 2), alpha / 255), (230, 240, 255, 255))
    motes(c, 33, 18, (0.15, 0.10, 0.90, 0.90), (0.006, 0.014), (220, 230, 255), (140, 170, 255))
    sparkles(c, [(0.78, 0.22, 0.09), (0.22, 0.30, 0.05)], glowc=(160, 190, 255))
    return K.finish(c)


def chocobo_jig():
    """A chocobo's three-toed tracks racing ahead, a yellow feather on the wind."""
    c = bg((70, 150, 60), (6, 24, 4), cy=0.5)

    def track(d, x, y, s, a):
        r = math.radians(a)
        for da in (-28, 0, 28):
            aa = r + math.radians(da)
            stroke(d, [(x, y), (x + math.cos(aa) * 0.17 * s, y + math.sin(aa) * 0.17 * s)], 0.05 * s, 0.045 * s)
        stroke(d, [(x, y), (x - math.cos(r) * 0.09 * s, y - math.sin(r) * 0.09 * s)], 0.07 * s, 0.045 * s)
    tr = K.shape(lambda d: [track(d, 0.20, 0.60, 0.9, -45), track(d, 0.42, 0.80, 0.9, -45)])
    lit(c, tr, (255, 240, 150), lin((255, 250, 220), (230, 190, 90)), 12, 1.3, sh=True)
    body, quill = feather_pts(0.68, 0.32, 0.46, 0.10, -40)
    fm = poly(body)
    lit(c, fm, (255, 230, 80), lin((255, 250, 160), (240, 170, 20)), 18, 1.5, sh=True)
    qm = K.shape(lambda d: stroke(d, quill, 0.014, 0.006))
    K.fill(c, K.soften(qm), (170, 110, 20, 255))
    sparkles(c, [(0.80, 0.66, 0.07)], glowc=(255, 240, 150))
    return K.finish(c)


def ribbon(c, glowc, paint, a0=150, rx=0.38, ry=0.30, cy=0.5):
    rib = K.shape(lambda d: stroke(d, [(0.5 + math.cos(math.radians(a0 + t * 4.2)) * (rx - t * 0.0012),
                                        cy + math.sin(math.radians(a0 + t * 4.2)) * (ry - t * 0.0010))
                                       for t in range(0, 61, 2)], 0.025, 0.07))
    lit(c, rib, glowc, paint, 10, 1.2)


def fm_orbs(c, n=3, color=(255, 250, 220), glowc=(255, 240, 180), y=0.84):
    xs = [0.5 + (i - (n - 1) / 2) * 0.12 for i in range(n)]
    o = K.shape(lambda d: [d.ellipse(pts([(x - 0.035, y - 0.035), (x + 0.035, y + 0.035)]), fill=255) for x in xs])
    lit(c, o, glowc, color, 8, 1.4)


def animated_flourish():
    """A taunting flourish: the ribbon whirls around a blazing '!'."""
    c = bg((200, 40, 40), (34, 4, 6), cy=0.48)
    ribbon(c, (255, 200, 120), lin((255, 220, 140), (230, 140, 40), 0))
    burst = K.shape(lambda d: star(d, 0.5, 0.46, 0.30, 0.17, 12))
    lit(c, burst, (255, 120, 60), K.radial((255, 230, 140, 255), (240, 80, 40, 255), 0.5, 0.46, 0.3), 20, 1.3)
    mark = K.shape(lambda d: [d.rounded_rectangle(pts([(0.455, 0.27), (0.545, 0.53)]), radius=0.03 * W, fill=255),
                              d.ellipse(pts([(0.45, 0.57), (0.55, 0.67)]), fill=255)])
    lit(c, mark, None, (255, 252, 240), sh=True)
    return K.finish(c)


def desperate_flourish():
    """A crushing flourish: a heavy weight drives the foe down (gravity)."""
    c = bg((110, 80, 60), (18, 10, 6), cy=0.45)
    ribbon(c, (255, 190, 150), lin((255, 200, 170), (200, 90, 60), 0), a0=170)
    wt = poly([(0.36, 0.28), (0.64, 0.28), (0.72, 0.58), (0.28, 0.58)])
    lit(c, wt, (200, 170, 255), lin((150, 130, 190), (50, 40, 80)), 18, 1.3, sh=True)
    hand = K.shape(lambda d: d.ellipse(pts([(0.42, 0.16), (0.58, 0.30)]), outline=255, width=int(0.03 * W)))
    lit(c, hand, None, (170, 150, 210))
    arr = K.shape(lambda d: [stroke(d, [(0.5, 0.36), (0.5, 0.48)], 0.06), arrowhead(d, 0.5, 0.56, 90, 0.10)])
    lit(c, arr, (255, 230, 200), (255, 245, 230), 8, 1.4)
    fm_orbs(c, 3, (255, 230, 200), (255, 190, 150), 0.80)
    return K.finish(c)


def violent_flourish():
    """A stunning flourish: lightning cracks out of the dancer's star."""
    c = bg((90, 60, 190), (8, 4, 34), cy=0.48)
    ribbon(c, (255, 240, 140), lin((255, 250, 180), (230, 190, 40), 0))
    st = K.shape(lambda d: star(d, 0.5, 0.48, 0.24, 0.10, 4, -45))
    K.glow(c, st, (200, 200, 255, 255), 16, 1.2)
    b = poly(bolt_pts(0.5, 0.48, 1.05))
    lit(c, b, (255, 240, 120), lin((255, 255, 240), (255, 210, 60)), 20, 1.8, sh=True)
    sparkles(c, [(0.24, 0.24, 0.06), (0.78, 0.74, 0.06)], glowc=(255, 240, 140))
    return K.finish(c)


def reverse_flourish():
    """Finishing moves turned back into TP: orbs spiral inward into a glowing core."""
    c = bg((30, 140, 150), (2, 22, 26), cy=0.5)
    path = [(0.5 + math.cos(math.radians(30 - t * 6)) * (0.36 - t * 0.0045),
             0.5 + math.sin(math.radians(30 - t * 6)) * (0.36 - t * 0.0045)) for t in range(0, 51, 2)]
    arrow_path(c, path, 0.02, 0.07, 0.11, (160, 255, 240), lin((240, 255, 255), (120, 220, 220)), 12, 1.4)
    for k, a in enumerate((80, 140, 200)):
        x, y = 0.5 + math.cos(math.radians(a)) * 0.34, 0.5 + math.sin(math.radians(a)) * 0.34
        o = ell(x - 0.045, y - 0.045, x + 0.045, y + 0.045)
        lit(c, o, (255, 240, 180), (255, 250, 220), 8, 1.4)
    spirit(c, 0.5, 0.5, 0.10, (120, 240, 230), (160, 255, 240), 20)
    return K.finish(c)


def building_flourish():
    """Finishing moves stacked into a rising surge for the next weapon skill."""
    c = bg((220, 120, 30), (40, 14, 2), cy=0.5)
    ribbon(c, (255, 220, 160), lin((255, 240, 200), (240, 150, 60), 0), a0=160)
    for k, y in enumerate((0.76, 0.62, 0.48)):
        o = ell(0.5 - 0.06, y - 0.06, 0.5 + 0.06, y + 0.06)
        lit(c, o, (255, 230, 150), K.radial((255, 255, 240, 255), (255, 190, 60, 255), 0.48, y - 0.02, 0.07), 10,
            1.5)
    arr = K.shape(lambda d: arrowhead(d, 0.5, 0.14, -90, 0.16))
    lit(c, arr, (255, 240, 160), lin((255, 255, 230), (255, 200, 80)), 14, 1.6, sh=True)
    return K.finish(c)


def wild_flourish():
    """Setting up the skillchain: a star shattered into prismatic shards."""
    c = bg((40, 160, 90), (2, 26, 10), cy=0.5)
    ribbon(c, (200, 255, 200), lin((230, 255, 230), (100, 210, 140), 0), a0=130)
    for i, rgb in enumerate(GD.ELEM_RGB):
        a = math.pi * 2 * i / 8 - math.pi / 2 + 0.3
        x, y = 0.5 + math.cos(a) * 0.30, 0.48 + math.sin(a) * 0.30
        sh = poly([(x + math.cos(a) * 0.06, y + math.sin(a) * 0.06), (x + math.cos(a + 2.2) * 0.035,
                   y + math.sin(a + 2.2) * 0.035), (x + math.cos(a - 2.2) * 0.035, y + math.sin(a - 2.2) * 0.035)])
        lit(c, sh, rgb, (255, 255, 255), 8, 1.8)
        K.fill(c, K.soften(sh), col(rgb)[:3] + (150,))
    st = K.shape(lambda d: star(d, 0.5, 0.48, 0.22, 0.09, 5))
    lit(c, st, (255, 255, 200), K.radial((255, 255, 240, 255), (200, 240, 160, 255), 0.5, 0.44, 0.24), 20, 1.6,
        sh=True)
    return K.finish(c)


def striking_flourish():
    """A doubled strike: two stars flash in one flourish (double attack)."""
    c = bg((200, 60, 100), (34, 4, 16), cy=0.5)
    ribbon(c, (255, 200, 220), lin((255, 230, 240), (230, 110, 150), 0))
    st = K.shape(lambda d: [star(d, 0.38, 0.40, 0.19, 0.08, 5), star(d, 0.62, 0.58, 0.19, 0.08, 5)])
    lit(c, st, (255, 220, 120), K.radial((255, 255, 220, 255), (240, 160, 40, 255), 0.5, 0.45, 0.35), 20, 1.5,
        sh=True)
    return K.finish(c)


def ternary_flourish():
    """A tripled strike: three stars flash in one flourish (triple attack)."""
    c = bg((120, 50, 190), (16, 4, 32), cy=0.5)
    ribbon(c, (230, 200, 255), lin((245, 230, 255), (170, 110, 230), 0))
    st = K.shape(lambda d: [star(d, 0.5, 0.32, 0.16, 0.07, 5), star(d, 0.32, 0.62, 0.16, 0.07, 5),
                            star(d, 0.68, 0.62, 0.16, 0.07, 5)])
    lit(c, st, (255, 220, 120), K.radial((255, 255, 220, 255), (240, 160, 40, 255), 0.5, 0.45, 0.35), 20, 1.5,
        sh=True)
    return K.finish(c)


# ---- SCH: stratagems as a light (white page) / dark (dark page) pair ----------------------------------------------
LIGHT_INK = (K.radial((255, 255, 235, 255), (255, 170, 30, 255), 0.5, 0.30, 0.3), (255, 230, 120))
DARK_INK = (K.radial((255, 248, 255, 255), (190, 130, 255, 255), 0.5, 0.30, 0.3), (210, 150, 255))


def move(m, sx, sy, dx, dy, s):
    """Scale mask m by s about unit point (sx, sy), landing it at (dx, dy)."""
    return m.transform((W, W), Image.AFFINE, (1 / s, 0, (sx - dx / s) * W, 0, 1 / s, (sy - dy / s) * W),
                       resample=Image.BICUBIC)


def strat(light, c0, c1, emblem):
    def painter():
        c = bg(c0, c1, cy=0.36)
        if light:
            rays(c, 0.5, 0.30, 16, (255, 250, 220), alpha=110)
            GD.open_book(K.linear((255, 255, 250, 255), (236, 226, 200, 255), 0),
                         K.linear((236, 226, 200, 255), (255, 255, 250, 255), 0), c, (255, 240, 180), top=0.64,
                         hw=0.30, h=0.17, cover_col=(150, 90, 40))
        else:
            rays(c, 0.5, 0.30, 12, (170, 110, 230), alpha=80)
            GD.open_book(K.linear((70, 50, 110, 255), (150, 120, 200, 255), 0),
                         K.linear((150, 120, 200, 255), (70, 50, 110, 255), 0), c, (210, 150, 255), top=0.64,
                         hw=0.30, h=0.17, cover_col=(20, 10, 30))
        paint, glowc = LIGHT_INK if light else DARK_INK
        m = move(emblem(), 0.5, 0.27, 0.5, 0.34, 1.3)
        lit(c, m, glowc, paint, 18, 1.7, sh=True)
        return K.finish(c)
    return painter


def em_half_drop():
    """An MP drop cut in half (Penury / Parsimony: half the MP cost)."""
    d = poly(GD.drop_pts(0.5, 0.08, 0.46, 0.15))
    hollow = minus(d, poly(GD.drop_pts(0.5, 0.14, 0.42, 0.11)))
    left = inter(d, poly([(0, 0), (0.49, 0), (0.49, 1), (0, 1)]))
    return lighter(left, hollow)


def em_fast():
    """Fast-forward chevrons (Celerity / Alacrity: faster casting)."""
    return K.shape(lambda d: [stroke(d, [(x, 0.12), (x + 0.12, 0.27), (x, 0.42)], 0.075) for x in (0.32, 0.50)])


def em_burst():
    """A potent burst (Rapture: heal / Ebullience: damage)."""
    return K.shape(lambda d: [star(d, 0.5, 0.27, 0.21, 0.08, 8, -90), star(d, 0.5, 0.27, 0.12, 0.05, 8, -67.5)])


def em_area():
    """A dot and its spreading rings (Accession / Manifestation: area of effect)."""
    return K.shape(lambda d: [d.ellipse(pts([(0.45, 0.22), (0.55, 0.32)]), fill=255)]
                   + [d.ellipse(pts([(0.5 - r, 0.27 - r * 0.8), (0.5 + r, 0.27 + r * 0.8)]), outline=255,
                                width=int(0.03 * W)) for r in (0.12, 0.21)])


def em_plus_page():
    """A new page with a plus (Addendum)."""
    page = K.shape(lambda d: d.rounded_rectangle(pts([(0.38, 0.07), (0.62, 0.43)]), radius=0.02 * W, fill=255))
    plus = K.shape(lambda d: [d.rectangle(pts([(0.475, 0.14), (0.525, 0.36)]), fill=255),
                              d.rectangle(pts([(0.39, 0.225), (0.61, 0.275)]), fill=255)])
    return lighter(minus(page, plus), scale(plus, 0.0))


def em_reticle():
    """A crosshair (Altruism / Focalization: accuracy)."""
    return K.shape(lambda d: [d.ellipse(pts([(0.35, 0.12), (0.65, 0.42)]), outline=255, width=int(0.032 * W)),
                              d.ellipse(pts([(0.47, 0.24), (0.53, 0.30)]), fill=255)]
                   + [d.line(pts([(0.5 + dx * 0.08, 0.27 + dy * 0.08), (0.5 + dx * 0.21, 0.27 + dy * 0.21)]),
                             fill=255, width=int(0.032 * W)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))])


def em_calm():
    """A down arrow over still water (Tranquility / Equanimity: less enmity)."""
    return K.shape(lambda d: [stroke(d, [(0.5, 0.06), (0.5, 0.24)], 0.07), arrowhead(d, 0.5, 0.36, 90, 0.13),
                              stroke(d, [(0.30 + 0.02 * i, 0.43 + 0.012 * math.sin(i * 1.3)) for i in range(21)],
                                     0.03)])


def em_infinity():
    """An infinity loop (Perpetuance: lasting enhancement)."""
    return K.shape(lambda d: stroke(d, [(0.5 + 0.20 * math.cos(t) / (1 + math.sin(t) ** 2),
                                         0.27 + 0.20 * math.sin(t) * math.cos(t) / (1 + math.sin(t) ** 2))
                                        for t in [math.pi * 2 * i / 80 for i in range(81)]], 0.05))


def em_chain():
    """Two linked chain rings (Immanence: a spell for the skillchain)."""
    a = K.shape(lambda d: d.ellipse(pts([(0.27, 0.17), (0.53, 0.37)]), outline=255, width=int(0.045 * W)))
    b = K.shape(lambda d: d.ellipse(pts([(0.47, 0.17), (0.73, 0.37)]), outline=255, width=int(0.045 * W)))
    a = rot(a, 25, 0.40, 0.27)
    b = rot(b, 25, 0.60, 0.27)
    gap = rot(poly([(0.44, 0.13), (0.50, 0.13), (0.50, 0.21), (0.44, 0.21)]), 25, 0.40, 0.27)
    return lighter(minus(a, gap), b)


# ---- RUN -----------------------------------------------------------------------------------------------------------
def rune_mark(c, cx, cy, s, glowc, w=0.06, paint=(255, 245, 220)):
    g = K.shape(lambda d: GD.rune_glyph(d, cx, cy, s, w))
    K.glow(c, g, col(glowc), 12, 1.8)
    K.fill(c, K.soften(g), col(paint))


def pflug():
    """A warding circle of runes around a central rune: status resistance up."""
    c = bg((60, 160, 90), (4, 26, 12), cy=0.5)
    ring = K.shape(lambda d: [d.ellipse(pts([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=int(0.03 * W)),
                              d.ellipse(pts([(0.22, 0.22), (0.78, 0.78)]), outline=255, width=int(0.014 * W))]
                   + [d.line(pts([(0.5 + math.cos(a) * 0.30, 0.5 + math.sin(a) * 0.30),
                                  (0.5 + math.cos(a) * 0.36, 0.5 + math.sin(a) * 0.36)]), fill=255,
                             width=int(0.02 * W)) for a in [math.pi * 2 * i / 12 for i in range(12)]])
    lit(c, ring, (150, 255, 170), (220, 255, 225), 14, 1.5)
    disc = ell(0.26, 0.26, 0.74, 0.74)
    K.fill(c, scale(K.soften(disc, 10), 0.4), (160, 255, 180, 255))
    rune_mark(c, 0.5, 0.5, 0.72, (120, 255, 150), 0.065)
    return K.finish(c)


def liement():
    """Elements drawn into the shield and drunk away: absorb elemental damage."""
    c = bg((200, 140, 40), (36, 20, 4), cy=0.5)
    for i, a in enumerate((200, 250, 290, 340)):
        r = math.radians(a)
        x0, y0 = 0.5 + math.cos(r) * 0.44, 0.52 + math.sin(r) * 0.44
        x1, y1 = 0.5 + math.cos(r) * 0.26, 0.52 + math.sin(r) * 0.26
        rgb = GD.ELEM_RGB[(i * 2) % 8]
        arrow_path(c, [(x0, y0), (x1 + (x0 - x1) * 0.4, y1 + (y0 - y1) * 0.4), (x1, y1)], 0.02, 0.045, 0.08,
                   rgb, (255, 250, 235), 10, 1.6, sh=False)
    GD.shield_paint(c, 0.5, 0.26, 0.20, 0.60, (255, 220, 140), K.linear((240, 160, 60, 255), (120, 60, 10, 255), 90))
    return K.finish(c)


def battuta():
    """A parrying blade: the blow turned aside in a burst of sparks."""
    c = bg((170, 40, 120), (28, 4, 22), cy=0.5)
    burst = K.shape(lambda d: star(d, 0.66, 0.34, 0.20, 0.06, 8, -20))
    lit(c, burst, (255, 220, 140), K.radial((255, 255, 230, 255), (255, 170, 60, 255), 0.66, 0.34, 0.2), 16, 1.6)
    other = rot(K.shape(lambda d: GD.sword(d, 0.5, 0.06, 0.90, 0.035)), 60, 0.5, 0.5)
    K.fill(c, scale(K.soften(other, 3), 0.5), (255, 200, 230, 255))
    s = rot(K.shape(lambda d: GD.sword(d, 0.5, 0.08, 0.92, 0.05)), -30, 0.5, 0.5)
    lit(c, s, (255, 180, 230), K.linear((255, 255, 255, 255), (160, 160, 190, 255), 30), 14, 1.2, sh=True)
    arc = K.shape(lambda d: stroke(d, arc_path(0.5, 0.5, 0.40, 0.40, 200, 260), 0.012, 0.04))
    lit(c, arc, (255, 200, 240), (255, 240, 250), 8, 1.4)
    return K.finish(c)


def swipe():
    """A single rune spent in one sweeping slash."""
    c = bg((40, 110, 190), (4, 12, 34), cy=0.5)
    sl = K.shape(lambda d: stroke(d, arc_path(0.42, 0.62, 0.40, 0.40, 190, 320), 0.012, 0.09))
    lit(c, sl, (150, 210, 255), lin((255, 255, 255), (150, 200, 255), 0), 18, 1.5)
    stone = poly([(0.56, 0.36), (0.80, 0.33), (0.86, 0.58), (0.80, 0.82), (0.58, 0.84), (0.52, 0.60)])
    lit(c, stone, (120, 190, 255), lin((140, 150, 190), (50, 50, 80), 60), 14, 1.3, sh=True)
    rune_mark(c, 0.69, 0.59, 0.55, (110, 180, 255), 0.05)
    return K.finish(c)


def lunge():
    """Every rune spent at once: a thrust that bursts into the elements."""
    c = bg((190, 70, 30), (32, 8, 4), cy=0.4)
    rays(c, 0.70, 0.30, 14, (255, 220, 170), alpha=90)
    burst = K.shape(lambda d: star(d, 0.70, 0.30, 0.26, 0.11, 10))
    lit(c, burst, (255, 160, 80), K.radial((255, 255, 230, 255), (255, 120, 40, 255), 0.70, 0.30, 0.26), 18, 1.4)
    s = rot(K.shape(lambda d: GD.sword(d, 0.5, 0.08, 0.92, 0.055)), -45, 0.5, 0.5)
    lit(c, s, (255, 220, 170), K.linear((255, 255, 255, 255), (160, 160, 190, 255), 30), 12, 1.2, sh=True)
    for k, rgb in enumerate(((140, 215, 255), (110, 230, 110), (255, 90, 50))):
        a = math.radians(-160 + k * 55)
        x, y = 0.70 + math.cos(a) * 0.0 + (k - 1) * 0.15, 0.30 - 0.18 + abs(k - 1) * 0.12
        o = ell(x - 0.05, y - 0.05, x + 0.05, y + 0.05)
        lit(c, o, rgb, K.radial((255, 255, 255, 255), col(rgb), x - 0.012, y - 0.012, 0.05), 10, 1.6)
    return K.finish(c)


def gambit():
    """The foe's elemental guard broken: a shield split by a rune."""
    c = bg((110, 50, 170), (14, 4, 28), cy=0.5)
    sp = GD.shield_pts(0.5, 0.18, 0.24, 0.66)
    sh = poly(sp)
    crack = poly([(0.46, 0.10), (0.56, 0.10), (0.50, 0.34), (0.58, 0.50), (0.48, 0.90), (0.42, 0.90), (0.48, 0.52),
                  (0.40, 0.36)])
    lft = minus(inter(sh, poly([(0, 0), (0.52, 0), (0.52, 1), (0, 1)])), crack)
    rgt = minus(inter(sh, poly([(0.48, 0), (1, 0), (1, 1), (0.48, 1)])), crack)
    lft = rot(lft, 6, 0.4, 0.8)
    rgt = rot(rgt, -6, 0.6, 0.8)
    m = lighter(lft, rgt)
    lit(c, m, (200, 150, 255), lin((200, 190, 220), (90, 80, 110)), 12, 1.2, sh=True)
    inner = poly(GD.shield_pts(0.5, 0.23, 0.19, 0.56))
    K.fill(c, K.soften(inter(inner, m)), lin((110, 70, 170), (40, 20, 70)))
    K.glow(c, crack, (220, 160, 255, 255), 10, 1.0)
    rune_mark(c, 0.5, 0.52, 0.60, (220, 150, 255), 0.05)
    arr = K.shape(lambda d: [stroke(d, [(0.82, 0.18), (0.82, 0.34)], 0.05), arrowhead(d, 0.82, 0.44, 90, 0.09)])
    lit(c, arr, (255, 120, 140), (255, 200, 210), 8, 1.4)
    return K.finish(c)


def rayke():
    """A rune stone cracking apart: the foe's elemental resistance shattered."""
    c = bg((30, 140, 130), (2, 22, 20), cy=0.5)
    stone = poly([(0.34, 0.18), (0.66, 0.16), (0.74, 0.42), (0.70, 0.82), (0.32, 0.86), (0.26, 0.50)])
    crack = poly([(0.48, 0.12), (0.54, 0.12), (0.50, 0.34), (0.58, 0.52), (0.50, 0.90), (0.46, 0.90), (0.52, 0.52),
                  (0.44, 0.34)])
    lft = minus(inter(stone, poly([(0, 0), (0.52, 0), (0.52, 1), (0, 1)])), crack)
    rgt = minus(inter(stone, poly([(0.48, 0), (1, 0), (1, 1), (0.48, 1)])), crack)
    lft = ImageChops.offset(rot(lft, 8, 0.4, 0.8), -int(0.04 * W), 0)
    rgt = ImageChops.offset(rot(rgt, -8, 0.6, 0.8), int(0.04 * W), 0)
    K.glow(c, crack, (140, 255, 230, 255), 22, 1.5)
    lit(c, lighter(lft, rgt), (120, 255, 220), lin((150, 170, 160), (50, 60, 60), 60), 12, 1.2, sh=True)
    g = K.shape(lambda d: GD.rune_glyph(d, 0.5, 0.50, 0.75, 0.06))
    gl = ImageChops.offset(inter(g, poly([(0, 0), (0.5, 0), (0.5, 1), (0, 1)])), -int(0.04 * W), 0)
    gr = ImageChops.offset(inter(g, poly([(0.5, 0), (1, 0), (1, 1), (0.5, 1)])), int(0.04 * W), 0)
    lit(c, lighter(gl, gr), (100, 255, 210), (230, 255, 245), 12, 1.8)
    motes(c, 19, 12, (0.38, 0.10, 0.62, 0.90), (0.008, 0.018), (220, 255, 245), (120, 255, 220))
    return K.finish(c)


# ---- registry ------------------------------------------------------------------------------------------------------
# SCH pair colours: (light bg), (dark bg).
GREEN_L, GREEN_D = ((150, 200, 90), (20, 34, 8)), ((30, 120, 70), (2, 16, 8))
CYAN_L, CYAN_D = ((110, 210, 230), (10, 36, 44)), ((40, 90, 190), (2, 8, 30))
ROSE_L, ROSE_D = ((240, 150, 160), (50, 14, 20)), ((170, 30, 60), (24, 2, 10))
BLUE_L, BLUE_D = ((150, 180, 240), (16, 24, 50)), ((80, 60, 200), (6, 4, 30))
GOLD_L, GOLD_D = ((236, 190, 80), (60, 32, 8)), ((100, 44, 150), (8, 2, 16))
ORNG_L, ORNG_D = ((240, 150, 70), (54, 22, 6)), ((170, 70, 30), (24, 6, 2))
TEAL_L, TEAL_D = ((120, 220, 190), (10, 40, 32)), ((30, 120, 130), (2, 16, 20))
PURP_L = ((230, 210, 120), (50, 40, 10))

ICONS = {
    # BST
    ('ja', 'Fight'): fight,
    ('ja', 'Heel'): heel,
    ('ja', 'Leave'): leave,
    ('ja', 'Sic'): sic,
    ('ja', 'Stay'): stay,
    ('ja', 'Snarl'): snarl,
    ('ja', 'Ready'): ready,
    ('ja', 'Spur'): spur,
    ('ja', 'Run Wild'): run_wild,
    # SMN
    ('ja', 'Assault'): assault,
    ('ja', 'Retreat'): retreat,
    ('ja', 'Release'): release,
    ('ja', 'Blood Pact: Rage'): bp_rage,
    ('ja', 'Blood Pact: Ward'): bp_ward,
    ("ja", "Avatar's Favor"): avatars_favor,
    # DRG
    ('ja', 'Dismiss'): dismiss,
    ('ja', 'Steady Wing'): steady_wing,
    ('ja', 'Smiting Breath'): smiting_breath,
    ('ja', 'Restoring Breath'): restoring_breath,
    # PUP
    ('ja', 'Deactivate'): deactivate,
    ('ja', 'Retrieve'): retrieve,
    ('ja', 'Maneuver'): maneuver,
    # DNC
    ('ja', 'Aspir Samba'): aspir_samba,
    ('ja', 'Haste Samba'): haste_samba,
    ('ja', 'Healing Waltz'): healing_waltz,
    ('ja', 'Quickstep'): quickstep,
    ('ja', 'Stutter Step'): stutter_step,
    ('ja', 'Feather Step'): feather_step,
    ('ja', 'Animated Flourish'): animated_flourish,
    ('ja', 'Desperate Flourish'): desperate_flourish,
    ('ja', 'Violent Flourish'): violent_flourish,
    ('ja', 'Reverse Flourish'): reverse_flourish,
    ('ja', 'Building Flourish'): building_flourish,
    ('ja', 'Wild Flourish'): wild_flourish,
    ('ja', 'Striking Flourish'): striking_flourish,
    ('ja', 'Ternary Flourish'): ternary_flourish,
    ('ja', 'Spectral Jig'): spectral_jig,
    ('ja', 'Chocobo Jig'): chocobo_jig,
    # SCH
    ('ja', 'Penury'): strat(True, *GREEN_L, em_half_drop),
    ('ja', 'Parsimony'): strat(False, *GREEN_D, em_half_drop),
    ('ja', 'Celerity'): strat(True, *CYAN_L, em_fast),
    ('ja', 'Alacrity'): strat(False, *CYAN_D, em_fast),
    ('ja', 'Rapture'): strat(True, *ROSE_L, em_burst),
    ('ja', 'Ebullience'): strat(False, *ROSE_D, em_burst),
    ('ja', 'Accession'): strat(True, *BLUE_L, em_area),
    ('ja', 'Manifestation'): strat(False, *BLUE_D, em_area),
    ('ja', 'Addendum: White'): strat(True, *PURP_L, em_plus_page),
    ('ja', 'Addendum: Black'): strat(False, *GOLD_D, em_plus_page),
    ('ja', 'Altruism'): strat(True, *ORNG_L, em_reticle),
    ('ja', 'Focalization'): strat(False, *ORNG_D, em_reticle),
    ('ja', 'Tranquility'): strat(True, *TEAL_L, em_calm),
    ('ja', 'Equanimity'): strat(False, *TEAL_D, em_calm),
    ('ja', 'Perpetuance'): strat(True, *GOLD_L, em_infinity),
    ('ja', 'Immanence'): strat(False, *GOLD_D, em_chain),
    # RUN
    ('ja', 'Pflug'): pflug,
    ('ja', 'Liement'): liement,
    ('ja', 'Battuta'): battuta,
    ('ja', 'Swipe'): swipe,
    ('ja', 'Lunge'): lunge,
    ('ja', 'Gambit'): gambit,
    ('ja', 'Rayke'): rayke,
}

COVERS = {
    'Aspir Samba': ['Aspir Samba', 'Aspir Samba II'],
    'Chocobo Jig': ['Chocobo Jig', 'Chocobo Jig II'],
}

MANEUVER_BASE = GD.FIRE
VARIANTS = {
    'Maneuver': GD.shifts(MANEUVER_BASE, {
        'Fire Maneuver': GD.FIRE, 'Ice Maneuver': GD.ICE, 'Wind Maneuver': GD.WIND, 'Earth Maneuver': GD.EARTH,
        'Thunder Maneuver': GD.THUNDER, 'Water Maneuver': GD.WATER, 'Light Maneuver': 0,
        'Dark Maneuver': 0}),
}
# Light / Dark can't be reached by a hue turn alone (they read as Earth / Thunder): pale gold-white, violet-black.
VARIANTS['Maneuver']['Light Maneuver'] = ((K.LIGHT[0] + GD.FIRE - MANEUVER_BASE) % 360,) + K.LIGHT[1:]
VARIANTS['Maneuver']['Dark Maneuver'] = ((K.DARK[0] + GD.FIRE - MANEUVER_BASE) % 360,) + K.DARK[1:]
