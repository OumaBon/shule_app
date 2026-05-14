from . import api 
from flask import request, jsonify
from app.services.user_service import user_services
from app.models.user import User    
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



@api.route('/users/query/by-email/<email>', methods=['GET'])
def get_user_by_email(email):
    """Get user by email"""
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    result, error, status_code = user_services.user_schema.dump(user), None, 200
    return jsonify(result), status_code

@api.route('/users/query/by-username/<username>', methods=['GET'])
def get_user_by_username(username):
    """Get user by username"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    result, error, status_code = user_services.user_schema.dump(user), None, 200
    return jsonify(result), status_code

@api.route('/users/query/active', methods=['GET'])
def get_active_users():
    """Get all active users"""
    users = User.query.filter_by(is_active=True).all()
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code

@api.route('/users/query/inactive', methods=['GET'])
def get_inactive_users():
    """Get all inactive users"""
    users = User.query.filter_by(is_active=False).all()
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code

@api.route('/users/query/by-role/<role>', methods=['GET'])
def get_users_by_role(role):
    """Get users by role (student, teacher, admin)"""
    if role not in ['student', 'teacher', 'admin']:
        return jsonify({"error": "Invalid role. Must be student, teacher, or admin"}), 400
    users = User.query.filter_by(role=role).all()
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code

@api.route('/users/query/search', methods=['GET'])
def search_users():
    """Search users by name, email, or username"""
    q = request.args.get('q', '')
    if not q:
        return jsonify({"error": "Search query parameter 'q' is required"}), 400
    
    search_term = f"%{q}%"
    users = User.query.filter(
        or_(
            User.email.ilike(search_term),
            User.username.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term)
        )
    ).all()
    
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code

@api.route('/users/query/recent', methods=['GET'])
def get_recent_users():
    """Get most recently created users"""
    limit = request.args.get('limit', 10, type=int)
    users = User.query.order_by(User.created_at.desc()).limit(limit).all()
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code

@api.route('/users/query/statistics', methods=['GET'])
def get_user_statistics():
    """Get user statistics"""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = User.query.filter_by(is_active=False).count()
    
    students = User.query.filter_by(role='student').count()
    teachers = User.query.filter_by(role='teacher').count()
    admins = User.query.filter_by(role='admin').count()
    
    # Recent signups (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = User.query.filter(User.created_at >= week_ago).count()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'by_role': {
            'students': students,
            'teachers': teachers,
            'admins': admins
        },
        'recent_signups_7days': recent_signups
    }), 200

@api.route('/users/query/bulk', methods=['POST'])
def get_users_bulk():
    """Get multiple users by IDs"""
    data = request.get_json()
    if not data or 'user_ids' not in data:
        return jsonify({"error": "Please provide user_ids array"}), 400
    
    user_ids = data.get('user_ids', [])
    if not isinstance(user_ids, list):
        return jsonify({"error": "user_ids must be an array"}), 400
    
    users = User.query.filter(User.id.in_(user_ids)).all()
    result, error, status_code = user_services.users_schema.dump(users), None, 200
    return jsonify(result), status_code