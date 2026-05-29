"""High-level BlueRetro device operations over BLE."""

from __future__ import annotations

import logging
import struct
from collections.abc import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from . import const
from .gameid import lookup_game_name
from .memorycard import make_formatted_pak
from .models import BlueRetroState, InputMapping
from .protocol import (
    decode_abi,
    decode_bdaddr,
    decode_global_config,
    decode_input_config,
    decode_output_config,
    decode_string,
    encode_input_config,
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

    async def async_update(
        self, ble_device: BLEDevice, output_ports: int = 1
    ) -> BlueRetroState:
        """Connect, read all fields, disconnect. Never raises.

        ``output_ports`` controls how many output ports' configs are read in the
        single connection (clamped to 1..``const.MAX_OUTPUT``); the results land
        in ``state.ports`` and port 0 also mirrors into ``controller_mode`` /
        ``accessory`` for backward compatibility.
        """
        output_ports = max(1, min(int(output_ports), const.MAX_OUTPUT))
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
            ports: dict[int, tuple[str | None, str | None]] = {}
            for port in range(output_ports):
                ports[port] = await self._read_output(client, port)
            controller_mode, accessory = ports[0]
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
            controller_mode=controller_mode,
            accessory=accessory,
            ports=ports,
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

    async def _read_output(
        self, client: BleakClient, port: int
    ) -> tuple[str | None, str | None]:
        try:
            await client.write_gatt_char(
                const.CHAR_OUTPUT_CTRL, struct.pack("<H", port), response=True
            )
            raw = await client.read_gatt_char(const.CHAR_OUTPUT_DATA)
            return decode_output_config(raw)
        except (BleakError, TimeoutError, OSError, Exception) as err:  # noqa: BLE001
            _LOGGER.debug("BlueRetro output config read failed: %s", err)
            return (None, None)

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

    async def async_read_output_config(
        self, ble_device: BLEDevice, port: int = 0
    ) -> tuple[str | None, str | None]:
        """Read a port's output config as ``(device, accessory)`` labels."""
        client = await self._connect(ble_device)
        try:
            return await self._read_output(client, port)
        finally:
            await client.disconnect()

    async def async_read_outputs(
        self, ble_device: BLEDevice, ports: int = const.MAX_OUTPUT
    ) -> dict[int, tuple[str | None, str | None]]:
        """Read several ports' output configs in one connection.

        Returns a ``{port: (device, accessory)}`` mapping for ports
        ``0..ports-1`` (``ports`` clamped to 1..``const.MAX_OUTPUT``).
        """
        ports = max(1, min(int(ports), const.MAX_OUTPUT))
        client = await self._connect(ble_device)
        try:
            return {p: await self._read_output(client, p) for p in range(ports)}
        finally:
            await client.disconnect()

    async def async_set_output_config(
        self,
        ble_device: BLEDevice,
        port: int = 0,
        *,
        device: str | None = None,
        accessory: str | None = None,
    ) -> None:
        """Set a port's device mode and/or accessory.

        ``device`` is a ``DEVICE_CFG`` label, ``accessory`` an ``ACCESSORY_CFG``
        label; ``None`` leaves that byte unchanged. Raises ``ValueError`` for
        unknown labels. Writes 2 bytes (`[device, accessory]`); no reboot needed.
        """
        dev_idx = None
        if device is not None:
            if device not in const.DEVICE_CFG:
                raise ValueError(f"invalid device mode {device!r}")
            dev_idx = const.DEVICE_CFG.index(device)
        acc_idx = None
        if accessory is not None:
            if accessory not in const.ACCESSORY_CFG:
                raise ValueError(f"invalid accessory {accessory!r}")
            acc_idx = const.ACCESSORY_CFG.index(accessory)

        client = await self._connect(ble_device)
        try:
            await client.write_gatt_char(
                const.CHAR_OUTPUT_CTRL, struct.pack("<H", port), response=True
            )
            current = bytearray(
                await client.read_gatt_char(const.CHAR_OUTPUT_DATA)
            )
            while len(current) < 2:
                current.append(0)
            if dev_idx is not None:
                current[0] = dev_idx
            if acc_idx is not None:
                current[1] = acc_idx
            # Re-select the output, then write the new config.
            await client.write_gatt_char(
                const.CHAR_OUTPUT_CTRL, struct.pack("<H", port), response=True
            )
            await client.write_gatt_char(
                const.CHAR_OUTPUT_DATA, bytes(current[:2]), response=True
            )
        finally:
            await client.disconnect()

    # -- File transport (memory card buffer: flat 128 KiB of 32 x 4 KiB blocks) --

    async def _read_file(
        self, client: BleakClient, offset: int, size: int
    ) -> bytes:
        """Read ``size`` bytes from the memory-card buffer at ``offset``."""
        mtu = getattr(client, "mtu_size", None)
        await client.write_gatt_char(
            const.CHAR_FILE_CTRL, struct.pack("<I", offset), response=True
        )
        data = bytearray()
        try:
            while len(data) < size:
                chunk = await client.read_gatt_char(const.CHAR_FILE_DATA)
                if not chunk:
                    break
                data += chunk
        except (BleakError, TimeoutError, OSError) as err:
            raise RuntimeError(
                f"file read failed after {len(data)} bytes (mtu={mtu}): {err}"
            ) from err
        # Reset the file cursor for the next transfer.
        await client.write_gatt_char(
            const.CHAR_FILE_CTRL, struct.pack("<I", 0), response=True
        )
        return bytes(data[:size])

    async def _write_file(
        self,
        client: BleakClient,
        offset: int,
        data: bytes,
        progress: Callable[[int], None] | None = None,
    ) -> None:
        """Write ``data`` to the memory-card buffer starting at ``offset``.

        Chunks are MTU-capped and block-aligned: a write never crosses a 4 KiB
        block boundary (firmware requirement). The firmware auto-advances its
        own cursor, so the start offset is written once up front.
        """
        mtu = getattr(client, "mtu_size", None)
        await client.write_gatt_char(
            const.CHAR_FILE_CTRL, struct.pack("<I", offset), response=True
        )
        pos = 0
        total = len(data)
        try:
            while pos < total:
                # Bytes left until the next 4 KiB boundary, capped at the MTU.
                next_block = (pos // const.MC_BLOCK + 1) * const.MC_BLOCK
                size = min(next_block - pos, const.FILE_CHUNK, total - pos)
                await client.write_gatt_char(
                    const.CHAR_FILE_DATA, data[pos : pos + size], response=True
                )
                pos += size
                if progress is not None:
                    progress(round(pos / total * 100))
        except (BleakError, TimeoutError, OSError) as err:
            raise RuntimeError(
                f"file write failed after {pos} bytes (mtu={mtu}): {err}"
            ) from err
        # Reset the file cursor for the next transfer.
        await client.write_gatt_char(
            const.CHAR_FILE_CTRL, struct.pack("<I", 0), response=True
        )

    async def async_read_vmu(self, ble_device: BLEDevice) -> bytes:
        """Download the emulated Dreamcast VMU image (128 KiB).

        Read-only: dumps the adapter's current VMU. The adapter must be idle.
        Raises ``RuntimeError`` if the adapter rejects the chunked read (e.g.
        when the negotiated MTU is too small).
        """
        client = await self._connect(ble_device)
        try:
            return await self._read_file(client, 0, const.VMU_SIZE)
        finally:
            await client.disconnect()

    async def async_write_vmu(
        self,
        ble_device: BLEDevice,
        data: bytes,
        progress: Callable[[int], None] | None = None,
    ) -> None:
        """Upload a Dreamcast VMU image (exactly 128 KiB).

        Overwrites the emulated VMU. Destructive. Requires a large negotiated
        MTU; the transfer fails (``RuntimeError``) otherwise. Power the console
        off first — the buffer is read live by the console.
        """
        if len(data) != const.VMU_SIZE:
            raise ValueError(
                f"VMU image must be exactly {const.VMU_SIZE} bytes"
            )
        client = await self._connect(ble_device)
        try:
            await self._write_file(client, 0, data, progress)
        finally:
            await client.disconnect()

    @staticmethod
    def _pak_offset(bank: int) -> int:
        if not 0 <= bank < const.PAK_BANKS:
            raise ValueError(f"pak bank must be 0..{const.PAK_BANKS - 1}")
        return bank * const.PAK_SIZE

    async def async_read_pak(self, ble_device: BLEDevice, bank: int) -> bytes:
        """Download an N64 Controller Pak bank (32 KiB, bank 0..3)."""
        offset = self._pak_offset(bank)
        client = await self._connect(ble_device)
        try:
            return await self._read_file(client, offset, const.PAK_SIZE)
        finally:
            await client.disconnect()

    async def async_write_pak(
        self,
        ble_device: BLEDevice,
        bank: int,
        data: bytes,
        progress: Callable[[int], None] | None = None,
    ) -> None:
        """Upload an N64 Controller Pak bank (exactly 32 KiB, bank 0..3)."""
        offset = self._pak_offset(bank)
        if len(data) != const.PAK_SIZE:
            raise ValueError(
                f"pak image must be exactly {const.PAK_SIZE} bytes"
            )
        client = await self._connect(ble_device)
        try:
            await self._write_file(client, offset, data, progress)
        finally:
            await client.disconnect()

    async def async_format_pak(self, ble_device: BLEDevice, bank: int) -> None:
        """Format an N64 Controller Pak bank (writes a blank formatted image)."""
        offset = self._pak_offset(bank)
        data = make_formatted_pak()
        client = await self._connect(ble_device)
        try:
            await self._write_file(client, offset, data)
        finally:
            await client.disconnect()

    # -- Config files (flash FAT filesystem, via CHAR_CMD) --

    async def async_list_files(self, ble_device: BLEDevice) -> list[str]:
        """List the adapter's stored config files (per-GameID configs)."""
        client = await self._connect(ble_device)
        try:
            await client.write_gatt_char(
                const.CHAR_CMD, bytes([const.CMD_OPEN_DIR]), response=True
            )
            await client.write_gatt_char(
                const.CHAR_CMD, bytes([const.CMD_GET_FILE]), response=True
            )
            files: list[str] = []
            while True:
                value = await client.read_gatt_char(const.CHAR_CMD)
                if not value:
                    break
                files.append(value.decode("utf-8", errors="replace"))
            await client.write_gatt_char(
                const.CHAR_CMD, bytes([const.CMD_CLOSE_DIR]), response=True
            )
            return files
        finally:
            await client.disconnect()

    async def async_delete_file(
        self, ble_device: BLEDevice, name: str
    ) -> None:
        """Delete a stored config file by name."""
        payload = bytes([const.CMD_DEL_FILE]) + name.encode("utf-8")
        client = await self._connect(ble_device)
        try:
            await client.write_gatt_char(
                const.CHAR_CMD, payload, response=True
            )
        finally:
            await client.disconnect()

    # -- OTA firmware update --

    async def async_ota_update(
        self,
        ble_device: BLEDevice,
        firmware: bytes,
        progress: Callable[[int], None] | None = None,
    ) -> None:
        """Flash a firmware image over the air (``BlueRetro_*.bin`` contents).

        Streams the image in MTU-sized chunks, then reboots into it. On any
        error the OTA is aborted. Requires a large negotiated MTU; risky over
        BlueZ. Destructive: replaces the running firmware.
        """
        if not firmware:
            raise ValueError("firmware image is empty")
        client = await self._connect(ble_device)
        try:
            await client.write_gatt_char(
                const.CHAR_CMD, bytes([const.CMD_OTA_START]), response=True
            )
            try:
                pos = 0
                total = len(firmware)
                while pos < total:
                    size = min(const.FILE_CHUNK, total - pos)
                    await client.write_gatt_char(
                        const.CHAR_OTA_FW_DATA,
                        firmware[pos : pos + size],
                        response=True,
                    )
                    pos += size
                    if progress is not None:
                        progress(round(pos / total * 100))
                await client.write_gatt_char(
                    const.CHAR_CMD, bytes([const.CMD_OTA_END]), response=True
                )
            except (BleakError, TimeoutError, OSError) as err:
                await client.write_gatt_char(
                    const.CHAR_CMD,
                    bytes([const.CMD_OTA_ABORT]),
                    response=True,
                )
                raise RuntimeError(f"OTA failed after {pos} bytes: {err}") from err
        finally:
            await client.disconnect()

    # -- Input mapping (advanced config) --

    async def async_read_input_config(
        self, ble_device: BLEDevice, cfg_id: int
    ) -> list[InputMapping]:
        """Read the advanced input mappings for a config slot."""
        client = await self._connect(ble_device)
        try:
            blob = bytearray()
            offset = 0
            while True:
                await client.write_gatt_char(
                    const.CHAR_IN_CFG_CTRL,
                    struct.pack("<HH", cfg_id, offset),
                    response=True,
                )
                chunk = await client.read_gatt_char(const.CHAR_IN_CFG_DATA)
                blob += chunk
                if len(chunk) < const.IN_CFG_CHUNK:
                    break
                offset += const.IN_CFG_CHUNK
            return decode_input_config(bytes(blob))
        finally:
            await client.disconnect()

    async def async_write_input_config(
        self,
        ble_device: BLEDevice,
        cfg_id: int,
        mappings: list[InputMapping],
    ) -> None:
        """Write advanced input mappings to a config slot.

        ``src``/``dest`` in each mapping are raw BlueRetro button/axis ids.
        """
        blob = encode_input_config(mappings)
        client = await self._connect(ble_device)
        try:
            offset = 0
            while True:
                await client.write_gatt_char(
                    const.CHAR_IN_CFG_CTRL,
                    struct.pack("<HH", cfg_id, offset),
                    response=True,
                )
                await client.write_gatt_char(
                    const.CHAR_IN_CFG_DATA,
                    blob[offset : offset + const.IN_CFG_CHUNK],
                    response=True,
                )
                offset += const.IN_CFG_CHUNK
                if offset >= len(blob):
                    break
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
