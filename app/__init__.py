from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_caching import Cache

# from app import models
from app import blueprint_register


app = Flask(__name__)
app.config.from_object('settings')

# cache = Cache(app, config={'CACHE_TYPE': 'simple'})
# db = SQLAlchemy(app)
