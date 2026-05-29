from unittest.mock import AsyncMock, patch

import pytest

from blueretro_ble import const
from blueretro_ble.device import BlueRetroDevice


class FakeClient:
    """Minimal stand-in for a connected BleakClient."""

    def __init__(self):
        self._last_cmd = None
        self.disconnect = AsyncMock()
        self.is_connected = True

    async def read_gatt_char(self, uuid):
        if uuid == const.CHAR_ABI:
            return bytes([0x02])
        if uuid == const.CHAR_APP:
            return b"v1.8.1"
        if uuid == const.CHAR_BDADDR:
            return bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66])
        if uuid == const.CHAR_GLOBAL_CFG:
            # system=PS2 (17), multitap=None (0), inquiry=Manual (1), bank byte 0 -> 1
            return bytes([17, 0, 1, 0])
        if uuid == const.CHAR_OUTPUT_DATA:
            # device=GamePad (0), accessory=Memory (1)
            return bytes([0, 1])
        if uuid == const.CHAR_CMD:
            if self._last_cmd == const.CMD_GET_GAMEID:
                return b"GALE01"
            if self._last_cmd == const.CMD_GET_CFG_SRC:
                return bytes([0x01])
            if self._last_cmd == const.CMD_GET_FW_NAME:
                return b"playstation hw1"
        raise AssertionError(f"unexpected read {uuid}")

    async def write_gatt_char(self, uuid, data, response=True):
        if uuid == const.CHAR_CMD:
            self._last_cmd = data[0]
        elif uuid == const.CHAR_OUTPUT_CTRL:
            self._selected_output = data
        else:
            raise AssertionError(f"unexpected write {uuid}")


@pytest.fixture
def fake_ble_device():
    dev = AsyncMock()
    dev.address = "AA:BB:CC:DD:EE:FF"
    dev.name = "BlueRetro_abcd"
    return dev


async def test_async_update_reads_all_fields(fake_ble_device):
    client = FakeClient()
    with (
        patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)),
        patch("blueretro_ble.device.lookup_game_name", return_value="Super Smash Bros. Melee"),
    ):
        device = BlueRetroDevice()
        state = await device.async_update(fake_ble_device)

    assert state.available is True
    assert state.abi_version == 2
    assert state.fw_version == "v1.8.1"
    assert state.bdaddr == "66:55:44:33:22:11"
    assert state.game_id == "GALE01"
    assert state.cfg_src == 1
    assert state.game_name == "Super Smash Bros. Melee"
    assert state.fw_name == "playstation hw1"
    assert state.system == "PS2"
    assert state.multitap == "None"
    assert state.inquiry_mode == "Manual"
    assert state.memory_card_bank == 1
    assert state.controller_mode == "GamePad"
    assert state.accessory == "Memory"
    client.disconnect.assert_awaited_once()


async def test_async_update_tolerates_missing_global_config(fake_ble_device):
    """Older firmware without global config / fw_name still reads core fields."""
    client = FakeClient()

    async def only_core(uuid):
        if uuid == const.CHAR_ABI:
            return bytes([0x02])
        if uuid == const.CHAR_APP:
            return b"v1.8.1"
        if uuid == const.CHAR_BDADDR:
            return bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66])
        if uuid == const.CHAR_CMD and client._last_cmd == const.CMD_GET_GAMEID:
            return b"GALE01"
        if uuid == const.CHAR_CMD and client._last_cmd == const.CMD_GET_CFG_SRC:
            return bytes([0x01])
        raise Exception("characteristic not supported")

    client.read_gatt_char = only_core
    with (
        patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)),
        patch("blueretro_ble.device.lookup_game_name", return_value=None),
    ):
        state = await BlueRetroDevice().async_update(fake_ble_device)

    assert state.available is True
    assert state.fw_version == "v1.8.1"
    assert state.system is None
    assert state.fw_name is None


async def test_async_update_disconnects_even_on_read_error(fake_ble_device):
    client = FakeClient()
    client.read_gatt_char = AsyncMock(side_effect=Exception("boom"))
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        device = BlueRetroDevice()
        state = await device.async_update(fake_ble_device)

    assert state.available is False
    client.disconnect.assert_awaited_once()


async def test_async_update_default_reads_only_port_0(fake_ble_device):
    """With no port count given, only port 0 lands in ``ports``."""
    client = FakeClient()
    with (
        patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)),
        patch("blueretro_ble.device.lookup_game_name", return_value=None),
    ):
        state = await BlueRetroDevice().async_update(fake_ble_device)

    assert set(state.ports) == {0}
    assert state.ports[0] == ("GamePad", "Memory")
    # Port 0 still mirrors into the legacy fields.
    assert state.controller_mode == "GamePad"
    assert state.accessory == "Memory"


class MultiPortClient(FakeClient):
    """Returns a distinct output config per selected port."""

    import struct as _struct

    _PORT_CFG = {
        0: bytes([0, 1]),  # GamePad, Memory
        1: bytes([1, 2]),  # GamePadAlt, Rumble
        2: bytes([2, 0]),  # Keyboard, None
    }

    async def read_gatt_char(self, uuid):
        if uuid == const.CHAR_OUTPUT_DATA:
            port = self._struct.unpack("<H", self._selected_output)[0]
            return self._PORT_CFG.get(port, bytes([0, 0]))
        return await super().read_gatt_char(uuid)


async def test_async_update_reads_multiple_ports(fake_ble_device):
    client = MultiPortClient()
    with (
        patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)),
        patch("blueretro_ble.device.lookup_game_name", return_value=None),
    ):
        state = await BlueRetroDevice().async_update(fake_ble_device, output_ports=3)

    assert state.ports == {
        0: ("GamePad", "Memory"),
        1: ("GamePadAlt", "Rumble"),
        2: ("Keyboard", "None"),
    }
    assert (state.controller_mode, state.accessory) == ("GamePad", "Memory")
    client.disconnect.assert_awaited_once()


async def test_async_update_clamps_port_count(fake_ble_device):
    client = MultiPortClient()
    with (
        patch("blueretro_ble.device.establish_connection", AsyncMock(return_value=client)),
        patch("blueretro_ble.device.lookup_game_name", return_value=None),
    ):
        state = await BlueRetroDevice().async_update(fake_ble_device, output_ports=999)

    assert len(state.ports) == const.MAX_OUTPUT


async def test_async_read_outputs_helper(fake_ble_device):
    client = MultiPortClient()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        result = await BlueRetroDevice().async_read_outputs(fake_ble_device, ports=2)

    assert result == {0: ("GamePad", "Memory"), 1: ("GamePadAlt", "Rumble")}
    client.disconnect.assert_awaited_once()


async def test_async_update_connection_failure_returns_unavailable(fake_ble_device):
    from bleak.exc import BleakError

    with patch(
        "blueretro_ble.device.establish_connection",
        AsyncMock(side_effect=BleakError("busy")),
    ):
        device = BlueRetroDevice()
        state = await device.async_update(fake_ble_device)

    assert state == device.last_state
    assert state.available is False
