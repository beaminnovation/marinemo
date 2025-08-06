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
from datetime import datetime, timezone

# Load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# Define the features
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']

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
action_flag = 0
scenario_flag = 1
counter = 0

def fetch_data_from_api(
    imsi: str = "999991000000001",
    base_url: str = "http://127.0.0.1:3000",
    window_seconds: int = 25 * 60
):
    try:
        from datetime import datetime, timedelta, timezone
        # Define the interval: end = now - 3s, start = end - window
        end_dt = datetime.now(timezone.utc) - timedelta(seconds=3)
        start_dt = end_dt - timedelta(seconds=window_seconds)

        params = {
            "report-type": "ue-usage",
            "tgt_ue": f"imsi-{imsi}",
            "start": end_dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z").replace("Z", "Z"),  # placeholder, overwritten below
            "end":   end_dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        # Set proper start after end computed above
        params["start"] = start_dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        url = f"{base_url}/api/v1.0/cnc/monitoring-report"
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            row = response.json()
            return pd.DataFrame([row])
        else:
            print(f"Failed to fetch data from API. Status code: {response.status_code} | body: {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return None

def save_monitoring_data_to_csv(data):
    # Append the monitoring data to the CSV file, ensuring it is not overwritten between runs
    file_exists = os.path.isfile(monitoring_csv_path)

    # Prepare the data for saving
    data_to_save = data[['timestamp', 'URLLC_BytesReceived', 'URLLC_BytesSent',
                         'URLLC_Received_thrp_Mbps',
                         'URLLC_Sent_thrp_Mbps']]

    # Save the data to the CSV file
    data_to_save.to_csv(monitoring_csv_path, mode='a', header=not file_exists, index=False)

# Function to save predictions to CSV
def save_prediction_to_csv(timestamp, alert_type):
    # Create a DataFrame with the new prediction
    new_data = pd.DataFrame([[timestamp, alert_type]], columns=['timestamp', 'alertType'])

    # Append the new prediction to the CSV file, ensuring it is not overwritten between runs
    file_exists = os.path.isfile(alerts_csv_path)
    new_data.to_csv(alerts_csv_path, mode='a', header=not file_exists, index=False)

def process_and_predict(testbed):
    global traffic_flag
    global action_flag
    global scenario_flag
    global counter
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
        current_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f UTC')

        # Save each prediction to the CSV
        for prediction in y_test_pred:
            save_prediction_to_csv(current_timestamp, prediction)

        imsi = "999991000000001"
        if action_flag == 0:
            print("Decision engine running. Fetching traffic data.")

        # Check if the traffic is estimated as high
        if 'high' in y_test_pred and counter != 9:
            traffic_flag = 1
            counter = counter + 1
            print("Traffic is high, setting flag to 1.")
            if action_flag == 0:
                action_flag = 1
                # scenario 0 - update unprioritized UE profile with diminished throughput cap
                if scenario_flag == 0:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data = {
                        "_id": "profile",
                        "dnn": "internet",             # must match an allowed DNN in the engine
                        "5gQosProfile": {"5qi": 9},    # accepted 5qi in the mock
                        "sessionAmbr": {
                            "downlink": f"{testbed['downlink-ambr-value']} {testbed['downlink-ambr-unit']}",
                            "uplink":   f"{testbed['uplink-ambr-value']} {testbed['uplink-ambr-unit']}",
                        }
                    }

                    response = requests.put('http://127.0.0.1:3000/api/v1.0/cnc-configuration/cnc-subscription-profile/profile', headers=headers, json=json_data)

                # scenario 1 - create new capped slice and provision the unprioritized UE to it
                elif scenario_flag == 1:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data1 = {
                        "sliceName": "slice-nemo",
                        "activate_slice": 1,  # run validation against mock RAN
                        "SliceDescription": "Lab slice with throughput caps",
                        "ServiceProfile": {
                            "PLMNIdList": [{"mcc": "999", "mnc": "99"}],
                            "SNSSAIList": [{"sst": 1, "sd": "000002"}],
                            "dnn": "internet",

                            # Throughput caps (both per-slice and per-UE for convenience)
                            "DLThptPerSlice": {"value": testbed["downlink-ambr-value"],
                                               "unit": testbed["downlink-ambr-unit"]},
                            "ULThptPerSlice": {"value": testbed["uplink-ambr-value"],
                                               "unit": testbed["uplink-ambr-unit"]},
                            "DLThptPerUE": {"value": testbed["downlink-ambr-value"],
                                            "unit": testbed["downlink-ambr-unit"]},
                            "ULThptPerUE": {"value": testbed["uplink-ambr-value"],
                                            "unit": testbed["uplink-ambr-unit"]},
                        },
                        "NetworkSliceSubnet": {
                            "EpTransport": {
                                "qosProfile": 9,
                                "epApplication": ["internet"]
                            }
                        }
                    }

                    json_data2 = {
                        "imsi": imsi,
                        "profile": "profile",
                        "slice": "slice-nemo"
                    }

                    response1 = requests.post('http://127.0.0.1:3000/api/v1.0/network-slice/slice-instance', headers=headers, json=json_data1)
                    response2 = requests.put('http://127.0.0.1:3000/api/v1.0/cnc-subscriber-management/999991000000001', headers=headers, json=json_data2)

        elif counter == 9:
            traffic_flag = 0
            print("Traffic is normal, setting flag to 0.")
            if action_flag == 1:
                action_flag = 0
                # scenario 0 - revert unprioritized UE profile to default throughput cap
                if scenario_flag == 0:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data = {
                        "_id": "profile",
                        "dnn": "internet",  # must match an allowed DNN in the engine
                        "5gQosProfile": {"5qi": 9},  # accepted 5qi in the mock
                        "sessionAmbr": {
                            "downlink": 100,
                            "uplink": 100,
                        }
                    }

                    response = requests.put('http://127.0.0.1:3000/api/v1.0/cnc-configuration/cnc-subscription-profile/profile', headers=headers, json=json_data)

                # scenario 1 - re-provision the unprioritized UE to the default slice and delete capped slice
                elif scenario_flag == 1:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data2 = {
                        "imsi": imsi,
                        "profile": "profile",
                        "slice": "slice-default"
                    }

                    response2 = requests.put('http://127.0.0.1:3000/api/v1.0/cnc-subscriber-management/999991000000001', headers=headers, json=json_data2)
                    response1 = requests.delete('http://127.0.0.1:3000/api/v1.0/network-slice/slice-instance/slice-nemo',headers=headers)


if __name__ == "__main__":
    testbed_id = 1
    filename = f'testbed-{testbed_id}.json'

    # Read JSON file
    try:
        with open(filename, 'r') as file:
            testbed = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")

    while True:
        process_and_predict(testbed)
        time.sleep(5)  # Wait for 5 seconds before polling the API again