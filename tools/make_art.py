"""Generate xiv1ui textures (original art in the style of the FFXIV 1.0 HUD).

Run: nix-shell --run 'python3 tools/make_art.py'
Writes addons/xiv1ui/assets/*.png plus assets/manifest.lua with each image's content size. Canvases are padded to
power-of-two sizes because D3DX8 rescales other sizes; the art always sits at the top-left of its canvas.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), '..', 'addons', 'xiv1ui', 'assets')
SS = 4  # supersampling factor
manifest = {}


def pow2(n):
    p = 1
    while p < n:
        p *= 2
    return p


def save(name, img):
    """img is at final resolution; pad to power-of-two and record its size."""
    w, h = img.size
    canvas = Image.new('RGBA', (pow2(w), pow2(h)), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    canvas.save(os.path.join(ROOT, name + '.png'))
    manifest[name] = (w, h)


def down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def hgrad(w, h, stops):
    """Horizontal gradient through (pos 0..1, (r,g,b,a)) stops."""
    img = Image.new('RGBA', (w, h))
    px = img.load()
    for x in range(w):
        t = x / max(1, w - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = (t - p0) / max(1e-6, p1 - p0)
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(4))
                break
        for y in range(h):
            px[x, y] = c
    return img


def vgloss(img, top=0.55, strength=110):
    """Brighten the upper part of an image (glass highlight) and darken the bottom slightly."""
    w, h = img.size
    over = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for y in range(h):
        t = y / max(1, h - 1)
        if t < top:
            a = int(strength * (1 - t / top) ** 1.5)
            d.line([(0, y), (w, y)], fill=(255, 255, 255, a))
        else:
            a = int(60 * (t - top) / (1 - top))
            d.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    return Image.alpha_composite(img, over)


def parallelogram_mask(w, h, slant):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).polygon([(slant, 0), (w, 0), (w - slant, h), (0, h)], fill=255)
    return m


# ---------------------------------------------------------------- gauges (final 1.0 style, reference §8)
GW, GH = 172, 9  # tube length/height, final pixels


def vgrad(w, h, stops):
    """Vertical gradient through (pos 0..1, (r,g,b,a)) stops."""
    img = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = (t - p0) / max(1e-6, p1 - p0)
                c = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(4))
                break
        d.line([(0, y), (w, y)], fill=c)
    return img


def capsule_mask(w, h):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=255)
    return m


def tube_mask(w, h):
    """Tube body: a slightly rounded rectangle (square-ended, to sit between the stop bars)."""
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=min(h // 3, 2 * SS), fill=255)
    return m


def stop_bars(d, o, w, h, pad):
    """Flat silver stop bars at both ends of a tube, standing a little proud of it."""
    bw = max(2 * SS, h // 4)
    over = min(pad * SS - SS, 2 * SS)
    for x in (o, o + w - bw):
        d.rectangle([x, o - over, x + bw - 1, o + h - 1 + over], fill=(206, 208, 216, 255),
                    outline=(60, 62, 70, 255), width=max(1, SS // 2))
        d.line([(x + SS // 2, o - over + SS // 2), (x + SS // 2, o + h - 1 + over - SS // 2)],
               fill=(250, 250, 255, 255), width=max(1, SS // 2))


def gauge_track():
    """Empty tube: dark olive-grey glass with a pewter rim and flat silver stop bars at the ends."""
    pad = 3
    w, h = GW * SS, GH * SS
    img = Image.new('RGBA', ((GW + 2 * pad) * SS, (GH + 2 * pad) * SS), (0, 0, 0, 0))
    o = pad * SS
    sh = Image.new('L', img.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle([o, o + SS, o + w, o + h + SS], radius=2 * SS, fill=190)
    img.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(SS * 1.5)))
    body = vgrad(w, h, [(0, (108, 108, 103, 235)), (0.35, (52, 52, 48, 235)), (1, (33, 33, 30, 235))])
    img.paste(body, (o, o), tube_mask(w, h))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([o, o, o + w - 1, o + h - 1], radius=min(h // 3, 2 * SS), outline=(40, 28, 17, 255), width=SS)
    stop_bars(d, o, w, h, pad)
    save('gauge_track', down(img))


def gauge_fill(name, stops):
    pad = 3
    inset = 1
    w, h = (GW - 2 * inset) * SS, (GH - 2 * inset) * SS
    img = Image.new('RGBA', ((GW + 2 * pad) * SS, (GH + 2 * pad) * SS), (0, 0, 0, 0))
    body = vgrad(w, h, stops)
    img.paste(body, ((pad + inset) * SS, (pad + inset) * SS), tube_mask(w, h))
    save(name, down(img))


def gauge_tip():
    """A bright vertical tick at the leading edge of a gauge's fill."""
    w, h = 8 * SS, (GH + 4) * SS
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g = Image.new('L', (w, h), 0)
    ImageDraw.Draw(g).rounded_rectangle([w * 0.38, h * 0.12, w * 0.62, h * 0.88], radius=SS, fill=255)
    g = g.filter(ImageFilter.GaussianBlur(SS))
    img.paste((255, 255, 255, 255), (0, 0), g)
    save('gauge_tip', down(img))


