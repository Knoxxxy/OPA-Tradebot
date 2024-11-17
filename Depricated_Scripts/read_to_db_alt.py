import os
import zipfile
import pandas as pd
import json
from pymongo import MongoClient, errors
from tqdm import tqdm

# MongoDB connection settings
def get_mongo_connection():
    try:
        client = MongoClient("mongodb://mongodb:27017/")
        db = client['OPA_Data']
        collection = db['historical_trading_data']
        collection.create_index([("open_time", 1)], unique=True)
        return collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)

# Function to extract ZIP files
def extract_zip(zip_file, extract_dir):
    print(f"Extracting {zip_file}...")
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"Files extracted to {extract_dir}")

# Function to import CSV files into MongoDB
def import_csv(file_path, collection):
    print(f"Importing CSV file: {file_path}")
    df = pd.read_csv(file_path)
    data = df.to_dict(orient='records')
    
    for record in tqdm(data, desc="Inserting records", unit="record"):
        try:
            collection.insert_one(record)
        except errors.DuplicateKeyError:
           continue

# Function to import JSON files into MongoDB
# Data is in CSV Format, so it might not be needed
"""def import_json(file_path, collection):
    print(f"Importing JSON file: {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        collection.insert_many(data)
    else:
        collection.insert_one(data)
    print(f"Inserted data from {file_path} into MongoDB.")
"""

# Function to process extracted files (CSV or JSON)
def process_files(extract_dir, collection):
    # Use os.walk to gather all CSV files recursively
    csv_files = []
    for root, dirs, files in os.walk(extract_dir):
        for filename in files:
            if filename.endswith(".csv"):
                csv_files.append(os.path.join(root, filename))
                print(f"Found CSV file: {os.path.join(root, filename)}")  # Debugging output

     # Debugging: Print the number of CSV files found
    print(f"Found {len(csv_files)} CSV files to process.")
    
    # Create a progress bar with tqdm
    for file_path in tqdm(csv_files, desc="Processing CSV files", unit="file"):
        import_csv(file_path, collection)

# Main function
def main():
    # Set the path to your folder containing ZIP files
    zip_folder = "Historical_data_Binance" 
    extract_base_dir = "./extracted_binance_data"

    # Connect to MongoDB
    collection = get_mongo_connection()

    # Process each ZIP file in the specified folder
    for zip_file in os.listdir(zip_folder):
        if zip_file.endswith(".zip"):
            zip_path = os.path.join(zip_folder, zip_file)
            extract_dir = os.path.join(extract_base_dir, os.path.splitext(zip_file)[0])  # Create a unique folder for each ZIP

            # Extract ZIP file
            extract_zip(zip_path, extract_dir)

    
    # Process extracted files (CSV/JSON) and insert into MongoDB
    process_files(extract_base_dir, collection)

    print("Data import completed for all ZIP files.")

if __name__ == "__main__":
    main()