#!/usr/bin/env python3
"""Read a real BlueRetro adapter over BLE and print everything (read-only).

Usage:
    .venv/bin/python scripts/validate_hardware.py [BD_ADDRESS]

Scans for a BlueRetro adapter (must be powered on and IDLE — no controller
connected), connects, and prints the decoded state plus the raw global-config
bytes so the protocol decoding can be verified against the device's real
settings. Performs NO writes (no reboot, no config change, no factory reset).

macOS note: a bare Python process needs Bluetooth permission. If this crashes
immediately (SIGABRT / "NSBluetoothAlwaysUsageDescription"), grant your terminal
Bluetooth access in System Settings > Privacy & Security > Bluetooth, or run it
once and approve the system prompt.
"""

from __future__ import annotations

import asyncio
import sys

from bleak import BleakClient, BleakScanner

from blueretro_ble import BlueRetroDevice, const, supports


async def find_device(address: str | None):
    print("Escaneando 12s (adaptador precisa estar ligado e ocioso)...")
    found = await BleakScanner.discover(timeout=12.0, return_adv=True)
    for addr, (dev, adv) in found.items():
        if address and addr.upper() != address.upper():
            continue

        class _Info:
            name = adv.local_name or dev.name
            service_uuids = adv.service_uuids or []

        if supports(_Info) or (address and addr.upper() == address.upper()):
            print(f"Encontrado: {addr}  name={_Info.name!r}  rssi={adv.rssi}")
            return dev
    return None


async def main():
    address = sys.argv[1] if len(sys.argv) > 1 else None
    dev = await find_device(address)
    if dev is None:
        print("Nenhum BlueRetro encontrado. Ligado? Sem controle conectado?")
        return

    print("\n--- Leitura via blueretro_ble.BlueRetroDevice.async_update ---")
    state = await BlueRetroDevice().async_update(dev)
    for field in (
        "available",
        "fw_version",
        "fw_name",
        "abi_version",
        "bdaddr",
        "game_id",
        "game_name",
        "cfg_src",
        "system",
        "multitap",
        "inquiry_mode",
        "memory_card_bank",
    ):
        print(f"  {field:18} = {getattr(state, field)!r}")

    print("\n--- Bytes crus do global config (para conferir o decode) ---")
    try:
        async with BleakClient(dev) as client:
            raw = await client.read_gatt_char(const.CHAR_GLOBAL_CFG)
            print(f"  CHAR_GLOBAL_CFG (a01) = {bytes(raw).hex(' ')}  (len={len(raw)})")
            print(
                "  interpretação: byte0=system, byte1=multitap, "
                "byte2=inquiry, byte3=bank(0-based)"
            )
    except Exception as err:  # noqa: BLE001
        print(f"  (não consegui ler os bytes crus: {err})")


if __name__ == "__main__":
    asyncio.run(main())
