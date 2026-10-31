"""Action icon families: which emblem every spell (and, below, every ability and weapon skill) gets.

An emblem is a frame (a Bar- shield, a song's note, an Indi- ring ...) holding a symbol from tools/icon_symbols.py,
in an accent colour. Tiers share their family's emblem (Cure II-VI, Utsusemi: Ni ...); the action bar draws the
tier itself. Actions no rule names get their category's emblem and keep their letters on the bar (generic = True).

families(rows) -> list of (name, slug, accent, drawing, generic); rows are tools/data/actions.tsv's.
"""
import math
import re

import icon_symbols as Y

P, L, at = Y.P, Y.L, Y.at

TIER = re.compile(r"(?:\s+(?:II|III|IV|V|VI|VII|VIII|IX|X)|:\s*(?:Ichi|Ni|San))$")


def family_name(name):
    return TIER.sub('', name)


# ---- frames -------------------------------------------------------------------------------------------------------
def dots(a):
    """The area mark: three dots above the emblem (-ra, -ga)."""
    for x in (0.34, 0.50, 0.66):
        a.ellipse(P([(x - 0.045, 0.05), (x + 0.045, 0.14)]), fill=255)


def solo(sym, area=False, big=0.36):
    def f(i, a):
        Y.STATUSES[sym](a, 0.5, 0.55 if area else 0.5, big)
        if area:
            dots(i)
    return f


def solo_ink(sym, accent_sym=None, area=False):
    def f(i, a):
        Y.STATUSES[sym](i, 0.48, 0.54, 0.34)
        if accent_sym:
            Y.STATUSES[accent_sym](a, 0.76, 0.24, 0.15)
        if area:
            dots(a)
    return f


def bar(sym, area=False):
    def f(i, a):
        Y.shield(i, 0.5, 0.52, 0.40)
        Y.STATUSES[sym](a, 0.5, 0.46, 0.16)
        if area:
            dots(a)
    return f


def na(sym):
    def f(i, a):
        Y.STATUSES[sym](a, 0.40, 0.58, 0.27)
        i.rectangle(P([(0.66, 0.16), (0.74, 0.44)]), fill=255)
        i.rectangle(P([(0.56, 0.26), (0.84, 0.34)]), fill=255)
    return f


def en(elem):
    def f(i, a):
        Y.sword(i, 0.40, 0.56, 0.38)
        Y.ELEMENTS[elem](a, 0.70, 0.30, 0.20)
    return f


def spikes(elem):
    def f(i, a):
        for k in range(8):
            t = k * math.pi / 4
            i.polygon(P([(0.5 + 0.42 * math.cos(t), 0.5 + 0.42 * math.sin(t)),
                         (0.5 + 0.24 * math.cos(t + 0.3), 0.5 + 0.24 * math.sin(t + 0.3)),
                         (0.5 + 0.24 * math.cos(t - 0.3), 0.5 + 0.24 * math.sin(t - 0.3))]), fill=255)
        Y.ELEMENTS[elem](a, 0.5, 0.5, 0.17)
    return f


def storm(elem):
    def f(i, a):
        for cx, cy, r in ((0.36, 0.34, 0.15), (0.56, 0.28, 0.19), (0.72, 0.38, 0.13)):
            i.ellipse(P([(cx - r, cy - r), (cx + r, cy + r)]), fill=255)
        i.rectangle(P([(0.24, 0.36), (0.84, 0.50)]), fill=255)
        Y.ELEMENTS[elem](a, 0.5, 0.72, 0.17)
    return f


def helix(elem):
    def f(i, a):
        for k in range(3):
            i.arc(P([(0.16 + k * 0.06, 0.16 + k * 0.06), (0.84 - k * 0.06, 0.84 - k * 0.06)]), 200 + k * 50,
                  420 + k * 50, fill=255, width=L(0.04))
        Y.ELEMENTS[elem](a, 0.5, 0.5, 0.16)
    return f


def nuke(elem, kind=''):
    def f(i, a):
        if kind == 'ancient':
            Y.burst(a, 0.5, 0.5, 0.44)
            Y.ELEMENTS[elem](i, 0.5, 0.52, 0.27)
            return
        Y.ELEMENTS[elem](i, 0.5, 0.56 if kind else 0.52, 0.34)
        if kind == 'ga':
            dots(a)
        elif kind == 'ja':
            dots(a)
            a.arc(P([(0.10, 0.62), (0.90, 1.00)]), 20, 160, fill=255, width=L(0.05))
        elif kind == 'ra':
            a.arc(P([(0.06, 0.12), (0.94, 1.00)]), 200, 340, fill=255, width=L(0.05))
        elif kind == 'dot':
            Y.arrow_down(a, 0.78, 0.26, 0.14)
    return f


def stat_frame(stat, kind):
    def f(i, a):
        Y.text(i, 0.56, 0.58, 0.24, stat)
        if kind == 'absorb':
            Y.drain(a, 0.30, 0.28, 0.17)
        else:
            Y.arrow_up(a, 0.26, 0.30, 0.16)
            if kind == 'boost':
                dots(a)
    return f


def summon(elem):
    def f(i, a):
        Y.ring(i, 0.5, 0.5, 0.40, 0.10)
        for k in range(4):
            t = k * math.pi / 2 + math.pi / 4
            i.ellipse(P([(0.5 + 0.40 * math.cos(t) - 0.05, 0.5 + 0.40 * math.sin(t) - 0.05),
                         (0.5 + 0.40 * math.cos(t) + 0.05, 0.5 + 0.40 * math.sin(t) + 0.05)]), fill=255)
        Y.ELEMENTS[elem](a, 0.5, 0.5, 0.22)
    return f


def spirit(elem):
    def f(i, a):
        Y.orb(i, 0.5, 0.5, 0.40)
        i.ellipse(P([(0.30, 0.30), (0.70, 0.70)]), fill=0)
        Y.ELEMENTS[elem](a, 0.5, 0.5, 0.17)
    return f


def scroll(sym):
    def f(i, a):
        i.rectangle(P([(0.22, 0.20), (0.78, 0.80)]), fill=255)
        i.ellipse(P([(0.14, 0.12), (0.30, 0.28)]), fill=255)
        i.ellipse(P([(0.70, 0.72), (0.86, 0.88)]), fill=255)
        i.rectangle(P([(0.28, 0.26), (0.72, 0.74)]), fill=0)
        Y.STATUSES[sym](a, 0.5, 0.5, 0.19)
    return f


def song(sym, down=False):
    def f(i, a):
        # a quaver on the left, the song's effect on the right
        i.ellipse(P([(0.10, 0.62), (0.32, 0.80)]), fill=255)
        i.rectangle(P([(0.27, 0.18), (0.32, 0.72)]), fill=255)
        i.polygon(P([(0.32, 0.18), (0.46, 0.30), (0.46, 0.40), (0.32, 0.30)]), fill=255)
        Y.STATUSES[sym](a, 0.66, 0.50, 0.24)
        if down:
            Y.arrow_down(i, 0.84, 0.22, 0.10)
    return f


def indi(sym, down=False):
    def f(i, a):
        Y.ring(i, 0.5, 0.5, 0.42, 0.08)
        i.arc(P([(0.16, 0.16), (0.84, 0.84)]), 0, 360, fill=255, width=L(0.025))
        Y.STATUSES[sym](a, 0.5, 0.5, 0.22)
        if down:
            Y.arrow_down(i, 0.80, 0.80, 0.10)
    return f


def geo(sym, down=False):
    def f(i, a):
        # the luopan: a dish on a pole
        i.rectangle(P([(0.47, 0.50), (0.53, 0.92)]), fill=255)
        i.chord(P([(0.22, 0.30), (0.78, 0.66)]), 0, 180, fill=255)
        Y.STATUSES[sym](a, 0.5, 0.30, 0.20)
        if down:
            Y.arrow_down(i, 0.80, 0.74, 0.10)
    return f


def two(sym1, sym2):
    """Two symbols: the main one in ink, a smaller one in the accent colour."""
    def f(i, a):
        Y.STATUSES[sym1](i, 0.44, 0.56, 0.32)
        Y.STATUSES[sym2](a, 0.76, 0.24, 0.17)
    return f


def generic(kind):
    """The category emblem for actions without one of their own (the bar keeps their letters over it)."""
    def f(i, a):
        sym = {'blue': 'eye', 'trust': 'figure', 'ws': 'sword', 'ja': 'burst', 'pet': 'heart', 'bp': 'crystal',
               'ready': 'heart', 'song': 'sparkles', 'nin': 'portal', 'white': 'sparkles', 'black': 'orb',
               'geo': 'orb', 'smn': 'crystal'}.get(kind, 'orb')
        Y.STATUSES[sym](i, 0.5, 0.5, 0.38)
    return f


