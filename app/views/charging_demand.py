import os.path
import json
from flask import Blueprint
from flask import request
from concurrent.futures import ThreadPoolExecutor
from app.EquilibriumTestTripChain import TripChainMain


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
        request.json.get('station_data'),                      # json
        request.json.get('demand_data'),                       # json
        int(request.json.get('initial_electricity_level')),    # int
        int(request.json.get('low_level_threshold')),          # int
        int(request.json.get('high_level_threshold'))          # int
    )
    computation_executor.submit(lambda x: TripChainMain(*x), args)

    return {
        'experiment_id': experiment_id
    }


@charging_demand.route('/output_check', methods=['POST'])
def output_check():
    check_id = request.json.get('experiment_id')
    return {
        'flag': os.path.exists('./app/experiment_result/' + check_id + '.json')
    }


@charging_demand.route('/get_output_data', methods=['POST'])
def get_output_data():
    get_id = request.json.get('experiment_id')
    with open('./app/experiment_result/' + get_id + '.json', 'r') as f:
        output_data = json.load(f)
        return output_data
