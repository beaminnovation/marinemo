import os
import requests
import json
import csv
import threading
import random
from flask import Flask, jsonify
from datetime import datetime

previous_values = {}

def update_cpe_data():
    
    # call the GenieACS TR-069 server API for getting the CPE monitoring data
    r = requests.get("http://localhost:5002/devices")
    data = r.json()

    if isinstance(data, dict):
        data = [data]  

    # select the CPEs of interest by their IDs
    ids_of_interest = [
        "A4FC77-3TG01797-FVN23500017C",
        "A4FC77-3TG01797-FVN23500017D"
    ]

    with open('output.csv', 'w', newline='') as csvfile:

        # select the fieldnames of interest
        fieldnames = ['id', 'BytesReceived', 'BytesSent', 'timestamp', 'URLLC_Received_thrp_Mbps', 'URLLC_Sent_thrp_Mbps']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for device in data:
            if device['_id'] in ids_of_interest:
                if device['_id'] == "A4FC77-3TG01797-FVN23500017C":
                    bytes_received = int(device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesReceived']['_value'])
                    bytes_sent = int(device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent']['_value'])
                    timestamp = datetime.strptime(device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent']['_timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

                    # check if there are previous values for this device
                    if device['_id'] in previous_values:
                        prev_data = previous_values[device['_id']]
                        prev_bytes_received = int(prev_data['BytesReceived'])
                        prev_bytes_sent = int(prev_data['BytesSent'])
                        prev_timestamp = prev_data['timestamp']

                        # calculate the bytes differences
                        delta_received = bytes_received - prev_bytes_received
                        delta_sent = bytes_sent - prev_bytes_sent

                        # calculate time difference in seconds
                        time_difference = (timestamp - prev_timestamp).total_seconds() + 1
                        
                        if time_difference > 0:
                            # convert bytes to megabytes
                            throughput_received = (delta_received / 1024 ** 2) / (time_difference / 1000)
                            throughput_sent = (delta_sent / 1024 ** 2) / (time_difference / 1000)

                            writer.writerow({
                                'id': device['_id'],
                                'BytesReceived': bytes_received,
                                'BytesSent': bytes_sent,
                                'timestamp': timestamp,
                                'URLLC_Received_thrp_Mbps': throughput_received,
                                'URLLC_Sent_thrp_Mbps': throughput_sent
                            })

                    # update the dictionary with current values for the next iteration
                    previous_values[device['_id']] = {
                        'BytesReceived': bytes_received,
                        'BytesSent': bytes_sent,
                        'timestamp': timestamp
                    }

    print("Data extraction and CSV writing complete.")

    input_csv_path = './output.csv'
    rows_to_insert = []

    with open(input_csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            formatted_row = {
                u'id': row['id'],
                u'URLLC_BytesReceived': row['BytesReceived'],
                u'URLLC_BytesSent': row['BytesSent'],
                u'URLLC_Received_thrp_Mbps': row['URLLC_Received_thrp_Mbps'],
                u'URLLC_Sent_thrp_Mbps': row['URLLC_Sent_thrp_Mbps'],
                u'timestamp': row['timestamp'],
                u'RTT': random.randint(17,25)
            }
            rows_to_insert.append(formatted_row)

    return rows_to_insert


app = Flask(__name__)

@app.route('/cpe-monitoring', methods=['GET'])
def get_cpe_data():
    
    # return the curated CPE monitoring data as JSON
    return jsonify(update_cpe_data())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

