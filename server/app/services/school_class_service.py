# app/services/class_service.py

from app.schemas.school_class_schema import class_schema, classes_schema, class_list_schema, classes_list_schema
from app.models.school_class import SchoolClass
from app.models.teacher import Teacher
from app import db 
from marshmallow import ValidationError 
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 
from datetime import datetime


class ClassService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClassService, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance  
    
    def __init__(self):
        if hasattr(self, '_initialised') and self._initialised:
            return 
       
        self.class_schema = class_schema
        self.classes_schema = classes_schema
        self.class_list_schema = class_list_schema
        self.classes_list_schema = classes_list_schema
        self._initialised = True
    
    def create_class(self, data):
        """
        Create a new class
        
        Args:
            data: Dictionary containing class data
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            # Load and validate data using schema
            school_class = self.class_schema.load(data, session=db.session)
            
            db.session.add(school_class)
            db.session.commit()
            return self.class_schema.dump(school_class), None, 201
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            # Check for specific integrity errors
            error_msg = str(err).lower()
            if 'name' in error_msg:
                return None, {"error": "Class name already exists for this year."}, 400
            elif 'class_teacher_id' in error_msg:
                return None, {"error": "Invalid teacher ID."}, 400
            return None, {"error": "Database integrity error occurred."}, 400
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in create_class: {err}")
            import traceback
            traceback.print_exc()
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_classes(self, skip=0, limit=100, year=None, is_active=None):
        """
        Get all classes with pagination and optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            year: Optional year filter
            is_active: Optional active status filter
            
        Returns:
            Tuple of (serialized_classes, error_messages, status_code)
        """
        try:
            query = SchoolClass.query
            
            # Apply filters
            if year:
                query = query.filter(SchoolClass.year == year)
            
            if is_active is not None:
                query = query.filter(SchoolClass.is_active == is_active)
            
            # Apply pagination and ordering
            classes = query.order_by(SchoolClass.year.desc(), SchoolClass.name) \
                          .offset(skip) \
                          .limit(limit) \
                          .all()
            
            # Get total count for pagination info
            total = query.count()
            
            result = {
                'classes': self.classes_list_schema.dump(classes),
                'total': total,
                'skip': skip,
                'limit': limit
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_class(self, class_id):
        """
        Get a class by ID
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_class_by_name_and_year(self, name, year):
        """
        Get class by name and year
        
        Args:
            name: Class name
            year: Academic year
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.filter_by(
                name=name.title().strip(),
                year=year
            ).first()
            
            if not school_class:
                return None, {"error": "Class not found."}, 404
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def update_class(self, class_id, data):
        """
        Update an existing class
        
        Args:
            class_id: Class ID to update
            data: Dictionary containing updated data
            
        Returns:
            Tuple of (updated_serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            # Check if trying to change class_teacher_id
            if 'class_teacher_id' in data and data['class_teacher_id'] != school_class.class_teacher_id:
                if data['class_teacher_id'] is not None:
                    teacher = Teacher.query.get(data['class_teacher_id'])
                    if not teacher:
                        return None, {
                            "class_teacher_id": f"Teacher with ID {data['class_teacher_id']} does not exist"
                        }, 400
                    
                    # Check if teacher is already a class teacher for another active class
                    existing_class = SchoolClass.query.filter(
                        SchoolClass.class_teacher_id == data['class_teacher_id'],
                        SchoolClass.id != class_id,
                        SchoolClass.is_active == True
                    ).first()
                    
                    if existing_class:
                        return None, {
                            "class_teacher_id": f"Teacher is already assigned as class teacher for '{existing_class.name}'"
                        }, 400
            
            # Check if name and year combination already exists
            if 'name' in data and 'year' in data:
                existing_class = SchoolClass.query.filter(
                    SchoolClass.name == data['name'],
                    SchoolClass.year == data['year'],
                    SchoolClass.id != class_id
                ).first()
                
                if existing_class:
                    return None, {
                        "name": f"Class '{data['name']}' already exists for year {data['year']}"
                    }, 400
            
            # Load and update class data
            updated_class = self.class_schema.load(
                data, 
                instance=school_class, 
                session=db.session, 
                partial=True
            )
            
            db.session.commit()
            return self.class_schema.dump(updated_class), None, 200
        
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
            print(f"Unexpected error in update_class: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def delete_class(self, class_id):
        """
        Delete a class by ID
        
        Args:
            class_id: Class ID to delete
            
        Returns:
            Tuple of (data, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            # Check if class has students
            student_count = school_class.students.count()
            if student_count > 0:
                return None, {
                    "error": f"Cannot delete class with {student_count} enrolled students. Transfer or remove students first."
                }, 400
            
            db.session.delete(school_class)
            db.session.commit()
            return None, None, 204
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in delete_class: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_classes_by_year(self, year):
        """
        Get all classes for a specific year
        
        Args:
            year: Academic year
            
        Returns:
            Tuple of (serialized_classes, error_messages, status_code)
        """
        try:
            classes = SchoolClass.query.filter_by(year=year) \
                                     .order_by(SchoolClass.name) \
                                     .all()
            
            return self.classes_list_schema.dump(classes), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_active_classes(self):
        """
        Get all active classes
        
        Returns:
            Tuple of (serialized_classes, error_messages, status_code)
        """
        try:
            classes = SchoolClass.query.filter_by(is_active=True) \
                                     .order_by(SchoolClass.year.desc(), SchoolClass.name) \
                                     .all()
            
            return self.classes_list_schema.dump(classes), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def assign_class_teacher(self, class_id, teacher_id):
        """
        Assign a class teacher to a class
        
        Args:
            class_id: Class ID
            teacher_id: Teacher ID
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                return None, {"error": "Teacher not found."}, 404
            
            # Check if teacher is already assigned to another active class
            existing_class = SchoolClass.query.filter(
                SchoolClass.class_teacher_id == teacher_id,
                SchoolClass.id != class_id,
                SchoolClass.is_active == True
            ).first()
            
            if existing_class:
                return None, {
                    "error": f"Teacher is already assigned as class teacher for '{existing_class.name}'"
                }, 400
            
            school_class.class_teacher_id = teacher_id
            db.session.commit()
            
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in assign_class_teacher: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def remove_class_teacher(self, class_id):
        """
        Remove class teacher assignment
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            school_class.class_teacher_id = None
            db.session.commit()
            
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in remove_class_teacher: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def deactivate_class(self, class_id):
        """
        Deactivate a class
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            if not school_class.is_active:
                return None, {"error": "Class is already deactivated."}, 400
            
            school_class.is_active = False
            db.session.commit()
            
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in deactivate_class: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def activate_class(self, class_id):
        """
        Activate a class
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (serialized_class, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            if school_class.is_active:
                return None, {"error": "Class is already active."}, 400
            
            school_class.is_active = True
            db.session.commit()
            
            return self.class_schema.dump(school_class), None, 200
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in activate_class: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_class_enrollment_details(self, class_id):
        """
        Get detailed enrollment information for a class
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (enrollment_data, error_messages, status_code)
        """
        try:
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            enrollment_data = {
                'class_id': school_class.id,
                'class_name': school_class.name,
                'year': school_class.year,
                'capacity': school_class.capacity,
                'current_enrollment': school_class.current_enrollment,
                'available_seats': school_class.available_seats,
                'is_full': school_class.is_full,
                'occupancy_rate': round(
                    (school_class.current_enrollment / school_class.capacity * 100), 1
                ) if school_class.capacity > 0 else 0,
                'students': [
                    {
                        'id': student.id,
                        'admission_number': student.admission_number,
                        'name': student.user.full_name if student.user else 'Unknown'
                    }
                    for student in school_class.students
                ]
            }
            
            return enrollment_data, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def search_classes(self, search_term):
        """
        Search classes by name or description
        
        Args:
            search_term: Search string
            
        Returns:
            Tuple of (serialized_classes, error_messages, status_code)
        """
        try:
            search_pattern = f'%{search_term}%'
            
            classes = SchoolClass.query.filter(
                db.or_(
                    SchoolClass.name.ilike(search_pattern),
                    SchoolClass.description.ilike(search_pattern),
                    SchoolClass.room_number.ilike(search_pattern)
                )
            ).limit(50).all()
            
            return self.classes_list_schema.dump(classes), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_class_statistics(self):
        """
        Get statistics about classes
        
        Returns:
            Tuple of (statistics_data, error_messages, status_code)
        """
        try:
            from sqlalchemy import func
            
            total_classes = SchoolClass.query.count()
            active_classes = SchoolClass.query.filter_by(is_active=True).count()
            inactive_classes = total_classes - active_classes
            
            # Classes by year
            year_stats = db.session.query(
                SchoolClass.year,
                func.count(SchoolClass.id).label('count')
            ).group_by(SchoolClass.year) \
             .order_by(SchoolClass.year.desc()) \
             .limit(5) \
             .all()
            
            # Average capacity
            avg_capacity = db.session.query(
                func.avg(SchoolClass.capacity)
            ).scalar() or 0
            
            # Total capacity vs enrollment
            total_capacity = db.session.query(
                func.sum(SchoolClass.capacity)
            ).filter(SchoolClass.is_active == True).scalar() or 0
            
            statistics = {
                'total_classes': total_classes,
                'active_classes': active_classes,
                'inactive_classes': inactive_classes,
                'average_capacity': round(float(avg_capacity), 1),
                'total_capacity': total_capacity,
                'year_distribution': [
                    {'year': year, 'count': count} 
                    for year, count in year_stats
                ]
            }
            
            return statistics, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500


class_service = ClassService()