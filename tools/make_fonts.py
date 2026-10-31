"""Build the bundled fonts from Alegreya (SIL OFL 1.1, see addons/xiv1ui/fonts/OFL.txt).

Alegreya replaced Cormorant Garamond (Oct 2026): Cormorant's hairline strokes and small x-height were hard to read
on a TV; Alegreya keeps a calligraphic, near-cursive feel with much sturdier strokes.

The upstream files are variable fonts, which GDI handles poorly, so this cuts fixed weights and renames them into two
simple families GDI+ can find reliably:
    'XIV1UI Serif'       Regular + Italic  (weight 600)
    'XIV1UI Serif Bold'  is cut at weight 750
    'XIV1UI Serif Bold'  bold italic glyphs, declared as the family's Regular style (GDI+ refuses a family that
                         has no Regular face) -> use with no style flags
    'XIV1UI Serif JP'    Noto Serif JP (SIL OFL 1.1, see fonts/OFL-NotoSerifJP.txt) for Japanese text, cut down to
                         the characters Shift-JIS can encode (all FFXI can show) to keep the download small
Run: nix-shell --run 'python3 tools/make_fonts.py <Alegreya[wght].ttf> <Alegreya-Italic[wght].ttf>
                      <NotoSerifJP[wght].ttf>'
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib import instancer

OUT = os.path.join(os.path.dirname(__file__), '..', 'addons', 'xiv1ui', 'fonts')


def sjis_chars():
    """Every character the Shift-JIS (cp932) code page can encode."""
    out = set(range(0x20, 0x7F))
    for lead in list(range(0x81, 0xA0)) + list(range(0xE0, 0xFD)):
        for trail in range(0x40, 0xFD):
            try:
                out.add(ord(bytes([lead, trail]).decode('cp932')))
            except UnicodeDecodeError:
                pass
    for b in range(0xA1, 0xE0):
        out.add(ord(bytes([b]).decode('cp932')))
    return sorted(out)


def build(src, weight, family, style, italic, out, chars=None):
    font = instancer.instantiateVariableFont(TTFont(src), {'wght': weight}, updateFontNames=False)
    if chars:
        sub = subset.Subsetter(subset.Options(layout_features=['*'], name_IDs=['*'], name_languages=['*'],
                                              notdef_outline=True, glyph_names=False))
        sub.populate(unicodes=chars)
        sub.subset(font)
    name = font['name']
    full = family if style == 'Regular' else f'{family} {style}'
    ps = (family + '-' + style).replace(' ', '')
    for rec in list(name.names):
        if rec.nameID in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
            name.removeNames(nameID=rec.nameID)
    for nid, val in ((1, family), (2, style), (3, ps), (4, full), (6, ps)):
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    os2 = font['OS/2']
    os2.usWeightClass = 400 if 'Bold' not in family else 700
    os2.fsSelection = (os2.fsSelection & ~0b1100001) | (0b1 if italic else 0b1000000)
    font['head'].macStyle = 0b10 if italic else 0
    # Lining, tabular digits: GDI can't turn on OpenType features, and the default old-style figures (a small
    # '0', descending '3') look wrong for HUD numerals. Point the cmap at the '.tf' glyphs instead.
    digits = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    order = set(font.getGlyphOrder())
    for table in font['cmap'].tables:
        for i, n in enumerate(digits):
            if ord('0') + i in table.cmap and n + '.tf' in order:
                table.cmap[ord('0') + i] = n + '.tf'
    font.save(os.path.join(OUT, out))


if __name__ == '__main__':
    upright, italic, jp = sys.argv[1], sys.argv[2], sys.argv[3]
    for f in os.listdir(OUT):
        if f.endswith('.ttf'):
            os.remove(os.path.join(OUT, f))
    build(upright, 600, 'XIV1UI Serif', 'Regular', False, 'XIV1UI-Serif-Regular.ttf')
    build(italic, 600, 'XIV1UI Serif', 'Italic', True, 'XIV1UI-Serif-Italic.ttf')
    build(italic, 750, 'XIV1UI Serif Bold', 'Regular', False, 'XIV1UI-SerifBold.ttf')
    build(jp, 600, 'XIV1UI Serif JP', 'Regular', False, 'XIV1UI-SerifJP.ttf', chars=sjis_chars())
    print('fonts written to', os.path.normpath(OUT))
