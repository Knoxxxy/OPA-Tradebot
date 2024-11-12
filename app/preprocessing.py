from fastapi import FastAPI
from fastapi.responses import JSONResponse
import pandas as pd
import pandas_ta as ta
from pymongo import MongoClient
from datetime import datetime, timedelta
import database

# FastAPI app instance
app = FastAPI()

# MongoDB connect settings
async def get_mongo_connection(symbol):
    db = database.db
    historical_collection = db[symbol]
    preprocessed_collection = db[f'preprocessed_{symbol}_data']
    print("Connected to MongoDB successfully.")
    return historical_collection, preprocessed_collection

# Function to load historical data from MongoDB
async def load_data_from_mongodb(collection, years=2):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)

    # Query MongoDB for data within the last two years
    query = {"open_time": {"$gte": start_date, "$lte": end_date}}

    # Retrieve data and convert to DataFrame
    cursor = collection.find(query)
    historical_data = pd.DataFrame(await cursor.to_list(length=None))

    # If less than 2 years of data, get all available data
    if historical_data.empty:
        cursor = collection.find() 
        historical_data = pd.DataFrame(await cursor.to_list(length=None))

    return historical_data

# Function to preprocess data
async def preprocess_data(historical_data):
    # Convert 'open_time' to datetime if not already in that format
    if historical_data['open_time'].dtype != 'datetime64[ns]':
        historical_data['open_time'] = pd.to_datetime(historical_data['open_time'], unit='ms')

    # Sort by 'open_time'
    historical_data.sort_values(by='open_time', inplace=True)

    # Filter out non-BTC values (optional: assuming BTC is always over $10,000)
    historical_data = historical_data[historical_data['close'] > 1000]

    # Reset index
    historical_data.reset_index(drop=True, inplace=True)

    # Calculate technical indicators: RSI, SMA_50, SMA_200
    historical_data['RSI'] = ta.rsi(historical_data['close'], length=14)
    historical_data['SMA_50'] = ta.sma(historical_data['close'], length=50)
    historical_data['SMA_200'] = ta.sma(historical_data['close'], length=200)

    # Calculate additional features: Price_Change, Lag_1_Close, Lag_1_RSI
    historical_data['Price_Change'] = historical_data['close'].pct_change() * 100  # Percentage change in close price
    historical_data['Lag_1_Close'] = historical_data['close'].shift(1)  # 1-period lagged close price
    historical_data['Lag_1_RSI'] = historical_data['RSI'].shift(1)

    # Drop rows with missing values (due to indicator calculation)
    historical_data.dropna(subset=['SMA_50', 'SMA_200', 'RSI'], inplace=True)

    return historical_data

# Store preprocessed data in a new MongoDB collection
async def store_preprocessed_data(preprocessed_df, collection):
    # Convert DataFrame to dictionary and store in MongoDB
    collection.insert_many(preprocessed_df.to_dict('records'))
    print("Preprocessed Data Sample:")
    print(preprocessed_df.head())

# Main function for preprocessing
async def preprocessing_ml_data(symbol):
    # Connect to MongoDB
    historical_collection, preprocessed_collection = await get_mongo_connection(symbol)

    # Load historical data from MongoDB (up to 2 years, or all available data if less)
    historical_data = await load_data_from_mongodb(historical_collection, years=2)  # Await this async function

    # Preprocess the data
    preprocessed_data = await preprocess_data(historical_data)  # Await this async function

    # Store the preprocessed data into a new MongoDB collection
    await store_preprocessed_data(preprocessed_data, preprocessed_collection)  # Await this async function

    return "Preprocessing completed and data stored in MongoDB."

# FastAPI endpoint to trigger the preprocessing
@app.post("/preprocess/{symbol}")
async def trigger_preprocessing(symbol: str):
    result = await preprocessing_ml_data(symbol)
    return JSONResponse(content={"message": result})