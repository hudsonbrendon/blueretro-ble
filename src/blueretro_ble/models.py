"""State container for a BlueRetro device."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class VmuSave:
    """One file in a Dreamcast VMU directory."""

    name: str
    kind: str  # "data" (save) or "game" (VMU mini-game)
    blocks: int
    saved: datetime | None = None


@dataclass(slots=True)
class BlueRetroState:
    """Snapshot of a BlueRetro adapter read over BLE."""

    available: bool = False
    fw_version: str | None = None
    fw_name: str | None = None
    abi_version: int | None = None
    bdaddr: str | None = None
    game_id: str | None = None
    game_name: str | None = None
    cfg_src: int | None = None
    # ``cfg_src`` as a label from ``const.CFG_SRC`` ("Default" / "Game ID").
    config_source: str | None = None
    # Global config (read from CHAR_GLOBAL_CFG)
    system: str | None = None
    multitap: str | None = None
    inquiry_mode: str | None = None
    memory_card_bank: int | None = None
    # Output config for port 1 (read from CHAR_OUTPUT_DATA). Kept for backward
    # compatibility; mirrors ``ports[0]``.
    controller_mode: str | None = None
    accessory: str | None = None
    # Output config per port, keyed by 0-based port index, each value a
    # ``(device, accessory)`` label pair. Populated by ``async_update`` for as
    # many ports as the caller requests (default: just port 0).
    ports: dict[int, tuple[str | None, str | None]] = field(default_factory=dict)
    # Dreamcast with an emulated VMU (accessory Memory/Both): its save files and
    # free blocks, read from the card's directory on every update. ``None``
    # when there is no VMU or the card is unformatted.
    vmu_saves: list[VmuSave] | None = None
    vmu_free_blocks: int | None = None


@dataclass(slots=True)
class InputMapping:
    """One advanced-config input mapping entry (8 bytes on the wire).

    All fields are raw values matching BlueRetro's advanced config:
    ``src``/``dest`` are button/axis ids, ``dest_id`` the destination output
    index, ``max``/``threshold``/``deadzone`` scaling parameters, ``turbo`` the
    turbo mask, and ``scaling``/``diag_scaling`` 4-bit response-curve selectors.
    """

    src: int
    dest: int
    dest_id: int = 0
    max: int = 0
    threshold: int = 0
    deadzone: int = 0
    turbo: int = 0
    scaling: int = 0
    diag_scaling: int = 0