# ---- spells -------------------------------------------------------------------------------------------------------
ELEM = {'Fire': 'fire', 'Blizzard': 'ice', 'Aero': 'wind', 'Stone': 'earth', 'Thunder': 'thunder',
        'Water': 'water'}
ELEM_GA = {'Firaga': 'fire', 'Blizzaga': 'ice', 'Aeroga': 'wind', 'Stonega': 'earth', 'Thundaga': 'thunder',
           'Waterga': 'water'}
ELEM_JA = {'Firaja': 'fire', 'Blizzaja': 'ice', 'Aeroja': 'wind', 'Stoneja': 'earth', 'Thundaja': 'thunder',
           'Waterja': 'water'}
ELEM_RA = {'Fira': 'fire', 'Blizzara': 'ice', 'Aera': 'wind', 'Stonera': 'earth', 'Thundara': 'thunder',
           'Watera': 'water'}
ANCIENT = {'Flare': 'fire', 'Freeze': 'ice', 'Tornado': 'wind', 'Quake': 'earth', 'Burst': 'thunder',
           'Flood': 'water'}
DOTS = {'Burn': 'fire', 'Frost': 'ice', 'Choke': 'wind', 'Rasp': 'earth', 'Shock': 'thunder', 'Drown': 'water'}
BAR_ELEM = {'fire': 'fire', 'blizzard': 'ice', 'aero': 'wind', 'stone': 'earth', 'thunder': 'thunder',
            'water': 'water', 'fira': 'fire', 'blizzara': 'ice', 'aera': 'wind', 'stonra': 'earth',
            'thundra': 'thunder', 'watera': 'water'}
BAR_STATUS = {'sleep': 'sleep', 'poison': 'poison', 'paralyze': 'paralyze', 'blind': 'blind', 'silence': 'silence',
              'petrify': 'petrify', 'virus': 'virus', 'amnesia': 'amnesia', 'sleepra': 'sleep',
              'poisonra': 'poison', 'paralyzra': 'paralyze', 'blindra': 'blind', 'silencera': 'silence',
              'petra': 'petrify', 'vira': 'virus', 'amnesra': 'amnesia'}
EN = {'Enfire': 'fire', 'Enblizzard': 'ice', 'Enaero': 'wind', 'Enstone': 'earth', 'Enthunder': 'thunder',
      'Enwater': 'water', 'Enlight': 'light', 'Endark': 'dark'}
SPIKES = {'Blaze Spikes': 'fire', 'Ice Spikes': 'ice', 'Shock Spikes': 'thunder', 'Dread Spikes': 'dark'}
STORMS = {'Firestorm': 'fire', 'Hailstorm': 'ice', 'Windstorm': 'wind', 'Sandstorm': 'earth',
          'Thunderstorm': 'thunder', 'Rainstorm': 'water', 'Aurorastorm': 'light', 'Voidstorm': 'dark'}
HELIX = {'Pyrohelix': 'fire', 'Cryohelix': 'ice', 'Anemohelix': 'wind', 'Geohelix': 'earth', 'Ionohelix': 'thunder',
         'Hydrohelix': 'water', 'Luminohelix': 'light', 'Noctohelix': 'dark'}
SPIRITS = {'Fire Spirit': 'fire', 'Ice Spirit': 'ice', 'Air Spirit': 'wind', 'Earth Spirit': 'earth',
           'Thunder Spirit': 'thunder', 'Water Spirit': 'water', 'Light Spirit': 'light', 'Dark Spirit': 'dark'}
AVATARS = {'Carbuncle': 'light', 'Fenrir': 'dark', 'Ifrit': 'fire', 'Titan': 'earth', 'Leviathan': 'water',
           'Garuda': 'wind', 'Shiva': 'ice', 'Ramuh': 'thunder', 'Diabolos': 'dark', 'Odin': 'dark',
           'Alexander': 'light', 'Cait Sith': 'light', 'Siren': 'wind', 'Atomos': 'dark'}
NINJUTSU = {'Katon': 'fire', 'Hyoton': 'ice', 'Huton': 'wind', 'Doton': 'earth', 'Raiton': 'thunder',
            'Suiton': 'water', 'Utsusemi': 'blink', 'Jubaku': 'paralyze', 'Hojo': 'slow', 'Kurayami': 'blind',
            'Dokumori': 'poison', 'Tonko': 'evasion', 'Monomi': 'footprints', 'Aisha': 'sword', 'Gekka': 'heart',
            'Yain': 'heart', 'Myoshu': 'target', 'Yurin': 'tp', 'Kakka': 'tp', 'Migawari': 'figure'}
STATS = ('STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR')

# one-off spells: name -> (accent, drawing)
SPELLS = {
    'Cure': ('green', solo_ink('regen', 'sparkles')),
    'Curaga': ('green', solo_ink('regen', None, area=True)),
    'Cura': ('green', two('regen', 'burst')),
    'Full Cure': ('green', two('regen', 'sparkles')),
    'Raise': ('holy', two('figure', 'wings')), 'Arise': ('holy', two('figure', 'sparkles')),
    'Reraise': ('holy', two('figure', 'crystal')),
    'Blindna': ('holy', na('blind')), 'Silena': ('holy', na('silence')), 'Stona': ('earth', na('petrify')),
    'Viruna': ('poison', na('virus')), 'Cursna': ('dark', na('curse')), 'Erase': ('holy', na('dispel')),
    'Esuna': ('holy', na('sparkles')), 'Sacrifice': ('red', na('heart')),
    'Holy': ('holy', nuke('light', 'ancient')), 'Diaga': ('light', None), 'Banishga': ('holy', None),
    'Shell': ('teal', solo('shell')), 'Shellra': ('teal', solo('shell', area=True)),
    'Blink': ('violet', solo('blink')), 'Stoneskin': ('earth', solo('stoneskin')),
    'Slow': ('earth', solo('slow')), 'Slowga': ('earth', solo('slow', area=True)),
    'Haste': ('wind', solo('haste')), 'Hastega': ('wind', solo('haste', area=True)),
    'Silence': ('wind', solo('silence')), 'Silencega': ('wind', solo('silence', area=True)),
    'Paralyga': ('gold', solo('paralyze', area=True)),
    'Auspice': ('holy', two('sword', 'light')), 'Reprisal': ('gold', two('shield', 'burst')),
    'Repose': ('holy', solo('sleep')), 'Phalanx': ('gold', None),
    'Regen': ('green', solo('regen')), 'Refresh': ('blue', solo('refresh')), 'Flash': ('holy', solo('burst')),
    'Protectra': ('gold', None), 'Invisible': ('violet', solo('figure')), 'Sneak': ('violet', solo('footprints')),
    'Deodorize': ('green', solo('flower')), 'Addle': ('violet', two('slow', 'orb')),
    'Animus Augeo': ('red', two('heart', 'up')), 'Animus Minuo': ('blue', two('heart', 'down')),
    'Crusade': ('red', two('heart', 'shield')), 'Embrava': ('gold', two('sparkles', 'haste')),
    'Temper': ('red', two('sword', 'haste')), 'Adloquium': ('gold', two('tp', 'up')),
    'Foil': ('teal', two('evasion', 'shield')), 'Flurry': ('wind', two('target', 'haste')),
    'Inundation': ('blue', two('water', 'down')),
    'Gravity': ('violet', solo('gravity')), 'Graviga': ('violet', solo('gravity', area=True)),
    'Meteor': ('fire', nuke('earth', 'ancient')), 'Comet': ('dark', nuke('dark', 'ancient')),
    'Poisonga': ('poison', None), 'Retrace': ('blue', two('portal', 'up')),
    'Absorb-ACC': ('dark', stat_frame('ACC', 'absorb')), 'Absorb-Attri': ('dark', stat_frame('ALL', 'absorb')),
    'Absorb-TP': ('dark', stat_frame('TP', 'absorb')),
    'Drain': ('dark', solo('drain')), 'Aspir': ('dark', solo('aspir')), 'Stun': ('violet', solo('stun')),
    'Sleep': ('violet', solo('sleep')), 'Sleepga': ('violet', solo('sleep', area=True)),
    'Blindga': ('dark', solo('blind', area=True)), 'Break': ('earth', solo('petrify')),
    'Breakga': ('earth', solo('petrify', area=True)), 'Virus': ('poison', solo('virus')),
    'Curse': ('dark', solo('curse')), 'Bindga': ('violet', solo('bind', area=True)),
    'Dispel': ('violet', solo('dispel')), 'Dispelga': ('violet', solo('dispel', area=True)),
    'Warp': ('violet', solo('portal')), 'Escape': ('violet', two('portal', 'footprints')),
    'Tractor': ('violet', two('figure', 'up')), 'Klimaform': ('teal', two('orb', 'wind')),
    'Death': ('dark', solo('curse', big=0.40)), 'Impact': ('dark', nuke('dark', 'ancient')),
    'Kaustra': ('dark', two('dark', 'burst')), 'Distract': ('wind', two('evasion', 'down')),
    'Frazzle': ('violet', two('sparkles', 'down')),
}
# Teleports and Recalls: a crystal and a portal
for _n in ('Teleport-Yhoat', 'Teleport-Altep', 'Teleport-Holla', 'Teleport-Dem', 'Teleport-Mea', 'Teleport-Vahzl',
           'Recall-Jugner', 'Recall-Pashh', 'Recall-Meriph'):
    SPELLS[_n] = ('teal', two('crystal', 'portal'))

