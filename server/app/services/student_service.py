# app/services/student_service.py

from app.schemas.student_schema import student_schema, students_schema, student_list_schema
from app.models.student import Student
from app.models.user import User
from app.models.school_class import SchoolClass
from app import db 
from marshmallow import ValidationError 
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 
from datetime import date, datetime, timedelta


class StudentService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StudentService, cls).__new__(cls)
            cls._instance._initialised = False
        return cls._instance  
    
    def __init__(self):
        if hasattr(self, '_initialised') and self._initialised:
            return 
       
        self.student_schema = student_schema
        self.students_schema = students_schema
        self.student_list_schema = student_list_schema
        self._initialised = True
    
    def create_student(self, data):
        """
        Create a new student
        
        Args:
            data: Dictionary containing student data
            
        Returns:
            Tuple of (serialized_student, error_messages, status_code)
        """
        try:
            # Load and validate data using schema
            student = self.student_schema.load(data, session=db.session)
            
            db.session.add(student)
            db.session.commit()
            return self.student_schema.dump(student), None, 201
        
        except ValidationError as err:
            db.session.rollback()
            return None, err.messages, 400
        
        except IntegrityError as err:
            db.session.rollback()
            # Check for specific integrity errors
            error_msg = str(err).lower()
            if 'admission_number' in error_msg:
                return None, {"error": "Admission number already exists."}, 400
            elif 'user_id' in error_msg:
                return None, {"error": "User already has a student profile or invalid user ID."}, 400
            elif 'class_id' in error_msg:
                return None, {"error": "Invalid class ID."}, 400
            return None, {"error": "Database integrity error occurred."}, 400
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in create_student: {err}")
            import traceback
            traceback.print_exc()
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_students(self, skip=0, limit=100, class_id=None, gender=None):
        """
        Get all students with pagination and optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            class_id: Optional class filter
            gender: Optional gender filter
            
        Returns:
            Tuple of (serialized_students, error_messages, status_code)
        """
        try:
            query = Student.query
            
            # Apply filters
            if class_id:
                query = query.filter(Student.class_id == class_id)
            
            if gender:
                query = query.filter(Student.gender.ilike(gender))
            
            # Apply pagination and ordering
            students = query.order_by(Student.created_at.desc()) \
                           .offset(skip) \
                           .limit(limit) \
                           .all()
            
            # Get total count for pagination info
            total = query.count()
            
            result = {
                'students': self.student_list_schema.dump(students),
                'total': total,
                'skip': skip,
                'limit': limit
            }
            
            return result, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_student(self, student_id):
        """
        Get a student by ID
        
        Args:
            student_id: Student ID
            
        Returns:
            Tuple of (serialized_student, error_messages, status_code)
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, {"error": "Student not found."}, 404
            return self.student_schema.dump(student), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_student_by_user_id(self, user_id):
        """
        Get student by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (serialized_student, error_messages, status_code)
        """
        try:
            student = Student.query.filter_by(user_id=user_id).first()
            if not student:
                return None, {"error": "Student not found for this user."}, 404
            return self.student_schema.dump(student), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_student_by_admission_number(self, admission_number):
        """
        Get student by admission number
        
        Args:
            admission_number: Student admission number
            
        Returns:
            Tuple of (serialized_student, error_messages, status_code)
        """
        try:
            student = Student.query.filter_by(
                admission_number=admission_number.upper().strip()
            ).first()
            if not student:
                return None, {"error": "Student not found with this admission number."}, 404
            return self.student_schema.dump(student), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def update_student(self, student_id, data):
        """
        Update an existing student
        
        Args:
            student_id: Student ID to update
            data: Dictionary containing updated data
            
        Returns:
            Tuple of (updated_serialized_student, error_messages, status_code)
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, {"error": "Student not found."}, 404
            
            # Check if trying to change user_id and if new user exists
            if 'user_id' in data and data['user_id'] != student.user_id:
                user = User.query.get(data['user_id'])
                if not user:
                    return None, {"user_id": f"User with ID {data['user_id']} does not exist"}, 400
                
                # Check if new user already has a student profile
                existing_student = Student.query.filter(
                    Student.user_id == data['user_id'],
                    Student.id != student_id
                ).first()
                if existing_student:
                    return None, {"user_id": "User already has a student profile"}, 400
            
            # Check if admission_number is being changed and if it's unique
            if 'admission_number' in data and data['admission_number'] != student.admission_number:
                existing_student = Student.query.filter(
                    Student.admission_number == data['admission_number'],
                    Student.id != student_id
                ).first()
                if existing_student:
                    return None, {
                        "admission_number": f"Admission number '{data['admission_number']}' already exists"
                    }, 400
            
            # Check if class_id is being changed and if class exists
            if 'class_id' in data and data['class_id'] != student.class_id:
                school_class = SchoolClass.query.get(data['class_id'])
                if not school_class:
                    return None, {"class_id": f"Class with ID {data['class_id']} does not exist"}, 400
            
            # Load and update student data
            updated_student = self.student_schema.load(
                data, 
                instance=student, 
                session=db.session, 
                partial=True
            )
            
            db.session.commit()
            return self.student_schema.dump(updated_student), None, 200
        
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
            print(f"Unexpected error in update_student: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def delete_student(self, student_id):
        """
        Delete a student by ID
        
        Args:
            student_id: Student ID to delete
            
        Returns:
            Tuple of (data, error_messages, status_code)
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, {"error": "Student not found."}, 404
            
            # Check for related attendance records before deletion
            if hasattr(student, 'attendance_records'):
                attendance_count = student.attendance_records.count()
                if attendance_count > 0:
                    return None, {
                        "error": f"Cannot delete student with {attendance_count} attendance records. Remove attendance records first."
                    }, 400
            
            db.session.delete(student)
            db.session.commit()
            return None, None, 204
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in delete_student: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def search_students(self, search_term):
        """
        Search students by admission number, guardian name, or guardian phone
        
        Args:
            search_term: Search string
            
        Returns:
            Tuple of (serialized_students, error_messages, status_code)
        """
        try:
            search_pattern = f'%{search_term}%'
            
            students = Student.query.filter(
                db.or_(
                    Student.admission_number.ilike(search_pattern),
                    Student.guardian_name.ilike(search_pattern),
                    Student.guardian_phone.ilike(search_pattern)
                )
            ).limit(50).all()
            
            return self.student_list_schema.dump(students), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_students_by_class(self, class_id):
        """
        Get all students in a specific class
        
        Args:
            class_id: Class ID
            
        Returns:
            Tuple of (serialized_students, error_messages, status_code)
        """
        try:
            # Verify class exists
            school_class = SchoolClass.query.get(class_id)
            if not school_class:
                return None, {"error": "Class not found."}, 404
            
            students = Student.query.filter_by(class_id=class_id) \
                                   .order_by(Student.admission_number) \
                                   .all()
            
            return self.student_list_schema.dump(students), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_students_by_gender(self, gender):
        """
        Get all students of a specific gender
        
        Args:
            gender: Gender to filter by
            
        Returns:
            Tuple of (serialized_students, error_messages, status_code)
        """
        try:
            students = Student.query.filter(
                Student.gender.ilike(gender)
            ).order_by(Student.admission_number).all()
            
            return self.student_list_schema.dump(students), None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500
    
    def promote_student(self, student_id, new_class_id):
        """
        Promote a student to a new class
        
        Args:
            student_id: Student ID
            new_class_id: New class ID
            
        Returns:
            Tuple of (serialized_student, error_messages, status_code)
        """
        try:
            student = Student.query.get(student_id)
            if not student:
                return None, {"error": "Student not found."}, 404
            
            # Verify new class exists
            new_class = SchoolClass.query.get(new_class_id)
            if not new_class:
                return None, {"error": "Target class not found."}, 404
            
            # Check if student is already in this class
            if student.class_id == new_class_id:
                return None, {"error": "Student is already in this class."}, 400
            
            # Update class
            student.class_id = new_class_id
            db.session.commit()
            
            return self.student_schema.dump(student), None, 200
        
        except SQLAlchemyError as err:
            db.session.rollback()
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            db.session.rollback()
            print(f"Unexpected error in promote_student: {err}")
            return None, {"error": "An unexpected error occurred."}, 500
    
    def get_student_statistics(self):
        """
        Get statistics about students
        
        Returns:
            Tuple of (statistics_data, error_messages, status_code)
        """
        try:
            from sqlalchemy import func
            
            total_students = Student.query.count()
            
            # Gender distribution
            gender_stats = db.session.query(
                Student.gender,
                func.count(Student.id).label('count')
            ).group_by(Student.gender).all()
            
            # Age groups
            today = date.today()
            students = Student.query.all()
            
            age_groups = {
                '3-6': 0,
                '7-10': 0,
                '11-14': 0,
                '15-18': 0,
                '19+': 0
            }
            
            for student in students:
                if student.age:
                    if student.age <= 6:
                        age_groups['3-6'] += 1
                    elif student.age <= 10:
                        age_groups['7-10'] += 1
                    elif student.age <= 14:
                        age_groups['11-14'] += 1
                    elif student.age <= 18:
                        age_groups['15-18'] += 1
                    else:
                        age_groups['19+'] += 1
            
            # Class distribution (top 10 classes)
            class_stats = db.session.query(
                Student.class_id,
                func.count(Student.id).label('count')
            ).group_by(Student.class_id) \
             .order_by(func.count(Student.id).desc()) \
             .limit(10) \
             .all()
            
            # Recent enrollments (last 30 days)
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            recent_enrollments = Student.query.filter(
                Student.date_enrolled >= thirty_days_ago
            ).count()
            
            statistics = {
                'total_students': total_students,
                'gender_distribution': [
                    {'gender': gender, 'count': count} 
                    for gender, count in gender_stats
                ],
                'age_groups': age_groups,
                'class_distribution': [
                    {'class_id': class_id, 'count': count} 
                    for class_id, count in class_stats
                ],
                'recent_enrollments_last_30_days': recent_enrollments
            }
            
            return statistics, None, 200
        
        except SQLAlchemyError as err:
            return None, {"error": "Database error occurred."}, 500 
        
        except Exception as err:
            return None, {"error": "An unexpected error occurred."}, 500


student_service = StudentService()