#!/usr/bin/env python3
"""The 3-D view has Wolfenstein 3D's own projection (72 degree field of view, a wall one tile away and 1.2 tiles
high is 158 px / distance): compare the wall extents of a ROM frame with tools/refview.py, a float ray caster of
the real textures and the real map.

usage: check_view.py <screenshot.ppm>   exit status 0 = the geometry matches

The picture is the start of Zillion 3D's episode 1 floor 1 (tile 24,62, looking east).  The player stands at the
centre of a tile, but a teleport can leave the camera a fraction of a tile off, so the best place of a 3 x 3
neighbourhood (and then of its own 3 x 3 sub-tiles) is compared: a projection that is off (KH, the wall height,
the pixel aspect) shows on every wall whatever the offset, an offset cannot fix it."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import refview

KH, WALL_K = 132.0, 158.4                    # gen/assets.h: PROJ_KH, and 1.2 x KH on square pixels
CEIL_ROM, FLOOR_ROM = (85, 85, 85), (170, 170, 170)        # palette entries 1 and 0
CEIL_REF, FLOOR_REF = (56, 56, 56), (113, 113, 113)


def extents(img, ceil, floor):
    """per column: the first row that is not the ceiling and the first row of the floor from the bottom (the
    weapon in the middle of the picture and the sprites in the view hide the floor of a few columns)"""
    def is_(px, c):
        return abs(px - np.array(c)).sum() < 12
    out = []
    for x in range(img.shape[1]):
        col = img[:, x]
        top = 0
        while top < len(col) and is_(col[top], ceil):
            top += 1
        bot = len(col)
        while bot > top and is_(col[bot - 1], floor):
            bot -= 1
        out.append((top, bot))
    return np.array(out)


rom = np.array(Image.open(sys.argv[1]).convert('RGB').crop((32, 0, 224, 96))).astype(int)
er = extents(rom, CEIL_ROM, FLOOR_ROM)
hr = er[:, 1] - er[:, 0]


def score(px, py):
    r = refview.render(px, py, 90, W=192, H=96, KH=KH, wall_k=WALL_K).astype(int)
    ef = extents(r, CEIL_REF, FLOOR_REF)
    hf = ef[:, 1] - ef[:, 0]
    tops = abs(er[:, 0] - ef[:, 0])
    return tops.mean() + abs(hr.mean() - hf.mean()), tops.mean(), hf.mean()


best = None
for step, offsets in ((0.5, (-0.5, 0.0, 0.5)), (0.25, (-0.25, 0.0, 0.25))):
    cx, cy = (24.5, 62.5) if best is None else (best[1], best[2])
    for dpx in offsets:
        for dpy in offsets:
            s = score(cx + dpx, cy + dpy)
            if best is None or s[0] < best[0][0]:
                best = (s, cx + dpx, cy + dpy)
(_, tmean, hfmean) = best[0]
print('camera %.2f,%.2f: wall top mean |diff| %.2f px; wall height rom %.1f ref %.1f'
      % (best[1], best[2], tmean, hr.mean(), hfmean))
ok = tmean <= 3.0 and abs(hr.mean() - hfmean) <= 5.0
print('PASS' if ok else 'FAIL: the view geometry does not match the Wolfenstein 3D projection')
sys.exit(0 if ok else 1)
