import os
import requests
import zipfile
import pandas as pd
import pandas_ta as ta
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pymongo import MongoClient

# MongoDB Connection Setup
client = MongoClient('mongodb://localhost:27017/')  
db = client['trading_data']
collection = db['btc_usdt_12h']

# Check if data exists in MongoDB
if collection.count_documents({}) > 0:
    # Retrieve data from MongoDB
    stored_data = list(collection.find())
    btc_usdt_data = pd.DataFrame(stored_data)
    
    # Convert the necessary columns back to their appropriate data types
    btc_usdt_data['open_time'] = pd.to_datetime(btc_usdt_data['open_time'])
    btc_usdt_data['close'] = pd.to_numeric(btc_usdt_data['close'])
    print("Data retrieved from MongoDB.")
else:
    # Step 1: Download Historical Data for BTC-USDT (One Year)
    
    # Create a directory for storing data
    os.makedirs('binance_data', exist_ok=True)

    # Define the start date (one year ago)
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()

    # Define the trading pair you want to download (BTC-USDT)
    pair = 'BTCUSDT'

    # Loop through each day from start_date to end_date
    current_date = start_date
    while current_date < end_date:
        # Format the date
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Construct the file URL
        file_url = f"https://data.binance.us/public_data/spot/daily/klines/{pair}/12h/{pair}-12h-{date_str}.zip"
        
        # Define the local file name
        local_file = f"binance_data/{pair}-12h-{date_str}.zip"
        
        # Download the file
        print(f"Downloading {file_url}")
        response = requests.get(file_url)
        
        # Save the file if the download is successful
        if response.status_code == 200:
            with open(local_file, 'wb') as f:
                f.write(response.content)
        else:
            print(f"Failed to download {file_url}")
        
        # Move to the next day
        current_date += timedelta(days=1)

    # Step 2: Extract and Combine the Data
    
    # Directories for data
    data_dir = 'binance_data'
    extracted_dir = 'extracted_data'

    # Create a directory to store extracted files
    os.makedirs(extracted_dir, exist_ok=True)

    # List to store DataFrames
    dfs = []

    # Extract all the zip files and load CSV files into DataFrames
    for filename in os.listdir(data_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(data_dir, filename)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)

    # Combine all CSV files for BTC-USDT
    for csv_filename in os.listdir(extracted_dir):
        if csv_filename.endswith('.csv'):
            csv_path = os.path.join(extracted_dir, csv_filename)
            df = pd.read_csv(csv_path)
            dfs.append(df)

    # Combine all DataFrames into one
    btc_usdt_data = pd.concat(dfs, ignore_index=True)

    # Store data in MongoDB
    collection.insert_many(btc_usdt_data.to_dict('records'))
    print("Data stored in MongoDB.")

# Data Preprocessing
btc_usdt_data['open_time'] = pd.to_datetime(btc_usdt_data['open_time'], unit='ms')

# Ensure the data is sorted by 'open_time' for correct chronological order
btc_usdt_data.sort_values(by='open_time', inplace=True)

# Filter out non-BTC values (BTC prices are generally above $10,000)
btc_usdt_data = btc_usdt_data[btc_usdt_data['close'] > 10000]

# Reset index after filtering
btc_usdt_data.reset_index(drop=True, inplace=True)

# Recalculate technical indicators: RSI, SMA_50, SMA_200
btc_usdt_data['RSI'] = ta.rsi(btc_usdt_data['close'], length=14)
btc_usdt_data['SMA_50'] = ta.sma(btc_usdt_data['close'], length=50)
btc_usdt_data['SMA_200'] = ta.sma(btc_usdt_data['close'], length=200)

# Drop rows with missing values in SMA_50, SMA_200, or RSI
btc_usdt_data.dropna(subset=['SMA_50', 'SMA_200', 'RSI'], inplace=True)

# Price changes (difference between consecutive close prices)
btc_usdt_data['Price_Change'] = btc_usdt_data['close'].diff()

# Lagged features (past values of indicators or prices)
btc_usdt_data['Lag_1_Close'] = btc_usdt_data['close'].shift(1)
btc_usdt_data['Lag_1_RSI'] = btc_usdt_data['RSI'].shift(1)

# Drop rows with missing values after feature engineering (important for modeling)
btc_usdt_data.dropna(subset=['Price_Change', 'Lag_1_Close', 'Lag_1_RSI'], inplace=True)

# Define features (X)
X = btc_usdt_data[['RSI', 'SMA_50', 'SMA_200', 'Price_Change', 'Lag_1_Close']]

# Define the target (y) - Binary classification: 1 for price increase, 0 for price decrease
y_cleaned = (btc_usdt_data['Price_Change'] > 0).astype(int).values.flatten()  # Ensure y_cleaned is binary (0 or 1)
X_cleaned = X  # X is already clean at this point

# Check the shape of X_cleaned and y_cleaned to ensure they are correct
print(f"X_cleaned shape: {X_cleaned.shape}")
print(f"y_cleaned shape: {y_cleaned.shape}")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X_cleaned, y_cleaned, test_size=0.3, random_state=42, shuffle=False)

# Train the Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

# Check the shape of y_test and y_pred to ensure they are correct
print(f"y_test shape: {y_test.shape}")
print(f"y_pred shape: {y_pred.shape}")

# Ensure y_test and y_pred are one-dimensional arrays
print(f"Unique values in y_test: {set(y_test)}")  # Should be {0, 1}
print(f"Unique values in y_pred: {set(y_pred)}")  # Should be {0, 1}

# Evaluate the model performance
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")  # Accuracy score
print(classification_report(y_test, y_pred))  # Detailed classification report

# Calculate daily returns
btc_usdt_data['Returns'] = btc_usdt_data['close'].pct_change()

# Strategy returns based on model predictions (shift to align with future predictions)
btc_usdt_data['Predicted_Signal'] = model.predict(X_cleaned)
btc_usdt_data['Strategy_Returns'] = btc_usdt_data['Returns'] * btc_usdt_data['Predicted_Signal'].shift(1)

# Calculate cumulative returns
btc_usdt_data['Cumulative_Market_Returns'] = (1 + btc_usdt_data['Returns']).cumprod()
btc_usdt_data['Cumulative_Strategy_Returns'] = (1 + btc_usdt_data['Strategy_Returns']).cumprod()

# Plot the results
plt.figure(figsize=(14, 7))
plt.plot(btc_usdt_data['open_time'], btc_usdt_data['Cumulative_Market_Returns'], label='Market Returns')
plt.plot(btc_usdt_data['open_time'], btc_usdt_data['Cumulative_Strategy_Returns'], label='Strategy Returns')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.title('Backtest: Market vs. Strategy Returns')
plt.legend()
plt.show()

# Save the plot as a PNG file
plt.savefig('strategy_vs_market_returns.png')