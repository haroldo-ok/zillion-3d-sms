"""Scenarios of the equivalence test (tests/det/det.py): scripts of input keyed to GAME frames, run on the
deterministic build (make DET=1: fixed 24 tic steps, constant random seed, binary pad).

An item is ('until', N)   wait until game frame N (and print the state hash there),
            ('tap', X, K)  press X for one frame and release it for one, K times (from the current frame),
            ('hold', X)   pad: up/down/left/right/1/2 joined with '+', or none,
            ('poke', SYM, VAL)  write a byte of system RAM,
            ('warp', x, y, dir) teleport (dir 0 N, 1 E, 2 S, 3 W),
            ('map', n)    jump to level n (1..20: the ten floors of episode 1, then the ten of episode 2).
Every game frame's screen is hashed too (smstest hooklog at the entry of ThreeDRefresh), so a build that
renders or plays differently in ANY frame of ANY scenario is caught.

The places come from Zillion 3D's own episode 1 floor 1 (the start corridor at x = 24, the door at 24,57, the
ambush room north of it, the machine gun in the corridor and the guard at 19,51); the game has no push walls,
so the old 'secret' scenario became 'items'."""

SCENARIOS = {
    # standing at the start: the guards of the room north of the corridor move about
    'idle': [('poke', 'dbg_god', 1), ('until', 50)],
    # the start corridor's door (button 2), then north into the ambush room
    'walk': [('poke', 'dbg_god', 1), ('until', 3), ('hold', 'up'), ('until', 32), ('hold', 'none'),
             ('tap', '2', 2), ('hold', 'up'), ('until', 110), ('hold', 'none'), ('until', 114)],
    # every ray changes every frame
    'turn': [('poke', 'dbg_god', 1), ('until', 3), ('hold', 'left'), ('until', 30), ('hold', 'right'), ('until', 50),
             ('hold', 'none'), ('until', 52)],
    # shooting a standing guard: AI, damage, death, drops, score (the guard at 19,51 seen from the west side)
    'fight': [('poke', 'dbg_god', 1), ('until', 2), ('warp', 23, 51, 3), ('until', 6), ('tap', '1', 24),
              ('until', 56), ('hold', 'up'), ('until', 64), ('hold', 'none'), ('until', 66)],
    # no god mode, standing in front of the guards: damage, the face, the red flash, death, respawn
    'hurt': [('until', 2), ('warp', 23, 51, 3), ('until', 40), ('hold', 'right'), ('until', 44), ('hold', 'none'),
             ('until', 160)],
    # the ambush room: walk and turn among the guards and the statics
    'room': [('poke', 'dbg_god', 1), ('until', 2), ('warp', 24, 55, 0), ('until', 5), ('hold', 'up'), ('until', 12),
             ('hold', 'right'), ('until', 20), ('hold', 'up'), ('until', 28), ('hold', 'left'), ('until', 36),
             ('hold', 'none'), ('until', 38)],
    # walking over a pickup: the machine gun of the start corridor gives ammo and the weapon
    'items': [('poke', 'dbg_god', 1), ('until', 2), ('warp', 23, 61, 0), ('until', 5), ('hold', 'up'), ('until', 20),
              ('hold', 'none'), ('until', 26)],
    # all twenty levels (both episodes): loading, every kind of spawn, idling AI
    'levels': [('poke', 'dbg_god', 1)]
              + sum([[('until', 3 + 5 * i), ('map', i + 1)] for i in range(20)], [])
              + [('until', 108)],
}
