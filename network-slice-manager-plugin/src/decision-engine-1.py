import json
import pandas as pd
import numpy as np
from joblib import load
import requests
import time
from confluent_kafka import Consumer, KafkaError, KafkaException
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
import datetime

# Load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# Define the features
features = ['URLLC_Sent_thrp_Mbps', 'BytesSent', 'BytesReceived', 'URLLC_Received_thrp_Mbps']

# CSV file to store predictions
alerts_csv_path = 'traffic_change_alerts_1.csv'
monitoring_csv_path = 'monitoring-1.csv'

# InfluxDB configuration
influxdb_url = 'http://localhost:8086'
token = 'your_influxdb_token'
org = 'your_org'
bucket = 'your_bucket'

# Connect to InfluxDB
client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Define the flag
traffic_flag = 0


def fetch_data_from_api():
    try:
        # Fetch the data from the API
        response = requests.get('http://localhost:5001/cpe-monitoring')
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            print(f"Failed to fetch data from API. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return None

# Function to save monitoring data to CSV
def save_monitoring_data_to_csv(data):
    # Append the monitoring data to the CSV file, ensuring it is not overwritten between runs
    file_exists = os.path.isfile(monitoring_csv_path)

    # Prepare the data for saving
    data_to_save = data[['timestamp', 'id', 'BytesReceived_URLLC', 'BytesSent_URLLC',
                         'URLLC_BytesReceived', 'URLLC_BytesSent', 'URLLC_Received_thrp_Mbps',
                         'URLLC_Sent_thrp_Mbps', 'RTT']]

    # Save the data to the CSV file
    data_to_save.to_csv(monitoring_csv_path, mode='a', header=not file_exists, index=False)

# Function to save predictions to CSV
def save_prediction_to_csv(timestamp, alert_type):
    # Create a DataFrame with the new prediction
    new_data = pd.DataFrame([[timestamp, alert_type]], columns=['timestamp', 'alertType'])

    # Append the new prediction to the CSV file, ensuring it is not overwritten between runs
    file_exists = os.path.isfile(alerts_csv_path)
    new_data.to_csv(alerts_csv_path, mode='a', header=not file_exists, index=False)

def process_and_predict(data):
    global traffic_flag
    # Fetch the data
    data = fetch_data_from_api()
    if data is not None:
        # Save monitoring data to CSV
        save_monitoring_data_to_csv(data)

        # Extract the features and scale them
        X_test = data[features]
        X_test_scaled = scaler.transform(X_test)

        # Make predictions
        y_test_pred = clf_ensemble.predict(X_test_scaled)

        # Get the current timestamp
        current_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f UTC')

        # Save each prediction to the CSV
        for prediction in y_test_pred:
            save_prediction_to_csv(current_timestamp, prediction)

        imsi = "001010000000004"

        # Check if the traffic is estimated as medium
        if 'medium' in y_test_pred:
            traffic_flag = 1
            print("Traffic is medium, setting flag to 1.")
            headers = {
                'Content-Type': 'application/json',
            }

            json_data = {
                'imsi': imsi,
                'downlink-ambr-value': data['downlink-ambr-value'],
                'downlink-ambr-unit': data['downlink-ambr-unit'],
                'uplink-ambr-value': data['uplink-ambr-value'],
                'uplink-ambr-unit': data['uplink-ambr-unit'],
            }

            response = requests.post('http://192.168.0.91:5000/update-subscriber', headers=headers, json=json_data)
        else:
            traffic_flag = 0
            print("Traffic is not medium, flag remains 0.")


if __name__ == "__main__":
    testbed_id = 1
    filename = f'testbed-{testbed_id}.json'

    # Read JSON file
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")

    while True:
        process_and_predict(data)
        time.sleep(5)  # Wait for 5 seconds before polling the API again
