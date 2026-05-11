from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config import config




db = SQLAlchemy() 
jwt = JWTManager()
bcrypt = Bcrypt()



def create_app(config_name):
    app = Flask(__name__) 
    app.config.from_object(config[config_name]) 
    config[config_name].init_app(app)

    db.init_app(app) 
    jwt.init_app(app)
    bcrypt.init_app(app)
  
    
    from app.api_v1 import api 
    app.register_blueprint(api)


    return app  