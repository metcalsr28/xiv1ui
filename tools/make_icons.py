"""Generate xiv1ui's macro icons: original painted discs (44 px, the size of an action-bar slot well) with an emblem.

Run: nix-shell --run 'python3 tools/make_icons.py'
Writes addons/xiv1ui/assets/mi_<name>.png (64x64 canvases, art at top-left), assets/icons_manifest.lua (sizes), and addons/xiv1ui/core/macro_icons.lua (the list the Macros window offers).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import make_art as A  # noqa: E402

S = 44
SS = A.SS
W = S * SS

FIELDS = {   # disc colours (top, bottom)
    'red':    ((236, 110, 96), (120, 24, 26)),
    'orange': ((246, 170, 86), (150, 70, 20)),
    'gold':   ((250, 222, 130), (150, 104, 30)),
    'green':  ((150, 220, 120), (34, 104, 46)),
    'teal':   ((120, 220, 210), (24, 100, 110)),
    'blue':   ((130, 176, 246), (28, 56, 150)),
    'violet': ((196, 150, 240), (78, 38, 140)),
    'pink':   ((246, 150, 200), (140, 40, 96)),
    'grey':   ((200, 204, 214), (70, 74, 88)),
    'dark':   ((110, 112, 130), (24, 24, 34)),
}

INK = (255, 252, 240, 255)
SHADE = (20, 16, 24, 220)


def disc(field):
    top, bot = FIELDS[field]
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    body = A.vgloss(A.vgrad(W, W, [(0, top + (255,)), (1, bot + (255,))]), top=0.48, strength=70)
    img.paste(body, (0, 0), A.circle_mask(W, SS))
    return img


def emblem(img, draw_fn):
    """Draw the emblem in INK on a mask, give it a dark outline/drop shadow, and composite it onto the disc."""
    m = Image.new('L', (W, W), 0)
    draw_fn(ImageDraw.Draw(m), W)
    sh = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(SS))
    shadow = Image.new('RGBA', (W, W), SHADE)
    img.paste(shadow, (SS // 2, SS), sh)
    ink = Image.new('RGBA', (W, W), INK)
    img.paste(ink, (0, 0), m)
    return img


def P(pts, w):
    return [(x * w, y * w) for x, y in pts]


# ---- emblems (coordinates in 0..1 of the icon) -------------------------------------------------
def sword(d, w):
    d.polygon(P([(0.50, 0.12), (0.56, 0.62), (0.44, 0.62)], w), fill=255)
    d.rectangle(P([(0.32, 0.62), (0.68, 0.68)], w), fill=255)
    d.rectangle(P([(0.47, 0.68), (0.53, 0.84)], w), fill=255)
    d.ellipse(P([(0.45, 0.83), (0.55, 0.91)], w), fill=255)


def shield(d, w):
    d.polygon(P([(0.25, 0.22), (0.75, 0.22), (0.75, 0.50), (0.50, 0.86), (0.25, 0.50)], w), fill=255)
    d.polygon(P([(0.33, 0.30), (0.67, 0.30), (0.67, 0.49), (0.50, 0.74), (0.33, 0.49)], w), fill=0)
    d.rectangle(P([(0.47, 0.30), (0.53, 0.70)], w), fill=255)


def staff(d, w):
    d.line(P([(0.30, 0.86), (0.62, 0.30)], w), fill=255, width=int(0.07 * w))
    d.ellipse(P([(0.55, 0.12), (0.80, 0.37)], w), outline=255, width=int(0.06 * w))
    d.ellipse(P([(0.63, 0.20), (0.72, 0.29)], w), fill=255)


def potion(d, w):
    d.ellipse(P([(0.26, 0.40), (0.74, 0.88)], w), fill=255)
    d.rectangle(P([(0.42, 0.18), (0.58, 0.44)], w), fill=255)
    d.rectangle(P([(0.38, 0.14), (0.62, 0.20)], w), fill=255)
    d.ellipse(P([(0.36, 0.56), (0.48, 0.68)], w), fill=0)


def heart(d, w):
    d.ellipse(P([(0.20, 0.24), (0.52, 0.56)], w), fill=255)
    d.ellipse(P([(0.48, 0.24), (0.80, 0.56)], w), fill=255)
    d.polygon(P([(0.22, 0.46), (0.78, 0.46), (0.50, 0.84)], w), fill=255)


def star(d, w):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 0.36 if i % 2 == 0 else 0.15
        pts.append((0.5 + r * math.cos(a), 0.53 + r * math.sin(a)))
    d.polygon(P(pts, w), fill=255)


def flame(d, w):
    d.polygon(P([(0.50, 0.12), (0.70, 0.42), (0.74, 0.62), (0.62, 0.84), (0.38, 0.84), (0.26, 0.62), (0.34, 0.40),
                 (0.42, 0.52)], w), fill=255)
    d.polygon(P([(0.52, 0.48), (0.60, 0.66), (0.54, 0.80), (0.44, 0.78), (0.42, 0.64)], w), fill=0)


def snow(d, w):
    for i in range(3):
        a = i * math.pi / 3
        d.line(P([(0.5 - 0.34 * math.cos(a), 0.5 - 0.34 * math.sin(a)), (0.5 + 0.34 * math.cos(a), 0.5 + 0.34 * math.sin(a))], w),
               fill=255, width=int(0.07 * w))
    d.ellipse(P([(0.42, 0.42), (0.58, 0.58)], w), fill=255)


def wind(d, w):
    for y, l in ((0.34, 0.62), (0.50, 0.74), (0.66, 0.54)):
        d.line(P([(0.20, y), (l, y)], w), fill=255, width=int(0.07 * w))
        d.arc(P([(l - 0.10, y - 0.14), (l + 0.08, y + 0.02)], w), -90, 120, fill=255, width=int(0.06 * w))


def rock(d, w):
    d.polygon(P([(0.22, 0.74), (0.30, 0.42), (0.48, 0.26), (0.70, 0.34), (0.80, 0.70), (0.60, 0.80)], w), fill=255)
    d.line(P([(0.48, 0.26), (0.52, 0.56), (0.80, 0.70)], w), fill=0, width=int(0.04 * w))


def bolt(d, w):
    d.polygon(P([(0.58, 0.10), (0.28, 0.56), (0.48, 0.56), (0.40, 0.90), (0.74, 0.40), (0.54, 0.40)], w), fill=255)


def drop(d, w):
    d.polygon(P([(0.50, 0.14), (0.72, 0.52), (0.28, 0.52)], w), fill=255)
    d.ellipse(P([(0.27, 0.36), (0.73, 0.84)], w), fill=255)
    d.ellipse(P([(0.36, 0.56), (0.46, 0.68)], w), fill=0)


def sun(d, w):
    d.ellipse(P([(0.34, 0.34), (0.66, 0.66)], w), fill=255)
    for i in range(8):
        a = i * math.pi / 4
        d.line(P([(0.5 + 0.22 * math.cos(a), 0.5 + 0.22 * math.sin(a)), (0.5 + 0.38 * math.cos(a), 0.5 + 0.38 * math.sin(a))], w),
               fill=255, width=int(0.06 * w))


def moon(d, w):
    d.ellipse(P([(0.22, 0.20), (0.78, 0.76)], w), fill=255)
    d.ellipse(P([(0.38, 0.12), (0.90, 0.64)], w), fill=0)


def arrow(d, w):
    d.polygon(P([(0.50, 0.14), (0.78, 0.46), (0.60, 0.46), (0.60, 0.86), (0.40, 0.86), (0.40, 0.46), (0.22, 0.46)], w), fill=255)


def bubble(d, w):
    d.rounded_rectangle(P([(0.18, 0.22), (0.82, 0.66)], w), radius=int(0.14 * w), fill=255)
    d.polygon(P([(0.30, 0.60), (0.46, 0.64), (0.26, 0.84)], w), fill=255)
    for x in (0.34, 0.50, 0.66):
        d.ellipse(P([(x - 0.05, 0.39), (x + 0.05, 0.49)], w), fill=0)


def note(d, w):
    d.ellipse(P([(0.22, 0.62), (0.44, 0.82)], w), fill=255)
    d.ellipse(P([(0.56, 0.54), (0.78, 0.74)], w), fill=255)
    d.rectangle(P([(0.38, 0.22), (0.44, 0.72)], w), fill=255)
    d.rectangle(P([(0.72, 0.16), (0.78, 0.64)], w), fill=255)
    d.polygon(P([(0.38, 0.22), (0.78, 0.14), (0.78, 0.26), (0.38, 0.34)], w), fill=255)


def crown(d, w):
    d.polygon(P([(0.20, 0.72), (0.20, 0.34), (0.36, 0.52), (0.50, 0.26), (0.64, 0.52), (0.80, 0.34), (0.80, 0.72)], w), fill=255)
    d.rectangle(P([(0.20, 0.74), (0.80, 0.82)], w), fill=255)


def skull(d, w):
    d.ellipse(P([(0.24, 0.18), (0.76, 0.68)], w), fill=255)
    d.rectangle(P([(0.34, 0.60), (0.66, 0.82)], w), fill=255)
    d.ellipse(P([(0.32, 0.38), (0.46, 0.52)], w), fill=0)
    d.ellipse(P([(0.54, 0.38), (0.68, 0.52)], w), fill=0)
    for x in (0.42, 0.50, 0.58):
        d.line(P([(x, 0.70), (x, 0.82)], w), fill=0, width=int(0.03 * w))


def eye(d, w):
    d.ellipse(P([(0.14, 0.32), (0.86, 0.68)], w), fill=255)
    d.ellipse(P([(0.36, 0.34), (0.64, 0.66)], w), fill=0)
    d.ellipse(P([(0.44, 0.42), (0.56, 0.58)], w), fill=255)


def bow(d, w):
    d.arc(P([(0.16, 0.14), (0.64, 0.86)], w), -70, 70, fill=255, width=int(0.07 * w))
    d.line(P([(0.48, 0.18), (0.48, 0.82)], w), fill=255, width=int(0.03 * w))
    d.line(P([(0.24, 0.50), (0.84, 0.50)], w), fill=255, width=int(0.04 * w))
    d.polygon(P([(0.84, 0.50), (0.74, 0.44), (0.74, 0.56)], w), fill=255)


def axe(d, w):
    d.line(P([(0.34, 0.86), (0.56, 0.18)], w), fill=255, width=int(0.07 * w))
    d.pieslice(P([(0.42, 0.14), (0.86, 0.58)], w), -100, 40, fill=255)


def dagger(d, w):
    d.polygon(P([(0.72, 0.18), (0.80, 0.26), (0.44, 0.62), (0.36, 0.54)], w), fill=255)
    d.line(P([(0.28, 0.48), (0.50, 0.70)], w), fill=255, width=int(0.06 * w))
    d.line(P([(0.40, 0.60), (0.22, 0.78)], w), fill=255, width=int(0.07 * w))


def cross(d, w):
    d.rectangle(P([(0.40, 0.18), (0.60, 0.82)], w), fill=255)
    d.rectangle(P([(0.18, 0.40), (0.82, 0.60)], w), fill=255)


def hourglass(d, w):
    d.polygon(P([(0.28, 0.18), (0.72, 0.18), (0.54, 0.50), (0.72, 0.82), (0.28, 0.82), (0.46, 0.50)], w), fill=255)
    d.polygon(P([(0.36, 0.24), (0.64, 0.24), (0.50, 0.44)], w), fill=0)


def gear(d, w):
    for i in range(8):
        a = i * math.pi / 4
        d.rectangle(P([(0.5 + 0.30 * math.cos(a) - 0.07, 0.5 + 0.30 * math.sin(a) - 0.07),
                       (0.5 + 0.30 * math.cos(a) + 0.07, 0.5 + 0.30 * math.sin(a) + 0.07)], w), fill=255)
    d.ellipse(P([(0.24, 0.24), (0.76, 0.76)], w), fill=255)
    d.ellipse(P([(0.40, 0.40), (0.60, 0.60)], w), fill=0)


def coin(d, w):
    d.ellipse(P([(0.20, 0.20), (0.80, 0.80)], w), fill=255)
    d.ellipse(P([(0.30, 0.30), (0.70, 0.70)], w), outline=0, width=int(0.04 * w))
    d.rectangle(P([(0.47, 0.38), (0.53, 0.62)], w), fill=0)


def key(d, w):
    d.ellipse(P([(0.16, 0.30), (0.46, 0.60)], w), fill=255)
    d.ellipse(P([(0.25, 0.39), (0.37, 0.51)], w), fill=0)
    d.rectangle(P([(0.42, 0.41), (0.84, 0.49)], w), fill=255)
    d.rectangle(P([(0.70, 0.49), (0.76, 0.62)], w), fill=255)
    d.rectangle(P([(0.80, 0.49), (0.84, 0.58)], w), fill=255)


def flag(d, w):
    d.rectangle(P([(0.26, 0.14), (0.32, 0.88)], w), fill=255)
    d.polygon(P([(0.32, 0.16), (0.80, 0.30), (0.32, 0.46)], w), fill=255)


def house(d, w):
    d.polygon(P([(0.50, 0.16), (0.84, 0.48), (0.16, 0.48)], w), fill=255)
    d.rectangle(P([(0.26, 0.48), (0.74, 0.82)], w), fill=255)
    d.rectangle(P([(0.44, 0.60), (0.56, 0.82)], w), fill=0)


def book(d, w):
    d.polygon(P([(0.14, 0.26), (0.48, 0.32), (0.48, 0.82), (0.14, 0.76)], w), fill=255)
    d.polygon(P([(0.86, 0.26), (0.52, 0.32), (0.52, 0.82), (0.86, 0.76)], w), fill=255)


def scroll(d, w):
    d.rectangle(P([(0.26, 0.24), (0.74, 0.76)], w), fill=255)
    d.ellipse(P([(0.18, 0.16), (0.34, 0.32)], w), fill=255)
    d.ellipse(P([(0.66, 0.68), (0.82, 0.84)], w), fill=255)
    for y in (0.40, 0.50, 0.60):
        d.line(P([(0.34, y), (0.66, y)], w), fill=0, width=int(0.03 * w))


def bell(d, w):
    d.pieslice(P([(0.24, 0.18), (0.76, 0.70)], w), 180, 360, fill=255)
    d.rectangle(P([(0.24, 0.44), (0.76, 0.70)], w), fill=255)
    d.rectangle(P([(0.18, 0.68), (0.82, 0.74)], w), fill=255)
    d.ellipse(P([(0.44, 0.74), (0.56, 0.86)], w), fill=255)


def target(d, w):
    d.ellipse(P([(0.16, 0.16), (0.84, 0.84)], w), outline=255, width=int(0.07 * w))
    d.ellipse(P([(0.32, 0.32), (0.68, 0.68)], w), outline=255, width=int(0.07 * w))
    d.ellipse(P([(0.44, 0.44), (0.56, 0.56)], w), fill=255)


def fist(d, w):
    d.rounded_rectangle(P([(0.26, 0.34), (0.74, 0.72)], w), radius=int(0.08 * w), fill=255)
    for x in (0.30, 0.42, 0.54):
        d.line(P([(x + 0.06, 0.36), (x + 0.06, 0.52)], w), fill=0, width=int(0.025 * w))
    d.rectangle(P([(0.34, 0.72), (0.66, 0.86)], w), fill=255)


def wing(d, w):
    for i, (y, l) in enumerate(((0.30, 0.80), (0.44, 0.74), (0.58, 0.66), (0.72, 0.56))):
        d.ellipse(P([(0.20, y - 0.06), (l, y + 0.06)], w), fill=255)


ICONS = [
    ('sword', 'red', sword), ('axe', 'red', axe), ('dagger', 'orange', dagger), ('bow', 'green', bow),
    ('fist', 'orange', fist), ('shield', 'grey', shield), ('staff', 'violet', staff), ('target', 'red', target),
    ('fire', 'red', flame), ('ice', 'teal', snow), ('wind', 'green', wind), ('earth', 'orange', rock),
    ('thunder', 'violet', bolt), ('water', 'blue', drop), ('light', 'gold', sun), ('dark', 'dark', moon),
    ('cure', 'green', cross), ('heart', 'pink', heart), ('potion', 'teal', potion), ('star', 'gold', star),
    ('up', 'blue', arrow), ('wing', 'teal', wing), ('time', 'gold', hourglass), ('eye', 'blue', eye),
    ('chat', 'blue', bubble), ('song', 'pink', note), ('crown', 'gold', crown), ('skull', 'dark', skull),
    ('gear', 'grey', gear), ('gil', 'gold', coin), ('key', 'gold', key), ('flag', 'red', flag),
    ('home', 'green', house), ('book', 'violet', book), ('scroll', 'orange', scroll), ('bell', 'gold', bell),
]

if __name__ == '__main__':
    A.manifest.clear()
    names = []
    for name, field, fn in ICONS:
        img = emblem(disc(field), fn)
        img = A.down(img)
        A.save('mi_' + name, img)
        names.append(name)
    # sizes go in their own manifest (make_art rewrites manifest.lua); core/layout.lua loads both
    with open(os.path.join(A.ROOT, 'icons_manifest.lua'), 'w') as f:
        f.write('-- Generated by tools/make_icons.py: content size of each macro icon texture.\nreturn {\n')
        for n in names:
            f.write("    ['mi_%s'] = { %d, %d },\n" % (n, S, S))
        f.write('};\n')
    out = os.path.join(A.ROOT, '..', 'core', 'macro_icons.lua')
    with open(out, 'w') as f:
        f.write('-- Generated by tools/make_icons.py: the macro icons the Macros window offers (textures mi_<name>).\n')
        f.write('return { ' + ', '.join("'%s'" % n for n in names) + ' };\n')
    print('wrote', len(names), 'icons')
