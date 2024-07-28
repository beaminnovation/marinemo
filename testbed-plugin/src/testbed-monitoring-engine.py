import os
import requests
import json
import csv
import threading
from flask import Flask, jsonify

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
                    bytes_received = \
                    device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesReceived'][
                        '_value']
                    bytes_sent = \
                    device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent'][
                        '_value']
                    timestamp = \
                    device['Device']['Cellular']['AccessPoint']['1']['X_ALU-COM_AccessPointStats']['BytesSent'][
                        '_timestamp']

                    writer.writerow({
                        'id': device['_id'],
                        'BytesReceived': bytes_received,
                        'BytesSent': bytes_sent,
                        'timestamp': timestamp
                    })

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

