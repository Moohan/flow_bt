"""Basic live data streaming example.

This example connects to a Flow 2 device and streams live PM2.5 readings.
"""

import asyncio
import logging

from flow_bt import Flow2Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def on_data(msg_type: str, payload) -> None:
    """Callback for incoming data packets."""
    if msg_type == "live":
        print(f"[LIVE] PM2.5: {payload:.2f} µg/m³")
    elif msg_type == "history":
        # We don't expect history data in this example
        print(f"[HISTORY] Packet Size: {len(payload)} bytes")


async def main():
    """Connect to device and stream live data."""
    # Replace with your device's MAC address
    ADDRESS = "E4:3D:7F:05:7C:FA"

    client = Flow2Client(ADDRESS)

    try:
        # Connect and authenticate
        await client.connect()

        # Read battery level
        battery = await client.read_battery()
        if battery is not None:
            print(f"Battery: {battery}%\n")

        # Start streaming
        await client.start_stream(on_data)

        print("Streaming live data (press Ctrl+C to stop)...")
        # Stream indefinitely until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
