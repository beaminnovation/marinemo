import pandas as pd
from joblib import load
import numpy as np

# Load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# Define the features
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']

# Function to process a single row and print results
def process_row(row, previous_prediction=None):
    # Prepare the data row
    X_row = pd.DataFrame([row[features]])
    
    # Normalize the data row
    X_row_scaled = scaler.transform(X_row)
    
    # Predict the traffic type for the current row
    current_prediction = clf_ensemble.predict(X_row_scaled)[0]
    
    # Display the prediction
    print(f"At {row['timestamp']}, predicted traffic type: {current_prediction}")
    
    # Check for change in traffic type
    if previous_prediction and current_prediction != previous_prediction:
        print(f"Change detected at {row['timestamp']} to {current_prediction} traffic.")
    
    # Return the current prediction for the next comparison
    return current_prediction

# Simulate real-time processing
previous_prediction = None
for _, row in pd.read_csv('CPE_normal_medium.csv').iterrows():  # Modify this to test different datasets
    previous_prediction = process_row(row, previous_prediction)
