"""State container for a BlueRetro device."""

from __future__ import annotations

from dataclasses import dataclass


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
    # Global config (read from CHAR_GLOBAL_CFG)
    system: str | None = None
    multitap: str | None = None
    inquiry_mode: str | None = None
    memory_card_bank: int | None = None
