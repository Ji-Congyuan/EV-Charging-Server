from flask import Flask
from flask_cors import CORS
# from flask_sqlalchemy import SQLAlchemy
# from flask_caching import Cache

# from app import models

app = Flask(__name__)
app.config.from_object('settings')
CORS(app, supports_credentials=True)

from app import blueprint_register
# cache = Cache(app, config={'CACHE_TYPE': 'simple'})
# db = SQLAlchemy(app)
