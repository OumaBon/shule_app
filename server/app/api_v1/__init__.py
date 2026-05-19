from flask import Blueprint 


api = Blueprint('api', __name__)


@api.route('/')
def index():
    return "<h1>Welcome to the API</h1>"



from . import users, errors,teachers,students,school_class ,attendance 
