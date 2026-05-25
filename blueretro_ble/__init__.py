"""BlueRetro BLE library."""

from .const import INQUIRY_MODE, MULTITAP_CFG, SERVICE_UUID, SYSTEM_CFG
from .device import BlueRetroDevice
from .discovery import supports
from .models import BlueRetroState

__version__ = "0.1.0"

__all__ = [
    "SERVICE_UUID",
    "SYSTEM_CFG",
    "MULTITAP_CFG",
    "INQUIRY_MODE",
    "BlueRetroDevice",
    "BlueRetroState",
    "supports",
    "__version__",
]
