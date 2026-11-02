"""Signature icons, group A: WAR, MNK, WHM, BLM, RDM (see tools/make_signature_icons.py for the kit)."""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import make_signature_icons as K

W = K.W
p, pts, mask, shape, soften = K.p, K.pts, K.mask, K.shape, K.soften


# ---- helpers --------------------------------------------------------------------------------------------------------
def star_pts(cx, cy, n, r1, r2, rot=-math.pi / 2):
    out = []
    for i in range(n * 2):
        a = math.pi * i / n + rot
        r = r1 if i % 2 == 0 else r2
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


def dots(seed, n, x0, x1, y0, y1, r0, r1):
    m = mask()
    d = ImageDraw.Draw(m)
    rnd = random.Random(seed)
    for _ in range(n):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(r0, r1)
        d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    return m


def motes(c, seed, n, box, rr, glow_col, col):
    m = dots(seed, n, box[0], box[2], box[1], box[3], rr[0], rr[1])
    K.glow(c, m, glow_col, 6)
    K.fill(c, m, col)


def sparkles(c, spots, glow_col=(255, 255, 255, 255)):
    st = shape(lambda d: [K.sparkle(d, x, y, r) for x, y, r in spots])
    K.glow(c, st, glow_col, 8)
    K.fill(c, soften(st), (255, 255, 255, 255))


def arc_arrow(d, cx, cy, r, a0, a1, width, head=None):
    """An arc (degrees, clockwise on screen from 3 o'clock) from a0 to a1 with an arrowhead at a1."""
    head = head or width * 2.2
    d.arc(pts([(cx - r, cy - r), (cx + r, cy + r)]), a0, a1, fill=255, width=int(width * W))
    a = math.radians(a1)
    ox, oy = math.cos(a), math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)      # direction of travel (clockwise)
    mx, my = cx + ox * (r - width / 2), cy + oy * (r - width / 2)
    d.polygon(pts([(mx + ox * head, my + oy * head), (mx - ox * head, my - oy * head),
                   (mx + tx * head * 1.4, my + ty * head * 1.4)]), fill=255)


