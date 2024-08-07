import pandas as pd
from joblib import load
import numpy as np

# Load the test dataset
test_data = pd.read_csv('CPE_normal_medium.csv')  # Modify this to test different datasets

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

# Test and print results on the test dataset
print("\nTesting on test dataset:")
test_and_print_results(test_data, X_test_scaled, clf_ensemble)
