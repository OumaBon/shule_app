from . import api 
from app.services.teacher_service import teacher_service
from flask import request, jsonify  



@api.route('/teachers', methods=['POST'])
def create_teacher():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = teacher_service.create_teacher(data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/teachers', methods=['GET'])
def get_teachers():
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    subject = request.args.get('subject')
    
    result, error, status_code = teacher_service.get_teachers(skip, limit, subject)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/teachers/<int:teacher_id>', methods=['GET'])
def get_teacher(teacher_id):
    result, error, status_code = teacher_service.get_teacher(teacher_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/teachers/<int:teacher_id>', methods=['PUT'])
def update_teacher(teacher_id):
    data = request.json
    result, error, status_code = teacher_service.update_teacher(teacher_id, data)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/teachers/<int:teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    result, error, status_code = teacher_service.delete_teacher(teacher_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code