"""Regenerate mods/hl_core, hl_halflife, hl_opfor and hl_blueshift from these specs.

    cd Patchwork/tools/halflife && python3 build.py
"""

import blueshift
import core
import halflife
import opfor

if __name__ == "__main__":
    for mod in (core, halflife, opfor, blueshift):
        mod.build()
        print("built", mod.B.mod_id, "(%d rooms)" % len(mod.B.rooms))
