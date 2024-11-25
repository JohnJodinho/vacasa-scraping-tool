import csv
import json
import os

def save_to_csv(location_name):
    json_file_name = f"location_extracted_data/{location_name}_properties.json"
    os.makedirs("location_extracted_data", exist_ok=True)
    csv_file_name = f"location_extracted_data/{location_name}_properties.csv"
  
    # Specify the CSV file name
    csv_file = csv_file_name
    with open(json_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)
    # Write to CSV file
    with open(csv_file, mode='w', newline='', encoding="utf-8") as file:
        # Extract fieldnames from the first dictionary
        fieldnames = data[0].keys()
        
        # Create a writer object
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write data rows
        writer.writerows(data)

    print(f"Data successfully written to {csv_file}")
