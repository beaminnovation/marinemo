from flask import Flask, jsonify
import json
import random
from datetime import datetime

app = Flask(__name__)

# Load the JSON data from the file (assuming the JSON data is stored locally)
with open('ex2.json', 'r') as file:
    data = json.load(file)

# Initialize the previous values
previous_bytes_received = int(data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]["BytesReceived"]["_value"])
previous_bytes_sent = int(data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]["BytesSent"]["_value"])

def update_data():
    global previous_bytes_received, previous_bytes_sent

    # Generate incremental values for BytesReceived and BytesSent
    increment_received = random.randint(1000000, 2000000)
    increment_sent = random.randint(1000000, 2000000)

    # Update previous values
    previous_bytes_received += increment_received
    previous_bytes_sent += increment_sent

    # Update values and timestamps in the JSON data
    device_data = data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"]
    device_data["BytesReceived"]["_value"] = str(previous_bytes_received)
    device_data["BytesReceived"]["_timestamp"] = datetime.utcnow().isoformat() + "Z"
    device_data["BytesSent"]["_value"] = str(previous_bytes_sent)
    device_data["BytesSent"]["_timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Write the updated data back to the data variable
    data[0]["Device"]["Cellular"]["AccessPoint"]["1"]["X_ALU-COM_AccessPointStats"] = device_data

    # Save the updated data back to the JSON file
    with open('ex2.json', 'w') as file:
        json.dump(data, file, indent=4)

@app.route('/devices', methods=['GET'])
def get_devices():
    update_data()
    return jsonify(data[0])  # Return the first item directly if your data is an array

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
