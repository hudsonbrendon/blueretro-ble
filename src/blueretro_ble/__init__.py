"""blueretro-ble: talk to the BlueRetro retro-console adapter over Bluetooth LE."""

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
from .memorycard import make_formatted_pak
from .models import BlueRetroState, InputMapping
from .presets import Preset, list_presets, load_preset, preset_from_json
from .protocol import decode_input_config, encode_input_config
from .scanner import discover, supports

__version__ = "0.8.0"

__all__ = [
    "ACCESSORY_CFG",
    "BlueRetroDevice",
    "BlueRetroState",
    "CFG_SRC",
    "DEVICE_CFG",
    "INQUIRY_MODE",
    "InputMapping",
    "MULTITAP_CFG",
    "PAK_BANKS",
    "PAK_SIZE",
    "Preset",
    "SERVICE_UUID",
    "SYSTEM_CFG",
    "VMU_SIZE",
    "decode_input_config",
    "discover",
    "encode_input_config",
    "list_presets",
    "load_preset",
    "make_formatted_pak",
    "parse_firmware",
    "preset_from_json",
    "supports",
    "__version__",
]
