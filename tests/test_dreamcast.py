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
