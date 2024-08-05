from flask import Flask, jsonify, request, abort
import yaml
import os

app = Flask(__name__)

# Paths to the YAML files
amf_yaml_file_path = 'sample.yaml'
ran_yaml_file_path = 'gnb_b210_20MHz_oneplus_8t.yml'


def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def write_yaml(file_path, data):
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False)


def get_new_sd(existing_sds):
    existing_sds_int = [int(sd, 16) for sd in existing_sds]
    new_sd_int = max(existing_sds_int) + 1
    new_sd_hex = f'{new_sd_int:06x}'
    return new_sd_hex


def update_amf_configuration(sst, sd):
    data = read_yaml(amf_yaml_file_path)
    amf_config = data.get('amf', {})
    slices = amf_config.get('s_nssai', [])

    new_s_nssai = {'- sst': sst, '  sd': sd}

    slices.append(new_s_nssai)
    amf_config['s_nssai'] = slices
    data['amf'] = amf_config

    write_yaml(amf_yaml_file_path, data)
    return new_s_nssai


def delete_amf_slice(sst, sd):
    data = read_yaml(amf_yaml_file_path)
    amf_config = data.get('amf', {})
    slices = amf_config.get('s_nssai', [])

    new_slices = [slice_ for slice_ in slices if not (slice_['sst'] == sst and slice_['sd'] == sd)]

    if len(new_slices) == len(slices):
        return None  # No slice was removed

    amf_config['s_nssai'] = new_slices
    data['amf'] = amf_config

    write_yaml(amf_yaml_file_path, data)
    return {'sst': sst, 'sd': sd}


def update_ran_configuration(new_s_nssai):
    data = read_yaml(ran_yaml_file_path)
    slicing = data.get('slicing', [])

    slicing.append({'sst': new_s_nssai['sst'], 'sd': new_s_nssai['sd']})
    data['slicing'] = slicing

    write_yaml(ran_yaml_file_path, data)
    return new_s_nssai


def delete_ran_slice(sst, sd):
    data = read_yaml(ran_yaml_file_path)
    slicing = data.get('slicing', [])

    new_slicing = [slice_ for slice_ in slicing if not (slice_['sst'] == sst and slice_['sd'] == sd)]

    if len(new_slicing) == len(slicing):
        return None  # No slice was removed

    data['slicing'] = new_slicing

    write_yaml(ran_yaml_file_path, data)
    return {'sst': sst, 'sd': sd}


@app.route('/api/add_slice', methods=['POST'])
def add_slice():
    if not request.is_json:
        abort(400, 'Request body must be JSON')

    data = request.get_json()
    sst = data.get('sst')
    sd = data.get('sd')

    new_slice = update_amf_configuration(sst, sd)
    updated_ran_slice = update_ran_configuration(new_slice)
    os.system("sudo systemctl restart open5gs-smfd")
    os.system("sudo systemctl restart open5gs-amfd")
    os.system("sudo systemctl restart open5gs-upfd")
    os.system("sudo systemctl restart open5gs-nssfd")
    return jsonify(updated_ran_slice)


@app.route('/api/delete_slice', methods=['DELETE'])
def delete_slice_api():
    if not request.is_json:
        abort(400, 'Request body must be JSON')

    data = request.get_json()
    sst = data.get('sst')
    sd = data.get('sd')

    if sst is None or sd is None:
        abort(400, 'Missing sst or sd parameter')

    deleted_amf_slice = delete_amf_slice(sst, sd)
    deleted_ran_slice = delete_ran_slice(sst, sd)

    if deleted_amf_slice is None or deleted_ran_slice is None:
        abort(404, 'Slice not found')

    return jsonify(deleted_amf_slice)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
