"""Memory-card helpers: N64 Controller Pak and Dreamcast VMU images."""

from __future__ import annotations

import random
import struct
from array import array
from datetime import datetime

from .const import PAK_SIZE
from .models import VmuSave

VMU_BLOCK = 512
# Blocks 240-255 hold the directory (241-253), FAT (254) and root (255) of a
# standard VMU, so the save list needs only the last 8 KiB of the image.
VMU_TAIL = 16 * VMU_BLOCK
_TAIL_FIRST = 256 - VMU_TAIL // VMU_BLOCK
_FAT_FREE = 0xFFFC


def vmu_swap(data: bytes) -> bytes:
    """Convert between the adapter's VMU buffer and a standard VMU image.

    BlueRetro stores the VMU as Maple bus words: every 32-bit word is
    byte-reversed relative to the standard ``.bin`` used by emulators and the
    web config (``dc_vmu.js``). The swap is its own inverse.
    """
    words = array("I", data)
    assert words.itemsize == 4
    words.byteswap()
    return words.tobytes()


def _bcd_time(raw: bytes) -> datetime | None:
    if any(b >> 4 > 9 or b & 0x0F > 9 for b in raw[:7]):
        return None
    try:
        century, year, month, day, hour, minute, second = (
            (b >> 4) * 10 + (b & 0x0F) for b in raw[:7]
        )
        return datetime(century * 100 + year, month, day, hour, minute, second)
    except ValueError:
        return None


def parse_vmu_directory(tail: bytes) -> tuple[list[VmuSave], int] | None:
    """Parse ``(saves, free_blocks)`` from the last 8 KiB of a standard VMU image.

    Returns ``None`` when the root block is missing (unformatted card) or the
    directory/FAT live outside the tail (non-standard layout).
    """
    if len(tail) != VMU_TAIL:
        return None
    root = tail[-VMU_BLOCK:]
    if root[:16] != b"\x55" * 16:
        return None
    fat_loc, _, dir_loc, dir_size, _, user_blocks = struct.unpack_from("<6H", root, 0x46)
    first_dir = dir_loc - dir_size + 1
    if not (_TAIL_FIRST <= first_dir <= dir_loc < 256 and _TAIL_FIRST <= fat_loc < 256):
        return None

    def block(n: int) -> bytes:
        start = (n - _TAIL_FIRST) * VMU_BLOCK
        return tail[start : start + VMU_BLOCK]

    fat = struct.unpack("<256H", block(fat_loc))
    free = sum(1 for n in range(min(user_blocks, 256)) if fat[n] == _FAT_FREE)
    saves = []
    for n in range(dir_loc, first_dir - 1, -1):
        data = block(n)
        for off in range(0, VMU_BLOCK, 32):
            entry = data[off : off + 32]
            if entry[0] not in (0x33, 0xCC):
                continue
            saves.append(
                VmuSave(
                    name=entry[4:16].decode("ascii", "replace").rstrip("\x00 "),
                    kind="game" if entry[0] == 0xCC else "data",
                    blocks=struct.unpack_from("<H", entry, 0x18)[0],
                    saved=_bcd_time(entry[0x10:0x17]),
                )
            )
    return saves, free


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
