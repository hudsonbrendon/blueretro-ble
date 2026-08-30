"""Bundled input-mapping presets (from darthcloud/BlueRetroWebCfg ``map/``).

Each preset is a JSON file ``{name, desc, console, map: [[src, dest, dest_id,
max, threshold, deadzone, turbo, scaling, diag_scaling], ...]}`` with button
*names*; :func:`load_preset` resolves them to ids via :data:`BUTTONS`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from importlib import resources

from .buttons import BUTTONS
from .models import InputMapping

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Preset:
    """A named input-mapping preset."""

    name: str
    desc: str
    console: str
    # Raw rows straight from the JSON (button names, not ids).
    map: list[list] = field(default_factory=list)

    def mappings(self, port: int = 0) -> list[InputMapping]:
        """Resolve rows to :class:`InputMapping`; ``port`` offsets ``dest_id``.

        Rows naming a button unknown to :data:`BUTTONS` are skipped with a
        warning (the upstream web config silently wrote them as id 0).
        """
        out: list[InputMapping] = []
        for row in self.map:
            src, dest = row[0], row[1]
            if src not in BUTTONS or dest not in BUTTONS:
                _LOGGER.warning(
                    "preset %r: unknown button in %r, skipping", self.name, row
                )
                continue
            nums = [int(v) for v in row[2:9]]
            out.append(
                InputMapping(
                    src=BUTTONS[src],
                    dest=BUTTONS[dest],
                    dest_id=nums[0] + port,
                    max=nums[1],
                    threshold=nums[2],
                    deadzone=nums[3],
                    turbo=nums[4],
                    scaling=nums[5],
                    diag_scaling=nums[6],
                )
            )
        return out


def _dir():
    return resources.files("blueretro_ble") / "presets"


def list_presets() -> list[str]:
    """Bundled preset ids (file stems), sorted."""
    return sorted(p.name[:-5] for p in _dir().iterdir() if p.name.endswith(".json"))


def load_preset(preset_id: str) -> Preset:
    """Load a bundled preset by id (file stem). Raises ``KeyError`` if missing."""
    path = _dir() / f"{preset_id}.json"
    if not path.is_file():
        raise KeyError(preset_id)
    return preset_from_json(path.read_text(encoding="utf-8"))


def preset_from_json(text: str) -> Preset:
    """Parse a preset from its JSON text (web-config ``map/*.json`` format)."""
    data = json.loads(text)
    return Preset(
        name=str(data.get("name", "")),
        desc=str(data.get("desc", "")),
        console=str(data.get("console", "")),
        map=list(data.get("map", [])),
    )