def gauge_swoosh():
    """Navy brush-stroke under the left end of a gauge, carrying the small label."""
    W, H = 64 * SS, 20 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    # a tapered stroke: thick at the left, thinning to a point at the right
    d.polygon([(0, H * 0.25), (W * 0.15, H * 0.05), (W, H * 0.62), (W * 0.15, H * 0.98), (0, H * 0.8)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(SS * 0.8))
    body = hgrad(W, H, [(0, (34, 52, 112, 235)), (0.6, (22, 34, 82, 210)), (1, (14, 20, 50, 0))])
    img.paste(body, (0, 0), m)
    # thin silver highlight along the top edge of the stroke
    ImageDraw.Draw(img).line([(W * 0.15, H * 0.08), (W * 0.95, H * 0.6)], fill=(200, 210, 235, 150), width=SS)
    save('gauge_swoosh', down(img))


# ---------------------------------------------------------------- action bar (reference §4)
SLOT = 52  # slot diameter, final pixels
WELL = SLOT - 8


def radial(size, inner, outer, center=(0.5, 0.42)):
    """Radial gradient disc (supersampled size), colours RGBA."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = img.load()
    cx, cy = size * center[0], size * center[1]
    r = size / 2
    for y in range(size):
        for x in range(size):
            d = min(1.0, math.hypot(x - cx, y - cy) / (r * 1.1))
            px[x, y] = tuple(int(inner[k] + (outer[k] - inner[k]) * d) for k in range(4))
    return img


def circle_mask(size, inset=0):
    m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).ellipse([inset, inset, size - 1 - inset, size - 1 - inset], fill=255)
    return m


def ring_image(colors, width=3, glow=None):
    """A ring the size of a slot (+4px pad): metallic vertical gradient between colors[0] (top) and colors[1]."""
    pad = 4
    S = (SLOT + 2 * pad) * SS
    o, D = pad * SS, SLOT * SS
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    if glow:
        g = Image.new('L', (S, S), 0)
        ImageDraw.Draw(g).ellipse([o - SS, o - SS, o + D + SS, o + D + SS], outline=255, width=5 * SS)
        img.paste(glow, (0, 0), g.filter(ImageFilter.GaussianBlur(SS * 2.5)))
    ring = vgrad(D, D, [(0, colors[0]), (1, colors[1])])
    ann = circle_mask(D)
    ImageDraw.Draw(ann).ellipse([width * SS, width * SS, D - 1 - width * SS, D - 1 - width * SS], fill=0)
    img.paste(ring, (o, o), ann)
    d = ImageDraw.Draw(img)
    d.ellipse([o, o, o + D - 1, o + D - 1], outline=(10, 10, 16, 255), width=SS)
    d.ellipse([o + width * SS, o + width * SS, o + D - 1 - width * SS, o + D - 1 - width * SS],
              outline=(16, 14, 20, 230), width=SS)
    return down(img)


def slot_rings():
    pad = 4
    S = (SLOT + 2 * pad) * SS
    o, D = pad * SS, SLOT * SS
    sh = Image.new('L', (S, S), 0)
    ImageDraw.Draw(sh).ellipse([o, o + 2 * SS, o + D, o + D + 2 * SS], fill=200)
    shadow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(SS * 2)))
    save('slot_shadow', down(shadow))
    save('slot_ring', ring_image([(236, 238, 246, 255), (112, 118, 136, 255)]))
    save('slot_ring_gold', ring_image([(255, 236, 160, 255), (176, 124, 40, 255)], glow=(255, 214, 110, 255)))
    save('slot_ring_white', ring_image([(255, 255, 255, 255), (176, 182, 198, 255)], glow=(235, 242, 255, 255)))
    save('slot_ring_blue', ring_image([(200, 236, 255, 255), (60, 120, 210, 255)], glow=(90, 170, 255, 255)))
    save('slot_ring_pink', ring_image([(255, 210, 240, 255), (200, 70, 160, 255)], glow=(255, 110, 210, 255)))


def slot_well():
    """Empty-slot interior: dark smoked glass."""
    D = WELL * SS
    img = radial(D, (46, 52, 70, 235), (8, 10, 18, 240))
    img = Image.composite(img, Image.new('RGBA', (D, D), (0, 0, 0, 0)), circle_mask(D))
    save('slot_well', down(img))


ELEMENTS = {  # glyph disc colours: (inner highlight, outer)
    'fire': ((255, 170, 110, 255), (150, 30, 20, 255)),
    'ice': ((210, 245, 255, 255), (40, 120, 170, 255)),
    'wind': ((200, 255, 170, 255), (40, 130, 50, 255)),
    'earth': ((250, 225, 140, 255), (130, 95, 30, 255)),
    'thunder': ((235, 190, 255, 255), (100, 40, 150, 255)),
    'water': ((160, 210, 255, 255), (25, 60, 160, 255)),
    'light': ((255, 255, 240, 255), (170, 160, 120, 255)),
    'dark': ((190, 150, 220, 255), (40, 20, 60, 255)),
    'ability': ((255, 235, 170, 255), (150, 105, 30, 255)),
    'weaponskill': ((255, 200, 150, 255), (140, 60, 25, 255)),
    'command': ((150, 170, 215, 255), (34, 44, 80, 255)),
}


def glyph_discs():
    D = WELL * SS
    for name, (inner, outer) in ELEMENTS.items():
        img = radial(D, inner, outer, center=(0.38, 0.3))
        img = vgloss(img, top=0.45, strength=70)
        img = Image.composite(img, Image.new('RGBA', (D, D), (0, 0, 0, 0)), circle_mask(D))
        save('disc_' + name, down(img))


def recast_sheet(frames=64, cols=8):
    """Recast overlay, frame i = i/frames of the recast elapsed: the icon is dimmed and a cyan arc around the edge
    shows the time remaining, sweeping clockwise from 12 o'clock."""
    D = WELL
    sheet = Image.new('RGBA', (D * cols, D * ((frames + cols - 1) // cols)), (0, 0, 0, 0))
    for i in range(frames):
        remain = 1 - i / frames
        big = Image.new('RGBA', (D * SS, D * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        d.ellipse([0, 0, D * SS - 1, D * SS - 1], fill=(0, 4, 12, 150))
        if remain > 0:
            d.arc([SS, SS, D * SS - 1 - SS, D * SS - 1 - SS], -90, -90 + 360 * remain, fill=(110, 230, 255, 255),
                  width=3 * SS)
        sheet.paste(down(big), ((i % cols) * D, (i // cols) * D))
    save('recast_sheet', sheet)


def motif(name, kind):
    """Small horizontal weapon motif under each icon: a silver sword with a gold crossguard (abilities,
    weapon skills) or a wand with a red gem (spells). It carries the cost and slot number."""
    W, H = 58 * SS, 12 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H / 2
    if kind == 'sword':
        d.polygon([(W * 0.22, cy - 2 * SS), (W * 0.96, cy), (W * 0.22, cy + 2 * SS)], fill=(220, 224, 236, 255),
                  outline=(60, 62, 76, 255))
        d.line([(W * 0.24, cy), (W * 0.9, cy)], fill=(140, 146, 166, 255), width=SS // 2 + 1)
        d.rounded_rectangle([W * 0.18, cy - 5 * SS, W * 0.22, cy + 5 * SS], radius=SS, fill=(222, 182, 90, 255),
                            outline=(110, 76, 24, 255))
        d.rounded_rectangle([W * 0.04, cy - 1.5 * SS, W * 0.18, cy + 1.5 * SS], radius=SS, fill=(120, 70, 40, 255))
        d.ellipse([0, cy - 2.5 * SS, 5 * SS, cy + 2.5 * SS], fill=(222, 182, 90, 255))
    else:
        d.rounded_rectangle([W * 0.04, cy - 1.5 * SS, W * 0.84, cy + 1.5 * SS], radius=SS,
                            fill=(150, 112, 70, 255), outline=(70, 46, 24, 255))
        d.ellipse([W * 0.82, cy - 4.5 * SS, W * 0.82 + 9 * SS, cy + 4.5 * SS], fill=(200, 30, 50, 255),
                  outline=(222, 182, 90, 255), width=SS)
        d.ellipse([W * 0.84, cy - 3 * SS, W * 0.84 + 3 * SS, cy], fill=(255, 170, 180, 220))
    save(name, down(img))


def bar_band(slots=10, step=56):
    """Navy-to-purple band behind the slots with a thin gold rail through the slot centres."""
    W, H = (slots * step + 40) * SS, 40 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, H * 0.18, W - 1, H * 0.82], radius=H // 3, fill=255)
    fade = hgrad(W, H, [(0, (0, 0, 0, 0)), (0.06, (0, 0, 0, 255)), (0.94, (0, 0, 0, 255)), (1, (0, 0, 0, 0))])
    m = Image.composite(m, Image.new('L', (W, H), 0), fade.split()[3])
    body = hgrad(W, H, [(0, (16, 24, 70, 200)), (0.5, (36, 26, 82, 200)), (1, (64, 26, 84, 200))])
    img.paste(body, (0, 0), m.filter(ImageFilter.GaussianBlur(SS)))
    d = ImageDraw.Draw(img)
    d.line([(W * 0.03, H / 2), (W * 0.97, H / 2)], fill=(214, 176, 92, 255), width=SS)
    d.line([(W * 0.03, H / 2 + SS), (W * 0.97, H / 2 + SS)], fill=(90, 62, 22, 200), width=SS // 2 + 1)
    save('bar_band', down(img))


CREST_FIELDS = {          # the shield's colour shows which layer of the bar is up
    'blue':  [(0, (128, 160, 232, 250)), (1, (36, 60, 150, 250))],     # nothing held
    'red':   [(0, (236, 120, 120, 250)), (1, (150, 30, 36, 250))],     # LT / Ctrl
    'green': [(0, (136, 214, 128, 250)), (1, (34, 116, 52, 250))],     # RT / Alt
}


def crest():
    """Left emblem: a gold-rimmed heraldic shield with a gold sword glyph (field blue / red / green for the bar's
    base / LT / RT layer), above a black hexagonal plate with a gold edge that holds the page number between
    up/down chevrons."""
    for name, field in CREST_FIELDS.items():
        crest_shield('crest_shield_' + name, field)
    crest_plate()


def crest_shield(out, field):
    W, H = 46 * SS, 50 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shape = [(W * 0.08, H * 0.05), (W * 0.92, H * 0.05), (W * 0.92, H * 0.5), (W * 0.5, H * 0.97),
             (W * 0.08, H * 0.5)]
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(shape, fill=255)
    body = vgloss(vgrad(W, H, field), top=0.4, strength=60)
    img.paste(body, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.polygon(shape, outline=(232, 196, 110, 255), width=2 * SS)
    # gold sword glyph
    cx = W / 2
    d.polygon([(cx, H * 0.14), (cx + 2.2 * SS, H * 0.62), (cx - 2.2 * SS, H * 0.62)], fill=(248, 214, 120, 255),
              outline=(120, 80, 24, 255))
    d.rounded_rectangle([cx - 8 * SS, H * 0.6, cx + 8 * SS, H * 0.6 + 2.5 * SS], radius=SS,
                        fill=(248, 214, 120, 255), outline=(120, 80, 24, 255))
    d.rounded_rectangle([cx - 1.6 * SS, H * 0.64, cx + 1.6 * SS, H * 0.78], radius=SS, fill=(120, 70, 40, 255))
    save(out, down(img))


def crest_plate():
    W, H = 40 * SS, 34 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hexa = [(W * 0.22, H * 0.18), (W * 0.78, H * 0.18), (W, H * 0.5), (W * 0.78, H * 0.82), (W * 0.22, H * 0.82),
            (0, H * 0.5)]
    d = ImageDraw.Draw(img)
    d.polygon(hexa, fill=(10, 10, 14, 240), outline=(222, 182, 90, 255), width=SS + SS // 2)
    for up, y in ((True, H * 0.02), (False, H * 0.98)):
        dy = 4 * SS if up else -4 * SS
        d.polygon([(W / 2 - 4 * SS, y + dy), (W / 2 + 4 * SS, y + dy), (W / 2, y)], fill=(222, 182, 90, 255))
    save('crest_plate', down(img))


def tooltip_panel():
    """Dark translucent pop-up help panel (9-slice source: 16 px corners)."""
    W, H = 64 * SS, 64 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([SS, SS, W - 1 - SS, H - 1 - SS], radius=7 * SS, fill=(10, 12, 20, 215),
                        outline=(150, 156, 176, 230), width=SS)
    save('tooltip_panel', down(img))


# ---------------------------------------------------------------- target frame (reference §9-11)
def long_tube(name, length, height, stops=None, track=False):
    """A long tube like the gauges, for the target and party frames. track=True draws the empty navy track."""
    pad = 3
    w, h = length * SS, height * SS
    img = Image.new('RGBA', ((length + 2 * pad) * SS, (height + 2 * pad) * SS), (0, 0, 0, 0))
    o = pad * SS
    if track:
        sh = Image.new('L', img.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle([o, o + SS, o + w, o + h + SS], radius=2 * SS, fill=190)
        img.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(SS * 1.5)))
        body = vgrad(w, h, [(0, (70, 80, 112, 235)), (0.35, (37, 47, 76, 235)), (1, (20, 26, 44, 235))])
        img.paste(body, (o, o), tube_mask(w, h))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([o, o, o + w - 1, o + h - 1], radius=min(h // 3, 2 * SS), outline=(30, 22, 16, 255), width=SS)
        stop_bars(d, o, w, h, pad)
    else:
        inset = SS
        body = vgrad(w - 2 * inset, h - 2 * inset, stops)
        img.paste(body, (o + inset, o + inset), tube_mask(w - 2 * inset, h - 2 * inset))
    save(name, down(img))


ENEMY_HP = [(0, (255, 236, 238, 255)), (0.3, (252, 199, 203, 255)), (0.62, (226, 120, 128, 255)),
            (0.85, (190, 60, 72, 255)), (1, (120, 40, 48, 255))]
# HP / MP / TP fills: top highlight -> body -> shade. Started from 1.0 screenshots (reference section 8), then
# deepened: the sampled pastels read as washed out on a TV.
HP_STOPS = [(0, (255, 214, 212, 255)), (0.3, (240, 150, 148, 255)), (0.65, (214, 86, 86, 255)),
            (0.9, (182, 60, 60, 255)), (1, (112, 38, 36, 255))]
MP_STOPS = [(0, (250, 248, 198, 255)), (0.3, (232, 228, 128, 255)), (0.65, (206, 208, 74, 255)),
            (1, (126, 136, 36, 255))]
TP_STOPS = [(0, (214, 248, 255, 255)), (0.35, (98, 208, 232, 255)), (0.8, (38, 158, 200, 255)),
            (1, (18, 98, 130, 255))]


def enmity_pills():
    """Small horizontal capsule left of the enemy HP bar: green / orange / red (reference §10)."""
    for name, col in (('green', (90, 220, 90)), ('orange', (255, 160, 50)), ('red', (255, 78, 76))):
        W, H = 34 * SS, 11 * SS
        img = Image.new('RGBA', (W + 4 * SS, H + 4 * SS), (0, 0, 0, 0))
        g = Image.new('L', img.size, 0)
        ImageDraw.Draw(g).rounded_rectangle([SS, SS, W + 3 * SS, H + 3 * SS], radius=H // 2 + SS, fill=255)
        img.paste(col + (255,), (0, 0), g.filter(ImageFilter.GaussianBlur(SS * 1.5)))
        body = vgloss(vgrad(W, H, [(0, tuple(min(255, c + 90) for c in col) + (255,)), (0.5, col + (255,)),
                                   (1, tuple(int(c * 0.55) for c in col) + (255,))]), top=0.45, strength=90)
        img.paste(body, (2 * SS, 2 * SS), capsule_mask(W, H))
        ImageDraw.Draw(img).rounded_rectangle([2 * SS, 2 * SS, W + 2 * SS - 1, H + 2 * SS - 1], radius=H // 2,
                                              outline=(20, 12, 10, 255), width=SS)
        save('enmity_' + name, down(img))


def aggression_orbs():
    """Green glossy sphere = passive; red spiky burst = aggressive (reference §9)."""
    D = 26 * SS
    img = radial(D, (200, 255, 190, 255), (30, 120, 40, 255), center=(0.36, 0.3))
    img = Image.composite(img, Image.new('RGBA', (D, D), (0, 0, 0, 0)), circle_mask(D, SS))
    ImageDraw.Draw(img).ellipse([SS, SS, D - 1 - SS, D - 1 - SS], outline=(10, 30, 10, 255), width=SS)
    save('aggro_passive', down(img))

    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    pts = []
    for k in range(20):
        r = D * (0.49 if k % 2 == 0 else 0.3)
        a = math.pi * 2 * k / 20 - math.pi / 2
        pts.append((D / 2 + r * math.cos(a), D / 2 + r * math.sin(a)))
    m = Image.new('L', (D, D), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    burst = radial(D, (255, 220, 160, 255), (180, 20, 20, 255), center=(0.45, 0.4))
    img.paste(burst, (0, 0), m)
    ImageDraw.Draw(img).polygon(pts, outline=(60, 8, 8, 255), width=SS)
    save('aggro_active', down(img))


def name_rule(length=300):
    """Thin rule under the target name, ending in a small curl at the left (reference §2 section headers)."""
    W, H = length * SS, 10 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(10 * SS, H / 2), (W, H / 2)], fill=(214, 186, 120, 230), width=SS)
    d.arc([2 * SS, H / 2 - 4 * SS, 12 * SS, H / 2 + 4 * SS], 90, 360, fill=(214, 186, 120, 230), width=SS)
    fade = hgrad(W, H, [(0, (0, 0, 0, 255)), (0.75, (0, 0, 0, 255)), (1, (0, 0, 0, 0))]).split()[3]
    img.putalpha(Image.composite(img.split()[3], Image.new('L', (W, H), 0), fade))
    save('name_rule', down(img))


def lock_mark():
    """Three small gold spearhead shards pointing inward (locked-on cursor, reference §11), drawn small by the
    target name."""
    D = 26 * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = D / 2
    for k in range(3):
        a = math.pi * 2 * k / 3 - math.pi / 2
        tip = (c + math.cos(a) * D * 0.14, c + math.sin(a) * D * 0.14)
        base = (c + math.cos(a) * D * 0.48, c + math.sin(a) * D * 0.48)
        px, py = -math.sin(a) * D * 0.09, math.cos(a) * D * 0.09
        d.polygon([tip, (base[0] + px, base[1] + py), (base[0] - px, base[1] - py)], fill=(250, 214, 120, 255),
                  outline=(110, 70, 20, 255))
    save('lock_mark', down(img))


def diamond(name, col, size=12):
    D = size * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon([(D / 2, 0), (D, D / 2), (D / 2, D), (0, D / 2)], fill=col,
                                outline=(60, 40, 10, 255))
    save(name, down(img))


# ---------------------------------------------------------------- cast bar & EXP bar (reference §8)
CAST_STOPS = [(0, (226, 236, 255, 255)), (0.3, (150, 176, 222, 255)), (0.7, (78, 108, 168, 255)),
              (1, (40, 58, 104, 255))]
# deepened like the HP/MP/TP fills, and kept a royal blue so it doesn't read as TP's cyan
EXP_STOPS = [(0, (206, 232, 255, 255)), (0.35, (96, 170, 240, 255)), (0.75, (46, 112, 206, 255)),
             (1, (24, 64, 140, 255))]


def job_tile():
    """Square class tile for the EXP bar: deep red field, gold rim, soft gloss."""
    D = 30 * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    body = vgloss(vgrad(D, D, [(0, (176, 50, 60, 250)), (1, (90, 16, 28, 250))]), top=0.45, strength=70)
    m = Image.new('L', (D, D), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, D - 1, D - 1], radius=4 * SS, fill=255)
    img.paste(body, (0, 0), m)
    ImageDraw.Draw(img).rounded_rectangle([SS, SS, D - 1 - SS, D - 1 - SS], radius=4 * SS,
                                          outline=(232, 196, 110, 255), width=SS + SS // 2)
    save('job_tile', down(img))


# ---------------------------------------------------------------- chat log (reference §16)
def log_tabs():
    """Trapezoidal dark tab at the top-left of a log window; the active one is brighter."""
    for name, top, bottom, rim in (('log_tab', (52, 56, 70, 220), (20, 22, 30, 220), (150, 156, 176, 200)),
                                   ('log_tab_active', (96, 104, 136, 235), (40, 44, 64, 235), (214, 218, 236, 255))):
        W, H = 96 * SS, 22 * SS
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        shape = [(8 * SS, 0), (W - 8 * SS, 0), (W - 1, H - 1), (0, H - 1)]
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).polygon(shape, fill=255)
        img.paste(vgrad(W, H, [(0, top), (1, bottom)]), (0, 0), m)
        ImageDraw.Draw(img).line(shape[:3], fill=rim, width=SS)
        ImageDraw.Draw(img).line([shape[0], shape[3]], fill=rim, width=SS)
        save(name, down(img))


def log_wash():
    """Battle-text wash: dark grey, translucent, solid on the left and fading out to the right; soft top/bottom.
    Stretched to size at runtime."""
    W, H = 256, 64
    img = Image.new('RGBA', (W, H), (16, 16, 20, 0))
    px = img.load()
    for x in range(W):
        t = x / (W - 1)
        a = 215 if t < 0.35 else 215 * max(0.0, 1 - (t - 0.35) / 0.65) ** 1.3
        for y in range(H):
            e = min(y, H - 1 - y) / 8
            px[x, y] = (16, 16, 20, int(a * min(1, e)))
    save('log_wash', img)


def lobby_glow():
    """A soft round shadow (dark at the centre, fading to nothing at the edges), stretched behind the lobby's title
    so it reads over any sky."""
    W, H = 256, 128
    img = Image.new('RGBA', (W, H), (8, 8, 12, 0))
    px = img.load()
    for y in range(H):
        for x in range(W):
            dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
            d = min(1.0, (dx * dx + dy * dy) ** 0.5)
            a = 200 * (1 - d) ** 1.6
            px[x, y] = (8, 8, 12, int(a))
    save('lobby_glow', img)


def log_panel():
    """Semi-transparent near-black log body with a 1 px light rim (stretched to size at runtime)."""
    W, H = 64 * SS, 64 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([0, 0, W - 1, H - 1], fill=(6, 8, 14, 165), outline=(140, 146, 166, 170), width=SS)
    save('log_panel', down(img))


# ---------------------------------------------------------------- windows (reference §2): nine-slice sources
def win_body():
    """Menu window body: deep navy, lighter at the top, faint brushed noise, 1-2 px steel-blue border with an inner
    periwinkle bevel, ~8 px corners. 64x64 nine-slice source with 12 px corners."""
    import random
    random.seed(7)
    W = H = 64 * SS
    body = vgrad(W, H, [(0, (34, 56, 108, 238)), (1, (12, 24, 56, 238))])
    px = body.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            n = random.randint(-6, 6)
            r, g, b, a = px[x, y]
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * SS, fill=255)
    img.paste(body, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * SS, outline=(196, 206, 230, 255), width=SS + SS // 2)
    d.rounded_rectangle([2 * SS, 2 * SS, W - 1 - 2 * SS, H - 1 - 2 * SS], radius=6 * SS, outline=(90, 106, 208, 180),
                        width=SS)
    save('win_body', down(img))


def win_hud():
    """HUD panel: near-black, semi-transparent, thin pewter rim (main-menu slide-out, retainer list...)."""
    W = H = 64 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=6 * SS, fill=255)
    img.paste(vgrad(W, H, [(0, (26, 22, 20, 215)), (1, (8, 6, 6, 215))]), (0, 0), m)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=6 * SS, outline=(150, 146, 140, 220),
                                          width=SS)
    save('win_hud', down(img))


def win_title():
    """Dark title strip that sits on top of a window body."""
    W, H = 64 * SS, 30 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=7 * SS, fill=255)
    img.paste(vgrad(W, H, [(0, (40, 44, 60, 245)), (1, (10, 12, 22, 245))]), (0, 0), m)
    ImageDraw.Draw(img).line([(6 * SS, H - SS), (W - 6 * SS, H - SS)], fill=(150, 160, 190, 200), width=SS)
    save('win_title', down(img))


def title_swash():
    """Curled scroll ornament at the left of a window title."""
    W, H = 46 * SS, 30 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gold = (226, 196, 124, 255)
    d.arc([2 * SS, 4 * SS, 22 * SS, 26 * SS], 60, 330, fill=gold, width=2 * SS)
    d.arc([8 * SS, 10 * SS, 18 * SS, 20 * SS], 200, 470, fill=gold, width=SS + SS // 2)
    d.line([(16 * SS, 25 * SS), (W - 2 * SS, 25 * SS)], fill=gold, width=SS + SS // 2)
    d.polygon([(W - 2 * SS, 22 * SS), (W, 25 * SS), (W - 2 * SS, 28 * SS)], fill=gold)
    save('title_swash', down(img))


# ---------------------------------------------------------------- NPC dialogue (1.0 talk window)
def dlg_box():
    """Talk window body: translucent near-black with feathered edges (no rim). 128x128 nine-slice source whose
    32 px corners hold the whole soft edge."""
    W = H = 128 * SS
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([16 * SS, 16 * SS, W - 16 * SS, H - 16 * SS], radius=10 * SS, fill=205)
    m = m.filter(ImageFilter.GaussianBlur(7 * SS))
    img = Image.new('RGBA', (W, H), (14, 14, 16, 0))
    img.putalpha(m)
    save('dlg_box', down(img))


def dlg_name():
    """Speaker name plate: a flat grey tab, darker at the bottom, with a 1 px light top edge and a curled hook at
    its left end (stretched horizontally at runtime; 14 px ends)."""
    W, H = 96 * SS, 22 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([(10 * SS, 0), (W - 2 * SS, 0), (W - 2 * SS, H - 1), (6 * SS, H - 1)], fill=255)
    img.paste(vgrad(W, H, [(0, (128, 128, 132, 235)), (1, (74, 74, 80, 235))]), (0, 0), m)
    d = ImageDraw.Draw(img)
    d.line([(10 * SS, SS // 2), (W - 2 * SS, SS // 2)], fill=(196, 196, 200, 255), width=SS)
    d.line([(W - 2 * SS, 0), (W - 2 * SS, H - 1)], fill=(40, 40, 44, 255), width=SS)
    # hook: a dark curl at the left
    d.arc([0, 2 * SS, 14 * SS, 26 * SS], 160, 300, fill=(30, 30, 34, 255), width=2 * SS)
    d.arc([3 * SS, 4 * SS, 11 * SS, 12 * SS], 180, 420, fill=(30, 30, 34, 255), width=SS + SS // 2)
    save('dlg_name', down(img))


def dlg_arrow():
    """Gold down-pointing chevron: the 'more text' prompt."""
    W, H = 14 * SS, 12 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon([(SS, SS), (W // 2, 4 * SS), (W - SS, SS), (W // 2, H - SS)], fill=255)
    img.paste(vgrad(W, H, [(0, (255, 238, 170, 255)), (1, (214, 150, 40, 255))]), (0, 0), m)
    glow = m.filter(ImageFilter.GaussianBlur(SS))
    out = Image.new('RGBA', (W, H), (255, 220, 120, 0))
    out.putalpha(glow.point(lambda v: v // 2))
    out.alpha_composite(img)
    save('dlg_arrow', down(out))


# ---------------------------------------------------------------- command menu (FF-style slanted stack)
CMD_W, CMD_H, CMD_SLANT = 300, 46, 15


def cmd_panel(name, top, bottom, rim, rim_w):
    """A slanted command panel (parallelogram) with a soft gloss and a rim; the text sits on it at runtime."""
    pad = 4
    W, H = (CMD_W + CMD_SLANT + 2 * pad) * SS, (CMD_H + 2 * pad) * SS
    o = pad * SS
    pts = [(o + CMD_SLANT * SS, o), (o + (CMD_W + CMD_SLANT) * SS, o), (o + CMD_W * SS, o + CMD_H * SS),
           (o, o + CMD_H * SS)]
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).polygon([(x + SS, y + 2 * SS) for x, y in pts], fill=170)
    img.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(2 * SS)))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    img.paste(vgloss(vgrad(W, H, [(0, top), (1, bottom)]), top=0.45, strength=40), (0, 0), m)
    d = ImageDraw.Draw(img)
    d.line(pts + [pts[0]], fill=rim, width=rim_w * SS)
    save(name, down(img))


def crystal_shard():
    """A pale blue crystal shard (elongated diamond with a facet line): the marker beside the selected command."""
    W, H = 28 * SS, 46 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pts = [(W / 2, SS), (W - 2 * SS, H * 0.42), (W / 2, H - SS), (2 * SS, H * 0.42)]
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).polygon(pts, fill=200)
    img.paste((150, 210, 255, 255), (0, 0), glow.filter(ImageFilter.GaussianBlur(3 * SS)))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    img.paste(vgrad(W, H, [(0, (235, 248, 255, 255)), (0.5, (140, 200, 255, 255)), (1, (70, 120, 220, 255))]), (0, 0), m)
    d = ImageDraw.Draw(img)
    d.line(pts + [pts[0]], fill=(245, 252, 255, 255), width=SS)
    d.line([(W / 2, SS), (W / 2, H - SS)], fill=(255, 255, 255, 160), width=SS)
    save('crystal_shard', down(img))


def row_sel():
    """Selected list row: lighter blue fill with a bright 1 px outline (nine-slice, 6 px corners)."""
    W, H = 32 * SS, 24 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * SS, fill=(59, 90, 168, 200),
                                          outline=(200, 220, 255, 255), width=SS)
    save('row_sel', down(img))



# ---------------------------------------------------------------- black-and-gold theme (draw.lua swaps these in)
GOLD_RIM, GOLD_DIM = (196, 164, 98, 255), (110, 90, 52, 170)


def win_body_gold():
    """Menu window body, black-and-gold theme: warm near-black, faint brushed noise, thin antique-gold rim with a
    dim inner bevel. Same shape as win_body."""
    import random
    random.seed(7)
    W = H = 64 * SS
    body = vgrad(W, H, [(0, (30, 26, 22, 236)), (1, (8, 7, 6, 236))])
    px = body.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            n = random.randint(-4, 4)
            r, g, b, a = px[x, y]
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * SS, fill=255)
    img.paste(body, (0, 0), m)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=8 * SS, outline=GOLD_RIM, width=SS)
    d.rounded_rectangle([2 * SS, 2 * SS, W - 1 - 2 * SS, H - 1 - 2 * SS], radius=6 * SS, outline=GOLD_DIM, width=SS)
    save('win_body_gold', down(img))


def win_title_gold():
    """Title strip, black-and-gold theme: darker band with a gold underline."""
    W, H = 64 * SS, 30 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=7 * SS, fill=255)
    img.paste(vgrad(W, H, [(0, (44, 38, 30, 245)), (1, (12, 10, 8, 245))]), (0, 0), m)
    ImageDraw.Draw(img).line([(6 * SS, H - SS), (W - 6 * SS, H - SS)], fill=(206, 172, 104, 220), width=SS)
    save('win_title_gold', down(img))


def row_sel_gold():
    """Selected list row, black-and-gold theme: a warm amber wash with a gold outline."""
    W, H = 32 * SS, 24 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * SS, fill=255)
    img.paste(hgrad(W, H, [(0, (150, 112, 44, 190)), (1, (70, 52, 22, 120))]), (0, 0), m)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=4 * SS, outline=(240, 208, 128, 255), width=SS)
    save('row_sel_gold', down(img))


def btn_pill_gold():
    """Pill buttons, black-and-gold theme."""
    for name, top, bottom in (('btn_pill_gold', (74, 62, 42, 250), (22, 18, 12, 250)),
                              ('btn_pill_focus_gold', (176, 138, 62, 255), (82, 60, 24, 255))):
        W, H = 64 * SS, 26 * SS
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        m = capsule_mask(W, H)
        img.paste(vgloss(vgrad(W, H, [(0, top), (1, bottom)]), top=0.45, strength=70), (0, 0), m)
        ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=H // 2, outline=(232, 204, 140, 255),
                                              width=SS)
        save(name, down(img))


def cursor_gold():
    """Gold ornate pointer (a spear-tip with small wings) that sits left of the focused item."""
    W, H = 28 * SS, 20 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H / 2
    gold, dark = (250, 214, 120, 255), (110, 70, 20, 255)
    d.polygon([(W - 1, cy), (W * 0.5, cy - 6 * SS), (W * 0.58, cy), (W * 0.5, cy + 6 * SS)], fill=gold, outline=dark)
    d.polygon([(W * 0.5, cy - 2 * SS), (W * 0.12, cy - 8 * SS), (W * 0.28, cy), (W * 0.12, cy + 8 * SS),
               (W * 0.5, cy + 2 * SS)], fill=(236, 186, 90, 255), outline=dark)
    d.ellipse([0, cy - 2.5 * SS, 5 * SS, cy + 2.5 * SS], fill=gold, outline=dark)
    save('cursor_gold', down(img))


def btn_pill():
    """Royal-blue pill button with a glossy top (nine-slice, 12 px caps); and a brighter focused version."""
    for name, top, bottom in (('btn_pill', (70, 110, 210, 250), (24, 44, 120, 250)),
                              ('btn_pill_focus', (110, 170, 255, 255), (40, 90, 190, 255))):
        W, H = 64 * SS, 26 * SS
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        m = capsule_mask(W, H)
        img.paste(vgloss(vgrad(W, H, [(0, top), (1, bottom)]), top=0.45, strength=90), (0, 0), m)
        ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=H // 2, outline=(214, 226, 255, 255),
                                              width=SS)
        save(name, down(img))


def slot_square():
    """Rounded navy square tile for grids (inventory, macro icons)."""
    W = H = 40 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=6 * SS, fill=(18, 30, 64, 230),
                                          outline=(110, 130, 190, 230), width=SS)
    save('slot_square', down(img))


# ---------------------------------------------------------------- micro menu roundels (reference §19)
def roundel(name, inner, outer, glyph, socket=False):
    """Small round icon: painted disc (or a dark grey socket) with a silver rim and a simple white glyph."""
    D = 30 * SS
    img = Image.new('RGBA', (D + 4 * SS, D + 4 * SS), (0, 0, 0, 0))
    o = 2 * SS
    sh = Image.new('L', img.size, 0)
    ImageDraw.Draw(sh).ellipse([o, o + SS, o + D, o + D + SS], fill=180)
    img.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(SS * 1.5)))
    if socket:
        disc = radial(D, (70, 72, 80, 255), (24, 25, 30, 255))
    else:
        disc = vgloss(radial(D, inner, outer, center=(0.38, 0.3)), top=0.45, strength=70)
    img.paste(disc, (o, o), circle_mask(D))
    d = ImageDraw.Draw(img)
    d.ellipse([o, o, o + D - 1, o + D - 1], outline=(214, 216, 226, 255), width=SS + SS // 2)
    g = ImageDraw.Draw(img)
    c = o + D / 2
    W = (250, 248, 240, 255)
    k = SS
    if glyph == 'scroll':
        g.rounded_rectangle([c - 8 * k, c - 9 * k, c + 8 * k, c + 9 * k], radius=2 * k, outline=W, width=2 * k)
        for yy in (-4, 0, 4):
            g.line([(c - 5 * k, c + yy * k), (c + 5 * k, c + yy * k)], fill=W, width=k + k // 2)
    elif glyph == 'sword':
        g.polygon([(c + 8 * k, c - 8 * k), (c + 9 * k, c - 9 * k), (c - 4 * k, c + 4 * k), (c - 5 * k, c + 3 * k)], fill=W)
        g.line([(c - 7 * k, c + 1 * k), (c - 1 * k, c + 7 * k)], fill=W, width=2 * k)
        g.line([(c - 4 * k, c + 4 * k), (c - 8 * k, c + 8 * k)], fill=W, width=2 * k)
    elif glyph == 'bag':
        g.ellipse([c - 9 * k, c - 3 * k, c + 9 * k, c + 10 * k], fill=W)                     # sack body
        g.polygon([(c - 4 * k, c - 2 * k), (c - 6 * k, c - 9 * k), (c + 6 * k, c - 9 * k), (c + 4 * k, c - 2 * k)], fill=W)
        g.line([(c - 5 * k, c - 3 * k), (c + 5 * k, c - 3 * k)], fill=outer, width=2 * k)     # tie
    elif glyph == 'bubble':
        g.ellipse([c - 9 * k, c - 8 * k, c + 9 * k, c + 5 * k], fill=W)
        g.polygon([(c - 5 * k, c + 2 * k), (c - 8 * k, c + 9 * k), (c, c + 3 * k)], fill=W)
    elif glyph == 'lock':
        g.rounded_rectangle([c - 7 * k, c - 2 * k, c + 7 * k, c + 9 * k], radius=2 * k, fill=W)
        g.arc([c - 5 * k, c - 10 * k, c + 5 * k, c + 2 * k], 180, 360, fill=W, width=2 * k)
    elif glyph == 'help':
        g.arc([c - 6 * k, c - 10 * k, c + 6 * k, c + 2 * k], 200, 420, fill=W, width=3 * k)
        g.line([(c, c + 1 * k), (c, c + 4 * k)], fill=W, width=3 * k)
        g.ellipse([c - 2 * k, c + 6 * k, c + 2 * k, c + 10 * k], fill=W)
    elif glyph == 'eye':
        g.ellipse([c - 9 * k, c - 5 * k, c + 9 * k, c + 5 * k], outline=W, width=2 * k)
        g.ellipse([c - 3 * k, c - 3 * k, c + 3 * k, c + 3 * k], fill=W)
    elif glyph == 'trade':
        g.line([(c - 8 * k, c - 3 * k), (c + 7 * k, c - 3 * k)], fill=W, width=2 * k)
        g.polygon([(c + 9 * k, c - 3 * k), (c + 4 * k, c - 7 * k), (c + 4 * k, c + 1 * k)], fill=W)
        g.line([(c + 8 * k, c + 4 * k), (c - 7 * k, c + 4 * k)], fill=W, width=2 * k)
        g.polygon([(c - 9 * k, c + 4 * k), (c - 4 * k, c), (c - 4 * k, c + 8 * k)], fill=W)
    elif glyph == 'invite':
        g.ellipse([c - 7 * k, c - 9 * k, c + 1 * k, c - 1 * k], fill=W)
        g.pieslice([c - 11 * k, c, c + 5 * k, c + 16 * k], 180, 360, fill=W)
        g.line([(c + 6 * k, c - 6 * k), (c + 6 * k, c + 2 * k)], fill=W, width=2 * k)
        g.line([(c + 2 * k, c - 2 * k), (c + 10 * k, c - 2 * k)], fill=W, width=2 * k)
    elif glyph == 'chest':
        g.rounded_rectangle([c - 9 * k, c - 1 * k, c + 9 * k, c + 8 * k], radius=k, fill=W)   # box
        g.rounded_rectangle([c - 9 * k, c - 7 * k, c + 9 * k, c - 2 * k], radius=3 * k, fill=W) # lid
        g.line([(c - 9 * k, c - 1 * k), (c + 9 * k, c - 1 * k)], fill=outer, width=k + k // 2)
        g.rectangle([c - 2 * k, c - 3 * k, c + 2 * k, c + 2 * k], fill=outer)
    save('micro_' + name, down(img))


MICRO = [
    ('menu', (255, 236, 170, 255), (150, 105, 30, 255), 'scroll'),
    ('battle', (255, 190, 170, 255), (150, 30, 30, 255), 'sword'),
    ('item', (230, 210, 170, 255), (110, 70, 40, 255), 'bag'),
    ('emote', (190, 230, 255, 255), (40, 90, 160, 255), 'bubble'),
    ('lock', (255, 236, 170, 255), (60, 90, 170, 255), 'lock'),
    ('help', (220, 222, 230, 255), (90, 92, 104, 255), 'help'),
    ('check', (210, 240, 255, 255), (40, 110, 150, 255), 'eye'),
    ('trade', (230, 255, 200, 255), (50, 120, 60, 255), 'trade'),
    ('invite', (190, 220, 255, 255), (40, 70, 160, 255), 'invite'),
    ('loot', (255, 230, 160, 255), (140, 90, 20, 255), 'chest'),
]


# ---------------------------------------------------------------- minimap & clock (reference §26)
def minimap_disc(size=180):
    """Parchment/sepia disc that fades out in a soft radial vignette (no hard frame), with faint hatching."""
    import random
    random.seed(11)
    D = size * SS
    img = radial(D, (226, 204, 160, 255), (176, 146, 100, 255), center=(0.5, 0.5))
    d = ImageDraw.Draw(img)
    for _ in range(140):   # cross-hatched strokes, like the hand-drawn map art
        x, y = random.uniform(0, D), random.uniform(0, D)
        L = random.uniform(4, 10) * SS
        d.line([(x, y), (x + L, y + L * 0.6)], fill=(120, 90, 56, 70), width=SS)
    for r in (0.33, 0.66):  # range rings
        d.ellipse([D * (0.5 - r / 2), D * (0.5 - r / 2), D * (0.5 + r / 2), D * (0.5 + r / 2)],
                  outline=(150, 112, 60, 110), width=SS)
    d.line([(D / 2, D * 0.04), (D / 2, D * 0.96)], fill=(150, 112, 60, 80), width=SS)
    d.line([(D * 0.04, D / 2), (D * 0.96, D / 2)], fill=(150, 112, 60, 80), width=SS)
    a = Image.new('L', (D, D), 0)
    px = a.load()
    for y in range(0, D):
        for x in range(0, D):
            r = math.hypot(x - D / 2, y - D / 2) / (D / 2)
            px[x, y] = int(255 * max(0.0, min(1.0, (1.0 - r) / 0.28))) if r < 1 else 0
    img.putalpha(Image.composite(img.split()[3], Image.new('L', (D, D), 0), a))
    img.putalpha(Image.eval(img.split()[3], lambda v: int(v * 0.92)))
    save('minimap_disc', down(img))


def minimap_rim(size=180):
    """Soft sepia ring laid over the edge of an area map in the minimap disc (the map itself is cut to a circle)."""
    D = size * SS
    img = Image.new('RGBA', (D, D), (84, 58, 30, 0))
    a = Image.new('L', (D, D), 0)
    px = a.load()
    edge = (size / 2 - 8) / (size / 2)
    for y in range(D):
        for x in range(D):
            r = math.hypot(x - D / 2, y - D / 2) / (D / 2)
            if r < edge:
                v = max(0.0, 1 - (edge - r) / 0.14) ** 2 * 235
            else:
                v = max(0.0, 1 - (r - edge) / (1 - edge)) * 235
            px[x, y] = int(v)
    img.putalpha(a)
    save('minimap_rim', down(img))


def fov_wedge(name, col, size=180, angle=70):
    """Translucent wedge pointing up from the centre (rotated at runtime)."""
    D = size * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    m = Image.new('L', (D, D), 0)
    ImageDraw.Draw(m).pieslice([D * 0.1, D * 0.1, D * 0.9, D * 0.9], -90 - angle / 2, -90 + angle / 2, fill=150)
    g = Image.new('L', (D, D), 0)
    px = g.load()
    for y in range(D):
        for x in range(D):
            r = math.hypot(x - D / 2, y - D / 2) / (D * 0.4)
            px[x, y] = int(255 * max(0, 1 - r))
    m = Image.composite(m, Image.new('L', (D, D), 0), g)
    img.paste(col, (0, 0), m.filter(ImageFilter.GaussianBlur(SS * 2)))
    save(name, down(img))



def death_vignette():
    """Knocked-out screen: dark edges with a deep crimson cast, clear-ish centre. Stretched to the screen at runtime."""
    W, H = 256, 144
    img = Image.new('RGBA', (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
            r = math.hypot(dx, dy * 0.9) / 1.27
            a = 70 + 175 * min(1.0, max(0.0, (r - 0.25) / 0.75)) ** 1.6
            k = min(1.0, r)
            px[x, y] = (int(28 + 30 * k), int(6 + 4 * (1 - k)), int(10 + 6 * (1 - k)), int(a))
    save('death_vignette', img)


def death_band():
    """Knocked-out screen: a dark band across the screen, solid in the middle and fading out to both ends and soft at
    top and bottom, with a thin crimson-gold line along each edge. Stretched to width at runtime."""
    W, H = 512, 160
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    for x in range(W):
        t = abs(x - W / 2) / (W / 2)
        ax = max(0.0, 1 - max(0.0, t - 0.35) / 0.65) ** 1.4
        for y in range(H):
            e = min(1.0, min(y, H - 1 - y) / 26)
            a = 205 * ax * e
            if y in (3, 4) or y in (H - 5, H - 4):
                px[x, y] = (196, 150, 96, int(200 * ax))
            else:
                px[x, y] = (10, 8, 12, int(a))
    save('death_band', img)



def hair_line():
    """A thin white line with soft ends and a faint glow, tinted and stretched at runtime (progress lines)."""
    W, H = 256 * SS, 8 * SS
    img = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    a = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(a)
    d.rounded_rectangle((2 * SS, 3 * SS, W - 2 * SS, 5 * SS), radius=SS, fill=255)
    glow = a.filter(ImageFilter.GaussianBlur(2 * SS)).point(lambda v: int(v * 0.6))
    a = Image.composite(a, glow, a)
    img.putalpha(a)
    save('hair_line', down(img))


def wide_button():
    """A dark translucent rounded button with a warm gold rim (stretched horizontally at runtime: keep it wide)."""
    W, H = 320 * SS, 44 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = H // 2
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=r, fill=(200, 160, 100, 235))
    d.rounded_rectangle((2 * SS, 2 * SS, W - 1 - 2 * SS, H - 1 - 2 * SS), radius=r - 2 * SS, fill=(18, 14, 20, 225))
    hl = vgrad(W - 8 * SS, H // 2 - 4 * SS, [(0, (255, 255, 255, 34)), (1, (255, 255, 255, 0))])
    mask = Image.new('L', hl.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, hl.width - 1, hl.height * 2), radius=r - 4 * SS, fill=255)
    img.paste(hl, (4 * SS, 4 * SS), Image.composite(hl, Image.new('RGBA', hl.size), mask))
    save('wide_button', down(img))


def button_glow():
    """A soft warm halo the size of wide_button plus a margin, laid behind the selected button."""
    M = 18
    W, H = (320 + 2 * M) * SS, (44 + 2 * M) * SS
    a = Image.new('L', (W, H), 0)
    ImageDraw.Draw(a).rounded_rectangle((M * SS, M * SS, W - M * SS, H - M * SS), radius=22 * SS, fill=255)
    a = a.filter(ImageFilter.GaussianBlur(7 * SS))
    img = Image.new('RGBA', (W, H), (255, 196, 120, 0))
    img.putalpha(a)
    save('button_glow', down(img))



def white():
    """An 8x8 white square: tinted and stretched at runtime for solid fills (letterbox bars)."""
    save('white', Image.new('RGBA', (8, 8), (255, 255, 255, 255)))


def map_arrow():
    """Small gold triangle arrow for the player, pointing up."""
    W, H = 16 * SS, 18 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon([(W / 2, 0), (W - 1, H - 1), (W / 2, H * 0.72), (0, H - 1)], fill=(255, 214, 90, 255),
                                outline=(90, 56, 10, 255))
    save('map_arrow', down(img))


def map_dot():
    D = 8 * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([SS, SS, D - 1 - SS, D - 1 - SS], fill=(255, 255, 255, 255), outline=(30, 20, 10, 255),
                                width=SS)
    save('map_dot', down(img))


def map_ntab():
    W, H = 18 * SS, 16 * SS
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, W - 1, H - 1], radius=3 * SS, fill=(232, 130, 40, 245),
                                          outline=(90, 40, 10, 255), width=SS)
    save('map_ntab', down(img))


def clock_orbs():
    """Day and moon orbs for the clock cluster: element-tinted day orb, pale-blue moon."""
    D = 18 * SS
    for name, inner, outer in (('orb_moon', (240, 248, 255, 255), (120, 150, 200, 255)),
                               ('orb_day', (255, 255, 255, 255), (150, 150, 150, 255))):
        img = vgloss(radial(D, inner, outer, center=(0.36, 0.3)), top=0.45, strength=60)
        img = Image.composite(img, Image.new('RGBA', (D, D), (0, 0, 0, 0)), circle_mask(D))
        ImageDraw.Draw(img).ellipse([0, 0, D - 1, D - 1], outline=(30, 30, 40, 255), width=SS)
        save(name, down(img))


# ---------------------------------------------------------------- world target cursor (reference §11)
def target_ring():
    """Gold broken ring of two curved strokes drawn over the target, with a small sword-swoosh at the lower right."""
    D = 72 * SS
    img = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    glow = Image.new('L', (D, D), 0)
    gd = ImageDraw.Draw(glow)
    for a0, a1 in ((200, 330), (20, 150)):
        gd.arc([6 * SS, 6 * SS, D - 6 * SS, D - 6 * SS], a0, a1, fill=255, width=6 * SS)
    img.paste((255, 200, 90, 255), (0, 0), glow.filter(ImageFilter.GaussianBlur(SS * 2.5)))
    d = ImageDraw.Draw(img)
    for a0, a1 in ((200, 330), (20, 150)):
        d.arc([6 * SS, 6 * SS, D - 6 * SS, D - 6 * SS], a0, a1, fill=(255, 226, 130, 255), width=3 * SS)
    # small swoosh emblem
    cx, cy = D * 0.8, D * 0.82
    d.polygon([(cx - 8 * SS, cy + 4 * SS), (cx + 8 * SS, cy - 6 * SS), (cx + 2 * SS, cy + 2 * SS)],
              fill=(255, 220, 120, 255), outline=(110, 70, 20, 255))
    save('target_ring', down(img))


# ---------------------------------------------------------------- write
def write_manifest():
    lines = ['-- Generated by tools/make_art.py: content size of each texture (canvas is padded to power-of-two).',
             'return {']
    for k in sorted(manifest):
        w, h = manifest[k]
        lines.append(f"    ['{k}'] = {{ {w}, {h} }},")
    lines.append('};')
    with open(os.path.join(ROOT, 'manifest.lua'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    os.makedirs(ROOT, exist_ok=True)
    for f in os.listdir(ROOT):
        # clear old output, but not the macro or action icons (mi_*.png by make_icons.py, ai_*.png by
        # make_action_icons.py)
        if f.endswith('.png') and not f.startswith(('mi_', 'ai_')):
            os.remove(os.path.join(ROOT, f))
    gauge_track()
    gauge_fill('gauge_fill_hp', HP_STOPS)
    gauge_fill('gauge_fill_mp', MP_STOPS)
    gauge_fill('gauge_fill_tp', TP_STOPS)
    gauge_tip()
    gauge_swoosh()
    slot_rings()
    slot_well()
    glyph_discs()
    recast_sheet()
    motif('motif_sword', 'sword')
    motif('motif_wand', 'wand')
    bar_band()
    crest()
    tooltip_panel()
    long_tube('tube_track_long', 300, 11, track=True)
    long_tube('tube_fill_enemy', 300, 11, ENEMY_HP)
    long_tube('tube_track_party', 120, 8, track=True)
    long_tube('tube_fill_party_hp', 120, 8, HP_STOPS)
    long_tube('tube_fill_party_mp', 120, 8, MP_STOPS)
    long_tube('tube_fill_party_tp', 120, 8, TP_STOPS)
    enmity_pills()
    aggression_orbs()
    name_rule()
    lock_mark()
    diamond('leader_diamond', (250, 212, 90, 255))
    long_tube('cast_track', 260, 12, track=True)
    long_tube('cast_fill', 260, 12, CAST_STOPS)
    long_tube('exp_track', 520, 6, track=True)
    long_tube('exp_fill', 520, 6, EXP_STOPS)
    job_tile()
    log_tabs()
    log_panel()
    log_wash()
    lobby_glow()
    win_body()
    win_hud()
    win_title()
    title_swash()
    row_sel()
    cursor_gold()
    dlg_box()
    dlg_name()
    dlg_arrow()
    cmd_panel('cmd_panel', (30, 44, 92, 228), (12, 20, 52, 228), (140, 150, 180, 210), 1)
    cmd_panel('cmd_panel_sel', (70, 108, 196, 242), (28, 52, 128, 242), (232, 200, 120, 255), 2)
    crystal_shard()
    btn_pill()
    win_body_gold()
    win_title_gold()
    row_sel_gold()
    btn_pill_gold()
    cmd_panel('cmd_panel_gold', (34, 30, 26, 228), (10, 9, 8, 228), (150, 128, 86, 210), 1)
    cmd_panel('cmd_panel_sel_gold', (110, 84, 36, 242), (40, 30, 14, 242), (250, 220, 140, 255), 2)
    slot_square()
    for n, i, o, g in MICRO:
        roundel(n, i, o, g)
    minimap_disc()
    minimap_rim()
    death_vignette()
    death_band()
    hair_line()
    wide_button()
    button_glow()
    white()
    fov_wedge('fov_passive', (255, 226, 120, 255))
    fov_wedge('fov_active', (255, 70, 60, 255))
    map_arrow()
    map_dot()
    map_ntab()
    clock_orbs()
    target_ring()
    write_manifest()
    print('wrote', len(manifest), 'textures to', os.path.normpath(ROOT))
