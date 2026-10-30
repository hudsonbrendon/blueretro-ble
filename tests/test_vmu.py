from datetime import datetime
import struct
from unittest.mock import AsyncMock, patch

from blueretro_ble import BlueRetroDevice, const, parse_vmu_directory, vmu_swap
from blueretro_ble.memorycard import VMU_TAIL

from .test_write_ops import MemClient


def _standard_vmu() -> bytes:
    """A formatted VMU (standard order) holding one save and one mini-game."""
    img = bytearray(const.VMU_SIZE)
    root = 255 * 512
    img[root : root + 16] = b"\x55" * 16
    struct.pack_into("<6H", img, root + 0x46, 254, 1, 253, 13, 0, 200)
    fat = [0xFFFC] * 256
    fat[0:3] = [1, 2, 0xFFFA]  # 3-block save
    fat[199] = 0xFFFA  # 1-block game at the end of user space
    struct.pack_into("<256H", img, 254 * 512, *fat)
    entry = bytearray(32)
    entry[0] = 0x33
    entry[4:16] = b"SONICADV_INT"
    entry[0x10:0x17] = bytes([0x20, 0x26, 0x10, 0x25, 0x15, 0x04, 0x11])
    struct.pack_into("<H", entry, 0x18, 3)
    img[253 * 512 : 253 * 512 + 32] = entry
    game = bytearray(32)
    game[0] = 0xCC
    game[4:16] = b"CHAO        "
    game[0x10:0x17] = bytes([0x19, 0xFE, 0x11, 0x27, 0, 0, 0])  # invalid BCD
    struct.pack_into("<H", game, 0x18, 1)
    img[253 * 512 + 32 : 253 * 512 + 64] = game
    return bytes(img)


def test_vmu_swap_is_word_byte_reversal_and_self_inverse():
    assert vmu_swap(b"\x01\x02\x03\x04\x05\x06\x07\x08") == b"\x04\x03\x02\x01\x08\x07\x06\x05"
    data = bytes(range(256)) * 4
    assert vmu_swap(vmu_swap(data)) == data


def test_parse_vmu_directory():
    saves, free = parse_vmu_directory(_standard_vmu()[-VMU_TAIL:])
    assert free == 196
    assert [(s.name, s.kind, s.blocks) for s in saves] == [
        ("SONICADV_INT", "data", 3),
        ("CHAO", "game", 1),
    ]
    assert saves[0].saved == datetime(2026, 10, 25, 15, 4, 11)
    assert saves[1].saved is None


def test_parse_vmu_directory_unformatted():
    assert parse_vmu_directory(bytes(VMU_TAIL)) is None
    assert parse_vmu_directory(b"short") is None


async def test_update_reads_vmu_directory_on_dreamcast():
    client = MemClient()
    client.buf[:] = vmu_swap(_standard_vmu())
    reads = {
        const.CHAR_ABI: b"\x02",
        const.CHAR_APP: b"v25.04 hw1 dreamcast",
        const.CHAR_BDADDR: bytes(6),
        const.CHAR_GLOBAL_CFG: bytes(4),
        const.CHAR_OUTPUT_DATA: bytes([0, 3]),  # GamePad + Both
    }
    mem_read, mem_write = client.read_gatt_char, client.write_gatt_char

    async def read(uuid):
        return reads[uuid] if uuid in reads else await mem_read(uuid)

    async def write(uuid, data, response=True):
        if uuid != const.CHAR_OUTPUT_CTRL:
            await mem_write(uuid, data, response)

    client.read_gatt_char, client.write_gatt_char = read, write
    ble = AsyncMock()
    with patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)):
        state = await BlueRetroDevice().async_update(ble)
    assert state.available
    assert state.vmu_free_blocks == 196
    assert [s.name for s in state.vmu_saves] == ["SONICADV_INT", "CHAO"]
    assert client.cursor >= 0 and client.ctrl_writes[-1] == 0