SONGS = {
    'Requiem': ('dark', 'curse', False), 'Lullaby': ('violet', 'sleep', False), 'Paeon': ('green', 'regen', False),
    'Ballad': ('blue', 'refresh', False), 'Minne': ('gold', 'shield', False), 'Minuet': ('red', 'sword', False),
    'Madrigal': ('red', 'target', False), 'Prelude': ('gold', 'eye', False), 'Mambo': ('teal', 'evasion', False),
    'Aubade': ('holy', 'sleep', False), 'Pastoral': ('holy', 'poison', False), 'Hum': ('gold', 'footprints', False),
    'Fantasia': ('holy', 'blind', False), 'Operetta': ('holy', 'silence', False),
    'Capriccio': ('holy', 'petrify', False), 'Serenade': ('holy', 'heart', False), 'Round': ('holy', 'curse', False),
    'Gavotte': ('holy', 'bind', False), 'Fugue': ('holy', 'shield', False), 'March': ('wind', 'haste', False),
    'Passion': ('red', 'heart', False), 'Elegy': ('earth', 'slow', False), 'Finale': ('violet', 'dispel', False),
    'Hymnus': ('holy', 'wings', False), 'Mazurka': ('gold', 'footprints', False), 'Virelai': ('red', 'heart', False),
    'Sirvente': ('red', 'up', False), 'Dirge': ('blue', 'down', False), 'Scherzo': ('gold', 'shield', False),
    'Nocturne': ('dark', 'slow', False),
}
ETUDE = {'Sinewy': 'STR', 'Herculean': 'STR', 'Dextrous': 'DEX', 'Uncanny': 'DEX', 'Vivacious': 'VIT',
         'Vital': 'VIT', 'Quick': 'AGI', 'Swift': 'AGI', 'Learned': 'INT', 'Sage': 'INT', 'Spirited': 'MND',
         'Logical': 'MND', 'Enchanting': 'CHR', 'Bewitching': 'CHR'}
SONG_ELEM = {'Fire': 'fire', 'Ice': 'ice', 'Wind': 'wind', 'Earth': 'earth', 'Lightning': 'thunder',
             'Ltng.': 'thunder', 'Water': 'water', 'Light': 'light', 'Dark': 'dark'}
GEO_EFFECT = {'Regen': ('green', 'regen', False), 'Poison': ('poison', 'poison', True),
              'Refresh': ('blue', 'refresh', False), 'Haste': ('wind', 'haste', False),
              'Fury': ('red', 'sword', False), 'Barrier': ('gold', 'shield', False), 'Acumen': ('violet', 'orb', False),
              'Fend': ('teal', 'shell', False), 'Precision': ('gold', 'target', False),
              'Voidance': ('teal', 'evasion', False), 'Focus': ('violet', 'eye', False),
              'Attunement': ('teal', 'sparkles', False), 'Wilt': ('dark', 'sword', True),
              'Frailty': ('dark', 'shield', True), 'Fade': ('dark', 'orb', True), 'Malaise': ('dark', 'shell', True),
              'Slip': ('dark', 'target', True), 'Torpor': ('dark', 'evasion', True), 'Vex': ('dark', 'eye', True),
              'Languor': ('dark', 'sparkles', True), 'Slow': ('earth', 'slow', True),
              'Paralysis': ('gold', 'paralyze', True), 'Gravity': ('violet', 'gravity', True)}
SPELL_KIND = {'1': 'white', '2': 'black', '3': 'smn', '4': 'nin', '5': 'song', '6': 'blue', '7': 'geo',
              '8': 'trust'}


def spell_icon(fam, typ):
    """(accent, drawing) for a spell family, or None. A None drawing means 'the hand-drawn family icon + area'."""
    if fam in SPELLS:
        return SPELLS[fam]
    if fam in ELEM:
        return Y.ELEMENT_ACCENT[ELEM[fam]], nuke(ELEM[fam])
    for table, kind in ((ELEM_GA, 'ga'), (ELEM_JA, 'ja'), (ELEM_RA, 'ra'), (ANCIENT, 'ancient'), (DOTS, 'dot')):
        if fam in table:
            return Y.ELEMENT_ACCENT[table[fam]], nuke(table[fam], kind)
    m = re.match(r'^Bar(.+)$', fam)
    if m:
        k = m.group(1).lower()
        area = k.endswith('ra') or k in ('fira', 'blizzara', 'aera', 'stonra', 'thundra', 'watera', 'petra', 'vira')
        if k in BAR_ELEM:
            e = BAR_ELEM[k]
            return Y.ELEMENT_ACCENT[e], bar(e, area)
        if k in BAR_STATUS:
            return 'holy', bar(BAR_STATUS[k], area)
    if fam in EN:
        return Y.ELEMENT_ACCENT[EN[fam]], en(EN[fam])
    if fam in SPIKES:
        return Y.ELEMENT_ACCENT[SPIKES[fam]], spikes(SPIKES[fam])
    if fam in STORMS:
        return Y.ELEMENT_ACCENT[STORMS[fam]], storm(STORMS[fam])
    if fam in HELIX:
        return Y.ELEMENT_ACCENT[HELIX[fam]], helix(HELIX[fam])
    if fam in SPIRITS:
        return Y.ELEMENT_ACCENT[SPIRITS[fam]], spirit(SPIRITS[fam])
    if fam in AVATARS:
        return Y.ELEMENT_ACCENT[AVATARS[fam]], summon(AVATARS[fam])
    if fam in NINJUTSU:
        s = NINJUTSU[fam]
        return (Y.ELEMENT_ACCENT.get(s, 'teal'), scroll(s))
    m = re.match(r'^(Boost|Gain|Absorb)-(\w+)$', fam)
    if m and m.group(2) in STATS:
        return ('dark' if m.group(1) == 'Absorb' else 'gold'), stat_frame(m.group(2), m.group(1).lower())
    m = re.match(r'^(Indi|Geo)-(\w+)$', fam)
    if m:
        eff = m.group(2)
        frame = indi if m.group(1) == 'Indi' else geo
        if eff in STATS:
            return 'gold', frame(eff)
        if eff in GEO_EFFECT:
            acc, sym, down = GEO_EFFECT[eff]
            return acc, frame(sym, down)
    if typ == '5':
        words = fam.split()
        if words[-1] == 'Etude' and words[0] in ETUDE:
            return 'gold', song(ETUDE[words[0]])
        if words[-1] in ('Carol', 'Threnody') and words[0] in SONG_ELEM:
            e = SONG_ELEM[words[0]]
            return Y.ELEMENT_ACCENT[e], song(e, words[-1] == 'Threnody')
        for w in reversed(words):
            if w in SONGS:
                acc, sym, down = SONGS[w]
                return acc, song(sym, down)
    return None


# Spells sit on a disc of their element's colour: an accent of the same hue would vanish into it
DISC_CLASH = {'0': ('red', 'fire'), '1': ('blue',), '2': ('green', 'wind', 'poison', 'teal'), '3': ('gold', 'earth'),
              '4': ('violet', 'dark'), '5': ('blue', 'teal'), '6': ('holy', 'light', 'grey'), '7': ('dark', 'violet')}


def readable(accent, element):
    if accent in DISC_CLASH.get(element, ()):
        return 'gold' if element in ('6',) else 'holy'
    return accent


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


