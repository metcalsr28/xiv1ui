"""xiv1ui's signature action icons: hand-drawn round paintings for a handful of each job's best-known spells and
abilities, drawn in place of the slot's disc and generated emblem (tools/make_action_icons.py does the rest).

Run: nix-shell --run 'python3 tools/make_signature_icons.py [names...]'
Writes addons/xiv1ui/assets/sig_<slug>.png (64x64 canvases, art 44x44 at the top-left), and
addons/xiv1ui/core/signature_icons.lua (action name -> texture).

Each icon is painted at 8x on a 352-pixel square: a background (radial gradient), the motif with gradient fills,
glows and highlights, a vignette and a thin gold rim, then cut to a circle and scaled down.
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), '..')
ASSETS = os.path.join(ROOT, 'addons', 'xiv1ui', 'assets')
OUT = os.path.join(ROOT, 'tools', 'sig_icons', 'out')         # the PNGs (not shipped: packed into PAK)
PAK = os.path.join(ASSETS, 'sig_icons.pak')
os.makedirs(OUT, exist_ok=True)
LUA = os.path.join(ROOT, 'addons', 'xiv1ui', 'core', 'signature_icons.lua')

S = 44            # art size on the bar (HUD pixels)
K = 8             # painting scale
W = S * K


# ---- painting kit ---------------------------------------------------------------------------------------------------
def p(x, y):
    """Unit coordinates (0..1) -> canvas pixels."""
    return (x * W, y * W)


def pts(seq):
    return [p(x, y) for x, y in seq]


def mask():
    return Image.new('L', (W, W), 0)


def radial(c0, c1, cx=0.5, cy=0.5, r=0.75):
    """A radial gradient: c0 at (cx, cy), c1 at distance r and beyond."""
    img = Image.new('RGBA', (W, W))
    px = img.load()
    for y in range(0, W, 2):
        for x in range(0, W, 2):
            d = min(1.0, math.hypot(x / W - cx, y / W - cy) / r)
            col = tuple(int(c0[i] + (c1[i] - c0[i]) * d) for i in range(4))
            px[x, y] = col
            if x + 1 < W:
                px[x + 1, y] = col
            if y + 1 < W:
                px[x, y + 1] = col
                if x + 1 < W:
                    px[x + 1, y + 1] = col
    return img


def linear(c0, c1, angle=90):
    """A linear gradient from c0 to c1 along `angle` degrees (90 = top to bottom)."""
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    grad = Image.linear_gradient('L').resize((W, W))
    grad = grad.rotate(90 - angle, resample=Image.BICUBIC, expand=False, fillcolor=None)
    img = Image.new('RGBA', (W, W))
    base = Image.new('RGBA', (W, W), c0)
    top = Image.new('RGBA', (W, W), c1)
    return Image.composite(top, base, grad)


def fill(canvas, m, paint):
    """Paint `paint` (a colour or an RGBA image) through mask m."""
    if isinstance(paint, tuple):
        paint = Image.new('RGBA', (W, W), paint)
    layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    layer.paste(paint, (0, 0), m)
    canvas.alpha_composite(layer)


def glow(canvas, m, color, radius=18, strength=1.0):
    """A soft light around mask m (additive-looking: a blurred copy under the shape)."""
    g = m.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = g.point(lambda v: min(255, int(v * strength)))
    fill(canvas, g, color)


def shadow(canvas, m, dx=6, dy=10, radius=10, alpha=170):
    sh = ImageChops.offset(m, dx, dy).filter(ImageFilter.GaussianBlur(radius))
    sh = sh.point(lambda v: int(v * alpha / 255))
    fill(canvas, sh, (8, 4, 14, 255))


def shape(draw_fn):
    m = mask()
    draw_fn(ImageDraw.Draw(m))
    return m


def soften(m, r=1.2):
    return m.filter(ImageFilter.GaussianBlur(r))


def sparkle(d, x, y, r, w=0.18):
    """A four-pointed star."""
    d.polygon(pts([(x, y - r), (x + r * w, y - r * w), (x + r, y), (x + r * w, y + r * w),
                   (x, y + r), (x - r * w, y + r * w), (x - r, y), (x - r * w, y - r * w)]), fill=255)


def finish(canvas, rim=(232, 196, 120)):
    """Vignette, glass highlight, gold rim; cut to a circle and scale to the bar's size."""
    vig = mask()
    ImageDraw.Draw(vig).ellipse(pts([(0.0, 0.0), (1.0, 1.0)]), fill=255)
    inner = mask()
    ImageDraw.Draw(inner).ellipse(pts([(0.12, 0.12), (0.88, 0.88)]), fill=255)
    ring = ImageChops.subtract(vig, inner).filter(ImageFilter.GaussianBlur(22))
    fill(canvas, ring.point(lambda v: int(v * 0.75)), (6, 2, 12, 255))
    hi = shape(lambda d: d.ellipse(pts([(0.16, 0.06), (0.76, 0.42)]), fill=255))
    hi = hi.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.16))
    fill(canvas, hi, (255, 255, 255, 255))
    circle = shape(lambda d: d.ellipse(pts([(0.02, 0.02), (0.98, 0.98)]), fill=255))
    rimm = ImageChops.subtract(circle, shape(lambda d: d.ellipse(pts([(0.045, 0.045), (0.955, 0.955)]), fill=255)))
    fill(canvas, rimm, rim + (255,))
    out = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), soften(circle, 1.5))
    small = out.resize((S, S), Image.LANCZOS)
    page = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    page.paste(small, (0, 0))
    return page


