from app import app
from app.views.api import api

app.register_blueprint(api, url_prefix='/api')