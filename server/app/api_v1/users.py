from . import api 
from flask import request, jsonify
from app.services.user_service import user_services

# Users routes

@api.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = user_services.create_user(data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code 

@api.route('/users', methods=['GET'])
def get_users():
    result, error, status_code = user_services.get_users()
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code

@api.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    result, error, status_code = user_services.get_user(user_id=id)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code

@api.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = user_services.update_user(user_id=id, data=data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code

# Optional: Add DELETE route
@api.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    result, error, status_code = user_services.delete_user(user_id=id)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code

@api.route('/users/<int:id>', methods=['PATCH'])
def patch_user(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = user_services.update_user(user_id=id, data=data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code