from flask import Blueprint
from flask import request
from flask import session

charging_demand = Blueprint('charging_demand', __name__)


@charging_demand.route('/', methods=['POST'])
def requireChargingResult():
    pass