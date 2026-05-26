"""High-level BlueRetro device operations over BLE."""

from __future__ import annotations

import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from . import const
from .gameid import lookup_game_name
from .models import BlueRetroState
from .protocol import (
    decode_abi,
    decode_bdaddr,
    decode_global_config,
    decode_string,
)

_LOGGER = logging.getLogger(__name__)


class BlueRetroDevice:
    """Connects to a BlueRetro adapter to read state and send commands."""

    def __init__(self) -> None:
        self.last_state = BlueRetroState()

    async def _connect(self, ble_device: BLEDevice) -> BleakClient:
        return await establish_connection(
            BleakClient, ble_device, ble_device.address
        )

    async def async_update(self, ble_device: BLEDevice) -> BlueRetroState:
        """Connect, read all fields, disconnect. Never raises."""
        try:
            client = await self._connect(ble_device)
        except (BleakError, TimeoutError, OSError) as err:
            _LOGGER.debug("BlueRetro connect failed: %s", err)
            self.last_state = BlueRetroState(available=False)
            return self.last_state

        try:
            abi = decode_abi(await client.read_gatt_char(const.CHAR_ABI))
            fw = decode_string(await client.read_gatt_char(const.CHAR_APP))
            bdaddr = decode_bdaddr(await client.read_gatt_char(const.CHAR_BDADDR))
            game_id = decode_string(
                await self._command(client, const.CMD_GET_GAMEID)
            )
            cfg_src = decode_abi(
                await self._command(client, const.CMD_GET_CFG_SRC)
            )
            # Best-effort extras: never fail the core read if firmware lacks them.
            system, multitap, inquiry_mode, memory_card_bank = (
                await self._read_global_config(client)
            )
            fw_name = await self._read_fw_name(client)
        except (BleakError, TimeoutError, OSError, Exception) as err:  # noqa: BLE001
            _LOGGER.debug("BlueRetro read failed: %s", err)
            self.last_state = BlueRetroState(available=False)
            return self.last_state
        finally:
            await client.disconnect()

        state = BlueRetroState(
            available=True,
            fw_version=fw,
            fw_name=fw_name,
            abi_version=abi,
            bdaddr=bdaddr,
            game_id=game_id,
            cfg_src=cfg_src,
            game_name=lookup_game_name(game_id),
            system=system,
            multitap=multitap,
            inquiry_mode=inquiry_mode,
            memory_card_bank=memory_card_bank,
        )
        self.last_state = state
        return state

    async def _read_global_config(
        self, client: BleakClient
    ) -> tuple[str | None, str | None, str | None, int | None]:
        try:
            raw = await client.read_gatt_char(const.CHAR_GLOBAL_CFG)
            return decode_global_config(raw)
        except (BleakError, TimeoutError, OSError, Exception) as err:  # noqa: BLE001
            _LOGGER.debug("BlueRetro global config read failed: %s", err)
            return (None, None, None, None)

    async def _read_fw_name(self, client: BleakClient) -> str | None:
        try:
            return decode_string(
                await self._command(client, const.CMD_GET_FW_NAME)
            )
        except (BleakError, TimeoutError, OSError, Exception) as err:  # noqa: BLE001
            _LOGGER.debug("BlueRetro firmware name read failed: %s", err)
            return None

    async def _command(self, client: BleakClient, command: int) -> bytes:
        """Write a command byte to CHAR_CMD then read the response."""
        await client.write_gatt_char(const.CHAR_CMD, bytes([command]), response=True)
        return await client.read_gatt_char(const.CHAR_CMD)

    async def async_reboot(self, ble_device: BLEDevice) -> None:
        """Reboot the adapter."""
        await self._send_command(ble_device, const.CMD_SYS_RESET)

    async def async_deep_sleep(self, ble_device: BLEDevice) -> None:
        """Put the adapter into deep sleep."""
        await self._send_command(ble_device, const.CMD_SYS_DEEP_SLEEP)

    async def async_factory_reset(self, ble_device: BLEDevice) -> None:
        """Factory-reset the adapter (erases all configuration). Destructive."""
        await self._send_command(ble_device, const.CMD_SYS_FACTORY)

    async def async_set_global_config(
        self,
        ble_device: BLEDevice,
        *,
        system: str | None = None,
        multitap: str | None = None,
        inquiry_mode: str | None = None,
        memory_card_bank: int | None = None,
        reboot: bool = True,
    ) -> None:
        """Update selected global-config fields, then reboot to apply.

        Each field is a label from the matching enum (``system="PS2"``); ``None``
        leaves that byte unchanged. Raises ``ValueError`` for unknown labels.
        Changes only take effect after a reboot (``reboot=True`` by default).
        """
        # Validate before connecting.
        overrides: dict[int, int] = {}
        for idx, table, label in (
            (0, const.SYSTEM_CFG, system),
            (1, const.MULTITAP_CFG, multitap),
            (2, const.INQUIRY_MODE, inquiry_mode),
        ):
            if label is None:
                continue
            if label not in table:
                raise ValueError(f"invalid global config value {label!r}")
            overrides[idx] = table.index(label)
        if memory_card_bank is not None:
            overrides[3] = max(0, int(memory_card_bank) - 1)

        client = await self._connect(ble_device)
        try:
            current = bytearray(
                await client.read_gatt_char(const.CHAR_GLOBAL_CFG)
            )
            for idx, value in overrides.items():
                if idx >= len(current):
                    raise ValueError(
                        "firmware global config is too short for this field"
                    )
                current[idx] = value
            await client.write_gatt_char(
                const.CHAR_GLOBAL_CFG, bytes(current), response=True
            )
            if reboot:
                await client.write_gatt_char(
                    const.CHAR_CMD, bytes([const.CMD_SYS_RESET]), response=True
                )
        finally:
            await client.disconnect()

    async def _send_command(self, ble_device: BLEDevice, command: int) -> None:
        client = await self._connect(ble_device)
        try:
            await client.write_gatt_char(
                const.CHAR_CMD, bytes([command]), response=True
            )
        finally:
            await client.disconnect()
