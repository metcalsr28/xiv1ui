"""Signature icons, group B: THF, PLD, DRK, BST, BRD."""
import math
import random

from PIL import ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K

W = K.W
p = K.p
pts = K.pts


# ---- shared motifs (unit coords; local shapes placed with xf) -------------------------------------------------------
def xf(seq, cx, cy, s=1.0, ang=0.0):
    """Local points -> canvas pixels: scale s, rotate ang degrees (clockwise), move to (cx, cy)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [p(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in seq]


def ell(cx, cy, rx, ry, n=36):
    return [(cx + math.cos(2 * math.pi * i / n) * rx, cy + math.sin(2 * math.pi * i / n) * ry) for i in range(n)]


def sparkles(c, spots, color=(255, 255, 255, 255), glow_col=None):
    st = K.shape(lambda d: [K.sparkle(d, x, y, r) for x, y, r in spots])
    K.glow(c, st, glow_col or color, 8)
    K.fill(c, K.soften(st), color)


def motes(c, seed, n, box, rr, color, glow_col):
    rnd = random.Random(seed)
    m = K.mask()
    md = ImageDraw.Draw(m)
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(*rr)
        md.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    K.glow(c, m, glow_col, 5)
    K.fill(c, m, color)


def rays(c, cx, cy, n, length, color, alpha=90, w=0.05, blur=8, phase=0.0):
    m = K.mask()
    d = ImageDraw.Draw(m)
    for i in range(n):
        a = math.pi * 2 * i / n + phase
        d.polygon(pts([(cx, cy), (cx + math.cos(a - w) * length, cy + math.sin(a - w) * length),
                       (cx + math.cos(a + w) * length, cy + math.sin(a + w) * length)]), fill=alpha)
    K.fill(c, m.filter(ImageFilter.GaussianBlur(blur)), color)


def sword_parts(length=1.0, blade_w=0.07, guard_w=0.30, grip_w=0.05):
    """A sword pointing up (local coords, ~-0.5..0.47): blade, guard, grip + pommel."""
    L = length
    g = grip_w / 2
    blade = [(0, -0.50 * L), (blade_w / 2, -0.42 * L), (blade_w / 2, 0.16), (-blade_w / 2, 0.16),
             (-blade_w / 2, -0.42 * L)]
    guard = [(-guard_w / 2, 0.15), (guard_w / 2, 0.15), (guard_w / 2 - 0.02, 0.21), (-guard_w / 2 + 0.02, 0.21)]
    grip = [(-g, 0.21), (g, 0.21), (g, 0.37), (-g, 0.37)]
    pommel = ell(0, 0.40, 0.045 + (g - 0.025), 0.045 + (g - 0.025), 20)
    return blade, guard + [], grip, pommel


def draw_sword(d, cx, cy, s, ang, **kw):
    for part in sword_parts(**kw):
        d.polygon(xf(part, cx, cy, s, ang), fill=255)


def dagger_parts():
    blade = [(0, -0.46), (0.05, -0.36), (0.055, 0.08), (-0.055, 0.08), (-0.04, -0.30)]
    guard = [(-0.16, 0.06), (0.16, 0.06), (0.13, 0.12), (-0.13, 0.12)]
    grip = [(-0.03, 0.12), (0.03, 0.12), (0.03, 0.30), (-0.03, 0.30)]
    pommel = ell(0, 0.33, 0.05, 0.05, 20)
    return blade, guard, grip, pommel


def draw_dagger(d, cx, cy, s, ang, parts=(0, 1, 2, 3)):
    dp = dagger_parts()
    for i in parts:
        d.polygon(xf(dp[i], cx, cy, s, ang), fill=255)


def shield_outline():
    """A heater shield, local coords ~(-0.32..0.32, -0.36..0.40)."""
    right = [(0.0, -0.30), (0.16, -0.32), (0.32, -0.36), (0.33, -0.10), (0.32, 0.04), (0.28, 0.16), (0.21, 0.27),
             (0.11, 0.35), (0.0, 0.40)]
    left = [(-x, y) for x, y in right[1:-1]][::-1]
    return right + left


def draw_shield(d, cx, cy, s, ang=0.0, inset=0.0):
    o = shield_outline()
    if inset:
        o = [(x * (1 - inset), y * (1 - inset) + inset * 0.02) for x, y in o]
    d.polygon(xf(o, cx, cy, s, ang), fill=255)


def note(d, cx, cy, s, flags=1, ang=0.0):
    """An eighth note (head at the bottom-left of the stem), local origin at the head."""
    head = [(x * math.cos(-0.45) - y * math.sin(-0.45), x * math.sin(-0.45) + y * math.cos(-0.45))
            for x, y in ell(0, 0, 0.13, 0.09)]
    d.polygon(xf(head, cx, cy, s, ang), fill=255)
    d.polygon(xf([(0.085, -0.02), (0.125, -0.04), (0.125, -0.62), (0.085, -0.62)], cx, cy, s, ang), fill=255)
    for k in range(flags):
        y0 = -0.62 + k * 0.14
        flag = [(0.10, y0), (0.14, y0), (0.20, y0 + 0.08), (0.30, y0 + 0.14), (0.33, y0 + 0.26), (0.28, y0 + 0.36),
                (0.29, y0 + 0.26), (0.24, y0 + 0.19), (0.14, y0 + 0.14), (0.10, y0 + 0.13)]
        d.polygon(xf(flag, cx, cy, s, ang), fill=255)


def paw(d, cx, cy, s):
    d.polygon(xf(ell(0, 0.08, 0.20, 0.16), cx, cy, s), fill=255)
    for x, y, r in ((-0.25, -0.12, 0.085), (-0.10, -0.25, 0.09), (0.10, -0.25, 0.09), (0.25, -0.12, 0.085)):
        d.polygon(xf(ell(x, y, r * 0.9, r * 1.1), cx, cy, s), fill=255)


def heart(d, cx, cy, s):
    seq = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        seq.append((x / 34, y / 34))
    d.polygon(xf(seq, cx, cy, s), fill=255)


def skull(d, cx, cy, s):
    d.polygon(xf(ell(0, -0.06, 0.30, 0.28), cx, cy, s), fill=255)
    d.polygon(xf([(-0.20, 0.08), (0.20, 0.08), (0.17, 0.32), (-0.17, 0.32)], cx, cy, s), fill=255)
    d.polygon(xf(ell(-0.12, 0.02, 0.085, 0.09), cx, cy, s), fill=0)
    d.polygon(xf(ell(0.12, 0.02, 0.085, 0.09), cx, cy, s), fill=0)
    d.polygon(xf([(0, 0.11), (0.04, 0.19), (-0.04, 0.19)], cx, cy, s), fill=0)
    for x in (-0.09, 0.0, 0.09):
        d.polygon(xf([(x - 0.012, 0.24), (x + 0.012, 0.24), (x + 0.012, 0.33), (x - 0.012, 0.33)], cx, cy, s), fill=0)


def crescent(d, cx, cy, r, off=(0.35, -0.2)):
    d.ellipse(pts([(cx - r, cy - r), (cx + r, cy + r)]), fill=255)
    ox, oy = cx + off[0] * r, cy + off[1] * r
    d.ellipse(pts([(ox - r * 0.85, oy - r * 0.85), (ox + r * 0.85, oy + r * 0.85)]), fill=0)


def metal(top=(250, 250, 255, 255), bot=(150, 160, 185, 255)):
    return K.linear(top, bot, 90)


def gold():
    return K.linear((255, 240, 170, 255), (210, 140, 50, 255), 90)


# ---- THF ----------------------------------------------------------------------------------------------------------
def sneak_attack():
    """A dagger plunging down out of the night, a crescent moon behind it."""
    c = K.radial((110, 60, 170, 255), (14, 6, 30, 255), 0.5, 0.42, 0.72)
    moon = K.shape(lambda d: crescent(d, 0.34, 0.32, 0.17, (0.42, -0.25)))
    K.glow(c, moon, (210, 190, 255, 255), 16)
    K.fill(c, K.soften(moon), (240, 232, 255, 255))
    dag = K.shape(lambda d: draw_dagger(d, 0.54, 0.52, 1.25, 205))
    K.glow(c, dag, (200, 150, 255, 255), 14, 1.2)
    K.shadow(c, dag, 5, 8, 8, 160)
    K.fill(c, K.soften(dag), metal())
    hilt = K.shape(lambda d: draw_dagger(d, 0.54, 0.52, 1.25, 205, (1, 2, 3)))
    K.fill(c, K.soften(hilt), K.linear((150, 90, 200, 255), (60, 20, 90, 255), 90))
    sparkles(c, [(0.30, 0.82, 0.10)], (255, 255, 255, 255), (220, 180, 255, 255))
    return K.finish(c)


def trick_dagger(part):
    """A broad, leaf-bladed dagger pointing up (local coords ~-0.5..0.36); part: 'blade', 'edge' (its lit half),
    'hilt'."""
    if part == 'blade':
        return [[(0, -0.50), (0.075, -0.36), (0.095, -0.16), (0.075, 0.06), (-0.075, 0.06), (-0.095, -0.16),
                 (-0.075, -0.36)]]
    if part == 'edge':
        return [[(0, -0.50), (0.0, 0.06), (-0.075, 0.06), (-0.095, -0.16), (-0.075, -0.36)]]
    return [[(-0.20, 0.04), (0.20, 0.04), (0.17, 0.12), (-0.17, 0.12)],
            [(-0.04, 0.12), (0.04, 0.12), (0.04, 0.29), (-0.04, 0.29)],
            ell(0, 0.33, 0.06, 0.06, 20)]


def trick_attack():
    """A dagger thrusting out from behind an ally's dark silhouette."""
    c = K.radial((50, 170, 160, 255), (4, 26, 28, 255), 0.62, 0.42, 0.72)
    at = (0.62, 0.44, 1.15, 50)

    def part(name):
        return K.shape(lambda d: [d.polygon(xf(q, *at), fill=255) for q in trick_dagger(name)])
    blade = part('blade')
    K.glow(c, blade, (120, 255, 230, 255), 12, 1.2)
    K.shadow(c, blade, 4, 6, 6, 160)
    K.fill(c, K.soften(blade), K.linear((150, 175, 190, 255), (70, 90, 110, 255), 90))
    K.fill(c, K.soften(part('edge')), K.linear((250, 255, 255, 255), (190, 215, 225, 255), 90))
    hilt = part('hilt')
    K.shadow(c, hilt, 3, 5, 5, 150)
    K.fill(c, K.soften(hilt), K.linear((240, 200, 110, 255), (130, 80, 30, 255), 90))
    ally = K.shape(lambda d: [d.ellipse(pts([(0.20, 0.30), (0.40, 0.50)]), fill=255),
                              d.polygon(pts([(0.02, 1.0), (0.06, 0.68), (0.17, 0.57), (0.30, 0.54), (0.43, 0.57),
                                             (0.53, 0.68), (0.58, 1.0)]), fill=255)])
    K.glow(c, ally, (150, 255, 235, 255), 8, 1.4)
    K.fill(c, K.soften(ally), K.linear((22, 44, 50, 255), (6, 14, 18, 255), 90))
    sparkles(c, [(0.86, 0.17, 0.09)], (255, 255, 255, 255), (170, 255, 240, 255))
    return K.finish(c)


