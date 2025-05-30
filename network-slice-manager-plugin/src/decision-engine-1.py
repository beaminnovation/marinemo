import json
import pandas as pd
import numpy as np
import requests
import time
import os
from joblib import load
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, KafkaException
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# load the trained model and scaler
clf_ensemble = load('traffic_model.joblib')
scaler = load('scaler.joblib')

# define the ML model features
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']

# CSV file to store predictions
alerts_csv_path = 'traffic_change_alerts_1.csv'

# CSV file to store CPE monitoring data
monitoring_csv_path = 'monitoring-1.csv'

# configure InfluxDB connection
influxdb_url = 'your_url'
token = 'your_influxdb_token'
org = 'your_org'
bucket = 'your_bucket'

client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# flags
traffic_flag = 0    # global flag for identifying the traffic type (0 = normal, 1 = high)
action_flag = 0     # global flag for identifying if there any scenario was executed (0 = no, 1 = yes)
scenario_flag = 0   # switches between 0 (updated user profile) and 1 (new slice and updated user profile) scenarios

def fetch_data_from_api():
    try:
        # fetch the data from the testbed monitoring API
        response = requests.get('http://192.168.0.91:5001/cpe-monitoring')
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            print(f"Failed to fetch data from API. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return None

# save monitoring data to the target CSV file
def save_monitoring_data_to_csv(data):
    
    file_exists = os.path.isfile(monitoring_csv_path)

    # prepare the data for saving
    data_to_save = data[['timestamp', 'id', 'URLLC_BytesReceived', 'URLLC_BytesSent',
                         'URLLC_Received_thrp_Mbps',
                         'URLLC_Sent_thrp_Mbps', 'RTT']]

    # save the data to the CSV file
    data_to_save.to_csv(monitoring_csv_path, mode='a', header=not file_exists, index=False)

# save predictions to the target CSV file
def save_prediction_to_csv(timestamp, alert_type):
    
    # create a DataFrame with the new prediction
    new_data = pd.DataFrame([[timestamp, alert_type]], columns=['timestamp', 'alertType'])

    # append the new prediction to the CSV file
    file_exists = os.path.isfile(alerts_csv_path)
    new_data.to_csv(alerts_csv_path, mode='a', header=not file_exists, index=False)

def process_and_predict(testbed):
    
    global traffic_flag
    global action_flag
    global scenario
    
    # fetch the CPE monitoring data
    data = fetch_data_from_api()
    if data is not None:
        # save monitoring data to the target CSV file
        save_monitoring_data_to_csv(data)

        # extract the features and scale them
        X_test = data[features]
        X_test_scaled = scaler.transform(X_test)

        # make predictions
        y_test_pred = clf_ensemble.predict(X_test_scaled)

        # get the current timestamp
        current_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f UTC')

        # save each prediction to the target CSV file
        for prediction in y_test_pred:
            save_prediction_to_csv(current_timestamp, prediction)

        imsi = "001010000000004"

        # check if the traffic is estimated as high
        if 'high' in y_test_pred:
            traffic_flag = 1
            
            print("Traffic is high, setting flag to 1.")
            if action_flag == 0:
                action_flag = 1

                # scenario 0 - update unprioritized UE profile with diminished throughput cap
                if scenario_flag == 0:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data = {
                        'imsi': imsi,
                        'downlink-ambr-value': testbed['downlink-ambr-value'],
                        'downlink-ambr-unit': testbed['downlink-ambr-unit'],
                        'uplink-ambr-value': testbed['uplink-ambr-value'],
                        'uplink-ambr-unit': testbed['uplink-ambr-unit'],
                    }

                    response = requests.post('http://192.168.0.91:5000/api/subscriber-update', headers=headers, json=json_data)

                # scenario 1 - create new capped slice and provision the unprioritized UE to it
                elif scenario_flag == 1:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data1 = {
                        'sst': 2,
                        'sd': 0
                    }

                    json_data2 = {
                        'imsi': imsi,
                        'sst': 2,
                        'downlink-ambr-value': testbed['downlink-ambr-value'],
                        'downlink-ambr-unit': testbed['downlink-ambr-unit'],
                        'uplink-ambr-value': testbed['uplink-ambr-value'],
                        'uplink-ambr-unit': testbed['uplink-ambr-unit'],
                    }

                    response1 = requests.post('http://192.168.0.91:5000/api/add-slice', headers=headers, json=json_data1)
                    response2 = requests.post('http://192.168.0.91:5000/api/subscriber-update', headers=headers, json=json_data2)
        
        # check if the traffic has returned to normal
        else:
            traffic_flag = 0
            print("Traffic is normal, setting flag to 0.")
            if action_flag == 1:
                action_flag = 0
                if scenario_flag == 0:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data = {
                        'imsi': imsi,
                        'downlink-ambr-value': 1,
                        'downlink-ambr-unit': 3,
                        'uplink-ambr-value': 1,
                        'uplink-ambr-unit': 3,
                    }

                    response = requests.post('http://192.168.0.91:5000/api/subscriber-update', headers=headers, json=json_data)

                elif scenario_flag == 1:
                    headers = {
                        'Content-Type': 'application/json',
                    }

                    json_data1 = {
                        'sst': 2,
                        'sd': 0
                    }

                    json_data2 = {
                        'imsi': imsi,
                        'sst': 1,
                        'downlink-ambr-value': 1,
                        'downlink-ambr-unit': 3,
                        'uplink-ambr-value': 1,
                        'uplink-ambr-unit': 3,
                    }

                    response2 = requests.post('http://192.168.0.91:5000/api/subscriber-update', headers=headers, json=json_data2)
                    response1 = requests.delete('http://192.168.0.91:5000/api/delete-slice', headers=headers, json=json_data1)


if __name__ == "__main__":
    
    # select the testbed on which to run the decision making engine
    testbed_id = 1
    filename = f'testbed-{testbed_id}.json'

    # read the testbed specific JSON file
    try:
        with open(filename, 'r') as file:
            testbed = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {filename} does not exist.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON.")

    while True:
        process_and_predict(testbed)
        # wait for 5 seconds before polling the function again
        time.sleep(5)  