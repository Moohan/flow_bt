import json
import pandas as pd


def merge_sensor_and_cap_data(csv_file, json_file, output_file):
    """
    Merges sensor readings from a CSV with packet capture data from a JSON
    based on the 'closest match' of their UTC timestamps.
    """
    # 1. Load CSV
    # Added 'delimiter' (or 'sep') and 'skipinitialspace' to handle potential spacing issues
    # Note: If your CSV is semicolon-separated, change delimiter=',' to delimiter=';'
    df_csv = pd.read_csv(csv_file, delimiter=',', skipinitialspace=True)

    # *** FIX: Clean up column headers by stripping leading/trailing whitespace ***
    df_csv.columns = df_csv.columns.str.strip()

    print("\n--- Cleaned CSV Column Headers ---")
    print(df_csv.columns.tolist())
    print("----------------------------------\n")
    # **************************************************************************

    # 2. Load and Normalize JSON
    # Assuming 'cap.json' still exists from your earlier attempt
    with open(json_file, 'r') as f:
        data_json = json.load(f)

    # Use json_normalize to flatten the nested structure.
    df_json_raw = pd.json_normalize(data_json)

    # Select and rename the required columns
    df_json = df_json_raw.rename(columns={
        '_source.layers.frame.frame.time_utc': 'frame_time_utc',
        '_source.layers.btatt.btatt.handle': 'btatt_handle',
        '_source.layers.btatt.btatt.value': 'btatt_value'
    })[['frame_time_utc', 'btatt_handle', 'btatt_value']].copy()

    # Drop JSON rows that don't contain the required 'btatt' data
    df_json = df_json.dropna(subset=['btatt_handle', 'btatt_value'])

    # 3. Convert time columns to UTC datetime objects
    # This line should now work correctly after stripping the header whitespace
    df_csv['date (UTC)'] = pd.to_datetime(df_csv['date (UTC)'], utc=True)
    df_json['frame_time_utc'] = pd.to_datetime(df_json['frame_time_utc'], utc=True)

    # 4. Sort for merge_asof (required)
    df_csv = df_csv.sort_values('date (UTC)')
    df_json = df_json.sort_values('frame_time_utc')

    # 5. Closest match merge using merge_asof
    df_merged = pd.merge_asof(
        df_csv,
        df_json,
        left_on='date (UTC)',
        right_on='frame_time_utc',
        direction='nearest',
        allow_exact_matches=True
    )

    # 6. Drop unmatched rows and the redundant time column
    df_final = df_merged.dropna(subset=['btatt_handle', 'btatt_value'])
    df_final = df_final.drop(columns=['frame_time_utc'])

    # 7. Save the output
    df_final.to_csv(output_file, index=False)

    print(f"\nSuccessfully processed and saved merged data to {output_file}.")
    print(f"Final merged row count: {len(df_final)}")

    return df_final


# --- Execution ---
CSV_FILE = 'real_sensor_readings.csv'
JSON_FILE = 'cap.json'
OUTPUT_FILE = 'merged_sensor_cap_readings.csv'

# Execute the function and save the result
# The execution above demonstrated the functionality using synthetic data.
# When run with your real data, the output will be saved to the CSV file.
final_df = merge_sensor_and_cap_data(CSV_FILE, JSON_FILE, OUTPUT_FILE)
