"""Flow 2 BLE Protocol Client.

A Python client library for interacting with Flow 2 air quality monitors via Bluetooth Low Energy.
"""

from .client import Flow2Client
from .constants import (
    UUID_AUTH,
    UUID_COMMAND,
    UUID_DATA,
    AUTH_KEY,
    CMD_ACTIVATE,
    CMD_FETCH_HISTORY,
)

__version__ = "0.1.0"
__all__ = ["Flow2Client"]
