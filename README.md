# Flow BT - Flow 2 BLE Client Library

[![PyPI version](https://img.shields.io/pypi/v/flow-bt.svg)](https://pypi.org/project/flow-bt/)
[![Python versions](https://img.shields.io/pypi/pyversions/flow-bt.svg)](https://pypi.org/project/flow-bt/)
[![codecov](https://codecov.io/gh/moohan/flow-bt/branch/main/graph/badge.svg)](https://codecov.io/gh/moohan/flow-bt)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python client library for interacting with Flow 2 air quality monitors via Bluetooth Low Energy (BLE).

## Features

- **Async/await API** using `asyncio` and `bleak`
- **Live data streaming** - Real-time PM2.5 readings
- **Historical data fetch** - Retrieve stored sensor measurements
- **Type hints** - Full type annotations for better IDE support
- **Well documented** - Comprehensive docstrings and examples

## Getting Started

### Prerequisites

- Python >= 3.8
- A Flow 2 air quality monitor
- Bluetooth enabled on your computer

### 1. Find Your Device

First, wake up your Flow 2 device (press the button until the LED blinks blue), then run the discovery script:

```bash
python examples/discover_device.py
```

This will scan for nearby Flow devices and display their MAC addresses:

```text
✅ Found 1 Flow device(s):

1. FLOW-00:43:A6
   MAC Address: E4:3D:7F:05:7C:FA

Use the MAC address in your Flow2Client:
  client = Flow2Client("E4:3D:7F:05:7C:FA")
```

**Note**: The MAC address format may differ by platform:

- **Windows/Linux**: `E4:3D:7F:05:7C:FA`
- **macOS**: `12345678-90AB-CDEF-1234-567890ABCDEF` (UUID format)

### 2. Install the Package

```bash
pip install flow-bt
```

### 3. CLI Tool

Flow BT comes with a built-in CLI for quick interaction:

```bash
# Discover nearby devices
flow-bt discover

# Stream live data from a specific device
flow-bt read E4:3D:7F:05:7C:FA --duration 60
```

### 4. Use the Library in Your Code

Replace `YOUR_MAC_ADDRESS` with the address from step 1:

### Basic Live Streaming

```python
import asyncio
from flow_bt import Flow2Client

async def main():
    client = Flow2Client("E4:3D:7F:05:7C:FA")  # Your device MAC

    def on_data(msg_type, payload):
        if msg_type == "live":
            print(f"PM2.5: {payload:.2f} µg/m³")

    await client.connect()
    await client.start_stream(on_data)
    await asyncio.sleep(10)  # Stream for 10 seconds
    await client.disconnect()

asyncio.run(main())
```

See the [Examples](./examples) directory for more advanced usage like historical data retrieval.

## Troubleshooting

### Device Not Found

- **Wake the device**: Press the button until the LED blinks blue
- **Check Bluetooth**: Ensure Bluetooth is enabled on your computer
- **Distance**: Move closer to the device (within 10m)
- **Interference**: Move away from other Bluetooth devices

### Connection Fails

- **Authentication Error**: The authentication key is hardcoded and should work for all Flow 2 devices
- **Timeout**: Try increasing the timeout in `BleakClient` initialization (currently 20 seconds)
- **Platform Issues**:
  - **Linux**: May require `bluez` and proper permissions (`sudo usermod -a -G bluetooth $USER`)
  - **macOS**: May need to grant Bluetooth permissions in System Preferences
  - **Windows**: Ensure Bluetooth is enabled in Settings

### No Data Received

- **Device in Sleep Mode**: Press the button to wake it up
- **Battery Low**: Check battery level with `client.read_battery()`
- **Keep-Alive**: The client sends keep-alive commands every 5 seconds automatically

## Examples

See the [`examples/`](./examples) directory for complete working examples:

- [`discover_device.py`](./examples/discover_device.py) - Find your Flow 2 device's MAC address
- [`basic_stream.py`](./examples/basic_stream.py) - Live data streaming
- [`fetch_history.py`](./examples/fetch_history.py) - Historical data retrieval

## Documentation

- **[PROTOCOL.md](./PROTOCOL.md)** - Detailed BLE protocol specification
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Reverse engineering process and implementation walkthrough

## Project Structure

```text
flow_bt/
├── src/flow_bt/          # Main package source
│   ├── __main__.py       # CLI Entry point
│   ├── client.py         # Flow2Client class
│   ├── constants.py      # Protocol constants
│   ├── exceptions.py     # Custom exceptions
│   └── protocol.py       # Data decoding utilities
├── examples/             # Usage examples
├── docs/                 # Documentation (Source for GitHub Pages)
├── tests/                # Test suite
└── tools/                # Analysis/debugging scripts
```

## Development

### Running Examples

```bash
# Stream live data
python examples/basic_stream.py

# Fetch historical data
python examples/fetch_history.py
```

### Code Formatting

```bash
# Format code with black
black src/ examples/

# Lint with ruff
ruff check src/ examples/
```

## License

MIT License - See LICENSE file for details

## Acknowledgments

This library was developed through reverse engineering of the Flow 2 BLE protocol. See [DEVELOPMENT.md](./DEVELOPMENT.md) for the full story.
