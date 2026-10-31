"""Generate xiv1ui's action icons: one painted emblem per spell / ability / weapon skill / command, drawn over the
action bar slot's own disc (which already carries the element or kind colour), in place of the old letter
abbreviations ("Cu", "At" ...).

Run: nix-shell --run 'python3 tools/make_action_icons.py'
Writes addons/xiv1ui/assets/ai_<slug>.png (64x64 canvases, art 44x44 at the top-left), assets/action_icons_manifest.lua
(sizes) and addons/xiv1ui/core/action_icons.lua (action name -> texture).

Each emblem draws on two masks: `ink` (the light main shape) and `acc` (an accent in the emblem's own colour). Both
get a soft dark outline so they read on any disc. Covers what the six starting jobs use up to level 10, the first
weapon skill of each weapon type, the basic commands, and one shared icon for every Trust.
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
INK = (255, 250, 238)
SHADE = (14, 10, 20, 230)

ACCENTS = {
    'light': (255, 226, 120), 'holy': (255, 244, 190), 'green': (120, 236, 140), 'red': (255, 96, 80),
    'blue': (110, 180, 255), 'teal': (110, 236, 220), 'earth': (232, 168, 92), 'wind': (150, 240, 150),
    'violet': (206, 140, 255), 'dark': (160, 110, 210), 'gold': (255, 206, 90), 'grey': (200, 206, 220),
    'poison': (170, 230, 90), 'fire': (255, 140, 60),
}


def P(pts):
    return [(x * W, y * W) for x, y in pts]


def L(w):
    return max(1, int(w * W))


def lua_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def make(fn, accent):
    ink = Image.new('L', (W, W), 0)
    acc = Image.new('L', (W, W), 0)
    fn(ImageDraw.Draw(ink), ImageDraw.Draw(acc))
    both = Image.fromarray if False else None
    m = Image.new('L', (W, W), 0)
    m.paste(255, (0, 0), ink)
    m.paste(255, (0, 0), acc)
    sh = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(SS * 1.2))
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.paste(Image.new('RGBA', (W, W), SHADE), (SS // 2, SS), sh)
    img.paste(Image.new('RGBA', (W, W), ACCENTS[accent] + (255,)), (0, 0), acc)
    img.paste(Image.new('RGBA', (W, W), INK + (255,)), (0, 0), ink)
    return A.down(img)


# ---- shared shapes ------------------------------------------------------------------------------------------------
def cross(d, cx=0.5, cy=0.5, r=0.26, t=0.10):
    d.rectangle(P([(cx - t / 2, cy - r), (cx + t / 2, cy + r)]), fill=255)
    d.rectangle(P([(cx - r, cy - t / 2), (cx + r, cy + t / 2)]), fill=255)


def sparkle(d, cx, cy, r):
    d.polygon(P([(cx, cy - r), (cx + r * 0.25, cy - r * 0.25), (cx + r, cy), (cx + r * 0.25, cy + r * 0.25),
                 (cx, cy + r), (cx - r * 0.25, cy + r * 0.25), (cx - r, cy), (cx - r * 0.25, cy - r * 0.25)]), fill=255)


def shield_shape(d, x0=0.24, y0=0.18, x1=0.76, y1=0.86, fill=255):
    mx = (x0 + x1) / 2
    d.polygon(P([(x0, y0), (x1, y0), (x1, y0 + (y1 - y0) * 0.45), (mx, y1), (x0, y0 + (y1 - y0) * 0.45)]), fill=fill)


def ra_dots(d):
    """The -ra (area) mark: three small dots above the emblem."""
    for x in (0.34, 0.50, 0.66):
        d.ellipse(P([(x - 0.045, 0.06), (x + 0.045, 0.15)]), fill=255)


def rock_shape(d, s=1.0, ox=0.0, oy=0.0):
    pts = [(0.22, 0.74), (0.30, 0.44), (0.46, 0.28), (0.68, 0.34), (0.80, 0.68), (0.60, 0.80)]
    d.polygon(P([(ox + 0.5 + (x - 0.5) * s, oy + 0.5 + (y - 0.5) * s) for x, y in pts]), fill=255)


def drop_shape(d, s=1.0, ox=0.0, oy=0.0):
    def q(x, y):
        return (ox + 0.5 + (x - 0.5) * s, oy + 0.5 + (y - 0.5) * s)
    d.polygon(P([q(0.50, 0.14), q(0.72, 0.52), q(0.28, 0.52)]), fill=255)
    d.ellipse(P([q(0.27, 0.36), q(0.73, 0.84)]), fill=255)


def swirl(d, cx=0.5, cy=0.52, r=0.30, w=0.07):
    for i, (a0, a1, rr) in enumerate(((200, 470, r), (220, 470, r * 0.62), (240, 470, r * 0.28))):
        d.arc(P([(cx - rr, cy - rr), (cx + rr, cy + rr)]), a0, a1, fill=255, width=L(w))


def zzz(d):
    for x, y, s in ((0.34, 0.62, 0.20), (0.56, 0.42, 0.15), (0.72, 0.26, 0.11)):
        d.line(P([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x - s / 2, y + s / 2), (x + s / 2, y + s / 2)]),
               fill=255, width=L(0.05))


def skull(d, oy=0.0):
    d.ellipse(P([(0.28, 0.20 + oy), (0.72, 0.62 + oy)]), fill=255)
    d.rectangle(P([(0.36, 0.54 + oy), (0.64, 0.74 + oy)]), fill=255)
    d.ellipse(P([(0.35, 0.36 + oy), (0.46, 0.48 + oy)]), fill=0)
    d.ellipse(P([(0.54, 0.36 + oy), (0.65, 0.48 + oy)]), fill=0)
    for x in (0.42, 0.50, 0.58):
        d.line(P([(x, 0.64 + oy), (x, 0.74 + oy)]), fill=0, width=L(0.025))


def blade(d, a=-45, cx=0.5, cy=0.5, length=0.70, width=0.09):
    r = math.radians(a)
    ux, uy = math.cos(r), math.sin(r)
    px, py = -uy, ux
    tip = (cx + ux * length / 2, cy + uy * length / 2)
    base = (cx - ux * length * 0.22, cy - uy * length * 0.22)
    d.polygon(P([tip, (base[0] + px * width / 2, base[1] + py * width / 2),
                 (base[0] - px * width / 2, base[1] - py * width / 2)]), fill=255)
    g = 0.16
    d.line(P([(base[0] + px * g, base[1] + py * g), (base[0] - px * g, base[1] - py * g)]), fill=255, width=L(0.06))
    hilt = (cx - ux * length / 2, cy - uy * length / 2)
    d.line(P([base, hilt]), fill=255, width=L(0.06))


def fist_shape(d, ox=0.0, oy=0.0):
    d.rounded_rectangle(P([(0.30 + ox, 0.30 + oy), (0.70 + ox, 0.62 + oy)]), radius=L(0.06), fill=255)
    for i in range(4):
        x = 0.31 + ox + i * 0.10
        d.line(P([(x, 0.30 + oy), (x, 0.42 + oy)]), fill=0, width=L(0.02))
    d.rectangle(P([(0.38 + ox, 0.60 + oy), (0.66 + ox, 0.82 + oy)]), fill=255)
    d.rounded_rectangle(P([(0.22 + ox, 0.40 + oy), (0.36 + ox, 0.56 + oy)]), radius=L(0.04), fill=255)


def hand(d):
    d.rounded_rectangle(P([(0.32, 0.44), (0.66, 0.80)]), radius=L(0.08), fill=255)
    for i, h in enumerate((0.20, 0.14, 0.16, 0.24)):
        x = 0.335 + i * 0.085
        d.rounded_rectangle(P([(x, h), (x + 0.07, 0.52)]), radius=L(0.035), fill=255)
    d.polygon(P([(0.66, 0.60), (0.80, 0.44), (0.84, 0.50), (0.68, 0.72)]), fill=255)


# ---- spells -------------------------------------------------------------------------------------------------------
def cure(i, a):
    cross(i, 0.5, 0.54, 0.26, 0.12)
    sparkle(a, 0.76, 0.24, 0.10)
    sparkle(a, 0.24, 0.30, 0.06)


def poisona(i, a):
    drop_shape(a, 0.62, -0.10, 0.06)
    cross(i, 0.66, 0.36, 0.16, 0.08)


def paralyna(i, a):
    a.polygon(P([(0.40, 0.18), (0.20, 0.50), (0.34, 0.50), (0.26, 0.82), (0.50, 0.44), (0.36, 0.44)]), fill=255)
    cross(i, 0.66, 0.40, 0.16, 0.08)


def dia(i, a):
    i.ellipse(P([(0.34, 0.34), (0.66, 0.66)]), fill=255)
    i.ellipse(P([(0.42, 0.42), (0.58, 0.58)]), fill=0)
    for k in range(8):
        t = k * math.pi / 4
        a.line(P([(0.5 + 0.22 * math.cos(t), 0.5 + 0.22 * math.sin(t)),
                  (0.5 + 0.38 * math.cos(t), 0.5 + 0.38 * math.sin(t))]), fill=255, width=L(0.05))


def banish(i, a):
    sparkle(a, 0.5, 0.5, 0.40)
    sparkle(i, 0.5, 0.5, 0.20)


def protect(i, a):
    shield_shape(i)
    shield_shape(i, 0.32, 0.26, 0.68, 0.74, fill=0)
    cross(a, 0.5, 0.46, 0.12, 0.07)


def protectra(i, a):
    protect(i, a)
    ra_dots(a)


def aquaveil(i, a):
    drop_shape(i, 0.55, 0, 0.04)
    a.arc(P([(0.14, 0.18), (0.86, 0.90)]), 200, 340, fill=255, width=L(0.06))
    a.arc(P([(0.14, 0.18), (0.86, 0.90)]), 20, 160, fill=255, width=L(0.06))


def paralyze(i, a):
    i.ellipse(P([(0.20, 0.56), (0.80, 0.74)]), outline=255, width=L(0.05))
    a.polygon(P([(0.56, 0.12), (0.34, 0.46), (0.48, 0.46), (0.40, 0.70), (0.66, 0.36), (0.52, 0.36)]), fill=255)


def bar_of(sym):
    def f(i, a):
        shield_shape(i)
        shield_shape(i, 0.31, 0.25, 0.69, 0.75, fill=0)
        sym(a)
    return f


def sym_stone(a):
    rock_shape(a, 0.42, 0, -0.03)


def sym_water(a):
    drop_shape(a, 0.40, 0, -0.03)


def sym_sleep(a):
    for x, y, s in ((0.42, 0.56, 0.12), (0.58, 0.40, 0.09)):
        a.line(P([(x - s / 2, y - s / 2), (x + s / 2, y - s / 2), (x - s / 2, y + s / 2), (x + s / 2, y + s / 2)]),
               fill=255, width=L(0.04))


def sym_poison(a):
    # a tiny skull
    a.ellipse(P([(0.39, 0.32), (0.61, 0.52)]), fill=255)
    a.rectangle(P([(0.43, 0.48), (0.57, 0.58)]), fill=255)
    a.ellipse(P([(0.42, 0.38), (0.48, 0.44)]), fill=0)
    a.ellipse(P([(0.52, 0.38), (0.58, 0.44)]), fill=0)


def ra(f):
    def g(i, a):
        f(i, a)
        ra_dots(a)
    return g


def aero(i, a):
    swirl(i)
    a.arc(P([(0.12, 0.16), (0.88, 0.92)]), 300, 360, fill=255, width=L(0.05))
    a.arc(P([(0.12, 0.16), (0.88, 0.92)]), 120, 180, fill=255, width=L(0.05))


def stone(i, a):
    rock_shape(i, 0.82, 0.04, 0.04)
    rock_shape(a, 0.36, -0.20, -0.22)


def water(i, a):
    drop_shape(i, 0.82, 0.04, 0.02)
    a.ellipse(P([(0.14, 0.70), (0.86, 0.90)]), outline=255, width=L(0.04))


def poison(i, a):
    skull(i, -0.02)
    for x, y in ((0.26, 0.82), (0.74, 0.80), (0.50, 0.90)):
        a.ellipse(P([(x - 0.05, y - 0.05), (x + 0.05, y + 0.05)]), fill=255)


def bio(i, a):
    skull(i, -0.04)
    a.arc(P([(0.10, 0.10), (0.90, 0.90)]), 30, 150, fill=255, width=L(0.06))


def blaze_spikes(i, a):
    for k in range(8):
        t = k * math.pi / 4
        i.polygon(P([(0.5 + 0.40 * math.cos(t), 0.5 + 0.40 * math.sin(t)),
                     (0.5 + 0.20 * math.cos(t + 0.3), 0.5 + 0.20 * math.sin(t + 0.3)),
                     (0.5 + 0.20 * math.cos(t - 0.3), 0.5 + 0.20 * math.sin(t - 0.3))]), fill=255)
    a.polygon(P([(0.50, 0.30), (0.62, 0.50), (0.60, 0.66), (0.40, 0.66), (0.38, 0.50)]), fill=255)


def blind(i, a):
    i.chord(P([(0.16, 0.30), (0.84, 0.74)]), 200, 340, fill=255)
    i.chord(P([(0.16, 0.26), (0.84, 0.70)]), 20, 160, fill=255)
    i.ellipse(P([(0.38, 0.38), (0.62, 0.62)]), fill=0)
    a.line(P([(0.22, 0.78), (0.78, 0.22)]), fill=255, width=L(0.07))


def bind(i, a):
    for k, (x, y) in enumerate(((0.30, 0.34), (0.50, 0.50), (0.70, 0.66))):
        d = i if k % 2 == 0 else a
        d.ellipse(P([(x - 0.13, y - 0.09), (x + 0.13, y + 0.09)]), outline=255, width=L(0.05))


def trust(i, a):
    # two figures side by side: the caller and the summoned ally
    i.ellipse(P([(0.20, 0.22), (0.40, 0.42)]), fill=255)
    i.pieslice(P([(0.12, 0.44), (0.48, 0.92)]), 180, 360, fill=255)
    a.ellipse(P([(0.58, 0.18), (0.80, 0.40)]), fill=255)
    a.pieslice(P([(0.50, 0.42), (0.88, 0.94)]), 180, 360, fill=255)


# ---- job abilities ------------------------------------------------------------------------------------------------
def provoke(i, a):
    i.polygon(P([(0.22, 0.30), (0.62, 0.30), (0.62, 0.62), (0.40, 0.62), (0.30, 0.76), (0.32, 0.62), (0.22, 0.62)]),
              fill=255)
    a.rectangle(P([(0.70, 0.22), (0.78, 0.52)]), fill=255)
    a.ellipse(P([(0.69, 0.58), (0.79, 0.68)]), fill=255)


def mighty_strikes(i, a):
    blade(i, -50, 0.42, 0.56, 0.72)
    sparkle(a, 0.70, 0.30, 0.20)


def hundred_fists(i, a):
    fist_shape(a, 0.06, 0.04)
    fist_shape(i, -0.06, -0.04)


def boost(i, a):
    fist_shape(i, -0.04, 0.06)
    a.polygon(P([(0.74, 0.12), (0.88, 0.32), (0.79, 0.32), (0.79, 0.50), (0.69, 0.50), (0.69, 0.32), (0.60, 0.32)]),
              fill=255)


def benediction(i, a):
    # a pair of feathered wings around a cross
    for side in (-1, 1):
        for k in range(4):
            x0 = 0.5 + side * (0.10 + k * 0.07)
            top = 0.30 + k * 0.05
            i.polygon(P([(0.5 + side * 0.08, 0.50), (x0 + side * 0.10, top), (x0 + side * 0.13, top + 0.10),
                         (0.5 + side * 0.10, 0.62)]), fill=255)
    cross(a, 0.5, 0.52, 0.20, 0.09)


def manafont(i, a):
    i.polygon(P([(0.26, 0.86), (0.74, 0.86), (0.64, 0.66), (0.36, 0.66)]), fill=255)
    for k, x in enumerate((0.36, 0.50, 0.64)):
        a.ellipse(P([(x - 0.07, 0.40 - k % 2 * 0.16), (x + 0.07, 0.54 - k % 2 * 0.16)]), fill=255)
    a.line(P([(0.50, 0.62), (0.50, 0.30)]), fill=255, width=L(0.04))


def chainspell(i, a):
    for k, (x, y) in enumerate(((0.28, 0.66), (0.44, 0.52), (0.60, 0.38))):
        i.ellipse(P([(x - 0.12, y - 0.08), (x + 0.12, y + 0.08)]), outline=255, width=L(0.045))
    sparkle(a, 0.76, 0.24, 0.13)


def perfect_dodge(i, a):
    a.ellipse(P([(0.20, 0.16), (0.42, 0.38)]), fill=255)
    a.polygon(P([(0.18, 0.42), (0.40, 0.42), (0.36, 0.86), (0.22, 0.86)]), fill=255)
    i.ellipse(P([(0.52, 0.16), (0.74, 0.38)]), fill=255)
    i.polygon(P([(0.50, 0.42), (0.72, 0.42), (0.80, 0.86), (0.62, 0.86)]), fill=255)
    for y in (0.48, 0.62, 0.76):
        i.line(P([(0.84, y), (0.94, y)]), fill=255, width=L(0.03))


def steal(i, a):
    hand(i)
    a.ellipse(P([(0.54, 0.10), (0.84, 0.40)]), fill=255)
    a.ellipse(P([(0.62, 0.18), (0.76, 0.32)]), fill=0)


# ---- weapon skills: weapon + a motion accent -------------------------------------------------------------------
def slash_arc(a, cx=0.5, cy=0.5, r=0.40, s=200, e=300):
    a.arc(P([(cx - r, cy - r), (cx + r, cy + r)]), s, e, fill=255, width=L(0.06))


def fast_blade(i, a):
    blade(i, -45)
    for k in range(3):
        a.line(P([(0.14 + k * 0.06, 0.60 + k * 0.10), (0.34 + k * 0.06, 0.60 + k * 0.10)]), fill=255, width=L(0.035))


def wasp_sting(i, a):
    blade(i, -45, 0.46, 0.54, 0.56, 0.08)
    a.ellipse(P([(0.64, 0.14), (0.84, 0.34)]), fill=255)
    a.line(P([(0.64, 0.24), (0.84, 0.24)]), fill=0, width=L(0.03))


def combo(i, a):
    fist_shape(i, -0.02, 0.04)
    for k in range(3):
        a.arc(P([(0.06 + k * 0.05, 0.16 + k * 0.05), (0.94 - k * 0.05, 0.94 - k * 0.05)]), 200, 250, fill=255,
              width=L(0.035))


def raging_axe(i, a):
    i.line(P([(0.26, 0.88), (0.58, 0.22)]), fill=255, width=L(0.07))
    # the axe head: a broad curved blade on one side of the haft
    i.polygon(P([(0.52, 0.24), (0.80, 0.14), (0.88, 0.32), (0.84, 0.50), (0.62, 0.46), (0.56, 0.38)]), fill=255)
    i.polygon(P([(0.60, 0.30), (0.76, 0.24), (0.78, 0.36), (0.64, 0.38)]), fill=0)
    slash_arc(a, 0.48, 0.52, 0.42, 200, 260)


def shining_strike(i, a):
    i.line(P([(0.30, 0.86), (0.56, 0.36)]), fill=255, width=L(0.07))
    i.ellipse(P([(0.46, 0.14), (0.76, 0.44)]), fill=255)
    sparkle(a, 0.78, 0.18, 0.14)


def heavy_swing(i, a):
    i.line(P([(0.22, 0.86), (0.70, 0.20)]), fill=255, width=L(0.07))
    i.ellipse(P([(0.60, 0.10), (0.82, 0.32)]), fill=255)
    slash_arc(a, 0.42, 0.52, 0.36, 140, 230)


def hard_slash(i, a):
    blade(i, -60, 0.48, 0.50, 0.80, 0.14)
    slash_arc(a, 0.5, 0.5, 0.42, 300, 360)


def slice_(i, a):
    i.line(P([(0.30, 0.88), (0.48, 0.20)]), fill=255, width=L(0.06))
    i.chord(P([(0.20, 0.12), (0.84, 0.50)]), 180, 360, fill=255)
    i.chord(P([(0.28, 0.20), (0.92, 0.50)]), 180, 360, fill=0)
    slash_arc(a, 0.5, 0.56, 0.40, 20, 100)


def double_thrust(i, a):
    i.line(P([(0.16, 0.84), (0.72, 0.28)]), fill=255, width=L(0.05))
    i.polygon(P([(0.84, 0.16), (0.66, 0.26), (0.74, 0.34)]), fill=255)
    for k in (0, 1):
        a.line(P([(0.20 + k * 0.10, 0.44 + k * 0.10), (0.40 + k * 0.10, 0.24 + k * 0.10)]), fill=255, width=L(0.03))


def flaming_arrow(i, a):
    i.line(P([(0.18, 0.82), (0.74, 0.26)]), fill=255, width=L(0.045))
    i.polygon(P([(0.84, 0.16), (0.66, 0.24), (0.76, 0.34)]), fill=255)
    a.polygon(P([(0.18, 0.82), (0.14, 0.62), (0.26, 0.70), (0.30, 0.56), (0.38, 0.74)]), fill=255)


def hot_shot(i, a):
    i.rectangle(P([(0.16, 0.46), (0.66, 0.56)]), fill=255)
    i.polygon(P([(0.20, 0.56), (0.34, 0.56), (0.30, 0.80), (0.18, 0.78)]), fill=255)
    sparkle(a, 0.78, 0.50, 0.16)


# ---- commands -----------------------------------------------------------------------------------------------------
def attack(i, a):
    blade(i, -45)
    blade(a, -135)


def disengage(i, a):
    blade(i, -45, 0.5, 0.5, 0.62)
    a.ellipse(P([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=L(0.06))
    a.line(P([(0.24, 0.76), (0.76, 0.24)]), fill=255, width=L(0.06))


def check(i, a):
    i.ellipse(P([(0.18, 0.16), (0.62, 0.60)]), outline=255, width=L(0.07))
    i.line(P([(0.56, 0.56), (0.84, 0.84)]), fill=255, width=L(0.09))
    a.ellipse(P([(0.28, 0.26), (0.40, 0.38)]), fill=255)


def heal(i, a):
    zzz(i)
    a.chord(P([(0.10, 0.70), (0.90, 1.02)]), 180, 360, fill=255)


def ranged_attack(i, a):
    i.arc(P([(0.12, 0.14), (0.68, 0.86)]), 270, 90, fill=255, width=L(0.06))
    i.line(P([(0.40, 0.14), (0.40, 0.86)]), fill=255, width=L(0.025))
    a.line(P([(0.30, 0.50), (0.88, 0.50)]), fill=255, width=L(0.04))
    a.polygon(P([(0.92, 0.50), (0.80, 0.42), (0.80, 0.58)]), fill=255)


def assist(i, a):
    i.ellipse(P([(0.14, 0.14), (0.86, 0.86)]), outline=255, width=L(0.05))
    i.ellipse(P([(0.40, 0.40), (0.60, 0.60)]), fill=255)
    for t in (0, 90, 180, 270):
        r = math.radians(t)
        a.line(P([(0.5 + 0.20 * math.cos(r), 0.5 + 0.20 * math.sin(r)),
                  (0.5 + 0.46 * math.cos(r), 0.5 + 0.46 * math.sin(r))]), fill=255, width=L(0.05))


# name -> (slug, accent, drawing). Names are the game's (spells / abilities / weapon skills) or the command labels.
ICONS = [
    ('Cure', 'cure', 'green', cure), ('Poisona', 'poisona', 'poison', poisona),
    ('Paralyna', 'paralyna', 'gold', paralyna), ('Dia', 'dia', 'light', dia), ('Banish', 'banish', 'holy', banish),
    ('Protect', 'protect', 'gold', protect), ('Protectra', 'protectra', 'gold', protectra),
    ('Aquaveil', 'aquaveil', 'blue', aquaveil), ('Paralyze', 'paralyze', 'gold', paralyze),
    ('Barstone', 'barstone', 'earth', bar_of(sym_stone)), ('Barwater', 'barwater', 'blue', bar_of(sym_water)),
    ('Barsleep', 'barsleep', 'violet', bar_of(sym_sleep)), ('Barpoison', 'barpoison', 'poison', bar_of(sym_poison)),
    ('Barstonra', 'barstonra', 'earth', ra(bar_of(sym_stone))), ('Barwatera', 'barwatera', 'blue', ra(bar_of(sym_water))),
    ('Barsleepra', 'barsleepra', 'violet', ra(bar_of(sym_sleep))),
    ('Barpoisonra', 'barpoisonra', 'poison', ra(bar_of(sym_poison))),
    ('Aero', 'aero', 'wind', aero), ('Stone', 'stone', 'earth', stone), ('Water', 'water', 'blue', water),
    ('Poison', 'poison', 'poison', poison), ('Bio', 'bio', 'dark', bio), ('Blaze Spikes', 'blaze_spikes', 'fire', blaze_spikes),
    ('Blind', 'blind', 'dark', blind), ('Bind', 'bind', 'violet', bind), ('*Trust', 'trust', 'gold', trust),
    ('Provoke', 'provoke', 'red', provoke), ('Mighty Strikes', 'mighty_strikes', 'gold', mighty_strikes),
    ('Hundred Fists', 'hundred_fists', 'red', hundred_fists), ('Boost', 'boost', 'gold', boost),
    ('Benediction', 'benediction', 'holy', benediction), ('Manafont', 'manafont', 'blue', manafont),
    ('Chainspell', 'chainspell', 'violet', chainspell), ('Perfect Dodge', 'perfect_dodge', 'teal', perfect_dodge),
    ('Steal', 'steal', 'gold', steal),
    ('Fast Blade', 'fast_blade', 'teal', fast_blade), ('Wasp Sting', 'wasp_sting', 'poison', wasp_sting),
    ('Combo', 'combo', 'gold', combo), ('Raging Axe', 'raging_axe', 'red', raging_axe),
    ('Shining Strike', 'shining_strike', 'light', shining_strike), ('Heavy Swing', 'heavy_swing', 'gold', heavy_swing),
    ('Hard Slash', 'hard_slash', 'teal', hard_slash), ('Slice', 'slice', 'dark', slice_),
    ('Double Thrust', 'double_thrust', 'teal', double_thrust), ('Flaming Arrow', 'flaming_arrow', 'fire', flaming_arrow),
    ('Hot Shot', 'hot_shot', 'fire', hot_shot),
    ('Attack', 'attack', 'red', attack), ('Disengage', 'disengage', 'red', disengage), ('Check', 'check', 'blue', check),
    ('Heal', 'heal', 'green', heal), ('Ranged Attack', 'ranged_attack', 'gold', ranged_attack),
    ('Assist', 'assist', 'teal', assist),
]

def all_icons():
    """[(name, slug, accent, fn, generic)]: the hand-drawn icons, then every family from tools/data/actions.tsv."""
    import icon_families as F
    out = [(name, slug, accent, fn, False, None) for name, slug, accent, fn in ICONS]
    hand = {name: (slug, accent, fn) for name, slug, accent, fn in ICONS}
    path = os.path.join(os.path.dirname(__file__), 'data', 'actions.tsv')
    with open(path, encoding='latin-1') as f:
        rows = [line.rstrip('\n').split('\t') for line in f]
    # each entry's kind: 'ma' (spells), 'ja' (abilities and weapon skills) or 'cmd' (commands and *Trust); a spell
    # and a pet's move can share a name
    kind = {}
    for r in rows:
        kind.setdefault(r[2], 'ma' if r[0] == 'spell' else 'ja')
    out = [(n, sl, ac, fn, g, kind.get(n, 'ma' if n == '*Trust' else 'cmd')) for n, sl, ac, fn, g, _ in out]
    out += [e + ('ma',) for e in F.families(rows, hand)]
    out += [e + ('ja',) for e in F.ability_families(rows, hand)]
    return out


if __name__ == '__main__':
    A.manifest.clear()
    icons = all_icons()
    drawn = {}                      # slug -> (accent, fn): one texture per emblem, however many actions use it
    for name, slug, accent, fn, _, _ in icons:
        if slug not in drawn:
            drawn[slug] = (accent, fn)
    for slug, (accent, fn) in drawn.items():
        A.save('ai_' + slug, make(fn, accent))
    with open(os.path.join(A.ROOT, 'action_icons_manifest.lua'), 'w') as f:
        f.write('-- Generated by tools/make_action_icons.py: content size of each action icon texture.\nreturn {\n')
        for slug in drawn:
            f.write("    ['ai_%s'] = { %d, %d },\n" % (slug, S, S))
        f.write('};\n')
    with open(os.path.join(A.ROOT, '..', 'core', 'action_icons.lua'), 'w') as f:
        f.write('-- Generated by tools/make_action_icons.py: action name -> icon texture (ai_<slug>). "*Trust" covers every\n'
                '-- Trust spell. Textures named ai_gen_* are a category\'s emblem (the bar keeps the letters over it).\n'
                '-- By kind: ma = spells, ja = abilities and weapon skills, cmd = commands (a spell and a pet\'s move can\n'
                '-- share a name).\n'
                'return {\n')
        for k in ('ma', 'ja', 'cmd'):
            f.write('    %s = {\n' % k)
            for name, slug, _, _, _, kk in icons:
                if kk == k:
                    f.write("        [%s] = 'ai_%s',\n" % (lua_str(name), slug))
            f.write('    },\n')
        f.write('};\n')
    # a contact sheet for checking them by eye
    cols = 16
    slugs = list(drawn)
    rows = (len(slugs) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * 56, rows * 56), (40, 44, 60, 255))
    for k, slug in enumerate(slugs):
        im = Image.open(os.path.join(A.ROOT, 'ai_%s.png' % slug)).crop((0, 0, S, S))
        x, y = (k % cols) * 56 + 6, (k // cols) * 56 + 6
        ImageDraw.Draw(sheet).ellipse([x, y, x + S, y + S], fill=(70, 74, 96, 255))
        sheet.paste(im, (x, y), im)
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.LANCZOS)
    sheet.save(os.path.join(os.path.dirname(__file__), '..', 'dev', 'shots', 'action_icons_sheet.png'))
    print('wrote', len(drawn), 'action icons for', len(icons), 'actions')
