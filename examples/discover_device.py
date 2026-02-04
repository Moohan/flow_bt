"""Device discovery utility for Flow 2 devices.

This script scans for nearby Flow 2 devices and displays their MAC addresses.
"""

import asyncio
import logging

from bleak import BleakScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def discover_flow_devices(timeout: float = 10.0) -> list:
    """Scan for Flow 2 devices.

    Args:
        timeout: Scan duration in seconds

    Returns:
        List of discovered Flow devices with name and address
    """
    logger.info(f"Scanning for Flow devices ({timeout}s)...")
    devices = await BleakScanner.discover(timeout=timeout)

    flow_devices = []
    for device in devices:
        if device.name and "FLOW" in device.name.upper():
            flow_devices.append({
                "name": device.name,
                "address": device.address,
                "rssi": device.rssi if hasattr(device, 'rssi') else None
            })

    return flow_devices


async def main():
    """Scan for and display Flow 2 devices."""
    print("Scanning for Flow 2 devices...")
    print("Make sure your device is awake (blinking blue LED).\n")

    devices = await discover_flow_devices(timeout=10.0)

    if not devices:
        print("❌ No Flow devices found.")
        print("\nTroubleshooting:")
        print("- Ensure your Flow 2 device is turned on (blinking blue)")
        print("- Check that Bluetooth is enabled on your computer")
        print("- Move closer to the device")
        print("- Try scanning again")
    else:
        print(f"✅ Found {len(devices)} Flow device(s):\n")
        for i, device in enumerate(devices, 1):
            rssi_str = f" (RSSI: {device['rssi']} dBm)" if device['rssi'] else ""
            print(f"{i}. {device['name']}")
            print(f"   MAC Address: {device['address']}{rssi_str}")
            print()

        print("Use the MAC address in your Flow2Client:")
        print(f'  client = Flow2Client("{devices[0]["address"]}")')


if __name__ == "__main__":
    asyncio.run(main())
