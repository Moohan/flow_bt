#!/usr/bin/env python3
"""
Wireshark JSON Packet Analyzer for Flow 2 Protocol Reverse Engineering
Extracts critical ATT Write/Notification payloads from Wireshark JSON export
"""

import json
import sys
from pathlib import Path

# Target packet numbers identified from CSV analysis
CRITICAL_PACKETS = {
    1781: "AUTH_KEY_WRITE (Handle 0x002C)",
    1789: "ACTIVATION_COMMAND (Handle 0x0025)",
    1792: "DEVICE_INDICATION_RESPONSE (Handle 0x0025)",
    1795: "KEEP_ALIVE_1 (Handle 0x0025)",
    1804: "KEEP_ALIVE_2 (Handle 0x0025)",
    1808: "FIRST_DATA_NOTIFICATION (Handle 0x0028)",
    1810: "DATA_NOTIFICATION_2 (Handle 0x0028)",
    1811: "DATA_NOTIFICATION_3 (Handle 0x0028 - 88 bytes)",
}

def extract_att_value(packet):
    """
    Extracts the ATT 'value' field from a Wireshark packet.
    Returns hex string of the payload.
    """
    try:
        # Navigate Wireshark JSON structure
        layers = packet.get("_source", {}).get("layers", {})

        # ATT protocol data
        btatt = layers.get("btatt", {})

        # Try different possible value fields
        value_fields = [
            "btatt.value",
            "btatt.value_raw",
            "btatt.handle_value",
            "btatt.write_value"
        ]

        for field in value_fields:
            if field in btatt:
                raw_value = btatt[field]
                # Remove colons if present (Wireshark format: "a5:97:14:69")
                return raw_value.replace(":", "")

        # If no value field, return the entire btatt layer for manual inspection
        return None

    except Exception as e:
        return None


def analyze_json_export(json_path):
    """
    Main analyzer function.
    """
    print("="*80)
    print("AETHERFLOW PACKET ANALYZER")
    print("="*80)
    print(f"Loading: {json_path}\n")

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    # Wireshark JSON can be either a list of packets or a single packet
    if isinstance(data, dict):
        packets = [data]
    else:
        packets = data

    print(f"Total packets in capture: {len(packets)}\n")
    print("="*80)
    print("CRITICAL PACKET ANALYSIS")
    print("="*80)

    for packet in packets:
        try:
            # Get packet number
            frame = packet.get("_source", {}).get("layers", {}).get("frame", {})
            packet_num = int(frame.get("frame.number", 0))

            if packet_num in CRITICAL_PACKETS:
                description = CRITICAL_PACKETS[packet_num]

                print(f"\n[PACKET {packet_num}] {description}")
                print("-" * 80)

                # Extract ATT details
                layers = packet.get("_source", {}).get("layers", {})
                btatt = layers.get("btatt", {})

                # Handle
                handle = btatt.get("btatt.handle", "Unknown")
                print(f"Handle: {handle}")

                # Opcode
                opcode = btatt.get("btatt.opcode", "Unknown")
                print(f"Opcode: {opcode}")

                # Extract value/payload
                value = extract_att_value(packet)
                if value:
                    print(f"Payload (hex): {value}")
                    print(f"Payload (length): {len(value) // 2} bytes")

                    # Decode as bytes
                    try:
                        byte_array = bytes.fromhex(value)
                        print(f"Payload (bytes): {' '.join(f'0x{b:02x}' for b in byte_array)}")
                    except:
                        pass
                else:
                    print("Payload: [Could not extract - see raw data below]")
                    print(f"Raw BTATT layer: {json.dumps(btatt, indent=2)}")

                print("-" * 80)

        except Exception as e:
            continue

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 wireshark_json_analyzer.py <capture.json>")
        print("\nTo export from Wireshark:")
        print("  1. File → Export Packet Dissections → As JSON")
        print("  2. Save as 'flow2_capture.json'")
        print("  3. Run: python3 wireshark_json_analyzer.py flow2_capture.json")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    analyze_json_export(json_path)
