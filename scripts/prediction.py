import time
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import requests
from pymongo import MongoClient
import sys

# Load the trained model
model = joblib.load('random_forest_model.pkl')
print("Model loaded successfully.")

# Initialize storage for actual prices and predictions
actual_prices = []
predicted_trends = []  # Store 1 for predicted increase, 0 for decrease
timestamps = []  # Track time for logging purposes


# Fetch historical data from Kraken to prefill recent_closes
def fetch_initial_data(pair='XXBTZUSD', interval=1, limit=200):
    """Fetches recent historical data from Kraken API to preload recent_closes."""
    url = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}'
    response = requests.get(url)
    data = response.json()

    if data['error']:
        print(f"Error fetching initial data: {data['error']}")
        return []

    ohlc_data = data['result'][pair]
    # Ensure all close prices are numeric, converting non-numeric to NaN
    close_prices = pd.to_numeric([candle[4] for candle in ohlc_data], errors='coerce')
    close_prices = [price for price in close_prices if not np.isnan(price)]  # Filter out NaN values
    return close_prices


# Initialize recent closes
recent_closes = fetch_initial_data()
print(f"Loaded {len(recent_closes)} data points to initialize recent_closes.")


# Fetch the latest OHLC market data from Kraken
def get_real_time_data(pair='XXBTZUSD', interval=1):
    """Fetches the latest OHLC data from Kraken."""
    url = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}'
    response = requests.get(url)
    data = response.json()

    if data['error']:
        print(f"Error fetching data: {data['error']}")
        return None

    ohlc_data = data['result'][pair]
    print(f"Number of data points received: {len(ohlc_data)}")

    # Convert the raw data into a pandas DataFrame for easier analysis
    df_ohlc = pd.DataFrame(ohlc_data, columns=["Timestamp", "Open", "High", "Low", "Close", "VWAP", "Volume", "Count"])

    # Ensure all columns are numeric where expected, converting errors to NaN
    df_ohlc = df_ohlc.apply(pd.to_numeric, errors='coerce')
    df_ohlc.dropna(inplace=True)  # Drop rows with NaN values after conversion

    # Display the first 5 entries of the DataFrame as a preview
    print("First 5 entries of OHLC data:")
    print(df_ohlc.head(5))

    return df_ohlc  # Return the whole DataFrame


# Compute RSI using a list of closing prices
def compute_rsi(prices, length=14):
    """Computes RSI given a list of closing prices."""
    if len(prices) < length + 1:
        return np.nan  # Not enough data for RSI
    deltas = np.diff(prices)
    gains = deltas[deltas > 0].sum() / length
    losses = -deltas[deltas < 0].sum() / length
    if losses == 0:
        return 100  # If there are no losses, RSI is maxed at 100
    rs = gains / losses
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Compute SMA using a list of closing prices
def compute_sma(prices, length):
    """Computes Simple Moving Average given a list of closing prices."""
    if len(prices) < length:
        return np.nan  # Not enough data for SMA
    return np.mean(prices[-length:])


def make_prediction(previous_close):
    """Generates a prediction based on the latest data."""
    # Ensure global access to recent_closes
    global recent_closes

    ohlc_data = get_real_time_data()  # Fetch the latest OHLC data
    if ohlc_data is None:
        return previous_close  # Skip this iteration if data fetch failed

    # Ensure all close prices from ohlc_data['Close'] are numeric
    valid_closes = pd.to_numeric(ohlc_data['Close'], errors='coerce').dropna().tolist()

    if not valid_closes:
        print("No valid close prices available in the latest data. Skipping prediction.")
        return previous_close

    # Limit list to max required length (200 for SMA_200 calculation)
    if len(recent_closes) > 200:
        recent_closes = recent_closes[-200:]  # Keep only the most recent 200 entries

    # Check if we have enough data points
    if len(recent_closes) < 200:
        print(f"Not enough data yet. Currently collected {len(recent_closes)} data points. Waiting for more...")
        return previous_close  # Wait until we have at least 200 data points

    # Debugging: Print the current state of recent_closes
    print(f"Total data points in recent_closes: {len(recent_closes)}")
    print("Recent closes (last 5 values):", recent_closes[-5:])

    # Initialize previous_close if it is None
    if previous_close is None:
        # Ensure that previous_close is not None and that there are enough data points
        if len(recent_closes) > 0:
            previous_close = recent_closes[-1]  # Avoid NaN for Lag_1_Close on the first run
        else:
            print("Not enough data for prediction. Waiting for more data.")
            return previous_close  # If there is no data yet, wait

    # Update recent_closes with valid closes from the latest data
    recent_closes.extend(valid_closes)  # Add valid closes from this call
    print(f"Updated recent_closes with valid closes from the latest data (last 5): {recent_closes[-5:]}")

    # Calculate features
    RSI = compute_rsi(recent_closes)
    SMA_50 = compute_sma(recent_closes, length=50)
    SMA_200 = compute_sma(recent_closes, length=200)
    Lag_1_RSI = compute_rsi(recent_closes[:-1])

    # Debugging prints for calculated features which are used for prediction
    print(f"Computed Features - RSI: {RSI}, SMA_50: {SMA_50}, SMA_200: {SMA_200}, Lag_1_RSI: {Lag_1_RSI}")

    # Create a DataFrame with the latest features for prediction
    latest_data = pd.DataFrame([[Lag_1_RSI, SMA_50, SMA_200, previous_close]],
                               columns=['Lag_1_RSI', 'SMA_50', 'SMA_200', 'Lag_1_Close'])

    # Check for NaN values and handle them
    if latest_data.isnull().values.any():
        print("Warning: NaN values found in features even after sufficient data collected.")
        latest_data = latest_data.fillna(0)  # Replace NaNs with 0
    # Print the head of latest_data
    print("Latest DataFrame with calculated features used for prediction: ")
    print(latest_data)

    # Check for NaN values and handle them
    if latest_data.isnull().values.any():
        print("Warning: NaN values found in features even after sufficient data collected.")
        latest_data = latest_data.fillna(0)  # Replace NaNs with 0

    # Make prediction (1 for price increase, 0 for decrease)
    prediction = model.predict(latest_data)
    predicted_trends.append(prediction[0])
    actual_prices.append(recent_closes[-1])  # Use the most recent close for actual prices
    timestamps.append(datetime.now())  # Store current time for logging purposes

    print(f"Prediction (1 for increase, 0 for decrease): {prediction[0]} - Actual Price: {recent_closes[-1]}")
    return recent_closes[-1]  # Return the current close price for use in the next prediction



# MongoDB connection settings
def get_mongo_connection(collection_name):
    """
    Connects to the MongoDB database and returns a collection.
    Allows specifying the collection name to use.
    """
    try:
        client = MongoClient("mongodb://mongodb:27017/")
        db = client['OPA_Data']  # Using the same database
        collection = db[collection_name]  # Dynamic collection
        return collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    previous_close = None

    while True:
        try:
            previous_close = make_prediction(previous_close)
           # Ensure there is at least one prediction and actual price before saving

            time.sleep(60)  # Wait for 1 minute before the next prediction
        except Exception as e:
            print(f"Error during prediction: {e}")
            time.sleep(60)  # Retry after 1 minute if there’s an error