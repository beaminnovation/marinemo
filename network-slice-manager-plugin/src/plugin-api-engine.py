from flask import Flask, request, jsonify
import json
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from flask_cors import CORS
import pytz

# Initialize Flask app
app = Flask(__name__)
CORS(app)

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

    # Validate the required parameters
    if not testbed_id or not start_date or not stop_date:
        return jsonify({"error": "Missing required parameters"}), 400

    # Construct the CSV filename based on the testbed-id
    csv_filename = f'traffic_change_alerts_{testbed_id}.csv'

    try:
        # Load the CSV file
        alerts_df = pd.read_csv(csv_filename)

        # Convert the timestamp column to datetime with UTC
        alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'], utc=True)

        # Convert the input dates to timezone-aware datetime objects (UTC)
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.UTC)
        stop_date = datetime.strptime(stop_date, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.UTC)

        # Filter the alerts within the specified date range
        filtered_alerts = alerts_df[
            (alerts_df['timestamp'] >= start_date) & (alerts_df['timestamp'] <= stop_date)
        ]

        # Return the filtered alerts as JSON
        return filtered_alerts.to_json(orient='records'), 200

    except FileNotFoundError:
        return jsonify({"error": f"File for testbed {testbed_id} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# def alerts():
#     testbed_id = request.args.get('testbed-id')
#     start_date = request.args.get('start-date')
#     stop_date = request.args.get('stop-date')
#
#     # InfluxDB query to retrieve alert data
#     query = f'''
#     from(bucket: "{INFLUXDB_BUCKET}")
#     |> range(start: {start_date}, stop: {stop_date})
#     |> filter(fn: (r) => r["_measurement"] == "alerts" and r["testbed-id"] == "{testbed_id}")
#     '''
#     result = query_api.query(org=INFLUXDB_ORG, query=query)
#     results = []
#     for table in result:
#         for record in table.records:
#             results.append(record.values)
#
#     return jsonify(results)

# Endpoint for performance analysis
@app.route('/slice-manager-performance-analysis', methods=['GET'])
def performance_analysis():
    # Extract query parameters
    testbed_id = request.args.get('testbed-id', type=int)
    start_date = request.args.get('start-date', type=str)
    stop_date = request.args.get('stop-date', type=str)

    # Parse dates
    start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    stop_date = datetime.fromisoformat(stop_date.replace("Z", "+00:00"))

    # Read the corresponding CSV file based on testbed_id
    filename = f'monitoring-{testbed_id}.csv'
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

    # Filter data for the time range
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_filtered = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= stop_date)]

    # Calculate metrics
    avg_downlink_throughput = df_filtered['URLLC_Received_thrp_Mbps'].mean()
    avg_uplink_throughput = df_filtered['URLLC_Sent_thrp_Mbps'].mean()
    avg_rtt = df_filtered['RTT'].mean()
    total_traffic_consumption = (df_filtered['URLLC_BytesReceived'].sum() + df_filtered['URLLC_BytesSent'].sum())/1000000000
    unique_users = df_filtered['id'].nunique()

    # Create the response
    response = {
        "average_downlink_throughput (Mbps)": float(avg_downlink_throughput),
        "average_uplink_throughput (Mbps)": float(avg_uplink_throughput),
        "average_RTT (ms)": float(avg_rtt),
        "total_traffic_consumption (GBs)": float(total_traffic_consumption),
        "unique_users": int(unique_users)
    }

    return jsonify(response), 200

# def performance_analysis():
#     testbed_id = request.args.get('testbed-id')
#     start_date = request.args.get('start-date')
#     stop_date = request.args.get('stop-date')
#
#     # InfluxDB query to retrieve performance data
#     query = f'''
#     from(bucket: "{INFLUXDB_BUCKET}")
#     |> range(start: {start_date}, stop: {stop_date})
#     |> filter(fn: (r) => r["_measurement"] == "performance" and r["testbed-id"] == "{testbed_id}")
#     '''
#     result = query_api.query(org=INFLUXDB_ORG, query=query)
#     results = []
#     for table in result:
#         for record in table.records:
#             results.append(record.values)
#
#     return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)