from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from config import Config
import os

mongo = PyMongo()

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'))
    app.config.from_object(config_class)

    CORS(app)
    mongo.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app