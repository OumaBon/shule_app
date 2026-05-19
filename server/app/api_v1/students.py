from . import api 
from flask import request, jsonify
from app.services.student_service import student_service

 

@api.route('/students', methods=['POST'])
def create_student():
    """Create a new student"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = student_service.create_student(data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students', methods=['GET'])
def get_students():
    """Get all students with optional filters"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    class_id = request.args.get('class_id', type=int)
    gender = request.args.get('gender')
    
    result, error, status_code = student_service.get_students(skip, limit, class_id, gender)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get a student by ID"""
    result, error, status_code = student_service.get_student(student_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = student_service.update_student(student_id, data)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    result, error, status_code = student_service.delete_student(student_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/search', methods=['GET'])
def search_students():
    """Search students by various criteria"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({"error": "Search term is required"}), 400
    
    result, error, status_code = student_service.search_students(search_term)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/admission/<admission_number>', methods=['GET'])
def get_student_by_admission(admission_number):
    """Get a student by admission number"""
    result, error, status_code = student_service.get_student_by_admission_number(admission_number)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/user/<int:user_id>', methods=['GET'])
def get_student_by_user(user_id):
    """Get a student by user ID"""
    result, error, status_code = student_service.get_student_by_user_id(user_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/class/<int:class_id>', methods=['GET'])
def get_students_by_class(class_id):
    """Get all students in a specific class"""
    result, error, status_code = student_service.get_students_by_class(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/gender/<gender>', methods=['GET'])
def get_students_by_gender(gender):
    """Get all students of a specific gender"""
    result, error, status_code = student_service.get_students_by_gender(gender)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/<int:student_id>/promote', methods=['PUT'])
def promote_student(student_id):
    """Promote a student to a new class"""
    data = request.get_json()
    if not data or 'class_id' not in data:
        return jsonify({"error": "New class ID is required"}), 400
    
    new_class_id = data['class_id']
    result, error, status_code = student_service.promote_student(student_id, new_class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/students/statistics', methods=['GET'])
def get_student_statistics():
    """Get student statistics"""
    result, error, status_code = student_service.get_student_statistics()
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code