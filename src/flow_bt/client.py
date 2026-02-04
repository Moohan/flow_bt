"""Flow 2 BLE client implementation."""

import asyncio
import logging
from typing import Callable, Optional

from bleak import BleakClient

from .constants import (
    UUID_AUTH,
    UUID_COMMAND,
    UUID_DATA,
    UUID_BATTERY,
    AUTH_KEY,
    CMD_ACTIVATE,
    CMD_FETCH_HISTORY,
    LIVE_DATA_PACKET_SIZE,
)
from .protocol import decode_live_pm_value
from .exceptions import (
    ConnectionError,
    AuthenticationError,
    NotConnectedError,
)

logger = logging.getLogger(__name__)


class Flow2Client:
    """Client for interacting with Flow 2 air quality monitors via BLE.

    This client handles connection, authentication, live data streaming,
    and historical data retrieval from Flow 2 devices.

    Example:
        >>> async def on_data(msg_type: str, payload):
        ...     if msg_type == "live":
        ...         print(f"PM2.5: {payload:.2f}")
        ...
        >>> client = Flow2Client("E4:3D:7F:05:7C:FA")
        >>> await client.connect()
        >>> await client.start_stream(on_data)
        >>> await asyncio.sleep(10)
        >>> await client.disconnect()
    """

    def __init__(self, address: str):
        """Initialize the Flow2 client.

        Args:
            address: Bluetooth MAC address of the Flow 2 device
        """
        self.address = address
        self.client: Optional[BleakClient] = None
        self.is_streaming = False
        self._keep_alive_task: Optional[asyncio.Task] = None
        self._data_callback: Optional[Callable[[str, any], None]] = None

    async def connect(self) -> None:
        """Connect to the device and perform authentication.

        Raises:
            BleakError: If connection or authentication fails
        """
        logger.info(f"Connecting to {self.address}...")
        try:
            self.client = BleakClient(self.address, timeout=20.0)
            await self.client.connect()
            logger.info("Connected.")

            # Authenticate
            logger.info("Writing authentication key...")
            await self.client.write_gatt_char(UUID_AUTH, AUTH_KEY, response=True)
            logger.info("Authentication successful.")

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            if self.client:
                await self.client.disconnect()
            if "Authentication" in str(e):
                raise AuthenticationError(f"Authentication failed: {e}") from e
            raise ConnectionError(f"Could not connect to {self.address}: {e}") from e

    async def disconnect(self) -> None:
        """Stop streaming and disconnect from the device."""
        if self.is_streaming:
            await self.stop_stream()

        if self.client and self.client.is_connected:
            logger.info("Disconnecting...")
            await self.client.disconnect()
            logger.info("Disconnected.")

    async def read_battery(self) -> Optional[int]:
        """Read the battery level from the device.

        Returns:
            Battery level as percentage (0-100), or None if read fails

        Raises:
            NotConnectedError: If client is not connected
        """
        if not self.client or not self.client.is_connected:
            raise NotConnectedError("Client not connected.")

        try:
            data = await self.client.read_gatt_char(UUID_BATTERY)
            level = int(data[0])
            logger.info(f"Battery Level: {level}%")
            return level
        except Exception as e:
            logger.error(f"Could not read battery: {e}")
            return None

    async def start_stream(self, callback: Callable[[str, any], None]) -> None:
        """Start data streaming and keep-alive loop.

        Args:
            callback: Function called with (msg_type, payload) for each data packet.
                     msg_type is either "live" or "history".
                     For live data, payload is a float (PM2.5 value).
                     For history data, payload is bytes (raw packet).

        Raises:
            NotConnectedError: If client is not connected
        """
        if not self.client or not self.client.is_connected:
            raise NotConnectedError("Client not connected.")

        self._data_callback = callback
        self.is_streaming = True

        logger.info("Subscribing to data notifications...")
        await self.client.start_notify(UUID_DATA, self._notification_handler)

        logger.info("Sending activation command...")
        await self.client.write_gatt_char(UUID_COMMAND, CMD_ACTIVATE, response=True)

        # Start keep-alive loop
        self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
        logger.info("Streaming started.")

    async def stop_stream(self) -> None:
        """Stop data streaming."""
        if not self.is_streaming:
            return

        self.is_streaming = False
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
            self._keep_alive_task = None

        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(UUID_DATA)
            except Exception as e:
                logger.warning(f"Error stopping notifications: {e}")

        logger.info("Streaming stopped.")

    async def fetch_history(self) -> None:
        """Trigger the device to dump its history data.

        History data will be received via the data callback registered
        with start_stream().

        Raises:
            NotConnectedError: If client is not connected
        """
        if not self.client or not self.client.is_connected:
            raise NotConnectedError("Client not connected.")

        logger.info("Sending FETCH HISTORY command...")
        await self.client.write_gatt_char(UUID_COMMAND, CMD_FETCH_HISTORY, response=True)

    def _notification_handler(self, sender: int, data: bytearray) -> None:
        """Handle incoming data packets.

        Args:
            sender: Characteristic handle
            data: Received data bytes
        """
        if len(data) == LIVE_DATA_PACKET_SIZE:
            # Live Data
            pm_value = decode_live_pm_value(data)
            if self._data_callback and pm_value is not None:
                self._data_callback("live", pm_value)
        elif len(data) > LIVE_DATA_PACKET_SIZE:
            # History Data
            if self._data_callback:
                self._data_callback("history", bytes(data))
        else:
            logger.debug(f"Unknown packet size: {len(data)}")

    async def _keep_alive_loop(self) -> None:
        """Send activation command periodically to keep stream alive."""
        try:
            while self.is_streaming:
                if self.client and self.client.is_connected:
                    await self.client.write_gatt_char(
                        UUID_COMMAND, CMD_ACTIVATE, response=False
                    )
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Keep-alive error: {e}")
            self.is_streaming = False
