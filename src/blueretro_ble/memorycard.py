"""N64 Controller Pak helpers."""

from __future__ import annotations

import random

from .const import PAK_SIZE


def make_formatted_pak(rng: random.Random | None = None) -> bytes:
    """Generate a blank, formatted 32 KiB N64 Controller Pak image.

    Direct port of BlueRetroWebCfg ``utils/makeFormattedPak.js`` (itself from
    bryc's MPKEdit). The id block carries a random serial; the header checksum
    and index tables are initialized so the console sees an empty, valid pak.

    ``rng`` lets callers inject a seeded generator for reproducible output
    (tests); by default a fresh ``random.Random`` is used.
    """
    rnd = rng or random.Random()
    data = bytearray(PAK_SIZE)
    block = bytearray(32)

    # id block (random serial)
    block[1] = rnd.randint(0, 255) & 0x3F
    block[5] = rnd.randint(0, 255) & 0x07
    block[6] = rnd.randint(0, 255)
    block[7] = rnd.randint(0, 255)
    block[8] = rnd.randint(0, 255) & 0x0F
    block[9] = rnd.randint(0, 255)
    block[10] = rnd.randint(0, 255)
    block[11] = rnd.randint(0, 255)
    block[25] = 0x01  # device bit
    block[26] = 0x01  # bank size (must be exactly 0x01)

    # pakId checksum
    sum_a = 0
    for i in range(0, 28, 2):
        sum_a = (sum_a + ((block[i] << 8) + block[i + 1])) & 0xFFFF
    sum_b = 0xFFF2 - sum_a  # may be negative; JS-style truncation below
    block[28] = (sum_a >> 8) & 0xFF
    block[29] = sum_a & 0xFF
    block[30] = (sum_b >> 8) & 0xFF
    block[31] = sum_b & 0xFF

    # the checksum block is mirrored across the header page
    for ofs in (32, 96, 128, 192):
        data[ofs : ofs + 32] = block

    # init index table and its backup (entry 3 = free)
    for i in range(5, 128):
        data[256 + i * 2 + 1] = 3
        data[512 + i * 2 + 1] = 3
    data[257] = 0x71
    data[513] = 0x71

    return bytes(data)
