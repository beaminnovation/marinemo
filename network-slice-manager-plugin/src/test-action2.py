import pandas as pd
import numpy as np
from joblib import load
from confluent_kafka import Consumer, KafkaError, KafkaException
import requests

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


# Function to process messages from Kafka and make predictions
def process_message(msg):
    try:
        # Assuming msg.value() is a CSV line or JSON string with the data
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

    except Exception as e:
        print(f"Failed to process message: {e}")


# Poll Kafka for new messages
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