# ---- the icons ----------------------------------------------------------------------------------------------------
def cure():
    c = radial((70, 150, 96, 255), (10, 34, 22, 255), 0.5, 0.42, 0.7)
    # rising motes
    rnd = random.Random(3)
    motes = mask()
    md = ImageDraw.Draw(motes)
    for _ in range(26):
        x, y, r = rnd.uniform(0.15, 0.85), rnd.uniform(0.2, 0.9), rnd.uniform(0.008, 0.022)
        md.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    glow(c, motes, (170, 255, 190, 255), 6)
    fill(c, motes, (220, 255, 230, 220))
    # the cross of light
    cross = shape(lambda d: [d.rounded_rectangle(pts([(0.40, 0.18), (0.60, 0.82)]), radius=0.05 * W, fill=255),
                             d.rounded_rectangle(pts([(0.18, 0.40), (0.82, 0.60)]), radius=0.05 * W, fill=255)])
    glow(c, cross, (120, 255, 160, 255), 34, 1.4)
    glow(c, cross, (210, 255, 220, 255), 12)
    fill(c, soften(cross), linear((255, 255, 250, 255), (176, 246, 196, 255), 90))
    st = shape(lambda d: [sparkle(d, 0.76, 0.24, 0.09), sparkle(d, 0.26, 0.74, 0.06)])
    glow(c, st, (200, 255, 210, 255), 8)
    fill(c, soften(st), (255, 255, 255, 255))
    return finish(c)


def fire():
    c = radial((150, 46, 18, 255), (24, 4, 6, 255), 0.5, 0.62, 0.66)

    def flame(d, cx, base, w, h, lean=0.0):
        steps = 40
        left, right = [], []
        for i in range(steps + 1):
            t = i / steps
            y = base - h * t
            half = w * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (1 - t) ** 0.35
            x = cx + lean * t * t
            left.append((x - half, y))
            right.append((x + half, y))
        d.polygon(pts(left + right[::-1]), fill=255)
    outer = shape(lambda d: [flame(d, 0.5, 0.86, 0.27, 0.70, 0.04), flame(d, 0.33, 0.86, 0.12, 0.40, -0.06),
                             flame(d, 0.67, 0.86, 0.12, 0.44, 0.07)])
    mid = shape(lambda d: flame(d, 0.5, 0.86, 0.18, 0.52, 0.03))
    core = shape(lambda d: flame(d, 0.5, 0.86, 0.10, 0.32, 0.01))
    glow(c, outer, (255, 110, 30, 255), 30, 1.3)
    fill(c, soften(outer), linear((255, 200, 70, 255), (230, 60, 20, 255), 270))
    fill(c, soften(mid), linear((255, 236, 140, 255), (255, 140, 40, 255), 270))
    glow(c, core, (255, 255, 220, 255), 10)
    fill(c, soften(core), (255, 252, 230, 255))
    sparks = mask()
    sd = ImageDraw.Draw(sparks)
    rnd = random.Random(7)
    for _ in range(14):
        x, y, r = rnd.uniform(0.25, 0.75), rnd.uniform(0.08, 0.4), rnd.uniform(0.006, 0.014)
        sd.ellipse(pts([(x - r, y - r), (x + r, y + r)]), fill=255)
    glow(c, sparks, (255, 180, 80, 255), 5)
    fill(c, sparks, (255, 230, 160, 255))
    return finish(c)


