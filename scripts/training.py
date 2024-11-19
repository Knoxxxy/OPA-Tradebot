import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score, confusion_matrix
from pymongo import MongoClient

# MongoDB Connection Setup
client = MongoClient('mongodb://mongodb:27017/')
db = client['OPA_Data']  # Match the database used in preprocessing.py


def train_model(collection_name):
    # Load preprocessed data from MongoDB
    collection = db[collection_name]
    stored_data = list(collection.find({}, {'RSI': 1, 'SMA_50': 1, 'SMA_200': 1, 'Price_Change': 1, 'Lag_1_Close': 1, 'Lag_1_RSI': 1}))
    collection_data = pd.DataFrame(stored_data)

    # Check if data is loaded successfully
    if collection_data.empty:
        print(f"No data found in collection '{collection_name}'. Exiting...")
        return

    # Define features (X) and target (y)
    X = collection_data[['Lag_1_RSI', 'SMA_50', 'SMA_200', 'Lag_1_Close']]
    y = (collection_data['Price_Change'] > 0).astype(int)  # Binary target: 1 if price increased, 0 if not

    # Print the features and target tables
    print("Features (X):")
    print(X.head)  # Print the first 5 entries of features
    print("\nTarget (y):")
    print(y.head)  # Print the first 5 entries of target

    print("Features shape (X.shape):")
    print(X.shape)
    print("\nTarget shape (y.shape):")
    print(y.shape)

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate the model and save predicitions
    y_pred = model.predict(X_test)

    # Calculate evaluation metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)

    # Print evaluation results
    print("Accuracy:", accuracy)
    print("F1 Score:", f1)
    print("Precision: ", precision)
    print("Recall:", recall)
    print("Confusion Matrix:\n", conf_matrix)
    print(classification_report(y_test, y_pred))

    # Save the trained model
    joblib.dump(model, 'random_forest_model.pkl')
    print("Model saved as 'random_forest_model.pkl' inside your project folder.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 training.py <collection_name>")
        sys.exit(1)

    collection_name = sys.argv[1]
    train_model(collection_name)
