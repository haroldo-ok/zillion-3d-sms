"""Names and indexes from the original headers (AUDIOWL6.H, GFXV_WL6.H)."""
import re, os

import paths
SRC = paths.SRC


def parse_enum_block(text, start_value=0):
    out = []
    v = start_value
    for line in text.split('\n'):
        line = re.sub(r'//.*', '', line).strip()
        if not line or line.startswith('typedef') or line.startswith('}'):
            continue
        for part in line.split(','):
            part = part.strip()
            if not part:
                continue
            if '=' in part:
                n, val = part.split('=')
                v = int(val.strip(), 0)
                out.append((n.strip(), v))
            else:
                out.append((part, v))
            v += 1
    return out


def audio_names():
    t = open(os.path.join(SRC, 'WOLFSRC', 'AUDIOWL6.H'), encoding='latin1').read()
    blocks = re.findall(r'typedef enum \{(.*?)\}\s*(\w+)\s*;', t, re.S)
    sounds = music = None
    for body, name in blocks:
        if 'HITWALLSND' in body:
            sounds = parse_enum_block(body)
        if '_MUS' in body:
            music = parse_enum_block(body)
    return sounds, music


def wl6_enum():
    """(name, chunk) for every entry of the WL6 graphics enum (GFXV_WL6.H).  Zillion 3D is a
    registered Wolfenstein 3D mod: its VGAGRAPH holds the 132 pictures of the WL6 data set
    (chunks 3..134), the two fonts (1, 2) and the help / end texts (T_HELPART, T_ENDART1..)."""
    t = open(os.path.join(SRC, 'WOLFSRC', 'GFXV_WL6.H'), encoding='latin1').read()
    e = t[t.index('typedef enum'):t.index('}', t.index('typedef enum'))]
    out = []
    val = None
    for line in e.splitlines():
        s = re.sub(r'//.*', '', line).strip().rstrip(',')
        if not s or s.startswith(('typedef', '{', '#')):
            continue
        for part in s.split(','):
            part = part.strip()
            if not part:
                continue
            if '=' in part:
                n, v = [x.strip() for x in part.split('=')]
                val = int(v, 0)
            else:
                n = part
                val = 3 if val is None else val + 1
            out.append((n, val))
    return out


def gfx_names():
    """the 132 pictures of VGAGRAPH (STARTPICS 3 .. 134)"""
    return [(n, c) for n, c in wl6_enum() if 3 <= c < 135]


def text_chunk(name):
    """chunk of a text lump of the WL6 graphics enum (T_HELPART, T_ENDART1)"""
    return dict(wl6_enum())[name]


if __name__ == '__main__':
    s, m = audio_names()
    print(len(s), s[:3], s[-3:])
    print(len(m), m[:3], m[-3:])
    g = gfx_names()
    print(len(g), g[:3], g[-5:])
