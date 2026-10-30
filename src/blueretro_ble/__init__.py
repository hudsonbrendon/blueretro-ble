"""blueretro-ble: talk to the BlueRetro retro-console adapter over Bluetooth LE."""

from importlib import metadata

from .const import (
    ACCESSORY_CFG,
    CFG_SRC,
    DEVICE_CFG,
    INQUIRY_MODE,
    MULTITAP_CFG,
    PAK_BANKS,
    PAK_SIZE,
    SERVICE_UUID,
    SYSTEM_CFG,
    VMU_SIZE,
)
from .device import BlueRetroDevice
from .firmware import parse_firmware
from .memorycard import make_formatted_pak, parse_vmu_directory, vmu_swap
from .models import BlueRetroState, InputMapping, VmuSave
from .presets import Preset, list_presets, load_preset, preset_from_json
from .protocol import decode_input_config, encode_input_config
from .scanner import discover, supports

__all__ = [
    "ACCESSORY_CFG",
    "CFG_SRC",
    "DEVICE_CFG",
    "INQUIRY_MODE",
    "MULTITAP_CFG",
    "PAK_BANKS",
    "PAK_SIZE",
    "SERVICE_UUID",
    "SYSTEM_CFG",
    "VMU_SIZE",
    "BlueRetroDevice",
    "BlueRetroState",
    "InputMapping",
    "Preset",
    "VmuSave",
    "__version__",
    "decode_input_config",
    "discover",
    "encode_input_config",
    "list_presets",
    "load_preset",
    "make_formatted_pak",
    "parse_firmware",
    "parse_vmu_directory",
    "preset_from_json",
    "supports",
    "vmu_swap",
]

try:
    __version__ = metadata.version("blueretro-ble")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