def figure(d, cx, cy, s):
    """A running ninja silhouette (head, scarf, body, legs) around (cx, cy), scale s."""
    def q(x, y):
        return (cx + x * s, cy + y * s)
    d.ellipse([p(*q(-0.07, -0.42)), p(*q(0.07, -0.28))], fill=255)                     # head
    d.polygon([p(*q(-0.06, -0.28)), p(*q(0.10, -0.26)), p(*q(0.12, 0.02)), p(*q(-0.10, 0.04))], fill=255)  # body
    d.polygon([p(*q(0.04, -0.30)), p(*q(-0.30, -0.36)), p(*q(-0.26, -0.30)), p(*q(0.02, -0.25))], fill=255)  # scarf
    d.polygon([p(*q(-0.10, 0.02)), p(*q(0.0, 0.02)), p(*q(-0.18, 0.36)), p(*q(-0.28, 0.34))], fill=255)   # leg
    d.polygon([p(*q(0.02, 0.0)), p(*q(0.12, 0.02)), p(*q(0.26, 0.30)), p(*q(0.18, 0.36))], fill=255)       # leg
    d.polygon([p(*q(0.08, -0.22)), p(*q(0.30, -0.10)), p(*q(0.27, -0.05)), p(*q(0.06, -0.14))], fill=255)  # arm


def utsusemi():
    c = radial((96, 120, 196, 255), (12, 14, 34, 255), 0.5, 0.42, 0.72)
    smoke = mask()
    sd = ImageDraw.Draw(smoke)
    rnd = random.Random(11)
    for _ in range(20):
        x, y, r = rnd.uniform(0.12, 0.88), rnd.uniform(0.62, 0.95), rnd.uniform(0.06, 0.13)
        sd.ellipse(pts([(x - r, y - r * 0.55), (x + r, y + r * 0.55)]), fill=120)
    fill(c, smoke.filter(ImageFilter.GaussianBlur(16)), (190, 210, 255, 255))
    # the shadow copies (cyan, fading), then the ninja with a bright rim
    for dx, a in ((-0.22, 80), (-0.11, 140)):
        ghost = shape(lambda d, dx=dx: figure(d, 0.54 + dx, 0.54, 0.78))
        fill(c, soften(ghost, 2).point(lambda v, a=a: int(v * a / 255)), (120, 230, 255, 255))
    ninja = shape(lambda d: figure(d, 0.56, 0.54, 0.78))
    glow(c, ninja, (200, 236, 255, 255), 10, 1.6)
    fill(c, soften(ninja), linear((34, 36, 70, 255), (10, 10, 24, 255), 90))
    doll = shape(lambda d: d.polygon(pts([(0.75, 0.15), (0.81, 0.15), (0.80, 0.24), (0.86, 0.28), (0.85, 0.33),
                                          (0.80, 0.31), (0.79, 0.40), (0.77, 0.40), (0.76, 0.31), (0.71, 0.33),
                                          (0.70, 0.28), (0.76, 0.24)]), fill=255))
    glow(c, doll, (230, 240, 255, 255), 8, 1.3)
    fill(c, soften(doll), (250, 248, 240, 255))
    return finish(c)


def provoke():
    c = radial((150, 30, 30, 255), (22, 4, 6, 255), 0.5, 0.5, 0.7)
    burst = mask()
    bd = ImageDraw.Draw(burst)
    n = 14
    star = []
    for i in range(n * 2):
        a = math.pi * i / n - math.pi / 2
        r = 0.42 if i % 2 == 0 else 0.24
        star.append((0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r))
    bd.polygon(pts(star), fill=255)
    glow(c, burst, (255, 80, 50, 255), 26, 1.2)
    fill(c, soften(burst), radial((255, 220, 120, 255), (230, 70, 40, 255), 0.5, 0.5, 0.42))
    mark = shape(lambda d: [d.rounded_rectangle(pts([(0.45, 0.24), (0.55, 0.58)]), radius=0.03 * W, fill=255),
                            d.ellipse(pts([(0.445, 0.64), (0.555, 0.75)]), fill=255)])
    shadow(c, mark, 4, 6, 6, 150)
    fill(c, soften(mark), (255, 252, 240, 255))
    return finish(c)


