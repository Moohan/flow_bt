import asyncio
from bleak import BleakScanner

async def run_scanner():
    print("Starting BLE scan for 10 seconds...")
    # This will print all discovered devices
    devices = await BleakScanner.discover(timeout=10.0)

    found_flow = False
    for d in devices:
        # Check if the device name matches the Flow device name (FLOW-00:43:A6)
        if d.name and "FLOW" in d.name:
            print(f"✅ Found Flow Device: {d.name} at address {d.address}")
            found_flow = True
        else:
            print(f"Found other device: {d.name} at address {d.address}")

    if not found_flow:
        print("❌ Could not find the Flow device in the scan results.")

if __name__ == "__main__":
    asyncio.run(run_scanner())
