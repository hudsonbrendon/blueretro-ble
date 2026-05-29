"""Pure decoders for BlueRetro characteristic payloads."""

from __future__ import annotations

from .const import (
    ACCESSORY_CFG,
    DEVICE_CFG,
    INQUIRY_MODE,
    MAX_MAPPINGS,
    MULTITAP_CFG,
    SYSTEM_CFG,
)
from .models import InputMapping


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


def encode_input_config(mappings: list[InputMapping]) -> bytes:
    """Encode input mappings into the CHAR_IN_CFG_DATA blob.

    Layout: ``[0, 0, n]`` then ``n`` 8-byte entries
    ``[src, dest, dest_id, max, threshold, deadzone, turbo,
    (scaling & 0x0F) | (diag_scaling << 4)]``. Raises ``ValueError`` if there
    are more than ``MAX_MAPPINGS`` entries or any byte is out of 0..255.
    """
    if len(mappings) > MAX_MAPPINGS:
        raise ValueError(f"at most {MAX_MAPPINGS} mappings allowed")
    out = bytearray([0, 0, len(mappings)])
    for m in mappings:
        packed = (m.scaling & 0x0F) | ((m.diag_scaling & 0x0F) << 4)
        entry = (
            m.src,
            m.dest,
            m.dest_id,
            m.max,
            m.threshold,
            m.deadzone,
            m.turbo,
            packed,
        )
        for value in entry:
            if not 0 <= value <= 255:
                raise ValueError(f"input mapping byte out of range: {value}")
        out += bytes(entry)
    return bytes(out)


def decode_input_config(raw: bytes) -> list[InputMapping]:
    """Decode a CHAR_IN_CFG_DATA blob into input mappings (inverse of encode)."""
    if len(raw) < 3:
        return []
    count = raw[2]
    mappings: list[InputMapping] = []
    for i in range(count):
        base = 3 + i * 8
        if base + 8 > len(raw):
            break
        e = raw[base : base + 8]
        mappings.append(
            InputMapping(
                src=e[0],
                dest=e[1],
                dest_id=e[2],
                max=e[3],
                threshold=e[4],
                deadzone=e[5],
                turbo=e[6],
                scaling=e[7] & 0x0F,
                diag_scaling=(e[7] >> 4) & 0x0F,
            )
        )
    return mappings
