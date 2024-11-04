import time
import joblib
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pymongo import MongoClient

# Load the trained model
model = joblib.load('random_forest_model.pkl')
print("Model loaded successfully.")

# Initialize storage for actual prices and predictions
actual_prices = []
predicted_trends = []  # Store 1 for predicted increase, 0 for decrease
timestamps = []  # Track time for logging purposes
recent_closes = []  # To keep the last N closes for feature calculation

# Fetch the latest OHLC market data from Kraken
def get_real_time_data(pair='XXBTZUSD', interval=1):
    """Fetches the latest OHLC data from Kraken."""
    url = f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}'
    response = requests.get(url)
    data = response.json()
    if data['error']:
        print(f"Error fetching data: {data['error']}")
        return None
    return data['result'][pair][-1]  # Return the latest OHLC entry

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
    ohlc_data = get_real_time_data()  # Fetch the latest OHLC data
    if ohlc_data is None:
        return previous_close  # Skip this iteration if data fetch failed

    # Extract the latest closing price from the OHLC data
    latest_close = float(ohlc_data[4])  # 4th index is the close price
    recent_closes.append(latest_close)

    # Limit list to max required length (200 for SMA_200 calculation)
    if len(recent_closes) > 200:
        recent_closes.pop(0)

    # Initialize previous_close if it is None
    if previous_close is None:
        previous_close = latest_close  # Avoid NaN for Lag_1_Close on the first run

    # Calculate features
    RSI = compute_rsi(recent_closes)
    SMA_50 = compute_sma(recent_closes, length=50)
    SMA_200 = compute_sma(recent_closes, length=200)
    price_change = latest_close - previous_close

    # Debugging prints for computed features
    print(f"Computed Features - RSI: {RSI}, SMA_50: {SMA_50}, SMA_200: {SMA_200}, Price Change: {price_change}")

    # Create a DataFrame with the latest features for prediction
    latest_data = pd.DataFrame([[RSI, SMA_50, SMA_200, price_change, previous_close]],
                                columns=['RSI', 'SMA_50', 'SMA_200', 'Price_Change', 'Lag_1_Close'])
    # Print the head of latest_data
    print("Latest DataFrame Head (first 5 entries):")
    print(latest_data.head(5))

    # Check for NaN values and handle them
    if latest_data.isnull().values.any():
        print("Warning: NaN values found in features even after sufficient data collected.")
        latest_data = latest_data.fillna(0)  # Replace NaNs with 0

    # Make prediction (1 for price increase, 0 for decrease)
    prediction = model.predict(latest_data)
    predicted_trends.append(prediction[0])
    actual_prices.append(latest_close)
    timestamps.append(datetime.now())  # Store current time for logging purposes

    print(f"Prediction (1 for increase, 0 for decrease): {prediction[0]} - Actual Price: {latest_close}")
    return latest_close  # Return the current close price for use in the next prediction


if __name__ == "__main__":
    previous_close = None

    while True:
        try:
            previous_close = make_prediction(previous_close)
            time.sleep(60)  # Wait for 1 minute before the next prediction
        except Exception as e:
            print(f"Error during prediction: {e}")
            time.sleep(60)  # Retry after 1 minute if there’s an error
