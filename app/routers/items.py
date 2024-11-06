# app/routers/items.py

from fastapi import APIRouter, FastAPI, File, UploadFile, HTTPException, Query
from ..models import OHLCDataModel
from ..database import db
from typing import List, Optional
from datetime import datetime
import pandas as pd
import zipfile
import io

router = APIRouter()

# 1. Single Datapoint Write Endpoint
@router.post("/ohlc/data-point")
async def create_data_point(data: OHLCDataModel):
    new_data = await db["ohlc_data"].insert_one(data)       #New Collection ohlc_data, might need changing
    return {"message": "Data point added successfully", "id": str(new_data.inserted_id)}

# 2. Bulk Data Upload Endpoint
@router.post("/ohlc/upload-file")
async def upload_file(file: UploadFile = File(...)):
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
    await db["ohlc_data"].insert_many(data_list)   #New Collection ohlc_data, might need changing
    return {"message": "File processed and data uploaded", "records_added": len(data_list)}

# 3. Read Data with Filters

@router.get("/ohlc/data")
async def get_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    # Dynamically select the collection based on the symbol
    collection = db[symbol]  # This will dynamically refer to the collection with the name 'symbol'
    
    # Initialize the query dictionary
    query = {}
    
    # Apply start_date filter if provided (converted to milliseconds)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)  # Convert to datetime
            start_timestamp = datetime_to_timestamp(start_dt)  # Convert to milliseconds timestamp
            query["open_time"] = {"$gte": start_timestamp}  # Filter for open_time >= start_timestamp
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Please use ISO 8601 format.")
    
    # Apply end_date filter if provided (converted to milliseconds)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)  # Convert to datetime
            end_timestamp = datetime_to_timestamp(end_dt)  # Convert to milliseconds timestamp
            query["close_time"] = {"$lte": end_timestamp}  # Filter for close_time <= end_timestamp
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Please use ISO 8601 format.")
    
    # Query the dynamically selected collection
    data = await collection.find(query).to_list(1000)  # Fetch up to 1000 records

    # If no data found
    if not data:
        raise HTTPException(status_code=404, detail="No data found for the given criteria.")
    
    return data


"""
# 4. Delete Data
@router.delete("/ohlc/data")
async def delete_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {"symbol": symbol}
    if start_date:
        query["timestamp"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        query["timestamp"]["$lte"] = datetime.fromisoformat(end_date)

    delete_result = await db["ohlc_data"].delete_many(query)
    return {"message": "Data deleted", "count": delete_result.deleted_count}
"""
