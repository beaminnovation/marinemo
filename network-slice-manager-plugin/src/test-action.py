import pandas as pd
from joblib import load
import numpy as np
import requests

# Load the test dataset
test_data = pd.read_csv('CPE_normal_medium.csv')  # Modify this to test different datasets
unique_ids = test_data['id'].unique()

for id in unique_ids:
    if id == 'A4FC77-3TG01797-FVN2350009C9':
        imsi = '999700000056834'

# Load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# Define the features
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']
X_test = test_data[features]

# Normalize the test data
X_test_scaled = scaler.transform(X_test)

# Function to test and print results
def test_and_print_results(test_data, X_test_scaled, clf):
    y_test_pred = clf.predict(X_test_scaled)
    predictions_df = test_data.copy()
    predictions_df['predicted_traffic_type'] = y_test_pred
    traffic_counts = predictions_df['predicted_traffic_type'].value_counts()

    print("Predicted Traffic Types for Each Row:")
    print(predictions_df[['timestamp', 'predicted_traffic_type']])

    print("\nTraffic Type Counts:")
    print(traffic_counts)

    alerts = []
    for i in range(1, len(predictions_df)):
        if predictions_df['predicted_traffic_type'].iloc[i] != predictions_df['predicted_traffic_type'].iloc[i - 1]:
            alerts.append((predictions_df['timestamp'].iloc[i], predictions_df['predicted_traffic_type'].iloc[i]))
    
    print("\nChange Alerts:")
    for alert in alerts:
        print(f"Change detected at {alert[0]} to {alert[1]} traffic.")
        if alert[1] == 'high':
            headers = {
                'Content-Type': 'application/json',
            }

            json_data = {
                'imsi': imsi,
                'downlink-ambr-value': 50,
                'downlink-ambr-unit': 2,
                'uplink-ambr-value': 50,
                'uplink-ambr-unit': 2,
            }

            response = requests.post('http://192.168.0.91:5000/update-subscriber', headers=headers, json=json_data)

# Test and print results on the test dataset
print("\nTesting on test dataset:")
test_and_print_results(test_data, X_test_scaled, clf_ensemble)
