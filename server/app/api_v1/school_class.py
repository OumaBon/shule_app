# app/api/classes.py

from . import api 
from app.services.school_class_service import class_service
from flask import request, jsonify  


@api.route('/classes', methods=['POST'])
def create_class():
    """Create a new class"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = class_service.create_class(data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes', methods=['GET'])
def get_classes():
    """Get all classes with optional filters"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    year = request.args.get('year', type=int)
    is_active = request.args.get('is_active')
    
    # Convert is_active string to boolean if provided
    if is_active is not None:
        is_active = is_active.lower() == 'true'
    
    result, error, status_code = class_service.get_classes(skip, limit, year, is_active)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>', methods=['GET'])
def get_class(class_id):
    """Get a class by ID"""
    result, error, status_code = class_service.get_class(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    """Update a class"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = class_service.update_class(class_id, data)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    """Delete a class"""
    result, error, status_code = class_service.delete_class(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/search', methods=['GET'])
def search_classes():
    """Search classes by name, description, or room number"""
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({"error": "Search term is required"}), 400
    
    result, error, status_code = class_service.search_classes(search_term)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/active', methods=['GET'])
def get_active_classes():
    """Get all active classes"""
    result, error, status_code = class_service.get_active_classes()
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/year/<int:year>', methods=['GET'])
def get_classes_by_year(year):
    """Get classes by academic year"""
    result, error, status_code = class_service.get_classes_by_year(year)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/name/<name>/year/<int:year>', methods=['GET'])
def get_class_by_name_and_year(name, year):
    """Get class by name and year"""
    result, error, status_code = class_service.get_class_by_name_and_year(name, year)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>/assign-teacher', methods=['PUT'])
def assign_class_teacher(class_id):
    """Assign a class teacher"""
    data = request.get_json()
    if not data or 'teacher_id' not in data:
        return jsonify({"error": "Teacher ID is required"}), 400
    
    teacher_id = data['teacher_id']
    result, error, status_code = class_service.assign_class_teacher(class_id, teacher_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>/remove-teacher', methods=['PUT'])
def remove_class_teacher(class_id):
    """Remove class teacher assignment"""
    result, error, status_code = class_service.remove_class_teacher(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>/deactivate', methods=['PUT'])
def deactivate_class(class_id):
    """Deactivate a class"""
    result, error, status_code = class_service.deactivate_class(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>/activate', methods=['PUT'])
def activate_class(class_id):
    """Activate a class"""
    result, error, status_code = class_service.activate_class(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/<int:class_id>/enrollment', methods=['GET'])
def get_class_enrollment(class_id):
    """Get detailed enrollment information for a class"""
    result, error, status_code = class_service.get_class_enrollment_details(class_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/classes/statistics', methods=['GET'])
def get_class_statistics():
    """Get class statistics"""
    result, error, status_code = class_service.get_class_statistics()
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code