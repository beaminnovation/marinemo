from flask import Blueprint, jsonify, request, abort
import yaml
import os

slices_blueprint = Blueprint('slices', __name__)

# Paths to the YAML files
core_yaml_file_path = 'sample.yaml'
ran_yaml_file_path = 'gnb_b210.yml'


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False)

def update_core_configuration(sst, sd):
    data = read_yaml(core_yaml_file_path)
    # amf
    # Apply the transformation to add an additional s_nssai item
    if 'amf' in data:
        for plmn in data['amf']['plmn_support']:
            # Check if the s_nssai list is correct and modify it if necessary
            if 's_nssai' in plmn and {'sst': sst, 'sd': sd} not in plmn['s_nssai']:
                plmn['s_nssai'].append({'sst': sst, 'sd': sd})

    # Save the modified data to a new YAML file with customized indentation
    with open(core_yaml_file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, indent=2)

    # nssf
    # Apply the transformation to add an additional s_nssai item
    if 'nssf' in data:
        for plmn in data['nssf']['plmn_support']:
            # Check if the s_nssai list is correct and modify it if necessary
            if 's_nssai' in plmn and {'sst': sst, 'sd': sd} not in plmn['s_nssai']:
                plmn['s_nssai'].append({'sst': sst, 'sd': sd})

    # Save the modified data to a new YAML file with customized indentation
    with open(core_yaml_file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, indent=2)

    return {'sst': sst, 'sd': sd}


def delete_core_slice(sst, sd):
    data = read_yaml(core_yaml_file_path)
    amf_config = data.get('amf', {})
    slices = amf_config.get('s_nssai', [])

    new_slices = [slice_ for slice_ in slices if not (slice_['sst'] == sst and slice_['sd'] == sd)]

    if len(new_slices) == len(slices):
        return None  # No slice was removed

    amf_config['s_nssai'] = new_slices
    data['amf'] = amf_config

    write_yaml(core_yaml_file_path, data)
    return {'sst': sst, 'sd': sd}


def update_ran_configuration(sst, sd):
    data = read_yaml(ran_yaml_file_path)

    # Add the new slicing entry
    new_slicing_entry = {'sst': sst, 'sd': sd}
    if 'slicing' in data:
        data['slicing'].append(new_slicing_entry)
    else:
        data['slicing'] = [new_slicing_entry]

    # Save the modified data back to a new YAML file
    with open(ran_yaml_file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False)

    return {'sst': sst, 'sd': sd}

def delete_ran_slice(sst, sd):
    data = read_yaml(ran_yaml_file_path)
    slicing = data.get('slicing', [])

    new_slicing = [slice_ for slice_ in slicing if not (slice_['sst'] == sst and slice_['sd'] == sd)]

    if len(new_slicing) == len(slicing):
        return None  # No slice was removed

    data['slicing'] = new_slicing

    write_yaml(ran_yaml_file_path, data)
    return {'sst': sst, 'sd': sd}


@slices_blueprint.route('/api/add-slice', methods=['POST'])
def add_slice():
    if not request.is_json:
        abort(400, 'Request body must be JSON')

    data = request.get_json()
    sst = data.get('sst')
    sd = data.get('sd')

    new_core_slice = update_core_configuration(sst, sd)
    new_ran_slice = update_ran_configuration(sst, sd)
    os.system("sudo systemctl restart open5gs-smfd")
    os.system("sudo systemctl restart open5gs-amfd")
    os.system("sudo systemctl restart open5gs-upfd")
    os.system("sudo systemctl restart open5gs-nssfd")
    return jsonify(new_ran_slice)


@slices_blueprint.route('/api/delete-slice', methods=['DELETE'])
def delete_slice():
    if not request.is_json:
        abort(400, 'Request body must be JSON')

    data = request.get_json()
    sst = data.get('sst')
    sd = data.get('sd')

    if sst is None or sd is None:
        abort(400, 'Missing sst or sd parameter')

    deleted_core_slice = delete_core_slice(sst, sd)
    deleted_ran_slice = delete_ran_slice(sst, sd)

    if deleted_core_slice is None or deleted_ran_slice is None:
        abort(404, 'Slice not found')

    return jsonify(deleted_core_slice)

@slices_blueprint.route('/api/get-slices', methods=['GET'])
def get_slices():
    data = read_yaml(core_yaml_file_path)
    if 'amf' not in data or 'plmn_support' not in data['amf']:
        return jsonify({'error': 'AMF configuration or plmn_support not found'}), 400

    plmn_support = data['amf']['plmn_support']
    slices = []

    for plmn in plmn_support:
        if 's_nssai' in plmn:
            for snssai in plmn['s_nssai']:
                slices.append({
                    'sst': snssai.get('sst'),
                    'sd': snssai.get('sd')
                })

    return jsonify(slices), 200