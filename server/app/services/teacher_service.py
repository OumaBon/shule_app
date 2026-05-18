# app/services/teacher_service.py

from app.schemas.teacher_schema import (teacher_schema, teachers_schema)
from app.models.teacher import Teacher
from app.models.user import User
from app import db 
from marshmallow import ValidationError 
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 
from datetime import date


class TeacherService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TeacherService, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance  
    
    def __init__(self):
        if hasattr(self, '_initialised') and self._initialised:
            return 
       
        self.teacher_schema = teacher_schema
        self.teachers_schema = teachers_schema
        self._initialised = True
    

    def create_teacher(self, data):
        """
        Create a new teacher
        
        Args:
            data: Dictionary containing teacher data
            
        Returns:
            Tuple of (serialized_teacher, error_messages, status_code)
        """
        try:
            # Load and validate data using schema
            teacher = self.teacher_schema.load(data, session=db.session)
            
            db.session.add(teacher)
            db.session.commit()
            return self.teacher_schema.dump(teacher), None, 201
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            # Check for specific integrity errors
            error_msg = str(err)
            if 'employee_id' in error_msg:
                return None, {"error": "Employee ID already exists."}, 400
            elif 'user_id' in error_msg:
                return None, {"error": "User already has a teacher profile or invalid user ID."}, 400
            return None, {"error": "Database integrity error occurred."}, 400
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in create_teacher: {err}")
            import traceback
            traceback.print_exc()
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teachers(self, skip=0, limit=100, subject=None):
        """
        Get all teachers with pagination and optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            subject: Optional subject filter
            
        Returns:
            Tuple of (serialized_teachers, error_messages, status_code)
        """
        try:
            query = Teacher.query
            
            # Apply filters
            if subject:
                query = query.filter(Teacher.subject.ilike(f'%{subject}%'))
            
            # Apply pagination and ordering
            teachers = query.order_by(Teacher.created_at.desc()) \
                           .offset(skip) \
                           .limit(limit) \
                           .all()
            
            # Get total count for pagination info
            total = query.count()
            
            result = {
                'teachers': self.teachers_schema.dump(teachers),
                'total': total,
                'skip': skip,
                'limit': limit
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teacher(self, teacher_id):
        """
        Get a teacher by ID
        
        Args:
            teacher_id: Teacher ID
            
        Returns:
            Tuple of (serialized_teacher, error_messages, status_code)
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return None, {"error": "Teacher not found."}, 404
            return self.teacher_schema.dump(teacher), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teacher_by_user_id(self, user_id):
        """
        Get teacher by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (serialized_teacher, error_messages, status_code)
        """
        try:
            teacher = Teacher.query.filter_by(user_id=user_id).first()
            if not teacher:
                return None, {"error": "Teacher not found for this user."}, 404
            return self.teacher_schema.dump(teacher), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teacher_by_employee_id(self, employee_id):
        """
        Get teacher by employee ID
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Tuple of (serialized_teacher, error_messages, status_code)
        """
        try:
            teacher = Teacher.query.filter_by(employee_id=employee_id).first()
            if not teacher:
                return None, {"error": "Teacher not found with this employee ID."}, 404
            return self.teacher_schema.dump(teacher), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def update_teacher(self, teacher_id, data):
        """
        Update an existing teacher
        
        Args:
            teacher_id: Teacher ID to update
            data: Dictionary containing updated data
            
        Returns:
            Tuple of (updated_serialized_teacher, error_messages, status_code)
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return None, {"error": "Teacher not found."}, 404
            
            # Check if trying to change user_id and if new user exists
            if 'user_id' in data and data['user_id'] != teacher.user_id:
                user = User.query.get(data['user_id'])
                if not user:
                    return None, {"user_id": f"User with ID {data['user_id']} does not exist"}, 400
                
                # Check if new user already has a teacher profile
                existing_teacher = Teacher.query.filter(
                    Teacher.user_id == data['user_id'],
                    Teacher.id != teacher_id
                ).first()
                if existing_teacher:
                    return None, {"user_id": "User already has a teacher profile"}, 400
            
            # Check if employee_id is being changed and if it's unique
            if 'employee_id' in data and data['employee_id'] != teacher.employee_id:
                existing_teacher = Teacher.query.filter(
                    Teacher.employee_id == data['employee_id'],
                    Teacher.id != teacher_id
                ).first()
                if existing_teacher:
                    return None, {"employee_id": f"Employee ID '{data['employee_id']}' already exists"}, 400
            
            # Load and update teacher data
            updated_teacher = self.teacher_schema.load(
                data, 
                instance=teacher, 
                session=db.session, 
                partial=True
            )
            
            db.session.commit()
            return self.teacher_schema.dump(updated_teacher), None, 200
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            return None, {"error": "Database integrity error occurred."}, 400
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in update_teacher: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def delete_teacher(self, teacher_id):
        """
        Delete a teacher by ID
        
        Args:
            teacher_id: Teacher ID to delete
            
        Returns:
            Tuple of (data, error_messages, status_code)
        """
        try:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return None, {"error": "Teacher not found."}, 404
            
            db.session.delete(teacher)
            db.session.commit()
            return None, None, 204
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in delete_teacher: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def search_teachers(self, search_term):
        """
        Search teachers by employee ID, subject, or qualification
        
        Args:
            search_term: Search string
            
        Returns:
            Tuple of (serialized_teachers, error_messages, status_code)
        """
        try:
            search_pattern = f'%{search_term}%'
            
            teachers = Teacher.query.filter(
                db.or_(
                    Teacher.employee_id.ilike(search_pattern),
                    Teacher.subject.ilike(search_pattern),
                    Teacher.qualification.ilike(search_pattern)
                )
            ).limit(50).all()
            
            return self.teachers_schema.dump(teachers), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teachers_by_subject(self, subject):
        """
        Get all teachers teaching a specific subject
        
        Args:
            subject: Subject name
            
        Returns:
            Tuple of (serialized_teachers, error_messages, status_code)
        """
        try:
            teachers = Teacher.query.filter(
                Teacher.subject.ilike(f'%{subject}%')
            ).all()
            
            return self.teachers_schema.dump(teachers), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_teacher_statistics(self):
        """
        Get statistics about teachers
        
        Returns:
            Tuple of (statistics_data, error_messages, status_code)
        """
        try:
            from sqlalchemy import func
            
            total_teachers = Teacher.query.count()
            
            # Count teachers by subject (top 5 subjects)
            subject_stats = db.session.query(
                Teacher.subject,
                func.count(Teacher.id).label('count')
            ).group_by(Teacher.subject) \
             .order_by(func.count(Teacher.id).desc()) \
             .limit(5) \
             .all()
            
            # Get recent joins (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            recent_joins = Teacher.query.filter(
                Teacher.date_joined >= thirty_days_ago
            ).count()
            
            statistics = {
                'total_teachers': total_teachers,
                'subject_distribution': [
                    {'subject': subj, 'count': count} 
                    for subj, count in subject_stats
                ],
                'recent_joins_last_30_days': recent_joins
            }
            
            return statistics, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500



teacher_service = TeacherService()