def steal():
    """A coin pouch snatched away, a gold coin flipping off it."""
    c = K.radial((120, 140, 50, 255), (14, 20, 6, 255), 0.5, 0.45, 0.72)
    # motion streaks to the left of the pouch
    st = K.mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.50, 0.10), (0.62, 0.14), (0.74, 0.18)):
        sd.rounded_rectangle(pts([(x0, y - 0.018), (0.38, y + 0.018)]), radius=0.018 * W, fill=170)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (230, 240, 190, 255))
    pouch_body = ell(0.0, 0.10, 0.25, 0.22, 48)
    pouch = K.shape(lambda d: [d.polygon(xf(pouch_body, 0.56, 0.56, 1.0, 12), fill=255),
                               d.polygon(xf([(-0.08, -0.12), (0.08, -0.12), (0.06, -0.06), (-0.06, -0.06)], 0.56,
                                            0.56, 1.0, 12), fill=255),
                               d.polygon(xf([(-0.06, -0.12), (-0.17, -0.24), (-0.04, -0.20), (0.0, -0.26),
                                             (0.04, -0.20), (0.17, -0.24), (0.06, -0.12)], 0.56, 0.56, 1.0, 12),
                                         fill=255)])
    K.glow(c, pouch, (240, 220, 140, 255), 14)
    K.shadow(c, pouch, 5, 8, 8, 160)
    K.fill(c, K.soften(pouch), K.linear((214, 150, 90, 255), (120, 66, 30, 255), 90))
    tie = K.shape(lambda d: d.polygon(xf([(-0.10, -0.115), (0.10, -0.115), (0.10, -0.075), (-0.10, -0.075)], 0.56,
                                         0.56, 1.0, 12), fill=255))
    K.fill(c, K.soften(tie), (255, 220, 120, 255))
    coin = K.shape(lambda d: d.ellipse(pts([(0.66, 0.16), (0.82, 0.32)]), fill=255))
    K.glow(c, coin, (255, 230, 120, 255), 14, 1.4)
    K.fill(c, K.soften(coin), gold())
    inner = K.shape(lambda d: d.ellipse(pts([(0.69, 0.19), (0.79, 0.29)]), outline=255, width=int(0.012 * W)))
    K.fill(c, K.soften(inner), (170, 110, 30, 255))
    sparkles(c, [(0.86, 0.44, 0.06), (0.62, 0.12, 0.05)], (255, 255, 230, 255), (255, 230, 140, 255))
    return K.finish(c)


