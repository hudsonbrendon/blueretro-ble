import struct
from unittest.mock import AsyncMock, patch

import pytest

from blueretro_ble import const
from blueretro_ble.device import BlueRetroDevice


@pytest.fixture
def fake_ble_device():
    dev = AsyncMock()
    dev.address = "AA:BB:CC:DD:EE:FF"
    return dev


async def test_async_read_output_config(fake_ble_device):
    client = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=bytes([2, 3]))  # Keyboard, Both
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        device, accessory = await BlueRetroDevice().async_read_output_config(
            fake_ble_device, port=1
        )
    assert (device, accessory) == ("Keyboard", "Both")
    # Selected the requested port on the control characteristic.
    client.write_gatt_char.assert_any_await(
        const.CHAR_OUTPUT_CTRL, struct.pack("<H", 1), response=True
    )
    client.disconnect.assert_awaited_once()


async def test_async_set_output_config_writes_device_and_accessory(fake_ble_device):
    client = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=bytes([0, 0]))  # GamePad, None
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_set_output_config(
            fake_ble_device, port=2, device="Keyboard", accessory="Both"
        )
    # Selected the port (uint16) and wrote [device=2, accessory=3].
    client.write_gatt_char.assert_any_await(
        const.CHAR_OUTPUT_CTRL, struct.pack("<H", 2), response=True
    )
    client.write_gatt_char.assert_any_await(
        const.CHAR_OUTPUT_DATA, bytes([2, 3]), response=True
    )
    client.disconnect.assert_awaited_once()


async def test_async_set_output_config_preserves_unset_byte(fake_ble_device):
    client = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=bytes([1, 1]))  # GamePadAlt, Memory
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_set_output_config(
            fake_ble_device, accessory="Rumble"
        )
    # device byte preserved (1), accessory set to Rumble (2).
    client.write_gatt_char.assert_any_await(
        const.CHAR_OUTPUT_DATA, bytes([1, 2]), response=True
    )


async def test_async_set_output_config_rejects_unknown(fake_ble_device):
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=AsyncMock())
    ):
        with pytest.raises(ValueError):
            await BlueRetroDevice().async_set_output_config(
                fake_ble_device, device="Joystick"
            )


async def test_async_read_vmu_accumulates_chunks(fake_ble_device):
    # Serve the 128 KiB VMU in 244-byte chunks.
    chunk = bytes(range(256))[: const.FILE_CHUNK]
    remaining = {"n": const.VMU_SIZE}

    async def read(uuid):
        assert uuid == const.CHAR_FILE_DATA
        take = min(const.FILE_CHUNK, remaining["n"])
        remaining["n"] -= take
        return chunk[:take]

    client = AsyncMock()
    client.read_gatt_char = read
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        data = await BlueRetroDevice().async_read_vmu(fake_ble_device)

    assert len(data) == const.VMU_SIZE
    # Reset the file offset before and after the transfer.
    client.write_gatt_char.assert_any_await(
        const.CHAR_FILE_CTRL, struct.pack("<I", 0), response=True
    )
    client.disconnect.assert_awaited_once()