def families(rows, hand):
    """hand: {name: (slug, accent, fn)} of the hand-drawn icons (they win, and lend their drawing to -ga / -ra
    versions). Returns [(name, slug, accent, fn, generic)] for every spell in rows."""
    out = []
    made = {}
    for r in rows:
        if r[0] != 'spell':
            continue
        name, typ, element = r[2], r[3], r[4]
        if name in hand:
            continue
        fam = family_name(name)
        if fam in hand:
            slug, acc, fn = hand[fam]
            out.append((name, slug, acc, fn, False))
            continue
        got = blu_icon(name, element) if typ == '6' else spell_icon(fam, typ)
        if got is not None and got[1] is None:
            # an area version of a hand-drawn family (Diaga, Banishga, Protectra, Poisonga, Phalanx)
            base = {'Diaga': 'Dia', 'Banishga': 'Banish', 'Protectra': 'Protect', 'Poisonga': 'Poison',
                    'Phalanx': 'Protect'}[fam]
            bslug, bacc, bfn = hand[base]
            if fam == 'Phalanx':
                def fn(i, a, bfn=bfn):
                    for dx in (-0.16, 0.16):
                        Y.shield(a, 0.5 + dx, 0.58, 0.22)
                    Y.shield(i, 0.5, 0.46, 0.30)
            else:
                def fn(i, a, bfn=bfn):
                    bfn(i, a)
                    dots(a)
            got = (got[0], fn)
        if got is None:
            kind = SPELL_KIND.get(typ, 'black')
            slug = 'gen_' + kind
            if kind == 'trust':
                continue                      # (the hand-drawn *Trust icon covers them)
            out.append((name, slug, 'grey', generic(kind), True))
            continue
        acc = readable(got[0], element)
        # (the same family on another element's disc gets its own texture when its accent had to change)
        slug = slugify(fam) + ('' if acc == got[0] else '_' + acc)
        out.append((name, slug, acc, got[1], False))
    return out


# ---- abilities ----------------------------------------------------------------------------------------------------
def area(f):
    def g(i, a):
        f(i, a)
        dots(a)
    return g


def T(main, acc=None):
    return two(main, acc) if acc else solo_ink(main)


