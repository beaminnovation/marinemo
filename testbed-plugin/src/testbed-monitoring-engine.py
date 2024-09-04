import os
import requests
import json
import csv
import threading
from flask import Flask, jsonify

# Dictionary to store previous values
previous_values = {}

def update_cpe_data():
    threading.Timer(5.0, update_cpe_data).start()
    r = requests.get("http://172.16.53.129:7557/devices")
    data = r.json()

    ids_of_interest = [
        "A4FC77-3TG01797-FVN23500017C"
    ]

    with open('output.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'BytesReceived', 'BytesSent', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for device in data:
            if device['_id'] in ids_of_interest:
                if device['_id'] == "A4FC77-3TG01797-FVN23500017C":
                    bytes_received = device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesReceived']['_value']
                    bytes_sent = device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent']['_value']
                    timestamp = device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent']['_timestamp']

                    # Check if there are previous values for this device
                    if device['_id'] in previous_values:
                        prev_data = previous_values[device['_id']]
                        prev_bytes_received = prev_data['BytesReceived']
                        prev_bytes_sent = prev_data['BytesSent']
                        prev_timestamp = prev_data['timestamp']

                        # Calculate the byte differences
                        delta_received = bytes_received - prev_bytes_received
                        delta_sent = bytes_sent - prev_bytes_sent

                        # Calculate time difference in seconds
                        time_difference = timestamp - prev_timestamp

                        if time_difference > 0:
                            # Convert bytes to megabytes (1 MB = 2^20 bytes)
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

                    # Update the dictionary with current values for the next iteration
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
                u'BytesReceived': row['BytesReceived'],
                u'BytesSent': row['BytesSent'],
                u'URLLC_Received_thrp_Mbps': row['URLLC_Received_thrp_Mbps'],
                u'URLLC_Sent_thrp_Mbps': row['URLLC_Sent_thrp_Mbps'],
                u'timestamp': row['timestamp']
            }
            rows_to_insert.append(formatted_row)

    return rows_to_insert


app = Flask(__name__)

@app.route('/cpe-monitoring', methods=['GET'])
def get_cpe_data():
    # Return the list of CPE statuses as JSON
    return jsonify(update_cpe_data())

if __name__ == '__main__':
    app.run(debug=True)

