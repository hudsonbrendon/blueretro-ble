import struct
from unittest.mock import AsyncMock, patch

import pytest

from blueretro_ble import const
from blueretro_ble.device import BlueRetroDevice


class MemClient:
    """Emulates the firmware's flat memory-card buffer + auto-advancing cursor."""

    def __init__(self, size=const.VMU_SIZE, mtu=247):
        self.buf = bytearray(size)
        self.cursor = 0
        self.mtu_size = mtu
        self.disconnect = AsyncMock()
        self.max_write_chunk = 0
        self.crossed_block = False
        self.ctrl_writes = []

    async def write_gatt_char(self, uuid, data, response=True):
        data = bytes(data)
        if uuid == const.CHAR_FILE_CTRL:
            self.cursor = struct.unpack("<I", data)[0]
            self.ctrl_writes.append(self.cursor)
        elif uuid == const.CHAR_FILE_DATA:
            self.max_write_chunk = max(self.max_write_chunk, len(data))
            start, end = self.cursor, self.cursor + len(data)
            if len(data) and start // const.MC_BLOCK != (end - 1) // const.MC_BLOCK:
                self.crossed_block = True
            self.buf[start:end] = data
            self.cursor = end  # firmware advances its own cursor
        else:
            raise AssertionError(f"unexpected write {uuid}")

    async def read_gatt_char(self, uuid):
        if uuid == const.CHAR_FILE_DATA:
            n = min(244, len(self.buf) - self.cursor)
            chunk = bytes(self.buf[self.cursor : self.cursor + n])
            self.cursor += n
            return chunk
        raise AssertionError(f"unexpected read {uuid}")


@pytest.fixture
def ble():
    dev = AsyncMock()
    dev.address = "AA:BB:CC:DD:EE:FF"
    return dev


def _patch(client):
    return patch(
        "blueretro_ble.device.establish_connection",
        AsyncMock(return_value=client),
    )


async def test_write_vmu_roundtrip_block_aligned(ble):
    data = bytes((i * 7) & 0xFF for i in range(const.VMU_SIZE))
    client = MemClient()
    with _patch(client):
        await BlueRetroDevice().async_write_vmu(ble, data)
    assert client.buf == data
    assert client.max_write_chunk <= const.FILE_CHUNK
    assert client.crossed_block is False
    # cursor reset to 0 at start and end
    assert client.ctrl_writes[0] == 0 and client.ctrl_writes[-1] == 0
    client.disconnect.assert_awaited_once()


async def test_write_vmu_wrong_size_rejected(ble):
    with pytest.raises(ValueError):
        await BlueRetroDevice().async_write_vmu(ble, b"too short")


async def test_write_pak_targets_bank_offset(ble):
    data = bytes((i ^ 0x5A) & 0xFF for i in range(const.PAK_SIZE))
    client = MemClient()
    with _patch(client):
        await BlueRetroDevice().async_write_pak(ble, 2, data)
    base = 2 * const.PAK_SIZE
    assert client.buf[base : base + const.PAK_SIZE] == data
    assert client.crossed_block is False


async def test_read_pak_reads_bank_offset(ble):
    client = MemClient()
    base = 1 * const.PAK_SIZE
    expected = bytes((i + 3) & 0xFF for i in range(const.PAK_SIZE))
    client.buf[base : base + const.PAK_SIZE] = expected
    with _patch(client):
        got = await BlueRetroDevice().async_read_pak(ble, 1)
    assert got == expected


async def test_format_pak_writes_formatted_image(ble):
    client = MemClient()
    with _patch(client):
        await BlueRetroDevice().async_format_pak(ble, 0)
    # id-block bank-size marker present (byte 26 of header page at offset 32)
    assert client.buf[32 + 26] == 0x01


async def test_pak_bank_out_of_range(ble):
    with pytest.raises(ValueError):
        await BlueRetroDevice().async_read_pak(ble, 9)


# -- Files manager + OTA + input config use a separate fake --


