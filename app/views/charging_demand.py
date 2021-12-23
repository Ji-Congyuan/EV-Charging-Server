import os.path
import os
import json
from flask import Blueprint
from flask import request
import threading
from app.EquilibriumTest import Equilibrium


charging_demand = Blueprint('charging_demand', __name__)


@charging_demand.route('/input_data', methods=['POST'])
def input_data():
    with open('./app/counter.json', 'r') as f:
        experiment_id = int(json.load(f)['counter'])

    experiment_id += 1
    with open('./app/counter.json', 'w') as f:
        json.dump({'counter': experiment_id}, f)

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
    # print(args)
    with open('./app/experiment_input/' + str(experiment_id) + '.json', 'w') as file_obj:
        json.dump(args, file_obj)

    # computation_executor.submit(lambda x: Equilibrium(*x), args)
    print("experiment id: " + str(experiment_id) + " is running")
    threading.Thread(target=Equilibrium, args=args).start()

    return {
        'id': str(experiment_id)
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