JA = {
    # WAR
    'Berserk': ('red', T('sword', 'up')), 'Warcry': ('red', area(T('sword', 'up'))),
    'Defender': ('gold', T('shield', 'up')), 'Aggressor': ('gold', T('target', 'up')),
    'Tomahawk': ('earth', T('w_axe', 'down')), "Warrior's Charge": ('red', T('burst', 'haste')),
    'Retaliation': ('red', T('shield', 'burst')), 'Restraint': ('red', T('fist', 'up')),
    'Blood Rage': ('red', area(T('heart', 'up'))), 'Brazen Rush': ('red', T('burst', 'up')),
    # MNK
    'Focus': ('gold', T('target', 'up')), 'Dodge': ('teal', T('evasion', 'up')),
    'Chakra': ('green', T('figure', 'regen')), 'Counterstance': ('gold', T('fist', 'shield')),
    'Chi Blast': ('holy', T('fist', 'burst')), 'Mantra': ('green', area(T('HP', 'up'))),
    'Formless Strikes': ('violet', T('fist', 'sparkles')), 'Footwork': ('gold', T('footprints', 'fist')),
    'Perfect Counter': ('gold', T('fist', 'burst')), 'Impetus': ('red', T('fist', 'haste')),
    'Inner Strength': ('red', T('HP', 'burst')),
    # WHM
    'Divine Seal': ('holy', T('regen', 'crystal')), 'Martyr': ('red', T('heart', 'down')),
    'Devotion': ('blue', T('heart', 'refresh')), 'Afflatus Solace': ('green', T('regen', 'heart')),
    'Afflatus Misery': ('dark', T('burst', 'heart')), 'Divine Caress': ('holy', T('regen', 'wings')),
    'Sacrosanctity': ('holy', area(T('shell', 'up'))),
    # BLM
    'Elemental Seal': ('violet', T('orb', 'crystal')), 'Mana Wall': ('blue', T('shell', 'MP')),
    'Enmity Douse': ('blue', T('heart', 'down')), 'Manawell': ('blue', T('MP', 'sparkles')),
    'Subtle Sorcery': ('violet', T('orb', 'down')), 'Cascade': ('violet', T('orb', 'tp')),
    # RDM
    'Convert': ('violet', T('HP', 'MP')), 'Composure': ('violet', T('figure', 'sparkles')),
    'Saboteur': ('dark', T('eye', 'down')), 'Spontaneity': ('violet', T('haste', 'orb')),
    'Stymie': ('violet', T('eye', 'up')),
    # THF
    'Flee': ('teal', T('footprints', 'haste')), 'Hide': ('violet', T('figure', 'evasion')),
    'Sneak Attack': ('red', T('w_dagger', 'burst')), 'Mug': ('gold', T('fist', 'orb')),
    'Trick Attack': ('teal', T('w_dagger', 'figure')), 'Accomplice': ('teal', T('figure', 'heart')),
    'Collaborator': ('teal', T('figure', 'heart')), "Assassin's Charge": ('red', T('w_dagger', 'haste')),
    'Feint': ('teal', T('evasion', 'down')), 'Despoil': ('gold', T('fist', 'down')),
    'Conspirator': ('teal', area(T('figure', 'up'))), 'Bully': ('red', T('fist', 'down')),
    'Larceny': ('gold', T('fist', 'dispel')),
    # PLD
    'Invincible': ('gold', T('shield', 'burst')), 'Shield Bash': ('gold', T('shield', 'stun')),
    'Holy Circle': ('holy', T('circle', 'curse')), 'Sentinel': ('gold', T('shield', 'heart')),
    'Cover': ('gold', T('figure', 'shield')), 'Rampart': ('gold', area(T('shield', 'shell'))),
    'Fealty': ('holy', T('shield', 'sparkles')), 'Chivalry': ('blue', T('tp', 'MP')),
    'Divine Emblem': ('holy', T('circle', 'light')), 'Sepulcher': ('holy', T('curse', 'down')),
    'Palisade': ('gold', T('shield', 'evasion')), 'Intervene': ('gold', T('shield', 'stun')),
    'Majesty': ('holy', T('regen', 'shield')),
    # DRK
    'Blood Weapon': ('dark', T('w_scythe', 'drain')), 'Souleater': ('dark', T('HP', 'sword')),
    'Arcane Circle': ('dark', T('circle', 'dark')), 'Last Resort': ('red', T('sword', 'down')),
    'Weapon Bash': ('dark', T('w_scythe', 'stun')), 'Dark Seal': ('dark', T('dark', 'crystal')),
    'Diabolic Eye': ('dark', T('eye', 'up')), 'Nether Void': ('dark', T('drain', 'up')),
    'Arcane Crest': ('dark', T('circle', 'down')), 'Scarlet Delirium': ('red', T('heart', 'burst')),
    'Soul Enslavement': ('dark', T('drain', 'tp')), 'Consume Mana': ('dark', T('MP', 'sword')),
    # BST
    'Familiar': ('gold', T('paw', 'up')), 'Charm': ('red', T('heart', 'paw')), 'Gauge': ('teal', T('paw', 'scales')),
    'Tame': ('teal', T('paw', 'heart')), 'Reward': ('green', T('paw', 'regen')), 'Call Beast': ('gold', T('paw', 'portal')),
    'Bestial Loyalty': ('gold', T('paw', 'portal')), 'Feral Howl': ('red', T('paw', 'burst')),
    'Killer Instinct': ('red', T('paw', 'sword')), 'Snarl': ('red', T('paw', 'heart')), 'Spur': ('red', T('paw', 'up')),
    'Run Wild': ('red', T('paw', 'haste')), 'Unleash': ('red', T('paw', 'burst')), 'Ready': ('gold', T('paw')),
    'Fight': ('red', T('paw', 'sword')), 'Heel': ('teal', T('paw', 'footprints')), 'Leave': ('grey', T('paw', 'down')),
    'Sic': ('red', T('paw', 'burst')), 'Stay': ('teal', T('paw', 'bind')),
    # BRD
    'Soul Voice': ('holy', song('up')), 'Nightingale': ('teal', song('haste')), 'Troubadour': ('teal', song('slow')),
    'Pianissimo': ('teal', song('figure')), 'Tenuto': ('teal', song('crystal')), 'Marcato': ('red', song('burst')),
    'Clarion Call': ('gold', song('sparkles')),
    # RNG
    'Eagle Eye Shot': ('gold', T('w_bow', 'burst')), 'Sharpshot': ('gold', T('w_bow', 'target')),
    'Barrage': ('gold', T('w_bow', 'haste')), 'Scavenge': ('gold', T('w_bow', 'down')),
    'Camouflage': ('green', T('figure', 'evasion')), 'Shadowbind': ('dark', T('w_bow', 'bind')),
    'Unlimited Shot': ('gold', T('w_bow', 'sparkles')), 'Stealth Shot': ('violet', T('w_bow', 'heart')),
    'Flashy Shot': ('gold', T('w_bow', 'light')), 'Velocity Shot': ('red', T('w_bow', 'haste')),
    'Double Shot': ('gold', T('w_bow', 'up')), 'Triple Shot': ('gold', T('w_gun', 'burst')),
    'Decoy Shot': ('gold', T('w_bow', 'figure')), 'Bounty Shot': ('gold', T('w_bow', 'orb')),
    'Hover Shot': ('gold', T('w_bow', 'wings')), 'Overkill': ('red', T('w_bow', 'burst')),
    # SAM
    'Meikyo Shisui': ('red', T('w_greatkatana', 'tp')), 'Warding Circle': ('holy', T('circle', 'shield')),
    'Third Eye': ('teal', T('eye')), 'Meditate': ('gold', T('tp', 'up')), 'Hasso': ('red', T('w_greatkatana', 'up')),
    'Seigan': ('gold', T('w_greatkatana', 'shield')), 'Shikikoyo': ('gold', T('tp', 'figure')),
    'Blade Bash': ('gold', T('w_greatkatana', 'stun')), 'Sekkanoki': ('red', T('tp', 'down')),
    'Sengikori': ('red', T('w_greatkatana', 'burst')), 'Konzen-ittai': ('red', T('burst', 'tp')),
    'Hamanoha': ('dark', T('w_greatkatana', 'down')), 'Hagakure': ('gold', T('tp', 'sparkles')),
    'Yaegasumi': ('teal', T('evasion', 'up')),
    # NIN
    'Mijin Gakure': ('red', T('burst', 'down')), 'Yonin': ('teal', T('evasion', 'heart')),
    'Innin': ('teal', T('figure', 'sword')), 'Sange': ('teal', T('w_katana', 'haste')),
    'Futae': ('teal', scroll('up')), 'Issekigan': ('teal', T('eye', 'shield')), 'Mikage': ('teal', T('blink', 'sword')),
    # DRG
    'Call Wyvern': ('teal', T('wyvern', 'portal')), 'Ancient Circle': ('teal', T('circle', 'wyvern')),
    'Jump': ('gold', T('jump')), 'High Jump': ('gold', T('jump', 'up')), 'Super Jump': ('gold', T('jump', 'heart')),
    'Spirit Link': ('green', T('wyvern', 'heart')), 'Deep Breathing': ('teal', T('wyvern', 'up')),
    'Angon': ('teal', T('w_polearm', 'down')), 'Spirit Jump': ('teal', T('jump', 'wyvern')),
    'Soul Jump': ('teal', T('jump', 'sparkles')), 'Dragon Breaker': ('dark', T('w_polearm', 'wyvern')),
    'Spirit Surge': ('gold', T('wyvern', 'burst')), 'Fly High': ('gold', T('jump', 'haste')),
    'Smiting Breath': ('red', T('wyvern', 'burst')), 'Restoring Breath': ('green', T('wyvern', 'regen')),
    'Steady Wing': ('gold', T('wyvern', 'shield')), 'Spirit Bond': ('green', T('wyvern', 'shield')),
    # SMN
    'Astral Flow': ('holy', T('crystal', 'burst')), 'Elemental Siphon': ('blue', T('crystal', 'MP')),
    'Mana Cede': ('blue', T('MP', 'crystal')), "Avatar's Favor": ('holy', T('crystal', 'sparkles')),
    'Astral Conduit': ('holy', T('crystal', 'haste')), 'Apogee': ('holy', T('crystal', 'up')),
    'Release': ('grey', T('crystal', 'down')), 'Assault': ('red', T('crystal', 'sword')),
    'Retreat': ('grey', T('crystal', 'footprints')), 'Blood Pact: Rage': ('red', T('crystal', 'burst')),
    'Blood Pact: Ward': ('green', T('crystal', 'shield')),
    # BLU
    'Azure Lore': ('blue', T('eye', 'burst')), 'Chain Affinity': ('blue', T('eye', 'sword')),
    'Burst Affinity': ('blue', T('eye', 'orb')), 'Diffusion': ('blue', area(T('eye', 'up'))),
    'Convergence': ('blue', T('eye', 'target')), 'Efflux': ('blue', T('eye', 'tp')),
    'Unbridled Learning': ('blue', T('eye', 'sparkles')), 'Unbridled Wisdom': ('blue', T('eye', 'light')),
    # COR
    'Wild Card': ('gold', T('card')), 'Phantom Roll': ('gold', T('die')), 'Double-Up': ('gold', T('die', 'up')),
    'Quick Draw': ('gold', T('w_gun')), 'Random Deal': ('gold', T('card', 'sparkles')),
    'Snake Eye': ('gold', T('die', 'eye')), 'Fold': ('gold', T('die', 'down')), 'Cutting Cards': ('gold', T('card', 'sword')),
    'Crooked Cards': ('gold', T('card', 'up')),
    # PUP
    'Overdrive': ('red', T('gear', 'burst')), 'Activate': ('teal', T('gear', 'up')), 'Repair': ('green', T('gear', 'regen')),
    'Role Reversal': ('teal', T('gear', 'figure')), 'Ventriloquy': ('teal', T('gear', 'heart')),
    'Cooldown': ('blue', T('gear', 'down')), 'Deus Ex Automata': ('teal', T('gear', 'sparkles')),
    'Maintenance': ('green', T('gear', 'sparkles')), 'Tactical Switch': ('teal', T('gear', 'tp')),
    'Heady Artifice': ('gold', T('gear', 'burst')), 'Deploy': ('red', T('gear', 'sword')),
    'Deactivate': ('grey', T('gear', 'down')), 'Retrieve': ('grey', T('gear', 'footprints')),
    # DNC
    'Trance': ('red', T('fan', 'sparkles')), 'Saber Dance': ('red', T('fan', 'sword')),
    'Fan Dance': ('teal', T('fan', 'shield')), 'No Foot Rise': ('gold', T('fan', 'up')),
    'Presto': ('teal', T('footprints', 'haste')), 'Grand Pas': ('gold', T('fan', 'burst')),
    'Contradance': ('green', T('fan', 'regen')),
    # SCH
    'Tabula Rasa': ('holy', T('book', 'sparkles')), 'Light Arts': ('holy', T('book', 'light')),
    'Dark Arts': ('dark', T('book', 'dark')), 'Modus Veritas': ('violet', T('book', 'eye')),
    'Stratagems': ('gold', T('book')), 'Sublimation': ('blue', T('book', 'MP')), 'Enlightenment': ('holy', T('book', 'up')),
    'Libra': ('teal', T('scales', 'eye')), 'Caper Emissarius': ('red', T('figure', 'heart')),
    # GEO
    'Full Circle': ('gold', T('circle', 'down')), 'Lasting Emanation': ('teal', T('circle', 'slow')),
    'Ecliptic Attrition': ('dark', T('circle', 'up')), 'Collimated Fervor': ('violet', T('orb', 'up')),
    'Life Cycle': ('green', T('HP', 'circle')), 'Blaze of Glory': ('fire', T('circle', 'burst')),
    'Dematerialize': ('violet', T('circle', 'shield')), 'Theurgic Focus': ('violet', T('orb', 'target')),
    'Concentric Pulse': ('violet', T('circle', 'burst')), 'Mending Halation': ('green', T('circle', 'regen')),
    'Radial Arcana': ('blue', T('circle', 'MP')), 'Entrust': ('gold', T('circle', 'figure')),
    'Bolster': ('gold', T('circle', 'up')), 'Widened Compass': ('gold', T('circle', 'haste')),
    # RUN
    'Elemental Sforzo': ('gold', T('rune', 'shield')), 'Rune Enchantment': ('gold', T('rune')),
    'Swordplay': ('red', T('sword', 'up')), 'Embolden': ('red', T('rune', 'up')),
    'One for All': ('gold', area(T('shell', 'up'))), 'Odyllic Subterfuge': ('violet', T('rune', 'down')),
    'Ward': ('gold', T('rune', 'shield')), 'Effusion': ('red', T('rune', 'burst')),
    'Vivacious Pulse': ('green', T('rune', 'regen')), 'Vallation': ('gold', T('rune', 'shield')),
    'Valiance': ('gold', area(T('rune', 'shield'))), 'Pflug': ('gold', T('rune', 'shell')),
    'Liement': ('dark', T('rune', 'drain')), 'Battuta': ('gold', T('rune', 'fist')),
    'Swipe': ('red', T('rune', 'burst')), 'Lunge': ('red', T('rune', 'haste')), 'Gambit': ('dark', T('rune', 'down')),
    'Rayke': ('dark', T('rune', 'shell')),
    # DNC: waltzes, sambas, steps, flourishes, jigs
    'Curing Waltz': ('green', T('fan', 'regen')), 'Healing Waltz': ('holy', T('fan', 'sparkles')),
    'Divine Waltz': ('green', area(T('fan', 'regen'))), 'Drain Samba': ('dark', T('fan', 'drain')),
    'Aspir Samba': ('dark', T('fan', 'aspir')), 'Haste Samba': ('wind', T('fan', 'haste')),
    'Quickstep': ('teal', T('footprints', 'evasion')), 'Box Step': ('teal', T('footprints', 'shield')),
    'Stutter Step': ('teal', T('footprints', 'eye')), 'Feather Step': ('teal', T('footprints', 'target')),
    'Animated Flourish': ('red', T('fan', 'heart')), 'Desperate Flourish': ('earth', T('fan', 'gravity')),
    'Violent Flourish': ('violet', T('fan', 'stun')), 'Reverse Flourish': ('gold', T('fan', 'tp')),
    'Building Flourish': ('red', T('fan', 'up')), 'Wild Flourish': ('red', T('fan', 'burst')),
    'Climactic Flourish': ('red', T('fan', 'target')), 'Striking Flourish': ('red', T('fan', 'sword')),
    'Ternary Flourish': ('red', T('fan', 'haste')), 'Spectral Jig': ('violet', T('footprints', 'figure')),
    'Chocobo Jig': ('gold', T('footprints', 'haste')),
    # SCH stratagems
    'Penury': ('holy', T('book', 'MP')), 'Celerity': ('holy', T('book', 'haste')), 'Rapture': ('holy', T('book', 'up')),
    'Accession': ('holy', area(T('book', 'regen'))), 'Parsimony': ('dark', T('book', 'MP')),
    'Alacrity': ('dark', T('book', 'haste')), 'Ebullience': ('dark', T('book', 'up')),
    'Manifestation': ('dark', area(T('book', 'orb'))), 'Addendum: White': ('holy', T('book', 'light')),
    'Addendum: Black': ('dark', T('book', 'dark')), 'Perpetuance': ('holy', T('book', 'slow')),
    'Immanence': ('dark', T('book', 'burst')), 'Focalization': ('dark', T('book', 'target')),
    'Equanimity': ('dark', T('book', 'heart')), 'Altruism': ('holy', T('book', 'heart')),
    'Tranquility': ('holy', T('book', 'down')),
    # menu entries and a few more
    'Sambas': ('dark', T('fan', 'drain')), 'Waltzes': ('green', T('fan', 'regen')),
    'Jigs': ('teal', T('footprints', 'evasion')), 'Steps': ('teal', T('footprints', 'down')),
    'Flourishes I': ('red', T('fan', 'burst')), 'Flourishes II': ('red', T('fan', 'tp')),
    'Flourishes III': ('red', T('fan', 'sword')), 'Pet commands': ('gold', T('paw')),
    'Dismiss': ('grey', T('wyvern', 'down')), 'Sanctuary': ('holy', area(T('shield', 'sparkles'))),
    'Relinquish': ('grey', T('rune', 'down')),
}
ROLL = {"Fighter's": 'sword', "Monk's": 'fist', "Healer's": 'regen', "Wizard's": 'orb', "Warlock's": 'eye',
        "Rogue's": 'target', "Gallant's": 'shield', 'Chaos': 'burst', 'Beast': 'paw', 'Choral': 'silence',
        "Hunter's": 'w_bow', 'Samurai': 'w_greatkatana', 'Ninja': 'evasion', 'Drachen': 'wyvern',
        "Evoker's": 'refresh', "Magus's": 'shell', "Corsair's": 'up', 'Puppet': 'gear', "Dancer's": 'fan',
        "Scholar's": 'book', "Bolter's": 'footprints', "Caster's": 'haste', "Courser's": 'sword',
        "Blitzer's": 'haste', "Tactician's": 'tp', "Allies'": 'figure', "Miser's": 'tp', "Companion's": 'heart',
        "Avenger's": 'burst', "Naturalist's": 'flower', "Runeist's": 'rune'}
