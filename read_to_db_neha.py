import os
import zipfile
import pandas as pd
import json
from pymongo import MongoClient

# MongoDB connection settings
def get_mongo_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client['binance_data']
        collection = db['historical_trading_data']
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
def import_csv(file_path, collection, symbol):
    print(f"Importing CSV file: {file_path}")
    df = pd.read_csv(file_path)
    data = df.to_dict(orient='records')
    
    if data:
        # Add the key (first 7 chars of the filename) as a key-value pair in each document
        for record in data:
            record['key'] = symbol
        
        collection.insert_many(data)
        print(f"Inserted {len(data)} records from {file_path} into MongoDB.")
    else:
        print(f"No data found in {file_path}")

# Function to import JSON files into MongoDB
def import_json(file_path, collection, symbol):
    print(f"Importing JSON file: {file_path}")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        # Add the key (first 7 chars of the filename) as a key-value pair in each document
        for record in data:
            record['key'] = symbol
        
        collection.insert_many(data)
    else:
        data['key'] = symbol  # Add key field to the single JSON document
        collection.insert_one(data)
    
    print(f"Inserted data from {file_path} into MongoDB.")

# Function to process extracted files (CSV or JSON)
def process_files(extract_dir, collection):
    for filename in os.listdir(extract_dir):
        file_path = os.path.join(extract_dir, filename)
        
        # Extract the first 7 characters from the filename (e.g., BTCUSDC)
        symbol = filename[:7]
        
        if filename.endswith(".csv"):
            import_csv(file_path, collection, symbol)
        elif filename.endswith(".json"):
            import_json(file_path, collection, symbol)
        else:
            print(f"Skipping unsupported file: {filename}")

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
            process_files(extract_dir, collection)

    print("Data import completed for all ZIP files.")

if __name__ == "__main__":
    main()