def fist_front(d, cx, cy, s):
    """A fist seen from the front: four knuckles over the folded fingers, the thumb across them."""
    def q(x, y):
        return p(cx + x * s, cy + y * s)
    d.rounded_rectangle([q(-0.22, -0.14), q(0.22, 0.20)], radius=0.08 * W * s, fill=255)
    for i in range(4):
        x = -0.165 + i * 0.11
        d.ellipse([q(x - 0.06, -0.22), q(x + 0.06, -0.08)], fill=255)
    d.rounded_rectangle([q(-0.24, 0.02), q(0.10, 0.12)], radius=0.05 * W * s, fill=255)


def fist_lines(d, cx, cy, s):
    def q(x, y):
        return p(cx + x * s, cy + y * s)
    for i in range(3):
        x = -0.11 + i * 0.11
        d.line([q(x, -0.12), q(x, 0.02)], fill=255, width=max(1, int(0.014 * W * s)))
    d.line([q(-0.22, 0.02), q(0.10, 0.02)], fill=255, width=max(1, int(0.012 * W * s)))


def hundred_fists():
    c = radial((196, 120, 50, 255), (30, 12, 6, 255), 0.5, 0.5, 0.72)
    burst = mask()
    bd = ImageDraw.Draw(burst)
    for i in range(24):
        a = math.pi * 2 * i / 24
        bd.line(pts([(0.5 + math.cos(a) * 0.20, 0.5 + math.sin(a) * 0.20),
                     (0.5 + math.cos(a) * 0.48, 0.5 + math.sin(a) * 0.48)]), fill=140, width=int(0.012 * W))
    fill(c, burst.filter(ImageFilter.GaussianBlur(3)), (255, 230, 170, 255))
    # a ring of after-images, then the fist
    for i in range(6):
        a = math.pi * 2 * i / 6 + 0.3
        x, y = 0.5 + math.cos(a) * 0.24, 0.5 + math.sin(a) * 0.24
        g = shape(lambda d, x=x, y=y: fist_front(d, x, y, 0.5))
        fill(c, soften(g, 3).point(lambda v: int(v * 0.42)), (255, 210, 150, 255))
    main = shape(lambda d: fist_front(d, 0.5, 0.52, 0.95))
    glow(c, main, (255, 190, 100, 255), 24, 1.3)
    shadow(c, main, 5, 8, 8, 150)
    fill(c, soften(main), linear((255, 232, 196, 255), (222, 146, 92, 255), 90))
    lines = shape(lambda d: fist_lines(d, 0.5, 0.52, 0.95))
    fill(c, soften(lines, 1.5).point(lambda v: int(v * 0.7)), (120, 60, 36, 255))
    return finish(c)


def benediction():
    c = radial((240, 214, 140, 255), (60, 40, 24, 255), 0.5, 0.42, 0.7)
    rays = mask()
    rd = ImageDraw.Draw(rays)
    for i in range(16):
        a = math.pi * 2 * i / 16
        w = 0.05
        rd.polygon(pts([(0.5, 0.42), (0.5 + math.cos(a - w) * 0.7, 0.42 + math.sin(a - w) * 0.7),
                        (0.5 + math.cos(a + w) * 0.7, 0.42 + math.sin(a + w) * 0.7)]), fill=90)
    fill(c, rays.filter(ImageFilter.GaussianBlur(8)), (255, 250, 220, 255))

    def wing(d, side):
        feathers = []
        for i in range(5):
            t = i / 4
            ang = math.radians(-20 - 40 * t) if side > 0 else math.radians(200 + 40 * t)
            length = 0.36 - 0.05 * t
            bx, by = 0.5 + side * 0.06, 0.52
            ex, ey = bx + math.cos(ang) * length, by + math.sin(ang) * length
            nx, ny = -math.sin(ang) * 0.045, math.cos(ang) * 0.045
            d.polygon(pts([(bx + nx, by + ny), (ex, ey), (bx - nx, by - ny)]), fill=255)
    wings = shape(lambda d: [wing(d, 1), wing(d, -1)])
    glow(c, wings, (255, 255, 230, 255), 16)
    fill(c, soften(wings), linear((255, 255, 250, 255), (238, 222, 180, 255), 90))
    halo = shape(lambda d: d.ellipse(pts([(0.36, 0.14), (0.64, 0.26)]), outline=255, width=int(0.03 * W)))
    glow(c, halo, (255, 236, 150, 255), 10, 1.3)
    fill(c, soften(halo), (255, 240, 170, 255))
    heart = shape(lambda d: [d.ellipse(pts([(0.43, 0.46), (0.57, 0.62)]), fill=255)])
    glow(c, heart, (255, 255, 255, 255), 18, 1.4)
    fill(c, soften(heart), (255, 255, 252, 255))
    return finish(c)


