"""Protocol utilities for decoding Flow 2 data packets."""

import struct
from datetime import datetime
from typing import Optional


def decode_live_pm_value(data: bytes) -> Optional[float]:
    """Decode PM2.5 value from live data packet.

    Args:
        data: 20-byte live data packet

    Returns:
        PM2.5 value in µg/m³, or None if decoding fails
    """
    if len(data) != 20:
        return None

    try:
        # Float at offset 8-11 (little-endian)
        return struct.unpack('<f', data[8:12])[0]
    except struct.error:
        return None


def decode_history_timestamp(data: bytes, offset: int = 0) -> Optional[datetime]:
    """Decode timestamp from history packet.

    Args:
        data: History data packet
        offset: Byte offset to start reading from

    Returns:
        Datetime object, or None if decoding fails
    """
    if len(data) < offset + 4:
        return None

    try:
        timestamp = struct.unpack('<I', data[offset:offset + 4])[0]
        return datetime.fromtimestamp(timestamp)
    except (struct.error, ValueError, OSError):
        return None
