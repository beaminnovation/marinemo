import json
import pandas as pd
import numpy as np
from joblib import load
from confluent_kafka import Consumer, KafkaError, KafkaException
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# Define the features
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']

# Kafka configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest'
}

# Create Kafka consumer
consumer = Consumer(conf)
consumer.subscribe(['test-data'])

# InfluxDB configuration
influxdb_url = 'http://localhost:8086'
token = 'your_influxdb_token'
org = 'your_org'
bucket = 'your_bucket'

# Connect to InfluxDB
client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

def process_message(msg):
    try:
        test_data = pd.read_json(msg.value())  # Adjust if data is in CSV or other format

        unique_ids = test_data['id'].unique()

        for id in unique_ids:
            if id == 'A4FC77-3TG01797-FVN2350009C9':
                imsi = '999700000056834'

        # Extract the features and scale them
        X_test = test_data[features]
        X_test_scaled = scaler.transform(X_test)

        # Make predictions
        y_test_pred = clf_ensemble.predict(X_test_scaled)

        # Combine predictions with original data
        predictions_df = test_data.copy()
        predictions_df['predicted_traffic_type'] = y_test_pred
        print(predictions_df[['timestamp', 'predicted_traffic_type']])

        traffic_counts = predictions_df['predicted_traffic_type'].value_counts()
        if traffic_counts.get('high', 0) > 2:
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

        alerts = []
        for i in range(1, len(predictions_df)):
            if predictions_df['predicted_traffic_type'].iloc[i] != predictions_df['predicted_traffic_type'].iloc[i - 1]:
                alert_time = predictions_df['timestamp'].iloc[i]
                alert_type = predictions_df['predicted_traffic_type'].iloc[i]
                alerts.append((alert_time, alert_type))
                point = Point("traffic_alert").tag("imsi", imsi).field("alert_type", alert_type).time(alert_time, WritePrecision.NS)
                write_api.write(bucket=bucket, org=org, record=point)

    except Exception as e:
        print(f"Failed to process message: {e}")

def decision_engine(testbed_id):
    filename = f'testbed-{testbed_id}.json'

    # Read JSON file
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
        return
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")
        return

    # Extract data
    testbed_id = data['testbed-id']
    prioritized_users = data['prioritized-users']
    downlink_ambr_value = data['downlink-ambr-value']
    downlink_ambr_unit = data['downlink-ambr-unit']
    uplink_ambr_value = data['uplink-ambr-value']
    uplink_ambr_unit = data['uplink-ambr-unit']
    qci = data['qci']

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())
            process_message(msg)
    finally:
        consumer.close()

if __name__ == '__main__':
    testbed_id = 1
    decision_engine(testbed_id)