# (kind, name): painter. `name` is the texture's name; the actions it covers are COVERS[name] (default: just
# itself). Spells match by family (tiers share), abilities by name. More painters live in tools/sig_icons/*.py, each
# with its own ICONS (and COVERS) merged in here.
ICONS = {
    ('ma', 'Cure'): cure,
    ('ma', 'Fire'): fire,
    ('ma', 'Utsusemi'): utsusemi,
    ('ja', 'Provoke'): provoke,
    ('ja', 'Hundred Fists'): hundred_fists,
    ('ja', 'Benediction'): benediction,
}
COVERS = {}
# Recoloured variants of one painting: VARIANTS[name] = {action name: hue shift in degrees (or None for the
# original)}. Each gets its own texture (sig_<slug>_<member slug>), the rim staying gold. Tiers don't need this:
# they share their family's painting and the bar shows the numeral.
VARIANTS = {}


# Light and Dark can't be reached by a hue turn alone (they came out yellow and magenta, close to Earth and
# Thunder): a variant may give (degrees, saturation factor, brightness factor) instead of degrees.
LIGHT = (45, 0.30, 1.30)      # pale gold-white
DARK = (275, 1.0, 1.0)        # the purple (owner: Dark takes the purple Thunder had)
THUNDER = (38, 1.4, 4.0)      # orange-yellow (owner picked it on Sulpor); the lift spares the bright motif
EARTH = (24, 1.0, 0.78)      # darker brown


def recolor(img, degrees):
    """The painting with its hues turned by `degrees` (or a (degrees, saturation, brightness) tuple), the gold rim
    (outside 0.86 of the radius) left alone."""
    sat_k, val_k = 1.0, 1.0
    if isinstance(degrees, tuple):
        degrees, sat_k, val_k = degrees
    if not degrees and sat_k == 1.0 and val_k == 1.0:
        return img
    art = img.crop((0, 0, S, S)).convert('RGBA')
    r, g, b, a = art.split()
    hsv = Image.merge('RGB', (r, g, b)).convert('HSV')
    h, sat, v = hsv.split()
    shift = int(degrees / 360 * 255) % 256
    h = h.point(lambda x: (x + shift) % 256)
    if sat_k != 1.0:
        sat = sat.point(lambda x: min(255, int(x * sat_k)))
    if val_k != 1.0:
        # (lifts the dark background most and the bright motif hardly at all, so a big lift doesn't wash it out)
        v = v.point(lambda x: min(255, int(x + x * (val_k - 1) * (1 - x / 255) ** 2)))
    turned = Image.merge('HSV', (h, sat, v)).convert('RGB')
    turned.putalpha(a)
    keep = Image.new('L', (S, S), 0)
    ImageDraw.Draw(keep).ellipse((S * 0.07, S * 0.07, S * 0.93, S * 0.93), fill=255)
    out = art.copy()
    out.paste(turned, (0, 0), keep.filter(ImageFilter.GaussianBlur(0.6)))
    page = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    page.paste(out, (0, 0))
    return page


