import psycopg2
import pandas as pd

def update_block_status_from_csv(csv_path):
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname="cclemente",
        user="cclemente",
        password="Parker123",
        host="localhost",
        port="5431"
    )
    cursor = conn.cursor()

    # Load the CSV
    df = pd.read_csv(csv_path)

    updates = 0
    # Iterate over rows where RW_Type == 1
    for idx, row in df.iterrows():
        block_id = row["PHYSICALID"]  # Adjust to your identifier column name
        rw_type = row.get("RW_TYPE")

        if pd.isna(block_id) or pd.isna(rw_type):
            continue  # Skip incomplete rows

        try:
            if int(rw_type) != 1:
                cursor.execute("""
                               UPDATE public.blocks
                               SET status = 'restricted'
                               WHERE id = %s;
                               """, (int(block_id),))
                updates += 1
        except Exception as e:
            print(f"Failed to update block {block_id} with RW_Type {rw_type}: {e}")

    # Commit and close
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Status update complete with {updates} updates.")

# Call the function
update_block_status_from_csv("modified_city_data.csv")