SHOT = {'Fire': 'fire', 'Ice': 'ice', 'Wind': 'wind', 'Earth': 'earth', 'Thunder': 'thunder', 'Water': 'water',
        'Light': 'light', 'Dark': 'dark'}
RUNES = {'Ignis': 'fire', 'Gelus': 'ice', 'Flabra': 'wind', 'Tellus': 'earth', 'Sulpor': 'thunder', 'Unda': 'water',
         'Lux': 'light', 'Tenebrae': 'dark'}
TRAIT = [  # (keyword, accent, drawing)
    ('Accuracy', 'gold', T('target', 'up')), ('Evasion', 'teal', T('evasion', 'up')),
    ('Attack', 'red', T('sword', 'up')), ('Defense', 'gold', T('shield', 'up')),
    ('Magic Atk', 'violet', T('orb', 'up')), ('Magic Def', 'teal', T('shell', 'up')),
    ('Magic Acc', 'violet', T('eye', 'up')), ('Max HP', 'red', T('HP', 'up')), ('Max MP', 'blue', T('MP', 'up')),
    ('Auto Regen', 'green', T('regen')), ('Auto Refresh', 'blue', T('refresh')), ('Killer', 'red', T('sword', 'target')),
    ('Resist', 'holy', T('shield', 'sparkles')), ('Store TP', 'gold', T('tp', 'up')),
    ('Double Attack', 'red', T('sword', 'haste')), ('Triple Attack', 'red', T('sword', 'burst')),
    ('Critical', 'red', T('target', 'burst')), ('Counter', 'gold', T('fist', 'shield')),
    ('Treasure Hunter', 'gold', T('orb', 'up')), ('Fast Cast', 'violet', T('orb', 'haste')),
    ('Conserve', 'blue', T('MP', 'down')), ('Clear Mind', 'blue', T('MP', 'regen')),
    ('Dual Wield', 'teal', T('w_dagger', 'w_dagger')), ('Martial Arts', 'gold', T('fist', 'haste')),
    ('Shield Mastery', 'gold', T('shield', 'tp')), ('Subtle Blow', 'teal', T('fist', 'down')),
    ('Gilfinder', 'gold', T('orb', 'sparkles')), ('Rapid Shot', 'gold', T('w_bow', 'haste')),
    ('Zanshin', 'red', T('w_greatkatana', 'haste')), ('Kick Attacks', 'gold', T('footprints', 'burst')),
    ('Treas. Hunter', 'gold', T('orb', 'up')), ('Crit. Atk', 'red', T('target', 'burst')),
    ('Crit. Def', 'gold', T('shield', 'burst')), ('Magic Eva', 'teal', T('sparkles', 'up')),
    ('Max. HP', 'red', T('HP', 'up')), ('Shield Def', 'gold', T('shield', 'up')),
    ('Mag. Burst', 'violet', T('orb', 'burst')), ('Skillchain', 'red', T('sword', 'burst')),
    ('Damage', 'red', T('sword', 'up')), ('Shield Barrier', 'gold', T('shield', 'shell')),
    ('Tactical', 'gold', T('shield', 'evasion')), ('Divine Veil', 'holy', T('sparkles', 'shield')),
    ('Snapshot', 'gold', T('w_gun', 'haste')), ('True Shot', 'gold', T('w_bow', 'target')),
    ('Dead Aim', 'gold', T('w_bow', 'burst')), ('Recycle', 'gold', T('w_bow', 'regen')),
    ('Stealth', 'violet', T('figure', 'down')), ('Alertness', 'teal', T('eye', 'up')),
    ('Assassin', 'red', T('w_dagger', 'burst')), ('Aura Steal', 'gold', T('fist', 'dispel')),
    ('Guardian', 'gold', T('shield', 'heart')), ('Iron Will', 'gold', T('shield', 'orb')),
    ('Beast', 'gold', T('paw', 'up')), ('Ninja Tool', 'teal', scroll('up')),
    ('Fencer', 'red', T('sword', 'tp')), ('Inquartata', 'gold', T('sword', 'shield')),
]


