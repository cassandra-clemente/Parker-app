import psycopg2
import pandas as pd
import geopandas as gpd
from shapely import wkt

import psycopg2
import re
from datetime import datetime
import pandas as pd
import geopy.distance

def get_first_word(street_name):
    """Extracts the first word from the street name."""
    street_name = street_name.strip().upper()  # Convert to uppercase for case insensitivity
    first_word = street_name.split()[0]  # Split by spaces and get the first word
    return first_word

def normalize_street_name(name):
    abbreviation_map = {
        "st": "street",
        "ave": "avenue",
        "av": "avenue",
        "blvd": "boulevard",
        "rd": "road",
        "dr": "drive",
        "ln": "lane",
        "pl": "place",
        "ct": "court",
        "ter": "terrace",
        "pkwy": "parkway",
        "hwy": "highway",
        "sq": "square",
        "trl": "trail",
        "cir": "circle",
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "bch": "beach"
    }

    words = name.lower().replace('.', '').split()
    expanded = []

    for word in words:
        if word in abbreviation_map:
            expanded.append(abbreviation_map[word])
        else:
            expanded.append(word)

    # Capitalize first letter of each word
    return ' '.join(expanded).title()


def main():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="cclemente",
        user="cclemente",
        password="Parker123",
        host="localhost",
        port="5431"
    )
    cursor = conn.cursor()

    # Load CSV
    meter_data = pd.read_csv("manhattan.csv")

    # === DAY EXPANSION MAP ===
    DAY_MAP = {
        "Mon": ["Mon"],
        "Tue": ["Tue"],
        "Wed": ["Wed"],
        "Thu": ["Thu"],
        "Fri": ["Fri"],
        "Sat": ["Sat"],
        "Sun": ["Sun"],
        "Mon-Fri": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "Mon-Sat": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        "Mon-Sun": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Sat-Sun": ["Sat", "Sun"],
    }

    # === HELPER: TIME CONVERT ===
    def format_time(t_str):
        """Converts 4-digit time string to HH:MM format."""
        if t_str == '2400':
            return '00:00'
        return datetime.strptime(t_str, '%H%M').strftime('%H:%M')

    # === HELPER: CALCULATE DISTANCE ===
    def get_nearest_block(latitude, longitude, blockCoordinates):
        """Calculates the nearest block_id based on lat/lon using Haversine formula."""
        nearest_block = None
        min_distance = float('inf')

        for block_id, (block_lat, block_lon, street_name) in blockCoordinates.items():
            distance = geopy.distance.distance((latitude, longitude), (block_lat, block_lon)).meters
            if distance < min_distance:
                min_distance = distance
                nearest_block = block_id
        return nearest_block

    # === LOAD BLOCK COORDINATES FROM DATABASE ===
    cursor.execute("SELECT id, latitude, longitude, street_name FROM public.blocks")
    block_coordinates = {block_id: (latitude, longitude, street_name) for block_id, latitude, longitude, street_name in cursor.fetchall()}

    # === PARSE FUNCTION ===
    def parse_meter_hours(meterHours):
        """Parses Meter_Hours string and returns a list of (day, start_time, end_time, time_limit_minutes)."""
        results = []
        rules = meterHours.split('/')
        for rule in rules:
            rule = rule.strip()
            if 'Pas' not in rule:
                continue  # Skip non-pas rules

            match = re.match(r'(\d+)HR\s+Pas\s+([A-Za-z\-]+)\s+(\d{4})-(\d{4})', rule)
            if match:
                limit, days, start, end = match.groups()
                minutesIn = int(limit) * 60
                startTime = format_time(start)
                endTime = format_time(end)

                for day in DAY_MAP.get(days, []):
                    results.append((day, startTime, endTime, minutesIn))
        return results

    # === PROCESS EACH ROW ===
    successful_inserts = 0
    failed_inserts = []

    for idx, row in meter_data.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        meter_number = row.get("Meter Number", "Unknown")
        on_street = row.get("On_Street", "Unknown")

        print(f"\nParsing meter {meter_number} on {on_street} at ({lat}, {lon})")

        block_id = get_nearest_block(lat, lon, block_coordinates)

        if block_id is None:
            continue  # If no nearest block found, skip this row

        '''
        # Ensure the first word of the street names match before proceeding
        block_street_name = block_coordinates[block_id][2]  # Extract the street name from block data
        if get_first_word(on_street) != get_first_word(block_street_name):
            print(
                f"Street mismatch: Meter on {on_street} does not match block street {block_street_name}. Skipping this row.")
            continue  # Skip this row if first word of street names do not match
        '''
        block_street_name = block_coordinates[block_id][2]  # Extract the street name from block data
        if normalize_street_name(on_street) != normalize_street_name(block_street_name):
            print(
                f"Street mismatch: Meter on {on_street} does not match block street {block_street_name}. Skipping this row.")
            continue

        meter_hours = row.get("Meter_Hours", "")
        if not isinstance(meter_hours, str) or not meter_hours.strip():
            continue

        restrictions = parse_meter_hours(meter_hours)
        for day, start_time, end_time, minutes in restrictions:
            try:
                # Check if the restriction already exists for this block, day, start_time, and end_time
                cursor.execute("""
                               SELECT 1
                               FROM public.block_restrictions
                               WHERE block_id = %s AND day = %s
                                 AND start_time = %s
                                 AND end_time = %s LIMIT 1;
                               """, (block_id, day, start_time, end_time))

                existing = cursor.fetchone()
                if not existing:
                    # Insert the restriction if not already present
                    cursor.execute("""
                                   INSERT INTO public.block_restrictions (block_id, day, start_time, end_time, time_limit_minutes)
                                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT (block_id, day) DO NOTHING;
                                   """, (block_id, day, start_time, end_time, minutes))
                    successful_inserts += 1
                    print(f"Successfully inserted: Block {block_id}, Day {day}, Time {start_time}-{end_time}, Limit {minutes} min")
                else:
                    print(f"Skipped existing entry: Block {block_id}, Day {day}, Time {start_time}-{end_time}")

            except Exception as e:
                failed_inserts.append((block_id, day, start_time, end_time, str(e)))
                print(f"Failed to insert for block {block_id} on {day}: {e}")

    # === COMMIT + CLOSE ===



    # Commit changes and close
    conn.commit()
    cursor.close()
    conn.close()
    print("Database updated ! Woohoo.")

    # === SUMMARY ===
    print(f"Data import complete. {successful_inserts} successful inserts.")
    if failed_inserts:
        print("Failed inserts:")
        for failed in failed_inserts:
            print(f"Block {failed[0]}, Day {failed[1]}, Time {failed[2]}-{failed[3]}: {failed[4]}")



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
