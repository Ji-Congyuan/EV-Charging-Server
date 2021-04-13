from flask import Blueprint
from flask import request
from flask import session

api = Blueprint('api', __name__)


@api.route('/')
def requireChargingResult():
    pass