def ability_icon(name, typ, aid):
    if name in JA:
        return JA[name]
    if typ == '8':                                   # Phantom Roll
        k = name.replace(' Roll', '')
        return 'gold', T('die', ROLL.get(k, 'sparkles'))
    if typ == '9':                                   # Quick Draw
        e = SHOT.get(name.replace(' Shot', ''))
        if e:
            return Y.ELEMENT_ACCENT[e], T('w_gun', e)
    if typ == '21' and name in RUNES:
        e = RUNES[name]
        return Y.ELEMENT_ACCENT[e], T('rune', e)
    m = re.match(r'^(\w+) Maneuver$', name)
    if m and m.group(1) in SHOT:
        e = SHOT[m.group(1)]
        return Y.ELEMENT_ACCENT[e], T('gear', e)
    if typ == '4':
        for key, acc, fn in TRAIT:
            if key in name:
                return acc, fn
        return None
    return None


WEAPON_RANGES = [(1, 'h2h'), (16, 'dagger'), (32, 'sword'), (48, 'greatsword'), (64, 'axe'), (80, 'greataxe'),
                 (96, 'scythe'), (112, 'polearm'), (128, 'katana'), (144, 'greatkatana'), (160, 'club'),
                 (176, 'staff'), (192, 'bow'), (208, 'gun'), (224, None)]
WEAPON_LATE = {'Exenterator': 'dagger', 'Chant du Cygne': 'sword', 'Requiescat': 'sword', 'Knights of Rotund': 'sword',
               'Final Paradise': 'h2h', 'Fast Blade II': 'sword', 'Dragon Blow': 'h2h', 'Maru Kala': 'h2h',
               'Ruthless Stroke': 'dagger', 'Imperator': 'polearm', 'Dagda': 'club', 'Oshala': 'staff',
               'Uriel Blade': 'sword', 'Glory Slash': 'sword', 'Tartarus Torpor': 'staff', 'Vulcan Shot': 'gun'}
WS_ELEMENT = {'40': 'fire', '41': 'ice', '42': 'wind', '43': 'earth', '44': 'thunder', '45': 'water', '47': 'dark'}
WS_MARKS = ['slash', 'double', 'burst', 'sparkle', 'spin', 'lines', 'cross', 'rise']
WS_ACCENTS = ['teal', 'gold', 'red', 'holy', 'blue', 'violet', 'green', 'fire']


def ws_icon(name, wid, element):
    weapon = WEAPON_LATE.get(name)
    if weapon is None:
        for start, w in WEAPON_RANGES:
            if wid >= start:
                weapon = w
    if weapon is None:
        return None
    wfn = Y.WEAPONS[weapon]
    e = WS_ELEMENT.get(element)
    k = wid % 16
    mark = WS_MARKS[k % len(WS_MARKS)]

    def f(i, a):
        wfn(i, 0.44, 0.56, 0.38)
        if e:
            Y.ELEMENTS[e](a, 0.76, 0.24, 0.16)
            return
        if mark == 'slash':
            a.arc(P([(0.08, 0.08), (0.92, 0.92)]), 290, 350, fill=255, width=L(0.05))
        elif mark == 'double':
            for r in (0.42, 0.34):
                a.arc(P([(0.5 - r, 0.5 - r), (0.5 + r, 0.5 + r)]), 285, 345, fill=255, width=L(0.04))
        elif mark == 'burst':
            Y.burst(a, 0.76, 0.24, 0.16)
        elif mark == 'sparkle':
            Y.light(a, 0.76, 0.24, 0.17)
        elif mark == 'spin':
            a.arc(P([(0.06, 0.06), (0.94, 0.94)]), 120, 300, fill=255, width=L(0.04))
        elif mark == 'lines':
            for n in range(3):
                a.line(P([(0.62 + n * 0.08, 0.10 + n * 0.04), (0.88, 0.36 - n * 0.06)]), fill=255, width=L(0.03))
        elif mark == 'cross':
            a.line(P([(0.66, 0.14), (0.88, 0.36)]), fill=255, width=L(0.05))
            a.line(P([(0.88, 0.14), (0.66, 0.36)]), fill=255, width=L(0.05))
        else:
            Y.arrow_up(a, 0.78, 0.26, 0.15)
    accent = Y.ELEMENT_ACCENT[e] if e else WS_ACCENTS[k % len(WS_ACCENTS)]
    return accent, f, weapon


def ability_families(rows, hand):
    out = []
    for r in rows:
        if r[0] not in ('ability', 'ws'):
            continue
        name, aid, typ, element = r[2], int(r[1]), r[3], r[4]
        if name in hand:
            continue
        fam = family_name(name)
        if fam in hand:
            slug, acc, fn = hand[fam]
            out.append((name, slug, acc, fn, False))
            continue
        if r[0] == 'ws':
            got = ws_icon(name, aid, element)
            if got is None:
                out.append((name, 'gen_ws', 'grey', generic('ws'), True))
                continue
            acc, fn, weapon = got
            out.append((name, 'ws_' + slugify(name), acc, fn, False))
            continue
        got = ability_icon(fam, typ, aid)
        if got is None:
            # pet moves and blood pacts, and anything unnamed: the category's emblem and the letters
            kind = {'6': 'bp', '10': 'bp', '18': 'ready', '20': 'ready', '2': 'pet', '4': 'ja'}.get(typ, 'ja')
            out.append((name, 'gen_' + kind, 'grey', generic(kind), True))
            continue
        out.append((name, 'ja_' + slugify(fam), got[0], got[1], False))
    return out


