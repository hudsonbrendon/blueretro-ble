"""Command-line tool for hands-on use: `python -m blueretro_ble ...`.

The adapter is only reachable while idle (no controller connected).
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict

from bleak import BleakScanner

from .device import BlueRetroDevice
from .scanner import discover


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blueretro", description="Talk to a BlueRetro adapter over BLE"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="scan for nearby BlueRetro adapters")

    p_info = sub.add_parser("info", help="connect and print the adapter state")
    p_info.add_argument("address")

    p_reboot = sub.add_parser("reboot", help="reboot the adapter")
    p_reboot.add_argument("address")

    p_sleep = sub.add_parser("sleep", help="put the adapter into deep sleep")
    p_sleep.add_argument("address")

    return parser


async def _resolve(address: str):
    device = await BleakScanner.find_device_by_address(address, timeout=10.0)
    if device is None:
        raise SystemExit(f"BlueRetro {address} not found (powered on and idle?)")
    return device


async def _run(args: argparse.Namespace) -> None:
    if args.command == "scan":
        devices = await discover()
        if not devices:
            print("No BlueRetro adapters found.")
            return
        for d in devices:
            print(f"{d.address}  {d.name}")
        return

    device = await _resolve(args.address)
    br = BlueRetroDevice()
    if args.command == "info":
        state = await br.async_update(device)
        for key, value in asdict(state).items():
            print(f"{key:18} = {value!r}")
    elif args.command == "reboot":
        await br.async_reboot(device)
        print("reboot command sent")
    elif args.command == "sleep":
        await br.async_deep_sleep(device)
        print("deep-sleep command sent")


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