def leaf(d, bx, by, ang, length, width, fill=255):
    """A pointed leaf / petal from (bx, by) along angle `ang` (radians)."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    left, right = [], []
    for i in range(25):
        t = i / 24
        w = width * math.sin(math.pi * t) ** 0.75
        x, y = bx + ux * length * t, by + uy * length * t
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    d.polygon(pts(left + right[::-1]), fill=fill)


def sword(d, hx, hy, tx, ty, w=0.045, guard=0.10, grip=0.13):
    """A straight sword from the pommel (hx, hy) to the tip (tx, ty)."""
    L = math.hypot(tx - hx, ty - hy)
    ux, uy = (tx - hx) / L, (ty - hy) / L
    nx, ny = -uy, ux
    gx, gy = hx + ux * grip, hy + uy * grip
    bx, by = tx - ux * w * 2.2, ty - uy * w * 2.2
    d.polygon(pts([(gx + nx * w, gy + ny * w), (bx + nx * w, by + ny * w), (tx, ty),
                   (bx - nx * w, by - ny * w), (gx - nx * w, gy - ny * w)]), fill=255)
    g = 0.022
    d.polygon(pts([(gx + nx * guard - ux * g, gy + ny * guard - uy * g), (gx + nx * guard + ux * g, gy + ny * guard + uy * g),
                   (gx - nx * guard + ux * g, gy - ny * guard + uy * g), (gx - nx * guard - ux * g, gy - ny * guard - uy * g)]),
              fill=255)
    gw = w * 0.6
    d.polygon(pts([(hx + nx * gw, hy + ny * gw), (gx + nx * gw, gy + ny * gw),
                   (gx - nx * gw, gy - ny * gw), (hx - nx * gw, hy - ny * gw)]), fill=255)
    r = w * 0.95
    d.ellipse(pts([(hx - r, hy - r), (hx + r, hy + r)]), fill=255)


def bezier(p0, p1, p2, n=20):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def heater(d, cx, top, w, h, fill=255):
    """A heater shield: flat-ish top, straight sides, curving to a point."""
    right = [(cx + w, top)] + bezier((cx + w, top + h * 0.42), (cx + w * 0.95, top + h * 0.82), (cx, top + h))
    left = [(cx - x + cx, y) for x, y in right[::-1]]
    top_arc = [(cx - w + 2 * w * t, top - 0.03 * math.sin(math.pi * t)) for t in (i / 10 for i in range(11))]
    d.polygon(pts(top_arc + right[1:] + left[:-1]), fill=fill)


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


def rotated(m, deg, cx=0.5, cy=0.5):
    return m.rotate(deg, resample=Image.BICUBIC, center=p(cx, cy))


def metal(c, m, top=(250, 250, 255, 255), bottom=(130, 140, 160, 255)):
    K.fill(c, soften(m), K.linear(top, bottom, 90))


# ---- WAR -------------------------------------------------------------------------------------------------------------
def berserk():
    """A double-bitted war axe in a red rage aura."""
    c = K.radial((96, 6, 22, 255), (10, 0, 4, 255), 0.5, 0.6, 0.62)
    aura = shape(lambda d: [flame(d, 0.5, 0.92, 0.36, 0.86, 0.0), flame(d, 0.26, 0.92, 0.14, 0.50, -0.08),
                            flame(d, 0.74, 0.92, 0.14, 0.52, 0.08)])
    K.glow(c, aura, (230, 20, 30, 255), 24, 0.9)
    K.fill(c, soften(aura, 4).point(lambda v: int(v * 0.5)), K.linear((255, 140, 60, 255), (170, 10, 20, 255), 270))

    def axe(d):
        d.rounded_rectangle(pts([(0.475, 0.16), (0.525, 0.86)]), radius=0.02 * W, fill=255)
        for side in (-1, 1):
            outer = [(0.5 + side * (0.21 + 0.06 * math.sin(math.pi * t)), 0.15 + 0.36 * t) for t in (i / 20 for i in range(21))]
            d.polygon(pts([(0.5, 0.27)] + outer + [(0.5, 0.39)]), fill=255)
        d.ellipse(pts([(0.465, 0.11), (0.535, 0.18)]), fill=255)
    m = shape(axe)
    K.shadow(c, m, 5, 8, 8, 170)
    metal(c, m, (255, 248, 240, 255), (150, 140, 150, 255))
    handle = shape(lambda d: d.rounded_rectangle(pts([(0.478, 0.52), (0.522, 0.86)]), radius=0.02 * W, fill=255))
    K.fill(c, soften(handle), (110, 50, 34, 255))
    edge = shape(lambda d: [d.line(pts([(0.5 + s * (0.21 + 0.06 * math.sin(math.pi * t)), 0.15 + 0.36 * t)
                                        for t in (i / 20 for i in range(21))]), fill=255, width=int(0.018 * W))
                            for s in (-1, 1)])
    K.fill(c, soften(edge).point(lambda v: int(v * 0.7)), (255, 90, 70, 255))
    motes(c, 5, 14, (0.18, 0.1, 0.82, 0.5), (0.006, 0.013), (255, 90, 60, 255), (255, 200, 150, 255))
    return K.finish(c)


def warcry():
    """A curved war horn blasting rings of sound."""
    c = K.radial((214, 120, 36, 255), (40, 16, 4, 255), 0.42, 0.6, 0.74)
    curve = bezier((0.14, 0.86), (0.20, 0.42), (0.56, 0.40), 40)
    spine = [(x, y, 0.02 + 0.12 * (i / 40) ** 2.2) for i, (x, y) in enumerate(curve)]

    def normal(i):
        j, k = min(i + 1, len(spine) - 1), max(i - 1, 0)
        dx, dy = spine[j][0] - spine[k][0], spine[j][1] - spine[k][1]
        L = math.hypot(dx, dy)
        return -dy / L, dx / L

    def horn(d):
        left, right = [], []
        for i, (x, y, w) in enumerate(spine):
            nx, ny = normal(i)
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        d.polygon(pts(left + right[::-1]), fill=255)
    ex, ey, ew = spine[-1]
    dx, dy = spine[-1][0] - spine[-4][0], spine[-1][1] - spine[-4][1]
    ang = math.degrees(math.atan2(dy, dx))
    waves = shape(lambda d: [d.arc(pts([(ex - r, ey - r), (ex + r, ey + r)]), ang - 45, ang + 45, fill=255,
                                   width=int(0.045 * W)) for r in (0.16, 0.26, 0.36)])
    K.glow(c, waves, (255, 220, 120, 255), 14, 1.4)
    K.fill(c, soften(waves, 1.5), (255, 248, 220, 255))
    m = shape(horn)
    K.shadow(c, m, 5, 8, 8, 160)
    K.glow(c, m, (255, 200, 110, 255), 12)
    K.fill(c, soften(m), K.linear((255, 246, 222, 255), (200, 160, 110, 255), 90))

    def bands(d):
        for i in (14, 28, 38):
            x, y, w = spine[i]
            nx, ny = normal(i)
            d.line(pts([(x + nx * w * 1.05, y + ny * w * 1.05), (x - nx * w * 1.05, y - ny * w * 1.05)]), fill=255,
                   width=int(0.026 * W))
    K.fill(c, soften(ImageChops.multiply(shape(bands), m)), K.linear((255, 220, 120, 255), (170, 110, 30, 255), 90))
    mouth = shape(lambda d: d.ellipse(pts([(ex - 0.028, ey - ew * 0.9), (ex + 0.028, ey + ew * 0.9)]), fill=255))
    K.fill(c, soften(rotated(mouth, -ang, ex, ey)), (110, 60, 24, 255))
    return K.finish(c)


def mighty_strikes():
    """A sword striking through a golden critical-hit burst."""
    c = K.radial((50, 60, 140, 255), (6, 8, 24, 255), 0.5, 0.5, 0.72)
    rays = mask()
    rd = ImageDraw.Draw(rays)
    for i in range(18):
        a = math.pi * 2 * i / 18
        w = 0.06
        rd.polygon(pts([(0.5, 0.5), (0.5 + math.cos(a - w) * 0.7, 0.5 + math.sin(a - w) * 0.7),
                        (0.5 + math.cos(a + w) * 0.7, 0.5 + math.sin(a + w) * 0.7)]), fill=80)
    K.fill(c, rays.filter(ImageFilter.GaussianBlur(6)), (255, 220, 120, 255))
    burst = shape(lambda d: d.polygon(pts(star_pts(0.5, 0.5, 8, 0.40, 0.17, -math.pi / 2 + 0.2)), fill=255))
    K.glow(c, burst, (255, 200, 60, 255), 26, 1.4)
    K.fill(c, soften(burst), K.radial((255, 255, 220, 255), (240, 160, 30, 255), 0.5, 0.5, 0.40))
    m = shape(lambda d: sword(d, 0.20, 0.80, 0.82, 0.18, 0.05, 0.11, 0.14))
    K.shadow(c, m, 5, 8, 8, 170)
    metal(c, m, (255, 255, 255, 255), (150, 160, 190, 255))
    hilt = shape(lambda d: d.ellipse(pts([(0.12, 0.72), (0.40, 1.0)]), fill=255))
    K.fill(c, soften(ImageChops.multiply(m, hilt)), (200, 150, 60, 255))
    sparkles(c, [(0.78, 0.74, 0.07), (0.24, 0.26, 0.06)], (255, 220, 120, 255))
    return K.finish(c)


def retaliation():
    """A bronze shield with a red arrow whipping back off it."""
    c = K.radial((40, 120, 112, 255), (4, 18, 18, 255), 0.5, 0.45, 0.72)
    arrow = shape(lambda d: arc_arrow(d, 0.5, 0.52, 0.34, -30, 205, 0.06, 0.07))
    K.glow(c, arrow, (255, 80, 40, 255), 14, 1.3)
    K.fill(c, soften(arrow), K.linear((255, 150, 80, 255), (210, 40, 30, 255), 90))
    m = shape(lambda d: heater(d, 0.5, 0.28, 0.20, 0.52))
    K.shadow(c, m, 5, 8, 8, 170)
    K.glow(c, m, (180, 255, 230, 255), 10, 0.8)
    K.fill(c, soften(m), K.linear((255, 226, 160, 255), (170, 100, 44, 255), 90))
    inner = shape(lambda d: heater(d, 0.5, 0.33, 0.145, 0.42))
    K.fill(c, soften(inner), K.linear((200, 60, 44, 255), (110, 20, 24, 255), 90))
    boss = shape(lambda d: d.ellipse(pts([(0.445, 0.43), (0.555, 0.54)]), fill=255))
    K.glow(c, boss, (255, 220, 150, 255), 6)
    K.fill(c, soften(boss), K.linear((255, 240, 200, 255), (190, 130, 60, 255), 90))
    return K.finish(c)


# ---- MNK -------------------------------------------------------------------------------------------------------------
def chakra():
    """A glowing lotus with a bright core of ki."""
    c = K.radial((140, 46, 120, 255), (18, 4, 20, 255), 0.5, 0.55, 0.72)
    halo = shape(lambda d: d.ellipse(pts([(0.28, 0.16), (0.72, 0.60)]), fill=255))
    K.fill(c, halo.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.6)), (255, 210, 120, 255))
    back = shape(lambda d: [leaf(d, 0.5, 0.70, math.radians(a), 0.40, 0.09) for a in (-160, -125, -55, -20)])
    K.fill(c, soften(back), K.linear((255, 170, 210, 255), (190, 60, 130, 255), 90))
    front = shape(lambda d: [leaf(d, 0.5, 0.72, math.radians(a), 0.44, 0.10) for a in (-140, -90, -40)])
    K.shadow(c, front, 3, 5, 6, 120)
    K.glow(c, front, (255, 200, 230, 255), 10)
    K.fill(c, soften(front), K.linear((255, 246, 250, 255), (240, 140, 190, 255), 90))
    lines = shape(lambda d: [d.line(pts([(0.5, 0.70), (0.5 + math.cos(math.radians(a)) * 0.30,
                                                         0.70 + math.sin(math.radians(a)) * 0.30)]),
                                    fill=255, width=int(0.008 * W)) for a in (-140, -90, -40)])
    K.fill(c, soften(lines).point(lambda v: int(v * 0.4)), (200, 80, 140, 255))
    base = shape(lambda d: d.ellipse(pts([(0.24, 0.68), (0.76, 0.80)]), fill=255))
    K.fill(c, soften(base), K.linear((120, 210, 140, 255), (30, 100, 60, 255), 90))
    orb = shape(lambda d: d.ellipse(pts([(0.44, 0.16), (0.56, 0.28)]), fill=255))
    K.glow(c, orb, (255, 230, 150, 255), 18, 1.6)
    K.fill(c, soften(orb), (255, 252, 230, 255))
    motes(c, 12, 10, (0.18, 0.12, 0.82, 0.5), (0.006, 0.012), (255, 200, 230, 255), (255, 240, 250, 255))
    return K.finish(c)


def boost():
    """A clenched fist powering up, energy surging upward."""
    c = K.radial((190, 40, 20, 255), (28, 4, 4, 255), 0.5, 0.62, 0.72)
    chev = shape(lambda d: [d.polygon(pts([(0.5, y), (0.80, y + 0.20), (0.80, y + 0.29), (0.5, y + 0.09),
                                           (0.20, y + 0.29), (0.20, y + 0.20)]), fill=255) for y in (0.06, 0.24)])
    K.glow(c, chev, (255, 150, 50, 255), 12)
    K.fill(c, soften(chev).point(lambda v: int(v * 0.85)), K.linear((255, 240, 160, 255), (255, 120, 30, 255), 90))
    aura = shape(lambda d: [flame(d, 0.5, 0.95, 0.30, 0.62), flame(d, 0.28, 0.95, 0.10, 0.36, -0.05),
                            flame(d, 0.72, 0.95, 0.10, 0.36, 0.05)])
    K.glow(c, aura, (255, 120, 30, 255), 20, 1.1)
    K.fill(c, soften(aura, 3).point(lambda v: int(v * 0.6)), K.linear((255, 200, 80, 255), (220, 60, 20, 255), 270))
    main = shape(lambda d: K.fist_front(d, 0.5, 0.66, 0.85))
    K.shadow(c, main, 5, 8, 8, 160)
    K.fill(c, soften(main), K.linear((255, 232, 196, 255), (222, 146, 92, 255), 90))
    lines = shape(lambda d: K.fist_lines(d, 0.5, 0.66, 0.85))
    K.fill(c, soften(lines, 1.5).point(lambda v: int(v * 0.7)), (120, 60, 36, 255))
    return K.finish(c)


def focus():
    """A reticle closing on its mark."""
    c = K.radial((30, 140, 104, 255), (2, 20, 16, 255), 0.5, 0.5, 0.70)
    conv = mask()
    cd = ImageDraw.Draw(conv)
    for i in range(16):
        a = math.pi * 2 * i / 16 + 0.2
        cd.line(pts([(0.5 + math.cos(a) * 0.46, 0.5 + math.sin(a) * 0.46),
                     (0.5 + math.cos(a) * 0.36, 0.5 + math.sin(a) * 0.36)]), fill=150, width=int(0.012 * W))
    K.fill(c, conv.filter(ImageFilter.GaussianBlur(2)), (190, 255, 220, 255))

    def ret(d):
        d.ellipse(pts([(0.22, 0.22), (0.78, 0.78)]), outline=255, width=int(0.045 * W))
        for x0, y0, x1, y1 in ((0.47, 0.10, 0.53, 0.34), (0.47, 0.66, 0.53, 0.90),
                               (0.10, 0.47, 0.34, 0.53), (0.66, 0.47, 0.90, 0.53)):
            d.rectangle(pts([(x0, y0), (x1, y1)]), fill=255)
    m = shape(ret)
    K.shadow(c, m, 4, 6, 6, 150)
    K.glow(c, m, (140, 255, 200, 255), 16, 1.3)
    K.fill(c, soften(m), (240, 255, 246, 255))
    dot = shape(lambda d: d.ellipse(pts([(0.43, 0.43), (0.57, 0.57)]), fill=255))
    K.glow(c, dot, (255, 120, 80, 255), 16, 1.5)
    K.fill(c, soften(dot), K.radial((255, 240, 200, 255), (240, 70, 40, 255), 0.5, 0.48, 0.07))
    return K.finish(c)


def counterstance():
    """A raised open palm set in a guard, with sweeping counter arcs."""
    c = K.radial((84, 96, 160, 255), (8, 10, 26, 255), 0.5, 0.5, 0.72)
    arcs = shape(lambda d: [arc_arrow(d, 0.5, 0.52, 0.38, 110, 230, 0.04, 0.05),
                            arc_arrow(d, 0.5, 0.52, 0.38, -70, 50, 0.04, 0.05)])
    K.glow(c, arcs, (160, 200, 255, 255), 12, 1.3)
    K.fill(c, soften(arcs), (230, 240, 255, 255))

    def palm(d):
        d.rounded_rectangle(pts([(0.33, 0.44), (0.65, 0.76)]), radius=0.09 * W, fill=255)
        for x, top in ((0.36, 0.24), (0.43, 0.18), (0.50, 0.17), (0.57, 0.22)):
            d.rounded_rectangle(pts([(x - 0.032, top), (x + 0.032, 0.52)]), radius=0.032 * W, fill=255)
        d.rounded_rectangle(pts([(0.40, 0.70), (0.60, 0.88)]), radius=0.04 * W, fill=255)    # wrist
    m = shape(palm)
    thumb = shape(lambda d: d.rounded_rectangle(pts([(0.62, 0.44), (0.69, 0.66)]), radius=0.035 * W, fill=255))
    m = ImageChops.lighter(m, rotated(thumb, -30, 0.64, 0.64))
    K.shadow(c, m, 5, 8, 8, 160)
    K.glow(c, m, (180, 210, 255, 255), 12)
    K.fill(c, soften(m), K.linear((255, 234, 204, 255), (214, 150, 104, 255), 90))
    gaps = shape(lambda d: [d.line(pts([(x, 0.40), (x, 0.52)]), fill=255, width=int(0.008 * W))
                            for x in (0.395, 0.465, 0.535)])
    K.fill(c, soften(gaps).point(lambda v: int(v * 0.5)), (140, 80, 50, 255))
    return K.finish(c)


# ---- WHM -------------------------------------------------------------------------------------------------------------
def cross(d, cx, cy, s):
    d.rounded_rectangle(pts([(cx - 0.10 * s, cy - 0.32 * s), (cx + 0.10 * s, cy + 0.32 * s)]), radius=0.05 * s * W, fill=255)
    d.rounded_rectangle(pts([(cx - 0.32 * s, cy - 0.10 * s), (cx + 0.32 * s, cy + 0.10 * s)]), radius=0.05 * s * W, fill=255)


def curaga():
    """Three crosses of healing light over a ring that spans the party."""
    c = K.radial((40, 150, 160, 255), (4, 22, 28, 255), 0.5, 0.45, 0.72)
    ring = shape(lambda d: d.ellipse(pts([(0.12, 0.62), (0.88, 0.90)]), outline=255, width=int(0.025 * W)))
    K.glow(c, ring, (120, 255, 240, 255), 12, 1.3)
    K.fill(c, soften(ring, 2), (210, 255, 250, 255))
    motes(c, 4, 18, (0.15, 0.2, 0.85, 0.85), (0.007, 0.018), (150, 255, 240, 255), (225, 255, 250, 220))
    small = shape(lambda d: [cross(d, 0.21, 0.60, 0.34), cross(d, 0.79, 0.60, 0.34)])
    K.glow(c, small, (120, 255, 230, 255), 14, 1.2)
    K.fill(c, soften(small), K.linear((240, 255, 252, 255), (150, 236, 220, 255), 90))
    big = shape(lambda d: cross(d, 0.5, 0.42, 0.72))
    K.shadow(c, big, 4, 6, 7, 120)
    K.glow(c, big, (140, 255, 230, 255), 26, 1.4)
    K.fill(c, soften(big), K.linear((255, 255, 252, 255), (170, 246, 228, 255), 90))
    return K.finish(c)


def raise_():
    """A golden ankh in a column of rising light."""
    c = K.radial((190, 110, 160, 255), (30, 8, 26, 255), 0.5, 0.42, 0.72)
    beam = shape(lambda d: d.rectangle(pts([(0.36, 0.0), (0.64, 1.0)]), fill=255))
    K.fill(c, beam.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.55)), (255, 240, 220, 255))
    motes(c, 9, 20, (0.3, 0.1, 0.7, 0.95), (0.006, 0.014), (255, 220, 200, 255), (255, 250, 240, 230))

    def ankh(d):
        d.ellipse(pts([(0.37, 0.12), (0.63, 0.46)]), outline=255, width=int(0.065 * W))
        d.rounded_rectangle(pts([(0.24, 0.43), (0.76, 0.52)]), radius=0.03 * W, fill=255)
        d.polygon(pts([(0.46, 0.46), (0.54, 0.46), (0.58, 0.88), (0.42, 0.88)]), fill=255)
    m = shape(ankh)
    K.shadow(c, m, 5, 8, 8, 150)
    K.glow(c, m, (255, 220, 140, 255), 18, 1.4)
    K.fill(c, soften(m), K.linear((255, 250, 210, 255), (220, 160, 60, 255), 90))
    sparkles(c, [(0.76, 0.22, 0.08), (0.24, 0.70, 0.06)], (255, 220, 200, 255))
    return K.finish(c)


def regen():
    """A sprouting seedling, life welling up slowly."""
    c = K.radial((140, 176, 40, 255), (14, 26, 4, 255), 0.5, 0.5, 0.72)
    arc = shape(lambda d: arc_arrow(d, 0.5, 0.52, 0.36, 120, 400, 0.035, 0.05))
    K.glow(c, arc, (230, 255, 150, 255), 10, 1.0)
    K.fill(c, soften(arc).point(lambda v: int(v * 0.75)), (240, 255, 200, 255))

    def sprout(d):
        d.line(pts(bezier((0.5, 0.84), (0.52, 0.66), (0.5, 0.48))), fill=255, width=int(0.045 * W), joint='curve')
        leaf(d, 0.5, 0.52, math.radians(-150), 0.34, 0.11)
        leaf(d, 0.5, 0.48, math.radians(-35), 0.38, 0.12)
        d.ellipse(pts([(0.32, 0.80), (0.68, 0.90)]), fill=255)
    m = shape(sprout)
    K.shadow(c, m, 4, 7, 7, 150)
    K.glow(c, m, (220, 255, 140, 255), 14, 1.3)
    K.fill(c, soften(m), K.linear((230, 255, 170, 255), (60, 170, 50, 255), 90))
    veins = shape(lambda d: [d.line(pts([(0.5, 0.52), (0.5 + math.cos(math.radians(-150)) * 0.28,
                                                         0.52 + math.sin(math.radians(-150)) * 0.28)]), fill=255,
                                    width=int(0.008 * W)),
                             d.line(pts([(0.5, 0.48), (0.5 + math.cos(math.radians(-35)) * 0.32,
                                                         0.48 + math.sin(math.radians(-35)) * 0.32)]), fill=255,
                                    width=int(0.008 * W))])
    K.fill(c, soften(veins).point(lambda v: int(v * 0.5)), (40, 110, 30, 255))
    motes(c, 21, 10, (0.2, 0.15, 0.8, 0.6), (0.006, 0.012), (230, 255, 160, 255), (250, 255, 230, 255))
    return K.finish(c)


def holy():
    """A blinding star of holy light with orbs bursting outward."""
    c = K.radial((190, 180, 240, 255), (26, 20, 60, 255), 0.5, 0.5, 0.72)
    rays = mask()
    rd = ImageDraw.Draw(rays)
    for i in range(12):
        a = math.pi * 2 * i / 12
        w = 0.07
        rd.polygon(pts([(0.5, 0.5), (0.5 + math.cos(a - w) * 0.7, 0.5 + math.sin(a - w) * 0.7),
                        (0.5 + math.cos(a + w) * 0.7, 0.5 + math.sin(a + w) * 0.7)]), fill=90)
    K.fill(c, rays.filter(ImageFilter.GaussianBlur(8)), (255, 255, 240, 255))
    orbs = shape(lambda d: [d.ellipse(pts([(0.5 + math.cos(a) * 0.30 - 0.045, 0.5 + math.sin(a) * 0.30 - 0.045),
                                           (0.5 + math.cos(a) * 0.30 + 0.045, 0.5 + math.sin(a) * 0.30 + 0.045)]),
                                      fill=255) for a in (math.pi * 2 * i / 4 + math.pi / 4 for i in range(4))])
    K.glow(c, orbs, (230, 220, 255, 255), 12, 1.4)
    K.fill(c, soften(orbs), (255, 255, 255, 255))
    st = shape(lambda d: d.polygon(pts(star_pts(0.5, 0.5, 4, 0.42, 0.075)), fill=255))
    K.glow(c, st, (255, 250, 220, 255), 30, 1.5)
    K.glow(c, st, (255, 255, 255, 255), 10)
    K.fill(c, soften(st), K.radial((255, 255, 255, 255), (240, 230, 255, 255), 0.5, 0.5, 0.4))
    core = shape(lambda d: d.ellipse(pts([(0.42, 0.42), (0.58, 0.58)]), fill=255))
    K.glow(c, core, (255, 255, 255, 255), 20, 1.6)
    K.fill(c, soften(core), (255, 255, 255, 255))
    return K.finish(c)


# ---- BLM -------------------------------------------------------------------------------------------------------------
def blizzard():
    """A six-armed snowflake of ice."""
    c = K.radial((100, 180, 236, 255), (6, 20, 44, 255), 0.5, 0.45, 0.72)
    motes(c, 31, 22, (0.1, 0.1, 0.9, 0.9), (0.005, 0.012), (200, 240, 255, 255), (240, 250, 255, 230))

    def flake(d):
        wd = int(0.05 * W)
        for i in range(6):
            a = math.pi * 2 * i / 6 - math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            d.line(pts([(0.5, 0.5), (0.5 + ux * 0.38, 0.5 + uy * 0.38)]), fill=255, width=wd)
            for r, L in ((0.22, 0.11), (0.31, 0.07)):
                bx, by = 0.5 + ux * r, 0.5 + uy * r
                for s in (-1, 1):
                    b = a + s * math.radians(55)
                    d.line(pts([(bx, by), (bx + math.cos(b) * L, by + math.sin(b) * L)]), fill=255, width=int(0.035 * W))
            tx, ty = 0.5 + ux * 0.40, 0.5 + uy * 0.40
            d.polygon(pts([(tx + ux * 0.04, ty + uy * 0.04), (tx - uy * 0.03, ty + ux * 0.03),
                           (tx - ux * 0.03, ty - uy * 0.03), (tx + uy * 0.03, ty - ux * 0.03)]), fill=255)
        d.polygon(pts(star_pts(0.5, 0.5, 6, 0.11, 0.07)), fill=255)
    m = shape(flake)
    K.shadow(c, m, 4, 6, 6, 140)
    K.glow(c, m, (150, 220, 255, 255), 18, 1.4)
    K.fill(c, soften(m), K.linear((255, 255, 255, 255), (170, 220, 250, 255), 90))
    core = shape(lambda d: d.ellipse(pts([(0.45, 0.45), (0.55, 0.55)]), fill=255))
    K.fill(c, soften(core), (120, 190, 240, 255))
    return K.finish(c)


def thunder():
    """A forked lightning bolt splitting a storm."""
    c = K.radial((70, 60, 160, 255), (8, 6, 26, 255), 0.5, 0.38, 0.74)
    cloud = dots(17, 14, 0.1, 0.9, 0.06, 0.22, 0.07, 0.13)
    K.fill(c, cloud.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.5)), (150, 140, 220, 255))
    bolt_pts = [(0.58, 0.08), (0.30, 0.50), (0.47, 0.50), (0.36, 0.92), (0.74, 0.40), (0.55, 0.40), (0.70, 0.08)]
    m = shape(lambda d: d.polygon(pts(bolt_pts), fill=255))
    K.glow(c, m, (255, 230, 100, 255), 30, 1.4)
    K.glow(c, m, (255, 255, 200, 255), 10, 1.2)
    K.fill(c, soften(m), K.linear((255, 255, 236, 255), (255, 210, 60, 255), 90))
    sparkles(c, [(0.36, 0.92, 0.08)], (255, 240, 160, 255))
    return K.finish(c)


def stone():
    """Jagged boulders hurled up from the earth."""
    c = K.radial((214, 170, 50, 255), (34, 20, 4, 255), 0.5, 0.42, 0.66)
    dust = dots(23, 16, 0.1, 0.9, 0.62, 0.95, 0.06, 0.12)
    K.fill(c, dust.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.5)), (240, 200, 130, 255))
    rocks = [
        [(0.30, 0.38), (0.46, 0.22), (0.64, 0.24), (0.74, 0.40), (0.70, 0.60), (0.52, 0.68), (0.34, 0.60)],
        [(0.12, 0.62), (0.20, 0.52), (0.32, 0.54), (0.36, 0.68), (0.26, 0.76), (0.14, 0.72)],
        [(0.68, 0.66), (0.78, 0.56), (0.90, 0.62), (0.88, 0.76), (0.74, 0.78)],
        [(0.20, 0.24), (0.27, 0.18), (0.32, 0.25), (0.26, 0.31)],
        [(0.76, 0.16), (0.84, 0.14), (0.86, 0.22), (0.79, 0.25)],
    ]
    m = shape(lambda d: [d.polygon(pts(r), fill=255) for r in rocks])
    K.shadow(c, m, 6, 10, 8, 220)
    K.glow(c, m, (255, 230, 140, 255), 10, 0.8)
    K.fill(c, soften(m), K.linear((196, 170, 140, 255), (84, 62, 46, 255), 90))
    # lit facets on the upper-left of each rock
    facets = shape(lambda d: [d.polygon(pts([r[0], r[1], r[2], ((r[0][0] + r[2][0]) / 2 + 0.01,
                                                                (r[0][1] + r[2][1]) / 2 + 0.06)]), fill=255)
                              for r in rocks[:3]])
    K.fill(c, soften(ImageChops.multiply(facets, m)).point(lambda v: int(v * 0.7)), (255, 244, 210, 255))
    cracks = shape(lambda d: d.line(pts([(0.50, 0.30), (0.54, 0.42), (0.48, 0.50), (0.56, 0.62)]), fill=255,
                                    width=int(0.012 * W)))
    K.fill(c, soften(cracks).point(lambda v: int(v * 0.7)), (80, 50, 24, 255))
    return K.finish(c)


def manafont():
    """A fountain of blue mana gushing without end."""
    c = K.radial((120, 36, 130, 255), (16, 4, 24, 255), 0.5, 0.6, 0.72)

    def jets(d):
        for s in (-1, 1):
            for spread, h, wd in ((0.30, 0.50, 0.045), (0.18, 0.62, 0.045)):
                d.line(pts(bezier((0.5, 0.70), (0.5 + s * spread * 0.3, 0.70 - h * 1.4), (0.5 + s * spread, 0.66))),
                       fill=255, width=int(wd * W), joint='curve')
        d.polygon(pts([(0.45, 0.72), (0.47, 0.28), (0.5, 0.12), (0.53, 0.28), (0.55, 0.72)]), fill=255)
    pool = shape(lambda d: d.ellipse(pts([(0.18, 0.66), (0.82, 0.86)]), fill=255))
    K.glow(c, pool, (100, 200, 255, 255), 16, 1.2)
    K.fill(c, soften(pool), K.linear((170, 230, 255, 255), (40, 100, 220, 255), 90))
    m = shape(jets)
    K.glow(c, m, (90, 210, 255, 255), 20, 1.5)
    K.fill(c, soften(m), K.linear((255, 255, 255, 255), (110, 200, 255, 255), 90))
    drops = shape(lambda d: [d.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
                             for x, y, r in ((0.18, 0.56, 0.022), (0.82, 0.56, 0.022), (0.30, 0.34, 0.018),
                                             (0.70, 0.34, 0.018), (0.5, 0.08, 0.02), (0.13, 0.42, 0.014),
                                             (0.87, 0.42, 0.014))])
    K.glow(c, drops, (120, 220, 255, 255), 8, 1.3)
    K.fill(c, soften(drops), (230, 248, 255, 255))
    return K.finish(c)


def sleep():
    """A crescent moon trailing drowsy Zs."""
    c = K.radial((40, 54, 120, 255), (4, 6, 22, 255), 0.42, 0.45, 0.72)
    motes(c, 41, 18, (0.1, 0.1, 0.9, 0.9), (0.004, 0.009), (200, 210, 255, 255), (240, 240, 255, 230))
    disc = shape(lambda d: d.ellipse(pts([(0.16, 0.22), (0.66, 0.72)]), fill=255))
    bite = shape(lambda d: d.ellipse(pts([(0.30, 0.12), (0.78, 0.60)]), fill=255))
    moon = ImageChops.subtract(disc, bite)
    K.glow(c, moon, (255, 230, 150, 255), 22, 1.4)
    K.fill(c, soften(moon), K.linear((255, 250, 220, 255), (240, 200, 110, 255), 90))

    def z(d, x, y, s):
        t = 0.06 * s
        d.polygon(pts([(x, y), (x + s, y), (x + s, y + t), (x + t * 1.3, y + s - t), (x + s, y + s - t), (x + s, y + s),
                       (x, y + s), (x, y + s - t), (x + s - t * 1.3, y + t), (x, y + t)]), fill=255)
    zs = shape(lambda d: [z(d, 0.56, 0.52, 0.22), z(d, 0.68, 0.30, 0.15), z(d, 0.76, 0.15, 0.10)])
    K.shadow(c, zs, 3, 5, 5, 140)
    K.glow(c, zs, (180, 200, 255, 255), 10, 1.2)
    K.fill(c, soften(zs), (240, 244, 255, 255))
    return K.finish(c)


# ---- RDM -------------------------------------------------------------------------------------------------------------
def chainspell():
    """Two golden chain links locked together, spell chained to spell."""
    c = K.radial((170, 24, 50, 255), (24, 2, 10, 255), 0.5, 0.5, 0.72)
    swirl = shape(lambda d: [d.arc(pts([(0.5 - r, 0.5 - r), (0.5 + r, 0.5 + r)]), a, a + 100, fill=255,
                                   width=int(0.02 * W)) for r, a in ((0.42, 200), (0.42, 20))])
    K.fill(c, swirl.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.55)), (255, 160, 170, 255))

    def link(cx, cy):
        m = shape(lambda d: d.rounded_rectangle(pts([(cx - 0.25, cy - 0.13), (cx + 0.25, cy + 0.13)]),
                                                radius=0.13 * W, outline=255, width=int(0.065 * W)))
        return rotated(m, 45, cx, cy)
    a, b = link(0.37, 0.63), link(0.63, 0.37)
    gold = K.linear((255, 240, 170, 255), (196, 124, 36, 255), 90)
    for m in (a, b):
        K.shadow(c, m, 4, 6, 6, 160)
        K.glow(c, m, (255, 190, 90, 255), 14, 1.2)
        K.fill(c, soften(m), gold)
    over = shape(lambda d: d.ellipse(pts([(0.52, 0.52), (0.68, 0.68)]), fill=255))
    K.shadow(c, ImageChops.multiply(a, over), 3, 4, 4, 160)
    K.fill(c, soften(ImageChops.multiply(a, over)), gold)
    sparkles(c, [(0.80, 0.78, 0.07), (0.20, 0.22, 0.06)], (255, 200, 200, 255))
    return K.finish(c)


def refresh():
    """A drop of mana with a renewing swirl."""
    c = K.radial((30, 80, 180, 255), (4, 8, 30, 255), 0.5, 0.45, 0.72)
    arc = shape(lambda d: [arc_arrow(d, 0.5, 0.54, 0.36, 160, 330, 0.035, 0.05),
                           arc_arrow(d, 0.5, 0.54, 0.36, -20, 150, 0.035, 0.05)])
    K.glow(c, arc, (130, 210, 255, 255), 10, 1.2)
    K.fill(c, soften(arc), (210, 240, 255, 255))

    def drop(d):
        d.ellipse(pts([(0.33, 0.42), (0.67, 0.76)]), fill=255)
        d.polygon(pts([(0.5, 0.14), (0.665, 0.56), (0.335, 0.56)]), fill=255)
    m = shape(drop)
    K.shadow(c, m, 4, 7, 7, 150)
    K.glow(c, m, (100, 200, 255, 255), 22, 1.4)
    K.fill(c, soften(m), K.linear((230, 248, 255, 255), (40, 120, 240, 255), 90))
    hl = shape(lambda d: d.ellipse(pts([(0.40, 0.50), (0.47, 0.64)]), fill=255))
    K.fill(c, soften(hl, 4), (255, 255, 255, 230))
    return K.finish(c)


def haste():
    """Double chevrons streaking forward in a rush of wind."""
    c = K.radial((210, 170, 40, 255), (40, 24, 4, 255), 0.4, 0.5, 0.74)
    streaks = shape(lambda d: [d.rounded_rectangle(pts([(x0, y - 0.016), (x1, y + 0.016)]), radius=0.016 * W, fill=255)
                               for x0, x1, y in ((0.08, 0.36, 0.30), (0.04, 0.30, 0.50), (0.08, 0.36, 0.70),
                                                 (0.16, 0.30, 0.40), (0.16, 0.30, 0.60))])
    K.glow(c, streaks, (255, 240, 170, 255), 8)
    K.fill(c, soften(streaks).point(lambda v: int(v * 0.8)), (255, 250, 220, 255))

    def chev(d, x):
        d.polygon(pts([(x, 0.22), (x + 0.15, 0.22), (x + 0.33, 0.50), (x + 0.15, 0.78), (x, 0.78), (x + 0.18, 0.50)]),
                  fill=255)
    m = shape(lambda d: [chev(d, 0.30), chev(d, 0.52)])
    K.shadow(c, m, 5, 8, 8, 170)
    K.glow(c, m, (255, 230, 120, 255), 16, 1.3)
    K.fill(c, soften(m), K.linear((255, 255, 240, 255), (240, 150, 40, 255), 90))
    return K.finish(c)


def phalanx():
    """Three shields locked edge to edge in a phalanx wall."""
    c = K.radial((70, 110, 190, 255), (6, 12, 34, 255), 0.5, 0.45, 0.72)
    wall = shape(lambda d: d.ellipse(pts([(0.12, 0.20), (0.88, 0.80)]), fill=255))
    K.fill(c, wall.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.5)), (170, 210, 255, 255))
    for cx, top, w, h, front in ((0.27, 0.26, 0.15, 0.44, False), (0.73, 0.26, 0.15, 0.44, False),
                                 (0.5, 0.20, 0.20, 0.60, True)):
        m = shape(lambda d, cx=cx, top=top, w=w, h=h: heater(d, cx, top, w, h))
        K.shadow(c, m, 5, 8, 8, 170)
        if front:
            K.glow(c, m, (170, 220, 255, 255), 16, 1.3)
            K.fill(c, soften(m), K.linear((255, 255, 255, 255), (150, 175, 210, 255), 90))
            inner = shape(lambda d: heater(d, 0.5, 0.26, 0.145, 0.48))
            K.fill(c, soften(inner), K.linear((110, 150, 220, 255), (36, 60, 130, 255), 90))
            st = shape(lambda d: K.sparkle(d, 0.5, 0.46, 0.14, 0.22))
            K.glow(c, st, (200, 230, 255, 255), 8)
            K.fill(c, soften(st), (240, 248, 255, 255))
        else:
            K.fill(c, soften(m), K.linear((210, 220, 236, 255), (100, 116, 150, 255), 90))
    return K.finish(c)


def convert():
    """Life and mana swapping places: a red and a blue arrow chasing each other."""
    c = K.radial((100, 50, 150, 255), (12, 6, 26, 255), 0.5, 0.5, 0.72)
    red = shape(lambda d: arc_arrow(d, 0.5, 0.5, 0.30, 190, 340, 0.08, 0.085))
    blue = shape(lambda d: arc_arrow(d, 0.5, 0.5, 0.30, 10, 160, 0.08, 0.085))
    for m, g, top, bot in ((red, (255, 80, 80, 255), (255, 200, 180, 255), (220, 40, 50, 255)),
                           (blue, (80, 160, 255, 255), (200, 236, 255, 255), (40, 100, 230, 255))):
        K.shadow(c, m, 4, 7, 7, 150)
        K.glow(c, m, g, 16, 1.4)
        K.fill(c, soften(m), K.linear(top, bot, 90))
    orb = shape(lambda d: d.ellipse(pts([(0.42, 0.42), (0.58, 0.58)]), fill=255))
    K.glow(c, orb, (255, 240, 255, 255), 16, 1.4)
    K.fill(c, soften(orb), (255, 250, 255, 255))
    return K.finish(c)


def dia():
    """A stinging orb of light, its spikes piercing the target's guard."""
    c = K.radial((40, 150, 150, 255), (4, 22, 26, 255), 0.5, 0.5, 0.72)
    spikes = shape(lambda d: d.polygon(pts(star_pts(0.5, 0.5, 12, 0.42, 0.20, -math.pi / 2)), fill=255))
    K.glow(c, spikes, (255, 255, 200, 255), 20, 1.2)
    K.fill(c, soften(spikes), K.radial((255, 255, 230, 255), (230, 220, 140, 255), 0.5, 0.5, 0.42))
    orb = shape(lambda d: d.ellipse(pts([(0.30, 0.30), (0.70, 0.70)]), fill=255))
    K.shadow(c, orb, 3, 5, 6, 100)
    K.glow(c, orb, (255, 255, 255, 255), 14, 1.4)
    K.fill(c, soften(orb), K.radial((255, 255, 255, 255), (250, 240, 170, 255), 0.45, 0.42, 0.22))
    return K.finish(c)


ICONS = {
    ('ja', 'Berserk'): berserk,
    ('ja', 'Warcry'): warcry,
    ('ja', 'Mighty Strikes'): mighty_strikes,
    ('ja', 'Retaliation'): retaliation,
    ('ja', 'Chakra'): chakra,
    ('ja', 'Boost'): boost,
    ('ja', 'Focus'): focus,
    ('ja', 'Counterstance'): counterstance,
    ('ma', 'Curaga'): curaga,
    ('ma', 'Raise'): raise_,
    ('ma', 'Regen'): regen,
    ('ma', 'Holy'): holy,
    ('ma', 'Blizzard'): blizzard,
    ('ma', 'Thunder'): thunder,
    ('ma', 'Stone'): stone,
    ('ja', 'Manafont'): manafont,
    ('ma', 'Sleep'): sleep,
    ('ja', 'Chainspell'): chainspell,
    ('ma', 'Refresh'): refresh,
    ('ma', 'Haste'): haste,
    ('ma', 'Phalanx'): phalanx,
    ('ja', 'Convert'): convert,
    ('ma', 'Dia'): dia,
}
COVERS = {'Stone': ['Stone', 'Quake']}
