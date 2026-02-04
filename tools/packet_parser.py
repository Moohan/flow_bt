import json
import csv
import sys
from typing import List, Dict, Any

# --- Configuration ---
# The characteristic UUIDs we are interested in.
# Expanded list based on debug output (0401, 0501, 0502 appear to be the active data streams).
TARGET_UUIDS = [
    "30390101-4e55-4c10-9dce-b654f35fdf99", # Original Target 1
    "303901014e554c109dceb654f35fdf99", # Original Target 1
    "30390102-4e55-4c10-9dce-b654f35fdf99", # Original Target 2
    "303901024e554c109dceb654f35fdf99", # Original Target 2
    "30390401-4e55-4c10-9dce-b654f35fdf99", # New Active Data Channel
    "303904014e554c109dceb654f35fdf99", # New Active Data Channel
    "30390501-4e55-4c10-9dce-b654f35fdf99", # New Active Data Channel
    "303905014e554c109dceb654f35fdf99", # New Active Data Channel
    "30390502-4e55-4c10-9dce-b654f35fdf99",  # New Active Data Channel
    "303905024e554c109dceb654f35fdf99"  # New Active Data Channel
]
INPUT_FILENAME = "flow2_trace.json"
OUTPUT_FILENAME = "flow2_filtered_data.csv"

# --- DEBUG FLAG ---
DEBUG_MODE = False # Disabling debug mode for final run
# --------------------

def get_ble_gatt_data(layers: Dict[str, Any], gatt_layer: Dict[str, Any]) -> str:
    """
    Extracts the hex data string from the GATT/ATT layer, using multiple fallbacks.
    """

    # CRITICAL FIX: Direct access to btatt.value based on the user's JSON structure
    btatt_layer = layers.get('btatt')
    if btatt_layer and 'btatt.value' in btatt_layer:
        return btatt_layer['btatt.value']

    # Fallback checks (less likely to be hit now)
    if 'att_value' in gatt_layer:
        return gatt_layer['att_value']
    if 'gatt_data' in gatt_layer:
        return gatt_layer['gatt_data']

    # 4. Fallback for raw data in HCI ACL layer
    acl_layer = layers.get('bthci_acl')
    if acl_layer and 'bthci_acl.data' in acl_layer:
        data_raw = acl_layer['bthci_acl.data']
        if isinstance(data_raw, list):
            data_raw = data_raw[0]

        if data_raw.startswith("data:"):
            return data_raw.split(':')[-1]

        return data_raw

    return ""

def get_gatt_uuid(layers: Dict[str, Any], gatt_layer: Dict[str, Any]) -> str:
    """Extracts the full 128-bit UUID from the GATT layer based on the handle tree."""

    # CRITICAL FIX: Access the UUID via the btatt layer's handle tree
    btatt_layer = layers.get('btatt')
    if btatt_layer and 'btatt.handle_tree' in btatt_layer:
        handle_tree = btatt_layer['btatt.handle_tree']

        # Check for the UUID associated with the characteristic handle
        if 'btatt.uuid128' in handle_tree:
            uuid_raw = handle_tree['btatt.uuid128']
            if isinstance(uuid_raw, list):
                uuid_raw = uuid_raw[0]

            # Remove colons and convert to lowercase for comparison
            return uuid_raw.replace(':', '').lower()

    # Fallback to the UUID field in the generic GATT layer
    if 'gatt_uuid_128' in gatt_layer:
        uuid_raw = gatt_layer['gatt_uuid_128']
        if isinstance(uuid_raw, list):
            uuid_raw = uuid_raw[0]

        # Cleanup should still happen for the fallback
        return uuid_raw.replace(':', '').replace('.', '').lower()

    return ""

def parse_trace(input_path: str, output_path: str):
    """Parses the JSON trace, filters packets, and writes to CSV."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            full_trace = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'. Please ensure you exported 'flow2_trace.json'.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Could not decode JSON. Ensure the Wireshark export was clean.")
        sys.exit(1)

    filtered_data = []

    print(f"Parsing {len(full_trace)} packets...")

    for packet in full_trace:
        if '_source' not in packet or 'layers' not in packet['_source']:
            continue

        layers = packet['_source']['layers']

        # Look for the GATT/ATT layer
        gatt_layer = layers.get('btgatt', layers.get('bluetooth_le_gatt'))
        btatt_layer = layers.get('btatt')

        if gatt_layer or btatt_layer:
            uuid = get_gatt_uuid(layers, gatt_layer or {})
            frame = layers.get('frame', {})
            timestamp = frame.get('frame_time_epoch', 'N/A')

            # Use the robust data extraction function to check for data presence
            hex_data = get_ble_gatt_data(layers, gatt_layer or {})

            if DEBUG_MODE:
                data_status = "DATA FOUND" if hex_data else "NO DATA"
                # Print relevant packet details regardless of UUID match
                print(f"[DEBUG] TS: {timestamp} | UUID: {uuid if uuid else 'N/A'} | Status: {data_status}")

            # Actual Filtering Logic
            if uuid in TARGET_UUIDS and hex_data:

                # Get Opcode from the ATT layer, or fallback to the GATT layer
                if btatt_layer and 'btatt.opcode' in btatt_layer:
                    packet_type = btatt_layer['btatt.opcode']
                else:
                    packet_type = gatt_layer.get('gatt_opcode', gatt_layer.get('att_opcode', 'N/A'))

                # Clean the hex data string (remove colons, dots, and convert to lowercase)
                hex_data = hex_data.replace(':', '').replace('.', '').lower()

                filtered_data.append({
                    'timestamp': timestamp,
                    'source_uuid': uuid,
                    'opcode': packet_type,
                    'hex_payload': hex_data
                })

    # Write results to CSV
    if filtered_data:
        fieldnames = ['timestamp', 'source_uuid', 'opcode', 'hex_payload']
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_data)

        print(f"Success! Filtered {len(filtered_data)} relevant packets to '{output_path}'.")
        print("Please upload the contents of the generated CSV file.")
    else:
        print("No packets matching the target UUIDs were found with data payloads. Check the Wireshark export settings again.")


if __name__ == "__main__":
    parse_trace(INPUT_FILENAME, OUTPUT_FILENAME)
