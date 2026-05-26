"""Pure decoders for BlueRetro characteristic payloads."""

from __future__ import annotations

from .const import ACCESSORY_CFG, DEVICE_CFG, INQUIRY_MODE, MULTITAP_CFG, SYSTEM_CFG


def _label(table: tuple[str, ...], index: int | None) -> str | None:
    """Map a config byte to its label, or None if out of range/missing."""
    if index is None or index < 0 or index >= len(table):
        return None
    return table[index]


def decode_global_config(
    raw: bytes,
) -> tuple[str | None, str | None, str | None, int | None]:
    """Decode the global-config characteristic payload.

    Returns ``(system, multitap, inquiry_mode, memory_card_bank)``. Older
    firmware sends a shorter payload, so trailing fields come back as ``None``.
    The memory card bank is reported 1-based (byte value + 1).
    """
    system = _label(SYSTEM_CFG, raw[0]) if len(raw) >= 1 else None
    multitap = _label(MULTITAP_CFG, raw[1]) if len(raw) >= 2 else None
    inquiry = _label(INQUIRY_MODE, raw[2]) if len(raw) >= 3 else None
    bank = raw[3] + 1 if len(raw) >= 4 else None
    return system, multitap, inquiry, bank


def decode_output_config(raw: bytes) -> tuple[str | None, str | None]:
    """Decode a per-output config payload into ``(device, accessory)`` labels."""
    device = _label(DEVICE_CFG, raw[0]) if len(raw) >= 1 else None
    accessory = _label(ACCESSORY_CFG, raw[1]) if len(raw) >= 2 else None
    return device, accessory


def decode_bdaddr(raw: bytes) -> str | None:
    """Decode a 6-byte BD address (little-endian, byte 5 first)."""
    if len(raw) < 6:
        return None
    return ":".join(f"{raw[i]:02x}" for i in range(5, -1, -1))


def decode_string(raw: bytes) -> str | None:
    """Decode a UTF-8 string, stripping trailing NULs. Empty -> None."""
    text = raw.decode("utf-8", errors="replace").rstrip("\x00").strip()
    return text or None


def decode_abi(raw: bytes) -> int | None:
    """Decode a small integer carried in the first byte."""
    if not raw:
        return None
    return raw[0]
