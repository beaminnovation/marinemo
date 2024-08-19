import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration for InfluxDB connection
INFLUXDB_URL = 'http://localhost:8086'
INFLUXDB_TOKEN = 'your_token'
INFLUXDB_ORG = 'your_org'
INFLUXDB_BUCKET = 'your_bucket'

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


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

    # ML model + data ingestion into influxDB

if __name__ == '__main__':
    testbed_id = 1
    decision_engine(testbed_id)
