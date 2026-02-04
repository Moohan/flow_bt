"""Historical data fetch example.

This example connects to a Flow 2 device, streams live data briefly,
then triggers a historical data dump.
"""

import asyncio
import logging

from flow_bt import Flow2Client
from flow_bt.protocol import decode_history_timestamp

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
        # Try to decode the first timestamp
        timestamp = decode_history_timestamp(payload)
        if timestamp:
            print(f"[HISTORY] Packet Size: {len(payload)} bytes | "
                  f"First timestamp: {timestamp}")
        else:
            print(f"[HISTORY] Packet Size: {len(payload)} bytes | "
                  f"Header: {payload[:10].hex()}...")


async def main():
    """Connect to device and fetch historical data."""
    # Replace with your device's MAC address
    ADDRESS = "E4:3D:7F:05:7C:FA"

    client = Flow2Client(ADDRESS)

    try:
        # Connect and authenticate
        await client.connect()

        # Start listening for data
        await client.start_stream(on_data)

        print("Streaming live data for 5 seconds...")
        await asyncio.sleep(5)

        print("\nRequesting historical data dump...")
        await client.fetch_history()

        print("Listening for history data (15 seconds)...")
        await asyncio.sleep(15)

        print("\nDone!")

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