def flee():
    """A winged boot dashing right, speed lines trailing."""
    c = K.radial((80, 170, 230, 255), (6, 22, 44, 255), 0.55, 0.45, 0.72)
    st = K.mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.40, 0.08), (0.54, 0.04), (0.68, 0.10), (0.80, 0.16)):
        sd.rounded_rectangle(pts([(x0, y - 0.016), (0.34, y + 0.016)]), radius=0.016 * W, fill=180)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (220, 245, 255, 255))
    boot = [(0.36, 0.18), (0.56, 0.18), (0.57, 0.56), (0.66, 0.60), (0.80, 0.64), (0.86, 0.70), (0.85, 0.78),
            (0.36, 0.78), (0.34, 0.60)]
    b = K.shape(lambda d: d.polygon(pts(boot), fill=255))
    K.glow(c, b, (200, 240, 255, 255), 14, 1.2)
    K.shadow(c, b, 5, 8, 8, 160)
    K.fill(c, K.soften(b), K.linear((150, 96, 60, 255), (80, 44, 24, 255), 90))
    cuff = K.shape(lambda d: [d.rounded_rectangle(pts([(0.33, 0.16), (0.59, 0.25)]), radius=0.02 * W, fill=255),
                              d.rounded_rectangle(pts([(0.34, 0.74), (0.87, 0.80)]), radius=0.02 * W, fill=255)])
    K.fill(c, K.soften(cuff), (220, 170, 110, 255))

    def wing(d):
        for i in range(4):
            ang = math.radians(-160 + i * 22)
            bx, by = 0.36, 0.38
            L = 0.26 - i * 0.03
            ex, ey = bx + math.cos(ang) * L, by + math.sin(ang) * L
            nx, ny = -math.sin(ang) * 0.04, math.cos(ang) * 0.04
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    w = K.shape(wing)
    K.glow(c, w, (255, 255, 255, 255), 10)
    K.fill(c, K.soften(w), K.linear((255, 255, 255, 255), (200, 225, 245, 255), 90))
    return K.finish(c)


def perfect_dodge():
    """A blade cuts only an after-image: the real figure has already slipped aside."""
    c = K.radial((220, 110, 140, 255), (36, 8, 22, 255), 0.5, 0.45, 0.72)
    ghost = K.shape(lambda d: K.figure(d, 0.36, 0.55, 0.80))
    K.fill(c, K.soften(ghost, 2.5).point(lambda v: int(v * 0.45)), (255, 235, 245, 255))
    # the slash cutting through the ghost
    sl = K.shape(lambda d: d.polygon(pts([(0.06, 0.30), (0.64, 0.76), (0.60, 0.80), (0.06, 0.34)]), fill=255))
    sl2 = K.shape(lambda d: d.polygon(pts([(0.10, 0.30), (0.62, 0.70), (0.66, 0.78), (0.08, 0.36)]), fill=255))
    K.glow(c, sl2, (255, 255, 255, 255), 10, 1.4)
    K.fill(c, K.soften(sl), (255, 255, 255, 255))
    fig = K.shape(lambda d: K.figure(d, 0.66, 0.53, 0.82))
    K.glow(c, fig, (255, 225, 240, 255), 10, 1.7)
    K.fill(c, K.soften(fig), K.linear((70, 24, 48, 255), (22, 6, 18, 255), 90))
    return K.finish(c)


