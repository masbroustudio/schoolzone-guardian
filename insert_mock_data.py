import datetime
from google.cloud import bigquery

def insert_crashes_only():
    project_id = "juaravibe01"
    dataset_id = "safety_dataset"
    client = bigquery.Client(project=project_id)
    
    print("Connecting to BigQuery to insert mock crash coordinates...")
    
    # 3. Insert Crashes Raw Data
    crashes_table = f"{project_id}.{dataset_id}.crashes_raw"
    crashes_rows = [
        # Near PS 199 (lat 40.7782, lon -73.9856)
        {
            "unique_key": "crash_101",
            "crash_date": "2026-06-15",
            "crash_time": "08:05:00",
            "latitude": 40.7785,
            "longitude": -73.9860,
            "geometry": "POINT(-73.9860 40.7785)",
            "number_of_persons_injured": 1,
            "number_of_pedestrians_injured": 1,
            "number_of_cyclist_injured": 0,
            "contributing_factor_vehicle_1": "Driver Inattention/Distraction",
            "vehicle_type_code1": "Sedan"
        },
        {
            "unique_key": "crash_102",
            "crash_date": "2026-06-20",
            "crash_time": "07:55:00",
            "latitude": 40.7779,
            "longitude": -73.9850,
            "geometry": "POINT(-73.9850 40.7779)",
            "number_of_persons_injured": 0,
            "number_of_pedestrians_injured": 0,
            "number_of_cyclist_injured": 0,
            "contributing_factor_vehicle_1": "Failure to Yield Right-of-Way",
            "vehicle_type_code1": "SUV"
        },
        # Near Stuyvesant (lat 40.7178, lon -74.0139)
        {
            "unique_key": "crash_103",
            "crash_date": "2026-06-18",
            "crash_time": "08:10:00",
            "latitude": 40.7180,
            "longitude": -74.0142,
            "geometry": "POINT(-74.0142 40.7180)",
            "number_of_persons_injured": 2,
            "number_of_pedestrians_injured": 2,
            "number_of_cyclist_injured": 0,
            "contributing_factor_vehicle_1": "Backing Unsafely",
            "vehicle_type_code1": "Box Truck"
        },
        {
            "unique_key": "crash_104",
            "crash_date": "2026-06-22",
            "crash_time": "15:15:00",
            "latitude": 40.7175,
            "longitude": -74.0135,
            "geometry": "POINT(-74.0135 40.7175)",
            "number_of_persons_injured": 0,
            "number_of_pedestrians_injured": 0,
            "number_of_cyclist_injured": 0,
            "contributing_factor_vehicle_1": "Driver Inexperience",
            "vehicle_type_code1": "SUV"
        },
        # Near Brooklyn Tech (lat 40.6888, lon -73.9765)
        {
            "unique_key": "crash_105",
            "crash_date": "2026-06-10",
            "crash_time": "07:50:00",
            "latitude": 40.6890,
            "longitude": -73.9768,
            "geometry": "POINT(-73.9768 40.6890)",
            "number_of_persons_injured": 1,
            "number_of_pedestrians_injured": 0,
            "number_of_cyclist_injured": 1,
            "contributing_factor_vehicle_1": "Passing Too Closely",
            "vehicle_type_code1": "Bicycle"
        },
        {
            "unique_key": "crash_106",
            "crash_date": "2026-06-25",
            "crash_time": "08:02:00",
            "latitude": 40.6885,
            "longitude": -73.9760,
            "geometry": "POINT(-73.9760 40.6885)",
            "number_of_persons_injured": 1,
            "number_of_pedestrians_injured": 1,
            "number_of_cyclist_injured": 0,
            "contributing_factor_vehicle_1": "Turning Improperly",
            "vehicle_type_code1": "Sedan"
        }
    ]

    try:
        # Clear existing crash rows
        print("Clearing crashes_raw table...")
        client.query(f"DELETE FROM {crashes_table} WHERE TRUE").result()
        
        # Insert mock raw crashes
        print("Inserting raw crashes...")
        errors = client.insert_rows_json(crashes_table, crashes_rows)
        if errors:
            print(f"Errors inserting crashes: {errors}")
            return
            
        print("Mock crash coordinates successfully loaded into crashes_raw table!")
    except Exception as e:
        print(f"Database insertion failed: {e}")

if __name__ == "__main__":
    insert_crashes_only()
