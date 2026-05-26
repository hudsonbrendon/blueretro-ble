"""blueretro-ble: talk to the BlueRetro retro-console adapter over Bluetooth LE."""

from .const import (
    ACCESSORY_CFG,
    DEVICE_CFG,
    INQUIRY_MODE,
    MULTITAP_CFG,
    SERVICE_UUID,
    SYSTEM_CFG,
)
from .device import BlueRetroDevice
from .models import BlueRetroState
from .scanner import discover, supports

__version__ = "0.3.0"

__all__ = [
    "ACCESSORY_CFG",
    "BlueRetroDevice",
    "BlueRetroState",
    "DEVICE_CFG",
    "INQUIRY_MODE",
    "MULTITAP_CFG",
    "SERVICE_UUID",
    "SYSTEM_CFG",
    "discover",
    "supports",
    "__version__",
]
