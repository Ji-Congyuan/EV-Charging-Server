from app import app
from app.views.charging_demand import charging_demand

app.register_blueprint(charging_demand, url_prefix='/charging_demand')