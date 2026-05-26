"""blueretro-ble: talk to the BlueRetro retro-console adapter over Bluetooth LE."""

from .const import INQUIRY_MODE, MULTITAP_CFG, SERVICE_UUID, SYSTEM_CFG
from .device import BlueRetroDevice
from .models import BlueRetroState
from .scanner import discover, supports

__version__ = "0.2.0"

__all__ = [
    "BlueRetroDevice",
    "BlueRetroState",
    "INQUIRY_MODE",
    "MULTITAP_CFG",
    "SERVICE_UUID",
    "SYSTEM_CFG",
    "discover",
    "supports",
    "__version__",
]
