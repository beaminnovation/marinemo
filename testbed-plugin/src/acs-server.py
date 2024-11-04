from flask import Flask, jsonify
import json
import random
from datetime import datetime

app = Flask(__name__)

# load the CPE monitoring JSON data model
with open('CPE_data-model.json', 'r') as file:
    data = json.load(file)

# initialize the previous values
previous_bytes_received = int(data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]["BytesReceived"]["_value"])
previous_bytes_sent = int(data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]["BytesSent"]["_value"])

# simulate CPE monitoring data
def update_data():
    global previous_bytes_received, previous_bytes_sent

    # generate incremental values for BytesReceived and BytesSent
    increment_received = random.randint(1000000, 2000000)
    increment_sent = random.randint(1000000, 2000000)

    # update previous values
    previous_bytes_received += increment_received
    previous_bytes_sent += increment_sent

    # update values and timestamps in the JSON data
    device_data = data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]
    device_data["BytesReceived"]["_value"] = str(previous_bytes_received)
    device_data["BytesReceived"]["_timestamp"] = datetime.utcnow().isoformat() + "Z"
    device_data["BytesSent"]["_value"] = str(previous_bytes_sent)
    device_data["BytesSent"]["_timestamp"] = datetime.utcnow().isoformat() + "Z"

    # write the updated data back to the data variable
    data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"] = device_data

    # save the updated data back to the JSON file
    with open('CPE_data-model.json', 'w') as file:
        json.dump(data, file, indent=4)

# endpoint for exposing the simulated data
@app.route('/devices', methods=['GET'])
def get_devices():
    
    update_data()
    return jsonify(data[0])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
