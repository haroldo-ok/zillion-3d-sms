"""The shared 16 colour palette of the 3-D view (walls + world sprites)."""
import os, json, collections
import numpy as np
import sms

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR_COLOR = 0x19
CEILING_COLOR = 0x1d
CACHE = os.path.join(HERE, '..', 'gen', 'viewpal.json')

# tile n is drawn with pages 2(n-1) (horizontal) and 2(n-1)+1 (vertical) -- SetupWalls of WL_MAIN.C --
# plus the 8 door pages; the pages that the levels of this game can show are the ones the view palette
# has to serve
DOORWALL = 98


def used_wall_tiles(d):
    """wall tiles of all levels (the game draws a tile < 64 as a wall, WL_GAME.C)"""
    out = set()
    for m in d.maps:
        for v in m['planes'][0]:
            if 0 < v < 64:
                out.add(v)
    return sorted(out)


def used_wall_pages(d):
    pages = set([DOORWALL + i for i in range(8)])
    for t in used_wall_tiles(d):
        pages.add(2 * (t - 1))
        pages.add(2 * (t - 1) + 1)
    return sorted(pages)


def build_view_palette(d, tries=16):
    if os.path.exists(CACHE):
        return [tuple(c) for c in json.load(open(CACHE))]
    allpal = d.pal8
    cnt = collections.Counter()
    for p in used_wall_pages(d):
        if d.page(p) is None:
            continue
        for col in d.wall(p):
            for v in col:
                cnt[v] += 1.0
    for s in range(d.num_sprites()):
        sp = d.sprite(s)
        if sp is None:
            continue
        for col in sp:
            for v in col:
                if v is not None:
                    cnt[v] += 0.5
    cols = np.array([allpal[i] for i in cnt])
    w = np.array([cnt[i] for i in cnt])
    # floor and ceiling must stay distinct: the SMS has only four grey levels
    fixed = [(2, 2, 2), (1, 1, 1)]
    pal, err = sms.choose_palette(cols, w, 16, fixed)
    pal = [tuple(int(v) for v in c) for c in pal]
    json.dump(pal, open(CACHE, 'w'))
    print('view palette error', err)
    return pal


def map256(d, pal):
    """256 colour VGA index -> view palette index"""
    lab = sms.rgb_to_lab(np.array(d.pal8, dtype=np.float64))
    idx, _ = sms.nearest_index(lab, pal)
    return [int(i) for i in idx]
