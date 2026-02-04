"""CLI entry point for Flow BT."""

import asyncio
import argparse
import sys
import logging
from bleak import BleakScanner
from flow_bt.client import Flow2Client

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

async def discover():
    """Discover Flow devices."""
    print("Searching for Flow devices...")
    devices = await BleakScanner.discover()
    flow_devices = [d for d in devices if d.name and "FLOW" in d.name.upper()]

    if not flow_devices:
        print("No Flow devices found.")
        return

    print(f"Found {len(flow_devices)} Flow device(s):")
    for i, device in enumerate(flow_devices, 1):
        print(f"{i}. {device.name} ({device.address})")

async def read_live(address: str, duration: int):
    """Read live data for a duration."""
    client = Flow2Client(address)

    def on_data(msg_type, payload):
        if msg_type == "live":
            print(f"PM2.5: {payload:.2f} µg/m³")

    try:
        await client.connect()
        await client.start_stream(on_data)
        print(f"Streaming live data for {duration} seconds... (Ctrl+C to stop)")
        await asyncio.sleep(duration)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Flow BT CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Discover command
    subparsers.add_parser("discover", help="Discover nearby Flow devices")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read live data from a device")
    read_parser.add_argument("address", help="MAC address or UUID of the device")
    read_parser.add_argument("--duration", type=int, default=30, help="Duration to stream data in seconds")

    args = parser.parse_args()

    if args.command == "discover":
        asyncio.run(discover())
    elif args.command == "read":
        asyncio.run(read_live(args.address, args.duration))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