# ---- PLD ----------------------------------------------------------------------------------------------------------
def invincible():
    """A radiant golden shield, light pouring off it."""
    c = K.radial((70, 110, 220, 255), (6, 10, 40, 255), 0.5, 0.48, 0.72)
    rays(c, 0.5, 0.5, 16, 0.7, (255, 240, 180, 255), 110, 0.06, 6)
    sh = K.shape(lambda d: draw_shield(d, 0.5, 0.50, 1.05))
    K.glow(c, sh, (255, 220, 120, 255), 30, 1.5)
    K.fill(c, K.soften(sh), gold())
    inner = K.shape(lambda d: draw_shield(d, 0.5, 0.50, 1.05, inset=0.22))
    K.fill(c, K.soften(inner), K.linear((255, 252, 230, 255), (240, 196, 100, 255), 90))
    cross = K.shape(lambda d: [d.rectangle(pts([(0.475, 0.24), (0.525, 0.72)]), fill=255),
                               d.rectangle(pts([(0.34, 0.40), (0.66, 0.45)]), fill=255)])
    K.fill(c, K.soften(cross), (190, 120, 40, 255))
    sparkles(c, [(0.80, 0.22, 0.09), (0.20, 0.74, 0.06)], (255, 255, 255, 255), (255, 230, 150, 255))
    return K.finish(c)


def sentinel():
    """A steel tower shield planted firm, a heavy down-arrow on it (damage taken cut)."""
    c = K.radial((110, 120, 150, 255), (10, 12, 22, 255), 0.5, 0.45, 0.72)
    sh = K.shape(lambda d: draw_shield(d, 0.5, 0.49, 1.12))
    K.glow(c, sh, (190, 210, 255, 255), 18, 1.1)
    K.shadow(c, sh, 5, 8, 8, 170)
    K.fill(c, K.soften(sh), metal((240, 244, 255, 255), (110, 120, 150, 255)))
    inner = K.shape(lambda d: draw_shield(d, 0.5, 0.49, 1.12, inset=0.14))
    K.fill(c, K.soften(inner), K.linear((70, 90, 150, 255), (24, 30, 70, 255), 90))
    arrow = K.shape(lambda d: d.polygon(pts([(0.44, 0.22), (0.56, 0.22), (0.56, 0.46), (0.67, 0.46), (0.5, 0.70),
                                             (0.33, 0.46), (0.44, 0.46)]), fill=255))
    K.glow(c, arrow, (180, 220, 255, 255), 10, 1.3)
    K.fill(c, K.soften(arrow), K.linear((255, 255, 255, 255), (170, 200, 240, 255), 90))
    return K.finish(c)


def flash():
    """A blinding burst of white light."""
    c = K.radial((170, 210, 250, 255), (14, 24, 60, 255), 0.5, 0.5, 0.66)
    rays(c, 0.5, 0.5, 12, 0.7, (255, 255, 255, 255), 150, 0.07, 5, 0.13)
    burst = K.mask()
    bd = ImageDraw.Draw(burst)
    n = 8
    star = []
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        r = 0.44 if i % 2 == 0 else 0.13
        if i % 4 == 2:
            r = 0.30
        star.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
    bd.polygon(pts(star), fill=255)
    K.glow(c, burst, (220, 240, 255, 255), 26, 1.5)
    K.fill(c, K.soften(burst, 2), K.radial((255, 255, 255, 255), (190, 220, 255, 255), 0.5, 0.5, 0.42))
    core = K.shape(lambda d: d.ellipse(pts([(0.38, 0.38), (0.62, 0.62)]), fill=255))
    K.glow(c, core, (255, 255, 255, 255), 22, 1.8)
    K.fill(c, K.soften(core, 6), (255, 255, 255, 255))
    return K.finish(c)


def shield_bash():
    """A shield driven forward, an impact burst at its face."""
    c = K.radial((220, 130, 50, 255), (40, 14, 4, 255), 0.6, 0.45, 0.72)
    burst = K.mask()
    bd = ImageDraw.Draw(burst)
    n = 10
    star = []
    for i in range(n * 2):
        a = math.pi * i / n
        r = 0.32 if i % 2 == 0 else 0.15
        star.append((0.68 + math.cos(a) * r, 0.42 + math.sin(a) * r))
    bd.polygon(pts(star), fill=255)
    K.glow(c, burst, (255, 220, 120, 255), 18, 1.3)
    K.fill(c, K.soften(burst), K.radial((255, 255, 220, 255), (255, 170, 60, 255), 0.68, 0.42, 0.3))
    st = K.mask()
    sd = ImageDraw.Draw(st)
    for y, x0 in ((0.30, 0.04), (0.50, 0.02), (0.70, 0.06)):
        sd.rounded_rectangle(pts([(x0, y - 0.016), (0.22, y + 0.016)]), radius=0.016 * W, fill=170)
    K.fill(c, st.filter(ImageFilter.GaussianBlur(3)), (255, 230, 180, 255))
    sh = K.shape(lambda d: draw_shield(d, 0.40, 0.54, 0.86, -18))
    K.shadow(c, sh, 6, 9, 8, 170)
    K.fill(c, K.soften(sh), metal((245, 240, 230, 255), (130, 120, 115, 255)))
    inner = K.shape(lambda d: draw_shield(d, 0.40, 0.54, 0.86, -18, inset=0.16))
    K.fill(c, K.soften(inner), K.linear((200, 60, 40, 255), (100, 20, 16, 255), 90))
    boss = K.shape(lambda d: d.ellipse(pts([(0.35, 0.46), (0.45, 0.56)]), fill=255))
    K.fill(c, K.soften(boss), gold())
    return K.finish(c)


