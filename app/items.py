# app/routers/items.py

import docker
from fastapi import APIRouter, FastAPI, File, UploadFile, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from models import OHLCDataModel
from database import db
from typing import List, Optional
from datetime import datetime
import pandas as pd
import zipfile
import io
import os
from io import BytesIO
from bson import ObjectId
from pymongo import MongoClient
import preprocessing
import base64

router = APIRouter()
client = docker.from_env()
ubuntu_container = client.containers.get("ubuntu_script_runner")

# Helper function to convert datetime to timestamp
def datetime_to_timestamp(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)

# 1. Single Datapoint Write Endpoint
@router.post("/data-point")
async def create_data_point(data: OHLCDataModel, symbol: str):
    """
    Entry point for singular Data Entry
    """
    new_data = await db[symbol].insert_one(data)       #New Collection ohlc_data, might need changing
    return {"message": "Data point added successfully", "id": str(new_data.inserted_id)}

# 2. Bulk Data Upload Endpoint
@router.post("/upload-file")
async def upload_file(symbol: str, file: UploadFile = File(...)):
    """
    Upload Data in ZIP or CSV format for direct Data Entry.\n
    The File doesnt get saved, and is directly inputted into MongoDB.
    """
    if file.content_type not in ["application/zip", "text/csv"]:
        raise HTTPException(status_code=400, detail="Only ZIP or CSV files are accepted")

    data_list = []

    if file.content_type == "application/zip":
        with zipfile.ZipFile(io.BytesIO(await file.read())) as zip_file:
            for filename in zip_file.namelist():
                if filename.endswith(".csv"):
                    with zip_file.open(filename) as csv_file:
                        df = pd.read_csv(csv_file)
                        data_list.extend(df.to_dict(orient="records"))
    else:
        df = pd.read_csv(io.BytesIO(await file.read()))
        data_list = df.to_dict(orient="records")

    # Bulk insert into MongoDB
    await db[symbol].insert_many(data_list)   #New Collection ohlc_data, might need changing
    return {"message": "File processed and data uploaded", "records_added": len(data_list)}

# 3. Read Data with Filters

@router.get("/data")
async def get_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    
    """
    Returns Data from MongoDB with a symbol (i.e. BTCUSD), and a start end end date
    """
    # Dynamically select the collection based on the symbol
    collection = db[symbol]
    
    # Initialize the query dictionary
    query = {}
    
    # Apply start_date filter if provided (converted to milliseconds)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            start_timestamp = datetime_to_timestamp(start_dt)
            query["open_time"] = {"$gte": start_timestamp}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Please use ISO 8601 format.")
    
    # Apply end_date filter if provided (converted to milliseconds)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            end_timestamp = datetime_to_timestamp(end_dt)
            query["close_time"] = {"$lte": end_timestamp}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Please use ISO 8601 format.")
    
    # Query the dynamically selected collection
    data = await collection.find(query, {"_id": 0}).to_list(1000)

    # If no data found
    if not data:
        raise HTTPException(status_code=404, detail="No data found for the given criteria.")
    
    # Return the serialized data
    
    return data

# Get Collection names Endpoint

@router.get("/trade-pairs")
async def get_trade_pairs():
    """
    Returns the names of all existing Collections in the DB
    """
    collection_names = await db.list_collection_names()
    return collection_names



@router.post("/run-script/{script_name}")
async def run_script(script_name: str):
    # Check if the script file exists
    
    """
    Run a script on the Ubuntu Script Runner container
    """
    script_path = f"/scripts/{script_name}"
    
    
    # Access the ubuntu_script_runner container
    try:
        # Run the script inside the ubuntu container
        exit_code, output = ubuntu_container.exec_run(f"python3 /scripts/{script_name}", stdout=True, stderr=True)
        if exit_code != 0:
            return {"error": output.decode('utf-8')}
        
        return {"message": "Script executed successfully", "output": output.decode('utf-8')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute script: {str(e)}")

@router.get("/scripts-available")
async def get_script_files():
    """
    Returns all file names in the Scripts folder of the scriptrunner
    """
    try:
       
        # Run the 'ls' command inside the Ubuntu container to list files in the /scripts directory
        exit_code, output = ubuntu_container.exec_run("ls /scripts", stdout=True, stderr=True)
        
        # Decode the output from bytes to a string
        files = output.decode().splitlines()  # Split by new lines to get individual file names
        
        # Return the list of files
        return {"files": files}
    
    except docker.errors.NotFound:
        return {"error": "Ubuntu container not found"}
    except Exception as e:
        return {"error": str(e)}
    
@router.post("/upload-script/")
async def upload_script(script: UploadFile = File(...)):
    """
    Currently not functional.\n
    Upload a Script into the scriptfolder
    """
    
    UPLOAD_FOLDER = "/scripts"
    #os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Ensure the uploaded file has a .py extension
    if not script.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are allowed")
    
    file_path = os.path.join(UPLOAD_FOLDER, script.filename)
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as f:
            content = await script.read()  # Read file content asynchronously
            f.write(content)  # Write content to the file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    return {"filename": script.filename, "message": "File uploaded successfully!"}


    

"""
# 4. Delete Data
@router.delete("/data")
async def delete_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {"symbol": symbol}
    if start_date:
        query["timestamp"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        query["timestamp"]["$lte"] = datetime.fromisoformat(end_date)

    delete_result = await db["ohlc_data"].delete_many(query)
    return {"message": "Data deleted", "count": delete_result.deleted_count}
"""