class CmdClient:
    def __init__(self, listing=None):
        self.disconnect = AsyncMock()
        self.writes = []
        self._listing = list(listing or [])
        self.ota_data = bytearray()
        self.mtu_size = 247

    async def write_gatt_char(self, uuid, data, response=True):
        self.writes.append((uuid, bytes(data)))
        if uuid == const.CHAR_OTA_FW_DATA:
            self.ota_data += bytes(data)

    async def read_gatt_char(self, uuid):
        if uuid == const.CHAR_CMD:
            if self._listing:
                return self._listing.pop(0).encode("utf-8")
            return b""
        raise AssertionError(f"unexpected read {uuid}")


async def test_list_files(ble):
    client = CmdClient(listing=["GALE01", "SMSE52"])
    with _patch(client):
        files = await BlueRetroDevice().async_list_files(ble)
    assert files == ["GALE01", "SMSE52"]
    ops = [w[1][0] for w in client.writes]
    assert ops == [const.CMD_OPEN_DIR, const.CMD_GET_FILE, const.CMD_CLOSE_DIR]


async def test_delete_file_payload(ble):
    client = CmdClient()
    with _patch(client):
        await BlueRetroDevice().async_delete_file(ble, "GALE01")
    uuid, payload = client.writes[0]
    assert uuid == const.CHAR_CMD
    assert payload == bytes([const.CMD_DEL_FILE]) + b"GALE01"


async def test_ota_streams_then_ends(ble):
    fw = bytes(range(256)) * 5  # 1280 bytes
    client = CmdClient()
    with _patch(client):
        await BlueRetroDevice().async_ota_update(ble, fw)
    assert client.ota_data == fw
    cmd_ops = [w[1][0] for w in client.writes if w[0] == const.CHAR_CMD]
    assert cmd_ops[0] == const.CMD_OTA_START
    assert cmd_ops[-1] == const.CMD_OTA_END


async def test_ota_aborts_on_error(ble):
    from bleak.exc import BleakError

    fw = bytes(range(256))
    client = CmdClient()

    async def boom(uuid, data, response=True):
        client.writes.append((uuid, bytes(data)))
        if uuid == const.CHAR_OTA_FW_DATA:
            raise BleakError("link lost")

    client.write_gatt_char = boom
    with _patch(client), pytest.raises(RuntimeError):
        await BlueRetroDevice().async_ota_update(ble, fw)
    cmd_ops = [w[1][0] for w in client.writes if w[0] == const.CHAR_CMD]
    assert const.CMD_OTA_ABORT in cmd_ops


class InCfgClient:
    """Records input-config ctrl/data writes and serves a blob for reads."""

    def __init__(self, blob=b""):
        self.disconnect = AsyncMock()
        self.writes = []
        self._blob = blob

    async def write_gatt_char(self, uuid, data, response=True):
        self.writes.append((uuid, bytes(data)))

    async def read_gatt_char(self, uuid):
        if uuid == const.CHAR_IN_CFG_DATA:
            # parse last ctrl offset
            offset = 0
            for u, d in reversed(self.writes):
                if u == const.CHAR_IN_CFG_CTRL:
                    offset = struct.unpack("<HH", d)[1]
                    break
            return self._blob[offset : offset + const.IN_CFG_CHUNK]
        raise AssertionError(f"unexpected read {uuid}")


async def test_write_input_config_ctrl_and_data(ble):
    from blueretro_ble import InputMapping, encode_input_config

    maps = [InputMapping(src=1, dest=2), InputMapping(src=3, dest=4)]
    client = InCfgClient()
    with _patch(client):
        await BlueRetroDevice().async_write_input_config(ble, 5, maps)
    ctrl = [w for w in client.writes if w[0] == const.CHAR_IN_CFG_CTRL]
    data = [w for w in client.writes if w[0] == const.CHAR_IN_CFG_DATA]
    cfg_id, offset = struct.unpack("<HH", ctrl[0][1])
    assert cfg_id == 5 and offset == 0
    assert data[0][1] == encode_input_config(maps)


async def test_read_input_config_roundtrip(ble):
    from blueretro_ble import InputMapping, encode_input_config

    maps = [InputMapping(src=7, dest=8, max=100, scaling=1)]
    client = InCfgClient(blob=encode_input_config(maps))
    with _patch(client):
        got = await BlueRetroDevice().async_read_input_config(ble, 0)
    assert got == maps
