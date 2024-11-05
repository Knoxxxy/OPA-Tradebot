import time
import joblib
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
from pymongo import MongoClient

# Use MongoDB URI from the environment variable
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/trading_data")
client = MongoClient(mongo_uri)
db = client['trading_data']
collection = db['btc_usdt_1m']
# Load the trained model
model = joblib.load('random_forest_model.pkl')
print("Model loaded successfully.")

# Initialize storage for actual prices and predictions
actual_prices = []
predicted_trends = []  # Store 1 for predicted increase, 0 for decrease
timestamps = []  # Track time for plotting

# Fetch historical data from Binance to prefill recent closes
def fetch_historical_data(pair='BTCUSDT', interval='1m', limit=200):
    """Fetches recent historical data from Binance API to preload recent_closes."""
    url = f'https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    close_prices = [float(candle[4]) for candle in data]  # 4th index is the close price
    return close_prices

# Initialize recent closes with historical data
recent_closes = fetch_historical_data()
print(f"Loaded {len(recent_closes)} historical data points to recent_closes.")

def get_real_time_data(pair='BTCUSDT'):
    """Fetches the latest market data from Binance (or another exchange API)."""
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={pair}'
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

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

def compute_sma(prices, length=50):
    """Computes Simple Moving Average given a list of closing prices."""
    if len(prices) < length:
        return np.nan  # Not enough data for SMA
    return np.mean(prices[-length:])

def make_prediction(previous_close):
    """Generates a prediction based on the latest data."""
    latest_close = get_real_time_data()
    recent_closes.append(latest_close)
    
    # Limit list to max required length (200 for SMA_200 calculation)
    if len(recent_closes) > 200:
        recent_closes.pop(0)

    # Initialize previous_close if it is None
    if previous_close is None:
        previous_close = latest_close  # Avoid NaN for Lag_1_Close on the first run

    # Calculate features
    RSI = compute_rsi(recent_closes, length=14)
    SMA_50 = compute_sma(recent_closes, length=50)
    SMA_200 = compute_sma(recent_closes, length=200)
    price_change = latest_close - previous_close

    # Debugging prints for computed features
    print(f"Computed Features - RSI: {RSI}, SMA_50: {SMA_50}, SMA_200: {SMA_200}, Price Change: {price_change}")

    # Create a DataFrame with the latest features for prediction
    latest_data = pd.DataFrame([[RSI, SMA_50, SMA_200, price_change, previous_close]], 
                               columns=['RSI', 'SMA_50', 'SMA_200', 'Price_Change', 'Lag_1_Close'])
    
    # Check for NaN values and handle them
    if latest_data.isnull().values.any():
        print("Warning: NaN values found in features even after sufficient data collected.")
        latest_data = latest_data.fillna(0)  # Replace NaNs with 0, or choose an appropriate value
    
    # Make prediction (1 for price increase, 0 for decrease)
    prediction = model.predict(latest_data)
    predicted_trends.append(prediction[0])
    actual_prices.append(latest_close)
    timestamps.append(datetime.now())  # Store current time for plotting

    print(f"Prediction (1 for increase, 0 for decrease): {prediction[0]} - Actual Price: {latest_close}")
    return latest_close  # Return the current close price for use in the next prediction

def plot_predictions():
    """Plots the last 100 data points of actual market prices versus predicted trend and saves as PNG."""
    plt.clf()  # Clear the previous plot
    plt.plot(timestamps[-100:], actual_prices[-100:], label='Actual Price', color='blue')
    plt.plot(timestamps[-100:], predicted_trends[-100:], label='Predicted Trend (1=Increase, 0=Decrease)', color='red', linestyle='--')
    plt.xlabel('Time')
    plt.ylabel('Price / Trend')
    plt.legend()
    plt.title('Actual Market Price vs Model Prediction (Last 100 points)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save each plot with a unique name based on the current time
    plt.savefig(f'prediction_plot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')

if __name__ == "__main__":
    previous_close = None

    while True:
        try:
            previous_close = make_prediction(previous_close)

            # Save the plot after every prediction
            plot_predictions()

            time.sleep(60)  # Wait for 1 minute before the next prediction
        except Exception as e:
            print(f"Error during prediction: {e}")
            time.sleep(60)  # Retry after 1 minute if there’s an error

