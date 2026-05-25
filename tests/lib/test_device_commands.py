from unittest.mock import AsyncMock, patch

import pytest

from blueretro_ble import const
from blueretro_ble.device import BlueRetroDevice


@pytest.fixture
def fake_ble_device():
    dev = AsyncMock()
    dev.address = "AA:BB:CC:DD:EE:FF"
    return dev


async def test_async_reboot_writes_reset_command(fake_ble_device):
    client = AsyncMock()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_reboot(fake_ble_device)

    client.write_gatt_char.assert_awaited_once_with(
        const.CHAR_CMD, bytes([const.CMD_SYS_RESET]), response=True
    )
    client.disconnect.assert_awaited_once()


async def test_async_deep_sleep_writes_sleep_command(fake_ble_device):
    client = AsyncMock()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_deep_sleep(fake_ble_device)

    client.write_gatt_char.assert_awaited_once_with(
        const.CHAR_CMD, bytes([const.CMD_SYS_DEEP_SLEEP]), response=True
    )
    client.disconnect.assert_awaited_once()


async def test_async_factory_reset_writes_factory_command(fake_ble_device):
    client = AsyncMock()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_factory_reset(fake_ble_device)

    client.write_gatt_char.assert_awaited_once_with(
        const.CHAR_CMD, bytes([const.CMD_SYS_FACTORY]), response=True
    )
    client.disconnect.assert_awaited_once()


async def test_async_set_global_config_writes_and_reboots(fake_ble_device):
    client = AsyncMock()
    # Current global config: system=Auto(0), multitap=None(0), inquiry=Auto(0), bank0
    client.read_gatt_char = AsyncMock(return_value=bytes([0, 0, 0, 0]))
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_set_global_config(
            fake_ble_device, system="PS2", inquiry_mode="Manual", memory_card_bank=3
        )

    # First write: the modified global config (system=17, multitap untouched=0,
    # inquiry=1, bank byte = 3-1 = 2).
    cfg_call = client.write_gatt_char.await_args_list[0]
    assert cfg_call.args[0] == const.CHAR_GLOBAL_CFG
    assert cfg_call.args[1] == bytes([17, 0, 1, 2])
    # Second write: reboot to apply.
    reboot_call = client.write_gatt_char.await_args_list[1]
    assert reboot_call.args == (const.CHAR_CMD, bytes([const.CMD_SYS_RESET]))
    client.disconnect.assert_awaited_once()


async def test_async_set_global_config_rejects_unknown_value(fake_ble_device):
    client = AsyncMock()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        with pytest.raises(ValueError):
            await BlueRetroDevice().async_set_global_config(
                fake_ble_device, system="NotAConsole"
            )
