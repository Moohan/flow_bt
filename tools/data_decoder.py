import csv
import struct
from typing import Dict, Any

# --- Configuration ---
INPUT_FILENAME = "flow2_filtered_data.csv"

# --- Decoding Helper Functions ---

def hex_to_float(hex_string: str, byte_order: str = '<') -> float:
    """
    Converts a 4-byte hex string (e.g., '0000ae43') into a 32-bit floating point number.

    Args:
        hex_string: 8-character hex string representing 4 bytes.
        byte_order: '<' for Little Endian (default), '>' for Big Endian.

    Returns:
        The decoded float value.
    """
    # 1. Convert hex string to bytes
    byte_data = bytes.fromhex(hex_string)

    # 2. Use struct.unpack to decode the bytes as a single-precision float ('f')
    # The byte order is specified by the first character of the format string (e.g., '<f' for LE float).
    #
    decoded_value = struct.unpack(f'{byte_order}f', byte_data)[0]
    return decoded_value

def decode_20_byte_payload(hex_payload: str) -> Dict[str, Any]:
    """
    Decodes the specific 20-byte data stream based on our reverse-engineering hypothesis.

    Args:
        hex_payload: The 40-character hex string from the CSV.

    Returns:
        A dictionary of decoded values.
    """
    if len(hex_payload) != 40:
        return {"error": "Invalid payload length", "raw": hex_payload}

    try:
        # Byte Indices (0-indexed)
        # Byte 0 (ID) - 1 byte
        # Bytes 1-4 (Timestamp/Counter) - 4 bytes
        # Bytes 5-8 (Value 1, Unknown Float) - 4 bytes
        # Bytes 9-12 (Value 2, Hypothesis: PM2.5/TVOC Float) - 4 bytes
        # Bytes 13-20 (Status/Flags/Other) - 8 bytes

        # 1. Extract the section hypothesised to be the main sensor value (Bytes 9-12)
        # 1-indexed for string slicing (Hex characters 19-26)
        value2_hex = hex_payload[18:26]

        # Decode using Little Endian (as hypothesised)
        decoded_value_2 = hex_to_float(value2_hex, byte_order='<')

        # 2. Extract the overall timestamp/counter (Bytes 1-4)
        timestamp_hex = hex_payload[2:10]
        # Use little-endian unsigned 32-bit integer ('I')
        byte_data = bytes.fromhex(timestamp_hex)
        decoded_timestamp = struct.unpack('<I', byte_data)[0]

        return {
            "timestamp_counter": decoded_timestamp,
            "raw_value_2_hex": value2_hex,
            "decoded_float_2": decoded_value_2,
            "raw_payload": hex_payload
        }

    except Exception as e:
        return {"error": f"Decoding failed: {e}", "raw": hex_payload}


def analyze_csv_data(input_path: str):
    """Reads the filtered CSV and attempts to decode the main 20-byte packets."""
    print(f"Reading and decoding data from '{input_path}'...")
    decoded_results = []

    try:
        with open(input_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                hex_payload = row.get('hex_payload', '')
                opcode = row.get('opcode', '')
                source_uuid = row.get('source_uuid', '')

                # We only want to decode the main 20-byte data notification packets
                # (which have a length of 40 hex characters)
                if len(hex_payload) == 40 and opcode == '0x1b':
                    result = decode_20_byte_payload(hex_payload)
                    result['packet_timestamp'] = row.get('timestamp')
                    result['source_uuid'] = source_uuid
                    decoded_results.append(result)

        # Print the first 5 results to confirm the decoding is working
        print("\n--- First 5 Decoded Sensor Values (Hypothesis Test) ---")
        for i, result in enumerate(decoded_results[:5]):
            print(f"Packet #{i+1} | Counter: {result['timestamp_counter']:<10} | Raw Hex: {result['raw_value_2_hex']} | Decoded Float: {result['decoded_float_2']:.2f}")

        # Summary Statistics (Rhetorical question for the user to confirm next steps)
        if decoded_results:
            print(f"\nSuccessfully processed and decoded {len(decoded_results)} full data packets.")
            print("The decoded float values should now look like plausible sensor data (e.g., 20.0 to 500.0).")
            print("Please confirm if the 'Decoded Float' values look like plausible sensor readings.")

    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'. Ensure '{INPUT_FILENAME}' is present.")
    except Exception as e:
        print(f"An error occurred during CSV reading or processing: {e}")

if __name__ == "__main__":
    analyze_csv_data(INPUT_FILENAME)