def cover():
    """A great shield raised in front of a smaller ally sheltering behind it."""
    c = K.radial((60, 140, 190, 255), (4, 18, 34, 255), 0.6, 0.45, 0.72)
    ally = K.shape(lambda d: [d.ellipse(pts([(0.60, 0.36), (0.76, 0.52)]), fill=255),
                              d.polygon(pts([(0.50, 0.92), (0.54, 0.62), (0.68, 0.54), (0.82, 0.62), (0.88, 0.92)]),
                                        fill=255)])
    K.glow(c, ally, (255, 240, 200, 255), 14, 1.6)
    K.fill(c, K.soften(ally), K.linear((255, 244, 220, 255), (200, 170, 130, 255), 90))
    sh = K.shape(lambda d: draw_shield(d, 0.38, 0.50, 0.90, -8))
    K.glow(c, sh, (180, 230, 255, 255), 18, 1.2)
    K.shadow(c, sh, 6, 9, 8, 190)
    K.fill(c, K.soften(sh), metal())
    inner = K.shape(lambda d: draw_shield(d, 0.38, 0.50, 0.90, -8, inset=0.16))
    K.fill(c, K.soften(inner), K.linear((60, 110, 200, 255), (20, 40, 100, 255), 90))
    cross = K.shape(lambda d: [d.polygon(xf([(-0.025, -0.22), (0.025, -0.22), (0.025, 0.24), (-0.025, 0.24)],
                                            0.38, 0.50, 0.90, -8), fill=255),
                               d.polygon(xf([(-0.15, -0.10), (0.15, -0.10), (0.15, -0.045), (-0.15, -0.045)],
                                            0.38, 0.50, 0.90, -8), fill=255)])
    K.fill(c, K.soften(cross), (240, 210, 120, 255))
    return K.finish(c)


# ---- DRK ----------------------------------------------------------------------------------------------------------
def blood_weapon():
    """A dark blade running with blood, drops falling from it."""
    c = K.radial((170, 24, 34, 255), (20, 2, 6, 255), 0.5, 0.42, 0.72)
    at = (0.50, 0.47, 1.0, 35)
    sw = K.shape(lambda d: draw_sword(d, *at, blade_w=0.18, guard_w=0.44, grip_w=0.07))
    K.glow(c, sw, (255, 70, 70, 255), 20, 1.6)
    K.shadow(c, sw, 5, 8, 8, 190)
    K.fill(c, K.soften(sw), metal((236, 232, 244, 255), (110, 100, 120, 255)))
    # the blade's lit half, so it reads as steel and not a flat bar
    lit_half = K.shape(lambda d: d.polygon(xf([(0, -0.50), (0.09, -0.42), (0.09, 0.15), (0, 0.15)], *at), fill=255))
    K.fill(c, K.soften(lit_half), (255, 255, 255, 120))
    # blood coating the upper blade
    blood = K.mask()
    bd = ImageDraw.Draw(blood)
    bd.polygon(xf([(0, -0.50), (0.09, -0.42), (0.09, -0.16), (0.05, -0.06), (0.01, -0.18), (-0.03, 0.02),
                   (-0.07, -0.10), (-0.09, -0.20), (-0.09, -0.42)], *at), fill=255)
    blood = ImageChops.multiply(blood, sw)
    K.fill(c, K.soften(blood), K.linear((255, 70, 70, 255), (150, 0, 10, 255), 90))
    drops = K.shape(lambda d: [heart_drop(d, x, y, r) for x, y, r in ((0.40, 0.68, 0.05), (0.30, 0.82, 0.038),
                                                                     (0.52, 0.85, 0.03))])
    K.glow(c, drops, (255, 60, 60, 255), 8, 1.2)
    K.fill(c, K.soften(drops), K.linear((255, 110, 110, 255), (170, 0, 10, 255), 90))
    return K.finish(c)


def heart_drop(d, x, y, r):
    """A teardrop, point up."""
    d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    d.polygon(pts([(x - r * 0.95, y - r * 0.3), (x, y - r * 2.6), (x + r * 0.95, y - r * 0.3)]), fill=255)


def souleater():
    """A skull wreathed in ghostly soul-fire."""
    c = K.radial((40, 130, 110, 255), (4, 18, 16, 255), 0.5, 0.55, 0.72)

    def flame(d, cx, base, w, h, lean=0.0):
        left, right = [], []
        for i in range(41):
            t = i / 40
            y = base - h * t
            half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
            x = cx + lean * t * t
            left.append((x - half, y))
            right.append((x + half, y))
        d.polygon(pts(left + right[::-1]), fill=255)
    fl = K.shape(lambda d: [flame(d, 0.5, 0.86, 0.36, 0.80, 0.03), flame(d, 0.28, 0.80, 0.12, 0.46, -0.08),
                            flame(d, 0.72, 0.80, 0.12, 0.50, 0.08)])
    K.glow(c, fl, (120, 255, 200, 255), 26, 1.2)
    K.fill(c, K.soften(fl), K.linear((210, 255, 230, 200), (40, 190, 140, 230), 270))
    sk = K.shape(lambda d: skull(d, 0.5, 0.58, 0.95))
    K.shadow(c, sk, 4, 7, 7, 160)
    K.fill(c, K.soften(sk), K.linear((60, 50, 70, 255), (14, 10, 22, 255), 90))
    eyes = K.shape(lambda d: [d.polygon(xf(ell(-0.12, 0.02, 0.05, 0.055), 0.5, 0.58, 0.95), fill=255),
                              d.polygon(xf(ell(0.12, 0.02, 0.05, 0.055), 0.5, 0.58, 0.95), fill=255)])
    K.glow(c, eyes, (140, 255, 210, 255), 8, 1.5)
    K.fill(c, K.soften(eyes), (220, 255, 240, 255))
    return K.finish(c)


