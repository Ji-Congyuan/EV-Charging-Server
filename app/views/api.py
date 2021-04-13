from flask import Blueprint
from flask import request
from flask import session

api = Blueprint('api', __name__)


@api.route('/', methods=['POST'])
def requireChargingResult():
    pass