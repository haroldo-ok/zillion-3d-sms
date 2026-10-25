"""Levels -> compact ROM blobs.

blob layout (all little endian):
  +0   u16 tilemap offset   (4096 bytes, x major: index = x*64 + y)
  +2   u16 area offset      (64 column offsets u16 (relative to the area
                             blob start), then (len, value) run pairs per
                             column; value 0..36 area, |0x40 ambush marker,
                             0xFF not a floor tile)
  +4   u16 object offset    (u16 count, then entries key lo, key hi, code;
                             key = y*64 + x ascending = the original
                             ScanInfoPlane order)
  +6   u16 door offset      (u8 count, then 6 bytes: x, y, vertical, lock,
                             area1, area2)
tile bytes: 0 floor, 1..63 wall (|0x40 next to a door), 0x80|n door n
"""
import os, struct
import wolfdata
import wl_levels

AREATILE = 107
NUMAREAS = 37
AMBUSHTILE = 106


def build_level(m):
    W = H = 64
    p0, p1 = m['planes'][0], m['planes'][1]
    t = [[0] * H for _ in range(W)]              # t[x][y]
    area = [[0xFF] * H for _ in range(W)]
    raw = lambda x, y: p0[y * 64 + x]
    for y in range(H):
        for x in range(W):
            v = raw(x, y)
            if v < AREATILE:
                t[x][y] = v if v < 64 else 0
            else:
                area[x][y] = v - AREATILE
    # doors (scan order of SetupGameLevel: y outer, x inner)
    doors = []
    for y in range(H):
        for x in range(W):
            v = raw(x, y)
            if 90 <= v <= 101:
                vertical = 1 if not (v & 1) else 0
                lock = (v - 90) // 2 if vertical else (v - 91) // 2
                n = len(doors)
                t[x][y] = 0x80 | n
                if vertical:
                    a = raw(x - 1, y)
                    b = raw(x + 1, y)
                    t[x][y - 1] |= 0x40
                    t[x][y + 1] |= 0x40
                else:
                    a = raw(x, y - 1)
                    b = raw(x, y + 1)
                    t[x - 1][y] |= 0x40
                    t[x + 1][y] |= 0x40
                area[x][y] = a - AREATILE if a >= AREATILE else 0
                doors.append((x, y, vertical, lock, a - AREATILE, b - AREATILE))
    assert len(doors) <= 64
    for d in doors:
        assert d[4] >= 0 and d[5] >= 0, d
    # objects
    objs = []
    for y in range(H):
        for x in range(W):
            v = p1[y * 64 + x]
            if v:
                assert v < 256
                objs.append((y * 64 + x, v))
    # ambush markers: the original looks right, then the three left cells
    amb = []
    for y in range(H):
        for x in range(W):
            if raw(x, y) == AMBUSHTILE:
                tile = AMBUSHTILE
                def at(xx, yy):
                    return raw(xx, yy) if 0 <= xx < W and 0 <= yy < H else 0
                # the original (WL_GAME.C) looks at *map (x+1), the tiles above and
                # below (x, y -+ 1) and x - 1; the last match wins
                if at(x + 1, y) >= AREATILE:
                    tile = at(x + 1, y)
                if at(x, y - 1) >= AREATILE:
                    tile = at(x, y - 1)
                if at(x, y + 1) >= AREATILE:
                    tile = at(x, y + 1)
                if at(x - 1, y) >= AREATILE:
                    tile = at(x - 1, y)
                assert tile >= AREATILE, (x, y)
                t[x][y] = 0
                area[x][y] = (tile - AREATILE) | 0x40
                amb.append((x, y))
    tile_b = bytearray()
    for x in range(W):
        for y in range(H):
            tile_b.append(t[x][y])
    # areas, per column runs
    col_ofs = bytearray(128)
    runs = bytearray()
    for x in range(W):
        o = 128 + len(runs)
        col_ofs[2 * x] = o & 0xFF
        col_ofs[2 * x + 1] = o >> 8
        y = 0
        while y < H:
            v = area[x][y]
            n = 1
            while y + n < H and area[x][y + n] == v:
                n += 1
            runs += bytes([n, v])
            y += n
    area_b = bytes(col_ofs) + bytes(runs)
    obj_b = bytearray(struct.pack('<H', len(objs)))
    for key, v in objs:
        obj_b += bytes([key & 0xFF, key >> 8, v])
    door_b = bytearray([len(doors)])
    for d in doors:
        door_b += bytes([d[0], d[1], d[2], d[3], d[4], d[5]])
    hdr = 8
    o_t = hdr
    o_a = o_t + len(tile_b)
    o_o = o_a + len(area_b)
    o_d = o_o + len(obj_b)
    blob = struct.pack('<4H', o_t, o_a, o_o, o_d) + bytes(tile_b) + area_b + bytes(obj_b) + bytes(door_b)
    return blob, dict(doors=len(doors), objs=len(objs), amb=len(amb))


def build(pk, H, C, d):
    assert len(d.maps) == wl_levels.NUM_LEVELS, len(d.maps)
    ceil_cram = [wl_levels.ceil_cram(d, c) for c in wl_levels.tables()[0]]
    banks, addrs = [], []
    for m in d.maps:
        blob, st = build_level(m)
        b, a = pk.add('map%d' % m['index'], blob)
        banks.append(b)
        addrs.append(a)
        print('map', m['index'], len(blob), st)
    H.append('#define NUMMAPS %d' % len(d.maps))
    H.append('extern const u8 map_bank[NUMMAPS];')
    H.append('extern const u16 map_addr[NUMMAPS];')
    H.append('extern const u8 map_ceil[NUMMAPS];')
    C.append('const u8 map_bank[NUMMAPS] = {%s};' % ','.join(map(str, banks)))
    C.append('const u16 map_addr[NUMMAPS] = {%s};' % ','.join(map(str, addrs)))
    # only wl_game.c (bank 1) reads it: a file of its own, linked into that bank
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gen')
    with open(os.path.join(gen, 'lvl_ceil.c'), 'w') as f:
        f.write('/* generated by tools/wl_maps.py: vgaCeiling of WL_DRAW.C, the CRAM byte of the ceiling colour */\n')
        f.write('#include "assets.h"\nconst u8 map_ceil[NUMMAPS] = {%s};\n' % ','.join(str(c) for c in ceil_cram))