def last_resort():
    """A great sword held aloft in a black-and-ember aura: all offence, no guard."""
    c = K.radial((190, 80, 20, 255), (24, 6, 2, 255), 0.5, 0.62, 0.66)
    aura = K.mask()
    ad = ImageDraw.Draw(aura)
    rnd = random.Random(5)
    for i in range(11):
        a = -math.pi / 2 + (i - 5) * 0.20
        L = rnd.uniform(0.34, 0.46)
        ad.polygon(pts([(0.5 - 0.10, 0.72), (0.5 + math.cos(a) * L, 0.62 + math.sin(a) * L), (0.5 + 0.10, 0.72)]),
                   fill=255)
    ad.ellipse(pts([(0.24, 0.46), (0.76, 0.92)]), fill=255)
    K.glow(c, aura, (255, 120, 30, 255), 24, 1.4)
    K.fill(c, aura.filter(ImageFilter.GaussianBlur(6)), (20, 4, 8, 255))
    sw = K.shape(lambda d: draw_sword(d, 0.5, 0.48, 1.0, 0, blade_w=0.15, guard_w=0.42))
    K.glow(c, sw, (255, 150, 60, 255), 12, 1.3)
    K.fill(c, K.soften(sw), K.linear((255, 220, 170, 255), (200, 70, 30, 255), 90))
    edge = K.shape(lambda d: d.polygon(pts([(0.5, 0.0), (0.51, 0.06), (0.51, 0.64), (0.49, 0.64), (0.49, 0.06)]),
                                       fill=255))
    K.fill(c, K.soften(ImageChops.multiply(edge, sw)), (120, 30, 20, 255))
    motes(c, 9, 14, (0.18, 0.08, 0.82, 0.5), (0.006, 0.013), (255, 210, 140, 255), (255, 140, 60, 255))
    return K.finish(c)


def drain():
    """Red life essence spiralling into a black void."""
    c = K.radial((150, 40, 110, 255), (18, 4, 18, 255), 0.5, 0.5, 0.72)
    sp = K.mask()
    sd = ImageDraw.Draw(sp)
    for arm in range(3):
        for i in range(60):
            t = i / 60
            a = arm * 2 * math.pi / 3 + t * 3.4
            r = 0.42 * (1 - t) + 0.10
            w = 0.055 * (1 - t) + 0.012
            x, y = 0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r
            sd.ellipse(pts([(x - w, y - w), (x + w, y + w)]), fill=255)
    K.glow(c, sp, (255, 60, 80, 255), 18, 1.3)
    K.fill(c, K.soften(sp), K.radial((150, 0, 20, 255), (255, 120, 120, 255), 0.5, 0.5, 0.48))
    void = K.shape(lambda d: d.ellipse(pts([(0.38, 0.38), (0.62, 0.62)]), fill=255))
    K.glow(c, void, (255, 80, 110, 255), 10, 1.4)
    K.fill(c, K.soften(void, 3), K.radial((0, 0, 0, 255), (40, 0, 20, 255), 0.5, 0.5, 0.12))
    motes(c, 4, 10, (0.12, 0.12, 0.88, 0.88), (0.008, 0.016), (255, 200, 200, 255), (255, 60, 80, 255))
    return K.finish(c)


def arcane_circle():
    """A glowing magic circle: double ring, hexagram, rune dots."""
    c = K.radial((80, 70, 190, 255), (8, 6, 34, 255), 0.5, 0.5, 0.7)
    circ = K.mask()
    cd = ImageDraw.Draw(circ)
    cd.ellipse(pts([(0.15, 0.15), (0.85, 0.85)]), outline=255, width=int(0.032 * W))
    cd.ellipse(pts([(0.22, 0.22), (0.78, 0.78)]), outline=255, width=int(0.016 * W))
    for k in range(2):
        tri = [(0.5 + math.cos(math.pi * 2 * i / 3 - math.pi / 2 + k * math.pi) * 0.28,
                0.5 + math.sin(math.pi * 2 * i / 3 - math.pi / 2 + k * math.pi) * 0.28) for i in range(3)]
        cd.line(pts(tri + [tri[0]]), fill=255, width=int(0.024 * W), joint='curve')
    for i in range(12):
        a = math.pi * 2 * i / 12 + math.pi / 12
        x, y = 0.5 + math.cos(a) * 0.315, 0.5 + math.sin(a) * 0.315
        cd.ellipse(pts([(x - 0.012, y - 0.012), (x + 0.012, y + 0.012)]), fill=255)
    K.glow(c, circ, (180, 140, 255, 255), 20, 1.6)
    K.glow(c, circ, (230, 210, 255, 255), 6)
    K.fill(c, K.soften(circ), (240, 230, 255, 255))
    core = K.shape(lambda d: d.ellipse(pts([(0.44, 0.44), (0.56, 0.56)]), fill=255))
    K.glow(c, core, (255, 255, 255, 255), 14, 1.5)
    K.fill(c, K.soften(core), (255, 255, 255, 255))
    return K.finish(c)


# ---- BST ----------------------------------------------------------------------------------------------------------
def familiar():
    """A paw print surging with power, in a burst of light."""
    c = K.radial((210, 150, 50, 255), (40, 20, 4, 255), 0.5, 0.5, 0.72)
    rays(c, 0.5, 0.5, 14, 0.7, (255, 240, 190, 255), 80, 0.06, 6)
    pw = K.shape(lambda d: paw(d, 0.5, 0.54, 1.05))
    K.glow(c, pw, (255, 220, 120, 255), 22, 1.4)
    K.shadow(c, pw, 4, 7, 7, 150)
    K.fill(c, K.soften(pw), K.linear((255, 250, 230, 255), (230, 170, 90, 255), 90))
    return K.finish(c)


