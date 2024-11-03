from flask import Blueprint, jsonify, request
from socket import socket
from Open5GS import Open5GS
import json
import os

# connect to the UDM MongoDB database
Open5GS = Open5GS('127.0.0.1', 27017)

subscribers_blueprint = Blueprint('subscribers', __name__)

@subscribers_blueprint.route('/api/subscriber-provisioning', methods=['POST'])
def provision_subscriber():

    data = request.json
    if not data:
        return jsonify({"error": "Invalid request, JSON data required"}), 400

    imsi = data.get('imsi')
    if not imsi:
        return jsonify({"error": "IMSI is required"}), 400

    # preparing the slice_data based on the incoming request
    slice_data = [{
        "sst": data.get('sst'),
        "default_indicator": True,
        "session": [{
            "name": data.get('apn'),
            "type": 3,
            "pcc_rule": [],
            "ambr": {
                "uplink": {"value": data.get('uplink-ambr-value'), "unit": data.get('uplink-ambr-unit')},
                "downlink": {"value": data.get('downlink-ambr-value'), "unit": data.get('downlink-ambr-unit')}
            },
            "qos": {
                "index": data.get('qci'),
                "arp": {
                    "priority_level": 8,
                    "pre_emption_capability": 1,
                    "pre_emption_vulnerability": 1
                }
            }
        }]
    }]

    # preparing the subscriber data
    sub_data = {
        "imsi": data.get('imsi'),
        "subscribed_rau_tau_timer": 12,
        "network_access_mode": 0,
        "subscriber_status": 0,
        "operator_determined_barring": 0,
        "access_restriction_data": 32,
        "slice": slice_data,
        "ambr": {
            "uplink": {"value": data.get('uplink-ambr-value'), "unit": data.get('uplink-ambr-unit')},
            "downlink": {"value": data.get('downlink-ambr-value'), "unit": data.get('downlink-ambr-unit')}
        },
        "security": {
            "k": data.get('k'),
            "amf": "8000",
            "op": None,
            "opc": data.get('opc')
        },
        "schema_version": 1,
        "__v": 0
    }

    # add the new subscriber
    Open5GS.AddSubscriber(sub_data)

    return jsonify({"message": "Subscriber provisioned successfully"}), 200

@subscribers_blueprint.route('/api/subscriber-update', methods=['POST'])
def subscriber_update():

    data = request.json
    if not data:
        return jsonify({"error": "Invalid request, JSON data required"}), 400

    imsi = data.get('imsi')
    if not imsi:
        return jsonify({"error": "IMSI is required"}), 400

    sub_data = Open5GS.GetSubscriber(imsi)

    # update the fields provided in the request
    sub_data['imsi'] = imsi  
    sub_data['security']['k'] = data.get('k', sub_data['security']['k'])
    sub_data['security']['opc'] = data.get('opc', sub_data['security']['opc'])

    sub_data['slice'][0]['sst'] = data.get('sst', sub_data['slice'][0]['sst'])
    sub_data['slice'][0]['session'][0]['name'] = data.get('apn', sub_data['slice'][0]['session'][0]['name'])
    sub_data['slice'][0]['session'][0]['qos']['index'] = data.get('qci',
                                                                  sub_data['slice'][0]['session'][0]['qos']['index'])
    sub_data['slice'][0]['session'][0]['ambr']['uplink']['value'] = data.get('uplink-ambr-value',
                                                                             sub_data['slice'][0]['session'][0]['ambr'][
                                                                                 'uplink']['value'])
    sub_data['slice'][0]['session'][0]['ambr']['uplink']['unit'] = data.get('uplink-ambr-unit',
                                                                            sub_data['slice'][0]['session'][0]['ambr'][
                                                                                'uplink']['unit'])
    sub_data['slice'][0]['session'][0]['ambr']['downlink']['value'] = data.get('downlink-ambr-value',
                                                                               sub_data['slice'][0]['session'][0][
                                                                                   'ambr']['downlink']['value'])
    sub_data['slice'][0]['session'][0]['ambr']['downlink']['unit'] = data.get('downlink-ambr-unit',
                                                                              sub_data['slice'][0]['session'][0][
                                                                                  'ambr']['downlink']['unit'])

    # update existing subscriber
    Open5GS.UpdateSubscriber(imsi, sub_data)

    return jsonify({"message": "Subscriber updated successfully"}), 200

@subscribers_blueprint.route('/api/subscriber-delete', methods=['DELETE'])
def delete_subscriber():

    imsi = request.args.get('imsi')
    Open5GS.DeleteSubscriber(imsi)
    return jsonify({"message": f"Subscriber {imsi} deleted successfully"}), 200

@subscribers_blueprint.route('/api/subscribers', methods=['GET'])
def get_subscribers():
    
    data = Open5GS.GetSubscribers()
   
    api_response = [
    {
        'imsi': entry['imsi'],
        'sst': entry['slice'][0]['sst'],
        'downlink': {
            'value': entry['slice'][0]['session'][0]['ambr']['downlink']['value'],
            'unit': entry['slice'][0]['session'][0]['ambr']['downlink']['unit']
        },
        'uplink': {
            'value': entry['slice'][0]['session'][0]['ambr']['uplink']['value'],
            'unit': entry['slice'][0]['session'][0]['ambr']['uplink']['unit']
        },
        'qos_index': entry['slice'][0]['session'][0]['qos']['index']
    }
    for entry in data
    ]

    # convert the response to JSON
    json_response = json.dumps(api_response, indent=2)
                
    return json_response, 200

@subscribers_blueprint.route('/api/subscriber', methods=['GET'])
def get_subscriber():
    
    imsi = request.args.get('imsi')
    data = Open5GS.GetSubscriber(imsi)
    
    api_response = {
    'imsi': data['imsi'],
    'sst': data['slice'][0]['sst'],
    'downlink': {
        'value': data['slice'][0]['session'][0]['ambr']['downlink']['value'],
        'unit': data['slice'][0]['session'][0]['ambr']['downlink']['unit']
    },
    'uplink': {
        'value': data['slice'][0]['session'][0]['ambr']['uplink']['value'],
        'unit': data['slice'][0]['session'][0]['ambr']['uplink']['unit']
    },
    'qos_index': data['slice'][0]['session'][0]['qos']['index']
    }

    # convert the response to JSON
    json_response = json.dumps(api_response, indent=2)
                
    return json_response, 200