def load_plugins():
    import importlib
    d = os.path.join(os.path.dirname(__file__), 'sig_icons')
    if not os.path.isdir(d):
        return
    sys.path.insert(0, d)
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.py') and not fn.startswith('_'):
            try:
                m = importlib.import_module(fn[:-3])
            except Exception as e:          # (one painter's broken file mustn't stop the others)
                print('skipped %s: %s' % (fn, e), file=sys.stderr)
                continue
            ICONS.update(getattr(m, 'ICONS', {}))
            COVERS.update(getattr(m, 'COVERS', {}))
            VARIANTS.update(getattr(m, 'VARIANTS', {}))


def slug(name):
    return ''.join(ch if ch.isalnum() else '_' for ch in name.lower()).strip('_')


def sheet(entries, path):
    """A review sheet: each icon large and at bar size, with its name."""
    from PIL import ImageFont
    cols = 6
    rows = (len(entries) + cols - 1) // cols
    o = Image.new('RGBA', (cols * 160, rows * 200), (30, 28, 40, 255))
    d = ImageDraw.Draw(o)
    for i, (_, name, tex) in enumerate(entries):
        im = Image.open(os.path.join(OUT, tex + '.png')).crop((0, 0, S, S))
        x, y = (i % cols) * 160, (i // cols) * 200
        o.alpha_composite(im.resize((132, 132), Image.LANCZOS), (x + 14, y + 6))
        o.alpha_composite(im, (x + 58, y + 142))
        d.text((x + 8, y + 186), name, fill=(230, 226, 214, 255))
    o.save(path)


def write_pak(textures):
    """Every icon PNG in one file for the addon (one download for the in-game updater, one file open):
    b'XSIGPAK1', u32 count, then count x (u16 name length, name, u32 offset, u32 size), then the PNGs."""
    import struct
    blobs = [(t, open(os.path.join(OUT, t + '.png'), 'rb').read()) for t in textures]
    head = b'XSIGPAK1' + struct.pack('<I', len(blobs))
    index_len = sum(2 + len(t.encode()) + 8 for t, _ in blobs)
    off = len(head) + index_len
    index, data = b'', b''
    for t, b in blobs:
        n = t.encode()
        index += struct.pack('<H', len(n)) + n + struct.pack('<II', off, len(b))
        off += len(b)
        data += b
    with open(PAK, 'wb') as f:
        f.write(head + index + data)
    print('packed %d icons into %s (%d bytes)' % (len(blobs), PAK, off))


def main(only, sheet_path=None):
    load_plugins()
    entries = []
    for (kind, name), fn in ICONS.items():
        if only and name not in only:
            continue
        img = fn()
        if name in VARIANTS:
            for member, deg in VARIANTS[name].items():
                tex = 'sig_' + slug(name) + '_' + slug(member)
                recolor(img, deg).save(os.path.join(OUT, tex + '.png'))
                entries.append((kind, member, tex))
                print('wrote', tex)
            continue
        tex = 'sig_' + slug(name)
        img.save(os.path.join(OUT, tex + '.png'))
        entries.append((kind, name, tex))
        print('wrote', tex)
    if sheet_path:
        sheet(entries, sheet_path)
    if not only:
        write_pak(sorted(set(t for _, _, t in entries)))
        with open(os.path.join(ASSETS, 'signature_icons_manifest.lua'), 'w') as f:
            f.write('-- Generated by tools/make_signature_icons.py: content size of each signature icon texture.\nreturn {\n')
            for _, _, t in entries:
                f.write("    ['%s'] = { %d, %d },\n" % (t, S, S))
            f.write('};\n')
        with open(LUA, 'w') as f:
            f.write('-- Generated by tools/make_signature_icons.py: action name -> signature icon (a round painting\n')
            f.write('-- drawn in place of the slot\'s disc and emblem). Spells by family (Cure II uses Cure\'s).\n')
            f.write('return {\n')
            for kind in ('ma', 'ja'):
                f.write('    %s = {\n' % kind)
                for k, n, t in entries:
                    if k == kind:
                        for cover in COVERS.get(n, [n]):
                            f.write("        ['%s'] = '%s',\n" % (cover.replace("'", "\\'"), t))
                f.write('    },\n')
            f.write('};\n')


if __name__ == '__main__':
    args = sys.argv[1:]
    sheet_path = None
    if args and args[0].startswith('--sheet='):
        sheet_path = args.pop(0)[len('--sheet='):]
    main(set(args), sheet_path)