def charm():
    """A heart that lures a beast to your side: pink heart with a paw on it."""
    c = K.radial((220, 90, 160, 255), (40, 6, 26, 255), 0.5, 0.45, 0.72)
    ht = K.shape(lambda d: heart(d, 0.5, 0.50, 0.74))
    K.glow(c, ht, (255, 150, 200, 255), 26, 1.5)
    K.shadow(c, ht, 4, 8, 8, 150)
    K.fill(c, K.soften(ht), K.linear((255, 200, 225, 255), (220, 40, 110, 255), 90))
    shine = K.shape(lambda d: d.ellipse(pts([(0.32, 0.32), (0.42, 0.40)]), fill=255))
    K.fill(c, K.soften(shine, 6).point(lambda v: int(v * 0.8)), (255, 255, 255, 255))
    pw = K.shape(lambda d: paw(d, 0.5, 0.51, 0.38))
    K.fill(c, K.soften(pw), (130, 10, 60, 255))
    sparkles(c, [(0.80, 0.22, 0.09), (0.20, 0.76, 0.06)], (255, 255, 255, 255), (255, 170, 210, 255))
    return K.finish(c)


def call_beast():
    """A clay jug, its stopper off, a swirl of beast-spirit rising out."""
    c = K.radial((50, 140, 130, 255), (4, 22, 22, 255), 0.5, 0.5, 0.72)
    sw = K.mask()
    sd = ImageDraw.Draw(sw)
    for i in range(70):
        t = i / 70
        y = 0.38 - t * 0.30
        x = 0.5 + math.sin(t * 9) * 0.12 * t
        r = 0.02 + 0.03 * t
        sd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    K.glow(c, sw, (180, 255, 230, 255), 12, 1.4)
    K.fill(c, K.soften(sw, 3), (230, 255, 245, 230))
    jug = K.shape(lambda d: [d.ellipse(pts([(0.27, 0.46), (0.73, 0.90)]), fill=255),
                             d.rectangle(pts([(0.42, 0.36), (0.58, 0.52)]), fill=255),
                             d.rounded_rectangle(pts([(0.39, 0.33), (0.61, 0.39)]), radius=0.02 * W, fill=255),
                             d.ellipse(pts([(0.62, 0.44), (0.80, 0.66)]), outline=255, width=int(0.035 * W))])
    K.shadow(c, jug, 5, 8, 8, 170)
    K.fill(c, K.soften(jug), K.linear((236, 150, 100, 255), (130, 60, 30, 255), 90))
    band = K.shape(lambda d: d.rectangle(pts([(0.28, 0.62), (0.72, 0.66)]), fill=255))
    K.fill(c, K.soften(ImageChops.multiply(band, jug)), (80, 34, 16, 255))
    hi = K.shape(lambda d: d.ellipse(pts([(0.34, 0.52), (0.44, 0.70)]), fill=255))
    K.fill(c, K.soften(hi, 6).point(lambda v: int(v * 0.5)), (255, 230, 200, 255))
    return K.finish(c)


def reward():
    """A meaty bone for the pet, glowing with healing."""
    c = K.radial((100, 170, 70, 255), (10, 28, 8, 255), 0.5, 0.45, 0.72)
    motes(c, 13, 18, (0.15, 0.2, 0.85, 0.9), (0.008, 0.02), (230, 255, 210, 220), (180, 255, 150, 255))

    def bone(d):
        d.polygon(xf([(-0.28, -0.05), (0.28, -0.05), (0.28, 0.05), (-0.28, 0.05)], 0.5, 0.5, 1.0, -35), fill=255)
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = sx * 0.30, sy * 0.06
                d.polygon(xf(ell(cx, cy, 0.085, 0.085), 0.5, 0.5, 1.0, -35), fill=255)
    bn = K.shape(bone)
    K.glow(c, bn, (210, 255, 180, 255), 22, 1.4)
    K.shadow(c, bn, 4, 7, 7, 150)
    K.fill(c, K.soften(bn), K.linear((255, 252, 236, 255), (214, 196, 160, 255), 90))
    meat = K.shape(lambda d: d.polygon(xf(ell(0, 0, 0.17, 0.12), 0.5, 0.5, 1.0, -35), fill=255))
    K.fill(c, K.soften(meat), K.linear((230, 120, 90, 255), (150, 50, 40, 255), 90))
    plus = K.shape(lambda d: [d.rectangle(pts([(0.74, 0.14), (0.79, 0.32)]), fill=255),
                              d.rectangle(pts([(0.675, 0.205), (0.855, 0.255)]), fill=255)])
    K.glow(c, plus, (200, 255, 170, 255), 8, 1.4)
    K.fill(c, K.soften(plus), (250, 255, 240, 255))
    return K.finish(c)


# ---- BRD ----------------------------------------------------------------------------------------------------------
def soul_voice():
    """A great golden note sending out rings of sound."""
    c = K.radial((190, 60, 170, 255), (30, 4, 34, 255), 0.45, 0.55, 0.72)
    rings = K.mask()
    rd = ImageDraw.Draw(rings)
    for r, a in ((0.22, 255), (0.32, 200), (0.42, 140)):
        rd.ellipse(pts([(0.42 - r, 0.62 - r), (0.42 + r, 0.62 + r)]), outline=a, width=int(0.026 * W))
    K.glow(c, rings, (255, 200, 255, 255), 10)
    K.fill(c, K.soften(rings, 2), (255, 220, 250, 255))
    nt = K.shape(lambda d: note(d, 0.40, 0.70, 0.95, 2))
    K.glow(c, nt, (255, 220, 140, 255), 22, 1.5)
    K.shadow(c, nt, 4, 7, 7, 150)
    K.fill(c, K.soften(nt), gold())
    sparkles(c, [(0.80, 0.24, 0.10), (0.20, 0.30, 0.06)], (255, 255, 255, 255), (255, 210, 250, 255))
    return K.finish(c)