# ---- Blue Magic: the monster's move (motif, in ink) and what it does (accent symbol) -------------------------------
BLU = {
    'Venom Shell': ('conch', 'poison'), 'Maelstrom': ('wave', 'down'), 'Metallic Body': ('figure', 'stoneskin'),
    'Screwdriver': ('drill', 'burst'), 'MP Drainkiss': ('mouth', 'aspir'), 'Death Ray': ('beam', 'skull'),
    'Sandspin': ('tornado', 'blind'), 'Smite of Rage': ('fist', 'burst'), 'Bludgeon': ('hammer', 'burst'),
    'Refueling': ('figure', 'haste'), 'Ice Break': ('impact', 'bind'), 'Blitzstrahl': ('beam', 'stun'),
    'Self-Destruct': ('bomb', 'burst'), 'Mysterious Light': ('light', 'down'), 'Cold Wave': ('wave', 'down'),
    'Poison Breath': ('breath', 'poison'), 'Stinking Gas': ('spores', 'down'), 'Memento Mori': ('skull', 'up'),
    'Terror Touch': ('claw', 'curse'), 'Spinal Cleave': ('w_greataxe', 'burst'), 'Blood Saber': ('drain', 'burst'),
    'Digest': ('mouth', 'drain'), 'Mandibular Bite': ('fang', 'burst'), 'Cursed Sphere': ('orb', 'curse'),
    'Sickle Slash': ('w_scythe', 'burst'), 'Cocoon': ('bug', 'shield'), 'Filamented Hold': ('bug', 'slow'),
    'Pollen': ('flower', 'regen'), 'Power Attack': ('fist', 'up'), 'Death Scissors': ('scissors', 'skull'),
    'Magnetite Cloud': ('spores', 'gravity'), 'Eyes On Me': ('eye', 'burst'), 'Frenetic Rip': ('claw', 'haste'),
    'Frightful Roar': ('roar', 'down'), 'Hecatomb Wave': ('wave', 'blind'), 'Body Slam': ('impact', 'burst'),
    'Radiant Breath': ('breath', 'slow'), 'Helldive': ('feather', 'impact'), 'Jet Stream': ('feather', 'haste'),
    'Blood Drain': ('fang', 'drain'), 'Sound Blast': ('roar', 'orb'), 'Feather Tickle': ('feather', 'tp'),
    'Feather Barrier': ('feather', 'evasion'), 'Jettatura': ('eye', 'stun'), 'Yawn': ('mouth', 'sleep'),
    'Foot Kick': ('boot', 'burst'), 'Wild Carrot': ('fruit', 'regen'), 'Voracious Trunk': ('tentacle', 'dispel'),
    'Healing Breeze': ('wind', 'regen'), 'Chaotic Eye': ('eye', 'silence'), 'Sheep Song': ('roar', 'sleep'),
    'Ram Charge': ('horn', 'burst'), 'Claw Cyclone': ('claw', 'wind'), 'Lowing': ('roar', 'virus'),
    'Dimensional Death': ('portal', 'skull'), 'Heat Breath': ('breath', 'fire'), 'Blank Gaze': ('eye', 'dispel'),
    'Magic Fruit': ('fruit', 'sparkles'), 'Uppercut': ('fist', 'jump'), '1000 Needles': ('needles', 'burst'),
    'Pinecone Bomb': ('bomb', 'sleep'), 'Sprout Smack': ('leaf', 'slow'), 'Soporific': ('flower', 'sleep'),
    'Queasyshroom': ('mushroom', 'poison'), 'Wild Oats': ('leaf', 'down'), 'Bad Breath': ('breath', 'skull'),
    'Geist Wall': ('curse', 'dispel'), 'Awful Eye': ('eye', 'down'), 'Frost Breath': ('breath', 'ice'),
    'Infrasonics': ('roar', 'evasion'), 'Disseverment': ('claw', 'poison'), 'Actinic Burst': ('burst', 'blind'),
    'Reactor Cool': ('ice', 'shield'), 'Saline Coat': ('bubble', 'shell'), 'Plasma Charge': ('thunder', 'shield'),
    'Temporal Shift': ('slow', 'stun'), 'Vertical Cleave': ('w_greataxe', 'down'), 'Blastbomb': ('bomb', 'bind'),
    'Battle Dance': ('fan', 'down'), 'Sandspray': ('tornado', 'blind'), 'Grand Slam': ('impact', 'up'),
    'Head Butt': ('horn', 'stun'), 'Bomb Toss': ('bomb', 'fire'), 'Frypan': ('pan', 'stun'),
    'Flying Hip Press': ('impact', 'wind'), 'Hydro Shot': ('water', 'down'), 'Diamondhide': ('stoneskin', 'sparkles'),
    'Enervation': ('dark', 'down'), 'Light of Penance': ('light', 'blind'), 'Warm-Up': ('figure', 'up'),
    'Firespit': ('mouth', 'fire'), 'Feather Storm': ('feather', 'poison'), 'Tail Slap': ('tail', 'stun'),
    'Hysteric Barrage': ('fist', 'haste'), 'Amplification': ('orb', 'up'), 'Cannonball': ('bomb', 'up'),
    'Mind Blast': ('eye', 'paralyze'), 'Exuviation': ('conch', 'sparkles'), 'Magic Hammer': ('hammer', 'aspir'),
    'Zephyr Mantle': ('wind', 'blink'), 'Regurgitation': ('mouth', 'water'), 'Seedspray': ('spores', 'down'),
    'Corrosive Ooze': ('bubble', 'down'), 'Spiral Spin': ('tornado', 'down'), 'Asuran Claws': ('claw', 'burst'),
    'Sub-zero Smash': ('impact', 'ice'), 'Triumphant Roar': ('roar', 'up'), 'Acrid Stream': ('wave', 'poison'),
    'Blazing Bound': ('fire', 'impact'), 'Plenilune Embrace': ('dark', 'regen'), 'Demoralizing Roar': ('roar', 'sword'),
    'Cimicine Discharge': ('bug', 'spores'), 'Animating Wail': ('roar', 'haste'), 'Battery Charge': ('thunder', 'refresh'),
    'Leafstorm': ('leaf', 'wind'), 'Regeneration': ('regen', 'up'), 'Final Sting': ('needles', 'skull'),
    'Goblin Rush': ('figure', 'burst'), 'Vanity Dive': ('feather', 'burst'), 'Magic Barrier': ('shell', 'sparkles'),
    'Whirl of Rage': ('tornado', 'stun'), 'Benthic Typhoon': ('wave', 'shield'), 'Auroral Drape': ('light', 'silence'),
    'Osmosis': ('bubble', 'dispel'), 'Quad. Continuum': ('horn', 'haste'), 'Fantod': ('heart', 'up'),
    'Thermal Pulse': ('burst', 'blind'), 'Empty Thrash': ('claw', 'down'), 'Dream Flower': ('spores', 'sleep'),
    'Occultation': ('blink', 'sparkles'), 'Charged Whisker': ('thunder', 'claw'), 'Winds of Promy.': ('wind', 'dispel'),
    'Delta Thrust': ('horn', 'down'), 'Evryone. Grudge': ('curse', 'burst'), 'Reaving Wind': ('wind', 'tp'),
    'Barrier Tusk': ('horn', 'shield'), 'Mortal Ray': ('beam', 'curse'), 'Water Bomb': ('water', 'silence'),
    'Heavy Strike': ('hammer', 'up'), 'Dark Orb': ('dark', 'orb'), 'White Wind': ('wind', 'regen'),
    'Sudden Lunge': ('claw', 'stun'), 'Quadrastrike': ('claw', 'target'), 'Vapor Spray': ('breath', 'water'),
    'Thunder Breath': ('breath', 'thunder'), 'O. Counterstance': ('fist', 'shield'), 'Amorphic Spikes': ('needles', 'down'),
    'Wind Breath': ('breath', 'wind'), 'Barbed Crescent': ('w_scythe', 'down'), 'Nat. Meditation': ('figure', 'sword'),
    'Tem. Upheaval': ('tornado', 'evasion'), 'Rending Deluge': ('wave', 'dispel'), 'Embalming Earth': ('earth', 'slow'),
    'Paralyzing Triad': ('claw', 'paralyze'), 'Foul Waters': ('wave', 'virus'), 'Glutinous Dart': ('needles', 'slow'),
    'Retinal Glare': ('eye', 'light'), 'Subduction': ('earth', 'down'), 'Thrashing Assault': ('fist', 'target'),
    'Erratic Flutter': ('feather', 'haste'), 'Restoral': ('regen', 'sparkles'), 'Rail Cannon': ('beam', 'burst'),
    'Diffusion Ray': ('beam', 'orb'), 'Sinker Drill': ('drill', 'down'), 'Molting Plumage': ('feather', 'up'),
    'Nectarous Deluge': ('flower', 'poison'), 'Sweeping Gouge': ('claw', 'shield'), 'Atra. Libations': ('drain', 'tp'),
    'Searing Tempest': ('fire', 'burst'), 'Spectral Floe': ('ice', 'burst'), 'Anvil Lightning': ('thunder', 'impact'),
    'Entomb': ('earth', 'petrify'), 'Saurian Slide': ('tail', 'down'), 'Palling Salvo': ('dark', 'burst'),
    'Blinding Fulgor': ('light', 'burst'), 'Scouring Spate': ('wave', 'sword'), 'Silent Storm': ('wind', 'silence'),
    'Tenebral Crush': ('dark', 'shield'), 'Thunderbolt': ('thunder', 'stun'), 'Harden Shell': ('conch', 'shield'),
    'Absolute Terror': ('skull', 'stun'), 'Gates of Hades': ('fire', 'skull'), 'Tourbillion': ('tornado', 'shield'),
    'Pyric Bulwark': ('fire', 'shield'), 'Bilgestorm': ('wave', 'sword'), 'Bloodrake': ('claw', 'drain'),
    'Droning Whirlwind': ('tornado', 'dispel'), 'Carcharian Verve': ('fang', 'up'), 'Blistering Roar': ('roar', 'fire'),
    'Uproot': ('leaf', 'burst'), 'Crashing Thunder': ('thunder', 'burst'), 'Polar Roar': ('roar', 'ice'),
    'Mighty Guard': ('shield', 'sparkles'), 'Cruel Joke': ('mouth', 'skull'), 'Cesspool': ('bubble', 'poison'),
    'Tearing Gust': ('wind', 'burst'),
}


# the accent's colour follows what it means (readable() still keeps it off its own disc's colour)
SYM_ACCENT = {'poison': 'poison', 'virus': 'poison', 'sleep': 'violet', 'silence': 'teal', 'paralyze': 'gold',
              'slow': 'earth', 'bind': 'violet', 'gravity': 'violet', 'stun': 'gold', 'blind': 'dark', 'curse': 'dark',
              'skull': 'grey', 'petrify': 'earth', 'down': 'blue', 'up': 'red', 'burst': 'red', 'haste': 'wind',
              'regen': 'green', 'refresh': 'blue', 'sparkles': 'holy', 'shield': 'gold', 'shell': 'teal',
              'evasion': 'teal', 'blink': 'violet', 'drain': 'red', 'aspir': 'blue', 'tp': 'gold', 'dispel': 'violet',
              'target': 'red', 'sword': 'red', 'orb': 'violet', 'impact': 'gold', 'claw': 'red', 'jump': 'gold',
              'spores': 'poison', 'stoneskin': 'earth'}


def blu_icon(name, element):
    got = BLU.get(name)
    if got is None:
        return None
    motif, accent_sym = got
    e = {'0': 'fire', '1': 'ice', '2': 'wind', '3': 'earth', '4': 'thunder', '5': 'water', '6': 'light',
         '7': 'dark'}.get(element)
    accent = Y.ELEMENT_ACCENT.get(accent_sym) or SYM_ACCENT.get(accent_sym) or (Y.ELEMENT_ACCENT[e] if e else 'gold')
    return accent, two(motif, accent_sym)
