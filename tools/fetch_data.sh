#!/bin/bash
# Puts what the converters (tools/build_assets.py) read where they look for it:
#   data/*.WL6    the game data: the Zillion 3D download from https://moonkey.itch.io/zillion-3d (a Windows zip
#                 of the mod's Wolfenstein 3D registered data).  itch.io hands the file out only to a session, so
#                 this script does not download it: put the zip in data/ (any name) and this unpacks it.
#   wolf3d/       id Software's source release: the names of the graphics and sounds, the 256-colour palette
#   wolf-3d-md/   (only with --genesis) the Genesis port; tools/port_game.py re-derives src/game/*.c from it.
#                 The ported files are already in src/game, so building does not need it.
# usage: tools/fetch_data.sh [--genesis] [DIR]
#   DIR defaults to ../work next to the project; the converters look there (tools/paths.py), or in the
#   directories named by WL_DATA, WL_SRC and WL_MD.  The Genesis port goes next to DIR (../wolf-3d-md).
set -euo pipefail
genesis=0
if [ "${1:-}" = "--genesis" ]; then genesis=1; shift; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-$ROOT/../work}"
mkdir -p "$W/data"
W="$(cd "$W" && pwd)"

need="AUDIOHED AUDIOT GAMEMAPS MAPHEAD VGADICT VGAGRAPH VGAHEAD VSWAP"
have=1
for f in $need; do [ -f "$W/data/$f.WL6" ] || have=0; done

if [ "$have" = 1 ]; then
    echo "the game data is already in $W/data"
else
    # a zip of the mod (any name) that was put next to where the data should be
    for z in "$W/data"/*.zip "$W"/*.zip; do
        [ -f "$z" ] || continue
        echo "unpacking $z ..."
        unzip -oq "$z" -d "$W/data" || true
    done
    # zips of mods often have the .WL6 files one directory down
    if [ ! -f "$W/data/VSWAP.WL6" ]; then
        found="$(find "$W/data" -name 'VSWAP.WL6' -printf '%h\n' 2>/dev/null | head -1)"
        [ -n "$found" ] && cp -n "$found"/*.WL6 "$W/data"/ || true
    fi
    have=1
    for f in $need; do [ -f "$W/data/$f.WL6" ] || have=0; done
    if [ "$have" != 1 ]; then
        cat >&2 <<'EOF'
the Zillion 3D data is missing: this needs the mod's Wolfenstein 3D registered files
  (VSWAP.WL6 VGAGRAPH.WL6 VGAHEAD.WL6 VGADICT.WL6 GAMEMAPS.WL6 MAPHEAD.WL6 AUDIOT.WL6 AUDIOHED.WL6).
Get the mod from https://moonkey.itch.io/zillion-3d (a free download, a Windows zip), drop the zip in that
directory and run this script again, or unzip it there yourself.
EOF
        exit 1
    fi
fi

if [ -f "$W/wolf3d/WOLFSRC/WL_MAIN.C" ]; then
    echo "id's source release is already in $W/wolf3d"
else
    echo "fetching id's source release ..."
    git clone --depth 1 https://github.com/id-Software/wolf3d "$W/wolf3d"
fi

if [ "$genesis" = 1 ]; then
    if [ -d "$W/../wolf-3d-md/src" ]; then
        echo "the Genesis port is already in $W/../wolf-3d-md"
    else
        echo "fetching the Genesis port ..."
        git clone --depth 1 https://github.com/haroldo-ok/zillion-3d-md "$W/../wolf-3d-md"
    fi
fi
echo "ready: $W   (tools/paths.py finds it when it is ../work next to the project)"