def valor_minuet():
    """A note beside a raised sword: the song of attack."""
    c = K.radial((200, 70, 40, 255), (34, 8, 4, 255), 0.5, 0.45, 0.72)
    sw = K.shape(lambda d: draw_sword(d, 0.60, 0.50, 0.96, 28, blade_w=0.14, guard_w=0.38, grip_w=0.06))
    K.glow(c, sw, (255, 190, 140, 255), 12, 1.3)
    K.shadow(c, sw, 4, 7, 7, 160)
    K.fill(c, K.soften(sw), metal((255, 255, 255, 255), (170, 160, 170, 255)))
    nt = K.shape(lambda d: note(d, 0.26, 0.68, 0.72, 1))
    K.glow(c, nt, (255, 220, 140, 255), 16, 1.5)
    K.shadow(c, nt, 4, 7, 7, 170)
    K.fill(c, K.soften(nt), gold())
    return K.finish(c)


def mages_ballad():
    """A note dripping blue mana: the song that refreshes MP."""
    c = K.radial((60, 110, 210, 255), (4, 12, 40, 255), 0.5, 0.45, 0.72)
    motes(c, 21, 16, (0.15, 0.15, 0.85, 0.85), (0.008, 0.018), (200, 230, 255, 230), (120, 180, 255, 255))
    nt = K.shape(lambda d: note(d, 0.40, 0.70, 0.95, 1))
    K.glow(c, nt, (140, 200, 255, 255), 20, 1.5)
    K.shadow(c, nt, 4, 7, 7, 150)
    K.fill(c, K.soften(nt), K.linear((255, 255, 255, 255), (150, 200, 255, 255), 90))
    drops = K.shape(lambda d: [heart_drop(d, 0.74, 0.70, 0.07), heart_drop(d, 0.62, 0.86, 0.04)])
    K.glow(c, drops, (100, 170, 255, 255), 10, 1.4)
    K.fill(c, K.soften(drops), K.linear((200, 230, 255, 255), (50, 110, 230, 255), 90))
    return K.finish(c)


def advancing_march():
    """A note marching forward, chevrons speeding it on (haste)."""
    c = K.radial((170, 180, 50, 255), (26, 28, 4, 255), 0.5, 0.45, 0.72)
    ch = K.mask()
    cd = ImageDraw.Draw(ch)
    for i, a in enumerate((110, 170, 240)):
        x = 0.50 + i * 0.12
        cd.line(pts([(x, 0.30), (x + 0.12, 0.50), (x, 0.70)]), fill=a, width=int(0.05 * W), joint='curve')
    K.glow(c, ch, (255, 255, 180, 255), 10, 1.2)
    K.fill(c, K.soften(ch), (255, 255, 220, 255))
    nt = K.shape(lambda d: note(d, 0.30, 0.72, 0.90, 1))
    K.glow(c, nt, (255, 240, 160, 255), 16, 1.4)
    K.shadow(c, nt, 4, 7, 7, 160)
    K.fill(c, K.soften(nt), gold())
    return K.finish(c)


def foe_lullaby():
    """A crescent moon cradling a note: the song of sleep."""
    c = K.radial((60, 60, 150, 255), (4, 4, 24, 255), 0.5, 0.45, 0.72)
    motes(c, 31, 14, (0.12, 0.12, 0.88, 0.5), (0.005, 0.011), (255, 255, 240, 255), (200, 200, 255, 255))
    moon = K.shape(lambda d: crescent(d, 0.46, 0.50, 0.34, (0.40, -0.30)))
    K.glow(c, moon, (230, 220, 160, 255), 22, 1.3)
    K.fill(c, K.soften(moon), K.linear((255, 250, 210, 255), (220, 190, 110, 255), 90))
    nt = K.shape(lambda d: note(d, 0.58, 0.66, 0.62, 1))
    K.glow(c, nt, (200, 200, 255, 255), 12, 1.3)
    K.fill(c, K.soften(nt), K.linear((240, 240, 255, 255), (170, 170, 230, 255), 90))
    return K.finish(c)


ICONS = {
    ('ja', 'Sneak Attack'): sneak_attack,
    ('ja', 'Trick Attack'): trick_attack,
    ('ja', 'Steal'): steal,
    ('ja', 'Flee'): flee,
    ('ja', 'Perfect Dodge'): perfect_dodge,
    ('ja', 'Invincible'): invincible,
    ('ja', 'Sentinel'): sentinel,
    ('ma', 'Flash'): flash,
    ('ja', 'Shield Bash'): shield_bash,
    ('ja', 'Cover'): cover,
    ('ja', 'Blood Weapon'): blood_weapon,
    ('ja', 'Souleater'): souleater,
    ('ja', 'Last Resort'): last_resort,
    ('ma', 'Drain'): drain,
    ('ja', 'Arcane Circle'): arcane_circle,
    ('ja', 'Familiar'): familiar,
    ('ja', 'Charm'): charm,
    ('ja', 'Call Beast'): call_beast,
    ('ja', 'Reward'): reward,
    ('ja', 'Soul Voice'): soul_voice,
    ('ma', 'Valor Minuet'): valor_minuet,
    ("ma", "Mage's Ballad"): mages_ballad,
    ('ma', 'Advancing March'): advancing_march,
    ('ma', 'Foe Lullaby'): foe_lullaby,
}
