import os.path
import os
import json
from flask import Blueprint
from flask import request
from concurrent.futures import ThreadPoolExecutor
from app.EquilibriumTest import Equilibrium


charging_demand = Blueprint('charging_demand', __name__)
computation_executor = ThreadPoolExecutor(max_workers=8)
experiment_id_counter = 0


@charging_demand.route('/input_data', methods=['POST'])
def input_data():
    global experiment_id_counter
    experiment_id = str(experiment_id_counter)
    experiment_id_counter += 1
    args = (
        experiment_id,                                         # string
        request.json.get('node_data'),                         # json
        request.json.get('network_data'),                      # json
        int(request.json.get('pile_density')),                 # int
        request.json.get('demand_data'),                       # json
        int(request.json.get('initial_electricity_level')),    # int
        int(request.json.get('low_level_threshold')),          # int
        int(request.json.get('high_level_threshold'))          # int
    )
    print(args)
    with open('./app/experiment_input/' + str(experiment_id) + '.json', 'w') as file_obj:
        json.dump(args, file_obj)

    computation_executor.submit(lambda x: Equilibrium(*x), args)

    return {
        'id': experiment_id
    }


@charging_demand.route('/all_finished_result_ids', methods=['GET'])
def all_finished_result_ids():
    file_list = []
    for root, ds, fs in os.walk('app/experiment_result'):
        for f in fs:
            file_list.append(f.strip('.json'))

    return {
        'data': file_list
    }


@charging_demand.route('/get_output_data', methods=['POST'])
def get_output_data():
    print("get_output_data called")
    get_id = request.json.get('experiment_id')
    with open('./app/experiment_result/' + get_id + '.json', 'r') as f:
        output_data = json.load(f)
        return output_data
