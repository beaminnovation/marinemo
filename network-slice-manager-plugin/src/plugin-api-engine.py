from flask import Flask, request, jsonify
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Initialize Flask app
app = Flask(__name__)

# Configure your InfluxDB connection
INFLUXDB_URL = 'http://localhost:8086'
INFLUXDB_TOKEN = 'your_token'
INFLUXDB_ORG = 'your_org'
INFLUXDB_BUCKET = 'your_bucket'

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()


# Endpoint for managing slice behavior
@app.route('/slice-manager-behaviour', methods=['POST'])
def manage_slice():
    data = request.json
    testbed_id = data['testbed-id']
    filename = f'testbed-{testbed_id}.json'
    with open(filename, 'w') as f:
        json.dump(data, f)
    return jsonify({"message": "Data saved successfully", "filename": filename}), 200

# Endpoint for alerts
@app.route('/slice-manager-alerts', methods=['GET'])
def alerts():
    testbed_id = request.args.get('testbed-id')
    start_date = request.args.get('start-date')
    stop_date = request.args.get('stop-date')

    # InfluxDB query to retrieve alert data
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: {start_date}, stop: {stop_date})
    |> filter(fn: (r) => r["_measurement"] == "alerts" and r["testbed-id"] == "{testbed_id}")
    '''
    result = query_api.query(org=INFLUXDB_ORG, query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append(record.values)

    return jsonify(results)

# Endpoint for performance analysis
@app.route('/slice-manager-performance-analysis', methods=['GET'])
def performance_analysis():
    testbed_id = request.args.get('testbed-id')
    start_date = request.args.get('start-date')
    stop_date = request.args.get('stop-date')

    # InfluxDB query to retrieve performance data
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: {start_date}, stop: {stop_date})
    |> filter(fn: (r) => r["_measurement"] == "performance" and r["testbed-id"] == "{testbed_id}")
    '''
    result = query_api.query(org=INFLUXDB_ORG, query=query)
    results = []
    for table in result:
        for record in table.records:
            results.append(record.values)

    return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True)
