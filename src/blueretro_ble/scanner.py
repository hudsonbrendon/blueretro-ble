"""Detect and discover BlueRetro adapters over BLE."""

from __future__ import annotations

from typing import Protocol

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .const import NAME_PREFIX, SERVICE_UUID


class _AdvertisementLike(Protocol):
    name: str | None
    service_uuids: list[str]


def supports(info: _AdvertisementLike) -> bool:
    """True if the advertisement looks like a BlueRetro adapter.

    Duck-typed: accepts anything exposing ``.name`` (str | None) and
    ``.service_uuids`` (list[str]) — including Home Assistant's
    ``BluetoothServiceInfoBleak``.
    """
    name = info.name or ""
    if name.startswith(NAME_PREFIX):
        return True
    return SERVICE_UUID.lower() in {u.lower() for u in info.service_uuids}


async def discover(timeout: float = 5.0) -> list[BLEDevice]:
    """Scan for nearby BlueRetro adapters (idle, no controller connected)."""
    discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)
    found: list[BLEDevice] = []
    for device, adv in discovered.values():
        name = adv.local_name or device.name
        if supports(_Advertisement(name, adv.service_uuids or [])):
            found.append(device)
    return found


class _Advertisement:
    """Adapt a bleak advertisement to the ``supports`` predicate."""

    def __init__(self, name: str | None, service_uuids: list[str]) -> None:
        self.name = name
        self.service_uuids = service_uuids
