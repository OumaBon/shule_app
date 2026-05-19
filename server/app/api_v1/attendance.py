
# app/api/attendance.py

from . import api 
from app.services.attendance_service import attendance_service
from flask import request, jsonify


@api.route('/attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for a single student"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = attendance_service.mark_attendance(data)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/bulk', methods=['POST'])
def mark_bulk_attendance():
    """Mark attendance for multiple students"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Get marked_by_id from request or data
    marked_by_id = request.args.get('marked_by_id', type=int)
    if not marked_by_id:
        return jsonify({"error": "Marked by teacher ID is required"}), 400
    
    result, error, status_code = attendance_service.mark_bulk_attendance(data, marked_by_id)
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/<int:attendance_id>', methods=['GET'])
def get_attendance(attendance_id):
    """Get attendance record by ID"""
    result, error, status_code = attendance_service.get_attendance(attendance_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    """Update an attendance record"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result, error, status_code = attendance_service.update_attendance(attendance_id, data)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    """Delete an attendance record"""
    result, error, status_code = attendance_service.delete_attendance(attendance_id)
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/student/<int:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    """Get attendance records for a specific student"""
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convert date strings to date objects
    from datetime import datetime
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    result, error, status_code = attendance_service.get_student_attendance(
        student_id, skip, limit, start_date, end_date
    )
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/daily', methods=['GET'])
def get_daily_attendance():
    """Get attendance records for a specific date"""
    date_str = request.args.get('date')
    class_id = request.args.get('class_id', type=int)
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    # Convert date string to date object
    from datetime import datetime, date
    attendance_date = None
    if date_str:
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        attendance_date = date.today()
    
    result, error, status_code = attendance_service.get_daily_attendance(
        attendance_date, class_id, skip, limit
    )
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/class/<int:class_id>/summary', methods=['GET'])
def get_class_attendance_summary(class_id):
    """Get attendance summary for a class"""
    date_str = request.args.get('date')
    
    # Convert date string to date object
    from datetime import datetime, date
    attendance_date = None
    if date_str:
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        attendance_date = date.today()
    
    result, error, status_code = attendance_service.get_class_attendance_summary(
        class_id, attendance_date
    )
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code


@api.route('/attendance/statistics', methods=['GET'])
def get_attendance_statistics():
    """Get attendance statistics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    class_id = request.args.get('class_id', type=int)
    
    # Convert date strings to date objects
    from datetime import datetime
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400
    
    result, error, status_code = attendance_service.get_attendance_statistics(
        start_date, end_date, class_id
    )
    
    if error:
        return jsonify(error), status_code
    return jsonify(result), status_code